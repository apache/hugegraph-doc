#!/usr/bin/env python3

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0.

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import shutil
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

HUGO_BIN = os.environ.get("HUGO_BIN", "hugo")
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

    def test_security_workers_preserve_cli_results(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = pathlib.Path(temp_name)

            def run(*options: str) -> subprocess.CompletedProcess:
                return subprocess.run(
                    [sys.executable, str(VALIDATOR_PATH), str(root),
                     "https://hugegraph.apache.org/", *options],
                    check=False, capture_output=True,
                )

            def assert_same_results(expected_code: int) -> bytes:
                default = run("--security-only")
                self.assertEqual(default.returncode, expected_code, default.stderr)
                for workers in ("1", "2"):
                    result = run("--security-only", "--workers", workers)
                    self.assertEqual(
                        (result.returncode, result.stdout, result.stderr),
                        (default.returncode, default.stdout, default.stderr),
                    )
                return default.stdout

            (root / "index.html").write_text("<main>safe</main>", encoding="utf-8")
            (root / "404.html").write_text(
                '<meta name="robots" content="noindex, nofollow">', encoding="utf-8"
            )
            (root / "site.css").write_text("body{color:black}", encoding="utf-8")
            assert_same_results(0)

            (root / "a-invalid-url.html").write_text(
                '<main><a href="https://[invalid">bad</a>'
                '<script>shape error must short-circuit</script></main>',
                encoding="utf-8",
            )
            (root / "b-invalid-utf8.html").write_bytes(b"<main>\xff</main>")
            (root / "c-unsafe.html").write_text(
                "<main><script>alert(1)</script></main>", encoding="utf-8"
            )
            (root / "404.html").write_text(
                '<meta name="robots" content="index, follow">', encoding="utf-8"
            )
            (root / "site.css").write_text(
                'body{background:url("missing.png")}', encoding="utf-8"
            )
            output = assert_same_results(1)
            for diagnostic in (
                b"malformed URL", b"cannot parse b-invalid-utf8.html",
                b"c-unsafe.html: unsafe content markup: authored <script>",
                b"404.html: expected one robots noindex,nofollow",
                b"broken internal CSS resource missing.png",
            ):
                self.assertIn(diagnostic, output)
            self.assertNotIn(b"a-invalid-url.html: unsafe content markup", output)

            # The option must not alter the normal full-contract validation path.
            normal = run()
            self.assertEqual(normal.returncode, 1)
            self.assertIn(b"missing required output", normal.stdout)
            for workers in ("1", "2"):
                result = run("--workers", workers)
                self.assertEqual(
                    (result.returncode, result.stdout, result.stderr),
                    (normal.returncode, normal.stdout, normal.stderr),
                )

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

    def test_exact_oink_chart_and_terminal_json_carriers_are_allowed(self) -> None:
        # Shapes emitted by tagged OINK 1.2 render-codeblock-echarts.html and
        # _shortcodes/asciinema.html, including their native wrapper markup.
        fragments = [
            '<div id="td-echarts-placeholder-f0" class="td-echarts td-max-width-on-larger-screens" data-td-echarts>'
            '<div data-td-echarts-canvas style="height:360px"></div>'
            '<script type="application/json" data-td-echarts-options>'
            '{"series":[{"type":"bar","data":[1,2]}]}</script></div>',
            '<div id="td-asciinema-placeholder-0" class="td-asciinema td-max-width-on-larger-screens" '
            'data-td-asciinema data-td-timer-label="Playback time">'
            '<div class="td-asciinema__chrome"><span class="td-asciinema__title" dir="auto">Demo</span></div>'
            '<div data-td-asciinema-player></div>'
            '<script type="application/json" data-td-asciinema-config>'
            '{"src":"/recording.cast","theme":"auto","options":{"autoPlay":false,"speed":1}}</script></div>',
        ]
        for fragment in fragments:
            with self.subTest(fragment=fragment):
                parser = parse(f"<main><article>{fragment}</article></main>")
                self.assertEqual(parser.authored_violations, [])
                self.assertEqual(VALIDATOR.document_security_errors(parser, "index.html", BASE), [])

    def test_component_json_carrier_disguises_and_breakouts_are_rejected(self) -> None:
        for marker in ("data-td-diagram-source", "data-td-echarts-options", "data-td-asciinema-config"):
            variants = [
                f'<script {marker}>alert(1)</script>',
                f'<script type="module" {marker}>alert(1)</script>',
                f'<script type="text/javascript" {marker}>alert(1)</script>',
                f'<script type="application/json" {marker}="true">{{}}</script>',
                f'<script type="application/json" {marker} src="/evil.js">{{}}</script>',
                f'<script type="application/json" {marker} onload="evil()">{{}}</script>',
                f'<script type="application/json" {marker} class="disguise">{{}}</script>',
                f'<script type="application/json" {marker} data-extra="true">{{}}</script>',
                f'<script type="application/json" {marker} data-td-fake-config>{{}}</script>',
                f'<script type="application/json" {marker}>{{"text":"</script><script>alert(1)</script>"}}',
                '<script type="application/json" data-td-fake-config>{}</script>',
            ]
            for variant in variants:
                with self.subTest(marker=marker, variant=variant):
                    parser = parse(f"<article>{variant}</article>")
                    self.assertIn("authored <script>", parser.authored_violations)
            duplicate = f'<script type="application/json" {marker} {marker}>{{}}</script>'
            parser = parse(f"<article>{duplicate}</article>")
            self.assertTrue(any("duplicate" in violation for violation in parser.authored_violations))

    def test_asciinema_payload_source_uses_active_resource_boundary(self) -> None:
        for source in ("https://evil.example/x.cast", "http://evil.example/x.cast", "//evil.example/x.cast",
                       "javascript:evil()", "data:text/plain,cast", "\\\\evil.example\\x.cast"):
            with self.subTest(source=source):
                parser = parse('<article><script type="application/json" data-td-asciinema-config>' +
                               json.dumps({"src": source, "theme": "auto", "options": {"autoPlay": False}}) + "</script></article>")
                errors = VALIDATOR.document_security_errors(parser, "index.html", BASE) + \
                         VALIDATOR.document_url_shape_errors(parser, "index.html")
                self.assertTrue(errors)
        parser = parse('<article><script type="application/json" data-td-asciinema-config>' +
                       json.dumps({"src": "/recording.cast", "theme": "auto", "options": {"autoPlay": False}}) + "</script></article>")
        self.assertEqual(VALIDATOR.document_security_errors(parser, "index.html", BASE), [])
        self.assertEqual(VALIDATOR.document_url_shape_errors(parser, "index.html"), [])

    def test_echarts_payload_images_and_formatter_html_are_validated(self) -> None:
        payloads = [
            {"series": [{"symbol": "image://https://evil.example/symbol.png"}]},
            {"graphic": {"style": {"image": "https://evil.example/image.png"}}},
            {"textStyle": {"rich": {"a": {"backgroundColor": {"image": "//evil.example/image.png"}}}}},
            {"tooltip": {"formatter": '<img src="https://evil.example/x.png">'}},
            {"tooltip": {"formatter": '<img src="/ok.png" onerror="evil()">'}},
            {"tooltip": {"formatter": '</article><script>evil()</script>'}},
            {"tooltip": {"formatter": '<template data-hg-authored-content="end"></template>'
                                       '<script>evil()</script><template data-hg-authored-content="start"></template>'}},
            {"tooltip": {"formatter": '<iframe src="/frame"></iframe>'}},
            {"tooltip": {"formatter": '<a href="javascript:evil()">link</a>'}},
            {"tooltip": {"formatter": '<div style="background:url(https://evil.example/x)">x</div>'}},
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                # Hugo's jsonify escapes HTML characters in the script body;
                # exercise runtime formatter markup after JSON decoding.
                encoded = json.dumps(payload).replace("<", "\\u003c").replace(">", "\\u003e")
                parser = parse('<article><script type="application/json" data-td-echarts-options>' +
                               encoded + "</script></article>")
                errors = VALIDATOR.document_security_errors(parser, "index.html", BASE) + \
                         VALIDATOR.document_url_shape_errors(parser, "index.html")
                self.assertTrue(errors)
        for payload in ({"tooltip": {"formatter": "<b>{b}</b>: {c}"}},
                        {"tooltip": {"trigger": "axis"}, "series": [{"type": "bar", "data": [1, 2]}]},
                        {"series": [{"symbol": "image:///local.png"}]}):
            parser = parse('<article><script type="application/json" data-td-echarts-options>' +
                           json.dumps(payload) + "</script></article>")
            self.assertEqual(VALIDATOR.document_security_errors(parser, "index.html", BASE), [])

    def test_reserved_component_markers_require_exact_carrier_on_every_element(self) -> None:
        for marker in VALIDATOR.OINK_CONFIG_MARKERS:
            for tag in ("pre", "div", "template", "span"):
                for attributes in (marker, f'{marker}="true"', f'{marker} data-extra="true"'):
                    with self.subTest(marker=marker, tag=tag, attributes=attributes):
                        parser = parse(f'<{tag} {attributes}>{{"src":"https://evil.example/cast"}}</{tag}>')
                        self.assertTrue(VALIDATOR.document_security_errors(parser, "index.html", BASE))

    def test_echarts_runtime_sink_paths_and_inert_dataset_columns(self) -> None:
        unsafe = [
            {"tooltip": {"extraCssText": "background:url(https://evil.example/a.png)"}},
            {"series": [{"tooltip": {"extraCssText": "background:url(//evil.example/a.png)"}}]},
            {"tooltip": {"extraCssText": "background:url(javascript:evil())"}},
            {"toolbox": {"feature": {"dataView": {"lang": ['<img src="/ok.png" onerror="evil()">', "Close", "Refresh"]}}}},
            {"toolbox": {"feature": {"dataView": {"title": '<img src="https://evil.example/a.png">'}}}},
            {"toolbox": {"feature": {"dataView": {"lang": {"0": '<img src="/ok.png" onerror="evil()">'}}}}},
            {"title": [{"link": "javascript:evil()", "target": "self"}]},
            {"title": {"sublink": "data:text/html,evil"}},
            {"title": {"link": ["javascript:evil()"]}},
            {"tooltip": {"extraCssText": ["background:url(https://evil.example/a.png)"]}},
            {"series": [{"type": "treemap", "data": [{"link": "javascript:evil()"}]}]},
            {"toolbox": {"feature": {"saveAsImage": {"lang": ['" onerror="evil()']}}}},
        ]
        safe = [
            {"dataset": {"source": [{"url": "https://external.example/data", "image": "https://external.example/a.png",
                                     "formatter": '<img src="/ok.png" onerror="evil()">', "value": 42}]}},
            {"title": {"link": "https://example.org/docs", "sublink": "/docs/"}},
            {"tooltip": {"extraCssText": "background:url(/local.png);padding:4px"}},
            {"toolbox": {"feature": {"dataView": {"lang": ["<b>Values</b>", "Close", "Refresh"]}}}},
        ]
        for payload, rejected in [(payload, True) for payload in unsafe] + [(payload, False) for payload in safe]:
            with self.subTest(payload=payload):
                parser = parse('<article><script type="application/json" data-td-echarts-options>' +
                               json.dumps(payload).replace("<", "\\u003c") + '</script></article>')
                errors = VALIDATOR.document_security_errors(parser, "index.html", BASE) + \
                         VALIDATOR.document_url_shape_errors(parser, "index.html")
                self.assertEqual(bool(errors), rejected, errors)

    def test_echarts_tooltip_shorthand_inherited_fonts_and_fallback_colors(self) -> None:
        hostile = '<img src="/missing" onerror="evil()">'
        unsafe = [
            {"series": [{"tooltip": hostile}]}, {"series": [{"data": [{"value": 5, "tooltip": hostile}]}]},
            {"textStyle": {"fontFamily": "serif;background:url(https://evil.example/font.png)"}},
            {"visualMap": {"pieces": [{"min": 0, "max": 10, "color": "red;background:url(https://evil.example/color.png)"}]}},
            {"tooltip": {"defaultBorderColor": "red;background:url(https://evil.example/border.png)"}},
        ]
        safe = [
            {"series": [{"tooltip": "<b>{b}</b>: {c}"}]},
            {"series": [{"data": [{"value": 5, "tooltip": "{b}: {c}"}]}]},
            {"textStyle": {"fontFamily": 'Arial, "思源黑体", sans-serif', "fontSize": 14}},
            {"visualMap": {"pieces": [{"color": {"type": "linear", "colorStops": [{"offset": 0, "color": "red"}]}}]}},
            {"tooltip": {"defaultBorderColor": "rgba(0,0,0,.5)"}},
            {"dataset": {"source": [{"tooltip": hostile, "textStyle": {"fontFamily": unsafe[2]["textStyle"]["fontFamily"]}}]}},
        ]
        for option, rejected in [(option, True) for option in unsafe] + [(option, False) for option in safe]:
            with self.subTest(option=option):
                parser = parse('<script type="application/json" data-td-echarts-options>' +
                               json.dumps(option).replace("<", "\\u003c") + '</script>')
                self.assertEqual(bool(VALIDATOR.document_security_errors(parser, "index.html", BASE)), rejected)

    def test_enabled_markmap_uses_explicit_plain_text_contract(self) -> None:
        import html
        runtime = '<script src="/third_party/markmap/markmap-autoloader.hash.js"></script>'
        plain = "---\n# layout comment\nmarkmap:\n  spacingHorizontal: 40 # layout\n---\n# HugeGraph\n- server\n- `core`"
        for source in [plain, "# Outline\n- `![image](https://evil.example/code.png)`", "# Outline\n```text\n![image](https://evil.example/code.png)\n```", "# Outline\n- &lt;img src=/literal&gt;"]:
            parser = parse('<pre><code class="language-markmap">' + html.escape(source) + '</code></pre>' + runtime)
            self.assertEqual(VALIDATOR.document_security_errors(parser, "index.html", BASE), [], source)
        blocked = ["# Parent\n- ![image](https://evil.example/map.png)", "# Parent\n- ![image](/img/allowed.png)",
                   "# Parent\n- ![image][ref]\n[ref]: /img/allowed.png", "# Parent\n- <img src=/allowed.png onerror=evil()>",
                   "---\nmarkmap:\n  extraJs: [/local.js]\n---\n# Parent", "---\ntitle: '<img src=/allowed.png>'\n---",
                   "# Parent\n- [link](/docs/)"]
        for source in blocked:
            with self.subTest(source=source):
                encoded = '<pre><code class="language-markmap">' + html.escape(source) + '</code></pre>'
                parser = parse(encoded + runtime)
                self.assertTrue(VALIDATOR.document_security_errors(parser, "index.html", BASE))
                # Disabled runtime and ordinary Markdown demonstrations remain
                # inert, even if their displayed text contains an image URL.
                self.assertEqual(VALIDATOR.document_security_errors(parse(encoded), "index.html", BASE), [])
                ordinary = encoded.replace("language-markmap", "language-markdown")
                self.assertEqual(VALIDATOR.document_security_errors(parse(ordinary + runtime), "index.html", BASE), [])

    @unittest.skipUnless(shutil.which(HUGO_BIN), "Hugo is required to render the pinned Markmap fixture")
    def test_native_markmap_runtime_on_off_obeys_plain_text_contract(self) -> None:
        repo = VALIDATOR_PATH.parents[1]
        with tempfile.TemporaryDirectory(prefix="oink-markmap-security-") as temporary:
            root = pathlib.Path(temporary)
            for name in ("go.mod", "go.sum"):
                shutil.copyfile(repo / name, root / name)
            (root / "layouts").mkdir()
            (root / "layouts/single.html").write_text('<article>{{ .Content }}</article>{{ partial "scripts.html" . }}')
            (root / "content").mkdir()
            sources = [
                ("# HugeGraph\n- server\n- core", False),
                ("---\nmarkmap:\n  spacingHorizontal: 40\n---\n# HugeGraph\n- server", False),
                ("# Parent\n- ![image](/img/local.png)", True),
                ("# Parent\n- ![image][ref]\n\n[ref]: https://evil.example/ref.png", True),
                # This pinned hook double-escapes raw HTML; textContent still
                # contains &lt; so MarkdownIt renders literal text, not an img.
                ("# Parent\n- <img src=/local.png onerror=evil()>", False),
                ("---\nmarkmap:\n  extraJs: [/local.js]\n---\n# Parent", True),
                ("# Parent\n- `![image](https://evil.example/code.png)`", False),
            ]
            for index, (source, _) in enumerate(sources):
                (root / f"content/map-{index}.md").write_text('---\ntitle: Map fixture\n---\n```markmap\n' + source + '\n```\n')
            artifact = root / "artifact"
            artifact.mkdir()
            for enabled in (True, False):
                (root / "hugo.yaml").write_text(
                    f'baseURL: {BASE.geturl()}\nparams:\n  markmap: {str(enabled).lower()}\n'
                    'module:\n  imports:\n  - path: github.com/pgsty/oink\n')
                result = subprocess.run([shutil.which(HUGO_BIN), "--source", str(root), "--destination", str(root / "public"),
                                         "--environment", "production", "--panicOnWarning"], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                for index, (_, rejected) in enumerate(sources):
                    with self.subTest(enabled=enabled, source=index):
                        shutil.copyfile(root / f"public/map-{index}/index.html", artifact / "index.html")
                        result = subprocess.run([sys.executable, str(VALIDATOR_PATH), str(artifact), BASE.geturl(), "--security-only"],
                                                text=True, capture_output=True)
                        self.assertEqual(bool(result.returncode), enabled and rejected, result.stdout + result.stderr)

    def test_echarts_effective_option_roots_reuse_all_sink_checks(self) -> None:
        wrappers = [lambda option: option, lambda option: {"baseOption": option},
                    lambda option: {"baseOption": {}, "options": [option]},
                    lambda option: {"baseOption": {}, "options": {"0": option}},
                    lambda option: {"media": [{"query": {"maxWidth": 600}, "option": option}]},
                    lambda option: {"media": [{"option": option}]}]
        unsafe_options = [
            {"title": {"link": "javascript:evil()"}},
            {"toolbox": {"feature": {"dataView": {"lang": ['<img src="/missing" onerror="evil()">']}}}},
            {"toolbox": {"feature": {"saveAsImage": {"lang": ['unsafe fallback']}}}},
            {"tooltip": {"backgroundColor": 'red;"><img src=/missing onerror=evil()>'}},
        ]
        safe = {"dataset": {"source": [{"symbol": "image://https://external.example/ordinary-data",
                                         "color": {"image": "https://external.example/ordinary-data"}}]},
                "tooltip": {"backgroundColor": "rgba(255, 255, 255, 0.8)"}}
        for wrap in wrappers:
            for option, rejected in [(option, True) for option in unsafe_options] + [(safe, False)]:
                with self.subTest(payload=wrap(option)):
                    parser = parse('<article><script type="application/json" data-td-echarts-options>' +
                                   json.dumps(wrap(option)).replace("<", "\\u003c") + '</script></article>')
                    errors = VALIDATOR.document_security_errors(parser, "index.html", BASE) + \
                             VALIDATOR.document_url_shape_errors(parser, "index.html")
                    self.assertEqual(bool(errors), rejected, errors)

    def test_echarts_html_css_color_sinks_accept_explicit_colors(self) -> None:
        legitimate = ["red", "AliceBlue", "transparent", "#f00", "#abcd", "#112233", "#11223388",
                      "rgb(255, 0, 0)", "rgba(100%, 0%, 50%, .8)", "hsl(120, 50%, 50%)", "hsla(120, 50%, 50%, 0.5)"]
        malicious = ['red;"><img src=/missing onerror=evil()>', "red;background-image:url(https://evil.example/a.png)",
                     ["red;background-image:url(https://evil.example/a.png)"], "var(--untrusted)", "not-a-color"]
        sinks = [lambda color: {"tooltip": {"backgroundColor": color}},
                 lambda color: {"series": [{"tooltip": {"borderColor": color}}]},
                 lambda color: {"tooltip": {"shadowColor": color, "textStyle": {"color": color, "textShadowColor": color}}},
                 lambda color: {"toolbox": {"feature": {"dataView": {"buttonColor": color, "buttonTextColor": color}}}}]
        for sink in sinks:
            for color, rejected in [(color, False) for color in legitimate] + [(color, True) for color in malicious]:
                with self.subTest(payload=sink(color)):
                    parser = parse('<script type="application/json" data-td-echarts-options>' +
                                   json.dumps(sink(color)).replace("<", "\\u003c") + '</script>')
                    self.assertEqual(bool(VALIDATOR.document_security_errors(parser, "index.html", BASE)), rejected)
        for stop, rejected in [("#f00", False), ('red;"><img src=/missing onerror=evil()>', True)]:
            parser = parse('<script type="application/json" data-td-echarts-options>' + json.dumps({
                "tooltip": {"borderColor": {"type": "linear", "colorStops": [{"offset": 0, "color": stop}]}}}) + '</script>')
            self.assertEqual(bool(VALIDATOR.document_security_errors(parser, "index.html", BASE)), rejected)

    def test_echarts_marker_color_sources_accept_palettes_gradients_and_patterns(self) -> None:
        gradient = {"type": "linear", "colorStops": [{"offset": 0, "color": "#f00"}, {"offset": 1, "color": "blue"}]}
        pattern = {"image": "/local.png", "repeat": "repeat"}
        safe_colors = ["#f00", "auto", "inherit", ["red", "#123456"], gradient, pattern]
        bad_colors = ["red;background:url(https://evil.example/a.png)", "$fn:uncheckedColor",
                      ["red", "blue;background:url(https://evil.example/a.png)"],
                      {"type": "linear", "colorStops": [{"offset": 0, "color": "red;background:url(https://evil.example/a.png)"}]}]
        sinks = [lambda color: {"color": color}, lambda color: {"colorLayer": [color]},
                 lambda color: {"series": [{"color": color}]},
                 lambda color: {"series": [{"itemStyle": {"color": color}}]},
                 lambda color: {"series": [{"data": [{"value": 1, "itemStyle": {"color": color}}]}]},
                 lambda color: {"series": [{"lineStyle": {"color": color}}]},
                 lambda color: {"visualMap": {"inRange": {"color": color}, "outOfRange": {"color": color}}}]
        for sink in sinks:
            for color, rejected in [(color, False) for color in safe_colors] + [(color, True) for color in bad_colors]:
                with self.subTest(option=sink(color)):
                    parser = parse('<script type="application/json" data-td-echarts-options>' + json.dumps(sink(color)) + '</script>')
                    errors = VALIDATOR.document_security_errors(parser, "index.html", BASE) + \
                             VALIDATOR.document_url_shape_errors(parser, "index.html")
                    self.assertEqual(bool(errors), rejected, errors)
        # The same fields in a dataset row are data, without a model style.
        parser = parse('<script type="application/json" data-td-echarts-options>' + json.dumps({
            "dataset": {"source": [{"color": bad_colors[0], "itemStyle": {"color": bad_colors[0]}}]}}) + '</script>')
        self.assertEqual(VALIDATOR.document_security_errors(parser, "index.html", BASE), [])

    def test_echarts_tooltip_css_numbers_and_font_options_use_declared_types(self) -> None:
        safe = {"shadowBlur": 4, "shadowOffsetX": -2, "shadowOffsetY": 0, "borderWidth": 1, "borderRadius": [4, 6],
                "padding": [4, 8], "textStyle": {"fontSize": 14, "lineHeight": 20, "textShadowBlur": 2,
                "textShadowOffsetX": 0, "textShadowOffsetY": 1, "fontFamily": "Arial, 'Noto Sans CJK SC', sans-serif",
                "fontStyle": "italic", "fontWeight": 600, "decoration": "underline", "align": "left"}}
        cases = [(safe, False)]
        for key in ("shadowBlur", "shadowOffsetX", "shadowOffsetY", "borderWidth", "borderRadius", "padding"):
            cases.append(({key: "1px;background:url(https://evil.example/a.png)"}, True))
        for key in ("fontSize", "lineHeight", "textShadowBlur", "textShadowOffsetX", "textShadowOffsetY",
                    "fontFamily", "fontStyle", "fontWeight", "decoration", "align"):
            cases.append(({"textStyle": {key: "1px;background:url(https://evil.example/a.png)"}}, True))
        cases.extend([({"shadowBlur": float("inf")}, True), ({"textStyle": {"fontSize": float("nan")}}, True),
                      ({"textStyle": {"fontFamily": '"思源黑体", sans-serif', "fontWeight": "bold"}}, False),
                      ({"textStyle": {"fontWeight": "600"}}, False), ({"shadowBlur": 10 ** 400}, True)])
        for tooltip, rejected in cases:
            with self.subTest(tooltip=tooltip):
                parser = parse('<script type="application/json" data-td-echarts-options>' +
                               json.dumps({"tooltip": tooltip}) + '</script>')
                self.assertEqual(bool(VALIDATOR.document_security_errors(parser, "index.html", BASE)), rejected)

    def test_echarts_array_symbols_and_pattern_images_are_active_resources(self) -> None:
        shapes = [lambda image: {"series": [{"markLine": {"symbol": ["image://" + image, "none"]}}]},
                  lambda image: {"visualMap": {"inRange": {"symbol": ["circle", "image://" + image]}}},
                  lambda image: {"series": [{"itemStyle": {"color": {"image": image, "repeat": "repeat"}}}]},
                  lambda image: {"graphic": {"style": {"fill": {"image": image}}}}]
        for shape in shapes:
            for image, rejected in [("https://evil.example/image.png", True), ("//evil.example/image.png", True),
                                    ("/local.png", False), ("https://hugegraph-oink.staged.apache.org/local.png", False)]:
                with self.subTest(payload=shape(image)):
                    parser = parse('<script type="application/json" data-td-echarts-options>' + json.dumps(shape(image)) + '</script>')
                    errors = VALIDATOR.document_security_errors(parser, "index.html", BASE) + \
                             VALIDATOR.document_url_shape_errors(parser, "index.html")
                    self.assertEqual(bool(errors), rejected, errors)

    @unittest.skipUnless(shutil.which(HUGO_BIN), "Hugo is required to render the pinned component fixture")
    def test_tagged_hugo_component_output_and_security_cli(self) -> None:
        repo = VALIDATOR_PATH.parents[1]
        with tempfile.TemporaryDirectory(prefix="oink-component-security-") as temporary:
            root = pathlib.Path(temporary)
            for name in ("go.mod", "go.sum"):
                shutil.copyfile(repo / name, root / name)
            (root / "hugo.yaml").write_text(
                "baseURL: https://hugegraph-oink.staged.apache.org/\nmodule:\n  imports:\n  - path: github.com/pgsty/oink\n")
            (root / "layouts").mkdir()
            (root / "layouts/single.html").write_text("<article>{{ .Content }}</article>")
            (root / "content").mkdir()
            (root / "content/fixture.md").write_text(
                '---\ntitle: Fixture\n---\n'
                '{{< asciinema file="/recording.cast" markers="10:Boot,25:Configure" >}}\n\n'
                '```echarts\n{"dataset":{"source":[{"url":"https://example.org/inert","value":42}]},'
                '"series":[{"type":"bar"}]}\n```\n')
            result = subprocess.run([shutil.which(HUGO_BIN), "--source", str(root), "--destination", str(root / "public")],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            html = (root / "public/fixture/index.html").read_text()
            self.assertIn('"markers":[10,"Boot",25,"Configure"]', html)
            parser = parse(html)
            self.assertEqual(VALIDATOR.document_security_errors(parser, "fixture/index.html", BASE), [])
            # Check the rendered component page in isolation; the fixture does
            # not include HugeGraph's SEO/CSS customizations for theme defaults.
            artifact = root / "artifact"
            artifact.mkdir()
            (artifact / "index.html").write_text(html)
            result = subprocess.run([sys.executable, str(VALIDATOR_PATH), str(artifact), BASE.geturl(), "--security-only"],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            # The actual native wrappers plus an alternate config carrier must
            # fail the same CLI, not just a manually constructed parser test.
            malicious = html.replace('<script type="application/json" data-td-asciinema-config>',
                                     '<pre data-td-asciinema-config>', 1)
            malicious = malicious.replace('</script>', '</pre>', 1)
            (artifact / "index.html").write_text(malicious)
            result = subprocess.run([sys.executable, str(VALIDATOR_PATH), str(artifact), BASE.geturl(), "--security-only"],
                                    text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("noncanonical OINK component", result.stdout)
            (root / "content/fixture.md").write_text(
                '---\ntitle: Unsafe fixture\n---\n```echarts\n' + json.dumps({
                    "tooltip": {"extraCssText": "background:url(https://evil.example/a.png)"},
                    "toolbox": {"feature": {"dataView": {"lang": ['<img src="/ok.png" onerror="evil()">']}}},
                    "title": {"link": "javascript:evil()"},
                }) + '\n```\n')
            html_option = {"toolbox": {"feature": {"dataView": {"lang": ['<img src="/missing" onerror="evil()">']}}}}
            native_counterexamples = [
                ({"series": [{"tooltip": '<img src="/missing" onerror="evil()">'}]}, "onerror"),
                ({"series": [{"data": [{"value": 5, "tooltip": '<img src="/missing" onerror="evil()">'}]}]}, "onerror"),
                ({"textStyle": {"fontFamily": "serif;background:url(https://evil.example/font.png)"}}, "invalid ECharts tooltip CSS font"),
                ({"visualMap": {"pieces": [{"color": "red;background:url(https://evil.example/piece.png)"}]}}, "invalid ECharts tooltip marker colour"),
                ({"tooltip": {"defaultBorderColor": "red;background:url(https://evil.example/border.png)"}}, "invalid ECharts CSS colour"),
                ({"color": ["red;background:url(https://evil.example/palette.png)"]}, "invalid ECharts tooltip marker colour"),
                ({"series": [{"itemStyle": {"color": "red;background:url(https://evil.example/itemstyle.png)"}}]},
                 "invalid ECharts tooltip marker colour"),
                ({"baseOption": html_option}, "onerror"),
                ({"baseOption": {}, "options": [html_option]}, "onerror"),
                ({"media": [{"query": {"maxWidth": 600}, "option": html_option}]}, "onerror"),
                ({"tooltip": {"backgroundColor": 'red;"><img src=/missing onerror=evil()>'}}, "invalid ECharts CSS colour"),
                ({"toolbox": {"feature": {"dataView": {"buttonColor": "red;background:url(https://evil.example/a.png)"}}}},
                 "invalid ECharts CSS colour"),
                ({"series": [{"markLine": {"symbol": ["image://https://evil.example/a.png", "none"]}}]}, "external active resource"),
                ({"visualMap": {"inRange": {"symbol": ["circle", "image://https://evil.example/a.png"]}}}, "external active resource"),
                ({"series": [{"itemStyle": {"color": {"image": "https://evil.example/a.png"}}}]}, "external active resource"),
            ]
            for index, (option, _) in enumerate(native_counterexamples):
                (root / f"content/unsafe-{index}.md").write_text(
                    '---\ntitle: Unsafe fixture\n---\n```echarts\n' + json.dumps(option) + '\n```\n')
            result = subprocess.run([shutil.which(HUGO_BIN), "--source", str(root), "--destination", str(root / "public")],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for index, (_, message) in enumerate(native_counterexamples):
                with self.subTest(native_counterexample=index):
                    shutil.copyfile(root / f"public/unsafe-{index}/index.html", artifact / "index.html")
                    result = subprocess.run([sys.executable, str(VALIDATOR_PATH), str(artifact), BASE.geturl(), "--security-only"],
                                            text=True, capture_output=True)
                    self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn(message, result.stdout)
            shutil.copyfile(root / "public/fixture/index.html", artifact / "index.html")
            result = subprocess.run([sys.executable, str(VALIDATOR_PATH), str(artifact), BASE.geturl(), "--security-only"],
                                    text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            # URL-shape errors take priority in this CLI; independently verify
            # all three runtime sinks on the very same rendered fixture.
            parser = parse((artifact / "index.html").read_text())
            errors = VALIDATOR.document_security_errors(parser, "index.html", BASE) + \
                     VALIDATOR.document_url_shape_errors(parser, "index.html")
            for message in ("external CSS", "onerror", "forbidden URL scheme"):
                self.assertIn(message, "\n".join(errors))

    def test_asciinema_payload_rejects_player_apis_outside_shortcode_schema(self) -> None:
        payload = {"src": "/recording.cast", "theme": "auto", "options": {"autoPlay": False}}
        variants = [dict(payload, audioUrl="https://evil.example/audio.mp3"),
                    dict(payload, options={"audioUrl": "https://evil.example/audio.mp3"}),
                    dict(payload, options={"driver": "benchmark"}),
                    dict(payload, options={"poster": "https://evil.example/poster.png"}),
                    dict(payload, options={"markers": [{"src": "https://evil.example/x"}]}),
                    dict(payload, options={"markers": [[1.0, "start"]]}),
                    dict(payload, options={"markers": [1.0]}),
                    dict(payload, options={"speed": {"url": "https://evil.example/x"}})]
        for variant in variants:
            with self.subTest(variant=variant):
                parser = parse('<article><script type="application/json" data-td-asciinema-config>' +
                               json.dumps(variant) + "</script></article>")
                self.assertTrue(VALIDATOR.document_security_errors(parser, "index.html", BASE))
        for poster in ("npt:0:10", "data:text/plain,hello"):
            parser = parse('<article><script type="application/json" data-td-asciinema-config>' +
                           json.dumps(dict(payload, options={"poster": poster, "markers": [1.0, "start"]})) + "</script></article>")
            self.assertEqual(VALIDATOR.document_security_errors(parser, "index.html", BASE), [])

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
            '<video></audio>'
            '<source src="https://www.apache.org/mismatched.mp4"></video>'
        )
        errors = VALIDATOR.document_security_errors(parser, "index.html", BASE)
        self.assertEqual(
            sum("external active resource" in error for error in errors),
            4,
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

        sequential = parse(
            '<template data-hg-authored-content="start"></template>'
            "<p>one</p>"
            '<template data-hg-authored-content="end"></template>'
            '<template data-hg-authored-content="start"></template>'
            "<p>two</p>"
            '<template data-hg-authored-content="end"></template>'
        )
        self.assertEqual(
            VALIDATOR.document_security_errors(sequential, "print.html", BASE),
            [],
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
