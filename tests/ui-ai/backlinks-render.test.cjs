const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const test = require('node:test');

const root = path.resolve(__dirname, '../..');

test('six backlink fixture renders five rows and one expandable row', () => {
  const destination = fs.mkdtempSync(
    path.join(os.tmpdir(), 'hg-backlinks-fixture-'),
  );
  try {
    const result = spawnSync(
      'hugo',
      [
        '--config',
        'hugo.yaml,tests/ui-ai/fixtures/backlinks.yaml',
        '--destination',
        destination,
        '--quiet',
      ],
      {
        cwd: root,
        encoding: 'utf8',
        env: {
          ...process.env,
          HUGO_CACHEDIR: path.join(destination, '.hugo-cache'),
        },
      },
    );
    assert.equal(result.status, 0, result.stderr || result.stdout);
    const html = fs.readFileSync(
      path.join(destination, 'docs/target/index.html'),
      'utf8',
    );
    const block = html.match(
      /<div class="td-shell-aside-group td-shell-backlinks">([\s\S]*?)<\/div>\s*<\/div>\s*<\/div>/,
    );
    assert.ok(block, 'expected rendered backlinks group');
    const beforeDetails = block[1].split(
      '<details class="td-shell-backlinks__more">',
    )[0];
    assert.equal(
      (beforeDetails.match(/td-shell-backlinks__item/g) || []).length,
      5,
    );
    assert.match(block[1], /<details class="td-shell-backlinks__more">/);
    assert.match(block[1], /Source 6/);
  } finally {
    fs.rmSync(destination, { recursive: true, force: true });
  }
});
