#!/usr/bin/env bash
set -euo pipefail

# Grep Gate: reports (and optionally enforces) legacy context patterns
# Usage: ENFORCE_GREP_GATE=true scripts/grep_gate.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$ROOT_DIR"

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

violations=0
enforced_violations=0

echo -e "${YELLOW}Running Grep Gate checks...${NC}"

function check_pattern() {
  local desc="$1"
  local pattern="$2"
  local paths=("src")
  local exclude_ui='--glob=!src/ui/**'
  local exclude_extra=()
  if [[ -n "${3:-}" ]]; then
    exclude_extra=("$3")
  fi

  if command -v rg >/dev/null 2>&1; then
    set +e
    rg -n -g "*.py" $exclude_ui ${exclude_extra[@]+${exclude_extra[@]}} "$pattern" "${paths[@]}"
    rc=$?
    set -e
  else
    set +e
    grep -RIn --exclude-dir=__pycache__ --include='*.py' --exclude='src/ui/*' "$pattern" "${paths[@]}"
    rc=$?
    set -e
  fi

  if [ $rc -eq 0 ]; then
    echo -e "${RED}Violation: ${desc}${NC}"
    violations=$((violations+1))
  else
    echo -e "${GREEN}OK: ${desc}${NC}"
  fi
}

# 1) No session_state context usage outside UI
# Exclude suggestion strings in context_adapter to avoid false positives
check_pattern "Direct session_state context usage outside UI" "st\.session_state\.(juridische_context|organisatorische_context|wettelijke_basis)" "--glob=!src/services/context/context_adapter.py"

# 2) No string 'context' fields in typed hints (rough heuristic)
# Strictly catch context typed as bare str (not list[str])
check_pattern "String context field usage" "context\s*:\s*str(\W|$)"

# 3) No legacy orchestrator imports
check_pattern "Legacy orchestrator imports" "from orchestration import orchestrator"

# 4) Multiple context_dict creation points (detect scattered usage)
check_pattern "Multiple context_dict creations" "context_dict\s*=\s*\{"

echo -e "${YELLOW}Grep Gate violations: ${violations}${NC}"

# Enforced checks (fail build when enabled)
if [ "${ENFORCE_GREP_GATE:-false}" = "true" ]; then
  echo -e "${YELLOW}Running enforced checks...${NC}"
  # Enforce: no new 'context: str' in src/services (allowlist legacy files)
  if command -v rg >/dev/null 2>&1; then
    set +e
    rg -n -g "src/services/**/*.py" \
      --glob '!src/services/interfaces.py' \
      --glob '!src/services/definition_generator_enhancement.py' \
      --glob '!src/services/service_factory.py' \
      "context\s*:\s*str(\W|$)"
    rc=$?
    set -e
  else
    set +e
    grep -RIn --include='*.py' --exclude-dir='__pycache__' \
      --exclude='src/services/interfaces.py' \
      --exclude='src/services/definition_generator_enhancement.py' \
      --exclude='src/services/service_factory.py' \
      "context\s*:\s*str\(\W\|$\)" src/services
    rc=$?
    set -e
  fi
  if [ $rc -eq 0 ]; then
    echo -e "${RED}Enforced violation: 'context: str' detected in src/services${NC}"
    enforced_violations=$((enforced_violations+1))
  else
    echo -e "${GREEN}OK (enforced): no 'context: str' in src/services${NC}"
  fi

  # Optional: repo-wide enforcement (set ENFORCE_REPO_WIDE=true)
  if [ "${ENFORCE_REPO_WIDE:-false}" = "true" ]; then
    echo -e "${YELLOW}Running repo-wide enforced checks...${NC}"
    if command -v rg >/dev/null 2>&1; then
      set +e
      rg -n -g "src/**/*.py" \
        --glob '!src/services/interfaces.py' \
        --glob '!src/services/definition_generator_enhancement.py' \
        --glob '!src/services/service_factory.py' \
        "context\s*:\s*str(\W|$)"
      rc2=$?
      set -e
    else
      set +e
      grep -RIn --include='*.py' --exclude-dir='__pycache__' \
        --exclude='src/services/interfaces.py' \
        --exclude='src/services/definition_generator_enhancement.py' \
        --exclude='src/services/service_factory.py' \
        "context\s*:\s*str\(\W\|$\)" src
      rc2=$?
      set -e
    fi
    if [ ${rc2:-1} -eq 0 ]; then
      echo -e "${RED}Enforced violation: 'context: str' detected repo-wide${NC}"
      enforced_violations=$((enforced_violations+1))
    else
      echo -e "${GREEN}OK (enforced): no 'context: str' repo-wide${NC}"
    fi
  fi

  echo -e "${YELLOW}Enforced violations: ${enforced_violations}${NC}"
  if [ $enforced_violations -gt 0 ]; then
    echo -e "${RED}Grep Gate enforced checks failed.${NC}"
    exit 1
  fi
fi

exit 0
