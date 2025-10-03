# ESS-05: Voldoende onderscheidend

## Metadata
- **ID:** ESS-05
- **Category:** ESS
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/ESS-05.py`
- **Class Name:** `ESS05Validator`
- **Lines of Code:** 157

## Business Purpose

### What
Een definitie moet duidelijk maken wat het begrip uniek maakt ten opzichte van andere verwante begrippen.

### Why
De definitie moet aangeven waarin het begrip zich onderscheidt van andere begrippen binnen hetzelfde domein, bijvoorbeeld via een expliciete tegenstelling, verschil- of unieke kenmerken. Zonder dit onderscheid zijn definities verwarrend en overlappend.

### When Applied
Applied to: alle
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from ESS05Validator)
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
    r"\bonderscheidt zich door\b",
    r"\bspecifiek voor\b",
    r"\bin tegenstelling tot\b",
    r"\bverschilt van\b",
    r"\bonderscheidend kenmerk\b",
    r"\bonderscheidend vermogen\b",
    r"\bonderscheiden door\b",
    r"\buniek ten opzichte van\b",
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
1. "Reclasseringstoezicht: toezicht gericht op gedragsverandering, in tegenstelling tot detentietoezicht dat gericht is op vrijheidsbeneming."
2. "Een onttrekking is een incident waarbij een jeugdige zonder toestemming één van de volgende voorzieningen verlaat: open justitiële inrichting of gesloten inrichtingsgebied."
3. "Auto: vierwielig motorvoertuig met uniek chassisnummer en kenteken, waardoor elke auto individueel wordt geïdentificeerd."

### Bad Examples (Should FAIL)
1. "Toezicht: het houden van toezicht op iemand."
2. "Een onttrekking is een incident waarbij een jeugdige zonder toestemming de inrichting verlaat."

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
- **Guideline:** Voldoende onderscheidend
- **URL:** [https://www.astraonline.nl/index.php/Voldoende_onderscheidend](https://www.astraonline.nl/index.php/Voldoende_onderscheidend)

**Compliance requirement:** verplicht

## Notes
- **Type:** essentie
- **Theme:** onderscheidend vermogen
- **Test Question:** Maakt de definitie expliciet duidelijk waarin het begrip zich onderscheidt van andere begrippen?

## Extraction Date
2025-10-02
