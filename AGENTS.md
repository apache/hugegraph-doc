# HugeGraph documentation

Bilingual Hugo site using OINK as a pinned Go module. English routes live under
`/docs/`, Chinese routes under `/cn/docs/`; historical releases share the current
site shell.

## Task entry points

- Preview or build: `scripts/hugo.sh server` / `scripts/hugo.sh build`.
- Content and contribution checks: [contribution.md](contribution.md).
- OINK upgrades, customization boundaries and recovery:
  [scripts/oink-upgrade.md](scripts/oink-upgrade.md).
- Version assembly and publishing: `scripts/versioning.py` and
  `.github/workflows/hugo.yml`; release selection comes from `versions.json`.
- Browser regression: `tests/e2e/package.json` and its Playwright configuration.
  Node dependencies are for tests, not the Hugo site build.
- Native content components and examples: the "Native content components" section
  of [contribution.md](contribution.md); check the pinned OINK documentation before
  adding a custom renderer, script or stylesheet.
- Image loading and album selection: [Gallery versus Expo](contribution.md#image-loading-and-albums).
  Expo's thumbnail, preloading and layout optimizations do not apply automatically to Gallery.

Read the entry relevant to the task; small content edits do not require the full
upgrade or deployment workflow. Use `go.mod` / `go.sum` and CI for pinned versions.

## Project constraints

- Keep English and Chinese documentation aligned when a change applies to both.
- Wrap new Markdown prose at 160 characters; preserve existing one-line paragraphs and use placeholders for generated IDs.
- Preserve public routes, historical-version navigation and language switching.
- When removing shared compatibility styles, check archived content against the
  current shell too. Apply necessary native component markers in the existing
  temporary historical assembly; do not rewrite release branches or add a runtime controller.
- Keep HugeGraph branding and behavior in site configuration, data, hooks and
  public OINK APIs. Do not edit the module cache or vendor a theme fork.
- Prefer native Markdown and public configuration: Cards for parallel choices,
  Steps for ordered actions, Tabs for equivalent examples, FileTree for annotated
  directories (`wrap=true` for complete comments), and `.td-table--wide` only for
  technical tables that need intact identifiers. Keep ordinary tables compact.
- Use Gallery for screenshots within an explanation and Expo for standalone image
  albums. Use Mermaid for relationships and flows, Markmap for text outlines, and
  ECharts for quantitative comparisons with source tables and test conditions.
  Adopt components where they clarify real content; keep assets local and runtimes
  loaded only where used, and check their Print/Markdown fallbacks.
- Record necessary upstream template overrides in the upgrade inventory; when
  upstream changes them, reconcile the customization with the new implementation.
- AI resources load only after explicit user consent; disabled AI must make no
  third-party AI requests.
- Validate behavior affected by the change. Theme/runtime changes require strict
  builds and browser checks; visual/navigation changes also need before/after
  screenshots. A rendered site alone does not prove interaction compatibility.
- Before pushing documentation edits, run `bash dist/validate-links.sh`. For
  title, description, keyword, route or substantial body changes, also run the
  source tests with CI's Python, Hugo Extended, Dart Sass and WebP tools; build
  and validate a fresh latest artifact. Run `tests/e2e/search-ranking.spec.js`
  when search-facing content changes; keep metadata accurate instead of
  weakening ranking checks. Small prose edits need only focused checks.
- Independent work may run in parallel. Review the final combined diff independently
  for changes affecting runtime behavior or multiple components; local content
  edits can use self-review.
- Local builds and disposable tests may run without repeated confirmation. Remote
  writes and publishing follow the user's explicit task scope.
