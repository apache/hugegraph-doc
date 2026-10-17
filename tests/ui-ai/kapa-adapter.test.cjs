const assert = require('node:assert/strict');
const test = require('node:test');

const adapter = require('../../assets/js/kapa-adapter.js');

function harness(storage = new Map()) {
  const calls = [];
  const timers = new Map();
  const scripts = [];
  let nextTimer = 1;
  let renderCallbacks = [];
  const trigger = {
    dataset: {},
    hidden: true,
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
  const continueButton = { focus() { this.focused = true; }, addEventListener(name, callback) { consentListeners.set(`continue:${name}`, callback); } };
  const cancelButton = { addEventListener(name, callback) { consentListeners.set(`cancel:${name}`, callback); } };
  const consent = {
    hidden: false,
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
      if (selector === '.hg-ask-ai-launcher') return trigger;
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
  const windowListeners = new Map();
  const windowObject = {
    addEventListener(name, cb) { windowListeners.set(name, cb); },
    location: { reload() { windowObject.reloaded = true; } },
    localStorage: {
      getItem(key) { return storage.get(key) || null; },
      setItem(key, value) { storage.set(key, value); },
      removeItem(key) { storage.delete(key); },
    },
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
    exampleQuestions: ['How do I start HugeGraph?', 'How do I import data?'],
    communityURL: 'https://github.com/apache/hugegraph/issues',
    labels: { error: 'unavailable', community: 'Ask the community' },
  };
  return {
    calls,
    status,
    storageEvent(event) { windowListeners.get('storage')(event); },
    consent,
    continueButton,
    storage,
    config,
    documentObject,
    fireRender(index = renderCallbacks.length - 1) { renderCallbacks[index](); },
    fireTimeout() { Array.from(timers.values()).forEach((callback) => callback()); },
    continueConsent() { consentListeners.get('continue:click')(); },
    cancelConsent() { consentListeners.get('cancel:click')(); },
    escapeConsent() { consentListeners.get('dialog:keydown')({ key: 'Escape', preventDefault() {}, stopPropagation() {} }); },
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
    exampleQuestions: ['如何启动 HugeGraph？', '如何导入数据？'],
    labels: { community: '向社区求助' },
    communityURL: 'https://github.com/apache/hugegraph/issues',
  });
  assert.equal(attrs['data-example-questions'], '如何启动 HugeGraph？,如何导入数据？');
  assert.equal(attrs['data-example-questions-col-span'], '12');
  assert.equal(attrs['data-answer-cta-button-enabled'], 'true');
  assert.equal(attrs['data-answer-cta-button-text'], '向社区求助');
  assert.equal(attrs['data-answer-cta-button-link'], 'https://github.com/apache/hugegraph/issues');
  assert.equal(attrs['data-chat-disclaimer'], undefined);
  assert.equal(Object.keys(attrs).some(name => /handoff|email/.test(name)), false);
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

test('cancel and Escape keep Kapa unloaded and restore focus', () => {
  for (const close of ['cancelConsent', 'escapeConsent']) {
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


test('persistent consent survives language navigation but never loads before activation', () => {
  const first = harness();
  const controller = adapter.createController(first.windowObject, first.documentObject, first.config);
  controller.activate('', false, first.trigger);
  first.continueConsent();
  const next = harness(first.storage);
  next.config.locale = 'zh';
  next.config.sourceGroupId = 'source-cn';
  next.config.labels.community = '向社区求助';
  const nextController = adapter.createController(next.windowObject, next.documentObject, next.config);
  assert.equal(nextController.getState(), 'idle');
  assert.equal(next.scripts.length, 0);
  nextController.activate('', false, next.trigger);
  assert.equal(nextController.getState(), 'loading');
  assert.equal(next.scripts[0].attrs['data-source-group-ids-include'], 'source-cn');
  assert.equal(next.scripts[0].attrs['data-answer-cta-button-text'], '向社区求助');

});

test('consent is scoped to website id and rejects obsolete or malformed grants', () => {
  for (const entries of [
    [['hg-ai-consent:v2:other', 'granted']],
    [['hg-ai-consent:v0:website', 'granted']],
    [['hg-ai-consent:v1:website', 'granted']],
    [['hg-ai-consent:v2:website', 'true']],
  ]) {
    const h = harness(new Map(entries));
    const controller = adapter.createController(h.windowObject, h.documentObject, h.config);
    controller.activate('', false, h.trigger);
    assert.equal(controller.getState(), 'consent');
    assert.equal(h.scripts.length, 0);
  }
});

test('unavailable local storage leaves consent explicit and usable for this page', () => {
  for (const failure of ['property', 'methods']) {
    const h = harness();
    if (failure === 'property') Object.defineProperty(h.windowObject, 'localStorage', {
      get() { throw new Error('blocked'); },
    });
    else h.windowObject.localStorage = {
      getItem() { throw new Error('blocked'); },
      setItem() { throw new Error('blocked'); },
      removeItem() { throw new Error('blocked'); },
    };
    const controller = adapter.createController(h.windowObject, h.documentObject, h.config);
    controller.activate('', false, h.trigger);
    assert.equal(controller.getState(), 'consent');
    assert.equal(h.scripts.length, 0);
    h.continueConsent();
    assert.equal(controller.getState(), 'loading');
    assert.equal(h.storage.size, 0);
  }
});


test('random examples select three distinct pool entries without mutating the pool', () => {
  const pool = ['one', 'two', 'three', 'four', 'five'];
  assert.deepEqual(adapter.pickExampleQuestions(pool, () => 0.999), ['one', 'two', 'three']);
  assert.deepEqual(adapter.pickExampleQuestions(pool, () => 0), ['two', 'three', 'four']);
  assert.deepEqual(pool, ['one', 'two', 'three', 'four', 'five']);
  assert.deepEqual(adapter.pickExampleQuestions(['one', 'one', 'two'], () => 0.999), ['one', 'two']);
  assert.deepEqual(adapter.pickExampleQuestions([], () => 0), []);
});

test('a page retains its sampled examples when the widget load is retried', () => {
  const h = harness();
  h.config.exampleQuestions = ['one', 'two', 'three', 'four', 'five'];
  const controller = adapter.createController(h.windowObject, h.documentObject, h.config);
  controller.activate('', false, h.trigger);
  h.continueConsent();
  const selected = h.scripts[0].attrs['data-example-questions'].split(',');
  assert.equal(selected.length, 3);
  assert.equal(new Set(selected).size, 3);
  assert.ok(selected.every(question => h.config.exampleQuestions.includes(question)));
  h.fireTimeout();
  controller.activate('', false, h.trigger);
  assert.equal(h.scripts[1].attrs['data-example-questions'], selected.join(','));
});


test('explicit activation opens consent and agreement restores the launcher on widget close', () => {
  const h = harness();
  const controller = adapter.createController(h.windowObject, h.documentObject, h.config);
  assert.equal(h.consent.hidden, true);
  assert.equal(h.trigger.hidden, false);
  assert.equal(h.scripts.length, 0);
  controller.activate('', false, h.trigger);
  assert.equal(h.consent.hidden, false);
  h.continueConsent();
  assert.equal(h.consent.hidden, true);
  assert.equal(h.trigger.hidden, false);
  assert.equal(h.trigger.attrs['aria-haspopup'], 'dialog');
  assert.equal(h.storage.get('hg-ai-consent:v2:website'), 'granted');
  h.scripts[0].fire('load');
  h.fireRender();
  assert.deepEqual(h.calls.at(-1), ['open', { mode: 'ai', query: '', submit: false }]);
  h.calls.find(([method]) => method === 'onModalClose')[1]();
  assert.equal(h.trigger.focused, true);
  h.continueConsent();
  assert.equal(h.scripts.length, 1);
});

test('explicit consent dismissal remembers no-grant choice and pending activation focuses agreement', () => {
  const h = harness();
  const controller = adapter.createController(h.windowObject, h.documentObject, h.config);
  controller.activate('', false, h.trigger);
  h.cancelConsent();
  assert.equal(h.trigger.hidden, false);
  assert.equal(h.trigger.focused, true);
  assert.equal(h.trigger.attrs['aria-haspopup'], undefined);
  assert.equal(h.consent.hidden, true);
  assert.equal(h.storage.get('hg-ai-consent:v2:website'), 'dismissed');
  assert.equal(h.scripts.length, 0);
  controller.activate('  import data  ', true, h.trigger);
  assert.equal(h.consent.hidden, false);
  assert.equal(h.continueButton.focused, true);
  assert.equal(h.trigger.hidden, true);
  h.continueConsent();
  h.scripts[0].fire('load');
  h.fireRender();
  assert.deepEqual(h.calls.at(-1), ['open', { mode: 'ai', query: 'import data', submit: true }]);
});


test('remembered dismissal stays local and explicit reopening still requires consent', () => {
  for (const dismiss of ['cancelConsent', 'escapeConsent']) {
    const first = harness();
    adapter.createController(first.windowObject, first.documentObject, first.config).activate('', false, first.trigger);
    first[dismiss]();
    const next = harness(first.storage);
    next.config.locale = 'zh';
    const controller = adapter.createController(next.windowObject, next.documentObject, next.config);
    assert.equal(next.consent.hidden, true);
    assert.equal(next.trigger.hidden, false);
    assert.equal(next.trigger.attrs['aria-haspopup'], undefined);
    assert.equal(next.scripts.length, 0);
    controller.activate('private query', true, next.trigger);
    assert.equal(controller.getState(), 'consent');
    assert.equal(next.consent.hidden, false);
    assert.equal(next.trigger.hidden, true);
    assert.equal(next.scripts.length, 0);
  }
});

test('blocked storage keeps dismissal page-only and requires explicit activation next visit', () => {
  const h = harness();
  h.windowObject.localStorage.setItem = () => { throw new Error('blocked'); };
  adapter.createController(h.windowObject, h.documentObject, h.config).activate('', false, h.trigger);
  h.cancelConsent();
  assert.equal(h.consent.hidden, true);
  assert.equal(h.storage.size, 0);
  const fresh = harness(h.storage);
  const controller = adapter.createController(fresh.windowObject, fresh.documentObject, fresh.config);
  assert.equal(fresh.consent.hidden, true);
  assert.equal(fresh.scripts.length, 0);
  controller.activate('', false, fresh.trigger);
  assert.equal(fresh.consent.hidden, false);
  assert.equal(fresh.scripts.length, 0);
});


test('cross-tab removal or storage clear reloads consented tabs and ignores unrelated updates', () => {
  for (const key of ['hg-ai-consent:v2:website', null]) {
    const h = harness(new Map([['hg-ai-consent:v2:website', 'granted']]));
    adapter.createController(h.windowObject, h.documentObject, h.config);
    h.storageEvent({ key: 'unrelated', newValue: null });
    assert.equal(h.windowObject.reloaded, undefined);
    h.storageEvent({ key: 'hg-ai-consent:v2:website', newValue: 'granted' });
    assert.equal(h.windowObject.reloaded, undefined);
    h.storageEvent({ key, newValue: null });
    assert.equal(h.windowObject.reloaded, true);
  }
  const h = harness();
  adapter.createController(h.windowObject, h.documentObject, h.config);
  h.storageEvent({ key: 'hg-ai-consent:v2:website', newValue: null });
  assert.equal(h.windowObject.reloaded, undefined);
});


test('incoming permission synchronizes stale preconsent tabs without loading the vendor', () => {
  for (const value of ['granted', 'dismissed']) {
    const h = harness();
    adapter.createController(h.windowObject, h.documentObject, h.config);
    h.storageEvent({ key: 'hg-ai-consent:v2:website', newValue: value });
    assert.equal(h.windowObject.reloaded, true);
    assert.equal(h.scripts.length, 0);
  }
  const h = harness(new Map([['hg-ai-consent:v2:website', 'dismissed']]));
  adapter.createController(h.windowObject, h.documentObject, h.config);
  h.storageEvent({ key: 'hg-ai-consent:v2:website', newValue: 'dismissed' });
  assert.equal(h.windowObject.reloaded, undefined);
});

test('load and vendor open failures return keyboard focus from hidden agreement to launcher', () => {
  for (const failure of ['bundle', 'open']) {
    const h = harness();
    adapter.createController(h.windowObject, h.documentObject, h.config).activate('', false, h.trigger);
    h.continueConsent();
    assert.equal(h.consent.hidden, true);
    if (failure === 'bundle') h.scripts[0].fire('error');
    else {
      const implementation = h.windowObject.Kapa;
      h.windowObject.Kapa = (method, value) => {
        if (method === 'open') throw new Error('vendor');
        return implementation(method, value);
      };
      h.scripts[0].fire('load');
      h.fireRender();
    }
    assert.equal(h.trigger.focused, true);
    assert.equal(h.trigger.disabled, false);
  }
});


test('page-only permission expires on navigation when storage is wholly blocked', () => {
  const h = harness();
  Object.defineProperty(h.windowObject, 'localStorage', {
    get() { throw new Error('blocked'); },
  });
  adapter.createController(h.windowObject, h.documentObject, h.config).activate('', false, h.trigger);
  h.continueConsent();
  h.scripts[0].fire('load');
  h.fireRender();
  assert.equal(h.storage.size, 0);
  const fresh = harness(h.storage);
  const controller = adapter.createController(fresh.windowObject, fresh.documentObject, fresh.config);
  assert.equal(fresh.consent.hidden, true);
  assert.equal(fresh.scripts.length, 0);
  controller.activate('', false, fresh.trigger);
  assert.equal(fresh.consent.hidden, false);
  assert.equal(fresh.scripts.length, 0);
});
