# Strategic Analysis: Pre-Processing Pattern voor Ontologische Classificatie

**Document Status:** Strategic Architecture Analysis
**Date:** 2025-10-07
**Version:** 1.0
**Author:** Claude Code (Analysis Agent)

---

## Executive Summary

**REQUIREMENT:**
> "Classificatie moet LOS van definitie generatie, want categorie bepaalt promptopbouw"

**STRATEGIC DECISION NEEDED:**
Waar in de pipeline hoort ontologische classificatie THUIS - als pre-processing stap, als service layer concern, of als dedicated classifier service?

**CURRENT STATE ASSESSMENT:**
- ✅ **OntologyClassifierService** bestaat (`src/services/classification/ontology_classifier.py`)
- ✅ **LLM-based classificatie** met rules-based validatie
- ✅ **Prompt module integratie** (`SemanticCategorisationModule`) gebruikt categorie voor template selection
- ⚠️ **Pipeline integration**: Classificatie is NIET expliciet pre-processing in current flow
- ⚠️ **UI integration**: Geen evidence van aparte classificatie stap in UI

**RECOMMENDED PATTERN:** **Pipeline Pattern met Pre-Processing Layer** (Optie B)

---

## 1. PATTERN IDENTIFICATION

### 1.1 Current Architecture Analysis

```
HUIDIGE FLOW (Implicit classification):
─────────────────────────────────────────
UI Input (begrip + context)
    ↓
DefinitionOrchestratorV2.create_definition()
    ├─ Phase 1: Security sanitization
    ├─ Phase 2: Feedback integration
    ├─ Phase 2.5: Web lookup
    ├─ Phase 3: Prompt generation ← HIER wordt ontologische_categorie GEBRUIKT
    │   └─ SemanticCategorisationModule.execute()
    │       └─ context.get_metadata("ontologische_categorie") ← Van request object
    ├─ Phase 4: AI generation
    └─ ...

ISSUE: ontologische_categorie komt van GenerationRequest, maar WAAR wordt die gezet?
```

**Critical Finding:**
```python
# src/services/orchestrators/definition_orchestrator_v2.py:201
logger.info(
    f"Generation {generation_id}: Starting orchestration for '{request.begrip}' "
    f"with category '{request.ontologische_categorie}'"  # ← Gebruikt, maar WAAR gezet?
)
```

**Evidence of category influencing prompt:**
```python
# src/services/prompts/modules/semantic_categorisation_module.py:86-90
categorie = context.get_metadata("ontologische_categorie")
if categorie:
    context.set_shared("ontological_category", categorie)  # ← Shared state!

# Category-specific guidance (line 154-157):
category_guidance = self._get_category_specific_guidance(categorie.lower())
# Returns different prompt sections per category:
# - PROCES: "is een activiteit waarbij..."
# - TYPE: "is een soort..."
# - RESULTAAT: "is het resultaat van..."
```

**CONCLUSION:** Categorie MOET pre-processing zijn, want het **verandert prompt template structure**.

---

## 2. WAAR HOORT CLASSIFICATIE IN DE PIPELINE?

### Analyse van 3 Architectuur Opties

