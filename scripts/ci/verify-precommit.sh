#!/bin/bash
# Pre-commit Verification Script
# Verifies that pre-commit hooks were executed before push
# Usage: ./verify-precommit.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Verifying pre-commit execution..."

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo -e "${RED}❌ pre-commit is not installed${NC}"
    echo "Install with: pip install pre-commit"
    exit 1
fi

# Check if .pre-commit-config.yaml exists
if [ ! -f ".pre-commit-config.yaml" ]; then
    echo -e "${YELLOW}⚠️  No .pre-commit-config.yaml found${NC}"
    echo "Pre-commit validation skipped"
    exit 0
fi

# Check if pre-commit hooks are installed
if [ ! -f ".git/hooks/pre-commit" ]; then
    echo -e "${RED}❌ Pre-commit hooks not installed${NC}"
    echo "Run: pre-commit install"
    exit 1
fi

# Get list of changed files in last commit or staged
if git rev-parse --verify HEAD >/dev/null 2>&1; then
    # We have commits, check the last one
    CHANGED_FILES=$(git show --name-only --format="" HEAD 2>/dev/null || echo "")
else
    # No commits yet, check staged files
    CHANGED_FILES=$(git diff --cached --name-only 2>/dev/null || echo "")
fi

if [ -z "$CHANGED_FILES" ]; then
    echo -e "${YELLOW}⚠️  No changed files to verify${NC}"
    exit 0
fi

echo "Verifying pre-commit ran on:"
echo "$CHANGED_FILES" | head -5
if [ $(echo "$CHANGED_FILES" | wc -l) -gt 5 ]; then
    echo "... and $(( $(echo "$CHANGED_FILES" | wc -l) - 5 )) more files"
fi

# Run pre-commit on changed files to verify they pass
echo ""
echo "Running pre-commit checks..."

# Use temporary file list
TEMP_FILE=$(mktemp)
echo "$CHANGED_FILES" > "$TEMP_FILE"

# Run pre-commit
if cat "$TEMP_FILE" | xargs -r pre-commit run --files 2>&1; then
    echo -e "${GREEN}✅ Pre-commit verification passed${NC}"
    rm -f "$TEMP_FILE"
    exit 0
else
    echo -e "${RED}❌ Pre-commit hooks failed${NC}"
    echo ""
    echo "This means either:"
    echo "  1. Pre-commit hooks were not run before committing"
    echo "  2. Pre-commit hooks were skipped (--no-verify)"
    echo "  3. Changes were made that don't pass current hooks"
    echo ""
    echo "To fix:"
    echo "  1. Run: pre-commit run --all-files"
    echo "  2. Fix any issues"
    echo "  3. Commit the fixes"
    echo ""
    rm -f "$TEMP_FILE"
    exit 1
fi
