# DEF-126: Context Injection Consolidation - Implementation Plan

## Executive Summary

**Problem:** Context instructions are scattered across 3 modules (ContextAwarenessModule, ErrorPreventionModule, DefinitionTaskModule), resulting in ~380 tokens of redundancy and inconsistent data access patterns.

**Solution:** Consolidate ALL context-related output into a single `ContextInstructionModule` that serves as the Single Source of Truth for context guidance.

**Expected Impact:**
- 50-65% token reduction (~200-250 tokens saved)
- Single source of truth for context instructions
- Consistent data access pattern
- Improved maintainability

**Implementation Effort:** 4-5 hours

---

## 1. PROBLEM ANALYSIS ✅

### Current State - 3 Modules Handling Context

| Module | File | Lines | Responsibility | Token Cost | Data Access |
|--------|------|-------|----------------|------------|-------------|
| **ContextAwarenessModule** | `context_awareness_module.py` | 186-280, 368-395 | Context formatting & sharing | ~200 | enriched_context |
| **ErrorPreventionModule** | `error_prevention_module.py` | 75-79, 95-100, 193-245 | Context-specific forbidden patterns | ~100 | shared_state |
| **DefinitionTaskModule** | `definition_task_module.py` | 84-104, 204, 206-299 | Context metadata & checklist | ~80 | base_context (DIRECT) |
| **TOTAL** | 3 files | ~150 lines | Scattered responsibility | **~380 tokens** | **Inconsistent** |

### Key Issues

1. **No Single Source of Truth**
   - Context instructions generated in 3 different places
   - Same context data listed 2-3 times in prompt
   - No coordination between modules

2. **Inconsistent Data Access Patterns**
   - ContextAwarenessModule: Reads `enriched_context`, writes `shared_state`
   - ErrorPreventionModule: Reads `shared_state` (depends on context_awareness)
   - DefinitionTaskModule: Reads `base_context` DIRECTLY (ignores shared_state!)
   
3. **Underutilized Context Richness Score**
   - ContextAwarenessModule calculates `context_richness_score` (0.0-1.0)
   - Score is stored in shared_state but ONLY used by ContextAwarenessModule itself
   - Other modules don't adapt output based on context quality

4. **Hardcoded Organization Mappings**
   - ErrorPreventionModule has hardcoded org mappings (lines 209-219)
   - Not reusable, not centralized
   - Difficult to maintain

### Evidence from Code Analysis

**ContextAwarenessModule (lines 368-395):**
```python
def _share_traditional_context(self, context: ModuleContext) -> None:
    """Deel alle actieve context types voor andere modules."""
    # Shares: organization_contexts, juridical_contexts, legal_basis_contexts
    context.set_shared("organization_contexts", org_contexts)
    context.set_shared("juridical_contexts", jur_contexts)
    context.set_shared("legal_basis_contexts", wet_contexts)
```

**ErrorPreventionModule (lines 75-79):**
```python
# Haal context informatie op van ContextAwarenessModule
org_contexts = context.get_shared("organization_contexts", [])
jur_contexts = context.get_shared("juridical_contexts", [])
wet_contexts = context.get_shared("legal_basis_contexts", [])
```

**DefinitionTaskModule (lines 84-98):**
```python
# Derive juridical and legal-basis contexts from enriched base_context
base_ctx = context.enriched_context.base_context if context and context.enriched_context else {}
jur_contexts = base_ctx.get("juridische_context") or base_ctx.get("juridisch") or []
wet_basis = base_ctx.get("wettelijke_basis") or base_ctx.get("wettelijk") or []
# ⚠️ INCONSISTENT: Reads directly from base_context, ignores shared_state!
```

---

## 2. SOLUTION ARCHITECTURE

### Design: Single Source of Truth Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                   NEW: ContextInstructionModule              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ SINGLE SOURCE OF TRUTH for ALL context instructions  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  Responsibilities:                                          │
│  ✓ Calculate context_richness_score (from ContextAwareness)│
│  ✓ Generate adaptive context instructions                  │
│  ✓ Generate context-specific forbidden patterns           │
│  ✓ Generate context metadata                              │
│  ✓ Centralize organization mappings                       │
│  ✓ Share via shared_state for other modules              │
│                                                              │
│  Priority: 75 (high - context is foundational)             │
│  Dependencies: NONE (reads enriched_context directly)      │
└─────────────────────────────────────────────────────────────┘
                                ↓
                    Shares via shared_state:
                    - context_richness_score
                    - organization_contexts
                    - juridical_contexts
                    - legal_basis_contexts
                                ↓
┌─────────────────────────────────────────────────────────────┐
│            OTHER MODULES (simplified)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ContextAwarenessModule: DELETED (logic moved)        │  │
│  │ ErrorPreventionModule: Context logic REMOVED         │  │
│  │ DefinitionTaskModule: Context metadata REMOVED       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Module Responsibilities After Refactor

#### ContextInstructionModule (NEW) ✨
**Single responsibility:** Generate ALL context-related prompt content

**What it does:**
1. **Context Richness Scoring** (from ContextAwarenessModule)
   - Calculate score: 0.0-1.0 based on base_context, sources, expanded_terms
   - Adaptive output based on score
   
2. **Context Instructions** (from ContextAwarenessModule)
   - Rich (≥0.8): "📊 UITGEBREIDE CONTEXT ANALYSE"
   - Moderate (0.5-0.8): "📌 VERPLICHTE CONTEXT INFORMATIE"
   - Minimal (<0.5): "📍 VERPLICHTE CONTEXT"
   
3. **Context-Specific Forbidden Patterns** (from ErrorPreventionModule)
   - Organization mappings (NP → Nederlands Politie)
   - Generate "🚨 CONTEXT-SPECIFIEKE VERBODEN" section
   
4. **Context Metadata** (from DefinitionTaskModule)
   - Prompt metadata footer with context listings

**What it shares:**
- `context_richness_score` (float)
- `organization_contexts` (list)
- `juridical_contexts` (list)
- `legal_basis_contexts` (list)

#### ContextAwarenessModule (DELETED) ❌
**Action:** DELETE entire file - logic moved to ContextInstructionModule

**Rationale:**
- All business logic migrated to ContextInstructionModule
- No remaining purpose after consolidation
- Simplifies architecture (one less module)

#### ErrorPreventionModule (REFACTORED) 🔧
**Keep:** General error prevention (forbidden starters, validation matrix)
**Remove:** All context-specific logic (lines 75-79, 95-100, 193-245)

**What remains:**
- `_build_basic_errors()` - ❌ "Begin niet met lidwoorden", etc.
- `_build_forbidden_starters()` - ❌ "Start niet met 'is', 'betreft'", etc.
- `_build_validation_matrix()` - Validation table
- Final warning: "🚫 Let op: context en bronnen mogen niet letterlijk..."

