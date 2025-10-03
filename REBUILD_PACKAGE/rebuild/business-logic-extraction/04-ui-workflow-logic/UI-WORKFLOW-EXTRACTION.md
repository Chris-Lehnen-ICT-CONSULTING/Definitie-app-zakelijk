# UI/Workflow Business Logic Extraction

**Extraction Date:** 2025-10-02
**Target:** All UI and workflow layer business logic
**Sources:** `src/main.py`, `src/ui/`, `src/integration/`, `src/services/definition_workflow_service.py`

---

## Application Flow

### Startup Logic (main.py)

**Entry Point:** `main()` function
- Initializes session state via `SessionStateManager.initialize_session_state()`
- Creates `TabbedInterface()` instance
- Renders complete UI via `interface.render()`
- Global error handling with logging and user-friendly error display

**Error Handling:**
- All startup exceptions are caught, logged, and displayed to user
- Uses `log_and_display_error()` utility for consistent error formatting

### Tab Navigation Rules (tabbed_interface.py)

**Radio-Based Navigation:**
- Active tab stored in session state: `SessionStateManager.get_value("active_tab", "generator")`
- Tab selection persisted across reruns
- Only selected tab content is rendered (performance optimization)

**Available Tabs:**
1. **Generator** - Definitie Generatie (default)
2. **Edit** - Bewerk definitie
3. **Expert** - Expert Review
4. **Import/Export/Beheer** - Consolidated management
5. **Monitoring** - Performance tracking
6. **Web Lookup** - External sources & duplicate checking
7. **Orchestration** (Legacy) - Only if feature flag enabled

**Tab Activation Flow:**
```
User selects tab → SessionState updated → UI reruns → Only selected tab renders
```

### Session State Management

**Core Manager:** `SessionStateManager` (singleton pattern)
- Centralized access to `st.session_state`
- Default values defined in `DEFAULT_VALUES` class variable
- CRITICAL RULE: NO direct `st.session_state` access outside SessionStateManager

**Key State Variables:**

**Definition Data:**
- `gegenereerd` - Generated definition text (legacy)
- `definitie_origineel` - Original AI-generated definition
- `definitie_gecorrigeerd` - Cleaned/corrected definition
- `aangepaste_definitie` - User-modified definition
- `marker` - Ontological category marker
- `beoordeling_gen` - Validation results from generation
- `beoordeling` - Current validation results

**Context Data:**
- `global_context` - Dict with org/jur/wet context for generation
- `context` (legacy) - Organizational context
- `juridische_context` - Legal context
- `wet_basis` - Legal basis (wettelijke basis)
- `edit_organisatorische_context` - Edit tab org context
- `edit_juridische_context` - Edit tab jur context
- `edit_wettelijke_basis` - Edit tab wet basis

**Examples & Content:**
- `voorbeeld_zinnen` - Example sentences
- `praktijkvoorbeelden` - Practice examples
- `tegenvoorbeelden` - Counter-examples
- `toelichting` - Explanation/clarification
- `synoniemen` - Synonyms
- `antoniemen` - Antonyms
- `voorkeursterm` - Preferred term
- `bronnen_gebruikt` - Sources used

**UI State:**
- `toon_ai_toetsing` - Show AI validation
- `toon_toetsing_hercontrole` - Show validation recheck
- `override_actief` - Forbidden words override active
- `override_verboden_woorden` - Custom forbidden words list

**Metadata:**
- `datum_voorstel` - Proposal date
- `voorgesteld_door` - Proposed by
- `ketenpartners` - Chain partners (list)
- `ufo_categorie` - UFO category (OntoUML/UFO)

**Edit Tab State:**
- `editing_definition_id` - ID of definition being edited
- `editing_definition` - Definition object being edited
- `edit_session` - Edit session metadata
- `edit_search_results` - Search results in edit tab
- `last_auto_save` - Auto-save timestamp
- `auto_save_enabled` - Auto-save toggle

**Generation State:**
- `last_generation_result` - Complete generation result dict
- `last_check_result` - Duplicate check result
- `generation_options` - Options for generation (force flags, etc.)

**Document Upload:**
- `selected_documents` - IDs of selected documents for context
- `documents_updated` - Flag for document list refresh

**Service Initialization:**
- Services initialized via `initialize_services_once()` with caching
- Prevents 6x re-initialization on Streamlit reruns

---

## Tab Business Logic

### 1. DefinitieGenerator Tab

**File:** `src/ui/components/definition_generator_tab.py`

**Workflow Steps:**

1. **Display Last Generation Results**
   - Checks `last_generation_result` in session state
   - Shows begrip, determined category, reasoning
   - Displays validation results (V2 format)
   - Shows definition (original + cleaned)
   - Renders examples block
   - Document context summary if applicable

2. **Check Result Display**
   - Shows duplicate check warnings
   - Offers options: "Show existing" or "Force generate"
   - Uses `CheckAction` enum for decision flow

