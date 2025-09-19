#!/usr/bin/env bash
set -euo pipefail

# Simple test runner with sensible defaults.
# Usage:
#   scripts/run_tests.sh fast      # unit + services + smoke (no slow/perf)
#   scripts/run_tests.sh pr        # + integration + contracts (no perf)
#   scripts/run_tests.sh full      # everything except performance by default
#   scripts/run_tests.sh perf      # performance/benchmark suites

# Usage: scripts/run_tests.sh <mode> [--include-legacy]
mode="${1:-fast}"
include_legacy="no"
if [[ "${2:-}" == "--include-legacy" ]] || [[ "${INCLUDE_LEGACY:-0}" == "1" ]]; then
  include_legacy="yes"
fi

case "$mode" in
  fast)
    echo "[tests] Running fast suite (smoke + unit + services)"
    if [[ "$include_legacy" == "yes" ]]; then
      pytest -q tests/smoke tests/unit tests/services -m "not performance and not slow"
    else
      pytest -q tests/smoke tests/unit tests/services -m "not performance and not slow" -k "not legacy"
    fi
    ;;
  pr)
    echo "[tests] Running PR suite (unit + services + integration + contracts)"
    if [[ "$include_legacy" == "yes" ]]; then
      pytest -q -m "not performance and not slow" tests/unit tests/services tests/integration tests/contracts
    else
      pytest -q -m "not performance and not slow" tests/unit tests/services tests/integration tests/contracts -k "not legacy"
    fi
    ;;
  full)
    echo "[tests] Running full suite (excluding performance)"
    if [[ "$include_legacy" == "yes" ]]; then
      pytest -q -m "not performance" tests
    else
      # Exclude legacy group unless explicitly included
      pytest -q -m "not performance" tests -k "not legacy"
    fi
    ;;
  perf)
    echo "[tests] Running performance/benchmark suite"
    pytest -q -m "performance or benchmark" tests/performance
    ;;
  *)
    echo "Unknown mode: $mode" >&2
    exit 1
    ;;
esac
