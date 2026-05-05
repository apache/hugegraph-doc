const fs = require('fs');
const path = require('path');

const SKIP_DIRS = new Set(['images', 'scripts', 'styles']);
const SKIP_FILES = new Set(['SUMMARY.md']);

const SECTION_ORDER = [
  'introduction',
  'quickstart',
  'config',
  'clients',
  'guides',
  'language',
  'performance',
  'changelog',
  'contribution-guidelines',
];

function readFrontMatter(filePath) {
  const text = fs.readFileSync(filePath, 'utf8');
  const match = text.match(/^---\n([\s\S]*?)\n---/);
  if (!match) {
    return {};
  }

  const data = {};
  for (const line of match[1].split('\n')) {
    const item = line.match(/^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$/);
    if (!item) {
      continue;
    }
    data[item[1]] = item[2].replace(/^['"]|['"]$/g, '');
  }
  return data;
}

function labelFromPath(filePath, fallback) {
  const fm = readFrontMatter(filePath);
  return fm.linkTitle || fm.title || fallback;
}

function weight(filePath, name) {
  const fm = fs.existsSync(filePath) ? readFrontMatter(filePath) : {};
  if (fm.weight !== undefined && !Number.isNaN(Number(fm.weight))) {
    return Number(fm.weight);
  }
  const sectionIndex = SECTION_ORDER.indexOf(name);
  return sectionIndex === -1 ? 1000 : sectionIndex;
}

function stripExtension(fileName) {
  return fileName.replace(/\.mdx?$/i, '');
}

function docId(relPath) {
  return stripExtension(relPath).split(path.sep).join('/');
}

function titleCase(value) {
  return value
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function sortEntries(baseDir, relDir, entries) {
  return entries.sort((a, b) => {
    const aPath = path.join(baseDir, relDir, a.name, a.isDirectory() ? '_index.md' : '');
    const bPath = path.join(baseDir, relDir, b.name, b.isDirectory() ? '_index.md' : '');
    const aWeight = weight(a.isDirectory() ? aPath : path.join(baseDir, relDir, a.name), stripExtension(a.name));
    const bWeight = weight(b.isDirectory() ? bPath : path.join(baseDir, relDir, b.name), stripExtension(b.name));
    if (aWeight !== bWeight) {
      return aWeight - bWeight;
    }
    return a.name.localeCompare(b.name);
  });
}

function buildDirectory(baseDir, relDir = '') {
  const dir = path.join(baseDir, relDir);
  const entries = fs.readdirSync(dir, {withFileTypes: true});

  const files = sortEntries(
    baseDir,
    relDir,
    entries.filter(
      (entry) =>
        entry.isFile() &&
        /\.mdx?$/i.test(entry.name) &&
        entry.name !== '_index.md' &&
        !SKIP_FILES.has(entry.name),
    ),
  ).map((entry) => ({
    type: 'doc',
    id: docId(path.join(relDir, entry.name)),
    label: labelFromPath(path.join(baseDir, relDir, entry.name), titleCase(stripExtension(entry.name))),
  }));

  const dirs = sortEntries(
    baseDir,
    relDir,
    entries.filter((entry) => entry.isDirectory() && !SKIP_DIRS.has(entry.name)),
  ).map((entry) => buildCategory(baseDir, path.join(relDir, entry.name)));

  return [...dirs, ...files];
}

function buildCategory(baseDir, relDir) {
  const indexFile = path.join(baseDir, relDir, '_index.md');
  const label = fs.existsSync(indexFile)
    ? labelFromPath(indexFile, titleCase(path.basename(relDir)))
    : titleCase(path.basename(relDir));
  const category = {
    type: 'category',
    label,
    collapsible: true,
    collapsed: true,
    items: buildDirectory(baseDir, relDir),
  };

  if (fs.existsSync(indexFile)) {
    category.link = {
      type: 'doc',
      id: docId(path.join(relDir, '_index.md')),
    };
  }

  return category;
}

function buildSidebar(baseDir) {
  const items = [];
  const rootIndex = path.join(baseDir, '_index.md');
  if (fs.existsSync(rootIndex)) {
    items.push({
      type: 'doc',
      id: '_index',
      label: labelFromPath(rootIndex, 'Documentation'),
    });
  }
  items.push(...buildDirectory(baseDir));
  return items;
}

module.exports = {buildSidebar};
