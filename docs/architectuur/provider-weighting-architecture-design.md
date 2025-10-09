# Provider Weighting Architecture Design

**Date**: 2025-10-09
**Author**: Claude Code (Solution Design)
**Status**: DESIGN PROPOSAL
**Related**: `docs/analyses/double-weighting-bug-analysis.md`

## Executive Summary

This document proposes a **robust, future-proof architecture** for provider weighting in the DefinitieAgent web lookup system. The design prevents double-weighting bugs through:

1. **Clear separation of concerns** - Intrinsic confidence vs extrinsic weights
2. **Type safety** - Explicit types prevent accidental re-weighting
3. **Single application point** - Weights applied ONLY in ranking module
4. **Configuration validation** - Schema ensures correct usage
5. **Test strategy** - Catches regressions at compile and runtime

---

## 1. Architecture Decision Record (ADR)

### ADR-001: Weight Only in Ranking Module

**Status**: RECOMMENDED
**Date**: 2025-10-09
**Context**: Double-weighting bug occurred when provider weights were applied in both lookup methods and ranking module.

#### Decision

Provider weights SHALL be applied **exclusively in the ranking module** (`src/services/web_lookup/ranking.py`). Lookup methods SHALL return **raw confidence scores** without weight application.

#### Rationale

| Criterion | Lookup Layer | Ranking Layer | Winner |
|-----------|--------------|---------------|--------|
| **Single Responsibility** | Fetch + Score = 2 concerns | Compare sources = 1 concern | Ranking ✅ |
| **Testability** | Must mock weights | Pure score testing | Ranking ✅ |
| **Debugging** | Hard to trace transformations | Explicit transformation point | Ranking ✅ |
| **Cross-source Comparison** | No context of other sources | Natural place for comparison | Ranking ✅ |
| **Configuration** | Duplicated weight config | Centralized config | Ranking ✅ |

#### Consequences

**Positive**:
- Single source of truth for provider weighting
- Easier to debug (inspect raw scores before ranking)
- Clearer data flow (fetch → boost → rank → weight)
- No hidden transformations in lookup layer

**Negative**:
- Breaking change (if code relied on weighted confidence in lookup results)
- Must document that `LookupResult.source.confidence` is raw, not weighted

**Mitigation**:
- Clear documentation in code comments
- Type system enforcement (see Section 2)
- Integration tests verify single application (see Section 5)

---

## 2. Interface Design

### 2.1 Core Types

We propose a **three-layer confidence model** that makes transformations explicit:

```python
from dataclasses import dataclass, field
from typing import Literal

@dataclass(frozen=True)  # Immutable - prevents accidental mutation
class RawConfidence:
    """
    Raw confidence from provider API (0.0 - 1.0).

    Represents intrinsic relevance score from the source:
    - Wikipedia relevance score
    - SRU result ranking score
    - API confidence metric

    This value is NEVER weighted by provider authority.
    """
    value: float  # 0.0 - 1.0

    def __post_init__(self):
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"Confidence must be 0-1, got {self.value}")

    def __float__(self) -> float:
        return self.value

    def __str__(self) -> str:
        return f"Raw({self.value:.2f})"


@dataclass(frozen=True)
class BoostedConfidence:
    """
    Confidence after juridical content boost (>= raw confidence).

    Boosts applied:
    - Juridical source boost (quality-gated, from config)
    - Keyword matches (juridische_keywords.yaml)
    - Article references (Art. 123)
    - Context matches (user-provided context)

    Provider weight NOT applied yet.
    """
    raw: RawConfidence
    boost_factor: float  # >= 1.0

    @property
    def value(self) -> float:
        """Boosted value (clamped to 1.0)."""
        return min(self.raw.value * self.boost_factor, 1.0)

    def __post_init__(self):
        if self.boost_factor < 1.0:
            raise ValueError(f"Boost must be >= 1.0, got {self.boost_factor}")

    def __float__(self) -> float:
        return self.value

    def __str__(self) -> str:
        return f"Boosted({self.value:.2f}=raw:{self.raw.value:.2f}×{self.boost_factor:.2f})"


@dataclass(frozen=True)
class WeightedScore:
    """
    Final score after provider weight application (ranking layer only).

    This is the ONLY place where provider weights are applied.
    Formula: boosted_confidence × provider_weight

    Example:
        Wikipedia: 0.8 (raw) × 1.1 (boost) × 0.85 (weight) = 0.748 (final)
        Overheid:  0.6 (raw) × 1.0 (boost) × 1.0 (weight)  = 0.600 (final)
    """
    boosted: BoostedConfidence
    provider_weight: float  # 0.0 - 1.0 (typically 0.5 - 1.0)

    @property
    def value(self) -> float:
        """Final weighted score."""
        return self.boosted.value * self.provider_weight

    def __post_init__(self):
        if not 0.0 <= self.provider_weight <= 1.0:
            raise ValueError(f"Weight must be 0-1, got {self.provider_weight}")

    def __float__(self) -> float:
        return self.value

    def __str__(self) -> str:
        return (
            f"Weighted({self.value:.2f}="
            f"boosted:{self.boosted.value:.2f}×weight:{self.provider_weight:.2f})"
        )

    @property
    def breakdown(self) -> dict[str, float]:
        """Full breakdown for debugging."""
        return {
            "raw": self.boosted.raw.value,
            "boost_factor": self.boosted.boost_factor,
            "boosted": self.boosted.value,
            "provider_weight": self.provider_weight,
            "final": self.value,
        }
```