```
┌───────────────────────────────────────────────────────────────────────┐
│ OPTIE A: SERVICE LAYER (in generate_definition)                      │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  UI → ServiceAdapter.generate_definition()                            │
│         ├─ 1. Classify (internal)                                     │
│         ├─ 2. Build GenerationRequest (with category)                 │
│         └─ 3. Call orchestrator                                       │
│                                                                       │
│  ✅ PRO:                                                              │
│     - Alles in 1 API call (simpel voor UI)                           │
│     - Geen UI-side state management                                  │
│     - Transparant voor callers                                       │
│                                                                       │
│  ❌ CON:                                                              │
│     - Classificatie is NIET herbruikbaar buiten generatie            │
│     - Batch classificatie (100 begrippen) MOET via generatie         │
│     - Corpus analyse (scan wetgeving) ONMOGELIJK                     │
│     - Validatie van bestaande definities (check categorie) niet      │
│     - ServiceAdapter wordt GOD OBJECT                                │
│                                                                       │
│  🎯 USE CASE FIT:                                                     │
│     ✅ Scenario: Gebruiker genereert definitie (1 begrip)            │
│     ❌ Scenario: Batch classificatie (100 begrippen ZONDER generatie)│
│     ❌ Scenario: Validatie bestaande definities                      │
│     ❌ Scenario: Corpus analyse (verdeling categorieën)              │
│                                                                       │
│  📊 SCORE: 2/5 - Te gekoppeld, beperkt herbruikbaarheid             │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────┐
│ OPTIE B: PRE-PROCESSING LAYER (aparte method)                        │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  UI → ServiceAdapter.classify_begrip() → ClassificationResult        │
│  UI → ServiceAdapter.generate_definition(category=result)            │
│         ├─ 1. Build GenerationRequest (with category)                │
│         └─ 2. Call orchestrator                                      │
│                                                                       │
│  ✅ PRO:                                                              │
│     - Classificatie is HERBRUIKBAAR (batch, validatie, analyse)      │
│     - Duidelijke separation of concerns                              │
│     - UI heeft controle over pre-processing pipeline                 │
│     - Caching mogelijk (classify once, reuse)                        │
│     - Expliciete pipeline: classify → build request → generate       │
│                                                                       │
│  ❌ CON:                                                              │
│     - UI moet 2 calls doen (meer boilerplate)                        │
│     - State management in UI (store ClassificationResult)            │
│     - Fout-handling op 2 niveaus                                     │
│                                                                       │
│  🎯 USE CASE FIT:                                                     │
│     ✅ Scenario: Gebruiker genereert definitie (classify eerst)      │
│     ✅ Scenario: Batch classificatie (100 begrippen ZONDER generatie)│
│     ✅ Scenario: Validatie bestaande definities                      │
│     ✅ Scenario: Corpus analyse (verdeling categorieën)              │
│     ✅ Scenario: Preview classificatie VOOR generatie (feedback)     │
│                                                                       │
│  📊 SCORE: 5/5 - Maximale herbruikbaarheid, duidelijke pipeline      │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────┐
│ OPTIE C: DEDICATED CLASSIFIER SERVICE (DI)                           │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  UI → OntologyClassifier.classify() → ClassificationResult           │
│  UI → DefinitionService.generate(category=result)                    │
│                                                                       │
│  ✅ PRO:                                                              │
│     - Maximale ontkoppeling (classifier = standalone)                │
│     - Direct DI via ServiceContainer                                 │
│     - Perfecte testbaarheid (mock classifier)                        │
│     - Classificatie kan OVERAL gebruikt worden                       │
│                                                                       │
│  ❌ CON:                                                              │
│     - UI heeft MEER verantwoordelijkheid (2 services te managen)     │
│     - Fout-handling complexer (2 aparte services)                    │
│     - Meer code in UI layer (orchestratie logic)                     │
│     - ServiceAdapter wordt bypassed (inconsistentie)                 │
│                                                                       │
│  🎯 USE CASE FIT:                                                     │
│     ✅ Scenario: Gebruiker genereert definitie                       │
│     ✅ Scenario: Batch classificatie                                 │
│     ✅ Scenario: Validatie bestaande definities                      │
│     ✅ Scenario: Corpus analyse                                      │
│     ❌ Scenario: Simpele UI (te veel boilerplate voor basic use)     │
│                                                                       │
│  📊 SCORE: 4/5 - Beste ontkoppeling, maar meer UI complexity         │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 3. PROMPT DEPENDENCY ANALYSE

### 3.1 Hoe Gebruikt Orchestrator de Categorie?

**Evidence:** `SemanticCategorisationModule` (`src/services/prompts/modules/semantic_categorisation_module.py`)

```python
def _get_category_specific_guidance(self, categorie: str) -> str | None:
    """Returns category-specific prompt sections."""
    category_guidance_map = {
        "proces": """**PROCES CATEGORIE - Focus op HANDELING en VERLOOP:**
        Gebruik formuleringen zoals:
        - 'is een activiteit waarbij...'
        - 'is het proces waarin...'
        ⚠️ PROCES SPECIFIEKE RICHTLIJNEN:
        - Beschrijf WIE doet WAT en HOE het verloopt
        - Geef aan waar het proces BEGINT en EINDIGT""",

        "type": """**TYPE CATEGORIE - Focus op CLASSIFICATIE en KENMERKEN:**
        - 'is een soort...'
        - 'betreft een categorie van...'""",

        "resultaat": """**RESULTAAT CATEGORIE - Focus op OORSPRONG en GEVOLG:**
        - 'is het resultaat van...'
        - 'ontstaat door...'""",

        "exemplaar": """**EXEMPLAAR CATEGORIE - Focus op SPECIFICITEIT:**
        - 'is een specifiek exemplaar van...'
        - 'betreft een individueel geval van...'"""
    }
