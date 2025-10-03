# ARAI-04SUB1: Beperk gebruik van modale werkwoorden

## Metadata
- **ID:** ARAI-04SUB1
- **Category:** ARAI
- **Priority:** midden
- **Status:** conceptueel
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/ARAI-04SUB1.py`
- **Class Name:** `ARAI04SUB1Validator`
- **Lines of Code:** 132

## Business Purpose

### What
Definities vermijden modale werkwoorden zoals ‘kan’, ‘mag’, ‘moet’, omdat deze onduidelijkheid scheppen over de essentie van het begrip.

### Why
Modale werkwoorden drukken mogelijkheid, toestemming of verplichting uit. In een definitie hoort objectieve beschrijving centraal te staan, niet potentie of wenselijkheid. Modale hulpwerkwoorden kunnen leiden tot interpretatieverschillen over of iets een kenmerk of een randvoorwaarde is.

### When Applied
Applied to: gehele definitie
Recommendation: optioneel

## Implementation

### Algorithm
```python
# Validation Logic (from ARAI04SUB1Validator)
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
    r"\bkan\b",
    r"\bkunnen\b",
    r"\bmag\b",
    r"\bmogen\b",
    r"\bmoet\b",
    r"\bmoeten\b",
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
1. "proces dat persoonsgegevens verwerkt"
2. "maatregel die tot gedragsverandering leidt"

### Bad Examples (Should FAIL)
1. "proces dat gegevens *kan* verwerken"
2. "maatregel die *moet* worden genomen bij overtreding"

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

**Compliance requirement:** optioneel

## Notes
- **Type:** formulering
- **Theme:** interne kwaliteit van de definitie
- **Test Question:** Bevat de definitie modale werkwoorden die verwarring kunnen veroorzaken over wat het begrip is?

## Extraction Date
2025-10-02
