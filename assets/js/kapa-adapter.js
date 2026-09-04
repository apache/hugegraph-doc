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
      'data-project-color': config.themeColor,
      'data-project-color-dark': '#9f83ff',
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
      'data-anchor-color-dark': '#b6a3ff',
      'data-color-scheme-selector': "[data-bs-theme='dark']",
      'data-font-family':
        '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif',
      'data-modal-content-border-radius': '12px',
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
    var attempt = 0;
    var timer = 0;
    var lastTrigger = null;
    var activeScript = null;
    var activeQueue = null;
    var status = documentObject.querySelector('[data-hg-ai-status]');

    function renderState(next, message) {
      state = next;
      documentObject.querySelectorAll('[data-hg-ask-ai]').forEach(function (button) {
        button.dataset.hgAiState = next;
        button.disabled = next === 'loading';
        if (next === 'loading') button.setAttribute('aria-busy', 'true');
        else button.removeAttribute('aria-busy');
        if (message) button.title = message;
      });
      if (status) {
        status.textContent = message || '';
        status.classList.toggle('visually-hidden', !message);
      }
    }

    function openWidget(query, submit) {
      invokeKapa(windowObject, 'setSourceGroupIDs', [config.sourceGroupId]);
      invokeKapa(windowObject, 'open', {
        mode: 'ai',
        query: query,
        submit: submit,
      });
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

    function activate(query, submit, trigger) {
      query = trimmedQuery(query);
      lastTrigger = trigger || documentObject.activeElement;
      if (state === 'loading') return;
      if (state === 'ready') {
        openWidget(query, Boolean(submit && query));
        return;
      }
      var retrying = state === 'error';
      var serial = ++attempt;
      renderState('loading', '');
      timer = windowObject.setTimeout(function () {
        fail(serial);
      }, TIMEOUT_MS);
      ensureScript(serial, query, Boolean(submit && query), retrying);
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
    var root = documentObject.getElementById('td-shell-search');
    var input = root && root.querySelector('.td-shell-search__input');
    var list = root && root.querySelector('.td-shell-search__list');
    var syncing = false;

    function bind(button) {
      if (button.dataset.hgAiBound !== undefined) return;
      button.dataset.hgAiBound = '';
      button.addEventListener('click', function () {
        controller.activate(
          button.dataset.hgAiQuery || '',
          button.dataset.hgAiSubmit === 'true',
          button,
        );
      });
    }
    documentObject.querySelectorAll('[data-hg-ask-ai]').forEach(bind);

    function syncTail() {
      syncing = false;
      if (!root || !input || !list || root.hidden) return;
      var old = list.querySelector('[data-hg-ai-search-tail]');
      var query = trimmedQuery(input.value);
      if (!query || query.charAt(0) === '>') {
        if (old) old.remove();
        return;
      }
      var choiceLabel = root.dataset.tdTChoice || '';
      if (
        choiceLabel &&
        Array.prototype.some.call(
          list.querySelectorAll('.td-shell-search__group-label'),
          function (label) { return label.textContent.trim() === choiceLabel; },
        )
      ) {
        if (old) old.remove();
        return;
      }
      var loading = root.dataset.tdTLoading || '';
      if (
        loading &&
        Array.prototype.some.call(
          list.querySelectorAll('.td-shell-search__empty'),
          function (node) { return node.textContent.trim() === loading; },
        )
      ) {
        if (old) old.remove();
        return;
      }
      var oldButton = old && old.querySelector('[data-hg-ask-ai]');
      if (oldButton && oldButton.dataset.hgAiQuery === query) return;
      if (old) old.remove();

      var group = documentObject.createElement('div');
      group.className = 'td-shell-search__group hg-ai-search-tail';
      group.dataset.hgAiSearchTail = '';
      group.setAttribute('role', 'group');
      var label = documentObject.createElement('div');
      label.className = 'td-shell-search__group-label';
      label.textContent = config.labels.ask;
      var row = documentObject.createElement('button');
      row.type = 'button';
      row.className = 'td-shell-search__item hg-ai-search-tail__button';
      row.dataset.hgAskAi = '';
      row.dataset.hgAiQuery = query;
      row.dataset.hgAiSubmit = 'true';
      var icon = documentObject.createElement('i');
      icon.className =
        'fa-solid fa-wand-magic-sparkles td-shell-search__item-icon';
      icon.setAttribute('aria-hidden', 'true');
      var meta = documentObject.createElement('span');
      meta.className = 'td-shell-search__item-meta';
      var title = documentObject.createElement('span');
      title.className = 'td-shell-search__item-title';
      title.textContent = config.labels.ask + ': “' + query + '”';
      var detail = documentObject.createElement('span');
      detail.className = 'td-shell-search__item-ref';
      detail.textContent =
        config.labels.description +
        (config.historical ? ' ' + config.labels.latest + '.' : '');
      meta.appendChild(title);
      meta.appendChild(detail);
      row.appendChild(icon);
      row.appendChild(meta);
      group.appendChild(label);
      group.appendChild(row);
      list.appendChild(group);
      bind(row);
    }

    if (list) {
      new MutationObserver(function () {
        if (syncing) return;
        syncing = true;
        windowObject.requestAnimationFrame(syncTail);
      }).observe(list, { childList: true, subtree: true });
      input.addEventListener('input', syncTail);
      syncTail();
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
