# UFO Classifier - Concrete Fixes voor Geïdentificeerde Bugs

**Datum**: 2025-10-07
**Bronanalyse**: `UFO_CLASSIFIER_DEBUG_ANALYSIS.md`
**Test Suite**: `tests/debug/test_ufo_classifier_bugs_reproduction.py`

---

## Quick Reference

| Bug ID | Severity | Impact | Fix Time | Status |
|--------|----------|--------|----------|--------|
| BUG-1  | CRITICAL | Tests falen | 1h | TODO |
| BUG-2  | CRITICAL | Silent failures | 30m | TODO |
| BUG-3  | MEDIUM | Inconsistent confidence | 2h | TODO |
| BUG-4  | MEDIUM | Performance hang | 3h | TODO |
| BUG-5  | MEDIUM | Data quality | 2h | TODO |

---

## BUG-1: Input Validatie Fix

### Probleem
```python
# Current code (line 323-334):
if not term or not definition:
    return UFOClassificationResult(
        term=term or "",
        definition=definition or "",
        primary_category=UFOCategory.UNKNOWN,
        confidence=MIN_CONFIDENCE,
        explanation=["Empty or invalid input"],
    )
```

**Issue**: Tests verwachten `ValueError`, code retourneert `UNKNOWN`.

### Fix

```python
def classify(
    self, term: str, definition: str, context: dict | None = None
) -> UFOClassificationResult:
    """
    Classify a Dutch legal term into UFO category.

    Args:
        term: The term to classify (non-empty string)
        definition: Definition of the term (non-empty string)
        context: Optional context information

    Returns:
        UFOClassificationResult with category and confidence

    Raises:
        ValueError: If term or definition is empty/whitespace after normalization
        TypeError: If term or definition is not a string
    """
    start_time = datetime.now()

    # PHASE 1: Type validation
    if term is None or definition is None:
        raise ValueError("term en definition mogen niet None zijn")

    if not isinstance(term, str):
        raise TypeError(f"term moet een string zijn, kreeg {type(term).__name__}")

    if not isinstance(definition, str):
        raise TypeError(
            f"definition moet een string zijn, kreeg {type(definition).__name__}"
        )

    # PHASE 2: Content validation (after normalization)
    term = self._normalize_text(term)
    definition = self._normalize_text(definition)

    if not term:
        raise ValueError(
            "term mag niet leeg zijn (na verwijderen whitespace en speciale tekens)"
        )

    if not definition:
        raise ValueError(
            "definition mag niet leeg zijn (na verwijderen whitespace en speciale tekens)"
        )

    # PHASE 3: Classification (existing logic)
    try:
        # ... existing feature extraction, disambiguation, etc.
        pass
    except Exception as e:
        logger.error(f"Error classifying '{term}': {e}")
        return UFOClassificationResult(
            term=term,
            definition=definition,
            primary_category=UFOCategory.UNKNOWN,
            confidence=MIN_CONFIDENCE,
            explanation=[f"Classification error: {e!s}"],
        )
```

### Test Verification

```python
# These should now pass:
def test_empty_term_raises(classifier):
    with pytest.raises(ValueError, match="mag niet leeg"):
        classifier.classify("", "valid definition")

def test_none_term_raises(classifier):
    with pytest.raises(ValueError, match="mogen niet None"):
        classifier.classify(None, "valid definition")

def test_non_string_raises(classifier):
    with pytest.raises(TypeError, match="moet een string zijn"):
        classifier.classify(123, "valid definition")
```

---

## BUG-2: None Guards Fix

### Probleem
```python
# _normalize_text() line 200:
if not text or not isinstance(text, str):
    return ""  # Silent failure
```

### Fix

