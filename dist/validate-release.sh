#!/usr/bin/env bash
################################################################################
# Apache HugeGraph Release Validation Script
################################################################################
#
# This script validates Apache HugeGraph release packages:
#   1. Check package integrity (SHA512, GPG signatures)
#   2. Validate package names and required files
#   3. Check license compliance (ASF categories)
#   4. Validate package contents
#   5. Compile source packages
#   6. Run server and toolchain tests
#
# Usage:
#   validate-release.sh <version> <user> [local-path] [java-version]
#   validate-release.sh --help
#
# Arguments:
#   version       Release version (e.g., 1.7.0)
#   user          Apache username for GPG key trust
#   local-path    (Optional) Local directory containing release files
#                 If omitted, downloads from Apache SVN
#   java-version  (Optional) Java version to validate (default: 11)
#
# Examples:
#   # Validate from Apache SVN
#   ./validate-release.sh 1.7.0 pengjunzhi
#
#   # Validate from local directory
#   ./validate-release.sh 1.7.0 pengjunzhi /path/to/dist
#
#   # Specify Java version
#   ./validate-release.sh 1.7.0 pengjunzhi /path/to/dist 11
#
################################################################################

# Strict mode - but don't exit on error yet (we collect all errors)
set -o pipefail
set -o nounset

################################################################################
# Configuration Constants
################################################################################

readonly SCRIPT_VERSION="2.2.0"
readonly SCRIPT_NAME=$(basename "$0")

# URLs
readonly SVN_URL_PREFIX="https://dist.apache.org/repos/dist/dev/hugegraph"
readonly KEYS_URL="https://downloads.apache.org/hugegraph/KEYS"

# Validation Rules
readonly MAX_FILE_SIZE="800k"
readonly SERVER_START_DELAY=3
readonly SERVICE_HEALTH_TIMEOUT=30

# License Patterns (ASF Category X - Prohibited)
readonly CATEGORY_X="\bGPL|\bLGPL|Sleepycat License|BSD-4-Clause|\bBCL\b|JSR-275|Amazon Software License|\bRSAL\b|\bQPL\b|\bSSPL|\bCPOL|\bNPL1|Creative Commons Non-Commercial|JSON\.org"

# License Patterns (ASF Category B - Must be documented)
readonly CATEGORY_B="\bCDDL1|\bCPL|\bEPL|\bIPL|\bMPL|\bSPL|OSL-3.0|UnRAR License|Erlang Public License|\bOFL\b|Ubuntu Font License Version 1.0|IPA Font License Agreement v1.0|EPL2.0|CC-BY"

# Color Definitions
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

################################################################################
# Global Variables
################################################################################

# Script state
WORK_DIR=""
LOG_FILE=""
DIST_DIR=""
RELEASE_VERSION=""
USER=""
LOCAL_DIST_PATH=""
JAVA_VERSION=11
NON_INTERACTIVE=0

# Error tracking
declare -a VALIDATION_ERRORS=()
declare -a VALIDATION_WARNINGS=()
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
CURRENT_STEP=""
CURRENT_PACKAGE=""

# Service tracking for cleanup
SERVER_STARTED=0
HUBBLE_STARTED=0

# Script execution time tracking
SCRIPT_START_TIME=0
ENABLE_CLEANUP=0

################################################################################
# Helper Functions - Output & Logging
################################################################################

show_usage() {
    cat << EOF
Apache HugeGraph Release Validation Script v${SCRIPT_VERSION}

Usage: ${SCRIPT_NAME} <version> <user> [local-path] [java-version]
       ${SCRIPT_NAME} --help | -h
       ${SCRIPT_NAME} --version | -v

Validates Apache HugeGraph release packages including:
  - Package integrity (SHA512, GPG signatures)
  - License compliance (ASF categories)
  - Package contents and structure
  - Compilation and runtime testing

Arguments:
  version       Release version (e.g., 1.7.0)
  user          Apache username for GPG key trust
  local-path    (Optional) Local directory path containing release files
                If omitted, downloads from Apache SVN
  java-version  (Optional) Java version to validate (default: 11)

Options:
  --help, -h            Show this help message
  --version, -v         Show script version
  --non-interactive     Run without prompts (for CI/CD)

Examples:
  # Validate from Apache SVN (downloads files)
  ${SCRIPT_NAME} 1.7.0 pengjunzhi

  # Validate from local directory
  ${SCRIPT_NAME} 1.7.0 pengjunzhi /path/to/dist

  # Specify Java version
  ${SCRIPT_NAME} 1.7.0 pengjunzhi "" 11
  ${SCRIPT_NAME} 1.7.0 pengjunzhi /path/to/dist 11

  # Non-interactive mode for CI
  ${SCRIPT_NAME} --non-interactive 1.7.0 pengjunzhi

For more information, visit:
  https://github.com/apache/hugegraph-doc/tree/master/dist

EOF
}

