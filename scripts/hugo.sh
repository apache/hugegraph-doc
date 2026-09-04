#!/bin/sh
set -eu

usage() {
  printf '%s\n' \
    "Usage: scripts/hugo.sh server [Hugo arguments...]" \
    "       scripts/hugo.sh build [Hugo arguments...]"
}

if [ "$#" -eq 0 ]; then
  usage >&2
  exit 2
fi

mode=$1
shift
case "$mode" in
  server|build) ;;
  *)
    usage >&2
    exit 2
    ;;
esac

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_dir=$(dirname "$script_dir")
cd "$repo_dir"

port=
base_url=
previous=
for argument in "$@"; do
  case "$previous" in
    --baseURL|-b) base_url=$argument ;;
    --port|-p) port=$argument ;;
  esac
  case "$argument" in
    --baseURL=*) base_url=${argument#*=} ;;
    --port=*) port=${argument#*=} ;;
  esac
  previous=$argument
done

if [ -n "${HG_DOC_SITE_ORIGIN:-}" ]; then
  site_origin=$HG_DOC_SITE_ORIGIN
elif [ -n "$base_url" ]; then
  site_origin=$base_url
elif [ "$mode" = "server" ]; then
  site_origin="http://localhost:${port:-1313}/"
else
  site_origin="https://hugegraph.apache.org/"
fi

temp_dir=$(mktemp -d "${TMPDIR:-/tmp}/hugegraph-hugo.XXXXXX")
config_file=$temp_dir/version-config.json
cleanup() {
  if [ -d "$temp_dir" ]; then
    rm -f -- "$config_file"
    rmdir -- "$temp_dir"
  fi
}
trap cleanup 0 HUP INT TERM

python_bin=${PYTHON_BIN:-python3}
hugo_bin=${HUGO_BIN:-hugo}
version=${HG_DOC_VERSION:-latest}
if [ -n "${HG_DOC_HISTORICAL_ORIGIN:-}" ]; then
  "$python_bin" scripts/versioning.py config \
    --version "$version" \
    --site-origin "$site_origin" \
    --historical-origin "$HG_DOC_HISTORICAL_ORIGIN" \
    --output "$config_file"
else
  "$python_bin" scripts/versioning.py config \
    --version "$version" \
    --site-origin "$site_origin" \
    --output "$config_file"
fi

if [ "$mode" = "server" ]; then
  "$hugo_bin" server --config "hugo.yaml,$config_file" "$@"
else
  "$hugo_bin" \
    --config "hugo.yaml,$config_file" \
    --cleanDestinationDir \
    --gc \
    --minify \
    --environment production \
    --printPathWarnings \
    --printI18nWarnings \
    --panicOnWarning \
    --logLevel info \
    "$@"
fi
