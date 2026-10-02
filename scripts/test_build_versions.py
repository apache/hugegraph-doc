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

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest import mock

import build_versions


class BuildVersionsTest(unittest.TestCase):
    def setUp(self):
        self.entry = {"id": "1.7", "sha": "a" * 40, "archived": True, "buildKey": "b" * 64}
        self.args = argparse.Namespace(output=Path("/tmp/versions-test"),
            cache_dir=Path("/tmp/cache-test"), site_origin="https://example.com/",
            historical_origin="https://example.com/", force_rebuild=False, workers=2)

    def run_one(self, restored, *, failure=None):
        with mock.patch.object(build_versions.version_cache, "restore", return_value=restored) as restore, \
             mock.patch.object(build_versions.version_cache, "record") as record, \
             mock.patch.object(build_versions.subprocess, "run", side_effect=failure) as run:
            build_versions.run_version(self.entry, self.args, Path("/tmp/hugo-test"))
            return restore, record, run

    def test_cached_version_still_validated(self):
        _, record, run = self.run_one(True)
        self.assertEqual([c.args[0][2] for c in run.call_args_list], ["validate"])
        record.assert_not_called()

    def test_miss_builds_and_validates(self):
        _, record, run = self.run_one(False)
        self.assertEqual([c.args[0][2] for c in run.call_args_list], ["build", "validate"])
        record.assert_called_once()
        self.assertEqual(run.call_args.kwargs["env"]["HUGO_CACHEDIR"], "/tmp/hugo-test/1.7")

    def test_invalid_cached_artifact_rebuilt_and_validated(self):
        _, record, run = self.run_one(True, failure=[subprocess.CalledProcessError(1, "validate"), None, None])
        self.assertEqual([c.args[0][2] for c in run.call_args_list], ["validate", "build", "validate"])
        record.assert_called_once()

    def test_failed_fresh_validation_not_cached(self):
        with mock.patch.object(build_versions.version_cache, "restore", return_value=False), \
             mock.patch.object(build_versions.version_cache, "record") as record, \
             mock.patch.object(build_versions.subprocess, "run",
                               side_effect=[None, subprocess.CalledProcessError(1, "validate")]):
            with self.assertRaises(subprocess.CalledProcessError):
                build_versions.run_version(self.entry, self.args, Path("/tmp/hugo-test"))
            record.assert_not_called()

    def test_forced_rebuild_does_not_restore(self):
        self.args.force_rebuild = True
        restore, _, run = self.run_one(True)
        restore.assert_not_called()
        self.assertEqual([c.args[0][2] for c in run.call_args_list], ["build", "validate"])

    def test_restore_io_failure_falls_back_to_build(self):
        with mock.patch.object(build_versions.version_cache, "restore", side_effect=OSError("disk")), \
             mock.patch.object(build_versions.version_cache, "record"), \
             mock.patch.object(build_versions.subprocess, "run") as run:
            build_versions.run_version(self.entry, self.args, Path("/tmp/hugo-test"))
        self.assertEqual([c.args[0][2] for c in run.call_args_list], ["build", "validate"])

    def test_corrupt_cache_symlink_does_not_fail_validated_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self.args.output = root / "output"
            self.args.cache_dir = root / "cache"
            self.args.cache_dir.mkdir()
            protected = root / "protected"
            protected.mkdir()
            marker = protected / "marker"
            marker.write_text("keep")
            (self.args.cache_dir / self.entry["id"]).symlink_to(protected, target_is_directory=True)

            def build(command, **_):
                if command[2] == "build":
                    artifact = self.args.output / self.entry["id"]
                    artifact.mkdir(parents=True)
                    (artifact / ".version.json").write_text(json.dumps(self.entry))

            with mock.patch.object(build_versions.subprocess, "run", side_effect=build) as run:
                build_versions.run_version(self.entry, self.args, root / "hugo")
            self.assertEqual([c.args[0][2] for c in run.call_args_list], ["build", "validate"])
            self.assertEqual(marker.read_text(), "keep")
            self.assertEqual(list(protected.iterdir()), [marker])

    def test_rejects_drifted_plan(self):
        with self.assertRaises(ValueError):
            build_versions.selected_entries({"versions": [self.entry]},
                {"versions": [dict(self.entry, sha="c" * 40)]})

    def test_configured_hugo_cache_preserved_and_isolated_by_version(self):
        entries = [self.entry, dict(self.entry, id="1.5")]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "hugo-cache"
            cache.mkdir()
            marker = cache / "existing-resource"
            marker.write_text("keep")
            self.args.output = root / "output"
            self.args.cache_dir = root / "artifacts"
            self.args.plan = root / "plan.json"
            self.args.plan.write_text(json.dumps({"versions": entries}))
            self.args.resolved_manifest = root / "resolved.json"
            with mock.patch.dict(os.environ, HUGO_CACHEDIR=str(cache)), \
                 mock.patch.object(build_versions.versioning, "prepare_output_directory", return_value=self.args.output), \
                 mock.patch.object(build_versions.versioning, "load_resolved_manifest", return_value={"versions": entries}), \
                 mock.patch.object(build_versions.versioning, "run"), \
                 mock.patch.object(build_versions.version_cache, "restore", return_value=False), \
                 mock.patch.object(build_versions.version_cache, "record"), \
                 mock.patch.object(build_versions.subprocess, "run") as run:
                build_versions.execute(self.args)
            self.assertEqual(marker.read_text(), "keep")
            self.assertEqual({c.kwargs["env"]["HUGO_CACHEDIR"] for c in run.call_args_list},
                             {str(cache.resolve() / "1.7"), str(cache.resolve() / "1.5")})

    def test_hugo_cache_inside_output_rejected_before_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.args.plan = Path(tmp) / "plan.json"
            self.args.plan.write_text(json.dumps({"versions": [self.entry]}))
            self.args.resolved_manifest = Path(tmp) / "resolved.json"
            with mock.patch.dict(os.environ, HUGO_CACHEDIR=str(self.args.output / "cache")), \
                 mock.patch.object(build_versions.versioning, "load_resolved_manifest", return_value={"versions": [self.entry]}), \
                 mock.patch.object(build_versions.versioning, "prepare_output_directory") as prepare:
                with self.assertRaisesRegex(ValueError, "must not overlap"):
                    build_versions.execute(self.args)
                prepare.assert_not_called()

    def test_bounded_workers_collect_failures_and_finish_other_versions(self):
        entries = [dict(self.entry, id=str(i)) for i in range(4)]
        gate = threading.Barrier(2, timeout=5)
        finished = []
        def work(entry, *_):
            gate.wait()
            finished.append(entry["id"])
            if entry["id"] == "0":
                raise RuntimeError("build failed")
        with tempfile.TemporaryDirectory() as tmp:
            self.args.plan = Path(tmp) / "plan.json"
            self.args.plan.write_text(json.dumps({"versions": entries}))
            self.args.resolved_manifest = Path(tmp) / "resolved.json"
            with mock.patch.object(build_versions.versioning, "load_resolved_manifest", return_value={"versions": entries}), \
                 mock.patch.object(build_versions.versioning, "prepare_output_directory", return_value=self.args.output), \
                 mock.patch.object(build_versions.versioning, "run"), \
                 mock.patch.object(build_versions, "run_version", side_effect=work):
                with self.assertRaisesRegex(RuntimeError, "failed versions: 0"):
                    build_versions.execute(self.args)
        self.assertEqual(sorted(finished), ["0", "1", "2", "3"])


if __name__ == "__main__":
    unittest.main()
