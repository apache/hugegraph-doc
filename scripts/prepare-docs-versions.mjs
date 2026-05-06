#!/usr/bin/env node
import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';

const require = createRequire(import.meta.url);
const {buildSidebar} = require('../src/sidebars/buildSidebars');

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const metadataPath = path.join(repoRoot, 'src/data/versions.json');
const versions = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));

const generatedPaths = [
  'versioned_docs',
  'versioned_sidebars',
  'versions.json',
  'docs-cn_versioned_docs',
  'docs-cn_versioned_sidebars',
  'docs-cn_versions.json',
];

const localeTargets = {
  en: {
    docsDir: 'versioned_docs',
    sidebarsDir: 'versioned_sidebars',
    versionsFile: 'versions.json',
    sourcePath: 'content/en/docs',
  },
  cn: {
    docsDir: 'docs-cn_versioned_docs',
    sidebarsDir: 'docs-cn_versioned_sidebars',
    versionsFile: 'docs-cn_versions.json',
    sourcePath: 'content/cn/docs',
  },
};

const legacyRouteAliases = new Map([['clients/hugegraph-api', 'clients/restful-api']]);

function log(message) {
  console.log(`[docs:versions] ${message}`);
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: repoRoot,
    encoding: options.encoding ?? 'utf8',
    input: options.input,
    maxBuffer: 1024 * 1024 * 200,
    stdio: options.stdio,
  });
  if (result.status !== 0) {
    const output = [result.stdout, result.stderr].filter(Boolean).join('\n').trim();
    throw new Error(`${command} ${args.join(' ')} failed${output ? `:\n${output}` : ''}`);
  }
  return result;
}

function gitRefExists(ref) {
  const result = spawnSync('git', ['cat-file', '-e', `${ref}^{tree}`], {
    cwd: repoRoot,
    stdio: 'ignore',
  });
  return result.status === 0;
}

function resolveGitRef(ref) {
  if (gitRefExists(ref)) {
    return ref;
  }

  const remoteRef = `origin/${ref}`;
  if (gitRefExists(remoteRef)) {
    return remoteRef;
  }

  return null;
}

function cleanGeneratedPaths() {
  for (const relPath of generatedPaths) {
    fs.rmSync(path.join(repoRoot, relPath), {force: true, recursive: true});
  }
}

function ensureDir(dir) {
  fs.mkdirSync(dir, {recursive: true});
}

function archivePaths(sourceRelPath, sourceIncludes) {
  if (!Array.isArray(sourceIncludes) || sourceIncludes.length === 0) {
    return [sourceRelPath];
  }

  if (sourceRelPath === '.' || sourceRelPath === '') {
    return sourceIncludes;
  }

  return sourceIncludes.map((includePath) => path.posix.join(sourceRelPath.split(path.sep).join('/'), includePath));
}

function copyFromWorkingTree(sourceRelPath, destinationDir) {
  const sourcePath = path.join(repoRoot, sourceRelPath);
  if (!fs.existsSync(sourcePath)) {
    throw new Error(`Missing source docs directory: ${sourceRelPath}`);
  }
  fs.cpSync(sourcePath, destinationDir, {recursive: true});
}

function copyFromGitRef(ref, sourceRelPath, destinationDir, sourceIncludes) {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'hugegraph-docs-version-'));
  try {
    const archive = run('git', ['archive', '--format=tar', ref, '--', ...archivePaths(sourceRelPath, sourceIncludes)], {
      encoding: 'buffer',
    });
    run('tar', ['-xf', '-', '-C', tempDir], {
      input: archive.stdout,
      stdio: ['pipe', 'ignore', 'pipe'],
    });
    const extractedPath = path.join(tempDir, sourceRelPath);
    if (!fs.existsSync(extractedPath)) {
      throw new Error(`Ref ${ref} does not contain ${sourceRelPath}`);
    }
    fs.cpSync(extractedPath, destinationDir, {recursive: true});
  } finally {
    fs.rmSync(tempDir, {force: true, recursive: true});
  }
}

function copyOverlayFromGitRef(ref, overlay, destinationDir) {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'hugegraph-docs-version-overlay-'));
  try {
    const archive = run('git', ['archive', '--format=tar', ref, '--', overlay.sourcePath], {
      encoding: 'buffer',
    });
    run('tar', ['-xf', '-', '-C', tempDir], {
      input: archive.stdout,
      stdio: ['pipe', 'ignore', 'pipe'],
    });
    const extractedPath = path.join(tempDir, overlay.sourcePath);
    if (!fs.existsSync(extractedPath)) {
      throw new Error(`Ref ${ref} does not contain overlay source ${overlay.sourcePath}`);
    }
    const targetPath = path.join(destinationDir, overlay.targetPath);
    fs.rmSync(targetPath, {force: true, recursive: true});
    fs.cpSync(extractedPath, targetPath, {recursive: true});
  } finally {
    fs.rmSync(tempDir, {force: true, recursive: true});
  }
}

