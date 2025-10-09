# Provider Weighting Architecture - Executive Summary

**Date**: 2025-10-09
**Status**: DESIGN COMPLETE, IMPLEMENTATION VALIDATED
**Related Documents**:
- Full Design: `docs/architectuur/provider-weighting-architecture-design.md`
- Bug Analysis: `docs/analyses/double-weighting-bug-analysis.md`
- Validation Script: `scripts/validate_provider_weighting.py`

---

## Problem Statement

**Double-weighting bug occurred**: Provider weights were applied in **two separate places**:

```python
# LOCATION 1: Lookup methods (❌ REMOVED)
result.source.confidence *= source.confidence_weight  # 0.8 × 0.85 = 0.68

# LOCATION 2: Ranking module (✅ KEPT)
final_score = provider_weight × base_score  # 0.68 × 0.85 = 0.578 (wrong!)
```

**Impact**: Wikipedia results penalized 38% more than intended (0.7225× instead of 0.85×).

---

## Solution: Single Application Architecture

### Core Principle

> **Provider weights SHALL be applied exclusively in the ranking module.**

### Three-Layer Pipeline

```
┌────────────────────────────────────────┐
│ 1. LOOKUP: Fetch Raw Confidence       │
│    Wikipedia: 0.8 (API relevance)     │
│    ⚠️ NO WEIGHTS APPLIED               │
└────────────────────────────────────────┘
                  ↓
┌────────────────────────────────────────┐
│ 2. BOOST: Content-Based Scoring       │
│    Wikipedia: 0.8 (no boost)          │
│    Overheid:  0.6 × 1.1 = 0.66        │
│    ⚠️ NO WEIGHTS APPLIED               │
└────────────────────────────────────────┘
                  ↓
┌────────────────────────────────────────┐
│ 3. RANKING: Apply Provider Weights    │
│    Wikipedia: 0.8 × 0.85 = 0.68       │
│    Overheid:  0.66 × 1.0 = 0.66       │
│    ✅ WEIGHTS APPLIED ONCE (HERE)      │
└────────────────────────────────────────┘
```

---

## Architectural Decisions

### ADR-001: Weight Only in Ranking

**Decision**: Provider weights applied exclusively in `ranking.py`.

**Why Ranking?**
- Natural place for cross-source comparison
- Single responsibility (lookup = fetch, ranking = compare)
- Easier to debug (inspect raw scores before weighting)
- Testable in isolation

**Why NOT Lookup?**
- Lookup methods have no context of other sources
- Mixed responsibility (fetch + score)
- Harder to test (must mock weights)

---

## Key Design Features

### 1. Type Safety (Future Phase)

```python
@dataclass(frozen=True)  # Immutable
class RawConfidence:
    """Raw API confidence - NEVER weighted."""
    value: float  # 0.0 - 1.0

@dataclass(frozen=True)
class BoostedConfidence:
    """After content boost - NO provider weight yet."""
    raw: RawConfidence
    boost_factor: float  # >= 1.0

@dataclass(frozen=True)
class WeightedScore:
    """Final score - provider weight applied ONCE."""
    boosted: BoostedConfidence
    provider_weight: float  # 0.0 - 1.0

    # ✅ Type system PREVENTS double-weighting
    # ❌ Cannot multiply WeightedScore × weight (type error)
```

### 2. Configuration Separation

```yaml
# EXPLICIT: Provider authority weights (ranking layer)
provider_weights:
  _metadata:
    application_layer: "ranking"  # ✅ Explicit declaration
  wikipedia: 0.85
  sru_overheid: 1.0

# EXPLICIT: Content boost factors (boost layer)
juridical_boost:
  _metadata:
    application_layer: "boost"  # ✅ Separate section
  juridische_bron: 1.2
  keyword_per_match: 1.1
```

### 3. Quality Gate

Prevents low-quality juridical sources from outranking high-quality relevant sources:

```yaml
quality_gate:
  enabled: true
  min_base_score: 0.65        # Threshold
  reduced_boost_factor: 0.5   # Penalty below threshold
```

