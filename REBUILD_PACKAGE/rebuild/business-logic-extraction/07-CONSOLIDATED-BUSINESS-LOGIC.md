# Consolidated Business Logic - Complete Overview

**Project:** DefinitieAgent
**Extraction Date:** 2025-10-02
**Status:** ✅ COMPLETE
**Coverage:** 85% (4,318 LOC extracted from code)

---

## 🎯 Purpose

Dit document bevat ALLE business logica geëxtraheerd uit de DefinitieAgent codebase, geconsolideerd vanuit 6 parallelle agent extracties. Dit is de **single source of truth** voor alle business rules, constraints, workflows, en domain logic.

---

## 📊 High-Level Architectuur

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     DefinitieAgent                          │
│  Nederlandse Juridische Definitiegenerator (AI-gestuurd)   │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐  ┌─────────────────┐  ┌──────────────┐
│  UI Layer     │  │  Services Layer │  │  Data Layer  │
│  (Streamlit)  │  │  (Business)     │  │  (SQLite)    │
└───────────────┘  └─────────────────┘  └──────────────┘
        │                   │                   │
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐  ┌─────────────────┐  ┌──────────────┐
│ • Generator   │  │ • Orchestrators │  │ • definities │
│ • Edit        │  │ • Validation    │  │ • history    │
│ • Review      │  │ • AI Service    │  │ • examples   │
│ • Repository  │  │ • Web Lookup    │  │ • tags       │
│ • Import/Exp  │  │ • Prompts       │  │ • sources    │
└───────────────┘  └─────────────────┘  └──────────────┘
```

### Core Business Flows

```
1. GENERATE FLOW
   Begrip Input → Context Selection → Category Determination →
   Web Lookup (optional) → Prompt Generation → AI Generation →
   Voorbeelden Generation → Text Cleaning → Validation (45 rules) →
   Enhancement → Duplicate Detection → Save → Feedback Loop

2. EDIT FLOW
   Search → Select → Edit (Rich Text) → Context Update →
   Re-validate → Auto-save (30s throttle) → Version History

3. REVIEW FLOW
   Review Queue → Filter → Select → Gate Check (Hard/Soft) →
   Approve/Reject/Unlock → Status Transition → Audit Log

4. WORKFLOW LIFECYCLE
   Imported → Draft → Review → [Gate] → Established → Archived
   (with role-based permissions and approval requirements)
```

---

## 🏗️ LAYER 1: SERVICES & CORE BUSINESS LOGIC

### 1.1 ServiceContainer (Dependency Injection)

**Purpose:** Central dependency injection container (singleton pattern)

**Business Rules:**
- **BR-SVC-001:** ServiceContainer is singleton - één instantie per applicatie
- **BR-SVC-002:** Generator = Orchestrator (UnifiedDefinitionGenerator wraps DefinitionOrchestratorV2)
- **BR-SVC-003:** Config priority: method args > session state > config file > defaults
- **BR-SVC-004:** Validator removed from container (legacy V1)
- **BR-SVC-005:** Web lookup graceful failure (missing dependencies = no lookup)

**Configuration (15+ Feature Flags):**
```python
# Model Selection Hierarchy
DEFAULT_MODEL = "gpt-4"
FALLBACK_MODEL = "gpt-3.5-turbo"

# Temperature Control
DEFAULT_TEMPERATURE = 0.3
CREATIVE_TEMPERATURE = 0.7

# Timeout Settings
AI_TIMEOUT = 30  # seconds
WEB_LOOKUP_TIMEOUT = 10  # seconds

# Rate Limits
RATE_LIMIT_PER_MINUTE = 60
RATE_LIMIT_PER_HOUR = 3000

# Token Limits
MAX_PROMPT_TOKENS = 10000
MAX_RESPONSE_TOKENS = 500

# Validation Settings
MIN_VALIDATION_SCORE = 0.7
ENABLE_AUTO_ENHANCEMENT = True

# Feature Flags
ENABLE_WEB_LOOKUP = True
ENABLE_DOCUMENT_CONTEXT = True
ENABLE_FEEDBACK_LOOP = True
ENABLE_PII_SANITIZATION = True
```

---

### 1.2 DefinitionOrchestratorV2 (Core Orchestrator)

**Purpose:** Hoofd orchestrator voor complete definitie generatie flow (11 fasen)

**God Object Warning:** 800+ LOC - **MUST REFACTOR** in rebuild

**Business Rules (11-Phase Flow):**

#### Phase 1: Security & Privacy
- **BR-ORC-001:** PII sanitization van alle user inputs
- **BR-ORC-002:** Geen hardcoded API keys (environment vars only)
- **BR-ORC-003:** Input validation op begrip (non-empty, max length)

#### Phase 2: Feedback Integration
- **BR-ORC-004:** Load previous feedback voor context continuity
- **BR-ORC-005:** Feedback limited to last 5 interactions
- **BR-ORC-006:** Feedback injection in prompt context

#### Phase 2.5: Web Lookup Enrichment
- **BR-ORC-007:** Web lookup only if ENABLE_WEB_LOOKUP=True
- **BR-ORC-008:** Provider weighting: Wikipedia (0.7), SRU (1.0), ECLI (boost)
- **BR-ORC-009:** Stage-based backoff: quick (5s) → full (10s) → extended (15s)
- **BR-ORC-010:** Graceful failure - continue without web data on timeout

#### Phase 2.9: Document Snippets Merge
- **BR-ORC-011:** Document context only if ENABLE_DOCUMENT_CONTEXT=True
- **BR-ORC-012:** Extract snippets with citations
- **BR-ORC-013:** Env-configurable limits (max snippets, max length)
- **BR-ORC-014:** Merge snippets into prompt context

#### Phase 3: Prompt Generation
- **BR-ORC-015:** Context-aware prompt building (PromptServiceV2)
- **BR-ORC-016:** Ontological mapping based on category
- **BR-ORC-017:** Web lookup augmentation if available
- **BR-ORC-018:** Document snippets injection if available
- **BR-ORC-019:** Token estimation and truncation if > MAX_PROMPT_TOKENS

#### Phase 4: AI Generation
- **BR-ORC-020:** GPT-4 default, fallback to GPT-3.5-turbo on failure
- **BR-ORC-021:** Temperature = 0.3 for consistency (juridisch text)
- **BR-ORC-022:** Rate limiting: 60/min, 3000/hour
- **BR-ORC-023:** Timeout: 30 seconds
- **BR-ORC-024:** Retry with exponential backoff (3 attempts)
- **BR-ORC-025:** Cache responses (15-minute TTL)

#### Phase 5: Voorbeelden Generation
- **BR-ORC-026:** Generate 3-5 voorbeelden per definitie
- **BR-ORC-027:** Voorbeelden types: zinsdeel, volzin, meervoudige_zinnen, alinea, fragment, anders
- **BR-ORC-028:** Normalize types: "zins deel" → "zinsdeel"
- **BR-ORC-029:** Voorkeursterm from synoniemen (if available)

#### Phase 6: Text Cleaning
- **BR-ORC-030:** GPT format detection and removal
- **BR-ORC-031:** Change analysis (track modifications)
- **BR-ORC-032:** Metadata preservation (source, timestamp, version)

#### Phase 7: Validation (45 Rules)
- **BR-ORC-033:** Automatic validation after generation
- **BR-ORC-034:** 7 categories: ARAI, CON, ESS, INT, SAM, STR, VER
- **BR-ORC-035:** Pre-cleaning policy (normalize before validation)
- **BR-ORC-036:** Context enrichment (add metadata for validators)
- **BR-ORC-037:** Error isolation (continue on rule failure)
- **BR-ORC-038:** Batch processing (all rules in parallel)
- **BR-ORC-039:** Score calculation: Σ(passed rules) / Σ(total rules)
- **BR-ORC-040:** Acceptability: score >= MIN_VALIDATION_SCORE (0.7)

#### Phase 8: Enhancement
- **BR-ORC-041:** Auto-enhancement only if ENABLE_AUTO_ENHANCEMENT=True
- **BR-ORC-042:** Enhancement only for low-scoring definitions (<0.7)
- **BR-ORC-043:** Max 3 enhancement attempts
- **BR-ORC-044:** Track enhancement history in metadata

#### Phase 9: Storage
- **BR-ORC-045:** Save via DefinitionRepository.save()
- **BR-ORC-046:** Duplicate detection before save (3-level matching)
- **BR-ORC-047:** Force option to bypass duplicate check
- **BR-ORC-048:** Audit logging (automatic via trigger)
- **BR-ORC-049:** Optimistic locking (version-based)

#### Phase 10: Feedback Loop
- **BR-ORC-050:** Store generation metadata for feedback
- **BR-ORC-051:** Event publishing for monitoring
- **BR-ORC-052:** Performance metrics logging

#### Phase 11: Monitoring
- **BR-ORC-053:** Distributed tracing (trace_id per generation)
- **BR-ORC-054:** Structured logging (JSON format)
- **BR-ORC-055:** Business metrics (success rate, validation scores)

---

### 1.3 ValidationOrchestratorV2

**Purpose:** Orchestrate 45+ validation rules across 7 categories

**Business Rules:**
- **BR-VAL-ORC-001:** Pre-cleaning policy (normalize text before validation)
- **BR-VAL-ORC-002:** Context enrichment (add begrip, context metadata)
- **BR-VAL-ORC-003:** Error isolation (rule failure doesn't stop batch)
- **BR-VAL-ORC-004:** Batch processing (all rules evaluated)
- **BR-VAL-ORC-005:** Deterministic evaluation order (priority: high → medium → low)
- **BR-VAL-ORC-006:** Score calculation: passed / total
- **BR-VAL-ORC-007:** Acceptability threshold: 0.7 (70%)

---

### 1.4 PromptServiceV2

**Purpose:** Modulaire prompt building met context-aware templates

**Business Rules:**
- **BR-PROMPT-001:** Context manager integration (org/jur/wet)
- **BR-PROMPT-002:** Ontological mapping based on category (11 categories)
- **BR-PROMPT-003:** Web lookup augmentation (inject external data)
- **BR-PROMPT-004:** Document snippets injection (with citations)
- **BR-PROMPT-005:** Token estimation (tiktoken library)
- **BR-PROMPT-006:** Truncation if > MAX_PROMPT_TOKENS (10K)
- **BR-PROMPT-007:** Template caching (@st.cache_data)

**Prompt Structure:**
```
System Message:
- Role definition (juridisch expert)
- Task description (definitie generatie)
- Quality criteria (duidelijk, precies, consistent)

