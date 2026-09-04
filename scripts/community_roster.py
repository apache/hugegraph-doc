#!/usr/bin/env python3
"""Refresh and validate the offline Apache HugeGraph community roster."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "community"
ROSTER_PATH = DATA_DIR / "roster.json"
MAP_PATH = DATA_DIR / "github-map.json"
AVATAR_DIR = ROOT / "static" / "img" / "community" / "avatars"
PROJECT = "hugegraph"
SCHEMA_VERSION = 1
SOURCES = {
    "committee": "https://whimsy.apache.org/public/committee-info.json",
    "projects": "https://whimsy.apache.org/public/public_ldap_projects.json",
    "people": "https://whimsy.apache.org/public/public_ldap_people.json",
}
JSON_LIMIT = 16 * 1024 * 1024
AVATAR_LIMIT = 5 * 1024 * 1024
ASF_ID_PATTERN = re.compile(r"^[a-z][a-z0-9._-]*$")
GITHUB_LOGIN_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
AVATAR_PATH_PATTERN = re.compile(r"^/img/community/avatars/([0-9a-f]{64})\.webp$")


class RosterError(ValueError):
    pass


def _read_json(path: pathlib.Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RosterError(f"{path.relative_to(ROOT)}: invalid JSON: {exc}") from exc


def _read_bounded_response(response, *, expected_hosts: set[str], content_types: set[str], limit: int, kind: str) -> bytes:
    final_url = response.geturl()
    parsed = urllib.parse.urlparse(final_url)
    if parsed.scheme != "https" or parsed.hostname not in expected_hosts:
        raise RosterError(f"{kind}: redirect target is not allowlisted: {final_url}")
    content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    if content_type not in content_types and not (kind == "JSON source" and content_type.endswith("+json")):
        raise RosterError(f"{kind}: unsupported Content-Type {content_type!r}")
    raw = response.read(limit + 1)
    if len(raw) > limit:
        raise RosterError(f"{kind}: response exceeds {limit} bytes")
    return raw


def _fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "apache-hugegraph-doc-community-roster/1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RosterError(f"{url}: HTTP {response.status}")
        raw = _read_bounded_response(
            response,
            expected_hosts={"whimsy.apache.org"},
            content_types={"application/json"},
            limit=JSON_LIMIT,
            kind="JSON source",
        )
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RosterError(f"{url}: malformed JSON: {exc}") from exc
    if not isinstance(result, dict):
        raise RosterError(f"{url}: JSON root must be an object")
    return result


def _person_name(people: dict, asf_id: str) -> str:
    if not ASF_ID_PATTERN.fullmatch(asf_id):
        raise RosterError(f"invalid ASF ID {asf_id!r}")
    record = people.get("people", {}).get(asf_id)
    name = record.get("name") if isinstance(record, dict) else None
    if isinstance(name, list):
        name = name[0] if name else ""
    if not isinstance(name, str) or not name.strip():
        raise RosterError(f"people source has no public name for ASF ID {asf_id!r}")
    return name.strip()


def _initials(name: str) -> str:
    parts = [part for part in name.replace("-", " ").split() if part]
    return "".join(part[0].upper() for part in parts[:2]) or "?"


def _sort_key(asf_id: str, names: dict[str, str]) -> tuple[str, str]:
    return names[asf_id].casefold(), asf_id.casefold()


def _validate_mapping(data: dict, roster_ids: set[str] | None = None) -> dict:
    if data.get("schema_version") != SCHEMA_VERSION:
        raise RosterError("github-map.json: schema_version must be 1")
    mappings = data.get("mappings")
    if not isinstance(mappings, dict):
        raise RosterError("github-map.json: mappings must be an object")
    logins: set[str] = set()
    user_ids: set[int] = set()
    for asf_id, mapping in mappings.items():
        if not ASF_ID_PATTERN.fullmatch(asf_id):
            raise RosterError(f"github-map.json: invalid ASF ID {asf_id!r}")
        if roster_ids is not None and asf_id not in roster_ids:
            raise RosterError(f"github-map.json: unknown ASF ID {asf_id!r}")
        if not isinstance(mapping, dict):
            raise RosterError(f"github-map.json: mapping for {asf_id!r} must be an object")
        login, user_id = mapping.get("login"), mapping.get("user_id")
        if not isinstance(login, str) or not login.strip() or login != login.strip():
            raise RosterError(f"github-map.json: {asf_id!r} needs a reviewed login")
        if not GITHUB_LOGIN_PATTERN.fullmatch(login) or "--" in login:
            raise RosterError(f"github-map.json: invalid GitHub login {login!r}")
        if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
            raise RosterError(f"github-map.json: {asf_id!r} needs a positive numeric user_id")
        if login.casefold() in logins:
            raise RosterError(f"github-map.json: duplicate GitHub login {login!r}")
        if user_id in user_ids:
            raise RosterError(f"github-map.json: duplicate GitHub user_id {user_id}")
        logins.add(login.casefold())
        user_ids.add(user_id)
    return mappings


def _webp_dimensions(raw: bytes) -> tuple[int, int]:
    if len(raw) < 30 or raw[:4] != b"RIFF" or raw[8:12] != b"WEBP":
        raise RosterError("avatar is not a WebP image")
    chunk = raw[12:16]
    if chunk == b"VP8X":
        return 1 + int.from_bytes(raw[24:27], "little"), 1 + int.from_bytes(raw[27:30], "little")
    if chunk == b"VP8L":
        bits = int.from_bytes(raw[21:25], "little")
        return 1 + (bits & 0x3FFF), 1 + ((bits >> 14) & 0x3FFF)
    if chunk == b"VP8 ":
        marker = raw.find(b"\x9d\x01\x2a", 20)
        if marker < 0 or marker + 7 > len(raw):
            raise RosterError("avatar has an invalid VP8 frame")
        width, height = struct.unpack_from("<HH", raw, marker + 3)
        return width & 0x3FFF, height & 0x3FFF
    raise RosterError(f"avatar uses unsupported WebP chunk {chunk!r}")


def _webp_chunk_kinds(raw: bytes) -> list[bytes]:
    if len(raw) < 20 or raw[:4] != b"RIFF" or raw[8:12] != b"WEBP":
        raise RosterError("avatar is not a WebP image")
    if int.from_bytes(raw[4:8], "little") != len(raw) - 8:
        raise RosterError("avatar has an invalid RIFF length")
    kinds: list[bytes] = []
    cursor = 12
    while cursor + 8 <= len(raw):
        kind = raw[cursor : cursor + 4]
        size = int.from_bytes(raw[cursor + 4 : cursor + 8], "little")
        cursor += 8 + size + (size % 2)
        if cursor > len(raw):
            raise RosterError("avatar has a truncated WebP chunk")
        kinds.append(kind)
    if cursor != len(raw):
        raise RosterError("avatar has trailing WebP data")
    return kinds


def _validate_webp(raw: bytes, expected_dimensions: tuple[int, int] | None = None) -> tuple[int, int]:
    dimensions = _webp_dimensions(raw)
    kinds = _webp_chunk_kinds(raw)
    if not any(kind in {b"VP8 ", b"VP8L"} for kind in kinds):
        raise RosterError("avatar has no decodable WebP image bitstream")
    if any(kind in {b"EXIF", b"XMP ", b"ICCP"} for kind in kinds):
        raise RosterError("avatar contains metadata")
    if expected_dimensions and dimensions != expected_dimensions:
        raise RosterError(f"avatar dimensions are {dimensions}, expected {expected_dimensions}")
    decoder = shutil.which("dwebp")
    if not decoder:
        raise RosterError("validating mapped avatars requires dwebp")
    with tempfile.TemporaryDirectory(prefix="hugegraph-avatar-decode-") as work:
        source = pathlib.Path(work) / "avatar.webp"
        target = pathlib.Path(work) / "avatar.ppm"
        source.write_bytes(raw)
        try:
            result = subprocess.run(
                [decoder, str(source), "-o", str(target)],
                text=True,
                capture_output=True,
                timeout=20,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RosterError(f"dwebp could not decode avatar: {exc}") from exc
        if result.returncode or not target.is_file():
            raise RosterError(f"dwebp rejected avatar: {result.stderr.strip()}")
    return dimensions


def _strip_webp_metadata(raw: bytes) -> bytes:
    """Remove optional metadata chunks while preserving the image bitstream."""
    _webp_dimensions(raw)
    chunks: list[bytes] = []
    cursor = 12
    while cursor + 8 <= len(raw):
        kind = raw[cursor : cursor + 4]
        size = int.from_bytes(raw[cursor + 4 : cursor + 8], "little")
        end = cursor + 8 + size + (size % 2)
        if end > len(raw):
            raise RosterError("avatar has a truncated WebP chunk")
        chunk = bytearray(raw[cursor:end])
        if kind not in {b"EXIF", b"XMP ", b"ICCP"}:
            if kind == b"VP8X":
                chunk[8] &= ~0x2D
            chunks.append(bytes(chunk))
        cursor = end
    if cursor != len(raw):
        raise RosterError("avatar has trailing WebP data")
    payload = b"WEBP" + b"".join(chunks)
    return b"RIFF" + len(payload).to_bytes(4, "little") + payload


def _avatar_bytes(user_id: int) -> bytes:
    request = urllib.request.Request(
        f"https://avatars.githubusercontent.com/u/{user_id}?s=128&v=4",
        headers={"Accept": "image/webp", "User-Agent": "apache-hugegraph-doc-community-roster/1"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = _read_bounded_response(
            response,
            expected_hosts={"avatars.githubusercontent.com"},
            content_types={"image/png", "image/jpeg", "image/webp"},
            limit=AVATAR_LIMIT,
            kind="GitHub avatar",
        )
    try:
        raw = _strip_webp_metadata(raw)
    except RosterError:
        converter = shutil.which("cwebp")
        if not converter:
            raise RosterError("mapped avatars require cwebp when GitHub does not return WebP")
        with tempfile.TemporaryDirectory(prefix="hugegraph-avatar-") as work:
            source = pathlib.Path(work) / "source"
            target = pathlib.Path(work) / "avatar.webp"
            source.write_bytes(raw)
            try:
                result = subprocess.run(
                    [converter, "-quiet", "-resize", "128", "128", "-metadata", "none", str(source), "-o", str(target)],
                    text=True,
                    capture_output=True,
                    timeout=20,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise RosterError(f"cwebp failed for numeric GitHub user ID {user_id}: {exc}") from exc
            if result.returncode:
                raise RosterError(f"cwebp failed for numeric GitHub user ID {user_id}: {result.stderr.strip()}")
            raw = _strip_webp_metadata(target.read_bytes())
    _validate_webp(raw, expected_dimensions=(128, 128))
    return raw


def _member(asf_id: str, name: str, chair: bool, mapping: dict | None) -> dict:
    member = {
        "asf_id": asf_id,
        "name": name,
        "initials": _initials(name),
        "chair": chair,
        "profile_url": f"https://people.apache.org/phonebook.html?uid={asf_id}",
    }
    if mapping:
        member["github"] = {"login": mapping["login"], "user_id": mapping["user_id"]}
    return member


def build_roster(committee_data: dict, projects_data: dict, people_data: dict, mapping_data: dict) -> dict:
    project = projects_data.get("projects", {}).get(PROJECT)
    committee = committee_data.get("committees", {}).get(PROJECT)
    if not isinstance(project, dict) or not isinstance(committee, dict):
        raise RosterError("ASF sources do not contain the HugeGraph project")
    owners, members = project.get("owners"), project.get("members")
    chair_map, committee_roster = committee.get("chair"), committee.get("roster")
    if not isinstance(owners, list) or not isinstance(members, list):
        raise RosterError("LDAP project owners/members must be arrays")
    if not isinstance(chair_map, dict) or len(chair_map) != 1:
        raise RosterError("committee source must name exactly one Chair")
    if not isinstance(committee_roster, dict):
        raise RosterError("committee roster must be an object")
    owner_ids, member_ids = set(owners), set(members)
    chair = next(iter(chair_map))
    if not owner_ids <= member_ids:
        raise RosterError("LDAP owners must be a subset of members")
    if chair not in owner_ids:
        raise RosterError("Chair must be an LDAP owner")
    if owner_ids != set(committee_roster):
        raise RosterError("committee roster and LDAP owners disagree")
    mappings = _validate_mapping(mapping_data, member_ids)
    names = {asf_id: _person_name(people_data, asf_id) for asf_id in member_ids}
    pmc_ids = [chair] + sorted(owner_ids - {chair}, key=lambda item: _sort_key(item, names))
    committer_ids = sorted(member_ids - owner_ids, key=lambda item: _sort_key(item, names))
    return {
        "schema_version": SCHEMA_VERSION,
        "project": PROJECT,
        "retrieved_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": {
            **SOURCES,
            "chair": chair,
            "owners": sorted(owner_ids),
            "members": sorted(member_ids),
        },
        "roles": {
            "pmc": [_member(i, names[i], i == chair, mappings.get(i)) for i in pmc_ids],
            "committers": [_member(i, names[i], False, mappings.get(i)) for i in committer_ids],
        },
    }


def _install_avatars(candidate: dict, target: pathlib.Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for role in ("pmc", "committers"):
        for member in candidate["roles"][role]:
            github = member.get("github")
            if not github:
                continue
            raw = _avatar_bytes(github["user_id"])
            digest = hashlib.sha256(raw).hexdigest()
            path = target / f"{digest}.webp"
            if not path.exists():
                path.write_bytes(raw)
            member["avatar"] = f"/img/community/avatars/{path.name}"
            member["profile_url"] = f"https://github.com/{github['login']}"


def validate_bundle(warn_after_days: int) -> list[str]:
    roster, mapping = _read_json(ROSTER_PATH), _read_json(MAP_PATH)
    if roster.get("schema_version") != SCHEMA_VERSION or roster.get("project") != PROJECT:
        raise RosterError("roster.json: unsupported schema_version or project")
    roles, source = roster.get("roles"), roster.get("source")
    if not isinstance(roles, dict) or set(roles) != {"pmc", "committers"}:
        raise RosterError("roster.json: roles must contain only pmc and committers")
    if not isinstance(source, dict):
        raise RosterError("roster.json: source must be an object")
    for key, url in SOURCES.items():
        if source.get(key) != url:
            raise RosterError(f"roster.json: source.{key} is not authoritative")
    owners, members, chair = source.get("owners"), source.get("members"), source.get("chair")
    if not isinstance(owners, list) or not isinstance(members, list):
        raise RosterError("roster.json: source owners/members must be arrays")
    if owners != sorted(set(owners)) or members != sorted(set(members)):
        raise RosterError("roster.json: source owners/members must be sorted and unique")
    if any(not isinstance(asf_id, str) or not ASF_ID_PATTERN.fullmatch(asf_id) for asf_id in members):
        raise RosterError("roster.json: source members contain an invalid ASF ID")
    if not set(owners) <= set(members) or chair not in owners:
        raise RosterError("roster.json: invalid owners/members/Chair relationship")
    pmc, committers = roles["pmc"], roles["committers"]
    if not isinstance(pmc, list) or not isinstance(committers, list) or not pmc:
        raise RosterError("roster.json: invalid role arrays")
    people = pmc + committers
    ids = [person.get("asf_id") for person in people if isinstance(person, dict)]
    if len(ids) != len(people) or len(ids) != len(set(ids)) or set(ids) != set(members):
        raise RosterError("roster.json: members must match unique source ASF IDs")
    if {p["asf_id"] for p in pmc} != set(owners):
        raise RosterError("roster.json: PMC must equal owners")
    if {p["asf_id"] for p in committers} != set(members) - set(owners):
        raise RosterError("roster.json: Committers must equal members minus owners")
    chairs = [person for person in people if person.get("chair") is True]
    if len(chairs) != 1 or chairs[0].get("asf_id") != chair or pmc[0] != chairs[0]:
        raise RosterError("roster.json: unique Chair must be first in PMC")
    for role, entries in roles.items():
        tail = entries[1:] if role == "pmc" else entries
        actual_order = [(p.get("name", "").casefold(), p.get("asf_id", "").casefold()) for p in tail]
        if actual_order != sorted(actual_order):
            raise RosterError(f"roster.json: {role} must be sorted by public name and ASF ID casefold")
        for person in entries:
            if any(key not in person for key in ("asf_id", "name", "initials", "chair", "profile_url")):
                raise RosterError(f"roster.json: incomplete member {person!r}")
            if type(person["chair"]) is not bool:
                raise RosterError(f"roster.json: chair must be boolean for {person['asf_id']!r}")
    mappings = _validate_mapping(mapping, set(ids))
    for person in people:
        expected, avatar = mappings.get(person["asf_id"]), person.get("avatar")
        if expected != person.get("github"):
            raise RosterError(f"roster.json: GitHub mapping drift for {person['asf_id']!r}")
        if expected:
            match = AVATAR_PATH_PATTERN.fullmatch(avatar) if isinstance(avatar, str) else None
            if not match:
                raise RosterError(f"roster.json: mapped member {person['asf_id']!r} needs a local avatar")
            filename = f"{match.group(1)}.webp"
            path = AVATAR_DIR / filename
            if path.is_symlink():
                raise RosterError(f"roster.json: avatar must not be a symlink {avatar}")
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != match.group(1):
                raise RosterError(f"roster.json: invalid avatar {avatar}")
            _validate_webp(raw, expected_dimensions=(128, 128))
            if person["profile_url"] != f"https://github.com/{expected['login']}":
                raise RosterError(f"roster.json: mapped profile URL mismatch")
        elif avatar:
            raise RosterError(f"roster.json: unmapped member has an avatar")
        elif person["profile_url"] != f"https://people.apache.org/phonebook.html?uid={person['asf_id']}":
            raise RosterError(f"roster.json: unmapped profile URL mismatch for {person['asf_id']!r}")
    try:
        retrieved = dt.datetime.fromisoformat(roster["retrieved_at"].replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError) as exc:
        raise RosterError("roster.json: retrieved_at must be ISO-8601 UTC") from exc
    now = dt.datetime.now(dt.timezone.utc)
    if retrieved.tzinfo is None or retrieved > now + dt.timedelta(minutes=5):
        raise RosterError("roster.json: retrieved_at is in the future or lacks a timezone")
    age = now - retrieved
    return [f"community roster is {age.days} days old (threshold: {warn_after_days})"] if age > dt.timedelta(days=warn_after_days) else []


def validate_rendered_outputs(destination: pathlib.Path) -> None:
    expected = {
        "community/index.html": ('data-community-role="pmc"', 'data-community-role="committers"'),
        "_print/community/index.html": ('data-community-role="pmc"', 'data-community-role="committers"'),
        "community/index.md": ("## Project members", "### PMC", "### Committers"),
        "cn/community/index.html": ('data-community-role="pmc"', 'data-community-role="committers"'),
        "cn/_print/community/index.html": ('data-community-role="pmc"', 'data-community-role="committers"'),
        "cn/community/index.md": ("## 项目成员", "### PMC", "### Committers"),
    }
    urls = [p["profile_url"] for role in ("pmc", "committers") for p in _read_json(ROSTER_PATH)["roles"][role]]
    for relative, markers in expected.items():
        path = destination / relative
        if not path.is_file():
            raise RosterError(f"rendered output is missing {relative}")
        rendered = path.read_text(encoding="utf-8")
        if any(marker not in rendered for marker in markers):
            raise RosterError(f"rendered output {relative} is missing Community markers")
        positions = [rendered.find(url.replace("&", "&amp;") if relative.endswith(".html") else url) for url in urls]
        if any(position < 0 for position in positions) or positions != sorted(positions):
            raise RosterError(f"rendered output {relative} has role/link parity drift")


def _atomic_write(path: pathlib.Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = pathlib.Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def _unlink(path: pathlib.Path) -> None:
    path.unlink()


def _copy_candidate(raw: bytes, destination: pathlib.Path) -> None:
    with destination.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def _validate_avatar_blob(name: str, raw: bytes) -> None:
    match = re.fullmatch(r"([0-9a-f]{64})\.webp", name)
    if not match or hashlib.sha256(raw).hexdigest() != match.group(1):
        raise RosterError(f"candidate avatar name/hash mismatch: {name}")
    _validate_webp(raw, expected_dimensions=(128, 128))


def _commit_bundle(candidate: dict, candidate_avatars: dict[str, bytes]) -> None:
    """Install one bundle or restore the exact prior roster/avatar state."""
    old_roster = ROSTER_PATH.read_bytes() if ROSTER_PATH.exists() else None
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    referenced = {
        pathlib.PurePosixPath(person["avatar"]).name
        for role in candidate["roles"].values()
        for person in role
        if person.get("avatar")
    }
    existing = {path.name: path for path in AVATAR_DIR.glob("*.webp")}
    installed: list[pathlib.Path] = []
    replaced: dict[pathlib.Path, bytes] = {}
    try:
        for name, avatar in sorted(candidate_avatars.items()):
            _validate_avatar_blob(name, avatar)
            destination = AVATAR_DIR / name
            if destination.exists():
                previous = destination.read_bytes()
                try:
                    _validate_avatar_blob(name, previous)
                    continue
                except RosterError:
                    replaced[destination] = previous
            staged = AVATAR_DIR / f".{name}.candidate"
            try:
                _copy_candidate(avatar, staged)
                os.replace(staged, destination)
            finally:
                if staged.exists():
                    _unlink(staged)
            if destination not in replaced:
                installed.append(destination)
        raw = (json.dumps(candidate, indent=2, ensure_ascii=False) + "\n").encode()
        _atomic_write(ROSTER_PATH, raw)
    except Exception:
        if old_roster is not None:
            _atomic_write(ROSTER_PATH, old_roster)
        for path, raw in replaced.items():
            _atomic_write(path, raw)
        for path in installed:
            try:
                _unlink(path)
            except OSError:
                pass
        raise
    for name in sorted(set(existing) - referenced):
        try:
            _unlink(AVATAR_DIR / name)
        except OSError as exc:
            print(
                f"::warning file=static/img/community/avatars/{name}::"
                f"could not remove unreferenced avatar: {exc}",
                file=sys.stderr,
            )


def refresh() -> None:
    source_data = {key: _fetch_json(url) for key, url in SOURCES.items()}
    candidate = build_roster(source_data["committee"], source_data["projects"], source_data["people"], _read_json(MAP_PATH))
    work = pathlib.Path(tempfile.mkdtemp(prefix=".community-refresh-", dir=DATA_DIR))
    try:
        candidate_avatars = work / "avatars"
        _install_avatars(candidate, candidate_avatars)
        avatar_bytes = {path.name: path.read_bytes() for path in candidate_avatars.glob("*.webp")}
    finally:
        # Candidate cleanup is deliberately completed before the checked-in
        # bundle changes, so cleanup failure cannot publish a new roster.
        shutil.rmtree(work)
    _commit_bundle(candidate, avatar_bytes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("refresh")
    validate = commands.add_parser("validate")
    validate.add_argument("--warn-after-days", type=int, default=90)
    validate.add_argument("--artifact", type=pathlib.Path, help="validate a prebuilt Hugo artifact")
    args = parser.parse_args()
    try:
        if args.command == "refresh":
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            refresh()
        else:
            if args.warn_after_days < 0:
                raise RosterError("--warn-after-days must be non-negative")
            for warning in validate_bundle(args.warn_after_days):
                print(f"::warning file=data/community/roster.json::{warning}")
            if args.artifact:
                validate_rendered_outputs(args.artifact.resolve())
    except (OSError, RosterError, urllib.error.URLError) as exc:
        print(f"community roster: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
