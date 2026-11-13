const { test, expect } = require('./artifact-test');

const VERSION_IDS = ['latest', '1.7', '1.5', '1.3', '1.0'];
const EXPECTED_IDS = (process.env.EXPECTED_VERSIONS || VERSION_IDS.join(',')).split(',');

function versionPrefix(version) {
  return version === 'latest' ? '' : `/versions/${version}`;
}

function docsRoute(version, locale) {
  return `${versionPrefix(version)}${locale === 'cn' ? '/cn' : ''}/docs/`;
}

function alternateDocsRoute(version, locale) {
  return docsRoute(version, locale === 'cn' ? 'en' : 'cn');
}

async function config(page) {
  return page.locator('#td-compare-config').evaluate(node => JSON.parse(node.textContent));
}

async function actionManifest(page) {
  return page.locator('#td-action-manifest').evaluate(node => JSON.parse(node.textContent));
}

function paneFrames(page) {
  return page.frames().filter(frame => {
    try {
      return new URL(frame.url()).searchParams.get('oink_compare_pane') === '1';
    } catch (_) {
      return false;
    }
  });
}

async function waitForReadyPanes(page) {
  const dialog = page.locator('dialog[data-td-compare]');
  await expect(dialog).toBeVisible();
  await expect(dialog.locator('[data-td-compare-frame]')).toHaveCount(2);
  await expect.poll(() => paneFrames(page).length).toBe(2);
  for (const frame of paneFrames(page)) {
    await expect.poll(() => frame.evaluate(() => Boolean(
      window.OinkComparePane &&
      document.documentElement.hasAttribute('data-td-compare-pane') &&
      document.querySelector('meta[name="oink-compare-page"]') &&
      document.querySelector('#td-main-content .td-content')
    ))).toBe(true);
  }
  await expect(dialog.locator('[data-td-compare-sync]')).toBeEnabled();
  return dialog;
}

async function visiblePaneCount(dialog) {
  return dialog.locator('[data-td-compare-side]').evaluateAll(nodes => nodes.filter(node => {
    const style = getComputedStyle(node);
    return style.visibility !== 'hidden' && style.display !== 'none';
  }).length);
}

for (const version of VERSION_IDS) {
  for (const locale of ['en', 'cn']) {
    test(`${version} ${locale} uses native Duo View on desktop and one-pane mobile`, async ({ page }) => {
      test.skip(!EXPECTED_IDS.includes(version), 'version not selected for this artifact');
      await page.setViewportSize({ width: 1440, height: 900 });
      const route = docsRoute(version, locale);
      await page.goto(route);

      const descriptor = await config(page);
      expect(descriptor.current.url).toBe(route);
      expect(descriptor.targets.map(target => target.url)).toContain(alternateDocsRoute(version, locale));
      expect(descriptor.shortcut).toBe('B');
      const manifest = await actionManifest(page);
      expect(manifest.actions.find(action => action.id === 'compare_translations')).toMatchObject({
        available: true,
        kind: 'invoke',
      });

      const entry = page.locator('[data-td-compare-open]');
      await expect(entry).toBeVisible();
      await expect(entry).toHaveAttribute('aria-keyshortcuts', 'B');
      await entry.click();
      const dialog = await waitForReadyPanes(page);
      await expect.poll(() => visiblePaneCount(dialog)).toBe(2);

      await page.setViewportSize({ width: 390, height: 844 });
      const tabs = dialog.locator('.td-compare__tab');
      await expect(tabs).toHaveCount(2);
      await expect(tabs.first()).toHaveAttribute('aria-pressed', 'true');
      await expect.poll(() => visiblePaneCount(dialog)).toBe(1);
      await tabs.nth(1).click();
      await expect(tabs.nth(1)).toHaveAttribute('aria-pressed', 'true');
      await expect.poll(() => visiblePaneCount(dialog)).toBe(1);

      await dialog.locator('[data-td-compare-close]').click();
      await expect(page.locator('dialog[data-td-compare]')).toHaveCount(0);
    });
  }
}