User Message:
- Begrip + Context
- Ontological category guidance
- Web lookup data (if available)
- Document snippets (if available)
- Previous feedback (if available)
```

---

### 1.5 AIServiceV2 (GPT-4 Integration)

**Purpose:** GPT-4 API integratie met rate limiting en caching

**Business Rules:**
- **BR-AI-001:** Default model: GPT-4 (gpt-4)
- **BR-AI-002:** Fallback model: GPT-3.5-turbo
- **BR-AI-003:** Temperature: 0.3 (juridisch text requires consistency)
- **BR-AI-004:** Rate limiting: 60 requests/min, 3000 requests/hour
- **BR-AI-005:** Timeout: 30 seconds
- **BR-AI-006:** Retry logic: Exponential backoff (3 attempts: 1s, 2s, 4s)
- **BR-AI-007:** Token estimation: tiktoken cl100k_base encoding
- **BR-AI-008:** Response caching: 15-minute TTL
- **BR-AI-009:** Error handling: RateLimitError → wait, APIError → fallback
- **BR-AI-010:** Logging: Structured JSON with trace_id

**Rate Limiting Algorithm:**
```python
# Token bucket algorithm
bucket_capacity = 60  # requests
refill_rate = 1  # request per second
hourly_limit = 3000

# Check both per-minute and per-hour limits
if requests_last_minute >= 60:
    wait_time = 60 - (now - oldest_request)
    raise RateLimitError(retry_after=wait_time)

if requests_last_hour >= 3000:
    wait_time = 3600 - (now - oldest_hour_request)
    raise RateLimitError(retry_after=wait_time)
```

---

### 1.6 ModernWebLookupService

**Purpose:** Externe bron integratie (Wikipedia, SRU, ECLI)

**Business Rules:**
- **BR-WEB-001:** Provider prioritization: ECLI (boost if legal context) > SRU (1.0) > Wikipedia (0.7)
- **BR-WEB-002:** Stage-based backoff:
  - Quick: 5s timeout
  - Full: 10s timeout
  - Extended: 15s timeout (only for critical terms)
- **BR-WEB-003:** ECLI boost: +0.3 weight if context = "wet" or "jur"
- **BR-WEB-004:** Legal metadata extraction:
  - Instantie (rechtbank, hof, etc.)
  - Datum uitspraak
  - Zaaknummer
  - Rechtsgebied
- **BR-WEB-005:** Graceful failure: Return empty results on timeout (don't block generation)
- **BR-WEB-006:** Result ranking: Relevance score = provider_weight × content_quality
- **BR-WEB-007:** Deduplication: Same source URL = merge results
- **BR-WEB-008:** Max results: 5 per provider (configurable)
- **BR-WEB-009:** Snippet extraction: Max 500 chars per result
- **BR-WEB-010:** Citation format: "[Source: {provider} - {title}]"

**Source Ranking Algorithm:**
```python
def rank_sources(results, context, begrip):
    for result in results:
        base_weight = PROVIDER_WEIGHTS[result.provider]

        # ECLI boost for legal contexts
        if result.provider == "ecli" and context in ["wet", "jur"]:
            base_weight += 0.3

        # Content quality score (0.0-1.0)
        quality = calculate_quality(result.content, begrip)

        # Final relevance score
        result.relevance = base_weight * quality

    # Sort by relevance (descending)
    return sorted(results, key=lambda r: r.relevance, reverse=True)
```

---

### 1.7 ModularValidationService

**Purpose:** 45+ validatieregels management en execution

**Business Rules:**
- **BR-MODVAL-001:** Rule loading strategy: JSON metadata + Python implementation
- **BR-MODVAL-002:** Baseline rules (always applied): ARAI-001, CON-001, ESS-001, SAM-001, STR-001
- **BR-MODVAL-003:** Deterministic evaluation order: Priority (high → medium → low) → Category → Rule ID
- **BR-MODVAL-004:** Score calculation: Σ(passed) / Σ(applicable)
- **BR-MODVAL-005:** Acceptability determination: score >= 0.7
- **BR-MODVAL-006:** Rule caching: @st.cache_data for performance
- **BR-MODVAL-007:** Error isolation: Rule exception = mark as failed, continue batch

**Validation Workflow:**
```
1. Load rules from config/toetsregels/regels/
2. Filter applicable rules (based on context, category)
3. Sort by priority (high → medium → low)
4. Execute batch (parallel where possible)
5. Aggregate results (pass/fail per rule)
6. Calculate score (passed / total)
7. Determine acceptability (>= 0.7)
8. Return ValidationResult object
```

---

### 1.8 DefinitionRepository

**Purpose:** Data access layer voor definities (CRUD operations)

**Business Rules:**
- **BR-REPO-001:** Save strategy: Insert new OR update existing (based on ID)
- **BR-REPO-002:** Duplicate detection integration (3-level matching)
- **BR-REPO-003:** Force option to bypass duplicate check
- **BR-REPO-004:** Soft delete (status = "archived", not physical delete)
- **BR-REPO-005:** Search logic:
  - Begrip: Substring match (LIKE %term%)
  - Context: Exact match OR IN (multi-select)
  - Category: Exact match
  - Status: Exact match OR IN (multi-select)
- **BR-REPO-006:** Pagination: Default page size = 20
- **BR-REPO-007:** Sorting: Created date DESC (newest first)
- **BR-REPO-008:** UTF-8 encoding: All text operations use UTF-8
- **BR-REPO-009:** Transaction management: Atomic operations (rollback on error)
- **BR-REPO-010:** Audit logging: Automatic via trigger (log_definitie_changes)

---

### 1.9 DuplicateDetectionService

**Purpose:** 3-level duplicate detection algorithm

**Business Rules:**
- **BR-DUP-001:** Level 1 (Exact Match): begrip match (case-insensitive)
- **BR-DUP-002:** Level 2 (Synonym Match): Check definitie_synoniemen table
- **BR-DUP-003:** Level 3 (Fuzzy Match): Jaccard similarity >= 0.7
- **BR-DUP-004:** Wettelijke basis normalization: Order-independent comparison (sort + unique)
- **BR-DUP-005:** Context consideration: Same begrip + different context = NOT duplicate
- **BR-DUP-006:** Risk assessment:
  - Exact match: HIGH risk
  - Synonym match: MEDIUM risk
  - Fuzzy match: LOW risk
- **BR-DUP-007:** Force option: User can override duplicate check

**Jaccard Similarity Algorithm:**
```python
def jaccard_similarity(text1, text2):
    # Tokenize and normalize
    tokens1 = set(normalize(text1).split())
    tokens2 = set(normalize(text2).split())

    # Jaccard coefficient
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    if not union:
        return 0.0

    return len(intersection) / len(union)

# Duplicate if similarity >= 0.7
is_duplicate = jaccard_similarity(def1, def2) >= 0.7
```

---

### 1.10 CleaningService

**Purpose:** Text cleaning en normalization

**Business Rules:**
- **BR-CLEAN-001:** GPT format detection: Detect patterns like "Definitie:", "Toelichting:", etc.
- **BR-CLEAN-002:** Change analysis: Track what was cleaned (metadata)
- **BR-CLEAN-003:** Metadata preservation: Keep source, timestamp, version
- **BR-CLEAN-004:** Whitespace normalization: Multiple spaces → single space
- **BR-CLEAN-005:** Unicode normalization: NFC form (for Dutch characters)
- **BR-CLEAN-006:** Line break normalization: \r\n → \n
- **BR-CLEAN-007:** Trim leading/trailing whitespace

---

### 1.11 WorkflowService

**Purpose:** Status transitions en role-based permissions

**Business Rules:**
- **BR-WORK-001:** Status transition rules:
  ```
  imported → draft (always allowed)
  draft → review (requires: validation score >= 0.7)
  review → established (requires: approval via gate check)
  established → archived (requires: role = admin)
  archived → draft (unlock, requires: role = admin)
  ```
- **BR-WORK-002:** Role-based permissions:
  - **User:** Create, edit draft, submit for review
  - **Reviewer:** Approve, reject, request changes
  - **Admin:** Archive, unlock, manage config
- **BR-WORK-003:** Approval metadata:
  - approved_by (user ID)
  - approved_at (timestamp)
  - approval_reason (optional note)
- **BR-WORK-004:** Archive metadata:
  - archived_by
  - archived_at
  - archive_reason
- **BR-WORK-005:** Event publishing: Status change → event log
- **BR-WORK-006:** Audit trail: All transitions logged (definitie_geschiedenis)

---

### 1.12 GatePolicyService (EPIC-016)

**Purpose:** Approval gate policy voor Vaststellen (review → established)

**Business Rules:**
- **BR-GATE-001:** Policy loading hierarchy: DB > config file > defaults
- **BR-GATE-002:** TTL caching: 5-minute cache for performance
- **BR-GATE-003:** Typed access: Strongly-typed policy objects
- **BR-GATE-004:** Hard requirements (BLOCKED if violated):
  - Validation score >= threshold (e.g., 0.8)
  - No high-priority rule failures
  - Begrip is non-empty
  - At least one context selected
- **BR-GATE-005:** Soft requirements (OVERRIDE REQUIRED if violated):
  - Toelichting_proces is filled
  - Voorbeelden exist (at least 1)
  - UFO category assigned
  - Wettelijke_basis is filled
- **BR-GATE-006:** Override requires reason: Must provide justification
- **BR-GATE-007:** Gate preview: UI can query gate outcome before submit
- **BR-GATE-008:** Audit logging: Gate decisions logged (including overrides)

**Gate Decision Logic:**
```python
def evaluate_gate(definition, policy):
    outcome = GateOutcome()

    # Check hard requirements (BLOCKING)
    for req in policy.hard_requirements:
        if not req.evaluate(definition):
            outcome.status = "BLOCKED"
            outcome.blocking_issues.append(req.message)

    # Check soft requirements (OVERRIDE REQUIRED)
    for req in policy.soft_requirements:
        if not req.evaluate(definition):
            outcome.status = max(outcome.status, "OVERRIDE_REQUIRED")
            outcome.soft_issues.append(req.message)

    # If no issues, gate passes
    if outcome.status is None:
        outcome.status = "PASS"

    return outcome
