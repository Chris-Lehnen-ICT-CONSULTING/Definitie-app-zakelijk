# INT-04: Lidwoord-verwijzing duidelijk

## Metadata
- **ID:** INT-04
- **Category:** INT
- **Priority:** midden
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/INT-04.py`
- **Class Name:** `INT04Validator`
- **Lines of Code:** 146

## Business Purpose

### What
Definities mogen geen onduidelijke verwijzingen met de lidwoorden 'de' of 'het' bevatten.

### Why
Wanneer een bepaald lidwoord wordt gebruikt, impliceert dat dat er verwezen wordt naar iets specifieks. Zorg dat in dezelfde zin duidelijk is naar welk concreet object of begrip met “de X” of “het Y” wordt verwezen, of vervang het door een X” of “een Y.”

### When Applied
Applied to: gehele definitie
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from INT04Validator)
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
    r"\bde\s+(instelling|maatregel|activiteit|persoon|functie|organisatie|toezichthouder)\b",
    r"\bhet\s+(proces|gegeven|systeem|document|resultaat|beleid|instrument)\b",
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
1. "Een instelling (de Raad voor de Rechtspraak) neemt beslissingen binnen het strafrechtelijk systeem."
2. "Het systeem (Reclasseringsapplicatie) voert controles automatisch uit."

### Bad Examples (Should FAIL)
1. "De instelling neemt beslissingen binnen het strafrechtelijk systeem."
2. "Het systeem voert controles uit zonder verdere specificatie."

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
- **Guideline:** Lidwoord-verwijzing duidelijk
- **URL:** [https://www.astraonline.nl/index.php/Lidwoord-verwijzing_duidelijk](https://www.astraonline.nl/index.php/Lidwoord-verwijzing_duidelijk)

**Compliance requirement:** verplicht

## Notes
- **Type:** interne structuur
- **Theme:** interne kwaliteit van de definitie
- **Test Question:** Bevat de definitie zinnen als 'de instelling', 'het systeem'? Zo ja: is in diezelfde zin expliciet benoemd welke instelling of welk systeem wordt bedoeld?

## Extraction Date
2025-10-02
