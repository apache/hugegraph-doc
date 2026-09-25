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
  const consentListeners = new Map();
  const continueButton = { addEventListener(name, callback) { consentListeners.set(`continue:${name}`, callback); } };
  const cancelButton = { addEventListener(name, callback) { consentListeners.set(`cancel:${name}`, callback); } };
  const consent = {
    open: false,
    showModal() { this.open = true; },
    close() { this.open = false; },
    addEventListener(name, callback) { consentListeners.set(`dialog:${name}`, callback); },
    querySelector(selector) {
      if (selector === '[data-hg-ai-continue]') return continueButton;
      if (selector === '[data-hg-ai-cancel]') return cancelButton;
      return null;
    },
  };
  const documentObject = {
    activeElement: trigger,
    querySelector(selector) {
      if (selector === '[data-hg-ai-status]') return status;
      if (selector === '[data-hg-ai-consent]') return consent;
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
    continueConsent() { consentListeners.get('continue:click')(); },
    cancelConsent() { consentListeners.get('cancel:click')(); },
    escapeConsent() { consentListeners.get('dialog:keydown')({ key: 'Escape', preventDefault() {}, stopPropagation() {} }); },
    nativeCancel() { consentListeners.get('dialog:cancel')({ preventDefault() {} }); },
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
  assert.equal(attrs['data-project-logo'], '/img/logo.svg');
  assert.ok(Number(attrs['data-modal-z-index']) > 1040, 'modal must cover the site launcher');
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
  h.continueConsent();
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
  h.continueConsent();
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
  h.continueConsent();
  h.scripts[0].fire('load');
  h.fireRender();
  assert.deepEqual(h.calls.at(-1), [
    'open',
    { mode: 'ai', query: '', submit: false },
  ]);
});

test('cancel, Escape, and native cancel keep Kapa unloaded and restore focus', () => {
  for (const close of ['cancelConsent', 'escapeConsent', 'nativeCancel']) {
    const h = harness();
    const controller = adapter.createController(h.windowObject, h.documentObject, h.config);
    controller.activate('private question', true, h.trigger);
    assert.equal(controller.getState(), 'consent');
    h[close]();
    assert.equal(controller.getState(), 'idle');
    assert.equal(h.scripts.length, 0);
    assert.equal(h.trigger.focused, true);
  }
});