```

---

## 🗄️ LAYER 2: DATABASE SCHEMA & BUSINESS RULES

### 2.1 Database Overview

**Database:** SQLite 3.x
**Location:** `data/definities.db`
**Encoding:** UTF-8 (critical for Dutch legal text)
**Tables:** 8 core tables

**ER Diagram (Textual):**
```
definities (1) ──< (N) definitie_geschiedenis [audit trail]
definities (1) ──< (N) definitie_voorbeelden [examples]
definities (1) ──< (N) definitie_tags [many-to-many]
definities (1) ──< (N) externe_bronnen [web lookup results]
definities (1) ──< (N) definitie_synoniemen [synonym lookup]

import_export_logs [operational audit]
validation_config [rule configuration]
```

---

### 2.2 definities Table (Core Table)

**Purpose:** Primary storage voor juridische definities

**Schema:**
```sql
CREATE TABLE definities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    begrip TEXT NOT NULL,
    definitie TEXT NOT NULL,
    voorkeursterm TEXT,  -- Single source of truth
    synoniemen TEXT,     -- JSON array
    toelichting TEXT,
    context TEXT,        -- org/jur/wet
    category TEXT,       -- 11 ontological categories
    subcategorie TEXT,
    wettelijke_basis TEXT,  -- JSON array (order-independent)
    ketenpartners TEXT,     -- JSON array
    validation_issues TEXT, -- JSON array (validation results)
    external_sources TEXT,  -- JSON array (web lookup citations)
    ufo_category TEXT,      -- UFO classification
    toelichting_proces TEXT,-- Review process notes
    status TEXT DEFAULT 'draft',  -- 5-stage workflow
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,  -- Optimistic locking
    UNIQUE(begrip, context)     -- Unique constraint
);
```

**Business Rules:**

#### BR-DB-001: 11-Category Ontological Classification
```
Categories:
1. Rol (persoon, organisatie, rol in proces)
2. Proces (activiteit, procedure)
3. Object (fysiek object, document, product)
4. Locatie (plaats, ruimte)
5. Tijd (tijdseenheid, periode)
6. Eigenschap (attribuut, kwaliteit)
7. Relatie (verbinding tussen entiteiten)
8. Gebeurtenis (event, incident)
9. Regel (wet, verordening, policy)
10. Informatie (data, kennis)
11. Anders (catch-all)
```

#### BR-DB-002: 5-Stage Status Workflow
```sql
-- Status values (ENUM-like constraint via CHECK)
status IN ('imported', 'draft', 'review', 'established', 'archived')

-- Transitions (enforced by WorkflowService)
imported → draft (always)
draft → review (requires validation score >= 0.7)
review → established (requires gate pass)
established → archived (admin only)
archived → draft (unlock, admin only)
```

#### BR-DB-003: Context Values (CHECK constraint)
```sql
context IN ('org', 'jur', 'wet')
-- At least one required (enforced by application layer)
```

#### BR-DB-004: Category Values (CHECK constraint)
```sql
category IN (
    'rol', 'proces', 'object', 'locatie', 'tijd',
    'eigenschap', 'relatie', 'gebeurtenis', 'regel',
    'informatie', 'anders'
)
```

#### BR-DB-005: Unique Constraint
```sql
UNIQUE(begrip, context)
-- Same begrip can exist in multiple contexts (org, jur, wet)
-- But only ONCE per context
```

#### BR-DB-006: JSON Array Storage for Multi-value Fields
```sql
-- synoniemen: ["term1", "term2", "term3"]
-- wettelijke_basis: ["wet1", "wet2"]
-- ketenpartners: ["partner1", "partner2"]
-- validation_issues: [{"rule": "ARAI-001", "status": "failed"}]
-- external_sources: [{"provider": "wikipedia", "title": "..."}]

-- Storage: TEXT column with JSON encoding
-- Retrieval: JSON_EXTRACT() for queries
-- Comparison: Normalize (sort + unique) before compare
```

#### BR-DB-007: Default Values
```sql
status = 'draft'
version = 1
created_at = CURRENT_TIMESTAMP
updated_at = CURRENT_TIMESTAMP
```

#### BR-DB-008: Cascade Delete Behavior
```sql
-- When definitie deleted:
-- - CASCADE delete voorbeelden (foreign key)
-- - CASCADE delete tags (foreign key)
-- - CASCADE delete externe_bronnen (foreign key)
-- - CASCADE delete synoniemen (foreign key)
-- - PRESERVE geschiedenis (audit trail)
```

#### BR-DB-009: Voorkeursterm Single Source of Truth
```sql
-- voorkeursterm is THE canonical term
-- begrip might be a synonym pointing to voorkeursterm
-- If voorkeursterm IS NULL, begrip IS the preferred term
-- UI shows voorkeursterm (if exists), fallback to begrip
```

#### BR-DB-010: 3-Level Duplicate Detection
```sql
-- Level 1: Exact match (begrip)
SELECT * FROM definities WHERE LOWER(begrip) = LOWER(:begrip) AND context = :context

-- Level 2: Synonym match
SELECT d.* FROM definities d
JOIN definitie_synoniemen s ON d.id = s.definitie_id
WHERE LOWER(s.synoniem) = LOWER(:begrip) AND d.context = :context

-- Level 3: Fuzzy match (Jaccard similarity >= 0.7)
-- Implemented in application layer (DuplicateDetectionService)
```

#### BR-DB-011: Wettelijke Basis Normalization (Order-Independent)
```sql
-- For duplicate detection, normalize:
-- ["wet2", "wet1"] === ["wet1", "wet2"]  (order doesn't matter)

-- Normalization algorithm:
-- 1. Parse JSON array
-- 2. Strip whitespace from each item
-- 3. Convert to lowercase
-- 4. Remove duplicates (unique)
-- 5. Sort alphabetically
-- 6. Compare

-- Example:
-- Input 1: '["AVG", "Wbp"]'  →  ["avg", "wbp"]
-- Input 2: '["Wbp", "AVG"]'  →  ["avg", "wbp"]
-- Result: MATCH (duplicates)
```

---

### 2.3 definitie_geschiedenis Table (Audit Trail)

**Purpose:** Volledig audit trail van alle wijzigingen

**Schema:**
```sql
CREATE TABLE definitie_geschiedenis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER NOT NULL,
    begrip TEXT,
    definitie_tekst TEXT,
    change_type TEXT NOT NULL,  -- created/updated/status_changed/approved/archived/auto_save
    changed_by TEXT,
    change_reason TEXT,
    context_snapshot TEXT,  -- JSON snapshot of full definitie at time of change
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (definitie_id) REFERENCES definities(id) ON DELETE CASCADE
);
```

**Business Rules:**

#### BR-HIST-001: Automatic Audit Logging (Trigger)
```sql
-- Trigger: log_definitie_changes
-- Fires on: INSERT, UPDATE on definities table
-- Action: INSERT INTO definitie_geschiedenis

CREATE TRIGGER log_definitie_changes
AFTER INSERT OR UPDATE ON definities
FOR EACH ROW
BEGIN
    INSERT INTO definitie_geschiedenis (
        definitie_id, begrip, definitie_tekst, change_type, context_snapshot, created_at
    ) VALUES (
        NEW.id,
        NEW.begrip,
        NEW.definitie,
        CASE
            WHEN OLD.id IS NULL THEN 'created'
            WHEN OLD.status != NEW.status THEN 'status_changed'
            ELSE 'updated'
        END,
        json_object(
            'begrip', NEW.begrip,
            'definitie', NEW.definitie,
            'context', NEW.context,
            'category', NEW.category,
            'status', NEW.status,
            'version', NEW.version
        ),
        CURRENT_TIMESTAMP
    );
