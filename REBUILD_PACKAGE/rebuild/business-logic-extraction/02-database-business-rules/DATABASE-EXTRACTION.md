# Database Business Rules Extraction

## Executive Summary

This document extracts all business logic, constraints, and validation rules embedded in the database layer of the DefinitieAgent application. The database uses SQLite with a comprehensive schema supporting audit trails, versioning, validation tracking, and multi-context definition management.

**Key Findings:**
- 8 core tables with complex relationships
- 30+ business rule constraints enforced at schema level
- Automatic audit logging via triggers
- Multi-level status workflow (imported → draft → review → established → archived)
- UTF-8 encoding for Dutch legal text
- JSON storage for flexible metadata (wettelijke_basis, ketenpartners, validation_issues)
- Ontological categorization (7 categories + UFO metamodel support)
- Duplicate prevention with sophisticated matching logic

---

## Schema Overview

### Tables and Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                         CORE TABLES                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐                                            │
│  │   definities    │◄───────────────┐                           │
│  │  (main table)   │                │                           │
│  └────────┬────────┘                │                           │
│           │                         │                           │
│           │ 1:N                     │ FK                        │
│           ├─────────────┐           │                           │
│           │             │           │                           │
│           ▼             ▼           │                           │
│  ┌──────────────┐  ┌──────────────┐│                           │
│  │  definitie_  │  │ definitie_   ││                           │
│  │ geschiedenis │  │ voorbeelden  ││                           │
│  │ (audit log)  │  │  (examples)  ││                           │
│  └──────────────┘  └──────────────┘│                           │
│           │                         │                           │
│           │ 1:N                     │                           │
│           ▼                         │                           │
│  ┌──────────────┐                   │                           │
│  │ definitie_   │                   │                           │
│  │    tags      │                   │                           │
│  └──────────────┘                   │                           │
│                                     │                           │
│  Self-reference (versioning): ─────┘                           │
│  previous_version_id → definities.id                            │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                      SUPPORTING TABLES                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐    ┌─────────────────────┐               │
│  │ externe_bronnen  │    │ import_export_logs  │               │
│  │  (API configs)   │    │   (operations log)  │               │
│  └──────────────────┘    └─────────────────────┘               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### ER Diagram (Textual)

```
DEFINITIES (1) ──── (N) DEFINITIE_GESCHIEDENIS
    │
    ├──── (N) DEFINITIE_VOORBEELDEN
    │
    ├──── (N) DEFINITIE_TAGS
    │
    └──── (1) DEFINITIES (self-reference: previous_version_id)

EXTERNE_BRONNEN (standalone configuration)

IMPORT_EXPORT_LOGS (standalone operations log)
```

---

## Business Rules by Table

### 1. `definities` Table

**Primary Purpose:** Core storage for legal definitions with full lifecycle management

#### Table Structure

```sql
CREATE TABLE definities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Core definition fields
    begrip VARCHAR(255) NOT NULL,
    definitie TEXT NOT NULL,
    categorie VARCHAR(50) NOT NULL,
    organisatorische_context TEXT NOT NULL DEFAULT '[]',
    juridische_context TEXT NOT NULL DEFAULT '[]',
    wettelijke_basis TEXT NOT NULL DEFAULT '[]',
    ufo_categorie TEXT,
    toelichting_proces TEXT,
    voorkeursterm TEXT,

    -- Status & versioning
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    version_number INTEGER NOT NULL DEFAULT 1,
    previous_version_id INTEGER REFERENCES definities(id),

    -- Validation
    validation_score DECIMAL(3,2),
    validation_date TIMESTAMP,
    validation_issues TEXT,

    -- Source tracking
    source_type VARCHAR(50) DEFAULT 'generated',
    source_reference VARCHAR(500),
    imported_from VARCHAR(255),

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),

    -- Approval workflow
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    approval_notes TEXT,

    -- Export tracking
    last_exported_at TIMESTAMP,
    export_destinations TEXT,

    -- Legacy fields
    datum_voorstel DATE,
    ketenpartners TEXT,
    voorkeursterm_is_begrip BOOLEAN NOT NULL DEFAULT FALSE
);
```

#### Business Rules & Constraints

##### BR-DB-001: Category Constraint
**Rule:** Definition must belong to one of 11 valid categories
**Enforcement:** CHECK constraint
```sql
CHECK (categorie IN (
    -- Legacy categories
    'type', 'proces', 'resultaat', 'exemplaar',
    -- Ontological categories
    'ENT',    -- Entiteit (type/klasse)
    'ACT',    -- Activiteit (proces/handeling)
    'REL',    -- Relatie (verband tussen entiteiten)
    'ATT',    -- Attribuut (eigenschap/kenmerk)
    'AUT',    -- Autorisatie (bevoegdheid/rechten)
    'STA',    -- Status (toestand/fase)
    'OTH'     -- Overig (niet-gecategoriseerd)
))
```
**Business Impact:** Ensures consistent ontological classification

##### BR-DB-002: Status Workflow Constraint
**Rule:** Definition status must follow defined workflow
**Enforcement:** CHECK constraint
```sql
CHECK (status IN ('imported', 'draft', 'review', 'established', 'archived'))
```
**Business Impact:** Enforces lifecycle state machine
**Workflow:**
```
imported → draft → review → established → archived
    ↓                         ↓
    └──────── archived ───────┘
```

##### BR-DB-003: Source Type Validation
**Rule:** Source must be one of three valid types
**Enforcement:** CHECK constraint
```sql
CHECK (source_type IN ('generated', 'imported', 'manual'))
```
**Business Impact:** Tracks origin of definition for auditing

##### BR-DB-004: UFO Metamodel Categories
**Rule:** UFO-categorie (OntoUML/UFO metamodel) must be from predefined set
**Enforcement:** CHECK constraint
```sql
CHECK (ufo_categorie IN (
    'Kind', 'Event', 'Role', 'Phase', 'Relator', 'Mode',
    'Quantity', 'Quality', 'Subkind', 'Category', 'Mixin',
    'RoleMixin', 'PhaseMixin', 'Abstract', 'Relatie',
    'Event Composition'
))
```
**Business Impact:** Supports advanced ontological modeling

