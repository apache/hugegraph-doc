const { test, expect } = require("./artifact-test");

test.use({ locale: "en-US" });

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    if (!localStorage.getItem("hg-language")) localStorage.setItem("hg-language", "en");
    localStorage.setItem("td-color-theme", "light");
  });
});

async function openHome(page, prefix = "") {
  const response = await page.goto(`${prefix}/`);
  expect(response && response.ok()).toBeTruthy();
  await expect(page.locator("#hg-landing")).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
}

async function onScreen(locator) {
  return locator.evaluate(node => {
    const box = node.getBoundingClientRect();
    if (!(box.width > 0 && box.height > 0 && box.left >= 0 && box.right <= innerWidth + 1
      && box.top >= 0 && box.bottom <= innerHeight + 1)) return false;
    let opacity = 1;
    for (let parent = node; parent; parent = parent.parentElement) {
      const style = getComputedStyle(parent);
      opacity *= Number(style.opacity);
      if (style.visibility === "hidden" || style.display === "none") return false;
      const clip = parent.getBoundingClientRect();
      if (/(hidden|clip|auto|scroll)/.test(style.overflowX)
        && (box.left < clip.left - 1 || box.right > clip.right + 1)) return false;
      if (/(hidden|clip|auto|scroll)/.test(style.overflowY)
        && (box.top < clip.top - 1 || box.bottom > clip.bottom + 1)) return false;
    }
    return opacity >= 0.5;
  });
}

async function visibleStoryPanels(page) {
  return page.locator("#story .panel").evaluateAll(nodes => nodes.flatMap(node => {
    const style = getComputedStyle(node);
    const box = node.getBoundingClientRect();
    if (style.visibility === "hidden" || Number(style.opacity) <= 0.01
      || box.bottom <= 0 || box.top >= innerHeight) return [];
    return [{ id: node.id, opacity: Number(style.opacity), text: node.textContent.trim() }];
  }));
}

for (const [language, prefix, locale] of [["en", "", "en-US"], ["cn", "/cn", "zh-CN"]]) {
  test(`${language} homepage keeps the hero and primary action above later content`, async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    const errors = [];
    page.on("pageerror", error => errors.push(error.message));
    await openHome(page, prefix);
    await expect(page.locator("html")).toHaveAttribute("lang", locale);
    const heading = page.locator("#hero h1");
    await expect(heading).toBeVisible();
    await expect.poll(() => onScreen(heading)).toBe(true);
    const start = page.locator(`#hero a[href*="${prefix}/docs/quickstart/"]`).first();
    await expect(start).toBeVisible();
    await expect.poll(() => onScreen(start)).toBe(true);
    expect(await page.locator("#capabilities").evaluate(node => node.getBoundingClientRect().top))
      .toBeGreaterThanOrEqual(1000);
    await start.click();
    await expect(page).toHaveURL(url => url.pathname === `${prefix}/docs/quickstart/`);
    await expect(page.locator("main h1").first()).toBeVisible();
    expect(errors).toEqual([]);
  });

  test(`${language} component choices link to the corresponding local guides`, async ({ page }) => {
    await openHome(page, prefix);
    const platforms = page.locator("#components .platform-set").first();
    await expect(platforms.locator("li")).toHaveCount(10);
    await page.locator("#components summary").click();
    const guides = {
      Server: "hugegraph/hugegraph-server",
      PD: "hugegraph/hugegraph-pd",
      Store: "hugegraph/hugegraph-hstore",
      Hubble: "toolchain/hugegraph-hubble",
      Loader: "toolchain/hugegraph-loader",
      Tools: "toolchain/hugegraph-tools",
      Vermeer: "computing/hugegraph-vermeer",
      AI: "hugegraph-ai"
    };
    const directory = page.locator("#components");
    await expect(directory.getByRole("link")).toHaveCount(Object.keys(guides).length);
    const siteOrigin = new URL(await page.locator('link[rel="canonical"]').getAttribute("href"), page.url()).origin;
    for (const [name, guide] of Object.entries(guides)) {
      const link = directory.getByRole("link", { name, exact: true });
      const path = `${prefix}/docs/quickstart/${guide}/`;
      const url = new URL(await link.getAttribute("href"), page.url());
      expect([siteOrigin, new URL(page.url()).origin]).toContain(url.origin);
      expect(url.pathname + url.search + url.hash, name).toBe(path);
      const response = await page.request.get(path, { maxRedirects: 0 });
      expect(response.ok(), name).toBe(true);
    }
    const server = page.locator("#components").getByRole("link", { name: "Server", exact: true });
    const serverPath = `${prefix}/docs/quickstart/hugegraph/hugegraph-server/`;
    const serverGuide = language === "en" ? "HugeGraph Server Quick Start" : "HugeGraph Server 快速上手";
    await Promise.all([
      page.waitForURL(url => url.pathname === serverPath, { waitUntil: "domcontentloaded" }),
      server.click()
    ]);
    await expect(page.getByRole("heading", { name: serverGuide, level: 1, exact: true })).toBeVisible();
  });

  test(`${language} startup copies the complete command and offers a next step`, async ({ page, context }) => {
    await context.grantPermissions(["clipboard-read", "clipboard-write"]);
    await openHome(page, prefix);
    const command = (await page.locator("#cmd").textContent()).trim();
    expect(command).toMatch(/^docker run /);
    expect(command).not.toMatch(/^\$/);
    await page.locator("#copy").click();
    await expect.poll(() => page.evaluate(() => navigator.clipboard.readText())).toBe(command);
    await expect(page.locator("#copy-status")).toHaveText(/\S/);
    const next = page.locator("#quickstart a[href]").first();
    await expect(next).toBeVisible();
    expect(new URL(await next.getAttribute("href"), page.url()).pathname).toMatch(new RegExp(`^${prefix}/docs/`));
  });

  test(`${language} reduced motion preserves all four explanations and usable layer controls`, async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.setViewportSize({ width: 390, height: 844 });
    await openHome(page, prefix);
    const controls = page.locator("#hg-stack button[data-layer]");
    await expect(controls).toHaveCount(4);
    for (const control of await controls.all()) {
      await expect(control).toHaveAccessibleName(/\S/);
      expect((await control.textContent()).trim()).not.toBe("");
    }
    const explanations = page.locator("#story .panel");
    await expect(explanations).toHaveCount(4);
    for (const explanation of await explanations.all()) {
      await explanation.scrollIntoViewIfNeeded();
      await expect(explanation).toBeVisible();
      await expect(explanation.locator("h2")).toHaveText(/\S/);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  });
}

