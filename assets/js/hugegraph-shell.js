/**
 * HugeGraph additions around OINK's shell.
 *
 * This file deliberately does not replace OINK's command palette. It only
 * persists authored tree disclosures through OINK's public API and adds an explicit retry control to the existing search error.
 */
(function (global) {
  'use strict';

  var versionExecutorRegistries = new WeakSet();

  function readConfig(documentObject) {
    var node = documentObject.getElementById('hg-shell-config');
    if (!node) return { version: 'latest', locale: 'en' };
    try {
      return JSON.parse(node.textContent || '{}');
    } catch (_) {
      return { version: 'latest', locale: 'en' };
    }
  }

  function safeStorage(windowObject) {
    try {
      var storage = windowObject.localStorage;
      var probe = '__hg_sidebar_probe__';
      storage.setItem(probe, '1');
      storage.removeItem(probe);
      return storage;
    } catch (_) {
      return null;
    }
  }

  function initTreePersistence(windowObject, documentObject, config) {
    var sidebar = windowObject.OinkSidebar;
    if (!sidebar) return;
    return sidebar.ready.then(function () {
      var buttons = Array.prototype.slice.call(documentObject.querySelectorAll(
        '#td-shell-sidebar [data-td-shell-tree-toggle][aria-controls], ' +
        '[data-td-shell-aside] [data-td-shell-tree-toggle][aria-controls]',
      ));
      if (!buttons.length) return;
      var storage = safeStorage(windowObject);
      var scope = String(config.version || 'latest') + '.' + String(config.locale || 'en');
      var key = 'oink.sidebar.v3.' + scope;
      var valid = new Set(buttons.map(function (button) {
        return button.getAttribute('aria-controls');
      }));
      var remembered = new Set();
      var hasSavedState = false;
      var legacyState = false;
      if (storage) {
        try {
          var stored = storage.getItem(key);
          if (stored === null) {
            stored = storage.getItem('oink.sidebar.v2.' + scope);
            legacyState = stored !== null;
          }
          var parsed = JSON.parse(stored || '[]');
          if (Array.isArray(parsed)) {
            hasSavedState = stored !== null;
            remembered = new Set(parsed.filter(function (id) {
              return typeof id === 'string' && valid.has(id);
            }));
          }
        } catch (_) { /* Keep active-path and docs-home defaults. */ }
      }
      var docsRoot = /(?:^|\/)(?:cn\/)?docs\/?$/.test(windowObject.location.pathname);
      buttons.forEach(function (button) {
        var id = button.getAttribute('aria-controls');
        var isAside = Boolean(button.closest('[data-td-shell-aside]'));
        // v2 stored only the main tree: an absent aside id was not a choice
        // to collapse it. v3 records both, including an explicitly empty set.
        var defaultOpen = isAside
          ? (!hasSavedState || legacyState) && sidebar.getState(id).expanded
          : !hasSavedState && docsRoot && /_nav(?:start|components)-children$/.test(id);
        // OINK preserves the active path and owns DOM, inert and ARIA state.
        sidebar.setExpanded(id, remembered.has(id) || defaultOpen, { source: 'api' });
      });

      function persist() {
        if (!storage) return;
        var expanded = buttons.filter(function (button) {
          var item = button.closest('li');
          var state = sidebar.getState(button.getAttribute('aria-controls'));
          return state && state.expanded &&
            !(item && item.classList.contains('td-active-path'));
        }).map(function (button) { return button.getAttribute('aria-controls'); });
        try { storage.setItem(key, JSON.stringify(expanded)); }
        catch (_) { /* Storage can become unavailable after initialization. */ }
      }
      documentObject.addEventListener('oink:sidebar-disclosure', function (event) {
        if (event.detail && event.detail.source === 'user' && valid.has(event.detail.id)) persist();
      });
      if (!hasSavedState || legacyState) persist();
    });
  }

  function initScrollableTables(documentObject) {
    documentObject.querySelectorAll('[data-td-asset-table-scroll]').forEach(function (region) {
      if (region.dataset.hgTableScrollBound !== undefined) return;
      region.dataset.hgTableScrollBound = '';
      region.addEventListener('keydown', function (event) {
        // Keep native keyboard behavior for links and other descendants in the table.
        if (event.target !== region) return;
        if (region.scrollWidth <= region.clientWidth) return;
        var delta = 0;
        if (event.key === 'ArrowRight') delta = 80;
        else if (event.key === 'ArrowLeft') delta = -80;
        else if (event.key === 'Home') delta = -region.scrollLeft;
        else if (event.key === 'End') delta = region.scrollWidth - region.clientWidth - region.scrollLeft;
        else return;
        event.preventDefault();
        region.scrollBy({ left: delta, behavior: 'smooth' });
      });
    });
  }

  function initSearchRetry(windowObject, documentObject) {
    var root = documentObject.getElementById('td-shell-search');
    if (!root) return;
    var list = root.querySelector('.td-shell-search__list');
    var input = root.querySelector('.td-shell-search__input');
    var status = root.querySelector('[data-td-shell-search-status]');
    if (!list || !input || !status) return;
    var scheduled = false;

    function sync() {
      scheduled = false;
      var existing = list.querySelector('[data-hg-search-retry]');
      var failure = root.dataset.tdTIndexUnavailable || '';
      var failed =
        failure &&
        (status.textContent.trim() === failure ||
          Array.prototype.some.call(
            list.querySelectorAll('.td-shell-search__empty'),
            function (node) {
              return node.textContent.trim() === failure;
            },
          ));
      if (failed && existing) return existing;
      if (existing) existing.remove();
      if (!failed) return null;

      var notice = documentObject.createElement('div');
      notice.className = 'hg-search-retry';
      notice.dataset.hgSearchRetry = '';
      var text = documentObject.createElement('span');
      text.textContent = failure;
      var button = documentObject.createElement('button');
      button.type = 'button';
      button.className = 'btn btn-sm btn-outline-primary';
      button.textContent =
        documentObject.documentElement.lang === 'cn' ||
        documentObject.documentElement.lang.indexOf('zh') === 0
          ? '重试'
          : 'Retry';
      button.addEventListener('click', function () {
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.focus();
      });
      notice.appendChild(text);
      notice.appendChild(button);
      list.appendChild(notice);
      return notice;
    }

    function schedule() {
      if (scheduled) return;
      scheduled = true;
      global.requestAnimationFrame(sync);
    }
    new MutationObserver(schedule).observe(list, {
      childList: true,
      subtree: true,
      characterData: true,
    });
    new MutationObserver(schedule).observe(status, {
      childList: true,
      subtree: true,
      characterData: true,
    });
    schedule();
  }

  function versionTarget(option, locationObject) {
    if (!option || !option.url) return '';
    try {
      var target = new URL(option.url, locationObject.href);
      if (target.protocol !== 'http:' && target.protocol !== 'https:')
        return '';
      if (option.equivalent === true && option.fallback !== true) {
        target.search = locationObject.search || '';
        target.hash = locationObject.hash || '';
      }
      return target.href;
    } catch (_) {
      return '';
    }
  }

  function boolData(value) {
    return value === true || value === 'true';
  }

  function initVersionSwitching(windowObject, documentObject) {
    Array.prototype.forEach.call(
      documentObject.querySelectorAll('a[data-hg-version-id]'),
      function (anchor) {
        var target = versionTarget(
          {
            url: anchor.getAttribute('href'),
            equivalent: boolData(anchor.dataset.hgVersionEquivalent),
            fallback: boolData(anchor.dataset.hgVersionFallback),
          },
          windowObject.location,
        );
        if (target) anchor.setAttribute('href', target);
      },
    );

    var registry = windowObject.OinkActions;
    if (
      !registry ||
      typeof registry.registerExecutor !== 'function' ||
      versionExecutorRegistries.has(registry)
    ) {
      return;
    }
    registry.registerExecutor('switch_version', function (context) {
      var target = versionTarget(
        context && context.value,
        windowObject.location,
      );
      if (target) windowObject.location.assign(target);
      return { action: 'switch_version', url: target };
    });
    versionExecutorRegistries.add(registry);
  }

  function consumeVersionFallback(windowObject, documentObject, config) {
    var locationObject = windowObject.location;
    if (locationObject.hash !== '#hg-version-fallback' || !config.docsRoot)
      return null;
    var docsPath;
    try {
      docsPath = new URL(config.docsRoot, locationObject.href).pathname;
    } catch (_) {
      return null;
    }
    if (locationObject.pathname !== docsPath) return null;

    windowObject.history.replaceState(
      windowObject.history.state,
      '',
      locationObject.pathname + locationObject.search,
    );
    var notice = documentObject.createElement('div');
    ['alert', 'alert-info', 'hg-version-fallback', 'd-print-none'].forEach(
      function (name) {
        notice.classList.add(name);
      },
    );
    notice.dataset.hgVersionFallbackNotice = '';
    notice.setAttribute('role', 'status');
    notice.setAttribute('aria-live', 'polite');
    notice.setAttribute('aria-atomic', 'true');
    notice.textContent = config.versionFallbackMessage || '';
    var container =
      (documentObject.querySelector && documentObject.querySelector('main')) ||
      documentObject.body;
    if (container) container.prepend(notice);
    return notice;
  }

  function init(windowObject, documentObject) {
    var config = readConfig(documentObject);
    consumeVersionFallback(windowObject, documentObject, config);
    initVersionSwitching(windowObject, documentObject);
    initTreePersistence(windowObject, documentObject, config);
    initScrollableTables(documentObject);
    initSearchRetry(windowObject, documentObject);
  }

  var api = {
    init: init,
    readConfig: readConfig,
    safeStorage: safeStorage,
    initTreePersistence: initTreePersistence,
    versionTarget: versionTarget,
    initVersionSwitching: initVersionSwitching,
    consumeVersionFallback: consumeVersionFallback,
  };
  global.HugeGraphShell = api;
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
