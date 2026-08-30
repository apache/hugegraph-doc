#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const allowPrivateContent = process.env.ALLOW_PRIVATE_CONTENT === 'true';
const scanRoots = [
  'content',
  'src/pages',
  'versioned_docs',
  'docs-cn_versioned_docs',
];

function walk(dir) {
  if (!fs.existsSync(dir)) {
    return [];
  }

  const entries = fs.readdirSync(dir, {withFileTypes: true});
  return entries.flatMap((entry) => {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      return walk(fullPath);
    }
    return /\.(md|mdx)$/i.test(entry.name) ? [fullPath] : [];
  });
}

function parseScalar(value) {
  const trimmed = value.trim().replace(/^['"]|['"]$/g, '');
  if (trimmed === 'true') {
    return true;
  }
  if (trimmed === 'false') {
    return false;
  }
  return trimmed;
}

function parseFrontMatter(filePath) {
  const text = fs.readFileSync(filePath, 'utf8');
  if (!text.startsWith('---\n')) {
    return {frontMatter: {}, body: text};
  }

  const end = text.indexOf('\n---', 4);
  if (end === -1) {
    return {frontMatter: {}, body: text};
  }

  const frontMatter = {};
  for (const line of text.slice(4, end).split('\n')) {
    const match = line.match(/^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$/);
    if (match) {
      frontMatter[match[1]] = parseScalar(match[2]);
    }
  }

  return {
    frontMatter,
    body: text.slice(end + '\n---'.length).trim(),
  };
}

function plainBody(body) {
  return body
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

const files = scanRoots.flatMap((root) => walk(path.join(repoRoot, root)));
const errors = [];
let privateCount = 0;
let draftCount = 0;
let unlistedCount = 0;
let placeholderCount = 0;

for (const filePath of files) {
  const relPath = path.relative(repoRoot, filePath);
  const {frontMatter, body} = parseFrontMatter(filePath);

  if (frontMatter.private === true) {
    privateCount += 1;
    if (!allowPrivateContent) {
      errors.push(`${relPath}: private: true content cannot be shipped in a production build.`);
    }
  }

  if (frontMatter.draft === true) {
    draftCount += 1;
  }
  if (frontMatter.unlisted === true) {
    unlistedCount += 1;
  }

  if (frontMatter.placeholder === true) {
    placeholderCount += 1;
    const bodyText = plainBody(body);
    if (frontMatter.private === true) {
      errors.push(`${relPath}: placeholder content must not also be private.`);
    }
    if (frontMatter.draft === true) {
      errors.push(`${relPath}: placeholder content reserves a route, so it must not also be draft.`);
    }
    if (frontMatter.unlisted !== true) {
      errors.push(`${relPath}: placeholder content must explicitly set unlisted: true.`);
    }
    if (frontMatter.noindex !== true) {
      errors.push(`${relPath}: placeholder content must explicitly set noindex: true.`);
    }
    if (bodyText.length > 600) {
      errors.push(`${relPath}: placeholder body must stay short and must not contain unfinished private content.`);
    }
  }
}

if (errors.length > 0) {
  console.error('Content visibility check failed:');
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  console.error('');
  console.error('Set ALLOW_PRIVATE_CONTENT=true only for a non-public, access-controlled preview build.');
  process.exit(1);
}

console.log(
  `Content visibility OK: scanned ${files.length} Markdown/MDX files; private=${privateCount}, draft=${draftCount}, unlisted=${unlistedCount}, placeholder=${placeholderCount}.`,
);
