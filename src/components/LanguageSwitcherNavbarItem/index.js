import React from 'react';
import {useLocation} from '@docusaurus/router';
import {useAllDocsData} from '@docusaurus/plugin-content-docs/client';
import DropdownNavbarItem from '@theme/NavbarItem/DropdownNavbarItem';

const cnPrefixes = ['/cn/docs/', '/cn/blog/', '/cn/community/', '/cn/team/', '/cn/users/', '/cn/download/'];
const enPrefixes = ['/docs/', '/blog/', '/community/', '/team/', '/users/', '/download/'];
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

function normalizeRoutePath(pathname) {
  const normalized = pathname.replace(/\/+$/, '');
  return normalized || '/';
}

function isNotFoundPath(pathname) {
  return pathname === '/404' || pathname === '/404.html' || pathname === '/404/';
}

function isDocsPath(pathname) {
  return pathname === '/docs' || pathname.startsWith('/docs/') || pathname === '/cn/docs' || pathname.startsWith('/cn/docs/');
}

function collectDocsPaths(allDocsData) {
  const paths = new Set();
  for (const pluginData of Object.values(allDocsData)) {
    for (const version of pluginData.versions || []) {
      paths.add(normalizeRoutePath(version.path));
      for (const doc of version.docs || []) {
        paths.add(normalizeRoutePath(doc.path));
      }
    }
  }
  return paths;
}

function docsRootFor(pathname) {
  const match = pathname.match(/^\/(cn\/)?docs(\/(?:next|docusaurus-[^/]+))?/);
  if (!match) {
    return pathname.startsWith('/cn/') ? '/cn/docs/' : '/docs/';
  }
  return `/${match[1] || ''}docs${match[2] || ''}/`;
}

function fallbackForMissingDocsPath(pathname) {
  const docsRoot = docsRootFor(pathname);
  if (pathname.includes('/changelog/')) {
    return `${docsRoot}changelog/`;
  }
  return docsRoot;
}

function resolveDocsTarget(pathname, docsPaths) {
  if (!isDocsPath(pathname) || docsPaths.has(normalizeRoutePath(pathname))) {
    return pathname;
  }

  const fallback = fallbackForMissingDocsPath(pathname);
  return docsPaths.has(normalizeRoutePath(fallback)) ? fallback : docsRootFor(pathname);
}

function toEnglish(pathname) {
  if (isNotFoundPath(pathname)) {
    return '/';
  }

  if (pathname === '/cn' || pathname === '/cn/') {
    return '/';
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
  const allDocsData = useAllDocsData();
  const docsPaths = React.useMemo(() => collectDocsPaths(allDocsData), [allDocsData]);
  const suffix = `${location.search}${location.hash}`;
  const isChinese = location.pathname === '/cn/' || location.pathname.startsWith('/cn/');
  const englishPath = resolveDocsTarget(toEnglish(location.pathname), docsPaths);
  const chinesePath = resolveDocsTarget(toChinese(location.pathname), docsPaths);

  return (
    <DropdownNavbarItem
      {...props}
      label={isChinese ? '中文' : 'English'}
      items={[
        {
          label: 'English',
          to: appendSuffix(englishPath, suffix),
        },
        {
          label: '中文',
          to: appendSuffix(chinesePath, suffix),
        },
      ]}
    />
  );
}
