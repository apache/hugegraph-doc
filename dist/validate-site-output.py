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

import html.parser
import json
import pathlib
import re
import sys
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
    "licenses/oink/LICENSE",
    "licenses/oink/NOTICE",
    "licenses/oink/VENDOR.json",
)

HREFLANG_FALLBACKS = {
    # The English release note is intentionally draft-only.
    "cn/docs/changelog/hugegraph-0.12.0-release-notes/index.html": {"en-US": "/"},
    # This community page currently has no Chinese source counterpart.
    "community/maturity/index.html": {"zh-CN": "/cn/"},
}

class DocumentParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.urls: list[tuple[str, str]] = []
        self.canonical: list[str] = []
        self.hreflang: list[tuple[str, str]] = []
        self.meta: list[dict[str, str]] = []
        self.action_manifest = ""
        self._in_action_manifest = False

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag in {"a", "link"} and values.get("href"):
            self.urls.append(("href", values["href"]))
        if tag in {"img", "script", "source"} and values.get("src"):
            self.urls.append(("src", values["src"]))
        if tag == "link" and values.get("rel", "").lower() == "canonical":
            self.canonical.append(values.get("href", ""))
        if tag == "link" and values.get("rel", "").lower() == "alternate" and values.get("hreflang"):
            self.hreflang.append((values["hreflang"], values.get("href", "")))
        if tag == "meta":
            self.meta.append(values)
        if tag == "script" and values.get("id") == "td-action-manifest":
            self._in_action_manifest = True

    def handle_data(self, data: str) -> None:
        if self._in_action_manifest:
            self.action_manifest += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._in_action_manifest:
            self._in_action_manifest = False


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


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: validate-site-output.py PUBLIC_DIR EXPECTED_BASE_URL")
        return 2

    root = pathlib.Path(sys.argv[1]).resolve()
    base = sys.argv[2].rstrip("/") + "/"
    base_parts = urllib.parse.urlsplit(base)
    errors: list[str] = []

    if not root.is_dir():
        errors.append(f"missing output directory: {root}")

    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing required output: {relative}")

    vendor_manifest = root / "licenses/oink/VENDOR.json"
    if vendor_manifest.is_file():
        try:
            vendor = json.loads(vendor_manifest.read_text(encoding="utf-8"))
            license_files = {
                license_path
                for dependency in vendor.get("dependencies", [])
                for license_path in dependency.get("licenseFiles", [])
            }
            for license_path in sorted(license_files):
                if not (root / "licenses/oink" / license_path).is_file():
                    errors.append(f"missing OINK dependency license: {license_path}")
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"cannot parse licenses/oink/VENDOR.json: {exc}")

    html_files = sorted(root.rglob("*.html")) if root.is_dir() else []
    if not html_files:
        errors.append("no generated HTML files found")

    for page in html_files:
        parser = DocumentParser()
        try:
            parser.feed(page.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot parse {page.relative_to(root)}: {exc}")
            continue

        page_name = page.relative_to(root).as_posix()
        try:
            alias_target = refresh_target(parser)
        except ValueError as exc:
            errors.append(f"{page_name}: {exc}")
            alias_target = None
        if page_name not in {"404.html", "cn/404.html", "client-go/index.html"}:
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
                    errors.append(f"{page_name}: alias target is absent: {alias_target}")
            except ValueError as exc:
                errors.append(f"{page_name}: unsafe alias target {alias_target}: {exc}")

        is_regular_page = (
            "_print/" not in page_name
            and page_name not in {"404.html", "cn/404.html", "client-go/index.html"}
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
            for language, fallback_path in HREFLANG_FALLBACKS.get(page_name, {}).items():
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
                            errors.append(f"{page_name}: {action_id} is externally enabled")

            for _attribute, link_url in parser.urls:
                hostname = (urllib.parse.urlsplit(link_url).hostname or "").lower()
                if hostname in {"chatgpt.com", "claude.ai", "anthropic.com"}:
                    errors.append(f"{page_name}: assistant link is externally enabled: {link_url}")

        for attribute, raw_url in parser.urls:
            url = raw_url.strip()
            lower_url = url.lower()
            if not url or url.startswith("#") or lower_url.startswith(("mailto:", "tel:")):
                continue
            if url.startswith("//"):
                errors.append(f"{page_name}: protocol-relative {attribute} is forbidden: {url}")
                continue

            parts = urllib.parse.urlsplit(url)
            if parts.scheme and parts.scheme.lower() not in {"http", "https"}:
                errors.append(f"{page_name}: forbidden URL scheme in {attribute}: {url}")
                continue
            if parts.netloc and parts.netloc != base_parts.netloc:
                continue
            resolved_path = parts.path
            if not parts.netloc and not parts.path.startswith("/"):
                resolved_path = urllib.parse.urljoin(page_url_path(root, page), parts.path)
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

    client_go = (root / "client-go/index.html")
    if client_go.is_file():
        parser = DocumentParser()
        parser.feed(client_go.read_text(encoding="utf-8"))
        go_import = [item.get("content", "") for item in parser.meta if item.get("name") == "go-import"]
        go_source = [item.get("content", "") for item in parser.meta if item.get("name") == "go-source"]
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
        if refresh_target(parser) != "https://pkg.go.dev/hugegraph.apache.org/client-go":
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
                node.text or "" for node in ET.parse(sitemap).iter() if node.tag.endswith("loc")
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
            if sitemap_name == "cn/sitemap.xml" and not urllib.parse.urlsplit(location).path.startswith("/cn/"):
                errors.append(f"{sitemap_name}: non-Chinese location: {location}")
            if sitemap_name == "en/sitemap.xml" and urllib.parse.urlsplit(location).path.startswith("/cn/"):
                errors.append(f"{sitemap_name}: Chinese location in English sitemap: {location}")
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

    for nav_name, language in (("navigation.json", "en"), ("cn/navigation.json", "cn")):
        nav_path = root / nav_name
        if not nav_path.is_file():
            continue
        try:
            nav = json.loads(nav_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"{nav_name}: cannot parse: {exc}")
            continue
        if nav.get("baseURL") != base or nav.get("language") != language:
            errors.append(f"{nav_name}: baseURL or language changed")
        expected_root_url = base if language == "en" else urllib.parse.urljoin(base, "cn/")
        if nav.get("root", {}).get("url") != expected_root_url:
            errors.append(f"{nav_name}: root URL is not language-scoped")
        pending = [nav]
        while pending:
            item = pending.pop()
            if isinstance(item, dict):
                for key in ("url", "markdown"):
                    value = item.get(key)
                    if not isinstance(value, str):
                        continue
                    if not value.startswith(base):
                        errors.append(f"{nav_name}: {key} escapes base: {value}")
                        continue
                    url_path = urllib.parse.urlsplit(value).path
                    if language == "cn" and not url_path.startswith("/cn/"):
                        errors.append(f"{nav_name}: {key} loses /cn/: {value}")
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
