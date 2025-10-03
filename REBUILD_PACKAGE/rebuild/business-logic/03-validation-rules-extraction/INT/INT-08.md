# INT-08: Positieve formulering

## Metadata
- **ID:** INT-08
- **Category:** INT
- **Priority:** midden
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/INT-08.py`
- **Class Name:** `INT08Validator`
- **Lines of Code:** 173

## Business Purpose

### What
Een definitie wordt in principe positief geformuleerd, dus zonder ontkenningen te gebruiken; uitzondering voor onderdelen die de definitie specifieker maken (bijv. relatieve bijzinnen).

### Why
Negatieve formuleringen kunnen verwarrend zijn of leiden tot onduidelijkheid. Een definitie moet helder en direct aangeven wat iets *wel* is, in plaats van wat het *niet* is. Elementen die een definitie specifieker maken, bijvoorbeeld via een relatieve bijzin, mogen wél in ontkennende vorm worden geformuleerd.

### When Applied
Applied to: gehele definitie
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from INT08Validator)
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
    r"\bniet\b",
    r"\bgeen\b",
    r"\bzonder\b",
    r"\buitgezonderd\b",
    r"\bniet geschikt voor\b",
    r"\bmag niet\b",
    r"\bvermijdt\b",
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
1. "bevoegd persoon: medewerker met formele autorisatie om gegevens in te zien"
2. "gevangene: persoon die zich niet vrij kan bewegen"

### Bad Examples (Should FAIL)
1. "bevoegd persoon: iemand die niet onbevoegd is"
2. "toegang: mogelijkheid om een ruimte te betreden, uitgezonderd voor onbevoegden"

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
- **Guideline:** Positieve formulering
- **URL:** [https://www.astraonline.nl/index.php/Positieve_formulering](https://www.astraonline.nl/index.php/Positieve_formulering)

**Compliance requirement:** verplicht

## Notes
- **Type:** formulering
- **Theme:** interne kwaliteit van de definitie
- **Test Question:** Is de definitie in principe positief geformuleerd en vermijdt deze negatieve formuleringen, behalve om specifieke onderdelen te verduidelijken?

## Extraction Date
2025-10-02
