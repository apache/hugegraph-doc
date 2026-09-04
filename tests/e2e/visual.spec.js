const { test, expect } = require("@playwright/test");
const fs = require("node:fs");
const path = require("node:path");

const states = [
  ["en-docs-desktop-light", "/docs/", { width: 1440, height: 900 }, "light"],
  ["cn-docs-desktop-dark", "/cn/docs/", { width: 1440, height: 900 }, "dark"],
  ["en-docs-mobile-light", "/docs/", { width: 390, height: 844 }, "light"],
  ["cn-community-mobile-dark", "/cn/community/", { width: 320, height: 720 }, "dark"]
];

for (const [name, url, viewport, theme] of states) {
  test(`capture advisory ${name}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.addInitScript(
      (value) => localStorage.setItem("td-color-theme", value),
      theme
    );
    await page.goto(url);
    await expect(page.locator("body")).toBeVisible();
    const directory = path.join(__dirname, "visual-results");
    fs.mkdirSync(directory, { recursive: true });
    await page.screenshot({
      path: path.join(directory, `${name}.png`),
      fullPage: true
    });
  });
}
