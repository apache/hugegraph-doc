/**
 * HugeGraph additions around OINK's shell.
 *
 * This file deliberately does not replace OINK's command palette. It only
 * persists authored tree disclosures, makes a collapsed/dismissed sidebar
 * inert, and adds an explicit retry control to the existing search error.
 */
(function (global) {
  'use strict';

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

  function setTreeExpanded(button, expanded, documentObject) {
    var target = documentObject.getElementById(
      button.getAttribute('aria-controls'),
    );
    if (!target) return;
    button.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    target.classList.toggle('td-is-open', expanded);
    var label = expanded
      ? button.dataset.tdLabelCollapse
      : button.dataset.tdLabelExpand;
    if (label) button.setAttribute('aria-label', label);
  }

  function initTreePersistence(windowObject, documentObject, config) {
    var buttons = Array.prototype.slice.call(
      documentObject.querySelectorAll('[data-td-shell-tree-toggle][aria-controls]'),
    );
    if (!buttons.length) return;
    var storage = safeStorage(windowObject);
    var key =
      'oink.sidebar.v1.' +
      String(config.version || 'latest') +
      '.' +
      String(config.locale || 'en');
    var valid = new Set(
      buttons.map(function (button) {
        return button.getAttribute('aria-controls');
      }),
    );
    var saved = [];
    if (storage) {
      try {
        var parsed = JSON.parse(storage.getItem(key) || '[]');
        if (Array.isArray(parsed)) {
          saved = parsed.filter(function (id) {
            return typeof id === 'string' && valid.has(id);
          });
        }
      } catch (_) {
        saved = [];
      }
    }
    var remembered = new Set(saved);

    buttons.forEach(function (button) {
      var item = button.closest('li');
      var activePath = item && item.classList.contains('td-active-path');
      setTreeExpanded(
        button,
        Boolean(activePath || remembered.has(button.getAttribute('aria-controls'))),
        documentObject,
      );
      button.addEventListener('click', function () {
        global.queueMicrotask(function () {
          if (!storage) return;
          var expanded = buttons
            .filter(function (candidate) {
              var candidateItem = candidate.closest('li');
              return (
                candidate.getAttribute('aria-expanded') === 'true' &&
                !(candidateItem &&
                  candidateItem.classList.contains('td-active-path'))
              );
            })
            .map(function (candidate) {
              return candidate.getAttribute('aria-controls');
            });
          try {
            storage.setItem(key, JSON.stringify(expanded));
          } catch (_) {
            /* Active-path expansion remains the storage-free fallback. */
          }
        });
      });
    });

    // Rewriting the filtered set removes stale node IDs after navigation
    // changes without retaining a second schema/version marker.
    if (storage) {
      try {
        storage.setItem(key, JSON.stringify(saved));
      } catch (_) {
        /* Ignore storage becoming unavailable after the probe. */
      }
    }
  }

  function initSidebarIsolation(windowObject, documentObject) {
    var html = documentObject.documentElement;
    var sidebar = documentObject.getElementById('td-shell-sidebar');
    if (!sidebar) return;
    var restore = documentObject.querySelector('.hg-sidebar-restore');
    var desktop = windowObject.matchMedia('(min-width: 768px)');

    function sync() {
      var collapsed =
        html.getAttribute('data-td-shell-sidebar') === 'collapsed';
      var drawerOpen =
        html.getAttribute('data-td-shell-drawer') === 'open';
      var isolated = desktop.matches ? collapsed : !drawerOpen;
      sidebar.inert = isolated;
      if (isolated) sidebar.setAttribute('aria-hidden', 'true');
      else sidebar.removeAttribute('aria-hidden');
      if (
        isolated &&
        sidebar.contains(documentObject.activeElement) &&
        restore &&
        restore.offsetParent !== null
      ) {
        restore.focus();
      }
    }

    new MutationObserver(sync).observe(html, {
      attributes: true,
      attributeFilter: ['data-td-shell-sidebar', 'data-td-shell-drawer'],
    });
    desktop.addEventListener('change', sync);
    documentObject
      .querySelectorAll('[data-td-shell-sidebar-toggle], [data-td-shell-drawer-close]')
      .forEach(function (button) {
        button.addEventListener('click', function () {
          global.queueMicrotask(sync);
        });
      });
    sync();
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
      if (existing) existing.remove();
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
      if (!failed) return;

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

  function init(windowObject, documentObject) {
    var config = readConfig(documentObject);
    initTreePersistence(windowObject, documentObject, config);
    initSidebarIsolation(windowObject, documentObject);
    initSearchRetry(windowObject, documentObject);
  }

  var api = {
    init: init,
    readConfig: readConfig,
    safeStorage: safeStorage,
    setTreeExpanded: setTreeExpanded,
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
