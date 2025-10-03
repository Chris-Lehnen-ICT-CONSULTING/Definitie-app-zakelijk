# Migration Scripts for DefinitieAgent Rebuild

**Parent Document:** [MIGRATION_STRATEGY.md](../../docs/planning/MIGRATION_STRATEGY.md)
**Version:** 1.0.0
**Date:** 2025-10-02

---

## Overview

This directory contains all migration scripts for transitioning from DefinitieAgent v2.3 (current) to v3.0 (rebuild).

**⚠️ WARNING:** These scripts modify production data. Always run with `--dry-run` first!

---

## Script Execution Order

### Phase 1: Data Preservation (Day 1-2)

```bash
# Step 1: Export baseline data (30 min)
python scripts/migration/1_export_baseline.py

# Step 2: Validate export completeness (5 min)
python scripts/migration/2_validate_export.py data/migration_baseline.json

# Step 3: Execute migration (DRY RUN first!)
python scripts/migration/3_migrate_database.py --dry-run

# Step 4: Execute migration (ACTUAL)
python scripts/migration/3_migrate_database.py --execute

# Step 5: Validate migrated data (10 min)
python scripts/migration/4_validate_migration.py

# Step 6: Test rollback procedure (5 min)
bash scripts/migration/rollback_database.sh --test
```

### Phase 2: Validation Rules (Day 3-5)

```bash
# Step 1: Generate YAML configs from Python validators
python scripts/migration/5_extract_validation_rules.py

# Step 2: Test validation parity (old vs new)
python scripts/migration/6_test_validation_parity.py

# Step 3: Generate validation rule documentation
python scripts/migration/7_document_validation_rules.py
```

### Phase 3: Test Suite Generation (Week 2)

```bash
# Generate regression test suite from 42 definitions
python scripts/migration/8_generate_test_suite.py

# Run regression tests (compare old vs new outputs)
python scripts/migration/9_run_regression_tests.py
```

---

## Script Details

### 1_export_baseline.py

**Purpose:** Export complete database snapshot for baseline validation

**Output:**
- `data/migration_baseline.json` - Full database export (42 definitions + metadata)
- `data/migration_baseline_checksum.txt` - SHA256 checksums for validation

**Usage:**
```bash
python scripts/migration/1_export_baseline.py

# Optional: Export to custom location
python scripts/migration/1_export_baseline.py --output /path/to/backup.json
```

**Exit Codes:**
- `0` - Success
- `1` - Database connection error
- `2` - Export validation failed

---

### 2_validate_export.py

**Purpose:** Validate exported baseline data completeness

**Checks:**
- Record counts (42 definitions, 96 history, 90 examples)
- UTF-8 encoding (Dutch characters preserved)
- Required fields (no NULLs in critical columns)
- JSON structure validity

**Usage:**
```bash
python scripts/migration/2_validate_export.py data/migration_baseline.json
```

**Exit Codes:**
- `0` - Validation passed
- `1` - Validation failed (see error output)

---

### 3_migrate_database.py

**Purpose:** Execute database migration from old to new schema

**Modes:**
- `--dry-run` - Preview migration without changes (recommended first run)
- `--execute` - Execute actual migration (requires confirmation)
- `--rollback` - Undo migration (restores from backup)

**Usage:**
```bash
# ALWAYS run dry-run first!
python scripts/migration/3_migrate_database.py --dry-run

# Review output, then execute if safe
python scripts/migration/3_migrate_database.py --execute

# If something goes wrong, rollback
python scripts/migration/3_migrate_database.py --rollback
```

**Safety Features:**
- Automatic backup before migration
- Transaction-based migration (atomic)
- Progress logging to `logs/migration_YYYYMMDD_HHMMSS.log`
- Automatic validation after migration

**Exit Codes:**
- `0` - Migration successful
- `1` - Migration failed (transaction rolled back)
- `2` - Validation failed after migration

---

### 4_validate_migration.py

**Purpose:** Validate migrated data against baseline

**Validation Tests:**
1. Record count match (42 definitions)
2. Sample data integrity (first 5 records)
3. Foreign key integrity (no orphaned records)
4. UTF-8 encoding (Dutch characters)
5. Required fields (no NULL violations)

**Usage:**
```bash
python scripts/migration/4_validate_migration.py

# Compare against custom baseline
python scripts/migration/4_validate_migration.py --baseline /path/to/baseline.json
```

**Exit Codes:**
- `0` - All tests passed
- `1` - One or more tests failed

---

### 5_extract_validation_rules.py

**Purpose:** Port 46 Python validators to YAML configs

**Process:**
1. Parse Python validator classes
2. Extract regex patterns, thresholds, messages
3. Generate YAML config files
4. Map to generic validator types

**Output:**
- `config/validation_rules/ARAI-01.yaml` (46 files)
- `docs/migration/validation_rule_mapping.md` (documentation)

