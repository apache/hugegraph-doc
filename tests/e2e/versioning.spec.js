const { test, expect } = require("./artifact-test");

const VERSION_IDS = ["latest", "1.7", "1.5", "1.3", "1.0"];
const EXPECTED_IDS = (process.env.EXPECTED_VERSIONS || VERSION_IDS.join(",")).split(",");

async function actionManifest(page) {
  return page.locator("#td-action-manifest").evaluate((node) => JSON.parse(node.textContent));
}

async function versionOption(page, id) {
  const manifest = await actionManifest(page);
  return manifest.actions
    .find((item) => item.id === "switch_version")
    .options.find((item) => item.id === id);
}

test("aggregate records the immutable five-version manifest", async ({ request }) => {
  const response = await request.get("/build-metadata/versions.json");
  expect(response.ok()).toBeTruthy();
  const manifest = await response.json();
  expect(manifest.schemaVersion).toBe(1);
  expect(manifest.versions.map((entry) => entry.id)).toEqual(EXPECTED_IDS);
  for (const entry of manifest.versions) {
    expect(entry.sha).toMatch(/^[0-9a-f]{40}$/);
  }
});

for (const locale of ["en", "cn"]) {
  test(`latest ${locale} exposes the fixed version order`, async ({ page }) => {
    await page.goto(locale === "cn" ? "/cn/docs/" : "/docs/");
    const manifest = await actionManifest(page);
    const action = manifest.actions.find((item) => item.id === "switch_version");
    expect(action.options.map((item) => item.id)).toEqual(VERSION_IDS);
  });
}

for (const version of VERSION_IDS.slice(1)) {
  for (const locale of ["en", "cn"]) {
    test(`${version} ${locale} is archived and directly reachable`, async ({ page }) => {
      test.skip(!EXPECTED_IDS.includes(version), "latest-only staging artifact");
      const prefix = `/versions/${version}${locale === "cn" ? "/cn" : ""}`;
      await page.goto(`${prefix}/docs/`);
      await expect(page.locator('meta[name="robots"]')).toHaveAttribute(
        "content",
        /noindex\s*,?\s*follow/i
      );
      await expect(page.locator(".td-page-notice--primary")).toBeVisible();
      const manifest = await actionManifest(page);
      const action = manifest.actions.find((item) => item.id === "switch_version");
      expect(action.options.map((item) => item.id)).toEqual(VERSION_IDS);
    });
  }
}

// Historical content shares the current theme; its technical catalogue needs
// the same authored layout policy without changing archived option values.
for (const version of VERSION_IDS.slice(1)) {
  for (const locale of ["en", "cn"]) {
    test(`${version} ${locale} archived configuration catalogues keep mobile identifiers readable`, async ({ page }) => {
      test.skip(!EXPECTED_IDS.includes(version), "latest-only staging artifact");
      await page.setViewportSize({ width: 390, height: 844 });
      const prefix = `/versions/${version}${locale === "cn" ? "/cn" : ""}`;
      await page.goto(`${prefix}/docs/config/config-option/`);
      for (const details of await page.locator(".td-content details").all()) {
        if (!await details.evaluate(node => node.open)) await details.locator(":scope > summary").click();
      }
      await page.evaluate(() => document.fonts.ready);
      const tables = page.locator(".td-content table");
      expect(await tables.count()).toBeGreaterThan(0);
      // Counts and optional sections differ between immutable releases.
      await expect(page.locator(".td-content table:not(.td-table--wide)")).toHaveCount(0);
      for (const key of ["gremlin.graph", "rocksdb.data_path"]) {
        const cell = page.locator(".td-content tbody tr > td:first-child")
          .filter({ hasText: new RegExp(`^\\s*${key.replaceAll(".", "\\.")}\\s*$`) });
        await expect(cell).toHaveCount(1);
        const wrapper = cell.locator("xpath=ancestor::div[contains(concat(' ', normalize-space(@class), ' '), ' td-table-scroll ')][1]");
        await wrapper.scrollIntoViewIfNeeded();
        const measurement = await cell.evaluate(node => {
          const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
          const tops = [];
          let text;
          while ((text = walker.nextNode())) {
            if (!text.textContent.trim()) continue;
            const range = document.createRange();
            range.selectNodeContents(text);
            for (const rectangle of range.getClientRects()) {
              if (!tops.some(top => Math.abs(top - rectangle.top) < 1)) tops.push(rectangle.top);
            }
          }
          return { lines: tops.length, font: parseFloat(getComputedStyle(node).fontSize) };
        });
        expect(measurement.lines, key).toBe(1);
        expect(measurement.font, key).toBeGreaterThanOrEqual(14);
        expect(await wrapper.evaluate(node => node.scrollWidth > node.clientWidth + 1)).toBe(true);
        await expect(wrapper).toHaveAttribute("tabindex", "0");
        await wrapper.focus();
        await wrapper.press("ArrowRight");
        await expect.poll(() => wrapper.evaluate(node => node.scrollLeft)).toBeGreaterThan(0);
      }
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    });
  }
}

