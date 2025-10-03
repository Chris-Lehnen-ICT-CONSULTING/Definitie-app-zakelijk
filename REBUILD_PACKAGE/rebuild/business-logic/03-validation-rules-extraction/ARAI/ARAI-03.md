# ARAI-03: Beperk gebruik van bijvoeglijke naamwoorden

## Metadata
- **ID:** ARAI-03
- **Category:** ARAI
- **Priority:** midden
- **Status:** conceptueel
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/ARAI-03.py`
- **Class Name:** `ARAI03Validator`
- **Lines of Code:** 128

## Business Purpose

### What
Definities bevatten zo min mogelijk subjectieve of contextafhankelijke bijvoeglijke naamwoorden.

### Why
Bijvoeglijke naamwoorden zoals 'effectief', 'belangrijk', 'relevant' of 'toereikend' voegen zelden objectieve waarde toe aan een definitie. Ze zijn interpretatiegevoelig en maken de definitie minder toetsbaar. Gebruik alleen bijvoeglijke naamwoorden als ze essentieel zijn en objectief meetbaar.

### When Applied
Applied to: gehele definitie
Recommendation: optioneel

## Implementation

### Algorithm
```python
# Validation Logic (from ARAI03Validator)
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
    r"\beffectief\b",
    r"\bbelangrijk\b",
    r"\brelevant\b",
    r"\btoereikend\b",
    r"\badequaat\b",
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
1. "maatregel die leidt tot het voorkomen van recidive"
2. "gegeven dat unieke identificatie mogelijk maakt"

### Bad Examples (Should FAIL)
1. "belangrijke maatregel ter bevordering van veiligheid"
2. "adequaat systeem voor gegevensuitwisseling"

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
- **Guideline:** Compacte en begrijpelijke zin
- **URL:** [https://www.astraonline.nl/index.php/Compacte_en_begrijpelijke_zin](https://www.astraonline.nl/index.php/Compacte_en_begrijpelijke_zin)
- **Guideline:** Verwant aan ARAI05 (Vermijd impliciete aannames)
- **URL:** [https://www.astraonline.nl/index.php/Geen_ontoegankelijke_achtergrondkennis_nodig](https://www.astraonline.nl/index.php/Geen_ontoegankelijke_achtergrondkennis_nodig)

**Compliance requirement:** optioneel

## Notes
- **Type:** formulering
- **Theme:** objectiviteit en helderheid
- **Test Question:** Bevat de definitie subjectieve of contextgevoelige bijvoeglijke naamwoorden die de duidelijkheid of toetsbaarheid verminderen?

## Extraction Date
2025-10-02
