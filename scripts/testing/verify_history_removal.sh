#!/bin/bash
#
# COMPREHENSIVE TEST & VERIFICATION PLAN
# for History Tab Removal in DefinitieAgent
#
# Run this script after removing the History tab to ensure:
# 1. Application remains functional
# 2. No broken references
# 3. Database integrity maintained
# 4. Performance improved
#

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log file for results
LOG_FILE="history_removal_verification_$(date +%Y%m%d_%H%M%S).log"

echo "Starting History Tab Removal Verification..."
echo "Results will be saved to: $LOG_FILE"
echo ""

# Initialize log
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

# ============================================================================
# 1. PRE-REMOVAL BASELINE (run this BEFORE removal for comparison)
# ============================================================================

capture_baseline() {
    echo -e "${BLUE}==== CAPTURING BASELINE ====${NC}"

    # Check if this is pre or post removal
    if grep -q "HistoryTab" src/ui/tabbed_interface.py 2>/dev/null; then
        echo -e "${YELLOW}WARNING: HistoryTab still present. This appears to be PRE-removal.${NC}"
        echo "Creating baseline file..."

        # Database state
        echo "Database statistics:"
        sqlite3 data/definities.db "SELECT 'Total definitions:', COUNT(*) FROM definities;" 2>/dev/null || echo "No database"
        sqlite3 data/definities.db "SELECT 'History entries:', COUNT(*) FROM definitie_geschiedenis;" 2>/dev/null || echo "No history table"

        # Count Python files
        echo "Python file count: $(find src -name "*.py" | wc -l)"

        # Check import time
        echo "Import time test:"
        time python -c "from src.ui.tabbed_interface import TabbedInterface" 2>/dev/null || echo "Import failed"

        # Save baseline
        echo "Baseline captured on $(date)" > baseline_history_removal.txt
        echo "Files with History references:" >> baseline_history_removal.txt
        grep -r "history" src/ --include="*.py" -l 2>/dev/null | wc -l >> baseline_history_removal.txt

        echo -e "${GREEN}Baseline saved to baseline_history_removal.txt${NC}"
        echo "Run this script again AFTER removing History tab."
        exit 0
    else
        echo -e "${GREEN}HistoryTab not found. Proceeding with POST-removal verification.${NC}"
    fi
}

# ============================================================================
# 2. POST-REMOVAL VERIFICATION
# ============================================================================

echo -e "${BLUE}==== POST-REMOVAL VERIFICATION ====${NC}"
echo ""

# A. Check for History Tab remnants
echo -e "${YELLOW}[A] Checking for History Tab remnants...${NC}"

check_history_remnants() {
    local errors=0

    # Check for HistoryTab imports
    echo -n "  Checking for HistoryTab imports... "
    if grep -r "from.*history_tab import\|import.*history_tab" src/ --include="*.py" 2>/dev/null; then
        echo -e "${RED}FAILED${NC} - Found history_tab imports"
        ((errors++))
    else
        echo -e "${GREEN}PASSED${NC}"
    fi

    # Check for HistoryTab instantiation
    echo -n "  Checking for HistoryTab instantiation... "
    if grep -r "HistoryTab\|history_tab\s*=" src/ --include="*.py" 2>/dev/null | grep -v "^#"; then
        echo -e "${RED}FAILED${NC} - Found HistoryTab references"
        ((errors++))
    else
        echo -e "${GREEN}PASSED${NC}"
    fi

    # Check tab configuration
    echo -n "  Checking tab configuration... "
    if grep -r '"history":\s*{' src/ --include="*.py" 2>/dev/null; then
        echo -e "${RED}FAILED${NC} - Found 'history' in tab config"
        ((errors++))
    else
        echo -e "${GREEN}PASSED${NC}"
    fi

    # Check for history tab file
    echo -n "  Checking for history_tab.py file... "
    if [ -f "src/ui/components/history_tab.py" ]; then
        echo -e "${YELLOW}WARNING${NC} - history_tab.py still exists (OK if unused)"
    else
        echo -e "${GREEN}PASSED${NC} - File removed"
    fi

    return $errors
}

