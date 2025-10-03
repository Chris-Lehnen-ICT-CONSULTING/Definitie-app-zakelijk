# REBUILD_PACKAGE Inventory & Readiness Report

**Generated:** 2025-10-02
**Package Version:** 2.0
**Analysis Scope:** scripts/, templates/, config/ directories + Week 1-2 requirements

---

## Executive Summary

### Current State
- **Documentation:** ✅ COMPLETE (18 docs + 130 requirements)
- **Scripts:** ❌ EMPTY (only .gitkeep)
- **Templates:** ❌ EMPTY (only .gitkeep)
- **Config:** ❌ EMPTY (only .gitkeep)

### Week 1-2 Readiness
- **Week 1 (Business Logic Extraction):** ⚠️ 40% READY
- **Week 2 (Modern Stack Setup):** ❌ 10% READY

### Critical Gaps
- **15 migration scripts MISSING** (required for execution)
- **3 core extraction scripts MISSING** (Day 1 blockers)
- **5+ validation config templates MISSING**
- **Prompt templates defined but NOT CREATED**

---

## Part 1: Referenced But Missing Scripts

### 🔴 CRITICAL - Week 1 Execution Scripts (Day 1 Blockers)

| Script | Referenced In | First Use | Priority |
|--------|--------------|-----------|----------|
| `rebuild/scripts/extract_rule.py` | REBUILD_EXECUTION_PLAN.md:314 | Day 1, 11:00 AM | **P0** |
| `rebuild/scripts/create_test_fixtures.py` | REBUILD_EXECUTION_PLAN.md:1339 | Day 4, 13:00 PM | **P0** |
| `scripts/validate_week1.sh` | GETTING_STARTED.md:355 | Day 5 (Gate 1) | **P0** |

**Impact:** Cannot start Week 1 execution without these scripts.

### 🟠 HIGH - Migration Scripts (Week 2-5 Required)

| Script | Referenced In | Purpose | Week |
|--------|--------------|---------|------|
| `scripts/migration/1_export_baseline.py` | MIGRATION_CHECKLIST.md:73 | Export 42 baseline definitions | W1 |
| `scripts/migration/2_validate_export.py` | MIGRATION_CHECKLIST.md:79 | Validate export completeness | W1 |
| `scripts/migration/3_migrate_database.py` | MIGRATION_CHECKLIST.md:93 | Execute database migration | W1 |
| `scripts/migration/4_validate_migration.py` | MIGRATION_CHECKLIST.md:120 | Validate migrated data | W1 |
| `scripts/migration/rollback_database.sh` | MIGRATION_CHECKLIST.md:155 | Emergency rollback | W1-5 |
| `scripts/migration/6_test_validation_parity.py` | MIGRATION_CHECKLIST.md:306 | Test rule parity (>=95%) | W1 |
| `scripts/migration/7_document_validation_rules.py` | MIGRATION_CHECKLIST.md:377 | Generate rule docs | W1 |
| `scripts/migration/9_run_regression_tests.py` | MIGRATION_CHECKLIST.md:452 | Regression testing | W2 |
| `scripts/migration/compare_outputs.py` | MIGRATION_CHECKLIST.md:508 | Compare old vs new | W4 |
| `scripts/migration/validate_shadow_writes.py` | MIGRATION_CHECKLIST.md:537 | Validate shadow DB | W4 |
| `scripts/migration/final_sync.py` | MIGRATION_CHECKLIST.md:629 | Final data sync | W5 |

**Impact:** Migration workflow completely blocked.

### 🟡 MEDIUM - Supporting Scripts

| Script | Referenced In | Purpose | Week |
|--------|--------------|---------|------|
| `scripts/migrate_data.py` | MODERN_REBUILD_ARCHITECTURE.md:1503 | Main data migration | W2 |
| `scripts/test_mvp.sh` | GETTING_STARTED.md:385 | MVP validation | W4 |
| `scripts/backup_restore.py` | verification_results.json:107 | Backup/restore util | Any |
| `scripts/archive_data.py` | verification_results.json:204 | Archive old data | W6 |

---

## Part 2: Referenced But Missing Templates

### 🔴 CRITICAL - Prompt Templates (Week 1 Day 3 Required)

