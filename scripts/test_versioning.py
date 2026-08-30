#!/usr/bin/env python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0.

import argparse
import json
import tempfile
import unittest
from pathlib import Path

import versioning


ORIGIN = "https://hugegraph.apache.org/"
STAGING_ORIGIN = "https://hugegraph-oink.staged.apache.org/"
PUBLISH_PATH = "versions/1.7"
ALLOWED_PATHS = {"/docs", "/versions/1.7/docs", "/versions/1.5/docs"}


def rewrite(value: str) -> str:
    return versioning.rewrite_internal_url(
        value,
        origin=ORIGIN,
        publish_path=PUBLISH_PATH,
        allowed_paths=ALLOWED_PATHS,
    )


class VersionUrlTest(unittest.TestCase):
    def test_scopes_root_relative_urls(self) -> None:
        self.assertEqual(rewrite("/docs/"), "/versions/1.7/docs/")
        self.assertEqual(
            rewrite("/cn/docs/config/?mode=all#backend"),
            "/versions/1.7/cn/docs/config/?mode=all#backend",
        )

    def test_preserves_exact_absolute_version_destinations(self) -> None:
        self.assertEqual(rewrite("https://hugegraph.apache.org/docs"), f"{ORIGIN}docs")
        self.assertEqual(
            rewrite("https://hugegraph.apache.org/versions/1.5/docs/"),
            "https://hugegraph.apache.org/versions/1.5/docs/",
        )

    def test_rewrites_production_origin_for_staging(self) -> None:
        self.assertEqual(
            versioning.rewrite_internal_url(
                "https://hugegraph.apache.org/docs/config/",
                origin=STAGING_ORIGIN,
                publish_path=PUBLISH_PATH,
                allowed_paths=ALLOWED_PATHS,
            ),
            "https://hugegraph-oink.staged.apache.org/versions/1.7/docs/config/",
        )
        self.assertEqual(
            versioning.rewrite_internal_url(
                "https://hugegraph.apache.org/blog/",
                origin=STAGING_ORIGIN,
                publish_path="",
                allowed_paths=ALLOWED_PATHS,
            ),
            "https://hugegraph-oink.staged.apache.org/blog/",
        )

    def test_rejects_non_selector_cross_version_url(self) -> None:
        with self.assertRaises(SystemExit):
            rewrite("/versions/1.5/docs/config/")

    def test_maps_known_historical_routes(self) -> None:
        self.assertEqual(
            rewrite("https://hugegraph.apache.org/versions/1.7/docs/introduction/"),
            "https://hugegraph.apache.org/versions/1.7/docs/introduction/readme/",
        )
        self.assertEqual(
            rewrite("/docs/quickstart/hugegraph-loader#usage"),
            "/versions/1.7/docs/quickstart/toolchain/hugegraph-loader/#usage",
        )

    def test_markdown_rewrite_skips_fenced_code(self) -> None:
        source = (
            "[Docs](/docs/)\n"
            "```html\n"
            '<a href="/docs/">example</a>\n'
            "```\n"
            '<a href="/blog/">Blog</a>\n'
        )
        rendered, count = versioning.rewrite_text_urls(source, rewrite, markdown=True)
        self.assertEqual(count, 2)
        self.assertIn("[Docs](/versions/1.7/docs/)", rendered)
        self.assertIn('<a href="/docs/">example</a>', rendered)
        self.assertIn('<a href="https://hugegraph.apache.org/blog/">Blog</a>', rendered)

    def test_rejects_artifact_from_unexpected_sha(self) -> None:
        expected = {
            "id": "1.7",
            "name": "1.7",
            "ref": "release-1.7.0",
            "publishPath": "versions/1.7",
            "archived": True,
            "githubBranch": "release-1.7.0",
            "sha": "a" * 40,
        }
        actual = dict(expected)
        actual["sha"] = "b" * 40
        with self.assertRaises(SystemExit):
            versioning.require_metadata_matches(expected, actual, Path(".version.json"))

    def test_validate_command_rejects_artifact_sha_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            artifact = Path(temp_name) / "artifact"
            artifact.mkdir()
            entry = json.loads(
                (versioning.ROOT / "versions.json").read_text(encoding="utf-8")
            )["versions"][0]
            metadata = dict(entry)
            metadata.update({"sha": "b" * 40, "baseURL": ORIGIN})
            (artifact / ".version.json").write_text(
                json.dumps(metadata), encoding="utf-8"
            )
            args = argparse.Namespace(
                manifest=versioning.ROOT / "versions.json",
                version="latest",
                sha="a" * 40,
                site_origin=ORIGIN,
                artifact=artifact,
            )
            with self.assertRaises(SystemExit):
                versioning.validate_artifact(args)

    def test_rejects_active_and_ambiguous_url_schemes(self) -> None:
        for value in (
            "javascript:alert(1)",
            "data:text/html,test",
            "file:///etc/passwd",
            "ftp://example.org/file",
            "//example.org/path",
        ):
            with self.subTest(value=value), self.assertRaises(SystemExit):
                versioning.require_safe_url_scheme(value, "fixture.html")
        self.assertFalse(versioning.require_safe_url_scheme("mailto:dev@x.org", "x"))
        self.assertFalse(versioning.require_safe_url_scheme("tel:+1", "x"))
        self.assertTrue(versioning.require_safe_url_scheme("/docs/", "x"))

    def test_rejects_resolved_manifest_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            manifest = json.loads(
                (versioning.ROOT / "versions.json").read_text(encoding="utf-8")
            )
            for entry in manifest["versions"]:
                entry["sha"] = "a" * 40
            manifest["versions"][1]["name"] = "unexpected"
            path = Path(temp_name) / "resolved.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(SystemExit):
                versioning.load_resolved_manifest(path)

    def test_aggregate_rejects_metadata_sha_before_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            manifest = json.loads(
                (versioning.ROOT / "versions.json").read_text(encoding="utf-8")
            )
            for entry in manifest["versions"]:
                entry["sha"] = "a" * 40
            resolved = temp / "resolved.json"
            resolved.write_text(json.dumps(manifest), encoding="utf-8")
            latest = temp / "artifacts/latest"
            latest.mkdir(parents=True)
            metadata = dict(manifest["versions"][0])
            metadata["sha"] = "b" * 40
            (latest / ".version.json").write_text(
                json.dumps(metadata), encoding="utf-8"
            )
            args = argparse.Namespace(
                resolved_manifest=resolved,
                artifacts=temp / "artifacts",
                artifact_prefix="",
                site_origin=ORIGIN,
                output=temp / "aggregate",
                asf_profile=None,
                asf_whoami=None,
            )
            with self.assertRaises(SystemExit):
                versioning.aggregate(args)

    def test_output_cleanup_is_limited_to_temporary_descendants(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            output = temp / "output"
            output.mkdir()
            (output / "stale").write_text("stale", encoding="utf-8")
            self.assertEqual(
                versioning.prepare_output_directory(output, "fixture"),
                output.resolve(),
            )
            self.assertFalse(output.exists())
            symlink = temp / "symlink"
            symlink.symlink_to(temp, target_is_directory=True)
            with self.assertRaises(SystemExit):
                versioning.prepare_output_directory(symlink, "fixture")
        with self.assertRaises(SystemExit):
            versioning.prepare_output_directory(versioning.ROOT, "fixture")


if __name__ == "__main__":
    unittest.main()
