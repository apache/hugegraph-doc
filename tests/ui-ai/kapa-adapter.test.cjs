const assert = require('node:assert/strict');
const test = require('node:test');

const adapter = require('../../assets/js/kapa-adapter.js');

function harness() {
  const calls = [];
  const timers = new Map();
  let nextTimer = 1;
  let onRender = null;
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
  const script = {};
  const documentObject = {
    activeElement: trigger,
    querySelector(selector) {
      if (selector === '[data-hg-ai-status]') return status;
      if (selector === 'script[data-hg-kapa-widget]') return script;
      return null;
    },
    querySelectorAll(selector) {
      return selector === '[data-hg-ask-ai]' ? [trigger] : [];
    },
  };
  const windowObject = {
    Kapa(method, value) {
      calls.push([method, value]);
      if (method === 'render') onRender = value.onRender;
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
    labels: { error: 'unavailable' },
  };
  return {
    calls,
    config,
    documentObject,
    fireRender() { onRender(); },
    fireTimeout() { Array.from(timers.values()).forEach((callback) => callback()); },
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
  h.fireRender();
  assert.deepEqual(h.calls.at(-1), [
    'open',
    { mode: 'ai', query: '', submit: false },
  ]);
});