##### BR-DB-005: NOT NULL Requirements
**Rule:** Core fields must always have values
**Enforcement:** NOT NULL constraints
- `begrip` - Term being defined (REQUIRED)
- `definitie` - Definition text (REQUIRED)
- `categorie` - Ontological category (REQUIRED)
- `organisatorische_context` - Organizational context (REQUIRED, defaults to '[]')
- `juridische_context` - Legal context (REQUIRED, defaults to '[]')
- `wettelijke_basis` - Legal basis (REQUIRED, defaults to '[]')
- `status` - Lifecycle status (REQUIRED, defaults to 'draft')
- `version_number` - Version counter (REQUIRED, defaults to 1)
- `created_at` - Creation timestamp (REQUIRED, auto-set)
- `updated_at` - Update timestamp (REQUIRED, auto-set)

##### BR-DB-006: JSON Array Storage Format
**Rule:** Multi-value fields stored as JSON arrays in TEXT columns
**Fields:**
- `organisatorische_context` - Organizations involved
- `juridische_context` - Legal contexts
- `wettelijke_basis` - Legal basis references (normalized, sorted)
- `validation_issues` - List of validation problems
- `export_destinations` - Export target locations
- `ketenpartners` - Chain partners

**Normalization Logic (from migrate_database.py):**
```python
def _normalize_list_json(raw: str | None) -> str:
    """
    Normalize JSON list: unique, sorted, stripped
    - Ensures consistent comparison for duplicate detection
    - Handles None, empty, JSON strings, or plain strings
    """
    if not raw:
        return json.dumps([], ensure_ascii=False)
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            items = {str(x).strip() for x in data}
            return json.dumps(sorted(items), ensure_ascii=False)
        return json.dumps([str(data).strip()], ensure_ascii=False)
    except Exception:
        return json.dumps([str(raw).strip()], ensure_ascii=False)
```

**Business Impact:** Enables reliable duplicate detection independent of input order

##### BR-DB-007: Self-Referencing Versioning
**Rule:** Definitions can reference previous versions
**Enforcement:** Foreign key to self
```sql
previous_version_id INTEGER REFERENCES definities(id)
```
**Business Impact:** Maintains version history chain

##### BR-DB-008: Validation Score Range
**Rule:** Validation score is decimal between 0.00 and 1.00
**Enforcement:** DECIMAL(3,2) type
**Business Impact:** Quality metric for definitions

##### BR-DB-009: Voorkeursterm (Preferred Term) Storage
**Rule:** Preferred term stored at definition level (single source of truth)
**Field:** `voorkeursterm TEXT`
**Migration Logic:** Backfills from:
1. Synonyms marked with `is_voorkeursterm = TRUE`
2. Legacy boolean flag `voorkeursterm_is_begrip = TRUE` → uses `begrip` as voorkeursterm

**Business Impact:** Centralized preferred term management, decoupled from synonym storage

##### BR-DB-010: Duplicate Prevention Logic (Repository Layer)
**Rule:** Prevent duplicate definitions with same context
**Implementation:** In `DefinitieRepository.create_definitie()` and `find_duplicates()`

**Matching Criteria:**
1. **Exact begrip match** + same organizational/legal/wettelijke_basis context
2. **Synonym match** (case-insensitive) + same context
3. **Fuzzy match** (70% similarity threshold) + same organization

**Exclusions:**
- Archived definitions excluded from duplicate check
- `allow_duplicate=True` parameter bypasses check

**Business Impact:** Prevents redundant definitions while allowing category-based variations

##### BR-DB-011: Context Normalization
**Rule:** `wettelijke_basis` lists normalized for consistent comparison
**Logic:** Repository methods normalize via sorted, unique, stripped JSON arrays
**Business Impact:** Duplicate detection works regardless of input order

---

### 2. `definitie_geschiedenis` Table

**Primary Purpose:** Audit trail for all definition changes

#### Table Structure

```sql
CREATE TABLE definitie_geschiedenis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER NOT NULL REFERENCES definities(id) ON DELETE CASCADE,

    -- Snapshot of change
    begrip VARCHAR(255) NOT NULL,
    definitie_oude_waarde TEXT,
    definitie_nieuwe_waarde TEXT,

    -- Change metadata
    wijziging_type VARCHAR(50) NOT NULL,
    wijziging_reden TEXT,

    -- User info
    gewijzigd_door VARCHAR(255),
    gewijzigd_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Context snapshot
    context_snapshot TEXT  -- JSON of complete context at moment of change
);
```

#### Business Rules & Constraints

##### BR-DB-020: Cascade Delete
**Rule:** When definition is deleted, all history records are deleted
**Enforcement:** `ON DELETE CASCADE`
**Business Impact:** Maintains referential integrity

##### BR-DB-021: Change Type Validation
**Rule:** Change type must be one of predefined types
**Enforcement:** CHECK constraint
```sql
CHECK (wijziging_type IN (
    'created',
    'updated',
    'status_changed',
    'approved',
    'archived',
    'auto_save'
))
```

##### BR-DB-022: Context Snapshot Format
**Rule:** Context snapshot stored as JSON object
**Structure (from trigger):**
```json
{
    "oude_status": "draft",
    "nieuwe_status": "review",
    "organisatorische_context": ["DJI"],
    "juridische_context": ["strafrecht"],
    "wettelijke_basis": ["Wetboek van Strafrecht"],
    "categorie": "ENT"
}
```

##### BR-DB-023: Automatic History Logging
**Rule:** Every update to definitie triggers history record
**Enforcement:** Trigger `log_definitie_changes`
**Business Impact:** Complete audit trail without manual intervention

---

