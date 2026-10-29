#!/usr/bin/env python3
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Validate the generated site's public URL and metadata contracts."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import html.parser
import json
import math
import pathlib
import re
import urllib.parse
import xml.etree.ElementTree as ET


REQUIRED_FILES = (
    "index.html",
    "404.html",
    "sitemap.xml",
    "en/sitemap.xml",
    "navigation.json",
    "llms.txt",
    "docs/index.html",
    "docs/quickstart/hugegraph-server/index.html",
    "docs/introduction/readme/index.html",
    "cn/index.html",
    "cn/404.html",
    "cn/sitemap.xml",
    "cn/navigation.json",
    "cn/llms.txt",
    "cn/docs/index.html",
    "cn/docs/quickstart/hugegraph-server/index.html",
    "cn/docs/introduction/readme/index.html",
    "en/index.html",
    "_print/docs/index.html",
    "cn/_print/docs/index.html",
    "client-go/index.html",
)

HREFLANG_FALLBACKS = {
    # The English release note is intentionally draft-only.
    "cn/docs/changelog/hugegraph-0.12.0-release-notes/index.html": {"en-US": "/"},
    # This community page currently has no Chinese source counterpart.
    "community/maturity/index.html": {"zh-CN": "/cn/"},
}

# Mirrors the HTTPS image sources currently allowed by the ASF staging CSP:
# https://*.apache.org, https://apache.org, the two conference sites, and
# https://*.scarf.sh. The expected site origin is allowed separately as self.
ASF_CSP_IMAGE_HOSTS = {
    "apache.org",
    "www.apachecon.com",
    "www.communityovercode.org",
}
ASF_CSP_IMAGE_SUFFIXES = (".apache.org", ".scarf.sh")
UNSAFE_AUTHORED_ELEMENTS = {"script", "iframe", "frame", "object", "embed"}
ERROR_DOCUMENT_PATHS = {
    "404.html",
    "cn/404.html",
}
DOCS_NAV_GROUP_TITLES = {
    "en": ("Get Started", "Components", "Develop", "Operate", "Reference"),
    "cn": ("开始", "组件", "开发", "配置", "参考"),
}
EXTERNAL_ACTIVE_RESOURCE_ATTRIBUTES = {
    ("asciinema-config", "src"),
    ("echarts-options", "resource"),
    ("script", "src"),
    ("link", "href"),
    ("iframe", "src"),
    ("frame", "src"),
    ("object", "data"),
    ("embed", "src"),
    ("audio", "src"),
    ("video", "src"),
    ("track", "src"),
    ("media-source", "src"),
    ("media-source", "srcset"),
    ("form", "action"),
    ("button", "formaction"),
    ("input", "formaction"),
    ("use", "href"),
    ("use", "xlink:href"),
    ("mpath", "href"),
    ("mpath", "xlink:href"),
    ("textpath", "href"),
    ("textpath", "xlink:href"),
    ("tref", "href"),
    ("tref", "xlink:href"),
    ("cursor", "href"),
    ("cursor", "xlink:href"),
    ("animate", "href"),
    ("animate", "xlink:href"),
    ("animatemotion", "href"),
    ("animatemotion", "xlink:href"),
    ("animatetransform", "href"),
    ("animatetransform", "xlink:href"),
    ("set", "href"),
    ("set", "xlink:href"),
    ("script", "href"),
    ("script", "xlink:href"),
    ("link", "imagesrcset"),
}
LINK_RESOURCE_RELS = {
    "stylesheet",
    "preload",
    "modulepreload",
    "icon",
    "apple-touch-icon",
    "mask-icon",
    "apple-touch-startup-image",
    "manifest",
    "prefetch",
    "prerender",
    "preconnect",
    "dns-prefetch",
}
LINK_METADATA_RELS = {"canonical"}
SVG_ACTIVE_IRI_ELEMENTS = {
    "use",
    "script",
    "mpath",
    "textpath",
    "tref",
    "cursor",
    "animate",
    "animatemotion",
    "animatetransform",
    "set",
}
CSS_PRESENTATION_ATTRIBUTES = {
    "clip-path",
    "color-profile",
    "cursor",
    "fill",
    "filter",
    "marker",
    "marker-start",
    "marker-mid",
    "marker-end",
    "mask",
    "stroke",
}
RUNTIME_ACTIVE_URL_ATTRIBUTES = {
    "data-td-index-src",
    "data-td-url",
    "data-td-action-url",
}
RUNTIME_IMAGE_URL_ATTRIBUTES = {"data-td-image-zoom"}
# Native reader dialogs use these localized strings only through textContent.
# Keep their exact pinned-template schema separate from chart/player options.
OINK_READER_LABEL_FIELDS = {
    "data-td-table-labels": {"title", "viewport"},
    "data-td-diagram-labels": {
        "source", "expand", "copy", "copied", "copyError", "error",
        "downloadStarted", "downloadError",
    },
}
OINK_CONFIG_MARKERS = {
    "data-td-diagram-source", "data-td-echarts-options", "data-td-asciinema-config",
} | set(OINK_READER_LABEL_FIELDS)


def is_inert_oink_component_source(tag: str, values: dict[str, str]) -> bool:
    """Match the exact inert JSON carriers emitted by pinned OINK templates."""

    if tag != "script" or values.get("type", "").strip().lower() != "application/json":
        return False
    # These templates emit only type and one empty marker. Extra attributes
    # (including class, src and handlers) are not part of the trusted shape.
    return any(set(values) == {"type", marker} and values[marker] == ""
               for marker in OINK_CONFIG_MARKERS)


# Named colours supported by the pinned ECharts/ZRender colour parser.
ECHARTS_COLOR_NAMES = frozenset("""
transparent aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue blueviolet
brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue darkcyan
darkgoldenrod darkgray darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid darkred
darksalmon darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink
deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold
goldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki lavender lavenderblush
lawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgreen lightgrey
lightpink lightsalmon lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime
limegreen linen magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen
mediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin
navajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise
palevioletred papayawhip peachpuff peru pink plum powderblue purple red rosybrown royalblue saddlebrown salmon
sandybrown seagreen seashell sienna silver skyblue slateblue slategray slategrey snow springgreen steelblue
tan teal thistle tomato turquoise violet wheat white whitesmoke yellow yellowgreen
""".split())


def echarts_css_color(value: object) -> bool:
    """Accept explicit colour syntax, never CSS declarations or HTML markup."""

    if not isinstance(value, str):
        return False
    value = value.strip().lower()
    if value in ECHARTS_COLOR_NAMES or re.fullmatch(r"#(?:[0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})", value):
        return True
    function = re.fullmatch(r"(rgba?|hsla?)\(\s*([^()]*)\s*\)", value)
    if not function:
        return False
    name, arguments = function.groups()
    parts = [part.strip() for part in arguments.split(",")]
    expected = 4 if name.endswith("a") else 3
    return len(parts) == expected and all(re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)%?", part) for part in parts)


def echarts_marker_color(value: object) -> bool:
    """Validate actual palette/style colour sources before tooltip markup."""

    if value is None:
        return True
    if isinstance(value, str):
        return echarts_css_color(value) or value in {"auto", "inherit"}
    if isinstance(value, list):
        return all(echarts_marker_color(color) for color in value)
    if isinstance(value, dict):
        if isinstance(value.get("colorStops"), list):
            return all(isinstance(stop, dict) and echarts_css_color(stop.get("color")) for stop in value["colorStops"])
        # ECharts pattern fills accept image URLs; the resource traversal below
        # checks that URL against the same-origin policy, including local URLs.
        return isinstance(value.get("image"), str)
    return False


def finite_json_number(value: object) -> bool:
    try:
        return type(value) in {int, float} and math.isfinite(value)
    except OverflowError:
        return False


def echarts_option_roots(payload: dict) -> list[dict]:
    """Enumerate ECharts OptionManager's base, timeline, and media options."""

    roots = [payload["baseOption"] if isinstance(payload.get("baseOption"), dict) else payload]
    options = payload.get("options")
    # ECharts' each() also visits object values; numeric keys can be selected
    # by its timeline index even though the documented form is an array.
    if isinstance(options, (list, dict)):
        roots.extend(option for option in (options.values() if isinstance(options, dict) else options)
                     if isinstance(option, dict))
    if isinstance(payload.get("media"), list):
        roots.extend(media["option"] for media in payload["media"]
                     if isinstance(media, dict) and isinstance(media.get("option"), dict))
    return roots


def srcset_urls(value: str) -> list[str]:
    """Return URL tokens from an HTML srcset without splitting data-URL commas."""

    urls: list[str] = []
    position = 0
    while position < len(value):
        while position < len(value) and (
            value[position].isspace() or value[position] == ","
        ):
            position += 1
        if position == len(value):
            break

        start = position
        is_data_url = value[start:].lower().startswith("data:")
        while position < len(value) and not value[position].isspace():
            if value[position] == "," and not is_data_url:
                break
            position += 1
        token = value[start:position]
        trailing_commas = len(token) - len(token.rstrip(","))
        token = token.rstrip(",")
        if token:
            urls.append(token)
        if position < len(value) and value[position] == ",":
            position += 1
            continue
        if trailing_commas:
            continue

        # Skip width/density descriptors until the next candidate delimiter.
        while position < len(value) and value[position] != ",":
            position += 1
        if position < len(value):
            position += 1
    return urls


