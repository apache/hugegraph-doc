# HugeGraph documentation contribution guide

For the short workflow, start with [README.md](./README.md). This file records the production-equivalent checks for changes to the documentation website.

## Pull request checklist

- [ ] Build the site with the strict production command and keep the complete exit status.
- [ ] Update both `content/en/` and `content/cn/` when the change applies to both languages.
- [ ] Include before/after screenshots for visual or navigation changes.
- [ ] Preserve public English routes under `/docs/...` and Chinese routes under `/cn/docs/...`.
- [ ] Link the related issue when one exists.

## Pinned toolchain

The site uses the Hugo Module recorded in `go.mod` and `go.sum`:

Toolchain versions are maintained in `go.mod` and `.github/workflows/hugo.yml`;
`go.mod` / `go.sum` pin the theme. Node.js is needed only for the browser tests,
with its version declared by `tests/e2e/package.json` and CI.

Verify the installed toolchain and locked module:

```bash
hugo version
go version
python3 scripts/oink_module.py
```

For theme updates and breaking-change recovery, follow
[scripts/oink-upgrade.md](scripts/oink-upgrade.md).

For Kapa staging, consent/CSP checks and production activation, follow
[scripts/kapa-rollout.md](scripts/kapa-rollout.md).

## Local preview

```bash
git clone https://github.com/apache/hugegraph-doc.git
cd hugegraph-doc
scripts/hugo.sh server
```

Open <http://localhost:1313/>. The local preview includes the language-aware search index so search behavior can be checked before publication.

## Strict production build

Run the same warning-strict build used by CI:

```bash
scripts/hugo.sh build
```

The wrapper derives the complete version menu from `versions.json` before
starting Hugo. Additional Hugo arguments are passed through unchanged, for
example `scripts/hugo.sh server -p 8080`. Set `HG_DOC_VERSION`,
`HG_DOC_SITE_ORIGIN`, or `HG_DOC_HISTORICAL_ORIGIN` only when validating a
specific version or publication origin.

The wrapper applies Hugo's configuration, environment, strict-warning,
cleanup, and minification flags before your arguments; Hugo's last-wins flag
handling means anything you append (for example `--logLevel debug`) takes
effect. Use `--baseURL` or `HG_DOC_SITE_ORIGIN` when changing the rendered
origin (the flag wins when both are set); a server `--port` is reflected in
the generated local origin.

A successful command proves that Hugo rendered the configured outputs. It does not replace browser checks for navigation, search, language switching, accessibility, mobile layout, print, or Content Security Policy behavior.

## CI queue and reruns

Each PR has its own concurrency group; a new commit cancels its previous run.
Cancelled runs skip report uploads and the final gate instead of holding the
queue with `always()`. A queued job with no runner has not started testing;
repeated reruns do not resolve runner capacity shortages.

Version builds remain parallel. Site assembly and blocking browser tests share
one runner and the same local artifact. The required `deploy` check still
requires all blocking jobs to succeed; visual captures remain advisory and
publication alone receives write permission. For a test failure, rerun failed
jobs after inspecting the cause; artifact names remain stable within the run.

## Repository structure

- `content/en/` and `content/cn/` contain the bilingual source pages.
- `hugo.yaml` owns routing, languages, outputs, search, navigation, and OINK parameters.
- `data/home/<language>.yaml` owns the bilingual homepage.
- `data/footer/<language>.yaml` owns the bilingual footer.
- `i18n/zh-CN.yaml` carries only HugeGraph-specific Simplified Chinese labels; generic interface translations come from OINK for the preserved `cn` URL language key; the file is named after the `zh-CN` locale because Hugo resolves translations by locale, not by the URL key.
- `assets/` and `static/` contain site-owned brand and compatibility assets.

OINK is a module dependency. Do not copy or edit generated module-cache files. Site-specific overrides belong in the corresponding root `layouts/`, `assets/`, or data path and require focused regression evidence.

## 中文说明

提交前请同时检查中英文页面、公开 URL、搜索结果和语言切换。视觉或导航变更必须提供修改前后的桌面与移动端截图。构建成功只证明模板可以渲染，不能替代真实浏览器、无障碍、打印和 CSP 检查。
