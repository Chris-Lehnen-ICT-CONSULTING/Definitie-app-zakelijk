# SAM-03: Definitieteksten niet nesten

## Metadata
- **ID:** SAM-03
- **Category:** SAM
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/SAM-03.py`
- **Class Name:** `SAM03Validator`
- **Lines of Code:** 115

## Business Purpose

### What
Een definitie van een begrip of een belangrijk deel daarvan mag niet letterlijk herhaald worden in de definitie van een ander begrip.

### Why
De betekenis van een begrip moet op één plek vastliggen. Herhaling van (een deel van) de definitie van het ene begrip in de definitie van een ander begrip leidt tot onderhoudsproblemen en verwarring. Verwijs in plaats daarvan naar het andere begrip of definieer begrippen afzonderlijk.

### When Applied
Applied to: gehele definitie
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from SAM03Validator)
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
    r"\bzie definitie van\b",
    r"\bzoals gedefinieerd in\b",
    r"\bzoals omschreven bij\b",
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
1. "procesmodel: model van een proces"
2. "procesmodel: schematisch model van een proces"

### Bad Examples (Should FAIL)
1. "procesmodel: doelgerichte abstractie van een aantal activiteiten die samen een bepaalde gewenste uitkomst oplevert"

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
- **Guideline:** Definitieteksten niet nesten
- **URL:** [https://www.astraonline.nl/index.php/Definitieteksten_niet_nesten](https://www.astraonline.nl/index.php/Definitieteksten_niet_nesten)

**Compliance requirement:** verplicht

## Notes
- **Type:** gehele definitie
- **Theme:** samenhang binnen domein
- **Test Question:** Bevat de definitie letterlijk een andere definitietekst of deel daarvan?

## Extraction Date
2025-10-02