3. **Validation Display (V2)**
   - Uses `render_validation_detailed_list()` component
   - Groups rules by category (CON, ESS, STR, etc.)
   - Shows violations with severity icons
   - Expandable passed rules section
   - Gate status indicators (pass/override/blocked)

**Business Rules:**

**Generation Trigger:**
- Requires `begrip` to be filled
- Validates at least one context (org/jur/wet)
- Optional: UFO category selection
- Optional: Document selection for hybrid context

**Duplicate Gate:**
- If NOT forced: Run duplicate check first
- Compares on: begrip + org context + jur context + wet basis + category
- Action outcomes:
  - `PROCEED` - No duplicates, continue
  - `USE_EXISTING` - Exact match found, show option
  - `UPDATE_EXISTING` - Draft exists, suggest update
  - `USER_CHOICE` - Similar found, let user decide

**Ontological Category Determination:**
- Tries 6-step OntologischeAnalyzer first
- Falls back to QuickOntologischeAnalyzer on error
- Ultimate fallback: pattern matching (default PROCES)
- Category reasoning displayed to user

**Regeneration (GVI Red Cable):**
- Checks for active regeneration context
- Overrides category if regeneration active
- Clears regeneration context after successful generation
- Updates UI session markers

**Document Context:**
- Aggregates keywords, concepts, legal refs from selected docs
- Builds compact summary (max items limited)
- Extracts snippets: searches for begrip in document text
- Max 1 snippet per doc, configurable via env vars
- Citations include page (PDF) or paragraph (DOCX) numbers

**Save Flow:**
- V2 Orchestrator saves automatically and returns `saved_definition_id`
- Auto-load into Edit tab: sets `editing_definition_id`
- Stores context for Edit tab: `edit_organisatorische_context`, etc.
- Edit tab auto-opens definition with contexts pre-filled

**Force Generation:**
- Sets `generation_options["force_generate"] = True`
- Also sets `force_duplicate = True` to mark duplicate as accepted
- CON-01 will show as error for duplicate
- Clears force flags after generation

**State Transitions:**
```
Input → Duplicate Check → [User Choice if needed] → Generate → Validate → Save → Auto-load Edit
```

### 2. DefinitionEditTab

**File:** `src/ui/components/definition_edit_tab.py`

**Workflow Steps:**

1. **Auto-Load on Entry**
   - Checks for `editing_definition_id` in session
   - Starts edit session automatically
   - Loads contexts from generator if available
   - Shows info message about auto-filled contexts

2. **Definition Search & Selection**
   - Search by: term, status, max results
   - Status options: All, Geïmporteerd, Concept, In review, Vastgesteld, Gearchiveerd
   - Auto-loads most recent if no search performed
   - Table view (selectable) or card view

3. **Rich Text Editor**
   - Scoped widget keys: `edit_{definition_id}_{field_name}`
   - Fields: begrip, definitie, category, UFO category, toelichting
   - Context fields with "Anders..." option for custom values
   - Status field (read-only if established/archived)

4. **Validation**
   - Re-validate button calls ModularValidationService
   - Full-width validation results display
   - Uses shared `render_validation_detailed_list()` component
   - Results stored with definition-scoped key

5. **Version Management**
   - Shows version history in sidebar
   - Revert to version capability
   - Auto-save with throttling (30s interval)
   - Optimistic locking via version numbers

6. **Examples Section**
   - Shared `render_examples_block()` component
   - Allow generate: False (edit mode)
   - Allow edit: True (including voorkeursterm selector)
   - Repository passed for saving

**Business Rules:**

**Edit Permissions:**
- ESTABLISHED: Read-only, show message to change status via Expert tab
- ARCHIVED: Read-only, show message to restore via Expert tab
- Other statuses: Fully editable

**Context Requirements:**
- At least ONE context required (org OR jur OR wet)
- Save button disabled if no context
- Warning shown if requirement not met

**Anders... Custom Values:**
- Multiselect shows known options + "Anders..."
- If "Anders..." selected: text input appears
- Comma-separated custom values
- Final list = known selections + parsed custom values
- Stored in session state with resolved values

**Auto-Save Logic:**
- Enabled via checkbox (default: on)
- Tracks changes by comparing current widget values vs definition fields
- Normalizes context lists for comparison
- Throttles to max 1 save per 30 seconds
- Saves to temporary storage (can be restored)

**Save Flow:**
- Validates context requirement
- Collects all field updates from session state
- Includes version number for optimistic locking
- Optionally validates during save
- Handles version conflicts (shows refresh button)
- Updates metadata (updated_by, timestamp)

**Widget Key Scoping:**
- Format: `edit_{definition_id}_{field_name}`
- Prevents state bleed between definitions
- Auto-hydrates on definition load
- No manual hydration needed

**State Transitions:**
```
Select Definition → Start Session → [Auto-save restore if exists] → Edit → Track Changes → [Auto-save] → Validate → Save → Refresh
```

