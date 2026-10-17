// Licensed to the Apache Software Foundation (ASF) under one or more
// contributor license agreements. See the NOTICE file distributed with
// this work for additional information regarding copyright ownership.
// The ASF licenses this file to You under the Apache License, Version 2.0.

const { test, expect } = require('@playwright/test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const root = process.env.SITE_ROOT;
const validator = path.resolve(__dirname, '../../dist/validate-site-output.py');
function asset(directory, prefix) {
  const folder = path.join(root, 'third_party', directory);
  return path.join(folder, fs.readdirSync(folder).find(name => name.startsWith(prefix) && name.endsWith('.js')));
}
function securityGate(html) {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'oink-runtime-security-'));
  try {
    fs.writeFileSync(path.join(temporary, 'index.html'), html);
    const result = spawnSync('python3', [validator, temporary, 'https://hugegraph-oink.staged.apache.org/', '--security-only'], { encoding: 'utf8' });
    if (result.error) throw result.error;
    return { status: result.status, output: result.stdout + result.stderr };
  } finally { fs.rmSync(temporary, { recursive: true, force: true }); }
}
function chartGate(option) {
  const json = JSON.stringify(option).replaceAll('<', '\\u003c');
  return securityGate(`<article><script type="application/json" data-td-echarts-options>${json}</script></article>`);
}
async function isolate(page) {
  const requests = [];
  await page.route('**/*', async route => {
    if (route.request().isNavigationRequest()) {
      await route.fulfill({ contentType: 'text/html', body: '<div id="chart" style="width:600px;height:400px"></div>' });
    } else {
      requests.push(route.request().url());
      await route.abort(); // Every probe request stays inside this test.
    }
  });
  await page.goto('http://component-security.invalid/');
  return requests;
}
async function hoverBar(page, extra) {
  await page.addScriptTag({ path: asset('echarts', 'echarts.min.') });
  const point = await page.evaluate(extra => {
    window.chart = echarts.init(document.getElementById('chart'));
    chart.setOption({ animation: false, xAxis: { data: ['A'] }, yAxis: {}, tooltip: { trigger: 'item' },
      series: [{ type: 'bar', data: [5] }], ...extra });
    const pixel = chart.convertToPixel({ seriesIndex: 0 }, [0, 2.5]);
    const rect = chart.getDom().getBoundingClientRect();
    return { x: rect.x + pixel[0], y: rect.y + pixel[1] };
  }, extra);
  await page.mouse.move(point.x, point.y);
}

const html = '<img src=/review-missing onerror=window.__reviewProbe=true>';
for (const [name, extra, probe] of [
  ['series tooltip shorthand', { series: [{ type: 'bar', data: [5], tooltip: html }] }, 'event'],
  ['item tooltip shorthand', { series: [{ type: 'bar', data: [{ value: 5, tooltip: html }] }] }, 'event'],
  ['inherited tooltip font', { textStyle: { fontFamily: 'serif;background-image:url(https://outside-review.invalid/font.png)' } }, '/font.png'],
  ['piecewise marker color', { visualMap: { type: 'piecewise', pieces: [{ min: 0, max: 10, color: 'red;background-image:url(https://outside-review.invalid/piece.png)' }] } }, '/piece.png'],
  ['axis border fallback', { tooltip: { trigger: 'axis', defaultBorderColor: 'red;background-image:url(https://outside-review.invalid/border.png)' } }, '/border.png'],
]) {
  test(`${name} is rejected before its native runtime sink`, async ({ page }) => {
    expect(chartGate(extra).status).toBe(1);
    const requests = await isolate(page);
    await hoverBar(page, extra);
    if (probe === 'event') await expect.poll(() => page.evaluate(() => !!window.__reviewProbe)).toBe(true);
    else await expect.poll(() => requests.some(url => url.endsWith(probe))).toBe(true);
  });
}

test('safe shorthand and inherited fonts render with no outside requests', async ({ page }) => {
  const extra = { textStyle: { fontFamily: 'Arial, "Noto Sans CJK SC", sans-serif' },
    series: [{ type: 'bar', data: [5], tooltip: '<b>Safe {b}: {c}</b>' }] };
  expect(chartGate(extra).status).toBe(0);
  const requests = await isolate(page);
  await hoverBar(page, extra);
  await expect(page.locator('b').filter({ hasText: 'Safe A: 5' })).toBeVisible();
  expect(requests).toEqual([]);
});

for (const [name, source, rejected, image] of [
  ['outline', '---\nmarkmap:\n  spacingHorizontal: 40\n---\n# HugeGraph\n- server\n- core', false, false],
  ['image', '# Parent\n- ![image](https://outside-review.invalid/map.png)', true, true],
  ['reference image', '# Parent\n- ![image][ref]\n\n[ref]: https://outside-review.invalid/ref.png', true, true],
  ['allowed-origin image', '# Parent\n- ![image](/img/local.png)', true, true],
  ['inert image example', '# Parent\n- `![image](https://outside-review.invalid/inert.png)`', false, false],
]) {
  test(`Markmap plain-text contract handles ${name} before rendering`, async ({ page }) => {
    const escaped = source.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
    const gate = securityGate(`<pre><code class="language-markmap">${escaped}</code></pre><script src="/third_party/markmap/markmap-autoloader.hash.js"></script>`);
    expect(gate.status, gate.output).toBe(rejected ? 1 : 0);
    const requests = await isolate(page);
    await page.addScriptTag({ path: asset('markmap', 'd3.min.') });
    await page.addScriptTag({ path: asset('markmap', 'markmap-lib.') });
    await page.addScriptTag({ path: asset('markmap', 'markmap-view.') });
    await page.evaluate(source => {
      document.getElementById('chart').innerHTML = '<svg style="width:600px;height:400px"></svg>';
      const transformed = new markmap.Transformer().transform(source);
      markmap.Markmap.create(document.querySelector('svg'), { duration: 0 }, transformed.root);
    }, source);
    if (image) await expect.poll(() => requests.length).toBeGreaterThan(0);
    else {
      await expect(page.locator('foreignObject').first()).toBeVisible();
      expect(requests).toEqual([]);
    }
  });
}
