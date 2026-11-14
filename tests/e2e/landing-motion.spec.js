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
  for (const [layer, beat] of [["2", "toolchain"], ["1", "computing"]]) {
    await page.evaluate(() => scrollTo({ top: 0, behavior: "instant" }));
    await page.locator(`#hg-stack button[data-layer="${layer}"]`).click();
    await expectStaticBeatAtTop(page, beat);
    await page.emulateMedia({ reducedMotion: "no-preference" });
    await expect(page.locator("#hg-landing")).toHaveClass(/\blive\b/);
    await expect(page.locator(`#beat-${beat}`)).toHaveClass(/\bon\b/);
    await expect(page.locator("#world")).toHaveCSS("opacity", "1");
    const paints = await page.evaluate(() => window.landingWorldPaints);
    await expect.poll(() => page.evaluate(() => window.landingWorldPaints)).toBeGreaterThan(paints);
    await page.evaluate(() => scrollTo({ top: 0, behavior: "instant" }));
    await expect(page.locator("#stage")).not.toHaveClass(/diving/);
    await page.locator('#hg-stack button[data-layer="3"]').click();
    await expect(page.locator("#beat-ai")).toHaveCSS("opacity", "1");
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

test("switching motion keeps partially revealed homepage content at the reading position", async ({ page }) => {
  await page.setViewportSize({ width: 1414, height: 826 });
  await page.goto("/");
  const landing = page.locator("#hg-landing");
  const content = page.locator(".landing-content");
  await expect(landing).toHaveClass(/\blive\b/);
  for (const remainingStory of [100, 20]) {
    await content.evaluate((element, top) => {
      scrollBy({ top: element.getBoundingClientRect().top - top, behavior: "instant" });
    }, remainingStory);
    const drift = () => content.evaluate((element, top) =>
      Math.abs(element.getBoundingClientRect().top - top), remainingStory);
    await expect.poll(drift).toBeLessThanOrEqual(2);
    for (const reducedMotion of ["reduce", "no-preference"]) {
      await page.emulateMedia({ reducedMotion });
      if (reducedMotion === "reduce") await expect(landing).not.toHaveClass(/\blive\b/);
      else await expect(landing).toHaveClass(/\blive\b/);
      await expect.poll(drift).toBeLessThanOrEqual(2);
    }
  }
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

test("idle layer tour follows the visual stack and yields to hover, keyboard and reduced motion", async ({ page }) => {
  const dwell = 3200;
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.clock.install({ time: new Date("2026-01-01T12:00:00Z") });
  await page.clock.pauseAt(new Date("2026-01-01T12:01:00Z"));
  await page.goto("/");
  const stack = page.locator("#hg-stack");
  const active = stack.locator(".hgs-layer.is-active");
  await page.clock.runFor(1800);
  await expect(stack).toHaveClass(/hgs-live/);
  await expect(active).toHaveCount(0);

  for (const id of ["ai", "toolchain", "computing", "database", null, "ai"]) {
    await page.clock.fastForward(dwell);
    if (id) await expect(active).toHaveAttribute("data-id", id);
    else await expect(active).toHaveCount(0);
  }

  const database = stack.getByRole("button", { name: "Explore Graph Database" });
  const box = await database.boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.clock.runFor(160);
  await expect(active).toHaveAttribute("data-id", "database");
  await page.clock.fastForward(dwell);
  await expect(active).toHaveAttribute("data-id", "database");
  await page.mouse.move(1, 1);
  await page.clock.runFor(160);
  await page.clock.fastForward(dwell);
  await expect(active).toHaveAttribute("data-id", "toolchain");

  // Tab from the preceding hero link to give the first layer real keyboard focus.
  await page.locator("#hero .cta-row a").last().focus();
  await page.keyboard.press("Tab");
  const aiButton = stack.getByRole("button", { name: "Explore Graph AI" });
  await expect(aiButton).toBeFocused();
  await page.clock.fastForward(dwell);
  await expect(active).toHaveAttribute("data-id", "ai");

  const computingBox = await stack.getByRole("button", { name: "Explore Graph Computing" }).boundingBox();
  await page.mouse.move(computingBox.x + computingBox.width / 2, computingBox.y + computingBox.height / 2);
  await page.clock.runFor(160);
  await expect(active).toHaveAttribute("data-id", "computing");
  await page.mouse.move(1, 1);
  await page.clock.runFor(160);
  await expect(aiButton).toBeFocused();
  await expect(active).toHaveAttribute("data-id", "ai");

  for (const reducedMotion of ["reduce", "no-preference"]) {
    await page.emulateMedia({ reducedMotion });
    await page.clock.runFor(200);
    if (reducedMotion === "reduce") await expect(page.locator("#hg-landing")).not.toHaveClass(/\blive\b/);
    else await expect(page.locator("#hg-landing")).toHaveClass(/\blive\b/);
    await page.clock.fastForward(dwell);
    await expect(aiButton).toBeFocused();
    await expect(active).toHaveAttribute("data-id", "ai");
  }

  await page.keyboard.press("Shift+Tab");
  await expect(page.locator("#hero .cta-row a").last()).toBeFocused();
  await page.clock.runFor(200);
  await page.clock.fastForward(dwell);
  await expect(active).toHaveAttribute("data-id", "ai");
  await page.clock.fastForward(dwell);
  await expect(active).toHaveAttribute("data-id", "toolchain");

  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(page.locator("#hg-landing")).not.toHaveClass(/\blive\b/);
  await page.clock.fastForward(dwell);
  await expect(active).toHaveCount(0);
});

async function graphInkBrightness(canvas) {
  return canvas.evaluate(node => {
    const pixels = node.getContext("2d").getImageData(0, 0, node.width, node.height).data;
    let brightness = 0;
    let samples = 0;
    // Sample solid graph marks. Transparent space and translucent halos would
    // otherwise dominate the measurement on this sparse drawing.
    for (let i = 0; i < pixels.length; i += 16) {
      if (pixels[i + 3] < 200) continue;
      brightness += (pixels[i] + pixels[i + 1] + pixels[i + 2]) / 3;
      samples++;
    }
    return samples > 0 ? brightness / samples : null;
  });
}

function luminance(color) {
  const channels = color.match(/[\d.]+/g).slice(0, 3).map(Number).map(channel => {
    const n = channel / 255;
    return n <= 0.04045 ? n / 12.92 : ((n + 0.055) / 1.055) ** 2.4;
  });
  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
}

function contrast(foreground, background) {
  const a = luminance(foreground), b = luminance(background);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}

test("the appearance switch recolors the open graph and keeps homepage copy readable", async ({ page }) => {
  await page.goto("/");
  await page.locator('#hg-stack button[data-layer="0"]').click();
  const canvas = page.locator("#world");
  const panel = page.locator("#beat-database");
  await expect(panel).toHaveCSS("opacity", "1");
  await expect(canvas).toHaveCSS("opacity", "1");
  for (const theme of ["dark", "light"]) {
    await page.locator('[data-td-appearance-trigger][aria-controls="td-appearance-navbar"]').click();
    await page.locator(`#td-appearance-navbar [data-bs-theme-value="${theme}"]`).locator("..").click();
    await expect(page.locator("html")).toHaveAttribute("data-bs-theme", theme);
    await page.keyboard.press("Escape");
    await expect(panel).toBeInViewport();
    const readingSurface = await page.locator(".landing-content").evaluate(node => getComputedStyle(node).backgroundColor);
    await expect(page.locator("#veil")).toHaveCSS("background-color", readingSurface);
    await expect(page.locator(".td-site-header")).toHaveCSS("background-color", readingSurface);
    const ink = expect.poll(() => graphInkBrightness(canvas));
    if (theme === "dark") await ink.toBeGreaterThan(150);
    else await ink.toBeLessThan(100);

    const surfaces = await page.evaluate(() => {
      const card = "#capabilities .cap:not(.cap-efficient,.cap-ai,.cap-open)";
      return [["#beat-database .lede", "#veil"], [card + " p", card], ["#cmd", "#quickstart .cmd"]]
        .map(([text, surface]) => ({
          surface, foreground: getComputedStyle(document.querySelector(text)).color,
          background: getComputedStyle(document.querySelector(surface)).backgroundColor
        }));
    });
    for (const { surface, foreground, background } of surfaces) {
      const paper = luminance(background);
      if (theme === "dark" || surface === "#quickstart .cmd") expect(paper, surface).toBeLessThan(0.15);
      else expect(paper, surface).toBeGreaterThan(0.7);
      expect(contrast(foreground, background), surface).toBeGreaterThanOrEqual(4.5);
    }
  }
});

test("the copy button has a visible keyboard focus indicator on the command panel in both themes", async ({ page }) => {
  await page.goto("/");
  for (const theme of ["light", "dark"]) {
    await page.evaluate(value => window.OinkActions.run("switch_theme", { value }), theme);
    await expect(page.locator("html")).toHaveAttribute("data-bs-theme", theme);
    await page.locator("#cmd").focus();
    await page.keyboard.press("Tab");
    const copy = page.locator("#copy");
    await expect(copy).toBeFocused();
    const ring = await copy.evaluate(button => {
      const style = getComputedStyle(button);
      return { color: style.outlineColor, style: style.outlineStyle, width: parseFloat(style.outlineWidth),
        background: getComputedStyle(button.parentElement).backgroundColor };
    });
    expect(ring.style).not.toBe("none");
    expect(ring.width).toBeGreaterThanOrEqual(2);
    expect(contrast(ring.color, ring.background), theme).toBeGreaterThanOrEqual(3);
  }
});

// Media emulation skips native beforeprint/afterprint. A frame lets pending
// scroll and media change events reach the page before the next layout change.
async function emulateMediaAfterFrame(page, options) {
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(resolve)));
  await page.emulateMedia(options);
}

test("printing an active graph scene exposes all four explanations and restores the screen scene", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.goto("/");
  await expect(page.locator("#hg-stack")).toHaveClass(/hgs-live/);
  await page.locator('#hg-stack button[data-layer="3"]').press("Enter");
  const guide = page.locator("#beat-ai .story-guide");
  await expect(guide).toBeFocused();
  const scrollBeforePrint = await page.evaluate(() => scrollY);
  const guides = page.locator("#story .panel").getByRole("link");
  await expect(guides).toHaveCount(1);

  await emulateMediaAfterFrame(page, { media: "print" });
  await expect(guides).toHaveCount(4);
  await expect(page.locator("#story .panel").getByRole("heading", { level: 2 })).toHaveCount(4);
  await expect(page.locator("#story .panel[inert]")).toHaveCount(0);

  await emulateMediaAfterFrame(page, { media: "screen" });
  await expect(guides).toHaveCount(1);
  await expect(guide).toBeFocused();
  await expect(page.locator("#beat-ai")).toHaveCSS("opacity", "1");
  await expect.poll(() => page.evaluate(() => scrollY)).toBeCloseTo(scrollBeforePrint, 0);
});

