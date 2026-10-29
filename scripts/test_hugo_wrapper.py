import json
import os
import pathlib
import stat
import shlex
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = pathlib.Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "hugo.sh"

LIBSASS_WARNING = (
    "WARN  deprecated: css.Sass: libsass was deprecated in Hugo v0.153.0 and will be removed in a future release. "
    "Use dartsass instead. See https://gohugo.io/functions/css/sass/#dart-sass\n"
)


class HugoWrapperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "calls.jsonl"
        self._write_executable(
            "python3",
            """#!/bin/sh
case "$1" in
  */hugo_build.py) exec __REAL_PYTHON__ "$@" ;;
esac
printf '{"tool":"python3","args":[' >> "$HG_WRAPPER_TEST_LOG"
first=1
output=
previous=
for arg in "$@"; do
  if [ "$first" -eq 0 ]; then printf ',' >> "$HG_WRAPPER_TEST_LOG"; fi
  first=0
  printf '"%s"' "$arg" >> "$HG_WRAPPER_TEST_LOG"
  if [ "$previous" = "--output" ]; then output=$arg; fi
  previous=$arg
done
printf ']}\\n' >> "$HG_WRAPPER_TEST_LOG"
printf '%s\\n' '{"params":{"versions":[1,2,3,4,5]}}' > "$output"
""".replace("__REAL_PYTHON__", shlex.quote(sys.executable)),
        )
        self._write_executable(
            "hugo",
            """#!/bin/sh
printf '{"tool":"hugo","args":[' >> "$HG_WRAPPER_TEST_LOG"
first=1
config=
previous=
for arg in "$@"; do
  if [ "$first" -eq 0 ]; then printf ',' >> "$HG_WRAPPER_TEST_LOG"; fi
  first=0
  printf '"%s"' "$arg" >> "$HG_WRAPPER_TEST_LOG"
  if [ "$previous" = "--config" ]; then config=$arg; fi
  previous=$arg
done
printf ']}\\n' >> "$HG_WRAPPER_TEST_LOG"
generated=${config#*,}
test -f "$generated"
grep -q '"versions":\\[1,2,3,4,5\\]' "$generated"
printf '%s' "${HG_WRAPPER_HUGO_STDOUT:-}"
printf '%s' "${HG_WRAPPER_HUGO_STDERR:-}" >&2
exit "${HG_WRAPPER_HUGO_EXIT:-0}"
""",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_executable(self, name: str, source: str) -> None:
        path = self.bin / name
        path.write_text(source, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def invoke_wrapper(
        self, *args: str, environment_overrides: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PATH"] = f"{self.bin}{os.pathsep}{environment['PATH']}"
        # These are argument-contract tests, not live server launches. Explicit
        # task-local compiler overrides must not escape the test's own shims.
        environment["HUGO_BIN"] = str(self.bin / "hugo")
        environment["PYTHON_BIN"] = str(self.bin / "python3")
        environment["HG_WRAPPER_TEST_LOG"] = str(self.log)
        environment.pop("HG_DOC_VERSION", None)
        environment.pop("HG_DOC_SITE_ORIGIN", None)
        if environment_overrides:
            environment.update(environment_overrides)
        return subprocess.run(
            [str(WRAPPER), *args],
            cwd=ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )

    def calls(self) -> list[dict]:
        if not self.log.exists():
            return []
        return [
            json.loads(line)
            for line in self.log.read_text(encoding="utf-8").splitlines()
        ]

    def run_wrapper(
        self, *args: str, environment_overrides: dict[str, str] | None = None
    ) -> list[dict]:
        result = self.invoke_wrapper(
            *args, environment_overrides=environment_overrides
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return self.calls()

    def test_server_derives_manifest_config_and_safely_forwards_arguments(self) -> None:
        calls = self.run_wrapper("server", "--port", "1414", "--bind", "127.0.0.1")
        self.assertEqual(calls[0]["tool"], "python3")
        self.assertEqual(
            calls[0]["args"][0:2], ["scripts/versioning.py", "config"]
        )
        self.assertNotIn("--version", calls[0]["args"])
        self.assertIn("--site-origin", calls[0]["args"])
        origin_index = calls[0]["args"].index("--site-origin") + 1
        self.assertEqual(calls[0]["args"][origin_index], "http://localhost:1414/")
        self.assertEqual(calls[1]["args"][0], "server")
        self.assertEqual(
            calls[1]["args"][-4:],
            ["--port", "1414", "--bind", "127.0.0.1"],
        )

    def test_task_local_tool_overrides_do_not_launch_real_tools(self) -> None:
        with patch.dict(os.environ, {"HUGO_BIN": "/unavailable/task/hugo", "PYTHON_BIN": "/unavailable/task/python"}):
            calls = self.run_wrapper("server")
        self.assertEqual([call["tool"] for call in calls], ["python3", "hugo"])

    def test_explicit_version_is_forwarded_only_when_requested(self) -> None:
        calls = self.run_wrapper(
            "build", environment_overrides={"HG_DOC_VERSION": "1.7"}
        )
        args = calls[0]["args"]
        self.assertEqual(args[args.index("--version") + 1], "1.7")

    def test_base_url_flag_wins_over_environment_and_pins_the_origin(self) -> None:
        calls = self.run_wrapper(
            "server",
            "--baseURL=https://preview.example/docs/",
            environment_overrides={
                "HG_DOC_SITE_ORIGIN": "https://other.example/"
            },
        )
        config_args = calls[0]["args"]
        self.assertEqual(
            config_args[config_args.index("--site-origin") + 1],
            "https://preview.example/docs/",
        )
        hugo_args = calls[1]["args"]
        self.assertIn("--appendPort=false", hugo_args)
        self.assertEqual(hugo_args[-1], "--baseURL=https://preview.example/docs/")

    def test_documented_origin_and_port_spellings_drive_generated_config(self) -> None:
        cases = (
            (("--baseURL", "https://long.example/"), "https://long.example/", True),
            (("-b", "https://short.example/"), "https://short.example/", True),
            (("-b=https://equals.example/",), "https://equals.example/", True),
            (("-bhttps://cluster.example/",), "https://cluster.example/", True),
            (("--port", "1414"), "http://localhost:1414/", False),
            (("--port=1515",), "http://localhost:1515/", False),
            (("-p=1616",), "http://localhost:1616/", False),
            (("-p1717",), "http://localhost:1717/", False),
        )
        for args, expected_origin, environment_set in cases:
            with self.subTest(args=args):
                self.log.unlink(missing_ok=True)
                environment_overrides = (
                    {"HG_DOC_SITE_ORIGIN": "https://environment.example/"}
                    if environment_set
                    else None
                )
                calls = self.run_wrapper(
                    "server",
                    *args,
                    environment_overrides=environment_overrides,
                )
                config_args = calls[0]["args"]
                self.assertEqual(
                    config_args[config_args.index("--site-origin") + 1],
                    expected_origin,
                )

    def test_build_enforces_strict_warnings_with_the_libsass_exception(self) -> None:
        calls = self.run_wrapper("build", "--destination", "custom public with spaces")
        args = calls[1]["args"]
        self.assertNotIn("build", args)
        for required in (
            "--cleanDestinationDir",
            "--gc",
            "--minify",
            "--environment",
            "production",
            "--printPathWarnings",
            "--printI18nWarnings",
        ):
            self.assertIn(required, args)
        self.assertNotIn("--panicOnWarning", args)
        self.assertIn("--logLevel", args)
        self.assertIn("info", args)
        self.assertEqual(args[-2:], ["--destination", "custom public with spaces"])

    def test_build_allows_only_the_exact_libsass_warning_and_keeps_output(self) -> None:
        output = "Starting Hugo build\n" + LIBSASS_WARNING + "Total in 12 ms\n"
        result = self.invoke_wrapper(
            "build", environment_overrides={"HG_WRAPPER_HUGO_STDERR": output}
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(output, result.stdout + result.stderr)

    def test_build_rejects_other_hugo_warnings_even_beside_libsass(self) -> None:
        for warning in (
            "WARN  i18n|MISSING_TRANSLATION|en|missing_key\n",
            "WARN  Duplicate target paths: /collision/index.html\n",
            "WARN  deprecated: another feature will be removed\n",
            LIBSASS_WARNING.rstrip("\n") + " unexpected suffix\n",
        ):
            with self.subTest(warning=warning):
                result = self.invoke_wrapper(
                    "build",
                    environment_overrides={
                        "HG_WRAPPER_HUGO_STDOUT": "build output before warning\n",
                        "HG_WRAPPER_HUGO_STDERR": LIBSASS_WARNING + warning + "build output after warning\n",
                    },
                )
                self.assertNotEqual(result.returncode, 0)
                output = result.stdout + result.stderr
                self.assertIn(warning, output)
                self.assertIn("build output before warning\n", output)
                self.assertIn("build output after warning\n", output)

    def test_build_preserves_hugo_failure_status_and_diagnostics(self) -> None:
        result = self.invoke_wrapper(
            "build",
            environment_overrides={
                "HG_WRAPPER_HUGO_EXIT": "7",
                "HG_WRAPPER_HUGO_STDERR": "WARN  unexpected warning\nERROR Hugo failed\n",
            },
        )
        self.assertEqual(result.returncode, 7)
        self.assertIn("ERROR Hugo failed\n", result.stdout + result.stderr)

    def test_documented_preview_and_build_use_the_wrapper(self) -> None:
        for relative in ("README.md", "contribution.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("hugo server", text)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        contribution = (ROOT / "contribution.md").read_text(encoding="utf-8")
        self.assertGreaterEqual(readme.count("scripts/hugo.sh server"), 4)
        self.assertGreaterEqual(readme.count("scripts/hugo.sh build"), 2)
        self.assertIn("scripts/hugo.sh server", contribution)
        self.assertIn("scripts/hugo.sh build", contribution)


if __name__ == "__main__":
    unittest.main()
