# OINK features used by HugeGraph

This is the authoring and integration reference for the OINK version pinned in
`go.mod`. Use native Markdown and public theme interfaces before adding a local
renderer, template, script or stylesheet. Upgrade mechanics and override review
belong in [oink-upgrade.md](oink-upgrade.md).

## Choose the component by the content

| Content | Native form | Existing HugeGraph example |
| --- | --- | --- |
| Parallel entry points | Unordered link list + `{.cards}` | [Server installation choices](../content/en/docs/quickstart/hugegraph/hugegraph-server.md) |
| Actions readers perform in order | Ordered list + `{.steps}` | [Local preview](../content/en/community/documentation.md) |
| Equivalent commands or configurations | Adjacent fences with `{tab="…"}` | [Server serializers](../content/en/docs/quickstart/hugegraph/hugegraph-server.md) |
| Annotated directories | `filetree` fence; `wrap=true` for complete comments | Use for actual directory layouts, keeping comments short |
| Technical catalogs | Table + `{.wide}`; optional `.expand` | [Configuration](../content/en/docs/config/config-option.md) |
| Architecture, dependencies or a decision flow | `mermaid` fence | [Server installation flow](../content/en/docs/quickstart/hugegraph/hugegraph-server.md) |
| Text hierarchy | `markmap` fence | [Server module outline](../content/en/docs/quickstart/hugegraph/hugegraph-server.md) |
| Quantitative comparison | `echarts` fence with its source table and test conditions | Benchmark content only when the chart clarifies a comparison |
| Screenshots inside an explanation | `gallery` fence | [Hubble screenshots](../content/en/docs/quickstart/toolchain/hugegraph-hubble.md) |
| Published release facts | `release-card` | [1.7.0 notes](../content/en/docs/changelog/hugegraph-1.7.0-release-notes.md) |

Automatic section cards already come from `params.ui.section_index: cards` and
child-page metadata. Keep that metadata accurate instead of duplicating a
section's child list. Handwritten cards suit cross-section recommendations.
Keep prerequisites and warnings visible; use a native `> [!DETAILS]- Title`
callout for supplemental detail.

## Common authoring patterns

Block attribute lines must touch the list, table or image they describe.
Fence attributes belong on the opening fence line, after the language.
The site's `markup.goldmark.parser.attribute.block: true` enables these markers.

### Cards and steps

```markdown
- [Server](/docs/quickstart/hugegraph/hugegraph-server/) — Run the database service.
- [Hubble](/docs/quickstart/toolchain/hugegraph-hubble/) — Explore and query a graph.
{.cards}

1. Install the required toolchain.
1. Clone the documentation repository.
1. Run the local preview.
{.steps}
```

OINK 1.4.0 adds compact presentation for short lists:
`{.cards .td-cards-list}` and `{.steps .td-steps-compact}`.
Select them where each item is brief; longer descriptions and nested commands
benefit from the regular layout. Cards are unordered choices; Steps express order.

### Code and tabs

Use standard language-labelled fences, including `text` for plain text. Global
Hugo highlighting supplies inline line numbers. Ordinary snippets do not need a
filename or title bar. For one short standalone command, OINK 1.4.0 supports:

````markdown
```bash {class="td-code-command" lineNos=false}
scripts/hugo.sh server
```
````

Command strips require exactly one line, no line numbers and no `collapse`.
Keep `lineNos=false` explicit because this site's global highlighting enables
line numbers.

Adjacent examples of the same settings in supported formats can become tabs
without a custom container:

````markdown
```json {tab="JSON"}
{"port": 8080}
```
```yaml {tab="YAML"}
port: 8080
```
````