### 3. `definitie_voorbeelden` Table

**Primary Purpose:** Store generated examples for definitions

#### Table Structure

```sql
CREATE TABLE definitie_voorbeelden (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER NOT NULL REFERENCES definities(id) ON DELETE CASCADE,

    -- Example information
    voorbeeld_type VARCHAR(50) NOT NULL,
    voorbeeld_tekst TEXT NOT NULL,
    voorbeeld_volgorde INTEGER DEFAULT 1,

    -- Generation metadata
    gegenereerd_door VARCHAR(50) DEFAULT 'system',
    generation_model VARCHAR(50),
    generation_parameters TEXT,  -- JSON

    -- Status
    actief BOOLEAN NOT NULL DEFAULT TRUE,
    beoordeeld BOOLEAN NOT NULL DEFAULT FALSE,
    beoordeeling VARCHAR(50),
    beoordeeling_notities TEXT,
    beoordeeld_door VARCHAR(255),
    beoordeeld_op TIMESTAMP,

    -- Timestamps
    aangemaakt_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    bijgewerkt_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(definitie_id, voorbeeld_type, voorbeeld_volgorde)
);
```

#### Business Rules & Constraints

##### BR-DB-030: Example Type Validation
**Rule:** Example type must be one of 6 valid types
**Enforcement:** CHECK constraint
```sql
CHECK (voorbeeld_type IN (
    'sentence',      -- Voorbeeldzinnen
    'practical',     -- Praktijkvoorbeelden
    'counter',       -- Tegenvoorbeelden
    'synonyms',      -- Synoniemen
    'antonyms',      -- Antoniemen
    'explanation'    -- Toelichting
))
```

##### BR-DB-031: Type Normalization (Repository Layer)
**Rule:** Various input forms normalized to canonical types
**Implementation:** `_normalize_type()` function in `save_voorbeelden()`
**Mapping Examples:**
- "voorbeeldzinnen", "zinnen", "sentences" → "sentence"
- "praktijkvoorbeelden", "praktijk" → "practical"
- "tegenvoorbeelden", "tegen", "counterexamples" → "counter"
- "synoniemen", "synonym" → "synonyms"

**Business Impact:** Consistent storage regardless of input variation

##### BR-DB-032: Unique Example Constraint
**Rule:** Each (definitie_id, type, volgorde) combination must be unique
**Enforcement:** UNIQUE constraint
**Business Impact:** Prevents duplicate examples

##### BR-DB-033: Cascade Delete
**Rule:** When definition is deleted, all examples are deleted
**Enforcement:** `ON DELETE CASCADE`

##### BR-DB-034: Assessment Values
**Rule:** Assessment rating must be one of three values
**Enforcement:** Application-level validation in `beoordeel_voorbeeld()`
```python
if beoordeeling not in ["goed", "matig", "slecht"]:
    raise ValueError("Beoordeeling moet 'goed', 'matig' of 'slecht' zijn")
```

##### BR-DB-035: Active Example Replacement
**Rule:** Saving new examples marks old ones inactive
**Implementation:** In `save_voorbeelden()`
```sql
UPDATE definitie_voorbeelden
SET actief = FALSE, bijgewerkt_op = CURRENT_TIMESTAMP
WHERE definitie_id = ? AND actief = TRUE
```
**Business Impact:** Maintains single active set of examples per definition

##### BR-DB-036: Empty Example Prevention
**Rule:** Skip saving empty examples or empty type lists
**Implementation:** Safety guard in `save_voorbeelden()`
```python
if total_new == 0:
    logger.info("No new examples provided — skipping overwrite")
    return []
```
**Business Impact:** Prevents accidental deletion of existing examples

##### BR-DB-037: Synonym-Based Lookup
**Rule:** Definitions can be found via synonym match (case-insensitive)
**Implementation:** In `find_definitie()` and `find_duplicates()`
```sql
SELECT d.*
FROM definities d
JOIN definitie_voorbeelden v ON v.definitie_id = d.id
WHERE LOWER(v.voorbeeld_tekst) = LOWER(?)
  AND v.voorbeeld_type = 'synonyms'
  AND v.actief = TRUE
  AND d.organisatorische_context = ?
  ...
```
**Index Support:** `idx_synonyms_text_ci` (case-insensitive)
**Business Impact:** Flexible term lookup beyond exact begrip match

---

### 4. `definitie_tags` Table

**Primary Purpose:** Flexible tagging system for definitions

#### Table Structure

```sql
CREATE TABLE definitie_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER NOT NULL REFERENCES definities(id) ON DELETE CASCADE,
    tag_naam VARCHAR(100) NOT NULL,
    tag_waarde VARCHAR(255),

    -- Metadata
    toegevoegd_door VARCHAR(255),
    toegevoegd_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(definitie_id, tag_naam)
);
```

#### Business Rules & Constraints

##### BR-DB-040: Unique Tag Names Per Definition
**Rule:** Each definition can have only one value per tag name
**Enforcement:** UNIQUE constraint
**Business Impact:** Prevents duplicate tags

##### BR-DB-041: Cascade Delete
**Rule:** When definition is deleted, all tags are deleted
**Enforcement:** `ON DELETE CASCADE`

---

### 5. `externe_bronnen` Table

**Primary Purpose:** Configuration for external data sources

#### Table Structure

```sql
CREATE TABLE externe_bronnen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Source information
    bron_naam VARCHAR(255) NOT NULL UNIQUE,
    bron_type VARCHAR(50) NOT NULL,
    bron_url VARCHAR(500),

    -- Configuration
    configuratie TEXT,  -- JSON configuration

    -- Credentials (encrypted)
    api_key_encrypted VARCHAR(500),
    gebruikersnaam VARCHAR(255),

    -- Status
    actief BOOLEAN NOT NULL DEFAULT TRUE,
    laatste_sync TIMESTAMP,
    laatste_sync_status VARCHAR(50),

    -- Metadata
    aangemaakt_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    aangemaakt_door VARCHAR(255)
);
```

