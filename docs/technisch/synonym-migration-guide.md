# Synonym Migration Guide - PHASE 1.4

## Overview

This guide covers the migration of synonym data from 3 legacy sources into the new unified graph-based synonym registry (Synonym Orchestrator Architecture v3.1).

**Architecture Reference:**
`docs/architectuur/synonym-orchestrator-architecture-v3.1.md` (Lines 814-913)

**Migration Script:**
`scripts/migrate_synonyms_to_registry.py`

## Migration Sources

### Source 1: YAML File (Legacy)
- **Location:** `config/juridische_synoniemen.yaml`
- **Structure:**
  ```yaml
  hoofdterm:
    - synoniem: term
      weight: 0.95
  ```
- **Status:** Legacy configuration file
- **Migration Target:** `imported_yaml` source, `active` status
- **Scope:** Global (definitie_id = NULL)

### Source 2: Database - synonym_suggestions Table
- **Location:** `data/definities.db` table `synonym_suggestions`
- **Filter:** Only approved suggestions (`status = 'approved'`)
- **Fields Used:** hoofdterm, synoniem, confidence, context_data, reviewed_by
- **Migration Target:** `ai_suggested` source, `active` status
- **Scope:** Global (definitie_id = NULL)

### Source 3: Database - definitie_voorbeelden Table
- **Location:** `data/definities.db` table `definitie_voorbeelden`
- **Filter:** Where `voorbeeld_type = 'synonyms'` and `actief = TRUE`
- **Fields Used:** definitie_id, begrip, voorbeeld_tekst
- **Migration Target:** `manual` source, `active` status
- **Scope:** Per-definitie (definitie_id = X) - SCOPED!

## Target Schema

### synonym_groups Table
```sql
CREATE TABLE synonym_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_term TEXT NOT NULL UNIQUE,  -- Hoofdterm/voorkeursterm
    domain TEXT,                           -- Optional domain
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    created_by TEXT
);
```

### synonym_group_members Table
```sql
CREATE TABLE synonym_group_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,            -- FK to synonym_groups
    term TEXT NOT NULL,
    weight REAL DEFAULT 1.0,              -- 0.0-1.0 range
    is_preferred BOOLEAN DEFAULT FALSE,
    status TEXT DEFAULT 'active',         -- active, ai_pending, rejected_auto, deprecated
    source TEXT NOT NULL,                 -- db_seed, manual, ai_suggested, imported_yaml
    context_json TEXT,                    -- JSON metadata
    definitie_id INTEGER,                 -- NULL = global, X = scoped
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    created_by TEXT,
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    FOREIGN KEY(group_id) REFERENCES synonym_groups(id) ON DELETE CASCADE,
    FOREIGN KEY(definitie_id) REFERENCES definities(id) ON DELETE CASCADE,
    UNIQUE(group_id, term)
);
```

## Usage

### 1. Preview Migration (Dry-Run)

**Recommended first step:** Always run dry-run to preview what will be migrated.

```bash
python scripts/migrate_synonyms_to_registry.py --dry-run
```

**Output:**
- Total groups that will be created
- Total members that will be added
- Breakdown by source (YAML, suggestions, voorbeelden)
- Conflict detection (duplicates, ambiguities)
- No database writes

**Example Output:**
```
GROUPS & MEMBERS:
  Groups created: 70
  Members added: 192

BY SOURCE:
  YAML imported: 70
  DB approved suggestions: 0
  Definitie voorbeelden: 122

ISSUES:
  Conflicts detected: 36
  Errors encountered: 0
  Items skipped: 36
```

### 2. Execute Migration

**Warning:** This writes to the database. Backup recommended.

```bash
# Backup database first (recommended)
cp data/definities.db data/definities.db.backup

# Execute migration
python scripts/migrate_synonyms_to_registry.py --execute
```

**What happens:**
- Creates synonym_groups for each hoofdterm/begrip
- Adds members to groups with proper source tracking
- Skips duplicates (same term in same group)
- Preserves context_data and reviewed_by from suggestions
- Sets definitie_id for scoped voorbeelden
- Validates migration results
- Logs to `logs/synonym_migration.log`

### 3. Rollback Migration (If Needed)

If migration needs to be undone:

```bash
python scripts/migrate_synonyms_to_registry.py --rollback
```