### 2.2 Updated Interfaces

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class WebSource:
    """Web source metadata."""
    name: str
    url: str
    confidence: RawConfidence  # CHANGED: Was float, now RawConfidence
    api_type: str
    is_juridical: bool = False


@dataclass
class LookupResult:
    """
    Result from a single lookup operation.

    IMPORTANT: confidence is RAW, not weighted by provider authority.
    Provider weights are applied in ranking module only.
    """
    term: str
    source: WebSource
    definition: str
    success: bool
    context: str | None = None
    metadata: dict[str, Any] | None = None

    @property
    def raw_confidence(self) -> float:
        """Raw confidence from API (convenience accessor)."""
        return float(self.source.confidence)
```

### 2.3 Migration Path

**Phase 1: Non-breaking addition** (current state - already done)
```python
# Lookup methods return float confidence (raw, no weight)
result.source.confidence = 0.8  # No weight applied ✅

# Ranking applies weight
final_score = 0.8 × 0.85  # Single application ✅
```

**Phase 2: Type safety (future enhancement)**
```python
# Lookup methods return RawConfidence
result.source.confidence = RawConfidence(0.8)

# Boost layer returns BoostedConfidence
boosted_confidence = BoostedConfidence(raw=RawConfidence(0.8), boost_factor=1.1)

# Ranking layer returns WeightedScore
final_score = WeightedScore(boosted=boosted_confidence, provider_weight=0.85)

# Type system PREVENTS double-weighting:
# ❌ Cannot multiply WeightedScore by weight again (type error)
# ❌ Cannot pass BoostedConfidence to lookup (type error)
```

---

## 3. Configuration Design

### 3.1 Current Config Structure

**File**: `config/web_lookup_defaults.yaml`

```yaml
web_lookup:
  providers:
    wikipedia:
      enabled: true
      weight: 0.85        # APPLIED IN: ranking module ONLY
      timeout: 5
      min_score: 0.3

    sru_overheid:
      enabled: true
      weight: 1.0         # APPLIED IN: ranking module ONLY
      timeout: 5
      min_score: 0.4

  juridical_boost:
    # Quality gate (controls WHEN boost is applied)
    quality_gate:
      enabled: true
      min_base_score: 0.65
      reduced_boost_factor: 0.5

    # Boost factors (APPLIED IN: boost layer, before ranking)
    juridische_bron: 1.2       # NOT a provider weight!
    keyword_per_match: 1.1
    artikel_referentie: 1.15
```

### 3.2 Proposed Config Schema with Validation

```yaml
web_lookup:
  # EXPLICIT SECTION: Provider authority weights (ranking layer)
  provider_weights:
    _metadata:
      description: "Provider authority weights - APPLIED IN RANKING MODULE ONLY"
      application_layer: "ranking"  # Explicit declaration
      valid_range: [0.0, 1.0]

    wikipedia: 0.85
    sru_overheid: 1.0
    rechtspraak_ecli: 0.95
    wiktionary: 0.65
    brave_search: 0.70

  # EXPLICIT SECTION: Content boost factors (boost layer)
  juridical_boost:
    _metadata:
      description: "Content-based boost factors - APPLIED IN BOOST LAYER"
      application_layer: "boost"
      valid_range: [1.0, 2.0]  # Boost factors must be >= 1.0

    quality_gate:
      enabled: true
      min_base_score: 0.65
      reduced_boost_factor: 0.5

    # Source-based boosts (quality-gated)
    juridische_bron: 1.2
    juridical_flag: 1.15

    # Content-based boosts (not gated)
    keyword_per_match: 1.1
    keyword_max_boost: 1.3
    artikel_referentie: 1.15
    lid_referentie: 1.05
    context_match: 1.1
    context_max_boost: 1.3
