#!/usr/bin/env bash

# Bundle EPIC-010 quick-checks: ripgrep legacy patterns + targeted tests
# Fails (exit != 0) on any findings or failing tests.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ROOT_DIR=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$ROOT_DIR"

echo "🔎 Running agent quick checks (EPIC-010)"
echo "======================================="

failed=0

# 1) Legacy pattern checks (reuse canonical script if available)
if [ -x "scripts/check-legacy-patterns.sh" ]; then
  echo "→ EPIC-010 legacy pattern scan"
  if ! bash scripts/check-legacy-patterns.sh; then
    echo -e "${RED}❌ Legacy pattern violations found${NC}"
    failed=1
  else
    echo -e "${GREEN}✅ Legacy patterns OK${NC}"
  fi
else
  echo -e "${YELLOW}⚠️  scripts/check-legacy-patterns.sh not found or not executable; running minimal grep checks${NC}"
  if rg -n "from src\\.models\\.generation_result import|best_iteration|request\\.context(?!_|\\w)" src/ --type py; then
    failed=1
  fi
  if rg -n "asyncio\\.run\\(" src/services/ --type py; then
    failed=1
  fi
  if rg -n "import streamlit|from streamlit" src/services/ --type py | grep -v "# Legacy\|# Deprecated"; then
    failed=1
  fi
fi

# 2) Targeted quick tests (fast, high-signal)
echo "\n→ Running targeted tests"

PYTEST_BIN=${PYTEST_BIN:-pytest}

targets=()
[ -f "tests/test_legacy_validation_removed.py" ] && targets+=("tests/test_legacy_validation_removed.py")
[ -f "tests/test_legacy_validation_removed_simple.py" ] && targets+=("tests/test_legacy_validation_removed_simple.py")
[ -f "test_smoke_generation.py" ] && targets+=("test_smoke_generation.py")

if [ ${#targets[@]} -eq 0 ]; then
  echo -e "${YELLOW}⚠️  No targeted quick tests found; skipping tests step${NC}"
else
  if ! "$PYTEST_BIN" -q "${targets[@]}"; then
    echo -e "${RED}❌ Targeted tests failed${NC}"
    failed=1
  else
    echo -e "${GREEN}✅ Targeted tests passed${NC}"
  fi
fi

echo "\n======================================="
if [ $failed -eq 0 ]; then
  echo -e "${GREEN}✅ Quick checks passed${NC}"
  exit 0
else
  echo -e "${RED}❌ Quick checks failed${NC}"
  exit 1
fi

