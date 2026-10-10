#!/usr/bin/env bash
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with this
# work for additional information regarding copyright ownership. The ASF
# licenses this file to You under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euo pipefail
# Prevent BSD tar from adding macOS resource forks to generated release archives.
export COPYFILE_DISABLE=1
shopt -s nullglob
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SVN_URL_PREFIX=https://dist.apache.org/repos/dist/dev/hugegraph
KEYS_URL=https://downloads.apache.org/hugegraph/KEYS
MAX_FILE_SIZE=800k
CATEGORY_X='(^|[^[:alnum:]_])(GPL|LGPL|BCL|RSAL|QPL|SSPL|CPOL|NPL1)([^[:alnum:]_]|$)|Sleepycat License|BSD-4-Clause|JSR-275|Amazon Software License|Creative Commons Non-Commercial|JSON\.org'
CATEGORY_B='(^|[^[:alnum:]_])(CDDL1|CPL|EPL|IPL|MPL|SPL|OFL)([^[:alnum:]_]|$)|OSL-3.0|UnRAR License|Erlang Public License|Ubuntu Font License Version 1.0|IPA Font License Agreement v1.0|EPL2.0|CC-BY'
VALIDATION_ERRORS=()
VALIDATION_WARNINGS=()
TOTAL_CHECKS=0
PASSED_CHECKS=0
CURRENT_STEP=''
CURRENT_PACKAGE=''
SVN_PATH=''
STAGING_REPOSITORY=https://repository.apache.org/content/groups/staging/
SOURCE_PREVALIDATION=0
SDK_REPOSITORY=''
SERVER_DIR=''
HUBBLE_DIR=''
RUN_DIR=''
SDK_VERIFIER=''
VALIDATION_COMPLETE=0
MAVEN_ARGS=()

info() { printf '%s\n' "$*"; }
success() { info "PASS: $*"; }
warn() { info "WARN: $*"; }
collect_error() { VALIDATION_ERRORS+=("[$CURRENT_STEP][$CURRENT_PACKAGE] $*"); info "ERROR: $*"; }
collect_warning() { VALIDATION_WARNINGS+=("[$CURRENT_STEP][$CURRENT_PACKAGE] $*"); warn "$*"; }
mark_check_passed() { PASSED_CHECKS=$((PASSED_CHECKS + 1)); }

usage() {
    cat <<'EOF'
Usage: validate-release.sh [options] <version> <gpg-user> [local-path] [java-version]
  --svn-path PATH           Candidate path below dev/hugegraph (default: version)
  --staging-repository URL  Maven staging repository URL
  --source-prevalidation   Unsigned same-source check, never a real RC validation
  --sdk-repository PATH     Same-source SDK Maven repository (prevalidation only)
  --work-dir PATH           Parent directory for a new validation run
  --non-interactive         Accepted for existing CI/local callers
  --help                    Show help
Java 17 is required. For real RC checks all four Server/Toolchain source/binary
packages, SHA512 files and signatures must exist. Logs and fresh Maven repositories
are retained in the validation run directory, including on failure.
EOF
}

