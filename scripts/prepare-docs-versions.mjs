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

function cleanGeneratedPaths() {
  for (const relPath of generatedPaths) {
    fs.rmSync(path.join(repoRoot, relPath), {force: true, recursive: true});
  }
}

function ensureDir(dir) {
  fs.mkdirSync(dir, {recursive: true});
}

function copyFromWorkingTree(sourceRelPath, destinationDir) {
  const sourcePath = path.join(repoRoot, sourceRelPath);
  if (!fs.existsSync(sourcePath)) {
    throw new Error(`Missing source docs directory: ${sourceRelPath}`);
  }
  fs.cpSync(sourcePath, destinationDir, {recursive: true});
}

function copyFromGitRef(ref, sourceRelPath, destinationDir) {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'hugegraph-docs-version-'));
  try {
    const archive = run('git', ['archive', '--format=tar', ref, '--', sourceRelPath], {
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

function sourceRefFor(version) {
  if (version.id === 'stable' && process.env.DOCS_STABLE_REF) {
    return process.env.DOCS_STABLE_REF;
  }
  return version.sourceRef || null;
}

function prepareVersion(version, locale, target) {
  const versionId = version.docusaurusVersion || version.id;
  const sourceRef = sourceRefFor(version);
  const sourcePath = version.sourcePaths?.[locale] || target.sourcePath;
  const destinationDir = path.join(repoRoot, target.docsDir, `version-${versionId}`);

  ensureDir(destinationDir);
  if (sourceRef) {
    if (!gitRefExists(sourceRef)) {
      throw new Error(
        `Configured docs source ref "${sourceRef}" is not available locally. Fetch tags/branches first, or override with DOCS_STABLE_REF.`,
      );
    }
    copyFromGitRef(sourceRef, sourcePath, destinationDir);
    log(`${locale}: generated ${versionId} from ${sourceRef}:${sourcePath}`);
  } else {
    copyFromWorkingTree(sourcePath, destinationDir);
    log(`${locale}: generated ${versionId} from working tree ${sourcePath}`);
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
