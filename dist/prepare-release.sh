#!/usr/bin/env bash
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

# Build unsigned archives from exact revisions for prevalidation only.
set -euo pipefail
# Prevent BSD tar from adding macOS resource forks to generated release archives.
export COPYFILE_DISABLE=1
VERSION=${1:?Release version required}
SERVER_SHA=${2:?Full Server commit SHA required}
TOOLCHAIN_SHA=${3:?Full Toolchain commit SHA required}
OUTPUT=${4:?New output directory required}
STAGING_REPOSITORY=${5:-}
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
[[ "$SERVER_SHA" =~ ^[0-9a-f]{40}$ && "$TOOLCHAIN_SHA" =~ ^[0-9a-f]{40}$ ]]
if [[ -n "$STAGING_REPOSITORY" ]]; then
    [[ "$STAGING_REPOSITORY" =~ ^https://repository\.apache\.org/content/repositories/orgapachehugegraph-[0-9]+/?$ ]] || {
        echo 'Expected a specific Apache HugeGraph staging repository URL'; exit 1;
    }
fi
[[ ! -e "$OUTPUT" ]] || { echo "Refusing to overwrite $OUTPUT"; exit 1; }
mkdir -p "$OUTPUT/packages" "$OUTPUT/source" "$OUTPUT/m2"
OUTPUT=$(cd "$OUTPUT" && pwd)
MAVEN_ARGS=(-B -ntp -Dmaven.repo.local="$OUTPUT/m2" -Papache-release -DskipTests -Dgpg.skip=true -Dmaven.javadoc.skip=true)
SERVER_GOAL=install
TOOLCHAIN_ARGS=("${MAVEN_ARGS[@]}")
SDK_ORIGIN="$OUTPUT/m2 (same Server source, NOT remote staging)"
if [[ -n "$STAGING_REPOSITORY" ]]; then
    # Do not install local SDK artifacts over the candidate being verified.
    SERVER_GOAL=package
    SDK_ORIGIN="$STAGING_REPOSITORY (remote staging; SDK content NOT compared with Server commit)"
    cat > "$OUTPUT/settings.xml" <<EOF
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0">
  <mirrors><mirror><id>selected-staging</id><mirrorOf>staged-releases,apache.releases.https</mirrorOf>
    <url>$STAGING_REPOSITORY</url>
  </mirror></mirrors>
</settings>
EOF
    TOOLCHAIN_ARGS+=(-Pstage -s "$OUTPUT/settings.xml")
fi

archive() {
    local repository=$1 sha=$2 name=$3 upstream
    if [[ "$repository" == server ]]; then upstream=hugegraph; else upstream=hugegraph-toolchain; fi
    git init -q "$OUTPUT/git-$repository"
    git -C "$OUTPUT/git-$repository" remote add origin "https://github.com/apache/$upstream.git"
    git -C "$OUTPUT/git-$repository" fetch --depth=1 origin "$sha"
    [[ $(git -C "$OUTPUT/git-$repository" rev-parse FETCH_HEAD) == "$sha" ]]
    git -C "$OUTPUT/git-$repository" archive --format=tar.gz --prefix="$name/" "$sha" > "$OUTPUT/packages/$name.tar.gz"
    tar -xzf "$OUTPUT/packages/$name.tar.gz" -C "$OUTPUT/source"
}
archive server "$SERVER_SHA" "apache-hugegraph-$VERSION-src"
archive toolchain "$TOOLCHAIN_SHA" "apache-hugegraph-toolchain-$VERSION-src"
# Server's root CI-friendly POM needs flattening before packaging or installation.
# The default install supplies the same-source SDK to Toolchain. Nested clean
# removes the parent flattened POM, so clean first.
(cd "$OUTPUT/source/apache-hugegraph-$VERSION-src" && \
    mvn clean "${MAVEN_ARGS[@]}" && \
    mvn org.codehaus.mojo:flatten-maven-plugin:1.3.0:flatten "$SERVER_GOAL" "${MAVEN_ARGS[@]}" \
        -Dflatten.mode=resolveCiFriendliesOnly -DupdatePomFile=true)
(cd "$OUTPUT/source/apache-hugegraph-toolchain-$VERSION-src" && \
    mvn clean "${TOOLCHAIN_ARGS[@]}" && mvn install "${TOOLCHAIN_ARGS[@]}")

if [[ -n "$STAGING_REPOSITORY" ]]; then
    toolchain_source="$OUTPUT/source/apache-hugegraph-toolchain-$VERSION-src"
    distribution="$toolchain_source/apache-hugegraph-toolchain-$VERSION"
    sdk_verifier="$toolchain_source/hugegraph-client/assembly/travis/verify_candidate_image_sdk.py"
    [[ -f "$sdk_verifier" ]] || sdk_verifier="$toolchain_source/.github/scripts/verify_candidate_image_sdk.py"
    python3 "$(dirname "${BASH_SOURCE[0]}")/release-smoke.py" staging-origin "$OUTPUT/m2" "$VERSION" \
        "$distribution" "$STAGING_REPOSITORY"
    for module in loader tools hubble; do
        matches=()
        while IFS= read -r path; do matches+=("$path"); done < <(
            find "$distribution" -maxdepth 4 -type d -name "apache-hugegraph-$module-$VERSION")
        [[ ${#matches[@]} -eq 1 ]] || { echo "Expected one $module distribution"; exit 1; }
        python3 "$sdk_verifier" "$OUTPUT/m2" --mode release --version "$VERSION" \
            --distribution "${matches[0]}" --module "$module"
    done
fi

for component in hugegraph hugegraph-toolchain; do
    archive_path="$OUTPUT/source/apache-$component-$VERSION-src/target/apache-$component-$VERSION.tar.gz"
    [[ -f "$archive_path" ]] || { echo "Missing built binary archive: $archive_path"; exit 1; }
    cp "$archive_path" "$OUTPUT/packages/"
done
(cd "$OUTPUT/packages" && for package in *.tar.gz; do shasum -a 512 "$package" > "$package.sha512"; done)
cat > "$OUTPUT/origin.txt" <<EOF
Unsigned source prevalidation, NOT an ASF release candidate
Server: https://github.com/apache/hugegraph/commit/$SERVER_SHA
Toolchain: https://github.com/apache/hugegraph-toolchain/commit/$TOOLCHAIN_SHA
SDK repository: $SDK_ORIGIN
Java: $(java -version 2>&1 | head -n 1)
EOF
cat "$OUTPUT/origin.txt"