test("dark reduced-motion diagrams follow appearance and print on paper", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce", colorScheme: "dark" });
  await page.goto("/cn/");
  await page.evaluate(() => window.OinkActions.run("switch_theme", { value: "auto" }));
  await expect(page.locator("html")).toHaveAttribute("data-bs-theme", "dark");
  await expectStaticStory(page);
  const still = page.locator("#beat-database .still");
  await expect.poll(() => graphInkBrightness(still)).toBeGreaterThan(150);
  await page.emulateMedia({ colorScheme: "light" });
  await expect(page.locator("html")).toHaveAttribute("data-bs-theme", "light");
  await expect.poll(() => graphInkBrightness(still)).toBeLessThan(100);

  const community = page.locator("#community");
  await community.scrollIntoViewIfNeeded();
  const contentTop = () => community.evaluate(node => node.getBoundingClientRect().top);
  const beforePrint = await contentTop();
  await emulateMediaAfterFrame(page, { colorScheme: "dark", media: "print" });
  await expect(page.locator("html")).toHaveAttribute("data-bs-theme", "dark");
  await expect(still).toBeHidden();
  await expect(page.locator("#beat-database .story-guide")).toBeVisible();
  await expect(page.locator("#hg-landing")).toHaveCSS("background-color", "rgb(255, 255, 255)");
  await expect(page.locator("#capabilities")).toHaveCSS("background-color", "rgb(255, 255, 255)");
  await emulateMediaAfterFrame(page, { media: "screen" });
  await expect.poll(contentTop).toBeCloseTo(beforePrint, 0);
});

