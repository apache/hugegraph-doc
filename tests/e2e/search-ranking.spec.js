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

// Body-only queries are separate from the 24 title/keyword metadata contracts.
// Do not add search_keywords or boosts to make these full-text cases pass.
const BODY_CASES = {
  en: [
    ["restserver.connection_max_requests", "/docs/config/config-option/"],
    ["auth.token_secret", "/docs/config/config-authentication/"],
    ["target-trust-store-password", "/docs/config/config-https/"],
    ["rocksdb.min_write_buffer_number_to_merge", "/docs/config/config-backend-rocksdb/"]
  ],
  cn: [
    ["restserver.connection_max_requests", "/cn/docs/config/config-option/"],
    ["auth.token_secret", "/cn/docs/config/config-authentication/"],
    ["target-trust-store-password", "/cn/docs/config/config-https/"],
    ["rocksdb.min_write_buffer_number_to_merge", "/cn/docs/config/config-backend-rocksdb/"],
    ["重启后继续有效", "/cn/docs/config/config-authentication/"],
    ["全键布隆过滤器", "/cn/docs/config/config-backend-rocksdb/"],
    ["服务端私钥", "/cn/docs/config/config-https/"]
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
      [...localeCases, ...BODY_CASES[locale]].map(([query, expectedRef]) => {
        const expectedTitle = titles.get(expectedRef);
        if (!expectedTitle) throw new Error(`missing search record ${expectedRef}`);
        return [query, expectedRef, expectedTitle];
      })
    ];
  })
);

for (const [locale, localeCases] of Object.entries(cases)) {
  for (const [query, expectedRef, expectedTitle] of localeCases) {
    test(`local Lunr ranks ${locale}: ${query}`, async ({ page }) => {
      test.skip(!metadataIntegrated, "Search metadata fixture is unavailable");
      // Search uses the JSON index; loading documentation images adds no signal
      // and can leave unrelated image requests in flight during navigation.
      await page.route(/\.(?:png|jpe?g|webp|svg)(?:\?.*)?$/i, (route) => route.abort());
      await page.goto(locale === "cn" ? "/cn/docs/" : "/docs/");
      await page.locator("[data-td-shell-search-open]").first().click();
      const input = page.locator(".td-shell-search__input");
      await input.fill(query);
      const pageResults = page
        .locator("#td-shell-search-results .td-shell-search__group")
        .first()
        .locator('[role="option"]');
      await expect(pageResults.first(), `no Lunr results for ${query}`).toBeVisible();
      // OINK may append " › section" to a page's indexed title. Accept only
      // that explicit suffix and activate the matching row within the top
      // three, then verify its real destination rather than a title substring.
      const expectedRank = () => pageResults.evaluateAll((rows, title) =>
        rows.slice(0, 3).findIndex((row) => {
          const label = row.querySelector(".td-shell-search__item-title")?.textContent.trim() || "";
          return label === title || label.startsWith(title + " › ");
        }), expectedTitle
      );
      await expect
        .poll(expectedRank, { message: `${query} must rank ${expectedRef} in the top three` })
        .toBeGreaterThanOrEqual(0);
      const rank = await expectedRank();
      expect(rank).toBeGreaterThanOrEqual(0);
      expect(rank).toBeLessThan(3);
      await pageResults.nth(rank).click();
      await expect(page).toHaveURL((url) => url.pathname === expectedRef);
    });
  }
}