### 3. ExpertReviewTab

**File:** `src/ui/components/expert_review_tab.py`

**Workflow Steps:**

1. **Prefill Read-Only Context**
   - Shows last generated definition (if available)
   - Read-only display with context
   - Helps expert see what was just created

2. **Forbidden Words Management**
   - Runtime override of forbidden words config
   - Test opschoning feature (preview before apply)
   - Shows standard forbidden words list
   - Status indicator for override state

3. **Review Queue**
   - Filters: search, org context, jur context, wet basis, sort by
   - Shows abbreviations help (from config)
   - Table view (selectable) or card view
   - Status labels in Dutch

4. **Definition Review Interface**
   - Full details panel (expandable)
   - UFO category selector
   - Toelichting proces (review/validation notes)
   - Examples block (no generate, yes edit)
   - Comparison view (original vs edited)
   - Validation issues grouped by severity

5. **Review Actions (US-155)**
   - **Vaststellen (Approve):**
     - Gate preview shows pass/override/blocked
     - Override requires reason in notes
     - Ketenpartners multiselect
     - Auto-saves UFO category on approve
   - **Afwijzen (Reject):**
     - Requires reason (text area)
     - Returns to Draft status
   - **Maak Bewerkbaar (Unlock):**
     - For Established definitions
     - Requires reason
     - Returns to Draft for editing
   - **Herstel (Restore):**
     - For Archived definitions
     - Requires reason
     - Returns to Draft

6. **Re-Validate**
   - Button to re-validate with current rules
   - Calls ValidationOrchestratorV2
   - Full-width V2 validation display
   - Stores result for persistence

**Business Rules:**

**Review Queue Filters:**
- Search: begrip OR definitie text match (case-insensitive)
- Context filters: Set intersection (OR within category, AND between categories)
- Sort options: Date (new/old), Begrip A-Z, Score
- Parses JSON context fields from database

**Gate Policy (US-160):**
- Preview gate BEFORE approve action
- Three outcomes:
  - **Pass:** Green indicator, approve enabled
  - **Override Required:** Yellow indicator, reason required
  - **Blocked:** Red indicator, approve disabled
- Gate checks:
  - At least one context (hard requirement)
  - Validation score ≥ hard threshold (0.75)
  - No critical issues (hard requirement)
  - Soft checks for high issues, missing wet basis

**Approve Flow:**
- Check gate status
- If blocked: Show reasons, disable button
- If override: Require non-empty notes
- Update UFO category if changed
- Call `DefinitionWorkflowService.approve()`
- Update ketenpartners if provided
- Log audit trail, publish event
- Return WorkflowResult with gate status

**Reject Flow:**
- Requires non-empty reason
- Calls `DefinitionWorkflowService.reject()`
- Changes status to DRAFT
- Logs audit trail, publishes event

**Status Transitions:**
```
Review → [Gate Check] → Approve → ESTABLISHED
Review → Reject → DRAFT
Established → Unlock → DRAFT
Archived → Restore → DRAFT
```

**Validation Issues Display:**
- Critical (red): Must be fixed before approve
- High (yellow): Can override with reason
- Other: Expandable section
- Shows rule ID, description, severity

**Comparison View:**
- Side-by-side: Original vs Edited
- Text area for expert edits
- Tracks changes in session state
- Saves edited version on submit

**Submit Review Decision:**
- Collects edited fields (definitie, UFO, toelichting_proces)
- Updates all changes in one DB call
- Routes approval through DefinitionWorkflowService (gate enforcement)
- Shows gate status in feedback

### 4. ImportExportBeheerTab

**File:** `src/ui/components/tabs/import_export_beheer.py`

**Workflow:** (Consolidated import, export, and database management)

**Expected Logic (based on naming):**
1. **Import Section**
   - File upload (JSON format expected)
   - Preview before import
   - Duplicate handling options
   - Bulk import with progress tracking

2. **Export Section**
   - Filter definitions for export
   - Format selection (JSON, CSV, TXT)
   - Batch export functionality
   - Export established definitions only option

3. **Beheer (Management) Section**
   - Database statistics
   - Cleanup operations
   - Archive old drafts
   - Delete functionality with confirmation

**Note:** File not found in glob results, likely separate implementation file.

### 5. MonitoringTab

**File:** `src/ui/components/monitoring_tab.py`

**Expected Monitoring Features:**
1. **Performance Metrics**
   - API call tracking (count, cost, timing)
   - Service performance (generation, validation times)
   - Cache hit/miss rates

2. **Usage Statistics**
   - Definitions created per day/week
   - User activity tracking
   - Popular contexts/categories

3. **System Health**
   - Database size and performance
   - Error rates and types
   - Service availability status

### 6. WebLookupTab

**File:** `src/ui/components/web_lookup_tab.py`

**Expected Features:**
1. **External Search**
   - Wikipedia lookup
   - SRU (library) search
   - Provider weighting configuration