| Template | Referenced In | Purpose | Day Needed |
|----------|--------------|---------|------------|
| `rebuild/extracted/generation/prompts/SYSTEM_PROMPT.md` | REBUILD_EXECUTION_PLAN.md:984 | AI system role definition | Day 3 |
| `rebuild/extracted/generation/prompts/CONTEXT_TEMPLATE.md` | REBUILD_EXECUTION_PLAN.md:1045 | Context injection template | Day 3 |
| `rebuild/extracted/generation/prompts/RULES_INJECTION.md` | REBUILD_EXECUTION_PLAN.md:1100 | Validation rules for AI | Day 3 |

**Status:** Templates are DOCUMENTED in REBUILD_EXECUTION_PLAN.md but NOT CREATED as files.

### 🟠 HIGH - Configuration Templates

| Template | Location | Purpose | Week |
|----------|----------|---------|------|
| Validation Rule YAML Template | REBUILD_APPENDICES.md:207-428 | Rule extraction template | W1 |
| `.env.example` | REBUILD_APPENDICES.md:432-617 | Environment config | W2 |
| `docker-compose.prod.yml` | REBUILD_APPENDICES.md:621-708 | Production deployment | W9 |

**Status:** Templates are DOCUMENTED but NOT CREATED as files.

### 🟡 MEDIUM - Architecture Templates

Referenced in requirements/PROJECT_INDEX.md:141-143:
- Enterprise Architecture Template
- Solution Architecture Template
- Technical Architecture Template

**Status:** May exist in requirements/architectuur/templates/ (outside package scope).

---

## Part 3: Missing Config Files

### 🔴 CRITICAL - Validation Rule Configs (Week 1 Required)

The documentation expects **46 YAML validation rule configs** in `config/validation_rules/{category}/`:

**Expected structure:**
```
config/validation_rules/
  arai/
    ARAI-01.yaml  # Template in APPENDICES.md:207-428
    ARAI-02.yaml
    ... (9 total)
  con/
    CON-01.yaml
    CON-02.yaml
  ess/
    ESS-01.yaml
    ... (5 total)
  int/
    INT-01.yaml
    ... (10 total)
  sam/
    SAM-01.yaml
    ... (8 total)
  str/
    STR-01.yaml
    ... (9 total)
  ver/
    VER-01.yaml
    ... (3 total)
```

**Current state:** Directory doesn't exist. Only `.gitkeep` in config/

**Referenced in:**
- REBUILD_EXECUTION_PLAN.md (Week 1 Day 1-2)
- REBUILD_APPENDICES.md (Complete template B.1)
- MIGRATION_STRATEGY.md:416

### 🟠 HIGH - Operational Configs

| Config | Referenced In | Purpose |
|--------|--------------|---------|
| `config/validation/rule_reasoning_config.yaml` | hardcoded_logic_extraction_quick_ref.md:55 | Rule reasoning patterns |
| `config/ontology/category_patterns.yaml` | hardcoded_logic_extraction_quick_ref.md:64 | Ontological patterns |
| `config/web_lookup_defaults.yaml` | REQ-040.md:19, REQ-021.md:19 | Web lookup settings |
| `config/toetsregels/toetsregels_config.yaml` | REQ-030.md:19 | Validation rules config |
| `config/config_development.yaml` | REQ-002.md:19 | Dev environment |
| `config/logging_config.yaml` | REQ-058.md:19 | Logging setup |
| `config/openai_config.yaml` | TRACEABILITY-MATRIX-COMPLETE.md:99 | AI service config |
| `config/cache_config.yaml` | TRACEABILITY-MATRIX-COMPLETE.md:192 | Cache settings |
| `config/approval_gate.yaml` | REQ-097.md:98 | Approval gate policy |

**Current state:** ALL MISSING. Only `.gitkeep` in config/

---

## Part 4: Week 1 Readiness Assessment

### Week 1 Schedule (5 days, 40 hours)

| Day | Tasks | Required Assets | Status |
|-----|-------|----------------|--------|
| **Day 1** | ARAI rules extraction | `extract_rule.py`, YAML template | ❌ BLOCKED |
| **Day 2** | Complete rule extraction (46 rules) | Same as Day 1 | ❌ BLOCKED |
| **Day 3** | Generation workflow + prompts | Prompt templates | ⚠️ PARTIAL |
| **Day 4** | Baseline export + test fixtures | `create_test_fixtures.py` | ❌ BLOCKED |
| **Day 5** | Validation + Week 1 Gate | `validate_week1.sh` | ❌ BLOCKED |