test('a pending timeout retries with a fresh script and ignores the late attempt', () => {
  const h = harness();
  const controller = adapter.createController(
    h.windowObject,
    h.documentObject,
    h.config,
  );
  controller.activate('first', true, h.trigger);
  h.continueConsent();
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

test('init succeeds without search shell and binds standalone triggers', () => {
  const h = harness();
  const configNode = {
    textContent: JSON.stringify({
      websiteId: 'test-id',
      sourceGroupId: 'test-group',
      locale: 'en',
      themeColor: '#532fc9',
      historical: false,
      labels: { ask: 'Ask AI' },
    }),
  };
  const doc = {
    ...h.documentObject,
    getElementById(id) {
      if (id === 'hg-ai-config') return configNode;
      if (id === 'td-shell-search') return null;
      return null;
    },
  };
  h.trigger.addEventListener = (name, cb) => {};
  const controller = adapter.init(h.windowObject, doc);
  assert.ok(controller);
  assert.equal(h.trigger.dataset.hgAiBound, '');
});

test('registers native search rows with localized title and historical notice', async () => {
  const h = harness();
  let extension;
  h.windowObject.OinkCommandPalette = { registerSearchTail(value) { extension = value; } };
  h.trigger.addEventListener = () => {};
  h.documentObject.getElementById = (id) => id === 'hg-ai-config' ? {
    textContent: JSON.stringify({ ...h.config, historical: true,
      labels: { ask: 'Ask AI', latest: 'Answers use latest docs' } }),
  } : null;
  adapter.init(h.windowObject, h.documentObject);
  assert.equal(extension.id, 'hugegraph-ai');
  assert.deepEqual(extension.rows({ query: '<graph>' }), [{
    id: 'ask', title: 'Ask AI: “<graph>”',
    description: 'Answers use latest docs.', icon: 'fa-solid fa-wand-magic-sparkles',
  }]);
  const abort = new AbortController();
  let handedOff = false;
  const completion = extension.activate({}, {
    query: 'graph query', signal: abort.signal,
    handoff() { handedOff = true; return true; },
  });
  assert.equal(handedOff, true);
  assert.equal(h.scripts.length, 0);
  h.continueConsent();
  h.scripts[0].fire('load');
  h.fireRender();
  await completion;
  assert.deepEqual(h.calls.at(-1), ['open', { mode: 'ai', query: 'graph query', submit: true }]);
});

test('search cancellation during consent or loading prevents stale widget opens', async () => {
  for (const stage of ['consent', 'loading']) {
    const h = harness();
    const controller = adapter.createController(h.windowObject, h.documentObject, h.config);
    const abort = new AbortController();
    const completion = controller.activate('private', true, h.trigger, {
      signal: abort.signal, handoff() { return true; },
    });
    if (stage === 'loading') h.continueConsent();
    abort.abort();
    await completion;
    assert.equal(controller.getState(), 'idle');
    if (stage === 'loading') {
      h.scripts[0].fire('load');
      h.fireRender();
      assert.equal(h.scripts[0].removed, true);
    }
    assert.equal(h.calls.some(([method]) => method === 'open'), false);
    assert.equal(h.trigger.focused, undefined, 'cancellation must not steal new palette focus');
  }
});

test('search handoff refuses stale activation and load failure rejects completion', async () => {
  const h = harness();
  const controller = adapter.createController(h.windowObject, h.documentObject, h.config);
  await controller.activate('stale', true, h.trigger, {
    signal: new AbortController().signal, handoff() { return false; },
  });
  assert.equal(controller.getState(), 'idle');
  const completion = controller.activate('retry', true, h.trigger, {
    signal: new AbortController().signal, handoff() { return true; },
  });
  h.continueConsent();
  h.scripts[0].fire('error');
  await assert.rejects(completion, /unavailable/);
  assert.equal(controller.getState(), 'error');
});


test('an aborted load retries with fresh callbacks and restores launcher focus on close', async () => {
  const h = harness();
  const controller = adapter.createController(h.windowObject, h.documentObject, h.config);
  const abort = new AbortController();
  const completion = controller.activate('cancelled', true, h.trigger, {
    signal: abort.signal, handoff() { return true; },
  });
  h.continueConsent();
  abort.abort();
  await completion;
  controller.activate('fresh', true, h.trigger);
  h.installBundle();
  h.scripts[1].fire('load');
  h.fireRender();
  assert.deepEqual(h.calls.at(-1), ['open', { mode: 'ai', query: 'fresh', submit: true }]);
  h.calls.filter(([method]) => method === 'onModalClose').at(-1)[1]();
  assert.equal(h.trigger.focused, true);
});

test('widget API failures settle palette activation and permit a fresh retry', async () => {
  for (const failingMethod of ['setSourceGroupIDs', 'open']) {
    for (const stage of ['initial load', 'ready reopen']) {
      const h = harness();
      const controller = adapter.createController(h.windowObject, h.documentObject, h.config);
      if (stage === 'ready reopen') {
        controller.activate('', false, h.trigger);
        h.continueConsent();
        h.scripts[0].fire('load');
        h.fireRender();
      }
      const originalKapa = h.windowObject.Kapa;
      h.windowObject.Kapa = (method, value) => {
        if (method === failingMethod) throw new Error('vendor failure');
        return originalKapa(method, value);
      };
      const abort = new AbortController();
      const completion = controller.activate('failing', true, h.trigger, {
        signal: abort.signal, handoff() { return true; },
      });
      if (stage === 'initial load') {
        h.continueConsent();
        h.scripts[0].fire('load');
        h.fireRender();
      }
      await assert.rejects(completion, /unavailable/);
      assert.equal(controller.getState(), 'error');
      assert.equal(h.trigger.disabled, false);
      assert.equal(h.scripts[0].removed, true);
      // Settlement must release the old cancellation listener.
      abort.abort();
      assert.equal(controller.getState(), 'error');

      const retry = controller.activate('recovered', true, h.trigger, {
        signal: new AbortController().signal, handoff() { return true; },
      });
      h.installBundle();
      h.scripts[1].fire('load');
      h.fireRender();
      await retry;
      assert.equal(controller.getState(), 'ready');
      assert.deepEqual(h.calls.at(-1), ['open', {
        mode: 'ai', query: 'recovered', submit: true,
      }]);
    }
  }
});

test('stale activation refreshes the palette query and cancellation context', () => {
  for (const query of ['fresh question', '', '   ', '> theme']) {
    const h = harness();
    let extension;
    const refreshed = [];
    const activated = [];
    h.windowObject.OinkCommandPalette = {
      registerSearchTail(value) { extension = value; },
      instance: {
        render(value) { refreshed.push(value); },
        rows() { return query === 'fresh question' ? [
          { type: 'page' }, { type: 'extension', owner: { id: 'hugegraph-ai' } },
        ] : []; },
        activate(index) { activated.push(index); },
      },
    };
    h.trigger.addEventListener = () => {};
    h.documentObject.getElementById = () => ({ textContent: JSON.stringify(h.config) });
    const originalQuery = h.documentObject.querySelector;
    h.documentObject.querySelector = selector =>
      selector === '#td-shell-search .td-shell-search__input' ? { value: query } : originalQuery(selector);
    adapter.init(h.windowObject, h.documentObject);
    extension.activate({}, {
      query: 'stale question', signal: new AbortController().signal,
      handoff() { assert.fail('stale context must not hand off'); },
    });
    assert.deepEqual(refreshed, [query.trim()]);
    assert.deepEqual(activated, query === 'fresh question' ? [1] : []);
    assert.equal(h.scripts.length, 0);
  }
});