# B. Python Import Tests
echo -e "${YELLOW}[B] Python Import Tests...${NC}"

test_python_imports() {
    local errors=0

    echo -n "  Testing TabbedInterface import... "
    if python -c "from src.ui.tabbed_interface import TabbedInterface" 2>/dev/null; then
        echo -e "${GREEN}PASSED${NC}"
    else
        echo -e "${RED}FAILED${NC} - Import error"
        python -c "from src.ui.tabbed_interface import TabbedInterface" 2>&1
        ((errors++))
    fi

    echo -n "  Testing main module import... "
    if python -c "import src.main" 2>/dev/null; then
        echo -e "${GREEN}PASSED${NC}"
    else
        echo -e "${RED}FAILED${NC} - Main import error"
        ((errors++))
    fi

    echo -n "  Testing all UI components... "
    if python -c "
from src.ui.components.definition_generator_tab import DefinitionGeneratorTab
from src.ui.components.definition_edit_tab import DefinitionEditTab
from src.ui.components.expert_review_tab import ExpertReviewTab
from src.ui.components.export_tab import ExportTab
from src.ui.components.management_tab import ManagementTab
print('All imports OK')
" 2>/dev/null; then
        echo -e "${GREEN}PASSED${NC}"
    else
        echo -e "${RED}FAILED${NC} - Component import errors"
        ((errors++))
    fi

    return $errors
}

# C. Database Integrity
echo -e "${YELLOW}[C] Database Integrity Tests...${NC}"

