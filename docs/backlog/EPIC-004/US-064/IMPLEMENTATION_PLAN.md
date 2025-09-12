# US-064: Definition Edit Interface - Geconsolideerd Implementatieplan

## Executive Summary

Dit plan combineert de architecturele robuustheid van het Codex-plan met de concrete implementatiedetails van het Claude-plan. Het volgt projectrichtlijnen (CLAUDE.md, README.md) en sluit aan op EPIC-012 (orchestratieconsolidatie).

**Kernprincipes:**
- Stateless services zonder UI-sessionstate als bron van waarheid
- Database-driven draft management met UNIQUE constraints
- Optimistic locking voor concurrent editing
- Privacy-first aanpak voor prompt opslag

## Doelen

1. **Editor toont standaard AI-gegenereerde definitie** (voorkeur opgeschoonde variant)
2. **Stateless architectuur** - geen Streamlit imports in services
3. **Draft management** met versies en audit trail
4. **Validatie met kwaliteitspoorten** bij publiceren
5. **Privacy controle** over prompt opslag

## Scope

### In Scope
- Tekstbewerking met preview/diff
- Context/metadata aanpassing (organisatorische/juridische context)
- Voorbeeldenbeheer per type met delta updates
- Draft opslag met versiebump
- Publiceren via workflow met kwaliteitspoorten

### Out of Scope
- WYSIWYG editor (markdown preview volstaat)
- Collaborative editing
- Real-time synchronisatie

## Technische Architectuur

### UI Component Structuur

```python
# src/ui/components/definition_edit_interface.py
import logging
import time
from datetime import datetime
from typing import Optional, Any

import streamlit as st
from ui.helpers.async_bridge import run_async
from services.container import ServiceContainer
from services.interfaces import Definition

logger = logging.getLogger(__name__)

class DefinitionEditInterface:
    """Stateless edit interface component."""
    
    def __init__(self, container: ServiceContainer):
        self.container = container
        self.repository = container.repository()
        self.orchestrator = container.orchestrator()
        self.validator = container.validation_orchestrator_v2()
        
        # Voorbeelden type mapping
        self.VOORBEELD_TYPES = {
            'sentence': 'Voorbeeldzin',
            'practical': 'Praktisch voorbeeld',
            'counter': 'Tegenvoorbeeld',
            'synonyms': 'Synoniemen',
            'antonyms': 'Antoniemen',
            'explanation': 'Uitleg'
        }
    
    def render(self, definition_id: int):
        """Render edit interface met draft management."""
        # Haal of maak draft
        draft_id = self._get_or_create_draft(definition_id)
        draft = self.repository.get(draft_id)
        
        if not draft:
            st.error(f"Kan definitie {definition_id} niet laden")
            return
        
        # Toon editor met AI definitie voorgevuld
        self._render_editor(draft)
        self._render_preview(draft)
        self._render_validation(draft)
        self._render_actions(draft)
```

### Repository Extensions