```python
def _normalize_text(self, text: str) -> str:
    """
    Normalize text with full Unicode support for Dutch.

    Args:
        text: Input text to normalize (must be string, can be empty)

    Returns:
        Normalized text (can be empty string if input was whitespace-only)

    Raises:
        TypeError: If text is not a string
    """
    # Type check
    if text is None:
        raise TypeError("text cannot be None")

    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")

    # Handle empty string early
    if not text:
        return ""

    # Strip whitespace
    text = text.strip()

    # Remove control characters (except tab, newline, return)
    text = "".join(
        ch
        for ch in text
        if unicodedata.category(ch)[0] != "C" or ch in "\t\n\r"
    )

    # Remove zero-width characters
    zero_width_chars = "\u200b\u200c\u200d\ufeff"
    for zwc in zero_width_chars:
        text = text.replace(zwc, "")

    # Normalize Unicode to NFC (canonical composition)
    text = unicodedata.normalize("NFC", text)

    # Normalize whitespace (collapse multiple spaces)
    text = " ".join(text.split())

    # Limit length with warning
    if len(text) > MAX_TEXT_LENGTH:
        logger.warning(
            f"Text truncated from {len(text)} to {MAX_TEXT_LENGTH} chars "
            f"for input starting with: {text[:50]!r}..."
        )
        text = text[:MAX_TEXT_LENGTH]

    return text
```

---

## BUG-3: Score Calculation Fix

### Probleem
Ambiguity penalty kan leiden tot inconsistente confidence scores.

### Fix

```python
def _determine_primary_category(
    self, scores: dict[UFOCategory, float]
) -> tuple[UFOCategory, float]:
    """
    Determine primary category from scores with proper guards.

    Args:
        scores: Dictionary mapping categories to raw scores

    Returns:
        Tuple of (primary_category, confidence)
    """
    if not scores:
        return UFOCategory.UNKNOWN, 0.0  # Changed from DEFAULT_CONFIDENCE

    # Sort by score DESC, then category name ASC (for determinism)
    sorted_scores = sorted(
        scores.items(), key=lambda x: (-x[1], x[0].value)
    )

    primary_cat, primary_score = sorted_scores[0]

    # GUARD: Ensure valid score
    primary_score = max(MIN_CONFIDENCE, min(primary_score, MAX_CONFIDENCE))

    # Count ties at top score (within 1% tolerance)
    top_score = primary_score
    num_ties = sum(1 for _, score in sorted_scores if abs(score - top_score) < 0.01)

    if num_ties > 1:
        # Multiple categories tied - very ambiguous
        confidence = primary_score * 0.5
        logger.warning(
            f"Highly ambiguous: {num_ties} categories tied at {top_score:.2f}"
        )
        return primary_cat, max(MIN_CONFIDENCE, confidence)

    # Check second place for ambiguity
    if len(sorted_scores) > 1:
        second_score = sorted_scores[1][1]
        margin = primary_score - second_score

        # Only reduce confidence if:
        # 1. Margin is small (< 0.1)
        # 2. Primary score is significant (> 0.3)
        if margin < 0.1 and primary_score > 0.3:
            # Proportional reduction based on margin
            # Margin 0.1 → no reduction
            # Margin 0.05 → 50% of max reduction
            # Margin 0.0 → max reduction (50%)
            margin_ratio = margin / 0.1  # [0.0, 1.0]
            reduction = 1.0 - (1.0 - margin_ratio) * 0.5  # [0.5, 1.0]

            primary_score *= reduction
            logger.debug(
                f"Ambiguity detected: margin={margin:.2f}, "
                f"reduction factor={reduction:.2f}"
            )

    # FINAL GUARD
    return primary_cat, max(MIN_CONFIDENCE, min(primary_score, MAX_CONFIDENCE))
```

---

## BUG-4: Regex Performance Fix

### Probleem
Geen timeout bij regex matching, kan hangen op pathological input.

### Fix

