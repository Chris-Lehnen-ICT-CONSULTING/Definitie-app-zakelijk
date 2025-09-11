#!/usr/bin/env bash
set -euo pipefail

# Fail if any TODO-like markers are present in code (src/, tests/, scripts/)
# Allowed markers (ignored): within docs/ or non-code assets

COMMENT_MARKERS='(TODO|FIXME|XXX|TBD|HACK|NOCOMMIT|@todo|@fixme)'
PATTERN_START='^\s*#\s*'"$COMMENT_MARKERS"'\b'
PATTERN_INLINE='\s#\s*'"$COMMENT_MARKERS"'\b'

if ! command -v rg >/dev/null 2>&1; then
  echo "ripgrep (rg) is required for this check" >&2
  exit 2
fi

echo "Running TODO marker check..."

set +e
OUTPUT=$(rg -n -i -S -e "$PATTERN_START|$PATTERN_INLINE" src tests scripts --glob '!**/*.md' --glob '!**/*.html')
RC=$?
set -e

if [ $RC -eq 0 ] && [ -n "$OUTPUT" ]; then
  echo "\n❌ Found disallowed TODO-like markers in code:\n" >&2
  echo "$OUTPUT" >&2
  echo "\nPlease move these to backlog and remove from code before committing." >&2
  exit 1
fi

echo "✅ No TODO-like markers found."
exit 0
