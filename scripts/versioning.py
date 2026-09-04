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

"""Resolve, build, and aggregate centrally rendered HugeGraph versions."""

from __future__ import annotations

import argparse
import hashlib
import html
import html.parser
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
from typing import NoReturn


ROOT = pathlib.Path(__file__).resolve().parents[1]
URL_CONTRACT = ROOT / "dist/url-contract.json"
CANONICAL_ORIGIN = "https://hugegraph.apache.org/"
SHELL_FILES = ("go.mod", "go.sum", "hugo.yaml")
SHELL_DIRS = ("assets", "data", "i18n", "layouts")
SHELL_CONTENT_DIRS = (
    "content/en/docs/_nav",
    "content/cn/docs/_nav",
)
SHELL_STATIC_FILES = ("favicon.svg",)
SHELL_CONTENT = (
    "content/en/_index.md",
    "content/cn/_index.md",
    "content/en/about/_index.md",
    "content/cn/about/_index.md",
    "content/en/docs/SUMMARY.md",
    "content/cn/docs/SUMMARY.md",
)
MENU_CONTENT = tuple(
    f"content/{language}/{section}/_index.md"
    for language in ("en", "cn")
    for section in ("docs", "blog", "community")
)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY_URL = "https://github.com/apache/hugegraph-doc.git"
VERSION_REFS = {
    "latest": "master",
    "1.7": "release-1.7.0",
    "1.5": "release-1.5.0",
    "1.3": "release-1.3.0",
    "1.0": "release-1.0.0",
}
VERSION_ORDER = ("latest", "1.7", "1.5", "1.3", "1.0")
KNOWN_HISTORICAL_ROUTES = {
    "/docs/quickstart/hugegraph-loader": "/docs/quickstart/toolchain/hugegraph-loader/",
    "/cn/docs/quickstart/hugegraph-loader": "/cn/docs/quickstart/toolchain/hugegraph-loader/",
}
KNOWN_HISTORICAL_ROUTES_BY_PUBLISH_PATH = {
    "versions/1.5": {
        "/docs/introduction": "/docs/introduction/readme/",
        "/cn/docs/introduction": "/cn/docs/introduction/readme/",
    },
}
LATEST_SHARED_DOC_ROUTES = {
    "/docs/guides/security/",
    "/cn/docs/guides/security/",
}
URL_ATTRIBUTE_RE = re.compile(
    r"(?P<prefix>[\s<](?:href|src|action|poster|data-td-index-src|data-td-url|data-td-image-zoom)=)"
    r"(?P<quote>[\"']?)(?P<url>[^\s\"'<>`]+)(?P=quote)",
    re.IGNORECASE,
)
ACTION_MANIFEST_RE = re.compile(
    r"(?P<open><script\b[^>]*\bid=[\"']?td-action-manifest[\"']?[^>]*>)"
    r"(?P<body>.*?)"
    r"(?P<close></script>)",
    re.IGNORECASE | re.DOTALL,
)
HREFLANG_LINK_RE = re.compile(
    r"<link\b(?=[^>]*\brel=[\"']?alternate(?:[\"'\s>]|$))"
    r"(?=[^>]*\bhreflang=)[^>]*>",
    re.IGNORECASE,
)
ROBOTS_META_RE = re.compile(
    r"<meta\b(?=[^>]*\bname=[\"']?robots(?:[\"'\s>]|$))[^>]*>",
    re.IGNORECASE,
)
MARKDOWN_DESTINATION_RE = re.compile(
    r"(?P<open>\]\(\s*<?)(?P<url>(?:https?://[^\s)>]+|/[^\s)>]+))(?P<close>>?[^)]*\))"
)
HREFLANG_FALLBACKS = {
    "cn/docs/changelog/hugegraph-0.12.0-release-notes/index.html": {"en-US": "/"},
    "community/maturity/index.html": {"zh-CN": "/cn/"},
}
LANGUAGE_OPTION_TITLES = {"en-US": "English", "zh-CN": "简体中文"}
DOCS_NAV_GROUP_IDS = ("start", "components", "develop", "operate", "reference")
DOCS_NAV_GROUP_TITLES = {
    "en": ("Get Started", "Components", "Develop", "Operate", "Reference"),
    "cn": ("开始", "组件", "开发", "运维", "参考"),
}
DOCS_NAV_EXPECTED_STATS = {
    "latest": {
        "groups": 5,
        "pages": 86,
        "removed": 4,
        "scopedLinks": 0,
        "treeSha256": "b252d700e9547f7468410edde28de6659018cdb0b2b0b379c125a32c3f802b79",
    },
    "1.7": {
        "groups": 5,
        "pages": 85,
        "removed": 5,
        "scopedLinks": 10,
        "treeSha256": "78abae8934d1245bd9b18754547d23a328506b22db4a1e6e8e9e38e94818df57",
    },
    "1.5": {
        "groups": 5,
        "pages": 77,
        "removed": 13,
        "scopedLinks": 10,
        "treeSha256": "70b2a46f047b3c88a6b1b937eb79676a7f68437485b3248e5f84b9c621d5ad06",
    },
    "1.3": {
        "groups": 5,
        "pages": 68,
        "removed": 22,
        "scopedLinks": 10,
        "treeSha256": "78700dfe484d5177f00c9fe657ae12f3ceecca9bbb592cc8626b782a7b9be61a",
    },
    "1.0": {
        "groups": 5,
        "pages": 59,
        "removed": 21,
        "scopedLinks": 10,
        "treeSha256": "52f0c3b5bef6e9db39a37bbd52b7993128951f592d88a835ec7e3c107edec399",
    },
}
LEGACY_IA_ROUTE_MAP = {
    "introduction/README.md": "introduction/readme.md",
    "quickstart/hugegraph-server.md": "quickstart/hugegraph/hugegraph-server.md",
    "quickstart/hugegraph-hubble.md": "quickstart/toolchain/hugegraph-hubble.md",
    "quickstart/hugegraph-loader.md": "quickstart/toolchain/hugegraph-loader.md",
    "quickstart/hugegraph-tools.md": "quickstart/toolchain/hugegraph-tools.md",
    "quickstart/hugegraph-computer.md": "quickstart/computing/hugegraph-computer.md",
    "quickstart/hugegraph-client.md": "quickstart/client/hugegraph-client.md",
}
LEGACY_IA_SECTIONS = {
    "quickstart/hugegraph": ("HugeGraph", "HugeGraph"),
    "quickstart/toolchain": ("Toolchain", "Toolchain"),
    "quickstart/computing": ("Graph computing", "图计算"),
    "quickstart/client": ("Clients", "客户端"),
}


class DocumentParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.urls: list[tuple[str, str]] = []
        self.canonical: list[str] = []
        self.hreflang: list[tuple[str, str]] = []
        self.meta: list[dict[str, str]] = []
        self.toc_nav_labels: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "nav" and "TableOfContents" in [
            value or "" for key, value in attrs if key.lower() == "id"
        ]:
            self.toc_nav_labels.append(
                [value or "" for key, value in attrs if key.lower() == "aria-label"]
            )
        for attribute in (
            "href",
            "src",
            "action",
            "poster",
            "data-td-index-src",
            "data-td-url",
            "data-td-image-zoom",
        ):
            if values.get(attribute):
                self.urls.append((attribute, values[attribute]))
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


def refresh_target(parser: DocumentParser) -> str | None:
    refresh = [
        item.get("content", "")
        for item in parser.meta
        if item.get("http-equiv", "").lower() == "refresh"
    ]
    if not refresh:
        return None
    if len(refresh) != 1:
        fail(f"expected one refresh directive, found {len(refresh)}")
    match = re.search(r"(?:^|;)\s*url\s*=\s*(.+)\s*$", refresh[0], re.IGNORECASE)
    if not match:
        fail(f"malformed refresh directive: {refresh[0]}")
    return match.group(1).strip(" \"'")


def require_error_document_without_canonical(
    relative: str, canonical_tags: list[str]
) -> bool:
    """Fail closed when a generated error document claims a canonical URL."""
    if relative not in {"404.html", "cn/404.html"}:
        return False
    if canonical_tags:
        fail(f"error document must not declare canonical: {relative}")
    return True


def require_toc_accessible_name(parser: DocumentParser, relative: str) -> None:
    """Require one localized label whenever Hugo renders its page TOC nav."""
    if not parser.toc_nav_labels:
        return
    if len(parser.toc_nav_labels) != 1:
        fail(
            f"expected at most one TableOfContents nav in {relative}, "
            f"found {len(parser.toc_nav_labels)}"
        )
    expected = "目录" if relative.startswith("cn/") else "Content"
    labels = parser.toc_nav_labels[0]
    if labels != [expected]:
        fail(
            f"TableOfContents nav in {relative} must have exactly one localized "
            f"aria-label {expected!r}, found {labels!r}"
        )


def require_safe_url_scheme(value: str, source: str) -> bool:
    """Reject active or ambiguous schemes; return whether target validation applies."""
    if value.startswith("//"):
        fail(f"protocol-relative URL in {source}: {value}")
    scheme = urllib.parse.urlsplit(value).scheme.lower()
    if scheme in {"mailto", "tel"}:
        return False
    if scheme not in {"", "http", "https"}:
        fail(f"forbidden URL scheme in {source}: {value}")
    return True


def fail(message: str) -> NoReturn:
    raise SystemExit(message)


def registered_worktree_roots() -> tuple[pathlib.Path, ...]:
    """Enumerate every checkout sharing this repository, failing closed."""
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain", "-z"],
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        fail(f"cannot enumerate protected Git worktrees: {exc}")
    if result.returncode != 0:
        detail = os.fsdecode(result.stderr).strip()
        fail(f"cannot enumerate protected Git worktrees: {detail or result.returncode}")
    roots = []
    for field in result.stdout.split(b"\0"):
        if not field.startswith(b"worktree "):
            continue
        raw = os.fsdecode(field.removeprefix(b"worktree "))
        path = pathlib.Path(raw)
        if not raw or not path.is_absolute():
            fail(f"invalid Git worktree path: {raw!r}")
        roots.append(path.resolve())
    if not roots:
        fail("cannot enumerate protected Git worktrees: no checkout paths")
    return tuple(roots)


def require_output_outside_git_checkouts(output: pathlib.Path, label: str) -> None:
    """Reject registered, prunable, and unregistered checkout paths."""
    protected = set(registered_worktree_roots())
    protected.add(ROOT.resolve())
    for checkout in protected:
        if (
            output == checkout
            or output in checkout.parents
            or checkout in output.parents
        ):
            fail(f"{label} must be outside every Git checkout: {output}")
    for candidate in (output, *output.parents):
        marker = candidate / ".git"
        if marker.exists() or marker.is_symlink():
            fail(f"{label} must be outside every Git checkout: {output}")


def prepare_output_directory(path: pathlib.Path, label: str) -> pathlib.Path:
    raw = path.expanduser()
    if raw.is_symlink():
        fail(f"{label} must not be a symbolic link: {raw}")
    output = raw.resolve()
    allowed_roots = {
        pathlib.Path(tempfile.gettempdir()).resolve(),
        pathlib.Path("/tmp").resolve(),
    }
    runner_temp = os.environ.get("RUNNER_TEMP")
    if runner_temp:
        allowed_roots.add(pathlib.Path(runner_temp).resolve())
    if not any(root != output and root in output.parents for root in allowed_roots):
        fail(f"{label} must be below a controlled temporary directory: {output}")
    require_output_outside_git_checkouts(output, label)
    if output.exists():
        if output.is_symlink() or not output.is_dir():
            fail(f"{label} is not a removable directory: {output}")
        shutil.rmtree(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def run(command: list[str], *, cwd: pathlib.Path = ROOT) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
    )
    return result.stdout.strip()


