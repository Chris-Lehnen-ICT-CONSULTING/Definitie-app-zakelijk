# DEF-101 Plan B: Complete Implementation Specification

**Document Type:** Comprehensive Implementation Guide
**Status:** Ready for Execution
**Created:** 2025-11-10
**Authors:** Multiagent Analysis (Explore, Debug-Specialist, Plan, Code-Reviewer)
**Estimated Effort:** 26 hours over 11 days
**Expected Impact:** -63% token reduction (7250→2650), system usability restored

---

## 🎯 Executive Summary

Plan B (Quality-focused) is een **11-daags implementatieplan** voor DEF-101 EPIC (Prompt Optimization) dat 9 subissues uitvoert in 3 gefaseerde weken met 6 test gates.

### Waarom Plan B?

**Huidige situatie:**
- ❌ Systeem UNUSABLE (5 blocking contradictions)
- ❌ 7.250 tokens (65% redundancy)
- ❌ Cognitive load 9/10 (100+ concepts)
- ❌ Geen automated validation

**Na Plan B:**
- ✅ Systeem USABLE (0 contradictions)
- ✅ 2.650 tokens (-63% reduction)
- ✅ Cognitive load 4/10 (30 effective concepts)
- ✅ Automated PromptValidator

### 3-Week Overview

| Week | Issues | Effort | Risk | Focus |
|------|--------|--------|------|-------|
| **Week 1** | DEF-102, DEF-103, DEF-126 | 10h | MEDIUM | **System restoration** - Fix contradictions, reduce cognitive load |
| **Week 2** | DEF-104, DEF-106, DEF-123 | 10h | **HIGH** ⚠️ | **Architecture** - Reorganize flow, add validation, context-aware loading |
| **Week 3** | DEF-105, DEF-124, DEF-107 | 6h | LOW | **Polish** - Visual hierarchy, caching, documentation |

### Success Metrics

| Metric | Baseline | Target | Validation Method |
|--------|----------|--------|-------------------|
| **Usability** | ❌ UNUSABLE | ✅ USABLE | 0 blocking contradictions |
| **Token Count** | 7,250 | 2,650 (-63%) | Measure actual prompts |
| **Cognitive Load** | 9/10 | 4/10 (-56%) | Rule count × redundancy |
| **Quality** | 90% pass | ≥ 90% pass | Golden reference tests |
| **Performance** | Baseline | +40% faster | With caching enabled |

---

## 📋 Complete Issue List (9 Issues)

### WEEK 1: System Restoration (10h)

| Issue | Title | Priority | Effort | Files | Impact |
|-------|-------|----------|--------|-------|--------|
| **DEF-102** | Fix 5 Blocking Contradictions | 🔴 P0 | 3h | 3 files | System USABLE |
| **DEF-103** | Reduce Cognitive Load | 🟡 P1 | 2h | 1 file | -10% tokens |
| **DEF-126** | Transform Rules to Instructions | 🔴 P0 | 5h | 7 files | -39% tokens |

### WEEK 2: Architecture Changes (10h) ⚠️ HIGH RISK

| Issue | Title | Priority | Effort | Files | Impact |
|-------|-------|----------|--------|-------|--------|
| **DEF-104** | Reorganize Module Flow | 🟡 P1 | 3h | 2 files | Flow 4/10→8/10 |
| **DEF-106** | Create PromptValidator | 🟢 P2 | 2h | 1 new | Automated QA |
| **DEF-123** | Context-Aware Module Loading | 🟡 P1 | 5h | 2 files | -17% tokens |

### WEEK 3: Polish & Quality (6h)

| Issue | Title | Priority | Effort | Files | Impact |
|-------|-------|----------|--------|-------|--------|
| **DEF-105** | Add Visual Priority Badges | 🟢 P2 | 2h | 7 files | Scanability |
| **DEF-124** | Static Module Caching | 🟢 P2 | 2h | 1 file | +40% speed |
| **DEF-107** | Documentation & Tests | 🟢 P2 | 4h | 5 new | Maintainability |

---

## 🗺️ File Mapping (15 Files Total)

