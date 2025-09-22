# 🔬 Pytest Test Failure Analysis Report
<!-- moved from project root to canonical docs location -->

**Date**: 2025-09-19
**Total Tests**: 1206
**Failed**: ~67+ tests across multiple categories
**Status**: Critical issues affecting test suite execution

---

## 📊 Executive Summary

De testsuite vertoont systematische failures in meerdere categorieën, voornamelijk veroorzaakt door:
1. **Streamlit Mock Issues** - MockStreamlit mist `cache_data` attribuut (3 tests kunnen niet collecteren)
2. **Import Dependencies** - Missing `tiktoken` module
3. **Type Mismatches** - ValidationResult TypedDict vs dataclass confusion
4. **Configuration Issues** - `get_api_config` niet gedefinieerd
5. **Test Assumptions** - Context parameter default waarden verschillen

---

## 🎯 Pattern Analysis

### Pattern 1: Streamlit Cache Decorator Issues
**Impact**: 3+ test files kunnen niet collecteren
**Root Cause**: MockStreamlit object heeft geen `cache_data` attribuut

```python
# Probleem in src/toetsregels/rule_cache.py:21
@st.cache_data(ttl=3600, show_spinner=False)  # MockStreamlit heeft dit niet
```

**Affected Files**:
- `tests/performance/test_rule_cache_performance.py`
- `tests/test_new_default.py`
- Indirect: alle tests die rule_cache importeren

**Dependency Chain**:
```
test_new_default.py
  → get_definition_service()
    → ServiceAdapter(container)
      → container.orchestrator()
        → cached_manager import
          → rule_cache import
            → @st.cache_data FAIL
```

---

### Pattern 2: Missing Dependencies
**Impact**: 1 test file
**Root Cause**: `tiktoken` module niet geïnstalleerd

```python
# tests/debug/test_prompt_token_analysis.py:15
import tiktoken  # ModuleNotFoundError
```

---

### Pattern 3: Context Parameter Default Mismatch
**Impact**: 2+ test failures in orchestrator tests
**Root Cause**: Tests verwachten `context=None`, code geeft `context={}`

```python
# Expected in test:
validate_definition(begrip='test_begrip', text='test text',
                   ontologische_categorie=None, context=None)

# Actual call:
validate_definition(begrip='test_begrip', text='test text',
                   ontologische_categorie=None, context={})
```

**Affected Tests**:
- `TestValidationOrchestratorV2::test_validate_text_without_context`
- `TestValidationOrchestratorV2::test_validate_text_with_cleaning`

---

### Pattern 4: DefinitieRecord Type Issues
**Impact**: 2+ repository tests
**Root Cause**: Tests verwachten DefinitieRecord object, krijgen dict

```python
# Test assertion:
assert isinstance(call_args[1], DefinitieRecord)  # Fails

# Actual value: dict met DefinitieRecord velden
{'begrip': 'Identiteitsbewijs', 'categorie': 'type', ...}
```

**Affected Tests**:
- `TestDefinitionRepository::test_save_existing_definition`
- `TestDefinitionRepository::test_update`

---

### Pattern 5: Configuration Import Errors
**Impact**: 12 config system tests
**Root Cause**: `get_api_config` functie niet gedefinieerd/geïmporteerd

```python
# NameError in test
adapter_config = get_api_config().config
                 ^^^^^^^^^^^^^^
E   NameError: name 'get_api_config' is not defined
```

**Affected Tests**: Alle tests in `TestConfigurationAdapters` class

---

### Pattern 6: Performance Test Assumptions
**Impact**: 2 performance tests
**Root Cause**: Timing assumptions te strikt

```python
# Test failure:
assert time_batch <= time_seq * 1.2  # Batch mag niet veel trager zijn
# Actual: 0.000157s > 0.000102s * 1.2
```

---

### Pattern 7: Golden Definition Score Mismatch
**Impact**: 1 contract test
**Root Cause**: Verwachte max score (0.75) vs actual (1.0)

```python
assert res["overall_score"] <= exp["max_overall_score"] + 0.001
# 1.0 > 0.75 + 0.001
```

---

## 📈 Impact Assessment

### By Category:
| Category | Failed | Impact Level | Root Causes |
|----------|--------|-------------|-------------|
| Unit Tests | ~50 | HIGH | Config imports, Mock issues |
| Service Tests | 17 | MEDIUM | Type mismatches, assumptions |
| Integration | 3-5 | MEDIUM | Streamlit mocking |
| Performance | 2 | LOW | Timing tolerances |
| Debug | 1 | LOW | Missing dependency |

### By Severity:
1. **CRITICAL** (Blocks test execution):
   - Streamlit cache_data mock issue (3+ test files)
   - Missing tiktoken dependency (1 test file)

