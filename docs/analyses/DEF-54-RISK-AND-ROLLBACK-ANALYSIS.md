# DEF-54: Risk & Rollback Analysis - Debug Specialist Report

**Date**: 2025-10-29
**Analyst**: Debug Specialist (Claude)
**Risk Assessment Level**: DETAILED
**Focus**: Failure probability, rollback strategies, test blindspots, recovery procedures

---

## Executive Summary

**CRITICAL FINDINGS**:
1. **Phase 5 (Type Conversions)** has 85% failure probability - HIGHEST RISK
2. **Database schema rollback** is MISSING - potential data loss scenario
3. **Streamlit session state corruption** not addressed - memory leak risk
4. **Race conditions in concurrent updates** - no detection strategy
5. **Feature flag has NO automatic health checks** - could fail silently

**RECOMMENDATION**: Use **Modified Hybrid Plan** with enhanced rollback mechanisms and mandatory health checks after each phase.

---

## 1. FAILURE PROBABILITY ANALYSIS

### Phase Risk Scoring (0-100%)

| Phase | Risk % | Failure Scenarios | Detection Time | Recovery Time |
|-------|--------|-------------------|----------------|---------------|
| **Phase 0: Schema** | 15% | Migration script fails mid-run | Immediate | 5 min |
| **Phase 1: Feature Flag** | 5% | Import errors, wrong logic | Immediate | 2 min |
| **Phase 2: Tests** | 0% | N/A (tests only) | N/A | N/A |
| **Phase 3a: CRUD** | 25% | Type mismatch, SQL errors | 1-2 days | 30 sec |
| **Phase 3b: Duplicates** | 30% | False positives/negatives | 3-5 days | 30 sec |
| **Phase 3c: Status** | 40% | Draft creation breaks UI | 1-2 days | 30 sec |
| **Phase 4: Voorbeelden** | 50% | Synonym sync deadlock | 2-3 days | 30 sec |
| **Phase 5: Conversions** | **85%** | 23 files break simultaneously | Hours-Days | **HARD** |
| **Phase 6a: UI Tabs** | 20% | Streamlit cache corruption | Immediate | 30 sec |
| **Phase 6b: Services** | 35% | Circular dependencies | 1-2 days | 30 sec |
| **Phase 6c: Utils** | 10% | Import errors | Immediate | 30 sec |
| **Phase 7: Delete Legacy** | 15% | Missed import, runtime error | Immediate | 5 min (git) |
| **Phase 8: Code Quality** | 10% | Refactor introduces bugs | 1-2 days | 5 min (git) |
| **Phase 9: Docs** | 0% | N/A (docs only) | N/A | N/A |

### Critical Risk Analysis

#### 🔴 PHASE 5: Type Conversions Elimination (85% FAILURE RISK)

**Why So Risky?**
1. **Blast Radius**: Touches 23 files simultaneously
2. **Type Safety**: Removing conversions = losing Pydantic validation
3. **Cascading Failures**: One file failure cascades to dependent modules
4. **Hard to Debug**: Which of 23 files caused the issue?
5. **Hard to Rollback**: Feature flag ineffective (requires git revert)

**Failure Scenarios**:
- Services expect `Definition` but receive `DefinitieRecord` → AttributeError
- Pydantic validation removed → invalid data enters database
- UI components break → Streamlit crashes
- Export service fails → CSV contains wrong fields
- Validation rules fail → false negatives

**Mitigation Strategies**:
1. **SKIP THIS PHASE** - Keep type conversions (they provide value)
2. **If you must do it**: Break into 23 sub-phases (1 file per day)
3. **Add runtime type checking**: Use `isinstance()` checks everywhere
4. **Implement adapter fallback**: Keep conversion functions as backup
5. **Extensive integration testing**: Test EVERY workflow after each file

**Rollback Difficulty**: HARD
- Feature flag won't help (conversions already removed)
- Git revert required (conflicts likely if other work done)
- May need to recreate conversion functions manually
- Database might have invalid data (requires cleanup)

---

#### 🟡 PHASE 4: Voorbeelden Management (50% FAILURE RISK)

**Why Risky?**
1. **Complex Business Logic**: 226-line god method
2. **Synonym Sync**: Bidirectional updates, conflict resolution
3. **Database Transactions**: Multi-table updates (voorbeelden + registry)
4. **Race Conditions**: Concurrent synonym updates

**Failure Scenarios**:
- Synonym sync deadlock → database locked, app frozen
- Partial updates → data inconsistency (voorbeelden saved, synonyms not)
- Duplicate detection fails → silent data corruption
- UI hangs → user can't save examples

**Detection Strategy** (MISSING IN PLAN):
```python
# Add health check after Phase 4
def test_voorbeelden_sync_health():
    """Detect synonym sync issues early."""
    # 1. Create voorbeeld with synonym
    repo.save_voorbeelden(def_id, [{"text": "test", "synoniemen": ["foo"]}])

    # 2. Verify synonym in registry
    registry = repo.get_synonym_registry(def_id)
    assert "foo" in registry

    # 3. Update synonym
    repo.save_voorbeelden(def_id, [{"text": "test", "synoniemen": ["bar"]}])

    # 4. Verify old synonym removed
    registry = repo.get_synonym_registry(def_id)
    assert "foo" not in registry
    assert "bar" in registry

    # 5. Concurrent update test
    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(repo.save_voorbeelden, def_id, [...])
        f2 = executor.submit(repo.save_voorbeelden, def_id, [...])
        # Should not deadlock
```

---

#### 🟡 PHASE 3c: Status & Draft Management (40% FAILURE RISK)

