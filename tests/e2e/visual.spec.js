const { test, expect } = require("./artifact-test");
const fs = require("node:fs");
const path = require("node:path");

const states = [
  ["en-docs-desktop-light", "/docs/", { width: 1440, height: 900 }, "light", "default"],
  ["cn-docs-desktop-dark", "/cn/docs/", { width: 1440, height: 900 }, "dark", "default"],
  ["en-search-desktop-light", "/docs/", { width: 1440, height: 900 }, "light", "search"],
  ["cn-search-mobile-dark", "/cn/docs/", { width: 390, height: 844 }, "dark", "search"],
  ["en-sidebar-desktop-light", "/docs/introduction/", { width: 1440, height: 900 }, "light", "collapse"],
  ["cn-sidebar-mobile-dark", "/cn/docs/", { width: 390, height: 844 }, "dark", "drawer"],
  ["en-community-desktop-light", "/community/", { width: 1440, height: 900 }, "light", "default"],
  ["cn-community-mobile-dark", "/cn/community/", { width: 320, height: 720 }, "dark", "default"],
  ["en-appearance-desktop-light", "/docs/introduction/", { width: 1440, height: 900 }, "light", "appearance"],
  ["cn-appearance-mobile-dark", "/cn/docs/introduction/", { width: 390, height: 844 }, "dark", "appearance"],
  ["en-paper-desktop-light", "/docs/introduction/", { width: 1440, height: 900 }, "light", "paper"],
  ["cn-paper-mobile-dark", "/cn/docs/introduction/", { width: 390, height: 844 }, "dark", "paper"],
  ...["en", "cn"].flatMap(language => {
    const prefix = language === "cn" ? "/cn" : "";
    return [
      [`${language}-adopted-blog-desktop`, `${prefix}/blog/`, { width: 1440, height: 1000 }, "light", "blog"],
      [`${language}-adopted-toplingdb-desktop`, `${prefix}/blog/2025/10/09/toplingdb-quick-start/`, { width: 1440, height: 1000 }, "light", "series"],
      [`${language}-adopted-rocksdb-desktop`, `${prefix}/docs/config/config-backend-rocksdb/`, { width: 1440, height: 1000 }, "light", "filetree"],
      [`${language}-adopted-server-desktop`, `${prefix}/docs/quickstart/hugegraph/hugegraph-server/`, { width: 1440, height: 1000 }, "light", "cards"],
      [`${language}-adopted-tools-mobile`, `${prefix}/docs/quickstart/toolchain/hugegraph-tools/`, { width: 390, height: 844 }, "light", "tabs"]
    ];
  }),
  ...["en", "cn"].flatMap(language => {
    const prefix = language === "cn" ? "/cn" : "";
    return [
      [`${language}-selected-hubble-gallery`, `${prefix}/docs/quickstart/toolchain/hugegraph-hubble/`, { width: 1440, height: 1000 }, "light", "gallery"],
      [`${language}-selected-historical-chart`, `${prefix}/docs/performance/hugegraph-benchmark-0.5.6/`, { width: 1440, height: 1000 }, "light", "chart"],
      [`${language}-selected-code-mobile`, `${prefix}/docs/quickstart/hugegraph/hugegraph-server/`, { width: 390, height: 844 }, "light", "longcode"],
      [`${language}-selected-map-narrow-mobile`, `${prefix}/docs/quickstart/hugegraph/hugegraph-server/`, { width: 320, height: 844 }, "light", "markmap"],
      [`${language}-selected-map-narrow-mobile-dark`, `${prefix}/docs/quickstart/hugegraph/hugegraph-server/`, { width: 320, height: 844 }, "dark", "markmap"],
      [`${language}-selected-map-mobile-dark`, `${prefix}/docs/quickstart/hugegraph/hugegraph-server/`, { width: 390, height: 844 }, "dark", "markmap"],
      [`${language}-selected-map-mobile`, `${prefix}/docs/quickstart/hugegraph/hugegraph-server/`, { width: 390, height: 844 }, "light", "markmap"],
      [`${language}-selected-terminal-mobile`, `${prefix}/community/documentation/`, { width: 390, height: 844 }, "light", "terminal"],
      [`${language}-selected-jaccard-math`, `${prefix}/docs/clients/restful-api/traverser/`, { width: 1440, height: 1000 }, "light", "math"]
    ];
  })
];

