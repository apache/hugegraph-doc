#!/bin/bash
set -o errexit
set -o pipefail

CONTENT_DIR="content"
EXIT_CODE=0

VERBOSE="${VERBOSE:-0}"

log_verbose() {
    if [[ "$VERBOSE" == "1" ]]; then
        echo "Info: $*"
    fi
}

ASSET_EXTENSIONS_REGEX='png|jpg|jpeg|svg|gif|webp|avif|ico|xml|yaml|yml|json|css|js|pdf|zip|tar\.gz|woff|woff2|ttf|eot|mp4|webm'
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || exit 1
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)" || exit 1
CONTENT_ROOT="$(cd "$REPO_ROOT/$CONTENT_DIR" && pwd)" || exit 1

if [[ ! -d "$CONTENT_ROOT" ]]; then
    echo "Error: content directory not found. Run from repository root."
    exit 1
fi

normalize_link() {
    local link="$1"

    # Decode common URL-encoded characters explicitly
    link="${link//%20/ }"   # space
    link="${link//%23/#}"   # hash
    link="${link//%2F/\/}"  # forward slash

    # Generic percent-decoding for remaining cases
    link="${link//%/\\x}"
    link="$(printf '%b' "$link")"

    link="${link%%#*}"
    link="${link%%\?*}"

    if [[ "$link" != "/" ]]; then
        link="${link%/}"
    fi

    printf "%s" "$link"
}

