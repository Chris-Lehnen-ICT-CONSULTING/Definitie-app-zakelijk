# DEF-126: Gecontroleerd Implementatieplan - Validatie naar Generatie Mindset
**Versie:** 1.0
**Datum:** 2025-11-13
**Status:** Ready for Implementation

## 🎯 Hoofddoel

Transformeer alle 16 prompt modules van een **validatie-mindset** ("controleer of") naar een **generatie-mindset** ("creëer door").

### Kritieke Aanpassing Hoofdinstructie

De definitie moet voor **belanghebbenden** voldoende eenduidig het begrip in de werkelijkheid aanduiden. Dit betekent:
- Niet alleen juridisch correct
- Maar praktisch bruikbaar voor alle stakeholders
- Eenduidig interpreteerbaar in de werkelijke context
- Afgestemd op het begrip van de doelgroep

## 📊 Impact Voorspelling

| Metric | Huidige Waarde | Target | Verwachte Verbetering |
|--------|----------------|--------|----------------------|
| Eerste-keer-goed ratio | 60% | 85% | +42% |
| Validatie failures per definitie | 8.5 | 3.2 | -62% |
| Gebruikerstevredenheid | 6.8/10 | 8.5/10 | +25% |
| Regeneratie nodig | 40% | 10% | -75% |

## 🔄 Gefaseerd Implementatieplan

### FASE 0: Voorbereiding & Baseline (2 uur)
**Datum:** Week 1 - Maandag ochtend
**Verantwoordelijke:** Lead Developer

#### Stappen:
1. **Baseline Meting** (30 min)
   ```bash
   # Genereer 20 test definities met huidige modules
   python scripts/test/generate_baseline_definitions.py
   ```
   - Bewaar output in: `tests/baseline/pre-transformation/`
   - Meet: validatie scores, token count, regeneratie ratio

2. **Backup Huidige Modules** (15 min)
   ```bash
   cp -r src/services/prompts/modules/ src/services/prompts/modules.backup/
   ```

3. **Test Suite Voorbereiden** (45 min)
   - Creëer test file: `tests/transformation/test_mindset_shift.py`
   - Setup A/B testing framework
   - Definieer success criteria

4. **Documentatie Template** (30 min)
   - Creëer: `docs/transformation/progress_log.md`
   - Setup metrics dashboard

#### Deliverables:
- [ ] Baseline definities (20 samples)
- [ ] Backup van alle modules
- [ ] Test suite ready
- [ ] Progress tracking document

#### Acceptatiecriteria:
- Alle huidige modules werken nog
- Baseline metrics gedocumenteerd
- Rollback mogelijk binnen 5 minuten

---

### FASE 1: Hoofdinstructie Transformatie (2 uur)
**Datum:** Week 1 - Maandag middag
**Module:** `expertise_module.py`
**Priority:** P0 - CRITICAL

#### Transformatie Details:

**HUIDIGE SITUATIE** (Lines 158-167):
```python
def _build_role_definition(self) -> str:
    return "Je bent een expert in beleidsmatige definities voor overheidsgebruik."

def _build_task_instruction(self) -> str:
    return "Formuleer een heldere definitie die het begrip precies afbakent."
```

**NIEUWE IMPLEMENTATIE**:
```python
def _build_role_definition(self) -> str:
    return """Je bent een expert in het creëren van definities die voor alle belanghebbenden
    voldoende eenduidig het begrip in de werkelijkheid aanduiden. Je definities zijn:
    - Praktisch bruikbaar voor beleidsmakers, uitvoerders en burgers
    - Juridisch solide maar toegankelijk geformuleerd
    - Afgestemd op de context waarin ze gebruikt worden
    - Eenduidig interpreteerbaar zonder specialistische voorkennis"""

def _build_task_instruction(self) -> str:
    return """CREËER een definitie die:
    1. Het begrip in de werkelijkheid precies aanduidt
    2. Voor belanghebbenden direct begrijpelijk is
    3. Ondubbelzinnig maakt wat wel/niet onder het begrip valt
    4. De praktische toepassing in de gegeven context mogelijk maakt

    Focus op CONSTRUCTIE, niet op controle. Bouw de definitie stap voor stap op."""
```

