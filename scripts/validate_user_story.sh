#!/bin/bash
# Validation script for User Story creation
# Usage: ./validate_user_story.sh EPIC-XXX US-XXX

set -e

EPIC_ID=$1
NEW_US_ID=$2

if [ -z "$EPIC_ID" ] || [ -z "$NEW_US_ID" ]; then
    echo "Usage: $0 EPIC-XXX US-XXX"
    exit 1
fi

echo "🔍 Validating User Story: $NEW_US_ID for $EPIC_ID"
echo "================================================"

# Check 1: Does US already exist anywhere?
echo -n "Checking if $NEW_US_ID already exists... "
if find docs/backlog -name "${NEW_US_ID}.md" 2>/dev/null | grep -q .; then
    echo "❌ FAILED"
    echo "ERROR: ${NEW_US_ID} already exists at:"
    find docs/backlog -name "${NEW_US_ID}.md" 2>/dev/null
    exit 1
else
    echo "✅ OK (not found)"
fi

# Check 2: Does EPIC exist?
echo -n "Checking if $EPIC_ID exists... "
if [ -f "docs/backlog/${EPIC_ID}/${EPIC_ID}.md" ]; then
    echo "✅ OK"
else
    echo "❌ FAILED"
    echo "ERROR: EPIC ${EPIC_ID} not found at docs/backlog/${EPIC_ID}/${EPIC_ID}.md"
    exit 1
fi

# Check 3: Is US mentioned in EPIC?
echo -n "Checking if $NEW_US_ID is planned in $EPIC_ID... "
if grep -q "$NEW_US_ID" "docs/backlog/${EPIC_ID}/${EPIC_ID}.md" 2>/dev/null; then
    echo "✅ OK (found in EPIC)"
else
    echo "⚠️  WARNING"
    echo "WARNING: ${NEW_US_ID} not found in ${EPIC_ID}.md"
    echo "Make sure to update the EPIC document!"
fi

# Check 4: Find highest US number
echo -n "Finding highest US number... "
LAST_US=$(find docs/backlog -name "US-*.md" 2>/dev/null | grep -o "US-[0-9]*" | grep -o "[0-9]*" | sort -n | tail -1)
if [ -z "$LAST_US" ]; then
    LAST_US=0
fi
echo "US-${LAST_US}"

# Check 5: Suggest next available
NEXT_US=$((LAST_US + 1))
echo "Next available ID: US-${NEXT_US}"

# Check 6: Validate ID format
echo -n "Validating ID format... "
if [[ "$NEW_US_ID" =~ ^US-[0-9]+$ ]]; then
    echo "✅ OK"
else
    echo "❌ FAILED"
    echo "ERROR: Invalid format. Use US-XXX where XXX is a number"
    exit 1
fi

# Check 7: Check for sub-story pattern (should not use US-XXXa format)
echo -n "Checking for invalid sub-story pattern... "
if [[ "$NEW_US_ID" =~ ^US-[0-9]+[a-zA-Z]$ ]]; then
    echo "❌ FAILED"
    echo "ERROR: Sub-story pattern (US-XXXa) not allowed. Use new ID instead."
    echo "Suggested: US-${NEXT_US}"
    exit 1
else
    echo "✅ OK"
fi

# Summary
echo ""
echo "================================================"
echo "✅ VALIDATION PASSED"
echo "================================================"
echo "You can create: docs/backlog/${EPIC_ID}/${NEW_US_ID}/${NEW_US_ID}.md"
echo ""
echo "Next steps:"
echo "1. Create directory: mkdir -p docs/backlog/${EPIC_ID}/${NEW_US_ID}"
echo "2. Create file: ${NEW_US_ID}.md with correct frontmatter"
echo "3. Update EPIC document if not already done"
echo ""

# Optional: Show template
echo "Template frontmatter:"
echo "---"
echo "id: ${NEW_US_ID}"
echo "epic_id: ${EPIC_ID}"
echo "title: [TODO: Add title]"
echo "status: OPEN"
echo "created_date: $(date +%Y-%m-%d)"
echo "---"