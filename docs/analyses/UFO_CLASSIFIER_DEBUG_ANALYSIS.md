# UFO Classifier - Grondige Debug Analyse

**Datum**: 2025-10-07
**Versie**: 5.0.0
**Doel**: Identificatie van potentiële bugs, edge cases en risico's

---

## Executive Summary

Na grondige analyse van `ufo_classifier_service.py` zijn **5 kritieke bugs**, **8 edge case risico's** en **12 potentiële verbeteringen** geïdentificeerd. De implementatie scoort:

- **Correctheid**: 7/10 (goede basis, maar mist input validatie)
- **Robuustheid**: 6/10 (geen guards voor edge cases)
- **Performance**: 8/10 (goede caching strategie)
- **Security**: 5/10 (geen input sanitization)

---

## 1. KRITIEKE BUGS 🔴

### BUG-1: Geen Input Validatie (HIGH SEVERITY)

**Locatie**: `classify()` method, line 323-334

**Probleem**:
```python
# Current code:
term = self._normalize_text(term)
definition = self._normalize_text(definition)

if not term or not definition:
    return UFOClassificationResult(
        term=term or "",
        definition=definition or "",
        primary_category=UFOCategory.UNKNOWN,
        confidence=MIN_CONFIDENCE,
        explanation=["Empty or invalid input"],
    )
```

**Issue**:
- Tests verwachten `ValueError` bij lege input (zie test_ufo_classifier_edge_cases.py:46)
- Huidige code returnt UNKNOWN i.p.v. exception
- Mismatch tussen test expectations en implementatie

**Bewijs**:
```python
# From test file:
def test_empty_string_validation(self, classifier):
    with pytest.raises(ValueError, match="term.*niet-lege"):
        classifier.classify("", "valid definition")  # Verwacht exception!
```

**Impact**: HOOG - Tests zullen falen, contract niet gerespecteerd

**Fix**:
```python
def classify(self, term: str, definition: str, context: dict | None = None) -> UFOClassificationResult:
    # VALIDATION FIRST
    if not isinstance(term, str) or not isinstance(definition, str):
        raise ValueError("term en definition moeten niet-lege strings zijn")

    # Normalize
    term = self._normalize_text(term)
    definition = self._normalize_text(definition)

    # Check after normalization
    if not term.strip():
        raise ValueError("term mag niet leeg zijn na normalisatie")
    if not definition.strip():
        raise ValueError("definition mag niet leeg zijn na normalisatie")

    # Continue with classification...
```

---

### BUG-2: Missing None Guards (HIGH SEVERITY)

**Locatie**: Multiple locations

**Probleem**:
```python
# _normalize_text() line 200:
if not text or not isinstance(text, str):
    return ""  # Returns empty string for None

# But classify() doesn't check for None BEFORE calling _normalize_text
term = self._normalize_text(term)  # If term is None, returns ""
```

**Test Expectation**:
```python
def test_none_input_handling(self, classifier):
    with pytest.raises(ValueError, match="niet-lege string"):
        classifier.classify(None, "definition")  # Expects exception!
```

**Impact**: HOOG - Silent failures instead of explicit errors

**Fix**:
```python
def classify(self, term: str, definition: str, context: dict | None = None):
    # Validate types FIRST
    if term is None or definition is None:
        raise ValueError("term en definition mogen niet None zijn")
    if not isinstance(term, str) or not isinstance(definition, str):
        raise TypeError(f"term en definition moeten strings zijn, got {type(term)}, {type(definition)}")

    # Then normalize
    term = self._normalize_text(term)
    definition = self._normalize_text(definition)
```

---

### BUG-3: Score Calculation Kan Leiden tot Confidence > 1.0 (MEDIUM SEVERITY)

**Locatie**: `_extract_features()`, line 224

**Probleem**:
```python
for pattern in patterns:
    if pattern.search(combined_text):
        score += 0.4  # Simple scoring: 0.4 per match
        matches.append(pattern.pattern)

if score > 0:
    scores[category] = min(score, MAX_CONFIDENCE)  # Clamps at 1.0
```

**Issue**:
- Disambiguation kan score verhogen: `scores[target_category] = min(current + 0.3, MAX_CONFIDENCE)`
- Maar wat als current al 0.8 is? Dan wordt het 1.0
- Daarna in `_determine_primary_category()` kan confidence worden verlaagd bij ambiguity
- Inconsistente scoring logica

**Edge Case**:
```python
# Scenario:
# - Pattern matching: score = 0.8
# - Disambiguation: score = 0.8 + 0.3 = 1.0 (clamped)
# - Ambiguity check: confidence = 1.0 * 0.8 = 0.8
#
# Maar wat als twee categorieën beide 1.0 scoren?
# Dan wordt primary: 1.0 * 0.8 = 0.8
# En secondary blijft 1.0 (internal score)
# → Secondary heeft hogere raw score dan primary!
```

