#!/usr/bin/env python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0.

import argparse
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import versioning


ORIGIN = "https://hugegraph.apache.org/"
STAGING_ORIGIN = "https://hugegraph-oink.staged.apache.org/"
PUBLISH_PATH = "versions/1.7"
ALLOWED_PATHS = {
    "/docs",
    "/cn/docs",
    "/versions/1.7/docs",
    "/versions/1.7/cn/docs",
    "/versions/1.5/docs",
    "/versions/1.5/cn/docs",
    "/versions/1.3/docs",
    "/versions/1.3/cn/docs",
    "/versions/1.0/docs",
    "/versions/1.0/cn/docs",
}


def rewrite(value: str) -> str:
    return versioning.rewrite_internal_url(
        value,
        origin=ORIGIN,
        publish_path=PUBLISH_PATH,
        allowed_paths=ALLOWED_PATHS,
    )


def _walk_docs_nav_pages(nodes):
    for node in nodes:
        yield node["page"]
        yield from _walk_docs_nav_pages(node.get("children", []))


class VersionUrlTest(unittest.TestCase):
    def test_historical_pruning_allows_footer_without_shared_routes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            assembly = Path(temp_name)
            for language in ("en", "cn"):
                docs = assembly / f"content/{language}/docs"
                docs.mkdir(parents=True)
                (docs / "index.md").write_text("# Docs\n", encoding="utf-8")
                footer = assembly / f"data/footer/{language}.yaml"
                footer.parent.mkdir(parents=True, exist_ok=True)
                footer.write_text(
                    "links:\n  - { label: Security, url: /docs/guides/security/ }\n",
                    encoding="utf-8",
                )

            versioning.prune_historical_content(assembly, ORIGIN)

            for language in ("en", "cn"):
                rendered = (assembly / f"data/footer/{language}.yaml").read_text(
                    encoding="utf-8"
                )
                self.assertIn("url: /docs/guides/security/", rendered)

    def test_historical_pruning_rejects_duplicate_shared_footer_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            assembly = Path(temp_name)
            for language in ("en", "cn"):
                docs = assembly / f"content/{language}/docs"
                docs.mkdir(parents=True)
                (docs / "index.md").write_text("# Docs\n", encoding="utf-8")
                footer = assembly / f"data/footer/{language}.yaml"
                footer.parent.mkdir(parents=True, exist_ok=True)
                prefix = "cn/" if language == "cn" else ""
                footer.write_text(
                    "links:\n"
                    f"  - {{ label: Blog, url: /{prefix}blog/ }}\n"
                    f"  - {{ label: Blog again, url: /{prefix}blog/ }}\n",
                    encoding="utf-8",
                )

            with self.assertRaisesRegex(SystemExit, "expected one shared footer route"):
                versioning.prune_historical_content(assembly, ORIGIN)

    def test_toc_accessible_name_accepts_en_cn_and_no_toc(self) -> None:
        fixtures = (
            (
                "docs/config/index.html",
                '<nav id="TableOfContents" aria-label="Content"></nav>',
            ),
            (
                "cn/docs/config/index.html",
                '<nav id="TableOfContents" aria-label="目录">'
                '<ul><li><a href="#server">Server</a></li></ul></nav>',
            ),
            ("docs/short/index.html", "<main>No table of contents</main>"),
        )
        for relative, fragment in fixtures:
            with self.subTest(relative=relative):
                parser = versioning.DocumentParser()
                parser.feed(fragment)
                versioning.require_toc_accessible_name(parser, relative)

    def test_toc_accessible_name_rejects_missing_wrong_and_duplicates(self) -> None:
        fixtures = (
            (
                "docs/config/index.html",
                '<nav id="TableOfContents"></nav>',
            ),
            (
                "cn/docs/config/index.html",
                '<nav id="TableOfContents" aria-label="Content"></nav>',
            ),
            (
                "docs/config/index.html",
                '<nav id="TableOfContents" aria-label="Content" '
                'aria-label="Content"></nav>',
            ),
            (
                "docs/config/index.html",
                '<nav id="TableOfContents" aria-label="Content"></nav>'
                '<nav id="TableOfContents" aria-label="Content"></nav>',
            ),
        )
        for relative, fragment in fixtures:
            with self.subTest(fragment=fragment):
                parser = versioning.DocumentParser()
                parser.feed(fragment)
                with self.assertRaises(SystemExit):
                    versioning.require_toc_accessible_name(parser, relative)

    def test_validate_artifact_rejects_missing_toc_accessible_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            artifact = temp / "artifact"
            artifact.mkdir()
            entry = json.loads(
                (versioning.ROOT / "versions.json").read_text(encoding="utf-8")
            )["versions"][0]
            sha = "a" * 40
            metadata = dict(entry)
            metadata.update(
                {
                    "sha": sha,
                    "baseURL": ORIGIN,
                    "docsNavigation": versioning.DOCS_NAV_EXPECTED_STATS["latest"],
                }
            )
            (artifact / ".version.json").write_text(
                json.dumps(metadata), encoding="utf-8"
            )
            (artifact / "index.html").write_text(
                '<nav id="TableOfContents"></nav>', encoding="utf-8"
            )
            contract = temp / "url-contract.json"
            contract.write_text(
                json.dumps({"schemaVersion": 1, "routes": []}), encoding="utf-8"
            )
            args = argparse.Namespace(
                manifest=versioning.ROOT / "versions.json",
                version="latest",
                sha=sha,
                site_origin=ORIGIN,
                artifact=artifact,
            )
            with (
                mock.patch.object(versioning, "URL_CONTRACT", contract),
                self.assertRaisesRegex(SystemExit, "TableOfContents nav"),
            ):
                versioning.validate_artifact(args)

    def test_version_urls_preserve_language_and_order(self) -> None:
        manifest = {
            "versions": [
                {"id": "latest", "name": "latest", "publishPath": ""},
                {"id": "1.7", "name": "1.7", "publishPath": "versions/1.7"},
                {"id": "1.5", "name": "1.5", "publishPath": "versions/1.5"},
                {"id": "1.3", "name": "1.3", "publishPath": "versions/1.3"},
                {"id": "1.0", "name": "1.0", "publishPath": "versions/1.0"},
            ]
        }
        self.assertEqual(
            [item["url"] for item in versioning.version_urls(manifest, ORIGIN, "en")],
            [
                f"{ORIGIN}docs/",
                f"{ORIGIN}versions/1.7/docs/",
                f"{ORIGIN}versions/1.5/docs/",
                f"{ORIGIN}versions/1.3/docs/",
                f"{ORIGIN}versions/1.0/docs/",
            ],
        )
        self.assertEqual(
            [item["url"] for item in versioning.version_urls(manifest, ORIGIN, "cn")],
            [
                f"{ORIGIN}cn/docs/",
                f"{ORIGIN}versions/1.7/cn/docs/",
                f"{ORIGIN}versions/1.5/cn/docs/",
                f"{ORIGIN}versions/1.3/cn/docs/",
                f"{ORIGIN}versions/1.0/cn/docs/",
            ],
        )
        self.assertEqual(
            versioning.language_version_params(manifest, ORIGIN, "en")["version_menu"],
            "Releases",
        )
        self.assertEqual(
            versioning.language_version_params(manifest, ORIGIN, "cn")["version_menu"],
            "版本",
        )
        self.assertEqual(
            versioning.language_version_params(manifest, ORIGIN, "cn")[
                "url_latest_version"
            ],
            f"{ORIGIN}cn/docs/",
        )

    def test_direct_hugo_config_is_derived_from_five_version_manifest(self) -> None:
        manifest = versioning.load_manifest(versioning.ROOT / "versions.json")
        latest = manifest["versions"][0]
        config = versioning.derived_version_config(manifest, latest, ORIGIN)
        expected = ["latest", "1.7", "1.5", "1.3", "1.0"]
        self.assertEqual(
            [item["version"] for item in config["params"]["versions"]], expected
        )
        for language in ("en", "cn"):
            self.assertEqual(
                [
                    item["version"]
                    for item in config["languages"][language]["params"]["versions"]
                ],
                expected,
            )
        self.assertNotIn("1.2", json.dumps(config))

    def test_write_error_documents_keeps_localized_404_status_targets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            output = Path(temp_name)
            for relative in (
                "404.html",
                "cn/404.html",
                "versions/1.7/404.html",
                "versions/1.7/cn/404.html",
            ):
                page = output / relative
                page.parent.mkdir(parents=True, exist_ok=True)
                page.write_text("not found", encoding="utf-8")
            seen: set[str] = set()
            self.assertEqual(versioning.write_error_documents(output, seen), 4)
            self.assertEqual(
                (output / ".htaccess").read_text(encoding="utf-8"),
                'RedirectMatch 404 "(?i)(?:^|/)\\.git(?:/|$)"\n'
                "ErrorDocument 404 /404.html\n",
            )
            self.assertEqual(
                (output / "cn/.htaccess").read_text(encoding="utf-8"),
                "ErrorDocument 404 /cn/404.html\n",
            )
            self.assertEqual(
                (output / "versions/1.7/cn/.htaccess").read_text(encoding="utf-8"),
                "ErrorDocument 404 /versions/1.7/cn/404.html\n",
            )

    def test_write_error_documents_requires_root_404_for_git_deny(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            output = Path(temp_name)
            page = output / "versions/1.7/404.html"
            page.parent.mkdir(parents=True)
            page.write_text("not found", encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "root 404.html"):
                versioning.write_error_documents(output, set())
            self.assertFalse((output / ".htaccess").exists())

    def test_error_documents_must_not_claim_canonical_urls(self) -> None:
        for relative in (
            "404.html",
            "cn/404.html",
        ):
            with self.subTest(relative=relative):
                self.assertTrue(
                    versioning.require_error_document_without_canonical(relative, [])
                )
                with self.assertRaises(SystemExit):
                    versioning.require_error_document_without_canonical(
                        relative,
                        ['<link rel="canonical" href="https://example.com/404.html">'],
                    )
        self.assertFalse(
            versioning.require_error_document_without_canonical(
                "docs/404.html",
                ['<link rel="canonical" href="https://example.com/docs/404.html">'],
            )
        )

    def test_ensure_frontmatter_preserves_body_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            page = Path(temp_name) / "legacy.md"
            page.write_text("## Legacy body\n", encoding="utf-8")
            self.assertEqual(
                versioning.ensure_frontmatter(
                    page,
                    title="Legacy title",
                    link_title="Legacy link",
                    weight=100,
                ),
                1,
            )
            rendered = page.read_text(encoding="utf-8")
            self.assertIn('title: "Legacy title"', rendered)
            self.assertTrue(rendered.endswith("## Legacy body\n"))
            self.assertEqual(
                versioning.ensure_frontmatter(
                    page,
                    title="Changed title",
                    link_title="Changed link",
                    weight=1,
                ),
                0,
            )
            self.assertEqual(page.read_text(encoding="utf-8"), rendered)

    def test_ensure_search_metadata_preserves_frontmatter_and_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            page = Path(temp_name) / "config.md"
            page.write_text(
                '---\ntitle: "Config"\nweight: 2\n---\n\n## Body\n',
                encoding="utf-8",
            )
            self.assertEqual(
                versioning.ensure_search_metadata(
                    page,
                    keywords=("gremlin.graph", "hugegraph.properties"),
                    boost=1.5,
                ),
                1,
            )
            rendered = page.read_text(encoding="utf-8")
            self.assertIn("search_keywords:\n  - gremlin.graph\n", rendered)
            self.assertIn("search_boost: 1.5\n---\n\n## Body\n", rendered)
            self.assertEqual(
                versioning.ensure_search_metadata(
                    page,
                    keywords=("changed",),
                    boost=9,
                ),
                0,
            )
            self.assertEqual(page.read_text(encoding="utf-8"), rendered)

    def test_ensure_search_excluded_is_fail_closed_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            page = Path(temp_name) / "cla.md"
            page.write_text(
                '---\ntitle: "Contributor Agreement"\n---\n\n## Body\n',
                encoding="utf-8",
            )
            self.assertEqual(versioning.ensure_search_excluded(page), 1)
            rendered = page.read_text(encoding="utf-8")
            self.assertIn("search_exclude: true\n---\n\n## Body\n", rendered)
            self.assertEqual(versioning.ensure_search_excluded(page), 0)
            self.assertEqual(page.read_text(encoding="utf-8"), rendered)

            page.write_text(
                '---\ntitle: "Contributor Agreement"\nsearch_exclude: false\n---\n',
                encoding="utf-8",
            )
            with self.assertRaises(SystemExit):
                versioning.ensure_search_excluded(page)

    def test_materialize_docs_navigation_adapts_historical_routes_and_groups(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            assembly = Path(temp_name)
            (assembly / "data").mkdir()
            shutil.copy2(
                versioning.ROOT / "data/docs_nav.json",
                assembly / "data/docs_nav.json",
            )
            routes = (
                "/docs/_nav/start",
                "/docs/_nav/components",
                "/docs/_nav/develop",
                "/docs/_nav/operate",
                "/docs/_nav/reference",
                "/docs/introduction/readme",
                "/docs/quickstart/toolchain",
                "/docs/quickstart/toolchain/hugegraph-loader",
                "/docs/clients",
                "/docs/clients/gremlin-console",
                "/docs/config",
                "/docs/config/config-guide",
                "/docs/performance",
                "/docs/performance/api-preformance",
                "/docs/performance/api-preformance/hugegraph-api-0.2",
                "/docs/changelog",
                "/docs/changelog/hugegraph-1.5.0-release-notes",
            )
            for language in ("en", "cn"):
                for route in routes:
                    relative = route.removeprefix("/docs/")
                    path = assembly / f"content/{language}/docs/{relative}.md"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    manual_link = (
                        f"manual_link: /{'cn/' if language == 'cn' else ''}docs/quickstart/\n"
                        if "/_nav/" in route
                        else ""
                    )
                    path.write_text(
                        f"---\ntitle: fixture\n{manual_link}---\n", encoding="utf-8"
                    )

            stats = versioning.materialize_docs_navigation(assembly, "versions/1.7")
            self.assertEqual(stats["groups"], 5)
            self.assertEqual(stats["scopedLinks"], 10)
            self.assertGreater(stats["removed"], 0)
            nav = json.loads(
                (assembly / "data/docs_nav.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                [group["group"] for group in nav["sections"]],
                list(versioning.DOCS_NAV_GROUP_IDS),
            )
            all_pages = list(_walk_docs_nav_pages(nav["sections"]))
            self.assertIn("/docs/introduction/readme", all_pages)
            self.assertIn("/docs/performance/api-preformance", all_pages)
            self.assertNotIn("/docs/introduction", all_pages)
            self.assertIn(
                "/docs/introduction/readme/",
                nav["active_path_by_url"],
            )
            original_digest = stats["treeSha256"]
            self.assertRegex(original_digest, r"^[0-9a-f]{64}$")
            moved = json.loads(json.dumps(nav["sections"]))
            moved[0]["children"].append(moved[1]["children"].pop())
            self.assertNotEqual(
                versioning.docs_navigation_tree_sha256(moved),
                original_digest,
            )
            self.assertEqual(
                nav["children_by_url"]["/docs/"],
                [f"/docs/_nav/{group}" for group in versioning.DOCS_NAV_GROUP_IDS],
            )
            self.assertIn(
                "manual_link: /versions/1.7/cn/docs/quickstart/",
                (assembly / "content/cn/docs/_nav/start.md").read_text(
                    encoding="utf-8"
                ),
            )

    def test_docs_navigation_json_requires_exact_localized_groups(self) -> None:
        groups = [
            {
                "title": title,
                "kind": "external",
                "url": f"https://example.org/docs/{index}/",
                "children": [{"title": "child"}],
            }
            for index, title in enumerate(versioning.DOCS_NAV_GROUP_TITLES["en"])
        ]
        nav = {"root": {"children": [{"id": "/docs/", "children": groups}]}}
        versioning.require_docs_navigation_json(nav, "navigation.json", "en")
        groups[0]["title"] = "Changed"
        with self.assertRaises(SystemExit):
            versioning.require_docs_navigation_json(nav, "navigation.json", "en")

    def test_legacy_wechat_images_ignore_historical_alt_text(self) -> None:
        source = (
            '<img src="https://github.com/apache/hugegraph-doc/blob/master/'
            'assets/images/wechat.png?raw=true" alt="QR png" width="300"/>'
            '\n<img width="200" alt="changed" src="https://raw.githubusercontent.com/'
            'apache/hugegraph-doc/master/assets/images/wechat.png">\n'
        )
        rendered, count = versioning.replace_legacy_wechat_images(source, "en")
        self.assertEqual(count, 2)
        self.assertIn(
            "![Apache HugeGraph WeChat QR Code](/images/docs/community/wechat.png)"
            '{width="300" height="94"}',
            rendered,
        )
        self.assertIn('{width="200" height="63"}', rendered)
        self.assertNotIn("github.com/apache/hugegraph-doc", rendered)
        self.assertNotIn("raw.githubusercontent.com", rendered)

    def test_historical_performance_routes_accept_source_and_migrated_states(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            summary = Path(temp_name) / "SUMMARY.md"
            historical = "\n".join(
                f"[route {index}](performance/api-preformance/{index})"
                for index in range(3)
            )
            summary.write_text(historical, encoding="utf-8")
            self.assertEqual(
                versioning.repair_historical_performance_routes(summary), 0
            )
            migrated = historical.replace(
                "performance/api-preformance", "performance/api-performance", 2
            )
            summary.write_text(migrated, encoding="utf-8")
            self.assertEqual(
                versioning.repair_historical_performance_routes(summary), 2
            )
            self.assertEqual(summary.read_text(encoding="utf-8"), historical)

    def test_historical_performance_routes_reject_unknown_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            summary = Path(temp_name) / "SUMMARY.md"
            summary.write_text(
                "[route](performance/api-preformance/one)", encoding="utf-8"
            )
            with self.assertRaises(SystemExit):
                versioning.repair_historical_performance_routes(summary)

    def test_historical_server_heading_normalization_skips_fenced_code(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            page = Path(temp_name) / "hugegraph-server.md"
            page.write_text(
                '---\ntitle: "HugeGraph Server"\n---\n\n'
                "### 1 Overview\n"
                "#### 1.1 Install\n"
                "````shell\n"
                "# shell comment\n"
                "### rendered as example text\n"
                "```\n"
                "````\n"
                "~~~markdown\n"
                "##### another example\n"
                "~~~\n"
                "### 2 Run\n",
                encoding="utf-8",
            )
            self.assertEqual(versioning.normalize_historical_server_headings(page), 3)
            rendered = page.read_text(encoding="utf-8")
            self.assertIn("## 1 Overview\n### 1.1 Install\n", rendered)
            self.assertIn("# shell comment\n### rendered as example text\n", rendered)
            self.assertIn("~~~markdown\n##### another example\n~~~\n", rendered)
            self.assertTrue(rendered.endswith("## 2 Run\n"))
            self.assertEqual(versioning.normalize_historical_server_headings(page), 0)
            self.assertEqual(page.read_text(encoding="utf-8"), rendered)

    def test_historical_server_heading_normalization_rejects_skips(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            page = Path(temp_name) / "hugegraph-server.md"
            page.write_text("### Overview\n##### Skipped child\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                versioning.normalize_historical_server_headings(page)

    def test_exact_legacy_content_fixes_cover_every_bound_mapping(self) -> None:
        for version, fixes in versioning.LEGACY_EXACT_CONTENT_FIXES.items():
            with (
                self.subTest(version=version),
                tempfile.TemporaryDirectory() as temp_name,
            ):
                assembly = Path(temp_name)
                fixtures: dict[Path, list[str]] = {}
                for language, relative, old, _, expected_count in fixes:
                    path = assembly / "content" / language / relative
                    fixtures.setdefault(path, []).extend([old] * expected_count)
                for path, source in fixtures.items():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("\n".join(source), encoding="utf-8")

                self.assertEqual(
                    versioning.apply_exact_legacy_content_fixes(assembly, version),
                    sum(fix[4] for fix in fixes),
                )
                for language, relative, old, new, expected_count in fixes:
                    rendered = (assembly / "content" / language / relative).read_text(
                        encoding="utf-8"
                    )
                    self.assertNotIn(old, rendered)
                    self.assertEqual(rendered.count(new), expected_count)

    def test_historical_pages_are_noindex_and_aliases_are_locale_aware(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            output = Path(temp_name)
            for index, language_prefix in enumerate(("", "cn/")):
                target = (
                    output
                    / language_prefix
                    / "docs/quickstart/hugegraph/hugegraph-server/index.html"
                )
                target.parent.mkdir(parents=True)
                target.write_text(
                    '<meta name="robots" content="index, follow">'
                    if index == 0
                    else '<meta name="robots" content="noindex, nofollow">',
                    encoding="utf-8",
                )
            error_page = output / "404.html"
            error_page.write_text(
                '<meta name="robots" content="noindex,nofollow">', encoding="utf-8"
            )
            self.assertEqual(versioning.mark_historical_pages_noindex(output), 2)
            self.assertIn(
                "noindex,nofollow", error_page.read_text(encoding="utf-8")
            )
            self.assertEqual(
                versioning.write_historical_route_aliases(
                    output, ORIGIN, "versions/1.0"
                ),
                2,
            )
            for language_prefix in ("", "cn/"):
                alias = (
                    output
                    / language_prefix
                    / "docs/quickstart/hugegraph-server/index.html"
                )
                body = alias.read_text(encoding="utf-8")
                self.assertIn('content="noindex,follow"', body)
                self.assertIn(
                    f"{ORIGIN}versions/1.0/{language_prefix}"
                    "docs/quickstart/hugegraph/hugegraph-server/",
                    body,
                )
            self.assertFalse((output / "cn/cn").exists())

    def test_exact_legacy_content_fixes_fail_closed_on_count_drift(self) -> None:
        language, relative, old, _, _ = versioning.LEGACY_EXACT_CONTENT_FIXES["1.5"][0]
        for source in ("no expected anchor", f"{old}\n{old}"):
            with (
                self.subTest(matches=source.count(old)),
                tempfile.TemporaryDirectory() as temp_name,
            ):
                assembly = Path(temp_name)
                path = assembly / "content" / language / relative
                path.parent.mkdir(parents=True)
                path.write_text(source, encoding="utf-8")
                with self.assertRaises(SystemExit):
                    versioning.apply_exact_legacy_content_fixes(assembly, "1.5")

    def test_17_exact_fixes_exclude_updated_server_page(self) -> None:
        server_path = "docs/quickstart/hugegraph/hugegraph-server.md"
        self.assertNotIn(
            server_path,
            {
                relative
                for _, relative, _, _, _ in versioning.LEGACY_EXACT_CONTENT_FIXES["1.7"]
            },
        )

    def test_legacy_adapter_normalizes_server_headings_for_all_archives(
        self,
    ) -> None:
        for version in ("1.7", "1.5"):
            with (
                self.subTest(version=version),
                tempfile.TemporaryDirectory() as temp_name,
            ):
                assembly = Path(temp_name)
                for language in ("en", "cn"):
                    docs = assembly / f"content/{language}/docs"
                    server = docs / "quickstart/hugegraph/hugegraph-server.md"
                    server.parent.mkdir(parents=True)
                    server.write_text(
                        "### 1 Server\n#### 1.1 Start\n"
                        "```shell\n# keep this comment\n```\n",
                        encoding="utf-8",
                    )
                    summary = docs / "SUMMARY.md"
                    summary.write_text(
                        "\n".join(
                            f"[route {index}](performance/"
                            + ("api-performance" if index < 2 else "api-preformance")
                            + f"/{index})"
                            for index in range(3)
                        ),
                        encoding="utf-8",
                    )

                exact_fixtures: dict[Path, list[str]] = {}
                for (
                    language,
                    relative,
                    old,
                    _,
                    expected_count,
                ) in versioning.LEGACY_EXACT_CONTENT_FIXES[version]:
                    path = assembly / "content" / language / relative
                    exact_fixtures.setdefault(path, []).extend([old] * expected_count)
                for path, source in exact_fixtures.items():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    existing = path.read_text(encoding="utf-8") if path.exists() else ""
                    path.write_text(
                        existing + "\n" + "\n".join(source) + "\n",
                        encoding="utf-8",
                    )

                with (
                    mock.patch.object(versioning, "ensure_frontmatter", return_value=0),
                    mock.patch.object(
                        versioning, "ensure_search_excluded", return_value=0
                    ),
                    mock.patch.object(
                        versioning, "ensure_search_metadata", return_value=0
                    ),
                ):
                    versioning.apply_known_legacy_fixes(assembly, version)

                for language in ("en", "cn"):
                    docs = assembly / f"content/{language}/docs"
                    server = (
                        docs / "quickstart/hugegraph/hugegraph-server.md"
                    ).read_text(encoding="utf-8")
                    self.assertTrue(server.startswith("## 1 Server\n### 1.1 Start\n"))
                    self.assertIn("```shell\n# keep this comment\n```\n", server)
                    summary = (docs / "SUMMARY.md").read_text(encoding="utf-8")
                    self.assertNotIn("performance/api-performance", summary)
                    self.assertEqual(summary.count("performance/api-preformance"), 3)

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
        for production_url in (
            "https://hugegraph.apache.org/docs/config/",
            "https://HUGEGRAPH.APACHE.ORG/docs/config/",
            "https://hugegraph.apache.org.:443/docs/config/",
        ):
            with self.subTest(production_url=production_url):
                self.assertEqual(
                    versioning.rewrite_internal_url(
                        production_url,
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
        for unsafe in (
            "https://hugegraph.apache.org:444/docs/config/",
            "https://evil@hugegraph-oink.staged.apache.org/docs/",
            "https://@hugegraph-oink.staged.apache.org/docs/",
            "https://hugegraph-oink.staged.apache.org\\docs/",
            "https://hugegraph-oink.staged.apache.org。/docs/",
            "https://hugegraph.apache.org%2e/docs/",
            "https://ｈｕｇｅｇｒａｐｈ.apache.org/docs/",
            r"https:\hugegraph-oink.staged.apache.org\docs/",
            r"https:/\hugegraph-oink.staged.apache.org\docs/",
        ):
            with (
                self.subTest(unsafe=unsafe),
                self.assertRaises(SystemExit),
            ):
                versioning.rewrite_internal_url(
                    unsafe,
                    origin=STAGING_ORIGIN,
                    publish_path=PUBLISH_PATH,
                    allowed_paths=ALLOWED_PATHS,
                )

    def test_latest_staging_scope_preserves_production_history_selector(self) -> None:
        manifest = versioning.load_manifest(versioning.ROOT / "versions.json")
        latest = manifest["versions"][0]
        with tempfile.TemporaryDirectory() as temp_name:
            output = Path(temp_name)
            history_url = f"{ORIGIN}versions/1.7/docs/"
            page = output / "index.html"
            page.write_text(
                f'<a href="{ORIGIN}docs/">latest</a>'
                f'<a href="{history_url}">1.7</a>',
                encoding="utf-8",
            )
            llms = output / "llms-full.txt"
            llms.write_text(
                f"# Corpus\n\n- [Latest]({ORIGIN}docs/)\n"
                f"- [1.7]({history_url})\n",
                encoding="utf-8",
            )

            versioning.scope_version_artifact(
                output,
                manifest,
                latest,
                STAGING_ORIGIN,
                historical_origin=ORIGIN,
            )

            rendered = page.read_text(encoding="utf-8")
            self.assertIn(f'href="{STAGING_ORIGIN}docs/"', rendered)
            self.assertIn(f'href="{history_url}"', rendered)
            rendered_llms = llms.read_text(encoding="utf-8")
            self.assertIn(f"]({STAGING_ORIGIN}docs/)", rendered_llms)
            self.assertIn(f"]({history_url})", rendered_llms)

    def test_rejects_non_selector_cross_version_url(self) -> None:
        with self.assertRaises(SystemExit):
            rewrite("/versions/1.5/docs/config/")

    def test_maps_known_historical_routes(self) -> None:
        self.assertEqual(
            rewrite("https://hugegraph.apache.org/versions/1.7/docs/introduction/"),
            "https://hugegraph.apache.org/versions/1.7/docs/introduction/",
        )
        self.assertEqual(
            versioning.rewrite_internal_url(
                "https://hugegraph.apache.org/versions/1.5/docs/introduction/",
                origin=ORIGIN,
                publish_path="versions/1.5",
                allowed_paths=ALLOWED_PATHS,
            ),
            "https://hugegraph.apache.org/versions/1.5/docs/introduction/readme/",
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

    def test_language_fallback_scopes_to_each_artifact_base(self) -> None:
        manifest = {
            "versions": [
                {"publishPath": ""},
                {"publishPath": "versions/1.7"},
                {"publishPath": "versions/1.5"},
            ]
        }
        relative = "cn/docs/changelog/hugegraph-0.12.0-release-notes/index.html"
        for publish_path, expected_url in (
            ("", "/"),
            ("versions/1.7", f"{STAGING_ORIGIN}versions/1.7/"),
            ("versions/1.5", f"{STAGING_ORIGIN}versions/1.5/"),
        ):
            with self.subTest(publish_path=publish_path):
                with tempfile.TemporaryDirectory() as temp_name:
                    output = Path(temp_name)
                    page = output / relative
                    page.parent.mkdir(parents=True)
                    action_data = {
                        "actions": [
                            {
                                "id": "switch_language",
                                "available": True,
                                "options": [
                                    {
                                        "id": "en-US",
                                        "active": False,
                                        "url": "/",
                                    },
                                    {
                                        "id": "zh-CN",
                                        "active": True,
                                        "url": "/cn/docs/changelog/",
                                    },
                                ],
                            }
                        ]
                    }
                    page.write_text(
                        '<script type="application/json" id="td-action-manifest">'
                        + json.dumps(action_data)
                        + "</script>",
                        encoding="utf-8",
                    )

                    versioning.scope_version_artifact(
                        output,
                        manifest,
                        {"publishPath": publish_path},
                        STAGING_ORIGIN,
                    )

                    rendered = page.read_text(encoding="utf-8")
                    scoped = json.loads(
                        versioning.ACTION_MANIFEST_RE.search(rendered).group("body")
                    )
                    switch = scoped["actions"][0]
                    self.assertEqual(switch["options"][0]["url"], expected_url)

    def test_latest_language_fallback_preserves_root_relative_url(self) -> None:
        relative = "cn/docs/changelog/hugegraph-0.12.0-release-notes/index.html"
        current_url = f"{ORIGIN}cn/docs/changelog/hugegraph-0.12.0-release-notes/"
        action_data = {
            "actions": [
                {
                    "id": "switch_language",
                    "available": True,
                    "options": [
                        {
                            "id": "en-US",
                            "title": "English",
                            "active": False,
                            "available": True,
                            "url": "/",
                        },
                        {
                            "id": "zh-CN",
                            "title": "简体中文",
                            "active": True,
                            "available": True,
                            "url": "/cn/docs/changelog/hugegraph-0.12.0-release-notes/",
                        },
                    ],
                }
            ]
        }
        self.assertEqual(
            versioning.scope_language_fallback_urls(action_data, relative, ORIGIN),
            0,
        )
        self.assertEqual(action_data["actions"][0]["options"][0]["url"], "/")
        versioning.validate_language_switch_contract(
            action_data,
            relative,
            {"en-US": ORIGIN, "zh-CN": current_url},
            current_url,
            "zh-CN",
        )

    def test_language_switch_validator_fails_closed(self) -> None:
        relative = "cn/docs/changelog/hugegraph-0.12.0-release-notes/index.html"
        expected_base = f"{STAGING_ORIGIN}versions/1.7/"
        current_url = (
            f"{expected_base}cn/docs/changelog/hugegraph-0.12.0-release-notes/"
        )
        expected_urls = {
            "en-US": expected_base,
            "zh-CN": current_url,
        }
        valid = {
            "actions": [
                {
                    "id": "switch_language",
                    "available": True,
                    "options": [
                        {
                            "id": "en-US",
                            "title": "English",
                            "active": False,
                            "available": True,
                            "url": expected_base,
                        },
                        {
                            "id": "zh-CN",
                            "title": "简体中文",
                            "active": True,
                            "available": True,
                            "url": "/versions/1.7/cn/docs/changelog/"
                            "hugegraph-0.12.0-release-notes/",
                        },
                    ],
                }
            ]
        }
        versioning.validate_language_switch_contract(
            valid, relative, expected_urls, current_url, "zh-CN"
        )

        escaped = json.loads(json.dumps(valid))
        escaped["actions"][0]["options"][0]["url"] = STAGING_ORIGIN
        with self.assertRaises(SystemExit):
            versioning.validate_language_switch_contract(
                escaped, relative, expected_urls, current_url, "zh-CN"
            )

        missing = {"actions": []}
        with self.assertRaises(SystemExit):
            versioning.validate_language_switch_contract(
                missing, relative, expected_urls, current_url, "zh-CN"
            )

        active = json.loads(json.dumps(valid))
        active["actions"][0]["options"][0]["active"] = True
        with self.assertRaises(SystemExit):
            versioning.validate_language_switch_contract(
                active, relative, expected_urls, current_url, "zh-CN"
            )

        duplicate = json.loads(json.dumps(valid))
        duplicate["actions"].append(duplicate["actions"][0])
        with self.assertRaises(SystemExit):
            versioning.validate_language_switch_contract(
                duplicate, relative, expected_urls, current_url, "zh-CN"
            )

        reversed_options = json.loads(json.dumps(valid))
        reversed_options["actions"][0]["options"].reverse()
        with self.assertRaises(SystemExit):
            versioning.validate_language_switch_contract(
                reversed_options, relative, expected_urls, current_url, "zh-CN"
            )

        for invalid_url in ("", "next/", "//example.org/", "javascript:alert(1)"):
            with self.subTest(invalid_url=invalid_url):
                invalid = json.loads(json.dumps(valid))
                invalid["actions"][0]["options"][0]["url"] = invalid_url
                with self.assertRaises(SystemExit):
                    versioning.validate_language_switch_contract(
                        invalid, relative, expected_urls, current_url, "zh-CN"
                    )

        unavailable = json.loads(json.dumps(valid))
        unavailable["actions"][0]["options"][0]["available"] = False
        with self.assertRaises(SystemExit):
            versioning.validate_language_switch_contract(
                unavailable, relative, expected_urls, current_url, "zh-CN"
            )

        disabled_action = json.loads(json.dumps(valid))
        disabled_action["actions"][0]["available"] = False
        with self.assertRaises(SystemExit):
            versioning.validate_language_switch_contract(
                disabled_action, relative, expected_urls, current_url, "zh-CN"
            )

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

    def test_aggregate_security_scan_runs_after_metadata_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            output = temp / "aggregate"
            source = temp / "artifacts/latest"
            source.mkdir(parents=True)
            entry = {"id": "latest", "publishPath": "", "sha": "a" * 40}
            (source / ".version.json").write_text(json.dumps(entry), encoding="utf-8")
            args = argparse.Namespace(
                resolved_manifest=temp / "resolved.json",
                artifacts=temp / "artifacts",
                artifact_prefix="",
                site_origin=ORIGIN,
                historical_origin="https://hugegraph.apache.org",
                output=output,
                asf_profile="oink",
                asf_whoami="asf-staging-oink",
            )

            def assert_complete_aggregate(path: Path, origin: str) -> None:
                self.assertEqual(path, output.resolve())
                self.assertEqual(origin, ORIGIN)
                self.assertTrue((path / ".asf.yaml").is_file())
                asf_text = (path / ".asf.yaml").read_text(encoding="utf-8")
                self.assertIn(
                    "staging:\n  profile: oink\n  whoami: asf-staging-oink\n",
                    asf_text,
                )
                self.assertTrue((path / "build-metadata/versions.json").is_file())

            with (
                mock.patch.object(
                    versioning,
                    "load_resolved_manifest",
                    return_value={"versions": [entry]},
                ),
                mock.patch.object(versioning, "require_metadata_matches"),
                mock.patch.object(
                    versioning, "validate_artifact"
                ) as validate_artifact,
                mock.patch.object(versioning, "write_error_documents", return_value=1),
                mock.patch.object(versioning, "sitemap_locations", return_value=[]),
                mock.patch.object(
                    versioning,
                    "validate_output_security",
                    side_effect=assert_complete_aggregate,
                ) as security_scan,
            ):
                versioning.aggregate(args)

            security_scan.assert_called_once_with(output.resolve(), ORIGIN)
            validate_args = validate_artifact.call_args.args[0]
            self.assertEqual(
                validate_args.historical_origin,
                "https://hugegraph.apache.org",
            )

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
        with self.assertRaises(SystemExit):
            versioning.prepare_output_directory(versioning.ROOT.parent, "fixture")
        checkout_child = versioning.ROOT / ".test-output-must-not-be-deleted"
        checkout_child.mkdir(exist_ok=True)
        try:
            with self.assertRaises(SystemExit):
                versioning.prepare_output_directory(checkout_child, "fixture")
            self.assertTrue(checkout_child.is_dir())
        finally:
            checkout_child.rmdir()

    def test_output_cleanup_rejects_sibling_checkout_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            sibling = Path(temp_name) / "sibling-worktree"
            sibling.mkdir()
            (sibling / ".git").write_text(
                "gitdir: /tmp/fixture.git/worktrees/sibling\n",
                encoding="utf-8",
            )
            with (
                mock.patch.object(versioning.shutil, "rmtree") as remove,
                self.assertRaisesRegex(SystemExit, "Git checkout"),
            ):
                versioning.prepare_output_directory(sibling, "fixture")
            remove.assert_not_called()

    def test_output_cleanup_rejects_existing_parent_symlink_before_resolve(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            target = temp / "target"
            target.mkdir()
            linked_parent = temp / "linked-parent"
            linked_parent.symlink_to(target, target_is_directory=True)
            output = linked_parent / "output"
            output.mkdir()
            sentinel = output / "sentinel"
            sentinel.write_text("keep", encoding="utf-8")

            with self.assertRaisesRegex(SystemExit, "symbolic link"):
                versioning.prepare_output_directory(output, "fixture")

            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
            self.assertTrue(output.is_dir())

    def test_output_cleanup_rejects_symlinked_runner_temp_before_resolve(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            target = temp / "target"
            output = target / "output"
            output.mkdir(parents=True)
            sentinel = output / "sentinel"
            sentinel.write_text("keep", encoding="utf-8")
            runner_temp = temp / "runner-temp"
            runner_temp.symlink_to(target, target_is_directory=True)

            with (
                mock.patch.dict(
                    versioning.os.environ,
                    {"RUNNER_TEMP": str(runner_temp)},
                ),
                self.assertRaisesRegex(SystemExit, "symbolic link"),
            ):
                versioning.prepare_output_directory(
                    runner_temp / "output",
                    "fixture",
                )

            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
            self.assertTrue(output.is_dir())

    def test_output_cleanup_rejects_symlink_above_runner_temp_before_resolve(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            target = temp / "target"
            runner_temp_target = target / "runner-temp"
            output = runner_temp_target / "output"
            output.mkdir(parents=True)
            sentinel = output / "sentinel"
            sentinel.write_text("keep", encoding="utf-8")
            linked_parent = temp / "linked-parent"
            linked_parent.symlink_to(target, target_is_directory=True)
            runner_temp = linked_parent / "runner-temp"

            with (
                mock.patch.dict(
                    versioning.os.environ,
                    {"RUNNER_TEMP": str(runner_temp)},
                ),
                self.assertRaisesRegex(SystemExit, "symbolic link"),
            ):
                versioning.prepare_output_directory(
                    runner_temp / "output",
                    "fixture",
                )

            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
            self.assertTrue(output.is_dir())

    def test_output_cleanup_accepts_real_runner_temp_below_tmp_alias(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as temp_name:
            runner_temp = Path(temp_name) / "runner-temp"
            output = runner_temp / "output"
            output.mkdir(parents=True)
            (output / "stale").write_text("remove", encoding="utf-8")

            with mock.patch.dict(
                versioning.os.environ,
                {"RUNNER_TEMP": str(runner_temp)},
            ):
                self.assertEqual(
                    versioning.prepare_output_directory(output, "fixture"),
                    output.resolve(),
                )

            self.assertFalse(output.exists())

    def test_output_cleanup_rejects_registered_sibling_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            sibling = Path(temp_name) / "registered-sibling"
            sibling.mkdir()
            with (
                mock.patch.object(
                    versioning,
                    "registered_worktree_roots",
                    return_value=(versioning.ROOT.resolve(), sibling.resolve()),
                ),
                mock.patch.object(versioning.shutil, "rmtree") as remove,
                self.assertRaisesRegex(SystemExit, "Git checkout"),
            ):
                versioning.prepare_output_directory(sibling, "fixture")
            remove.assert_not_called()

    def test_output_cleanup_fails_closed_when_worktrees_cannot_be_enumerated(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            output = Path(temp_name) / "output"
            output.mkdir()
            with (
                mock.patch.object(
                    versioning,
                    "registered_worktree_roots",
                    side_effect=SystemExit("cannot enumerate protected Git worktrees"),
                ),
                mock.patch.object(versioning.shutil, "rmtree") as remove,
                self.assertRaisesRegex(SystemExit, "cannot enumerate"),
            ):
                versioning.prepare_output_directory(output, "fixture")
            remove.assert_not_called()


if __name__ == "__main__":
    unittest.main()
