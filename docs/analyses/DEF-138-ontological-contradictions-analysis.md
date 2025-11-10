# DEF-138: Deep Analysis of Ontological Category Contradictions

## Executive Summary

This document presents a comprehensive analysis of the contradictions in the DefinitieAgent prompt system regarding ontological categories, specifically the PROCES category and the use of "handelingsnaamwoorden" (gerunds/action nouns). The analysis reveals a fundamental linguistic confusion that needs resolution.

## The Core Contradiction Identified

### 1. Contradictory Instructions

The system contains three conflicting instructions:

1. **General Structure Rule (STR-01)**:
   - "De definitie moet starten met een zelfstandig naamwoord" (Definition must start with a noun)
   - Location: `structure_rules_module.py` line 136-138

2. **PROCES Category Guidance (semantic_categorisation_module.py)**:
   - Lines 139: `start met: 'activiteit waarbij...', 'handeling die...', 'proces waarin...'`
   - Lines 181-202: Explicit PROCES guidance says start with these action nouns
   - **Key insight**: "activiteit", "handeling", "proces" ARE nouns (zelfstandige naamwoorden)

3. **ARAI-01 Validation Rule**:
   - "geen werkwoord als kern (afgeleid)" (no verb as core (derived))
   - Pattern matches: `\\b(is|zijn|doet|kan|heeft|hebben|wordt|vormt|creëert)\\b`
   - **Critical**: This actually checks for CONJUGATED VERBS, not nominalized forms!

### 2. Linguistic Analysis

#### What is a "Handelingsnaamwoord"?

A handelingsnaamwoord (gerund/action noun) in Dutch is:
- **Morphologically**: A NOUN (zelfstandig naamwoord)
- **Semantically**: Describes an action/process
- **Examples**:
  - "observatie" (from observeren)
  - "verzameling" (from verzamelen)
  - "registratie" (from registreren)
  - "activiteit" (activity)
  - "handeling" (action)
  - "proces" (process)

**CRUCIAL FINDING**: These ARE grammatically nouns, NOT verbs!

### 3. The Real Problem

The contradiction is actually a **misunderstanding of linguistic terminology**:

1. **ARAI-01 is checking for CONJUGATED VERBS** (is, heeft, wordt) - which is CORRECT
2. **STR-01 requires starting with a NOUN** - which is CORRECT
3. **PROCES requires handelingsnaamwoorden** - which ARE NOUNS, so also CORRECT!

**There is NO actual contradiction** - just unclear documentation!

## Current Implementation Analysis

### ARAI-01 Implementation
```python
# ARAI-01.json line 8-9:
"herkenbaar_patronen": [
    "\\b(is|zijn|doet|kan|heeft|hebben|wordt|vormt|creëert)\\b"
]
```
- Checks for CONJUGATED verbs (is, zijn, heeft, etc.)
- Does NOT check for gerunds/action nouns
- Correctly prevents: "is een activiteit" ❌
- Correctly allows: "activiteit waarbij" ✅

### ESS-02 Implementation
```json
# ESS-02.json lines 15-18:
"herkenbaar_patronen_proces": [
    "\\b(is een|betreft een) (proces|activiteit|handeling|gebeurtenis)\\b",
    "\\b(proces|activiteit|handeling|gebeurtenis)\\b"
]
```
- Correctly identifies process-related nouns
- Example good patterns: "activiteit waarbij gegevens worden verzameld"

### Semantic Categorisation Module
```python
# Lines 181-202 show PROCES kick-off options:
"activiteit waarbij..." → focus op wat er gebeurt
"handeling die..." → focus op de actie
"proces waarin..." → focus op het verloop
```
- All start with NOUNS (activiteit, handeling, proces)
- Comply with STR-01 (start with noun)
- Comply with ARAI-01 (no conjugated verb)

## Solution Recommendation: Option C - Linguistic Precision

### Chosen Solution: Differentiate Morphology from Function

**Rationale**: The "contradiction" is actually a documentation/clarity issue, not a code issue.

**Key Principles**:
1. **Handelingsnaamwoorden ARE morphologically nouns** → Valid for STR-01
2. **They functionally describe actions** → Perfect for PROCES category
3. **ARAI-01 applies to CONJUGATED verbs only** → Not to nominalized forms

### Why This Solution?

1. **Linguistically Correct**: Respects Dutch grammar rules
2. **No Code Changes Required**: The implementation is already correct!
3. **Only Documentation Updates Needed**: Clarify terminology
4. **Maintains All Existing Validations**: No regression risk

## Required Changes

### 1. Documentation Updates