### Files to Modify (10 existing)

| File | Size | Issues | Changes | Risk |
|------|------|--------|---------|------|
| `error_prevention_module.py` | 262L | DEF-102, DEF-103 | +50L, -30L | MEDIUM |
| `semantic_categorisation_module.py` | 279L | DEF-102 | +20L | LOW |
| `arai_rules_module.py` | 128L | DEF-126 | +20L | MEDIUM |
| `con_rules_module.py` | 128L | DEF-126 | +20L | MEDIUM |
| `ess_rules_module.py` | 128L | DEF-126 | +20L | MEDIUM |
| `sam_rules_module.py` | 128L | DEF-126 | +20L | MEDIUM |
| `ver_rules_module.py` | 128L | DEF-126 | +20L | MEDIUM |
| `structure_rules_module.py` | 332L | DEF-126, DEF-105 | +45L | MEDIUM |
| `integrity_rules_module.py` | 314L | DEF-126, DEF-105 | +45L | MEDIUM |
| `prompt_orchestrator.py` | 414L | DEF-104, DEF-123, DEF-124 | +120L | **HIGH** |

### Files to Create (5 new)

| File | Size | Issues | Purpose |
|------|------|--------|---------|
| `prompt_validator.py` | ~150L | DEF-106 | Automated validation |
| `test_prompt_validator.py` | ~150L | DEF-107 | Validator tests |
| `test_rule_transformations.py` | ~200L | DEF-107 | Rule tone tests |
| `test_context_aware_loading.py` | ~150L | DEF-107 | Context tests |
| `prompt-quality-improvements.md` | ~500L | DEF-107 | Documentation |

**Total:** ~1,200 lines added/modified

---

## ⚠️ Risk Analysis Summary

### Risk Heatmap

| Issue | Technical Risk | Business Risk | Rollback | Overall |
|-------|---------------|---------------|----------|---------|
| DEF-102 | 7/10 | 6/10 | EASY | MEDIUM |
| DEF-103 | 3/10 | 2/10 | EASY | LOW |
| DEF-126 | 6/10 | 5/10 | MEDIUM | MEDIUM |
| DEF-104 | **8/10** | 7/10 | MEDIUM | **HIGH** ⚠️ |
| DEF-106 | 4/10 | 3/10 | EASY | LOW |
| DEF-123 | **8/10** | **8/10** | HARD | **HIGH** ⚠️ |
| DEF-105 | 2/10 | 1/10 | EASY | LOW |
| DEF-124 | 5/10 | 3/10 | EASY | MEDIUM |
| DEF-107 | 2/10 | 1/10 | N/A | LOW |

### Critical Risks

**HIGH RISK Issues (Require Extra Caution):**

1. **DEF-104** (Module Reordering)
   - **Risk:** 60% chance of dependency breaks (missing shared_state keys)
   - **Impact:** System unusable if module order breaks dependencies
   - **Mitigation:** Document dependencies BEFORE reordering, add validation
   - **Rollback:** git revert, 10 minutes

2. **DEF-123** (Context-Aware Loading)
   - **Risk:** 50% chance of wrong modules skipped
   - **Impact:** Quality drops if critical modules not loaded
   - **Mitigation:** Feature flag (default OFF), extensive testing
   - **Rollback:** Disable flag, 5 minutes

**Compound Risk:**
- DEF-104 + DEF-123 together = 10/10 severity
- **DO NOT deploy same day** - 3-day gap minimum

### Test Gates (6 Checkpoints)

| Gate | After | Validation | GO/NO-GO Criteria |
|------|-------|------------|-------------------|
| **#1** | DEF-102 | 10 golden definitions | ≥ 9/10 pass (90%) |
| **#2** | DEF-103, DEF-126 | Token count + quality | -49% tokens, ≥ 90% pass |
| **#3** | DEF-104 | Dependency validation | No KeyErrors, 40/40 pass |
| **#4** | DEF-123 | Context-aware testing | Token reduction ≥ 10%, quality ≥ 85% |
| **#5** | DEF-105, DEF-124 | Performance validation | +40% speed, visual badges present |
| **#6** | DEF-107 | Final validation | 100 definitions, ≥ 90% pass, -63% tokens |