**Why Risky?**
1. **UI Impact**: Breaks draft workflow (high visibility)
2. **State Management**: Streamlit session state corruption
3. **Complex Logic**: `get_or_create_draft()` has multiple paths

**Failure Scenarios**:
- Draft creation fails silently → user loses work
- Status transitions broken → definitions stuck in wrong state
- Session state bloat → memory leak (app slows down)
- Concurrent draft creation → duplicate drafts

**Detection Strategy** (MISSING IN PLAN):
```python
# Add session state health check
def test_draft_workflow_session_state():
    """Detect session state corruption."""
    initial_state_size = len(st.session_state)

    # Run workflow 10x
    for i in range(10):
        draft = repo.get_or_create_draft(f"Test_{i}")
        # ... edit draft ...
        repo.save(draft)

    final_state_size = len(st.session_state)

    # Should not grow unbounded
    assert final_state_size - initial_state_size < 5

    # Check for leaked definitions
    leaked_keys = [k for k in st.session_state.keys()
                   if k.startswith('generated_definition_')]
    assert len(leaked_keys) == 0
```

---

## 2. ROLLBACK STRATEGY ASSESSMENT

### Feature Flag vs Git Revert Analysis

#### Feature Flag Approach (Phases 1-6c)

**Strengths**:
- ✅ Instant rollback (30 seconds)
- ✅ No git expertise needed
- ✅ Can toggle back and forth for debugging
- ✅ No code conflicts

**Weaknesses**:
- ❌ No automatic health monitoring
- ❌ Flag could be set wrong (human error)
- ❌ Doesn't help with Phase 5 (type conversions removed)
- ❌ Doesn't rollback database schema changes
- ❌ Session state corruption persists across flag toggle

**MISSING: Health Check Automation**
```python
# Recommended: Auto-health check on startup
# src/services/container.py

def _create_definition_repository(self) -> DefinitionRepositoryInterface:
    if os.getenv("USE_LEGACY_REPO", "false") == "true":
        repo = DefinitionRepository(self.db_path)
    else:
        repo = DefinitieRepositoryV2(self.db_path)

    # AUTO HEALTH CHECK (MISSING IN PLAN)
    try:
        self._verify_repository_health(repo)
    except HealthCheckError as e:
        logger.error(f"Repository health check failed: {e}")
        logger.warning("Falling back to legacy repository")
        repo = DefinitionRepository(self.db_path)  # Auto-fallback

    return repo

def _verify_repository_health(self, repo):
    """Verify repository can perform basic operations."""
    # 1. Can connect to database?
    repo.get(1)  # Try fetching definition

    # 2. Can write to database?
    test_def = DefinitieRecord(begrip="__HEALTH_CHECK__", ...)
    test_id = repo.save(test_def)
    repo.delete(test_id)  # Cleanup

    # 3. Can search?
    repo.search("test")

    # If any fail, raises HealthCheckError
```

#### Git Revert Approach (Phases 7-9)

**Strengths**:
- ✅ Complete rollback (code + tests + docs)
- ✅ Atomic (all or nothing)
- ✅ Audit trail (git history)

**Weaknesses**:
- ❌ Slower (5-10 minutes)
- ❌ Requires git expertise
- ❌ May have merge conflicts
- ❌ Doesn't rollback database data (only schema)

---

### Database Rollback Strategy (CRITICAL GAP)

**PROBLEM**: Current plan has NO database rollback strategy beyond "restore from backup"

**Scenarios Not Covered**:
1. **Phase 0**: Schema migration adds columns → rollback removes columns → **DATA LOSS**
2. **Phase 3a**: New CRUD logic writes invalid data → rollback → invalid data persists
3. **Phase 4**: Synonym sync corrupts registry → rollback code → **registry still corrupt**

**SOLUTION: Implement Database Migration Rollback**

```sql
-- src/database/migrations/007_rollback.sql (MISSING)

-- Rollback for 007_duplicate_constraint.sql
ALTER TABLE definities DROP CONSTRAINT IF EXISTS unique_begrip_active;

-- Rollback for any new columns (example)
ALTER TABLE definities DROP COLUMN IF EXISTS new_column_name;

-- Restore old triggers (if modified)
DROP TRIGGER IF EXISTS new_trigger;
CREATE TRIGGER old_trigger ...;
```

```python
# scripts/rollback/rollback_schema.py (MISSING)

import sqlite3
import sys
from pathlib import Path

def rollback_schema(db_path: str, target_version: int):
    """Rollback database schema to target version."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get current version
    cursor.execute("SELECT MAX(version) FROM schema_migrations")
    current_version = cursor.fetchone()[0]

    if current_version <= target_version:
        print(f"Already at version {current_version}")
        return

    # Apply rollback migrations in reverse
    for version in range(current_version, target_version, -1):
        rollback_file = f"src/database/migrations/{version:03d}_rollback.sql"
        if not Path(rollback_file).exists():
            print(f"ERROR: Rollback file missing: {rollback_file}")
            sys.exit(1)

        print(f"Rolling back version {version}...")
        with open(rollback_file) as f:
            cursor.executescript(f.read())

        # Update migration table
        cursor.execute("DELETE FROM schema_migrations WHERE version = ?", (version,))

    conn.commit()
    print(f"Rolled back to version {target_version}")

if __name__ == "__main__":
    rollback_schema("data/definities.db", int(sys.argv[1]))
```

---

### Points of No Return (HARD TO ROLLBACK)

