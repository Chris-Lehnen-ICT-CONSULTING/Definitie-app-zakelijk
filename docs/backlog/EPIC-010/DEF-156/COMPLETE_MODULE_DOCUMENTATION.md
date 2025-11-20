# Volledige Prompt Module Documentatie

**Versie:** 1.0
**Datum:** 2025-11-14
**Issue:** DEF-156
**Doel:** Complete technische beschrijving van alle 19 prompt modules

---

## 📋 Inhoudsopgave

1. [Overzicht Prompt Systeem](#overzicht-prompt-systeem)
2. [Module Architectuur](#module-architectuur)
3. [Module Documentatie (A-Z)](#module-documentatie)
   - [1. ARAI Rules Module](#1-arai-rules-module)
   - [2. CON Rules Module](#2-con-rules-module)
   - [3. Context Awareness Module](#3-context-awareness-module)
   - [4. Definition Task Module](#4-definition-task-module)
   - [5. Error Prevention Module](#5-error-prevention-module)
   - [6. ESS Rules Module](#6-ess-rules-module)
   - [7. Expertise Module](#7-expertise-module)
   - [8. Grammar Module](#8-grammar-module)
   - [9. Integrity Rules Module](#9-integrity-rules-module)
   - [10. Metrics Module](#10-metrics-module)
   - [11. Output Specification Module](#11-output-specification-module)
   - [12. SAM Rules Module](#12-sam-rules-module)
   - [13. Semantic Categorisation Module](#13-semantic-categorisation-module)
   - [14. Structure Rules Module](#14-structure-rules-module)
   - [15. Template Module](#15-template-module)
   - [16. VER Rules Module](#16-ver-rules-module)
4. [Shared State Systeem](#shared-state-systeem)
5. [Dependency Graph](#dependency-graph)
6. [Context Duplication Analysis](#context-duplication-analysis)

---

## Overzicht Prompt Systeem

Het prompt systeem bestaat uit **19 gespecialiseerde modules** die samenwerken om een complete GPT-4 prompt te genereren voor definitiecreatie. Elke module heeft een specifieke verantwoordelijkheid en kan data delen via een `shared_state` mechanisme.

### Kern Principes

1. **Modularity**: Elke module heeft één verantwoordelijkheid
2. **Composability**: Modules worden gecombineerd via `PromptOrchestrator`
3. **Priority-based execution**: Modules draaien in volgorde van prioriteit (100 → 0)
4. **Dependency resolution**: Modules kunnen afhankelijk zijn van andere modules
5. **Shared state**: Modules kunnen data delen via `context.set_shared()` / `context.get_shared()`

### Execution Flow

```
PromptOrchestrator.build_prompt(begrip, context, config)
│
├─→ Create ModuleContext (EENMALIG)
│   └─→ Contains: begrip, enriched_context, config, shared_state={}
│
├─→ Resolve dependencies (topological sort)
│
└─→ Execute modules in priority order:
    │
    ├─→ Priority 100: ExpertiseModule
    ├─→ Priority 90:  OutputSpecificationModule
    ├─→ Priority 85:  GrammarModule
    ├─→ Priority 75:  AraiRulesModule, EssRulesModule
    ├─→ Priority 70:  ContextAwarenessModule, ConRulesModule, SemanticCategorisationModule
    ├─→ Priority 65:  StructureRulesModule, IntegrityRulesModule, SamRulesModule
    ├─→ Priority 60:  TemplateModule, VerRulesModule
    ├─→ Priority 50:  ErrorPreventionModule
    └─→ Priority 30:  MetricsModule
        └─→ Priority 10:  DefinitionTaskModule
```

**KRITIEK**: Context wordt **1x** aangemaakt en door reference gedeeld met alle modules. Er is **GEEN** redundante context creatie op code niveau!

---

## Module Architectuur

### Base Module Interface

Alle modules erven van `BasePromptModule`:

```python
class BasePromptModule:
    def __init__(self, module_id: str, module_name: str, priority: int = 50):
        self.module_id = module_id
        self.module_name = module_name
        self.priority = priority

    def initialize(self, config: dict) -> None:
        """Setup met configuratie"""

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """Check of module mag draaien"""

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """Genereer module output"""

    def get_dependencies(self) -> list[str]:
        """Return lijst van module_ids waarvan deze module afhankelijk is"""
```

### Module Context Object

```python
@dataclass
class ModuleContext:
    begrip: str                      # Het te definiëren begrip
    enriched_context: EnrichedContext # Context data (organisatorisch/juridisch/wettelijk)
    config: ConfigObject             # Module configuratie
    shared_state: dict               # GEDEELD tussen modules

    def get_shared(self, key: str, default=None):
        """Haal data op uit shared state"""

    def set_shared(self, key: str, value):
        """Sla data op in shared state"""

    def get_metadata(self, key: str, default=None):
        """Haal metadata op uit enriched_context"""
```

**BELANGRIJK**: `shared_state` is een **dictionary** die door **ALLE** modules wordt gedeeld. Modules communiceren hiermee met elkaar.

---

## Module Documentatie

---

## 1. ARAI Rules Module

### Identificatie
- **Module ID**: `arai_rules`
- **Class**: `AraiRulesModule`
- **File**: `src/services/prompts/modules/arai_rules_module.py`
- **Priority**: 75 (hoog)

### Functie
Genereert alle **ARAI (Algemene Regels AI)** validatieregels. Deze regels bevatten de basis kwaliteitsrichtlijnen voor definities.

### Dependencies
- **Geen directe dependencies**
- **Data source**: `ToetsregelManager` via `get_cached_toetsregel_manager()`

### Configuratie
```python
{
    "include_examples": True  # Toon ✅/❌ voorbeelden bij elke regel
}
```

### Statisch vs Dynamisch

| Aspect | Type | Beschrijving |
|--------|------|-------------|
| **Header** | Statisch | `### ✅ Algemene Regels AI (ARAI):` |
| **Regels** | Statisch | Alle ARAI-XX regels uit JSON config |
| **Voorbeelden** | Statisch | ✅/❌ voorbeelden per regel |
| **Aantal regels** | Dynamisch | Afhankelijk van toetsregels config |

### Output Voorbeeld
```markdown
### ✅ Algemene Regels AI (ARAI):
🔹 **ARAI-01 - geen werkwoord als kern**
- De definitie mag niet beginnen met een werkwoord als kern.
- Toetsvraag: Begint de definitie met een werkwoord als kern?
  ✅ proces dat beslissers identificeert
  ❌ identificeert beslissers

🔹 **ARAI-02 - Vermijd vage containerbegrippen**
- De definitie vermijdt vage termen als 'aspect', 'element', 'factor'.
- Toetsvraag: Bevat de definitie vage containerbegrippen?
  ✅ criterium voor beoordeling
  ❌ belangrijk aspect van het proces
```

### Shared State Interactions
- **Reads**: Geen
- **Writes**: Geen
- **Effect**: Puur output generatie

### Code Flow
```python
def execute(self, context: ModuleContext) -> ModuleOutput:
    # 1. Load cached toetsregels manager (SINGLETON - 1x geladen)
    manager = get_cached_toetsregel_manager()

    # 2. Get ALL regels
    all_rules = manager.get_all_regels()

    # 3. Filter alleen ARAI regels
    arai_rules = {k: v for k, v in all_rules.items() if k.startswith("ARAI")}

    # 4. Format elke regel
    for regel_key, regel_data in sorted(arai_rules.items()):
        sections.extend(self._format_rule(regel_key, regel_data))

    return ModuleOutput(content="\n".join(sections))
```

### Performance
- **Regel loading**: 1x via cached singleton (gedeeld met alle regel modules)
- **Formatting**: O(n) waar n = aantal ARAI regels
- **Memory**: Laag (regels zijn al in cache)

---

## 2. CON Rules Module

### Identificatie
- **Module ID**: `con_rules`
- **Class**: `ConRulesModule`
- **File**: `src/services/prompts/modules/con_rules_module.py`
- **Priority**: 70 (hoog)

### Functie
Genereert alle **CON (Context)** validatieregels voor context-specifieke formuleringen en bronverwijzingen.

### Dependencies
- **Geen directe dependencies**
- **Data source**: `ToetsregelManager` via `get_cached_toetsregel_manager()`

### Configuratie
```python
{
    "include_examples": True  # Toon ✅/❌ voorbeelden bij elke regel
}
```

### Statisch vs Dynamisch

| Aspect | Type | Beschrijving |
|--------|------|-------------|
| **Header** | Statisch | `### 🌐 Context Regels (CON):` |
| **Regels** | Statisch | Alle CON-XX regels uit JSON config |
| **Voorbeelden** | Statisch | ✅/❌ voorbeelden per regel |

### Output Voorbeeld
```markdown
### 🌐 Context Regels (CON):
🔹 **CON-01 - Contextspecifieke formulering zonder expliciete benoeming**
- De definitie is specifiek voor de context, zonder deze expliciet te benoemen.
- Toetsvraag: Is de definitie geformuleerd zonder de context expliciet te noemen?
  ✅ Proces waarbij verdachten worden ondervraagd
  ❌ Proces binnen het OM waarbij verdachten worden ondervraagd
```

### Shared State Interactions
- **Reads**: Geen
- **Writes**: Geen
- **Effect**: Puur output generatie

### Identiek Pattern
CON, ESS, SAM, VER modules volgen **exact hetzelfde pattern** als ARAI Rules Module, alleen met verschillende regel prefixes.

---

## 3. Context Awareness Module

### Identificatie
- **Module ID**: `context_awareness`
- **Class**: `ContextAwarenessModule`
- **File**: `src/services/prompts/modules/context_awareness_module.py`
- **Priority**: 70 (hoog)

### Functie
**Centrale module voor context verwerking**. Berekent context richness score en genereert adaptieve context instructies op basis van beschikbare context kwaliteit.

### Dependencies
- **Geen directe dependencies**
- **Data source**: `context.enriched_context`

### Configuratie
```python
{
    "adaptive_formatting": True,      # Adapteer output op basis van context richness
    "confidence_indicators": True,    # Toon 🟢🟡🔴 confidence emojis
    "include_abbreviations": True     # Toon afkortingen/uitbreidingen
}
```

### Statisch vs Dynamisch

| Aspect | Type | Beschrijving |
|--------|------|-------------|
| **Header** | Dynamisch | Verandert op basis van context score |
| **Context data** | **100% Dynamisch** | Organisatorisch/juridisch/wettelijk |
| **Bronnen** | Dynamisch | Wikipedia, SRU met confidence scores |
| **Afkortingen** | Dynamisch | Detecteerde afkortingen + expansies |
| **Formatting level** | Dynamisch | Rich/Moderate/Minimal op basis van score |

### Context Richness Score Berekening

```python
def _calculate_context_score(self, enriched_context) -> float:
    """
    Score 0.0 - 1.0 gebaseerd op:
    - Base context items (max 0.3)
    - Sources confidence (max 0.4)
    - Expanded terms (max 0.2)
    - Confidence scores (max 0.1)
    """
    score = 0.0

    # Base context: 0.3 max
    total_base_items = sum(len(items) for items in base_context.values())
    score += min(total_base_items / 10, 0.3)

    # Sources: 0.4 max
    if sources:
        avg_confidence = sum(s.confidence for s in sources) / len(sources)
        score += avg_confidence * 0.4

    # Expanded terms: 0.2 max
    if expanded_terms:
        score += min(len(expanded_terms) / 5, 0.2)

    # Confidence scores: 0.1 max
    if confidence_scores:
        avg = sum(confidence_scores.values()) / len(confidence_scores)
        score += avg * 0.1

    return min(score, 1.0)
```

### Adaptive Output

**Scenario A: Rich Context** (score ≥ 0.8)
```markdown
📊 UITGEBREIDE CONTEXT ANALYSE:
⚠️ VERPLICHT: Gebruik onderstaande specifieke context om de definitie te formuleren...

ORGANISATORISCH:
  • OM
  • Reclassering

JURIDISCH:
  • Strafrecht

WETTELIJK:
  • Wetboek van Strafrecht

ADDITIONELE BRONNEN:
  🟢 Wikipedia (0.95): Een slachtoffer is een persoon die...
  🟡 SRU (0.72): In juridische context...

AFKORTINGEN:
  • OM = Openbaar Ministerie
  • WvSr = Wetboek van Strafrecht
```

**Scenario B: Moderate Context** (0.5 ≤ score < 0.8)
```markdown
📌 VERPLICHTE CONTEXT INFORMATIE:
⚠️ BELANGRIJKE INSTRUCTIE: Gebruik onderstaande context...

🎯 SPECIFIEKE CONTEXT VOOR DEZE DEFINITIE:
Organisatorisch: OM, Reclassering
Juridisch: Strafrecht
```

**Scenario C: Minimal Context** (score < 0.5)
```markdown
📍 VERPLICHTE CONTEXT: OM, Reclassering
⚠️ INSTRUCTIE: Formuleer de definitie specifiek voor bovenstaande context...
```

### Shared State Interactions

#### WRITES (Kritiek voor andere modules!)
```python
# 1. Context richness score
context.set_shared("context_richness_score", 0.85)

# 2. Traditionele context types (EPIC-010 compliant)
context.set_shared("organization_contexts", ["OM", "Reclassering"])
context.set_shared("juridical_contexts", ["Strafrecht"])
context.set_shared("legal_basis_contexts", ["Wetboek van Strafrecht"])
```

#### READS
- Geen

### Code Flow
```python
def execute(self, context: ModuleContext) -> ModuleOutput:
    # 1. Bereken context richness score (0.0 - 1.0)
    context_score = self._calculate_context_score(context.enriched_context)

    # 2. Sla score op voor andere modules
    context.set_shared("context_richness_score", context_score)

    # 3. Kies formatting strategie
    if context_score >= 0.8:
        content = self._build_rich_context_section(context)
    elif context_score >= 0.5:
        content = self._build_moderate_context_section(context)
    else:
        content = self._build_minimal_context_section(context)

    # 4. Deel traditionele context voor andere modules
    self._share_traditional_context(context)

    return ModuleOutput(content=content, metadata={...})
```

### ⚠️ KRITIEKE BEVINDING: Context Duplication

Dit is **MODULE 1 van 3** die context toevoegt aan de prompt:

1. **ContextAwarenessModule** (regel 62-68): Primaire context sectie
2. **ErrorPreventionModule** (regel 340-343): Context-specifieke verboden
3. **DefinitionTaskModule** (regel 418-423): Prompt metadata met context

**Probleem**: Dezelfde context waarden verschijnen **3x** in de finale prompt, maar via verschillende modules zonder coördinatie!

---

## 4. Definition Task Module

### Identificatie
- **Module ID**: `definition_task`
- **Class**: `DefinitionTaskModule`
- **File**: `src/services/prompts/modules/definition_task_module.py`
- **Priority**: 10 (laagst - komt als LAATSTE in prompt)

### Functie
Genereert het **finale deel** van de prompt met:
1. De specifieke definitie opdracht
2. Constructie checklist
3. Kwaliteitscontrole vragen
4. Metadata voor traceerbaarheid
5. Ontologische marker instructie
6. Prompt metadata

### Dependencies
```python
["semantic_categorisation", "context_awareness"]
```

**Waarom**: Gebruikt `ontological_category` en `organization_contexts` die door die modules worden gezet.

### Configuratie
```python
{
    "include_quality_control": True,  # Voeg kwaliteitscontrole vragen toe
    "include_metadata": True          # Voeg metadata sectie toe
}
```

### Statisch vs Dynamisch

| Aspect | Type | Beschrijving |
|--------|------|-------------|
| **Header** | Statisch | `### 🎯 FINALE INSTRUCTIES:` |
| **Begrip** | **Dynamisch** | Het te definiëren begrip |
| **Checklist basis** | Statisch | Vaste checkpunten |
| **Ontologische focus** | Dynamisch | Alleen als categorie bekend |
| **Kwaliteitscontrole** | Semi-dynamisch | Aangepast aan context aanwezigheid |
| **Metadata** | **Dynamisch** | Timestamp, context info |
| **Prompt metadata** | **Dynamisch** | Begrip, woordtype, contexten |

### Output Voorbeeld
```markdown
### 🎯 FINALE INSTRUCTIES:

#### ✏️ Definitieopdracht:
Formuleer nu de definitie van **slachtoffer** volgens deze specificaties:

📋 **CONSTRUCTIE GUIDE - Bouw je definitie op:**
→ Begint met zelfstandig naamwoord (geen lidwoord/koppelwerkwoord)
→ Eén enkele zin zonder punt aan het einde
→ Geen toelichting, voorbeelden of haakjes
→ Ontologische categorie is duidelijk
🎯 Focus: Dit is een **type** (soort/categorie)
→ Geen verboden woorden (aspect, element, kan, moet, etc.)
→ Context verwerkt zonder expliciete benoeming

#### 🔍 KWALITEITSCONTROLE:
Stel jezelf deze vragen:
1. Is direct duidelijk WAT het begrip is (niet het doel)?
2. Kan iemand hiermee bepalen of iets wel/niet onder dit begrip valt?
3. Is de formulering specifiek genoeg voor de gegeven context?
4. Bevat de definitie alleen essentiële informatie?

#### 📊 METADATA voor traceerbaarheid:
- Begrip: slachtoffer
- Timestamp: 2025-11-14 15:30:00
- Context beschikbaar: Ja
- Builder versie: Modular Architecture v2.0

---

📋 **Ontologische marker (lever als eerste regel):**
- Ontologische categorie: kies uit [soort, exemplaar, proces, resultaat]

✏️ Geef nu de definitie van het begrip **slachtoffer** in één enkele zin, zonder toelichting.

🆔 Promptmetadata:
- Begrip: slachtoffer
- Termtype: overig
- Organisatorische context: OM, Reclassering
- Juridische context: Strafrecht
- Wettelijke basis: Wetboek van Strafrecht
```

### Shared State Interactions

#### READS (Afhankelijk van andere modules!)
```python
word_type = context.get_shared("word_type", "onbekend")              # Van ExpertiseModule
ontological_category = context.get_shared("ontological_category")    # Van SemanticCategorisationModule
org_contexts = context.get_shared("organization_contexts", [])       # Van ContextAwarenessModule
jur_contexts = context.get_shared("juridical_contexts", [])          # Van ContextAwarenessModule
wet_basis = context.get_shared("legal_basis_contexts", [])           # Van ContextAwarenessModule
```

#### WRITES
- Geen

### ⚠️ KRITIEKE BEVINDING: Dit is de 3e plaats waar context verschijnt!

**Prompt metadata sectie (regel 418-423)** herhaalt:
```markdown
🆔 Promptmetadata:
- Organisatorische context: OM, Reclassering      ← DUPLICATE van regel 66!
- Juridische context: Strafrecht                  ← DUPLICATE!
- Wettelijke basis: Wetboek van Strafrecht        ← DUPLICATE!
```

**Identieke data als:**
- ContextAwarenessModule (regel 62-68)
- ErrorPreventionModule context forbidden (regel 340-343)

---

## 5. Error Prevention Module

### Identificatie
- **Module ID**: `error_prevention`
- **Class**: `ErrorPreventionModule`
- **File**: `src/services/prompts/modules/error_prevention_module.py`
- **Priority**: 50 (medium)

### Functie
Genereert **verboden patronen** en veelgemaakte fouten sectie. Bevat:
1. Basis veelgemaakte fouten (statisch)
2. **39 verboden startwoorden** (statisch)
3. **Context-specifieke verboden** (dynamisch)
4. Validatiematrix (statisch)

### Dependencies
```python
["context_awareness"]
```

**Waarom**: Gebruikt `organization_contexts`, `juridical_contexts`, `legal_basis_contexts` om context-specifieke verboden te genereren.

### Configuratie
```python
{
    "include_validation_matrix": True,   # Toon probleem coverage tabel
    "extended_forbidden_list": True      # Toon alle 39 verboden startwoorden
}
```

### Statisch vs Dynamisch

| Aspect | Type | Beschrijving |
|--------|------|-------------|
| **Header** | Statisch | `### ⚠️ Veelgemaakte fouten (vermijden!):` |
| **Basis fouten** | Statisch | 6 vaste regels (geen lidwoord, etc.) |
| **39 verboden starters** | **Statisch** | Complete lijst van 'is', 'betreft', etc. |
| **Context verboden** | **Dynamisch** | Specifiek per context |
| **Validatiematrix** | Statisch | Probleemoverzicht tabel |
| **Laatste waarschuwing** | Statisch | Context mag niet letterlijk voorkomen |

### Output Voorbeeld
```markdown
### ⚠️ Veelgemaakte fouten (vermijden!):
- ❌ Begin niet met lidwoorden ('de', 'het', 'een')
- ❌ Gebruik geen koppelwerkwoord aan het begin ('is', 'betekent', 'omvat')
- ❌ Herhaal het begrip niet letterlijk
- ❌ Gebruik geen synoniem als definitie
- ❌ Vermijd vage containerbegrippen ('aspect', 'element', 'factor', 'kwestie')
- ❌ Gebruik enkelvoud; infinitief bij werkwoorden

- ❌ Start niet met 'is'
- ❌ Start niet met 'betreft'
- ❌ Start niet met 'omvat'
... (nog 36 andere verboden starters)

### 🚨 CONTEXT-SPECIFIEKE VERBODEN:
- Gebruik de term 'OM' of een variant daarvan niet letterlijk in de definitie.
- Gebruik de term 'Openbaar Ministerie' of een variant daarvan niet letterlijk in de definitie.
- Gebruik de term 'Reclassering' of een variant daarvan niet letterlijk in de definitie.
- Vermijd expliciete vermelding van juridisch context 'Strafrecht' in de definitie.
- Vermijd expliciete vermelding van wetboek 'Wetboek van Strafrecht' in de definitie.

| Probleem                             | Afgedekt? | Toelichting                                |
|--------------------------------------|-----------|---------------------------------------------|
| Start met begrip                     | ✅        | Vermijd cirkeldefinities                     |
| Abstracte constructies               | ✅        | 'proces waarbij', 'handeling die', enz.      |
...

🚫 Let op: context en bronnen mogen niet letterlijk of herleidbaar in de definitie voorkomen.
```

### Shared State Interactions

#### READS (Afhankelijk van ContextAwarenessModule!)
```python
org_contexts = context.get_shared("organization_contexts", [])
jur_contexts = context.get_shared("juridical_contexts", [])
wet_contexts = context.get_shared("legal_basis_contexts", [])
```

#### WRITES
- Geen

### Organisatie Mapping (Hardcoded!)
```python
org_mappings = {
    "NP": "Nederlands Politie",
    "DJI": "Dienst Justitiële Inrichtingen",
    "OM": "Openbaar Ministerie",
    "ZM": "Zittende Magistratuur",
    "3RO": "Samenwerkingsverband Reclasseringsorganisaties",
    "CJIB": "Centraal Justitieel Incassobureau",
    "KMAR": "Koninklijke Marechaussee",
    "FIOD": "Fiscale Inlichtingen- en Opsporingsdienst",
}
```

Voor elke organisatie afkorting worden **TWEE** verboden toegevoegd:
1. De afkorting zelf ("OM")
2. De volledige naam ("Openbaar Ministerie")

### ⚠️ KRITIEKE BEVINDING: 39 Verboden Starters

Dit is **EXTREEM bloat**! Alle 39 starters zijn varianten van:
- Koppelwerkwoorden ('is', 'betekent', 'omvat')
- Lidwoorden ('de', 'het', 'een')
- Meta-termen ('type van', 'soort van')

**Kan geconsolideerd worden tot 1 regex pattern!**

### ⚠️ KRITIEKE BEVINDING: Dit is de 2e plaats waar context verschijnt!

Context-specifieke verboden sectie (regel 340-343) herhaalt:
```markdown
- Gebruik de term 'OM' niet letterlijk       ← Context waarde van regel 66!
- Gebruik de term 'Openbaar Ministerie'...   ← Afgeleid van regel 66 context!
```

---

## 6. ESS Rules Module

### Identificatie
- **Module ID**: `ess_rules`
- **Class**: `EssRulesModule`
- **File**: `src/services/prompts/modules/ess_rules_module.py`
- **Priority**: 75 (hoog)

### Functie
Genereert alle **ESS (Essentie)** validatieregels voor ontologische categorisatie en toetsbaarheid.

**Identiek patroon als ARAI Rules Module**, maar met ESS- prefix.

### Dependencies, Config, Output
Zie ARAI Rules Module - exact hetzelfde patroon.

---

## 7. Expertise Module

### Identificatie
- **Module ID**: `expertise`
- **Class**: `ExpertiseModule`
- **File**: `src/services/prompts/modules/expertise_module.py`
- **Priority**: 100 (hoogst - komt als EERSTE in prompt!)

### Functie
Definieert de **expert rol** en basis instructies. Dit is de OPENING van de prompt.

### Dependencies
- **Geen**

### Configuratie
```python
# Geen configureerbare opties
```

### Statisch vs Dynamisch

| Aspect | Type | Beschrijving |
|--------|------|-------------|
| **Rol definitie** | **100% Statisch** | Expert tekst altijd hetzelfde |
| **Taak instructie** | **100% Statisch** | Vaste tekst |
| **Basis vereisten** | **100% Statisch** | 5 vaste punten |
| **Woordsoort detectie** | Dynamisch (intern) | Wordt berekend maar niet getoond |

### Output (ALTIJD Identiek)
```text
Je bent een expert in het creëren van definities die EENDUIDIG zijn voor alle BELANGHEBBENDEN en aansluiten bij de WERKELIJKHEID.

Formuleer een heldere definitie die het begrip precies afbakent.

BELANGRIJKE VEREISTEN:
- Gebruik objectieve, neutrale taal
- Vermijd vage of subjectieve termen
- Focus op de essentie van het begrip
- Wees precies en ondubbelzinnig
- Vermijd normatieve of evaluatieve uitspraken
```

### Woordsoort Detectie (Intern)

```python
def _bepaal_woordsoort(self, begrip: str) -> str:
    """
    Returns: 'werkwoord', 'deverbaal', of 'overig'

    Werkwoord: eindigt op -eren, -elen, -en (niet -ing, -atie)
    Deverbaal: eindigt op -ing, -atie, -age, -ment, -tie, -sie, -isatie
    Overig: alles anders
    """
```

**Voorbeelden:**
- "observeren" → werkwoord
- "observatie" → deverbaal
- "slachtoffer" → overig

### Shared State Interactions

#### WRITES (Kritiek voor GrammarModule en TemplateModule!)
```python
context.set_shared("word_type", "werkwoord")  # of "deverbaal" of "overig"
```

#### READS
- Geen

### Code Flow
```python
def execute(self, context: ModuleContext) -> ModuleOutput:
    # 1. Bepaal woordsoort van begrip
    woordsoort = self._bepaal_woordsoort(context.begrip)

    # 2. Sla op voor andere modules (GrammarModule, TemplateModule)
    context.set_shared("word_type", woordsoort)

    # 3. Bouw statische sectie (ALTIJD hetzelfde)
    sections = [
        self._build_role_definition(),      # Expert rol
        self._build_task_instruction(),     # Taak
        self._build_basic_requirements()    # Vereisten
    ]

    return ModuleOutput(content="\n".join(sections))
```

### Belangrijke Notities
- **DEF-154**: `word_type_advice` sectie is VERWIJDERD wegens redundantie met TemplateModule
- Deze module draait ALTIJD als eerste (priority 100)
- Output is 100% statisch (behalve interne woordsoort detectie)

---

## 8. Grammar Module

### Identificatie
- **Module ID**: `grammar`
- **Class**: `GrammarModule`
- **File**: `src/services/prompts/modules/grammar_module.py`
- **Priority**: 85 (zeer hoog)

### Functie
Genereert grammaticale richtlijnen en schrijfstijl instructies.

### Dependencies
```python
[]  # Soft dependency op ExpertiseModule via shared_state
```

**Leest** `word_type` van ExpertiseModule, maar declareert dit niet als harde dependency.

### Configuratie
```python
{
    "include_examples": True,  # Toon ✅/❌ voorbeelden
    "strict_mode": False       # Extra strikte regels (geen bijv. nw, max 1 bijzin, etc.)
}
```

### Statisch vs Dynamisch

| Aspect | Type | Beschrijving |
|--------|------|-------------|
| **Header** | Statisch | `### 🔤 GRAMMATICA REGELS:` |
| **Basis regels** | Statisch | Enkelvoud, actieve vorm, tegenwoordige tijd |
| **Woordsoort-specifiek** | **Dynamisch** | Alleen als word_type bekend |
| **Interpunctie** | Statisch | Komma's, afkortingen, haakjes |
| **Strict mode regels** | Conditioneel | Alleen als strict_mode=True |

### Output Voorbeeld
```markdown
### 🔤 GRAMMATICA REGELS:

🔸 **Enkelvoud als standaard**
- Gebruik enkelvoud tenzij het begrip specifiek een meervoud aanduidt
- Bij twijfel: gebruik enkelvoud
  ✅ proces (niet: processen)
  ✅ maatregel (niet: maatregelen)
  ✅ gegevens (correct meervoud wanneer het begrip dit vereist)

🔸 **Actieve vorm prefereren**
- Gebruik waar mogelijk de actieve vorm
- Passieve vorm alleen bij focus op het ondergaan van actie
  ✅ instantie die toezicht houdt
  ❌ instantie waardoor toezicht wordt gehouden

🔸 **Tegenwoordige tijd**
- Formuleer definities in de tegenwoordige tijd
- Vermijd verleden of toekomende tijd
  ✅ proces dat identificeert
  ❌ proces dat zal identificeren
  ❌ proces dat identificeerde

🔸 **Werkwoord-specifieke regels** ← DYNAMISCH (alleen bij word_type="werkwoord")
- Definieer als handeling of proces
- Begin met een zelfstandig naamwoord dat de handeling beschrijft
  ✅ controleren: handeling waarbij...
  ✅ registreren: proces van het vastleggen...
  ❌ controleren: het controleren van...

🔸 **Komma gebruik**
- Gebruik komma's spaarzaam en alleen waar nodig voor duidelijkheid
...
```

### Shared State Interactions

#### READS
```python
word_type = context.get_shared("word_type", "overig")  # Van ExpertiseModule
```

#### WRITES
- Geen

### Woordsoort-Specifieke Regels

**Voor "werkwoord":**
```markdown
🔸 **Werkwoord-specifieke regels**
- Definieer als handeling of proces
- Begin met een zelfstandig naamwoord dat de handeling beschrijft
  ✅ controleren: handeling waarbij...
  ❌ controleren: het controleren van...
```

**Voor "deverbaal":**
```markdown
🔸 **Deverbaal-specifieke regels**
- Focus op het resultaat of de staat
- Vermijd procesbeschrijvingen
  ✅ registratie: vastgelegde gegevens...
  ❌ registratie: het proces van registreren...
```

**Voor "overig":**
Geen extra regels.

### Strict Mode Regels (Optioneel)
```markdown
🔸 **[STRICT] Geen bijvoeglijke naamwoorden**
- Vermijd alle niet-essentiële bijvoeglijke naamwoorden
- Alleen objectieve, meetbare kwalificaties

🔸 **[STRICT] Maximaal één bijzin**
- Beperk complexiteit door maximaal één bijzin toe te staan

🔸 **[STRICT] Geen voorzetsels aan het einde**
- Eindig nooit een definitie met een voorzetsel
```

---

## 9. Integrity Rules Module

### Identificatie
- **Module ID**: `integrity_rules`
- **Class**: `IntegrityRulesModule`
- **File**: `src/services/prompts/modules/integrity_rules_module.py`
- **Priority**: 65 (medium-hoog)

### Functie
Genereert alle **INT (Integriteit)** validatieregels voor definitie integriteit en compleetheid.

### Dependencies
- **Geen**

### Configuratie
```python
{
    "include_examples": True  # Toon ✅/❌ voorbeelden
}
```

### Statisch vs Dynamisch
**100% Statisch** - Alle INT regels zijn hardcoded in de module (niet via JSON zoals ARAI/CON/ESS/SAM/VER).

### Output Structuur
```markdown
### 🔒 Integriteit Regels (INT):

🔹 **INT-01 - Compacte en begrijpelijke zin**
🔹 **INT-02 - Geen beslisregel**
🔹 **INT-03 - Voornaamwoord-verwijzing duidelijk**
🔹 **INT-04 - Lidwoord-verwijzing duidelijk**
🔹 **INT-06 - Definitie bevat geen toelichting**
🔹 **INT-07 - Alleen toegankelijke afkortingen**
🔹 **INT-08 - Positieve formulering**
```

**Opmerking**: INT-05 ontbreekt (mogelijk deprecated).

### Voorbeeld Regel
```markdown
🔹 **INT-01 - Compacte en begrijpelijke zin**
- Een definitie is compact en in één enkele zin geformuleerd.
- Toetsvraag: Is de definitie geformuleerd als één enkele, begrijpelijke zin?
  ✅ transitie-eis: eis die een organisatie moet ondersteunen om migratie...
  ❌ transitie-eis: eis die een organisatie moet ondersteunen om migratie... In tegenstelling tot andere eisen vertegenwoordigen transitie-eisen tijdelijke behoeften...
```

### Code Verschil: Hardcoded vs JSON
```python
# INT Rules: Handmatig gebouwd
def _build_int01_rule(self) -> list[str]:
    rules = []
    rules.append("🔹 **INT-01 - Compacte en begrijpelijke zin**")
    rules.append("- Een definitie is compact en in één enkele zin geformuleerd.")
    ...
    return rules

# vs ARAI/CON/ESS/SAM/VER: Uit JSON geladen
manager = get_cached_toetsregel_manager()
arai_rules = {k: v for k, v in manager.get_all_regels().items() if k.startswith("ARAI")}
```

**Waarom verschil?** INT regels zijn mogelijk toegevoegd voordat het JSON-based systeem werd geïmplementeerd.

---

## 10. Metrics Module

### Identificatie
- **Module ID**: `metrics`
- **Class**: `MetricsModule`
- **File**: `src/services/prompts/modules/metrics_module.py`
- **Priority**: 30 (laag)

### Functie
Genereert kwaliteitsmetrieken en scoring informatie voor **monitoring en advies**.

### Dependencies
```python
[]  # Geen harde dependencies
```

Leest optioneel `organization_contexts` via shared_state.

### Configuratie
```python
{
    "include_detailed_metrics": True,  # Toon complexiteit, leesbaarheid, checks
    "track_history": False             # Historische tracking (niet geïmplementeerd)
}
```

### Statisch vs Dynamisch

| Aspect | Type | Beschrijving |
|--------|------|-------------|
| **Header** | Statisch | `### 📊 Kwaliteitsmetrieken:` |
| **Karakterlimieten** | **Dynamisch** | Van config (min/max/recommended) |
| **Complexiteitsscore** | **Dynamisch** | Berekend per begrip |
| **Leesbaarheid** | **Dynamisch** | Afgeleid van complexiteit |
| **Kwaliteitschecks** | **Dynamisch** | 5 checks gebaseerd op metrics |
| **Context complexiteit** | **Dynamisch** | Alleen bij multi-context |
| **Scoring advies** | **Dynamisch** | Gegenereerd op basis van scores |

### Output Voorbeeld
```markdown
### 📊 Kwaliteitsmetrieken:

**Karakterlimieten:**
- Minimum: 150 karakters
- Maximum: 350 karakters
- Aanbevolen: 250 karakters

**Complexiteit indicatoren:**
- Geschatte woorden: 45
- Complexiteitsscore: 7/10
- Leesbaarheid: Complex

**Kwaliteitschecks:**
- ✅ Enkelvoudige zin mogelijk
- ⚠️ Binnen aanbevolen lengte
- ✅ Geen extreem lange term
- ⚠️ Hanteerbare context
- ✅ Duidelijke term

**Context complexiteit:**
- Aantal contexten: 2
- Multi-context uitdaging: Gemiddeld

**Aanbevelingen voor kwaliteit:**
- ⚠️ Hoge complexiteit - overweeg vereenvoudiging of opdeling
- 🔍 Aandachtspunten: Binnen aanbevolen lengte, Hanteerbare context
```

### Complexiteitsscore Berekening
```python
def _calculate_metrics(self, begrip, org_contexts, char_limits):
    complexity_factors = []

    # Term complexiteit
    if len(begrip) > 30:
        complexity_factors.append(2)
    elif len(begrip) > 20:
        complexity_factors.append(1)

    # Multi-word term
    if term_words > 3:
        complexity_factors.append(2)
    elif term_words > 1:
        complexity_factors.append(1)

    # Context complexiteit
    if org_contexts and len(org_contexts) > 3:
        complexity_factors.append(2)
    elif org_contexts and len(org_contexts) > 1:
        complexity_factors.append(1)

    # Totaal (1-10 schaal)
    base_complexity = 3
    complexity_score = min(10, base_complexity + sum(complexity_factors))

    # Leesbaarheid afleiding
    if complexity_score <= 3:
        readability = "Eenvoudig"
    elif complexity_score <= 6:
        readability = "Gemiddeld"
    else:
        readability = "Complex"
```

### Shared State Interactions

#### READS
```python
org_contexts = context.get_shared("organization_contexts", [])  # Van ContextAwarenessModule
```

#### WRITES
- Geen

### Belangrijke Notities
- **Informatief, niet bindend**: Deze metrics zijn voor monitoring, niet voor prompt instructies
- **Token overhead**: ~25 regels per prompt zonder directe functie voor GPT-4
- **Potentiële optimalisatie**: Deze sectie kan verwijderd worden zonder kwaliteitsverlies

---

## 11. Output Specification Module

### Identificatie
- **Module ID**: `output_specification`
- **Class**: `OutputSpecificationModule`
- **File**: `src/services/prompts/modules/output_specification_module.py`
- **Priority**: 90 (zeer hoog - komt vroeg in prompt)

### Functie
Genereert **output format specificaties** en karakter limiet waarschuwingen.

### Dependencies
- **Geen**

### Configuratie
```python
{
    "default_min_chars": 150,  # Standaard minimum
    "default_max_chars": 350   # Standaard maximum
}
```

### Statisch vs Dynamisch

| Aspect | Type | Beschrijving |
|--------|------|-------------|
| **Basis format vereisten** | **100% Statisch** | Altijd hetzelfde |
| **Karakter limiet waarschuwing** | **Dynamisch** | Alleen bij afwijkende limieten |
| **Format richtlijnen** | **100% Statisch** | Altijd hetzelfde |

### Output (Basis - Altijd)
```markdown
### 📏 OUTPUT FORMAT VEREISTEN:
- Definitie in één enkele zin
- Geen punt aan het einde
- Geen haakjes voor toelichtingen
- Geen voorbeelden in de definitie
- Focus op WAT het is, niet het doel of gebruik

### 📝 DEFINITIE KWALITEIT:
- Gebruik formele, zakelijke taal
- Vermijd jargon tenzij noodzakelijk voor het vakgebied
- Gebruik concrete, specifieke termen
- Vermijd vage kwalificaties (veel, weinig, meestal)
- Maak onderscheid tussen het begrip en verwante begrippen
```

### Output (Met Karakter Waarschuwing)
```markdown
⚠️ **KARAKTER LIMIET WAARSCHUWING:**
Deze definitie heeft specifieke lengte-eisen:
- Minimum: 100 karakters
- Maximum: 200 karakters
- Streef naar een balans tussen volledigheid en beknoptheid
- Tel alleen de definitie zelf, niet de ontologische marker
```

**Wanneer getoond**: Alleen als min_chars ≠ 150 OF max_chars ≠ 350

### Shared State Interactions

#### WRITES (Conditioneel)
```python
if needs_warning:
    context.set_shared("character_limit_warning", {
        "min": min_chars,
        "max": max_chars
    })
```

#### READS
```python
# Leest uit enriched_context.metadata (NIET shared_state)
metadata = context.enriched_context.metadata
min_chars = metadata.get("min_karakters", self.default_min_chars)
max_chars = metadata.get("max_karakters", self.default_max_chars)
```

### Code Flow
```python
def execute(self, context: ModuleContext) -> ModuleOutput:
    # 1. Haal karakter limieten op (uit metadata of defaults)
    metadata = context.enriched_context.metadata
    min_chars = metadata.get("min_karakters", 150)
    max_chars = metadata.get("max_karakters", 350)

    # 2. Check of er een waarschuwing nodig is
    needs_warning = (min_chars != 150 or max_chars != 350)

    # 3. Bouw secties
    sections = []
    sections.append(self._build_basic_format_requirements())  # ALTIJD

    if needs_warning:
        sections.append(self._build_character_limit_warning(min_chars, max_chars))
        context.set_shared("character_limit_warning", {"min": min_chars, "max": max_chars})

    sections.append(self._build_format_guidelines())  # ALTIJD

    return ModuleOutput(content="\n".join(sections))
```

---

## 12. SAM Rules Module

### Identificatie
- **Module ID**: `sam_rules`
- **Class**: `SamRulesModule`
- **File**: `src/services/prompts/modules/sam_rules_module.py`
- **Priority**: 65 (medium-hoog)

### Functie
Genereert alle **SAM (Samenhang)** validatieregels voor relaties tussen begrippen en cirkeldefinities.

**Identiek patroon als ARAI Rules Module**, maar met SAM- prefix.

### Dependencies, Config, Output
Zie ARAI Rules Module - exact hetzelfde patroon.

---

## 13. Semantic Categorisation Module

### Identificatie
- **Module ID**: `semantic_categorisation`
- **Class**: `SemanticCategorisationModule`
- **File**: `src/services/prompts/modules/semantic_categorisation_module.py`
- **Priority**: 70 (hoog)

### Functie
Genereert **ESS-02 ontologische categorie instructies**. Maakt de UI-geselecteerde categorie expliciet voor het taalmodel met categorie-specifieke guidance.

### Dependencies
- **Geen**

### Configuratie
```python
{
    "detailed_guidance": True  # Toon uitgebreide categorie-specifieke instructies
}
```

### Statisch vs Dynamisch

| Aspect | Type | Beschrijving |
|--------|------|-------------|
| **Basis ESS-02 sectie** | **100% Statisch** | Altijd getoond |
| **Categorie-specifieke guidance** | **Dynamisch** | Alleen als categorie bekend EN detailed_guidance=True |

### Output Structuur

**Basis Sectie (ALTIJD):**
```markdown
### 📐 Let op betekenislaag (ESS-02 - Ontologische categorie):
Je **moet** één van de vier categorieën expliciet maken door de JUISTE KICK-OFF term te kiezen:

• PROCES begrippen → start met: 'activiteit waarbij...', 'handeling die...', 'proces waarin...'
• TYPE begrippen → start met: [kernwoord] dat/die [kenmerk] (bijv. 'woord dat...', 'document dat...', 'persoon die...')
• RESULTAAT begrippen → start met: 'resultaat van...', 'uitkomst van...', 'product dat...'
• EXEMPLAAR begrippen → start met: 'exemplaar van... dat...', 'specifiek geval van...'

⚠️ Let op: Start NOOIT met 'is een' of andere koppelwerkwoorden!
⚠️ Voor TYPE: Start NOOIT met meta-woorden ('soort', 'type', 'categorie')!
De kick-off term MOET een zelfstandig naamwoord zijn dat de categorie aangeeft.

BELANGRIJK: Bepaal de juiste categorie op basis van het BEGRIP zelf:
- Eindigt op -ING of -TIE en beschrijft een handeling? → PROCES
- Is het een gevolg/uitkomst van iets? → RESULTAAT (bijv. sanctie, rapport, besluit)
- Is het een classificatie/soort? → TYPE (begin direct met kernwoord!)
- Is het een specifiek geval? → EXEMPLAAR
```

**Category-Specific Guidance (DYNAMISCH):**

**Voor "proces":**
```markdown
**PROCES CATEGORIE - Formuleer als ACTIVITEIT/HANDELING:**

⚠️ BELANGRIJK: De kick-off termen hieronder zijn ZELFSTANDIGE NAAMWOORDEN (handelingsnaamwoorden),
geen werkwoorden! Ze voldoen dus aan STR-01 (start met zelfstandig naamwoord) en ARAI-01
(geen vervoegd werkwoord als kern).

KICK-OFF opties (kies één):
- 'activiteit waarbij...' → focus op wat er gebeurt
- 'handeling die...' → focus op de actie
- 'proces waarin...' → focus op het verloop

VERVOLG met:
- WIE voert het uit (actor/rol)
- WAT er precies gebeurt (actie)
- HOE het verloopt (stappen/methode)
- WAAR het begint en eindigt (scope)

VOORBEELDEN (GOED):
✅ "activiteit waarbij gegevens worden verzameld door directe waarneming"
✅ "handeling waarin door middel van vraaggesprekken informatie wordt verzameld"
✅ "proces waarin documenten systematisch worden geanalyseerd"

VOORBEELDEN (FOUT):
❌ "is een activiteit waarbij..." (start met 'is')
❌ "het observeren van..." (werkwoordelijk)
❌ "manier om gegevens te verzamelen" (te abstract)
```

**Voor "type":**
```markdown
**TYPE CATEGORIE - Begin met het ZELFSTANDIG NAAMWOORD dat de klasse aanduidt:**

⚠️ BELANGRIJK: Begin DIRECT met het kernwoord, NIET met meta-woorden!

INSTRUCTIE: Start met het zelfstandig naamwoord dat de klasse of soort benoemt

STRUCTUUR van je definitie:
1. Start: [Zelfstandig naamwoord van de klasse]
2. Vervolg: [die/dat/met] [onderscheidend kenmerk]

VERVOLG met:
- BREDERE KLASSE (impliciet door kernwoord keuze)
- ONDERSCHEIDENDE KENMERKEN (wat maakt dit uniek)
- VERSCHIL met andere types (hoe te onderscheiden)

VOORBEELDEN (GOED):
✅ "woord dat handelingen of toestanden uitdrukt"
✅ "document dat juridische beslissingen formeel vastlegt"
✅ "persoon die bevoegd is tot het nemen van besluiten"

VOORBEELDEN (FOUT):
❌ "soort woord dat..." (begin niet met 'soort')
❌ "type document dat..." (begin niet met 'type')
❌ "is een woord dat..." (geen koppelwerkwoord)
```

**Voor "resultaat" en "exemplaar":** Zie modulecode voor volledige guidance.

### Shared State Interactions

#### WRITES
```python
if categorie:
    context.set_shared("ontological_category", categorie)  # Voor TemplateModule en DefinitionTaskModule
```

#### READS
```python
# Leest uit enriched_context.metadata (NIET shared_state)
categorie = context.get_metadata("ontologische_categorie")
```

### Belangrijke Notities
- **UI → Metadata → Module**: De UI bepaalt de categorie en injecteert deze in metadata
- **Module → Shared State → Other Modules**: Deze module deelt de categorie met TemplateModule en DefinitionTaskModule
- **ESS-02 Compliance**: Zonder deze module blijft de categorie alleen metadata; deze module maakt het actionable voor GPT-4
- **Compacte modus mogelijk**: Door `detailed_guidance=False` kan de uitgebreide guidance worden uitgeschakeld (token besparing)

---

## 14. Structure Rules Module

### Identificatie
- **Module ID**: `structure_rules`
- **Class**: `StructureRulesModule`
- **File**: `src/services/prompts/modules/structure_rules_module.py`
- **Priority**: 65 (medium-hoog)

### Functie
Genereert alle **STR (Structuur)** validatieregels voor grammaticale structuur en definitie opbouw.

### Dependencies
- **Geen**

### Configuratie
```python
{
    "include_examples": True  # Toon ✅/❌ voorbeelden
}
```

### Statisch vs Dynamisch
**100% Statisch** - Alle STR regels zijn hardcoded (zoals INT regels).

### Output Structuur
```markdown
### 🏗️ Structuur Regels (STR):

🔹 **STR-01 - definitie start met zelfstandig naamwoord**
🔹 **STR-02 - Kick-off ≠ de term**
🔹 **STR-03 - Definitie ≠ synoniem**
🔹 **STR-04 - Kick-off vervolgen met toespitsing**
🔹 **STR-05 - Definitie ≠ constructie**
🔹 **STR-06 - Essentie ≠ informatiebehoefte**
🔹 **STR-07 - Geen dubbele ontkenning**
🔹 **STR-08 - Dubbelzinnige 'en' is verboden**
🔹 **STR-09 - Dubbelzinnige 'of' is verboden**
```

**9 regels** in totaal (meest uitgebreide regel-module).

### Voorbeeld Regels

**STR-01:**
```markdown
🔹 **STR-01 - definitie start met zelfstandig naamwoord**
- De definitie moet starten met een zelfstandig naamwoord of naamwoordgroep, niet met een werkwoord.
- Let op: Handelingsnaamwoorden ('activiteit', 'proces', 'handeling') zijn zelfstandige naamwoorden!
- Toetsvraag: Begint de definitie met een zelfstandig naamwoord of naamwoordgroep, en niet met een werkwoord?
  ✅ proces dat beslissers identificeert...
  ✅ maatregel die recidive voorkomt...
  ❌ is een maatregel die recidive voorkomt
  ❌ wordt toegepast in het gevangeniswezen
```

**STR-05:**
```markdown
🔹 **STR-05 - Definitie ≠ constructie**
- Een definitie moet aangeven wat iets is, niet uit welke onderdelen het bestaat.
- Toetsvraag: Geeft de definitie aan wat het begrip is, in plaats van alleen waar het uit bestaat?
  ✅ motorvoertuig: gemotoriseerd voertuig dat niet over rails rijdt, zoals auto's, vrachtwagens en bussen
  ❌ motorvoertuig: een voertuig met een chassis, vier wielen en een motor van meer dan 50 cc
```

### Code Pattern (Hardcoded)
```python
def execute(self, context: ModuleContext) -> ModuleOutput:
    sections = []
    sections.append("### 🏗️ Structuur Regels (STR):")
    sections.append("")

    # Elke regel is een aparte method
    sections.extend(self._build_str01_rule())
    sections.extend(self._build_str02_rule())
    sections.extend(self._build_str03_rule())
    # ... tot STR-09

    return ModuleOutput(content="\n".join(sections))
```

### Shared State Interactions
- **Reads**: Geen
- **Writes**: Geen
- **Effect**: Puur output generatie

---

## 15. Template Module

### Identificatie
- **Module ID**: `template`
- **Class**: `TemplateModule`
- **File**: `src/services/prompts/modules/template_module.py`
- **Priority**: 60 (medium)

### Functie
Genereert **definitie templates en patronen** per semantische categorie. Biedt concrete voorbeelden en structurele richtlijnen.

### Dependencies
```python
[]  # Soft dependencies via shared_state
```

Leest `semantic_category` (metadata) en `word_type` (shared_state).

### Configuratie
```python
{
    "include_examples": True,   # Toon voorbeelden per categorie
    "detailed_templates": True  # Toon uitgebreide templates
}
```

### Statisch vs Dynamisch

| Aspect | Type | Beschrijving |
|--------|------|-------------|
| **Header** | Statisch | `### 📋 Definitie Templates:` |
| **Template selectie** | **Dynamisch** | Gebaseerd op semantic_category |
| **Definitiepatronen** | **Dynamisch** | Gebaseerd op word_type |
| **Categorie voorbeelden** | **Dynamisch** | Gebaseerd op semantic_category |

### Categorie Templates (10 categorieën)
```python
templates = {
    "Proces": "[Handeling/activiteit] waarbij [actor/systeem] [actie] uitvoert [met welk doel/resultaat]",
    "Object": "[Fysiek/digitaal ding] dat [kenmerkende eigenschap] heeft en [functie/rol] vervult",
    "Actor": "[Persoon/instantie/systeem] die [verantwoordelijkheid/rol] heeft voor [domein/activiteit]",
    "Toestand": "[Status/situatie] waarin [object/actor] zich bevindt wanneer [voorwaarde/kenmerk]",
    "Gebeurtenis": "[Voorval/incident] dat optreedt wanneer [trigger/voorwaarde] en resulteert in [uitkomst]",
    "Maatregel": "[Interventie/actie] die wordt toegepast om [doel] te bereiken bij [situatie]",
    "Informatie": "[Gegevens/data] over [onderwerp] die [doel/gebruik] dient",
    "Regel": "[Voorschrift/norm] dat bepaalt [wat] onder [welke voorwaarden]",
    "Recht": "[Bevoegdheid/aanspraak] van [rechthebbende] om [wat te doen/krijgen]",
    "Verplichting": "[Plicht/opdracht] voor [verplichte partij] om [actie/nalating] te doen",
}
```

### Definitiepatronen per Woordsoort

**Voor "werkwoord":**
```markdown
- [werkwoord]: handeling waarbij [wie/wat] [actie beschrijving]
- [werkwoord]: proces van het [activiteit omschrijving]
- [werkwoord]: activiteit die leidt tot [resultaat/uitkomst]
```

**Voor "deverbaal":**
```markdown
- [deverbaal]: resultaat van het [werkwoord]
- [deverbaal]: uitkomst waarbij [beschrijving van eindtoestand]
- [deverbaal]: vastgelegde [wat] na afronding van [proces]
```

**Voor "overig":**
```markdown
- [begrip]: [categorie] die/dat [onderscheidend kenmerk]
- [begrip]: [bovenbegrip] met als kenmerk [specificatie]
- [begrip]: [type/soort] [bovenbegrip] voor [doel/functie]
```

### Categorie Voorbeelden

**Voor "Proces":**
```markdown
  ✅ toezicht: systematisch volgen van handelingen om naleving van regels te waarborgen
  ✅ registratie: proces waarbij gegevens formeel worden vastgelegd in een systeem
  ✅ beoordeling: evaluatie van prestaties aan de hand van vooraf bepaalde criteria
```

**Voor "Object":**
```markdown
  ✅ dossier: verzameling documenten die betrekking hebben op één zaak of persoon
  ✅ systeem: geheel van onderling verbonden componenten met een gemeenschappelijk doel
  ✅ register: officiële vastlegging van geordende gegevens voor raadpleging
```

**Voor "Actor", "Maatregel", "Regel":** Zie modulecode.

**Voor onbekende categorie:**
```markdown
  ℹ️ Geen specifieke voorbeelden beschikbaar voor deze categorie
```

### Output Voorbeeld
```markdown
### 📋 Definitie Templates:

**Template voor Proces:**
[Handeling/activiteit] waarbij [actor/systeem] [actie] uitvoert [met welk doel/resultaat]

**Aanbevolen definitiepatronen:**
- [werkwoord]: handeling waarbij [wie/wat] [actie beschrijving]
- [werkwoord]: proces van het [activiteit omschrijving]
- [werkwoord]: activiteit die leidt tot [resultaat/uitkomst]

**Voorbeelden uit categorie Proces:**
  ✅ toezicht: systematisch volgen van handelingen om naleving van regels te waarborgen
  ✅ registratie: proces waarbij gegevens formeel worden vastgelegd in een systeem
  ✅ beoordeling: evaluatie van prestaties aan de hand van vooraf bepaalde criteria
```

### Shared State Interactions

#### READS
```python
category = context.get_metadata("semantic_category", "algemeen")  # Van metadata
word_type = context.get_shared("word_type", "overig")              # Van ExpertiseModule
```

#### WRITES
- Geen

### Code Flow
```python
def execute(self, context: ModuleContext) -> ModuleOutput:
    # 1. Haal categorie en woordsoort op
    category = context.get_metadata("semantic_category", "algemeen")
    word_type = context.get_shared("word_type", "overig")

    # 2. Bouw sectie
    sections = []
    sections.append("### 📋 Definitie Templates:")

    # 3. Template voor categorie
    template = self._get_category_template(category)
    if template:
        sections.append(f"**Template voor {category}:**")
        sections.append(template)

    # 4. Patronen voor woordsoort
    patterns = self._get_definition_patterns(word_type)
    if patterns:
        sections.append("**Aanbevolen definitiepatronen:**")
        sections.extend(patterns)

    # 5. Voorbeelden voor categorie
    if self.include_examples:
        examples = self._get_category_examples(category)
        sections.append(f"**Voorbeelden uit categorie {category}:**")
        sections.extend(examples)

    return ModuleOutput(content="\n".join(sections))
```

### Validation Logic
```python
def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
    # Check of we categorie informatie hebben
    category = context.get_metadata("semantic_category")
    if not category and self.detailed_templates:
        return False, "Geen semantische categorie beschikbaar voor templates"

    return True, None
```

**Als geen categorie**: Module wordt overgeslagen (bij detailed_templates=True).

---

## 16. VER Rules Module

### Identificatie
- **Module ID**: `ver_rules`
- **Class**: `VerRulesModule`
- **File**: `src/services/prompts/modules/ver_rules_module.py`
- **Priority**: 60 (medium)

### Functie
Genereert alle **VER (Vorm)** validatieregels voor enkelvoud/meervoud en werkwoord vorm.

**Identiek patroon als ARAI Rules Module**, maar met VER- prefix.

### Dependencies, Config, Output
Zie ARAI Rules Module - exact hetzelfde patroon.

---

## Shared State Systeem

Het **shared_state** dictionary is het communicatiemechanisme tussen modules. Het wordt **1x** aangemaakt in `ModuleContext` en door **reference** gedeeld met alle modules.

### Shared State Flow

```
PromptOrchestrator.build_prompt()
│
├─→ Creates: ModuleContext(shared_state={})  ← EMPTY dict
│
├─→ Priority 100: ExpertiseModule
│   └─→ WRITES: shared_state["word_type"] = "werkwoord"
│
├─→ Priority 70: ContextAwarenessModule
│   ├─→ WRITES: shared_state["context_richness_score"] = 0.85
│   ├─→ WRITES: shared_state["organization_contexts"] = ["OM", "Reclassering"]
│   ├─→ WRITES: shared_state["juridical_contexts"] = ["Strafrecht"]
│   └─→ WRITES: shared_state["legal_basis_contexts"] = ["WvSr"]
│
├─→ Priority 70: SemanticCategorisationModule
│   └─→ WRITES: shared_state["ontological_category"] = "type"
│
├─→ Priority 85: GrammarModule
│   └─→ READS: word_type = shared_state["word_type"]  ← Van ExpertiseModule
│
├─→ Priority 60: TemplateModule
│   ├─→ READS: word_type = shared_state["word_type"]          ← Van ExpertiseModule
│   └─→ READS: category = metadata["semantic_category"]       ← Van metadata
│
├─→ Priority 50: ErrorPreventionModule
│   ├─→ READS: org_contexts = shared_state["organization_contexts"]  ← Van ContextAwarenessModule
│   ├─→ READS: jur_contexts = shared_state["juridical_contexts"]
│   └─→ READS: wet_contexts = shared_state["legal_basis_contexts"]
│
└─→ Priority 10: DefinitionTaskModule
    ├─→ READS: word_type = shared_state["word_type"]
    ├─→ READS: ontological_category = shared_state["ontological_category"]
    ├─→ READS: org_contexts = shared_state["organization_contexts"]
    ├─→ READS: jur_contexts = shared_state["juridical_contexts"]
    └─→ READS: wet_basis = shared_state["legal_basis_contexts"]
```

### Shared State Keys (Complete Lijst)

| Key | Type | Set By | Read By | Purpose |
|-----|------|--------|---------|---------|
| `word_type` | str | ExpertiseModule | GrammarModule, TemplateModule, DefinitionTaskModule | Woordsoort bepaling |
| `context_richness_score` | float | ContextAwarenessModule | (Geen lezers) | Context kwaliteit score |
| `organization_contexts` | list[str] | ContextAwarenessModule | ErrorPreventionModule, MetricsModule, DefinitionTaskModule | Organisatie contexten |
| `juridical_contexts` | list[str] | ContextAwarenessModule | ErrorPreventionModule, DefinitionTaskModule | Juridische contexten |
| `legal_basis_contexts` | list[str] | ContextAwarenessModule | ErrorPreventionModule, DefinitionTaskModule | Wettelijke basis |
| `ontological_category` | str | SemanticCategorisationModule | TemplateModule, DefinitionTaskModule | Ontologische categorie |
| `character_limit_warning` | dict | OutputSpecificationModule | (Geen lezers) | Karakterlimiet info |

### Metadata vs Shared State

**Metadata** (`context.enriched_context.metadata`):
- Komt van **buiten** het prompt systeem (UI, database)
- **Read-only** voor modules
- Bevat: `ontologische_categorie`, `semantic_category`, `min_karakters`, `max_karakters`

**Shared State** (`context.shared_state`):
- Wordt **intern** gebouwd door modules
- **Read-write** voor modules
- Bevat: Afgeleide informatie voor module communicatie

**Voorbeeld:**
```python
# Metadata → Shared State transformatie in SemanticCategorisationModule
categorie = context.get_metadata("ontologische_categorie")  # Van UI
context.set_shared("ontological_category", categorie)       # Voor andere modules
```

---

## Dependency Graph

### Expliciete Dependencies (Via get_dependencies())

```
DefinitionTaskModule
├─→ semantic_categorisation
└─→ context_awareness

ErrorPreventionModule
└─→ context_awareness

TemplateModule (validates but doesn't declare)
└─→ (semantic_category via metadata)

Alle Regel Modules (ARAI, CON, ESS, INT, SAM, STR, VER)
└─→ Geen dependencies
```

### Impliciete Dependencies (Via Shared State)

```
GrammarModule
└─→ (word_type) ← ExpertiseModule

TemplateModule
├─→ (word_type) ← ExpertiseModule
└─→ (semantic_category) ← metadata

ErrorPreventionModule
├─→ (organization_contexts) ← ContextAwarenessModule
├─→ (juridical_contexts) ← ContextAwarenessModule
└─→ (legal_basis_contexts) ← ContextAwarenessModule

MetricsModule
└─→ (organization_contexts) ← ContextAwarenessModule

DefinitionTaskModule
├─→ (word_type) ← ExpertiseModule
├─→ (ontological_category) ← SemanticCategorisationModule
├─→ (organization_contexts) ← ContextAwarenessModule
├─→ (juridical_contexts) ← ContextAwarenessModule
└─→ (legal_basis_contexts) ← ContextAwarenessModule
```

### Execution Order (Priority-Based)

```
Priority 100: ExpertiseModule                    ← Sets word_type
Priority 90:  OutputSpecificationModule
Priority 85:  GrammarModule                      ← Uses word_type
Priority 75:  AraiRulesModule, EssRulesModule
Priority 70:  ContextAwarenessModule             ← Sets org/jur/wet contexts
              ConRulesModule
              SemanticCategorisationModule       ← Sets ontological_category
Priority 65:  StructureRulesModule
              IntegrityRulesModule
              SamRulesModule
Priority 60:  TemplateModule                     ← Uses word_type, category
              VerRulesModule
Priority 50:  ErrorPreventionModule              ← Uses org/jur/wet contexts
Priority 30:  MetricsModule                      ← Uses org contexts
Priority 10:  DefinitionTaskModule               ← Uses ALL shared state
```

**Kritieke Observatie**: De priority volgorde respecteert de data dependencies! Modules die data **schrijven** hebben hogere priority dan modules die deze data **lezen**.

---

## Context Duplication Analysis

### Problem Statement
Context informatie verschijnt **3 keer** in de finale prompt via verschillende modules zonder coördinatie.

### Duplication Locations

#### Location 1: ContextAwarenessModule (regel 62-68)
```markdown
📊 UITGEBREIDE CONTEXT ANALYSE:
⚠️ VERPLICHT: Gebruik onderstaande specifieke context...

ORGANISATORISCH:
  • OM
  • Reclassering

JURIDISCH:
  • Strafrecht

WETTELIJK:
  • Wetboek van Strafrecht
```

**Purpose**: Primaire context instructies voor GPT-4
**Module Priority**: 70
**Data Source**: `enriched_context.base_context`

#### Location 2: ErrorPreventionModule (regel 340-343)
```markdown
### 🚨 CONTEXT-SPECIFIEKE VERBODEN:
- Gebruik de term 'OM' of een variant daarvan niet letterlijk in de definitie.
- Gebruik de term 'Openbaar Ministerie' of een variant daarvan niet letterlijk in de definitie.
- Gebruik de term 'Reclassering' of een variant daarvan niet letterlijk in de definitie.
- Vermijd expliciete vermelding van juridisch context 'Strafrecht' in de definitie.
- Vermijd expliciete vermelding van wetboek 'Wetboek van Strafrecht' in de definitie.
```

**Purpose**: Context-specifieke verboden patronen
**Module Priority**: 50
**Data Source**: `shared_state` (van ContextAwarenessModule)

#### Location 3: DefinitionTaskModule (regel 418-423)
```markdown
🆔 Promptmetadata:
- Begrip: slachtoffer
- Termtype: werkwoord
- Organisatorische context: OM, Reclassering
- Juridische context: Strafrecht
- Wettelijke basis: Wetboek van Strafrecht
```

**Purpose**: Metadata voor traceerbaarheid
**Module Priority**: 10
**Data Source**: `shared_state` (van ContextAwarenessModule)

### Duplication Metrics

| Context Value | Occurrence 1 | Occurrence 2 | Occurrence 3 | Total Chars |
|---------------|--------------|--------------|--------------|-------------|
| "OM" | Regel 66 (ORGANISATORISCH) | Regel 341 (verboden) | Regel 421 (metadata) | 6 chars × 3 = 18 |
| "Reclassering" | Regel 66 (ORGANISATORISCH) | Regel 343 (verboden) | Regel 421 (metadata) | 13 chars × 3 = 39 |
| "Strafrecht" | Regel 67 (JURIDISCH) | Regel 344 (verboden) | Regel 422 (metadata) | 11 chars × 3 = 33 |
| "Wetboek van Strafrecht" | Regel 68 (WETTELIJK) | Regel 345 (verboden) | Regel 423 (metadata) | 23 chars × 3 = 69 |

**Total Duplicate Character Count**: 159 characters
**Estimated Token Overhead**: ~40-50 tokens per prompt

### Instruction Duplication

De instructie **"gebruik context niet letterlijk"** verschijnt **6 keer**:

1. **Regel 63**: "zonder de context expliciet te benoemen" (ContextAwarenessModule)
2. **Regel 143**: "Contextspecifieke formulering zonder expliciete benoeming" (CON-01 regel)
3. **Regel 341-342**: "Gebruik de term 'X' niet letterlijk" (ErrorPreventionModule, per context item)
4. **Regel 350**: "Noem context niet letterlijk" (ErrorPreventionModule validatiematrix)
5. **Regel 355**: "context en bronnen mogen niet letterlijk of herleidbaar in de definitie voorkomen" (ErrorPreventionModule laatste waarschuwing)
6. **Regel 396**: "Context verwerkt zonder expliciete benoeming" (DefinitionTaskModule checklist)

**Estimated Token Overhead**: ~100-150 tokens per prompt

### Root Cause

**Lack of Module Coordination**: Modules voegen elk hun eigen context sectie toe zonder te weten wat andere modules al hebben toegevoegd.

**Why This Happens:**
1. ContextAwarenessModule voegt primaire context toe (functie)
2. ErrorPreventionModule voegt context-specifieke verboden toe (functie)
3. DefinitionTaskModule voegt metadata toe (traceerbaarheid)

Elk heeft een **legitieme reden** om context te tonen, maar er is **geen deduplicatie** mechanisme.

### Impact Assessment

**Token Waste**: ~150-200 tokens per prompt
**At 1,000 requests/day**: 150,000-200,000 tokens/day
**Annual Cost**: ~€500-700 verspild aan duplicate tokens

**Cognitive Load**: GPT-4 moet dezelfde informatie 3x verwerken, wat kan leiden tot:
- Verhoogde kans op inconsistentie
- Lagere attention op andere instructies
- Potentiële verwarring bij tegenstrijdige formuleringen

### Recommended Solution

**Option A: Centralize Context Display** (Preferred)
```python
# In PromptOrchestrator, after all modules execute:
def _deduplicate_context_sections(self, module_outputs):
    """Remove duplicate context mentions, keep only primary"""
    # Keep ContextAwarenessModule output
    # Remove context from ErrorPreventionModule (keep only non-context forbidden patterns)
    # Remove context metadata from DefinitionTaskModule
```

**Option B: Context Module Flag**
```python
# Add to shared_state:
context.set_shared("context_displayed", True)  # In ContextAwarenessModule

# In ErrorPreventionModule and DefinitionTaskModule:
if context.get_shared("context_displayed"):
    # Skip adding context again
```

**Option C: Consolidate in Single Module**
```python
# Create new ContextConsolidationModule (priority 70)
# Combines:
# - Primary context display (from ContextAwarenessModule)
# - Context-specific forbidden patterns (from ErrorPreventionModule)
# - Context metadata (from DefinitionTaskModule)
```

**Expected Savings**: 150-200 tokens per prompt (20-25% of current prompt size)

---

## Performance Characteristics

### Module Execution Timing (Estimated)

| Module | Priority | Execution Time | Complexity |
|--------|----------|----------------|------------|
| ExpertiseModule | 100 | ~1ms | O(n) woordsoort detectie |
| OutputSpecificationModule | 90 | ~1ms | O(1) string building |
| GrammarModule | 85 | ~2ms | O(1) conditionals |
| AraiRulesModule | 75 | ~10ms | O(n) regel formatting |
| EssRulesModule | 75 | ~10ms | O(n) regel formatting |
| ContextAwarenessModule | 70 | ~5ms | O(n) context processing |
| ConRulesModule | 70 | ~8ms | O(n) regel formatting |
| SemanticCategorisationModule | 70 | ~3ms | O(1) template lookup |
| StructureRulesModule | 65 | ~15ms | O(1) hardcoded rules |
| IntegrityRulesModule | 65 | ~12ms | O(1) hardcoded rules |
| SamRulesModule | 65 | ~8ms | O(n) regel formatting |
| TemplateModule | 60 | ~4ms | O(1) lookups |
| VerRulesModule | 60 | ~6ms | O(n) regel formatting |
| ErrorPreventionModule | 50 | ~8ms | O(n) context mapping |
| MetricsModule | 30 | ~3ms | O(1) calculations |
| DefinitionTaskModule | 10 | ~2ms | O(1) string building |

**Total Estimated Execution Time**: ~100-120ms per prompt generation

### Memory Characteristics

**Regel Cache (CachedToetsregelManager):**
- **Initialization**: 1x bij eerste gebruik
- **Memory**: ~50-100KB voor alle regels
- **Sharing**: Singleton pattern - 1 instantie voor alle modules
- **Performance**: 77% sneller dan individuele loads (US-202)

**ModuleContext Object:**
- **Size**: ~5-10KB per request
- **Lifetime**: Single request scope
- **Sharing**: Passed by reference (geen copying overhead)

**Module Instances:**
- **Lifecycle**: Singleton per `PromptOrchestrator` instance
- **Memory**: ~1-2KB per module × 19 modules = ~20-40KB
- **Reuse**: Modules worden hergebruikt voor alle requests

### Optimization Opportunities

**Identified in DEF-156 Analysis:**

1. **Context Deduplication** (High Priority)
   - Savings: 150-200 tokens per prompt
   - Effort: 2-4 hours
   - Risk: Low

2. **Forbidden Starters Consolidation** (Medium Priority)
   - Savings: ~40 lines → 1 regex pattern = 38 lines
   - Effort: 1 hour
   - Risk: Low

3. **Example Reduction** (Medium Priority)
   - Current: 56 ✅/❌ examples
   - Proposed: 20 best examples
   - Savings: ~35 lines
   - Effort: 2-3 hours (curation)
   - Risk: Medium (quality impact)

4. **Metadata Removal** (Low Priority)
   - Savings: ~20 lines per prompt
   - Effort: 30 minutes
   - Risk: Low (metadata is informational only)

5. **Conditional Rule Loading** (High Effort, High Value)
   - Current: All 45 rules loaded always
   - Proposed: Load only relevant rules per term type
   - Savings: ~50-60% of rule sections
   - Effort: 8-12 hours
   - Risk: Medium (requires rule categorization)

**Total Optimization Potential**: From 423 lines to ~200 lines (53% reduction)

---

## Conclusion

Dit document beschrijft de complete architectuur van het modulaire prompt systeem. De belangrijkste bevindingen:

### ✅ Strengths
1. **Clean Modularity**: Elke module heeft duidelijke verantwoordelijkheid
2. **Shared State Pattern**: Effectieve inter-module communicatie
3. **Priority-Based Execution**: Respecteert data dependencies
4. **Cached Regel Loading**: Efficiënte regel hergebruik (US-202)
5. **Adaptive Context**: Intelligente aanpassing aan context kwaliteit

### ⚠️ Issues Identified (DEF-156)
1. **Context Duplication**: 3x hetzelfde context (150-200 tokens waste)
2. **Instruction Redundancy**: 6x "gebruik context niet letterlijk"
3. **Excessive Forbidden Starters**: 39 items kan 1 pattern zijn
4. **Example Overload**: 56 voorbeelden, 20 is genoeg
5. **No Conditional Loading**: Alle 45 regels altijd, ongeacht relevantie

### 📊 Optimization Impact (If Implemented)
- **Current**: 423 lines, ~7,000 tokens
- **Optimized**: ~200 lines, ~3,000 tokens
- **Reduction**: 53% smaller prompts
- **Annual Savings**: €10,400/year (at 1,000 requests/day)
- **Quality Impact**: Minimal to positive (better focus)

---

**Document Einde**

*Voor implementatie details van optimalisaties, zie DEF-156 implementation plan.*
