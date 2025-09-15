#!/bin/bash
# Check for legacy patterns that were removed in EPIC-010
# Run this before committing to ensure compliance with new architecture

set -e

echo "🔍 Running EPIC-010 legacy pattern checks..."
echo "============================================"

FAILED=0
WARNINGS=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check pattern
check_pattern() {
    local pattern=$1
    local description=$2
    local path=${3:-"src/"}
    local exclude_pattern=${4:-""}
    
    echo -n "Checking $description... "
    
    if [ -n "$exclude_pattern" ]; then
        MATCHES=$(rg "$pattern" "$path" --type py 2>/dev/null | grep -v "$exclude_pattern" || true)
    else
        MATCHES=$(rg "$pattern" "$path" --type py 2>/dev/null || true)
    fi
    
    if [ -n "$MATCHES" ]; then
        echo -e "${RED}❌ FAIL${NC}"
        echo "  Found in:"
        echo "$MATCHES" | head -5 | sed 's/^/    /'
        FAILED=$((FAILED + 1))
        return 1
    else
        echo -e "${GREEN}✅ PASS${NC}"
        return 0
    fi
}

# Function for warnings (not failures yet)
check_warning() {
    local pattern=$1
    local description=$2
    local path=${3:-"src/"}
    
    echo -n "Checking $description... "
    MATCHES=$(rg "$pattern" "$path" --type py 2>/dev/null || true)
    
    if [ -n "$MATCHES" ]; then
        echo -e "${YELLOW}⚠️  WARNING${NC}"
        echo "  Found in (will be error after Sprint 37):"
        echo "$MATCHES" | head -3 | sed 's/^/    /'
        WARNINGS=$((WARNINGS + 1))
        return 1
    else
        echo -e "${GREEN}✅ PASS${NC}"
        return 0
    fi
}

echo ""
echo "1. Legacy Imports Check"
echo "-----------------------"
check_pattern "from src\.models\.generation_result import" "generation_result imports" "."

echo ""
echo "2. Deprecated Attributes Check"
echo "------------------------------"
# Exclude ValidationResult.overall_score which is valid
DEPRECATED_MATCHES=$(rg "\.overall_score|\.best_iteration" src/services/ --type py 2>/dev/null | \
                    grep -v "ValidationResult" | \
                    grep -v "if __name__" | \
                    grep -v "# Test" | \
                    grep -v "# Example" | \
                    grep -v "# Demo" || true)

echo -n "Checking deprecated attributes... "
if [ -n "$DEPRECATED_MATCHES" ]; then
    echo -e "${RED}❌ FAIL${NC}"
    echo "  Found in:"
    echo "$DEPRECATED_MATCHES" | head -5 | sed 's/^/    /'
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}✅ PASS${NC}"
fi

echo ""
echo "3. String Context Check"
echo "-----------------------"
# Match request.context but NOT request.context_dict or request.context_*
check_pattern "request\.context(?!_|\w)" "string context usage"

echo ""
echo "4. Domein Field Check"
echo "--------------------"
# Exclude comments and docstrings
DOMEIN_MATCHES=$(rg "\bdomein\b" src/ --type py 2>/dev/null | \
                grep -v "^.*#.*domein" | \
                grep -v '""".*domein.*"""' | \
                grep -v "# Legacy" | \
                grep -v "# Deprecated" || true)

echo -n "Checking domein field usage... "
if [ -n "$DOMEIN_MATCHES" ]; then
    echo -e "${RED}❌ FAIL${NC}"
    echo "  Found in:"
    echo "$DOMEIN_MATCHES" | head -5 | sed 's/^/    /'
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}✅ PASS${NC}"
fi

echo ""
echo "5. Services Architecture Check"
echo "------------------------------"
check_pattern "asyncio\.run\(" "asyncio.run in services" "src/services/"
check_pattern "import streamlit|from streamlit" "streamlit imports in services" "src/services/" "# Legacy|# Deprecated"

echo ""
echo "6. Sync Wrapper Usage Check (Warning)"
echo "-------------------------------------"
# Check for sync wrappers outside of allowed locations
SYNC_VIOLATIONS=$(rg "generate_definition_sync|search_web_sources\(" src/ --type py 2>/dev/null | \
                 grep -v "async_bridge\.py" | \
                 grep -v "service_factory\.py" | \
                 grep -v "from.*import" | \
                 grep -v "def generate_definition_sync" | \
                 grep -v "def search_web_sources" || true)

echo -n "Checking direct sync wrapper calls... "
if [ -n "$SYNC_VIOLATIONS" ]; then
    echo -e "${YELLOW}⚠️  WARNING${NC}"
    echo "  These will be removed in Sprint 37:"
    echo "$SYNC_VIOLATIONS" | head -3 | sed 's/^/    /'
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✅ PASS${NC}"
fi

# Summary
echo ""
echo "============================================"
echo "                  SUMMARY                   "
echo "============================================"

if [ $FAILED -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}🎉 All checks passed!${NC}"
    echo "Your code is fully compliant with EPIC-010 architecture."
    exit 0
elif [ $FAILED -eq 0 ]; then
    echo -e "${YELLOW}✅ All required checks passed with $WARNINGS warning(s)${NC}"
    echo "Please address the warnings before Sprint 37."
    exit 0
else
    echo -e "${RED}❌ $FAILED check(s) failed${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Plus $WARNINGS warning(s)${NC}"
    fi
    echo ""
    echo "Please fix the violations before committing."
    echo "These patterns were removed in EPIC-010 refactoring."
    exit 1
fi
