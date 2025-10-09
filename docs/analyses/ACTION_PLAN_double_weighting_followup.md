# ACTION PLAN: Double-Weighting Follow-up

**Date**: 2025-10-09
**Context**: Multi-agent consensus analysis complete
**Decision**: Balanced selective investment (5.75 hours)
**Status**: Ready to execute

---

## TL;DR

**DO**: 5.75 hours of strategic improvements
**SKIP**: 24+ hours of over-engineering
**THEN**: Build synonym management features

**ROI**: 143% (8.25h net value over 2 years)

---

## Week 1: Core Protection (3 hours)

### Day 1: End-to-End Integration Test (1.5 hours) ⭐⭐⭐⭐⭐

**File**: `tests/services/test_modern_web_lookup_integration.py`

**Goal**: Permanent safety net against double-weighting regression.

**Code**:
```python
import pytest
from services.interfaces import LookupRequest
from services.modern_web_lookup_service import ModernWebLookupService

@pytest.mark.asyncio()
async def test_confidence_scoring_end_to_end():
    """
    CRITICAL: Prevent double-weighting regression.

    Validates confidence flow: lookup → boost → ranking
    Ensures provider weights applied ONCE (ranking only).

    Expected flow:
    1. Lookup:  Wikipedia 0.8 (raw), Overheid 0.6 (raw)
    2. Boost:   Wikipedia 0.8 (no boost), Overheid 0.66 (1.1× boost)
    3. Ranking: Wikipedia 0.68 (0.8×0.85), Overheid 0.66 (0.66×1.0)
    4. Result:  Wikipedia wins (0.68 > 0.66)

    Reference: docs/analyses/double-weighting-bug-analysis.md
    """
    # Mock providers
    async def mock_wikipedia(term: str, language: str = "nl"):
        from services.interfaces import LookupResult, WebSource
        return LookupResult(
            term=term,
            source=WebSource(
                name="Wikipedia",
                url="https://nl.wikipedia.org/wiki/Test",
                confidence=0.8,  # RAW confidence
                is_juridical=False
            ),
            definition="Relevant Wikipedia definition with legal context",
            success=True
        )

    class MockSRU:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def search(self, term, endpoint, max_records):
            from services.interfaces import LookupResult, WebSource
            return [LookupResult(
                term=term,
                source=WebSource(
                    name="Overheid.nl",
                    url="https://wetten.overheid.nl/test",
                    confidence=0.6,  # RAW confidence (below quality gate)
                    is_juridical=True
                ),
                definition="Artikel 12 lid 1: Juridische definitie",
                success=True
            )]

    # Apply mocks
    import sys
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "services.web_lookup.wikipedia_service.wikipedia_lookup",
        mock_wikipedia
    )
    monkeypatch.setattr(
        "services.web_lookup.sru_service.SRUService",
        MockSRU
    )

    # Execute lookup
    service = ModernWebLookupService()
    results = await service.lookup(LookupRequest(
        term="onherroepelijk",
        sources=["wikipedia", "overheid"],
        max_results=5,
        context="Sv|strafrecht"  # Triggers juridical boost
    ))

    # CRITICAL ASSERTIONS
    assert len(results) >= 1, "Should have at least one result"

    # Wikipedia should win (high-quality relevant > low-quality juridical)
    # Expected scores:
    # - Wikipedia: 0.8 × 0.85 (weight) = 0.68
    # - Overheid:  0.6 × 1.1 (boost, quality-gated) × 1.0 (weight) = 0.66
    assert "Wikipedia" in results[0].source.name, \
        f"Expected Wikipedia to win, got {results[0].source.name}"

    # Verify confidence is in expected range (allow ±5% tolerance)
    # This catches if double-weighting returns (would be 0.578)
    expected_confidence = 0.68
    tolerance = 0.05
    actual_confidence = results[0].source.confidence

    assert expected_confidence - tolerance < actual_confidence < expected_confidence + tolerance, \
        f"Expected confidence ~{expected_confidence}, got {actual_confidence:.3f}. " \
        f"If {actual_confidence:.3f} < 0.6, check for DOUBLE-WEIGHTING bug!"


@pytest.mark.asyncio()
async def test_quality_gate_interaction_with_weighting():
    """
    Verify quality gate uses RAW confidence, not weighted.

    Quality gate should evaluate base score (0.6) BEFORE provider weight,
    not after (which would be 0.51 for Wikipedia with 0.85 weight).
    """
    # Similar test, but focus on quality gate trigger threshold
    # ... (implementation similar to above)
    pass
```

