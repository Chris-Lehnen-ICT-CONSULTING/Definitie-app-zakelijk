---
id: EPIC-026-RESPONSIBILITY-MAP-TABBED-INTERFACE
epic: EPIC-026
phase: 1
day: 2
analyzed_file: src/ui/tabbed_interface.py
created: 2025-10-02
owner: code-architect
status: complete
---

# Responsibility Map: tabbed_interface.py

**Analysis Date:** 2025-10-02
**File Path:** `src/ui/tabbed_interface.py`
**File Size:** 1,793 LOC
**Methods Count:** 39 methods (33 real + 6 stub + 4 module-level)
**Complexity:** **VERY HIGH** (Orchestration God Object)

---

## Executive Summary

### Key Findings

- **Orchestration God Object:** 1,793 LOC als centrale controller voor ALLE UI functionaliteit
- **7 Service Boundaries** geïdentificeerd (UI orchestration, Generation, Context, Document, etc.)
- **ZERO Test Coverage:** Geen directe tests voor tabbed_interface.py
- **Single Importer:** Alleen `main.py` gebruikt deze class (goed voor refactoring!)
- **Mixed Concerns:** Tab routing, business logic, async orchestration, document processing - **ALLES in één class**
- **8 No-Op Stub Methods:** Pragma: no cover stubs die niets doen (code smell)

### Refactoring Complexity: **VERY HIGH**

**Factors increasing complexity:**
- Central orchestrator for ENTIRE UI
- Async/sync mixing (ontological category determination)
- Direct service instantiation in __init__
- Multiple tab component coordination
- Document processing integration
- Session state management (50+ calls)
- Complex category scoring logic (hardcoded)

**Factors supporting refactoring:**
- Single importer (main.py) - easy migration
- Clear tab delegation pattern
- Service abstraction already exists (get_definition_service)
- Tab components are separate classes
- No circular dependencies

---

## File Statistics

### Code Metrics
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| **Total LOC** | 1,793 | <500 | ❌ CRITICAL (3.6x over) |
| **Real Methods** | 33 | <20 | ❌ CRITICAL (1.7x over) |
| **Stub Methods** | 6 | 0 | ❌ Dead code |
| **Module Functions** | 4 | N/A | ℹ️ Helper functions |
| **Importers** | 1 (main.py) | N/A | ✅ Good |
| **Test Files** | 0 | N/A | ❌ NO coverage |

### Dependency Analysis

**Direct Imports (30+):**
```python
# External
import asyncio, os, json, re, logging, importlib.util
from datetime import datetime, UTC
from typing import Any
import streamlit as st

# Database
from database.definitie_repository import get_definitie_repository

# Domain
from domain.ontological_categories import OntologischeCategorie

# Document Processing
from document_processing.document_extractor import supported_file_types
from document_processing.document_processor import get_document_processor

# Services
from services import get_definition_service
from services.regeneration_service import RegenerationService

# UI Components (9 tabs!)
from ui.components.definition_edit_tab import DefinitionEditTab
from ui.components.definition_generator_tab import DefinitionGeneratorTab
from ui.components.enhanced_context_manager_selector import EnhancedContextManagerSelector
from ui.components.expert_review_tab import ExpertReviewTab
from ui.components.monitoring_tab import MonitoringTab
from ui.components.tabs.import_export_beheer import ImportExportBeheerTab
from ui.components.web_lookup_tab import WebLookupTab
from ui.components.prompt_debug_section import capture_voorbeelden_prompts
from ui.components.context_state_cleaner import init_context_cleaner

# Config & Utils
from config.feature_flags import FeatureFlags
from ui.session_state import SessionStateManager
from utils.container_manager import get_cached_container
from utils.type_helpers import ensure_dict
from integration.definitie_checker import CheckAction, DefinitieChecker
```

**Importers (1 file):**
```
src/main.py
```

**Test Coverage:**
```
NONE - No direct tests found
```

---

## Method Inventory (39 Methods)

### A. Class Methods - TabbedInterface (33 methods)

#### 1. Initialization (1 method)
```python
__init__()                                                         # L97   - Initialize interface with ALL services
```

#### 2. Main Rendering (2 methods)
```python
render()                                                           # L255  - Main entry point, renders entire UI
_render_main_tabs()                                                # L1592 - Render tab navigation
_render_tab_content(tab_key)                                       # L1627 - Delegate to tab component
```

