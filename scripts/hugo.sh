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

reject_argument() {
  printf 'scripts/hugo.sh: argument is owned by the wrapper: %s\n' "$1" >&2
  exit 2
}

port=
base_url=
port_set=false
base_url_set=false
expect_value=
for argument in "$@"; do
  if [ -n "$expect_value" ]; then
    case "$argument" in
      -*) printf 'scripts/hugo.sh: missing value for %s\n' "$expect_value" >&2; exit 2 ;;
    esac
    case "$expect_value" in
      baseURL) base_url=$argument; base_url_set=true ;;
      port) port=$argument; port_set=true ;;
    esac
    expect_value=
    continue
  fi
  case "$argument" in
    --config|--config=*|-c|-c?*|\
    --configDir|--configDir=*|\
    --environment|--environment=*|-e|-e?*|\
    --cleanDestinationDir|--cleanDestinationDir=*|\
    --gc|--gc=*|\
    --minify|--minify=*|\
    --panicOnWarning|--panicOnWarning=*|\
    --printPathWarnings|--printPathWarnings=*|\
    --printI18nWarnings|--printI18nWarnings=*|\
    --logLevel|--logLevel=*|\
    --appendPort|--appendPort=*)
      reject_argument "$argument"
      ;;
    --baseURL|-b) expect_value=baseURL ;;
    --baseURL=*) base_url=${argument#*=}; base_url_set=true ;;
    -b=*) base_url=${argument#-b=}; base_url_set=true ;;
    -b?*) base_url=${argument#-b}; base_url_set=true ;;
    --port|-p) expect_value=port ;;
    --port=*) port=${argument#*=}; port_set=true ;;
    -p=*) port=${argument#-p=}; port_set=true ;;
    -p?*) port=${argument#-p}; port_set=true ;;
  esac
done
if [ -n "$expect_value" ]; then
  printf 'scripts/hugo.sh: missing value for %s\n' "$expect_value" >&2
  exit 2
fi
if [ "$base_url_set" = true ] && [ -z "$base_url" ]; then
  printf '%s\n' "scripts/hugo.sh: --baseURL cannot be empty" >&2
  exit 2
fi
if [ "$port_set" = true ] && [ -z "$port" ]; then
  printf '%s\n' "scripts/hugo.sh: --port cannot be empty" >&2
  exit 2
fi
if [ "$base_url_set" = true ] && [ -n "${HG_DOC_SITE_ORIGIN:-}" ]; then
  printf '%s\n' \
    "scripts/hugo.sh: use either --baseURL or HG_DOC_SITE_ORIGIN, not both" >&2
  exit 2
fi
if [ "$mode" = "build" ] && [ "$port_set" = true ]; then
  printf '%s\n' "scripts/hugo.sh: --port is valid only in server mode" >&2
  exit 2
fi
if [ -n "$port" ]; then
  case "$port" in
    *[!0-9]*) printf 'scripts/hugo.sh: invalid port: %s\n' "$port" >&2; exit 2 ;;
  esac
fi

if [ -n "${HG_DOC_SITE_ORIGIN:-}" ]; then
  site_origin=$HG_DOC_SITE_ORIGIN
elif [ -n "$base_url" ]; then
  site_origin=$base_url
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