END;
```

#### BR-HIST-002: Context Snapshot (Full State)
```sql
-- JSON snapshot includes:
{
    "begrip": "...",
    "definitie": "...",
    "context": "org",
    "category": "rol",
    "status": "draft",
    "version": 3,
    "synoniemen": ["term1", "term2"],
    "wettelijke_basis": ["wet1"],
    "voorkeursterm": "..."
}
-- Allows full state reconstruction at any point in time
```

#### BR-HIST-003: Change Types (6 Types)
```sql
change_type IN (
    'created',         -- Initial creation
    'updated',         -- Field updates
    'status_changed',  -- Workflow status transition
    'approved',        -- Review approval
    'archived',        -- Archival
    'auto_save'        -- Auto-save in Edit tab
)
```

#### BR-HIST-004: History Retention
```sql
-- Retention policy: INDEFINITE
-- History is NEVER deleted (even when definitie is deleted)
-- Exception: Physical CASCADE delete when definitie removed
-- Recommendation: Archive old history to separate table after 2 years
```

---

### 2.4 definitie_voorbeelden Table (Examples)

**Purpose:** Opslag van voorbeelden per definitie

**Schema:**
```sql
CREATE TABLE definitie_voorbeelden (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER NOT NULL,
    type TEXT NOT NULL,  -- 6 types
    text TEXT NOT NULL,
    bron TEXT,
    voorkeursterm TEXT,  -- Voor welke term dit voorbeeld geldt
    source_type TEXT DEFAULT 'user',  -- user/ai/imported
    is_active BOOLEAN DEFAULT 1,
    assessment TEXT,  -- JSON: {score, validated_by, validated_at}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (definitie_id) REFERENCES definities(id) ON DELETE CASCADE
);
```

**Business Rules:**

#### BR-VOOR-001: 6 Example Types (with Normalization)
```sql
-- Valid types:
type IN (
    'zinsdeel',             -- Fragment van zin
    'volzin',               -- Complete zin
    'meervoudige_zinnen',   -- Meerdere zinnen
    'alinea',               -- Volledige alinea
    'fragment',             -- Tekstfragment
    'anders'                -- Catch-all
)

-- Normalization mapping (application layer):
"zins deel" → "zinsdeel"
"hele zin" → "volzin"
"meerdere zinnen" → "meervoudige_zinnen"
```

#### BR-VOOR-002: Active Example Replacement Strategy
```sql
-- When new examples generated:
-- 1. Mark ALL existing is_active=1 examples as is_active=0
UPDATE definitie_voorbeelden
SET is_active = 0
WHERE definitie_id = :id AND voorkeursterm = :term

-- 2. Insert new examples with is_active=1
INSERT INTO definitie_voorbeelden (definitie_id, type, text, is_active, ...)
VALUES (:id, :type, :text, 1, ...)

-- Reason: Keep history, but only show latest active set
```

#### BR-VOOR-003: Voorkeursterm-Based Lookup
```sql
-- Examples are linked to voorkeursterm, NOT begrip
-- If begrip is a synonym, lookup by voorkeursterm

-- Query:
SELECT * FROM definitie_voorbeelden
WHERE definitie_id = :id
  AND voorkeursterm = :voorkeursterm
  AND is_active = 1
ORDER BY created_at DESC
```

#### BR-VOOR-004: Source Type Tracking
```sql
source_type IN ('user', 'ai', 'imported')

-- user: Manually entered by user
-- ai: Generated by AIServiceV2
-- imported: Imported from external source (CSV, etc.)
```

#### BR-VOOR-005: Assessment JSON Structure
```json
{
    "score": 0.85,              // Quality score (0.0-1.0)
    "validated_by": "user123",  // User ID
    "validated_at": "2025-10-02T14:30:00Z",
    "comments": "Excellent example, very clear"
}
```

#### BR-VOOR-006: Example Upsert Logic (LOC 1368-1805 in definitie_repository.py)
```python
def upsert_voorbeelden(definitie_id, voorbeelden_data):
    # 1. Type normalization
    for voorbeeld in voorbeelden_data:
        voorbeeld['type'] = normalize_type(voorbeeld['type'])

    # 2. Deactivate existing active examples
    db.execute(
        "UPDATE definitie_voorbeelden SET is_active = 0 "
        "WHERE definitie_id = ? AND voorkeursterm = ?",
        (definitie_id, voorkeursterm)
    )

    # 3. Insert new examples
    for voorbeeld in voorbeelden_data:
        db.execute(
            "INSERT INTO definitie_voorbeelden "
            "(definitie_id, type, text, voorkeursterm, is_active, source_type) "
            "VALUES (?, ?, ?, ?, 1, ?)",
            (definitie_id, voorbeeld['type'], voorbeeld['text'],
             voorkeursterm, voorbeeld.get('source_type', 'user'))
        )
```

#### BR-VOOR-007: Automatic Timestamp Update (Trigger)
```sql
CREATE TRIGGER update_voorbeelden_timestamp
AFTER UPDATE ON definitie_voorbeelden
FOR EACH ROW
BEGIN
    UPDATE definitie_voorbeelden
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;
```

#### BR-VOOR-008: Voorkeursterm Handling
```sql
-- If voorkeursterm IS NULL in definitie:
--   voorkeursterm = begrip (fallback)
-- Else:
--   voorkeursterm = definities.voorkeursterm

-- Ensures examples always linked to canonical term
```

---

### 2.5 definitie_tags Table (Many-to-Many)

**Purpose:** Tags voor categorisatie en filtering

**Schema:**
```sql
CREATE TABLE definitie_tags (
    definitie_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (definitie_id, tag),
    FOREIGN KEY (definitie_id) REFERENCES definities(id) ON DELETE CASCADE
);
```

**Business Rules:**

#### BR-TAG-001: Many-to-Many Relationship
```sql
-- One definitie can have multiple tags
-- One tag can apply to multiple definities
-- Junction table pattern
```

#### BR-TAG-002: Tag Normalization
```sql
-- Application layer normalization:
-- 1. Trim whitespace
-- 2. Lowercase
-- 3. Remove duplicates

-- Example:
-- Input: "  Privacy  ", "PRIVACY", "privacy"
-- Stored: "privacy" (once)
```

#### BR-TAG-003: Cascade Delete
```sql
-- When definitie deleted, CASCADE delete all tags
ON DELETE CASCADE
```

---

### 2.6 externe_bronnen Table (Web Lookup Results)

**Purpose:** Storage van externe bron integratie resultaten

**Schema:**
```sql
CREATE TABLE externe_bronnen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER,
    begrip TEXT NOT NULL,
    source_type TEXT NOT NULL,  -- wikipedia/sru/ecli
    title TEXT,
    snippet TEXT,
    url TEXT,
    relevance_score REAL,
    metadata TEXT,  -- JSON (legal metadata for ECLI)
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (definitie_id) REFERENCES definities(id) ON DELETE SET NULL
);
```

**Business Rules:**

#### BR-EXT-001: 5 Source Types
```sql
source_type IN ('wikipedia', 'sru', 'ecli', 'wetten.nl', 'manual')
```

#### BR-EXT-002: Relevance Score Calculation
```sql
-- Score = provider_weight × content_quality
-- provider_weight:
--   - ECLI: 1.0 (1.3 if legal context)
--   - SRU: 1.0
--   - Wikipedia: 0.7
--   - Manual: 1.0

-- content_quality: 0.0-1.0 based on:
--   - Begrip mention frequency
--   - Context keyword matches
--   - Snippet length/completeness
```

#### BR-EXT-003: ECLI Metadata JSON Structure
```json
{
    "instantie": "Rechtbank Amsterdam",
    "datum_uitspraak": "2024-03-15",
    "zaaknummer": "C/13/123456",
    "rechtsgebied": "Bestuursrecht",
    "procedure": "Eerste aanleg",
    "vindplaatsen": ["AB 2024/123"]
}
```

#### BR-EXT-004: NULL definitie_id (Orphaned Sources)
```sql
-- ON DELETE SET NULL allows externe_bronnen to persist
-- even if definitie is deleted (for historical lookups)
-- Alternative: ON DELETE CASCADE to remove entirely
```

#### BR-EXT-005: Duplicate Prevention
```sql
-- Unique constraint on (definitie_id, url)
-- Prevents same source URL stored multiple times
CREATE UNIQUE INDEX idx_externe_bronnen_unique
ON externe_bronnen(definitie_id, url);
```

---

### 2.7 import_export_logs Table (Operational Audit)

**Purpose:** Audit trail voor import/export operaties

**Schema:**
```sql
CREATE TABLE import_export_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_type TEXT NOT NULL,  -- import/export
    format TEXT,  -- csv/json/yaml/xml
    file_name TEXT,
    records_processed INTEGER,
    records_succeeded INTEGER,
    records_failed INTEGER,
    error_log TEXT,  -- JSON array of errors
    performed_by TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Business Rules:**

#### BR-LOG-001: Operation Types
```sql
operation_type IN ('import', 'export', 'bulk_update', 'bulk_delete')
```

#### BR-LOG-002: Format Types
```sql
format IN ('csv', 'json', 'yaml', 'xml', 'excel')
```

#### BR-LOG-003: Error Log JSON Structure
```json
[
    {
        "row": 5,
        "error": "Duplicate begrip 'test' in context 'org'",
        "severity": "error"
    },
    {
        "row": 12,
        "error": "Missing required field 'definitie'",
        "severity": "error"
    }
]
```

#### BR-LOG-004: Success Rate Calculation
```sql
success_rate = records_succeeded / records_processed
-- Display in UI as percentage
```

---

### 2.8 validation_config Table (Rule Configuration)

**Purpose:** Runtime configuratie van validatieregels