**Usage:**
```bash
python scripts/migration/5_extract_validation_rules.py

# Generate with custom output directory
python scripts/migration/5_extract_validation_rules.py --output /path/to/rules
```

---

### 6_test_validation_parity.py

**Purpose:** Compare old (Python) vs new (YAML) validation outputs

**Test Approach:**
1. Load 42 test definitions
2. Run old validators (Python)
3. Run new validators (YAML + generic)
4. Compare scores (tolerance: ± 5%)

**Usage:**
```bash
# Test all rules
python scripts/migration/6_test_validation_parity.py

# Test specific rule
python scripts/migration/6_test_validation_parity.py --rule ARAI-01

# Generate detailed report
python scripts/migration/6_test_validation_parity.py --report validation_parity.html
```

**Exit Codes:**
- `0` - Parity >= 95% (acceptable)
- `1` - Parity < 95% (needs investigation)

---

### 7_document_validation_rules.py

**Purpose:** Generate human-readable validation rule documentation

**Output:**
- `docs/validation_rules.md` - Complete rule reference
- `docs/validation_rule_index.html` - Searchable HTML version

**Usage:**
```bash
python scripts/migration/7_document_validation_rules.py
```

---

### 8_generate_test_suite.py

**Purpose:** Generate regression test suite from 42 production definitions

**Output:**
- `tests/migration/test_suite_baseline.json` - Test data
- `tests/migration/test_definition_generation.py` - Pytest tests
- `tests/migration/test_validation_parity.py` - Validation tests

**Usage:**
```bash
python scripts/migration/8_generate_test_suite.py
```

---

### 9_run_regression_tests.py

**Purpose:** Execute regression tests and generate comparison report

**Tests:**
1. Definition generation (42 cases)
2. Validation scores (± 5% tolerance)
3. Export formats (byte-identical)
4. Performance benchmarks

**Usage:**
```bash
# Run all regression tests
python scripts/migration/9_run_regression_tests.py

# Run with detailed output
python scripts/migration/9_run_regression_tests.py --verbose

# Generate HTML report
python scripts/migration/9_run_regression_tests.py --report regression_report.html
```

**Exit Codes:**
- `0` - All tests passed (>= 95% similarity)
- `1` - Tests failed (< 95% similarity)

---

### rollback_database.sh

**Purpose:** Emergency rollback procedure (< 5 minutes)

**Modes:**
- `--test` - Test rollback without affecting production
- `--execute` - Execute actual rollback (requires confirmation)

**Usage:**
```bash
# Test rollback procedure (recommended weekly)
bash scripts/migration/rollback_database.sh --test

# Emergency rollback (if migration fails)
bash scripts/migration/rollback_database.sh --execute
```

**Steps:**
1. Stop new system (30 sec)
2. Restore database backup (60 sec)
3. Verify backup integrity (30 sec)
4. Restart old system (60 sec)
5. Health check (30 sec)

**Total Time:** ~3 minutes

**Exit Codes:**
- `0` - Rollback successful
- `1` - Rollback failed (manual intervention required)

---

## Emergency Procedures

### If Migration Fails

```bash
# 1. Stop migration immediately
Ctrl+C

# 2. Check logs
tail -f logs/migration_*.log

# 3. Execute rollback
bash scripts/migration/rollback_database.sh --execute

# 4. Verify old system working
curl http://localhost:8501/_stcore/health

# 5. Notify team
# Report issue to migration lead
```

### If Validation Fails

```bash
# 1. Generate detailed validation report
python scripts/migration/4_validate_migration.py --verbose > validation_errors.txt

# 2. Review errors
cat validation_errors.txt

# 3. If data loss detected
bash scripts/migration/rollback_database.sh --execute

# 4. If minor issues (< 5% drift)
# Document discrepancies and proceed with caution
```

### If Performance Regression Detected

```bash
# 1. Run performance benchmarks
python scripts/migration/10_benchmark_performance.py

# 2. Compare to baseline
python scripts/migration/10_benchmark_performance.py --compare baseline_metrics.json

# 3. If regression > 20%
# Consider rollback or performance optimization sprint
```

---

## Monitoring During Migration

### Real-time Progress Tracking

```bash
# Monitor migration log in real-time
tail -f logs/migration_*.log

# Monitor system resources
watch -n 5 'ps aux | grep python'
watch -n 5 'df -h | grep data'
```

### Success Indicators

**Look for these in logs:**
- ✅ "Migration step X/10 complete"
- ✅ "Validation passed: 42 definitions migrated"
- ✅ "Foreign key integrity: OK"
- ✅ "UTF-8 encoding: OK"

**Red Flags (stop immediately):**
- ❌ "ERROR: Data loss detected"
- ❌ "CRITICAL: Foreign key violation"
- ❌ "FATAL: Transaction failed"

