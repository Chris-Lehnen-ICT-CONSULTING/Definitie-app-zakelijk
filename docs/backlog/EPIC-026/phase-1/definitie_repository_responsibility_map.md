---
id: EPIC-026-RESP-MAP-001
epic: EPIC-026
phase: 1
titel: definitie_repository.py Responsibility Map
status: complete
aangemaakt: 2025-10-02
owner: code-architect
canonical: true
applies_to: definitie-app@epic-026
last_verified: 2025-10-02
---

# definitie_repository.py Responsibility Map

**Analysis Date:** 2025-10-02
**Phase:** EPIC-026 Phase 1 - Design
**Day:** 1 of 5
**Agent:** Code Architect

---

## Executive Summary

**File:** `src/database/definitie_repository.py`
**LOC:** 1,815 lines
**Methods:** 41 methods
**Classes:** 5 (DefinitieStatus, SourceType, DefinitieRecord, VoorbeeldenRecord, DuplicateMatch, DefinitieRepository)
**Primary Responsibilities:** Complete database abstraction layer for definition management system

**Assessment:** **MEDIUM-HIGH complexity** God Object with clear internal structure and excellent test coverage (51 tests). Boundaries are identifiable but extraction requires careful dependency management.

**Migration Complexity:** **MEDIUM** - Clear READ/WRITE/BULK/VOORBEELDEN boundaries exist, good test coverage provides safety net, but complex duplicate detection and transaction logic needs careful handling.

---

## Overview

### Purpose
DefinitieRepository provides a complete database abstraction layer for all definitie (definition) management operations, including:
- CRUD operations for definitions
- Duplicate detection (exact + fuzzy + synonym matching)
- Voorbeelden (examples) management (sentences, practical, counter, synonyms, antonyms)
- Import/Export functionality (JSON)
- Search and filtering
- Status management and approval workflow
- History/audit logging

### God Object Indicators
- **Size:** 1,815 LOC (target: <500)
- **Method count:** 41 methods
- **Multiple responsibilities:** Database access, duplicate detection, validation, import/export, logging, similarity calculation
- **Mixed concerns:** Data access, business logic (duplicate rules), utility functions (similarity)

---

## Method Inventory (41 Methods)

### Responsibility 1: DATABASE CONNECTION & INITIALIZATION (~150 LOC)

**Methods:**
1. `__init__(db_path)` - Initialize repository with database connection
   - LOC: ~5
   - Dependencies: Path, logging
   - Returns: None
   - Purpose: Set up database path and initialize schema

2. `_get_connection(timeout)` - Create database connection with proper settings
   - LOC: ~23
   - Dependencies: sqlite3
   - Returns: sqlite3.Connection
   - Purpose: Provide configured connection with WAL mode, pragmas, row factory
   - **Cross-cutting:** Used by ALL database operations

3. `_init_database()` - Initialize database schema
   - LOC: ~56
   - Dependencies: Path, schema.sql, logging
   - Returns: None
   - Purpose: Create tables if not exist, load schema from schema.sql
   - **Complexity:** Handles both schema file and fallback creation

4. `_has_legacy_columns()` - Check if database has legacy columns
   - LOC: ~6
   - Dependencies: _get_connection
   - Returns: bool
   - Purpose: Detect if datum_voorstel, ketenpartners columns exist

5. `_has_legacy_columns_in_conn(conn)` - Static version using existing connection
   - LOC: ~5
   - Dependencies: sqlite3.Connection
   - Returns: bool
   - Purpose: Check legacy columns without creating new connection

6. `_build_insert_columns(record, wb_value, include_legacy)` - Compose insert columns/values
   - LOC: ~65
   - Dependencies: DefinitieRecord
   - Returns: tuple[list[str], list[Any]]
   - Purpose: Build column list and values for INSERT statement
   - **Static method** - No instance state

7. `_split_sql_statements(sql)` - Split SQL file into individual statements
   - LOC: ~40
   - Dependencies: None
   - Returns: list[str]
   - Purpose: Parse SQL file for executescript fallback
   - **Utility function** - Could be extracted

---

### Responsibility 2: READ OPERATIONS (Queries, Retrieval) (~350 LOC)

**Methods:**
8. `get_definitie(definitie_id)` - Retrieve single definition by ID
   - LOC: ~18
   - Dependencies: _get_connection, _row_to_record
   - Returns: DefinitieRecord | None
   - Purpose: Simple ID lookup
   - **Tests:** Covered by test_definition_repository.py

9. `find_definitie(begrip, org_context, jur_context, status, categorie, wettelijke_basis)` - Find definition by context
   - LOC: ~107
   - Dependencies: _get_connection, _row_to_record, json
   - Returns: DefinitieRecord | None
   - Purpose: Context-aware lookup with synonym fallback
   - **Complexity:** Two-stage query (exact + synonym), wettelijke_basis normalization
   - **Business logic:** Synonym matching, context matching rules