log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}" | tee -a "${LOG_FILE:-/dev/null}"
}

info() {
    echo -e "$*"
    log "INFO" "$*"
}

success() {
    echo -e "${GREEN}✓ $*${NC}"
    log "SUCCESS" "$*"
}

warn() {
    echo -e "${YELLOW}⚠ $*${NC}" >&2
    log "WARN" "$*"
}

error() {
    echo -e "${RED}✗ $*${NC}" >&2
    log "ERROR" "$*"
}

print_step() {
    local step=$1
    local total=$2
    local description=$3
    CURRENT_STEP="Step $step: $description"
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Step [$step/$total]: $description${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    log "STEP" "[$step/$total] $description"
}

print_progress() {
    local current=$1
    local total=$2
    local item=$3
    echo -e "  [${current}/${total}] ${item}"
}

collect_error() {
    local error_msg="$1"
    local context=""

    # Build context string
    if [[ -n "$CURRENT_STEP" ]]; then
        context="[$CURRENT_STEP]"
    fi

    if [[ -n "$CURRENT_PACKAGE" ]]; then
        if [[ -n "$context" ]]; then
            context="$context [$CURRENT_PACKAGE]"
        else
            context="[$CURRENT_PACKAGE]"
        fi
    fi

    # Store error with context
    if [[ -n "$context" ]]; then
        VALIDATION_ERRORS+=("$context $error_msg")
    else
        VALIDATION_ERRORS+=("$error_msg")
    fi

    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    error "$error_msg"
}

collect_warning() {
    local warning_msg="$1"
    local context=""

    # Build context string
    if [[ -n "$CURRENT_STEP" ]]; then
        context="[$CURRENT_STEP]"
    fi

    if [[ -n "$CURRENT_PACKAGE" ]]; then
        if [[ -n "$context" ]]; then
            context="$context [$CURRENT_PACKAGE]"
        else
            context="[$CURRENT_PACKAGE]"
        fi
    fi

    # Store warning with context
    if [[ -n "$context" ]]; then
        VALIDATION_WARNINGS+=("$context $warning_msg")
    else
        VALIDATION_WARNINGS+=("$warning_msg")
    fi

    warn "$warning_msg"
}

mark_check_passed() {
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
}

mark_check_failed() {
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
}

################################################################################
# Helper Functions - System & Environment
################################################################################

setup_logging() {
    local log_dir="${WORK_DIR}/logs"
    mkdir -p "$log_dir"
    LOG_FILE="$log_dir/validate-${RELEASE_VERSION}-$(date +%Y%m%d-%H%M%S).log"
    ENABLE_CLEANUP=1

    info "Logging to: ${LOG_FILE}"
    log "INIT" "Starting validation for HugeGraph ${RELEASE_VERSION}"
    log "INIT" "User: ${USER}, Java: ${JAVA_VERSION}"
}

check_dependencies() {
    local missing_deps=()
    local required_commands=("svn" "gpg" "shasum" "mvn" "java" "wget" "tar" "curl" "awk" "grep" "find" "perl")

    info "Checking required dependencies..."

    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
            error "Missing: $cmd"
        else
            local version_info
            case "$cmd" in
                java)
                    version_info=$(java -version 2>&1 | head -n1 | cut -d'"' -f2)
                    ;;
                mvn)
                    version_info=$(mvn --version 2>&1 | head -n1 | awk '{print $3}')
                    ;;
                *)
                    version_info=$($cmd --version 2>&1 | head -n1 || echo "installed")
                    ;;
            esac
            success "$cmd: $version_info"
        fi
    done

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        error "Missing required dependencies: ${missing_deps[*]}"
        echo ""
        echo "Please install missing dependencies:"
        echo "  Ubuntu/Debian: sudo apt-get install ${missing_deps[*]}"
        echo "  macOS: brew install ${missing_deps[*]}"
        exit 1
    fi

    success "All dependencies are installed"
}