def css_http_resources(value: str) -> list[str]:
    """Find insecure HTTP resources in CSS declarations or stylesheets."""
    return [
        resource
        for resource in css_resource_urls(value)
        if urllib.parse.urlsplit(resource).scheme.lower() == "http"
    ]


def css_resource_urls(value: str) -> list[str]:
    """Extract browser request URLs from CSS without regex token ambiguity."""

    def consume_escape(source: str, position: int) -> tuple[str, int]:
        position += 1
        if position >= len(source):
            return "", position
        if source[position] in "\r\n\f":
            if source[position] == "\r" and position + 1 < len(source):
                position += source[position + 1] == "\n"
            return "", position + 1
        end = position
        while (
            end < len(source)
            and end - position < 6
            and source[end] in "0123456789abcdefABCDEF"
        ):
            end += 1
        if end > position:
            codepoint = int(source[position:end], 16)
            if end < len(source) and source[end].isspace():
                end += 1
            if codepoint == 0 or codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
                return "\N{REPLACEMENT CHARACTER}", end
            return chr(codepoint), end
        return source[position], position + 1

    def skip_space_and_comments(source: str, position: int) -> int:
        while position < len(source):
            if source[position].isspace():
                position += 1
            elif source.startswith("/*", position):
                closing = source.find("*/", position + 2)
                position = len(source) if closing < 0 else closing + 2
            else:
                break
        return position

    def consume_name(source: str, position: int) -> tuple[str, int]:
        decoded: list[str] = []
        while position < len(source):
            char = source[position]
            if char == "\\":
                escaped, position = consume_escape(source, position)
                decoded.append(escaped)
            elif char.isalnum() or char in "_-" or ord(char) >= 0x80:
                decoded.append(char)
                position += 1
            else:
                break
        return "".join(decoded), position

    def consume_string(source: str, position: int) -> tuple[str, int]:
        quote = source[position]
        position += 1
        decoded: list[str] = []
        while position < len(source):
            char = source[position]
            if char == quote:
                return "".join(decoded), position + 1
            if char == "\\":
                escaped, position = consume_escape(source, position)
                decoded.append(escaped)
                continue
            decoded.append(char)
            position += 1
        return "".join(decoded), position

    def matching_paren(source: str, position: int) -> int:
        depth = 1
        while position < len(source):
            if source.startswith("/*", position):
                position = skip_space_and_comments(source, position)
                continue
            char = source[position]
            if char in "'\"":
                _string, position = consume_string(source, position)
            elif char == "\\":
                _escaped, position = consume_escape(source, position)
            else:
                depth += char == "("
                depth -= char == ")"
                position += 1
                if depth == 0:
                    return position - 1
        return len(source)

    def consume_url_function(source: str, position: int) -> tuple[str, int]:
        position = skip_space_and_comments(source, position)
        if position < len(source) and source[position] in "'\"":
            resource, position = consume_string(source, position)
            position = skip_space_and_comments(source, position)
            closed = position < len(source) and source[position] == ")"
            return resource, position + closed

        decoded: list[str] = []
        while position < len(source):
            if source.startswith("/*", position):
                position = skip_space_and_comments(source, position)
                continue
            char = source[position]
            if char == ")":
                return "".join(decoded).strip(), position + 1
            if char.isspace():
                position = skip_space_and_comments(source, position)
                while position < len(source) and source[position] != ")":
                    position += 1
                return "".join(decoded), position + (position < len(source))
            if char == "\\":
                escaped, position = consume_escape(source, position)
                decoded.append(escaped)
                continue
            decoded.append(char)
            position += 1
        return "".join(decoded).strip(), position

    def scan(source: str) -> list[str]:
        resources: list[str] = []
        position = 0
        while position < len(source):
            if source.startswith("/*", position) or source[position].isspace():
                position = skip_space_and_comments(source, position)
                continue
            if source[position] in "'\"":
                _string, position = consume_string(source, position)
                continue
            if source[position] == "@":
                name, after_name = consume_name(source, position + 1)
                if name.lower() == "import":
                    candidate = skip_space_and_comments(source, after_name)
                    if candidate < len(source) and source[candidate] in "'\"":
                        resource, position = consume_string(source, candidate)
                        resources.append(resource)
                        continue
                position = max(after_name, position + 1)
                continue
            if (
                source[position].isalnum()
                or source[position] in "_-\\"
                or ord(source[position]) >= 0x80
            ):
                name, after_name = consume_name(source, position)
                opening = skip_space_and_comments(source, after_name)
                if opening >= len(source) or source[opening] != "(":
                    position = max(after_name, position + 1)
                    continue
                lowered = name.lower()
                if lowered == "url":
                    resource, position = consume_url_function(source, opening + 1)
                    if resource:
                        resources.append(resource)
                    continue
                if lowered in {"image-set", "-webkit-image-set"}:
                    closing = matching_paren(source, opening + 1)
                    body = source[opening + 1 : closing]
                    candidate_start = 0
                    depth = 0
                    cursor = 0
                    while cursor <= len(body):
                        at_end = cursor == len(body)
                        if not at_end and body.startswith("/*", cursor):
                            cursor = skip_space_and_comments(body, cursor)
                            continue
                        if not at_end and body[cursor] in "'\"":
                            _string, cursor = consume_string(body, cursor)
                            continue
                        if not at_end and body[cursor] == "\\":
                            _escaped, cursor = consume_escape(body, cursor)
                            continue
                        if not at_end:
                            depth += body[cursor] == "("
                            depth -= body[cursor] == ")"
                        if at_end or (body[cursor] == "," and depth == 0):
                            candidate = body[candidate_start:cursor]
                            first = skip_space_and_comments(candidate, 0)
                            if first < len(candidate) and candidate[first] in "'\"":
                                resource, _end = consume_string(candidate, first)
                                resources.append(resource)
                            else:
                                resources.extend(scan(candidate))
                            candidate_start = cursor + 1
                        cursor += 1
                    position = closing + (closing < len(source))
                    continue
                position = opening + 1
                continue
            position += 1
        return resources

    return scan(value)


def css_external_resources(
    value: str, base_parts: urllib.parse.SplitResult
) -> list[str]:
    """Reject HTTPS/protocol-relative CSS resources outside the site origin."""
    resources = []
    for resource in css_resource_urls(value):
        parts = urllib.parse.urlsplit(resource)
        if (
            parts.netloc
            and parts.netloc != base_parts.netloc
            and parts.scheme.lower() != "http"
        ):
            resources.append(resource)
    return resources


def image_url_allowed_by_asf_csp(
    url: str, base_parts: urllib.parse.SplitResult
) -> bool:
    """Return whether an external image URL is loadable by the ASF staging CSP."""

    parts = urllib.parse.urlsplit(url)
    if not parts.netloc or parts.netloc == base_parts.netloc:
        return True
    if parts.scheme.lower() != "https":
        return False
    try:
        if parts.port not in {None, 443}:
            return False
    except ValueError:
        return False
    hostname = (parts.hostname or "").lower().rstrip(".")
    return hostname in ASF_CSP_IMAGE_HOSTS or hostname.endswith(ASF_CSP_IMAGE_SUFFIXES)


def error_document_paths(root: pathlib.Path | None = None) -> set[str]:
    """Return root and version-scoped error documents from the active manifest."""

    manifest_paths = []
    if root is not None:
        manifest_paths.append(root / "build-metadata/versions.json")
    manifest_paths.append(pathlib.Path(__file__).resolve().parents[1] / "versions.json")
    manifest_path = next((path for path in manifest_paths if path.is_file()), None)
    if manifest_path is None:
        return set(ERROR_DOCUMENT_PATHS)

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot parse version manifest {manifest_path}: {exc}") from exc
    versions = manifest.get("versions")
    if not isinstance(versions, list):
        raise ValueError(f"version manifest {manifest_path} has no versions list")

    paths = set(ERROR_DOCUMENT_PATHS)
    for entry in versions:
        publish_path = entry.get("publishPath") if isinstance(entry, dict) else None
        if not isinstance(publish_path, str):
            raise ValueError(
                f"version manifest {manifest_path} has invalid publishPath"
            )
        if not publish_path:
            continue
        pure_path = pathlib.PurePosixPath(publish_path)
        if (
            pure_path.is_absolute()
            or ".." in pure_path.parts
            or pure_path.as_posix() != publish_path
        ):
            raise ValueError(
                f"version manifest {manifest_path} has unsafe publishPath "
                f"{publish_path!r}"
            )
        paths.add(f"{publish_path}/404.html")
        paths.add(f"{publish_path}/cn/404.html")
    return paths


