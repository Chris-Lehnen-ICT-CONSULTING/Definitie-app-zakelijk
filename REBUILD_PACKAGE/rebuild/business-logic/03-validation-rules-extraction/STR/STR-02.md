# STR-02: Kick-off ≠ de term

## Metadata
- **ID:** STR-02
- **Category:** STR
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/STR-02.py`
- **Class Name:** `STR02Validator`
- **Lines of Code:** 129

## Business Purpose

### What
De definitie moet beginnen met verwijzing naar een breder begrip, en dan de verbijzondering ten opzichte daarvan aangeven.

### Why
De definitie moet beginnen met een term ('kick-off term') die een breder begrip aanduidt, en moet vervolgens aangeven hoe het te definiëren begrip verschilt van het bredere begrip, of, anders gezegd, een speciaal geval is van het bredere begrip.

### When Applied
Applied to: alle
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from STR02Validator)
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
    r"^\s*\b(\w+)\b\s*:\s*\1\b",
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
1. "analist: professional verantwoordelijk voor …"

### Bad Examples (Should FAIL)
1. "analist: analist die verantwoordelijk is voor …"

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
- **Guideline:** Kick-off vervolgen met toespitsing
- **URL:** [https://www.astraonline.nl/index.php/Kick-off_vervolgen_met_toespitsing](https://www.astraonline.nl/index.php/Kick-off_vervolgen_met_toespitsing)

**Compliance requirement:** verplicht

## Notes
- **Type:** element in de definitie
- **Theme:** structuur van de definitie
- **Test Question:** Begint de definitie met een breder begrip en specificeert het vervolgens hoe het te definiëren begrip daarvan verschilt?

## Extraction Date
2025-10-02