10. `search_definities(query, categorie, org_context, status, limit)` - Search with filters
    - LOC: ~58
    - Dependencies: _get_connection, _row_to_record
    - Returns: list[DefinitieRecord]
    - Purpose: Flexible search with LIKE queries
    - **Security:** Validates limit parameter

11. `get_statistics()` - Retrieve database statistics
    - LOC: ~37
    - Dependencies: _get_connection
    - Returns: dict[str, Any]
    - Purpose: Aggregated counts by status, category, avg validation score
    - **Read-only** - No side effects

12. `_row_to_record(row)` - Convert database row to DefinitieRecord
    - LOC: ~55
    - Dependencies: sqlite3.Row, datetime, DefinitieRecord
    - Returns: DefinitieRecord
    - Purpose: Map SQLite row to dataclass with datetime parsing
    - **Cross-cutting:** Used by all READ operations

---

### Responsibility 3: WRITE OPERATIONS (Insert, Update, Delete) (~400 LOC)

**Methods:**
13. `create_definitie(record, allow_duplicate)` - Create new definition
    - LOC: ~67
    - Dependencies: _get_connection, find_duplicates, _build_insert_columns, _log_geschiedenis
    - Returns: int (new ID)
    - Purpose: Insert new definition with duplicate check
    - **Business logic:** Duplicate gate (unless allow_duplicate=True)
    - **Side effects:** Logs history, sets timestamps
    - **Tests:** 51 tests cover this path

14. `update_definitie(definitie_id, updates, updated_by)` - Update existing definition
    - LOC: ~101
    - Dependencies: _get_connection, get_definitie, _log_geschiedenis
    - Returns: bool
    - Purpose: Update definition fields with whitelist validation
    - **Security:** Field whitelist prevents SQL injection
    - **Business logic:** Optimistic locking with version_number
    - **Side effects:** Increments version, logs history

15. `change_status(definitie_id, new_status, changed_by, notes)` - Change definition status
    - LOC: ~41
    - Dependencies: update_definitie, _log_geschiedenis
    - Returns: bool
    - Purpose: Status transition with approval metadata
    - **Business logic:** Sets approved_by/approved_at when status=ESTABLISHED
    - **Workflow:** Part of approval process

16. `_log_geschiedenis(definitie_id, wijziging_type, gewijzigd_door, reden)` - Log change history
    - LOC: ~23
    - Dependencies: _get_connection
    - Returns: None
    - Purpose: Audit trail for all changes
    - **Cross-cutting:** Called by create, update, change_status

---

### Responsibility 4: DUPLICATE DETECTION (Business Logic) (~250 LOC)

**Methods:**
17. `find_duplicates(begrip, org_context, jur_context, categorie, wettelijke_basis)` - Find potential duplicates
    - LOC: ~113
    - Dependencies: _get_connection, _row_to_record, _calculate_similarity, json
    - Returns: list[DuplicateMatch]
    - Purpose: Multi-stage duplicate detection (exact + synonym + fuzzy)
    - **Business logic:** Three matching strategies:
      1. Exact match: begrip + context
      2. Synonym match: via definitie_voorbeelden join
      3. Fuzzy match: LIKE query + similarity threshold (70%)
    - **Complexity:** HIGH - Normalized wettelijke_basis comparison, multiple queries
    - **Tests:** Critical for duplicate prevention

18. `count_exact_by_context(begrip, org_context, jur_context, wettelijke_basis)` - Count exact matches
    - LOC: ~30
    - Dependencies: _get_connection, json
    - Returns: int
    - Purpose: Fast count for validation rules (CON-01)
    - **Business logic:** Same normalization as find_duplicates
    - **Use case:** Pre-insert duplicate check

19. `_calculate_similarity(str1, str2)` - Calculate similarity score
    - LOC: ~17
    - Dependencies: None
    - Returns: float
    - Purpose: Jaccard similarity for fuzzy matching
    - **Algorithm:** Set intersection / union of words
    - **Utility function** - Could be extracted to utils

---

### Responsibility 5: BULK OPERATIONS (Import/Export) (~180 LOC)

**Methods:**
20. `export_to_json(file_path, filters)` - Export definitions to JSON
    - LOC: ~49
    - Dependencies: search_definities, json, datetime, Path, _log_import_export
    - Returns: int (count exported)
    - Purpose: Export filtered definitions with metadata
    - **Format:** Includes export_info (timestamp, count, filters)
    - **Side effects:** Writes file, logs export operation

21. `import_from_json(file_path, import_by)` - Import definitions from JSON
    - LOC: ~56
    - Dependencies: json, DefinitieRecord, create_definitie, _log_import_export
    - Returns: tuple[int, int, list[str]] (successful, failed, errors)
    - Purpose: Bulk import with error collection
    - **Business logic:** Sets source_type=IMPORTED, clears ID/timestamps
    - **Error handling:** Per-record try/except, collects errors
    - **Side effects:** Logs import operation

