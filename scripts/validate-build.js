#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const repoRoot = path.resolve(__dirname, '..');
const buildDir = path.join(repoRoot, 'build');

const expectedPages = [
  ['homepage', 'index.html', 'Apache HugeGraph'],
  ['docs landing', 'docs/index.html', 'Apache HugeGraph Documentation'],
  ['English deep docs page', 'docs/quickstart/hugegraph/hugegraph-server/index.html', 'HugeGraph-Server'],
  ['Chinese docs landing', 'cn/docs/index.html', 'Apache HugeGraph 文档'],
  ['Chinese deep docs page', 'cn/docs/quickstart/hugegraph/hugegraph-server/index.html', 'HugeGraph-Server'],
  ['English blog', 'blog/index.html', 'Blog'],
  ['Chinese blog', 'cn/blog/index.html', 'Blog'],
  ['community', 'community/index.html', 'Community'],
  ['community maturity', 'community/maturity/index.html', 'Apache Maturity Model'],
];

for (const [label, relPath, text] of expectedPages) {
  const file = path.join(buildDir, relPath);
  if (!fs.existsSync(file)) {
    throw new Error(`Missing ${label}: ${relPath}`);
  }
  const html = fs.readFileSync(file, 'utf8');
  if (!html.includes(text)) {
    throw new Error(`Expected ${label} to contain "${text}"`);
  }
}

const homepage = fs.readFileSync(path.join(buildDir, 'index.html'), 'utf8');
for (const label of ['Foundation', 'License', 'Events', 'Privacy', 'Security', 'Sponsorship', 'Thanks', 'Code of Conduct']) {
  if (!homepage.includes(label)) {
    throw new Error(`Homepage is missing ASF menu label: ${label}`);
  }
}

console.log(`Build content OK: ${expectedPages.length} representative pages found.`);