def error_document_seo_errors(
    parser: DocumentParser,
    page_name: str,
    error_paths: set[str] | None = None,
) -> list[str]:
    """Require error documents to stay out of indexes and canonical clusters."""

    if page_name not in (
        error_paths if error_paths is not None else error_document_paths()
    ):
        return []

    errors: list[str] = []
    robots = [
        meta.get("content", "")
        for meta in parser.meta
        if meta.get("name", "").strip().lower() == "robots"
    ]
    expected_directives = {"noindex", "nofollow"}
    if (
        len(robots) != 1
        or {
            directive.strip().lower()
            for directive in robots[0].split(",")
            if directive.strip()
        }
        != expected_directives
    ):
        errors.append(
            f"{page_name}: expected one robots noindex,nofollow directive, "
            f"found {robots!r}"
        )
    if parser.canonical:
        errors.append(f"{page_name}: error document must not declare canonical")
    if parser.hreflang:
        errors.append(f"{page_name}: error document must not declare hreflang")
    return errors


def toc_accessibility_errors(parser: DocumentParser, page_name: str) -> list[str]:
    """Require each rendered Hugo TOC nav to have one localized accessible name."""

    if not parser.toc_nav_labels:
        return []
    if len(parser.toc_nav_labels) != 1:
        return [
            f"{page_name}: expected at most one TableOfContents nav, "
            f"found {len(parser.toc_nav_labels)}"
        ]
    parts = pathlib.PurePosixPath(page_name).parts
    is_chinese = bool(parts) and (
        parts[0] == "cn"
        or (len(parts) >= 3 and parts[0] == "versions" and parts[2] == "cn")
    )
    expected = "目录" if is_chinese else "Content"
    labels = parser.toc_nav_labels[0]
    if labels != [expected]:
        return [
            f"{page_name}: TableOfContents nav must have exactly one localized "
            f"aria-label {expected!r}, found {labels!r}"
        ]
    return []


def docs_navigation_errors(data: dict, source: str, language: str) -> list[str]:
    """Validate the five-group Docs IA in one OINK NAVJSON output."""
    errors: list[str] = []
    expected = DOCS_NAV_GROUP_TITLES.get(language)
    if expected is None:
        return [f"{source}: unsupported navigation language: {language}"]
    docs_nodes = [
        item
        for item in data.get("root", {}).get("children", [])
        if isinstance(item, dict) and item.get("id") == "/docs/"
    ]
    if len(docs_nodes) != 1:
        return [f"{source}: expected one Docs node, found {len(docs_nodes)}"]
    groups = docs_nodes[0].get("children")
    if not isinstance(groups, list):
        return [f"{source}: Docs navigation children are missing"]
    actual = tuple(
        item.get("title") if isinstance(item, dict) else None for item in groups
    )
    if actual != expected:
        errors.append(f"{source}: Docs groups {actual!r} != {expected!r}")
    for group in groups:
        if not isinstance(group, dict):
            continue
        if group.get("kind") != "external" or not group.get("children"):
            errors.append(f"{source}: Docs group is not a populated link: {group!r}")
    pending = [data]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
        elif isinstance(item, str) and "/_nav/" in item.lower():
            errors.append(f"{source}: private Docs navigation route leaked: {item}")
    return errors


def document_security_errors(
    parser: DocumentParser, page_name: str, base_parts: urllib.parse.SplitResult
) -> list[str]:
    """Return fail-closed resource and authored-markup errors for one page."""

    parser._check_markmap_sources()
    errors = [
        f"{page_name}: unsafe content markup: {violation}"
        for violation in parser.authored_violations
    ]
    if parser._content_markers[0] != parser._content_markers[1]:
        errors.append(
            f"{page_name}: unsafe content markup: unbalanced authored-content markers"
        )
    errors.extend(
        f"{page_name}: mixed-content CSS resource: {resource}"
        for resource in parser.inline_css_http_resources
    )
    errors.extend(
        f"{page_name}: external CSS resource is forbidden: {resource}"
        for resource in css_external_resources(
            "\n".join(parser.inline_css_sources), base_parts
        )
    )
    errors.extend(
        f"{page_name}: mixed-content <{tag}> {attribute}: {resource}"
        for tag, attribute, resource in parser.resources
        if urllib.parse.urlsplit(resource.strip()).scheme.lower() == "http"
    )
    errors.extend(
        f"{page_name}: external active resource is forbidden <{tag}> "
        f"{attribute}: {resource}"
        for tag, attribute, resource in parser.resources
        if (
            (tag, attribute) in EXTERNAL_ACTIVE_RESOURCE_ATTRIBUTES
            or attribute in RUNTIME_ACTIVE_URL_ATTRIBUTES
            or (
                attribute in {"href", "xlink:href"}
                and tag not in {"a", "image", "feimage"}
            )
        )
        and urllib.parse.urlsplit(resource.strip()).netloc
        and urllib.parse.urlsplit(resource.strip()).netloc != base_parts.netloc
        and urllib.parse.urlsplit(resource.strip()).scheme.lower() != "http"
    )
    for tag, attribute, image_url in parser.image_urls:
        parts = urllib.parse.urlsplit(image_url.strip())
        if (
            parts.scheme.lower() != "http"
            and parts.netloc
            and not image_url_allowed_by_asf_csp(image_url, base_parts)
        ):
            errors.append(
                f"{page_name}: image URL is outside ASF CSP <{tag}> "
                f"{attribute}: {image_url}"
            )
    return errors


class DocumentParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.urls: list[tuple[str, str]] = []
        self.navigation_urls: list[tuple[str, str, str]] = []
        self.canonical: list[str] = []
        self.hreflang: list[tuple[str, str]] = []
        self.meta: list[dict[str, str]] = []
        self.resources: list[tuple[str, str, str]] = []
        self.image_urls: list[tuple[str, str, str]] = []
        self.authored_violations: list[str] = []
        self.inline_css_http_resources: list[str] = []
        self.inline_css_sources: list[str] = []
        self.toc_nav_labels: list[list[str]] = []
        self.action_manifest = ""
        self._in_action_manifest = False
        self._component_source = ""
        self._component_json = ""
        self._content_depth = 0
        self._content_markers = [0, 0]
        self._in_content_marker = False
        self._in_style = False
        self._svg_depth = 0
        self._media_elements: list[str] = []
        self._pre_sources: list[dict] = []
        self._markmap_containers: list[dict] = []
        self._markmap_sources: list[str] = []
        self._markmap_carrier_errors: list[str] = []
        self._markmap_checked = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"audio", "video"}:
            self._media_elements.append(tag)
        in_svg = bool(self._svg_depth) or tag == "svg"
        if tag == "svg":
            self._svg_depth += 1
        seen_attributes: set[str] = set()
        duplicate_attributes: set[str] = set()
        for key, _value in attrs:
            attribute = key.lower()
            if attribute in seen_attributes and attribute not in duplicate_attributes:
                self.authored_violations.append(
                    f"duplicate {attribute} attribute on <{tag}>"
                )
                duplicate_attributes.add(attribute)
            seen_attributes.add(attribute)
        values = {key.lower(): value or "" for key, value in attrs}
        content_marker = (
            values.get("data-hg-authored-content")
            if tag == "template"
            else None
        )
        if content_marker == "start":
            self._content_markers[0] += 1
            if self._in_content_marker:
                self.authored_violations.append(
                    "nested authored-content start marker"
                )
            self._in_content_marker = True
        elif content_marker == "end":
            self._content_markers[1] += 1
            if not self._in_content_marker:
                self.authored_violations.append(
                    "unexpected authored-content end marker"
                )
            self._in_content_marker = False
        # Runtime configOf() queries the marker on any element, not just a
        # script. Reject every non-template carrier even outside article/main.
        if OINK_CONFIG_MARKERS.intersection(values) and not is_inert_oink_component_source(tag, values):
            self.authored_violations.append(f"noncanonical OINK component configuration on <{tag}>")
        for container in self._markmap_containers:
            if tag == container["tag"]:
                container["depth"] += 1
        if tag == "pre":
            self._pre_sources.append({"source": "", "markmap": False})
        classes = values.get("class", "").split()
        if "language-markmap" in classes:
            if tag == "code" and self._pre_sources:
                self._pre_sources[-1]["markmap"] = True
            else:
                self._markmap_carrier_errors.append("noncanonical Markmap source carrier")
        if "markmap" in classes:
            self._markmap_containers.append({"tag": tag, "depth": 1, "source": ""})
        if tag == "nav" and "TableOfContents" in [
            value or "" for key, value in attrs if key.lower() == "id"
        ]:
            self.toc_nav_labels.append(
                [value or "" for key, value in attrs if key.lower() == "aria-label"]
            )
        if tag in {"main", "article"}:
            self._content_depth += 1
        if self._content_depth or self._in_content_marker:
            if tag in UNSAFE_AUTHORED_ELEMENTS and not is_inert_oink_component_source(
                tag, values
            ):
                self.authored_violations.append(f"authored <{tag}>")
            for attribute in values:
                if attribute.startswith("on"):
                    self.authored_violations.append(
                        f"authored {attribute} event attribute on <{tag}>"
                    )

        if tag in {"a", "area"} and values.get("href"):
            self.urls.append(("href", values["href"]))
            self.navigation_urls.append((tag, "href", values["href"]))
        if tag == "link" and values.get("href"):
            self.urls.append(("href", values["href"]))
        if tag in {"img", "script", "source"} and values.get("src"):
            self.urls.append(("src", values["src"]))
        resource_attributes: list[tuple[str, str]] = []
        if tag in {"img", "script", "source", "video", "audio", "track", "embed"}:
            if values.get("src"):
                resource_attributes.append(("src", values["src"]))
        if tag == "video" and values.get("poster"):
            resource_attributes.append(("poster", values["poster"]))
        if tag == "object" and values.get("data"):
            resource_attributes.append(("data", values["data"]))
            self.urls.append(("data", values["data"]))
        if tag == "form" and values.get("action"):
            resource_attributes.append(("action", values["action"]))
            self.urls.append(("action", values["action"]))
        if tag in {"button", "input"} and values.get("formaction"):
            resource_attributes.append(("formaction", values["formaction"]))
            self.urls.append(("formaction", values["formaction"]))
        if tag in SVG_ACTIVE_IRI_ELEMENTS | {"image", "feimage"}:
            for attribute in ("href", "xlink:href"):
                if not values.get(attribute):
                    continue
                if (attribute, values[attribute]) not in resource_attributes:
                    resource_attributes.append((attribute, values[attribute]))
                if (attribute, values[attribute]) not in self.urls:
                    self.urls.append((attribute, values[attribute]))
        if (
            in_svg
            and tag not in {"a", "image", "feimage", "link"}
            and values.get("href")
        ):
            if ("href", values["href"]) not in resource_attributes:
                resource_attributes.append(("href", values["href"]))
            if ("href", values["href"]) not in self.urls:
                self.urls.append(("href", values["href"]))
        if tag == "a" and values.get("xlink:href"):
            self.urls.append(("xlink:href", values["xlink:href"]))
            self.navigation_urls.append((tag, "xlink:href", values["xlink:href"]))
        elif (
            values.get("xlink:href")
            and tag not in SVG_ACTIVE_IRI_ELEMENTS | {"image", "feimage"}
        ):
            resource_attributes.append(("xlink:href", values["xlink:href"]))
            self.urls.append(("xlink:href", values["xlink:href"]))
        if tag == "iframe" and values.get("src"):
            resource_attributes.append(("src", values["src"]))
        if tag == "frame" and values.get("src"):
            resource_attributes.append(("src", values["src"]))
            self.urls.append(("src", values["src"]))
        if (
            tag == "input"
            and values.get("type", "").lower() == "image"
            and values.get("src")
        ):
            resource_attributes.append(("src", values["src"]))
        if tag == "link" and values.get("href"):
            rel = set(values.get("rel", "").lower().split())
            is_metadata = rel == LINK_METADATA_RELS or (
                rel == {"alternate"} and bool(values.get("hreflang"))
            )
            if rel & LINK_RESOURCE_RELS or not is_metadata:
                resource_attributes.append(("href", values["href"]))
            else:
                self.navigation_urls.append((tag, "href", values["href"]))
        if tag == "link" and values.get("imagesrcset"):
            urls = srcset_urls(values["imagesrcset"])
            resource_attributes.extend(
                ("imagesrcset", url) for url in urls
            )
            self.urls.extend(("imagesrcset", url) for url in urls)
            self.image_urls.extend(
                (tag, "imagesrcset", url) for url in urls
            )
        if tag in {"a", "area"} and "ping" in values:
            self.authored_violations.append(f"forbidden ping attribute on <{tag}>")
        if tag == "base" and "href" in values:
            self.authored_violations.append("forbidden base[href]")
        if tag == "iframe" and "srcdoc" in values:
            self.authored_violations.append("forbidden iframe[srcdoc]")
        if "attributionsrc" in values:
            self.authored_violations.append(
                f"forbidden attributionsrc attribute on <{tag}>"
            )
        if tag in {"body", "table", "td", "th"} and values.get("background"):
            resource_attributes.append(("background", values["background"]))
            self.urls.append(("background", values["background"]))
            self.image_urls.append((tag, "background", values["background"]))
        for attribute in RUNTIME_ACTIVE_URL_ATTRIBUTES | RUNTIME_IMAGE_URL_ATTRIBUTES:
            if not values.get(attribute):
                continue
            resource_attributes.append((attribute, values[attribute]))
            self.urls.append((attribute, values[attribute]))
            if attribute in RUNTIME_IMAGE_URL_ATTRIBUTES:
                self.image_urls.append((tag, attribute, values[attribute]))
        resource_tag = (
            "media-source"
            if tag == "source" and self._media_elements
            else tag
        )
        self.resources.extend(
            (resource_tag, attribute, url)
            for attribute, url in resource_attributes
        )

        if tag == "img" or (tag == "source" and not self._media_elements):
            for attribute in ("src", "srcset"):
                if not values.get(attribute):
                    continue
                urls = (
                    srcset_urls(values[attribute])
                    if attribute == "srcset"
                    else [values[attribute]]
                )
                self.image_urls.extend((tag, attribute, url) for url in urls)
                if attribute == "srcset":
                    self.resources.extend(
                        (resource_tag, attribute, url) for url in urls
                    )
                    self.urls.extend((attribute, url) for url in urls)
        elif tag == "source" and values.get("srcset"):
            urls = srcset_urls(values["srcset"])
            self.resources.extend(
                (resource_tag, "srcset", url) for url in urls
            )
            self.urls.extend(("srcset", url) for url in urls)
        if tag == "video" and values.get("poster"):
            self.image_urls.append((tag, "poster", values["poster"]))
        if (
            tag == "input"
            and values.get("type", "").lower() == "image"
            and values.get("src")
        ):
            self.image_urls.append((tag, "src", values["src"]))
        if tag in {"image", "feimage"}:
            for attribute in ("href", "xlink:href"):
                if values.get(attribute):
                    self.image_urls.append((tag, attribute, values[attribute]))

        if values.get("style"):
            self.inline_css_sources.append(values["style"])
            self.inline_css_http_resources.extend(css_http_resources(values["style"]))
        for attribute in CSS_PRESENTATION_ATTRIBUTES:
            if values.get(attribute):
                self.inline_css_sources.append(values[attribute])
                self.inline_css_http_resources.extend(
                    css_http_resources(values[attribute])
                )
        if tag == "link" and values.get("rel", "").lower() == "canonical":
            self.canonical.append(values.get("href", ""))
        if (
            tag == "link"
            and values.get("rel", "").lower() == "alternate"
            and values.get("hreflang")
        ):
            self.hreflang.append((values["hreflang"], values.get("href", "")))
        if tag == "meta":
            self.meta.append(values)
        if tag == "script" and values.get("id") == "td-action-manifest":
            self._in_action_manifest = True
        if is_inert_oink_component_source(tag, values):
            for marker in ("data-td-echarts-options", "data-td-asciinema-config", *OINK_READER_LABEL_FIELDS):
                if marker in values:
                    self._component_source = marker
                    self._component_json = ""
        if tag == "style":
            self._in_style = True

    def handle_data(self, data: str) -> None:
        for pre in self._pre_sources:
            pre["source"] += data
        for container in self._markmap_containers:
            container["source"] += data
        if self._component_source:
            self._component_json += data
        if self._in_action_manifest:
            self.action_manifest += data
        if self._in_style:
            self.inline_css_sources.append(data)
            self.inline_css_http_resources.extend(css_http_resources(data))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "pre" and self._pre_sources:
            pre = self._pre_sources.pop()
            if pre["markmap"]:
                self._markmap_sources.append(pre["source"])
        for container in self._markmap_containers[:]:
            if tag == container["tag"]:
                container["depth"] -= 1
                if not container["depth"]:
                    self._markmap_sources.append(container["source"])
                    self._markmap_containers.remove(container)
        if tag == "script" and self._component_source:
            self._check_component_payload()
            self._component_source = ""
            self._component_json = ""
        if tag == "script" and self._in_action_manifest:
            self._in_action_manifest = False
        if tag == "style":
            self._in_style = False
        if tag == "svg" and self._svg_depth:
            self._svg_depth -= 1
        if tag in {"audio", "video"}:
            if self._media_elements and self._media_elements[-1] == tag:
                self._media_elements.pop()
            elif self._media_elements:
                self.authored_violations.append(
                    f"mismatched </{tag}> inside <{self._media_elements[-1]}>"
                )
            else:
                self.authored_violations.append(
                    f"unmatched </{tag}>"
                )
        if tag in {"main", "article"} and self._content_depth:
            self._content_depth -= 1

    def _check_markmap_sources(self) -> None:
        if self._markmap_checked:
            return
        self._markmap_checked = True
        # Only the native enabled runtime turns these code sources into HTML.
        enabled = any(tag == "script" and attribute == "src" and re.search(
            r"/(?:third_party/markmap/markmap-autoloader|js/chunks/markmap-[^/]+)[^/]*\.js$",
            urllib.parse.urlsplit(url).path) for tag, attribute, url in self.resources)
        if not enabled:
            return
        self.authored_violations.extend(self._markmap_carrier_errors)
        for source in self._markmap_sources:
            lines = source.splitlines()
            if lines and lines[0].strip() == "---":
                end = next((index for index in range(1, len(lines)) if lines[index].strip() in {"---", "..."}), None)
                header = lines[1:end] if end is not None else lines[1:]
                allowed = all(not line.strip() or line.lstrip().startswith("#") or
                              re.fullmatch(r"markmap:\s*(?:#.*)?", line) or
                              re.fullmatch(r"  spacingHorizontal:\s*(?:\d+(?:\.\d*)?|\.\d+)\s*(?:#.*)?", line)
                              for line in header)
                roots = sum(bool(re.fullmatch(r"markmap:\s*(?:#.*)?", line)) for line in header)
                spacing_values = [re.match(r"  spacingHorizontal:\s*((?:\d+(?:\.\d*)?|\.\d+))", line)[1]
                                  for line in header if re.match(r"  spacingHorizontal:\s*((?:\d+(?:\.\d*)?|\.\d+))", line)]
                spacing_valid = all(finite_json_number(float(value)) for value in spacing_values)
                if end is None or not allowed or roots != 1 or len(spacing_values) > 1 or not spacing_valid:
                    self.authored_violations.append("Markmap plain-text policy permits only numeric markmap.spacingHorizontal frontmatter")
                lines = lines[end + 1:] if end is not None else []
            # MarkdownIt keeps inline/fenced code inert. Preserve that property
            # instead of mistaking a displayed image example for active markup.
            ordinary = []
            fence = None
            for line in lines:
                if fence:
                    if re.fullmatch(r" {0,3}" + re.escape(fence[0]) + "{" + str(fence[1]) + r",}\s*", line):
                        fence = None
                    continue
                opening = re.match(r" {0,3}(`{3,}|~{3,})", line)
                if opening:
                    fence = (opening[1][0], len(opening[1]))
                else:
                    ordinary.append(line)
            body = "\n".join(ordinary)
            body = re.sub(r"(?<!`)(`+)(?!`)[\s\S]*?\1(?!`)", "", body)
            # Consume Markdown escapes pairwise: an escaped bang/bracket is
            # literal, while an escaped backslash followed by ![ is active.
            body = re.sub(r"\\([!\\<>\[\]()])", " ", body)
            if ("![" in body or re.search(r"<[A-Za-z!/][^>]*>", body) or
                    re.search(r"\[[^\]\n]*\]\s*(?:\(|\[)", body) or
                    re.search(r"(?m)^ {0,3}\[[^\]\n]+\]:", body)):
                self.authored_violations.append("Markmap is limited to plain-text outlines; images, links and raw HTML are forbidden")

    def _check_component_payload(self) -> None:
        try:
            payload = json.loads(self._component_json)
        except (ValueError, RecursionError):
            self.authored_violations.append("invalid OINK component JSON payload")
            return
        if not isinstance(payload, dict):
            self.authored_violations.append("OINK component JSON payload must be an object")
            return
        label_fields = OINK_READER_LABEL_FIELDS.get(self._component_source)
        if label_fields is not None:
            if set(payload) != label_fields or any(not isinstance(value, str) for value in payload.values()):
                self.authored_violations.append("OINK reader labels JSON payload does not match the pinned template schema")
            return
        if self._component_source == "data-td-asciinema-config":
            # Trust only the shortcode schema, not the player's much broader
            # API (audioUrl, custom drivers, etc. can initiate other requests).
            option_keys = {"autoPlay", "fit", "loop", "preload", "speed", "startAt", "poster", "cols", "rows",
                           "idleTimeLimit", "pauseOnMarkers", "markers"}
            options = payload.get("options")
            if (set(payload) != {"src", "theme", "options"} or not isinstance(payload.get("theme"), str)
                    or not isinstance(options, dict) or set(options) - option_keys):
                self.authored_violations.append("Asciinema JSON payload does not match the OINK shortcode schema")
                return
            for key, value in options.items():
                valid = True
                if key in {"autoPlay", "loop", "preload", "pauseOnMarkers"}:
                    valid = isinstance(value, bool)
                elif key == "fit":
                    valid = isinstance(value, str) and value in {"width", "height", "both", "none"}
                elif key in {"cols", "rows"}:
                    valid = type(value) is int and value > 0
                elif key in {"speed", "startAt", "idleTimeLimit"}:
                    valid = type(value) in {int, float} and value >= 0 and (key != "speed" or value > 0)
                elif key == "poster":
                    # The pinned player _parsePoster accepts terminal text or a
                    # recording timestamp; it does not load an image/URL.
                    valid = isinstance(value, str) and value.startswith(("npt:", "data:text/plain,"))
                elif key == "markers":
                    # Hugo append flattens the shortcode's [time, label] slices.
                    valid = (isinstance(value, list) and len(value) % 2 == 0 and
                             all(type(value[index]) in {int, float} and value[index] >= 0 and
                                 isinstance(value[index + 1], str) for index in range(0, len(value), 2)))
                if not valid:
                    self.authored_violations.append(f"invalid Asciinema shortcode option: {key}")
            source = payload.get("src")
            if not isinstance(source, str) or not source:
                self.authored_violations.append("Asciinema JSON payload requires a source URL")
            else:
                self.resources.append(("asciinema-config", "src", source))
                self.urls.append(("src", source))
            return
        # Match ECharts 6.1 sinks by option path. Arbitrary dataset columns
        # (including names such as url/image/formatter) remain inert data.
        pending = [((), option) for option in echarts_option_roots(payload)]
        while pending:
            path, value = pending.pop()
            if path[:1] == ("dataset",) and "source" in path:
                continue
            option_path = tuple(part for part in path if part != "[]")
            text_style_sink = option_path[-3:-1] == ("tooltip", "textStyle") or (option_path[:1] == ("textStyle",) and len(option_path) == 2)
            # Series/item string tooltip shorthand becomes {formatter: value}
            # in ECharts' model; dataset columns were excluded above.
            if option_path[:1] == ("series",) and option_path[-1:] == ("tooltip",) and isinstance(value, str):
                self._check_component_html(value)
                continue
            marker_color_sink = option_path in {
                ("color",), ("colorLayer",), ("series", "color"), ("series", "colorLayer"),
                ("visualMap", "inRange", "color"), ("visualMap", "outOfRange", "color"), ("visualMap", "pieces", "color"),
            } or (option_path[:1] == ("series",) and option_path[-2:] in {("itemStyle", "color"), ("lineStyle", "color")})
            if marker_color_sink and not echarts_marker_color(value):
                self.authored_violations.append("invalid ECharts tooltip marker colour: " + ".".join(option_path))
                continue
            color_sink = option_path[-2:] in {
                ("tooltip", "backgroundColor"), ("tooltip", "borderColor"), ("tooltip", "defaultBorderColor"), ("tooltip", "shadowColor"),
            } or (text_style_sink and option_path[-1] in {"color", "textShadowColor"}) or option_path in {
                ("toolbox", "feature", "dataView", "buttonColor"),
                ("toolbox", "feature", "dataView", "buttonTextColor"),
            }
            if color_sink and value is not None:
                # Tooltip border gradients use their first stop via Nf(). A
                # background gradient becomes inert [object Object] in HTML.
                gradient = (isinstance(value, dict) and isinstance(value.get("colorStops"), list) and
                            all(isinstance(stop, dict) and echarts_css_color(stop.get("color"))
                                for stop in value["colorStops"]))
                if not echarts_css_color(value) and not gradient:
                    self.authored_violations.append("invalid ECharts CSS colour: " + ".".join(option_path))
                    continue
            # NY() constructs tooltip cssText from these numeric and font
            # fields. Apply their declared types before browser coercion.
            tooltip_number = option_path[-2:] in {
                ("tooltip", key) for key in ("shadowBlur", "shadowOffsetX", "shadowOffsetY", "borderWidth", "borderRadius", "padding")
            } or (text_style_sink and option_path[-1] in {
                "fontSize", "lineHeight", "textShadowBlur", "textShadowOffsetX", "textShadowOffsetY"
            })
            if tooltip_number and value is not None:
                numbers = value if isinstance(value, list) and option_path[-1] in {"padding", "borderRadius"} else [value]
                if not numbers or not all(finite_json_number(number) for number in numbers):
                    self.authored_violations.append("ECharts tooltip CSS number must be finite: " + ".".join(option_path))
                    continue
            if text_style_sink and value is not None:
                key = option_path[-1]
                font_valid = True
                if key == "fontFamily":
                    # Match quoted families or identifier-word families, not
                    # arbitrary CSS text; supports Unicode family names.
                    family = r"(?:[\w+-]+(?:[ ]+[\w+-]+)*|'[\w +\-]+'|\"[\w +\-]+\")"
                    font_valid = isinstance(value, str) and bool(re.fullmatch(family + r"(?:\s*,\s*" + family + r")*", value.strip()))
                elif key == "fontStyle":
                    font_valid = isinstance(value, str) and value in {"normal", "italic", "oblique"}
                elif key == "fontWeight":
                    font_valid = ((finite_json_number(value)) or
                                  (isinstance(value, str) and (value in {"normal", "bold", "bolder", "lighter"} or
                                                            bool(re.fullmatch(r"(?:[1-9][0-9]{0,2}|1000)", value)))))
                elif key == "decoration":
                    font_valid = isinstance(value, str) and value in {"none", "underline", "overline", "line-through"}
                elif key == "align":
                    font_valid = isinstance(value, str) and value in {"left", "right", "center", "justify", "start", "end"}
                if not font_valid:
                    self.authored_violations.append("invalid ECharts tooltip CSS font option: " + ".".join(option_path))
                    continue
            navigation_sink = ((option_path[:1] == ("title",) and option_path[-1:] in {("link",), ("sublink",)}) or
                               (option_path[:1] == ("series",) and "data" in path and option_path[-1:] == ("link",)))
            string_sink = navigation_sink or option_path[-2:] in {
                ("tooltip", "formatter"), ("tooltip", "extraCssText"),
            } or option_path == ("toolbox", "feature", "dataView", "title")
            if option_path == ("toolbox", "feature", "saveAsImage", "lang"):
                # Its legacy fallback interpolates lang into an HTML attribute.
                self.authored_violations.append("custom ECharts saveAsImage.lang is unsupported")
                continue
            if option_path == ("toolbox", "feature", "dataView", "lang") and "[]" not in path[-1:]:
                if not isinstance(value, list) or not all(isinstance(label, str) for label in value):
                    self.authored_violations.append("ECharts dataView.lang requires a list of strings")
                    continue
            # Browser DOM APIs coerce arrays/objects to strings. Do not let an
            # alternate JSON type bypass checks at a known string-valued sink.
            if string_sink and not isinstance(value, str):
                self.authored_violations.append("ECharts string option requires a string: " + ".".join(option_path))
                continue
            if isinstance(value, dict):
                pending.extend((path + (key,), child) for key, child in value.items()
                               if path or key not in {"baseOption", "options", "media"})
            elif isinstance(value, list):
                pending.extend((path + ("[]",), child) for child in value)
            elif isinstance(value, str):
                key = option_path[-1]
                resource = None
                if key in {"symbol", "icon"} and value.startswith("image://"):
                    resource = value[len("image://"):]
                elif key == "image" and ("graphic" in path or any(part in path for part in {"backgroundColor", "color", "fill", "stroke"})):
                    resource = value
                if resource:
                    self.resources.append(("echarts-options", "resource", resource))
                    self.urls.append(("src", resource))
                if navigation_sink:
                    self.navigation_urls.append(("a", "href", value))
                    self.urls.append(("href", value))
                if option_path[-2:] == ("tooltip", "extraCssText"):
                    self.inline_css_sources.append(value)
                    self.inline_css_http_resources.extend(css_http_resources(value))
                html_sink = option_path[-2:] == ("tooltip", "formatter") or option_path in {
                    ("toolbox", "feature", "dataView", "lang"),
                    ("toolbox", "feature", "dataView", "title"),
                }
                if html_sink:
                    self._check_component_html(value)

    def _check_component_html(self, value: str) -> None:
        if "data-hg-authored-content" in value.lower():
            self.authored_violations.append("ECharts HTML cannot contain authored-content markers")
        fragment = DocumentParser()
        fragment.feed('<template data-hg-authored-content="start"></template>' + value +
                      '<template data-hg-authored-content="end"></template>')
        self.authored_violations.extend(fragment.authored_violations)
        if fragment._content_markers[0] != fragment._content_markers[1]:
            self.authored_violations.append("unbalanced ECharts HTML content markers")
        self.resources.extend(fragment.resources)
        self.urls.extend(fragment.urls)
        self.navigation_urls.extend(fragment.navigation_urls)
        self.resources.extend(("echarts-options", "resource", resource) for _, _, resource in fragment.image_urls)
        self.image_urls.extend(fragment.image_urls)
        self.inline_css_sources.extend(fragment.inline_css_sources)
        self.inline_css_http_resources.extend(fragment.inline_css_http_resources)