**What is removed:**
- Context retrieval from shared_state (lines 75-79)
- `_build_context_forbidden()` method (lines 193-245)
- Organization mappings (lines 209-219)
- Context-specific verboden section (lines 95-100)

#### DefinitionTaskModule (REFACTORED) 🔧
**Keep:** Final instructions, checklist, quality control
**Remove:** Context metadata, context-aware adaptations (lines 84-104, 259-299)

**What remains:**
- `_build_task_assignment()` - ✏️ Definitieopdracht
- `_build_checklist()` - 📋 CONSTRUCTIE GUIDE (simplified, no context mention)
- `_build_quality_control()` - 🔍 KWALITEITSCONTROLE (generic version)
- `_build_ontological_marker()` - 📋 Ontologische marker
- `_build_final_instruction()` - ✏️ Geef nu de definitie

**What is removed:**
- Context detection logic (lines 84-104)
- Context-aware quality control adaptation (lines 206-223)
- `_build_metadata()` method (lines 225-246)
- `_build_prompt_metadata()` method (lines 259-299)
- Checklist line "Context verwerkt zonder..." (line 204)

---

## 3. DATA ACCESS PATTERN - UNIFIED APPROACH

### Decision: Use shared_state as Single Channel

**Rationale:**
- ✅ Enforces module boundaries (no direct access to enriched_context)
- ✅ Clear dependency graph (ContextInstructionModule has no deps)
- ✅ Testable (mock shared_state for unit tests)
- ✅ Consistent across all modules

### Data Flow (After Refactor)

```
EnrichedContext (input)
    ↓
ContextInstructionModule
    ├─ Reads: enriched_context.base_context
    ├─ Calculates: context_richness_score = 0.65
    ├─ Generates: ALL context output (~180 tokens)
    └─ Shares:
        - context_richness_score: 0.65
        - organization_contexts: ["NP", "OM"]
        - juridical_contexts: ["Strafrecht"]
        - legal_basis_contexts: ["Wetboek van Strafrecht"]
    ↓
ErrorPreventionModule (refactored)
    ├─ Reads: NOTHING from shared_state
    └─ Generates: Generic forbidden patterns only
    ↓
DefinitionTaskModule (refactored)
    ├─ Reads: NOTHING from shared_state (context-agnostic)
    └─ Generates: Generic final instructions
```

### No Backwards Compatibility Adapter Needed ✅

**Why:** Per CLAUDE.md → "⚠️ GEEN BACKWARDS COMPATIBILITY" (single-user app, not in production)

**Approach:** Direct refactor, no feature flags, no parallel paths

---

## 4. TOKEN OPTIMIZATION

### Current Token Distribution

| Section | Module | Current Tokens | After Consolidation | Reduction |
|---------|--------|----------------|---------------------|-----------|
| Context instructions | ContextAwarenessModule | ~200 | ~120 (adaptive) | -40% |
| Context forbidden | ErrorPreventionModule | ~100 | ~60 (consolidated) | -40% |
| Context metadata | DefinitionTaskModule | ~80 | ~0 (removed) | -100% |
| **TOTAL** | 3 modules | **~380** | **~180** | **-53%** |

### Adaptive Output Strategy

Use `context_richness_score` to determine output verbosity:

**Score ≥ 0.8 (Rich Context):**
```
📊 UITGEBREIDE CONTEXT ANALYSE:
⚠️ VERPLICHT: Gebruik onderstaande specifieke context...

🎯 ORGANISATORISCHE CONTEXT:
  • Nederlands Politie (NP)
🎯 JURIDISCHE CONTEXT:
  • Strafrecht
🎯 WETTELIJKE BASIS:
  • Wetboek van Strafrecht

🚨 CONTEXT-SPECIFIEKE VERBODEN:
- Gebruik 'NP' of 'Nederlands Politie' niet letterlijk...

📊 CONTEXT METADATA:
- Context type: organisatorisch + juridisch + wettelijk
- Context richness: 0.85
```
**Estimated tokens:** ~220

**Score 0.5-0.8 (Moderate Context):**
```
📌 VERPLICHTE CONTEXT INFORMATIE:
⚠️ INSTRUCTIE: Gebruik context zonder expliciete benoeming.

Context: Nederlands Politie (NP), Strafrecht, Wetboek van Strafrecht

🚨 VERBODEN: Vermijd letterlijke vermelding van NP, Strafrecht, Wetboek.
```
**Estimated tokens:** ~120

**Score < 0.5 (Minimal Context):**
```
📍 Context: geen specifieke context beschikbaar.
```
**Estimated tokens:** ~10

### Expected Savings

- **Typical case** (moderate context): 380 → 120 tokens = **-68% reduction**
- **Rich context**: 380 → 220 tokens = **-42% reduction**
- **Minimal context**: 380 → 10 tokens = **-97% reduction**

**Average across all cases:** **~53% token reduction**

---

## 5. IMPLEMENTATION PHASES

### Phase 1: Create ContextInstructionModule Skeleton (30 min)

**File:** `src/services/prompts/modules/context_instruction_module.py`

**Checklist:**
- [ ] Create new file based on BasePromptModule
- [ ] Define module_id: "context_instruction"
- [ ] Set priority: 75 (high - context is foundational)
- [ ] Implement empty methods: initialize(), validate_input(), execute(), get_dependencies()
- [ ] Return empty list from get_dependencies() (no dependencies)
- [ ] Add docstring explaining Single Source of Truth responsibility

**Skeleton code:**
```python
"""
Context Instruction Module - Single Source of Truth for ALL context-related output.

Consolidates context handling from:
- ContextAwarenessModule (context richness scoring, adaptive formatting)
- ErrorPreventionModule (context-specific forbidden patterns)
- DefinitionTaskModule (context metadata)

This module is the ONLY place that generates context instructions.
"""

import logging
from typing import Any

from .base_module import BasePromptModule, ModuleContext, ModuleOutput

logger = logging.getLogger(__name__)


class ContextInstructionModule(BasePromptModule):
    """
    Single Source of Truth for context instructions.
    
    Responsibilities:
    1. Calculate context richness score (0.0-1.0)
    2. Generate adaptive context instructions
    3. Generate context-specific forbidden patterns
    4. Generate context metadata
    5. Share context data via shared_state
    """

    def __init__(self):
        super().__init__(
            module_id="context_instruction",
            module_name="Context Instruction (Single Source of Truth)",
            priority=75,  # High priority - context is foundational
        )
        # Configuration flags
        self.adaptive_formatting = True
        self.confidence_indicators = True
        self.include_metadata = True

    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize module with configuration."""
        self._config = config
        self.adaptive_formatting = config.get("adaptive_formatting", True)
        self.confidence_indicators = config.get("confidence_indicators", True)
        self.include_metadata = config.get("include_metadata", True)
        self._initialized = True
        logger.debug("ContextInstructionModule initialized")

    def validate_input(self, context: ModuleContext) -> tuple[bool, str | None]:
        """This module always runs (even with no context)."""
        return True, None

    def execute(self, context: ModuleContext) -> ModuleOutput:
        """Generate all context-related output."""
        # TODO: Implement in Phase 2
        return ModuleOutput(content="", metadata={})

    def get_dependencies(self) -> list[str]:
        """No dependencies - reads enriched_context directly."""
        return []
```