for (const [name, url, viewport, theme, state] of states) {
  test(`capture advisory ${name}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.addInitScript(
      (value) => localStorage.setItem("td-color-theme", value),
      theme
    );
    await page.goto(url);
    await expect(page.locator("body")).toBeVisible();
    if (["gallery", "chart", "longcode", "markmap", "terminal", "math"].includes(state)) {
      const selector = { gallery: ".td-gallery", chart: "[data-td-echarts-canvas]",
        longcode: "[data-td-collapse-lines]", markmap: ".markmap svg",
        terminal: "[data-td-asciinema]", math: ".katex-display" }[state];
      const component = page.locator(selector).first();
      if (state === "terminal") {
        const optionalDemo = page.locator("details").filter({ has: component });
        await expect(optionalDemo).not.toHaveAttribute("open", "");
        await optionalDemo.locator(":scope > summary").click();
      }
      await component.scrollIntoViewIfNeeded();
      await expect(component).toBeVisible();
      if (state === "gallery") {
        for (const image of await component.locator("img").all()) {
          await expect.poll(() => image.evaluate(node => node.complete && node.naturalWidth > 0)).toBe(true);
        }
      } else if (state === "chart") {
        await expect(component.locator("canvas")).toBeVisible();
        // Canvas creation precedes ECharts' initial bar animation. Wait for
        // the actual renderer to finish so the capture shows final data heights.
        await expect.poll(() => component.evaluate(node => {
          const chart = window.echarts.getInstanceByDom(node);
          return Boolean(chart && chart.getZr().animation.isFinished());
        })).toBe(true);
      }
      else if (state === "markmap") {
        // Ensure the fit animation has settled into legible labels before capture.
        await expect.poll(() => component.locator("foreignObject").evaluateAll(nodes => nodes.every(node => {
          const matrix = node.getScreenCTM();
          const text = node.querySelector("div");
          const bounds = node.getBoundingClientRect();
          return parseFloat(getComputedStyle(text).fontSize) * Math.hypot(matrix.a, matrix.b) >= 12 &&
            bounds.left >= 0 && bounds.right <= innerWidth;
        }))).toBe(true);
      }
      else if (state === "terminal") {
        await component.locator(".ap-overlay-start .ap-play-button").click();
        await expect(component).toContainText("github.com/pgsty/oink@v1.2.0", { timeout: 15000 });
        // Measure text after fit-to-width scaling, which CSS font-size alone misses.
        await expect.poll(() => component.locator(".ap-term-text .ap-line span").first()
          .evaluate(node => node.getBoundingClientRect().height)).toBeGreaterThanOrEqual(11);
      }
      await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    } else if (state === "series") {
      await page.locator('.td-series-strip summary').press('Enter');
      await expect(page.locator('.td-series-strip__list')).toBeVisible();
    } else if (["filetree", "cards", "tabs", "blog"].includes(state)) {
      const component = page.locator({ filetree: ".td-filetree", cards: ".td-content ul.cards",
        tabs: ".td-tabs", blog: ".td-blog-card" }[state]).first();
      await expect(component).toBeVisible();
      if (state !== "blog") await component.scrollIntoViewIfNeeded();
      if (state === "tabs") await component.getByRole('tab').nth(1).click();
      if (state === "blog") {
        await expect.poll(() => component.locator('.td-blog-card__image')
          .evaluate(image => image.complete && image.naturalWidth > 0)).toBe(true);
      }
    } else if (state === "appearance" || state === "paper") {
      await page.locator('[data-td-appearance-trigger][aria-controls="td-appearance-navbar"]').click();
      const panel = page.locator("#td-appearance-navbar");
      await expect(panel).toBeVisible();
      if (state === "paper") {
        await panel.locator('[data-td-preset-value="paper"]').locator("..").click();
        await expect(page.locator("html")).toHaveAttribute("data-td-preset", "paper");
        await page.keyboard.press("Escape");
      }
    } else if (state === "search") {
      await page.locator("[data-td-shell-search-open]").first().click();
      await page.locator(".td-shell-search__input").fill(url.startsWith("/cn/") ? "服务端" : "server");
      await expect(page.locator('[role="option"]').first()).toBeVisible();
    } else if (state === "collapse") {
      await page.locator(".td-shell-sidebar__collapse").click();
      await expect(page.locator("html")).toHaveAttribute("data-td-shell-sidebar", "collapsed");
    } else if (state === "drawer") {
      await page.locator("[data-td-shell-drawer-open]").click();
      await expect(page.locator("html")).toHaveAttribute("data-td-shell-drawer", "open");
    }
    const directory = path.join(__dirname, "visual-results");
    fs.mkdirSync(directory, { recursive: true });
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({
      animations: "disabled",
      path: path.join(directory, `${name}.png`),
      fullPage: !["gallery", "chart", "longcode", "markmap", "terminal", "math"].includes(state)
    });
  });
}