---

## 🏗️ Architecture Impact

### Architecture Score: 7.2/10 (Good)

| Dimension | Before | After | Delta | Score |
|-----------|--------|-------|-------|-------|
| **Cohesion** | 7/10 | 8/10 | +1 | 8/10 |
| **Coupling** | 6/10 | 5/10 | -1 | 5/10 |
| **Testability** | 5/10 | 8/10 | +3 | 8/10 |
| **Maintainability** | 6/10 | 7/10 | +1 | 7/10 |
| **Scalability** | 7/10 | 8/10 | +1 | 8/10 |

### Key Architectural Changes

**Week 1:**
- ✅ Exception clauses added (error handling improvement)
- ✅ Rule tone transformation (UX improvement, no structural change)

**Week 2:** ⚠️ **MAJOR CHANGES**
- ⚠️ Module execution order changed (affects ALL prompts)
- ✅ Validator added (separation of concerns)
- ⚠️ Dynamic module loading (architectural shift)

**Week 3:**
- ✅ Visual hierarchy (presentation layer only)
- ✅ Caching added (performance optimization)
- ✅ Tests + docs (quality improvement)

### Technical Debt Assessment

| Category | Debt Removed | Debt Added | Net |
|----------|--------------|------------|-----|
| **Contradictions** | 5 blocking issues | 0 | **-5** ✅ |
| **Testing** | No validator | PromptValidator | **-1** ✅ |
| **Complexity** | 100+ concepts | 30 concepts | **-70** ✅ |
| **Dependencies** | 3 implicit | 5 documented | **+2** ⚠️ |
| **Caching** | No cache invalidation | Cache strategy needed | **+1** ⚠️ |

**Net Technical Debt:** **-73 points** (MAJOR IMPROVEMENT)

### Alignment with DEF-111

**Recommendation:** **Execute Plan B FIRST**, then DEF-111

**Rationale:**
- Plan B fixes prompt content (3 weeks)
- DEF-111 refactors architecture (18 weeks)
- No conflicts if Plan B goes first
- DEF-111 benefits from cleaner prompts (+$2,700 savings)

**Parallel Work:** Possible after Week 1 (low risk period)

---

## 📅 11-Day Implementation Timeline

### Week 1: System Restoration (4 days, 10h)

#### DAY 1 (Monday) - 2.5h
- **08:00-10:00** DEF-103: Categorize 42 patterns (2h)
- **10:00-11:30** DEF-102: Start contradiction fixes (1.5h)
- **Deliverable:** DEF-103 done, DEF-102 40% done

#### DAY 2 (Tuesday) - 3h
- **08:00-10:00** DEF-102: Finish contradictions (2h)
- **10:00-11:00** TEST GATE #1: Validate with 10 golden definitions
- **Deliverable:** DEF-102 done, staging validated

#### DAY 3 (Wednesday) - 2.5h
- **08:00-10:30** DEF-126: Transform ARAI, CON, ESS modules (2.5h)
- **Deliverable:** 3 of 7 modules transformed

#### DAY 4 (Thursday) - 3h
- **08:00-11:00** DEF-126: Transform SAM, VER, STR, INT modules (3h)
- **11:00-11:45** TEST GATE #2: Validate all 7 transformations
- **Deliverable:** Week 1 complete, -49% tokens

---

### Week 2: Architecture Changes (4 days, 10h) ⚠️ HIGH RISK

#### DAY 5 (Monday) - 2h
- **08:00-10:30** DEF-104: Start module reordering (2h)
- **Deliverable:** Module order changed, initial testing

#### DAY 6 (Tuesday) - 3h
- **08:00-09:15** DEF-104: Finish reordering + extensive testing
- **09:15-09:45** TEST GATE #3: Dependency validation
- **10:00-11:15** DEF-106: Create PromptValidator (1.5h)
- **Deliverable:** DEF-104 on staging, DEF-106 done