**Checklist**:
- [ ] Create test file
- [ ] Copy code above
- [ ] Run test: `pytest tests/services/test_modern_web_lookup_integration.py -v`
- [ ] Verify it passes
- [ ] Add to CI pipeline (if not already running all tests)

**Success Criteria**: Test passes, catches regression if weights re-added to lookup.

---

### Day 2 Morning: Pre-commit Lint Rule (0.5 hours)

**File**: `scripts/check_provider_weighting.sh` (new)

**Goal**: Passive protection against copy-paste errors.

**Code**:
```bash
#!/bin/bash
# scripts/check_provider_weighting.sh
# Prevents provider weight multiplication in lookup methods

echo "🔍 Checking for provider weight multiplication in lookup methods..."

# Search for .confidence *= pattern in web lookup files
# Exclude ranking.py (where weights SHOULD be applied)
# Exclude fallback penalty (0.95 is intrinsic, not provider weight)

VIOLATIONS=$(grep -rn "\.confidence\s*\*=" src/services/web_lookup/*.py \
    | grep -v "ranking.py" \
    | grep -v "0.95" \
    | grep -v "# OK: intrinsic penalty")

if [ -n "$VIOLATIONS" ]; then
    echo "❌ ERROR: Provider weight multiplication found in lookup method!"
    echo ""
    echo "Provider weights should ONLY be applied in ranking layer (ranking.py)."
    echo "Lookup methods must return RAW confidence scores."
    echo ""
    echo "Violations found:"
    echo "$VIOLATIONS"
    echo ""
    echo "Reference: docs/analyses/double-weighting-bug-analysis.md"
    exit 1
fi

echo "✅ No provider weight violations found"
exit 0
```

**Make executable**:
```bash
chmod +x scripts/check_provider_weighting.sh
```

**Add to pre-commit** (`.pre-commit-config.yaml`):
```yaml
# Add to existing hooks:
- repo: local
  hooks:
    - id: check-provider-weighting
      name: Check provider weighting (no double-weighting)
      entry: scripts/check_provider_weighting.sh
      language: system
      pass_filenames: false
      always_run: true
```

**Test it**:
```bash
# Should pass
./scripts/check_provider_weighting.sh

# Test false positive detection (add temporary violation)
echo "result.confidence *= 0.85  # Test violation" >> src/services/web_lookup/test_file.py
./scripts/check_provider_weighting.sh  # Should FAIL
rm src/services/web_lookup/test_file.py
```

**Checklist**:
- [ ] Create script file
- [ ] Make executable (`chmod +x`)
- [ ] Add to `.pre-commit-config.yaml`
- [ ] Test manually (should pass)
- [ ] Test false positive (should catch violation)
- [ ] Commit

**Success Criteria**: Pre-commit hook catches if developer accidentally adds weight multiplication.

---

### Day 2 Afternoon: Architecture Documentation (0.75 hours)

**File**: `docs/architectuur/TECHNICAL_ARCHITECTURE.md`

**Goal**: Document confidence flow for future-you.

**Add this section**:

````markdown
## Confidence Score Transformations

### ⚠️ CRITICAL: NO DOUBLE-WEIGHTING

Provider weights are applied **EXACTLY ONCE**, in the **ranking layer only**.

**Why this matters**: We previously had a bug where weights were applied both in lookup AND ranking, causing Wikipedia to be penalized 72% (0.85²) instead of 15% (0.85). This made low-quality juridical sources incorrectly outrank high-quality relevant sources.

**Reference**: `docs/analyses/double-weighting-bug-analysis.md`

---

### The Three-Layer Pipeline

