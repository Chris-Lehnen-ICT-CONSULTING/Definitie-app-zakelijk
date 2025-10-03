# STR-07: Geen dubbele ontkenning

## Metadata
- **ID:** STR-07
- **Category:** STR
- **Priority:** midden
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/STR-07.py`
- **Class Name:** `STR07Validator`
- **Lines of Code:** 125

## Business Purpose

### What
Een definitie bevat geen dubbele ontkenning.

### Why
Dubbele ontkenningen zijn verwarrend en vermoeilijken het begrijpen van een definitie. Formuleringen zoals 'niet zonder' of 'onmogelijk om niet te' zorgen voor ambiguïteit.

### When Applied
Applied to: alle
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from STR07Validator)
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
    r"niet\s+zonder",
    r"onmogelijk\s+om\s+niet",
    r"niet\s+onmogelijk",
    r"zonder\s+geen",
]
```

### Thresholds
| Threshold | Value | Usage | Notes |
|-----------|-------|-------|-------|
| Pass score | 1.0 | Perfect validation | No violations found |
| Warning score | 0.5 | Partial pass | Minor issues detected |
| Fail score | 0.0 | Validation failed | Violations found |
| Extracted value | 0.5 | Used in implementation | See Python code |
| Extracted value | 1.0 | Used in implementation | See Python code |

### Error Messages
- **Pass:** "✔️ {rule_id}: [validation passed message]"
- **Warning:** "🟡 {rule_id}: [warning message with details]"
- **Fail:** "❌ {rule_id}: [failure message with found violations]"

## Test Cases

### Good Examples (Should PASS)
1. "Beveiliging: maatregelen die toegang beperken tot bevoegde personen"

### Bad Examples (Should FAIL)
1. "Beveiliging: maatregelen die het niet onmogelijk maken om geen toegang te verkrijgen"

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
- **Guideline:** Geen dubbele ontkenning
- **URL:** [https://www.astraonline.nl/index.php/Geen_dubbele_ontkenning](https://www.astraonline.nl/index.php/Geen_dubbele_ontkenning)

**Compliance requirement:** verplicht

## Notes
- **Type:** gehele definitie
- **Theme:** structuur van de definitie
- **Test Question:** Bevat de definitie een dubbele ontkenning die de begrijpelijkheid schaadt?

## Extraction Date
2025-10-02
