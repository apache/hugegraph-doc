#!/usr/bin/env python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0.

"""Explicit, review-gated OINK upgrades using the existing site validators."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
import re
import shlex
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile

from hugo_build import is_unexpected_warning
from oink_module import MODULE, SITE_MODULE, VERSION, command, download_locked, locked_version

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "scripts/oink-overrides.json"
WATCH = ("assets/js/sidebar-state.js", "assets/js/sidebar-nav.js",
         "assets/js/docs-shell.js", "assets/js/search.js", "assets/js/search-engine.js",
         "assets/js/surface-coordinator.js", "assets/js/command-palette.js",
         "assets/js/appearance.js", "assets/js/dark-mode.js",
         "layouts/_partials/shell/appearance-menu.html",
         "layouts/_partials/preset-config.html", "layouts/_partials/dark-mode-config.html")


def run(args, *, cwd=ROOT, env=None):
    print("+ " + " ".join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, env=env, check=True)


def release_environment():
    """Release checks must use the published module, never a local preview."""
    env = dict(os.environ)
    env.pop("HUGO_MODULE_REPLACEMENTS", None)
    env.pop("HUGO_THEME", None)
    # LibSass emits an expected deprecation warning; release checks retain it.
    env.pop("HUGO_PANICONWARNING", None)
    env.update(GOWORK="off", HUGO_MODULE_WORKSPACE="off")
    # Version assembly changes cwd; relative HUGO_BIN paths would stop working.
    hugo = env.get("HUGO_BIN")
    executable = shutil.which(hugo) if hugo else None
    if executable:
        env["HUGO_BIN"] = str(Path(executable).resolve())
    return env


@contextmanager
def isolated_release():
    original = dict(os.environ)
    isolated = release_environment()
    try:
        os.environ.clear()
        os.environ.update(isolated)
        yield
    finally:
        os.environ.clear()
        os.environ.update(original)


@contextmanager
def graph_workspace(root):
    """Give Hugo disposable locks while preserving relative config/import paths.

    Hugo's graph command can fetch configured imports and rewrite both locks.
    A sibling workspace keeps parent-relative paths unchanged; link project
    inputs to their current files and copy the two writable root lock files.
    """
    root = Path(root).resolve()
    with tempfile.TemporaryDirectory(prefix="hugegraph-oink-graph-", dir=root.parent) as directory:
        workspace = Path(directory)
        for entry in root.iterdir():
            destination = workspace / entry.name
            if entry.name in {"go.mod", "go.sum"}:
                shutil.copy2(entry, destination)
            else:
                destination.symlink_to(entry, target_is_directory=entry.is_dir())
        yield workspace


def verify_hugo_graph(root, version):
    if (root / "_vendor").exists():
        raise ValueError("_vendor is unsupported by this module-only updater; move it aside and rerun, or refresh and review it separately")
    env = release_environment()
    with graph_workspace(root) as workspace:
        graph = subprocess.check_output([env.get("HUGO_BIN", "hugo"), "mod", "graph",
                                         "--config", "hugo.yaml", "--environment", "production", "--quiet"],
                                        cwd=workspace, env=env, text=True)
        graph = graph.replace(str(workspace), str(Path(root).resolve()))
    expected = MODULE + "@" + version
    edges = [line.split() for line in graph.splitlines() if line.strip()]
    root_imports = [tokens[1] for tokens in edges if len(tokens) == 2 and tokens[0] == SITE_MODULE]
    nodes = [token for tokens in edges for token in tokens
             if token == MODULE or token.startswith(MODULE + "@")]
    # Check every root import: an additional local theme can supply unpublished
    # templates even when the pinned OINK edge itself is correct. Dependencies
    # imported by OINK (and their transitive edges) remain valid.
    if (root_imports != [expected] or not nodes or any(node != expected for node in nodes)
            or any(len(tokens) != 2 for tokens in edges)):
        raise ValueError(f"expected Hugo root {SITE_MODULE} to import only published {MODULE}@{version}; actual graph: {graph}")
    return graph


def prior_release(root, version):
    with graph_workspace(root) as workspace:
        module = json.loads(command(["mod", "download", "-json", MODULE + "@" + version], workspace))
    if module.get("Error") or module.get("Version") != version or not module.get("Dir"):
        raise ValueError(f"cannot resolve reviewed previous release: {module}")
    return module


def snapshot(root, upstream):
    paths = set(WATCH)
    # Project SCSS depends on upstream selectors even without a same-name override.
    paths.update(str(p.relative_to(upstream)) for p in (upstream / "assets/scss").rglob("*.scss"))
    for folder in ("layouts", "assets", "i18n", "data"):
        def key(relative):
            name = relative.as_posix()
            # Locale filenames are case-insensitive; record the upstream spelling
            # rather than letting the host filesystem decide which file matches.
            return name.casefold().replace("_", "-") if folder == "i18n" else name

        upstream_paths = {key(p.relative_to(upstream)): p.relative_to(upstream).as_posix()
                          for p in (upstream / folder).rglob("*") if p.is_file()}
        paths.update(upstream_paths[key(p.relative_to(root))]
                     for p in (root / folder).rglob("*")
                     if p.is_file() and key(p.relative_to(root)) in upstream_paths)
    return {p: hashlib.sha256((upstream / p).read_bytes()).hexdigest()
            if (upstream / p).is_file() else None for p in sorted(paths)}


def changes(previous, current):
    return [p for p in sorted(previous.keys() | current.keys()) if previous.get(p) != current.get(p)]


def describe_changes(previous, current):
    return [f"{change_kind(previous, current, p)}: {p}"
            for p in changes(previous, current)]


def change_kind(previous, current, path):
    return "added" if previous.get(path) is None else "removed" if current.get(path) is None else "changed"


def prune_checksums(root, version):
    """Keep only target checksums after go get; do not use go mod tidy."""
    path = root / "go.sum"
    lines = [line for line in path.read_text().splitlines()
             if line.split()[:2] in [[MODULE, version], [MODULE, version + "/go.mod"]]]
    if len(lines) != 2 or len({line.split()[1] for line in lines}) != 2:
        raise ValueError(f"expected both target checksums before cleanup: {MODULE}@{version}")
    path.write_text("\n".join(lines) + "\n")


def preflight(root, target, resume):
    if not VERSION.fullmatch(target):
        raise ValueError("use an explicit release such as v1.1.0; branches and latest are not accepted")
    if (root / "_vendor").exists():
        raise ValueError("_vendor is unsupported by this module-only updater; move it aside and rerun, or refresh and review it separately")
    if resume:
        if locked_version(root) != target:
            raise ValueError("--resume only validates the already-pinned target; it cannot switch versions")
    elif subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip():
        raise ValueError("working tree is not clean; commit/stash your work first, or use --resume for this pinned target")


def version_tuple(value):
    match = re.search(r"(?<![0-9])(\d+)\.(\d+)\.(\d+)(?![0-9])", value)
    if not match:
        raise ValueError(f"cannot identify tool version: {value!r}")
    return tuple(map(int, match.groups()))


def tool_output(argv):
    try:
        return subprocess.check_output(argv, env=release_environment(), text=True,
                                       stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        detail = getattr(error, "output", None) or str(error)
        raise ValueError(f"toolchain command {' '.join(argv)} failed: {detail}; "
                         "prepare the tools in scripts/oink-upgrade.md and rerun with the same --work-dir") from None


def tool_versions():
    return {"hugo": tool_output([release_environment().get("HUGO_BIN", "hugo"), "version"]),
            "go": tool_output([os.environ.get("GO_BIN", "go"), "version"]),
            "webp": tool_output(["cwebp", "-version"])}


def check_toolchain(root, target):
    """Resolve target metadata and compile in disposable roots before changing locks."""
    try:
        import tomllib
    except ImportError:
        raise ValueError("OINK upgrades require Python >= 3.11; use Python 3.13 as documented in scripts/oink-upgrade.md") from None
    module = prior_release(root, target)
    upstream = Path(module["Dir"])
    minimum = max((0, 168, 0), version_tuple(tomllib.loads((upstream / "theme.toml").read_text())["min_version"]))
    versions = tool_versions()
    if version_tuple(versions["hugo"]) < minimum or "+extended" not in versions["hugo"]:
        raise ValueError(f"Hugo Extended >= {'.'.join(map(str, minimum))} is required for {target}; "
                         f"found {versions['hugo']}. Prepare tools using scripts/oink-upgrade.md; locks are unchanged")
    directive = re.search(r"(?m)^go\s+(\d+)\.(\d+)(?:\.(\d+))?\s*$", (upstream / "go.mod").read_text())
    if not directive:
        raise ValueError(f"cannot identify target Go requirement for {target}; locks are unchanged")
    minimum_go = tuple(int(part or 0) for part in directive.groups())
    if version_tuple(versions["go"]) < minimum_go:
        raise ValueError(f"Go >= {'.'.join(map(str, minimum_go))} is required for {target}; "
                         f"found {versions['go']}. Prepare tools using scripts/oink-upgrade.md; locks are unchanged")
    with tempfile.TemporaryDirectory(prefix="oink-libsass-check-") as directory:
        fixture = Path(directory)
        (fixture / "hugo.toml").write_text('baseURL = "https://example.test/"\ndisableKinds = ["taxonomy", "term", "RSS", "sitemap"]\n')
        (fixture / "layouts").mkdir()
        (fixture / "assets").mkdir()
        (fixture / "assets/probe.scss").write_text('$width: 12px; .probe { width: ($width / 3); }\n')
        (fixture / "layouts/index.html").write_text(
            '{{ $css := resources.Get "probe.scss" | css.Sass (dict "transpiler" "libsass" "targetPath" "probe.css") }}{{ $css.Content }}')
        env = release_environment()
        try:
            result = subprocess.run([env.get("HUGO_BIN", "hugo"), "--source", str(fixture),
                                     "--environment", "production", "--logLevel", "info"],
                                    env=env, text=True, capture_output=True, timeout=30)
        except subprocess.TimeoutExpired:
            raise ValueError("Hugo → LibSass smoke compilation timed out; locks are unchanged") from None
        rendered = fixture / "public/index.html"
        unexpected = any(is_unexpected_warning(line) for line in (result.stdout + result.stderr).splitlines())
        if result.returncode or unexpected or not rendered.is_file() or "width: 4px" not in rendered.read_text():
            raise ValueError(f"Hugo → LibSass smoke compilation failed with {versions['hugo']}: "
                             f"{result.stdout}{result.stderr}. "
                             "Prepare tools using scripts/oink-upgrade.md; locks are unchanged")
    return versions


def prepare_work(root, baseline, requested, resume, target):
    work = requested.expanduser().resolve() if requested else Path(tempfile.mkdtemp(prefix="hugegraph-oink-"))
    source = root.resolve()
    if work == source or work in source.parents or source in work.parents:
        raise ValueError("--work-dir must be outside the repository and its ancestors; use a fresh --work-dir")
    work.mkdir(parents=True, exist_ok=True)
    backup = work / "before"
    names = ("go.mod", "go.sum", "oink-overrides.json")
    present = [(backup / name).exists() for name in names]
    report = work / "review.json"
    if any(present):
        if not all(present):
            raise ValueError(f"incomplete original lock backup in {backup}; use a fresh --work-dir")
        if not resume or not report.is_file():
            raise ValueError("existing upgrade backup requires --resume and its original review.json; use a fresh --work-dir")
    elif report.exists():
        raise ValueError("review.json has no original lock backup; use a fresh --work-dir")
    if report.is_file():
        previous = json.loads(report.read_text())
        if previous.get("to") != target or previous.get("root") != str(root.resolve()):
            raise ValueError("--work-dir belongs to another target or checkout; use its matching --resume command")
    if not any(present):
        reserved = ("toolchain.json", "resolved.json", "build-plan.json", "validation-snapshot.json",
                    "strict", "artifacts", "site", "ai", "ai-disabled", "ai.json", "ai-disabled.json",
                    "hugo-cache", "version-cache", "after")
        conflicts = [name for name in reserved if (work / name).exists() or (work / name).is_symlink()]
        if conflicts:
            raise ValueError(f"--work-dir contains reserved runner outputs: {', '.join(conflicts)}; use a fresh --work-dir")
        backup.mkdir(exist_ok=True)
        for name, source in (("go.mod", root / "go.mod"), ("go.sum", root / "go.sum"),
                             ("oink-overrides.json", baseline)):
            with (backup / name).open("xb") as destination:
                destination.write(source.read_bytes())
        recovery = " && ".join("cp " + shlex.quote(str(backup / name)) + " " + shlex.quote(str(destination))
                               for name, destination in (("go.mod", root / "go.mod"), ("go.sum", root / "go.sum"),
                                                         ("oink-overrides.json", baseline)))
        report.write_text(json.dumps({"root": str(root.resolve()), "to": target, "startedFromResume": resume,
                                      "recoveryCommand": recovery,
                                      "recoveryScope": "Restores locks and reviewed inventory from the first invocation in this directory; "
                                                       "startedFromResume means the backup may already pin the target. Local adaptations are retained.",
                                      "resumeCommand": " ".join(map(shlex.quote, [sys.executable, str(root / "scripts/update_oink.py"),
                                                                                target, "--resume", "--accept-reviewed", "--work-dir", str(work)]))},
                                     indent=2) + "\n")
    return work


def validate(work):
    with isolated_release():
        _validate(work)


def validation_snapshot(root, work):
    """Capture current publishable sources without touching the user's index."""
    def git(*args, env=None):
        return subprocess.check_output(["git", *args], cwd=root, env=env, text=True).strip()

    head = git("rev-parse", "HEAD")
    head_tree = git("rev-parse", "HEAD^{tree}")
    with tempfile.TemporaryDirectory(prefix="oink-validation-index-") as directory:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(directory) / "index"))
        git("read-tree", head, env=env)
        git("add", "-A", "--", "content", "static", env=env)
        tree = git("write-tree", env=env)
        latest = head
        if tree != head_tree:
            identity = dict(env, GIT_AUTHOR_NAME="OINK validation", GIT_AUTHOR_EMAIL="validation@localhost",
                            GIT_COMMITTER_NAME="OINK validation", GIT_COMMITTER_EMAIL="validation@localhost")
            latest = git("commit-tree", tree, "-p", head, "-m", "chore: snapshot validation sources", "-m",
                         "- capture current content/static\n- preserve user index and refs\n- feed latest validation artifact", env=identity)
    report = {"baseHead": head, "latestSha": latest, "tree": tree,
              "source": "working tree content/static" if latest != head else "HEAD (content/static unchanged)",
              "scope": ["content", "static"],
              "exclusions": "Untracked ignored files and all changes outside content/static; normal Git ignore rules apply.",
              "references": "Validation-only unreferenced commit; real index, HEAD, branches and Git configuration are unchanged."}
    (work / "validation-snapshot.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Latest validation source: {latest} ({report['source']}); details: {work / 'validation-snapshot.json'}", flush=True)
    return latest