function copyOverlayFromWorkingTree(overlay, destinationDir) {
  const sourcePath = path.join(repoRoot, overlay.sourcePath);
  if (!fs.existsSync(sourcePath)) {
    throw new Error(`Missing overlay source docs directory: ${overlay.sourcePath}`);
  }
  const targetPath = path.join(destinationDir, overlay.targetPath);
  fs.rmSync(targetPath, {force: true, recursive: true});
  fs.cpSync(sourcePath, targetPath, {recursive: true});
}

function copySourceOverlays(legacyCompatibility, locale, destinationDir, resolvedSourceRef) {
  const overlays = legacyCompatibility?.sourceOverlays?.[locale] || [];
  for (const overlay of overlays) {
    if (resolvedSourceRef) {
      copyOverlayFromGitRef(resolvedSourceRef, overlay, destinationDir);
      log(`${locale}: applied overlay ${overlay.sourcePath} -> ${overlay.targetPath}`);
    } else {
      copyOverlayFromWorkingTree(overlay, destinationDir);
      log(`${locale}: applied working tree overlay ${overlay.sourcePath} -> ${overlay.targetPath}`);
    }
  }
}

function prepareIndex(destinationDir, indexFrom) {
  if (!indexFrom) {
    return;
  }

  const sourcePath = path.join(destinationDir, indexFrom);
  if (!fs.existsSync(sourcePath)) {
    throw new Error(`Configured index source does not exist: ${indexFrom}`);
  }

  fs.copyFileSync(sourcePath, path.join(destinationDir, '_index.md'));
  fs.rmSync(sourcePath, {force: true});
}

function walkMarkdownFiles(dir) {
  const entries = fs.readdirSync(dir, {withFileTypes: true});
  return entries.flatMap((entry) => {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      return walkMarkdownFiles(fullPath);
    }
    return /\.mdx?$/i.test(entry.name) ? [fullPath] : [];
  });
}

function stripMarkdownExtension(filePath) {
  return filePath.replace(/\.mdx?$/i, '');
}

function stripRoute(value) {
  return value.replace(/^\/+|\/+$/g, '');
}

function routeFromMarkdownFile(filePath, destinationDir) {
  const relPath = path.relative(destinationDir, stripMarkdownExtension(filePath)).split(path.sep).join('/');
  if (relPath === '_index') {
    return '';
  }
  const route = relPath.endsWith('/_index') ? relPath.slice(0, -'/_index'.length) : relPath;
  return stripRoute(route);
}

function buildDocRouteIndex(destinationDir) {
  const routes = new Map();
  const basenameRoutes = new Map();

  for (const filePath of walkMarkdownFiles(destinationDir)) {
    const normalizedRoute = routeFromMarkdownFile(filePath, destinationDir);
    const key = normalizedRoute.toLowerCase();
    routes.set(key, normalizedRoute);

    const parentRoute = path.posix.dirname(normalizedRoute);
    if (path.posix.basename(parentRoute) === path.posix.basename(normalizedRoute)) {
      routes.set(normalizedRoute.toLowerCase(), parentRoute);
    }

    const basename = path.posix.basename(normalizedRoute).toLowerCase();
    const existing = basenameRoutes.get(basename);
    basenameRoutes.set(basename, existing && existing !== normalizedRoute ? null : normalizedRoute);
  }

  return {basenameRoutes, routes};
}

