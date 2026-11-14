const { test, expect } = require("./artifact-test");

test.beforeEach(async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.addInitScript(() => {
    localStorage.setItem("hg-language", "en");
    localStorage.setItem("td-color-theme", "light");
    // Observe real canvas work, including frames painted while CSS hides it.
    window.landingWorldPaints = 0;
    const clear = CanvasRenderingContext2D.prototype.clearRect;
    CanvasRenderingContext2D.prototype.clearRect = function (...args) {
      if (this.canvas.id === "world") window.landingWorldPaints++;
      return clear.apply(this, args);
    };
  });
});

async function expectStaticStory(page) {
  await expect(page.locator("#hg-landing")).not.toHaveClass(/\blive\b/);
  await expect(page.locator("#world")).toBeHidden();
  const panels = page.locator("#story .panel");
  await expect(panels).toHaveCount(4);
  for (const panel of await panels.all()) {
    await expect(panel).toBeVisible();
    expect(await panel.evaluate(node => node.inert)).toBe(false);
    expect(await panel.getAttribute("aria-hidden")).not.toBe("true");
  }
  await expect.poll(() => page.locator(".still").evaluateAll(canvases =>
    canvases.every(canvas => {
      const pixels = canvas.getContext("2d").getImageData(0, 0, canvas.width, canvas.height).data;
      for (let i = 3; i < pixels.length; i += 4) if (pixels[i] > 16) return true;
      return false;
    }))).toBe(true);
}

async function expectStaticBeatAtTop(page, id) {
  await expect.poll(() => page.locator(`#beat-${id}`).evaluate(node => {
    const margin = parseFloat(getComputedStyle(node).scrollMarginTop) || 0;
    const padding = parseFloat(getComputedStyle(document.scrollingElement).scrollPaddingTop) || 0;
    return Math.abs(node.getBoundingClientRect().top - margin - padding);
  })).toBeLessThanOrEqual(2);
}

test("enabling reduced motion keeps the selected layer and stops hidden canvas work", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 568 });
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.goto("/");
  await expect(page.locator("#hg-landing")).toHaveClass(/\blive\b/);
  const timeOrigin = await page.evaluate(() => performance.timeOrigin);
  await page.locator('#hg-stack button[data-layer="3"]').click();
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expectStaticStory(page);
  await expectStaticBeatAtTop(page, "ai");
  const stopped = await page.evaluate(() => ({ y: scrollY, paints: window.landingWorldPaints }));
  // Give the old frame loop several chances to repaint or move the page.
  await page.waitForTimeout(300);
  expect(await page.evaluate(() => ({ y: scrollY, paints: window.landingWorldPaints }))).toEqual(stopped);
  expect(await page.evaluate(() => performance.timeOrigin)).toBe(timeOrigin);
  await page.evaluate(() => scrollTo({ top: 0, behavior: "instant" }));
  // The static hero uses natural document flow on short screens: readers can
  // scroll its complete legend into view without triggering the graph story.
  await page.locator("#hg-stack .hgs-labels").evaluate(node =>
    node.scrollIntoView({ block: "center", behavior: "instant" }));
  for (const button of await page.locator("#hg-stack button[data-layer]").all()) {
    await expect(button).toBeVisible();
    expect(await button.evaluate(node => {
      const box = node.getBoundingClientRect();
      return box.left >= 0 && box.right <= innerWidth && box.top >= 0 && box.bottom <= innerHeight
        && node.contains(document.elementFromPoint(box.left + box.width / 2, box.top + box.height / 2));
    })).toBe(true);
  }
  await page.locator('#hg-stack button[data-layer="0"]').click();
  await expectStaticBeatAtTop(page, "database");
  await expect(page.locator("#beat-database .story-guide")).toBeVisible();
});

test("motion preferences can switch repeatedly without losing explanations or duplicating navigation", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const timeOrigin = await page.evaluate(() => performance.timeOrigin);
  await expectStaticStory(page);
  for (const [layer, beat] of [["1", "toolchain"], ["2", "computing"]]) {
    await page.evaluate(() => scrollTo({ top: 0, behavior: "instant" }));
    await page.locator(`#hg-stack button[data-layer="${layer}"]`).click();
    await expectStaticBeatAtTop(page, beat);
    await page.emulateMedia({ reducedMotion: "no-preference" });
    await expect(page.locator("#hg-landing")).toHaveClass(/\blive\b/);
    await expect(page.locator(`#beat-${beat}`)).toHaveClass(/\bon\b/);
    await expect(page.locator("#world")).toHaveCSS("opacity", "1");
    const paints = await page.evaluate(() => window.landingWorldPaints);
    await expect.poll(() => page.evaluate(() => window.landingWorldPaints)).toBeGreaterThan(paints);
    await page.locator('#mini button[data-id="ai"]').click();
    await expect(page.locator("#beat-ai")).toHaveClass(/\bon\b/);
    await page.emulateMedia({ reducedMotion: "reduce" });
    await expectStaticStory(page);
    await expectStaticBeatAtTop(page, "ai");
  }
  expect(await page.evaluate(() => performance.timeOrigin)).toBe(timeOrigin);
  await page.locator("#components").scrollIntoViewIfNeeded();
  const before = await page.locator("#components").evaluate(node => node.getBoundingClientRect().top);
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await expect(page.locator("#hg-landing")).toHaveClass(/\blive\b/);
  await expect.poll(() => page.locator("#components").evaluate(node => node.getBoundingClientRect().top))
    .toBeCloseTo(before, 0);
});

test("each layer animates its own artwork on the idle hero and respects reduced motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.goto("/");
  const layers = page.locator("#hg-stack .hgs-layer");
  await expect(page.locator("#hg-stack")).toHaveClass(/hgs-live/);

  // Look inside each SVG, so floating the entire slab cannot satisfy this check.
  const snapshot = () => layers.evaluateAll(elements => elements.map(layer => {
    const animations = layer.querySelector(".hgs-art").getAnimations({ subtree: true });
    return animations.filter(animation => animation.playState === "running").map(animation => {
      const style = getComputedStyle(animation.effect.target);
      return [style.transform, style.opacity, style.strokeDashoffset, style.fillOpacity].join("/");
    }).join("|");
  }));
  const first = await snapshot();
  expect(first).toHaveLength(4);
  expect(first.every(Boolean)).toBe(true);
  const changed = new Set();
  await expect.poll(async () => {
    (await snapshot()).forEach((frame, i) => { if (frame !== first[i]) changed.add(i); });
    return changed.size;
  }).toBe(4);

  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect.poll(snapshot).toEqual(["", "", "", ""]);
});
