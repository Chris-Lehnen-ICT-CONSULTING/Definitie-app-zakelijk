# ARAI-06: Correcte definitiestart: geen lidwoord, geen koppelwerkwoord, geen herhaling begrip

## Metadata
- **ID:** ARAI-06
- **Category:** ARAI
- **Priority:** hoog
- **Status:** conceptueel
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/ARAI-06.py`
- **Class Name:** `ARAI06Validator`
- **Lines of Code:** 143

## Business Purpose

### What
De definitie mag niet beginnen met een lidwoord, geen koppelwerkwoord bevatten aan het begin en het begrip mag niet herhaald worden in de definitie.

### Why
Een goede definitie start direct met de kern: een zelfstandig naamwoord of naamwoordgroep. Formuleringen die beginnen met 'De ... is ...' of 'Het begrip betekent ...' zijn niet geschikt voor hergebruik en leiden tot cirkeldefinities. Deze toetsregel voorkomt verwarring over de structuur van de definitie en bundelt drie veelvoorkomende fouten.

### When Applied
Applied to: gehele definitie
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from ARAI06Validator)
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
    r"^\s*(de|het|een)\s+",
    r"^\s*(is|omvat|betekent)\s+",
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
1. "proces waarbij toezicht plaatsvindt op naleving van wetgeving."
2. "maatregel die wordt ingezet bij overtredingen van regels."

### Bad Examples (Should FAIL)
1. "De maatregel is bedoeld voor naleving."
2. "Het begrip betekent: een controlemechanisme."
3. "Registratie is een registratie van gegevens."

### Edge Cases
- Empty definition
- Very short definition (< 10 characters)
- Very long definition (> 500 characters)
- Special characters and unicode
- Multiple pattern matches

## Dependencies
**Imports:**
- `logging`
- `config.verboden_woorden`

**Called by:**
- ModularValidationService
- ValidationOrchestratorV2

## ASTRA References
- **Guideline:** Start met zelfstandig naamwoord (STR-01)
- **URL:** [https://www.astraonline.nl/index.php/Structuur_van_definities](https://www.astraonline.nl/index.php/Structuur_van_definities)
- **Guideline:** Kick-off ≠ de term (STR-02)
- **URL:** [https://www.astraonline.nl/index.php/Kick-off_vervolgen_met_toespitsing](https://www.astraonline.nl/index.php/Kick-off_vervolgen_met_toespitsing)
- **Guideline:** Geen cirkeldefinities (SAM-05)
- **URL:** [https://www.astraonline.nl/index.php/Géén_cirkeldefinities](https://www.astraonline.nl/index.php/Géén_cirkeldefinities)

**Compliance requirement:** verplicht

## Notes
- **Type:** formulering
- **Theme:** interne structuur en helderheid
- **Test Question:** Begint de definitie correct zonder lidwoord, zonder koppelwerkwoord en zonder herhaling van het begrip?

## Extraction Date
2025-10-02
