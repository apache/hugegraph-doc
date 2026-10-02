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

import copy
import json
import pathlib
import tempfile
import unittest

import version_cache as cache


class VersionCacheTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name).resolve()
        self.bundle = self.root / "cache"
        self.manifest = {"repository": "https://example.org/docs.git", "versions": [
            {"id": "latest", "sha": "a" * 40, "archived": False},
            {"id": "1.7", "sha": "b" * 40, "archived": True},
            {"id": "1.5", "sha": "c" * 40, "archived": True}]}
        self.write("hugo.yaml", "theme: oink")
        self.write("versions.json", json.dumps(self.manifest))
        self.write("content/en/docs/page.md", "latest body")
        self.options = dict(site_origin="https://example.org/", historical_origin="https://example.org/",
                            hugo_version="0.165.0", go_version="1.27", webp_version="1.2", year=2026)

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)
        return path

    def plan(self):
        return cache.make_plan(self.root, self.manifest, self.bundle, **self.options)

    def save(self):
        entry = self.plan()["versions"][1]
        self.write("artifact/.version.json", json.dumps({"id": "1.7", "sha": "b" * 40, "archived": True}))
        self.write("artifact/index.html", "page")
        cache.record(self.bundle, entry, self.root / "artifact")
        return entry

    def test_body_and_latest_sha_do_not_invalidate_history(self):
        before = self.plan()
        self.write("content/en/docs/page.md", "updated body")
        self.manifest["versions"][0]["sha"] = "d" * 40
        after = self.plan()
        self.assertEqual(before["cacheKey"], after["cacheKey"])
        self.assertEqual(before["versions"][1:], after["versions"][1:])

    def test_shell_changes_invalidate_history(self):
        before = self.plan()["cacheKey"]
        self.write("layouts/partials/test.html", "new shell")
        self.assertNotEqual(before, self.plan()["cacheKey"])

    def test_history_sha_only_invalidates_corresponding_version(self):
        before = self.plan()
        self.manifest["versions"][1]["sha"] = "d" * 40
        after = self.plan()
        self.assertNotEqual(before["versions"][1]["buildKey"], after["versions"][1]["buildKey"])
        self.assertEqual(before["versions"][2], after["versions"][2])

    def test_origins_toolchain_year_invalidate(self):
        for key in self.options:
            with self.subTest(key=key):
                original = self.options[key]
                before = self.plan()["cacheKey"]
                self.options[key] = 2027 if key == "year" else original + "changed"
                self.assertNotEqual(before, self.plan()["cacheKey"])
                self.options[key] = original

    def test_cache_round_trip_and_missing(self):
        self.assertFalse(self.plan()["versions"][1]["reusable"])
        entry = self.save()
        self.assertTrue(self.plan()["versions"][1]["reusable"])
        self.assertEqual([e["id"] for e in self.plan()["include"]], ["latest", "1.5"])
        self.assertTrue(cache.restore(self.bundle, entry, self.root / "restored"))
        self.assertEqual((self.root / "restored/index.html").read_text(), "page")
        self.assertFalse(self.plan()["versions"][0]["reusable"])

    def test_corruption_and_receipt_mismatch_are_misses(self):
        entry = self.save()
        cached = self.bundle / "1.7/artifact/index.html"
        cached.write_text("corrupt")
        self.assertFalse(cache.reusable(self.bundle, entry))
        cached.write_text("page")
        wrong = dict(entry, buildKey="wrong")
        self.assertFalse(cache.reusable(self.bundle, wrong))
        (self.bundle / "1.7/receipt.json").write_text("invalid json")
        self.assertFalse(cache.reusable(self.bundle, entry))

    def test_symlink_and_traversal_rejected(self):
        entry = self.save()
        (self.bundle / "1.7/artifact/link").symlink_to(self.root / "hugo.yaml")
        self.assertFalse(cache.reusable(self.bundle, entry))
        for version in ("../outside", "/tmp/outside", "..", "."):
            with self.subTest(version=version), self.assertRaises(ValueError):
                cache.version_directory(self.bundle, version)

    def test_plan_treats_symlink_cache_slot_as_miss_without_touching_target(self):
        entry = self.save()
        original = self.bundle / "1.7"
        target = self.root / "external"
        original.rename(target)
        original.symlink_to(target, target_is_directory=True)
        before = cache.snapshot(target)
        plan = self.plan()
        self.assertFalse(plan["versions"][1]["reusable"])
        self.assertIn("1.7", [e["id"] for e in plan["include"]])
        self.assertFalse(cache.restore(self.bundle, entry, self.root / "restored"))
        with self.assertRaises(ValueError):
            cache.record(self.bundle, entry, self.root / "artifact")
        self.assertEqual(before, cache.snapshot(target))
        self.assertTrue(original.is_symlink())

    def test_source_symlink_rejected(self):
        (self.root / "data").symlink_to(self.root / "content", target_is_directory=True)
        with self.assertRaises(ValueError):
            self.plan()

    def test_shared_navigation_scripts_and_assets_invalidate(self):
        for path in ("data/version_routes.json", "content/en/docs/SUMMARY.md",
                     "content/cn/docs/_nav/intro.md", "scripts/versioning.py",
                     "dist/url-contract.json", "static/favicon.svg"):
            with self.subTest(path=path):
                before = self.plan()["cacheKey"]
                self.write(path, "changed")
                self.assertNotEqual(before, self.plan()["cacheKey"])

    def test_wrong_artifact_metadata_is_not_recorded(self):
        entry = self.save()
        self.write("artifact/.version.json", json.dumps({"id": "1.5", "sha": "b" * 40}))
        with self.assertRaises(ValueError):
            cache.record(self.bundle, entry, self.root / "artifact")
        self.assertTrue(cache.reusable(self.bundle, entry))

    def test_unarchived_version_need_not_be_named_latest(self):
        self.manifest["versions"][0]["id"] = "current"
        before = self.plan()
        self.manifest["versions"][0]["sha"] = "d" * 40
        after = self.plan()
        self.assertEqual(before["cacheKey"], after["cacheKey"])
        self.assertFalse(after["versions"][0]["reusable"])

    def test_selection_is_honored(self):
        self.manifest["include"] = [copy.deepcopy(self.manifest["versions"][0])]
        self.assertEqual([e["id"] for e in self.plan()["versions"]], ["latest"])


if __name__ == "__main__":
    unittest.main()
