const { test, expect } = require("./artifact-test");
const AxeBuilder = require("@axe-core/playwright").default;

for (const route of [
  "/",
  "/cn/",
  "/docs/",
  "/cn/docs/",
  "/community/",
  "/cn/community/",
  "/community/documentation/",
  "/cn/community/documentation/",
  "/docs/download/download/",
  "/cn/docs/download/download/",
  "/blog/",
  "/cn/blog/",
  "/blog/2025/10/09/toplingdb-quick-start/",
  "/cn/blog/2025/10/09/toplingdb-quick-start/",
  "/series/toplingdb/",
  "/cn/series/toplingdb/",
]) {
  test(`axe WCAG 2.2 AA guard ${route}`, async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    const response = await page.goto(route);
    expect(response && response.ok()).toBeTruthy();
    if (route.includes("/docs/download/")) {
      await expect(page.locator(".hg-asf-release").first()).toBeVisible();
      await expect(page.locator(".hg-asf-release").first()).toContainText("1.7.0");
    }
    await page.addStyleTag({
      content: "*,*::before,*::after{animation:none!important;transition:none!important}"
    });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(250);
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

test("homepage graph computing guide remains accessible on the light graph surface", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.goto("/");
  await expect(page.locator("#hg-landing")).toBeVisible();
  await page.locator("#story").evaluate(story => {
    const top = story.getBoundingClientRect().top + scrollY;
    scrollTo({ top: top + (story.offsetHeight - innerHeight) * 0.68, behavior: "instant" });
  });
  const panel = page.locator("#beat-computing");
  await expect(panel).toHaveCSS("opacity", "1");
  await expect(panel.getByRole("link")).toBeVisible();
  const results = await new AxeBuilder({ page })
    .include("#beat-computing")
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(results.violations.filter(item => ["critical", "serious"].includes(item.impact)))
    .toEqual([]);
});

for (const locale of ["en", "cn"]) {
  test(`download table scrolls with the keyboard on mobile ${locale}`, async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${locale === "cn" ? "/cn" : ""}/docs/download/download/`);
    const region = page.locator(".hg-asf-release .td-asset-list__table-wrap").first();
    await region.scrollIntoViewIfNeeded();
    await region.focus();
    await expect(region).toBeFocused();
    await region.press("ArrowRight");
    await expect.poll(() => region.evaluate((element) => element.scrollLeft)).toBeGreaterThan(0);
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  });
}
