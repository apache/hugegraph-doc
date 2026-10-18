const { test, expect } = require('./artifact-test');

const expectedVersions = (process.env.EXPECTED_VERSIONS || 'latest,1.7,1.5,1.3,1.0').split(',');

const appearanceTrigger = '[data-td-appearance-trigger][aria-controls="td-appearance-navbar"]';

// These exercise the adopted components on real documentation, including
// their original content and destinations, rather than a component fixture.
for (const language of ['en', 'cn']) {
  const prefix = language === 'cn' ? '/cn' : '';
  const quickStart = `${prefix}/blog/2025/10/09/toplingdb-quick-start/`;
  const configuration = `${prefix}/blog/2025/09/30/toplingdb-yaml-configuration-file/`;

  for (const preset of ['slate', 'paper']) {
    for (const theme of ['light', 'dark']) {
      test(`${language} ${preset} ${theme} taxonomy rail avoids the footer after resizing and reflow`, async ({ page }) => {
        await page.addInitScript(({ preset, theme }) => {
          localStorage.setItem('td-preset', preset);
          localStorage.setItem('td-color-theme', theme);
        }, { preset, theme });
        await page.goto(quickStart);
        const rail = page.locator('.td-shell-toc__panel');
        const footer = page.locator('footer');
        const expectClearFooter = async () => {
          await footer.scrollIntoViewIfNeeded();
          await expect.poll(async () => {
            const panel = await rail.boundingBox();
            const bottom = await footer.boundingBox();
            return panel.y + panel.height <= bottom.y + 1;
          }).toBe(true);
        };
        for (const viewport of [{ width: 1440, height: 1000 }, { width: 1280, height: 760 }, { width: 1600, height: 900 }]) {
          await page.setViewportSize(viewport);
          await expectClearFooter();
        }
        // Reflow after load must update the native footer offset too.
        await footer.evaluate(node => { node.style.minHeight = '280px'; });
        await expectClearFooter();
        const tags = rail.locator('a[href*="/tags/"]').last();
        await tags.scrollIntoViewIfNeeded();
        const box = await tags.boundingBox();
        const bottom = await footer.boundingBox();
        expect(box.y + box.height).toBeLessThanOrEqual(bottom.y + 1);
        await tags.click();
        await expect(page).toHaveURL(/\/tags\//);
        await expect(page.locator('main')).toContainText('Workflow');
      });
    }
  }

  test(`${language} native code blocks inherit global inline line numbers without custom headers`, async ({ page }) => {
    for (const route of ['config/config-backend-rocksdb', 'clients/restful-api/vertex', 'quickstart/hugegraph/hugegraph-server',
      'clients/restful-api/cypher', 'quickstart/toolchain/import/hugegraph-seatunnel-connector']) {
      await page.goto(`${prefix}/docs/${route}/`);
      const blocks = page.locator('[data-td-code]');
      expect(await blocks.count()).toBeGreaterThan(0);
      await expect(blocks.locator('.td-code__filename')).toHaveCount(0);
      const results = await blocks.evaluateAll(nodes => nodes.map(node => ({
        language: node.getAttribute('data-td-language'),
        numbers: node.querySelectorAll('.ln').length,
        tables: node.querySelectorAll('.lntable').length
      })));
      for (const result of results) {
        expect(result.language).toBeTruthy();
        expect(result.numbers, `${route}: ${result.language}`).toBeGreaterThan(0);
        expect(result.tables).toBe(0);
      }
      if (route === 'quickstart/hugegraph/hugegraph-server') {
        const listener = blocks.filter({ hasText: 'vim conf/rest-server.properties' });
        await expect(listener).toHaveCount(1);
        await expect(listener.locator('.ln')).toHaveCount(3);
        expect(await listener.textContent()).not.toContain('```');
      }
    }
  });

  test(`${language} RocksDB parameter identifiers stay readable on desktop and mobile`, async ({ page }) => {
    for (const width of [1280, 320]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(`${prefix}/docs/config/config-backend-rocksdb/`);
      await page.evaluate(() => document.fonts.ready);
      const cells = page.locator('.td-table-scroll tbody tr > td:first-child');
      expect(await cells.count()).toBeGreaterThan(20);
      const identifiers = await cells.evaluateAll(nodes => nodes.map(node => {
        const range = document.createRange();
        range.selectNodeContents(node);
        return { text: node.textContent.trim(), lines: range.getClientRects().length };
      }));
      for (const identifier of identifiers) {
        expect(identifier.text).toMatch(/^rocksdb\./);
        expect(identifier.lines, `${width}px: ${identifier.text}`).toBe(1);
      }
      expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
      if (width === 320) {
        const wrapper = page.locator('.td-table-scroll').first();
        expect(await wrapper.evaluate(node => node.scrollWidth > node.clientWidth)).toBe(true);
        await wrapper.focus();
        await page.keyboard.press('ArrowRight');
        await expect.poll(() => wrapper.evaluate(node => node.scrollLeft)).toBeGreaterThan(0);
      }
    }
  });

  test(`${language} RocksDB file tree preserves store explanations and supports folding and keyboard resizing`, async ({ page }) => {
    await page.goto(`${prefix}/docs/config/config-backend-rocksdb/`);
    const tree = page.locator('.td-filetree');
    await expect(tree).toBeVisible();
    const data = tree.locator('details').filter({ has: page.locator(':scope > summary .td-filetree__name', { hasText: /^data\/$/ }) });
    for (const [name, explanation] of [['m/', 'schema store'], ['g/', 'graph store'], ['s/', 'system store']]) {
      const row = data.locator('.td-filetree__row').filter({ has: page.locator('.td-filetree__name', { hasText: name }) });
      await expect(row).toContainText(explanation);
    }
    const schemaComment = data.locator('.td-filetree__comment-text').filter({ hasText: 'schema store' });
    await expect(schemaComment).toBeVisible();
    await data.locator(':scope > summary').press('Enter');
    await expect(schemaComment).toBeHidden();
    await data.locator(':scope > summary').press('Enter');
    await expect(schemaComment).toBeVisible();
    const divider = tree.getByRole('separator');
    await divider.focus();
    await divider.press('Home');
    await expect(divider).toHaveAttribute('aria-valuenow', '50');
    await divider.press('ArrowRight');
    await expect(divider).toHaveAttribute('aria-valuenow', '52');
    await divider.press('End');
    await expect(divider).toHaveAttribute('aria-valuenow', '70');
    await expect(schemaComment).toBeVisible();
  });

  test(`${language} Server deployment cards link to the four original deployment sections`, async ({ page }) => {
    await page.goto(`${prefix}/docs/quickstart/hugegraph/hugegraph-server/`);
    const cards = page.locator('.td-content ul.cards');
    const links = cards.locator(':scope > li a');
    await expect(links).toHaveCount(4);
    for (const link of await links.all()) {
      const target = new URL(await link.getAttribute('href'), page.url());
      expect(target.pathname).toBe(`${prefix}/docs/quickstart/hugegraph/hugegraph-server/`);
      expect(['https://hugegraph.apache.org', new URL(page.url()).origin]).toContain(target.origin);
      const hash = target.hash;
      expect(hash).toMatch(/^#3[1-4]-/);
      await link.click();
      await expect(page).toHaveURL(url => url.pathname === target.pathname);
      await expect(page).toHaveURL(url => decodeURIComponent(url.hash) === decodeURIComponent(hash));
      await expect(page.locator(`[id=${JSON.stringify(decodeURIComponent(hash.slice(1)))}]`)).toBeVisible();
    }
  });

  test(`${language} Tools tabs keep equivalent CLI and environment commands accessible by keyboard`, async ({ page }) => {
    await page.goto(`${prefix}/docs/quickstart/toolchain/hugegraph-tools/`);
    const tabs = page.locator('.td-tabs').filter({ hasText: 'g.V().count()' });
    const choices = tabs.getByRole('tab');
    await expect(choices).toHaveCount(2);
    const panels = tabs.getByRole('tabpanel', { includeHidden: true });
    await expect(panels).toHaveCount(2);
    for (const panel of await panels.all()) {
      await expect(panel).toContainText('gremlin-execute');
      await expect(panel).toContainText("--script 'g.V().count()'");
      await expect(panel).toContainText('http://127.0.0.1:8080');
      await expect(panel).toContainText('hugegraph');
    }
    await expect(choices.nth(0)).toHaveAttribute('aria-selected', 'true');
    await expect(panels.nth(1)).toBeHidden();
    await choices.nth(0).focus();
    await choices.nth(0).press('ArrowRight');
    await expect(choices.nth(1)).toBeFocused();
    await expect(choices.nth(1)).toHaveAttribute('aria-selected', 'true');
    await expect(panels.nth(0)).toBeHidden();
    await expect(panels.nth(1)).toBeVisible();
    await choices.nth(1).press('Home');
    await expect(choices.nth(0)).toBeFocused();
    await expect(panels.nth(0)).toBeVisible();
  });

  test(`${language} explicit sidebar and section icons keep navigation labels aligned`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goto(`${prefix}/blog/`);
    await page.evaluate(() => document.fonts.ready);
    const sidebar = page.locator('#td-section-nav');
    const labelStarts = [];
    for (const [section, icon] of [
      ['hugegraph', 'fa-database'], ['toolchain', 'fa-screwdriver-wrench'],
      ['hugegraph-ai', 'fa-brain'], ['computing', 'fa-diagram-project']
    ]) {
      const link = sidebar.locator(`a[href$="${prefix}/blog/${section}/"]`);
      await expect(link.locator(`i.${icon}`)).toBeVisible();
      const label = await link.locator(':scope > span').boundingBox();
      expect(label).not.toBeNull();
      labelStarts.push(label.x);
    }
    expect(Math.max(...labelStarts) - Math.min(...labelStarts)).toBeLessThan(1);
    await page.screenshot({ path: testInfo.outputPath(`${language}-sidebar-icons.png`), animations: 'disabled' });

    await page.locator('[data-td-shell-root-toggle]').click();
    const chooser = page.locator('.td-shell-root__pop');
    await expect(chooser).toBeVisible();
    const rootLabels = language === 'cn'
      ? ['Documentation', '关于', '博客', '社区'] : ['Documentation', 'About', 'Blog', 'Community'];
    for (const [index, section] of ['docs', 'about', 'blog', 'community'].entries()) {
      const item = chooser.locator(`a[href$="${prefix}/${section}/"]`);
      await expect(item.locator('.td-shell-root__icon > i')).toBeVisible();
      const label = item.locator('.td-shell-root__item-title');
      await expect(label).toHaveText(rootLabels[index]);
    }
    // Read all positions in one browser frame while the popover animates.
    await expect.poll(() => chooser.locator('.td-shell-root__item-title').evaluateAll(labels => {
      const starts = labels.map(label => label.getBoundingClientRect().x);
      return Math.max(...starts) - Math.min(...starts);
    })).toBeLessThan(1);
    await page.screenshot({ path: testInfo.outputPath(`${language}-navigation-icons.png`), animations: 'disabled' });
  });

  test(`${language} blog covers load and category and series rails lead to real article indexes`, async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goto(`${prefix}/blog/`);
    const card = page.locator('.td-blog-card').filter({ has: page.locator(`a[href$="${quickStart}"]`) });
    const cover = card.locator('.td-blog-card__image');
    await cover.scrollIntoViewIfNeeded();
    await expect.poll(() => cover.evaluate(image => image.complete && image.naturalWidth > 0)).toBe(true);
    await expect(card.locator('.td-blog-meta__author')).toHaveCount(0);
    const aside = page.locator('[data-td-shell-aside]');
    await expect(aside.locator(`[data-td-taxonomy="categories"] a[href$="${prefix}/categories/storage/"]`)).toBeVisible();
    await expect(aside.locator(`[data-td-taxonomy="categories"] a[href$="${prefix}/categories/graph-ai/"]`)).toBeVisible();
    const series = aside.locator(`[data-td-taxonomy="series"] a[href$="${prefix}/series/toplingdb/"]`);
    await expect(series).toBeVisible();
    await series.click();
    const orderedLinks = page.locator('.td-blog-posts-list--numbered h2 > a');
    await expect(orderedLinks).toHaveCount(2);
    await expect(orderedLinks.nth(0)).toHaveAttribute('href', new RegExp(`${quickStart}$`));
    await expect(orderedLinks.nth(1)).toHaveAttribute('href', new RegExp(`${configuration}$`));
    await orderedLinks.nth(0).click();
    const strip = page.locator('.td-series-strip');
    await expect(strip.locator('.td-series-strip__name')).toHaveAttribute('href', new RegExp(`${prefix}/series/toplingdb/$`));
    await strip.locator('summary').press('Enter');
    await expect(strip.locator('.td-series-strip__list')).toBeVisible();
    await expect(strip.locator('a[aria-current="page"]')).toHaveAttribute('href', new RegExp(`${quickStart}$`));
    await strip.locator(`.td-series-strip__list a[href$="${configuration}"]`).click();
    await expect(page).toHaveURL(url => url.pathname === configuration);
    await expect(page.locator('.td-byline')).toHaveCount(0);
    const category = page.locator(`.td-article-meta a[href$="${prefix}/categories/storage/"]`);
    await category.click();
    await expect(page.locator(`.td-blog-posts h2 > a[href$="${quickStart}"]`)).toBeVisible();
    await expect(page.locator(`.td-blog-posts h2 > a[href$="${configuration}"]`)).toBeVisible();
  });
}