**What happens:**
- Deletes all groups with `created_by LIKE 'migration_%'`
- CASCADE deletes all associated members
- Safe: Won't delete manually created groups
- Reports count of deleted groups and members

**Example Output:**
```
Will delete 70 groups
Will delete 192 members
Deleted 70 groups (and their members)
```

### 4. Custom Paths

For testing or alternative configurations:

```bash
python scripts/migrate_synonyms_to_registry.py --execute \
    --db-path data/test.db \
    --yaml-path config/custom_synonyms.yaml
```

### 5. Verbose Mode

For detailed logging (DEBUG level):

```bash
python scripts/migrate_synonyms_to_registry.py --dry-run --verbose
```

## Migration Process Flow

### Phase 1: YAML File Migration
1. Check if YAML file exists
2. Load YAML with PyYAML
3. For each hoofdterm:
   - Normalize (replace underscores with spaces)
   - Get or create synonym_group
   - For each synoniem:
     - Check for duplicates
     - Add as member with `source='imported_yaml'`
     - Preserve weight from YAML

### Phase 2: Synonym Suggestions Migration
1. Check if synonym_suggestions table exists
2. Query approved suggestions only
3. For each approved suggestion:
   - Get or create synonym_group for hoofdterm
   - Check for duplicates
   - Add as member with `source='ai_suggested'`
   - Use confidence as weight
   - Preserve context_data and reviewed_by
   - Status: 'active' (already approved)

### Phase 3: Definitie Voorbeelden Migration
1. Check if definitie_voorbeelden table exists
2. Query voorbeelden where type='synonyms' and actief=TRUE
3. Join with definities to get begrip
4. For each voorbeeld:
   - Parse voorbeeld_tekst (JSON array or comma-separated)
   - Get or create synonym_group for begrip
   - For each synoniem:
     - Check for duplicates
     - Add as member with `source='manual'`
     - **SCOPED:** Set definitie_id (not global!)
     - Weight: 1.0 (default for manual)
     - Status: 'active'

### Phase 4: Validation (Execute Mode Only)
1. Get registry statistics
2. Check for orphaned members (should be 0)
3. Check for empty groups (should be 0)
4. Report validation results

## Conflict Detection

The migration script detects and handles several types of conflicts:

### 1. Duplicate Members
**Detection:** Same term appears multiple times in same group
**Behavior:** First occurrence wins, subsequent skipped
**Example:**
```
CONFLICT: Duplicate member in suggestions: 'kracht van gewijsde' in group 'onherroepelijk'
```

**Cause:** Term appears in both YAML and synonym_suggestions
**Resolution:** Use YAML (Source 1) weight, skip suggestion (Source 2)

### 2. Definitie Scoping Duplicates
**Detection:** Same term in multiple definitie_voorbeelden for same begrip
**Behavior:** First definitie_id wins, subsequent skipped
**Example:**
```
CONFLICT: Duplicate member in voorbeelden: 'definitief' in group 'onherroepelijk' (definitie 64)
CONFLICT: Duplicate member in voorbeelden: 'definitief' in group 'onherroepelijk' (definitie 67)
```

**Cause:** Multiple definitions for 'onherroepelijk' with same synonym
**Resolution:** First definitie_id (64) wins, others (67, 69) skipped

**Note:** This is expected behavior. The graph model doesn't support duplicate terms per group.

### 3. Validation Errors
**Detection:** Invalid weight, status, or source values
**Behavior:** Error logged, item skipped
**Example:**
```
ERROR: Failed to add member 'term': weight moet tussen 0.0 en 1.0 zijn: 1.5
```

**Resolution:** Check source data quality, fix invalid values

## Statistics & Reporting

### Migration Statistics
- `groups_created`: Number of new synonym_groups
- `members_added`: Total members added to groups
- `yaml_imported`: Members from YAML file
- `db_approved`: Members from synonym_suggestions
- `definitie_voorbeelden`: Members from definitie_voorbeelden
- `by_source`: Breakdown by source type
- `conflicts`: Number of conflicts detected
- `errors`: Number of errors encountered
- `skipped`: Number of items not migrated
- `duration_seconds`: Total migration time

### Post-Migration Validation
- `total_groups`: Total groups in registry
- `total_members`: Total members in registry
- `members_by_source`: Count per source
- `members_by_status`: Count per status
- `orphaned_members`: Members without group (should be 0)
- `groups_without_members`: Empty groups (should be 0)
- `avg_group_size`: Average members per group

