#!/usr/bin/env node
import {spawnSync} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const version = process.argv[2];

if (!version) {
  console.error('Usage: npm run docs:version -- <version>');
  process.exit(1);
}

const docusaurusBin = path.join(repoRoot, 'node_modules', '.bin', 'docusaurus');

function run(args) {
  const result = spawnSync(process.execPath, [docusaurusBin, ...args], {
    cwd: repoRoot,
    stdio: 'inherit',
  });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

run(['docs:version', version]);
run(['docs:version:docs-cn', version]);

console.log('');
console.log(`Created EN and CN docs snapshots for ${version}.`);
console.log('Review versions.json, docs-cn_versions.json, and src/data/versions.json before publishing.');