test("homepage language choice navigates to translated content and persists", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  // Use the published origin for this preference test so navigating a
  // canonical language link keeps localStorage on the same origin.
  await page.goto("https://hugegraph.apache.org/");
  await expect(page.locator("#hg-landing")).toBeVisible();
  const english = await page.locator("#hero h1").textContent();
  const language = page.locator(".td-site-header .td-site-nav__language");
  await language.locator(".td-language-selector__trigger").hover();
  await language.locator('ul a[hreflang="zh-CN"]').click();
  await expect(page).toHaveURL(url => url.pathname === "/cn/");
  await expect(page.locator("html")).toHaveAttribute("lang", "zh-CN");
  await expect(page.locator("#hero h1")).not.toHaveText(english);
  expect(await page.evaluate(() => localStorage.getItem("hg-language"))).toBe("cn");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("lang", "zh-CN");
  await expect(page.locator("#hero h1")).not.toHaveText(english);
  expect(await page.evaluate(() => localStorage.getItem("hg-language"))).toBe("cn");
});

test("320px homepage navigation remains reachable and Escape restores focus", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 844 });
  await openHome(page);
  const opener = page.locator("[data-td-landing-menu-toggle]");
  await expect(opener).toBeVisible();
  await expect.poll(() => onScreen(opener)).toBe(true);
  await opener.click();
  const drawer = page.locator("[data-td-landing-menu]");
  await expect(drawer).toBeVisible();
  await expect(drawer.locator('a[href*="/docs/"]').first()).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(drawer).toBeHidden();
  await expect(opener).toBeFocused();
  await expect(opener).toHaveAttribute("aria-expanded", "false");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
});

for (const viewport of [{ width: 1200, height: 900 }, { width: 1440, height: 700 }, { width: 320, height: 568 }, { width: 390, height: 844 }, { width: 844, height: 390 }]) {
  test(`${viewport.width}x${viewport.height} homepage retains a readable architecture`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await openHome(page);
    const diagram = page.locator("#hg-stack");
    const box = await diagram.boundingBox();
    expect(box.width).toBeGreaterThanOrEqual(200);
    expect(box.height).toBeGreaterThanOrEqual(200);
    const names = diagram.locator("button[data-layer] .hgs-lab-name");
    await expect(names).toHaveCount(4);
    for (const name of await names.all()) {
      await expect(name).toBeVisible();
      expect((await name.textContent()).trim()).not.toBe("");
      // A button may have a nonzero box even when its actual name is
      // hidden or clipped beyond the hero. Check what readers see.
      await expect.poll(() => onScreen(name)).toBe(true);
      expect((await name.boundingBox()).height).toBeGreaterThanOrEqual(12);
      const overlapsLauncher = await name.evaluate(node => {
        const launcher = document.querySelector(".hg-ask-ai-launcher");
        if (!launcher || !launcher.checkVisibility()) return false;
        const a = node.closest("button").getBoundingClientRect(), b = launcher.getBoundingClientRect();
        return a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
      });
      expect(overlapsLauncher).toBe(false);
      expect(await name.evaluate(node => {
        const button = node.closest("button"), box = button.getBoundingClientRect();
        return [box.left + 5, (box.left + box.right) / 2, box.right - 5].every(x =>
          button.contains(document.elementFromPoint(x, (box.top + box.bottom) / 2)));
      })).toBe(true);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  });
}

