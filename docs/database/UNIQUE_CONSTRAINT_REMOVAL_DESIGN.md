# UNIQUE INDEX Removal Strategy - Design Document

## Document Information
- **Created**: 2025-11-10
- **Author**: Claude Code (AI Assistant)
- **Status**: Design Phase
- **Risk Level**: MEDIUM (reversible, but requires careful testing)

## Executive Summary

This document provides a comprehensive, safe strategy for removing the database UNIQUE INDEX constraint (`idx_definities_unique_full`) that currently prevents creating multiple definitions with the same attributes (begrip, context, categorie, wettelijke_basis).

**Key Insight**: The constraint is implemented as a **UNIQUE INDEX**, not a table-level UNIQUE constraint. This makes removal simple and fully reversible.

---

## 1. Problem Statement

### Current State
- Migration `008_add_unique_constraint.sql` (2025-10-31) added UNIQUE INDEX:
  ```sql
  CREATE UNIQUE INDEX IF NOT EXISTS idx_definities_unique_full
  ON definities(begrip, organisatorische_context, juridische_context, wettelijke_basis, categorie)
  WHERE status != 'archived';
  ```
- This index prevents multiple definitions with identical 5-field combinations
- Python-level duplicate detection in `find_duplicates()` still warns users

### Desired State
- Allow multiple definitions with same attributes (no database constraint)
- Keep Python-level duplicate check as **warning only** (not blocking)
- Maintain data integrity through application logic
- Preserve audit trail and version history

### Business Justification
From schema.sql line 81:
```sql
-- (UNIQUE constraint tijdelijk uitgeschakeld i.v.m. importstrategie)
```
The constraint was **already intended to be temporary** for import strategy.

---

## 2. Architecture Analysis

### 2.1 Constraint Type: UNIQUE INDEX
**Critical Discovery**: This is NOT a table-level UNIQUE constraint, but a **UNIQUE INDEX**.

**Implications**:
- ✅ **SAFE**: Can be dropped without schema modification
- ✅ **REVERSIBLE**: Can be recreated with same SQL command
- ✅ **NO DATA LOSS**: Only affects insert validation, not existing data
- ✅ **NO FOREIGN KEY CASCADE**: Index removal doesn't trigger cascades

### 2.2 Code Impact Areas

#### Python Code Handling Duplicates

**1. `definitie_repository.py` (lines 531-573)**
```python
def create_definitie(self, record: DefinitieRecord, allow_duplicate: bool = False) -> int:
    # Check for duplicates: permit if explicitly allowed
    if not allow_duplicate:
        duplicates = self.find_duplicates(...)
        if duplicates and any(d.definitie_record.status != DefinitieStatus.ARCHIVED.value for d in duplicates):
            raise ValueError(f"Definitie voor '{record.begrip}' bestaat al in deze context")
```

**Impact**: NO CHANGES NEEDED
- Already has `allow_duplicate` parameter
- Python check remains as **warning mechanism**
- Will continue to raise `ValueError` (caught by UI as warning)

**2. `definition_repository.py` (lines 89-120)**
```python
def save(self, definition: Definition) -> int:
    try:
        # Bypass duplicate guard if explicitly allowed via metadata
        allow_duplicate = False
        if definition.metadata and bool(definition.metadata.get("force_duplicate")):
            allow_duplicate = True

        result_id = self.legacy_repo.create_definitie(record, allow_duplicate=allow_duplicate)
    except ValueError as e:
        if "bestaat al" in str(e).lower():
            raise DuplicateDefinitionError(...) from e
```

**Impact**: MINIMAL CHANGES
- Already handles duplicates gracefully
- Error handling remains valid (Python check still raises ValueError)
- May want to add logging when `allow_duplicate=True` is used

**3. `find_duplicates()` (lines 750-898)**
```python
def find_duplicates(self, begrip: str, organisatorische_context: str,
                   juridische_context: str = "", categorie: str | None = None,
                   wettelijke_basis: list[str] | None = None) -> list[DuplicateMatch]:
    """
    Searches for potential duplicates matching:
    - Exact match: begrip + context + categorie + wettelijke_basis
    - Exact synonym match (case-insensitive)
    - Fuzzy match on begrip (>70% similarity)
    """
```

