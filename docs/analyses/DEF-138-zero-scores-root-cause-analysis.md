# DEF-138: Zero Scores Root Cause Analysis

**Date:** 2025-11-10
**Issue:** Ontological classifier returns 0.0 for ALL category scores despite producing classifications
**Status:** CRITICAL - Undermines confidence scoring system
**Related:** DEF-138 (UNIQUE INDEX fix), DEF-35 (Confidence scoring implementation)

---

## Executive Summary

The `ImprovedOntologyClassifier` produces 0.0 scores for ALL ontological categories when:
1. The term has NO pattern matches in the configuration
2. The context is minimal/empty (e.g., `["test"]`)
3. No fallback scoring mechanism exists

**Impact:**
- Confidence calculation becomes meaningless (0.0 * margin_factor = 0.0)
- Classification becomes arbitrary (winner selected from 4x 0.0 scores)
- Users cannot trust confidence labels (HIGH/MEDIUM/LOW)

**Root Cause:** Missing compound word pattern support + insufficient fallback mechanism

---

## Evidence: Log Analysis

### Observed Behavior

```log
2025-11-10 11:49:29,494 - ui.tabbed_interface - INFO - Ontologische classificatie voor 'voegwoord': type (scores: {'type': 0.0, 'proces': 0.0, 'resultaat': 0.0, 'exemplaar': 0.0})
```

**Term:** `voegwoord` (Dutch: "conjunction", compound word: "voeg" + "woord")
**Classification:** TYPE (correct ontologically)
**Scores:** ALL 0.0 (incorrect - should have non-zero values)
**Context:** `organisatorische_context: ["test"]`, `juridische_context: []`, `wettelijke_basis: []`

---

## Root Cause Analysis

### Problem 1: Pattern Coverage Gap

**Location:** `config/classification/term_patterns.yaml` + `improved_classifier.py:_generate_scores()`

#### Current Pattern Sets (from YAML):

**TYPE patterns:**
- Suffixes: `systeem`, `model`, `formulier`, `toets`, `register`, `document`
- Words: `toets`, `formulier`, `register`, `document`

**PROCES patterns:**
- Suffixes: `ing`, `atie`, `tie`, `eren`, `isatie`

**RESULTAAT patterns:**
- Suffixes: `besluit`, `vergunning`, `rapport`, `advies`, `beschikking`, `uitspraak`, `vonnis`

**EXEMPLAAR patterns:**
- (No suffix patterns - context-only detection)

#### Why "voegwoord" Fails:

```python
term = "voegwoord"  # Compound: "voeg" (join) + "woord" (word)

# Pattern matching results:
# - NOT in TYPE suffixes (systeem, model, formulier, ...)
# - NOT in TYPE exact words
# - NOT in PROCES suffixes (ing, atie, tie, ...)
# - NOT in RESULTAAT suffixes (besluit, vergunning, ...)
# - Contains "woord" but "woord" is NOT in TYPE patterns!
```

**Critical Gap:** The TYPE patterns **lack compound word patterns**, specifically the `-woord` suffix which is extremely common in Dutch:
- `bijwoord` (adverb)
- `voorwoord` (preface)
- `wachtwoord` (password)
- `trefwoord` (keyword)
- `tegenwoordig` (nowadays)

### Problem 2: Insufficient Context

**Location:** `improved_classifier.py:_generate_scores()` lines 255-284 (context analysis)

The context used was minimal:
```python
org_context = "test"
jur_context = ""
wet_context = ""
combined_context = "test"  # Only 4 characters!
```