test('real Docs pair is lazy, pane-isolated, synchronized and history-restorable', async ({ page }) => {
  const runtimeRequests = [];
  const thirdPartyRequests = [];
  page.on('request', request => {
    if (request.url().includes('document-compare')) runtimeRequests.push(request.url());
    if (/kapa\.ai|hcaptcha\.com|kapa-widget-proxy/.test(request.url())) thirdPartyRequests.push(request.url());
  });

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/docs/quickstart/hugegraph/hugegraph-server/');
  expect(runtimeRequests).toEqual([]);
  const descriptor = await config(page);
  expect(descriptor.targets.map(target => target.url)).toContain(
    '/cn/docs/quickstart/hugegraph/hugegraph-server/'
  );

  await page.keyboard.press('b');
  let dialog = await waitForReadyPanes(page);
  expect(runtimeRequests.length).toBeGreaterThan(0);
  let frames = paneFrames(page);
  for (const frame of frames) {
    expect(await frame.evaluate(() => ({
      shell: typeof window.HugeGraphShell,
      kapa: typeof window.HugeGraphKapa,
      pane: window.OinkComparePane,
    }))).toEqual({ shell: 'undefined', kapa: 'undefined', pane: true });
  }
  expect(thirdPartyRequests).toEqual([]);

  const sync = dialog.locator('[data-td-compare-sync]');
  await expect(sync).toHaveAttribute('role', 'switch');
  await expect(sync).toHaveAttribute('aria-checked', 'true');
  await sync.click();
  await expect(sync).toHaveAttribute('aria-checked', 'false');
  await sync.click();
  await expect(sync).toHaveAttribute('aria-checked', 'true');

  await frames[0].evaluate(() => window.scrollTo({
    top: Math.max(500, document.documentElement.scrollHeight * 0.55),
    behavior: 'instant',
  }));
  await expect.poll(() => frames[1].evaluate(() => window.scrollY)).toBeGreaterThan(100);
  const firstFollowerPosition = await frames[1].evaluate(() => window.scrollY);
  await frames[0].evaluate(() => window.scrollTo({
    top: document.documentElement.scrollHeight * 0.8,
    behavior: 'instant',
  }));
  await expect.poll(() => frames[1].evaluate(() => window.scrollY))
    .toBeGreaterThan(firstFollowerPosition + 20);

  const followerBeforeFragment = await frames[1].evaluate(() => window.scrollY);
  const selfLink = frames[0].locator('#td-main-content .td-content a.td-heading-self-link').nth(2);
  await expect(selfLink).toBeAttached();
  await selfLink.click();
  await expect.poll(() => new URL(frames[0].url()).hash.length).toBeGreaterThan(1);
  await expect.poll(async () => Math.abs(
    await frames[1].evaluate(() => window.scrollY) - followerBeforeFragment
  )).toBeGreaterThan(20);

  await page.waitForTimeout(450);
  await page.reload();
  dialog = await waitForReadyPanes(page);
  frames = paneFrames(page);
  await expect.poll(() => frames[0].evaluate(() => window.scrollY)).toBeGreaterThan(100);
  await expect.poll(() => frames[1].evaluate(() => window.scrollY)).toBeGreaterThan(100);

  await page.keyboard.press('b');
  await expect(page.locator('dialog[data-td-compare]')).toHaveCount(0);
  await expect.poll(() => page.evaluate(() => Boolean(history.state?.oinkCompareReader))).toBe(false);
  await page.goForward();
  await waitForReadyPanes(page);
  await page.goBack();
  await expect(page.locator('dialog[data-td-compare]')).toHaveCount(0);

  await page.locator('[data-td-shell-search-open]').first().click();
  const input = page.locator('.td-shell-search__input');
  await input.fill('>Duo View');
  const command = page.locator('[role="option"]').filter({ hasText: 'Duo View' }).first();
  await expect(command).toBeVisible();
  await command.click();
  await waitForReadyPanes(page);
});

test('real Blog translation coexists with search, Print, Markdown and RSS', async ({ page, request }) => {
  const route = '/blog/2025/10/09/toplingdb-quick-start/';
  await page.goto(route);
  const descriptor = await config(page);
  expect(descriptor.targets.map(target => target.url)).toContain(
    '/cn/blog/2025/10/09/toplingdb-quick-start/'
  );
  await page.locator('[data-td-compare-open]').click();
  const dialog = await waitForReadyPanes(page);
  await dialog.locator('[data-td-compare-close]').click();
  await page.locator('[data-td-shell-search-open]').first().click();
  await page.locator('.td-shell-search__input').fill('ToplingDB');
  await expect(page.locator('[role="option"]').first()).toBeVisible();

  for (const output of ['/blog/index.xml', '/_print/docs/', `${route}index.md`]) {
    const response = await request.get(output);
    expect(response.ok(), output).toBeTruthy();
    const body = await response.text();
    expect(body, output).not.toContain('id="td-compare-config"');
    expect(body, output).not.toMatch(/<button[^>]+data-td-compare-open/);
  }
});

test('a real one-language page exposes no Duo View entry or command', async ({ page }) => {
  await page.goto('/cn/docs/changelog/hugegraph-0.10.4-release-notes/');
  await expect(page.locator('#td-compare-config')).toHaveCount(0);
  await expect(page.locator('[data-td-compare-open]')).toHaveCount(0);
  const manifest = await actionManifest(page);
  expect(manifest.actions.some(action => action.id === 'compare_translations')).toBe(false);
  await page.keyboard.press('b');
  await expect(page.locator('dialog[data-td-compare]')).toHaveCount(0);
});

test('failed pane times out to an accessible retry and recovers', async ({ page }) => {
  await page.addInitScript(() => {
    const nativeSetTimeout = window.setTimeout.bind(window);
    window.setTimeout = (callback, delay, ...args) =>
      nativeSetTimeout(callback, delay === 15000 ? 80 : delay, ...args);
  });
  let held = false;
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (!held && url.pathname === '/cn/docs/' && url.searchParams.get('oink_compare_pane') === '1') {
      held = true;
      await new Promise(resolve => setTimeout(resolve, 250));
      try { await route.abort('failed'); } catch (_) { /* The timed-out frame may already be gone. */ }
      return;
    }
    await route.fallback();
  });

  await page.goto('/docs/');
  await page.locator('[data-td-compare-open]').click();
  const dialog = page.locator('dialog[data-td-compare]');
  await expect(dialog).toBeVisible();
  const failure = dialog.locator('.td-compare__failure');
  await expect(failure).toBeVisible();
  await expect(failure).toContainText('Could not load this page.');
  const retry = failure.locator('.td-compare__retry');
  await expect(retry).toHaveAccessibleName('Retry');
  await expect(failure.locator('a[target="_blank"]')).toHaveAttribute('rel', 'noopener');
  await retry.click();
  await waitForReadyPanes(page);
});
