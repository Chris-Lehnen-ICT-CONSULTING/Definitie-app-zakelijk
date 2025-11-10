# BUG-138-001: False Positive Classifier Bug - Action Plan

**Priority:** CRITICAL
**Impact:** USER-FACING - Incorrect classifications for compound words
**Estimated Fix Time:** 2-3 hours
**Status:** READY FOR IMPLEMENTATION

---

## Problem Summary

The new compound word patterns added in DEF-138 cause false positives:

```yaml
# config/classification/term_patterns.yaml
TYPE:
  woord: 0.70  # Matches "woordvoerder" (wrong!)
  naam: 0.65   # Matches "naamsverminking" (wrong!)
  boek: 0.70   # Matches "boekhouding" (wrong!)
```

**Examples of False Positives:**
- `woordvoerder` (spokesperson) → TYPE (should be PROCES)
- `naamsverminking` (slander) → TYPE (should be PROCES)
- `woordbreuk` (breaking word) → TYPE (should be PROCES/RESULTAAT)

**Root Cause:**
Pattern matching in `improved_classifier.py:239` applies full weight to ANY word ending in suffix, without semantic validation.

---

## Solution Options

### Option A: Add Exclusion Patterns (RECOMMENDED)

**Pros:**
- Explicit control over edge cases
- Easy to maintain and understand
- No performance impact

**Cons:**
- Requires maintaining exclusion list
- Reactive (add exclusions as we find them)

**Implementation:**
1. Extend YAML schema to support exclusions:
   ```yaml
   TYPE:
     woord:
       weight: 0.70
       exclusions:
         - "woordvoerder"   # spokesperson = PROCES
         - "woordbreuk"     # breaking word = PROCES
         - "voorwoord"      # preface = TYPE (but contextual)
   ```

2. Update `TermPatternConfig` dataclass:
   ```python
   @dataclass
   class SuffixPattern:
       weight: float
       exclusions: list[str] = field(default_factory=list)

   @dataclass
   class TermPatternConfig:
       suffix_weights: dict[str, dict[str, SuffixPattern | float]]  # Support both formats
   ```

3. Update pattern matching in `improved_classifier.py`:
   ```python
   for suffix, pattern_data in suffix_weights.items():
       # Handle both old format (float) and new format (SuffixPattern)
       if isinstance(pattern_data, dict):
           weight = pattern_data.get("weight", 0.4)
           exclusions = pattern_data.get("exclusions", [])
       else:
           weight = pattern_data
           exclusions = []

       if begrip_lower in exclusions:
           continue  # Skip this pattern

       if begrip_lower.endswith(suffix):
           pattern_score += weight
   ```

**Estimated Time:** 2 hours

---

### Option B: Lower Weights

**Pros:**
- Quick fix (5 minutes)
- No schema changes

**Cons:**
- Might break correct classifications
- Doesn't address root cause
- Requires empirical tuning

**Implementation:**
```yaml
TYPE:
  woord: 0.40  # Lowered from 0.70
  naam: 0.35   # Lowered from 0.65
  boek: 0.40   # Lowered from 0.70
```

**Risk:** Could cause TRUE positives (werkwoord, bijwoord) to lose to PROCES patterns.

**Estimated Time:** 30 minutes + extensive testing

---

### Option C: Semantic Validation Layer

**Pros:**
- Most robust solution
- Handles future edge cases automatically
- No manual exclusion list

**Cons:**
- Complex implementation
- Requires NLP/semantic analysis
- Higher computational cost
- Longer development time

**Implementation:**
```python
def _is_linguistic_term(self, begrip: str) -> bool:
    """Check if compound word is actual linguistic term (werkwoord, bijwoord) vs semantic compound."""
    # Use external dictionary or rule-based system
    linguistic_terms = {"werkwoord", "bijwoord", "voornaamwoord", "lidwoord", "handboek", "wetboek"}
    return begrip.lower() in linguistic_terms

def _check_suffix_with_semantics(self, begrip_lower: str, suffix: str, weight: float) -> float:
    """Apply suffix match with semantic validation."""
    if begrip_lower.endswith(suffix):
        # Check if this is a linguistic term vs semantic compound
        if suffix in ["woord", "naam", "boek"]:
            if not self._is_linguistic_term(begrip_lower):
                # Semantic compound → reduce weight
                return weight * 0.3
        return weight  # Full weight for linguistic terms
    return 0.0
```

