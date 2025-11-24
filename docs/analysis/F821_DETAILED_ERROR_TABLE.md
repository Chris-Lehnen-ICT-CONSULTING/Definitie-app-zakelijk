# F821 Errors - Detailed Line-by-Line Reference

## test_astra_nora_context_compliance.py (4 errors)

| Line | Error | Type | Root Cause | Fix | Status |
|------|-------|------|-----------|-----|--------|
| 149 | `ContextManager()` | Undefined name | Import commented out (line 29) | `from src.services.context.context_manager import ContextManager` | ✅ SAFE |
| 231 | `ContextManager()` | Undefined name | Import commented out (line 29) | `from src.services.context.context_manager import ContextManager` | ✅ SAFE |
| 254 | `ContextManager()` | Undefined name | Import commented out (line 29) | `from src.services.context.context_manager import ContextManager` | ✅ SAFE |
| 350 | `ContextManager()` | Undefined name | Import commented out (line 29) | `from src.services.context.context_manager import ContextManager` | ✅ SAFE |

**File Status:** All tests marked as `@pytest.mark.xfail` (expected failure, US-041/042/043 pending)

---

## test_context_flow_performance.py (1 error)

| Line | Error | Type | Root Cause | Fix | Status |
|------|-------|------|-----------|-----|--------|
| 73 | `ContextManager()` | Undefined name | Import commented out (line 34) | `from src.services.context.context_manager import ContextManager` | ✅ SAFE |

**File Status:** Class marked with `@pytest.mark.skip` (context module not implemented, US-041/042/043 pending)

---

## test_performance.py (8 errors)

| Line | Error | Type | Root Cause | Fix | Status |
|------|-------|------|-----------|-----|--------|
| 32 | `CacheManager()` | Undefined name | Missing import | `from src.utils.cache import CacheManager` | ✅ SAFE |
| 173 | `CacheManager()` | Undefined name | Missing import | `from src.utils.cache import CacheManager` | ✅ SAFE |
| 208 | `CacheManager()` | Undefined name | Missing import | `from src.utils.cache import CacheManager` | ✅ SAFE |
| 330 | `CacheManager()` | Undefined name | Missing import | `from src.utils.cache import CacheManager` | ✅ SAFE |
| 490 | `CacheManager()` | Undefined name | Missing import | `from src.utils.cache import CacheManager` | ✅ SAFE |
| 539 | `CacheManager()` | Undefined name | Missing import | `from src.utils.cache import CacheManager` | ✅ SAFE |
| 562 | `CacheManager()` | Undefined name | Missing import | `from src.utils.cache import CacheManager` | ✅ SAFE |
| 577 | `CacheManager()` | Undefined name | Missing import | `from src.utils.cache import CacheManager` | ✅ SAFE |

**File Status:** Active tests, no skip marker - PRIORITY FIX

**Import Source Analysis:**
- Option A: `from src.ui.cache_manager import CacheManager` - Streamlit UI components (WRONG for perf tests)
- Option B: `from src.utils.cache import CacheManager` - Core cache implementation (CORRECT)
- Selected: Option B ✅

---

## test_performance_comprehensive.py (1 error)

| Line | Error | Type | Root Cause | Fix | Status |
|------|-------|------|-----------|-----|--------|
| 308 | `get_api_config()` | Undefined name | Missing import | `from config import get_api_config` | ✅ SAFE |

**File Status:** Active tests, no skip marker

**Import Source Verified:**
- Primary: `/Users/chrislehnen/Projektven/Definitie-app/src/config/__init__.py` - Public API (RECOMMENDED)
- Secondary: `/Users/chrislehnen/Projektven/Definitie-app/src/config/config_adapters.py` - Implementation
- Selected: Primary ✅

---

## test_feature_flags_context_flow.py (24 errors)

| Line | Error | Type | Root Cause | Fix | Status |
|------|-------|------|-----------|-----|--------|
| 39 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 65 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 70 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 91 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 105 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 173 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 203 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 222 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 270 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 288 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 303 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 332 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 348 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 364 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 387 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 405 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 431 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 444 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 460 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 503 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 514 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 530 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 548 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |
| 566 | `FeatureFlags()` | Undefined name | Import commented out (line 26) | `from config.feature_flags import FeatureFlags` | ✅ SAFE |

