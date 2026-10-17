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
    return ["slate", "paper"].flatMap(preset => ["light", "dark"].flatMap(theme => {
      const viewport = theme === "light" ? { width: 1440, height: 1000 } : { width: 390, height: 844 };
      return [
        [`${language}-upgrade-home-${preset}-${theme}`, `${prefix}/`, viewport, theme, "default", preset],
        [`${language}-upgrade-pd-${preset}-${theme}`, `${prefix}/docs/quickstart/hugegraph/hugegraph-pd/`, viewport, theme, "pd", preset],
        [`${language}-upgrade-helm-${preset}-${theme}`, `${prefix}/docs/quickstart/hugegraph/hugegraph-helm/`, viewport, theme, "helm", preset],
        [`${language}-upgrade-computer-${preset}-${theme}`, `${prefix}/docs/quickstart/computing/hugegraph-computer-config/`, viewport, theme, "computer", preset],
        [`${language}-upgrade-api-${preset}-${theme}`, `${prefix}/docs/quickstart/hugegraph-ai/config-reference/`, viewport, theme, "config-api", preset],
        [`${language}-upgrade-footer-${preset}-${theme}`, `${prefix}/blog/2025/10/09/toplingdb-quick-start/`,
          { width: 1440, height: 1000 }, theme, "footer", preset]
      ];
    }));
  }),
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
  }),
  ...["en", "cn"].flatMap(language => {
    const prefix = language === "cn" ? "/cn" : "";
    return ["desktop", "mobile"].flatMap(device => {
      const viewport = device === "desktop" ? { width: 1440, height: 1000 } : { width: 390, height: 844 };
      return [
        [`${language}-hubble-import-${device}`, `${prefix}/docs/quickstart/toolchain/hugegraph-hubble/`, viewport, "light", "hubble-import"],
        [`${language}-hubble-nodes-${device}`, `${prefix}/docs/quickstart/toolchain/visualization/hugegraph-hubble-hstore/`, viewport, "light", "hubble-nodes"]
      ];
    });
  })
];

for (const [name, url, viewport, theme, state, preset = "slate"] of states) {
  test(`capture advisory ${name}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.addInitScript(
      ({ theme, preset }) => {
        localStorage.setItem("td-color-theme", theme);
        localStorage.setItem("td-preset", preset);
      },
      { theme, preset }
    );
    await page.goto(url);
    await expect(page.locator("body")).toBeVisible();
    let sectionHeading;
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
    } else if (state === "hubble-import" || state === "hubble-nodes") {
      const chinese = url.startsWith("/cn/");
      const headingId = state === "hubble-import"
        ? (chinese ? "数据导入从字段映射到可查询的图" : "data-import-turn-fields-into-a-queryable-graph")
        : (chinese ? "节点详情读什么" : "read-node-details");
      const heading = page.locator(`[id="${headingId}"]`);
      sectionHeading = heading;
      await expect(heading).toBeVisible();
      await heading.scrollIntoViewIfNeeded();
      await page.waitForLoadState("networkidle");
      await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    } else if (state === "pd") {
      // Content-based selection works for both the old local class and native wide tables.
      const table = page.locator(".td-content table").filter({ hasText: "HG_PD_AUTH_SECRET_KEY" });
      const viewport = table.locator("..");
      await viewport.scrollIntoViewIfNeeded();
      // Compare the explanation column, not just the identifiers at the left edge.
      await viewport.evaluate(node => { node.scrollLeft = node.scrollWidth; });
      await expect(table).toBeVisible();
    } else if (state === "computer" || state === "config-api") {
      const token = state === "computer" ? "worker.vertex_properties_combiner_class" : "LITELLM_TEXT2GQL_LANGUAGE_MODEL";
      const table = page.locator(".td-content table").filter({ hasText: token });
      await table.locator("..").scrollIntoViewIfNeeded();
      await expect(table).toBeVisible();
    } else if (state === "helm") {
      const tree = page.locator(".td-filetree").filter({ hasText: "values-single.yaml" });
      await tree.scrollIntoViewIfNeeded();
      await expect(tree).toBeVisible();
    } else if (state === "footer") {
      await page.locator("footer").scrollIntoViewIfNeeded();
      await expect(page.locator(".td-shell-toc__panel")).toBeVisible();
      await expect.poll(() => page.evaluate(() => window.scrollY + innerHeight >= document.documentElement.scrollHeight - 2)).toBe(true);
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
    const directory = process.env.VISUAL_RESULTS_DIR
      ? path.resolve(process.env.VISUAL_RESULTS_DIR) : path.join(__dirname, "visual-results");
    fs.mkdirSync(directory, { recursive: true });
    await page.evaluate(async () => {
      await document.fonts.ready;
      await Promise.all(Array.from(document.images).filter(image => {
        const rect = image.getBoundingClientRect();
        return rect.bottom > 0 && rect.top < innerHeight;
      }).map(image => image.decode().catch(() => {})));
      await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    });
    if (sectionHeading) {
      // Align after fonts and lazy images settle; compare the same section,
      // not unchanged page headers or different points in the article.
      await expect(async () => {
        await sectionHeading.evaluate(async node => {
          window.scrollTo({ top: window.scrollY + node.getBoundingClientRect().top - 108, behavior: "instant" });
          await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        });
        expect(await sectionHeading.evaluate(node => Math.abs(node.getBoundingClientRect().top - 108))).toBeLessThan(2);
      }).toPass();
    }
    await page.screenshot({
      animations: "disabled",
      path: path.join(directory, `${name}.png`),
      fullPage: !["gallery", "chart", "longcode", "markmap", "terminal", "math", "pd", "computer", "config-api", "helm", "footer", "hubble-import", "hubble-nodes"].includes(state)
    });
    if (sectionHeading) {
      expect(await sectionHeading.evaluate(node => Math.abs(node.getBoundingClientRect().top - 108))).toBeLessThan(2);
    }
  });
}
