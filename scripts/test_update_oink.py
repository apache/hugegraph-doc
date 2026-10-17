#!/usr/bin/env python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0.

from pathlib import Path
import tempfile
import unittest
import zipfile
import json
import os
import shutil
import subprocess
import sys
from unittest.mock import patch

import update_oink

from oink_module import MODULE, SITE_MODULE
from update_oink import describe_changes, prune_checksums, snapshot


class UpgradeInventoryTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which(os.environ.get("HUGO_BIN", "hugo")), "Hugo executable is required")
    def test_real_hugo_graph_with_empty_module_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "site"
            root.mkdir()
            before = {}
            for name in ("go.mod", "go.sum"):
                before[name] = (update_oink.ROOT / name).read_bytes()
                (root / name).write_bytes(before[name])
            (root / "hugo.yaml").write_text("module:\n  imports:\n    - path: " + MODULE + "\n")
            with patch.dict(os.environ, {"HUGO_CACHEDIR": str(Path(directory) / "empty-cache")}):
                version = update_oink.download_locked(root)["Version"]
                graph = update_oink.verify_hugo_graph(root, version)
                self.assertEqual(graph.strip(), f"{SITE_MODULE} {MODULE}@{version}")
                self.assertNotIn("downloading modules", graph)
            for name, contents in before.items():
                self.assertEqual((root / name).read_bytes(), contents)

    @unittest.skipUnless(shutil.which(os.environ.get("GO_BIN", "go")), "Go executable is required")
    def test_target_release_resolution_preserves_both_original_locks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            root.mkdir()
            before = {}
            for name in ("go.mod", "go.sum"):
                before[name] = (update_oink.ROOT / name).read_bytes()
                (root / name).write_bytes(before[name])
            # Download a release outside the currently pinned graph, which would
            # normally add its checksums when executed against the real source.
            other = "v1.2.0" if b"v1.3.1" in before["go.mod"] else "v1.3.1"
            self.assertEqual(update_oink.prior_release(root, other)["Version"], other)
            for name, contents in before.items():
                self.assertEqual((root / name).read_bytes(), contents)

    def test_baseline_check_never_requires_sass_or_compiles(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline.json"
            baseline.write_text(json.dumps({"version": "v1.2.0", "files": {}}))
            with patch.object(update_oink, "BASELINE", baseline), \
                 patch.object(update_oink, "download_locked", return_value={"Version": "v1.2.0", "Dir": directory}), \
                 patch.object(update_oink, "verify_hugo_graph"), \
                 patch.object(update_oink, "snapshot", return_value={}), \
                 patch.object(update_oink, "check_toolchain") as tools, \
                 patch.object(update_oink.subprocess, "run") as compile, \
                 patch("sys.argv", ["update", "--check-baseline"]):
                update_oink.main()
                tools.assert_not_called()
                compile.assert_not_called()

    def test_hugo_graph_suppresses_cold_cache_progress_without_relaxing_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            graph = f"{SITE_MODULE} {MODULE}@v1.2.0\n"
            with patch.object(update_oink.subprocess, "check_output", return_value=graph) as command:
                self.assertEqual(update_oink.verify_hugo_graph(root, "v1.2.0"), graph)
                self.assertIn("--quiet", command.call_args.args[0])
            with patch.object(update_oink.subprocess, "check_output", return_value=graph + "unexpected diagnostic output\n"):
                with self.assertRaises(ValueError):
                    update_oink.verify_hugo_graph(root, "v1.2.0")

    def test_default_hugo_is_resolved_from_subprocess_path(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(update_oink.shutil, "which") as which:
            self.assertNotIn("HUGO_BIN", update_oink.release_environment())
            which.assert_not_called()

    def test_release_graph_ignores_local_preview_environment_and_restores_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hugo = root / "hugo"
            hugo.write_text(f"#!{sys.executable}\n" +
                            "import os\n" +
                            "assert 'HUGO_MODULE_REPLACEMENTS' not in os.environ\n" +
                            "assert 'HUGO_THEME' not in os.environ\n" +
                            "assert os.environ['GOWORK'] == 'off'\n" +
                            "assert os.environ['HUGO_MODULE_WORKSPACE'] == 'off'\n" +
                            f"print('{SITE_MODULE} {MODULE}@v1.2.0')\n")
            hugo.chmod(0o755)
            preview = {"HUGO_BIN": str(hugo), "HUGO_MODULE_REPLACEMENTS": "oink -> /tmp/local-theme",
                       "HUGO_THEME": "/tmp/local-preview", "GOWORK": "/tmp/go.work", "HUGO_MODULE_WORKSPACE": "/tmp/hugo.work"}
            with patch.dict(os.environ, preview):
                with update_oink.isolated_release():
                    update_oink.verify_hugo_graph(root, "v1.2.0")
                for key, value in preview.items():
                    self.assertEqual(os.environ[key], value)

    def test_hugo_graph_rejects_wrong_release_replacement_and_vendor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for graph in (f"{SITE_MODULE} {MODULE}@v1.1.0\n", f"{SITE_MODULE} {MODULE}@v1.2.0+vendor\n",
                          f"{SITE_MODULE} {MODULE}@v1.2.0 => /tmp/local\n", f"{SITE_MODULE} unrelated@v1.2.0\n",
                          f"{SITE_MODULE} {MODULE}@v1.2.0\n{SITE_MODULE} /tmp/local-preview\n",
                          f"{SITE_MODULE} {MODULE}@v1.2.0\n{SITE_MODULE} extra@v1.0.0\n",
                          f"{SITE_MODULE} {MODULE}@v1.2.0\n{SITE_MODULE} {MODULE}@v1.1.0\n",
                          f"{SITE_MODULE} {MODULE}@v1.2.0\n{MODULE}@v1.1.0 dependency@v1.0.0\n",
                          f"{SITE_MODULE} {MODULE}@v1.2.0\n{MODULE}@v1.2.0 => /tmp/local\n"):
                with patch.object(update_oink.subprocess, "check_output", return_value=graph):
                    with self.assertRaisesRegex(ValueError, "expected Hugo"):
                        update_oink.verify_hugo_graph(root, "v1.2.0")
            (root / "_vendor").mkdir()
            with patch.object(update_oink.subprocess, "check_output") as command:
                with self.assertRaisesRegex(ValueError, "_vendor"):
                    update_oink.verify_hugo_graph(root, "v1.2.0")
                with self.assertRaisesRegex(ValueError, "_vendor"):
                    update_oink.preflight(root, "v1.2.0", False)
                command.assert_not_called()

    def test_hugo_graph_accepts_published_theme_with_outgoing_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            graph = (f"{SITE_MODULE} {MODULE}@v1.2.0\n{MODULE}@v1.2.0 dependency@v1.0.0\n"
                     "dependency@v1.0.0 transitive@v2.0.0\n")
            with patch.object(update_oink.subprocess, "check_output", return_value=graph):
                self.assertEqual(update_oink.verify_hugo_graph(Path(directory), "v1.2.0"), graph)

    @unittest.skipUnless(shutil.which(os.environ.get("HUGO_BIN", "hugo")), "Hugo executable is required")
    def test_real_hugo_rejects_unpublished_local_theme_capability(self):
        """A valid Go lock does not exclude additional Hugo root theme imports."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("go.mod", "go.sum"):
                (root / name).write_bytes((update_oink.ROOT / name).read_bytes())
            config = ("baseURL: https://example.test/\n"
                      "disableKinds: [taxonomy, term, RSS, sitemap]\n"
                      "module:\n  imports:\n    - path: " + MODULE + "\n")
            (root / "hugo.yaml").write_text(config)
            (root / "layouts").mkdir()
            (root / "layouts/index.html").write_text("{{ .Content }}")
            (root / "content").mkdir()
            page = root / "content/_index.md"
            page.write_text('---\ntitle: Fixture\n---\n{{< unpublished >}}\n')
            preview = root / "preview"
            shortcodes = preview / "layouts/shortcodes"
            shortcodes.mkdir(parents=True)
            (shortcodes / "unpublished.html").write_text("unpublished fixture capability")
            env = update_oink.release_environment()
            env["HUGO_THEME"] = str(preview)
            hugo = env.get("HUGO_BIN", "hugo")
            argv = [hugo, "--environment", "production", "--panicOnWarning"]
            with patch.dict(os.environ, env, clear=True):
                version = update_oink.download_locked(root)["Version"]
                graph = subprocess.check_output([hugo, "mod", "graph"], cwd=root, env=env, text=True)
                self.assertIn(f"{SITE_MODULE} {MODULE}@{version}", graph)
                self.assertIn(f"{SITE_MODULE} {preview}", graph)
                # Reproduce the former false pass with real Hugo and Go commands.
                contaminated = subprocess.run(argv, cwd=root, env=env, text=True, capture_output=True)
                self.assertEqual(contaminated.returncode, 0, contaminated.stdout + contaminated.stderr)
                self.assertIn("unpublished fixture capability", (root / "public/index.html").read_text())
                with update_oink.isolated_release():
                    self.assertNotIn("HUGO_THEME", os.environ)
                    isolated_graph = update_oink.verify_hugo_graph(root, version)
                    self.assertNotIn(str(preview), isolated_graph)
                    isolated = subprocess.run(argv, cwd=root, text=True, capture_output=True)
                    self.assertNotEqual(isolated.returncode, 0)
                    self.assertIn('template for shortcode "unpublished" not found', isolated.stdout + isolated.stderr)
                self.assertEqual(os.environ["HUGO_THEME"], str(preview))
                # A local theme in checked-in configuration must also fail the
                # graph gate, even after environment isolation removes HUGO_THEME.
                (root / "hugo.yaml").write_text(config + f"    - path: {preview}\n")
                with self.assertRaisesRegex(ValueError, "expected Hugo root"):
                    update_oink.verify_hugo_graph(root, version)
                (root / "hugo.yaml").write_text(config)
                page.write_text('---\ntitle: Fixture\n---\nPublished theme only.\n')
                with update_oink.isolated_release():
                    published = subprocess.run(argv, cwd=root, text=True, capture_output=True)
                    self.assertEqual(published.returncode, 0, published.stdout + published.stderr)

    @unittest.skipUnless(shutil.which(os.environ.get("HUGO_BIN", "hugo")), "Hugo executable is required")
    def test_readonly_baseline_rejection_preserves_locks_with_real_hugo_proxy(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            proxy = base / "proxy/example.com/extra/@v"
            proxy.mkdir(parents=True)
            (proxy / "list").write_text("v1.0.0\n")
            (proxy / "v1.0.0.info").write_text('{"Version":"v1.0.0","Time":"2026-01-01T00:00:00Z"}')
            module_text = "module example.com/extra\n\ngo 1.20\n"
            (proxy / "v1.0.0.mod").write_text(module_text)
            with zipfile.ZipFile(proxy / "v1.0.0.zip", "w") as archive:
                archive.writestr("example.com/extra@v1.0.0/go.mod", module_text)
                archive.writestr("example.com/extra@v1.0.0/README.md", "Local regression fixture.\n")
            root = base / "site"
            root.mkdir()
            for name in ("go.mod", "go.sum"):
                (root / name).write_bytes((update_oink.ROOT / name).read_bytes())
            (root / "hugo.yaml").write_text("module:\n  imports:\n    - path: " + MODULE +
                                            "\n    - path: example.com/extra\n")
            before = {name: (root / name).read_bytes() for name in ("go.mod", "go.sum")}
            env = update_oink.release_environment()
            env.update(GOPROXY=(base / "proxy").as_uri(), HUGO_MODULE_PROXY=(base / "proxy").as_uri(), GOSUMDB="off")
            hugo = env.get("HUGO_BIN", "hugo")
            # Prove this proxy causes real Hugo to mutate locks when run directly.
            contaminated = base / "contaminated"
            shutil.copytree(root, contaminated)
            direct = subprocess.run([hugo, "mod", "graph"], cwd=contaminated, env=env, text=True, capture_output=True)
            self.assertEqual(direct.returncode, 0, direct.stdout + direct.stderr)
            self.assertIn("example.com/extra@v1.0.0", direct.stdout)
            for name, contents in before.items():
                self.assertNotEqual((contaminated / name).read_bytes(), contents)
            scripts = root / "scripts"
            scripts.mkdir()
            for name in ("update_oink.py", "oink_module.py", "oink-overrides.json"):
                shutil.copy2(update_oink.ROOT / "scripts" / name, scripts / name)
            failed = subprocess.run([sys.executable, scripts / "update_oink.py", "--check-baseline"],
                                    cwd=root, env=env, text=True, capture_output=True)
            self.assertEqual(failed.returncode, 1, failed.stdout + failed.stderr)
            self.assertIn("expected Hugo root", failed.stderr)
            self.assertIn("example.com/extra@v1.0.0", failed.stderr)
            for name, contents in before.items():
                self.assertEqual((root / name).read_bytes(), contents)
            # Parent-relative local themes must still resolve in the workspace.
            preview = base / "relative-preview"
            (preview / "layouts/shortcodes").mkdir(parents=True)
            (preview / "layouts/shortcodes/unpublished.html").write_text("unpublished")
            (root / "hugo.yaml").write_text("themesDir: ..\ntheme: relative-preview\n"
                                            "module:\n  imports:\n    - path: " + MODULE + "\n")
            relative = subprocess.run([sys.executable, scripts / "update_oink.py", "--check-baseline"],
                                      cwd=root, env=env, text=True, capture_output=True)
            self.assertEqual(relative.returncode, 1, relative.stdout + relative.stderr)
            self.assertIn("expected Hugo root", relative.stderr)
            self.assertIn(f"{SITE_MODULE} relative-preview", relative.stderr)
            (root / "layouts").mkdir()
            (root / "layouts/index.html").write_text("{{ .Content }}")
            (root / "content").mkdir()
            (root / "content/_index.md").write_text('---\ntitle: Relative fixture\n---\n{{< unpublished >}}\n')
            with update_oink.graph_workspace(root) as workspace:
                rendered = subprocess.run([hugo, "--environment", "production", "--panicOnWarning"],
                                          cwd=workspace, env=env, text=True, capture_output=True)
                self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
                self.assertIn("unpublished", (workspace / "public/index.html").read_text())
            for name, contents in before.items():
                self.assertEqual((root / name).read_bytes(), contents)

    @unittest.skipUnless(shutil.which(os.environ.get("HUGO_BIN", "hugo")), "Hugo executable is required")
    def test_real_hugo_graph_uses_production_in_both_environment_directions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "site"
            root.mkdir()
            for name in ("go.mod", "go.sum"):
                (root / name).write_bytes((update_oink.ROOT / name).read_bytes())
            base_config = ("baseURL: https://example.test/\n"
                           "disableKinds: [taxonomy, term, RSS, sitemap]\n"
                           "module:\n  imports:\n    - path: " + MODULE + "\n")
            development = root / "config/development"
            development.mkdir(parents=True)
            preview = root.parent / "preview"
            (preview / "layouts/shortcodes").mkdir(parents=True)
            (preview / "layouts/shortcodes/unpublished.html").write_text("unpublished development capability")
            (root / "layouts").mkdir()
            (root / "layouts/index.html").write_text("{{ .Content }}")
            (root / "content").mkdir()
            page = root / "content/_index.md"
            page.write_text('---\ntitle: Environment fixture\n---\nPublished content.\n')
            env = update_oink.release_environment()
            env["HUGO_ENVIRONMENT"] = "development"
            hugo = env.get("HUGO_BIN", "hugo")
            before = {name: (root / name).read_bytes() for name in ("go.mod", "go.sum")}
            with patch.dict(os.environ, env, clear=True):
                version = update_oink.download_locked(root)["Version"]
                (root / "hugo.yaml").write_text(base_config)
                (development / "hugo.yaml").write_text(f"theme: [{preview}]\n")
                inherited = subprocess.check_output([hugo, "mod", "graph", "--config", "hugo.yaml"],
                                                    cwd=root, env=env, text=True)
                self.assertIn(str(preview), inherited)
                # A development-only import must not reject the production site.
                accepted = update_oink.verify_hugo_graph(root, version)
                self.assertNotIn(str(preview), accepted)
                production = [hugo, "--config", "hugo.yaml", "--environment", "production", "--panicOnWarning"]
                built = subprocess.run(production, cwd=root, env=env, text=True, capture_output=True)
                self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
                # Conversely, development clearing a production theme must not
                # conceal its unpublished shortcode from the production gate.
                (root / "hugo.yaml").write_text(base_config + f"theme: [{preview}]\n")
                (development / "hugo.yaml").write_text("theme: []\n")
                page.write_text('---\ntitle: Environment fixture\n---\n{{< unpublished >}}\n')
                inherited = subprocess.check_output([hugo, "mod", "graph", "--config", "hugo.yaml"],
                                                    cwd=root, env=env, text=True)
                self.assertNotIn(str(preview), inherited)
                with self.assertRaisesRegex(ValueError, "expected Hugo root"):
                    update_oink.verify_hugo_graph(root, version)
                built = subprocess.run(production, cwd=root, env=env, text=True, capture_output=True)
                self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
                self.assertIn("unpublished development capability", (root / "public/index.html").read_text())
            for name, contents in before.items():
                self.assertEqual((root / name).read_bytes(), contents)

    def test_validation_subprocesses_inherit_isolation_and_absolute_hugo_path(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / "toolchain.json").write_text(json.dumps(dict(hugo="hugo 0.168.0", sass="1.105.2", go="go1.27.0", webp="1.6.0")))
            (work / "resolved.json").write_text(json.dumps({"versions": [{"id": "latest", "sha": "example"}]}))
            observations = []

            def run(argv, **kwargs):
                env = kwargs.get("env") or os.environ
                observations.append(list(argv))
                self.assertNotIn("HUGO_MODULE_REPLACEMENTS", env)
                self.assertNotIn("HUGO_THEME", env)
                self.assertEqual(env["GOWORK"], "off")
                self.assertEqual(env["HUGO_MODULE_WORKSPACE"], "off")
                self.assertEqual(env["HUGO_BIN"], "/resolved/hugo")

            with patch.dict(os.environ, {"HUGO_BIN": "./relative-hugo", "HUGO_MODULE_REPLACEMENTS": "preview"}), \
                 patch.object(update_oink.shutil, "which", return_value="/resolved/hugo"), \
                 patch.object(update_oink, "validation_snapshot", return_value="local-snapshot"), \
                 patch.object(update_oink, "run", side_effect=run):
                update_oink.validate(work)
            self.assertTrue(any("scripts/build_versions.py" in argv and "--force-rebuild" in argv for argv in observations))
            self.assertTrue(any(argv[0] == "/resolved/hugo" for argv in observations))
            self.assertTrue(any("discover" in argv for argv in observations))
            prepare = next(argv for argv in observations if "prepare" in argv)
            self.assertEqual(prepare[prepare.index("--latest-sha") + 1], "local-snapshot")

    def test_null_inventory_hashes_classify_added_and_removed_upstream_files(self):
        self.assertEqual(describe_changes({"new": None, "gone": "old"}, {"new": "hash", "gone": None}),
                         ["removed: gone", "added: new"])

    def test_validation_builds_both_ai_modes_before_browser_tests(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / "toolchain.json").write_text(json.dumps(dict(hugo="hugo 0.168.0", sass="1.105.2", go="go1.27.0", webp="1.6.0")))
            (work / "resolved.json").write_text(json.dumps({"versions": []}))
            with patch.object(update_oink, "validation_snapshot", return_value="local-snapshot"), \
                 patch.object(update_oink, "run") as run:
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
            plan = next(call.args[0] for call in calls if "scripts/version_cache.py" in call.args[0])
            self.assertEqual(plan[plan.index("--sass-version") + 1], "1.105.2")
            versions = next(call for call in calls if "scripts/build_versions.py" in call.args[0])
            self.assertIn("--force-rebuild", versions.args[0])
            self.assertEqual(versions.args[0][versions.args[0].index("--workers") + 1], "2")
            self.assertEqual(versions.kwargs["env"]["HUGO_CACHEDIR"], str(work / "hugo-cache"))
            visual = next(call for call in calls if call.args[0] == ["npm", "run", "test:visual"])
            self.assertEqual(visual.kwargs["env"]["VISUAL_RESULTS_DIR"], str(work / "after"))

    def test_validation_snapshot_captures_worktree_sources_without_mutating_git_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            work = Path(directory) / "report"
            work.mkdir()

            def git(*args):
                return subprocess.check_output(["git", "-c", "user.name=Test", "-c", "user.email=test@localhost", *args],
                                               cwd=root, text=True).strip()

            def write(name, text):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)

            git("init", "-q")
            names = ["content/staged.md", "content/unstaged.md", "static/staged.txt",
                     "content/deleted.md", "static/deleted.txt", "content/ignored/tracked.md", "unrelated.txt"]
            for name in names:
                write(name, "head")
            # Track one ignored-directory file before introducing ignore rules.
            git("add", ".")
            write(".gitignore", "content/ignored/\nstatic/ignored/\n")
            git("add", ".gitignore")
            git("commit", "-qm", "initial")
            head = git("rev-parse", "HEAD")
            write("content/staged.md", "staged")
            write("static/staged.txt", "staged")
            write("unrelated.txt", "staged unrelated")
            (root / "static/deleted.txt").unlink()
            git("add", "-A")
            write("content/staged.md", "working tree wins")
            write("content/unstaged.md", "unstaged")
            write("content/ignored/tracked.md", "tracked ignored update")
            (root / "content/deleted.md").unlink()
            write("content/new.md", "new content")
            write("static/new.txt", "new asset")
            write("content/ignored/new.md", "ignored content")
            write("static/ignored/new.txt", "ignored asset")
            write("unrelated-new.txt", "exclude untracked")
            index = (root / ".git/index").read_bytes()
            status = git("status", "--porcelain")
            refs = git("show-ref")
            config = git("config", "--local", "--list")
            latest = update_oink.validation_snapshot(root, work)
            self.assertNotEqual(latest, head)
            for name, value in {"content/staged.md": "working tree wins", "content/unstaged.md": "unstaged",
                                "static/staged.txt": "staged", "content/new.md": "new content", "static/new.txt": "new asset",
                                "content/ignored/tracked.md": "tracked ignored update", "unrelated.txt": "head"}.items():
                self.assertEqual(git("show", f"{latest}:{name}"), value)
            paths = git("ls-tree", "-r", "--name-only", latest).splitlines()
            for name in ["content/deleted.md", "static/deleted.txt", "content/ignored/new.md",
                         "static/ignored/new.txt", "unrelated-new.txt"]:
                self.assertNotIn(name, paths)
            self.assertEqual(git("rev-parse", "HEAD"), head)
            self.assertEqual((root / ".git/index").read_bytes(), index)
            self.assertEqual(git("status", "--porcelain"), status)
            self.assertEqual(git("show-ref"), refs)
            self.assertEqual(git("config", "--local", "--list"), config)
            report = json.loads((work / "validation-snapshot.json").read_text())
            self.assertEqual(report["latestSha"], latest)
            self.assertEqual(report["scope"], ["content", "static"])
            self.assertEqual(git("show", "-s", "--format=%an <%ae>", latest), "OINK validation <validation@localhost>")
            git("reset", "--hard", "-q", head)
            git("clean", "-fdq")
            def commits():
                return {line for line in git("cat-file", "--batch-all-objects", "--batch-check=%(objectname) %(objecttype)").splitlines()
                        if line.endswith(" commit")}
            before_commits = commits()
            # Ignored untracked assets remain and must still not produce a snapshot.
            self.assertEqual(update_oink.validation_snapshot(root, work), head)
            self.assertEqual(commits(), before_commits)

    def test_resume_cleans_interrupted_upgrade_before_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            root.mkdir()
            (root / "go.mod").write_text("module fixture")
            target = f"{MODULE} v1.1.0 h1:new\n{MODULE} v1.1.0/go.mod h1:newmod\n"
            (root / "go.sum").write_text(f"{MODULE} v1.0.0 h1:old\n" + target)
            baseline = root / "baseline.json"
            baseline.write_text(json.dumps({"version": "v1.1.0", "files": {}}))

            def download(path):
                self.assertEqual((path / "go.sum").read_text(), target)
                return {"Dir": str(root)}

            with patch.object(update_oink, "ROOT", root), patch.object(update_oink, "check_toolchain", return_value={}), patch.object(update_oink, "BASELINE", baseline), \
                 patch.object(update_oink, "locked_version", return_value="v1.1.0"), \
                 patch.object(update_oink, "download_locked", side_effect=download), \
                 patch.object(update_oink, "verify_hugo_graph", return_value="verified"), \
                 patch.object(update_oink, "snapshot", return_value={}), \
                 patch.object(update_oink, "validate") as validate, \
                 patch.object(update_oink, "command") as command, \
                 patch.object(update_oink.tempfile, "mkdtemp", return_value=str(root.parent / "artifacts")), \
                 patch("sys.argv", ["update", "v1.1.0", "--resume"]):
                update_oink.main()
                with patch("sys.argv", ["update", "v1.1.0", "--resume", "--work-dir", str(root.parent / "artifacts")]):
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