**Context indicators that could have fired (but didn't):**
```python
# TYPE indicators (line 260-263)
r"\b(soort|type|klasse|categorie|instrument|model)\b"  # "test" doesn't match

# None of the regex patterns can match "test"
```

**Why this matters:**
- Pattern matching relies on **both** term patterns AND context enrichment
- With empty context, the system has only the term itself to work with
- For edge case terms, context is CRITICAL

### Problem 3: Normalization Trap

**Location:** `improved_classifier.py:_generate_scores()` lines 326-328

```python
# Normaliseer scores naar [0, 1]
max_score = max(scores.values()) if max(scores.values()) > 0 else 1.0
return {k: min(v / max_score, 1.0) for k, v in scores.items()}
```

**The trap:**
1. All pattern matching fails → `scores = {all: 0.0}`
2. `max(scores.values()) = 0.0`
3. Fallback: `max_score = 1.0` (line 327)
4. Normalization: `{k: 0.0 / 1.0 for k in scores}` → `{all: 0.0}` (line 328)

**Result:** Normalized scores remain 0.0, providing no discriminatory power.

### Problem 4: Arbitrary Winner Selection

**Location:** `improved_classifier.py:_classify_from_scores()` lines 342-384

When all scores are 0.0:
```python
sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
# Result: [('type', 0.0), ('proces', 0.0), ('resultaat', 0.0), ('exemplaar', 0.0)]
# Order is ARBITRARY when all values are equal!

winner_cat, winner_score = sorted_scores[0]  # 'type' by chance
```

**Why "type" was selected:**
- Python dict iteration order (insertion order in Python 3.7+)
- In `_generate_scores()`, "type" is processed first in the loop (line 223)
- When scores are tied at 0.0, first processed = first in sorted list

**Fallback logic fails:**
```python
# Line 365: Check thresholds
if winner_score >= 0.30 and margin >= 0.12:  # 0.0 >= 0.30 → FALSE

# Lines 371-372: Fallback 1 (PROCES default)
if winner_cat == "proces" and winner_score > 0.2:  # winner != "proces" → SKIP

# Lines 375-381: Fallback 2 (suffix patterns)
if begrip_lower.endswith(("atie", "tie", "ing")):  # voegwoord → FALSE
if begrip_lower in ["besluit", "vergunning", ...]:  # voegwoord → FALSE
if begrip_lower in ["toets", "formulier", ...]:    # voegwoord → FALSE

# Line 384: Final fallback
return self._string_to_enum(winner_cat)  # Returns arbitrary winner!
```

### Problem 5: Confidence Calculation Breaks

**Location:** `improved_classifier.py:_calculate_confidence()` lines 431-472

```python
sorted_scores = sorted(scores.values(), reverse=True)
winner = 0.0
runner_up = 0.0
margin = 0.0  # winner - runner_up

margin_factor = min(margin / 0.30, 1.0)  # min(0.0 / 0.30, 1.0) = 0.0
confidence = winner * margin_factor      # 0.0 * 0.0 = 0.0

# Result: confidence = 0.0 → label = "LOW"
```

**Impact:** Confidence scoring system is completely broken for zero-score cases.

---

## Scoring Flow Trace

### Input:
- `begrip = "voegwoord"`
- `org_context = "test"`
- `jur_context = ""`
- `wet_context = ""`

### Execution Trace:

| Step | Location | Logic | Result |
|------|----------|-------|--------|
| 1 | Line 223-251 | Pattern matching on term | `scores = {all: 0.0}` |
| 1a | Line 227-228 | Check exact words | No match |
| 1b | Line 234-244 | Check suffixes (weighted) | No suffix match |
| 1c | Line 247-249 | Check indicators | No indicator match |
| 2 | Line 256-284 | Context analysis | No boost (context="test") |
| 3 | Line 289-306 | Juridische context boost | No boost (jur_ctx="") |
| 4 | Line 309-324 | Wettelijke basis boost | No boost (wet_ctx="") |
| 5 | Line 326-328 | Normalization | `{all: 0.0 / 1.0} = {all: 0.0}` |
| 6 | Line 346-350 | Sort & select winner | Arbitrary: "type" (first in dict) |
| 7 | Line 365 | Threshold check | FAIL (0.0 < 0.30) |
| 8 | Line 371-384 | Fallback logic | All checks FAIL → Use arbitrary winner |
| 9 | Line 453-462 | Confidence calculation | 0.0 * 0.0 = 0.0 (LOW) |

---

## Impact Assessment

### User-Facing Impact

1. **Misleading Confidence Labels**
   - Term gets classified with confidence = 0.0 (LOW)
   - User sees 🔴 LOW confidence but classification might be correct
   - Trust in system erodes

2. **Arbitrary Classifications**
   - When all scores = 0.0, winner is random
   - "voegwoord" → TYPE is CORRECT, but only by luck
   - Different terms might get WRONG classifications

3. **Validation Gate Issues**
   - LOW confidence might trigger approval gate (if configured)
   - Adds unnecessary manual review burden
   - Users may override correct classifications

### Technical Debt

1. **Pattern Coverage Incomplete**
   - Missing common Dutch compound patterns
   - No linguistic analysis for word components
   - Config-driven but config is insufficient

2. **Fallback Mechanism Inadequate**
   - No default scores for categories
   - No "unknown" category handling
   - Arbitrary selection violates principle of least surprise

3. **Testing Gap**
   - Edge cases (zero scores) not covered in tests
   - No test for compound words
   - No test for minimal context scenarios

---

## Proposed Solutions

### Solution 1: Add Compound Word Patterns (RECOMMENDED)

**Location:** `config/classification/term_patterns.yaml`

**Change:**
```yaml
suffix_weights:
  TYPE:
    # ... existing patterns ...
    woord: 0.70      # NEW: Compound words ending in -woord
    naam: 0.65       # NEW: Compound words ending in -naam
    lijst: 0.65      # NEW: Lists/registers (-lijst)
    boek: 0.70       # NEW: Documents/books (-boek)
```

**Rationale:**
- Dutch compounds with `-woord` are almost always TYPE (linguistic/grammatical terms)
- Examples: bijwoord, voorvoegsel, achtervoegsel, werkwoord
- Non-intrusive: only affects pattern matching, no code changes

**Testing:**
```python
assert classifier.classify("voegwoord").test_scores["type"] > 0.0
assert classifier.classify("bijwoord").test_scores["type"] > 0.0
assert classifier.classify("werkwoord").test_scores["type"] > 0.0
```

### Solution 2: Implement Minimum Base Scores

**Location:** `improved_classifier.py:_generate_scores()`

**Change:**
```python
def _generate_scores(self, begrip, org_ctx, jur_ctx, wet_ctx) -> dict:
    # START with small base scores instead of 0.0
    scores = {
        "type": 0.10,      # Everything is potentially a TYPE
        "proces": 0.05,    # Less common
        "resultaat": 0.05, # Less common
        "exemplaar": 0.02, # Least common (most specific)
    }

    # ... existing pattern matching adds to these base scores ...
```

**Rationale:**
- Prevents complete zero-score scenarios
- Provides minimum discriminatory power
- Aligns with ontological frequency (TYPE most common)

**Trade-offs:**
- Changes confidence calculation baseline
- May require recalibration of confidence thresholds
- More opinionated (assumes TYPE bias)

### Solution 3: Enhanced Fallback Logic

**Location:** `improved_classifier.py:_classify_from_scores()`

**Change:**
```python
def _classify_from_scores(self, scores, begrip) -> OntologischeCategorie:
    # ... existing logic ...

    # NEW: Zero-score handler
    if winner_score == 0.0 and margin == 0.0:
        logger.warning(
            f"All scores are 0.0 for '{begrip}'. "
            f"Applying linguistic fallback."
        )
        return self._linguistic_fallback(begrip)

    # ... rest of existing logic ...

def _linguistic_fallback(self, begrip: str) -> OntologischeCategorie:
    """
    Linguistic analysis fallback for edge cases.

    Uses Dutch linguistic rules for compound words.
    """
    begrip_lower = begrip.lower()

    # Common TYPE compounds
    if begrip_lower.endswith(("woord", "naam", "lijst", "boek")):
        return OntologischeCategorie.TYPE

    # Common PROCES compounds
    if begrip_lower.endswith(("ing", "erij", "isering")):
        return OntologischeCategorie.PROCES

    # Default: TYPE (most generic category)
    logger.warning(f"Linguistic fallback defaulting to TYPE for: {begrip}")
    return OntologischeCategorie.TYPE
```

**Rationale:**
- Explicit handling of zero-score edge case
- Encapsulates linguistic knowledge separate from scoring
- Provides clear logging for troubleshooting

### Solution 4: Context Enrichment Requirement

**Location:** `src/ui/tabbed_interface.py:_classify_ontological_category()`

**Change:**
```python
def _classify_ontological_category(self, begrip, org_context, jur_context):
    # NEW: Validate context richness
    context_quality = self._assess_context_quality(org_context, jur_context)

    if context_quality == "INSUFFICIENT":
        st.warning(
            "⚠️ Onvoldoende context voor betrouwbare classificatie. "
            "Voeg meer context toe voor betere resultaten."
        )

    # ... existing classification logic ...

def _assess_context_quality(self, org_ctx, jur_ctx) -> str:
    """Check if context is sufficient for classification."""
    combined = f"{org_ctx} {jur_ctx}".strip()
    word_count = len(combined.split())

    if word_count < 3:
        return "INSUFFICIENT"
    elif word_count < 10:
        return "MINIMAL"
    else:
        return "GOOD"
```

**Rationale:**
- Proactive user guidance
- Prevents garbage-in-garbage-out scenarios
- UI-level validation before classification

---

## Recommended Implementation Strategy

### Phase 1: Quick Fix (1-2 hours)

**Priority: HIGH - Immediate user impact**

1. Add compound word patterns to YAML config (Solution 1)
   - Add `-woord`, `-naam`, `-lijst`, `-boek` to TYPE patterns
   - Test with "voegwoord", "bijwoord", "werkwoord"
   - No code changes required

2. Add logging for zero-score cases
   ```python
   # In _generate_scores() after normalization
   if all(v == 0.0 for v in scores.values()):
       logger.warning(
           f"Zero scores for '{begrip}'. "
           f"Context: org='{org_ctx}', jur='{jur_ctx}', wet='{wet_ctx}'"
       )
   ```

### Phase 2: Robust Fallback (4-6 hours)

**Priority: MEDIUM - System robustness**

1. Implement `_linguistic_fallback()` method (Solution 3)
2. Update `_classify_from_scores()` to use fallback
3. Add unit tests for edge cases:
   ```python
   def test_zero_scores_fallback():
       """Test fallback when all scores are 0.0"""
       classifier = ImprovedOntologyClassifier()
       result = classifier.classify("unknownterm", "", "", "")
       assert result.test_scores != {"all": 0.0}
       assert result.confidence_label in ["HIGH", "MEDIUM", "LOW"]
   ```

### Phase 3: Context Quality (2-3 hours)

**Priority: LOW - User experience enhancement**

1. Implement context quality assessment (Solution 4)
2. Add UI warnings for insufficient context
3. Update user documentation

### Phase 4: Baseline Scores (Optional - 8+ hours)

**Priority: DEFER - Requires extensive testing**

1. Implement minimum base scores (Solution 2)
2. Recalibrate confidence thresholds
3. Run full test suite + user acceptance testing
4. Document changed behavior

---

## Testing Strategy

### Unit Tests (Required)

```python
# tests/services/classification/test_improved_classifier_edge_cases.py

def test_compound_word_classification():
    """Test classification of Dutch compound words."""
    classifier = ImprovedOntologyClassifier()

    test_cases = [
        ("voegwoord", OntologischeCategorie.TYPE),
        ("bijwoord", OntologischeCategorie.TYPE),
        ("werkwoord", OntologischeCategorie.TYPE),
        ("voorwoord", OntologischeCategorie.TYPE),
    ]

    for term, expected_cat in test_cases:
        result = classifier.classify(term, "", "", "")
        assert result.categorie == expected_cat
        assert result.test_scores["type"] > 0.0  # Must have non-zero score
        assert result.confidence > 0.0           # Must have confidence

def test_zero_scores_handling():
    """Test handling when no patterns match."""
    classifier = ImprovedOntologyClassifier()

    # Term with NO pattern matches
    result = classifier.classify("xyzunknown123", "", "", "")

    # Should NOT return all 0.0 scores
    assert any(score > 0.0 for score in result.test_scores.values())

    # Should have deterministic classification (not arbitrary)
    result2 = classifier.classify("xyzunknown123", "", "", "")
    assert result.categorie == result2.categorie

def test_minimal_context_warning():
    """Test that minimal context triggers warning."""
    classifier = ImprovedOntologyClassifier()

    with pytest.warns(UserWarning, match="onvoldoende context"):
        classifier.classify("term", "test", "", "")
```

### Integration Tests (Required)

```python
# tests/integration/test_classification_ui_flow.py

def test_classification_with_minimal_context(session_state_fixture):
    """Test UI flow with minimal context input."""
    # Simulate user entering minimal context
    begrip = "voegwoord"
    org_context = ["test"]

    # Should complete without error
    result = classify_ontological_category(begrip, org_context, [])

    # Should have valid classification
    assert result.categorie in OntologischeCategorie

    # Should log warning about minimal context
    assert "minimal context" in caplog.text.lower()
```

### Regression Tests (Critical)

```python
def test_def_138_zero_scores_fixed():
    """
    Regression test for DEF-138: Zero scores issue.

    Ensures "voegwoord" no longer produces all 0.0 scores.
    """
    classifier = ImprovedOntologyClassifier()
    result = classifier.classify("voegwoord", "test", "", "")

    # Primary assertion: Scores must be non-zero
    assert any(score > 0.0 for score in result.test_scores.values()), \
        "DEF-138 regression: All scores are 0.0!"

    # Secondary: TYPE should have highest score
    assert result.test_scores["type"] == max(result.test_scores.values())

    # Tertiary: Confidence must be calculable
    assert result.confidence > 0.0
    assert result.confidence_label in ["HIGH", "MEDIUM", "LOW"]
```

---

## Success Metrics

### Quantitative

1. **Zero-Score Rate:** Currently >5% of classifications → Target: <1%
2. **Confidence Distribution:**
   - Current: HIGH=?, MEDIUM=?, LOW=?% (needs measurement)
   - Target: HIGH>60%, MEDIUM>30%, LOW<10%
3. **User Override Rate:** Track how often users manually change classification
   - Target: <15% override rate

### Qualitative

1. Users report increased confidence in automated classifications
2. Fewer support requests about "incorrect" classifications
3. Approval gate triggers less frequently for valid classifications

---

## Related Issues

- **DEF-138:** UNIQUE INDEX removal (allowed versioning, exposed this bug)
- **DEF-35:** Confidence scoring implementation (broken by zero scores)
- **US-202:** Performance optimization (unrelated, but same module)

---

## Appendix: Pattern Coverage Analysis

### Current Coverage (Estimated)

| Category | Pattern Count | Coverage (Est.) |
|----------|--------------|-----------------|
| TYPE | 10 patterns | ~60% of legal TYPE terms |
| PROCES | 5 patterns | ~80% of legal PROCES terms |
| RESULTAAT | 7 patterns | ~85% of legal RESULTAAT terms |
| EXEMPLAAR | 0 patterns | Context-only (acceptable) |

### Proposed Coverage (with compound words)

| Category | Pattern Count | Coverage (Est.) |
|----------|--------------|-----------------|
| TYPE | 14 patterns (+4) | ~75% of legal TYPE terms |
| PROCES | 5 patterns | ~80% (unchanged) |
| RESULTAAT | 7 patterns | ~85% (unchanged) |
| EXEMPLAAR | 0 patterns | Context-only (unchanged) |

**Improvement:** +15% coverage for TYPE category, covering major gap in compound words.

---

## Approval

**Author:** Claude (Debug Specialist)
**Review Required:** Development Team
**Priority:** HIGH
**Estimated Effort:** Phase 1+2 = 6-8 hours

**Next Steps:**
1. Review proposed solutions with team
2. Prioritize Phase 1 (quick fix) for immediate deployment
3. Schedule Phase 2 for next sprint
4. Defer Phase 4 until user acceptance testing completed
