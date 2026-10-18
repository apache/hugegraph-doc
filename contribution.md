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
`go.mod` / `go.sum` pin the theme. Hugo Extended uses standalone Dart Sass from
`PATH`; CI installs the official archive with a pinned checksum. Node.js is needed only for the browser tests,
with its version declared by `tests/e2e/package.json` and CI.

Verify the installed toolchain and locked module:

```bash
hugo version
sass --version
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

The site's [local preview guide](https://hugegraph.apache.org/community/documentation/) includes a real toolchain-check recording and a short preview workflow.

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

A complete historical cache hit uses one build job. Cold runs use at most three
build groups, with at most two versions building concurrently within each runner.
Historical artifacts are reused only when both the complete build-input fingerprint
and artifact digest match. Missing or invalid cache entries rebuild automatically;
manual dispatches start without the artifact cache and use the original build and
validate commands so older candidate branches do not need the new CI helpers. Cache hits still run the full
version validator, and aggregation validates every selected version again.

Assembly validates at most two versions concurrently, then writes the complete
site and runs the cross-version checks. The final security scan also uses at most
two processes; it starts after version validation finishes, so these pools do not
nest. All checks remain enabled. Stage timings are printed as
`timing <stage>: <seconds>s`; nested security timings are included in their parent
validation duration and must not be added twice. Site assembly and blocking browser
tests share one runner and the same local artifact. The assembly job carries the
required `deploy` check name, avoiding a separate gate runner and its queue time.
Its first step requires successful preparation and builds, and all assembly and
browser checks remain blocking. Visual captures remain advisory and publication
alone receives write permission. For a test failure, rerun failed
jobs after inspecting the cause; artifact names remain stable within the run.

## SeaTunnel documentation versions

The `latest` SeaTunnel guides use the 3.0+ minimum-version label and link to
upstream latest/Next documentation. Concrete versions in installation commands are
examples, with the engine and plugins kept at the same version. When preparing the
HugeGraph 1.8.0 documentation snapshot, pin its SeaTunnel references and installation
version to 3.0.0 in the release branch; keep the `latest` guides tracking upstream.

latest 文档使用 SeaTunnel 3.0+ 等最低版本说明，并引用上游 latest/Next 文档；安装命令中的具体版本仅作为示例，引擎和插件保持同版。
准备 HugeGraph 1.8.0 文档快照时，在发布分支中将 SeaTunnel 文档引用和安装版本固定为 3.0.0，latest 文档继续跟随上游。

## Native content components

Prefer [OINK's native Markdown components](https://oink.pgsty.com/docs/components/)
over copied theme templates: `filetree` for annotated directory layouts, `{.cards}`
for parallel navigation choices, `{tab="..."}` for equivalent code alternatives,
and `kbd` for physical keys. Use `{.steps}` only for actions performed in order.
Keep important prerequisites visible; reserve folding for supplemental detail.
For FileTree comments that readers must see in full, opt into native wrapping:

````markdown
```filetree {title="Store directories" wrap=true}
data/
  m/ # schema store: property keys and labels
  g/ # graph store: vertices, edges and indexes
```
````

Keep the compact default for short comments. For a technical table whose identifiers
would squeeze its descriptions, add `{.td-table--wide}` immediately after the table.
Its native wrapper owns keyboard scrolling; ordinary tables need no modifier.
Do not restore these behaviors with site-wide table or FileTree CSS.

Use Mermaid for relationships and flows, Markmap for a text hierarchy, and ECharts
for quantitative comparisons; keep chart data and test conditions alongside the chart.
Use [Gallery](https://oink.pgsty.com/docs/components/gallery/) for a few screenshots
inside a tutorial. Use [Expo](https://oink.pgsty.com/docs/write/expo/) when the images
are the main content of an independent album: a section with `type: expo` and
`cascade: {type: expo}`, containing leaf bundles with `index.md` and local images.
For example, `content/en/product-images/hubble/index.md` and an `images/` subdirectory
can form one album; add the matching Chinese bundle when adopting it. Expo supplies
wall, masonry and seamless layouts plus original-image viewing; image captions,
credits and ordering belong in Hugo resource metadata. It does not replace the
step-by-step explanation in a tutorial. These are authoring examples, not routes
that this site publishes automatically.

Published Markmap diagrams are limited to text outlines and code. Only a finite,
nonnegative `spacingHorizontal` is allowed in frontmatter; active images, links, raw HTML
and other frontmatter fail the site's safety validation.
Use standard language-labelled fences (`bash`, `properties`, `json`, or `text`
for plain text). Inline line numbers come from the global Hugo highlight config;
ordinary documentation code blocks do not need custom filename or title headers.
For long code examples, show at least 5–9 source lines according to the reading
context. Do not fold short examples that already fit within that range; preserve
complete clipboard output, including hidden lines. Keep benchmark tables and test
conditions beside charts, and use Gallery summaries alongside detailed screenshots
when readers need to follow UI steps. Math should clarify a real documented formula.

Use terminal recordings only when timing, interactive input or changing output
adds useful information, such as a startup or troubleshooting walkthrough. Keep
the commands as copyable code; a version check alone does not need a player.
The local preview guide includes one optional player-authoring example in both
languages; it demonstrates component usage rather than replacing version checks.
Asciicast files store terminal text and timestamps, not video or executable
commands. Change the shortcode's `title` or `speed` for presentation; re-record
when commands or output change. Resize the terminal to the intended dimensions
before recording; overriding the player's `cols` or `rows` can crop the recording.

With the optional [Asciinema recorder](https://oink.pgsty.com/docs/components/asciinema/)
installed, record a real session, run the demonstration commands, then exit:

```bash
asciinema rec demo.cast
```

Save the checked recording under `static/casts/` and reference it from Markdown:

```text
{{< asciinema file="/casts/demo.cast" title="Startup walkthrough" speed="1" >}}
```

The recorder is an authoring tool, not a site build dependency. Check both desktop
and mobile playback, keep output readable, and review the plain-text file before
committing it so credentials or private output are not included.

Blog section metadata supplies default cover images and reading time; individual
articles supply real categories, tags and series order. Confirm original authorship
before creating an author profile. Keep both languages aligned, public article
routes stable, and accurate defaults; content styling is not a reason to change
commands or historical benchmark claims. Verify relevant HTML interactions and
Print/Markdown/RSS fallbacks when adopting a new content component.

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
