#!/usr/bin/env bash
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euo pipefail

DOWNLOAD_URL_PREFIX="https://downloads.apache.org/hugegraph"

usage() {
  cat <<USAGE
Usage: $(basename "$0") <release-version>

Examples:
  $(basename "$0") 1.7.0
USAGE
}

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

download_tarball() {
  local tar_name=$1
  local url=""
  if [[ -f "$tar_name" ]]; then
    log "Reuse local tarball: $tar_name"
    return 0
  fi

  url="${DOWNLOAD_URL_PREFIX}/${RELEASE_VERSION}/${tar_name}"
  if ! wget --spider -q "$url"; then
    echo "Cannot find tarball: $url" >&2
    return 1
  fi

  log "Download $url"
  wget "$url"
}

extract_tar_if_needed() {
  local tar_name=$1
  local top_dir
  top_dir=$(tar -tzf "$tar_name" | head -n1 | cut -d'/' -f1)
  if [[ -n "$top_dir" && -d "$top_dir" ]]; then
    log "Skip extract, directory already exists: $top_dir"
  else
    log "Extract $tar_name"
    tar -xzvf "$tar_name"
  fi
}

find_server_dir() {
  find . -maxdepth 3 -type d -name "*hugegraph-server*${RELEASE_VERSION}*" | head -n1
}

find_hubble_dir() {
  find . -maxdepth 4 -type d -name "*hubble*${RELEASE_VERSION}*" | head -n1
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --help|-h)
        usage
        exit 0
        ;;
      --*)
        echo "Unknown option: $1" >&2
        usage
        exit 1
        ;;
      *)
        break
        ;;
    esac
  done

  RELEASE_VERSION=${1:-}
  if [[ -z "$RELEASE_VERSION" ]]; then
    echo "Please provide release version, e.g. 1.7.0" >&2
    usage
    exit 1
  fi
}

main() {
  parse_args "$@"
  log "Release version: $RELEASE_VERSION"
  log "Download prefix: $DOWNLOAD_URL_PREFIX"

  local server_tar="apache-hugegraph-${RELEASE_VERSION}.tar.gz"
  local toolchain_tar="apache-hugegraph-toolchain-${RELEASE_VERSION}.tar.gz"

  download_tarball "$server_tar"
  download_tarball "$toolchain_tar"

  extract_tar_if_needed "${server_tar}"
  extract_tar_if_needed "${toolchain_tar}"

  local server_dir
  server_dir=$(find_server_dir)
  if [[ -z "$server_dir" ]]; then
    echo "Cannot find hugegraph-server directory for version $RELEASE_VERSION" >&2
    exit 1
  fi

  local hubble_dir
  hubble_dir=$(find_hubble_dir)
  if [[ -z "$hubble_dir" ]]; then
    echo "Cannot find hugegraph-hubble directory for version $RELEASE_VERSION" >&2
    exit 1
  fi

  log "Start hugegraph-server from $server_dir"
  pushd "$server_dir" >/dev/null
  bin/init-store.sh
  sleep 3
  bin/start-hugegraph.sh
  popd >/dev/null

  log "Start hugegraph-hubble from $hubble_dir"
  pushd "$hubble_dir" >/dev/null
  bin/start-hubble.sh
  popd >/dev/null
}

main "$@"
