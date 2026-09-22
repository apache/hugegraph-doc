#!/usr/bin/env python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0.

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import oink_module


class ModuleLockTest(unittest.TestCase):
    def config(self, version="v1.0.0", **changes):
        return dict(Module={"Path": oink_module.SITE_MODULE},
                    Require=[{"Path": oink_module.MODULE, "Version": version}], **changes)

    def download(self, version="v1.0.0", config=None, metadata=None, resolved=None, graph=None, sums=True):
        module = dict(Path=oink_module.MODULE, Version=version, Sum="h1:archive", GoModSum="h1:mod")
        resolution = dict(Path=oink_module.MODULE, Version=version)
        module.update(metadata or {})
        resolution.update(resolved or {})
        replies = [json.dumps(config or self.config(version)), json.dumps(module),
                   json.dumps(resolution), graph or f"{oink_module.SITE_MODULE}\n{oink_module.MODULE} {version}\n", "all modules verified"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "go.sum").write_text(
                f"\n{oink_module.MODULE} {version} h1:archive\n\n{oink_module.MODULE} {version}/go.mod h1:mod\n" if sums else "")
            with patch.object(oink_module, "command", side_effect=replies) as command:
                result = oink_module.download_locked(root)
                self.assertEqual(command.call_args.args[0], ["mod", "verify"])
                return result

    def test_accepts_each_locked_release(self):
        for version in ["v1.0.0", "v1.1.0"]:
            with self.subTest(version=version):
                self.assertEqual(self.download(version)["Version"], version)

    def test_rejects_changed_dependency_boundary(self):
        configurations = [self.config(Replace=[{"New": {"Path": "local"}}]),
                          self.config(Exclude=[{"Path": oink_module.MODULE, "Version": "v1.0.0"}])]
        wrong_site = self.config()
        wrong_site["Module"]["Path"] = "example.com/site"
        configurations.append(wrong_site)
        extra = self.config()
        extra["Require"].append({"Path": "example.com/extra", "Version": "v1.0.0"})
        configurations.append(extra)
        for config in configurations:
            with self.subTest(config=config), self.assertRaises(ValueError):
                self.download(config=config)

    def test_missing_checksums_stop_before_download(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "go.sum").write_text("")
            with patch.object(oink_module, "command", return_value=json.dumps(self.config())) as command:
                with self.assertRaises(ValueError):
                    oink_module.download_locked(root)
                self.assertEqual(command.call_count, 1)

    def test_rejects_download_identity_or_checksum_mismatch(self):
        for metadata in [{"Sum": "h1:wrong"}, {"GoModSum": "h1:wrong"},
                         {"Path": "example.com/theme"}, {"Version": "v9.0.0"}]:
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                self.download(metadata=metadata)

    def test_rejects_resolved_override_and_extra_dependency(self):
        for resolved in [{"Replace": {"Path": "local"}}, {"Version": "v9.0.0"},
                         {"Path": "example.com/theme"}]:
            with self.subTest(resolved=resolved), self.assertRaises(ValueError):
                self.download(resolved=resolved)
        with self.assertRaises(ValueError):
            self.download(graph=f"{oink_module.SITE_MODULE}\n{oink_module.MODULE} v1.0.0\nexample.com/extra v1.0.0\n")


if __name__ == "__main__":
    unittest.main()
