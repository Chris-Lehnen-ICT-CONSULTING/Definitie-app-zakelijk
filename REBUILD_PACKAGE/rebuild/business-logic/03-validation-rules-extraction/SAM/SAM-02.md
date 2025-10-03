# SAM-02: Kwalificatie omvat geen herhaling

## Metadata
- **ID:** SAM-02
- **Category:** SAM
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/SAM-02.py`
- **Class Name:** `SAM02Validator`
- **Lines of Code:** 130

## Business Purpose

### What
Als een begrip wordt gekwalificeerd, mag de definitie geen herhaling bevatten uit of conflict bevatten met de definitie van het hoofdbegrip.

### Why
Letterlijke herhaling of nauwkeurige paraphrasering van de basisterm of elementen daarvan leidt tot misverstanden en strijdt met andere principes zoals 'Definities niet nesten' en 'Kwalificatie leidt niet tot afwijking'. Gebruik een genus+differentia-patroon zonder herhaling van de eerdere definitie.

### When Applied
Applied to: gehele definitie
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from SAM02Validator)
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
1. "delict: menselijke gedraging die binnen de grenzen van een wettelijke strafbepaling valt"
2. "opgehelderd delict: delict waarvoor de politie voldoende bewijs tegen een verdachte heeft om te veroordelen"

### Bad Examples (Should FAIL)
1. "delict: delict dat binnen de grenzen van een of meer wettelijke strafbepalingen valt en waarvoor de politie voldoende bewijs tegen een verdachte heeft voor een veroordeling"

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
- **Guideline:** Kwalificatie omvat geen herhaling
- **URL:** [https://www.astraonline.nl/index.php/Kwalificatie_omvat_geen_herhaling](https://www.astraonline.nl/index.php/Kwalificatie_omvat_geen_herhaling)

**Compliance requirement:** verplicht

## Notes
- **Type:** gehele definitie
- **Theme:** samenhang binnen domein
- **Test Question:** Bevat de definitie herhaling of conflict met de definitie van het hoofdbegrip?

## Extraction Date
2025-10-02
