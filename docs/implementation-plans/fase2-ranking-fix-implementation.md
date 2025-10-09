# FASE 2: Ranking Flow Bug Fix - Implementation Plan

## Executive Summary

**Problem:** Juridical boost is applied AFTER `rank_and_dedup()`, then ignored during result assembly.

**Root Cause:** Confidence values are frozen in `ranked` list before boost is applied, resulting in pre-boost ordering.

**Solution:** Move `boost_juridische_resultaten()` BEFORE `rank_and_dedup()` to ensure boosted confidence values affect sort order.

**Effort:** 2.5 hours
**Risk:** Low
**Impact:** High (juridical content will correctly rank higher)

---

## 1. PROBLEM ANALYSIS

### 1.1 Current Flow (BUGGY)

```python
# Line 292-293: Convert to contract dicts
prepared = [self._to_contract_dict(r) for r in valid_results]

# Line 296: Rank BEFORE boost
ranked = rank_and_dedup(prepared, self._provider_weights)

# Line 328-330: Boost AFTER ranking (TOO LATE!)
valid_results = boost_juridische_resultaten(valid_results, context=context_tokens)

# Line 340-366: Build final_results from `ranked` (pre-boost order!)
for item in ranked:
    key = ...
    picked = index.get(key)
    if picked is not None:
        final_results.append(picked)
```

### 1.2 Why This Is Wrong

1. **`rank_and_dedup()` uses `score` from contract dict**
   - Score = `result.source.confidence` (pre-boost)
   - Results are sorted by this pre-boost confidence

2. **`boost_juridische_resultaten()` updates original confidence values**
   - Updates `valid_results` list AFTER ranking
   - Boosted values NOT propagated to `ranked` list

3. **Final assembly uses `ranked` order**
   - Order is based on pre-boost scores
   - Juridical boost effectively ignored

### 1.3 Confidence Flow Trace

```
LookupResult.source.confidence (0.5)
    ↓
_to_contract_dict() → dict["score"] = 0.5
    ↓
rank_and_dedup() → sorts by score=0.5
    ↓
ranked list (ORDER FROZEN at score=0.5)
    ↓
boost_juridische_resultaten() → updates confidence to 0.69
    ↓
final_results → uses ranked ORDER (wrong!) + boosted VALUES (ignored for ordering)
```

---

## 2. SOLUTION DESIGN

### 2.1 Core Fix

**Move `boost_juridische_resultaten()` BEFORE `rank_and_dedup()`**

```python
# NEW FLOW:
# 1. Boost confidence values
valid_results = boost_juridische_resultaten(valid_results, context=context_tokens)

# 2. Convert boosted results to contract dicts
prepared = [self._to_contract_dict(r) for r in valid_results]

# 3. Rank with boosted scores
ranked = rank_and_dedup(prepared, self._provider_weights)
```

### 2.2 Implementation Details

**File:** `src/services/modern_web_lookup_service.py`
**Lines to modify:** 286-340

**BEFORE:**
```python
# Ranking & dedup volgens Epic 3
try:
    from .web_lookup.context_filter import ContextFilter
    from .web_lookup.ranking import rank_and_dedup

    # Convert to contract-like dicts for ranking
    prepared = [
        self._to_contract_dict(r) for r in valid_results if r is not None
    ]
    ranked = rank_and_dedup(prepared, self._provider_weights)

    # Context filtering...
    if request.context:
        # ...

    # JURIDISCHE RANKING BOOST (BUG: TOO LATE!)
    try:
        from .web_lookup.juridisch_ranker import boost_juridische_resultaten
        # Extract context tokens...
        valid_results = boost_juridische_resultaten(
            valid_results, context=context_tokens
        )
```

