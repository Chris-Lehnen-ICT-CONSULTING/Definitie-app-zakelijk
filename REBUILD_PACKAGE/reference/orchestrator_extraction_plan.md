---
id: EPIC-026-ORCHESTRATOR-EXTRACTION-PLAN
epic: EPIC-026
phase: 1
created: 2025-10-02
owner: code-architect
status: draft
---

# Orchestrator Extraction Plan (EPIC-026)

**Analysis Date:** 2025-10-02
**Focus:** Hidden orchestrators in UI layer
**Complexity:** VERY HIGH (9/10)

---

## Executive Summary

### Critical Discovery

Two MAJOR orchestrators are hidden in the UI layer, masquerading as presentation code:

1. **Regeneration Orchestrator** in `definition_generator_tab.py` (~500 LOC)
   - Orchestrates definition regeneration workflow
   - Category change workflow coordination
   - Multi-service coordination (4+ services)
   - Direct service instantiation and async execution

2. **Generation Orchestrator** in `tabbed_interface.py` (~380 LOC god method)
   - `_handle_definition_generation()` method
   - Orchestrates 5+ services in a single method
   - Complex async/sync mixing
   - Extensive state management (15+ session state mutations)
   - Duplicate check workflow
   - Document processing integration

### Strategic Recommendation

**EXTRACT ORCHESTRATORS FIRST, BEFORE UI SPLITTING!**

**Rationale:**
1. Orchestrators contain the CORE business logic
2. UI refactoring without orchestrator extraction = moving god objects around
3. Orchestrators have clear service boundaries once extracted
4. Reduces UI complexity IMMEDIATELY (from 2,525 + 1,793 = 4,318 LOC to ~500 LOC)
5. Enables proper testing of business logic separate from UI

---

## Part 1: Orchestrator Characterization

### 1.1 Regeneration Orchestrator (definition_generator_tab.py)

**Location:** Lines 2008-2370 (~500 LOC across 8 methods)

**What It Does:**
- Coordinates definition regeneration when category changes
- Manages regeneration context (old category → new category)
- Analyzes category change impact
- Executes direct regeneration or prepares manual regeneration
- Compares old vs new definitions
- Handles navigation to generator tab with pre-filled state

**Service Dependencies (4):**
```python
- RegenerationService        # Set/get regeneration context
- CategoryService            # Category display names, validation
- DefinitionService          # Generate new definition (via dynamic import)
- WorkflowService            # Category change impact analysis
```

**State Management:**
```python
# SessionStateManager mutations (7 keys):
- "regeneration_active": bool
- "regeneration_begrip": str
- "regeneration_category": str
- "editing_definition_id": int
- "edit_*_context": lists (3 keys)
```

**Async Patterns:**
```python
# Uses run_async() bridge for:
- definition_service.generate_definition()
# Progress bar updates during async execution
```

**Business Logic:**
- Category change impact analysis (hardcoded rules):
  - proces → type: "Focus shifts from 'how' to 'what'"
  - type → proces: "Focus shifts from 'what' to 'how'"
  - resultaat: "Outcome-oriented wording"
  - exemplaar: "Specificity level changes"
- Context extraction from generation_result dict
- Definition comparison formatting
- Regeneration preview UI coordination

**Complexity Factors:**
- **Workflow Orchestration:** 3-path decision (direct/manual/keep)
- **Async Execution:** run_async() bridge with progress tracking
- **Context Juggling:** Extract from result → combine with UI → pass to service
- **Navigation Logic:** Tab switching with state preparation
- **Error Handling:** Try/except with fallback to UI error display

**Why VERY HIGH Complexity (9/10):**
- Orchestrates 4 services + dynamic imports
- Mixed async/sync execution
- Complex state mutation sequence (7 session keys)
- Hardcoded business rules (not data-driven)
- UI/business logic tightly coupled
- Navigation side effects

---

### 1.2 Generation Orchestrator (tabbed_interface.py)

**Location:** Lines 821-1200 (~380 LOC in SINGLE method!)

**What It Does:**
- Validates minimum context requirement (1 of org/jur/wet)
- Determines ontological category (async 6-step protocol + fallbacks)
- Checks for duplicates (with user choice workflow)
- Integrates document context (upload → process → extract snippets)
- Handles regeneration context (category override)
- Orchestrates definition generation
- Stores results in session state
- Prepares edit tab state
- Cleans up regeneration context
- Shows success message

**Service Dependencies (5+):**
```python
- get_definition_service()       # Main generation
- RegenerationService            # Get/clear regeneration context
- get_document_processor()       # Document processing
- DefinitieChecker               # Duplicate check
- OntologischeAnalyzer           # Category determination (async)
# Plus: SessionStateManager (pervasive)
```

**State Management:**
```python
# SessionStateManager mutations (15+ keys):
- "generation_options": dict (force flags)
- "last_check_result": CheckResult
- "selected_definition": DefinitieRecord
- "last_generation_result": dict
- "selected_documents": list[str]
- "editing_definition_id": int
- "edit_*_context": lists (3 keys)
- "ufo_categorie": str
- Plus debug flags and temporary state
```

**Async Patterns:**
```python
# Async operations:
1. asyncio.run(_determine_ontological_category())
2. run_async(definition_service.generate_definition())
# Sync wrapper for async context mixing
```

**Business Logic:**
1. **Context Validation:**
   ```python
   # Min 1 required: org OR jur OR wet
   if not (org_context or jur_context or wet_context):
       raise ValidationError
   ```

2. **Duplicate Check Workflow:**
   ```python
   if not is_forced:
       check_result = checker.check_before_generation()
       if check_result.action != PROCEED:
           # STOP and show UI choice:
           # [Toon bestaande] [Genereer nieuwe]
           return  # Exit early!
   ```

3. **Category Determination (3-layer fallback):**
   ```python
   # Layer 1: Async 6-step ontological analysis
   # Layer 2: Quick ontological analyzer (faster)
   # Layer 3: Pattern matching (legacy fallback)
   ```

4. **Document Context Integration:**
   ```python
   # If documents selected:
   doc_summary = _build_document_context_summary()
   doc_snippets = _build_document_snippets(
       max_snippets=len(doc_ids) * 4,
       window_chars=280
   )
   ```

5. **Regeneration Context Override:**
   ```python
   regeneration_ctx = service.get_active_context()
   if regeneration_ctx:
       auto_categorie = regeneration_ctx.new_category
       category_reasoning = "Regeneratie: aangepast..."
   ```

**Complexity Factors:**
- **God Method:** 380 LOC in SINGLE method
- **Orchestration Depth:** 5+ service calls sequentially
- **Control Flow:** 6 early returns, 3 nested conditionals
- **Async/Sync Mixing:** 2 async bridges in sync method
- **State Mutations:** 15+ session state writes
- **Error Handling:** 8+ try/except blocks
- **Side Effects:** DB writes, navigation prep, context cleanup

**Why CRITICAL Complexity (10/10):**
- Largest god method in entire codebase
- Violates EVERY SOLID principle
- Impossible to test in isolation
- Contains 5+ distinct responsibilities
- Complex state machine (duplicate check → regeneration override → generation → result storage)
- Breaking this breaks the entire app

---

## Part 2: Extraction Strategy

### 2.1 Strategic Decision: Extract Orchestrators FIRST

**Option A: Extract Orchestrators FIRST** ✅ RECOMMENDED
```
Phase 1: Extract orchestrators to services (3 weeks)
Phase 2: Thin UI layer (1 week)
Phase 3: Split UI components (2 weeks)
```

**Option B: Extract UI components FIRST** ❌ NOT RECOMMENDED
```
Phase 1: Split UI components (2 weeks)
Phase 2: Extract orchestrators from split components (4 weeks)
Phase 3: Thin UI layer (1 week)
```