```
┌─────────────────────────────────────────────────────────┐
│ LAYER 1: LOOKUP (Data Fetching)                        │
├─────────────────────────────────────────────────────────┤
│ Returns: RAW confidence (0.0-1.0 from API)              │
│ Examples:                                               │
│   - Wikipedia: 0.8 (relevance score from API)           │
│   - Overheid.nl: 0.6 (SRU result quality)              │
│                                                         │
│ ✅ Intrinsic penalties allowed:                        │
│   - Fallback queries: 0.95× (less precise)             │
│   - Timeout penalties: 0.9× (incomplete data)          │
│                                                         │
│ ❌ NEVER apply provider weights here                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ LAYER 2: BOOST (Content Analysis)                      │
├─────────────────────────────────────────────────────────┤
│ Applies: Content-based boosts (NOT provider weights)   │
│ Examples:                                               │
│   - Juridische bron: 1.2× (if high quality)           │
│   - Keywords: 1.1× per keyword (max 1.3×)              │
│   - Artikel refs: 1.15×                                 │
│                                                         │
│ Quality Gate (FASE 3):                                 │
│   If base_score < 0.65: Reduced boost (50%)           │
│   If base_score >= 0.65: Full boost (100%)            │
│                                                         │
│ Input:  0.6 (raw)                                      │
│ Output: 0.66 (0.6 × 1.1 quality-gated boost)          │
│                                                         │
│ ❌ NEVER apply provider weights here                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ LAYER 3: RANKING (Cross-Provider Comparison)           │
├─────────────────────────────────────────────────────────┤
│ Applies: Provider weights (authority/trust)            │
│ Examples:                                               │
│   - Wikipedia: 0.85 (good, but not authoritative)      │
│   - Overheid.nl: 1.0 (official source)                │
│   - Rechtspraak: 0.95 (primary jurisprudence)         │
│                                                         │
│ Formula: final_score = boosted_confidence × weight     │
│                                                         │
│ Input:  Wikipedia 0.8 (boosted), Overheid 0.66        │
│ Output: Wikipedia 0.68, Overheid 0.66                  │
│ Winner: Wikipedia (0.68 > 0.66)                        │
│                                                         │
│ ✅ Provider weights applied HERE, ONCE                 │
└─────────────────────────────────────────────────────────┘
```

### Code Locations

| Layer | File | Function | Responsibility |
|-------|------|----------|----------------|
| **Lookup** | `modern_web_lookup_service.py` | `_lookup_mediawiki`, `_lookup_sru`, etc. | Return RAW confidence |
| **Boost** | `web_lookup/juridisch_ranker.py` | `boost_juridische_resultaten` | Apply content boosts |
| **Ranking** | `web_lookup/ranking.py` | `rank_and_dedup` → `_final_score` | Apply provider weights |

### Validation

**Pre-commit hook**: `scripts/check_provider_weighting.sh` catches weight multiplication in lookup methods.

**Integration test**: `tests/services/test_modern_web_lookup_integration.py::test_confidence_scoring_end_to_end` verifies end-to-end flow.

### Example Trace

```python
# Wikipedia lookup (LAYER 1)
result = await wikipedia_lookup("onherroepelijk")
# → confidence = 0.8 (RAW, no weight applied)

# Juridical boost (LAYER 2)
boosted_results = boost_juridische_resultaten([result], context=["Sv"])
# → confidence = 0.8 (no boost for non-juridical Wikipedia)

# Ranking (LAYER 3)
final_scores = rank_and_dedup(boosted_results, provider_weights)
# → Wikipedia: 0.8 × 0.85 (weight) = 0.68

# If weights were applied in lookup:
# → 0.8 × 0.85 (lookup) × 0.85 (ranking) = 0.578 ❌ DOUBLE-WEIGHTING BUG
```

### Common Pitfalls

**❌ WRONG**:
```python
# In lookup method
result.source.confidence *= source.confidence_weight  # NO!
return result
```

**✅ CORRECT**:
```python
# In lookup method
# NOTE: Provider weight applied in ranking, not here (Oct 2025)
return result  # Raw confidence, no weight
```

