# OINK upgrade SOP

OINK is the site's sole theme module. Its version and two checksums live in
`go.mod` / `go.sum`; CI and historical builds use the same locks through
`oink_module.py`. Keep site changes in configuration, data, hooks and public APIs.
Do not edit the module cache, vendor a fork or run `go mod tidy` (there are no Go
source imports, so it can remove the theme).

## Toolchain and upstream guidance

Use the Hugo Extended version pinned in `.github/workflows/hugo.yml`, the Go
version in `go.mod`, Python 3.13, WebP's `cwebp` / `dwebp`, and Node satisfying
`tests/e2e/package.json`. Node is only for browser tests. OINK 1.5.1 requires
Hugo Extended 0.168.0 and Go 1.27.3; Hugo's built-in LibSass compiles the site,
so no standalone Dart Sass or npm site-build dependencies are needed.
Set `HUGO_BIN` / `PYTHON_BIN` for task-local tools.

Read the target release notes and the [official upgrade guide](https://oink.pgsty.com/zh/docs/admin/upgrade/).
For [OINK 1.5.1](https://github.com/pgsty/oink/releases/tag/v1.5.1), keep LibSass deprecation
warnings visible: do not add `--panicOnWarning` or suppress the warning through
`ignoreLogs`. The shared `scripts/hugo_build.py` runner streams the full output
and permits only that exact LibSass warning; every other Hugo `WARN`, including
missing translations and duplicate target paths, fails production builds. The
same gate covers local, versioned and AI fixture builds. Build errors,
source/output validation and browser contracts remain blocking.

The official Module sequence is `hugo mod get`, `hugo mod tidy`, `hugo mod graph`
and a production build. Our runner adds HugeGraph's module identity, historical
navigation, search, consent and browser checks to that workflow. Its `go get`
and checksum cleanup preserve the site's sole-theme contract. Use the existing
runner; the upstream multi-consumer updater is unnecessary for this one site.

## Upgrade and review

Start with a clean worktree and capture the current site with its matching
toolchain. Network access is needed for modules, archived content, npm and
Chromium; ports 4173–4175 must be free.

```sh
upgrade_dir=$(mktemp -d "${TMPDIR:-/tmp}/hugegraph-oink-review.XXXXXX")
scripts/hugo.sh build --destination "$upgrade_dir/before-site"
(
  cd tests/e2e
  npm ci
  npx playwright install chromium
  SITE_ROOT="$upgrade_dir/before-site" VISUAL_RESULTS_DIR="$upgrade_dir/before" npm run test:visual
)
# Select the target toolchain, then use an explicit release tag.
scripts/update-oink.sh v1.5.1 --work-dir "$upgrade_dir"
```

The single command checks target tool requirements and a real Hugo/LibSass
compilation before changing locks. It then updates the pin, removes old
checksums, verifies Go/Hugo module identity and reports watched upstream changes
in `review.json`. With no review impacts it runs all checks and records the
new override baseline. It never installs tools, commits, pushes or publishes.

When upstream changes affect local integrations, compare the old upstream, new
upstream and local override. Adapt only affected behavior, then resume:

```sh
scripts/update-oink.sh v1.5.1 --resume --accept-reviewed --work-dir "$upgrade_dir"
```

`--accept-reviewed` acknowledges the reported compatibility review; it skips no
validation. A failed run retains the target pin, artifacts, Playwright report and
traces. Fix the cause and resume in the same directory. A same-version run also
validates changes to local overrides. The baseline advances only after all
checks pass. Inspect bilingual desktop/mobile before/after captures and obtain
an independent combined-diff review before publishing.

## Validation and reuse

The runner reuses existing link checks, Python source tests, production build,
bounded two-worker version builder, aggregate validator, blocking Chromium suite
and visual harness. It checks every selected version. Latest always rebuilds;
archived artifacts can be reused only when source, shared shell, toolchain,
origins and year fingerprints plus file digests match. Restored artifacts are
validated again. A theme or shell change invalidates those receipts automatically;
a browser-only repair can resume without recompiling unchanged archives.

CI derives build groups from `versions.json`: adding a version needs no copied
job/action. A compatible historical bundle uses one warm group even when only
some per-version keys match; a fully cold shell uses at most three groups of
two workers. Compatibility lookup uses a shared-input prefix, while each
artifact still needs its exact version key, digest and validation before reuse.
Theme, Hugo, branding or version-menu changes correctly rebuild archives:
their static HTML shares the current shell. Updating ordinary latest Docs
content or browser/source tests leaves historical content reusable.

Validation includes current `content/` and `static/` changes, including
non-ignored new files and deletions, using a temporary index and (if needed) an
unreferenced validation commit. It does not stage files or move HEAD/branches.
`validation-snapshot.json` records that scope; historical sources remain pinned
by `versions.json`.

Release checks disable inherited Hugo replacements and preview themes, set
`GOWORK=off` / `HUGO_MODULE_WORKSPACE=off`, and reject `_vendor`. A correct
`go.mod` alone cannot prove Hugo used the selected theme. Read-only
`--check-baseline` uses disposable locks in a sibling workspace so Hugo's graph
initialization cannot rewrite the checkout; the parent directory must be writable.
Normal preview commands retain local-development capabilities.

Manual CI dispatches inspect the immutable candidate's theme pin before scheduling
builds. OINK 1.3.0 manual candidates are outside this workflow's supported scope;
OINK 1.3.1 requires standalone Dart Sass. Both pins are rejected by the current
workflow; upgrade such a candidate to OINK 1.5.1 first.
This restriction concerns the candidate's theme, not historical documentation:
archived content continues to use the current site shell.

Reuse the same external work directory to preserve the first lock/inventory
backup, `review.json`, `toolchain.json`, build artifacts and captures. Initial
runs reject reserved outputs instead of overwriting user files; existing
`before/` captures and `before-site/` are allowed. Resume never regenerates
baseline screenshots. A fresh `--resume` directory backs up the already-pinned
target, which `review.json` explicitly records.

## Duo View acceptance matrix

Use the product names **OINK**, **Duo View / 双列视图** and **Sync Scroll /
同步滚动** consistently. API names such as `params.ui.compare`,
`compare_translations` and `window.OinkComparePane` stay unchanged.

The blocking browser suite uses real generated content and the aggregate
artifact. `tests/e2e/duo-view.spec.js` covers this route formula for every
selected version, both languages and both responsive layouts:

| Version | English | Chinese | Desktop | Mobile |
| --- | --- | --- | --- | --- |
| latest | `/docs/` | `/cn/docs/` | two panes at 1440×900 | one visible pane at 390×844 |
| 1.7 | `/versions/1.7/docs/` | `/versions/1.7/cn/docs/` | same | same |
| 1.5 | `/versions/1.5/docs/` | `/versions/1.5/cn/docs/` | same | same |
| 1.3 | `/versions/1.3/docs/` | `/versions/1.3/cn/docs/` | same | same |
| 1.0 | `/versions/1.0/docs/` | `/versions/1.0/cn/docs/` | same | same |

The detailed interaction path is the real HugeGraph Server quick-start pair; it
checks lazy loading, the page entry, Command Palette action, `B`, Sync Scroll,
continuous scrolling, fragment links, iframe isolation, reload, Back/Forward,
reading-position recovery and third-party request suppression. The real
ToplingDB Blog pair checks Blog/search/Print/Markdown/RSS coexistence. The
Chinese-only 0.10.4 release note checks that a missing translation has no entry
or command. A controlled failed pane checks the 15-second timeout contract,
accessible Retry and successful recovery.

OINK supports Docs, Book and Blog through the same native discovery partial.
HugeGraph currently publishes no Book section, so do not add synthetic or
machine-translated Book content merely to manufacture coverage. The exact
OINK module lock and reviewed upstream inventory preserve Book support for the
first real bilingual Book page; upstream owns draft, non-HTML and `build.render`
filtering. Consumer tests concentrate on HugeGraph's real routes and hook
integrations rather than copying OINK's fixture suite.

Visual CI captures English and Chinese Duo View at desktop and mobile sizes.
Review those images together with ordinary navigation, search, appearance and
content captures. No comparison runtime or peer page may be requested before a
user opens Duo View.

## Staging, release and rollback

A pull request builds the full aggregate but does not publish. After the same
commit exists on an ASF repository branch, run **Build and deploy site** from
ASF `master` with:

```text
operation: staging-next
scope: full
candidate_branch: <ASF branch containing the candidate commit>
confirmation: publish asf-staging-oink
```

Verify `https://hugegraph-oink.staged.apache.org/` with the complete matrix,
canonical/hreflang, version switching, search, Kapa consent, Print/RSS and the
visual artifact. Do not run `production-history-refresh` and do not publish
`asf-site` without separate authorization. An ORG-only branch cannot satisfy
this Staging gate because the privileged workflow resolves `candidate_branch`
inside the ASF repository.

Record the pre-upgrade commit and the candidate commit before Staging. Recovery
is deliberately symmetric:

1. **Before merge or publication:** restore `go.mod`, `go.sum`, `hugo.yaml`,
   the reviewed overrides and compatibility changes from the recorded
   pre-upgrade commit, then rerun the complete PR suite.
2. **After merge but before Production:** revert the focused upgrade commit on
   an ASF branch and dispatch `staging-next` with `scope: full` for that revert.
   Verify all five versions before merging the revert.
3. **After a future Production publication:** merge the tested revert through
   the normal ASF review flow and let the existing `master` deployment restore
   `asf-site`; never force-update a publish branch or reuse an unverified cached
   artifact.

The legacy `netlify.toml` is not consumed by the ASF/GitHub Actions historical
builder and is removed from archived assemblies. It remains aligned with the
locked Go/Hugo versions for optional local/Netlify previews, without
`--panicOnWarning`; the GitHub workflow is the deployment authority.

## Customization review map

| Integration | Local entry | Required evidence |
| --- | --- | --- |
| Version/language navigation, historical shell | `layouts/`, `scripts/versioning.py` | All-version aggregate and navigation/browser contracts |
| Language preference and sidebar memory | `language-preference.js`, `hugegraph-shell.js`, head hook | Storage, focus, keyboard and public OinkSidebar API |
| Ask AI consent and community entry | `hugo.yaml`, AI config partial, `kapa-adapter.js`, body/footer hooks | Enabled/disabled AI fixtures, public search-tail API |
| Branding and appearance | `assets/scss/`, `data/`, `i18n/` | Four presets, light/dark, bilingual desktop/mobile and Print |
| Native content | `content/`, output validator | Component behavior, actual payload sinks, Print/Markdown fallbacks |

`scripts/oink-overrides.json` stores upstream hashes, not copied source. The
inventory covers same-name local layouts/assets/translations/data, watched
sidebar/search/surface/appearance interfaces and upstream SCSS selectors used
locally. Added/removed/changed entries require review; unchanged hashes do not
prove interaction compatibility. After adding/removing an override, use
`scripts/update-oink.sh <pinned-version> --resume --accept-reviewed` to validate
and record the inventory.

Use [OINK features](oink-features.md) for native component selection and real
site examples. Prefer native configuration/components over a copied template,
CSS patch or second DOM controller. When removing shared styles, also check
archived content in its temporary assembly; do not rewrite release branches.
Visible virtual Docs groups must omit `toc_hide`, which hides whole subtrees.

## Recovery

Keep upgrade/adaptations/baseline in a dedicated commit. Revert that commit to
undo a committed upgrade, then validate the restored version with `--resume`.
For an uncommitted run, inspect the diff and restore only upgrade files from the
known pre-upgrade revision or the first work-directory backup. Do not reset
unrelated work. The runner does not roll back automatically. Publication uses
the existing release workflow.
