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

# Check 2: No UI imports in services/
if rg -q "from ui\.|from src\.ui\." src/services/ 2>/dev/null; then
    echo -e "${RED}❌ Found UI imports in services/${NC}"
    rg -n "from ui\.|from src\.ui\." src/services/ 2>/dev/null || true
    echo -e "${YELLOW}   → Services must not import from UI layer${NC}"
    ((VIOLATIONS++))
fi

# Check 3: No repository imports in UI (should go through services)
if rg -q "from src\.database\.|from database\." src/ui/ 2>/dev/null; then
    echo -e "${RED}❌ Found direct database imports in UI${NC}"
    rg -n "from src\.database\.|from database\." src/ui/ 2>/dev/null || true
    echo -e "${YELLOW}   → UI should access data through services${NC}"
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