```python
# src/services/definition_repository.py aanvullingen
import sqlite3
import logging
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List

logger = logging.getLogger(__name__)

def get_or_create_draft(self, definition_id: int) -> int:
    """
    Implementeert INSERT→SELECT transaction pattern.
    Voorkomt dubbele drafts door UNIQUE constraint.
    """
    with self._get_connection() as conn:
        cursor = conn.cursor()
        
        # Probeer eerst insert
        try:
            cursor.execute("""
                INSERT INTO definities (
                    begrip, definitie, organisatorische_context,
                    juridische_context, categorie, status,
                    previous_version_id, version_number
                )
                SELECT 
                    begrip, definitie, organisatorische_context,
                    juridische_context, categorie, 'draft',
                    id, version_number + 1
                FROM definities
                WHERE id = ?
            """, (definition_id,))
            
            conn.commit()
            return cursor.lastrowid
            
        except sqlite3.IntegrityError:
            # Draft bestaat al, haal op
            cursor.execute("""
                SELECT d2.id FROM definities d1
                JOIN definities d2 ON 
                    d2.begrip = d1.begrip AND
                    d2.organisatorische_context = d1.organisatorische_context AND
                    COALESCE(d2.juridische_context, '') = COALESCE(d1.juridische_context, '') AND
                    d2.categorie = d1.categorie AND
                    d2.status = 'draft'
                WHERE d1.id = ?
            """, (definition_id,))
            
            row = cursor.fetchone()
            if row:
                return row[0]
            raise ValueError(f"Kan geen draft vinden of maken voor {definition_id}")

def update_with_lock_check(self, definition_id: int, updates: dict, 
                          expected_updated_at: datetime) -> Tuple[bool, Optional[Dict]]:
    """
    Optimistic locking met rowcount verificatie.
    Returns: (success, server_version_if_conflict)
    """
    # Whitelist van toegestane kolommen (aligned met schema.sql)
    ALLOWED_COLUMNS = {
        'definitie', 'organisatorische_context', 'juridische_context',
        'categorie', 'status', 'validation_score', 'validation_date',
        'validation_issues', 'approved_by', 'approved_at', 'approval_notes',
        'last_exported_at', 'export_destinations', 'created_by', 'updated_by',
        'version_number', 'previous_version_id', 'wettelijke_basis',
        'ai_definition_raw', 'ai_definition_cleaned'
    }
    
    # Filter updates
    filtered_updates = {k: v for k, v in updates.items() if k in ALLOWED_COLUMNS}
    
    with self._get_connection() as conn:
        cursor = conn.cursor()
        
        # Build UPDATE query met lock check
        set_clause = ", ".join([f"{k} = ?" for k in filtered_updates.keys()])
        values = list(filtered_updates.values())
        values.extend([definition_id, expected_updated_at.isoformat()])
        
        cursor.execute(f"""
            UPDATE definities 
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND updated_at = ?
        """, values)
        
        if cursor.rowcount == 1:
            conn.commit()
            return (True, None)
        
        # Conflict - return server version
        cursor.execute("SELECT * FROM definities WHERE id = ?", (definition_id,))
        row = cursor.fetchone()
        if row:
            return (False, self._row_to_dict(row))
        
        return (False, None)

def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
    """Convert database row to dictionary."""
    return {key: row[key] for key in row.keys()}

def update_voorbeelden_delta(self, definitie_id: int, 
                            nieuwe: dict[str, list[str]]) -> None:
    """
    Delta update voor voorbeelden om autosave thrashing te voorkomen.
    Vergelijkt met bestaande en voert alleen nodige wijzigingen uit.
    """
    with self._get_connection() as conn:
        cursor = conn.cursor()
        
        # Haal bestaande voorbeelden op
        cursor.execute("""
            SELECT voorbeeld_type, voorbeeld_text, voorbeeld_volgorde
            FROM voorbeelden
            WHERE definitie_id = ? AND actief = 1
        """, (definitie_id,))
        
        bestaande = {}
        for row in cursor.fetchall():
            type_key = row[0]
            if type_key not in bestaande:
                bestaande[type_key] = []
            bestaande[type_key].append(row[1])
        
        # Bepaal delta
        for type_key, nieuwe_lijst in nieuwe.items():
            bestaande_lijst = bestaande.get(type_key, [])
            
            # Skip als identiek
            if nieuwe_lijst == bestaande_lijst:
                continue
            
            # Deactiveer oude
            cursor.execute("""
                UPDATE voorbeelden 
                SET actief = 0 
                WHERE definitie_id = ? AND voorbeeld_type = ?
            """, (definitie_id, type_key))
            
            # Insert nieuwe
            for idx, tekst in enumerate(nieuwe_lijst):
                cursor.execute("""
                    INSERT INTO voorbeelden (
                        definitie_id, voorbeeld_type, voorbeeld_text,
                        voorbeeld_volgorde, actief
                    ) VALUES (?, ?, ?, ?, 1)
                """, (definitie_id, type_key, tekst, idx))
        
        conn.commit()
```

### Orchestrator V2 Implementatie

