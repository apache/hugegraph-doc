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

function nativeOptions(anchors) {
  return new Map(
    anchors.slice(0, 5).map((anchor) => [
      anchor['data-hg-version-id'],
      anchor,
    ]),
  );
}

test('wrapper output keeps Palette choices and native version links identical', () => {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), 'hg-version-data-'));
  const fixtureData = path.join(fixture, 'data');
  fs.cpSync(path.join(root, 'data'), fixtureData, { recursive: true });
  const routesPath = path.join(fixtureData, 'version_routes.json');
  const routes = JSON.parse(fs.readFileSync(routesPath, 'utf8'));
  routes.equivalents = [
    ['cn:introduction', 'cn:introduction/readme'],
    ['en:introduction', 'en:introduction/readme'],
  ];
  fs.writeFileSync(routesPath, `${JSON.stringify(routes)}\n`);
  try {
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
            env: {
              ...process.env,
              HG_DOC_VERSION: version,
              HUGO_DATADIR: fixtureData,
            },
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
          const native = nativeOptions(anchors);
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
            assert.ok(
              anchor,
              `native ${option.id} option missing from ${relative}`,
            );
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

        for (const locale of ['', 'cn/']) {
          const relative = `${locale}docs/introduction/index.html`;
          const { action, anchors } = pageContract(site, relative);
          const native = nativeOptions(anchors);
          const direct = action.options.find(({ id }) => id === version);
          assert.equal(direct.equivalent, true);
          assert.equal(direct.fallback, false);
          assert.match(
            direct.url,
            new RegExp(
              `${version === 'latest' ? '' : `versions/${version}/`}` +
                `${locale}docs/introduction/$`,
            ),
          );
          const renamed = action.options.find(({ id }) => id === '1.5');
          assert.equal(renamed.equivalent, true);
          assert.equal(renamed.fallback, false);
          assert.match(
            renamed.url,
            new RegExp(`versions/1\\.5/${locale}docs/introduction/readme/$`),
          );
          for (const option of action.options) {
            const anchor = native.get(option.id);
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
  } finally {
    fs.rmSync(fixture, { recursive: true });
  }
});
