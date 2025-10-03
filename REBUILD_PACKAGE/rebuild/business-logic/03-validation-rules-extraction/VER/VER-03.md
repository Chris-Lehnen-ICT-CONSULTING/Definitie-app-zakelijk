# VER-03: Werkwoord-term in infinitief

## Metadata
- **ID:** VER-03
- **Category:** VER
- **Priority:** midden
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/VER-03.py`
- **Class Name:** `VER03Validator`
- **Lines of Code:** 118

## Business Purpose

### What
Een werkwoord als term moet in de onbepaalde wijs (infinitief) staan.

### Why
Alleen de infinitief wordt als term opgenomen; vervoegde vormen zijn niet gewenst.

### When Applied
Applied to: term
Recommendation: aanbevolen

## Implementation

### Algorithm
```python
# Validation Logic (from VER03Validator)
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
    r".+t\b",
    r".+d\b",
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
1. "beoordelen"
2. "toezicht houden"

### Bad Examples (Should FAIL)
1. "beoordeelt"
2. "houdt toezicht"

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
- **Guideline:** Werkwoord-term in infinitief
- **URL:** [https://www.astraonline.nl/index.php/Werkwoord-term_in_infinitief](https://www.astraonline.nl/index.php/Werkwoord-term_in_infinitief)

**Compliance requirement:** aanbevolen

## Notes
- **Type:** samenhang tussen termen
- **Theme:** verschijningsvorm van de term
- **Test Question:** Staat de term in de infinitief en niet als vervoegd werkwoord?

## Extraction Date
2025-10-02
