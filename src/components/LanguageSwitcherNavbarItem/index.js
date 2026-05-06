import React from 'react';
import {useLocation} from '@docusaurus/router';
import DropdownNavbarItem from '@theme/NavbarItem/DropdownNavbarItem';

const cnPrefixes = ['/cn/docs/', '/cn/blog/', '/cn/community/', '/cn/team/', '/cn/users/', '/cn/download/'];
const enPrefixes = ['/docs/', '/blog/', '/community/', '/team/', '/users/', '/download/'];
const cnToEnFallbacks = new Map([
  ['/cn/docs/changelog/hugegraph-0.12.0-release-notes/', '/docs/changelog/'],
]);
const enToCnFallbacks = new Map([
  ['/community/maturity/', '/cn/community/'],
]);

function appendSuffix(pathname, suffix) {
  return `${pathname}${suffix}`;
}

function matchesPrefix(pathname, prefix) {
  return pathname === prefix.slice(0, -1) || pathname.startsWith(prefix);
}

function normalizeLookupPath(pathname) {
  return pathname.endsWith('/') ? pathname : `${pathname}/`;
}

function isNotFoundPath(pathname) {
  return pathname === '/404' || pathname === '/404.html' || pathname === '/404/';
}

function toEnglish(pathname) {
  if (isNotFoundPath(pathname)) {
    return '/';
  }

  if (pathname === '/cn' || pathname === '/cn/') {
    return '/';
  }

  const versionedChangelogFallback = pathname.match(
    /^\/cn\/docs\/(?:(next)\/)?changelog\/hugegraph-0\.12\.0-release-notes\/?$/,
  );
  if (versionedChangelogFallback) {
    const versionPrefix = versionedChangelogFallback[1] ? `${versionedChangelogFallback[1]}/` : '';
    return `/docs/${versionPrefix}changelog/`;
  }

  const fallback = cnToEnFallbacks.get(normalizeLookupPath(pathname));
  if (fallback) {
    return fallback;
  }

  const matchedPrefix = cnPrefixes.find((prefix) => matchesPrefix(pathname, prefix));
  if (matchedPrefix) {
    const englishPrefix = matchedPrefix.replace('/cn', '');
    if (pathname === matchedPrefix.slice(0, -1)) {
      return englishPrefix.slice(0, -1);
    }
    return pathname.replace(matchedPrefix, englishPrefix);
  }

  return pathname.startsWith('/cn/') ? pathname.replace(/^\/cn/, '') : pathname;
}

function toChinese(pathname) {
  if (isNotFoundPath(pathname)) {
    return '/cn/';
  }

  if (pathname === '/') {
    return '/cn/';
  }

  if (pathname === '/cn' || pathname.startsWith('/cn/')) {
    return pathname;
  }

  const fallback = enToCnFallbacks.get(normalizeLookupPath(pathname));
  if (fallback) {
    return fallback;
  }

  const matchedPrefix = enPrefixes.find((prefix) => matchesPrefix(pathname, prefix));
  if (matchedPrefix) {
    return `/cn${pathname}`;
  }

  return '/cn/';
}

export default function LanguageSwitcherNavbarItem(props) {
  const location = useLocation();
  const suffix = `${location.search}${location.hash}`;
  const isChinese = location.pathname === '/cn/' || location.pathname.startsWith('/cn/');

  return (
    <DropdownNavbarItem
      {...props}
      label={isChinese ? '中文' : 'English'}
      items={[
        {
          label: 'English',
          to: appendSuffix(toEnglish(location.pathname), suffix),
        },
        {
          label: '中文',
          to: appendSuffix(toChinese(location.pathname), suffix),
        },
      ]}
    />
  );
}
