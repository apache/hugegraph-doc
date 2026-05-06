#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

function readJson(relPath) {
  return JSON.parse(fs.readFileSync(path.join(repoRoot, relPath), 'utf8'));
}

const metadata = readJson('src/data/versions.json');
const englishVersions = readJson('versions.json');
const chineseVersions = readJson('docs-cn_versions.json');

console.log('HugeGraph documentation versions');
console.log('');
for (const version of metadata) {
  console.log(`- ${version.label} [${version.status}]`);
  console.log(`  EN: ${version.path}`);
  console.log(`  CN: ${version.cnPath}`);
  if (version.releaseDate) {
    console.log(`  Released: ${version.releaseDate}`);
  }
  if (version.githubTagUrl) {
    console.log(`  Tag: ${version.githubTagUrl}`);
  }
}
console.log('');
console.log(`Docusaurus EN versions.json: ${englishVersions.join(', ')}`);
console.log(`Docusaurus CN docs-cn_versions.json: ${chineseVersions.join(', ')}`);
