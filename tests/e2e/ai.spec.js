const { test, expect } = require("./artifact-test");

const AI_ORIGIN = "http://127.0.0.1:4174";
const mockBundle = `
(function () {
  var queued = window.Kapa && window.Kapa.q ? window.Kapa.q.slice() : [];
  window.__kapaCalls = window.__kapaCalls || [];
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
    await page.route("https://widget.kapa.ai/kapa-widget.bundle.js*", async (route) => {
      requests.push(route.request().url());
      await route.fulfill({ status: 200, contentType: "text/javascript", body: mockBundle });
    });
    await page.goto(AI_ORIGIN + route);
    expect(requests).toEqual([]);
    await page.evaluate(() =>
      document.documentElement.setAttribute("data-bs-theme", "dark")
    );
    const launcher = page.locator(".hg-ask-ai-launcher");
    await expect(launcher).toBeHidden();
    await expect(page.locator("[data-hg-ai-consent]")).toBeVisible();

    await page.locator("[data-td-shell-search-open]").first().click();
    const input = page.locator(".td-shell-search__input");
    await input.fill("  server auth  ");
    const tail = page.getByRole("option").filter({ hasText: /Ask AI|询问 AI|问 AI/ });
    await expect(tail).toBeVisible();
    await expect(tail).toContainText("server auth");
    await input.fill("");
    await expect(tail).toHaveCount(0);
    await input.fill(">theme");
    await expect(tail).toHaveCount(0);
    await input.fill("server auth");
    await tail.click();
    await expect(page.locator("[data-hg-ai-consent]")).toBeVisible();
    expect(requests).toEqual([]);
    await page.locator("[data-hg-ai-consent] [data-hg-ai-continue]").click();
    await expect.poll(() => requests.length).toBe(1);
    await expect.poll(() => page.evaluate(() => window.__kapaCalls || [])).toContainEqual([
      "setSourceGroupIDs", [source]
    ]);
    const script = page.locator("script[data-hg-kapa-widget]");
    await expect(script).toHaveAttribute("data-language", language);
    const config = await page.locator("#hg-ai-config").evaluate(node => JSON.parse(node.textContent));
    expect(config.exampleQuestions).toHaveLength(36);
    const displayed = (await script.getAttribute("data-example-questions")).split(",");
    expect(displayed).toHaveLength(3);
    expect(new Set(displayed).size).toBe(3);
    expect(displayed.every(question => config.exampleQuestions.includes(question))).toBe(true);
    await expect(script).not.toHaveAttribute("data-chat-disclaimer");
    await expect(script).toHaveAttribute("data-answer-cta-button-enabled", "true");
    await expect(script).toHaveAttribute("data-answer-cta-button-text", config.labels.community);
    await expect(script).toHaveAttribute("data-answer-cta-button-link", "https://github.com/apache/hugegraph/discussions");
    expect(await script.evaluate(node => Array.from(node.attributes).some(attr =>
      /handoff|email/.test(attr.name)))).toBe(false);
    await expect(script).toHaveAttribute("data-user-analytics-cookie-enabled", "false");
    await expect(script).toHaveAttribute("data-user-analytics-fingerprint-enabled", "false");
    await expect(script).toHaveAttribute("data-source-group-ids-include", source);
    await expect(script).toHaveAttribute("data-project-color", "#532fc9");
    await expect(script).toHaveAttribute("data-project-color-dark", "#a693e3");
    await expect(script).toHaveAttribute("data-anchor-color-dark", "#baace9");
    await expect(script).toHaveAttribute(
      "data-color-scheme-selector", "[data-bs-theme='dark']"
    );
    const calls = await page.evaluate(() => window.__kapaCalls);
    expect(calls).toContainEqual([
      "open", { mode: "ai", query: "server auth", submit: true }
    ]);
  });
}

test("AI consent cancel and Escape keep native search local", async ({ page }) => {
  const requests = [];
  await page.route("https://widget.kapa.ai/kapa-widget.bundle.js*", async (route) => {
    requests.push(route.request().url());
    await route.fulfill({ status: 200, contentType: "text/javascript", body: mockBundle });
  });
  await page.goto(AI_ORIGIN + "/docs/");
  const launcher = page.locator(".hg-ask-ai-launcher");
  const consent = page.locator("[data-hg-ai-consent]");
  await expect(consent).toBeVisible();
  await consent.locator("[data-hg-ai-cancel]").click();
  await expect(consent).toBeHidden();
  await expect(launcher).toBeFocused();
  expect(requests).toEqual([]);
  await launcher.click();
  await expect(consent).toBeVisible();
  await consent.press("Escape");
  await expect(consent).toBeHidden();
  await expect(launcher).toBeFocused();
  expect(requests).toEqual([]);
  await page.locator("[data-td-shell-search-open]").first().click();
  await expect(page.locator(".td-shell-search__input")).toBeVisible();
});

test("AI 500 remains non-blocking and retry issues one fresh request", async ({ page }) => {
  let attempts = 0;
  await page.route("https://widget.kapa.ai/kapa-widget.bundle.js*", async (route) => {
    attempts += 1;
    if (attempts === 1) await route.fulfill({ status: 500, body: "failed" });
    else await route.fulfill({ status: 200, contentType: "text/javascript", body: mockBundle });
  });
  await page.goto(AI_ORIGIN + "/docs/");
  const launcher = page.locator(".hg-ask-ai-launcher");
  await expect(page.locator("[data-hg-ai-consent]")).toBeVisible();
  expect(attempts).toBe(0);
  await page.locator("[data-hg-ai-consent] [data-hg-ai-continue]").click();
  await expect.poll(() => attempts).toBe(1);
  await expect(launcher).toHaveAttribute("data-hg-ai-state", "error");
  await expect(launcher).toHaveAttribute("title", /unavailable/i);
  await expect(launcher).toBeFocused();
  await launcher.click();
  await expect.poll(() => attempts).toBe(2);
  await expect(launcher).toHaveAttribute("data-hg-ai-state", "ready");
  await expect(launcher).not.toHaveAttribute("title", /unavailable/i);
});

test("AI pending timeout discards stale state and retry waits for a fresh bundle", async ({
  page
}) => {
  let attempts = 0;
  let releaseStale;
  const staleGate = new Promise((resolve) => { releaseStale = resolve; });
  await page.route("https://widget.kapa.ai/kapa-widget.bundle.js*", async (route) => {
    attempts += 1;
    if (attempts === 1) {
      await staleGate;
    }
    await route.fulfill({
      status: 200,
      contentType: "text/javascript",
      body: mockBundle
    });
  });
  await page.goto(AI_ORIGIN + "/docs/");
  const launcher = page.locator(".hg-ask-ai-launcher");
  await expect(page.locator("[data-hg-ai-consent]")).toBeVisible();
  expect(attempts).toBe(0);
  await page.locator("[data-hg-ai-consent] [data-hg-ai-continue]").click();
  await expect.poll(() => attempts).toBe(1);
  await expect(launcher).toHaveAttribute("data-hg-ai-state", "error", {
    timeout: 7_000
  });
  await launcher.click();
  await expect.poll(() => attempts).toBe(2);
  await expect(launcher).toHaveAttribute("data-hg-ai-state", "ready");
  expect(
    await page.locator("script[data-hg-kapa-widget]").getAttribute("src")
  ).toContain("?hg-retry=2");
  expect(
    await page.evaluate(() =>
      (window.__kapaCalls || []).filter(([method]) => method === "open").length
    )
  ).toBe(1);

  releaseStale();
  await page.waitForTimeout(250);
  expect(
    await page.evaluate(() =>
      (window.__kapaCalls || []).filter(([method]) => method === "open").length
    )
  ).toBe(1);
});


test("native AI row supports keyboard selection, IME, and consent focus handoff", async ({ page }) => {
  const requests = [];
  await page.route("https://widget.kapa.ai/kapa-widget.bundle.js*", async (route) => {
    requests.push(route.request().url());
    await route.fulfill({ status: 200, contentType: "text/javascript", body: mockBundle });
  });
  await page.goto(AI_ORIGIN + "/docs/");
  await page.locator("[data-hg-ai-cancel]").click();
  await page.locator("[data-td-shell-search-open]").first().click();
  const input = page.locator(".td-shell-search__input");
  await input.fill("server");
  const tail = page.getByRole("option").filter({ hasText: "Ask AI:" });
  await expect(tail).toBeVisible();
  await input.press("Control+End");
  await expect(tail).toHaveAttribute("aria-selected", "true");
  await input.dispatchEvent("keydown", { key: "Enter", isComposing: true });
  await expect(page.locator("[data-hg-ai-consent]")).toBeHidden();
  await input.press("Enter");
  await expect(page.locator("[data-hg-ai-consent]")).toBeVisible();
  await expect(page.locator("#td-shell-search")).toBeHidden();
  await page.locator("[data-hg-ai-cancel]").click();
  await expect(page.locator(".hg-ask-ai-launcher")).toBeFocused();
  expect(requests).toEqual([]);

  await page.locator("[data-td-shell-search-open]").first().click();
  await input.fill("zzzxqnonexistentzzzxq");
  await expect(tail).toBeVisible();
  await expect(tail).toHaveAttribute("aria-selected", "true");
  await input.press("Enter");
  await page.locator("[data-hg-ai-continue]").click();
  await expect.poll(() => page.evaluate(() => window.__kapaCalls || [])).toContainEqual([
    "open", { mode: "ai", query: "zzzxqnonexistentzzzxq", submit: true }
  ]);
});

test("reopening native search cancels a pending AI handoff", async ({ page }) => {
  let release;
  const gate = new Promise((resolve) => { release = resolve; });
  let requested = false;
  await page.route("https://widget.kapa.ai/kapa-widget.bundle.js*", async (route) => {
    requested = true;
    await gate;
    await route.fulfill({ status: 200, contentType: "text/javascript", body: mockBundle });
  });
  await page.goto(AI_ORIGIN + "/docs/");
  await page.locator("[data-td-shell-search-open]").first().click();
  const input = page.locator(".td-shell-search__input");
  await input.fill("zzzxqnonexistentzzzxq");
  await expect(page.getByRole("option").filter({ hasText: "Ask AI:" })).toBeVisible();
  await input.press("Enter");
  await page.locator("[data-hg-ai-continue]").click();
  await expect.poll(() => requested).toBe(true);
  await page.locator("[data-td-shell-search-open]").first().click();
  await expect(input).toBeFocused();
  release();
  await expect(page.locator(".hg-ask-ai-launcher")).toHaveAttribute("data-hg-ai-state", "idle");
  await page.waitForTimeout(250);
  expect(await page.evaluate(() => (window.__kapaCalls || []).filter(([method]) => method === "open"))).toEqual([]);
  await expect(input).toBeFocused();
});


test("persistent consent survives language navigation, reload and a fresh tab without loading AI", async ({ page }) => {
  const requests = [];
  await page.route("https://widget.kapa.ai/kapa-widget.bundle.js*", async route => {
    requests.push(route.request().url());
    await route.fulfill({ status: 200, contentType: "text/javascript", body: mockBundle });
  });
  await page.goto(AI_ORIGIN + "/docs/");
  await expect(page.locator("[data-hg-ai-revoke]")).toBeHidden();
  await expect(page.locator(".hg-ask-ai-launcher")).toBeHidden();
  await page.locator("[data-hg-ai-continue]").click();
  await expect.poll(() => requests.length).toBe(1);

  await page.goto(AI_ORIGIN + "/cn/docs/");
  expect(requests).toHaveLength(1);
  await expect(page.locator("script[data-hg-kapa-widget]")).toHaveCount(0);
  await page.locator(".hg-ask-ai-launcher").click();
  await expect(page.locator("[data-hg-ai-consent]")).toBeHidden();
  await expect.poll(() => requests.length).toBe(2);
  await expect(page.locator("script[data-hg-kapa-widget]")).toHaveAttribute("data-language", "zh");

  await page.reload();
  await expect(page.locator("script[data-hg-kapa-widget]")).toHaveCount(0);
  expect(requests).toHaveLength(2);
  await page.locator(".hg-ask-ai-launcher").click();
  await expect(page.locator("[data-hg-ai-consent]")).toBeHidden();
  await expect.poll(() => requests.length).toBe(3);
  const fresh = await page.context().newPage();
  await fresh.route("https://widget.kapa.ai/kapa-widget.bundle.js*", async route => {
    requests.push(route.request().url());
    await route.fulfill({ status: 200, contentType: "text/javascript", body: mockBundle });
  });
  await fresh.goto(AI_ORIGIN + "/docs/");
  await expect(fresh.locator("[data-hg-ai-consent]")).toBeHidden();
  await expect(fresh.locator(".hg-ask-ai-launcher")).toBeVisible();
  await expect(fresh.locator("script[data-hg-kapa-widget]")).toHaveCount(0);
  expect(requests).toHaveLength(3);
  await fresh.close();
});

test("blocked local storage requires fresh consent after navigation", async ({ page }) => {
  const requests = [];
  await page.addInitScript(() => {
    Object.defineProperty(window, "localStorage", {
      get() { throw new DOMException("Storage disabled", "SecurityError"); },
    });
  });
  await page.route("https://widget.kapa.ai/kapa-widget.bundle.js*", async route => {
    requests.push(route.request().url());
    await route.fulfill({ status: 200, contentType: "text/javascript", body: mockBundle });
  });
  await page.goto(AI_ORIGIN + "/docs/");
  await expect(page.locator("[data-hg-ai-consent]")).toBeVisible();
  await page.locator("[data-hg-ai-cancel]").click();
  await expect(page.locator("[data-hg-ai-consent]")).toBeHidden();
  await page.reload();
  await expect(page.locator("[data-hg-ai-consent]")).toBeVisible();
  expect(requests).toHaveLength(0);
  await page.locator("[data-hg-ai-continue]").click();
  await expect.poll(() => requests.length).toBe(1);
  await page.goto(AI_ORIGIN + "/cn/docs/");
  await expect(page.locator("script[data-hg-kapa-widget]")).toHaveCount(0);
  await expect(page.locator("[data-hg-ai-consent]")).toBeVisible();
  expect(requests).toHaveLength(1);
});


test("inline disclosure is nonmodal and first agreement opens AI with one click", async ({ page }) => {
  const requests = [];
  await page.route("https://widget.kapa.ai/kapa-widget.bundle.js*", async route => {
    requests.push(route.request().url());
    await route.fulfill({ status: 200, contentType: "text/javascript", body: mockBundle });
  });
  await page.goto(AI_ORIGIN + "/docs/");
  const notice = page.locator("[data-hg-ai-consent]");
  await expect(notice).toBeVisible();
  expect(await notice.evaluate(node => node.tagName)).toBe("SECTION");
  await expect(notice).not.toHaveAttribute("aria-modal", "true");
  await expect(page.locator("dialog[data-hg-ai-consent]")).toHaveCount(0);
  await expect(page.locator(".hg-ask-ai-launcher")).toBeHidden();
  // Reading and native search remain interactive before making any AI choice.
  await page.locator("[data-td-shell-search-open]").first().click();
  await expect(page.locator(".td-shell-search__input")).toBeFocused();
  await page.locator(".td-shell-search__input").press("Escape");
  expect(requests).toHaveLength(0);
  await notice.locator("[data-hg-ai-continue]").click();
  await expect.poll(() => requests.length).toBe(1);
  await expect(notice).toBeHidden();
  await expect(page.locator(".hg-ask-ai-launcher")).toBeVisible();
  await expect.poll(() => page.evaluate(() => window.__kapaCalls || [])).toContainEqual([
    "open", { mode: "ai", query: "", submit: false }
  ]);
});


for (const dismiss of ["button", "escape"]) {
  test(`dismissal via ${dismiss} survives navigation and a fresh tab without granting AI`, async ({ page }) => {
    const requests = [];
    await page.context().route("https://widget.kapa.ai/kapa-widget.bundle.js*", async route => {
      requests.push(route.request().url());
      await route.fulfill({ status: 200, contentType: "text/javascript", body: mockBundle });
    });
    await page.goto(AI_ORIGIN + "/docs/");
    if (dismiss === "button") await page.locator("[data-hg-ai-cancel]").click();
    else await page.locator("[data-hg-ai-continue]").press("Escape");
    await page.goto(AI_ORIGIN + "/cn/docs/");
    await expect(page.locator("[data-hg-ai-consent]")).toBeHidden();
    await expect(page.locator(".hg-ask-ai-launcher")).toBeVisible();
    await expect(page.locator("[data-hg-ai-revoke]")).toBeHidden();
    await page.reload();
    await expect(page.locator("[data-hg-ai-consent]")).toBeHidden();
    const fresh = await page.context().newPage();
    await fresh.goto(AI_ORIGIN + "/docs/");
    await expect(fresh.locator("[data-hg-ai-consent]")).toBeHidden();
    await fresh.locator(".hg-ask-ai-launcher").click();
    await expect(fresh.locator("[data-hg-ai-consent]")).toBeVisible();
    await expect(fresh.locator("[data-hg-ai-continue]")).toBeFocused();
    expect(requests).toHaveLength(0);
    await fresh.close();
    await page.locator("[data-td-shell-search-open]").first().click();
    await page.locator(".td-shell-search__input").fill("zzzxqnonexistentzzzxq");
    await page.getByRole("option").filter({ hasText: /Ask AI|询问 AI|问 AI/ }).click();
    await expect(page.locator("[data-hg-ai-consent]")).toBeVisible();
    expect(requests).toHaveLength(0);
  });
}

for (const loaded of [false, true]) {
  test(`revocation resets grant and vendor state (${loaded ? "after" : "before"} loading)`, async ({ page }) => {
    const requests = [];
    await page.route("https://widget.kapa.ai/kapa-widget.bundle.js*", async route => {
      requests.push(route.request().url());
      await route.fulfill({ status: 200, contentType: "text/javascript", body: mockBundle });
    });
    await page.goto(AI_ORIGIN + "/docs/");
    await page.evaluate(() => {
      const config = JSON.parse(document.querySelector("#hg-ai-config").textContent);
      localStorage.setItem('hg-ai-consent:v2:' + config.websiteId, 'granted');
      localStorage.setItem('unrelated', 'preserve');
    });
    await page.reload();
    await expect(page.locator("[data-hg-ai-revoke]")).toBeVisible();
    expect(requests).toHaveLength(0);
    if (loaded) {
      await page.locator(".hg-ask-ai-launcher").click();
      await expect.poll(() => requests.length).toBe(1);
      await expect(page.locator(".hg-ask-ai-launcher")).toHaveAttribute("data-hg-ai-state", "ready");
    }
    await page.locator("[data-hg-ai-revoke]").click();
    await expect(page.locator("[data-hg-ai-consent]")).toBeVisible();
    await expect(page.locator(".hg-ask-ai-launcher")).toBeHidden();
    await expect(page.locator("[data-hg-ai-revoke]")).toBeHidden();
    await expect(page.locator("script[data-hg-kapa-widget]")).toHaveCount(0);
    expect(await page.evaluate(() => window.__kapaCalls)).toBeUndefined();
    expect(await page.evaluate(() => localStorage.getItem('unrelated'))).toBe('preserve');
    expect(requests).toHaveLength(loaded ? 1 : 0);
  });
}

test("blocked adapter leaves consent and launcher hidden and native search usable", async ({ page }) => {
  const requests = [];
  await page.route("**/js/kapa-adapter*.js", route => route.abort());
  await page.route("https://widget.kapa.ai/kapa-widget.bundle.js*", route => {
    requests.push(route.request().url());
    return route.abort();
  });
  await page.goto(AI_ORIGIN + "/docs/");
  await expect(page.locator("[data-hg-ai-consent]")).toBeHidden();
  await expect(page.locator(".hg-ask-ai-launcher")).toBeHidden();
  await expect(page.locator("[data-hg-ai-revoke]")).toBeHidden();
  await page.locator("[data-td-shell-search-open]").first().click();
  await expect(page.locator(".td-shell-search__input")).toBeFocused();
  expect(requests).toHaveLength(0);
});


test("failed persistent grant removal announces error without pretending to revoke", async ({ page }) => {
  await page.goto(AI_ORIGIN + "/docs/");
  await page.evaluate(() => {
    const config = JSON.parse(document.querySelector("#hg-ai-config").textContent);
    localStorage.setItem('hg-ai-consent:v2:' + config.websiteId, 'granted');
  });
  await page.reload();
  await page.evaluate(() => {
    Storage.prototype.removeItem = function () { throw new DOMException('blocked', 'SecurityError'); };
  });
  await page.locator("[data-hg-ai-revoke]").click();
  const revokeError = await page.locator("#hg-ai-config").evaluate(node =>
    JSON.parse(node.textContent).labels.revokeError);
  await expect(page.locator("[data-hg-ai-status]")).toHaveText(revokeError);
  await expect(page.locator("[data-hg-ai-revoke]")).toBeVisible();
  await expect(page.locator("[data-hg-ai-consent]")).toBeHidden();
  expect(await page.evaluate(() => {
    const config = JSON.parse(document.querySelector("#hg-ai-config").textContent);
    return localStorage.getItem('hg-ai-consent:v2:' + config.websiteId);
  })).toBe('granted');
});


for (const loaded of [false, true]) {
  test(`revocation synchronizes sibling tabs (${loaded ? "loaded vendor" : "before loading"})`, async ({ page }) => {
    const requests = [];
    const fulfillBundle = async route => {
      requests.push(route.request().url());
      await route.fulfill({ status: 200, contentType: "text/javascript", body: mockBundle });
    };
    await page.route("https://widget.kapa.ai/kapa-widget.bundle.js*", fulfillBundle);
    await page.context().route("https://widget.kapa.ai/kapa-widget.bundle.js*", fulfillBundle);
    await page.goto(AI_ORIGIN + "/docs/");
    await page.evaluate(() => {
      const config = JSON.parse(document.querySelector("#hg-ai-config").textContent);
      localStorage.setItem('hg-ai-consent:v2:' + config.websiteId, 'granted');
    });
    await page.reload();
    const sibling = await page.context().newPage();
    await sibling.goto(AI_ORIGIN + "/cn/docs/");
    await expect(sibling.locator("[data-hg-ai-consent]")).toBeHidden();
    if (loaded) {
      await page.locator(".hg-ask-ai-launcher").click();
      await sibling.locator(".hg-ask-ai-launcher").click();
      await expect.poll(() => requests.length).toBe(2);
      await expect(sibling.locator(".hg-ask-ai-launcher")).toHaveAttribute("data-hg-ai-state", "ready");
    }
    await page.locator("[data-hg-ai-revoke]").click();
    await expect(page.locator("[data-hg-ai-consent]")).toBeVisible();
    await expect(sibling.locator("[data-hg-ai-consent]")).toBeVisible();
    await expect(sibling.locator("script[data-hg-kapa-widget]")).toHaveCount(0);
    expect(await sibling.evaluate(() => window.__kapaCalls)).toBeUndefined();
    expect(requests).toHaveLength(loaded ? 2 : 0);
    await sibling.close();
  });
}


test("grant synchronizes stale disclosure tabs without autoloading AI", async ({ page }) => {
  const requests = [];
  const fulfillBundle = async route => {
    requests.push(route.request().url());
    await route.fulfill({ status: 200, contentType: "text/javascript", body: mockBundle });
  };
  await page.route("https://widget.kapa.ai/kapa-widget.bundle.js*", fulfillBundle);
  await page.context().route("https://widget.kapa.ai/kapa-widget.bundle.js*", fulfillBundle);
  await page.goto(AI_ORIGIN + "/docs/");
  const sibling = await page.context().newPage();
  await sibling.goto(AI_ORIGIN + "/cn/docs/");
  await expect(sibling.locator("[data-hg-ai-consent]")).toBeVisible();
  await page.locator("[data-hg-ai-continue]").click();
  await expect.poll(() => requests.length).toBe(1);
  await expect(sibling.locator("[data-hg-ai-consent]")).toBeHidden();
  await expect(sibling.locator(".hg-ask-ai-launcher")).toBeVisible();
  await expect(sibling.locator("[data-hg-ai-revoke]")).toBeVisible();
  await expect(sibling.locator("script[data-hg-kapa-widget]")).toHaveCount(0);
  expect(requests).toHaveLength(1);
  await sibling.close();
});


test("blocked storage page-only consent can be revoked after loading AI", async ({ page }) => {
  const requests = [];
  await page.addInitScript(() => {
    Object.defineProperty(window, "localStorage", {
      get() { throw new DOMException("Storage disabled", "SecurityError"); },
    });
  });
  await page.route("https://widget.kapa.ai/kapa-widget.bundle.js*", async route => {
    requests.push(route.request().url());
    await route.fulfill({ status: 200, contentType: "text/javascript", body: mockBundle });
  });
  await page.goto(AI_ORIGIN + "/docs/");
  await page.locator("[data-hg-ai-continue]").click();
  await expect.poll(() => requests.length).toBe(1);
  await expect(page.locator(".hg-ask-ai-launcher")).toHaveAttribute("data-hg-ai-state", "ready");
  await page.locator("[data-hg-ai-revoke]").click();
  await expect(page.locator("[data-hg-ai-consent]")).toBeVisible();
  await expect(page.locator("[data-hg-ai-revoke]")).toBeHidden();
  await expect(page.locator("script[data-hg-kapa-widget]")).toHaveCount(0);
  expect(await page.evaluate(() => window.__kapaCalls)).toBeUndefined();
  expect(requests).toHaveLength(1);
});