canonicalize_path() {
    local path="$1"
    local result=()
    local part
    local parts

    # Bash 3.2 compatible: use here-string
    IFS='/' read -r -a parts <<< "$path"

    for part in "${parts[@]}"; do
        if [[ -z "$part" || "$part" == "." ]]; then
            continue
        elif [[ "$part" == ".." ]]; then
            # Bash 3.2 compatible: calculate last index instead of using -1
            if [[ ${#result[@]} -gt 0 ]]; then
                local last_idx=$((${#result[@]} - 1))
                unset "result[$last_idx]"
            fi
        else
            result+=("$part")
        fi
    done

    if [[ ${#result[@]} -eq 0 ]]; then
        printf "/"
    else
        ( IFS='/'; printf "/%s" "${result[*]}" )
    fi
}

resolve_real_path() {
    local path="$1"

    if command -v python3 >/dev/null 2>&1; then
        # Use Python to compute realpath which resolves symlinks AND normalizes paths
        # Python's os.path.realpath is tolerant of non-existent final targets
        python3 - <<'PY' "$path"
import os
import sys
p = sys.argv[1]
print(os.path.realpath(p))
PY
    else
        # Fallback: Normalize without symlink resolution if Python3 unavailable
        # Note: This won't resolve symlinks, only normalize .. and . components
        canonicalize_path "$path"
    fi
}

check_internal_link() {
    local link="$1"
    local file="$2"
    local line_no="$3"
    local clean_link
    local target_path
    local location

    clean_link="$(normalize_link "$link")"

    [[ -z "$clean_link" || "$clean_link" == "#" ]] && return 0

    if [[ "$clean_link" == "{{"* ]]; then
        log_verbose "Skipping Hugo shortcode link: $link ($file:$line_no)"
        return 0
    fi

    local clean_lower
    clean_lower="$(printf "%s" "$clean_link" | tr '[:upper:]' '[:lower:]')"

    if [[ "$clean_lower" == http://* || "$clean_lower" == https://* || "$clean_lower" == "//"* ]]; then
        log_verbose "Skipping external link: $link ($file:$line_no)"
        return 0
    fi

    case "$clean_lower" in
        mailto:*|tel:*|javascript:*|data:*)
            return 0
            ;;
    esac

    if [[ "$clean_link" == /docs/* ]]; then
        target_path="$CONTENT_ROOT/en${clean_link}"

    elif [[ "$clean_link" == /cn/docs/* ]]; then
        target_path="$CONTENT_ROOT${clean_link}"

    elif [[ "$clean_link" == /community/* ]]; then
        target_path="$CONTENT_ROOT/en${clean_link}"

    elif [[ "$clean_link" == /blog/* || "$clean_link" == /cn/blog/* ]]; then
    # Blog URLs are permalink-based and don't map 1:1 to content file paths.
    # Skip deterministic filesystem validation for these routes.
    log_verbose "Skipping permalink-based blog link: $link ($file:$line_no)"
    return 0

    elif [[ "$clean_link" == /language/* ]]; then
        target_path="$CONTENT_ROOT/en${clean_link}"

    elif [[ "$clean_link" == /clients/* ]]; then
        target_path="$REPO_ROOT/static${clean_link}"

    elif [[ "$clean_link" == /* ]]; then
        location="$file"
        [[ -n "$line_no" ]] && location="$file:$line_no"

        echo "Error: Unsupported absolute internal path (cannot validate deterministically)"
        echo "  File: $location"
        echo "  Link: $link"

        EXIT_CODE=1
        return

    else
        local file_dir
        file_dir="$(cd "$(dirname "$file")" && pwd)"
        target_path="$file_dir/$clean_link"
    fi

    target_path="$(canonicalize_path "$target_path")"
    target_path="$(resolve_real_path "$target_path")"

    case "$target_path" in
        "$CONTENT_ROOT"/*) ;;
        "$REPO_ROOT/static"/*) ;;
        *)
            location="$file"
            [[ -n "$line_no" ]] && location="$file:$line_no"
            echo "Error: Link resolves outside content directory"
            echo "  File: $location"
            echo "  Link: $link"
            EXIT_CODE=1
            return
            ;;
    esac

    if [[ "$clean_lower" =~ \.(${ASSET_EXTENSIONS_REGEX})$ ]]; then
        if [[ -f "$target_path" ]]; then
            return 0
        else
            location="$file"
            [[ -n "$line_no" ]] && location="$file:$line_no"
            echo "Error: Broken link"
            echo "  File: $location"
            echo "  Link: $link"
            echo "  Target: $target_path"
            EXIT_CODE=1
            return
        fi
    fi

    if [[ -f "$target_path" || -f "$target_path.md" || -f "$target_path/_index.md" || -f "$target_path/README.md" ]]; then
        return 0
    fi

    location="$file"
    [[ -n "$line_no" ]] && location="$file:$line_no"

    echo "Error: Broken link"
    echo "  File: $location"
    echo "  Link: $link"
    echo "  Target: $target_path"
    EXIT_CODE=1
}

echo "Starting link validation..."

while IFS= read -r FILE; do

    CODE_LINES=""
    in_fence=false
    line_no=0

    while IFS= read -r line || [[ -n "$line" ]]; do
        ((++line_no))
        # NOTE:
        # Code fence detection is heuristic and does not validate proper pairing.
        # The logic simply toggles state when encountering ``` or ~~~ markers.
        # If a Markdown file contains an unclosed fence or mismatched fence types,
        # all subsequent lines may be treated as code and skipped from validation.
        # This behavior is intentional to keep the validator lightweight and
        # avoids implementing a full Markdown parser. Such cases require manual review.
        if [[ "$line" =~ ^[[:space:]]*(\`\`\`|~~~) ]]; then
            # NOTE:
            # Code fence detection assumes fences are properly paired.
            # If a Markdown file contains an unclosed or mismatched fence,
            # subsequent content may be treated as code and skipped.
            # This script does not attempt full Markdown validation.

            if $in_fence; then
                in_fence=false
            else
                in_fence=true
            fi
            CODE_LINES="$CODE_LINES $line_no "
            continue
        fi

        if $in_fence; then
            CODE_LINES="$CODE_LINES $line_no "
            continue
        fi

        # NOTE:
        # Inline code detection is heuristic and intentionally simplistic.
        # The logic assumes backticks are properly paired within a single line
        # after removing escaped backticks. Malformed Markdown, complex inline
        # constructs, or unusual escaping patterns may cause false positives
        # or false negatives. This validator does not implement a full Markdown
        # parser and therefore cannot guarantee perfect inline code detection.
        escaped_line="${line//\\\`/}"
        only_ticks="${escaped_line//[^\`]/}"
        inline_count=${#only_ticks}
        if (( inline_count % 2 == 1 )); then
            CODE_LINES="$CODE_LINES $line_no "
        fi

    done < "$FILE"

    while read -r MATCH || [[ -n "$MATCH" ]]; do
        [[ -z "$MATCH" ]] && continue

        LINE_NO="${MATCH%%:*}"
        LINK_PART="${MATCH#*:}"

        [[ "$CODE_LINES" == *" $LINE_NO "* ]] && continue

        LINK="${LINK_PART#*](}"
        LINK="${LINK%)}"

        check_internal_link "$LINK" "$FILE" "$LINE_NO"
    done < <(grep -n -oE '\]\([^)]+\)' "$FILE" || true)

    unset CODE_LINES
done < <(find "$CONTENT_ROOT" -type f -name "*.md" 2>/dev/null || true)

if [[ $EXIT_CODE -eq 0 ]]; then
    echo "Link validation passed!"
else
    echo "Link validation failed!"
fi

exit $EXIT_CODE
