#!/bin/bash

# PER-007 TDD Test Runner
# This script runs the TDD workflow for PER-007 Context Flow Refactoring

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}    PER-007 TDD Workflow: Context Flow Refactoring${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Function to run tests and capture results
run_test_phase() {
    local phase=$1
    local marker=$2
    local expected_result=$3

    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Running $phase Phase Tests${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if [ "$expected_result" == "FAIL" ]; then
        echo -e "${RED}Expected: Tests should FAIL (proving issues exist)${NC}"
    else
        echo -e "${GREEN}Expected: Tests should PASS (proving fixes work)${NC}"
    fi
    echo ""

    # Run the tests
    if pytest -c tests/pytest_per007.ini -m "$marker" --tb=short -q; then
        test_result="PASS"
    else
        test_result="FAIL"
    fi

    # Check if result matches expectation
    if [ "$test_result" == "$expected_result" ]; then
        echo -e "${GREEN}✓ $phase phase completed as expected ($test_result)${NC}"
        return 0
    else
        echo -e "${RED}✗ $phase phase unexpected result: got $test_result, expected $expected_result${NC}"
        return 1
    fi
}

# Function to show implementation checklist
show_implementation_checklist() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Implementation Checklist (GREEN Phase)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "To make tests pass, implement:"
    echo ""
    echo "1. [ ] Create ContextFormatter class:"
    echo "       - services/ui/formatters.py"
    echo "       - format_ui_preview(context: EnrichedContext) -> str"
    echo "       - format_prompt_context(context: EnrichedContext) -> dict"
    echo ""
    echo "2. [ ] Update HybridContextManager:"
    echo "       - Handle 'Anders...' option correctly"
    echo "       - Add order-preserving deduplication"
    echo "       - Remove UI string processing methods"
    echo ""
    echo "3. [ ] Create ASTRA Validator:"
    echo "       - services/validation/astra_validator.py"
    echo "       - Warning-only mode (never blocking)"
    echo "       - Fuzzy matching for suggestions"
    echo ""
    echo "4. [ ] Block legacy paths:"
    echo "       - Mark old context_manager deprecated"
    echo "       - Remove prompt_context legacy route"
    echo "       - Ensure single path through DefinitionGeneratorContext"
    echo ""
}

# Main TDD Workflow
main() {
    local current_phase=${1:-"RED"}

    case $current_phase in
        "RED"|"red")
            echo -e "${RED}═══════════════════════════════════════════════════════${NC}"
            echo -e "${RED}PHASE 1: RED - Proving Issues Exist${NC}"
            echo -e "${RED}═══════════════════════════════════════════════════════${NC}"
            echo ""

            # Run RED phase tests - these SHOULD fail
            if run_test_phase "RED" "red_phase" "FAIL"; then
                echo ""
                echo -e "${GREEN}RED phase complete! Issues confirmed to exist.${NC}"
                echo ""
                show_implementation_checklist
                echo ""
                echo -e "${YELLOW}Next step: Implement fixes, then run:${NC}"
                echo -e "${YELLOW}  ./scripts/run_per007_tdd.sh GREEN${NC}"
            else
                echo ""
                echo -e "${YELLOW}⚠ Some tests already passing. Check if partial implementation exists.${NC}"
                echo -e "${YELLOW}Continue with: ./scripts/run_per007_tdd.sh GREEN${NC}"
            fi
            ;;

        "GREEN"|"green")
            echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
            echo -e "${GREEN}PHASE 2: GREEN - Validating Fixes${NC}"
            echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
            echo ""

            # Run all tests - these SHOULD pass
            if pytest -c tests/pytest_per007.ini tests/test_per007_*.py --tb=short; then
                echo ""
                echo -e "${GREEN}✓ GREEN phase complete! All tests passing.${NC}"
                echo ""
                echo -e "${YELLOW}Next step: Run performance tests:${NC}"
                echo -e "${YELLOW}  ./scripts/run_per007_tdd.sh REFACTOR${NC}"
            else
                echo ""
                echo -e "${RED}✗ Some tests still failing. Continue implementation.${NC}"
                show_implementation_checklist
            fi
            ;;

        "REFACTOR"|"refactor")
            echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
            echo -e "${BLUE}PHASE 3: REFACTOR - Performance & Quality${NC}"
            echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
            echo ""

            # Run performance tests
            echo "Running performance benchmarks..."
            pytest -c tests/pytest_per007.ini -m "performance or benchmark" --benchmark-only

            # Run anti-pattern tests
            echo ""
            echo "Checking anti-patterns are blocked..."
            pytest -c tests/pytest_per007.ini -m "antipattern"

            # Run acceptance tests
            echo ""
            echo "Running acceptance tests..."
            pytest -c tests/pytest_per007.ini -m "acceptance"

            echo ""
            echo -e "${GREEN}✓ REFACTOR phase complete!${NC}"
            echo ""
            echo -e "${YELLOW}Next step: Final validation:${NC}"
            echo -e "${YELLOW}  ./scripts/run_per007_tdd.sh CONFIRM${NC}"
            ;;

        "CONFIRM"|"confirm")
            echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
            echo -e "${GREEN}PHASE 4: CONFIRM - Final Validation${NC}"
            echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
            echo ""

            # Run complete test suite
            echo "Running complete test suite..."
            if pytest tests/test_per007_*.py -v --cov=src/services --cov-report=term-missing; then
                echo ""
                echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
                echo -e "${GREEN}✓ PER-007 Implementation COMPLETE!${NC}"
                echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
                echo ""
                echo "Summary:"
                echo "  ✓ UI preview strings blocked as data source"
                echo "  ✓ Single context processing path enforced"
                echo "  ✓ Anders... option works correctly"
                echo "  ✓ ASTRA compliance with warnings only"
                echo "  ✓ Performance targets met"
                echo "  ✓ Anti-patterns blocked"
                echo ""
                echo -e "${YELLOW}Ready for deployment!${NC}"
            else
                echo ""
                echo -e "${RED}✗ Some tests still failing. Review and fix remaining issues.${NC}"
            fi
            ;;

        "REPORT"|"report")
            echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
            echo -e "${BLUE}PER-007 Test Report${NC}"
            echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
            echo ""

            # Generate detailed test report
            pytest tests/test_per007_*.py \
                --html=reports/per007_test_report.html \
                --self-contained-html \
                --cov=src/services \
                --cov-report=html:reports/per007_coverage \
                --cov-report=term \
                -v

            echo ""
            echo "Reports generated:"
            echo "  - Test report: reports/per007_test_report.html"
            echo "  - Coverage report: reports/per007_coverage/index.html"
            ;;

        *)
            echo "PER-007 TDD Test Runner"
            echo ""
            echo "Usage: $0 [PHASE]"
            echo ""
            echo "Phases:"
            echo "  RED      - Run RED phase tests (should fail)"
            echo "  GREEN    - Run GREEN phase tests (should pass after implementation)"
            echo "  REFACTOR - Run performance and quality tests"
            echo "  CONFIRM  - Run complete validation suite"
            echo "  REPORT   - Generate test and coverage reports"
            echo ""
            echo "Example:"
            echo "  $0 RED      # Start with RED phase"
            echo "  $0 GREEN    # After implementing fixes"
            echo "  $0 REFACTOR # Optimize and clean up"
            echo "  $0 CONFIRM  # Final validation"
            ;;
    esac
}

# Run the main function
main "$@"