```python
import signal
from contextlib import contextmanager

@contextmanager
def time_limit(seconds: int):
    """
    Context manager voor timeout protection.

    Raises:
        TimeoutError: Als operatie te lang duurt
    """

    def signal_handler(signum, frame):
        raise TimeoutError("Operation timed out")

    # Set alarm
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        # Cancel alarm
        signal.alarm(0)


def _extract_features(self, term: str, definition: str) -> dict[UFOCategory, float]:
    """
    Extract pattern-based features from text with timeout protection.

    Args:
        term: Term to classify
        definition: Definition text

    Returns:
        Dictionary mapping categories to raw scores
    """
    scores = {}

    # Combine and normalize
    combined_text = f"{term} {definition}".lower()

    # Limit text length for regex performance
    # (More aggressive than MAX_TEXT_LENGTH for pattern matching)
    if len(combined_text) > 5000:
        logger.warning(f"Combined text truncated to 5000 chars for pattern matching")
        combined_text = combined_text[:5000]

    # Pattern matching with timeout protection
    try:
        with time_limit(2):  # 2 second timeout
            for category, patterns in self.compiled_patterns.items():
                score = 0.0
                pattern_count = 0

                for pattern in patterns:
                    try:
                        if match := pattern.search(combined_text):
                            # Weight by position (earlier = more important)
                            match_pos = match.start() / max(len(combined_text), 1)
                            match_len = len(match.group(0))

                            # Score: base 0.4, adjusted for position and length
                            position_weight = 1.0 - (match_pos * 0.3)  # [0.7, 1.0]
                            length_weight = min(match_len / 10, 1.0)  # [0.0, 1.0]

                            weight = 0.4 * position_weight * length_weight
                            score += weight
                            pattern_count += 1

                    except Exception as e:
                        logger.warning(f"Pattern matching error: {e}")
                        continue

                # Apply quality penalty for single weak match
                if pattern_count == 1 and score < 0.2:
                    score *= 0.7  # 30% penalty for single weak pattern

                if score > 0:
                    scores[category] = min(score, MAX_CONFIDENCE)

    except TimeoutError:
        logger.error(
            f"Regex timeout for term '{term[:50]}' with {len(combined_text)} chars"
        )
        # Return empty scores - will trigger UNKNOWN classification
        return {}

    return scores
```

---

## BUG-5: Unicode Normalization Fix

**Zie BUG-2 fix hierboven** - `_normalize_text()` is volledig herschreven met:
- Control character removal
- Zero-width character removal
- NFC normalization
- Whitespace collapse
- Length limiting met warning

---

## EDGE CASE FIXES

### EDGE-1: All Scores Zero

```python
# In _determine_primary_category():
if not scores:
    return UFOCategory.UNKNOWN, 0.0  # Changed from DEFAULT_CONFIDENCE (0.3)
```

**Rationale**: Geen evidence = geen confidence. 0.3 is misleidend.

---

### EDGE-3: All Scores Equal (Tie-Breaking)

```python
# Deterministic sorting:
sorted_scores = sorted(
    scores.items(),
    key=lambda x: (-x[1], x[0].value)  # Score DESC, category name ASC
)
```

**Rationale**: Bij gelijke scores, sort op category naam voor determinisme.

---

### EDGE-7: Very Long Text Truncation

```python
# In _normalize_text():
if len(text) > MAX_TEXT_LENGTH:
    logger.warning(
        f"Text truncated from {len(text)} to {MAX_TEXT_LENGTH} chars "
        f"for input starting with: {text[:50]!r}..."
    )
    text = text[:MAX_TEXT_LENGTH]
```

**Rationale**: User moet weten dat truncation plaatsvond.

---

## IMPROVED CONFIDENCE FORMULA

### Current Formula
```python
# Pattern score: 0.4 per match, clamped at 1.0
# Disambiguation: +0.3
# Ambiguity: *0.8 if margin < 0.1
```

### Proposed Formula

```python
def _calculate_calibrated_confidence(
    self,
    primary_cat: UFOCategory,
    raw_score: float,
    all_scores: dict[UFOCategory, float],
    num_patterns: int,
    disambiguation_used: bool,
) -> float:
    """
    Calculate calibrated confidence using multiple factors.

    Factors:
    1. Raw score magnitude [0-1]
    2. Pattern count quality [0.5-1.0]
    3. Score distribution (ambiguity) [0.5-1.0]
    4. Disambiguation boost [1.0-1.1]

    Returns:
        Calibrated confidence in [MIN_CONFIDENCE, MAX_CONFIDENCE]
    """

    # Factor 1: Base score
    base = raw_score

    # Factor 2: Quality (more patterns = higher confidence)
    if num_patterns >= 3:
        quality = 1.0
    elif num_patterns == 2:
        quality = 0.9
    elif num_patterns == 1:
        quality = 0.7
    else:
        quality = 0.5

    # Factor 3: Ambiguity (score distribution)
    sorted_scores = sorted(all_scores.values(), reverse=True)
    if len(sorted_scores) >= 2:
        margin = sorted_scores[0] - sorted_scores[1]
        margin_ratio = margin / max(sorted_scores[0], 0.01)
        # High margin_ratio = clear winner = high certainty
        ambiguity = 0.5 + (margin_ratio * 0.5)  # [0.5, 1.0]
    else:
        ambiguity = 1.0  # Only one category

    # Factor 4: Disambiguation
    disambiguation_boost = 1.1 if disambiguation_used else 1.0

    # Combine factors
    confidence = base * quality * ambiguity * disambiguation_boost

    # Clamp
    return max(MIN_CONFIDENCE, min(confidence, MAX_CONFIDENCE))
```

