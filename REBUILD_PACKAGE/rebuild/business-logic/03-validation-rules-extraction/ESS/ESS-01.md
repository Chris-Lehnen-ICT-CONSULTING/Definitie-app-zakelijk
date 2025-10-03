# ESS-01: Essentie, niet doel

## Metadata
- **ID:** ESS-01
- **Category:** ESS
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/ESS-01.py`
- **Class Name:** `ESS01Validator`
- **Lines of Code:** 118

## Business Purpose

### What
Een definitie beschrijft wat iets is, niet wat het doel of de bedoeling ervan is.

### Why
Definities moeten focussen op de aard en kenmerken van een begrip, niet op de reden waarom het bestaat of waarvoor het gebruikt wordt. Formuleringen als ‘om te’, ‘met als doel’, of ‘zodat’ wijzen vaak op een doel in plaats van op een definitie.

### When Applied
Applied to: gehele definitie
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from ESS01Validator)
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
    r"\bom te\b",
    r"\bmet als doel\b",
    r"\bbedoeld om\b",
    r"\bbedoeld voor\b",
    r"\bteneinde\b",
    r"\bopdat\b",
    r"\bten behoeve van\b",
    r"\bin het kader van\b",
    r"\bzodat\b",
    r"\bgericht op\b",
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
1. "meldpunt: instantie die meldingen registreert over strafbare feiten"
2. "sanctie: maatregel die volgt op normovertreding"

### Bad Examples (Should FAIL)
1. "meldpunt: instantie om meldingen te kunnen verwerken"
2. "sanctie: maatregel met als doel naleving te bevorderen"

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
- **Guideline:** Essentie, niet doel
- **URL:** [https://www.astraonline.nl/index.php/Essentie,_niet_doel](https://www.astraonline.nl/index.php/Essentie,_niet_doel)

**Compliance requirement:** verplicht

## Notes
- **Type:** essentie versus gebruik
- **Theme:** begripszuiverheid
- **Test Question:** Bevat de definitie uitsluitend de essentie van het begrip, zonder doel- of gebruiksgericht taalgebruik?

## Extraction Date
2025-10-02