#### Business Rules & Constraints

##### BR-DB-050: Source Type Validation
**Rule:** External source must be one of 4 valid types
**Enforcement:** CHECK constraint
```sql
CHECK (bron_type IN ('database', 'api', 'file', 'manual'))
```

##### BR-DB-051: Unique Source Names
**Rule:** Each external source must have unique name
**Enforcement:** UNIQUE constraint on `bron_naam`

##### BR-DB-052: Encrypted Credentials
**Rule:** API keys stored in encrypted form
**Field:** `api_key_encrypted VARCHAR(500)`
**Business Impact:** Security best practice for sensitive data

---

### 6. `import_export_logs` Table

**Primary Purpose:** Operations audit trail for import/export

#### Table Structure

```sql
CREATE TABLE import_export_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Operation info
    operatie_type VARCHAR(50) NOT NULL,
    bron_bestemming VARCHAR(255) NOT NULL,

    -- Results
    aantal_verwerkt INTEGER NOT NULL DEFAULT 0,
    aantal_succesvol INTEGER NOT NULL DEFAULT 0,
    aantal_gefaald INTEGER NOT NULL DEFAULT 0,

    -- Details
    bestand_pad VARCHAR(500),
    formaat VARCHAR(50),  -- json, csv, xml, sql
    fouten_details TEXT,  -- JSON array of errors

    -- Metadata
    gestart_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    voltooid_op TIMESTAMP,
    gestart_door VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'running'
);
```

#### Business Rules & Constraints

##### BR-DB-060: Operation Type Validation
**Rule:** Operation must be import or export
**Enforcement:** CHECK constraint
```sql
CHECK (operatie_type IN ('import', 'export'))
```

##### BR-DB-061: Status Validation
**Rule:** Operation status must be one of 4 valid states
**Enforcement:** CHECK constraint
```sql
CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
```

##### BR-DB-062: Success Metrics
**Rule:** Track success/failure counts for each operation
**Fields:**
- `aantal_verwerkt` - Total processed
- `aantal_succesvol` - Successfully processed
- `aantal_gefaald` - Failed records

**Business Impact:** Enables operation success rate reporting

---

## Triggers & Automation

### Trigger 1: `update_definities_timestamp`

**Purpose:** Automatically update `updated_at` timestamp on record modification

**Implementation:**
```sql
CREATE TRIGGER update_definities_timestamp
    AFTER UPDATE ON definities
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE definities SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

**Business Rule:** BR-DB-070: Automatic timestamp tracking
**Trigger:** When definition is updated AND timestamp hasn't been manually changed
**Action:** Set `updated_at` to current timestamp
**Business Impact:** Automatic audit trail without manual intervention

---

### Trigger 2: `log_definitie_changes`

**Purpose:** Automatically log all definition changes to audit trail

**Implementation:**
```sql
CREATE TRIGGER log_definitie_changes
    AFTER UPDATE ON definities
    FOR EACH ROW
BEGIN
    INSERT INTO definitie_geschiedenis (
        definitie_id, begrip,
        definitie_oude_waarde, definitie_nieuwe_waarde,
        wijziging_type, gewijzigd_door, context_snapshot
    ) VALUES (
        NEW.id, NEW.begrip,
        OLD.definitie, NEW.definitie,
        CASE
            WHEN OLD.status != NEW.status THEN 'status_changed'
            WHEN OLD.definitie != NEW.definitie THEN 'updated'
            ELSE 'updated'
        END,
        NEW.updated_by,
        json_object(
            'oude_status', OLD.status,
            'nieuwe_status', NEW.status,
            'organisatorische_context', NEW.organisatorische_context,
            'juridische_context', NEW.juridische_context,
            'wettelijke_basis', NEW.wettelijke_basis
        )
    );
END;
```

**Business Rule:** BR-DB-071: Automatic change logging
**Trigger:** After any update to definitions table
**Action:**
1. Capture old and new definition text
2. Determine change type (status_changed vs. updated)
3. Store complete context snapshot as JSON
4. Record who made the change

**Business Impact:**
- Complete audit trail for compliance
- Change history for all definitions
- Context snapshot enables rollback scenarios

---

### Trigger 3: `update_voorbeelden_timestamp`

**Purpose:** Automatically update `bijgewerkt_op` timestamp on example modification

**Implementation:**
```sql
CREATE TRIGGER update_voorbeelden_timestamp
    AFTER UPDATE ON definitie_voorbeelden
    FOR EACH ROW
    WHEN NEW.bijgewerkt_op = OLD.bijgewerkt_op
BEGIN
    UPDATE definitie_voorbeelden SET bijgewerkt_op = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

**Business Rule:** BR-DB-072: Automatic example timestamp tracking
**Business Impact:** Track when examples were last modified

---

## Data Integrity Rules

### Referential Integrity

#### RI-001: Definition → Previous Version
**Constraint:** `previous_version_id INTEGER REFERENCES definities(id)`
**Type:** Self-referencing foreign key
**Business Rule:** Definition can reference its previous version
**Enforcement:** SQLite foreign key constraint
**Impact:** Enables version chain navigation

#### RI-002: Geschiedenis → Definition
**Constraint:** `definitie_id INTEGER NOT NULL REFERENCES definities(id) ON DELETE CASCADE`
**Business Rule:** History records tied to parent definition
**Enforcement:** Foreign key with CASCADE delete
**Impact:** Orphaned history records automatically cleaned up

#### RI-003: Voorbeelden → Definition
**Constraint:** `definitie_id INTEGER NOT NULL REFERENCES definities(id) ON DELETE CASCADE`
**Business Rule:** Examples tied to parent definition
**Enforcement:** Foreign key with CASCADE delete
**Impact:** Orphaned examples automatically cleaned up

