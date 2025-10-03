# CON-02: Baseren op authentieke bron

## Metadata
- **ID:** CON-02
- **Category:** CON
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/CON-02.py`
- **Class Name:** `CON02Validator`
- **Lines of Code:** 154

## Business Purpose

### What
Gebruik een gezaghebbende of officiële bron als basis voor de definitie.

### Why
Een definitie moet gebaseerd zijn op een erkende bron (bijv. wetgeving, officiële beleidsdocumenten, standaarden). Dit waarborgt de betrouwbaarheid en maakt discussie over interpretatie minder waarschijnlijk.

### When Applied
Applied to: alle
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from CON02Validator)
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
    r"\bvolgens (de|het)\b",
    r"\bzoals beschreven in\b",
    r"\bzoals bepaald in\b",
    r"\bzoals bedoeld in\b",
    r"\bconform (de|het)\b",
    r"\bovereenkomstig (de|het)\b",
    r"\bingevolge (de|het)\b",
    r"\bop grond van\b",
    r"\buit (de|het)?\s*(Wetboek|Besluit|Regeling|Beleidsregel|Standaard|Verordening|Richtlijn)\b",
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
1. "gegevensverwerking: iedere handeling met gegevens zoals bedoeld in de AVG"
2. "delict: gedraging die volgens het Wetboek van Strafrecht strafbaar is gesteld"

### Bad Examples (Should FAIL)
1. "gegevensverwerking: handeling met gegevens (geen bron vermeld)"
2. "delict: iets strafbaars (geen verwijzing naar wet)"

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
- **Guideline:** Baseren op authentieke bron
- **URL:** [https://www.astraonline.nl/index.php/Baseren_op_authentieke_bron](https://www.astraonline.nl/index.php/Baseren_op_authentieke_bron)

**Compliance requirement:** verplicht

## Notes
- **Type:** herkomst en bronvermelding
- **Theme:** context en legitimiteit
- **Test Question:** Is duidelijk op welke authentieke of officiële bron de definitie is gebaseerd?

## Extraction Date
2025-10-02