for (const language of ['en', 'cn']) {
  const prefix = language === 'cn' ? '/cn' : '';

  test(`${language} appearance keeps style and light preference independent across reload and language`, async ({ page }) => {
    // Language links use the public origin; keep storage on that same origin.
    await page.goto(`https://hugegraph.apache.org${prefix}/docs/introduction/`);
    await expect(page.locator('html')).toHaveAttribute('data-td-preset', 'slate');
    await page.locator(appearanceTrigger).click();
    const panel = page.locator('#td-appearance-navbar');
    await expect(panel.locator('[data-td-preset-value]')).toHaveCount(2);
    await panel.locator('[data-bs-theme-value="dark"]').locator('..').click();
    await panel.locator('[data-td-preset-value="paper"]').locator('..').click();
    await expect(page.locator('html')).toHaveAttribute('data-td-preset', 'paper');
    await expect(page.locator('html')).toHaveAttribute('data-bs-theme', 'dark');
    await expect(panel.locator('[data-bs-theme-value="dark"]')).toBeChecked();
    await panel.locator('[data-bs-theme-value="light"]').locator('..').click();
    await expect(page.locator('html')).toHaveAttribute('data-bs-theme', 'light');
    await expect(page.locator('html')).toHaveAttribute('data-td-preset', 'paper');
    await page.keyboard.press('Escape');
    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('data-td-preset', 'paper');
    await expect(page.locator('html')).toHaveAttribute('data-bs-theme', 'light');
    const targetLanguage = language === 'cn' ? 'en-US' : 'zh-CN';
    await page.locator(`.td-language-selector a[hreflang="${targetLanguage}"]`).first().click();
    await expect(page.locator('html')).toHaveAttribute('lang', targetLanguage);
    await expect(page.locator('html')).toHaveAttribute('data-td-preset', 'paper');
    await expect(page.locator('html')).toHaveAttribute('data-bs-theme', 'light');
    await page.locator(appearanceTrigger).click();
    await expect(panel.locator('[data-td-preset-value="paper"]')).toBeChecked();
    await expect(panel.locator('[data-bs-theme-value="light"]')).toBeChecked();
    await panel.locator('[data-td-preset-value="slate"]').locator('..').click();
    expect(await page.evaluate(() => localStorage.getItem('td-preset'))).toBeNull();
    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('data-td-preset', 'slate');
    await expect(page.locator('html')).toHaveAttribute('data-bs-theme', 'light');
  });

  test(`${language} appearance supports radio keyboard selection and Escape focus restoration`, async ({ page }) => {
    await page.goto(`${prefix}/docs/introduction/`);
    const trigger = page.locator(appearanceTrigger);
    const panel = page.locator('#td-appearance-navbar');
    await trigger.focus();
    await trigger.press('ArrowDown');
    await expect(panel).toBeVisible();
    await expect(trigger).toHaveAttribute('aria-expanded', 'true');
    await expect(panel.locator('[data-td-preset-value="slate"]')).toBeFocused();
    await page.keyboard.press('ArrowLeft');
    await expect(panel.locator('[data-td-preset-value="paper"]')).toBeChecked();
    await expect(page.locator('html')).toHaveAttribute('data-td-preset', 'paper');
    await page.keyboard.press('Escape');
    await expect(panel).toBeHidden();
    await expect(trigger).toHaveAttribute('aria-expanded', 'false');
    await expect(trigger).toBeFocused();
  });

  for (const surface of ['docs', 'home']) {
    test(`${language} ${surface} mobile appearance is modal and preserves its drawer`, async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto(`${prefix}/${surface === 'docs' ? 'docs/' : ''}`);
      const drawerOpener = page.locator(surface === 'docs'
        ? '[data-td-shell-drawer-open]' : '[data-td-landing-menu-toggle]');
      const drawer = page.locator(surface === 'docs' ? '#td-shell-sidebar' : '[data-td-landing-menu]');
      await drawerOpener.click();
      const trigger = drawer.locator('[data-td-appearance-trigger]');
      const panel = drawer.locator('#td-appearance-drawer');
      await trigger.click();
      await expect(panel).toBeVisible();
      expect(await panel.evaluate(node => node.matches(':modal'))).toBe(true);
      const box = await panel.boundingBox();
      expect(box.x).toBeGreaterThanOrEqual(0);
      expect(box.x + box.width).toBeLessThanOrEqual(390);
      expect(box.y + box.height).toBeLessThanOrEqual(844);
      await panel.locator('[data-td-preset-value="paper"]').locator('..').click();
      await expect(page.locator('html')).toHaveAttribute('data-td-preset', 'paper');
      await page.keyboard.press('Escape');
      await expect(panel).toBeHidden();
      await expect(trigger).toBeFocused();
      await expect(drawer).toBeVisible();
      if (surface === 'docs') {
        await expect(page.locator('html')).toHaveAttribute('data-td-shell-drawer', 'open');
        await page.locator('button[data-td-shell-drawer-close]').click();
      } else {
        await expect(drawerOpener).toHaveAttribute('aria-expanded', 'true');
        await page.keyboard.press('Escape');
        await expect(drawer).toBeHidden();
      }
      await expect(drawerOpener).toBeFocused();
      await expect(page.locator('html')).not.toHaveAttribute('data-td-shell-lock', '');
    });
  }

  test(`${language} style switching keeps the reader on the same long-document block`, async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`${prefix}/docs/config/config-guide/`);
    await page.evaluate(async () => {
      await document.fonts.ready;
      window.scrollTo({ top: 1400, behavior: 'instant' });
    });
    expect(await page.evaluate(() => window.scrollY)).toBeGreaterThan(1000);
    await page.locator(appearanceTrigger).click();
    const anchor = await page.evaluate(() => {
      const blocks = document.querySelectorAll('#td-main-content h1, #td-main-content h2, #td-main-content h3, '
        + '#td-main-content p, #td-main-content li, #td-main-content pre, #td-main-content table');
      window.__appearanceReadingBlock = Array.from(blocks).find(block => {
        const rect = block.getBoundingClientRect();
        return rect.bottom > 0 && rect.height > 0;
      });
      return window.__appearanceReadingBlock.getBoundingClientRect().top;
    });
    await page.locator('#td-appearance-navbar [data-td-preset-value="paper"]').locator('..').click();
    await expect(page.locator('html')).toHaveAttribute('data-td-preset', 'paper');
    await page.evaluate(async () => {
      await document.fonts.ready;
      await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    });
    await expect.poll(async () => Math.abs(await page.evaluate(() =>
      window.__appearanceReadingBlock.getBoundingClientRect().top) - anchor)).toBeLessThan(3);
    await page.keyboard.press('Escape');
    await expect.poll(async () => Math.abs(await page.evaluate(() =>
      window.__appearanceReadingBlock.getBoundingClientRect().top) - anchor)).toBeLessThan(3);
    expect(await page.evaluate(() => window.scrollY)).toBeGreaterThan(0);
  });
}