Give a synchronized tab set a meaningful `group` on the first fence and a stable
`value` on every fence only when shared selection and persistence help readers.
For long code, choose enough initially visible lines for the task (usually 5–9);
do not fold short examples. Folding must preserve the complete copied source.
See [upstream code](https://oink.pgsty.com/docs/components/code/) and
[Tabs](https://oink.pgsty.com/docs/components/tabs/) for supported parameters.

### FileTree and technical tables

````markdown
```filetree {title="Store directories" wrap=true}
data/
  m/ # schema store: property keys and labels
  g/ # graph store: vertices, edges and indexes
```
````

Use `wrap=true` when readers need complete comments; keep the compact default for
short comments. Do not recreate wrapping with global CSS.

```markdown
| Option | Default | Meaning |
| --- | --- | --- |
| `auth.token_expire` | `86400` | JWT lifetime in seconds. |
{.wide .expand}
```

`.wide` preserves technical identifiers while giving descriptions room.
`.expand` adds OINK's table reader in HTML, including keyboard and close behavior;
Print, Markdown and RSS keep the complete static table. Ordinary tables should
remain compact. Existing `.td-table--wide` markers are compatible, so unrelated
pages and historical source branches need no mechanical migration.
Do not combine `.expand` with `.fields`, which renders a definition list.
See [upstream tables](https://oink.pgsty.com/docs/components/table/).

### Release cards

The release box is a native shortcode, not copied HTML. Its only source of
version and repository facts is an exact GitHub release-tag URL in front matter:

```yaml
---
title: HugeGraph 1.7.0 Release Notes
date: 2025-11-16
release_url: https://github.com/apache/hugegraph/releases/tag/1.7.0
---
```

```text
{{< release-card >}}
```

The shortcode takes no parameters. The tag supplies the displayed version,
the page's `date` supplies the release date, and OINK generates release,
source tarball/ZIP and repository links locally. Confirm the URL and date against
the actual release; do not point `release_url` at the project's download page.
The card complements HugeGraph's ASF download, signature and checksum guidance.
It also has readable Print, Markdown and RSS output.
See [release authoring](https://oink.pgsty.com/docs/write/releases/).

## Diagrams and images

Use Mermaid for relationships and flows, Markmap for text outlines, and ECharts
for numerical comparisons. OINK 1.4.0 gives existing Mermaid diagrams a shared
reader with zoom/pan, source and SVG access; authors keep the same fence syntax.
Keep required diagram resources local and let OINK load runtimes only on pages
that use them. Enable another runtime only when real content needs it.

Published Markmap content is limited to text outlines and code. Its front matter
allows only a finite, nonnegative `spacingHorizontal`; active images, links,
raw HTML and other front matter fail the site's validator. ECharts needs its
source table, units and test conditions alongside the chart. Keep options within
the URL, HTML and CSS sinks accepted by `dist/validate-site-output.py`;
`$fn:` colour callbacks require a reviewed output contract before adoption.

### Image loading and albums

Use [Gallery](https://oink.pgsty.com/docs/components/gallery/) for screenshots
within a tutorial. Give images meaningful alternative text and captions; keep
assets local and avoid repeating the same screenshot at full width.

Use [Expo](https://oink.pgsty.com/docs/write/expo/) only for a standalone album:
a section with `type: expo` and `cascade: {type: expo}`, with leaf bundles
containing `index.md` and local images. Resource metadata owns captions,
credits and ordering. Add the matching Chinese bundle when adopting an album.

Expo supplies wall, masonry and seamless layouts. Processable local images get
WebP previews fitted within 960 × 960 pixels when either dimension exceeds 960
or the source is a GIF; otherwise they reuse the original. The viewer retains
the original, uses its cached preview while loading, and preloads one neighbor
on either side. The first four album tiles load eagerly (the first with high
priority), later tiles lazily; layout batches geometry work and uses known sizes.

Gallery has native lazy loading, asynchronous decoding and the shared viewer;
Expo's generated previews, neighboring-original preload and album layout work
do not apply to Gallery. Supply intrinsic `width` and `height` on standalone
Markdown images to reserve space; those attributes do not compress the file.
Inspect generated HTML and measure bytes/timing before claiming an improvement.
See the [tagged Expo implementation](https://github.com/pgsty/oink/blob/v1.4.0/layouts/_partials/expo/items.html).

### Terminal recordings

Use the optional [Asciinema recorder](https://oink.pgsty.com/docs/components/asciinema/)
when timing or interactive output helps, such as a startup walkthrough. Keep
commands copyable. A simple version check needs no player.

Record a real session with `asciinema rec demo.cast`, run the commands and exit.
Store the reviewed recording in `static/casts/`, then use:

```text
{{< asciinema file="/casts/demo.cast" title="Startup walkthrough" speed="1" >}}
```

Recordings contain terminal text and timestamps. Review them for credentials and
private output. Re-record when commands/output change; change `title` or `speed`
only for presentation. Resize the terminal before recording: overriding player
`cols`/`rows` can crop it. Check desktop and mobile playback.
The recorder is an authoring tool, not a build dependency.

## Site integration and output checks

- `hugo.yaml` owns appearance, search and output configuration. Four style
  presets are selected with `params.ui.preset_menu: [paper, slate, ink, terminal]`;
  boolean `true` offers only Paper/Slate. Ink and Terminal are experimental.
  Style and light/dark mode are independent; OINK owns saved preferences.
- Header and mobile drawers use the public `shell/appearance-menu.html` partial.
  Sidebar persistence uses `OinkSidebar`; AI integration uses the public
  search-tail API. Keep HugeGraph consent, version/language scope and local
  availability behavior in their existing hooks/adapters.
- Local search uses `params.offline_search_index: content` so configuration names,
  error messages and other body-only terms are searchable in both languages.
  OINK loads the current language's index on demand; full content increases its
  size and first-search initialization cost. Keep accurate titles, descriptions
  and keywords for ranking. Run `tests/e2e/search-ranking.spec.js`, which preserves
  the 24 metadata cases and separately checks 11 body-only queries with real
  result clicks. Do not add keywords or boosts merely to satisfy body queries.
- Blog sections provide default covers and reading-time metadata; articles own
  their real tags, categories and series order. Confirm authorship before adding
  an author profile. `blog_index: cards` is a card index; it is distinct from
  `blog_index: gallery` with `blog_gallery.mode: cards` (a masonry gallery).
  Keep the current index until article imagery justifies another layout.
- Keep English/Chinese content and stable public routes aligned. Component styling
  is not a reason to change executable commands or historical benchmark claims.
- Check affected HTML interaction, keyboard/mobile behavior and Print/Markdown
  fallbacks. Check RSS where the component appears in a feed. A successful Hugo
  render alone does not establish compatibility.

The [1.4.0 release notes](https://oink.pgsty.com/zh/blog/release/1.4.0/) and
[tagged source](https://github.com/pgsty/oink/tree/v1.4.0) are the reference for
this upgrade. Consult the pinned release before extending a component; the
upstream website can describe a newer version.
