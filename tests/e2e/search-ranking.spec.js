const { test, expect } = require("@playwright/test");

const CASES = {
  en: [
    ["introduction", "/docs/introduction/", "Apache HugeGraph Introduction"],
    ["server", "/docs/quickstart/hugegraph/hugegraph-server/", "HugeGraph Server Quick Start"],
    ["hstore", "/docs/quickstart/hugegraph/hugegraph-hstore/", "HugeGraph-Store Quick Start"],
    ["placement driver", "/docs/quickstart/hugegraph/hugegraph-pd/", "HugeGraph-PD Quick Start"],
    ["computer", "/docs/quickstart/computing/hugegraph-computer/", "HugeGraph-Computer Quick Start"],
    ["loader", "/docs/quickstart/toolchain/hugegraph-loader/", "HugeGraph-Loader Quick Start"],
    ["hubble", "/docs/quickstart/toolchain/hugegraph-hubble/", "HugeGraph-Hubble Quick Start"],
    ["clients", "/docs/clients/", "Clients and APIs"],
    ["rest api", "/docs/clients/restful-api/", "HugeGraph RESTful API"],
    ["configuration", "/docs/config/", "HugeGraph-Server Configuration"],
    ["authentication", "/docs/config/config-authentication/", "Built-in User Authentication"],
    ["download", "/docs/download/download/", "Download Apache HugeGraph"]
  ],
  cn: [
    ["介绍", "/cn/docs/introduction/", "Apache HugeGraph 介绍"],
    ["服务端", "/cn/docs/quickstart/hugegraph/hugegraph-server/", "HugeGraph Server 快速开始"],
    ["HStore", "/cn/docs/quickstart/hugegraph/hugegraph-hstore/", "HugeGraph-Store Quick Start"],
    ["PD", "/cn/docs/quickstart/hugegraph/hugegraph-pd/", "HugeGraph-PD Quick Start"],
    ["图计算", "/cn/docs/quickstart/computing/hugegraph-computer/", "HugeGraph-Computer Quick Start"],
    ["数据导入", "/cn/docs/quickstart/toolchain/hugegraph-loader/", "HugeGraph-Loader Quick Start"],
    ["图形化界面", "/cn/docs/quickstart/toolchain/hugegraph-hubble/", "HugeGraph-Hubble Quick Start"],
    ["客户端", "/cn/docs/clients/", "客户端与 API"],
    ["REST API", "/cn/docs/clients/restful-api/", "HugeGraph RESTful API"],
    ["配置", "/cn/docs/config/", "HugeGraph-Server 配置"],
    ["认证", "/cn/docs/config/config-authentication/", "HugeGraph 内置用户权限"],
    ["下载", "/cn/docs/download/download/", "下载 Apache HugeGraph"]
  ]
};

for (const [locale, cases] of Object.entries(CASES)) {
  test(`summary Lunr ranks fixed ${locale} entry queries`, async ({ page }) => {
    for (const [query, expectedRef, expectedTitle] of cases) {
      await page.goto(locale === "cn" ? "/cn/docs/" : "/docs/");
      await page.locator("[data-td-shell-search-open]").first().click();
      const input = page.locator(".td-shell-search__input");
      await input.fill(query);
      const pageResults = page
        .locator("#td-shell-search-results .td-shell-search__group")
        .first()
        .locator('[role="option"]');
      await expect(pageResults.first(), `no Lunr results for ${query}`).toBeVisible();
      const titles = await pageResults.evaluateAll((rows) =>
        rows.slice(0, 3).map((row) =>
          row.querySelector(".td-shell-search__item-title").textContent.trim()
        )
      );
      expect(
        titles.some((title) => title.includes(expectedTitle)),
        `${query} must rank ${expectedRef} in the top three`
      ).toBe(true);
      const target = pageResults.filter({ hasText: expectedTitle }).first();
      await target.click();
      await expect(page).toHaveURL((url) => url.pathname === expectedRef);
    }
  });
}