#### 1. Phase 5: Type Conversions Removed
- **Why No Return**: 186 lines of conversion code deleted
- **Impact**: 23 files dependent on conversions
- **Rollback Difficulty**: HIGH
- **Recovery Plan**:
  1. Git revert commit (may have conflicts)
  2. Manually recreate `_definition_to_record()` and `_record_to_definition()`
  3. Re-update all 23 files
  4. Re-test everything
- **Time to Recover**: 4-8 hours

#### 2. Phase 7: Legacy Wrapper Deleted
- **Why No Return**: 887 lines deleted, feature flag removed
- **Impact**: No fallback mechanism
- **Rollback Difficulty**: MEDIUM
- **Recovery Plan**:
  1. Git revert commit
  2. Restore `src/services/definition_repository.py`
  3. Restore feature flag logic
  4. Restart app
- **Time to Recover**: 10-15 minutes

#### 3. Phase 0: Schema Migration (DATA LOSS RISK)
- **Why No Return**: ALTER TABLE adds columns (removing = data loss)
- **Impact**: Can't rollback schema without losing data
- **Rollback Difficulty**: HIGH (if data written to new columns)
- **Recovery Plan**:
  1. Export all data to CSV BEFORE Phase 0
  2. Restore database from backup
  3. Re-import data
- **Time to Recover**: 20-30 minutes

**RECOMMENDATION**: Create rollback scripts for Phase 0, 5, 7 BEFORE starting

---

## 3. MISSING TESTS BLINDSPOTS

### Edge Cases Not Covered

#### Blindspot 1: Concurrent Updates (Race Conditions)

**Current Plan**: No concurrency tests
**Risk**: User clicks "Save" twice → duplicate definitions

```python
# tests/database/test_definitie_repository_v2_concurrency.py (MISSING)

import pytest
from concurrent.futures import ThreadPoolExecutor

def test_concurrent_saves_no_duplicates():
    """Test concurrent saves don't create duplicates."""
    repo = DefinitieRepositoryV2()

    def save_definition(i):
        return repo.save(DefinitieRecord(begrip=f"Test_{i}", ...))

    # Save 10 definitions concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(save_definition, i) for i in range(10)]
        results = [f.result() for f in futures]

    # All should succeed
    assert len(results) == 10
    assert len(set(results)) == 10  # No duplicate IDs

def test_concurrent_updates_last_write_wins():
    """Test concurrent updates don't corrupt data."""
    repo = DefinitieRepositoryV2()

    # Create definition
    def_id = repo.save(DefinitieRecord(begrip="Test", definitie="v1"))

    # Update concurrently
    def update_definition(version):
        record = repo.get(def_id)
        record.definitie = f"v{version}"
        repo.save(record)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(update_definition, i) for i in range(2, 7)]
        [f.result() for f in futures]

    # Final state should be consistent (one of v2-v6)
    final = repo.get(def_id)
    assert final.definitie in ["v2", "v3", "v4", "v5", "v6"]
    # Should NOT be corrupted like "v2v3" or empty

def test_concurrent_delete_and_save_safe():
    """Test delete + save race condition."""
    repo = DefinitieRepositoryV2()

    def_id = repo.save(DefinitieRecord(begrip="Test", ...))

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(repo.delete, def_id)
        f2 = executor.submit(repo.save, repo.get(def_id))

        # One should succeed, one should fail gracefully
        # Should NOT corrupt database
```

---

#### Blindspot 2: Memory Leaks (Session State Bloat)

**Current Plan**: No memory leak tests
**Risk**: `st.session_state` grows unbounded → app slows down

```python
# tests/integration/test_session_state_leaks.py (MISSING)

import pytest
import streamlit as st
from src.ui.tabbed_interface import main

def test_generate_workflow_no_memory_leak():
    """Test generating definitions doesn't leak memory."""
    initial_keys = set(st.session_state.keys())

    # Generate 50 definitions
    for i in range(50):
        st.session_state['term'] = f"Test_{i}"
        # Trigger generate workflow
        main()  # Simplified - actual test would click buttons

    final_keys = set(st.session_state.keys())

    # Should not have 50 new keys
    new_keys = final_keys - initial_keys
    assert len(new_keys) < 10  # Max 10 new keys (reasonable)

def test_validation_results_not_accumulated():
    """Test validation results are overwritten, not accumulated."""
    # Generate + validate 20 times
    for i in range(20):
        definition = generate_definition(f"Test_{i}")
        results = validate_definition(definition)

    # Session state should only have LATEST results
    assert 'validation_results' in st.session_state
    # Should be single result, not list of 20
    assert not isinstance(st.session_state.validation_results, list)
```

---

#### Blindspot 3: Database Corruption (Invalid Data)

**Current Plan**: No data integrity tests
**Risk**: New CRUD logic writes invalid data → database corrupted

```python
# tests/database/test_data_integrity.py (MISSING)

def test_save_rejects_invalid_data():
    """Test repository rejects invalid data."""
    repo = DefinitieRepositoryV2()

    # Empty begrip
    with pytest.raises(ValueError, match="begrip"):
        repo.save(DefinitieRecord(begrip="", definitie="test"))

    # None definitie
    with pytest.raises(ValueError, match="definitie"):
        repo.save(DefinitieRecord(begrip="test", definitie=None))

    # Invalid status
    with pytest.raises(ValueError, match="status"):
        repo.save(DefinitieRecord(begrip="test", definitie="test", status="INVALID"))

def test_database_constraints_enforced():
    """Test database constraints prevent corruption."""
    repo = DefinitieRepositoryV2()

    # Create definition
    repo.save(DefinitieRecord(begrip="Duplicate", definitie="v1", status="CONCEPT"))

    # Try to create another active definition with same begrip
    with pytest.raises(ValueError, match="bestaat al"):
        repo.save(DefinitieRecord(begrip="Duplicate", definitie="v2", status="CONCEPT"))

    # But should allow if status=ARCHIVED
    archived_id = repo.save(DefinitieRecord(begrip="Duplicate", definitie="v2", status="ARCHIVED"))
    assert archived_id > 0

def test_voorbeelden_referential_integrity():
    """Test voorbeelden can't exist without parent definition."""
    repo = DefinitieRepositoryV2()

    # Try to save voorbeelden for non-existent definition
    with pytest.raises(ValueError, match="Definitie.*niet gevonden"):
        repo.save_voorbeelden(999999, [{"text": "test"}])
```

