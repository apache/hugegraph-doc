# OINK upgrade SOP

OINK is the site's sole theme module. Its exact release and checksums live in `go.mod` / `go.sum`; latest and historical builds consume the same locks
through `oink_module.py`. Keep HugeGraph customizations in configuration, data, hooks and public OINK APIs. Do not edit the module cache, vendor a fork,
copy the Duo View implementation, or run `go mod tidy`: this repository has no Go source imports, so `tidy` can remove the theme module.

This document uses the upstream product names consistently:

- **OINK 1.5.1** is the theme release.
- **Duo View** is the English feature name; the Chinese UI label is **双列视图**.
- **Sync Scroll** is the English control; the Chinese UI label is **同步滚动**.

## Toolchain and upstream guidance

OINK 1.5.1 requires Hugo Extended 0.168.0 and Go 1.27.3. Hugo's built-in LibSass compiles the site, so no standalone Dart Sass or npm site-build
dependency is needed. Use Python 3.13, WebP's `cwebp` / `dwebp`, and a Node version satisfying `tests/e2e/package.json`; Node is used only by browser tests.
The pinned versions live in `.github/workflows/hugo.yml`, `go.mod`, and the local/legacy preview configuration. Set `HUGO_BIN`, `GO_BIN`, or `PYTHON_BIN`
only for task-local tools.

