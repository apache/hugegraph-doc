import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("community_roster", ROOT / "scripts" / "community_roster.py")
roster = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(roster)


class CommunityRosterTests(unittest.TestCase):
    def fixture(self):
        return (
            {"committees": {"hugegraph": {"chair": {"chair": {"name": "Chair Person"}}, "roster": {"chair": {}, "zeta": {}}}}},
            {"projects": {"hugegraph": {"owners": ["zeta", "chair"], "members": ["other", "zeta", "chair"]}}},
            {"people": {"chair": {"name": "Chair Person"}, "zeta": {"name": "Alpha Owner"}, "other": {"name": "Beta Committer"}}},
            {"schema_version": 1, "mappings": {}},
        )

    def test_build_roster_derives_roles_and_order(self):
        candidate = roster.build_roster(*self.fixture())
        self.assertEqual(["chair", "zeta"], [p["asf_id"] for p in candidate["roles"]["pmc"]])
        self.assertEqual(["other"], [p["asf_id"] for p in candidate["roles"]["committers"]])
        self.assertTrue(candidate["roles"]["pmc"][0]["chair"])

    def test_same_names_use_asf_id_tiebreaker_across_hash_seeds(self):
        program = f"""
import importlib.util, json
spec = importlib.util.spec_from_file_location("community_roster", {str(ROOT / "scripts/community_roster.py")!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
committee = {{"committees": {{"hugegraph": {{"chair": {{"chair": {{}}}}, "roster": {{"chair": {{}}, "zeta": {{}}, "alpha": {{}}}}}}}}}}
projects = {{"projects": {{"hugegraph": {{"owners": ["zeta", "chair", "alpha"], "members": ["zeta", "chair", "alpha"]}}}}}}
people = {{"people": {{"chair": {{"name": "Chair"}}, "zeta": {{"name": "Same Name"}}, "alpha": {{"name": "Same Name"}}}}}}
result = module.build_roster(committee, projects, people, {{"schema_version": 1, "mappings": {{}}}})
print(json.dumps([person["asf_id"] for person in result["roles"]["pmc"]]))
"""
        outputs = []
        for seed in ("1", "777"):
            environment = {**os.environ, "PYTHONHASHSEED": seed}
            outputs.append(subprocess.check_output([sys.executable, "-c", program], env=environment, text=True))
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(["chair", "alpha", "zeta"], json.loads(outputs[0]))

    def test_build_roster_rejects_committee_ldap_drift(self):
        committee, projects, people, mapping = self.fixture()
        committee["committees"]["hugegraph"]["roster"].pop("zeta")
        with self.assertRaisesRegex(roster.RosterError, "disagree"):
            roster.build_roster(committee, projects, people, mapping)

    def test_mapping_requires_unique_numeric_ids(self):
        mapping = {"schema_version": 1, "mappings": {"one": {"login": "same", "user_id": 1}, "two": {"login": "other", "user_id": 1}}}
        with self.assertRaisesRegex(roster.RosterError, "duplicate GitHub user_id"):
            roster._validate_mapping(mapping, {"one", "two"})

    def test_avatar_metadata_is_stripped(self):
        vp8x = b"VP8X" + (10).to_bytes(4, "little") + bytes([0x2C]) + b"\0" * 9
        exif = b"EXIF" + (4).to_bytes(4, "little") + b"meta"
        payload = b"WEBP" + vp8x + exif
        raw = b"RIFF" + len(payload).to_bytes(4, "little") + payload
        stripped = roster._strip_webp_metadata(raw)
        self.assertNotIn(b"EXIF", stripped)
        self.assertEqual(0, stripped[20] & 0x2C)

    def test_checked_in_bundle_validates(self):
        self.assertEqual([], roster.validate_bundle(90))

    def test_unmapped_profile_must_be_exact_phonebook_url(self):
        with tempfile.TemporaryDirectory(prefix="community-profile-test-") as directory:
            root = pathlib.Path(directory)
            candidate = json.loads(roster.ROSTER_PATH.read_text())
            candidate["roles"]["committers"][0]["profile_url"] = "https://example.invalid/profile"
            roster_path, map_path = root / "roster.json", root / "github-map.json"
            roster_path.write_text(json.dumps(candidate))
            map_path.write_text(roster.MAP_PATH.read_text())
            with mock.patch.object(roster, "ROSTER_PATH", roster_path), \
                 mock.patch.object(roster, "MAP_PATH", map_path), \
                 mock.patch.object(roster, "AVATAR_DIR", root / "avatars"):
                with self.assertRaisesRegex(roster.RosterError, "unmapped profile URL mismatch"):
                    roster.validate_bundle(90)

    def test_validator_rejects_same_name_out_of_asf_id_order(self):
        committee, projects, people, mapping = self.fixture()
        committee["committees"]["hugegraph"]["roster"]["alpha"] = {}
        projects["projects"]["hugegraph"]["owners"].append("alpha")
        projects["projects"]["hugegraph"]["members"].append("alpha")
        people["people"]["zeta"]["name"] = "Same Name"
        people["people"]["alpha"] = {"name": "Same Name"}
        candidate = roster.build_roster(committee, projects, people, mapping)
        candidate["roles"]["pmc"][1:] = reversed(candidate["roles"]["pmc"][1:])
        with tempfile.TemporaryDirectory(prefix="community-order-test-") as directory:
            root = pathlib.Path(directory)
            roster_path, map_path = root / "roster.json", root / "github-map.json"
            roster_path.write_text(json.dumps(candidate))
            map_path.write_text(json.dumps(mapping))
            with mock.patch.object(roster, "ROSTER_PATH", roster_path), \
                 mock.patch.object(roster, "MAP_PATH", map_path), \
                 mock.patch.object(roster, "AVATAR_DIR", root / "avatars"):
                with self.assertRaisesRegex(roster.RosterError, "sorted by public name"):
                    roster.validate_bundle(90)

    def test_fetch_failure_preserves_last_good(self):
        original, old_fetch = roster.ROSTER_PATH.read_bytes(), roster._fetch_json
        try:
            roster._fetch_json = lambda _url: (_ for _ in ()).throw(OSError("network down"))
            with self.assertRaises(OSError):
                roster.refresh()
        finally:
            roster._fetch_json = old_fetch
        self.assertEqual(original, roster.ROSTER_PATH.read_bytes())

    def test_copy_failure_preserves_last_good_bundle(self):
        with tempfile.TemporaryDirectory(prefix="community-copy-test-") as directory:
            root = pathlib.Path(directory)
            roster_path, avatar_dir = root / "roster.json", root / "avatars"
            avatar_dir.mkdir()
            roster_path.write_bytes(b"last-good\n")
            (avatar_dir / "old.webp").write_bytes(b"old")
            candidate = {"roles": {"pmc": [{"avatar": "/img/community/avatars/new.webp"}], "committers": []}}
            with mock.patch.object(roster, "ROSTER_PATH", roster_path), \
                 mock.patch.object(roster, "AVATAR_DIR", avatar_dir), \
                 mock.patch.object(roster, "_copy_candidate", side_effect=OSError("copy failed")):
                with self.assertRaisesRegex(OSError, "copy failed"):
                    roster._commit_bundle(candidate, {"new.webp": b"new"})
            self.assertEqual(b"last-good\n", roster_path.read_bytes())
            self.assertEqual(b"old", (avatar_dir / "old.webp").read_bytes())

    def test_candidate_cleanup_failure_does_not_publish_roster(self):
        with tempfile.TemporaryDirectory(prefix="community-cleanup-test-") as directory:
            root = pathlib.Path(directory)
            roster_path, map_path = root / "roster.json", root / "github-map.json"
            roster_path.write_bytes(b"last-good\n")
            map_path.write_text('{"schema_version": 1, "mappings": {}}')
            candidate = {"roles": {"pmc": [], "committers": []}}
            with mock.patch.object(roster, "DATA_DIR", root), \
                 mock.patch.object(roster, "ROSTER_PATH", roster_path), \
                 mock.patch.object(roster, "MAP_PATH", map_path), \
                 mock.patch.object(roster, "_fetch_json", return_value={}), \
                 mock.patch.object(roster, "build_roster", return_value=candidate), \
                 mock.patch.object(roster, "_install_avatars"), \
                 mock.patch.object(roster.shutil, "rmtree", side_effect=OSError("cleanup failed")):
                with self.assertRaisesRegex(OSError, "cleanup failed"):
                    roster.refresh()
            self.assertEqual(b"last-good\n", roster_path.read_bytes())

    def test_unlink_failure_rolls_back_roster_and_avatars(self):
        with tempfile.TemporaryDirectory(prefix="community-unlink-test-") as directory:
            root = pathlib.Path(directory)
            roster_path, avatar_dir = root / "roster.json", root / "avatars"
            avatar_dir.mkdir()
            roster_path.write_bytes(b"last-good\n")
            (avatar_dir / "old.webp").write_bytes(b"old")
            candidate = {"roles": {"pmc": [{"avatar": "/img/community/avatars/new.webp"}], "committers": []}}
            real_unlink, failed = roster._unlink, False

            def fail_once(path):
                nonlocal failed
                if path.name == "old.webp" and not failed:
                    failed = True
                    raise OSError("unlink failed")
                real_unlink(path)

            with mock.patch.object(roster, "ROSTER_PATH", roster_path), \
                 mock.patch.object(roster, "AVATAR_DIR", avatar_dir), \
                 mock.patch.object(roster, "_unlink", side_effect=fail_once):
                with self.assertRaisesRegex(OSError, "unlink failed"):
                    roster._commit_bundle(candidate, {"new.webp": b"new"})
            self.assertEqual(b"last-good\n", roster_path.read_bytes())
            self.assertEqual(b"old", (avatar_dir / "old.webp").read_bytes())
            self.assertFalse((avatar_dir / "new.webp").exists())


class CommunityContentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._site = tempfile.TemporaryDirectory(prefix="community-content-site-")
        environment = {**os.environ, "GOPROXY": "off"}
        subprocess.run(
            ["hugo", "--quiet", "--destination", cls._site.name],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=True,
        )
        cls.site = pathlib.Path(cls._site.name)

    @classmethod
    def tearDownClass(cls):
        cls._site.cleanup()

    def test_search_metadata_covers_fixed_bilingual_entries(self):
        entries = [
            "docs/introduction/_index.md",
            "docs/quickstart/hugegraph/hugegraph-server.md",
            "docs/quickstart/hugegraph/hugegraph-hstore.md",
            "docs/quickstart/hugegraph/hugegraph-pd.md",
            "docs/quickstart/computing/hugegraph-computer.md",
            "docs/quickstart/toolchain/hugegraph-loader.md",
            "docs/quickstart/toolchain/hugegraph-hubble.md",
            "docs/clients/_index.md",
            "docs/clients/restful-api/_index.md",
            "docs/config/config-guide.md",
            "docs/config/config-authentication.md",
            "docs/download/download.md",
        ]
        for language in ("en", "cn"):
            for relative in entries:
                text = (ROOT / "content" / language / relative).read_text(encoding="utf-8")
                self.assertIn("search_keywords:", text, f"{language}/{relative}")
                self.assertIn("search_boost:", text, f"{language}/{relative}")

    def test_docs_roots_leave_llmsfull_to_core_platform_lane(self):
        for language in ("en", "cn"):
            text = (ROOT / "content" / language / "docs/_index.md").read_text(encoding="utf-8")
            self.assertNotIn("LLMSFULL", text.split("---", 2)[1])

    def test_component_pilots_are_bilingual_and_scoped(self):
        for language in ("en", "cn"):
            server = (ROOT / "content" / language / "docs/quickstart/hugegraph/hugegraph-server.md").read_text()
            config = (ROOT / "content" / language / "docs/config/config-guide.md").read_text()
            vertex = (ROOT / "content" / language / "docs/clients/restful-api/vertex.md").read_text()
            self.assertIn("{.steps}", server)
            self.assertIn('filename="conf/gremlin-server.yaml"', config)
            self.assertIn(".full-width", vertex)
            self.assertIn("{#vertex-id-strategy", vertex)

    def test_component_pilots_render_in_html_print_and_markdown(self):
        for prefix in ("", "cn/"):
            outputs = {
                "server_html": self.site / prefix / "docs/quickstart/hugegraph/hugegraph-server/index.html",
                "server_print": self.site / prefix / "_print/docs/quickstart/hugegraph/index.html",
                "server_md": self.site / prefix / "docs/quickstart/hugegraph/hugegraph-server/index.md",
                "config_html": self.site / prefix / "docs/config/config-guide/index.html",
                "config_print": self.site / prefix / "_print/docs/config/index.html",
                "config_md": self.site / prefix / "docs/config/config-guide/index.md",
                "vertex_html": self.site / prefix / "docs/clients/restful-api/vertex/index.html",
                "vertex_print": self.site / prefix / "_print/docs/clients/restful-api/index.html",
                "vertex_md": self.site / prefix / "docs/clients/restful-api/vertex/index.md",
            }
            rendered = {key: path.read_text(encoding="utf-8") for key, path in outputs.items()}
            self.assertIn('class="steps"', rendered["server_html"])
            self.assertIn('class="steps"', rendered["server_print"])
            self.assertIn("{.steps}", rendered["server_md"])
            for key in ("config_html", "config_print", "config_md"):
                self.assertIn("conf/gremlin-server.yaml", rendered[key])
            self.assertIn('id="vertex-id-strategy"', rendered["vertex_html"])
            self.assertIn('id="vertex-id-strategy"', rendered["vertex_print"])
            self.assertIn("{#vertex-id-strategy .full-width", rendered["vertex_md"])

    def test_community_markdown_follows_section_order_and_about_is_unchanged(self):
        expected = {
            "community/index.md": (
                "## Join the Apache HugeGraph community",
                "## Get involved",
                "## Project members",
                "## Learn how the project works",
            ),
            "cn/community/index.md": (
                "## 加入 Apache HugeGraph 社区",
                "## 参与社区",
                "## 项目成员",
                "## 了解项目运作方式",
            ),
        }
        for relative, markers in expected.items():
            rendered = (self.site / relative).read_text(encoding="utf-8")
            positions = [rendered.index(marker) for marker in markers]
            self.assertEqual(positions, sorted(positions))
        about = {
            "about/index.md": (
                "## One ecosystem for graph data and graph intelligence",
                "HugeGraph is an Apache top-level project",
            ),
            "cn/about/index.md": (
                "## 连接图数据与图智能的一体化生态",
                "HugeGraph 是 Apache 顶级项目",
            ),
        }
        for relative, markers in about.items():
            rendered = (self.site / relative).read_text(encoding="utf-8")
            self.assertNotIn("Project members", rendered)
            for marker in markers:
                self.assertIn(marker, rendered)

    def test_fixed_metadata_is_present_in_actual_offline_indexes(self):
        relative_refs = [
            "docs/introduction/",
            "docs/quickstart/hugegraph/hugegraph-server/",
            "docs/quickstart/hugegraph/hugegraph-hstore/",
            "docs/quickstart/hugegraph/hugegraph-pd/",
            "docs/quickstart/computing/hugegraph-computer/",
            "docs/quickstart/toolchain/hugegraph-loader/",
            "docs/quickstart/toolchain/hugegraph-hubble/",
            "docs/clients/",
            "docs/clients/restful-api/",
            "docs/config/config-guide/",
            "docs/config/config-authentication/",
            "docs/download/download/",
        ]
        for language, prefix in (("en", "/"), ("cn", "/cn/")):
            indexes = list(self.site.glob(f"offline-search-index.{language}.*.json"))
            self.assertEqual(1, len(indexes))
            records = {record["ref"]: record for record in json.loads(indexes[0].read_text())}
            for relative in relative_refs:
                ref = prefix + relative
                self.assertIn(ref, records)
                self.assertTrue(records[ref]["keywords"], ref)
                self.assertGreater(records[ref]["boost"], 1, ref)


if __name__ == "__main__":
    unittest.main()
