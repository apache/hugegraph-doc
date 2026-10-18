const { test, expect } = require('./artifact-test');

// Native opt-ins replace the removed site-wide token rule across current guides,
// including catalogues whose current URL differs from their archived predecessor.
const catalogues = [
  ['clients/restful-api/graphspace', 2, [['internal_algorithm_image_url', 2]]],
  ['quickstart/toolchain/hugegraph-tools', 1, ['HUGEGRAPH_TRUST_STORE_PASSWORD']],
  ['quickstart/toolchain/visualization/hugegraph-hubble-hstore', 2, ['operations.store.allowed_targets', 'Leader/Follower']],
  ['guides/hugegraph-docker-cluster', 4, ['HG_PD_INITIAL_STORE_COUNT', 'HG_STORE_RAFT_ADDRESS',
    'HG_SERVER_REQUIRE_AUTH_TOKEN_SECRET', 'HUGEGRAPH_AUTH_TOKEN_SECRET']],
  ['quickstart/toolchain/import/hugegraph-seatunnel-connector', 1, ['env.sink.flush.interval']],
  ['quickstart/hugegraph-ai/hugegraph-ml', 4, ['convert_graph_with_edge_feat(', 'import_graph_from_dgl_with_edge_feat',
    'hetero_sample_embed_gatne.py', 'correct_and_smooth_example.py']],
  ['quickstart/toolchain/hugegraph-loader', 1, ['--single-insert-threads']]
];

for (const language of ['en', 'cn']) {
  for (const width of [1440, 390]) {
    for (const [route, count, identifiers] of catalogues) {
      test(`${language} technical catalogue ${route} preserves identifiers at ${width}px`, async ({ page }) => {
        await page.setViewportSize({ width, height: 1000 });
        await page.addInitScript(() => {
          localStorage.setItem('td-preset', 'slate');
          localStorage.setItem('td-color-theme', 'light');
        });
        await page.goto(`${language === 'cn' ? '/cn' : ''}/docs/${route}/`);
        await page.evaluate(() => document.fonts.ready);
        const tables = page.locator('.td-content table.td-table--wide');
        await expect(tables).toHaveCount(count);
        for (const entry of identifiers) {
          const [identifier, expectedTables] = Array.isArray(entry) ? entry : [entry, 1];
          // Bind every technical table to its content, so swapping an opt-in
          // with an ordinary table cannot pass through a matching page total.
          const matchingTables = tables.filter({ hasText: identifier });
          await expect(matchingTables, identifier).toHaveCount(expectedTables);
          const cells = matchingTables.locator('tbody td').filter({ hasText: identifier });
          expect(await cells.count(), identifier).toBeGreaterThan(0);
          const measurements = await cells.evaluateAll((nodes, identifier) => nodes.flatMap(node => {
            const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
            const results = [];
            let text;
            while ((text = walker.nextNode())) {
              const start = text.textContent.indexOf(identifier);
              if (start < 0) continue;
              // Signatures may wrap between arguments; the identifier itself
              // must remain intact, with no font reduction to make it fit.
              const range = document.createRange();
              range.setStart(text, start);
              range.setEnd(text, start + identifier.length);
              const tops = new Set(Array.from(range.getClientRects(), rect => Math.round(rect.top)));
              results.push({ lines: tops.size, font: parseFloat(getComputedStyle(text.parentElement).fontSize) });
            }
            return results;
          }), identifier);
          expect(measurements.length, identifier).toBeGreaterThan(0);
          for (const measurement of measurements) {
            expect(measurement.lines, identifier).toBe(1);
            expect(measurement.font, identifier).toBeGreaterThanOrEqual(14);
          }
        }
        for (const table of await tables.all()) {
          const wrapper = table.locator('..');
          await wrapper.scrollIntoViewIfNeeded();
          if (await wrapper.evaluate(node => node.scrollWidth > node.clientWidth + 1)) {
            await expect(wrapper).toHaveAttribute('tabindex', '0');
            await wrapper.focus();
            await wrapper.press('ArrowRight');
            await expect.poll(() => wrapper.evaluate(node => node.scrollLeft)).toBeGreaterThan(0);
          }
        }
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
      });
    }
  }
}