#### 3. Header & Footer (2 methods)
```python
_render_header()                                                   # L516  - App title and branding
_render_footer()                                                   # L1693 - System info and diagnostics
```

#### 4. Ontological Category Determination (3 methods - ASYNC!)
```python
_determine_ontological_category(begrip, org_ctx, jur_ctx)         # L272  - ASYNC 6-step protocol
_legacy_pattern_matching(begrip: str) -> str                       # L334  - Fallback pattern matching
_generate_category_reasoning(begrip, category, scores) -> str      # L347  - Generate explanation
_get_category_scores(begrip: str) -> dict[str, int]               # L420  - Calculate category scores
```

#### 5. Global Context Management (3 methods)
```python
_render_global_context()                                           # L615  - Global context selector
_render_simplified_context_selector() -> dict[str, Any]            # L680  - Simplified context UI
_render_context_summary(context_data)                              # L1394 - Display context summary
```

#### 6. Metadata & Status (2 methods)
```python
_render_metadata_fields()                                          # L702  - Metadata input fields
_render_status_indicator()                                         # L602  - System status display
```

#### 7. Definition Generation Workflow (2 methods)
```python
_render_quick_generate_button(begrip, context_data)                # L787  - Quick generate button
_handle_definition_generation(begrip, context_data)                # L821  - MAIN ORCHESTRATOR (380 LOC!)
```

#### 8. Document Context Processing (5 methods)
```python
_get_document_context() -> dict[str, Any] | None                   # L1207 - Get doc context
_build_document_context_summary(aggregated) -> str                 # L1226 - Build summary
_build_document_snippets(begrip, doc_ids, ...) -> list[dict]       # L1260 - Extract snippets
_render_document_upload_section()                                  # L1416 - Upload UI
_process_uploaded_files(uploaded_files)                            # L1452 - Process uploads
_render_uploaded_documents_list()                                  # L1497 - List uploaded docs
```

#### 9. Duplicate Check (1 method)
```python
_handle_duplicate_check(begrip, context_data)                      # L1349 - Duplicate checking
```

#### 10. Utility Methods (3 methods)
```python
_clear_all_fields()                                                # L1380 - Clear session state
_dbg(label: str) -> None                                           # L500  - Debug logging
```

#### 11. NO-OP STUB METHODS (8 methods - pragma: no cover)
```python
_handle_file_upload() -> bool                                      # L1725 - Empty stub
_handle_export()                                                   # L1729 - Empty stub
_validate_inputs() -> bool                                         # L1733 - Empty stub
_update_progress() -> dict                                         # L1737 - Empty stub
_handle_user_interaction()                                         # L1741 - Empty stub
_process_large_data() -> bool                                      # L1745 - Empty stub
_sync_backend_state() -> dict                                      # L1749 - Empty stub
_integrate_with_backend()                                          # L1753 - Empty stub
```

### B. Module-Level Functions (4 functions)

```python
render_tabbed_interface()                                          # L1758 - Main render wrapper
initialize_session_state()                                         # L1768 - Init session state
generate_definition(*args, **kwargs)                               # L1781 - Patch target for tests
process_uploaded_file(*args, **kwargs)                             # L1786 - Patch target for tests
export_to_txt(*args, **kwargs)                                     # L1791 - Patch target for tests
```

---

## Responsibility Boundaries (7 Services)

### 1️⃣ **UI ORCHESTRATION & TAB ROUTING Service** (~350 LOC)

**Purpose:** Main controller for UI navigation and tab coordination

**Methods (7):**
- `__init__()` - Initialize ALL services and tab components
- `render()` - Main entry point
- `_render_header()` - App branding
- `_render_footer()` - System info
- `_render_status_indicator()` - Status display
- `_render_main_tabs()` - Tab navigation
- `_render_tab_content(tab_key)` - Delegate to tabs

**Tab Components Managed:**
- DefinitionGeneratorTab
- DefinitionEditTab
- ExpertReviewTab
- ImportExportBeheerTab
- MonitoringTab
- WebLookupTab
- OrchestrationTab (optional, legacy)

**Dependencies:**
- ALL tab components (9 imports!)
- SessionStateManager (state persistence)
- ServiceContainer (cached services)
- DefinitieChecker, DefinitieRepository