#### RI-004: Tags → Definition
**Constraint:** `definitie_id INTEGER NOT NULL REFERENCES definities(id) ON DELETE CASCADE`
**Business Rule:** Tags tied to parent definition
**Enforcement:** Foreign key with CASCADE delete
**Impact:** Orphaned tags automatically cleaned up

---

### Domain Constraints

#### DC-001: Categorie Domain
**Rule:** Only 11 valid ontological categories
**Values:** type, proces, resultaat, exemplaar, ENT, ACT, REL, ATT, AUT, STA, OTH
**Enforcement:** CHECK constraint
**Business Impact:** Consistent classification scheme

#### DC-002: Status Domain
**Rule:** Only 5 valid lifecycle statuses
**Values:** imported, draft, review, established, archived
**Enforcement:** CHECK constraint
**Business Impact:** Enforces workflow state machine

#### DC-003: Source Type Domain
**Rule:** Only 3 valid source types
**Values:** generated, imported, manual
**Enforcement:** CHECK constraint
**Business Impact:** Tracks definition origin

#### DC-004: UFO Categorie Domain
**Rule:** Only 16 valid UFO metamodel categories
**Values:** Kind, Event, Role, Phase, Relator, Mode, Quantity, Quality, Subkind, Category, Mixin, RoleMixin, PhaseMixin, Abstract, Relatie, Event Composition
**Enforcement:** CHECK constraint (nullable)
**Business Impact:** Advanced ontological modeling support

#### DC-005: Example Type Domain
**Rule:** Only 6 valid example types
**Values:** sentence, practical, counter, synonyms, antonyms, explanation
**Enforcement:** CHECK constraint
**Business Impact:** Structured example categorization

#### DC-006: Bron Type Domain
**Rule:** Only 4 valid external source types
**Values:** database, api, file, manual
**Enforcement:** CHECK constraint
**Business Impact:** Structured source configuration

#### DC-007: Operation Type Domain
**Rule:** Only 2 valid operation types
**Values:** import, export
**Enforcement:** CHECK constraint
**Business Impact:** Clear operation logging

#### DC-008: Operation Status Domain
**Rule:** Only 4 valid operation statuses
**Values:** running, completed, failed, cancelled
**Enforcement:** CHECK constraint
**Business Impact:** Clear operation state tracking

#### DC-009: Assessment Domain
**Rule:** Only 3 valid assessment ratings (application-level)
**Values:** goed, matig, slecht
**Enforcement:** Application validation in `beoordeel_voorbeeld()`
**Business Impact:** Consistent quality ratings

---

### Business Rule Constraints

#### BRC-001: Required Core Fields
**Rule:** Core definition fields cannot be empty
**Enforcement:** NOT NULL constraints
**Fields:** begrip, definitie, categorie, status, version_number, created_at, updated_at
**Business Impact:** Data completeness for critical fields

#### BRC-002: Unique Tag Per Definition
**Rule:** Each definition can have only one value per tag name
**Enforcement:** UNIQUE(definitie_id, tag_naam)
**Business Impact:** Consistent tag structure

#### BRC-003: Unique Example Per Type+Order
**Rule:** Each (definition, type, order) combination must be unique
**Enforcement:** UNIQUE(definitie_id, voorbeeld_type, voorbeeld_volgorde)
**Business Impact:** Structured example ordering

#### BRC-004: Unique External Source Name
**Rule:** External source names must be unique
**Enforcement:** UNIQUE(bron_naam)
**Business Impact:** Clear source identification

#### BRC-005: Validation Score Range
**Rule:** Validation score must be between 0.00 and 1.00
**Enforcement:** DECIMAL(3,2) type constraint
**Business Impact:** Normalized quality metric

#### BRC-006: Default Values
**Rule:** Several fields have business-meaningful defaults
**Defaults:**
- `organisatorische_context` → '[]'
- `juridische_context` → '[]'
- `wettelijke_basis` → '[]'
- `status` → 'draft'
- `version_number` → 1
- `source_type` → 'generated'
- `actief` (voorbeelden) → TRUE
- `beoordeeld` (voorbeelden) → FALSE
- `gegenereerd_door` (voorbeelden) → 'system'

**Business Impact:** Sensible defaults reduce data entry burden

#### BRC-007: Automatic Timestamps
**Rule:** Creation and update timestamps automatically set
**Enforcement:** DEFAULT CURRENT_TIMESTAMP + triggers
**Business Impact:** Automatic audit timestamps

#### BRC-008: Optimistic Locking (Repository Layer)
**Rule:** Updates check expected version number to prevent conflicts
**Implementation:** In `update_definitie()`
```python
# Verhoog versie altijd bij update
set_clauses.append("version_number = version_number + 1")

# Check expected version if provided
if expected_version is not None:
    where_clause += " AND version_number = ?"
    where_params.append(expected_version)

cursor = conn.execute(query, params + where_params)
if cursor.rowcount == 0 and expected_version is not None:
    logger.warning("Optimistic lock failed")
    return False
```

**Business Impact:** Prevents lost updates in concurrent scenarios

#### BRC-009: Wettelijke Basis Normalization
**Rule:** Legal basis lists normalized for consistent comparison
**Implementation:** `_normalize_wettelijke_basis()` in migration script
**Logic:**
1. Parse JSON array
2. Strip whitespace from each element
3. Create unique set
4. Sort alphabetically
5. Store as JSON array

**Business Impact:** Order-independent duplicate detection

#### BRC-010: Duplicate Detection Multi-Level
**Rule:** Prevent duplicates using three-level matching
**Levels:**
1. **Exact begrip match** + context (score: 1.0)
2. **Synonym match** (case-insensitive) + context (score: 1.0)
3. **Fuzzy match** (70% similarity) + organization (score: 0.7-1.0)

**Exclusions:** Archived definitions excluded
**Business Impact:** Smart duplicate prevention without blocking legitimate variations

---

## Indexes and Performance Rules

### Index Strategy

