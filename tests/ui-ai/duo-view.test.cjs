const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const root = path.resolve(__dirname, '../..');
const read = (file) => fs.readFileSync(path.join(root, file), 'utf8');
const exists = (file) => fs.existsSync(path.join(root, file));

const shell = require('../../assets/js/hugegraph-shell.js');
const kapa = require('../../assets/js/kapa-adapter.js');

test('the site enables native Duo View', () => {
  assert.match(read('hugo.yaml'), /^\s*compare: true\s*$/m);
});

test('the legacy preview uses the same build command and toolchain as the site', () => {
  const goVersion = read('go.mod').match(/^go (\S+)$/m)[1];
  const hugoVersion = read('.github/workflows/hugo.yml').match(/^ +HUGO_VERSION: (\S+)$/m)[1];
  const netlify = read('netlify.toml');
  assert.match(netlify, /^command = "bash scripts\/hugo\.sh build"$/m);
  assert.equal(netlify.match(/^GO_VERSION = "([^"]+)"$/m)[1], goVersion);
  assert.equal(netlify.match(/^HUGO_VERSION = "([^"]+)"$/m)[1], hugoVersion);
});

test('the site reuses OINK Duo View instead of carrying a second reader or router', () => {
  for (const file of [
    'assets/js/compare-entry.js',
    'assets/js/compare-scroll.js',
    'assets/js/document-compare.js',
    'layouts/_partials/compare/bootstrap.html',
    'layouts/_partials/compare/entry.html',
    'layouts/_partials/compare/targets.html',
  ]) {
    assert.equal(exists(file), false, `${file} must remain owned by OINK`);
  }

  const updater = read('scripts/update_oink.py');
  for (const file of [
    'assets/js/compare-entry.js',
    'assets/js/compare-scroll.js',
    'assets/js/document-compare.js',
    'layouts/_partials/actions/context.html',
    'layouts/_partials/head.html',
    'layouts/_partials/compare/analytics.html',
    'layouts/_partials/compare/bootstrap.html',
    'layouts/_partials/compare/enabled.html',
    'layouts/_partials/compare/entry.html',
    'layouts/_partials/compare/page-key.html',
    'layouts/_partials/compare/scripts.html',
    'layouts/_partials/compare/targets.html',
  ]) {
    assert.match(updater, new RegExp(file.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  }
});

test('local template overrides retain OINK 1.5.1 page and mobile contracts', () => {
  const manifest = read('layouts/_partials/actions/manifest.html');
  const navbar = read('layouts/_partials/navbar.html');
  const sidebar = read('layouts/_partials/shell/sidebar-panel.html');
  assert.match(manifest, /partial "compare\/page-key\.html" \./);
  assert.doesNotMatch(manifest, /\.RelPermalink \$outputFormat/);
  assert.match(navbar, /\$landingSurface := not \$drawerMode/);
  assert.doesNotMatch(navbar, /\$landingSurface := and \(not \$drawerMode\)/);
  assert.match(sidebar, /T "ui_home"/);
  assert.doesNotMatch(sidebar, /brandName }} home/);
});

test('Duo View panes keep article tables but do not initialize HugeGraph shell controllers', () => {
  let keydown;
  const table = {
    dataset: {},
    addEventListener(name, callback) {
      assert.equal(name, 'keydown');
      keydown = callback;
    },
  };
  const documentObject = new Proxy({
    querySelectorAll(selector) {
      assert.equal(selector, '[data-td-asset-table-scroll]');
      return [table];
    },
  }, {
    get(target, property) {
      if (property in target) return target[property];
      throw new Error(`unexpected pane shell access: ${String(property)}`);
    },
  });

  assert.equal(shell.init({ OinkComparePane: true }, documentObject), undefined);
  assert.equal(table.dataset.hgTableScrollBound, '');
  assert.equal(typeof keydown, 'function');
});

test('language preference and Kapa return before touching a Duo View pane document', () => {
  const forbiddenDocument = new Proxy({}, {
    get(_, property) {
      throw new Error(`unexpected pane document access: ${String(property)}`);
    },
  });

  assert.equal(kapa.init({ OinkComparePane: true }, forbiddenDocument), null);
  vm.runInNewContext(read('assets/js/language-preference.js'), {
    window: { OinkComparePane: true },
    document: forbiddenDocument,
  });
});

test('pane-only HugeGraph chrome is hidden without disabling content runtimes', () => {
  const styles = read('assets/scss/_styles_project.scss');
  assert.match(styles, /html\[data-td-compare-pane\]/);
  for (const selector of ['.hg-ask-ai-launcher', '.hg-ai-consent', '.hg-ai-status']) {
    assert.match(styles, new RegExp(selector.replace('.', '\\.')));
  }
  assert.doesNotMatch(styles, /html\[data-td-compare-pane\][^{]*\{[^}]*script/i);
});
