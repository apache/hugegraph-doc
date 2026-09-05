const { test, expect } = require("./artifact-test");
const fs = require("node:fs");
const path = require("node:path");

const states = [
  ["en-docs-desktop-light", "/docs/", { width: 1440, height: 900 }, "light", "default"],
  ["cn-docs-desktop-dark", "/cn/docs/", { width: 1440, height: 900 }, "dark", "default"],
  ["en-search-desktop-light", "/docs/", { width: 1440, height: 900 }, "light", "search"],
  ["cn-search-mobile-dark", "/cn/docs/", { width: 390, height: 844 }, "dark", "search"],
  ["en-sidebar-desktop-light", "/docs/introduction/", { width: 1440, height: 900 }, "light", "collapse"],
  ["cn-sidebar-mobile-dark", "/cn/docs/", { width: 390, height: 844 }, "dark", "drawer"],
  ["en-community-desktop-light", "/community/", { width: 1440, height: 900 }, "light", "default"],
  ["cn-community-mobile-dark", "/cn/community/", { width: 320, height: 720 }, "dark", "default"]
];

for (const [name, url, viewport, theme, state] of states) {
  test(`capture advisory ${name}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.addInitScript(
      (value) => localStorage.setItem("td-color-theme", value),
      theme
    );
    await page.goto(url);
    await expect(page.locator("body")).toBeVisible();
    if (state === "search") {
      await page.locator("[data-td-shell-search-open]").first().click();
      await page.locator(".td-shell-search__input").fill(url.startsWith("/cn/") ? "服务端" : "server");
      await expect(page.locator('[role="option"]').first()).toBeVisible();
    } else if (state === "collapse") {
      await page.locator(".td-shell-sidebar__collapse").click();
      await expect(page.locator("#td-shell-sidebar")).toHaveAttribute("aria-hidden", "true");
    } else if (state === "drawer") {
      await page.locator("[data-td-shell-drawer-open]").click();
      await expect(page.locator("html")).toHaveAttribute("data-td-shell-drawer", "open");
    }
    const directory = path.join(__dirname, "visual-results");
    fs.mkdirSync(directory, { recursive: true });
    await page.screenshot({
      path: path.join(directory, `${name}.png`),
      fullPage: true
    });
  });
}
