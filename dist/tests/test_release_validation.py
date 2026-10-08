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

import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import tarfile
import tempfile
import unittest
import zipfile
from unittest.mock import patch

DIST = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release_smoke", DIST / "release-smoke.py")
SMOKE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SMOKE)


class ReleaseValidationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.archive = self.root / "apache-hugegraph-1.8.0-src.tar.gz"

    def tearDown(self):
        self.temp.cleanup()

    def archive_with(self, name, link=False):
        with tarfile.open(self.archive, "w:gz") as archive:
            member = tarfile.TarInfo(name)
            if link:
                member.type = tarfile.SYMTYPE
                member.linkname = "/tmp/outside"
                archive.addfile(member)
            else:
                member.size = 4
                archive.addfile(member, io.BytesIO(b"test"))

    def shell(self, code):
        return subprocess.run(["bash", "-c", f"source {shlex.quote(str(DIST / 'validate-release.sh'))}; {code}"],
                              env=dict(os.environ, COPYFILE_DISABLE="0"), capture_output=True, text=True)

    def test_binary_license_checks_actual_pom_and_retains_manual_review(self):
        library = self.root / "distribution/lib/component.jar"
        library.parent.mkdir(parents=True)
        report = self.root / "license-review.txt"
        def pom(licenses):
            return ('<project xmlns="http://maven.apache.org/POM/4.0.0"><licenses>' +
                    ''.join(f'<license><name>{name}</name></license>' for name in licenses) + '</licenses></project>')
        with zipfile.ZipFile(library, "w") as archive:
            archive.writestr("META-INF/maven/example/component/pom.xml", pom(["GPLv2"]))
        with self.assertRaisesRegex(RuntimeError, "Category-X-only declaration"):
            SMOKE.binary_licenses(self.root / "distribution", report)
        # A separate Apache POM in the same shaded JAR cannot hide a GPL-only component.
        with zipfile.ZipFile(library, "a") as archive:
            archive.writestr("META-INF/maven/example/another/pom.xml", pom(["Apache License 2.0"]))
        with self.assertRaisesRegex(RuntimeError, "Category-X-only declaration"):
            SMOKE.binary_licenses(self.root / "distribution", report)
        for declarations in (["GPL-2.0", "LGPL-2.1"], ["GPL version 2 or later"], ["BSD-4-Clause"]):
            with zipfile.ZipFile(library, "w") as archive:
                archive.writestr("META-INF/maven/example/component/pom.xml", pom(declarations))
            with self.assertRaisesRegex(RuntimeError, "Category-X-only declaration"):
                SMOKE.binary_licenses(self.root / "distribution", report)
        for declarations in (["Apache License 2.0", "LGPL-2.1"], ["GPL OR Apache License 2.0"],
                             ["GPL-2.0 WITH ClasspathException-2.0"], []):
            with zipfile.ZipFile(library, "w") as archive:
                archive.writestr("META-INF/maven/example/component/pom.xml", pom(declarations))
            SMOKE.binary_licenses(self.root / "distribution", report)
            self.assertIn("MANUAL LICENSING REVIEW", report.read_text())
            self.assertIn("component.jar!", report.read_text())

    def test_runtime_properties_replace_duplicate_active_keys_preserving_other_lines(self):
        config = self.root / "hugegraph-hubble.properties"
        config.write_text("# Keep the standalone documentation\n#pd.enabled=true\npd.enabled=false\n"
                          "pd.enabled = true\nserver.direct_url=http://127.0.0.1:8080\n"
                          "server.direct_url: http://old-server\nserver.port=8088\n")
        assignments = ("pd.enabled=false", "server.direct_url=http://127.0.0.1:8080")
        SMOKE.properties(str(config), *assignments)
        expected = ("# Keep the standalone documentation\n#pd.enabled=true\nserver.port=8088\n"
                    "pd.enabled=false\nserver.direct_url=http://127.0.0.1:8080\n")
        self.assertEqual(config.read_text(), expected)
        SMOKE.properties(str(config), *assignments)
        self.assertEqual(config.read_text(), expected)

    def test_server_response_with_real_gzip_payload_is_decoded(self):
        expected = {"status": {"code": 200}, "result": {"data": [0]}}
        response = io.BytesIO(gzip.compress(json.dumps(expected).encode()))
        response.headers = {"Content-Encoding": "gzip"}
        with patch.object(SMOKE.OPENER, "open", return_value=response):
            self.assertEqual(SMOKE.request("http://127.0.0.1:8080/gremlin", {"gremlin": "g.V().count()"}), expected)

    def test_extract_expected_root(self):
        self.archive_with("./apache-hugegraph-1.8.0-src/LICENSE")
        SMOKE.extract(str(self.archive), str(self.root / "extracted"))
        self.assertEqual((self.root / "extracted/apache-hugegraph-1.8.0-src/LICENSE").read_text(), "test")

    def test_reject_unsafe_or_wrong_root(self):
        for name in ("../outside", "/outside", "wrong-root/LICENSE", "apache-hugegraph-1.8.0-src/../outside"):
            with self.subTest(name=name):
                self.archive_with(name)
                with self.assertRaises(RuntimeError):
                    SMOKE.extract(str(self.archive), str(self.root / "extracted"))
        self.archive_with("apache-hugegraph-1.8.0-src/link", link=True)
        with self.assertRaises(RuntimeError):
            SMOKE.extract(str(self.archive), str(self.root / "extracted"))

    def test_binary_archive_rejects_nested_macos_metadata(self):
        self.archive = self.root / "apache-hugegraph-1.8.0.tar.gz"
        for name in ("apache-hugegraph-1.8.0/lib/._hugegraph-core.jar",
                     "apache-hugegraph-1.8.0/__MACOSX/lib/metadata"):
            with self.subTest(name=name):
                self.archive_with(name)
                with self.assertRaisesRegex(RuntimeError, "macOS metadata is not allowed"):
                    SMOKE.extract(str(self.archive), str(self.root / "extracted"))

    def test_checksum_formats_and_mismatch(self):
        self.archive.write_bytes(b"release")
        digest = hashlib.sha512(b"release").hexdigest()
        checksum = Path(str(self.archive) + ".sha512")
        for text in (digest, f"{digest}  {self.archive.name}", f"SHA512 ({self.archive.name}) = {digest}"):
            checksum.write_text(text)
            SMOKE.checksum(str(self.archive))
        checksum.write_text("0" * 128)
        with self.assertRaises(RuntimeError):
            SMOKE.checksum(str(self.archive))
        checksum.write_text(f"{digest}  another.tar.gz")
        with self.assertRaises(RuntimeError):
            SMOKE.checksum(str(self.archive))

    def write_jar(self, path, artifact, version="1.8.0", duplicate=False):
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w") as archive:
            name = f"META-INF/maven/org.apache.hugegraph/{artifact}/pom.properties"
            data = f"artifactId={artifact}\ngroupId=org.apache.hugegraph\nversion={version}\n"
            archive.writestr(name, data)
            if duplicate:
                archive.writestr(name, data)

    def version_fixture(self):
        server = self.root / "server"
        toolchain = self.root / "toolchain"
        for artifact in ("hugegraph-core", "hugegraph-api", "hugegraph-dist"):
            self.write_jar(server / "lib" / f"{artifact}-1.8.0.jar", artifact)
        for module, artifact in (("loader", "hugegraph-loader"), ("tools", "hugegraph-tools"), ("hubble", "hubble-be")):
            library = toolchain / f"apache-hugegraph-{module}-1.8.0/lib"
            self.write_jar(library / f"{artifact}-1.8.0.jar", artifact)
            self.write_jar(library / "hugegraph-client-1.8.0.jar", "hugegraph-client")
        return server, toolchain

    def test_embedded_versions_reject_renamed_missing_and_duplicate_artifacts(self):
        server, toolchain = self.version_fixture()
        SMOKE.embedded_versions("1.8.0", server, toolchain)
        client = toolchain / "apache-hugegraph-loader-1.8.0/lib/hugegraph-client-1.8.0.jar"
        self.write_jar(client, "hugegraph-client", "1.7.0")
        with self.assertRaisesRegex(RuntimeError, "Wrong embedded Maven coordinates"):
            SMOKE.embedded_versions("1.8.0", server, toolchain)
        self.write_jar(client, "hugegraph-client", duplicate=True)
        with self.assertRaisesRegex(RuntimeError, "duplicate Maven metadata"):
            SMOKE.embedded_versions("1.8.0", server, toolchain)
        client.unlink()
        with self.assertRaisesRegex(RuntimeError, "Missing self artifacts"):
            SMOKE.embedded_versions("1.8.0", server, toolchain)
        self.write_jar(client.with_name("hugegraph-client-1.7.0.jar"), "hugegraph-client", "1.7.0")
        with self.assertRaisesRegex(RuntimeError, "Mixed embedded version"):
            SMOKE.embedded_versions("1.8.0", server, toolchain)

    def test_extra_renamed_old_jar_rejected_with_correct_self_jars_present(self):
        server, toolchain = self.version_fixture()
        extra = toolchain / "apache-hugegraph-loader-1.8.0/lib/legacy.jar"
        self.write_jar(extra, "hugegraph-client", "1.7.0")
        with self.assertRaisesRegex(RuntimeError, "Mixed embedded version"):
            SMOKE.embedded_versions("1.8.0", server, toolchain)

    def test_shaded_same_version_coordinates_are_allowed(self):
        server, toolchain = self.version_fixture()
        library = server / "lib/hugegraph-core-1.8.0.jar"
        with zipfile.ZipFile(library, "a") as archive:
            archive.writestr("META-INF/maven/org.apache.hugegraph/hugegraph-common/pom.properties",
                             "groupId=org.apache.hugegraph\nartifactId=hugegraph-common\nversion=1.8.0\n")
        SMOKE.embedded_versions("1.8.0", server, toolchain)

    def test_native_loader_shaded_name_and_dependencies_are_allowed(self):
        server, toolchain = self.version_fixture()
        library = toolchain / "apache-hugegraph-loader-1.8.0/lib/apache-hugegraph-loader-1.8.0-shaded.jar"
        self.write_jar(library, "hugegraph-loader")
        with zipfile.ZipFile(library, "a") as archive:
            archive.writestr("META-INF/maven/org.apache.hugegraph/hugegraph-client/pom.properties",
                             "groupId=org.apache.hugegraph\nartifactId=hugegraph-client\nversion=1.8.0\n")
        SMOKE.embedded_versions("1.8.0", server, toolchain)

    def test_validator_exports_copyfile_disable_to_child_processes(self):
        result = self.shell("python3 -c 'import os; print(os.environ[\"COPYFILE_DISABLE\"])'")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "1")

    def test_selected_signer_rejects_another_valid_signature(self):
        keyring = self.root / "gnupg"
        keyring.mkdir(mode=0o700)
        for identity in ("Release Test Alice <alice@example.invalid>", "Release Test Bob <bob@example.invalid>"):
            subprocess.run(["gpg", "--homedir", str(keyring), "--batch", "--pinentry-mode", "loopback",
                            "--passphrase", "", "--quick-generate-key", identity, "ed25519", "sign", "0"],
                           check=True, capture_output=True)
        self.archive.write_bytes(b"release")
        Path(str(self.archive) + ".sha512").write_text(hashlib.sha512(b"release").hexdigest())
        subprocess.run(["gpg", "--homedir", str(keyring), "--batch", "--local-user", "bob@example.invalid",
                        "--armor", "--detach-sign", str(self.archive)], check=True, capture_output=True)
        code = (f"RUN_DIR={shlex.quote(str(self.root))}; GPG_USER=alice@example.invalid; "
                f"select_signer; PACKAGES=({shlex.quote(str(self.archive))}); verify_integrity")
        result = self.shell(code)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        # A selector resembling a GPG option must not export the entire project keyring.
        result = self.shell(code.replace("alice@example.invalid", "--armor")
                            .replace("select_signer;", f"rm -rf {shlex.quote(str(self.root / 'signer'))}; select_signer;"))
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Selected release signer not found: --armor", result.stdout)
        # Use Bob's actual disposable public key; Alice's valid but unrelated key cannot authorize it.
        bob_code = code.replace("alice@example.invalid", "bob@example.invalid").replace(
            "select_signer;", f"rm -rf {shlex.quote(str(self.root / 'signer'))}; select_signer;")
        result = self.shell(bob_code)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        listing = subprocess.run(["gpg", "--homedir", str(keyring), "--batch", "--with-colons",
                                  "--fingerprint", "--", "bob@example.invalid"], check=True, capture_output=True, text=True)
        fingerprint = next(line.split(":")[9] for line in listing.stdout.splitlines() if line.startswith("fpr:"))
        certificate = (keyring / "openpgp-revocs.d" / f"{fingerprint}.rev").read_text()
        certificate = certificate.replace(":-----BEGIN PGP PUBLIC KEY BLOCK-----", "-----BEGIN PGP PUBLIC KEY BLOCK-----")
        subprocess.run(["gpg", "--homedir", str(keyring), "--batch", "--import"], input=certificate,
                       text=True, check=True, capture_output=True)
        result = self.shell(bob_code.replace("GPG_USER=bob@example.invalid", f"GPG_USER={fingerprint}"))
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Expired or revoked release signature", result.stdout)
        status = self.root / "logs/signatures" / f"{self.archive.name}.status"
        self.assertIn("[GNUPG:] REVKEYSIG ", status.read_text())
        subprocess.run(["gpgconf", "--homedir", str(keyring), "--kill", "gpg-agent"], capture_output=True)

    def test_machine_signature_status_rejects_expiry_even_with_validsig(self):
        status = self.root / "signature.status"
        for token in ("EXPKEYSIG", "EXPSIG"):
            status.write_text(f"[GNUPG:] {token} KEY User\n[GNUPG:] VALIDSIG FINGERPRINT details\n")
            result = self.shell(f"check_signature_status {shlex.quote(str(status))}")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Expired or revoked release signature", result.stdout)
        status.write_text("[GNUPG:] GOODSIG KEY User\n")
        result = self.shell(f"check_signature_status {shlex.quote(str(status))}")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing VALIDSIG", result.stdout)

    def test_posix_license_boundaries_reject_gpl_and_lgpl_in_notice(self):
        (self.root / "LICENSE").write_text("Apache License, Version 2.0")
        for license in ("GPL", "LGPL"):
            (self.root / "NOTICE").write_text(f"Bundled component: {license} 2.1\n")
            result = self.shell(f"cd {shlex.quote(str(self.root))}; check_license_categories fixture LICENSE NOTICE")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("prohibited ASF Category X", result.stdout)

    def test_server_launcher_supplies_stdin_and_disables_monitor(self):
        service = self.root / "server"
        (service / "bin").mkdir(parents=True)
        commands = {
            "init-store.sh": f"read password\nprintf '%s' \"$password\" > {shlex.quote(str(self.root / 'init-stdin'))}\n",
            "start-hugegraph.sh": f"printf '%s' \"$*\" > {shlex.quote(str(self.root / 'start-args'))}\n",
            "stop-hugegraph.sh": f"printf '%s' \"$*\" > {shlex.quote(str(self.root / 'stop-args'))}\n",
        }
        for name, body in commands.items():
            command = service / "bin" / name
            command.write_text("#!/bin/sh\n" + body)
            command.chmod(0o755)
        (self.root / "release-smoke.py").write_text("# Test helper: disposable fixture port is closed\n")
        result = self.shell(f"RUN_DIR={shlex.quote(str(self.root))}; SCRIPT_DIR={shlex.quote(str(self.root))}; "
                            f"start_server {shlex.quote(str(service))}; stop_services")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.root / "init-stdin").read_text(), "release-smoke")
        self.assertEqual((self.root / "start-args").read_text(), "-m false")
        self.assertEqual((self.root / "stop-args").read_text(), "-m false")

    def test_failed_store_init_does_not_claim_a_started_server(self):
        service = self.root / "server"
        (service / "bin").mkdir(parents=True)
        init = service / "bin/init-store.sh"
        init.write_text("#!/bin/sh\nexit 11\n")
        init.chmod(0o755)
        stop = service / "bin/stop-hugegraph.sh"
        marker = self.root / "unexpected-stop"
        stop.write_text(f"#!/bin/sh\ntouch {shlex.quote(str(marker))}\n")
        stop.chmod(0o755)
        result = self.shell(f"RUN_DIR={shlex.quote(str(self.root))}; start_server {shlex.quote(str(service))}")
        self.assertEqual(result.returncode, 11)
        self.assertFalse(marker.exists())

    def test_failed_start_and_incomplete_stop_keep_cleanup_ownership(self):
        service = self.root / "service"
        (service / "bin").mkdir(parents=True)
        marker = self.root / "stop-count"
        stop = service / "bin/stop-hubble.sh"
        stop.write_text(f"#!/bin/sh\necho stopped >> {shlex.quote(str(marker))}\n")
        stop.chmod(0o755)
        start = service / "bin/start-hubble.sh"
        start.write_text("#!/bin/sh\nexit 19\n")
        start.chmod(0o755)
        check_marker = self.root / "port-checks"
        (self.root / "release-smoke.py").write_text(
            f"from pathlib import Path\nPath({str(check_marker)!r}).write_text('checked')\n")
        code = (f"RUN_DIR={shlex.quote(str(self.root))}; HUBBLE_DIR={shlex.quote(str(service))}; "
                f"SCRIPT_DIR={shlex.quote(str(self.root))}; (cd \"$HUBBLE_DIR\" && bin/start-hubble.sh)")
        result = self.shell(code)
        self.assertEqual(result.returncode, 19)
        self.assertEqual(marker.read_text().splitlines(), ["stopped"])
        self.assertEqual(check_marker.read_text(), "checked")
        # Simulate the business-level stopped check finding the port still open.
        (self.root / "release-smoke.py").write_text("import sys\nsys.exit(17)\n")
        result = self.shell(f"RUN_DIR={shlex.quote(str(self.root))}; HUBBLE_DIR={shlex.quote(str(service))}; "
                            f"SCRIPT_DIR={shlex.quote(str(self.root))}; stop_services")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(marker.read_text().splitlines(), ["stopped", "stopped", "stopped"])

    def test_exit_cleanup_reports_open_port_and_preserves_original_failure(self):
        marker = self.root / "stops"
        checks = self.root / "checks"
        for module, script in (("hubble", "stop-hubble.sh"), ("server", "stop-hugegraph.sh")):
            directory = self.root / module / "bin"
            directory.mkdir(parents=True)
            command = directory / script
            command.write_text(f"#!/bin/sh\necho {module} >> {shlex.quote(str(marker))}\n")
            command.chmod(0o755)
        (self.root / "release-smoke.py").write_text(
            "import sys\nfrom pathlib import Path\n"
            f"with Path({str(checks)!r}).open('a') as output: output.write(sys.argv[-1] + '\\n')\n"
            "sys.exit(17 if sys.argv[-1] == '8088' else 0)\n")
        code = (f"RUN_DIR={shlex.quote(str(self.root))}; SCRIPT_DIR={shlex.quote(str(self.root))}; "
                f"HUBBLE_DIR={shlex.quote(str(self.root / 'hubble'))}; "
                f"SERVER_DIR={shlex.quote(str(self.root / 'server'))}; exit 7")
        result = self.shell(code)
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertEqual(marker.read_text().splitlines(), ["hubble", "server"])
        self.assertEqual(checks.read_text().splitlines(), ["8088", "8080"])
        self.assertIn("Service shutdown checks failed during cleanup", result.stdout)
        self.assertIn("VALIDATION FAILED", result.stdout)
        self.assertNotIn("VALIDATION PASSED", result.stdout)

    def test_prepare_failure_survives_ci_tee_pipeline(self):
        # Exercise the real preparation script with a failing Git transport and
        # the same explicit Bash pipefail behavior as the Actions step.
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        git = bin_dir / "git"
        git.write_text("#!/bin/sh\nif [ \"$1\" = init ]; then mkdir -p \"$3\"; exit 0; fi\n"
                       "if [ \"$3\" = fetch ]; then echo \"COPYFILE_DISABLE=$COPYFILE_DISABLE\"; echo 'transport failed' >&2; exit 23; fi\nexit 0\n")
        git.chmod(0o755)
        environment = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"], COPYFILE_DISABLE="0")
        command = (f"bash {shlex.quote(str(DIST / 'prepare-release.sh'))} 1.8.0 "
                   f"{'a' * 40} {'b' * 40} {shlex.quote(str(self.root / 'output'))} "
                   f"2>&1 | tee {shlex.quote(str(self.root / 'build.log'))}")
        result = subprocess.run(["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", command],
                                env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 23, result.stdout + result.stderr)
        self.assertIn("transport failed", (self.root / "build.log").read_text())
        self.assertIn("COPYFILE_DISABLE=1", (self.root / "build.log").read_text())

    def test_cleanup_preserves_startup_failure(self):
        result = self.shell(f"RUN_DIR={shlex.quote(str(self.root))}; exit 7")
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertIn("VALIDATION FAILED", result.stdout)
        self.assertNotIn("VALIDATION PASSED", result.stdout)

    def test_required_signature_and_invalid_gpg_fail(self):
        self.archive.write_bytes(b"release")
        Path(str(self.archive) + ".sha512").write_text(hashlib.sha512(b"release").hexdigest())
        code = f"RUN_DIR={shlex.quote(str(self.root))}; PACKAGES=({shlex.quote(str(self.archive))}); verify_integrity"
        result = self.shell(code)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing signature", result.stdout)
        (self.root / "gnupg").mkdir(mode=0o700)
        Path(str(self.archive) + ".asc").write_text("invalid signature")
        result = self.shell(code)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("RELEASE VALIDATION PASSED", result.stdout)

    def test_image_resource_does_not_waive_compiled_binary(self):
        resource = self.root / "docs/images"
        resource.mkdir(parents=True)
        (self.root / "LICENSE").write_text("Apache License, Version 2.0")
        (resource / "diagram.png").write_bytes(b"\x89PNG\x00\x01\x00")
        result = self.shell(f"cd {shlex.quote(str(self.root))}; check_binary_files fixture")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Review provenance/licensing", result.stdout)
        (resource / "compiled.jar").write_bytes(b"PK\x00\x01\x00")
        result = self.shell(f"cd {shlex.quote(str(self.root))}; check_binary_files fixture")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Undocumented binary file: ./docs/images/compiled.jar", result.stdout)

    def test_missing_required_packages_fail(self):
        result = self.shell(f"RELEASE_VERSION=1.8.0; DIST_DIR={shlex.quote(str(self.root))}; require_packages")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing required package", result.stdout)

    def test_extra_same_version_archive_rejected(self):
        for name in ("apache-hugegraph-1.8.0-src", "apache-hugegraph-1.8.0",
                     "apache-hugegraph-toolchain-1.8.0-src", "apache-hugegraph-toolchain-1.8.0"):
            (self.root / f"{name}.tar.gz").write_bytes(b"package")
        code = f"RELEASE_VERSION=1.8.0; DIST_DIR={shlex.quote(str(self.root))}; require_packages"
        self.assertEqual(self.shell(code).returncode, 0)
        (self.root / "apache-hugegraph-other-1.8.0.tar.gz").write_bytes(b"extra")
        result = self.shell(code)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Expected exactly the four Server/Toolchain archives", result.stdout)

    def test_staging_origin_rejects_central_or_local_sdk(self):
        sdk = ("hugegraph-common", "hg-pd-common", "hg-pd-client", "hg-pd-grpc", "hugegraph-core")
        for artifact in sdk:
            directory = self.root / "m2/org/apache/hugegraph" / artifact / "1.8.0"
            directory.mkdir(parents=True)
            metadata = []
            for extension in ("pom", "jar"):
                name = f"{artifact}-1.8.0.{extension}"
                (directory / name).write_bytes(b"downloaded")
                metadata.append(f"{name}>selected-staging=")
            (directory / "_remote.repositories").write_text("\n".join(metadata))
        distribution = self.root / "distribution"
        (distribution / "lib").mkdir(parents=True)
        SMOKE.staging_origin(str(self.root / "m2"), "1.8.0", str(distribution))
        metadata = self.root / "m2/org/apache/hugegraph/hugegraph-common/1.8.0/_remote.repositories"
        metadata.write_text(metadata.read_text().replace("selected-staging", "central"))
        with self.assertRaisesRegex(RuntimeError, "not fetched from selected staging"):
            SMOKE.staging_origin(str(self.root / "m2"), "1.8.0", str(distribution))

    def test_package_version_and_incubating_rejected(self):
        for name in ("apache-hugegraph-1.8.00-src.tar.gz", "apache-hugegraph-incubating-1.8.0-src.tar.gz"):
            result = self.shell(f"RELEASE_VERSION=1.8.0; check_package_name {shlex.quote(name)}")
            self.assertNotEqual(result.returncode, 0, name)

    def test_unique_directory_rejects_missing_and_ambiguous(self):
        command = f"unique_directory {shlex.quote(str(self.root))} 'apache-hugegraph-server-1.8.0'"
        self.assertNotEqual(self.shell(command).returncode, 0)
        for prefix in ("first", "second"):
            (self.root / prefix / "apache-hugegraph-server-1.8.0").mkdir(parents=True)
        self.assertNotEqual(self.shell(command).returncode, 0)


if __name__ == "__main__":
    unittest.main()