test("a motion change during print preserves the community reading position", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.goto("/");
  const landing = page.locator("#hg-landing");
  const community = page.locator("#community");
  await community.scrollIntoViewIfNeeded();
  const top = () => community.evaluate(node => node.getBoundingClientRect().top);
  const before = await top();
  for (const reducedMotion of ["reduce", "no-preference"]) {
    await emulateMediaAfterFrame(page, { media: "print" });
    await emulateMediaAfterFrame(page, { reducedMotion });
    await emulateMediaAfterFrame(page, { media: "screen" });
    if (reducedMotion === "reduce") await expect(landing).not.toHaveClass(/\blive\b/);
    else await expect(landing).toHaveClass(/\blive\b/);
    await expect.poll(top).toBeCloseTo(before, 0);
  }
});

for (const position of ["north", "south"]) {
  test(`light travels along the ${position} constellation and follows motion preferences`, async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "no-preference" });
    await page.goto("/");
    const constellation = page.locator(`.hg-constellation--${position}`);
    const band = constellation.locator(".hg-star-band");
    await expect(band).toBeVisible();
    const mask = constellation.locator("mask");
    const maskId = await mask.getAttribute("id");
    await expect(band.locator("..")).toHaveCSS("mask-image", new RegExp(`#${maskId}["')]`));
    const routeLength = await mask.locator("path").evaluate(path => path.getTotalLength());
    expect(routeLength).toBeGreaterThan(0);

    const positions = await band.evaluate(node => {
      const [animation] = node.getAnimations();
      const { delay, duration } = animation.effect.getTiming();
      animation.pause();
      const samples = [0.25, 0.5, 0.75].map(fraction => {
        animation.currentTime = delay + duration * (1 + fraction);
        return new DOMMatrix(getComputedStyle(node).transform).m41;
      });
      animation.play();
      return samples;
    });
    expect(positions[0]).toBeLessThan(positions[1]);
    expect(positions[1]).toBeLessThan(positions[2]);
    await page.emulateMedia({ reducedMotion: "reduce" });
    await expect(band).toBeHidden();
    await expect.poll(() => constellation.evaluate(svg => svg.getAnimations({ subtree: true }).length)).toBe(0);
    await page.emulateMedia({ reducedMotion: "no-preference" });
    await expect(band).toHaveCSS("animation-play-state", "running");
    await page.locator('#hg-stack button[data-layer="0"]').click();
    await expect(band).toHaveCSS("animation-play-state", "paused");
  });
}