2. **HIGH** (Many failures):
   - Configuration import errors (12 tests)
   - Type system mismatches (multiple)

3. **MEDIUM** (Functional issues):
   - Context parameter defaults
   - Performance assumptions

4. **LOW** (Isolated issues):
   - Golden definition scoring

---

## 🔧 Recommended Fixes

### Priority 1: Fix Test Infrastructure
```python
# 1. Update MockStreamlit in conftest.py
class MockStreamlit:
    def cache_data(self, ttl=None, show_spinner=True):
        def decorator(func):
            return func
        return decorator

    # OR: Use unittest.mock properly
    @property
    def cache_data(self):
        return lambda **kwargs: lambda func: func
```

### Priority 2: Install Missing Dependencies
```bash
# Add to requirements-dev.txt or install directly
pip install tiktoken
```

### Priority 3: Fix Import Issues
```python
# In test_config_system.py, add proper imports:
from config.configuration import get_api_config  # or correct path
```

### Priority 4: Align Test Expectations
```python
# Update orchestrator tests to expect empty dict instead of None:
mock_validation_service.validate_definition.assert_called_once_with(
    begrip='test_begrip',
    text='cleaned text',
    ontologische_categorie=None,
    context={}  # Not None
)
```

### Priority 5: Fix Type Conversions
```python
# Repository should handle both dict and DefinitieRecord:
if isinstance(record, dict):
    record = DefinitieRecord(**record)
```

---

## 🔄 Dependency Chains

### Chain 1: Streamlit Mock → Rule Cache → Service Container
```
MockStreamlit missing cache_data
  ↓
rule_cache.py cannot decorate
  ↓
cached_manager cannot import
  ↓
container.orchestrator() fails
  ↓
service_factory fails
  ↓
Multiple test failures
```

### Chain 2: Config System → Service Factory
```
get_api_config not defined
  ↓
Configuration adapters fail
  ↓
Service initialization fails
  ↓
Integration tests fail
```

---

## 📋 Action Items

### Immediate (Fix test execution):
1. ✅ Fix MockStreamlit to include cache_data
2. ✅ Install tiktoken dependency
3. ✅ Fix config imports in test_config_system.py

### Short-term (Fix test assertions):
4. ⏳ Update context parameter expectations
5. ⏳ Handle DefinitieRecord/dict conversion
6. ⏳ Adjust performance test tolerances

### Long-term (Improve test quality):
7. 📌 Add type hints to all test fixtures
8. 📌 Create integration test suite for config system
9. 📌 Improve mock consistency across test files
10. 📌 Add pre-commit hook for import validation

---

## 🎯 Success Metrics

After fixes:
- [ ] All 1206 tests should collect successfully
- [ ] <5% test failure rate (target: <60 failures)
- [ ] No import/collection errors
- [ ] Consistent mock behavior across all tests
- [ ] Clear error messages for actual failures

---

## 📊 Test Categories Breakdown

```
tests/
├── unit/           50 failures - Config & mock issues
├── services/       17 failures - Type & assumption issues
├── integration/    3-5 failures - Streamlit mock issues
├── performance/    2 failures - Timing tolerances
├── debug/          1 failure - Missing dependency
├── validation/     Unknown - Likely affected by mocks
└── rate_limiting/  1 skipped - Expected behavior
```

---

## 🔍 Deep Dive: Most Common Errors

### 1. AttributeError: 'MockStreamlit' object has no attribute 'cache_data'
**Frequency**: 3+ direct, many indirect
**Solution**: Enhance MockStreamlit class with proper cache decorators

### 2. NameError: name 'get_api_config' is not defined
**Frequency**: 12 tests
**Solution**: Fix import statements in test files

### 3. AssertionError: expected call not found (context mismatch)
**Frequency**: 2+ tests
**Solution**: Update test assertions to match actual behavior

### 4. ModuleNotFoundError: No module named 'tiktoken'
**Frequency**: 1 test
**Solution**: Add to dev dependencies

---

## 🚀 Next Steps

1. **Triage Meeting**: Review this analysis with team
2. **Fix Order**: Start with infrastructure (mocks) → dependencies → assertions
3. **CI/CD Update**: Add dependency checks to GitHub Actions
4. **Documentation**: Update test README with mock requirements
5. **Monitoring**: Set up test failure tracking dashboard

---

## 📝 Notes

- Test suite uses pytest with custom fixtures in conftest.py
- Heavy reliance on mocking Streamlit components
- Mix of unit, integration, and performance tests
- Some tests have environment-specific behavior (DEV_MODE)
- Golden definition tests suggest contract-based testing approach

**Recommendation**: Consider splitting mock-heavy tests into separate suite with dedicated mock infrastructure.
