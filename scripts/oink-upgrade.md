# OINK upgrade SOP

The theme version and its two checksums live only in `go.mod` / `go.sum`.
The historical builder and CI resolve the same module through `oink_module.py`:
site identity, sole theme dependency, no replacement/exclusion, resolved identity,
and downloaded checksums are all checked. Do not run `go mod tidy`: Hugo uses
this dependency without Go source imports.

## Upstream reference

The [OINK v1.3.1 release notes](https://github.com/pgsty/oink/releases/tag/v1.3.1)
cover native Markmap text colours, footer-aware outlines, opt-in complete FileTree
comments and technical wide tables. HugeGraph uses those native implementations;
the corresponding local CSS patches have been removed. FileTree authors select
`wrap=true`; technical tables select `.td-table--wide`. Existing behavior tests
continue to check readability, keyboard access and Print after removing the patches.
Historical configuration catalogues acquire the same native wide-table marker
through the existing temporary assembly fixes. Their pinned release sources are
unchanged. When removing shared styling, inventory both published current configuration
guides and their archived predecessors: renamed successors such as
`quickstart/computing/hugegraph-computer-config` still need explicit native markers.
The 1.3 series also adds optional Expo albums and repairs navigation, Landing and
aggregate Print. See [contribution.md](../contribution.md#native-content-components)
for component selection and examples. A theme update does not create new albums.
Expo's preview, neighbor-preloading and batched-layout improvements do not change
existing Gallery fences; review the [image-loading guidance](../contribution.md#image-loading-and-albums)
before migrating content or making performance claims.

OINK 1.2 introduced independent visual-style and light/dark controls. HugeGraph retains Slate
as the default and enables the stable Paper/Slate reader menu with
`params.ui.preset_menu: true`. The public `shell/appearance-menu.html` partial is
used in the header and both mobile drawers; the theme owns dialogs, keyboard
controls, saved preferences and reading-position preservation. Ink and Terminal
remain experimental upstream and are not offered by this site.

Visible virtual Docs groups must omit `toc_hide`: OINK 1.2 applies it to the
whole navigation subtree. Their `manual_link`, `search_exclude`, `pager: false`
and `build` settings keep the grouping pages out of public content and search.

The 1.2 upgrade also reconciles 404 preset attributes and translated-only SEO
alternates with paginated blog canonicals, retaining the site's Print and error-page
exclusions. Chinese search summaries and dialog/clipboard fixes come from the theme.
Existing public sidebar-state and search-tail APIs remain the integration points.
Generic UI translations come from OINK; HugeGraph labels remain in `i18n/`.
Use tagged source when checking API details; issue proposals are background.

## Normal upgrade

Start from a clean worktree with the Go, Hugo Extended and standalone Dart Sass
versions pinned in `.github/workflows/hugo.yml`, Python 3.13, and Node.js satisfying
`tests/e2e/package.json`. Install WebP's `cwebp` and `dwebp` validators too
(`brew install webp` on macOS; CI uses the `webp` apt package). Network access is needed for modules, archived content,
npm and Chromium. Local ports 4173, 4174 and 4175 must be available.
The browser harness serves artifacts through its standard-library
`tests/e2e/serve.py` helper, with room for concurrent font and avatar requests;
no machine-local Python startup override is required.

Dart Sass must be available as `sass` on `PATH`, including its sibling `src/`
directory; a script that only prints a version is insufficient. CI reuses the local
`setup-site-tools` composite action and verifies the official Sass archive checksum.
When changing Sass, update the workflow pin and the action's verified version/checksum
together. Historical build fingerprints include the actual compiler version.
The updater checks target requirements and performs a real Hugo-to-Dart-Sass compile
before changing root locks. It never installs tools or modifies the global `PATH`.
Set `HUGO_BIN` or `PYTHON_BIN` when using a task-local toolchain.

Before changing the pin, capture the current site using its matching toolchain.
Use the same screenshot harness, viewport matrix and browser for both versions:

```sh
upgrade_dir=$(mktemp -d "${TMPDIR:-/tmp}/hugegraph-oink-review.XXXXXX")
scripts/hugo.sh build --destination "$upgrade_dir/before-site"
(
  cd tests/e2e
  npm ci
  npx playwright install chromium
  SITE_ROOT="$upgrade_dir/before-site" VISUAL_RESULTS_DIR="$upgrade_dir/before" npm run test:visual
)
# Select the target toolchain, then upgrade from the still-clean worktree.
scripts/update-oink.sh v1.3.1 --work-dir "$upgrade_dir"
```

Use an explicit release tag. The command updates the lock files, removes old-version
checksums from `go.sum`, validates module
identity, reports upstream changes affecting customizations, then reuses the
strict build, Python/link tests, all historical builds through the existing bounded
two-worker builder with independent caches and forced rebuilds, aggregate validation
(which validates each version artifact once),
blocking Chromium suite and visual captures. It installs the locked browser test
dependencies. It does not commit to a branch, push or publish.

A supplied `--work-dir` keeps the original lock backups, review report, build
artifacts and `before/` / `after/` captures together. Without it, a temporary
`hugegraph-oink-*` directory is printed at startup. Browser failures keep the
existing Playwright report and traces. No automatic reset is performed.
Use a dedicated directory outside the checkout. An initial run rejects existing
reserved output paths rather than overwriting user files; existing `before/`
captures and `before-site/` are allowed. Resume retains the first lock backup and
never regenerates baseline screenshots from the upgraded site. A fresh `--resume`
directory can only back up the already-pinned target; `review.json` states that
scope, so retain the original source or commit for rollback.
A same-version run is valid. After a failed or interrupted run, retain the target
pin and resume explicitly; this accepts a dirty worktree for manual adaptations:

```sh
scripts/update-oink.sh v1.3.1 --resume --work-dir "$upgrade_dir"
```

Local validation includes the current `content/` and `static/`, including new
non-ignored files and deletions. It creates a temporary Git index and, when needed,
an unreferenced validation commit for the existing `prepare --latest-sha` input.
It does not stage changes in your index, move HEAD or a branch, change Git
configuration, or create a publishable release. `validation-snapshot.json` records
the input and scope. The current site shell still comes from the normal overlay;
historical content remains pinned by `versions.json`. This prevents a resumed
upgrade from passing against old HEAD content while omitting local adaptations.

## Compatibility review and breaking changes

1. Read the release notes and the printed `review.json`. Its `from` version is
   the last reviewed baseline, not necessarily the previous command's target.
2. Compare each reported file in the two downloaded module directories. For
   templates, compare old upstream, new upstream, and the corresponding local
   override. Absorb upstream changes while retaining the site behavior.
3. Prefer documented configuration, hooks and public JavaScript APIs. Adapt the
   relevant integration and its behavior tests together. Do not patch module
   cache files or add a second DOM/state controller alongside the theme.
4. After reviewing every reported change, rerun the full verification:

   ```sh
   scripts/update-oink.sh v1.3.1 --resume --accept-reviewed --work-dir "$upgrade_dir"
   ```

   This acknowledges review; it does not bypass any tests. The baseline advances
   only after every command succeeds. If a test fails, fix its cause and rerun.
5. Inspect the visual captures under the work directory's `before/` and `after/`, compare before
   and after desktop/mobile in both languages, and independently review the final
   diff before release. Automated success is not a visual approval or a promise
   of compatibility with every untested upstream change.

Get upstream directories for comparison without changing the site pin:

```sh
go mod download -json github.com/pgsty/oink@v1.3.1
go mod download -json github.com/pgsty/oink@v1.2.0
git diff --check
git diff -- go.mod go.sum layouts assets scripts .github/workflows/hugo.yml
```

## Keeping upgrades small

The default workflow remains one command: `scripts/update-oink.sh <release-tag>`.
If the watched integration files are unchanged, the runner completes all checks and
records the new baseline. A reported upstream change is an impact to review, not
an instruction to rewrite every listed file. When an adaptation is necessary,
keep the pinned target, fix the affected integration and use the printed resume
command. `--accept-reviewed` acknowledges that review; it never skips validation.

The [official Module upgrade guide](https://oink.pgsty.com/docs/admin/upgrade/)
uses `hugo mod get github.com/pgsty/oink@<release-tag>`, `hugo mod tidy`, then
`hugo mod graph` and a warning-strict build without local module replacements.
`hugo mod tidy` is different from `go mod tidy`: the latter sees no Go source
imports in this Hugo site and can remove the theme. Our runner uses `go get`
and keeps exactly the two target checksums under the site's sole-theme contract.

The official tagged `bin/update-consumers.py` is useful for several consumer
sites; explicit `--sites` can select a linked worktree. Its pin/graph/build checks
do not replace this site's historical navigation, search, AI consent and browser
contracts. Use our existing runner for HugeGraph rather than running both upgrade
controllers or bypassing the site's checks.

The runner validates the release in an isolated environment: no inherited Hugo
module replacement or workspace, `GOWORK=off`, and the actual Hugo module graph
must match the pin. A local `_vendor` tree stops validation so a cached theme
cannot masquerade as the selected release. Normal preview commands retain their
local-development capabilities. Generated artifacts and failures are retained;
there is no automatic deletion of user work or rollback.

For 1.1 → 1.2, a zero-adaptation upgrade was not possible:

| Cause | Minimal local adaptation |
| --- | --- |
| The navbar override retained the old theme menu | Delegate the header and mobile drawers to the public Appearance partial |
| The local 404 and SEO partials shadowed upstream fixes | Add preset attributes; absorb true-translation and pagination SEO behavior |
| Brand CSS targeted the former menu selector | Update the two selectors for the public Appearance control |
| Virtual Docs groups had `toc_hide: true` | Remove that flag in both languages; retain all non-public grouping constraints |

The fourth issue changes navigation behavior and is caught by the browser suite,
not merely by matching override hashes. The first upgrade attempt reported 28
upstream files, largely including stylesheet dependencies; only the affected
local integrations needed adaptation. Blog taxonomy and native content components
are separate content improvements, not prerequisites for the module upgrade.

Future low-effort upgrades depend on keeping local customizations small: use
configuration, content metadata, site hooks and public APIs first. Do not copy a
shared template just to enable an existing feature. When the theme offers a public
extension point that replaces a necessary override, remove the override after
proving parity with the site's version/language/AI/keyboard behavior. Avoid a new
DOM controller or automated text migration for content that already works.

## Customization map

| Customization | Local entry | Review evidence |
| --- | --- | --- |
| Version/language navigation and historical shell | `layouts/`, `scripts/versioning.py` | All-version aggregate, versioning and platform browser tests |
| Browser language default and manual preference | `assets/js/language-preference.js`, `hooks/head-end.html` | Homepage, explicit links, storage, palette and keyboard browser tests |
| Sidebar expansion memory | `assets/js/hugegraph-shell.js` | Public OinkSidebar API, storage/focus/keyboard browser tests |
| Authorized Ask AI, remembered consent/dismissal, withdrawal and community entry | `assets/js/kapa-adapter.js`, `layouts/_partials/hooks/body-end.html`, `layouts/_partials/footer.html` | Public search-tail API, adapter tests and AI browser contracts |
| Brand and layout | `assets/scss/`, `data/`, `i18n/` | Bilingual desktop/mobile, dark/light and print captures |
| Native content components | `content/`, `assets/scss/_styles_project.scss`, `dist/validate-site-output.py` | Exact component data carriers and payload sinks; Markmap scaled text and contrast in both themes |

Markmap text and Print colours now come from OINK; do not restore a site token
override when upgrading. Component payload validation follows the pinned runtime's actual URL, HTML and
CSS sinks. Recheck those contracts when component runtimes change; an unchanged
template name does not prove that an updated runtime consumes data safely.

`scripts/oink-overrides.json` records upstream hashes, not copies of upstream
code. The generated inventory covers same-name local layouts/assets/translations/data,
the sidebar/search/surface/appearance interface files and upstream SCSS used by local CSS.
New, removed or changed upstream files in that inventory require review. Site-only
hooks are listed above; their behavior is checked by tests rather than inferred
from matching filenames. Template hashes alone never prove full compatibility.

Adding or removing a same-name local override changes the inventory even without
a theme upgrade. The read-only `--check-baseline` diagnostic names added, removed,
and changed paths. Review those changes, then run
`scripts/update-oink.sh <pinned-version> --resume --accept-reviewed` to validate
and record the revised inventory; use the version currently pinned in `go.mod`.

Hugo can fetch imports and rewrite locks even during `hugo mod graph`. The
diagnostic runs it in a sibling temporary workspace with independent lock copies,
preserving current configuration and relative paths. It explicitly uses
`--config hugo.yaml --environment production`, matching the release build
entry and ignoring a caller's development environment selection. The checkout's parent must
be writable; failure leaves the original `go.mod` and `go.sum` unchanged.

The baseline advances only after manual compatibility review and the full
automated verification pass.

The output validator checks ECharts option roots, active resource paths and
HTML/CSS sinks. Ordinary dataset columns remain data. Checked colour sources
accept literal colours, palettes, gradients and same-origin image patterns;
`$fn:` colour callbacks are unsupported because their returned colours cannot
be checked statically. Add a reviewed runtime output contract before using them.

## Rollback

Keep the upgrade in a dedicated commit. To undo an already committed upgrade,
revert that commit (including adaptations and the baseline), then rerun the
restored target with `--resume`. For an uncommitted attempt, inspect `git diff`
and restore only the upgrade files from the known pre-upgrade revision; do not
reset the whole worktree or remove unrelated changes. The script never performs
either rollback automatically. Publishing remains the existing release workflow.
