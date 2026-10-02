#!/usr/bin/env python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Exact historical build reuse; a receipt never replaces current validation."""

import argparse
import datetime
import hashlib
import json
import pathlib
import platform
import re
import shutil
import stat
import tempfile

import versioning


SCHEMA = 1


def digest_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def safe_path(path):
    path = pathlib.Path(path).absolute()
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError(f"symlink is not a cache input: {path}")
    return path


def snapshot(path):
    """Hash names, types and bytes, rejecting links and special files."""
    path = safe_path(path)
    if not path.exists():
        return [["", "missing"]]
    result = []
    for item in [path, *sorted(path.rglob("*"))] if path.is_dir() else [path]:
        mode = item.lstat().st_mode
        name = item.relative_to(path).as_posix()
        if stat.S_ISDIR(mode):
            result.append([name, "directory"])
        elif stat.S_ISREG(mode):
            result.append([name, hashlib.sha256(item.read_bytes()).hexdigest()])
        else:
            raise ValueError(f"unsupported cache input: {item}")
    return result


def shared_digest(root):
    paths = {*versioning.SHELL_FILES, *versioning.SHELL_DIRS,
             *versioning.SHELL_CONTENT_DIRS, "versions.json", "dist", ".htaccess", ".asf.yaml"}
    paths.update(p for p in versioning.SHELL_CONTENT if p.endswith("docs/SUMMARY.md"))
    paths.update("static/" + p for p in (*versioning.SHELL_STATIC_FILES, *versioning.SHELL_STATIC_DIRS))
    paths.update(p.relative_to(root).as_posix() for p in (root / "scripts").glob("*.py"))
    paths.update(p.relative_to(root).as_posix() for p in (root / "scripts").glob("*.sh"))
    return digest_json([[p, snapshot(root / p)] for p in sorted(paths)])


def validate_version_id(version):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", version):
        raise ValueError("invalid version identifier")


def version_directory(cache_dir, version):
    validate_version_id(version)
    return safe_path(pathlib.Path(cache_dir) / version)


def reusable(cache_dir, entry):
    if not entry["archived"]:
        return False
    try:
        directory = version_directory(cache_dir, entry["id"])
        receipt_path = safe_path(directory / "receipt.json")
        receipt = json.loads(receipt_path.read_text())
        artifact = safe_path(directory / "artifact")
        return (artifact.is_dir() and (artifact / ".version.json").is_file()
                and receipt["schemaVersion"] == SCHEMA
                and receipt["buildKey"] == entry["buildKey"]
                and receipt["treeDigest"] == digest_json(snapshot(artifact)))
    except (OSError, ValueError, KeyError, TypeError):
        return False


def make_plan(root, manifest, cache_dir, *, site_origin, historical_origin,
              hugo_version, go_version, webp_version, year=None):
    common = {"schemaVersion": SCHEMA, "shared": shared_digest(root),
              "siteOrigin": site_origin, "historicalOrigin": historical_origin,
              "hugo": hugo_version, "go": go_version, "webp": webp_version,
              "python": platform.python_version(), "system": platform.system(),
              "machine": platform.machine(), "year": year or datetime.datetime.now(datetime.timezone.utc).year}
    entries = []
    for source in manifest.get("include", manifest["versions"]):
        entry = dict(source)
        validate_version_id(entry["id"])
        entry["buildKey"] = digest_json({"common": common, "version": source,
                                         "repository": manifest["repository"]})
        entry["reusable"] = reusable(cache_dir, entry)
        entries.append(entry)
    return {"schemaVersion": SCHEMA, "cacheKey": "history-v1-" + digest_json(
        [[e["id"], e["buildKey"]] for e in entries if e["archived"]]),
        "versions": entries, "include": [e for e in entries if not e["reusable"]]}


