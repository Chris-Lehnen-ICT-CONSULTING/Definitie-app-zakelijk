#!/usr/bin/env bash
set -euo pipefail

# Fail if any TODO-like markers are present in code.
# Twee passes:
#   1. Comment-markers (breed, case-insensitive) in #-commentaar over src/tests/scripts.
#   2. String/docstring-markers (DEF-459): case-SENSITIVE, gereduceerde set, ALLEEN src/.
#      Sluit XXX/TBD/HACK bewust uit — die botsen met legitieme placeholders (US-XXX,
#      BUG-XXX) en lowercase status-waarden ("status": "todo") in scripts/tests.
#      Deze pass dicht het gat waardoor docstring-TODO's (bv. een placeholder-service)
#      eerder als 'TODO-vrij' door de gate glipten.
# Allowed markers (ignored): within docs/ of non-code assets.
#
# Gebruik: check_no_todo_markers.sh [PAD ...]
#   Zonder args (productie): comment-pass over src/tests/scripts, string-pass over src.
#   Met args (tests): beide passes over de opgegeven paden.

COMMENT_MARKERS='(TODO|FIXME|XXX|TBD|HACK|NOCOMMIT|@todo|@fixme)'
PATTERN_START='^\s*#\s*'"$COMMENT_MARKERS"'\b'
PATTERN_INLINE='\s#\s*'"$COMMENT_MARKERS"'\b'
STRING_MARKERS='\b(TODO|FIXME|NOCOMMIT)\b'

if ! command -v rg >/dev/null 2>&1; then
  echo "ripgrep (rg) is required for this check" >&2
  exit 2
fi

echo "Running TODO marker check..."

if [ "$#" -gt 0 ]; then
  COMMENT_TARGETS=("$@")
  STRING_TARGETS=("$@")
else
  COMMENT_TARGETS=(src tests scripts)
  STRING_TARGETS=(src)
fi

set +e
OUTPUT_COMMENT=$(rg -n -i -S -e "$PATTERN_START|$PATTERN_INLINE" \
  "${COMMENT_TARGETS[@]}" --glob '!**/*.md' --glob '!**/*.html')
OUTPUT_STRING=$(rg -n -e "$STRING_MARKERS" \
  "${STRING_TARGETS[@]}" --glob '!**/*.md' --glob '!**/*.html')
set -e

OUTPUT=$(printf '%s\n%s\n' "$OUTPUT_COMMENT" "$OUTPUT_STRING" | rg -v '^\s*$' || true)

if [ -n "$OUTPUT" ]; then
  echo "❌ Found disallowed TODO-like markers in code:" >&2
  echo "$OUTPUT" >&2
  echo "Please move these to backlog and remove from code before committing." >&2
  exit 1
fi

echo "✅ No TODO-like markers found."
exit 0
