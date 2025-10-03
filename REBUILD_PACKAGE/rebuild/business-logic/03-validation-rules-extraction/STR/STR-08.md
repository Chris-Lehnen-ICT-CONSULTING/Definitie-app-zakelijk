# STR-08: Dubbelzinnige 'en' is verboden

## Metadata
- **ID:** STR-08
- **Category:** STR
- **Priority:** midden
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/STR-08.py`
- **Class Name:** `STR08Validator`
- **Lines of Code:** 149

## Business Purpose

### What
Een definitie bevat geen 'en' die onduidelijk maakt of beide kenmerken vereist zijn of slechts één van beide.

### Why
Wanneer 'en' wordt gebruikt in een opsomming van kenmerken of voorwaarden, moet duidelijk zijn of het om een cumulatieve eis (beide) of een alternatieve (één van beide) gaat. Onduidelijkheid kan leiden tot verkeerde interpretatie.

### When Applied
Applied to: alle
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from STR08Validator)
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
    r"\ben\b.+\b(of)?\b",
    r"\b(en)\s+.*\s+en\s+.*",
    r"\b(vereist.*en.*)\b",
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
1. "Toegang is beperkt tot personen met een geldig toegangspasje en een schriftelijke toestemming"

### Bad Examples (Should FAIL)
1. "Toegang is beperkt tot personen met een pasje en toestemming"
2. "Het systeem vereist login en verificatie"

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
- **Guideline:** Dubbelzinnige 'en' is verboden
- **URL:** [https://www.astraonline.nl/index.php/Dubbelzinnige_'en'_is_verboden](https://www.astraonline.nl/index.php/Dubbelzinnige_'en'_is_verboden)

**Compliance requirement:** verplicht

## Notes
- **Type:** gehele definitie
- **Theme:** structuur van de definitie
- **Test Question:** Is het gebruik van 'en' in de definitie ondubbelzinnig? Is het duidelijk of beide elementen vereist zijn of slechts één?

## Extraction Date
2025-10-02
