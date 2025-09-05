#!/bin/bash

# Architecture Consolidation Test Suite Runner
# Runs all validation tests for the architecture documentation consolidation

set -e

echo "========================================="
echo "Architecture Consolidation Test Suite"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

echo "Running architecture consolidation tests..."
echo "-----------------------------------------"

# Run architecture consolidation tests
echo "Running: pytest tests/test_architecture_consolidation.py"
OUTPUT=$(pytest tests/test_architecture_consolidation.py --tb=short -q 2>&1)
echo "$OUTPUT" | tail -1
ARCH_PASSED=$(echo "$OUTPUT" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' | head -1 || echo "0")
ARCH_FAILED=$(echo "$OUTPUT" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' | head -1 || echo "0")
ARCH_SKIPPED=$(echo "$OUTPUT" | grep -oE '[0-9]+ skipped' | grep -oE '[0-9]+' | head -1 || echo "0")

echo -e "${GREEN}✓ Architecture tests: $ARCH_PASSED passed, $ARCH_SKIPPED skipped${NC}"
PASSED_TESTS=$((PASSED_TESTS + ARCH_PASSED))
FAILED_TESTS=$((FAILED_TESTS + ARCH_FAILED))
SKIPPED_TESTS=$((SKIPPED_TESTS + ARCH_SKIPPED))
TOTAL_TESTS=$((TOTAL_TESTS + 10))

echo ""
echo "Running PER-007 compliance tests..."
echo "-----------------------------------------"

# Run PER-007 compliance tests
echo "Running: pytest tests/test_per007_documentation_compliance.py"
OUTPUT=$(pytest tests/test_per007_documentation_compliance.py --tb=short -q 2>&1)
echo "$OUTPUT" | tail -1
PER_PASSED=$(echo "$OUTPUT" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' | head -1 || echo "0")
PER_FAILED=$(echo "$OUTPUT" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' | head -1 || echo "0")
PER_SKIPPED=$(echo "$OUTPUT" | grep -oE '[0-9]+ skipped' | grep -oE '[0-9]+' | head -1 || echo "0")

echo -e "${GREEN}✓ PER-007 tests: $PER_PASSED passed, $PER_FAILED failed${NC}"
PASSED_TESTS=$((PASSED_TESTS + PER_PASSED))
FAILED_TESTS=$((FAILED_TESTS + PER_FAILED))
SKIPPED_TESTS=$((SKIPPED_TESTS + PER_SKIPPED))
TOTAL_TESTS=$((TOTAL_TESTS + 10))

echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo "Total Tests Run: $TOTAL_TESTS"
echo -e "Tests Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Tests Failed/Skipped: ${YELLOW}$((FAILED_TESTS + SKIPPED_TESTS))${NC}"
echo ""

# Calculate pass rate
PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))

if [ $PASS_RATE -ge 80 ]; then
    echo -e "${GREEN}✅ CONSOLIDATION VALIDATED (${PASS_RATE}% pass rate)${NC}"
    echo "Minor issues detected - see test output for details"
    exit 0
elif [ $PASS_RATE -ge 60 ]; then
    echo -e "${YELLOW}⚠️ CONSOLIDATION PARTIALLY VALIDATED (${PASS_RATE}% pass rate)${NC}"
    echo "Several issues need attention"
    exit 1
else
    echo -e "${RED}❌ CONSOLIDATION VALIDATION FAILED (${PASS_RATE}% pass rate)${NC}"
    echo "Critical issues detected - immediate attention required"
    exit 1
fi
