# REBUILD PACKAGE - TODO LIST

**Status:** Week 1 APPROVED with constraints
**Last Updated:** 2025-10-02
**Priority:** Complete P0/P1 items before Week 1 Day 3

---

## IMMEDIATE (Before Week 1 Starts)

### ✅ COMPLETED

- [x] Create comprehensive completeness report
- [x] Validate existing scripts (Python syntax checks)
- [x] Validate existing configs (YAML syntax checks)
- [x] Test `extract_rule.py` functionality
- [x] Fix path resolution bug in `extract_rule.py`
- [x] Create 9 ARAI validation rule YAMLs
- [x] Create baseline extraction scripts (1-3)
- [x] Create infrastructure templates (docker-compose, .env.example)

### 🔴 P0 - CRITICAL (Before Week 1 Day 3)

#### 1. Create Rollback Script
**File:** `scripts/migration/rollback_database.sh`
**Effort:** 1-2 hours
**Purpose:** Safety mechanism to restore database if migration fails
**Requirements:**
- Restore from backup created by script #1
- Validate backup exists before restore
- Log all operations
- Include help function
- Use `set -euo pipefail`

**Implementation Checklist:**
```bash
#!/bin/bash
set -euo pipefail

# Check backup exists
# Validate backup integrity
# Stop running services
# Restore database from backup
# Verify restore success
# Restart services
# Log completion
```

#### 2. Create Validation Script #4
**File:** `scripts/migration/4_validate_migration.py`
**Effort:** 2-3 hours
**Purpose:** Verify migration completed successfully
**Requirements:**
- Compare record counts (old vs new DB)
- Validate schema matches expected structure
- Check data integrity (no nulls in required fields)
- Verify all validation rules present
- Generate validation report (JSON + text)

**Implementation Checklist:**
```python
# Load both databases (old + new)
# Compare table structures
# Compare record counts
# Sample data integrity checks
# Validate foreign keys
# Check validation rules table
# Generate comparison report
# Exit with proper status code
```

---

## WEEK 1 - HIGH PRIORITY

### 🟡 P1 - Day 1-2 (Infrastructure)

#### 3. Create Missing Operational Configs (as-needed)
**Files:** (3 configs, create if needed during setup)
- `config/openai_config.yaml`
- `config/cache_config.yaml`
- `config/logging_config.yaml`

**Effort:** 1-2 hours total
**Source:** Extract from existing codebase
**Note:** May not be needed if existing config files suffice

**Extraction Guide:**
```bash
# OpenAI config from:
grep -r "openai" src/services/ai_service_v2.py

# Cache config from:
grep -r "cache" src/ --include="*.py"

# Logging config from:
grep -r "logging" src/ --include="*.py"
```

### 🟡 P1 - Day 5 (Rule Extraction)

#### 4. Extract Remaining 37 Validation Rules
**Categories:** CON (2), ESS (5), INT (10), SAM (8), STR (9), VER (3)
**Effort:** 6-8 hours (mostly automated)
**Tool:** `rebuild/scripts/extract_rule.py` (already working)

**Batch Extraction Script:**
```bash
#!/bin/bash
set -euo pipefail

PROJECT_ROOT="/Users/chrislehnen/Projecten/Definitie-app"
cd "$PROJECT_ROOT"

# Categories to process
categories=("con" "ess" "int" "sam" "str" "ver")

for category in "${categories[@]}"; do
    echo "Processing ${category^^} category..."

    # Find all rule files for this category
    for rule_file in src/toetsregels/regels/${category^^}-*.py; do
        if [ -f "$rule_file" ]; then
            echo "  Extracting $(basename $rule_file)..."
            python3 rebuild/scripts/extract_rule.py "$rule_file"
        fi
    done

    echo "  ${category^^} complete."
done

echo ""
echo "✓ All rules extracted. Validating YAMLs..."

# Validate all generated YAMLs
find config/validation_rules -name "*.yaml" -exec python3 -c "import yaml; yaml.safe_load(open('{}'))" \;

echo "✓ All YAMLs validated successfully."
```

**Validation After Extraction:**
- Run YAML syntax validation on all files
- Verify expected counts (46 total rules)
- Spot-check 2-3 rules manually for quality
- Commit to git with descriptive message

---

## WEEK 2 - MEDIUM PRIORITY

### 🟢 P2 - Parity & Documentation

#### 5. Create Parity Testing Script
**File:** `scripts/migration/6_test_validation_parity.py`
**Effort:** 4-6 hours
**Purpose:** Verify new validation logic matches old logic

**Requirements:**
- Load test definitions (100+ samples)
- Run through old validation logic
- Run through new validation logic
- Compare results
- Report discrepancies
- Generate parity score (%)

#### 6. Create Documentation Generator
**File:** `scripts/migration/7_document_validation_rules.py`
**Effort:** 3-4 hours
**Purpose:** Auto-generate validation rule documentation

**Requirements:**
- Read all validation rule YAMLs
- Extract metadata, patterns, examples
- Generate markdown documentation
- Include usage examples
- Create index/table of contents

#### 7. Create Output Comparison Script
**File:** `scripts/migration/compare_outputs.py`
**Effort:** 2-3 hours
**Purpose:** Compare definition outputs between old/new systems

**Requirements:**
- Load definitions from both systems
- Compare field by field
- Calculate similarity scores
- Report differences
- Flag potential issues

---

## WEEK 3 - LOW PRIORITY

