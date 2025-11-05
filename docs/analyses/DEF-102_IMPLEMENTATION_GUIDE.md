# DEF-102: Implementation Guide - Fix Blocking Contradictions

**Status:** Ready to implement
**Effort:** 3 uur
**Risk:** LOW (surgical fixes, proven exception pattern)

---

## 🎯 Het Probleem in 1 Zin

ESS-02 VEREIST "is een activiteit waarbij..." maar STR-01 + error_prevention VERBIEDEN starten met "is" → **ONMOGELIJK om valide PROCES definities te maken.**

---

## ✅ De Oplossing: Exception Clauses

Voeg **expliciete exception clauses** toe die zeggen: "ESS-02 ontologische markers OVERRIDEN de algemene verboden."

**Pattern:** Al 4× gebruikt in codebase ("tenzij", "uitzondering", "behalve")

---

## 📋 Wat Moet Je Aanpassen (5 Wijzigingen)

### 1️⃣ ESS-02: Add Exception Notice (PRIORITEIT 1)

**Waarom:** Maak duidelijk dat "is een activiteit" TOEGESTAAN is voor ontologische precisie

**Waar:** `src/services/prompts/modules/semantic_categorisation_module.py`

**Functie:** `_get_category_specific_guidance(categorie: str)`

**Lijn:** Voor regel 182 (in PROCES category block)

**Wat toevoegen:**
```python
"proces": """
⚠️ UITZONDERING - Ontologische Categorie Marking:
Voor PROCES categorieën MAG je starten met:
- "is een activiteit waarbij..."
- "is het proces waarin..."
Dit is de ENIGE uitzondering op STR-01 en forbidden starts.

**PROCES CATEGORIE - Focus op HANDELING en VERLOOP:**
Gebruik formuleringen zoals:
- 'is een activiteit waarbij...'
- 'is het proces waarin...'
...
```

**Waarom deze fix:**
- ESS-02 is TIER 1 regel (ontologische precisie is kritiek)
- Nederlandse grammatica VEREIST "is" voor procesdefinitiess
- ASTRA framework (bron van ESS-02) vereist dit patroon

---

### 2️⃣ STR-01: Add Exception Clause (PRIORITEIT 2)

**Waarom:** Voorkom dat STR-01 ESS-02 patronen blokkeert

**Waar:** `src/services/prompts/modules/structure_rules_module.py`

**Functie:** `_build_str01_rule()`

**Lijn:** Na regel 141 (na toetsvraag)

**Wat toevoegen:**
```python
rules.append("🔹 **STR-01 - definitie start met zelfstandig naamwoord**")
rules.append(
    "- De definitie moet starten met een zelfstandig naamwoord of naamwoordgroep, niet met een werkwoord."
)
rules.append(
    "- Toetsvraag: Begint de definitie met een zelfstandig naamwoord of naamwoordgroep, en niet met een werkwoord?"
)

# TOEVOEGEN:
rules.append("")
rules.append("⚠️ **UITZONDERING voor ESS-02 (Ontologische Categorie):**")
rules.append("Bij ontologische categorie marking MAG 'is een activiteit/proces/resultaat' gebruikt worden.")
rules.append("Dit is nodig voor ontologische precisie en overschrijft STR-01.")
rules.append("")

if self.include_examples:
    rules.append("  ✅ proces dat beslissers identificeert...")
```

**Waarom deze fix:**
- STR-01 is TIER 2 regel (structuur)
- ESS-02 is TIER 1 regel (ontologie) → TIER 1 wins
- Expliciete hiërarchie voorkomt verwarring

---

### 3️⃣ error_prevention: Modify Koppelwerkwoord Regel (PRIORITEIT 3)

**Waarom:** Voorkom dat error_prevention ESS-02 blokkeert

**Waar:** `src/services/prompts/modules/error_prevention_module.py`

**Functie:** `_build_basic_errors()`

**Lijn:** 147

**Wat wijzigen:**
```python
# VOOR:
"- ❌ Gebruik geen koppelwerkwoord aan het begin ('is', 'betekent', 'omvat')",

# NA:
"- ❌ Gebruik geen koppelwerkwoord aan het begin ('is', 'betekent', 'omvat'), tenzij vereist voor ontologische categorie (ESS-02)",
```

**Waarom deze fix:**
- Behoudt algemene regel (geen "is" voor vage definities)
- Maakt exception expliciet (ESS-02 patronen toegestaan)
- Consistent met bestaand "tenzij" patroon in codebase

---

### 4️⃣ error_prevention: Modify Containerbegrippen Regel (PRIORITEIT 4)

**Waarom:** "proces" en "activiteit" zijn VAGE containers (slecht) vs ONTOLOGISCHE markers (goed)

