const { test, expect } = require("./artifact-test");
const AxeBuilder = require("@axe-core/playwright").default;

for (const route of ["/docs/", "/cn/docs/", "/community/", "/cn/community/"]) {
  test(`axe WCAG 2.2 AA guard ${route}`, async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto(route);
    await page.addStyleTag({
      content: "*,*::before,*::after{animation:none!important;transition:none!important}"
    });
    await page.evaluate(() => document.fonts.ready);
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
      .analyze();
    const knownOinkBaseline = new Set(["list", "target-size"]);
    const blocking = results.violations.filter(
      (item) =>
        ["critical", "serious"].includes(item.impact) &&
        !knownOinkBaseline.has(item.id)
    );
    expect(blocking).toEqual([]);
  });
}
