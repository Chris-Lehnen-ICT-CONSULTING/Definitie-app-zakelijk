#!/usr/bin/env sh
printf '%s\n' 'DEF-666-QUARANTINE-GUARD: scripts/hooks/run_ruff_changed.sh is bij de bron uitgeschakeld.' >&2
return 92 2>/dev/null || exit 92
# DEF-666: de blokkade hierboven staat vóór elke instelling, functiedefinitie en
# opdracht. Gesourcet stopt zij het script zonder de aanroepende shell te doden;
# rechtstreeks uitgevoerd sluit zij af met status 92. De code hieronder blijft
# ongewijzigd staan en wordt niet meer bereikt.
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