```

**CONCRETE IMPACT:**

| Categorie | Prompt Aanpassingen | Token Overhead | Semantic Guidance |
|-----------|--------------------|-----------------|--------------------|
| **PROCES** | + 8-10 regels specifieke instructies | ~120 tokens | WIE/WAT/HOE/BEGIN/EINDE |
| **TYPE** | + 6-8 regels | ~90 tokens | CLASSIFICATIE/KENMERKEN |
| **RESULTAAT** | + 7-9 regels | ~105 tokens | OORSPRONG/GEVOLG/CAUSALITEIT |
| **EXEMPLAAR** | + 6-8 regels | ~95 tokens | SPECIFICITEIT/INDIVIDUALITEIT |
| **Geen categorie** | Basis instructies only | 0 extra tokens | Generieke guidance |

**CONCLUSION:** Categorie heeft **SIGNIFICANT** invloed op:
1. **Prompt structure** (verschillende templates)
2. **Token budget** (+90-120 tokens per categorie)
3. **Semantic guidance** (WIE/WAT vs. OORSPRONG/GEVOLG)
4. **LLM behavior** (actief vs. classificerend taalgebruik)

**THEREFORE:** Classificatie MOET pre-processing zijn - het is **niet** alleen metadata!

---

## 4. HERBRUIKBAARHEID SCENARIO'S

### Scenario 1: Batch Classificatie (100 begrippen ZONDER generatie)

**Use Case:** Gebruiker uploadt Excel met 100 begrippen + definities, wil alleen categorieën zien.

```
OPTIE A (Service Layer):
❌ PROBLEEM: Moet 100x generate_definition() aanroepen
❌ GEVOLG: 100 AI calls voor definitie generatie (NIET NODIG)
❌ KOSTEN: ~$5-10 (onnodige AI costs)
❌ TIJD: ~5-10 minuten

OPTIE B (Pre-Processing Layer):
✅ OPLOSSING: batch_classify_begrippen() → List[ClassificationResult]
✅ AI CALLS: 100 classificaties (ALLEEN wat nodig is)
✅ KOSTEN: ~$0.50 (10x goedkoper)
✅ TIJD: ~30-60 seconden

OPTIE C (Dedicated Service):
✅ OPLOSSING: classifier.batch_classify(items)
✅ IDENTIEK AAN OPTIE B
```

**WINNER:** Optie B of C (10x goedkoper, 10x sneller)

---

### Scenario 2: Validatie van Bestaande Definities

**Use Case:** Check of 500 bestaande definities juiste categorie hebben.

```
OPTIE A (Service Layer):
❌ PROBLEEM: Classificatie is GEKOPPELD aan generatie
❌ GEVOLG: Kan alleen checken door NIEUWE definitie te genereren
❌ USE CASE: ONMOGELIJK

OPTIE B (Pre-Processing Layer):
✅ OPLOSSING:
    for definitie in database:
        result = classify_begrip(definitie.begrip, definitie.definitie)
        if result.level != definitie.ontologische_categorie:
            report_mismatch(definitie, result)

OPTIE C (Dedicated Service):
✅ IDENTIEK AAN OPTIE B
```

**WINNER:** Optie B of C (Optie A kan dit niet)

---

### Scenario 3: Corpus Analyse (Verdeling categorieën in wetgeving)

**Use Case:** Analyseer 1000 begrippen uit wetgeving, genereer statistieken over verdeling TYPE/PROCES/RESULTAAT.

```
OPTIE A (Service Layer):
❌ PROBLEEM: Moet 1000 definities genereren (NIET NODIG)
❌ GEVOLG: 1000 AI calls (1-2 uur processing)
❌ USE CASE: PRAKTISCH ONMOGELIJK

OPTIE B (Pre-Processing Layer):
✅ OPLOSSING:
    results = batch_classify_begrippen(corpus_items)
    stats = {
        "TYPE": sum(1 for r in results if r.level == "TYPE"),
        "PROCES": sum(1 for r in results if r.level == "PROCES"),
        ...
    }
✅ TIJD: 5-10 minuten voor 1000 items

