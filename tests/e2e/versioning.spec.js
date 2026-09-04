const { test, expect } = require("./artifact-test");

const VERSION_IDS = ["latest", "1.7", "1.5", "1.3", "1.0"];
const EXPECTED_IDS = (process.env.EXPECTED_VERSIONS || VERSION_IDS.join(",")).split(",");

async function actionManifest(page) {
  return page.locator("#td-action-manifest").evaluate((node) => JSON.parse(node.textContent));
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