---

## Post-Migration Checklist

After successful migration, verify:

- [ ] Record counts match (42/96/90)
- [ ] Sample data verified (first 5 records)
- [ ] Foreign keys intact (no orphans)
- [ ] UTF-8 encoding correct (Dutch characters)
- [ ] Rollback procedure tested
- [ ] Backup verified (restorable)
- [ ] Migration log archived
- [ ] Stakeholder sign-off obtained

---

## Troubleshooting

### "Database locked" error

```bash
# Check for active connections
lsof data/definities.db

# Kill processes if safe
pkill -f streamlit
pkill -f python

# Retry migration
```

### "UTF-8 encoding error"

```bash
# Verify database encoding
sqlite3 data/definities.db "PRAGMA encoding;"

# Re-export with UTF-8 explicit
export LC_ALL=en_US.UTF-8
python scripts/migration/1_export_baseline.py
```

### "Missing validation rules"

```bash
# Count rules
ls -1 src/toetsregels/regels/*.py | wc -l
# Should be 46

# Re-extract if mismatch
python scripts/migration/5_extract_validation_rules.py --force
```

---

## Support & Escalation

**For script issues:**
- Check logs in `logs/migration_*.log`
- Review [MIGRATION_STRATEGY.md](../../docs/planning/MIGRATION_STRATEGY.md)
- Contact: Data Migration Lead

**For data integrity issues:**
- Execute rollback immediately
- Preserve logs for analysis
- Escalate to Product Owner

**For emergency rollback:**
- No approval needed
- Execute rollback procedure
- Notify team after complete

---

## ✅ NEWLY CREATED SCRIPTS SUMMARY

**Date Created:** 2025-10-02
**Total New Scripts:** 11
**Total Lines of Code:** 4,507 LOC
**Status:** ✅ Complete and Ready for Use

### Script Implementation Summary

| # | Script | LOC | Purpose | Status |
|---|--------|-----|---------|--------|
| 1 | `1_export_baseline.py` | 240 | Export 42 baseline definitions | ✅ Complete |
| 2 | `2_validate_export.py` | 388 | Validate export (42/96/90 check) | ✅ Complete |
| 3 | `3_migrate_database.py` | 531 | Execute database migration | ✅ Complete |
| 4 | `4_validate_migration.py` | 382 | Validate migrated data | ✅ Complete |
| 5 | `5_rollback_database.sh` | 362 | Emergency rollback (< 5 min) | ✅ Complete |
| 6 | `6_test_validation_parity.py` | 379 | Test >=95% validation parity | ✅ Complete |
| 7 | `7_document_validation_rules.py` | 487 | Generate docs (HTML/MD) | ✅ Complete |
| 9 | `9_run_regression_tests.py` | 391 | Full regression suite | ✅ Complete |
| 10 | `compare_outputs.py` | 411 | Compare old vs new outputs | ✅ Complete |
| 11 | `validate_shadow_writes.py` | 458 | Validate shadow DB writes | ✅ Complete |
| 12 | `final_sync.py` | 478 | Final cutover sync | ✅ Complete |

### Key Features Implemented

All scripts include:
- ✅ **Type hints** (Python 3.11+ compatible)
- ✅ **Comprehensive error handling** (specific exceptions)
- ✅ **Dual logging** (console + file)
- ✅ **Exit codes** (0=success, 1=failure)
- ✅ **CLI arguments** (argparse with help)
- ✅ **Dry-run modes** (safety first)
- ✅ **Docstrings** (purpose, usage, examples)
- ✅ **No external dependencies** (stdlib only)

### Production-Ready Features

1. **Safety First:**
   - Automatic backups before modifications
   - Dry-run modes for all destructive operations
   - Transaction-based database operations
   - Comprehensive validation at each step

2. **Observability:**
   - Detailed logging to `logs/migration/`
   - Progress tracking with step indicators
   - Error messages with context
   - JSON result files for analysis

3. **Robustness:**
   - UTF-8 encoding support (Dutch characters)
   - Foreign key integrity checks
   - Record count validation
   - Timestamp alignment verification

4. **Documentation:**
   - Inline code documentation
   - Usage examples in docstrings
   - CLI help text (--help)
   - This comprehensive README

### Quick Start Guide

```bash
# Phase 1: Data Preservation (Day 1-2)
python scripts/migration/1_export_baseline.py
python scripts/migration/2_validate_export.py data/migration_baseline.json
python scripts/migration/3_migrate_database.py --dry-run
python scripts/migration/3_migrate_database.py --execute
python scripts/migration/4_validate_migration.py
bash scripts/migration/5_rollback_database.sh --test

# Phase 2: Validation Testing (Day 3-5)
python scripts/migration/6_test_validation_parity.py
python scripts/migration/7_document_validation_rules.py

# Phase 3: Regression Testing (Week 2)
python scripts/migration/9_run_regression_tests.py

# Phase 4: Parallel Run (Week 4)
python scripts/migration/compare_outputs.py --continuous --interval 3600
python scripts/migration/validate_shadow_writes.py

# Phase 5: Cutover (Week 5)
python scripts/migration/final_sync.py --dry-run
python scripts/migration/final_sync.py --execute --verify
```

