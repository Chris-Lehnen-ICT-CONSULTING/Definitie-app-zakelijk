#!/bin/bash
# Check for forbidden V1 symbols to prevent regression

echo "Checking for forbidden V1 symbols..."

FAILED=0

# Check for V1 files that should not exist
if [ -f "src/services/ai_service.py" ]; then
  echo "ERROR: V1 AI service file found (src/services/ai_service.py)"
  FAILED=1
fi

if [ -f "src/services/definition_orchestrator.py" ]; then
  echo "ERROR: V1 orchestrator file found (src/services/definition_orchestrator.py)"
  FAILED=1
fi

# Check for V1 function references
if grep -r "stuur_prompt_naar_gpt" src/ --exclude-dir=__pycache__ --include="*.py" 2>/dev/null; then
  echo "ERROR: Found references to V1 function 'stuur_prompt_naar_gpt'"
  FAILED=1
fi

# Check for V1 class references (but allow DefinitionOrchestratorV2 and Interface)
if grep -r "^class DefinitionOrchestrator[^VI]" src/ --exclude-dir=__pycache__ --include="*.py" 2>/dev/null | grep -v "DefinitionOrchestratorInterface"; then
  echo "ERROR: Found V1 DefinitionOrchestrator class (should use DefinitionOrchestratorV2)"
  FAILED=1
fi

# Check for get_ai_service imports
if grep -r "from services.ai_service import get_ai_service" src/ --exclude-dir=__pycache__ --include="*.py" 2>/dev/null; then
  echo "ERROR: Found imports of V1 get_ai_service function"
  FAILED=1
fi

# Check for USE_V2_ORCHESTRATOR feature flag
if grep -r "USE_V2_ORCHESTRATOR" src/ --exclude-dir=__pycache__ --include="*.py" 2>/dev/null; then
  echo "ERROR: Found USE_V2_ORCHESTRATOR feature flag (should be removed)"
  FAILED=1
fi

if [ $FAILED -eq 0 ]; then
  echo "✓ No forbidden V1 symbols found"
else
  echo ""
  echo "CI Gate Failed: V1 code detected!"
  exit 1
fi