test('Chinese keyword-only summary search displays the authored description', async ({ page }) => {
  const fs = require('node:fs');
  const path = require('node:path');
  const root = process.env.SITE_ROOT;
  const indexName = fs.readdirSync(root).find(name => /^offline-search-index\.cn\..*\.json$/.test(name));
  expect(indexName, 'Chinese search index must be present in the artifact').toBeTruthy();
  const records = JSON.parse(fs.readFileSync(path.join(root, indexName), 'utf8'));
  const record = records.find(item => item.ref === '/cn/docs/quickstart/toolchain/hugegraph-hubble/');
  expect(record).toBeTruthy();
  const query = '图形化界面';
  expect(record.keywords).toContain(query);
  for (const value of [record.title, record.headings, record.description, record.body]) {
    expect(JSON.stringify(value || '')).not.toContain(query);
  }
  expect(record.description.length).toBeGreaterThan(10);
  await page.goto('/cn/docs/');
  await page.locator('[data-td-shell-search-open]').first().click();
  await page.locator('.td-shell-search__input').fill(query);
  const result = page.locator('#td-shell-search-results [role="option"]').filter({ hasText: record.title });
  await expect(result).toBeVisible();
  await expect(result.locator('.td-shell-search__item-excerpt')).toHaveText(record.description);
  await result.click();
  await expect(page).toHaveURL(url => url.pathname === record.ref);
});

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

