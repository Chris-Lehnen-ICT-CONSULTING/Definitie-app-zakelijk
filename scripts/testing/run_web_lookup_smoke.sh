#!/usr/bin/env bash
set -euo pipefail

echo "[smoke] Web Lookup smoke tests (mocked):"
export PYTHONPATH=src
pytest -q -m smoke_web_lookup "$@"

