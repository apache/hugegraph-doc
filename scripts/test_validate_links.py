#!/usr/bin/env python3

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0.

from __future__ import annotations

import pathlib
import shutil
import subprocess
import tempfile
import unittest


VALIDATOR = pathlib.Path(__file__).parents[1] / "dist/validate-links.sh"


class ValidateLinksImagesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary_directory.name)
        (self.root / "dist").mkdir()
        (self.root / "content/en").mkdir(parents=True)
        shutil.copy2(VALIDATOR, self.root / "dist/validate-links.sh")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write_content(self, link: str) -> None:
        (self.root / "content/en/page.md").write_text(
            f"![diagram]({link})\n", encoding="utf-8"
        )

    def write_file(self, relative: str) -> pathlib.Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"image")
        return path

    def run_validator(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", "dist/validate-links.sh"],
            cwd=self.root,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_images_path_maps_to_assets_images(self) -> None:
        self.write_content("/images/docs/diagram.png")
        self.write_file("assets/images/docs/diagram.png")

        result = self.run_validator()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Link validation passed!", result.stdout)

    def test_images_path_falls_back_to_static_images(self) -> None:
        self.write_content("/images/docs/legacy.png")
        self.write_file("static/images/docs/legacy.png")

        result = self.run_validator()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_image_fails_closed(self) -> None:
        self.write_content("/images/docs/missing.png")

        result = self.run_validator()

        self.assertEqual(result.returncode, 1)
        self.assertIn("Error: Broken link", result.stdout)
        self.assertIn("assets/images/docs/missing.png", result.stdout)

    def test_images_path_cannot_escape_with_parent_segments(self) -> None:
        self.write_content("/images/%2e%2e/secret.png")
        self.write_file("assets/secret.png")

        result = self.run_validator()

        self.assertEqual(result.returncode, 1)
        self.assertIn("Error: Link resolves outside content directory", result.stdout)

    def test_static_fallback_cannot_escape_static_images(self) -> None:
        self.write_content("/images/%2e%2e/%2e%2e/static/secret.png")
        self.write_file("static/secret.png")

        result = self.run_validator()

        self.assertEqual(result.returncode, 1)
        self.assertIn("Error: Link resolves outside content directory", result.stdout)

    def test_assets_symlink_escape_is_not_hidden_by_static_fallback(self) -> None:
        self.write_content("/images/docs/escape.png")
        outside = self.write_file("private/escape.png")
        asset = self.root / "assets/images/docs/escape.png"
        asset.parent.mkdir(parents=True)
        asset.symlink_to(outside)
        self.write_file("static/images/docs/escape.png")

        result = self.run_validator()

        self.assertEqual(result.returncode, 1)
        self.assertIn("Error: Link resolves outside content directory", result.stdout)

    def test_broken_assets_symlink_is_not_hidden_by_static_fallback(self) -> None:
        self.write_content("/images/docs/broken.png")
        asset = self.root / "assets/images/docs/broken.png"
        asset.parent.mkdir(parents=True)
        asset.symlink_to(self.root / "missing/broken.png")
        self.write_file("static/images/docs/broken.png")

        result = self.run_validator()

        self.assertEqual(result.returncode, 1)
        self.assertIn("Error: Link resolves outside content directory", result.stdout)


if __name__ == "__main__":
    unittest.main()
