const { test, expect } = require("./artifact-test");
const fs = require("node:fs");
const path = require("node:path");

const FALLBACK_CASES = {
  en: [
    ["introduction", "/docs/introduction/"],
    ["server", "/docs/quickstart/hugegraph/hugegraph-server/"],
    ["hstore", "/docs/quickstart/hugegraph/hugegraph-hstore/"],
    ["placement driver", "/docs/quickstart/hugegraph/hugegraph-pd/"],
    ["computer", "/docs/quickstart/computing/hugegraph-computer/"],
    ["loader", "/docs/quickstart/toolchain/hugegraph-loader/"],
    ["hubble", "/docs/quickstart/toolchain/hugegraph-hubble/"],
    ["clients", "/docs/clients/"],
    ["rest api", "/docs/clients/restful-api/"],
    ["configuration", "/docs/config/"],
    ["authentication", "/docs/config/config-authentication/"],
    ["download", "/docs/download/download/"]
  ],
  cn: [
    ["介绍", "/cn/docs/introduction/"],
    ["服务端", "/cn/docs/quickstart/hugegraph/hugegraph-server/"],
    ["HStore", "/cn/docs/quickstart/hugegraph/hugegraph-hstore/"],
    ["PD", "/cn/docs/quickstart/hugegraph/hugegraph-pd/"],
    ["图计算", "/cn/docs/quickstart/computing/hugegraph-computer/"],
    ["数据导入", "/cn/docs/quickstart/toolchain/hugegraph-loader/"],
    ["图形化界面", "/cn/docs/quickstart/toolchain/hugegraph-hubble/"],
    ["客户端", "/cn/docs/clients/"],
    ["REST API", "/cn/docs/clients/restful-api/"],
    ["配置", "/cn/docs/config/"],
    ["认证", "/cn/docs/config/config-authentication/"],
    ["下载", "/cn/docs/download/download/"]
  ]
};

const metadataFixture = path.resolve(__dirname, "../../scripts/fixtures/community_search_queries.json");
const metadataIntegrated = fs.existsSync(metadataFixture);
const siteRoot = process.env.SITE_ROOT;
const rawCases = metadataIntegrated
  ? Object.groupBy(
      JSON.parse(fs.readFileSync(metadataFixture, "utf8")).map((entry) => [
        entry.query,
        entry.expected_ref
      ]),
      ([query, expectedRef]) => (expectedRef.startsWith("/cn/") ? "cn" : "en")
    )
  : FALLBACK_CASES;
const cases = Object.fromEntries(
  Object.entries(rawCases).map(([locale, localeCases]) => {
    const indexName = fs
      .readdirSync(siteRoot)
      .find((name) => name.startsWith(`offline-search-index.${locale}.`) && name.endsWith(".json"));
    if (!indexName) throw new Error(`missing ${locale} offline search index`);
    const records = JSON.parse(fs.readFileSync(path.join(siteRoot, indexName), "utf8"));
    const titles = new Map(records.map((record) => [record.ref, record.title]));
    return [
      locale,
      localeCases.map(([query, expectedRef]) => {
        const expectedTitle = titles.get(expectedRef);
        if (!expectedTitle) throw new Error(`missing search record ${expectedRef}`);
        return [query, expectedRef, expectedTitle];
      })
    ];
  })
);

for (const [locale, localeCases] of Object.entries(cases)) {
  test(`summary Lunr ranks fixed ${locale} entry queries`, async ({ page }) => {
    test.skip(!metadataIntegrated, "PR-B search metadata fixture is not integrated");
    for (const [query, expectedRef, expectedTitle] of localeCases) {
      await page.goto(locale === "cn" ? "/cn/docs/" : "/docs/");
      await page.locator("[data-td-shell-search-open]").first().click();
      const input = page.locator(".td-shell-search__input");
      await input.fill(query);
      const pageResults = page
        .locator("#td-shell-search-results .td-shell-search__group")
        .first()
        .locator('[role="option"]');
      await expect(pageResults.first(), `no Lunr results for ${query}`).toBeVisible();
      await expect
        .poll(() =>
          pageResults.evaluateAll((rows) =>
            rows
              .slice(0, 3)
              .map((row) => row.querySelector(".td-shell-search__item-title")?.textContent.trim())
          )
        )
        .toContain(expectedTitle);
      const titles = await pageResults.evaluateAll((rows) =>
        rows.slice(0, 3).map((row) =>
          row.querySelector(".td-shell-search__item-title")?.textContent.trim()
        )
      );
      expect(
        titles.includes(expectedTitle),
        `${query} must rank ${expectedRef} in the top three`
      ).toBe(true);
      const target = pageResults.filter({ hasText: expectedTitle }).first();
      await target.click();
      await expect(page).toHaveURL((url) => url.pathname === expectedRef);
    }
  });
}