def _validate(work):
    py = sys.executable
    cli = [py, "scripts/versioning.py"]
    origin = "https://hugegraph.apache.org/"
    historical = "https://hugegraph.apache.org/"
    run(["bash", "dist/validate-links.sh"])
    run([py, "-m", "unittest", "discover", "-s", "scripts", "-p", "test_*.py"])
    run(["scripts/hugo.sh", "build", "--destination", work / "strict"])
    resolved = work / "resolved.json"
    latest = validation_snapshot(ROOT, work)
    run([*cli, "prepare", "--latest-sha", latest, "--output", resolved])
    versions = json.loads((work / "toolchain.json").read_text())
    plan = work / "build-plan.json"
    run([py, "scripts/version_cache.py", "plan", "--resolved-manifest", resolved,
         "--site-origin", origin, "--historical-origin", historical,
         "--hugo-version", versions["hugo"],
         "--go-version", versions["go"], "--webp-version", versions["webp"],
         "--cache-dir", work / "version-cache", "--output", plan])
    run([py, "scripts/build_versions.py", "--resolved-manifest", resolved, "--plan", plan,
         "--cache-dir", work / "version-cache", "--output", work / "artifacts",
         "--site-origin", origin, "--historical-origin", historical, "--workers", "2"],
        env=dict(os.environ, HUGO_CACHEDIR=str(work / "hugo-cache")))
    # aggregate validates every version artifact before merging it.
    run([*cli, "aggregate", "--resolved-manifest", resolved,
         "--artifacts", work / "artifacts", "--site-origin", origin,
         "--historical-origin", historical, "--output", work / "site"])
    run([py, "-m", "unittest", "scripts.test_download_data.DownloadDataTest.test_rendered_download_pages_have_verified_rows", "-v"],
        env=dict(os.environ, DOWNLOAD_PUBLIC_DIR=str(work / "site")))
    for name, port, config in [("ai", 4174, "ai-enabled"), ("ai-disabled", 4175, "ai-disabled")]:
        run([*cli, "config", "--version", "latest", "--site-origin", f"http://127.0.0.1:{port}/",
             "--historical-origin", historical, "--output", work / f"{name}.json"])
        run([py, "scripts/hugo_build.py", os.environ.get("HUGO_BIN", "hugo"), "--config",
             f"hugo.yaml,{work / f'{name}.json'},tests/e2e/{config}.yaml",
             "--destination", work / name, "--cleanDestinationDir", "--gc", "--minify",
             "--environment", "production", "--printPathWarnings", "--printI18nWarnings", "--logLevel", "info"])
    env = dict(os.environ, SITE_ROOT=str(work / "site"), AI_SITE_ROOT=str(work / "ai"),
               AI_DISABLED_SITE_ROOT=str(work / "ai-disabled"), VISUAL_RESULTS_DIR=str(work / "after"))
    run(["npm", "ci"], cwd=ROOT / "tests/e2e")
    run(["npx", "playwright", "install", "chromium"], cwd=ROOT / "tests/e2e")
    run(["npm", "run", "test:ci"], cwd=ROOT / "tests/e2e", env=env)
    run(["npm", "run", "test:visual"], cwd=ROOT / "tests/e2e", env=env)