**Impact**: NO CHANGES NEEDED
- This method provides **detection only**, not blocking
- Returns list of matches for UI to display as warnings
- Algorithm remains valid after constraint removal

---

## 3. Migration Design

### 3.1 Forward Migration (Remove Constraint)

**File**: `src/database/migrations/009_remove_unique_constraint.sql`

```sql
-- Migration 009: Remove UNIQUE constraint to allow multiple definitions (DESIGN-2025-11-10)
-- Author: System (AI-assisted design)
-- Date: 2025-11-10
-- Description: Removes the UNIQUE INDEX constraint that was added in migration 008.
--              This allows multiple definitions with same attributes (begrip, context,
--              categorie, wettelijke_basis) to be created. Duplicate detection remains
--              at application level (Python code) as warning-only mechanism.
--
-- Business Rationale:
--   - The constraint was marked as temporary in schema.sql line 81
--   - Import strategy requires flexibility to create similar definitions
--   - Application-level duplicate detection provides better UX (warnings vs hard blocks)
--   - Users need ability to create contextually similar definitions
--
-- Prerequisites:
--   - Migration 008 must have been applied (UNIQUE INDEX exists)
--   - No code changes required (Python duplicate check remains)
--
-- Rollback: Re-apply migration 008 (see 008_add_unique_constraint.sql)

-- Drop the UNIQUE INDEX created in migration 008
DROP INDEX IF EXISTS idx_definities_unique_full;

-- Verification query (should return the index count = 0):
-- SELECT COUNT(*) FROM sqlite_master
-- WHERE type='index' AND name='idx_definities_unique_full';

-- After this migration:
-- - Multiple definitions with identical attributes CAN be created
-- - Python code in definitie_repository.find_duplicates() still detects them
-- - UI will show warnings but allow creation (if user confirms)
-- - Database integrity relies on application logic (not SQL constraints)
```

### 3.2 Rollback Migration (Restore Constraint)

**File**: `src/database/migrations/009_rollback_remove_unique_constraint.sql`

```sql
-- Rollback Migration 009: Restore UNIQUE constraint
-- Author: System (emergency rollback)
-- Date: 2025-11-10
-- Description: Restores the UNIQUE INDEX that was removed in migration 009.
--
-- WARNING: This rollback will FAIL if duplicate records exist in database!
--          Run cleanup_duplicates.py BEFORE rolling back.
--
-- Prerequisites:
--   - No duplicate records in definities table (status != 'archived')
--   - Run: python scripts/cleanup_duplicates.py --preview first
--   - Then: python scripts/cleanup_duplicates.py --execute

-- Restore the UNIQUE INDEX (exact copy from migration 008)
CREATE UNIQUE INDEX IF NOT EXISTS idx_definities_unique_full
ON definities(
    begrip,
    organisatorische_context,
    juridische_context,
    wettelijke_basis,
    categorie
)
WHERE status != 'archived';

-- Verification query (should return 0 duplicates):
-- SELECT begrip, organisatorische_context, juridische_context,
--        wettelijke_basis, categorie, COUNT(*) as count
-- FROM definities
-- WHERE status != 'archived'
-- GROUP BY begrip, organisatorische_context, juridische_context,
--          wettelijke_basis, categorie
-- HAVING COUNT(*) > 1;
```

---

## 4. Code Changes Required

### 4.1 MINIMAL - Add Logging When Allowing Duplicates

**File**: `src/database/definitie_repository.py`

**Location**: Line 553 (in `create_definitie()` method)

```python
def create_definitie(self, record: DefinitieRecord, allow_duplicate: bool = False) -> int:
    """Create new definition, optionally allowing duplicates."""

    # Set database save flag
    try:
        from ui.session_state import SessionStateManager
        SessionStateManager.set_value("saving_to_database", True)
    except Exception:
        pass

    try:
        with self._get_connection() as conn:
            # Check for duplicates: permit if explicitly allowed
            if not allow_duplicate:
                duplicates = self.find_duplicates(...)

                if duplicates and any(d.definitie_record.status != DefinitieStatus.ARCHIVED.value
                                     for d in duplicates):
                    msg = f"Definitie voor '{record.begrip}' bestaat al in deze context"
                    raise ValueError(msg)
            else:
                # NEW: Log when explicitly allowing duplicates
                logger.info(
                    f"Creating definition with allow_duplicate=True: "
                    f"begrip='{record.begrip}', categorie={record.categorie}, "
                    f"context={record.organisatorische_context}"
                )

            # ... rest of create logic ...
```