def output_path(root: pathlib.Path, url_path: str) -> pathlib.Path:
    decoded = urllib.parse.unquote(url_path)
    if "\x00" in decoded or "\\" in decoded:
        raise ValueError("contains a NUL or backslash")
    if ".." in pathlib.PurePosixPath(decoded).parts:
        raise ValueError("contains a parent-directory segment")
    relative = decoded.lstrip("/")
    candidate = root / relative
    if decoded.endswith("/") or not pathlib.PurePosixPath(decoded).suffix:
        candidate = candidate / "index.html"
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("escapes the output directory") from exc
    return candidate


def page_url_path(root: pathlib.Path, page: pathlib.Path) -> str:
    relative = page.relative_to(root).as_posix()
    if relative == "index.html":
        return "/"
    if relative.endswith("/index.html"):
        return "/" + relative.removesuffix("index.html")
    return "/" + relative


def internal_output_target(
    root: pathlib.Path, base_parts: urllib.parse.SplitResult, url: str
) -> pathlib.Path | None:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme.lower() not in {"", "http", "https"}:
        raise ValueError(f"forbidden URL scheme: {url}")
    if parts.netloc and parts.netloc != base_parts.netloc:
        return None
    return output_path(root, parts.path or "/")


def css_internal_output_target(
    root: pathlib.Path,
    stylesheet: pathlib.Path,
    base_parts: urllib.parse.SplitResult,
    url: str,
) -> pathlib.Path | None:
    """Resolve one same-origin CSS request against its emitted stylesheet."""

    parts = urllib.parse.urlsplit(url)
    if parts.netloc and parts.netloc != base_parts.netloc:
        return None
    decoded = urllib.parse.unquote(parts.path)
    if not decoded:
        return None if parts.fragment else stylesheet
    if "\x00" in decoded or "\\" in decoded:
        raise ValueError("contains a NUL or backslash")

    if decoded.startswith("/"):
        artifact_base = urllib.parse.unquote(base_parts.path).rstrip("/")
        if artifact_base and (
            decoded == artifact_base or decoded.startswith(artifact_base + "/")
        ):
            decoded = decoded[len(artifact_base) :] or "/"
        candidate = root / decoded.lstrip("/")
    else:
        candidate = stylesheet.parent / decoded
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("escapes output directory") from exc
    if decoded.endswith("/") or (
        not candidate.is_file() and not pathlib.PurePosixPath(decoded).suffix
    ):
        candidate /= "index.html"
    return candidate