**Schema:**
```sql
CREATE TABLE validation_config (
    rule_id TEXT PRIMARY KEY,  -- ARAI-001, CON-001, etc.
    is_enabled BOOLEAN DEFAULT 1,
    priority TEXT DEFAULT 'medium',  -- high/medium/low
    threshold REAL,  -- Rule-specific threshold (if applicable)
    custom_params TEXT,  -- JSON for rule-specific config
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Business Rules:**

#### BR-VALCONF-001: Dynamic Rule Enabling
```sql
-- Rules can be enabled/disabled at runtime
-- Affects validation execution in ModularValidationService
SELECT * FROM validation_config WHERE is_enabled = 1
```

#### BR-VALCONF-002: Priority Override
```sql
-- Priority can be changed from JSON default
-- Affects evaluation order in ValidationOrchestratorV2
priority IN ('high', 'medium', 'low')
```

#### BR-VALCONF-003: Custom Params JSON
```json
{
    "max_length": 500,          // For STR-LEN rules
    "forbidden_words": ["..."], // For CON-FORB rules
    "similarity_threshold": 0.7 // For duplicate detection
}
```

---

## ✅ LAYER 3: VALIDATION RULES (45+)

### 3.1 Validation Overview

**Total Rules:** 45+
**Categories:** 7 (ARAI, CON, ESS, INT, SAM, STR, VER)
**Priority Distribution:**
- High: 15 rules
- Medium: 22 rules
- Low: 8 rules

**Dual Format:**
- JSON metadata: `config/toetsregels/regels/{CATEGORY}/{RULE-ID}.json`
- Python implementation: `src/toetsregels/regels/{CATEGORY}/{rule_id}.py`

---

### 3.2 ARAI Category (Atomiciteit, Relevantie, Adequaatheid, Inconsistentie)

**Purpose:** Detectie van circulaire definities, zelfverwijzingen, irrelevantie

#### ARAI-001: Circulaire Definitie Detectie
- **Priority:** HIGH
- **Business Rule:** Definitie mag niet cirkelverwijs bevatten naar begrip zelf
- **Algorithm:**
  ```python
  def check_circular(begrip, definitie):
      # Direct self-reference
      if begrip.lower() in definitie.lower():
          return "FAILED: Self-reference detected"

      # Circular chain (A → B → A)
      if begrip in get_referenced_terms(definitie):
          chain = find_circular_chain(begrip, definitie)
          return f"FAILED: Circular chain: {chain}"

      return "PASSED"
  ```
- **Error Message:** "Definitie bevat circulaire verwijzing naar '{begrip}'"

#### ARAI-002: Atomiciteit Check
- **Priority:** MEDIUM
- **Business Rule:** Definitie moet atomair zijn (één concept)
- **Indicators:** Multiple "en/of" conjunctions, lists, compound sentences
- **Threshold:** Max 3 conjunctions allowed

#### ARAI-003: Relevantie Check
- **Priority:** HIGH
- **Business Rule:** Definitie moet relevant zijn voor begrip en context
- **Algorithm:** Keyword overlap between begrip and definitie must be > 30%

#### ARAI-004: Adequaatheid Check
- **Priority:** MEDIUM
- **Business Rule:** Definitie moet voldoende zijn (niet te kort, niet te lang)
- **Thresholds:**
  - Min length: 20 characters
  - Max length: 500 characters

#### ARAI-005: Inconsistentie Detectie (Cross-Definition)
- **Priority:** HIGH
- **Business Rule:** Definitie mag niet inconsistent zijn met andere definities in zelfde context
- **Algorithm:** Check for contradictions in related definitions

#### ARAI-006: Zelfverwijzing Detectie
- **Priority:** HIGH
- **Business Rule:** Definitie mag niet zichzelf definiëren
- **Pattern:** "X is X die/dat/wat..."

#### ARAI-007: Tautologie Detectie
- **Priority:** MEDIUM
- **Business Rule:** Definitie mag niet tautologisch zijn
- **Pattern:** "X is een X", "Y is het Y-zijn van..."

#### ARAI-008: Lege Definitie
- **Priority:** HIGH
- **Business Rule:** Definitie mag niet leeg zijn (after whitespace trim)
- **Check:** `len(definitie.strip()) > 0`

---

### 3.3 CON Category (Consistentie)

**Purpose:** Consistentie checks voor terminologie, context, formaat

#### CON-001: Context Consistentie
- **Priority:** HIGH
- **Business Rule:** Definitie moet consistent zijn met geselecteerde context (org/jur/wet)
- **Algorithm:**
  ```python
  def check_context_consistency(definitie, context):
      # Context-specific keywords
      context_keywords = {
          "org": ["organisatie", "afdeling", "medewerker", "proces"],
          "jur": ["recht", "wet", "artikel", "jurisprudentie"],
          "wet": ["wettelijk", "verordening", "grondwet", "regelgeving"]
      }

      keywords = context_keywords[context]
      matches = sum(1 for kw in keywords if kw in definitie.lower())

      # At least 1 context keyword required
      return matches >= 1
  ```

#### CON-002: Terminologie Consistentie
- **Priority:** HIGH
- **Business Rule:** Definitie moet consistente terminologie gebruiken (geen synoniemen door elkaar)
- **Check:** Detect synonym usage within same definitie

#### CON-003: Formaat Consistentie
- **Priority:** MEDIUM
- **Business Rule:** Definitie moet consistent formaat volgen (bijv. start met "Een...")
- **Pattern:** Check for consistent sentence structure

#### CON-004: Afkorting Consistentie
- **Priority:** MEDIUM
- **Business Rule:** Afkortingen moeten uitgeschreven worden bij eerste gebruik
- **Pattern:** "Algemene Verordening Gegevensbescherming (AVG)"

#### CON-005: Geslacht Consistentie
- **Priority:** LOW
- **Business Rule:** Consistent gebruik van mannelijk/vrouwelijk/onzijdig
- **Check:** Detect mixed gebruik van "de/het", "hij/zij/het"

#### CON-006: Tijd Consistentie
- **Priority:** MEDIUM
- **Business Rule:** Consistent gebruik van tegenwoordige/verleden tijd
- **Check:** Detect mixed tense usage

#### CON-007: Forbidden Words (UFO Rules)
- **Priority:** HIGH
- **Business Rule:** Definitie mag geen verboden woorden bevatten (configureerbaar in ExpertReviewTab)
- **Algorithm:**
  ```python
  def check_forbidden_words(definitie, forbidden_list):
      found = [word for word in forbidden_list if word.lower() in definitie.lower()]
      if found:
          return f"FAILED: Forbidden words: {', '.join(found)}"
      return "PASSED"
  ```

---

### 3.4 ESS Category (Essentie)

**Purpose:** Essentie-preservatie en inhoudelijke volledigheid

#### ESS-001: Essentie Preservatie
- **Priority:** CRITICAL
- **Business Rule:** Definitie moet essentie van begrip behouden (niet te abstract, niet te concreet)
- **Algorithm:** Check for essential characteristics vs. accidental properties

#### ESS-002: Inhoudelijke Volledigheid
- **Priority:** HIGH
- **Business Rule:** Definitie moet alle essentiële kenmerken bevatten
- **Check:** Compare against ontological category requirements

#### ESS-003: Geen Irrelevante Details
- **Priority:** MEDIUM
- **Business Rule:** Definitie mag geen irrelevante details bevatten
- **Indicators:** Over-specifieke voorbeelden, randgevallen, uitzonderingen

#### ESS-004: Differentiation (Genus + Differentia)
- **Priority:** HIGH
- **Business Rule:** Definitie moet genus (category) + differentia (distinguishing feature) bevatten
- **Pattern:** "Een [genus] die/dat [differentia]"

#### ESS-005: Neutral Point of View
- **Priority:** MEDIUM
- **Business Rule:** Definitie moet neutraal geformuleerd zijn (geen waardeoordelen)
- **Check:** Detect subjective terms: "goed", "slecht", "belangrijk", "onbelangrijk"

#### ESS-006: Context Volledigheid
- **Priority:** MEDIUM
- **Business Rule:** Definitie moet voldoende context geven voor begrip
- **Check:** At least 2 context clues (when, where, who, what, why, how)

---

### 3.5 INT Category (Intertekstueel)

**Purpose:** Cross-reference checks en intertextualiteit

#### INT-001: Cross-Reference Validity
- **Priority:** MEDIUM
- **Business Rule:** Als definitie verwijst naar andere termen, moeten die bestaan
- **Algorithm:**
  ```python
  def check_references(definitie, repository):
      referenced_terms = extract_referenced_terms(definitie)
      for term in referenced_terms:
          if not repository.exists(term):
              return f"FAILED: Unknown term '{term}'"
      return "PASSED"
  ```

#### INT-002: Wettelijke Basis Validatie
- **Priority:** HIGH
- **Business Rule:** Als wettelijke_basis vermeld, moet deze bestaan en geldig zijn
- **Check:** Validate against wetten.nl or legal database

#### INT-003: Externe Bron Consistentie
- **Priority:** MEDIUM
- **Business Rule:** Definitie moet consistent zijn met externe bronnen (Wikipedia, SRU, ECLI)
- **Algorithm:** Compare key concepts with web lookup results

#### INT-004: Synonym Consistency
- **Priority:** MEDIUM
- **Business Rule:** Synoniemen moeten consistent zijn met definitie
- **Check:** Synonyms should be interchangeable with begrip in context

#### INT-005: Ketenpartners Validatie
- **Priority:** LOW
- **Business Rule:** Als ketenpartners vermeld, moeten deze bekend zijn in systeem
- **Check:** Validate against known organizations list

---

### 3.6 SAM Category (Samenhang)

**Purpose:** Samenhang tussen context en definitie, coherentie

#### SAM-001: Context-Definitie Samenhang
- **Priority:** HIGH
- **Business Rule:** Definitie moet samenhangen met gekozen context (org/jur/wet)
- **Algorithm:** See CON-001 (similar but focuses on coherence, not just keyword presence)

#### SAM-002: Intern Coherentie
- **Priority:** HIGH
- **Business Rule:** Zinnen binnen definitie moeten samenhangen (logische flow)
- **Check:** Detect abrupt topic changes, missing connectors

#### SAM-003: Begrip-Categorie Samenhang
- **Priority:** MEDIUM
- **Business Rule:** Begrip moet passen bij ontological category
- **Check:** Category-specific validation (e.g., "proces" should have action verbs)

#### SAM-004: Volledigheid
- **Priority:** MEDIUM
- **Business Rule:** Definitie moet volledig zijn (geen missing information)
- **Check:** Essential fields filled based on category

#### SAM-005: Logische Structuur
- **Priority:** MEDIUM
- **Business Rule:** Definitie moet logische structuur volgen (intro → body → conclusion)
- **Check:** Sentence structure analysis

#### SAM-006: Voorbeeld-Definitie Samenhang
- **Priority:** LOW
- **Business Rule:** Voorbeelden moeten passen bij definitie
- **Check:** Voorbeelden should illustrate defined concept

#### SAM-007: Voorkeursterm-Synoniem Samenhang
- **Priority:** MEDIUM
- **Business Rule:** Voorkeursterm moet één van de synoniemen zijn (of begrip zelf)
- **Algorithm:**
  ```python
  def check_voorkeursterm(begrip, voorkeursterm, synoniemen):
      valid_terms = [begrip] + synoniemen
      return voorkeursterm in valid_terms
  ```

---

### 3.7 STR Category (Structuur)

**Purpose:** Structurele eisen (lengte, leesbaarheid, formaat)

#### STR-001: Lengte Eisen
- **Priority:** MEDIUM
- **Business Rule:** Definitie moet tussen min/max lengte zijn
- **Thresholds:**
  - Min: 20 characters
  - Max: 500 characters
  - Optimal: 100-250 characters

#### STR-002: Leesbaarheid (Flesch-Douma)
- **Priority:** MEDIUM
- **Business Rule:** Definitie moet leesbaar zijn voor juridisch publiek (B1-C1 niveau)
- **Algorithm:** Flesch-Douma reading ease score >= 40

#### STR-003: Zinstructuur
- **Priority:** LOW
- **Business Rule:** Definitie moet uit 1-3 zinnen bestaan
- **Check:** Count sentences (by period + space pattern)

#### STR-004: Opsomming Formaat
- **Priority:** LOW
- **Business Rule:** Als opsomming, gebruik consistent formaat (bullets/nummering)
- **Pattern:** Detect list patterns

#### STR-005: Haakjes Balancing
- **Priority:** MEDIUM
- **Business Rule:** Haakjes moeten gebalanceerd zijn
- **Check:** Count '(' == count ')'

#### STR-006: Aanhalingstekens Balancing
- **Priority:** MEDIUM
- **Business Rule:** Quotes moeten gebalanceerd zijn
- **Check:** Count opening quotes == count closing quotes

#### STR-007: Hoofdletter Gebruik
- **Priority:** LOW
- **Business Rule:** Definitie moet met hoofdletter starten (tenzij lowercase term)
- **Check:** `definitie[0].isupper()`

#### STR-008: Interpunctie
- **Priority:** LOW
- **Business Rule:** Definitie moet eindigen met punt
- **Check:** `definitie.strip().endswith('.')`

---

### 3.8 VER Category (Verduidelijking)

**Purpose:** Duidelijkheid en begrijpelijkheid

#### VER-001: Jargon Check
- **Priority:** MEDIUM
- **Business Rule:** Jargon moet uitgelegd worden
- **Algorithm:** Detect technical terms without explanation

#### VER-002: Dubbelzinnigheid Detectie
- **Priority:** HIGH
- **Business Rule:** Definitie mag niet dubbelzinnig zijn
- **Check:** Detect ambiguous pronouns ("het", "deze", "die" without clear antecedent)

#### VER-003: Passieve Constructies
- **Priority:** LOW
- **Business Rule:** Prefer actieve constructies boven passieve
- **Pattern:** Detect "wordt gedaan", "is gemaakt" patterns

#### VER-004: Negatieve Definities
- **Priority:** MEDIUM
- **Business Rule:** Define what something IS, not what it ISN'T
- **Pattern:** Avoid "niet", "geen" dominant definitions

---

### 3.9 Missing Rules (Identified by Gap Analysis)

**GAP:** 7 rules identified in code but not documented in extraction plan

#### VAL-EMP-001: Empty Field Validation
- **Priority:** HIGH
- **Business Rule:** Required fields must not be empty
- **Fields:** begrip, definitie, context

#### VAL-LEN-001: Minimum Length Validation
- **Priority:** MEDIUM
- **Business Rule:** Definitie minimum 20 characters

#### VAL-LEN-002: Maximum Length Validation
- **Priority:** MEDIUM
- **Business Rule:** Definitie maximum 500 characters

#### CON-CIRC-001: Circulaire Reference Check (Duplicate of ARAI-001?)
- **Priority:** HIGH
- **Needs investigation:** May be duplicate or different aspect

#### ESS-CONT-001: Content Essentiality Check
- **Priority:** HIGH
- **Business Rule:** Definitie must contain essential content (not just filler words)

#### STR-TERM-001: Terminology Structure
- **Priority:** MEDIUM
- **Business Rule:** Proper terminology usage in structure

#### STR-ORG-001: Organizational Structure
- **Priority:** LOW
- **Business Rule:** Proper organization of definitie content

---

### 3.10 Validation Orchestration

**Service:** ModularValidationService + ValidationOrchestratorV2

**Workflow:**
```
1. Pre-Cleaning (normalize text)
2. Context Enrichment (add metadata)
3. Load Applicable Rules (filter by context, category)
4. Sort by Priority (high → medium → low)
5. Execute Batch (parallel where possible)
6. Error Isolation (continue on rule failure)
7. Aggregate Results (pass/fail per rule)
8. Calculate Score (passed / total)
9. Determine Acceptability (>= 0.7)
10. Return ValidationResult object
```

**Score Calculation:**
```python
def calculate_validation_score(results):
    total_rules = len(results)
    passed_rules = sum(1 for r in results if r.status == "passed")

    # Score = percentage of passed rules
    score = passed_rules / total_rules if total_rules > 0 else 0.0

    # Acceptability threshold
    is_acceptable = score >= 0.7

    return {
        "score": score,
        "is_acceptable": is_acceptable,
        "total_rules": total_rules,
        "passed_rules": passed_rules,
        "failed_rules": total_rules - passed_rules
    }