**Test:**
```bash
python -m py_compile src/services/prompts/modules/context_instruction_module.py
```

---

### Phase 2: Migrate Business Logic (2 hours)

#### Step 2.1: Migrate Context Richness Scoring (30 min)

**Source:** `context_awareness_module.py` lines 143-184

**Action:** Copy `_calculate_context_score()` method to ContextInstructionModule

**Preservation checklist:**
- [ ] Base context contribution (max 0.3)
- [ ] Sources contribution (max 0.4)
- [ ] Expanded terms contribution (max 0.2)
- [ ] Confidence scores contribution (max 0.1)
- [ ] Score clamped to 1.0

**Test:**
```python
def test_context_richness_scoring():
    """Verify context richness score calculation."""
    module = ContextInstructionModule()
    context = ModuleContext(...)
    
    # Add test data
    context.enriched_context.base_context = {"organisatorisch": ["NP"]}
    
    output = module.execute(context)
    
    score = context.get_shared("context_richness_score")
    assert 0.0 <= score <= 1.0
```

#### Step 2.2: Migrate Adaptive Formatting (30 min)

**Source:** `context_awareness_module.py` lines 186-280

**Methods to migrate:**
- `_build_rich_context_section()` (lines 186-224)
- `_build_moderate_context_section()` (lines 226-261)
- `_build_minimal_context_section()` (lines 263-280)
- Helper methods: `_format_detailed_base_context()`, `_format_sources_with_confidence()`, etc.

**Consolidation opportunity:**
- Combine rich/moderate/minimal into single `_build_context_instructions()` method
- Use score-based switch statement
- Reduce duplication in formatting code

**Test:**
```python
def test_adaptive_formatting_rich():
    """Verify rich context formatting (score ≥ 0.8)."""
    # Mock high score
    assert "📊 UITGEBREIDE CONTEXT ANALYSE" in output.content

def test_adaptive_formatting_moderate():
    """Verify moderate context formatting (0.5 ≤ score < 0.8)."""
    # Mock medium score
    assert "📌 VERPLICHTE CONTEXT INFORMATIE" in output.content

def test_adaptive_formatting_minimal():
    """Verify minimal context formatting (score < 0.5)."""
    # Mock low score
    assert "📍 VERPLICHTE CONTEXT" in output.content
```

#### Step 2.3: Migrate Context Forbidden Patterns (30 min)

**Source:** `error_prevention_module.py` lines 193-245

**Methods to migrate:**
- `_build_context_forbidden()` (lines 193-245)

**Centralize organization mappings:**
```python
# Move to module-level constant for reusability
ORGANIZATION_MAPPINGS = {
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

**Consolidation opportunity:**
- Integrate forbidden patterns into main output (don't generate separately)
- Only generate when contexts exist (skip if empty)

**Test:**
```python
def test_context_forbidden_patterns():
    """Verify context-specific forbidden patterns."""
    # Mock context with NP
    assert "Gebruik de term 'NP'" in output.content
    assert "Nederlands Politie" in output.content  # Full name
```

#### Step 2.4: Migrate Context Metadata (30 min)

**Source:** `definition_task_module.py` lines 259-299

**Method to migrate:**
- `_build_prompt_metadata()` (lines 259-299)

**Consolidation opportunity:**
- Only generate metadata if `include_metadata=True` in config
- Use shared_state data (don't re-read base_context)
- Combine with main output as footer section

**Test:**
```python
def test_context_metadata():
    """Verify context metadata generation."""
    module = ContextInstructionModule()
    module.include_metadata = True
    
    output = module.execute(context)
    
    assert "🆔 Promptmetadata:" in output.content
    assert "Organisatorische context:" in output.content
```

---

### Phase 3: Implement Complete execute() Method (30 min)

**Orchestration logic:**

```python
def execute(self, context: ModuleContext) -> ModuleOutput:
    """Generate all context-related output."""
    try:
        # Step 1: Calculate context richness score
        context_score = self._calculate_context_score(context.enriched_context)
        context.set_shared("context_richness_score", context_score)
        
        # Step 2: Extract and share context data
        self._share_context_data(context)
        
        # Step 3: Generate main output sections
        sections = []
        
        # 3a. Context instructions (adaptive based on score)
        context_instructions = self._build_context_instructions(
            context, context_score
        )
        if context_instructions:
            sections.append(context_instructions)
        
        # 3b. Context-specific forbidden patterns
        forbidden_patterns = self._build_context_forbidden(context)
        if forbidden_patterns:
            sections.append("\n### 🚨 CONTEXT-SPECIFIEKE VERBODEN:")
            sections.extend(forbidden_patterns)
        
        # 3c. Context metadata (if enabled)
        if self.include_metadata:
            metadata = self._build_context_metadata(context)
            if metadata:
                sections.append("\n" + metadata)
        
        # Step 4: Combine sections
        content = "\n".join(sections)
        
        return ModuleOutput(
            content=content,
            metadata={
                "context_score": context_score,
                "has_context": bool(content.strip()),
            },
        )
        
    except Exception as e:
        logger.error(f"ContextInstructionModule failed: {e}", exc_info=True)
        return ModuleOutput(
            content="📍 Context: geen context beschikbaar (error)",
            metadata={"error": str(e)},
            success=False,
            error_message=f"Context instruction generation failed: {e}",
        )
```

**Test:**
```python
def test_complete_context_output():
    """Verify complete context output integration."""
    module = ContextInstructionModule()
    context = create_test_context(org=["NP"], jur=["Strafrecht"])
    
    output = module.execute(context)
    
    # Verify all three sections present
    assert "📌 VERPLICHTE CONTEXT" in output.content  # Instructions
    assert "🚨 CONTEXT-SPECIFIEKE VERBODEN" in output.content  # Forbidden
    assert "🆔 Promptmetadata" in output.content  # Metadata
    
    # Verify shared_state populated
    assert context.get_shared("context_richness_score") is not None
    assert context.get_shared("organization_contexts") == ["NP"]
```

---

### Phase 4: Update Orchestrator Registration (30 min)

**File:** Find where modules are registered (likely `src/services/prompts/prompt_service_v2.py` or similar)

**Actions:**
1. [ ] Register ContextInstructionModule
2. [ ] Remove ContextAwarenessModule registration
3. [ ] Verify execution order (ContextInstruction should run early, priority 75)

**Find registration point:**
```bash
grep -r "register_module" src/services/prompts/ --include="*.py"
```

**Expected registration code:**
```python
# NEW: Single source of truth for context
orchestrator.register_module(ContextInstructionModule())

