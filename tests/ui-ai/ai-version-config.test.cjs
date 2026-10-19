const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const test = require('node:test');

const root = path.resolve(__dirname, '../..');
const groups = Object.fromEntries(['latest', '1.7', '1.5'].map(version => [
  version, { en: `${version}-en`, cn: `${version}-cn` },
]));

// Render the real config partial and hook in a tiny site, without the theme or
// network access, so these checks exercise Hugo's actual map/merge semantics.
function render(version, { enabled = true, sourceGroups = groups } = {}) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'hg-ai-version-'));
  const write = (file, value) => {
    const target = path.join(directory, file);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, value);
  };
  try {
    for (const file of ['layouts/_partials/ai/config.html', 'layouts/_partials/hooks/body-end.html',
      'assets/js/hugegraph-shell.js', 'assets/js/kapa-adapter.js', 'i18n/en.yaml', 'i18n/zh-CN.yaml']) {
      write(file, fs.readFileSync(path.join(root, file)));
    }
    write('layouts/home.html', '<html><body>{{ partial "hooks/body-end.html" . }}</body></html>');
    write('hugo.json', JSON.stringify({
      baseURL: 'https://example.org/', defaultContentLanguage: 'en',
      disableKinds: ['taxonomy', 'term', 'RSS', 'sitemap', 'robotsTXT', '404'],
      languages: { en: { languageCode: 'en-US' }, cn: { languageCode: 'zh-CN' } },
      params: { version, ui: { theme_color: '#532fc9' }, ai_search: {
        enabled, provider: 'kapa', website_id: 'test-website', source_groups: sourceGroups,
      } },
    }));
    const result = spawnSync(process.env.HUGO_BIN || 'hugo', ['--source', directory], {
      encoding: 'utf8', timeout: 30_000,
    });
    const pages = {};
    if (result.status === 0) {
      for (const [locale, file] of [['en', 'index.html'], ['cn', 'cn/index.html']]) {
        const html = fs.readFileSync(path.join(directory, 'public', file), 'utf8');
        const match = html.match(/id="hg-ai-config">([\s\S]*?)<\/script>/);
        pages[locale] = { html, config: match && JSON.parse(match[1]) };
      }
    }
    return { ...result, pages };
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
}

for (const version of ['latest', '1.7', '1.5']) {
  test(`Ask AI selects only ${version}'s language groups and names that version`, () => {
    const result = render(version);
    assert.equal(result.status, 0, result.stderr || result.stdout);
    for (const locale of ['en', 'cn']) {
      const { config, html } = result.pages[locale];
      assert.equal(config.sourceGroupId, `${version}-${locale}`);
      assert.equal(config.version, version);
      assert.equal(config.locale, locale === 'cn' ? 'zh' : 'en');
      assert.ok(config.labels.version.includes(version));
      assert.ok(html.includes(`title="${config.labels.version}"`));
      if (version !== 'latest') assert.equal(html.includes('latest'), false);
    }
  });
}

for (const version of ['1.3', '1.0', 'unknown']) {
  test(`unconfigured ${version} keeps a local notice without a latest group`, () => {
    const result = render(version);
    assert.equal(result.status, 0, result.stderr || result.stdout);
    for (const { html, config } of Object.values(result.pages)) {
      assert.equal(config.sourceGroupId, '');
      assert.ok(config.labels.unavailable.includes(version));
      assert.ok(html.includes('hg-ask-ai-launcher'));
      assert.equal(html.includes('latest-en'), false);
    }
  });
}

test('enabled latest requires an index even when other versions are configured', () => {
  const { latest, ...historicalGroups } = groups;
  const result = render('latest', { sourceGroups: historicalGroups });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr + result.stdout, /source_groups\.latest\.en and \.cn are required/);
});

for (const version of ['latest', '1.7']) {
  for (const missingLocale of ['en', 'cn']) {
    test(`configured ${version} requires its ${missingLocale} group`, () => {
      const result = render(version, { sourceGroups: {
        ...groups, [version]: { ...groups[version], [missingLocale]: '' },
      } });
      assert.notEqual(result.status, 0);
      assert.ok((result.stderr + result.stdout).includes(`source_groups.${version}.en and .cn are required`));
    });
  }
}

for (const sourceGroups of ['invalid', '', ['latest-en'], [], false, null]) {
  test(`enabled AI rejects malformed source_groups: ${JSON.stringify(sourceGroups)}`, () => {
    const result = render('1.7', { sourceGroups });
    assert.notEqual(result.status, 0);
    assert.match(result.stderr + result.stdout, /source_groups must be a map/);
  });
}

for (const version of ['latest', '1.7']) {
  test(`disabled AI stays absent on ${version} even with incomplete groups`, () => {
    const result = render(version, { enabled: false, sourceGroups: { '1.7': { en: '' } } });
    assert.equal(result.status, 0, result.stderr || result.stdout);
    for (const { html, config } of Object.values(result.pages)) {
      assert.equal(config, null);
      assert.equal(/kapa|hg-ai-|hg-ask-ai/.test(html), false);
    }
  });
}
