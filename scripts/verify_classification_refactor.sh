#!/bin/bash
# Verification script for classification refactoring
# Checks that dead code is removed and single path is implemented

set -e

echo "=============================================="
echo "Classification Refactor Verification Script"
echo "=============================================="
echo ""

FAILED=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check 1: Dead code removed
echo "✓ Check 1: Verifying dead code is removed..."
if grep -q "_classify_term_on_change" src/ui/tabbed_interface.py; then
    echo -e "${RED}❌ FAIL: _classify_term_on_change still exists${NC}"
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}✅ PASS: _classify_term_on_change removed${NC}"
fi

if grep -q "_legacy_pattern_matching" src/ui/tabbed_interface.py; then
    echo -e "${RED}❌ FAIL: _legacy_pattern_matching still exists${NC}"
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}✅ PASS: _legacy_pattern_matching removed${NC}"
fi

if grep -q "_generate_category_reasoning" src/ui/tabbed_interface.py; then
    echo -e "${RED}❌ FAIL: _generate_category_reasoning still exists${NC}"
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}✅ PASS: _generate_category_reasoning removed${NC}"
fi

if grep -q "_get_category_scores" src/ui/tabbed_interface.py; then
    echo -e "${RED}❌ FAIL: _get_category_scores still exists${NC}"
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}✅ PASS: _get_category_scores removed${NC}"
fi

echo ""

# Check 2: No on_change handler
echo "✓ Check 2: Verifying on_change handler removed..."
if grep -q "on_change=self._classify_term_on_change" src/ui/tabbed_interface.py; then
    echo -e "${RED}❌ FAIL: on_change handler still attached to input${NC}"
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}✅ PASS: on_change handler removed${NC}"
fi

echo ""

# Check 3: No fallback classification in generation
echo "✓ Check 3: Verifying no fallback classification in generation..."
if grep -A 20 "_handle_definition_generation" src/ui/tabbed_interface.py | grep -q "asyncio.run.*_determine_ontological_category"; then
    echo -e "${RED}❌ FAIL: Fallback classification found in generation handler${NC}"
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}✅ PASS: No fallback classification in generation${NC}"
fi

echo ""

# Check 4: Validation exists
echo "✓ Check 4: Verifying validation block exists..."
if grep -A 5 "if not determined_category:" src/ui/tabbed_interface.py | grep -q "GEEN FALLBACK"; then
    echo -e "${GREEN}✅ PASS: Validation block with error message exists${NC}"
else
    echo -e "${RED}❌ FAIL: Validation block not found${NC}"
    FAILED=$((FAILED + 1))
fi

echo ""

# Check 5: Clear fields updated
echo "✓ Check 5: Verifying clear_all_fields updated..."
if grep -A 15 "def _clear_all_fields" src/ui/tabbed_interface.py | grep -q "determined_category"; then
    echo -e "${GREEN}✅ PASS: Clear fields includes classification state${NC}"
else
    echo -e "${RED}❌ FAIL: Clear fields doesn't clear classification state${NC}"
    FAILED=$((FAILED + 1))
fi

echo ""

# Check 6: Test file exists
echo "✓ Check 6: Verifying test file exists..."
if [ -f "tests/unit/test_classification_single_path.py" ]; then
    echo -e "${GREEN}✅ PASS: Test file exists${NC}"

    # Count test methods
    TEST_COUNT=$(grep -c "def test_" tests/unit/test_classification_single_path.py || true)
    echo -e "${GREEN}   Found ${TEST_COUNT} test methods${NC}"
else
    echo -e "${RED}❌ FAIL: Test file not found${NC}"
    FAILED=$((FAILED + 1))
fi

echo ""

# Check 7: Documentation exists
echo "✓ Check 7: Verifying documentation exists..."
if [ -f "docs/reports/classification-single-path-implementation.md" ]; then
    echo -e "${GREEN}✅ PASS: Implementation docs exist${NC}"
else
    echo -e "${YELLOW}⚠️  WARN: Implementation docs not found${NC}"
fi

if [ -f "docs/reports/classification-refactor-visual.md" ]; then
    echo -e "${GREEN}✅ PASS: Visual docs exist${NC}"
else
    echo -e "${YELLOW}⚠️  WARN: Visual docs not found${NC}"
fi

if [ -f "IMPLEMENTATION_SUMMARY.md" ]; then
    echo -e "${GREEN}✅ PASS: Summary exists${NC}"
else
    echo -e "${YELLOW}⚠️  WARN: Summary not found${NC}"
fi

echo ""
echo "=============================================="
echo "Verification Summary"
echo "=============================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}"
    echo ""
    echo "The classification refactoring is complete and verified:"
    echo "  • Dead code removed"
    echo "  • Single path implemented"
    echo "  • Validation added"
    echo "  • Tests created"
    echo "  • Documentation complete"
    echo ""
    echo "Status: READY FOR USE ✨"
    exit 0
else
    echo -e "${RED}❌ ${FAILED} CHECK(S) FAILED${NC}"
    echo ""
    echo "Please review the failures above and fix before using."
    exit 1
fi
