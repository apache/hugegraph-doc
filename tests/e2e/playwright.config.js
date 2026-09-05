const { defineConfig } = require("@playwright/test");

const siteRoot = process.env.SITE_ROOT;
const aiSiteRoot = process.env.AI_SITE_ROOT;
if (!siteRoot) {
  throw new Error("SITE_ROOT must point to an aggregate site artifact");
}

module.exports = defineConfig({
  testDir: ".",
  testMatch: "*.spec.js",
  outputDir: "test-results",
  timeout: 30_000,
  expect: { timeout: 5_000 },
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [["line"], ["html", { outputFolder: "playwright-report", open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:4173",
    browserName: "chromium",
    trace: "retain-on-failure",
    screenshot: "only-on-failure"
  },
  webServer: [
    {
      command: `python3 -m http.server 4173 --bind 127.0.0.1 --directory ${JSON.stringify(siteRoot)}`,
      url: "http://127.0.0.1:4173/",
      reuseExistingServer: false,
      timeout: 30_000,
      stdout: "ignore",
      stderr: "ignore"
    },
    ...(aiSiteRoot
      ? [{
          command: `python3 -m http.server 4174 --bind 127.0.0.1 --directory ${JSON.stringify(aiSiteRoot)}`,
          url: "http://127.0.0.1:4174/",
          reuseExistingServer: false,
          timeout: 30_000,
          stdout: "ignore",
          stderr: "ignore"
        }]
      : [])
  ]
});
