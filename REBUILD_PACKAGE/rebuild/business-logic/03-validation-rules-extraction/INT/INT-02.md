# INT-02: Geen beslisregel

## Metadata
- **ID:** INT-02
- **Category:** INT
- **Priority:** midden
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/INT-02.py`
- **Class Name:** `INT02Validator`
- **Lines of Code:** 137

## Business Purpose

### What
Een definitie bevat geen beslisregels of voorwaarden.

### Why
Een definitie beschrijft wat iets ís, niet wat ermee moet gebeuren of onder welke voorwaarden het geldig is. Voorwaardelijke of normatieve formuleringen zoals 'indien', 'mits' en 'tenzij' horen thuis in regelgeving, niet in definities.

### When Applied
Applied to: alle
Recommendation: aanbevolen

## Implementation

### Algorithm
```python
# Validation Logic (from INT02Validator)
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
    r"\bindien\b",
    r"\bmits\b",
    r"\balleen als\b",
    r"\btenzij\b",
    r"\bvoor zover\b",
    r"\bop voorwaarde dat\b",
    r"\bin geval dat\b",
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
1. "transitie-eis: eis die een organisatie ondersteunt om migratie van de huidige naar de toekomstige situatie mogelijk te maken."
2. "Toegang: toestemming verleend door een bevoegde autoriteit om een systeem te gebruiken."
3. "Beschikking: schriftelijk besluit genomen door een bevoegde autoriteit."
4. "Register: officiële inschrijving in een openbaar register door een bevoegde instantie."

### Bad Examples (Should FAIL)
1. "transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken."
2. "Toegang: toestemming verleend door een bevoegde autoriteit, indien alle voorwaarden zijn vervuld."
3. "Beschikking: schriftelijk besluit, mits de aanvraag compleet is ingediend."
4. "Register: officiële inschrijving in een openbaar register, tenzij er bezwaar ligt."

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
- **Guideline:** Geen beslisregel
- **URL:** [https://www.astraonline.nl/index.php/Geen_beslisregel](https://www.astraonline.nl/index.php/Geen_beslisregel)

**Compliance requirement:** aanbevolen

## Notes
- **Type:** interne structuur
- **Theme:** interne kwaliteit van de definitie
- **Test Question:** Bevat de definitie geen voorwaardelijke of normatieve formuleringen zoals beslisregels?

## Extraction Date
2025-10-02
