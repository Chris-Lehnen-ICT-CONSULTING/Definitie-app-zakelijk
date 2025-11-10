# Migration 009 Execution Checklist

**Migration**: Remove UNIQUE constraint on definities table
**Date**: 2025-11-10
**Estimated Time**: 10 minutes

---

## Pre-Flight Checklist

### Preparation
- [ ] Read design document: `docs/database/UNIQUE_CONSTRAINT_REMOVAL_DESIGN.md`
- [ ] Read summary: `docs/database/UNIQUE_CONSTRAINT_REMOVAL_SUMMARY.md`
- [ ] Understand rollback procedure

### Environment Check
- [ ] Database exists: `data/definities.db`
- [ ] Backup directory exists: `data/`
- [ ] Migration file exists: `src/database/migrations/009_remove_unique_constraint.sql`
- [ ] Test file exists: `tests/database/test_unique_constraint_removal.py`

---

## Execution Steps

### Step 1: Backup Database
```bash
cp data/definities.db data/definities.db.backup_pre_migration_009
ls -lh data/definities.db.backup_pre_migration_009
```
- [ ] Backup created successfully
- [ ] Backup file size > 0

### Step 2: Verify Current State
```bash
sqlite3 data/definities.db "SELECT name, sql FROM sqlite_master WHERE type='index' AND name='idx_definities_unique_full';"
```
- [ ] Output shows: `idx_definities_unique_full`
- [ ] Index SQL includes: `CREATE UNIQUE INDEX`

### Step 3: Run Pre-Migration Tests
```bash
pytest tests/database/test_unique_constraint_removal.py::TestPreMigration -v
```
- [ ] All tests PASSED
- [ ] Test `test_unique_index_exists` passed
- [ ] Test `test_duplicate_blocked_by_database` passed
- [ ] Test `test_python_check_detects_duplicates` passed

### Step 4: Apply Migration
```bash
sqlite3 data/definities.db < src/database/migrations/009_remove_unique_constraint.sql
```
- [ ] No errors displayed
- [ ] Exit code: 0

### Step 5: Verify Migration Applied
```bash
sqlite3 data/definities.db "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name='idx_definities_unique_full';"
```
- [ ] Output shows: `0`
- [ ] Index removed successfully

### Step 6: Run Post-Migration Tests
```bash
pytest tests/database/test_unique_constraint_removal.py::TestPostMigration -v
```
- [ ] All tests PASSED
- [ ] Test `test_unique_index_removed` passed
- [ ] Test `test_duplicate_allowed_with_flag` passed
- [ ] Test `test_python_guard_still_blocks_without_flag` passed
- [ ] Test `test_find_duplicates_still_works` passed

### Step 7: Run Regression Tests
```bash
pytest tests/services/test_duplicate_detection_service.py -v
pytest tests/services/test_definition_repository.py -v
```
- [ ] All tests PASSED
- [ ] No new failures introduced

### Step 8: Smoke Test via UI
```bash
bash scripts/run_app.sh
```

**Test Scenario**:
1. Create definition: `begrip="test_migration"`, `categorie="ENT"`, context="DJI"
2. Attempt duplicate: Same attributes
3. Expected: Warning dialog shown
4. Click "Create Anyway"
5. Expected: Second definition created successfully

- [ ] Warning dialog shown on duplicate attempt
- [ ] User can override warning
- [ ] Duplicate definition created successfully
- [ ] Both definitions visible in database

---

## Rollback (If Needed)

### Immediate Rollback (No Duplicates)
```bash
cp data/definities.db.backup_pre_migration_009 data/definities.db
sqlite3 data/definities.db "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_definities_unique_full';"
```
- [ ] Backup restored
- [ ] Index exists again

### Delayed Rollback (With Duplicates)
```bash
# Step 1: Preview duplicates
python scripts/cleanup_duplicates.py --preview

# Step 2: Clean up duplicates
python scripts/cleanup_duplicates.py --execute

# Step 3: Apply rollback migration
sqlite3 data/definities.db < src/database/migrations/009_rollback_remove_unique_constraint.sql

# Step 4: Verify
sqlite3 data/definities.db "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_definities_unique_full';"
```
- [ ] Duplicates identified
- [ ] Duplicates archived
- [ ] Rollback migration applied
- [ ] Index restored

---

## Post-Migration Monitoring

### Day 1 (Immediate)
- [ ] No errors in application logs
- [ ] Duplicate creation works as expected
- [ ] Python warnings still functional

### Week 1 (Monitor Daily)
```bash
# Count duplicates created
grep "allow_duplicate=True" logs/app.log | wc -l

# Check duplicate percentage
sqlite3 data/definities.db <<EOF
SELECT
    (SELECT COUNT(*) FROM definities WHERE status != 'archived') as total,
    (SELECT COUNT(*) FROM (
        SELECT begrip, organisatorische_context, COUNT(*) as cnt
        FROM definities WHERE status != 'archived'
        GROUP BY begrip, organisatorische_context, juridische_context, wettelijke_basis, categorie
        HAVING COUNT(*) > 1
    )) as duplicates;
EOF
```
- [ ] Duplicate rate < 5%
- [ ] No user complaints
- [ ] No performance degradation

---

## Sign-Off

### Executed By
- Name: __________________
- Date: __________________
- Time: __________________

### Verified By
- Name: __________________
- Date: __________________
- Time: __________________

### Result
- [ ] ✅ SUCCESS - Migration applied successfully
- [ ] ⚠️ PARTIAL - Issues encountered (describe below)
- [ ] ❌ FAILED - Rolled back (describe below)

### Notes
```
[Add any observations, issues, or deviations from plan]





```

---

## Emergency Contacts

**If issues occur**:
1. Stop application immediately
2. Check logs: `logs/app.log`
3. Restore backup if necessary
4. Document issue in notes above
5. Consult design document for troubleshooting

---

**END OF CHECKLIST**