**Business Logic:**
- Tab visibility logic (feature flags)
- Service initialization orchestration
- Dummy service fallback (for tests)
- Context cleaner initialization (force_clean=True)

**Complexity:** MEDIUM-HIGH
- Central initialization of ALL services
- Tab lifecycle management
- Feature flag coordination
- Fallback logic for missing services

---

### 2️⃣ **ONTOLOGICAL CATEGORY DETERMINATION Service** (~260 LOC)

**Purpose:** Determine ontological category for begrip (async 6-step protocol)

**Methods (4):**
- `_determine_ontological_category(begrip, org, jur)` - **ASYNC** main logic
- `_legacy_pattern_matching(begrip)` - Fallback patterns
- `_generate_category_reasoning(begrip, category, scores)` - Explanation generation
- `_get_category_scores(begrip)` - Score calculation

**Dependencies:**
- `OntologischeAnalyzer` (6-step protocol)
- `QuickOntologischeAnalyzer` (quick fallback)
- Hardcoded category patterns (type, proces, resultaat, exemplaar)

**Business Logic:**
- 6-step ontological analysis (async)
- Fallback to quick analyzer
- Ultra-fallback to pattern matching
- Pattern detection:
  - **Proces:** atie, eren, ing, verificatie, validatie, etc.
  - **Type:** bewijs, document, middel, systeem, etc.
  - **Resultaat:** besluit, uitslag, rapport, conclusie, etc.
  - **Exemplaar:** specifiek, individueel, persoon, zaak, etc.
- Score calculation (count pattern matches)
- Reasoning generation from patterns

**Complexity:** **VERY HIGH**
- Async orchestration in sync UI context
- Multiple fallback layers (3 levels!)
- Hardcoded business rules (NOT data-driven)
- Pattern duplicated across 3 methods

**⚠️ CRITICAL ISSUES:**
1. **Hardcoded patterns** - Same patterns in 3 places (_generate_category_reasoning, _get_category_scores, _legacy_pattern_matching)
2. **Async/Sync mixing** - Async method called from sync render context
3. **Business logic in UI** - Category determination should be in domain/services layer

---

### 3️⃣ **DEFINITION GENERATION ORCHESTRATION Service** (~380 LOC)

**Purpose:** Main orchestrator for definition generation workflow

**Methods (2):**
- `_render_quick_generate_button(begrip, context_data)` - Generate button UI
- `_handle_definition_generation(begrip, context_data)` - **MAIN ORCHESTRATOR**

**The _handle_definition_generation method is a MASSIVE orchestrator (380 LOC!) that:**
1. Validates context (min 1 of org/jur/wet)
2. Determines ontological category (async call!)
3. Gets document context
4. Builds document snippets
5. Gets regeneration context
6. Calls definition service (async)
7. Stores results in session state
8. Prepares edit tab state
9. Clears regeneration context
10. Shows success message

**Dependencies:**
- `get_definition_service()` - Definition generation
- `RegenerationService` - Regeneration context
- `get_document_processor()` - Document processing
- `SessionStateManager` - State storage (15+ calls!)
- `run_async()` - Async bridge
- `capture_voorbeelden_prompts()` - Debug prompts

**Business Logic:**
- Context validation (min 1 required)
- Ontological category determination
- Document context aggregation
- Snippet extraction (max 2 snippets, 280 char window)
- Regeneration context handling
- Result formatting and storage
- Edit tab preparation
- Debug logging (DEBUG_EXAMPLES env var)

**Complexity:** **CRITICAL**
- 380 LOC in SINGLE method!
- Orchestrates 5+ services
- Complex async/sync coordination
- Extensive session state mutations
- Multiple error handling paths
- Debug instrumentation throughout

**⚠️ THIS IS THE CORE GOD METHOD - HIGHEST REFACTORING PRIORITY!**

---

### 4️⃣ **DOCUMENT CONTEXT PROCESSING Service** (~350 LOC)

**Purpose:** Handle document upload, processing, and context extraction

**Methods (6):**
- `_get_document_context()` - Get aggregated doc context
- `_build_document_context_summary(aggregated)` - Build summary
- `_build_document_snippets(begrip, doc_ids, ...)` - Extract snippets
- `_render_document_upload_section()` - Upload UI
- `_process_uploaded_files(uploaded_files)` - Process uploads
- `_render_uploaded_documents_list()` - List uploaded docs