**Waar:** `src/services/prompts/modules/error_prevention_module.py`

**Functie:** `_build_basic_errors()`

**Lijn:** 150

**Wat wijzigen:**
```python
# VOOR:
"- ❌ Vermijd containerbegrippen ('proces', 'activiteit')",

# NA:
"- ❌ Vermijd vage containerbegrippen ('proces', 'activiteit'), behalve als ontologische marker (ESS-02: 'is een proces dat...', 'is een activiteit waarbij...')",
```

**Waarom deze fix:**
- Onderscheid tussen VAGE gebruik (❌ "proces dat plaatsvindt") vs SPECIFIEKE gebruik (✅ "is een activiteit waarbij gecontroleerd wordt...")
- Context matters: same word, different meaning
- ARAI-02 bedoeling was vage fillers verbieden, niet ontologische markers

---

### 5️⃣ error_prevention: Clarify Bijzinnen Regel (PRIORITEIT 5)

**Waarom:** "die", "waarbij" zijn SOMS nodig voor precisie, niet altijd verboden

**Waar:** `src/services/prompts/modules/error_prevention_module.py`

**Functie:** `_build_basic_errors()`

**Lijn:** 151

**Wat wijzigen:**
```python
# VOOR:
"- ❌ Vermijd bijzinnen zoals 'die', 'waarin', 'zoals'",

# NA:
"- ⚠️ Beperk relatieve bijzinnen ('die', 'waarin', 'waarbij'). Gebruik ALLEEN wanneer: (1) Nodig voor ontologische categorie (ESS-02), (2) Essentieel voor specificiteit. Prefereer zelfstandig naamwoord constructies.",
```

**Waarom deze fix:**
- Verandert ABSOLUTE verbod (❌) naar VOORKEURSREGEL (⚠️)
- Geeft VOORWAARDEN wanneer toegestaan
- Nederlandse juridische taal vereist soms bijzinnen voor precisie
- Grammar module leert al comma usage met bijzinnen → consistent maken

---

## 🎯 Prioritering & Volgorde

### Fase 1: Critical (1 uur)
1. ✅ **Wijziging #1** - ESS-02 exception notice
2. ✅ **Wijziging #2** - STR-01 exception clause

**Test na Fase 1:** Generate prompt voor begrip "registratie" (PROCES) → Check voor contradictions

### Fase 2: Important (1 uur)
3. ✅ **Wijziging #3** - error_prevention koppelwerkwoord
4. ✅ **Wijziging #4** - error_prevention containerbegrippen

**Test na Fase 2:** Generate prompts voor alle 4 categorieën (TYPE, PROCES, RESULTAAT, EXEMPLAAR)

### Fase 3: Polish (1 uur)
5. ✅ **Wijziging #5** - error_prevention bijzinnen clarificatie
6. ✅ **Integration test** - Volledige validatie flow
7. ✅ **Documentation update** - Update CLAUDE.md indien nodig

---

## 🧪 Test Strategy

### Unit Tests (per wijziging)

**Test 1: ESS-02 Exception Aanwezig**
```python
def test_ess02_exception_clause_present():
    """Verify ESS-02 exception clause in semantic categorisation."""
    module = SemanticCategorisationModule()
    module.initialize({})
    context = ModuleContext(begrip="test", enriched_context=..., config=...)
    context.set_metadata("ontologische_categorie", "proces")

    output = module.execute(context)

    assert "UITZONDERING" in output.content
    assert "is een activiteit waarbij" in output.content
    assert "Dit is de ENIGE uitzondering" in output.content
```

**Test 2: STR-01 Exception Aanwezig**
```python
def test_str01_exception_clause():
    """Verify STR-01 has exception for ESS-02."""
    module = StructureRulesModule()
    module.initialize({})
    context = ModuleContext(...)

    output = module.execute(context)

    assert "UITZONDERING voor ESS-02" in output.content
    assert "ontologische categorie marking MAG" in output.content
```

**Test 3: error_prevention Modifications**
```python
def test_error_prevention_exceptions():
    """Verify error prevention has ESS-02 exceptions."""
    module = ErrorPreventionModule()
    module.initialize({})
    context = ModuleContext(...)

    output = module.execute(context)

    # Check "tenzij vereist voor ontologische categorie"
    assert "tenzij vereist voor ontologische categorie" in output.content
    # Check "behalve als ontologische marker"
    assert "behalve als ontologische marker" in output.content
    # Check bijzinnen clarification
    assert "Beperk relatieve bijzinnen" in output.content
```

### Integration Test