test("a painted slab eases into its stop and scrolling takes over", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await openHome(page);
  await expect(page.locator("#hg-stack")).toHaveClass(/hgs-live/);
  // The outer corner of the visible plate was outside the old rectangular hit overlay.
  const edge = await page.locator('.hgs-layer[data-id="ai"] .hgs-flat').evaluate(node => {
    const box = node.getBoundingClientRect();
    return { x: box.left + box.width * 0.08, y: box.top + box.height / 2 };
  });
  await page.evaluate(() => {
    window.travelPositions = [];
    const record = () => {
      window.travelPositions.push(scrollY);
      if (!document.querySelector("#beat-ai.on")) requestAnimationFrame(record);
    };
    addEventListener("click", () => requestAnimationFrame(record), { once: true });
  });
  await page.mouse.click(edge.x, edge.y);
  await expect(page.locator("#beat-ai")).toHaveClass(/\bon\b/);
  expect(await page.evaluate(() => new Set(window.travelPositions).size)).toBeGreaterThan(1);
  await page.mouse.wheel(0, -2200);
  await expect(page.locator("#beat-ai")).not.toHaveClass(/\bon\b/);
});

test("keyboard activation transfers focus to the selected graph layer", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await openHome(page);
  // During the first part of liftoff these controls have started fading but are still keyboard reachable.
  await page.locator("#story").evaluate(story => {
    const top = story.getBoundingClientRect().top + scrollY;
    scrollTo({ top: top + (story.offsetHeight - innerHeight) * 0.012, behavior: "instant" });
  });
  await expect(page.locator("#stage")).toHaveClass(/diving/);
  await page.locator('.hgs-lab[data-layer="0"]').press("Enter");
  const destination = page.locator("#beat-database .story-guide");
  await expect(destination).toBeFocused();
  await expect(page.locator(".hero-copy")).toBeHidden();
  await expect(page.locator(".hgs-labels")).toBeHidden();
});

test("progressive graph remains rendered while each stopped scene has one readable explanation", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await openHome(page);
  const frames = [];
  const scenes = [];
  for (const [progress, id] of [[0.20, "database"], [0.42, "toolchain"], [0.68, "computing"], [0.94, "ai"]]) {
    await page.locator("#story").evaluate((story, progress) => {
      const top = story.getBoundingClientRect().top + scrollY;
      scrollTo({ top: top + (story.offsetHeight - innerHeight) * progress, behavior: "instant" });
    }, progress);
    // The scene eases toward the real scroll position. Stopping mid-story
    // must settle into readable text rather than a perpetual cross-fade.
    await expect.poll(async () => (await visibleStoryPanels(page)).map(panel => panel.id)).toEqual([`beat-${id}`]);
    const [panel] = await visibleStoryPanels(page);
    expect(panel.opacity).toBeGreaterThanOrEqual(0.95);
    expect(panel.text).not.toBe("");
    scenes.push(panel.id);
    const canvas = page.locator("#world");
    await expect(canvas).toBeVisible();
    const frame = await canvas.evaluate(node => {
      const context = node.getContext("2d");
      const pixels = context.getImageData(0, 0, node.width, node.height).data;
      let drawn = 0;
      for (let i = 3; i < pixels.length; i += 16) if (pixels[i] > 16) drawn++;
      return { drawn, image: node.toDataURL() };
    });
    expect(frame.drawn).toBeGreaterThan(50);
    frames.push(frame.image);
  }
  expect(scenes).toEqual(["beat-database", "beat-toolchain", "beat-computing", "beat-ai"]);
  expect(new Set(frames).size).toBe(4);
});

test("blue hero fades to the reading surface before graph evolution and restores on reverse scroll", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openHome(page);
  const progress = async value => {
    await page.locator("#story").evaluate((story, value) => {
      scrollTo({ top: story.offsetTop + (story.offsetHeight - innerHeight) * value, behavior: "instant" });
    }, value);
  };
  const light = () => page.locator("#stage").evaluate(node =>
    Number(getComputedStyle(node).getPropertyValue("--scene-light")));
  await expect.poll(light).toBe(0);
  await progress(0.05);
  await expect.poll(light).toBeGreaterThan(0);
  expect(await light()).toBeLessThan(1);
  // Background conversion finishes before the first canvas graph appears.
  await progress(0.10);
  await expect.poll(light).toBe(1);
  await expect(page.locator("#world")).toHaveCSS("opacity", "0");
  await expect(page.locator("#beat-database")).toHaveCSS("opacity", "1");
  await expect(page.locator("#beat-database .story-guide")).toBeVisible();
  for (const [value, beat] of [[0.20, "database"], [0.42, "toolchain"], [0.68, "computing"], [0.94, "ai"]]) {
    await progress(value);
    await expect(page.locator(`#beat-${beat}`)).toHaveCSS("opacity", "1");
    expect(await light()).toBe(1);
    await expect(page.locator("#veil")).toHaveCSS("background-color", "rgb(243, 245, 251)");
    await expect(page.locator("#story .panel.on h2")).toHaveCSS("color", "rgb(20, 26, 51)");
  }
  await progress(0);
  await expect.poll(light).toBe(0);
  await expect(page.locator("#hero h1")).toBeVisible();
  await expect(page.locator("#hero h1")).toHaveCSS("color", "rgb(255, 255, 255)");
});
