import json
import os
import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "downloads" / "asf.json"
PARTIAL = ROOT / "layouts" / "_partials" / "asf-downloads.html"
PAGES = (
    ROOT / "content" / "en" / "docs" / "download" / "download.md",
    ROOT / "content" / "cn" / "docs" / "download" / "download.md",
)
I18N = (ROOT / "i18n" / "en.yaml", ROOT / "i18n" / "zh-CN.yaml")
PUBLIC_DIR = pathlib.Path(os.environ["DOWNLOAD_PUBLIC_DIR"]) if os.environ.get("DOWNLOAD_PUBLIC_DIR") else None

# Exact dist state, verified against
# https://downloads.apache.org/hugegraph/<version>/ on 2026-09-13. The data
# file must derive exactly these artifacts; a new release edits both the data
# file and this expectation with a fresh dist listing.
EXPECTED_ARTIFACTS = {
    "1.7.0": {
        "apache-hugegraph-incubating-1.7.0.tar.gz",
        "apache-hugegraph-toolchain-incubating-1.7.0.tar.gz",
        "apache-hugegraph-incubating-1.7.0-src.tar.gz",
        "apache-hugegraph-toolchain-incubating-1.7.0-src.tar.gz",
        "apache-hugegraph-ai-incubating-1.7.0-src.tar.gz",
        "apache-hugegraph-computer-incubating-1.7.0-src.tar.gz",
    },
    "1.5.0": {
        "apache-hugegraph-incubating-1.5.0.tar.gz",
        "apache-hugegraph-toolchain-incubating-1.5.0.tar.gz",
        "apache-hugegraph-incubating-1.5.0-src.tar.gz",
        "apache-hugegraph-toolchain-incubating-1.5.0-src.tar.gz",
        "apache-hugegraph-ai-incubating-1.5.0-src.tar.gz",
        "apache-hugegraph-computer-incubating-1.5.0-src.tar.gz",
    },
    "1.3.0": {
        "apache-hugegraph-incubating-1.3.0.tar.gz",
        "apache-hugegraph-toolchain-incubating-1.3.0.tar.gz",
        "apache-hugegraph-incubating-1.3.0-src.tar.gz",
        "apache-hugegraph-toolchain-incubating-1.3.0-src.tar.gz",
        "apache-hugegraph-ai-incubating-1.3.0-src.tar.gz",
        "apache-hugegraph-commons-incubating-1.3.0-src.tar.gz",
    },
    "1.2.0": {
        "apache-hugegraph-incubating-1.2.0.tar.gz",
        "apache-hugegraph-toolchain-incubating-1.2.0.tar.gz",
        "apache-hugegraph-incubating-1.2.0-src.tar.gz",
        "apache-hugegraph-toolchain-incubating-1.2.0-src.tar.gz",
        "apache-hugegraph-computer-incubating-1.2.0-src.tar.gz",
        "apache-hugegraph-commons-incubating-1.2.0-src.tar.gz",
    },
    "1.0.0": {
        "apache-hugegraph-incubating-1.0.0.tar.gz",
        "apache-hugegraph-toolchain-incubating-1.0.0.tar.gz",
        "apache-hugegraph-computer-incubating-1.0.0.tar.gz",
        "apache-hugegraph-incubating-1.0.0-src.tar.gz",
        "apache-hugegraph-toolchain-incubating-1.0.0-src.tar.gz",
        "apache-hugegraph-computer-incubating-1.0.0-src.tar.gz",
        "apache-hugegraph-commons-incubating-1.0.0-src.tar.gz",
    },
}

# Site-owned labels only; ui_assets_download is inherited from OINK and checked
# in the rendered output below.
FIXED_I18N_KEYS = (
    "download_release_version",
    "download_release_date",
    "download_release_notes",
    "download_table_component",
    "download_table_type",
    "download_table_mirror",
    "download_type_binary",
    "download_type_source",
    "download_asf_note",
)


def load_data() -> dict:
    with DATA.open(encoding="utf-8") as handle:
        return json.load(handle)


def derive_files(release: dict, components: dict) -> set[str]:
    files = set()
    infix = "-incubating" if release["incubating"] else ""
    for kind, suffix in (("binary", ""), ("source", "-src")):
        for component_id in release.get(kind, []):
            prefix = components[component_id]["prefix"]
            files.add(f"{prefix}{infix}-{release['version']}{suffix}.tar.gz")
    return files


def i18n_keys(path: pathlib.Path) -> set[str]:
    keys = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith(("#", " ")) and ":" in line:
            keys.add(line.split(":", 1)[0].strip())
    return keys


