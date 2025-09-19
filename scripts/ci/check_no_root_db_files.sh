#!/usr/bin/env bash
set -euo pipefail

# Blocks committing or keeping root-level *.db files.
# Behavior:
# - In pre-commit (local): fails if any staged root-level *.db is present.
# - In CI (GITHUB_ACTIONS=true): fails if any tracked root-level *.db exists.

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

echo -e "${YELLOW}🔎 Checking for root-level *.db files...${NC}"

fail_with_list() {
  echo -e "${RED}❌ Root-level database files are not allowed:${NC}"
  echo "$1" | sed 's/^/  - /'
  echo
  echo "Move database files under 'data/' or use ':memory:'/tmp paths in tests."
  echo "Hint: add 'use_database=False' or use pytest's tmp_path fixture."
  exit 1
}

if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
  # CI mode: fail if any tracked root-level *.db exists in the repo
  ROOT_DB_FILES=$(git ls-files | awk '/^[^\/]+\.db$/') || ROOT_DB_FILES=""
  if [[ -n "$ROOT_DB_FILES" ]]; then
    fail_with_list "$ROOT_DB_FILES"
  fi
else
  # Local pre-commit: fail only if staged root-level *.db is present
  STAGED_FILES=$(git diff --name-only --cached --diff-filter=ACMR || true)
  ROOT_DB_STAGED=$(echo "$STAGED_FILES" | awk '/^[^\/]+\.db$/') || ROOT_DB_STAGED=""
  if [[ -n "$ROOT_DB_STAGED" ]]; then
    fail_with_list "$ROOT_DB_STAGED"
  fi
fi

echo -e "${GREEN}✅ No root-level *.db files detected.${NC}"

