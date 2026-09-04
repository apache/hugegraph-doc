import importlib.util
import pathlib
import unittest

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

    def test_build_roster_rejects_committee_ldap_drift(self):
        committee, projects, people, mapping = self.fixture()
        committee["committees"]["hugegraph"]["roster"].pop("zeta")
        with self.assertRaisesRegex(roster.RosterError, "disagree"):
            roster.build_roster(committee, projects, people, mapping)

    def test_mapping_requires_unique_numeric_ids(self):
        mapping = {"schema_version": 1, "mappings": {"one": {"login": "same", "user_id": 1}, "two": {"login": "other", "user_id": 1}}}
        with self.assertRaisesRegex(roster.RosterError, "duplicate GitHub user_id"):
            roster._validate_mapping(mapping, {"one", "two"})

    def test_checked_in_bundle_validates(self):
        self.assertEqual([], roster.validate_bundle(90))

    def test_fetch_failure_preserves_last_good(self):
        original, old_fetch = roster.ROSTER_PATH.read_bytes(), roster._fetch_json
        try:
            roster._fetch_json = lambda _url: (_ for _ in ()).throw(OSError("network down"))
            with self.assertRaises(OSError):
                roster.refresh()
        finally:
            roster._fetch_json = old_fetch
        self.assertEqual(original, roster.ROSTER_PATH.read_bytes())


class CommunityContentContractTests(unittest.TestCase):
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

    def test_docs_roots_enable_llmsfull_only_in_front_matter(self):
        for language in ("en", "cn"):
            text = (ROOT / "content" / language / "docs/_index.md").read_text(encoding="utf-8")
            self.assertIn("LLMSFULL", text.split("---", 2)[1])


if __name__ == "__main__":
    unittest.main()