22. `_log_import_export(operatie_type, bestand_pad, verwerkt, succesvol, gefaald)` - Log import/export
    - LOC: ~20
    - Dependencies: _get_connection, datetime
    - Returns: None
    - Purpose: Audit trail for bulk operations
    - **Cross-cutting:** Called by export_to_json, import_from_json

---

### Responsibility 6: VOORBEELDEN MANAGEMENT (~550 LOC)

**Methods:**
23. `save_voorbeelden(definitie_id, voorbeelden_dict, generation_model, generation_params, gegenereerd_door, voorkeursterm)` - Save examples
    - LOC: ~210
    - Dependencies: _get_connection, VoorbeeldenRecord, json, logging
    - Returns: list[int] (saved IDs)
    - Purpose: Upsert examples by type (sentence, practical, counter, synonyms, antonyms)
    - **Business logic:**
      - Deactivates old examples (soft delete)
      - Normalizes voorbeeld_type (voorbeeldzinnen → sentence)
      - Handles voorkeursterm (single source: definities.voorkeursterm)
      - Upsert logic (update existing or insert new)
    - **Complexity:** HIGH - Transaction, type normalization, voorkeursterm logic
    - **Safety guard:** Skips if no new examples provided (prevents accidental wipe)

24. `get_voorbeelden(definitie_id, voorbeeld_type, actief_only)` - Retrieve examples
    - LOC: ~72
    - Dependencies: _get_connection, VoorbeeldenRecord, datetime
    - Returns: list[VoorbeeldenRecord]
    - Purpose: Query examples with filters
    - **Flexibility:** Filter by type, active status

25. `get_voorbeelden_by_type(definitie_id)` - Get examples grouped by type
    - LOC: ~18
    - Dependencies: get_voorbeelden
    - Returns: dict[str, list[str]]
    - Purpose: Convenience method for UI display
    - **Format:** {"sentence": [...], "practical": [...], ...}

26. `get_voorkeursterm(definitie_id)` - Get preferred term
    - LOC: ~18
    - Dependencies: _get_connection
    - Returns: str | None
    - Purpose: Retrieve single source voorkeursterm from definities table
    - **Business rule:** Single source of truth in definities.voorkeursterm column

27. `beoordeel_voorbeeld(voorbeeld_id, beoordeeling, beoordeeling_notities, beoordeeld_door)` - Rate example
    - LOC: ~48
    - Dependencies: _get_connection, logging
    - Returns: bool
    - Purpose: Expert review of examples
    - **Validation:** beoordeeling must be 'goed', 'matig', 'slecht'
    - **Workflow:** Part of quality assurance process

28. `delete_voorbeelden(definitie_id, voorbeeld_type)` - Delete examples
    - LOC: ~36
    - Dependencies: _get_connection, logging
    - Returns: int (deleted count)
    - Purpose: Hard delete examples (vs soft delete in save_voorbeelden)

---

### Responsibility 7: UTILITY FUNCTIONS & HELPERS (~80 LOC)

**Methods:**
29. `get_definitie_repository(db_path)` - Factory function (module-level)
    - LOC: ~8
    - Dependencies: Path, DefinitieRepository
    - Returns: DefinitieRepository
    - Purpose: Convenience factory with default path

**Dataclass Helper Methods:**

30-33. **DefinitieRecord helper methods:**
    - `to_dict()` - Convert to dict with datetime ISO strings (13 LOC)
    - `get_validation_issues_list()` - Parse JSON validation issues (9 LOC)
    - `set_validation_issues(issues)` - Store validation issues as JSON (4 LOC)
    - `get_wettelijke_basis_list()` - Parse JSON wettelijke basis (8 LOC)
    - `set_wettelijke_basis(basis)` - Store wettelijke basis as JSON with normalization (9 LOC)
    - `get_export_destinations_list()` - Parse JSON export destinations (9 LOC)
    - `add_export_destination(destination)` - Add export destination (9 LOC)
    - `get_ketenpartners_list()` - Parse JSON ketenpartners (8 LOC)
    - `set_ketenpartners(partners)` - Store ketenpartners as JSON (3 LOC)

34-36. **VoorbeeldenRecord helper methods:**
    - `to_dict()` - Convert to dict with datetime ISO strings (9 LOC)
    - `get_generation_parameters_dict()` - Parse JSON generation params (8 LOC)
    - `set_generation_parameters(params)` - Store generation params as JSON (4 LOC)

---

## Responsibility Grouping Analysis

### Primary Responsibilities (Proposed Service Boundaries)

#### **1. READ Service (~400 LOC)**
**Purpose:** All SELECT queries, data retrieval, search

