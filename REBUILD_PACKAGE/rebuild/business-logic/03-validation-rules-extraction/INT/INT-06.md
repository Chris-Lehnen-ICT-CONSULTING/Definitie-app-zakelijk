# INT-06: Definitie bevat geen toelichting

## Metadata
- **ID:** INT-06
- **Category:** INT
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/INT-06.py`
- **Class Name:** `INT06Validator`
- **Lines of Code:** 140

## Business Purpose

### What
Een definitie bevat geen nadere toelichting of voorbeelden, maar uitsluitend de afbakening van het begrip.

### Why
Definities moeten kort en krachtig zijn. Een toelichting (bijvoorbeeld een uitwerking of extra context) hoort thuis in een notitie of toelichtende tekst, niet in de definitiezin zelf.

### When Applied
Applied to: gehele definitie
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from INT06Validator)
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
    r"\bbijvoorbeeld\b",
    r"\bzoals\b",
    r"\bdit houdt in\b",
    r"\bdat wil zeggen\b",
    r"\bnamelijk\b",
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
1. "model: vereenvoudigde weergave van de werkelijkheid"

### Bad Examples (Should FAIL)
1. "model: vereenvoudigde weergave van de werkelijkheid, die visueel wordt weergegeven"

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
- **Guideline:** Definitie bevat geen toelichting
- **URL:** [https://www.astraonline.nl/index.php/Definitie_bevat_geen_toelichting](https://www.astraonline.nl/index.php/Definitie_bevat_geen_toelichting)

**Compliance requirement:** verplicht

## Notes
- **Type:** inhoud
- **Theme:** interne kwaliteit van de definitie
- **Test Question:** Bevat de definitie signalen van toelichting zoals 'bijvoorbeeld', 'zoals', 'dit houdt in', enzovoort?

## Extraction Date
2025-10-02
