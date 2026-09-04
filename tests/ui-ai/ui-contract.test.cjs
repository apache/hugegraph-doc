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

test('theme color and social fallback have one configuration authority', () => {
  const config = read('hugo.yaml');
  const css = read('assets/scss/_styles_project.scss');
  assert.match(config, /theme_color: '#532fc9'/);
  assert.match(config, /images: \[\/img\/social\/hugegraph-default\.png\]/);
  assert.equal(css.includes('$hg-navbar-purple'), false);
  assert.equal(css.includes('#532fc9'), false);
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

test('shell persistence uses the version and locale scoped key', () => {
  const source = read('assets/js/hugegraph-shell.js');
  assert.match(source, /oink\.sidebar\.v1\./);
  assert.match(source, /config\.version/);
  assert.match(source, /config\.locale/);
  assert.match(source, /sidebar\.inert = isolated/);
});
