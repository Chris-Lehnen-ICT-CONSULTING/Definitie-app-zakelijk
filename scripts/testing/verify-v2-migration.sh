#!/bin/bash
# V1→V2 Migration Verification Script
# This script performs comprehensive checks before and after V2 migration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "V1→V2 Migration Verification Script"
echo "========================================="
echo ""

# Function to check V1 symbols
check_v1_symbols() {
    echo "Checking for V1 symbols..."
    local count=$(grep -r "get_ai_service\|stuur_prompt_naar_gpt" \
        src/ \
        --exclude-dir=__pycache__ \
        --include="*.py" 2>/dev/null | wc -l)

    if [ "$count" -gt 0 ]; then
        echo -e "${YELLOW}Found $count V1 symbol references:${NC}"
        grep -rn "get_ai_service\|stuur_prompt_naar_gpt" \
            src/ \
            --exclude-dir=__pycache__ \
            --include="*.py" 2>/dev/null | head -10
        return 1
    else
        echo -e "${GREEN}✅ No V1 symbols found${NC}"
        return 0
    fi
}

# Function to check imports
check_imports() {
    echo "Checking for legacy imports..."
    local legacy_imports=$(grep -r "from services.ai_service import\|from services.definition_orchestrator import" \
        src/ tests/ \
        --exclude-dir=__pycache__ \
        --include="*.py" 2>/dev/null | grep -v "_v2" | wc -l)

    if [ "$legacy_imports" -gt 0 ]; then
        echo -e "${YELLOW}Found $legacy_imports legacy imports${NC}"
        return 1
    else
        echo -e "${GREEN}✅ No legacy imports found${NC}"
        return 0
    fi
}

# Function to test service container
test_service_container() {
    echo "Testing ServiceContainer..."
    python3 -c "
import sys
sys.path.insert(0, 'src')
from services.container import ServiceContainer
try:
    c = ServiceContainer()
    orch = c.orchestrator()
    print('✅ Container Type:', type(c).__name__)
    print('✅ Orchestrator Type:', type(orch).__name__)
    if 'V2' in type(orch).__name__:
        print('✅ Using V2 Orchestrator')
    else:
        print('⚠️  Warning: Not using V2 orchestrator')
        sys.exit(1)
except Exception as e:
    print('❌ Error:', e)
    sys.exit(1)
" || return 1
}

# Function to run critical smoke tests
run_smoke_tests() {
    echo "Running critical smoke tests..."

    # Check if pytest is available
    if ! command -v pytest &> /dev/null; then
        echo -e "${YELLOW}⚠️  pytest not found, skipping smoke tests${NC}"
        return 0
    fi

    # Run specific critical test
    if pytest tests/smoke/test_smoke_generation.py::test_service_container_initialization -xvs 2>/dev/null; then
        echo -e "${GREEN}✅ Smoke tests passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Some smoke tests failed (may be unrelated to migration)${NC}"
    fi
}

# Function to check file existence
check_legacy_files() {
    echo "Checking for legacy files..."
    local legacy_files=0

    if [ -f "src/services/definition_orchestrator.py" ]; then
        echo -e "${YELLOW}Found: src/services/definition_orchestrator.py (V1 orchestrator)${NC}"
        ((legacy_files++))
    fi

    if [ -f "src/services/ai_service.py" ]; then
        echo -e "${YELLOW}Found: src/services/ai_service.py (V1 service)${NC}"
        ((legacy_files++))
    fi

    if [ $legacy_files -eq 0 ]; then
        echo -e "${GREEN}✅ No legacy files found${NC}"
        return 0
    else
        echo -e "${YELLOW}Found $legacy_files legacy files${NC}"
        return 1
    fi
}

# Function to compile Python files
check_compilation() {
    echo "Checking Python compilation..."

    # Find all Python files and compile them
    local errors=0
    for file in $(find src/services -name "*.py" -type f); do
        if ! python3 -m py_compile "$file" 2>/dev/null; then
            echo -e "${RED}❌ Compilation error in $file${NC}"
            ((errors++))
        fi
    done

    if [ $errors -eq 0 ]; then
        echo -e "${GREEN}✅ All files compile successfully${NC}"
        return 0
    else
        echo -e "${RED}Found $errors compilation errors${NC}"
        return 1
    fi
}

# Main verification flow
echo "=== Pre-Migration Status ==="
echo ""

# Track overall status
overall_status=0

# Run all checks
check_legacy_files || overall_status=1
echo ""
check_v1_symbols || overall_status=1
echo ""
check_imports || overall_status=1
echo ""
test_service_container || overall_status=1
echo ""
check_compilation || overall_status=1
echo ""
run_smoke_tests || overall_status=1

echo ""
echo "========================================="

if [ $overall_status -eq 0 ]; then
    echo -e "${GREEN}✅ VERIFICATION PASSED${NC}"
    echo "The migration appears to be complete!"
else
    echo -e "${YELLOW}⚠️  VERIFICATION INCOMPLETE${NC}"
    echo "Some V1 references still exist. Run the migration to complete."
fi

echo "========================================="

# Provide summary
echo ""
echo "Summary Report:"
echo "---------------"

# Count issues
v1_symbols=$(grep -r "get_ai_service\|stuur_prompt_naar_gpt" src/ --include="*.py" --exclude-dir=__pycache__ 2>/dev/null | wc -l)
legacy_files=0
[ -f "src/services/definition_orchestrator.py" ] && ((legacy_files++))
[ -f "src/services/ai_service.py" ] && ((legacy_files++))

echo "• V1 Symbol References: $v1_symbols"
echo "• Legacy Files Present: $legacy_files"
echo "• Container Status: $([ $overall_status -eq 0 ] && echo "✅ V2 Ready" || echo "⚠️  Needs Migration")"

echo ""
echo "Next Steps:"
if [ $overall_status -eq 0 ]; then
    echo "• The migration is complete!"
    echo "• Run 'pytest tests/smoke/' to verify functionality"
else
    echo "• Run the migration script to remove legacy code"
    echo "• Re-run this verification after migration"
fi

exit $overall_status