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
    .filter({ hasText: "Releases" })
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