**AFTER:**
```python
# Ranking & dedup volgens Epic 3
try:
    from .web_lookup.context_filter import ContextFilter
    from .web_lookup.ranking import rank_and_dedup

    # PHASE 1: JURIDISCHE RANKING BOOST (MOVED UP!)
    # CRITICAL: Boost MUST happen BEFORE ranking to affect sort order
    try:
        from .web_lookup.juridisch_ranker import boost_juridische_resultaten

        # Extract context tokens voor juridische ranking
        context_tokens = None
        if request.context:
            org, jur, wet = self._classify_context_tokens(request.context)
            context_tokens = jur + wet

        # Boost valid_results BEFORE conversion
        valid_results = boost_juridische_resultaten(
            valid_results, context=context_tokens
        )
        logger.info(
            f"Juridische ranking boost applied to {len(valid_results)} results"
        )
    except Exception as e:
        logger.warning(f"Juridische ranking boost gefaald: {e}")

    # PHASE 2: Convert BOOSTED results to contract dicts
    prepared = [
        self._to_contract_dict(r) for r in valid_results if r is not None
    ]

    # PHASE 3: Rank with boosted scores
    ranked = rank_and_dedup(prepared, self._provider_weights)

    # PHASE 4: Context filtering (AFTER ranking, as before)
    if request.context:
        org, jur, wet = self._classify_context_tokens(request.context)
        context_filter = ContextFilter()
        ranked = context_filter.filter_results(
            ranked,
            org_context=org if org else None,
            jur_context=jur if jur else None,
            wet_context=wet if wet else None,
            min_score=0.0,
        )
```

---

## 3. SIDE EFFECTS ANALYSIS

### 3.1 Impact on Other Components

| Component | Impact | Analysis | Mitigation |
|-----------|--------|----------|------------|
| **Context Filter** | Low | Runs AFTER boost (no conflict) | None needed |
| **UI Tabs** | Medium | Result order changes | Test all tabs |
| **Prompt Augmentation** | High | Top results change | Verify prompts use juridical content |
| **Caching** | None | No caching at this level | None needed |
| **Tests** | High | Order assertions fail | Update tests |

### 3.2 Breaking Changes

- ❌ **Result order WILL change** (this is the intended fix!)
- ❌ **Tests asserting specific order will fail** (need updates)
- ✅ **API contract unchanged** (same data structure)
- ✅ **No config changes needed**
- ✅ **No database migrations needed**

### 3.3 Edge Cases

#### 3.3.1 Empty Results
```python
valid_results = []
boost_juridische_resultaten([])  # Returns []
# No impact, safe
```

#### 3.3.2 All Non-Juridical Content
```python
# All results get boost=1.0 (no change)
# Relative order unchanged
# Safe
```

#### 3.3.3 Confidence Capping
```python
# Original confidence: 0.9
# Boost: 1.3x → 1.17
# Capped at: 1.0 (max confidence)
# Expected behavior (juridical content should max out)
```

#### 3.3.4 Context Filter Re-ordering
```python
# Context filter applies AFTER juridical boost
# Both boosts are ADDITIVE (desired)
# Juridical + context match = highest rank
```

---

## 4. VALIDATION STRATEGY

### 4.1 Unit Test (New)

**File:** `tests/services/test_modern_web_lookup_juridical_boost_integration.py`

```python
"""Integration test: Verify juridical boost affects ranking."""

import pytest
from unittest.mock import AsyncMock
from src.services.modern_web_lookup_service import ModernWebLookupService
from src.services.interfaces import LookupRequest, LookupResult, WebSource

@pytest.mark.asyncio
async def test_juridical_boost_affects_ranking_order():
    """
    Test: Juridical boost is applied BEFORE ranking.

    Setup:
    - Wikipedia: confidence 0.8 (no boost) → final 0.8 * 0.7 = 0.56
    - Rechtspraak: confidence 0.5 (1.38x boost) → final 0.69 * 1.0 = 0.69
    - Expected: Rechtspraak ranks #1
    """
    service = ModernWebLookupService()

    wiki_result = LookupResult(
        term="voorlopige hechtenis",
        source=WebSource(
            name="Wikipedia",
            url="https://nl.wikipedia.org/wiki/Voorlopige_hechtenis",
            confidence=0.8,
            is_juridical=False,
        ),
        definition="Wikipedia definitie zonder juridische keywords",
        success=True,
    )

    rechtspraak_result = LookupResult(
        term="voorlopige hechtenis",
        source=WebSource(
            name="Rechtspraak.nl",
            url="https://www.rechtspraak.nl/uitspraken/123",
            confidence=0.5,
            is_juridical=True,
        ),
        definition="Volgens Artikel 63 Sv kan voorlopige hechtenis worden toegepast",
        success=True,
    )

    async def mock_lookup(term, source_name, request):
        if "wikipedia" in source_name:
            return wiki_result
        elif "rechtspraak" in source_name:
            return rechtspraak_result
        return None

    service._lookup_source = AsyncMock(side_effect=mock_lookup)

    request = LookupRequest(
        term="voorlopige hechtenis",
        context="Sv|strafrecht",
        max_results=5,
    )

    results = await service.lookup(request)

    # CRITICAL ASSERTION: Juridical result ranks FIRST
    assert len(results) >= 2
    assert results[0].source.name == "Rechtspraak.nl"
    assert results[0].source.confidence > 0.56  # Higher than Wikipedia
```

