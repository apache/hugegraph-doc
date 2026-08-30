#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const {execFileSync} = require('child_process');

const repoRoot = path.resolve(__dirname, '..');
const artifactDir = path.join(repoRoot, 'artifacts', 'validation');

function gitFiles() {
  return execFileSync('git', ['ls-files', '*.md', '*.mdx'], {
    cwd: repoRoot,
    encoding: 'utf8',
  })
    .trim()
    .split('\n')
    .filter(Boolean)
    .sort();
}

function exists(relPath) {
  return fs.existsSync(path.join(repoRoot, relPath));
}

fs.mkdirSync(artifactDir, {recursive: true});

const before = gitFiles();
const missing = before.filter((file) => !exists(file));

const after = before.filter(exists);
fs.writeFileSync(path.join(artifactDir, 'md-inventory-before.txt'), `${before.join('\n')}\n`);
fs.writeFileSync(path.join(artifactDir, 'md-inventory-after.txt'), `${after.join('\n')}\n`);
fs.writeFileSync(path.join(artifactDir, 'md-inventory-missing.json'), `${JSON.stringify(missing, null, 2)}\n`);

if (missing.length > 0) {
  console.error(`Missing Markdown/MDX files:\n${missing.join('\n')}`);
  process.exit(1);
}

console.log(`Markdown inventory OK: ${before.length} original tracked .md/.mdx files still exist.`);
console.log(`Inventory artifacts: ${path.relative(repoRoot, artifactDir)}`);