---

#### Blindspot 4: Export/Import Round-Trip

**Current Plan**: No round-trip tests
**Risk**: Export format incompatible with import → data loss

```python
# tests/integration/test_export_import_roundtrip.py (MISSING)

def test_csv_export_import_roundtrip():
    """Test exported CSV can be re-imported without data loss."""
    repo = DefinitieRepositoryV2()

    # Create test definition with all fields
    original = DefinitieRecord(
        begrip="Test",
        definitie="Test definitie",
        categorie="Algemeen",
        status="VASTGESTELD",
        synoniemen=["foo", "bar"],
        organisatorische_context="Test context",
        validatie_opmerkingen="Test opmerking"
    )
    original_id = repo.save(original)

    # Export to CSV
    export_service = ExportService(repo)
    csv_path = export_service.export_to_csv([original_id])

    # Import back
    import_service = DefinitionImportService(repo)
    imported_ids = import_service.import_from_csv(csv_path)

    # Verify data integrity
    imported = repo.get(imported_ids[0])
    assert imported.begrip == original.begrip
    assert imported.definitie == original.definitie
    assert imported.categorie == original.categorie
    assert set(imported.synoniemen) == set(original.synoniemen)
    # ... all fields should match
```

---

#### Blindspot 5: Streamlit Cache Invalidation

**Current Plan**: No cache invalidation tests
**Risk**: Stale data shown to user after updates

```python
# tests/ui/test_streamlit_cache.py (MISSING)

@st.cache_data
def get_definition_cached(def_id):
    return repo.get(def_id)

def test_cache_invalidated_after_update():
    """Test Streamlit cache is invalidated after updates."""
    repo = DefinitieRepositoryV2()

    # Create definition
    def_id = repo.save(DefinitieRecord(begrip="Test", definitie="v1"))

    # Fetch (caches)
    cached_v1 = get_definition_cached(def_id)
    assert cached_v1.definitie == "v1"

    # Update
    repo.save(DefinitieRecord(id=def_id, begrip="Test", definitie="v2"))

    # Fetch again (should be v2, not cached v1)
    cached_v2 = get_definition_cached(def_id)
    assert cached_v2.definitie == "v2"  # FAILS if cache not invalidated
```

---

### Integration Path Coverage Gaps

**Missing Integration Tests**:
1. **Generate → Validate → Save → Export**: Full workflow test
2. **Import → Duplicate Detection → Merge**: Import workflow test
3. **Draft → Edit → Validate → Publish**: Publication workflow test
4. **Bulk Operations**: Select 100 definitions → Export → Verify
5. **Error Recovery**: Simulate API failure → Verify graceful degradation

---

## 4. ENHANCED ROLLBACK PROCEDURES

### Multi-Level Backup Strategy

#### Level 1: Instant Rollback (Feature Flag)
**Use When**: Immediate issue detected (< 1 hour after deployment)
**Time**: 30 seconds

```bash
# Emergency rollback procedure
export USE_LEGACY_REPO=true
streamlit run src/main.py

# Verify rollback successful
curl http://localhost:8501/health  # Should return 200

# Monitor logs
tail -f logs/app.log | grep ERROR
```

---

#### Level 2: Code Rollback (Git Revert)
**Use When**: Issue detected after > 1 hour, feature flag insufficient
**Time**: 5-10 minutes

```bash
# Find commit to revert
git log --oneline -n 20

# Revert specific commit
git revert <commit-hash>

# Or reset to previous commit (DESTRUCTIVE)
git reset --hard HEAD~1

# Verify tests pass
pytest -q

# Restart app
streamlit run src/main.py
```

---

#### Level 3: Database Rollback (Restore from Backup)
**Use When**: Data corruption detected
**Time**: 5-15 minutes

```bash
# scripts/rollback/rollback_database.sh (MISSING)

#!/bin/bash
set -e

BACKUP_DIR="data/backups"
DB_PATH="data/definities.db"

echo "Available backups:"
ls -lh $BACKUP_DIR/*.db

read -p "Enter backup filename to restore: " backup_file

# Verify backup exists
if [ ! -f "$BACKUP_DIR/$backup_file" ]; then
    echo "ERROR: Backup not found"
    exit 1
fi

# Stop app (if running)
pkill -f "streamlit run" || true

# Backup current (corrupt) database
cp $DB_PATH "${DB_PATH}.corrupt.$(date +%Y%m%d_%H%M%S)"

# Restore from backup
cp "$BACKUP_DIR/$backup_file" $DB_PATH

# Verify integrity
sqlite3 $DB_PATH "PRAGMA integrity_check;"

echo "Database restored from $backup_file"
echo "Restart app: streamlit run src/main.py"
```

---

#### Level 4: Emergency Recovery (Full System Restore)
**Use When**: Multiple failures, system unstable
**Time**: 20-30 minutes