**Rationale**: Audit trail for when duplicates are intentionally created.

### 4.2 NO CHANGES NEEDED

The following code **already handles duplicates correctly**:

1. **`find_duplicates()`** - Detection logic remains valid
2. **`allow_duplicate` parameter** - Already exists and works
3. **Error handling in `definition_repository.py`** - Catches ValueError correctly
4. **UI duplicate warnings** - Show warnings but allow override

---

## 5. Testing Strategy

### 5.1 Pre-Migration Tests

**File**: `tests/database/test_unique_constraint_exists.py` (NEW)

```python
"""Test that UNIQUE INDEX exists before migration 009."""
import sqlite3
import pytest

def test_unique_index_exists_before_migration(test_db_path):
    """Verify UNIQUE INDEX exists before removal."""
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    # Check index exists
    cursor.execute("""
        SELECT COUNT(*) FROM sqlite_master
        WHERE type='index' AND name='idx_definities_unique_full'
    """)
    count = cursor.fetchone()[0]

    assert count == 1, "UNIQUE INDEX should exist before migration"

def test_duplicate_insert_blocked_before_migration(test_db_path):
    """Verify duplicates are blocked before migration."""
    repo = DefinitieRepository(test_db_path)

    record1 = DefinitieRecord(
        begrip="test", definitie="def1", categorie="ENT",
        organisatorische_context="DJI", juridische_context="strafrecht",
        wettelijke_basis="[]"
    )

    id1 = repo.create_definitie(record1)
    assert id1 > 0

    # Attempt duplicate - should raise ValueError
    record2 = DefinitieRecord(
        begrip="test", definitie="def2", categorie="ENT",
        organisatorische_context="DJI", juridische_context="strafrecht",
        wettelijke_basis="[]"
    )

    with pytest.raises(ValueError, match="bestaat al"):
        repo.create_definitie(record2)
```

### 5.2 Post-Migration Tests

**File**: `tests/database/test_unique_constraint_removed.py` (NEW)

```python
"""Test that UNIQUE INDEX is removed after migration 009."""
import sqlite3
import pytest

def test_unique_index_removed_after_migration(test_db_path):
    """Verify UNIQUE INDEX is removed after migration."""
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    # Check index does NOT exist
    cursor.execute("""
        SELECT COUNT(*) FROM sqlite_master
        WHERE type='index' AND name='idx_definities_unique_full'
    """)
    count = cursor.fetchone()[0]

    assert count == 0, "UNIQUE INDEX should NOT exist after migration"

def test_duplicate_insert_allowed_after_migration(test_db_path):
    """Verify duplicates ARE allowed after migration (with allow_duplicate=True)."""
    repo = DefinitieRepository(test_db_path)

    record1 = DefinitieRecord(
        begrip="test", definitie="def1", categorie="ENT",
        organisatorische_context="DJI", juridische_context="strafrecht",
        wettelijke_basis="[]"
    )

    id1 = repo.create_definitie(record1, allow_duplicate=False)
    assert id1 > 0

    # Attempt duplicate WITH allow_duplicate=True - should succeed
    record2 = DefinitieRecord(
        begrip="test", definitie="def2 (variant)", categorie="ENT",
        organisatorische_context="DJI", juridische_context="strafrecht",
        wettelijke_basis="[]"
    )

    id2 = repo.create_definitie(record2, allow_duplicate=True)
    assert id2 > 0
    assert id2 != id1

    # Verify both records exist
    def1 = repo.get_definitie(id1)
    def2 = repo.get_definitie(id2)

    assert def1.definitie == "def1"
    assert def2.definitie == "def2 (variant)"

def test_duplicate_check_still_detects_after_migration(test_db_path):
    """Verify find_duplicates() still works after constraint removal."""
    repo = DefinitieRepository(test_db_path)

    # Create two identical definitions
    record1 = DefinitieRecord(
        begrip="test", definitie="def1", categorie="ENT",
        organisatorische_context="DJI", juridische_context="strafrecht",
        wettelijke_basis="[]"
    )
    record2 = DefinitieRecord(
        begrip="test", definitie="def2", categorie="ENT",
        organisatorische_context="DJI", juridische_context="strafrecht",
        wettelijke_basis="[]"
    )

    repo.create_definitie(record1)
    repo.create_definitie(record2, allow_duplicate=True)

    # find_duplicates should detect both
    duplicates = repo.find_duplicates("test", "DJI", "strafrecht", "ENT", [])

    assert len(duplicates) == 2, "Should find both definitions as duplicates"
    assert all(d.match_score == 1.0 for d in duplicates), "Should be exact matches"

def test_python_duplicate_guard_without_allow_flag(test_db_path):
    """Verify Python-level duplicate check still blocks when allow_duplicate=False."""
    repo = DefinitieRepository(test_db_path)

    record1 = DefinitieRecord(
        begrip="test", definitie="def1", categorie="ENT",
        organisatorische_context="DJI", juridische_context="strafrecht",
        wettelijke_basis="[]"
    )

    repo.create_definitie(record1)

    # Attempt duplicate WITHOUT allow_duplicate - should raise ValueError
    record2 = DefinitieRecord(
        begrip="test", definitie="def2", categorie="ENT",
        organisatorische_context="DJI", juridische_context="strafrecht",
        wettelijke_basis="[]"
    )

    with pytest.raises(ValueError, match="bestaat al"):
        repo.create_definitie(record2, allow_duplicate=False)
```