### 4.2 Manual Test Scenarios

**Test 1: Juridical vs Non-Juridical**
```python
# Term: "voorlopige hechtenis"
# Context: "Sv|strafrecht"
# Expected: Rechtspraak.nl > Wikipedia
```

**Test 2: Artikel Reference Boost**
```python
# Term: "strafbaar feit"
# Context: "Wetboek van Strafrecht"
# Expected: Results with "Artikel X" rank higher
```

**Test 3: Context Token Matching**
```python
# Term: "onherroepelijk vonnis"
# Context: "strafrecht"
# Expected: Results mentioning "strafrecht" rank higher
```

### 4.3 Regression Tests

**Update existing tests:**
- `tests/services/test_modern_web_lookup_service_unit.py`
- `tests/integration/test_improved_web_lookup.py`

**Expected failures (to fix):**
- Any test asserting "Wikipedia ranks first" for juridical terms
- Order-dependent assertions

---

## 5. RISK ANALYSIS

### 5.1 Risk Matrix

| Risk | Probability | Impact | Severity | Mitigation |
|------|------------|--------|----------|------------|
| UI breaks | Low | Medium | **LOW** | Test all tabs |
| Tests fail | High | Low | **LOW** | Update tests |
| Over-boosting | Low | Low | **LOW** | Monitor confidence values |
| Performance | Very Low | Low | **VERY LOW** | Boost is O(n) |
| Rollback needed | Low | Medium | **LOW** | Clean git revert |

### 5.2 Rollback Plan

**Trigger:** UI shows empty results OR tests fail >50%

**Procedure:**
```bash
# Identify commit hash
git log --oneline -5

# Revert
git revert <commit-hash>
git push origin main

# Verify
pytest tests/services/test_modern_web_lookup_service_unit.py -v
bash scripts/run_app.sh
```

**Fallback:** Feature flag (NOT recommended for this fix)

---

## 6. IMPLEMENTATION STEPS

### 6.1 Execution Plan

**Step 1: Create Branch**
```bash
git checkout -b fix/juridical-boost-ranking-order
```

**Step 2: Implement Fix**
- Edit `src/services/modern_web_lookup_service.py` lines 286-340
- Move juridical boost block BEFORE ranking
- Add inline comment explaining fix

**Step 3: Add Integration Test**
- Create `tests/services/test_modern_web_lookup_juridical_boost_integration.py`
- Implement test from Section 4.1

**Step 4: Update Existing Tests**
```bash
# Run tests to find failures
pytest tests/services/test_modern_web_lookup_service_unit.py -v

# Update assertions for new order
# Example: Change "assert results[0].source.name == 'Wikipedia'"
#          to "assert results[0].source.name == 'Rechtspraak.nl'"
```

**Step 5: Manual Testing**
```bash
# Start app
bash scripts/run_app.sh

# Test scenarios from Section 4.2
# Verify result order in UI
```