**Methods:**
- `get_definitie(id)` - Single record lookup
- `find_definitie(...)` - Context-aware search with synonym fallback
- `search_definities(...)` - Multi-filter search
- `get_statistics()` - Aggregated queries
- `_row_to_record(row)` - Row mapping (shared utility)

**Dependencies:**
- Database connection (inject)
- Logger (inject)
- datetime parsing
- JSON parsing (for wettelijke_basis)

**Complexity:** MEDIUM
- Synonym matching logic
- Wettelijke_basis normalization
- Multiple query strategies

**Tests:** ~20 tests in test_definition_repository.py

---

#### **2. WRITE Service (~450 LOC)**
**Purpose:** All INSERT/UPDATE/DELETE operations, status changes

**Methods:**
- `create_definitie(record)` - INSERT with duplicate check
- `update_definitie(id, updates)` - UPDATE with optimistic locking
- `change_status(id, status)` - Status transition with approval
- `_log_geschiedenis(...)` - Audit logging (shared utility)

**Dependencies:**
- Database connection (inject)
- Logger (inject)
- DuplicateDetectionService (for create_definitie duplicate check)
- datetime for timestamps

**Business Logic:**
- Duplicate gate on insert
- Field whitelist validation
- Optimistic locking with version_number
- Approval workflow (ESTABLISHED status)

**Complexity:** MEDIUM-HIGH
- Transaction management
- Optimistic locking
- Duplicate prevention

**Tests:** ~15 tests in test_definitie_repository_insert_payload.py, test_definition_repository_error_handling.py

---

#### **3. DUPLICATE Detection Service (~250 LOC)**
**Purpose:** All duplicate detection and matching logic

**Methods:**
- `find_duplicates(...)` - Multi-stage matching
- `count_exact_by_context(...)` - Fast exact count
- `_calculate_similarity(str1, str2)` - Similarity algorithm

**Business Logic:**
- **Stage 1:** Exact match (begrip + context)
- **Stage 2:** Synonym match (via voorbeelden join)
- **Stage 3:** Fuzzy match (LIKE + similarity threshold)
- Wettelijke_basis normalization (sorted, unique, stripped)

**Dependencies:**
- Database connection (inject)
- Logger (inject)
- JSON for wettelijke_basis comparison
- Similarity algorithm (Jaccard)

**Complexity:** HIGH
- Three matching strategies
- Complex JOIN queries
- Normalization logic
- Threshold tuning (70%)

**Tests:** ~8 tests in test_duplicate_check_*.py

---

#### **4. BULK Operations Service (~180 LOC)**
**Purpose:** Import/Export functionality

**Methods:**
- `export_to_json(file_path, filters)` - JSON export
- `import_from_json(file_path, import_by)` - JSON import
- `_log_import_export(...)` - Bulk operation logging

**Dependencies:**
- Database connection (inject)
- Logger (inject)
- File I/O (Path, json)
- ReadService (for export filtering)
- WriteService (for import inserts)

**Complexity:** MEDIUM
- File I/O error handling
- Batch processing
- Per-record error collection

**Tests:** ~5 tests in test_import_export_beheer_tab.py

---

#### **5. VOORBEELDEN (Examples) Service (~550 LOC)**
**Purpose:** All example/synonym management

**Methods:**
- `save_voorbeelden(...)` - Upsert examples with type normalization
- `get_voorbeelden(...)` - Retrieve examples
- `get_voorbeelden_by_type(...)` - Grouped retrieval
- `get_voorkeursterm(...)` - Get preferred term
- `beoordeel_voorbeeld(...)` - Rate example
- `delete_voorbeelden(...)` - Delete examples

**Business Logic:**
- Type normalization (voorbeeldzinnen → sentence)
- Soft delete (actief flag) vs hard delete
- Voorkeursterm single source (definities.voorkeursterm)
- Upsert logic (update existing or insert)

**Dependencies:**
- Database connection (inject)
- Logger (inject)
- JSON for generation_parameters
- VoorbeeldenRecord dataclass

**Complexity:** MEDIUM-HIGH
- Transaction management
- Type normalization mapping
- Upsert logic
- Voorkeursterm persistence

**Tests:** ~8 tests in voorbeelden_functionality_tests.py, test_voorkeursterm_text_source.py

---

#### **6. CONNECTION & SCHEMA Service (~150 LOC)**
**Purpose:** Database initialization, connection management, schema

**Methods:**
- `__init__(db_path)` - Repository initialization
- `_get_connection(timeout)` - Connection factory
- `_init_database()` - Schema initialization
- `_has_legacy_columns()` - Schema introspection
- `_has_legacy_columns_in_conn(conn)` - Static introspection
- `_build_insert_columns(...)` - INSERT builder
- `_split_sql_statements(sql)` - SQL parser

**Purpose:** Infrastructure, not business logic

**Dependencies:**
- sqlite3
- schema.sql file
- Path, logging

