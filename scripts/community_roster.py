#!/usr/bin/env python3
"""Refresh and validate the offline Apache HugeGraph community roster."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.error
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


class RosterError(ValueError):
    pass


def _read_json(path: pathlib.Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RosterError(f"{path.relative_to(ROOT)}: invalid JSON: {exc}") from exc


def _fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "apache-hugegraph-doc-community-roster/1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RosterError(f"{url}: HTTP {response.status}")
        return json.load(response)


def _person_name(people: dict, asf_id: str) -> str:
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
        if roster_ids is not None and asf_id not in roster_ids:
            raise RosterError(f"github-map.json: unknown ASF ID {asf_id!r}")
        if not isinstance(mapping, dict):
            raise RosterError(f"github-map.json: mapping for {asf_id!r} must be an object")
        login, user_id = mapping.get("login"), mapping.get("user_id")
        if not isinstance(login, str) or not login.strip() or login != login.strip():
            raise RosterError(f"github-map.json: {asf_id!r} needs a reviewed login")
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
                chunk[8] &= ~0x2C
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
        raw = response.read()
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
            result = subprocess.run(
                [converter, "-quiet", "-resize", "128", "128", "-metadata", "none", str(source), "-o", str(target)],
                text=True,
                capture_output=True,
            )
            if result.returncode:
                raise RosterError(f"cwebp failed for numeric GitHub user ID {user_id}: {result.stderr.strip()}")
            raw = _strip_webp_metadata(target.read_bytes())
    if _webp_dimensions(raw) != (128, 128):
        raise RosterError(f"GitHub avatar for numeric user ID {user_id} is not 128x128 WebP")
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
    mappings = _validate_mapping(mapping, set(ids))
    for person in people:
        expected, avatar = mappings.get(person["asf_id"]), person.get("avatar")
        if expected != person.get("github"):
            raise RosterError(f"roster.json: GitHub mapping drift for {person['asf_id']!r}")
        if expected:
            if not isinstance(avatar, str) or not avatar.startswith("/img/community/avatars/"):
                raise RosterError(f"roster.json: mapped member {person['asf_id']!r} needs a local avatar")
            filename = pathlib.PurePosixPath(avatar).name
            if len(filename) != 69 or not filename.endswith(".webp"):
                raise RosterError(f"roster.json: avatar filename must be a SHA-256 digest")
            raw = (ROOT / "static" / avatar.lstrip("/")).read_bytes()
            if hashlib.sha256(raw).hexdigest() != filename[:-5] or _webp_dimensions(raw) != (128, 128):
                raise RosterError(f"roster.json: invalid avatar {avatar}")
            if any(marker in raw for marker in (b"EXIF", b"XMP ", b"ICCP")):
                raise RosterError(f"roster.json: avatar contains metadata {avatar}")
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


def validate_rendered_outputs() -> None:
    with tempfile.TemporaryDirectory(prefix="hugegraph-community-site-") as destination:
        environment = {**os.environ, "GOPROXY": "off"}
        result = subprocess.run(
            ["hugo", "--quiet", "--destination", destination],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
        )
        if result.returncode:
            raise RosterError(f"Hugo render failed:\n{result.stderr.strip()}")
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
            path = pathlib.Path(destination) / relative
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
    orphan_bytes = {name: path.read_bytes() for name, path in existing.items() if name not in referenced}
    installed: list[pathlib.Path] = []
    roster_replaced = False
    try:
        for name, avatar in sorted(candidate_avatars.items()):
            destination = AVATAR_DIR / name
            if destination.exists():
                continue
            staged = AVATAR_DIR / f".{name}.candidate"
            try:
                _copy_candidate(avatar, staged)
                os.replace(staged, destination)
            finally:
                if staged.exists():
                    _unlink(staged)
            installed.append(destination)
        raw = (json.dumps(candidate, indent=2, ensure_ascii=False) + "\n").encode()
        _atomic_write(ROSTER_PATH, raw)
        roster_replaced = True
        for name in sorted(orphan_bytes):
            _unlink(AVATAR_DIR / name)
    except Exception:
        if roster_replaced:
            if old_roster is None:
                try:
                    _unlink(ROSTER_PATH)
                except OSError:
                    pass
            else:
                _atomic_write(ROSTER_PATH, old_roster)
        for name, raw in orphan_bytes.items():
            _atomic_write(AVATAR_DIR / name, raw)
        for path in installed:
            try:
                _unlink(path)
            except OSError:
                pass
        raise


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
    validate.add_argument("--skip-render", action="store_true")
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
            if not args.skip_render:
                validate_rendered_outputs()
    except (OSError, RosterError, urllib.error.URLError) as exc:
        print(f"community roster: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
