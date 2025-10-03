# ARAI-02SUB1: Lexicale containerbegrippen vermijden

## Metadata
- **ID:** ARAI-02SUB1
- **Category:** ARAI
- **Priority:** midden
- **Status:** conceptueel
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/ARAI-02SUB1.py`
- **Class Name:** `ARAI02SUB1Validator`
- **Lines of Code:** 132

## Business Purpose

### What
Vermijd algemene termen als 'aspect', 'ding', 'iets' of 'element' in definities.

### Why
Dergelijke termen zijn te vaag en voegen onvoldoende betekenis toe. Een goede definitie gebruikt specifieke en informatieve termen.

### When Applied
Applied to: gehele definitie
Recommendation: optioneel

## Implementation

### Algorithm
```python
# Validation Logic (from ARAI02SUB1Validator)
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
    r"\baspect\b",
    r"\bding\b",
    r"\biets\b",
    r"\belement\b",
    r"\bfactor\b",
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
1. "maatregel die gericht is op risicobeheersing"
2. "gegeven dat betrekking heeft op de identiteit van een persoon"

### Bad Examples (Should FAIL)
1. "iets dat helpt bij het beheersen van risico’s"
2. "element dat informatie bevat"

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
- **Source:** Subsidieregel van ARAI02

**Compliance requirement:** optioneel

## Notes
- **Type:** inhoud
- **Theme:** begripszuiverheid
- **Test Question:** Bevat de definitie algemene containertermen die geen concrete of specifieke betekenis toevoegen?

## Extraction Date
2025-10-02