```

**Priority Impact:**
```python
# High-priority failure = Stronger negative impact
# Low-priority failure = Weaker negative impact

def weighted_score(results):
    weights = {"high": 3.0, "medium": 2.0, "low": 1.0}

    total_weight = sum(weights[r.priority] for r in results)
    passed_weight = sum(weights[r.priority] for r in results if r.status == "passed")

    return passed_weight / total_weight
```

---

## 🖥️ LAYER 4: UI/WORKFLOW BUSINESS LOGIC

### 4.1 Application Flow

**Entry Point:** `src/main.py`

**Startup Logic:**
```python
1. Initialize Streamlit app (set page config)
2. Load ServiceContainer (singleton with @st.cache_resource)
3. Initialize SessionStateManager
4. Load user preferences (if any)
5. Render tab navigation (radio buttons)
6. Dispatch to selected tab
```

**Tab Navigation:**
```python
tabs = [
    "Definitie Generator",
    "Definitie Bewerken",
    "Definitie Repository",
    "Expert Review",
    "Import/Export Beheer",
    "Instellingen"
]

selected_tab = st.radio("Navigatie", tabs, horizontal=True)

# Dispatch
if selected_tab == "Definitie Generator":
    DefinitieGeneratorTab().render()
elif selected_tab == "Definitie Bewerken":
    DefinitionEditTab().render()
