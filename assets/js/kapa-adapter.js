/**
 * Click-gated Kapa adapter for OINK.
 *
 * The third-party bundle URL and privacy posture are fixed here. The page
 * supplies only reviewed public identifiers and localized labels.
 */
(function (global) {
  'use strict';

  var BUNDLE_URL = 'https://widget.kapa.ai/kapa-widget.bundle.js';
  var TIMEOUT_MS = 5000;

  function trimmedQuery(value) {
    return String(value || '').trim();
  }

  function mixWithWhite(color, percentage) {
    var match = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(color);
    if (!match) throw new Error('Kapa theme color must be a six-digit hexadecimal color');
    var weight = percentage / 100;
    return '#' + match.slice(1).map(function (channel) {
      var mixed = Math.round(parseInt(channel, 16) * (1 - weight) + 255 * weight);
      return mixed.toString(16).padStart(2, '0');
    }).join('');
  }

  function readConfig(documentObject) {
    var node = documentObject.getElementById('hg-ai-config');
    if (!node) return null;
    try {
      var config = JSON.parse(node.textContent || '{}');
      return config.websiteId && config.sourceGroupId ? config : null;
    } catch (_) {
      return null;
    }
  }

  function invokeKapa(windowObject, method, value) {
    var api = windowObject.Kapa;
    if (typeof api === 'function') return api(method, value);
    if (api && typeof api[method] === 'function') return api[method](value);
    throw new Error('Kapa API is unavailable');
  }

  function preinitialize(windowObject, force) {
    if (!force && windowObject.Kapa) return windowObject.Kapa;
    if (
      force &&
      windowObject.Kapa &&
      windowObject.Kapa.hgKapaPreinitialized &&
      Array.isArray(windowObject.Kapa.q)
    ) {
      windowObject.Kapa.q.length = 0;
    }
    var queue = function () {
      queue.c(arguments);
    };
    queue.q = [];
    queue.hgKapaPreinitialized = true;
    queue.c = function (args) {
      queue.q.push(args);
    };
    windowObject.Kapa = queue;
    return queue;
  }

  function scriptAttributes(config) {
    return {
      'data-website-id': config.websiteId,
      'data-source-group-ids-include': config.sourceGroupId,
      'data-language': config.locale,
      'data-project-name': 'Apache HugeGraph',
      'data-project-logo': '/img/logo.svg',
      'data-project-color': config.themeColor,
      'data-project-color-dark': mixWithWhite(config.themeColor, 48),
      'data-surface-color': '#ffffff',
      'data-surface-elevated-color': '#f6f4fb',
      'data-surface-hover-color': '#eeeafd',
      'data-text-color': '#24212d',
      'data-text-muted-color': '#686275',
      'data-border-color': '#d9d4e4',
      'data-anchor-color': config.themeColor,
      'data-surface-color-dark': '#17151d',
      'data-surface-elevated-color-dark': '#221f2b',
      'data-surface-hover-color-dark': '#302b3d',
      'data-text-color-dark': '#f0edf7',
      'data-text-muted-color-dark': '#b6afc2',
      'data-border-color-dark': '#494254',
      'data-anchor-color-dark': mixWithWhite(config.themeColor, 60),
      'data-color-scheme-selector': "[data-bs-theme='dark']",
      'data-font-family':
        '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif',
      'data-modal-content-border-radius': '12px',
      'data-modal-z-index': '1050',
      'data-modal-content-border': '1px solid #d9d4e4',
      'data-modal-content-border-dark': '1px solid #494254',
      'data-launcher-button-hidden': 'true',
      'data-render-on-load': 'false',
      'data-search-mode-enabled': 'false',
      'data-modal-open-on-command-k': 'false',
      'data-consent-required': 'false',
      'data-user-analytics-cookie-enabled': 'false',
      'data-user-analytics-fingerprint-enabled': 'false',
      'data-exit-feedback-enabled': 'false',
      'data-user-satisfaction-feedback-enabled': 'false',
      'data-bot-protection-mechanism': 'hcaptcha',
    };
  }

  function createController(windowObject, documentObject, config) {
    var state = 'idle';
    var consented = false;
    var pending = null;
    var consent = documentObject.querySelector('[data-hg-ai-consent]');
    var attempt = 0;
    var timer = 0;
    var lastTrigger = null;
    var activeScript = null;
    var activeQueue = null;
    var operation = null;
    var status = documentObject.querySelector('[data-hg-ai-status]');

    function renderState(next, message) {
      state = next;
      documentObject.querySelectorAll('[data-hg-ask-ai]').forEach(function (button) {
        button.dataset.hgAiState = next;
        button.disabled = next === 'loading';
        if (next === 'loading') button.setAttribute('aria-busy', 'true');
        else button.removeAttribute('aria-busy');
        if (message) button.setAttribute('title', message);
        else button.removeAttribute('title');
      });
      if (status) {
        status.textContent = message || '';
        status.classList.toggle('visually-hidden', !message);
      }
    }

    function settle(error) {
      if (!operation) return;
      var current = operation;
      operation = null;
      current.signal.removeEventListener('abort', current.abort);
      if (error) current.reject(error);
      else current.resolve();
    }

    function openWidget(query, submit) {
      try {
        invokeKapa(windowObject, 'setSourceGroupIDs', [config.sourceGroupId]);
        invokeKapa(windowObject, 'open', {
          mode: 'ai',
          query: query,
          submit: submit,
        });
        settle();
      } catch (_) {
        discardAttempt(attempt);
        renderState('error', config.labels.error);
        settle(new Error(config.labels.error));
      }
    }

    function discardAttempt(serial) {
      if (
        activeScript &&
        activeScript.dataset.hgKapaAttempt === String(serial)
      ) {
        activeScript.remove();
        activeScript = null;
      }
      if (
        activeQueue &&
        activeQueue.hgKapaPreinitialized &&
        Array.isArray(activeQueue.q)
      ) {
        activeQueue.q.length = 0;
        if (windowObject.Kapa === activeQueue) {
          try {
            delete windowObject.Kapa;
          } catch (_) {
            windowObject.Kapa = undefined;
          }
        }
      }
      activeQueue = null;
    }

    function fail(serial) {
      if (serial !== attempt || state !== 'loading') return;
      windowObject.clearTimeout(timer);
      discardAttempt(serial);
      renderState('error', config.labels.error);
      settle(new Error(config.labels.error));
    }

    function ready(serial, query, submit) {
      if (serial !== attempt || state !== 'loading') return;
      windowObject.clearTimeout(timer);
      renderState('ready', '');
      openWidget(query, submit);
    }

    function ensureScript(serial, query, submit, retrying) {
      var loaded = false;
      var rendered = false;
      activeQueue = preinitialize(windowObject, retrying);
      if (retrying) {
        invokeKapa(windowObject, 'onModalClose', restoreFocus);
      }
      var script = documentObject.createElement('script');
      activeScript = script;
      script.async = true;
      script.src =
        BUNDLE_URL + (retrying ? '?hg-retry=' + encodeURIComponent(serial) : '');
      script.dataset.hgKapaWidget = '';
      script.dataset.hgKapaAttempt = String(serial);
      var attrs = scriptAttributes(config);
      Object.keys(attrs).forEach(function (name) {
        script.setAttribute(name, attrs[name]);
      });
      function finish() {
        if (loaded && rendered) ready(serial, query, submit);
      }
      script.addEventListener('load', function () {
        loaded = true;
        finish();
      }, { once: true });
      script.addEventListener('error', function () {
        fail(serial);
      }, { once: true });
      try {
        invokeKapa(windowObject, 'render', {
          onRender: function () {
            rendered = true;
            finish();
          },
        });
      } catch (_) {
        fail(serial);
        return;
      }
      documentObject.head.appendChild(script);
    }

    function load(query, submit) {
      query = trimmedQuery(query);
      if (state === 'loading') return;
      if (state === 'ready') {
        openWidget(query, Boolean(submit && query));
        return;
      }
      var retrying = attempt > 0;
      var serial = ++attempt;
      renderState('loading', '');
      timer = windowObject.setTimeout(function () {
        fail(serial);
      }, TIMEOUT_MS);
      ensureScript(serial, query, Boolean(submit && query), retrying);
    }

    function cancelConsent() {
      pending = null;
      renderState('idle', '');
      if (consent && consent.open) consent.close();
      restoreFocus();
      settle();
    }

    function activate(query, submit, trigger, context) {
      if (state === 'loading' || state === 'consent') return;
      if (context && context.signal.aborted) return Promise.resolve();
      lastTrigger = trigger || documentObject.activeElement;
      var completion;
      if (context) {
        completion = new Promise(function (resolve, reject) {
          operation = { signal: context.signal, resolve: resolve, reject: reject };
          operation.abort = function () {
            windowObject.clearTimeout(timer);
            if (state === 'loading') discardAttempt(attempt);
            attempt += 1;
            pending = null;
            if (consent && consent.open) consent.close();
            renderState('idle', '');
            settle();
          };
          context.signal.addEventListener('abort', operation.abort, { once: true });
        });
        // Transfer focus before opening a dialog; OINK keeps cancellation alive
        // until this promise settles, including when search is opened again.
        if (!context.handoff()) {
          settle();
          return completion;
        }
      }
      if (consented) {
        load(query, submit);
        return completion;
      }
      // Fail closed if the local consent panel is unavailable.
      if (!consent || typeof consent.showModal !== 'function') {
        renderState('error', config.labels.error);
        settle(new Error(config.labels.error));
        return completion;
      }
      pending = { query: trimmedQuery(query), submit: submit };
      renderState('consent', '');
      consent.showModal();
      return completion;
    }

    if (consent) {
      // Keep the underlying search palette from consuming modal keyboard events.
      consent.addEventListener('keydown', function (event) {
        event.stopPropagation();
        if (event.key === 'Escape') {
          event.preventDefault();
          cancelConsent();
        }
      });
      consent.querySelector('[data-hg-ai-continue]').addEventListener('click', function () {
        if (!pending) return;
        var request = pending;
        pending = null;
        consented = true;
        consent.close();
        load(request.query, request.submit);
      });
      consent.querySelector('[data-hg-ai-cancel]').addEventListener('click', cancelConsent);
      consent.addEventListener('cancel', function (event) {
        event.preventDefault();
        cancelConsent();
      });
    }

    function restoreFocus() {
      if (lastTrigger && typeof lastTrigger.focus === 'function') {
        lastTrigger.focus();
      }
    }

    activeQueue = preinitialize(windowObject);
    invokeKapa(windowObject, 'onModalClose', restoreFocus);

    return {
      activate: activate,
      getState: function () { return state; },
    };
  }

  function init(windowObject, documentObject) {
    var config = readConfig(documentObject);
    if (!config) return null;
    var controller = createController(windowObject, documentObject, config);
    documentObject.querySelectorAll('[data-hg-ask-ai]').forEach(function (button) {
      if (button.dataset.hgAiBound !== undefined) return;
      button.dataset.hgAiBound = '';
      button.addEventListener('click', function () {
        controller.activate('', false, button);
      });
    });

    var palette = windowObject.OinkCommandPalette;
    if (palette && typeof palette.registerSearchTail === 'function') {
      palette.registerSearchTail({
        id: 'hugegraph-ai',
        rows: function (context) {
          return [{
            id: 'ask',
            title: config.labels.ask + ': “' + context.query + '”',
            description: config.historical ? config.labels.latest + '.' : '',
            icon: 'fa-solid fa-wand-magic-sparkles',
          }];
        },
        activate: function (_, context) {
          // OINK debounces row rendering; Enter can activate an older row.
          var input = documentObject.querySelector('#td-shell-search .td-shell-search__input');
          var query = trimmedQuery(input ? input.value : context.query);
          if (query !== context.query) {
            // Refresh OINK's cancellation token as well as the submitted text;
            // otherwise its pending render aborts a handoff for the old query.
            var instance = palette.instance;
            instance.render(query);
            var rows = instance.rows();
            var index = rows.findIndex(function (row) {
              return row.type === 'extension' && row.owner.id === 'hugegraph-ai';
            });
            if (index >= 0) instance.activate(index);
            return;
          }
          if (!query || query.charAt(0) === '>') return;
          // Search options are ephemeral and become hidden on handoff.
          var trigger = documentObject.querySelector('.hg-ask-ai-launcher');
          return controller.activate(query, true, trigger, context);
        },
      });
    }
    return controller;
  }

  var api = {
    BUNDLE_URL: BUNDLE_URL,
    TIMEOUT_MS: TIMEOUT_MS,
    createController: createController,
    init: init,
    invokeKapa: invokeKapa,
    preinitialize: preinitialize,
    readConfig: readConfig,
    scriptAttributes: scriptAttributes,
    trimmedQuery: trimmedQuery,
  };
  global.HugeGraphKapa = api;
  if (typeof module === 'object' && module.exports) module.exports = api;

  if (global.document) {
    if (global.document.readyState === 'loading') {
      global.document.addEventListener('DOMContentLoaded', function () {
        init(global, global.document);
      });
    } else {
      init(global, global.document);
    }
  }
})(typeof window === 'object' ? window : globalThis);