## Expected Results

Based on current data (as of 2025-10-09):

```
DRY-RUN SUMMARY:
  Groups created: 70
  Members added: 192

  YAML imported: 70
  DB approved suggestions: 0 (all duplicates)
  Definitie voorbeelden: 122

  Conflicts detected: 36 (expected duplicates)
  Errors encountered: 0
  Items skipped: 36
```

**Why 0 DB approved suggestions?**
All approved suggestions already exist in YAML (Source 1), so they're correctly detected as duplicates and skipped.

**Why 36 conflicts?**
- 13 from synonym_suggestions (already in YAML)
- 23 from definitie_voorbeelden (multiple definitions with same synonyms)

This is **expected and correct behavior**. The migration prioritizes Source 1 (YAML) over Source 2 (suggestions).

## Troubleshooting

### Issue: YAML file not found
```
YAML file not found: config/juridische_synoniemen.yaml
Skipping Source 1
```
**Solution:** Check YAML path exists, or use `--yaml-path` to specify custom location.

### Issue: Table not found
```
synonym_suggestions table not found
Skipping Source 2
```
**Solution:** Verify database schema is up-to-date. Run migrations if needed.

### Issue: Permission denied
```
FATAL ERROR: unable to open database file
```
**Solution:** Check file permissions on database and logs directory.

### Issue: Foreign key constraint failed
```
ERROR: Failed to add member: FOREIGN KEY constraint failed
```
**Solution:** Verify synonym_groups exists before adding members. Check group_id.

### Issue: UNIQUE constraint failed
```
ValueError: Member 'term' bestaat al in groep X (ID: Y)
```
**Solution:** This is caught and logged as conflict. Check duplicate detection logic.

## Logs

Migration logs are written to:
- **Console:** INFO level by default, DEBUG with `--verbose`
- **File:** `logs/synonym_migration.log` (all levels, persistent)

**Log format:**
```
2025-10-09 21:14:24,937 [INFO] Initialized migration with database: data/definities.db
2025-10-09 21:14:24,949 [INFO] Completed Source 1: 70 members from YAML
2025-10-09 21:14:24,950 [WARNING] CONFLICT: Duplicate member in suggestions: 'kracht van gewijsde'
2025-10-09 21:14:24,962 [ERROR] ERROR: Failed to process 'term': ValueError
```

## Next Steps

After successful migration:

1. **Verify Data:**
   ```sql
   SELECT COUNT(*) FROM synonym_groups;
   SELECT COUNT(*) FROM synonym_group_members;
   SELECT source, COUNT(*) FROM synonym_group_members GROUP BY source;
   ```

2. **Test Registry:**
   ```python
   from repositories.synonym_registry import get_synonym_registry

   registry = get_synonym_registry()
   synonyms = registry.get_synonyms("onherroepelijk", statuses=["active"])
   print(f"Found {len(synonyms)} synonyms for 'onherroepelijk'")
   ```

3. **Update Services:**
   - Connect ProviderManager to SynonymRegistry (PHASE 2)
   - Implement cache layer (PHASE 2)
   - Add AI suggestion flow (PHASE 3)

4. **Archive Legacy:**
   - Keep `juridische_synoniemen.yaml` as backup
   - Document migration date in schema
   - Update application to use registry exclusively

## Architecture Integration

**Current Phase:** PHASE 1.4 - Migration Script
**Dependencies:**
- PHASE 1.1: Database Schema (synonym_groups, synonym_group_members) ✅
- PHASE 1.2: SynonymRegistry Repository ✅
- PHASE 1.3: SynonymConfig ✅

**Next Phases:**
- PHASE 1.5: Integration Testing
- PHASE 2.1: ProviderManager connects to Registry
- PHASE 2.2: Cache Layer (LRU + TTL)
- PHASE 3.1: Orchestrator with AI suggestions

## References

- **Architecture:** `docs/architectuur/synonym-orchestrator-architecture-v3.1.md`
- **Schema:** `src/database/schema.sql` (lines 347-444)
- **Registry:** `src/repositories/synonym_registry.py`
- **Models:** `src/models/synonym_models.py`
- **Script:** `scripts/migrate_synonyms_to_registry.py`

---

**Document Version:** 1.0
**Date:** 2025-10-09
**Phase:** 1.4 - Migration Script
**Status:** Ready for integration testing (PHASE 1.5)