### Detailed Blockers

#### Day 1 (09:00 AM Start)
**09:30 Task:** Extract ARAI-01 rule using `extract_rule.py`
- **Status:** ❌ Script doesn't exist
- **Impact:** Cannot start extraction workflow
- **Workaround:** Manual extraction (slow, error-prone)

**11:00 Task:** Extract all ARAI rules (9 rules)
```bash
for rule in src/toetsregels/regels/ARAI-*.py; do
    python rebuild/scripts/extract_rule.py "$rule"
done
```
- **Status:** ❌ Script doesn't exist
- **Impact:** 9 rules × 30 min manual = 4.5 hours delay

#### Day 3 (Prompt Templates)
**Morning Task:** Extract prompt templates
- SYSTEM_PROMPT.md: ✅ Template defined in EXECUTION_PLAN.md:984-1043
- CONTEXT_TEMPLATE.md: ✅ Template defined in EXECUTION_PLAN.md:1045-1098
- RULES_INJECTION.md: ✅ Template defined in EXECUTION_PLAN.md:1100-1137

**Status:** ⚠️ Can manually create from docs, but expected to be pre-populated.

#### Day 4 (Test Fixtures)
**13:00 Task:** Create pytest fixtures
```bash
python rebuild/scripts/create_test_fixtures.py
```
- **Status:** ❌ Script doesn't exist
- **Impact:** Must manually write 200+ LOC fixture code

#### Day 5 (Gate 1 Validation)
**15:00 Task:** Week 1 validation gate
```bash
bash scripts/validate_week1.sh
```
- **Status:** ❌ Script doesn't exist
- **Impact:** Manual validation = 2+ hours

### Week 1 Readiness: 40% ✅ 60% ❌

**Can proceed:** Documentation, templates (copy from docs)
**Cannot proceed:** Automated extraction, automated validation

---

## Part 5: Week 2 Readiness Assessment

### Week 2 Schedule (5 days, 40 hours)

| Day | Tasks | Required Assets | Status |
|-----|-------|----------------|--------|
| **Day 1** | Docker + FastAPI setup | docker-compose templates | ⚠️ PARTIAL |
| **Day 2** | Database models + migrations | `.env.example` | ❌ BLOCKED |
| **Day 3** | CI/CD pipeline | GitHub Actions workflow | ⚠️ CAN CREATE |
| **Day 4** | Redis cache | `cache_config.yaml` | ❌ BLOCKED |
| **Day 5** | API skeleton | Environment configs | ❌ BLOCKED |

### Detailed Blockers

#### Day 1 (Docker Setup)
**Needs:**
- `docker-compose.yml` (development)
- `docker-compose.prod.yml` (template in APPENDICES.md:621-708)
- `Dockerfile` (for API)
- `Dockerfile.streamlit` (for UI)

**Status:** ⚠️ Templates documented, but not created

#### Day 2 (Database)
**Needs:**
- `.env.example` (template in APPENDICES.md:432-617)
- Database connection strings
- Migration configs

**Status:** ❌ BLOCKED - No .env.example file

#### Day 4 (Redis Cache)
**Needs:**
- `config/cache_config.yaml`
- Redis connection settings

**Status:** ❌ BLOCKED - Config missing

### Week 2 Readiness: 10% ✅ 90% ❌

**Major blocker:** No environment configuration templates created.

---

## Part 6: Prioritized Creation List

### 🚨 P0 - Week 1 Day 1 Blockers (Create First)

1. **`rebuild/scripts/extract_rule.py`** (~200 LOC)
   - Purpose: Extract validation rule from Python to YAML
   - Template: REBUILD_EXECUTION_PLAN.md:314-412
   - Effort: 2 hours
   - Blocks: Day 1 morning tasks

2. **`config/validation_rules/` structure + ARAI-01.yaml example**
   - Purpose: Provide template for rule extraction
   - Template: REBUILD_APPENDICES.md:207-428
   - Effort: 1 hour (create structure + 1 example)
   - Blocks: Day 1 afternoon tasks

