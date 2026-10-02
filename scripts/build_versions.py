#!/usr/bin/env python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Build selected versions with bounded concurrency and fully validate cache hits."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import nullcontext
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

import version_cache
import versioning


def log(version, message, started):
    print(f"[version {version}] {message} ({time.monotonic() - started:.2f}s)", flush=True)


def run_version(entry, args, hugo_cache):
    started = time.monotonic()
    output = args.output / entry["id"]
    environment = dict(os.environ, HUGO_CACHEDIR=str(hugo_cache / entry["id"]))
    common = ["--version", entry["id"], "--sha", entry["sha"],
              "--site-origin", args.site_origin, "--historical-origin", args.historical_origin]

    def command(operation):
        target = "--output" if operation == "build" else "--artifact"
        subprocess.run([sys.executable, str(versioning.ROOT / "scripts/versioning.py"),
                        operation, *common, target, str(output)],
                       cwd=versioning.ROOT, env=environment, check=True)

    restored = False
    if entry["archived"] and not args.force_rebuild:
        try:
            restored = version_cache.restore(args.cache_dir, entry, output)
        except OSError as error:
            log(entry["id"], f"cache restore unavailable; rebuilding: {error}", started)
    if restored:
        log(entry["id"], "cache restored; validating", started)
        try:
            command("validate")
        except subprocess.CalledProcessError:
            log(entry["id"], "cached artifact failed validation; rebuilding", started)
        else:
            log(entry["id"], "cache validated", started)
            return
    log(entry["id"], "building", started)
    command("build")
    command("validate")
    log(entry["id"], "build validated", started)
    if entry["archived"]:
        try:
            version_cache.record(args.cache_dir, entry, output)
        except (OSError, ValueError) as error:
            log(entry["id"], f"cache save unavailable: {error}", started)
    log(entry["id"], "complete", started)


def selected_entries(manifest, plan):
    selected = manifest.get("include", manifest["versions"])
    if not selected or len({e["id"] for e in selected}) != len(selected):
        raise ValueError("resolved selection must be nonempty and unique")
    expected = {e["id"]: e for e in manifest["versions"]}
    if any(e != expected.get(e["id"]) for e in selected):
        raise ValueError("resolved selection does not match resolved versions")
    entries = plan["versions"]
    if [e["id"] for e in entries] != [e["id"] for e in selected]:
        raise ValueError("cache plan does not match selected versions")
    for entry, source in zip(entries, selected):
        if any(entry.get(key) != value for key, value in source.items()):
            raise ValueError("cache plan source differs from resolved manifest")
        if not re.fullmatch(r"[0-9a-f]{64}", entry.get("buildKey", "")):
            raise ValueError("cache plan has invalid build key")
    return entries


def execute(args):
    if not 1 <= args.workers <= 3:
        raise ValueError("workers must be between 1 and 3")
    manifest = versioning.load_resolved_manifest(args.resolved_manifest)
    entries = selected_entries(manifest, json.loads(args.plan.read_text()))
    output, cache = args.output.resolve(), args.cache_dir.resolve()
    if output == cache or output in cache.parents or cache in output.parents:
        raise ValueError("output and cache directories must not overlap")
    configured_hugo_cache = os.environ.get("HUGO_CACHEDIR")
    hugo_cache = Path(configured_hugo_cache).expanduser().resolve() if configured_hugo_cache else None
    if hugo_cache is not None:
        for other in (output, cache):
            if hugo_cache == other or hugo_cache in other.parents or other in hugo_cache.parents:
                raise ValueError("Hugo cache, artifact cache and output directories must not overlap")
    args.output = versioning.prepare_output_directory(args.output, "versions output")
    # Complete shared Git mutations before independent build subprocesses start.
    for sha in dict.fromkeys(e["sha"] for e in entries):
        try:
            versioning.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"])
        except subprocess.CalledProcessError:
            versioning.run(["git", "fetch", "--no-tags", "origin", sha])
    print(f"version build workers: {args.workers}; available CPUs: {os.cpu_count()}", flush=True)
    failures = []
    cache_context = (nullcontext(hugo_cache) if hugo_cache is not None
                     else tempfile.TemporaryDirectory(prefix="hugo-versions-"))
    with cache_context as directory:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(run_version, entry, args, Path(directory)): entry["id"]
                       for entry in entries}
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as error:
                    failures.append(futures[future])
                    print(f"[version {futures[future]}] FAILED: {error}", file=sys.stderr, flush=True)
    if failures:
        raise RuntimeError(f"failed versions: {', '.join(sorted(failures))}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("resolved-manifest", "plan", "cache-dir", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--site-origin", required=True)
    parser.add_argument("--historical-origin", required=True)
    parser.add_argument("--workers", type=int, choices=range(1, 4), default=2)
    parser.add_argument("--force-rebuild", action="store_true")
    execute(parser.parse_args())


if __name__ == "__main__":
    main()
