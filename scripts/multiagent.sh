#!/usr/bin/env bash

# Multi‑Agent Helper for Codex CLI
# Creates parallel worktrees/branches, runs quick checks/scoreboard, and cleans up.
#
# Usage examples:
#   bash scripts/multiagent.sh init -n 2                   # create agent-a, agent-b worktrees
#   bash scripts/multiagent.sh init agent-a agent-b agent-c # create named worktrees
#   bash scripts/multiagent.sh status                      # show current agent branches/worktrees
#   bash scripts/multiagent.sh review                      # run scoreboard across agent branches
#   bash scripts/multiagent.sh review --quick-checks       # also run quick checks in each branch
#   bash scripts/multiagent.sh teardown                    # remove worktrees (keep branches)
#   bash scripts/multiagent.sh teardown --delete-branches  # remove worktrees and delete branches

set -euo pipefail

ROOT_DIR=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$ROOT_DIR"

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

default_agents() {
  echo "agent-a agent-b"
}

agent_path() {
  local name="$1"
  local parent
  parent=$(dirname "$ROOT_DIR")
  echo "$parent/$(basename "$ROOT_DIR")-$name"
}

have_branch() {
  local name="$1"
  git show-ref --verify --quiet "refs/heads/${name}"
}

have_worktree_for() {
  local path="$1"
  git worktree list --porcelain | awk '/worktree /{print $2}' | grep -Fxq "$path"
}

cmd_init() {
  local count=0
  local names=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -n|--num)
        count="$2"; shift 2;;
      -h|--help)
        echo "Usage: $0 init [-n 2] [agent-a agent-b ...]"; exit 0;;
      *) names+=("$1"); shift;;
    esac
  done

  if [[ ${#names[@]} -eq 0 ]]; then
    if [[ "$count" -gt 0 ]]; then
      for i in $(seq 1 "$count"); do names+=("agent-$i"); done
    else
      # default two agents
      read -r -a names <<< "$(default_agents)"
    fi
  fi

  local base_branch
  base_branch=$(git rev-parse --abbrev-ref HEAD)
  echo -e "${YELLOW}Creating worktrees from base branch:${NC} $base_branch"

  for name in "${names[@]}"; do
    local path
    path=$(agent_path "$name")
    if have_worktree_for "$path"; then
      echo -e "${YELLOW}• Worktree already exists:${NC} $path"
    else
      if ! have_branch "$name"; then
        git worktree add "$path" -b "$name" "$base_branch"
      else
        git worktree add "$path" "$name"
      fi
      echo -e "${GREEN}✓ Created worktree:${NC} $path (branch $name)"
    fi
  done

  echo -e "\n${GREEN}Done.${NC} Open each worktree in a terminal/editor and proceed."
}

cmd_status() {
  echo "# Worktrees"
  git worktree list
  echo
  echo "# Local agent branches"
  git for-each-ref --format='%(refname:short)' refs/heads | grep -E '^agent(-|[0-9])' || true
}

run_quick_checks() {
  if [[ -x scripts/agent_quick_checks.sh ]]; then
    bash scripts/agent_quick_checks.sh || return 1
  else
    echo "(quick checks script not found; skipping)"
  fi
}

cmd_review() {
  local do_quick=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --quick-checks) do_quick=1; shift;;
      -h|--help) echo "Usage: $0 review [--quick-checks] [agent-a agent-b ...]"; exit 0;;
      *) break;;
    esac
  done

  local names=()
  if [[ $# -gt 0 ]]; then
    names=("$@")
  else
    read -r -a names <<< "$(default_agents)"
  fi

  local current
  current=$(git rev-parse --abbrev-ref HEAD)

  # Optional quick-checks in each branch (without leaving current tree)
  if [[ $do_quick -eq 1 ]]; then
    for name in "${names[@]}"; do
      local path
      path=$(agent_path "$name")
      if [[ -d "$path" ]]; then
        echo -e "${YELLOW}→ Quick checks in ${name}${NC}"
        (cd "$path" && run_quick_checks) || echo -e "${RED}Quick checks failed in ${name}${NC}"
      fi
    done
  fi

  # Run scoreboard across branches
  if [[ -x scripts/agent_scoreboard.sh ]]; then
    bash scripts/agent_scoreboard.sh "${names[@]}"
  else
    echo -e "${RED}scripts/agent_scoreboard.sh not found${NC}"
    exit 1
  fi

  # restore current branch
  git checkout -q "$current" || true
}

cmd_teardown() {
  local delete_branches=0
  local names=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --delete-branches) delete_branches=1; shift;;
      -h|--help) echo "Usage: $0 teardown [--delete-branches] [agent-a agent-b ...]"; exit 0;;
      *) names+=("$1"); shift;;
    esac
  done

  if [[ ${#names[@]} -eq 0 ]]; then
    read -r -a names <<< "$(default_agents)"
  fi

  for name in "${names[@]}"; do
    local path
    path=$(agent_path "$name")
    if [[ -d "$path" ]]; then
      git worktree remove "$path" --force || true
      echo -e "${GREEN}✓ Removed worktree:${NC} $path"
    fi
    if [[ $delete_branches -eq 1 ]] && have_branch "$name"; then
      git branch -D "$name" || true
      echo -e "${GREEN}✓ Deleted branch:${NC} $name"
    fi
  done
}

cmd_help() {
  cat <<EOF
Multi‑Agent Helper

Commands:
  init [-n NUM] [NAMES...]     Create worktrees for agents (default: agent-a agent-b)
  status                        Show worktrees and local agent branches
  review [--quick-checks] [NAMES...]  Run tests scoreboard (and optional quick checks)
  teardown [--delete-branches] [NAMES...]  Remove worktrees (and optionally branches)

Examples:
  $0 init -n 2
  $0 init agent-a agent-b agent-c
  $0 review --quick-checks
  $0 teardown --delete-branches
EOF
}

main() {
  local cmd="${1:-help}"; shift || true
  case "$cmd" in
    init) cmd_init "$@" ;;
    status) cmd_status "$@" ;;
    review) cmd_review "$@" ;;
    teardown) cmd_teardown "$@" ;;
    -h|--help|help) cmd_help ;;
    *) echo -e "${RED}Unknown command:${NC} $cmd"; cmd_help; exit 1;;
  esac
}

main "$@"

