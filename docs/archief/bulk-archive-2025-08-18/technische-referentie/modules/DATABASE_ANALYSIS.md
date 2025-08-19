# Database Module Comprehensive Analysis

## Overview
Het database module implementeert een robuuste repository pattern voor het beheren van definities en voorbeelden in een SQLite database. Het systeem ondersteunt volledige CRUD operaties, versiebeheer, validatie tracking, import/export functionaliteit, en uitgebreide metadata management.

## Architecture

### Core Components

1. **DefinitieRepository** (definitie_repository.py)
   - Centrale database access layer
   - Implementeert repository pattern voor abstractie
   - Biedt complete CRUD operaties voor definities en voorbeelden
   - Ondersteunt duplicate detection, versioning, en audit trails

2. **Data Models**
   - **DefinitieRecord**: Dataclass voor definitie entiteiten
   - **VoorbeeldenRecord**: Dataclass voor voorbeelden bij definities
   - **DuplicateMatch**: Dataclass voor duplicate detection resultaten

3. **Enumerations**
   - **DefinitieStatus**: draft → review → established → archived
   - **SourceType**: generated, imported, manual
   - **OntologischeCategorie**: type, proces, resultaat, exemplaar

## Database Schema

### Primary Tables

#### 1. **definities** (Core Table)
```sql
- id: INTEGER PRIMARY KEY
- begrip: VARCHAR(255) NOT NULL
- definitie: TEXT NOT NULL
- categorie: VARCHAR(50) with CHECK constraint
- organisatorische_context: VARCHAR(255) NOT NULL
- juridische_context: VARCHAR(255) nullable
- status: VARCHAR(50) DEFAULT 'draft'
- version_number: INTEGER DEFAULT 1
- previous_version_id: INTEGER (self-reference)
- validation_score: DECIMAL(3,2)
- source_type, timestamps, user tracking
- approval workflow fields
- export tracking fields
- legacy metadata fields (datum_voorstel, ketenpartners)
```

**Constraints & Indexes:**
- UNIQUE(begrip, organisatorische_context, juridische_context, status)
- Indexes on: begrip, context, status, categorie, created_at, datum_voorstel

#### 2. **definitie_voorbeelden** (Examples Table)
```sql
- id: INTEGER PRIMARY KEY
- definitie_id: INTEGER REFERENCES definities(id)
- voorbeeld_type: VARCHAR(50) CHECK constrained
- voorbeeld_tekst: TEXT NOT NULL
- voorbeeld_volgorde: INTEGER
- generation metadata (model, parameters)
- beoordeling fields (assessment tracking)
- timestamps and active status
```

**Constraints:**
- UNIQUE(definitie_id, voorbeeld_type, voorbeeld_volgorde)
- Foreign key to definities with CASCADE DELETE

#### 3. **definitie_geschiedenis** (Audit Trail)
```sql
- Tracks all changes to definities
- Stores old/new values
- Change type tracking
- User and timestamp information
- Context snapshot as JSON
```

#### 4. **Supporting Tables**
- **definitie_tags**: Flexible tagging system
- **externe_bronnen**: External source configurations
- **import_export_logs**: Track import/export operations

### Database Views
- **actieve_definities**: Non-archived definitions
- **vastgestelde_definities**: Established definitions only
- **definitie_statistieken**: Aggregated statistics

### Triggers
1. **update_definities_timestamp**: Auto-update timestamps
2. **log_definitie_changes**: Automatic audit logging
3. **update_voorbeelden_timestamp**: Timestamp management for examples

## Repository Methods

### Definition CRUD Operations

#### Create Operations
```python
create_definitie(record: DefinitieRecord) -> int
```
- Validates for duplicates before creation
- Sets timestamps automatically
- Logs creation in geschiedenis table
- Returns new record ID

#### Read Operations
```python
get_definitie(definitie_id: int) -> Optional[DefinitieRecord]
find_definitie(begrip, context, status) -> Optional[DefinitieRecord]
search_definities(query, categorie, context, status, limit) -> List[DefinitieRecord]
```
- Flexible search with multiple filters
- Full-text search in begrip and definitie
- Configurable result limits

#### Update Operations
```python
update_definitie(definitie_id, updates: Dict, updated_by) -> bool
change_status(definitie_id, new_status, changed_by, notes) -> bool
```
- Dynamic field updates
- Status transition management
- Automatic audit logging
- Approval workflow support

#### Duplicate Detection
```python
find_duplicates(begrip, context) -> List[DuplicateMatch]
```
- Exact match detection
- Fuzzy matching with similarity scoring
- Configurable similarity threshold (70%)
- Excludes archived definitions

### Voorbeelden (Examples) Management

#### Save Operations
```python
save_voorbeelden(definitie_id, voorbeelden_dict, generation_model, params) -> List[int]
```
- Batch save functionality
- Deactivates existing examples
- Maintains order within types
- Tracks generation metadata

#### Retrieval Operations
```python
get_voorbeelden(definitie_id, type, actief_only) -> List[VoorbeeldenRecord]
get_voorbeelden_by_type(definitie_id) -> Dict[str, List[str]]
```
- Filter by type and active status
- Grouped retrieval by type
- Ordered by type and sequence