2. **Duplicate Detection**
   - Cross-reference with external sources
   - Similarity scoring
   - Source citation tracking

3. **Context Enrichment**
   - Import external definitions
   - Augment with web sources
   - Provider settings management

---

## Workflow Orchestration

### User Journey Rules

**Complete Definition Lifecycle:**

```
1. CREATION PHASE
   ├─ Input: Begrip + Context (org/jur/wet) + Optional (UFO, documents)
   ├─ Duplicate Check (unless forced)
   ├─ Category Determination (6-step → quick → pattern fallback)
   ├─ Generation via V2 Orchestrator
   ├─ Validation (45 rules, modular)
   ├─ Save with status: REVIEW
   └─ Auto-load into Edit tab

2. EDIT PHASE (Optional)
   ├─ Auto-load from generation OR manual search
   ├─ Edit fields (context, definitie, UFO, etc.)
   ├─ Re-validate as needed
   ├─ Auto-save (30s throttle)
   ├─ Save final version
   └─ Increment version number

3. REVIEW PHASE
   ├─ Expert selects from queue
   ├─ Reviews details, validation, examples
   ├─ Can edit definition directly
   ├─ Re-validate if needed
   ├─ Gate check on approve
   ├─ Actions:
   │  ├─ Approve → ESTABLISHED (if gate passes)
   │  ├─ Approve with override → ESTABLISHED (if override allowed + reason given)
   │  ├─ Reject → DRAFT (requires reason)
   │  └─ Mark for changes → stays REVIEW
   └─ Audit log + event published

4. ESTABLISHED PHASE
   ├─ Read-only in Edit tab
   ├─ Can unlock (Expert tab, requires reason) → DRAFT
   ├─ Available for export
   └─ Visible in repository

5. ARCHIVED PHASE
   ├─ Read-only everywhere
   ├─ Can restore (Expert tab, requires reason) → DRAFT
   └─ Not shown in normal searches
```

### State Machine Logic

**Status Enum:** `DefinitieStatus`
- DRAFT - Concept, editable
- REVIEW - In review, editable by expert
- ESTABLISHED - Approved, read-only
- ARCHIVED - Archived, read-only

**Allowed Transitions (enforced by WorkflowService):**

```
DRAFT → REVIEW       (submit for review)
REVIEW → DRAFT       (reject)
REVIEW → ESTABLISHED (approve, requires gate pass)
ESTABLISHED → DRAFT  (unlock, expert only)
ESTABLISHED → ARCHIVED (archive, admin only)
ARCHIVED → DRAFT     (restore, expert only)
```

**Transition Validation:**
- `WorkflowService.can_change_status(current, target, user_role)` checks rules
- Role-based restrictions (expert, reviewer, admin)
- Audit logging on every transition
- Event publishing (if event bus configured)

### Approval Gates (US-160)

**Gate Policy Architecture:**

**Policy Service:** `GatePolicyService` (injectable)
- Loads policy from config/database
- Provides hard/soft requirements
- Configurable thresholds

**Gate Evaluation (in DefinitionWorkflowService):**

**Hard Requirements (Blocked if violated):**
1. **Context Required:**
   - At least one of: org_context OR jur_context OR wettelijke_basis
   - Blocks if ALL empty

2. **Critical Issues:**
   - No critical severity validation issues allowed
   - Blocks if any critical found

3. **Hard Score Threshold:**
   - Default: 0.75
   - Blocks if score < threshold

4. **Validation Result:**
   - Must have validation_score (not None)
   - Blocks if missing (prompt to re-validate)

**Soft Requirements (Override Required):**
1. **Score Range:**
   - Between soft (0.65) and hard (0.75) thresholds
   - Requires override + reason

2. **High Issues:**
   - High severity issues (no critical)
   - Requires override + reason

3. **Missing Wet Basis:**
   - wettelijke_basis empty
   - Requires override + reason

**Gate Outcomes:**

1. **Pass** (`status: "pass"`)
   - All hard requirements met
   - No soft issues
   - Approve button enabled, no reason required

2. **Override Required** (`status: "override_required"`)
   - Hard requirements met
   - Soft issues present
   - Approve enabled IF reason provided
   - Reason field marked required

3. **Blocked** (`status: "blocked"`)
   - Hard requirement(s) violated
   - Approve button disabled
   - Must fix issues first (or configure override in policy)

**Gate Preview:**
- `DefinitionWorkflowService.preview_gate(definition_id)` returns status + reasons
- UI shows indicator BEFORE user clicks approve
- Helps user know what's needed

**Override Handling:**
- Override requires non-empty notes/reason
- Validated in `approve()` method
- Reason stored in audit trail
- Gate status + reasons included in WorkflowResult

### Error Recovery Workflows

**Generation Failures:**
1. Show error message with details
2. Preserve input (begrip, context) in session
3. Allow retry with same inputs
4. Log error for monitoring