def refresh_target(parser: DocumentParser) -> str | None:
    refresh = [
        item.get("content", "")
        for item in parser.meta
        if item.get("http-equiv", "").lower() == "refresh"
    ]
    if not refresh:
        return None
    if len(refresh) != 1:
        raise ValueError(f"expected one refresh directive, found {len(refresh)}")
    match = re.search(r"(?:^|;)\s*url\s*=\s*(.+)\s*$", refresh[0], re.IGNORECASE)
    if not match:
        raise ValueError(f"malformed refresh directive: {refresh[0]}")
    return match.group(1).strip(" \"'")


def rendered_url_shape_error(
    value: str,
    page_name: str,
    attribute: str,
    *,
    allow_contact: bool = False,
) -> str | None:
    """Reject URL spellings that browsers and RFC parsers interpret differently."""
    if any(
        char.isspace() or ord(char) < 0x20 or ord(char) == 0x7F for char in value
    ):
        return (
            f"{page_name}: unsafe whitespace/control URL in {attribute}: {value}"
        )
    if "\\" in value:
        return f"{page_name}: unsafe backslash URL in {attribute}: {value}"
    if value.startswith("//"):
        return f"{page_name}: protocol-relative {attribute} is forbidden: {value}"
    try:
        parts = urllib.parse.urlsplit(value)
    except ValueError as exc:
        return f"{page_name}: malformed URL in {attribute}: {value}: {exc}"
    if parts.scheme.lower() in {"http", "https"} and not parts.netloc:
        return f"{page_name}: HTTP(S) URL has no authority in {attribute}: {value}"
    allowed_schemes = {"", "http", "https"}
    if allow_contact:
        allowed_schemes.update({"mailto", "tel"})
    if parts.scheme.lower() not in allowed_schemes:
        return f"{page_name}: forbidden URL scheme in {attribute}: {value}"
    return None