**Dependencies:**
- `get_document_processor()` - Document processor service
- `supported_file_types()` - Supported formats
- `SessionStateManager` - Doc storage

**Business Logic:**
- Document upload handling (TXT, PDF, DOCX, MD, CSV, JSON, HTML, RTF)
- Text extraction per format
- Aggregated context building:
  - Keywords (top 10)
  - Concepts (top 5)
  - Legal refs (top 5)
  - Context hints (top 3)
- Snippet extraction with citation:
  - PDF: page numbers (p. X)
  - DOCX: paragraph numbers (¶ X)
  - Max 2 snippets per doc
  - 280 char window around begrip
- Progress bar UI
- Error handling per document

**Complexity:** MEDIUM-HIGH
- Multi-format document handling
- Citation extraction logic
- Aggregation and limiting
- Snippet windowing algorithm

---

### 5️⃣ **CONTEXT MANAGEMENT Service** (~180 LOC)

**Purpose:** Manage global context (org/jur/wet) selection and display

**Methods (3):**
- `_render_global_context()` - Global context selector
- `_render_simplified_context_selector()` - Simplified UI
- `_render_context_summary(context_data)` - Display summary

**Dependencies:**
- `ContextSelector` (EnhancedContextManagerSelector)
- `SessionStateManager` - Context storage
- Streamlit UI components

**Business Logic:**
- Context selection UI (org, juridisch, wettelijk)
- Context summary formatting
- Global context availability for all tabs

**Complexity:** LOW-MEDIUM
- Delegated to ContextSelector component
- Simple display logic
- Clear separation of concerns

---

### 6️⃣ **DUPLICATE CHECK Service** (~30 LOC)

**Purpose:** Check for duplicate definitions before generation

**Methods (1):**
- `_handle_duplicate_check(begrip, context_data)` - Duplicate check

**Dependencies:**
- `DefinitieChecker` - Duplicate detection service
- `SessionStateManager` - Result storage

**Business Logic:**
- Context normalization (JSON sorted arrays)
- Duplicate check via checker service
- Result storage for UI display

**Complexity:** LOW
- Simple delegation to checker
- Minimal logic

---

### 7️⃣ **UTILITY & METADATA Service** (~90 LOC)

**Purpose:** Metadata fields, utilities, debugging

**Methods (4 real + 8 stubs):**
- `_render_metadata_fields()` - Metadata input
- `_clear_all_fields()` - Clear session state
- `_dbg(label)` - Debug logging
- **8 NO-OP STUBS** (pragma: no cover)

**Dependencies:**
- `SessionStateManager` - State management

**Business Logic:**
- Metadata input fields (organisatie, categorie, etc.)
- Session state clearing (6 fields)
- Debug output

**Complexity:** LOW
- Simple utilities
- **Code smell: 8 empty stub methods**

**⚠️ ISSUE:** 8 stub methods with `pragma: no cover` - DEAD CODE to remove

---

## Cross-Cutting Concerns

### 1. Session State Management
**Usage:** Pervasive throughout ALL methods (50+ calls)
- Context storage (org/jur/wet)
- Generation results
- Document context
- Regeneration state
- Navigation state
- Edit tab preparation
- Debug flags

**Risk:** Tight coupling to session state structure

### 2. Async/Sync Mixing
**Async operations in sync UI:**
- `_determine_ontological_category()` is ASYNC
- Called from sync `_handle_definition_generation()`
- Uses `run_async()` bridge for `definition_service.generate_definition()`

**Risk:** Concurrency issues, complex error handling

### 3. Service Orchestration
**Multiple service coordination:**
- DefinitionService
- RegenerationService
- DocumentProcessor
- DefinitieChecker
- OntologischeAnalyzer
- ValidationOrchestratorV2

**Risk:** Complex initialization, dependency management

### 4. Hardcoded Business Logic
**Pattern detection duplicated:**
- `_generate_category_reasoning()` - patterns dict
- `_get_category_scores()` - indicator lists
- `_legacy_pattern_matching()` - patterns

**Risk:** Duplication, inconsistency, not data-driven

### 5. Error Handling
**Error patterns:**
- Try/except blocks everywhere
- Silent failures (pass in except)
- Fallback chains (3 levels for category determination)
- Dummy service for missing API key

