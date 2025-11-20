# CONTEXT INJECTION SCATTER - KEY FINDINGS

## Quick Reference: Where Context Instructions Are Scattered

### 🚨 PROBLEM: Context handling is SPLIT across 3 different modules

| # | Module | File | Line(s) | Injection | Token Cost |
|----|--------|------|---------|-----------|------------|
| 1️⃣ | **ContextAwarenessModule** | `context_awareness_module.py` | 239, 201, 277 | "📌 VERPLICHTE CONTEXT INFORMATIE" | ~200 |
| 2️⃣ | **ErrorPreventionModule** | `error_prevention_module.py` | 99 | "🚨 CONTEXT-SPECIFIEKE VERBODEN" | ~100 |
| 3️⃣ | **DefinitionTaskModule** | `definition_task_module.py` | 204 | "Context verwerkt zonder expliciete benoeming" | ~80 |

**Total Redundant Token Cost: ~380 tokens**

---

## INJECTION POINT #1: ContextAwarenessModule

**File:** `src/services/prompts/modules/context_awareness_module.py`

### What It Does:
- Calculates `context_richness_score` (0.0-1.0) based on context quality
- Generates adaptive formatting:
  - Rich (≥0.8): "📊 UITGEBREIDE CONTEXT ANALYSE"
  - Moderate (0.5-0.8): "📌 VERPLICHTE CONTEXT INFORMATIE"
  - Minimal (<0.5): "📍 VERPLICHTE CONTEXT"
- **Shares context via shared_state:**
  ```python
  context.set_shared("organization_contexts", org_contexts)
  context.set_shared("juridical_contexts", jur_contexts)
  context.set_shared("legal_basis_contexts", wet_contexts)
  ```

### Context Instruction Text (Lines 239-242):
```python
"📌 VERPLICHTE CONTEXT INFORMATIE:"
"⚠️ BELANGRIJKE INSTRUCTIE: Gebruik onderstaande context om de definitie 
specifiek te maken voor deze organisatorische, juridische en wettelijke context. 
Formuleer de definitie zodanig dat deze past binnen deze specifieke context, 
zonder de context expliciet te benoemen."
```

### Problem:
- **Score-based formatting** not propagated to other modules
- Other modules don't know if context is rich/moderate/minimal
- Can't adapt their output based on context richness

---

## INJECTION POINT #2: ErrorPreventionModule

**File:** `src/services/prompts/modules/error_prevention_module.py`

### What It Does:
- **Reads shared_state** from ContextAwarenessModule (Lines 75-79):
  ```python
  org_contexts = context.get_shared("organization_contexts", [])
  jur_contexts = context.get_shared("juridical_contexts", [])
  wet_contexts = context.get_shared("legal_basis_contexts", [])
  ```
- Maps organization codes to full names (Lines 209-219):
  ```python
  org_mappings = {
      "NP": "Nederlands Politie",
      "DJI": "Dienst Justitiële Inrichtingen",
      ...
  }
  ```
- Generates context-specific forbidden patterns (Lines 193-245)

### Context Injection (Lines 95-100):
```python
context_forbidden = self._build_context_forbidden(...)
if context_forbidden:
    sections.append("\n### 🚨 CONTEXT-SPECIFIEKE VERBODEN:")
    sections.extend(context_forbidden)
```

### Generated Output Example:
```
### 🚨 CONTEXT-SPECIFIEKE VERBODEN:
- Gebruik de term 'NP' niet letterlijk in de definitie.
- Gebruik de term 'Nederlands Politie' niet letterlijk in de definitie.
- Vermijd expliciete vermelding van juridisch context 'Strafrecht' in de definitie.
- Vermijd expliciete vermelding van wetboek 'Wetboek van Strafrecht' in de definitie.
```

### Problems:
1. **Organization mappings hardcoded** - Not centralized, not reusable
2. **Re-lists contexts already shown** - User sees same contexts 2-3 times
3. **Tight coupling** - Depends on ContextAwarenessModule's shared_state
4. **Dependency marked explicitly** - `get_dependencies() = ["context_awareness"]`

---

## INJECTION POINT #3: DefinitionTaskModule

**File:** `src/services/prompts/modules/definition_task_module.py`

### What It Does:
- Generates final instructions and metadata
- Reads context **directly from base_context** (NOT via shared_state) - Lines 84-104:
  ```python
  base_ctx = context.enriched_context.base_context
  jur_contexts = base_ctx.get("juridische_context") or base_ctx.get("juridisch") or []
  wet_basis = base_ctx.get("wettelijke_basis") or base_ctx.get("wettelijk") or []
  has_context = bool(org_contexts or jur_contexts or wet_basis)
  ```
- Adapts quality control questions based on `has_context`
- Generates context metadata listing

### Context References:

**In Checklist (Line 204):**
```python
→ Context verwerkt zonder expliciete benoeming
```

**Quality Control Adaption (Lines 206-223):**
```python
if has_context:
    q3 = "Is de formulering specifiek genoeg voor de gegeven context?"
else:
    q3 = "Is de formulering specifiek genoeg voor algemeen gebruik?"
```

**Metadata Generation (Lines 259-299):**
```python
if jur_contexts:
    lines.append(f"- Juridische context: {', '.join(jur_contexts)}")
if wet_basis:
    lines.append(f"- Wettelijke basis: {', '.join(wet_basis)}")
```