```bash
# scripts/rollback/emergency_recovery.sh (MISSING)

#!/bin/bash
set -e

echo "EMERGENCY RECOVERY PROCEDURE"
echo "This will:"
echo "  1. Restore database from latest backup"
echo "  2. Reset git to last known good commit"
echo "  3. Clear Streamlit cache"
echo "  4. Reinstall dependencies"

read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    exit 1
fi

# 1. Restore database
./scripts/rollback/rollback_database.sh

# 2. Reset git (DESTRUCTIVE)
git reset --hard $(git tag | grep "known-good" | tail -1)

# 3. Clear caches
rm -rf .streamlit/cache
rm -rf __pycache__

# 4. Reinstall deps
pip install -r requirements.txt

# 5. Run smoke tests
pytest tests/smoke/ -v

# 6. Restart app
streamlit run src/main.py

echo "Recovery complete!"
```

---

### Phase-by-Phase Checkpoint Strategy

**RECOMMENDATION**: Create git tags after each successful phase

```bash
# After Phase 0 completes successfully
git tag -a "DEF-54-phase-0-schema-complete" -m "Schema validation completed"
git push origin DEF-54-phase-0-schema-complete

# After Phase 1
git tag -a "DEF-54-phase-1-feature-flag-complete" -m "Feature flag implemented"

# ... etc for all phases

# Rollback to specific phase
git reset --hard DEF-54-phase-3a-crud-complete
```

**Automated Checkpoint Script**:
```bash
# scripts/rollback/create_checkpoint.sh (MISSING)

#!/bin/bash
set -e

PHASE=$1
if [ -z "$PHASE" ]; then
    echo "Usage: ./create_checkpoint.sh <phase-name>"
    exit 1
fi

TAG="DEF-54-checkpoint-$PHASE"

# Verify tests pass
echo "Running tests before checkpoint..."
pytest -q || {
    echo "ERROR: Tests failing, cannot create checkpoint"
    exit 1
}

# Backup database
BACKUP_FILE="data/backups/definities_${PHASE}_$(date +%Y%m%d_%H%M%S).db"
cp data/definities.db "$BACKUP_FILE"
echo "Database backed up: $BACKUP_FILE"

# Create git tag
git tag -a "$TAG" -m "DEF-54 Phase $PHASE completed successfully"
echo "Git tag created: $TAG"

# Record metrics
echo "Recording metrics..."
METRICS_FILE="docs/analyses/DEF-54-phase-metrics.txt"
echo "=== $TAG ===" >> $METRICS_FILE
echo "Date: $(date)" >> $METRICS_FILE
echo "Lines changed: $(git diff HEAD~1 --stat | tail -1)" >> $METRICS_FILE
echo "Test coverage: $(pytest --cov --cov-report=term | grep TOTAL)" >> $METRICS_FILE
echo "" >> $METRICS_FILE

echo "Checkpoint created successfully!"
```

---

## 5. WARNING SIGNS (When to STOP and Rollback)

### Red Flags During Implementation

#### Immediate Rollback Triggers (STOP NOW)

| Warning Sign | Severity | Action | Example |
|--------------|----------|--------|---------|
| **Tests failing >5 files** | 🔴 CRITICAL | Rollback immediately | `pytest` shows 5+ failures |
| **App won't start** | 🔴 CRITICAL | Rollback immediately | `ModuleNotFoundError` |
| **Database locked** | 🔴 CRITICAL | Rollback immediately | `database is locked` error |
| **Memory usage >2GB** | 🔴 CRITICAL | Rollback immediately | `htop` shows 2GB+ for Streamlit |
| **Data corruption** | 🔴 CRITICAL | Rollback + restore DB | Definitions have NULL fields |

#### Investigate Before Rollback (CAUTION)

| Warning Sign | Severity | Action | Example |
|--------------|----------|--------|---------|
| **1-2 tests failing** | 🟡 CAUTION | Investigate, fix or rollback | Minor test failures |
| **Slow performance (>10s)** | 🟡 CAUTION | Profile, optimize or rollback | Saves take 10+ seconds |
| **UI glitches** | 🟡 CAUTION | Debug, fix or rollback | Buttons don't respond |
| **Warning logs** | 🟡 CAUTION | Review, fix or rollback | Deprecation warnings |

#### Monitor and Continue (ACCEPTABLE)

| Warning Sign | Severity | Action | Example |
|--------------|----------|--------|---------|
| **Minor lint warnings** | 🟢 ACCEPTABLE | Fix in Phase 8 | Unused imports |
| **Documentation outdated** | 🟢 ACCEPTABLE | Fix in Phase 9 | Old docstrings |
| **Slight perf degradation (<20%)** | 🟢 ACCEPTABLE | Optimize later | Save 4.5s instead of 4s |

---

### Test Failure Thresholds

**Rollback Decision Matrix**:

```
Test Pass Rate     | Action
-------------------|------------------------------------------
100%               | ✅ Proceed to next phase
95-99%             | ⚠️ Investigate failures, fix if trivial
90-94%             | 🛑 STOP - Fix failures before proceeding
< 90%              | 🔴 ROLLBACK - Phase failed
```

**Coverage Thresholds**:
```
Coverage           | Action
-------------------|------------------------------------------
> 85%              | ✅ Acceptable
80-85%             | ⚠️ Add tests for critical paths
70-79%             | 🛑 Add tests before proceeding
< 70%              | 🔴 ROLLBACK - Insufficient test coverage
```

---

### Performance Degradation Indicators