OPTIE C (Dedicated Service):
✅ IDENTIEK AAN OPTIE B
```

**WINNER:** Optie B of C (Optie A is te traag)

---

### Scenario 4: Preview Classificatie VOOR Generatie

**Use Case:** Gebruiker ziet eerst classificatie resultaat, kan corrigeren VOOR definitie generatie.

```
OPTIE A (Service Layer):
❌ PROBLEEM: Classificatie gebeurt INSIDE generatie
❌ GEVOLG: Geen preview mogelijk (hidden black box)

OPTIE B (Pre-Processing Layer):
✅ FLOW:
    1. User: Input begrip + context
    2. App: Toon classificatie preview (category + confidence)
    3. User: Correct indien nodig (override)
    4. App: Generate definitie met correcte categorie
✅ UX: Transparantie + controle

OPTIE C (Dedicated Service):
✅ IDENTIEK AAN OPTIE B
```

**WINNER:** Optie B of C (betere UX)

---

## 5. BEST PRACTICE AANBEVELING

### 🏆 RECOMMENDED PATTERN: **Pipeline Pattern met Pre-Processing Layer (Optie B)**

```
┌─────────────────────────────────────────────────────────────────┐
│ AANBEVOLEN ARCHITECTUUR                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ UI LAYER (Streamlit)                                    │   │
│  │  - Begrip input                                         │   │
│  │  - Context input                                        │   │
│  │  - [STAP 1] Classify button                             │   │
│  │  - [STAP 2] Preview classificatie (edit mogelijk)       │   │
│  │  - [STAP 3] Generate button                             │   │
│  └────────────┬────────────────────────────────────────────┘   │
│               │                                                 │
│               ▼                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ SERVICE ADAPTER (Facade)                                │   │
│  │                                                         │   │
│  │  classify_begrip(begrip, definitie, context)            │   │
│  │    ├─ Validate input                                    │   │
│  │    ├─ Call OntologyClassifier                           │   │
│  │    └─ Return ClassificationResult                       │   │
│  │                                                         │   │
│  │  generate_definition(request: GenerationRequest)        │   │
│  │    ├─ Require: request.ontologische_categorie != None   │   │
│  │    ├─ Build prompt (uses category)                      │   │
│  │    └─ Call orchestrator                                 │   │
│  │                                                         │   │
│  │  classify_and_generate(begrip, context, auto=True)      │   │
│  │    ├─ Step 1: classify_begrip()                         │   │
│  │    ├─ Step 2: build request                             │   │
│  │    └─ Step 3: generate_definition()                     │   │
│  │                                                         │   │
│  └────────────┬────────────────────────────────────────────┘   │
│               │                                                 │
│               ▼                                                 │
│  ┌──────────────────┐        ┌─────────────────────────────┐   │
│  │ OntologyClassifier│        │ DefinitionOrchestratorV2    │   │
│  │ (DI via Container)│        │                             │   │
│  │  - classify()     │        │  - create_definition()      │   │
│  │  - batch_classify()│        │    (uses category in       │   │
│  │                   │        │     prompt building)        │   │
│  └──────────────────┘        └─────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.1 Implementation Details

#### **ServiceAdapter Methods:**