### Problems:
1. **Inconsistent data access** - Reads base_context directly (unlike ErrorPreventionModule)
2. **Doesn't use shared_state** - Ignores score or context richness
3. **Static checklist text** - Always the same, not context-aware
4. **Re-lists contexts again** - Third place where contexts are mentioned

---

## DATA FLOW VISUALIZATION

```
GenerationRequest
    ↓
HybridContextManager.build_enriched_context()
    ↓
EnrichedContext:
  base_context = {
    "organisatorisch": ["NP"],
    "juridisch": ["Strafrecht"],
    "wettelijk": ["Wetboek..."]
  }
    ↓
PromptOrchestrator.build_prompt()
    ├─→ ContextAwarenessModule
    │   ├─ Calculates: context_score = 0.35
    │   ├─ Generates: "📌 VERPLICHTE CONTEXT INFORMATIE"
    │   └─ Shares:
    │      - organization_contexts: ["NP"]
    │      - juridical_contexts: ["Strafrecht"]
    │      - legal_basis_contexts: ["Wetboek..."]
    │      - context_richness_score: 0.35
    │
    ├─→ ErrorPreventionModule (depends on context_awareness)
    │   ├─ Reads: shared_state
    │   ├─ Maps: NP → "Nederlands Politie"
    │   ├─ Generates: "🚨 CONTEXT-SPECIFIEKE VERBODEN"
    │   └─ Lists contexts again:
    │      - NP (literal)
    │      - Nederlands Politie (full name)
    │      - Strafrecht
    │      - Wetboek...
    │
    └─→ DefinitionTaskModule (depends on semantic_categorisation)
        ├─ Reads: base_context DIRECTLY
        ├─ Detects: has_context = True
        ├─ Generates:
        │  - Quality control (context-aware)
        │  - Metadata section
        │  - Checklist line: "Context verwerkt zonder..."
        └─ Lists contexts THIRD time:
           - Organisatorische: NP
           - Juridische: Strafrecht
           - Wettelijke basis: Wetboek...
```

---

## CONSOLIDATION OPPORTUNITY

### Current Situation:
- **3 modules** generate context-related content
- **380 tokens** wasted on redundancy
- **No single source of truth** for context guidance
- **Inconsistent data access** patterns

### Proposed Solution:

**Create a single ContextInjectionModule** that:

1. **Consolidates all context output** into one place
2. **Uses context_richness_score** to determine output level
3. **Generates all three parts together:**
   - Initial context instructions (adaptive)
   - Context-specific forbidden patterns
   - Context metadata
4. **Centralizes organization mappings**
5. **Enforces consistent data access** via shared_state

### Benefits:
- ✅ Reduce token usage by ~200-300 tokens
- ✅ Single source of truth for context handling
- ✅ Easier maintenance and updates
- ✅ Clear responsibility separation
- ✅ Reusable organization mappings

---

## DETAILED CONTEXT LOCATIONS FOR CONSOLIDATION

### Module 1: ContextAwarenessModule
- **File:** `src/services/prompts/modules/context_awareness_module.py`
- **Lines to consolidate:**
  - 239: Moderate context header
  - 201: Rich context header
  - 277: Minimal context fallback
  - 368-395: Shared state distribution

### Module 2: ErrorPreventionModule
- **File:** `src/services/prompts/modules/error_prevention_module.py`
- **Lines to consolidate:**
  - 75-79: Context retrieval
  - 95-100: Context forbidden injection
  - 193-245: _build_context_forbidden() method
  - 209-219: Organization mappings

### Module 3: DefinitionTaskModule
- **File:** `src/services/prompts/modules/definition_task_module.py`
- **Lines to consolidate:**
  - 84-104: Context detection from base_context
  - 206-223: Context-aware quality control
  - 259-299: Context metadata generation
  - 204: Checklist line "Context verwerkt..."

---

## EXECUTION ORDER IMPACT

```
Current order (PromptOrchestrator, lines 354-372):

...
4. context_awareness           (Priority: 70)
...
14. error_prevention           (Depends: ["context_awareness"])
16. definition_task            (Depends: ["semantic_categorisation"])

New proposed order (after consolidation):

...
4. context_injection           (Priority: 75, single source of truth)
...
(error_prevention and definition_task no longer handle context)
```

---

## NEXT STEPS FOR IMPLEMENTATION

### Phase 1: Analysis & Planning
- ✅ **DONE:** Identify all context injection points (3 modules)
- ✅ **DONE:** Map data dependencies
- ✅ **DONE:** Quantify token waste
- **TODO:** Design new ContextInjectionModule interface
- **TODO:** Plan fallback/compatibility strategy

### Phase 2: Consolidation
- **TODO:** Create new ContextInjectionModule
- **TODO:** Test context richness scoring
- **TODO:** Verify organization mappings work
- **TODO:** Update ErrorPreventionModule to remove context logic
- **TODO:** Update DefinitionTaskModule to remove context logic

### Phase 3: Integration & Testing
- **TODO:** Update ModularPromptAdapter registration
- **TODO:** Test with various context combinations
- **TODO:** Verify token reduction
- **TODO:** Test UI integration

### Phase 4: Documentation
- **TODO:** Update architecture documentation
- **TODO:** Document ContextInjectionModule design
- **TODO:** Update developer guidelines