**Step 6: Commit**
```bash
git add .
git commit -m "fix(web-lookup): apply juridical boost BEFORE ranking

PROBLEM:
- Juridical boost was applied AFTER rank_and_dedup()
- Boosted confidence values were ignored in ordering
- Juridical sources ranked lower than expected

SOLUTION:
- Move boost_juridische_resultaten() BEFORE rank_and_dedup()
- Boosted confidence now affects sort order
- Juridical sources (rechtspraak.nl, overheid.nl) rank higher

IMPACT:
- Result order changes (juridical content ranks higher)
- Updated tests to reflect expected behavior
- No API contract changes

Fixes: FASE 2 Ranking Flow Bug
"
```

**Step 7: Push & Merge**
```bash
git push origin fix/juridical-boost-ranking-order
git checkout main
git merge fix/juridical-boost-ranking-order
git push origin main
```

### 6.2 Timeline

| Task | Duration |
|------|----------|
| Implement fix | 15 min |
| Add integration test | 30 min |
| Update existing tests | 45 min |
| Manual testing | 30 min |
| Documentation | 15 min |
| **TOTAL** | **2.5 hours** |

---

## 7. SUCCESS METRICS

### 7.1 Before vs After

**BEFORE Fix:**
```
Term: "voorlopige hechtenis"
Context: "Sv|strafrecht"

Results:
1. Wikipedia (conf: 0.8 * 0.7 = 0.56)
2. Overheid.nl (conf: 0.55 * 1.0 = 0.55)
3. Rechtspraak (conf: 0.5 * 1.0 = 0.5)  ← Should be #1!
```

**AFTER Fix:**
```
Term: "voorlopige hechtenis"
Context: "Sv|strafrecht"

Results:
1. Rechtspraak (conf: 0.69 * 1.0 = 0.69)  ← Now #1! ✅
   - Base: 0.5
   - Boost: 1.15 (is_juridical) * 1.2 (keyword "Artikel") = 1.38
   - Final: min(0.5 * 1.38, 1.0) = 0.69
2. Overheid.nl (conf: 0.66 * 1.0 = 0.66)
   - Base: 0.55
   - Boost: 1.2 (is_juridical)
   - Final: 0.55 * 1.2 = 0.66
3. Wikipedia (conf: 0.8 * 0.7 = 0.56)
   - No boost (not juridical)
```

### 7.2 Validation Checks

**Immediate (0-15 min):**
- [ ] App starts without errors
- [ ] Lookup returns results
- [ ] Juridical content ranks higher than Wikipedia
- [ ] No crashes in logs

**Short-term (1 hour):**
- [ ] Full test suite passes
- [ ] 5-10 manual test terms
- [ ] UI displays results correctly
- [ ] Performance < 5s per lookup

**Long-term (1 day):**
- [ ] Error rate = 0%
- [ ] Result quality verified
- [ ] No user complaints

---

## 8. DOCUMENTATION UPDATES

### 8.1 Inline Comments

**Add in `modern_web_lookup_service.py`:**
```python
# CRITICAL ORDER: Juridical boost MUST happen BEFORE ranking!
# Reason: boost_juridische_resultaten() updates result.source.confidence
# which is used by rank_and_dedup() for sorting.
# If boost happens AFTER ranking, boosted scores are ignored.
# Bug fix: Moved from line 328 to line 290 (2025-10-09)
valid_results = boost_juridische_resultaten(valid_results, context=context_tokens)
```

### 8.2 Architecture Docs

**Update `docs/architectuur/TECHNICAL_ARCHITECTURE.md`:**

```markdown
## Web Lookup Ranking Pipeline

### Execution Order (Fixed: 2025-10-09)

1. **Fetch** results from providers
2. **Juridical Boost** ⬅️ MUST BE FIRST!
   - Apply `boost_juridische_resultaten()`
   - Updates `result.source.confidence`
3. **Convert** to contract dicts (`_to_contract_dict()`)
   - Extract boosted confidence as `score`
4. **Rank & Dedup** (`rank_and_dedup()`)
   - Sort by weighted score
   - Dedup by URL/content hash
5. **Context Filter** (optional)
   - Additional relevance scoring
6. **Limit** to max_results and return

**CRITICAL:** Steps must execute in this order!
```