check_java_version() {
    local required_version=$1

    info "Checking Java version..."

    if ! command -v java &> /dev/null; then
        collect_error "Java is not installed or not in PATH"
        return 1
    fi

    local current_version=$(java -version 2>&1 | head -n 1 | awk -F '"' '{print $2}' | awk -F '.' '{print $1}')
    info "Current Java version: $current_version (Required: ${required_version})"

    if [[ "$current_version" != "$required_version" ]]; then
        collect_error "Java version mismatch! Current: Java $current_version, Required: Java ${required_version}"
        collect_error "Please switch to Java ${required_version} before running this script"
        return 1
    fi

    success "Java version check passed: Java $current_version"
    mark_check_passed
    return 0
}

find_package_dir() {
    local pattern=$1
    local base_dir=${2:-"${DIST_DIR}"}

    local found=$(find "$base_dir" -maxdepth 3 -type d -path "$pattern" 2>/dev/null | head -n1)

    if [[ -z "$found" ]]; then
        collect_error "Could not find directory matching pattern: $pattern"
        return 1
    fi

    echo "$found"
}

find_package_dir_silent() {
    local pattern=$1
    local base_dir=${2:-"${DIST_DIR}"}
    find "$base_dir" -maxdepth 3 -type d -path "$pattern" 2>/dev/null | head -n1
}

################################################################################
# Helper Functions - GPG & Signatures
################################################################################

import_and_trust_gpg_keys() {
    local user=$1

    info "Downloading KEYS file from ${KEYS_URL}..."
    if ! wget -q "${KEYS_URL}" -O KEYS; then
        collect_error "Failed to download KEYS file from ${KEYS_URL}"
        return 1
    fi
    success "KEYS file downloaded"

    info "Importing GPG keys..."
    local import_output=$(gpg --import KEYS 2>&1)
    local imported_count=$(echo "$import_output" | grep -c "imported" || echo "0")

    if [[ "$imported_count" == "0" ]]; then
        warn "No new keys imported (may already exist in keyring)"
    else
        success "Imported GPG keys"
    fi

    # Trust specific user key
    if ! gpg --list-keys "$user" &>/dev/null; then
        collect_error "User '$user' key not found in imported keys. Please verify the username."
        return 1
    fi

    info "Trusting GPG key for user: $user"
    echo -e "5\ny\n" | gpg --batch --command-fd 0 --edit-key "$user" trust 2>/dev/null
    success "Trusted key for $user"

    # Trust all imported keys
    info "Trusting all imported public keys..."
    local trusted=0
    for key in $(gpg --no-tty --list-keys --with-colons | awk -F: '/^pub/ {print $5}'); do
        echo -e "5\ny\n" | gpg --batch --command-fd 0 --edit-key "$key" trust 2>/dev/null
        trusted=$((trusted + 1))
    done
    success "Trusted $trusted GPG keys"

    mark_check_passed
    return 0
}

################################################################################
# Validation Functions - Package Checks
################################################################################

