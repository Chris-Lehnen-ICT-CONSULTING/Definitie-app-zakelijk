# STR-04: Kick-off vervolgen met toespitsing

## Metadata
- **ID:** STR-04
- **Category:** STR
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/STR-04.py`
- **Class Name:** `STR04Validator`
- **Lines of Code:** 129

## Business Purpose

### What
Een definitie moet na de algemene opening meteen toespitsen op het specifieke begrip.

### Why
De 'kick-off' (bijv. 'proces', 'activiteit', 'gegeven') moet onmiddellijk gevolgd worden door een toespitsing die uitlegt welk soort proces of activiteit bedoeld wordt. Te algemene definities zonder verdere specificatie zijn ontoereikend.

### When Applied
Applied to: alle
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from STR04Validator)
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
    r"^\s*(proces|gegeven|activiteit|maatregel|functie|instantie|persoon)\s*(\.|$)",
    r"^\s*(proces|gegeven|activiteit|maatregel|functie|instantie|persoon)\s+die\s*$",
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
1. "proces dat beslissers informeert"
2. "gegeven over de verblijfplaats van een betrokkene"

### Bad Examples (Should FAIL)
1. "proces"
2. "gegeven"
3. "activiteit die plaatsvindt"

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
- **Guideline:** Kick-off vervolgen met toespitsing
- **URL:** [https://www.astraonline.nl/index.php/Kick-off_vervolgen_met_toespitsing](https://www.astraonline.nl/index.php/Kick-off_vervolgen_met_toespitsing)

**Compliance requirement:** verplicht

## Notes
- **Type:** gehele definitie
- **Theme:** structuur van de definitie
- **Test Question:** Volgt na de algemene opening direct een toespitsing die uitlegt welk soort proces of element bedoeld wordt?

## Extraction Date
2025-10-02
