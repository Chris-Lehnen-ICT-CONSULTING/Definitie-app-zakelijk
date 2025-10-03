# SAM-08: Synoniemen hebben één definitie

## Metadata
- **ID:** SAM-08
- **Category:** SAM
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/SAM-08.py`
- **Class Name:** `SAM08Validator`
- **Lines of Code:** 130

## Business Purpose

### What
Voor synoniemen wordt één en dezelfde definitie gehanteerd.

### Why
Als meerdere termen als synoniem worden beschouwd, moet exact dezelfde definitie worden gebruikt. Dit voorkomt inconsistentie en verwarring over betekenisverschillen tussen termen die eigenlijk gelijk zijn.

### When Applied
Applied to: alle
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from SAM08Validator)
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
    r"\bzie\s+term\s+[A-Z]",
    r"\bsynoniem\s+van\b",
    r"\book wel\b",
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
1. "term A: proces waarbij gegevens worden verzameld"
2. "term B: zie term A"

### Bad Examples (Should FAIL)
1. "term A: proces waarbij gegevens worden verzameld"
2. "term B: methode om gegevens op te slaan"

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
- **Guideline:** Synoniemen hebben één definitie
- **URL:** [https://www.astraonline.nl/index.php/Synoniemen_hebben_%C3%A9%C3%A9n_definitie](https://www.astraonline.nl/index.php/Synoniemen_hebben_%C3%A9%C3%A9n_definitie)

**Compliance requirement:** verplicht

## Notes
- **Type:** samenhang van termen
- **Theme:** begripsconsistentie
- **Test Question:** Wordt voor synoniemen exact dezelfde definitie gebruikt?

## Extraction Date
2025-10-02
