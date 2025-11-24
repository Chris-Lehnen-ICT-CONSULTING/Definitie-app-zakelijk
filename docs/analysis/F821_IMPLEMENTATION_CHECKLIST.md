# F821 Error Fix - Implementation Checklist

**Status:** Ready for Phase 1 Implementation
**Date:** 2025-11-24
**Estimated Time:** 30 minutes
**Risk Level:** LOW (SAFE fixes only)

---

## Phase 1: Apply SAFE Fixes (15 minutes)

### Step 1.1: Fix test_performance.py (8 errors)

- [ ] Open file: `/Users/chrislehnen/Projektven/Definitie-app/tests/performance/test_performance.py`
- [ ] Locate line 19: `from utils.smart_rate_limiter import SmartRateLimiter`
- [ ] Add import after line 19:
  ```python
  from utils.cache import CacheManager
  ```
- [ ] Verify: Line 32 should now resolve `CacheManager()`
- [ ] Verify: All 8 uses of `CacheManager` (lines 32, 173, 208, 330, 490, 539, 562, 577) are now valid

**Verification:**
```bash
ruff check --select F821 tests/performance/test_performance.py
# Expected: No F821 errors for this file
```

---

### Step 1.2: Fix test_performance_comprehensive.py (1 error)

- [ ] Open file: `/Users/chrislehnen/Projektven/Definitie-app/tests/performance/test_performance_comprehensive.py`
- [ ] Locate line 24: `from utils.cache import cached, clear_cache, get_cache_stats`
- [ ] Add import after line 24:
  ```python
  from config import get_api_config
  ```
- [ ] Verify: Line 308 should now resolve `get_api_config()`

**Verification:**
```bash
ruff check --select F821 tests/performance/test_performance_comprehensive.py
# Expected: No F821 errors for this file
```

---

### Step 1.3: Fix test_astra_nora_context_compliance.py (4 errors)

- [ ] Open file: `/Users/chrislehnen/Projektven/Definitie-app/tests/compliance/test_astra_nora_context_compliance.py`
- [ ] Locate line 27: `from src.services.interfaces import GenerationRequest`
- [ ] Find commented line 29: `# from src.services.context.context_manager import ContextManager`
- [ ] Replace commented line with active import:
  ```python
  from src.services.context.context_manager import ContextManager
  ```
- [ ] Verify: All 4 uses of `ContextManager` (lines 149, 231, 254, 350) are now valid

**Verification:**
```bash
ruff check --select F821 tests/compliance/test_astra_nora_context_compliance.py
# Expected: No F821 errors for this file
```

---

### Step 1.4: Fix test_context_flow_performance.py (1 error)

- [ ] Open file: `/Users/chrislehnen/Projektven/Definitie-app/tests/performance/test_context_flow_performance.py`
- [ ] Locate line 32: `from src.services.prompts.prompt_service_v2 import PromptServiceV2`
- [ ] Find commented line 34: `# from src.services.context.context_manager import ContextManager`
- [ ] Replace commented line with active import:
  ```python
  from src.services.context.context_manager import ContextManager
  ```
- [ ] Verify: Line 73 should now resolve `ContextManager()`

**Verification:**
```bash
ruff check --select F821 tests/performance/test_context_flow_performance.py
# Expected: No F821 errors for this file
```

---

### Step 1.5: Fix test_feature_flags_context_flow.py (24 errors)

- [ ] Open file: `/Users/chrislehnen/Projektven/Definitie-app/tests/unit/test_feature_flags_context_flow.py`
- [ ] Locate line 27: `from src.services.interfaces import GenerationRequest`
- [ ] Find commented line 26: `# from src.services.feature_flags import FeatureFlags, FeatureFlagConfig`
- [ ] Replace commented line with correct import (NOTE: Path correction from comment):
  ```python
  from config.feature_flags import FeatureFlags
  ```
- [ ] Verify: All 24 uses of `FeatureFlags` are now valid
- [ ] Note: If `FeatureFlagConfig` is used, add it to the import after testing

**Verification:**
```bash
ruff check --select F821 tests/unit/test_feature_flags_context_flow.py
# Expected: No F821 errors for this file
```

---

## Phase 2: Verify All Fixes (10 minutes)

### Step 2.1: Run Ruff Check

- [ ] Run comprehensive ruff check:
  ```bash
  ruff check --select F821 tests/
  ```
- [ ] Verify output shows only `test_modern_service.py` errors (5 errors)
- [ ] Verify all other files have 0 F821 errors

**Expected Output:**
```
tests/unit/web_lookup/test_modern_service.py:35:16: F821 Undefined name `wikipedia_lookup_stub`
tests/unit/web_lookup/test_modern_service.py:41:8: F821 Undefined name `SRUServiceStub`
tests/unit/web_lookup/test_modern_service.py:66:8: F821 Undefined name `wikipedia_lookup_stub`
tests/unit/web_lookup/test_modern_service.py:72:8: F821 Undefined name `SRUServiceStub`
tests/unit/web_lookup/test_modern_service.py:92:8: F821 Undefined name `wikipedia_lookup_stub`

Found 5 errors in 1 file.
```

---

### Step 2.2: Test Imports

- [ ] Run import verification for test_performance.py:
  ```bash
  python -c "from tests.performance.test_performance import *"
  ```
- [ ] Run import verification for test_performance_comprehensive.py:
  ```bash
  python -c "from tests.performance.test_performance_comprehensive import *"
  ```