### 6. Debug Instrumentation
**Debug code throughout:**
- `DEBUG_EXAMPLES` env var checks
- `_dbg()` method calls
- Extensive logging
- Debug checkboxes in UI

---

## Tab Component Architecture

### Managed Tab Components (7 active + 1 legacy)

```python
# Active tabs
self.definition_tab = DefinitionGeneratorTab(self.checker)
self.edit_tab = DefinitionEditTab(validation_service)
self.expert_tab = ExpertReviewTab(self.repository)
self.import_export_beheer_tab = ImportExportBeheerTab(self.repository)
self.monitoring_tab = MonitoringTab(self.repository)
self.web_lookup_tab = WebLookupTab(self.repository)

# Legacy (feature flagged)
self.orchestration_tab = OrchestrationTab(self.repository)  # if ENABLE_LEGACY_TAB
```

### Tab Configuration Structure
```python
self.tab_config = {
    "generator": {...},
    "edit": {...},
    "expert": {...},
    "import_export_beheer": {...},
    "monitoring": {...},
    "web_lookup": {...},
    # "orchestration": {...}  # DISABLED
}
```

### Tab Delegation Pattern
- `_render_main_tabs()` - Creates tab UI
- `_render_tab_content(tab_key)` - Delegates to tab.render()
- Tab components are self-contained (good!)
- TabbedInterface just coordinates (less good - still too much logic)

---

## Service Boundary Design (Proposed)

### 🎯 Target Architecture

```
tabbed_interface.py (UI COORDINATOR ONLY - ~200 LOC)
├── Tab routing logic (~50 LOC)
├── Service initialization (~50 LOC)
├── Header/Footer rendering (~50 LOC)
└── Context selector delegation (~50 LOC)

NEW Services:
├── OntologicalCategoryService (~260 LOC) **CRITICAL**
│   ├── 6-step protocol
│   ├── Quick analysis
│   ├── Pattern matching
│   └── Score calculation
│   └── NOTE: Extract patterns to config/data
│
├── DefinitionGenerationOrchestratorService (~380 LOC) **CRITICAL**
│   ├── Context validation
│   ├── Category determination (delegates to OntologicalCategoryService)
│   ├── Document context integration
│   ├── Snippet extraction
│   ├── Regeneration handling
│   ├── Service coordination
│   └── Result storage
│
├── DocumentContextService (~350 LOC)
│   ├── Upload handling
│   ├── Text extraction
│   ├── Context aggregation
│   ├── Snippet extraction
│   └── Citation formatting
│
├── ContextManagementPresentationService (~180 LOC)
│   ├── Context selector UI
│   ├── Summary formatting
│   └── Global context coordination
│
└── DuplicateCheckService (~30 LOC)
    └── Duplicate detection (already abstracted via DefinitieChecker)
```

---

## Migration Complexity Assessment

### Complexity Rating: **VERY HIGH** (9/10)

**Factors Supporting Migration:**
✅ Single importer (only main.py)
✅ Tab components already separated
✅ Service abstraction exists (get_definition_service)
✅ No circular dependencies
✅ Clear orchestration pattern

**Factors Increasing Complexity:**
❌ Central orchestrator for ENTIRE UI (1,793 LOC)
❌ _handle_definition_generation is 380 LOC GOD METHOD
❌ Async/sync mixing (category determination, generation)
❌ Hardcoded business logic (patterns in 3 places)
❌ Pervasive session state usage (50+ calls)
❌ Zero test coverage
❌ 8 dead stub methods (code smell)
❌ Complex service initialization with fallbacks
❌ Document processing integration
❌ Regeneration context coordination

### Migration Risk Areas

1. **God Method Refactoring**
   - `_handle_definition_generation()` is 380 LOC
   - Orchestrates 5+ services
   - Risk: Breaking complex workflow

2. **Async/Sync Boundary**
   - Category determination is async in sync UI
   - `run_async()` bridge usage
   - Risk: Concurrency issues

3. **Hardcoded Patterns**
   - Category patterns in 3 places
   - Risk: Inconsistency, duplication

4. **Session State Coupling**
   - 50+ SessionStateManager calls
   - Risk: Breaking state contracts

5. **Service Initialization**
   - Complex __init__ with fallbacks
   - Risk: Initialization failures

---

