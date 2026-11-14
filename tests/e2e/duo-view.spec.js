const { test, expect } = require('./artifact-test');

const VERSION_IDS = ['latest', '1.7', '1.5', '1.3', '1.0'];
const EXPECTED_IDS = new Set((process.env.EXPECTED_VERSIONS || VERSION_IDS.join(','))
  .split(',').map(value => value.trim()).filter(Boolean));

function docsRoute(version, locale, relative = '') {
  const versionPrefix = version === 'latest' ? '' : `/versions/${version}`;
  const languagePrefix = locale === 'cn' ? '/cn' : '';
  return `${versionPrefix}${languagePrefix}/docs/${relative}`;
}

async function compareConfig(page) {
  return page.locator('#td-compare-config').evaluate(node => JSON.parse(node.textContent));
}

function resolvedURL(page, value) {
  return new URL(value, page.url());
}

async function actionManifest(page) {
  return page.locator('#td-action-manifest').evaluate(node => JSON.parse(node.textContent));
}

async function paneFrames(page) {
  const dialog = page.locator('dialog[data-td-compare]');
  await expect(dialog).toBeVisible({ timeout: 15_000 });
  // OINK keeps aria-busy while loading and removes failed frames on error.
  const locators = dialog.locator('.td-compare__body:not([aria-busy]) > iframe[data-td-compare-frame]');
  await expect(locators).toHaveCount(2, { timeout: 15_000 });
  const frames = [];
  for (let index = 0; index < 2; index += 1) {
    const handle = await locators.nth(index).elementHandle();
    const frame = await handle.contentFrame();
    await frame.waitForFunction(() => window.OinkComparePane === true &&
      document.querySelector('meta[name="oink-compare-page"]')?.content === location.pathname &&
      Boolean(document.querySelector('#td-main-content .td-content')));
    frames.push(frame);
  }
  return { dialog, locators, frames };
}

async function closeReader(page) {
  const dialog = page.locator('dialog[data-td-compare]');
  if (await dialog.count()) {
    await dialog.locator('[data-td-compare-close]').click();
    await expect(dialog).toHaveCount(0);
    await expect.poll(() => page.evaluate(() => history.state?.oinkCompareReader || null)).toBe(null);
  }
}

for (const version of VERSION_IDS) {
  for (const locale of ['en', 'cn']) {
    test(`${version} ${locale} Duo View covers desktop and mobile Docs`, async ({ page }) => {
      test.skip(!EXPECTED_IDS.has(version), 'version absent from this aggregate artifact');
      test.setTimeout(60_000);
      const route = docsRoute(version, locale);
      const expectedTarget = docsRoute(version, locale === 'en' ? 'cn' : 'en');

      for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
        await page.setViewportSize(viewport);
        await page.goto(route);
        const darkMobile = version === 'latest' && locale === 'cn' && viewport.width < 900;
        if (darkMobile) {
          await page.evaluate(() => localStorage.setItem('td-color-theme', 'dark'));
          await page.reload({ waitUntil: 'domcontentloaded' });
          await expect(page.locator('html')).toHaveAttribute('data-bs-theme', 'dark');
        }
        const entry = page.locator('[data-td-compare-open]');
        await expect(entry).toBeVisible();
        const config = await compareConfig(page);
        expect(resolvedURL(page, config.current.url).pathname).toBe(route);
        expect(config.targets).toHaveLength(1);
        expect(resolvedURL(page, config.targets[0].url).pathname).toBe(expectedTarget);
        const manifest = await actionManifest(page);
        expect(manifest.actions.some(action => action.id === 'compare_translations')).toBe(true);
        expect(manifest.actions.some(action => action.id === 'switch_version')).toBe(true);

        const targetLocale = locale === 'en' ? 'zh-CN' : 'en-US';
        const alternate = page.locator(`link[rel="alternate"][hreflang="${targetLocale}"]`);
        await expect(alternate).toHaveCount(1);
        expect(new URL(await alternate.getAttribute('href')).pathname).toBe(expectedTarget);
        expect(new URL(await page.locator('link[rel="canonical"]').getAttribute('href')).pathname).toBe(route);

        await entry.click();
        const { dialog, locators, frames } = await paneFrames(page);
        await expect(dialog).toHaveAccessibleName(locale === 'cn' ? '双列视图' : 'Duo View');
        await expect(locators.nth(0)).toHaveAttribute('title', config.current.label);
        await expect(locators.nth(1)).toHaveAttribute('title', config.targets[0].label);
        await expect(dialog.locator('[data-td-compare-close]')).toHaveAttribute('aria-keyshortcuts', /Escape B/);

        const panes = dialog.locator('[data-td-compare-side]');
        if (viewport.width >= 900) {
          await expect(panes.nth(0)).toHaveAttribute('aria-hidden', 'false');
          await expect(panes.nth(1)).toHaveAttribute('aria-hidden', 'false');
        } else {
          await expect(dialog.locator('.td-compare__tab')).toHaveCount(2);
          await expect(panes.nth(0)).toHaveAttribute('aria-hidden', 'false');
          await expect(panes.nth(1)).toHaveAttribute('aria-hidden', 'true');
          await dialog.locator('.td-compare__tab').nth(1).click();
          await expect(panes.nth(0)).toHaveAttribute('aria-hidden', 'true');
          await expect(panes.nth(1)).toHaveAttribute('aria-hidden', 'false');
        }

        for (const [index, frame] of frames.entries()) {
          expect(await frame.evaluate(() => new URL(location.href).searchParams.get('oink_compare_pane'))).toBe('1');
          const canonicalPath = await frame.locator('link[rel="canonical"]').evaluate(node => new URL(node.href).pathname);
          expect(canonicalPath).toBe(index === 0 ? route : expectedTarget);
          expect(await frame.evaluate(() => document.querySelector('.hg-ask-ai-launcher')?.dataset.hgAiBound)).toBeUndefined();
          if (darkMobile) {
            expect(await frame.evaluate(() => document.documentElement.getAttribute('data-bs-theme'))).toBe('dark');
          }
          const launcher = frame.locator('.hg-ask-ai-launcher');
          if (await launcher.count()) await expect(launcher).toBeHidden();
        }
        await closeReader(page);
      }
    });
  }
}