const archivedReferenceCatalogues = [
  [VERSION_IDS.slice(1), 'quickstart/toolchain/hugegraph-tools', 1, [['HUGEGRAPH_TRUST_STORE_PASSWORD', 1]]],
  [VERSION_IDS.slice(1), 'quickstart/toolchain/hugegraph-loader', 1, [['single-insert-threads', 1]]],
  [['1.7'], 'clients/restful-api/graphspace', 2, [['internal_algorithm_image_url', 2]]],
  [['1.7'], 'quickstart/toolchain/hugegraph-hubble', 1, [['gremlin.vertex_degree_limit', 1]]],
  [['1.7'], 'quickstart/hugegraph-ai/config-reference', 3, [
    ['OPENAI_TEXT2GQL_LANGUAGE_MODEL', 1], ['LITELLM_TEXT2GQL_LANGUAGE_MODEL', 1], ['OLLAMA_TEXT2GQL_LANGUAGE_MODEL', 1]
  ]],
  [['1.7'], 'quickstart/hugegraph/hugegraph-pd', 1, [['HG_PD_INITIAL_STORE_COUNT', 1]]],
  [['1.7'], 'quickstart/hugegraph/hugegraph-hstore', 1, [['HG_STORE_RAFT_ADDRESS', 1]]]
];

for (const [versions, route, wideCount, identifiers] of archivedReferenceCatalogues) {
  for (const version of versions) {
    for (const locale of ['en', 'cn']) {
      test(`${version} ${locale} archived technical reference ${route} keeps mobile identifiers readable`, async ({ page }) => {
        test.skip(!EXPECTED_IDS.includes(version), 'latest-only staging artifact');
        await page.setViewportSize({ width: 390, height: 844 });
        await page.goto(`/versions/${version}${locale === 'cn' ? '/cn' : ''}/docs/${route}/`);
        await page.evaluate(() => document.fonts.ready);
        const tables = page.locator('.td-content table.td-table--wide');
        await expect(tables).toHaveCount(wideCount);
        for (const [identifier, expectedTables] of identifiers) {
          const matchingTables = tables.filter({ hasText: identifier });
          await expect(matchingTables, identifier).toHaveCount(expectedTables);
          const cells = matchingTables.locator('tbody td').filter({ hasText: identifier });
          const measurements = await cells.evaluateAll((nodes, identifier) => nodes.flatMap(node => {
            const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
            const results = [];
            let text;
            while ((text = walker.nextNode())) {
              const start = text.textContent.indexOf(identifier);
              if (start < 0) continue;
              const range = document.createRange();
              range.setStart(text, start);
              range.setEnd(text, start + identifier.length);
              results.push({ lines: new Set(Array.from(range.getClientRects(), rect => Math.round(rect.top))).size,
                font: parseFloat(getComputedStyle(text.parentElement).fontSize) });
            }
            return results;
          }), identifier);
          expect(measurements.length, identifier).toBeGreaterThan(0);
          for (const measurement of measurements) {
            expect(measurement.lines, identifier).toBe(1);
            expect(measurement.font, identifier).toBeGreaterThanOrEqual(14);
          }
        }
        for (const table of await tables.all()) {
          const wrapper = table.locator('..');
          await wrapper.scrollIntoViewIfNeeded();
          if (await wrapper.evaluate(node => node.scrollWidth > node.clientWidth + 1)) {
            await expect(wrapper).toHaveAttribute('tabindex', '0');
            await wrapper.focus();
            await wrapper.press('ArrowRight');
            await expect.poll(() => wrapper.evaluate(node => node.scrollLeft)).toBeGreaterThan(0);
          }
        }
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
      });
    }
  }
}

test("1.0 flat Server URL remains a static alias", async ({ request }) => {
  test.skip(!EXPECTED_IDS.includes("1.0"), "latest-only staging artifact");
  const response = await request.get(
    "/versions/1.0/docs/quickstart/hugegraph-server/"
  );
  expect(response.ok()).toBeTruthy();
  const body = await response.text();
  expect(body).toMatch(
    /http-equiv="refresh"[^>]+quickstart\/hugegraph\/hugegraph-server/
  );
  expect(body).toMatch(
    /rel="canonical"[^>]+versions\/1\.0\/docs\/quickstart\/hugegraph\/hugegraph-server\//
  );
});

