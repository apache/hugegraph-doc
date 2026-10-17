const { test, expect } = require('./artifact-test');

for (const language of ['en', 'cn']) {
  for (const width of [1440, 768, 390]) {
    test(`${language} PD environment descriptions stay readable and scrollable at ${width}px`, async ({ page }) => {
      await page.setViewportSize({ width, height: 1000 });
      const prefix = language === 'cn' ? '/cn' : '';
      await page.goto(`${prefix}/docs/quickstart/hugegraph/hugegraph-pd/`);
      const table = page.locator('table.hg-pd-env');
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