```

### 3.3 Config Validation

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class ConfigMetadata:
    """Metadata for config validation."""
    description: str
    application_layer: Literal["lookup", "boost", "ranking"]
    valid_range: tuple[float, float]


class WebLookupConfigValidator:
    """Validates web lookup configuration."""

    def validate(self, config: dict) -> list[str]:
        """
        Validate config structure and values.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate provider weights
        weights = config.get("web_lookup", {}).get("provider_weights", {})
        for provider, weight in weights.items():
            if provider == "_metadata":
                continue

            if not isinstance(weight, (int, float)):
                errors.append(f"provider_weights.{provider}: must be numeric")
            elif not 0.0 <= weight <= 1.0:
                errors.append(
                    f"provider_weights.{provider}: {weight} not in [0.0, 1.0]"
                )

        # Validate boost factors
        boost = config.get("web_lookup", {}).get("juridical_boost", {})
        for key, value in boost.items():
            if key in ("_metadata", "quality_gate"):
                continue

            if not isinstance(value, (int, float)):
                errors.append(f"juridical_boost.{key}: must be numeric")
            elif value < 1.0:
                errors.append(
                    f"juridical_boost.{key}: {value} < 1.0 (boost must be >= 1.0)"
                )

        return errors

    def validate_no_overlap(self, config: dict) -> list[str]:
        """
        Validate that provider weights are not used as boost factors.

        This prevents confusion where same config key is used in multiple layers.
        """
        errors = []

        weights = set(
            config.get("web_lookup", {}).get("provider_weights", {}).keys()
        )
        boost_keys = set(
            config.get("web_lookup", {}).get("juridical_boost", {}).keys()
        )

        overlap = weights & boost_keys - {"_metadata"}
        if overlap:
            errors.append(
                f"Config keys appear in both provider_weights AND juridical_boost: {overlap}"
            )

        return errors
```

---

## 4. Data Flow Architecture

### 4.1 Pipeline Stages

```
┌────────────────────────────────────────────────────────────────┐
│ STAGE 1: LOOKUP (Fetch Raw Data)                              │
│ Location: src/services/modern_web_lookup_service.py           │
│ Output: LookupResult with RawConfidence                        │
├────────────────────────────────────────────────────────────────┤
│ Wikipedia: 0.8 (raw relevance from API)                       │
│ Overheid:  0.6 (raw relevance from SRU)                       │
│                                                                 │
│ ⚠️ NO PROVIDER WEIGHTS APPLIED                                 │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ STAGE 2: BOOST (Content-Based Scoring)                        │
│ Location: src/services/web_lookup/juridisch_ranker.py         │
│ Output: LookupResult with BoostedConfidence                    │
├────────────────────────────────────────────────────────────────┤
│ Wikipedia: 0.8 (no boost, not juridical)                      │
│ Overheid:  0.6 × 1.1 (juridical boost) = 0.66                 │
│                                                                 │
│ Quality Gate Applied:                                          │
│   - Only sources with base_score >= 0.65 get full boost       │
│   - Overheid 0.6 < 0.65 → reduced boost (50%)                 │
│   - Result: 0.6 × (1.0 + (1.1-1.0)×0.5) = 0.63               │
│                                                                 │
│ ⚠️ NO PROVIDER WEIGHTS APPLIED                                 │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ STAGE 3: RANKING (Cross-Source Comparison)                    │
│ Location: src/services/web_lookup/ranking.py                  │
│ Output: Ranked list with WeightedScore                         │
├────────────────────────────────────────────────────────────────┤
│ Wikipedia: 0.8 × 0.85 (provider weight) = 0.68                │
│ Overheid:  0.63 × 1.0 (provider weight) = 0.63                │
│                                                                 │
│ Final Ranking: Wikipedia (0.68) > Overheid (0.63) ✅           │
│                                                                 │
│ ✅ PROVIDER WEIGHTS APPLIED ONCE (ONLY HERE)                   │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 Code Flow

```python
# STAGE 1: LOOKUP
async def _lookup_wikipedia(term, source, request):
    # Fetch from API
    result = await wikipedia_lookup(term)

    # Return RAW confidence (no weight)
    result.source.confidence = RawConfidence(0.8)  # From API relevance

    # ✅ CORRECT: No provider weight applied
    return result


