# INT-03: Voornaamwoord-verwijzing duidelijk

## Metadata
- **ID:** INT-03
- **Category:** INT
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/INT-03.py`
- **Class Name:** `INT03Validator`
- **Lines of Code:** 149

## Business Purpose

### What
Definities mogen geen voornaamwoorden bevatten waarvan niet direct duidelijk is waarnaar verwezen wordt.

### Why
Voornaamwoorden als 'deze', 'dit', 'die', 'daarvan' enzovoort verwijzen naar een antecedent. In een definitie moet altijd in dezelfde zin of zinsdeel staan welk zelfstandig naamwoord bedoeld is, zodat de definitie zelfstandig en eenduidig leesbaar blijft.

### When Applied
Applied to: gehele definitie
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from INT03Validator)
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
    r"\bdeze\b",
    r"\bdit\b",
    r"\bdie\b",
    r"\bdaarvan\b",
    r"\bdaarbij\b",
    r"\bwaarvan\b",
    r"\bwaarmee\b",
    r"\binzienelijk maken\b",
    r"\bwaarbij\b",
    r"\bin het kader\b",
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
1. "Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die de basis vormen waardoor die gebeurtenis volledig kan worden begrepen en geanalyseerd."
2. "Voorwaarde: bepaling die aangeeft onder welke omstandigheden een handeling is toegestaan."

### Bad Examples (Should FAIL)
1. "Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die de basis vormen waardoor het volledig kan worden begrepen en geanalyseerd."
2. "Voorwaarde: bepaling die aangeeft onder welke omstandigheden deze geldt."

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
- **Guideline:** Voornaamwoord-verwijzing duidelijk
- **URL:** [https://www.astraonline.nl/index.php/Voornaamwoord-verwijzing_duidelijk](https://www.astraonline.nl/index.php/Voornaamwoord-verwijzing_duidelijk)

**Compliance requirement:** verplicht

## Notes
- **Type:** interne structuur
- **Theme:** interne kwaliteit van de definitie
- **Test Question:** Bevat de definitie voornaamwoorden zoals 'deze', 'dit', 'die'? Zo ja: is voor de lezer direct helder waarnaar ze verwijzen?

## Extraction Date
2025-10-02
