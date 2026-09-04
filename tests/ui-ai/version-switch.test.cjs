const assert = require('node:assert/strict');
const test = require('node:test');

const shell = require('../../assets/js/hugegraph-shell.js');

function classList() {
  const values = new Set();
  return {
    add(value) { values.add(value); },
    contains(value) { return values.has(value); },
  };
}

test('equivalent targets preserve the current query and hash', () => {
  assert.equal(
    shell.versionTarget(
      {
        url: 'https://hugegraph.apache.org/versions/1.7/docs/quickstart/',
        equivalent: true,
        fallback: false,
      },
      {
        href: 'https://hugegraph.apache.org/docs/quickstart/?q=server#install',
        search: '?q=server',
        hash: '#install',
      },
    ),
    'https://hugegraph.apache.org/versions/1.7/docs/quickstart/?q=server#install',
  );
});

test('fallback targets discard the previous query and hash', () => {
  assert.equal(
    shell.versionTarget(
      {
        url: 'https://hugegraph.apache.org/versions/1.0/cn/docs/#hg-version-fallback',
        equivalent: false,
        fallback: true,
      },
      {
        href: 'https://hugegraph.apache.org/cn/docs/new-page/?q=server#install',
        search: '?q=server',
        hash: '#install',
      },
    ),
    'https://hugegraph.apache.org/versions/1.0/cn/docs/#hg-version-fallback',
  );
});

test('version targets reject executable URL schemes', () => {
  assert.equal(
    shell.versionTarget(
      { url: 'javascript:alert(1)', equivalent: false, fallback: false },
      { href: 'https://hugegraph.apache.org/docs/', search: '', hash: '' },
    ),
    '',
  );
});

test('palette executor and all anchors use the same target semantics', () => {
  const assigned = [];
  const executor = {};
  const anchors = [
    {
      dataset: {
        hgVersionEquivalent: 'true',
        hgVersionFallback: 'false',
      },
      attrs: {
        href: 'https://hugegraph.apache.org/versions/1.7/docs/quickstart/',
      },
      getAttribute(name) { return this.attrs[name]; },
      setAttribute(name, value) { this.attrs[name] = value; },
    },
    {
      dataset: {
        hgVersionEquivalent: 'false',
        hgVersionFallback: 'true',
      },
      attrs: {
        href: 'https://hugegraph.apache.org/versions/1.0/docs/#hg-version-fallback',
      },
      getAttribute(name) { return this.attrs[name]; },
      setAttribute(name, value) { this.attrs[name] = value; },
    },
  ];
  const documentObject = {
    querySelectorAll(selector) {
      assert.equal(selector, 'a[data-hg-version-id]');
      return anchors;
    },
  };
  const location = {
    href: 'https://hugegraph.apache.org/docs/quickstart/?q=server#install',
    search: '?q=server',
    hash: '#install',
    assign(value) { assigned.push(value); },
  };
  const windowObject = {
    location,
    OinkActions: {
      registerExecutor(id, callback) { executor[id] = callback; },
    },
  };

  shell.initVersionSwitching(windowObject, documentObject);

  assert.equal(
    anchors[0].attrs.href,
    'https://hugegraph.apache.org/versions/1.7/docs/quickstart/?q=server#install',
  );
  assert.equal(
    anchors[1].attrs.href,
    'https://hugegraph.apache.org/versions/1.0/docs/#hg-version-fallback',
  );
  executor.switch_version({
    value: {
      url: 'https://hugegraph.apache.org/versions/1.7/docs/quickstart/',
      equivalent: true,
      fallback: false,
    },
  });
  assert.deepEqual(assigned, [anchors[0].attrs.href]);
});

test('fallback notice is localized, visible, and consumed exactly once', () => {
  const appended = [];
  const replacements = [];
  const location = {
    href: 'https://hugegraph.apache.org/cn/docs/#hg-version-fallback',
    pathname: '/cn/docs/',
    search: '',
    hash: '#hg-version-fallback',
  };
  const documentObject = {
    body: { prepend(node) { appended.push(node); } },
    createElement(name) {
      return {
        name,
        classList: classList(),
        attrs: {},
        dataset: {},
        setAttribute(key, value) { this.attrs[key] = value; },
        textContent: '',
      };
    },
  };
  const windowObject = {
    location,
    history: {
      state: { page: 1 },
      replaceState(state, title, url) {
        replacements.push([state, title, url]);
        location.hash = '';
      },
    },
  };
  const config = {
    docsRoot: '/cn/docs/',
    versionFallbackMessage:
      '目标版本没有此页面，已转到该版本的文档首页。',
  };

  shell.consumeVersionFallback(windowObject, documentObject, config);
  shell.consumeVersionFallback(windowObject, documentObject, config);

  assert.deepEqual(replacements, [[{ page: 1 }, '', '/cn/docs/']]);
  assert.equal(appended.length, 1);
  assert.equal(appended[0].attrs.role, 'status');
  assert.equal(appended[0].attrs['aria-live'], 'polite');
  assert.equal(appended[0].attrs['aria-atomic'], 'true');
  assert.equal(appended[0].dataset.hgVersionFallbackNotice, '');
  assert.equal(appended[0].textContent, config.versionFallbackMessage);
  assert.equal(appended[0].classList.contains('hg-version-fallback'), true);
});