#### Assessment Operations
```python
beoordeel_voorbeeld(voorbeeld_id, beoordeeling, notities, beoordeeld_door) -> bool
```
- Three-level assessment: goed, matig, slecht
- Tracks reviewer and timestamp
- Optional assessment notes

### Import/Export Functionality

#### Export
```python
export_to_json(file_path, filters) -> int
```
- Flexible filtering (status, category, context)
- Includes export metadata
- Pretty-printed JSON output
- Automatic export logging

#### Import
```python
import_from_json(file_path, import_by) -> Tuple[int, int, List[str]]
```
- Batch import with error handling
- Automatic source tracking
- Returns success/failure counts
- Detailed error messages

### Statistics & Monitoring
```python
get_statistics() -> Dict[str, Any]
```
- Total counts by status and category
- Average validation scores
- Aggregated metrics

## Data Models Detail

### DefinitieRecord
Complete data structure with:
- Core fields: id, begrip, definitie, categorie, contexts
- Status management: status, version_number, previous_version_id
- Validation: score, date, issues (JSON)
- Source tracking: type, reference, import source
- User tracking: created_by, updated_by, approved_by
- Timestamps: created_at, updated_at, approved_at, last_exported_at
- Legacy support: datum_voorstel, ketenpartners (JSON)

**Helper Methods:**
- `to_dict()`: JSON serialization
- `get_validation_issues_list()`: Parse validation JSON
- `get_ketenpartners_list()`: Parse partners JSON
- `add_export_destination()`: Track export locations

### VoorbeeldenRecord
Example data structure with:
- Reference: definitie_id
- Content: voorbeeld_type, voorbeeld_tekst, volgorde
- Generation: model, parameters (JSON), gegenereerd_door
- Assessment: beoordeeld, beoordeeling, notities
- Status: actief flag
- Timestamps: aangemaakt_op, bijgewerkt_op

## Security Considerations

1. **SQL Injection Protection**
   - All queries use parameterized statements
   - No string concatenation for user input
   - Proper escaping for all values

2. **Data Validation**
   - CHECK constraints on enums
   - Foreign key constraints
   - Unique constraints for data integrity

3. **Access Control**
   - User tracking on all operations
   - Audit trail for compliance
   - Approval workflow enforcement

## Performance Optimizations

1. **Indexing Strategy**
   - Indexes on all foreign keys
   - Covering indexes for common queries
   - Composite indexes for complex filters

2. **Query Optimization**
   - Row factory for efficient object mapping
   - Lazy loading where appropriate
   - Connection pooling via context managers

3. **Batch Operations**
   - Bulk insert for voorbeelden
   - Transaction management
   - Efficient duplicate detection

## Migration Strategy

The module includes migration support:
- Initial schema in schema.sql
- Migration files in migrations/ folder
- add_metadata_fields.sql adds legacy support fields
- Automatic schema initialization on first use

## Error Handling

1. **Database Errors**
   - Proper exception handling with rollback
   - Detailed error logging
   - User-friendly error messages

2. **Data Integrity**
   - Foreign key enforcement
   - Transaction consistency
   - Validation before operations

3. **Recovery Mechanisms**
   - Transaction rollback on errors
   - Audit trail for recovery
   - Export/import for backup

## Usage Patterns

### Basic Usage
```python
# Initialize repository
repo = DefinitieRepository("definities.db")

# Create definitie
record = DefinitieRecord(
    begrip="test",
    definitie="Een test definitie",
    categorie="proces",
    organisatorische_context="DJI"
)
definitie_id = repo.create_definitie(record)

# Search definities
results = repo.search_definities(query="test", status=DefinitieStatus.DRAFT)

# Update status
repo.change_status(definitie_id, DefinitieStatus.ESTABLISHED, "reviewer")
```

### Voorbeelden Management
```python
# Save examples
voorbeelden = {
    "sentence": ["Voorbeeld zin 1", "Voorbeeld zin 2"],
    "practical": ["Praktisch voorbeeld"]
}
repo.save_voorbeelden(definitie_id, voorbeelden, "gpt-4")

# Retrieve and assess
examples = repo.get_voorbeelden(definitie_id)
repo.beoordeel_voorbeeld(examples[0].id, "goed", "Uitstekend voorbeeld")
```

## Potential Issues & Improvements

### Current Issues
1. **Connection Management**: Uses SQLite directly, could benefit from connection pooling
2. **Error in save_voorbeelden**: References self.conn instead of using connection context
3. **Missing conn attribute**: Repository doesn't maintain persistent connection

### Suggested Improvements
1. **Connection Pool**: Implement proper connection pooling for concurrent access
2. **Async Support**: Add async methods for better performance
3. **Caching Layer**: Add caching for frequently accessed definitions
4. **Full-Text Search**: Implement FTS5 for better search capabilities
5. **Backup Strategy**: Automated backup procedures
6. **Data Archival**: Implement archival strategy for old definitions

## Conclusion

The database module provides a comprehensive, well-structured solution for definition management with strong emphasis on:
- Data integrity through constraints and validation
- Audit trails and compliance tracking
- Flexible search and filtering capabilities
- Version control and change management
- Import/export for interoperability

The repository pattern provides good abstraction, making it easy to potentially switch to other database systems in the future while maintaining the same interface.
