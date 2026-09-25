const { test, expect } = require('./artifact-test');

const expectedVersions = (process.env.EXPECTED_VERSIONS || 'latest,1.7,1.5,1.3,1.0').split(',');

for (const prefix of ['', '/cn', '/versions/1.7', '/versions/1.7/cn']) {
  test(`print preserves authored content after theme upgrade: ${prefix || 'en'}`, async ({ page }) => {
    const versionId = prefix.startsWith('/versions/1.7') ? '1.7' : 'latest';
    test.skip(!expectedVersions.includes(versionId), 'version not selected for this artifact');
    await page.goto(`${prefix}/docs/introduction/`);
    const excerpt = (await page.locator('.td-content p').first().innerText()).trim();
    expect(excerpt.length).toBeGreaterThan(10);
    // Print URLs put the output prefix inside the selected version's base path.
    const version = prefix.startsWith('/versions/1.7') ? '/versions/1.7' : '';
    const language = prefix.endsWith('/cn') ? '/cn' : '';
    const response = await page.goto(`${version}${language}/_print/docs/`);
    expect(response.status()).toBe(200);
    await expect(page.locator('body')).toContainText(excerpt);
    expect(await page.locator('template[data-hg-authored-content="start"]').count()).toBeGreaterThan(0);
    await expect(page.locator('body')).not.toContainText('map[book:');
  });
}

test.describe('without JavaScript', () => {
  test.use({ javaScriptEnabled: false });
  test('server-rendered documentation remains navigable', async ({ page }) => {
    await page.goto('/cn/docs/');
    const sidebar = page.locator('#td-shell-sidebar');
    await expect(sidebar).toBeVisible();
    await expect(sidebar.locator('a[href]').first()).toBeVisible();
    await expect(sidebar).not.toHaveAttribute('inert', '');
  });
});

test('blocked storage leaves active-path navigation usable', async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('Blocked', 'SecurityError'); } });
  });
  await page.goto('/docs/introduction/');
  const active = page.locator('#td-shell-sidebar .td-active-path [data-td-shell-tree-toggle]').first();
  await expect(active).toHaveAttribute('aria-expanded', 'true');
  await expect(page.locator('#td-shell-sidebar .td-shell-tree__link[aria-current="page"]')).toBeVisible();
});

test('aside TOC user preference persists across reload', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.addInitScript(() => localStorage.setItem('oink.sidebar.v2.latest.en', '[]'));
  await page.goto('/docs/introduction/');
  await page.evaluate(() => window.OinkSidebar.ready);
  const toggle = page.locator('[data-td-shell-aside] [aria-controls="td-shell-aside-toc"]');
  await expect(toggle).toBeVisible();
  await expect(toggle).toHaveAttribute('aria-expanded', 'true');
  await toggle.click();
  await expect(toggle).toHaveAttribute('aria-expanded', 'false');
  await page.reload();
  await page.evaluate(() => window.OinkSidebar.ready);
  await expect(toggle).toHaveAttribute('aria-expanded', 'false');
  await toggle.click();
  await expect.poll(() => page.evaluate(() => JSON.parse(localStorage.getItem('oink.sidebar.v3.latest.en'))))
    .toContain('td-shell-aside-toc');
  await page.reload();
  await page.evaluate(() => window.OinkSidebar.ready);
  await expect(toggle).toHaveAttribute('aria-expanded', 'true');
});

test('AI activation uses live text within the palette debounce window', async ({ page }) => {
  test.skip(!process.env.AI_SITE_ROOT, 'AI-enabled fixture was not built');
  await page.goto('http://127.0.0.1:4174/docs/');
  await page.locator('[data-td-shell-search-open]').first().click();
  const input = page.locator('.td-shell-search__input');
  await input.fill('zzzxqstalezzzxq');
  const tail = page.getByRole('option').filter({ hasText: 'Ask AI:' });
  await expect(tail).toBeVisible();
  await expect(tail).toHaveAttribute('aria-selected', 'true');
  // One browser task guarantees Enter precedes OINK's 80 ms render timer.
  await input.evaluate(input => {
    input.value = 'zzzxqfreshzzzxq';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
  });
  await expect(page.locator('[data-hg-ai-consent]')).toBeVisible();
  await page.route('https://widget.kapa.ai/kapa-widget.bundle.js*', route => route.fulfill({
    contentType: 'text/javascript', body: `
      var queued = window.Kapa.q.slice();
      window.Kapa = function(method, value) {
        if (method === 'render') value.onRender();
        if (method === 'open') window.__submittedQuery = value.query;
      };
      queued.forEach(args => window.Kapa(...args));`,
  }));
  // Keep the consent open across the delayed render; it must not abort the handoff.
  await page.waitForTimeout(160);
  await expect(page.locator('[data-hg-ai-consent]')).toBeVisible();
  await page.locator('[data-hg-ai-continue]').click();
  await expect.poll(() => page.evaluate(() => window.__submittedQuery)).toBe('zzzxqfreshzzzxq');
});