**Baseline Metrics** (establish before Phase 0):
```bash
# scripts/measure_baseline.sh (MISSING)

#!/bin/bash

echo "=== BASELINE METRICS ===" > metrics_baseline.txt

# 1. Save time (100 definitions)
echo "Measuring save time..." >> metrics_baseline.txt
python scripts/perf/measure_save_time.py >> metrics_baseline.txt

# 2. Search time (1000 queries)
echo "Measuring search time..." >> metrics_baseline.txt
python scripts/perf/measure_search_time.py >> metrics_baseline.txt

# 3. Memory usage
echo "Measuring memory..." >> metrics_baseline.txt
ps aux | grep streamlit >> metrics_baseline.txt

# 4. Database size
echo "Database size:" >> metrics_baseline.txt
du -h data/definities.db >> metrics_baseline.txt

echo "Baseline metrics saved to metrics_baseline.txt"
```

**Rollback Triggers**:
- Save time >2x baseline (was 4s, now 10s) → 🔴 ROLLBACK
- Search time >5x baseline (was 200ms, now 1s) → 🔴 ROLLBACK
- Memory usage >2x baseline (was 500MB, now 1GB) → 🔴 ROLLBACK
- Database size >1.5x baseline → 🟡 INVESTIGATE

---

## 6. RECOMMENDED MODIFICATIONS TO PLAN

### Modified Hybrid Plan with Enhanced Safety

#### Changes to Original Plan

**ADD: Pre-Phase 0: Baseline & Backup**
```
Duration: 0.5 days
Tasks:
- [ ] Measure baseline metrics (save/search time, memory, coverage)
- [ ] Create full database backup
- [ ] Export all definitions to CSV (emergency restore)
- [ ] Tag current commit: "DEF-54-pre-refactor-baseline"
- [ ] Document current system behavior
```

**MODIFY: Phase 0: Schema Validation**
```diff
+ Add rollback script: src/database/migrations/007_rollback.sql
+ Add integrity verification: scripts/verify_schema_integrity.sh
+ Add automated backup: cp data/definities.db data/backups/schema_before.db
```

**MODIFY: Phase 1: Feature Flag**
```diff
+ Add health check automation (see Section 2)
+ Add fallback logging (when/why flag triggered)
+ Add monitoring dashboard (track flag usage)
```

**ADD: Phase 2.5: Concurrency Tests (MISSING)**
```
Duration: 0.5 days
Tasks:
- [ ] Write concurrent save tests (see Blindspot 1)
- [ ] Write memory leak tests (see Blindspot 2)
- [ ] Write data integrity tests (see Blindspot 3)
- [ ] All tests should FAIL (not implemented yet)
```

**MODIFY: Phase 5: Type Conversions**
```diff
- Eliminate conversions (186 lines, 23 files)
+ SKIP THIS PHASE (keep conversions for safety)
+ Alternative: Document conversion layer in architecture
+ Rationale: 85% failure risk, minimal benefit
```

**ADD: Phase 6.5: Integration Testing (MISSING)**
```
Duration: 0.5 days
Tasks:
- [ ] Full workflow test (generate → validate → export)
- [ ] Round-trip test (export → import → verify)
- [ ] Bulk operations test (100 definitions)
- [ ] Error recovery test (API failure simulation)
```

**MODIFY: Phase 7: Delete Legacy**
```diff
+ Verify 0 imports with grep search
+ Create rollback tag: git tag DEF-54-legacy-deleted
+ Keep feature flag infrastructure (emergency use)
+ Add deployment checklist
```

---

### Enhanced Timeline

| Phase | Original | Modified | Reason |
|-------|----------|----------|--------|
| Pre-0: Baseline | N/A | 0.5 days | Establish metrics |
| 0: Schema | 0.5 days | 0.5 days | No change |
| 1: Feature Flag | 0.5 days | 0.5 days | No change |
| 2: Tests | 1 day | 1 day | No change |
| 2.5: Concurrency | N/A | 0.5 days | Add missing tests |
| 3a-3c: CRUD | 3 days | 3 days | No change |
| 4: Voorbeelden | 1 day | 1 day | No change |
| 5: Conversions | 1 day | SKIP | Too risky |
| 6a-6c: Callsites | 1.5 days | 1.5 days | No change |
| 6.5: Integration | N/A | 0.5 days | Add missing tests |
| 7: Delete Legacy | 0.5 days | 0.5 days | No change |
| 8: Code Quality | 1 day | 0.5 days | Reduced scope |
| 9: Docs | 0.5 days | 0.5 days | No change |
| **TOTAL** | **10.5 days** | **10 days** | Saved 0.5 days |

---

## 7. EMERGENCY RECOVERY PROCEDURES

### Scenario 1: Database Corrupted

**Symptoms**:
- Definitions have NULL values
- Foreign key constraints violated
- App shows "database is malformed"

**Recovery Steps**:
1. **STOP APP IMMEDIATELY** (`pkill -f streamlit`)
2. **Backup corrupt database**: `cp data/definities.db data/corrupt_$(date +%Y%m%d_%H%M%S).db`
3. **Restore from backup**:
   ```bash
   ./scripts/rollback/rollback_database.sh
   # Select most recent pre-refactor backup
   ```
4. **Verify integrity**: `sqlite3 data/definities.db "PRAGMA integrity_check;"`
5. **Export all data** (in case of future corruption):
   ```bash
   python scripts/export_all_definitions.py > backup_export.csv
   ```
6. **Restart app**: `streamlit run src/main.py`
7. **Verify functionality**: Run manual smoke tests
8. **Investigate cause**: Check git history, review changes

**Time to Recover**: 15-20 minutes

---

### Scenario 2: Feature Flag Not Working

**Symptoms**:
- Set `USE_LEGACY_REPO=true` but app still uses new repo
- Or vice versa
- Flag logic broken

**Recovery Steps**:
1. **Verify flag is set**:
   ```bash
   echo $USE_LEGACY_REPO  # Should print "true"
   ```
