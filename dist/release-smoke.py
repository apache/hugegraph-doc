#!/usr/bin/env python3
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with this
# work for additional information regarding copyright ownership. The ASF
# licenses this file to You under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Release archive checks and assertions against disposable local services."""

import base64
import gzip
import hashlib
import http.cookiejar
import json
from pathlib import Path, PurePosixPath
import re
import socket
import sys
import tarfile
import time
import urllib.error
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

AUTH = "Basic " + base64.b64encode(b"admin:release-smoke").decode()
SERVER = "http://127.0.0.1:8080"
HUBBLE = "http://127.0.0.1:8088"
OPENER = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def request(url, body=None, hubble=False):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if not hubble:
        headers["Authorization"] = AUTH
    data = json.dumps(body).encode() if body is not None else None
    with OPENER.open(urllib.request.Request(url, data, headers), timeout=10) as response:
        payload = response.read()
        if response.headers.get("Content-Encoding", "").lower() == "gzip":
            payload = gzip.decompress(payload)
        result = json.loads(payload)
    if hubble:
        require(result.get("status") == 200, f"Hubble business failure: {result}")
        return result["data"]
    return result


def wait_for(check, timeout=120):
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            return check()
        except (OSError, ValueError, RuntimeError, KeyError) as error:
            last_error = error
            time.sleep(2)
    raise RuntimeError(f"Service check timed out: {last_error}")


def gremlin(script):
    response = request(SERVER + "/gremlin", {
        "gremlin": script, "bindings": {}, "language": "gremlin-groovy",
        "aliases": {"g": "__g_DEFAULT-hugegraph"},
    })
    require(response["status"]["code"] == 200, response)
    return response["result"]["data"]


def server():
    def ready():
        response = request(SERVER + "/graphspaces/DEFAULT/graphs")
        require("hugegraph" in response["graphs"], response)
        require(gremlin("g.V().count()") == [0], "Expected a fresh disposable graph")
    wait_for(ready)
    print("PASS: authenticated Server graph API and Gremlin")


def loader():
    require(gremlin("g.V().hasLabel('person').count()") == [6], "Validation failed")
    require(gremlin("g.V().hasLabel('software').count()") == [2], "Validation failed")
    require(gremlin("g.E().hasLabel('knows').count()") == [2], "Validation failed")
    require(gremlin("g.E().hasLabel('created').count()") == [4], "Validation failed")
    print("PASS: Loader imported six people, two software vertices and six edges")


def hubble():
    def about():
        response = request(HUBBLE + "/about", hubble=True)
        require(response["name"] == "hugegraph-hubble", response)
    wait_for(about)
    request(HUBBLE + "/api/v1.3/auth/login", {"user_name": "admin", "user_password": "release-smoke"}, hubble=True)
    spaces = request(HUBBLE + "/api/v1.3/graphspaces/list", hubble=True)
    require("DEFAULT" in spaces["graphspaces"], spaces)
    schema = request(HUBBLE + "/api/v1.3/graphspaces/DEFAULT/graphs/hugegraph/schema/groovy", hubble=True)
    require("person" in schema["schema"] and "knows" in schema["schema"], schema)
    print("PASS: Hubble login, graphspace and schema export through Server")


def stopped(port):
    def check():
        with socket.socket() as connection:
            connection.settimeout(1)
            require(connection.connect_ex(("127.0.0.1", port)) != 0, f"Port {port} is still open")
    wait_for(check, 30)


def ports():
    for port in (8080, 8088):
        with socket.socket() as connection:
            connection.bind(("127.0.0.1", port))


def checksum(filename):
    archive = Path(filename)
    digest = hashlib.sha512()
    with archive.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    text = Path(filename + ".sha512").read_text().strip()
    # ASF releases use either a bare digest, shasum or BSD checksum format.
    matches = re.findall(r"(?<![a-fA-F0-9])[a-fA-F0-9]{128}(?![a-fA-F0-9])", text)
    require(len(matches) == 1 and matches[0].lower() == digest.hexdigest(), f"Invalid SHA512: {archive.name}")
    remainder = text.replace(matches[0], "").strip()
    require(not remainder or archive.name in remainder, f"Checksum names a different archive: {text}")
    print(f"PASS: SHA512 {archive.name}")