# etc...
```

**Session State Management:**
- **RULE:** SessionStateManager is ONLY module that touches `st.session_state`
- **Pattern:**
  ```python
  # Get value
  value = SessionStateManager.get_value("key", default=None)

  # Set value
  SessionStateManager.set_value("key", value)
  ```

---

### 4.2 DefinitieGenerator Tab (Core Generation Workflow)

**Workflow Steps:**
```
Begrip Input → Context Selection → Category Determination →
[Duplicate Check] → [Force Option] → Generate →
Validate → Save → Auto-load to Edit Tab
```

**Business Rules:**

#### UI-GEN-001: Duplicate Check Gate
- **Rule:** Before generation, check for duplicates (unless force=True)
- **Algorithm:** DuplicateDetectionService.check(begrip, context)
- **3 Levels:**
  1. Exact match: High-risk warning, block unless force
  2. Synonym match: Medium-risk warning, suggest review
  3. Fuzzy match (Jaccard >= 0.7): Low-risk warning, allow

#### UI-GEN-002: Ontological Category Determination
- **Algorithm:**
  1. **6-step decision tree** (primary method)
  2. **Quick determination** (keyword-based fallback)
  3. **Pattern matching** (regex patterns for categories)
  4. **User override** (manual selection)

#### UI-GEN-003: Document Context Processing
- **Workflow:**
  1. Upload PDF/DOCX/TXT documents
  2. Extract text with pypdf/python-docx
  3. Select relevant passages (manual selection UI)
  4. Aggregate selected snippets
  5. Extract snippets with citations (max 500 chars each)
  6. Inject into prompt context

#### UI-GEN-004: Regeneration (GVI Red Cable)
- **Trigger:** User clicks "Regenereer" button
- **Business Rules:**
  - Preserve context selection
  - Allow category override
  - Show diff (old vs new definition)
  - Track regeneration count (metadata)

#### UI-GEN-005: Force Generation
- **Trigger:** User clicks "Forceer Generatie" after duplicate warning
- **Business Rules:**
  - Bypass duplicate check
  - Log forced generation (audit trail)
  - Display confirmation warning

#### UI-GEN-006: Auto-Load to Edit Tab
- **Trigger:** After successful generation
- **Business Rules:**
  - Store generated definition in session state
  - Switch to "Definitie Bewerken" tab
  - Pre-fill all fields (including voorbeelden, context, category)
  - Show success message

---

### 4.3 DefinitionEditTab (Edit & Refine Workflow)

**Workflow Steps:**
```
[Auto-load from Generator] OR [Search → Select] →
Edit (Rich Text) → Context Update → Re-validate →
Auto-save (30s throttle) → Version History
```

**Business Rules:**

#### UI-EDIT-001: Auto-Load from Generator
- **Trigger:** After generation in Generator tab
- **Business Rules:**
  - Load full definition object (all fields)
  - Pre-fill form fields
  - Show "Laatst gegenereerd" indicator
  - Enable immediate editing

#### UI-EDIT-002: Search & Selection
- **Search Filters:**
  - Begrip (substring match)
  - Context (multi-select: org/jur/wet)
  - Category (multi-select: 11 categories)
  - Status (multi-select: 5 statuses)
- **Display Modes:**
  - Table view (compact, sortable)
  - Card view (rich, detailed)
- **Selection:** Click row/card to load into editor

#### UI-EDIT-003: Rich Text Editor
- **Widget:** Streamlit text_area with scoped keys
- **Scoped Keys:** `{tab}_{field}_{definitie_id}` to prevent state conflicts
- **Features:**
  - Multi-line editing
  - Syntax highlighting (future)
  - Character count display
  - Validation live preview (future)

#### UI-EDIT-004: Context Management
- **UI Component:** Enhanced selector component
- **Business Rules:**
  - At least one context required (org OR jur OR wet)
  - Multi-select allowed
  - "Anders..." pattern for custom values (rare)
  - Context propagation: Updates affect validation + web lookup

#### UI-EDIT-005: Validation Integration
- **Trigger:** Manual "Re-validate" button OR auto-validate on save
- **Display:** V2 validation display component (shared)
- **Features:**
  - Rule sorting by category
  - Grouping by priority (high/medium/low)
  - Gate status indicators (pass/override/blocked)
  - Expandable details per rule

#### UI-EDIT-006: Auto-Save System
- **Algorithm:**
  ```python
  def auto_save():
      # Change detection
      current_state = get_current_form_state()
      last_saved_state = SessionStateManager.get_value("last_saved_state")

      if current_state != last_saved_state:
          # Throttle: Only save if > 30s since last save
          if time.now() - last_save_time > 30:
              try:
                  repository.save(current_state)
                  SessionStateManager.set_value("last_saved_state", current_state)
                  show_success("Auto-saved")
              except OptimisticLockingError:
                  show_error("Conflict detected. Refresh to see latest version.")
  ```
- **Throttle:** 30 seconds between auto-saves
- **Conflict Detection:** Optimistic locking (version-based)
- **Restore Capability:** Restore from last auto-save if user navigates away

#### UI-EDIT-007: Version Management
- **Features:**
  - Version history display (timeline)
  - Revert to previous version
  - Diff view (show changes)
  - Optimistic locking (prevent lost updates)
- **Algorithm:**
  ```python
  def save_with_optimistic_locking(definitie):
      current_version = repository.get_version(definitie.id)

      if definitie.version != current_version:
          raise OptimisticLockingError("Version conflict")

      definitie.version += 1
      repository.update(definitie)
  ```

#### UI-EDIT-008: Examples Block Integration
- **Component:** Shared voorbeelden component
- **Features:**
  - Display active voorbeelden
  - Manual editing (text_area per voorbeeld)
  - Type selection (6 types dropdown)
  - Add/Remove voorbeelden
  - Voorkeursterm selector (from synoniemen)
- **Business Rules:**
  - AI generation ONLY in Generator tab (not Edit)
  - Manual editing allowed in Edit + Expert tabs
  - Active replacement strategy (deactivate old, insert new)

---

### 4.4 ExpertReviewTab (Review & Approval Workflow)

**Workflow Steps:**
```
Review Queue (filtered) → Select Definition → Review →
[Gate Check] → Approve/Reject/Unlock → Status Transition → Audit Log
```

**Business Rules:**

#### UI-REVIEW-001: Review Queue
- **Filters:**
  - Status: "review" (default)
  - Context: org/jur/wet (multi-select)
  - Category: 11 categories (multi-select)
  - Validation score: >= threshold (slider)
  - Has voorbeelden: Yes/No (checkbox)
- **Display:** Table with key fields (begrip, context, category, score, submitted_by, submitted_at)
- **Sorting:** Priority (high score → low score), then date (oldest first)

#### UI-REVIEW-002: Forbidden Words Runtime Management
- **Feature:** Expert can add/edit forbidden words list in UI
- **Storage:** validation_config table (custom_params JSON)
- **Live Update:** Changes apply immediately (no restart)
- **Algorithm:**
  ```python
  def update_forbidden_words(new_list):
      # Validate list (no empty strings, duplicates)
      cleaned_list = [w.strip().lower() for w in new_list if w.strip()]
      unique_list = list(set(cleaned_list))

      # Update config
      db.execute(
          "UPDATE validation_config "
          "SET custom_params = json_set(custom_params, '$.forbidden_words', ?) "
          "WHERE rule_id = 'CON-007'",
          (json.dumps(unique_list),)
      )
  ```

#### UI-REVIEW-003: Gate-Based Approval System (US-160)
- **Policy:** ApprovalGatePolicy (loaded from GatePolicyService)
- **Gate Check:** Evaluate definition against policy before approval
- **Outcomes:**
  1. **PASS:** All requirements met → Allow approval
  2. **OVERRIDE_REQUIRED:** Soft requirements violated → Require override reason
  3. **BLOCKED:** Hard requirements violated → Block approval
- **UI Display:**
  - Green checkmark: PASS
  - Yellow warning: OVERRIDE_REQUIRED (show issues + reason input)
  - Red X: BLOCKED (show issues, disable approve button)

#### UI-REVIEW-004: Three Review Actions
1. **Approve:**
   - Trigger: "Goedkeuren" button
   - Prerequisites: Gate check PASS OR override reason provided
   - Action: Status → "established", log approval (user, timestamp, reason)
   - Audit: Log in definitie_geschiedenis (change_type = "approved")

2. **Reject:**
   - Trigger: "Afwijzen" button
   - Prerequisites: Rejection reason required
   - Action: Status → "draft", log rejection (user, timestamp, reason)
   - Notification: Notify submitter (if notification system exists)

3. **Unlock:**
   - Trigger: "Ontgrendelen" button (only for status = "established")
   - Prerequisites: Role = admin
   - Action: Status → "draft", log unlock (user, timestamp, reason)
   - Purpose: Allow editing of established definitions (rare)

#### UI-REVIEW-005: Gate Outcomes Detail
- **Hard Requirements (BLOCKED if violated):**
  - Validation score >= 0.8 (configurable)
  - No high-priority rule failures
  - Begrip is non-empty
  - At least one context selected
  - Definitie non-empty (after trim)
- **Soft Requirements (OVERRIDE REQUIRED if violated):**
  - Toelichting_proces is filled
  - Voorbeelden exist (at least 1)
  - UFO category assigned
  - Wettelijke_basis is filled (if legal context)
- **Override Reason Input:**
  - Required if soft requirements violated
  - Free text area (min 20 chars)
  - Stored in approval metadata
  - Auditability: Override logged in geschiedenis

#### UI-REVIEW-006: Validation Re-run Capability
- **Feature:** Expert can re-run validation during review
- **Trigger:** "Hervalideer" button
- **Use Case:** After expert edits forbidden words list or validation config
- **Display:** Updated validation results with new scores

#### UI-REVIEW-007: UFO Category & Toelichting_Proces Fields
- **UFO Category:** Dropdown with UFO classification options (loaded from config)
- **Toelichting_Proces:** Text area for review process notes (optional for draft, required for approval if gate policy enforces)
- **Business Rule:** These fields exposed ONLY in ExpertReviewTab (not in Generator/Edit)

---

### 4.5 DefinitieRepository Tab (Search & Export)

**Workflow Steps:**
```
Search (filters) → Display Results (table/card) →
Select → View/Edit/Delete → Export (format selection)
```

**Business Rules:**

#### UI-REPO-001: Search Filters
- Same as Edit tab (begrip, context, category, status)
- Additional: Date range (created_at, updated_at)

#### UI-REPO-002: Export Business Rules
- **Formats:** CSV, JSON, YAML, XML, Excel
- **Format Rules:**
  ```python
  # CSV
  - All fields as columns
  - JSON arrays serialized as comma-separated strings
  - UTF-8 encoding with BOM for Excel compatibility

  # JSON
  - Pretty-printed (indent=2)
  - ensure_ascii=False (preserve Dutch characters)
  - Arrays preserved as JSON arrays

  # YAML
  - Human-readable format
  - Arrays as YAML lists
  - Proper escaping of special characters

  # XML
  - Root element: <definities>
  - Child elements: <definitie>
  - Attributes: id, status, version
  - UTF-8 encoding declaration

  # Excel
  - Use openpyxl library
  - Multiple sheets (definitions, examples, tags)
  - Auto-width columns
  - Header row bold
  ```

#### UI-REPO-003: Bulk Operations
- **Feature:** Select multiple definitions (checkboxes)
- **Operations:**
  - Bulk status update (e.g., draft → review)
  - Bulk tag assignment
  - Bulk delete (archive)
  - Bulk export
- **Safeguards:**
  - Confirmation dialog (show count + preview)
  - Transaction rollback on error
  - Audit logging (bulk operation logged)

---

### 4.6 Import/Export Beheer Tab (Orchestrator)

**Purpose:** Orchestrate import/export workflows (modularized in EPIC-026)

**Components (Planned in EPIC-026):**
1. **csv_importer.py** (137 LOC)
2. **format_exporter.py** (153 LOC)
3. **bulk_operations.py** (69 LOC)
4. **database_manager.py** (107 LOC)
5. **orchestrator.py** (81 LOC)

**Business Rules:**

#### UI-IMPORT-001: CSV Import Validation Rules
- **Validation:**
  - Required fields: begrip, definitie, context
  - Optional fields: All others
  - Duplicate check: Warn but allow (with flag)
  - Encoding: Auto-detect (UTF-8, Latin-1, CP-1252)
  - Headers: First row = headers (required)

#### UI-IMPORT-002: Import Conflict Resolution
- **Strategy:**
  1. **Skip:** Skip conflicting rows (default)
  2. **Update:** Update existing definitions (override)
  3. **Append:** Create new with suffix (e.g., "begrip (2)")
- **User Choice:** Radio buttons to select strategy

#### UI-EXPORT-003: Format Selection UI
- **Dropdown:** Select format (CSV/JSON/YAML/XML/Excel)
- **Options:**
  - Include voorbeelden: Yes/No
  - Include tags: Yes/No
  - Include history: Yes/No (large exports)
  - Date range filter: Start/End dates

---

### 4.7 Workflow Orchestration (Complete Lifecycle)

**Status Machine:**
```
[imported] ──────→ [draft] ──────→ [review] ──────→ [established] ──────→ [archived]
              ↑                  ↑            ↑                    ↑
              └──────────────────┴────────────┴────────────────────┘
                              (unlock/reject)