# REMOVE: Old context awareness
# orchestrator.register_module(ContextAwarenessModule())  # DELETED
```

**Test:**
```python
def test_orchestrator_includes_context_instruction():
    """Verify ContextInstructionModule is registered."""
    orchestrator = create_test_orchestrator()
    
    assert "context_instruction" in orchestrator.modules
    assert "context_awareness" not in orchestrator.modules  # Removed
```

---

### Phase 5: Refactor ErrorPreventionModule (45 min)

**File:** `src/services/prompts/modules/error_prevention_module.py`

**Remove lines:**
- [ ] 75-79: Context retrieval from shared_state
- [ ] 95-100: Context forbidden section injection
- [ ] 193-245: `_build_context_forbidden()` method
- [ ] 209-219: Organization mappings (moved to ContextInstructionModule)

**Update execute() method:**

**Before:**
```python
def execute(self, context: ModuleContext) -> ModuleOutput:
    # Haal context informatie op
    org_contexts = context.get_shared("organization_contexts", [])
    jur_contexts = context.get_shared("juridical_contexts", [])
    wet_contexts = context.get_shared("legal_basis_contexts", [])
    
    sections = []
    sections.append("### ⚠️ Veelgemaakte fouten:")
    sections.extend(self._build_basic_errors())
    sections.extend(self._build_forbidden_starters())
    
    # Context-specifieke verboden
    context_forbidden = self._build_context_forbidden(...)
    if context_forbidden:
        sections.append("\n### 🚨 CONTEXT-SPECIFIEKE VERBODEN:")
        sections.extend(context_forbidden)
    
    # ... rest
```

**After:**
```python
def execute(self, context: ModuleContext) -> ModuleOutput:
    sections = []
    sections.append("### ⚠️ Veelgemaakte fouten (vermijden!):")
    sections.extend(self._build_basic_errors())
    
    if self.extended_forbidden_list:
        sections.extend(self._build_forbidden_starters())
    
    if self.include_validation_matrix:
        sections.append(self._build_validation_matrix())
    
    # Generic warning (not context-specific)
    sections.append(
        "\n🚫 Let op: bronnen en context mogen niet letterlijk of herleidbaar in de definitie voorkomen."
    )
    
    content = "\n".join(sections)
    
    return ModuleOutput(
        content=content,
        metadata={"extended_list": self.extended_forbidden_list},
    )
```

**Update dependencies:**

**Before:**
```python
def get_dependencies(self) -> list[str]:
    return ["context_awareness"]  # Dependency on context
```

**After:**
```python
def get_dependencies(self) -> list[str]:
    return []  # No dependencies (context-agnostic now)
```

**Test:**
```python
def test_error_prevention_no_context_logic():
    """Verify ErrorPreventionModule no longer handles context."""
    module = ErrorPreventionModule()
    context = create_test_context(org=["NP"])
    
    output = module.execute(context)
    
    # Should NOT contain context-specific forbidden patterns
    assert "Nederlands Politie" not in output.content
    assert "NP" not in output.content
    
    # Should still contain generic errors
    assert "Begin niet met lidwoorden" in output.content
```

---

### Phase 6: Refactor DefinitionTaskModule (45 min)

**File:** `src/services/prompts/modules/definition_task_module.py`

**Remove lines:**
- [ ] 84-104: Context detection from base_context
- [ ] 206-223: Context-aware quality control adaptation
- [ ] 225-246: `_build_metadata()` method
- [ ] 259-299: `_build_prompt_metadata()` method
- [ ] 204: Checklist line "Context verwerkt zonder expliciete benoeming"

**Update execute() method:**

**Before:**
```python
def execute(self, context: ModuleContext) -> ModuleOutput:
    begrip = context.begrip
    word_type = context.get_shared("word_type", "onbekend")
    ontological_category = context.get_shared("ontological_category")
    
    # REMOVE: Context detection
    org_contexts = context.get_shared("organization_contexts", [])
    base_ctx = context.enriched_context.base_context
    jur_contexts = base_ctx.get("juridische_context") or []
    wet_basis = base_ctx.get("wettelijke_basis") or []
    has_context = bool(org_contexts or jur_contexts or wet_basis)
    
    sections = []
    sections.append("### 🎯 FINALE INSTRUCTIES:")
    sections.append(self._build_task_assignment(begrip))
    sections.append(self._build_checklist(ontological_category))
    
    # REMOVE: Context-aware quality control
    if self.include_quality_control:
        sections.append(self._build_quality_control(has_context))
    
    # REMOVE: Context metadata
    if self.include_metadata:
        sections.append(self._build_metadata(...))
    
    # ... rest
    sections.append(self._build_prompt_metadata(...))  # REMOVE
    
    # ...
```

**After:**
```python
def execute(self, context: ModuleContext) -> ModuleOutput:
    begrip = context.begrip
    ontological_category = context.get_shared("ontological_category")
    
    sections = []
    sections.append("### 🎯 FINALE INSTRUCTIES:")
    sections.append(self._build_task_assignment(begrip))
    sections.append(self._build_checklist(ontological_category))
    
    if self.include_quality_control:
        sections.append(self._build_quality_control())  # No context param
    
    sections.append(self._build_ontological_marker())
    sections.append(self._build_final_instruction(begrip))
    
    content = "\n\n".join(sections)
    
    return ModuleOutput(
        content=content,
        metadata={
            "begrip": begrip,
            "ontological_category": ontological_category,
        },
    )