**Usage**:
```python
# In classify():
confidence = self._calculate_calibrated_confidence(
    primary_category=primary_cat,
    raw_score=raw_score,
    all_scores=scores,
    num_patterns=len(matched_patterns),
    disambiguation_used=disambiguation_applied,
)
```

---

## POLICY UPDATES

### Updated Constants

```python
# Confidence bounds
MIN_CONFIDENCE = 0.05  # Lowered from 0.1
MAX_CONFIDENCE = 1.0
DEFAULT_CONFIDENCE = 0.0  # Changed from 0.3 (no evidence = no confidence)

# Quality gates
CONFIDENCE_HIGH = 0.8  # Auto-approve
CONFIDENCE_MEDIUM = 0.6  # Review recommended
CONFIDENCE_LOW = 0.4  # Review required
CONFIDENCE_INSUFFICIENT = 0.4  # Below this: manual classification

# Secondary category threshold
SECONDARY_THRESHOLD = 0.35  # Raised from 0.2 (reduce noise)
```

### Result Properties

```python
@dataclass
class UFOClassificationResult:
    # ... existing fields ...

    @property
    def quality_level(self) -> str:
        """Quality level for approval gates."""
        if self.confidence >= CONFIDENCE_HIGH:
            return "HIGH"
        elif self.confidence >= CONFIDENCE_MEDIUM:
            return "MEDIUM"
        elif self.confidence >= CONFIDENCE_LOW:
            return "LOW"
        else:
            return "INSUFFICIENT"

    @property
    def requires_review(self) -> bool:
        """True if human review recommended."""
        return self.confidence < CONFIDENCE_MEDIUM

    @property
    def requires_manual_classification(self) -> bool:
        """True if automatic classification unreliable."""
        return self.confidence < CONFIDENCE_LOW

    @property
    def can_auto_approve(self) -> bool:
        """True if confidence high enough for auto-approval."""
        return self.confidence >= CONFIDENCE_HIGH
```

---

## DISAMBIGUATION IMPROVEMENTS

### Current Issue
```python
# Only first matching pattern gets boost:
for pattern_str, target_category in rules["patterns"].items():
    if re.search(pattern_str, definition_lower):
        scores[target_category] = min(current + 0.3, MAX_CONFIDENCE)
        break  # STOPS HERE!
```

### Improved Version

```python
def _apply_disambiguation(
    self, term: str, definition: str, scores: dict[UFOCategory, float]
) -> tuple[dict[UFOCategory, float], bool]:
    """
    Apply disambiguation rules with weighted boosting.

    Returns:
        Tuple of (updated_scores, disambiguation_applied)
    """
    term_lower = term.lower()

    if term_lower not in self.DISAMBIGUATION_RULES:
        return scores, False

    rules = self.DISAMBIGUATION_RULES[term_lower]
    definition_lower = definition.lower()

    # Collect ALL matches with position scores
    matches = []
    for pattern_str, target_category in rules["patterns"].items():
        if match := re.search(pattern_str, definition_lower):
            # Earlier matches are more important
            position = match.start() / max(len(definition_lower), 1)
            position_score = 1.0 - position  # [0.0, 1.0]
            matches.append((target_category, position_score))

    if not matches:
        return scores, False

    # Distribute boost proportionally
    total_position_score = sum(ps for _, ps in matches)

    for target_cat, pos_score in matches:
        weight = pos_score / total_position_score
        boost = 0.3 * weight  # Proportional boost

        current = scores.get(target_cat, 0.0)
        scores[target_cat] = min(current + boost, MAX_CONFIDENCE)

        logger.debug(
            f"Disambiguation: '{term}' → {target_cat.value} "
            f"(boost={boost:.2f}, position_weight={weight:.2f})"
        )

    return scores, True
```

---

## TEST VERIFICATION CHECKLIST

### BUG-1 Tests
- [ ] `test_empty_term_raises()`
- [ ] `test_empty_definition_raises()`
- [ ] `test_whitespace_only_raises()`
- [ ] `test_none_term_raises()`
- [ ] `test_none_definition_raises()`
- [ ] `test_non_string_raises()`

