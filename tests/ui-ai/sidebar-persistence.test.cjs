const assert = require('node:assert/strict');
const test = require('node:test');
const shell = require('../../assets/js/hugegraph-shell.js');

function fixture({ saved, legacy, asideExpanded = false, blocked = false, pathname = '/docs/', version = 'latest', locale = 'en' } = {}) {
  const key = `oink.sidebar.v3.${version}.${locale}`;
  const values = new Map(saved === undefined ? [] : [[key, saved]]);
  if (legacy !== undefined) values.set(`oink.sidebar.v2.${version}.${locale}`, legacy);
  const ids = ['root_navstart-children', 'root_navcomponents-children', 'root_navdevelop-children', 'active', 'aside-toc'];
  const states = new Map(ids.map(id => [id, false]));
  states.set('aside-toc', asideExpanded);
  const calls = [];
  const listeners = new Map();
  let ready;
  const api = {
    ready: new Promise(resolve => { ready = resolve; }),
    setExpanded(id, value, options) {
      calls.push({ id, value, options });
      states.set(id, id === 'active' || value);
    },
    getState(id) { return { id, expanded: states.get(id) }; },
  };
  const doc = {
    querySelectorAll(selector) {
      const selected = ids.filter(id => id !== 'aside-toc' || selector.includes('[data-td-shell-aside]'));
      return selected.map(id => ({
        getAttribute() { return id; },
        closest(selector) {
          if (selector === '[data-td-shell-aside]') return id === 'aside-toc' ? {} : null;
          return { classList: { contains() { return id === 'active'; } } };
        },
      }));
    },
    addEventListener(name, listener) { listeners.set(name, listener); },
  };
  const win = {
    OinkSidebar: api,
    location: { pathname },
    get localStorage() {
      if (blocked) throw new Error('denied');
      return {
        getItem(name) { return values.get(name) ?? null; },
        setItem(name, value) { values.set(name, value); },
        removeItem(name) { values.delete(name); },
      };
    },
  };
  const initialized = shell.initTreePersistence(win, doc, { version, locale });
  return { key, values, states, calls, ready, initialized, change(id, expanded, source) {
    states.set(id, expanded);
    listeners.get('oink:sidebar-disclosure')({ detail: { id, expanded, source } });
  } };
}

test('waits for OINK hydration then restores docs defaults through the API', async () => {
  const f = fixture();
  assert.equal(f.calls.length, 0);
  f.ready();
  await f.initialized;
  assert.equal(f.states.get('root_navstart-children'), true);
  assert.equal(f.states.get('root_navcomponents-children'), true);
  assert.equal(f.states.get('root_navdevelop-children'), false);
  assert.equal(f.states.get('active'), true);
  assert.ok(f.calls.every(call => call.options.source === 'api'));
  assert.deepEqual(JSON.parse(f.values.get(f.key)), ['root_navstart-children', 'root_navcomponents-children']);
});

test('preserves stored empty choices and ignores automatic and non-sidebar events', async () => {
  const f = fixture({ saved: '[]', version: '1.7', locale: 'cn', pathname: '/versions/1.7/cn/docs/' });
  f.ready();
  await f.initialized;
  assert.equal(f.states.get('root_navstart-children'), false);
  f.change('root_navdevelop-children', true, 'responsive');
  assert.equal(f.values.get(f.key), '[]');
  f.change('unrelated-disclosure', true, 'user');
  assert.equal(f.values.get(f.key), '[]');
  f.change('root_navdevelop-children', true, 'user');
  assert.deepEqual(JSON.parse(f.values.get(f.key)), ['root_navdevelop-children']);
  f.change('root_navdevelop-children', false, 'user');
  assert.equal(f.values.get(f.key), '[]');
});

test('restores compatible stored ids and discards stale ids', async () => {
  const f = fixture({ saved: '["root_navdevelop-children","removed",42]' });
  f.ready();
  await f.initialized;
  assert.equal(f.states.get('root_navdevelop-children'), true);
  assert.equal(f.states.get('root_navstart-children'), false);
  assert.equal(f.calls.length, 5);
});

for (const options of [{ blocked: true }, { saved: '{bad' }, { saved: '{}' }]) {
  test(`unavailable or invalid storage retains defaults: ${JSON.stringify(options)}`, async () => {
    const f = fixture(options);
    f.ready();
    await f.initialized;
    assert.equal(f.states.get('root_navstart-children'), true);
    assert.equal(f.states.get('active'), true);
    assert.doesNotThrow(() => f.change('root_navdevelop-children', true, 'user'));
  });
}

test('restores and saves aside TOC disclosures through the same API', async () => {
  const f = fixture({ saved: '["aside-toc"]', pathname: '/docs/introduction/' });
  f.ready();
  await f.initialized;
  assert.equal(f.states.get('aside-toc'), true);
  f.change('aside-toc', false, 'user');
  assert.equal(f.values.get(f.key), '[]');
  f.change('aside-toc', true, 'user');
  assert.deepEqual(JSON.parse(f.values.get(f.key)), ['aside-toc']);
});

for (const legacy of ['[]', '["root_navdevelop-children"]']) {
  test(`migrates main-tree v2 preferences without collapsing the aside: ${legacy}`, async () => {
    const f = fixture({ legacy, asideExpanded: true });
    f.ready();
    await f.initialized;
    assert.equal(f.states.get('aside-toc'), true);
    assert.equal(f.states.get('root_navstart-children'), false);
    assert.equal(f.states.get('root_navdevelop-children'), legacy !== '[]');
    assert.deepEqual(JSON.parse(f.values.get(f.key)), [...JSON.parse(legacy), 'aside-toc']);
    f.change('aside-toc', false, 'user');
    const reloaded = fixture({ saved: f.values.get(f.key), legacy, asideExpanded: true });
    reloaded.ready();
    await reloaded.initialized;
    assert.equal(reloaded.states.get('aside-toc'), false);
    assert.equal(reloaded.states.get('root_navdevelop-children'), legacy !== '[]');
  });
}