## Recommended Extraction Order

### Phase 1: PREPARATION (Week 1)
**Before ANY extraction:**
1. Create integration tests for current behavior
2. Document session state schema
3. Document tab coordination protocol
4. Extract hardcoded patterns to config
5. Remove 8 dead stub methods

### Phase 2: LOW-RISK Extractions (Week 2)
1. **Context Management Service** (LOW, 3 methods, ~180 LOC)
   - Already delegated to ContextSelector
   - Simple presentation logic
   - Easy to test

2. **Duplicate Check Service** (LOW, 1 method, ~30 LOC)
   - Already abstracted via DefinitieChecker
   - Minimal logic
   - Quick win

### Phase 3: MEDIUM-RISK Extractions (Week 3)
3. **Document Context Service** (MEDIUM-HIGH, 6 methods, ~350 LOC)
   - Self-contained processing logic
   - Clear inputs/outputs
   - Some complexity (snippets, citations)

4. **Ontological Category Service** (HIGH, 4 methods, ~260 LOC)
   - Extract patterns to config FIRST
   - Then extract service logic
   - Complex async/sync boundary
   - Multiple fallback layers

### Phase 4: CRITICAL Extraction (Week 4-5)
5. **Definition Generation Orchestrator Service** ⚠️ (VERY HIGH, 2 methods, ~380 LOC)
   - **MOST COMPLEX!**
   - God method with 380 LOC
   - Orchestrates 5+ services
   - Async/sync coordination
   - Extensive state management
   - **REQUIRES extensive testing**

### Phase 5: THIN UI LAYER (Week 6)
6. Reduce TabbedInterface to pure coordinator (~200 LOC)
   - Tab routing only
   - Service initialization
   - Header/Footer
   - Delegate everything else to services

---

## Testing Strategy

### Current Coverage: **ZERO**
- No direct tests for tabbed_interface.py
- Indirect coverage via UI tests only
- High risk for regressions

### Required Test Coverage

**Priority 1 (Before Refactor):**
1. Integration tests for full generation flow
   - Context validation
   - Category determination
   - Document context integration
   - Generation orchestration
   - Result storage

**Priority 2 (During Refactor):**
2. Unit tests for each extracted service
   - OntologicalCategoryService: 90%+ (business logic)
   - DefinitionGenerationOrchestrator: 95%+ (critical path)
   - DocumentContextService: 85%+ (processing logic)
   - ContextManagementService: 80%+ (presentation)

**Priority 3 (After Refactor):**
3. UI coordinator tests
   - Tab routing
   - Service initialization
   - Error fallbacks

### Test Data Requirements
- Mock DefinitieChecker
- Mock DefinitionService
- Mock DocumentProcessor
- Mock OntologischeAnalyzer
- Sample generation results
- Sample document uploads
- Mock session state

---

## Dependencies & Side Effects

### External Dependencies
1. **Streamlit** - Heavy UI dependency
2. **SessionStateManager** - Pervasive (50+ calls)
3. **Service Layer** (6 services):
   - DefinitionService
   - RegenerationService
   - DocumentProcessor
   - DefinitieChecker
   - OntologischeAnalyzer
   - ValidationOrchestratorV2

### Side Effects

**Session State Mutations:**
- last_generation_result
- editing_definition_id
- edit_*_context (3 fields)
- regeneration_* (3 fields)
- generation_options
- selected_documents
- documents_updated

**Async Operations:**
- Category determination (asyncio)
- Definition generation (run_async)

**Service Initialization:**
- Container initialization (cached)
- Tab component creation (7 tabs)
- Service fallback logic (dummy services)

**UI Navigation:**
- Tab switching
- State preparation for other tabs

---

## Key Insights & Recommendations

### 🚨 Critical Issues

1. **God Method Anti-Pattern**
   - `_handle_definition_generation()` is 380 LOC - **URGENT refactoring**
   - Violates Single Responsibility Principle severely

2. **Hardcoded Business Logic**
   - Category patterns in 3 different methods
   - NOT data-driven, NOT configurable
   - Duplication risk

3. **Async/Sync Mixing**
   - Async category determination in sync UI
   - `run_async()` bridge complexity
   - Error handling challenges

4. **Zero Test Coverage**
   - No direct tests for 1,793 LOC
   - High regression risk