```

**Transitions:**

#### imported → draft
- **Trigger:** User imports from external source
- **Allowed:** Always
- **Prerequisites:** None
- **Action:** Save with status = "draft"

#### draft → review
- **Trigger:** User clicks "Indienen voor Review" in Edit tab
- **Allowed:** Only if validation score >= 0.7
- **Prerequisites:**
  - At least one context
  - Definitie non-empty
  - Begrip non-empty
- **Action:** Status = "review", log submission (submitted_by, submitted_at)

#### review → established
- **Trigger:** Expert clicks "Goedkeuren" in Review tab
- **Allowed:** Only if gate check PASS OR override reason provided
- **Prerequisites:** See UI-REVIEW-003 (gate requirements)
- **Action:** Status = "established", log approval (approved_by, approved_at, approval_reason, override_reason)

#### established → archived
- **Trigger:** Admin clicks "Archiveren" in Repository tab
- **Allowed:** Role = admin only
- **Prerequisites:** Archive reason required
- **Action:** Status = "archived", log archival (archived_by, archived_at, archive_reason)

#### archived → draft (Unlock)
- **Trigger:** Admin clicks "Ontgrendelen" in Review tab
- **Allowed:** Role = admin only
- **Prerequisites:** Unlock reason required
- **Action:** Status = "draft", log unlock (unlocked_by, unlocked_at, unlock_reason)

#### review → draft (Reject)
- **Trigger:** Expert clicks "Afwijzen" in Review tab
- **Allowed:** Always
- **Prerequisites:** Rejection reason required
- **Action:** Status = "draft", log rejection (rejected_by, rejected_at, rejection_reason)

---

### 4.8 Error Handling Patterns (4-Level UI Messaging)

**Levels:**

1. **Success (Green):**
   ```python
   st.success("Definitie succesvol opgeslagen!")
   ```
   - Use for: Successful operations (save, approve, export)

2. **Info (Blue):**
   ```python
   st.info("Auto-save ingeschakeld. Wijzigingen worden elke 30 seconden opgeslagen.")
   ```
   - Use for: Informational messages, tips, guidance

3. **Warning (Yellow):**
   ```python
   st.warning("Mogelijk duplicaat gevonden. Weet u zeker dat u wilt doorgaan?")
   ```
   - Use for: Non-blocking warnings (duplicates, low validation scores)

4. **Error (Red):**
   ```python
   st.error("Kan definitie niet opslaan. Database fout: {error}")
   ```
   - Use for: Blocking errors (save failed, API error, validation blocked)

**Error Recovery Workflows:**

#### Retry with Same Inputs
- **Trigger:** User clicks "Probeer opnieuw" button
- **Use Case:** Transient errors (network timeout, rate limit)
- **Action:** Re-execute same operation with same inputs

#### Refresh and Retry
- **Trigger:** User clicks "Ververs en probeer opnieuw" button
- **Use Case:** Stale state (optimistic locking conflict)
- **Action:** Reload data from DB, then re-execute operation

#### Fallback Mechanisms
- **GPT-4 → GPT-3.5-turbo:** If GPT-4 fails, retry with fallback model
- **Web Lookup → Continue without:** If web lookup times out, continue generation without external data
- **Validation → Partial Results:** If some rules fail, show partial results (don't block entire validation)

#### Graceful Degradation
- **Auto-save Disabled:** If auto-save fails repeatedly, show error + disable auto-save (manual save only)
- **Web Lookup Disabled:** If web lookup service down, disable web lookup feature (show message)
- **Validation Degraded:** If validation service slow, show "Validatie in progress..." with spinner

---

## 🔍 LAYER 5: CROSS-CUTTING CONCERNS

### 5.1 Security

#### SEC-001: PII Sanitization
- **Where:** DefinitionOrchestratorV2 Phase 1
- **What:** Remove or mask personally identifiable information
- **Patterns:** Email addresses, phone numbers, social security numbers
- **Algorithm:** Regex-based detection + replacement with `[REDACTED]`

#### SEC-002: API Key Management
- **Rule:** NO hardcoded API keys in code
- **Storage:** Environment variables only
- **Access:** Via `os.environ.get("OPENAI_API_KEY")`
- **Fallback:** Prompt user to enter key if missing (UI input)

#### SEC-003: SQL Injection Prevention
- **Rule:** Parameterized queries ONLY
- **Pattern:**
  ```python
  # WRONG
  cursor.execute(f"SELECT * FROM definities WHERE begrip = '{begrip}'")

  # CORRECT
  cursor.execute("SELECT * FROM definities WHERE begrip = ?", (begrip,))
  ```

#### SEC-004: XSS Prevention
- **Rule:** Escape HTML in user inputs displayed in UI
- **Library:** Streamlit handles this automatically for text components
- **Manual Escaping:** If using custom HTML (`st.markdown(html, unsafe_allow_html=True)`)

---

### 5.2 Performance

#### PERF-001: Service Initialization
- **Problem:** Services initialized 6x per Streamlit rerun
- **Solution:** Use `@st.cache_resource` on ServiceContainer

#### PERF-002: Prompt Token Optimization
- **Problem:** 7,250 tokens with duplications
- **Solution:** Implement prompt caching (OpenAI cache API) + deduplication

#### PERF-003: Validation Rule Loading
- **Problem:** 45 rules reloaded per session
- **Solution:** Use `@st.cache_data` for rule loading

#### PERF-004: Database Query Optimization
- **Indexes:** 11 indexes (see 2.2-2.8 sections)
- **Query Patterns:** Avoid SELECT * (select only needed columns)
- **Pagination:** Default page size = 20 (avoid loading all definitions)

---

### 5.3 Monitoring & Observability

#### OBS-001: Distributed Tracing
- **Pattern:** trace_id per generation (UUID)
- **Propagation:** Pass trace_id through all service calls
- **Logging:** Include trace_id in all log messages

#### OBS-002: Structured Logging
- **Format:** JSON
- **Fields:** timestamp, level, trace_id, service, message, metadata
- **Storage:** `logs/` directory (rotate daily)

#### OBS-003: Business Metrics
- **Metrics:**
  - Definition generation success rate
  - Validation score distribution (histogram)
  - Approval gate pass/fail rate
  - Web lookup success rate
  - Average generation time (p50, p95, p99)

---

## 📋 APPENDIX: REFERENCES

### A.1 Source Documents
- Agent 1: `rebuild/business-logic-extraction/01-services-core-logic/SERVICES-EXTRACTION.md`
- Agent 2: `rebuild/business-logic-extraction/02-database-business-rules/DATABASE-EXTRACTION.md`
- Agent 3: `rebuild/business-logic-extraction/03-validation-rules/VALIDATION-EXTRACTION.md`
- Agent 4: `rebuild/business-logic-extraction/04-ui-workflow-logic/UI-WORKFLOW-EXTRACTION.md`
- Agent 5: `rebuild/business-logic-extraction/05-existing-docs-inventory/DOCS-INVENTORY.md`
- Agent 6: `rebuild/business-logic-extraction/06-gap-analysis/GAP-ANALYSIS.md`

### A.2 Critical Files in Codebase
- **Main:** `src/main.py`
- **Container:** `src/services/container.py`
- **Orchestrator:** `src/services/orchestration/definition_orchestrator_v2.py`
- **Validator:** `src/services/validation/modular_validation_service.py`
- **Repository:** `src/database/repository.py`
- **Schema:** `src/database/schema.sql`

### A.3 Key Configuration Files
- **Validation Rules (JSON):** `config/toetsregels/regels/{CATEGORY}/{RULE-ID}.json`
- **Validation Rules (Python):** `src/toetsregels/regels/{CATEGORY}/{rule_id}.py`
- **Web Lookup Config:** `config/web_lookup_defaults.yaml`
- **UFO Rules:** `config/ufo_rules.yaml`

### A.4 Statistics Summary
- **Total business rules extracted:** 4,318 LOC
- **Total documentation:** 850,684 words analyzed
- **Coverage:** 85% (26% gap)
- **Validation rules:** 45+ (87% documented)
- **Database tables:** 8 (100% extracted)
- **Services:** 15+ (extracted)
- **UI tabs:** 6+ (extracted)

---

## ✅ COMPLETION STATUS

**Extraction Status:** ✅ COMPLETE
**Gap Analysis Status:** ✅ COMPLETE
**Consolidation Status:** ✅ COMPLETE

**Next Steps:**
1. Review this consolidated document
2. Close P0 critical gaps (12-14 hours)
3. Close P1 high-priority gaps (26-37 hours)
4. Update EPIC-026 Phase 1 plan
5. Proceed to Phase 2 (Implementation)

**Total Effort to Close Gaps:** 38-53 hours (1-2 weeks)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-02
**Maintained By:** BMad Master (6 Parallel Agents)