#### Update ARAI-01.json
```json
{
  "naam": "geen werkwoord als kern (vervoegd werkwoord)",
  "uitleg": "De kern van de definitie mag geen vervoegd werkwoord zijn. Zelfstandige naamwoorden die een handeling aanduiden (handelingsnaamwoorden zoals 'activiteit', 'proces', 'registratie') zijn WEL toegestaan.",
  "toelichting": "Een definitie moet beschrijven wat iets is, niet wat het doet. Vervoegde werkwoorden ('is', 'heeft', 'wordt') als begin leiden tot onduidelijkheid. Handelingsnaamwoorden zijn grammaticaal zelfstandige naamwoorden en daarom toegestaan voor PROCES-begrippen."
}
```

#### Update semantic_categorisation_module.py
Add clarifying comment at line 180:
```python
"proces": """**PROCES CATEGORIE - Formuleer als ACTIVITEIT/HANDELING:**

⚠️ BELANGRIJK: De kick-off termen hieronder zijn ZELFSTANDIGE NAAMWOORDEN (handelingsnaamwoorden),
geen werkwoorden! Ze voldoen dus aan STR-01 (start met zelfstandig naamwoord) en ARAI-01
(geen vervoegd werkwoord als kern).

KICK-OFF opties (kies één):
- 'activiteit waarbij...' → focus op wat er gebeurt (zelfstandig naamwoord!)
- 'handeling die...' → focus op de actie (zelfstandig naamwoord!)
- 'proces waarin...' → focus op het verloop (zelfstandig naamwoord!)
```

#### Update structure_rules_module.py
Add clarification at line 138:
```python
"- De definitie moet starten met een zelfstandig naamwoord of naamwoordgroep, niet met een werkwoord."
"- Let op: Handelingsnaamwoorden ('activiteit', 'proces', 'handeling') zijn zelfstandige naamwoorden!"
```

### 2. Validation Pattern Updates

#### ARAI-01.py
Add comment at line 52:
```python
# Check for CONJUGATED verbs only, not action nouns (handelingsnaamwoorden)
# Action nouns like 'activiteit', 'proces', 'handeling' are valid nouns
patroon_lijst = regel.get("herkenbaar_patronen", [])
```

### 3. Test Case Updates

Create test to verify correct behavior:
```python
def test_proces_handelingsnaamwoord_allowed():
    """Verify that action nouns are allowed for PROCES category."""

    # These should PASS validation
    valid_proces_definitions = [
        "activiteit waarbij gegevens worden verzameld",
        "handeling die leidt tot een besluit",
        "proces waarin documenten worden beoordeeld",
        "registratie van persoonsgegevens in een systeem",
        "observatie door middel van directe waarneming"
    ]

    # These should FAIL validation (conjugated verbs)
    invalid_definitions = [
        "is een activiteit waarbij...",
        "heeft betrekking op een proces...",
        "wordt uitgevoerd door..."
    ]

    # Test implementation here
```

## Impact Analysis

### What Changes?
- **Documentation only** - clearer explanations
- **Comments in code** - better understanding
- **Test coverage** - explicit validation of the pattern

### What Stays the Same?
- **All validation logic** - already correct!
- **All prompt generation** - working as intended
- **All existing definitions** - remain valid

### Risk Assessment
- **Risk Level**: LOW
- **Breaking Changes**: NONE
- **User Impact**: Positive (clearer guidance)
- **Developer Impact**: Positive (less confusion)

## Conclusion

The "contradiction" is actually a **documentation clarity issue**, not a functional bug. The system correctly:

1. Requires definitions to start with nouns (STR-01) ✅
2. Prevents conjugated verbs at the start (ARAI-01) ✅
3. Allows action nouns for PROCES category (ESS-02) ✅

The solution is to **clarify the documentation** to explicitly state that:
- Handelingsnaamwoorden ARE nouns (zelfstandige naamwoorden)
- ARAI-01 refers to conjugated verbs, not nominalized forms
- PROCES definitions correctly use action nouns, which comply with all rules

## Recommendation

**Implement Option C: Linguistic Precision**

This requires only documentation updates and clarifying comments, no functional changes. The system is already working correctly; we just need to explain it better.

## Next Steps

1. Update documentation as specified above
2. Add clarifying comments to code
3. Create explicit test cases for handelingsnaamwoorden
4. Update user guidance in the UI if needed
5. Consider adding a tooltip/help text explaining the linguistic distinction

---

**Analysis Date**: 2025-11-07
**Analyst**: Claude Code
**Issue**: DEF-138
**Status**: Ready for Implementation