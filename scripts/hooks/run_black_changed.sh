#!/usr/bin/env sh
set -eu

# Gather staged Python files limited to src/ and config/
files=$(git diff --cached --name-only --diff-filter=ACM | grep -E '^(src|config)/.+\.py$' || true)

if [ -z "${files}" ]; then
  echo "[black] No changed Python files under src/ or config/. Skipping."
  exit 0
fi

echo "[black] Formatting changed files"

# Run black on the staged files
python -m black ${files}

# Re-stage files after formatting
git add ${files}
