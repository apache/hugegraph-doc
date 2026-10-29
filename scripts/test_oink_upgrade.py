#!/usr/bin/env python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0.

import json
import os
import shutil
import sys
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch

import update_oink


class UpgradeTest(unittest.TestCase):
    def test_toolchain_failure_precedes_backup_and_lock_mutation(self):
        with patch.object(update_oink, "preflight"), \
             patch.object(update_oink, "check_toolchain", side_effect=ValueError("missing compiler")), \
             patch.object(update_oink, "prepare_work") as work, \
             patch.object(update_oink, "command") as command, \
             patch("sys.argv", ["update", "v1.3.1"]):
            with self.assertRaisesRegex(ValueError, "missing compiler"):
                update_oink.main()
            work.assert_not_called()
            command.assert_not_called()

    def test_target_hugo_and_go_requirements_fail_before_compilation(self):
        with tempfile.TemporaryDirectory() as directory:
            theme = Path(directory)
            (theme / "theme.toml").write_text('min_version = "0.170.0"\n')
            (theme / "go.mod").write_text('module example.test/theme\n\ngo 1.27.3\n')
            for hugo in ("hugo v0.168.0+extended", "hugo v0.170.0"):
                with patch.object(update_oink, "prior_release", return_value={"Dir": directory}), \
                     patch.object(update_oink, "tool_versions", return_value={"hugo": hugo, "go": "go1.27.3"}), \
                     patch.object(update_oink.subprocess, "run") as compile:
                    with self.assertRaisesRegex(ValueError, "Extended >= 0.170.0"):
                        update_oink.check_toolchain(theme, "v1.4.0")
                    compile.assert_not_called()
            with patch.object(update_oink, "prior_release", return_value={"Dir": directory}), \
                 patch.object(update_oink, "tool_versions", return_value={"hugo": "hugo v0.170.0+extended", "go": "go1.27.2"}), \
                 patch.object(update_oink.subprocess, "run") as compile:
                with self.assertRaisesRegex(ValueError, "Go >= 1.27.3"):
                    update_oink.check_toolchain(theme, "v1.4.0")
                compile.assert_not_called()

    @unittest.skipUnless(shutil.which(os.environ.get("HUGO_BIN", "hugo")), "Hugo is required")
    def test_real_hugo_libsass_smoke_never_invokes_standalone_sass(self):
        if update_oink.version_tuple(update_oink.tool_output([os.environ.get("HUGO_BIN", "hugo"), "version"])) < (0, 168, 0):
            self.skipTest("Hugo >= 0.168.0 is required")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "theme.toml").write_text('min_version = "0.168.0"\n')
            (root / "go.mod").write_text('module example.test/theme\n\ngo 1.27.3\n')
            marker = root / "sass-invoked"
            shim = root / "sass"
            shim.write_text(f"#!{sys.executable}\nfrom pathlib import Path\n"
                            f"Path({str(marker)!r}).touch()\nraise SystemExit(17)\n")
            shim.chmod(0o755)
            with patch.object(update_oink, "prior_release", return_value={"Dir": directory}), \
                 patch.dict(os.environ, {"PATH": str(root) + os.pathsep + os.environ["PATH"]}):
                versions = update_oink.check_toolchain(root, "v1.4.0")
            self.assertNotIn("sass", versions)
            self.assertFalse(marker.exists(), "Hugo must use its built-in compiler")

    def test_work_directory_preserves_before_captures_and_first_lock_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root, work = Path(directory) / "source", Path(directory) / "upgrade"
            root.mkdir()
            for name in ("go.mod", "go.sum", "oink-overrides.json"):
                (root / name).write_text("original " + name)
            (work / "before").mkdir(parents=True)
            capture = work / "before/home.png"
            capture.write_bytes(b"baseline capture")
            baseline = root / "oink-overrides.json"
            for name in ("before-site", "notes", "tools", "logs"):
                (work / name).mkdir()
                (work / name / "keep.txt").write_text("helper asset")
            resolved = update_oink.prepare_work(root, baseline, work, False, "v1.3.1")
            (root / "go.mod").write_text("upgraded lock")
            (work / "toolchain.json").write_text("existing runner output")
            self.assertEqual(update_oink.prepare_work(root, baseline, work, True, "v1.3.1"), resolved)
            self.assertEqual((work / "before/go.mod").read_text(), "original go.mod")
            self.assertEqual(capture.read_bytes(), b"baseline capture")
            with self.assertRaisesRegex(ValueError, "requires --resume"):
                update_oink.prepare_work(root, baseline, work, False, "v1.3.1")
            with self.assertRaisesRegex(ValueError, "another target"):
                update_oink.prepare_work(root, baseline, work, True, "v1.4.0")
            with self.assertRaisesRegex(ValueError, "another target or checkout"):
                update_oink.prepare_work(root / "other", baseline, work, True, "v1.3.1")
            (work / "before/go.sum").unlink()
            with self.assertRaisesRegex(ValueError, "incomplete"):
                update_oink.prepare_work(root, baseline, work, True, "v1.3.1")
            self.assertEqual((work / "before/go.mod").read_text(), "original go.mod")

    def test_work_directory_rejects_repository_and_preserves_existing_reserved_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            root.mkdir()
            baseline = root / "oink-overrides.json"
            for name in ("go.mod", "go.sum", "oink-overrides.json"):
                (root / name).write_text("original " + name)
            internal = root / "notes"
            internal.mkdir()
            internal_file = internal / "toolchain.json"
            internal_file.write_text("user settings")
            for forbidden in (internal, root, root.parent):
                with self.subTest(forbidden=forbidden), self.assertRaisesRegex(ValueError, "outside the repository"):
                    update_oink.prepare_work(root, baseline, forbidden, False, "v1.3.1")
            self.assertEqual(internal_file.read_text(), "user settings")
            self.assertFalse((internal / "before").exists())
            for reserved in ("toolchain.json", "resolved.json", "build-plan.json", "strict", "artifacts", "site", "ai",
                             "ai-disabled", "hugo-cache", "version-cache", "after", "validation-snapshot.json", "ai.json", "ai-disabled.json"):
                work = Path(directory) / ("external-" + reserved)
                work.mkdir()
                existing = work / reserved
                existing.write_text("user file")
                for resume in (False, True):
                    with self.subTest(reserved=reserved, resume=resume), self.assertRaisesRegex(ValueError, "reserved runner outputs"):
                        update_oink.prepare_work(root, baseline, work, resume, "v1.3.1")
                    self.assertEqual(existing.read_text(), "user file")
                    self.assertFalse((work / "before").exists())
                    self.assertFalse((work / "review.json").exists())

    def test_fresh_resume_records_that_backup_can_already_pin_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root, work = Path(directory) / "source", Path(directory) / "upgrade"
            root.mkdir()
            for name in ("go.mod", "go.sum", "oink-overrides.json"):
                (root / name).write_text("already upgraded")
            update_oink.prepare_work(root, root / "oink-overrides.json", work, True, "v1.3.1")
            self.assertTrue(json.loads((work / "review.json").read_text())["startedFromResume"])

    def test_check_baseline_rejects_upgrade_options_without_toolchain_or_lock_changes(self):
        with patch.object(update_oink, "download_locked") as download, \
             patch.object(update_oink, "check_toolchain") as tools, \
             patch("sys.argv", ["update", "--check-baseline", "--work-dir", "artifacts"]):
            with self.assertRaises(SystemExit):
                update_oink.main()
            tools.assert_not_called()
            download.assert_not_called()

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
            root = Path(d) / "source"
            root.mkdir()
            (root / "go.mod").write_text("before mod")
            (root / "go.sum").write_text("before sum")
            baseline = root / "baseline.json"
            original = json.dumps({"version": "v1.0.0", "files": {"a": "old"}})
            baseline.write_text(original)
            with patch.object(update_oink, "ROOT", root), patch.object(update_oink, "check_toolchain", return_value={}), patch.object(update_oink, "verify_hugo_graph", return_value="verified"), \
                 patch.object(update_oink, "prior_release", return_value={"Dir": str(root / "prior")}), \
                 patch.object(update_oink, "BASELINE", baseline), patch.object(update_oink, "preflight"), patch.object(update_oink, "prune_checksums"), \
                 patch.object(update_oink, "download_locked", return_value={"Dir": d}), \
                 patch.object(update_oink, "snapshot", return_value={"a": "new"}), \
                 patch.object(update_oink.tempfile, "mkdtemp", return_value=str(root.parent / "artifacts")), \
                 patch.object(update_oink, "validate", side_effect=ValueError("test failed")), \
                 patch("sys.argv", ["update", "v1.1.0", "--resume", "--accept-reviewed"]):
                with self.assertRaisesRegex(ValueError, "test failed"):
                    update_oink.main()
            self.assertEqual(baseline.read_text(), original)
            report = json.loads((root.parent / "artifacts/review.json").read_text())
            self.assertEqual(report["priorModuleDir"], str(root / "prior"))
            self.assertEqual(report["targetModuleDir"], d)
            self.assertEqual(report["changes"], [{"path": "a", "kind": "changed",
                                                 "reason": "local override or watched upstream interface"}])
            self.assertIn("not a list of required local edits", report["reviewMeaning"])
            self.assertIn("v1.1.0 --resume --accept-reviewed", report["resumeCommand"])
            (root / "go.mod").write_text("changed")
            (root / "go.sum").write_text("changed")
            subprocess.run(report["recoveryCommand"], shell=True, check=True)
            self.assertEqual((root / "go.mod").read_text(), "before mod")
            self.assertEqual((root / "go.sum").read_text(), "before sum")

    def test_same_target_retry_runs_gates_and_updates_baseline(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "source"
            root.mkdir()
            (root / "go.mod").write_text("before mod")
            (root / "go.sum").write_text("before sum")
            baseline = root / "baseline.json"
            baseline.write_text(json.dumps({"version": "v1.1.0", "files": {"a": "same"}}))
            with patch.object(update_oink, "ROOT", root), patch.object(update_oink, "check_toolchain", return_value={}), patch.object(update_oink, "verify_hugo_graph", return_value="verified"), \
                 patch.object(update_oink, "prior_release", return_value={"Dir": str(root / "prior")}), \
                 patch.object(update_oink, "BASELINE", baseline), patch.object(update_oink, "preflight"), patch.object(update_oink, "prune_checksums"), \
                 patch.object(update_oink, "locked_version", return_value="v1.1.0"), \
                 patch.object(update_oink, "command") as command, \
                 patch.object(update_oink, "download_locked", return_value={"Dir": d}), \
                 patch.object(update_oink, "snapshot", return_value={"a": "same"}), \
                 patch.object(update_oink.tempfile, "mkdtemp", return_value=str(root.parent / "artifacts")), \
                 patch.object(update_oink, "validate") as validate, \
                 patch("sys.argv", ["update", "v1.1.0"]):
                update_oink.main()
                with patch("sys.argv", ["update", "v1.1.0", "--resume", "--work-dir", str(root.parent / "artifacts")]):
                    update_oink.main()
                command.assert_not_called()
                self.assertEqual(validate.call_count, 2)
            self.assertEqual(json.loads(baseline.read_text())["version"], "v1.1.0")

    def test_unreviewed_change_stops_before_validation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "source"
            root.mkdir()
            (root / "go.mod").write_text("before mod")
            (root / "go.sum").write_text("before sum")
            baseline = root / "baseline.json"
            baseline.write_text(json.dumps({"version": "v1.0.0", "files": {"a": "old"}}))
            with patch.object(update_oink, "ROOT", root), patch.object(update_oink, "check_toolchain", return_value={}), patch.object(update_oink, "verify_hugo_graph", return_value="verified"), \
                 patch.object(update_oink, "prior_release", return_value={"Dir": str(root / "prior")}), \
                 patch.object(update_oink, "BASELINE", baseline), patch.object(update_oink, "preflight"), patch.object(update_oink, "prune_checksums"), \
                 patch.object(update_oink, "download_locked", return_value={"Dir": d}), \
                 patch.object(update_oink, "snapshot", return_value={"a": "new"}), \
                 patch.object(update_oink.tempfile, "mkdtemp", return_value=str(root.parent / "artifacts")), \
                 patch.object(update_oink, "validate") as validate, \
                 patch("sys.argv", ["update", "v1.1.0", "--resume"]):
                with self.assertRaisesRegex(ValueError, "review required"):
                    update_oink.main()
                validate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
