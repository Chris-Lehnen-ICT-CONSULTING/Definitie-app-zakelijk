# COMPREHENSIVE PROMPT BUILDING SYSTEM ANALYSIS - DefinitieAgent

**Analysis Date:** November 13, 2025  
**Project:** DefinitieAgent  
**Focus:** Context injection architecture and module organization  
**Thoroughness Level:** VERY THOROUGH

---

## EXECUTIVE SUMMARY

The DefinitieAgent prompt building system is a **true modular architecture** using an **Orchestrator pattern** with 16 specialized modules. The system is designed to generate complex legal definition prompts by orchestrating independent modules that each contribute specific prompt sections.

### Key Findings:

1. **16 Modules Total** - All registered and orchestrated by `PromptOrchestrator`
2. **Context Injection Scatter** - Context-related instructions are SCATTERED across **3 different modules**:
   - **ContextAwarenessModule** - Injects "📌 VERPLICHTE CONTEXT INFORMATIE"
   - **ErrorPreventionModule** - Injects "🚨 CONTEXT-SPECIFIEKE VERBODEN"  
   - **DefinitionTaskModule** - Contains "Context verwerkt zonder expliciete benoeming" in checklist

3. **Shared State Pattern** - Modules share context via `ModuleContext.shared_state` dictionary
4. **Dependency Management** - PromptOrchestrator resolves execution order using topological sort (Kahn's algorithm)

---

## ARCHITECTURE OVERVIEW

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROMPT BUILDING SYSTEM                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────┐
        │      PromptServiceV2 (Entry Point)     │
        │  - Builds EnrichedContext                │
        │  - Calls UnifiedPromptBuilder            │
        └─────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────┐
        │     UnifiedPromptBuilder (Legacy)       │
        │  - Alternative prompt generation        │
        └─────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────┐
        │        ModularPromptAdapter             │
        │  - Facade/Adapter pattern               │
        │  - Bridges old interface to new system  │
        └─────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────┐
        │       PromptOrchestrator                │
        │  - Module registration & lifecycle     │
        │  - Dependency resolution               │
        │  - Parallel/sequential execution       │
        │  - Output combination                  │
        └─────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────┐
        │          16 SPECIALIZED MODULES         │
        │   (See details below - Section 3)       │
        └─────────────────────────────────────────┘
```

---

## SECTION 1: PROMPT ORCHESTRATOR ARCHITECTURE

### File: `src/services/prompts/modules/prompt_orchestrator.py`

**Purpose:** Central orchestration of all prompt modules

**Key Responsibilities:**
1. Module registration and lifecycle management
2. Dependency resolution using Kahn's algorithm
3. Parallel and sequential execution
4. Output combination and validation

### Module Registration Flow

```python
# ModularPromptAdapter._setup_orchestrator() (line 120-130)
orchestrator = get_cached_orchestrator()  # Singleton pattern
modules = [
    ExpertiseModule(),
    OutputSpecificationModule(),
    GrammarModule(),
    ContextAwarenessModule(),        # ← CONTEXT INJECTION #1
    SemanticCategorisationModule(),
    TemplateModule(),
    # Rule modules (7 total)
    AraiRulesModule(),
    ConRulesModule(),
    EssRulesModule(),
    IntegrityRulesModule(),
    SamRulesModule(),
    StructureRulesModule(),
    VerRulesModule(),
    # Final modules
    ErrorPreventionModule(),         # ← CONTEXT INJECTION #2
    MetricsModule(),
    DefinitionTaskModule(),          # ← CONTEXT INJECTION #3
]

for module in modules:
    orchestrator.register_module(module)
```

### Default Module Execution Order

From `prompt_orchestrator.py`, lines 354-372:

```python
[
    "expertise",                    # Priority: 100
    "output_specification",
    "grammar",
    "context_awareness",            # Priority: 70
    "semantic_categorisation",
    "template",
    "arai_rules",                   # Validation rules
    "con_rules",
    "ess_rules",
    "structure_rules",
    "integrity_rules",
    "sam_rules",
    "ver_rules",
    "error_prevention",             # Priority: default
    "metrics",
    "definition_task",              # Final module
]
```

### Execution Model

**Sequential Batching (Lines 97-141):**
- Uses topological sort (Kahn's algorithm)
- Determines dependencies between modules
- Groups independent modules into batches
- Executes batches sequentially, modules within batch in parallel

**Parallel Workers:**
- Default: 4 max_workers
- Uses ThreadPoolExecutor for batch execution
- Thread-safe with proper error handling

---

## SECTION 2: CONTEXT INJECTION POINTS - DETAILED MAPPING

### INJECTION POINT #1: ContextAwarenessModule

**File:** `src/services/prompts/modules/context_awareness_module.py`  
**Module ID:** `context_awareness`  
**Priority:** 70  
**Dependencies:** None

#### Context Injection Locations:

**Line 239 (Moderate Context - 0.5 ≤ score < 0.8):**
```python
sections.append("📌 VERPLICHTE CONTEXT INFORMATIE:")
sections.append(
    "⚠️ BELANGRIJKE INSTRUCTIE: Gebruik onderstaande context om de definitie "
    "specifiek te maken voor deze organisatorische, juridische en wettelijke context. "
    "Formuleer de definitie zodanig dat deze past binnen deze specifieke context, "
    "zonder de context expliciet te benoemen."
)
```

**Line 201 (Rich Context - score ≥ 0.8):**
```python
sections.append("📊 UITGEBREIDE CONTEXT ANALYSE:")
sections.append(
    "⚠️ VERPLICHT: Gebruik onderstaande specifieke context om de definitie te formuleren "
    "voor deze organisatorische, juridische en wettelijke setting. Maak de definitie "
    "contextspecifiek zonder de context expliciet te benoemen."
)
```

**Line 277 (Minimal Context - score < 0.5):**
```python
return f"📍 VERPLICHTE CONTEXT: {context_text}\n⚠️ INSTRUCTIE: Formuleer de "
        f"definitie specifiek voor bovenstaande organisatorische, juridische en "
        f"wettelijke context zonder deze expliciet te benoemen."
```

#### Context Richness Scoring (Lines 143-184):

```python
def _calculate_context_score(self, enriched_context) -> float:
    """Calculates 0.0-1.0 score based on:
    - Base context items (max 0.3)
    - Sources confidence (max 0.4)  
    - Expanded terms (max 0.2)
    - Confidence scores (max 0.1)
    """
```

#### Shared State Distribution (Lines 368-395):

The module shares context types via `context.set_shared()`:
```python
# Line 388-392
context.set_shared("organization_contexts", org_contexts)      # Used by ErrorPreventionModule
context.set_shared("juridical_contexts", jur_contexts)        # Used by ErrorPreventionModule
context.set_shared("legal_basis_contexts", wet_contexts)      # Used by ErrorPreventionModule
```

#### Context Types Handled:

From lines 382-384:
```python
org_contexts = self._extract_contexts(base_context.get("organisatorisch"))
jur_contexts = self._extract_contexts(base_context.get("juridisch"))
wet_contexts = self._extract_contexts(base_context.get("wettelijk"))
```

These come from `EnrichedContext.base_context` which has keys:
- `organisatorisch` / `organisatorische_context`
- `juridisch` / `juridische_context`
- `wettelijk` / `wettelijke_basis`

---

### INJECTION POINT #2: ErrorPreventionModule

**File:** `src/services/prompts/modules/error_prevention_module.py`  
**Module ID:** `error_prevention`  
**Priority:** Default (50)  
**Dependencies:** `["context_awareness"]`

#### Context Injection Location:

**Lines 95-100:**
```python
context_forbidden = self._build_context_forbidden(
    org_contexts, jur_contexts, wet_contexts
)
if context_forbidden:
    sections.append("\n### 🚨 CONTEXT-SPECIFIEKE VERBODEN:")
    sections.extend(context_forbidden)
```

#### Context Injection Method (Lines 193-245):

**Context Retrieval (Lines 75-79):**
```python
# Haal context informatie op van ContextAwarenessModule (via shared state)
org_contexts = context.get_shared("organization_contexts", [])
jur_contexts = context.get_shared("juridical_contexts", [])
wet_contexts = context.get_shared("legal_basis_contexts", [])
```

**Organization Mapping (Lines 209-219):**
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

**Generated Forbidden Instructions (Lines 221-243):**

For each context type, generates specific warnings:
```python
# Organisational context (line 222-231)
for org in org_contexts:
    forbidden.append(f"- Gebruik de term '{org}' of een variant daarvan "
                    f"niet letterlijk in de definitie.")
    if org in org_mappings:
        forbidden.append(f"- Gebruik de term '{org_mappings[org]}' of een "
                        f"variant daarvan niet letterlijk in de definitie.")

# Juridical context (lines 234-237)
for jur in jur_contexts:
    forbidden.append(f"- Vermijd expliciete vermelding van juridisch context "
                    f"'{jur}' in de definitie.")

# Legal basis context (lines 240-243)
for wet in wet_contexts:
    forbidden.append(f"- Vermijd expliciete vermelding van wetboek '{wet}' "
                    f"in de definitie.")
```

#### Validation Matrix (Lines 247-259):

Also includes a validation matrix that references context handling:
- Line 256: "Letterlijke contextvermelding | ✅ | Noem context niet letterlijk"

---

### INJECTION POINT #3: DefinitionTaskModule

**File:** `src/services/prompts/modules/definition_task_module.py`  
**Module ID:** `definition_task`  
**Priority:** Default (50)  
**Dependencies:** `["semantic_categorisation"]`

#### Context References in Checklist:

**Lines 172-204 - _build_checklist():**

The checklist includes this line (line 204):
```python
→ Context verwerkt zonder expliciete benoeming
```

This is part of the construction guide that appears in the final checklist.

#### Context-Aware Quality Control (Lines 206-223):

```python
def _build_quality_control(self, has_context: bool) -> str:
    context_vraag = "de gegeven context" if has_context else "algemeen gebruik"
    
    return f"""#### 🔍 KWALITEITSCONTROLE:
Stel jezelf deze vragen:
1. Is direct duidelijk WAT het begrip is (niet het doel)?
2. Kan iemand hiermee bepalen of iets wel/niet onder dit begrip valt?
3. Is de formulering specifiek genoeg voor {context_vraag}?
4. Bevat de definitie alleen essentiële informatie?"""
```

#### Context Detection in Execute (Lines 84-104):

```python
# Derive context from enriched_context.base_context
base_ctx = context.enriched_context.base_context if context and context.enriched_context else {}
jur_contexts = base_ctx.get("juridische_context") or base_ctx.get("juridisch") or []
wet_basis = base_ctx.get("wettelijke_basis") or base_ctx.get("wettelijk") or []
has_context = bool(org_contexts or jur_contexts or wet_basis)
```

#### Metadata Generation (Lines 259-299):

Generates context metadata including:
```python
if jur_contexts:
    lines.append(f"- Juridische context: {', '.join(jur_contexts)}")
else:
    lines.append("- Juridische context: geen")

if wet_basis:
    lines.append(f"- Wettelijke basis: {', '.join(wet_basis)}")
else:
    lines.append("- Wettelijke basis: geen")
```

---

## SECTION 3: COMPLETE MODULE INVENTORY

### All 16 Modules with Context Handling

| # | Module ID | Class Name | Priority | Dependencies | Context Role | File |
|---|-----------|-----------|----------|--------------|--------------|------|
| 1 | expertise | ExpertiseModule | 100 | None | Sets "word_type" | expertise_module.py |
| 2 | output_specification | OutputSpecificationModule | - | None | Validates output | output_specification_module.py |
| 3 | grammar | GrammarModule | - | None | Grammar rules | grammar_module.py |
| 4 | **context_awareness** | **ContextAwarenessModule** | **70** | **None** | **🚨 INJECTS CONTEXT** | context_awareness_module.py |
| 5 | semantic_categorisation | SemanticCategorisationModule | - | None | Sets "ontological_category" | semantic_categorisation_module.py |
| 6 | template | TemplateModule | 60 | None | Uses ontological_category | template_module.py |
| 7 | arai_rules | AraiRulesModule | - | None | General validation rules | arai_rules_module.py |
| 8 | con_rules | ConRulesModule | - | None | Context validation rules | con_rules_module.py |
| 9 | ess_rules | EssRulesModule | - | None | Essence validation rules | ess_rules_module.py |
| 10 | structure_rules | StructureRulesModule | - | None | Structure validation rules | structure_rules_module.py |
| 11 | integrity_rules | IntegrityRulesModule | 65 | None | Integrity validation rules | integrity_rules_module.py |
| 12 | sam_rules | SamRulesModule | - | None | Coherence validation rules | sam_rules_module.py |
| 13 | ver_rules | VerRulesModule | - | None | Form validation rules | ver_rules_module.py |
| 14 | **error_prevention** | **ErrorPreventionModule** | **50** | **context_awareness** | **🚨 INJECTS FORBIDDEN** | error_prevention_module.py |
| 15 | metrics | MetricsModule | - | None | Quality metrics | metrics_module.py |
| 16 | **definition_task** | **DefinitionTaskModule** | **50** | **semantic_categorisation** | **🚨 CONTEXT METADATA** | definition_task_module.py |

### Context Dependency Map

```
┌──────────────────────────────────────┐
│  ContextAwarenessModule              │
│  - Calculates context richness       │
│  - Injects "VERPLICHTE CONTEXT"      │
│  - Shares context via set_shared()   │
└──────────────────┬───────────────────┘
                   │
                   ├─→ Shares to ErrorPreventionModule
                   │   - organization_contexts
                   │   - juridical_contexts  
                   │   - legal_basis_contexts
                   │
                   └─→ Shares to DefinitionTaskModule
                       (indirectly via base_context)

┌──────────────────────────────────────┐
│  ErrorPreventionModule               │
│  - Depends on ContextAwarenessModule │
│  - Injects "CONTEXT-SPECIFIEKE       │
│    VERBODEN"                         │
│  - Maps org names to full names      │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│  DefinitionTaskModule                │
│  - Mentions "Context verwerkt        │
│    zonder expliciete benoeming"      │
│  - Generates context metadata        │
│  - Modifies quality control          │
│    instructions based on context     │
└──────────────────────────────────────┘
```

---

## SECTION 4: CONTEXT FLOW - ENTRY TO OUTPUT

### Step 1: Entry Point - PromptServiceV2

**File:** `src/services/prompts/prompt_service_v2.py` (Lines 84-142)

```python
async def build_generation_prompt(
    self,
    request: GenerationRequest,
    feedback_history: list[dict] | None = None,
    context: dict[str, Any] | None = None,
) -> PromptResult:
    # Build enriched context via HybridContextManager
    enriched_context = await self.context_manager.build_enriched_context(request)
    
    # Add ontologische_categorie to metadata
    if request.ontologische_categorie:
        enriched_context.metadata["ontologische_categorie"] = cat
```

### Step 2: Context Enrichment

**EnrichedContext Structure:**
```python
{
    "base_context": {
        "organisatorisch": ["NP", "DJI"],
        "organisatorische_context": ["Netherlands Police"],
        "juridisch": ["Criminal Code"],
        "juridische_context": ["Criminal Code"],
        "wettelijk": ["Wetboek van Strafrecht"],
        "wettelijke_basis": ["Wetboek van Strafrecht"],
    },
    "sources": [...],
    "expanded_terms": {...},
    "confidence_scores": {...},
    "metadata": {
        "ontologische_categorie": "proces",
        "semantic_category": "Proces",
        ...
    }
}
```

### Step 3: Module Execution - ContextAwarenessModule

```
INPUT: EnrichedContext with base_context values
  ↓
CALCULATION: context_score = f(base_context size, sources, expanded_terms, confidence)
  ↓
OUTPUT FORMAT SELECTION:
  - score ≥ 0.8: Rich formatting with detailed categories + sources + abbreviations
  - 0.5 ≤ score < 0.8: Moderate formatting with context list
  - score < 0.5: Minimal formatting
  ↓
SHARED STATE DISTRIBUTION:
  - context.set_shared("organization_contexts", org_contexts)
  - context.set_shared("juridical_contexts", jur_contexts)
  - context.set_shared("legal_basis_contexts", wet_contexts)
  ↓
OUTPUT TO PROMPT: Formatted context section with warnings
```

### Step 4: Module Execution - ErrorPreventionModule

```
INPUT: Shared state from ContextAwarenessModule
  ↓
RETRIEVAL:
  org_contexts = context.get_shared("organization_contexts", [])
  jur_contexts = context.get_shared("juridical_contexts", [])
  wet_contexts = context.get_shared("legal_basis_contexts", [])
  ↓
PROCESSING:
  - Map organization codes to full names
  - Generate "CONTEXT-SPECIFIEKE VERBODEN" for each context item
  - Add validation matrix
  ↓
OUTPUT TO PROMPT: Forbidden patterns section with context-specific rules
```

### Step 5: Module Execution - DefinitionTaskModule

```
INPUT: EnrichedContext + shared state
  ↓
CONTEXT DETECTION:
  has_context = bool(org_contexts or jur_contexts or wet_basis)
  ↓
OUTPUT MODIFICATIONS:
  - Quality control questions adapt based on has_context
  - Metadata section lists all active contexts
  - Checklist includes "Context verwerkt zonder expliciete benoeming"
  ↓
OUTPUT TO PROMPT: Final instructions with context metadata
```

### Step 6: Final Prompt Assembly

**PromptOrchestrator._combine_outputs()** (Lines 307-335):

```python
# Combines outputs in default module order:
ordered_sections = [
    expertise_output,
    output_specification_output,
    grammar_output,
    context_awareness_output,            # ← CONTEXT #1
    semantic_categorisation_output,
    template_output,
    arai_rules_output,
    con_rules_output,
    ess_rules_output,
    structure_rules_output,
    integrity_rules_output,
    sam_rules_output,
    ver_rules_output,
    error_prevention_output,             # ← CONTEXT #2
    metrics_output,
    definition_task_output,              # ← CONTEXT #3
]

final_prompt = "\n\n".join(ordered_sections)
```

---

## SECTION 5: CONTEXT INJECTION DUPLICATION ANALYSIS

### Problem Summary

Context-related instructions are **SCATTERED across 3 modules** instead of being **CONSOLIDATED**:

| Aspect | Location 1 | Location 2 | Location 3 |
|--------|-----------|-----------|-----------|
| **Module** | ContextAwarenessModule | ErrorPreventionModule | DefinitionTaskModule |
| **File** | context_awareness_module.py | error_prevention_module.py | definition_task_module.py |
| **Lines** | 239, 201, 277 | 99 | 204 |
| **Injection Type** | Context instructions | Forbidden patterns | Metadata + checklist |
| **What it says** | "VERPLICHTE CONTEXT INFORMATIE" | "CONTEXT-SPECIFIEKE VERBODEN" | "Context verwerkt zonder..." |
| **Data Dependency** | Direct from base_context | Shared state from module above | Direct from base_context |
| **Duplication Risk** | Score-based formatting | Re-lists contexts | Static text in checklist |

### Current Problem: Multiple Instruction Points

Users see context instructions in **3 different parts of prompt**:

1. **Early (After Grammar):** ContextAwarenessModule injects "📌 VERPLICHTE CONTEXT INFORMATIE"
2. **Middle (Before Metrics):** ErrorPreventionModule injects "🚨 CONTEXT-SPECIFIEKE VERBODEN"
3. **End (Final Section):** DefinitionTaskModule mentions "Context verwerkt zonder..." in checklist

### Redundancy Issues

1. **Context Information Repeated**
   - ContextAwarenessModule lists contexts in formatted section
   - ErrorPreventionModule re-lists contexts as "verboden" for each one
   - DefinitionTaskModule generates metadata listing contexts again

2. **Instructions Scattered**
   - Instruction to "use context but don't mention it literally" appears at **3 places**
   - Score-based formatting in ContextAwarenessModule vs. static text in DefinitionTaskModule
   - No single source of truth for context handling guidance

3. **Shared State Dependencies**
   - ErrorPreventionModule depends on ContextAwarenessModule's shared state
   - DefinitionTaskModule doesn't use shared state, reads base_context directly
   - Creates tight coupling and fragile data flow

4. **Token Usage Impact**
   - Each module reformats context information
   - Score-based strategy in ContextAwarenessModule doesn't fully propagate to other modules
   - ErrorPreventionModule generates forbidden lists that could be reused

---

## SECTION 6: MODULE DEPENDENCY GRAPH

### Explicit Dependencies

```
Definition of "dependency" per BasePromptModule.get_dependencies():
- Module A depends on Module B if get_dependencies() returns [B.module_id]
- Orchestrator uses Kahn's algorithm to order execution

Current explicit dependencies:
├── ErrorPreventionModule
│   └── depends on: ["context_awareness"]
│
└── DefinitionTaskModule
    └── depends on: ["semantic_categorisation"]

All other modules:
└── depend on: [] (no explicit dependencies)
```

### Implicit Dependencies (via shared_state)

```
Context Awareness Module (PRODUCER)
├── Sets: "context_richness_score"
├── Sets: "organization_contexts"
├── Sets: "juridical_contexts"
├── Sets: "legal_basis_contexts"
└── Sets: "word_type"

Error Prevention Module (CONSUMER)
├── Reads: "organization_contexts"
├── Reads: "juridical_contexts"
└── Reads: "legal_basis_contexts"

Definition Task Module (CONSUMER)
├── Reads: "word_type"
├── Reads: "ontological_category"
└── Also reads: base_context directly (not via shared_state)

Semantic Categorisation Module (PRODUCER)
├── Sets: "ontological_category"
└── Sets: "organization_contexts" (indirectly)

Template Module (CONSUMER)
├── Reads: "semantic_category" (from metadata)
└── Reads: "word_type"
```

### Execution Order vs Dependency Analysis

```
Default order (lines 354-372):
1. expertise                    [no deps]
2. output_specification         [no deps]
3. grammar                      [no deps]
4. context_awareness           [no deps] ← PRODUCER of shared contexts
5. semantic_categorisation     [no deps]
6. template                    [no deps]
7. arai_rules                  [no deps]
8. con_rules                   [no deps]
9. ess_rules                   [no deps]
10. structure_rules             [no deps]
11. integrity_rules             [no deps]
12. sam_rules                   [no deps]
13. ver_rules                   [no deps]
14. error_prevention            [context_awareness] ← CONSUMER of shared contexts
15. metrics                     [no deps]
16. definition_task             [semantic_categorisation]

Observation: ErrorPreventionModule's explicit dependency on context_awareness
is correct and enforced by Kahn's algorithm.
```

---

## SECTION 7: DATA FLOW - CONTEXT THROUGH MODULES

### Base Context Entry Point

From `prompt_service_v2.py`, the GenerationRequest is converted to EnrichedContext:

```python
request.organisatorische_context        → enriched_context.base_context["organisatorisch"]
request.juridische_context              → enriched_context.base_context["juridisch"]
request.wettelijke_basis                → enriched_context.base_context["wettelijk"]
```

### Context Awareness Module Processing

```
INPUT base_context:
{
    "organisatorisch": ["NP"],
    "juridisch": ["Strafrecht"],
    "wettelijk": ["Wetboek van Strafrecht"],
}

CALCULATION:
score = base_items/10 (max 0.3)
      + source_confidence * 0.4 (max 0.4)
      + expanded_terms/5 (max 0.2)
      + avg_confidence * 0.1 (max 0.1)
      = variable between 0.0-1.0

FORMATTING (based on score):
if score ≥ 0.8:
    - "📊 UITGEBREIDE CONTEXT ANALYSE:"
    - Detailed context with categories
    - Sources with confidence indicators
    - Abbreviations detailed
elif 0.5 ≤ score < 0.8:
    - "📌 VERPLICHTE CONTEXT INFORMATIE:"
    - Simple context list with warning
    - Abbreviations simple
else:
    - "📍 VERPLICHTE CONTEXT:"
    - Minimal formatting

OUTPUT shared_state:
- organization_contexts: ["NP"]
- juridical_contexts: ["Strafrecht"]
- legal_basis_contexts: ["Wetboek van Strafrecht"]
- context_richness_score: 0.35 (example)
```

### Error Prevention Module Processing

```
INPUT shared_state:
- organization_contexts: ["NP"]
- juridical_contexts: ["Strafrecht"]
- legal_basis_contexts: ["Wetboek van Strafrecht"]

PROCESSING:
for org in organization_contexts:
    output += f"- Gebruik de term '{org}' niet letterlijk"
    if org in mappings:
        output += f"- Gebruik de term '{mappings[org]}' niet letterlijk"

for jur in juridical_contexts:
    output += f"- Vermijd expliciete vermelding van '{jur}'"

for wet in legal_basis_contexts:
    output += f"- Vermijd expliciete vermelding van '{wet}'"

OUTPUT:
"### 🚨 CONTEXT-SPECIFIEKE VERBODEN:
- Gebruik de term 'NP' niet letterlijk in de definitie.
- Gebruik de term 'Nederlands Politie' niet letterlijk in de definitie.
- Vermijd expliciete vermelding van juridisch context 'Strafrecht' in de definitie.
- Vermijd expliciete vermelding van wetboek 'Wetboek van Strafrecht' in de definitie."
```

### Definition Task Module Processing

```
INPUT enriched_context.base_context:
{
    "organisatorisch": ["NP"],
    "juridisch": ["Strafrecht"],
    "wettelijk": ["Wetboek van Strafrecht"],
}

DETECTION:
has_context = bool(org_contexts or jur_contexts or wet_basis)
            = bool(["NP"] or ["Strafrecht"] or ["Wetboek..."])
            = True

MODIFICATION 1 - Quality Control:
if has_context:
    q3 = "Is de formulering specifiek genoeg voor de gegeven context?"
else:
    q3 = "Is de formulering specifiek genoeg voor algemeen gebruik?"

MODIFICATION 2 - Metadata:
metadata += "- Organisatorische context: NP"
metadata += "- Juridische context: Strafrecht"
metadata += "- Wettelijke basis: Wetboek van Strafrecht"

MODIFICATION 3 - Checklist:
→ Context verwerkt zonder expliciete benoeming (static text)

OUTPUT:
3 different context-related outputs in final prompt section
```

---

## SECTION 8: CONFIGURATION & INITIALIZATION

### Configuration Flow

From `modular_prompt_adapter.py` lines 136-213:

```python
def _convert_config_to_module_configs(self) -> dict[str, dict[str, Any]]:
    """Converts PromptComponentConfig to per-module configs"""
    
    return {
        "context_awareness": {
            "adaptive_formatting": not config.compact_mode,
            "confidence_indicators": config.enable_component_metadata,
            "include_abbreviations": config.include_examples_in_rules,
        },
        "error_prevention": {
            "include_validation_matrix": not config.compact_mode,
            "extended_forbidden_list": not config.compact_mode,
        },
        "definition_task": {
            "include_quality_control": not config.compact_mode,
            "include_metadata": config.enable_component_metadata,
        },
        # ... other modules
    }
```

### Singleton Pattern

From `modular_prompt_adapter.py` lines 42-88:

```python
def get_cached_orchestrator() -> PromptOrchestrator:
    """Singleton pattern with double-check locking"""
    global _global_orchestrator
    
    if _global_orchestrator is None:
        with _orchestrator_lock:
            if _global_orchestrator is None:
                orchestrator = PromptOrchestrator(max_workers=4)
                # Register all 16 modules
                _global_orchestrator = orchestrator
    
    return _global_orchestrator
```

**Benefit:** Modules only instantiated once per Streamlit session

---

## SECTION 9: EXECUTION FLOW - COMPLETE SEQUENCE

### Full Call Stack

```
1. UI Tab (e.g., definition_generator_tab.py)
   ↓
2. async_bridge.run_async(build_generation_prompt)
   ↓
3. PromptServiceV2.build_generation_prompt(request)
   ↓
4. HybridContextManager.build_enriched_context(request)
   ↓
5. UnifiedPromptBuilder.build_prompt(begrip, enriched_context)
   ↓
6. ModularPromptAdapter.build_prompt(begrip, enriched_context, config)
   ↓
7. PromptOrchestrator.build_prompt(begrip, enriched_context, config)
   ├─ resolve_execution_order() → [batch1, batch2, ..., batchN]
   ├─ For each batch:
   │  ├─ _execute_batch_parallel() or _execute_module()
   │  ├─ module.validate_input(context)
   │  ├─ module.execute(context) ← Generates prompt section
   │  └─ Returns ModuleOutput(content, metadata, success)
   └─ _combine_outputs() → Final prompt text
   ↓
8. Return complete prompt to UI
   ↓
9. UI passes prompt to UnifiedDefinitionGenerator for API call
```

### Module Execution Timeline

```
Timeline for 16 modules (parallel execution in batches):

Batch 1 (t=0):
  expertise
  output_specification
  grammar
  → No dependencies, all run in parallel

Batch 2 (t=T1):
  context_awareness        ← Produces shared context data
  semantic_categorisation
  template
  → Depends on Batch 1, can run in parallel

Batch 3 (t=T1+T2):
  arai_rules
  con_rules
  ess_rules
  structure_rules
  integrity_rules
  sam_rules
  ver_rules
  → Depend on Batch 2, run in parallel

Batch 4 (t=T1+T2+T3):
  error_prevention         ← Consumes context_awareness output
  metrics
  → error_prevention explicitly depends on context_awareness (enforced)

Batch 5 (t=T1+T2+T3+T4):
  definition_task          ← Consumes semantic_categorisation
  → Depends on semantic_categorisation (enforced)

Final: _combine_outputs() concatenates in defined order
```

---

## SECTION 10: CURRENT ISSUES & CONSOLIDATION OPPORTUNITIES

### Issue 1: Context Instructions Scattered

**Root Cause:**
- Each module that needs context information generates its own instructions
- No single point where context handling is consolidated
- Three different modules each contribute context-related text

**Impact:**
- Users see repetitive warnings about using context
- Token usage is higher than necessary
- If context handling needs updating, must change 3 modules

**Example - Token Waste:**
```
ContextAwarenessModule outputs:
"📌 VERPLICHTE CONTEXT INFORMATIE: ... gebruik context ... zonder expliciet..."
(~200 tokens)

ErrorPreventionModule outputs:
"🚨 CONTEXT-SPECIFIEKE VERBODEN:
- Gebruik 'NP' niet letterlijk
- Gebruik 'Netherlands Police' niet letterlijk
- Vermijd 'Strafrecht'
- Vermijd 'Wetboek van Strafrecht'"
(~100 tokens)

DefinitionTaskModule outputs:
"→ Context verwerkt zonder expliciete benoeming"
+ Quality control adapted
+ Metadata section
(~80 tokens)

Total: ~380 tokens for context-related content across 3 modules
```

### Issue 2: Shared State vs Direct Access

**Root Cause:**
- ErrorPreventionModule uses shared_state from ContextAwarenessModule
- DefinitionTaskModule reads base_context directly
- Inconsistent data access pattern

**Impact:**
- If context structure changes, must update multiple modules
- Harder to trace context flow through codebase
- Possible desynchronization if shared_state and base_context diverge

### Issue 3: Score-Based Formatting Not Propagated

**Root Cause:**
- ContextAwarenessModule calculates context_richness_score (0.0-1.0)
- Other modules don't use this score to adapt their output
- ErrorPreventionModule generates same "forbidden" output regardless of context richness

**Impact:**
- Opportunity for smarter, more concise context handling missed
- Could use low-richness-score to shorten context sections

### Issue 4: Organization Name Mapping Duplication

**Root Cause:**
- ErrorPreventionModule has hardcoded mapping:
  ```python
  org_mappings = {
      "NP": "Nederlands Politie",
      "DJI": "Dienst Justitiële Inrichtingen",
      ...
  }
  ```
- This mapping could be centralized in context manager or configuration

**Impact:**
- Maintenance burden if mappings change
- Not reusable by other modules
- Creates knowledge silos in codebase

---

## SECTION 11: TECHNICAL SPECIFICATIONS FOR ANALYSIS

### Module Interface

All modules implement `BasePromptModule` with:

```python
class BasePromptModule(ABC):
    def __init__(self, module_id: str, module_name: str, priority: int = 50)
    def initialize(self, config: dict[str, Any]) -> None
    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]
    def execute(self, context: ModuleContext) -> ModuleOutput
    def get_dependencies(self) -> list[str]
    def get_info(self) -> dict[str, Any]