3. **Prompt templates** (3 files)
   - `rebuild/extracted/generation/prompts/SYSTEM_PROMPT.md`
   - `rebuild/extracted/generation/prompts/CONTEXT_TEMPLATE.md`
   - `rebuild/extracted/generation/prompts/RULES_INJECTION.md`
   - Template: REBUILD_EXECUTION_PLAN.md:984-1137
   - Effort: 30 minutes (copy from docs)
   - Blocks: Day 3 tasks

### 🔥 P1 - Week 1 Completion (Days 4-5)

4. **`rebuild/scripts/create_test_fixtures.py`** (~100 LOC)
   - Template: REBUILD_EXECUTION_PLAN.md:1339-1410
   - Effort: 1.5 hours
   - Blocks: Day 4 afternoon

5. **`scripts/validate_week1.sh`** (~50 LOC)
   - Template: GETTING_STARTED.md:355-377
   - Effort: 30 minutes
   - Blocks: Day 5 Gate 1

### ⚡ P2 - Week 1 Migration Scripts (Parallel Track)

6. **Migration script suite** (11 scripts, ~1200 LOC total)
   - All scripts in `scripts/migration/` directory
   - Templates: MIGRATION_CHECKLIST.md
   - Effort: 8-12 hours (can parallelize)
   - Blocks: Migration workflow (runs parallel to rebuild)

### 🔧 P3 - Week 2 Infrastructure (Create During Week 1)

7. **`.env.example`** (environment template)
   - Template: REBUILD_APPENDICES.md:432-617
   - Effort: 30 minutes
   - Blocks: Week 2 Day 2

8. **`docker-compose.yml`** (development)
   - Create from docker-compose.prod.yml template
   - Effort: 1 hour
   - Blocks: Week 2 Day 1

9. **Config files** (9 YAML configs)
   - All in `config/` directory
   - Effort: 2-3 hours total
   - Blocks: Week 2 Days 2-5

---

## Part 7: Recommended Action Plan

### Immediate Actions (Before Week 1 Start)

**Day -1 (Preparation Day):**

**Morning (4 hours):**
1. ✅ Create `rebuild/scripts/extract_rule.py` (2h)
2. ✅ Create `config/validation_rules/` structure (30min)
3. ✅ Create ARAI-01.yaml example (30min)
4. ✅ Create 3 prompt templates (30min)
5. ✅ Test extraction script with ARAI-01 (30min)

**Afternoon (4 hours):**
6. ✅ Create `rebuild/scripts/create_test_fixtures.py` (1.5h)
7. ✅ Create `scripts/validate_week1.sh` (30min)
8. ✅ Create `.env.example` (30min)
9. ✅ Create initial `docker-compose.yml` (1h)
10. ✅ Document any deviations (30min)

**Outcome:** Week 1 is **UNBLOCKED** and can start on schedule.

### Concurrent Actions (During Week 1)

**Week 1 Days 1-3:** Focus on extraction using created scripts

**Week 1 Days 4-5 (Parallel):**
- Delegate migration script creation (11 scripts)
- Create remaining config files (9 configs)
- Validate all scripts with dry-runs

### Alternative: Simplified Week 1

If script creation takes longer:

**Option A: Manual Extraction (Week 1)**
- Day 1-2: Manual rule extraction (slower, but works)
- Day 3: Create scripts based on learned patterns
- Day 4-5: Use scripts to validate/fix manually extracted rules

**Option B: Delay Week 1 by 2 days**
- Day -2 to -1: Create all required scripts
- Day 1-5: Execute as planned with automation

---

## Part 8: Script Templates Summary

### Scripts That Have Complete Templates in Docs

| Script | Template Location | LOC | Can Generate |
|--------|------------------|-----|--------------|
| `extract_rule.py` | REBUILD_EXECUTION_PLAN.md:314-412 | 200 | ✅ YES |
| `create_test_fixtures.py` | REBUILD_EXECUTION_PLAN.md:1339-1410 | 100 | ✅ YES |
| `validate_week1.sh` | GETTING_STARTED.md:355-377 | 50 | ✅ YES |
| `migrate_data.py` | REBUILD_APPENDICES.md:716-1067 | 350 | ✅ YES |
| `test_mvp.sh` | GETTING_STARTED.md:385-408 | 30 | ✅ YES |