```python
# src/services/orchestrators/definition_orchestrator_v2.py aanvullingen
import logging
from datetime import datetime
from typing import Any, Dict

from services.response_models import DefinitionResponseV2
from services.interfaces import Definition

logger = logging.getLogger(__name__)

async def update_definition(self, definition_id: int, 
                           updates: dict[str, Any]) -> DefinitionResponseV2:
    """
    Update definitie met validatie en cleaning.
    Gebruikt DefinitionResponseV2.metadata voor extended info.
    """
    start_time = datetime.now()
    
    try:
        # Load current definition
        definition = self.repository.get(definition_id)
        if not definition:
            return DefinitionResponseV2(
                success=False,
                error="Definition not found",
                metadata={"error_code": "NOT_FOUND"}
            )
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(definition, key):
                setattr(definition, key, value)
        
        # Clean if requested
        if updates.get("apply_cleaning", False):
            cleaning_result = await self.cleaning_service.clean_text(
                definition.definitie
            )
            definition.definitie = cleaning_result.cleaned_text
        
        # Validate
        validation_result = await self.validator.validate_text(
            begrip=definition.begrip,
            definitie=definition.definitie,
            categorie=definition.categorie,
            context={
                "organisatorische_context": definition.organisatorische_context,
                "juridische_context": definition.juridische_context
            }
        )
        
        # Check quality gates
        gates_passed = self._check_quality_gates(validation_result)
        
        # Save with lock check
        expected_updated_at = definition.updated_at
        success, conflict_data = self.repository.update_with_lock_check(
            definition_id, 
            updates,
            expected_updated_at
        )
        
        if not success:
            return DefinitionResponseV2(
                success=False,
                error="Concurrent modification detected",
                metadata={
                    "error_code": "CONFLICT",
                    "server_version": conflict_data
                }
            )
        
        # Return response
        return DefinitionResponseV2(
            success=True,
            definition_id=definition_id,
            definition=definition,
            validation_result=validation_result,
            metadata={
                "updated_fields": list(updates.keys()),
                "duration": (datetime.now() - start_time).total_seconds(),
                "orchestrator_version": "2.0",
                "gates_passed": gates_passed,
                "cleaning_applied": updates.get("apply_cleaning", False)
            }
        )
        
    except Exception as e:
        logger.error(f"Error updating definition: {e}")
        return DefinitionResponseV2(
            success=False,
            error=str(e),
            metadata={"error_code": "INTERNAL_ERROR"}
        )

def _check_quality_gates(self, validation_result: dict) -> bool:
    """
    Controleert kwaliteitspoorten voor publicatie.
    
    Gates:
    - Overall score ≥ 0.80
    - Juridisch & Structuur scores ≥ 0.75
    - Geen errors (severity='error')
    """
    # Overall score check
    if validation_result.get("overall_score", 0) < 0.80:
        return False
    
    # Category scores check
    detailed = validation_result.get("detailed_scores", {})
    if detailed.get("juridisch", 0) < 0.75:
        return False
    if detailed.get("structuur", 0) < 0.75:
        return False
    
    # No errors check
    for violation in validation_result.get("violations", []):
        if violation.get("severity") == "error":
            return False
    
    return True
```

### UI Navigatie & State Management

```python
# src/ui/components/definition_edit_interface.py

def _handle_navigation(self) -> Optional[int]:
    """
    Robuuste navigatie met query parameters en fallback.
    Geen dependency op session state voor data.
    """
    # Try modern query params first
    if hasattr(st, 'query_params'):
        draft_id = st.query_params.get('draft_id')
        if draft_id:
            return int(draft_id)
    
    # Fallback voor oudere Streamlit versies
    try:
        params = st.experimental_get_query_params()
        draft_id = params.get('draft_id', [None])[0]
        if draft_id:
            return int(draft_id)
    except AttributeError:
        pass
    
    # Check voor form submission (als fallback)
    if "edit_definition_id" in st.session_state:
        # Alleen voor navigatie, niet voor data
        definition_id = st.session_state.edit_definition_id
        del st.session_state.edit_definition_id
        return definition_id
    
    return None

def _render_editor(self, draft: Definition):
    """
    Render editor met AI definitie voorgevuld.
    Voorkeursvolgorde: cleaned AI → raw AI → current.
    """
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 Bewerk Definitie")
        
        # Bepaal voorvultekst
        if draft.metadata.get("ai_definition_cleaned"):
            default_text = draft.metadata["ai_definition_cleaned"]
            source = "AI (opgeschoond)"
        elif draft.metadata.get("ai_definition_raw"):
            default_text = draft.metadata["ai_definition_raw"]
            source = "AI (origineel)"
        else:
            default_text = draft.definitie
            source = "Huidige versie"
        
        st.caption(f"Bron: {source}")
        
        # Editor met throttled auto-save
        new_text = st.text_area(
            "Definitie",
            value=default_text,
            height=300,
            key=f"editor_{draft.id}",
            help="Bewerk de definitie. Wijzigingen worden automatisch opgeslagen als concept."
        )
        
        # Auto-save met cooldown (2 sec)
        if new_text != draft.definitie:
            if self._should_autosave():
                self._save_draft(draft.id, {"definitie": new_text})
                st.success("✅ Concept opgeslagen", icon="💾")
    
    with col2:
        st.subheader("🔍 Preview")
        with st.container(border=True):
            st.markdown(new_text)
        
        # Diff view
        if st.checkbox("Toon verschillen"):
            self._render_diff(default_text, new_text)

def _should_autosave(self) -> bool:
    """Throttle autosave om rate limits te respecteren."""
    last_save = st.session_state.get("last_autosave", 0)
    now = time.time()
    
    if now - last_save >= 2.0:  # 2 seconden cooldown
        st.session_state.last_autosave = now
        return True
    return False
```

