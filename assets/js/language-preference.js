/** HugeGraph language defaults; OINK still owns language menus and navigation. */
(function () {
  'use strict';

  var node = document.getElementById('hg-language-config');
  if (!node) return;
  var config = JSON.parse(node.textContent);
  var key = 'hg-language';

  function language(value) {
    if (/^zh(?:[-_]|$)/i.test(value)) return 'cn';
    if (/^en(?:[-_]|$)/i.test(value)) return 'en';
    return '';
  }

  function remember(value) {
    if (value !== 'en' && value !== 'cn') return;
    try { localStorage.setItem(key, value); }
    catch (_) { /* Language links still work when storage is blocked. */ }
  }

  function targetForURL(value) {
    var url;
    try { url = new URL(value, location.href); }
    catch (_) { return null; }
    if (url.origin !== location.origin) return null;
    return config.targets.find(function (target) {
      return new URL(target.url, location.href).pathname === url.pathname;
    });
  }

  // Only the unqualified latest homepage chooses a default. Explicit language
  // URLs, document links and archived versions keep their requested language.
  var internalVisit = false;
  try { internalVisit = new URL(document.referrer).origin === location.origin; }
  catch (_) { /* A direct visit has no referrer. */ }
  if (config.auto && !internalVisit) {
    var preferred;
    try { preferred = localStorage.getItem(key); }
    catch (_) { /* Use browser languages without storing the detected default. */ }
    if (preferred !== 'en' && preferred !== 'cn') {
      var languages = navigator.languages || [navigator.language];
      preferred = languages.map(language).find(Boolean) || 'en';
    }
    var target = config.targets.find(function (item) {
      return language(item.code) === preferred;
    });
    if (target && preferred !== config.locale) {
      var destination = new URL(target.url, location.href);
      destination.search = location.search;
      destination.hash = location.hash;
      location.replace(destination.href);
      return;
    }
  }

  function init() {
    function rememberLink(event) {
      if (!event.target || typeof event.target.closest !== 'function') return;
      var anchor = event.target.closest('.td-language-selector a[hreflang]');
      if (anchor) remember(language(anchor.getAttribute('hreflang')));
    }
    document.addEventListener('click', rememberLink);
    document.addEventListener('auxclick', rememberLink);

    var actions = window.OinkActions;
    if (actions && actions.get('switch_language')) {
      actions.registerExecutor('switch_language', function (context) {
        var url = actions.resolveUrl('switch_language', context && context.value);
        var target = url && targetForURL(url);
        if (!target) throw new Error('Unsupported language target');
        remember(language(target.code));
        location.assign(url);
        return { action: 'switch_language', url: url };
      });
    }

    // Observe OINK's native l/y shortcut navigation without duplicating its
    // keyboard controller. Back/forward and same-language links are not choices.
    if (window.navigation) {
      window.navigation.addEventListener('navigate', function (event) {
        if (event.navigationType === 'traverse' || event.navigationType === 'reload') return;
        var target = targetForURL(event.destination.url);
        var selected = target && language(target.code);
        if (selected && selected !== config.locale) remember(selected);
      });
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