**Validation Failures:**
1. Show validation issues grouped by severity
2. Offer re-generate option (category regeneration)
3. Allow manual editing to fix issues
4. Re-validate after changes

**Save Conflicts (Optimistic Locking):**
1. Detect version mismatch
2. Show conflict message
3. Offer refresh button to reload latest
4. User must re-apply changes manually

**Auto-Save Recovery:**
1. Check for auto-save on edit session start
2. Show "Restore auto-save" button if found
3. User chooses: restore or discard
4. Auto-save cleared after manual save

**Service Unavailable:**
1. Graceful degradation (dummy service)
2. Show clear "service unavailable" message
3. Log warning for ops
4. Allow UI to function in read-only mode

---

## Integration Points

### DefinitieChecker (Duplicate Detection)

**File:** `src/integration/definitie_checker.py`

**Business Logic:**

**Duplicate Check Algorithm:**
1. **Exact Match Search:**
   - Criteria: begrip + org_context + jur_context + wettelijke_basis (order-independent)
   - Category NOT part of duplicate criteria (allows same term, different category)
   - Uses `repository.find_definitie()`

2. **Fuzzy Match Search (if no exact):**
   - Uses `repository.find_duplicates()`
   - Returns matches with similarity scores
   - Sorted by score (highest first)

3. **Decision Logic:**
   - Exact match + ESTABLISHED → `USE_EXISTING`
   - Exact match + DRAFT → `UPDATE_EXISTING`
   - Exact match + other status → `USER_CHOICE`
   - Fuzzy match score > 0.9 → `USER_CHOICE`
   - Fuzzy match score > 0.7 → `USER_CHOICE`
   - Fuzzy match score ≤ 0.7 → `PROCEED` (weak match, safe to generate)

**Generate with Check Flow:**
1. Run duplicate check (unless `force_generate=True`)
2. If duplicates found: return check result + existing definition
3. If no duplicates OR forced: call ServiceAdapter.generate_definition()
4. Parse V2 response (definitie_gecorrigeerd, final_score, validation_details)
5. Save to database with REVIEW status
6. Return: (check_result, agent_result, saved_record)

**Update Existing:**
- Option 1: Simple metadata update (no regenerate)
- Option 2: Full regenerate with same inputs + version increment

**Synonym Detection:**
- Checks if search term differs from found begrip
- Indicates match via synonym rather than exact begrip match
- Enhanced message: "Found via synonym 'X' with equal context"

### DefinitionWorkflowService

**File:** `src/services/definition_workflow_service.py`

**Business Logic:**

**Workflow Transition Methods:**

1. **`submit_for_review(definition_id, user, notes)`**
   - Validates: current_status → REVIEW allowed
   - Updates status in repository atomically
   - Logs audit trail
   - Publishes event: `definition.submitted_for_review`
   - Returns WorkflowResult

2. **`approve(definition_id, user, notes, ketenpartners, user_role)`**
   - Validates: current_status → ESTABLISHED allowed (role-based)
   - **Gate evaluation BEFORE status change**
   - If blocked: return error with reasons
   - If override required: validate notes present
   - Updates status to ESTABLISHED
   - Updates ketenpartners (JSON array)
   - Logs audit trail with gate status
   - Publishes event: `definition.approved`
   - Returns WorkflowResult with gate_status + reasons

3. **`reject(definition_id, user, reason)`**
   - Validates: current_status → DRAFT allowed
   - Requires non-empty reason
   - Updates status to DRAFT
   - Logs audit trail
   - Publishes event: `definition.rejected`
   - Returns WorkflowResult

4. **`update_status(definition_id, new_status, user, notes)`**
   - Generic status change method
   - Converts string to DefinitieStatus enum
   - Delegates to repository.change_status()
   - No workflow validation (direct override)
   - Used for expert unlock/restore actions

**Audit & Events:**
- Audit logger: Records all transitions with user, timestamp, notes
- Event bus: Publishes events for external systems/notifications
- Both optional (dependency injection)

**WorkflowResult Structure:**
```python
@dataclass
class WorkflowResult:
    success: bool
    new_status: str | None
    updated_by: str | None
    notes: str | None
    events: list[str]
    error_message: str | None
    timestamp: datetime
    gate_status: str | None  # pass | override_required | blocked
    gate_reasons: list[str] | None
```

---

## Context Management

### Context Types

1. **Organisatorische Context:**
   - Options from UI config: `organizational_contexts`
   - Stored as JSON array in database
   - Multiselect with "Anders..." for custom values
   - Abbreviations help available in UI

2. **Juridische Context:**
   - Options from UI config: `legal_contexts`
   - Stored as JSON array in database
   - Multiselect with "Anders..." for custom values

3. **Wettelijke Basis:**
   - Options from UI config: `common_laws`
   - Stored as JSON TEXT in database (array)
   - Multiselect with "Anders..." for custom values
   - Retrieved via `get_wettelijke_basis_list()` helper