### Workflow Service Integratie

```python
# src/services/workflow/definition_workflow_service.py aanpassing

class WorkflowResult:
    """Gestandaardiseerd workflow resultaat."""
    
    def __init__(self, success: bool, data: Any = None, 
                 error_code: str = None, message: str = None):
        self.success = success
        self.data = data
        self.error_code = error_code  # INVALID_TRANSITION, CONFLICT, NOT_FOUND
        self.message = message

class DefinitionWorkflowService:
    """Workflow service met uniforme error handling."""
    
    def update_status(self, definition_id: int, new_status: str,
                     user: str = None) -> WorkflowResult:
        """
        Adapter method voor services-repository integratie.
        Mapt naar database change_status met error handling.
        """
        try:
            # Valideer transitie
            current = self.repository.get(definition_id)
            if not current:
                return WorkflowResult(
                    success=False,
                    error_code="NOT_FOUND",
                    message=f"Definition {definition_id} not found"
                )
            
            if not self._is_valid_transition(current.status, new_status):
                return WorkflowResult(
                    success=False,
                    error_code="INVALID_TRANSITION",
                    message=f"Cannot transition from {current.status} to {new_status}"
                )
            
            # Gebruik database repository change_status
            self.db_repository.change_status(
                definition_id, 
                new_status,
                changed_by=user
            )
            
            return WorkflowResult(
                success=True,
                data={"old_status": current.status, "new_status": new_status}
            )
            
        except Exception as e:
            logger.error(f"Workflow error: {e}")
            return WorkflowResult(
                success=False,
                error_code="INTERNAL_ERROR",
                message=str(e)
            )
```

## Validatie & Kwaliteitspoorten

### Validatie Tijdens Bewerken

```python
def _render_validation(self, draft: Definition):
    """Render validatie panel met throttling."""
    
    if st.button("🔍 Valideer", key=f"validate_{draft.id}"):
        with st.spinner("Validatie wordt uitgevoerd..."):
            # Gebruik run_async bridge naar V2 validator
            validation_result = run_async(
                self.validator.validate_text(
                    begrip=draft.begrip,
                    definitie=draft.definitie,
                    categorie=draft.categorie,
                    context={
                        "organisatorische_context": draft.organisatorische_context,
                        "juridische_context": draft.juridische_context
                    }
                )
            )
            
            # Cache resultaat
            st.session_state[f"validation_{draft.id}"] = validation_result
    
    # Toon resultaat
    if f"validation_{draft.id}" in st.session_state:
        result = st.session_state[f"validation_{draft.id}"]
        self._render_validation_result(result)
```

### Kwaliteitspoorten bij Publiceren

```python
def _can_publish(self, validation_result: dict) -> tuple[bool, list[str]]:
    """
    Controleert of definitie voldoet aan kwaliteitspoorten.
    
    Returns:
        (can_publish, list_of_blocking_issues)
    """
    issues = []
    
    # Overall score ≥ 0.80
    if validation_result.get("overall_score", 0) < 0.80:
        issues.append(f"Overall score te laag: {validation_result['overall_score']:.2f} (min: 0.80)")
    
    # Category scores ≥ 0.75
    detailed = validation_result.get("detailed_scores", {})
    if detailed.get("juridisch", 0) < 0.75:
        issues.append(f"Juridische score te laag: {detailed['juridisch']:.2f} (min: 0.75)")
    if detailed.get("structuur", 0) < 0.75:
        issues.append(f"Structuur score te laag: {detailed['structuur']:.2f} (min: 0.75)")
    
    # Geen errors
    errors = [v for v in validation_result.get("violations", []) 
              if v.get("severity") == "error"]
    if errors:
        issues.append(f"{len(errors)} error(s) gevonden - los deze eerst op")
    
    return (len(issues) == 0, issues)
```