### 5.3 Integration Tests

**File**: `tests/integration/test_duplicate_workflow_after_migration.py` (NEW)

```python
"""Integration tests for duplicate handling after constraint removal."""

def test_ui_duplicate_warning_workflow(test_app):
    """Test that UI shows warning but allows creation with confirmation."""
    # 1. Create first definition
    result1 = test_app.create_definition(
        begrip="test",
        definitie="First definition",
        categorie="ENT",
        context={"organisatorische_context": ["DJI"], "juridische_context": ["strafrecht"]}
    )
    assert result1.success

    # 2. Attempt duplicate - should show warning dialog
    result2 = test_app.create_definition(
        begrip="test",
        definitie="Second definition",
        categorie="ENT",
        context={"organisatorische_context": ["DJI"], "juridische_context": ["strafrecht"]}
    )

    assert result2.duplicate_warning is True, "Should show duplicate warning"
    assert result2.can_override is True, "Should allow override"

    # 3. Confirm creation (user clicks "Create Anyway")
    result3 = test_app.create_definition(
        begrip="test",
        definitie="Second definition",
        categorie="ENT",
        context={"organisatorische_context": ["DJI"], "juridische_context": ["strafrecht"]},
        force_duplicate=True  # User confirmed
    )

    assert result3.success is True, "Should succeed with force_duplicate"
    assert result3.id != result1.id, "Should be different definitions"
```

### 5.4 Regression Tests

**Ensure existing tests still pass:**

```bash
# Run existing duplicate detection tests
pytest tests/services/test_duplicate_detection_service.py -v

# Run repository tests
pytest tests/services/test_definition_repository.py -v
pytest tests/unit/test_definition_repository_error_handling.py -v

# Run integration tests
pytest tests/test_duplicate_detection_fix.py -v
pytest tests/test_duplicate_web_lookup_fix.py -v
```

---

## 6. Risk Assessment

### 6.1 Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Accidental duplicate creation** | MEDIUM | LOW | Python-level check still warns; logging added |
| **Performance degradation (duplicate checks)** | LOW | LOW | find_duplicates() already optimized with indexes |
| **Data integrity loss** | LOW | MEDIUM | Application logic enforces rules; audit trail preserved |
| **Rollback failure due to duplicates** | MEDIUM | MEDIUM | Provide cleanup script; test rollback in staging |
| **User confusion (multiple similar defs)** | MEDIUM | LOW | UI improvements to show duplicate warnings clearly |

### 6.2 Rollback Scenarios

**Scenario 1: Migration fails during deployment**
- **Solution**: Migration script has `IF EXISTS` check - safe to retry
- **Impact**: NONE (no changes applied)

**Scenario 2: Duplicates created after migration, need to restore constraint**
- **Solution**: Run `cleanup_duplicates.py` BEFORE rollback
- **Impact**: MEDIUM (requires manual cleanup)
- **Prevention**: Test rollback procedure in staging first