**Test 4: No Blocking Contradictions**
```python
def test_no_blocking_contradictions_in_full_prompt():
    """Verify no blocking contradictions in generated prompt."""
    orchestrator = PromptOrchestrator()
    # ... register all modules

    prompt = orchestrator.build_prompt(
        begrip="registratie",
        context=EnrichedContext(
            organisatorische_context=["Politie"],
            juridische_context=["Strafrecht"]
        ),
        config=UnifiedGeneratorConfig()
    )

    # If ESS-02 requires "is", must have exception in STR-01/error_prevention
    if "is een activiteit waarbij" in prompt or "is het proces" in prompt:
        assert "UITZONDERING" in prompt or "tenzij" in prompt, \
            "ESS-02 'is' usage without exception clause"

    # Container terms must have exemption
    if "❌ Vermijd containerbegrippen ('proces'" in prompt:
        assert "behalve" in prompt or "ontologische marker" in prompt, \
            "Container terms forbidden without exemption"
```

---

## ✅ Success Criteria

### Functioneel
- [ ] Prompt voor "registratie" (PROCES) bevat geen contradictions
- [ ] Alle 4 ontologische categorieën genereren valide prompts
- [ ] GPT-4 kan "is een activiteit waarbij..." gebruiken zonder validatie errors
- [ ] Ontologische precisie behouden (>95% consistency)

### Technisch
- [ ] Alle 5 wijzigingen geïmplementeerd
- [ ] 4 unit tests passing
- [ ] 1 integration test passing
- [ ] Pre-commit hooks passing
- [ ] No regressions in existing tests

### Business
- [ ] PROCES definities mogelijk (40% van use cases)
- [ ] ASTRA framework compliance (ontologische precisie)
- [ ] Nederlandse juridische grammatica correct

---

## 📊 Risk Analysis

### Risico's

| Risico | Impact | Likelihood | Mitigatie |
|--------|--------|------------|-----------|
| Exception clause te breed | MED | LOW | Test met edge cases, specifieke formulering |
| GPT-4 interpreteert exception verkeerd | MED | LOW | Expliciete voorbeelden toevoegen |
| Regression in andere categorieën | HIGH | LOW | Integration tests voor alle 4 categorieën |
| Exception pattern inconsistent | LOW | MED | Gebruik bestaand "tenzij" patroon |

### Waarom LOW Risk

1. **Pattern is proven** - Al 4× gebruikt in codebase (INT-08, Grammar, etc.)
2. **Surgical fixes** - 5-10 lijnen per module, geen architectuur wijzigingen
3. **Backwards compatible** - Geen breaking changes, alleen verduidelijkingen
4. **Testable** - Concrete success criteria, meetbare output

---

## 🎯 Deliverables Checklist

### Code Changes
- [ ] `semantic_categorisation_module.py` - Exception notice toegevoegd
- [ ] `structure_rules_module.py` - Exception clause toegevoegd
- [ ] `error_prevention_module.py` - 3 regel modificaties

### Tests
- [ ] 4 unit tests geschreven en passing
- [ ] 1 integration test geschreven en passing
- [ ] Regression tests passing (bestaande test suite)

### Documentation
- [ ] Deze implementation guide (✅ DONE)
- [ ] Code comments toegevoegd bij exceptions
- [ ] CLAUDE.md update (indien nodig)

### Validation
- [ ] Prompt gegenereerd voor alle 4 categorieën
- [ ] Geen contradictions gedetecteerd
- [ ] GPT-4 test: definitie genereren met nieuwe prompt

---

## 💡 Pro Tips

1. **Test incrementeel:** Na elke wijziging, genereer een prompt en check visueel
2. **Gebruik diff:** Check dat je ALLEEN de bedoelde regels wijzigt
3. **Pre-commit:** Run `pre-commit run --all-files` na elke wijziging
4. **Backup:** Commit na elke succesvolle wijziging (niet alles tegelijk)
5. **Visual check:** Gebruik `print(prompt)` om de output te inspecteren

---

## 📞 Hulp Nodig?

**Blockers:**
- Exception clause syntax onduidelijk? → Check INT-08 module voor voorbeeld
- Test faalt? → Check `docs/analyses/DEF-102_INJECTION_CALL_STACK.md` voor call stack
- Merge conflict? → Wijzigingen zijn in verschillende functies, geen conflicts verwacht

**Resources:**
- Architectuur map: `docs/analyses/DEF-102_ARCHITECTURE_MAP.md`
- Forensic analysis: `docs/analyses/DEF-102_CONTRADICTION_FORENSIC_ANALYSIS.md`
- Call stack trace: `docs/analyses/DEF-102_INJECTION_CALL_STACK.md`

---

**Ready to implement!** Start met wijziging #1 (ESS-02 exception), test, dan volgende. 🚀