def document_url_shape_errors(
    parser: DocumentParser,
    page_name: str,
) -> list[str]:
    """Apply the browser-safe URL shape contract to every rendered URL token."""
    tokens: list[tuple[str, str, bool]] = [
        (f"{tag}[{attribute}]", value, tag in {"a", "area"})
        for tag, attribute, value in parser.navigation_urls
    ]
    tokens.extend(
        (f"{tag}[{attribute}]", value, False)
        for tag, attribute, value in parser.resources
    )
    tokens.extend(
        ("inline CSS", value, False)
        for source in parser.inline_css_sources
        for value in css_resource_urls(source)
    )
    try:
        alias_target = refresh_target(parser)
    except ValueError as exc:
        return [f"{page_name}: {exc}"]
    if alias_target:
        tokens.append(("meta refresh", alias_target, False))

    errors = []
    seen: set[tuple[str, str, bool]] = set()
    for attribute, value, allow_contact in tokens:
        key = (attribute, value, allow_contact)
        if key in seen:
            continue
        seen.add(key)
        error = rendered_url_shape_error(
            value,
            page_name,
            attribute,
            allow_contact=allow_contact,
        )
        if error:
            errors.append(error)
    return errors


def parse_and_check_page_security(
    page: pathlib.Path,
    root: pathlib.Path,
    base_parts: urllib.parse.SplitResult,
    error_paths: set[str],
) -> tuple[DocumentParser | None, list[str]]:
    parser = DocumentParser()
    try:
        parser.feed(page.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        return None, [f"cannot parse {page.relative_to(root)}: {exc}"]

    page_name = page.relative_to(root).as_posix()
    errors = document_url_shape_errors(parser, page_name)
    if errors:
        return None, errors
    errors.extend(document_security_errors(parser, page_name, base_parts))
    errors.extend(error_document_seo_errors(parser, page_name, error_paths))
    return parser, errors


def page_security_errors(
    page: pathlib.Path,
    root: pathlib.Path,
    base_parts: urllib.parse.SplitResult,
    error_paths: set[str],
) -> list[str]:
    # Keep the parsed document local to the worker instead of serializing it.
    return parse_and_check_page_security(page, root, base_parts, error_paths)[1]


def main() -> int:
    argument_parser = argparse.ArgumentParser(
        description="Validate a generated HugeGraph documentation artifact."
    )
    argument_parser.add_argument("public_dir", type=pathlib.Path)
    argument_parser.add_argument("expected_base_url")
    argument_parser.add_argument(
        "--security-only",
        action="store_true",
        help=(
            "Check rendered active-content, mixed-content, and CSP image "
            "boundaries only; versioning.py validates isolated URL contracts."
        ),
    )
    argument_parser.add_argument(
        "--workers",
        type=int,
        choices=(1, 2),
        default=1,
        help="Number of HTML security-check processes in --security-only mode.",
    )
    args = argument_parser.parse_args()

    root = args.public_dir.resolve()
    base = args.expected_base_url.rstrip("/") + "/"
    base_parts = urllib.parse.urlsplit(base)
    errors: list[str] = []
    try:
        error_paths = error_document_paths(root)
    except ValueError as exc:
        errors.append(str(exc))
        error_paths = set(ERROR_DOCUMENT_PATHS)

    if not root.is_dir():
        errors.append(f"missing output directory: {root}")

    if not args.security_only:
        for relative in REQUIRED_FILES:
            if not (root / relative).is_file():
                errors.append(f"missing required output: {relative}")

    html_files = sorted(root.rglob("*.html")) if root.is_dir() else []
    if not html_files:
        errors.append("no generated HTML files found")
    if not args.security_only:
        for path in sorted(root.rglob("*")):
            if path.is_file() and "_nav" in path.relative_to(root).parts:
                errors.append(
                    f"private Docs navigation route was rendered: {path.relative_to(root)}"
                )
        for search_path in sorted(root.rglob("offline-search-index.*.json")):
            try:
                search_data = json.loads(search_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                errors.append(f"{search_path.relative_to(root)}: cannot parse: {exc}")
                continue
            for item in search_data if isinstance(search_data, list) else []:
                ref = item.get("ref") if isinstance(item, dict) else None
                if isinstance(ref, str) and "/_nav/" in ref.lower():
                    errors.append(
                        f"{search_path.relative_to(root)}: private Docs navigation "
                        f"route leaked into search: {ref}"
                    )

    if args.security_only:
        check_page = partial(
            page_security_errors, root=root, base_parts=base_parts,
            error_paths=error_paths,
        )
        if args.workers == 2 and html_files:
            with ProcessPoolExecutor(max_workers=args.workers) as executor:
                # map preserves sorted page order, including diagnostics.
                for page_errors in executor.map(check_page, html_files):
                    errors.extend(page_errors)
        else:
            for page_errors in map(check_page, html_files):
                errors.extend(page_errors)

    for page in [] if args.security_only else html_files:
        parser, page_errors = parse_and_check_page_security(
            page, root, base_parts, error_paths
        )
        errors.extend(page_errors)
        if parser is None:
            continue
        page_name = page.relative_to(root).as_posix()
        errors.extend(toc_accessibility_errors(parser, page_name))
        try:
            alias_target = refresh_target(parser)
        except ValueError as exc:
            errors.append(f"{page_name}: {exc}")
            alias_target = None
        is_error_document = page_name in error_paths
        if not is_error_document and page_name != "client-go/index.html":
            if len(parser.canonical) != 1:
                errors.append(
                    f"{page_name}: expected one canonical, found {len(parser.canonical)}"
                )
            else:
                if "_print/" in page_name:
                    print_parts = list(pathlib.PurePosixPath(page_name).parts)
                    print_parts.remove("_print")
                    regular_path = pathlib.PurePosixPath(*print_parts).as_posix()
                    if regular_path.endswith("index.html"):
                        regular_path = regular_path.removesuffix("index.html")
                    expected_canonical = urllib.parse.urljoin(base, regular_path)
                elif alias_target:
                    expected_canonical = urllib.parse.urljoin(
                        base, alias_target.lstrip("/")
                    )
                else:
                    expected_canonical = urllib.parse.urljoin(
                        base, page_url_path(root, page).lstrip("/")
                    )
                if parser.canonical[0] != expected_canonical:
                    errors.append(
                        f"{page_name}: canonical {parser.canonical[0]} != "
                        f"{expected_canonical}"
                    )

        if alias_target and page_name != "client-go/index.html":
            try:
                alias_output = internal_output_target(root, base_parts, alias_target)
                if alias_output is None or not alias_output.is_file():
                    errors.append(
                        f"{page_name}: alias target is absent: {alias_target}"
                    )
            except ValueError as exc:
                errors.append(f"{page_name}: unsafe alias target {alias_target}: {exc}")

        is_regular_page = (
            "_print/" not in page_name
            and not is_error_document
            and page_name != "client-go/index.html"
            and not alias_target
        )
        if is_regular_page:
            actual_hreflang = dict(parser.hreflang)
            if len(actual_hreflang) != len(parser.hreflang):
                errors.append(f"{page_name}: duplicate hreflang entries")
            current_path = page_url_path(root, page)
            english_path = (
                current_path.removeprefix("/cn")
                if current_path.startswith("/cn/")
                else current_path
            )
            chinese_path = "/cn/" if english_path == "/" else "/cn" + english_path
            expected_hreflang = {
                "en-US": urllib.parse.urljoin(base, english_path.lstrip("/")),
                "zh-CN": urllib.parse.urljoin(base, chinese_path.lstrip("/")),
            }
            for language, fallback_path in HREFLANG_FALLBACKS.get(
                page_name, {}
            ).items():
                expected_hreflang[language] = urllib.parse.urljoin(
                    base, fallback_path.lstrip("/")
                )
            if actual_hreflang != expected_hreflang:
                errors.append(
                    f"{page_name}: hreflang {actual_hreflang} != {expected_hreflang}"
                )

            if not parser.action_manifest:
                errors.append(f"{page_name}: missing action manifest")
            else:
                try:
                    manifest = json.loads(parser.action_manifest)
                except json.JSONDecodeError as exc:
                    errors.append(f"{page_name}: malformed action manifest: {exc}")
                else:
                    actions = {
                        action.get("id"): action
                        for action in manifest.get("actions", [])
                        if isinstance(action, dict)
                    }
                    for action_id in ("open_chatgpt", "open_claude"):
                        action = actions.get(action_id)
                        if not action:
                            errors.append(f"{page_name}: missing {action_id} boundary")
                            continue
                        placements = action.get("placements", {})
                        if (
                            action.get("available") is not False
                            or action.get("url") != ""
                            or placements.get("page") is not False
                            or placements.get("palette") is not False
                        ):
                            errors.append(
                                f"{page_name}: {action_id} is externally enabled"
                            )

            for _attribute, link_url in parser.urls:
                hostname = (urllib.parse.urlsplit(link_url).hostname or "").lower()
                if hostname in {"chatgpt.com", "claude.ai", "anthropic.com"}:
                    errors.append(
                        f"{page_name}: assistant link is externally enabled: {link_url}"
                    )

        for attribute, raw_url in parser.urls:
            if rendered_url_shape_error(
                raw_url,
                page_name,
                attribute,
                allow_contact=True,
            ):
                continue
            url = raw_url
            lower_url = url.lower()
            if "/_nav/" in lower_url:
                errors.append(
                    f"{page_name}: private Docs navigation route in {attribute}: {url}"
                )
                continue
            if (
                not url
                or url.startswith("#")
                or lower_url.startswith(("mailto:", "tel:"))
            ):
                continue
            parts = urllib.parse.urlsplit(url)
            if parts.scheme and parts.scheme.lower() not in {"http", "https"}:
                errors.append(
                    f"{page_name}: forbidden URL scheme in {attribute}: {url}"
                )
                continue
            if parts.netloc and parts.netloc != base_parts.netloc:
                continue
            resolved_path = parts.path
            if not parts.netloc and not parts.path.startswith("/"):
                resolved_path = urllib.parse.urljoin(
                    page_url_path(root, page), parts.path
                )
            if resolved_path.startswith("/versions/"):
                errors.append(f"{page_name}: unpublished version URL: {url}")
                continue

            try:
                target = output_path(root, resolved_path or page_url_path(root, page))
            except ValueError as exc:
                errors.append(f"{page_name}: unsafe internal {attribute} {url}: {exc}")
                continue
            if not target.is_file():
                errors.append(
                    f"{page_name}: broken internal {attribute} {url} -> "
                    f"{target.relative_to(root)}"
                )

    for stylesheet in sorted(root.rglob("*.css")) if root.is_dir() else []:
        try:
            stylesheet_text = stylesheet.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot parse {stylesheet.relative_to(root)}: {exc}")
            continue
        stylesheet_name = stylesheet.relative_to(root).as_posix()
        shape_errors = [
            error
            for resource in css_resource_urls(stylesheet_text)
            if (
                error := rendered_url_shape_error(
                    resource,
                    stylesheet_name,
                    "CSS resource",
                )
            )
        ]
        errors.extend(shape_errors)
        if shape_errors:
            continue
        for resource in css_http_resources(stylesheet_text):
            errors.append(
                f"{stylesheet.relative_to(root)}: mixed-content CSS resource: {resource}"
            )
        for resource in css_external_resources(stylesheet_text, base_parts):
            errors.append(
                f"{stylesheet.relative_to(root)}: external CSS resource is forbidden: "
                f"{resource}"
            )
        for resource in css_resource_urls(stylesheet_text):
            try:
                target = css_internal_output_target(
                    root, stylesheet, base_parts, resource
                )
            except ValueError as exc:
                errors.append(
                    f"{stylesheet_name}: unsafe internal CSS resource "
                    f"{resource}: {exc}"
                )
                continue
            if target is not None and not target.is_file():
                errors.append(
                    f"{stylesheet_name}: broken internal CSS resource {resource} -> "
                    f"{target.relative_to(root)}"
                )

    if args.security_only:
        if errors:
            print("Generated site security validation failed:")
            for error in errors:
                print(f"- {error}")
            return 1
        print(
            f"Generated site security validation passed: {len(html_files)} HTML "
            f"files, base {base}"
        )
        return 0

    client_go = root / "client-go/index.html"
    if client_go.is_file():
        parser = DocumentParser()
        parser.feed(client_go.read_text(encoding="utf-8"))
        go_import = [
            item.get("content", "")
            for item in parser.meta
            if item.get("name") == "go-import"
        ]
        go_source = [
            item.get("content", "")
            for item in parser.meta
            if item.get("name") == "go-source"
        ]
        if go_import != [
            "hugegraph.apache.org/client-go git https://github.com/apache/hugegraph-toolchain.git"
        ]:
            errors.append("client-go/index.html: go-import metadata changed")
        expected_go_source = (
            "hugegraph.apache.org/client-go https://github.com/apache/hugegraph-toolchain "
            "https://github.com/apache/hugegraph-toolchain/tree/master/hugegraph-client-go{/dir} "
            "https://github.com/apache/hugegraph-toolchain/blob/master/hugegraph-client-go{/dir}/{file}#L{line}"
        )
        if go_source != [expected_go_source]:
            errors.append("client-go/index.html: go-source metadata changed")
        if (
            refresh_target(parser)
            != "https://pkg.go.dev/hugegraph.apache.org/client-go"
        ):
            errors.append("client-go/index.html: refresh target changed")
        client_links = [url for attribute, url in parser.urls if attribute == "href"]
        if client_links != ["https://pkg.go.dev/hugegraph.apache.org/client-go"]:
            errors.append("client-go/index.html: visible redirect link changed")

    for sitemap_name in ("sitemap.xml", "en/sitemap.xml", "cn/sitemap.xml"):
        sitemap = root / sitemap_name
        if not sitemap.is_file():
            continue
        try:
            locations = [
                node.text or ""
                for node in ET.parse(sitemap).iter()
                if node.tag.endswith("loc")
            ]
        except (ET.ParseError, OSError) as exc:
            errors.append(f"{sitemap_name}: cannot parse sitemap: {exc}")
            continue
        if not locations:
            errors.append(f"{sitemap_name}: sitemap has no locations")
        for location in locations:
            if not location.startswith(base):
                errors.append(f"{sitemap_name}: location escapes base: {location}")
                continue
            if sitemap_name == "cn/sitemap.xml" and not urllib.parse.urlsplit(
                location
            ).path.startswith("/cn/"):
                errors.append(f"{sitemap_name}: non-Chinese location: {location}")
            if sitemap_name == "en/sitemap.xml" and urllib.parse.urlsplit(
                location
            ).path.startswith("/cn/"):
                errors.append(
                    f"{sitemap_name}: Chinese location in English sitemap: {location}"
                )
            target = internal_output_target(root, base_parts, location)
            if target is not None and not target.is_file():
                errors.append(f"{sitemap_name}: missing location output: {location}")

    for llms_name in ("llms.txt", "cn/llms.txt"):
        llms = root / llms_name
        if not llms.is_file():
            continue
        for url in re.findall(r"https?://[^)\s]+", llms.read_text(encoding="utf-8")):
            if not url.startswith(base):
                errors.append(f"{llms_name}: URL escapes base: {url}")
                continue
            url_path = urllib.parse.urlsplit(url).path
            if (
                llms_name == "cn/llms.txt"
                and not url_path.startswith("/cn/")
                and url_path != "/index.md"
            ):
                errors.append(f"{llms_name}: non-Chinese URL: {url}")
            if (
                llms_name == "llms.txt"
                and url_path.startswith("/cn/")
                and url_path != "/cn/index.md"
            ):
                errors.append(f"{llms_name}: Chinese URL in English index: {url}")
            target = internal_output_target(root, base_parts, url)
            if target is not None and not target.is_file():
                errors.append(f"{llms_name}: missing URL output: {url}")

    for nav_path in sorted(root.rglob("navigation.json")):
        nav_name = nav_path.relative_to(root).as_posix()
        parts = pathlib.PurePosixPath(nav_name).parts
        language = "cn" if len(parts) >= 2 and parts[-2] == "cn" else "en"
        prefix_parts = parts[:-2] if language == "cn" else parts[:-1]
        nav_base = urllib.parse.urljoin(
            base, "/".join(prefix_parts) + ("/" if prefix_parts else "")
        )
        try:
            nav = json.loads(nav_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"{nav_name}: cannot parse: {exc}")
            continue
        if nav.get("baseURL") != nav_base or nav.get("language") != language:
            errors.append(f"{nav_name}: baseURL or language changed")
        expected_root_url = (
            nav_base if language == "en" else urllib.parse.urljoin(nav_base, "cn/")
        )
        if nav.get("root", {}).get("url") != expected_root_url:
            errors.append(f"{nav_name}: root URL is not language-scoped")
        errors.extend(docs_navigation_errors(nav, nav_name, language))
        pending = [nav]
        while pending:
            item = pending.pop()
            if isinstance(item, dict):
                for key in ("url", "markdown"):
                    value = item.get(key)
                    if not isinstance(value, str):
                        continue
                    resolved_value = urllib.parse.urljoin(nav_base, value)
                    if not resolved_value.startswith(nav_base):
                        errors.append(
                            f"{nav_name}: {key} escapes version base: {value}"
                        )
                        continue
                    url_path = urllib.parse.urlsplit(resolved_value).path
                    nav_path_prefix = urllib.parse.urlsplit(nav_base).path.rstrip("/")
                    chinese_prefix = nav_path_prefix + "/cn/"
                    if language == "cn" and not url_path.startswith(chinese_prefix):
                        errors.append(f"{nav_name}: {key} loses /cn/: {value}")
                    if language == "en" and url_path.startswith(chinese_prefix):
                        errors.append(f"{nav_name}: {key} crosses into /cn/: {value}")
                    target = internal_output_target(root, base_parts, value)
                    if target is not None and not target.is_file():
                        errors.append(f"{nav_name}: missing {key} output: {value}")
                pending.extend(item.values())
            elif isinstance(item, list):
                pending.extend(item)

    if errors:
        print("Generated site validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"Generated site validation passed: {len(html_files)} HTML files, base {base}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