**❌ WRONG**:
```python
# In boost method
result.source.confidence *= provider_weight  # NO! This is ranking's job
```

**✅ CORRECT**:
```python
# In boost method
result.source.confidence *= juridical_boost_factor  # OK: Content boost
# (provider weight applied later in ranking)
```

---

### Decision Record

For full rationale and alternatives considered, see:
- **ADR-001**: Apply Provider Weights Only in Ranking Layer
- **Bug Analysis**: `docs/analyses/double-weighting-bug-analysis.md`
````

**Checklist**:
- [ ] Add section to `docs/architectuur/TECHNICAL_ARCHITECTURE.md`
- [ ] Verify formatting (diagrams, code blocks)
- [ ] Test links to other docs
- [ ] Commit

**Success Criteria**: Developer can read this in 5 minutes and understand the rule.

---

## Week 2: Documentation & Validation (2.75 hours)

### Day 3: Config Validation Test (0.5 hours)

**File**: `tests/services/test_web_lookup_config.py` (new)

**Goal**: Catch config drift (YAML vs code defaults).

**Code**:
```python
import pytest
from services.modern_web_lookup_service import ModernWebLookupService
from services.web_lookup.config_loader import load_web_lookup_config

def test_yaml_weights_match_code_defaults():
    """
    Prevent config drift: YAML weights should match code fallback.

    If YAML is updated but code defaults aren't, inconsistent behavior.
    This test catches that immediately.

    Reference: Multi-agent consensus - config refactoring alternative
    """
    # Load YAML config
    yaml_config = load_web_lookup_config()
    yaml_providers = yaml_config.get("web_lookup", {}).get("providers", {})

    # Extract weights from YAML
    yaml_weights = {
        "wikipedia": yaml_providers.get("wikipedia", {}).get("weight", 0.85),
        "wiktionary": yaml_providers.get("wiktionary", {}).get("weight", 0.9),
        "overheid": yaml_providers.get("sru_overheid", {}).get("weight", 1.0),
        "rechtspraak": yaml_providers.get("rechtspraak_ecli", {}).get("weight", 0.95),
        "wetgeving": yaml_providers.get("wetgeving_nl", {}).get("weight", 0.9),
        "brave_search": yaml_providers.get("brave_search", {}).get("weight", 0.85),
    }

    # Get code defaults (fallback when YAML fails to load)
    service = ModernWebLookupService()
    code_weights = service._provider_weights

    # Compare
    for provider, yaml_weight in yaml_weights.items():
        code_weight = code_weights.get(provider)
        assert code_weight == yaml_weight, \
            f"Config drift detected for {provider}: " \
            f"YAML={yaml_weight}, Code={code_weight}. " \
            f"Update ModernWebLookupService._setup_sources() fallback!"


def test_provider_weights_in_valid_range():
    """Sanity check: All weights should be between 0.0 and 1.0."""
    service = ModernWebLookupService()

    for provider, weight in service._provider_weights.items():
        assert 0.0 <= weight <= 1.0, \
            f"Invalid weight for {provider}: {weight} (must be 0-1)"
```

**Checklist**:
- [ ] Create test file
- [ ] Run test: `pytest tests/services/test_web_lookup_config.py -v`
- [ ] Verify it passes
- [ ] Commit

**Success Criteria**: Test catches if YAML and code weights diverge.

---

### Day 4: One Provider Contract Test (1 hour)

**File**: `tests/services/web_lookup/test_provider_contracts.py` (new)

**Goal**: Validate most complex provider (Wikipedia) returns raw confidence.