# STAGE 2: BOOST
def boost_juridische_resultaten(results, context):
    for result in results:
        # Calculate boost based on content
        boost_factor = calculate_juridische_boost(result, context)

        # Apply boost to confidence
        raw = result.source.confidence  # RawConfidence
        result.source.confidence = BoostedConfidence(
            raw=raw,
            boost_factor=boost_factor
        )

    # ✅ CORRECT: No provider weight applied
    return results


# STAGE 3: RANKING
def rank_and_dedup(items, provider_weights):
    def _final_score(item):
        provider = item.get("provider", "")
        weight = provider_weights.get(provider, 1.0)
        boosted = float(item.get("score", 0.0))  # BoostedConfidence

        # ✅ CORRECT: Provider weight applied ONLY here
        return WeightedScore(
            boosted=BoostedConfidence(
                raw=RawConfidence(item["raw_score"]),
                boost_factor=item["boost_factor"]
            ),
            provider_weight=weight
        )

    return sorted(items, key=_final_score, reverse=True)
```

---

## 5. Test Strategy

### 5.1 Unit Tests - Lookup Layer

**Goal**: Verify lookup returns RAW confidence (no weight applied)

```python
# File: tests/services/test_modern_web_lookup_service_unit.py

import pytest
from services.modern_web_lookup_service import ModernWebLookupService


@pytest.mark.asyncio
async def test_wikipedia_lookup_returns_raw_confidence():
    """Wikipedia lookup should return UN-weighted confidence."""
    service = ModernWebLookupService()

    # Mock Wikipedia API to return 0.8 relevance
    with patch("services.web_lookup.wikipedia_service.wikipedia_lookup") as mock:
        mock_result = LookupResult(
            term="test",
            source=WebSource(
                name="Wikipedia",
                url="https://nl.wikipedia.org/wiki/Test",
                confidence=RawConfidence(0.8),  # Raw score from API
                api_type="mediawiki"
            ),
            definition="Test definition",
            success=True
        )
        mock.return_value = mock_result

        # Lookup
        result = await service._lookup_mediawiki(
            "test",
            service.sources["wikipedia"],
            LookupRequest(term="test")
        )

        # Verify: confidence is RAW (0.8), NOT weighted (0.8 × 0.85 = 0.68)
        assert result.source.confidence.value == 0.8  # ✅ Raw
        assert result.source.confidence.value != 0.68  # ✅ Not weighted


@pytest.mark.asyncio
async def test_sru_lookup_returns_raw_confidence():
    """SRU lookup should return UN-weighted confidence."""
    service = ModernWebLookupService()

    with patch("services.web_lookup.sru_service.SRUService") as MockSRU:
        mock_sru = MockSRU.return_value.__aenter__.return_value
        mock_sru.search.return_value = [
            LookupResult(
                term="test",
                source=WebSource(
                    name="Overheid.nl",
                    url="https://overheid.nl/test",
                    confidence=RawConfidence(0.6),  # Raw SRU score
                    api_type="sru",
                    is_juridical=True
                ),
                definition="Test definition",
                success=True
            )
        ]

        result = await service._lookup_sru(
            "test",
            service.sources["overheid"],
            LookupRequest(term="test")
        )

        # Verify: confidence is RAW (0.6), NOT weighted (0.6 × 1.0 = 0.6)
        # (same value, but semantically different - it's raw, not weighted)
        assert result.source.confidence.value == 0.6
        assert isinstance(result.source.confidence, RawConfidence)
```

### 5.2 Unit Tests - Boost Layer

**Goal**: Verify boost applied without provider weight

```python
# File: tests/services/web_lookup/test_juridisch_ranker.py

