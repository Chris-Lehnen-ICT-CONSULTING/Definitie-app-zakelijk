# INT-10: Geen ontoegankelijke achtergrondkennis nodig

## Metadata
- **ID:** INT-10
- **Category:** INT
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/INT-10.py`
- **Class Name:** `INT10Validator`
- **Lines of Code:** 149

## Business Purpose

### What
Een definitie moet begrijpelijk zijn zonder specialistische of niet-openbare kennis; uitzondering: zeer specifieke verwijzing naar openbare bron (bijv. wet met artikel).

### Why
Een goede definitie is zelfstandig begrijpelijk en mag niet verwijzen naar impliciete kennis in hoofden van mensen, interne procedures of niet-openbare documenten. Verwijzen naar een openbare bron (zoals een wet met specifiek artikel en hyperlink) is wel toegestaan mits eenduidig en volledig.

### When Applied
Applied to: gehele definitie
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from INT10Validator)
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
    r"\bzie\b",
    r"\bzoals gedefinieerd in\b",
    r"\bafgekort als\b",
    r"\bzoals bekend binnen\b",
    r"\bvolgens interne richtlijn\b",
    r"\binterne notitie\b",
    r"\bbekend binnen [A-Za-z]+\b",
    r"\bindien\b",
    r"benodigde bescheiden",
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
1. "instantie: organisatieonderdeel dat belast is met een bestuurlijke taak"
2. "… voldoet aan de criteria uit Wet politiegegevens art 13.1.d"

### Bad Examples (Should FAIL)
1. "instantie: zie definitie in het beleidsdocument X"
2. "gegevens: zoals bekend binnen de sector"
3. "… voldoen aan wettelijke voorwaarden …"
4. "… indien blijkt uit de aard van het strafbare feit …"
5. "… indien de maatschappelijke impact van het gedrag …"
6. "… benodigde bescheiden …"

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
- **Type:** begrijpelijkheid
- **Theme:** interne kwaliteit van de definitie
- **Test Question:** Is de definitie begrijpelijk zonder niet-openbare achtergrondkennis (behalve bij zeer specifieke bronvermelding)?

## Extraction Date
2025-10-02