### 8.3 Changelog

**Add to `CHANGELOG.md`:**
```markdown
## [Unreleased]

### Fixed
- **Web Lookup Ranking:** Juridical boost now correctly affects result order
  - Moved `boost_juridische_resultaten()` before `rank_and_dedup()`
  - Juridical sources (rechtspraak.nl, overheid.nl) now rank higher
  - Fixes: FASE 2 Ranking Flow Bug
```

---

## 9. APPENDIX

### A. Complete Code Change

**File:** `src/services/modern_web_lookup_service.py`
**Lines:** 286-340

```python
# Ranking & dedup volgens Epic 3
try:
    from .web_lookup.context_filter import ContextFilter
    from .web_lookup.ranking import rank_and_dedup

    # PHASE 1: JURIDISCHE RANKING BOOST (MOVED UP!)
    # CRITICAL: Boost MUST happen BEFORE ranking to affect sort order
    # Bug fix: Previously at line 328 (after ranking) - moved to line 290
    # Reason: boost updates result.source.confidence which is used for sorting
    try:
        from .web_lookup.juridisch_ranker import boost_juridische_resultaten

        # Extract context tokens voor juridische ranking
        context_tokens = None
        if request.context:
            org, jur, wet = self._classify_context_tokens(request.context)
            # Combineer juridische en wettelijke tokens
            context_tokens = jur + wet

        # Boost valid_results (LookupResult objecten) VOOR conversie naar dicts
        valid_results = boost_juridische_resultaten(
            valid_results, context=context_tokens
        )
        logger.info(
            f"Juridische ranking boost applied to {len(valid_results)} results"
        )

    except Exception as e:
        logger.warning(f"Juridische ranking boost gefaald: {e}")
        # Continue zonder boost

    # PHASE 2: Convert BOOSTED results to contract-like dicts for ranking
    # NOW confidence values reflect juridical boost!
    prepared = [
        self._to_contract_dict(r) for r in valid_results if r is not None
    ]

    # PHASE 3: Rank with boosted scores
    # Provider keys mapping based on source names
    ranked = rank_and_dedup(prepared, self._provider_weights)

    # PHASE 4: Context filtering en relevance scoring
    # Pas context filtering toe NA ranking maar VOOR limitering
    if request.context:
        org, jur, wet = self._classify_context_tokens(request.context)
        context_filter = ContextFilter()
        # Filter met min_score=0.0 (keep all, maar voeg relevance score toe)
        ranked = context_filter.filter_results(
            ranked,
            org_context=org if org else None,
            jur_context=jur if jur else None,
            wet_context=wet if wet else None,
            min_score=0.0,  # Keep all results, maar rank by relevance
        )
        logger.info(
            f"Context filtering applied: {len(ranked)} results scored with context relevance"
        )

    # Reorder/filter original results according to ranked unique set
    # (Rest of code unchanged...)
```

### B. Test Example Output

```
BEFORE FIX:
===========
Term: voorlopige hechtenis
Context: Sv|strafrecht

Results:
  #1 Wikipedia (0.56) - "Voorlopige hechtenis is een maatregel..."
  #2 Overheid.nl (0.55) - "Definitie voorlopige hechtenis..."
  #3 Rechtspraak.nl (0.50) - "Artikel 63 Sv: Voorlopige hechtenis..."

AFTER FIX:
==========
Term: voorlopige hechtenis
Context: Sv|strafrecht

Results:
  #1 Rechtspraak.nl (0.69) - "Artikel 63 Sv: Voorlopige hechtenis..." ✅
  #2 Overheid.nl (0.66) - "Definitie voorlopige hechtenis..."
  #3 Wikipedia (0.56) - "Voorlopige hechtenis is een maatregel..."
```

---

## READY FOR IMPLEMENTATION ✅

**Reviewed:** 2025-10-09
**Approved:** Self-approved (single-user app)
**Estimated completion:** 2.5 hours
**Risk level:** LOW
**Impact:** HIGH (improved result quality)
