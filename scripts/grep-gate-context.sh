#!/bin/bash
# grep-gate-context.sh - Enforce single context entry point (US-043)
#
# This script prevents regression by detecting multiple context entry points.
# Only HybridContextManager should handle context mapping.
#
# Usage: bash scripts/grep-gate-context.sh
# Returns: 0 if compliant, 1 if violations found

set -e

echo "🔍 Checking for context entry point violations (US-043)..."

VIOLATIONS=0
VIOLATIONS_DETAILS=""

# Check for direct context mapping outside HybridContextManager
# Exclude the deprecated method and this script
echo "Checking for unauthorized context mapping patterns..."

# Pattern 1: Direct creation of EnrichedContext outside HybridContextManager
if grep -r "= EnrichedContext(" src/ --include="*.py" | \
   grep -v "definition_generator_context.py" | \
   grep -v "_DEPRECATED" | \
   grep -v "# US-043" | \
   grep -v "# Legacy code" > /dev/null 2>&1; then
    echo "❌ Found direct EnrichedContext creation outside HybridContextManager:"
    grep -r "= EnrichedContext(" src/ --include="*.py" | \
       grep -v "definition_generator_context.py" | \
       grep -v "_DEPRECATED" | \
       grep -v "# US-043" | \
       grep -v "# Legacy code" | head -5
    VIOLATIONS=$((VIOLATIONS + 1))
    VIOLATIONS_DETAILS="${VIOLATIONS_DETAILS}\n- Direct EnrichedContext creation"
fi

# Pattern 2: Context dict building with specific keys
CONTEXT_KEYS="organisatorisch|juridisch|wettelijk"
if grep -r "\"${CONTEXT_KEYS}\".*\[\]" src/ --include="*.py" | \
   grep -v "definition_generator_context.py" | \
   grep -v "context_manager.py" | \
   grep -v "_DEPRECATED_convert_request_to_context" | \
   grep -v "# US-043" | \
   grep -v "test_" > /dev/null 2>&1; then
    echo "❌ Found manual context dict building outside authorized modules:"
    grep -r "\"${CONTEXT_KEYS}\".*\[\]" src/ --include="*.py" | \
       grep -v "definition_generator_context.py" | \
       grep -v "context_manager.py" | \
       grep -v "_DEPRECATED_convert_request_to_context" | \
       grep -v "# US-043" | \
       grep -v "test_" | head -5
    VIOLATIONS=$((VIOLATIONS + 1))
    VIOLATIONS_DETAILS="${VIOLATIONS_DETAILS}\n- Manual context dict building"
fi

# Pattern 3: Check for usage of deprecated method (should warn)
if grep -r "_convert_request_to_context" src/ --include="*.py" | \
   grep -v "def _DEPRECATED_convert_request_to_context" | \
   grep -v "# US-043" > /dev/null 2>&1; then
    echo "⚠️  Warning: Found usage of deprecated _convert_request_to_context method:"
    grep -r "_convert_request_to_context" src/ --include="*.py" | \
       grep -v "def _DEPRECATED_convert_request_to_context" | \
       grep -v "# US-043" | head -5
    # This is a warning, not a hard failure
fi

# Pattern 4: Direct session state context manipulation (should go through ContextManager)
# Exclude string literals in comments/documentation  
if grep -r "st\.session_state\[.*context.*\]\s*=\s*[^\"']" src/ --include="*.py" | \
   grep -v "context_manager.py" | \
   grep -v "context_selector.py" | \
   grep -v "context_adapter.py" | \
   grep -v "# US-043" | \
   grep -v "test_" > /dev/null 2>&1; then
    echo "❌ Found direct session state context manipulation:"
    grep -r "st\.session_state\[.*context.*\]\s*=\s*[^\"']" src/ --include="*.py" | \
       grep -v "context_manager.py" | \
       grep -v "context_selector.py" | \
       grep -v "context_adapter.py" | \
       grep -v "# US-043" | \
       grep -v "test_" | head -5
    VIOLATIONS=$((VIOLATIONS + 1))
    VIOLATIONS_DETAILS="${VIOLATIONS_DETAILS}\n- Direct session state context manipulation"
fi

# Check positive patterns - ensure HybridContextManager is used
echo "Checking for proper HybridContextManager usage..."

# Verify HybridContextManager is imported where PromptServiceV2 is used
if ! grep -r "from.*definition_generator_context import.*HybridContextManager" src/services/prompts/prompt_service_v2.py > /dev/null 2>&1; then
    echo "❌ PromptServiceV2 does not import HybridContextManager"
    VIOLATIONS=$((VIOLATIONS + 1))
    VIOLATIONS_DETAILS="${VIOLATIONS_DETAILS}\n- Missing HybridContextManager import"
fi

# Verify build_enriched_context is called in PromptServiceV2
if ! grep -r "context_manager.build_enriched_context" src/services/prompts/prompt_service_v2.py > /dev/null 2>&1; then
    echo "❌ PromptServiceV2 does not use HybridContextManager.build_enriched_context"
    VIOLATIONS=$((VIOLATIONS + 1))
    VIOLATIONS_DETAILS="${VIOLATIONS_DETAILS}\n- Missing build_enriched_context usage"
fi

# Summary
echo ""
echo "========================================"
if [ $VIOLATIONS -eq 0 ]; then
    echo "✅ Context entry point check PASSED!"
    echo "All context mapping goes through the single authorized path."
    echo ""
    echo "Authorized context mappers:"
    echo "  - HybridContextManager.build_enriched_context()"
    echo "  - ContextManager.set_context()"
    echo ""
    echo "Architecture compliance: US-043 ✓"
else
    echo "❌ Context entry point check FAILED!"
    echo ""
    echo "Found $VIOLATIONS violation(s):$VIOLATIONS_DETAILS"
    echo ""
    echo "To fix:"
    echo "1. Use HybridContextManager.build_enriched_context() for context mapping"
    echo "2. Use ContextManager for session state context operations"
    echo "3. Remove any direct EnrichedContext creation"
    echo "4. Remove manual context dict building"
    echo ""
    echo "See US-043 for architecture requirements."
fi
echo "========================================"

exit $VIOLATIONS