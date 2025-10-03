# ARAI-02: Vermijd vage containerbegrippen

## Metadata
- **ID:** ARAI-02
- **Category:** ARAI
- **Priority:** midden
- **Status:** conceptueel
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/ARAI-02.py`
- **Class Name:** `ARAI02Validator`
- **Lines of Code:** 128

## Business Purpose

### What
De definitie mag geen containerbegrippen bevatten die op zichzelf weinig verklarende waarde hebben.

### Why
Containerbegrippen zoals 'aspect', 'element', 'activiteit', 'proces', of 'systeem' geven zonder verdere specificatie onvoldoende informatie. Ze moeten altijd gevolgd worden door een duidelijke concretisering of toespitsing om de definitie informatief en toetsbaar te maken.

### When Applied
Applied to: gehele definitie
Recommendation: optioneel

## Implementation

### Algorithm
```python
# Validation Logic (from ARAI02Validator)
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
    r"\bproces\b(?!\s+dat|\s+van)",
    r"\bactiviteit\b(?!\s+die|\s+van)",
    r"\bsysteem\b(?!\s+dat|\s+voor)",
    r"\baspect\b",
    r"\belement\b",
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
1. "proces dat gegevens verzamelt voor analyse"
2. "activiteit die gericht is op toezicht"

### Bad Examples (Should FAIL)
1. "proces ter ondersteuning"
2. "activiteit binnen het systeem"

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
- **Guideline:** Subsidieregel: ARAI02SUB1 – Lexicale containerbegrippen
- **URL:** [https://www.astraonline.nl/index.php/Essentie,_niet_doel](https://www.astraonline.nl/index.php/Essentie,_niet_doel)
- **Guideline:** Subsidieregel: ARAI02SUB2 – Ambtelijke containerbegrippen
- **URL:** [https://www.astraonline.nl/index.php/Kick-off_vervolgen_met_toespitsing](https://www.astraonline.nl/index.php/Kick-off_vervolgen_met_toespitsing)

**Compliance requirement:** optioneel

## Notes
- **Type:** interne logica en leesbaarheid
- **Theme:** begripsverheldering
- **Test Question:** Bevat de definitie containerbegrippen zonder verdere concretisering of specificatie?

## Extraction Date
2025-10-02