**Fix**:
```python
def _determine_primary_category(
    self, scores: dict[UFOCategory, float]
) -> tuple[UFOCategory, float]:
    if not scores:
        return UFOCategory.UNKNOWN, DEFAULT_CONFIDENCE

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary_cat, primary_score = sorted_scores[0]

    # GUARD: Ensure score is valid
    primary_score = max(MIN_CONFIDENCE, min(primary_score, MAX_CONFIDENCE))

    # Check for ambiguity
    if len(sorted_scores) > 1:
        second_score = sorted_scores[1][1]
        margin = primary_score - second_score

        # Only reduce if margin is small AND scores are high
        if margin < 0.1 and primary_score > 0.5:
            # Reduce proportionally to margin
            reduction = 1.0 - (margin / 0.1) * 0.2  # Max 20% reduction
            primary_score *= reduction

    # FINAL CLAMP
    return primary_cat, max(MIN_CONFIDENCE, min(primary_score, MAX_CONFIDENCE))
```

---

### BUG-4: Regex Performance op Lange Teksten (MEDIUM SEVERITY)

**Locatie**: `_extract_features()`, line 218-229

**Probleem**:
```python
combined_text = f"{term} {definition}".lower()

for category, patterns in self.compiled_patterns.items():
    for pattern in patterns:
        if pattern.search(combined_text):  # O(n*m) per category
```

**Issue**:
- Bij MAX_TEXT_LENGTH = 10000 kan dit traag zijn
- Er zijn 9 categorieën × ~5 patterns = 45 regex searches per classificatie
- Geen timeout op regex matching
- Potentiële ReDoS (Regular Expression Denial of Service) bij malicious input

**Bewijs van Risico**:
```python
# Malicious input that can cause catastrophic backtracking:
term = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!"
definition = "a" * 5000  # Long repeated pattern

# Pattern zoals r"\b(procedure|proces|zitting)\b" is safe
# Maar custom patterns kunnen gevaarlijk zijn
```

**Test Case**:
```python
def test_regex_performance_large_text(classifier):
    """Test regex doesn't hang on large text."""
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError("Regex took too long")

    # Set 1 second timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(1)

    try:
        huge_text = "x" * 10000
        result = classifier.classify(huge_text, huge_text)
        signal.alarm(0)  # Cancel alarm
        assert result.classification_time_ms < 1000
    except TimeoutError:
        pytest.fail("Regex timeout on large input")
```

**Fix**:
```python
# Add timeout wrapper
import signal
from contextlib import contextmanager

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutError("Operation timed out")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

def _extract_features(self, term: str, definition: str) -> dict[UFOCategory, float]:
    scores = {}
    combined_text = f"{term} {definition}".lower()

    # Limit text length for regex
    if len(combined_text) > 5000:
        combined_text = combined_text[:5000]

    try:
        with time_limit(2):  # 2 second timeout
            for category, patterns in self.compiled_patterns.items():
                # ... existing logic
    except TimeoutError:
        logger.warning(f"Regex timeout for term '{term[:50]}'")
        return {}  # Return empty scores on timeout

    return scores
```

---

### BUG-5: Unicode Normalization Inconsistentie (LOW-MEDIUM SEVERITY)

**Locatie**: `_normalize_text()`, line 205

**Probleem**:
```python
text = unicodedata.normalize("NFC", text)
```

**Issue**:
- Tests verwachten consistent gedrag voor NFC, NFD, NFKC, NFKD (zie test line 227-241)
- Maar alleen NFC wordt gebruikt
- NFD input wordt geconverteerd naar NFC, maar dit kan semantiek veranderen

**Voorbeeld**:
```python
# Input: "café" in NFD form (e + combining acute)
# After NFC: "café" (precomposed é)
#
# Problem: Pattern matching kan verschillen
# r"\bcafé\b" in NFD form matches niet met NFC normalisatie
```

**Impact**: MEDIUM - Inconsistent behavior voor niet-NFC input

**Fix**:
```python
def _normalize_text(self, text: str) -> str:
    """Normalize text with full Unicode support for Dutch."""
    if not text or not isinstance(text, str):
        return ""

    # Strip whitespace first
    text = text.strip()

    # Remove control characters and zero-width spaces
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in "\t\n\r")

    # Normalize to NFC (canonical composition) for Dutch
    # This handles: café, coöperatie, geïnformeerd consistently
    text = unicodedata.normalize("NFC", text)

    # Also normalize whitespace
    text = " ".join(text.split())

    # Limit length
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]
        logger.warning(f"Text truncated to {MAX_TEXT_LENGTH} chars")

    return text
```

---

## 2. EDGE CASES & RISICO'S ⚠️

### EDGE-1: Alle Scores 0.0

**Scenario**:
```python
result = classifier.classify("xyz", "abc def ghi")
# No patterns match → scores = {}
```

**Huidige Gedrag**:
```python
# _determine_primary_category():
if not scores:
    return UFOCategory.UNKNOWN, DEFAULT_CONFIDENCE  # Returns 0.3
```

**Risico**:
- Is DEFAULT_CONFIDENCE (0.3) te hoog voor "geen enkele match"?
- Gebruiker ziet 30% confidence zonder enige evidence
- Misleidend voor decision making

