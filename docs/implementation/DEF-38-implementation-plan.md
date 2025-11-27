# DEF-38 Implementation Plan: Ontologische Promptinjecties Verbeteringen

**Issue:** DEF-38 - Kritieke Issues in Ontologische Promptinjecties
**Status:** In Progress
**Priority:** P2
**Effort:** ~14 uur
**Risk:** LAAG

---

## Executive Summary

Na multi-agent analyse (2025-11-27) is vastgesteld dat DEF-38 de primaire issue is voor ontologische categorie verbeteringen. DEF-138 is gesloten als "Done" omdat de kernfunctionaliteit al geïmplementeerd is.

### Huidige Status

| Criterium | Oorspronkelijk | Na DEF-138 | Target |
|-----------|----------------|------------|--------|
| Quality Score | 5.2/10 | 6.5/10 | **7.5/10** |
| Issues opgelost | 0/5 | 2/5 | **5/5** |
| BFO compliance | 0% | 0% | **80%+** |

---

## Remaining Tasks

### Task 1: Type/Instance Disambiguation (4 uur)

**Doel:** Voorkom dat proper names (eigennamen) als TYPE worden gecategoriseerd.

**Probleem:**
- "Hoge Raad" → Wordt nu mogelijk als TYPE gezien
- Zou EXEMPLAAR moeten zijn (er is maar één Hoge Raad)

**Implementatie:**

```python
# Toevoegen aan semantic_categorisation_module.py:203-231 (TYPE sectie)

"""
⚠️ TYPE vs PROPER NAME DISAMBIGUATION:
- TYPE: "rechtbank die functioneert als..." (class met meerdere instances)
- PROPER NAME (EXEMPLAAR): "Hoge Raad" → behandel als EXEMPLAAR, niet TYPE

TEST: Vraag jezelf: "Kunnen er MEERDERE van dit begrip bestaan?"
- JA → TYPE ("rechtbank" → er zijn meerdere rechtbanken)
- NEE → EXEMPLAAR ("Hoge Raad" → er is maar één)
"""
```

**Acceptance Criteria:**
- [ ] Disambiguation tekst toegevoegd aan TYPE sectie
- [ ] Test case: `test_proper_name_is_exemplaar()`
- [ ] Documentatie updated

---

### Task 2: BFO Foundations (6 uur)

**Doel:** Voeg Basic Formal Ontology (BFO) principes toe voor formele grounding.

**Probleem:**
- Huidige categorisatie mist ontologische fundering
- Geen duidelijke continuant vs occurrent distinctie

**Implementatie:**

```python
# Toevoegen als nieuwe sectie in _build_ess02_section() na base_section

BFO_FOUNDATIONS = """
📐 ONTOLOGISCHE GRONDSLAGEN (gebaseerd op BFO):

1. CONTINUANTS (bestaan door de tijd heen):
   - TYPE: Universele klasse (bijv. "rechtbank")
   - EXEMPLAAR: Particulier individu (bijv. "Rechtbank Den Haag")

2. OCCURRENTS (ontvouwen zich in de tijd):
   - PROCES: Heeft temporele delen (begin, midden, eind)
   - RESULTAAT: Eindtoestand/product van een proces

KEUZETEST:
- Kan het TEGELIJKERTIJD volledig bestaan? → CONTINUANT (TYPE/EXEMPLAAR)
- Heeft het FASEN die elkaar opvolgen? → OCCURRENT (PROCES)
- Is het de EINDTOESTAND van iets? → RESULTAAT
"""
```

**Acceptance Criteria:**
- [ ] BFO foundations sectie toegevoegd
- [ ] Keuzetest geïntegreerd
- [ ] Test case: `test_bfo_categorization_hints()`

---

### Task 3: PROCES/RESULTAAT Boundary (2 uur)

**Doel:** Verduidelijk de grens tussen PROCES en RESULTAAT voor ambigue begrippen.

**Probleem:**
- "registratie" → Is dit een PROCES (de handeling) of RESULTAAT (het document)?
- "verlening" → Is dit een PROCES of RESULTAAT?

**Implementatie:**

```python
# Toevoegen aan base_section (regel 136-147)

"""
⚠️ DING vs DOEN TEST (PROCES vs RESULTAAT):
Vraag: "Kan dit PLAATSVINDEN of BESTAAN?"
- "Het vindt PLAATS" → PROCES (bijv. "registratie" als handeling)
- "Het BESTAAT" → RESULTAAT (bijv. "registratie" als document/record)

VOORBEELDEN:
- "registratie" (de handeling) → PROCES: "activiteit waarbij..."
- "registratie" (het document) → RESULTAAT: "resultaat van..."
"""
```

**Acceptance Criteria:**
- [ ] "DING vs DOEN" test toegevoegd
- [ ] Voorbeelden voor ambigue begrippen
- [ ] Test case: `test_proces_resultaat_disambiguation()`

---

### Task 4: EXEMPLAAR "Unieke Kenmerken" Fix (1 uur)

**Doel:** Verwijder misleidende "unieke kenmerken" instructie.

**Probleem:**
- Regel 262: "Wat dit exemplaar UNIEK maakt (identificerende kenmerken)"
- Dit is verwarrend - EXEMPLAAR gaat over IDENTIFICATIE, niet uniciteit