### Context Selectors

**Enhanced Context Manager Selector:**
- File: `src/ui/components/enhanced_context_manager_selector.py`
- Used globally (top of TabbedInterface)
- Returns dict: `{organisatorische_context: [...], juridische_context: [...], wettelijke_basis: [...]}`
- Stored in `session_state["global_context"]`

**Edit Tab Context:**
- Pre-filled from generator if available (`edit_organisatorische_context`, etc.)
- "Anders..." option for custom values (comma-separated)
- Resolved values stored in session state with definition-scoped keys
- Cleared after auto-load to prevent persistence

**Context Propagation:**
```
Generator → global_context (session) → Generation call → V2 Orchestrator → Database save → Edit tab auto-load (separate keys)
```

### Custom Context Values

**UI Pattern (all tabs):**
1. Multiselect shows: [known options...] + "Anders..."
2. If "Anders..." selected: text input appears
3. User enters comma-separated values
4. On save: `resolved = [known selections] + [parsed custom values]`
5. "Anders..." removed from final list
6. Resolved list stored/saved

**Validation:**
- At least ONE context type required for save (org OR jur OR wet)
- Enforced in Edit tab (save button disabled)
- Enforced in gate policy (hard requirement)

---

## Validation Integration

### V2 Validation Display

**Shared Component:** `render_validation_detailed_list()`
- File: `src/ui/components/validation_view.py`
- Used in: Generator, Edit, Expert tabs
- Input: V2 validation dict (`ValidationDetailsDict`)
- Features:
  - Overall score with color coding
  - Violations grouped by category (CON, ESS, STR, etc.)
  - Passed rules in expandable section
  - Rule info fetched from JSON (name, explanation)
  - Suggestions shown inline
  - Gate status indicators

**Validation Result Structure (V2):**
```python
{
    "version": "1.0.0",
    "overall_score": float,
    "is_acceptable": bool,
    "violations": [
        {
            "rule_id": str,
            "code": str,
            "severity": str,  # critical | high | medium | low
            "message": str,
            "description": str,
            "suggestion": str | None,
            "category": str,
        }
    ],
    "passed_rules": [str],
    "detailed_scores": dict,
    "system": {
        "correlation_id": str,
        ...
    }
}
```

### Validation Triggers

1. **During Generation:**
   - Automatic via V2 Orchestrator
   - Included in generation response
   - Displayed immediately after generation

2. **Manual Re-Validate (Edit Tab):**
   - Button in action section
   - Calls `edit_service._validate_definition()`
   - Falls back to async orchestrator if service returns None
   - Full-width display after validation

3. **Manual Re-Validate (Expert Tab):**
   - "Re-validate" button
   - Builds Definition object from record
   - Calls `ValidationOrchestratorV2.validate_definition()`
   - Stores result with definition-scoped key
   - Full-width display on rerun

### Rule Sorting & Grouping

**Category Order (fixed):**
1. CON - Consistentie
2. ESS - Essentialiteit
3. STR - Structuur
4. INT - Integriteit
5. SAM - Samenhang
6. ARAI - ARAI criteria
7. VER - Verificatie
8. VAL - Validatie (system)

**Within Category:**
- Sort by numeric suffix (CON-01, CON-02, ...)
- Fallback: alphabetical

**Display:**
- Violations shown first (by category)
- Passed rules in expandable section (by category)
- Each rule shows: icon + ID + name + why failed/passed + what it tests

---

## Document Processing

### Upload & Processing

**Workflow:**
1. User uploads files via file_uploader (multiple)
2. Supported types: TXT, PDF, DOCX, DOC, MD, CSV, JSON, HTML, RTF
3. `DocumentProcessor.process_uploaded_file(content, filename, mime_type)`
4. Extraction:
   - Text content
   - Keywords (frequency-based)
   - Concepts (NER/heuristics)
   - Legal references (pattern matching)
   - Context hints (domain-specific)
5. Store in processor cache with ID
6. Display processed documents list

### Document Selection

**UI Flow:**
1. Multiselect shows: `filename (X chars, Y keywords)`
2. Selected IDs stored in `session_state["selected_documents"]`
3. On generation: aggregated context built from selected docs

### Context Aggregation

**Process:**
1. `DocumentProcessor.get_aggregated_context(selected_doc_ids)`
2. Returns:
   ```python
   {
       "document_count": int,
       "total_text_length": int,
       "aggregated_keywords": [str],  # top N, deduplicated
       "aggregated_concepts": [str],  # top N, deduplicated
       "aggregated_legal_refs": [str],  # deduplicated
       "aggregated_context_hints": [str],  # merged
   }
   ```
3. Summary built: compact string with top items
4. Passed to generation as `document_context` parameter

### Snippet Extraction