def build_groups(manifest, cache_hit):
    """Bound cold-build jobs while keeping a warm bundle in one job."""
    selected = [entry["id"] for entry in manifest.get("include", manifest["versions"])]
    for version in selected:
        validate_version_id(version)
    if not selected or len(set(selected)) != len(selected):
        raise ValueError("selected versions must be nonempty and unique")
    count = 1 if cache_hit else min(3, (len(selected) + 1) // 2)
    return [{"id": str(index), "versions": selected[index::count]} for index in range(count)]


def verify_expected_plan(actual, expected):
    """Builders may select a subset, but must reproduce every prepared key."""
    expected_keys = {entry["id"]: entry["buildKey"] for entry in expected["versions"]}
    if len(expected_keys) != len(expected["versions"]):
        raise ValueError("expected plan contains duplicate versions")
    for entry in actual["versions"]:
        if expected_keys.get(entry["id"]) != entry["buildKey"]:
            raise ValueError(f"build inputs differ from prepared plan: {entry['id']}")


def record(cache_dir, entry, artifact):
    if not entry["archived"]:
        raise ValueError("latest artifacts are not reusable")
    artifact = safe_path(artifact)
    if not artifact.is_dir() or not (artifact / ".version.json").is_file():
        raise ValueError("artifact is missing version metadata")
    tree_digest = digest_json(snapshot(artifact))
    metadata = json.loads((artifact / ".version.json").read_text())
    if any(metadata.get(field) != entry.get(field) for field in ("id", "sha")):
        raise ValueError("artifact metadata does not match planned version")
    destination = version_directory(cache_dir, entry["id"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="record-", dir=destination.parent) as temporary:
        staging = pathlib.Path(temporary) / "version"
        staging.mkdir()
        shutil.copytree(artifact, staging / "artifact")
        (staging / "receipt.json").write_text(json.dumps({"schemaVersion": SCHEMA,
            "buildKey": entry["buildKey"], "treeDigest": tree_digest}))
        if destination.exists():
            shutil.rmtree(destination)
        staging.rename(destination)


def restore(cache_dir, entry, output):
    if not reusable(cache_dir, entry):
        return False
    output = safe_path(output)
    if output.exists():
        raise ValueError("restore output must not exist")
    shutil.copytree(version_directory(cache_dir, entry["id"]) / "artifact", output)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan")
    plan.add_argument("--resolved-manifest", type=pathlib.Path, required=True)
    plan.add_argument("--site-origin", required=True)
    plan.add_argument("--historical-origin", required=True)
    plan.add_argument("--hugo-version", default="0.165.0")
    plan.add_argument("--go-version", required=True)
    plan.add_argument("--webp-version", default="unspecified")
    plan.add_argument("--output", type=pathlib.Path, required=True)
    plan.add_argument("--expected-plan", type=pathlib.Path)
    groups = commands.add_parser("groups")
    groups.add_argument("--resolved-manifest", type=pathlib.Path, required=True)
    groups.add_argument("--cache-hit", choices=("true", "false"), required=True)
    for name in ("restore", "record"):
        command = commands.add_parser(name)
        command.add_argument("--plan", type=pathlib.Path, required=True)
        command.add_argument("--version", required=True)
        command.add_argument("--output" if name == "restore" else "--artifact", type=pathlib.Path, required=True)
        command.add_argument("--cache-dir", type=pathlib.Path, required=True)
    plan.add_argument("--cache-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    if args.command == "plan":
        manifest = versioning.load_resolved_manifest(args.resolved_manifest)
        result = make_plan(versioning.ROOT, manifest, args.cache_dir,
            site_origin=args.site_origin, historical_origin=args.historical_origin,
            hugo_version=args.hugo_version, go_version=args.go_version, webp_version=args.webp_version)
        if args.expected_plan:
            verify_expected_plan(result, json.loads(args.expected_plan.read_text()))
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    elif args.command == "groups":
        manifest = versioning.load_resolved_manifest(args.resolved_manifest)
        print(json.dumps(build_groups(manifest, args.cache_hit == "true")))
    else:
        plan_data = json.loads(args.plan.read_text())
        entry = next(e for e in plan_data["versions"] if e["id"] == args.version)
        if args.command == "record":
            record(args.cache_dir, entry, args.artifact)
        elif not restore(args.cache_dir, entry, args.output):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
