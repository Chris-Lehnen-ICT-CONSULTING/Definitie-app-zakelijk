#!/bin/bash
# File Size Check Script
# Warns about files larger than 500 LOC (Lines of Code)
# Suggests refactoring for better maintainability
# Usage: ./check-file-size.sh [files...]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Thresholds
WARN_THRESHOLD=500
ERROR_THRESHOLD=1000

echo "📏 Checking file sizes..."

WARNINGS=0
ERRORS=0

# Get list of Python files to check
if [ $# -gt 0 ]; then
    # Check specific files passed as arguments
    FILES="$@"
else
    # Check all Python files in src/
    FILES=$(find src -name "*.py" -type f 2>/dev/null || echo "")
fi

if [ -z "$FILES" ]; then
    echo -e "${GREEN}✅ No files to check${NC}"
    exit 0
fi

# Check each file
for file in $FILES; do
    if [ ! -f "$file" ]; then
        continue
    fi

    # Count lines (excluding blank lines and comments)
    LOC=$(grep -v '^\s*#\|^\s*$' "$file" 2>/dev/null | wc -l | tr -d ' ')

    if [ "$LOC" -ge "$ERROR_THRESHOLD" ]; then
        echo -e "${RED}❌ $file: $LOC LOC (threshold: $ERROR_THRESHOLD)${NC}"
        echo -e "${YELLOW}   → File is very large. Consider breaking into smaller modules${NC}"
        ((ERRORS++))
    elif [ "$LOC" -ge "$WARN_THRESHOLD" ]; then
        echo -e "${YELLOW}⚠️  $file: $LOC LOC (threshold: $WARN_THRESHOLD)${NC}"
        echo -e "${YELLOW}   → File is getting large. Consider refactoring${NC}"
        ((WARNINGS++))
    fi
done

# Summary
if [ $ERRORS -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ Found $ERRORS file(s) exceeding $ERROR_THRESHOLD LOC${NC}"
    echo "Large files are harder to maintain and test."
    echo "Consider:"
    echo "  - Extract classes into separate files"
    echo "  - Split by responsibility (SRP)"
    echo "  - Move utilities to helper modules"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Found $WARNINGS file(s) exceeding $WARN_THRESHOLD LOC${NC}"
    echo "Consider refactoring before files get too large."
    # Warning only - don't block commit
    exit 0
else
    echo -e "${GREEN}✅ All files within size limits${NC}"
    exit 0
fi
