#!/usr/bin/env python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0.

"""Explicit, review-gated OINK upgrades using the existing site validators."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from oink_module import MODULE, VERSION, command, download_locked, locked_version

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "scripts/oink-overrides.json"
WATCH = ("assets/js/sidebar-state.js", "assets/js/sidebar-nav.js",
         "assets/js/docs-shell.js", "assets/js/search.js", "assets/js/search-engine.js",
         "assets/js/surface-coordinator.js", "assets/js/command-palette.js")


def run(args, *, cwd=ROOT, env=None):
    print("+ " + " ".join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, env=env, check=True)


def snapshot(root, upstream):
    paths = set(WATCH)
    # Project SCSS depends on upstream selectors even without a same-name override.
    paths.update(str(p.relative_to(upstream)) for p in (upstream / "assets/scss").rglob("*.scss"))
    for folder in ("layouts", "assets", "i18n"):
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


def preflight(root, target, resume):
    if not VERSION.fullmatch(target):
        raise ValueError("use an explicit release such as v1.1.0; branches and latest are not accepted")
    if resume:
        if locked_version(root) != target:
            raise ValueError("--resume only validates the already-pinned target; it cannot switch versions")
    elif subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip():
        raise ValueError("working tree is not clean; commit/stash your work first, or use --resume for this pinned target")


def validate(work):
    py = sys.executable
    cli = [py, "scripts/versioning.py"]
    origin = "https://hugegraph.apache.org/"
    historical = "https://hugegraph.apache.org/"
    run(["bash", "dist/validate-links.sh"])
    run([py, "-m", "unittest", "discover", "-s", "scripts", "-p", "test_*.py"])
    run(["scripts/hugo.sh", "build", "--destination", work / "strict"])
    resolved = work / "resolved.json"
    run([*cli, "prepare", "--output", resolved])
    manifest = json.loads(resolved.read_text())
    for entry in manifest["versions"]:
        artifact = work / "artifacts" / entry["id"]
        run([*cli, "build", "--version", entry["id"], "--sha", entry["sha"],
             "--site-origin", origin, "--historical-origin", historical, "--output", artifact])
    # aggregate validates every version artifact before merging it.
    run([*cli, "aggregate", "--resolved-manifest", resolved,
         "--artifacts", work / "artifacts", "--site-origin", origin,
         "--historical-origin", historical, "--output", work / "site"])
    run([py, "-m", "unittest", "scripts.test_download_data.DownloadDataTest.test_rendered_download_pages_have_verified_rows", "-v"],
        env=dict(os.environ, DOWNLOAD_PUBLIC_DIR=str(work / "site")))
    run([*cli, "config", "--version", "latest", "--site-origin", "http://127.0.0.1:4174/",
         "--historical-origin", historical, "--output", work / "ai.json"])
    run([os.environ.get("HUGO_BIN", "hugo"), "--config",
         f"hugo.yaml,{work / 'ai.json'},tests/e2e/ai-enabled.yaml",
         "--destination", work / "ai", "--cleanDestinationDir", "--gc", "--minify",
         "--environment", "production", "--panicOnWarning"])
    env = dict(os.environ, SITE_ROOT=str(work / "site"), AI_SITE_ROOT=str(work / "ai"))
    run(["npm", "ci"], cwd=ROOT / "tests/e2e")
    run(["npx", "playwright", "install", "chromium"], cwd=ROOT / "tests/e2e")
    run(["npm", "run", "test:ci"], cwd=ROOT / "tests/e2e", env=env)
    run(["npm", "run", "test:visual"], cwd=ROOT / "tests/e2e", env=env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", nargs="?")
    parser.add_argument("--check-baseline", action="store_true", help="read-only CI check of reviewed upstream files")
    parser.add_argument("--resume", action="store_true", help="validate/adapt the already-pinned target in a dirty worktree")
    parser.add_argument("--accept-reviewed", action="store_true", help="record human review of reported upstream changes; still run every validator")
    args = parser.parse_args()
    if args.check_baseline:
        module = download_locked(ROOT)
        baseline = json.loads(BASELINE.read_text())
        if (baseline["version"] != module["Version"]
                or changes(baseline["files"], snapshot(ROOT, Path(module["Dir"])))):
            raise ValueError("OINK upstream files differ from reviewed baseline; follow scripts/oink-upgrade.md")
        print("Reviewed OINK upstream baseline matches")
        return
    if args.version is None:
        parser.error("version is required for upgrades")
    preflight(ROOT, args.version, args.resume)
    previous = json.loads(BASELINE.read_text())
    work = Path(tempfile.mkdtemp(prefix="hugegraph-oink-"))
    print(f"Upgrade artifacts and review report: {work}", flush=True)
    if not args.resume and locked_version(ROOT) != args.version:
        command(["get", MODULE + "@" + args.version], ROOT)
    module = download_locked(ROOT)
    current = snapshot(ROOT, Path(module["Dir"]))
    changed = changes(previous["files"], current)
    report = {"from": previous["version"], "to": args.version, "reviewRequired": changed,
              "scope": "same-name overrides, sidebar/search interfaces and upstream SCSS; not a full compatibility proof"}
    (work / "review.json").write_text(json.dumps(report, indent=2) + "\n")
    if changed and not args.accept_reviewed:
        raise ValueError(f"review required for {len(changed)} upstream files; inspect {work / 'review.json'}, adapt, then rerun with --resume --accept-reviewed")
    validate(work)
    BASELINE.write_text(json.dumps({"version": args.version, "files": current}, indent=2) + "\n")
    print(f"Upgrade checks passed: {args.version}. Review visual captures in tests/e2e/visual-results before publishing. No commit or publication performed.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, subprocess.CalledProcessError) as error:
        print(f"OINK upgrade incomplete: {error}. Changes and artifacts are retained.", file=sys.stderr)
        sys.exit(1)