check_package_name() {
    local package=$1
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [[ "$package" != apache-hugegraph* ]]; then
        collect_error "Package name '$package' should start with 'apache-hugegraph'"
        return 1
    fi

    if [[ "$package" != *"${RELEASE_VERSION}"* ]]; then
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
    local files=$2
    local has_error=0

    # Check Category X (Prohibited)
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    local cat_x_matches=$(grep -r -E "$CATEGORY_X" $files 2>/dev/null)
    local cat_x_count=$(echo "$cat_x_matches" | grep -v '^$' | wc -l | tr -d ' ')

    if [[ $cat_x_count -ne 0 ]]; then
        # Build detailed error message with license information
        local error_details="Package '$package' contains $cat_x_count prohibited ASF Category X license(s):"

        # Extract and format each violation
        while IFS= read -r match_line; do
            if [[ -n "$match_line" ]]; then
                # Parse file:content format
                local file_name=$(echo "$match_line" | cut -d':' -f1)
                local license_info=$(echo "$match_line" | cut -d':' -f2-)

                # Try to extract specific license name
                local license_name=$(echo "$license_info" | grep -oE "$CATEGORY_X" | head -n1)

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
    local cat_b_count=$(grep -r -E "$CATEGORY_B" $files 2>/dev/null | wc -l | tr -d ' ')
    if [[ $cat_b_count -ne 0 ]]; then
        collect_warning "Package '$package' contains $cat_b_count ASF Category B license(s) - please verify documentation"
    else
        mark_check_passed
    fi

    return $has_error
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
        collect_error "Package '$package' contains ${#large_files[@]} file(s) larger than ${max_size}:"
        for file in "${large_files[@]}"; do
            local size=$(du -h "$file" | awk '{print $1}')
            echo "    $file ($size)"
        done
        has_error=1
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

    # Find binary files using perl
    while IFS= read -r binary_file; do
        binary_count=$((binary_count + 1))
        local file_name=$(basename "$binary_file")

        # Check if documented in LICENSE
        if grep -q "$file_name" LICENSE 2>/dev/null; then
            success "Binary file '$binary_file' is documented in LICENSE"
        else
            collect_error "Undocumented binary file: $binary_file"
            undocumented_count=$((undocumented_count + 1))
            has_error=1
        fi
    done < <(find . -type f 2>/dev/null | perl -lne 'print if -B $_')

    if [[ $binary_count -eq 0 ]]; then
        success "No binary files found"
        mark_check_passed
    elif [[ $undocumented_count -eq 0 ]]; then
        success "All $binary_count binary file(s) are documented"
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
            local file_name=$(basename "$source_file")
            local file_path_relative=$(echo "$source_file" | sed 's|^\./||')

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
        collect_warning "No <revision> property found in pom.xml files - skipping version check"
        mark_check_passed
        return 0
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

    local current_year=$(date +%Y)
    if ! grep -q "$current_year" NOTICE; then
        collect_warning "Package '$package': NOTICE file may not contain current year ($current_year). Please verify copyright dates."
    else
        mark_check_passed
    fi
}

################################################################################
# Main Validation Functions
################################################################################

validate_source_package() {
    local package_file=$1
    local package_dir=$(basename "$package_file" .tar.gz)

    # Set current package context for error reporting
    CURRENT_PACKAGE="$package_file"

    info "Validating source package: $package_file"

    # Extract package
    rm -rf "$package_dir"
    tar -xzf "$package_file"

    if [[ ! -d "$package_dir" ]]; then
        collect_error "Failed to extract package: $package_file"
        CURRENT_PACKAGE=""
        return 1
    fi

    pushd "$package_dir" > /dev/null

    # Run all checks
    check_package_name "$package_file"
    check_required_files "$package_file"
    check_license_categories "$package_file" "LICENSE NOTICE"
    check_empty_files_and_dirs "$package_file"
    check_file_sizes "$package_file" "$MAX_FILE_SIZE"
    check_binary_files "$package_file"
    check_license_headers "$package_file"
    check_version_consistency "$package_file" "$RELEASE_VERSION"
    check_notice_year "$package_file"

    # Compile check
    info "Compiling source package: $package_file"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [[ "$package_file" =~ 'hugegraph-ai' ]]; then
        warn "Skipping compilation for AI module (not required)"
        mark_check_passed
    elif [[ "$package_file" =~ "hugegraph-computer" ]]; then
        if cd computer 2>/dev/null && mvn clean package -DskipTests -Dcheckstyle.skip=true -ntp -e; then
            success "Compilation successful: $package_file"
            mark_check_passed
        else
            collect_error "Compilation failed: $package_file"
        fi
        cd ..
    else
        if mvn clean package -DskipTests -Dcheckstyle.skip=true -ntp -e; then
            success "Compilation successful: $package_file"
            mark_check_passed
        else
            collect_error "Compilation failed: $package_file"
        fi
    fi

    popd > /dev/null

    # Clear package context
    CURRENT_PACKAGE=""

    info "Finished validating source package: $package_file"
}

