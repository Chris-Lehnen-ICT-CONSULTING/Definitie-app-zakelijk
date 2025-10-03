# DUP-01: Geen duplicaat definities in database

## Metadata
- **ID:** DUP-01
- **Category:** DUP
- **Priority:** hoog
- **Status:** definitief
- **Source File:** `/Users/chrislehnen/Projecten/Definitie-app/src/toetsregels/regels/DUP_01.py`
- **Class Name:** `DUP01`
- **Lines of Code:** 151

## Business Purpose

### What
Controleer of er geen identieke of zeer vergelijkbare definitie al bestaat in de database voor hetzelfde begrip.

### Why
Voorkom dat dezelfde definitie meerdere keren wordt opgeslagen. Dit verbetert de datakwaliteit en voorkomt inconsistenties bij latere wijzigingen.

### When Applied
Applied to: alle
Recommendation: verplicht

## Implementation

### Algorithm
```python
# Validation Logic (from DUP01)
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
1. "Een nieuwe unieke definitie voor het begrip 'sanctie' die nog niet bestaat"
2. "Een definitie met substantiële verschillen ten opzichte van bestaande versies"

### Bad Examples (Should FAIL)
1. "Exact dezelfde definitie die al bestaat voor dit begrip"
2. "Een minimaal gewijzigde versie (alleen interpunctie) van een bestaande definitie"

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
- **Source:** Interne richtlijn

**Compliance requirement:** verplicht

## Notes
- **Type:** database
- **Theme:** datakwaliteit
- **Test Question:** Bestaat deze definitie nog niet in de database?

## Extraction Date
2025-10-02