test("desktop and mobile selectors preserve query and hash for an equivalent page", async ({
  page
}) => {
  test.skip(!EXPECTED_IDS.includes("1.7"), "latest-only staging artifact");
  await page.goto("/docs/quickstart/hugegraph/?query=server#server");
  const option = await versionOption(page, "1.7");
  expect(option.equivalent).toBe(true);
  expect(option.fallback).toBe(false);

  const desktop = page.locator(
    ".td-nav-version-menu a[data-hg-version-id='1.7']"
  );
  const href = await desktop.getAttribute("href");
  expect(new URL(href).search).toBe("?query=server");
  expect(new URL(href).hash).toBe("#server");
  expect(new URL(href).pathname).toBe(new URL(option.url).pathname);
  await page.locator(".td-nav-version-menu [data-td-nav-hover-trigger]").hover();
  await expect(desktop).toBeVisible();
  await desktop.click();
  await expect(page).toHaveURL((url) =>
    url.pathname === new URL(option.url).pathname &&
    url.search === "?query=server" &&
    url.hash === "#server"
  );

  await page.goto("/docs/quickstart/hugegraph/?query=server#server");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator("[data-td-shell-drawer-open]").click();
  const drawer = page.locator(
    "#td-shell-sidebar a[data-hg-version-id='1.7']"
  );
  await expect(drawer).toHaveAttribute("href", href);
  await drawer.click();
  await expect(page).toHaveURL((url) =>
    url.pathname === new URL(option.url).pathname &&
    url.search === "?query=server" &&
    url.hash === "#server"
  );
});

test("Palette version choice uses the same equivalent target", async ({ page }) => {
  test.skip(!EXPECTED_IDS.includes("1.7"), "latest-only staging artifact");
  await page.goto("/docs/quickstart/hugegraph/?query=server#server");
  const option = await versionOption(page, "1.7");
  await page.locator("[data-td-shell-search-open]").first().click();
  const input = page.locator(".td-shell-search__input");
  await input.fill("Releases");
  await page
    .locator('[role="option"]')
    .filter({ hasText: /^Releases$/ })
    .first()
    .click();
  await page
    .locator('[role="option"]')
    .filter({ hasText: /^1\.7$/ })
    .click();
  await expect(page).toHaveURL((url) =>
    url.pathname === new URL(option.url).pathname &&
    url.search === "?query=server" &&
    url.hash === "#server"
  );
});

test("historical selectors preserve the readme route across desktop, mobile, and Palette", async ({
  page
}) => {
  test.skip(
    !["1.7", "1.5", "1.3"].every((version) => EXPECTED_IDS.includes(version)),
    "latest-only staging artifact"
  );

  await page.goto(
    "/versions/1.7/docs/introduction/readme/?query=history#overview"
  );
  let option = await versionOption(page, "1.5");
  expect(option.equivalent).toBe(true);
  expect(option.fallback).toBe(false);
  expect(new URL(option.url).pathname).toBe(
    "/versions/1.5/docs/introduction/readme/"
  );
  const desktop = page.locator(
    ".td-nav-version-menu a[data-hg-version-id='1.5']"
  );
  await page.locator(".td-nav-version-menu [data-td-nav-hover-trigger]").hover();
  await desktop.click();
  await expect(page).toHaveURL((url) =>
    url.pathname === "/versions/1.5/docs/introduction/readme/" &&
    url.search === "?query=history" &&
    url.hash === "#overview"
  );

  await page.goto(
    "/versions/1.7/cn/docs/introduction/readme/?query=history#overview"
  );
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator("[data-td-shell-drawer-open]").click();
  const mobile = page.locator(
    "#td-shell-sidebar a[data-hg-version-id='1.3']"
  );
  await page.locator("#td-shell-sidebar .hg-version-overflow summary").click();
  await mobile.click();
  await expect(page).toHaveURL((url) =>
    url.pathname === "/versions/1.3/cn/docs/introduction/readme/" &&
    url.search === "?query=history" &&
    url.hash === "#overview"
  );

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(
    "/versions/1.3/docs/introduction/readme/?query=history#overview"
  );
  option = await versionOption(page, "1.5");
  expect(new URL(option.url).pathname).toBe(
    "/versions/1.5/docs/introduction/readme/"
  );
  await page.locator("[data-td-shell-search-open]").first().click();
  const input = page.locator(".td-shell-search__input");
  await input.fill("Releases");
  await page
    .locator('[role="option"]')
    .filter({ hasText: /^Releases$/ })
    .first()
    .click();
  await page
    .locator('[role="option"]')
    .filter({ hasText: /^1\.5$/ })
    .click();
  await expect(page).toHaveURL((url) =>
    url.pathname === "/versions/1.5/docs/introduction/readme/" &&
    url.search === "?query=history" &&
    url.hash === "#overview"
  );
});