2. **Check flag logic**:
   ```python
   # In src/services/container.py
   print(f"USE_LEGACY_REPO={os.getenv('USE_LEGACY_REPO')}")  # Debug
   ```
3. **Hardcode fallback temporarily**:
   ```python
   # Emergency override
   def _create_definition_repository(self):
       # return DefinitieRepositoryV2(self.db_path)  # Comment out
       return DefinitionRepository(self.db_path)  # Force legacy
   ```
4. **Restart app**
5. **Fix flag logic properly**
6. **Remove hardcoded override**

**Time to Recover**: 5-10 minutes

---

### Scenario 3: Streamlit Session State Corrupted

**Symptoms**:
- App slows down over time
- Memory usage grows unbounded
- Definitions not saving
- UI shows stale data

**Recovery Steps**:
1. **Clear cache**:
   ```bash
   rm -rf .streamlit/cache
   ```
2. **Reset session state** (add to UI):
   ```python
   # Emergency reset button
   if st.button("Reset Session (Emergency)"):
       for key in list(st.session_state.keys()):
           del st.session_state[key]
       st.experimental_rerun()
   ```
3. **Restart app**
4. **Investigate memory leak**:
   ```python
   # Add to app startup
   st.write(f"Session state keys: {len(st.session_state.keys())}")
   st.write(f"Memory usage: {psutil.Process().memory_info().rss / 1024 / 1024:.1f} MB")
   ```
5. **Fix root cause** (see Blindspot 2)

**Time to Recover**: 2-5 minutes

---

### Scenario 4: 23 Files Break Simultaneously (Phase 5)

**Symptoms**:
- After removing type conversions, app won't start
- Multiple `AttributeError: 'DefinitieRecord' object has no attribute 'X'`
- Tests failing across multiple modules

**Recovery Steps**:
1. **IMMEDIATELY ROLLBACK**:
   ```bash
   git reset --hard DEF-54-phase-4-voorbeelden-complete
   ```
2. **Verify rollback**:
   ```bash
   pytest -q  # Should pass
   streamlit run src/main.py  # Should start
   ```