## Privacy & Prompt Opslag

```python
def _handle_prompt_storage(self, definition: Definition, prompt: str) -> None:
    """
    Beheer prompt opslag met privacy controles.
    Gebruiker bepaalt of prompt wordt opgeslagen.
    """
    if st.checkbox("💾 Bewaar prompt voor toekomstige referentie", 
                   value=False,
                   help="Prompt wordt veilig opgeslagen in de database"):
        
        # Sla prompt op in metadata
        definition.metadata["generation_prompt"] = prompt
        definition.metadata["prompt_stored_at"] = datetime.now().isoformat()
        definition.metadata["prompt_consent"] = True
        
        # Optioneel: hash voor privacy
        import hashlib
        definition.metadata["prompt_hash"] = hashlib.sha256(
            prompt.encode()
        ).hexdigest()
    else:
        # Verwijder eventuele bestaande prompt
        definition.metadata.pop("generation_prompt", None)
        definition.metadata["prompt_consent"] = False
```

## Implementatie Mijlpalen

### Mijlpaal 1: Backend Foundations (2 dagen)
- ✅ Repository extensions (get_or_create_draft, update_with_lock_check, update_voorbeelden_delta)
- ✅ Orchestrator V2 update_definition met response contract
- ✅ Workflow service adapter met WorkflowResult
- ✅ Database whitelist implementatie

### Mijlpaal 2: UI Editor MVP (3 dagen)
- ✅ Edit interface component met stateless design
- ✅ Editor met AI definitie voorvulling
- ✅ Preview/diff functionaliteit
- ✅ Navigatie met query params & fallback

### Mijlpaal 3: Validatie & Voorbeelden (2 dagen)
- ✅ Validatie panel met throttling
- ✅ Kwaliteitspoorten implementatie
- ✅ Voorbeelden CRUD met delta updates
- ✅ Type mapping voor voorbeelden

### Mijlpaal 4: Polish & Integratie (2 dagen)
- ✅ Concurrency UI (merge/conflict handling)
- ✅ Auto-save met cooldown
- ✅ Privacy controls voor prompt opslag
- ✅ End-to-end testing

## Test Strategie

### Unit Tests
```python
# tests/services/test_definition_repository.py
def test_get_or_create_draft_transaction():
    """Test INSERT→SELECT pattern voor draft creation."""
    
def test_update_with_lock_check():
    """Test optimistic locking met rowcount."""
    
def test_update_voorbeelden_delta():
    """Test delta updates voorkomt thrashing."""

# tests/services/test_orchestrator_v2.py
def test_update_definition_with_validation():
    """Test update flow met cleaning en validatie."""
    
def test_quality_gates_enforcement():
    """Test kwaliteitspoorten blokkeren publicatie."""
```

### Integratie Tests
```python
# tests/integration/test_edit_workflow.py
def test_complete_edit_flow():
    """
    Test: open → edit → validate → save → publish → approve
    """
    
def test_concurrent_edit_handling():
    """Test conflict detection en merge UI."""
```

### Regressie Tests
- Versie management met audit trail
- UNIQUE constraint handhaving
- Query parameter navigatie fallback
- Cache invalidatie bij updates

## Risico's & Mitigatie

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| Concurrent editing conflicts | Hoog | Optimistic locking + merge UI |
| Autosave performance | Medium | Delta updates + 2s cooldown |
| Session state dependencies | Hoog | Query params + form fallback |
| Rate limit violations | Medium | Throttling + explicit save |
| UNIQUE constraint violations | Hoog | INSERT→SELECT pattern |

## Acceptatiecriteria

- ✅ AI-definitie standaard zichtbaar in editor
- ✅ Preview/diff functionaliteit werkt
- ✅ Context/metadata bewerkbaar en persistent
- ✅ Voorbeelden CRUD zonder thrashing
- ✅ Draft opslag met audit trail
- ✅ Publicatie alleen met kwaliteitspoorten
- ✅ Geen session state als data bron
- ✅ Privacy controle over prompt opslag
- ✅ Concurrent edit handling

## Database Migratie

### Schema Updates

