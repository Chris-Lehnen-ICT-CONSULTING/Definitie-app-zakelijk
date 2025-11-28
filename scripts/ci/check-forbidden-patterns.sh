#!/bin/bash
# Forbidden Patterns Check Script
# Checks for architectural violations and forbidden imports
# Usage: ./check-forbidden-patterns.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚫 Checking for forbidden patterns..."

VIOLATIONS=0

# Check 1: No streamlit imports in services/
if rg -q "import streamlit|from streamlit" src/services/ 2>/dev/null; then
    echo -e "${RED}❌ Found streamlit imports in services/${NC}"
    rg -n "import streamlit|from streamlit" src/services/ 2>/dev/null || true
    echo -e "${YELLOW}   → Services must not depend on UI framework${NC}"
    ((VIOLATIONS++))
fi

# Check 2: No UI imports in services/utils
# DEF-198: Clean architecture fix - services now use utils/progress_callback
#   instead of ui.helpers.progress_context. No more layer violations.
# DEF-173: Exclude approved bridge modules (lazy imports + soft-fail pattern):
# - voorbeelden_debug.py: Debug utility with callback pattern (soft-fail)
UI_VIOLATIONS=$(rg -n \
    --glob='!src/utils/voorbeelden_debug.py' \
    "from ui\.|from src\.ui\." src/services/ src/utils/ 2>/dev/null || true)
if [ -n "$UI_VIOLATIONS" ]; then
    echo -e "${RED}❌ Found UI imports in services/utils${NC}"
    echo "$UI_VIOLATIONS"
    echo -e "${YELLOW}   → Services/utils must not import from UI layer${NC}"
    ((VIOLATIONS++))
fi

# Check 3: No top-level repository imports in UI (should go through services)
# DEF-175: Only match non-indented imports (excludes TYPE_CHECKING and lazy imports)
DB_VIOLATIONS=$(rg -n "^from (src\.)?database\." src/ui/ 2>/dev/null || true)
if [ -n "$DB_VIOLATIONS" ]; then
    echo -e "${RED}❌ Found direct database imports in UI${NC}"
    echo "$DB_VIOLATIONS"
    echo -e "${YELLOW}   → UI should access data through services${NC}"
    ((VIOLATIONS++))
fi

# Check 3b: No direct get_container() imports in UI (use cached_services instead)
# DEF-202: UI components must use get_cached_service_container() for singleton guarantee
CONTAINER_VIOLATIONS=$(rg -n "from (src\.)?services\.container import.*get_container" src/ui/ 2>/dev/null || true)
if [ -n "$CONTAINER_VIOLATIONS" ]; then
    echo -e "${RED}❌ Found direct get_container() imports in UI${NC}"
    echo "$CONTAINER_VIOLATIONS"
    echo -e "${YELLOW}   → Use 'from ui.cached_services import get_cached_service_container' instead${NC}"
    ((VIOLATIONS++))
fi

# Check 4: No asyncio.run() in services (use async/await properly)
if rg -q "asyncio\.run\(" src/services/ 2>/dev/null; then
    echo -e "${RED}❌ Found asyncio.run() in services/${NC}"
    rg -n "asyncio\.run\(" src/services/ 2>/dev/null || true
    echo -e "${YELLOW}   → Use async/await properly without asyncio.run()${NC}"
    ((VIOLATIONS++))
fi

# Check 5: No hardcoded API keys
if rg -q "api_key\s*=\s*[\"'][A-Za-z0-9]" --type py 2>/dev/null; then
    echo -e "${RED}❌ Potential hardcoded API key found${NC}"
    rg -n "api_key\s*=\s*[\"'][A-Za-z0-9]" --type py 2>/dev/null || true
    echo -e "${YELLOW}   → Use environment variables for secrets${NC}"
    ((VIOLATIONS++))
fi

# Check 6: No V1 references (we're on V2)
if rg -q "ValidationOrchestratorV1|OrchestratorV1" --type py 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Found V1 orchestrator references${NC}"
    rg -n "ValidationOrchestratorV1|OrchestratorV1" --type py 2>/dev/null || true
    echo -e "${YELLOW}   → Should use V2 orchestrator${NC}"
    # Warning only, not a blocking violation
fi

# Summary
if [ $VIOLATIONS -eq 0 ]; then
    echo -e "${GREEN}✅ No forbidden patterns found${NC}"
    exit 0
else
    echo -e "${RED}❌ Found $VIOLATIONS forbidden pattern violation(s)${NC}"
    echo ""
    echo "Forbidden patterns enforce architectural boundaries:"
    echo "  - Services: Pure business logic, no UI dependencies"
    echo "  - UI: No direct database access, use services"
    echo "  - Security: No hardcoded secrets"
    echo ""
    exit 1
fi