**Complexity:** LOW-MEDIUM
- Schema loading
- Legacy column detection
- Pragma configuration

**Tests:** Indirect (via all other tests)

---

## Cross-Cutting Concerns

### Logging
**Pattern:** `logger.info()`, `logger.warning()`, `logger.error()`, `logger.debug()`

**Used in:**
- ALL create/update/delete operations
- Import/export operations
- Error handling
- Database initialization
- Voorbeelden operations

**Recommendation:** Inject logger via constructor

---

### Error Handling
**Pattern:** `try/except` with specific exceptions

**Used in:**
- Database operations (sqlite3.Error)
- JSON parsing (json.JSONDecodeError)
- File I/O (Exception)
- Import operations (per-record error collection)

**Recommendation:** Consistent error handling strategy across all services

---

### Transaction Management
**Pattern:** `with self._get_connection() as conn:` (context manager)

**Used in:**
- ALL database operations
- Autocommit mode (`isolation_level=None`) for most operations
- Explicit `conn.commit()` in complex operations (save_voorbeelden)

**Recommendation:** Connection injection + transaction decorator for multi-step operations

---

### JSON Serialization
**Pattern:** `json.dumps(data, ensure_ascii=False)`, `json.loads(data)`

**Used in:**
- wettelijke_basis (normalized, sorted)
- validation_issues
- export_destinations
- ketenpartners
- generation_parameters

**Recommendation:** Utility module or dataclass property methods

---

### Datetime Handling
**Pattern:** `datetime.now(UTC)`, `datetime.fromisoformat()`

**Used in:**
- created_at, updated_at timestamps
- approved_at, validation_date
- Export metadata
- Row to record conversion

**Recommendation:** Utility module for consistent datetime operations

---

## Dependencies

### Direct Imports
- **Standard Library:**
  - `json` - JSON encoding/decoding (metadata, wettelijke_basis, voorbeelden)
  - `logging` - Logging throughout
  - `sqlite3` - Database interface
  - `dataclasses` - DefinitieRecord, VoorbeeldenRecord, DuplicateMatch
  - `datetime` - Timestamps, UTC handling
  - `enum` - DefinitieStatus, SourceType
  - `pathlib.Path` - File path manipulation
  - `typing.Any` - Type hints

- **Domain Models:**
  - `domain.ontological_categories.OntologischeCategorie` - Category enum

### This File Is Imported By (20+ files)

**UI Components (13 files):**
- `src/ui/tabbed_interface.py` - Main interface (imports factory)
- `src/ui/components/tabs/import_export_beheer/*.py` - Import/Export tab (6 files)
- `src/ui/components/definition_edit_tab.py` - Edit tab
- `src/ui/components/orchestration_tab.py` - Orchestration tab
- `src/ui/components/expert_review_tab.py` - Review tab
- `src/ui/components/web_lookup_tab.py` - Lookup tab
- `src/ui/components/definition_generator_tab.py` - Generator tab
- `src/ui/components/monitoring_tab.py` - Monitoring tab
- `src/ui/helpers/examples.py` - Example helpers
- `src/ui/services/definition_ui_service.py` - UI service layer

**Tools (3 files):**
- `src/tools/setup_database.py` - Database setup scripts
- `src/tools/definitie_manager.py` - CLI manager
- `src/integration/definitie_checker.py` - Integration tool

**Tests (20+ files):**
- `tests/services/test_definition_repository.py` - **46 tests** ✅
- `tests/unit/test_definitie_repository_insert_payload.py` - **2 tests** ✅
- `tests/unit/test_definition_repository_error_handling.py` - **3 tests** ✅
- `tests/unit/voorbeelden_functionality_tests.py` - Voorbeelden tests
- `tests/integration/test_duplicate_check_*.py` - Duplicate detection tests (3 files)
- `tests/integration/test_voorkeursterm_text_source.py` - Voorkeursterm tests
- `tests/integration/test_import_export_beheer_tab.py` - Import/Export tests
- `tests/services/test_export_service.py` - Export service tests
- `tests/services/test_data_aggregation_service.py` - Aggregation tests
- Plus 10+ other test files

**Test Coverage:** **EXCELLENT** (51 tests directly, 20+ test files)

---

## Data Flow

### Input Paths

**1. Direct API Calls:**
- UI components call repository methods directly
- Tools (CLI) call repository methods
- Service layer wraps some repository methods

**2. Import Operations:**
- JSON file → `import_from_json()` → `create_definitie()` → database

**3. User Actions (via UI):**
- Generate definition → `create_definitie()`
- Edit definition → `update_definitie()`
- Approve definition → `change_status()`
- Add examples → `save_voorbeelden()`

### Output Paths

**1. Query Results:**
- `get_definitie()` → DefinitieRecord → UI display
- `search_definities()` → list[DefinitieRecord] → UI table
- `find_duplicates()` → list[DuplicateMatch] → duplicate warning