```python
class DefinitionServiceAdapter:
    """Facade voor definitie generatie met classificatie pre-processing."""

    def __init__(self, container: ServiceContainer):
        self.container = container
        self.classifier = container.ontology_classifier()
        self.orchestrator = container.definition_orchestrator_v2()

    # ==========================================
    # PRE-PROCESSING: Classificatie (standalone)
    # ==========================================

    def classify_begrip(
        self,
        begrip: str,
        definitie: str,
        context: Optional[str] = None,
        voorbeelden: Optional[List[str]] = None
    ) -> ClassificationResult:
        """
        Classificeer begrip ZONDER definitie te genereren.

        Use cases:
        - Preview classificatie voor gebruiker
        - Batch classificatie (corpus analyse)
        - Validatie bestaande definities

        Args:
            begrip: Te classificeren begrip
            definitie: Definitie van begrip (voor context)
            context: Optionele extra context
            voorbeelden: Optionele voorbeeldzinnen

        Returns:
            ClassificationResult met level, confidence, rationale
        """
        logger.info(f"Classificatie pre-processing voor: {begrip}")

        result = self.classifier.classify(
            begrip=begrip,
            definitie=definitie,
            context=context,
            voorbeelden=voorbeelden
        )

        logger.info(f"Classificatie resultaat: {result.level} (confidence: {result.confidence:.0%})")
        return result

    def batch_classify_begrippen(
        self,
        items: List[Dict[str, str]]
    ) -> List[ClassificationResult]:
        """
        Batch classificatie voor corpus analyse.

        Args:
            items: List van {"begrip": ..., "definitie": ..., "context": ...}

        Returns:
            List van ClassificationResult objecten
        """
        logger.info(f"Batch classificatie: {len(items)} begrippen")
        return self.classifier.classify_batch(items)

    # ==========================================
    # CORE: Definitie Generatie (requires category)
    # ==========================================

    async def generate_definition(
        self,
        request: GenerationRequest
    ) -> DefinitionResponseV2:
        """
        Genereer definitie met VERPLICHTE ontologische categorie.

        Args:
            request: GenerationRequest met begrip + ontologische_categorie

        Raises:
            ValueError: Als ontologische_categorie ontbreekt

        Returns:
            DefinitionResponseV2
        """
        # VALIDATE: Category is required
        if not request.ontologische_categorie:
            raise ValueError(
                "ontologische_categorie is VERPLICHT. "
                "Roep eerst classify_begrip() aan om categorie te bepalen."
            )

        logger.info(
            f"Definitie generatie met category: {request.ontologische_categorie}"
        )

        return await self.orchestrator.create_definition(request)

    # ==========================================
    # CONVENIENCE: All-in-one (auto classify)
    # ==========================================

    async def classify_and_generate(
        self,
        begrip: str,
        context_dict: Dict[str, Any],
        auto_classify: bool = True,
        override_category: Optional[str] = None
    ) -> Tuple[ClassificationResult, DefinitionResponseV2]:
        """
        Convenience method: classificeer + genereer in 1 call.

        Args:
            begrip: Te definiëren begrip
            context_dict: Context data (organisatorisch, juridisch, etc.)
            auto_classify: Automatisch classificeren (True) of override gebruiken
            override_category: Handmatige category override (optional)

        Returns:
            (ClassificationResult, DefinitionResponseV2)
        """
        # STEP 1: Classificatie (pre-processing)
        if override_category:
            # Mock result voor override scenario
            classification = ClassificationResult(
                level=override_category,
                confidence=1.0,
                rationale="Handmatig overschreven door gebruiker",
                linguistic_cues=[]
            )
        else:
            classification = self.classify_begrip(
                begrip=begrip,
                definitie="",  # Nog geen definitie (pre-processing!)
                context=context_dict.get("context")
            )

        # STEP 2: Build request met classificatie
        request = GenerationRequest(
            begrip=begrip,
            ontologische_categorie=classification.level,
            organisatorische_context=context_dict.get("organisatorisch", []),
            juridische_context=context_dict.get("juridisch", []),
            wettelijke_basis=context_dict.get("wettelijk", [])
        )

        # STEP 3: Generate definitie
        response = await self.generate_definition(request)

        return classification, response
```

---

### 5.2 UI Integration Example

