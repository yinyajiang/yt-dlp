#!/bin/zsh
# Recursively sign a PyInstaller onedir build (sign libraries first, then main executable), then verify.
# Usage:
#   ./s.sh --identity "Developer ID Application: Company (TEAMID)" --dir /path/to/onedir
# Optional flags:
#   -i, --identity       Developer ID Application identity
#   -d, --dir            Target onedir path
#   -e, --entitlements   Path to entitlements.plist (optional)
#   -h, --help           Show help
# Only CLI flags are supported (no environment variable fallback).

set -e
set -u
set -o pipefail

SIGN_IDENTITY=""
ENTITLEMENTS=""
TARGET_DIR=""

usage() {
  cat <<EOF
Usage:
  $0 --identity "Developer ID Application: Company (TEAMID)" --dir /path/to/onedir [options]

Options:
  -i, --identity STRING       Developer ID Application identity (required)
  -d, --dir PATH              Target onedir path (required)
  -e, --entitlements PATH     Path to entitlements.plist (optional; if provided, file must exist)
  -h, --help                  Show this help
EOF
}

# Parse CLI args
while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--identity)
      [[ $# -ge 2 ]] || { echo "Error: --identity requires a value"; usage; exit 2; }
      SIGN_IDENTITY="$2"; shift 2;;
    -d|--dir)
      [[ $# -ge 2 ]] || { echo "Error: --dir requires a value"; usage; exit 2; }
      TARGET_DIR="$2"; shift 2;;
    -e|--entitlements)
      [[ $# -ge 2 ]] || { echo "Error: --entitlements requires a value"; usage; exit 2; }
      ENTITLEMENTS="$2"; shift 2;;
    -h|--help)
      usage; exit 0;;
    --)
      shift; break;;
    -*)
      echo "Unknown option: $1"; usage; exit 2;;
    *)
      # Positional: treat as TARGET_DIR if not set
      if [[ -z "$TARGET_DIR" ]]; then
        TARGET_DIR="$1"; shift
      else
        echo "Unexpected positional argument: $1"; usage; exit 2
      fi
      ;;
  esac
done


# Validate required args
if [[ -z "$SIGN_IDENTITY" ]]; then
  echo "Error: signing identity not provided. Use --identity."
  usage
  exit 2
fi

if [[ -z "$TARGET_DIR" ]]; then
  echo "Error: target directory not provided. Use --dir."
  usage
  exit 2
fi

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "Error: target directory does not exist: $TARGET_DIR"
  exit 1
fi

if [[ -n "$ENTITLEMENTS" && ! -f "$ENTITLEMENTS" ]]; then
  echo "Error: entitlements file does not exist: $ENTITLEMENTS"
  exit 1
fi

echo "Target directory: $TARGET_DIR"
echo "Signing identity: $SIGN_IDENTITY"
[[ -f "$ENTITLEMENTS" ]] && echo "Entitlements: $ENTITLEMENTS"

# Remove quarantine attribute to avoid restrictions
if command -v xattr >/dev/null 2>&1; then
  xattr -dr com.apple.quarantine "$TARGET_DIR" 2>/dev/null || true
fi

is_macho() {
  local f="$1"
  [[ -f "$f" ]] || return 1
  local desc
  desc="$(file -h "$f" 2>/dev/null || true)"
  [[ "$desc" == *"Mach-O"* ]] || [[ "$desc" == *"universal binary"* ]]
}

sign_one_file() {
  local f="$1"
  if ! is_macho "$f"; then
    return 0
  fi
  local args=(--force --timestamp --options runtime -s "$SIGN_IDENTITY")
  if [[ -f "$ENTITLEMENTS" ]]; then
    args+=(--entitlements "$ENTITLEMENTS")
  fi
  echo "Signing file: $f"
  codesign "${args[@]}" "$f"
}

verify_one() {
  local p="$1"
  codesign --verify --verbose=2 "$p"
}

# 1) Sign all dynamic libraries (.dylib/.so)
echo "Step 1: Signing dynamic libraries (*.dylib / *.so)"
find "$TARGET_DIR" -type f \( -name "*.dylib" -o -name "*.so" \) -print0 | \
while IFS= read -r -d '' f; do
  sign_one_file "$f"
done

# 2) Sign all executable Mach-O files (PyInstaller Python executable and helpers)
echo "Step 2: Signing executable Mach-O files"
find "$TARGET_DIR" -type f -perm -u+x -print0 | \
while IFS= read -r -d '' f; do
  sign_one_file "$f"
done

# 3) Sign .framework bundles (assumes inner binaries already signed)
echo "Step 3: Signing .framework bundles"
find "$TARGET_DIR" -type d -name "*.framework" -print0 | \
while IFS= read -r -d '' fw; do
  local_args=(--force --timestamp --options runtime -s "$SIGN_IDENTITY")
  if [[ -f "$ENTITLEMENTS" ]]; then
    local_args+=(--entitlements "$ENTITLEMENTS")
  fi
  echo "Signing framework: $fw"
  codesign "${local_args[@]}" "$fw"
done

# 4) Finally sign the main executable (first top-level executable)
echo "Step 4: Signing main executable"
main_exec=""
# Pick the first top-level executable as main
main_exec="$(find "$TARGET_DIR" -maxdepth 1 -type f -perm -u+x -print | head -n 1 || true)"

if [[ -z "$main_exec" ]]; then
  echo "Warning: main executable not found at top level of $TARGET_DIR."
else
  sign_one_file "$main_exec"
fi

# 5) Verify
echo "Step 5: Verifying signatures"
if [[ -n "$main_exec" ]]; then
  echo "codesign verify (deep/strict): $main_exec"
  codesign --verify --deep --strict --verbose=2 "$main_exec"
  echo "spctl assess: $main_exec"
  spctl -a -vv "$main_exec" || true
else
  # If no main executable, at least attempt deep verification on directory
  echo "codesign verify (deep/strict): $TARGET_DIR"
  codesign --verify --deep --strict --verbose=2 "$TARGET_DIR" || true
fi

echo "Done."
