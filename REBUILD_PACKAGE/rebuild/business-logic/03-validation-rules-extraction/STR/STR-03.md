# STR-03: Definitie ≠ synoniem

## Metadata
- **ID:** STR-03
- **Category:** STR
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/STR-03.py`
- **Class Name:** `STR03Validator`
- **Lines of Code:** 135

## Business Purpose

### What
De definitie van een begrip mag niet simpelweg een synoniem zijn van de te definiëren term.

### Why
Het aandragen van een synoniem wordt niet gezien als een goede definitie, want het verheldert de werkelijke betekenis van het begrip niet. (Het opnemen van synoniemen van een term, naast de eigenlijke definitie van het begrip, is overigens wel zinvol.)

### When Applied
Applied to: alle
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from STR03Validator)
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
    r"^\s*\w+\s*$",
    r"^\s*\w+\s*\(.*\)\s*$",
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
1. "evaluatie: resultaat van iets beoordelen, appreciëren of interpreteren"

### Bad Examples (Should FAIL)
1. "evaluatie: beoordeling"
2. "registratie: vastlegging (in een systeem)"

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
- **Guideline:** Definitie ≠ synoniem
- **URL:** [https://www.astraonline.nl/index.php/Definitie_%E2%89%A0_synoniem](https://www.astraonline.nl/index.php/Definitie_%E2%89%A0_synoniem)

**Compliance requirement:** verplicht

## Notes
- **Type:** gehele definitie
- **Theme:** structuur van de definitie
- **Test Question:** Is de definitie meer dan alleen een synoniem van de term?

## Extraction Date
2025-10-02
