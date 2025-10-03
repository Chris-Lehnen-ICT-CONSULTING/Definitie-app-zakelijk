# ESS-03: Instanties uniek onderscheidbaar (telbaarheid)

## Metadata
- **ID:** ESS-03
- **Category:** ESS
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/ESS-03.py`
- **Class Name:** `ESS03Validator`
- **Lines of Code:** 170

## Business Purpose

### What
Een definitie moet criterium(en) bevatten waarmee afzonderlijke instanties uniek herkenbaar en telbaar zijn (singulariteit of pluraliteit).

### Why
Bij telbare zelfstandige naamwoorden moet de definitie unieke kenmerken of identificatoren noemen (zoals serienummer, kenteken, VIN, ISBN, document-ID, inventarisnummer), zodat verschillende deskundigen in elke situatie tot exact dezelfde telling komen.

### When Applied
Applied to: telbare zelfstandige naamwoorden
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from ESS03Validator)
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
    r"\b(serienummer|serie?nummer|kenteken|vin|isbn|document-?id|identificatienummer|registratienummer|objectnummer|inventarisnummer)\b",
    r"\buniek(e)?\b",
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
1. "Een auto is een vierwielig motorvoertuig met een uniek chassisnummer (VIN) en kenteken."
2. "Een boekexemplaar is een fysiek gebonden exemplaar van een titel met eigen ISBN en inventarisnummer."

### Bad Examples (Should FAIL)
1. "Een auto is een vervoermiddel op vier wielen met een motor."
2. "Een boek is een verzameling pagina’s met tekst gebonden in een omslag."

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
- **Guideline:** Instanties uniek onderscheidbaar
- **URL:** [https://www.astraonline.nl/index.php/Instanties_uniek_onderscheidbaar](https://www.astraonline.nl/index.php/Instanties_uniek_onderscheidbaar)

**Compliance requirement:** verplicht

## Notes
- **Type:** essentie
- **Theme:** telbaarheid en onderscheidbaarheid
- **Test Question:** Bevat de definitie duidelijke criteria (bijv. serienummer, kenteken, ID) waarmee unieke identificatie van instanties mogelijk is?

## Extraction Date
2025-10-02
