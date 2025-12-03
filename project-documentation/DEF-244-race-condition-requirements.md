# DEF-244: Race Condition in ModularValidationService - Product Requirements

**Document Version:** 1.0
**Date:** 2025-12-03
**Status:** ✅ IMPLEMENTED (commit 481f5543)
**Priority:** P1 (High - Confirmed not CRITICAL)

---

## Executive Summary

### Elevator Pitch
The validation service stores temporary data in instance variables that can be overwritten when multiple validations run at the same time, potentially causing one definition to be validated against another definition's context.

### Problem Statement
`ModularValidationService` uses instance-level state (`self._current_begrip`) during async validation operations. When `batch_validate` runs with `max_concurrency > 1` or when multiple UI tabs trigger validations concurrently, the begrip (term) stored in one validation can leak into another validation's rule evaluation, causing:
- Circular definition checks (CON-CIRC-001) to use wrong begrip
- Incorrect violation messages referencing wrong terms
- False positives/negatives in validation results

### Target Audience
- **Primary:** Solo developer maintaining the Definitie-app
- **Secondary:** Future maintainers who may enable parallel validation
- **Tertiary:** End users (Dutch legal professionals) who rely on accurate validation feedback

### Unique Selling Proposition (of the fix)
Eliminate shared mutable state pattern to ensure deterministic, thread-safe validation regardless of concurrency level - enabling safe future parallelization without breaking current functionality.

### Success Metrics
| Metric | Current | Target | Measurement Method |
|--------|---------|--------|-------------------|
| Race condition incidents | Unknown (latent bug) | 0 | Unit test coverage |
| Validation result determinism | Potentially non-deterministic | 100% deterministic | Golden file tests with concurrent execution |
| batch_validate with max_concurrency>1 safety | Unsafe | Safe | Integration test with 10 concurrent items |

---

## Problem Analysis

### Root Cause Identification

The race condition exists in `ModularValidationService.validate_definition()` at lines 429-465:

```python
# Line 429: Instance-level state set BEFORE rule evaluation
self._current_begrip: str | None = begrip

# Line 430-463: Rules evaluated in loop (async context switches possible)
for code in sorted(self._internal_rules):
    out = self._evaluate_rule(code, eval_ctx)  # <-- Can read stale _current_begrip
    ...

# Line 464-465: State cleared AFTER all rules complete
current_begrip = self._current_begrip
self._current_begrip = None
```

**The Problem Flow:**
1. Validation A starts for begrip "Contract"
2. `self._current_begrip = "Contract"` is set
3. Async context switch occurs (or parallel task starts)
4. Validation B starts for begrip "Overeenkomst"
5. `self._current_begrip = "Overeenkomst"` overwrites value
6. Validation A resumes `_evaluate_rule` for CON-CIRC-001
7. Rule checks if "Overeenkomst" (wrong!) is in text - **INCORRECT RESULT**

### Affected Rules

Rules that read `self._current_begrip`:
- `CON-CIRC-001` (line 853): Circular definition detection
- `VER-03` (line 925): Infinitive form check
- `SAM-02` (lines 946-993): Qualification/base definition check
- `SAM-04` (lines 1011-1026): Composition genus check
- `VER-01` (line 1251): Singular lemma check
- Suggestion generation (line 1695): Uses begrip for user feedback

### When Does This Actually Trigger?

| Scenario | Current Behavior | Risk Level |
|----------|------------------|------------|
| Single validation (UI button click) | Safe | None |
| `batch_validate(max_concurrency=1)` | Safe (sequential) | None |
| `batch_validate(max_concurrency>1)` | **UNSAFE** | Medium - Feature exists but default is 1 |
| Multiple browser tabs validating | Safe (separate sessions) | None |
| Streamlit rerun during validation | Safe (new request context) | None |

**Key Finding:** The race condition is **latent but not actively triggered** in production because:
1. Default `max_concurrency=1` forces sequential processing
2. Streamlit's execution model prevents true parallel UI actions
3. Solo user app has no multi-tenant concerns

---

## Priority Validation

### Is This Truly CRITICAL Priority?

**Verdict: No - Downgrade to P1 (High)**

| Factor | Assessment |
|--------|------------|
| Current production impact | **None** - Default concurrency=1 prevents triggering |
| User-visible symptoms | **None observed** - No bug reports |
| Data corruption risk | **Low** - Wrong validation results, not DB corruption |
| Blast radius if triggered | **Medium** - Single validation session affected |
| Existing workaround | **Yes** - Keep max_concurrency=1 (current default) |

### Blast Radius Analysis