test("introduction aliases resolve bidirectionally without merging canonical pages", async ({
  page
}) => {
  test.skip(
    !["1.7", "1.5", "1.3", "1.0"].every((version) =>
      EXPECTED_IDS.includes(version)
    ),
    "latest-only staging artifact"
  );

  await page.goto("/docs/introduction/?query=history#overview");
  let option = await versionOption(page, "1.5");
  expect(option.equivalent).toBe(true);
  expect(option.fallback).toBe(false);
  expect(new URL(option.url).pathname).toBe(
    "/versions/1.5/docs/introduction/readme/"
  );
  await page.locator(".td-nav-version-menu [data-td-nav-hover-trigger]").hover();
  await page
    .locator(".td-nav-version-menu a[data-hg-version-id='1.5']")
    .click();
  await expect(page).toHaveURL((url) =>
    url.pathname === "/versions/1.5/docs/introduction/readme/" &&
    url.search === "?query=history" &&
    url.hash === "#overview"
  );

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/cn/docs/introduction/?query=history#overview");
  await page.locator("[data-td-shell-drawer-open]").click();
  await page.locator("#td-shell-sidebar .hg-version-overflow summary").click();
  await page
    .locator("#td-shell-sidebar a[data-hg-version-id='1.3']")
    .click();
  await expect(page).toHaveURL((url) =>
    url.pathname === "/versions/1.3/cn/docs/introduction/readme/" &&
    url.search === "?query=history" &&
    url.hash === "#overview"
  );

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(
    "/versions/1.7/docs/introduction/readme/?query=history#overview"
  );
  option = await versionOption(page, "latest");
  expect(new URL(option.url).pathname).toBe("/docs/introduction/");
  await page.locator("[data-td-shell-search-open]").first().click();
  await page.locator(".td-shell-search__input").fill("Releases");
  await page
    .locator('[role="option"]')
    .filter({ hasText: /^Releases$/ })
    .first()
    .click();
  await page
    .locator('[role="option"]')
    .filter({ hasText: /^latest$/ })
    .click();
  await expect(page).toHaveURL((url) =>
    url.pathname === "/docs/introduction/" &&
    url.search === "?query=history" &&
    url.hash === "#overview"
  );

  for (const locale of ["en", "cn"]) {
    const prefix = locale === "cn" ? "/cn" : "";
    await page.goto(`/versions/1.7${prefix}/docs/introduction/`);
    option = await versionOption(page, "latest");
    expect(new URL(option.url).pathname).toBe(
      `${prefix}/docs/introduction/`
    );
    expect(option.equivalent).toBe(true);
    expect(option.fallback).toBe(false);
  }
});

for (const locale of ["en", "cn"]) {
  test(`${locale} missing page falls back to its docs root once`, async ({ page }) => {
    test.skip(!EXPECTED_IDS.includes("1.0"), "latest-only staging artifact");
    const prefix = locale === "cn" ? "/cn" : "";
    await page.goto(`${prefix}/docs/guides/security/?query=discard#discard`);
    const option = await versionOption(page, "1.0");
    expect(option.fallback).toBe(true);
    expect(option.equivalent).toBe(false);
    expect(new URL(option.url).pathname).toBe(`/versions/1.0${prefix}/docs/`);
    expect(new URL(option.url).search).toBe("");
    expect(new URL(option.url).hash).toBe("#hg-version-fallback");

    await page.evaluate((target) => {
      window.OinkActions.run("switch_version", { value: target });
    }, option);
    await page.waitForURL((url) => url.pathname === `/versions/1.0${prefix}/docs/`);
    await expect(
      page.locator("[data-hg-version-fallback-notice]")
    ).toHaveCount(1);
    expect(new URL(page.url()).search).toBe("");
    expect(new URL(page.url()).hash).toBe("");
    await page.reload();
    await expect(
      page.locator("[data-hg-version-fallback-notice]")
    ).toHaveCount(0);
  });
}
