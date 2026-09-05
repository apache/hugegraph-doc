#!/usr/bin/env python3

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0.

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
import urllib.parse


VALIDATOR_PATH = pathlib.Path(__file__).parents[1] / "dist/validate-site-output.py"
SPEC = importlib.util.spec_from_file_location("validate_site_output", VALIDATOR_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

BASE = urllib.parse.urlsplit("https://hugegraph-oink.staged.apache.org/")


def parse(fragment: str):
    parser = VALIDATOR.DocumentParser()
    parser.feed(fragment)
    return parser


class SiteOutputSecurityTest(unittest.TestCase):
    def test_docs_navigation_requires_five_localized_populated_groups(self) -> None:
        for language in ("en", "cn"):
            groups = [
                {
                    "title": title,
                    "kind": "external",
                    "url": f"https://example.org/{language}/docs/{index}/",
                    "children": [{"title": "child"}],
                }
                for index, title in enumerate(VALIDATOR.DOCS_NAV_GROUP_TITLES[language])
            ]
            nav = {"root": {"children": [{"id": "/docs/", "children": groups}]}}
            with self.subTest(language=language):
                self.assertEqual(
                    VALIDATOR.docs_navigation_errors(
                        nav, f"{language}/navigation.json", language
                    ),
                    [],
                )

        groups[0]["url"] = "https://example.org/docs/_nav/start/"
        self.assertIn(
            "private Docs navigation route leaked",
            "\n".join(VALIDATOR.docs_navigation_errors(nav, "navigation.json", "cn")),
        )

    def test_toc_accessibility_accepts_empty_and_populated_localized_navs(self) -> None:
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
            (
                "versions/1.7/cn/docs/config/index.html",
                '<nav id="TableOfContents" aria-label="目录"></nav>',
            ),
        )
        for page_name, fragment in fixtures:
            with self.subTest(page_name=page_name):
                self.assertEqual(
                    VALIDATOR.toc_accessibility_errors(parse(fragment), page_name), []
                )

        self.assertEqual(
            VALIDATOR.toc_accessibility_errors(
                parse("<main>No table of contents</main>"), "docs/short/index.html"
            ),
            [],
        )

    def test_toc_accessibility_rejects_missing_wrong_and_duplicate_labels(self) -> None:
        fixtures = (
            (
                '<nav id="TableOfContents"></nav>',
                "docs/config/index.html: TableOfContents nav must have exactly one "
                "localized aria-label 'Content', found []",
            ),
            (
                '<nav id="TableOfContents" aria-label="Content"></nav>',
                "cn/docs/config/index.html: TableOfContents nav must have exactly one "
                "localized aria-label '目录', found ['Content']",
            ),
            (
                '<nav id="TableOfContents" aria-label="Content" '
                'aria-label="Content"></nav>',
                "docs/config/index.html: TableOfContents nav must have exactly one "
                "localized aria-label 'Content', found ['Content', 'Content']",
            ),
        )
        for fragment, expected in fixtures:
            page_name = (
                "cn/docs/config/index.html"
                if "localized aria-label '目录'" in expected
                else "docs/config/index.html"
            )
            with self.subTest(fragment=fragment):
                self.assertEqual(
                    VALIDATOR.toc_accessibility_errors(parse(fragment), page_name),
                    [expected],
                )

    def test_error_documents_are_noindex_without_canonical_or_hreflang(self) -> None:
        parser = parse(
            '<meta name="robots" content="noindex, nofollow"><main>Not found</main>'
        )
        for page_name in (
            "404.html",
            "cn/404.html",
            "versions/1.7/404.html",
            "versions/1.7/cn/404.html",
        ):
            with self.subTest(page_name=page_name):
                self.assertEqual(
                    VALIDATOR.error_document_seo_errors(parser, page_name), []
                )

    def test_error_document_seo_rejects_indexing_and_url_claims(self) -> None:
        parser = parse(
            '<meta name="robots" content="index, follow">'
            '<link rel="canonical" href="https://example.com/404.html">'
            '<link rel="alternate" hreflang="en-US" '
            'href="https://example.com/404.html">'
        )
        self.assertEqual(
            VALIDATOR.error_document_seo_errors(parser, "versions/1.5/cn/404.html"),
            [
                "versions/1.5/cn/404.html: expected one robots "
                "noindex,nofollow directive, found ['index, follow']",
                "versions/1.5/cn/404.html: error document must not declare canonical",
                "versions/1.5/cn/404.html: error document must not declare hreflang",
            ],
        )

    def test_error_document_paths_follow_all_manifest_versions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = pathlib.Path(temp_name)
            manifest = {
                "versions": [
                    {"id": "latest", "publishPath": ""},
                    {"id": "1.7", "publishPath": "versions/1.7"},
                    {"id": "1.5", "publishPath": "versions/1.5"},
                    {"id": "1.3", "publishPath": "versions/1.3"},
                    {"id": "1.0", "publishPath": "versions/1.0"},
                ]
            }
            metadata = root / "build-metadata"
            metadata.mkdir()
            (metadata / "versions.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )

            self.assertEqual(
                VALIDATOR.error_document_paths(root),
                {
                    "404.html",
                    "cn/404.html",
                    "versions/1.7/404.html",
                    "versions/1.7/cn/404.html",
                    "versions/1.5/404.html",
                    "versions/1.5/cn/404.html",
                    "versions/1.3/404.html",
                    "versions/1.3/cn/404.html",
                    "versions/1.0/404.html",
                    "versions/1.0/cn/404.html",
                },
            )

    def test_all_modes_reject_old_version_error_page_seo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = pathlib.Path(temp_name)
            manifest = {
                "versions": [
                    {"id": "latest", "publishPath": ""},
                    {"id": "1.3", "publishPath": "versions/1.3"},
                    {"id": "1.0", "publishPath": "versions/1.0"},
                ]
            }
            metadata = root / "build-metadata"
            metadata.mkdir()
            (metadata / "versions.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            unsafe = (
                '<meta name="robots" content="index, follow">'
                '<link rel="canonical" href="https://example.com/404.html">'
                '<link rel="alternate" hreflang="en-US" '
                'href="https://example.com/404.html">'
            )
            for version in ("1.3", "1.0"):
                for language in ("", "cn/"):
                    page = root / f"versions/{version}/{language}404.html"
                    page.parent.mkdir(parents=True, exist_ok=True)
                    page.write_text(unsafe, encoding="utf-8")

            for extra_args in (["--security-only"], []):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(VALIDATOR_PATH),
                        str(root),
                        "https://hugegraph.apache.org/",
                        *extra_args,
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                for version in ("1.3", "1.0"):
                    for language in ("", "cn/"):
                        page_name = f"versions/{version}/{language}404.html"
                        with self.subTest(mode=extra_args, page_name=page_name):
                            self.assertIn(
                                f"{page_name}: expected one robots noindex,nofollow",
                                result.stdout,
                            )
                            self.assertIn(
                                f"{page_name}: error document must not declare canonical",
                                result.stdout,
                            )
                            self.assertIn(
                                f"{page_name}: error document must not declare hreflang",
                                result.stdout,
                            )

    def test_nested_content_404_is_not_an_error_document_exception(self) -> None:
        parser = parse(
            '<meta name="robots" content="index, follow">'
            '<link rel="canonical" href="https://example.com/docs/404.html">'
        )
        self.assertNotIn("docs/404.html", VALIDATOR.ERROR_DOCUMENT_PATHS)
        self.assertEqual(
            VALIDATOR.error_document_seo_errors(parser, "docs/404.html"), []
        )

    def test_security_only_mode_skips_aggregate_url_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = pathlib.Path(temp_name)
            (root / "index.html").write_text(
                '<main><a href="/versions/1.7/docs/">1.7</a></main>'
                '<nav id="TableOfContents"></nav>',
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR_PATH),
                    str(root),
                    "https://hugegraph.apache.org/versions/1.5/",
                    "--security-only",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            full_result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR_PATH),
                    str(root),
                    "https://hugegraph.apache.org/versions/1.5/",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(full_result.returncode, 1)
            self.assertIn(
                "TableOfContents nav must have exactly one localized aria-label",
                full_result.stdout,
            )

            (root / "index.html").write_text(
                "<main><script>alert(1)</script></main>", encoding="utf-8"
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR_PATH),
                    str(root),
                    "https://hugegraph.apache.org/versions/1.5/",
                    "--security-only",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("authored <script>", result.stdout)

            (root / "index.html").write_text("<main>safe</main>", encoding="utf-8")
            (root / "site.css").write_text(
                ".hero{background:url(https://evil.example/hero.png)}",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR_PATH),
                    str(root),
                    "https://hugegraph.apache.org/versions/1.5/",
                    "--security-only",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("external CSS resource is forbidden", result.stdout)

    def test_shell_scripts_outside_content_are_allowed(self) -> None:
        parser = parse(
            '<head><script src="/shell.js"></script></head>'
            "<main><p>Documentation</p></main>"
            '<script id="td-action-manifest" type="application/json">{}</script>'
        )
        self.assertEqual(parser.authored_violations, [])

    def test_active_markup_and_event_handlers_inside_content_are_rejected(self) -> None:
        parser = parse(
            '<main onclick="run()"><script>alert(1)</script>'
            '<iframe src="/frame"></iframe><object data="/object"></object>'
            '<embed src="/embed"><article><img src="/ok.png" onerror="run()">'
            "</article></main>"
        )
        self.assertEqual(
            parser.authored_violations,
            [
                "authored onclick event attribute on <main>",
                "authored <script>",
                "authored <iframe>",
                "authored <object>",
                "authored <embed>",
                "authored onerror event attribute on <img>",
            ],
        )

    def test_duplicate_attributes_are_rejected_case_insensitively(self) -> None:
        parser = parse(
            '<img src="/safe.png" SRC="https://evil.example/image.png">'
            '<svg><use xlink:href="#safe" XLINK:HREF="https://evil.example/x">'
            "</use></svg>"
        )
        self.assertEqual(
            parser.authored_violations,
            [
                "duplicate src attribute on <img>",
                "duplicate xlink:href attribute on <use>",
            ],
        )
        errors = VALIDATOR.document_security_errors(parser, "index.html", BASE)
        self.assertIn(
            "index.html: unsafe content markup: duplicate src attribute on <img>",
            errors,
        )
        self.assertIn(
            "index.html: unsafe content markup: duplicate xlink:href attribute "
            "on <use>",
            errors,
        )

    def test_exact_oink_diagram_source_is_allowed_inside_content(self) -> None:
        parser = parse(
            '<main><script type="application/json" data-td-diagram-source>'
            '{"code":"graph TD; A-->B"}</script></main>'
        )
        self.assertEqual(parser.authored_violations, [])

    def test_other_json_and_diagram_marked_scripts_are_rejected(self) -> None:
        rejected = [
            '<script type="application/json">{}</script>',
            "<script data-td-diagram-source>{}</script>",
            '<script type="text/javascript" data-td-diagram-source></script>',
            '<script type="application/json" data-td-diagram-source '
            'src="/payload.json"></script>',
            '<script type="application/json" data-td-diagram-source '
            'data-extra="true"></script>',
        ]
        for script in rejected:
            with self.subTest(script=script):
                parser = parse(f"<article>{script}</article>")
                self.assertIn("authored <script>", parser.authored_violations)

    def test_http_resources_are_distinct_from_ordinary_links(self) -> None:
        parser = parse(
            '<a href="http://example.com/docs">docs</a>'
            '<img src="http://example.com/image.png" '
            'srcset="/small.png 1x, http://example.com/large.png 2x">'
            '<link rel="stylesheet" href="http://example.com/site.css">'
        )
        insecure = [
            url
            for _tag, _attribute, url in parser.resources
            if urllib.parse.urlsplit(url).scheme == "http"
        ]
        self.assertEqual(
            insecure,
            [
                "http://example.com/image.png",
                "http://example.com/large.png",
                "http://example.com/site.css",
            ],
        )

    def test_authorityless_and_ambiguous_http_links_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = pathlib.Path(temp_name)
            docs = root / "docs/introduction"
            docs.mkdir(parents=True)
            (docs / "index.html").write_text("target", encoding="utf-8")
            (root / "index.html").write_text(
                (
                    '<a href="https:///docs/introduction/">triple</a>'
                    '<a href="https:////docs/introduction/">quad</a>'
                    '<a href="http:docs/introduction/">opaque</a>'
                    '<a href="/docs/introduction/\t">control</a>'
                    '<a href="/docs\\introduction/">backslash</a>'
                    '<img srcset="https:///docs/introduction/ 1x">'
                    '<object data="https:///docs/introduction/"></object>'
                    '<video poster="https:///docs/introduction/"></video>'
                    '<style>.hero{background:url(https:///docs/introduction/)}</style>'
                    '<a href="javascript:alert(1)">active link</a>'
                    '<script src="javascript:alert(1)"></script>'
                    '<iframe src="javascript:alert(1)"></iframe>'
                    '<object data="javascript:alert(1)"></object>'
                    '<a href="mailto:dev@example.com">allowed contact</a>'
                ),
                encoding="utf-8",
            )
            (root / "boundary.html").write_text(
                (
                    '<form action="https://evil.example/collect">'
                    '<button formaction="https://evil.example/button">go</button>'
                    '<input formaction="https://evil.example/input">'
                    "</form>"
                    '<a href="/docs/" ping="https://evil.example/ping">ping</a>'
                    '<area href="/docs/" ping="https://evil.example/ping">'
                    '<base href="https://evil.example/">'
                ),
                encoding="utf-8",
            )
            (root / "site.css").write_text(
                ".hero{background:url(https:///docs/introduction/)}",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR_PATH),
                    str(root),
                    "https://hugegraph.apache.org/",
                    "--security-only",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("HTTP(S) URL has no authority", result.stdout)
            self.assertGreaterEqual(
                result.stdout.count("HTTP(S) URL has no authority"),
                6,
                result.stdout,
            )
            self.assertIn("unsafe whitespace/control URL", result.stdout)
            self.assertIn("unsafe backslash URL", result.stdout)
            self.assertIn("forbidden URL scheme", result.stdout)
            self.assertIn("site.css", result.stdout)

    def test_security_only_rejects_unreviewed_request_attributes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = pathlib.Path(temp_name)
            (root / "index.html").write_text(
                (
                    '<form action="javascript:alert(1)">'
                    '<button formaction="javascript:alert(1)">go</button>'
                    '<input formaction="https://evil.example/submit">'
                    "</form>"
                    '<a href="/docs/" ping="https://evil.example/ping">ping</a>'
                    '<area href="/docs/" ping="https://evil.example/ping">'
                    '<base href="https://evil.example/">'
                    '<svg><use href="javascript:alert(1)"></use></svg>'
                ),
                encoding="utf-8",
            )
            (root / "external-boundary.html").write_text(
                (
                    '<form action="https://evil.example/collect">'
                    '<button formaction="https://evil.example/button">go</button>'
                    '<input formaction="https://evil.example/input">'
                    "</form>"
                    '<a href="/docs/" ping="https://evil.example/ping">ping</a>'
                    '<area href="/docs/" ping="https://evil.example/ping">'
                    '<base href="https://evil.example/">'
                    '<link rel="prefetch" href="https://evil.example/payload">'
                    '<link rel="prerender" href="https://evil.example/page">'
                    '<link rel="preconnect" href="https://evil.example/">'
                    '<link rel="dns-prefetch" href="https://evil.example/">'
                    '<link rel="preload" as="image" '
                    'imagesrcset="https://evil.example/preload.png 1x">'
                    '<svg><use xlink:href="https://evil.example/icon.svg"></use>'
                    '<image xlink:href="https://evil.example/image.svg"></image></svg>'
                    '<img src="/local.png" '
                    'attributionsrc="https://evil.example/attribute">'
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR_PATH),
                    str(root),
                    "https://hugegraph.apache.org/",
                    "--security-only",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("forbidden ping attribute", result.stdout)
            self.assertIn("forbidden base[href]", result.stdout)
            self.assertIn("forbidden URL scheme in form[action]", result.stdout)
            self.assertIn("forbidden URL scheme in button[formaction]", result.stdout)
            self.assertIn("external active resource", result.stdout)
            self.assertIn(
                "external active resource is forbidden <link> href: "
                "https://evil.example/payload",
                result.stdout,
            )
            self.assertIn(
                "external active resource is forbidden <link> href: "
                "https://evil.example/page",
                result.stdout,
            )
            self.assertIn(
                "external active resource is forbidden <use> xlink:href",
                result.stdout,
            )
            self.assertIn(
                "external active resource is forbidden <link> imagesrcset",
                result.stdout,
            )
            self.assertIn("forbidden attributionsrc attribute", result.stdout)
            self.assertIn("forbidden URL scheme in use[href]", result.stdout)

    def test_runtime_url_attributes_enter_security_and_target_validation(self) -> None:
        fragment = (
            '<main data-td-index-src="/missing-index.json" '
            'data-td-url="/missing-runtime/" '
            'data-td-action-url="/missing-action/" '
            'data-td-image-zoom="https://images.example.com/zoom.png"></main>'
        )
        parser = parse(fragment)
        for attribute, url in (
            ("data-td-index-src", "/missing-index.json"),
            ("data-td-url", "/missing-runtime/"),
            ("data-td-action-url", "/missing-action/"),
            ("data-td-image-zoom", "https://images.example.com/zoom.png"),
        ):
            self.assertIn((attribute, url), parser.urls)
        errors = VALIDATOR.document_security_errors(parser, "index.html", BASE)
        self.assertIn(
            "index.html: image URL is outside ASF CSP <main> "
            "data-td-image-zoom: https://images.example.com/zoom.png",
            errors,
        )

        with tempfile.TemporaryDirectory() as temp_name:
            root = pathlib.Path(temp_name)
            (root / "index.html").write_text(fragment, encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR_PATH),
                    str(root),
                    "https://hugegraph.apache.org/",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "broken internal data-td-index-src /missing-index.json",
                result.stdout,
            )
            self.assertIn(
                "broken internal data-td-url /missing-runtime/",
                result.stdout,
            )
            self.assertIn(
                "broken internal data-td-action-url /missing-action/",
                result.stdout,
            )

    def test_security_only_rejects_data_resource_schemes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = pathlib.Path(temp_name)
            data_image = "data:image/png;base64,AAAA"
            (root / "index.html").write_text(
                (
                    f'<img src="{data_image}" srcset="{data_image} 1x">'
                    f'<picture><source srcset="{data_image} 1x"></picture>'
                    f'<video poster="{data_image}"></video>'
                    f'<style>.hero{{background:url({data_image})}}</style>'
                ),
                encoding="utf-8",
            )
            (root / "site.css").write_text(
                f".hero{{background:url({data_image})}}",
                encoding="utf-8",
            )

            passive = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR_PATH),
                    str(root),
                    "https://hugegraph.apache.org/",
                    "--security-only",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(passive.returncode, 1)
            self.assertIn("forbidden URL scheme in img[src]", passive.stdout)
            self.assertIn("forbidden URL scheme in inline CSS", passive.stdout)
            self.assertIn("forbidden URL scheme in CSS resource", passive.stdout)

            (root / "active.html").write_text(
                f'<script src="{data_image}"></script>',
                encoding="utf-8",
            )
            rejected = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR_PATH),
                    str(root),
                    "https://hugegraph.apache.org/",
                    "--security-only",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(rejected.returncode, 1)
            self.assertIn("forbidden URL scheme in script[src]", rejected.stdout)

    def test_css_http_resources_are_detected(self) -> None:
        parser = parse(
            '<style>@import "http://example.com/base.css"; '
            ".hero { background: url(http://example.com/hero.png) }</style>"
            "<p style=\"background-image:url('http://example.com/card.png')\">x</p>"
        )
        self.assertEqual(
            parser.inline_css_http_resources,
            [
                "http://example.com/base.css",
                "http://example.com/hero.png",
                "http://example.com/card.png",
            ],
        )

    def test_css_external_resources_are_detected(self) -> None:
        source = (
            '@import "https://evil.example/base.css";'
            ".hero { background: url(//evil.example/hero.png) }"
            ".self { background: url(/img/self.png) }"
        )
        self.assertEqual(
            VALIDATOR.css_external_resources(source, BASE),
            [
                "https://evil.example/base.css",
                "//evil.example/hero.png",
            ],
        )

    def test_css_tokenizer_covers_escaped_and_image_set_resources(self) -> None:
        source = (
            '@\\69mport "https://evil.example/import with space.css";'
            ".quoted { background: url('https://evil.example/image with space.png') }"
            ".escaped { background: u\\72l(h\\74tps://evil.example/escaped.png) }"
            ".set { background-image: image-set("
            '"https://evil.example/one.png" 1x, '
            "url(https://evil.example/two.png) 2x) }"
            ".webkit { background-image: -webkit-image-set("
            '"https://evil.example/three.png" 1x) }'
        )
        self.assertEqual(
            VALIDATOR.css_resource_urls(source),
            [
                "https://evil.example/import with space.css",
                "https://evil.example/image with space.png",
                "https://evil.example/escaped.png",
                "https://evil.example/one.png",
                "https://evil.example/two.png",
                "https://evil.example/three.png",
            ],
        )

    def test_css_request_surfaces_share_the_same_security_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = pathlib.Path(temp_name)
            escaped = "h\\74tps://evil.example/request.png"
            (root / "index.html").write_text(
                (
                    f'<div style="background:image-set(&quot;{escaped}&quot; 1x)">'
                    "</div>"
                    f"<style>.hero{{background:url('{escaped}')}}</style>"
                ),
                encoding="utf-8",
            )
            (root / "site.css").write_text(
                f".hero{{background:-webkit-image-set(\"{escaped}\" 1x)}}",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR_PATH),
                    str(root),
                    "https://hugegraph.apache.org/",
                    "--security-only",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertGreaterEqual(
                result.stdout.count("external CSS resource is forbidden"),
                3,
                result.stdout,
            )

    def test_css_internal_resources_resolve_from_stylesheet_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = pathlib.Path(temp_name)
            (root / "index.html").write_text("<main>safe</main>", encoding="utf-8")
            (root / "scss").mkdir()
            (root / "img").mkdir()
            (root / "img/present.svg").write_text("<svg/>", encoding="utf-8")
            (root / "scss/site.css").write_text(
                (
                    '.present{background:url("../img/present.svg")}'
                    '.scoped{background:url("https://hugegraph.apache.org/'
                    'versions/1.7/img/present.svg")}'
                    '.missing{background:url("../img/missing.svg")}'
                    '@import "./missing.css";'
                    '.escape{background:url("../../escape.svg")}'
                    '.fragment{filter:url("#local-filter")}'
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR_PATH),
                    str(root),
                    "https://hugegraph.apache.org/versions/1.7/",
                    "--security-only",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertNotIn("present.svg", result.stdout)
            self.assertIn(
                "broken internal CSS resource ../img/missing.svg -> img/missing.svg",
                result.stdout,
            )
            self.assertIn(
                "broken internal CSS resource ./missing.css -> scss/missing.css",
                result.stdout,
            )
            self.assertIn(
                "unsafe internal CSS resource ../../escape.svg: "
                "escapes output directory",
                result.stdout,
            )
            self.assertNotIn("local-filter", result.stdout)

    def test_parser_covers_legacy_and_svg_request_surfaces(self) -> None:
        parser = parse(
            '<iframe srcdoc="<script>run()</script>"></iframe>'
            '<frame src="https://evil.example/frame">'
            '<body background="https://images.example.com/body.png">'
            '<table background="/table.png"><tr>'
            '<th background="/head.png">h</th>'
            '<td background="/cell.png">c</td></tr></table>'
            '<svg>'
            '<a xlink:href="https://example.com/docs">docs</a>'
            '<image xlink:href="https://www.apache.org/image.svg"></image>'
            '<feImage href="https://www.apache.org/filter.svg"></feImage>'
            '<mpath xlink:href="https://evil.example/path.svg#p"></mpath>'
            '<pattern href="https://evil.example/pattern.svg#p"></pattern>'
            '<path fill="url(https://evil.example/paint.svg#gradient)"></path>'
            "</svg>"
        )
        self.assertIn("forbidden iframe[srcdoc]", parser.authored_violations)
        self.assertIn(
            ("a", "xlink:href", "https://example.com/docs"),
            parser.navigation_urls,
        )
        self.assertIn(
            ("mpath", "xlink:href", "https://evil.example/path.svg#p"),
            parser.resources,
        )
        self.assertIn(
            ("pattern", "href", "https://evil.example/pattern.svg#p"),
            parser.resources,
        )
        self.assertIn(
            ("image", "xlink:href", "https://www.apache.org/image.svg"),
            parser.image_urls,
        )
        self.assertIn(
            ("feimage", "href", "https://www.apache.org/filter.svg"),
            parser.image_urls,
        )
        self.assertIn(
            "https://evil.example/paint.svg#gradient",
            [
                url
                for source in parser.inline_css_sources
                for url in VALIDATOR.css_resource_urls(source)
            ],
        )
        self.assertIn(
            "external active resource is forbidden <frame> src",
            "\n".join(
                VALIDATOR.document_security_errors(parser, "index.html", BASE)
            ),
        )

    def test_media_sources_are_not_treated_as_csp_images(self) -> None:
        parser = parse(
            '<picture><source srcset="https://www.apache.org/image.webp 1x">'
            '<img src="https://www.apache.org/image.png"></picture>'
            '<video><source src="https://www.apache.org/video.mp4" '
            'srcset="https://www.apache.org/video-hd.mp4 2x"></video>'
            '<audio><source src="https://www.apache.org/audio.mp3"></audio>'
        )
        errors = VALIDATOR.document_security_errors(parser, "index.html", BASE)
        self.assertEqual(
            sum("external active resource" in error for error in errors),
            3,
            errors,
        )
        self.assertFalse(
            any("image.webp" in error or "image.png" in error for error in errors),
            errors,
        )

    def test_authored_content_markers_survive_premature_container_closures(
        self,
    ) -> None:
        parser = parse(
            '<main><article><template data-hg-authored-content="start"></template>'
            '</article></main><script src="/escaped.js"></script>'
            '<template data-hg-authored-content="end"></template>'
        )
        self.assertIn("authored <script>", parser.authored_violations)

        spoofed = parse(
            '<template data-hg-authored-content="start"></template>'
            '<template data-hg-authored-content="end"></template>'
            '<script src="/escaped.js"></script>'
            '<template data-hg-authored-content="end"></template>'
        )
        self.assertIn(
            "unexpected authored-content end marker",
            spoofed.authored_violations,
        )
        self.assertTrue(
            VALIDATOR.document_security_errors(spoofed, "index.html", BASE)
        )

    def test_link_rel_is_fail_closed_for_request_capable_and_unknown_values(self) -> None:
        parser = parse(
            '<link rel="canonical" href="https://hugegraph-oink.staged.apache.org/">'
            '<link rel="alternate" hreflang="zh-CN" '
            'href="https://hugegraph-oink.staged.apache.org/cn/">'
            '<link rel="mask-icon" href="https://evil.example/mask.svg">'
            '<link rel="apple-touch-startup-image" '
            'href="https://evil.example/start.png">'
            '<link rel="future-browser-fetch" href="https://evil.example/future">'
        )
        errors = VALIDATOR.document_security_errors(parser, "index.html", BASE)
        self.assertEqual(len(errors), 3, errors)
        self.assertTrue(all("external active resource" in error for error in errors))

    def test_srcset_and_imagesrcset_candidates_are_internal_targets(self) -> None:
        fragment = (
            '<img srcset="/present.png 1x, /missing.png 2x">'
            '<link rel="preload" as="image" '
            'imagesrcset="/present-link.png 1x, /missing-link.png 2x">'
        )
        parser = parse(fragment)
        self.assertIn(("srcset", "/missing.png"), parser.urls)
        self.assertIn(("imagesrcset", "/missing-link.png"), parser.urls)
        with tempfile.TemporaryDirectory() as temp_name:
            root = pathlib.Path(temp_name)
            (root / "index.html").write_text(fragment, encoding="utf-8")
            (root / "present.png").write_bytes(b"present")
            (root / "present-link.png").write_bytes(b"present")
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR_PATH),
                    str(root),
                    "https://hugegraph.apache.org/",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "broken internal srcset /missing.png -> missing.png",
                result.stdout,
            )
            self.assertIn(
                "broken internal imagesrcset /missing-link.png -> missing-link.png",
                result.stdout,
            )

    def test_asf_csp_image_sources_are_allowed(self) -> None:
        allowed = [
            "/img/local.svg",
            "https://hugegraph-oink.staged.apache.org/img/self.svg",
            "https://apache.org/img/foundation.svg",
            "https://www.apache.org/img/logo.svg",
            "https://community.apache.org/img/community.svg",
            "https://www.apachecon.com/img/event.svg",
            "https://www.communityovercode.org/img/event.svg",
            "https://c2.scarf.sh/a.png",
        ]
        for url in allowed:
            with self.subTest(url=url):
                self.assertTrue(VALIDATOR.image_url_allowed_by_asf_csp(url, BASE))

    def test_non_csp_external_image_sources_are_rejected(self) -> None:
        rejected = [
            "http://www.apache.org/img/logo.svg",
            "https://images.example.com/hero.png",
            "https://apache.org.evil.example/hero.png",
            "https://www.apache.org:8443/img/logo.svg",
            "https://scarf.sh/a.png",
            "//images.example.com/hero.png",
        ]
        for url in rejected:
            with self.subTest(url=url):
                self.assertFalse(VALIDATOR.image_url_allowed_by_asf_csp(url, BASE))

    def test_external_active_resources_are_rejected(self) -> None:
        parser = parse(
            '<script src="https://evil.example/app.js"></script>'
            '<link rel="stylesheet" href="https://evil.example/app.css">'
            '<img src="https://www.apache.org/img/logo.svg">'
        )
        self.assertEqual(
            VALIDATOR.document_security_errors(parser, "index.html", BASE),
            [
                "index.html: external active resource is forbidden <script> src: "
                "https://evil.example/app.js",
                "index.html: external active resource is forbidden <link> href: "
                "https://evil.example/app.css",
            ],
        )

    def test_srcset_candidates_are_all_checked(self) -> None:
        parser = parse(
            '<picture><source srcset="/small.webp 1x, '
            'https://images.example.com/large.webp 2x">'
            '<img src="/fallback.png" srcset="data:image/png;base64,AAAA 1x, '
            'https://www.apache.org/img/large.png 2x"></picture>'
        )
        self.assertEqual(
            parser.image_urls,
            [
                ("source", "srcset", "/small.webp"),
                ("source", "srcset", "https://images.example.com/large.webp"),
                ("img", "src", "/fallback.png"),
                ("img", "srcset", "data:image/png;base64,AAAA"),
                ("img", "srcset", "https://www.apache.org/img/large.png"),
            ],
        )

    def test_srcset_candidates_without_spaces_are_all_checked(self) -> None:
        parser = parse(
            '<source srcset="https://www.apache.org/a.png,http://evil.example/b.png">'
        )
        self.assertEqual(
            parser.image_urls,
            [
                ("source", "srcset", "https://www.apache.org/a.png"),
                ("source", "srcset", "http://evil.example/b.png"),
            ],
        )
        self.assertEqual(
            VALIDATOR.document_security_errors(parser, "index.html", BASE),
            [
                "index.html: mixed-content <source> srcset: http://evil.example/b.png",
            ],
        )

    def test_security_decision_accepts_shell_and_asf_images(self) -> None:
        parser = parse(
            '<script src="/shell.js"></script><main><img '
            'src="https://www.apache.org/img/logo.svg"></main>'
        )
        self.assertEqual(
            VALIDATOR.document_security_errors(parser, "index.html", BASE), []
        )

    def test_security_decision_reports_each_failure_class(self) -> None:
        parser = parse(
            '<link rel="stylesheet" href="http://example.com/site.css">'
            '<main onload="run()" style="background:url(http://example.com/bg.png)">'
            '<iframe src="/frame"></iframe>'
            '<source srcset="/small.png 1x, http://example.com/large.png 2x">'
            '<img src="https://images.example.com/hero.png"></main>'
        )
        self.assertEqual(
            VALIDATOR.document_security_errors(parser, "docs/index.html", BASE),
            [
                "docs/index.html: unsafe content markup: authored onload event "
                "attribute on <main>",
                "docs/index.html: unsafe content markup: authored <iframe>",
                "docs/index.html: mixed-content CSS resource: "
                "http://example.com/bg.png",
                "docs/index.html: mixed-content <link> href: "
                "http://example.com/site.css",
                "docs/index.html: mixed-content <source> srcset: "
                "http://example.com/large.png",
                "docs/index.html: image URL is outside ASF CSP <img> src: "
                "https://images.example.com/hero.png",
            ],
        )


if __name__ == "__main__":
    unittest.main()
