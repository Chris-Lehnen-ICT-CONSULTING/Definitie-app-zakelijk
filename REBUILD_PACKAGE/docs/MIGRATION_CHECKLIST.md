---
aangemaakt: 2025-10-02
applies_to: definitie-app@rebuild
canonical: false
id: MIGRATION-CHECKLIST
owner: code-architect
parent: MIGRATION_STRATEGY.md
prioriteit: P0
status: draft
titel: Migration Execution Checklist (Print-Ready)
type: checklist
---

# MIGRATION EXECUTION CHECKLIST

**Print This Document:** Use as day-to-day execution guide
**Parent:** [MIGRATION_STRATEGY.md](./MIGRATION_STRATEGY.md)
**Roadmap:** [MIGRATION_ROADMAP.md](./MIGRATION_ROADMAP.md)

---

## PRE-MIGRATION PREPARATION

### Setup & Planning (1 Day Before)

- [ ] **Read complete migration strategy** (MIGRATION_STRATEGY.md)
- [ ] **Schedule stakeholder meetings** (Go/No-Go gates)
- [ ] **Set up communication channels** (Slack/Teams for team updates)
- [ ] **Prepare rollback procedure** (test once, document)
- [ ] **Back up current database** (verify restorable)
  ```bash
  cp data/definities.db data/definities.db.pre-migration-backup
  sqlite3 data/definities.db.pre-migration-backup "PRAGMA integrity_check;"
  ```

### Environment Setup

- [ ] **Clone repository** (fresh clone for migration)
  ```bash
  git clone <repo-url> definitie-app-migration
  cd definitie-app-migration
  git checkout main
  ```

- [ ] **Install dependencies**
  ```bash
  pip install -r requirements.txt
  pip install -r requirements-dev.txt
  ```

- [ ] **Verify database access**
  ```bash
  sqlite3 data/definities.db "SELECT COUNT(*) FROM definities;"
  # Expected: 42
  ```

- [ ] **Set up logging directory**
  ```bash
  mkdir -p logs/migration
  chmod 755 logs/migration
  ```

---

## WEEK 1: DATA PRESERVATION & RULE EXTRACTION

### Day 1: Database Export & Migration (8 hours)

**Morning (4 hours)**

- [ ] 09:00 - Export baseline data
  ```bash
  python scripts/migration/1_export_baseline.py
  # Creates: data/migration_baseline.json
  ```

- [ ] 09:30 - Validate export completeness
  ```bash
  python scripts/migration/2_validate_export.py data/migration_baseline.json
  # Expected: ✅ All tests passed
  ```

- [ ] 10:00 - Review export logs
  ```bash
  cat logs/migration/export_baseline_*.log
  # Look for: "42 definitions exported"
  ```

- [ ] 10:30 - Coffee break ☕

- [ ] 11:00 - Execute migration (DRY RUN)
  ```bash
  python scripts/migration/3_migrate_database.py --dry-run
  # Review output carefully!
  ```

- [ ] 11:30 - Review dry-run results
  - [ ] Record counts correct (42/96/90)
  - [ ] No errors or warnings
  - [ ] Estimated time < 30 minutes

- [ ] 12:00 - Lunch break 🍽️

**Afternoon (4 hours)**

- [ ] 13:00 - Execute migration (ACTUAL)
  ```bash
  python scripts/migration/3_migrate_database.py --execute
  # This creates automatic backup!
  ```

- [ ] 13:30 - Monitor migration progress
  ```bash
  tail -f logs/migration/migrate_database_*.log
  # Watch for: "Step X/10 complete"
  ```

- [ ] 14:00 - Validate migrated data
  ```bash
  python scripts/migration/4_validate_migration.py
  # Expected: ✅ All validation tests passed
  ```

- [ ] 14:30 - Verify sample records (manual check)
  ```bash
  sqlite3 data/definities.db.new
  SELECT begrip, definitie FROM definitions LIMIT 5;
  # Compare to old database manually
  ```

- [ ] 15:00 - Document any issues
  - [ ] Screenshot of validation results
  - [ ] Note any warnings (even if tests passed)
  - [ ] Calculate actual migration time