5. **Dead Code**
   - 8 stub methods with pragma: no cover
   - Should be removed immediately

### ✅ Positive Findings

1. **Single Importer**
   - Only main.py uses TabbedInterface
   - Easy migration with facade pattern

2. **Tab Component Separation**
   - Tab logic already in separate classes
   - Good foundation for further separation

3. **Service Abstraction**
   - Already using service factories
   - Can extract more services easily

4. **Clear Orchestration Pattern**
   - Tab routing is clean
   - Delegation pattern works well

### 📋 Immediate Actions

**Before Refactoring:**
1. ✅ Remove 8 dead stub methods
2. ✅ Extract hardcoded patterns to config/data
3. ✅ Create integration test suite
4. ✅ Document session state schema
5. ✅ Document tab coordination protocol

**During Refactoring:**
1. ✅ Extract OntologicalCategoryService (make data-driven)
2. ✅ Split _handle_definition_generation into orchestrator service
3. ✅ Extract DocumentContextService
4. ✅ Use Facade pattern for backwards compatibility
5. ✅ Test after EVERY extraction

**After Refactoring:**
1. ✅ Reduce TabbedInterface to <200 LOC
2. ✅ Remove all business logic from UI
3. ✅ Verify main.py still works
4. ✅ Remove facade
5. ✅ Final test pass

---

## Comparative Analysis: tabbed_interface.py vs definition_generator_tab.py

### Size Comparison
| Metric | tabbed_interface.py | definition_generator_tab.py |
|--------|---------------------|----------------------------|
| LOC | 1,793 | 2,525 |
| Methods | 39 (33 real + 6 stubs) | 60 |
| Services | 7 | 8 |
| Complexity | VERY HIGH | VERY HIGH |

### Key Differences
1. **Purpose:**
   - TabbedInterface: **Orchestrator** (coordinates entire UI)
   - DefinitionGeneratorTab: **Renderer** (displays generation results)

2. **Critical Methods:**
   - TabbedInterface: `_handle_definition_generation()` (380 LOC god method)
   - DefinitionGeneratorTab: `_render_generation_results()` (800 LOC total across 13 methods)

3. **Business Logic:**
   - TabbedInterface: Category determination, generation orchestration, document processing
   - DefinitionGeneratorTab: Validation formatting, rule reasoning, regeneration UI

4. **Dependencies:**
   - TabbedInterface: 30+ imports, 7 tab components, 6 services
   - DefinitionGeneratorTab: 14 imports, heavy session state, database access

### Combined Refactoring Impact
- **Total LOC to refactor:** 4,318 (1,793 + 2,525)
- **Total methods to split:** 99 (39 + 60)
- **Total services to extract:** 15 unique services
- **Estimated effort:** 8-10 weeks full-time

---

## Migration Checklist

### Pre-Migration
- [ ] Remove 8 dead stub methods
- [ ] Extract hardcoded category patterns to config
- [ ] Create integration test suite (generation flow, tab routing, document processing)
- [ ] Document session state schema
- [ ] Document tab coordination protocol
- [ ] Map all service dependencies

### Service Extraction (6 weeks)
- [ ] Week 1: Context Management Service (3 days)
- [ ] Week 1: Duplicate Check Service (2 days)
- [ ] Week 2: Document Context Service (5 days)
- [ ] Week 3: Ontological Category Service (5 days)
- [ ] Week 4-5: Definition Generation Orchestrator Service (10 days) ⚠️
- [ ] Week 6: Reduce TabbedInterface to <200 LOC (5 days)

### Post-Migration
- [ ] All integration tests pass
- [ ] TabbedInterface reduced to <200 LOC
- [ ] main.py works unchanged
- [ ] Remove facade pattern
- [ ] Update architecture documentation
- [ ] Test coverage >80% for services

### Success Criteria
- ✅ Zero regressions in UI behavior
- ✅ TabbedInterface <200 LOC (pure coordinator)
- ✅ All business logic in services
- ✅ No hardcoded patterns (data-driven)
- ✅ Test coverage >80%
- ✅ No async/sync mixing (clean boundaries)

---

**Analysis Complete**
**Next Steps:** Create Day 2 standup report

---

**Analyst:** Code Architect Agent
**Date:** 2025-10-02
**Phase:** EPIC-026 Phase 1 (Design)
**Day:** 2 of 5
