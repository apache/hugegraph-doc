import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
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


class FakeResponse:
    def __init__(self, raw, *, url, content_type, status=200):
        self.raw = raw
        self.url = url
        self.headers = {"Content-Type": content_type}
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def geturl(self):
        return self.url

    def read(self, limit=-1):
        return self.raw if limit < 0 else self.raw[:limit]


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

    def test_mapping_rejects_invalid_identity_characters(self):
        with self.assertRaisesRegex(roster.RosterError, "invalid ASF ID"):
            roster._validate_mapping(
                {"schema_version": 1, "mappings": {"Bad ID": {"login": "valid", "user_id": 1}}},
                {"Bad ID"},
            )
        with self.assertRaisesRegex(roster.RosterError, "invalid GitHub login"):
            roster._validate_mapping(
                {"schema_version": 1, "mappings": {"valid": {"login": "bad/login", "user_id": 1}}},
                {"valid"},
            )

    def test_avatar_metadata_is_stripped(self):
        vp8x = b"VP8X" + (10).to_bytes(4, "little") + bytes([0x2D]) + b"\0" * 9
        exif = b"EXIF" + (4).to_bytes(4, "little") + b"meta"
        iccp = b"ICCP" + (4).to_bytes(4, "little") + b"icc!"
        payload = b"WEBP" + vp8x + exif + iccp
        raw = b"RIFF" + len(payload).to_bytes(4, "little") + payload
        stripped = roster._strip_webp_metadata(raw)
        self.assertNotIn(b"EXIF", stripped)
        self.assertNotIn(b"ICCP", stripped)
        self.assertEqual(0, stripped[20] & 0x2D)

    def test_truncated_vp8x_without_image_bitstream_is_rejected(self):
        vp8x = b"VP8X" + (10).to_bytes(4, "little") + b"\0" * 10
        payload = b"WEBP" + vp8x
        raw = b"RIFF" + len(payload).to_bytes(4, "little") + payload
        with self.assertRaisesRegex(roster.RosterError, "no decodable"):
            roster._validate_webp(raw)

    def test_network_response_contracts_are_bounded_and_allowlisted(self):
        with self.assertRaisesRegex(roster.RosterError, "not allowlisted"):
            roster._read_bounded_response(
                FakeResponse(b"{}", url="https://evil.example/data", content_type="application/json"),
                expected_hosts={"whimsy.apache.org"},
                content_types={"application/json"},
                limit=10,
                kind="JSON source",
            )
        with self.assertRaisesRegex(roster.RosterError, "Content-Type"):
            roster._read_bounded_response(
                FakeResponse(b"{}", url="https://whimsy.apache.org/data", content_type="text/html"),
                expected_hosts={"whimsy.apache.org"},
                content_types={"application/json"},
                limit=10,
                kind="JSON source",
            )
        with self.assertRaisesRegex(roster.RosterError, "exceeds"):
            roster._read_bounded_response(
                FakeResponse(b"x" * 11, url="https://whimsy.apache.org/data", content_type="application/json"),
                expected_hosts={"whimsy.apache.org"},
                content_types={"application/json"},
                limit=10,
                kind="JSON source",
            )

    def test_redirect_is_rejected_before_following_disallowed_host(self):
        handler = roster._AllowlistedRedirectHandler({"whimsy.apache.org"}, "JSON source")
        with self.assertRaisesRegex(roster.RosterError, "not allowlisted"):
            handler.redirect_request(
                mock.Mock(),
                None,
                302,
                "Found",
                {},
                "http://127.0.0.1/private",
            )

    def test_malformed_json_and_encoder_timeout_are_roster_errors(self):
        response = FakeResponse(
            b"{bad",
            url="https://whimsy.apache.org/public/committee-info.json",
            content_type="application/json",
        )
        with mock.patch.object(roster, "_open_allowlisted", return_value=response):
            with self.assertRaisesRegex(roster.RosterError, "malformed JSON"):
                roster._fetch_json(roster.SOURCES["committee"])
        avatar = FakeResponse(
            b"not-an-image",
            url="https://avatars.githubusercontent.com/u/1?s=128&v=4",
            content_type="image/png",
        )
        with mock.patch.object(roster, "_open_allowlisted", return_value=avatar), \
             mock.patch.object(roster.shutil, "which", return_value="/fake/cwebp"), \
             mock.patch.object(roster.subprocess, "run", side_effect=subprocess.TimeoutExpired("cwebp", 20)):
            with self.assertRaisesRegex(roster.RosterError, "cwebp failed"):
                roster._avatar_bytes(1)

    def test_nested_source_schema_errors_are_roster_errors(self):
        committee, projects, people, mapping = self.fixture()
        projects["projects"] = []
        with self.assertRaisesRegex(roster.RosterError, "projects and committees objects"):
            roster.build_roster(committee, projects, people, mapping)
        committee, projects, people, mapping = self.fixture()
        projects["projects"]["hugegraph"]["owners"] = [[]]
        with self.assertRaisesRegex(roster.RosterError, "invalid ASF ID"):
            roster.build_roster(committee, projects, people, mapping)
        with tempfile.TemporaryDirectory(prefix="community-json-root-") as directory:
            path = pathlib.Path(directory) / "array.json"
            path.write_text("[]")
            with self.assertRaisesRegex(roster.RosterError, "JSON root must be an object"):
                roster._read_json(path)

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
                 mock.patch.object(roster, "ROOT", root), \
                 mock.patch.object(roster, "DATA_DIR", root), \
                 mock.patch.object(roster, "AVATAR_DIR", root / "avatars"):
                with self.assertRaisesRegex(roster.RosterError, "unmapped profile URL mismatch"):
                    roster.validate_bundle(90)

    def test_chair_values_must_be_strict_booleans(self):
        with tempfile.TemporaryDirectory(prefix="community-chair-test-") as directory:
            root = pathlib.Path(directory)
            candidate = json.loads(roster.ROSTER_PATH.read_text())
            candidate["roles"]["committers"][0]["chair"] = 0
            roster_path, map_path = root / "roster.json", root / "github-map.json"
            roster_path.write_text(json.dumps(candidate))
            map_path.write_text(roster.MAP_PATH.read_text())
            with mock.patch.object(roster, "ROSTER_PATH", roster_path), \
                 mock.patch.object(roster, "MAP_PATH", map_path), \
                 mock.patch.object(roster, "ROOT", root), \
                 mock.patch.object(roster, "DATA_DIR", root), \
                 mock.patch.object(roster, "AVATAR_DIR", root / "avatars"):
                with self.assertRaisesRegex(roster.RosterError, "chair must be boolean"):
                    roster.validate_bundle(90)

    def test_avatar_path_rejects_extra_segments_and_symlinks(self):
        base = json.loads(roster.ROSTER_PATH.read_text())
        asf_id = base["roles"]["committers"][0]["asf_id"]
        mapping = {"schema_version": 1, "mappings": {asf_id: {"login": "valid-user", "user_id": 1}}}
        for avatar in (
            "/img/community/avatars/extra/" + "a" * 64 + ".webp",
            "/img/community/avatars/../" + "a" * 64 + ".webp",
        ):
            with self.subTest(avatar=avatar), tempfile.TemporaryDirectory(prefix="community-avatar-path-") as directory:
                root = pathlib.Path(directory)
                candidate = json.loads(json.dumps(base))
                member = next(p for p in candidate["roles"]["committers"] if p["asf_id"] == asf_id)
                member.update(github=mapping["mappings"][asf_id], avatar=avatar, profile_url="https://github.com/valid-user")
                roster_path, map_path = root / "roster.json", root / "github-map.json"
                roster_path.write_text(json.dumps(candidate))
                map_path.write_text(json.dumps(mapping))
                with mock.patch.object(roster, "ROSTER_PATH", roster_path), \
                     mock.patch.object(roster, "MAP_PATH", map_path), \
                     mock.patch.object(roster, "ROOT", root), \
                     mock.patch.object(roster, "DATA_DIR", root), \
                     mock.patch.object(roster, "AVATAR_DIR", root / "avatars"):
                    with self.assertRaisesRegex(roster.RosterError, "needs a local avatar"):
                        roster.validate_bundle(90)
        with tempfile.TemporaryDirectory(prefix="community-avatar-link-") as directory:
            root = pathlib.Path(directory)
            avatar_dir = root / "avatars"
            avatar_dir.mkdir()
            raw = b"target"
            digest = hashlib.sha256(raw).hexdigest()
            target = root / "target.webp"
            target.write_bytes(raw)
            (avatar_dir / f"{digest}.webp").symlink_to(target)
            candidate = json.loads(json.dumps(base))
            member = next(p for p in candidate["roles"]["committers"] if p["asf_id"] == asf_id)
            member.update(
                github=mapping["mappings"][asf_id],
                avatar=f"/img/community/avatars/{digest}.webp",
                profile_url="https://github.com/valid-user",
            )
            roster_path, map_path = root / "roster.json", root / "github-map.json"
            roster_path.write_text(json.dumps(candidate))
            map_path.write_text(json.dumps(mapping))
            with mock.patch.object(roster, "ROSTER_PATH", roster_path), \
                 mock.patch.object(roster, "MAP_PATH", map_path), \
                 mock.patch.object(roster, "ROOT", root), \
                 mock.patch.object(roster, "DATA_DIR", root), \
                 mock.patch.object(roster, "AVATAR_DIR", avatar_dir):
                with self.assertRaisesRegex(roster.RosterError, "must not be a symlink"):
                    roster.validate_bundle(90)

    def test_avatar_directory_parent_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="community-avatar-parent-") as directory:
            root = pathlib.Path(directory)
            outside = root / "outside"
            outside.mkdir()
            avatar_link = root / "static" / "img" / "community" / "avatars"
            avatar_link.parent.mkdir(parents=True)
            avatar_link.symlink_to(outside, target_is_directory=True)
            with mock.patch.object(roster, "ROOT", root), \
                 mock.patch.object(roster, "DATA_DIR", root / "data" / "community"), \
                 mock.patch.object(roster, "ROSTER_PATH", root / "data" / "community" / "roster.json"), \
                 mock.patch.object(roster, "MAP_PATH", root / "data" / "community" / "github-map.json"), \
                 mock.patch.object(roster, "AVATAR_DIR", avatar_link):
                with self.assertRaisesRegex(roster.RosterError, "symlink path components"):
                    roster._validate_repo_paths()

    def test_member_name_and_initials_must_be_non_empty_and_derived(self):
        base = json.loads(roster.ROSTER_PATH.read_text())
        mapping = json.loads(roster.MAP_PATH.read_text())
        for field, value, message in (
            ("name", "", "name must be non-empty"),
            ("initials", "", "initials mismatch"),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory(prefix="community-identity-") as directory:
                root = pathlib.Path(directory)
                candidate = json.loads(json.dumps(base))
                candidate["roles"]["committers"][0][field] = value
                roster_path, map_path = root / "roster.json", root / "github-map.json"
                roster_path.write_text(json.dumps(candidate))
                map_path.write_text(json.dumps(mapping))
                with mock.patch.object(roster, "ROOT", root), \
                     mock.patch.object(roster, "DATA_DIR", root), \
                     mock.patch.object(roster, "ROSTER_PATH", roster_path), \
                     mock.patch.object(roster, "MAP_PATH", map_path), \
                     mock.patch.object(roster, "AVATAR_DIR", root / "avatars"):
                    with self.assertRaisesRegex(roster.RosterError, message):
                        roster.validate_bundle(90)

    def test_local_roster_schema_errors_are_roster_errors(self):
        base = json.loads(roster.ROSTER_PATH.read_text())
        mapping = json.loads(roster.MAP_PATH.read_text())
        mutations = (
            ("asf_id", [], "invalid ASF ID"),
            ("name", 123, "name must be non-empty"),
            ("retrieved_at", None, "ISO-8601 UTC string"),
        )
        for field, value, message in mutations:
            with self.subTest(field=field), tempfile.TemporaryDirectory(prefix="community-schema-") as directory:
                root = pathlib.Path(directory)
                candidate = json.loads(json.dumps(base))
                if field == "retrieved_at":
                    candidate[field] = value
                else:
                    candidate["roles"]["committers"][0][field] = value
                roster_path, map_path = root / "roster.json", root / "github-map.json"
                roster_path.write_text(json.dumps(candidate))
                map_path.write_text(json.dumps(mapping))
                with mock.patch.object(roster, "ROOT", root), \
                     mock.patch.object(roster, "DATA_DIR", root), \
                     mock.patch.object(roster, "ROSTER_PATH", roster_path), \
                     mock.patch.object(roster, "MAP_PATH", map_path), \
                     mock.patch.object(roster, "AVATAR_DIR", root / "avatars"):
                    with self.assertRaisesRegex(roster.RosterError, message):
                        roster.validate_bundle(90)

    def test_refresh_validates_paths_before_creating_data_directory(self):
        with tempfile.TemporaryDirectory(prefix="community-refresh-path-") as directory:
            root = pathlib.Path(directory)
            outside = root / "outside"
            outside.mkdir()
            (root / "data").symlink_to(outside, target_is_directory=True)
            data_dir = root / "data" / "community"
            with mock.patch.object(roster, "ROOT", root), \
                 mock.patch.object(roster, "DATA_DIR", data_dir), \
                 mock.patch.object(roster, "ROSTER_PATH", data_dir / "roster.json"), \
                 mock.patch.object(roster, "MAP_PATH", data_dir / "github-map.json"), \
                 mock.patch.object(roster, "AVATAR_DIR", root / "static" / "img" / "community" / "avatars"):
                with self.assertRaisesRegex(roster.RosterError, "symlink path components"):
                    roster.refresh()
            self.assertFalse((outside / "community").exists())

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
                 mock.patch.object(roster, "ROOT", root), \
                 mock.patch.object(roster, "DATA_DIR", root), \
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
                 mock.patch.object(roster, "_validate_repo_paths"), \
                 mock.patch.object(roster, "_validate_avatar_blob"), \
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
                 mock.patch.object(roster, "_validate_repo_paths"), \
                 mock.patch.object(roster, "_fetch_json", return_value={}), \
                 mock.patch.object(roster, "build_roster", return_value=candidate), \
                 mock.patch.object(roster, "_install_avatars"), \
                 mock.patch.object(roster.shutil, "rmtree", side_effect=OSError("cleanup failed")):
                with self.assertRaisesRegex(OSError, "cleanup failed"):
                    roster.refresh()
            self.assertEqual(b"last-good\n", roster_path.read_bytes())

    def test_atomic_roster_write_failure_keeps_last_good_selected(self):
        with tempfile.TemporaryDirectory(prefix="community-write-test-") as directory:
            root = pathlib.Path(directory)
            roster_path, avatar_dir = root / "roster.json", root / "avatars"
            avatar_dir.mkdir()
            roster_path.write_bytes(b"last-good\n")
            candidate = {"roles": {"pmc": [{"avatar": "/img/community/avatars/new.webp"}], "committers": []}}
            with mock.patch.object(roster, "ROSTER_PATH", roster_path), \
                 mock.patch.object(roster, "AVATAR_DIR", avatar_dir), \
                 mock.patch.object(roster, "_validate_repo_paths"), \
                 mock.patch.object(roster, "_validate_avatar_blob"), \
                 mock.patch.object(roster, "_atomic_write", side_effect=OSError("write failed")):
                with self.assertRaisesRegex(OSError, "write failed"):
                    roster._commit_bundle(candidate, {"new.webp": b"new"})
            self.assertEqual(b"last-good\n", roster_path.read_bytes())

    def test_orphan_unlink_failure_is_a_successful_commit_warning(self):
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
                 mock.patch.object(roster, "_validate_repo_paths"), \
                 mock.patch.object(roster, "_validate_avatar_blob"), \
                 mock.patch.object(roster, "_unlink", side_effect=fail_once):
                roster._commit_bundle(candidate, {"new.webp": b"new"})
            self.assertNotEqual(b"last-good\n", roster_path.read_bytes())
            self.assertEqual(b"old", (avatar_dir / "old.webp").read_bytes())
            self.assertEqual(b"new", (avatar_dir / "new.webp").read_bytes())

    def test_corrupt_existing_candidate_destination_is_replaced(self):
        with tempfile.TemporaryDirectory(prefix="community-replace-test-") as directory:
            root = pathlib.Path(directory)
            roster_path, avatar_dir = root / "roster.json", root / "avatars"
            avatar_dir.mkdir()
            roster_path.write_bytes(b"last-good\n")
            raw = b"new"
            name = f"{__import__('hashlib').sha256(raw).hexdigest()}.webp"
            destination = avatar_dir / name
            destination.write_bytes(b"corrupt")
            candidate = {"roles": {"pmc": [{"avatar": f"/img/community/avatars/{name}"}], "committers": []}}
            with mock.patch.object(roster, "ROSTER_PATH", roster_path), \
                 mock.patch.object(roster, "AVATAR_DIR", avatar_dir), \
                 mock.patch.object(roster, "_validate_repo_paths"), \
                 mock.patch.object(roster, "_validate_webp"):
                roster._commit_bundle(candidate, {name: raw})
            self.assertEqual(raw, destination.read_bytes())


class CommunityContentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._site = tempfile.TemporaryDirectory(prefix="community-content-site-")
        hugo_version = subprocess.check_output(["hugo", "version"], text=True)
        if "hugo v0.165.0+extended" not in hugo_version:
            raise RuntimeError(
                f"Community render contracts require Hugo v0.165.0 Extended: {hugo_version.strip()}"
            )
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

    def test_docs_roots_respect_core_platform_llmsfull_ownership(self):
        versions = {
            entry["id"]
            for entry in json.loads((ROOT / "versions.json").read_text(encoding="utf-8"))["versions"]
        }
        core_platform_integrated = {"1.3", "1.0"} <= versions
        for language in ("en", "cn"):
            text = (ROOT / "content" / language / "docs/_index.md").read_text(encoding="utf-8")
            frontmatter = text.split("---", 2)[1]
            if core_platform_integrated:
                self.assertIn("outputs: [HTML, RSS, print, markdown, LLMSFULL]", frontmatter)
            else:
                self.assertNotIn("LLMSFULL", frontmatter)

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
            expected_title = "# 社区" if relative.startswith("cn/") else "# Community"
            self.assertTrue(rendered.startswith(expected_title + "\n"))
            self.assertNotIn("td-page-meta__footer", rendered)
            positions = [rendered.index(marker) for marker in markers]
            self.assertEqual(positions, sorted(positions))
            member_heading = "项目成员" if relative.startswith("cn/") else "Project members"
            self.assertRegex(rendered, rf"(?m)^## {member_heading}$")
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

    def test_explicit_artifact_validator_accepts_prebuilt_site(self):
        roster.validate_rendered_outputs(self.site)
        result = subprocess.run(
            [
                sys.executable,
                "scripts/community_roster.py",
                "validate",
                "--warn-after-days",
                "90",
                "--artifact",
                str(self.site),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_artifact_validator_rejects_swapped_role_sections(self):
        with tempfile.TemporaryDirectory(prefix="community-role-output-") as directory:
            destination = pathlib.Path(directory)
            for relative in (
                "community/index.html",
                "_print/community/index.html",
                "community/index.md",
                "cn/community/index.html",
                "cn/_print/community/index.html",
                "cn/community/index.md",
            ):
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(self.site / relative, target)
            path = destination / "community/index.html"
            rendered = path.read_text(encoding="utf-8")
            rendered = rendered.replace('data-community-role="pmc"', 'data-community-role="temporary"', 1)
            rendered = rendered.replace('data-community-role="committers"', 'data-community-role="pmc"', 1)
            rendered = rendered.replace('data-community-role="temporary"', 'data-community-role="committers"', 1)
            path.write_text(rendered, encoding="utf-8")
            with self.assertRaisesRegex(roster.RosterError, "link parity drift"):
                roster.validate_rendered_outputs(destination)

    def test_artifact_validator_rejects_plain_text_profile_urls(self):
        with tempfile.TemporaryDirectory(prefix="community-fake-output-") as directory:
            destination = pathlib.Path(directory)
            roles = json.loads(roster.ROSTER_PATH.read_text())["roles"]
            for relative in (
                "community/index.html",
                "_print/community/index.html",
                "cn/community/index.html",
                "cn/_print/community/index.html",
            ):
                path = destination / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    '<section data-community-role="pmc">'
                    + " ".join(person["profile_url"] for person in roles["pmc"])
                    + '</section><section data-community-role="committers">'
                    + " ".join(person["profile_url"] for person in roles["committers"])
                    + "</section>"
                )
            for relative, title in (
                ("community/index.md", "Project members"),
                ("cn/community/index.md", "项目成员"),
            ):
                path = destination / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    f"## {title}\n\n### PMC\n"
                    + "\n".join(person["profile_url"] for person in roles["pmc"])
                    + "\n\n### Committers\n"
                    + "\n".join(person["profile_url"] for person in roles["committers"])
                )
            with self.assertRaisesRegex(roster.RosterError, "link parity drift"):
                roster.validate_rendered_outputs(destination)

    def test_fixed_metadata_is_present_in_actual_offline_indexes(self):
        fixture = json.loads(
            (ROOT / "scripts/fixtures/community_search_queries.json").read_text(encoding="utf-8")
        )
        self.assertEqual(24, len(fixture))
        self.assertEqual(24, len({(item["locale"], item["query"]) for item in fixture}))
        for language in ("en", "cn"):
            indexes = list(self.site.glob(f"offline-search-index.{language}.*.json"))
            self.assertEqual(1, len(indexes))
            records = {record["ref"]: record for record in json.loads(indexes[0].read_text())}
            for item in (entry for entry in fixture if entry["locale"] == language):
                ref = item["expected_ref"]
                self.assertIn(ref, records)
                self.assertTrue(records[ref]["keywords"], ref)
                self.assertGreater(records[ref]["boost"], 1, ref)
                normalized_query = item["query"].casefold()
                searchable = " ".join(
                    [records[ref]["title"], *records[ref]["keywords"]]
                ).casefold()
                self.assertIn(normalized_query, searchable, ref)


if __name__ == "__main__":
    unittest.main()
