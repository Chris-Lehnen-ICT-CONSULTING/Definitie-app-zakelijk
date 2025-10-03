# SAM-07: Geen betekenisverruiming binnen definitie

## Metadata
- **ID:** SAM-07
- **Category:** SAM
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/SAM-07.py`
- **Class Name:** `SAM07Validator`
- **Lines of Code:** 133

## Business Purpose

### What
De definitie mag de betekenis van de term niet uitbreiden met extra elementen die niet in de term besloten liggen.

### Why
Een definitie moet de betekenis van de term expliciteren, niet uitbreiden met verwante aspecten of extra functies. Dit voorkomt dat een begrip verwarring oplevert doordat het meer gaat betekenen dan bedoeld.

### When Applied
Applied to: alle
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from SAM07Validator)
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
    r"en indien nodig",
    r"en ook",
    r"en eventueel",
    r"eveneens",
    r"aanvullend",
    r"extra",
    r"tevens",
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
1. "toezicht houden: het controleren of regels worden nageleefd"

### Bad Examples (Should FAIL)
1. "toezicht houden: het controleren en indien nodig corrigeren van gedrag"

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
- **Guideline:** Geen betekenisverruiming binnen definitie
- **URL:** [https://www.astraonline.nl/index.php/Geen_betekenisverruiming_binnen_definitie](https://www.astraonline.nl/index.php/Geen_betekenisverruiming_binnen_definitie)

**Compliance requirement:** verplicht

## Notes
- **Type:** samenhang van termen
- **Theme:** begripsafbakening
- **Test Question:** Bevat de definitie uitsluitend elementen die inherent zijn aan de term, zonder aanvullende uitbreidingen?

## Extraction Date
2025-10-02