summary() {
    local status=$1
    info '=== Validation summary ==='
    if [[ $status -ne 0 ]]; then
        info "VALIDATION FAILED (exit $status)"
        if [[ $VALIDATION_COMPLETE -eq 1 ]]; then
            info 'Checks completed; see errors or cleanup log'
        else
            info "Stopped at: ${CURRENT_STEP:-initialization} / ${CURRENT_PACKAGE:-package set}"
        fi
    elif [[ $VALIDATION_COMPLETE -eq 0 ]]; then
        info 'CHECKS COMPLETED; full release validation was not requested'
    elif [[ $SOURCE_PREVALIDATION -eq 1 ]]; then
        info 'SOURCE PREVALIDATION AUTOMATED CHECKS PASSED'
    else
        info 'AUTOMATED RELEASE CHECKS PASSED'
    fi
    info "Release: ${RELEASE_VERSION:-not selected}"
    if declare -p PACKAGES >/dev/null 2>&1; then info "Packages selected: ${#PACKAGES[@]}"; fi
    if [[ $VALIDATION_COMPLETE -eq 1 ]]; then
        info 'Server/Toolchain: source and binary runtime checks passed'
        if [[ ${#PACKAGES[@]} -gt 4 ]]; then
            info 'Extra components: source checks only; product runtime NOT checked'
        fi
    fi
    info "Review notes: ${#VALIDATION_WARNINGS[@]}"
    if [[ $SOURCE_PREVALIDATION -eq 1 ]]; then
        info 'RC signatures/download/staging origin NOT verified'
    fi
    info 'Manual licensing review and release approval remain required'
    for entry in ${VALIDATION_ERRORS[@]+"${VALIDATION_ERRORS[@]}"}; do info "ERROR: ${entry%%$'\n'*}"; done
    for entry in ${VALIDATION_WARNINGS[@]+"${VALIDATION_WARNINGS[@]}"}; do info "REVIEW: ${entry%%$'\n'*}"; done
    info "Evidence: $RUN_DIR"
}

cleanup() {
    local status=$?
    trap - EXIT
    set +e
    if ! stop_services; then
        info 'ERROR: Service shutdown checks failed during cleanup'
        if [[ $status -eq 0 ]]; then status=1; fi
    fi
    if [[ ${#VALIDATION_ERRORS[@]} -gt 0 && $status -eq 0 ]]; then status=1; fi
    if [[ -n "$RUN_DIR" ]]; then
        summary "$status"
        if [[ -n ${GITHUB_STEP_SUMMARY:-} ]]; then
            { printf '### Release validation\n\n```text\n'; summary "$status"; printf '```\n'; } >> "$GITHUB_STEP_SUMMARY"
        fi
    fi
    exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

check_package_name() {
    local package=$1
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [[ "$package" != apache-hugegraph* ]]; then
        collect_error "Package name '$package' should start with 'apache-hugegraph'"
        return 1
    fi

    if [[ "$package" != *"-${RELEASE_VERSION}.tar.gz" && "$package" != *"-${RELEASE_VERSION}-src.tar.gz" ]]; then
        collect_error "Package name '$package' does not include release version '${RELEASE_VERSION}'"
        return 1
    fi

    if [[ "$package" =~ incubating ]]; then
        collect_error "Package '$package' should not contain 'incubating' for post-graduation releases"
        return 1
    fi

    mark_check_passed
    return 0
}

check_required_files() {
    local package=$1
    local has_error=0

    if [[ ! -f "LICENSE" ]]; then
        collect_error "Package '$package' missing LICENSE file"
        has_error=1
    else
        mark_check_passed
    fi

    if [[ ! -f "NOTICE" ]]; then
        collect_error "Package '$package' missing NOTICE file"
        has_error=1
    else
        mark_check_passed
    fi

    return $has_error
}

check_license_categories() {
    local package=$1
    shift
    local files=("$@")
    local has_error=0

    # Check Category X (Prohibited)
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    local cat_x_matches
    cat_x_matches=$(grep -r -E "$CATEGORY_X" "${files[@]}" 2>/dev/null)
    local cat_x_count
    cat_x_count=$(echo "$cat_x_matches" | grep -c '.' | tr -d ' ')

    if [[ $cat_x_count -ne 0 ]]; then
        # Build detailed error message with license information
        local error_details="Package '$package' contains $cat_x_count prohibited ASF Category X license(s):"

        # Extract and format each violation
        while IFS= read -r match_line; do
            if [[ -n "$match_line" ]]; then
                # Parse file:content format
                local file_name
                file_name=$(echo "$match_line" | cut -d':' -f1)
                local license_info
                license_info=$(echo "$match_line" | cut -d':' -f2-)

                # Try to extract specific license name
                local license_name
                license_name=$(echo "$license_info" | grep -oE "$CATEGORY_X" | head -n1)

                error_details="${error_details}\n    - File: ${file_name}\n      License: ${license_name}\n      Context: ${license_info}"
            fi
        done <<< "$cat_x_matches"

        collect_error "$error_details"
        has_error=1
    else
        mark_check_passed
    fi

    # Check Category B (Must be documented - warning only)
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    local cat_b_count
    cat_b_count=$(grep -r -E "$CATEGORY_B" "${files[@]}" 2>/dev/null | wc -l | tr -d ' ')
    if [[ $cat_b_count -ne 0 ]]; then
        collect_warning "Package '$package' contains $cat_b_count ASF Category B license(s) - please verify documentation"
    else
        mark_check_passed
    fi

    return $has_error
}


check_binary_licenses() {
    local package=$1 matches
    matches=$(grep -rn -E "$CATEGORY_X|$CATEGORY_B" LICENSE NOTICE licenses 2>/dev/null || true)
    if [[ -n "$matches" ]]; then
        collect_warning "Package '$package': inspect aggregate license mentions manually; keywords alone do not prove a bundled dependency's license"
        printf '%s\n' "$matches"
    fi
    python3 "$SCRIPT_DIR/release-smoke.py" binary-licenses "$PWD" "$RUN_DIR/license-review-${package%.tar.gz}.txt" ||
        collect_error "Package '$package': actual dependency license check failed; inspect the license review report"
}

check_empty_files_and_dirs() {
    local package=$1
    local has_error=0

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    # Find empty directories
    local empty_dirs=()
    while IFS= read -r empty_dir; do
        empty_dirs+=("$empty_dir")
    done < <(find . -type d -empty 2>/dev/null)

    # Find empty files
    local empty_files=()
    while IFS= read -r empty_file; do
        empty_files+=("$empty_file")
    done < <(find . -type f -empty 2>/dev/null)

    if [[ ${#empty_dirs[@]} -gt 0 ]]; then
        collect_error "Package '$package' contains ${#empty_dirs[@]} empty director(y/ies):"
        printf '    %s\n' "${empty_dirs[@]}"
        has_error=1
    fi

    if [[ ${#empty_files[@]} -gt 0 ]]; then
        collect_error "Package '$package' contains ${#empty_files[@]} empty file(s):"
        printf '    %s\n' "${empty_files[@]}"
        has_error=1
    fi

    if [[ $has_error -eq 0 ]]; then
        mark_check_passed
    fi

    return $has_error
}

check_file_sizes() {
    local package=$1
    local max_size=$2
    local has_error=0

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    local large_files=()
    while IFS= read -r large_file; do
        large_files+=("$large_file")
    done < <(find . -type f -size "+${max_size}" 2>/dev/null)

    if [[ ${#large_files[@]} -gt 0 ]]; then
        collect_warning "Package '$package' contains ${#large_files[@]} file(s) larger than ${max_size}; review these manually:"
        for file in "${large_files[@]}"; do
            local size
            size=$(du -h "$file" | awk '{print $1}')
            echo "    $file ($size)"
        done
    else
        mark_check_passed
    fi

    return $has_error
}

check_binary_files() {
    local package=$1
    local has_error=0

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    info "Checking for undocumented binary files..."

    local binary_count=0
    local undocumented_count=0
    local image_resources=()

    # Find binary files using perl
    while IFS= read -r binary_file; do
        binary_count=$((binary_count + 1))
        local file_name
        file_name=$(basename "$binary_file")

        # Check if documented in LICENSE
        if [[ ( "$binary_file" == ./docs/images/* || "$binary_file" == ./helm/*/images/* ||
                "$binary_file" == ./hugegraph-hubble/docs/images/* || "$binary_file" == ./.github/images/* ||
                "$binary_file" == ./hugegraph-hubble/hubble-fe/public/* ||
                "$binary_file" == ./hugegraph-hubble/hubble-fe/src/assets/* ) &&
              ( "$binary_file" == *.png || "$binary_file" == *.jpg ) ]]; then
            # Documentation/UI images are source resources, not compiled dependencies.
            # Their provenance/licensing still needs review; never waive JAR/native checks.
            image_resources+=("$binary_file")
        elif grep -Fq "$file_name" LICENSE 2>/dev/null; then
            success "Binary file '$binary_file' is documented in LICENSE"
        else
            collect_error "Undocumented binary file: $binary_file"
            undocumented_count=$((undocumented_count + 1))
            has_error=1
        fi
    done < <(find . -type f 2>/dev/null | perl -lne 'print if -B $_')

    if [[ ${#image_resources[@]} -gt 0 ]]; then
        collect_warning "Review provenance/licensing of ${#image_resources[@]} documentation/UI image resources:"
        printf '    %s\n' "${image_resources[@]}"
    fi

    if [[ $binary_count -eq 0 ]]; then
        success "No binary files found"
        mark_check_passed
    elif [[ $undocumented_count -eq 0 ]]; then
        success "No undocumented compiled binary dependencies found"
        mark_check_passed
    fi

    return $has_error
}

check_license_headers() {
    local package=$1

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    info "Checking for ASF license headers in source files..."

    # Define file patterns to check for license headers
    # Including: Java, Shell scripts, Python, Go, JavaScript, TypeScript, C/C++, Scala, Groovy, etc.
    local -a file_patterns=(
        "*.java"      # Java files
        "*.sh"        # Shell scripts
        "*.py"        # Python files
        "*.go"        # Go files
        "*.js"        # JavaScript files
        "*.ts"        # TypeScript files
        "*.jsx"       # React JSX files
        "*.tsx"       # React TypeScript files
        "*.c"         # C files
        "*.h"         # C header files
        "*.cpp"       # C++ files
        "*.cc"        # C++ files
        "*.cxx"       # C++ files
        "*.hpp"       # C++ header files
        "*.scala"     # Scala files
        "*.groovy"    # Groovy files
        "*.gradle"    # Gradle build files
        "*.rs"        # Rust files
        "*.kt"        # Kotlin files
        "*.proto"     # Protocol buffer files
    )

    # Files to exclude from license header check
    local -a exclude_patterns=(
        "*.min.js"              # Minified JavaScript
        "*.min.css"             # Minified CSS
        "*node_modules*"        # Node.js dependencies
        "*target*"              # Maven build output
        "*build*"               # Build directories
        "*.pb.go"               # Generated protobuf files
        "*generated*"           # Generated code
        "*third_party*"         # Third party code
        "*vendor*"              # Vendor dependencies
    )

    local files_without_license=()
    local total_checked=0
    local excluded_count=0

    # Build find command with all patterns
    local find_cmd="find . -type f \\("
    local first=1
    for pattern in "${file_patterns[@]}"; do
        if [[ $first -eq 1 ]]; then
            find_cmd="$find_cmd -name \"$pattern\""
            first=0
        else
            find_cmd="$find_cmd -o -name \"$pattern\""
        fi
    done
    find_cmd="$find_cmd \\) 2>/dev/null"

    # Check each source file for ASF license header
    local documented_count=0
    while IFS= read -r source_file; do
        # Skip if file matches exclude patterns
        local should_exclude=0
        for exclude_pattern in "${exclude_patterns[@]}"; do
            # shellcheck disable=SC2053 # intentional exclusion glob
            if [[ "$source_file" == $exclude_pattern ]]; then
                should_exclude=1
                excluded_count=$((excluded_count + 1))
                break
            fi
        done

        if [[ $should_exclude -eq 1 ]]; then
            continue
        fi

        total_checked=$((total_checked + 1))

        # Check first 30 lines for Apache license header
        # Looking for the standard ASF license header text
        if ! head -n 30 "$source_file" | grep -q "Licensed to the Apache Software Foundation"; then
            # No ASF header found - check if it's documented in LICENSE file as third-party code
            local file_name
            file_name=$(basename "$source_file")
            local file_path_relative=${source_file#./}

            # Check if file name or path is mentioned in LICENSE file
            if [[ -f "LICENSE" ]] && (grep -q "$file_name" LICENSE 2>/dev/null || grep -q "$file_path_relative" LICENSE 2>/dev/null); then
                # File is documented in LICENSE as third-party code - this is allowed
                documented_count=$((documented_count + 1))
            else
                # Not documented - this is an error
                files_without_license+=("$source_file")
            fi
        fi
    done < <(eval "$find_cmd")

    # Report results
    info "Checked $total_checked source file(s) for ASF license headers (excluded $excluded_count generated/vendored files)"

    if [[ $documented_count -gt 0 ]]; then
        info "Found $documented_count source file(s) documented in LICENSE as third-party code (allowed)"
    fi

    if [[ ${#files_without_license[@]} -gt 0 ]]; then
        collect_error "Found ${#files_without_license[@]} source file(s) without ASF license headers:"

        # Show first 20 files without headers (to avoid overwhelming output)
        local show_count=${#files_without_license[@]}
        if [[ $show_count -gt 20 ]]; then
            show_count=20
        fi

        for ((i=0; i<show_count; i++)); do
            echo "    ${files_without_license[$i]}"
        done

        if [[ ${#files_without_license[@]} -gt 20 ]]; then
            echo "    ... and $((${#files_without_license[@]} - 20)) more files"
        fi

        echo ""
        collect_error "All source files must include the Apache License header or be documented in LICENSE file"
        collect_error "You can use 'mvn apache-rat:check' for detailed license header analysis"
        return 1
    else
        success "All $total_checked source file(s) have ASF license headers or are documented in LICENSE"
        mark_check_passed
        return 0
    fi
}

check_version_consistency() {
    local package=$1
    local expected_version=$2

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    # Skip version check for Python projects (hugegraph-ai)
    if [[ "$package" =~ 'hugegraph-ai' ]]; then
        info "Skipping version check for Python project: $package"
        mark_check_passed
        return 0
    fi

    info "Checking version consistency (revision property)..."

    # Find the parent/root pom.xml that defines the revision property
    local root_pom=""
    local revision_value=""

    # Look for pom.xml files that define the revision property
    while IFS= read -r pom_file; do
        if grep -q "<revision>" "$pom_file" 2>/dev/null; then
            # Extract the revision value
            revision_value=$(grep "<revision>" "$pom_file" | head -1 | sed 's/.*<revision>\(.*\)<\/revision>.*/\1/')
            root_pom="$pom_file"
            break
        fi
    done < <(find . -name "pom.xml" -type f 2>/dev/null)

    if [[ -z "$root_pom" ]]; then
        collect_error "No <revision> property found in source package"
        return 1
    fi

    info "Found revision property in $root_pom: <revision>$revision_value</revision>"

    # Check if revision matches expected version
    if [[ "$revision_value" != "$expected_version" ]]; then
        collect_error "Version mismatch: <revision>$revision_value</revision> in $root_pom (expected: $expected_version)"
        return 1
    fi

    success "Version consistency check passed: revision=$revision_value"
    mark_check_passed
    return 0
}

check_notice_year() {
    local package=$1

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [[ ! -f "NOTICE" ]]; then
        return 0  # Already checked in check_required_files
    fi

    local current_year

    current_year=$(date +%Y)
    if ! grep -q "$current_year" NOTICE; then
        collect_warning "Package '$package': NOTICE file may not contain current year ($current_year). Please verify copyright dates."
    else
        mark_check_passed
    fi
}


check_java() {
    local actual
    actual=$(java -version 2>&1 | awk -F '"' '/version/ {print $2; exit}')
    [[ "$actual" == 17.* && "$JAVA_VERSION" == 17 ]] || {
        info "Java 17 required (requested $JAVA_VERSION, actual $actual)"; return 1;
    }
}

prepare_maven() {
    [[ "$STAGING_REPOSITORY" =~ ^https://repository\.apache\.org/content/(repositories/[A-Za-z0-9._-]+|groups/staging)/?$ ]] || {
        info 'Expected an Apache HTTPS staging repository URL'; return 1;
    }
    mkdir -p "$RUN_DIR/m2/server" "$RUN_DIR/m2/toolchain"
    cat > "$RUN_DIR/settings.xml" <<EOF
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0">
  <profiles><profile><id>release-validation</id><repositories>
    <repository><id>selected-staging</id><url>$STAGING_REPOSITORY</url>
      <releases><enabled>true</enabled><updatePolicy>always</updatePolicy><checksumPolicy>fail</checksumPolicy></releases>
      <snapshots><enabled>false</enabled></snapshots>
    </repository>
  </repositories></profile></profiles>
  <activeProfiles><activeProfile>release-validation</activeProfile></activeProfiles>
</settings>
EOF
    MAVEN_ARGS=(-B -ntp -s "$RUN_DIR/settings.xml" -Papache-release -DskipTests -Dgpg.skip=true)
    if [[ -n "$SDK_REPOSITORY" ]]; then
        [[ $SOURCE_PREVALIDATION -eq 1 && -d "$SDK_REPOSITORY/org/apache/hugegraph" ]] || {
            info '--sdk-repository requires source-prevalidation and a built SDK repository'; return 1;
        }
        mkdir -p "$RUN_DIR/m2/toolchain/org/apache"
        cp -R "$SDK_REPOSITORY/org/apache/hugegraph" "$RUN_DIR/m2/toolchain/org/apache/"
        info "SDK origin: same-source repository $SDK_REPOSITORY (NOT remote staging)"
    else info "SDK origin: remote Maven resolution using $STAGING_REPOSITORY"; fi
}

extract_package() {
    local archive=$1 destination=$2
    # Validate archive paths and its single, expected root before extraction.
    python3 "$SCRIPT_DIR/release-smoke.py" extract "$archive" "$destination"
}

validate_package() {
    local archive=$1 kind=$2 destination=$3
    local name root before
    name=$(basename "$archive")
    root="$destination/${name%.tar.gz}"
    CURRENT_PACKAGE=$name
    extract_package "$archive" "$destination"
    pushd "$root" >/dev/null
    before=${#VALIDATION_ERRORS[@]}
    check_package_name "$name" || true
    check_required_files "$name" || true
    check_empty_files_and_dirs "$name" || true
    if [[ "$kind" == source ]]; then
        check_license_categories "$name" LICENSE NOTICE || true
        check_file_sizes "$name" "$MAX_FILE_SIZE" || true
        check_binary_files "$name" || true
        check_license_headers "$name" || true
        check_version_consistency "$name" "$RELEASE_VERSION" || true
        check_notice_year "$name" || true
    else
        [[ -d licenses ]] || collect_error 'Missing licenses directory'
        check_binary_licenses "$name"
    fi
    popd >/dev/null
    [[ ${#VALIDATION_ERRORS[@]} -eq $before ]]
}

require_packages() {
    PACKAGES=("$DIST_DIR/apache-hugegraph-$RELEASE_VERSION-src.tar.gz"
              "$DIST_DIR/apache-hugegraph-toolchain-$RELEASE_VERSION-src.tar.gz"
              "$DIST_DIR/apache-hugegraph-$RELEASE_VERSION.tar.gz"
              "$DIST_DIR/apache-hugegraph-toolchain-$RELEASE_VERSION.tar.gz")
    local archive component
    for archive in "${PACKAGES[@]}"; do
        [[ -f "$archive" ]] || { info "Missing required package: $archive"; return 1; }
    done
    # Keep the four core positions stable; other components ship source only.
    for component in ai computer; do
        archive="$DIST_DIR/apache-hugegraph-$component-$RELEASE_VERSION-src.tar.gz"
        if [[ -f "$archive" ]]; then PACKAGES+=("$archive"); fi
    done
    local candidates=("$DIST_DIR"/*.tar.gz)
    [[ ${#candidates[@]} -eq ${#PACKAGES[@]} ]] || {
        info 'Unexpected archive: only Server/Toolchain packages and AI/Computer sources are supported'; return 1;
    }
}


select_signer() {
    mkdir -m 700 "$RUN_DIR/signer"
    gpg --homedir "$RUN_DIR/gnupg" --batch --export -- "$GPG_USER" > "$RUN_DIR/signer.pgp"
    [[ -s "$RUN_DIR/signer.pgp" ]] || { info "Selected release signer not found: $GPG_USER"; return 1; }
    gpg --homedir "$RUN_DIR/signer" --batch --import "$RUN_DIR/signer.pgp"
}


check_signature_status() {
    if grep -Eq '^\[GNUPG:\] (REVKEYSIG|EXPKEYSIG|EXPSIG)( |$)' "$1"; then
        info "Expired or revoked release signature: $1; the release manager must review/update the candidate"; return 1
    fi
    grep -q '^\[GNUPG:\] VALIDSIG ' "$1" || { info "Missing VALIDSIG: $1"; return 1; }
}

verify_integrity() {
    local archive name status_file
    for archive in "${PACKAGES[@]}"; do
        name=$(basename "$archive")
        CURRENT_PACKAGE=$name
        [[ -f "$archive.sha512" ]] || { info "Missing SHA512: $name"; return 1; }
        python3 "$SCRIPT_DIR/release-smoke.py" checksum "$archive"
        if [[ $SOURCE_PREVALIDATION -eq 0 ]]; then
            [[ -f "$archive.asc" ]] || { info "Missing signature: $name"; return 1; }
            # Check process status, not localized human-readable 'Good signature'.
            mkdir -p "$RUN_DIR/logs/signatures"
            status_file="$RUN_DIR/logs/signatures/$name.status"
            gpg --homedir "$RUN_DIR/signer" --batch --status-fd 1 --verify -- "$archive.asc" "$archive" > "$status_file" || return $?
            check_signature_status "$status_file" || return $?
        fi
    done
}

unique_directory() {
    local base=$1 pattern=$2
    local matches=()
    while IFS= read -r path; do matches+=("$path"); done < <(find "$base" -maxdepth 4 -type d -name "$pattern")
    [[ ${#matches[@]} -eq 1 ]] || { info "Expected one $pattern under $base; found ${#matches[@]}" >&2; return 1; }
    printf '%s\n' "${matches[0]}"
}



start_server() {
    local server=$1
    (cd "$server" && printf '%s\n' release-smoke | bin/init-store.sh) || return $?
    SERVER_DIR=$server
    (cd "$server" && bin/start-hugegraph.sh -m false)
}

stop_services() {
    local failed=0
    if [[ -n "$HUBBLE_DIR" ]]; then
        if (cd "$HUBBLE_DIR" && bin/stop-hubble.sh) &&
           python3 "$SCRIPT_DIR/release-smoke.py" stopped 8088; then
            HUBBLE_DIR=''
        else
            info "ERROR: Hubble shutdown failed: $HUBBLE_DIR"
            failed=1
        fi
    fi
    if [[ -n "$SERVER_DIR" ]]; then
        if (cd "$SERVER_DIR" && bin/stop-hugegraph.sh -m false) &&
           python3 "$SCRIPT_DIR/release-smoke.py" stopped 8080; then
            SERVER_DIR=''
        else
            info "ERROR: Server shutdown failed: $SERVER_DIR"
            failed=1
        fi
    fi
    return "$failed"
}

run_packages() {
    local server=$1 toolchain=$2 label=$3 loader tools hubble classpath
    CURRENT_STEP="$label runtime"
    CURRENT_PACKAGE='Server/Toolchain'
    info "Running $label packages"
    python3 "$SCRIPT_DIR/release-smoke.py" embedded-versions "$RELEASE_VERSION" "$server" "$toolchain"
    python3 "$SCRIPT_DIR/release-smoke.py" ports
    # Only modify disposable extraction directories. Enable standalone authentication
    # so Client, Loader, Tools and Hubble exercise the same authenticated server.
    python3 "$SCRIPT_DIR/release-smoke.py" properties "$server/conf/rest-server.properties" \
        auth.authenticator=org.apache.hugegraph.auth.StandardAuthenticator auth.graph_store=hugegraph
    start_server "$server"
    python3 "$SCRIPT_DIR/release-smoke.py" server
    loader=$(unique_directory "$toolchain" "apache-hugegraph-loader-$RELEASE_VERSION")
    tools=$(unique_directory "$toolchain" "apache-hugegraph-tools-$RELEASE_VERSION")
    hubble=$(unique_directory "$toolchain" "apache-hugegraph-hubble-$RELEASE_VERSION")
    for module in loader tools hubble; do
        local distribution
        distribution=$(unique_directory "$toolchain" "apache-hugegraph-$module-$RELEASE_VERSION")
        python3 "$SDK_VERIFIER" "$RUN_DIR/m2/toolchain" --mode release --version "$RELEASE_VERSION" \
            --distribution "$distribution" --module "$module"
    done
    classpath="$loader/lib/*"
    mkdir -p "$RUN_DIR/client-$label"
    javac -cp "$classpath" -d "$RUN_DIR/client-$label" "$SCRIPT_DIR/ReleaseClientSmoke.java"
    java -cp "$RUN_DIR/client-$label:$classpath" ReleaseClientSmoke
    (cd "$loader" && bin/hugegraph-loader.sh -f example/file/struct.json -s example/file/schema.groovy \
        -g hugegraph --username admin --password release-smoke)
    python3 "$SCRIPT_DIR/release-smoke.py" loader
    (cd "$tools" && bin/hugegraph --user admin --password release-smoke gremlin-execute --script 'g.V().count()' && \
        bin/hugegraph --user admin --password release-smoke task-list && \
        bin/hugegraph --user admin --password release-smoke backup -t all --directory "$RUN_DIR/backup-$label")
    [[ -n $(find "$RUN_DIR/backup-$label" -type f -size +0c -print -quit) ]] || {
        info 'Tools backup produced no nonempty file'; return 1;
    }
    python3 "$SCRIPT_DIR/release-smoke.py" properties "$hubble/conf/hugegraph-hubble.properties" \
        pd.enabled=false server.direct_url=http://127.0.0.1:8080
    HUBBLE_DIR=$hubble
    (cd "$hubble" && bin/start-hubble.sh)
    python3 "$SCRIPT_DIR/release-smoke.py" hubble
    stop_services
    success "$label Server, Client, ordinary Loader, Tools and Hubble"
}

main() {
    local work_parent=${RELEASE_WORK_DIR:-"$SCRIPT_DIR/validation"}
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h) usage; return;;
            --version|-v) info 'Release validation 3.0'; return;;
            --non-interactive) shift;;
            --source-prevalidation) SOURCE_PREVALIDATION=1; shift;;
            --svn-path) SVN_PATH=${2:?Missing SVN path}; shift 2;;
            --staging-repository) STAGING_REPOSITORY=${2:?Missing staging URL}; shift 2;;
            --sdk-repository) SDK_REPOSITORY=${2:?Missing SDK repository}; shift 2;;
            --work-dir) work_parent=${2:?Missing work directory}; shift 2;;
            --*) info "Unknown option: $1"; return 1;;
            *) break;;
        esac
    done
    RELEASE_VERSION=${1:?Missing release version}
    GPG_USER=${2:?Missing release signer}
    local local_path=${3:-}
    JAVA_VERSION=${4:-17}
    [[ $# -le 4 && "$RELEASE_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { usage; return 1; }
    SVN_PATH=${SVN_PATH:-$RELEASE_VERSION}
    [[ "$SVN_PATH" =~ ^[A-Za-z0-9._/-]+$ && "$SVN_PATH" != /* && "$SVN_PATH" != *..* ]] || {
        info 'Invalid relative SVN candidate path'; return 1;
    }
    for cmd in java javac mvn python3 gpg shasum tar curl find perl; do command -v "$cmd" >/dev/null; done
    check_java
    mkdir -p "$work_parent"
    work_parent=$(cd "$work_parent" && pwd)
    RUN_DIR=$(mktemp -d "$work_parent/$RELEASE_VERSION.XXXXXX")
    exec > >(tee "$RUN_DIR/validation.log") 2>&1
    info "Release $RELEASE_VERSION; Java $JAVA_VERSION; evidence $RUN_DIR"
    if [[ -n "$local_path" ]]; then
        local_path=$(cd "$local_path" && pwd)
        DIST_DIR=$local_path
    else
        [[ $SOURCE_PREVALIDATION -eq 0 ]] || { info 'Source prevalidation requires a local package directory'; return 1; }
        command -v svn >/dev/null
        DIST_DIR="$RUN_DIR/download"
        svn export "$SVN_URL_PREFIX/$SVN_PATH" "$DIST_DIR"
    fi
    CURRENT_STEP='package selection'
    require_packages
    CURRENT_STEP='integrity'
    # Package set is exact; reject legacy/incubating names before any build.
    local archive
    for archive in "$DIST_DIR"/*.tar.gz; do check_package_name "$(basename "$archive")"; done
    if [[ $SOURCE_PREVALIDATION -eq 0 ]]; then
        mkdir -m 700 "$RUN_DIR/gnupg"
        curl -fsSL "$KEYS_URL" -o "$RUN_DIR/KEYS"
        gpg --homedir "$RUN_DIR/gnupg" --batch --import "$RUN_DIR/KEYS"
        select_signer
    else warn 'Unsigned source prevalidation; RC signature/download checks are excluded'; fi
    verify_integrity
    prepare_maven
    CURRENT_STEP='source contents'
    validate_package "${PACKAGES[0]}" source "$RUN_DIR/source/server"
    validate_package "${PACKAGES[1]}" source "$RUN_DIR/source/toolchain"
    for archive in "${PACKAGES[@]:4}"; do
        validate_package "$archive" source "$RUN_DIR/source/extra"
    done
    local server_source="$RUN_DIR/source/server/apache-hugegraph-$RELEASE_VERSION-src"
    local toolchain_source="$RUN_DIR/source/toolchain/apache-hugegraph-toolchain-$RELEASE_VERSION-src"
    CURRENT_STEP='source build'
    CURRENT_PACKAGE='Server'
    (cd "$server_source" && mvn clean "${MAVEN_ARGS[@]}" -Dmaven.repo.local="$RUN_DIR/m2/server" && \
        mvn package "${MAVEN_ARGS[@]}" -Dmaven.repo.local="$RUN_DIR/m2/server")
    CURRENT_PACKAGE='Toolchain'
    (cd "$toolchain_source" && mvn clean "${MAVEN_ARGS[@]}" -Dmaven.repo.local="$RUN_DIR/m2/toolchain" && \
        mvn install "${MAVEN_ARGS[@]}" -Dmaven.repo.local="$RUN_DIR/m2/toolchain")
    SDK_VERIFIER="$toolchain_source/.github/scripts/verify_candidate_image_sdk.py"
    [[ -f "$SDK_VERIFIER" ]] || { info 'Toolchain source archive is missing the release SDK verifier'; return 1; }
    if [[ -z "$SDK_REPOSITORY" ]]; then
        python3 "$SCRIPT_DIR/release-smoke.py" staging-origin "$RUN_DIR/m2/toolchain" "$RELEASE_VERSION" \
            "$toolchain_source/apache-hugegraph-toolchain-$RELEASE_VERSION" "$STAGING_REPOSITORY"
    fi
    local computer_source="$RUN_DIR/source/extra/apache-hugegraph-computer-$RELEASE_VERSION-src"
    if [[ -d "$computer_source" ]]; then
        CURRENT_PACKAGE='Computer'
        (cd "$computer_source/computer" && mvn clean package "${MAVEN_ARGS[@]}" \
            -Dmaven.repo.local="$RUN_DIR/m2/computer")
        success 'Computer source build (product runtime tests are not included)'
    fi
    local server toolchain
    extract_package "$server_source/target/apache-hugegraph-$RELEASE_VERSION.tar.gz" "$RUN_DIR/compiled/server"
    extract_package "$toolchain_source/target/apache-hugegraph-toolchain-$RELEASE_VERSION.tar.gz" "$RUN_DIR/compiled/toolchain"
    server=$(unique_directory "$RUN_DIR/compiled/server" "apache-hugegraph-server-$RELEASE_VERSION")
    toolchain="$RUN_DIR/compiled/toolchain/apache-hugegraph-toolchain-$RELEASE_VERSION"
    run_packages "$server" "$toolchain" source
    CURRENT_STEP='binary contents'
    validate_package "${PACKAGES[2]}" binary "$RUN_DIR/binary/server"
    validate_package "${PACKAGES[3]}" binary "$RUN_DIR/binary/toolchain"
    server=$(unique_directory "$RUN_DIR/binary/server" "apache-hugegraph-server-$RELEASE_VERSION")
    toolchain="$RUN_DIR/binary/toolchain/apache-hugegraph-toolchain-$RELEASE_VERSION"
    run_packages "$server" "$toolchain" binary
    VALIDATION_COMPLETE=1
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then main "$@"; fi