def binary_licenses(directory, report):
    # Maven declarations identify bundled components; aggregate NOTICE keyword
    # mentions do not identify the license of an actual packaged dependency.
    prohibited = re.compile(r"\b(?:AGPL|LGPL|GPL)(?:[- ]?v?[0-9]+(?:\.[0-9]+)?)?\b|\b(?:BCL|RSAL|QPL|SSPL|CPOL|NPL1)\b|GNU .*General Public License|"
                            r"Sleepycat|BSD-4-Clause|Binary Code License|JSR-275|Amazon Software License|"
                            r"Creative Commons Non-Commercial|JSON\.org", re.I)
    exceptions = re.compile(r"classpath|exception|\bCPE\b", re.I)
    conditional = re.compile(r"\b(?:CDDL|CPL|EPL|IPL|MPL|SPL|OFL)(?:[- ]?v?[0-9]+(?:\.[0-9]+)?)?\b|"
                             r"Mozilla Public|Eclipse Public|Common Development|CC-BY", re.I)
    permissive = re.compile(r"Apache|\bMIT\b|\bBSD\b|\bISC\b|Zlib|Boost|W3C|Public Domain|CC0", re.I)
    review, errors = [], []
    for library in Path(directory).rglob("lib/*.jar"):
        with zipfile.ZipFile(library) as archive:
            poms = [item for item in archive.infolist()
                    if item.filename.startswith("META-INF/maven/") and item.filename.endswith("/pom.xml")]
            if not poms:
                review.append(f"{library}: no embedded Maven POM; inspect the component license")
            for entry in poms:
                context = f"{library}!{entry.filename}"
                try:
                    root = ET.fromstring(archive.read(entry))
                    labels = [" ".join(item.itertext()).strip() for item in root.findall("{*}licenses/{*}license")]
                except ET.ParseError:
                    labels = []
                if not labels:
                    review.append(f"{context}: missing/invalid license declaration; inspect inherited/actual license")
                else:
                    # 'GPL or later' remains Category X. Only explicit non-X
                    # license evidence or an exception requires choice review.
                    only_x = [bool(prohibited.search(label)) and not exceptions.search(label) and
                              not (conditional.search(prohibited.sub("", label)) or
                                   permissive.search(prohibited.sub("", label))) for label in labels]
                    if all(only_x):
                        errors.append(f"{context}: Category-X-only declaration: {' | '.join(labels)}")
                    elif len(labels) > 1 or any(prohibited.search(label) or exceptions.search(label) or
                                               conditional.search(label) or not permissive.search(label) for label in labels):
                        review.append(f"{context}: review license selection/conditions: {' | '.join(labels)}")
    Path(report).write_text("MANUAL LICENSING REVIEW (automatic checks are not release approval)\n" +
                            "\n".join(review + errors) + "\n")
    print(f"Manual license review: {len(review)} declarations; report: {report}")
    require(not errors, "\n".join(errors))


def properties(filename, *assignments):
    # These runtime overrides are single-line scalar properties. Remove only
    # their active definitions; preserve comments and every other setting.
    updates = dict(item.split("=", 1) for item in assignments)
    pattern = re.compile(r"^\s*(?:" + "|".join(re.escape(key) for key in updates) + r")\s*[=:]")
    path = Path(filename)
    content = "".join(line for line in path.read_text().splitlines(keepends=True) if not pattern.match(line))
    if content and not content.endswith("\n"):
        content += "\n"
    path.write_text(content + "".join(f"{key}={value}\n" for key, value in updates.items()))