```sql
-- migrations/add_edit_interface_columns.sql
-- Voeg AI definitie kolommen toe
ALTER TABLE definities ADD COLUMN IF NOT EXISTS 
    ai_definition_raw TEXT;
ALTER TABLE definities ADD COLUMN IF NOT EXISTS 
    ai_definition_cleaned TEXT;

-- Create audit trail table
CREATE TABLE IF NOT EXISTS definitie_geschiedenis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER NOT NULL REFERENCES definities(id),
    actie VARCHAR(50) NOT NULL, -- 'CREATE', 'UPDATE', 'DELETE', 'STATUS_CHANGE'
    oude_waarde TEXT, -- JSON van oude record
    nieuwe_waarde TEXT, -- JSON van nieuwe record
    gewijzigd_door VARCHAR(255),
    gewijzigd_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    wijzigingen TEXT -- JSON van specifieke veld wijzigingen
);

-- Create index voor performance
CREATE INDEX IF NOT EXISTS idx_geschiedenis_definitie 
    ON definitie_geschiedenis(definitie_id, gewijzigd_op DESC);

-- Trigger voor audit trail
CREATE TRIGGER IF NOT EXISTS definitie_audit_update
AFTER UPDATE ON definities
FOR EACH ROW
BEGIN
    INSERT INTO definitie_geschiedenis (
        definitie_id, actie, oude_waarde, nieuwe_waarde, 
        gewijzigd_door, wijzigingen
    )
    VALUES (
        NEW.id, 
        'UPDATE',
        json_object(
            'definitie', OLD.definitie,
            'status', OLD.status,
            'version', OLD.version_number
        ),
        json_object(
            'definitie', NEW.definitie,
            'status', NEW.status,
            'version', NEW.version_number
        ),
        NEW.updated_by,
        json_object(
            'changed_fields', 
            CASE 
                WHEN OLD.definitie != NEW.definitie THEN 'definitie,'
                ELSE ''
            END ||
            CASE 
                WHEN OLD.status != NEW.status THEN 'status,'
                ELSE ''
            END
        )
    );
END;
```

## UI Integratie

### Integratie in Bestaande Tabs

```python
# src/ui/tabs/definition_generator_tab.py aanpassing
def _render_existing_definition_actions(self, definition: Definition):
    """Render action buttons voor bestaande definitie."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✏️ Bewerk", key=f"edit_{definition.id}"):
            # Navigeer naar edit interface via query params
            st.query_params["draft_id"] = str(definition.id)
            st.query_params["tab"] = "edit"
            st.rerun()
    
    with col2:
        if st.button("📋 Kopieer", key=f"copy_{definition.id}"):
            st.clipboard.write(definition.definitie)
            st.success("Gekopieerd!")
    
    with col3:
        if st.button("🗑️ Archiveer", key=f"archive_{definition.id}"):
            self._archive_definition(definition.id)

# src/main.py aanpassing voor tab routing
def render_main_interface():
    """Render hoofdinterface met tabs."""
    # Check voor edit mode via query params
    if st.query_params.get("tab") == "edit":
        draft_id = st.query_params.get("draft_id")
        if draft_id:
            # Render edit interface
            edit_interface = DefinitionEditInterface(
                st.session_state.service_container
            )
            edit_interface.render(int(draft_id))
            
            # Terug naar hoofdinterface knop
            if st.button("← Terug naar overzicht"):
                del st.query_params["tab"]
                del st.query_params["draft_id"]
                st.rerun()
            return
    
    # Normal tab rendering
    render_tabs()
```

## Performance Optimalisaties

### Caching Strategy

```python
# src/ui/components/definition_edit_interface.py aanvulling

@st.cache_data(ttl=300)  # 5 minuten cache
def _get_draft_cached(repository, definition_id: int, 
                     cache_buster: str) -> Optional[Definition]:
    """Cache draft lookups voor performance."""
    return repository.get(definition_id)

def _get_draft_with_cache(self, definition_id: int) -> Optional[Definition]:
    """Haal draft met caching."""
    # Use updated_at als cache buster
    current = self.repository.get(definition_id)
    if current:
        cache_buster = current.updated_at.isoformat()
        return _get_draft_cached(
            self.repository, 
            definition_id, 
            cache_buster
        )
    return None
```

### Batch Operations

