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

# Sniff the documented origin/port spellings so the generated version config
# stays aligned with the origin Hugo itself will use. Every argument is still
# forwarded to Hugo unchanged; pflag's last-wins handling resolves overrides.
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
    -b=*) base_url=${argument#-b=} ;;
    -b?*) base_url=${argument#-b} ;;
    --port=*) port=${argument#*=} ;;
    -p=*) port=${argument#-p=} ;;
    -p?*) port=${argument#-p} ;;
  esac
  previous=$argument
done

if [ -n "$base_url" ]; then
  site_origin=$base_url
elif [ -n "${HG_DOC_SITE_ORIGIN:-}" ]; then
  site_origin=$HG_DOC_SITE_ORIGIN
elif [ "$mode" = "server" ]; then
  site_origin="http://localhost:${port:-1313}/"
else
  site_origin="https://hugegraph.apache.org/"
fi
case "$site_origin" in
  http://*|https://*) ;;
  *) printf 'scripts/hugo.sh: invalid site origin: %s\n' "$site_origin" >&2; exit 2 ;;
esac

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
(
  set -- scripts/versioning.py config \
    --site-origin "$site_origin" \
    --output "$config_file"
  if [ -n "${HG_DOC_VERSION:-}" ]; then
    set -- "$@" --version "$HG_DOC_VERSION"
  fi
  if [ -n "${HG_DOC_HISTORICAL_ORIGIN:-}" ]; then
    set -- "$@" --historical-origin "$HG_DOC_HISTORICAL_ORIGIN"
  fi
  exec "$python_bin" "$@"
)

if [ "$mode" = "server" ]; then
  if [ -n "$base_url" ] || [ -n "${HG_DOC_SITE_ORIGIN:-}" ]; then
    "$hugo_bin" server \
      --config "hugo.yaml,$config_file" \
      --appendPort=false \
      "$@"
  else
    "$hugo_bin" server --config "hugo.yaml,$config_file" "$@"
  fi
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
