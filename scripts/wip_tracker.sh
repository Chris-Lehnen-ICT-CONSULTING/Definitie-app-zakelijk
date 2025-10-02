#!/bin/bash
# WIP Tracker: Real-time visibility into work in progress
# Shows all stories currently being worked on (status: in_progress or open with recent activity)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKLOG_DIR="$PROJECT_ROOT/docs/backlog"

echo -e "${CYAN}🚧 Work In Progress Tracker${NC}"
echo "======================================"
echo ""

# Check if backlog directory exists
if [ ! -d "$BACKLOG_DIR" ]; then
    echo -e "${RED}❌ Backlog directory not found: $BACKLOG_DIR${NC}"
    exit 1
fi

# Track counts
IN_PROGRESS_COUNT=0
OPEN_COUNT=0
TOTAL_COUNT=0

# Function to extract frontmatter field
extract_field() {
    local file="$1"
    local field="$2"
    grep "^$field:" "$file" 2>/dev/null | cut -d':' -f2- | xargs || echo ""
}

# Find all user stories
while IFS= read -r -d '' story_file; do
    # Extract metadata
    STATUS=$(extract_field "$story_file" "status")
    TITEL=$(extract_field "$story_file" "titel")
    EPIC=$(extract_field "$story_file" "epic")
    OWNER=$(extract_field "$story_file" "owner")
    STORY_ID=$(basename "$(dirname "$story_file")")

    # Check if in progress or recently opened
    if [ "$STATUS" == "in_progress" ]; then
        echo -e "${YELLOW}🔨 $STORY_ID${NC}: $TITEL"
        echo -e "   Epic: ${BLUE}$EPIC${NC} | Owner: ${CYAN}$OWNER${NC}"
        echo -e "   Status: ${YELLOW}IN PROGRESS${NC}"

        # Check for associated files
        STORY_DIR=$(dirname "$story_file")
        TEST_FILES=$(find "$STORY_DIR" -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ')
        if [ "$TEST_FILES" -gt 0 ]; then
            echo -e "   Tests: ${GREEN}$TEST_FILES file(s)${NC}"
        fi

        echo ""
        ((IN_PROGRESS_COUNT++))
        ((TOTAL_COUNT++))

    elif [ "$STATUS" == "open" ]; then
        # Check if recently modified (within last 7 days)
        if [ -n "$(find "$story_file" -mtime -7 2>/dev/null)" ]; then
            echo -e "${GREEN}📝 $STORY_ID${NC}: $TITEL"
            echo -e "   Epic: ${BLUE}$EPIC${NC} | Owner: ${CYAN}$OWNER${NC}"
            echo -e "   Status: ${GREEN}OPEN (recently updated)${NC}"
            echo ""
            ((OPEN_COUNT++))
            ((TOTAL_COUNT++))
        fi
    fi
done < <(find "$BACKLOG_DIR" -type f -name "US-*.md" -print0)

# Summary
echo "======================================"
echo -e "${CYAN}📊 Summary${NC}"
echo "  In Progress: $IN_PROGRESS_COUNT"
echo "  Recently Opened: $OPEN_COUNT"
echo "  Total WIP: $TOTAL_COUNT"
echo ""

# Show TDD phase if available
if [ -f "$PROJECT_ROOT/.tdd-phase" ]; then
    PHASE=$(cat "$PROJECT_ROOT/.tdd-phase")
    case $PHASE in
        RED)
            echo -e "  TDD Phase: ${RED}🔴 RED${NC} (Writing failing tests)"
            ;;
        GREEN)
            echo -e "  TDD Phase: ${GREEN}🟢 GREEN${NC} (Making tests pass)"
            ;;
        REFACTOR)
            echo -e "  TDD Phase: ${BLUE}🔵 REFACTOR${NC} (Improving code)"
            ;;
    esac
    echo ""
fi

# Helpful commands
if [ $TOTAL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ No work in progress!${NC}"
    echo ""
    echo "To start a new story:"
    echo "  1. Find a story: ls docs/backlog/EPIC-*/US-*/"
    echo "  2. Set status to 'in_progress' in the frontmatter"
    echo "  3. Run: python scripts/phase-tracker.py set RED"
else
    echo "Helpful commands:"
    echo "  • Check TDD phase: python scripts/phase-tracker.py"
    echo "  • Run workflow guard: python scripts/workflow-guard.py"
    echo "  • View story: cat docs/backlog/EPIC-XXX/US-XXX/US-XXX.md"
fi

echo ""
