#!/usr/bin/env bash
set -euo pipefail

# Map OPENAI_API_KEY from OPENAI_API_KEY_PROD if not set explicitly
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  if [[ -n "${OPENAI_API_KEY_PROD:-}" ]]; then
    export OPENAI_API_KEY="${OPENAI_API_KEY_PROD}"
  else
    echo "Error: OPENAI_API_KEY is not set and OPENAI_API_KEY_PROD is not set." >&2
    echo "Set one of them, e.g.: export OPENAI_API_KEY_PROD=sk-..." >&2
    exit 1
  fi
fi

# Default command runs the Streamlit app; allow overrides
if [[ $# -eq 0 ]]; then
  set -- streamlit run src/main.py
fi

exec "$@"