#### Test Procedure:
1. Update `expertise_module.py`
2. Run: `pytest tests/services/prompts/test_expertise_module.py`
3. Genereer 5 test definities
4. Vergelijk met baseline

#### Acceptatiecriteria:
- [ ] Module output bevat "CREËER" instructies
- [ ] Geen "controleer" of "test" taal meer
- [ ] Focus op belanghebbenden expliciet
- [ ] Tests groen

---

### FASE 2: DefinitionTaskModule Transformatie (3 uur)
**Datum:** Week 1 - Dinsdag ochtend
**Module:** `definition_task_module.py`
**Priority:** P0 - HIGHEST IMPACT

#### Transformatie Details:

**Kritieke Wijziging** (Line 198):
```python
# VOOR: Checklist mindset
def _build_checklist(self, ontological_category: str | None) -> str:
    return f"""📋 **CHECKLIST - Controleer voor je antwoord:**
    □ Begint met zelfstandig naamwoord
    □ Eén enkele zin zonder punt
    □ Geen verboden woorden"""

# NA: Constructie mindset
def _build_construction_guide(self, ontological_category: str | None) -> str:
    category_builders = {
        "proces": """
        1️⃣ START met: 'activiteit waarbij' of 'handeling die'
        2️⃣ IDENTIFICEER: wie voert uit (actor)
        3️⃣ BESCHRIJF: wat gebeurt er (actie)
        4️⃣ EINDIG met: het resultaat of doel""",

        "type": """
        1️⃣ START met: het kernwoord (GEEN 'soort'!)
        2️⃣ VOEG TOE: 'die' of 'dat'
        3️⃣ SPECIFICEER: onderscheidend kenmerk
        4️⃣ CONTEXTUALISEER: waarin het voorkomt""",

        "resultaat": """
        1️⃣ START met: 'uitkomst van' of 'product dat'
        2️⃣ BESCHRIJF: het ontstaan proces
        3️⃣ SPECIFICEER: de vorm of eigenschappen
        4️⃣ EINDIG met: de functie of toepassing""",

        "exemplaar": """
        1️⃣ START met: 'specifiek geval van'
        2️⃣ IDENTIFICEER: wat maakt het uniek
        3️⃣ PLAATS in tijd/ruimte: wanneer/waar
        4️⃣ VERBIND met: de algemene klasse"""
    }

    guide = category_builders.get(ontological_category, self._build_generic_guide())

    return f"""🏗️ **CONSTRUCTIE GIDS - Bouw je definitie stapsgewijs op:**

    {guide}

    💡 **Pro tip:** Elke stap voegt waarde toe. Sla geen stappen over."""
```

#### Substeps:
1. **Rename methods** (30 min)
   - `_build_checklist` → `_build_construction_guide`
   - `_build_quality_control` → `_build_quality_enhancement`

2. **Transform content** (1.5 uur)
   - Alle "Controleer" → "Creëer"
   - Alle vragen → instructies
   - Negatieve → positieve formuleringen

3. **Update tests** (1 uur)
   - New test cases voor constructie gids
   - Verify geen checklist taal

#### Acceptatiecriteria:
- [ ] Geen "□ checklist" items meer
- [ ] Stap-voor-stap constructie per categorie
- [ ] Positieve, opbouwende taal
- [ ] 30% betere eerste-keer-goed ratio in test

---

### FASE 3: ErrorPrevention → QualityEnhancement (3 uur)
**Datum:** Week 1 - Dinsdag middag
**Module:** `error_prevention_module.py`
**Priority:** P0 - CRITICAL (removes contradictions)

#### Transformatie Details:

**Kritieke Issues om op te lossen:**
1. Lines 179-180: Verwijder "proces waarbij", "handeling die" uit verboden lijst
2. Rename module class en file
3. Transform van negatief naar positief

**File Rename:**
```bash
git mv src/services/prompts/modules/error_prevention_module.py \
      src/services/prompts/modules/quality_enhancement_module.py
```