// User-selected enhancements run on maintained content, not the decision gallery.
for (const language of ['en', 'cn']) {
  const prefix = language === 'cn' ? '/cn' : '';
  const serverPath = `${prefix}/docs/quickstart/hugegraph/hugegraph-server/`;
  const tableValues = [[0.629, 5.711, 5.243, 67.033], [10.15, 108.569, 150.266, 1217.944], [3.884, 18.938, 24.89, 281.537]];

  test(`${language} selected wash loads the article image without hiding its heading`, async ({ page }) => {
    await page.goto(`${prefix}/blog/2025/10/09/toplingdb-quick-start/`);
    const header = page.locator('.td-article-header--wash');
    await expect(header.locator('h1')).toBeVisible();
    const image = header.locator('.td-featured-wash img');
    await expect.poll(() => image.evaluate(node => node.complete && node.naturalWidth > 0)).toBe(true);
    await expect(image).toHaveAttribute('alt', '');
    await expect(page.locator('.td-byline')).toHaveCount(0);
  });

  test(`${language} historical chart toggles a legend series and preserves all original measurements`, async ({ page }) => {
    await page.goto(`${prefix}/docs/performance/hugegraph-benchmark-0.5.6/`);
    const target = page.locator('[data-td-echarts-canvas]');
    await target.scrollIntoViewIfNeeded();
    await expect(target.locator('canvas')).toBeVisible();
    const option = await target.evaluate(node => window.echarts.getInstanceByDom(node).getOption());
    expect(option.yAxis[0].type).toBe('log');
    expect(option.series.map(series => series.data)).toEqual(tableValues);
    const table = page.locator('.td-content table').filter({ hasText: '0.629' });
    const rows = table.locator('tbody tr');
    await expect(rows).toHaveCount(3);
    for (let index = 0; index < tableValues.length; index++) {
      const cells = await rows.nth(index).locator('td').allTextContents();
      expect(cells.slice(1).map(value => Number(value.trim()))).toEqual(tableValues[index]);
    }
    // ECharts paints its legend on canvas: click the actual legend hit target,
    // then observe the public instance instead of dispatching an action directly.
    const rectangle = await target.boundingBox();
    const legendPoint = await target.evaluate(node => {
      const chart = window.echarts.getInstanceByDom(node);
      const label = chart.getZr().storage.getDisplayList().find(element => element.type === 'tspan' && element.style.text === 'Titan');
      if (!label) throw new Error('Titan legend label must be painted');
      const bounds = label.getBoundingRect();
      const x = bounds.x + bounds.width / 2;
      const y = bounds.y + bounds.height / 2;
      const matrix = label.getComputedTransform();
      return matrix ? { x: matrix[0] * x + matrix[2] * y + matrix[4], y: matrix[1] * x + matrix[3] * y + matrix[5] } : { x, y };
    });
    await page.mouse.click(rectangle.x + legendPoint.x, rectangle.y + legendPoint.y);
    await expect.poll(() => target.evaluate(node => {
      const selected = window.echarts.getInstanceByDom(node).getOption().legend[0].selected;
      return Object.values(selected).some(value => value === false);
    })).toBe(true);
    await expect(table).toContainText('1217.944');
  });

  test(`${language} Hubble gallery images load, open at full size and restore focus on Escape`, async ({ page }) => {
    await page.goto(`${prefix}/docs/quickstart/toolchain/hugegraph-hubble/`);
    const gallery = page.locator('.td-gallery');
    await expect(gallery.locator('img')).toHaveCount(3);
    const image = gallery.locator('img').nth(1);
    await image.scrollIntoViewIfNeeded();
    await expect.poll(() => image.evaluate(node => node.complete && node.naturalWidth > 0)).toBe(true);
    const opener = image.locator('..');
    await image.click();
    const zoom = page.locator('[data-td-image-zoom-dialog]');
    await expect(zoom).toBeVisible();
    await expect.poll(() => zoom.locator('img').evaluate(node => node.complete && node.naturalWidth > 0)).toBe(true);
    await page.keyboard.press('Escape');
    await expect(zoom).toBeHidden();
    // Escape returns focus to the native button wrapped around this image.
    await expect(opener).toBeFocused();
  });

  test(`${language} Server map folds nodes while steps and outdated status retain real context`, async ({ page }) => {
    await page.goto(serverPath);
    const map = page.locator('div.markmap');
    await expect(map.locator('svg')).toBeVisible();
    const nodes = map.locator('.markmap-node');
    await expect.poll(() => nodes.count()).toBeGreaterThan(3);
    const branch = nodes.filter({ hasText: /^server$/ }).locator('circle');
    const before = await nodes.count();
    await branch.click();
    await expect.poll(() => nodes.count()).toBeLessThan(before);
    await branch.click();
    await expect.poll(() => nodes.count()).toBe(before);
    const steps = page.locator('.td-content ol.steps > li');
    await expect(steps).toHaveCount(5);
    await expect(steps.nth(1).locator('a')).toHaveAttribute('href', /#33-/);
    await expect(steps.nth(1)).toContainText('master');
    await expect(steps.nth(1)).not.toContainText(language === 'cn' ? '发布包' : 'release archive');
    const outdated = page.locator('details').filter({ hasText: language === 'cn' ? '过时的 tools' : 'Outdated tools' }).filter({ has: page.locator('.td-badge') });
    await outdated.locator(':scope > summary').click();
    await expect(outdated.locator('.td-badge')).toBeVisible();
    await expect(outdated).toContainText(language === 'cn' ? '一键' : 'one-click');
    await expect(page.locator('.td-content .td-callout').first()).toBeVisible();
  });

  for (const preset of ['slate', 'paper']) {
    for (const colorTheme of ['light', 'dark']) {
      for (const width of [320, 390]) {
        test(`${language} ${preset} Server map remains readable after fitting to ${width}px in ${colorTheme} mode`, async ({ page }) => {
          await page.setViewportSize({ width, height: 844 });
          await page.addInitScript(({ preset, colorTheme }) => {
            localStorage.setItem('td-preset', preset);
            localStorage.setItem('td-color-theme', colorTheme);
          }, { preset, colorTheme });
          await page.goto(serverPath);
          await expect(page.locator('html')).toHaveAttribute('data-bs-theme', colorTheme);
          const map = page.locator('div.markmap');
          await map.scrollIntoViewIfNeeded();
          await expect(map.locator('.markmap-node')).toHaveCount(7);
          // Markmap scales the SVG group, so computed font-size alone can report
          // 16px while the labels actually render at only 4px on a narrow screen.
          await expect.poll(() => map.locator('foreignObject').evaluateAll(nodes => {
            const labels = nodes.map(node => {
              const text = node.querySelector('div');
              const transform = node.getScreenCTM();
              const { left, right } = node.getBoundingClientRect();
              return { left, right,
                font: parseFloat(getComputedStyle(text).fontSize) * Math.hypot(transform.a, transform.b) };
            });
            return labels.every(label => label.font >= 12 && label.left >= 0 && label.right <= innerWidth);
          })).toBe(true);
          const colors = await map.locator('.markmap-foreign div').first().evaluate(node => {
            const rgb = color => color.match(/[\d.]+/g).slice(0, 3).map(Number);
            let ancestor = node;
            while (ancestor && !/^rgb\(/.test(getComputedStyle(ancestor).backgroundColor)) ancestor = ancestor.parentElement;
            const foreground = getComputedStyle(node).color;
            const background = getComputedStyle(ancestor || document.body).backgroundColor;
            const luminance = color => rgb(color).map(value => {
              const channel = value / 255;
              return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
            }).reduce((sum, channel, i) => sum + channel * [0.2126, 0.7152, 0.0722][i], 0);
            const light = luminance(foreground), dark = luminance(background);
            return { foreground, bodyText: getComputedStyle(document.body).color, background,
              contrast: (Math.max(light, dark) + 0.05) / (Math.min(light, dark) + 0.05) };
          });
          expect(colors.foreground).toBe(colors.bodyText);
          expect(colors.contrast).toBeGreaterThanOrEqual(4.5);
        });
      }
    }
  }

  test(`${language} aggregated Print preserves the destination of relative article links`, async ({ page }) => {
    await page.goto(`${prefix}/docs/clients/restful-api/gremlin/`);
    const taskLink = page.locator('.td-content a').filter({ hasText: language === 'cn' ? '异步任务' : 'asynchronous task REST API' }).first();
    await expect(taskLink).toBeVisible();
    const label = await taskLink.textContent();
    const destination = new URL(await taskLink.getAttribute('href'), page.url()).pathname;
    await page.goto(`${prefix}/_print/docs/`);
    const printedLink = page.locator('a').filter({ hasText: label }).filter({ hasNot: page.locator('.td-heading-self-link') });
    expect(await printedLink.count()).toBeGreaterThan(0);
    expect(await printedLink.evaluateAll((links, destination) => links.some(link => new URL(link.href).pathname === destination), destination)).toBe(true);
  });

  test(`${language} native Markmap keeps dark ink when printing from dark mode`, async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('td-color-theme', 'dark'));
    await page.goto(serverPath);
    const labels = page.locator('div.markmap .markmap-foreign div');
    await expect(labels.first()).toBeVisible();
    await page.emulateMedia({ media: 'print' });
    const printColors = await labels.first().evaluate(node => ({
      text: getComputedStyle(node).color,
      background: getComputedStyle(document.body).backgroundColor
    }));
    expect(printColors.text).toBe('rgb(51, 51, 51)');
    expect(printColors.background).toBe('rgb(255, 255, 255)');
    await page.goto(`${prefix}/_print/docs/`);
    await expect(page.locator('body')).toContainText('hugegraph-core');
    await expect(page.locator('body')).toContainText('values-single.yaml');
    await expect(page.locator('body')).toContainText('HG_PD_AUTH_SECRET_KEY');
  });

  test(`${language} long Server script initially shows nine source lines and copies its complete hidden tail`, async ({ page, context }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    await page.goto(serverPath);
    const code = page.locator('[data-td-code][data-td-collapse-lines="9"]').filter({ hasText: 'set-hubble-pd-password.sh' });
    await code.scrollIntoViewIfNeeded();
    await expect(code).toHaveAttribute('data-td-collapse-lines', '9');
    await expect(code).toHaveClass(/td-is-collapsed/);
    const lines = code.locator('code .line');
    await expect(lines).toHaveCount(15);
    const viewport = code.locator('[data-td-code-viewport]');
    const collapsed = await viewport.boundingBox();
    const ninth = await lines.nth(8).boundingBox();
    const tenth = await lines.nth(9).boundingBox();
    expect(ninth.y + ninth.height).toBeLessThanOrEqual(collapsed.y + collapsed.height + 1);
    expect(tenth.y + tenth.height).toBeGreaterThan(collapsed.y + collapsed.height + 2);
    await code.locator('[data-td-code-copy]').first().click();
    await expect.poll(() => page.evaluate(() => navigator.clipboard.readText())).toContain('./set-hubble-pd-password.sh hstore-ha');
    const copied = await page.evaluate(() => navigator.clipboard.readText());
    expect(copied.trim().split('\n')).toHaveLength(15);
    expect(copied.trim().endsWith(')')).toBe(true);
    await code.locator('[data-td-code-expand]').click();
    await expect(code).toHaveClass(/is-expanded/);
    await expect.poll(async () => (await viewport.boundingBox()).height).toBeGreaterThan(collapsed.height);
    await code.locator('[data-td-code-expand]').click();
    await expect(code).toHaveClass(/td-is-collapsed/);
    const short = page.locator('[data-td-code]').filter({ hasText: 'docker build -f hugegraph-pd/Dockerfile' });
    await expect(short).not.toHaveAttribute('data-td-collapse-lines');
    await expect(short.locator('[data-td-code-expand]')).toBeHidden();
  });

  test(`${language} REST Jaccard equation has readable MathML and survives Markdown and Print`, async ({ page, request }) => {
    const route = `${prefix}/docs/clients/restful-api/traverser/`;
    await page.goto(route);
    const math = page.locator('.td-content .katex-display');
    await expect(math).toBeVisible();
    await expect(math.locator('math')).toHaveCount(1);
    await expect(math.locator('annotation')).toContainText('J');
    const markdown = await request.get(`${route}index.md`);
    expect(markdown.ok()).toBe(true);
    expect(await markdown.text()).toContain('N(u)');
    await page.goto(`${prefix}/_print/docs/`);
    await expect(page.locator('.katex-display').filter({ hasText: 'J' }).first()).toBeVisible();
    await expect(page.locator('body')).toContainText('Jaccard');
  });

  test(`${language} local terminal recording plays the actual Hugo and OINK verification output`, async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    const playbackRequests = [];
    page.on('request', request => {
      if (new URL(request.url()).pathname === '/casts/oink-upgrade-check.cast') playbackRequests.push(request.url());
    });
    await page.goto(`${prefix}/community/documentation/`);
    const player = page.locator('[data-td-asciinema]');
    const optionalDemo = page.locator('details').filter({ has: player });
    await expect(optionalDemo).not.toHaveAttribute('open', '');
    await expect(page.locator('[data-td-code]').filter({ hasText: 'hugo mod graph' })).toBeVisible();
    expect(playbackRequests).toHaveLength(0);
    await optionalDemo.locator(':scope > summary').click();
    await player.scrollIntoViewIfNeeded();
    await expect(player.locator('.ap-overlay-start .ap-play-button')).toBeVisible();
    await player.locator('.ap-overlay-start .ap-play-button').click();
    await expect(player).toContainText('hugo v0.165.0', { timeout: 15000 });
    await expect(player).toContainText('github.com/pgsty/oink@v1.2.0', { timeout: 15000 });
    await expect.poll(() => player.locator('.ap-term-text .ap-line span').first()
      .evaluate(node => node.getBoundingClientRect().height)).toBeGreaterThanOrEqual(11);
  });

  test(`${language} selected components fit a narrow screen and retain native output fallbacks`, async ({ page, request }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    for (const route of [serverPath, `${prefix}/docs/quickstart/toolchain/hugegraph-hubble/`,
      `${prefix}/docs/performance/hugegraph-benchmark-0.5.6/`, `${prefix}/community/documentation/`]) {
      await page.goto(route);
      await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    }
    const markdown = await request.get(`${serverPath}index.md`);
    expect(markdown.ok()).toBe(true);
    const text = await markdown.text();
    expect(text).toContain('hugegraph-core');
    expect(text).toContain('./set-hubble-pd-password.sh hstore-ha');
    const hubble = await request.get(`${prefix}/docs/quickstart/toolchain/hugegraph-hubble/index.md`);
    expect(await hubble.text()).toContain('/docs/images/hubble/schema.jpg');
    const chart = await request.get(`${prefix}/docs/performance/hugegraph-benchmark-0.5.6/index.md`);
    expect(await chart.text()).toContain('1217.944');
  });
}