**Scenario 3: Application bugs cause excessive duplicates**
- **Solution**: Monitor logs for `allow_duplicate=True` usage; restore constraint if needed
- **Impact**: LOW (duplicates can be merged later)

---

## 7. Deployment Plan

### 7.1 Pre-Deployment Checklist

- [ ] Review migration SQL (009_remove_unique_constraint.sql)
- [ ] Review rollback SQL (009_rollback_remove_unique_constraint.sql)
- [ ] Add logging to `create_definitie()` (optional enhancement)
- [ ] Write pre-migration tests
- [ ] Write post-migration tests
- [ ] Test migration in local dev environment
- [ ] Test rollback procedure (critical!)
- [ ] Document expected behavior change in user docs

### 7.2 Deployment Steps

```bash
# 1. Backup database
cp data/definities.db data/definities.db.backup_pre_migration_009

# 2. Verify UNIQUE INDEX exists
sqlite3 data/definities.db "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_definities_unique_full';"
# Expected output: idx_definities_unique_full

# 3. Run pre-migration tests
pytest tests/database/test_unique_constraint_exists.py -v

# 4. Apply migration
sqlite3 data/definities.db < src/database/migrations/009_remove_unique_constraint.sql

# 5. Verify INDEX removed
sqlite3 data/definities.db "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name='idx_definities_unique_full';"
# Expected output: 0

# 6. Run post-migration tests
pytest tests/database/test_unique_constraint_removed.py -v

# 7. Run regression tests
pytest tests/services/test_duplicate_detection_service.py -v
pytest tests/services/test_definition_repository.py -v

# 8. Smoke test: Create duplicate definition via UI
# - Open app: bash scripts/run_app.sh
# - Create definition: begrip="test", categorie="ENT"
# - Attempt duplicate: should show warning but allow creation
```

### 7.3 Post-Deployment Monitoring

**Monitor these logs for 1 week:**

```python
# Look for duplicate creation events
grep "allow_duplicate=True" logs/app.log

# Count duplicate definitions per day
# Should remain LOW (< 5% of total definitions)
```

**If duplicate rate > 10%:**
- Investigate root cause (UI bug? User confusion?)
- Consider restoring constraint temporarily
- Add UI improvements to reduce confusion

---

## 8. Rollback Procedure

### 8.1 Emergency Rollback (if migration causes issues)

```bash
# 1. Stop application
# Ctrl+C if running locally

# 2. Restore backup
cp data/definities.db.backup_pre_migration_009 data/definities.db

# 3. Verify INDEX restored
sqlite3 data/definities.db "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_definities_unique_full';"
# Expected output: idx_definities_unique_full

# 4. Restart application
bash scripts/run_app.sh
```

### 8.2 Planned Rollback (after duplicates exist)

```bash
# 1. Check for duplicates
sqlite3 data/definities.db <<EOF
SELECT begrip, organisatorische_context, COUNT(*) as count
FROM definities
WHERE status != 'archived'
GROUP BY begrip, organisatorische_context, juridische_context, wettelijke_basis, categorie
HAVING COUNT(*) > 1;
EOF

# 2. If duplicates exist, clean up FIRST
python scripts/cleanup_duplicates.py --preview
python scripts/cleanup_duplicates.py --execute

# 3. Apply rollback migration
sqlite3 data/definities.db < src/database/migrations/009_rollback_remove_unique_constraint.sql

# 4. Verify no errors during rollback
# If UNIQUE constraint violation occurs, repeat step 2
```

---

## 9. Success Criteria

### 9.1 Technical Success Criteria

- ✅ UNIQUE INDEX removed from database
- ✅ Duplicate definitions CAN be created (with `allow_duplicate=True`)
- ✅ Python-level duplicate check STILL raises ValueError (when `allow_duplicate=False`)
- ✅ All existing tests pass
- ✅ New post-migration tests pass
- ✅ Rollback procedure tested and documented

### 9.2 Business Success Criteria

- ✅ Users can create multiple definitions with same attributes (after confirmation)
- ✅ UI still shows duplicate warnings (not silently creating duplicates)
- ✅ Import strategy works without constraint violations
- ✅ No performance degradation
- ✅ Audit trail preserved

