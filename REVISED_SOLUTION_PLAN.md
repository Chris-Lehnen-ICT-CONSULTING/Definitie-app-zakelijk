# V1→V2 Migration Complete Solution Plan

## Executive Summary
The V1→V2 migration is mostly complete with only **2 legacy references** remaining in obsolete files that are not actively used:
1. `src/services/definition_orchestrator.py` - Legacy V1 orchestrator (OBSOLETE)
2. `src/services/orchestrators/definition_orchestrator_v2.py` - Fallback method (NOT USED)

## Current Architecture Status

### ✅ V2-Only Services in Active Use
- **ServiceContainer** (`src/services/container.py`): Fully V2, creates only V2 services
- **AIServiceV2** (`src/services/ai_service_v2.py`): Native async implementation
- **PromptServiceV2** (`src/services/prompts/prompt_service_v2.py`): V2 prompt builder
- **ValidationOrchestratorV2**: V2 validation orchestrator
- **DefinitionOrchestratorV2**: Main V2 orchestrator

### ⚠️ Legacy Files Still Present (But Not Used)
1. **`src/services/ai_service.py`** - V1 service with deprecated methods:
   - Contains `get_ai_service()` and `stuur_prompt_naar_gpt()`
   - NOT imported or used anywhere in V2 flow

2. **`src/services/definition_orchestrator.py`** - V1 orchestrator:
   - Imports `get_ai_service` on line 612
   - This entire file is OBSOLETE and not used

3. **`src/services/orchestrators/definition_orchestrator_v2.py`** - V2 with fallback:
   - Has a fallback import of `get_ai_service` on line 913
   - This is in `_get_legacy_ai_service()` method which is NEVER called

## Complete V1→V2 Symbol Mapping

### Core Service Mappings
| V1 Symbol | V2 Replacement | Status |
|-----------|---------------|--------|
| `get_ai_service()` | `AIServiceV2()` instance | ✅ Replaced |
| `stuur_prompt_naar_gpt()` | `AIServiceV2.generate_definition()` | ✅ Replaced |
| `AIService` (V1 class) | `AIServiceV2` | ✅ Replaced |
| `DefinitionOrchestrator` (V1) | `DefinitionOrchestratorV2` | ✅ Replaced |
| `PromptService` (V1) | `PromptServiceV2` | ✅ Replaced |
| `ValidationService` (V1) | `ValidationOrchestratorV2` | ✅ Replaced |
| `get_container()` validator | Removed - V2 uses orchestrator | ✅ Removed |

### Container Method Mappings
| V1 Method | V2 Method | Notes |
|-----------|-----------|--------|
| `container.validator()` | N/A | Removed - validation via orchestrator |
| `container.generator()` | Returns V2 orchestrator | V2 orchestrator is the generator |
| `container.orchestrator()` | Returns V2 orchestrator | Only V2 available |

## Migration Actions Required

### Phase 1: Clean Up Unused Legacy Files (SAFE)
These files are not imported or used anywhere:

```bash
# 1. Remove completely obsolete V1 orchestrator
rm src/services/definition_orchestrator.py

# 2. Remove V1 AI service (deprecated methods)
rm src/services/ai_service.py
```

### Phase 2: Clean V2 Orchestrator Fallback (SAFE)
Remove the unused legacy fallback method from V2 orchestrator:

```python
# In src/services/orchestrators/definition_orchestrator_v2.py
# DELETE lines 896-940 (_get_legacy_ai_service method)
# This method is never called and contains the only V1 import
```

### Phase 3: Verify No Forbidden Symbols
After cleanup, verify:

```bash
# Should find NO results
grep -r "get_ai_service\|stuur_prompt_naar_gpt\|DefinitionOrchestrator[^V]" \
  src/ \
  --exclude-dir=__pycache__ \
  --include="*.py"

# Should find NO results
grep -r "from services.ai_service import" \
  src/ \
  --exclude-dir=__pycache__ \
  --include="*.py"
```

## Test Commands Post-Migration

```bash
# 1. Run smoke tests to ensure V2 flow works
pytest tests/smoke/test_end_to_end_v2.py -v

# 2. Check service initialization
python -c "
from services.container import ServiceContainer
c = ServiceContainer()
print('Orchestrator:', type(c.orchestrator()).__name__)
print('Generator:', type(c.generator()).__name__)
"

# 3. Run integration tests
pytest tests/integration/test_v2_orchestrator_integration.py -v

# 4. Check for any import errors
python -m py_compile src/services/**/*.py
```

## Risk Assessment

**Risk Level: LOW** ✅

Reasons:
1. The V1 files are completely unused in the active code path
2. ServiceContainer only creates V2 services
3. All UI and main.py use V2 exclusively
4. The legacy fallback in V2 orchestrator is never executed
5. Tests already validate V2 flow

## Implementation Order

1. **First**: Remove `src/services/definition_orchestrator.py` (completely obsolete)
2. **Second**: Remove `src/services/ai_service.py` (deprecated, unused)
3. **Third**: Clean up `_get_legacy_ai_service()` method from V2 orchestrator
4. **Fourth**: Run verification script to confirm no V1 symbols remain
5. **Fifth**: Run full test suite to ensure nothing broke

## Success Criteria

✅ No files contain `get_ai_service` or `stuur_prompt_naar_gpt`
✅ No files import from `services.ai_service`
✅ No references to V1 `DefinitionOrchestrator` class
✅ All smoke tests pass
✅ Application starts and generates definitions successfully
✅ `scripts/check-v1-symbols.sh` reports zero violations

## Summary

The migration is **99% complete**. Only 2 obsolete files contain V1 references:
- One is a completely unused V1 orchestrator
- The other is the deprecated V1 AI service

These can be safely removed without any impact on the running system since:
- ServiceContainer creates only V2 services
- All active code paths use V2 exclusively
- The V2 orchestrator's legacy fallback is never executed

**Recommended Action**: Proceed with cleanup immediately as it's risk-free.