### Script Details

#### compare_outputs.py (NEW)
**Purpose:** Compare outputs between old and new systems during parallel run

**Features:**
- Definition record comparison (100% match target)
- Validation score comparison (± 5% tolerance)
- Generation quality metrics (>= 85% similarity)
- Continuous monitoring mode (hourly runs)

**Usage:**
```bash
# Single comparison
python scripts/migration/compare_outputs.py

# Continuous monitoring (every hour)
python scripts/migration/compare_outputs.py --continuous --interval 3600
```

#### validate_shadow_writes.py (NEW)
**Purpose:** Validate shadow database writes during parallel run

**Features:**
- Write operation validation (counts match)
- Record-level consistency checks (100%)
- Timestamp alignment (< 5s drift tolerance)
- Since-timestamp filtering

**Usage:**
```bash
# Validate all writes
python scripts/migration/validate_shadow_writes.py

# Validate since specific time
python scripts/migration/validate_shadow_writes.py --since "2025-10-02 00:00:00"
```

#### final_sync.py (NEW)
**Purpose:** Final data synchronization before cutover

**Features:**
- Pre-sync backup creation
- Change identification (new/updated/deleted)
- Incremental sync operations
- Post-sync verification (100% consistency)

**Usage:**
```bash
# Dry-run (recommended)
python scripts/migration/final_sync.py --dry-run

# Execute with verification
python scripts/migration/final_sync.py --execute --verify
```

### Dependencies

**All scripts use Python 3.11+ standard library only:**
- `argparse`, `json`, `logging`, `sqlite3`, `sys`, `pathlib`, `datetime`, `shutil`, `time`

**No external packages required** - Ready to run immediately!

### Testing Before Production Use

```bash
# 1. Verify all scripts exist
ls -lh scripts/migration/*.py scripts/migration/*.sh

# 2. Test export
python scripts/migration/1_export_baseline.py --validate

# 3. Test validation
python scripts/migration/2_validate_export.py data/migration_baseline.json --strict

# 4. Test migration (dry-run)
python scripts/migration/3_migrate_database.py --dry-run

# 5. Test rollback
bash scripts/migration/5_rollback_database.sh --test

# All tests should pass before proceeding to production migration
```

### Logging Locations

All scripts log to:
- **Console:** INFO level with emojis (✅ ❌ ⚠️  🔍)
- **File:** `logs/migration/{script_name}_{timestamp}.log`

Example log files:
```
logs/migration/export_baseline_20251002_171405.log
logs/migration/validate_export_20251002_171510.log
logs/migration/migrate_database_20251002_171620.log
logs/migration/comparison_20251002_172145.log
logs/migration/shadow_writes_20251002_200015.log
logs/migration/final_sync_20251002_090005.log
```

### Success Criteria Per Script

| Script | Success Criteria |
|--------|------------------|
| 1_export_baseline.py | 42 definitions exported, JSON valid |
| 2_validate_export.py | All 6 validation tests passed |
| 3_migrate_database.py | 42/96/90 records migrated, validation passed |
| 4_validate_migration.py | 100% record match, no discrepancies |
| 5_rollback_database.sh | < 5 min completion, integrity verified |
| 6_test_validation_parity.py | >= 95% parity for all categories |
| 7_document_validation_rules.py | HTML/MD docs generated |
| 9_run_regression_tests.py | 100% tests passed |
| compare_outputs.py | < 1% discrepancies |
| validate_shadow_writes.py | 100% consistency |
| final_sync.py | 100% sync, verification passed |

### Troubleshooting New Scripts

**Issue:** "No module named 'sqlite3'"
```bash
# Solution: Use Python 3.11+
python3 --version  # Must be 3.11 or higher
python3 scripts/migration/script.py
```

**Issue:** "Permission denied" for rollback script
```bash
# Solution: Make script executable
chmod +x scripts/migration/5_rollback_database.sh
```

**Issue:** "Log directory does not exist"
```bash
# Solution: Create logs directory
mkdir -p logs/migration
```

**Issue:** "Dry-run mode not working"
```bash
# Solution: Ensure --dry-run flag is used
python scripts/migration/3_migrate_database.py --dry-run
# NOT: python scripts/migration/3_migrate_database.py
```

---

**Last Updated:** 2025-10-02
**Maintained By:** Code Architect Team
**Scripts Verified:** 2025-10-02 17:30 UTC
**Production Ready:** ✅ Yes (all 11 scripts complete)