#### Performance Index 1: Begrip Lookup
```sql
CREATE INDEX idx_definities_begrip ON definities(begrip);
```
**Purpose:** Fast term lookup
**Business Impact:** Core search performance

#### Performance Index 2: Context Lookup
```sql
CREATE INDEX idx_definities_context ON definities(
    organisatorische_context,
    juridische_context
);
```
**Purpose:** Fast context-based filtering
**Business Impact:** Multi-context queries (Note: JSON arrays in actual schema may limit effectiveness)

#### Performance Index 3: Status Filtering
```sql
CREATE INDEX idx_definities_status ON definities(status);
```
**Purpose:** Fast status-based queries (draft, review, established, etc.)
**Business Impact:** Workflow filtering performance

#### Performance Index 4: Category Filtering
```sql
CREATE INDEX idx_definities_categorie ON definities(categorie);
```
**Purpose:** Fast ontological category filtering
**Business Impact:** Category-based reporting

#### Performance Index 5: Created Date Sorting
```sql
CREATE INDEX idx_definities_created_at ON definities(created_at);
```
**Purpose:** Fast chronological sorting
**Business Impact:** Timeline views

#### Performance Index 6: Proposal Date Sorting
```sql
CREATE INDEX idx_definities_datum_voorstel ON definities(datum_voorstel);
```
**Purpose:** Fast legacy proposal date sorting
**Business Impact:** Legacy compatibility queries

#### Performance Index 7: History Lookup
```sql
CREATE INDEX idx_geschiedenis_definitie_id ON definitie_geschiedenis(definitie_id);
CREATE INDEX idx_geschiedenis_datum ON definitie_geschiedenis(gewijzigd_op);
```
**Purpose:** Fast history retrieval by definition and date
**Business Impact:** Audit trail queries

#### Performance Index 8: Tag Lookup
```sql
CREATE INDEX idx_tags_definitie_id ON definitie_tags(definitie_id);
CREATE INDEX idx_tags_naam ON definitie_tags(tag_naam);
```
**Purpose:** Fast tag filtering
**Business Impact:** Tag-based search

#### Performance Index 9: Example Lookup
```sql
CREATE INDEX idx_voorbeelden_definitie_id ON definitie_voorbeelden(definitie_id);
CREATE INDEX idx_voorbeelden_type ON definitie_voorbeelden(voorbeeld_type);
CREATE INDEX idx_voorbeelden_actief ON definitie_voorbeelden(actief);
```
**Purpose:** Fast example retrieval by definition, type, and active status
**Business Impact:** Example display performance

#### Performance Index 10: Case-Insensitive Synonym Lookup
```sql
CREATE INDEX idx_synonyms_text_ci ON definitie_voorbeelden(
    voorbeeld_type,
    actief,
    voorbeeld_tekst COLLATE NOCASE
);
```
**Purpose:** Fast case-insensitive synonym matching
**Business Impact:** Flexible term lookup regardless of case

#### Performance Index 11: Operations Log
```sql
CREATE INDEX idx_logs_operatie_type ON import_export_logs(operatie_type);
CREATE INDEX idx_logs_datum ON import_export_logs(gestart_op);
```
**Purpose:** Fast operation log filtering
**Business Impact:** Operations reporting

---

## UTF-8 Encoding Rules for Dutch Legal Text

### Encoding Strategy

#### UTF-8-001: Database Connection Settings
**Rule:** All database connections use UTF-8 encoding
**Implementation:** In `DefinitieRepository._get_connection()`
```python
conn = sqlite3.connect(
    self.db_path,
    timeout=30.0,
    isolation_level=None,
    check_same_thread=False
)
```

#### UTF-8-002: File Operations
**Rule:** All file operations use explicit UTF-8 encoding
**Examples:**
- Schema loading: `open(schema_path, encoding="utf-8")`
- JSON export: `json.dump(..., ensure_ascii=False, indent=2)`
- JSON import: `open(file_path, encoding="utf-8")`

**Business Impact:** Proper handling of Dutch characters (é, ë, ü, etc.) in legal text

#### UTF-8-003: JSON Storage
**Rule:** JSON stored in TEXT columns uses `ensure_ascii=False`
**Implementation:**
```python
json.dumps(data, ensure_ascii=False)  # Preserves Unicode characters
```

**Business Impact:** Readable JSON storage with native Dutch characters

#### UTF-8-004: Text Column Types
**Rule:** Use TEXT type for variable-length Unicode strings
**Columns:** definitie, toelichting_proces, validation_issues, context_snapshot, approval_notes, etc.

**Business Impact:** No length restrictions on legal text

---

## Audit Trails and Versioning Logic

### Audit Trail Strategy

#### Audit Trail 1: Definition History
**Table:** `definitie_geschiedenis`
**Captured Information:**
- Old and new definition text
- Change type (created, updated, status_changed, approved, archived, auto_save)
- Reason for change
- User who made change
- Complete context snapshot (JSON)

**Triggers:**
- Manual logging via `_log_geschiedenis()` in repository
- Automatic logging via `log_definitie_changes` trigger

**Business Value:**
- Compliance audit trail
- Rollback capability
- Change attribution
- Context reconstruction

#### Audit Trail 2: Import/Export Operations
**Table:** `import_export_logs`
**Captured Information:**
- Operation type (import/export)
- Source/destination
- Counts (processed, successful, failed)
- File path and format
- Error details (JSON)
- Start/end timestamps
- User who initiated

**Business Value:**
- Operations audit trail
- Error tracking
- Success rate metrics

#### Audit Trail 3: Example Assessment
**Captured in:** `definitie_voorbeelden` table
**Fields:**
- `beoordeeld` (boolean)
- `beoordeeling` (goed/matig/slecht)
- `beoordeeling_notities` (text)
- `beoordeeld_door` (user)
- `beoordeeld_op` (timestamp)

**Business Value:**
- Quality tracking for generated examples
- Human-in-the-loop feedback

---

### Versioning Logic

