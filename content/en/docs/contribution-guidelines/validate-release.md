---
title: "Validate Apache Release"
linkTitle: "Validate Apache Release"
weight: 3
---

> [!NOTE]
> This doc will be updated continuously.
> - **Java version**: use Java 17 for 1.8.0 builds and release verification; Java 11 for 1.7.0; Java 8 is no longer supported since 1.5.0 (except the client).
> - **Graduation**: Apache HugeGraph graduated in January 2026. Release voting is now completed within the HugeGraph community (PMC binding votes on `dev@hugegraph.apache.org`); Incubator approval is no longer required.

## Automated release validation

The workflow and `dist/validate-release.sh` use the same Java 17 checks. Specify the package version and SVN RC path separately,
and use the Maven staging repository from the vote email. The four Server/Toolchain source and binary archives are required.
The same directory may also contain AI and Computer source archives. Every archive must include SHA512 and GPG signatures;
unknown packages and mismatched versions are rejected. All present archives receive integrity, contents and license checks;
Computer sources are also rebuilt with Maven. AI and Computer product runtime validation remains a separate task.

```bash
bash dist/validate-release.sh --svn-path 1.8.0/RC1 \
  --staging-repository https://repository.apache.org/content/repositories/<staging-id>/ 1.8.0 imbajin
# Existing local-package interface is preserved:
bash dist/validate-release.sh 1.8.0 imbajin /path/to/rc 17
```

Strict RC validation builds with fresh, separate Maven repositories and does not preinstall a local Server SDK.
It validates both source-built and downloaded binaries through Server, Client, ordinary Loader, Tools and Hubble business assertions.

