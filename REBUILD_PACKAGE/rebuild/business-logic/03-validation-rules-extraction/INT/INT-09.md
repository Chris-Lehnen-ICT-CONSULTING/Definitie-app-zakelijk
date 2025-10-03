# INT-09: Opsomming in extensionele definitie is limitatief

## Metadata
- **ID:** INT-09
- **Category:** INT
- **Priority:** midden
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/INT-09.py`
- **Class Name:** `INT09Validator`
- **Lines of Code:** 160

## Business Purpose

### What
Een extensionele definitie definieert een begrip door opsomming van alle bedoelde elementen; deze opsomming moet uitsluitend limitatief zijn.

### Why
Een extensionele definitie is een definitie door opsomming van alle bedoelde elementen. Bijvoorbeeld VOERTUIG = AUTO of BOOT of VLIEGTUIG. Wanneer een opsomming in een definitie voorkomt, moet expliciet blijken dat de genoemde elementen de enige mogelijke zijn. Vermijd termen als "zoals", "bijvoorbeeld", "onder andere", "enz." of "waaronder begrepen".

### When Applied
Applied to: termen die door extensionele definities worden gedefinieerd
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from INT09Validator)
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
    r"zoals",
    r"bijvoorbeeld",
    r"onder andere",
    r"etc\.",
    r"enz\.",
    r"en andere",
    r"\bo\.a\.\b",
    r"\binclusief\b",
    r"waaronder begrepen",
    r"al dan niet",
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
1. "niet-natuurlijk persoon: rechtspersoon of samenwerkingsverband"
2. "voertuig: gemotoriseerd vervoermiddel, zoals auto, motorfiets of brommer (uitsluitend deze types)"

### Bad Examples (Should FAIL)
1. "voertuig: zoals auto, motorfiets of brommer"
2. "maatregel: bijvoorbeeld een waarschuwing, boete of sanctie"

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
- **Guideline:** Opsomming in extensionele definitie is limitatief
- **URL:** [https://www.astraonline.nl/index.php/Opsomming_in_extensionele_definitie_is_limitatief](https://www.astraonline.nl/index.php/Opsomming_in_extensionele_definitie_is_limitatief)

**Compliance requirement:** verplicht

## Notes
- **Type:** gehele definitie
- **Theme:** interne kwaliteit van de definitie
- **Test Question:** Is een opsomming in de definitie uitsluitend limitatief (zonder suggestie van andere mogelijke elementen)?

## Extraction Date
2025-10-02
