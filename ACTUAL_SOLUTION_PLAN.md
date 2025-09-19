# ACTUAL Solution Plan - Based on Real Investigation

## Investigation Summary

After thorough analysis, the REVISED_SOLUTION_PLAN was wrong. The actual problems are:

1. **Services have NO Streamlit dependencies** - The plan was incorrect
2. **ui_helpers.py is properly organized DRY code** - Not a GOD object
3. **ValidationResult.score exists** - No .status problem
4. **MockStreamlit already has cache_data** - No missing mock needed
5. **Real issues are different from what was assumed**

## ACTUAL Problems Found

### 1. Missing Module: ai_toetser.validators
- **Location**: `tests/unit/test_modular_toetser.py:54`
- **Error**: `ModuleNotFoundError: No module named 'ai_toetser.validators'`
- **Reality**: ai_toetser/ only contains: `__init__.py`, `toetser.py`, `modular_toetser.py`, `json_validator_loader.py`
- **Impact**: Test fails trying to import non-existent module

### 2. Forbidden V1 Symbols Still in Use
- **Files affected**:
  - `src/services/ai_service.py` - uses get_ai_service, stuur_prompt_naar_gpt
  - `src/services/definition_orchestrator.py` - uses V1 DefinitionOrchestrator class
  - `src/services/orchestrators/definition_orchestrator_v2.py` - imports from V1 ai_service
- **Impact**: CI test `test_forbidden_symbols.py` fails

### 3. Test Collection Warnings
- **Location**: `tests/integration/test_modular_prompts.py`
- **Issue**: @dataclass classes named TestCase and TestResult confuse pytest
- **Impact**: Pytest tries to collect them as test classes

### 4. Cache Expiration Test Failure
- **Location**: `tests/unit/test_cache_system.py::TestCacheManager::test_cache_expiration_in_manager`
- **Impact**: One unit test failing

### 5. Business Logic Parity Test Failure
- **Location**: `tests/integration/test_business_logic_parity.py::TestBusinessLogicParity::test_validation_rules_consistency`
- **Impact**: Integration test failing

## Root Cause Analysis

The fundamental issue is **incomplete refactoring** from V1 to V2 architecture:
- V2 services exist but still reference V1 components
- Tests reference modules that were never created during refactoring
- The refactoring process wasn't completed, leaving hybrid V1/V2 code

## Solution Strategy

### Quick Fixes (Immediate)

#### 1. Fix Missing validators Module (5 min)
```python
# Option A: Remove the failing test (it tests non-existent code)
# Option B: Create minimal ai_toetser/validators.py with ValidationContext
```

#### 2. Fix Test Collection Warnings (2 min)
- Rename TestCase → ValidationTestCase
- Rename TestResult → ValidationTestResult

#### 3. Complete V1 → V2 Migration (30 min)
- Update all V1 references to use V2 services
- Remove get_ai_service() calls, use ServiceContainer instead
- Remove V1 imports from V2 modules

### Medium-term Fixes (if needed)

#### 4. Fix Cache Test (10 min)
- Debug why cache expiration test fails
- Likely a timing issue or incorrect mock

#### 5. Fix Business Logic Parity Test (15 min)
- Check what consistency issue exists
- Align V1 and V2 validation rules

## Implementation Priority

1. **First**: Fix test imports (remove/fix ai_toetser.validators reference)
2. **Second**: Complete V1→V2 migration to fix forbidden symbols
3. **Third**: Fix pytest collection warnings
4. **Fourth**: Fix remaining test failures if needed

## Key Insights

- The codebase is in a **transitional state** between V1 and V2
- Tests were written for planned modules that were never created
- The refactoring follows CLAUDE.md: "Refactor, geen backwards compatibility"
- This is a single-user app, so we can refactor aggressively

## Next Steps

1. Start with the quick fixes to get tests passing
2. Complete the V1→V2 migration
3. Clean up any remaining test issues
4. Document the completed migration

## Success Criteria

- All tests pass (or are properly skipped)
- No forbidden V1 symbols in V2 code
- Clean pytest collection without warnings
- Consistent V2 architecture throughout

## Time Estimate

- Quick fixes: ~40 minutes
- Full cleanup: ~1-2 hours
- With testing: ~2-3 hours total

This plan is based on **actual code investigation** not assumptions.