Read the [OINK 1.5 upgrade guide](https://oink.pgsty.com/zh/docs/admin/upgrade/#preparing-1-5) and the
[OINK 1.5.1 release notes](https://github.com/pgsty/oink/releases/tag/v1.5.1) before changing the lock. Keep LibSass deprecation warnings visible: do not add
`--panicOnWarning` or suppress them through `ignoreLogs`. The shared `scripts/hugo_build.py` runner permits only the known LibSass warning; every other Hugo
`WARN`, including missing translations and duplicate target paths, remains blocking.

The upstream generic Module sequence includes `hugo mod get`, `go mod tidy`, `hugo mod graph`, and a production build. HugeGraph's updater deliberately replaces
that sequence: it changes the exact pin, preserves the theme requirement, prunes only stale OINK checksums, verifies the published module graph, runs the full
site/version/browser checks, and updates the reviewed override inventory.

## Duo View scope and route matrix

Set `params.ui.compare: true` once. OINK then discovers only real, same-origin HTML translations for page types `docs`, `book`, and `blog`. It supplies the page
entry button, Command Palette action, `B` shortcut, lazy reader runtime, Sync Scroll, history/state restoration, mobile pane switcher, failure/retry UI, and
accessibility behavior. HugeGraph must not add a second comparison component or route map.

HugeGraph currently publishes translated Docs and Blog pages but no real Book content tree. Book remains enabled through the native OINK type support; browser
verification starts when actual translated Book pages exist. Do not create fixture-like production Book pages merely to satisfy a matrix.

| Release | English Docs | Chinese Docs | Blog | Book |
| --- | --- | --- | --- | --- |
| latest | `/docs/…` | `/cn/docs/…` | `/blog/…` and `/cn/blog/…` | No published HugeGraph Book route |
| 1.7 | `/versions/1.7/docs/…` | `/versions/1.7/cn/docs/…` | Shared latest Blog, not archived | No published HugeGraph Book route |
| 1.5 | `/versions/1.5/docs/…` | `/versions/1.5/cn/docs/…` | Shared latest Blog, not archived | No published HugeGraph Book route |
| 1.3 | `/versions/1.3/docs/…` | `/versions/1.3/cn/docs/…` | Shared latest Blog, not archived | No published HugeGraph Book route |
| 1.0 | `/versions/1.0/docs/…` | `/versions/1.0/cn/docs/…` | Shared latest Blog, not archived | No published HugeGraph Book route |

For each real pair, validate both language entry routes. Desktop widths at or above OINK's 900 px breakpoint show two panes; narrower viewports show one
pane and native language tabs. A page with no real peer, a draft peer, a `build.render: link/never/false` peer, a non-HTML peer, or a later Blog archive page
must not show Duo View. Print, Markdown and RSS outputs must never carry the reader.

Sync Scroll intentionally uses approximate alignment when heading IDs differ. Improve explicit shared heading IDs only on important pages where evidence shows a
poor reading experience; do not rewrite the documentation tree as part of a theme upgrade.

## Upgrade and review

Start from a clean worktree and capture the pre-upgrade OINK 1.4.0 site with its matching toolchain. Network access is needed for modules, archived content, npm
and Chromium; ports 4173-4175 must be free.

```sh
upgrade_dir=$(mktemp -d "${TMPDIR:-/tmp}/hugegraph-oink-review.XXXXXX")
scripts/hugo.sh build --destination "$upgrade_dir/before-site"
(
  cd tests/e2e
  npm ci
  npx playwright install chromium
  SITE_ROOT="$upgrade_dir/before-site" VISUAL_RESULTS_DIR="$upgrade_dir/before" npm run test:visual
)

scripts/update-oink.sh v1.5.1 --work-dir "$upgrade_dir"
```

The updater first resolves target metadata and performs a real Hugo Extended/LibSass smoke compilation without changing locks. It then updates `go.mod` and
`go.sum`, verifies that `github.com/apache/hugegraph-doc` imports only published `github.com/pgsty/oink@v1.5.1`, and compares the reviewed upstream inventory in
`scripts/oink-overrides.json`.

When `review.json` reports an affected local integration, compare the old upstream implementation, OINK 1.5.1, and the HugeGraph override. Adapt only behavior
that is actually affected, then resume in the same work directory:

```sh
scripts/update-oink.sh v1.5.1 --resume --accept-reviewed --work-dir "$upgrade_dir"
```

`--accept-reviewed` acknowledges the compatibility review; it skips no validation. A failed run retains locks, logs, Playwright traces, captures and the first
pre-upgrade backup. A same-version run validates later fixes against the same OINK release. The override baseline advances only after the required checks pass.

## Compatibility review map

| Integration | Local entry | Required evidence |
| --- | --- | --- |
| Navbar, mobile drawer and keyboard help | `layouts/_partials/navbar.html` | OINK 1.5.1 navbar semantics, desktop/mobile utilities and version links |
| Page actions and Command Palette | `layouts/_partials/actions/manifest.html` | Page-scoped `compare_translations` availability and no cache leakage |
| Language preference / historical shell | `language-preference.js`, `hugegraph-shell.js`, `layouts/` | No duplicate controllers; language/version/history |
| Kapa AI and consent | `kapa-adapter.js`, body/footer hooks, project SCSS | No duplicate widget, consent, request or floating launcher inside panes |
| SEO and language targets | `seo-alternates.html`, `language-targets.html` | Canonical/hreflang only for real translations across current and archived Docs |
| Branding and appearance | `assets/scss/`, `data/`, `i18n/` | Light/dark, presets, Print and mobile; pane content remains usable |
| Historical assembly and cache | `versioning.py`, `version_cache.py`, `versions.json` | Five-version aggregate; theme/toolchain invalidates archived caches |
| Native content outputs | `content/`, output validator | Docs/Blog, draft/missing peers, HTML-only entry, Print/Markdown/RSS isolation |

A Duo View iframe is an ordinary same-origin page. Preserve content-level runtimes such as tables, tabs and diagrams, but suppress HugeGraph's top-level shell,
language preference controller and Kapa initialization inside `window.OinkComparePane`. Do not disable all scripts in the pane.

`scripts/oink-overrides.json` stores upstream hashes, not copied source. Its inventory includes same-name local overrides, upstream SCSS selectors consumed by
project styles, and watched public interfaces. Added, removed, or changed hashes require review; unchanged hashes alone do not prove interaction compatibility.

## Required validation

Run the updater's complete validation and retain its report. At minimum, the evidence must include:

1. Exact locks: OINK `v1.5.1`, both `go.sum` entries, Hugo Extended 0.168.0, Go 1.27.3, and built-in LibSass.
2. Source/link tests and a production Hugo build with no new warning class.
3. The five-version aggregate with English and Chinese Docs routes shown in the matrix above.
4. Real latest Docs and Blog pairs opened from both languages; the published Chinese 0.12.0 release notes page must not offer Duo View because its English peer
   is still a draft.
5. Page button, Command Palette, `B`, close/reopen, Back/Forward, refresh restoration, reading-position restoration, fragment navigation, Sync Scroll and
   continuous scrolling.
6. Desktop two-pane and mobile single-pane/tab behavior, light/dark themes, Print, RSS, Markdown, search, version switching and Kapa coexistence.
7. Lazy loading: before opening, no translated page or `document-compare.js` request; inside panes, no duplicate Kapa load or HugeGraph top-level controllers.
8. Failure, Retry and direct-link fallback, keyboard focus, dialog name, pane titles and reduced-motion behavior.
9. Before/after desktop Duo View captures, mobile captures, and a short Sync Scroll GIF. Use real HugeGraph pages, not only generated fixtures.
10. An independent combined-diff review covering correctness, native reuse, security/CSP, performance and over-design.

OINK's release fixtures cover Docs/Book/Blog discovery, draft/non-HTML filtering, output isolation, lazy assets, pane runtime classification and reader
geometry. HugeGraph's Playwright suite adds real content, historical paths, local override behavior and product integration. Review both layers; neither
replaces the other.

## Cache and build behavior

Latest always rebuilds. Historical artifacts may be reused only when their source, current shared shell, theme lock, Hugo/Go toolchain, origins, year
fingerprints and file digests match. A change to `go.sum`, OINK inventory, shared layouts, styles or shell scripts invalidates the relevant cache receipts;
every restored artifact is validated again. Browser-only fixes may reuse unchanged compiled archives.

Release checks clear Hugo replacements and preview themes, set `GOWORK=off` and `HUGO_MODULE_WORKSPACE=off`, and reject `_vendor`. A correct `go.mod` is not
proof that Hugo used the selected module; the module graph and rendered artifacts are both checked.

`netlify.toml` is retained only for legacy/ad-hoc previews. ASF staging and production use `.github/workflows/hugo.yml`; Netlify settings must not become a
second release authority.

## Staging release gate

Do not publish Production as part of an upgrade PR. After the candidate branch exists in the ASF repository and PR CI passes, dispatch **Build and deploy site**
from ASF `master` with the immutable candidate branch and these inputs:

```text
operation: staging-next
scope: full
candidate_branch: <ASF candidate branch>
confirmation: publish asf-staging-oink
```

`scope: full` is required for this upgrade because the current theme is applied to latest plus 1.7, 1.5, 1.3 and 1.0. Verify the staged origin's English/Chinese
route matrix, same-origin iframe policy, canonical/hreflang, search, Kapa consent, Print/RSS/Markdown outputs, desktop/mobile behavior and captures. Record the
candidate commit and the workflow run; a local build or ORG-only branch is not an ASF Staging pass.

Production remains a separate authorized operation. Do not dispatch `production-history-refresh` and do not update `asf-site` until Staging evidence is accepted
and explicit Production approval is given.

## Rollback

Keep the version lock, compatibility fixes, tests and reviewed baseline in one focused upgrade commit or a small contiguous commit series.

### Before Production

1. Revert the complete upgrade commit/series; do not reset unrelated work.
2. Confirm `go.mod`, `go.sum`, `hugo.yaml` and `scripts/oink-overrides.json` are back to the OINK 1.4.0 state.
3. From a clean worktree, run a same-version validation with a new work directory:

   ```sh
   rollback_dir=$(mktemp -d "${TMPDIR:-/tmp}/hugegraph-oink-rollback.XXXXXX")
   scripts/update-oink.sh v1.4.0 --work-dir "$rollback_dir"
   ```

4. Run the full five-version browser matrix and publish only to Staging with `scope: full`.
5. Compare the staged rollback against the retained pre-upgrade captures before any Production decision.

### Uncommitted recovery

Use the first updater work-directory backup or `git restore --source=<known-pre-upgrade-commit>` for only the upgrade-owned files. Do not use a broad hard
reset.
The updater does not roll back automatically.

### After Production

Use the repository's normal git revert and release workflow; never patch generated `asf-site` content by hand. Rebuild all five versions from the reverted
source, validate Staging, then publish Production only with the same explicit authorization used for the original release. Retain both release workflow run
IDs and the rollback commit for auditability.