**Total:** 5 scripts, ~730 LOC, ALL can be generated from existing templates.

### Scripts That Need Design

| Script | Purpose | Estimated LOC | Design Required |
|--------|---------|---------------|----------------|
| Migration suite (11 scripts) | Data migration workflow | 1200 | ⚠️ MEDIUM |
| Validation parity tester | Compare old vs new validation | 150 | ⚠️ MEDIUM |
| Regression test runner | Full system regression | 200 | ⚠️ MEDIUM |

**Total:** 13 scripts, ~1550 LOC, require design work.

---

## Part 9: Configuration Files Summary

### Configs With Complete Templates

| Config | Template Location | Can Generate |
|--------|------------------|--------------|
| ARAI-01.yaml (rule example) | REBUILD_APPENDICES.md:207-428 | ✅ YES |
| .env.example | REBUILD_APPENDICES.md:432-617 | ✅ YES |
| docker-compose.prod.yml | REBUILD_APPENDICES.md:621-708 | ✅ YES |
| PROMPT_STRUCTURE.yaml | REBUILD_EXECUTION_PLAN.md:1148-1210 | ✅ YES |

### Configs That Need Design

| Config | Purpose | Week Needed | Design Effort |
|--------|---------|-------------|---------------|
| rule_reasoning_config.yaml | Rule reasoning patterns | W1 | 2h |
| category_patterns.yaml | Ontological patterns | W1 | 2h |
| web_lookup_defaults.yaml | Web lookup settings | W2 | 1h |
| openai_config.yaml | AI service config | W2 | 1h |
| cache_config.yaml | Cache settings | W2 | 1h |
| logging_config.yaml | Logging setup | W2 | 1h |
| approval_gate.yaml | Gate policy | W3 | 1h |

**Total:** 7 configs, ~10 hours design effort.

---

## Part 10: Final Recommendations

### Critical Path to Unblock Week 1

**Estimated Effort:** 1 preparation day (8 hours)

**Priority Queue:**
1. ✅ `extract_rule.py` - 2h (BLOCKING Day 1 start)
2. ✅ `config/validation_rules/` + ARAI-01.yaml - 1h (BLOCKING Day 1)
3. ✅ Prompt templates (3 files) - 30min (BLOCKING Day 3)
4. ✅ `create_test_fixtures.py` - 1.5h (BLOCKING Day 4)
5. ✅ `validate_week1.sh` - 30min (BLOCKING Day 5 Gate)
6. ✅ `.env.example` - 30min (BLOCKING Week 2)
7. ✅ Initial `docker-compose.yml` - 1h (BLOCKING Week 2)

**Total:** 7.5 hours → Fits in 1 preparation day

### Migration Scripts (Parallel Track)

**Estimated Effort:** 2-3 days (16-24 hours)

Can be created in parallel during Week 1 execution:
- 11 migration scripts (~1200 LOC)
- 7 operational configs (~10h design)

**Recommended:** Assign to second developer or create during Week 1 evenings.

### Risk Mitigation

**Risk:** Scripts don't work as expected
**Mitigation:** Build + test each script immediately after creation

**Risk:** Template translations have errors
**Mitigation:** Validate with dry-runs before Week 1 start

**Risk:** Config files missing fields
**Mitigation:** Start with minimal configs, extend as needed

---

## Appendix A: Quick Reference - Missing Items Checklist

### Scripts (18 total)
- [ ] `rebuild/scripts/extract_rule.py` (P0)
- [ ] `rebuild/scripts/create_test_fixtures.py` (P0)
- [ ] `scripts/validate_week1.sh` (P0)
- [ ] `scripts/test_mvp.sh` (P3)
- [ ] `scripts/migrate_data.py` (P2)
- [ ] `scripts/migration/1_export_baseline.py` (P1)
- [ ] `scripts/migration/2_validate_export.py` (P1)
- [ ] `scripts/migration/3_migrate_database.py` (P1)
- [ ] `scripts/migration/4_validate_migration.py` (P1)
- [ ] `scripts/migration/rollback_database.sh` (P1)
- [ ] `scripts/migration/6_test_validation_parity.py` (P1)
- [ ] `scripts/migration/7_document_validation_rules.py` (P1)
- [ ] `scripts/migration/9_run_regression_tests.py` (P2)
- [ ] `scripts/migration/compare_outputs.py` (P2)
- [ ] `scripts/migration/validate_shadow_writes.py` (P2)
- [ ] `scripts/migration/final_sync.py` (P2)
- [ ] `scripts/backup_restore.py` (P3)
- [ ] `scripts/archive_data.py` (P3)