- [ ] 15:30 - Team sync meeting
  - [ ] Share validation results
  - [ ] Discuss any concerns
  - [ ] Plan next steps

**End of Day 1 Deliverable:**
- [ ] ✅ Migrated database (42 definitions)
- [ ] ✅ Baseline export (migration_baseline.json)
- [ ] ✅ Validation passed (100% records)
- [ ] ✅ Migration log saved

---

### Day 2: Rollback Testing & Validator Design (8 hours)

**Morning (4 hours)**

- [ ] 09:00 - Test rollback procedure
  ```bash
  bash scripts/migration/rollback_database.sh --test
  # Expected: Completes in < 5 minutes
  ```

- [ ] 09:15 - Time rollback execution
  - [ ] Start timer
  - [ ] Execute rollback
  - [ ] Stop timer
  - [ ] Record time: _______ minutes (target: < 5 min)

- [ ] 09:30 - Verify rollback worked
  ```bash
  sqlite3 data/definities.db "SELECT COUNT(*) FROM definities;"
  # Expected: 42 (same as before)
  ```

- [ ] 10:00 - Document rollback procedure
  - [ ] Write step-by-step instructions
  - [ ] Note any issues encountered
  - [ ] Share with team

- [ ] 10:30 - Coffee break ☕

- [ ] 11:00 - Stakeholder meeting: Data Migration Sign-Off
  - [ ] Present migration results (42/96/90 records)
  - [ ] Demo rollback procedure (< 5 min)
  - [ ] Address any questions/concerns
  - [ ] **Get formal sign-off** ✍️

- [ ] 12:00 - Lunch break 🍽️

**Afternoon (4 hours)**

- [ ] 13:00 - Design generic validator architecture
  - [ ] Review 46 current validators
  - [ ] Identify common patterns
  - [ ] Design 5 validator types:
    - [ ] Pattern validator (regex-based)
    - [ ] Length validator (min/max)
    - [ ] Semantic validator (meaning checks)
    - [ ] Structural validator (format checks)
    - [ ] Custom validator (complex logic)

- [ ] 14:00 - Create validator interface specification
  ```python
  # Document in: docs/migration/validator_interface.md
  class ValidatorInterface:
      def validate(self, text: str, config: dict) -> ValidationResult
  ```

- [ ] 15:00 - Document validator patterns
  - [ ] Create mapping: Python rule → Validator type
  - [ ] List config parameters per validator
  - [ ] Write YAML schema examples

- [ ] 16:00 - Team review: Validator design
  - [ ] Share design document
  - [ ] Get feedback from team
  - [ ] Finalize architecture

**End of Day 2 Deliverable:**
- [ ] ✅ Rollback tested (< 5 min)
- [ ] ✅ Stakeholder sign-off obtained
- [ ] ✅ Validator architecture designed
- [ ] ✅ Validator interface documented

---

### Day 3: Implement Generic Validators (8 hours)

**Morning (4 hours)**

- [ ] 09:00 - Implement PatternValidator
  ```python
  # File: validators/pattern_validator.py
  # Handles: ARAI rules (regex patterns)
  # Lines: ~50 LOC
  ```

- [ ] 10:00 - Test PatternValidator
  - [ ] Unit tests (10 test cases)
  - [ ] Test with ARAI-01 config
  - [ ] Verify ± 5% parity with old validator

- [ ] 10:30 - Coffee break ☕

- [ ] 11:00 - Implement LengthValidator
  ```python
  # File: validators/length_validator.py
  # Handles: STR rules (min/max length)
  # Lines: ~40 LOC
  ```

- [ ] 11:30 - Test LengthValidator
  - [ ] Unit tests (8 test cases)
  - [ ] Test with STR-01 config
  - [ ] Verify parity

- [ ] 12:00 - Lunch break 🍽️

**Afternoon (4 hours)**

- [ ] 13:00 - Implement SemanticValidator
  ```python
  # File: validators/semantic_validator.py
  # Handles: ESS rules (meaning checks)
  # Lines: ~60 LOC
  ```