**Why Option A (Orchestrators First)?**

1. **Preserves Business Logic Integrity**
   - Orchestrators contain core workflows
   - Extracting them as coherent units preserves business logic
   - Splitting UI first scatters orchestration logic

2. **Reduces Risk**
   - Orchestrators have clear inputs/outputs once extracted
   - Testing orchestrators in isolation is easier than testing UI
   - Rollback is easier with service boundaries

3. **Immediate Complexity Reduction**
   - tabbed_interface.py: 1,793 LOC → ~400 LOC (78% reduction!)
   - definition_generator_tab.py: 2,525 LOC → ~800 LOC (68% reduction!)
   - Total reduction: ~2,600 LOC moved to services

4. **Enables Parallel Work**
   - Once orchestrators extracted, UI refactoring can happen independently
   - Services can be optimized without UI changes
   - Multiple developers can work in parallel

5. **Better Architecture**
   - Services layer becomes the source of truth
   - UI becomes thin presentation layer
   - Clear separation of concerns

---

### 2.2 New Service Architecture Design

```
┌─────────────────────────────────────────────────────────┐
│ UI Layer (THIN - Presentation Only)                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  tabbed_interface.py (~400 LOC)                         │
│  ├── Tab routing logic                                  │
│  ├── Header/Footer rendering                            │
│  └── Delegates to orchestrators                         │
│                                                          │
│  definition_generator_tab.py (~800 LOC)                 │
│  ├── Results rendering                                  │
│  ├── Validation display                                 │
│  └── Delegates to orchestrators                         │
│                                                          │
└─────────────────────────────────────────────────────────┘
                          ↓ delegates to
┌─────────────────────────────────────────────────────────┐
│ Orchestration Layer (NEW)                               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  DefinitionGenerationOrchestrator (~500 LOC) **NEW**    │
│  ├── Context validation                                 │
│  ├── Category determination (delegates)                 │
│  ├── Duplicate check workflow                           │
│  ├── Document integration                               │
│  ├── Regeneration handling                              │
│  ├── Service coordination                               │
│  └── Result preparation                                 │
│                                                          │
│  RegenerationOrchestrator (~600 LOC) **NEW**            │
│  ├── Category change impact analysis                    │
│  ├── Regeneration workflow (3 paths)                    │
│  ├── Context extraction & preparation                   │
│  ├── Definition comparison                              │
│  └── Navigation coordination                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
                          ↓ uses
┌─────────────────────────────────────────────────────────┐
│ Service Layer (EXISTING + NEW)                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  UnifiedDefinitionGenerator (existing)                  │
│  ValidationOrchestratorV2 (existing)                    │
│  RegenerationService (existing)                         │
│  DocumentProcessor (existing)                           │
│  DefinitieChecker (existing)                            │
│                                                          │
│  OntologicalCategoryService (~300 LOC) **NEW**          │
│  ├── 6-step protocol                                    │
│  ├── Quick analysis                                     │
│  ├── Pattern matching (from config)                     │
│  └── Score calculation                                  │
│                                                          │
│  DocumentContextService (~350 LOC) **NEW**              │
│  ├── Context aggregation                                │
│  ├── Snippet extraction                                 │
│  └── Citation formatting                                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

### 2.3 Interface Contracts

#### 2.3.1 DefinitionGenerationOrchestrator

```python
from dataclasses import dataclass
from typing import Optional
from domain.ontological_categories import OntologischeCategorie

@dataclass
class GenerationRequest:
    """Input for generation orchestration."""
    begrip: str
    organisatorische_context: list[str]
    juridische_context: list[str]
    wettelijke_basis: list[str]
    selected_document_ids: list[str] = None
    ufo_categorie: Optional[str] = None
    force_generate: bool = False
    force_duplicate: bool = False

@dataclass
class GenerationResult:
    """Output from generation orchestration."""
    success: bool
    definitie: str
    definitie_gecorrigeerd: Optional[str]
    validation_result: dict
    ontological_category: OntologischeCategorie
    category_reasoning: str
    category_scores: dict[str, int]
    saved_definition_id: Optional[int]
    voorbeelden: dict
    document_context: Optional[dict]
    error: Optional[str] = None
    duplicate_check_result: Optional[CheckResult] = None

