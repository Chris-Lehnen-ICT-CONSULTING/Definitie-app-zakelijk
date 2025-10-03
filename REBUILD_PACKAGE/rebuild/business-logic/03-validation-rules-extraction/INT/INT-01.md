# INT-01: Compacte en begrijpelijke zin

## Metadata
- **ID:** INT-01
- **Category:** INT
- **Priority:** midden
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/INT-01.py`
- **Class Name:** `INT01Validator`
- **Lines of Code:** 165

## Business Purpose

### What
Een definitie is compact en in één enkele zin geformuleerd.

### Why
Een definitie moet in één zin worden gegeven. Deze zin moet helder, kernachtig en goed leesbaar zijn. Opsommingen, bijzinnen of overmatige complexiteit maken de definitie minder toegankelijk.

### When Applied
Applied to: alle
Recommendation: aanbevolen

## Implementation

### Algorithm
```python
# Validation Logic (from INT01Validator)
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
    r",",
    r";",
    r"\ben\b",
    r"\bmaar\b",
    r"\bof\b",
    r"\bmet betrekking tot\b",
    r"\bwaarbij\b",
    r"\bdie\b",
    r"\bwelke\b",
    r"\balsmede\b",
    r"\bindien\b",
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
1. "transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken."

### Bad Examples (Should FAIL)
1. "transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken. In tegenstelling tot andere eisen vertegenwoordigen transitie-eisen tijdelijke behoeften, in plaats van meer permanente."

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

**Compliance requirement:** aanbevolen

## Notes
- **Type:** interne structuur
- **Theme:** interne kwaliteit van de definitie
- **Test Question:** Is de definitie geformuleerd als één enkele, begrijpelijke zin?

## Extraction Date
2025-10-02