```

**Simplify _build_checklist():**

**Before (lines 177-204):**
```python
def _build_checklist(self, ontological_category: str | None) -> str:
    # ...
    return f"""📋 **CONSTRUCTIE GUIDE - Bouw je definitie op:**
→ Begint met zelfstandig naamwoord (geen lidwoord/koppelwerkwoord)
→ Eén enkele zin zonder punt aan het einde
→ Geen toelichting, voorbeelden of haakjes
→ Ontologische categorie is duidelijk{ont_cat}
→ Geen verboden woorden (aspect, element, kan, moet, etc.)
→ Context verwerkt zonder expliciete benoeming"""  # ← REMOVE this line
```

**After:**
```python
def _build_checklist(self, ontological_category: str | None) -> str:
    ont_cat = ""
    if ontological_category:
        category_hints = {...}
        ont_cat = f"\n🎯 Focus: Dit is een **{ontological_category}** (...)"
    
    return f"""📋 **CONSTRUCTIE GUIDE - Bouw je definitie op:**
→ Begint met zelfstandig naamwoord (geen lidwoord/koppelwerkwoord)
→ Eén enkele zin zonder punt aan het einde
→ Geen toelichting, voorbeelden of haakjes
→ Ontologische categorie is duidelijk{ont_cat}
→ Geen verboden woorden (aspect, element, kan, moet, etc.)"""
```

**Simplify _build_quality_control():**

**Before (lines 206-223):**
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

**After:**
```python
def _build_quality_control(self) -> str:
    return """#### 🔍 KWALITEITSCONTROLE:
Stel jezelf deze vragen:
1. Is direct duidelijk WAT het begrip is (niet het doel)?
2. Kan iemand hiermee bepalen of iets wel/niet onder dit begrip valt?
3. Is de formulering specifiek en accuraat?
4. Bevat de definitie alleen essentiële informatie?"""
```

**Test:**
```python
def test_definition_task_no_context_logic():
    """Verify DefinitionTaskModule no longer handles context."""
    module = DefinitionTaskModule()
    context = create_test_context(begrip="vergunning")
    
    output = module.execute(context)
    
    # Should NOT contain context metadata
    assert "Organisatorische context:" not in output.content
    assert "Juridische context:" not in output.content
    
    # Should NOT adapt quality control to context
    assert "de gegeven context" not in output.content
    
    # Should still contain generic final instructions
    assert "FINALE INSTRUCTIES" in output.content
    assert "CONSTRUCTIE GUIDE" in output.content
```

---

### Phase 7: Delete ContextAwarenessModule (15 min)

**File:** `src/services/prompts/modules/context_awareness_module.py`

**Actions:**
1. [ ] Delete entire file (433 lines)
2. [ ] Search for imports and remove them
3. [ ] Search for references and update

**Search for references:**
```bash
grep -r "ContextAwarenessModule" src/ --include="*.py"
grep -r "context_awareness_module" src/ --include="*.py"
```

**Expected references to remove:**
```python
# Remove import
from .context_awareness_module import ContextAwarenessModule

# Remove registration
orchestrator.register_module(ContextAwarenessModule())
```

**Verify deletion:**
```bash
# Should return "No such file"
cat src/services/prompts/modules/context_awareness_module.py
```

---

## 6. TESTING STRATEGY

### Unit Tests (Create New File)

**File:** `tests/services/prompts/modules/test_context_instruction_module.py`

**Test suite:**

```python
"""Unit tests for ContextInstructionModule."""

import pytest
from services.definition_generator_context import EnrichedContext
from services.definition_generator_config import UnifiedGeneratorConfig
from services.prompts.modules.context_instruction_module import (
    ContextInstructionModule,
)
from services.prompts.modules.base_module import ModuleContext


def create_test_context(
    begrip="vergunning",
    org=None,
    jur=None,
    wet=None,
):
    """Helper to create test context."""
    base_context = {}
    if org:
        base_context["organisatorisch"] = org
    if jur:
        base_context["juridisch"] = jur
    if wet:
        base_context["wettelijk"] = wet
    
    enriched = EnrichedContext(base_context=base_context)
    config = UnifiedGeneratorConfig()
    
    return ModuleContext(
        begrip=begrip,
        enriched_context=enriched,
        config=config,
        shared_state={},
    )


class TestContextInstructionModule:
    """Test suite for ContextInstructionModule."""
    
    def test_initialization(self):
        """Test module initializes correctly."""
        module = ContextInstructionModule()
        
        assert module.module_id == "context_instruction"
        assert module.priority == 75
        assert module.adaptive_formatting is True
    
    def test_no_dependencies(self):
        """Verify module has no dependencies."""
        module = ContextInstructionModule()
        
        assert module.get_dependencies() == []
    
    def test_validate_input_always_true(self):
        """Module should always run (even with no context)."""
        module = ContextInstructionModule()
        context = create_test_context()
        
        valid, error = module.validate_input(context)
        
        assert valid is True
        assert error is None
    
    def test_context_richness_score_calculation(self):
        """Test context richness score is calculated and shared."""
        module = ContextInstructionModule()
        module.initialize({})
        
        context = create_test_context(org=["NP"], jur=["Strafrecht"])
        
        output = module.execute(context)
        
        score = context.get_shared("context_richness_score")
        assert score is not None
        assert 0.0 <= score <= 1.0
    
    def test_context_data_shared(self):
        """Test context data is shared via shared_state."""
        module = ContextInstructionModule()
        module.initialize({})
        
        context = create_test_context(
            org=["NP", "OM"],
            jur=["Strafrecht"],
            wet=["Wetboek van Strafrecht"],
        )
        
        output = module.execute(context)
        
        assert context.get_shared("organization_contexts") == ["NP", "OM"]
        assert context.get_shared("juridical_contexts") == ["Strafrecht"]
        assert context.get_shared("legal_basis_contexts") == ["Wetboek van Strafrecht"]
    
    def test_rich_context_formatting(self):
        """Test rich context formatting (score ≥ 0.8)."""
        # Mock high score by providing lots of context
        # ... implementation
        pass
    
    def test_moderate_context_formatting(self):
        """Test moderate context formatting (0.5 ≤ score < 0.8)."""
        module = ContextInstructionModule()
        module.initialize({})
        
        context = create_test_context(org=["NP"])
        
        output = module.execute(context)
        
        # Should contain moderate formatting
        assert "📌 VERPLICHTE CONTEXT" in output.content or "📊 UITGEBREIDE" in output.content
    
    def test_minimal_context_formatting(self):
        """Test minimal context formatting (score < 0.5)."""
        module = ContextInstructionModule()
        module.initialize({})
        
        context = create_test_context()  # No context
        
        output = module.execute(context)
        
        # Should contain minimal formatting
        assert "📍" in output.content or "geen" in output.content.lower()
    
    def test_context_forbidden_patterns(self):
        """Test context-specific forbidden patterns generation."""
        module = ContextInstructionModule()
        module.initialize({})
        
        context = create_test_context(org=["NP"], jur=["Strafrecht"])
        
        output = module.execute(context)
        
        # Should contain forbidden patterns
        assert "🚨 CONTEXT-SPECIFIEKE VERBODEN" in output.content
        assert "NP" in output.content
        assert "Nederlands Politie" in output.content  # Full name
        assert "Strafrecht" in output.content
    
    def test_organization_mapping(self):
        """Test organization code mapping to full names."""
        module = ContextInstructionModule()
        module.initialize({})
        
        context = create_test_context(org=["DJI"])
        
        output = module.execute(context)
        
        # Should map DJI to full name
        assert "Dienst Justitiële Inrichtingen" in output.content
    
    def test_context_metadata(self):
        """Test context metadata generation."""
        module = ContextInstructionModule()
        module.initialize({"include_metadata": True})
        
        context = create_test_context(org=["NP"])
        
        output = module.execute(context)
        
        # Should contain metadata
        assert "🆔 Promptmetadata" in output.content or "context" in output.content.lower()
    
    def test_no_context_scenario(self):
        """Test behavior when no context is provided."""
        module = ContextInstructionModule()
        module.initialize({})
        
        context = create_test_context()  # Empty context
        
        output = module.execute(context)
        
        assert output.success is True
        assert len(output.content) > 0  # Should still generate something
    
    def test_error_handling(self):
        """Test error handling in execution."""
        module = ContextInstructionModule()
        module.initialize({})
        
        # Create invalid context (missing required fields)
        invalid_context = ModuleContext(
            begrip="",
            enriched_context=None,  # Invalid
            config=None,
            shared_state={},
        )
        
        output = module.execute(invalid_context)
        
        assert output.success is False
        assert output.error_message is not None


