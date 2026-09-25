const { test, expect } = require("./artifact-test");

for (const locale of ["en", "cn"]) {
  const prefix = locale === "cn" ? "/cn" : "";
  test(`latest ${locale} sidebar persists and isolates collapse`, async ({ page }) => {
    await page.goto(`${prefix}/docs/introduction/`);
    const key = `oink.sidebar.v3.latest.${locale}`;
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
    await expect(page.locator(".td-shell-sidebar__panel")).toHaveAttribute("aria-hidden", "true");
    await expect(page.locator(".td-shell-sidebar__panel > *").first()).toHaveJSProperty("inert", true);
    const restore = page.locator(".td-shell-float [data-td-shell-sidebar-toggle]");
    await expect(restore).toBeVisible();
    await expect(restore).toBeFocused();
    await page.waitForTimeout(200);
    await page.mouse.move(2, 200);
    await expect(page.locator("#td-shell-sidebar")).toHaveClass(
      /td-shell-sidebar--overlay/
    );
    const previewBox = await page.locator(".td-shell-sidebar__panel").boundingBox();
    expect(previewBox.x).toBeLessThanOrEqual(1);
    expect(previewBox.y).toBeLessThanOrEqual(1);
    await page.mouse.move(900, 300);
    await expect.poll(
      () => page.locator("#td-shell-sidebar").getAttribute("class"),
      { timeout: 1500 }
    ).not.toContain("td-shell-sidebar--overlay");
    await restore.focus();
    await restore.press("Enter");
    await expect(page.locator(".td-shell-sidebar__collapse")).toBeFocused();
    await expect(page.locator(".td-shell-sidebar__panel")).not.toHaveAttribute(
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
    await expect(page.locator(".td-shell-sidebar__panel > *").first()).toHaveJSProperty("inert", true);
    await expect(opener).toBeFocused();
    await expect(page.locator("html")).not.toHaveAttribute("data-td-shell-lock", "");
  });
}

for (const locale of ["en", "cn"]) {
  const prefix = locale === "cn" ? "/cn" : "";
  test(`latest ${locale} docs home opens start and components by default`, async ({ page }) => {
    const key = `oink.sidebar.v3.latest.${locale}`;
    await page.goto(`${prefix}/docs/`);
    await page.evaluate((name) => localStorage.removeItem(name), key);
    await page.reload();
    const start = page.locator(
      '#td-shell-sidebar [data-td-shell-tree-toggle][aria-controls$="_navstart-children"]',
    );
    const components = page.locator(
      '#td-shell-sidebar [data-td-shell-tree-toggle][aria-controls$="_navcomponents-children"]',
    );
    const develop = page.locator(
      '#td-shell-sidebar [data-td-shell-tree-toggle][aria-controls$="_navdevelop-children"]',
    );
    await expect(start).toHaveAttribute("aria-expanded", "true");
    await expect(components).toHaveAttribute("aria-expanded", "true");
    await expect(develop).toHaveAttribute("aria-expanded", "false");
    await start.click();
    await page.reload();
    await expect(page.locator(`[aria-controls="${await start.getAttribute("aria-controls")}"]`))
      .toHaveAttribute("aria-expanded", "false");
  });
}

for (const route of ["/docs/", "/cn/docs/"]) {
  test(`disabled AI emits no UI or third-party request at ${route}`, async ({ page }) => {
    expect(process.env.AI_DISABLED_SITE_ROOT, "Build the AI-disabled fixture").toBeTruthy();
    const requests = [];
    page.on("request", (request) => {
      if (/kapa\.ai|hcaptcha\.com|kapa-widget-proxy/.test(request.url())) {
        requests.push(request.url());
      }
    });
    await page.goto("http://127.0.0.1:4175" + route);
    await page.locator("[data-td-shell-search-open]").first().click();
    await page.locator(".td-shell-search__input").fill("server");
    await expect(page.locator('[role="option"]').first()).toBeVisible();
    await expect(page.locator("[data-hg-ask-ai]")).toHaveCount(0);
    await expect(page.locator('script[src*="kapa-adapter"]')).toHaveCount(0);
    expect(requests).toEqual([]);
  });
}

test("enabled AI makes no third-party request before consent", async ({ page }) => {
  const kapaRequests = [];
  page.on("request", (request) => {
    if (/kapa\.ai|hcaptcha\.com|kapa-widget-proxy/.test(request.url())) {
      kapaRequests.push(request.url());
    }
  });
  await page.goto("/docs/");
  await page.locator("[data-td-shell-search-open]").first().click();
  await page.locator(".td-shell-search__input").fill("server");
  await expect(page.locator('[role="option"]').first()).toBeVisible();
  expect(kapaRequests).toEqual([]);
  await page.locator(".td-shell-search__input").press("Escape");
  const launcher = page.locator("[data-hg-ask-ai]").first();
  await expect(launcher).toBeVisible();
  await launcher.click();
  await expect(page.locator("[data-hg-ai-consent]")).toBeVisible();
  await page.locator("[data-hg-ai-cancel]").click();
  await expect(page.locator("[data-hg-ai-consent]")).not.toBeVisible();
  await expect(launcher).toBeFocused();
  expect(kapaRequests).toEqual([]);
});

test("search index failure keeps one stable, focusable retry control", async ({
  page
}) => {
  let attempts = 0;
  await page.route("**/offline-search-index.en.*.json", async (route) => {
    attempts += 1;
    if (attempts === 1) await route.abort("failed");
    else await route.fallback();
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
  for (const [width, columns] of [[1440, 4], [900, 3], [390, 2], [320, 2]]) {
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
  await expect(page.locator(".hg-community-member__role-label")).toHaveCount(0);
  expect(await page.locator(".hg-community-member__surface:not(.hg-community-member__link)").count()).toBeGreaterThan(0);
  expect(await page.locator(".hg-community-member__surface:not(.hg-community-member__link) a").count()).toBe(0);
  const publicNames = await page
    .locator("#project-members .hg-community-member__identity")
    .allTextContents();
  expect(publicNames).toContain("coderzc");
  expect(publicNames).toContain("Jacky Yang");
  expect(publicNames).toContain("Jermy Li");
  await expect(page.getByRole("link", { name: "coderzc on GitHub", exact: true })).toBeVisible();
  await page.goto("/cn/community/");
  await expect(page.getByRole("link", { name: "coderzc 的 GitHub 主页", exact: true })).toBeVisible();

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