**Estimated Time:** 4-6 hours (research + implement + test)

---

## Recommended Implementation: OPTION A (Exclusion Patterns)

### Step 1: Extend YAML Schema (30 min)

**Before:**
```yaml
TYPE:
  woord: 0.70
  naam: 0.65
```

**After:**
```yaml
TYPE:
  woord:
    weight: 0.70
    exclusions:
      - "woordvoerder"   # spokesperson = PROCES
      - "woordbreuk"     # breaking word = PROCES
  naam:
    weight: 0.65
    exclusions:
      - "naamsverminking"  # slander = PROCES
      - "naamgeving"       # naming = PROCES
  lijst: 0.65  # Keep simple format for patterns without exclusions
  boek:
    weight: 0.70
    exclusions:
      - "boekhouding"      # accounting = PROCES (context override wins anyway)
```

**Migration:** Support both formats (backward compatible).

---

### Step 2: Update TermPatternConfig (30 min)

```python
# src/services/classification/term_config.py

from typing import Union

@dataclass
class SuffixPattern:
    """Pattern with weight and optional exclusions."""
    weight: float
    exclusions: list[str] = field(default_factory=list)

@dataclass
class TermPatternConfig:
    """Config with support for complex suffix patterns."""
    domain_overrides: dict[str, str]
    suffix_weights: dict[str, dict[str, Union[float, dict]]]  # float or {weight, exclusions}
    category_priority: list[str]
    confidence_thresholds: dict[str, float]

    def get_suffix_data(self, category: str, suffix: str) -> tuple[float, list[str]]:
        """Extract weight and exclusions from config.

        Returns:
            Tuple of (weight, exclusions_list)
        """
        pattern_data = self.suffix_weights.get(category, {}).get(suffix)

        if pattern_data is None:
            return 0.0, []

        if isinstance(pattern_data, (int, float)):
            # Simple format: just a weight
            return float(pattern_data), []

        if isinstance(pattern_data, dict):
            # Complex format: {weight, exclusions}
            weight = pattern_data.get("weight", 0.0)
            exclusions = pattern_data.get("exclusions", [])
            return weight, exclusions

        raise ValueError(f"Invalid suffix pattern format for {category}/{suffix}: {pattern_data}")
```

---

### Step 3: Update Pattern Matching Logic (30 min)

```python
# src/ontologie/improved_classifier.py:230-245

# BEFORE
for suffix in patterns["suffixes"]:
    weight = suffix_weights.get(suffix, 0.4)

    if begrip_lower.endswith(suffix):
        pattern_score += weight
    elif suffix in begrip_lower:
        pattern_score += weight * 0.5

# AFTER
for suffix in patterns["suffixes"]:
    # Get weight and exclusions from config
    weight, exclusions = self.config.get_suffix_data(category_upper, suffix)

    # Check exclusions FIRST
    if begrip_lower in exclusions:
        logger.debug(f"Skipping pattern '{suffix}' for '{begrip_lower}' (excluded)")
        continue  # Skip this pattern entirely

    if begrip_lower.endswith(suffix):
        pattern_score += weight
    elif suffix in begrip_lower:
        pattern_score += weight * 0.5
```

---

### Step 4: Add Tests (30 min)