### BUG-2 Tests
- [ ] `test_none_handling()`
- [ ] `test_type_checking()`

### BUG-3 Tests
- [ ] `test_confidence_never_exceeds_one()`
- [ ] `test_confidence_bounds()`

### BUG-4 Tests
- [ ] `test_regex_performance_large_text()`
- [ ] `test_redos_protection()`

### BUG-5 Tests
- [ ] `test_zero_width_removed()`
- [ ] `test_bom_removed()`
- [ ] `test_control_chars_removed()`
- [ ] `test_nfc_nfd_consistency()`

### Edge Case Tests
- [ ] `test_no_pattern_matches()` - Confidence should be 0.0
- [ ] `test_perfect_ambiguity()` - Deterministic tie-breaking
- [ ] `test_long_text_warning_logged()`
- [ ] `test_emoji_handling()`
- [ ] `test_mixed_scripts()`

---

## IMPLEMENTATION PLAN

### Phase 1: Critical Bugs (Priority 1)
**Tijd**: 2 uur

1. **BUG-1**: Input validatie
   - Update `classify()` met type/content checks
   - Add proper exception raising
   - Test: Run `test_ufo_classifier_edge_cases.py`

2. **BUG-2**: None guards
   - Rewrite `_normalize_text()` met guards
   - Add zero-width/control char removal
   - Test: Run bug reproduction tests

### Phase 2: Score & Performance (Priority 2)
**Tijd**: 5 uur

3. **BUG-3**: Score calculation
   - Update `_determine_primary_category()` met proper guards
   - Implement proportional ambiguity penalty
   - Test: Confidence bounds tests

4. **BUG-4**: Regex timeout
   - Add `time_limit()` context manager
   - Wrap pattern matching in timeout
   - Test: Performance tests

5. **EDGE-3**: Tie-breaking
   - Update sorting for determinism
   - Test: Run disambiguation tests 10x

### Phase 3: Confidence & Policy (Priority 3)
**Tijd**: 4 uur

6. **Confidence Formula**: Implement calibrated version
   - Add `_calculate_calibrated_confidence()`
   - Update result properties
   - Test: Compare old vs new confidence scores

7. **Policy Updates**: Update constants and thresholds
   - DEFAULT_CONFIDENCE = 0.0
   - SECONDARY_THRESHOLD = 0.35
   - Add quality level properties

8. **Disambiguation**: Improve weighted boosting
   - Rewrite `_apply_disambiguation()`
   - Handle multiple matches proportionally
   - Test: Disambiguation tests

### Phase 4: Testing & Validation (Priority 4)
**Tijd**: 3 uur

9. Run full test suite
10. Fix any remaining failures
11. Update documentation
12. Code review

**Total Estimated Time**: ~14 uur (2 dagen)

---

## VERIFICATION COMMANDS

```bash
# Run bug reproduction tests
pytest tests/debug/test_ufo_classifier_bugs_reproduction.py -v

# Run edge case tests
pytest tests/services/test_ufo_classifier_edge_cases.py -v

# Run full classifier test suite
pytest tests/services/test_ufo_classifier*.py -v

# Check coverage
pytest tests/services/test_ufo_classifier*.py --cov=src.services.ufo_classifier_service --cov-report=html

# Benchmark performance
pytest tests/debug/test_ufo_performance.py -v
```

---

## ROLLBACK PLAN

Als fixes problemen veroorzaken:

1. **Backup current version**:
   ```bash
   cp src/services/ufo_classifier_service.py src/services/ufo_classifier_service.py.backup
   ```

2. **Git revert**:
   ```bash
   git checkout src/services/ufo_classifier_service.py
   ```

3. **Cherry-pick safe fixes**:
   - Start met BUG-1 en BUG-2 (input validatie)
   - Test grondig voor elke fix
   - Commit incrementeel

---

## NOTES

- Alle fixes zijn **backwards incompatible** maar dit is acceptabel:
  - Single-user application
  - No production usage yet
  - Refactor, geen backwards compatibility (per CLAUDE.md)

- Tests zullen **initieel falen** - dit is verwacht:
  - Huidige implementation matcht niet test expectations
  - Fixes maken implementation compliant met tests

- Performance impact is **minimal**:
  - Type checking: negligible
  - Timeout wrapper: only for edge cases
  - Unicode normalization: already present, just improved

---

**End of Fixes Document**