**Algorithm (US-229):**
1. For each selected document:
   - Search for begrip in extracted text (case-insensitive)
   - Find all matches (regex)
   - For each match (up to `per_doc_max`, default 4):
     - Extract window around match (default 280 chars)
     - Determine citation (page for PDF, paragraph for DOCX)
     - Build snippet dict
2. Total limit: `len(docs) * per_doc_max`
3. Snippet structure:
   ```python
   {
       "provider": "documents",
       "title": filename,
       "filename": filename,
       "doc_id": str,
       "snippet": str,  # text window
       "score": 1.0,
       "used_in_prompt": True,
       "citation_label": str | None,  # "p. 5" or "¶ 12"
   }
   ```

**Citation Labels:**
- PDF: Count `\f` (form feed) to determine page number → "p. N"
- DOCX: Count `\n` to determine paragraph → "¶ N"
- Other: No label

**Env Config:**
- `DOCUMENT_SNIPPETS_PER_DOC` (default: 4)
- `SNIPPET_WINDOW_CHARS` (default: 280)

---

## Examples Management

### Shared Examples Block

**Component:** `render_examples_block()`
- File: `src/ui/components/examples_block.py`
- Used in: Generator, Edit, Expert tabs
- Parameters:
  - `definition`: DefinitieRecord
  - `state_prefix`: Scoped key prefix (e.g., "edit_123")
  - `allow_generate`: Enable AI generation button
  - `allow_edit`: Enable editing + voorkeursterm selector
  - `repository`: For saving changes

**Display Sections:**
1. **Voorbeeldzinnen (Example Sentences):**
   - AI-generated or manual
   - Edit: textarea per example
   - Save changes to database

2. **Praktijkvoorbeelden (Practice Examples):**
   - Real-world usage scenarios
   - Edit: textarea per example
   - Save changes to database

3. **Tegenvoorbeelden (Counter-examples):**
   - Cases where term does NOT apply
   - Edit: textarea per example
   - Save changes to database

4. **Synoniemen (Synonyms):**
   - Alternative terms
   - Edit: textarea, comma-separated
   - Voorkeursterm selector (dropdown)
   - Save preferred term to database

5. **Antoniemen (Antonyms):**
   - Opposite terms
   - Edit: textarea, comma-separated

6. **Toelichting (Explanation):**
   - Additional clarification
   - Edit: textarea
   - Save to database

### Voorkeursterm Logic

**Selector Options:**
- Original begrip (always included)
- All synoniemen (from database)

**Behavior:**
- If user selects begrip: No DB flag set (implicit preferred term)
- If user selects synonym: Save to `voorkeeldsterm` table with definition_id + term
- Display: "Huidige voorkeursterm: [term]"
- Consistent across Generator and Edit tabs

**Database:**
- Table: `voorkeeldsterm` (term, definitie_id)
- Helper: `repository.get_voorkeursterm(definitie_id)` returns term or None
- Helper: `repository.save_voorkeursterm(definitie_id, term)` saves selection

### Generation (if enabled)

**Trigger:** "Genereer voorbeelden" button
- Only in Generator tab (`allow_generate=True`)
- Calls examples generation service
- Updates session state + database
- Reruns to display new examples

---

## Auto-Save & Versioning

### Auto-Save System (Edit Tab)

**Configuration:**
- Toggle: `auto_save_enabled` (checkbox, default: True)
- Throttle: Max 1 save per 30 seconds
- Storage: Temporary `auto_save` record per definition

**Change Detection:**
- Compares widget values vs loaded definition fields
- Fields checked: begrip, definitie, category, UFO, toelichting, contexts (normalized)
- Context lists normalized: sorted, stripped, compared

**Auto-Save Flow:**
1. User edits field → widget value changes
2. `_track_changes()` called (on render)
3. If changed AND 30s elapsed since last auto-save:
4. `_perform_auto_save()` → saves to temporary storage
5. Updates `last_auto_save` timestamp

**Restore:**
- On edit session start: check for auto-save
- If found: show "Restore auto-save" button
- User clicks → `_restore_auto_save(content)` → updates session state → rerun
- Auto-save cleared after manual save

### Version Management

**Version Tracking:**
- Field: `version_number` (integer, incremented on save)
- Field: `previous_version_id` (FK to prior version)
- Table: `definitie_history` (tracks all changes)

**Optimistic Locking:**
- On save: include current `version_number` in update
- Repository checks: WHERE version_number = ?
- If mismatch: version conflict detected
- UI shows error + refresh button

**Version History:**
- Display: Last 10 versions (expandable)
- Shows: summary, date, user, old/new values, reason
- Action: "Herstel" button → reverts to that version
- Revert creates NEW version (no destructive changes)

---

## Configuration & Overrides

### Forbidden Words Management (Expert Tab)

**Purpose:** Configure words to remove from definition start

**UI:**
1. **Current Words Display:**
   - Loads from `config/verboden_woorden.py`
   - Shows as comma-separated text area
   - Editable

