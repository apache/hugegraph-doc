#!/usr/bin/env python3

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0.

from __future__ import annotations

import importlib.util
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
