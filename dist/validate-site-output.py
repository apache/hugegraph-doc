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
import html.parser
import json
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
UNSAFE_AUTHORED_ELEMENTS = {"script", "iframe", "object", "embed"}
ERROR_DOCUMENT_PATHS = {
    "404.html",
    "cn/404.html",
}
DOCS_NAV_GROUP_TITLES = {
    "en": ("Get Started", "Components", "Develop", "Operate", "Reference"),
    "cn": ("开始", "组件", "开发", "运维", "参考"),
}
EXTERNAL_ACTIVE_RESOURCE_ATTRIBUTES = {
    ("script", "src"),
    ("link", "href"),
    ("iframe", "src"),
    ("object", "data"),
    ("embed", "src"),
    ("audio", "src"),
    ("video", "src"),
    ("track", "src"),
}


def is_inert_oink_diagram_source(tag: str, values: dict[str, str]) -> bool:
    """Match only OINK's inert Mermaid source carrier, not authored JSON scripts."""

    return (
        tag == "script"
        and set(values) == {"type", "data-td-diagram-source"}
        and values["type"].strip().lower() == "application/json"
        and values["data-td-diagram-source"] == ""
    )


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
    """Extract CSS url() and quoted @import resources in source order."""
    pattern = re.compile(
        r"url\(\s*(?P<quote>['\"]?)(?P<url>[^'\"\s)]+)(?P=quote)\s*\)"
        r"|@import\s+(?P<import_quote>['\"])(?P<import_url>[^'\"]+)"
        r"(?P=import_quote)",
        re.IGNORECASE,
    )
    return [
        match.group("url") or match.group("import_url")
        for match in pattern.finditer(value)
    ]


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

    errors = [
        f"{page_name}: unsafe content markup: {violation}"
        for violation in parser.authored_violations
    ]
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
        if (tag, attribute) in EXTERNAL_ACTIVE_RESOURCE_ATTRIBUTES
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
        self._content_depth = 0
        self._in_style = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "nav" and "TableOfContents" in [
            value or "" for key, value in attrs if key.lower() == "id"
        ]:
            self.toc_nav_labels.append(
                [value or "" for key, value in attrs if key.lower() == "aria-label"]
            )
        if tag in {"main", "article"}:
            self._content_depth += 1
        if self._content_depth:
            if tag in UNSAFE_AUTHORED_ELEMENTS and not is_inert_oink_diagram_source(
                tag, values
            ):
                self.authored_violations.append(f"authored <{tag}>")
            for attribute in values:
                if attribute.startswith("on"):
                    self.authored_violations.append(
                        f"authored {attribute} event attribute on <{tag}>"
                    )

        if tag in {"a", "link"} and values.get("href"):
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
        if tag == "iframe" and values.get("src"):
            resource_attributes.append(("src", values["src"]))
        if (
            tag == "input"
            and values.get("type", "").lower() == "image"
            and values.get("src")
        ):
            resource_attributes.append(("src", values["src"]))
        if tag == "image" and values.get("href"):
            resource_attributes.append(("href", values["href"]))
        if tag == "link" and values.get("href"):
            rel = set(values.get("rel", "").lower().split())
            if rel & {
                "stylesheet",
                "preload",
                "modulepreload",
                "icon",
                "apple-touch-icon",
                "manifest",
            }:
                resource_attributes.append(("href", values["href"]))
        self.resources.extend(
            (tag, attribute, url) for attribute, url in resource_attributes
        )

        if tag in {"img", "source"}:
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
                    self.resources.extend((tag, attribute, url) for url in urls)
        if tag == "video" and values.get("poster"):
            self.image_urls.append((tag, "poster", values["poster"]))
        if (
            tag == "input"
            and values.get("type", "").lower() == "image"
            and values.get("src")
        ):
            self.image_urls.append((tag, "src", values["src"]))
        if tag == "image" and values.get("href"):
            self.image_urls.append((tag, "href", values["href"]))

        if values.get("style"):
            self.inline_css_sources.append(values["style"])
            self.inline_css_http_resources.extend(css_http_resources(values["style"]))
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
        if tag == "style":
            self._in_style = True

    def handle_data(self, data: str) -> None:
        if self._in_action_manifest:
            self.action_manifest += data
        if self._in_style:
            self.inline_css_sources.append(data)
            self.inline_css_http_resources.extend(css_http_resources(data))

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._in_action_manifest:
            self._in_action_manifest = False
        if tag == "style":
            self._in_style = False
        if tag in {"main", "article"} and self._content_depth:
            self._content_depth -= 1


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
    return None


def document_url_shape_errors(
    parser: DocumentParser,
    page_name: str,
) -> list[str]:
    """Apply the browser-safe URL shape contract to every rendered URL token."""
    tokens: list[tuple[str, str]] = list(parser.urls)
    tokens.extend(
        (f"{tag}[{attribute}]", value)
        for tag, attribute, value in parser.resources
    )
    tokens.extend(
        ("inline CSS", value)
        for source in parser.inline_css_sources
        for value in css_resource_urls(source)
    )
    try:
        alias_target = refresh_target(parser)
    except ValueError as exc:
        return [f"{page_name}: {exc}"]
    if alias_target:
        tokens.append(("meta refresh", alias_target))

    errors = []
    seen: set[tuple[str, str]] = set()
    for attribute, value in tokens:
        key = (attribute, value)
        if key in seen:
            continue
        seen.add(key)
        error = rendered_url_shape_error(value, page_name, attribute)
        if error:
            errors.append(error)
    return errors


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

    for page in html_files:
        parser = DocumentParser()
        try:
            parser.feed(page.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot parse {page.relative_to(root)}: {exc}")
            continue

        page_name = page.relative_to(root).as_posix()
        shape_errors = document_url_shape_errors(parser, page_name)
        errors.extend(shape_errors)
        if shape_errors:
            continue
        errors.extend(document_security_errors(parser, page_name, base_parts))
        errors.extend(error_document_seo_errors(parser, page_name, error_paths))
        if args.security_only:
            continue
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
            if rendered_url_shape_error(raw_url, page_name, attribute):
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
