#!/usr/bin/env python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0.

"""Resolve the sole theme dependency from the checked-in Go lock files."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

MODULE = "github.com/pgsty/oink"
SITE_MODULE = "github.com/apache/hugegraph-doc"
VERSION = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?")


def command(args, root, go_executable=None):
    argv = [go_executable or os.environ.get("GO_BIN", "go"), *args]
    try:
        return subprocess.check_output(argv, cwd=root, text=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.output or "").strip()
        raise ValueError(f"Go command {' '.join(argv)} failed ({error.returncode}): {detail}") from None
    except OSError as error:
        raise ValueError(f"Go executable is unavailable: {argv[0]} ({error})") from None


def locked_version(root, go_executable=None):
    data = json.loads(command(["mod", "edit", "-json"], root, go_executable))
    requirements = data.get("Require") or []
    if (data.get("Module", {}).get("Path") != SITE_MODULE
            or data.get("Replace") or data.get("Exclude")
            or len(requirements) != 1 or requirements[0]["Path"] != MODULE):
        raise ValueError(f"expected the HugeGraph module with only OINK and no replace/exclude directives; actual: {data!r}")
    version = requirements[0]["Version"]
    if not VERSION.fullmatch(version):
        raise ValueError(f"OINK must be pinned to an explicit release version; actual: {version!r}")
    return version


def download_locked(root, go_executable=None):
    root = Path(root)
    version = locked_version(root, go_executable)
    sums = {}
    for line in (root / "go.sum").read_text().splitlines():
        if not line.strip():
            continue
        path, revision, digest = line.split()
        if (path, revision) in sums:
            raise ValueError(f"duplicate go.sum entry: {path} {revision}")
        sums[(path, revision)] = digest
    expected = [sums.get((MODULE, version)), sums.get((MODULE, version + "/go.mod"))]
    if not all(expected):
        raise ValueError(f"expected checksums for {MODULE}@{version} and /go.mod in go.sum; actual entries: {list(sums)!r}")
    if set(sums) != {(MODULE, version), (MODULE, version + "/go.mod")}:
        raise ValueError(f"go.sum must contain only {MODULE}@{version} and /go.mod; actual entries: {list(sums)!r}")
    module = json.loads(command(["mod", "download", "-json", MODULE + "@" + version], root, go_executable))
    if (module.get("Path") != MODULE or module.get("Version") != version
            or module.get("Sum") != expected[0] or module.get("GoModSum") != expected[1]
            or module.get("Error")):
        raise ValueError(f"expected {MODULE}@{version} checksums {expected!r}; downloaded metadata: {module!r}")
    resolved = json.loads(command(["list", "-m", "-json", MODULE], root, go_executable))
    if resolved.get("Replace") or resolved.get("Version") != version or resolved.get("Path") != MODULE:
        raise ValueError(f"expected resolved {MODULE}@{version} without replacement; actual: {resolved!r}")
    graph = command(["list", "-m", "all"], root, go_executable).splitlines()
    if graph != [SITE_MODULE, MODULE + " " + version]:
        raise ValueError(f"expected module graph {[SITE_MODULE, MODULE + ' ' + version]!r}; actual: {graph!r}")
    command(["mod", "verify"], root, go_executable)
    return module


if __name__ == "__main__":
    try:
        print(json.dumps(download_locked(Path(__file__).resolve().parents[1]), indent=2))
    except (ValueError, OSError) as error:
        sys.exit(f"OINK module verification failed: {error}")
