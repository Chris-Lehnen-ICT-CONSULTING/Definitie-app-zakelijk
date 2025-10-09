# Double-Weighting Bug Analysis - Quality Gate Implementation

**Date**: 2025-10-09
**Author**: Claude Code
**Status**: RESOLVED
**Severity**: HIGH (Test Failure)

## Executive Summary

After implementing quality-gated juridical boost (FASE 3), the test `test_ranking_relevance_based` failed. The root cause was **double-weighting of provider weights** - confidence scores were being multiplied by provider weights twice: once during lookup and once during ranking. This caused Wikipedia (weighted 0.85) to be unfairly penalized compared to Overheid.nl (weighted 1.0).

## Problem Statement

### Expected Behavior
```
Wikipedia:   0.8 (base) × 0.85 (weight) = 0.68 final score
Overheid.nl: 0.6 (base) × 1.10 (boost) × 1.0 (weight) = 0.66 final score
Result: Wikipedia wins (0.68 > 0.66) ✅
```

### Actual Behavior
```
Wikipedia:   0.8 × 0.85 (in lookup) × 0.85 (in ranking) = 0.578 ❌
Overheid.nl: 0.6 × 1.10 (boost) × 1.0 (in ranking) = 0.66
Result: Overheid.nl wins (0.66 > 0.578) ❌
```

## Root Cause Analysis

### Data Flow Trace

1. **Step 1: Lookup** (`_lookup_mediawiki`, `_lookup_sru`, etc.)
   - Raw Wikipedia result: confidence = 0.8
   - **FIRST WEIGHT APPLICATION**: `result.source.confidence *= source.confidence_weight`
   - Wikipedia confidence becomes: 0.8 × 0.85 = **0.68** ❌

2. **Step 2: Juridical Boost** (`boost_juridische_resultaten`)
   - Wikipedia: 0.68 (no boost, not juridical)
   - Overheid.nl: 0.6 × 1.10 = **0.66** (quality gate applied correctly)

3. **Step 3: Contract Conversion** (`_to_contract_dict`)
   - Wikipedia: score = 0.68 (already weighted once)
   - Overheid.nl: score = 0.66

4. **Step 4: Ranking** (`rank_and_dedup` → `_final_score`)
   - **SECOND WEIGHT APPLICATION**: `final = provider_weight × base_score`
   - Wikipedia: 0.68 × 0.85 = **0.578** ❌ (double-weighted!)
   - Overheid.nl: 0.66 × 1.0 = **0.66** ✅

5. **Result**: Overheid.nl wins despite lower relevance

### The Bug

Provider weights were applied in **two separate places**:

```python
# LOCATION 1: In lookup methods (modern_web_lookup_service.py)
async def _lookup_mediawiki(...):
    # ... fetch result ...
    if result and result.success:
        result.source.confidence *= source.confidence_weight  # ❌ FIRST WEIGHT
        return result

# LOCATION 2: In ranking (ranking.py)
def _final_score(item, provider_weights):
    w = provider_weights.get(item.get("provider", ""), 1.0)
    base = float(item.get("score", 0.0))
    return w * base  # ❌ SECOND WEIGHT (using same weights!)
```

### Why This Happened

The system evolved organically:
- Originally, lookup methods applied weights (single-source use case)
- Later, ranking module was added with cross-source comparison (multi-source use case)
- Both used the same `provider_weights` mapping
- No one noticed the double application because tests didn't compare weighted vs non-weighted sources

## Solution

### Design Decision: Weight Only in Ranking

We removed weight application from **all lookup methods** and applied weights **only in ranking**:

**Rationale**:
- Ranking is the natural place for cross-source comparison
- Lookup methods return "pure" confidence scores (easier to debug)
- Single responsibility: lookup = fetch, ranking = compare
- Easier to test (mocks can return simple confidence values)

### Code Changes

#### File: `src/services/modern_web_lookup_service.py`

**Changed 6 locations** (all lookup methods):

```python
# BEFORE (wrong - double weight)
if result and result.success:
    result.source.confidence *= source.confidence_weight  # ❌
    return result

# AFTER (correct - no weight in lookup)
if result and result.success:
    # NOTE: Provider weight applied in ranking, not here
    # to avoid double-weighting (Oct 2025)
    return result
```

**Locations changed**:
1. `_lookup_mediawiki` - Wikipedia branch (line ~602)
2. `_lookup_mediawiki` - Wiktionary branch (line ~680)
3. `_lookup_sru` - Main stage loop (line ~758)
4. `_lookup_sru` - Fallback loop (line ~785, kept 0.95 penalty)
5. `_lookup_rest` - Rechtspraak lookup (line ~828)
6. `_lookup_brave` - Brave Search lookup (line ~906)

**Note**: In `_lookup_sru` fallback (line 789), we kept the 0.95 penalty but removed the provider weight:
```python
# Fallback penalty (intrinsic quality reduction)
r.source.confidence *= 0.95  # ✅ Keep (not provider weight)
return r
```

## Verification

### Debug Test Output

Created temporary debug test (`tests/debug_ranking_test.py`) that traced complete flow:

```
================================================================================
STEP 1: LOOKUP RAW RESULTS
================================================================================
Wikipedia raw result:
  confidence: 0.8     ✅ No provider weight applied

Overheid.nl raw result:
  confidence: 0.6     ✅ No provider weight applied

================================================================================
STEP 2: JURIDICAL BOOST APPLICATION
================================================================================
Before boost:
  Wikipedia: confidence=0.800
  Overheid.nl: confidence=0.600

After boost:
  Wikipedia: confidence=0.800    ✅ No boost (not juridical)
  Overheid.nl: confidence=0.660  ✅ Quality gate: 0.6 × 1.10 = 0.66

================================================================================
STEP 4: APPLY PROVIDER WEIGHTS & RANKING
================================================================================
Final scores (before ranking):
  Wikipedia:
    base_score: 0.800
    weight: 0.850
    final_score: 0.680 (= 0.800 × 0.850)  ✅ Single weight application

  Overheid.nl:
    base_score: 0.660
    weight: 1.000
    final_score: 0.660 (= 0.660 × 1.000)  ✅ Single weight application

================================================================================
RESULT: Wikipedia wins (0.68 > 0.66) ✅
================================================================================
```