#### DAY 7 (Wednesday) - 3h ⚠️ HIGH RISK DAY
- **08:00-08:30** PRE-123 SAFETY BRIEFING
- **08:30-11:30** DEF-123: Implement context-aware loading (3h)
- **Feature flag:** Default OFF (disabled)
- **Deliverable:** DEF-123 implemented but disabled

#### DAY 8 (Thursday) - 2.5h
- **08:00-10:00** DEF-123: Enable flag + testing (2h)
- **10:00-10:30** TEST GATE #4: Context-aware validation
- **Deliverable:** DEF-123 validated, Week 2 complete

---

### Week 3: Polish & Quality (3 days, 6h)

#### DAY 9 (Monday) - 2h
- **08:00-10:00** DEF-105: Visual priority badges (2h)
- **10:00-11:30** DEF-124: Start static caching (1.5h)
- **Deliverable:** Visual badges live, caching 50% done

#### DAY 10 (Tuesday) - 2h
- **08:00-09:00** DEF-124: Finish caching + performance testing
- **09:00-11:00** DEF-107: Start tests + documentation (2h)
- **Deliverable:** DEF-124 validated, DEF-107 50% done

#### DAY 11 (Wednesday) - 2h FINAL DAY
- **08:00-10:00** DEF-107: Finish tests + documentation (2h)
- **10:00-11:00** TEST GATE #6: Final validation (100 definitions)
- **11:00-11:30** PRODUCTION DEPLOYMENT
- **Deliverable:** Plan B complete, production stable

---

## 🧪 Testing Strategy

### Golden Reference Test Suite

**Location:** `tests/fixtures/golden_definitions.json`

**Sample Size:** 10 definitions (baseline), 40 definitions (thorough), 100 definitions (final)

**Categories Covered:**
- 25% PROCES (activiteit, handeling)
- 25% TYPE (soort, categorie)
- 25% RESULTAAT (uitkomst, product)
- 25% EXEMPLAAR (specifiek geval)

**Pass Threshold:** ≥ 90% (same as baseline)

### Test Commands

```bash
# Unit tests (fast)
pytest tests/services/prompts/ -v

# Integration tests (with golden reference)
pytest tests/fixtures/ -v --tb=short

# Performance tests (with caching)
pytest tests/services/prompts/test_performance.py -v

# Full test suite (comprehensive)
pytest tests/ -v --cov=src/services/prompts --cov-report=html
```

### Test Gates Checklist

**GATE #1** (After DEF-102):
- [ ] 10 golden definitions pass
- [ ] 0 "is" contradictions
- [ ] 0 container term violations
- [ ] ESS-02 exception works correctly

**GATE #2** (After DEF-103 + DEF-126):
- [ ] Token count ≤ 4,500 (from 7,250)
- [ ] Forbidden patterns < 10 bullets (categorized)
- [ ] No "Toetsvraag:" in output
- [ ] Instructions are clear and actionable

**GATE #3** (After DEF-104):
- [ ] 40 definitions pass dependency validation
- [ ] No KeyErrors from missing shared_state
- [ ] ESS-02 appears before line 50
- [ ] Task metadata appears before line 20

**GATE #4** (After DEF-123):
- [ ] Token reduction ≥ 10% (with context-aware loading)
- [ ] Quality drops < 5% (vs flag OFF)
- [ ] Rich context: 14-16 modules loaded
- [ ] Minimal context: 6-8 modules loaded

**GATE #5** (After DEF-105 + DEF-124):
- [ ] Priority badges present (🔴 TIER 1, 🟡 TIER 2, 🟢 TIER 3)
- [ ] Performance +40% (with caching)
- [ ] Cache hits > 80% for static modules

**GATE #6** (Final):
- [ ] 100 definitions pass
- [ ] Token count ≤ 2,650 (from 7,250 = -63%)
- [ ] Quality ≥ 90% pass rate
- [ ] Performance +40% faster
- [ ] Cognitive load 4/10 (from 9/10)

---

## 🚨 Rollback Procedures

### Emergency Rollback (< 5 min)

**Scenario:** System unusable, critical failure