def test_boost_juridische_bron_without_provider_weight():
    """Juridical boost should NOT include provider weight."""
    result = LookupResult(
        term="test",
        source=WebSource(
            name="Overheid.nl",
            url="https://wetten.overheid.nl/test",
            confidence=RawConfidence(0.6),  # Raw confidence
            api_type="sru",
            is_juridical=True
        ),
        definition="Artikel 123: Test definitie",
        success=True
    )

    # Calculate boost (should be content-based only)
    boost_factor = calculate_juridische_boost(result, context=None)

    # Boost includes: juridical source (1.2×), artikel ref (1.15×)
    # Expected: 1.2 × 1.15 = 1.38
    assert 1.35 <= boost_factor <= 1.40

    # Apply boost
    boosted = BoostedConfidence(
        raw=result.source.confidence,
        boost_factor=boost_factor
    )

    # Verify: boosted value is 0.6 × 1.38 = 0.828 (clamped to 0.828)
    # NOT multiplied by provider weight (1.0)
    assert 0.82 <= boosted.value <= 0.84
    assert boosted.value != 0.6  # Changed from raw
    assert boosted.value != 0.828 * 1.0  # Not weighted yet


def test_quality_gate_reduces_boost_for_low_quality():
    """Quality gate should reduce boost for base_score < threshold."""
    # Low quality source (0.5 < 0.65 threshold)
    result = LookupResult(
        term="test",
        source=WebSource(
            name="Overheid.nl",
            url="https://overheid.nl/test",
            confidence=RawConfidence(0.5),  # Below threshold
            api_type="sru",
            is_juridical=True
        ),
        definition="Test definitie",
        success=True
    )

    # Calculate boost with quality gate
    boost_factor = calculate_juridische_boost(result, context=None)

    # Expected: reduced boost (50% of 1.2×) = 1.0 + (1.2-1.0)×0.5 = 1.1
    assert 1.08 <= boost_factor <= 1.12
```

### 5.3 Integration Tests - End-to-End

**Goal**: Verify single weight application through entire pipeline

```python
# File: tests/integration/test_web_lookup_weighting.py

@pytest.mark.asyncio
async def test_provider_weight_applied_once_in_ranking():
    """
    Integration test: Provider weight applied ONCE in ranking.

    Scenario:
        Wikipedia: 0.8 raw, 0.85 weight → 0.68 final
        Overheid:  0.6 raw, 1.0 weight  → 0.6 final (no boost due to low quality)

    Expected: Wikipedia wins (0.68 > 0.6)
    """
    service = ModernWebLookupService()

    # Mock lookups
    with patch.multiple(
        service,
        _lookup_mediawiki=AsyncMock(return_value=LookupResult(
            term="test",
            source=WebSource(
                name="Wikipedia",
                url="https://nl.wikipedia.org/wiki/Test",
                confidence=RawConfidence(0.8),  # Raw
                api_type="mediawiki"
            ),
            definition="High quality relevant definition",
            success=True
        )),
        _lookup_sru=AsyncMock(return_value=LookupResult(
            term="test",
            source=WebSource(
                name="Overheid.nl",
                url="https://overheid.nl/test",
                confidence=RawConfidence(0.6),  # Raw
                api_type="sru",
                is_juridical=True
            ),
            definition="Low quality juridical definition",
            success=True
        ))
    ):
        # Execute full lookup pipeline
        results = await service.lookup(
            LookupRequest(term="test", max_results=5)
        )

        # Verify ranking
        assert len(results) >= 2

        # Top result should be Wikipedia (0.68 > 0.6)
        top = results[0]
        assert "wikipedia" in top.source.url.lower()

        # Verify confidence values
        # NOTE: After ranking, confidence is weighted
        wikipedia_result = next(r for r in results if "wikipedia" in r.source.url.lower())
        overheid_result = next(r for r in results if "overheid" in r.source.url.lower())

        # Wikipedia: 0.8 × 0.85 = 0.68
        assert 0.67 <= float(wikipedia_result.source.confidence) <= 0.69

        # Overheid: 0.6 × 1.0 = 0.6 (no boost due to quality gate)
        assert 0.59 <= float(overheid_result.source.confidence) <= 0.61

        # Verify no double-weighting occurred
        # If double-weighted: 0.8 × 0.85 × 0.85 = 0.578 (wrong)
        assert float(wikipedia_result.source.confidence) >= 0.65  # Not 0.578


@pytest.mark.asyncio
async def test_quality_gate_prevents_low_quality_juridical_outranking():
    """
    Quality gate should prevent low-quality juridical from outranking
    high-quality relevant sources.

    Scenario:
        Wikipedia: 0.8 raw, no boost, 0.85 weight → 0.68 final
        Overheid:  0.5 raw (low quality), 1.1× boost (reduced), 1.0 weight → 0.55 final

    Expected: Wikipedia wins (0.68 > 0.55)
    """
    service = ModernWebLookupService()

    # ... (similar setup as above, but Overheid has 0.5 raw score)

    results = await service.lookup(LookupRequest(term="test"))

    # Wikipedia should win despite Overheid being juridical
    assert "wikipedia" in results[0].source.url.lower()
