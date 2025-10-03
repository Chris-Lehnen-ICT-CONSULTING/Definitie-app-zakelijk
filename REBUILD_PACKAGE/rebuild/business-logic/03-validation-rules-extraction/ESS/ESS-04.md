# ESS-04: Toetsbaarheid

## Metadata
- **ID:** ESS-04
- **Category:** ESS
- **Priority:** midden
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/ESS-04.py`
- **Class Name:** `ESS04Validator`
- **Lines of Code:** 156

## Business Purpose

### What
Een definitie bevat objectief toetsbare elementen (harde deadlines, aantallen, percentages, meetbare criteria).

### Why
Zonder toetsbare criteria kan een lezer niet objectief vaststellen of iets onder de definitie valt. Voorbeelden van *niet*-toetsbaar: ‘zo snel mogelijk’, ‘zo veel mogelijk’. Wél-toetsbaar: ‘binnen 3 dagen’, ‘tenminste 80%’, ‘uiterlijk na 1 week’.

### When Applied
Applied to: alle
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from ESS04Validator)
def validate(definitie: str, begrip: str, context: dict | None = None) -> tuple[bool, str, float]:
    # 1. Extract patterns from config
    # 2. Match patterns against definition
    # 3. Check good/bad examples
    # 4. Return (success, message, score)
    pass
```

**Key Steps:**
1. Load recognizable patterns from JSON config
2. Use regex matching to find violations
3. Compare with good/bad examples
4. Calculate score: 1.0 (pass), 0.5 (warning), 0.0 (fail)

### Patterns
```python
# Regex patterns used for detection
herkenbaar_patronen = [
    r"\bbinnen\s+\d+\s+dagen?\b",
    r"\buiterlijk\s+na\s+\d+\s+(dagen?|weken?)\b",
    r"\btenminste\s+\d+%\b",
    r"\bminimaal\s+\d+%\b",
    r"\bmaximaal\s+\d+%\b",
    r"\b\d+\s+%\b",
    r"\baan de hand van\b",
    r"\bobjectieve criteria\b",
    r"\bbevat\b",
    r"\bomvat\b",
    r"\bheeft als eigenschap\b",
    r"\bwordt gekenmerkt door\b",
    r"\bcontrole op\b",
    r"\bwaarneembare\b",
    r"\btoetsbaar\b",
]
```

### Thresholds
| Threshold | Value | Usage | Notes |
|-----------|-------|-------|-------|
| Pass score | 1.0 | Perfect validation | No violations found |
| Warning score | 0.5 | Partial pass | Minor issues detected |
| Fail score | 0.0 | Validation failed | Violations found |

### Error Messages
- **Pass:** "✔️ {rule_id}: [validation passed message]"
- **Warning:** "🟡 {rule_id}: [warning message with details]"
- **Fail:** "❌ {rule_id}: [failure message with found violations]"

## Test Cases

### Good Examples (Should PASS)
1. "…binnen 3 dagen nadat het verzoek is ingediend…"
2. "…tenminste 80% van de steekproef voldoet…"
3. "…uiterlijk na 1 week na ontvangst…"

### Bad Examples (Should FAIL)
1. "…zo snel mogelijk na ontvangst…"
2. "…zo veel mogelijk resultaten…"
3. "…moet zo mogelijk conform…"

### Edge Cases
- Empty definition
- Very short definition (< 10 characters)
- Very long definition (> 500 characters)
- Special characters and unicode
- Multiple pattern matches

## Dependencies
**Imports:**
- `logging`

**Called by:**
- ModularValidationService
- ValidationOrchestratorV2

## ASTRA References
- **Guideline:** Toetsbaarheid
- **URL:** [https://www.astraonline.nl/index.php/Toetsbaarheid](https://www.astraonline.nl/index.php/Toetsbaarheid)

**Compliance requirement:** verplicht

## Notes
- **Type:** element in de definitie
- **Theme:** toepasbaarheid
- **Test Question:** Bevat de definitie elementen waarmee je objectief kunt vaststellen of iets wel of niet onder het begrip valt?

## Extraction Date
2025-10-02
