#!/usr/bin/env bash
# check_namespace_collisions.sh — DEF-409
#
# Detecteert dependency-confusion risico: src/ top-level packages die ook
# bestaan als PyPI-package in requirements*.txt. Met `pythonpath = src`
# (pytest.ini) zou een PyPI-pakket met dezelfde naam stilletjes de in-repo
# module shadowen — een dependency-confusion attack vector.
#
# Faalt met exit 1 als overlap gevonden + lijst de conflicten.
# Faalt met exit 1 bij setup-fouten (missende files, lege src/).
#
# Gebruik:
#   bash scripts/ci/check_namespace_collisions.sh
#
# Geconvergeerd voor:
# - Lokaal pre-commit hook (alleen bij requirements*.txt changes)
# - CI step (elke push/PR)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SRC_DIR="$REPO_ROOT/src"
REQ_FILES=(
  "$REPO_ROOT/requirements.txt"
  "$REPO_ROOT/requirements-dev.txt"
)

if [ ! -d "$SRC_DIR" ]; then
  echo "FOUT: src/ directory niet gevonden op $SRC_DIR" >&2
  exit 1
fi

# Verzamel top-level src/-package-namen (normaliseren: lowercase, _ ipv -)
# Exclude: __pycache__, *.egg-info, hidden dirs, niet-directories
TOP_LEVELS=$(
  find "$SRC_DIR" -mindepth 1 -maxdepth 1 -type d \
    -not -name '__pycache__' \
    -not -name '.*' \
    -not -name '*.egg-info' \
    -exec basename {} \; \
  | tr '[:upper:]' '[:lower:]' \
  | tr '-' '_' \
  | sort -u
)

if [ -z "$TOP_LEVELS" ]; then
  echo "FOUT: geen top-level packages gevonden in $SRC_DIR" >&2
  exit 1
fi

# Verzamel package-namen uit requirements*.txt
# Strip versie-specifiers, comments, lege regels, frontmatter (---).
# Normaliseer: lowercase, _ ipv -
INSTALLED=""
for req in "${REQ_FILES[@]}"; do
  if [ -f "$req" ]; then
    pkgs=$(
      grep -v '^[[:space:]]*#' "$req" \
        | grep -v '^[[:space:]]*$' \
        | grep -v '^---' \
        | sed 's/[<>=!~].*//' \
        | sed 's/\[.*\]//' \
        | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
        | tr '[:upper:]' '[:lower:]' \
        | tr '-' '_' \
        || true
    )
    INSTALLED="$INSTALLED"$'\n'"$pkgs"
  fi
done

INSTALLED=$(echo "$INSTALLED" | grep -v '^$' | sort -u)

if [ -z "$INSTALLED" ]; then
  echo "FOUT: geen packages gevonden in requirements*.txt" >&2
  exit 1
fi

# Vind overlap (set-intersection)
COLLISIONS=$(comm -12 <(echo "$INSTALLED") <(echo "$TOP_LEVELS") || true)

if [ -n "$COLLISIONS" ]; then
  echo "❌ DEPENDENCY-CONFUSION RISICO: src/ top-level packages botsen met PyPI-deps:" >&2
  echo "$COLLISIONS" | sed 's/^/  - /' >&2
  echo "" >&2
  echo "Met pythonpath=src zou de PyPI-package de in-repo module stil kunnen" >&2
  echo "shadowen. Mogelijke fixes:" >&2
  echo "  1. Hernoem de src/-package (bv. naar definitieagent.X — zie DEF-409)" >&2
  echo "  2. Verwijder de botsende PyPI-dependency uit requirements*.txt" >&2
  echo "  3. Vervang door een specifiekere PyPI-package met andere naam" >&2
  echo "" >&2
  echo "Zie docs/CONTRIBUTING.md sectie 'Dependency-confusion policy'." >&2
  exit 1
fi

echo "✓ Geen namespace-collisions tussen requirements*.txt en src/ top-levels."
exit 0
