const { test, expect } = require('./artifact-test');

const releaseURL = 'https://github.com/apache/hugegraph/releases/tag/1.7.0';
const releaseLinks = [
  releaseURL,
  'https://github.com/apache/hugegraph/archive/refs/tags/1.7.0.tar.gz',
  'https://github.com/apache/hugegraph/archive/refs/tags/1.7.0.zip',
  'https://github.com/apache/hugegraph'
];

for (const language of ['en', 'cn']) {
  const prefix = language === 'cn' ? '/cn' : '';
  const releaseRoute = `${prefix}/docs/changelog/hugegraph-1.7.0-release-notes/`;
  const configurationRoute = `${prefix}/docs/config/config-option/`;

  test(`${language} native release card derives real release links and date in HTML and Markdown`, async ({ page, request }) => {
    await page.goto(releaseRoute);
    const card = page.locator('.td-release-card');
    await expect(card).toHaveCount(1);
    await expect(card.locator('.td-release-card__tag')).toHaveText('1.7.0');
    await expect(card.locator('time')).toHaveAttribute('datetime', '2025-11-16');
    await expect(card.locator('time')).toHaveText('2025-11-16');
    expect(await card.locator('a').evaluateAll(links => links.map(link => link.getAttribute('href')))).toEqual(releaseLinks);

    const markdown = await request.get(`${releaseRoute}index.md`);
    expect(markdown.ok()).toBe(true);
    const text = await markdown.text();
    // Escape punctuation in the tag while preserving its literal Markdown text.
    expect(text).toContain(String.raw`**1\.7\.0 · 2025-11-16**`);
    for (const url of releaseLinks) expect(text).toContain(`](${url})`);
    expect(text).not.toContain('{{< release-card');
  });

  for (const width of [1440, 390]) {
    test(`${language} native configuration table reader preserves data, keyboard focus and Print at ${width}px`, async ({ page, request }) => {
      await page.setViewportSize({ width, height: 1000 });
      await page.goto(configurationRoute);
      const frame = page.locator('[data-td-table-expand]').filter({ hasText: 'restserver.connection_max_requests' });
      const button = frame.locator('.td-table-expand');
      const dialog = page.locator('[data-td-table-reader]');
      const table = page.locator('table.expand').filter({ hasText: 'restserver.connection_max_requests' });
      await expect(frame).toHaveCount(1);
      await expect(button).toBeVisible();
      await expect(table).toHaveClass(/td-table--wide/);
      const rows = await table.locator('tbody tr').count();
      expect(rows).toBeGreaterThan(20);
      await button.scrollIntoViewIfNeeded();
      await button.focus();
      const scrollY = await page.evaluate(() => window.scrollY);
      await button.press('Enter');
      await expect(dialog).toBeVisible();
      await expect(dialog.locator('table')).toHaveCount(1);
      await expect(frame.locator('table')).toHaveCount(0);
      await expect(dialog.locator('tbody tr')).toHaveCount(rows);
      await expect(dialog).toContainText('restserver.connection_max_requests');
      await expect(dialog.locator('#td-table-reader-title')).toBeFocused();
      await page.keyboard.press('Shift+Tab');
      expect(await dialog.evaluate(node => node.contains(document.activeElement))).toBe(true);
      await page.keyboard.press('Escape');
      await expect(dialog).toBeHidden();
      await expect(button).toBeFocused();
      await expect(frame.locator('tbody tr')).toHaveCount(rows);
      expect(Math.abs(await page.evaluate(() => window.scrollY) - scrollY)).toBeLessThanOrEqual(1);

      await button.press('Enter');
      await expect(dialog).toBeVisible();
      await page.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
      await expect(dialog).toBeHidden();
      await expect(frame.locator('tbody tr')).toHaveCount(rows);
      await page.emulateMedia({ media: 'print' });
      await expect(button).toBeHidden();
      await expect(table).toBeVisible();
      await expect(table).toContainText('restserver.connection_max_requests');
      await page.emulateMedia({ media: 'screen' });
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);

      const markdown = await request.get(`${configurationRoute}index.md`);
      expect(markdown.ok()).toBe(true);
      const text = await markdown.text();
      expect(text).toContain('restserver.connection_max_requests');
      expect(text).toContain('server.start_ignore_single_graph_error');
      expect(text).not.toContain('data-td-table-reader');
    });
  }

  test(`${language} native Mermaid reader keeps zoom, exact source copy, SVG export and keyboard return usable`, async ({ page, context, request }) => {
    test.setTimeout(45_000);
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    const route = `${prefix}/docs/quickstart/hugegraph/hugegraph-server/`;
    await page.goto(route);
    const diagram = page.locator('.td-diagram--mermaid').filter({ hasText: 'bin/start-hugegraph.sh -p true' });
    await expect(diagram).toHaveCount(1);
    await diagram.scrollIntoViewIfNeeded();
    await expect(diagram).toHaveAttribute('data-td-diagram-state', 'rendered', { timeout: 20_000 });
    const source = await diagram.locator('.td-mermaid-source code').textContent();
    expect(source).toContain('flowchart TD');
    expect(source).toContain('bin/init-store.sh');
    const expand = diagram.locator('[data-td-diagram-expand]');
    await expand.focus();
    await expand.press('Enter');

    const dialog = page.locator('[data-td-diagram-zoom-dialog]');
    const viewport = dialog.locator('[data-td-diagram-zoom-viewport]');
    const canvas = dialog.locator('[data-td-diagram-zoom-canvas]');
    const zoomIn = dialog.locator('[data-td-diagram-zoom-in]');
    const sourceToggle = dialog.locator('[data-td-diagram-source-toggle]');
    const sourcePane = dialog.locator('[data-td-diagram-zoom-source]');
    await expect(dialog).toBeVisible();
    await expect(dialog.locator('[data-td-diagram-zoom-close]')).toBeFocused();
    await expect(canvas.locator('img')).toBeVisible();
    await expect(zoomIn).toBeEnabled();
    const beforeZoom = await canvas.evaluate(node => node.style.transform);
    await zoomIn.click();
    await expect.poll(() => canvas.evaluate(node => node.style.transform)).not.toBe(beforeZoom);
    const beforePan = await canvas.evaluate(node => node.style.transform);
    await viewport.focus();
    await viewport.press('ArrowRight');
    await expect.poll(() => canvas.evaluate(node => node.style.transform)).not.toBe(beforePan);

    await sourceToggle.click();
    await expect(sourceToggle).toHaveAttribute('aria-pressed', 'true');
    await expect(sourcePane).toBeVisible();
    expect(await sourcePane.locator('code').textContent()).toBe(source);
    await expect(zoomIn).toBeDisabled();
    await dialog.locator('[data-td-diagram-copy]').click();
    await expect.poll(() => page.evaluate(() => navigator.clipboard.readText())).toBe(source);
    await sourceToggle.click();
    await expect(sourceToggle).toHaveAttribute('aria-pressed', 'false');
    await expect(canvas.locator('img')).toBeVisible();
    await expect(zoomIn).toBeEnabled();

    const downloadPromise = page.waitForEvent('download');
    await dialog.locator('[data-td-diagram-download]').click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toBe('mermaid-1.svg');
    const stream = await download.createReadStream();
    expect(stream).not.toBeNull();
    const chunks = [];
    for await (const chunk of stream) chunks.push(chunk);
    const svg = Buffer.concat(chunks).toString('utf8');
    expect(svg).toContain('<svg');
    expect(svg).toContain('xmlns="http://www.w3.org/2000/svg"');
    expect(svg).toContain('HugeGraph 1.7.0');
    expect(svg).toContain('bin/start-hugegraph.sh -p true');
    await page.keyboard.press('Escape');
    await expect(dialog).toBeHidden();
    await expect(expand).toBeFocused();

    const markdown = await request.get(`${route}index.md`);
    expect(markdown.ok()).toBe(true);
    const text = await markdown.text();
    expect(text).toContain('flowchart TD');
    expect(text).toContain('bin/init-store.sh');
    expect(text).not.toContain('data-td-diagram');
  });

  test(`${language} aggregate Print keeps release links and the complete expanded table without modal controls`, async ({ page }) => {
    await page.goto(`${prefix}/_print/docs/`);
    const card = page.locator('.td-release-card-static').filter({ hasText: '1.7.0' });
    await expect(card).toHaveCount(1);
    await expect(card.locator('time')).toHaveAttribute('datetime', '2025-11-16');
    expect(await card.locator('a').evaluateAll(links => links.map(link => link.getAttribute('href')))).toEqual(releaseLinks);
    await expect(page.locator('table').filter({ hasText: 'restserver.connection_max_requests' })).toHaveCount(1);
    await expect(page.locator('[data-td-table-reader]')).toHaveCount(0);
    await expect(page.locator('.td-table-expand')).toHaveCount(0);
    const diagramSource = page.locator('pre.td-mermaid-source code').filter({ hasText: 'bin/start-hugegraph.sh -p true' });
    await expect(diagramSource).toHaveCount(1);
    await expect(diagramSource).toBeVisible();
    await expect(diagramSource).toContainText('flowchart TD');
    await expect(page.locator('[data-td-diagram-zoom-dialog]')).toHaveCount(0);
  });
}