def embedded_versions(version, server_directory, toolchain_directory):
    directories = [(Path(server_directory), {"hugegraph-core", "hugegraph-api", "hugegraph-dist"})]
    for module, required in (("loader", {"hugegraph-client", "hugegraph-loader"}),
                             ("tools", {"hugegraph-client", "hugegraph-tools"}),
                             ("hubble", {"hugegraph-client", "hubble-be"})):
        directories.append((Path(toolchain_directory) / f"apache-hugegraph-{module}-{version}", required))
    for directory, required in directories:
        seen = set()
        identities = set()
        for library in (directory / "lib").glob("*.jar"):
            known_name = library.name.startswith(("hugegraph-", "hg-", "hubble-"))
            coordinates = []
            with zipfile.ZipFile(library) as archive:
                for entry in archive.infolist():
                    if not entry.filename.endswith("/pom.properties"):
                        continue
                    properties = dict(line.split("=", 1) for line in archive.read(entry).decode().splitlines()
                                      if "=" in line and not line.startswith("#"))
                    if properties.get("groupId") == "org.apache.hugegraph":
                        coordinates.append(properties)
            if not coordinates:
                require(not known_name, f"Missing HugeGraph Maven metadata: {library}")
                continue
            shaded_loader = library.name == f"apache-hugegraph-loader-{version}-shaded.jar"
            require(library.name.endswith(f"-{version}.jar") or shaded_loader,
                    f"Mixed embedded version: {library}")
            require(all(item.get("version") == version for item in coordinates),
                    f"Wrong embedded Maven coordinates: {library}")
            # Shaded JARs may carry several dependency coordinates. Only the
            # main artifact must match its filename; every HugeGraph coordinate
            # must still have the expected version, including renamed extras.
            main = [item for item in coordinates
                    if library.name == f"{item.get('artifactId')}-{version}.jar" or
                    (shaded_loader and item.get("artifactId") == "hugegraph-loader")]
            require(len(main) == 1, f"Missing or duplicate Maven metadata for main artifact: {library}")
            artifact = main[0]["artifactId"]
            # Loader ships both its regular JAR and its explicitly named shaded JAR.
            identity = (artifact, "shaded" if shaded_loader else "main")
            require(identity not in identities and not library.is_symlink(),
                    f"Duplicate or linked self artifact: {library}")
            identities.add(identity)
            seen.add(artifact)
        require(required <= seen, f"Missing self artifacts in {directory}: {sorted(required - seen)}")
    print("PASS: Server and Toolchain self artifacts have matching filenames and embedded Maven versions")


def staging_origin(repository, version, distribution):
    repository = Path(repository)
    required = {"hugegraph-common", "hg-pd-common", "hg-pd-client", "hg-pd-grpc", "hugegraph-core"}
    for library in Path(distribution).rglob("lib/*.jar"):
        if library.name.startswith(("hugegraph-client-", "hugegraph-loader-", "hugegraph-tools-")):
            require(library.name.endswith(f"-{version}.jar"), f"Mixed Toolchain version: {library.name}")
            continue
        if library.name.startswith(("hugegraph-", "hg-")):
            require(library.name.endswith(f"-{version}.jar"), f"Mixed SDK version: {library.name}")
            required.add(library.name[:-len(f"-{version}.jar")])
    for artifact in sorted(required):
        directory = repository / "org/apache/hugegraph" / artifact / version
        metadata = (directory / "_remote.repositories").read_text().splitlines()
        for extension in ("pom", "jar"):
            name = f"{artifact}-{version}.{extension}"
            require((directory / name).is_file(), f"Missing staged artifact: {name}")
            require(f"{name}>selected-staging=" in metadata, f"Artifact was not fetched from selected staging: {name}")
    print(f"PASS: {len(required)} SDK coordinates resolved from selected staging")


def extract(filename, destination):
    archive = Path(filename)
    root = archive.name.removesuffix(".tar.gz")
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as stream:
        members = stream.getmembers()
        require(members, f"Empty archive: {archive.name}")
        for member in members:
            path = PurePosixPath(member.name)
            require(not path.is_absolute() and ".." not in path.parts, f"Unsafe archive path: {member.name}")
            require(not any(part.startswith("._") or part == "__MACOSX" for part in path.parts),
                    f"macOS metadata is not allowed in release archives: {member.name}")
            require(path.parts and path.parts[0] == root, f"Unexpected archive root: {member.name}")
            require(member.isfile() or member.isdir(), f"Unsupported archive member: {member.name}")
        # Paths and member types are validated above, including on Python 3.9/3.10 runners.
        stream.extractall(destination, members=members)
    require((destination / root).is_dir(), f"Missing archive root: {root}")


if __name__ == "__main__":
    commands = {
        "server": server, "loader": loader, "hubble": hubble, "ports": ports,
        "checksum": checksum, "extract": extract, "properties": properties,
        "binary-licenses": binary_licenses, "staging-origin": staging_origin,
        "embedded-versions": embedded_versions, "stopped": lambda port: stopped(int(port)),
    }
    commands[sys.argv[1]](*sys.argv[2:])
