# OINK upgrade SOP

The theme version and its two checksums live only in `go.mod` / `go.sum`.
The historical builder and CI resolve the same module through `oink_module.py`:
site identity, sole theme dependency, no replacement/exclusion, resolved identity,
and downloaded checksums are all checked. Do not run `go mod tidy`: Hugo uses
this dependency without Go source imports.

## Upstream reference

The [OINK v1.1.0 release notes](https://github.com/pgsty/oink/releases/tag/v1.1.0)
introduce the public [sidebar state API (#41)](https://github.com/pgsty/oink/issues/41)
and [search-tail API (#40)](https://github.com/pgsty/oink/issues/40).
HugeGraph uses these instead of its previous DOM/state workarounds. The local
Print override follows the 1.1 plain/book return contract; generic Chinese UI
labels come from OINK, while site-owned labels remain in `i18n/`.
Use the tagged source when checking API details; issue proposals are background.

## Normal upgrade

Start from a clean worktree with the Go and Hugo versions documented in
[contribution.md](../contribution.md), Python 3, and Node.js satisfying
`tests/e2e/package.json`. Network access is needed for modules, archived content,
npm and Chromium. Local ports 4173, 4174 and 4175 must be available.

```sh
scripts/update-oink.sh v1.1.0
```

Use an explicit release tag. The command updates the lock files, removes old-version
checksums from `go.sum`, validates module
identity, reports upstream changes affecting customizations, then reuses the
strict build, Python/link tests, all historical builds, aggregate validation
(which validates each version artifact once),
blocking Chromium suite and visual captures. It installs the locked browser test
dependencies. It does not commit, push or publish.

A temporary `hugegraph-oink-*` directory printed at startup holds the review
report and build artifacts, including on failure. Browser failures keep the
existing Playwright report and traces. No automatic reset is performed.
A same-version run is valid. After a failed or interrupted run, retain the target
pin and resume explicitly; this accepts a dirty worktree for manual adaptations:

```sh
scripts/update-oink.sh v1.1.0 --resume
```

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
   scripts/update-oink.sh v1.1.0 --resume --accept-reviewed
   ```

   This acknowledges review; it does not bypass any tests. The baseline advances
   only after every command succeeds. If a test fails, fix its cause and rerun.
5. Inspect the visual captures under `tests/e2e/visual-results`, compare before
   and after desktop/mobile in both languages, and independently review the final
   diff before release. Automated success is not a visual approval or a promise
   of compatibility with every untested upstream change.

Get upstream directories for comparison without changing the site pin:

```sh
go mod download -json github.com/pgsty/oink@v1.0.0
go mod download -json github.com/pgsty/oink@v1.1.0
git diff --check
git diff -- go.mod go.sum layouts assets scripts .github/workflows/hugo.yml
```

## Customization map

| Customization | Local entry | Review evidence |
| --- | --- | --- |
| Version/language navigation and historical shell | `layouts/`, `scripts/versioning.py` | All-version aggregate, versioning and platform browser tests |
| Sidebar expansion memory | `assets/js/hugegraph-shell.js` | Public OinkSidebar API, storage/focus/keyboard browser tests |
| Authorized Ask AI | `assets/js/kapa-adapter.js` | Public search-tail API, adapter tests and AI browser contracts |
| Brand and layout | `assets/scss/`, `data/`, `i18n/` | Bilingual desktop/mobile, dark/light and print captures |

`scripts/oink-overrides.json` records upstream hashes, not copies of upstream
code. The generated inventory covers same-name local layouts/assets/translations/data,
the sidebar/search/surface interface files and upstream SCSS used by local CSS.
New, removed or changed upstream files in that inventory require review. Site-only
hooks are listed above; their behavior is checked by tests rather than inferred
from matching filenames. Template hashes alone never prove full compatibility.

Adding or removing a same-name local override changes the inventory even without
a theme upgrade. The read-only `--check-baseline` diagnostic names added, removed,
and changed paths. Review those changes, then run
`scripts/update-oink.sh <pinned-version> --resume --accept-reviewed` to validate
and record the revised inventory; use the version currently pinned in `go.mod`.

For this initial 1.1 migration the baseline is generated after manual review and
is accepted with the repository's full migration verification. Future runs update
it only after the same automated gates pass.

## Rollback

Keep the upgrade in a dedicated commit. To undo an already committed upgrade,
revert that commit (including adaptations and the baseline), then rerun the
restored target with `--resume`. For an uncommitted attempt, inspect `git diff`
and restore only the upgrade files from the known pre-upgrade revision; do not
reset the whole worktree or remove unrelated changes. The script never performs
either rollback automatically. Publishing remains the existing release workflow.
