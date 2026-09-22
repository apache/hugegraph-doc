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