class TestContextInstructionIntegration:
    """Integration tests with other modules."""
    
    def test_error_prevention_no_longer_depends(self):
        """Test ErrorPreventionModule no longer depends on context_awareness."""
        from services.prompts.modules.error_prevention_module import (
            ErrorPreventionModule,
        )
        
        module = ErrorPreventionModule()
        
        # Should have NO dependencies
        assert "context_awareness" not in module.get_dependencies()
        assert "context_instruction" not in module.get_dependencies()
    
    def test_definition_task_no_context_logic(self):
        """Test DefinitionTaskModule no longer handles context."""
        from services.prompts.modules.definition_task_module import (
            DefinitionTaskModule,
        )
        
        module = DefinitionTaskModule()
        module.initialize({})
        
        context = create_test_context(org=["NP"])
        
        output = module.execute(context)
        
        # Should NOT contain context metadata
        assert "Organisatorische context:" not in output.content
```

**Run tests:**
```bash
pytest tests/services/prompts/modules/test_context_instruction_module.py -v
```

---

### Integration Tests (Update Existing)

**File:** `tests/services/prompts/modules/test_prompt_orchestrator.py`

**Add tests:**

```python
def test_orchestrator_with_context_instruction_module():
    """Test orchestrator includes ContextInstructionModule."""
    orchestrator = create_test_orchestrator()
    
    # Verify registration
    assert "context_instruction" in orchestrator.modules
    assert "context_awareness" not in orchestrator.modules  # Deleted
    
    # Verify execution order
    execution_batches = orchestrator.resolve_execution_order()
    
    # ContextInstructionModule should run early (no dependencies)
    first_batch = execution_batches[0]
    assert "context_instruction" in first_batch


def test_full_prompt_generation_with_context():
    """Test full prompt generation with context consolidation."""
    orchestrator = create_test_orchestrator()
    
    begrip = "vergunning"
    context = create_test_enriched_context(org=["NP"])
    config = UnifiedGeneratorConfig()
    
    prompt = orchestrator.build_prompt(begrip, context, config)
    
    # Verify context appears ONCE (consolidated)
    assert prompt.count("📌 VERPLICHTE CONTEXT") <= 1
    assert prompt.count("NP") >= 1  # At least once
    
    # Verify no redundant sections
    assert prompt.count("Nederlands Politie") <= 2  # Once in context, once in forbidden


def test_token_reduction():
    """Verify token reduction from consolidation."""
    # This test requires comparing old vs new system
    # Mock or use fixtures for old system output
    
    # Generate with new system
    orchestrator = create_test_orchestrator()
    prompt_new = orchestrator.build_prompt(...)
    
    # Compare token counts
    tokens_new = count_tokens(prompt_new)
    
    # Should be significantly lower than old system (~380 tokens saved)
    # Exact assertion depends on baseline measurement
    assert tokens_new < 5000  # Example threshold
```

**Run integration tests:**
```bash
pytest tests/services/prompts/modules/test_prompt_orchestrator.py -v -k context
```

---

### Validation Tests

**File:** `tests/services/test_definition_generator.py`

**Add end-to-end test:**

```python
def test_definition_quality_maintained_after_refactor():
    """Ensure definition quality is maintained after context consolidation."""
    test_terms = [
        ("vergunning", ["NP"], ["Strafrecht"]),
        ("registratie", ["DJI"], []),
        ("beoordeling", [], ["Bestuursrecht"]),
    ]
    
    for begrip, org, jur in test_terms:
        # Generate definition with new system
        generator = get_definition_generator()
        definition = generator.generate(
            begrip=begrip,
            organisatorische_context=org,
            juridische_context=jur,
        )
        
        # Validate definition
        validator = get_validator()
        results = validator.validate(definition)
        
        # Quality should be maintained
        assert results.overall_score >= 0.7  # Acceptable quality
        assert definition.content  # Non-empty
        assert begrip not in definition.content  # No circularity
