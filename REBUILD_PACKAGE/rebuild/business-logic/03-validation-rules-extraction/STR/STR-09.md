# STR-09: Dubbelzinnige 'of' is verboden

## Metadata
- **ID:** STR-09
- **Category:** STR
- **Priority:** midden
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/STR-09.py`
- **Class Name:** `STR09Validator`
- **Lines of Code:** 146

## Business Purpose

### What
Een definitie bevat geen 'of' die onduidelijk maakt of beide mogelijkheden gelden of slechts één van de twee.

### Why
Het gebruik van 'of' kan leiden tot verwarring als niet duidelijk is of beide alternatieven toegestaan zijn (inclusief of) of slechts één (exclusief of). In definities moet dit expliciet zijn.

### When Applied
Applied to: alle
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from STR09Validator)
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
    r"\bof\b",
    r"\b(paspoort|identiteitskaart)\b.*\bof\b.*\b(paspoort|identiteitskaart)\b",
    r"\bofwel\b",
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
1. "Een persoon met een paspoort of, indien niet beschikbaar, een identiteitskaart"

### Bad Examples (Should FAIL)
1. "Een persoon met een paspoort of identiteitskaart"
2. "Een verdachte is iemand die een misdrijf beraamt of uitvoert"

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
- **Guideline:** Dubbelzinnige 'of' is verboden
- **URL:** [https://www.astraonline.nl/index.php/Dubbelzinnige_'of'_is_verboden](https://www.astraonline.nl/index.php/Dubbelzinnige_'of'_is_verboden)

**Compliance requirement:** verplicht

## Notes
- **Type:** gehele definitie
- **Theme:** structuur van de definitie
- **Test Question:** Is het gebruik van 'of' in de definitie ondubbelzinnig? Is het duidelijk of het gaat om een inclusieve of exclusieve keuze?

## Extraction Date
2025-10-02