- [ ] 14:00 - Implement StructuralValidator
  ```python
  # File: validators/structural_validator.py
  # Handles: INT rules (format checks)
  # Lines: ~50 LOC
  ```

- [ ] 15:00 - Implement CustomValidator
  ```python
  # File: validators/custom_validator.py
  # Handles: Complex rules (custom logic)
  # Lines: ~50 LOC
  ```

- [ ] 16:00 - Test all 5 validators
  - [ ] Integration tests
  - [ ] Test with sample definitions
  - [ ] Document validator usage

**End of Day 3 Deliverable:**
- [ ] ✅ 5 generic validators implemented (250 LOC total)
- [ ] ✅ All validators tested
- [ ] ✅ Validator documentation complete

---

### Day 4: Port Validation Rules (Part 1) (8 hours)

**Morning (4 hours)**

- [ ] 09:00 - Port ARAI rules (8 rules)
  - [ ] ARAI-01.yaml
  - [ ] ARAI-02.yaml
  - [ ] ARAI-02SUB1.yaml
  - [ ] ARAI-02SUB2.yaml
  - [ ] ARAI-03.yaml
  - [ ] ARAI-04.yaml
  - [ ] ARAI-04SUB1.yaml
  - [ ] ARAI-05.yaml

- [ ] 10:00 - Test ARAI rules parity
  ```bash
  python scripts/migration/6_test_validation_parity.py --category ARAI
  # Expected: >= 95% parity
  ```

- [ ] 10:30 - Coffee break ☕

- [ ] 11:00 - Port CON rules (2 rules)
  - [ ] CON-01.yaml
  - [ ] CON-02.yaml

- [ ] 11:15 - Port ESS rules (5 rules)
  - [ ] ESS-01.yaml
  - [ ] ESS-02.yaml
  - [ ] ESS-03.yaml
  - [ ] ESS-04.yaml
  - [ ] ESS-05.yaml

- [ ] 12:00 - Lunch break 🍽️

**Afternoon (4 hours)**

- [ ] 13:00 - Port INT rules (10 rules)
  - [ ] INT-01.yaml through INT-10.yaml
  - [ ] Test each rule after porting

- [ ] 14:30 - Port SAM rules (8 rules)
  - [ ] SAM-01.yaml through SAM-08.yaml
  - [ ] Test each rule

- [ ] 16:00 - Test all ported rules (33/46 done)
  ```bash
  python scripts/migration/6_test_validation_parity.py
  # Expected: >= 95% parity for 33 rules
  ```

**End of Day 4 Deliverable:**
- [ ] ✅ 33/46 rules ported to YAML
- [ ] ✅ >= 95% parity validated
- [ ] ✅ Rule configurations documented

---

### Day 5: Port Validation Rules (Part 2) & Week 1 Wrap-Up (8 hours)

**Morning (4 hours)**

- [ ] 09:00 - Port STR rules (9 rules)
  - [ ] STR-01.yaml through STR-09.yaml

- [ ] 10:00 - Port VER rules (3 rules)
  - [ ] VER-01.yaml
  - [ ] VER-02.yaml
  - [ ] VER-03.yaml

- [ ] 10:30 - Coffee break ☕

- [ ] 11:00 - Port DUP rule (1 rule)
  - [ ] DUP-01.yaml

- [ ] 11:15 - Test all 46 rules (full parity check)
  ```bash
  python scripts/migration/6_test_validation_parity.py --all
  # Expected: >= 95% parity for all 46 rules
  ```

- [ ] 12:00 - Lunch break 🍽️

**Afternoon (4 hours)**

- [ ] 13:00 - Generate validation rule documentation
  ```bash
  python scripts/migration/7_document_validation_rules.py
  # Creates: docs/validation_rules.md
  ```

- [ ] 13:30 - Fix any parity issues (< 95%)
  - [ ] Review rules with < 95% parity
  - [ ] Adjust YAML configs
  - [ ] Re-test until >= 95%