```bash
# 1. Disable feature flags
export ENABLE_CONTEXT_AWARE_LOADING=false

# 2. Revert to main branch
git checkout main
git pull

# 3. Redeploy
bash scripts/run_app.sh

# 4. Verify
pytest tests/smoke/ -v
```

**Recovery Time:** 5 minutes
**Data Loss:** None

### Selective Rollback (per issue)

| Issue | Rollback Complexity | Time | Procedure |
|-------|-------------------|------|-----------|
| DEF-102 | EASY | 5 min | `git revert <commit>` |
| DEF-103 | EASY | 5 min | `git revert <commit>` |
| DEF-126 | MEDIUM | 10 min | Revert 7 commits (one per module) |
| DEF-104 | MEDIUM | 10 min | Revert order, test dependencies |
| DEF-106 | EASY | 2 min | Remove validator call |
| DEF-123 | EASY | 2 min | Set flag to false |
| DEF-105 | EASY | 5 min | Revert visual changes |
| DEF-124 | EASY | 5 min | Disable caching |
| DEF-107 | N/A | N/A | Tests/docs don't affect runtime |

### Auto-Rollback Triggers

**Immediate Rollback (automated):**
- Prompt generation failure rate > 5%
- System errors > 10/hour
- Data corruption detected
- Quality drops > 20%

**24h Observation Period (manual decision):**
- Quality drops 10-20%
- User complaints > 5 tickets/day
- Performance degrades > 10%
- Token reduction < expected (but system works)

---

## 📦 Deliverables Checklist

### Week 1 Deliverables
- [ ] DEF-102: 3 files modified (contradiction fixes)
- [ ] DEF-103: 1 file modified (cognitive load reduction)
- [ ] DEF-126: 7 files modified (tone transformation)
- [ ] TEST GATE #1: Passed with ≥ 9/10
- [ ] TEST GATE #2: Passed with ≥ 90% + -49% tokens
- [ ] Staging deployment validated
- [ ] Linear issues updated (DEF-102, DEF-103, DEF-126 → Done)

### Week 2 Deliverables
- [ ] DEF-104: 2 files modified (flow reorganization)
- [ ] DEF-106: 1 new file (PromptValidator)
- [ ] DEF-123: 2 files modified (context-aware loading)
- [ ] TEST GATE #3: Passed (dependency validation)
- [ ] TEST GATE #4: Passed (context-aware validation)
- [ ] Feature flags configured (DEF-123 default OFF)
- [ ] Staging deployment validated
- [ ] Linear issues updated (DEF-104, DEF-106, DEF-123 → Done)

### Week 3 Deliverables
- [ ] DEF-105: 7 files modified (visual badges)
- [ ] DEF-124: 1 file modified (static caching)
- [ ] DEF-107: 5 new files (tests + docs)
- [ ] TEST GATE #5: Passed (performance validation)
- [ ] TEST GATE #6: Passed (final validation)
- [ ] Production deployment complete
- [ ] All 9 Linear issues → Done
- [ ] DEF-101 EPIC → Complete
- [ ] Documentation updated
- [ ] Lessons learned documented

---

## 🎓 Lessons Learned (Pre-Implementation)

### From Multiagent Analysis

1. **File mapping is critical** - Knowing exact line numbers prevents scope creep
2. **Risk analysis prevents surprises** - 75 risks identified, 73 mitigated
3. **Realistic timelines work** - 2.5h/day is sustainable, 8h/day is fantasy
4. **Architecture review catches debt** - Net -73 technical debt points
5. **Test gates enforce quality** - 6 checkpoints prevent regression

### Key Insights

1. **Week 2 is HIGH RISK** - DEF-104 + DEF-123 need 3-day gap
2. **Feature flags are essential** - Enable gradual rollout + easy rollback
3. **Golden reference testing is critical** - 90% pass threshold maintains quality
4. **Documentation pays off** - Dependency docs prevent DEF-104 failures
5. **Cognitive load matters** - 42 patterns → 5 categories reduces mental overhead

### Success Factors