#### Version Strategy
**Approach:** Explicit version numbering with optional version chain linking

#### Version-001: Version Number
**Field:** `version_number INTEGER NOT NULL DEFAULT 1`
**Business Rule:** Incremented atomically on every update
**Implementation:**
```sql
UPDATE definities
SET version_number = version_number + 1, ...
WHERE id = ?
```

#### Version-002: Previous Version Link
**Field:** `previous_version_id INTEGER REFERENCES definities(id)`
**Business Rule:** Optional link to previous version of same definition
**Use Case:** Track definition evolution when creating new major version

#### Version-003: Optimistic Locking
**Mechanism:** Check expected version on update
**Implementation:** See BRC-008
**Business Impact:** Prevents lost updates in concurrent scenarios

#### Version-004: History Reconstruction
**Capability:** Reconstruct any previous version from audit trail
**Data:** `definitie_geschiedenis` contains old/new values for each change
**Business Impact:** Time-travel queries and rollback scenarios

---

## Migration Business Logic

### Migration Strategy (from `migrate_database.py`)

#### Migration-001: Column Addition Detection
**Logic:** Check `PRAGMA table_info(definities)` for missing columns
**Columns Managed:**
- `datum_voorstel` (TIMESTAMP)
- `ketenpartners` (TEXT)
- `wettelijke_basis` (TEXT)
- `ufo_categorie` (TEXT)
- `voorkeursterm` (TEXT)
- `voorkeursterm_is_begrip` (BOOLEAN) - deprecated

#### Migration-002: Safe Column Addition
**Rule:** Only add columns from whitelist
**Whitelist:**
```python
allowed_columns = {
    "datum_voorstel": "TIMESTAMP",
    "ketenpartners": "TEXT",
    "wettelijke_basis": "TEXT",
    "ufo_categorie": "TEXT",
}
```
**Business Impact:** Security against SQL injection in migration

#### Migration-003: Default Value Backfill
**Rule:** Set sensible defaults for newly added columns
**Example:**
```sql
UPDATE definities
SET datum_voorstel = created_at
WHERE datum_voorstel IS NULL
```

#### Migration-004: Voorkeursterm Backfill
**Rule:** Migrate voorkeursterm from multiple sources
**Priority:**
1. Synonyms marked with `is_voorkeursterm = TRUE`
2. Legacy boolean flag `voorkeursterm_is_begrip = TRUE` → use `begrip`

**SQL:**
```sql
-- From synonyms
UPDATE definities
SET voorkeursterm = (
    SELECT v.voorbeeld_tekst FROM definitie_voorbeelden v
    WHERE v.definitie_id = definities.id
      AND v.voorbeeld_type = 'synonyms'
      AND v.actief = TRUE
      AND v.is_voorkeursterm = TRUE
    LIMIT 1
)
WHERE voorkeursterm IS NULL;

-- From boolean flag
UPDATE definities
SET voorkeursterm = begrip
WHERE voorkeursterm IS NULL AND voorkeursterm_is_begrip = TRUE;
```

#### Migration-005: Deprecated Column Removal
**Rule:** Remove obsolete columns by table rebuild
**Columns Removed:**
- `is_voorkeursterm` from `definitie_voorbeelden`
- `voorkeursterm_is_begrip` from `definities`

**Process:**
1. Disable foreign keys
2. Rename old table
3. Create new table without deprecated columns
4. Copy data (excluding deprecated columns)
5. Recreate indexes and triggers
6. Drop old table
7. Re-enable foreign keys

**Business Impact:** Clean schema without legacy baggage

#### Migration-006: Wettelijke Basis Normalization
**Rule:** Normalize all existing `wettelijke_basis` values
**Logic:** See `_normalize_list_json()` function
**Business Impact:** Consistent duplicate detection after migration

#### Migration-007: Foreign Key Correction
**Rule:** Fix any foreign keys still pointing to renamed tables
**Example:** Correct FK from `definities_old` → `definities`
**Business Impact:** Maintain referential integrity after rebuild

#### Migration-008: Index Recreation
**Rule:** Always recreate indexes after table rebuild
**Functions:**
- `_ensure_definities_indexes()`
- `_ensure_definitie_voorbeelden_indexes()`

**Business Impact:** Maintain query performance

---

## Views for Convenience

### View 1: `actieve_definities`
```sql
CREATE VIEW actieve_definities AS
SELECT * FROM definities
WHERE status != 'archived'
ORDER BY begrip, created_at DESC;
```
**Purpose:** Quick access to non-archived definitions
**Business Impact:** Simplified queries for active content

### View 2: `vastgestelde_definities`
```sql
CREATE VIEW vastgestelde_definities AS
SELECT * FROM definities
WHERE status = 'established'
ORDER BY begrip, approved_at DESC;
```
**Purpose:** Quick access to approved definitions
**Business Impact:** Simplified queries for finalized content

### View 3: `definitie_statistieken`
```sql
CREATE VIEW definitie_statistieken AS
SELECT
    categorie,
    organisatorische_context,
    status,
    COUNT(*) as aantal,
    AVG(validation_score) as gemiddelde_score,
    MIN(created_at) as eerste_definitie,
    MAX(updated_at) as laatste_update
FROM definities
GROUP BY categorie, organisatorische_context, status;
```
**Purpose:** Aggregated statistics for reporting
**Business Impact:** Dashboard queries without complex SQL

---

## Database Performance Configuration

### Connection Settings (from `DefinitieRepository`)

```python
conn = sqlite3.connect(
    self.db_path,
    timeout=30.0,              # Prevent "database is locked" errors
    isolation_level=None,      # Autocommit mode
    check_same_thread=False    # Multi-threading support
)

# Performance pragmas
conn.execute("PRAGMA journal_mode=WAL")      # Write-Ahead Logging
conn.execute("PRAGMA synchronous=NORMAL")    # Faster writes
conn.execute("PRAGMA temp_store=MEMORY")     # Temp tables in memory
conn.execute("PRAGMA foreign_keys=ON")       # Enable FK constraints
conn.row_factory = sqlite3.Row               # Column access by name
```