**2. Export Operations:**
- `export_to_json()` → JSON file → external systems

**3. Statistics:**
- `get_statistics()` → dict → monitoring dashboard

### State Changes

**Database State:**
- `create_definitie()` → INSERT into definities + definitie_geschiedenis
- `update_definitie()` → UPDATE definities + version increment + geschiedenis
- `change_status()` → UPDATE definities.status + approval metadata
- `save_voorbeelden()` → UPSERT definitie_voorbeelden (soft delete old + insert new)

**No In-Memory State:**
- Repository is stateless (except db_path)
- No caching
- No session management
- Each method call is independent

---

## Circular Dependency Analysis

### Current Structure
```
DefinitieRepository (self-contained)
    ↓ imports
domain.ontological_categories.OntologischeCategorie
```

**No circular dependencies within this file.**

### Potential Risks When Splitting

**Risk 1: ReadService ← WriteService (create_definitie duplicate check)**
- `create_definitie()` calls `find_duplicates()` (read operation)
- **Mitigation:** DuplicateService as separate dependency

**Risk 2: BulkService → ReadService + WriteService**
- `export_to_json()` calls `search_definities()` (read)
- `import_from_json()` calls `create_definitie()` (write)
- **Mitigation:** Inject both services, no circular dependency

**Risk 3: VoorbeeldenService → WriteService (voorkeursterm update)**
- `save_voorbeelden()` updates `definities.voorkeursterm` (write operation)
- **Mitigation:** Extract voorkeursterm update to WriteService, VoorbeeldenService calls it

**No circular dependencies expected if proper dependency injection is used.**

---

## Recommendations for Service Boundaries

### Proposed Structure

```
src/database/definitie_repository/
├── __init__.py                     # Facade pattern (backwards compatible)
├── connection_service.py           # ~150 LOC - Database connection & schema
├── read_service.py                 # ~400 LOC - All queries (get, find, search)
├── write_service.py                # ~450 LOC - Insert, update, delete, status
├── duplicate_detection_service.py  # ~250 LOC - Duplicate matching logic
├── bulk_operations_service.py      # ~180 LOC - Import/Export
├── voorbeelden_service.py          # ~550 LOC - Examples management
├── models.py                       # ~200 LOC - Move dataclasses here
└── utils.py                        # ~100 LOC - Shared utilities (similarity, JSON)
```

**Total:** ~2,280 LOC (includes dataclasses, currently external)

---

### Service Boundary Definitions

#### **1. ConnectionService**
**Responsibility:** Database connection lifecycle, schema initialization

**Public API:**
- `get_connection(timeout=30.0) -> sqlite3.Connection`
- `init_database() -> None`
- `has_legacy_columns() -> bool`

**Injected Into:** All other services

**Complexity:** LOW

---

#### **2. ReadService**
**Responsibility:** All SELECT queries, no side effects

**Public API:**
- `get_by_id(definitie_id: int) -> DefinitieRecord | None`
- `find_by_context(...) -> DefinitieRecord | None`
- `search(query, filters) -> list[DefinitieRecord]`
- `get_statistics() -> dict[str, Any]`

**Dependencies:**
- ConnectionService (injected)
- Logger (injected)

**Complexity:** MEDIUM

---

#### **3. WriteService**
**Responsibility:** All INSERT/UPDATE/DELETE, status management

**Public API:**
- `create(record: DefinitieRecord, allow_duplicate=False) -> int`
- `update(definitie_id: int, updates: dict) -> bool`
- `change_status(definitie_id: int, new_status: DefinitieStatus) -> bool`
- `update_voorkeursterm(definitie_id: int, voorkeursterm: str | None) -> bool`

**Dependencies:**
- ConnectionService (injected)
- DuplicateDetectionService (injected, for create duplicate check)
- Logger (injected)

**Complexity:** MEDIUM-HIGH

---

#### **4. DuplicateDetectionService**
**Responsibility:** Duplicate matching logic, similarity calculation

**Public API:**
- `find_duplicates(begrip, context, ...) -> list[DuplicateMatch]`
- `count_exact(begrip, context, ...) -> int`
- `calculate_similarity(str1, str2) -> float`

**Dependencies:**
- ConnectionService (injected)
- Logger (injected)

**Complexity:** HIGH

---

#### **5. BulkOperationsService**
**Responsibility:** Import/Export operations

**Public API:**
- `export_to_json(file_path, filters) -> int`
- `import_from_json(file_path, import_by) -> tuple[int, int, list[str]]`

**Dependencies:**
- ConnectionService (injected)
- ReadService (injected, for export filtering)
- WriteService (injected, for import inserts)
- Logger (injected)

**Complexity:** MEDIUM

---

#### **6. VoorbeeldenService**
**Responsibility:** Examples (voorbeelden) management

