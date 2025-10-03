# STR-05: Definitie ≠ constructie

## Metadata
- **ID:** STR-05
- **Category:** STR
- **Priority:** midden
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/STR-05.py`
- **Class Name:** `STR05Validator`
- **Lines of Code:** 128

## Business Purpose

### What
Een definitie moet aangeven wat iets is, niet uit welke onderdelen het bestaat.

### Why
Een definitie beschrijft de aard of functie van het begrip. Het is niet voldoende om alleen de samenstellende onderdelen of kenmerken op te sommen. Dat leidt tot verwarring over wat het begrip daadwerkelijk is.

### When Applied
Applied to: alle
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from STR05Validator)
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
    r"\bbestaat uit\b",
    r"\bsamengesteld uit\b",
    r"\bomvat\b",
    r"\bonderdelen zijn\b",
    r"\bcomponenten zijn\b",
    r"\bvormt een geheel van\b",
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
1. "motorvoertuig: gemotoriseerd voertuig dat niet over rails rijdt, zoals auto’s, vrachtwagens en bussen"

### Bad Examples (Should FAIL)
1. "motorvoertuig: een voertuig met een chassis, vier wielen en een motor van meer dan 50 cc"

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
- **Guideline:** Definitie ≠ constructie
- **URL:** [https://www.astraonline.nl/index.php/Definitie_≠_constructie](https://www.astraonline.nl/index.php/Definitie_≠_constructie)

**Compliance requirement:** verplicht

## Notes
- **Type:** gehele definitie
- **Theme:** structuur van de definitie
- **Test Question:** Geeft de definitie aan wat het begrip is, in plaats van alleen waar het uit bestaat?

## Extraction Date
2025-10-02