**Code**:
```python
import pytest
from services.modern_web_lookup_service import ModernWebLookupService
from services.interfaces import LookupRequest

@pytest.mark.asyncio()
async def test_wikipedia_returns_raw_confidence():
    """
    Contract test: Wikipedia lookup returns UN-weighted confidence.

    Wikipedia provider weight is 0.85 in config.
    If lookup applies weight: 0.8 × 0.85 = 0.68
    If lookup returns raw (correct): 0.8

    This test validates the lookup contract: return RAW confidence.

    Reference: Multi-agent consensus - provider contract validation
    """
    # Real Wikipedia lookup (not mocked)
    service = ModernWebLookupService()

    # Search for term likely to return high-confidence result
    result = await service._lookup_mediawiki(
        "rechtspraak",  # Common legal term
        service.sources["wikipedia"],
        LookupRequest(term="rechtspraak", timeout=10)
    )

    # Allow failure (Wikipedia API might be down)
    if not result or not result.success:
        pytest.skip("Wikipedia lookup failed (API down?)")

    confidence = result.source.confidence

    # Sanity checks
    assert 0.0 <= confidence <= 1.0, \
        f"Confidence out of range: {confidence}"

    # CRITICAL: Confidence should be RAW (not weighted)
    # If weighted by 0.85, typical score 0.8 becomes 0.68
    # We expect scores >= 0.75 for good matches (raw)
    # If we see consistent scores < 0.7, likely double-weighted

    # This is a heuristic check (can't know exact API score)
    # But if EVERY result is < 0.7, something is wrong
    if confidence < 0.7:
        import warnings
        warnings.warn(
            f"Wikipedia confidence suspiciously low ({confidence:.2f}). "
            f"If this persists across multiple runs, check for weight application in lookup."
        )

    # Stronger assertion: confidence should not be EXACTLY weight × round_number
    # e.g., 0.85 × 0.9 = 0.765 (suspiciously specific)
    weighted_85 = round(confidence / 0.85, 2)
    if weighted_85 in [0.8, 0.9, 1.0]:  # Common API scores
        pytest.fail(
            f"Confidence {confidence:.3f} suspiciously matches "
            f"0.85 × {weighted_85} = {confidence:.3f}. "
            f"Check if provider weight is being applied in lookup!"
        )


@pytest.mark.asyncio()
async def test_provider_weight_only_in_ranking():
    """
    Meta-test: Verify lookup methods don't multiply confidence by weight.

    This is a code inspection test (checks source code, not behavior).
    """
    import inspect
    from services.modern_web_lookup_service import ModernWebLookupService

    service = ModernWebLookupService()

    # Get source code of lookup methods
    lookup_methods = [
        service._lookup_mediawiki,
        service._lookup_sru,
        service._lookup_rest,
        service._lookup_brave,
    ]

    for method in lookup_methods:
        source = inspect.getsource(method)

        # Check for suspicious patterns
        if "confidence_weight" in source and "*=" in source:
            # Allow fallback penalty (0.95)
            if "0.95" not in source and "fallback" not in source.lower():
                pytest.fail(
                    f"Method {method.__name__} contains 'confidence_weight' and '*=' - "
                    f"possible weight multiplication! Check source."
                )
```

**Checklist**:
- [ ] Create test file
- [ ] Run test: `pytest tests/services/web_lookup/test_provider_contracts.py -v`
- [ ] Verify it passes (may skip if Wikipedia API down)
- [ ] Commit

**Success Criteria**: Test validates Wikipedia contract, catches violations.

---

### Day 5: ADR-001 Document (1 hour)

**File**: `docs/architectuur/adr/ADR-001-provider-weights-ranking-only.md` (new directory + file)

**Goal**: Document THIS critical architectural decision.

