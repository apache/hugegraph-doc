#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

function readJson(relPath) {
  return JSON.parse(fs.readFileSync(path.join(repoRoot, relPath), 'utf8'));
}

const metadata = readJson('src/data/versions.json');
const releaseVersions = metadata
  .filter((version) => version.status !== 'next')
  .map((version) => version.docusaurusVersion || version.id);

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
  if (version.sourceRef) {
    console.log(`  Source ref: ${version.sourceRef}`);
  }
}
console.log('');
console.log(`Generated Docusaurus release versions: ${releaseVersions.join(', ') || '(none)'}`);
console.log('Run npm run docs:versions:prepare to regenerate Docusaurus version files from the configured source refs.');