**Aanbeveling**:
```python
if not scores:
    return UFOCategory.UNKNOWN, 0.0  # Zero confidence, geen matches
```

---

### EDGE-2: Één Score 1.0, Rest 0.0

**Scenario**:
```python
# Term matches 3+ patterns in één category:
scores = {
    UFOCategory.KIND: 1.0,
    # Rest: 0.0 (niet in dict)
}
```

**Huidige Gedrag**:
```python
# _determine_primary_category():
sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
primary_cat, primary_score = sorted_scores[0]  # KIND, 1.0

if len(sorted_scores) > 1:  # False! Only 1 entry
    # Ambiguity check skipped
```

**Risico**:
- Goede score, geen ambiguity check
- Maar wat als 1.0 is based on weak patterns?
- Geen quality check op "waarom 1.0?"

**Fix**:
```python
# Add pattern quality check
def _extract_features(self, term: str, definition: str) -> dict[UFOCategory, float]:
    scores = {}
    combined_text = f"{term} {definition}".lower()

    for category, patterns in self.compiled_patterns.items():
        score = 0.0
        matches = []
        pattern_weights = []  # Track individual pattern contributions

        for pattern in patterns:
            if match := pattern.search(combined_text):
                # Weight based on match position and length
                match_pos = match.start() / max(len(combined_text), 1)
                match_len = len(match.group(0))

                # Prefer matches early in text and longer matches
                weight = 0.4 * (1.0 - match_pos * 0.3) * min(match_len / 10, 1.0)
                score += weight
                pattern_weights.append(weight)
                matches.append(pattern.pattern)

        if score > 0:
            # If only one weak pattern matched, reduce confidence
            if len(pattern_weights) == 1 and pattern_weights[0] < 0.2:
                score *= 0.5  # Reduce confidence for single weak match

            scores[category] = min(score, MAX_CONFIDENCE)

    return scores
```

---

### EDGE-3: Alle Scores Gelijk

**Scenario**:
```python
# Ambiguous term matches equally across categories:
scores = {
    UFOCategory.KIND: 0.4,
    UFOCategory.EVENT: 0.4,
    UFOCategory.ROLE: 0.4,
    UFOCategory.RELATOR: 0.4,
}
```

**Huidige Gedrag**:
```python
sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
# Order is UNDEFINED for equal values! Python dict iteration order is insertion order in 3.7+
# but sorted() with equal keys is non-deterministic

primary_cat, primary_score = sorted_scores[0]  # Random category!
second_score = sorted_scores[1][1]  # 0.4
margin = 0.4 - 0.4 = 0.0

if margin < 0.1:  # True!
    primary_score *= 0.8  # 0.4 * 0.8 = 0.32
```

**Risico**:
- Non-deterministic results voor identieke input
- Tie-breaking is arbitrair (dict iteration order)
- Confidence wordt verlaagd maar primary category is random

**Fix**:
```python
def _determine_primary_category(
    self, scores: dict[UFOCategory, float]
) -> tuple[UFOCategory, float]:
    if not scores:
        return UFOCategory.UNKNOWN, DEFAULT_CONFIDENCE

    # Sort by score DESC, then by category name ASC for determinism
    sorted_scores = sorted(
        scores.items(),
        key=lambda x: (-x[1], x[0].value)  # Score DESC, name ASC
    )

    primary_cat, primary_score = sorted_scores[0]

    # Count ties at top score
    top_score = primary_score
    num_ties = sum(1 for _, score in sorted_scores if abs(score - top_score) < 0.01)

    if num_ties > 1:
        # Multiple categories tied - very low confidence
        confidence = primary_score * 0.5
        logger.warning(
            f"Ambiguous classification: {num_ties} categories tied at {top_score:.2f}"
        )
        return primary_cat, max(MIN_CONFIDENCE, confidence)

    # Check second place
    if len(sorted_scores) > 1:
        second_score = sorted_scores[1][1]
        margin = primary_score - second_score

        if margin < 0.1:
            primary_score *= 0.8

    return primary_cat, max(MIN_CONFIDENCE, min(primary_score, MAX_CONFIDENCE))
```

---

### EDGE-4: Scores met Negatieve Waarden

**Scenario**: Kan dit gebeuren?

**Analyse**:
```python
# In _extract_features():
score += 0.4  # Always positive increment
scores[category] = min(score, MAX_CONFIDENCE)  # Always positive

# In _apply_disambiguation():
current = scores.get(target_category, 0.0)  # Default 0.0
scores[target_category] = min(current + 0.3, MAX_CONFIDENCE)  # Always positive
```

**Conclusie**: ✅ GEEN RISICO - scores zijn altijd >= 0.0

---

### EDGE-5: Scores > 1.0

**Scenario**: Kan dit gebeuren na disambiguation?

**Analyse**:
```python
# _extract_features():
scores[category] = min(score, MAX_CONFIDENCE)  # Clamped at 1.0

# _apply_disambiguation():
scores[target_category] = min(current + 0.3, MAX_CONFIDENCE)  # Clamped at 1.0

# _determine_primary_category():
# primary_score komt direct uit scores dict, dus max 1.0
# But: primary_score *= 0.8 kan het verlagen
# GEEN check op MAX_CONFIDENCE na verlaging!
```