**Code**:
```markdown
# ADR-001: Apply Provider Weights Only in Ranking Layer

**Status**: ✅ Accepted (2025-10-09)
**Deciders**: Solo developer (multi-agent consensus analysis)
**Date**: 2025-10-09

---

## Context

The DefinitieAgent web lookup system fetches legal definitions from 6 providers:
- Wikipedia (encyclopedia, confidence weight 0.85)
- Wiktionary (dictionary, weight 0.9)
- Overheid.nl (official government, weight 1.0)
- Rechtspraak.nl (case law, weight 0.95)
- Wetgeving.nl (legislation, weight 0.9)
- Brave Search (general web, weight 0.85)

Each provider has different **authority/trustworthiness** (provider weight), and each result has **relevance** (confidence score from API).

**Problem**: Where should provider weights be applied?

**Bug History**: On Oct 9, 2025, we discovered weights were being applied in BOTH lookup methods AND ranking module, causing Wikipedia to be penalized 72% (0.85²) instead of 15% (0.85). This made low-quality juridical sources incorrectly outrank high-quality relevant sources.

---

## Decision

**Provider weights are applied ONLY in the ranking layer** (`web_lookup/ranking.py`).

Lookup methods (`modern_web_lookup_service.py`) return **RAW confidence scores** (0.0-1.0 from API), with NO provider weights applied.

---

## Rationale

### Single Responsibility Principle

- **Lookup layer**: Responsible for fetching data and assessing intrinsic quality
- **Ranking layer**: Responsible for cross-provider comparison using authority weights

Mixing these concerns (weighting in lookup) violates SRP and caused the double-weighting bug.

### Testability

- Lookup methods can be tested independently (mock API, verify raw score)
- Ranking logic can be tested independently (mock scores, verify weighted comparison)
- Integration tests verify end-to-end pipeline

### Debuggability

- Developers can inspect raw API scores before weighting
- Clear separation makes data flow explicit
- Easier to trace: "Is this score raw or weighted?"

### Composability

- Boost layer (juridical ranking) can analyze raw scores for quality gate
- Quality gate needs raw scores to determine if source deserves full boost
- If weights were already applied, quality gate couldn't assess true source quality

---

## Alternatives Considered

### Alternative 1: Apply Weights in Lookup Methods

**Rejected**: This is what caused the double-weighting bug.

**Pros**:
- Simpler: Each provider returns already-weighted score

**Cons**:
- ❌ Violates SRP (lookup mixes fetching + business logic)
- ❌ Makes testing harder (can't verify raw API score)
- ❌ Breaks boost layer (quality gate can't see raw scores)
- ❌ Caused actual production bug (double-weighting)

### Alternative 2: Apply Weights in Both Layers

**Rejected**: This was the bug we just fixed.

**Cons**:
- ❌ Double-weighting (weights applied twice)
- ❌ Wikipedia penalized 72% instead of 15%
- ❌ Low-quality juridical beats high-quality relevant

### Alternative 3: No Weights (Treat All Providers Equal)

**Rejected**: Ignores provider authority differences.

**Cons**:
- ❌ Wikipedia (encyclopedia) treated same as Overheid.nl (official source)
- ❌ Can't prioritize authoritative sources
- ❌ Users expect official sources to rank higher

---

## Consequences

### Positive

- ✅ **No double-weighting**: Weights applied exactly once
- ✅ **Clear separation**: Lookup fetches, ranking compares
- ✅ **Testable**: Each layer can be tested independently
- ✅ **Debuggable**: Raw scores visible before weighting
- ✅ **Quality gate works**: Can assess raw source quality

### Negative

- ⚠️ **Developer must remember**: New providers should NOT apply weights
- ⚠️ **Implicit contract**: Lookup methods must return raw scores (not enforced by type system)

### Mitigations

- ✅ **Pre-commit hook**: Catches weight multiplication in lookup files (`scripts/check_provider_weighting.sh`)
- ✅ **Integration test**: Verifies end-to-end flow (`test_confidence_scoring_end_to_end`)
- ✅ **Documentation**: Architecture doc explains three-layer pipeline
- ✅ **Inline comments**: 6 comments in lookup methods warn "NO WEIGHTS HERE"
- 🔄 **Future**: Consider type system (`RawConfidence` vs `WeightedScore`) if bugs recur

---

## Compliance

To comply with this ADR when adding new providers:

1. **Lookup method**: Return raw confidence (0-1) from API
2. **NO weight multiplication**: Don't multiply by `source.confidence_weight`
3. **Add comment**: `# NOTE: Provider weight applied in ranking, not here`
4. **Provider weights**: Add to `config/web_lookup_defaults.yaml` (ranking config)
5. **Mapping**: Add to `_infer_provider_key()` and `_provider_weights` dict
6. **Test**: Verify `test_confidence_scoring_end_to_end` still passes

---

## References