def load_manifest(path: pathlib.Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 1:
        fail("versions manifest schemaVersion must be 1")
    versions = data.get("versions")
    if not isinstance(versions, list) or not versions:
        fail("versions manifest must contain a non-empty versions array")
    ids: set[str] = set()
    paths: set[str] = set()
    for entry in versions:
        required = {"id", "name", "ref", "publishPath", "archived", "githubBranch"}
        if not isinstance(entry, dict) or not required.issubset(entry):
            fail(f"invalid version entry: {entry!r}")
        version_id = entry["id"]
        expected_ref = VERSION_REFS.get(version_id)
        if entry["ref"] != expected_ref:
            fail(f"unexpected source ref for {version_id}: {entry['ref']}")
        if entry["githubBranch"] != expected_ref:
            fail(f"unexpected GitHub branch for {version_id}: {entry['githubBranch']}")
        if entry["name"] != version_id:
            fail(f"unexpected display name for {version_id}: {entry['name']}")
        if entry["archived"] is not (version_id != "latest"):
            fail(f"unexpected archive state for {version_id}: {entry['archived']}")
        publish_path = entry["publishPath"].strip("/")
        if version_id in ids or publish_path in paths:
            fail(f"duplicate version id or publish path: {version_id}")
        if version_id == "latest" and publish_path:
            fail("latest must publish at the site root")
        if version_id != "latest" and not publish_path.startswith("versions/"):
            fail(f"historical version {version_id} must publish below versions/")
        if ".." in pathlib.PurePosixPath(publish_path).parts:
            fail(f"unsafe publish path for {version_id}: {publish_path}")
        entry["publishPath"] = publish_path
        ids.add(version_id)
        paths.add(publish_path)
    if tuple(entry["id"] for entry in versions) != VERSION_ORDER:
        fail(f"version order must be {', '.join(VERSION_ORDER)}")
    if data.get("repository") != REPOSITORY_URL:
        fail(f"versions manifest repository must be {REPOSITORY_URL}")
    return data


def load_resolved_manifest(path: pathlib.Path) -> dict:
    resolved = load_manifest(path)
    expected = load_manifest(ROOT / "versions.json")
    if resolved.get("repository") != expected.get("repository"):
        fail("resolved manifest repository does not match versions.json")
    fields = ("id", "name", "ref", "publishPath", "archived", "githubBranch")
    for expected_entry, resolved_entry in zip(
        expected["versions"], resolved["versions"]
    ):
        if any(
            resolved_entry.get(field) != expected_entry.get(field) for field in fields
        ):
            fail(
                f"resolved manifest entry drifted from versions.json: {resolved_entry!r}"
            )
        if not SHA_RE.fullmatch(resolved_entry.get("sha", "")):
            fail(f"resolved manifest has invalid SHA: {resolved_entry!r}")
    return resolved


def require_metadata_matches(entry: dict, metadata: dict, source: pathlib.Path) -> None:
    fields = (
        "id",
        "name",
        "ref",
        "publishPath",
        "archived",
        "githubBranch",
        "sha",
    )
    mismatches = [field for field in fields if metadata.get(field) != entry.get(field)]
    if mismatches:
        fail(f"version metadata mismatch in {source}: {', '.join(mismatches)}")


def resolve_remote(repository: str, ref: str) -> str:
    output = run(["git", "ls-remote", "--heads", repository, f"refs/heads/{ref}"])
    rows = [row.split() for row in output.splitlines() if row.strip()]
    if len(rows) != 1 or len(rows[0]) != 2 or not SHA_RE.fullmatch(rows[0][0]):
        fail(f"cannot resolve exactly one branch SHA for {ref}: {output!r}")
    return rows[0][0]


def selected_version_ids(raw: str | None) -> tuple[str, ...]:
    if raw is None:
        return VERSION_ORDER
    selected = tuple(part.strip() for part in raw.split(",") if part.strip())
    if not selected or len(set(selected)) != len(selected):
        fail("selected versions must be a non-empty unique comma-separated list")
    unknown = set(selected) - set(VERSION_ORDER)
    if unknown:
        fail(f"unknown selected versions: {', '.join(sorted(unknown))}")
    return tuple(version for version in VERSION_ORDER if version in selected)


def prepare(args: argparse.Namespace) -> None:
    manifest = load_manifest(args.manifest)
    selected = selected_version_ids(args.select)
    resolved = []
    for entry in manifest["versions"]:
        item = dict(entry)
        if entry["id"] == "latest":
            sha = run(["git", "rev-parse", f"{args.latest_sha}^{{commit}}"])
        elif args.local:
            sha = run(
                ["git", "rev-parse", f"refs/remotes/origin/{entry['ref']}^{{commit}}"]
            )
        else:
            sha = resolve_remote(manifest["repository"], entry["ref"])
        if not SHA_RE.fullmatch(sha):
            fail(f"resolved value is not a commit SHA for {entry['id']}: {sha}")
        item["sha"] = sha
        resolved.append(item)
    result = {
        "schemaVersion": 1,
        "repository": manifest["repository"],
        "versions": resolved,
        "include": [item for item in resolved if item["id"] in selected],
    }
    rendered = json.dumps(
        result, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


def overlay_shell(assembly: pathlib.Path, *, historical: bool, origin: str) -> None:
    for obsolete in (
        "config.toml",
        "package.json",
        "netlify.toml",
        "deploy.sh",
        ".nvmrc",
    ):
        path = assembly / obsolete
        if path.exists() or path.is_symlink():
            path.unlink()
    for obsolete_dir in (*SHELL_DIRS, "themes", "config"):
        path = assembly / obsolete_dir
        if path.exists():
            shutil.rmtree(path)
    for name in SHELL_FILES:
        shutil.copy2(ROOT / name, assembly / name)
    for name in SHELL_DIRS:
        source = ROOT / name
        if source.exists():
            shutil.copytree(source, assembly / name, dirs_exist_ok=True)
    for relative in SHELL_STATIC_FILES:
        source = ROOT / "static" / relative
        target = assembly / "static" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    client_go_target = assembly / "static/client-go"
    if historical:
        if client_go_target.exists():
            shutil.rmtree(client_go_target)
    else:
        client_go_source = ROOT / "static/client-go"
        if client_go_source.exists():
            shutil.copytree(client_go_source, client_go_target, dirs_exist_ok=True)
    for relative in SHELL_CONTENT:
        if historical and not relative.endswith("docs/SUMMARY.md"):
            continue
        source = ROOT / relative
        target = assembly / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        legacy_html = target.with_suffix(".html")
        if legacy_html.exists():
            legacy_html.unlink()
        shutil.copy2(source, target)
    for relative in SHELL_CONTENT_DIRS:
        source = ROOT / relative
        target = assembly / relative
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
    for relative in MENU_CONTENT:
        strip_menu_frontmatter(assembly / relative)
    if historical:
        prune_historical_content(assembly, origin)


def prune_historical_content(assembly: pathlib.Path, origin: str) -> None:
    """Keep versioned Docs only; shared site surfaces continue to latest."""
    normalized_origin = origin.rstrip("/") + "/"
    for language in ("en", "cn"):
        language_root = assembly / f"content/{language}"
        for path in sorted(language_root.iterdir()):
            if path.name == "docs":
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

        footer_path = assembly / f"data/footer/{language}.yaml"
        footer = footer_path.read_text(encoding="utf-8")
        prefix = "cn/" if language == "cn" else ""
        replacements = {
            f"url: /{prefix}blog/": (
                "url: '"
                + urllib.parse.urljoin(normalized_origin, f"{prefix}blog/")
                + "'"
            ),
            f"url: /{prefix}community/": (
                "url: '"
                + urllib.parse.urljoin(normalized_origin, f"{prefix}community/")
                + "'"
            ),
        }
        for old, new in replacements.items():
            occurrences = footer.count(old)
            if occurrences > 1:
                fail(f"expected one shared footer route in {footer_path}: {old}")
            if occurrences == 1:
                footer = footer.replace(old, new)
        footer_path.write_text(footer, encoding="utf-8")

        blog_ref = (
            '{{< ref path="/blog/hugegraph/toplingdb/'
            f'toplingdb-quick-start.md" lang="{language}">}}}}'
        )
        latest_blog = urllib.parse.urljoin(
            normalized_origin,
            f"{prefix}blog/hugegraph/toplingdb/toplingdb-quick-start/",
        )
        for path in sorted((language_root / "docs").rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            if blog_ref in text:
                path.write_text(text.replace(blog_ref, latest_blog), encoding="utf-8")


def strip_menu_frontmatter(path: pathlib.Path) -> None:
    if not path.is_file():
        return
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    opening_index = next(
        (index for index, line in enumerate(lines) if line.strip()), None
    )
    if opening_index is None or lines[opening_index].strip() != "---":
        fail(f"cannot remove menu from non-YAML front matter: {path}")
    try:
        closing_index = next(
            index
            for index, line in enumerate(lines[opening_index + 1 :], opening_index + 1)
            if line.strip() == "---"
        )
    except StopIteration:
        fail(f"unterminated YAML front matter: {path}")
    frontmatter = lines[opening_index + 1 : closing_index]
    output = lines[: opening_index + 1]
    index = 0
    while index < len(frontmatter):
        line = frontmatter[index]
        if re.fullmatch(r"menu:\s*", line):
            index += 1
            while index < len(frontmatter):
                candidate = frontmatter[index]
                if candidate.strip() and candidate[:1] not in {" ", "\t"}:
                    break
                index += 1
            continue
        output.append(line)
        index += 1
    output.append(lines[closing_index])
    output.extend(lines[closing_index + 1 :])
    path.write_text("".join(output), encoding="utf-8")


def base_url(origin: str, publish_path: str) -> str:
    normalized_origin = origin.rstrip("/") + "/"
    if not publish_path:
        return normalized_origin
    return urllib.parse.urljoin(normalized_origin, publish_path.rstrip("/") + "/")


def ensure_frontmatter(
    path: pathlib.Path, *, title: str, link_title: str, weight: int
) -> int:
    """Add navigation metadata to a legacy Markdown page without replacing its body."""
    source = path.read_text(encoding="utf-8")
    if source.startswith("---\n"):
        return 0
    path.write_text(
        "---\n"
        f'title: "{title}"\n'
        f'linkTitle: "{link_title}"\n'
        f"weight: {weight}\n"
        "---\n\n"
        f"{source}",
        encoding="utf-8",
    )
    return 1


def add_frontmatter_alias(path: pathlib.Path, alias: str) -> None:
    source = path.read_text(encoding="utf-8")
    opening = source.find("---")
    if opening < 0 or source[:opening].strip():
        fail(f"cannot add route alias without YAML front matter: {path}")
    closing = source.find("\n---", opening + 3)
    if closing < 0:
        fail(f"unterminated YAML front matter: {path}")
    frontmatter = source[opening + 3 : closing]
    if re.search(r"(?m)^aliases\s*:", frontmatter):
        fail(f"historical page already declares aliases: {path}")
    source = source[:closing] + f"\naliases:\n  - {alias}\n" + source[closing:]
    path.write_text(source, encoding="utf-8")


def migrate_legacy_information_architecture(
    assembly: pathlib.Path, version: str
) -> int:
    """Move 1.3/1.0 flat pages into the current five-group route hierarchy."""
    if version not in {"1.3", "1.0"}:
        return 0
    changed = 0
    for language in ("en", "cn"):
        docs = assembly / "content" / language / "docs"
        for section, titles in LEGACY_IA_SECTIONS.items():
            index = docs / section / "_index.md"
            if not index.exists():
                index.parent.mkdir(parents=True, exist_ok=True)
                title = titles[0] if language == "en" else titles[1]
                index.write_text(
                    f'---\ntitle: "{title}"\nlinkTitle: "{title}"\n---\n',
                    encoding="utf-8",
                )
                changed += 1
        for old_relative, new_relative in LEGACY_IA_ROUTE_MAP.items():
            source = docs / old_relative
            if not source.is_file():
                continue
            target = docs / new_relative
            if target.exists():
                if not source.samefile(target):
                    fail(f"historical route migration target already exists: {target}")
                intermediate = source.with_name(source.name + ".route-migration-tmp")
                source.rename(intermediate)
                source = intermediate
            target.parent.mkdir(parents=True, exist_ok=True)
            source.rename(target)
            changed += 1
        summary = docs / "SUMMARY.md"
        text = summary.read_text(encoding="utf-8")
        for old_relative, new_relative in LEGACY_IA_ROUTE_MAP.items():
            text = text.replace(old_relative, new_relative)
        summary.write_text(text, encoding="utf-8")
    return changed


def ensure_search_metadata(
    path: pathlib.Path, *, keywords: tuple[str, ...], boost: float
) -> int:
    """Add search hints to an existing YAML front matter block once."""
    source = path.read_text(encoding="utf-8")
    if not source.startswith("---\n"):
        fail(f"cannot add search metadata without YAML front matter: {path}")
    closing = source.find("\n---\n", 4)
    if closing < 0:
        fail(f"unterminated YAML front matter: {path}")
    frontmatter = source[4:closing]
    if re.search(r"(?m)^search_keywords\s*:", frontmatter):
        return 0
    metadata = "search_keywords:\n" + "".join(
        f"  - {keyword}\n" for keyword in keywords
    )
    metadata += f"search_boost: {boost:g}\n"
    path.write_text(
        source[: closing + 1] + metadata + source[closing + 1 :],
        encoding="utf-8",
    )
    return 1


def ensure_search_excluded(path: pathlib.Path) -> int:
    """Exclude a rendered utility page from OINK's offline search index."""
    source = path.read_text(encoding="utf-8")
    if not source.startswith("---\n"):
        fail(f"cannot add search exclusion without YAML front matter: {path}")
    closing = source.find("\n---\n", 4)
    if closing < 0:
        fail(f"unterminated YAML front matter: {path}")
    frontmatter = source[4:closing]
    match = re.search(r"(?m)^search_exclude\s*:\s*(\S+)\s*$", frontmatter)
    if match:
        if match.group(1) == "true":
            return 0
        fail(f"unexpected search_exclude value in {path}: {match.group(1)}")
    path.write_text(
        source[: closing + 1] + "search_exclude: true\n" + source[closing + 1 :],
        encoding="utf-8",
    )
    return 1


def docs_content_routes(assembly: pathlib.Path, language: str) -> set[str]:
    """Return case-normalized GetPage routes backed by one language's Docs."""
    docs_root = assembly / f"content/{language}/docs"
    if not docs_root.is_dir():
        fail(f"Docs content root is missing: {docs_root}")
    routes: set[str] = set()
    for path in docs_root.rglob("*.md"):
        source = path.read_text(encoding="utf-8")
        if source.startswith("---\n"):
            closing = source.find("\n---\n", 4)
            frontmatter = source[4:closing] if closing >= 0 else ""
            if re.search(r"(?m)^draft\s*:\s*true\s*$", frontmatter):
                continue
        relative = path.relative_to(docs_root)
        if path.name == "_index.md":
            route = pathlib.PurePosixPath("/docs", *relative.parent.parts).as_posix()
        else:
            route = pathlib.PurePosixPath(
                "/docs", *relative.with_suffix("").parts
            ).as_posix()
        routes.add(route.rstrip("/").lower())
    return routes


def docs_nav_page_for_routes(page: str, routes: set[str]) -> str | None:
    """Resolve a declared latest route against latest or pinned historical content."""
    normalized = page.rstrip("/").lower()
    candidates = [normalized]
    if normalized == "/docs/introduction":
        candidates.append("/docs/introduction/readme")
    if "/api-performance" in normalized:
        candidates.append(normalized.replace("/api-performance", "/api-preformance"))
    return next((candidate for candidate in candidates if candidate in routes), None)


def docs_nav_url(page: str) -> str:
    """Return Hugo's language-neutral RelPermalink key for Docs navigation."""
    return page.rstrip("/") + "/"


def scope_docs_nav_group_links(assembly: pathlib.Path, publish_path: str) -> int:
    """Scope group manual links before Hugo serializes them into NAVJSON."""
    if not publish_path:
        return 0
    prefix = "/" + publish_path.strip("/")
    changed = 0
    for language in ("en", "cn"):
        for group_id in DOCS_NAV_GROUP_IDS:
            path = assembly / f"content/{language}/docs/_nav/{group_id}.md"
            source = path.read_text(encoding="utf-8")
            match = re.search(r"(?m)^manual_link:\s*(/\S+)\s*$", source)
            if match is None:
                fail(f"Docs navigation manual_link is missing: {path}")
            target = match.group(1)
            if target == prefix or target.startswith(prefix + "/"):
                continue
            if target == "/versions" or target.startswith("/versions/"):
                fail(f"Docs navigation manual_link has the wrong version: {path}")
            scoped = prefix + target
            path.write_text(
                source[: match.start(1)] + scoped + source[match.end(1) :],
                encoding="utf-8",
            )
            changed += 1
    return changed


def docs_navigation_tree_sha256(sections: list[dict]) -> str:
    """Fingerprint exact group membership, order, routes, and hierarchy."""
    return hashlib.sha256(
        json.dumps(sections, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def materialize_docs_navigation(
    assembly: pathlib.Path, publish_path: str
) -> dict[str, int]:
    """Adapt the five-group IA to the checked-out bilingual Docs snapshot.

    The authored ``groups`` tree is latest-oriented. Historical builds retain
    the same task groups while missing later pages are removed and the two
    legacy route spellings are resolved. Derived maps are regenerated so the
    OINK sidebar, pager, section index, and NAVJSON share one authority.
    """
    nav_path = assembly / "data/docs_nav.json"
    try:
        source = json.loads(nav_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"cannot read Docs navigation source {nav_path}: {exc}")
    if source.get("schemaVersion") != 1 or not isinstance(source.get("groups"), list):
        fail("data/docs_nav.json must contain schemaVersion 1 and a groups array")
    groups = source["groups"]
    if [group.get("id") for group in groups if isinstance(group, dict)] != list(
        DOCS_NAV_GROUP_IDS
    ):
        fail(
            "Docs navigation groups must be start, components, develop, operate, reference"
        )

    scoped_links = scope_docs_nav_group_links(assembly, publish_path)

    routes = docs_content_routes(assembly, "en") & docs_content_routes(assembly, "cn")
    seen_pages: set[str] = set()
    removed = 0

    def adapt(node: dict, *, group: bool = False) -> dict | None:
        nonlocal removed
        if not isinstance(node, dict) or not isinstance(node.get("page"), str):
            fail(f"invalid Docs navigation node: {node!r}")
        resolved = docs_nav_page_for_routes(node["page"], routes)
        if resolved is None:
            removed += 1
            return None
        if resolved in seen_pages:
            fail(f"duplicate Docs navigation page: {resolved}")
        seen_pages.add(resolved)
        children = []
        for child in node.get("children", []):
            adapted = adapt(child)
            if adapted is not None:
                children.append(adapted)
        if group and not children:
            fail(f"Docs navigation group is empty: {node.get('id')}")
        return {
            "page": resolved,
            "url": f"@group/{node['id']}" if group else docs_nav_url(resolved),
            "children": children,
            **({"group": node["id"]} if group else {}),
        }

    sections = [adapt(group, group=True) for group in groups]
    if any(section is None for section in sections):
        fail("one or more Docs navigation group pages are missing")

    active_path_by_url: dict[str, list[str]] = {}
    children_by_url: dict[str, list[str]] = {
        docs_nav_url("/docs"): [section["page"] for section in sections]
    }

    def index_node(node: dict, ancestors: list[str]) -> None:
        current_path = [*ancestors, node["url"]]
        if not node.get("group"):
            active_path_by_url[node["url"]] = current_path
            if node["children"]:
                children_by_url[node["url"]] = [
                    child["page"] for child in node["children"]
                ]
        for child in node["children"]:
            index_node(child, current_path)

    for section in sections:
        index_node(section, [])

    materialized = {
        "schemaVersion": 1,
        "groups": groups,
        "sections": sections,
        "active_path_by_url": active_path_by_url,
        "children_by_url": children_by_url,
    }
    nav_path.write_text(
        json.dumps(materialized, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "groups": len(sections),
        "pages": len(active_path_by_url),
        "removed": removed,
        "scopedLinks": scoped_links,
        "treeSha256": docs_navigation_tree_sha256(sections),
    }


LEGACY_WECHAT_IMAGE_RE = re.compile(
    r'<img\b(?=[^>]*\bsrc="(?:https://github\.com/apache/(?:incubator-)?hugegraph-doc/'
    r"blob/master/assets/images/wechat\.png\?raw=true|https://raw\.githubusercontent\.com/"
    r'apache/(?:incubator-)?hugegraph-doc/master/assets/images/wechat\.png)")'
    r'(?=[^>]*\bwidth="(?P<width>200|300)")[^>]*?/?>',
    re.IGNORECASE,
)


def replace_legacy_wechat_images(source: str, language: str) -> tuple[str, int]:
    """Localize legacy WeChat images regardless of their historical alt text."""
    if language not in {"en", "cn"}:
        fail(f"unsupported legacy image language: {language}")
    alt = (
        "Apache HugeGraph WeChat QR Code"
        if language == "en"
        else "Apache HugeGraph 微信公众号二维码"
    )

    def replacement(match: re.Match) -> str:
        width = int(match.group("width"))
        height = 63 if width == 200 else 94
        return (
            f"![{alt}](/images/docs/community/wechat.png)"
            f'{{width="{width}" height="{height}"}}'
        )

    return LEGACY_WECHAT_IMAGE_RE.subn(replacement, source)


def repair_historical_performance_routes(path: pathlib.Path) -> int:
    """Restore the misspelled directory name used by pinned historical refs."""
    source = path.read_text(encoding="utf-8")
    corrected = source.count("performance/api-performance")
    historical = source.count("performance/api-preformance")
    if corrected + historical != 3:
        fail(
            f"expected 3 historical performance routes in {path}, "
            f"found {corrected + historical}"
        )
    if corrected == 0:
        return 0
    path.write_text(
        source.replace("performance/api-performance", "performance/api-preformance"),
        encoding="utf-8",
    )
    return corrected


MARKDOWN_ATX_HEADING_RE = re.compile(
    r"^(?P<indent> {0,3})(?P<marks>#{1,6})(?P<spacing>[ \t]+)(?P<body>.*)$"
)
MARKDOWN_FENCE_OPEN_RE = re.compile(
    r"^ {0,3}(?P<marker>`{3,}|~{3,})(?:[^\r\n]*)?(?:\r?\n)?$"
)


def normalize_historical_server_headings(path: pathlib.Path) -> int:
    """Promote legacy Server headings without touching fenced examples."""
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)
    headings: list[tuple[int, re.Match[str]]] = []
    fence_character: str | None = None
    fence_length = 0

    for index, line in enumerate(lines):
        line_without_ending = line.rstrip("\r\n")
        if fence_character is not None:
            closing = re.match(
                rf"^ {{0,3}}{re.escape(fence_character)}{{{fence_length},}}[ \t]*$",
                line_without_ending,
            )
            if closing:
                fence_character = None
                fence_length = 0
            continue

        opening = MARKDOWN_FENCE_OPEN_RE.match(line)
        if opening:
            marker = opening.group("marker")
            fence_character = marker[0]
            fence_length = len(marker)
            continue

        heading = MARKDOWN_ATX_HEADING_RE.match(line_without_ending)
        if heading:
            headings.append((index, heading))

    if fence_character is not None:
        fail(f"unterminated Markdown fence in historical Server page: {path}")
    if not headings:
        fail(f"no Markdown headings found in historical Server page: {path}")

    first_level = len(headings[0][1].group("marks"))
    if first_level == 2:
        shift = 0
    elif first_level == 3:
        shift = 1
    else:
        fail(
            f"unexpected first heading level in historical Server page {path}: "
            f"h{first_level}"
        )

    previous_level: int | None = None
    for _, heading in headings:
        normalized_level = len(heading.group("marks")) - shift
        if normalized_level < 2:
            fail(f"heading would collide with the page title in {path}")
        if previous_level is not None and normalized_level > previous_level + 1:
            fail(
                f"heading level skips from h{previous_level} to h{normalized_level} "
                f"in {path}"
            )
        previous_level = normalized_level

    if shift == 0:
        return 0

    for index, heading in headings:
        newline = "\r\n" if lines[index].endswith("\r\n") else "\n"
        if not lines[index].endswith(("\n", "\r")):
            newline = ""
        lines[index] = (
            heading.group("indent")
            + heading.group("marks")[shift:]
            + heading.group("spacing")
            + heading.group("body")
            + newline
        )
    path.write_text("".join(lines), encoding="utf-8")
    return len(headings)


LEGACY_EXACT_CONTENT_FIXES = {
    "1.5": (
        (
            "cn",
            "docs/quickstart/computing/hugegraph-computer.md",
            "/docs/clients/restful-api/graphs/"
            "#634-modify-graphs-read-mode-this-operation-requires-administrator-privileges",
            "/docs/clients/restful-api/graphs/"
            "#634-设置某个图的读模式该操作需要管理员权限",
            1,
        ),
        (
            "cn",
            "docs/quickstart/hugegraph/hugegraph-server.md",
            "/cn/docs/quickstart/hugegraph-server/"
            "#511-%E5%90%AF%E5%8A%A8-server-%E7%9A%84%E6%97%B6%E5%80%99"
            "%E5%88%9B%E5%BB%BA%E7%A4%BA%E4%BE%8B%E5%9B%BE",
            "/cn/docs/quickstart/hugegraph-server/"
            "#518-%E5%90%AF%E5%8A%A8-server-%E7%9A%84%E6%97%B6%E5%80%99"
            "%E5%88%9B%E5%BB%BA%E7%A4%BA%E4%BE%8B%E5%9B%BE",
            1,
        ),
        (
            "cn",
            "docs/quickstart/hugegraph/hugegraph-server.md",
            "#33-使用-docker-容器",
            "#31-使用-docker-容器-便于测试",
            1,
        ),
        (
            "en",
            "docs/quickstart/hugegraph/hugegraph-server.md",
            "/docs/config/config-authentication"
            "#Use-docker-to-enble-authentication-mode",
            "/docs/config/config-authentication/"
            "#use-docker-to-enable-authentication-mode",
            1,
        ),
        (
            "en",
            "docs/quickstart/hugegraph/hugegraph-server.md",
            "#33-use-docker-container",
            "#31-use-docker-container-convenient-for-testdev",
            1,
        ),
        (
            "en",
            "docs/quickstart/hugegraph/hugegraph-server.md",
            '<img src="/docs/images/images-server/31docker-option.jpg" '
            'alt="image" style="width:33%;">',
            '<img src="/docs/images/images-server/31docker-option.jpg" '
            'alt="Docker Desktop settings for a HugeGraph container" '
            'style="width:33%;">',
            1,
        ),
        (
            "en",
            "docs/quickstart/hugegraph/hugegraph-server.md",
            '<img src="/docs/images/images-server/swagger-ui.png" alt="image">',
            '<img src="/docs/images/images-server/swagger-ui.png" '
            'alt="HugeGraph RESTful API endpoints in Swagger UI">',
            1,
        ),
        (
            "en",
            "docs/quickstart/hugegraph/hugegraph-server.md",
            '<img src="/docs/images/images-server/'
            'swagger-ui-where-set-auth-example.png" alt="image">',
            '<img src="/docs/images/images-server/'
            'swagger-ui-where-set-auth-example.png" '
            'alt="Authorize button in the HugeGraph Swagger UI">',
            1,
        ),
        (
            "en",
            "docs/quickstart/hugegraph/hugegraph-server.md",
            '<img src="/docs/images/images-server/'
            'swagger-ui-set-auth-example.png" alt="image">',
            '<img src="/docs/images/images-server/'
            'swagger-ui-set-auth-example.png" '
            'alt="Basic and Bearer credential fields in the Swagger UI '
            'authorization dialog">',
            1,
        ),
        (
            "cn",
            "docs/quickstart/hugegraph/hugegraph-server.md",
            '<img src="/docs/images/images-server/31docker-option.jpg" '
            'alt="image" style="width:33%;">',
            '<img src="/docs/images/images-server/31docker-option.jpg" '
            'alt="Docker Desktop 中 HugeGraph 容器的运行设置" '
            'style="width:33%;">',
            1,
        ),
        (
            "cn",
            "docs/quickstart/hugegraph/hugegraph-server.md",
            '<img src="/docs/images/images-server/swagger-ui.png" alt="image">',
            '<img src="/docs/images/images-server/swagger-ui.png" '
            'alt="Swagger UI 中的 HugeGraph RESTful API 接口列表">',
            1,
        ),
        (
            "cn",
            "docs/quickstart/hugegraph/hugegraph-server.md",
            '<img src="/docs/images/images-server/'
            'swagger-ui-where-set-auth-example.png" alt="image">',
            '<img src="/docs/images/images-server/'
            'swagger-ui-where-set-auth-example.png" '
            'alt="HugeGraph Swagger UI 中的 Authorize 按钮">',
            1,
        ),
        (
            "cn",
            "docs/quickstart/hugegraph/hugegraph-server.md",
            '<img src="/docs/images/images-server/'
            'swagger-ui-set-auth-example.png" alt="image">',
            '<img src="/docs/images/images-server/'
            'swagger-ui-set-auth-example.png" '
            'alt="Swagger UI 授权对话框中的 Basic 和 Bearer 凭据输入框">',
            1,
        ),
    ),
    "1.7": (
        (
            "cn",
            "docs/quickstart/computing/hugegraph-computer.md",
            "/docs/clients/restful-api/graphs/"
            "#634-modify-graphs-read-mode-this-operation-requires-administrator-privileges",
            "/docs/clients/restful-api/graphs/"
            "#634-设置某个图的读模式该操作需要管理员权限",
            1,
        ),
    ),
}


def apply_exact_legacy_content_fixes(assembly: pathlib.Path, version: str) -> int:
    """Apply version, language, and path-bound historical content repairs."""
    fixes = LEGACY_EXACT_CONTENT_FIXES.get(version)
    if fixes is None:
        fail(f"unsupported exact legacy content-fix version: {version}")
    fixed = 0
    for language, relative, old, new, expected_count in fixes:
        path = assembly / "content" / language / relative
        source = path.read_text(encoding="utf-8")
        count = source.count(old)
        if count != expected_count:
            fail(
                f"expected {expected_count} exact historical content match(es) "
                f"for {version}/{language}/{relative}, found {count}"
            )
        path.write_text(source.replace(old, new), encoding="utf-8")
        fixed += count
    return fixed


def first_existing_path(assembly: pathlib.Path, candidates: tuple[str, ...]) -> pathlib.Path:
    """Resolve one version-specific content path without guessing missing files."""
    matches = [assembly / candidate for candidate in candidates if (assembly / candidate).is_file()]
    if len(matches) != 1:
        fail(f"expected exactly one historical path, found {len(matches)}: {candidates!r}")
    return matches[0]


def apply_known_legacy_fixes(assembly: pathlib.Path, version: str) -> int:
    fixed = 0
    if version in {"1.7", "1.5", "1.3", "1.0"}:
        if version in LEGACY_EXACT_CONTENT_FIXES:
            fixed += apply_exact_legacy_content_fixes(assembly, version)
        for language in ("en", "cn"):
            language_prefix = "/cn" if language == "cn" else ""
            legacy_metadata = (
                ("CLA.md", "Contributor Agreement", "Contributor Agreement"),
                (
                    "performance/hugegraph-benchmark-0.4.4.md",
                    "HugeGraph 0.4.4 Benchmark"
                    if language == "en"
                    else "HugeGraph 0.4.4 性能测试",
                    "HugeGraph 0.4.4 Benchmark"
                    if language == "en"
                    else "HugeGraph 0.4.4 性能测试",
                ),
            )
            for relative, title, link_title in legacy_metadata:
                page = assembly / f"content/{language}/docs/{relative}"
                if page.is_file():
                    fixed += ensure_frontmatter(
                        page, title=title, link_title=link_title, weight=100
                    )
            cla = assembly / f"content/{language}/docs/CLA.md"
            if cla.is_file():
                fixed += ensure_search_excluded(cla)
            search_metadata = (
                (
                    "config/config-option.md",
                    ("gremlin.graph", "rest-server.properties", "hugegraph.properties"),
                ),
                (
                    "quickstart/hugegraph/hugegraph-hstore.md",
                    (
                        "server.port",
                        "REST port" if language == "en" else "REST 端口",
                        "Store REST port" if language == "en" else "Store REST 端口",
                    ),
                ),
            )
            for relative, keywords in search_metadata:
                page = assembly / f"content/{language}/docs/{relative}"
                if page.is_file():
                    fixed += ensure_search_metadata(page, keywords=keywords, boost=1.5)
            summary_path = assembly / f"content/{language}/docs/SUMMARY.md"
            if version in {"1.7", "1.5"}:
                fixed += repair_historical_performance_routes(summary_path)
            fixed += normalize_historical_server_headings(
                first_existing_path(
                    assembly,
                    (
                        f"content/{language}/docs/quickstart/hugegraph/hugegraph-server.md",
                        f"content/{language}/docs/quickstart/hugegraph-server.md",
                    ),
                )
            )
            replacements = []
            if language == "cn":
                replacements.append(
                    (
                        "/cn/docs/quickstart/hugegraph-server",
                        "/cn/docs/quickstart/hugegraph/hugegraph-server",
                    )
                )
            replacements.extend(
                [
                    ("/en/docs/", "/docs/"),
                    (
                        "/dcos/clients/restful-api",
                        f"{language_prefix}/docs/clients/restful-api/",
                    ),
                    (
                        "/docs/quickstart/hugegraph-studio",
                        f"{language_prefix}/docs/quickstart/toolchain/hugegraph-hubble",
                    ),
                    (
                        "/docs/quickstart/hugegraph-server",
                        f"{language_prefix}/docs/quickstart/hugegraph/hugegraph-server",
                    ),
                    (
                        "/clients/gremlin-console.html",
                        f"{language_prefix}/docs/clients/gremlin-console/",
                    ),
                    (
                        "/clients/hugegraph-api.html",
                        f"{language_prefix}/docs/clients/restful-api/",
                    ),
                    (
                        "./hugegraph-style.xml",
                        "https://github.com/apache/hugegraph/blob/"
                        f"release-{version}.0/style/checkstyle.xml",
                    ),
                ]
            )
            image_urls = {
                "http://tinkerpop.apache.org/docs/3.4.0/images/tinkerpop-modern.png": "/images/docs/graphs/tinkerpop-modern.png",
                "https://hugegraph.apache.org/docs/images/gradio-kg.png": "/images/docs/hugegraph-ai/gradio-kg.jpg",
                "https://github.com/user-attachments/assets/f3366d46-2e31-4638-94c4-7214951ef77a": "/images/docs/hugegraph-ai/quick-start-01.png",
                "https://github.com/user-attachments/assets/33698062-e46b-4757-8b5e-93e8f10eae65": "/images/docs/hugegraph-ai/quick-start-02.png",
                "https://github.com/user-attachments/assets/26641e09-249f-4b3a-8013-16dc9383d333": "/images/docs/hugegraph-ai/quick-start-03.jpg",
                "https://github.com/user-attachments/assets/b49e269f-eaec-40b1-8d8f-9e409821d75d": "/images/docs/hugegraph-ai/quick-start-04.png",
                "https://github.com/user-attachments/assets/7d4496a3-d44c-4491-9463-8e93595dfa45": "/images/docs/hugegraph-ai/quick-start-05.jpg",
                "https://github.com/user-attachments/assets/fc678369-261d-49ea-a289-1ca6ade5ca55": "/images/docs/hugegraph-ai/quick-start-06.png",
                "https://github.com/user-attachments/assets/d2a72f45-488c-4099-968b-a11816655ba0": "/images/docs/hugegraph-ai/quick-start-07.png",
                "https://github.com/user-attachments/assets/d2a72f45-488c-4499-968b-a11816655ba0": "/images/docs/hugegraph-ai/quick-start-07.png",
                "https://github.com/user-attachments/assets/fd150f87-27f8-48e5-8a55-319ec039b7e0": "/images/docs/hugegraph-ai/quick-start-08.png",
            }
            replacements.extend(image_urls.items())
            replacements.extend(
                [
                    (
                        "[![License](https://img.shields.io/badge/license-Apache%202-0E78BA.svg)](https://www.apache.org/licenses/LICENSE-2.0.html)",
                        "[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.html)",
                    ),
                    (
                        "[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/apache/incubator-hugegraph-ai)",
                        "[Ask DeepWiki](https://deepwiki.com/apache/incubator-hugegraph-ai)",
                    ),
                    (
                        "[![contributors graph](https://contrib.rocks/image?repo=apache/incubator-hugegraph-ai)](https://github.com/apache/incubator-hugegraph-ai/graphs/contributors)",
                        "[View the HugeGraph-AI contributors](https://github.com/apache/incubator-hugegraph-ai/graphs/contributors).",
                    ),
                ]
            )
            contribution_images = (
                (
                    '<img width="884" alt="image" src="https://user-images.githubusercontent.com/9625821/159643158-8bf72c0a-93c3-4a58-8912-7b2ab20ced1d.png">',
                    "Fork the HugeGraph repository on GitHub"
                    if language == "en"
                    else "在 GitHub 上 Fork HugeGraph 仓库",
                    "/images/docs/contribution/github-fork.png",
                    884,
                    462,
                ),
                (
                    '<img width="1280" alt="image" src="https://user-images.githubusercontent.com/9625821/163524204-7fe0e6bf-9c8b-4b1a-ac65-6a0ac423eb16.png">',
                    "Authenticate a Git push with a personal access token"
                    if language == "en"
                    else "使用个人访问令牌认证 Git 推送",
                    "/images/docs/contribution/github-authentication.png",
                    1280,
                    422,
                ),
                (
                    '<img width="1280" alt="image" src="https://user-images.githubusercontent.com/9625821/163522445-2a50a72a-dea2-434f-9868-3a0d40d0d037.png">',
                    "Verify the commit email address in GitHub"
                    if language == "en"
                    else "在 GitHub 中验证提交邮箱",
                    "/images/docs/contribution/github-email.png",
                    1280,
                    592,
                ),
            )
            replacements.extend(
                (
                    raw,
                    f'![{alt}]({url}){{width="{width}" height="{height}"}}',
                )
                for raw, alt, url, width, height in contribution_images
            )
            for path in sorted((assembly / f"content/{language}").rglob("*.md")):
                text = path.read_text(encoding="utf-8")
                rendered, wechat_count = replace_legacy_wechat_images(text, language)
                fixed += wechat_count
                for old, new in replacements:
                    count = rendered.count(old)
                    rendered = rendered.replace(old, new)
                    fixed += count
                if rendered != text:
                    path.write_text(rendered, encoding="utf-8")
        if fixed < 4:
            fail(f"expected known historical route fixes for {version}, found {fixed}")
    return fixed


def version_urls(
    manifest: dict,
    origin: str,
    language: str = "en",
    historical_origin: str | None = None,
) -> list[dict]:
    if language not in {"en", "cn"}:
        fail(f"unsupported version-menu language: {language}")
    language_prefix = "cn/" if language == "cn" else ""
    urls = []
    for entry in manifest["versions"]:
        entry_origin = (
            historical_origin
            if entry.get("archived", entry["id"] != "latest")
            and historical_origin is not None
            else origin
        )
        path = (
            f"{entry['publishPath']}/{language_prefix}docs/"
            if entry["publishPath"]
            else f"{language_prefix}docs/"
        )
        urls.append(
            {
                "version": entry["id"],
                "name": entry["name"],
                "url": urllib.parse.urljoin(entry_origin.rstrip("/") + "/", path),
                "pagelinks": False,
            }
        )
    return urls


def language_version_params(
    manifest: dict,
    origin: str,
    language: str,
    historical_origin: str | None = None,
) -> dict:
    """Build language-preserving version selector and archive-banner params."""
    if language not in {"en", "cn"}:
        fail(f"unsupported version-menu language: {language}")
    return {
        "version_menu": "Releases" if language == "en" else "版本",
        "versions": version_urls(manifest, origin, language, historical_origin),
        "url_latest_version": urllib.parse.urljoin(
            origin.rstrip("/") + "/",
            "cn/docs/" if language == "cn" else "docs/",
        ),
    }


def historical_language_menus(origin: str) -> dict:
    normalized_origin = origin.rstrip("/") + "/"
    result = {}
    for language, labels in (
        (
            "en",
            {
                "docs": "Documentation",
                "download": "Download",
                "blog": "Blog",
                "community": "Community",
            },
        ),
        (
            "cn",
            {"docs": "文档", "download": "下载", "blog": "博客", "community": "社区"},
        ),
    ):
        language_prefix = "cn/" if language == "cn" else ""
        result[language] = {
            "menus": {
                "main": [
                    {
                        "identifier": "docs",
                        "name": labels["docs"],
                        "pageRef": "/docs",
                        "weight": 10,
                    },
                    {
                        "identifier": "download",
                        "name": labels["download"],
                        "pageRef": "/docs/download/download",
                        "weight": 20,
                    },
                    {
                        "identifier": "blog",
                        "name": labels["blog"],
                        "url": urllib.parse.urljoin(
                            normalized_origin, f"{language_prefix}blog/"
                        ),
                        "weight": 30,
                    },
                    {
                        "identifier": "community",
                        "name": labels["community"],
                        "url": urllib.parse.urljoin(
                            normalized_origin, f"{language_prefix}community/"
                        ),
                        "weight": 40,
                    },
                    {
                        "identifier": "github",
                        "name": "GitHub",
                        "url": "https://github.com/apache/hugegraph",
                        "weight": 50,
                    },
                ]
            }
        }
    return result


def allowed_version_paths(manifest: dict) -> set[str]:
    result = {"/", "/cn", "/blog", "/cn/blog", "/community", "/cn/community"}
    for entry in manifest["versions"]:
        version_prefix = f"/{entry['publishPath']}" if entry["publishPath"] else ""
        for language_prefix in ("", "/cn"):
            path = f"{version_prefix}{language_prefix}/docs"
            result.add(path.rstrip("/") or "/")
    return result


def is_latest_shared_path(path: str) -> bool:
    normalized = path.rstrip("/") or "/"
    return normalized in {"/", "/cn"} or any(
        normalized == shared or normalized.startswith(shared + "/")
        for shared in ("/blog", "/cn/blog", "/community", "/cn/community")
    )


def same_site_host(parts: urllib.parse.SplitResult) -> str | None:
    """Normalize an HTTP(S) site authority while rejecting unsafe variants."""
    scheme = parts.scheme.lower()
    if scheme not in {"http", "https"} or "@" in parts.netloc:
        return None
    try:
        port = parts.port
    except ValueError:
        return None
    if port is not None and port != {"http": 80, "https": 443}[scheme]:
        return None
    hostname = (parts.hostname or "").lower().rstrip(".")
    return hostname or None


def normalized_hostname(parts: urllib.parse.SplitResult) -> str | None:
    """Return the DNS hostname independently from authority validity."""
    hostname = (parts.hostname or "").lower().rstrip(".")
    return hostname or None


def require_safe_url_syntax(value: str) -> None:
    """Reject separators whose browser meaning differs from RFC urlsplit."""
    if "\\" in value:
        fail(f"unsafe URL syntax: {value}")


def require_safe_http_authority(parts: urllib.parse.SplitResult, value: str) -> None:
    """Reject authority syntax that browsers normalize differently from urlsplit."""
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        return
    if not parts.netloc.isascii() or any(
        char in parts.netloc for char in ("@", "\\", "%")
    ):
        fail(f"unsafe URL authority: {value}")


def rewrite_internal_url(
    value: str,
    *,
    origin: str,
    publish_path: str,
    allowed_paths: set[str],
) -> str:
    """Scope a same-site absolute/root URL to one historical artifact."""
    if not value or value.startswith(("#", "?")):
        return value
    require_safe_url_syntax(value)
    if value.startswith("//"):
        fail(f"protocol-relative URL is not allowed in a version artifact: {value}")
    parsed = urllib.parse.urlsplit(value)
    origin_parts = urllib.parse.urlsplit(origin.rstrip("/") + "/")
    canonical_parts = urllib.parse.urlsplit(CANONICAL_ORIGIN)
    require_safe_http_authority(parsed, value)
    parsed_host = same_site_host(parsed)
    origin_host = same_site_host(origin_parts)
    canonical_host = same_site_host(canonical_parts)
    absolute = bool(parsed.scheme or parsed.netloc)
    if absolute:
        if (
            normalized_hostname(parsed) in {origin_host, canonical_host}
            and parsed_host is None
        ):
            fail(f"unsafe same-site URL authority: {value}")
        if parsed_host not in {origin_host, canonical_host}:
            return value
        path = parsed.path or "/"
    elif value.startswith("/"):
        path = parsed.path or "/"
    else:
        return value

    if not publish_path:
        if absolute and parsed_host != origin_host:
            return urllib.parse.urlunsplit(
                (
                    origin_parts.scheme,
                    origin_parts.netloc,
                    path,
                    parsed.query,
                    parsed.fragment,
                )
            )
        return value

    normalized = path.rstrip("/") or "/"
    prefix = "/" + publish_path.strip("/")
    internal_path = (
        path[len(prefix) :]
        if normalized == prefix or normalized.startswith(prefix + "/")
        else path
    )
    normalized_internal = internal_path.rstrip("/") or "/"
    mapped_path = KNOWN_HISTORICAL_ROUTES_BY_PUBLISH_PATH.get(
        publish_path.strip("/"), {}
    ).get(normalized_internal)
    if mapped_path is None:
        mapped_path = KNOWN_HISTORICAL_ROUTES.get(normalized_internal)
    if mapped_path is not None:
        scoped_path = prefix + mapped_path
        if absolute:
            return urllib.parse.urlunsplit(
                (
                    origin_parts.scheme,
                    origin_parts.netloc,
                    scoped_path,
                    parsed.query,
                    parsed.fragment,
                )
            )
        return urllib.parse.urlunsplit(
            ("", "", scoped_path, parsed.query, parsed.fragment)
        )
    if normalized == prefix or normalized.startswith(prefix + "/"):
        if absolute and (
            parsed.scheme.lower() != origin_parts.scheme.lower()
            or parsed.netloc != origin_parts.netloc
        ):
            return urllib.parse.urlunsplit(
                (
                    origin_parts.scheme,
                    origin_parts.netloc,
                    path,
                    parsed.query,
                    parsed.fragment,
                )
            )
        return value
    if is_latest_shared_path(normalized) or (absolute and normalized in allowed_paths):
        return urllib.parse.urlunsplit(
            (
                origin_parts.scheme,
                origin_parts.netloc,
                path,
                parsed.query,
                parsed.fragment,
            )
        )
    if normalized == "/versions" or normalized.startswith("/versions/"):
        fail(f"non-selector cross-version URL is not allowed: {value}")

    scoped_path = prefix + (path if path.startswith("/") else "/" + path)
    if absolute:
        return urllib.parse.urlunsplit(
            (
                origin_parts.scheme,
                origin_parts.netloc,
                scoped_path,
                parsed.query,
                parsed.fragment,
            )
        )
    return urllib.parse.urlunsplit(("", "", scoped_path, parsed.query, parsed.fragment))


def rewrite_json_urls(value, rewrite):
    if isinstance(value, dict):
        return {key: rewrite_json_urls(item, rewrite) for key, item in value.items()}
    if isinstance(value, list):
        return [rewrite_json_urls(item, rewrite) for item in value]
    if isinstance(value, str):
        return rewrite(value)
    return value


def expected_language_fallback_urls(
    relative: str, artifact_base: str
) -> dict[str, str]:
    """Resolve declared missing-translation fallbacks within the current artifact."""
    return {
        language: urllib.parse.urljoin(artifact_base, fallback.lstrip("/"))
        for language, fallback in HREFLANG_FALLBACKS.get(relative, {}).items()
    }


def language_fallback_options(action_data: dict, relative: str) -> dict[str, dict]:
    """Return manifest options covered by HREFLANG_FALLBACKS, failing closed."""
    fallbacks = HREFLANG_FALLBACKS.get(relative, {})
    if not fallbacks:
        return {}
    actions = action_data.get("actions")
    if not isinstance(actions, list):
        fail(f"action manifest has no actions array in {relative}")
    switches = [
        action
        for action in actions
        if isinstance(action, dict) and action.get("id") == "switch_language"
    ]
    if (
        len(switches) != 1
        or switches[0].get("available") is not True
        or not isinstance(switches[0].get("options"), list)
    ):
        fail(f"language switch contract missing in {relative}")
    result = {}
    for language in fallbacks:
        matches = [
            option
            for option in switches[0]["options"]
            if isinstance(option, dict) and option.get("id") == language
        ]
        if (
            len(matches) != 1
            or not isinstance(matches[0].get("url"), str)
            or matches[0].get("active") is not False
        ):
            fail(f"language fallback option mismatch in {relative}: {language}")
        result[language] = matches[0]
    return result


def scope_language_fallback_urls(
    action_data: dict, relative: str, artifact_base: str
) -> int:
    """Keep missing-translation actions inside the current version artifact."""
    expected = expected_language_fallback_urls(relative, artifact_base)
    options = language_fallback_options(action_data, relative)
    changed = 0
    for language, url in expected.items():
        option = options[language]
        if urllib.parse.urljoin(artifact_base, option["url"]) != url:
            option["url"] = url
            changed += 1
    return changed


def normalize_language_switch_urls(
    action_data: dict,
    relative: str,
    artifact_base: str,
    output: pathlib.Path,
) -> int:
    """Keep language choices on an equivalent page or the same-version locale root."""
    actions = action_data.get("actions")
    if not isinstance(actions, list):
        return 0
    switches = [
        action
        for action in actions
        if isinstance(action, dict) and action.get("id") == "switch_language"
    ]
    if len(switches) != 1 or not isinstance(switches[0].get("options"), list):
        return 0
    english_relative = relative.removeprefix("cn/")
    chinese_relative = "cn/" + english_relative
    candidates = {"en-US": english_relative, "zh-CN": chinese_relative}
    roots = {"en-US": "", "zh-CN": "cn/"}
    changed = 0
    for option in switches[0]["options"]:
        language = option.get("id")
        candidate = candidates.get(language)
        if candidate is None:
            continue
        target = output / candidate
        route = candidate
        if not target.is_file():
            route = roots[language]
        elif route.endswith("index.html"):
            route = route[: -len("index.html")]
        new_url = (
            "/" + route
            if not target.is_file()
            and urllib.parse.urlsplit(artifact_base).path == "/"
            else urllib.parse.urljoin(artifact_base, route)
        )
        if option.get("url") != new_url:
            option["url"] = new_url
            changed += 1
    return changed


def validate_language_switch_contract(
    action_data: dict,
    relative: str,
    expected_urls: dict[str, str],
    current_url: str,
    current_language: str,
) -> None:
    """Require one exact language switch whose URLs mirror page hreflang links."""
    actions = action_data.get("actions")
    if not isinstance(actions, list):
        fail(f"action manifest has no actions array in {relative}")
    switches = [
        action
        for action in actions
        if isinstance(action, dict) and action.get("id") == "switch_language"
    ]
    if (
        len(switches) != 1
        or switches[0].get("available") is not True
        or not isinstance(switches[0].get("options"), list)
    ):
        fail(f"language switch contract missing in {relative}")
    options = switches[0]["options"]
    if len(options) != len(expected_urls):
        fail(f"language switch option count mismatch in {relative}")
    actual_ids = [
        option.get("id") if isinstance(option, dict) else None for option in options
    ]
    if actual_ids != list(expected_urls):
        fail(f"language switch option order mismatch in {relative}: {actual_ids}")
    for option in options:
        language = option["id"]
        url = option.get("url")
        if not isinstance(url, str) or not url:
            fail(f"language switch URL missing in {relative}: {language}")
        url_parts = urllib.parse.urlsplit(url)
        is_root_relative = url.startswith("/") and not url.startswith("//")
        is_http_absolute = url_parts.scheme in {"http", "https"} and bool(
            url_parts.netloc
        )
        if not (is_root_relative or is_http_absolute):
            fail(f"language switch URL shape mismatch in {relative}: {url}")
        resolved_url = urllib.parse.urljoin(current_url, url)
        if resolved_url != expected_urls[language]:
            fail(
                f"language switch URL mismatch in {relative}: "
                f"{resolved_url} != {expected_urls[language]}"
            )
        if option.get("active") is not (language == current_language):
            fail(f"language switch active option mismatch in {relative}: {language}")
        if (
            option.get("title") != LANGUAGE_OPTION_TITLES.get(language)
            or option.get("available") is not True
        ):
            fail(f"language switch metadata mismatch in {relative}: {language}")


def rewrite_text_urls(text: str, rewrite, *, markdown: bool) -> tuple[str, int]:
    count = 0

    def replace_attribute(match: re.Match) -> str:
        nonlocal count
        old = match.group("url")
        new = rewrite(old)
        count += old != new
        return (
            f"{match.group('prefix')}{match.group('quote')}{new}{match.group('quote')}"
        )

    if markdown:
        in_fence = False
        lines = []
        for line in text.splitlines(keepends=True):
            if re.match(r"^\s*(```|~~~)", line):
                in_fence = not in_fence
                lines.append(line)
                continue
            if not in_fence:

                def replace_destination(match: re.Match) -> str:
                    nonlocal count
                    old = match.group("url")
                    new = rewrite(old)
                    count += old != new
                    return f"{match.group('open')}{new}{match.group('close')}"

                line = URL_ATTRIBUTE_RE.sub(replace_attribute, line)
                line = MARKDOWN_DESTINATION_RE.sub(replace_destination, line)
            lines.append(line)
        text = "".join(lines)
    else:
        text = URL_ATTRIBUTE_RE.sub(replace_attribute, text)
    return text, count


def scope_version_artifact(
    output: pathlib.Path,
    manifest: dict,
    entry: dict,
    origin: str,
) -> dict:
    """Repair URL fields Hugo cannot canonify, then return auditable counts."""
    if not entry["publishPath"] and origin.rstrip("/") == CANONICAL_ORIGIN.rstrip("/"):
        return {"files": 0, "urls": 0, "manifests": 0, "searchRefs": 0}
    allowed_paths = allowed_version_paths(manifest)
    artifact_base = base_url(origin, entry["publishPath"])

    def rewrite(value: str) -> str:
        rewritten = rewrite_internal_url(
            value,
            origin=origin,
            publish_path=entry["publishPath"],
            allowed_paths=allowed_paths,
        )
        if entry.get("archived", bool(entry.get("publishPath"))):
            original = urllib.parse.urlsplit(value)
            original_path = original.path.rstrip("/") + "/"
            version_prefix = "/" + entry["publishPath"]
            if original_path.startswith(version_prefix + "/"):
                original_path = original_path[len(version_prefix) :]
            rewritten_parts = urllib.parse.urlsplit(rewritten)
            scoped_relative = (
                rewritten_parts.path[len("/" + entry["publishPath"]) :]
                if rewritten_parts.path.startswith("/" + entry["publishPath"])
                else rewritten_parts.path
            )
            if (
                original_path in LATEST_SHARED_DOC_ROUTES
                and not target_exists(output, scoped_relative)
            ):
                return urllib.parse.urlunsplit(
                    (
                        urllib.parse.urlsplit(CANONICAL_ORIGIN).scheme,
                        urllib.parse.urlsplit(CANONICAL_ORIGIN).netloc,
                        original_path,
                        original.query,
                        original.fragment,
                    )
                )
            if not target_exists(output, scoped_relative):
                counterpart = (
                    "/cn" + scoped_relative
                    if scoped_relative.startswith("/docs/")
                    else scoped_relative.removeprefix("/cn")
                    if scoped_relative.startswith("/cn/docs/")
                    else ""
                )
                if counterpart and target_exists(output, counterpart):
                    counterpart_path = "/" + entry["publishPath"] + counterpart
                    return urllib.parse.urlunsplit(
                        (
                            urllib.parse.urlsplit(origin).scheme,
                            urllib.parse.urlsplit(origin).netloc,
                            counterpart_path,
                            original.query,
                            original.fragment,
                        )
                    )
                if re.match(
                    r"^/(?:cn/)?docs/changelog/hugegraph-0\.[^/]+-release-notes/?$",
                    scoped_relative,
                ):
                    language_prefix = "/cn" if scoped_relative.startswith("/cn/") else ""
                    changelog = f"{language_prefix}/docs/changelog/"
                    if target_exists(output, changelog):
                        return urllib.parse.urljoin(
                            base_url(origin, entry["publishPath"]),
                            changelog.lstrip("/"),
                        )
        return rewritten

    stats = {"files": 0, "urls": 0, "manifests": 0, "searchRefs": 0}
    for path in sorted(output.rglob("*")):
        if not path.is_file():
            continue
        if path.match("offline-search-index.*.json"):
            parts = path.name.split(".")
            digest = hashlib.md5(path.read_bytes()).hexdigest()
            if len(parts) != 4 or parts[2] != digest:
                fail(
                    f"stale search index fingerprint before rewrite: {path.relative_to(output)}"
                )
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                fail(f"unexpected search index shape: {path}")
            for item in data:
                if not isinstance(item, dict) or not isinstance(item.get("ref"), str):
                    fail(f"invalid search index entry: {path}")
                old = item["ref"]
                item["ref"] = rewrite(old)
                stats["searchRefs"] += old != item["ref"]
            path.write_text(
                json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
            stats["files"] += 1
            continue
        if path.suffix not in {".html", ".md", ".xml"}:
            continue
        original = path.read_text(encoding="utf-8")
        rendered, changed = rewrite_text_urls(
            original,
            rewrite,
            markdown=path.suffix == ".md",
        )

        def replace_manifest(match: re.Match) -> str:
            data = json.loads(match.group("body"))
            rewritten = rewrite_json_urls(data, rewrite)
            normalize_language_switch_urls(
                rewritten,
                path.relative_to(output).as_posix(),
                artifact_base,
                output,
            )
            stats["manifests"] += 1
            return (
                match.group("open")
                + json.dumps(rewritten, ensure_ascii=False, separators=(",", ":"))
                + match.group("close")
            )

        if path.suffix == ".html":
            rendered = ACTION_MANIFEST_RE.sub(replace_manifest, rendered)
        if rendered != original:
            path.write_text(rendered, encoding="utf-8")
            stats["files"] += 1
            stats["urls"] += changed
    renamed_indexes = []
    for path in sorted(output.glob("offline-search-index.*.json")):
        digest = hashlib.md5(path.read_bytes()).hexdigest()
        parts = path.name.split(".")
        if len(parts) != 4:
            fail(f"unexpected search index filename: {path.name}")
        new_name = f"offline-search-index.{parts[1]}.{digest}.json"
        if path.name != new_name:
            new_path = path.with_name(new_name)
            path.rename(new_path)
            renamed_indexes.append((path.name, new_name))
    for old_name, new_name in renamed_indexes:
        references = 0
        for path in sorted(output.rglob("*")):
            if not path.is_file() or path.suffix not in {
                ".html",
                ".md",
                ".xml",
                ".txt",
                ".json",
            }:
                continue
            text = path.read_text(encoding="utf-8")
            count = text.count(old_name)
            if count:
                path.write_text(text.replace(old_name, new_name), encoding="utf-8")
                references += count
        if references == 0:
            fail(f"renamed search index has no generated reference: {old_name}")
    stats["searchFingerprints"] = len(renamed_indexes)
    return stats


def write_historical_home_redirects(output: pathlib.Path, origin: str) -> int:
    normalized_origin = origin.rstrip("/") + "/"
    targets = (
        (output / "index.html", "en-US", normalized_origin, "Apache HugeGraph"),
        (
            output / "cn/index.html",
            "zh-CN",
            urllib.parse.urljoin(normalized_origin, "cn/"),
            "Apache HugeGraph",
        ),
    )
    for path, language, target, title in targets:
        escaped_target = html.escape(target, quote=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "<!doctype html>\n"
            f'<html lang="{language}"><head><meta charset="utf-8">\n'
            '<meta name="robots" content="noindex,follow">\n'
            f'<link rel="canonical" href="{escaped_target}">\n'
            f'<meta http-equiv="refresh" content="0; url={escaped_target}">\n'
            f"<title>{title}</title></head><body>\n"
            f'<p><a href="{escaped_target}">Continue to {title}</a></p>\n'
            "</body></html>\n",
            encoding="utf-8",
        )
    return len(targets)


def exclude_historical_sitemaps(output: pathlib.Path) -> int:
    """Keep archived pages directly reachable without advertising them for indexing."""
    removed = 0
    for path in sorted(output.rglob("sitemap.xml")):
        path.unlink()
        removed += 1
    robots = output / "robots.txt"
    if robots.is_file():
        robots.write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    return removed


def mark_historical_pages_noindex(output: pathlib.Path) -> int:
    """Apply the archive indexing policy to every rendered historical page."""
    changed = 0
    for path in sorted(output.rglob("*.html")):
        if path.name == "404.html":
            continue
        source = path.read_text(encoding="utf-8")
        rendered, count = ROBOTS_META_RE.subn(
            '<meta name="robots" content="noindex,follow">', source
        )
        if count:
            path.write_text(rendered, encoding="utf-8")
            changed += count
    return changed


def write_historical_route_aliases(
    output: pathlib.Path, origin: str, publish_path: str
) -> int:
    """Create deterministic locale-aware redirects for migrated flat routes."""
    written = 0
    site_base = base_url(origin, publish_path)
    for language_prefix in ("", "cn/"):
        for old_relative, new_relative in LEGACY_IA_ROUTE_MAP.items():
            old_route = language_prefix + "docs/" + old_relative.removesuffix(".md")
            old_route = old_route.replace("/README", "")
            new_route = language_prefix + "docs/" + new_relative.removesuffix(".md")
            target = output / new_route / "index.html"
            if not target.is_file():
                continue
            alias = output / old_route / "index.html"
            if alias.exists():
                fail(f"historical alias collides with rendered output: {alias}")
            alias.parent.mkdir(parents=True, exist_ok=True)
            target_url = urllib.parse.urljoin(site_base, new_route.rstrip("/") + "/")
            escaped = html.escape(target_url, quote=True)
            alias.write_text(
                "<!doctype html>\n"
                '<html><head><meta charset="utf-8">\n'
                '<meta name="robots" content="noindex,follow">\n'
                f'<link rel="canonical" href="{escaped}">\n'
                f'<meta http-equiv="refresh" content="0; url={escaped}">\n'
                f'</head><body><a href="{escaped}">Continue</a></body></html>\n',
                encoding="utf-8",
            )
            written += 1
    return written


def remove_non_equivalent_hreflang(
    output: pathlib.Path, origin: str, publish_path: str
) -> int:
    """Remove Hugo language fallbacks from hreflang while keeping real translations."""
    removed = 0
    prefix = "/" + publish_path.strip("/") if publish_path else ""
    origin_parts = urllib.parse.urlsplit(origin.rstrip("/") + "/")
    for path in sorted(output.rglob("*.html")):
        relative = path.relative_to(output).as_posix()
        if relative in {"404.html", "cn/404.html"} or "_print/" in relative:
            continue
        current_url = public_url_for_file(path, output, origin, publish_path)
        current_path = urllib.parse.urlsplit(current_url).path
        cn_prefix = prefix + "/cn/"
        if current_path.startswith(cn_prefix):
            english_path = prefix + current_path[len(prefix + "/cn") :]
        else:
            english_path = current_path
        chinese_path = (
            prefix + "/cn/"
            if english_path.rstrip("/") == prefix
            else prefix + "/cn" + english_path[len(prefix) :]
        )
        expected_paths = {"en-US": english_path, "zh-CN": chinese_path}

        def keep_equivalent(match: re.Match) -> str:
            nonlocal removed
            parser = DocumentParser()
            parser.feed(match.group(0))
            if len(parser.hreflang) != 1:
                fail(f"cannot parse hreflang link in {relative}: {match.group(0)}")
            language, href = parser.hreflang[0]
            expected_path = expected_paths.get(language)
            href_parts = urllib.parse.urlsplit(
                urllib.parse.urljoin(current_url, href)
            )
            local_relative = (
                expected_path[len(prefix) :] if prefix and expected_path else expected_path
            )
            if (
                expected_path is not None
                and href_parts.scheme == origin_parts.scheme
                and href_parts.netloc == origin_parts.netloc
                and href_parts.path == expected_path
                and target_exists(output, local_relative or "/")
            ):
                return match.group(0)
            removed += 1
            return ""

        source = path.read_text(encoding="utf-8")
        rendered = HREFLANG_LINK_RE.sub(keep_equivalent, source)
        if rendered != source:
            path.write_text(rendered, encoding="utf-8")
    return removed


def public_url_for_file(
    path: pathlib.Path,
    root: pathlib.Path,
    origin: str,
    publish_path: str,
) -> str:
    relative = path.relative_to(root).as_posix()
    if relative == "index.html":
        relative = ""
    elif relative.endswith("/index.html"):
        relative = relative[: -len("index.html")]
    base = base_url(origin, publish_path)
    return urllib.parse.urljoin(base, relative)


def target_exists(root: pathlib.Path, relative: str) -> bool:
    relative = urllib.parse.unquote(relative).lstrip("/")
    parts = pathlib.PurePosixPath(relative).parts
    if ".." in parts:
        return False
    candidate = root.joinpath(*parts)
    return candidate.is_file() or (candidate / "index.html").is_file()


def iter_json_strings(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from iter_json_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_json_strings(item)
    elif isinstance(value, str):
        yield value


def iter_json_url_fields(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"baseURL", "url", "markdown"} and isinstance(item, str):
                yield item
            else:
                yield from iter_json_url_fields(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_json_url_fields(item)


def require_docs_navigation_json(data: dict, source: str, language: str) -> None:
    """Require the five task groups in the machine-readable navigation tree."""
    expected_titles = DOCS_NAV_GROUP_TITLES.get(language)
    if expected_titles is None:
        fail(f"unsupported Docs navigation language in {source}: {language}")
    docs_nodes = [
        item
        for item in data.get("root", {}).get("children", [])
        if isinstance(item, dict) and item.get("id") == "/docs/"
    ]
    if len(docs_nodes) != 1:
        fail(f"expected one Docs node in {source}, found {len(docs_nodes)}")
    groups = docs_nodes[0].get("children")
    if not isinstance(groups, list):
        fail(f"Docs navigation children are missing in {source}")
    actual_titles = tuple(
        item.get("title") if isinstance(item, dict) else None for item in groups
    )
    if actual_titles != expected_titles:
        fail(
            f"Docs navigation groups changed in {source}: "
            f"{actual_titles!r} != {expected_titles!r}"
        )
    for group in groups:
        if group.get("kind") != "external" or not group.get("children"):
            fail(
                f"Docs navigation group is not a populated link in {source}: {group!r}"
            )
    if any("/_nav/" in value.lower() for value in iter_json_strings(data)):
        fail(f"private Docs navigation route leaked into {source}")


def validate_artifact(args: argparse.Namespace) -> None:
    manifest = load_manifest(args.manifest)
    entry = next(
        (item for item in manifest["versions"] if item["id"] == args.version), None
    )
    if entry is None:
        fail(f"unknown version {args.version}")
    root = args.artifact.resolve()
    metadata_path = root / ".version.json"
    if not metadata_path.is_file():
        fail(f"missing version metadata: {metadata_path}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    expected_base = base_url(args.site_origin, entry["publishPath"])
    expected_entry = dict(entry)
    expected_entry["sha"] = args.sha
    require_metadata_matches(expected_entry, metadata, metadata_path)
    if metadata.get("baseURL") != expected_base:
        fail(f"version metadata does not match {entry['id']} at {expected_base}")
    docs_navigation = metadata.get("docsNavigation")
    expected_docs_navigation = DOCS_NAV_EXPECTED_STATS[entry["id"]]
    if docs_navigation != expected_docs_navigation:
        fail(
            f"Docs navigation metadata mismatch for {entry['id']}: "
            f"{docs_navigation!r} != {expected_docs_navigation!r}"
        )
    if entry["archived"]:
        for shared_path in (
            "about",
            "blog",
            "client-go",
            "community",
            "cn/about",
            "cn/blog",
            "cn/community",
        ):
            if (root / shared_path).exists():
                fail(f"historical artifact contains latest-only output: {shared_path}")

    origin_parts = urllib.parse.urlsplit(args.site_origin.rstrip("/") + "/")
    canonical_parts = urllib.parse.urlsplit(CANONICAL_ORIGIN)
    origin_host = same_site_host(origin_parts)
    canonical_host = same_site_host(canonical_parts)
    prefix = "/" + entry["publishPath"].strip("/") if entry["publishPath"] else ""
    allowed_paths = allowed_version_paths(manifest)
    current_docs = (prefix + "/docs").rstrip("/") or "/docs"
    checked_urls = 0
    canonical_pages = 0
    manifest_pages = 0
    contract_data = json.loads(URL_CONTRACT.read_text(encoding="utf-8"))
    if contract_data.get("schemaVersion") != 1 or not isinstance(
        contract_data.get("routes"), list
    ):
        fail(f"invalid URL contract: {URL_CONTRACT}")
    contract_routes = 0
    for route in contract_data["routes"]:
        if entry["id"] not in route.get("versions", []):
            continue
        public_path = route.get("path")
        file_path = route.get("file")
        markers = route.get("contains")
        if (
            not isinstance(public_path, str)
            or not public_path.startswith("/")
            or not isinstance(file_path, str)
            or ".." in pathlib.PurePosixPath(file_path).parts
            or not isinstance(markers, list)
            or not all(isinstance(marker, str) and marker for marker in markers)
        ):
            fail(f"invalid URL contract route: {route!r}")
        expected_file = (
            "index.html"
            if public_path == "/"
            else public_path.lstrip("/")
            + ("index.html" if public_path.endswith("/") else "")
        )
        if file_path != expected_file:
            fail(f"URL contract path/file mismatch: {public_path} -> {file_path}")
        target = root / file_path
        if not target.is_file():
            fail(f"URL contract target missing for {entry['id']}: {public_path}")
        body = target.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in body:
                fail(
                    f"URL contract marker missing for {entry['id']} {public_path}: {marker}"
                )
        contract_routes += 1

    def validate_url(value: str, source: pathlib.Path) -> None:
        nonlocal checked_urls
        if not value or value.startswith(("#", "?")):
            return
        source_name = source.relative_to(root).as_posix()
        require_safe_url_syntax(value)
        if not require_safe_url_scheme(value, source_name):
            return
        parsed = urllib.parse.urlsplit(value)
        require_safe_http_authority(parsed, value)
        parsed_host = same_site_host(parsed) if parsed.netloc else None
        if (
            parsed.netloc
            and normalized_hostname(parsed) in {origin_host, canonical_host}
            and parsed_host is None
        ):
            fail(f"unsafe same-site URL authority in {source_name}: {value}")
        if parsed_host == canonical_host and parsed_host != origin_host:
            if re.match(r"^/versions/(?:1\.7|1\.5|1\.3|1\.0)/(?:cn/)?docs(?:/|$)", parsed.path):
                checked_urls += 1
                return
            fail(f"production-origin URL leaked into staging {source_name}: {value}")
        if parsed.netloc and parsed_host != origin_host:
            return
        if not parsed.netloc and not value.startswith("/"):
            source_relative = source.relative_to(root).as_posix()
            if source.suffix == ".xml" or source_relative.startswith(
                ("_print/", "cn/_print/")
            ):
                return
            value = urllib.parse.urljoin(
                public_url_for_file(
                    source, root, args.site_origin, entry["publishPath"]
                ),
                value,
            )
            parsed = urllib.parse.urlsplit(value)
            require_safe_http_authority(parsed, value)
            parsed_host = same_site_host(parsed) if parsed.netloc else None
        if parsed.netloc and parsed_host != origin_host:
            return
        if parsed.scheme and parsed.scheme != origin_parts.scheme:
            fail(
                f"same-site URL uses the wrong scheme in {source.relative_to(root)}: {value}"
            )
        path = parsed.path or "/"
        normalized = path.rstrip("/") or "/"
        normalized_with_slash = normalized.rstrip("/") + "/"
        if normalized_with_slash in LATEST_SHARED_DOC_ROUTES:
            checked_urls += 1
            return
        if (
            parsed.netloc
            and (normalized in allowed_paths or is_latest_shared_path(normalized))
            and normalized != current_docs
        ):
            checked_urls += 1
            return
        if prefix and not (normalized == prefix or normalized.startswith(prefix + "/")):
            fail(
                f"URL escapes version {entry['id']} in {source.relative_to(root)}: {value}"
            )
        relative = path[len(prefix) :] if prefix else path
        if not target_exists(root, relative):
            fail(f"missing local target from {source.relative_to(root)}: {value}")
        checked_urls += 1

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(root)
        if "_nav" in relative_path.parts:
            fail(f"private Docs navigation route was rendered: {relative_path}")
        if path.match("offline-search-index.*.json"):
            parts = path.name.split(".")
            digest = hashlib.md5(path.read_bytes()).hexdigest()
            if len(parts) != 4 or parts[2] != digest:
                fail(f"stale search index fingerprint: {path.relative_to(root)}")
            data = json.loads(path.read_text(encoding="utf-8"))
            for item in data:
                ref = item.get("ref") if isinstance(item, dict) else None
                if not isinstance(ref, str):
                    fail(f"invalid search entry in {path.relative_to(root)}")
                if "/_nav/" in ref.lower():
                    fail(f"private Docs navigation route leaked into search: {ref}")
                validate_url(ref, path)
            continue
        if path.name == "navigation.json":
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("schemaVersion") != 1:
                fail(f"invalid navigation schema in {path.relative_to(root)}")
            relative = path.relative_to(root).as_posix()
            language = "cn" if relative.startswith("cn/") else "en"
            expected_root_url = (
                urllib.parse.urljoin(expected_base, "cn/")
                if language == "cn"
                else expected_base
            )
            if data.get("baseURL") != expected_base or data.get("language") != language:
                fail(f"navigation baseURL/language mismatch in {relative}")
            if data.get("root", {}).get("url") != expected_root_url:
                fail(f"navigation root is not language-scoped in {relative}")
            require_docs_navigation_json(data, relative, language)
            for value in iter_json_url_fields(data):
                validate_url(value, path)
                value_parts = urllib.parse.urlsplit(value)
                if value == expected_base or (
                    value_parts.netloc and value_parts.netloc != origin_parts.netloc
                ):
                    continue
                value_path = value_parts.path
                language_prefix = prefix + "/cn/"
                if language == "cn" and not value_path.startswith(language_prefix):
                    fail(f"navigation URL loses Chinese scope in {relative}: {value}")
                if language == "en" and value_path.startswith(language_prefix):
                    fail(
                        f"navigation URL crosses into Chinese scope in {relative}: {value}"
                    )
            continue
        if path.suffix not in {".html", ".md", ".xml", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix not in {".md", ".txt"}:
            for match in URL_ATTRIBUTE_RE.finditer(text):
                validate_url(match.group("url"), path)
        if path.suffix == ".xml":
            try:
                xml_root = ET.fromstring(text)
            except ET.ParseError as error:
                fail(f"invalid XML in {path.relative_to(root)}: {error}")
            for node in xml_root.iter():
                if (
                    node.tag.split("}")[-1] in {"loc", "link", "guid"}
                    and (node.text or "").strip()
                ):
                    validate_url((node.text or "").strip(), path)
        if path.suffix in {".md", ".txt"}:
            in_fence = False
            for line in text.splitlines():
                if re.match(r"^\s*(```|~~~)", line):
                    in_fence = not in_fence
                    continue
                if not in_fence:
                    for match in URL_ATTRIBUTE_RE.finditer(line):
                        validate_url(match.group("url"), path)
                    for match in MARKDOWN_DESTINATION_RE.finditer(line):
                        validate_url(match.group("url"), path)
            relative = path.relative_to(root).as_posix()
            if path.name == "llms.txt":
                is_chinese = relative.startswith("cn/")
                for value in re.findall(r"https?://[^)\s]+", text):
                    value_path = urllib.parse.urlsplit(value).path
                    chinese_prefix = prefix + "/cn/"
                    shared_latest = is_latest_shared_path(value_path)
                    if is_chinese and not value_path.startswith(chinese_prefix):
                        if shared_latest and value_path.startswith("/cn/"):
                            continue
                        if value_path != prefix + "/index.md":
                            fail(f"Chinese llms index loses language scope: {value}")
                    if not is_chinese and value_path.startswith(chinese_prefix):
                        if value_path != prefix + "/cn/index.md":
                            fail(f"English llms index crosses language scope: {value}")
                    if (
                        not is_chinese
                        and shared_latest
                        and value_path.startswith("/cn/")
                    ):
                        fail(f"English llms index crosses language scope: {value}")
        if path.suffix != ".html":
            continue
        relative = path.relative_to(root).as_posix()
        archive_exceptions = {"404.html", "cn/404.html", "client-go/index.html"}
        canonical_exceptions = {"client-go/index.html"}
        if relative in {"404.html", "cn/404.html"} and (
            "td-site-header" not in text or "td-print-view" in text
        ):
            fail(f"404 page does not use the interactive OINK shell: {relative}")
        document = DocumentParser()
        document.feed(text)
        require_toc_accessible_name(document, relative)
        alias_target = refresh_target(document)
        if entry["archived"] and relative not in {"404.html", "cn/404.html"}:
            robots = [
                re.sub(r"\s+", "", item.get("content", "").lower())
                for item in document.meta
                if item.get("name", "").lower() == "robots"
            ]
            if robots != ["noindex,follow"]:
                fail(f"historical page must be noindex,follow: {relative}: {robots!r}")
        if alias_target:
            validate_url(alias_target, path)
        action_data = {}
        manifests = list(ACTION_MANIFEST_RE.finditer(text))
        if manifests:
            if len(manifests) != 1:
                fail(f"unexpected action manifest count in {path.relative_to(root)}")
            action_data = json.loads(manifests[0].group("body"))
            for value in iter_json_url_fields(action_data):
                if value:
                    validate_url(value, path)
            actions = {
                item.get("id"): item
                for item in action_data.get("actions", [])
                if isinstance(item, dict)
            }
            for action_id in ("open_chatgpt", "open_claude"):
                action = actions.get(action_id)
                placements = action.get("placements", {}) if action else {}
                if (
                    not action
                    or action.get("available") is not False
                    or action.get("url") != ""
                    or placements.get("page") is not False
                    or placements.get("palette") is not False
                ):
                    fail(
                        f"assistant action is externally enabled in "
                        f"{path.relative_to(root)}: {action_id}"
                    )
            switch = next(
                (
                    item
                    for item in action_data.get("actions", [])
                    if item.get("id") == "switch_version"
                ),
                None,
            )
            language = "cn" if relative.startswith("cn/") else "en"
            expected_options = version_urls(
                manifest,
                args.site_origin,
                language,
                getattr(args, "historical_origin", None),
            )
            if switch is None or [
                (
                    item.get("id"),
                    item.get("title"),
                    str(item.get("url", "")).rstrip("/"),
                    item.get("active"),
                )
                for item in switch.get("options", [])
            ] != [
                (
                    item["version"],
                    item["name"],
                    item["url"].rstrip("/"),
                    item["version"] == entry["id"],
                )
                for item in expected_options
            ]:
                fail(f"version switch contract mismatch in {path.relative_to(root)}")
            if (
                entry["archived"]
                and relative not in archive_exceptions
                and not relative.startswith(("_print/", "cn/_print/"))
                and "td-page-notice--primary" not in text
            ):
                fail(f"archive notice missing in {path.relative_to(root)}")
            manifest_pages += 1

        for _attribute, value in document.urls:
            validate_url(value, path)
            hostname = (urllib.parse.urlsplit(value).hostname or "").lower()
            if hostname in {"chatgpt.com", "claude.ai", "anthropic.com"}:
                fail(f"assistant link is externally enabled in {relative}: {value}")

        canonical_tags = [
            tag
            for tag in re.findall(r"<link\b[^>]*>", text, flags=re.IGNORECASE)
            if re.search(
                r"\brel=[\"']?canonical(?:[\"'\s>]|$)", tag, flags=re.IGNORECASE
            )
        ]
        if require_error_document_without_canonical(relative, canonical_tags):
            pass
        elif relative in canonical_exceptions:
            if len(canonical_tags) > 1:
                fail(f"too many canonicals on special page {relative}")
            if canonical_tags:
                match = URL_ATTRIBUTE_RE.search(canonical_tags[0])
                if match is None:
                    fail(f"cannot parse canonical in {relative}")
                validate_url(match.group("url"), path)
                canonical_pages += 1
        else:
            if len(canonical_tags) != 1:
                fail(
                    f"expected one canonical in {relative}, found {len(canonical_tags)}"
                )
            match = URL_ATTRIBUTE_RE.search(canonical_tags[0])
            if match is None or not canonical_tags[0].lower().startswith("<link"):
                fail(f"cannot parse canonical in {relative}")
            validate_url(match.group("url"), path)
            actual_canonical = match.group("url")
            if alias_target:
                expected_canonical = urllib.parse.urljoin(expected_base, alias_target)
            elif "_print/" in relative:
                parts = list(pathlib.PurePosixPath(relative).parts)
                parts.remove("_print")
                regular = pathlib.PurePosixPath(*parts).as_posix()
                if regular.endswith("index.html"):
                    regular = regular[: -len("index.html")]
                expected_canonical = urllib.parse.urljoin(expected_base, regular)
            else:
                expected_canonical = public_url_for_file(
                    path, root, args.site_origin, entry["publishPath"]
                )
            if actual_canonical != expected_canonical:
                fail(
                    f"canonical mismatch in {relative}: "
                    f"{actual_canonical} != {expected_canonical}"
                )
            canonical_pages += 1

        is_regular_page = (
            "_print/" not in relative
            and relative not in archive_exceptions
            and not alias_target
        )
        if is_regular_page:
            actual_hreflang = dict(document.hreflang)
            if len(actual_hreflang) != len(document.hreflang):
                fail(f"duplicate hreflang entries in {relative}")
            current_path = public_url_for_file(
                path, root, args.site_origin, entry["publishPath"]
            )
            current_parts = urllib.parse.urlsplit(current_path)
            language_base_path = prefix + "/cn/"
            if current_parts.path.startswith(language_base_path):
                english_path = prefix + current_parts.path[len(prefix + "/cn") :]
            else:
                english_path = current_parts.path
            chinese_path = (
                prefix + "/cn/"
                if english_path.rstrip("/") == prefix
                else prefix + "/cn" + english_path[len(prefix) :]
            )
            equivalent_urls = {
                "en-US": urllib.parse.urlunsplit(
                    (origin_parts.scheme, origin_parts.netloc, english_path, "", "")
                ),
                "zh-CN": urllib.parse.urlunsplit(
                    (origin_parts.scheme, origin_parts.netloc, chinese_path, "", "")
                ),
            }
            equivalent_paths = {
                "en-US": english_path[len(prefix) :] if prefix else english_path,
                "zh-CN": chinese_path[len(prefix) :] if prefix else chinese_path,
            }
            expected_hreflang = {
                language: url
                for language, url in equivalent_urls.items()
                if target_exists(root, equivalent_paths[language])
            }
            if actual_hreflang != expected_hreflang:
                fail(
                    f"hreflang mismatch in {relative}: "
                    f"{actual_hreflang} != {expected_hreflang}"
                )
            validate_language_switch_contract(
                action_data,
                relative,
                {
                    "en-US": expected_hreflang.get("en-US", expected_base),
                    "zh-CN": expected_hreflang.get(
                        "zh-CN", urllib.parse.urljoin(expected_base, "cn/")
                    ),
                },
                current_path,
                "zh-CN" if relative.startswith("cn/") else "en-US",
            )

    if not entry["archived"]:
        client_go = root / "client-go/index.html"
        if not client_go.is_file():
            fail("missing client-go/index.html")
        client_parser = DocumentParser()
        client_parser.feed(client_go.read_text(encoding="utf-8"))
        go_import = [
            item.get("content", "")
            for item in client_parser.meta
            if item.get("name") == "go-import"
        ]
        if go_import != [
            "hugegraph.apache.org/client-go git "
            "https://github.com/apache/hugegraph-toolchain.git"
        ]:
            fail("client-go go-import metadata changed")
        expected_go_source = (
            "hugegraph.apache.org/client-go "
            "https://github.com/apache/hugegraph-toolchain "
            "https://github.com/apache/hugegraph-toolchain/tree/master/"
            "hugegraph-client-go{/dir} https://github.com/apache/hugegraph-toolchain/"
            "blob/master/hugegraph-client-go{/dir}/{file}#L{line}"
        )
        go_source = [
            item.get("content", "")
            for item in client_parser.meta
            if item.get("name") == "go-source"
        ]
        if go_source != [expected_go_source]:
            fail("client-go go-source metadata changed")
        package_url = "https://pkg.go.dev/hugegraph.apache.org/client-go"
        if refresh_target(client_parser) != package_url:
            fail("client-go refresh target changed")
        if [url for attribute, url in client_parser.urls if attribute == "href"] != [
            package_url
        ]:
            fail("client-go visible redirect link changed")

    if manifest_pages == 0 or canonical_pages == 0:
        fail("artifact validation did not inspect rendered pages")
    print(
        f"validated {entry['id']}: {canonical_pages} canonical pages, "
        f"{manifest_pages} action manifests, {checked_urls} internal URLs, "
        f"{contract_routes} contract routes"
    )


def derived_version_config(
    manifest: dict,
    entry: dict,
    site_origin: str,
    historical_origin: str | None = None,
) -> dict:
    """Derive every Hugo version-menu value from versions.json."""
    override = {
        "baseURL": base_url(site_origin, entry["publishPath"]),
        "canonifyURLs": True,
        "params": {
            "version": entry["id"],
            "version_menu": "Releases",
            "version_menu_pagelinks": False,
            "versions": version_urls(
                manifest, site_origin, "en", historical_origin
            ),
            "archived_version": bool(entry["archived"]),
            "url_latest_version": urllib.parse.urljoin(
                site_origin.rstrip("/") + "/", "docs/"
            ),
            "github_repo": "https://github.com/apache/hugegraph-doc",
            "github_branch": entry["githubBranch"],
        },
    }
    language_overrides = (
        historical_language_menus(site_origin)
        if entry["archived"]
        else {"en": {}, "cn": {}}
    )
    for language in ("en", "cn"):
        language_overrides[language]["params"] = language_version_params(
            manifest,
            site_origin,
            language,
            historical_origin,
        )
    override["languages"] = language_overrides
    return override


def render_config(args: argparse.Namespace) -> None:
    """Write the manifest-derived override used by direct Hugo commands."""
    manifest = load_manifest(args.manifest)
    entry = next(
        (item for item in manifest["versions"] if item["id"] == args.version), None
    )
    if entry is None:
        fail(f"unknown version {args.version}")
    override = derived_version_config(
        manifest, entry, args.site_origin, args.historical_origin
    )
    rendered = json.dumps(override, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    args.output.write_text(rendered, encoding="utf-8")
    print(f"rendered Hugo config for {entry['id']} -> {args.output}")


def build(args: argparse.Namespace) -> None:
    manifest = load_manifest(args.manifest)
    entry = next(
        (item for item in manifest["versions"] if item["id"] == args.version), None
    )
    if entry is None:
        fail(f"unknown version {args.version}")
    if not SHA_RE.fullmatch(args.sha):
        fail(f"invalid source SHA: {args.sha}")
    try:
        run(["git", "cat-file", "-e", f"{args.sha}^{{commit}}"])
    except subprocess.CalledProcessError:
        run(["git", "fetch", "--no-tags", "origin", args.sha])

    output = prepare_output_directory(args.output, "version output")

    with tempfile.TemporaryDirectory(prefix=f"hugegraph-{args.version}-") as temp_name:
        assembly = pathlib.Path(temp_name) / "site"
        subprocess.run(
            [
                "git",
                "clone",
                "--quiet",
                "--shared",
                "--no-checkout",
                str(ROOT),
                str(assembly),
            ],
            cwd=ROOT,
            check=True,
        )
        subprocess.run(
            ["git", "checkout", "--quiet", "--detach", args.sha],
            cwd=assembly,
            check=True,
        )
        overlay_shell(
            assembly,
            historical=bool(entry["archived"]),
            origin=args.site_origin,
        )
        site_base = base_url(args.site_origin, entry["publishPath"])
        override = derived_version_config(
            manifest, entry, args.site_origin, args.historical_origin
        )
        override_path = assembly / "version-config.json"
        override_path.write_text(
            json.dumps(override, ensure_ascii=False), encoding="utf-8"
        )
        hugo = os.environ.get("HUGO_BIN", "hugo")
        go = os.environ.get("GO_BIN", "go")
        go_executable = shutil.which(go)
        if go_executable is None:
            fail(f"Go executable is unavailable: {go}")
        module_result = subprocess.run(
            [
                go_executable,
                "mod",
                "download",
                "-json",
                "github.com/pgsty/oink@v1.0.0",
            ],
            cwd=assembly,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        module = json.loads(module_result.stdout)
        if (
            module.get("Path") != "github.com/pgsty/oink"
            or module.get("Version") != "v1.0.0"
            or module.get("Sum") != "h1:E+WHFP9zSRT+5RKoIkWNp+ASRGS1BKG+rDEi9by/BjE="
        ):
            fail(f"unexpected OINK module metadata: {module!r}")
        migration_script = pathlib.Path(module["Dir"]) / "bin/migrations/oink06.py"
        if not migration_script.is_file():
            fail(f"pinned OINK migration tool is absent: {migration_script}")
        migration_report = assembly / ".oink06-migration.json"
        migration_python = os.environ.get("OINK_PYTHON", sys.executable)
        subprocess.run(
            [
                migration_python,
                str(migration_script),
                "migrate",
                "--site",
                str(assembly),
                "--paths",
                "content",
                "--write",
                "--json",
                str(migration_report),
                "--quiet",
            ],
            cwd=assembly,
            check=True,
        )
        route_migrations = migrate_legacy_information_architecture(
            assembly, entry["id"]
        )
        known_fixes = apply_known_legacy_fixes(assembly, entry["id"])
        docs_navigation = materialize_docs_navigation(assembly, entry["publishPath"])
        subprocess.run(
            [
                migration_python,
                str(migration_script),
                "check",
                "--site",
                str(assembly),
                "--paths",
                "content",
            ],
            cwd=assembly,
            check=True,
        )
        command = [
            hugo,
            "--config",
            "hugo.yaml,version-config.json",
            "--destination",
            str(output),
            "--cleanDestinationDir",
            "--gc",
            "--minify",
            "--environment",
            "production",
            "--printPathWarnings",
            "--printI18nWarnings",
            "--panicOnWarning",
            "--logLevel",
            "info",
        ]
        build_environment = os.environ.copy()
        go_directory = str(pathlib.Path(go_executable).resolve().parent)
        build_environment["PATH"] = (
            go_directory + os.pathsep + build_environment.get("PATH", "")
        )
        subprocess.run(command, cwd=assembly, check=True, env=build_environment)
        route_aliases = (
            write_historical_route_aliases(
                output, args.site_origin, entry["publishPath"]
            )
            if entry["id"] in {"1.3", "1.0"}
            else 0
        )
        archived_noindex = (
            mark_historical_pages_noindex(output) if entry["archived"] else 0
        )
        non_equivalent_hreflang = remove_non_equivalent_hreflang(
            output, args.site_origin, entry["publishPath"]
        )
        historical_sitemaps = (
            exclude_historical_sitemaps(output) if entry["archived"] else 0
        )
        url_scoping = scope_version_artifact(
            output,
            manifest,
            entry,
            args.site_origin,
        )
        url_scoping["historicalHomeRedirects"] = (
            write_historical_home_redirects(output, args.site_origin)
            if entry["archived"]
            else 0
        )
        subprocess.run(
            [
                migration_python,
                str(ROOT / "dist/validate-site-output.py"),
                str(output),
                site_base,
                "--security-only",
            ],
            cwd=assembly,
            check=True,
        )
        metadata = dict(entry)
        migration_data = json.loads(migration_report.read_text(encoding="utf-8"))
        metadata.update(
            {
                "sha": args.sha,
                "baseURL": site_base,
                "migration": {
                    "files": len(migration_data.get("files", [])),
                    "changed": sum(
                        1
                        for item in migration_data.get("files", [])
                        if item.get("changed")
                    ),
                    "findings": sum(
                        len(item.get("findings", []))
                        for item in migration_data.get("files", [])
                    ),
                    "knownFixes": known_fixes,
                    "routeMigrations": route_migrations,
                    "residual": 0,
                },
                "docsNavigation": docs_navigation,
                "urlScoping": url_scoping,
                "historicalSitemapsRemoved": historical_sitemaps,
                "historicalNoindexPages": archived_noindex,
                "historicalRouteAliases": route_aliases,
                "nonEquivalentHreflangRemoved": non_equivalent_hreflang,
            }
        )
        (output / ".version.json").write_text(
            json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"built {entry['id']}@{args.sha} -> {output} ({site_base})")


def sitemap_locations(path: pathlib.Path) -> list[str]:
    return [
        node.text or "" for node in ET.parse(path).iter() if node.tag.endswith("loc")
    ]


def write_aggregate_sitemap(output: pathlib.Path, origin: str, manifest: dict) -> None:
    locations = [
        urllib.parse.urljoin(origin.rstrip("/") + "/", "en/sitemap.xml"),
        urllib.parse.urljoin(origin.rstrip("/") + "/", "cn/sitemap.xml"),
    ]
    root = ET.Element(
        "sitemapindex", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
    )
    for location in locations:
        item = ET.SubElement(root, "sitemap")
        ET.SubElement(item, "loc").text = location
    ET.indent(root)
    ET.ElementTree(root).write(
        output / "sitemap.xml", encoding="utf-8", xml_declaration=True
    )


def copy_without_collision(
    source: pathlib.Path, destination: pathlib.Path, seen: set[str]
) -> None:
    for path in sorted(source.rglob("*")):
        if path.is_dir():
            continue
        relative = path.relative_to(source).as_posix()
        target_relative = (destination / relative).as_posix()
        if target_relative in seen:
            fail(f"aggregate path collision: {target_relative}")
        seen.add(target_relative)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def write_error_documents(output: pathlib.Path, seen: set[str]) -> int:
    """Install localized Apache error documents beside every generated 404 page."""
    template = (ROOT / ".htaccess").read_text(encoding="utf-8")
    if template != (
        'RedirectMatch 404 "(?i)(?:^|/)\\.git(?:/|$)"\nErrorDocument 404 /404.html\n'
    ):
        fail("unexpected root .htaccess contract")
    root_page = output / "404.html"
    if not root_page.is_file():
        fail("aggregate root 404.html is required before writing .htaccess")
    root_target = output / ".htaccess"
    if root_target.exists() or ".htaccess" in seen:
        fail("aggregate error-document collision: .htaccess")
    root_target.write_text(template, encoding="utf-8")
    seen.add(".htaccess")
    count = 1
    for page in sorted(output.rglob("404.html")):
        relative = page.relative_to(output).as_posix()
        if relative == "404.html":
            continue
        target = page.parent / ".htaccess"
        target_relative = target.relative_to(output).as_posix()
        if target.exists() or target_relative in seen:
            fail(f"aggregate error-document collision: {target_relative}")
        target.write_text(f"ErrorDocument 404 /{relative}\n", encoding="utf-8")
        seen.add(target_relative)
        count += 1
    return count


def validate_output_security(output: pathlib.Path, site_origin: str) -> None:
    """Re-scan a complete output tree before it can be published."""
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "dist/validate-site-output.py"),
            str(output),
            site_origin,
            "--security-only",
        ],
        cwd=ROOT,
        check=True,
    )


def aggregate(args: argparse.Namespace) -> None:
    manifest = load_resolved_manifest(args.resolved_manifest)
    selected = selected_version_ids(getattr(args, "select", None))
    output = prepare_output_directory(args.output, "aggregate output")
    output.mkdir(parents=True)
    seen: set[str] = set()
    resolved = []
    for entry in manifest["versions"]:
        if entry["id"] not in selected:
            continue
        source = args.artifacts / (
            f"{args.artifact_prefix}{entry['id']}"
            f"{getattr(args, 'artifact_suffix', '')}"
        )
        metadata_path = source / ".version.json"
        if not metadata_path.is_file():
            fail(f"missing version metadata: {metadata_path}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        require_metadata_matches(entry, metadata, metadata_path)
        validate_artifact(
            argparse.Namespace(
                manifest=args.resolved_manifest,
                version=entry["id"],
                sha=entry["sha"],
                site_origin=args.site_origin,
                artifact=source,
            )
        )
        destination = output / entry["publishPath"]
        destination.mkdir(parents=True, exist_ok=True)
        copy_without_collision(source, destination, seen)
        resolved.append(metadata)
    error_documents = write_error_documents(output, seen)
    write_aggregate_sitemap(output, args.site_origin, manifest)
    expected_sitemaps = sitemap_locations(output / "sitemap.xml")
    for location in expected_sitemaps:
        parsed = urllib.parse.urlsplit(location)
        origin_parts = urllib.parse.urlsplit(args.site_origin.rstrip("/") + "/")
        if parsed.scheme != origin_parts.scheme or parsed.netloc != origin_parts.netloc:
            fail(f"aggregate sitemap escapes the configured origin: {location}")
        if not target_exists(output, parsed.path):
            fail(f"aggregate sitemap target is missing: {location}")
    asf_text = (ROOT / ".asf.yaml").read_text(encoding="utf-8")
    if args.asf_profile or args.asf_whoami:
        if not args.asf_profile or not args.asf_whoami:
            fail("ASF staging profile and whoami must be set together")
        old_staging = "staging:\n  profile: ~\n  whoami: asf-staging"
        new_staging = (
            f"staging:\n  profile: {args.asf_profile}\n  whoami: {args.asf_whoami}"
        )
        if asf_text.count(old_staging) != 1:
            fail("cannot locate the exact ASF staging block")
        asf_text = asf_text.replace(old_staging, new_staging)
    (output / ".asf.yaml").write_text(asf_text, encoding="utf-8")
    metadata_dir = output / "build-metadata"
    metadata_dir.mkdir()
    (metadata_dir / "versions.json").write_text(
        json.dumps(
            {"schemaVersion": 1, "versions": resolved},
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    validate_output_security(output, args.site_origin)
    print(
        f"aggregated {len(resolved)} versions and {len(seen)} files "
        f"with {error_documents} error documents -> {output}"
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--manifest", type=pathlib.Path, default=ROOT / "versions.json")
    commands = result.add_subparsers(dest="command", required=True)

    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--local", action="store_true")
    prepare_parser.add_argument("--latest-sha", default="HEAD")
    prepare_parser.add_argument("--select")
    prepare_parser.add_argument("--output", type=pathlib.Path)
    prepare_parser.set_defaults(func=prepare)

    config_parser = commands.add_parser("config")
    config_parser.add_argument("--version", default="latest")
    config_parser.add_argument("--site-origin", default=CANONICAL_ORIGIN)
    config_parser.add_argument("--historical-origin")
    config_parser.add_argument("--output", type=pathlib.Path, required=True)
    config_parser.set_defaults(func=render_config)

    build_parser = commands.add_parser("build")
    build_parser.add_argument("--version", required=True)
    build_parser.add_argument("--sha", required=True)
    build_parser.add_argument("--site-origin", required=True)
    build_parser.add_argument("--historical-origin")
    build_parser.add_argument("--output", type=pathlib.Path, required=True)
    build_parser.set_defaults(func=build)

    validate_parser = commands.add_parser("validate")
    validate_parser.add_argument("--version", required=True)
    validate_parser.add_argument("--sha", required=True)
    validate_parser.add_argument("--site-origin", required=True)
    validate_parser.add_argument("--historical-origin")
    validate_parser.add_argument("--artifact", type=pathlib.Path, required=True)
    validate_parser.set_defaults(func=validate_artifact)

    aggregate_parser = commands.add_parser("aggregate")
    aggregate_parser.add_argument("--artifacts", type=pathlib.Path, required=True)
    aggregate_parser.add_argument("--artifact-prefix", default="")
    aggregate_parser.add_argument("--artifact-suffix", default="")
    aggregate_parser.add_argument(
        "--resolved-manifest", type=pathlib.Path, required=True
    )
    aggregate_parser.add_argument("--site-origin", required=True)
    aggregate_parser.add_argument("--select")
    aggregate_parser.add_argument("--output", type=pathlib.Path, required=True)
    aggregate_parser.add_argument("--asf-profile")
    aggregate_parser.add_argument("--asf-whoami")
    aggregate_parser.set_defaults(func=aggregate)
    return result


def main() -> None:
    args = parser().parse_args()
    args.manifest = args.manifest.resolve()
    if hasattr(args, "resolved_manifest"):
        args.resolved_manifest = args.resolved_manifest.resolve()
    args.func(args)


if __name__ == "__main__":
    main()
