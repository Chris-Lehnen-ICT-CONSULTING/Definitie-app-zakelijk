#!/usr/bin/env bash
set -euo pipefail

# Simple test runner with sensible defaults.
# Usage:
#   scripts/run_tests.sh fast      # unit + services + smoke (no slow/perf)
#   scripts/run_tests.sh pr        # + integration + contracts (no perf)
#   scripts/run_tests.sh full      # everything except performance by default
#   scripts/run_tests.sh perf      # performance/benchmark suites

mode="${1:-fast}"

case "$mode" in
  fast)
    echo "[tests] Running fast suite (smoke + unit + services)"
    pytest -q tests/smoke tests/unit tests/services -m "not performance and not slow"
    ;;
  pr)
    echo "[tests] Running PR suite (unit + services + integration + contracts)"
    pytest -q -m "not performance and not slow" tests/unit tests/services tests/integration tests/contracts
    ;;
  full)
    echo "[tests] Running full suite (excluding performance)"
    pytest -q -m "not performance" tests
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