**Business Impact:**
- **WAL mode:** Concurrent reads while writing
- **NORMAL sync:** Balance between performance and safety
- **Memory temp:** Faster complex queries
- **30s timeout:** Handle concurrent access gracefully

---

## Security Considerations

### SQL Injection Prevention

#### Security-001: Parameterized Queries Only
**Rule:** All queries use parameterized placeholders
**Example:**
```python
cursor.execute(
    "SELECT * FROM definities WHERE id = ?",
    (definitie_id,)
)
```
**Business Impact:** Complete SQL injection protection

#### Security-002: Whitelist-Based Updates
**Rule:** Only allow updates to predefined fields
**Implementation:**
```python
allowed_fields = {
    "begrip", "definitie", "status", "categorie",
    "organisatorische_context", "juridische_context",
    "wettelijke_basis", "toelichting_proces", ...
}

for field, value in updates.items():
    if hasattr(current, field) and field in allowed_fields:
        set_clauses.append(f"{field} = ?")
        params.append(value)
```
**Business Impact:** Prevents unauthorized field updates

#### Security-003: Table Name Validation
**Rule:** Validate table names against whitelist in utility functions
**Example:**
```python
allowed_tables = {"definities", "geschiedenis", "metadata"}
if table not in allowed_tables:
    raise ValueError(f"Tabel '{table}' niet toegestaan")
```
**Business Impact:** Prevents table name injection

#### Security-004: Encrypted Credentials
**Rule:** API keys stored encrypted
**Field:** `api_key_encrypted VARCHAR(500)` in `externe_bronnen`
**Business Impact:** Protect sensitive external service credentials

---

## Summary of Key Business Rules

### Critical Business Rules (Top 10)

1. **BR-DB-002:** Status workflow enforcement (imported → draft → review → established → archived)
2. **BR-DB-010:** Duplicate prevention via exact + synonym + fuzzy matching
3. **BR-DB-071:** Automatic change logging via trigger
4. **BR-DB-035:** Active example replacement strategy
5. **BRC-008:** Optimistic locking for concurrent updates
6. **BRC-009:** Wettelijke basis normalization for consistent duplicate detection
7. **BR-DB-006:** JSON array storage for multi-value fields
8. **BR-DB-037:** Synonym-based lookup with case-insensitive matching
9. **BR-DB-009:** Voorkeursterm single source of truth at definition level
10. **BR-DB-001:** 11-category ontological classification system

### Data Quality Rules

- All core fields NOT NULL
- Validation scores 0.00-1.00 range
- Automatic timestamps via triggers
- Cascade deletes maintain referential integrity
- Unique constraints prevent duplicates
- CHECK constraints enforce valid domains

### Audit & Compliance

- Complete change history via triggers
- Context snapshots for rollback
- Import/export operation logging
- User attribution for all changes
- Example assessment tracking

### Performance Optimizations

- 11 strategic indexes
- WAL mode for concurrent access
- Parameterized queries for plan caching
- Row factory for named column access
- 30-second timeout for lock contention

---

## Recommendations for Rebuild

### Data Preservation Priorities

1. **Critical:** Preserve all business rules encoded in CHECK constraints
2. **Critical:** Preserve automatic audit logging (triggers)
3. **Critical:** Preserve duplicate detection logic (exact + synonym + fuzzy)
4. **Critical:** Preserve JSON normalization for wettelijke_basis
5. **High:** Preserve cascade delete behavior
6. **High:** Preserve index strategy
7. **Medium:** Consider simplifying context storage (JSON arrays may complicate indexing)
8. **Low:** Deprecated columns (`voorkeursterm_is_begrip`) can be dropped

### Schema Improvement Opportunities

1. **Context Normalization:** Consider separate tables for organizational/legal contexts instead of JSON arrays for better indexing
2. **Validation Rules Table:** Extract validation_issues JSON to separate table for structured analysis
3. **Ketenpartners Normalization:** Separate table for many-to-many relationship
4. **Audit Trail Querying:** Add indexes on `context_snapshot` JSON fields if SQLite version supports JSON functions
5. **Foreign Key Cleanup:** Remove leftover `definitie_voorbeelden_old2` table references

### Testing Priorities

1. Duplicate detection across all three matching levels
2. Trigger execution for audit logging
3. Optimistic locking under concurrent updates
4. JSON normalization for wettelijke_basis
5. Synonym-based lookup (case-insensitive)
6. Cascade delete behavior
7. Migration backfill logic for voorkeursterm

---

## Appendix: Repository Business Logic Not in Schema

### Duplicate Detection Similarity Algorithm

**Implementation:** `_calculate_similarity()` in repository
```python
def _calculate_similarity(self, str1: str, str2: str) -> float:
    """Jaccard similarity between two strings."""
    str1_lower = str1.lower()
    str2_lower = str2.lower()

    if str1_lower == str2_lower:
        return 1.0

    # Jaccard similarity on word sets
    set1 = set(str1_lower.split())
    set2 = set(str2_lower.split())

    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))

    return intersection / union if union > 0 else 0.0
```

**Business Rule:** 70% similarity threshold for fuzzy matches
**Business Impact:** Balance between catching near-duplicates and allowing legitimate variations

### Search Query Logic

**Implementation:** `search_definities()` with LIKE operators
```python
if query:
    where_clauses.append("(begrip LIKE ? OR definitie LIKE ?)")
    search_term = f"%{query}%"
    params.extend([search_term, search_term])
```

**Business Impact:** Substring matching for flexible search

### Statistics Aggregation

**Implementation:** `get_statistics()` method
**Metrics:**
- Total definitions count
- Counts by status
- Counts by category
- Average validation score

**Business Impact:** Dashboard and reporting capability

---

**End of Database Business Rules Extraction**
