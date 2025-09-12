#!/usr/bin/env bash

# Agent Scoreboard: iterate branches, run pytest, log duration/status
# Usage:
#   bash scripts/agent_scoreboard.sh [branch1 branch2 ...]
# If no branches provided, uses all local branches except the current one.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ROOT_DIR=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$ROOT_DIR"

# Check for dirty working tree (to avoid losing changes)
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo -e "${YELLOW}⚠️  Working tree has uncommitted changes. Commit or stash before running.${NC}"
  # Continue, but warn the user that checkout may fail
fi

current_branch=$(git rev-parse --abbrev-ref HEAD)

if [ "$#" -gt 0 ]; then
  branches=("$@")
else
  # All local branches except current
  mapfile -t branches < <(git for-each-ref --format='%(refname:short)' refs/heads | grep -v "^${current_branch}$" || true)
fi

if [ ${#branches[@]} -eq 0 ]; then
  echo "No branches to test. Provide branches explicitly: bash scripts/agent_scoreboard.sh agent-a agent-b"
  exit 0
fi

mkdir -p reports
log_file="reports/agent_scoreboard_$(date +%Y%m%d_%H%M%S).log"

echo "# Agent Scoreboard $(date)" | tee "$log_file"
printf "%-24s | %-6s | %-8s | %s\n" "BRANCH" "TESTS" "DURATION" "NOTES" | tee -a "$log_file"
printf -- "%.0s-" {1..80}; echo | tee -a "$log_file"

overall_fail=0

for b in "${branches[@]}"; do
  notes=""
  if ! git show-ref --verify --quiet "refs/heads/${b}"; then
    printf "%-24s | %-6s | %-8s | %s\n" "$b" "SKIP" "-" "Branch not found" | tee -a "$log_file"
    continue
  fi

  # Try to checkout the branch
  if ! git checkout -q "$b"; then
    printf "%-24s | %-6s | %-8s | %s\n" "$b" "SKIP" "-" "Checkout failed" | tee -a "$log_file"
    continue
  fi

  start=$(date +%s)
  status=0

  # Prefer running only a fast smoke if available, else default to full pytest
  if [ -f "test_smoke_generation.py" ]; then
    pytest -q test_smoke_generation.py || status=$?
  elif [ -d "tests" ]; then
    # Run a quick subset first if exists
    if ls tests/*legacy* 1> /dev/null 2>&1; then
      pytest -q tests/*legacy* || status=$?
    else
      pytest -q || status=$?
    fi
  else
    notes="no tests directory"
    status=0
  fi

  dur=$(( $(date +%s) - start ))

  if [ $status -eq 0 ]; then
    printf "%-24s | ${GREEN}%-6s${NC} | %-8ss | %s\n" "$b" "PASS" "$dur" "$notes" | tee -a "$log_file"
  else
    printf "%-24s | ${RED}%-6s${NC} | %-8ss | %s\n" "$b" "FAIL" "$dur" "$notes" | tee -a "$log_file"
    overall_fail=1
  fi
done

# Switch back to the original branch
git checkout -q "$current_branch" || true

echo | tee -a "$log_file"
if [ $overall_fail -eq 0 ]; then
  echo -e "${GREEN}✅ All tested branches passed${NC}" | tee -a "$log_file"
else
  echo -e "${RED}❌ One or more branches failed tests${NC}" | tee -a "$log_file"
fi

exit $overall_fail

