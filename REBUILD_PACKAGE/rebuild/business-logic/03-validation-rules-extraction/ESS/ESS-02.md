# ESS-02: Ontologische categorie expliciteren (type / particulier / proces / resultaat)

## Metadata
- **ID:** ESS-02
- **Category:** ESS
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/ESS-02.py`
- **Class Name:** `ESS02Validator`
- **Lines of Code:** 232

## Business Purpose

### What
Indien een begrip meerdere ontologische categorieën kan aanduiden, moet uit de definitie ondubbelzinnig blijken welke van deze vier bedoeld wordt: soort (type), exemplaar (particulier), proces (activiteit) of resultaat (uitkomst).

### Why
Begrippen kunnen polysemisch zijn. Om verwarring te voorkomen, moet de definitie expliciet aangeven om welke categorie het gaat, bijvoorbeeld door 'is een categorie', 'is een exemplaar', 'is een activiteit' of 'is het resultaat van'.

### When Applied
Applied to: gehele definitie
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from ESS02Validator)
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
*No specific patterns defined*

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
*No good examples provided*

### Bad Examples (Should FAIL)
*No bad examples provided*

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
- **Guideline:** Ontologische categorie expliciteren
- **URL:** [https://www.astraonline.nl/index.php/Polysemie_proces_vs_resultaat](https://www.astraonline.nl/index.php/Polysemie_proces_vs_resultaat)

**Compliance requirement:** verplicht

## Notes
- **Type:** polysemie
- **Theme:** betekenislagen
- **Test Question:** Geeft de definitie ondubbelzinnig aan of het begrip een type, een particular, een proces of een resultaat is?

## Extraction Date
2025-10-02