class DefinitionGenerationOrchestrator:
    """Orchestrates complete definition generation workflow."""

    def __init__(
        self,
        definition_service: UnifiedDefinitionGenerator,
        regeneration_service: RegenerationService,
        document_service: DocumentContextService,
        category_service: OntologicalCategoryService,
        checker: DefinitieChecker,
    ):
        self.definition_service = definition_service
        self.regeneration_service = regeneration_service
        self.document_service = document_service
        self.category_service = category_service
        self.checker = checker

    async def orchestrate_generation(
        self,
        request: GenerationRequest,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> GenerationResult:
        """
        Orchestrate complete generation workflow:
        1. Validate context
        2. Determine category
        3. Check duplicates
        4. Process documents
        5. Handle regeneration override
        6. Generate definition
        7. Prepare result

        Args:
            request: Generation request with all inputs
            progress_callback: Optional callback for UI progress (message, percentage)

        Returns:
            GenerationResult with all outputs or error
        """
        pass
```

#### 2.3.2 RegenerationOrchestrator

```python
@dataclass
class RegenerationRequest:
    """Input for regeneration orchestration."""
    begrip: str
    current_definition_id: int
    old_category: str
    new_category: str
    regeneration_mode: str  # "direct" | "manual" | "keep"
    generation_result: dict  # Original generation context

@dataclass
class RegenerationResult:
    """Output from regeneration orchestration."""
    success: bool
    mode: str  # "direct" | "manual" | "keep"
    new_definition: Optional[str] = None
    new_definition_id: Optional[int] = None
    impact_analysis: list[str] = None
    comparison: Optional[dict] = None  # old vs new
    navigation_state: Optional[dict] = None  # For manual mode
    error: Optional[str] = None

class RegenerationOrchestrator:
    """Orchestrates definition regeneration workflow."""

    def __init__(
        self,
        regeneration_service: RegenerationService,
        category_service: CategoryService,
        definition_service: UnifiedDefinitionGenerator,
        workflow_service: WorkflowService,
    ):
        self.regeneration_service = regeneration_service
        self.category_service = category_service
        self.definition_service = definition_service
        self.workflow_service = workflow_service

    def analyze_category_change_impact(
        self,
        old_category: str,
        new_category: str
    ) -> list[str]:
        """Analyze impact of category change."""
        pass

    async def orchestrate_regeneration(
        self,
        request: RegenerationRequest,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> RegenerationResult:
        """
        Orchestrate regeneration workflow:
        1. Analyze impact
        2. Set regeneration context
        3. If direct: execute generation
        4. If manual: prepare navigation state
        5. If keep: update category only
        6. Return result with appropriate data

        Args:
            request: Regeneration request
            progress_callback: Optional UI progress callback

        Returns:
            RegenerationResult with outcome
        """
        pass
```

#### 2.3.3 OntologicalCategoryService

```python
@dataclass
class CategoryDeterminationResult:
    """Result of category determination."""
    category: OntologischeCategorie
    reasoning: str
    scores: dict[str, int]
    method: str  # "6-step" | "quick" | "pattern"
    confidence: float

class OntologicalCategoryService:
    """Determines ontological category using multi-layer fallback."""

    def __init__(
        self,
        analyzer: OntologischeAnalyzer,
        quick_analyzer: QuickOntologischeAnalyzer,
        pattern_config: dict,  # From config/data
    ):
        self.analyzer = analyzer
        self.quick_analyzer = quick_analyzer
        self.patterns = pattern_config

    async def determine_category(
        self,
        begrip: str,
        org_context: str,
        jur_context: str,
    ) -> CategoryDeterminationResult:
        """
        Determine category using 3-layer fallback:
        1. Try 6-step ontological analysis (async)
        2. Fallback to quick analyzer
        3. Ultra-fallback to pattern matching

        Returns:
            CategoryDeterminationResult with category and metadata
        """
        pass
```

#### 2.3.4 DocumentContextService

```python
@dataclass
class DocumentContext:
    """Aggregated document context."""
    summary: str
    snippets: list[dict]  # [{text, doc_id, citation}, ...]
    document_count: int
    keywords: list[str]
    concepts: list[str]
    legal_refs: list[str]

class DocumentContextService:
    """Handles document context aggregation and snippet extraction."""

    def __init__(self, document_processor):
        self.processor = document_processor

    def build_context_summary(
        self,
        selected_doc_ids: list[str]
    ) -> DocumentContext:
        """Build aggregated context from selected documents."""
        pass

    def extract_snippets(
        self,
        begrip: str,
        selected_doc_ids: list[str],
        max_snippets_total: int = 8,
        per_doc_max: int = 4,
        window_chars: int = 280,
    ) -> list[dict]:
        """Extract snippets with citations."""
        pass
```

---

## Part 3: Step-by-Step Extraction Plan

### Phase 0: Preparation (Week 1)

#### 3.1 Step 0.1: Create Integration Tests (3 days)
**Goal:** Capture current behavior before any changes

**Tasks:**
1. Test full generation flow end-to-end
   ```python
   def test_generation_flow_complete():
       # Test: begrip + context → generation result
       # Assert: all session state correctly populated
       # Assert: saved to DB with correct ID
   ```

2. Test duplicate check workflow
   ```python
   def test_duplicate_check_stops_generation():
       # Test: existing definitie → shows choice UI
       # Test: force_generate flag → proceeds anyway
   ```

3. Test regeneration workflow
   ```python
   def test_category_change_regeneration():
       # Test: category change → regeneration triggered
       # Test: impact analysis correct
       # Test: new definition generated with correct category
   ```

4. Test document integration
   ```python
   def test_document_context_integration():
       # Test: uploaded docs → snippets extracted
       # Test: context aggregated correctly
   ```

**Success Criteria:**
- [ ] 10+ integration tests covering all workflows
- [ ] All tests GREEN with current code
- [ ] Tests can detect regressions

---

#### 3.2 Step 0.2: Extract Hardcoded Patterns to Config (2 days)

**Goal:** Make category patterns data-driven

**Tasks:**
1. Create `config/ontological_patterns.yaml`:
   ```yaml
   patterns:
     proces:
       indicators:
         - atie
         - eren
         - ing
         - verificatie
         - validatie
       description: "Focus op 'hoe' - procedureel"

     type:
       indicators:
         - bewijs
         - document
         - middel
         - systeem
       description: "Focus op 'wat' - beschrijvend"

     # ... etc
   ```

2. Replace hardcoded dicts in 3 places:
   - `_generate_category_reasoning()` in definition_generator_tab.py
   - `_get_category_scores()` in tabbed_interface.py
   - `_legacy_pattern_matching()` in tabbed_interface.py

3. Create `OntologicalPatternConfig` loader

**Success Criteria:**
- [ ] All patterns in config file
- [ ] No hardcoded pattern dicts in code
- [ ] Tests still GREEN

---

#### 3.3 Step 0.3: Document State Contracts (2 days)

**Goal:** Explicit contracts for session state

**Tasks:**
1. Create `docs/backlog/EPIC-026/session_state_schema.md`:
   ```markdown
   ## Generation Flow State
   - last_generation_result: dict (schema...)
   - generation_options: dict (force flags)
   - editing_definition_id: int | None

   ## Regeneration Flow State
   - regeneration_active: bool
   - regeneration_begrip: str
   - regeneration_category: str

   ## Document Flow State
   - selected_documents: list[str]
   - documents_updated: bool
   ```

2. Create `GenerationStateManager` wrapper:
   ```python
   class GenerationStateManager:
       """Type-safe wrapper for generation state."""

       @staticmethod
       def get_generation_result() -> Optional[dict]:
           return SessionStateManager.get_value("last_generation_result")

       @staticmethod
       def set_generation_result(result: dict):
           # Validate schema
           SessionStateManager.set_value("last_generation_result", result)
   ```

**Success Criteria:**
- [ ] All state contracts documented
- [ ] Type-safe wrappers created
- [ ] Tests still GREEN

---

### Phase 1: Extract OntologicalCategoryService (Week 2)

#### 3.4 Step 1.1: Create Service Skeleton (1 day)

**Tasks:**
1. Create `src/services/ontological_category_service.py`
2. Implement interface from 2.3.3
3. Move pattern loading from config
4. Create unit tests

**Code Structure:**
```python
# src/services/ontological_category_service.py

class OntologicalCategoryService:
    def __init__(self, analyzer, quick_analyzer, pattern_config):
        self.analyzer = analyzer
        self.quick_analyzer = quick_analyzer
        self.patterns = pattern_config

    async def determine_category(
        self, begrip: str, org_context: str, jur_context: str
    ) -> CategoryDeterminationResult:
        # Layer 1: Try 6-step async analysis
        try:
            result = await self.analyzer.analyze(begrip, org_context, jur_context)
            if result.confidence > 0.8:
                return CategoryDeterminationResult(
                    category=result.category,
                    reasoning=result.reasoning,
                    scores=result.scores,
                    method="6-step",
                    confidence=result.confidence,
                )
        except Exception as e:
            logger.warning(f"6-step analysis failed: {e}")

        # Layer 2: Quick analyzer fallback
        # Layer 3: Pattern matching ultra-fallback
        # ...
```

**Success Criteria:**
- [ ] Service class created
- [ ] Unit tests GREEN (mock analyzers)
- [ ] Pattern config loaded

---

#### 3.5 Step 1.2: Integrate into tabbed_interface (2 days)

**Tasks:**
1. Inject `OntologicalCategoryService` in `__init__`
2. Replace `_determine_ontological_category()` with service call
3. Remove `_legacy_pattern_matching()`, `_get_category_scores()`, `_generate_category_reasoning()`
4. Update integration tests

**Before:**
```python
# tabbed_interface.py (260 LOC of category logic)
auto_categorie, reasoning, scores = asyncio.run(
    self._determine_ontological_category(begrip, org, jur)
)
```

**After:**
```python
# tabbed_interface.py (~10 LOC delegation)
category_result = await self.category_service.determine_category(
    begrip, org, jur
)
auto_categorie = category_result.category
reasoning = category_result.reasoning
scores = category_result.scores
```

**Success Criteria:**
- [ ] Integration tests still GREEN
- [ ] 250 LOC removed from tabbed_interface.py
- [ ] Service unit tests cover all patterns

---

### Phase 2: Extract DocumentContextService (Week 3)

#### 3.6 Step 2.1: Create Service (2 days)

**Tasks:**
1. Create `src/services/document_context_service.py`
2. Move `_build_document_context_summary()` from tabbed_interface
3. Move `_build_document_snippets()` from tabbed_interface
4. Create unit tests with mock documents

**Success Criteria:**
- [ ] Service created with interface from 2.3.4
- [ ] Unit tests GREEN

---

#### 3.7 Step 2.2: Integrate (2 days)

**Tasks:**
1. Inject service in `__init__`
2. Replace methods with service calls
3. Update integration tests

**Success Criteria:**
- [ ] 350 LOC removed from tabbed_interface.py
- [ ] Integration tests GREEN

---

### Phase 3: Extract DefinitionGenerationOrchestrator (Week 4-5)

#### 3.8 Step 3.1: Create Orchestrator Skeleton (3 days)

**Tasks:**
1. Create `src/services/orchestrators/definition_generation_orchestrator.py`
2. Implement interface from 2.3.1
3. Move workflow steps from `_handle_definition_generation()`
4. Create comprehensive unit tests

**Code Structure:**
```python
class DefinitionGenerationOrchestrator:
    async def orchestrate_generation(
        self, request: GenerationRequest, progress_callback=None
    ) -> GenerationResult:
        # Step 1: Validate context
        if progress_callback:
            progress_callback("Validating context...", 10)

        if not self._validate_context(request):
            return GenerationResult(
                success=False,
                error="Minimum 1 context required"
            )

        # Step 2: Determine category
        if progress_callback:
            progress_callback("Determining category...", 20)

        category_result = await self.category_service.determine_category(
            request.begrip,
            request.organisatorische_context[0] if request.organisatorische_context else "",
            request.juridische_context[0] if request.juridische_context else "",
        )

        # Step 3: Check duplicates
        if progress_callback:
            progress_callback("Checking duplicates...", 30)

        if not request.force_generate:
            check_result = self.checker.check_before_generation(...)
            if check_result.action != CheckAction.PROCEED:
                return GenerationResult(
                    success=False,
                    duplicate_check_result=check_result,
                )

        # Step 4-7: Continue workflow...
```

**Success Criteria:**
- [ ] Orchestrator created
- [ ] All 7 workflow steps implemented
- [ ] Unit tests cover all paths
- [ ] Error handling tested

---

#### 3.9 Step 3.2: Integrate into tabbed_interface (3 days)

**Tasks:**
1. Inject orchestrator in `__init__`
2. Replace `_handle_definition_generation()` with orchestrator call
3. Handle progress callback for UI updates
4. Map GenerationResult to session state
5. Update integration tests

**Before:**
```python
# tabbed_interface.py (380 LOC god method)
def _handle_definition_generation(self, begrip, context_data):
    # ... 380 lines of orchestration ...
```

**After:**
```python
# tabbed_interface.py (~30 LOC delegation)
async def _handle_definition_generation(self, begrip, context_data):
    request = GenerationRequest(
        begrip=begrip,
        organisatorische_context=context_data.get("organisatorische_context", []),
        # ... map inputs ...
    )

    result = await self.generation_orchestrator.orchestrate_generation(
        request,
        progress_callback=self._update_progress_bar
    )

    if result.success:
        self._store_generation_result(result)
        st.success("Definition generated!")
    elif result.duplicate_check_result:
        self._show_duplicate_choice(result.duplicate_check_result)
    else:
        st.error(result.error)
```

**Success Criteria:**
- [ ] 350 LOC removed from tabbed_interface.py
- [ ] Integration tests GREEN
- [ ] UI behavior unchanged

---

### Phase 4: Extract RegenerationOrchestrator (Week 6-7)

#### 3.10 Step 4.1: Create Orchestrator (3 days)

**Tasks:**
1. Create `src/services/orchestrators/regeneration_orchestrator.py`
2. Implement interface from 2.3.2
3. Move all 8 regeneration methods from definition_generator_tab.py
4. Create unit tests

**Code Structure:**
```python
class RegenerationOrchestrator:
    async def orchestrate_regeneration(
        self, request: RegenerationRequest, progress_callback=None
    ) -> RegenerationResult:
        # Step 1: Analyze impact
        impact = self.analyze_category_change_impact(
            request.old_category,
            request.new_category
        )

        # Step 2: Set context
        self.regeneration_service.set_regeneration_context(...)

        # Step 3: Execute based on mode
        if request.regeneration_mode == "direct":
            return await self._execute_direct_regeneration(request, impact)
        elif request.regeneration_mode == "manual":
            return self._prepare_manual_regeneration(request, impact)
        else:  # keep
            return RegenerationResult(
                success=True,
                mode="keep",
                impact_analysis=impact
            )
```

**Success Criteria:**
- [ ] Orchestrator created
- [ ] All 3 modes implemented
- [ ] Unit tests GREEN

---

#### 3.11 Step 4.2: Integrate into definition_generator_tab (3 days)

**Tasks:**
1. Inject orchestrator in `__init__`
2. Replace 8 regeneration methods with orchestrator calls
3. Update UI to use RegenerationResult
4. Update integration tests

**Before:**
```python
# definition_generator_tab.py (500 LOC across 8 methods)
def _trigger_regeneration_with_category(...): ...
def _render_regeneration_preview(...): ...
def _analyze_regeneration_impact(...): ...
def _direct_regenerate_definition(...): ...
# ... 4 more methods ...
```

**After:**
```python
# definition_generator_tab.py (~50 LOC delegation)
def _handle_regeneration(self, request: RegenerationRequest):
    result = await self.regeneration_orchestrator.orchestrate_regeneration(
        request,
        progress_callback=self._update_progress
    )

    if result.mode == "direct":
        self._show_new_definition(result.new_definition)
    elif result.mode == "manual":
        self._navigate_to_generator(result.navigation_state)
    else:
        st.success("Category updated, definition kept.")
```

**Success Criteria:**
- [ ] 450 LOC removed from definition_generator_tab.py
- [ ] Integration tests GREEN
- [ ] All 3 modes working

---

### Phase 5: Thin UI Layer (Week 8)

#### 3.12 Step 5.1: Reduce tabbed_interface to <400 LOC (2 days)

**Tasks:**
1. Remove all extracted methods
2. Keep only:
   - Tab routing
   - Header/Footer
   - Service initialization
   - Orchestrator delegation
3. Verify integration tests

**Target Structure:**
```python
class TabbedInterface:
    def __init__(self):  # ~50 LOC - service init
    def render(self):  # ~50 LOC - main entry
    def _render_header(self):  # ~20 LOC
    def _render_footer(self):  # ~20 LOC
    def _render_main_tabs(self):  # ~30 LOC
    def _render_tab_content(self, tab_key):  # ~20 LOC

    # Orchestrator delegation (~150 LOC total)
    def _handle_generation_click(self, ...):  # ~50 LOC
    def _update_progress_bar(self, msg, pct):  # ~10 LOC
    def _store_generation_result(self, result):  # ~30 LOC
    def _show_duplicate_choice(self, check_result):  # ~30 LOC

    # Utils (~50 LOC)
    def _clear_all_fields(self):  # ~20 LOC
    def _dbg(self, label):  # ~10 LOC

    # REMOVE: 8 stub methods (dead code)
```

**Success Criteria:**
- [ ] <400 LOC in tabbed_interface.py
- [ ] Integration tests GREEN
- [ ] 8 stub methods removed

---

#### 3.13 Step 5.2: Reduce definition_generator_tab to <800 LOC (2 days)

**Tasks:**
1. Remove all extracted methods
2. Keep only rendering logic
3. Delegate to orchestrators/services

**Target Structure:**
```python
class DefinitionGeneratorTab:
    def __init__(self):  # ~20 LOC
    def render(self):  # ~30 LOC

    # Duplicate check rendering (~200 LOC)
    def _render_duplicate_check_results(self, ...):
    def _render_existing_definition(self, ...):

    # Generation results rendering (~400 LOC)
    def _render_generation_results(self, ...):
    def _render_validation_results(self, ...):

    # Action handlers (~100 LOC)
    def _use_existing_definition(self, ...):
    def _edit_definition(self, ...):
    def _export_definition(self, ...):

    # Utils (~50 LOC)
    def _clear_results(self):

    # REMOVE: All orchestration logic (500 LOC to orchestrators)
```

**Success Criteria:**
- [ ] <800 LOC in definition_generator_tab.py
- [ ] Integration tests GREEN
- [ ] All rendering preserved

---

### Phase 6: Cleanup & Documentation (Week 9)

#### 3.14 Step 6.1: Remove Scaffolding (1 day)

**Tasks:**
1. Remove any temporary compatibility code
2. Clean up unused imports
3. Remove deprecated methods
4. Final test pass

**Success Criteria:**
- [ ] No dead code
- [ ] All imports used
- [ ] All tests GREEN

---

#### 3.15 Step 6.2: Update Documentation (2 days)

**Tasks:**
1. Update architecture diagrams
2. Document orchestrator APIs
3. Update EPIC-026 status
4. Create migration guide

**Deliverables:**
- `docs/architectuur/orchestrators.md` - Orchestrator design
- `docs/backlog/EPIC-026/migration_guide.md` - How to use new orchestrators
- Updated `SOLUTION_ARCHITECTURE.md`

---

## Part 4: Risk Assessment & Mitigation

### 4.1 Risk Matrix

| Risk | Probability | Impact | Severity | Mitigation |
|------|------------|--------|----------|------------|
| **Breaking generation workflow** | HIGH | CRITICAL | 🔴 VERY HIGH | Comprehensive integration tests BEFORE extraction |
| **Async/sync boundary issues** | MEDIUM | HIGH | 🟠 HIGH | Careful async wrapper design, unit test each boundary |
| **State management bugs** | MEDIUM | HIGH | 🟠 HIGH | Type-safe state wrappers, schema validation |
| **Duplicate check regression** | MEDIUM | MEDIUM | 🟡 MEDIUM | Specific tests for duplicate workflow paths |
| **Document integration breaks** | LOW | MEDIUM | 🟡 MEDIUM | DocumentContextService unit tests with mocks |
| **Performance degradation** | LOW | MEDIUM | 🟡 MEDIUM | Benchmark tests, profile orchestrators |
| **Test coverage gaps** | MEDIUM | MEDIUM | 🟡 MEDIUM | Require 90%+ coverage for orchestrators |

---

### 4.2 Breaking Changes Risk

**High Risk Areas:**

1. **`_handle_definition_generation()` removal**
   - **Risk:** Single importer (main.py) but deeply coupled
   - **Mitigation:** Keep method as thin wrapper initially, remove in Phase 6

2. **Session state structure changes**
   - **Risk:** 15+ keys used across multiple components
   - **Mitigation:** Type-safe wrappers, no schema changes, only access pattern changes

3. **Async execution patterns**
   - **Risk:** `run_async()` bridge might hide concurrency issues
   - **Mitigation:** Make orchestrators fully async, use proper async context

4. **Regeneration context coordination**
   - **Risk:** Complex state machine across UI and services
   - **Mitigation:** Move ALL state machine logic to orchestrator

**Low Risk Areas:**

1. **Pattern extraction to config**
   - Already data-driven in spirit, just making it explicit

2. **DocumentContextService extraction**
   - Self-contained logic, clear boundaries

3. **OntologicalCategoryService extraction**
   - Already has service-like structure

---

### 4.3 State Management Migration Risks

**Current Pattern (RISKY):**
```python
# UI directly mutates session state in workflow
SessionStateManager.set_value("regeneration_active", True)
SessionStateManager.set_value("regeneration_begrip", begrip)
# ... 5 more mutations ...
# Then calls service
service.generate(...)
# Then mutates more state
SessionStateManager.set_value("last_result", result)
```

**Target Pattern (SAFE):**
```python
# Orchestrator owns state machine
result = await orchestrator.orchestrate_generation(request)
# UI only stores final result
SessionStateManager.set_value("last_result", result.to_dict())
```

**Migration Strategy:**
1. Orchestrator internally uses state manager (Phase 3-4)
2. Move state logic to orchestrator methods (Phase 5)
3. UI only reads/writes final results (Phase 5)

---

### 4.4 Async/Sync Refactoring Challenges

**Current Pattern (PROBLEMATIC):**
```python
# Sync UI method calls async method via asyncio.run()
def _handle_definition_generation(self, ...):  # SYNC
    category = asyncio.run(self._determine_ontological_category(...))  # ASYNC
    result = run_async(definition_service.generate(...))  # ASYNC via bridge
```

**Issues:**
- Nested event loops (asyncio.run inside streamlit context)
- Error handling complexity
- Progress callback threading issues

**Target Pattern (CLEAN):**
```python
# UI method is properly async
async def _handle_definition_generation(self, ...):  # ASYNC
    result = await self.generation_orchestrator.orchestrate_generation(...)  # ASYNC

# Streamlit calls via async wrapper
def render(self):
    if st.button("Generate"):
        result = asyncio.run(self._handle_definition_generation(...))
```

**Migration Strategy:**
1. Make orchestrators fully async (Phase 3-4)
2. Add async wrappers in UI (Phase 5)
3. Remove `run_async()` bridge (Phase 5)

---

## Part 5: Validation & Success Criteria

### 5.1 Per-Step Validation

**After EACH extraction step:**
- [ ] All integration tests GREEN
- [ ] No regressions in UI behavior
- [ ] Unit tests for new service/orchestrator
- [ ] Code review passed
- [ ] Documentation updated

### 5.2 Phase Completion Criteria

**Phase 0 (Preparation) Complete When:**
- [ ] 10+ integration tests covering all workflows
- [ ] All patterns in config file (no hardcoded dicts)
- [ ] Session state schema documented
- [ ] Type-safe state wrappers created

**Phase 1 (OntologicalCategoryService) Complete When:**
- [ ] Service created with full interface
- [ ] 250 LOC removed from tabbed_interface.py
- [ ] Unit tests 90%+ coverage
- [ ] Integration tests GREEN

**Phase 2 (DocumentContextService) Complete When:**
- [ ] Service created with full interface
- [ ] 350 LOC removed from tabbed_interface.py
- [ ] Unit tests 85%+ coverage
- [ ] Integration tests GREEN

**Phase 3 (DefinitionGenerationOrchestrator) Complete When:**
- [ ] Orchestrator created with all 7 steps
- [ ] 350 LOC removed from tabbed_interface.py
- [ ] Unit tests 95%+ coverage (critical path!)
- [ ] Integration tests GREEN
- [ ] Async patterns clean (no asyncio.run nesting)

**Phase 4 (RegenerationOrchestrator) Complete When:**
- [ ] Orchestrator created with all 3 modes
- [ ] 450 LOC removed from definition_generator_tab.py
- [ ] Unit tests 90%+ coverage
- [ ] Integration tests GREEN

**Phase 5 (Thin UI Layer) Complete When:**
- [ ] tabbed_interface.py <400 LOC
- [ ] definition_generator_tab.py <800 LOC
- [ ] All business logic in orchestrators
- [ ] Integration tests GREEN
- [ ] No async/sync mixing issues

**Phase 6 (Cleanup) Complete When:**
- [ ] No dead code
- [ ] All documentation updated
- [ ] Migration guide complete
- [ ] Architecture diagrams updated

### 5.3 Final Success Criteria

**Quantitative Metrics:**
- [ ] tabbed_interface.py: 1,793 → <400 LOC (78% reduction)
- [ ] definition_generator_tab.py: 2,525 → <800 LOC (68% reduction)
- [ ] Total LOC reduction: ~2,600 LOC moved to services
- [ ] Test coverage: 90%+ for orchestrators
- [ ] Zero integration test failures

**Qualitative Criteria:**
- [ ] UI layer is pure presentation (no business logic)
- [ ] Orchestrators are testable in isolation
- [ ] Service boundaries are clear and documented
- [ ] Async patterns are clean (no bridges or hacks)
- [ ] State management is centralized in orchestrators
- [ ] Error handling is consistent
- [ ] Code is maintainable (future devs can understand)

---

## Part 6: Timeline Estimate

### 6.1 Detailed Timeline (9 Weeks)

| Week | Phase | Deliverables | Risk | Effort |
|------|-------|--------------|------|--------|
| **1** | Preparation | Integration tests, Pattern config, State docs | LOW | 5 days |
| **2** | OntologicalCategoryService | Service + Integration | MEDIUM | 5 days |
| **3** | DocumentContextService | Service + Integration | LOW | 4 days |
| **4-5** | DefinitionGenerationOrchestrator | Orchestrator + Integration | **HIGH** | 10 days |
| **6-7** | RegenerationOrchestrator | Orchestrator + Integration | **HIGH** | 8 days |
| **8** | Thin UI Layer | Reduce both files | MEDIUM | 4 days |
| **9** | Cleanup & Docs | Polish & Documentation | LOW | 4 days |

**Total: 9 weeks (45 working days)**

### 6.2 Critical Path

```
Week 1 (Prep) → Week 2 (Category) → Week 3 (Document) → Week 4-5 (Generation) → Week 6-7 (Regeneration) → Week 8 (UI) → Week 9 (Cleanup)
     ↓              ↓                    ↓                      ↓                        ↓                    ↓             ↓
   Tests      Extract Service     Extract Service    **CRITICAL EXTRACTION**    Extract Orchestrator    Thin UI    Polish
```

**Dependencies:**
- Week 2 depends on Week 1 (tests + patterns)
- Week 4-5 depends on Week 2-3 (services)
- Week 6-7 can partially overlap with Week 4-5
- Week 8 depends on Week 4-7
- Week 9 depends on Week 8

### 6.3 Accelerators

**Parallel Work Opportunities:**
1. Weeks 2-3: Category + Document services can be extracted in parallel (different codebases)
2. Weeks 4-7: After Week 4 (Generation Orchestrator skeleton), Week 6 (Regeneration) can start
3. Week 9: Docs can be written while code review happens

**Potential to reduce to 7 weeks with parallel work.**

### 6.4 Contingency Planning

**If timeline slips:**
1. **After Week 5:** If Generation Orchestrator not complete, add 1 week
2. **After Week 7:** If Regeneration Orchestrator not complete, add 1 week
3. **After Week 8:** If UI reduction incomplete, move to Phase 2 (acceptable)

**Maximum timeline: 11 weeks (with 2 weeks contingency)**

---

## Part 7: Rollback Strategy

### 7.1 Rollback Checkpoints

**Every step has a rollback plan:**

| Step | Checkpoint | Rollback Action | Data Loss Risk |
|------|-----------|-----------------|----------------|
| 0.2 | Patterns in config | Revert config, restore hardcoded dicts | NONE |
| 1.1 | Category service created | Delete service file | NONE |
| 1.2 | Category service integrated | Revert tabbed_interface.py, restore old methods | NONE |
| 2.1-2.2 | Document service | Revert files | NONE |
| 3.1 | Generation orchestrator created | Delete orchestrator | NONE |
| 3.2 | Generation orchestrator integrated | Revert tabbed_interface.py | NONE |
| 4.1 | Regeneration orchestrator created | Delete orchestrator | NONE |
| 4.2 | Regeneration orchestrator integrated | Revert definition_generator_tab.py | NONE |
| 5.1-5.2 | Thin UI layer | Revert to pre-Phase-5 commit | NONE |

**Key Principle:** NO DATABASE SCHEMA CHANGES → NO DATA LOSS RISK

### 7.2 Rollback Procedure

**For any step:**
1. Stop work immediately
2. Run integration tests to confirm failure
3. `git revert <commit>` or `git reset --hard <checkpoint>`
4. Verify integration tests GREEN
5. Document what went wrong
6. Adjust plan and retry

**Critical Rollback Points:**
- **End of Week 5:** If Generation Orchestrator extraction fails, rollback to end of Week 3
- **End of Week 7:** If Regeneration Orchestrator extraction fails, rollback to end of Week 5
- **End of Week 8:** If UI thinning breaks, rollback to end of Week 7

### 7.3 Safe Harbor Commits

**Create git tags at these milestones:**
- `epic-026-prep-complete` (end of Week 1)
- `epic-026-category-service` (end of Week 2)
- `epic-026-document-service` (end of Week 3)
- `epic-026-generation-orchestrator` (end of Week 5) **← CRITICAL**
- `epic-026-regeneration-orchestrator` (end of Week 7) **← CRITICAL**
- `epic-026-thin-ui` (end of Week 8)
- `epic-026-complete` (end of Week 9)

**Each tag = rollback checkpoint with GREEN tests**

---

## Part 8: Code Structure Before/After

### 8.1 Before Extraction (Current)

```
src/
├── ui/
│   ├── tabbed_interface.py (1,793 LOC) **GOD OBJECT**
│   │   ├── Tab routing (100 LOC)
│   │   ├── Service init (150 LOC)
│   │   ├── Category determination (260 LOC) **← HIDDEN SERVICE**
│   │   ├── Generation orchestration (380 LOC) **← HIDDEN ORCHESTRATOR**
│   │   ├── Document processing (350 LOC) **← HIDDEN SERVICE**
│   │   ├── Context management (180 LOC)
│   │   ├── Duplicate check (30 LOC)
│   │   ├── Utils + 8 dead stubs (90 LOC)
│   │   └── Header/Footer (100 LOC)
│   │
│   └── components/
│       └── definition_generator_tab.py (2,525 LOC) **GOD OBJECT**
│           ├── Duplicate check rendering (450 LOC)
│           ├── Generation results rendering (800 LOC)
│           ├── Validation rendering (250 LOC)
│           ├── Rule reasoning (180 LOC) **← HARDCODED LOGIC**
│           ├── Action handlers (150 LOC)
│           ├── Examples persistence (180 LOC)
│           ├── Regeneration orchestration (500 LOC) **← HIDDEN ORCHESTRATOR**
│           └── Utils (65 LOC)
│
└── services/
    ├── unified_definition_generator.py (existing)
    ├── validation_orchestrator_v2.py (existing)
    ├── regeneration_service.py (existing - partial)
    └── ... (other services)
```

**Problems:**
- 4,318 LOC in UI layer (should be ~1,000 LOC)
- 2 hidden orchestrators (880 LOC combined)
- 610 LOC of service logic in UI (category + document)
- 180 LOC hardcoded business logic (rule reasoning)
- No clear boundaries
- Impossible to test business logic separately

---

### 8.2 After Extraction (Target)

```
src/
├── ui/
│   ├── tabbed_interface.py (~350 LOC) **THIN UI**
│   │   ├── Tab routing (80 LOC)
│   │   ├── Service init (50 LOC)
│   │   ├── Header/Footer (50 LOC)
│   │   ├── Orchestrator delegation (120 LOC)
│   │   └── Utils (50 LOC)
│   │
│   └── components/
│       └── definition_generator_tab.py (~750 LOC) **THIN UI**
│           ├── Duplicate check rendering (250 LOC)
│           ├── Generation results rendering (350 LOC)
│           ├── Validation rendering (100 LOC)
│           ├── Action handlers (50 LOC)
│           └── Utils (50 LOC)
│
├── services/
│   ├── unified_definition_generator.py (existing)
│   ├── validation_orchestrator_v2.py (existing)
│   ├── regeneration_service.py (existing)
│   │
│   ├── ontological_category_service.py (~300 LOC) **NEW**
│   │   ├── 6-step protocol
│   │   ├── Quick analysis
│   │   ├── Pattern matching (from config)
│   │   └── Score calculation
│   │
│   ├── document_context_service.py (~350 LOC) **NEW**
│   │   ├── Context aggregation
│   │   ├── Snippet extraction
│   │   └── Citation formatting
│   │
│   └── orchestrators/
│       ├── definition_generation_orchestrator.py (~500 LOC) **NEW**
│       │   ├── Context validation
│       │   ├── Category determination (delegates to service)
│       │   ├── Duplicate check workflow
│       │   ├── Document integration (delegates to service)
│       │   ├── Regeneration handling
│       │   ├── Service coordination (5+ services)
│       │   └── Result preparation
│       │
│       └── regeneration_orchestrator.py (~600 LOC) **NEW**
│           ├── Category change impact analysis
│           ├── Regeneration workflow (3 modes)
│           ├── Context extraction & preparation
│           ├── Definition comparison
│           └── Navigation coordination
│
└── config/
    └── ontological_patterns.yaml **NEW** (data-driven patterns)
```

**Improvements:**
- UI layer: 4,318 → 1,100 LOC (74% reduction)
- Service layer: +1,750 LOC (new orchestrators + services)
- Clear separation: UI (presentation) vs Services (business logic) vs Orchestrators (workflows)
- Testable: Each service/orchestrator can be unit tested
- Maintainable: Single Responsibility Principle
- Data-driven: Patterns in config, not code

---

## Part 9: Recommendations & Next Steps

### 9.1 Strategic Recommendations

1. **EXTRACT ORCHESTRATORS FIRST ✅**
   - Do NOT attempt UI splitting before orchestrator extraction
   - Orchestrators contain core business logic that must be preserved
   - UI refactoring is MUCH easier after orchestrators are extracted

2. **Invest in Integration Tests UPFRONT ✅**
   - Week 1 preparation is CRITICAL
   - Integration tests are your safety net
   - DO NOT skip test creation

3. **Extract Hardcoded Logic to Config EARLY ✅**
   - Week 1 pattern extraction prevents duplication
   - Makes category service clean from day 1
   - Enables future configurability

4. **Use Type-Safe State Wrappers ✅**
   - Prevents state schema bugs
   - Makes state contracts explicit
   - Easier debugging

5. **Keep Rollback Points Close ✅**
   - Git tag after EVERY major step
   - Never more than 1 week from last checkpoint
   - Integration tests must be GREEN before moving on

### 9.2 Immediate Next Steps (Post Day-2)

**Tomorrow (Day 3):**
1. Complete responsibility maps for remaining files:
   - `web_lookup_service.py`
   - `validation_orchestrator_v2.py`

2. Review this extraction plan with team

3. **DECISION POINT:** Approve orchestrator-first strategy or revise

**Day 4-5 (if approved):**
1. Begin Week 1 preparation:
   - Create integration test suite
   - Extract patterns to config
   - Document state contracts

2. Set up project tracking:
   - Create EPIC-026 Phase 2 (Extraction) epic
   - Create user stories for each week
   - Set up CI/CD for integration tests

**Week 2 onwards:**
1. Execute extraction plan as outlined
2. Daily standups to track progress
3. Weekly reviews to assess risks
4. Adjust timeline if needed

### 9.3 Success Indicators

**We'll know we're succeeding when:**
1. ✅ Integration tests stay GREEN after every step
2. ✅ LOC in UI layer decreases week over week
3. ✅ Unit test coverage increases for services/orchestrators
4. ✅ Code reviews are faster (clearer boundaries)
5. ✅ New features are easier to add (better architecture)

**We'll know we need to pause/revise if:**
1. ⚠️ Integration tests fail and we can't fix in 1 day
2. ⚠️ More than 2 rollbacks in a week
3. ⚠️ Orchestrator complexity is higher than original code
4. ⚠️ State management becomes more confusing
5. ⚠️ Timeline slips more than 2 weeks

---

## Appendix A: Orchestrator Method Mapping

### A.1 Definition Generation Orchestrator Methods

**From `tabbed_interface.py` → `DefinitionGenerationOrchestrator`**

| Current Method | Lines | New Orchestrator Method | Notes |
|----------------|-------|-------------------------|-------|
| `_handle_definition_generation()` | 821-1200 | `orchestrate_generation()` | Main orchestration method |
| `_determine_ontological_category()` | 272-333 | **DELEGATED** to `OntologicalCategoryService` | Move to service |
| `_get_document_context()` | 1207-1225 | **DELEGATED** to `DocumentContextService.build_context_summary()` | Move to service |
| `_build_document_snippets()` | 1260-1348 | **DELEGATED** to `DocumentContextService.extract_snippets()` | Move to service |
| Context validation logic | Inline | `_validate_context()` | Extract to method |
| Duplicate check logic | Inline | `_check_duplicates()` | Extract to method |
| Regeneration override logic | Inline | `_apply_regeneration_override()` | Extract to method |
| Result storage logic | Inline | `_prepare_result()` | Extract to method |

**Total: 380 LOC → Orchestrator (~500 LOC with proper structure)**

---

### A.2 Regeneration Orchestrator Methods

**From `definition_generator_tab.py` → `RegenerationOrchestrator`**

| Current Method | Lines | New Orchestrator Method | Notes |
|----------------|-------|-------------------------|-------|
| `_trigger_regeneration_with_category()` | 2008-2048 | `_prepare_manual_regeneration()` | Manual mode |
| `_render_regeneration_preview()` | 2049-2135 | **UI STAYS** in tab | Rendering only |
| `_get_category_display_name()` | 2136-2152 | **DELEGATED** to `CategoryService` | Already exists |
| `_analyze_regeneration_impact()` | 2153-2191 | `analyze_category_change_impact()` | Extract logic |
| `_direct_regenerate_definition()` | 2192-2344 | `_execute_direct_regeneration()` | Direct mode |
| `_extract_context_from_generation_result()` | 2345-2369 | `_extract_context()` | Helper method |
| `_render_definition_comparison()` | 2370-2411 | **UI STAYS** in tab | Rendering only |
| `_extract_definition_from_result()` | 2412-2427 | `_extract_definition()` | Helper method |

**Total: 500 LOC → Orchestrator (~600 LOC with 3 mode handlers) + UI rendering stays in tab**

---

## Appendix B: State Schema Documentation

### B.1 Generation Flow State

```python
# Session State Keys Used by Generation Orchestrator

"generation_options": {
    "force_generate": bool,      # Skip duplicate check
    "force_duplicate": bool,     # Accept duplicate violation
}

"last_generation_result": {
    "success": bool,
    "definitie": str,
    "definitie_gecorrigeerd": str,
    "validation_result": dict,
    "category": str,
    "category_reasoning": str,
    "saved_definition_id": int,
    "voorbeelden": dict,
    # ... etc
}

"last_check_result": CheckResult  # Duplicate check result

"selected_definition": DefinitieRecord  # For "show existing" choice

"editing_definition_id": int  # For edit tab preparation

"edit_organisatorische_context": list[str]
"edit_juridische_context": list[str]
"edit_wettelijke_basis": list[str]
```

### B.2 Regeneration Flow State

```python
# Session State Keys Used by Regeneration Orchestrator

"regeneration_active": bool
"regeneration_begrip": str
"regeneration_category": str

# Also uses generation flow state for result storage
```

### B.3 Document Flow State

```python
# Session State Keys Used by Document Context Service

"selected_documents": list[str]  # Document IDs
"documents_updated": bool  # Trigger re-extraction
```

---

## Appendix C: Test Strategy Detail

### C.1 Integration Test Scenarios

**Scenario 1: Full Generation Flow (Happy Path)**
```python
def test_full_generation_flow_happy_path():
    # Setup
    begrip = "testbegrip"
    context = {
        "organisatorische_context": ["test org"],
        "juridische_context": ["test jur"],
        "wettelijke_basis": ["test wet"],
    }

    # Execute
    orchestrator = DefinitionGenerationOrchestrator(...)
    result = await orchestrator.orchestrate_generation(
        GenerationRequest(begrip=begrip, **context)
    )

    # Assert
    assert result.success
    assert result.definitie
    assert result.saved_definition_id
    assert result.ontological_category
    assert result.validation_result["passed"]
```

**Scenario 2: Duplicate Check Stops Generation**
```python
def test_duplicate_check_stops_generation():
    # Setup: Create existing definitie
    existing = create_definitie(begrip="testbegrip")

    # Execute
    result = await orchestrator.orchestrate_generation(
        GenerationRequest(begrip="testbegrip", ...)
    )

    # Assert: Generation stopped, duplicate result returned
    assert not result.success
    assert result.duplicate_check_result
    assert result.duplicate_check_result.action == CheckAction.SHOW_EXISTING
```

**Scenario 3: Force Generate Bypasses Duplicate**
```python
def test_force_generate_bypasses_duplicate():
    # Setup: Existing + force flag
    existing = create_definitie(begrip="testbegrip")

    # Execute with force
    result = await orchestrator.orchestrate_generation(
        GenerationRequest(
            begrip="testbegrip",
            force_generate=True,
            ...
        )
    )

    # Assert: New definition created despite duplicate
    assert result.success
    assert result.saved_definition_id != existing.id
```

**Scenario 4: Category Change Regeneration**
```python
def test_category_change_regeneration():
    # Setup
    existing = create_definitie(begrip="test", category="type")

    # Execute
    result = await regeneration_orchestrator.orchestrate_regeneration(
        RegenerationRequest(
            begrip="test",
            current_definition_id=existing.id,
            old_category="type",
            new_category="proces",
            regeneration_mode="direct",
            generation_result=existing.metadata,
        )
    )

    # Assert
    assert result.success
    assert result.mode == "direct"
    assert result.new_definition
    assert "proces" in result.new_definition.lower()  # Category-appropriate language
```

**... 6 more scenarios covering edge cases, errors, document integration, etc.**

### C.2 Unit Test Coverage Targets

| Component | Target Coverage | Critical Paths |
|-----------|----------------|----------------|
| **OntologicalCategoryService** | 90%+ | All 3 fallback layers, pattern matching |
| **DocumentContextService** | 85%+ | Snippet extraction, citation formatting |
| **DefinitionGenerationOrchestrator** | 95%+ | All workflow steps, error paths, duplicate logic |
| **RegenerationOrchestrator** | 90%+ | All 3 modes, impact analysis |

---

## Appendix D: Architecture Diagrams

### D.1 Current Architecture (Before)

```
┌─────────────────────────────────────────────────┐
│ main.py                                          │
└────────────────────┬────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────┐
│ TabbedInterface (1,793 LOC)                     │
│ ┌─────────────────────────────────────────────┐ │
│ │ Tab Routing                                  │ │
│ └─────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────┐ │
│ │ HIDDEN: OntologicalCategoryService (260 LOC)│ │
│ └─────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────┐ │
│ │ HIDDEN: GenerationOrchestrator (380 LOC)    │ │
│ │ ├── Duplicate Check                         │ │
│ │ ├── Category Determination                  │ │
│ │ ├── Document Integration                    │ │
│ │ ├── Service Coordination                    │ │
│ │ └── State Management                        │ │
│ └─────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────┐ │
│ │ HIDDEN: DocumentContextService (350 LOC)    │ │
│ └─────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────┐
│ DefinitionGeneratorTab (2,525 LOC)              │
│ ┌─────────────────────────────────────────────┐ │
│ │ Results Rendering                            │ │
│ └─────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────┐ │
│ │ HIDDEN: RegenerationOrchestrator (500 LOC)  │ │
│ │ ├── Impact Analysis                         │ │
│ │ ├── Direct Regeneration                     │ │
│ │ ├── Manual Regeneration Prep               │ │
│ │ └── Definition Comparison                   │ │
│ └─────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────┐ │
│ │ HARDCODED: Rule Reasoning (180 LOC)         │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘

**PROBLEM: Business logic hidden in UI layer!**
```

---

### D.2 Target Architecture (After)

```
┌─────────────────────────────────────────────────┐
│ main.py                                          │
└────────────────────┬────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────┐
│ TabbedInterface (~350 LOC) **THIN UI**          │
│ ├── Tab Routing                                 │
│ ├── Header/Footer                               │
│ └── Orchestrator Delegation                     │
└────────────────────┬────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────┐
│ DefinitionGeneratorTab (~750 LOC) **THIN UI**   │
│ ├── Results Rendering                           │
│ ├── Validation Display                          │
│ └── Action Handlers (delegate to orchestrators) │
└─────────────────────────────────────────────────┘

                     ↓ delegates to

┌─────────────────────────────────────────────────┐
│ ORCHESTRATION LAYER (NEW)                       │
├─────────────────────────────────────────────────┤
│                                                  │
│ DefinitionGenerationOrchestrator (~500 LOC)     │
│ ├── Context Validation                          │
│ ├── Category Determination (→ service)          │
│ ├── Duplicate Check Workflow                    │
│ ├── Document Integration (→ service)            │
│ ├── Regeneration Handling                       │
│ └── Result Preparation                          │
│                                                  │
│ RegenerationOrchestrator (~600 LOC)             │
│ ├── Impact Analysis                             │
│ ├── Direct Regeneration                         │
│ ├── Manual Regeneration Prep                    │
│ └── Definition Comparison                       │
│                                                  │
└────────────────────┬────────────────────────────┘
                     │
                     ↓ uses
┌─────────────────────────────────────────────────┐
│ SERVICE LAYER                                    │
├─────────────────────────────────────────────────┤
│                                                  │
│ OntologicalCategoryService (~300 LOC) **NEW**   │
│ ├── 6-Step Protocol                             │
│ ├── Quick Analysis                              │
│ └── Pattern Matching (config-driven)            │
│                                                  │
│ DocumentContextService (~350 LOC) **NEW**       │
│ ├── Context Aggregation                         │
│ ├── Snippet Extraction                          │
│ └── Citation Formatting                         │
│                                                  │
│ UnifiedDefinitionGenerator (existing)           │
│ ValidationOrchestratorV2 (existing)             │
│ RegenerationService (existing)                  │
│ ... (other services)                            │
│                                                  │
└─────────────────────────────────────────────────┘

**SOLUTION: Clear separation of concerns!**
```

---

## Summary

### What We've Designed

1. **Characterized 2 Hidden Orchestrators**
   - Generation Orchestrator: 380 LOC god method in tabbed_interface.py
   - Regeneration Orchestrator: 500 LOC across 8 methods in definition_generator_tab.py

2. **Designed Extraction Strategy**
   - ORCHESTRATORS FIRST (not UI splitting first)
   - 9-week phased approach
   - Clear service boundaries
   - Type-safe interfaces

3. **Created Step-by-Step Plan**
   - 15 steps across 6 phases
   - Integration tests before ANY changes
   - Extract patterns to config first
   - Services → Orchestrators → Thin UI → Cleanup

4. **Assessed Risks**
   - Async/sync boundaries (HIGH)
   - State management (MEDIUM)
   - Breaking changes (MEDIUM)
   - Mitigation for each risk

5. **Defined Success Criteria**
   - 74% LOC reduction in UI layer
   - 90%+ test coverage for orchestrators
   - Clean async patterns
   - Zero regressions

### Why This Plan Works

1. **Preserves Business Logic** - Orchestrators extracted as coherent units
2. **Reduces Risk** - Integration tests + rollback points every step
3. **Enables Testing** - Services/orchestrators testable in isolation
4. **Improves Architecture** - Clear layers (UI → Orchestrators → Services)
5. **Maintainable** - Future changes are localized, not scattered

### Next Steps

1. **Day 3:** Complete remaining responsibility maps
2. **Day 4:** Review and approve this extraction plan
3. **Day 5:** Begin Week 1 preparation (integration tests, config extraction)
4. **Week 2+:** Execute extraction plan as outlined

---

**Status:** ✅ EXTRACTION PLAN COMPLETE
**Owner:** Code Architect
**Date:** 2025-10-02
**EPIC:** EPIC-026 Phase 1 (Design)
**Ready for:** Team review and approval
