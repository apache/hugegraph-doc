const { test, expect } = require('./artifact-test');

test.use({ hasTouch: true });

async function measureComments(tree) {
  return tree.locator('.td-filetree__comment-text').evaluateAll(nodes => nodes.map(node => {
    const row = node.closest('.td-filetree__row').getBoundingClientRect();
    const range = document.createRange();
    range.selectNodeContents(node);
    const rectangles = Array.from(range.getClientRects());
    const clips = [];
    const tree = node.closest('.td-filetree');
    // Only component clipping truncates these comments. Document scrolling
    // keeps below-fold rows readable and must not count as content clipping.
    for (let ancestor = node; ancestor; ancestor = ancestor.parentElement) {
      const style = getComputedStyle(ancestor);
      const box = ancestor.getBoundingClientRect();
      const left = box.left + ancestor.clientLeft;
      const top = box.top + ancestor.clientTop;
      clips.push({ left, top, right: left + ancestor.clientWidth, bottom: top + ancestor.clientHeight,
        x: /^(hidden|clip|auto|scroll)$/.test(style.overflowX),
        y: /^(hidden|clip|auto|scroll)$/.test(style.overflowY) });
      if (ancestor === tree) break;
    }
    return {
      text: node.textContent,
      // CJK closing punctuation may hang outside a visible-overflow inline
      // box. It is clipped only when it crosses an actual clipping ancestor.
      clipped: rectangles.some(rectangle => clips.some(clip =>
        (clip.x && (rectangle.left < clip.left - 1 || rectangle.right > clip.right + 1)) ||
        (clip.y && (rectangle.top < clip.top - 1 || rectangle.bottom > clip.bottom + 1)))),
      allLinesVisible: rectangles.every(rectangle => rectangle.left >= row.left - 1 &&
        rectangle.right <= row.right + 1 && rectangle.top >= row.top - 1 && rectangle.bottom <= row.bottom + 1)
    };
  }));
}

async function expectCompleteComments(tree, count) {
  await expect(tree.locator('.td-filetree__comment-text')).toHaveCount(count);
  for (const measurement of await measureComments(tree)) {
    expect(measurement.clipped, measurement.text).toBe(false);
    expect(measurement.allLinesVisible, measurement.text).toBe(true);
  }
}

test('file tree readability measurement detects compact nowrap and hidden comments', async ({ page }) => {
  await page.goto('/docs/config/config-backend-rocksdb/');
  const tree = page.locator('.td-filetree');
  await tree.scrollIntoViewIfNeeded();
  await expectCompleteComments(tree, 3);
  await tree.locator('.td-filetree__comment-text').first().evaluate(node => {
    Object.assign(node.style, { maxWidth: '4ch', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' });
  });
  expect((await measureComments(tree))[0].clipped).toBe(true);
});

for (const language of ['en', 'cn']) {
  for (const preset of ['slate', 'paper']) {
    for (const theme of ['light', 'dark']) {
      for (const width of [1440, 768, 390]) {
        test(`${language} ${preset} ${theme} complete file tree comments remain readable at ${width}px without hovering`, async ({ page }) => {
          await page.setViewportSize({ width, height: 1000 });
          await page.addInitScript(({ preset, theme }) => {
            localStorage.setItem('td-preset', preset);
            localStorage.setItem('td-color-theme', theme);
          }, { preset, theme });
          const prefix = language === 'cn' ? '/cn' : '';
          for (const [route, count] of [['config/config-backend-rocksdb', 3], ['quickstart/hugegraph/hugegraph-helm', 14]]) {
            await page.goto(`${prefix}/docs/${route}/`);
            const tree = page.locator('.td-filetree');
            await expect(tree).toHaveClass(/td-filetree--wrap/);
            await tree.scrollIntoViewIfNeeded();
            await expectCompleteComments(tree, count);
            if (count === 3) {
              for (const store of ['schema store', 'graph store', 'system store']) await expect(tree).toContainText(store);
            } else {
              await expect(tree).toContainText(language === 'cn' ? '1 副本且关闭反亲和与 PDB' : '1 replica and no anti-affinity');
            }
            if (width >= 576) {
              const divider = tree.getByRole('separator');
              await divider.focus();
              for (const key of ['Home', 'End']) {
                await divider.press(key);
                await expectCompleteComments(tree, count);
              }
            }
            const folder = tree.locator('details').first();
            await folder.locator(':scope > summary').press('Enter');
            await expect(tree.locator('.td-filetree__comment-text').first()).toBeHidden();
            await folder.locator(':scope > summary').press('Enter');
            await expectCompleteComments(tree, count);
            expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
            if (width === 1440) {
              await page.emulateMedia({ media: 'print' });
              await expectCompleteComments(tree, count);
              await page.emulateMedia({ media: 'screen' });
            }
          }
        });
      }
    }
  }
}
