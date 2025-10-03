# STR-01: definitie start met zelfstandig naamwoord

## Metadata
- **ID:** STR-01
- **Category:** STR
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/STR-01.py`
- **Class Name:** `STR01Validator`
- **Lines of Code:** 126

## Business Purpose

### What
De definitie moet starten met een zelfstandig naamwoord of naamwoordgroep, niet met een werkwoord.

### Why
De definitie moet uitdrukken wat het begrip *is*, niet wat het *doet*. Daarom moet de zin beginnen met een zelfstandig naamwoord (de 'kick-off term'). Beginnen met een werkwoord leidt tot verwarring over de aard van het begrip.

### When Applied
Applied to: alle
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from STR01Validator)
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
    r"^is\b",
    r"^zijn\b",
    r"^heeft\b",
    r"^hebben\b",
    r"^wordt\b",
    r"^kan\b",
    r"^doet\b",
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
1. "proces dat beslissers identificeert..."
2. "maatregel die recidive voorkomt..."

### Bad Examples (Should FAIL)
1. "is een maatregel die recidive voorkomt"
2. "wordt toegepast in het gevangeniswezen"

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
- **Guideline:** Structuur van definities
- **URL:** [https://www.astraonline.nl/index.php/Structuur_van_definities](https://www.astraonline.nl/index.php/Structuur_van_definities)

**Compliance requirement:** verplicht

## Notes
- **Type:** gehele definitie
- **Theme:** structuur van de definitie
- **Test Question:** Begint de definitie met een zelfstandig naamwoord of naamwoordgroep, en niet met een werkwoord?

## Extraction Date
2025-10-02