**File Status:** All tests marked as `@pytest.mark.skip` (feature flags not yet implemented, US-041/042/043 pending)

**Import Path Correction:**
- Comment says: `from src.services.feature_flags import FeatureFlags`
- Actual location: `/Users/chrislehnen/Projektven/Definitie-app/src/config/feature_flags.py`
- Correct import: `from config.feature_flags import FeatureFlags` ✅

---

## test_modern_service.py (5 errors)

| Line | Error | Type | Root Cause | Fix | Status |
|------|-------|------|-----------|-----|--------|
| 35 | `wikipedia_lookup_stub` | Undefined name | Fixture import commented (line 23) | Import from `tests.fixtures.web_lookup_mocks` | ⚠️ MEDIUM |
| 41 | `SRUServiceStub` | Undefined name | Fixture import commented (line 23) | Import from `tests.fixtures.web_lookup_mocks` | ⚠️ MEDIUM |
| 66 | `wikipedia_lookup_stub` | Undefined name | Fixture import commented (line 23) | Import from `tests.fixtures.web_lookup_mocks` | ⚠️ MEDIUM |
| 72 | `SRUServiceStub` | Undefined name | Fixture import commented (line 23) | Import from `tests.fixtures.web_lookup_mocks` | ⚠️ MEDIUM |
| 92 | `wikipedia_lookup_stub` | Undefined name | Fixture import commented (line 23) | Import from `tests.fixtures.web_lookup_mocks` | ⚠️ MEDIUM |

**File Status:** ALL TESTS SKIPPED (`pytestmark = pytest.mark.skip(reason="Fixtures removed, will restore incrementally")`)

**Recommendation:** Skip fixture restoration for now
- Reason: Tests are already skipped, fixtures may be stale
- Action: Create separate DEF-XXX ticket for fixture restoration
- Current approach: Leave marked as "pending restoration"

**Fixture Existence Verified:**
- `wikipedia_lookup_stub` - `/Users/chrislehnen/Projektven/Definitie-app/tests/fixtures/web_lookup_mocks.py` (line 80+)
- `SRUServiceStub` - `/Users/chrislehnen/Projektven/Definitie-app/tests/fixtures/web_lookup_mocks.py` (line 30+)

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| **Total F821 Errors** | 43 |
| **SAFE Fixes** | 38 |
| **MEDIUM Risk** | 5 |
| **HIGH Risk** | 0 |
| **Files Needing Changes** | 5 |
| **Files to Skip** | 1 |
| **Unique Import Statements Needed** | 5 |

---

## Implementation Order (Recommended)

### Priority 1 (Active Tests) - Fix immediately
1. `test_performance.py` - 8 errors (no skip marker, active)
2. `test_performance_comprehensive.py` - 1 error (no skip marker, active)

### Priority 2 (Pending Features) - Fix for completeness
3. `test_astra_nora_context_compliance.py` - 4 errors (xfail marker, US-041/042/043)
4. `test_context_flow_performance.py` - 1 error (skip marker, US-041/042/043)
5. `test_feature_flags_context_flow.py` - 24 errors (skip marker, US-041/042/043)

### Priority 3 (Deferred) - Handle separately
6. `test_modern_service.py` - 5 errors (skip marker, create follow-up ticket)

---

## Verification Commands

```bash
# Before fixes
ruff check --select F821 tests/

# After fixes (should show only test_modern_service.py errors)
ruff check --select F821 tests/ | wc -l
# Expected output: 5 errors remaining

# Run affected tests to verify imports work
pytest tests/compliance/test_astra_nora_context_compliance.py -v --tb=short
pytest tests/performance/test_context_flow_performance.py -v --tb=short
pytest tests/performance/test_performance.py -v --tb=short
pytest tests/performance/test_performance_comprehensive.py -v --tb=short
pytest tests/unit/test_feature_flags_context_flow.py -v --tb=short

# Verify test_modern_service.py still skipped
pytest tests/unit/web_lookup/test_modern_service.py -v
# Expected: "5 skipped"
```

---

Generated: 2025-11-24
Status: ANALYSIS COMPLETE - READY FOR IMPLEMENTATION