```

### ModuleContext Structure

```python
@dataclass
class ModuleContext:
    begrip: str                              # The term to define
    enriched_context: EnrichedContext        # Full context with base_context, sources
    config: UnifiedGeneratorConfig           # Generator configuration
    shared_state: dict[str, Any]             # Inter-module communication
    
    def get_metadata(self, key: str, default: Any = None) -> Any
    def set_shared(self, key: str, value: Any) -> None
    def get_shared(self, key: str, default: Any = None) -> Any
```

### EnrichedContext Structure

```python
@dataclass
class EnrichedContext:
    base_context: dict[str, list[str]]       # Context types (organisatorisch, juridisch, etc)
    sources: list[Source]                    # External sources
    expanded_terms: dict[str, str]           # Abbreviations
    confidence_scores: dict[str, float]      # Confidence per item
    metadata: dict[str, Any]                 # Flexible metadata
```

### ModuleOutput Structure

```python
@dataclass
class ModuleOutput:
    content: str                             # Prompt section generated
    metadata: dict[str, Any]                 # Execution metadata
    success: bool = True                     # Execution succeeded?
    error_message: str | None = None         # Error if failed
    
    @property
    def is_empty(self) -> bool               # True if content empty
```

---

## SECTION 12: CONSOLIDATION DESIGN PATTERNS

### Pattern 1: Unified Context Module

**Proposed approach:**
- Create single `ContextInjectionModule` that handles ALL context-related output
- Takes context_richness_score into account for output sizing
- Generates:
  1. Initial context instructions (adaptive based on score)
  2. Context-specific forbidden patterns
  3. Context metadata
- Other modules only read context via shared_state, don't generate context output

**Benefits:**
- Single source of truth for context guidance
- Reduces token usage through consolidation
- Easier maintenance and updates
- Clear responsibility separation

### Pattern 2: Context Service

**Proposed approach:**
- Extract context handling logic into separate service
- Service provides:
  1. `calculate_context_richness(base_context) → float`
  2. `generate_context_instructions(score, contexts) → str`
  3. `generate_forbidden_patterns(contexts) → list[str]`
  4. `map_organization_names(codes) → dict[str, str]`
- Modules use service instead of implementing logic directly

**Benefits:**
- Reusable across codebase
- Centralized organization mappings
- Consistent calculations
- Testable

### Pattern 3: Tiered Context Output

**Proposed approach:**
- Define 3 output "levels" based on context_richness_score:
  - **Level 1 (score < 0.3):** Minimal context warning + metadata
  - **Level 2 (0.3-0.7):** Standard context instructions + specific forbiddens
  - **Level 3 (score ≥ 0.7):** Detailed context analysis + rich formatting
- Single module generates appropriate level output
- Reduces redundancy and token waste

---

## CONCLUSION

The DefinitieAgent prompt building system uses a well-designed **16-module orchestrator pattern** with proper dependency management and parallel execution. However, **context-related instructions are scattered across 3 different modules**, creating redundancy and maintenance challenges.

### Key Takeaways:

1. **Architecture is sound** - Modular design, proper orchestration, dependency handling
2. **Context injection is scattered** - Instructions repeated across ContextAwarenessModule, ErrorPreventionModule, DefinitionTaskModule
3. **Consolidation opportunity** - Significant token savings and maintenance improvement possible
4. **Data flow is mostly clean** - Uses shared_state pattern effectively (with one exception: DefinitionTaskModule reads base_context directly)
5. **Organization mappings are hardcoded** - Should be centralized

### Recommendations:

1. **High Priority:** Consolidate context injection into single module
2. **Medium Priority:** Centralize organization name mappings
3. **Medium Priority:** Ensure consistent context data access (shared_state everywhere)
4. **Low Priority:** Utilize context_richness_score in all context-aware modules
5. **Enhancement:** Create reusable ContextService for cross-module use

---

**Analysis Complete** - Ready for implementation planning
