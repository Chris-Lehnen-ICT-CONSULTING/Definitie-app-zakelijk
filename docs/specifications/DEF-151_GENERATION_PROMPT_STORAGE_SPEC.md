# DEF-151: Generation Prompt Storage - Implementation Specification
**Version:** 1.0
**Date:** 2025-11-11
**Author:** BMad Master (Claude Code)
**Status:** READY FOR IMPLEMENTATION
**Linear Issue:** https://linear.app/definitie-app/issue/DEF-151

---

## 📋 TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Database Design](#database-design)
4. [Data Model](#data-model)
5. [Service Layer Changes](#service-layer-changes)
6. [Repository Layer](#repository-layer)
7. [Integration Points](#integration-points)
8. [Migration Strategy](#migration-strategy)
9. [Testing Strategy](#testing-strategy)
10. [Performance Considerations](#performance-considerations)
11. [Security & Privacy](#security--privacy)
12. [Rollout Plan](#rollout-plan)

---

## 🎯 EXECUTIVE SUMMARY

### Problem
90 gegenereerde definities hebben GEEN audit trail van gebruikte prompts, wat leidt tot:
- 🚫 Geen reproducibility (kan definitie niet opnieuw genereren)
- 🚫 Geen debugging capability (waarom deze output?)
- 🚫 Geen A/B testing (kan prompts niet vergelijken)
- 🚫 Compliance risk (geen GDPR-compliant audit trail)

### Solution
Implementeer `generation_logs` tabel die voor elke gegenereerde definitie opslaat:
- Complete prompt tekst (10KB+)
- Model parameters (temperature, max_tokens, etc.)
- Token usage & duration
- Response metadata

### Success Criteria
- ✅ Alle nieuwe definities hebben generation log
- ✅ <100ms overhead per generatie
- ✅ >95% test coverage
- ✅ Zero data loss (ACID compliance)

---

## 🏗️ ARCHITECTURE OVERVIEW

### Current Flow (WITHOUT Logging)
```
User Input
    ↓
UnifiedDefinitionGenerator.generate()
    ↓
PromptOrchestrator.build_prompt()
    ↓
AIServiceV2.generate()
    ↓
DefinitionRepository.save()
    ↓
Database (definities table)
```

### New Flow (WITH Logging)
```
User Input
    ↓
UnifiedDefinitionGenerator.generate()
    ↓
PromptOrchestrator.build_prompt()
    ↓ [CAPTURE: prompt_full_text + params]
    ↓
GenerationLogRepository.create_pending_log()  ← NEW
    ↓
AIServiceV2.generate()
    ↓ [CAPTURE: tokens + duration + response_id]
    ↓
GenerationLogRepository.update_with_response()  ← NEW
    ↓
DefinitionRepository.save()
    ↓
Database (definities + generation_logs tables)
```

### Key Design Decisions

**Decision 1: Separate Table (Not Columns)**
- ✅ CHOSEN: `generation_logs` table (normalized)
- ❌ REJECTED: Add columns to `definities` (denormalized)
- **Rationale:** Future-proof, supports multiple generation attempts, keeps main table lean

**Decision 2: Log BEFORE API Call**
- ✅ CHOSEN: Create pending log → update after response
- ❌ REJECTED: Create log only after successful response
- **Rationale:** Captures failures, enables retry analysis, better debugging

**Decision 3: Store Full Prompt (Not Template ID)**
- ✅ CHOSEN: Store complete prompt text (10KB+)
- ❌ REJECTED: Store only template ID + variables
- **Rationale:** True reproducibility requires exact prompt, templates change over time

---

## 🗃️ DATABASE DESIGN

### Schema Definition

**File:** `src/database/migrations/20251111_add_generation_logs.sql`

```sql
-- ================================================================
-- Migration: Add generation_logs table for prompt audit trail
-- Date: 2025-11-11
-- Author: DEF-151
-- ================================================================

CREATE TABLE generation_logs (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Link to Definitie (UNIQUE: 1 log per definitie)
    definitie_id INTEGER NOT NULL UNIQUE,

    -- ============================================================
    -- PROMPT CONTEXT (captured BEFORE API call)
    -- ============================================================

    -- Full prompt text (10KB+ typical)
    prompt_full_text TEXT NOT NULL,

    -- Template versioning
    prompt_template_version VARCHAR(50), -- e.g., "2.0", "2.1-beta"
    prompt_template_name VARCHAR(100),   -- e.g., "unified_definition_v2"

    -- Prompt modules included
    prompt_modules_used TEXT,            -- JSON array: ["base", "context", "examples", ...]

    -- ============================================================
    -- MODEL PARAMETERS (from OpenAI API request)
    -- ============================================================

    model_name VARCHAR(100) NOT NULL,    -- e.g., "gpt-4-turbo-2024-04-09"
    model_temperature DECIMAL(3,2),      -- e.g., 0.70
    model_max_tokens INTEGER,            -- e.g., 2000
    model_top_p DECIMAL(3,2),            -- e.g., 1.00
    model_frequency_penalty DECIMAL(3,2), -- e.g., 0.00
    model_presence_penalty DECIMAL(3,2),  -- e.g., 0.00

    -- ============================================================
    -- GENERATION RESULTS (captured AFTER API response)
    -- ============================================================

    -- Token usage (from response.usage)
    tokens_prompt INTEGER,               -- Input tokens
    tokens_completion INTEGER,           -- Output tokens
    tokens_total INTEGER,                -- Total tokens

    -- Performance metrics
    duration_ms INTEGER,                 -- Generation time in milliseconds

    -- Response metadata (from OpenAI response)
    response_finish_reason VARCHAR(50),  -- "stop", "length", "content_filter", etc.
    response_id VARCHAR(255),            -- OpenAI response ID (e.g., "chatcmpl-...")
    response_created_at INTEGER,         -- Unix timestamp from OpenAI

    -- Generation status
    generation_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- Values: 'pending' (before API call), 'success', 'failed', 'timeout'

    -- Error tracking (if generation failed)
    error_message TEXT,
    error_type VARCHAR(50),              -- "api_error", "timeout", "validation_error", etc.
    error_traceback TEXT,

    -- ============================================================
    -- EXTENSIBILITY
    -- ============================================================

    -- JSON field for future metadata (system info, feature flags, etc.)
    additional_metadata TEXT,

    -- ============================================================
    -- AUDIT TRAIL
    -- ============================================================

    logged_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- ============================================================
    -- CONSTRAINTS
    -- ============================================================

    FOREIGN KEY(definitie_id) REFERENCES definities(id) ON DELETE CASCADE,

    CHECK (generation_status IN ('pending', 'success', 'failed', 'timeout')),
    CHECK (model_temperature >= 0.0 AND model_temperature <= 2.0),
    CHECK (tokens_prompt >= 0),
    CHECK (tokens_completion >= 0),
    CHECK (duration_ms >= 0)
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

-- Primary lookup: Get log for a definitie
CREATE INDEX idx_generation_logs_definitie
    ON generation_logs(definitie_id);

-- Analytics: Query by timestamp
CREATE INDEX idx_generation_logs_timestamp
    ON generation_logs(logged_at);

-- Analytics: Query by model
CREATE INDEX idx_generation_logs_model
    ON generation_logs(model_name);

-- Analytics: Query by template version
CREATE INDEX idx_generation_logs_template
    ON generation_logs(prompt_template_version);

-- Debug: Find failed generations
CREATE INDEX idx_generation_logs_status
    ON generation_logs(generation_status);

-- ============================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================

CREATE TRIGGER generation_logs_updated_at
AFTER UPDATE ON generation_logs
FOR EACH ROW
BEGIN
    UPDATE generation_logs
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- ============================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================

-- View: Definities with generation context
CREATE VIEW definities_with_generation AS
SELECT
    d.*,
    gl.prompt_template_version,
    gl.model_name,
    gl.tokens_total,
    gl.duration_ms,
    gl.generation_status,
    gl.logged_at as generated_at
FROM definities d
LEFT JOIN generation_logs gl ON d.id = gl.definitie_id
WHERE d.source_type = 'generated';

-- View: Failed generations for debugging
CREATE VIEW failed_generations AS
SELECT
    d.begrip,
    gl.error_message,
    gl.error_type,
    gl.logged_at,
    gl.prompt_full_text
FROM generation_logs gl
JOIN definities d ON gl.definitie_id = d.id
WHERE gl.generation_status = 'failed';

-- ============================================================
-- COMMENTS
-- ============================================================

-- Table purpose
COMMENT ON TABLE generation_logs IS
'Audit trail for AI-generated definitions. Stores complete prompt context,
model parameters, and response metadata for reproducibility and compliance.';

-- Column comments
COMMENT ON COLUMN generation_logs.prompt_full_text IS
'Complete prompt sent to GPT-4 including all modules. Typically 5KB-15KB.';

COMMENT ON COLUMN generation_logs.generation_status IS
'pending: Log created before API call
success: Definition generated successfully
failed: API error or validation failure
timeout: Request timed out';
```

---

## 📦 DATA MODEL

### Python Models

**File:** `src/models/generation_context.py` (NEW)

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

@dataclass
class ModelParameters:
    """OpenAI model configuration."""
    name: str                           # "gpt-4-turbo-2024-04-09"
    temperature: Decimal = Decimal("0.7")
    max_tokens: int = 2000
    top_p: Decimal = Decimal("1.0")
    frequency_penalty: Decimal = Decimal("0.0")
    presence_penalty: Decimal = Decimal("0.0")

@dataclass
class PromptContext:
    """Complete prompt context before API call."""
    full_text: str                      # Complete prompt (10KB+)
    template_version: str               # "2.0"
    template_name: str                  # "unified_definition_v2"
    modules_used: List[str]             # ["base", "context", "examples"]
    model_params: ModelParameters

@dataclass
class ResponseMetadata:
    """OpenAI API response metadata."""
    tokens_prompt: int
    tokens_completion: int
    tokens_total: int
    finish_reason: str                  # "stop", "length", etc.
    response_id: str                    # "chatcmpl-..."
    created_at: int                     # Unix timestamp
    duration_ms: int

@dataclass
class ErrorContext:
    """Error information if generation failed."""
    message: str
    error_type: str                     # "api_error", "timeout", etc.
    traceback: Optional[str] = None

@dataclass
class GenerationContext:
    """
    Complete generation context for audit trail.

    Lifecycle:
    1. Created with PromptContext (status='pending')
    2. Updated with ResponseMetadata (status='success') OR
       Updated with ErrorContext (status='failed')
    """
    id: Optional[int] = None
    definitie_id: Optional[int] = None

    # Prompt context (set at creation)
    prompt: PromptContext = None

    # Response metadata (set after API call)
    response: Optional[ResponseMetadata] = None

    # Error context (set if failed)
    error: Optional[ErrorContext] = None

    # Status tracking
    status: str = "pending"  # pending, success, failed, timeout

    # Additional metadata (extensibility)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    logged_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def mark_success(self, response: ResponseMetadata):
        """Update with successful response."""
        self.response = response
        self.status = "success"
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error: ErrorContext):
        """Update with failure information."""
        self.error = error
        self.status = "failed"
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage."""
        return {
            'id': self.id,
            'definitie_id': self.definitie_id,
            'prompt': {
                'full_text': self.prompt.full_text,
                'template_version': self.prompt.template_version,
                'template_name': self.prompt.template_name,
                'modules_used': self.prompt.modules_used,
                'model_params': {
                    'name': self.prompt.model_params.name,
                    'temperature': float(self.prompt.model_params.temperature),
                    'max_tokens': self.prompt.model_params.max_tokens,
                    'top_p': float(self.prompt.model_params.top_p),
                    'frequency_penalty': float(self.prompt.model_params.frequency_penalty),
                    'presence_penalty': float(self.prompt.model_params.presence_penalty),
                }
            },
            'response': {
                'tokens_prompt': self.response.tokens_prompt,
                'tokens_completion': self.response.tokens_completion,
                'tokens_total': self.response.tokens_total,
                'finish_reason': self.response.finish_reason,
                'response_id': self.response.response_id,
                'created_at': self.response.created_at,
                'duration_ms': self.response.duration_ms,
            } if self.response else None,
            'error': {
                'message': self.error.message,
                'error_type': self.error.error_type,
                'traceback': self.error.traceback,
            } if self.error else None,
            'status': self.status,
            'metadata': self.metadata,
            'logged_at': self.logged_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
```

---

## 🔧 SERVICE LAYER CHANGES

### 1. UnifiedDefinitionGenerator

**File:** `src/services/generation/unified_definition_generator.py`

**Changes:**

```python
from models.generation_context import (
    GenerationContext, PromptContext, ModelParameters,
    ResponseMetadata, ErrorContext
)
from repositories.generation_log_repository import GenerationLogRepository

class UnifiedDefinitionGenerator:
    def __init__(
        self,
        ai_service: AIServiceV2,
        prompt_orchestrator: PromptOrchestrator,
        generation_log_repo: GenerationLogRepository  # NEW dependency
    ):
        self.ai_service = ai_service
        self.prompt_orchestrator = prompt_orchestrator
        self.generation_log_repo = generation_log_repo  # NEW

    def generate_definition(self, input_data: dict) -> dict:
        """
        Generate definition with complete audit trail.

        Returns:
            {
                'definitie': str,
                'generation_log_id': int,
                'tokens_used': int,
                'duration_ms': int
            }
        """
        # Step 1: Build complete prompt
        prompt_result = self.prompt_orchestrator.build_prompt(input_data)
        prompt_text = prompt_result['complete_prompt']
        modules_used = prompt_result['modules_used']

        # Step 2: Prepare model parameters
        model_params = ModelParameters(
            name=self.ai_service.model_name,
            temperature=Decimal(str(self.ai_service.temperature)),
            max_tokens=self.ai_service.max_tokens,
            # ... other params
        )

        # Step 3: Create generation context
        prompt_context = PromptContext(
            full_text=prompt_text,
            template_version="2.0",  # From config
            template_name="unified_definition_v2",
            modules_used=modules_used,
            model_params=model_params
        )

        generation_context = GenerationContext(
            prompt=prompt_context,
            status="pending"
        )

        # Step 4: Create pending log BEFORE API call
        log_id = self.generation_log_repo.create_pending_log(generation_context)
        generation_context.id = log_id

        # Step 5: Call GPT-4
        start_time = datetime.utcnow()

        try:
            response = self.ai_service.generate(
                prompt=prompt_text,
                temperature=float(model_params.temperature),
                max_tokens=model_params.max_tokens
            )

            # Step 6: Calculate duration
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Step 7: Create response metadata
            response_meta = ResponseMetadata(
                tokens_prompt=response.usage.prompt_tokens,
                tokens_completion=response.usage.completion_tokens,
                tokens_total=response.usage.total_tokens,
                finish_reason=response.finish_reason,
                response_id=response.id,
                created_at=response.created,
                duration_ms=duration_ms
            )

            # Step 8: Update generation log with success
            generation_context.mark_success(response_meta)
            self.generation_log_repo.update_with_response(
                log_id,
                generation_context
            )

            # Step 9: Return result
            return {
                'definitie': response.choices[0].message.content,
                'generation_log_id': log_id,
                'tokens_used': response_meta.tokens_total,
                'duration_ms': duration_ms
            }

        except Exception as e:
            # Step 10: Log failure
            error_ctx = ErrorContext(
                message=str(e),
                error_type=type(e).__name__,
                traceback=traceback.format_exc()
            )

            generation_context.mark_failed(error_ctx)
            self.generation_log_repo.update_with_error(
                log_id,
                generation_context
            )

            # Re-raise for caller to handle
            raise
```

---

## 📂 REPOSITORY LAYER

### GenerationLogRepository

**File:** `src/repositories/generation_log_repository.py` (NEW)

```python
import json
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from models.generation_context import GenerationContext, ErrorContext
from database.connection import get_connection

class GenerationLogRepository:
    """Repository for generation_logs table."""

    def create_pending_log(self, context: GenerationContext) -> int:
        """
        Create pending generation log BEFORE API call.

        Args:
            context: GenerationContext with PromptContext filled

        Returns:
            generation_log_id
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO generation_logs (
                prompt_full_text,
                prompt_template_version,
                prompt_template_name,
                prompt_modules_used,
                model_name,
                model_temperature,
                model_max_tokens,
                model_top_p,
                model_frequency_penalty,
                model_presence_penalty,
                generation_status,
                logged_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (
            context.prompt.full_text,
            context.prompt.template_version,
            context.prompt.template_name,
            json.dumps(context.prompt.modules_used),
            context.prompt.model_params.name,
            float(context.prompt.model_params.temperature),
            context.prompt.model_params.max_tokens,
            float(context.prompt.model_params.top_p),
            float(context.prompt.model_params.frequency_penalty),
            float(context.prompt.model_params.presence_penalty),
            context.logged_at.isoformat()
        ))

        log_id = cursor.lastrowid
        conn.commit()

        return log_id

    def update_with_response(
        self,
        log_id: int,
        context: GenerationContext
    ) -> None:
        """
        Update generation log with successful response metadata.

        Args:
            log_id: Generation log ID
            context: GenerationContext with ResponseMetadata filled
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE generation_logs SET
                tokens_prompt = ?,
                tokens_completion = ?,
                tokens_total = ?,
                duration_ms = ?,
                response_finish_reason = ?,
                response_id = ?,
                response_created_at = ?,
                generation_status = 'success',
                updated_at = ?
            WHERE id = ?
        """, (
            context.response.tokens_prompt,
            context.response.tokens_completion,
            context.response.tokens_total,
            context.response.duration_ms,
            context.response.finish_reason,
            context.response.response_id,
            context.response.created_at,
            context.updated_at.isoformat(),
            log_id
        ))

        conn.commit()

    def update_with_error(
        self,
        log_id: int,
        context: GenerationContext
    ) -> None:
        """
        Update generation log with error information.

        Args:
            log_id: Generation log ID
            context: GenerationContext with ErrorContext filled
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE generation_logs SET
                error_message = ?,
                error_type = ?,
                error_traceback = ?,
                generation_status = 'failed',
                updated_at = ?
            WHERE id = ?
        """, (
            context.error.message,
            context.error.error_type,
            context.error.traceback,
            context.updated_at.isoformat(),
            log_id
        ))

        conn.commit()

    def link_to_definitie(self, log_id: int, definitie_id: int) -> None:
        """
        Link generation log to definitie after definitie is saved.

        Args:
            log_id: Generation log ID
            definitie_id: Definitie ID
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE generation_logs
            SET definitie_id = ?
            WHERE id = ?
        """, (definitie_id, log_id))

        conn.commit()

    def get_by_definitie_id(self, definitie_id: int) -> Optional[GenerationContext]:
        """
        Retrieve generation log for a definitie.

        Args:
            definitie_id: Definitie ID

        Returns:
            GenerationContext or None if not found
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM generation_logs
            WHERE definitie_id = ?
        """, (definitie_id,))

        row = cursor.fetchone()

        if not row:
            return None

        # Convert row to GenerationContext
        return self._row_to_context(row)

    def get_prompt_history(
        self,
        template_version: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[GenerationContext]:
        """
        Query generation logs for analysis.

        Args:
            template_version: Filter by template version
            from_date: Filter by date range (start)
            to_date: Filter by date range (end)
            status: Filter by generation status
            limit: Maximum results

        Returns:
            List of GenerationContext
        """
        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM generation_logs WHERE 1=1"
        params = []

        if template_version:
            query += " AND prompt_template_version = ?"
            params.append(template_version)

        if from_date:
            query += " AND logged_at >= ?"
            params.append(from_date.isoformat())

        if to_date:
            query += " AND logged_at <= ?"
            params.append(to_date.isoformat())

        if status:
            query += " AND generation_status = ?"
            params.append(status)

        query += " ORDER BY logged_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [self._row_to_context(row) for row in rows]

    def _row_to_context(self, row: tuple) -> GenerationContext:
        """Convert database row to GenerationContext."""
        # Implementation: Map row columns to GenerationContext fields
        # ... (omitted for brevity)
        pass
```

---

## 🔗 INTEGRATION POINTS

### 1. Definition Creation Flow

**File:** `src/ui/tabs/creation_tab.py`

```python
def on_generate_button_click():
    """User clicked 'Genereer Definitie' button."""

    # Step 1: Collect input
    input_data = collect_user_input()

    # Step 2: Generate definitie (with logging)
    result = generator.generate_definition(input_data)

    # Step 3: Save definitie to database
    definitie_id = repository.save_definitie({
        'begrip': input_data['begrip'],
        'definitie': result['definitie'],
        'source_type': 'generated',
        # ... other fields
    })

    # Step 4: Link generation log to definitie
    generation_log_repo.link_to_definitie(
        log_id=result['generation_log_id'],
        definitie_id=definitie_id
    )

    # Step 5: Show success message
    st.success(f"Definitie gegenereerd in {result['duration_ms']}ms")
    st.info(f"Tokens gebruikt: {result['tokens_used']}")
```

---

### 2. Definitie Detail View (Optional Phase 2)

**File:** `src/ui/components/definitie_detail.py`

```python
def show_generation_details(definitie_id: int):
    """Show generation metadata in expander."""

    # Fetch generation log
    log = generation_log_repo.get_by_definitie_id(definitie_id)

    if not log:
        st.info("Geen generatie metadata beschikbaar (geïmporteerde of legacy definitie)")
        return

    with st.expander("📊 Generatie Details"):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Model", log.prompt.model_params.name)
            st.metric("Temperature", float(log.prompt.model_params.temperature))

        with col2:
            st.metric("Tokens Gebruikt", log.response.tokens_total)
            st.metric("Prompt Tokens", log.response.tokens_prompt)
            st.metric("Completion Tokens", log.response.tokens_completion)

        with col3:
            st.metric("Generatietijd", f"{log.response.duration_ms}ms")
            st.metric("Template Versie", log.prompt.template_version)

        # Show full prompt (collapsible)
        if st.checkbox("Toon Volledige Prompt"):
            st.code(log.prompt.full_text, language="markdown")
```

---

## 🚀 MIGRATION STRATEGY

### Phase 1: Database Migration (Week 1, Day 1)

```bash
# Run migration
python src/database/migrate_database.py

# Verify schema
sqlite3 data/definities.db "PRAGMA table_info(generation_logs);"

# Check indexes
sqlite3 data/definities.db ".indexes generation_logs"
```

### Phase 2: Code Deployment (Week 1, Day 2-4)

**Step 1:** Deploy repository layer
- Create `GenerationLogRepository`
- Add tests

**Step 2:** Deploy service layer
- Update `UnifiedDefinitionGenerator`
- Add generation context capture

**Step 3:** Deploy UI layer
- Update creation tab to link logs
- Add generation details view (optional)

### Phase 3: Validation (Week 1, Day 5)

**Test in production:**
- Generate 10 test definitions
- Verify all have generation_logs entries
- Check prompt_full_text is complete
- Verify token counts match

---

## 🧪 TESTING STRATEGY

### Unit Tests

**File:** `tests/repositories/test_generation_log_repository.py`

```python
def test_create_pending_log():
    """Verify pending log created with correct fields."""
    pass

def test_update_with_response():
    """Verify log updated with response metadata."""
    pass

def test_update_with_error():
    """Verify log updated with error information."""
    pass

def test_link_to_definitie():
    """Verify definitie_id linked correctly."""
    pass

def test_get_by_definitie_id():
    """Verify log retrieved by definitie_id."""
    pass

def test_get_prompt_history_filters():
    """Verify query filters work correctly."""
    pass
```

### Integration Tests

**File:** `tests/integration/test_generation_with_logging.py`

```python
def test_end_to_end_generation():
    """
    Full generation flow with logging:
    1. Generate definitie
    2. Verify definitie saved
    3. Verify generation log created
    4. Verify link exists
    5. Verify prompt is complete
    """
    pass

def test_generation_failure_logged():
    """Verify failures are logged with error details."""
    pass

def test_token_count_accuracy():
    """Verify logged token counts match actual usage."""
    pass
```

---

## ⚡ PERFORMANCE CONSIDERATIONS

### Expected Overhead

**Per Generation:**
- 2x database INSERT: ~10ms each = 20ms
- 1x database UPDATE: ~10ms
- JSON serialization: ~5ms
- **Total overhead: ~35ms** (<100ms target ✅)

### Prompt Storage Size

**Typical prompt:**
- Base: 2KB
- Context: 1KB
- Examples: 3KB
- Rules: 4KB
- **Total: ~10KB per log**

**Storage calculation (1 year):**
- 1,000 definitions/year × 10KB = 10MB/year ✅
- Negligible storage impact

### Database Size Impact

**After 1 year:**
- `definities` table: ~1MB (existing)
- `generation_logs` table: ~10MB (new)
- **Total: ~11MB** (very manageable ✅)

---

## 🔒 SECURITY & PRIVACY

### Sensitive Data in Prompts

**Risk:** Prompts may contain PII from context fields

**Mitigation:**
1. ✅ Same access controls as `definities` table
2. ✅ Cascade delete: Delete definitie → delete log
3. ⚠️ Consider: Redact PII from prompts before storage (Phase 2)

### GDPR Compliance

**Article 22: Right to Explanation**
- ✅ Generation logs provide explanation for AI decisions
- ✅ User can request: "Show me prompt used for definitie X"

**Article 17: Right to Erasure**
- ✅ ON DELETE CASCADE ensures log deleted with definitie

---

## 📅 ROLLOUT PLAN

### Week 1: Implementation

**Day 1:** Database migration
- [ ] Create migration script
- [ ] Test on dev database
- [ ] Deploy to production

**Day 2-3:** Repository + Service Layer
- [ ] Implement `GenerationLogRepository`
- [ ] Update `UnifiedDefinitionGenerator`
- [ ] Write unit tests

**Day 4:** Integration
- [ ] Update creation tab
- [ ] Link logs to definities
- [ ] Write integration tests

**Day 5:** Validation
- [ ] Generate 10 test definitions
- [ ] Verify logs complete
- [ ] Performance testing

### Week 2: Monitoring

**Day 1-5:** Production monitoring
- [ ] Check all new definitions have logs
- [ ] Monitor database size
- [ ] Monitor generation time overhead
- [ ] Fix any issues

### Week 3: Enhancement (Optional)

**UI enhancements:**
- [ ] Add generation details to definitie view
- [ ] Add admin dashboard: token usage trends
- [ ] Add export: generation logs to CSV

---

## ✅ ACCEPTANCE CRITERIA

### Must Have (Week 1)
- [ ] `generation_logs` table created
- [ ] All new definitions have generation log
- [ ] Prompt full text stored (not truncated)
- [ ] Token usage & duration captured
- [ ] Model parameters captured
- [ ] Tests passing (>95% coverage)
- [ ] Performance overhead <100ms

### Should Have (Week 2)
- [ ] UI shows generation metadata
- [ ] Admin can query logs
- [ ] Error logging works

### Nice to Have (Week 3)
- [ ] Export logs to CSV
- [ ] Compare prompts (diff view)
- [ ] Token usage dashboard

---

## 📚 APPENDIX

### A. Example Generation Log

```json
{
  "id": 123,
  "definitie_id": 456,
  "prompt_full_text": "# DEFINITIE GENERATIE\n\nGenereer een definitie voor...",
  "prompt_template_version": "2.0",
  "prompt_template_name": "unified_definition_v2",
  "prompt_modules_used": ["base", "context", "examples", "validation"],
  "model_name": "gpt-4-turbo-2024-04-09",
  "model_temperature": 0.7,
  "model_max_tokens": 2000,
  "tokens_prompt": 1234,
  "tokens_completion": 567,
  "tokens_total": 1801,
  "duration_ms": 2345,
  "response_finish_reason": "stop",
  "response_id": "chatcmpl-AbCdEf123456",
  "generation_status": "success",
  "logged_at": "2025-11-11T14:23:45.123Z",
  "updated_at": "2025-11-11T14:23:47.456Z"
}
```

### B. SQL Queries for Analysis

**Token usage over time:**
```sql
SELECT
    DATE(logged_at) as date,
    AVG(tokens_total) as avg_tokens,
    MAX(tokens_total) as max_tokens,
    COUNT(*) as generations
FROM generation_logs
WHERE generation_status = 'success'
GROUP BY DATE(logged_at)
ORDER BY date DESC;
```

**Most expensive prompts:**
```sql
SELECT
    d.begrip,
    gl.tokens_total,
    gl.duration_ms,
    gl.logged_at
FROM generation_logs gl
JOIN definities d ON gl.definitie_id = d.id
WHERE gl.generation_status = 'success'
ORDER BY gl.tokens_total DESC
LIMIT 10;
```

**Failure rate by template:**
```sql
SELECT
    prompt_template_version,
    COUNT(*) as total,
    SUM(CASE WHEN generation_status = 'failed' THEN 1 ELSE 0 END) as failures,
    ROUND(100.0 * SUM(CASE WHEN generation_status = 'failed' THEN 1 ELSE 0 END) / COUNT(*), 2) as failure_rate
FROM generation_logs
GROUP BY prompt_template_version;
```

---

## 🏁 CONCLUSION

**Implementation Status:** ✅ READY FOR DEVELOPMENT

**Key Benefits:**
- ✅ Complete audit trail (GDPR compliant)
- ✅ Reproducibility (exact prompts stored)
- ✅ Debugging capability (see what GPT-4 received)
- ✅ A/B testing framework (compare prompts)
- ✅ Low overhead (<100ms per generation)

**Next Steps:**
1. Review this specification
2. Approve database schema
3. Begin Week 1 implementation
4. Deploy to production
5. Monitor for 1 week

---

**Document Version:** 1.0
**Last Updated:** 2025-11-11
**Approved By:** [PENDING REVIEW]
**Implementation Target:** Week 1 (6-8 hours)