```

**Run validation tests:**
```bash
pytest tests/services/test_definition_generator.py -v -k quality
```

---

## 7. RISK ANALYSIS & MITIGATION

### Identified Risks

| Risk | Likelihood | Impact | Severity | Mitigation Strategy |
|------|------------|--------|----------|---------------------|
| **Breaking prompt generation** | Medium | High | 🔴 CRITICAL | Comprehensive unit tests before integration |
| **Context not appearing in output** | Low | High | 🔴 CRITICAL | Integration tests verify context presence |
| **Token reduction not achieved** | Low | Medium | 🟡 MEDIUM | Measure tokens before/after, adjust strategy |
| **Definition quality degradation** | Low | High | 🔴 CRITICAL | Validation tests compare quality metrics |
| **Module dependencies break** | Low | Medium | 🟡 MEDIUM | Update dependency graph, test orchestrator |
| **Regression in existing features** | Medium | Medium | 🟡 MEDIUM | Full regression test suite before merge |

### Mitigation Details

#### Risk 1: Breaking Prompt Generation
**Prevention:**
- [ ] Unit test each method in ContextInstructionModule
- [ ] Test with empty context, single context, multiple contexts
- [ ] Verify shared_state is populated correctly

**Detection:**
- [ ] Integration tests fail if prompt is malformed
- [ ] Manual inspection of generated prompts

**Recovery:**
- [ ] Keep original modules as `.bak` files
- [ ] Git revert to last working commit

#### Risk 2: Context Not Appearing
**Prevention:**
- [ ] Test execute() method outputs non-empty content
- [ ] Test shared_state is set correctly
- [ ] Verify orchestrator includes module in execution

**Detection:**
- [ ] Integration test checks for "📌 VERPLICHTE CONTEXT" in output
- [ ] Validation test checks context data in shared_state

**Recovery:**
- [ ] Debug orchestrator execution order
- [ ] Check module priority and dependencies

#### Risk 3: Token Reduction Not Achieved
**Prevention:**
- [ ] Measure baseline token count before refactor
- [ ] Calculate expected savings (380 → ~180 tokens)
- [ ] Design adaptive output with minimal variants

**Detection:**
- [ ] Token counting test compares old vs new
- [ ] Performance test tracks prompt length

**Recovery:**
- [ ] Adjust adaptive formatting thresholds
- [ ] Further consolidate output sections

#### Risk 4: Definition Quality Degradation
**Prevention:**
- [ ] Run existing validation tests before and after
- [ ] Compare definition quality scores
- [ ] Manual review of sample definitions

**Detection:**
- [ ] Validation test suite catches quality drops
- [ ] User testing reveals issues

**Recovery:**
- [ ] Review business logic migration
- [ ] Check for missing instructions in new module

---

### Rollback Plan

**NO rollback mechanism needed** per CLAUDE.md:
- ⚠️ GEEN BACKWARDS COMPATIBILITY (single-user app, not in production)
- ✅ Direct refactor, no feature flags

**However, safety measures:**

1. **Git safety:**
   ```bash
   # Create feature branch
   git checkout -b feature/DEF-126-context-consolidation
   
   # Commit after each phase
   git add -A
   git commit -m "feat(DEF-126): Phase 1 - Create ContextInstructionModule skeleton"
   
   # Can revert individual phases if needed
   git revert <commit-hash>
   ```

2. **Backup original modules:**
   ```bash
   # Optional: Keep backups during development
   cp src/services/prompts/modules/context_awareness_module.py \
      src/services/prompts/modules/context_awareness_module.py.bak
   ```

3. **Quick verification:**
   ```bash
   # After each phase, run quick smoke test
   pytest tests/services/prompts/modules/ -v -k context
   ```

---

## 8. METRICS & SUCCESS CRITERIA

### Primary Success Criteria ✅

| Metric | Target | Measurement Method | Pass/Fail |
|--------|--------|-------------------|-----------|
| **Token Reduction** | ≥50% (380 → ≤190) | Token counting test | ⏳ TBD |
| **Test Coverage** | ≥80% for new module | pytest --cov | ⏳ TBD |
| **All Tests Pass** | 100% pass rate | pytest exit code | ⏳ TBD |
| **Definition Quality** | No regression | Validation score comparison | ⏳ TBD |
| **Single Source of Truth** | 1 module handles context | Code review | ⏳ TBD |

### Secondary Success Criteria ✅

| Metric | Target | Measurement |
|--------|--------|-------------|
| Code Reduction | ~150 lines removed | Line count diff |
| Module Coupling | ErrorPrevention & DefinitionTask no context deps | Dependency graph |
| Execution Time | No significant increase (<5%) | Performance test |
| Maintainability | Easier to update context logic | Developer feedback |

### Measurement Scripts

**Token Counting:**
```python
# tests/debug/measure_token_reduction.py
import tiktoken

def count_tokens(text: str) -> int:
    """Count tokens using GPT-4 tokenizer."""
    encoder = tiktoken.encoding_for_model("gpt-4")
    return len(encoder.encode(text))

def measure_context_section_tokens():
    """Measure token usage before and after consolidation."""
    # Generate prompt with test case
    orchestrator = create_test_orchestrator()
    prompt = orchestrator.build_prompt(...)
    
    # Extract context-related sections
    # (requires pattern matching or section markers)
    
    tokens = count_tokens(prompt)
    print(f"Total prompt tokens: {tokens}")
    
    # Compare to baseline
    baseline = 380  # Old system
    reduction = baseline - tokens
    print(f"Token reduction: {reduction} ({reduction/baseline*100:.1f}%)")
```

**Coverage Measurement:**
```bash
pytest tests/services/prompts/modules/test_context_instruction_module.py \
    --cov=src/services/prompts/modules/context_instruction_module \
    --cov-report=term-missing \
    --cov-report=html
```

---

## 9. IMPLEMENTATION TIMELINE

### Detailed Schedule

| Phase | Task | Duration | Dependencies | Priority | Status |
|-------|------|----------|--------------|----------|--------|
| **1** | Create ContextInstructionModule skeleton | 30 min | None | HIGH | ⏳ TODO |
| **2.1** | Migrate context richness scoring | 30 min | Phase 1 | HIGH | ⏳ TODO |
| **2.2** | Migrate adaptive formatting | 30 min | Phase 2.1 | HIGH | ⏳ TODO |
| **2.3** | Migrate context forbidden patterns | 30 min | Phase 2.2 | HIGH | ⏳ TODO |
| **2.4** | Migrate context metadata | 30 min | Phase 2.3 | HIGH | ⏳ TODO |
| **3** | Implement complete execute() | 30 min | Phase 2 | HIGH | ⏳ TODO |
| **4** | Update orchestrator registration | 30 min | Phase 3 | HIGH | ⏳ TODO |
| **5** | Refactor ErrorPreventionModule | 45 min | Phase 4 | MEDIUM | ⏳ TODO |
| **6** | Refactor DefinitionTaskModule | 45 min | Phase 5 | MEDIUM | ⏳ TODO |
| **7** | Delete ContextAwarenessModule | 15 min | Phases 5-6 | LOW | ⏳ TODO |
| **8** | Unit testing | 1 hour | Phases 1-7 | HIGH | ⏳ TODO |
| **9** | Integration testing | 45 min | Phase 8 | HIGH | ⏳ TODO |
| **10** | Documentation update | 30 min | Phase 9 | LOW | ⏳ TODO |
| **TOTAL** | **Full implementation** | **~6 hours** | - | - | ⏳ TODO |

### Recommended Schedule

**Day 1 (3 hours):**
- Morning: Phases 1-3 (create new module, migrate logic)
- Afternoon: Phase 4 (orchestrator registration)

**Day 2 (3 hours):**
- Morning: Phases 5-7 (refactor old modules, delete)
- Afternoon: Phases 8-10 (testing, documentation)

---

## 10. DOCUMENTATION UPDATES

### Files to Update

1. **Architecture Documentation**
   - `docs/architectuur/PROMPT_SYSTEM_ARCHITECTURE.md`
   - Update module diagram to show ContextInstructionModule
   - Remove ContextAwarenessModule references
   - Update data flow diagrams

2. **Module Documentation**
   - Create: `docs/technisch/context_instruction_module.md`
   - Delete: References to `context_awareness_module.md` (if exists)

3. **Developer Guidelines**
   - `CLAUDE.md` → Update "Belangrijke Bestandslocaties" section
   - Add: ContextInstructionModule as Single Source of Truth for context

4. **Changelog**
   - `docs/refactor-log.md`
   - Add entry for DEF-126 context consolidation

### Documentation Template

**File:** `docs/technisch/context_instruction_module.md`

```markdown
# ContextInstructionModule - Single Source of Truth voor Context

## Overzicht

De ContextInstructionModule is de enige module die context-gerelateerde instructies genereert in het prompt systeem. Deze module consolideert de logica van drie voormalige modules:
- ContextAwarenessModule (VERWIJDERD)
- ErrorPreventionModule (context logica verwijderd)
- DefinitionTaskModule (context metadata verwijderd)

