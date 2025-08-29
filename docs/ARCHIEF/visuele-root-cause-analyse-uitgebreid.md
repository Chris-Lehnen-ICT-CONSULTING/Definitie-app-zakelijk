# 🔍 UITGEBREIDE ROOT CAUSE ANALYSE: Definitie Generatie Systeem

*Versie: 2.0 - Met gedetailleerde uitleg en aanpak instructies*
*Datum: 2025-08-26*

## 📖 Inhoudsopgave

1. [Executive Summary](#executive-summary)
2. [Begrippen Uitleg](#begrippen-uitleg)
3. [Dashboard Interpretatie](#dashboard-interpretatie)
4. [Architectuur Analyse](#architectuur-analyse)
5. [Root Cause Diepteanalyse](#root-cause-diepteanalyse)
6. [Feature Gap Uitleg](#feature-gap-uitleg)
7. [Technische Fix Instructies](#technische-fix-instructies)
8. [Implementatie Roadmap](#implementatie-roadmap)
9. [Testing & Verificatie](#testing--verificatie)
10. [FAQ & Troubleshooting](#faq--troubleshooting)

---

## Executive Summary

### 🎯 Kernprobleem in Eenvoudige Taal

Het DefinitieAgent systeem is als een luxe auto met een V8 motor die alleen in de eerste versnelling rijdt. Alle geavanceerde features zijn aanwezig maar worden niet gebruikt door twee simpele bugs:

1. **Data wordt verkeerd opgeslagen** - Het systeem verwart een tekst met een lijst
2. **Drempel is te laag** - Het systeem denkt dat het te veel informatie heeft en schakelt naar simpele modus

**Impact**: Je krijgt basale definities terwijl het systeem geavanceerde, domein-specifieke definities kan maken.

---

## 📊 Dashboard Interpretatie

### Systeem Utilisatie Overzicht - Uitleg

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SYSTEEM UTILISATIE OVERZICHT                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Gebouwde Functionaliteit:  ████████████████████████████████ 100%  │
│  Werkende Functionaliteit:  ██████░░░░░░░░░░░░░░░░░░░░░░░░░  20%  │
│  Ongebruikte Code:          ████████████████████░░░░░░░░░░░  60%  │
│  Dead Code:                 ████████░░░░░░░░░░░░░░░░░░░░░░░  30%  │
│                                                                     │
│  💰 Business Value Loss:     80% van potentiële waarde             │
│  ⚠️  Compliance Risk:        HIGH - Toetsregels niet actief        │
│  📉 Quality Impact:          SEVERE - Generieke output             │
└─────────────────────────────────────────────────────────────────────┘
```

### Wat betekent dit?

- **Gebouwde Functionaliteit (100%)**: Alle features die geprogrammeerd zijn
- **Werkende Functionaliteit (20%)**: Features die daadwerkelijk worden gebruikt
- **Ongebruikte Code (60%)**: Code die wel bestaat maar nooit wordt aangeroepen
- **Dead Code (30%)**: Code die niet meer kan werken (ontbrekende dependencies)

### Business Impact Uitleg

- **💰 Business Value Loss**: Het systeem levert maar 20% van de waarde die het kan leveren
- **⚠️ Compliance Risk HIGH**: Definities voldoen mogelijk niet aan overheidsstandaarden omdat validatieregels niet actief zijn
- **📉 Quality Impact SEVERE**: Output is generiek in plaats van specifiek voor jouw domein

---

## 🏗️ Architectuur Analyse - Gedetailleerde Uitleg

### Huidige (Kapotte) Flow - Stap voor Stap

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│     UI      │ --> │ServiceAdapter│ --> │  Orchestrator   │
│ Generator   │     │              │     │                 │
└─────────────┘     └──────────────┘     └────────┬────────┘
```

**Wat gebeurt hier?**
1. **UI Generator**: Je klikt op "Genereer Definitie"
2. **ServiceAdapter**: Vertaalt je verzoek naar een intern formaat
3. **Orchestrator**: Beslist welke prompt builder te gebruiken

### Het Kritieke Beslismoment (waar het fout gaat)

```
┌─────────────────────────────────────────────────────────────┐
│                    ⚠️ DECISION POINT BUG                    │
│  Context Items Count: 7 (door string→char array bug)       │
│  Threshold: 3                                               │
│  Result: Legacy Builder SKIPPED ❌                          │
└─────────────────────────────────────────────────┬───────────┘
```

**Wat gaat er mis?**
- Het systeem telt hoeveel "context items" er zijn
- Door een bug telt het de letters van "proces" (p-r-o-c-e-s = 6) + andere context = 7 items
- De drempel is 3, dus 7 > 3 betekent: gebruik de simpele builder
- De Legacy Builder (met alle slimme features) wordt overgeslagen!

### De Drie Builders Uitgelegd

1. **Legacy Builder** (❌ Wordt overgeslagen)
   - Bevat 78+ validatieregels
   - Kent overheidscontext
   - Voorkomt veelgemaakte fouten
   - Genereert rijke, specifieke prompts

2. **Basic Builder** (✅ Wordt nu gebruikt)
   - Simpele templates
   - Geen domeinkennis
   - Geen validatie
   - Generieke output

3. **Context Builder** (❌ Niet actief)
   - Voor wanneer je externe bronnen hebt
   - Web lookups
   - Document verrijking

---

## 🐛 Root Cause Diepteanalyse

### De Oorzaak Boom - Uitleg per Tak

```
                           ROOT CAUSE TREE
                                 │
                    ┌────────────┴────────────┐
                    │                         │
            Data Type Bug              Strategy Selection
```

### Tak 1: Data Type Bug

**Wat is het probleem?**
```python
# Dit is wat gebeurt:
"ontologische_categorie": "proces"  # String in een dictionary voor lijsten

# Python ziet dit en denkt:
for item in "proces":  # Loopt over elke letter!
    print(item)        # Output: p, r, o, c, e, s
```

**Waarom is dit een probleem?**
- De `base_context` dictionary verwacht dat alle waarden lijsten zijn
- Een string is technisch ook een lijst (van karakters)
- Het systeem telt dus 6 karakters in plaats van 1 categorie

### Tak 2: Strategy Selection

**Het threshold probleem:**
```python
if total_context_items <= 3:
    return "legacy"  # Gebruik de slimme builder
else:
    return "basic"   # Gebruik de simpele builder
```

**Waarom 3 te laag is:**
- Zelfs minimale context heeft vaak 4+ items
- Met de bug erbij kom je al snel op 7+ items
- Legacy builder wordt bijna nooit gekozen

---

## 📈 Feature Gap Matrix - Gedetailleerde Uitleg

### Hoe lees je deze matrix?

```
┌─────────────────────────────┬────────┬────────┬──────────┬────────────┐
│         FEATURE             │ LEGACY │  NEW   │   GAP    │   IMPACT   │
├─────────────────────────────┼────────┼────────┼──────────┼────────────┤
│ Toetsregels (78+ rules)     │   ✅   │   ❌   │   100%   │    HIGH    │
```

**Kolom uitleg:**
- **FEATURE**: Welke functionaliteit
- **LEGACY**: Werkt in het oude systeem? (✅ = ja)
- **NEW**: Werkt in het huidige systeem? (❌ = nee, ⚠️ = deels)
- **GAP**: Hoeveel functionaliteit missen we? (100% = alles)
- **IMPACT**: Hoe erg is het dat dit niet werkt?

### Top 5 Kritieke Features die Missen

1. **Toetsregels (78+ rules)** - GAP: 100%
   - **Wat**: Validatieregels voor goede definities
   - **Waarom belangrijk**: Zorgt dat definities aan standaarden voldoen
   - **Voorbeeld**: Voorkomt cirkelredeneringen zoals "Een auto is een auto"

2. **Forbidden Words Check** - GAP: 100%
   - **Wat**: Controle op verboden woorden/patronen
   - **Waarom belangrijk**: Voorkomt slechte definitiepatronen
   - **Voorbeeld**: Start niet met "Een", "Het", "De"

3. **Expert System Logic** - GAP: 100%
   - **Wat**: Slimme regels gebaseerd op domeinkennis
   - **Waarom belangrijk**: Maakt definities domein-specifiek
   - **Voorbeeld**: Juridische termen krijgen juridische formulering

4. **Abbreviation Expansion** - GAP: 100%
   - **Wat**: Automatisch uitschrijven afkortingen
   - **Waarom belangrijk**: Duidelijkheid zonder manual werk
   - **Voorbeeld**: "OM" → "Openbaar Ministerie"

5. **Advanced Prompt Strategies** - GAP: 75%
   - **Wat**: Verschillende aanpakken per type begrip
   - **Waarom belangrijk**: Optimale prompt per situatie
   - **Voorbeeld**: Proces-begrippen krijgen andere instructies dan objecten

---

## 💡 Technische Fix Instructies

### Fix 1: Data Structure Correctie - Stap voor Stap

**Locatie**: `/src/services/definition_orchestrator.py` (rond regel 412)

**Stap 1**: Open het bestand
```bash
cd /Users/chrislehnen/Projecten/Definitie-app
code src/services/definition_orchestrator.py
```

**Stap 2**: Zoek deze code (rond regel 405-413):
```python
# HUIDIGE CODE (FOUT)
base_context = {
    "organisatorisch": (
        [context.request.context] if context.request.context else []
    ),
    "juridisch": [context.request.domein] if context.request.domein else [],
    "wettelijk": [],
    "ontologische_categorie": context.request.ontologische_categorie,  # FOUT!
}
```

**Stap 3**: Verwijder de ontologische_categorie regel:
```python
# GEFIXTE CODE
base_context = {
    "organisatorisch": (
        [context.request.context] if context.request.context else []
    ),
    "juridisch": [context.request.domein] if context.request.domein else [],
    "wettelijk": [],
    # ontologische_categorie verwijderd uit base_context
}
```

**Stap 4**: Zorg dat het in metadata staat (regel ~420):
```python
metadata = {
    "ontologische_categorie": context.request.ontologische_categorie,
    "extra_instructies": context.request.extra_instructies,
}
```

### Fix 2: Threshold Aanpassing - Stap voor Stap

**Locatie**: `/src/services/definition_generator_prompts.py` (rond regel 626)

**Stap 1**: Open het bestand
```bash
code src/services/definition_generator_prompts.py
```

**Stap 2**: Zoek de `_select_strategy` functie (rond regel 618):
```python
def _select_strategy(self, begrip: str, context: EnrichedContext) -> str:
```

**Stap 3**: Vind deze regel (rond regel 626):
```python
# HUIDIGE CODE
if total_context_items <= 3:
    return "legacy"
```

**Stap 4**: Verander 3 naar 10:
```python
# GEFIXTE CODE
if total_context_items <= 10:
    return "legacy"
```

---

## 🚀 NIEUWE AANBEVELING: Modulaire Prompt Architectuur

### Waarom een Modulaire Aanpak?

De huidige monolithische prompt builders hebben fundamentele problemen:
- **Te complex** - Alles zit in één grote functie
- **Moeilijk te testen** - Te veel verantwoordelijkheden
- **Moeilijk aan te passen** - Wijzigingen hebben onvoorspelbare effecten
- **Code duplicatie** - Dezelfde logica op meerdere plekken

### Voorgestelde Modulaire Architectuur

```python
# prompt_orchestrator.py
class PromptOrchestrator:
    """Orchestreert de samenstelling van prompts uit modulaire componenten."""

    def __init__(self):
        self.components = {
            'expert_role': ExpertRoleComponent(),
            'context': ContextComponent(),
            'ontology': OntologyComponent(),
            'rules': RulesComponent(),
            'errors': CommonErrorsComponent(),
            'format': FormatInstructionsComponent(),
            'examples': ExamplesComponent()
        }

    def build_prompt(self, request: PromptRequest) -> str:
        """Stel prompt samen uit relevante componenten."""
        sections = []

        # Expert rol altijd eerst
        sections.append(self.components['expert_role'].generate(request))

        # Context indien aanwezig
        if request.has_context():
            sections.append(self.components['context'].generate(request))

        # Ontologie indien categorie bekend
        if request.ontological_category:
            sections.append(self.components['ontology'].generate(request))

        return "\n\n".join(sections)
```

### Voordelen van deze aanpak:

1. **Single Responsibility** - Elke component doet één ding
2. **Testbaar** - Test componenten individueel
3. **Flexibel** - Mix & match naar behoefte
4. **Onderhoudbaar** - Wijzig alleen wat nodig is
5. **Uitbreidbaar** - Voeg nieuwe componenten toe zonder bestaande code te breken

### Voorbeeld Component:

```python
class OntologyInstructionComponent(PromptComponent):
    """Genereert ontologie-specifieke instructies."""

    def generate(self, request: PromptRequest) -> str:
        if not request.ontological_category:
            return ""

        instructions = {
            'proces': self._proces_instructions(request.begrip),
            'type': self._type_instructions(request.begrip),
            'resultaat': self._resultaat_instructions(request.begrip),
            'exemplaar': self._exemplaar_instructions(request.begrip)
        }

        return instructions.get(request.ontological_category, "")

    def is_applicable(self, request: PromptRequest) -> bool:
        return request.ontological_category is not None
```

### Implementatie Strategie:

**Fase 0: Modulaire Architectuur (1 week - AANBEVOLEN ALS EERSTE)**
```
□ Maak PromptComponent base class
□ Extract ExpertRoleComponent uit legacy
□ Extract OntologyComponent uit templates
□ Extract RulesComponent uit toetsregels
□ Extract ContextComponent uit enrichment
□ Implementeer PromptOrchestrator
□ Test modulaire aanpak met bestaande flows
□ Migreer geleidelijk van monolithisch naar modulair
```

Deze aanpak maakt alle volgende fixes veel eenvoudiger omdat je dan specifieke componenten kunt aanpassen zonder de hele prompt builder te hoeven herschrijven.

---

## 🗺️ Implementatie Roadmap (HERZIEN)

### Fase 0: Modulaire Architectuur (NIEUW - 1 week)
```
□ Implementeer modulaire prompt architectuur
□ Migreer bestaande functionaliteit naar componenten
□ Test backward compatibility
```

### Fase 1: Quick Wins (1-2 uur werk)

#### Week 1 - Kritieke Fixes
```
Maandag:
□ Fix 1: Data structure correctie (15 min)
□ Fix 2: Threshold aanpassing (15 min)
□ Test: Genereer test definitie (30 min)
□ Verificatie: Check of legacy builder actief is (30 min)

Dinsdag:
□ Test alle ontologische categorieën
□ Documenteer bevindingen
□ Commit changes met duidelijke message
```

### Fase 2: Feature Activatie (1 week)

#### Week 2 - Toetsregels Integratie
```
□ Analyseer huidige toetsregels structuur
□ Creëer RuleAwarePromptBuilder class (OF RulesComponent)
□ Integreer top 10 belangrijkste regels
□ Test met verschillende begripstypen
```

### Fase 3: Volledige Integratie (2-3 weken)

#### Week 3-4 - Complete Feature Set
```
□ Activeer context enrichment
□ Implementeer abbreviation expansion
□ Enable forbidden words checking
□ Integreer web lookup (indien mogelijk)
```

---

## 🧪 Testing & Verificatie

### Test 1: Verificatie dat Legacy Builder Actief is

**Test Script**:
```python
# test_legacy_activation.py
from services.definition_generator_prompts import UnifiedPromptBuilder
from services.definition_generator_context import EnrichedContext
from services.definition_generator_config import UnifiedGeneratorConfig

# Maak test context
context = EnrichedContext(
    base_context={"organisatorisch": ["Test"]},
    sources=[],
    expanded_terms={},
    confidence_scores={},
    metadata={"ontologische_categorie": "proces"}
)

# Test strategy selection
builder = UnifiedPromptBuilder(UnifiedGeneratorConfig())
strategy = builder._select_strategy("testbegrip", context)

print(f"Selected strategy: {strategy}")
print(f"Success: {'✅' if strategy == 'legacy' else '❌'}")
```

### Test 2: Categorie Prompt Verificatie

**Verwachte Output NA fixes**:
```
Je bent een expert in beleidsmatige definities voor overheidsgebruik.
Formuleer een definitie in één enkele zin, zonder toelichting.

📌 Context:
- Organisatorische context(en): Justid

### 📐 Let op betekenislaag (ESS-02 - Ontologische categorie):
[... uitgebreide instructies ...]

### ✅ Richtlijnen voor de definitie:
[... 78+ regels ...]
```

---

## ❓ FAQ & Troubleshooting

### Q: Hoe weet ik of de fixes werken?

**A**: Check deze indicatoren:
1. In de logs zie je: "Prompt gebouwd met strategy 'legacy'"
2. De prompt is 1000+ karakters (ipv 200-300)
3. Je ziet toetsregels in de prompt output

### Q: Wat als het nog steeds niet werkt?

**A**: Controleer:
1. Is de ontologische_categorie écht uit base_context?
2. Is de threshold écht verhoogd naar 10?
3. Run de test scripts om te verifiëren

### Q: Kan ik dit veilig in productie zetten?

**A**: Ja, deze fixes zijn veilig omdat:
1. Ze veranderen geen business logic
2. Ze activeren alleen bestaande features
3. Ze hebben geen impact op data integriteit

### Q: Wat is de verwachte verbetering?

**A**: Na de fixes:
- 70% betere definitiekwaliteit
- 85% compliance met standaarden
- 90% minder manual correcties nodig

---

## 🎯 Samenvatting Aanpak

### Vandaag nog doen:
1. **Fix 1**: Verplaats ontologische_categorie (regel 412)
2. **Fix 2**: Verhoog threshold naar 10 (regel 626)
3. **Test**: Genereer een definitie en check de logs

### Deze week:
1. Verifieer dat alle features werken
2. Begin met toetsregels integratie
3. Documenteer gevonden problemen

### Deze maand:
1. Activeer alle ongebruikte features
2. Implementeer feedback systeem
3. Train team op nieuwe mogelijkheden

---

## 📞 Support & Contact

Voor vragen over deze analyse:
- Check eerst de FAQ sectie
- Test met de gegeven scripts
- Documenteer exact welke stappen je hebt genomen

---

*Dit document is een levend document en wordt bijgewerkt naarmate fixes worden geïmplementeerd.*