**Risico**: ❌ GEEN RISICO voor > 1.0, maar wel voor inconsistentie

**Echter**: Er is geen GUARD dat primary_score niet hoger wordt in edge cases.

**Defensive Fix**:
```python
def _determine_primary_category(
    self, scores: dict[UFOCategory, float]
) -> tuple[UFOCategory, float]:
    # ... existing logic ...

    # FINAL GUARD - paranoid but safe
    return primary_cat, max(MIN_CONFIDENCE, min(primary_score, MAX_CONFIDENCE))
```

---

### EDGE-6: Empty text_context (Lege Definitie)

**Scenario**:
```python
result = classifier.classify("test", "")
# After normalization: definition = ""
```

**Huidige Gedrag**:
```python
if not term or not definition:
    return UFOClassificationResult(
        term=term or "",
        definition=definition or "",
        primary_category=UFOCategory.UNKNOWN,
        confidence=MIN_CONFIDENCE,
        explanation=["Empty or invalid input"],
    )
```

**Issue**: Dit retourneert UNKNOWN met confidence 0.1

**Maar**: Test verwacht ValueError! (Zie BUG-1)

---

### EDGE-7: Zeer Lange text_context (10000+ chars)

**Scenario**:
```python
long_text = "x" * 15000
result = classifier.classify("test", long_text)
```

**Huidige Gedrag**:
```python
# _normalize_text():
if len(text) > MAX_TEXT_LENGTH:
    text = text[:MAX_TEXT_LENGTH]  # Truncates at 10000

# No warning logged!
```

**Risico**:
- Silent truncation kan leiden tot incomplete classification
- Belangrijk deel van definitie kan worden afgekapt
- Geen feedback naar gebruiker

**Fix**:
```python
if len(text) > MAX_TEXT_LENGTH:
    logger.warning(
        f"Text truncated from {len(text)} to {MAX_TEXT_LENGTH} chars for term '{text[:50]}...'"
    )
    text = text[:MAX_TEXT_LENGTH]
```

**Test**:
```python
def test_long_text_truncation_logging(classifier, caplog):
    """Test that truncation is logged."""
    long_text = "x" * 15000

    with caplog.at_level(logging.WARNING):
        result = classifier.classify("test", long_text)

    assert "truncated" in caplog.text.lower()
    assert len(result.definition) == 10000
```

---

### EDGE-8: Unicode/Special Chars Edge Cases

**Scenario**: Emoji, control characters, RTL text

**Test Bevindingen** (from test_ufo_classifier_edge_cases.py:208-216):
```python
test_cases = [
    ("test\u200b", "zero-width space"),  # Zero-width space
    ("test\ufeff", "BOM character"),      # Byte order mark
    ("🏛️", "emoji rechtbank"),            # Emoji
    ("test™", "trademark symbol"),         # Special symbols
    ("Α", "Greek alpha"),                  # Non-Latin scripts
    ("א", "Hebrew aleph"),                 # Right-to-left script
]
```

**Risico**: Huidige `_normalize_text()` handelt deze NIET af!

**Probleem**:
```python
# Current normalization:
text = unicodedata.normalize("NFC", text)

# But:
# - Zero-width spaces blijven staan
# - BOM characters blijven staan
# - Emoji blijven staan
# - RTL marks blijven staan
```

**Fix**:
```python
def _normalize_text(self, text: str) -> str:
    if not text or not isinstance(text, str):
        return ""

    text = text.strip()

    # Remove control characters (category C*)
    # Keep only: Cc (control) that are tab/newline/return
    text = "".join(
        ch for ch in text
        if unicodedata.category(ch)[0] != "C"
        or ch in "\t\n\r"
    )

    # Remove zero-width characters
    zero_width_chars = "\u200b\u200c\u200d\ufeff"
    for zwc in zero_width_chars:
        text = text.replace(zwc, "")

    # Normalize Unicode
    text = unicodedata.normalize("NFC", text)

    # Normalize whitespace (collapse multiple spaces)
    text = " ".join(text.split())

    # Length limit
    if len(text) > MAX_TEXT_LENGTH:
        logger.warning(f"Text truncated to {MAX_TEXT_LENGTH} chars")
        text = text[:MAX_TEXT_LENGTH]

    return text
```

---

## 3. CONFIDENCE FORMULA ANALYSE 🧮

### Huidige Formule

**Pattern Matching Score**:
```python
score = 0.4 * number_of_matches  # Max: 0.4 * 3+ = 1.2+ → clamped to 1.0
```

**Disambiguation Boost**:
```python
score = min(current + 0.3, 1.0)  # Adds 0.3 if disambiguation matches
```

**Ambiguity Penalty**:
```python
if margin < 0.1:
    confidence = primary_score * 0.8  # 20% reduction
```

### Problemen

