# VER-01: Term in enkelvoud

## Metadata
- **ID:** VER-01
- **Category:** VER
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/VER-01.py`
- **Class Name:** `VER01Validator`
- **Lines of Code:** 112

## Business Purpose

### What
De te definiëren term moet in het enkelvoud staan, tenzij deze alleen in het meervoud bestaat.

### Why
Gebruik het enkelvoud als lemma. Sommige woorden – zoals 'kosten', 'hersenen' – zijn 'plurale tantum' en mogen als uitzondering in meervoud blijven.

### When Applied
Applied to: lemma/term
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from VER01Validator)
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
    r"\b(\w+en)\b",
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
1. "gegeven"
2. "voertuig"

### Bad Examples (Should FAIL)
1. "gegevens"
2. "voertuigen"

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
- **Guideline:** Term in enkelvoud
- **URL:** [https://www.astraonline.nl/index.php/Term_in_enkelvoud](https://www.astraonline.nl/index.php/Term_in_enkelvoud)

**Compliance requirement:** verplicht

## Notes
- **Type:** term
- **Theme:** verschijningsvorm
- **Test Question:** Is de term in het enkelvoud (of een erkende plurale-tantum)?

## Extraction Date
2025-10-02
