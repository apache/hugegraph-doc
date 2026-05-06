#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const repoRoot = path.resolve(__dirname, '..');
const buildDir = path.join(repoRoot, 'build');

const expectedPages = [
  ['homepage', 'index.html', 'Apache HugeGraph'],
  ['docs landing', 'docs/index.html', 'Apache HugeGraph Documentation'],
  ['next docs landing', 'docs/next/index.html', 'This is unreleased documentation'],
  ['English deep docs page', 'docs/quickstart/hugegraph/hugegraph-server/index.html', 'HugeGraph-Server'],
  ['Chinese docs landing', 'cn/docs/index.html', 'Apache HugeGraph 文档'],
  ['Chinese next docs landing', 'cn/docs/next/index.html', 'noindex, nofollow'],
  ['Chinese deep docs page', 'cn/docs/quickstart/hugegraph/hugegraph-server/index.html', 'HugeGraph-Server'],
  ['English blog', 'blog/index.html', 'Blog'],
  ['Chinese blog', 'cn/blog/index.html', 'Blog'],
  ['community', 'community/index.html', 'Community'],
  ['community maturity', 'community/maturity/index.html', 'Apache Maturity Model'],
  ['team page', 'team/index.html', 'Apache HugeGraph Team'],
  ['Chinese team page', 'cn/team/index.html', 'Apache HugeGraph 团队'],
  ['users page', 'users/index.html', 'HugeGraph User Showcase'],
  ['Chinese users page', 'cn/users/index.html', 'HugeGraph 用户案例'],
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

const docsLanding = fs.readFileSync(path.join(buildDir, 'docs/index.html'), 'utf8');
for (const label of ['Documentation', 'next', 'Stable (1.7.0)']) {
  if (!docsLanding.includes(label)) {
    throw new Error(`Docs landing is missing version selector label: ${label}`);
  }
}

if (fs.existsSync(path.join(buildDir, 'docs/v1.3.0/index.html'))) {
  throw new Error('Historical v1.3.0 docs route should not be generated for this preview.');
}

console.log(`Build content OK: ${expectedPages.length} representative pages found.`);