1. **Overweegt Pattern Quantity over Quality**
   - 3 weak patterns = 1.0 confidence
   - 1 strong pattern = 0.4 confidence
   - Geen weighting voor pattern importance

2. **Disambiguation Te Sterk**
   - +0.3 is 75% van een pattern match (0.4)
   - Disambiguation boost > pattern match

3. **Ambiguity Penalty Te Simpel**
   - Only checks top 2 scores
   - Doesn't consider magnitude of scores
   - 0.9 vs 0.85 gets same penalty as 0.3 vs 0.25

4. **Geen Calibratie**
   - Confidence heeft geen semantische betekenis
   - 0.7 betekent niet "70% kans op correct"
   - Geen historische validatie data

### Voorgestelde Verbeterde Formule

```python
def _calculate_confidence(
    self,
    primary_cat: UFOCategory,
    primary_score: float,
    all_scores: dict[UFOCategory, float],
    num_patterns_matched: int,
    disambiguation_applied: bool
) -> float:
    """
    Calculate calibrated confidence score.

    Factors:
    1. Raw score magnitude (0-1)
    2. Number of patterns matched (quality signal)
    3. Score distribution (ambiguity)
    4. Disambiguation certainty

    Returns confidence in [0.1, 1.0]
    """

    # Base confidence from score
    base_conf = primary_score

    # Quality adjustment: More patterns = higher confidence
    if num_patterns_matched >= 3:
        quality_mult = 1.0
    elif num_patterns_matched == 2:
        quality_mult = 0.9
    elif num_patterns_matched == 1:
        quality_mult = 0.7  # Single pattern is weaker
    else:
        quality_mult = 0.5  # Should not happen

    # Ambiguity adjustment: Calculate entropy of score distribution
    sorted_scores = sorted(all_scores.values(), reverse=True)

    if len(sorted_scores) >= 2:
        # Margin ratio: how much better is #1 vs #2?
        margin = sorted_scores[0] - sorted_scores[1]
        margin_ratio = margin / max(sorted_scores[0], 0.01)  # Avoid div/0

        # High margin ratio (e.g., 0.8 vs 0.2 → ratio=0.75) = high certainty
        # Low margin ratio (e.g., 0.5 vs 0.48 → ratio=0.04) = low certainty
        ambiguity_mult = 0.5 + (margin_ratio * 0.5)  # [0.5, 1.0]
    else:
        ambiguity_mult = 1.0  # Only one category matched

    # Disambiguation adjustment
    disambiguation_mult = 1.1 if disambiguation_applied else 1.0

    # Combine factors
    confidence = base_conf * quality_mult * ambiguity_mult * disambiguation_mult

    # Clamp to valid range
    return max(MIN_CONFIDENCE, min(confidence, MAX_CONFIDENCE))
```

**Voordelen**:
- Multifactorial (4 factoren)
- Considers pattern quality (count)
- Uses margin ratio instead of absolute margin
- Explicit disambiguation signal
- Still clamped to [0.1, 1.0]

---

## 4. POLICY DREMPELS ⚙️

### Huidige Drempels

```python
MIN_CONFIDENCE = 0.1
MAX_CONFIDENCE = 1.0
DEFAULT_CONFIDENCE = 0.3

# In _get_secondary_categories():
threshold = 0.2  # Hardcoded secondary threshold
```

### Problemen

1. **DEFAULT_CONFIDENCE = 0.3 Te Hoog**
   - Bij geen enkele match: 30% confidence
   - Misleidend - suggereert enige zekerheid
   - Beter: 0.0 of 0.05

2. **Secondary Threshold = 0.2 Te Laag**
   - Bijna elke category met 1 pattern match komt in secondary
   - Ruis in results
   - Beter: 0.3 of 0.4

3. **Geen Approval Gate Drempels**
   - Wanneer is confidence "hoog genoeg" voor auto-approval?
   - Wanneer moet human review?
   - Geen explicit thresholds

### Voorgestelde Policy

```python
# Confidence levels
MIN_CONFIDENCE = 0.05  # Lowered from 0.1
MAX_CONFIDENCE = 1.0
DEFAULT_CONFIDENCE = 0.0  # Changed from 0.3 - no evidence = no confidence

# Classification quality gates
CONFIDENCE_HIGH = 0.8       # Auto-approve safe
CONFIDENCE_MEDIUM = 0.6     # Review recommended
CONFIDENCE_LOW = 0.4        # Review required
# Below 0.4: Manual classification required

# Secondary category threshold
SECONDARY_THRESHOLD = 0.35  # Raised from 0.2 - reduce noise

# Approval gate integration
@dataclass
class UFOClassificationResult:
    # ... existing fields ...

    @property
    def quality_level(self) -> str:
        """Return quality level for approval gates."""
        if self.confidence >= 0.8:
            return "HIGH"
        elif self.confidence >= 0.6:
            return "MEDIUM"
        elif self.confidence >= 0.4:
            return "LOW"
        else:
            return "INSUFFICIENT"

    @property
    def requires_review(self) -> bool:
        """True if human review is required."""
        return self.confidence < 0.6

    @property
    def requires_manual_classification(self) -> bool:
        """True if automatic classification is not reliable."""
        return self.confidence < 0.4
```

