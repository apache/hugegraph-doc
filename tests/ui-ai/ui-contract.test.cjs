const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const root = path.resolve(__dirname, '../..');
const read = (file) => fs.readFileSync(path.join(root, file), 'utf8');

test('disabled AI emits no widget or adapter markup', () => {
  const config = read('hugo.yaml');
  const hook = read('layouts/_partials/hooks/body-end.html');
  assert.match(config, /ai_search:\n\s+enabled: false/);
  assert.match(hook, /\{\{- if \$ai\.enabled -\}\}/);
  assert.equal(config.includes('widget.kapa.ai'), false);
});

test('Kapa active resource is dynamic, exact-hosted, and never wildcarded', () => {
  const adapter = read('assets/js/kapa-adapter.js');
  const hook = read('layouts/_partials/hooks/body-end.html');
  assert.match(
    adapter,
    /https:\/\/widget\.kapa\.ai\/kapa-widget\.bundle\.js/,
  );
  assert.equal(adapter.includes('*.kapa.ai'), false);
  assert.equal(adapter.includes('https://*'), false);
  assert.equal(hook.includes('<script src="https://'), false);
  assert.equal(hook.includes('widget.kapa.ai'), false);
});

test('theme color and social fallback have one configuration authority', () => {
  const config = read('hugo.yaml');
  const css = read('assets/scss/_styles_project.scss');
  const hook = read('layouts/_partials/hooks/body-end.html');
  const adapter = read('assets/js/kapa-adapter.js');
  assert.match(config, /theme_color: '#532fc9'/);
  assert.match(config, /images: \[\/img\/social\/hugegraph-default\.png\]/);
  assert.equal(css.includes('$hg-navbar-purple'), false);
  assert.equal(css.includes('#532fc9'), false);
  assert.match(hook, /"themeColor"\s+\$themeColor/);
  assert.equal(adapter.includes("'data-project-color': '#532fc9'"), false);
  assert.match(adapter, /'data-project-color': config\.themeColor/);
});

test('documentation menu has five groups and no duplicate version panel', () => {
  const config = read('hugo.yaml');
  const navbarItem = read('layouts/_partials/navbar-item.html');
  for (const id of [
    'docs-start',
    'docs-components',
    'docs-develop',
    'docs-operate',
    'docs-reference',
  ]) {
    assert.match(config, new RegExp(`identifier: ${id}`));
  }
  assert.equal(navbarItem.includes('$hasVersionLinks'), false);
});

test('backlinks are limited to latest documentation', () => {
  const partial = read('layouts/_partials/backlinks-sources.html');
  const renderer = read('layouts/_partials/backlinks.html');
  assert.match(partial, /Params\.version/);
  assert.match(partial, /"latest"/);
  assert.match(partial, /\.Section "docs"/);
  assert.match(renderer, /\$shown := first 5/);
  assert.match(renderer, /\$rest := after 5/);
  assert.match(renderer, /<details class="td-shell-backlinks__more">/);
});

test('search retry reconciliation keeps an existing failure control stable', () => {
  const source = read('assets/js/hugegraph-shell.js');
  assert.match(source, /if \(failed && existing\) return existing/);
  assert.equal(
    source.includes("if (existing) existing.remove();\n      var failure"),
    false,
  );
});

test('image zoom is limited to docs and blog', () => {
  const partial = read('layouts/_partials/content/image-zoom-config.html');
  assert.match(partial, /slice "docs" "blog"/);
});

test('shell persistence uses the version and locale scoped key', () => {
  const source = read('assets/js/hugegraph-shell.js');
  assert.match(source, /oink\.sidebar\.v1\./);
  assert.match(source, /config\.version/);
  assert.match(source, /config\.locale/);
  assert.match(source, /sidebar\.inert = isolated/);
});

test('social fallback asset is exactly 1200 by 630 pixels', () => {
  const image = fs.readFileSync(
    path.join(root, 'static/img/social/hugegraph-default.png'),
  );
  assert.deepEqual(
    [...image.subarray(12, 16)],
    [0x49, 0x48, 0x44, 0x52],
    'PNG must start with an IHDR chunk',
  );
  assert.equal(image.readUInt32BE(16), 1200);
  assert.equal(image.readUInt32BE(20), 630);
});
