const assert = require('node:assert/strict');
const test = require('node:test');
const shell = require('../../assets/js/hugegraph-shell.js');

function fixture({ saved, blocked = false, pathname = '/docs/', version = 'latest', locale = 'en' } = {}) {
  const key = `oink.sidebar.v2.${version}.${locale}`;
  const values = new Map(saved === undefined ? [] : [[key, saved]]);
  const ids = ['root_navstart-children', 'root_navcomponents-children', 'root_navdevelop-children', 'active'];
  const states = new Map(ids.map(id => [id, false]));
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
    querySelectorAll() {
      return ids.map(id => ({
        getAttribute() { return id; },
        closest() { return { classList: { contains() { return id === 'active'; } } }; },
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
  f.change('aside-toc', true, 'user');
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
  assert.equal(f.calls.length, 4);
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