**Public API:**
- `save(definitie_id, voorbeelden_dict, ...) -> list[int]`
- `get(definitie_id, type, actief_only) -> list[VoorbeeldenRecord]`
- `get_by_type(definitie_id) -> dict[str, list[str]]`
- `get_voorkeursterm(definitie_id) -> str | None`
- `beoordeel(voorbeeld_id, beoordeeling, ...) -> bool`
- `delete(definitie_id, type) -> int`

**Dependencies:**
- ConnectionService (injected)
- WriteService (injected, for voorkeursterm update)
- Logger (injected)

**Complexity:** MEDIUM-HIGH

---

### Shared Dependencies

**Models Module:**
- `DefinitieRecord` (dataclass)
- `VoorbeeldenRecord` (dataclass)
- `DuplicateMatch` (dataclass)
- `DefinitieStatus` (enum)
- `SourceType` (enum)

**Utils Module:**
- `calculate_similarity(str1, str2) -> float` (Jaccard)
- `normalize_wettelijke_basis(basis: list[str]) -> str` (JSON normalization)
- `parse_datetime(dt_str: str) -> datetime | None`
- `format_datetime(dt: datetime) -> str`

---

### Facade Pattern (Backwards Compatibility)

**`__init__.py` exports:**
```python
# Backwards compatibility facade
from .models import DefinitieRecord, VoorbeeldenRecord, DuplicateMatch, DefinitieStatus, SourceType
from .read_service import ReadService
from .write_service import WriteService
from .duplicate_detection_service import DuplicateDetectionService
from .bulk_operations_service import BulkOperationsService
from .voorbeelden_service import VoorbeeldenService
from .connection_service import ConnectionService

class DefinitieRepository:
    """Facade maintaining backwards compatibility."""
    def __init__(self, db_path="data/definities.db"):
        self.connection_service = ConnectionService(db_path)
        self.read_service = ReadService(self.connection_service)
        self.duplicate_service = DuplicateDetectionService(self.connection_service)
        self.write_service = WriteService(self.connection_service, self.duplicate_service)
        self.bulk_service = BulkOperationsService(self.connection_service, self.read_service, self.write_service)
        self.voorbeelden_service = VoorbeeldenService(self.connection_service, self.write_service)

    # Delegate all methods to respective services
    def get_definitie(self, definitie_id): return self.read_service.get_by_id(definitie_id)
    def create_definitie(self, record, allow_duplicate=False): return self.write_service.create(record, allow_duplicate)
    # ... etc
```

**Migration Strategy:**
1. Create new service modules
2. Implement facade in `__init__.py`
3. All existing imports continue to work
4. Gradually migrate callers to use services directly
5. Remove facade when usage = 0

---

## Migration Complexity Assessment

### Complexity Rating: **MEDIUM**

**Factors Supporting Low Complexity:**
- ✅ Clear responsibility boundaries
- ✅ Excellent test coverage (51 tests)
- ✅ No circular dependencies in current file
- ✅ Stateless design (no in-memory state)
- ✅ Well-defined interfaces (method signatures)

**Factors Increasing Complexity:**
- ⚠️ 41 methods to split
- ⚠️ 20+ files import this module
- ⚠️ Complex duplicate detection logic (3 matching strategies)
- ⚠️ Transaction management in save_voorbeelden
- ⚠️ Voorkeursterm persistence (cross-service coordination)

**Risk Areas:**
1. **Duplicate detection** - Complex business logic, must preserve exact behavior
2. **save_voorbeelden** - Transaction with voorkeursterm update (cross-service)
3. **create_definitie** - Calls find_duplicates (cross-service)
4. **Import callers** - 20+ files need gradual migration

**Mitigation:**
- Use facade pattern for backwards compatibility
- Extract services incrementally (one at a time)
- Run tests after EACH extraction
- Keep original file until 100% migrated

---

## Test Coverage Analysis

### Direct Tests (51 tests)

**test_definition_repository.py:** 46 tests
- CRUD operations
- Duplicate detection
- Search functionality
- Status changes
- Voorbeelden operations

**test_definitie_repository_insert_payload.py:** 2 tests
- INSERT payload validation
- Legacy column handling

**test_definition_repository_error_handling.py:** 3 tests
- Error scenarios
- Exception handling

### Indirect Tests (20+ test files)

**Integration Tests:**
- `test_duplicate_check_three_contexts.py` - Duplicate detection
- `test_duplicate_check_synonyms.py` - Synonym matching
- `test_voorkeursterm_text_source.py` - Voorkeursterm persistence
- `test_import_export_beheer_tab.py` - Import/Export workflow

**Functionality Tests:**
- `voorbeelden_functionality_tests.py` - Examples management

**Service Tests:**
- `test_export_service.py` - Export operations
- `test_data_aggregation_service.py` - Aggregation queries

### Coverage Quality: **EXCELLENT**

