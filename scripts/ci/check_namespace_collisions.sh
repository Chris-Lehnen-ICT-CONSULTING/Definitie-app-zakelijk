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

# Verzamel package-namen uit requirements*.txt.
# Parsing-volgorde matters — eerst gevaarlijke ontsnappingsroutes filteren:
#   1. Pip directives (-r, -c, -i, --index-url, etc.) — skip volledig, anders
#      verschijnt 'extra_index_url' als package-naam
#   2. Editable VCS installs (-e git+...#egg=NAME) — extract egg-name
#   3. Inline comments strippen (pkg==1.0  # note) vóór andere transforms
#   4. Env markers (numpy; python_version >= "3.10") — strip
#   5. YAML frontmatter (---)
#   6. Comments / lege regels
#   7. Extras: requests[security] → requests
#   8. Version specs: pkg>=1.0 → pkg
INSTALLED=""
for req in "${REQ_FILES[@]}"; do
  if [ -f "$req" ]; then
    pkgs=$(
      sed -E 's/^[[:space:]]*-e[[:space:]]+.*#egg=([^[:space:]&]+).*/\1/' "$req" \
        | grep -vE '^[[:space:]]*(-[a-zA-Z]|--[a-zA-Z])' \
        | sed 's/#.*$//' \
        | sed 's/;.*$//' \
        | grep -v '^---' \
        | grep -v '^[[:space:]]*$' \
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

INSTALLED=$(echo "$INSTALLED" | grep -v '^$' | sort -u || true)

if [ -z "$INSTALLED" ]; then
  # Lege/whitespace-only requirements is een geldige staat (initiële project
  # of na dependency-cleanup) — geen packages = geen collision mogelijk.
  # Maar log explicit hoeveel src/-packages ongecontroleerd blijven zodat
  # reviewers de stille staat niet missen (MEDIUM uit security-review).
  src_count=$(echo "$TOP_LEVELS" | wc -l | tr -d '[:space:]')
  echo "INFO: geen packages in requirements*.txt — $src_count src/-modules ongecontroleerd."
  exit 0
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
