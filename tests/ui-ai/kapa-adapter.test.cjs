const assert = require('node:assert/strict');
const test = require('node:test');

const adapter = require('../../assets/js/kapa-adapter.js');

function harness() {
  const calls = [];
  const timers = new Map();
  const scripts = [];
  let nextTimer = 1;
  let renderCallbacks = [];
  const trigger = {
    dataset: {},
    disabled: false,
    attrs: {},
    setAttribute(name, value) { this.attrs[name] = value; },
    removeAttribute(name) { delete this.attrs[name]; },
    focus() { this.focused = true; },
  };
  const status = {
    textContent: '',
    classList: { toggle() {} },
  };
  const documentObject = {
    activeElement: trigger,
    querySelector(selector) {
      if (selector === '[data-hg-ai-status]') return status;
      if (selector === 'script[data-hg-kapa-widget]') {
        return scripts.find((script) => !script.removed) || null;
      }
      return null;
    },
    querySelectorAll(selector) {
      return selector === '[data-hg-ask-ai]' ? [trigger] : [];
    },
    createElement(name) {
      assert.equal(name, 'script');
      const listeners = new Map();
      const script = {
        dataset: {},
        attrs: {},
        addEventListener(name, callback) { listeners.set(name, callback); },
        setAttribute(name, value) { this.attrs[name] = value; },
        remove() { this.removed = true; },
        fire(name) {
          const callback = listeners.get(name);
          if (callback) callback();
        },
      };
      scripts.push(script);
      return script;
    },
    head: {
      appendChild(script) { script.appended = true; },
    },
  };
  const windowObject = {
    setKapaImplementation() {
      this.Kapa = function (method, value) {
        calls.push([method, value]);
        if (method === 'render') renderCallbacks.push(value.onRender);
      };
    },
    Kapa(method, value) {
      calls.push([method, value]);
      if (method === 'render') renderCallbacks.push(value.onRender);
    },
    setTimeout(callback) {
      const id = nextTimer++;
      timers.set(id, callback);
      return id;
    },
    clearTimeout(id) { timers.delete(id); },
  };
  const config = {
    websiteId: 'website',
    sourceGroupId: 'source-en',
    locale: 'en',
    themeColor: '#123456',
    labels: { error: 'unavailable' },
  };
  return {
    calls,
    config,
    documentObject,
    fireRender(index = renderCallbacks.length - 1) { renderCallbacks[index](); },
    fireTimeout() { Array.from(timers.values()).forEach((callback) => callback()); },
    installBundle() {
      const queued =
        windowObject.Kapa && Array.isArray(windowObject.Kapa.q)
          ? windowObject.Kapa.q.slice()
          : [];
      windowObject.setKapaImplementation();
      queued.forEach((args) => windowObject.Kapa(...Array.from(args)));
    },
    renderCallbacks,
    scripts,
    trigger,
    windowObject,
  };
}

test('uses one fixed bundle and explicit privacy-safe widget settings', () => {
  assert.equal(
    adapter.BUNDLE_URL,
    'https://widget.kapa.ai/kapa-widget.bundle.js',
  );
  const attrs = adapter.scriptAttributes({
    websiteId: 'website',
    sourceGroupId: 'source-cn',
    locale: 'zh',
    themeColor: '#123456',
  });
  assert.equal(attrs['data-render-on-load'], 'false');
  assert.equal(attrs['data-launcher-button-hidden'], 'true');
  assert.equal(attrs['data-search-mode-enabled'], 'false');
  assert.equal(attrs['data-modal-open-on-command-k'], 'false');
  assert.equal(attrs['data-consent-required'], 'false');
  assert.equal(attrs['data-user-analytics-cookie-enabled'], 'false');
  assert.equal(attrs['data-user-analytics-fingerprint-enabled'], 'false');
  assert.equal(attrs['data-bot-protection-mechanism'], 'hcaptcha');
  assert.equal(attrs['data-source-group-ids-include'], 'source-cn');
  assert.equal(attrs['data-project-color'], '#123456');
  assert.equal(attrs['data-anchor-color'], '#123456');
  assert.equal(attrs['data-project-color-dark'], '#8495a7');
  assert.equal(attrs['data-anchor-color-dark'], '#a0aebb');
  assert.notEqual(attrs['data-project-color-dark'], '#9f83ff');
  assert.notEqual(attrs['data-anchor-color-dark'], '#b6a3ff');
});

test('sends only the trimmed query after explicit activation and render', () => {
  const h = harness();
  const controller = adapter.createController(
    h.windowObject,
    h.documentObject,
    h.config,
  );
  assert.deepEqual(h.calls.map(([name]) => name), ['onModalClose']);

  controller.activate('  how to start?  ', true, h.trigger);
  assert.equal(controller.getState(), 'loading');
  assert.deepEqual(h.calls.map(([name]) => name), ['onModalClose', 'render']);

  h.scripts[0].fire('load');
  h.fireRender();
  assert.equal(controller.getState(), 'ready');
  assert.deepEqual(h.calls.slice(-2), [
    ['setSourceGroupIDs', ['source-en']],
    ['open', { mode: 'ai', query: 'how to start?', submit: true }],
  ]);
  assert.equal(
    JSON.stringify(h.calls).includes('http'),
    false,
    'no page URL is passed to Kapa',
  );
});

test('ignores duplicate activation and never opens after a late render', () => {
  const h = harness();
  const controller = adapter.createController(
    h.windowObject,
    h.documentObject,
    h.config,
  );
  controller.activate('first', true, h.trigger);
  controller.activate('second', true, h.trigger);
  assert.equal(
    h.calls.filter(([name]) => name === 'render').length,
    1,
  );

  h.fireTimeout();
  assert.equal(controller.getState(), 'error');
  assert.equal(h.scripts[0].removed, true);
  h.fireRender();
  assert.equal(
    h.calls.filter(([name]) => name === 'open').length,
    0,
  );
});

test('launcher opens a blank session without auto-submit', () => {
  const h = harness();
  const controller = adapter.createController(
    h.windowObject,
    h.documentObject,
    h.config,
  );
  controller.activate('', false, h.trigger);
  h.scripts[0].fire('load');
  h.fireRender();
  assert.deepEqual(h.calls.at(-1), [
    'open',
    { mode: 'ai', query: '', submit: false },
  ]);
});

test('a pending timeout retries with a fresh script and ignores the late attempt', () => {
  const h = harness();
  const controller = adapter.createController(
    h.windowObject,
    h.documentObject,
    h.config,
  );
  controller.activate('first', true, h.trigger);
  assert.equal(h.scripts.length, 1);
  const staleRender = h.renderCallbacks[0];

  h.fireTimeout();
  assert.equal(controller.getState(), 'error');
  assert.equal(h.scripts[0].removed, true);
  assert.equal(h.trigger.attrs.title, 'unavailable');

  controller.activate('second', true, h.trigger);
  assert.equal(h.trigger.attrs.title, undefined);
  assert.equal(h.scripts.length, 2);
  assert.match(h.scripts[1].src, /\?hg-retry=2$/);
  staleRender();
  assert.equal(
    h.calls.filter(([name]) => name === 'open').length,
    0,
    'a late callback from the timed-out script must stay inert',
  );

  h.installBundle();
  h.scripts[1].fire('load');
  h.fireRender();
  assert.equal(controller.getState(), 'ready');
  assert.equal(h.trigger.attrs.title, undefined);
  assert.deepEqual(h.calls.at(-1), [
    'open',
    { mode: 'ai', query: 'second', submit: true },
  ]);
});