**Example**:
```
Overheid.nl: 0.5 raw < 0.65 threshold
→ Reduced boost: 1.0 + (1.2-1.0)×0.5 = 1.1 (not 1.2)
→ Prevents low-quality juridical from beating high-quality relevant
```

---

## Validation & Testing

### Automated Validation

```bash
# Run architecture validation
python scripts/validate_provider_weighting.py

# Expected output:
# ✅ ALL CHECKS PASSED - Provider weighting architecture is valid!
```

**Validates**:
- ✅ No weight applications in lookup methods
- ✅ Documentation comments present
- ✅ Ranking module applies weights
- ✅ Config structure valid

### Test Strategy

**Unit Tests** (Lookup Layer):
```python
def test_lookup_returns_raw_confidence():
    """Verify lookup returns RAW confidence (no weight)."""
    result = await service._lookup_wikipedia("test")
    assert result.source.confidence == 0.8  # Raw, NOT 0.68
```

**Integration Tests** (End-to-End):
```python
def test_weight_applied_once():
    """Verify provider weight applied ONCE in ranking."""
    results = await service.lookup(request)
    # Wikipedia: 0.8 × 0.85 = 0.68 (not 0.8 × 0.85 × 0.85 = 0.578)
    assert results[0].source.confidence == 0.68
```

**Property Tests** (Mathematical):
```python
@given(confidence=floats(0.0, 1.0), weight=floats(0.0, 1.0))
def test_weighting_is_bounded(confidence, weight):
    """Final score always in [0, 1]."""
    score = WeightedScore(confidence, weight)
    assert 0.0 <= score.value <= 1.0
```

---

## Migration Checklist (New Providers)

When adding a new provider:

- [ ] Lookup method returns **raw confidence** (no weight)
- [ ] Add comment: `"Provider weight applied in ranking, not here"`
- [ ] Add provider weight to `config/web_lookup_defaults.yaml`
- [ ] Update `_infer_provider_key()` in ranking
- [ ] Write unit test: Verify raw confidence returned
- [ ] Write integration test: Verify single weight application

---

## Impact Analysis

### Before Fix (Double-Weighted)

```
Wikipedia:   0.8 × 0.85 × 0.85 = 0.578 (38% penalty!)
Overheid.nl: 0.6 × 1.0 × 1.0  = 0.6
Result: Overheid wins (incorrect)
```

### After Fix (Single-Weighted)

```
Wikipedia:   0.8 × 0.85 = 0.68 (15% penalty - intended)
Overheid.nl: 0.6 × 1.0  = 0.6
Result: Wikipedia wins (correct) ✅
```

---

## Benefits

### Immediate
- ✅ Bug fixed (double-weighting eliminated)
- ✅ Simpler code (single responsibility per layer)
- ✅ Easier debugging (inspect raw scores before weighting)
- ✅ Validated architecture (automated checks)

### Long-Term
- 🔄 Type safety (Phase 2) - Compile-time prevention
- 🔄 Observability (Phase 2) - Trace transformations
- 🔄 Configuration UI (Phase 3) - Non-technical weight tuning

---

## References

| Document | Purpose |
|----------|---------|
| `provider-weighting-architecture-design.md` | Full technical design |
| `double-weighting-bug-analysis.md` | Bug investigation & fix |
| `scripts/validate_provider_weighting.py` | Automated validation |
| `ADR-001-weight-only-in-ranking.md` | Architecture decision record |

---

## Quick Commands

```bash
# Validate architecture
python scripts/validate_provider_weighting.py

# Run weighting tests
pytest tests/services/test_modern_web_lookup_service_unit.py -k "confidence"
pytest tests/integration/test_web_lookup_weighting.py

# Check for weight applications (should be NONE in lookup methods)
grep -n "confidence_weight" src/services/modern_web_lookup_service.py
```

---

## Status: ✅ VALIDATED

- Architecture validated: 2025-10-09
- All checks passed: 4/4
- Implementation complete: Yes
- Tests passing: Yes (existing tests updated)
- Documentation complete: Yes

**Recommendation**: Architecture is production-ready. Consider Phase 2 type safety for additional compile-time protection.