**Strengths:**
- All major operations covered
- Edge cases tested (duplicate detection, error handling)
- Integration tests for complex workflows
- Good separation of unit vs integration tests

**Gaps:**
- Fuzzy matching threshold (70%) not explicitly tested
- SQL injection tests (field whitelist validation)
- Legacy column migration edge cases

---

## Recommendations

### 1. Extraction Order (Lowest Risk First)

**Phase 2a: Extract ReadService (Day 1-2)**
- **Why first:** No side effects, stateless, well-tested
- **Risk:** LOW
- **Tests:** 20+ tests cover read operations

**Phase 2b: Extract DuplicateDetectionService (Day 2-3)**
- **Why second:** Independent logic, clear interface
- **Risk:** MEDIUM (complex logic)
- **Tests:** 8+ tests cover duplicate detection

**Phase 2c: Extract WriteService (Day 3-4)**
- **Why third:** Depends on DuplicateService, core operations
- **Risk:** MEDIUM-HIGH (duplicate check dependency)
- **Tests:** 15+ tests cover write operations

**Phase 2d: Extract VoorbeeldenService (Day 4-5)**
- **Why fourth:** Depends on WriteService (voorkeursterm)
- **Risk:** MEDIUM-HIGH (transaction logic)
- **Tests:** 8+ tests cover voorbeelden

**Phase 2e: Extract BulkOperationsService (Day 5-6)**
- **Why last:** Depends on Read + Write services
- **Risk:** MEDIUM
- **Tests:** 5+ tests cover import/export

**Phase 2f: Extract ConnectionService + Utils (Day 6)**
- **Why last:** Shared infrastructure, all other services depend on it
- **Risk:** LOW (refactor only)

---

### 2. Shared Dependencies Strategy

**ConnectionService:**
- Extract first as separate module
- Inject into all other services
- No circular dependencies

**Logger:**
- Inject via constructor in all services
- Use `logging.getLogger(__name__)` in each module

**Utils Module:**
- `calculate_similarity()` - Pure function, easy extract
- `normalize_wettelijke_basis()` - Pure function
- Datetime helpers - Pure functions

---

### 3. Testing Strategy

**For Each Service Extraction:**
1. Create new service module
2. Move methods from DefinitieRepository
3. Update facade to delegate to new service
4. Run ALL 51 tests - must pass
5. Run integration tests - must pass
6. Commit checkpoint (rollback point)

**Acceptance Criteria:**
- ✅ All 51 tests pass
- ✅ All integration tests pass
- ✅ No new warnings/errors
- ✅ Coverage >= baseline

---

### 4. Rollback Strategy

**Checkpoints:**
- After each service extraction (6 checkpoints)
- Git commit with message: "Extract [ServiceName] - tests passing"

**Rollback Trigger:**
- Tests fail after extraction
- Import errors in production code
- Performance degradation

**Rollback Command:**
```bash
git revert HEAD  # Undo last extraction
pytest -q       # Verify tests pass
```

---

## Next Steps (Day 2)

**Tomorrow's Tasks:**
1. Map `definition_generator_tab.py` (2339 LOC, 46 methods)
2. Map `tabbed_interface.py` (1733 LOC, 38 methods)
3. Create responsibility maps for both files

**Deliverables:**
- `definition_generator_tab_responsibility_map.md`
- `tabbed_interface_responsibility_map.md`

**Checkpoint 1 (End of Day 2):**
- Are all 3 responsibility maps complete?
- Are boundaries clear for all files?
- **GO/NO-GO decision:** Proceed to Day 3 or need more analysis?

---

## Conclusion

**definitie_repository.py** is a well-structured God Object with clear internal boundaries and excellent test coverage. The file exhibits classic God Object symptoms (1815 LOC, 41 methods, multiple responsibilities), but the code quality is high and responsibilities are identifiable.

**Key Findings:**
- ✅ **Clear boundaries:** READ/WRITE/DUPLICATE/BULK/VOORBEELDEN responsibilities are distinct
- ✅ **Good tests:** 51 tests provide excellent safety net
- ✅ **No circular deps:** File is self-contained
- ⚠️ **Migration complexity:** MEDIUM - 20+ importers, complex duplicate logic
- ⚠️ **Cross-service calls:** create_definitie → find_duplicates, save_voorbeelden → update voorkeursterm

**Migration is FEASIBLE with proper planning and incremental approach.**

**Recommended Strategy:**
1. Extract services incrementally (6 phases)
2. Use facade pattern for backwards compatibility
3. Test after EACH extraction
4. Migrate callers gradually (20+ files)
5. Remove facade when usage = 0

**Timeline Estimate:** 2-3 days (as per EPIC-026 plan)

---

**Status:** ✅ COMPLETE
**Date:** 2025-10-02
**Agent:** Code Architect
**Next:** Map definition_generator_tab.py (Day 2)