- [ ] Run import verification for test_astra_nora_context_compliance.py:
  ```bash
  python -c "from tests.compliance.test_astra_nora_context_compliance import *"
  ```
- [ ] Run import verification for test_context_flow_performance.py:
  ```bash
  python -c "from tests.performance.test_context_flow_performance import *"
  ```
- [ ] Run import verification for test_feature_flags_context_flow.py:
  ```bash
  python -c "from tests.unit.test_feature_flags_context_flow import *"
  ```

---

### Step 2.3: Run Active Tests

- [ ] Run active test file without skip marker:
  ```bash
  pytest tests/performance/test_performance.py::TestPerformanceBenchmarks -v --tb=short
  ```
  Expected: Tests run (may fail on assertions, but imports succeed)

- [ ] Run active test file:
  ```bash
  pytest tests/performance/test_performance_comprehensive.py -v --tb=short
  ```
  Expected: Tests run (may fail on assertions, but imports succeed)

---

### Step 2.4: Verify Skipped Tests Load Without Errors

- [ ] Run xfail test file (should load, then xfail):
  ```bash
  pytest tests/compliance/test_astra_nora_context_compliance.py -v --tb=short
  ```
  Expected: Tests load, show as xfail (expected failure)

- [ ] Run skip test file (should mark as skipped):
  ```bash
  pytest tests/performance/test_context_flow_performance.py -v --tb=short
  ```
  Expected: Tests load, show as skipped

- [ ] Run skip test file:
  ```bash
  pytest tests/unit/test_feature_flags_context_flow.py -v --tb=short
  ```
  Expected: Tests load, show as skipped

- [ ] Verify test_modern_service.py still skipped:
  ```bash
  pytest tests/unit/web_lookup/test_modern_service.py -v --tb=short
  ```
  Expected: "5 skipped"

---

## Phase 3: Documentation & Cleanup (5 minutes)

### Step 3.1: Update Analysis Report

- [ ] Mark all SAFE fixes as "COMPLETED" in analysis report
- [ ] Update status to "PHASE 1 COMPLETE"
- [ ] Record completion timestamp

---

### Step 3.2: Handle MEDIUM Risk (test_modern_service.py)

Choose one:

**Option A: Create Follow-Up Ticket**
- [ ] Create new ticket: "DEF-XXX: Restore web_lookup test fixtures (incremental restoration)"
- [ ] Link to current ticket (DEF-172)
- [ ] Leave `test_modern_service.py` marked as skipped
- [ ] Add note: "Fixtures exist but may be stale, to be restored in dedicated PR"

**Option B: Document in Sprint Notes**
- [ ] Add to sprint notes: "F821 fixture errors deferred - requires fixture modernization"
- [ ] Schedule review: "DEF-XXX follow-up for fixture restoration"

**Selected:** Option A (Create follow-up ticket)
- [ ] Follow-up ticket created: _________________ (fill in DEF number)

---

## Pre-Commit Checklist

Before committing changes:

- [ ] All imports added to correct locations
- [ ] No duplicate imports
- [ ] Import statements follow project style (ruff compatible)
- [ ] Test files still run without import errors
- [ ] `ruff check --select F821` passes (5 errors remaining in test_modern_service.py)
- [ ] Git status shows only modified test files
- [ ] Commit message references DEF-172

---

## Rollback Instructions

If any fix causes issues:

1. Identify affected file
2. Revert import statement
3. Return commented state
4. Report issue with specific error message

**Contact:** Review analysis report section "Root Cause" for original reasoning.

---

## Success Criteria

**Phase 1 Complete When:**
- [ ] 38/38 SAFE fixes applied
- [ ] `ruff check --select F821` shows 5 errors (only test_modern_service.py)
- [ ] No new import errors in active tests
- [ ] All modified files pass Python syntax check
- [ ] Commit created with all changes

**Phase 1 Success Threshold:** 90% (34/38 fixes required, acceptable error rate)

---

## Files Modified Summary

| File | Changes | Status |
|------|---------|--------|
| test_performance.py | +1 import | ✅ Ready |
| test_performance_comprehensive.py | +1 import | ✅ Ready |
| test_astra_nora_context_compliance.py | 1 uncommented | ✅ Ready |
| test_context_flow_performance.py | 1 uncommented | ✅ Ready |
| test_feature_flags_context_flow.py | 1 uncommented | ✅ Ready |
| test_modern_service.py | 0 (skip) | ✅ N/A |
| **Total** | **5 changes** | **✅ Ready** |

---

## Time Breakdown

| Phase | Task | Time | Status |
|-------|------|------|--------|
| 1.1 | Fix test_performance.py | 3 min | ⏳ |
| 1.2 | Fix test_performance_comprehensive.py | 2 min | ⏳ |
| 1.3 | Fix test_astra_nora_context_compliance.py | 2 min | ⏳ |
| 1.4 | Fix test_context_flow_performance.py | 2 min | ⏳ |
| 1.5 | Fix test_feature_flags_context_flow.py | 3 min | ⏳ |
| 2 | Verification & Testing | 10 min | ⏳ |
| 3 | Documentation & Cleanup | 5 min | ⏳ |
| **Total** | | **30 min** | ⏳ |

---

## Sign-Off

- [ ] Analysis reviewed and approved
- [ ] Implementation plan understood
- [ ] Ready to proceed with Phase 1

**Ready to start?** YES / NO

---

Generated: 2025-11-24
Document: `/Users/chrislehnen/Projektven/Definitie-app/docs/analysis/F821_IMPLEMENTATION_CHECKLIST.md`
