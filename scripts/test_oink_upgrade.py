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

import update_oink


class UpgradeTest(unittest.TestCase):
    def test_invalid_version_stops_before_commands(self):
        with patch.object(update_oink.subprocess, "check_output") as command:
            with self.assertRaises(ValueError):
                update_oink.preflight(Path("."), "latest", False)
            command.assert_not_called()

    def test_dirty_tree_requires_explicit_resume(self):
        with patch.object(update_oink.subprocess, "check_output", return_value=" M file"):
            with self.assertRaisesRegex(ValueError, "not clean"):
                update_oink.preflight(Path("."), "v1.1.0", False)
        with patch.object(update_oink, "locked_version", return_value="v1.1.0"):
            update_oink.preflight(Path("."), "v1.1.0", True)
            with self.assertRaises(ValueError):
                update_oink.preflight(Path("."), "v1.2.0", True)

    def test_locale_override_uses_upstream_canonical_case(self):
        with tempfile.TemporaryDirectory() as d:
            root, upstream = Path(d) / "site", Path(d) / "theme"
            (root / "i18n").mkdir(parents=True)
            (upstream / "i18n").mkdir(parents=True)
            (root / "i18n/zh-CN.yaml").write_text("local translation")
            (upstream / "i18n/zh-cn.yaml").write_text("upstream translation")
            files = update_oink.snapshot(root, upstream)
            self.assertIn("i18n/zh-cn.yaml", files)
            self.assertNotIn("i18n/zh-CN.yaml", files)
            self.assertIsNotNone(files["i18n/zh-cn.yaml"])

    def test_review_catches_added_changed_deleted_files(self):
        self.assertEqual(update_oink.changes({"old": "a", "changed": "b", "stable": "c"},
                                            {"new": "d", "changed": "e", "stable": "c"}),
                         ["changed", "new", "old"])
        self.assertEqual(update_oink.changes({"a": "b"}, {"a": "b"}), [])

    def test_failed_validation_keeps_baseline(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            baseline = root / "baseline.json"
            original = json.dumps({"version": "v1.0.0", "files": {"a": "old"}})
            baseline.write_text(original)
            with patch.object(update_oink, "BASELINE", baseline), patch.object(update_oink, "preflight"), patch.object(update_oink, "prune_checksums"), \
                 patch.object(update_oink, "download_locked", return_value={"Dir": d}), \
                 patch.object(update_oink, "snapshot", return_value={"a": "new"}), \
                 patch.object(update_oink.tempfile, "mkdtemp", return_value=d), \
                 patch.object(update_oink, "validate", side_effect=ValueError("test failed")), \
                 patch("sys.argv", ["update", "v1.1.0", "--resume", "--accept-reviewed"]):
                with self.assertRaisesRegex(ValueError, "test failed"):
                    update_oink.main()
            self.assertEqual(baseline.read_text(), original)

    def test_same_target_retry_runs_gates_and_updates_baseline(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = Path(d) / "baseline.json"
            baseline.write_text(json.dumps({"version": "v1.1.0", "files": {"a": "same"}}))
            with patch.object(update_oink, "BASELINE", baseline), patch.object(update_oink, "preflight"), patch.object(update_oink, "prune_checksums"), \
                 patch.object(update_oink, "locked_version", return_value="v1.1.0"), \
                 patch.object(update_oink, "command") as command, \
                 patch.object(update_oink, "download_locked", return_value={"Dir": d}), \
                 patch.object(update_oink, "snapshot", return_value={"a": "same"}), \
                 patch.object(update_oink.tempfile, "mkdtemp", return_value=d), \
                 patch.object(update_oink, "validate") as validate, \
                 patch("sys.argv", ["update", "v1.1.0"]):
                update_oink.main()
                update_oink.main()
                command.assert_not_called()
                self.assertEqual(validate.call_count, 2)
            self.assertEqual(json.loads(baseline.read_text())["version"], "v1.1.0")

    def test_unreviewed_change_stops_before_validation(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = Path(d) / "baseline.json"
            baseline.write_text(json.dumps({"version": "v1.0.0", "files": {"a": "old"}}))
            with patch.object(update_oink, "BASELINE", baseline), patch.object(update_oink, "preflight"), patch.object(update_oink, "prune_checksums"), \
                 patch.object(update_oink, "download_locked", return_value={"Dir": d}), \
                 patch.object(update_oink, "snapshot", return_value={"a": "new"}), \
                 patch.object(update_oink.tempfile, "mkdtemp", return_value=d), \
                 patch.object(update_oink, "validate") as validate, \
                 patch("sys.argv", ["update", "v1.1.0", "--resume"]):
                with self.assertRaisesRegex(ValueError, "review required"):
                    update_oink.main()
                validate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
