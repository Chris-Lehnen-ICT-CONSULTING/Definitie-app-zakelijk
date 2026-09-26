#!/bin/bash
# SessionStart-hook voor Claude Code on the web (cloudsessies).
# Zet een Python 3.13 project-venv (.venv) op met alle runtime- en dev-
# dependencies, zodat `make test` en `make lint` direct werken.
# Lokaal (op de Mac) doet deze hook niets.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

# De Makefile gebruikt .venv/bin/python als die bestaat (zie PY in Makefile)
# en eist Python 3.13 (check-python). Idempotent: bestaande venv hergebruiken.
if [ ! -x .venv/bin/python ] || ! .venv/bin/python -c 'import sys; sys.exit(sys.version_info[:2] != (3, 13))'; then
  uv venv --clear --python 3.13 .venv
fi

# requirements-dev.txt bevat geen runtime-deps, dus beide installeren.
uv pip install --python .venv/bin/python -r requirements.txt -r requirements-dev.txt

# Venv ook buiten make beschikbaar maken (python, pytest, ruff, black).
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export VIRTUAL_ENV=\"$PWD/.venv\"" >> "$CLAUDE_ENV_FILE"
  echo "export PATH=\"$PWD/.venv/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
fi