function relativeLocalImageUrl(filePath, destinationDir, url) {
  const localImagePath = url.replace(/^\/(?:docs\/)?images\//, 'images/');
  const imagePath = path.join(destinationDir, localImagePath);
  let relativePath = path.relative(path.dirname(filePath), imagePath).split(path.sep).join('/');
  if (!relativePath.startsWith('.')) {
    relativePath = `./${relativePath}`;
  }
  return relativePath;
}

function splitUrl(url) {
  const match = url.match(/^([^?#]*)([^#]*)(#.*)?$/);
  return {
    pathname: match?.[1] || url,
    search: match?.[2] || '',
    hash: match?.[3] || '',
  };
}

function routeBase(locale, versionId) {
  const base = locale === 'cn' ? '/cn/docs' : '/docs';
  return versionId === 'stable' ? base : `${base}/${versionId}`;
}

function normalizeLegacyDocsRelPath(pathname) {
  let normalized = pathname.replace(/^\/dcos\//, '/docs/');
  normalized = normalized.replace(/\.(?:html|mdx?)\/?$/i, '');

  const versionedDocsMatch = normalized.match(/^\/(?:cn\/)?docs\/docusaurus-[^/]+\/?(.*)$/);
  if (versionedDocsMatch) {
    return versionedDocsMatch[1];
  }

  for (const prefix of ['/en/docs/', '/cn/docs/', '/docs/']) {
    if (normalized.startsWith(prefix)) {
      return normalized.slice(prefix.length);
    }
  }

  const legacyRootMatch = normalized.match(/^\/(changelog|clients|config|download|guides|language|performance|quickstart)\/?(.*)$/);
  if (legacyRootMatch) {
    return [legacyRootMatch[1], legacyRootMatch[2]].filter(Boolean).join('/');
  }

  return null;
}

function resolveDocsRelPath(relPath, docRouteIndex) {
  const normalized = stripRoute(relPath);
  const alias = legacyRouteAliases.get(normalized.toLowerCase());
  if (alias && docRouteIndex.routes.has(alias)) {
    return alias;
  }

  const byFullPath = docRouteIndex.routes.get(normalized.toLowerCase());
  if (byFullPath) {
    return byFullPath;
  }

  const basename = path.posix.basename(normalized).toLowerCase();
  const byBasename = docRouteIndex.basenameRoutes.get(basename);
  if (byBasename) {
    return byBasename;
  }

  return normalized;
}

function normalizeLegacyLinkUrl(url, context) {
  if (
    !url ||
    url.startsWith('http://') ||
    url.startsWith('https://') ||
    url.startsWith('mailto:') ||
    url.startsWith('pathname://')
  ) {
    return url;
  }

  if (url.startsWith('#')) {
    return context.dropInternalAnchors
      ? `${routeBase(context.locale, context.versionId)}${context.currentRoute ? `/${context.currentRoute}` : ''}`
      : url;
  }

  if (url === './hugegraph-style.xml') {
    return null;
  }

  const {hash, pathname, search} = splitUrl(url);
  const targetHash = context.dropInternalAnchors ? '' : hash;
  const relPath = normalizeLegacyDocsRelPath(pathname);
  if (relPath === null) {
    return url;
  }

  const resolvedRelPath = resolveDocsRelPath(relPath, context.docRouteIndex);
  if (resolvedRelPath === 'download' && !context.docRouteIndex.routes.has('download')) {
    const downloadBase = context.locale === 'cn' ? '/cn/download' : '/download';
    return `${downloadBase}${search}${targetHash}`;
  }
  return `${routeBase(context.locale, context.versionId)}/${resolvedRelPath}${search}${targetHash}`;
}

function normalizeMarkdownLinks(text, context) {
  let normalized = text.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (match, label, url) => {
    const normalizedUrl = normalizeLegacyLinkUrl(url, context);
    return normalizedUrl === null ? label : `[${label}](${normalizedUrl})`;
  });
  normalized = normalized.replace(/(<a\b[^>]*\bhref=["'])([^"']+)(["'])/g, (match, prefix, url, suffix) => {
    const normalizedUrl = normalizeLegacyLinkUrl(url, context);
    return normalizedUrl === null ? match : `${prefix}${normalizedUrl}${suffix}`;
  });
  return normalized;
}

function normalizeLegacyMarkdownLine(line) {
  if (line.includes('`')) {
    return line;
  }
  return line
    .replace(/http:\/\/host:port/g, '`http://host:port`')
    .replace(/https?:\/\/[A-Za-z0-9.-]+:\d+(?=[，；、。])/g, (url) => `\`${url}\``);
}

function normalizeGeneratedFrontMatter(text) {
  return text.replace(/^---\n([\s\S]*?)\n---/, (match, frontMatter) => {
    const normalizedFrontMatter = frontMatter
      .split('\n')
      .filter((line) => !/^draft:\s*true\s*$/i.test(line.trim()))
      .join('\n');
    return `---\n${normalizedFrontMatter}\n---`;
  });
}

// Compatibility adapter for archived pre-Docusaurus release branches only.
function normalizeGeneratedMarkdown(destinationDir, context) {
  const docRouteIndex = buildDocRouteIndex(destinationDir);
  const normalizeContext = {...context, docRouteIndex};

  for (const filePath of walkMarkdownFiles(destinationDir)) {
    let inFence = false;
    const fileContext = {
      ...normalizeContext,
      currentRoute: routeFromMarkdownFile(filePath, destinationDir),
      dropInternalAnchors: true,
    };
    let text = normalizeGeneratedFrontMatter(fs.readFileSync(filePath, 'utf8'));
    text = text
      .split('\n')
      .map((line) => {
        if (/^\s*```/.test(line)) {
          inFence = !inFence;
          return line;
        }
        return inFence ? line : normalizeLegacyMarkdownLine(line);
      })
      .join('\n');

    text = text.replace(/(!\[[^\]]*\]\()\/(?:docs\/)?images\/([^)]+)(\))/g, (_, prefix, imagePath, suffix) => {
      return `${prefix}${relativeLocalImageUrl(filePath, destinationDir, `/images/${imagePath}`)}${suffix}`;
    });
    text = text.replace(/(<img\b[^>]*\bsrc=["'])\/(?:docs\/)?images\/([^"']+)(["'])/g, (_, prefix, imagePath, suffix) => {
      return `${prefix}${relativeLocalImageUrl(filePath, destinationDir, `/images/${imagePath}`)}${suffix}`;
    });
    text = normalizeMarkdownLinks(text, fileContext);

    fs.writeFileSync(filePath, text);
  }
}

function sourceRefFor(version) {
  if (version.id === 'stable' && process.env.DOCS_STABLE_REF) {
    return process.env.DOCS_STABLE_REF;
  }
  return version.sourceRef || null;
}

function legacyCompatibilityFor(version) {
  return version.legacyCompatibility?.enabled === true ? version.legacyCompatibility : null;
}

function assertNoTopLevelLegacyOptions(version) {
  const legacyOnlyFields = ['sourcePaths', 'sourceIncludes', 'sourceOverlays', 'indexFrom'];
  for (const field of legacyOnlyFields) {
    if (version[field] !== undefined) {
      throw new Error(
        `${version.id}: ${field} is a legacy compatibility option. Put it under legacyCompatibility and set legacyCompatibility.enabled=true.`,
      );
    }
  }
}

function prepareVersion(version, locale, target) {
  assertNoTopLevelLegacyOptions(version);

  const legacyCompatibility = legacyCompatibilityFor(version);
  const versionId = version.docusaurusVersion || version.id;
  const sourceRef = sourceRefFor(version);
  const sourcePath = legacyCompatibility?.sourcePaths?.[locale] || target.sourcePath;
  const sourceIncludes = legacyCompatibility?.sourceIncludes;
  const destinationDir = path.join(repoRoot, target.docsDir, `version-${versionId}`);
  let resolvedSourceRef = null;

  ensureDir(destinationDir);
  if (sourceRef) {
    resolvedSourceRef = resolveGitRef(sourceRef);
    if (!resolvedSourceRef) {
      throw new Error(
        `Configured docs source ref "${sourceRef}" is not available locally. Fetch tags/branches first, or override with DOCS_STABLE_REF.`,
      );
    }
    copyFromGitRef(resolvedSourceRef, sourcePath, destinationDir, sourceIncludes);
    log(`${locale}: generated ${versionId} from ${resolvedSourceRef}:${sourcePath}`);
  } else {
    copyFromWorkingTree(sourcePath, destinationDir);
    log(`${locale}: generated ${versionId} from working tree ${sourcePath}`);
  }
  copySourceOverlays(legacyCompatibility, locale, destinationDir, resolvedSourceRef);
  prepareIndex(destinationDir, legacyCompatibility?.indexFrom);
  if (legacyCompatibility?.normalizeMarkdown) {
    normalizeGeneratedMarkdown(destinationDir, {locale, versionId});
    log(`${locale}: applied legacy compatibility normalization for ${versionId}`);
  }

  const sidebarsDir = path.join(repoRoot, target.sidebarsDir);
  ensureDir(sidebarsDir);
  const sidebarsPath = path.join(sidebarsDir, `version-${versionId}-sidebars.json`);
  const sidebar = {
    docsSidebar: buildSidebar(path.relative(repoRoot, destinationDir)),
  };
  fs.writeFileSync(sidebarsPath, `${JSON.stringify(sidebar, null, 2)}\n`);
}

cleanGeneratedPaths();

const releaseVersions = versions.filter((version) => version.status !== 'next');
const releaseIds = releaseVersions.map((version) => version.docusaurusVersion || version.id);

for (const [locale, target] of Object.entries(localeTargets)) {
  ensureDir(path.join(repoRoot, target.docsDir));
  ensureDir(path.join(repoRoot, target.sidebarsDir));
  fs.writeFileSync(path.join(repoRoot, target.versionsFile), `${JSON.stringify(releaseIds, null, 2)}\n`);

  for (const version of releaseVersions) {
    prepareVersion(version, locale, target);
  }
}

log(`prepared ${releaseIds.length} release version(s): ${releaseIds.join(', ') || 'none'}`);