**Implementatie:**

```python
# Wijzig regel 260-263 in EXEMPLAAR sectie

# VOOR:
"""
VERVOLG met:
- Van welke ALGEMENE KLASSE dit een exemplaar is
- Wat dit exemplaar UNIEK maakt (identificerende kenmerken)
- WANNEER/WAAR het voorkomt (contextualisering)
"""

# NA:
"""
VERVOLG met:
- Van welke ALGEMENE KLASSE dit een exemplaar is
- IDENTIFICERENDE kenmerken (datum, locatie, naam)
- WANNEER/WAAR het voorkomt (contextualisering)
"""
```

**Acceptance Criteria:**
- [ ] "UNIEK" vervangen door "IDENTIFICERENDE"
- [ ] Geen semantische wijziging in voorbeelden
- [ ] Bestaande tests blijven slagen

---

## Implementation Schedule

```
Week 1 (8 uur)
├── Maandag: Task 1 - Type/Instance disambiguation (4u)
│   ├── Implementatie (2u)
│   ├── Tests (1u)
│   └── Documentatie (1u)
│
└── Dinsdag-Woensdag: Task 2 - BFO foundations (4u van 6u)
    ├── Research BFO principes (1u)
    ├── Implementatie sectie (2u)
    └── Integratie in module (1u)

Week 2 (6 uur)
├── Donderdag: Task 2 - BFO foundations (2u remaining)
│   ├── Tests (1u)
│   └── Documentatie (1u)
│
├── Vrijdag: Task 3 - PROCES/RESULTAAT boundary (2u)
│   ├── Implementatie (1u)
│   └── Tests + docs (1u)
│
└── Vrijdag: Task 4 - EXEMPLAAR fix (1u)
    └── Simple text change + verify tests

Week 2 (slot): Validatie (1u)
├── Full test suite run
├── Manual QA check
└── Update Linear issue
```

---

## Test Strategy

### Unit Tests (Nieuw)

```python
# tests/unit/test_def38_improvements.py

def test_proper_name_is_exemplaar():
    """Proper names should be categorized as EXEMPLAAR."""
    assert categorize("Hoge Raad") == "EXEMPLAAR"
    assert categorize("Rechtbank Den Haag") == "EXEMPLAAR"

def test_generic_type_is_type():
    """Generic classes should be categorized as TYPE."""
    assert categorize("rechtbank") == "TYPE"
    assert categorize("document") == "TYPE"

def test_bfo_categorization_hints():
    """BFO hints should be present in guidance."""
    guidance = get_bfo_foundations()
    assert "CONTINUANT" in guidance
    assert "OCCURRENT" in guidance

def test_proces_resultaat_disambiguation():
    """Ambiguous terms should have disambiguation guidance."""
    guidance = get_base_section()
    assert "DING vs DOEN" in guidance
    assert "registratie" in guidance
```

### Integration Tests

```python
# tests/integration/test_def38_e2e.py

def test_full_categorization_flow():
    """Test complete flow from UI to generation."""
    # Test PROCES
    result = generate_definition("observatie", category="proces")
    assert result.startswith(("activiteit", "handeling", "proces"))

    # Test TYPE
    result = generate_definition("rechtbank", category="type")
    assert not result.startswith(("soort", "type", "categorie"))

    # Test EXEMPLAAR (proper name)
    result = generate_definition("Hoge Raad", category="exemplaar")
    assert "specifiek" in result.lower() or "exemplaar" in result.lower()
```

---

## Risk Assessment

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| Breaking existing tests | LAAG | Alleen additieve changes |
| Token budget impact | LAAG | BFO sectie is ~100 tokens |
| LLM confusion | LAAG | Duidelijke formatting |
| User confusion | MEDIUM | Goede documentatie |

---

## Success Criteria

### Quality Score Target: 7.5/10

| Criterium | Oorspronkelijk | Target | Measurement |
|-----------|----------------|--------|-------------|
| PROCES guidance | 4.9/10 | 7.0/10 | Manual review |
| TYPE guidance | 5.5/10 | 7.5/10 | Disambiguation test |
| EXEMPLAAR guidance | 4.8/10 | 7.0/10 | Instance detection |
| RESULTAAT guidance | 6.0/10 | 7.5/10 | Boundary test |
| BFO compliance | 0% | 80% | Formal ontology check |

### Definition of Done

- [ ] Alle 4 tasks geïmplementeerd
- [ ] Alle nieuwe tests slagen
- [ ] Bestaande tests blijven slagen (geen regressie)
- [ ] Documentatie updated
- [ ] Code review completed
- [ ] Quality score gemeten: ≥7.5/10

---

## Related Issues

- **DEF-138** (Closed - Done): Superseded, kernfunctionaliteit geïmplementeerd
- **DEF-40**: Optimaliseer category-specific prompt injecties (wacht op DEF-38)
- **DEF-139**: Improve Ontological Category Detection (gerelateerd)

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/services/prompts/modules/semantic_categorisation_module.py` | Tasks 1-4 |
| `tests/unit/test_def38_improvements.py` | New test file |
| `tests/integration/test_def38_e2e.py` | New test file |
| `docs/implementation/DEF-38-implementation-plan.md` | This document |

---

*Plan created: 2025-11-27*
*Generated by: Multi-agent conflict analysis*
