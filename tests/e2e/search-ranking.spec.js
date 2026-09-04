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
const cases = fs.existsSync(metadataFixture)
  ? Object.groupBy(
      JSON.parse(fs.readFileSync(metadataFixture, "utf8")).map((entry) => [
        entry.query,
        entry.expected_ref
      ]),
      ([query, expectedRef]) => (expectedRef.startsWith("/cn/") ? "cn" : "en")
    )
  : FALLBACK_CASES;

for (const [locale, localeCases] of Object.entries(cases)) {
  test(`summary Lunr ranks fixed ${locale} entry queries`, async ({ page }) => {
    for (const [query, expectedRef] of localeCases) {
      await page.goto(locale === "cn" ? "/cn/docs/" : "/docs/");
      await page.locator("[data-td-shell-search-open]").first().click();
      const input = page.locator(".td-shell-search__input");
      await input.fill(query);
      const pageResults = page
        .locator("#td-shell-search-results .td-shell-search__group")
        .first()
        .locator('[role="option"]');
      await expect(pageResults.first(), `no Lunr results for ${query}`).toBeVisible();
      const paths = await pageResults.evaluateAll((rows) =>
        rows.slice(0, 3).map((row) => {
          const link = row.matches("a[href]") ? row : row.querySelector("a[href]");
          return link ? new URL(link.href).pathname : "";
        })
      );
      expect(
        paths.includes(expectedRef),
        `${query} must rank ${expectedRef} in the top three`
      ).toBe(true);
      const target = page
        .locator("#td-shell-search-results .td-shell-search__group")
        .first()
        .locator(`a[role="option"][href="${expectedRef}"]`)
        .first();
      await target.click();
      await expect(page).toHaveURL((url) => url.pathname === expectedRef);
    }
  });
}
