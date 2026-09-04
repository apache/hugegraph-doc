const { test, expect } = require("./artifact-test");

const AI_ORIGIN = "http://127.0.0.1:4174";
const mockBundle = `
(function () {
  var queued = window.Kapa && window.Kapa.q ? window.Kapa.q.slice() : [];
  window.__kapaCalls = [];
  window.Kapa = function (method, value) {
    window.__kapaCalls.push([method, value]);
    if (method === 'render' && value && value.onRender) value.onRender();
  };
  queued.forEach(function (args) { window.Kapa.apply(null, Array.from(args)); });
})();`;

test.beforeEach(async ({}, testInfo) => {
  testInfo.skip(!process.env.AI_SITE_ROOT, "AI-enabled fixture was not built");
});

for (const [locale, route, source, language] of [
  ["en", "/docs/", "e2e-source-en", "en"],
  ["cn", "/cn/docs/", "e2e-source-cn", "zh"]
]) {
  test(`AI tail is click-gated and locale-bound for ${locale}`, async ({ page }) => {
    const requests = [];
    await page.route("https://widget.kapa.ai/kapa-widget.bundle.js", async (route) => {
      requests.push(route.request().url());
      await route.fulfill({ status: 200, contentType: "text/javascript", body: mockBundle });
    });
    await page.goto(AI_ORIGIN + route);
    expect(requests).toEqual([]);
    const launcher = page.locator(".hg-ask-ai-launcher");
    await expect(launcher).toBeVisible();

    await page.locator("[data-td-shell-search-open]").first().click();
    const input = page.locator(".td-shell-search__input");
    await input.fill("  server auth  ");
    const tail = page.locator("[data-hg-ai-search-tail]");
    await expect(tail).toBeVisible();
    await expect(tail.locator("[data-hg-ask-ai]")).toHaveAttribute(
      "data-hg-ai-query", "server auth"
    );
    await input.fill("");
    await expect(tail).toHaveCount(0);
    await input.fill(">theme");
    await expect(tail).toHaveCount(0);
    await input.fill("server auth");
    await tail.locator("[data-hg-ask-ai]").click();
    await expect.poll(() => requests.length).toBe(1);
    await expect.poll(() => page.evaluate(() => window.__kapaCalls || [])).toContainEqual([
      "setSourceGroupIDs", [source]
    ]);
    const script = page.locator("script[data-hg-kapa-widget]");
    await expect(script).toHaveAttribute("data-language", language);
    await expect(script).toHaveAttribute("data-source-group-ids-include", source);
    const calls = await page.evaluate(() => window.__kapaCalls);
    expect(calls).toContainEqual([
      "open", { mode: "ai", query: "server auth", submit: true }
    ]);
  });
}

test("AI 500 remains non-blocking and retry issues one fresh request", async ({ page }) => {
  let attempts = 0;
  await page.route("https://widget.kapa.ai/kapa-widget.bundle.js", async (route) => {
    attempts += 1;
    if (attempts === 1) await route.fulfill({ status: 500, body: "failed" });
    else await route.fulfill({ status: 200, contentType: "text/javascript", body: mockBundle });
  });
  await page.goto(AI_ORIGIN + "/docs/");
  const launcher = page.locator(".hg-ask-ai-launcher");
  await launcher.dblclick();
  await expect.poll(() => attempts).toBe(1);
  await expect(launcher).toHaveAttribute("data-hg-ai-state", "error");
  await launcher.click();
  await expect.poll(() => attempts).toBe(2);
  await expect(launcher).toHaveAttribute("data-hg-ai-state", "ready");
});