def main():
    with isolated_release():
        _main()


def _main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", nargs="?")
    parser.add_argument("--check-baseline", action="store_true", help="read-only CI check of reviewed upstream files")
    parser.add_argument("--resume", action="store_true", help="validate/adapt the already-pinned target in a dirty worktree")
    parser.add_argument("--accept-reviewed", action="store_true", help="record human review of reported upstream changes; still run every validator")
    parser.add_argument("--work-dir", type=Path, help="artifact directory; reuse the same directory with --resume")
    args = parser.parse_args()
    if args.check_baseline and (args.version or args.resume or args.accept_reviewed or args.work_dir):
        parser.error("--check-baseline cannot be combined with upgrade options")
    if args.accept_reviewed and not args.version:
        parser.error("--accept-reviewed requires a target version")
    if args.check_baseline:
        module = download_locked(ROOT)
        verify_hugo_graph(ROOT, module["Version"])
        baseline = json.loads(BASELINE.read_text())
        changed = describe_changes(baseline["files"], snapshot(ROOT, Path(module["Dir"])))
        if baseline["version"] != module["Version"] or changed:
            detail = "; ".join(changed) or "no file changes"
            raise ValueError(f"OINK baseline differs (reviewed {baseline['version']}, pinned {module['Version']}): "
                             f"{detail}; local override additions/removals also require review; "
                             "follow scripts/oink-upgrade.md")
        print("Reviewed OINK upstream baseline matches")
        return
    if args.version is None:
        parser.error("version is required for upgrades")
    preflight(ROOT, args.version, args.resume)
    previous = json.loads(BASELINE.read_text())
    versions = check_toolchain(ROOT, args.version)
    work = prepare_work(ROOT, BASELINE, args.work_dir, args.resume, args.version)
    (work / "toolchain.json").write_text(json.dumps(versions, indent=2) + "\n")
    print(f"Upgrade artifacts and review report: {work}", flush=True)
    backup = work / "before"
    previous = json.loads((backup / "oink-overrides.json").read_text())
    initial_report = json.loads((work / "review.json").read_text())
    if previous["version"] == args.version:
        prior_module = None
    else:
        prior_module = prior_release(ROOT, previous["version"])
    if not args.resume and locked_version(ROOT) != args.version:
        command(["get", MODULE + "@" + args.version], ROOT)
        prune_checksums(ROOT, args.version)
    elif args.resume:
        prune_checksums(ROOT, args.version)
    module = download_locked(ROOT)
    graph = verify_hugo_graph(ROOT, args.version)
    current = snapshot(ROOT, Path(module["Dir"]))
    changed = changes(previous["files"], current)
    report = {**initial_report, "from": previous["version"], "reviewRequired": changed,
              "priorModuleDir": (prior_module or module)["Dir"], "targetModuleDir": module["Dir"],
              "hugoModuleGraph": graph,
              "changes": [{"path": p, "kind": change_kind(previous["files"], current, p),
                           "reason": "upstream SCSS selector dependency" if p.startswith("assets/scss/") else
                                     "local override or watched upstream interface"} for p in changed],
              "reviewMeaning": "These are upstream review impacts, not a list of required local edits. Added/removed describe watched inventory coverage; SCSS changes may need no adaptation.",
              "scope": "same-name layouts/assets/translations/data overrides, sidebar/search/appearance interfaces and upstream SCSS; not a full compatibility proof"}
    (work / "review.json").write_text(json.dumps(report, indent=2) + "\n")
    if changed and not args.accept_reviewed:
        raise ValueError(f"review required for {len(changed)} upstream files; inspect {work / 'review.json'}, adapt, then rerun with {report['resumeCommand']}")
    validate(work)
    BASELINE.write_text(json.dumps({"version": args.version, "files": current}, indent=2) + "\n")
    print(f"Upgrade checks passed: {args.version}. Review visual captures in {work / 'after'} before publishing. No branch commit or publication performed.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"OINK check failed: {error}" if "--check-baseline" in sys.argv else
              f"OINK upgrade incomplete: {error}. Changes and artifacts are retained.", file=sys.stderr)
        sys.exit(1)
