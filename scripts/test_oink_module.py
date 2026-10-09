#!/usr/bin/env python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0.

import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

import oink_module


class ModuleLockTest(unittest.TestCase):
    def test_build_resolves_relative_go_before_changing_directory(self):
        import argparse
        import os
        import versioning
        actual_run = subprocess.run
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "go"
            executable.write_text("#!/bin/sh\nprintf 'resolved-go'\n")
            executable.chmod(0o755)
            relative = os.path.relpath(executable, Path.cwd())
            entry = {"id": "latest", "archived": False, "publishPath": ""}
            args = argparse.Namespace(manifest=root / "manifest", version="latest", sha="a" * 40,
                                      output=root / "out", site_origin="https://example.org/",
                                      historical_origin="https://example.org/")

            def download(assembly, go):
                self.assertEqual(go, str(executable.resolve()))
                self.assertEqual(subprocess.check_output([go], cwd=assembly, text=True), "resolved-go")
                raise ValueError("verified relative Go from assembly")

            with patch.dict(os.environ, GO_BIN=relative), \
                 patch.object(versioning, "load_manifest", return_value={"versions": [entry]}), \
                 patch.object(versioning, "prepare_output_directory", return_value=args.output), \
                 patch.object(versioning, "run"), \
                 patch.object(versioning.subprocess, "run", side_effect=lambda argv, **kw:
                              None if argv[0] == "git" else actual_run(argv, **kw)), \
                 patch.object(versioning, "overlay_shell", side_effect=lambda assembly, **kw: assembly.mkdir()), \
                 patch.object(versioning, "derived_version_config", return_value={}), \
                 patch.object(versioning, "download_locked", side_effect=download) as resolve:
                with self.assertRaisesRegex(SystemExit, "OINK module verification failed: verified relative Go"):
                    versioning.build(args)
                resolve.assert_called_once()

    def config(self, version="v1.0.0", **changes):
        return dict(Module={"Path": oink_module.SITE_MODULE},
                    Require=[{"Path": oink_module.MODULE, "Version": version}], **changes)

    def download(self, version="v1.0.0", config=None, metadata=None, resolved=None, graph=None, sums=True, extra=""):
        module = dict(Path=oink_module.MODULE, Version=version, Sum="h1:archive", GoModSum="h1:mod")
        resolution = dict(Path=oink_module.MODULE, Version=version)
        module.update(metadata or {})
        resolution.update(resolved or {})
        replies = [json.dumps(config or self.config(version)), json.dumps(module),
                   json.dumps(resolution), graph or f"{oink_module.SITE_MODULE}\n{oink_module.MODULE} {version}\n", "all modules verified"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "go.sum").write_text(
                (f"\n{oink_module.MODULE} {version} h1:archive\n\n{oink_module.MODULE} {version}/go.mod h1:mod\n" if sums else "") + extra)
            with patch.object(oink_module, "command", side_effect=replies) as command:
                result = oink_module.download_locked(root, "/verified/bin/go")
                self.assertEqual(command.call_args.args[0], ["mod", "verify"])
                self.assertTrue(all(call.args[2] == "/verified/bin/go" for call in command.call_args_list))
                return result

    def test_rejects_stale_and_duplicate_checksums(self):
        for extra in [f"{oink_module.MODULE} v0.9.0 h1:stale\n",
                      f"{oink_module.MODULE} v1.0.0 h1:duplicate\n"]:
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                self.download(extra=extra)

    def test_mismatch_diagnostic_has_expected_and_actual(self):
        with self.assertRaisesRegex(ValueError, "h1:archive.*h1:wrong"):
            self.download(metadata={"Sum": "h1:wrong"})

    def test_failed_go_command_preserves_download_error(self):
        failure = subprocess.CalledProcessError(1, ["go"], output='{"Error":"checksum mismatch"}')
        with patch.object(oink_module.subprocess, "check_output", side_effect=failure):
            with self.assertRaisesRegex(ValueError, "verified/bin/go.*checksum mismatch"):
                oink_module.command(["mod", "download", "-json"], Path("."), "/verified/bin/go")

    def test_cli_missing_go_has_no_traceback(self):
        import os
        result = subprocess.run([sys.executable, oink_module.__file__], text=True, capture_output=True,
                                env=dict(os.environ, GO_BIN="/missing/oink-test-go"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("/missing/oink-test-go", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

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
