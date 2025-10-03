# STR-06: Essentie ≠ informatiebehoefte

## Metadata
- **ID:** STR-06
- **Category:** STR
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/STR-06.py`
- **Class Name:** `STR06Validator`
- **Lines of Code:** 134

## Business Purpose

### What
Een definitie geeft de aard van het begrip weer, niet de reden waarom het nodig is.

### Why
De definitie beschrijft wat het begrip *is*, niet waarvoor het nodig is. Formuleringen als 'om te kunnen...' of 'ten behoeve van...' beschrijven een behoefte of gebruik en horen niet thuis in de definitie zelf.

### When Applied
Applied to: alle
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from STR06Validator)
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
    r"\bzodat\b",
    r"\bten behoeve van\b",
    r"\bvoor het verkrijgen van\b",
    r"\bmet het oog op\b",
    r"\bgericht op\b",
]
```

### Thresholds
| Threshold | Value | Usage | Notes |
|-----------|-------|-------|-------|
| Pass score | 1.0 | Perfect validation | No violations found |
| Warning score | 0.5 | Partial pass | Minor issues detected |
| Fail score | 0.0 | Validation failed | Violations found |
| Extracted value | 0.5 | Used in implementation | See Python code |
| Extracted value | 1.0 | Used in implementation | See Python code |

### Error Messages
- **Pass:** "✔️ {rule_id}: [validation passed message]"
- **Warning:** "🟡 {rule_id}: [warning message with details]"
- **Fail:** "❌ {rule_id}: [failure message with found violations]"

## Test Cases

### Good Examples (Should PASS)
1. "beveiligingsmaatregel: voorziening die ongeautoriseerde toegang voorkomt"

### Bad Examples (Should FAIL)
1. "beveiligingsmaatregel: voorziening om ongeautoriseerde toegang te voorkomen"

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
- **Guideline:** Essentie ≠ informatiebehoefte
- **URL:** [https://www.astraonline.nl/index.php/Essentie_≠_informatiebehoefte](https://www.astraonline.nl/index.php/Essentie_≠_informatiebehoefte)

**Compliance requirement:** verplicht

## Notes
- **Type:** gehele definitie
- **Theme:** structuur van de definitie
- **Test Question:** Bevat de definitie uitsluitend wat het begrip is, en niet waarom het nodig is of waarvoor het gebruikt wordt?

## Extraction Date
2025-10-02