```

### 5.4 Property-Based Tests

**Goal**: Verify mathematical properties hold under all conditions

```python
# File: tests/properties/test_weighting_properties.py

from hypothesis import given, strategies as st

@given(
    raw_confidence=st.floats(min_value=0.0, max_value=1.0),
    boost_factor=st.floats(min_value=1.0, max_value=2.0),
    provider_weight=st.floats(min_value=0.0, max_value=1.0)
)
def test_weighting_is_monotonic(raw_confidence, boost_factor, provider_weight):
    """
    Property: Higher raw confidence → Higher final score (all else equal).
    """
    score1 = WeightedScore(
        boosted=BoostedConfidence(
            raw=RawConfidence(raw_confidence),
            boost_factor=boost_factor
        ),
        provider_weight=provider_weight
    )

    # Higher raw confidence
    score2 = WeightedScore(
        boosted=BoostedConfidence(
            raw=RawConfidence(min(raw_confidence + 0.1, 1.0)),
            boost_factor=boost_factor
        ),
        provider_weight=provider_weight
    )

    assert score2.value >= score1.value


@given(
    raw_confidence=st.floats(min_value=0.0, max_value=1.0),
    boost_factor=st.floats(min_value=1.0, max_value=2.0),
    provider_weight=st.floats(min_value=0.0, max_value=1.0)
)
def test_weighting_is_bounded(raw_confidence, boost_factor, provider_weight):
    """
    Property: Final score always in [0, 1] regardless of inputs.
    """
    score = WeightedScore(
        boosted=BoostedConfidence(
            raw=RawConfidence(raw_confidence),
            boost_factor=boost_factor
        ),
        provider_weight=provider_weight
    )

    assert 0.0 <= score.value <= 1.0


@given(
    raw_confidence=st.floats(min_value=0.0, max_value=1.0),
    boost_factor=st.floats(min_value=1.0, max_value=2.0)
)
def test_boost_never_decreases_confidence(raw_confidence, boost_factor):
    """
    Property: Boost factor >= 1.0 → Boosted >= Raw.
    """
    boosted = BoostedConfidence(
        raw=RawConfidence(raw_confidence),
        boost_factor=boost_factor
    )

    assert boosted.value >= raw_confidence
```

---

## 6. Migration & Validation Plan

### 6.1 Current State Validation

The fix has been applied. Verify completeness:

#### Checklist: All Weight Applications Removed from Lookup

- [ ] **`_lookup_mediawiki` (Wikipedia branch)**: Line ~602
  - Check: No `result.source.confidence *= source.confidence_weight`
  - Comment: "Provider weight applied in ranking, not here"

- [ ] **`_lookup_mediawiki` (Wiktionary branch)**: Line ~680
  - Check: No weight application
  - Comment: Present

- [ ] **`_lookup_sru` (Main stage loop)**: Line ~758
  - Check: No weight application
  - Comment: Present

- [ ] **`_lookup_sru` (Fallback loop)**: Line ~785
  - Check: Only 0.95 penalty (intrinsic quality), NOT provider weight
  - Comment: Distinguishes fallback penalty from provider weight

- [ ] **`_lookup_rest` (Rechtspraak lookup)**: Line ~828
  - Check: No weight application
  - Comment: Present

- [ ] **`_lookup_brave` (Brave Search lookup)**: Line ~906
  - Check: No weight application
  - Comment: Present

#### Verification Commands

```bash
# Search for any remaining weight applications in lookup methods
grep -n "confidence_weight" src/services/modern_web_lookup_service.py

# Expected: Only in __init__ (line 52, 134, etc.) for config loading
# NOT in _lookup_* methods

# Verify comments are present
grep -B2 -A2 "Provider weight applied in ranking" src/services/modern_web_lookup_service.py

# Expected: 6 occurrences (one per lookup method)
```

### 6.2 Performance Testing

**Goal**: Verify fix doesn't impact performance

```bash
# Benchmark lookup performance
pytest tests/performance/test_lookup_benchmarks.py -v