- **Bug Analysis**: `docs/analyses/double-weighting-bug-analysis.md`
- **Multi-Agent Consensus**: `docs/analyses/multi-agent-consensus-single-dev-context.md`
- **Architecture Docs**: `docs/architectuur/TECHNICAL_ARCHITECTURE.md`
- **Pre-commit Hook**: `scripts/check_provider_weighting.sh`
- **Integration Test**: `tests/services/test_modern_web_lookup_integration.py`

---

## Change Log

- **2025-10-09**: Initial decision (fixed double-weighting bug)
```

**Checklist**:
- [ ] Create `docs/architectuur/adr/` directory
- [ ] Create ADR-001 file
- [ ] Link from architecture docs
- [ ] Commit

**Success Criteria**: ADR documents decision for future reference.

---

## Post-Implementation Checklist

After completing all tasks:

### Verification

- [ ] All tests pass: `pytest tests/services/ -v`
- [ ] Pre-commit hook works: `pre-commit run --all-files`
- [ ] Documentation renders correctly
- [ ] No regressions in existing functionality

### Git Commit

```bash
# Stage all changes
git add tests/services/test_modern_web_lookup_integration.py
git add tests/services/test_web_lookup_config.py
git add tests/services/web_lookup/test_provider_contracts.py
git add scripts/check_provider_weighting.sh
git add .pre-commit-config.yaml
git add docs/architectuur/TECHNICAL_ARCHITECTURE.md
git add docs/architectuur/adr/ADR-001-provider-weights-ranking-only.md

# Commit with reference to analysis
git commit -m "feat(web-lookup): add strategic protections against double-weighting

Add 5.75h of strategic improvements based on multi-agent consensus analysis:

1. E2E integration test (1.5h) - permanent regression safety net
2. Pre-commit lint rule (0.5h) - catches weight multiplication
3. Architecture docs (0.75h) - documents three-layer pipeline
4. Config validation (0.5h) - prevents YAML-code drift
5. Provider contract test (1h) - validates Wikipedia contract
6. ADR-001 (1h) - documents critical architectural decision

References:
- Multi-agent consensus: docs/analyses/multi-agent-consensus-single-dev-context.md
- Bug analysis: docs/analyses/double-weighting-bug-analysis.md
- Action plan: docs/analyses/ACTION_PLAN_double_weighting_followup.md

ROI: 143% (8.25h net value over 2 years)
Deferred: 24h of over-engineering (type safety, comprehensive ADRs)
Next: Build synonym management features (24h saved)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Post-Commit Validation

```bash
# Run full test suite
make test

# Verify pre-commit hook
pre-commit run --all-files

# Check documentation links
# (manually verify links in architecture docs work)
```

---

## Re-evaluation Triggers (Year 2)

**Revisit deferred improvements IF**:

### Type Safety (12h deferred)
- [ ] 2+ weight-related bugs occur in next 12 months
- [ ] New developer joins team
- [ ] Codebase grows to 150K+ LOC

### Comprehensive ADRs (6h deferred)
- [ ] Developer works sporadically (3+ month gaps between sessions)
- [ ] Onboarding new developer
- [ ] Frequent "why did we decide this?" moments

### Config Refactoring (6h skipped)
- [ ] Config drift causes production bug
- [ ] 3+ providers added (complexity justifies cleanup)

---

## Success Metrics (6-Month Check-in)

**Measure these after 6 months**:

| Metric | Target | Measurement |
|--------|--------|-------------|
| **New provider added without bugs** | ✅ YES | Did tests catch contract violation? |
| **Returned after break, oriented in < 2h** | ✅ YES | Did arch docs help? |
| **No weight-related bugs** | ✅ YES | Did protections work? |

**If 2/3 above are "yes"**: Investment paying off.
**If 0/3**: Re-evaluate (but evidence suggests 3/3 likely).

---

## Summary

**Total Time**: 5.75 hours
**Total Value**: +8.25 hours (2-year ROI)
**Time Saved**: 24+ hours (vs comprehensive plan)

**Next Step**: Build synonym management features with saved time!

---

**Generated**: 2025-10-09
**Author**: Multi-agent consensus (PM, Debug Specialist, Pragmatic Dev)
**Status**: ✅ Ready to execute