validate_binary_package() {
    local package_file=$1
    local package_dir=$(basename "$package_file" .tar.gz)

    # Set current package context for error reporting
    CURRENT_PACKAGE="$package_file"

    info "Validating binary package: $package_file"

    # Extract package
    rm -rf "$package_dir"
    tar -xzf "$package_file"

    if [[ ! -d "$package_dir" ]]; then
        collect_error "Failed to extract package: $package_file"
        CURRENT_PACKAGE=""
        return 1
    fi

    pushd "$package_dir" > /dev/null

    # Run checks
    check_package_name "$package_file"
    check_required_files "$package_file"

    # Binary packages should have licenses directory
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [[ ! -d "licenses" ]]; then
        collect_error "Package '$package_file' missing licenses directory"
    else
        mark_check_passed
    fi

    check_license_categories "$package_file" "LICENSE NOTICE licenses"
    check_empty_files_and_dirs "$package_file"

    popd > /dev/null

    # Clear package context
    CURRENT_PACKAGE=""

    info "Finished validating binary package: $package_file"
}

################################################################################
# Cleanup Function
################################################################################

cleanup() {
    local exit_code=$?

    if [[ $ENABLE_CLEANUP -eq 0 ]]; then
        return "$exit_code"
    fi

    log "CLEANUP" "Starting cleanup (exit code: $exit_code)"

    # Stop running services
    if [[ $SERVER_STARTED -eq 1 ]]; then
        info "Stopping HugeGraph server..."
        local server_dir=$(find_package_dir_silent "*hugegraph*${RELEASE_VERSION}*src/hugegraph-server/*hugegraph-server*${RELEASE_VERSION}*")
        if [[ -n "$server_dir" ]] && [[ -d "$server_dir" ]]; then
            pushd "$server_dir" > /dev/null 2>&1
            bin/stop-hugegraph.sh || true
            popd > /dev/null 2>&1
        fi
    fi

    if [[ $HUBBLE_STARTED -eq 1 ]]; then
        info "Stopping Hubble..."
        # Hubble stop is handled in the test flow
    fi

    # Show final report
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "                    VALIDATION SUMMARY                        "
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Calculate execution time
    local script_end_time=$(date +%s)
    local execution_seconds=$((script_end_time - SCRIPT_START_TIME))
    local execution_minutes=$((execution_seconds / 60))
    local execution_seconds_remainder=$((execution_seconds % 60))

    echo "Execution Time: ${execution_minutes}m ${execution_seconds_remainder}s"
    echo "Total Checks:   $TOTAL_CHECKS"
    echo -e "${GREEN}Passed:         $PASSED_CHECKS${NC}"
    echo -e "${RED}Failed:         $FAILED_CHECKS${NC}"
    echo -e "${YELLOW}Warnings:       ${#VALIDATION_WARNINGS[@]}${NC}"
    echo ""

    if [[ ${#VALIDATION_ERRORS[@]} -gt 0 ]]; then
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${RED}                        ERRORS                                ${NC}"
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        local err_index=1
        for err in "${VALIDATION_ERRORS[@]}"; do
            echo -e "${RED}[E${err_index}] $err${NC}"
            echo ""  # Blank line between errors for readability
            err_index=$((err_index + 1))
        done
    fi

    if [[ ${#VALIDATION_WARNINGS[@]} -gt 0 ]]; then
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}                       WARNINGS                              ${NC}"
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        local warn_index=1
        for warn in "${VALIDATION_WARNINGS[@]}"; do
            echo -e "${YELLOW}[W${warn_index}] $warn${NC}"
            echo ""  # Blank line between warnings for readability
            warn_index=$((warn_index + 1))
        done
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    if [[ ${#VALIDATION_ERRORS[@]} -gt 0 ]]; then
        echo -e "${RED}VALIDATION FAILED${NC}"
        echo -e "Log file: ${LOG_FILE}"
        echo ""
        exit 1
    else
        echo -e "${GREEN}✓ VALIDATION PASSED${NC}"
        echo -e "Log file: ${LOG_FILE}"
        echo ""
        echo "Please review the validation results and provide feedback in the"
        echo "release voting thread on the mailing list."
        echo ""
        exit 0
    fi
}

# Set trap for cleanup
trap cleanup EXIT
trap 'echo -e "${RED}Script interrupted${NC}"; exit 130' INT TERM

################################################################################
# Main Execution
################################################################################

main() {
    # Record script start time
    SCRIPT_START_TIME=$(date +%s)

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_usage
                exit 0
                ;;
            --version|-v)
                echo "Apache HugeGraph Release Validation Script v${SCRIPT_VERSION}"
                exit 0
                ;;
            --non-interactive)
                NON_INTERACTIVE=1
                shift
                ;;
            *)
                break
                ;;
        esac
    done

    # Parse positional arguments
    RELEASE_VERSION=${1:-}
    USER=${2:-}
    LOCAL_DIST_PATH=${3:-}
    JAVA_VERSION=${4:-11}

    # Validate required arguments
    if [[ -z "$RELEASE_VERSION" ]]; then
        error "Missing required argument: version"
        echo ""
        show_usage
        exit 1
    fi

    if [[ -z "$USER" ]]; then
        error "Missing required argument: user"
        echo ""
        show_usage
        exit 1
    fi

    # Initialize
    WORK_DIR=$(cd "$(dirname "$0")" && pwd)
    cd "${WORK_DIR}"

    setup_logging

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "    Apache HugeGraph Release Validation v${SCRIPT_VERSION}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "  Version:   ${RELEASE_VERSION}"
    echo "  User:      ${USER}"
    echo "  Java:      ${JAVA_VERSION}"
    echo "  Mode:      $([ -n "${LOCAL_DIST_PATH}" ] && echo "Local (${LOCAL_DIST_PATH})" || echo "SVN Download")"
    echo "  Log:       ${LOG_FILE}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    ####################################################
    # Step 1: Check Dependencies
    ####################################################
    print_step 1 9 "Check Dependencies"
    check_dependencies
    check_java_version "$JAVA_VERSION"

    ####################################################
    # Step 2: Prepare Release Files
    ####################################################
    print_step 2 9 "Prepare Release Files"

    if [[ -n "${LOCAL_DIST_PATH}" ]]; then
        # Use local directory
        DIST_DIR="${LOCAL_DIST_PATH}"
        info "Using local directory: ${DIST_DIR}"

        if [[ ! -d "${DIST_DIR}" ]]; then
            collect_error "Directory ${DIST_DIR} does not exist"
            exit 1
        fi

        info "Contents of ${DIST_DIR}:"
        ls -lh "${DIST_DIR}"
    else
        # Download from SVN
        if ! svn ls "${SVN_URL_PREFIX}/${RELEASE_VERSION}" &>/dev/null; then
            collect_error "Release version '${RELEASE_VERSION}' not found in TLP dist path: ${SVN_URL_PREFIX}/${RELEASE_VERSION}"
            exit 1
        fi
        DIST_DIR="${WORK_DIR}/dist/${RELEASE_VERSION}"
        info "Downloading from SVN to: ${DIST_DIR}"

        rm -rf "${DIST_DIR}"
        mkdir -p "${DIST_DIR}"

        if ! svn co "${SVN_URL_PREFIX}/${RELEASE_VERSION}" "${DIST_DIR}"; then
            collect_error "Failed to download from SVN: ${SVN_URL_PREFIX}/${RELEASE_VERSION}"
            exit 1
        fi

        success "Downloaded release files from SVN"
    fi

    cd "${DIST_DIR}"

    ####################################################
    # Step 3: Import GPG Keys
    ####################################################
    print_step 3 9 "Import & Trust GPG Keys"
    import_and_trust_gpg_keys "$USER"

    ####################################################
    # Step 4: Check SHA512 & GPG Signatures
    ####################################################
    print_step 4 9 "Verify SHA512 & GPG Signatures"

    local package_count=0
    local packages=()
    for pkg in *.tar.gz; do
        if [[ -f "$pkg" ]]; then
            packages+=("$pkg")
            package_count=$((package_count + 1))
        fi
    done

    local current=0
    for pkg in "${packages[@]}"; do
        current=$((current + 1))
        print_progress $current $package_count "$pkg"

        # Check SHA512
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        if shasum -a 512 --check "${pkg}.sha512"; then
            success "SHA512 verified: $pkg"
            mark_check_passed
        else
            collect_error "SHA512 verification failed: $pkg"
        fi

        # Check GPG signature
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        if gpg --verify "${pkg}.asc" "$pkg" 2>&1 | grep -q "Good signature"; then
            success "GPG signature verified: $pkg"
            mark_check_passed
        else
            collect_error "GPG signature verification failed: $pkg"
        fi
    done

    ####################################################
    # Step 5: Validate Source Packages
    ####################################################
    print_step 5 9 "Validate Source Packages"

    local src_packages=()
    for pkg in *-src.tar.gz; do
        if [[ -f "$pkg" ]]; then
            src_packages+=("$pkg")
        fi
    done

    info "Found ${#src_packages[@]} source package(s)"

    for src_pkg in "${src_packages[@]}"; do
        validate_source_package "$src_pkg"
    done

    ####################################################
    # Step 6: Run Compiled Packages (Server)
    ####################################################
    print_step 6 9 "Test Compiled Server Package"

    local server_dir=$(find_package_dir "*hugegraph*${RELEASE_VERSION}*src/hugegraph-server/*hugegraph-server*${RELEASE_VERSION}*")
    if [[ -n "$server_dir" ]]; then
        info "Starting HugeGraph server from: $server_dir"
        pushd "$server_dir" > /dev/null

        if bin/init-store.sh; then
            success "Store initialized"
        else
            collect_error "Failed to initialize store"
        fi

        sleep $SERVER_START_DELAY

        if bin/start-hugegraph.sh; then
            success "Server started"
            SERVER_STARTED=1
        else
            collect_error "Failed to start server"
        fi

        popd > /dev/null
    else
        collect_error "Could not find compiled server directory"
    fi

    ####################################################
    # Step 7: Test Toolchain (Loader, Tool, Hubble)
    ####################################################
    print_step 7 9 "Test Compiled Toolchain Packages"

    local toolchain_src=$(find_package_dir "*toolchain*src")
    if [[ -n "$toolchain_src" ]]; then
        pushd "$toolchain_src" > /dev/null

        local toolchain_dir=$(find . -maxdepth 1 -type d -name "*toolchain*${RELEASE_VERSION}" | head -n1)
        if [[ -n "$toolchain_dir" ]]; then
            pushd "$toolchain_dir" > /dev/null

            # Test Loader
            info "Testing HugeGraph Loader..."
            local loader_dir=$(find . -maxdepth 1 -type d -name "*loader*${RELEASE_VERSION}" | head -n1)
            if [[ -n "$loader_dir" ]]; then
                pushd "$loader_dir" > /dev/null
                if bin/hugegraph-loader.sh -f ./example/file/struct.json -s ./example/file/schema.groovy -g hugegraph; then
                    success "Loader test passed"
                else
                    collect_error "Loader test failed"
                fi
                popd > /dev/null
            fi

            # Test Tool
            info "Testing HugeGraph Tool..."
            local tool_dir=$(find . -maxdepth 1 -type d -name "*tool*${RELEASE_VERSION}" | head -n1)
            if [[ -n "$tool_dir" ]]; then
                pushd "$tool_dir" > /dev/null
                if bin/hugegraph gremlin-execute --script 'g.V().count()' && \
                   bin/hugegraph task-list && \
                   bin/hugegraph backup -t all --directory ./backup-test; then
                    success "Tool test passed"
                else
                    collect_error "Tool test failed"
                fi
                popd > /dev/null
            fi

            # Test Hubble
            info "Testing HugeGraph Hubble..."
            local hubble_dir=$(find . -maxdepth 1 -type d -name "*hubble*${RELEASE_VERSION}" | head -n1)
            if [[ -n "$hubble_dir" ]]; then
                pushd "$hubble_dir" > /dev/null
                if bin/start-hubble.sh; then
                    HUBBLE_STARTED=1
                    success "Hubble started"
                    sleep 2
                    bin/stop-hubble.sh
                    HUBBLE_STARTED=0
                    success "Hubble stopped"
                else
                    collect_error "Hubble test failed"
                fi
                popd > /dev/null
            fi

            popd > /dev/null
        fi

        popd > /dev/null
    fi

    # Stop server after toolchain tests
    if [[ $SERVER_STARTED -eq 1 ]] && [[ -n "$server_dir" ]]; then
        info "Stopping server..."
        pushd "$server_dir" > /dev/null
        bin/stop-hugegraph.sh
        SERVER_STARTED=0
        success "Server stopped"
        popd > /dev/null
    fi

    ####################################################
    # Step 8: Validate Binary Packages
    ####################################################
    print_step 8 9 "Validate Binary Packages"

    cd "${DIST_DIR}"

    local bin_packages=()
    for pkg in *.tar.gz; do
        if [[ "$pkg" != *-src.tar.gz ]]; then
            bin_packages+=("$pkg")
        fi
    done

    info "Found ${#bin_packages[@]} binary package(s)"

    for bin_pkg in "${bin_packages[@]}"; do
        validate_binary_package "$bin_pkg"
    done

    ####################################################
    # Step 9: Test Binary Packages
    ####################################################
    print_step 9 9 "Test Binary Server & Toolchain"

    # Test binary server
    local bin_server_dir=$(find_package_dir "*hugegraph*${RELEASE_VERSION}/*hugegraph-server*${RELEASE_VERSION}*")
    if [[ -n "$bin_server_dir" ]]; then
        info "Testing binary server package..."
        pushd "$bin_server_dir" > /dev/null

        if bin/init-store.sh && sleep $SERVER_START_DELAY && bin/start-hugegraph.sh; then
            success "Binary server started"
            SERVER_STARTED=1
        else
            collect_error "Failed to start binary server"
        fi

        popd > /dev/null
    fi

    # Test binary toolchain
    local bin_toolchain=$(find_package_dir "*toolchain*${RELEASE_VERSION}" "${DIST_DIR}")
    if [[ -n "$bin_toolchain" ]]; then
        pushd "$bin_toolchain" > /dev/null

        # Test binary loader
        local bin_loader=$(find . -maxdepth 1 -type d -name "*loader*${RELEASE_VERSION}" | head -n1)
        if [[ -n "$bin_loader" ]]; then
            pushd "$bin_loader" > /dev/null
            if bin/hugegraph-loader.sh -f ./example/file/struct.json -s ./example/file/schema.groovy -g hugegraph; then
                success "Binary loader test passed"
            else
                collect_error "Binary loader test failed"
            fi
            popd > /dev/null
        fi

        # Test binary tool
        local bin_tool=$(find . -maxdepth 1 -type d -name "*tool*${RELEASE_VERSION}" | head -n1)
        if [[ -n "$bin_tool" ]]; then
            pushd "$bin_tool" > /dev/null
            if bin/hugegraph gremlin-execute --script 'g.V().count()' && \
               bin/hugegraph task-list && \
               bin/hugegraph backup -t all --directory ./backup-test; then
                success "Binary tool test passed"
            else
                collect_error "Binary tool test failed"
            fi
            popd > /dev/null
        fi

        # Test binary hubble
        local bin_hubble=$(find . -maxdepth 1 -type d -name "*hubble*${RELEASE_VERSION}" | head -n1)
        if [[ -n "$bin_hubble" ]]; then
            pushd "$bin_hubble" > /dev/null
            if bin/start-hubble.sh; then
                HUBBLE_STARTED=1
                success "Binary hubble started"
                sleep 2
                bin/stop-hubble.sh
                HUBBLE_STARTED=0
                success "Binary hubble stopped"
            else
                collect_error "Binary hubble test failed"
            fi
            popd > /dev/null
        fi

        popd > /dev/null
    fi

    # Stop binary server
    if [[ $SERVER_STARTED -eq 1 ]] && [[ -n "$bin_server_dir" ]]; then
        pushd "$bin_server_dir" > /dev/null
        bin/stop-hugegraph.sh
        SERVER_STARTED=0
        success "Binary server stopped"
        popd > /dev/null
    fi

    ####################################################
    # Validation Complete
    ####################################################
    success "All validation steps completed!"

    # Cleanup function will show the final report
}

# Run main function
main "$@"