# Expected metrics:
# - Lookup time: < 5 seconds (unchanged)
# - Boost time: < 100ms (unchanged)
# - Ranking time: < 50ms (unchanged)
```

```python
# File: tests/performance/test_lookup_benchmarks.py

import time
import pytest

@pytest.mark.asyncio
async def test_lookup_performance_baseline():
    """Verify lookup performance unchanged after fix."""
    service = ModernWebLookupService()

    start = time.time()
    results = await service.lookup(
        LookupRequest(term="voorlopige hechtenis", max_results=5)
    )
    duration = time.time() - start

    assert len(results) > 0
    assert duration < 5.0  # Max 5 seconds for lookup

    # Log for tracking
    print(f"Lookup duration: {duration:.2f}s for {len(results)} results")
```

### 6.3 Regression Prevention

**Add to CI pipeline**:

```yaml
# .github/workflows/ci.yml

- name: Run weighting regression tests
  run: |
    # Unit tests - verify raw confidence in lookups
    pytest tests/services/test_modern_web_lookup_service_unit.py \
      -k "raw_confidence" -v

    # Integration tests - verify single weight application
    pytest tests/integration/test_web_lookup_weighting.py \
      -k "weight_applied_once" -v

    # Property tests - verify mathematical properties
    pytest tests/properties/test_weighting_properties.py -v

    # Fail if any test fails
    if [ $? -ne 0 ]; then
      echo "❌ Weighting regression detected!"
      exit 1
    fi

    echo "✅ All weighting tests passed"
```

---

## 7. Documentation Updates

### 7.1 Code Comments

**Add to `src/services/modern_web_lookup_service.py`**:

```python
class ModernWebLookupService:
    """
    Modern web lookup service with single-responsibility layers.

    ARCHITECTURE: Provider Weighting
    ================================

    Provider weights are applied EXCLUSIVELY in the ranking module.
    Lookup methods return RAW confidence scores (0-1) from APIs.

    Data Flow:
        1. Lookup → RawConfidence (no weight)
        2. Boost  → BoostedConfidence (content-based, no weight)
        3. Ranking → WeightedScore (provider weight applied ONCE)

    WHY: This prevents double-weighting bugs where provider weights
    were accidentally applied in both lookup AND ranking layers.

    See: docs/architectuur/provider-weighting-architecture-design.md
    """
```

### 7.2 ADR Documentation

**Create**: `docs/architectuur/ADR-001-weight-only-in-ranking.md`

```markdown
# ADR-001: Weight Provider Authority Only in Ranking Module

**Status**: Accepted
**Date**: 2025-10-09
**Supersedes**: None

## Context

Provider weights were applied in both lookup methods and ranking module,
causing double-weighting bug (Epic 3, Oct 2025).

## Decision

Provider weights SHALL be applied exclusively in ranking module.

## Consequences

- Lookup methods return raw confidence (easier to debug)
- Single source of truth for weighting (prevents bugs)
- Breaking change for code relying on weighted lookup results

## Compliance

Verify with:
```bash
grep -n "confidence_weight" src/services/modern_web_lookup_service.py
# Should NOT appear in _lookup_* methods
```
```

### 7.3 Architecture Documentation

**Update**: `docs/architectuur/TECHNICAL_ARCHITECTURE.md`

Add section:

```markdown
## Web Lookup Confidence Scoring

### Three-Layer Model

1. **Raw Confidence** (Lookup Layer)
   - Source: API relevance score (Wikipedia, SRU, etc.)
   - Range: 0.0 - 1.0
   - Location: `result.source.confidence` (type: `RawConfidence`)

2. **Boosted Confidence** (Boost Layer)
   - Source: Juridical content analysis
   - Factors: Keywords, article refs, context matches
   - Range: >= Raw confidence (capped at 1.0)
   - Location: Applied by `boost_juridische_resultaten()`

3. **Weighted Score** (Ranking Layer)
   - Source: Provider authority weighting
   - Factors: Provider trust level (wikipedia=0.85, overheid=1.0)
   - Range: 0.0 - 1.0
   - Location: Applied by `rank_and_dedup()`

### Quality Gate

Prevents low-quality juridical sources from outranking high-quality
relevant sources:

- Threshold: `min_base_score = 0.65` (configurable)
- Below threshold: Reduced boost (50% of nominal)
- Above threshold: Full boost applied

