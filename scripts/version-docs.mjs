#!/usr/bin/env node

console.error('This repository generates Docusaurus version snapshots from Git refs instead of committing them.');
console.error('');
console.error('To add or refresh a documentation version:');
console.error('1. Update src/data/versions.json with the version id, label, routes, and sourceRef.');
console.error('2. Run npm run docs:versions:prepare.');
console.error('3. Run npm run build to verify the generated output.');
console.error('');
console.error('The generated versioned_docs and docs-cn_versioned_docs directories are intentionally ignored by Git.');
process.exit(1);