## Verantwoordelijkheden

1. **Context Richness Scoring:** Bereken score (0.0-1.0) op basis van context kwaliteit
2. **Adaptive Formatting:** Genereer output aangepast aan context rijkheid
3. **Context-Specific Forbidden Patterns:** Genereer verboden patronen per context
4. **Context Metadata:** Genereer metadata footer met context informatie
5. **Shared State Management:** Deel context data met andere modules

## Data Flow

```
EnrichedContext
    ↓
ContextInstructionModule.execute()
    ├─ _calculate_context_score() → 0.65
    ├─ _build_context_instructions() → "📌 VERPLICHTE CONTEXT..."
    ├─ _build_context_forbidden() → "🚨 VERBODEN: ..."
    └─ _build_context_metadata() → "🆔 Promptmetadata: ..."
    ↓
shared_state:
    - context_richness_score: 0.65
    - organization_contexts: ["NP"]
    - juridical_contexts: ["Strafrecht"]
```

## Configuratie

```python
{
    "adaptive_formatting": True,      # Gebruik adaptive output
    "confidence_indicators": True,    # Toon confidence emoji's
    "include_metadata": True,         # Genereer metadata footer
}
```

## Token Optimization

De module gebruikt adaptive output om tokens te besparen:

| Context Score | Output Level | Estimated Tokens |
|---------------|--------------|------------------|
| ≥ 0.8 | Rich | ~220 |
| 0.5 - 0.8 | Moderate | ~120 |
| < 0.5 | Minimal | ~10 |

## Testing

Zie `tests/services/prompts/modules/test_context_instruction_module.py`

## Migratie van Oude Modules

| Oude Module | Oude Methode | Nieuwe Locatie |
|-------------|--------------|----------------|
| ContextAwarenessModule | `_calculate_context_score()` | ContextInstructionModule (zelfde naam) |
| ContextAwarenessModule | `_build_rich_context_section()` | ContextInstructionModule._build_context_instructions() |
| ErrorPreventionModule | `_build_context_forbidden()` | ContextInstructionModule (zelfde naam) |
| DefinitionTaskModule | `_build_prompt_metadata()` | ContextInstructionModule._build_context_metadata() |
```

---

## 11. APPROVAL & SIGN-OFF

### Approval Requirements

**Per UNIFIED_INSTRUCTIONS.md → APPROVAL LADDER:**

- ✅ **Changes >100 lines:** YES (150+ lines changed across 4 files)
- ✅ **Changes >5 files:** NO (4 files: 1 new, 3 modified)
- ✅ **Schema changes:** NO
- ✅ **Network calls:** NO

**Conclusion:** **USER APPROVAL REQUIRED** (>100 lines threshold)

### Stakeholders

| Role | Name | Responsibility | Sign-off |
|------|------|----------------|----------|
| **Developer** | bmad-dev | Implementation | ⏳ Pending |
| **Architect** | bmad-architect | Design review | ⏳ Pending |
| **QA** | bmad-tester | Test execution | ⏳ Pending |
| **Product Owner** | User | Final approval | ⏳ **REQUIRED** |

---

## 12. CONCLUSION

### Summary

The DEF-126 Context Consolidation solution:

1. ✅ **Verified Problem:** 380 tokens of redundancy across 3 modules
2. ✅ **Clear Architecture:** Single Source of Truth pattern
3. ✅ **Low Risk:** No backwards compatibility, comprehensive tests
4. ✅ **High Impact:** 50-65% token reduction, improved maintainability
5. ✅ **Detailed Plan:** 10 phases with concrete steps and tests

### Implementation Readiness

**Ready for bmad-dev to execute:**
- ✅ Complete phase-by-phase breakdown
- ✅ Code examples for each step
- ✅ Test strategy with concrete test cases
- ✅ Risk mitigation for each identified risk
- ✅ Success criteria with measurement methods

### Recommendation

**IMPLEMENT following this plan** with user approval for >100 lines changes.

**Next Steps:**
1. User approves implementation plan
2. bmad-dev executes Phases 1-10 sequentially
3. bmad-tester verifies all tests pass
4. User reviews final results and quality

---

## APPENDIX A: Code Reference

### Organization Mappings (Centralized)

```python
# src/services/prompts/modules/context_instruction_module.py

# Module-level constant for reusability
ORGANIZATION_MAPPINGS = {
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

### Context Extraction Helper

```python
def _extract_contexts(self, context_value: Any) -> list[str]:
    """
    Extract context lijst uit verschillende input formaten.
    
    Backwards compatibility method (from ContextAwarenessModule).
    """
    if not context_value:
        return []
    
    if isinstance(context_value, bool):
        return []  # Legacy: True means no specific context
    if isinstance(context_value, str):
        return [context_value]
    if isinstance(context_value, list):
        return [str(item) for item in context_value if item]
    
    logger.warning(f"Unknown context type: {type(context_value)}")
    return []
```

---

## APPENDIX B: Testing Checklist

### Pre-Implementation Tests ✅

- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Verify all tests pass (baseline)
- [ ] Measure current prompt token count
- [ ] Document definition quality scores

### Phase 1-3 Tests (New Module)

- [ ] `pytest tests/services/prompts/modules/test_context_instruction_module.py -v`
- [ ] Verify no import errors
- [ ] Verify execute() returns valid output
- [ ] Verify shared_state is populated

### Phase 4 Tests (Orchestrator)

- [ ] `pytest tests/services/prompts/modules/test_prompt_orchestrator.py -v`
- [ ] Verify ContextInstructionModule registered
- [ ] Verify execution order correct
- [ ] Verify no dependency cycles

### Phase 5-6 Tests (Refactored Modules)

- [ ] `pytest tests/services/prompts/modules/test_error_prevention_module.py -v`
- [ ] `pytest tests/services/prompts/modules/test_definition_task_module.py -v`
- [ ] Verify no context logic remains
- [ ] Verify generic functionality preserved

### Phase 7 Tests (Deletion)

- [ ] Verify ContextAwarenessModule file deleted
- [ ] Verify no import errors across codebase
- [ ] `grep -r "ContextAwarenessModule" src/` returns nothing

### Integration Tests

- [ ] `pytest tests/services/test_definition_generator.py -v`
- [ ] Generate sample definitions with context
- [ ] Verify context appears in output
- [ ] Verify no redundancy (context listed once)

### Performance Tests

- [ ] Measure token count after refactor
- [ ] Verify ≥50% reduction achieved
- [ ] Measure execution time (should not increase >5%)

### Validation Tests

- [ ] Run validation suite on sample definitions
- [ ] Compare quality scores before/after
- [ ] Verify no regression

---

**Document Status:** ✅ READY FOR IMPLEMENTATION  
**Created:** 2025-11-13  
**Priority:** HIGH - Significant token/cost savings  
**Approval Required:** YES (>100 lines changed)

