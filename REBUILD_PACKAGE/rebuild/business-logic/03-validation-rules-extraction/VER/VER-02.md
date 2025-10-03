# VER-02: Definitie in enkelvoud

## Metadata
- **ID:** VER-02
- **Category:** VER
- **Priority:** midden
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/VER-02.py`
- **Class Name:** `VER02Validator`
- **Lines of Code:** 138

## Business Purpose

### What
De definitie is geformuleerd in het enkelvoud.

### Why
Net als de term, moet ook de definitie zoveel mogelijk in het enkelvoud geformuleerd worden. Dit verhoogt de helderheid, precisie en logische consistentie van definities. Uitzonderingen zijn mogelijk, maar slechts bij gemotiveerde noodzaak.

### When Applied
Applied to: gehele definitie
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from VER02Validator)
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
    r"\bgegevens zijn\b",
    r"\bmaatregelen zijn\b",
    r"\bvoertuigen zijn\b",
    r"\bsystemen zijn\b",
    r"\bactiviteiten zijn\b",
    r"\b\w+en zijn\b",
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
1. "gegeven: feitelijke eenheid van informatie die kan worden vastgelegd"
2. "maatregel: actie die is genomen om een doel te bereiken"
3. "natuurlijke persoon die wordt vertegenwoordigd"

### Bad Examples (Should FAIL)
1. "gegevens zijn feiten en getallen die zijn verzameld voor analyse"
2. "maatregelen zijn acties die genomen worden om een doel te bereiken"

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
- **Guideline:** Definitie in enkelvoud
- **URL:** [https://www.astraonline.nl/index.php/Definitie_in_enkelvoud](https://www.astraonline.nl/index.php/Definitie_in_enkelvoud)

**Compliance requirement:** verplicht

## Notes
- **Type:** formulering
- **Theme:** verwoording van de definitie
- **Test Question:** Is de formulering van de definitie in het enkelvoud?

## Extraction Date
2025-10-02
