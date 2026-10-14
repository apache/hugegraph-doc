const { test, expect } = require('./artifact-test');

test.use({ hasTouch: true });

const datasets = ['email-enron (30w)', 'amazon0601 (300w)', 'YouTube (300w)', 'LiveJournal (3000w)'];
const measurements = [
  [0.629, 5.711, 5.243, 67.033],
  [10.15, 108.569, 150.266, 1217.944],
  [3.884, 18.938, 24.89, 281.537]
];

for (const language of ['en', 'cn']) {
  for (const width of [320, 390]) {
    test(`${language} historical chart keeps every tapped tooltip inside a ${width}px viewport`, async ({ page }) => {
      await page.setViewportSize({ width, height: 844 });
      const prefix = language === 'cn' ? '/cn' : '';
      await page.goto(`${prefix}/docs/performance/hugegraph-benchmark-0.5.6/`);
      const chart = page.locator('[data-td-echarts-canvas]');
      await chart.scrollIntoViewIfNeeded();
      await expect(chart.locator('canvas')).toBeVisible();
      await expect.poll(() => chart.evaluate(node => {
        const instance = window.echarts.getInstanceByDom(node);
        return instance && instance.getZr().animation.isFinished();
      })).toBe(true);

      for (let index = 0; index < datasets.length; index++) {
        // Use the public coordinate conversion only to locate the real tap.
        // A dispatched showTip action would bypass touch hit testing.
        const point = await chart.evaluate((node, index) => {
          const instance = window.echarts.getInstanceByDom(node);
          return {
            x: instance.convertToPixel({ xAxisIndex: 0 }, index),
            y: instance.convertToPixel({ yAxisIndex: 0 }, 10)
          };
        }, index);
        const bounds = await chart.boundingBox();
        await page.touchscreen.tap(bounds.x + point.x, bounds.y + point.y);
        const tooltip = chart.locator(':scope > div').filter({ hasText: datasets[index] });
        await expect(tooltip).toBeVisible();
        for (const [seriesIndex, name] of ['HugeGraph', 'Titan', 'Neo4j'].entries()) {
          await expect(tooltip).toContainText(name);
          expect((await tooltip.innerText()).replaceAll(',', '')).toContain(String(measurements[seriesIndex][index]));
        }
        // Wait for tooltip movement animation before checking its true bounds.
        await expect.poll(async () => {
          const rectangle = await tooltip.boundingBox();
          return rectangle && rectangle.x >= 0 && rectangle.x + rectangle.width <= width;
        }).toBe(true);
      }
      await expect(page.locator('.td-content table').filter({ hasText: '0.629' })).toContainText('1217.944');
    });
  }
}
