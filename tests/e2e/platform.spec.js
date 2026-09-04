const { test, expect } = require("./artifact-test");

for (const locale of ["en", "cn"]) {
  const prefix = locale === "cn" ? "/cn" : "";
  test(`latest ${locale} sidebar persists and isolates collapse`, async ({ page }) => {
    await page.goto(`${prefix}/docs/introduction/`);
    const key = `oink.sidebar.v1.latest.${locale}`;
    await expect.poll(() => page.evaluate((name) => localStorage.getItem(name), key))
      .not.toBeNull();
    const toggle = page
      .locator('#td-shell-sidebar [data-td-shell-tree-toggle][aria-controls$="_navdevelop-children"]')
      .first();
    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    await toggle.click();
    const target = await toggle.getAttribute("aria-controls");
    await expect.poll(() => page.evaluate((name) => localStorage.getItem(name), key))
      .toContain(target);
    await page.reload();
    await expect(page.locator(`[aria-controls="${target}"]`)).toHaveAttribute(
      "aria-expanded", "true"
    );

    await page.locator(".td-shell-sidebar__collapse").click();
    await expect(page.locator("#td-shell-sidebar")).toHaveAttribute("aria-hidden", "true");
    await expect(page.locator("#td-shell-sidebar")).toHaveJSProperty("inert", true);
    const restore = page.locator(".hg-sidebar-restore");
    await expect(restore).toBeVisible();
    await restore.click();
    await expect(page.locator("#td-shell-sidebar")).not.toHaveAttribute(
      "aria-hidden", "true"
    );
  });

  test(`latest ${locale} mobile drawer restores focus and unlocks scroll`, async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${prefix}/docs/`);
    const opener = page.locator("[data-td-shell-drawer-open]");
    await opener.click();
    await expect(page.locator("html")).toHaveAttribute("data-td-shell-drawer", "open");
    await page.locator("button[data-td-shell-drawer-close]").click();
    await expect(page.locator("#td-shell-sidebar")).toHaveJSProperty("inert", true);
    await expect(opener).toBeFocused();
    await expect(page.locator("html")).not.toHaveAttribute("data-td-shell-lock", "");
  });
}

test("disabled AI emits no UI or Kapa request", async ({ page }) => {
  const kapaRequests = [];
  page.on("request", (request) => {
    if (request.url().includes("kapa.ai")) kapaRequests.push(request.url());
  });
  await page.goto("/docs/");
  await page.locator("[data-td-shell-search-open]").first().click();
  await page.locator(".td-shell-search__input").fill("server");
  await expect(page.locator('[role="option"]').first()).toBeVisible();
  expect(kapaRequests).toEqual([]);
  await expect(page.locator("[data-hg-ask-ai]")).toHaveCount(0);
});

test("search index failure keeps one stable, focusable retry control", async ({
  page
}) => {
  let attempts = 0;
  await page.route("**/offline-search-index.en.*.json", async (route) => {
    attempts += 1;
    if (attempts === 1) await route.abort("failed");
    else await route.continue();
  });
  await page.goto("/docs/");
  await page.locator("[data-td-shell-search-open]").first().click();
  await page.locator(".td-shell-search__input").fill("server");
  const retry = page.locator("[data-hg-search-retry]");
  await expect(retry).toHaveCount(1);
  const mutations = await retry.evaluate((node) => {
    window.__hgRetryNode = node;
    window.__hgRetryMutations = 0;
    new MutationObserver(() => { window.__hgRetryMutations += 1; })
      .observe(node.parentNode, { childList: true, subtree: true });
    return window.__hgRetryMutations;
  });
  expect(mutations).toBe(0);
  await page.waitForTimeout(250);
  expect(await page.evaluate(() => window.__hgRetryMutations)).toBe(0);
  expect(
    await retry.evaluate((node) => node === window.__hgRetryNode)
  ).toBe(true);

  const button = retry.locator("button");
  await button.focus();
  await expect(button).toBeFocused();
  await button.click();
  await expect.poll(() => attempts).toBe(2);
  await expect(page.locator('[role="option"]').first()).toBeVisible();
  await expect(page.locator(".td-shell-search__input")).toBeFocused();
  await expect(retry).toHaveCount(0);
});

test("Community grid and HTML/Print/Markdown profiles stay in parity", async ({
  page,
  request
}) => {
  await page.goto("/community/");
  test.skip(
    (await page.locator(".hg-community-members__grid").count()) === 0,
    "PR-B Community section is not integrated in this artifact"
  );
  for (const [width, columns] of [[1440, 5], [900, 3], [390, 2], [320, 2]]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/community/");
    const grid = page.locator(".hg-community-members__grid").first();
    await expect(grid).toBeVisible();
    expect(
      await grid.evaluate((node) => getComputedStyle(node).gridTemplateColumns.split(" ").length)
    ).toBe(columns);
  }
  await page.evaluate(() => localStorage.setItem("td-color-theme", "dark"));
  await page.reload();
  await expect(page.locator(".hg-community-member__link").first()).toBeVisible();
  await expect(page.locator(".hg-community-member__initials").first()).toBeAttached();

  const htmlProfiles = await page
    .locator("#project-members .hg-community-member__link")
    .evaluateAll((links) => links.map((link) => link.href).sort());
  const print = await (await request.get("/_print/community/")).text();
  const markdown = await (await request.get("/community/index.md")).text();
  for (const profile of htmlProfiles) {
    expect(print).toContain(profile);
    expect(markdown).toContain(profile);
  }
});
