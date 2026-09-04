import json
import os
import pathlib
import stat
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "hugo.sh"


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
""",
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
""",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_executable(self, name: str, source: str) -> None:
        path = self.bin / name
        path.write_text(source, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def run_wrapper(self, *args: str) -> list[dict]:
        environment = os.environ.copy()
        environment["PATH"] = f"{self.bin}{os.pathsep}{environment['PATH']}"
        environment["HG_WRAPPER_TEST_LOG"] = str(self.log)
        result = subprocess.run(
            [str(WRAPPER), *args],
            cwd=ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return [
            json.loads(line)
            for line in self.log.read_text(encoding="utf-8").splitlines()
        ]

    def test_server_derives_manifest_config_and_safely_forwards_arguments(self) -> None:
        calls = self.run_wrapper("server", "--port", "1414", "--bind", "127.0.0.1")
        self.assertEqual(calls[0]["tool"], "python3")
        self.assertEqual(calls[0]["args"][0:3], [
            "scripts/versioning.py",
            "config",
            "--version",
        ])
        self.assertIn("--site-origin", calls[0]["args"])
        self.assertEqual(calls[1]["args"][0], "server")
        self.assertEqual(
            calls[1]["args"][-4:],
            ["--port", "1414", "--bind", "127.0.0.1"],
        )

    def test_build_enforces_the_warning_strict_production_contract(self) -> None:
        calls = self.run_wrapper("build", "--destination", "custom-public")
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
            "--panicOnWarning",
        ):
            self.assertIn(required, args)
        self.assertEqual(args[-2:], ["--destination", "custom-public"])

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