```python
def update_voorbeelden_batch(self, updates: List[Tuple[int, Dict[str, List[str]]]]) -> None:
    """
    Batch update voor meerdere definities tegelijk.
    Reduces database round trips.
    """
    with self._get_connection() as conn:
        cursor = conn.cursor()
        
        try:
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            
            for definitie_id, nieuwe_voorbeelden in updates:
                # Gebruik existing delta logic
                self._update_voorbeelden_delta_internal(
                    cursor, definitie_id, nieuwe_voorbeelden
                )
            
            cursor.execute("COMMIT")
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            logger.error(f"Batch update failed: {e}")
            raise
```

## Monitoring & Logging

### Structured Logging

```python
# src/ui/components/definition_edit_interface.py

import structlog

logger = structlog.get_logger()

def _log_edit_session(self, action: str, definition_id: int, 
                     metadata: Dict[str, Any] = None):
    """Log edit session events voor monitoring."""
    logger.info(
        "edit_session_event",
        action=action,
        definition_id=definition_id,
        user=st.session_state.get("user", "anonymous"),
        timestamp=datetime.now().isoformat(),
        metadata=metadata or {}
    )

def _save_draft(self, draft_id: int, updates: Dict[str, Any]):
    """Save draft met logging."""
    start_time = time.time()
    
    try:
        success, conflict = self.repository.update_with_lock_check(
            draft_id, updates, self.draft.updated_at
        )
        
        duration = time.time() - start_time
        
        self._log_edit_session(
            "draft_saved",
            draft_id,
            {
                "success": success,
                "duration_ms": duration * 1000,
                "fields_updated": list(updates.keys()),
                "conflict": conflict is not None
            }
        )
        
        return success
        
    except Exception as e:
        self._log_edit_session(
            "draft_save_failed",
            draft_id,
            {"error": str(e)}
        )
        raise
```

## Error Recovery

### Retry Logic & Rollback

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class DefinitionEditInterface:
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    def _save_with_retry(self, draft_id: int, updates: Dict[str, Any]) -> bool:
        """Save met automatic retry voor transient failures."""
        try:
            return self._save_draft(draft_id, updates)
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                logger.warning(f"Database locked, retrying: {e}")
                raise  # Tenacity will retry
            raise  # Other errors propagate
    
    def _rollback_on_failure(self, definition_id: int, 
                           original_state: Definition):
        """Rollback naar originele state bij failure."""
        try:
            # Restore original
            self.repository.update(
                definition_id,
                {
                    "definitie": original_state.definitie,
                    "status": original_state.status,
                    "updated_at": original_state.updated_at
                }
            )
            st.warning("Wijzigingen teruggedraaid vanwege fout")
            
        except Exception as e:
            st.error(f"Rollback mislukt: {e}")
            logger.error(f"Rollback failed for {definition_id}: {e}")
```

## Keyboard Shortcuts

```python
# src/ui/components/definition_edit_interface.py

def _setup_keyboard_shortcuts(self):
    """Setup keyboard shortcuts voor edit acties."""
    
    # JavaScript injection voor shortcuts
    st.markdown("""
    <script>
    document.addEventListener('keydown', function(e) {
        // Ctrl+S: Save draft
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            document.querySelector('[data-testid="save-draft"]').click();
        }
        
        // Ctrl+Enter: Validate
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            document.querySelector('[data-testid="validate"]').click();
        }
        
        // Escape: Close editor
        if (e.key === 'Escape') {
            document.querySelector('[data-testid="close-editor"]').click();
        }
    });
    </script>
    """, unsafe_allow_html=True)
    
    # Help text
    with st.expander("⌨️ Keyboard Shortcuts"):
        st.markdown("""
        - **Ctrl+S**: Opslaan als concept
        - **Ctrl+Enter**: Valideer definitie
        - **Escape**: Sluit editor
        - **Ctrl+Z**: Ongedaan maken (in tekstveld)
        """)
```

## Conclusie

Dit geconsolideerde en verbeterde plan combineert:
- **Architecturele robuustheid** van het Codex-plan (transaction patterns, delta updates)
- **Concrete implementatiedetails** van het Claude-plan (code voorbeelden, UI flow)
- **Praktische verbeteringen** zoals database migraties, monitoring, error recovery
- **Complete integratie** met bestaande UI en services

Het resultaat is een production-ready implementatie die voldoet aan alle projectrichtlijnen, inclusief proper imports, database alignment, audit trail, en performance optimalisaties.