---

## 5. TIE-BREAKING ANALYSE 🎲

### Huidige Implementatie

**Disambiguation Rules** (line 152-180):
```python
DISAMBIGUATION_RULES = {
    "zaak": {
        "patterns": {
            r"rechts|procedure|behandel": UFOCategory.EVENT,
            r"dossier|nummer|registr": UFOCategory.KIND,
            r"eigendom|goed|object": UFOCategory.RELATOR,
        }
    },
    # ... more rules
}
```

**Tie-Breaking Logic**:
```python
# In _determine_primary_category():
sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
primary_cat, primary_score = sorted_scores[0]
```

### Problemen

1. **Disambiguation Kan Bias Introduceren**

   **Voorbeeld**:
   ```python
   term = "zaak"
   definition = "Een rechtszaak met dossier en procedures"

   # Initial scores:
   # EVENT: 0.4 (procedure match)
   # KIND: 0.4 (dossier match)

   # Disambiguation matches BOTH:
   # - "rechts|procedure" → EVENT
   # - "dossier|nummer" → KIND

   # First pattern to match wins!
   # Order-dependent = bias
   ```

2. **Meerdere Tie-Breaker Matches**

   **Current Code**:
   ```python
   for pattern_str, target_category in rules["patterns"].items():
       if re.search(pattern_str, definition_lower):
           scores[target_category] = min(current + 0.3, MAX_CONFIDENCE)
           break  # ONLY FIRST MATCH!
   ```

   **Probleem**: Als 2 patterns matchen, alleen de eerste wordt gebruikt.
   - Dict iteration order in Python 3.7+ is insertion order
   - Maar dit is niet semantisch - willekeurig welke eerst is

3. **Geen Tie-Breaking voor Gelijke Scores**

   Als na disambiguation nog steeds tie:
   ```python
   scores = {
       UFOCategory.EVENT: 0.7,
       UFOCategory.KIND: 0.7,
   }

   sorted_scores = sorted(...)  # Order is undefined for equal values!
   ```

### Voorgestelde Fix

```python
def _apply_disambiguation(
    self, term: str, definition: str, scores: dict[UFOCategory, float]
) -> dict[UFOCategory, float]:
    """Apply disambiguation rules with proper tie-breaking."""
    term_lower = term.lower()

    if term_lower not in self.DISAMBIGUATION_RULES:
        return scores

    rules = self.DISAMBIGUATION_RULES[term_lower]
    definition_lower = definition.lower()

    # Collect ALL matches, not just first
    matches = []
    for pattern_str, target_category in rules["patterns"].items():
        if match := re.search(pattern_str, definition_lower):
            # Score by match position (earlier = more important)
            position_score = 1.0 - (match.start() / len(definition_lower))
            matches.append((target_category, position_score))

    if not matches:
        return scores

    # If multiple matches, use weighted average
    if len(matches) > 1:
        # Distribute boost proportionally
        total_position_score = sum(ps for _, ps in matches)
        for target_cat, pos_score in matches:
            weight = pos_score / total_position_score
            boost = 0.3 * weight  # Proportional boost
            current = scores.get(target_cat, 0.0)
            scores[target_cat] = min(current + boost, MAX_CONFIDENCE)
            logger.debug(
                f"Disambiguation: '{term}' → {target_cat} (+{boost:.2f}, position weight={weight:.2f})"
            )
    else:
        # Single match - full boost
        target_cat, _ = matches[0]
        current = scores.get(target_cat, 0.0)
        scores[target_cat] = min(current + 0.3, MAX_CONFIDENCE)
        logger.debug(f"Disambiguation: '{term}' → {target_cat} (+0.3)")

    return scores
```

**Deterministic Tie-Breaking**:
```python
def _determine_primary_category(
    self, scores: dict[UFOCategory, float]
) -> tuple[UFOCategory, float]:
    if not scores:
        return UFOCategory.UNKNOWN, DEFAULT_CONFIDENCE

    # Sort by: score DESC, then category name ASC (deterministic)
    sorted_scores = sorted(
        scores.items(),
        key=lambda x: (-x[1], x[0].value)
    )

    # ... rest of logic
```

---

## 6. PROBLEMATISCHE INPUT VOORBEELDEN 💣

### Test Case Suite

