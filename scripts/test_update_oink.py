#!/usr/bin/env python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0.

from pathlib import Path
import tempfile
import unittest
import json
from unittest.mock import patch

import update_oink

from oink_module import MODULE
from update_oink import describe_changes, prune_checksums, snapshot


class UpgradeInventoryTest(unittest.TestCase):
    def test_validation_builds_both_ai_modes_before_browser_tests(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / "resolved.json").write_text(json.dumps({"versions": []}))
            with patch.object(update_oink, "run") as run:
                update_oink.validate(work)
            calls = run.call_args_list
            browser = next(call for call in calls if call.args[0] == ["npm", "run", "test:ci"])
            for name, config, variable in [("ai", "ai-enabled", "AI_SITE_ROOT"),
                                            ("ai-disabled", "ai-disabled", "AI_DISABLED_SITE_ROOT")]:
                self.assertEqual(browser.kwargs["env"][variable], str(work / name))
                builds = [call for call in calls if "--destination" in call.args[0]
                          and call.args[0][call.args[0].index("--destination") + 1] == work / name]
                self.assertEqual(len(builds), 1)
                self.assertIn(f"tests/e2e/{config}.yaml", str(builds[0].args[0]))
                self.assertLess(calls.index(builds[0]), calls.index(browser))

    def test_resume_cleans_interrupted_upgrade_before_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = f"{MODULE} v1.1.0 h1:new\n{MODULE} v1.1.0/go.mod h1:newmod\n"
            (root / "go.sum").write_text(f"{MODULE} v1.0.0 h1:old\n" + target)
            baseline = root / "baseline.json"
            baseline.write_text(json.dumps({"version": "v1.1.0", "files": {}}))

            def download(path):
                self.assertEqual((path / "go.sum").read_text(), target)
                return {"Dir": str(root)}

            with patch.object(update_oink, "ROOT", root), patch.object(update_oink, "BASELINE", baseline), \
                 patch.object(update_oink, "locked_version", return_value="v1.1.0"), \
                 patch.object(update_oink, "download_locked", side_effect=download), \
                 patch.object(update_oink, "snapshot", return_value={}), \
                 patch.object(update_oink, "validate") as validate, \
                 patch.object(update_oink, "command") as command, \
                 patch.object(update_oink.tempfile, "mkdtemp", return_value=directory), \
                 patch("sys.argv", ["update", "v1.1.0", "--resume"]):
                update_oink.main()
                update_oink.main()
                command.assert_not_called()
                self.assertEqual(validate.call_count, 2)

    def test_data_override_and_locale_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            root, upstream = Path(directory) / "site", Path(directory) / "theme"
            for base, paths in [(root, ["data/brand.yaml", "data/site-only.yaml", "i18n/zh_CN.yaml"]),
                                (upstream, ["data/brand.yaml", "data/upstream-only.yaml", "i18n/zh-cn.yaml"])]:
                for name in paths:
                    path = base / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("value")
            result = snapshot(root, upstream)
            self.assertIn("data/brand.yaml", result)
            self.assertIn("i18n/zh-cn.yaml", result)
            self.assertNotIn("data/site-only.yaml", result)
            self.assertNotIn("data/upstream-only.yaml", result)
            before = dict(result)
            (root / "data/brand.yaml").unlink()
            self.assertIn("removed: data/brand.yaml", describe_changes(before, snapshot(root, upstream)))

    def test_change_diagnostics(self):
        self.assertEqual(describe_changes({"b": "old", "c": "old"}, {"a": "new", "b": "new"}),
                         ["added: a", "changed: b", "removed: c"])

    def test_upgrade_removes_old_checksums(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = f"{MODULE} v1.0.0 h1:old\n{MODULE} v1.0.0/go.mod h1:oldmod\n"
            new = f"{MODULE} v1.1.0 h1:new\n{MODULE} v1.1.0/go.mod h1:newmod\n"
            (root / "go.sum").write_text(old + new)
            prune_checksums(root, "v1.1.0")
            self.assertEqual((root / "go.sum").read_text(), new)
            with self.assertRaises(ValueError):
                prune_checksums(root, "v9.0.0")
            self.assertEqual((root / "go.sum").read_text(), new)


if __name__ == "__main__":
    unittest.main()
