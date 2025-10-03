# ARAI-04: Vermijd modale hulpwerkwoorden

## Metadata
- **ID:** ARAI-04
- **Category:** ARAI
- **Priority:** midden
- **Status:** conceptueel
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/ARAI-04.py`
- **Class Name:** `ARAI04Validator`
- **Lines of Code:** 127

## Business Purpose

### What
Definities vermijden het gebruik van modale hulpwerkwoorden zoals 'kunnen', 'mogen', 'moeten' of 'zullen'.

### Why
Modale hulpwerkwoorden impliceren mogelijkheid, verplichting of verwachting en zijn daarom niet geschikt voor afbakenende definities. Ze maken de betekenis vaag of afhankelijk van context. Een definitie moet beschrijven wat iets *is*, niet wat het zou kunnen zijn of moet doen.

### When Applied
Applied to: gehele definitie
Recommendation: optioneel

## Implementation

### Algorithm
```python
# Validation Logic (from ARAI04Validator)
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
    r"\bmoet\b",
    r"\bmoeten\b",
    r"\bmogen\b",
    r"\bzou\b",
    r"\bzullen\b",
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
1. "maatregel die toegang beperkt tot bevoegde personen"
2. "procedure die leidt tot besluitvorming"

### Bad Examples (Should FAIL)
1. "maatregel die toegang kan beperken"
2. "procedure die tot besluitvorming zou kunnen leiden"

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

**Compliance requirement:** optioneel

## Notes
- **Type:** formulering
- **Theme:** duidelijkheid en afbakening
- **Test Question:** Bevat de definitie modale hulpwerkwoorden die wijzen op mogelijkheid, plicht of wenselijkheid?

## Extraction Date
2025-10-02