```python
# tests/debug/test_ufo_classifier_problematic_inputs.py

import pytest
from src.services.ufo_classifier_service import UFOClassifierService, UFOCategory

class TestProblematicInputs:
    """Test suite for problematic and edge case inputs."""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    # ============ EDGE CASE 1: ALL SCORES ZERO ============
    def test_no_pattern_matches(self, classifier):
        """Test classification when no patterns match."""
        result = classifier.classify("xyzabc", "qwerty asdf jklö")

        assert result.primary_category == UFOCategory.UNKNOWN
        assert result.confidence == 0.0  # Should be 0, not 0.3!
        assert "geen matches" in " ".join(result.explanation).lower()

    # ============ EDGE CASE 2: SINGLE HIGH SCORE ============
    def test_single_category_perfect_match(self, classifier):
        """Test when only one category matches strongly."""
        # 3+ KIND patterns: persoon, organisatie, document
        result = classifier.classify(
            "rechtspersoon",
            "Een natuurlijk persoon of organisatie met rechtspersoonlijkheid volgens document"
        )

        assert result.primary_category == UFOCategory.KIND
        assert result.confidence >= 0.9  # High confidence expected
        assert len(result.secondary_categories) == 0  # No secondary

    # ============ EDGE CASE 3: ALL SCORES EQUAL ============
    def test_completely_ambiguous_term(self, classifier):
        """Test term that matches all categories equally."""
        # Term designed to hit multiple categories
        result = classifier.classify(
            "status",
            "Een toestand waarbij een persoon een rol heeft in een procedure met verplichtingen"
            # persoon=KIND, rol=ROLE, procedure=EVENT, verplichtingen=MODE, toestand=PHASE
        )

        # Should be low confidence due to ambiguity
        assert result.confidence <= 0.5
        assert len(result.secondary_categories) >= 2

        # Check for determinism: same input = same output
        result2 = classifier.classify("status", result.definition)
        assert result.primary_category == result2.primary_category

    # ============ EDGE CASE 4: NEGATIVE SCORES (IMPOSSIBLE?) ============
    def test_no_negative_scores_possible(self, classifier):
        """Verify negative scores cannot occur."""
        # Try to trigger edge cases
        test_cases = [
            ("", ""),  # Will raise ValueError
            ("x", "y"),  # No matches
            ("test" * 1000, "test" * 1000),  # Repetition
        ]

        for term, definition in test_cases:
            try:
                result = classifier.classify(term, definition)
                # If successful, confidence should be non-negative
                assert result.confidence >= 0.0
            except ValueError:
                pass  # Expected for empty input

    # ============ EDGE CASE 5: SCORES > 1.0 (IMPOSSIBLE?) ============
    def test_confidence_never_exceeds_one(self, classifier):
        """Verify confidence is always <= 1.0."""
        # Try to trigger score inflation
        test_cases = [
            # Term with many keywords from same category
            ("rechtspersoon", "Een natuurlijk persoon is een mens die als persoon optreedt volgens persoonlijke gegevens"),
            # Disambiguation + high score
            ("zaak", "Een rechtszaak is een procedure met behandeling in rechtzaak"),
            # Multiple categories matching
            ("contract", "Een overeenkomst is een relatie tussen partijen als personen"),
        ]

        for term, definition in test_cases:
            result = classifier.classify(term, definition)
            assert 0.0 <= result.confidence <= 1.0, \
                f"Confidence {result.confidence} out of bounds for '{term}'"

    # ============ EDGE CASE 6: EMPTY CONTEXT ============
    def test_empty_definition_after_normalization(self, classifier):
        """Test when definition becomes empty after normalization."""
        # Only whitespace and control chars
        with pytest.raises(ValueError):
            classifier.classify("test", "   \t\n\r   ")

    # ============ EDGE CASE 7: EXTREMELY LONG TEXT ============
    def test_very_long_input_performance(self, classifier):
        """Test performance doesn't degrade on long input."""
        import time

        long_def = "juridisch begrip " * 1000  # 17k chars

        start = time.perf_counter()
        result = classifier.classify("test", long_def)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Should complete in reasonable time
        assert elapsed_ms < 500, f"Classification took {elapsed_ms}ms"
        assert len(result.definition) == 10000  # Truncated

    # ============ EDGE CASE 8: UNICODE EDGE CASES ============
    def test_zero_width_characters(self, classifier):
        """Test handling of invisible Unicode characters."""
        # Zero-width space, BOM, etc.
        term_with_zwsp = "test\u200b\u200c\u200d\ufeff"

        result = classifier.classify(term_with_zwsp, "definitie")

        # Should be normalized away
        assert "\u200b" not in result.term
        assert "\ufeff" not in result.term
        assert result.term == "test"  # Clean

    def test_emoji_in_text(self, classifier):
        """Test handling of emoji and special symbols."""
        result = classifier.classify(
            "🏛️ rechtbank",
            "De rechtbank ⚖️ is een juridische instantie"
        )

        # Should classify based on text, not emoji
        assert result.primary_category == UFOCategory.KIND
        assert result.confidence > 0.5

    def test_mixed_scripts(self, classifier):
        """Test handling of mixed writing systems."""
        result = classifier.classify(
            "test Α 中 א",  # Latin, Greek, Chinese, Hebrew
            "een begrip met mixed scripts"
        )

        assert result is not None
        assert result.primary_category in UFOCategory

    # ============ SECURITY EDGE CASES ============
    def test_regex_dos_protection(self, classifier):
        """Test protection against ReDoS attacks."""
        import signal

        # Pathological input for regex
        evil_input = "a" * 10000 + "!"

        # Should complete without hanging
        def timeout_handler(signum, frame):
            raise TimeoutError("Regex took too long")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(2)  # 2 second timeout

        try:
            result = classifier.classify(evil_input, evil_input)
            signal.alarm(0)  # Cancel
            assert result is not None
        except TimeoutError:
            pytest.fail("Classification timed out - possible ReDoS vulnerability")
        finally:
            signal.alarm(0)

    def test_sql_injection_safety(self, classifier):
        """Test SQL injection attempts are handled safely."""
        dangerous = "'; DROP TABLE definities; --"

        result = classifier.classify(dangerous, "test definition")

        # Should classify safely without executing anything
        assert result is not None
        assert dangerous in result.term  # Preserved as-is

    # ============ DISAMBIGUATION EDGE CASES ============
    def test_disambiguation_multiple_matches(self, classifier):
        """Test when multiple disambiguation patterns match."""
        result = classifier.classify(
            "zaak",
            "Een rechtszaak is een dossier met een nummer voor registratie van eigendom"
            # Matches: rechts (EVENT), dossier (KIND), eigendom (RELATOR)
        )

        # Should handle gracefully, pick most appropriate
        assert result.primary_category in [UFOCategory.EVENT, UFOCategory.KIND, UFOCategory.RELATOR]
        # Confidence should reflect ambiguity
        assert result.confidence < 0.8

    def test_disambiguation_tie_breaking_determinism(self, classifier):
        """Test disambiguation is deterministic."""
        term = "eigendom"
        definition = "Het verkrijgen van eigendom door overdracht van een goed"
        # Matches: verkrijg (EVENT), eigendom (RELATOR), goed (KIND)

        # Run 10 times
        results = [classifier.classify(term, definition) for _ in range(10)]

        # All results should be identical
        categories = [r.primary_category for r in results]
        assert len(set(categories)) == 1, "Non-deterministic disambiguation"

    # ============ CONFIDENCE CALCULATION EDGE CASES ============
    def test_confidence_calibration_low_scores(self, classifier):
        """Test confidence is reasonable for low pattern matches."""
        # Single weak match
        result = classifier.classify("test", "een persoon")  # Only 1 KIND pattern

        # Confidence should reflect single pattern
        assert 0.2 <= result.confidence <= 0.5, \
            f"Confidence {result.confidence} not calibrated for single pattern"

    def test_confidence_with_high_ambiguity(self, classifier):
        """Test confidence is reduced for ambiguous cases."""
        # Multiple categories with close scores
        result = classifier.classify(
            "handeling",
            "Een handeling is een procedure die personen uitvoeren met verplichtingen"
            # procedure=EVENT, personen=KIND, verplichtingen=MODE, handeling=EVENT
        )

        # High ambiguity should reduce confidence
        assert result.confidence < 0.7
        assert len(result.secondary_categories) >= 1
```