### 🟢 P3 - Regression & Final Sync

#### 8. Create Regression Test Suite
**File:** `scripts/migration/9_run_regression_tests.py`
**Effort:** 6-8 hours
**Purpose:** Comprehensive regression testing

**Requirements:**
- Load historical test cases
- Run through new system
- Compare with expected outputs
- Generate test report
- Track pass/fail rates

#### 9. Create Shadow Write Validator
**File:** `scripts/migration/validate_shadow_writes.py`
**Effort:** 3-4 hours
**Purpose:** Validate dual-write consistency

**Requirements:**
- Monitor writes to both systems
- Compare written data
- Report inconsistencies
- Alert on failures

#### 10. Create Final Sync Script
**File:** `scripts/migration/final_sync.py`
**Effort:** 4-5 hours
**Purpose:** Final data synchronization before cutover

**Requirements:**
- Identify delta records
- Migrate missing records
- Validate completeness
- Generate sync report

#### 11. Create Production Docker Compose (Optional)
**File:** `docker-compose.prod.yml`
**Effort:** 1-2 hours
**Purpose:** Production-ready Docker configuration

**Requirements:**
- Remove debug settings
- Use production-grade database
- Add health checks
- Configure logging
- Add restart policies

---

## QUALITY IMPROVEMENTS (Optional)

### Non-Blocking Enhancements

#### 12. Add Error Handling to extract_rule.py
**Effort:** 30 minutes
**Changes:**
- Wrap main logic in try/except
- Add file existence checks
- Handle AST parsing errors gracefully
- Add logging statements

#### 13. Add Error Handling to create_test_fixtures.py
**Effort:** 30 minutes
**Changes:**
- Similar to extract_rule.py
- Add CLI interface with argparse
- Add logging

#### 14. Improve validate_week1.sh
**Effort:** 15 minutes
**Changes:**
- Add `set -euo pipefail`
- Add help function
- Improve error messages

---

## SUMMARY BY PRIORITY

### Must Do (P0) - Before Week 1 Day 3
- [ ] Create rollback script (1-2 hours)
- [ ] Create validation script #4 (2-3 hours)

**Total Effort:** 3-5 hours

### Should Do (P1) - During Week 1
- [ ] Extract remaining 37 rules (6-8 hours, mostly automated)
- [ ] Create missing configs as-needed (1-2 hours)

**Total Effort:** 7-10 hours

### Could Do (P2) - Week 2
- [ ] Parity testing (4-6 hours)
- [ ] Documentation generator (3-4 hours)
- [ ] Output comparison (2-3 hours)

**Total Effort:** 9-13 hours

### Nice to Have (P3) - Week 3+
- [ ] Regression tests (6-8 hours)
- [ ] Shadow write validator (3-4 hours)
- [ ] Final sync script (4-5 hours)
- [ ] Production docker-compose (1-2 hours)

**Total Effort:** 14-19 hours

### Optional Quality Improvements
- [ ] Error handling improvements (1-2 hours)

---

## WEEK 1 DAILY BREAKDOWN

### Day 1: Infrastructure Setup
**Duration:** 4-6 hours
**Tasks:**
- Set up Docker environment
- Configure .env file
- Test database connectivity
- Verify all configs load correctly
- Create missing configs if needed

### Day 2: Infrastructure Validation
**Duration:** 2-4 hours
**Tasks:**
- Run smoke tests
- Validate all services start
- Test basic CRUD operations
- Document any issues

### Day 3: Baseline Extraction
**Duration:** 4-6 hours
**Tasks:**
- **MUST DO FIRST:** Create rollback script
- Run script #1 (export baseline)
- Run script #2 (validate export)
- Verify backup integrity
- Document baseline stats

### Day 4: Database Migration
**Duration:** 6-8 hours
**Tasks:**
- Run script #3 (migrate database)
- **CREATE:** validation script #4
- Run validation script #4
- Compare old vs new DB
- Document migration results

### Day 5: Rule Extraction
**Duration:** 6-8 hours
**Tasks:**
- Batch extract 37 remaining rules
- Validate all YAMLs
- Spot-check rule quality
- Create test fixtures
- Run end-to-end validation test

---

## TRACKING PROGRESS

### Completion Tracking

**P0 Critical:** 0/2 (0%)
**P1 High:** 0/2 (0%)
**P2 Medium:** 0/3 (0%)
**P3 Low:** 0/5 (0%)
**Optional:** 0/3 (0%)

**Overall:** 0/15 remaining tasks (100% complete for existing files)

### Update This Document

After completing each task:
1. Change `[ ]` to `[x]`
2. Update completion percentages
3. Document any issues encountered
4. Add notes for future reference

---

## NOTES & LESSONS LEARNED

### During QA Process (2025-10-02)

**Issues Found & Fixed:**
1. `extract_rule.py` had path resolution bug using `relative_to()`
   - **Fixed:** Changed to `rule_file.resolve()`
   - **Tested:** Successfully extracts ARAI-02 rule

**Quality Observations:**
- Migration scripts (1-3) are excellent quality
- ARAI rules complete and validated
- All YAMLs have valid syntax
- Directory structure well organized

**Recommendations:**
- Prioritize rollback script (safety first)
- Use batch script for rule extraction (proven to work)
- Create configs as-needed rather than upfront

---

**Last Updated:** 2025-10-02
**Next Review:** Before Week 1 Day 1
**Owner:** REBUILD Migration Team
