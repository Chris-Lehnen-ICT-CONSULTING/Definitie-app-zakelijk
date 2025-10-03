# Rebuild Directory Reorganization - Complete

**Date:** 2025-10-02
**Action:** Consolidated all rebuild-related files into `rebuild/` directory

---

## What Was Done

All files created by the multi-agent rebuild preparation have been moved from project root into the `rebuild/` directory for clean separation.

---

## Directory Structure

```
rebuild/
├── extracted/
│   ├── generation/
│   │   └── prompts/          # 3 prompt templates (SYSTEM, CONTEXT, RULES)
│   └── validation/            # 46 validation rule YAMLs (9 ARAI, 2 CON, 5 ESS, etc.)
│       ├── arai/
│       ├── con/
│       ├── ess/
│       ├── int/
│       ├── sam/
│       ├── str/
│       └── ver/
├── scripts/
│   ├── migration/             # 11 migration scripts
│   │   ├── 1_export_baseline.py
│   │   ├── 2_validate_export.py
│   │   ├── 3_migrate_database.py
│   │   ├── 4_validate_migration.py
│   │   ├── 5_rollback_database.sh
│   │   ├── 6_test_validation_parity.py
│   │   ├── 7_document_validation_rules.py
│   │   ├── 9_run_regression_tests.py
│   │   ├── compare_outputs.py
│   │   ├── validate_shadow_writes.py
│   │   └── final_sync.py
│   ├── extract_rule.py
│   └── create_test_fixtures.py
├── tests/
│   ├── baseline/              # Parity tests (validation, categorization, duplicates)
│   ├── fixtures/              # Pytest fixtures
│   ├── integration/           # Integration tests
│   └── data/                  # Test data (good, bad, edge case definitions)
├── config/
│   ├── validation/            # rule_reasoning_config.yaml
│   ├── ontology/              # category_patterns.yaml
│   ├── toetsregels/           # toetsregels_config.yaml
│   ├── openai_config.yaml
│   ├── cache_config.yaml
│   ├── logging_config.yaml
│   └── config_development.yaml
├── business-logic/            # Extracted business logic
│   └── baseline_42_definitions.json
└── business-logic-extraction/ # Extraction workspace

```

---

## Files Moved

| Category | Count | From → To |
|----------|-------|-----------|
| **Validation Rules** | 46 | `config/validation_rules/` → `rebuild/extracted/validation/` |
| **Migration Scripts** | 11 | `scripts/migration/` → `rebuild/scripts/migration/` |
| **Test Infrastructure** | 10 | `tests/baseline/`, `tests/fixtures/`, etc. → `rebuild/tests/` |
| **Operational Configs** | 9 | `config/` → `rebuild/config/` |

**Total:** 76 files reorganized

---

## Path Updates

All scripts and configs have been updated to use new paths:

**Old Paths:**
- `config/validation_rules/` → **Now:** `rebuild/extracted/validation/`
- `scripts/migration/` → **Now:** `rebuild/scripts/migration/`
- `tests/baseline/` → **Now:** `rebuild/tests/baseline/`
- `config/validation/` → **Now:** `rebuild/config/validation/`

**Updated In:**
- All Python scripts (`.py`)
- All YAML configs (`.yaml`)
- Migration scripts
- Test files

---

## Benefits

✅ **Clean Separation:** All rebuild work isolated in `rebuild/` directory
✅ **Easy to Delete:** Can remove entire `rebuild/` after migration complete
✅ **No Confusion:** Clear distinction between old system and new system
✅ **Self-Contained:** All rebuild assets in one place
✅ **Version Control:** Easy to track rebuild-specific changes

---

## Verification

Run these commands to verify structure:

```bash
# Show structure
tree -L 3 rebuild/

# Count files
find rebuild/extracted/validation -name "*.yaml" | wc -l  # Should be 46
find rebuild/scripts/migration -type f | wc -l            # Should be 11
find rebuild/tests -name "*.py" | wc -l                   # Should be 10+
find rebuild/config -name "*.yaml" | wc -l                # Should be 9+

# Test extraction script still works
python rebuild/scripts/extract_rule.py src/toetsregels/regels/ARAI-02.py
```

---

## What Stayed in Root

These files remain in project root (not rebuild-specific):

- `docker-compose.yml` - Infrastructure for both old and new
- `.env.example` - Environment template
- `scripts/` - General utility scripts (not migration-specific)
- `src/` - Current application code
- `data/` - Database and data files
- `logs/` - Log files
- `tests/` - Main test suite (non-rebuild tests)

---

## Next Steps

1. **Verify paths:** Run tests to ensure all paths work
2. **Start Week 1:** Begin execution with `rebuild/` as workspace
3. **After Rebuild:** Can archive or delete `rebuild/` directory
4. **New System:** Will have its own structure (FastAPI app)

---

**Status:** ✅ COMPLETE
**All rebuild assets now in:** `/Users/chrislehnen/Projecten/Definitie-app/rebuild/`