If the race condition were triggered:
- **Immediate:** Single validation returns wrong results
- **Downstream:** User might approve/reject definition based on false validation
- **Recovery:** Re-run validation fixes it (no persistent corruption)
- **Scale:** Only affects current session, not other users/sessions

### Why Still P1 (High)?

1. **Code quality debt:** Pattern violates thread-safety best practices
2. **Future-proofing blocker:** Cannot safely enable parallel validation for batch imports
3. **Test fragility:** Concurrent test execution could produce flaky results
4. **Maintainability:** Instance state pattern is confusing for future developers

---

## Acceptance Criteria

### Must-Have (P0 - Required for fix completion)

- [x] **AC-1:** `_current_begrip` is NOT stored as instance state during validation ✅
- [x] **AC-2:** Each call to `validate_definition()` uses only function-local or parameter-passed state ✅
- [x] **AC-3:** Unit test demonstrating race condition FAILS before fix, PASSES after fix ✅ (7 tests)
- [x] **AC-4:** Existing golden file tests pass unchanged ✅
- [x] **AC-5:** `batch_validate(max_concurrency=10)` produces same results as sequential execution ✅

### Should-Have (P1 - Recommended)

- [x] **AC-6:** Similar instance-state patterns reviewed - no other `_current_*` patterns found ✅
- [ ] **AC-7:** Ruff/pylint rule added to detect `self._current_*` anti-pattern (SKIPPED - not needed)
- [ ] **AC-8:** Documentation updated in CLAUDE.md about async service patterns (DEFERRED)

### Could-Have (P2 - Nice to have)

- [ ] **AC-9:** Performance benchmark (SKIPPED - minimal change, no impact expected)
- [ ] **AC-10:** Architecture decision record (DEFERRED - documented in commit message)

---

## Scope Recommendation

### Recommended Approach: Hotfix (Minimal Change)

**Rationale:**
- Bug is latent, not actively causing issues
- Minimal change = minimal regression risk
- Broader refactor not justified by current impact

### Hotfix Specification

**Change Summary:** Pass begrip through EvaluationContext instead of instance state

**Files to Modify:**
1. `src/services/validation/modular_validation_service.py`
   - Remove `self._current_begrip` assignments (lines 429, 464-465)
   - Add `begrip` field to `EvaluationContext.from_params()` call
   - Update `_evaluate_rule()` to read begrip from context

2. `src/services/validation/types_internal.py`
   - Add `begrip: str | None = None` field to `EvaluationContext` dataclass

**Estimated Effort:** 2-4 hours implementation + 2 hours testing

### Alternative: Broader Refactor (NOT Recommended)

Would involve:
- Creating thread-local storage or validation session objects
- Refactoring all 6 methods reading `_current_begrip`
- Adding dependency injection for validation context

**Why NOT recommended:**
- 3-4x more effort (8-16 hours)
- Higher regression risk
- Overkill for latent bug with workaround

---

## Risk Assessment

### Implementation Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing rule behavior | Low | High | Run full golden file test suite |
| EvaluationContext changes break callers | Low | Medium | Context is internal type, not public API |
| Performance regression | Very Low | Low | Context is already passed, just add field |

### Non-Implementation Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Future developer enables concurrency>1 | Medium | High | Add warning log when concurrency>1 used |
| Flaky tests in CI | Low | Medium | Tests currently run sequentially |

---

## Communication Plan

### Existing Users Affected
- **None** - Bug is latent and not triggered in production

### Changelog Entry
```markdown
### Fixed
- DEF-244: Fixed potential race condition in validation service when using parallel batch validation (was latent bug, not actively triggered)
```

### Documentation Updates

1. **CLAUDE.md** (if implementing broader fix):
   Add pattern to "Streamlit Patterns" section:
   ```markdown
   ### Async Service State Anti-Pattern (Forbidden)

   # WRONG: Instance state in async method
   async def process(self, item):
       self._current_item = item  # Race condition!
       ...

   # CORRECT: Pass state through parameters
   async def process(self, item):
       result = self._evaluate(item, context_with_item)
       ...
   ```

2. **No user-facing documentation needed** - Internal implementation detail

---

## Technical Specifications

### Current Architecture (Problematic)

```
ModularValidationService (singleton via ServiceContainer)
    |
    +-- validate_definition(begrip, text, ...)
    |       |
    |       +-- self._current_begrip = begrip  <-- SHARED MUTABLE STATE
    |       |
    |       +-- for rule in rules:
    |       |       _evaluate_rule(code, ctx)
    |       |           |
    |       |           +-- getattr(self, "_current_begrip")  <-- READS SHARED STATE
    |       |
    |       +-- self._current_begrip = None
```