```python
# src/ui/components/tabs/definitie_tab.py

class DefinitieGeneratieTab:
    """Tab voor definitie generatie met classificatie preview."""

    def __init__(self, container: ServiceContainer):
        self.adapter = DefinitionServiceAdapter(container)

    def render(self):
        st.header("Definitie Generatie")

        # INPUT SECTION
        begrip = st.text_input("Begrip")
        context = st.text_area("Context")

        # ==========================================
        # STAP 1: CLASSIFICATIE PRE-PROCESSING
        # ==========================================
        if st.button("🔍 Classificeer", key="classify_btn"):
            if not begrip:
                st.error("Begrip is verplicht")
                return

            with st.spinner("Classificeren..."):
                # Pre-processing: classify VOOR generatie
                result = self.adapter.classify_begrip(
                    begrip=begrip,
                    definitie="",  # Nog geen definitie
                    context=context
                )

                # Store in session state
                st.session_state.classification_result = result

        # ==========================================
        # STAP 2: CLASSIFICATIE PREVIEW & OVERRIDE
        # ==========================================
        if "classification_result" in st.session_state:
            result = st.session_state.classification_result

            st.subheader("📊 Classificatie Resultaat")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Categorie", result.level)
            with col2:
                st.metric("Confidence", f"{result.confidence:.0%}")
            with col3:
                st.metric("Warnings", len(result.validation_warnings))

            # TRANSPARENCY: Show rationale
            with st.expander("🔍 Rationale"):
                st.write(result.rationale)
                if result.linguistic_cues:
                    st.write("**Linguistic cues:**")
                    for cue in result.linguistic_cues:
                        st.write(f"- {cue}")

            # OVERRIDE OPTION
            st.write("**Override categorie (optioneel):**")
            override = st.selectbox(
                "Gebruik andere categorie",
                options=["Gebruik AI suggestie", "TYPE", "EXEMPLAAR",
                         "PROCES", "RESULTAAT"],
                index=0
            )

            if override != "Gebruik AI suggestie":
                st.session_state.override_category = override
                st.info(f"✓ Categorie overschreven naar: {override}")

        # ==========================================
        # STAP 3: DEFINITIE GENERATIE
        # ==========================================
        if st.button("✨ Genereer Definitie", key="generate_btn"):
            if "classification_result" not in st.session_state:
                st.error("Classificeer eerst het begrip!")
                return

            # Get category (AI suggestie of override)
            category = st.session_state.get(
                "override_category",
                st.session_state.classification_result.level
            )

            with st.spinner("Genereren..."):
                # Build request met classificatie
                request = GenerationRequest(
                    begrip=begrip,
                    ontologische_categorie=category,
                    organisatorische_context=[context] if context else []
                )

                # Generate definitie
                response = await self.adapter.generate_definition(request)

                if response.success:
                    st.success("✓ Definitie gegenereerd!")
                    st.write(response.definition.definitie)
                else:
                    st.error(f"Fout: {response.error}")
```

---

### 5.3 Batch Processing Example

```python
# scripts/batch_classify_corpus.py

def batch_classify_wetgeving():
    """Classificeer 1000 begrippen uit wetgeving corpus."""

    # Load corpus
    corpus = load_wetgeving_corpus()  # 1000 begrippen

    # Prepare items
    items = [
        {
            "begrip": item["begrip"],
            "definitie": item["definitie"],
            "context": item.get("context")
        }
        for item in corpus
    ]

    # Batch classify (NO definition generation!)
    container = get_cached_container()
    adapter = DefinitionServiceAdapter(container)

    print(f"Classificeren {len(items)} begrippen...")
    results = adapter.batch_classify_begrippen(items)

    # Analyse verdeling
    stats = {
        "TYPE": sum(1 for r in results if r.level == "TYPE"),
        "EXEMPLAAR": sum(1 for r in results if r.level == "EXEMPLAAR"),
        "PROCES": sum(1 for r in results if r.level == "PROCES"),
        "RESULTAAT": sum(1 for r in results if r.level == "RESULTAAT"),
        "ONBESLIST": sum(1 for r in results if r.level == "ONBESLIST")
    }

    print("\n📊 Verdeling:")
    for category, count in stats.items():
        pct = count / len(results) * 100
        print(f"  {category:12} {count:4d} ({pct:5.1f}%)")

    # Export results
    export_classification_results(results, "wetgeving_classificaties.csv")
```

---

## 6. TRADE-OFFS SAMENVATTING

| Aspect | Optie A (Service Layer) | Optie B (Pre-Processing) ✅ | Optie C (Dedicated Service) |
|--------|-------------------------|----------------------------|------------------------------|
| **Herbruikbaarheid** | ❌ Laag | ✅ Hoog | ✅ Hoog |
| **UI Complexity** | ✅ Simpel (1 call) | ⚠️ Medium (2 calls) | ❌ Hoog (2 services) |
| **Separation of Concerns** | ❌ Gekoppeld | ✅ Gescheiden | ✅ Maximaal gescheiden |
| **Batch Processing** | ❌ Onmogelijk | ✅ Efficiënt | ✅ Efficiënt |
| **Preview UX** | ❌ Geen preview | ✅ Transparant | ✅ Transparant |
| **Testbaarheid** | ⚠️ Moeilijk | ✅ Goed | ✅ Excellent |
| **Corpus Analyse** | ❌ Te traag | ✅ Haalbaar | ✅ Haalbaar |
| **Validatie Bestaande** | ❌ Onmogelijk | ✅ Mogelijk | ✅ Mogelijk |
| **ServiceAdapter Rol** | ❌ GOD OBJECT | ✅ Facade (clean) | ⚠️ Bypassed |

