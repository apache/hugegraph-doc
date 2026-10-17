const { test, expect } = require('./artifact-test');

async function expectConfigurationCatalog(page, route, wideCount, ordinaryCount, environmentKeys = false) {
  await page.goto(route);
  // Optional/deprecated catalogues still need readable identifiers
  // when readers explicitly expand them. Open through their UI.
  for (const details of await page.locator('.td-content details').all()) {
    if (!await details.evaluate(node => node.open)) await details.locator(':scope > summary').click();
  }
  await page.evaluate(() => document.fonts.ready);
  const tables = page.locator('.td-content table.td-table--wide');
  await expect(tables).toHaveCount(wideCount);
  await expect(page.locator('.td-content table:not(.td-table--wide)')).toHaveCount(ordinaryCount);
  for (const table of await tables.all()) {
    const wrapper = table.locator('..');
    await wrapper.scrollIntoViewIfNeeded();
    // AI provider matrices put environment keys in several columns; their
    // Purpose labels are prose and are allowed to wrap normally.
    const identifiers = environmentKeys
      ? table.locator('tbody td code').filter({ hasText: /^[A-Z][A-Z0-9_]*(?:=[^\s]+)?$/ })
      : table.locator('tbody tr > td:first-child');
    expect(await identifiers.count()).toBeGreaterThan(0);
    const cells = await identifiers.evaluateAll(nodes => nodes.map(node => {
      const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
      const tops = [];
      let text;
      while ((text = walker.nextNode())) {
        if (!text.textContent.trim()) continue;
        const range = document.createRange();
        range.selectNodeContents(text);
        for (const rectangle of range.getClientRects()) {
          if (!tops.some(top => Math.abs(top - rectangle.top) < 1)) tops.push(rectangle.top);
        }
      }
      return { text: node.textContent.trim(), lines: tops.length,
        font: parseFloat(getComputedStyle(node).fontSize),
        rowHeight: node.closest('tr').getBoundingClientRect().height };
    }));
    for (const cell of cells) {
      expect(cell.lines, `${route}: ${cell.text}`).toBe(1);
      expect(cell.font, `${route}: ${cell.text}`).toBeGreaterThanOrEqual(14);
      if (['gremlin.graph', 'hstore.partition_count', 'hbase.kerberos_enable'].includes(cell.text)) {
        expect(cell.rowHeight, `${route}: ${cell.text}`).toBeLessThan(100);
      } else if (cell.text === 'auth.audit_log_rate') {
        // Its full explanation is about 200 characters, so several
        // normal prose lines are expected; an 800px token column is not.
        expect(cell.rowHeight).toBeLessThan(200);
      }
    }
    const description = table.locator('tbody tr > td:nth-child(3)').first();
    await expect(description).not.toBeEmpty();
    expect(await description.evaluate(node => parseFloat(getComputedStyle(node).fontSize))).toBeGreaterThanOrEqual(14);
    if (await wrapper.evaluate(node => node.scrollWidth > node.clientWidth + 1)) {
      await expect(wrapper).toHaveAttribute('tabindex', '0');
      await wrapper.focus();
      await wrapper.press('ArrowRight');
      await expect.poll(() => wrapper.evaluate(node => node.scrollLeft)).toBeGreaterThan(0);
    }
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
}

for (const language of ['en', 'cn']) {
  for (const preset of ['slate', 'paper']) {
    for (const theme of ['light', 'dark']) {
      for (const width of [1440, 768, 390]) {
        test(`${language} ${preset} ${theme} PD environment descriptions stay readable and scrollable at ${width}px`, async ({ page }) => {
          await page.setViewportSize({ width, height: 1000 });
          await page.addInitScript(({ preset, theme }) => {
            localStorage.setItem('td-preset', preset);
            localStorage.setItem('td-color-theme', theme);
          }, { preset, theme });
          const prefix = language === 'cn' ? '/cn' : '';
          await page.goto(`${prefix}/docs/quickstart/hugegraph/hugegraph-pd/`);
          const table = page.locator('table.td-table--wide').filter({ hasText: 'HG_PD_AUTH_SECRET_KEY' });
          const wrapper = table.locator('..');
          await wrapper.scrollIntoViewIfNeeded();

          const assertReadable = async () => {
            const measurements = await table.evaluate(node => {
              const description = node.querySelector('tbody td:last-child');
              return {
                descriptionWidth: description.getBoundingClientRect().width,
                descriptionFont: parseFloat(getComputedStyle(description).fontSize),
                firstRowHeight: node.querySelector('tbody tr').getBoundingClientRect().height,
                viewport: node.parentElement.clientWidth,
                scrollWidth: node.parentElement.scrollWidth
              };
            });
            // Fixed technical identifiers must not squeeze prose into a few
            // characters per line, or require reducing the prose font size.
            expect(measurements.descriptionWidth).toBeGreaterThanOrEqual(288);
            expect(measurements.descriptionFont).toBeGreaterThanOrEqual(14);
            expect(measurements.firstRowHeight).toBeLessThan(100);
            expect(measurements.scrollWidth).toBeGreaterThan(measurements.viewport);
            await expect(wrapper).toHaveAttribute('tabindex', '0');
            await wrapper.focus();
            await wrapper.press('ArrowRight');
            await expect.poll(() => wrapper.evaluate(node => node.scrollLeft)).toBeGreaterThan(0);
            expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
            return measurements;
          };
          const expanded = await assertReadable();
          if (width === 1440) {
            const toggle = page.locator('[data-td-shell-right-toggle]').first();
            await toggle.click();
            await expect.poll(() => wrapper.evaluate(node => node.clientWidth)).toBeGreaterThan(expanded.viewport);
            await assertReadable();
          }
          await expect(table).toContainText('management.endpoints.web.exposure.include');
          await expect(table).toContainText('HG_PD_AUTH_SECRET_KEY');
        });
      }
    }
  }
}

// Removing a global table override must preserve other authored configuration
// references too. Only their technical tables opt into OINK's wide layout.
for (const language of ['en', 'cn']) {
  for (const preset of ['slate', 'paper']) {
    for (const theme of ['light', 'dark']) {
      for (const width of [1440, 390]) {
        test(`${language} ${preset} ${theme} configuration identifiers remain intact at ${width}px`, async ({ page }) => {
          await page.setViewportSize({ width, height: 1000 });
          await page.addInitScript(({ preset, theme }) => {
            localStorage.setItem('td-preset', preset);
            localStorage.setItem('td-color-theme', theme);
          }, { preset, theme });
          const prefix = language === 'cn' ? '/cn' : '';
          for (const [route, wideCount, ordinaryCount] of [
            ['config-backend-hbase', 4, 2], ['config-backend-hstore', 2, 3], ['config-option', 16, 0]
          ]) {
            await expectConfigurationCatalog(page, `${prefix}/docs/config/${route}/`, wideCount, ordinaryCount);
          }
        });
        test(`${language} ${preset} ${theme} Computer configuration identifiers remain intact at ${width}px`, async ({ page }) => {
          await page.setViewportSize({ width, height: 1000 });
          await page.addInitScript(({ preset, theme }) => {
            localStorage.setItem('td-preset', preset);
            localStorage.setItem('td-color-theme', theme);
          }, { preset, theme });
          const prefix = language === 'cn' ? '/cn' : '';
          await expectConfigurationCatalog(page, `${prefix}/docs/quickstart/computing/hugegraph-computer-config/`, 35, 0);
        });
      }
    }
  }
}


for (const language of ['en', 'cn']) {
  for (const width of [1440, 390]) {
    for (const [route, wideCount, ordinaryCount, environmentKeys] of [
      ['hugegraph/hugegraph-hstore', 9, 2, false],
      ['hugegraph/hugegraph-pd', 8, 3, false],
      ['hugegraph-ai/config-reference', 3, 5, true]
    ]) {
      test(`${language} ${route} technical references keep identifiers intact at ${width}px`, async ({ page }) => {
        await page.setViewportSize({ width, height: 1000 });
        await page.addInitScript(() => {
          localStorage.setItem('td-preset', 'slate');
          localStorage.setItem('td-color-theme', 'light');
        });
        const prefix = language === 'cn' ? '/cn' : '';
        await expectConfigurationCatalog(page, `${prefix}/docs/quickstart/${route}/`, wideCount, ordinaryCount, environmentKeys);
      });
    }
  }
}
