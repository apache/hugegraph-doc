const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const test = require('node:test');

const root = path.resolve(__dirname, '../..');

function attributes(tag) {
  return Object.fromEntries(
    Array.from(
      tag.matchAll(/([:\w-]+)(?:=(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g),
      (match) => [match[1], match[2] ?? match[3] ?? match[4] ?? ''],
    ),
  );
}

function pageContract(site, relative) {
  const html = fs.readFileSync(path.join(site, relative), 'utf8');
  const manifestMatch = html.match(
    /<script[^>]*id=td-action-manifest[^>]*>(.*?)<\/script>/,
  );
  assert.ok(manifestMatch, `action manifest missing from ${relative}`);
  const manifest = JSON.parse(manifestMatch[1]);
  const action = manifest.actions.find(({ id }) => id === 'switch_version');
  const anchors = Array.from(
    html.matchAll(/<a\b[^>]*data-hg-version-id[^>]*>/g),
    (match) => attributes(match[0]),
  );
  return { action, anchors };
}

test('wrapper output keeps Palette choices and native version links identical', () => {
  for (const version of ['latest', '1.7']) {
    const site = fs.mkdtempSync(path.join(os.tmpdir(), 'hg-version-manifest-'));
    try {
      const build = spawnSync(
        path.join(root, 'scripts/hugo.sh'),
        ['build', '--destination', site],
        {
          cwd: root,
          encoding: 'utf8',
          timeout: 60_000,
          env: { ...process.env, HG_DOC_VERSION: version },
        },
      );
      assert.equal(build.status, 0, build.stderr);

      for (const relative of [
        'docs/guides/security/index.html',
        'cn/docs/guides/security/index.html',
      ]) {
        const { action, anchors } = pageContract(site, relative);
        assert.ok(action);
        assert.deepEqual(
          action.options.map(({ id }) => id),
          ['latest', '1.7', '1.5', '1.3', '1.0'],
        );
        assert.equal(
          action.options.find(({ id }) => id === version).active,
          true,
        );
        const native = new Map(
          anchors.slice(0, 5).map((anchor) => [
            anchor['data-hg-version-id'],
            anchor,
          ]),
        );
        for (const option of action.options) {
          assert.deepEqual(Object.keys(option).sort(), [
            'active',
            'available',
            'disabledReason',
            'equivalent',
            'fallback',
            'id',
            'title',
            'url',
          ]);
          const anchor = native.get(option.id);
          assert.ok(anchor, `native ${option.id} option missing from ${relative}`);
          assert.equal(option.url, anchor.href);
          assert.equal(
            option.equivalent,
            anchor['data-hg-version-equivalent'] === 'true',
          );
          assert.equal(
            option.fallback,
            anchor['data-hg-version-fallback'] === 'true',
          );
        }
      }
    } finally {
      fs.rmSync(site, { recursive: true });
    }
  }
});