---

## 7. IMPLEMENTATION ROADMAP

### Phase 1: Refactor ServiceAdapter (Week 1)

```
✓ Add classify_begrip() method
✓ Add batch_classify_begrippen() method
✓ Add validation: ontologische_categorie required in generate_definition()
✓ Add classify_and_generate() convenience method
✓ Update tests
```

### Phase 2: UI Integration (Week 2)

```
✓ Update DefinitieGeneratieTab met 3-stappen flow
✓ Add classificatie preview component
✓ Add override option
✓ Update user flow documentation
```

### Phase 3: Batch Processing (Week 3)

```
✓ Create scripts/batch_classify_corpus.py
✓ Add CSV export functionaliteit
✓ Create corpus analyse dashboard
✓ Performance optimization (parallel processing)
```

### Phase 4: Validation & Monitoring (Week 4)

```
✓ Add classificatie accuracy monitoring
✓ Create misclassification detection
✓ Add feedback loop (learn from corrections)
✓ Performance metrics dashboard
```

---

## 8. CONCLUSION & DECISION

### 🏆 FINAL RECOMMENDATION: **Optie B - Pipeline Pattern met Pre-Processing Layer**

**RATIONALE:**

1. **✅ Herbruikbaarheid:** Classificatie is standalone service, bruikbaar voor batch/validatie/analyse
2. **✅ Separation of Concerns:** Duidelijke pipeline: classify → build request → generate
3. **✅ UX Transparantie:** Gebruiker ziet classificatie VOOR generatie (preview + override)
4. **✅ Efficiency:** Batch classificatie 10x goedkoper dan via generatie
5. **✅ Testbaarheid:** Pre-processing stap is unit testable
6. **✅ Maintainability:** ServiceAdapter blijft Facade (geen GOD OBJECT)

**IMPLEMENTATION EFFORT:**

| Component | Effort | Priority |
|-----------|--------|----------|
| ServiceAdapter refactor | 4 uur | HIGH |
| UI integration (3-stappen flow) | 6 uur | HIGH |
| Batch processing scripts | 3 uur | MEDIUM |
| Tests + documentation | 4 uur | HIGH |
| **TOTAL** | **17 uur** (~2 dagen) | |

**RISKS:**

- ⚠️ UI moet 2 calls doen (maar convenience method lost dit op)
- ⚠️ State management in UI (maar Streamlit session_state lost dit op)
- ⚠️ Backward compatibility (maar refactor lost dit op)

**MITIGATIONS:**

1. Add `classify_and_generate()` convenience method voor simpele use case
2. Add state management helpers in UI utilities
3. Add deprecation warnings voor oude API

---

## 9. STRATEGIC VALUE

**Voor de organisatie:**

- **Cost Savings:** 10x goedkopere batch processing (€50 → €5 voor 1000 classificaties)
- **Time Savings:** 10x sneller (10 min → 1 min voor 100 begrippen)
- **Quality:** Preview + override → betere accuracy
- **Insights:** Corpus analyse mogelijk (verdeling TYPE/PROCES/RESULTAAT in wetgeving)

**Voor developers:**

- **Clean Architecture:** Duidelijke separation of concerns
- **Testability:** Pre-processing stap is unit testable
- **Maintainability:** ServiceAdapter blijft Facade, geen GOD OBJECT
- **Reusability:** Classificatie bruikbaar in alle scenario's

**Voor gebruikers:**

- **Transparency:** Zie classificatie VOOR generatie
- **Control:** Override optie voor AI suggesties
- **Feedback:** Rationale + confidence scoring
- **Speed:** Snellere batch operations

---

## 10. NEXT STEPS

1. **Decision:** Approve Optie B als strategic direction
2. **Planning:** Schedule 2-dag sprint voor implementation
3. **Design:** Review ServiceAdapter API met team
4. **Implementation:** Start met Phase 1 (ServiceAdapter refactor)
5. **Testing:** Unit + integration tests
6. **Documentation:** Update architecture docs + user guides
7. **Rollout:** Phased rollout met feature flag

---

**END OF STRATEGIC ANALYSIS**

**Decision Required:** Approve/Reject/Modify recommendation voor Optie B

**Next Document:** Implementation Plan (indien approved)