### Test Results

```bash
$ pytest tests/services/test_modern_web_lookup_service_unit.py::test_ranking_relevance_based -v

============================== 1 passed in 0.11s ===============================
```

All 3 tests in the file pass:
- `test_parallel_lookup_concurrency_and_timeout` ✅
- `test_error_handling_returns_empty_results` ✅
- `test_ranking_relevance_based` ✅ (was failing, now passes)

## Impact Analysis

### Changed Behavior

**Before Fix** (double-weighted):
- Wikipedia results: confidence × 0.85 × 0.85 = **0.7225×** original
- Overheid.nl results: confidence × 1.0 × 1.0 = **1.0×** original
- Bias: 38% penalty for Wikipedia!

**After Fix** (single-weighted):
- Wikipedia results: confidence × 0.85 = **0.85×** original
- Overheid.nl results: confidence × 1.0 = **1.0×** original
- Bias: 15% penalty for Wikipedia (as intended)

### Affected Components

1. **All provider lookups** - Now return pure confidence scores
2. **Ranking module** - Single source of truth for provider weighting
3. **Tests** - Updated mocks to return realistic data

### Backward Compatibility

**Breaking change**: Yes, but acceptable because:
- This is a single-user application (not in production)
- Bug caused incorrect behavior (high-quality sources were unfairly penalized)
- Quality gate implementation depends on correct weighting
- No backwards compatibility required per project policy

## Lessons Learned

### Design Principles Violated

1. **DRY with hidden coupling**: `provider_weights` used in 2 places, but coupling not documented
2. **Single Responsibility**: Lookup methods both fetched AND scored results
3. **Lack of integration tests**: No test compared weighted vs non-weighted sources
4. **Implicit contracts**: Weight application not clearly documented in interfaces

### Prevention Strategies

1. **Document data flow** - Add comments about where transformations happen
2. **Integration tests** - Test cross-provider ranking with different weights
3. **Explicit contracts** - Clearly document whether returned confidence is "raw" or "weighted"
4. **Single transformation location** - Apply transformations (like weighting) in exactly ONE place

### Code Quality Improvements

Added clear documentation in code:
```python
# NOTE: Provider weight applied in ranking, not here
# to avoid double-weighting (Oct 2025)
```

This prevents future developers from "fixing" the "missing" weight application.

## Related Work

- **EPIC-003**: Web Lookup Phase 2 - Provider prioritization
- **US-151**: Quality-gated juridical boost (triggered this bug)
- **Issue**: `test_ranking_relevance_based` failure (resolved)

## Recommendations

### Short-term (Completed)

1. ✅ Remove weight application from all lookup methods
2. ✅ Update tests to verify single-weight application
3. ✅ Document weight application location in code comments
4. ✅ Verify quality gate works correctly with fix

### Long-term

1. **Refactor confidence scoring** - Create explicit `RawConfidence` vs `WeightedScore` types
2. **Add property tests** - Verify score transformations are monotonic and bounded
3. **Integration test suite** - Test ranking across all provider combinations
4. **Architecture documentation** - Document data flow from lookup → boost → ranking

## Appendix: Full Test Scenario

### Test Setup
```python
# Wikipedia: High-quality relevant non-juridical
make_result(
    "Wikipedia",
    "https://nl.wikipedia.org/wiki/Kracht_van_gewijsde",
    0.8,      # Good base score
    False,    # Not juridical, but relevant
    "Kracht van gewijsde betekent onherroepelijk"
)

# Overheid.nl: Low-quality irrelevant juridical
make_result(
    "Overheid.nl",
    "https://wetten.overheid.nl/BES-wetgeving",
    0.6,      # Lower score (low relevance)
    True,     # Juridical, but not relevant
    "BES wetgeving paragraaf 3.2"
)
```

### Expected Flow
1. **Lookup**: Wikipedia 0.8, Overheid.nl 0.6 (raw scores)
2. **Boost**: Wikipedia 0.8 (no boost), Overheid.nl 0.66 (quality-gated 1.10×)
3. **Ranking**: Wikipedia 0.68 (0.8 × 0.85), Overheid.nl 0.66 (0.66 × 1.0)
4. **Result**: Wikipedia wins ✅

### Config Dependencies
```yaml
# config/web_lookup_defaults.yaml
providers:
  wikipedia:
    weight: 0.85  # Slightly penalized (not authoritative)
  sru_overheid:
    weight: 1.0   # Full authority weight

juridical_boost:
  quality_gate:
    enabled: true
    min_base_score: 0.65        # Only boost high-quality sources
    reduced_boost_factor: 0.5   # 50% boost if below threshold
```

## Conclusion

The double-weighting bug was a subtle but critical issue caused by applying provider weights in multiple locations. By centralizing weight application to the ranking module, we:

1. Fixed the immediate test failure ✅
2. Simplified the codebase (single responsibility) ✅
3. Made debugging easier (pure confidence in lookups) ✅
4. Enabled quality gate to work correctly ✅

The fix aligns with the principle: **"Autoriteit moet verdient worden met kwaliteit"** - provider weights now correctly compare sources without unfair double-penalty.
