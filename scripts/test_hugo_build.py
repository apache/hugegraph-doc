#!/usr/bin/env python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0.

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from hugo_build import is_unexpected_warning, run_hugo


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/hugo_build.py"
LIBSASS_PAYLOAD = (
    "deprecated: css.Sass: libsass was deprecated in Hugo v0.153.0 and will be removed in a future release. "
    "Use dartsass instead. See https://gohugo.io/functions/css/sass/#dart-sass"
)
LIBSASS_WARNING = "WARN  " + LIBSASS_PAYLOAD + "\n"


class HugoBuildTest(unittest.TestCase):
    def invoke(self, source, *args):
        return subprocess.run(
            [sys.executable, str(RUNNER), sys.executable, "-c", source, *args],
            text=True, capture_output=True, timeout=15,
        )

    def test_classifier_allows_only_the_exact_libsass_payload(self):
        self.assertFalse(is_unexpected_warning(LIBSASS_WARNING))
        self.assertFalse(is_unexpected_warning("WARN\t" + LIBSASS_PAYLOAD + "\r\n"))
        self.assertFalse(is_unexpected_warning("\033[33mWARN\033[0m  " + LIBSASS_PAYLOAD + "\n"))
        for line in (
            "WARN  i18n|MISSING_TRANSLATION|en|missing_key\n",
            "WARN  Duplicate target paths: /collision/index.html\n",
            "WARN  unknown warning\n",
            "WARN  deprecated: another feature will be removed\n",
            "WARN  " + LIBSASS_PAYLOAD + " extra\n",
            "WARN  " + LIBSASS_PAYLOAD.replace("0.153.0", "0.154.0") + "\n",
            "WARN  " + LIBSASS_PAYLOAD.replace("libsass", "dartsass") + "\n",
        ):
            with self.subTest(line=line):
                self.assertTrue(is_unexpected_warning(line))

    def test_classifier_does_not_treat_ordinary_output_as_a_warning_record(self):
        for line in (
            "INFO  build succeeded\n", "WARNINGS in documentation\n",
            "page body mentions WARN  example\n", "  WARN is source text\n", "\n",
        ):
            with self.subTest(line=line):
                self.assertFalse(is_unexpected_warning(line))

    def test_cli_keeps_both_output_streams_and_the_expected_warning(self):
        before = "Starting build\n"
        after = "Total in 12 ms\n"
        result = self.invoke(
            "import sys; sys.stdout.write(sys.argv[1]); sys.stdout.flush(); "
            "sys.stderr.write(sys.argv[2]); sys.stderr.flush(); sys.stdout.write(sys.argv[3])",
            before, LIBSASS_WARNING, after,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, before + LIBSASS_WARNING + after)

    def test_cli_fails_for_other_warnings_from_either_stream_after_draining_output(self):
        for stream in ("stdout", "stderr"):
            with self.subTest(stream=stream):
                result = self.invoke(
                    "import sys; sys.stdout.write(sys.argv[1]); sys.stdout.flush(); "
                    "getattr(sys, sys.argv[2]).write('WARN  unexpected warning\\n'); "
                    "getattr(sys, sys.argv[2]).flush(); sys.stdout.write('finished build\\n')",
                    LIBSASS_WARNING, stream,
                )
                self.assertEqual(result.returncode, 1)
                self.assertIn(LIBSASS_WARNING, result.stdout)
                self.assertIn("WARN  unexpected warning\n", result.stdout)
                self.assertIn("finished build\n", result.stdout)

    def test_cli_preserves_the_child_failure_status_even_with_another_warning(self):
        result = self.invoke(
            "import sys; sys.stderr.write('WARN  unexpected warning\\nERROR compilation failed\\n'); sys.exit(7)"
        )
        self.assertEqual(result.returncode, 7)
        self.assertIn("WARN  unexpected warning\nERROR compilation failed\n", result.stdout)

    @unittest.skipUnless(os.name == "posix", "POSIX signal exit convention")
    def test_cli_converts_child_signal_to_shell_exit_status(self):
        result = self.invoke("import os, signal; os.kill(os.getpid(), signal.SIGTERM)")
        self.assertEqual(result.returncode, 143)

    def test_runner_preserves_argument_boundaries_cwd_and_environment(self):
        with tempfile.TemporaryDirectory(prefix="hugo build with spaces ") as directory:
            env = dict(os.environ, HUGO_RUNNER_SENTINEL="value with spaces")
            run_hugo(
                [
                    sys.executable, "-c",
                    "import json, os, pathlib, sys; "
                    "pathlib.Path('observed.json').write_text(json.dumps("
                    "{'cwd': os.getcwd(), 'env': os.environ['HUGO_RUNNER_SENTINEL'], 'args': sys.argv[1:]}))",
                    "path with spaces", "literal;$value",
                ],
                cwd=directory, env=env,
            )
            observed = json.loads((Path(directory) / "observed.json").read_text())
            self.assertEqual(Path(observed["cwd"]).resolve(), Path(directory).resolve())
            self.assertEqual(observed["env"], "value with spaces")
            self.assertEqual(observed["args"], ["path with spaces", "literal;$value"])

    def test_runner_raises_for_a_failing_child(self):
        command = [sys.executable, "-c", "raise SystemExit(9)"]
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            run_hugo(command)
        self.assertEqual(caught.exception.returncode, 9)
        self.assertEqual(caught.exception.cmd, command)

    @unittest.skipUnless(shutil.which(os.environ.get("HUGO_BIN", "hugo")), "Hugo executable is required")
    def test_real_hugo_missing_translation_and_duplicate_path_are_blocking(self):
        hugo = shutil.which(os.environ.get("HUGO_BIN", "hugo"))
        for kind, expected in (
            ("translation", "MISSING_TRANSLATION"),
            ("duplicate", "Duplicate target paths"),
        ):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "hugo.toml").write_text(
                    'baseURL = "https://example.test/"\n'
                    'disableKinds = ["taxonomy", "term", "RSS", "sitemap", "robotsTXT", "404", "section"]\n'
                )
                (root / "layouts").mkdir()
                (root / "layouts/home.html").write_text(
                    '{{ i18n "missing_guard_fixture" }}' if kind == "translation" else "home"
                )
                (root / "layouts/single.html").write_text("{{ .Content }}")
                if kind == "translation":
                    (root / "i18n").mkdir()
                    (root / "i18n/en.toml").write_text('[existing]\nother = "Existing translation"\n')
                if kind == "duplicate":
                    (root / "content").mkdir()
                    for name in ("one", "two"):
                        (root / "content" / (name + ".md")).write_text(
                            "---\ntitle: " + name + "\nurl: /collision/\n---\nbody\n"
                        )
                env = dict(os.environ)
                env.pop("HUGO_PANICONWARNING", None)
                command = [
                    hugo, "--source", str(root), "--environment", "production",
                    "--printPathWarnings", "--printI18nWarnings", "--logLevel", "info",
                ]
                baseline = subprocess.run(command, text=True, capture_output=True, env=env, timeout=30)
                self.assertEqual(baseline.returncode, 0, baseline.stdout + baseline.stderr)
                self.assertIn(expected, baseline.stdout + baseline.stderr)
                guarded = subprocess.run(
                    [sys.executable, str(RUNNER), *command],
                    text=True, capture_output=True, env=env, timeout=30,
                )
                self.assertEqual(guarded.returncode, 1, guarded.stdout + guarded.stderr)
                self.assertIn(expected, guarded.stdout + guarded.stderr)


if __name__ == "__main__":
    unittest.main()