### Proposed Architecture (Fixed)

```
ModularValidationService (singleton, stateless validation)
    |
    +-- validate_definition(begrip, text, ...)
    |       |
    |       +-- ctx = EvaluationContext.from_params(begrip=begrip, ...)
    |       |
    |       +-- for rule in rules:
    |               _evaluate_rule(code, ctx)
    |                   |
    |                   +-- ctx.begrip  <-- READS FROM CONTEXT (NO SHARED STATE)
```

### EvaluationContext Changes

```python
@dataclass
class EvaluationContext:
    raw_text: str
    cleaned_text: str
    locale: str | None
    profile: str | None
    correlation_id: str
    tokens: tuple[str, ...]
    metadata: dict[str, Any]
    begrip: str | None = None  # <-- NEW FIELD

    @classmethod
    def from_params(cls, *, begrip: str | None = None, text: str, ...) -> "EvaluationContext":
        return cls(
            begrip=begrip,
            ...
        )
```

---

## Verification Plan

### Pre-Fix Verification

1. Write test demonstrating race condition:
```python
async def test_race_condition_in_batch_validate():
    """Prove race condition exists with concurrent validation."""
    service = ModularValidationService(...)

    # Two items with different begrippen
    items = [
        ("Contract", "Een juridische overeenkomst."),
        ("Overeenkomst", "Een contract tussen partijen."),
    ]

    # Run with concurrency - should produce DIFFERENT results due to race
    results_concurrent = await service.batch_validate(items, max_concurrency=2)

    # Run sequentially - CORRECT results
    results_sequential = await service.batch_validate(items, max_concurrency=1)

    # If race condition exists, these MAY differ (non-deterministic)
    # After fix, these MUST be identical
```

### Post-Fix Verification

1. Run race condition test - must pass
2. Run full golden file suite (`pytest -m golden`)
3. Run existing validation tests (`pytest tests/services/validation/`)
4. Run 10x with `max_concurrency=5` to verify determinism

### Production Monitoring

Add log entry when batch_validate uses concurrency>1:
```python
if max_concurrency > 1:
    logger.info(
        f"batch_validate using parallel execution (concurrency={max_concurrency})",
        extra={"component": "modular_validation_service", "concurrency": max_concurrency}
    )
```

---

## Critical Questions Checklist

- [x] Are there existing solutions we're improving upon? **Yes - Sequential fallback works**
- [x] What's the minimum viable version? **Pass begrip via context parameter**
- [x] What are the potential risks or unintended consequences? **Minimal - context is internal type**
- [x] Have we considered platform-specific requirements? **N/A - Python-only backend**
- [x] What GAPS exist that you need more clarity on from the user? **None - Analysis complete**

---

## Appendix A: Similar Patterns Found

Other instance-state patterns that should be reviewed (not blocking this fix):

1. `self._compiled_json_cache` (line 177) - Safe (read-only after init)
2. `self._compiled_ess02_cache` (line 178) - Safe (read-only after init)
3. `self._is_degraded_mode` (line 200) - Safe (set once on init failure)
4. `self._rules_loaded_count` (line 191) - Safe (set once on init)

No other `self._current_*` patterns found outside `_current_begrip`.

---

## Appendix B: Alternative Solutions Considered

| Solution | Pros | Cons | Verdict |
|----------|------|------|---------|
| Pass begrip via EvaluationContext | Minimal change, explicit data flow | Requires context schema change | **RECOMMENDED** |
| Thread-local storage | No context changes | Complex, Python-specific footgun | Rejected |
| Lock around validation | Guaranteed serialization | Defeats purpose of async, performance hit | Rejected |
| Copy-on-write service instances | True isolation | Memory overhead, complex lifecycle | Overkill |
| Deprecate max_concurrency>1 | Zero effort | Blocks future parallelization | Short-term workaround only |

---

## Final Recommendation

**Proceed with Hotfix approach:**
1. Add `begrip` field to `EvaluationContext`
2. Remove `self._current_begrip` pattern from `validate_definition()`
3. Update all 6 methods reading `_current_begrip` to use `ctx.begrip`
4. Add unit test proving fix works
5. Add log warning if `max_concurrency>1` is used

**Estimated Total Effort:** 4-6 hours

**Do NOT proceed with broader refactor** unless future requirements demand it (e.g., true multi-tenant support).

---

*Document generated: 2025-12-03*
*Analysis method: Codebase exploration + Impact assessment + Risk analysis*
*Data sources: src/services/validation/modular_validation_service.py, src/services/container.py, src/ui/components/*
