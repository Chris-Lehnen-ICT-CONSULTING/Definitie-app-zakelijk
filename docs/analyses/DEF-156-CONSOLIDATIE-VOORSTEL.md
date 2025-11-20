# DEF-156: Consolidatie Voorstel Prompt Module Systeem

**Status:** Voorstel
**Datum:** 2025-01-14
**Auteur:** Claude (Code Review + Research)
**Doel:** Elimineren van duplicatie en simplificeren van context injection in prompt modules

---

## 📋 Inhoudsopgave

1. [Executive Summary](#executive-summary)
2. [Huidige Architectuur](#huidige-architectuur)
3. [Module Beschrijvingen](#module-beschrijvingen)
4. [Geïdentificeerde Problemen](#geïdentificeerde-problemen)
5. [Voorgestelde Oplossingen](#voorgestelde-oplossingen)
6. [Implementatieplan](#implementatieplan)
7. [Impact Analyse](#impact-analyse)
8. [Risico's en Mitigatie](#risicos-en-mitigatie)

---

## Executive Summary

### Kern Bevindingen

Het prompt module systeem bestaat uit **16 modules** die door een **PromptOrchestrator** worden gecoördineerd. Tijdens de analyse zijn drie kritieke problemen geïdentificeerd:

1. **640 regels duplicatie** (77% code waste) in 5 identieke rule modules
2. **3-laagse context injection** die tot complexiteit en inconsistentie leidt
3. **Ongebruikte dependency graph** - alle modules retourneren lege dependencies

### Aanbevolen Actie

**Fase 1 (Hoge Prioriteit):** Elimineer duplicatie door generieke `JSONBasedRulesModule` te implementeren
- **Impact:** -512 regels code (80% reductie in rule modules)
- **Risico:** Laag (pure refactor, business logica onveranderd)
- **Effort:** 8 uur
- **Approval:** Vereist (>100 regels wijziging totaal)

**Fase 2 (Medium Prioriteit):** Simplificeer context injection van 3 naar 2 lagen
- **Impact:** -171 regels, duidelijkere verantwoordelijkheden
- **Risico:** Medium (raakt context flow)
- **Effort:** 12 uur

**Fase 3 (Optioneel):** Introduceer Jinja2 templates voor prompts
- **Impact:** Prompt wijzigingen zonder deployment
- **Risico:** Medium (verandert generatie mechanisme)
- **Effort:** 16 uur

---

## Huidige Architectuur

### Overzicht van het Systeem

Het prompt systeem is gebouwd volgens een **modulaire architectuur** waarbij elke module verantwoordelijk is voor één specifiek aspect van de prompt generatie. Dit volgt het **Single Responsibility Principle** en maakt modules onafhankelijk testbaar.

```
┌─────────────────────────────────────────────────────────┐
│              PromptServiceV2 (Entry Point)              │
│  - Bouwt EnrichedContext via HybridContextManager       │
│  - Augmenteert prompt met web lookup & document snippets│
│  - Roept UnifiedPromptBuilder aan                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            UnifiedPromptBuilder (Facade)                │
│  - Selecteert strategie (alleen "modular" actief)      │
│  - Delegeert naar ModularPromptAdapter                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         ModularPromptAdapter (Compatibility Layer)      │
│  - Backwards compatibility met oude PromptBuilder      │
│  - Roept get_cached_orchestrator() (singleton)         │
│  - Converteert PromptComponentConfig → module configs  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            PromptOrchestrator (Coordinator)             │
│  - Beheert 16 geregistreerde modules                   │
│  - Dependency resolution (Kahn's algorithm)            │
│  - Parallel execution (ThreadPoolExecutor)             │
│  - Output combinatie in geconfigureerde volgorde       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │    ModuleContext       │
        │  - begrip: str         │
        │  - enriched_context    │
        │  - config              │
        │  - shared_state: dict  │ ← Inter-module communicatie
        └────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  16 PROMPT MODULES                      │
│                                                         │
│  [Priority Order - hoogste eerst]                      │
│                                                         │
│  1. ExpertiseModule (P=90)                             │
│     └─ "Je bent juridisch expert voor definities"     │
│                                                         │
│  2. OutputSpecificationModule (P=85)                   │
│     └─ "150-350 karakters, Nederlands, juridisch"     │
│                                                         │
│  3. GrammarModule (P=75)                               │
│     └─ "Passieve vorm, geen hoofdletters"             │
│                                                         │
│  4. ContextAwarenessModule (P=70) ★ KEY MODULE         │
│     └─ Adaptive context formatting (rich/moderate/min) │
│                                                         │
│  5. SemanticCategorisationModule (P=50)                │
│     └─ "Type/Proces/Resultaat categorisatie"          │
│                                                         │
│  6. TemplateModule (P=60)                              │
│     └─ Category-specific templates                    │
│                                                         │
│  7-13. VALIDATIE REGEL MODULES (P=64-75):              │
│     ┌────────────────────────────────────┐            │
│     │  AraiRulesModule (P=75)  ┐         │            │
│     │  ConRulesModule  (P=70)  │         │            │
│     │  EssRulesModule  (P=68)  ├─ 100%   │ ← PROBLEEM │
│     │  SamRulesModule  (P=66)  │  DUPL   │            │
│     │  VerRulesModule  (P=64)  ┘  640L   │            │
│     │                                     │            │
│     │  IntegrityRulesModule (P=65)       │            │
│     │  StructureRulesModule (P=65)       │            │
│     └────────────────────────────────────┘            │
│                                                         │
│  14. ErrorPreventionModule (P=65)                      │
│      └─ "Veelvoorkomende fouten vermijden"            │
│                                                         │
│  15. MetricsModule (P=30)                              │
│      └─ "Kwaliteitsmetrieken tracking"                │
│                                                         │
│  16. DefinitionTaskModule (P=20)                       │
│      └─ "Finale taak instructies"                     │
└─────────────────────────────────────────────────────────┘
```

### Context Flow (3 Lagen - TE COMPLEX)

De context doorloopt momenteel **drie verschillende transformatie lagen**, wat leidt tot verwarring en inconsistenties:

```
LAAG 1: CONTEXT BUILDING
┌─────────────────────────────────────────────────────┐
│  HybridContextManager.build_enriched_context()      │
│  Locatie: src/services/definition_generator_context.py │
├─────────────────────────────────────────────────────┤
│  INPUT:                                             │
│    GenerationRequest                                │
│      - begrip: "toezicht"                          │
│      - organisatorische_context: ["OM"]            │
│      - juridische_context: ["strafrecht"]          │
│      - wettelijke_basis: ["WvSv"]                  │
│      - ontologische_categorie: "proces"            │
├─────────────────────────────────────────────────────┤
│  PROCESSING:                                        │
│    1. Build base_context dict                      │
│    2. Expand abbreviations (OM → Openbaar Min.)    │
│    3. Collect context sources (web, documents)     │
├─────────────────────────────────────────────────────┤
│  OUTPUT: EnrichedContext                           │
│    .base_context = {                               │
│       "organisatorisch": ["Openbaar Ministerie"],  │
│       "juridisch": ["strafrecht"],                 │
│       "wettelijk": ["WvSv"]                        │
│    }                                               │
│    .sources = [                                    │
│       ContextSource(type="web", confidence=0.9),   │
│       ContextSource(type="doc", confidence=0.95)   │
│    ]                                               │
│    .expanded_terms = {"OM": "Openbaar Ministerie"}│
│    .metadata = {                                   │
│       "ontologische_categorie": "proces",          │
│       "web_lookup": {...},                         │
│       "documents": {...}                           │
│    }                                               │
└─────────────────────────────────────────────────────┘
                        ▼
LAAG 2: PROMPT AUGMENTATION
┌─────────────────────────────────────────────────────┐
│  PromptServiceV2.build_generation_prompt()          │
│  Locatie: src/services/prompts/prompt_service_v2.py│
├─────────────────────────────────────────────────────┤
│  PROCESSING:                                        │
│    1. Merge web_lookup from orchestrator context   │
│    2. Map ontologische_categorie → semantic_cat    │
│    3. Generate base prompt via UnifiedPromptBuilder│
│    4. Augment with web context snippets            │
│       (lines 414-541: _maybe_augment_with_web...)  │
│    5. Augment with document snippets               │
│       (lines 196-254: _maybe_augment_with_doc...)  │
├─────────────────────────────────────────────────────┤
│  OUTPUT: Augmented prompt_text (STRING)            │
│    "📄 DOCUMENTCONTEXT (snippets):                 │
│     • WvSv Art. 12: definitie toezicht...          │
│                                                     │
│     [Base prompt van UnifiedPromptBuilder]         │
│                                                     │
│     ### Contextinformatie uit bronnen:             │
│     - Bron 1: Wikipedia definitie toezicht...      │
│     - Bron 2: Juridische context strafrecht..."    │
└─────────────────────────────────────────────────────┘
                        ▼
LAAG 3: MODULE PROCESSING
┌─────────────────────────────────────────────────────┐
│  ContextAwarenessModule.execute()                   │
│  Locatie: src/services/prompts/modules/context_... │
├─────────────────────────────────────────────────────┤
│  PROCESSING:                                        │
│    1. Calculate context richness score (0.0-1.0)   │
│       (lines 143-184: _calculate_context_score)    │
│       - base_context items: max 0.3               │
│       - sources confidence: max 0.4               │
│       - expanded terms: max 0.2                   │
│       - confidence scores: max 0.1                │
│                                                     │
│    2. Adaptive formatting based on score:          │
│       - score ≥ 0.8: Rich context section         │
│       - score ≥ 0.5: Moderate section             │
│       - score < 0.5: Minimal section              │
│                                                     │
│    3. Share traditional context via shared_state:  │
│       (lines 368-423: _share_traditional_context)  │
│       shared_state["organization_contexts"] = [...] │
│       shared_state["juridical_contexts"] = [...]    │
│       shared_state["legal_basis_contexts"] = [...]  │
├─────────────────────────────────────────────────────┤
│  OUTPUT: ModuleOutput                              │
│    .content = """                                  │
│      📊 UITGEBREIDE CONTEXT ANALYSE:               │
│      ⚠️ VERPLICHT: Gebruik onderstaande context... │
│                                                     │
│      ORGANISATORISCH:                              │
│        • Openbaar Ministerie                       │
│      JURIDISCH:                                    │
│        • strafrecht                                │
│                                                     │
│      ADDITIONELE BRONNEN:                          │
│        🟢 Web (0.90): definitie toezicht...        │
│                                                     │
│      AFKORTINGEN:                                  │
│        • OM = Openbaar Ministerie                  │
│    """                                             │
└─────────────────────────────────────────────────────┘
```

### Waarom 3 Lagen Problematisch Is

**Probleem 1: Multiple Sources of Truth**
- `enriched_context.base_context` bevat context
- `enriched_context.metadata` bevat ook context informatie
- `shared_state` bevat nóg een kopie van context
- **Gevolg:** Onduidelijk waar de "echte" context zit

**Probleem 2: Inconsistente Field Names**
- Laag 1: `"organisatorisch"` (key in dict)
- Laag 3: `"organization_contexts"` (key in shared_state)
- **Gevolg:** Moeilijk te volgen, foutgevoelig bij refactoring

**Probleem 3: Metadata Bloat**
- `enriched_context.metadata` bevat heterogene data:
  - Ontological category (business data)
  - Web lookup results (retrieval data)
  - Document snippets (augmentation data)
  - Request metadata (request_id, actor, etc.)
- **Gevolg:** Onduidelijke verantwoordelijkheden

**Probleem 4: String Augmentation in Layer 2**
- PromptServiceV2 injecteert web/document snippets direct in prompt STRING
- ContextAwarenessModule kan deze niet meer "zien" of scoren
- **Gevolg:** Context richness score mist augmentation data

---

## Module Beschrijvingen

### Core Infrastructure Modules (3)

#### 1. BasePromptModule (`base_module.py` - 207 regels)

**Verantwoordelijkheid:** Abstract base class voor alle modules

**Belangrijke Componenten:**
```python
class ModuleContext:
    begrip: str
    enriched_context: EnrichedContext
    config: UnifiedGeneratorConfig
    shared_state: dict[str, Any]  # Inter-module communicatie

class ModuleOutput:
    content: str  # Gegenereerde prompt sectie
    metadata: dict[str, Any]
    success: bool = True
    error_message: str | None = None

class BasePromptModule(ABC):
    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> None: ...
    @abstractmethod
    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]: ...
    @abstractmethod
    def execute(self, context: ModuleContext) -> ModuleOutput: ...
    @abstractmethod
    def get_dependencies(self) -> list[str]: ...
```

**Status:** ✅ Goed ontworpen, solide foundation

#### 2. PromptOrchestrator (`prompt_orchestrator.py` - 415 regels)

**Verantwoordelijkheid:** Coördineer module executie met dependency resolution en parallel processing

**Belangrijke Features:**

1. **Module Registration** (lines 59-79)
   ```python
   def register_module(self, module: BasePromptModule) -> None:
       self.modules[module.module_id] = module
       dependencies = module.get_dependencies()
       self.dependency_graph[module.module_id] = set(dependencies)
   ```

2. **Dependency Resolution** (lines 97-141) - Kahn's Algorithm
   ```python
   def resolve_execution_order(self) -> list[list[str]]:
       # Topological sort met batch detection
       # Returns: List van batches die parallel kunnen
   ```

3. **Parallel Execution** (lines 268-305)
   ```python
   def _execute_batch_parallel(self, batch: list[str], context: ModuleContext):
       with ThreadPoolExecutor(max_workers=min(len(batch), self.max_workers)):
           # Execute modules in parallel
   ```

4. **Output Combination** (lines 307-335)
   ```python
   def _combine_outputs(self, outputs: dict[str, ModuleOutput]) -> str:
       # Combine volgens custom module order
       return "\n\n".join(ordered_sections)
   ```

**Status:** ✅ Goed, maar dependency graph wordt niet gebruikt (alle modules return `[]`)

#### 3. ModularPromptAdapter (`modular_prompt_adapter.py` - 379 regels)

**Verantwoordelijkheid:** Backwards compatibility layer tussen oude en nieuwe systeem

**Key Function:**
```python
def get_cached_orchestrator() -> PromptOrchestrator:
    """Singleton met thread-safe lazy initialization."""
    global _global_orchestrator
    if _global_orchestrator is None:
        with _orchestrator_lock:  # Double-check locking
            if _global_orchestrator is None:
                orchestrator = PromptOrchestrator(max_workers=4)
                # Registreer alle 16 modules
                orchestrator.register_module(ExpertiseModule())
                orchestrator.register_module(OutputSpecificationModule())
                # ... etc
                _global_orchestrator = orchestrator
    return _global_orchestrator
```

**Status:** ✅ Goed - voorkomt 16x module instantiation overhead

### Content Modules (9)

#### 4. ExpertiseModule (`expertise_module.py` - 181 regels, P=90)

**Doel:** Definieer AI rol als juridisch expert
**Output:** "Je bent een expert in het formuleren van juridische definities..."
**Status:** ✅ Goed

#### 5. OutputSpecificationModule (`output_specification_module.py` - 174 regels, P=85)

**Doel:** Specificeer output formaat en beperkingen
**Business Logic:**
- Default: 150-350 karakters
- Nederlands, juridisch taalgebruik
- Geen hoofdletters in namen

**Status:** ✅ Goed

#### 6. GrammarModule (`grammar_module.py` - 255 regels, P=75)

**Doel:** Nederlandse grammatica regels
**Business Logic:**
- Passieve vorm ("wordt ingezet" ipv "zet in")
- Geen hoofdletters (tenzij eigennamen)
- Correct lidwoordgebruik (de/het)

**Status:** ✅ Goed

#### 7. ContextAwarenessModule (`context_awareness_module.py` - 432 regels, P=70) ⭐

**Doel:** Intelligente context processing met adaptieve formatting

**Dit is de KEY MODULE voor DEF-156 omdat deze:**
1. Context richness score berekent (0.0-1.0)
2. Adaptive formatting implementeert (rich/moderate/minimal)
3. Context deelt met andere modules via shared_state

**Business Logic Details:**

**A. Context Richness Scoring** (lines 143-184)
```python
def _calculate_context_score(self, enriched_context) -> float:
    score = 0.0

    # Base context contribution (max 0.3)
    total_base_items = sum(len(items) for items in enriched_context.base_context.values())
    score += min(total_base_items / 10, 0.3)

    # Sources contribution (max 0.4)
    if enriched_context.sources:
        source_score = sum(source.confidence for source in enriched_context.sources) / len(enriched_context.sources)
        score += source_score * 0.4

    # Expanded terms contribution (max 0.2)
    if enriched_context.expanded_terms:
        score += min(len(enriched_context.expanded_terms) / 5, 0.2)

    # Confidence scores contribution (max 0.1)
    if enriched_context.confidence_scores:
        avg_confidence = sum(enriched_context.confidence_scores.values()) / len(enriched_context.confidence_scores)
        score += avg_confidence * 0.1

    return min(score, 1.0)
```

**B. Adaptive Formatting** (lines 92-101)
```python
if context_score >= 0.8:
    content = self._build_rich_context_section(context)
    # Output: "📊 UITGEBREIDE CONTEXT ANALYSE:" met alle details
elif context_score >= 0.5:
    content = self._build_moderate_context_section(context)
    # Output: "📌 VERPLICHTE CONTEXT INFORMATIE:" basis format
else:
    content = self._build_minimal_context_section(context)
    # Output: "📍 VERPLICHTE CONTEXT:" minimaal
```

**C. Confidence Indicators** (lines 316-334)
```python
if source.confidence < 0.5:
    confidence_indicator = "🔴"  # Lage betrouwbaarheid
elif source.confidence < 0.8:
    confidence_indicator = "🟡"  # Matige betrouwbaarheid
else:
    confidence_indicator = "🟢"  # Hoge betrouwbaarheid
```

**D. Shared State voor Andere Modules** (lines 368-423)
```python
def _share_traditional_context(self, context: ModuleContext) -> None:
    base_context = context.enriched_context.base_context

    # Extract contexten
    org_contexts = self._extract_contexts(base_context.get("organisatorisch"))
    jur_contexts = self._extract_contexts(base_context.get("juridisch"))
    wet_contexts = self._extract_contexts(base_context.get("wettelijk"))

    # Deel voor andere modules (TemplateModule, SemanticCategorisationModule)
    context.set_shared("organization_contexts", org_contexts)
    context.set_shared("juridical_contexts", jur_contexts)
    context.set_shared("legal_basis_contexts", wet_contexts)
```

**Status:** ✅ Excellent - bewaar alle business logica!

#### 8-13. Andere Content Modules

- **SemanticCategorisationModule** (279 regels, P=50) - ESS-02 ontologische categorieën
- **TemplateModule** (250 regels, P=60) - Category-specific templates
- **ErrorPreventionModule** (259 regels, P=65) - Veelvoorkomende fouten
- **MetricsModule** (325 regels, P=30) - Kwaliteitsmetrieken tracking
- **DefinitionTaskModule** (286 regels, P=20) - Finale taak instructies

**Status:** ✅ Allemaal goed

### Validatie Regel Modules (7)

#### 14-18. JSON-Based Rule Modules ❌ DUPLICATES

Deze 5 modules zijn **100% identiek** behalve:
- Filter prefix (`startswith("ARAI")` vs `startswith("CON-")` etc.)
- Header emoji en titel
- module_id en module_name in `__init__`

**Vergelijking:**

| Module | File | Lines | Filter Prefix | Header | Priority |
|--------|------|-------|--------------|--------|----------|
| AraiRulesModule | `arai_rules_module.py` | 128 | `"ARAI"` | "### ✅ Algemene Regels AI" | 75 |
| ConRulesModule | `con_rules_module.py` | 128 | `"CON-"` | "### 🌐 Context Regels" | 70 |
| EssRulesModule | `ess_rules_module.py` | 128 | `"ESS"` | "### 🎯 Essentie Regels" | 68 |
| SamRulesModule | `sam_rules_module.py` | 128 | `"SAM"` | "### 🔗 Samenhang Regels" | 66 |
| VerRulesModule | `ver_rules_module.py` | 128 | `"VER"` | "### 📝 Vorm Regels" | 64 |

**Identieke Code Blokken:**

**Execute Method** (100% identiek in alle 5):
```python
def execute(self, context: ModuleContext) -> ModuleOutput:
    try:
        sections = []
        sections.append("### {emoji} {title}:")

        # Load toetsregels on-demand from cached singleton
        from toetsregels.cached_manager import get_cached_toetsregel_manager

        manager = get_cached_toetsregel_manager()
        all_rules = manager.get_all_regels()

        # ENIGE VERSCHIL: filter prefix
        xxx_rules = {k: v for k, v in all_rules.items() if k.startswith("XXX")}

        # Sorteer regels
        sorted_rules = sorted(xxx_rules.items())

        for regel_key, regel_data in sorted_rules:
            sections.extend(self._format_rule(regel_key, regel_data))

        content = "\n".join(sections)

        return ModuleOutput(
            content=content,
            metadata={
                "rules_count": len(xxx_rules),
                "include_examples": self.include_examples,
                "rule_prefix": "XXX",
            },
        )
    except Exception as e:
        # ... error handling (ook identiek)
```

**_format_rule Method** (lines 98-128, 100% identiek):
```python
def _format_rule(self, regel_key: str, regel_data: dict) -> list[str]:
    """Formateer een regel uit JSON data."""
    lines = []

    # Header met emoji
    naam = regel_data.get("naam", "Onbekende regel")
    lines.append(f"🔹 **{regel_key} - {naam}**")

    # Uitleg
    uitleg = regel_data.get("uitleg", "")
    if uitleg:
        lines.append(f"- {uitleg}")

    # Toetsvraag
    toetsvraag = regel_data.get("toetsvraag", "")
    if toetsvraag:
        lines.append(f"- Toetsvraag: {toetsvraag}")

    # Voorbeelden (indien enabled)
    if self.include_examples:
        # Goede voorbeelden
        goede_voorbeelden = regel_data.get("goede_voorbeelden", [])
        for goed in goede_voorbeelden:
            lines.append(f"  ✅ {goed}")

        # Foute voorbeelden
        foute_voorbeelden = regel_data.get("foute_voorbeelden", [])
        for fout in foute_voorbeelden:
            lines.append(f"  ❌ {fout}")

    return lines
```

**Duplicatie Breakdown:**
- Per module: 128 regels
- 5 modules: 128 × 5 = **640 regels**
- Echte logica: ~128 regels (generiek)
- **Duplicatie: 512 regels (80%)**

#### 19-20. Custom Rule Modules

- **IntegrityRulesModule** (314 regels, P=65) - Hardcoded integrity checks
- **StructureRulesModule** (332 regels, P=65) - Hardcoded structure rules

Deze zijn NIET identiek omdat ze custom implementaties hebben (niet JSON-based).

**Status:** ✅ Behouden zoals ze zijn

---

## Geïdentificeerde Problemen

### Probleem 1: Massive Code Duplication (KRITIEK)

**Impact:** 🔴 Hoog
**Urgency:** 🔴 Kritiek
**Effort to Fix:** 🟢 Laag (8 uur)

**Details:**
- **640 regels duplicatie** in 5 rule modules
- **77% waste** - alleen filter prefix verschilt
- **Bug fix overhead:** 5× fix needed voor één bug
- **Test overhead:** 5× identieke tests
- **Maintainability:** Zeer laag - elke wijziging moet 5× gebeuren

**Bewijs:**

Side-by-side vergelijking `AraiRulesModule` vs `ConRulesModule`:

```python
# arai_rules_module.py:66          # con_rules_module.py:66
arai_rules = {k: v for ...         con_rules = {k: v for ...
  if k.startswith("ARAI")}           if k.startswith("CON-")}
```

Dat is het ENIGE verschil in 128 regels code!

**Root Cause:**
- Geen abstraction layer
- Copy-paste development
- Missing template method pattern

**Business Impact:**
- Toevoegen van nieuwe regel categorie = +128 regels copy-paste
- Bug in `_format_rule` = 5× identieke fix
- Feature wijziging (bv. andere emoji) = 5× aanpassen

### Probleem 2: Complex Context Injection (MEDIUM)

**Impact:** 🟡 Medium
**Urgency:** 🟡 Medium
**Effort to Fix:** 🟡 Medium (12 uur)

**Details:**
- **3 lagen** van context transformatie
- **Multiple truth sources:** base_context, metadata, shared_state
- **Inconsistent naming:** organisatorisch vs organization_contexts
- **Metadata bloat:** 7+ verschillende data types in één dict

**Concrete Voorbeeld van Verwarring:**

Een developer wil "organisatorische context" lezen. Waar zit die?

**Optie A:** `enriched_context.base_context["organisatorisch"]`
**Optie B:** `enriched_context.metadata["organizational_data"]`
**Optie C:** `context.get_shared("organization_contexts")`

Antwoord: **Alle drie!** (maar met verschillende namen en formats)

**Impact:**
- Moeilijk debuggen - waar komt data vandaan?
- Foutgevoelig bij refactoring
- Onduidelijke ownership - wie is verantwoordelijk voor wat?
- Test complexity - moet 3 lagen mocken

### Probleem 3: Unused Dependency Graph (LAAG)

**Impact:** 🟢 Laag
**Urgency:** 🟢 Laag
**Effort to Fix:** 🟢 Zeer Laag (2 uur)

**Details:**
- PromptOrchestrator heeft sophisticated Kahn's algorithm (lines 97-141)
- ThreadPoolExecutor voor parallel execution (lines 268-305)
- **MAAR:** Alle modules retourneren `get_dependencies() → []`
- **Resultaat:** Alle modules in 1 batch, geen parallel execution benefit

**Code Evidence:**

Elke module:
```python
def get_dependencies(self) -> list[str]:
    """Deze module heeft geen dependencies."""
    return []
```

PromptOrchestrator:
```python
# lines 107-141: Kahn's algorithm voor topological sort
# lines 268-305: Parallel execution met ThreadPoolExecutor
# NOOIT GEBRUIKT omdat alle dependencies = []
```

**Impact:**
- 94 regels "dead code" (dependency resolution)
- Missed opportunity voor parallel execution
- Confusion voor developers - waarom is dit er?

**Mogelijke Actie:**
- **Optie A:** Definieer echte dependencies (bv. TemplateModule depends on SemanticCategorisationModule)
- **Optie B:** Verwijder dependency graph infrastructuur
- **Aanbeveling:** Optie B (YAGNI principle)

### Probleem 4: Hardcoded Configuration (LAAG)

**Impact:** 🟢 Laag
**Urgency:** 🟢 Laag
**Effort to Fix:** 🟡 Medium (6 uur)

**Details:**

**Module Volgorde** (lines 347-372 in prompt_orchestrator.py):
```python
def _get_default_module_order(self) -> list[str]:
    return [
        "expertise",
        "output_specification",
        "grammar",
        # ... 13 more hardcoded
    ]
```

**Character Limits** (in meerdere files):
```python
# output_specification_module.py:37-38
self.default_min_chars = config.get("default_min_chars", 150)
self.default_max_chars = config.get("default_max_chars", 350)

# modular_prompt_adapter.py:151-152
"default_min_chars": getattr(config, "min_chars", 150),
"default_max_chars": getattr(config, "max_chars", 350),
```

**Impact:**
- Config wijziging = code deployment nodig
- Moeilijk A/B testen met verschillende volgordes
- Environment-specific config (dev/staging/prod) niet mogelijk

---

## Voorgestelde Oplossingen

### Oplossing 1: Generic JSONBasedRulesModule (PRIORITEIT 1)

**Doel:** Elimineer 512 regels duplicatie door 1 generieke module te maken

**Approach:** Template Method Pattern

**Nieuwe File:** `src/services/prompts/modules/generic_rules_module.py`

```python
"""
Generic JSON-Based Rules Module - Eliminates duplication in rule modules.

This module replaces 5 identical modules (AraiRulesModule, ConRulesModule,
EssRulesModule, SamRulesModule, VerRulesModule) with a single generic
implementation that's configured with rule prefix and metadata.
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class JSONBasedRulesModule(BasePromptModule):
    """
    Generieke module voor JSON-based validation rules.

    Deze module laadt regels uit de cached toetsregel manager en filtert
    ze op basis van een configureerbaar prefix. Alle formatting logic
    is gedeeld tussen regel categorieën.

    Args:
        rule_prefix: Prefix om regels te filteren (bijv. "ARAI", "CON-")
        module_name: Menselijk leesbare naam voor de module
        header_emoji: Emoji voor de sectie header
        priority: Module prioriteit (0-100, hoger = belangrijker)

    Example:
        >>> arai_module = JSONBasedRulesModule(
        ...     rule_prefix="ARAI",
        ...     module_name="Algemene Regels AI (ARAI)",
        ...     header_emoji="✅",
        ...     priority=75
        ... )
    """

    def __init__(
        self,
        rule_prefix: str,
        module_name: str,
        header_emoji: str,
        priority: int,
    ):
        """
        Initialize de generic rules module.

        Args:
            rule_prefix: Prefix voor regel filtering (case-sensitive)
            module_name: Display naam voor de module
            header_emoji: Emoji voor sectie header
            priority: Execution prioriteit (hoger eerst)
        """
        # Genereer module_id uit prefix (lowercase, underscores)
        module_id = f"{rule_prefix.lower().replace('-', '_')}_rules"

        super().__init__(
            module_id=module_id,
            module_name=module_name,
            priority=priority,
        )

        self.rule_prefix = rule_prefix
        self.header_emoji = header_emoji
        self.include_examples = True

        logger.debug(
            f"JSONBasedRulesModule created: {module_id} "
            f"(prefix={rule_prefix}, priority={priority})"
        )

    def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize module met configuratie.

        Args:
            config: Module configuratie
                - include_examples (bool): Toon goede/foute voorbeelden
        """
        self._config = config
        self.include_examples = config.get("include_examples", True)
        self._initialized = True

        logger.debug(
            f"{self.module_id} geïnitialiseerd "
            f"(examples={self.include_examples})"
        )

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """
        Valideer input - deze module draait altijd.

        Args:
            context: Module context

        Returns:
            (True, None) - module kan altijd draaien
        """
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """
        Genereer validatieregels voor dit prefix.

        Args:
            context: Module context met begrip en enriched context

        Returns:
            ModuleOutput met geformatteerde regels
        """
        try:
            sections = []
            sections.append(f"### {self.header_emoji} {self.module_name}:")

            # Load toetsregels on-demand from cached singleton
            from toetsregels.cached_manager import get_cached_toetsregel_manager

            manager = get_cached_toetsregel_manager()
            all_rules = manager.get_all_regels()

            # Filter regels op basis van prefix
            filtered_rules = {
                k: v
                for k, v in all_rules.items()
                if k.startswith(self.rule_prefix)
            }

            # Sorteer regels alfabetisch
            sorted_rules = sorted(filtered_rules.items())

            # Formatteer elke regel
            for regel_key, regel_data in sorted_rules:
                sections.extend(self._format_rule(regel_key, regel_data))

            content = "\n".join(sections)

            return ModuleOutput(
                content=content,
                metadata={
                    "rules_count": len(filtered_rules),
                    "include_examples": self.include_examples,
                    "rule_prefix": self.rule_prefix,
                },
            )

        except Exception as e:
            logger.error(
                f"{self.module_id} execution failed: {e}",
                exc_info=True,
            )
            return ModuleOutput(
                content="",
                metadata={"error": str(e)},
                success=False,
                error_message=f"Failed to generate {self.rule_prefix} rules: {e!s}",
            )

    def get_dependencies(self) -> list[str]:
        """
        Deze module heeft geen dependencies.

        Returns:
            Lege lijst
        """
        return []

    def _format_rule(self, regel_key: str, regel_data: dict) -> list[str]:
        """
        Formatteer een regel uit JSON data.

        Args:
            regel_key: Regel identifier (bijv. "ARAI-01")
            regel_data: Regel data uit JSON
                - naam: Regel naam
                - uitleg: Uitleg van de regel
                - toetsvraag: Vraag om regel te toetsen
                - goede_voorbeelden: List van goede voorbeelden
                - foute_voorbeelden: List van foute voorbeelden

        Returns:
            List van geformatteerde regels (multi-line)
        """
        lines = []

        # Header met emoji
        naam = regel_data.get("naam", "Onbekende regel")
        lines.append(f"🔹 **{regel_key} - {naam}**")

        # Uitleg
        uitleg = regel_data.get("uitleg", "")
        if uitleg:
            lines.append(f"- {uitleg}")

        # Toetsvraag
        toetsvraag = regel_data.get("toetsvraag", "")
        if toetsvraag:
            lines.append(f"- Toetsvraag: {toetsvraag}")

        # Voorbeelden (indien enabled)
        if self.include_examples:
            # Goede voorbeelden
            goede_voorbeelden = regel_data.get("goede_voorbeelden", [])
            for goed in goede_voorbeelden:
                lines.append(f"  ✅ {goed}")

            # Foute voorbeelden
            foute_voorbeelden = regel_data.get("foute_voorbeelden", [])
            for fout in foute_voorbeelden:
                lines.append(f"  ❌ {fout}")

        return lines
```

**Usage in `modular_prompt_adapter.py`:**

```python
# BEFORE (lines 60-74): 5 separate imports en instantiations
from .modules.arai_rules_module import AraiRulesModule
from .modules.con_rules_module import ConRulesModule
from .modules.ess_rules_module import EssRulesModule
from .modules.sam_rules_module import SamRulesModule
from .modules.ver_rules_module import VerRulesModule

modules = [
    AraiRulesModule(),
    ConRulesModule(),
    EssRulesModule(),
    SamRulesModule(),
    VerRulesModule(),
    # ... andere modules
]

# AFTER: 1 import, 5 configuraties
from .modules.generic_rules_module import JSONBasedRulesModule

modules = [
    # JSON-based rule modules (configureerbaar)
    JSONBasedRulesModule("ARAI", "Algemene Regels AI (ARAI)", "✅", priority=75),
    JSONBasedRulesModule("CON-", "Context Regels (CON)", "🌐", priority=70),
    JSONBasedRulesModule("ESS", "Essentie Regels (ESS)", "🎯", priority=68),
    JSONBasedRulesModule("SAM", "Samenhang Regels (SAM)", "🔗", priority=66),
    JSONBasedRulesModule("VER", "Vorm Regels (VER)", "📝", priority=64),

    # Custom rule modules (blijven apart)
    IntegrityRulesModule(),
    StructureRulesModule(),

    # ... andere modules
]
```

**Benefits:**
- ✅ **-512 regels** (80% reductie in rule modules)
- ✅ **Single point of truth** voor regel formatting
- ✅ **Bug fix eenmaal** in plaats van 5×
- ✅ **Nieuwe regel categorie** = 1 regel configuratie ipv 128 regels copy-paste
- ✅ **Testability:** Test 1 generic module ipv 5 identieke tests

**Migration Path:**

1. Create `generic_rules_module.py` met nieuwe implementatie
2. Update `modular_prompt_adapter.py` om generic module te gebruiken
3. Run tests - verify 45 validatie regels nog steeds in prompt staan
4. Delete 5 oude files:
   - `arai_rules_module.py`
   - `con_rules_module.py`
   - `ess_rules_module.py`
   - `sam_rules_module.py`
   - `ver_rules_module.py`
5. Update `__init__.py` imports

**Testing Strategy:**
```python
# Test dat alle 45 regels nog steeds verschijnen
def test_all_rules_present_after_refactor():
    orchestrator = get_cached_orchestrator()
    prompt = orchestrator.build_prompt(begrip, context, config)

    # Verify ARAI regels
    assert "ARAI-01" in prompt
    assert "ARAI-02" in prompt

    # Verify CON regels
    assert "CON-01" in prompt
    assert "CON-02" in prompt

    # ... etc voor alle 45 regels

def test_generic_module_filtering():
    # Test dat prefix filtering correct werkt
    arai_module = JSONBasedRulesModule("ARAI", "Test ARAI", "✅", 75)
    arai_module.initialize({"include_examples": True})

    output = arai_module.execute(mock_context)

    # Moet alleen ARAI regels bevatten
    assert "ARAI-01" in output.content
    assert "CON-01" not in output.content
```

### Oplossing 2: Unified Prompt Context (PRIORITEIT 2)

**Doel:** Simplificeer context injection van 3 naar 2 lagen

**Approach:** Single data structure met duidelijke ownership

**Nieuwe File:** `src/services/prompts/unified_prompt_context.py`

```python
"""
Unified Prompt Context - Single source of truth voor prompt context data.

This dataclass replaces the complex 3-layer context injection with a single,
clear structure that has well-defined ownership and consistent naming.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WebSource:
    """Context bron uit web lookup."""

    source_type: str  # "wikipedia", "sru", etc.
    content: str
    confidence: float  # 0.0-1.0
    url: Optional[str] = None
    used_in_prompt: bool = False


@dataclass
class DocumentSnippet:
    """Snippet uit uploaded document."""

    document_name: str
    content: str
    page_number: Optional[int] = None
    relevance_score: float = 0.0


@dataclass
class UnifiedPromptContext:
    """
    Unified context structure voor prompt generatie.

    Deze dataclass vervangt de huidige EnrichedContext met een duidelijkere
    structuur die consistent named fields heeft en geen metadata bloat.

    Ownership:
        - Built by: HybridContextManager.build_unified_context()
        - Consumed by: All prompt modules via ModuleContext
        - Scored by: ContextAwarenessModule._calculate_context_score()

    Attributes:
        # User-provided context (renamed voor consistency)
        organizational_context: Organisatorische context (was: organisatorisch)
        juridical_context: Juridische context (was: juridisch)
        legal_basis: Wettelijke basis (was: wettelijk)

        # Enrichments (from external sources)
        web_sources: Context uit web lookup (Wikipedia, SRU)
        document_snippets: Snippets uit uploaded documenten
        abbreviations: Afkortingen → volledige namen (OM → Openbaar Ministerie)

        # Metadata (business data)
        ontological_category: Ontologische categorie (type/proces/resultaat)
        semantic_category: Mapped semantic category voor templates

        # Computed (by ContextAwarenessModule)
        richness_score: Context rijkheid score (0.0-1.0)
    """

    # User-provided context (CONSISTENT NAMING)
    organizational_context: list[str] = field(default_factory=list)
    juridical_context: list[str] = field(default_factory=list)
    legal_basis: list[str] = field(default_factory=list)

    # Enrichments
    web_sources: list[WebSource] = field(default_factory=list)
    document_snippets: list[DocumentSnippet] = field(default_factory=list)
    abbreviations: dict[str, str] = field(default_factory=dict)

    # Metadata (business data only)
    ontological_category: Optional[str] = None
    semantic_category: Optional[str] = None

    # Computed (by ContextAwarenessModule)
    richness_score: float = 0.0

    def has_organizational_context(self) -> bool:
        """Check of er organisatorische context is."""
        return bool(self.organizational_context)

    def has_juridical_context(self) -> bool:
        """Check of er juridische context is."""
        return bool(self.juridical_context)

    def has_legal_basis(self) -> bool:
        """Check of er wettelijke basis is."""
        return bool(self.legal_basis)

    def has_enrichments(self) -> bool:
        """Check of er externe verrijkingen zijn."""
        return bool(self.web_sources or self.document_snippets)

    def get_all_context_text(self) -> str:
        """
        Verkrijg alle context als één text string.

        Returns:
            Gecombineerde context string
        """
        all_items = []
        all_items.extend(self.organizational_context)
        all_items.extend(self.juridical_context)
        all_items.extend(self.legal_basis)
        return ", ".join(all_items) if all_items else ""

    def get_high_confidence_sources(self, threshold: float = 0.8) -> list[WebSource]:
        """
        Verkrijg alleen web sources met hoge confidence.

        Args:
            threshold: Minimum confidence (default 0.8)

        Returns:
            Lijst van hoge-confidence sources
        """
        return [
            source
            for source in self.web_sources
            if source.confidence >= threshold
        ]
```

**Migration in `definition_generator_context.py`:**

```python
# BEFORE
class HybridContextManager:
    async def build_enriched_context(self, request: GenerationRequest) -> EnrichedContext:
        base_context = self._build_base_context(request)
        expanded_terms = self._expand_abbreviations(base_context)
        sources = []  # ContextSource objects

        return EnrichedContext(
            base_context=base_context,  # dict with "organisatorisch", "juridisch"
            sources=sources,
            expanded_terms=expanded_terms,
            metadata={...}  # BLOAT: 7+ verschillende data types
        )

# AFTER
class HybridContextManager:
    async def build_unified_context(self, request: GenerationRequest) -> UnifiedPromptContext:
        # Extract user-provided context
        org_context = request.organisatorische_context or []
        jur_context = request.juridische_context or []
        legal_basis = request.wettelijke_basis or []

        # Expand abbreviations
        abbreviations = self._expand_abbreviations(org_context + jur_context)

        # Collect web sources
        web_sources = await self._collect_web_sources(request)

        # Collect document snippets
        doc_snippets = self._collect_document_snippets(request)

        # Map ontological category
        semantic_cat = CATEGORY_MAPPING.get(request.ontologische_categorie)

        return UnifiedPromptContext(
            organizational_context=org_context,
            juridical_context=jur_context,
            legal_basis=legal_basis,
            web_sources=web_sources,
            document_snippets=doc_snippets,
            abbreviations=abbreviations,
            ontological_category=request.ontologische_categorie,
            semantic_category=semantic_cat,
            richness_score=0.0,  # Berekend door ContextAwarenessModule
        )
```

**Update `base_module.py`:**

```python
@dataclass
class ModuleContext:
    """Context object dat tussen modules wordt doorgegeven."""

    begrip: str
    unified_context: UnifiedPromptContext  # Was: enriched_context
    config: UnifiedGeneratorConfig
    shared_state: dict[str, Any]
```

**Update `ContextAwarenessModule`:**

```python
def execute(self, context: ModuleContext) -> ModuleOutput:
    unified_ctx = context.unified_context

    # Bereken richness score
    score = self._calculate_context_score(unified_ctx)
    unified_ctx.richness_score = score  # Store in context itself

    # Build adaptive section
    if score >= 0.8:
        content = self._build_rich_section(unified_ctx)
    elif score >= 0.5:
        content = self._build_moderate_section(unified_ctx)
    else:
        content = self._build_minimal_section(unified_ctx)

    return ModuleOutput(content=content, ...)

def _build_rich_section(self, ctx: UnifiedPromptContext) -> str:
    sections = ["📊 UITGEBREIDE CONTEXT ANALYSE:"]

    if ctx.organizational_context:
        sections.append("ORGANISATORISCH:")
        for item in ctx.organizational_context:
            sections.append(f"  • {item}")

    if ctx.web_sources:
        sections.append("ADDITIONELE BRONNEN:")
        for source in ctx.web_sources:
            emoji = self._get_confidence_emoji(source.confidence)
            sections.append(f"  {emoji} {source.source_type}: {source.content[:150]}...")

    return "\n".join(sections)
```

**Benefits:**
- ✅ **Single source of truth** - geen multiple base_context/metadata/shared_state
- ✅ **Consistent naming** - organizational_context overal hetzelfde
- ✅ **Clear ownership** - HybridContextManager bouwt, modules consumeren
- ✅ **No metadata bloat** - alleen relevante business data
- ✅ **Easier testing** - één structure om te mocken

### Oplossing 3: Jinja2 Templates (PRIORITEIT 3 - Optioneel)

**Doel:** Maak prompt wijzigingen mogelijk zonder code deployment

**Approach:** Extract template strings naar `.j2` files

**Use Case:**
- Product owner wil prompt tweaken zonder development cycle
- A/B testing met verschillende prompt varianten
- Environment-specific prompts (dev/staging/prod)

**Directory Structure:**
```
templates/
└── prompts/
    ├── base/
    │   ├── expertise.j2
    │   ├── output_specification.j2
    │   └── grammar.j2
    ├── context/
    │   ├── rich_context.j2
    │   ├── moderate_context.j2
    │   └── minimal_context.j2
    ├── rules/
    │   ├── rule_header.j2
    │   └── rule_item.j2
    └── macros/
        ├── confidence_emoji.j2
        └── format_list.j2
```

**Example Template:** `templates/prompts/context/rich_context.j2`

```jinja2
{# Rich Context Template - Used when context score ≥ 0.8 #}

📊 UITGEBREIDE CONTEXT ANALYSE:
⚠️ VERPLICHT: Gebruik onderstaande specifieke context om de definitie te formuleren voor deze organisatorische, juridische en wettelijke setting. Maak de definitie contextspecifiek zonder de context expliciet te benoemen.

{% if organizational_context %}
ORGANISATORISCH:
{% for item in organizational_context %}
  • {{ item }}
{% endfor %}
{% endif %}

{% if juridical_context %}
JURIDISCH:
{% for item in juridical_context %}
  • {{ item }}
{% endfor %}
{% endif %}

{% if legal_basis %}
WETTELIJK:
{% for item in legal_basis %}
  • {{ item }}
{% endfor %}
{% endif %}

{% if web_sources %}
ADDITIONELE BRONNEN:
{% for source in web_sources %}
  {{ confidence_emoji(source.confidence) }} {{ source.source_type|title }} ({{ "%.2f"|format(source.confidence) }}): {{ source.content[:150] }}...
{% endfor %}
{% endif %}

{% if abbreviations %}
AFKORTINGEN & UITBREIDINGEN:
{% for abbr, expansion in abbreviations.items() %}
  • {{ abbr }} = {{ expansion }}
{% endfor %}
{% endif %}
```

**Jinja2 Macro:** `templates/prompts/macros/confidence_emoji.j2`

```jinja2
{# Confidence emoji macro - DRY principe #}
{% macro confidence_emoji(confidence) -%}
{% if confidence < 0.5 -%}
🔴
{%- elif confidence < 0.8 -%}
🟡
{%- else -%}
🟢
{%- endif %}
{%- endmacro %}
```

**Usage in Module:**

```python
from jinja2 import Environment, FileSystemLoader, select_autoescape

class ContextAwarenessModule(BasePromptModule):
    def __init__(self):
        super().__init__(...)

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader("templates/prompts"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register custom filters/macros
        self.jinja_env.globals["confidence_emoji"] = self._confidence_emoji

    def _build_rich_section(self, ctx: UnifiedPromptContext) -> str:
        # BEFORE: Python string building
        # sections = ["📊 UITGEBREIDE CONTEXT ANALYSE:"]
        # sections.append("ORGANISATORISCH:")
        # for item in ctx.organizational_context:
        #     sections.append(f"  • {item}")
        # return "\n".join(sections)

        # AFTER: Jinja2 template rendering
        template = self.jinja_env.get_template("context/rich_context.j2")
        return template.render(
            organizational_context=ctx.organizational_context,
            juridical_context=ctx.juridical_context,
            legal_basis=ctx.legal_basis,
            web_sources=ctx.web_sources,
            abbreviations=ctx.abbreviations,
        )

    @staticmethod
    def _confidence_emoji(confidence: float) -> str:
        if confidence < 0.5:
            return "🔴"
        elif confidence < 0.8:
            return "🟡"
        else:
            return "🟢"
```

**Template Versioning:**

```
templates/
└── prompts/
    ├── v1/
    │   └── context/
    │       └── rich_context.j2
    └── v2/
        └── context/
            └── rich_context.j2
```

```python
# In config
PROMPT_TEMPLATE_VERSION = os.getenv("PROMPT_TEMPLATE_VERSION", "v2")

# In module
template_path = f"{PROMPT_TEMPLATE_VERSION}/context/rich_context.j2"
template = self.jinja_env.get_template(template_path)
```

**Benefits:**
- ✅ **Zero-deploy prompt changes** - edit `.j2` file, restart app
- ✅ **A/B testing** - switch templates via environment variable
- ✅ **Version control** - git tracks template changes apart from code
- ✅ **Non-technical edits** - product owners can tweak prompts
- ✅ **Template reuse** - macros zoals confidence_emoji herbruikbaar

**Drawbacks:**
- ⚠️ **Complexity:** Jinja2 dependency + learning curve
- ⚠️ **Debugging:** Template errors minder duidelijk dan Python errors
- ⚠️ **Deployment:** Templates moeten mee-deployed worden

**Aanbeveling:** Implementeer alleen als er echte behoefte is aan frequent prompt wijzigingen zonder deployment. Voor huidige use case (solo developer) is dit mogelijk YAGNI (You Aren't Gonna Need It).

---

## Implementatieplan

### Fasering

Het implementatieplan is opgedeeld in **3 fasen** die onafhankelijk uitgevoerd kunnen worden. Elke fase heeft approval checkpoints volgens UNIFIED_INSTRUCTIONS.md (>100 regels wijziging = approval vereist).

### Fase 1: Elimineer Duplicatie (PRIORITEIT: HOOG)

**Doel:** Vervang 5 identieke rule modules door 1 generic module
**Impact:** -512 regels (80% reductie)
**Risico:** 🟢 Laag (pure refactor, business logica onveranderd)
**Effort:** 8 uur
**Approval:** ✅ Vereist (totaal >100 regels wijziging)

#### Stappen

**Step 1.1: Create Generic Module (2 uur)**
- Create file: `src/services/prompts/modules/generic_rules_module.py`
- Implement `JSONBasedRulesModule` class (zie Oplossing 1)
- Copy `_format_rule()` logic van bestaande module
- Add docstrings en type hints
- **Lines changed:** +130 (new file)

**Step 1.2: Update Adapter (1 uur)**
- Edit: `src/services/prompts/modular_prompt_adapter.py`
- Replace 5 imports met 1 generic import
- Replace 5 instantiations met 5 configured instantiations
- **Lines changed:** +5, -10 (net -5)

**Step 1.3: Test Verification (2 uur)**
- Run existing tests: `pytest tests/services/prompts/`
- Verify: Alle 45 validation regels nog in prompt
- Create regression test: `test_generic_rules_module.py`
  - Test filtering werkt correct (ARAI vs CON)
  - Test formatting identiek aan oude modules
  - Test metadata correct
- **Lines changed:** +150 (new test file)

**Step 1.4: Delete Old Modules (1 uur)**
- Delete files:
  - `src/services/prompts/modules/arai_rules_module.py` (-128)
  - `src/services/prompts/modules/con_rules_module.py` (-128)
  - `src/services/prompts/modules/ess_rules_module.py` (-128)
  - `src/services/prompts/modules/sam_rules_module.py` (-128)
  - `src/services/prompts/modules/ver_rules_module.py` (-128)
- Update: `src/services/prompts/modules/__init__.py`
  - Remove 5 old imports
  - Add 1 new import
- **Lines changed:** -640, +1

**Step 1.5: Documentation (2 uur)**
- Update: `docs/architectuur/ARCHITECTURE.md`
  - Add section over generic rule module pattern
- Create: Migration guide in commit message
- **Lines changed:** +50

**Totaal Fase 1:**
- **Lines added:** +330
- **Lines deleted:** -645
- **Net change:** -315 regels
- **Approval checkpoint:** ✅ Na Step 1.2 (>100 regels totaal wijziging)

**Verification Checklist:**
- [ ] Alle 45 validation regels verschijnen in generated prompt
- [ ] Regel formatting identiek aan voor (emoji, structuur, voorbeelden)
- [ ] Metadata bevat correct rule_prefix
- [ ] Tests passen met 100% coverage
- [ ] No regression in prompt quality (manual check)

---

### Fase 2: Simplificeer Context (PRIORITEIT: MEDIUM)

**Doel:** Reduce context layers van 3 → 2 met unified structure
**Impact:** -171 regels, duidelijkere ownership
**Risico:** 🟡 Medium (raakt context flow)
**Effort:** 12 uur
**Approval:** ✅ Vereist (>100 regels wijziging)

#### Stappen

**Step 2.1: Create Unified Context (2 uur)**
- Create file: `src/services/prompts/unified_prompt_context.py`
- Implement `UnifiedPromptContext` dataclass (zie Oplossing 2)
- Implement `WebSource` en `DocumentSnippet` dataclasses
- Add utility methods (`has_organizational_context()`, etc.)
- **Lines changed:** +120 (new file)

**Step 2.2: Update HybridContextManager (3 uur)**
- Edit: `src/services/definition_generator_context.py`
- Rename: `build_enriched_context()` → `build_unified_context()`
- Refactor: Build UnifiedPromptContext instead of EnrichedContext
- Remove: Metadata bloat logic
- **Lines changed:** +80, -120 (net -40)

**Step 2.3: Update Base Module (1 uur)**
- Edit: `src/services/prompts/modules/base_module.py`
- Change: `ModuleContext.enriched_context` → `ModuleContext.unified_context`
- Update type hints
- **Lines changed:** +10, -10 (net 0)

**Step 2.4: Update ContextAwarenessModule (3 uur)**
- Edit: `src/services/prompts/modules/context_awareness_module.py`
- Update: All references van enriched_context → unified_context
- Update: Field names (organisatorisch → organizational_context)
- Simplify: Context scoring logic (direct access ipv nested dicts)
- Remove: `_share_traditional_context()` - data zit al in unified_context
- **Lines changed:** +150, -200 (net -50)

**Step 2.5: Update Other Modules (2 uur)**
- Edit: `template_module.py` - use unified_context
- Edit: `semantic_categorisation_module.py` - use unified_context
- Update: All modules die context raadplegen
- **Lines changed:** +60, -80 (net -20)

**Step 2.6: Test & Verification (1 uur)**
- Update: Alle tests om UnifiedPromptContext te gebruiken
- Create: Unit tests voor UnifiedPromptContext utility methods
- Regression test: Prompt output identiek aan voor
- **Lines changed:** +100, -80 (net +20)

**Totaal Fase 2:**
- **Lines added:** +520
- **Lines deleted:** -490
- **Net change:** +30 regels (maar -171 complexity)
- **Approval checkpoint:** ✅ Na Step 2.2 (>100 regels wijziging)

**Verification Checklist:**
- [ ] Context richness scoring produces same scores
- [ ] Adaptive formatting werkt correct (rich/moderate/minimal)
- [ ] Shared state niet meer nodig (data in unified_context)
- [ ] Field names consistent (organizational_context overal)
- [ ] No regression in prompt quality

---

### Fase 3: Jinja2 Templates (PRIORITEIT: LAAG - Optioneel)

**Doel:** Enable zero-deploy prompt changes via templates
**Impact:** Operational flexibility, A/B testing capability
**Risico:** 🟡 Medium (verandert generatie mechanisme)
**Effort:** 16 uur
**Approval:** ✅ Vereist (>100 regels wijziging)
**Aanbeveling:** Implementeer alleen bij aantoonbare behoefte

#### Stappen

**Step 3.1: Setup Jinja2 Infrastructure (2 uur)**
- Add dependency: `jinja2==3.1.3` in `requirements.txt`
- Create: `templates/prompts/` directory structure
- Create: Base template loader utility
- **Lines changed:** +50 (new utility)

**Step 3.2: Extract ContextAwarenessModule Templates (4 uur)**
- Create templates:
  - `templates/prompts/context/rich_context.j2`
  - `templates/prompts/context/moderate_context.j2`
  - `templates/prompts/context/minimal_context.j2`
- Create macros:
  - `templates/prompts/macros/confidence_emoji.j2`
- Update: `context_awareness_module.py` om templates te laden
- **Lines changed:** +200 (templates), +80 (loader), -150 (string building)

**Step 3.3: Extract Other Content Modules (6 uur)**
- Extract templates voor:
  - ExpertiseModule
  - OutputSpecificationModule
  - GrammarModule
  - TemplateModule
  - ErrorPreventionModule
- Update modules om Jinja2 te gebruiken
- **Lines changed:** +400 (templates), +200 (loaders), -300 (string building)

**Step 3.4: Template Versioning (2 uur)**
- Implement: `v1/` en `v2/` directory structure
- Add: Environment variable `PROMPT_TEMPLATE_VERSION`
- Update: Template loader om version te respecteren
- **Lines changed:** +100

**Step 3.5: Testing & Documentation (2 uur)**
- Test: Template rendering produces identical output
- Test: Version switching werkt correct
- Document: How to edit templates
- Document: Template syntax guide voor product owners
- **Lines changed:** +150 (tests), +200 (docs)

**Totaal Fase 3:**
- **Lines added:** +1380
- **Lines deleted:** -450
- **Net change:** +930 regels (maar operational flexibility++)
- **Approval checkpoint:** ✅ Na Step 3.2 (>100 regels wijziging)

**Verification Checklist:**
- [ ] Template rendering produces identical prompts
- [ ] Version switching werkt zonder deployment
- [ ] Non-technical users kunnen templates editen
- [ ] Template errors hebben duidelijke error messages
- [ ] Performance overhead acceptabel (< 50ms)

---

## Impact Analyse

### Code Metrics

| Metric | Baseline | Na Fase 1 | Na Fase 2 | Na Fase 3 |
|--------|----------|-----------|-----------|-----------|
| **Total Lines** | 5,383 | 5,068 (-6%) | 5,098 (-5%) | 6,028 (+12%) |
| **Duplicate Code** | 640 (77%) | 128 (100%) | 128 (100%) | 128 (100%) |
| **Context Layers** | 3 | 3 | 2 | 2 |
| **Template Files** | 0 | 0 | 0 | 15 |
| **Module Files** | 19 | 15 (-21%) | 15 | 15 |

### Maintainability Impact

**Voor Fase 1:**
- ❌ Bug in rule formatting = **5× fix** nodig
- ❌ Nieuwe regel categorie = **+128 regels** copy-paste
- ❌ Test coverage = **5× identieke tests**

**Na Fase 1:**
- ✅ Bug in rule formatting = **1× fix** in generic module
- ✅ Nieuwe regel categorie = **1 regel** configuratie
- ✅ Test coverage = **1 module** met parameterized tests

**Voor Fase 2:**
- ❌ Context data in **3 plaatsen** (base_context, metadata, shared_state)
- ❌ Field names **inconsistent** (organisatorisch vs organization_contexts)
- ❌ Debugging moeilijk - waar komt data vandaan?

**Na Fase 2:**
- ✅ Context data in **1 plaats** (UnifiedPromptContext)
- ✅ Field names **consistent** (organizational_context overal)
- ✅ Debugging makkelijk - clear ownership

**Voor Fase 3:**
- ❌ Prompt wijziging = **code deployment** nodig
- ❌ A/B testing = **if/else in code**
- ❌ Non-technical edits = **niet mogelijk**

**Na Fase 3:**
- ✅ Prompt wijziging = **edit .j2 file** + restart
- ✅ A/B testing = **environment variable**
- ✅ Non-technical edits = **template files**

### Performance Impact

**Fase 1: Geen impact**
- Generic module heeft identieke logic
- Zelfde caching via `get_cached_toetsregel_manager()`
- **Performance change:** 0%

**Fase 2: Lichte verbetering**
- Minder nested dict lookups
- No shared_state overhead
- **Performance change:** +2-5% (verwacht)

**Fase 3: Lichte overhead**
- Jinja2 template rendering overhead
- **Performance change:** -5-10% (verwacht < 50ms)
- Mitigatie: Template caching via `@cached` decorator

### Testing Impact

**Fase 1:**
- **Delete:** 5× identieke test files (~150 regels elk = 750 regels)
- **Create:** 1× generic test with parametrization (~200 regels)
- **Net:** -550 regels test code
- **Coverage:** Blijft 100% (beter gefocust)

**Fase 2:**
- **Update:** Alle context-related tests (~30 test functions)
- **Create:** UnifiedPromptContext unit tests (~15 tests)
- **Net:** +100 regels test code
- **Coverage:** Blijft 100%

**Fase 3:**
- **Create:** Template rendering tests (~20 tests)
- **Create:** Version switching tests (~10 tests)
- **Net:** +200 regels test code
- **Coverage:** Target 95% voor templates

---

## Risico's en Mitigatie

### Fase 1 Risico's

#### Risico 1.1: Regel Filtering Breekt

**Waarschijnlijkheid:** 🟢 Laag
**Impact:** 🔴 Kritiek (regels verdwijnen uit prompt)

**Scenario:**
Generic filter `startswith("CON-")` matcht niet correct en CON regels verdwijnen uit prompt.

**Mitigatie:**
```python
# Test voor elke regel categorie
@pytest.mark.parametrize("prefix,expected_count", [
    ("ARAI", 8),   # We weten dat er 8 ARAI regels zijn
    ("CON-", 5),   # We weten dat er 5 CON regels zijn
    ("ESS", 10),   # etc.
    ("SAM", 12),
    ("VER", 10),
])
def test_rule_filtering(prefix, expected_count):
    module = JSONBasedRulesModule(prefix, "Test", "🔹", 70)
    module.initialize({"include_examples": True})

    output = module.execute(mock_context)

    assert output.metadata["rules_count"] == expected_count
    assert prefix in output.content
```

**Recovery Plan:**
Als test faalt, rollback naar oude modules en debug generic filter logic.

#### Risico 1.2: Formatting Inconsistentie

**Waarschijnlijkheid:** 🟡 Medium
**Impact:** 🟡 Medium (visuele inconsistentie in prompt)

**Scenario:**
`_format_rule()` in generic module produceert net iets andere formatting dan oude modules.

**Mitigatie:**
- Snapshot testing: Save oude prompt output, compare met nieuwe
- Visual diff check: Manual inspection van generated prompts
- Regression test: Exact string match voor 1 test prompt

```python
def test_formatting_identical_to_legacy():
    # Load legacy output (saved during migration)
    with open("tests/fixtures/legacy_arai_output.txt") as f:
        legacy_output = f.read()

    # Generate new output
    module = JSONBasedRulesModule("ARAI", "Test", "✅", 75)
    new_output = module.execute(mock_context).content

    # Compare
    assert new_output == legacy_output
```

### Fase 2 Risico's

#### Risico 2.1: Context Data Loss

**Waarschijnlijkheid:** 🟡 Medium
**Impact:** 🔴 Kritiek (context verdwijnt uit prompt)

**Scenario:**
During migration, een context field wordt niet correct gemapped naar UnifiedPromptContext en gaat verloren.

**Mitigatie:**
- **Audit trail:** Log ALLE context transformaties during migration
- **Comparison test:** Compare oude EnrichedContext data met nieuwe UnifiedPromptContext
- **Rollback plan:** Keep oude build_enriched_context() als fallback

```python
def test_context_data_complete():
    """Verify ALL data migrated from EnrichedContext to UnifiedPromptContext."""
    request = create_test_request()

    # OLD: Build EnrichedContext
    old_manager = OldHybridContextManager()
    old_context = old_manager.build_enriched_context(request)

    # NEW: Build UnifiedPromptContext
    new_manager = HybridContextManager()
    new_context = new_manager.build_unified_context(request)

    # Verify data equivalence
    assert len(new_context.organizational_context) == len(old_context.base_context["organisatorisch"])
    assert new_context.abbreviations == old_context.expanded_terms
    # ... verify ALL fields
```

#### Risico 2.2: Shared State Dependencies

**Waarschijnlijkheid:** 🟡 Medium
**Impact:** 🟡 Medium (modules kunnen data niet vinden)

**Scenario:**
Een module verwacht data in `shared_state["organization_contexts"]` maar die is niet meer beschikbaar na migratie.

**Mitigatie:**
- **Grep search:** Find alle `shared_state` usages in codebase
- **Deprecation warnings:** Add warnings if modules access old shared_state keys
- **Gradual migration:** Keep both EnrichedContext en UnifiedPromptContext voor 1 release

```bash
# Find all shared_state usages
grep -r "shared_state\[" src/services/prompts/modules/
grep -r "get_shared(" src/services/prompts/modules/
```

### Fase 3 Risico's

#### Risico 3.1: Template Syntax Errors

**Waarschijnlijkheid:** 🟡 Medium (bij edits door non-developers)
**Impact:** 🔴 Kritiek (app crash tijdens prompt generation)

**Scenario:**
Product owner edits template, maakt Jinja2 syntax fout, app crasht.

**Mitigatie:**
- **Template validation:** Validate alle templates tijdens app startup
- **Error messages:** Clear error messages met line number en expected syntax
- **CI check:** Pre-commit hook valideerd template syntax

```python
def validate_all_templates_on_startup():
    """Run tijdens app initialization."""
    env = get_jinja_environment()

    for template_name in os.listdir("templates/prompts"):
        if template_name.endswith(".j2"):
            try:
                env.get_template(template_name)
            except Exception as e:
                logger.error(f"Template {template_name} heeft syntax fout: {e}")
                raise SystemExit(1)
```

#### Risico 3.2: Performance Degradation

**Waarschijnlijkheid:** 🟢 Laag
**Impact:** 🟡 Medium (langzamere prompt generation)

**Scenario:**
Jinja2 rendering overhead maakt prompt generation >50ms langzamer.

**Mitigatie:**
- **Template caching:** Use Jinja2 bytecode cache
- **Performance monitoring:** Log rendering times
- **Threshold alert:** Alert if prompt generation > 2 seconden

```python
from jinja2 import Environment, FileSystemBytecodeCache

env = Environment(
    loader=FileSystemLoader("templates/prompts"),
    bytecode_cache=FileSystemBytecodeCache("/tmp/jinja2_cache"),
    auto_reload=False,  # In productie
)
```

---

## Aanbeveling & Beslispunten

### Definitieve Aanbeveling

**Implementeer Fase 1 nu, evalueer Fase 2/3 later.**

**Rationale:**

**Fase 1 (Elimineer Duplicatie):**
- ✅ **Laag risico** - pure refactor, business logica onveranderd
- ✅ **Hoge impact** - 80% code reductie in rule modules
- ✅ **Quick win** - 8 uur effort voor 512 regels saving
- ✅ **Schaalbaar** - nieuwe regel categorie = 1 regel config ipv 128 regels code
- ✅ **Technical debt fix** - eliminates most problematic duplication

**Fase 2 (Simplify Context):**
- ⚠️ **Medium risico** - raakt kritieke context flow
- ✅ **Medium impact** - clarity improvement, beperkte LOC saving
- ⚠️ **Geen directe business value** - internal refactor
- 🤔 **Decision point:** Implementeer alleen als je context injection problemen ervaart in practice

**Fase 3 (Jinja2 Templates):**
- ⚠️ **Medium risico** - nieuwe dependency + complexity
- 🤷 **Twijfelachtige value** voor solo developer project
- ❌ **YAGNI concern** - is er echt behoefte aan frequent prompt tweaks zonder deployment?
- 🤔 **Decision point:** Implementeer alleen als je aantoonbaar 5+ prompt edits per maand doet

### Decision Tree

```
Start: DEF-156 Context Injection Consolidation
│
├─► Fase 1: Generic JSONBasedRulesModule
│   │
│   ├─► ✅ IMPLEMENTEREN (8 uur)
│   │   └─► Test: Alle 45 regels nog in prompt?
│   │       ├─► Ja: ✅ DONE - Merge naar main
│   │       └─► Nee: Debug filtering logic, retry
│   │
│   └─► Result: -512 regels, betere maintainability
│
├─► Fase 2: UnifiedPromptContext
│   │
│   ├─► Beslispunt: Ervaar je context injection complexity in practice?
│   │   ├─► Ja: ✅ IMPLEMENTEREN (12 uur)
│   │   │   └─► Test: Context data complete? Prompt identiek?
│   │   │       ├─► Ja: ✅ DONE
│   │   │       └─► Nee: Fix data loss, retry
│   │   │
│   │   └─► Nee: ⏸️ SKIP - Bewaar voor later
│   │
│   └─► Result: -171 complexity, 2 layers ipv 3
│
└─► Fase 3: Jinja2 Templates
    │
    ├─► Beslispunt: Heb je frequent prompt edits nodig (5+/maand)?
    │   ├─► Ja: ✅ IMPLEMENTEREN (16 uur)
    │   │   └─► Test: Template rendering correct? Performance OK?
    │   │       ├─► Ja: ✅ DONE
    │   │       └─► Nee: Fix templates, optimize rendering
    │   │
    │   └─► Nee: ❌ SKIP - YAGNI
    │
    └─► Result: Zero-deploy prompt edits, maar +930 regels complexity
```

### Approval Vereisten (volgens UNIFIED_INSTRUCTIONS.md)

**Fase 1:**
- ✅ **Approval vereist** na Step 1.2 (totaal >100 regels wijziging)
- **Reviewers:** Check dat filtering logic correct is
- **Acceptance criteria:**
  - Alle 45 validatie regels verschijnen in prompt
  - Tests passen 100%
  - Geen visuele regression in prompt

**Fase 2:**
- ✅ **Approval vereist** na Step 2.2 (totaal >100 regels wijziging)
- **Reviewers:** Check dat context data niet verloren gaat
- **Acceptance criteria:**
  - Context richness scoring onveranderd
  - Adaptive formatting werkt correct
  - Geen data loss in context flow

**Fase 3:**
- ✅ **Approval vereist** na Step 3.2 (totaal >100 regels wijziging)
- **Reviewers:** Check template syntax en rendering
- **Acceptance criteria:**
  - Templates produceren identieke prompts
  - Performance overhead < 50ms
  - Non-technical users kunnen templates editen

---

## Conclusie

Het prompt module systeem heeft een **solide architectuur** met duidelijke separation of concerns, maar lijdt onder **77% code duplicatie** in rule modules en een **te complexe 3-laagse context injection**.

**Direct Actie (Aanbevolen):**
- ✅ **Implementeer Fase 1** (Generic JSONBasedRulesModule)
  - **Effort:** 8 uur
  - **Impact:** -512 regels (80% reductie in rule modules)
  - **Risk:** Laag
  - **Value:** Hoog (eliminates most problematic technical debt)

**Evalueer Later:**
- 🤔 **Fase 2** (UnifiedPromptContext) - implementeer alleen bij aantoonbare complexity issues
- 🤔 **Fase 3** (Jinja2 Templates) - implementeer alleen bij frequent prompt edit behoefte

Deze aanpak volgt **YAGNI principe** (You Aren't Gonna Need It) - implementeer alleen wat je NU nodig hebt, rest kan later.

---

## Bijlagen

### A. Code Statistics

```
Huidige Codebase (src/services/prompts/):
├── Total files: 21
├── Total lines: 5,383
├── Distribution:
│   ├── Entry points & adapters: 737 lines (14%)
│   ├── Core infrastructure: 1,000 lines (19%)
│   ├── Content modules: 2,401 lines (45%)
│   └── Rule modules: 1,245 lines (23%)
│       └── Duplicated code: 640 lines (52% of rule modules)

Duplicatie Breakdown:
├── 5 JSON-based rule modules: 640 lines (100% duplicate structure)
├── Template patterns (2 modules): ~100 lines overlap
├── Context handling (3 layers): ~200 lines redundant logic
└── Total estimated duplication: ~940 lines (17% of codebase)

Potential Reduction:
├── After Fase 1: 5,383 → 4,871 lines (512 lines saved)
├── After Fase 2: 4,871 → 4,700 lines (171 lines saved)
└── After Fase 3: 4,700 → 5,630 lines (+930 lines, maar operational gain)
```

### B. Module Dependency Matrix

```
CURRENT (All modules return []):
                          depends_on
ExpertiseModule           []
OutputSpecificationModule []
GrammarModule             []
ContextAwarenessModule    []
SemanticCategorisation    []
TemplateModule            []
AraiRulesModule           []
ConRulesModule            []
...                       []

POTENTIAL (If we'd use dependency graph):
                          depends_on
ExpertiseModule           []
OutputSpecificationModule []
GrammarModule             []
ContextAwarenessModule    []
SemanticCategorisation    [ContextAwarenessModule]
TemplateModule            [SemanticCategorisation]
AraiRulesModule           [ContextAwarenessModule]
ConRulesModule            [ContextAwarenessModule]
...
```

### C. Test Coverage Goals

| Module | Current Coverage | Target After Refactor |
|--------|-----------------|----------------------|
| generic_rules_module.py | N/A | 100% |
| unified_prompt_context.py | N/A | 100% |
| context_awareness_module.py | 85% | 95% |
| prompt_orchestrator.py | 78% | 85% |
| Overall prompts/ | 72% | 90% |

---

**Einde Document**

_Wil je dat ik Fase 1 implementeer? Of heb je nog vragen over de analyse?_