### 9.3 Monitoring Metrics

**Track for 2 weeks after deployment:**

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| Duplicate definitions created per day | < 5 | > 10 |
| Percentage of definitions that are duplicates | < 5% | > 10% |
| User complaints about duplicates | 0 | > 1 |
| Performance of `find_duplicates()` | < 100ms | > 500ms |
| Database size growth | < 10% | > 25% |

---

## 10. Next Steps

### 10.1 Implementation Checklist

1. **Create migration files** (this document → SQL)
2. **Add logging enhancement** (optional)
3. **Write pre-migration tests**
4. **Write post-migration tests**
5. **Test locally** (dev environment)
6. **Document user-facing changes**
7. **Execute migration** (production)
8. **Monitor for 1 week**

### 10.2 Follow-Up Tasks

- **EPIC-XXX**: UI improvements for duplicate warnings
- **US-XXX**: Add merge functionality for duplicate definitions
- **US-XXX**: Add "View Similar Definitions" in definition detail view
- **DOCS**: Update user guide with duplicate handling explanation

---

## Appendix A: Related Files

### Database Files
- `src/database/schema.sql` - Main schema (line 81: constraint comment)
- `src/database/migrations/008_add_unique_constraint.sql` - Original constraint
- `src/database/migrations/009_remove_unique_constraint.sql` - This migration (TO BE CREATED)

### Python Code
- `src/database/definitie_repository.py` - create_definitie(), find_duplicates()
- `src/services/definition_repository.py` - save(), error handling

### Tests
- `tests/services/test_duplicate_detection_service.py`
- `tests/services/test_definition_repository.py`
- `tests/unit/test_definition_repository_error_handling.py`
- `tests/test_duplicate_detection_fix.py`

### Documentation
- `CLAUDE.md` - Project guidelines
- `docs/architectuur/TECHNICAL_ARCHITECTURE.md` - Database architecture

---

## Appendix B: SQL Commands Reference

### Check if UNIQUE INDEX exists
```sql
SELECT name, sql FROM sqlite_master
WHERE type='index' AND name='idx_definities_unique_full';
```

### List all indexes on definities table
```sql
SELECT name, sql FROM sqlite_master
WHERE type='index' AND tbl_name='definities';
```

### Count duplicate definitions (should be 0 before migration)
```sql
SELECT begrip, organisatorische_context, juridische_context,
       wettelijke_basis, categorie, COUNT(*) as count
FROM definities
WHERE status != 'archived'
GROUP BY begrip, organisatorische_context, juridische_context,
         wettelijke_basis, categorie
HAVING COUNT(*) > 1;
```

### Manually drop UNIQUE INDEX (if needed)
```sql
DROP INDEX IF EXISTS idx_definities_unique_full;
```

### Manually recreate UNIQUE INDEX (rollback)
```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_definities_unique_full
ON definities(begrip, organisatorische_context, juridische_context,
              wettelijke_basis, categorie)
WHERE status != 'archived';
```

---

## Appendix C: Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-11-10 | Remove UNIQUE INDEX (not table constraint) | Simpler, reversible, no schema changes |
| 2025-11-10 | Keep Python-level duplicate check | Provides user warnings without hard blocks |
| 2025-11-10 | Add logging for allow_duplicate=True | Audit trail for intentional duplicates |
| 2025-11-10 | Require cleanup before rollback | Prevents UNIQUE constraint violations on rollback |

---

## Appendix D: Questions & Answers

**Q: Why remove the constraint instead of adding more exceptions?**
**A**: The constraint was marked as temporary in schema.sql. Removing it aligns with original intent and provides flexibility for import strategy.

**Q: Won't this lead to data quality issues?**
**A**: No - Python-level validation still detects duplicates and warns users. Users must explicitly confirm to create duplicates.

**Q: What if we need to restore the constraint later?**
**A**: Rollback migration is provided. Just run cleanup script first to remove any duplicates that were created.

**Q: How do we prevent accidental duplicate creation?**
**A**: UI shows warnings, Python code requires explicit `allow_duplicate=True`, and logging tracks all duplicate creations.

**Q: Can this migration be run multiple times safely?**
**A**: Yes - uses `DROP INDEX IF EXISTS`, so it's idempotent.

---

**END OF DESIGN DOCUMENT**