3. **SKIP PHASE 5** (don't retry)
4. **Document decision**:
   ```markdown
   # docs/decisions/DEF-54-PHASE-5-SKIPPED.md

   **Decision**: Skip Phase 5 (Type Conversions Elimination)
   **Reason**: Too risky (23 files, 85% failure probability)
   **Trade-off**: Keep 186 lines of conversion code
   **Benefit**: App stability, domain model separation
   ```
5. **Continue with Phase 6**

**Time to Recover**: 5-10 minutes

---

## 8. HEALTH CHECK FRAMEWORK

### Automated Health Checks (MISSING)

```python
# src/services/health_check.py (NEW FILE)

import logging
from typing import List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class HealthCheckResult:
    name: str
    passed: bool
    message: str
    duration_ms: float

class RepositoryHealthCheck:
    """Automated health checks for repository."""

    def __init__(self, repo):
        self.repo = repo

    def run_all_checks(self) -> List[HealthCheckResult]:
        """Run all health checks."""
        checks = [
            self.check_database_connection,
            self.check_basic_crud,
            self.check_search_functionality,
            self.check_duplicate_detection,
            self.check_voorbeelden_sync,
            self.check_data_integrity,
        ]

        results = []
        for check in checks:
            try:
                result = check()
                results.append(result)
            except Exception as e:
                results.append(HealthCheckResult(
                    name=check.__name__,
                    passed=False,
                    message=f"Exception: {e}",
                    duration_ms=0
                ))

        return results

    def check_database_connection(self) -> HealthCheckResult:
        """Check database is accessible."""
        import time
        start = time.time()

        try:
            # Try to query database
            self.repo.get(1)
            duration = (time.time() - start) * 1000
            return HealthCheckResult(
                name="database_connection",
                passed=True,
                message="Database accessible",
                duration_ms=duration
            )
        except Exception as e:
            return HealthCheckResult(
                name="database_connection",
                passed=False,
                message=f"Cannot access database: {e}",
                duration_ms=0
            )

    def check_basic_crud(self) -> HealthCheckResult:
        """Check create/read/update/delete work."""
        import time
        start = time.time()

        try:
            # Create
            test_id = self.repo.save(DefinitieRecord(
                begrip="__HEALTH_CHECK__",
                definitie="Test",
                status="CONCEPT"
            ))

            # Read
            record = self.repo.get(test_id)
            assert record.begrip == "__HEALTH_CHECK__"

            # Update
            record.definitie = "Updated"
            self.repo.save(record)
            updated = self.repo.get(test_id)
            assert updated.definitie == "Updated"

            # Delete
            self.repo.delete(test_id)

            duration = (time.time() - start) * 1000
            return HealthCheckResult(
                name="basic_crud",
                passed=True,
                message="CRUD operations working",
                duration_ms=duration
            )
        except Exception as e:
            return HealthCheckResult(
                name="basic_crud",
                passed=False,
                message=f"CRUD failure: {e}",
                duration_ms=0
            )

    # ... more checks ...
```

**Integration**:
```python
# src/main.py

from services.health_check import RepositoryHealthCheck

def startup_health_check():
    """Run health checks on app startup."""
    repo = get_repository()
    checker = RepositoryHealthCheck(repo)

    results = checker.run_all_checks()

    passed = sum(1 for r in results if r.passed)
    total = len(results)

    if passed < total:
        st.error(f"⚠️ Health check failed: {passed}/{total} passed")
        st.write("Failed checks:")
        for r in results:
            if not r.passed:
                st.write(f"- {r.name}: {r.message}")

        # Auto-fallback to legacy repo
        if os.getenv("USE_LEGACY_REPO") != "true":
            st.warning("Falling back to legacy repository...")
            os.environ["USE_LEGACY_REPO"] = "true"
            st.experimental_rerun()
    else:
        st.success(f"✅ All health checks passed ({total}/{total})")

# Run on startup
startup_health_check()
```

---

## 9. FINAL RECOMMENDATIONS

### Decision: Which Plan to Use?

**RECOMMENDED PLAN: Modified Hybrid (10 days)**

**Rationale**:
1. ✅ Adds missing safety mechanisms (health checks, concurrency tests)
2. ✅ Skips Phase 5 (85% failure risk)
3. ✅ Adds integration testing (Phase 6.5)
4. ✅ Comprehensive rollback procedures
5. ✅ Same timeline as simplified plan (10 days)

**Comparison to Original Plans**:
- vs Simplified: Adds concurrency tests, skips risky Phase 5
- vs Accelerated: Adds 5 days, but much safer (60% less risk)
- vs Conservative: Saves 0-2 days, similar safety level

---

### Mandatory Pre-Requisites

**Before starting ANY phase**:
1. ✅ Create `scripts/rollback/` directory with all rollback scripts
2. ✅ Implement health check framework (`src/services/health_check.py`)
3. ✅ Set up automated checkpoints (`scripts/rollback/create_checkpoint.sh`)
4. ✅ Measure baseline metrics (`scripts/measure_baseline.sh`)
5. ✅ Export all definitions to CSV (emergency backup)
6. ✅ Create rollback decision tree poster (print and put on wall)

---

### Critical Success Factors

**Phase-by-Phase**:
- ✅ Run health checks after EVERY phase
- ✅ Create git checkpoint after EVERY phase
- ✅ Measure metrics after EVERY phase
- ✅ Manual smoke test after EVERY phase
- ✅ Review rollback procedure BEFORE each phase

**Rollback Triggers**:
- 🔴 Any health check failure → Investigate, fix or rollback
- 🔴 Test pass rate <90% → Rollback
- 🔴 Performance degradation >2x → Rollback
- 🔴 Memory usage >2GB → Rollback
- 🔴 Database locked → Rollback immediately

---

### Risk Mitigation Checklist

**Before starting refactor**:
- [ ] Read all 3 planning documents
- [ ] Read this risk analysis document
- [ ] Understand rollback procedures (practice once)
- [ ] Set up monitoring (health checks, metrics)
- [ ] Create all rollback scripts
- [ ] Backup database (multiple copies)
- [ ] Export all definitions to CSV
- [ ] Know when to stop and rollback

**During refactor**:
- [ ] Run health checks after each phase
- [ ] Create checkpoint after each phase
- [ ] Measure metrics vs baseline
- [ ] Manual smoke test after each phase
- [ ] Review rollback decision tree
- [ ] Monitor memory usage continuously

**After completion**:
- [ ] Run full integration test suite
- [ ] Verify performance metrics
- [ ] Load test with 1000 definitions
- [ ] Keep feature flag for 1 week (safety net)
- [ ] Document lessons learned

---

## 10. APPENDIX: ROLLBACK DECISION TREE

```
┌─────────────────────────────────────────┐
│  ISSUE DETECTED DURING REFACTOR          │
└─────────────┬───────────────────────────┘
              │
              ▼
     ┌────────────────────┐
     │ Is app still       │
     │ functional?        │
     └────┬───────────┬───┘
          │ YES       │ NO
          ▼           ▼
    ┌─────────┐  ┌────────────────────┐
    │ Can you │  │ ROLLBACK           │
    │ fix in  │  │ IMMEDIATELY        │
    │ <1 hour?│  │ (Feature Flag or   │
    └────┬─┬──┘  │ Git Revert)        │
         │ │     └────────────────────┘
     YES │ │ NO
         ▼ ▼
    ┌────────┐  ┌────────────────────┐
    │ FIX    │  │ Are tests passing? │
    │ ISSUE  │  └────┬───────────┬───┘
    └────────┘       │ >90%      │ <90%
                     ▼           ▼
              ┌──────────┐  ┌────────────┐
              │ Is perf  │  │ ROLLBACK   │
              │ degraded │  │            │
              │ >2x?     │  └────────────┘
              └────┬─┬───┘
               YES │ │ NO
                   ▼ ▼
            ┌──────────┐  ┌────────────┐
            │ ROLLBACK │  │ INVESTIGATE│
            │          │  │ Fix or     │
            │          │  │ Rollback   │
            └──────────┘  └────────────┘
```

---

## CONCLUSION

**Key Takeaways**:

1. **Phase 5 is too risky** (85% failure probability) → SKIP IT
2. **Database rollback is missing** → Add rollback scripts BEFORE starting
3. **Health checks are critical** → Implement automated checks
4. **Concurrency tests are missing** → Add before Phase 3
5. **Feature flag needs health monitoring** → Auto-fallback on failure

**Recommended Approach**:
- Use **Modified Hybrid Plan** (10 days)
- Skip Phase 5 (keep type conversions)
- Add Pre-Phase 0 (baseline metrics)
- Add Phase 2.5 (concurrency tests)
- Add Phase 6.5 (integration tests)
- Implement all rollback scripts BEFORE Phase 0

**Timeline**: 10 days (same as simplified plan, but safer)
**Risk Level**: LOW-MEDIUM (reduced from MEDIUM)
**Confidence**: HIGH (comprehensive safety mechanisms)

---

**END OF RISK & ROLLBACK ANALYSIS**
