# ARAI-01: geen werkwoord als kern (afgeleid)

## Metadata
- **ID:** ARAI-01
- **Category:** ARAI
- **Priority:** midden
- **Status:** conceptueel
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/ARAI-01.py`
- **Class Name:** `ARAI01Validator`
- **Lines of Code:** 131

## Business Purpose

### What
De kern van de definitie mag geen werkwoord zijn, om verwarring tussen handelingen en concepten te voorkomen.

### Why
Een definitie moet beschrijven wat iets is, niet wat het doet. Werkwoorden als kern kunnen leiden tot onduidelijkheid over de aard van het begrip. Deze regel is afgeleid van de ASTRA-aanbeveling 'Definitie ≠ beschrijving van gedrag'.

### When Applied
Applied to: alle
Recommendation: optioneel

## Implementation

### Algorithm
```python
# Validation Logic (from ARAI01Validator)
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
    r"\b(is|zijn|doet|kan|heeft|hebben|wordt|vormt|creëert)\b",
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
1. "proces dat beslissers identificeert"
2. "instelling die zorg verleent"

### Bad Examples (Should FAIL)
1. "Een systeem dat registreert..."
2. "Een functie die uitvoert..."

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
- **Guideline:** Definitie ≠ beschrijving van gedrag
- **URL:** [https://www.astraonline.nl/index.php/Definitie_≠_beschrijving_van_gedrag](https://www.astraonline.nl/index.php/Definitie_≠_beschrijving_van_gedrag)

**Compliance requirement:** optioneel

## Notes
- **Type:** gehele definitie
- **Theme:** interne logica en leesbaarheid
- **Test Question:** Is de kern van de definitie een zelfstandig naamwoord (en geen werkwoord)?

## Extraction Date
2025-10-02