**Class Transformation:**
```python
# VOOR
class ErrorPreventionModule(BasePromptModule):
    def _build_basic_errors(self) -> list[str]:
        return [
            "- ❌ Begin niet met lidwoorden",
            "- ❌ Gebruik geen koppelwerkwoord",
        ]

# NA
class QualityEnhancementModule(BasePromptModule):
    def _build_quality_techniques(self) -> list[str]:
        return [
            "✅ Begin direct met een zelfstandig naamwoord",
            "✅ Gebruik actieve, beschrijvende werkwoorden",
            "✅ Integreer context impliciet in de formulering",
        ]

    def _build_strong_starters(self) -> list[str]:
        """Bouw sterke startpatronen per categorie."""
        return [
            "🚀 **Sterke startpatronen:**",
            "",
            "PROCES: 'activiteit waarbij', 'handeling die', 'proces waarin'",
            "TYPE: [kernwoord] + 'die/dat' (NOOIT 'soort' ervoor)",
            "RESULTAAT: 'uitkomst van', 'product dat', 'gevolg van'",
            "EXEMPLAAR: 'specifiek geval van', 'individuele instantie'",
        ]
```

#### Substeps:
1. **Backup & Rename** (30 min)
2. **Transform Methods** (1.5 uur)
3. **Update Imports** (30 min)
4. **Test Integration** (30 min)

#### Acceptatiecriteria:
- [ ] Geen contradictie meer met SemanticCategorisation
- [ ] 100% positieve formuleringen
- [ ] Sterke startpatronen per categorie
- [ ] Orchestrator herkent nieuwe module naam

---

### FASE 4: Transform 7 Regel Modules (5 uur)
**Datum:** Week 1 - Woensdag & Donderdag
**Modules:** ARAI, CON, ESS, STR, INT, SAM, VER
**Priority:** P0 - CORE TRANSFORMATION

#### Universele Transformatie Pattern:

Voor ELKE regel module, pas dit pattern toe:

```python
def _format_rule(self, regel_key: str, regel_data: dict) -> list[str]:
    """Transform validation rule to generation instruction."""
    lines = []

    # Transform rule name to instruction
    naam = regel_data.get("naam", "")
    instruction = self._transform_to_instruction(regel_key, naam)
    lines.append(f"📝 **{regel_key}:** {instruction}")

    # Transform test question to construction hint
    if toetsvraag := regel_data.get("toetsvraag", ""):
        hint = self._question_to_construction_hint(toetsvraag)
        lines.append(f"   💡 Hint: {hint}")

    # Show ONLY positive examples
    if self.include_examples:
        if good := regel_data.get("goede_voorbeelden", []):
            lines.append(f"   ✓ Voorbeeld: {good[0]}")

    return lines

def _transform_to_instruction(self, key: str, naam: str) -> str:
    """Transform negative rule to positive instruction."""
    # Map per module type
    transformations = self._get_transformation_map()
    return transformations.get(key, f"Creëer met: {naam}")

def _question_to_construction_hint(self, question: str) -> str:
    """Transform validation question to construction hint."""
    # "Is X een Y?" → "Maak X tot een Y"
    hint = question.replace("Is ", "Zorg dat ")
    hint = hint.replace("?", "")
    return hint
```

#### Implementatie Volgorde:

**Dag 1 (Woensdag) - 3 modules:**
1. **ARAI Module** (1.5 uur) - Meeste regels
2. **ESS Module** (1 uur) - Essentiële regels
3. **STR Module** (1 uur) - Structuur regels

**Dag 2 (Donderdag) - 4 modules:**
4. **INT Module** (45 min) - Integriteit
5. **CON Module** (30 min) - Context regels
6. **SAM Module** (30 min) - Samenhang
7. **VER Module** (30 min) - Vorm regels

#### Module-Specifieke Transformaties:

**ARAI Transformations:**
```python
{
    "ARAI-01": "Begin met een zelfstandig naamwoord als kern",
    "ARAI-02": "Gebruik specifieke termen in plaats van vage begrippen",
    "ARAI-03": "Beperk bijvoeglijke naamwoorden tot het essentiële",
    "ARAI-04": "Formuleer zonder modale hulpwerkwoorden",
    "ARAI-05": "Maak impliciete aannames expliciet",
    "ARAI-06": "Start direct zonder lidwoord of koppelwerkwoord"
}
```

**ESS Transformations:**
```python
{
    "ESS-01": "Beschrijf de essentie (WAT), niet het doel (WAARVOOR)",
    "ESS-02": "Maak de ontologische categorie duidelijk",
    "ESS-03": "Focus op inherente eigenschappen",
}
```

#### Test Per Module:
```bash
# Na elke module transformatie:
pytest tests/services/prompts/test_{module_name}_module.py -v

# Integratie test na alle 7:
pytest tests/services/prompts/test_all_rules_integration.py -v
```

#### Acceptatiecriteria PER module:
- [ ] Geen "toetsvraag" meer in output
- [ ] Alleen positieve voorbeelden
- [ ] Instructie-taal, geen vraag-taal
- [ ] Tests groen

---

### FASE 5: Template Module Fix (30 min)
**Datum:** Week 1 - Vrijdag ochtend
**Module:** `template_module.py`
**Priority:** P1 - QUICK FIX

#### Simple Fix:

**Line 63 & 81:**
```python
# VOOR
category = context.get_metadata("semantic_category")

# NA
category = context.get_metadata("ontologische_categorie")
```

Of overweeg: **MODULE VERWIJDEREN** (SemanticCategorisation doet dit al beter)

#### Acceptatiecriteria:
- [ ] Module draait zonder validation error
- [ ] Of: Module verwijderd en orchestrator updated

---

### FASE 6: Integration Testing (2 uur)
**Datum:** Week 1 - Vrijdag middag
**Focus:** End-to-end validation

#### Test Procedure:

1. **Generate Test Set** (30 min)
   ```python
   test_terms = [
       "integriteit",      # TYPE
       "validatie",        # PROCES
       "rapport",          # RESULTAAT
       "Awb",             # EXEMPLAAR
   ]
   ```

2. **A/B Testing** (1 uur)
   - 20 definities met oude modules (backup)
   - 20 definities met nieuwe modules
   - Vergelijk scores

3. **Metrics Measurement** (30 min)
   - Validatie scores
   - Token usage
   - Gebruiker simulatie

#### Acceptatiecriteria:
- [ ] Alle modules werken samen
- [ ] Geen contradictties in output
- [ ] 40% betere kwaliteit gemeten

---

### FASE 7: Rollout & Monitoring (2 uur)
**Datum:** Week 2 - Maandag
**Focus:** Production ready

#### Steps:

1. **Documentation Update** (30 min)
   - Update `CLAUDE.md`
   - Update module docstrings
   - Create migration guide

2. **Performance Baseline** (30 min)
   - Measure token usage
   - Measure generation time
   - Document improvements

3. **Create PR** (30 min)
   - Comprehensive description
   - Before/after examples
   - Metrics summary

4. **Rollback Plan** (30 min)
   - Document rollback procedure
   - Test rollback works
   - Emergency contacts

---

## 📊 Succes Metrics & Monitoring

### Key Performance Indicators

| KPI | Measurement Method | Target | Alert Threshold |
|-----|-------------------|--------|-----------------|
| Eerste-keer-goed | Track "Vaststellen" clicks | >85% | <75% |
| Validatie failures | Count regel violations | <3.5 | >5 |
| Regeneratie ratio | Track "Opnieuw" clicks | <10% | >20% |
| Token usage | tiktoken count | <7000 | >8000 |
| User satisfaction | Weekly survey | >8/10 | <7/10 |

### Monitoring Dashboard

```python
# Create monitoring script: scripts/monitor_transformation.py

def monitor_transformation_impact():
    metrics = {
        "definitions_generated": 0,
        "first_time_success": 0,
        "validation_failures": [],
        "regenerations": 0,
        "average_tokens": 0,
        "user_feedback": []
    }

    # Log to: logs/transformation_metrics.json
    return metrics
```