```python
# tests/ontologie/test_classifier_exclusions.py

import pytest
from ontologie.improved_classifier import ImprovedOntologyClassifier
from domain.ontological_categories import OntologischeCategorie


def test_woord_suffix_exclusions():
    """DEF-138: Test that exclusions prevent false positives for -woord pattern."""
    classifier = ImprovedOntologyClassifier()

    # TRUE POSITIVES (should be TYPE)
    result = classifier.classify("werkwoord")
    assert result.categorie == OntologischeCategorie.TYPE
    assert result.confidence >= 0.70  # High confidence

    result = classifier.classify("bijwoord")
    assert result.categorie == OntologischeCategorie.TYPE

    # FALSE POSITIVES (excluded, should NOT be TYPE)
    result = classifier.classify("woordvoerder")
    assert result.categorie == OntologischeCategorie.PROCES
    assert "woordvoerder" not in result.reasoning  # Pattern should not have matched

    result = classifier.classify("woordbreuk")
    assert result.categorie != OntologischeCategorie.TYPE


def test_naam_suffix_exclusions():
    """DEF-138: Test that exclusions prevent false positives for -naam pattern."""
    classifier = ImprovedOntologyClassifier()

    # TRUE POSITIVES (should be TYPE)
    result = classifier.classify("voornaam")
    assert result.categorie == OntologischeCategorie.TYPE

    # FALSE POSITIVES (excluded, should NOT be TYPE)
    result = classifier.classify("naamsverminking")
    assert result.categorie == OntologischeCategorie.PROCES

    result = classifier.classify("naamgeving")
    assert result.categorie == OntologischeCategorie.PROCES


def test_exclusion_list_validation():
    """Ensure exclusion list only contains lowercase terms."""
    from services.classification.term_config import load_term_config

    config = load_term_config()

    for category, patterns in config.suffix_weights.items():
        for suffix, pattern_data in patterns.items():
            if isinstance(pattern_data, dict):
                exclusions = pattern_data.get("exclusions", [])
                for term in exclusions:
                    assert term == term.lower(), f"Exclusion '{term}' must be lowercase"
```

---

### Step 5: Documentation (15 min)

Update `config/classification/term_patterns.yaml` with comments:

```yaml
# ============================================================
# SUFFIX WEIGHTS - EXTENDED FORMAT (DEF-138 Bug Fix)
# ============================================================
# Two formats supported:
#
# 1. Simple format (backward compatible):
#    suffix: 0.70
#
# 2. Complex format (with exclusions):
#    suffix:
#      weight: 0.70
#      exclusions:
#        - "term1"  # Reason why excluded
#        - "term2"
#
# EXCLUSIONS: Prevent false positives by explicitly listing
# compound words that match the pattern but belong to different category.
# Example: "woordvoerder" ends in -woord but is PROCES, not TYPE.
```

---

## Rollout Plan

### Phase 1: Implementation (2 hours)
- ✅ Update YAML schema
- ✅ Update TermPatternConfig
- ✅ Update pattern matching logic
- ✅ Add exclusions for known false positives

### Phase 2: Testing (30 min)
- ✅ Run new test suite
- ✅ Regression test: verify existing classifications still work
- ✅ Manual testing: spot-check 20 problematic terms

### Phase 3: Deployment (15 min)
- ✅ Commit changes with conventional commit message
- ✅ Update DEF-138 ticket with resolution
- ✅ Monitor production logs for any new classification issues

---

## Risk Assessment

**Risk Level:** LOW
- Backward compatible (both formats supported)
- Explicit exclusions (easy to debug)
- No performance impact (simple list check)

**Rollback Plan:**
If issues arise, remove exclusions from YAML → classifier falls back to old behavior.

---

## Success Criteria

1. ✅ `woordvoerder` classified as PROCES (not TYPE)
2. ✅ `werkwoord` still classified as TYPE (not broken)
3. ✅ All existing tests pass
4. ✅ New test suite passes (100% coverage for exclusions)
5. ✅ No performance regression (<5ms overhead)

---

## Next Steps

1. **Implement Option A** (exclusion patterns)
2. **Run comprehensive test suite**
3. **Manual QA:** Test 20 known edge cases
4. **Update DEF-138 documentation**
5. **Monitor production:** Watch for new false positives in next 48h

---

**Created:** 2025-11-10
**Author:** Debug Specialist
**Related:** DEF-138, BUG_HUNT_REPORT_DEF138_COMPREHENSIVE.md