- [ ] 14:30 - Create validation rule index
  - [ ] Searchable HTML version
  - [ ] Rule category breakdown
  - [ ] Usage examples

- [ ] 15:00 - Stakeholder meeting: Week 1 Sign-Off
  - [ ] Present migration results
    - [ ] ✅ 42 definitions migrated
    - [ ] ✅ 46 rules ported to YAML
    - [ ] ✅ >= 95% validation parity
    - [ ] ✅ Rollback tested (< 5 min)
  - [ ] **Get formal sign-off for Phase 1** ✍️

- [ ] 16:00 - Week 1 retrospective
  - [ ] What went well?
  - [ ] What could be improved?
  - [ ] Lessons learned
  - [ ] Plan for Week 2

**End of Week 1 Deliverable:**
- [ ] ✅ Phase 1 Complete: Data Preservation ✅
- [ ] ✅ 46 YAML validation configs
- [ ] ✅ >= 95% validation parity
- [ ] ✅ Stakeholder sign-off obtained

---

## WEEK 2-3: FEATURE PARITY MVP

### Week 2, Day 1: Definition Generation (Morning)

**Core Feature: GPT-4 Integration**

- [ ] 09:00 - Setup AI service
  - [ ] Configure OpenAI API key
  - [ ] Test GPT-4 connection
  - [ ] Verify rate limits

- [ ] 10:00 - Implement generation service
  - [ ] Port prompt templates
  - [ ] Add temperature control
  - [ ] Add token limiting

- [ ] 11:00 - Test generation with 5 sample terms
  - [ ] "verificatie" (process)
  - [ ] "toets" (process)
  - [ ] "traject" (type)
  - [ ] "biometrie" (type)
  - [ ] "grondslagsoort" (type)

- [ ] 12:00 - Lunch break 🍽️

**Similarity Validation (Afternoon)**

- [ ] 13:00 - Compare outputs (old vs new)
  - [ ] Calculate cosine similarity (target: >= 85%)
  - [ ] Check length variation (target: ± 20%)
  - [ ] Document any differences

- [ ] 14:00 - Fix generation issues
  - [ ] Adjust prompts if needed
  - [ ] Tune temperature
  - [ ] Re-test

- [ ] 15:00 - Generate all 42 definitions
  ```bash
  python scripts/migration/9_run_regression_tests.py --feature generation
  ```

- [ ] 16:00 - Review results
  - [ ] Similarity scores (all >= 85%)
  - [ ] No errors/crashes
  - [ ] Performance acceptable (< 5s per definition)

**End of Day Checklist:**
- [ ] ✅ Definition generation working
- [ ] ✅ 42 test cases >= 85% similarity
- [ ] ✅ Performance meets targets

---

### Week 2, Day 2-5: Continue MVP Features

**Use this template for each day:**

**Daily Standup (09:00)**
- [ ] What did I complete yesterday?
- [ ] What am I working on today?
- [ ] Any blockers?

**Implementation (09:30-12:00)**
- [ ] Feature implementation
- [ ] Unit tests
- [ ] Integration tests

**Testing (13:00-16:00)**
- [ ] Regression testing
- [ ] Performance benchmarks
- [ ] Bug fixes

**Daily Wrap-Up (16:00)**
- [ ] Update progress tracker
- [ ] Document issues
- [ ] Plan tomorrow

---

## WEEK 4: PARALLEL RUN

### Day 1-3: Read-Only Validation

**Daily Checklist (Repeat for 3 Days)**

**Morning (09:00)**
- [ ] Start both systems (old + new)
- [ ] Verify both systems healthy
- [ ] Set new system to read-only mode
- [ ] Monitor error logs

**During Day (10:00-16:00)**
- [ ] Run comparison tests every 2 hours
  ```bash
  python scripts/migration/compare_outputs.py
  ```
- [ ] Log any discrepancies
- [ ] Monitor performance metrics
- [ ] Check error rates (target: < 1%)

**End of Day (17:00)**
- [ ] Generate daily report
- [ ] Review discrepancies
- [ ] Plan fixes for tomorrow
- [ ] Send stakeholder update

