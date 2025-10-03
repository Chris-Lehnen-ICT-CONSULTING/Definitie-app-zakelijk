# SAM-01: Kwalificatie leidt niet tot afwijking

## Metadata
- **ID:** SAM-01
- **Category:** SAM
- **Priority:** midden
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/SAM-01.py`
- **Class Name:** `SAM01Validator`
- **Lines of Code:** 160

## Business Purpose

### What
Een definitie mag niet zodanig zijn geformuleerd dat deze afwijkt van de betekenis die de term in andere contexten heeft.

### Why
Soms wordt geprobeerd een term met een bekende betekenis een andere lading te geven door een kwalificatie toe te voegen, zoals 'technisch proces' of 'juridische maatregel'. Dat mag, zolang de definitie niet in strijd is met de gebruikelijke betekenis van de term. Een definitie moet dus geen semantisch misleidende kwalificaties bevatten.

### When Applied
Applied to: gehele definitie
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from SAM01Validator)
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
    r"\btechnisch\b",
    r"\bjuridisch\b",
    r"\boperationeel\b",
    r"\bintern\b",
    r"\bexterne\b",
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
1. "proces: reeks activiteiten met een gemeenschappelijk doel"
2. "juridisch proces: proces binnen de context van rechtspleging"

### Bad Examples (Should FAIL)
1. "proces: technische afhandeling van informatie tussen systemen (terwijl 'proces' elders breder wordt gebruikt)"

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
- **Guideline:** Kwalificatie leidt niet tot afwijking
- **URL:** [https://www.astraonline.nl/index.php/Kwalificatie_leidt_niet_tot_afwijking](https://www.astraonline.nl/index.php/Kwalificatie_leidt_niet_tot_afwijking)

**Compliance requirement:** verplicht

## Notes
- **Type:** semantische zuiverheid
- **Theme:** betekenisconsistentie
- **Test Question:** Leidt de gebruikte kwalificatie in de definitie tot een betekenis die wezenlijk afwijkt van het algemeen aanvaarde begrip?

## Extraction Date
2025-10-02
