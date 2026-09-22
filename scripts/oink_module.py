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
from pathlib import Path

MODULE = "github.com/pgsty/oink"
SITE_MODULE = "github.com/apache/hugegraph-doc"
VERSION = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?")


def command(args, root):
    return subprocess.check_output([os.environ.get("GO_BIN", "go"), *args], cwd=root, text=True)


def locked_version(root):
    data = json.loads(command(["mod", "edit", "-json"], root))
    requirements = data.get("Require") or []
    if (data.get("Module", {}).get("Path") != SITE_MODULE
            or data.get("Replace") or data.get("Exclude")
            or len(requirements) != 1 or requirements[0]["Path"] != MODULE):
        raise ValueError("expected the HugeGraph module with only OINK and no replace/exclude directives")
    version = requirements[0]["Version"]
    if not VERSION.fullmatch(version):
        raise ValueError("OINK must be pinned to an explicit release version")
    return version


def download_locked(root):
    root = Path(root)
    version = locked_version(root)
    sums = {}
    for line in (root / "go.sum").read_text().splitlines():
        if not line.strip():
            continue
        path, revision, digest = line.split()
        sums[(path, revision)] = digest
    expected = [sums.get((MODULE, version)), sums.get((MODULE, version + "/go.mod"))]
    if not all(expected):
        raise ValueError("OINK module and go.mod checksums must already exist in go.sum")
    module = json.loads(command(["mod", "download", "-json", MODULE + "@" + version], root))
    if (module.get("Path") != MODULE or module.get("Version") != version
            or module.get("Sum") != expected[0] or module.get("GoModSum") != expected[1]
            or module.get("Error")):
        raise ValueError("downloaded OINK identity or checksum differs from lock files")
    resolved = json.loads(command(["list", "-m", "-json", MODULE], root))
    if resolved.get("Replace") or resolved.get("Version") != version or resolved.get("Path") != MODULE:
        raise ValueError("resolved OINK module differs from lock files")
    graph = command(["list", "-m", "all"], root).splitlines()
    if graph != [SITE_MODULE, MODULE + " " + version]:
        raise ValueError("module graph must contain only this site and the pinned OINK module")
    command(["mod", "verify"], root)
    return module


if __name__ == "__main__":
    print(json.dumps(download_locked(Path(__file__).resolve().parents[1]), indent=2))