---

### Day 4-5: Shadow Writes

**Morning (09:00)**
- [ ] Enable write mode on new system
- [ ] Configure shadow database
- [ ] Set up nightly sync job

**During Day**
- [ ] Monitor both databases
- [ ] Check write operations
- [ ] Verify data consistency

**Nightly Sync (20:00)**
- [ ] Run sync validation
  ```bash
  python scripts/migration/validate_shadow_writes.py
  ```
- [ ] Check for discrepancies (target: 100% match)
- [ ] Document any issues

---

### Day 6-7: Pilot Users (20% Traffic)

**Morning (09:00)**
- [ ] Route 20% traffic to new system
- [ ] Monitor both systems
- [ ] Set up alerts (error rate > 1%)

**During Day (Every Hour)**
- [ ] Check error rates
- [ ] Monitor performance
- [ ] Review user feedback
- [ ] Document issues

**If Error Rate > 5%:**
- [ ] 🚨 Execute emergency rollback
  ```bash
  bash scripts/migration/rollback_database.sh --execute
  ```
- [ ] Notify stakeholders
- [ ] Investigate issues

**End of Day**
- [ ] Generate metrics report
- [ ] Survey pilot users
- [ ] Plan fixes

---

## WEEK 5: CUTOVER & STABILIZATION

### Day 1: Go/No-Go Decision

**Pre-Meeting Preparation (09:00-11:00)**

- [ ] Generate final metrics report
  - [ ] 7 days parallel run stable
  - [ ] Error rate: ______% (target: < 1%)
  - [ ] User satisfaction: ______% (target: >= 80%)
  - [ ] Data consistency: ______% (target: 100%)

- [ ] Prepare presentation
  - [ ] Migration summary
  - [ ] Success metrics
  - [ ] Risk assessment
  - [ ] Rollback plan

**Stakeholder Meeting (11:00-12:00)**

- [ ] Present metrics
- [ ] Address questions/concerns
- [ ] Review rollback procedure
- [ ] **Make Go/No-Go decision** ✍️

**Decision: [ ] GO / [ ] NO-GO**

**If NO-GO:**
- [ ] Extend parallel run (add 7 days)
- [ ] Fix identified issues
- [ ] Re-schedule Go/No-Go meeting

**If GO:**
- [ ] Proceed to Day 2 (Cutover)
- [ ] Schedule cutover window
- [ ] Notify all stakeholders

---

### Day 2: Cutover Execution

**Pre-Cutover (08:00-09:00)**

- [ ] Final database sync
- [ ] Verify both systems healthy
- [ ] Notify users (maintenance window)
- [ ] Prepare rollback script (just in case)

**Cutover Window (09:00-10:00)**

- [ ] 09:00 - Stop old system
  ```bash
  systemctl stop definitieagent-v2
  ```

- [ ] 09:05 - Final database sync
  ```bash
  python scripts/migration/final_sync.py
  ```

- [ ] 09:10 - Route 100% traffic to new system
  ```bash
  # Update load balancer / DNS
  ```

- [ ] 09:15 - Start new system
  ```bash
  systemctl start definitieagent-v3
  ```

- [ ] 09:20 - Health check
  ```bash
  curl -f http://localhost:8501/_stcore/health
  # Expected: 200 OK
  ```

- [ ] 09:30 - Monitor for 30 minutes
  - [ ] Watch error logs
  - [ ] Check performance
  - [ ] Verify user access

**Post-Cutover (10:00-12:00)**

- [ ] Test all core features
  - [ ] Definition generation
  - [ ] Validation
  - [ ] Search
  - [ ] Export

