#!/usr/bin/env bash
# check_namespace_collisions.sh — DEF-409 / DEF-410
#
# Thin shim. De detectielogica is in DEF-410 herschreven naar Python en leeft
# nu in check_namespace_collisions.py (PEP 508 strict parser via `packaging`,
# distribution→import mapping, recursieve -r/-c includes, formele pytest-tests).
#
# Dit script blijft het stabiele entrypoint zodat de CI-stap
# (.github/workflows/test.yml) en de pre-commit hook (.pre-commit-config.yaml)
# ongewijzigd blijven werken.
#
# Interpreter-keuze (eerste die bestaat):
#   1. $PYTHON env-var (expliciete override)
#   2. repo .venv/bin/python (zodat pre-commit ook zonder geactiveerde venv het
#      `packaging`-pakket vindt)
#   3. python3 op PATH (CI installeert deps in de actieve env)
#
# Exit codes en argumenten worden 1-op-1 doorgegeven aan het Python-script.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -n "${PYTHON:-}" ]; then
  PY="$PYTHON"
elif [ -x "$REPO_ROOT/.venv/bin/python" ]; then
  PY="$REPO_ROOT/.venv/bin/python"
else
  PY="python3"
fi

exec "$PY" "$SCRIPT_DIR/check_namespace_collisions.py" "$@"
