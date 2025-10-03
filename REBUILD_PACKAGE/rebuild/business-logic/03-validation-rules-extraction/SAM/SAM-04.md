# SAM-04: Begrip-samenstelling strijdt niet met samenstellende begrippen

## Metadata
- **ID:** SAM-04
- **Category:** SAM
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/SAM-04.py`
- **Class Name:** `SAM04Validator`
- **Lines of Code:** 124

## Business Purpose

### What
De betekenis van een samengesteld begrip mag niet in strijd zijn met de betekenissen van de samenstellende begrippen; de samenstelling leidt tot een specialisatie van één van de delen.

### Why
Een samenstelling (bijv. 'procesmodel') is altijd een specialisatie van één van de componenten (hier: 'model'). De definitie moet beginnen met dat component (genus) en daarna specificeren. Conflict ontstaat als je een ander begrip als genus gebruikt.

### When Applied
Applied to: samengestelde begrippen
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from SAM04Validator)
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
*No specific patterns defined*

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
1. "procesmodel: model van een proces"
2. "procesmodel: schematisch model van een proces"

### Bad Examples (Should FAIL)
1. "procesmodel: weergave, meestal als diagram, van een proces"

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
- **Guideline:** Begrip-samenstelling strijdt niet met samenstellende begrippen
- **URL:** [https://www.astraonline.nl/index.php/Begrip-samenstelling_strijdt_niet_met_samenstellende_begrippen](https://www.astraonline.nl/index.php/Begrip-samenstelling_strijdt_niet_met_samenstellende_begrippen)

**Compliance requirement:** verplicht

## Notes
- **Type:** samenhang tussen termen/definities
- **Theme:** samenhang binnen domein
- **Test Question:** Begint de definitie met het onderdeel dat de specialisatie vormt van de samenstelling?

## Extraction Date
2025-10-02
