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

Read the entry relevant to the task; small content edits do not require the full
upgrade or deployment workflow. Use `go.mod` / `go.sum` and CI for pinned versions.

## Project constraints

- Keep English and Chinese documentation aligned when a change applies to both.
- Preserve public routes, historical-version navigation and language switching.
- Keep HugeGraph branding and behavior in site configuration, data, hooks and
  public OINK APIs. Do not edit the module cache or vendor a theme fork.
- Record necessary upstream template overrides in the upgrade inventory; when
  upstream changes them, reconcile the customization with the new implementation.
- AI resources load only after explicit user consent; disabled AI must make no
  third-party AI requests.
- Validate behavior affected by the change. Theme/runtime changes require strict
  builds and browser checks; visual/navigation changes also need before/after
  screenshots. A rendered site alone does not prove interaction compatibility.
- Independent work may run in parallel. Review the final combined diff independently
  for changes affecting runtime behavior or multiple components; local content
  edits can use self-review.
- Local builds and disposable tests may run without repeated confirmation. Remote
  writes and publishing follow the user's explicit task scope.