---

## 7. AANBEVELINGEN & PRIORITEITEN 📋

### Hoge Prioriteit (Fix Onmiddellijk)

1. **BUG-1: Input Validatie** - KRITIEK
   - Tests falen zonder dit
   - Contract breach
   - Geschatte tijd: 1 uur

2. **BUG-2: None Guards** - KRITIEK
   - Silent failures
   - Geschatte tijd: 30 min

3. **EDGE-8: Unicode Normalization** - HOOG
   - Data quality issue
   - Geschatte tijd: 2 uur

### Medium Prioriteit (Deze Sprint)

4. **BUG-3: Score Calculation Guards** - MEDIUM
   - Rare maar mogelijk
   - Geschatte tijd: 2 uur

5. **EDGE-3: Tie-Breaking Determinisme** - MEDIUM
   - Non-determinisme is slecht voor tests
   - Geschatte tijd: 2 uur

6. **Confidence Formula Verbetering** - MEDIUM
   - Betere gebruikerservaring
   - Geschatte tijd: 4 uur

### Lage Prioriteit (Volgende Sprint)

7. **BUG-4: Regex Performance** - LOW
   - Alleen bij extreme input
   - Geschatte tijd: 3 uur

8. **Policy Drempels Review** - LOW
   - Optimization, niet bug
   - Geschatte tijd: 2 uur

9. **Disambiguation Verbetering** - LOW
   - Nice to have
   - Geschatte tijd: 3 uur

### Totale Geschatte Effort

- **Hoge prioriteit**: 3.5 uur
- **Medium prioriteit**: 10 uur
- **Lage prioriteit**: 8 uur
- **Totaal**: ~22 uur (3 dagen dev time)

---

## 8. CONCLUSIE

De UFO Classifier heeft een **solide basis** maar mist **kritieke input validatie** en heeft **edge case vulnerabilities**. De belangrijkste risico's zijn:

1. **Test Failures** - Huidige code matcht niet test expectations
2. **Non-Determinisme** - Tie-breaking is arbitrair
3. **Silent Failures** - Geen exceptions bij invalid input
4. **Unicode Issues** - Incomplete normalization
5. **Misleading Confidence** - Formule is te simpel

**Prioritize**: Fix BUG-1 en BUG-2 eerst, dan work through edge cases.

---

**End of Analysis**