test('real Docs page lazily opens, synchronizes, restores and exposes all native entries', async ({ page }) => {
  test.setTimeout(90_000);
  const requested = [];
  page.on('request', request => requested.push(request.url()));
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/docs/quickstart/hugegraph/hugegraph-server/');
  expect(await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches)).toBe(true);

  const config = await compareConfig(page);
  const targetPath = resolvedURL(page, config.targets[0].url).pathname;
  expect(requested.some(url => url.includes('document-compare'))).toBe(false);
  expect(requested.some(url => new URL(url).pathname === targetPath)).toBe(false);

  const readingHeading = page.locator('#td-main-content .td-content h2[id]').nth(2);
  await readingHeading.scrollIntoViewIfNeeded();
  const sourceScroll = await page.evaluate(() => scrollY);
  expect(sourceScroll).toBeGreaterThan(0);

  await page.keyboard.press('b');
  let { dialog, frames } = await paneFrames(page);
  expect(requested.some(url => url.includes('document-compare'))).toBe(true);
  expect(requested.some(url => new URL(url).pathname === targetPath)).toBe(true);
  const sync = dialog.locator('[data-td-compare-sync]');
  await expect(sync).toBeEnabled();
  await expect(sync).toHaveAttribute('aria-checked', 'true');
  await sync.click();
  await expect(sync).toHaveAttribute('aria-checked', 'false');
  await sync.click();
  await expect(sync).toHaveAttribute('aria-checked', 'true');
  expect(await frames[0].evaluate(() => scrollY)).toBeGreaterThan(0);
  await expect.poll(() => frames[1].evaluate(() => scrollY)).toBeGreaterThan(0);

  const targetBefore = await frames[1].evaluate(() => scrollY);
  await frames[0].evaluate(() => {
    document.dispatchEvent(new WheelEvent('wheel', { bubbles: true }));
    window.scrollTo({ top: Math.min(document.documentElement.scrollHeight - innerHeight, scrollY + 700), behavior: 'instant' });
  });
  await expect.poll(() => frames[1].evaluate(() => scrollY)).not.toBe(targetBefore);
  const targetAfterFirstMove = await frames[1].evaluate(() => scrollY);
  await frames[0].evaluate(() => {
    document.dispatchEvent(new WheelEvent('wheel', { bubbles: true }));
    window.scrollBy({ top: 500, behavior: 'instant' });
  });
  await expect.poll(() => frames[1].evaluate(() => scrollY)).not.toBe(targetAfterFirstMove);

  const fragment = await frames[0].evaluate(() => {
    const heading = [...document.querySelectorAll('#td-main-content .td-content h2[id], #td-main-content .td-content h3[id]')]
      .find(node => node.getBoundingClientRect().height > 0 && node.id);
    if (!heading) return null;
    const link = [...document.querySelectorAll('a[href]')].find(anchor => {
      try { return new URL(anchor.href).hash === `#${heading.id}`; } catch (_) { return false; }
    });
    if (!link) return null;
    link.click();
    return `#${heading.id}`;
  });
  expect(fragment).toBeTruthy();
  await expect.poll(() => frames[0].evaluate(() => location.hash)).toBe(fragment);

  await page.keyboard.press('b');
  await expect(page.locator('dialog[data-td-compare]')).toHaveCount(0);
  await expect.poll(() => page.evaluate(() => history.state?.oinkCompareReader || null)).toBe(null);

  await page.locator('[data-td-shell-search-open]').first().click();
  const input = page.locator('.td-shell-search__input');
  await input.fill('Duo View');
  await page.getByRole('group', { name: 'Actions' }).getByText('Duo View', { exact: true }).click();
  ({ dialog } = await paneFrames(page));

  await page.reload({ waitUntil: 'domcontentloaded' });
  ({ dialog, frames } = await paneFrames(page));
  expect(await frames[0].evaluate(() => scrollY)).toBeGreaterThan(0);
  await page.goBack();
  await expect(page.locator('dialog[data-td-compare]')).toHaveCount(0);
  await page.goForward();
  await expect(page.locator('dialog[data-td-compare]')).toBeVisible({ timeout: 15_000 });
  await closeReader(page);
});