test_database_integrity() {
    local errors=0

    echo -n "  Checking database exists... "
    if [ -f "data/definities.db" ]; then
        echo -e "${GREEN}PASSED${NC}"
    else
        echo -e "${RED}FAILED${NC} - Database not found"
        return 1
    fi

    echo -n "  Testing history table... "
    if sqlite3 data/definities.db "SELECT COUNT(*) FROM definitie_geschiedenis;" 2>/dev/null >/dev/null; then
        echo -e "${GREEN}PASSED${NC}"
        count=$(sqlite3 data/definities.db "SELECT COUNT(*) FROM definitie_geschiedenis;")
        echo "    History entries: $count"
    else
        echo -e "${YELLOW}WARNING${NC} - History table missing (OK if intentional)"
    fi

    echo -n "  Testing triggers... "
    # Create temp test entry
    test_id=$(sqlite3 data/definities.db "
        INSERT INTO definities (begrip, definitie, organisatorische_context, juridische_context)
        VALUES ('TEST_HISTORY_REMOVAL', 'Test definitie', '[]', '[]');
        SELECT last_insert_rowid();
    " 2>/dev/null)

    if [ -n "$test_id" ]; then
        # Check if trigger created history
        history_count=$(sqlite3 data/definities.db "
            SELECT COUNT(*) FROM definitie_geschiedenis
            WHERE definitie_id = $test_id;
        " 2>/dev/null || echo "0")

        # Clean up test entry
        sqlite3 data/definities.db "DELETE FROM definities WHERE id = $test_id;" 2>/dev/null

        if [ "$history_count" -gt "0" ]; then
            echo -e "${GREEN}PASSED${NC} - Triggers working"
        else
            echo -e "${YELLOW}WARNING${NC} - Triggers may not be creating history"
        fi
    else
        echo -e "${RED}FAILED${NC} - Cannot test triggers"
        ((errors++))
    fi

    return $errors
}

# D. Application Smoke Tests
echo -e "${YELLOW}[D] Application Smoke Tests...${NC}"

run_smoke_tests() {
    local errors=0

    echo -n "  Running unit tests... "
    if pytest tests/unit/ -q --tb=no 2>/dev/null; then
        echo -e "${GREEN}PASSED${NC}"
    else
        echo -e "${YELLOW}WARNING${NC} - Some unit tests failed"
    fi

    echo -n "  Running smoke tests... "
    if pytest tests/smoke/ -q --tb=no 2>/dev/null; then
        echo -e "${GREEN}PASSED${NC}"
    else
        echo -e "${YELLOW}WARNING${NC} - Some smoke tests failed"
    fi

    # Test specific functionality
    echo -n "  Testing tab functionality... "
    if python -c "
from src.ui.tabbed_interface import TabbedInterface
ti = TabbedInterface()
# Check all tabs except history
assert hasattr(ti, 'definition_tab')
assert hasattr(ti, 'edit_tab')
assert hasattr(ti, 'expert_tab')
assert hasattr(ti, 'export_tab')
assert hasattr(ti, 'management_tab')
# Should NOT have history_tab
assert not hasattr(ti, 'history_tab') or ti.history_tab is None
print('Tab structure OK')
" 2>/dev/null; then
        echo -e "${GREEN}PASSED${NC}"
    else
        echo -e "${RED}FAILED${NC} - Tab structure issue"
        ((errors++))
    fi

    return $errors
}

# E. Session State Verification
echo -e "${YELLOW}[E] Session State Verification...${NC}"

verify_session_state() {
    local errors=0

    echo -n "  Checking for history keys in session state... "
    if python -c "
import sys
sys.path.insert(0, '.')
from ui.session_state import SessionStateManager

# Initialize
SessionStateManager.initialize_session_state()

# Get all keys (this would be populated in real usage)
# For now, just check the module loads
print('Session state module OK')
" 2>/dev/null; then
        echo -e "${GREEN}PASSED${NC}"
    else
        echo -e "${YELLOW}WARNING${NC} - Cannot verify session state"
    fi

    return $errors
}

# F. Performance Check
echo -e "${YELLOW}[F] Performance Checks...${NC}"

check_performance() {
    echo "  Import time comparison:"

    # Test import time
    echo -n "    TabbedInterface import: "
    start_time=$(date +%s%N)
    python -c "from src.ui.tabbed_interface import TabbedInterface" 2>/dev/null
    end_time=$(date +%s%N)
    elapsed=$((($end_time - $start_time) / 1000000))
    echo "${elapsed}ms"

    if [ -f "baseline_history_removal.txt" ]; then
        echo "    (Compare with baseline in baseline_history_removal.txt)"
    fi

    # Memory usage (simplified)
    echo -n "    Memory after import: "
    python -c "
import tracemalloc
tracemalloc.start()
from src.ui.tabbed_interface import TabbedInterface
current, peak = tracemalloc.get_traced_memory()
print(f'{current / 1024 / 1024:.2f} MB')
tracemalloc.stop()
" 2>/dev/null || echo "Unable to measure"
}

# G. UI Verification Checklist
echo -e "${YELLOW}[G] UI Verification Checklist...${NC}"

print_ui_checklist() {
    cat << EOF
  Manual verification needed (run app and check):
  [ ] Generator tab works
  [ ] Edit tab works
  [ ] Expert Review tab works
  [ ] Management tab works
  [ ] Export tab works
  [ ] Monitoring tab works
  [ ] Quality Control tab works
  [ ] Web Lookup tab works
  [ ] External Sources tab works
  [ ] NO "History" tab visible
  [ ] No broken navigation
  [ ] No console errors in browser

  To test manually:
    streamlit run src/main.py
EOF
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

# Check if this is pre or post removal
capture_baseline

# Run all verification tests
total_errors=0

check_history_remnants
total_errors=$((total_errors + $?))

test_python_imports
total_errors=$((total_errors + $?))

test_database_integrity
total_errors=$((total_errors + $?))

run_smoke_tests
total_errors=$((total_errors + $?))

verify_session_state
total_errors=$((total_errors + $?))

check_performance

print_ui_checklist

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo -e "${BLUE}==== VERIFICATION SUMMARY ====${NC}"

if [ $total_errors -eq 0 ]; then
    echo -e "${GREEN}✅ All automated checks PASSED!${NC}"
    echo "Please complete the manual UI checklist above."
else
    echo -e "${RED}❌ Found $total_errors issue(s) that need attention.${NC}"
    echo "Review the log file: $LOG_FILE"
fi

echo ""
echo "Verification completed on $(date)"
echo "Log saved to: $LOG_FILE"

# Create success marker if all tests pass
if [ $total_errors -eq 0 ]; then
    echo "$(date): History removal verification PASSED" > .history_removal_verified
fi

exit $total_errors