2. **Runtime Override:**
   - Checkbox: "Activeer runtime override"
   - When active: uses session state words instead of config
   - Session keys: `override_actief`, `override_verboden_woorden`

3. **Test Section:**
   - Input: test definitie + test begrip
   - Button: "Test Opschoning"
   - Shows: original vs cleaned (side-by-side)
   - Uses: `opschoning.opschonen(definitie, begrip)`

4. **Quick Actions:**
   - "Reset naar standaard" button
   - Clears override, reruns

**Default Words (shown in sidebar):**
- is, zijn, wordt, betekent, omvat, behelst, houdt in, betreft, gaat over, heeft betrekking op, de, het, een, proces waarbij, handeling waarbij, activiteit waarbij, methode waarbij

### Feature Flags

**System:** `config/feature_flags.py`

**UI Toggle:**
- Sidebar: "Feature Flag Toggle" (helper component)
- Shows current V2 service mode
- Allows switching between modes (if available)

**Available Flags:**
- `ENABLE_LEGACY_TAB` - Show legacy Orchestration tab
- V2 service toggles (handled in container)

---

## Error Handling Patterns

### UI Error Display

**Levels:**
1. **Error (st.error):**
   - Red box, critical issues
   - Blocks workflow continuation
   - Shows actionable message

2. **Warning (st.warning):**
   - Yellow box, non-critical
   - Workflow can continue
   - User should be aware

3. **Info (st.info):**
   - Blue box, informational
   - No action required
   - Helpful context

4. **Success (st.success):**
   - Green box, confirmation
   - Action completed successfully

### Error Recovery

**Pattern 1: Retry with Same Inputs**
- Preserve session state on error
- Show error message
- Allow user to retry (same button)
- Example: Generation fails → show error → user clicks generate again

**Pattern 2: Refresh and Retry**
- Conflict detected (version mismatch)
- Show "Refresh" button
- Reload latest from database
- User re-applies changes manually

**Pattern 3: Fallback**
- Primary method fails
- Automatic fallback to alternative
- Log warning
- Example: Enhanced context selector fails → fallback to simplified version

**Pattern 4: Graceful Degradation**
- Service unavailable
- Show dummy/limited functionality
- Clear message to user
- Example: Definition service not available → show read-only mode

### Logging Strategy

**Levels:**
- ERROR: Exceptions, failures, critical issues
- WARNING: Fallbacks, deprecated paths, non-critical issues
- INFO: Normal operations, transitions, key actions
- DEBUG: Detailed flow, state changes (optional)

**Context:**
- Always include: user, definition_id, action
- Include: begrip, context, status for major operations
- Stack traces for exceptions

---

## Key Takeaways

### Business Rules Summary

1. **Duplicate Prevention:**
   - Check before generate (unless forced)
   - Match on: begrip + org + jur + wet basis (category excluded)
   - User choice if similar found

2. **Context Requirements:**
   - At least ONE context (org OR jur OR wet) required
   - Enforced at save and approve gates
   - Custom values via "Anders..." pattern

3. **Validation:**
   - 45 rules in 7 categories
   - V2 modular system
   - Critical issues block approval (hard gate)
   - High issues allow override (soft gate)

4. **Status Workflow:**
   - DRAFT → REVIEW → ESTABLISHED (normal flow)
   - Expert can unlock ESTABLISHED → DRAFT
   - Rejected returns to DRAFT
   - ARCHIVED can be restored to DRAFT

5. **Approval Gates (US-160):**
   - Hard: context + no critical + score ≥ 0.75 + validation present
   - Soft: high issues, missing wet basis, score 0.65-0.75
   - Override requires reason (notes field)

6. **Auto-Load Pattern:**
   - Generator → Edit tab (definition_id + contexts)
   - Contexts auto-filled but cleared after use
   - Seamless user experience

7. **Examples Management:**
   - Shared component across tabs
   - AI generation (Generator only)
   - Manual editing (Edit + Expert)
   - Voorkeursterm selector (synoniemen)

8. **Document Context:**
   - Upload → extract → select → aggregate → generate
   - Snippets with citations
   - Configurable limits

9. **Versioning:**
   - Auto-save with throttle
   - Optimistic locking (version_number)
   - Full history with revert capability

10. **Error Recovery:**
    - Preserve state on failure
    - Offer retry/refresh options
    - Graceful degradation
    - Clear user messaging

### Anti-Patterns Identified

1. **God Object Risk:**
   - `dry_helpers.py` pattern explicitly forbidden
   - Solution: Specific modules per responsibility

2. **Session State Leakage:**
   - Direct `st.session_state` access forbidden
   - Solution: SessionStateManager only

3. **Backwards Compatibility:**
   - NOT a production app
   - Refactor freely, no compat code
   - Document business logic during refactor

4. **Service Re-initialization:**
   - Streamlit reruns cause 6x init
   - Solution: `@st.cache_resource` on container

---

**End of UI/Workflow Extraction**