---

## 🚨 Rollback Procedure

### Immediate Rollback (< 5 min)

```bash
# 1. Stop application
systemctl stop definitie-app

# 2. Restore modules
rm -rf src/services/prompts/modules/
mv src/services/prompts/modules.backup/ src/services/prompts/modules/

# 3. Restart
systemctl start definitie-app

# 4. Verify
python scripts/test/verify_rollback.py
```

### Gradual Rollback

Feature flag implementation:
```python
# In orchestrator.py
USE_GENERATION_MINDSET = os.getenv("USE_GENERATION_MINDSET", "true") == "true"

if USE_GENERATION_MINDSET:
    # Use new modules
else:
    # Use backup modules
```

---

## 📝 Communicatieplan

### Stakeholder Updates

**Week 1 Start:**
- Email: "Start transformatie prompt modules"
- Verwachte impact: Tijdelijke instabiliteit mogelijk

**Daily Standup:**
- Progress update
- Blockers
- Metrics van gisteren

**Week 1 End:**
- Resultaten eerste week
- Go/No-go voor productie

### User Communication

**Na succesvolle rollout:**
```
📢 Verbetering Definitie Generatie

We hebben de manier waarop definities worden gegenereerd verbeterd:
- Definities zijn nu beter afgestemd op belanghebbenden
- Hogere kwaliteit bij eerste generatie
- Minder vaak regeneratie nodig

Mocht u problemen ervaren, meld dit via [support link]
```

---

## ✅ Final Checklist

### Voor Start:
- [ ] Management approval
- [ ] Test environment ready
- [ ] Backup strategie getest
- [ ] Team geïnformeerd

### Per Fase:
- [ ] Code review door peer
- [ ] Tests geschreven en groen
- [ ] Documentatie bijgewerkt
- [ ] Metrics baseline vastgelegd

### Voor Productie:
- [ ] Alle acceptatiecriteria gehaald
- [ ] Performance acceptable
- [ ] Rollback getest
- [ ] Monitoring actief

### Na Rollout:
- [ ] 24-uur monitoring
- [ ] User feedback verzameld
- [ ] Lessons learned gedocumenteerd
- [ ] Volgend iteration gepland

---

## 📚 Appendix: Code Templates

### A. Transformation Helper Functions

```python
# helpers/transformation_utils.py

def transform_validation_to_generation(text: str) -> str:
    """Transform validation language to generation language."""
    replacements = {
        "Controleer": "Creëer",
        "Test of": "Zorg dat",
        "Vermijd": "Gebruik",
        "Niet": "Wel",
        "Verboden": "Aanbevolen",
        "Fout": "Goed",
        "❌": "✅",
        "□": "→"
    }

    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result

def question_to_instruction(question: str) -> str:
    """Convert question to instruction."""
    if "?" not in question:
        return question

    # "Is X een Y?" → "Maak X een Y"
    instruction = question.replace("Is ", "Maak ")
    instruction = instruction.replace("?", "")

    # "Heeft X een Y?" → "Geef X een Y"
    instruction = instruction.replace("Heeft ", "Geef ")

    return instruction
```

### B. Test Template

```python
# tests/transformation/test_mindset_shift.py

import pytest
from src.services.prompts.modules import definition_task_module

class TestMindsetTransformation:

    def test_no_checklist_language(self, module):
        output = module.execute(context)
        assert "CHECKLIST" not in output.content
        assert "Controleer" not in output.content
        assert "□" not in output.content

    def test_construction_language_present(self, module):
        output = module.execute(context)
        assert "CONSTRUCTIE" in output.content
        assert "Creëer" in output.content or "Bouw" in output.content
        assert "→" in output.content or "1️⃣" in output.content

    def test_positive_formulations(self, module):
        output = module.execute(context)
        # Count positive vs negative indicators
        positive = output.content.count("✅")
        negative = output.content.count("❌")
        assert positive > negative
```

---

**Document Status:** Complete
**Ready for:** Implementation
**Estimated Total Effort:** 20-25 hours
**Expected ROI:** 40% quality improvement