### Templates (6 total)
- [ ] `rebuild/extracted/generation/prompts/SYSTEM_PROMPT.md` (P0)
- [ ] `rebuild/extracted/generation/prompts/CONTEXT_TEMPLATE.md` (P0)
- [ ] `rebuild/extracted/generation/prompts/RULES_INJECTION.md` (P0)
- [ ] `.env.example` (P1)
- [ ] `docker-compose.yml` (P1)
- [ ] `docker-compose.prod.yml` (P3)

### Configs (46 validation rules + 9 operational = 55 total)
- [ ] `config/validation_rules/arai/ARAI-*.yaml` (9 rules) (P0)
- [ ] `config/validation_rules/con/CON-*.yaml` (2 rules) (P0)
- [ ] `config/validation_rules/ess/ESS-*.yaml` (5 rules) (P0)
- [ ] `config/validation_rules/int/INT-*.yaml` (10 rules) (P0)
- [ ] `config/validation_rules/sam/SAM-*.yaml` (8 rules) (P0)
- [ ] `config/validation_rules/str/STR-*.yaml` (9 rules) (P0)
- [ ] `config/validation_rules/ver/VER-*.yaml` (3 rules) (P0)
- [ ] `config/validation/rule_reasoning_config.yaml` (P1)
- [ ] `config/ontology/category_patterns.yaml` (P1)
- [ ] `config/web_lookup_defaults.yaml` (P2)
- [ ] `config/openai_config.yaml` (P2)
- [ ] `config/cache_config.yaml` (P2)
- [ ] `config/logging_config.yaml` (P2)
- [ ] `config/approval_gate.yaml` (P3)
- [ ] `config/config_development.yaml` (P2)
- [ ] `config/toetsregels/toetsregels_config.yaml` (P2)

**Grand Total:** 79 files missing

---

## Appendix B: Template Extraction Commands

### Generate Scripts From Documentation

```bash
# Extract extract_rule.py from REBUILD_EXECUTION_PLAN.md
sed -n '/^```python$/,/^```$/p' REBUILD_PACKAGE/docs/REBUILD_EXECUTION_PLAN.md | \
  sed '1d;$d' > rebuild/scripts/extract_rule.py

# Extract create_test_fixtures.py
sed -n '1339,1410p' REBUILD_PACKAGE/docs/REBUILD_EXECUTION_PLAN.md | \
  sed '/^```python$/,/^```$/!d;//d' > rebuild/scripts/create_test_fixtures.py

# Extract validate_week1.sh
sed -n '355,377p' REBUILD_PACKAGE/GETTING_STARTED.md | \
  sed '/^```bash$/,/^```$/!d;//d' > scripts/validate_week1.sh

# Extract .env.example
sed -n '432,617p' REBUILD_PACKAGE/docs/REBUILD_APPENDICES.md | \
  sed '/^```bash$/,/^```$/!d;//d' > .env.example
```

### Generate Configs From Templates

```bash
# Extract ARAI-01.yaml template
sed -n '212,300p' REBUILD_PACKAGE/docs/REBUILD_EXECUTION_PLAN.md | \
  sed '/^```yaml$/,/^```$/!d;//d' > config/validation_rules/arai/ARAI-01.yaml

# Extract docker-compose.prod.yml
sed -n '621,708p' REBUILD_PACKAGE/docs/REBUILD_APPENDICES.md | \
  sed '/^```yaml$/,/^```$/!d;//d' > docker-compose.prod.yml
```

---

**End of Report**

**Status:** 📋 COMPLETE
**Action Required:** Create 79 missing files before Week 1 start
**Estimated Effort:** 1 preparation day (P0 items) + 2-3 days parallel (P1-P3 items)
**Recommendation:** Execute "Immediate Actions" plan to unblock Week 1
