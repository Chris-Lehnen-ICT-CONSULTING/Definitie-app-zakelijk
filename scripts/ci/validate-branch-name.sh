#!/bin/bash
# Branch Name Validation Script
# Validates that branch names follow the convention: {type}/{description}
# Valid types: feature, fix, hotfix, docs, refactor, test, chore
# Usage: ./validate-branch-name.sh [branch-name]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get branch name from argument or current branch
if [ $# -eq 1 ]; then
    BRANCH_NAME="$1"
else
    BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
    if [ -z "$BRANCH_NAME" ]; then
        echo -e "${RED}❌ Not in a git repository${NC}"
        exit 1
    fi
fi

echo "Validating branch name: $BRANCH_NAME"

# Skip validation for main/master branches
if [[ "$BRANCH_NAME" == "main" ]] || [[ "$BRANCH_NAME" == "master" ]]; then
    echo -e "${GREEN}✅ Main branch - validation skipped${NC}"
    exit 0
fi

# Valid patterns: feature/*, fix/*, hotfix/*, docs/*, refactor/*, test/*, chore/*
if [[ "$BRANCH_NAME" =~ ^(feature|fix|hotfix|docs|refactor|test|chore)/.+ ]]; then
    echo -e "${GREEN}✅ Branch name follows convention${NC}"

    # Extract and show branch type
    BRANCH_TYPE=$(echo "$BRANCH_NAME" | cut -d'/' -f1)
    BRANCH_DESC=$(echo "$BRANCH_NAME" | cut -d'/' -f2-)
    echo "  Type: $BRANCH_TYPE"
    echo "  Description: $BRANCH_DESC"

    exit 0
else
    echo -e "${RED}❌ Invalid branch name: $BRANCH_NAME${NC}"
    echo ""
    echo "Branch names must follow the pattern: {type}/{description}"
    echo ""
    echo "Valid types:"
    echo "  - feature/    New features or enhancements"
    echo "  - fix/        Bug fixes"
    echo "  - hotfix/     Urgent production fixes"
    echo "  - docs/       Documentation updates"
    echo "  - refactor/   Code refactoring"
    echo "  - test/       Test additions or improvements"
    echo "  - chore/      Maintenance tasks"
    echo ""
    echo "Examples:"
    echo "  ✅ feature/add-export-functionality"
    echo "  ✅ fix/validation-error-handling"
    echo "  ✅ docs/update-readme"
    echo "  ❌ my-feature-branch"
    echo "  ❌ fix_bug"
    echo ""
    exit 1
fi
