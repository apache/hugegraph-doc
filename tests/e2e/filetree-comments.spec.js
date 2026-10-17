const { test, expect } = require('./artifact-test');

test.use({ hasTouch: true });

async function expectCompleteDefinitions(tree) {
  const comments = tree.locator('.td-filetree__comment-text');
  await expect(comments).toHaveCount(3);
  const measurements = await comments.evaluateAll(nodes => nodes.map(node => {
    const text = node.getBoundingClientRect();
    const row = node.closest('.td-filetree__row').getBoundingClientRect();
    const range = document.createRange();
    range.selectNodeContents(node);
    const rectangles = Array.from(range.getClientRects());
    return {
      text: node.textContent,
      clipped: node.scrollWidth > node.clientWidth + 1,
      allLinesVisible: rectangles.every(rectangle => rectangle.left >= text.left - 1 &&
        rectangle.right <= text.right + 1 && rectangle.top >= row.top - 1 && rectangle.bottom <= row.bottom + 1)
    };
  }));
  for (const [index, store] of ['schema store', 'graph store', 'system store'].entries()) {
    expect(measurements[index].text).toContain(store);
    // Text presence alone also passes when native nowrap/ellipsis hides its end.
    expect(measurements[index].clipped).toBe(false);
    expect(measurements[index].allLinesVisible).toBe(true);
  }
}

for (const language of ['en', 'cn']) {
  for (const width of [1440, 768, 390]) {
    test(`${language} RocksDB complete definitions remain visually readable at ${width}px without hovering`, async ({ page }) => {
      await page.setViewportSize({ width, height: 1000 });
      const prefix = language === 'cn' ? '/cn' : '';
      await page.goto(`${prefix}/docs/config/config-backend-rocksdb/`);
      const tree = page.locator('.hg-filetree-notes');
      await tree.scrollIntoViewIfNeeded();
      await expectCompleteDefinitions(tree);
      if (width >= 576) {
        const divider = tree.getByRole('separator');
        await divider.focus();
        for (const key of ['Home', 'End']) {
          await divider.press(key);
          await expectCompleteDefinitions(tree);
        }
      }
      const folder = tree.locator('details').filter({
        has: page.locator(':scope > summary .td-filetree__name', { hasText: /^data\/$/ })
      });
      await folder.locator(':scope > summary').press('Enter');
      await expect(tree.locator('.td-filetree__comment-text').first()).toBeHidden();
      await folder.locator(':scope > summary').press('Enter');
      await expectCompleteDefinitions(tree);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    });
  }
}