Example:
```
Overheid.nl: 0.6 raw < 0.65 threshold
→ Reduced boost: 1.0 + (1.2-1.0)×0.5 = 1.1
→ Boosted: 0.6 × 1.1 = 0.66
→ Weighted: 0.66 × 1.0 = 0.66

Wikipedia: 0.8 raw (no boost, not juridical)
→ Weighted: 0.8 × 0.85 = 0.68

Result: Wikipedia wins (0.68 > 0.66) ✅
```
```

---

## 8. Future Enhancements

### 8.1 Type Safety (Phase 2)

**Goal**: Compile-time prevention of double-weighting

**Implementation**:

1. Introduce `RawConfidence`, `BoostedConfidence`, `WeightedScore` types
2. Update all function signatures to use explicit types
3. Add type checking to CI pipeline

**Benefit**: TypeErrors prevent double-weighting at development time.

### 8.2 Observability

**Goal**: Debug weighting issues in production

**Implementation**:

```python
@dataclass
class ConfidenceTrace:
    """Audit trail for confidence transformations."""
    raw: float
    boost_factor: float
    boosted: float
    provider_weight: float
    final: float
    transformations: list[str]  # ["raw → boosted", "boosted → weighted"]

    def to_json(self) -> dict:
        return {
            "raw": self.raw,
            "boost_factor": self.boost_factor,
            "boosted": self.boosted,
            "provider_weight": self.provider_weight,
            "final": self.final,
            "transformations": self.transformations
        }


# Attach to LookupResult
result.metadata["confidence_trace"] = ConfidenceTrace(
    raw=0.8,
    boost_factor=1.0,
    boosted=0.8,
    provider_weight=0.85,
    final=0.68,
    transformations=["raw (0.8)", "no boost (×1.0)", "weighted (×0.85 = 0.68)"]
)
```

**Benefit**: Full visibility into score calculation for debugging.

### 8.3 Configuration UI

**Goal**: Allow non-technical users to adjust provider weights

**Implementation**:

- Admin panel in Streamlit app
- Live preview of ranking changes
- Validation prevents invalid configs

**Benefit**: Easier weight tuning without code changes.

---

## 9. Appendix: Bug Prevention Checklist

Use this checklist when adding new providers:

### New Provider Implementation Checklist

- [ ] **Lookup method returns RAW confidence**
  - [ ] No `result.source.confidence *= weight`
  - [ ] Add comment: "Provider weight applied in ranking, not here"

- [ ] **Provider weight added to config**
  - [ ] Add to `config/web_lookup_defaults.yaml` under `provider_weights`
  - [ ] Value in range [0.0, 1.0]
  - [ ] Add comment explaining authority level

- [ ] **Provider key added to ranking**
  - [ ] Update `self._provider_weights` in `ModernWebLookupService.__init__`
  - [ ] Update `_infer_provider_key()` method

- [ ] **Tests added**
  - [ ] Unit test: Lookup returns raw confidence
  - [ ] Integration test: Verify single weight application
  - [ ] End-to-end test: Verify correct ranking vs existing providers

- [ ] **Documentation updated**
  - [ ] Add provider to architecture docs
  - [ ] Document authority level reasoning

---

## 10. Conclusion

This architecture design provides **robust protection** against double-weighting bugs through:

1. **Clear separation of concerns** - Lookup fetches, boost enhances, ranking weights
2. **Type safety** (future) - Compile-time prevention of re-weighting
3. **Single application point** - Provider weights ONLY in ranking module
4. **Configuration validation** - Schema prevents invalid configs
5. **Comprehensive testing** - Unit, integration, and property tests
6. **Excellent observability** - Trace transformations for debugging

The design is **future-proof** and **extensible** - new providers can be added safely by following the checklist, and the type system (Phase 2) will catch errors at compile time.

**Recommended Next Steps**:

1. ✅ **Immediate**: Validate fix completeness (Section 6.1)
2. ✅ **Short-term**: Add integration tests (Section 5.3)
3. 🔄 **Medium-term**: Implement type safety (Section 8.1)
4. 🔄 **Long-term**: Add observability (Section 8.2)

---

**References**:
- Bug Analysis: `docs/analyses/double-weighting-bug-analysis.md`
- Config: `config/web_lookup_defaults.yaml`
- Implementation: `src/services/modern_web_lookup_service.py`
- Ranking: `src/services/web_lookup/ranking.py`
- Boost: `src/services/web_lookup/juridisch_ranker.py`
