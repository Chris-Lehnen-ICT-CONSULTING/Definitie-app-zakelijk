# SAM-05: Geen cirkeldefinities

## Metadata
- **ID:** SAM-05
- **Category:** SAM
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/SAM-05.py`
- **Class Name:** `SAM05Validator`
- **Lines of Code:** 127

## Business Purpose

### What
Een cirkeldefinitie (wederzijdse of meerdiepse verwijzing tussen begrippen) mag niet voorkomen.

### Why
Definities zijn circulair als begrip A in definitie B staat en begrip B in definitie A (diepte 2), of dieper (A→B→C→A). Dit leidt tot onbegrijpelijkheid.

### When Applied
Applied to: alle
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from SAM05Validator)
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
1. "object: fysiek ding dat bestaat in ruimte en tijd"
2. "entiteit: iets dat bestaat"

### Bad Examples (Should FAIL)
1. "object: een ding is een object"
2. "ding: een object is een ding"

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
- **Guideline:** Geen cirkeldefinities
- **URL:** [https://www.astraonline.nl/index.php/Géén_cirkeldefinities](https://www.astraonline.nl/index.php/Géén_cirkeldefinities)

**Compliance requirement:** verplicht

## Notes
- **Type:** samenhang tussen termen/definities
- **Theme:** begripszuiverheid
- **Test Question:** Treden er wederzijdse verwijzingen op tussen begrippen (cirkeldefinitie)?

## Extraction Date
2025-10-02