1. ✅ **Phased approach** (3 weeks, 6 gates)
2. ✅ **Test coverage** (unit + integration + golden reference)
3. ✅ **Feature flags** (gradual rollout, easy rollback)
4. ✅ **Documentation** (dependencies, architecture, rollback)
5. ✅ **Realistic timeline** (26h over 11 days, not 3 days)

---

## 🚀 Next Steps

### TODAY (Before Starting)
1. [ ] Stakeholder approval for Plan B
2. [ ] Confirm feature branch: `feature/def-101-plan-b-quality`
3. [ ] Review risk analysis (focus on Week 2)
4. [ ] Set up staging environment
5. [ ] Configure feature flags (DEF-123, DEF-124)

### MONDAY (Start Week 1)
1. [ ] Morning standup (review Plan B)
2. [ ] Check out feature branch
3. [ ] Start DEF-103 (categorize patterns)
4. [ ] Commit + push EOD

### ONGOING
- [ ] Daily standups (15 min)
- [ ] Update Linear issues after each completion
- [ ] Run test gates at specified checkpoints
- [ ] Document progress in commit messages
- [ ] Monitor staging deployment

---

## 📚 Reference Documents

**Primary:**
- `DEF-101-TECHNICAL-COMPLEXITY-ANALYSIS.md` - Technical deep-dive
- `DEF-101-ALTERNATIVE-SEQUENCING-PLANS.md` - Plan A/B/C comparison
- `DEF-101-SEQUENCING-INSIGHTS.md` - Strategic insights
- `PLAN-B-FILE-MAPPING.md` - Exact file locations (Explore agent)
- `PLAN-B-RISK-ANALYSIS.md` - 75 risks identified (Debug-Specialist agent)
- `PLAN-B-EXECUTION-TIMELINE.md` - Hour-by-hour breakdown (Plan agent)
- `PLAN-B-ARCHITECTURE-REVIEW.md` - Architecture impact (Code-Reviewer agent)

**Supporting:**
- `CONSENSUS_IMPLEMENTATION_PLAN.md` - Original Plan B specification
- `DEF-101-IMPLEMENTATION-GUIDE.md` - Implementation guide
- `PROMPT_COMPREHENSIVE_ANALYSIS_AND_IMPROVEMENT_PLAN.md` - Analysis basis

**Testing:**
- `tests/fixtures/golden_definitions.json` - Golden reference suite
- `tests/services/prompts/` - Existing test patterns

---

## ✅ Success Criteria

**Plan B is successful if:**

1. ✅ **System is USABLE** (0 blocking contradictions)
2. ✅ **Token reduction ≥ 60%** (target: -63%, 7250 → 2650)
3. ✅ **Quality maintained** (≥ 90% golden reference pass rate)
4. ✅ **Performance improved** (≥ 30% faster with caching)
5. ✅ **Cognitive load reduced** (≤ 5/10, from 9/10)
6. ✅ **All 6 test gates pass**
7. ✅ **Production stable** (no rollbacks needed)
8. ✅ **Documentation complete** (tests + architecture docs)

**Additional Success Indicators:**
- User satisfaction ≥ 80%
- Support tickets decrease ≥ 50%
- Development velocity maintained (no regression)
- DEF-111 execution unblocked (parallel work feasible)

---

## 🎉 Conclusion

Plan B is a **comprehensive, realistic, and well-analyzed** implementation plan for DEF-101 EPIC. With 4 multiagent analyses, 6 test gates, and detailed risk mitigation, this plan balances **speed** (11 days) with **quality** (90%+ pass rate) and **safety** (feature flags + rollback procedures).

**Recommendation:** ✅ **APPROVE and BEGIN EXECUTION**

**Confidence:** 85% (High confidence with identified risks mitigated)

---

**Document Status:** ✅ COMPLETE
**Ready for:** Stakeholder approval → Execution
**Next Action:** Review with team, obtain approval, start Day 1

🤖 Generated with [Claude Code](https://claude.com/claude-code) using multiagent ultrathink analysis

Co-Authored-By: Claude <noreply@anthropic.com>