class DownloadDataTest(unittest.TestCase):
    def setUp(self) -> None:
        self.data = load_data()

    def test_schema_and_release_ordering(self) -> None:
        data = self.data
        self.assertEqual(
            set(data), {"$comment", "dist_path", "components", "releases"}
        )
        self.assertEqual(data["dist_path"], "hugegraph")
        label_keys = [c["label_key"] for c in data["components"].values()]
        self.assertEqual(len(label_keys), len(set(label_keys)))
        for component_id, component in data["components"].items():
            self.assertRegex(component_id, r"^[a-z][a-z0-9]*\Z")
            self.assertRegex(component["prefix"], r"^apache-hugegraph(-[a-z]+)?\Z")
            self.assertRegex(component["label_key"], r"^download_component_[a-z]+\Z")
        releases = data["releases"]
        versions = [release["version"] for release in releases]
        self.assertEqual(versions, sorted(versions, key=lambda v: tuple(map(int, v.split("."))), reverse=True))
        self.assertEqual(len(versions), len(set(versions)))
        self.assertEqual(sum(1 for release in releases if release.get("latest")), 1)
        self.assertTrue(releases[0].get("latest"), "the newest release must be the latest")
        for release in releases:
            self.assertRegex(release["version"], r"^\d+\.\d+\.\d+\Z")
            self.assertRegex(release["date"], r"^\d{4}-\d{2}-\d{2}\Z")
            self.assertIsInstance(release["incubating"], bool)
            for kind in ("binary", "source"):
                ids = release.get(kind, [])
                self.assertTrue(ids, f"{release['version']} has no {kind} artifacts")
                self.assertEqual(len(ids), len(set(ids)))
                for component_id in ids:
                    self.assertIn(component_id, data["components"])

    def test_derived_artifacts_match_the_verified_dist_listing(self) -> None:
        data = self.data
        derived = {
            release["version"]: derive_files(release, data["components"])
            for release in data["releases"]
        }
        self.assertEqual(derived, EXPECTED_ARTIFACTS)
        total = sum(len(files) for files in derived.values())
        self.assertEqual(total, 31)

    def test_derived_urls_are_well_formed(self) -> None:
        data = self.data
        pattern = re.compile(r"^https://[a-z.]+/[A-Za-z0-9./?=_-]+$")
        for release in data["releases"]:
            for file in derive_files(release, data["components"]):
                urls = (
                    f"https://www.apache.org/dyn/closer.lua/{data['dist_path']}/"
                    f"{release['version']}/{file}?action=download",
                    f"https://downloads.apache.org/{data['dist_path']}/"
                    f"{release['version']}/{file}.asc",
                    f"https://downloads.apache.org/{data['dist_path']}/"
                    f"{release['version']}/{file}.sha512",
                )
                for url in urls:
                    self.assertRegex(url, pattern)

    def test_pages_render_from_data_not_hardcoded_tables(self) -> None:
        for page in PAGES:
            text = page.read_text(encoding="utf-8")
            self.assertIn("{{< asf-downloads latest >}}", text, page)
            self.assertIn("{{< asf-downloads archived >}}", text, page)
            self.assertNotIn("closer.lua", text, page)
            self.assertNotIn(".tar.gz", text, page)
            artifact_links = re.findall(
                r"downloads\.apache\.org/hugegraph/\d", text
            )
            self.assertEqual(artifact_links, [], page)

    def test_partial_derives_urls_with_the_same_tokens(self) -> None:
        # The partial re-derives the same filenames and URLs in Go templates;
        # lock its literal format tokens to this module's derivation so the
        # two cannot drift apart silently.
        template = PARTIAL.read_text(encoding="utf-8")
        for token in (
            '"-incubating" ""',
            '"-src" ""',
            '"%s%s-%s%s.tar.gz" $component.prefix $infix $version $suffix',
            'https://www.apache.org/dyn/closer.lua/%s/%s/%s?action=download',
            'https://downloads.apache.org/%s/%s/%s.asc',
            'https://downloads.apache.org/%s/%s/%s.sha512',
        ):
            self.assertIn(token, template)

    def test_i18n_catalogues_carry_every_label(self) -> None:
        data = self.data
        required = set(FIXED_I18N_KEYS)
        for component in data["components"].values():
            required.add(component["label_key"])
        for catalogue in I18N:
            missing = required - i18n_keys(catalogue)
            self.assertEqual(missing, set(), catalogue)

    def test_rendered_download_pages_have_verified_rows(self) -> None:
        if PUBLIC_DIR is None:
            self.skipTest("set DOWNLOAD_PUBLIC_DIR after an aggregate build")
        for relative in ("docs/download/download/index.html", "cn/docs/download/download/index.html"):
            page = PUBLIC_DIR / relative
            self.assertTrue(page.is_file(), page)
            text = page.read_text(encoding="utf-8")
            self.assertIn("hg-asf-release", text, page)
            labels = re.findall(r'aria-label="([^"<>]+): apache-hugegraph[^"<>]*"', text)
            self.assertTrue(labels, page)
            self.assertTrue(all(label.strip() and label != "ui_assets_download" for label in labels), page)
            self.assertIn("1.7.0", text, page)
            for version, expected_files in EXPECTED_ARTIFACTS.items():
                self.assertIn(f"hugegraph-{version}-release-notes", text, page)
                for filename in expected_files:
                    self.assertIn(filename, text, page)
                    self.assertIn(f"/dyn/closer.lua/hugegraph/{version}/{filename}?action=download", text, page)
                    self.assertIn(f"downloads.apache.org/hugegraph/{version}/{filename}.asc", text, page)
                    self.assertIn(f"downloads.apache.org/hugegraph/{version}/{filename}.sha512", text, page)


if __name__ == "__main__":
    unittest.main()
