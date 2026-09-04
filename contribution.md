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

```text
Go:             1.27.0 or newer
Hugo Extended:  0.165.0
OINK:           v1.0.0
```

Node.js, npm, PostCSS, and a vendored Docsy checkout are not part of the build.

Verify the resolved theme before editing:

```bash
hugo version
go version
hugo mod graph
```

The module graph must contain exactly the pinned `github.com/pgsty/oink@v1.0.0` dependency for this site.

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

A successful command proves that Hugo rendered the configured outputs. It does not replace browser checks for navigation, search, language switching, accessibility, mobile layout, print, or Content Security Policy behavior.

## Repository structure

- `content/en/` and `content/cn/` contain the bilingual source pages.
- `hugo.yaml` owns routing, languages, outputs, search, navigation, and OINK parameters.
- `data/home/<language>.yaml` owns the bilingual homepage.
- `data/footer/<language>.yaml` owns the bilingual footer.
- `i18n/cn.yaml` maps the preserved `cn` URL language key to the Simplified Chinese OINK interface catalogue.
- `assets/` and `static/` contain site-owned brand and compatibility assets.

OINK is a module dependency. Do not copy or edit generated module-cache files. Site-specific overrides belong in the corresponding root `layouts/`, `assets/`, or data path and require focused regression evidence.

## 中文说明

提交前请同时检查中英文页面、公开 URL、搜索结果和语言切换。视觉或导航变更必须提供修改前后的桌面与移动端截图。构建成功只证明模板可以渲染，不能替代真实浏览器、无障碍、打印和 CSP 检查。
