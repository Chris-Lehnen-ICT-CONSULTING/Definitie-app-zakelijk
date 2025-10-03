# ARAI-05: Vermijd impliciete aannames

## Metadata
- **ID:** ARAI-05
- **Category:** ARAI
- **Priority:** midden
- **Status:** conceptueel
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/ARAI-05.py`
- **Class Name:** `ARAI05Validator`
- **Lines of Code:** 127

## Business Purpose

### What
Een definitie bevat geen impliciete aannames die alleen met voorkennis begrepen kunnen worden.

### Why
Definities moeten zelfstandig begrijpelijk zijn. Formuleringen die gebaseerd zijn op aannames zoals 'gebruikelijk is', 'het systeem', of verwijzen naar onbekende contexten zorgen voor interpretatieproblemen. Een goede definitie maakt expliciet wat bedoeld wordt, zonder impliciete verwijzingen.

### When Applied
Applied to: gehele definitie
Recommendation: optioneel

## Implementation

### Algorithm
```python
# Validation Logic (from ARAI05Validator)
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
    r"\bzoals gebruikelijk\b",
    r"\bzoals bekend\b",
    r"\bin het systeem\b",
    r"\bde standaard\b",
    r"\bbekende procedure\b",
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
1. "procedure: vastgelegde reeks stappen die wordt uitgevoerd bij het registreren van incidenten"

### Bad Examples (Should FAIL)
1. "procedure: zoals gebruikelijk uitgevoerd binnen het systeem"
2. "gegeven: informatie zoals bekend in de registratiepraktijk"

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

**Compliance requirement:** optioneel

## Notes
- **Type:** begrijpelijkheid
- **Theme:** zelfstandige leesbaarheid
- **Test Question:** Bevat de definitie formuleringen die impliciet verwijzen naar aannames, gewoonten of contexten die niet worden toegelicht?

## Extraction Date
2025-10-02
