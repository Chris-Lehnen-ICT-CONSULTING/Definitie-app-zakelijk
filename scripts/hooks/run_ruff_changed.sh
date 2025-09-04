#!/usr/bin/env sh
set -eu

# Gather staged Python files limited to src/ and config/
files=$(git diff --cached --name-only --diff-filter=ACM | grep -E '^(src|config)/.+\.py$' || true)

if [ -z "${files}" ]; then
  echo "[ruff] No changed Python files under src/ or config/. Skipping."
  exit 0
fi

echo "[ruff] Linting changed files"

# Run ruff with fixes on the staged files
python -m ruff check --fix --force-exclude --exit-non-zero-on-fix ${files}

# Re-stage files if ruff fixed them
git add ${files}