- [ ] Archive old system (don't delete!)
  ```bash
  mv definitieagent-v2 definitieagent-v2-archived
  ```

- [ ] Send cutover success notification
- [ ] Update documentation
- [ ] Celebrate! 🎉

**24-Hour Monitoring**

- [ ] Monitor every hour for first 24 hours
- [ ] Check error rates
- [ ] Watch performance metrics
- [ ] Respond to user feedback

---

### Day 3-7: Stabilization & Monitoring

**Daily Checklist (Repeat for 5 Days)**

**Morning (09:00)**
- [ ] Check overnight logs
- [ ] Review error reports
- [ ] Check performance metrics
- [ ] Plan daily priorities

**During Day**
- [ ] Fix minor bugs (< 24h turnaround)
- [ ] Performance tuning (if needed)
- [ ] Respond to user feedback
- [ ] Document issues/solutions

**End of Day (17:00)**
- [ ] Generate daily report
- [ ] Update stakeholders
- [ ] Archive logs
- [ ] Plan tomorrow

---

## POST-MIGRATION

### Week 6: Retrospective & Cleanup

- [ ] **Conduct retrospective meeting**
  - [ ] What went well?
  - [ ] What didn't go well?
  - [ ] What would we do differently?
  - [ ] Lessons learned documentation

- [ ] **Update documentation**
  - [ ] Architecture diagrams
  - [ ] API documentation
  - [ ] User guides
  - [ ] Developer guides

- [ ] **Archive old system** (after 30 days)
  - [ ] Verify new system stable
  - [ ] Create final backup of old system
  - [ ] Decommission old infrastructure
  - [ ] Update monitoring/alerts

- [ ] **Knowledge transfer**
  - [ ] Train support team
  - [ ] Document common issues
  - [ ] Create troubleshooting guide
  - [ ] Conduct training sessions

---

## EMERGENCY PROCEDURES

### If Migration Fails (Any Phase)

**Immediate Actions:**
1. [ ] Stop migration process (Ctrl+C)
2. [ ] Check logs (logs/migration/*.log)
3. [ ] Execute rollback
   ```bash
   bash scripts/migration/rollback_database.sh --execute
   ```
4. [ ] Verify old system working
5. [ ] Notify team

**Investigation:**
- [ ] Preserve all logs
- [ ] Document error details
- [ ] Identify root cause
- [ ] Plan fix

**Recovery:**
- [ ] Fix identified issues
- [ ] Re-test in dev environment
- [ ] Re-schedule migration
- [ ] Update procedures

---

### If Validation Fails (< 95% Parity)

**Immediate Actions:**
1. [ ] Generate detailed report
   ```bash
   python scripts/migration/6_test_validation_parity.py --verbose
   ```
2. [ ] Review failing rules
3. [ ] Identify patterns in failures

**Analysis:**
- [ ] Is failure < 5% drift? → Acceptable, document
- [ ] Is failure > 10% drift? → Investigate, fix

**Fix Strategy:**
- [ ] Adjust YAML configs
- [ ] Re-test validators
- [ ] Document changes

---

### If Rollback Needed (Production)

**Decision Criteria:**
- Error rate > 10% → Automatic rollback
- Error rate 5-10% → Stakeholder decision
- Critical bug (data loss) → Immediate rollback

**Execution (< 5 minutes):**
```bash
# 1. Execute rollback script
bash scripts/migration/rollback_database.sh --execute

# 2. Verify old system
curl http://localhost:8501/_stcore/health

# 3. Notify stakeholders
# Send immediate notification

# 4. Preserve logs
tar -czf rollback_logs_$(date +%Y%m%d_%H%M%S).tar.gz logs/

# 5. Plan fix
# Schedule investigation meeting
```

---

## SIGN-OFF SHEET

**Phase 1: Data Preservation**
- Date: _______________
- Signed: _______________
- Notes: _______________

**Phase 2: Feature Parity**
- Date: _______________
- Signed: _______________
- Notes: _______________

**Phase 3: Parallel Run**
- Date: _______________
- Signed: _______________
- Notes: _______________

**Go/No-Go Decision**
- Date: _______________
- Decision: [ ] GO / [ ] NO-GO
- Signed: _______________
- Notes: _______________

**Cutover Complete**
- Date: _______________
- Signed: _______________
- Notes: _______________

---

**Checklist Version:** 1.0.0
**Last Updated:** 2025-10-02
**Print Date:** _______________
**Migration Lead:** _______________