Logs remain available after failures. Once the validation script executes and creates an evidence directory, the console and GitHub Job Summary show the result, failed phase, review notes and log location (if the workflow fails during early checks like `Check validator` or pre-build steps before the validator runs, inspect the step console logs directly).
See [the validator instructions](https://github.com/apache/hugegraph-doc/blob/master/dist/README.md) for local prevalidation and evidence paths.

The `source-prevalidation` workflow mode uses exact Server/Toolchain commit SHAs and unsigned archives;
its result does not prove real RC signatures, downloads or remote staging dependency resolution.
Review `license-review-*.txt` for license choices and exceptions; explicit Category-X-only dependencies block validation.
Automatic success does not approve the release, and source prevalidation is separate from RC acceptance.

## Verification

When the internal temporary release and packaging work is completed, other community developers (
especially PMC) need to participate in verification based on ASF release policy and checklist references:
- [ASF release policy](https://www.apache.org/legal/release-policy.html)
- [Incubator checklist (historical reference)](https://cwiki.apache.org/confluence/display/INCUBATOR/Incubator+Release+Checklist)
To ensure the "correctness + completeness" of someone's published version, here requires **everyone
** to participate as much as possible, and then explain which items you have **checked** in the
subsequent **email reply**.(The following are the core items)

#### 1. prepare

If there is no svn or gpg or wget environment locally, it is recommended to install it first 
(windows recommend using WSL2 environment, or at least `git-bash`), also make sure to install java 
(Java 17 for HugeGraph 1.8.0+, Java 11 for 1.7.0) and maven software (≥ 3.6.3)

```bash
# 1. install svn
# ubuntu/debian
sudo apt install subversion -y
# MacOS
brew install subversion
# To verify that the installation was successful, execute the following command:
svn --version

# 2. install gpg
# ubuntu/debian
sudo apt-get install gnupg -y
# MacOS
brew install gnupg
# To verify that the installation was successful, execute the following command:
gpg --version

# 3. install wget (we will enhance it later, like use `curl`)
# ubuntu/debian
sudo apt-get install wget -y
# MacOS
brew install wget

# 4. Download the hugegraph-svn directory 
# For version number, pay attention to fill in the verification version
svn co https://dist.apache.org/repos/dist/dev/hugegraph/1.x.x/
# (Note) If svn downloads a file very slowly, 
# you can consider wget to download a single file, as follows (or consider using a proxy)
wget https://dist.apache.org/repos/dist/dev/hugegraph/1.x.x/apache-hugegraph-toolchain-1.x.x.tar.gz
```

#### 2. check hash value

First you need to check the file integrity of the `source + binary` package, Verify by `shasum` to
ensure that it is consistent with the hash value published on apache/GitHub (Usually sha512), Here
is the same as the last step of 0x02 inspection.

```bash
(
  for archive in *.tar.gz; do
    printf '%s\n' "$archive"
    grep -E "([[:space:]]|\*)${archive}$|^SHA512[[:space:]]*\(${archive}\)[[:space:]]*=" "$archive.sha512" | shasum -a 512 --check || exit "$?"
  done
)
```

Run the loop in a subshell; the check verifies that the sidecar references the current archive (in either standard or BSD checksum format), and the first failed checksum stops validation without closing your interactive terminal.

#### 3. check gpg signature

Import the project's public keys, compare the signer's full fingerprint with the release vote email, and verify each archive's signature.

```bash
# 1. Download project trusted public key to local (required for the first time) & import
curl  https://downloads.apache.org/hugegraph/KEYS > KEYS
gpg --import KEYS

# 2. Compare the full primary-key fingerprint with the release vote email
release_signer_fingerprint='<signer-full-fingerprint>'
gpg --fingerprint -- "$release_signer_fingerprint"

# 3. Use a subshell so verification failure does not exit your interactive terminal
(
  for archive in *.tar.gz; do
    gpg --status-fd 1 --verify -- "$archive.asc" "$archive" > "$archive.status" || {
      status=$?
      printf 'Signature verification failed: %s\n' "$archive" >&2
      cat "$archive.status"
      exit "$status"
    }
    cat "$archive.status"
    if grep -Eq '^\[GNUPG:\] (REVKEYSIG|EXPKEYSIG|EXPSIG)( |$)' "$archive.status"; then
      printf 'Expired or revoked signature: %s\n' "$archive" >&2
      exit 1
    fi
    grep -q '^\[GNUPG:\] VALIDSIG ' "$archive.status" || {
      printf 'Missing valid signature: %s\n' "$archive" >&2
      exit 1
    }
  done
)
```

Require exit code zero and a `VALIDSIG` fingerprint matching the vote signer. When a signing subkey is used, compare its reported
primary-key fingerprint. A key-trust warning alone does not invalidate a signature; do not infer success from localized `Good signature` text.
Stop on `REVKEYSIG`, `EXPKEYSIG` or `EXPSIG`, even alongside `VALIDSIG` or exit code zero; ask the release manager to review or update the candidate.
See the [GnuPG status format](https://github.com/gpg/gnupg/blob/master/doc/DETAILS).

First confirm the overall integrity/consistency, and then confirm the specific content (**key**)

#### 4. Check the archive contents

Check the contents of the archive downloaded from preparation work. Divided into two aspects: source code package + binary package, The source code package is stricter, it can be said that the core part (Because it is longer, For a complete list refer to
the official [Wiki](https://cwiki.apache.org/confluence/display/INCUBATOR/Incubator+Release+Checklist))

##### A. source package

After decompressing `*hugegraph*src.tar.gz`, Do the following checks:

1. package/folder naming should match the release line (historical releases may still contain `incubating`), and no **empty** files/folders
2. `LICENSE` + `NOTICE` exist and the content is normal; `DISCLAIMER` is required for historical incubating artifacts
3. **does not exist** binaries (without LICENSE)
4. The source code files all contain the standard `ASF License` header (this could be done with
   the `Maven RAT` plugin)
5. Check whether the `pom.xml` version number of each parent/child module is consistent (and meet
   expectations)
6. Finally, make sure the source code works/compiles correctly

```bash
# Use JDK 17 for HugeGraph 1.8.0, including Computer 1.8.0 sources.
# Use Java 11 for HugeGraph 1.7.0.
# java --version

# try to compile in the Unix env to check if it works well (-P is optional)
mvn -s /path/to/staging-settings.xml -Dmaven.repo.local=/path/to/fresh-m2 \
  clean install -Papache-release -DskipTests -Dgpg.skip=true
```

The manual Maven command must use settings pointing to the staging repository from the vote email and a fresh local repository.
Do not preinstall local Server SDK artifacts to hide missing staged dependencies. The automated validator configures these settings for you.

##### B. binary package

After decompressing `xxx-hugegraph.tar.gz`, perform the following checks:

1. package/folder naming should match the release line (historical releases may still contain `incubating`)
2. `LICENSE` and `NOTICE` file exists and the content is normal (`DISCLAIMER` applies to historical incubating artifacts)
3. start server

```bash
# hugegraph-server
bin/start-hugegraph.sh

# hugegraph-loader
bin/hugegraph-loader.sh -g hugegraph -f example/file/struct.json -s example/file/schema.groovy

# hugegraph-hubble
bin/start-hubble.sh
```

[Quick start guides](/docs/quickstart/) cover the component startup procedures.

**Note:** If a third-party dependency is introduced in the binary package, you need to update the
LICENSE and add the third-party dependent LICENSE; if the third-party dependent LICENSE is Apache
2.0, and the corresponding project contains NOTICE, you also need to update Our NOTICE file

#### 5. Check the official website and GitHub and other pages

1. Make sure that the official website at least meets [apache website check](https://whimsy.apache.org/pods/project/hugegraph),
   and no circular links, etc.
2. Update **download link** and release notes updated
3. ...

## Mail Template

After the check & test, you should reply to the mail with the following content: (normal devs & PMC)

```markdown
[] +1 approve

[] +0 no opinion

[] -1 disapprove with the reason
```

```markdown
+1 (non-binding)
I checked:
1. Download link/tag in mail are valid
2. Checksum and GPG signatures are OK
3. LICENSE & NOTICE exist
4. Build successfully on XX OS & Version XX
5. No unexpected binary files
6. Date is right in the NOTICE file
7. Compile from source is fine under JavaXX
8. No empty file & directory found
9. Test running XXX service OK
10. ....
```

and the PMC members should reply with `binding`, it's important for summary the valid votes:

```markdown
+1 (binding)
I checked:
1. Download link/tag in mail are valid
2. Checksum and GPG signatures are OK
3. LICENSE & NOTICE exist
4. Build successfully on XX OS & Version XX
5. No unexpected binary files
6. Date is right in the NOTICE file
7. Compile from source is fine under JavaXX
8. No empty file & directory found
9. Test running XX process OK
10. ....
```
