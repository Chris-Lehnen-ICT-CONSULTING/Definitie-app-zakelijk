# SAM-06: Één synoniem krijgt voorkeur

## Metadata
- **ID:** SAM-06
- **Category:** SAM
- **Priority:** midden
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/SAM-06.py`
- **Class Name:** `SAM06Validator`
- **Lines of Code:** 134

## Business Purpose

### What
Kies per begrip één voorkeurs-term (lemma).

### Why
Business rationale not explicitly documented.

### When Applied
Applied to: termniveau
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from SAM06Validator)
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
*No good examples provided*

### Bad Examples (Should FAIL)
*No bad examples provided*

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
- **Guideline:** Één synoniem krijgt voorkeur
- **URL:** [https://www.astraonline.nl/index.php/Één_synoniem_krijgt_voorkeur](https://www.astraonline.nl/index.php/Één_synoniem_krijgt_voorkeur)

**Compliance requirement:** verplicht

## Notes
- **Type:** samenhang van termen
- **Theme:** begripsafbakening
- **Test Question:** Heeft de gebruiker een voorkeurs-term geselecteerd?

## Extraction Date
2025-10-02