test('Duo View times out a stalled pane, retries and keeps an explicit direct link', async ({ page }) => {
  test.setTimeout(45_000);
  await page.goto('/docs/quickstart/hugegraph/hugegraph-server/');
  const config = await compareConfig(page);
  const target = resolvedURL(page, config.targets[0].url);
  await page.evaluate(() => {
    const nativeTimeout = window.setTimeout.bind(window);
    let paneTimeouts = 0;
    window.setTimeout = (callback, delay, ...args) => {
      if (delay === 15_000) {
        paneTimeouts += 1;
        // OINK loads the source pane first and the target pane second. Fail
        // only the target's first attempt; the source and retry keep the real
        // timeout so this test cannot manufacture a two-pane race.
        if (paneTimeouts === 2) return nativeTimeout(callback, 100, ...args);
      }
      return nativeTimeout(callback, delay, ...args);
    };
  });
  let attempts = 0;
  await page.route(url => url.pathname === target.pathname && url.searchParams.get('oink_compare_pane') === '1', async route => {
    attempts += 1;
    if (attempts === 1) {
      await new Promise(resolve => setTimeout(resolve, 300));
      try { await route.continue(); } catch (_) { /* Timed-out iframe was disposed. */ }
    } else {
      await route.continue();
    }
  });

  await page.locator('[data-td-compare-open]').click();
  const dialog = page.locator('dialog[data-td-compare]');
  await expect(dialog).toBeVisible();
  const retry = dialog.locator('.td-compare__retry');
  await expect(retry).toBeVisible({ timeout: 15_000 });
  const direct = retry.locator('xpath=following-sibling::a');
  await expect(direct).toHaveAttribute('href', target.href);
  await expect(direct).toHaveAttribute('target', '_blank');
  await expect(direct).toHaveAttribute('rel', 'noopener');

  await retry.click();
  const { frames } = await paneFrames(page);
  expect(attempts).toBe(2);
  expect(await frames[1].evaluate(() => document.querySelector('meta[name="oink-compare-page"]')?.content)).toBe(target.pathname);
  await closeReader(page);
});

test('draft/missing peers and non-HTML outputs never expose Duo View', async ({ page, request }) => {
  await page.goto('/cn/docs/changelog/hugegraph-0.12.0-release-notes/');
  await expect(page.locator('[data-td-compare-open]')).toHaveCount(0);
  await expect(page.locator('#td-compare-config')).toHaveCount(0);
  const manifest = await actionManifest(page);
  expect(manifest.actions.some(action => action.id === 'compare_translations')).toBe(false);

  for (const route of [
    '/docs/quickstart/hugegraph/hugegraph-server/index.md',
    '/_print/docs/',
    '/docs/index.xml',
  ]) {
    const response = await request.get(route);
    expect(response.ok(), route).toBeTruthy();
    const body = await response.text();
    expect(body, route).not.toContain('td-compare-config');
    expect(body, route).not.toContain('data-td-compare-open');
  }
});

for (const [locale, route] of [
  ['en', '/blog/2025/10/09/toplingdb-quick-start/'],
  ['cn', '/cn/blog/2025/10/09/toplingdb-quick-start/'],
]) {
  test(`${locale} real Blog page uses native Duo View without preloading the peer`, async ({ page }) => {
    const requested = [];
    page.on('request', request => requested.push(request.url()));
    await page.goto(route);
    const config = await compareConfig(page);
    const target = resolvedURL(page, config.targets[0].url);
    await expect(page.locator('[data-td-compare-open]')).toBeVisible();
    expect(requested.some(url => new URL(url).pathname === target.pathname)).toBe(false);
    await page.locator('[data-td-compare-open]').click();
    await paneFrames(page);
    expect(requested.some(url => new URL(url).pathname === target.pathname)).toBe(true);
    expect(requested.filter(url => /(?:kapa\.ai|hcaptcha\.com|a\.run\.app)/.test(url))).toEqual([]);
    await closeReader(page);
  });
}
