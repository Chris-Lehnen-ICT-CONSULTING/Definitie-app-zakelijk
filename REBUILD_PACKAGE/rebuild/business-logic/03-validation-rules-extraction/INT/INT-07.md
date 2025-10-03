# INT-07: Alleen toegankelijke afkortingen

## Metadata
- **ID:** INT-07
- **Category:** INT
- **Priority:** midden
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/INT-07.py`
- **Class Name:** `INT07Validator`
- **Lines of Code:** 149

## Business Purpose

### What
In een definitie gebruikte afkortingen zijn voorzien van een voor de doelgroep direct toegankelijke referentie.

### Why
Het vermijden van onverklaarde afkortingen bevordert leesbaarheid. Elke afkorting moet in de definitie direct worden toegelicht(bijv. DJI (Dienst Justitiële Inrichtingen), OM (Openbaar Ministerie)), of worden aangeboden als hyperlink of Wiki-link.

### When Applied
Applied to: alle
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from INT07Validator)
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
    r"\b[A-Z]{2,6}\b",
    r"\bDJI\b",
    r"\bOM\b",
    r"\bICT\b",
    r"\bAVG\b",
    r"\bWpg\b",
    r"\bGGZ\b",
    r"\bNCTV\b",
    r"\bKvK\b",
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
1. "Dienst Justitiële Inrichtingen (DJI)"
2. "OM (Openbaar Ministerie)"
3. "AVG (Algemene verordening gegevensbescherming)"
4. "KvK (Kamer van Koophandel)"
5. "[[Algemene verordening gegevensbescherming]]"

### Bad Examples (Should FAIL)
1. "DJI voert toezicht uit."
2. "De AVG vereist naleving."
3. "OM is bevoegd tot vervolging."
4. "KvK registreert bedrijven."

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
- **Guideline:** Geen ontoegankelijke achtergrondkennis nodig
- **URL:** [https://www.astraonline.nl/index.php/Geen_ontoegankelijke_achtergrondkennis_nodig](https://www.astraonline.nl/index.php/Geen_ontoegankelijke_achtergrondkennis_nodig)

**Compliance requirement:** verplicht

## Notes
- **Type:** gehele definitie
- **Theme:** interne kwaliteit van de definitie
- **Test Question:** Bevat de definitie afkortingen? Zo ja: zijn deze in hetzelfde stuk tekst uitgelegd of gelinkt?

## Extraction Date
2025-10-02
