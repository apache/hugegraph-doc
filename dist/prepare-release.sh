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
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
[[ "$SERVER_SHA" =~ ^[0-9a-f]{40}$ && "$TOOLCHAIN_SHA" =~ ^[0-9a-f]{40}$ ]]
[[ ! -e "$OUTPUT" ]] || { echo "Refusing to overwrite $OUTPUT"; exit 1; }
mkdir -p "$OUTPUT/packages" "$OUTPUT/source" "$OUTPUT/m2"
OUTPUT=$(cd "$OUTPUT" && pwd)
MAVEN_ARGS=(-B -ntp -Dmaven.repo.local="$OUTPUT/m2" -Papache-release -DskipTests -Dgpg.skip=true -Dmaven.javadoc.skip=true)
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
# Server's root CI-friendly POM needs flattening before it is installed for SDK
# consumers. Its nested clean removes the parent flattened POM, so clean first.
(cd "$OUTPUT/source/apache-hugegraph-$VERSION-src" && \
    mvn clean "${MAVEN_ARGS[@]}" && \
    mvn org.codehaus.mojo:flatten-maven-plugin:1.3.0:flatten install "${MAVEN_ARGS[@]}" \
        -Dflatten.mode=resolveCiFriendliesOnly -DupdatePomFile=true)
(cd "$OUTPUT/source/apache-hugegraph-toolchain-$VERSION-src" && \
    mvn clean "${MAVEN_ARGS[@]}" && mvn install "${MAVEN_ARGS[@]}")
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
SDK repository: $OUTPUT/m2 (same Server source, NOT remote staging)
Java: $(java -version 2>&1 | head -n 1)
EOF
cat "$OUTPUT/origin.txt"
