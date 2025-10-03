# VAL-EMP-001: Lege definitie is ongeldig

## Metadata
- **ID:** VAL-EMP-001
- **Category:** VAL (Validation)
- **Priority:** hoog
- **Status:** defined (JSON only, no Python implementation)
- **Source File:** `src/toetsregels/regels/VAL-EMP-001.json`
- **Implementation Status:** ⚠️ JSON config exists, but no dedicated Python validator class

## Business Purpose

### What
Validates that the definition text is not empty. This is a fundamental pre-condition for all other validation rules.

### Why
An empty definition provides no value and would fail all meaningful quality checks. This is a basic data integrity requirement that must be satisfied before any semantic or structural validation can occur.

### When Applied
- **Always:** This is the first validation check
- **Applies to:** All definitions (new, imported, or edited)
- **Recommendation:** verplicht (mandatory)

## Implementation

### Algorithm
```python
def validate_not_empty(definitie: str) -> tuple[bool, str, float]:
    """
    Check if definition text is not empty.

    Steps:
    1. Strip whitespace from definition
    2. Check if result has length > 0
    3. Return pass/fail based on emptiness
    """
    if not definitie or len(definitie.strip()) < 1:
        return False, "❌ VAL-EMP-001: Definitie is leeg", 0.0

    return True, "✔️ VAL-EMP-001: Definitie bevat tekst", 1.0
```

**Key Steps:**
1. Normalize whitespace (strip leading/trailing spaces)
2. Check character count > 0
3. Binary pass/fail (no warnings)

### Thresholds
| Threshold | Value | Usage | Rationale |
|-----------|-------|-------|-----------|
| min_chars | 1 | Minimum non-whitespace characters | Even a single character satisfies "not empty" |
| Pass score | 1.0 | Validation passed | Definition contains text |
| Fail score | 0.0 | Validation failed | Definition is empty or whitespace-only |

**Hardcoded Values:**
- Line in JSON: `"min_chars": 1`
- This is the absolute minimum - any definition must have at least one character

### Patterns
*No regex patterns needed - simple length check*

### Error Messages
- **Pass:** "✔️ VAL-EMP-001: Definitie bevat tekst"
- **Fail:** "❌ VAL-EMP-001: Definitie is leeg"

**No warnings** - this is binary pass/fail

## Test Cases

### Good Examples (Should PASS)
1. "Een besluit is een vastgelegde uitkomst."
   - Reason: Contains meaningful text

2. "X"
   - Reason: Single character satisfies non-empty requirement

3. "   spatie   "
   - Reason: After strip, contains characters

### Bad Examples (Should FAIL)
1. ""
   - Reason: Completely empty string

2. "   "
   - Reason: Only whitespace (stripped = empty)

3. None
   - Reason: Null value

4. "\n\n\t  \n"
   - Reason: Only whitespace characters (tabs, newlines, spaces)

### Edge Cases
1. Single space: " " → FAIL (stripped is empty)
2. Single newline: "\n" → FAIL (whitespace only)
3. Unicode spaces: "\u00A0" → Depends on strip() behavior
4. Zero-width characters: May pass but are semantically empty

## Dependencies
- None (basic validation)
- **Should be called FIRST** before any other validation

**Called by:**
- ModularValidationService (pre-validation phase)
- Input validation layer
- Definition save operations

## ASTRA References
- **Type:** validatie (basic validation)
- **Theme:** basis (fundamental requirement)
- **Source:** Common sense data integrity requirement
- **Compliance requirement:** verplicht (mandatory)

This is not explicitly in ASTRA guidelines but is a fundamental requirement for any definition system.

## Notes
- **Implementation Gap:** This rule is defined in JSON but has no dedicated Python validator class
- **Current Implementation:** Likely handled inline in input validation or sanitization layer
- **Recommended Action:** Consider implementing as a formal validator for consistency
- **Performance:** Extremely fast (O(1) operation)
- **Type:** validatie
- **Theme:** basis
- **Test Question:** "Is er definitietekst ingevuld?"

## Rebuild Recommendations
1. Implement as lightweight pre-validation check
2. Run BEFORE loading other validators (fail fast)
3. Consider combining with VAL-LEN-001 for efficiency
4. Add to validation pipeline as "phase 0" (pre-checks)

## Extraction Date
2025-10-02

## Status: JSON-Only Rule
⚠️ **Implementation Status:** This rule exists as a JSON configuration but does not have a dedicated Python validator class. The validation logic is likely embedded in:
- `src/validation/input_validator.py`
- `src/services/cleaning_service.py`
- Or inline checks in the UI layer

**Recommendation:** Extract this logic into a formal validator for consistency with other rules.
