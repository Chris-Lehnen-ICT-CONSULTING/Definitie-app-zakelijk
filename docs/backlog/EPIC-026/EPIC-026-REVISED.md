---
aangemaakt: 2025-09-30
bijgewerkt: 2025-10-03
applies_to: definitie-app@current
canonical: true
completion: 0%
id: EPIC-026
last_verified: 2025-10-03
owner: code-architect
prioriteit: P2
status: pending-approval
target_release: v2.3
revision: 2.0
revised_by: 5-agent-analysis-2025-10-03
vereisten:
- REQ-091
---

# EPIC-026: God Object Refactoring (Architectural Debt Resolution)

**🔄 REVISION 2.0** - Based on comprehensive 5-agent analysis (2025-10-03)

**⚠️ CRITICAL CHANGES FROM v1.0:**
- Timeline: 11-16 days → **10-12 weeks** (Hybrid Staged Approach)
- Cost: €12.8k → **€43-67k** (includes mandatory Phase 0)
- User Stories: 13 → **17 stories** (added Phase 0 + missing orchestrators)
- Risk Profile: 3 documented → **17 identified** (6 critical)
- Scope: 3 files → **2 files prioritized** (definitie_repository deferred)

---

## Epic Overview

**ID:** EPIC-026

> **Consolidatie-update (2025-10-03):** EPIC-026 bundelt nu alle refactoringscope uit EPIC-010, EPIC-012, EPIC-020-PHOENIX en losstaande stories. Onderstaande mapping maakt zichtbaar welke verhalen zijn opgenomen.

| Oorspronkelijk epic | Gebruikersverhalen nu onder EPIC-026 |
|---|---|
| EPIC-010 Context Flow Refactoring | US-171, US-172 |
| EPIC-012 Legacy Orchestrator Refactoring | US-061, US-072, US-074, US-152, US-159, US-170, US-175 |
| EPIC-020 Operation Phoenix | US-201 t/m US-212 |
| EPIC-004 UI (refactor story) | US-177 |

**Titel:** God Object Refactoring (Architectural Debt Resolution)
**Status:** PENDING APPROVAL (Revision 2.0)
**Priority:** P2 (downgraded from P1 - not blocking, important)
**Created:** 2025-09-30
**Revised:** 2025-10-03
**Owner:** Code Architect Team
**Target Release:** v2.3
**Predecessor:** EPIC-025 (Brownfield Cleanup)

**Revision Rationale:**
Multi-agent analysis (5 agents, ~200 pages) revealed:
1. Original 11-16 day estimate was based on "file splitting" assumption
2. Reality: Architectural refactoring with 880 LOC hidden orchestrators
3. Test coverage crisis: 0-5% coverage on god objects (vs assumed 73 tests)
4. 6 critical risks undocumented in v1.0

---

## Problem Statement

### Verified God Objects (2 of 3)

US-427 discovery and subsequent code analysis revealed that **2 critical files** (4,318 LOC) suffer from **God Object anti-pattern**:

#### ✅ Confirmed God Objects

| File | LOC | Complexity | Tests | Verdict |
|------|-----|------------|-------|---------|
| `definition_generator_tab.py` | 2,525 | 116 (CRITICAL) | 1 test | ☢️ **TRUE god object** |
| `tabbed_interface.py` | 1,793 | 59 (HIGH) | 0 tests | 🔴 **TRUE god object** |

#### ❌ False Positive (Deferred)

| File | LOC | Complexity | Tests | Verdict |
|------|-----|------------|-------|---------|
| `definitie_repository.py` | 1,815 | 4.7 (NORMAL) | 51 tests | ✅ **Well-structured, DEFER** |

**Deferral Rationale:** definitie_repository.py has:
- Low complexity (4.7 avg cyclomatic complexity)
- Clear boundaries (READ/WRITE/BULK separation)
- Excellent test coverage (100%, 51 tests)
- **Not a god object** - postpone to future epic

---

### Hidden Complexity Discovered

**880 LOC Hidden Orchestrators** (not in original scope):

1. **Generation Orchestrator** (380 LOC god method)
   - Location: `tabbed_interface.py::_handle_definition_generation()`
   - Complexity: 10-step workflow, 15+ state mutations, 6 early exits
   - Services coordinated: 5+ (Definition, Regeneration, Document, Category, Checker)
   - **Impact:** CRITICAL - this IS the application's core workflow

2. **Regeneration Orchestrator** (500 LOC across 8 methods)
   - Location: `definition_generator_tab.py::_trigger_regeneration_with_category()` + 7 helpers
   - Complexity: 3 regeneration modes (direct/manual/keep), category change analysis
   - Hardcoded rules: 4 category pairs with special handling
   - **Impact:** HIGH - category change is key feature

**610 LOC Hidden Services** (in UI layer):
- OntologicalCategoryService (260 LOC) - category determination logic
- DocumentContextService (350 LOC) - document processing logic

**Total hidden complexity:** 1,490 LOC business logic masquerading as UI code

---

### Test Coverage Crisis

**Current Coverage State:**

```
definition_generator_tab.py:  2,525 LOC,  1 test,  ~5% coverage  🔴 CRITICAL
tabbed_interface.py:          1,793 LOC,  0 tests,  0% coverage  ☢️ CATASTROPHIC

Combined god objects:         4,318 LOC,  1 test,  ~0.02% coverage
```

**Regression Risk Scores:**
- definition_generator_tab: **2,847** (CRITICAL - dangerous to refactor)
- tabbed_interface: **3,156** (CATASTROPHIC - suicidal without tests)

**Original assumption:** "Test coverage >= 73 tests"
**Reality:** 73 tests exist in CODEBASE, but 0-1 tests for god objects being refactored

---

### Impact

**Technical Debt:**
- 4,318 LOC unmaintainable code (380 LOC god method!)
- 880 LOC orchestrators hidden in UI layer
- 208 occurrences of `st.session_state` (coupling)
- 0% test coverage (regression risk)

**Business Impact:**
- Blocked feature development (cannot safely extend)
- High regression risk (changes cascade unpredictably)
- Long debugging cycles (complex state management)
- Developer frustration (code is "scary to touch")

**Root Cause:**
Not just file size, but:
1. **Business logic leakage** into UI layer (architecture violation)
2. **Hardcoded rules** (not data-driven)
3. **Missing orchestration layer** (god methods do everything)

---

## Business Value

### Revised ROI Analysis

**Original Claim (v1.0):**
- Cost: €12.8k (11-16 days)
- ROI: 4-6 month payback via 40% velocity gain
- Benefit: +200% maintainability, zero regression risk

**Reality Check (v2.0):**

| Scenario | Timeline | Cost | Velocity Gain | ROI (3yr) | Realistic? |
|----------|----------|------|---------------|-----------|------------|
| v1.0 Claim | 16 days | €12.8k | 40% | +341% | ❌ NO |
| Optimistic | 10 weeks | €40k | 40% | +112% | ⚠️ MAYBE |
| **Realistic** | **12 weeks** | **€67k** | **20%** | **+89%** | ✅ **YES** |
| Conservative | 14 weeks | €67k | 10% | -13% | ⚠️ RISK |

**Revised Business Case (Hybrid Approach):**
- **Investment:** €67k (12 weeks: Phase 0 + Phase 1 + Phase 2)
- **Payback:** 9-12 months (conservative 20% velocity gain)
- **3-year ROI:** +89% to +157% (positive)
- **Risk-adjusted:** MEDIUM (acceptable with Phase 0)

---

### Direct Benefits (Evidence-Based)

#### 1. Code Quality (Measurable)
- **Before:** 2,525 LOC file, complexity 116
- **After:** Multiple files <500 LOC, complexity <10 each
- **Metric:** Maintainability Index (MI) from 20 → 70 (industry standard)
- **Evidence:** ✅ File size reduction is quantifiable

#### 2. Test Coverage (Critical)
- **Before:** 0-1 tests for 4,318 LOC (0.02%)
- **After:** 436+ tests (85% coverage)
- **Metric:** Branch coverage >= 85%
- **Evidence:** ✅ Phase 0 Test Recovery Plan

#### 3. Development Velocity (Measured)
- **Baseline:** Establish in Phase 1 (features/week)
- **Target:** 15-20% improvement (realistic, not 40%)
- **Metric:** Track feature completion rate for 3 months post-refactor
- **Evidence:** ⚠️ Will be measured, not assumed

#### 4. Regression Risk (Reduced)
- **Before:** HIGH (0% test coverage)
- **After:** LOW (85% coverage + integration tests)
- **Metric:** Regression bugs per month (track for 6 months)
- **Evidence:** ✅ Phase 0 addresses directly

---

### Risk Reduction

| Risk | Before Epic | After Epic | Mitigation |
|------|-------------|------------|------------|
| **Breaking changes** | CRITICAL | LOW | Phase 0 tests + golden baseline |
| **Business logic loss** | CRITICAL | MEDIUM | Business logic extraction doc |
| **State management** | CRITICAL | MEDIUM | State audit + schema |
| **Single developer** | CRITICAL | MEDIUM | Backup dev + knowledge transfer |
| **Production regression** | HIGH | LOW | Golden baseline (42 definitions) |

---

## Scope

### ✅ In Scope (Hybrid Staged Approach - 12 weeks)

#### **Phase 0: Test Foundation** (5 weeks, €25k) - MANDATORY

**Week 1: Test Infrastructure**
- Set up Streamlit test harness (pytest-playwright)
- Create golden master testing framework
- Build async test patterns
- **Deliverable:** Test infrastructure operational

**Week 2-3: Critical Path Tests**
- 368 tests for orchestrators (generation + regeneration workflows)
- 50+ integration test scenarios (was 10 in v1.0)
- State mutation tests (15+ mutations per workflow)
- **Deliverable:** 368 tests, 70%+ coverage

**Week 4: Coverage Gap Tests**
- 68 tests for UI rendering, navigation, error paths
- Edge case coverage (category changes, duplicates)
- **Deliverable:** 85%+ total coverage

**Week 5: Validation & Refinement**
- Fix flaky tests (<5% flakiness threshold)
- Performance baseline benchmarks
- Golden baseline export (42 definitions)
- **Deliverable:** 436+ tests, GREEN suite, golden baseline

**Gate:** Cannot proceed to Phase 1 without 85% coverage + 436 tests

---

#### **Phase 1: Repository Safe Refactor** (3 weeks, €18k)

**REVISED SCOPE:** Extract definitie_repository ONLY (deferred from critical path due to low priority)

**Week 6: Extract READ Service**
- Move all read operations to `definitie_repository_read.py`
- Maintain backward compatibility (facade pattern)
- **Tests:** 25 tests for READ service

**Week 7: Extract WRITE Service**
- Move all write operations to `definitie_repository_write.py`
- Transaction handling preserved
- **Tests:** 15 tests for WRITE service

**Week 8: Extract BULK Service**
- Move bulk operations to `definitie_repository_bulk.py`
- Performance optimization maintained
- **Tests:** 11 tests for BULK service

**Deliverable:** definitie_repository split into 3 services, all 51+ tests passing

**Gate:** GO to Phase 2 only if velocity improvement >= 10% observed

---

#### **Phase 2: Critical Path UI** (4 weeks, €24k) - OPTIONAL

**REVISED SCOPE:** tabbed_interface + definition_generator_tab orchestrators

**Week 9-10: Extract Generation Orchestrator**
- Extract 380 LOC god method to `GenerationOrchestrator` service
- Clean async patterns (no asyncio.run nesting)
- 7-step workflow preserved
- **Tests:** 95%+ coverage for orchestrator

**Week 11-12: Extract Regeneration Orchestrator**
- Extract 500 LOC regeneration logic to `RegenerationOrchestrator` service
- 3 modes (direct/manual/keep) implemented
- Category change rules → config-driven
- **Tests:** 90%+ coverage for orchestrator

**Week 13: Thin UI Layer**
- Reduce tabbed_interface.py to <400 LOC
- Reduce definition_generator_tab.py to <800 LOC
- Remove all business logic from UI
- **Tests:** All integration tests GREEN

**Deliverable:** UI thinned by 74%, orchestrators extracted, all tests passing

**Gate:** GO to production only if golden baseline 100% match

---

### ❌ Out of Scope

**Deferred to future epics:**
- ~~definitie_repository refactoring~~ → Move to Phase 1 (low priority)
- web_lookup_service refactoring (2-3 weeks)
- validation_orchestrator_v2 refactoring (2-3 weeks)
- Performance optimization (separate epic)
- New features (no functionality changes)
- UI redesign (Streamlit structure unchanged)
- Database migration (SQLite schema unchanged)

---

### Scope Flexibility

**Decision Framework:**

```yaml
minimum_viable:
  scope: "Phase 0 only (tests)"
  duration: 5 weeks
  cost: €25k
  value: "Tests protect existing code, no refactoring"
  trigger: "If stakeholders reject Phase 1"

hybrid_staged:
  scope: "Phase 0 + Phase 1 (repository)"
  duration: 8 weeks
  cost: €43k
  value: "30% of epic value, LOW risk"
  trigger: "Default commitment"

hybrid_full:
  scope: "Phase 0 + Phase 1 + Phase 2 (UI)"
  duration: 12 weeks
  cost: €67k
  value: "70% of epic value, MEDIUM risk"
  trigger: "If Phase 1 shows >= 10% velocity gain"

full_scope:
  scope: "All 5 god objects (add 4-8 weeks)"
  duration: 16-20 weeks
  cost: €100-150k
  value: "100% value, MEDIUM-HIGH risk"
  trigger: "If hybrid successful + roadmap requires it"
```

---

## Goals & Success Criteria

### Phase 0 Success Criteria (MANDATORY)

**Gate 1: Week 5 Checkpoint**

- [ ] **Test count:** >= 436 tests created
- [ ] **Coverage:** >= 85% for god objects (definition_generator_tab, tabbed_interface)
- [ ] **Flaky tests:** < 5% flakiness rate
- [ ] **Integration tests:** >= 50 scenarios (not 10!)
- [ ] **Golden baseline:** 42 definitions exported with validation results
- [ ] **Test infrastructure:** Streamlit test harness operational
- [ ] **Performance baseline:** Benchmarks recorded

**Decision:** GO to Phase 1 only if ALL criteria met

**Abort scenarios:**
- Coverage < 70% after Week 5 → Extend Phase 0 by 2 weeks OR abort epic
- Coverage < 60% after Week 7 → Abort epic, accept technical debt

---

### Phase 1 Success Criteria

**Gate 2: Week 8 Checkpoint**

- [ ] **Service extraction:** definitie_repository split into READ/WRITE/BULK
- [ ] **Tests passing:** All 51 existing tests + 51 new service tests (102 total)
- [ ] **No breaking changes:** All 20+ importers still work
- [ ] **Backward compatibility:** Facade pattern maintains API
- [ ] **Velocity baseline:** Feature completion rate measured (baseline established)
- [ ] **Code review:** Architecture team approval

**Decision:** GO to Phase 2 only if:
1. All tests GREEN
2. Velocity improvement >= 10% observed (measure over 2 weeks)
3. Stakeholder approves Phase 2 budget (€24k)

**Abort scenarios:**
- Velocity improvement < 5% → STOP, focus on features for 6 months
- Velocity degrades → Rollback, investigate root cause

---

### Phase 2 Success Criteria

**Gate 3: Week 13 Checkpoint**

- [ ] **Generation Orchestrator:** 380 LOC god method extracted to service
- [ ] **Regeneration Orchestrator:** 500 LOC extracted to service
- [ ] **UI thinned:** tabbed_interface <400 LOC, generator_tab <800 LOC
- [ ] **Golden baseline match:** 100% match for all 42 definitions
- [ ] **Integration tests:** All 50+ scenarios GREEN
- [ ] **Async patterns:** Clean (no asyncio.run nesting)
- [ ] **State management:** Centralized via SessionStateManager
- [ ] **Performance:** Benchmarks >= baseline (no degradation)

**Decision:** GO to production only if:
1. Golden baseline 100% match
2. All integration tests GREEN
3. Performance maintained

**Abort scenarios:**
- Golden baseline < 95% match → STOP deployment, debug
- Integration tests > 2 failures → Rollback to Week 12

---

### Quantitative Targets (Revised)

| Metric | Baseline | Target (Hybrid) | Validation |
|--------|----------|-----------------|------------|
| **Max file size** | 2,525 LOC | <800 LOC (74% reduction) | `find src -exec wc -l` |
| **God method size** | 380 LOC | <50 LOC (87% reduction) | Code review |
| **Test count** | 1 test | 436+ tests | pytest --count |
| **Test coverage** | 0.02% | 85%+ | pytest --cov |
| **God Object count** | 2 | 0 (UI thinned) | Architecture review |
| **Circular dependencies** | Unknown | 0 | Import graph check |
| **Flaky tests** | N/A | <5% | CI metrics |
| **Regression bugs** | Baseline | <1/month | Track 6 months |

---

## Timeline

### Duration: 8-12 weeks (Hybrid Staged Approach)

**Committed:** 8 weeks (Phase 0 + Phase 1)
**Optional:** +4 weeks (Phase 2, if Phase 1 successful)
**Maximum:** 14 weeks (with 2-week contingency buffer)

---

### Detailed Timeline

#### **Phase 0: Test Foundation** (Week 1-5)

```
Week 1: Test Infrastructure Setup
├─ Day 1-2: pytest-playwright setup, Streamlit test harness
├─ Day 3-4: Golden master framework, async test patterns
└─ Day 5: Test 10 integration scenarios (proof of concept)

Week 2: Critical Path Tests (Generation)
├─ Day 6-7: 150 tests for generation orchestrator (380 LOC god method)
├─ Day 8-9: 100 tests for category determination (260 LOC)
└─ Day 10: 50 tests for document context (350 LOC)

Week 3: Critical Path Tests (Regeneration)
├─ Day 11-12: 118 tests for regeneration orchestrator (500 LOC)
├─ Day 13-14: Edge cases, error paths
└─ Day 15: Integration tests (20 scenarios)

Week 4: Coverage Gaps
├─ Day 16-17: 68 UI tests (rendering, navigation, state)
├─ Day 18-19: 30 integration tests (duplicate check, validation)
└─ Day 20: Mutation testing (validate tests catch bugs)

Week 5: Validation & Golden Baseline
├─ Day 21-22: Fix flaky tests (<5% threshold)
├─ Day 23: Performance benchmarks
├─ Day 24: Export golden baseline (42 definitions)
└─ Day 25: CHECKPOINT - Gate 1 review
```

**Deliverable:** 436+ tests, 85%+ coverage, golden baseline

---

#### **Phase 1: Repository Safe Refactor** (Week 6-8)

```
Week 6: Extract READ Service
├─ Day 26-27: Move read methods to definitie_repository_read.py
├─ Day 28: Create 25 tests for READ service
├─ Day 29: Integration testing
└─ Day 30: Code review + merge

Week 7: Extract WRITE Service
├─ Day 31-32: Move write methods to definitie_repository_write.py
├─ Day 33: Create 15 tests for WRITE service
├─ Day 34: Transaction testing
└─ Day 35: Code review + merge

Week 8: Extract BULK Service + Validation
├─ Day 36-37: Move bulk methods to definitie_repository_bulk.py
├─ Day 38: Create 11 tests for BULK service
├─ Day 39: Full regression testing (102 tests)
└─ Day 40: CHECKPOINT - Gate 2 review, measure velocity
```

**Deliverable:** definitie_repository split, 102 tests passing, velocity measured

**Decision Point:** Continue to Phase 2? (Requires >= 10% velocity gain + budget approval)

---

#### **Phase 2: Critical Path UI** (Week 9-13) - OPTIONAL

```
Week 9-10: Extract Generation Orchestrator
├─ Day 41-43: Extract 380 LOC god method to service
├─ Day 44-45: Clean async patterns, 7-step workflow
├─ Day 46-48: 150 tests for orchestrator (95% coverage)
└─ Day 49-50: Integration testing, golden baseline validation

Week 11-12: Extract Regeneration Orchestrator
├─ Day 51-53: Extract 500 LOC regeneration logic to service
├─ Day 54-55: 3 modes (direct/manual/keep), config-driven rules
├─ Day 56-58: 118 tests for orchestrator (90% coverage)
└─ Day 59-60: Integration testing, state migration validation

Week 13: Thin UI Layer + Validation
├─ Day 61-62: Reduce tabbed_interface to <400 LOC
├─ Day 63: Reduce generator_tab to <800 LOC
├─ Day 64: Full regression suite (50+ integration scenarios)
└─ Day 65: CHECKPOINT - Gate 3 review, golden baseline 100% match
```

**Deliverable:** UI thinned by 74%, orchestrators extracted, golden baseline match

**Decision Point:** Deploy to production? (Requires 100% golden baseline match)

---

### Milestones

| Week | Milestone | Gate | Criteria |
|------|-----------|------|----------|
| **Week 5** | Phase 0 Complete | Gate 1 | 436 tests, 85% coverage |
| **Week 8** | Phase 1 Complete | Gate 2 | 102 tests, velocity >=10% |
| **Week 13** | Phase 2 Complete | Gate 3 | Golden baseline 100% match |
| **Week 14** | Production Deploy | Final | All tests GREEN, no regressions |

---

### Contingency Timeline

**Best Case:** 10 weeks (Phase 0: 4 weeks, Phase 1: 3 weeks, Phase 2: 3 weeks)
**Likely Case:** 12 weeks (as planned)
**Worst Case:** 14 weeks (2-week buffer for Phase 0 issues)
**Abort Case:** 16 weeks (if > 14 weeks, abort and deliver what's complete)

---

## User Stories

### Phase 0: Test Foundation (5 stories, 5 weeks)

- **US-640:** Set up Test Infrastructure (Test Engineer, 1w)
  - pytest-playwright, Streamlit harness, golden master framework
- **US-454:** Create Generation Orchestrator Tests (Test Engineer, 2w)
  - 368 tests for generation + category + document workflows
- **US-455:** Create Regeneration Orchestrator Tests (Test Engineer, 1w)
  - 118 tests for regeneration workflows
- **US-456:** Create Coverage Gap Tests (Test Engineer, 0.5w)
  - 68 tests for UI, edge cases, error paths
- **US-457:** Validate & Create Golden Baseline (Test Engineer, 0.5w)
  - Fix flaky tests, export 42 definitions baseline

---

### Phase 1: Repository Refactor (3 stories, 3 weeks)

- **US-444:** Extract READ Service (Code Architect, 1w)
  - Move read methods to definitie_repository_read.py, 25 tests
- **US-445:** Extract WRITE Service (Code Architect, 1w)
  - Move write methods to definitie_repository_write.py, 15 tests
- **US-446:** Extract BULK Service (Code Architect, 1w)
  - Move bulk methods to definitie_repository_bulk.py, 11 tests

---

### Phase 2: Critical Path UI (4 stories, 4 weeks) - OPTIONAL

- **US-447:** Extract Generation Orchestrator (Code Architect, 2w)
  - Extract 380 LOC god method, 150 tests, 95% coverage
- **US-458:** Extract Regeneration Orchestrator (Code Architect, 2w)
  - Extract 500 LOC regeneration logic, 118 tests, 90% coverage
- **US-451:** Thin UI Layer (Code Architect, 0.5w)
  - Reduce UI files by 74%, remove business logic
- **US-453:** Final Validation & Review (Code Architect, 0.5w)
  - Golden baseline 100% match, full regression

---

### Phase 1 (Design - REMOVED from new structure)

**Rationale:** Design work already completed in EPIC-026 Phase 1:
- ✅ 3 responsibility maps exist (Day 1-2 analysis)
- ✅ RECOMMENDATION.md (9-week extraction plan)
- ✅ BUSINESS_LOGIC_EXTRACTION_PLAN.md (comprehensive)

**No need to repeat design phase - proceed directly to Phase 0 (tests)**

---

### Total User Stories: 15 stories

**Phase 0:** 5 stories (5 weeks)
**Phase 1:** 3 stories (3 weeks)
**Phase 2:** 4 stories (4 weeks) - optional
**Removed:** 3 design stories (already complete)

---

## Dependencies

### External Prerequisites (Must complete before start)

- ✅ **EPIC-025 Sprint 1 complete** (US-426, US-428 done)
- ✅ **Phase 1 Design complete** (responsibility maps, RECOMMENDATION.md)
- ✅ **US-427 coverage baseline** established (73 tests documented)
- ⚠️ **5-agent analysis reviewed** (stakeholders read this revision)

---

### Internal Prerequisites (Week 0 - Before Phase 0)

**Critical (Must complete before GO decision):**

1. **Stakeholder Approval**
   - [ ] Phase 0 approved (5 weeks, €25k)
   - [ ] Hybrid Staged Approach accepted (8-12 weeks, €43-67k)
   - [ ] Timeline realistic (not 11-16 days)
   - [ ] Risk profile acceptable (6 critical risks identified)

2. **Resource Allocation**
   - [ ] Test engineer assigned (5 weeks full-time, Phase 0)
   - [ ] Code architect available (7 weeks, Phase 1-2)
   - [ ] Backup developer identified (bus factor mitigation)

3. **Technical Preparation**
   - [ ] Business logic extraction document created (1 week)
   - [ ] State audit completed (208 st.session_state usages inventoried)
   - [ ] Git tagging infrastructure set up (automated hooks)
   - [ ] Golden baseline directory created (`data/golden_baseline_epic026/`)

4. **Knowledge Transfer**
   - [ ] Backup developer onboarded (shadow Week 0)
   - [ ] Architecture decision records (ADR) template created
   - [ ] Weekly review cadence established

**Gate 0 (Week 0 End):** Cannot start Phase 0 without ALL prerequisites complete

---

### Per-Phase Dependencies

**Phase 1 depends on:**
- [ ] Phase 0 complete (436 tests, 85% coverage)
- [ ] Gate 1 passed (all Phase 0 criteria met)
- [ ] Integration test suite GREEN

**Phase 2 depends on:**
- [ ] Phase 1 complete (repository refactored)
- [ ] Velocity improvement >= 10% measured
- [ ] Stakeholder approves Phase 2 budget (€24k)
- [ ] Gate 2 passed (all Phase 1 criteria met)

---

### Blocks (What this epic unlocks)

**Immediate (after Phase 0):**
- Safe refactoring of ANY module (test safety net)
- CI/CD pipeline improvements (test automation)

**After Phase 1:**
- Database schema changes (repository layer isolated)
- New data sources (clean repository interface)
- Parallel repository work (clear service boundaries)

**After Phase 2:**
- UI redesign (business logic decoupled)
- New workflows (orchestrators are services)
- Feature flags (orchestrators are injectable)

---

## Risks & Mitigation

### Risk Summary

**Total Risks Identified:** 17 (was 3 in v1.0)

**Risk Distribution:**
- 🔴 **CRITICAL:** 6 risks (Phase 0 mandatory to mitigate)
- 🟠 **HIGH:** 5 risks (mitigations in Phase 0-1)
- 🟡 **MEDIUM:** 6 risks (monitor & mitigate)

**Residual Risk (after mitigations):** MEDIUM (acceptable)

---

### Critical Risks (🔴 Require Phase 0)

#### **R1: Breaking Changes During Extraction**

**Likelihood:** HIGH (without Phase 0) → MEDIUM (with Phase 0)
**Impact:** CRITICAL (application breaks, features fail)

**Root Cause:**
- 0% test coverage on tabbed_interface.py
- 1 test for definition_generator_tab.py (2,525 LOC)
- 380 LOC god method with 15 state mutations, 6 early exits

**Original Mitigation (v1.0):** "Test after each step" ❌ INSUFFICIENT (no tests exist!)

**Enhanced Mitigation (v2.0):**
1. ✅ **Phase 0 mandatory:** 436 tests before any refactoring
2. ✅ **Golden master testing:** Record current behavior, compare post-refactor
3. ✅ **Integration tests:** 50+ scenarios (not 10)
4. ✅ **Mutation testing:** Validate tests catch bugs
5. ✅ **Staged rollout:** Feature flag, parallel run for 1 week

**Contingency:** If tests fail post-refactor → Git rollback to last checkpoint

---

#### **R9: Business Logic Loss During Extraction** (NEW in v2.0)

**Likelihood:** HIGH (70%)
**Impact:** CRITICAL (lost domain knowledge, silent bugs)

**Root Cause:**
- 880 LOC orchestrators contain implicit business rules
- Hardcoded category change logic (not documented)
- 6-step ontological protocol (no workflow diagram)
- Regeneration modes (3 modes, decision tree in code)

**Mitigation:**
1. ✅ **Business logic extraction doc** (Week 0, before Phase 0)
   - Extract ALL hardcoded rules from orchestrators
   - Create decision trees for workflows
   - Document implicit assumptions
2. ✅ **Domain expert review:** Legal/compliance validation
3. ✅ **Golden master testing:** Record behavior for all 42 definitions
4. ✅ **Config-driven rules:** Move hardcoded rules to YAML

**Deliverable:** `docs/business-logic/EPIC-026-extracted-rules.md` (Week 0)

**Contingency:** If logic is lost → Silent bugs in production, months to debug

---

#### **R10: Test Coverage Catastrophe** (NEW in v2.0)

**Likelihood:** CERTAIN (100% without Phase 0)
**Impact:** CRITICAL (blind refactoring, guaranteed regressions)

**Current State:**
```
tabbed_interface.py:         0 tests,  1,793 LOC  (Regression Risk: 3,156 ☢️)
definition_generator_tab.py: 1 test,   2,525 LOC  (Regression Risk: 2,847 🔴)
```

**Mitigation:**
✅ **Phase 0 Test Recovery Plan (5 weeks, 436 tests)**
- Week 1: Infrastructure (pytest-playwright, golden master)
- Week 2-3: Critical path tests (368 tests for orchestrators)
- Week 4: Coverage gaps (68 tests for UI)
- Week 5: Validation (fix flaky tests, golden baseline)

**Success Criteria:** 85%+ coverage, <5% flaky tests

**Contingency:**
- If coverage < 70% after Week 5 → Extend Phase 0 by 2 weeks
- If coverage < 60% after Week 7 → Abort epic, accept technical debt

---

#### **R12: Single Developer (Bus Factor = 1)** (NEW in v2.0)

**Likelihood:** HIGH (70% for 12-week project)
**Impact:** CRITICAL (project failure if developer leaves)

**Evidence:**
- 5 contributors ever, recent commits dominated by 1-2 authors
- Ownership: code-architect agent (single role)
- No pair programming or code review process mentioned

**Mitigation:**
1. ✅ **Backup developer onboarded** (Week 0, shadow Phase 0)
2. ✅ **Knowledge transfer:** Weekly ADRs, documentation reviews
3. ✅ **Mandatory code review:** No self-approvals
4. ✅ **Contingency plan:** If unavailable >3 days → Pause project

**Abort Trigger:** If primary developer leaves at Week 8 → Options:
- Pause, find replacement (2-4 weeks hiring + onboarding)
- Rollback to last checkpoint
- Cancel epic, accept technical debt

---

#### **R17: State Migration Errors** (NEW in v2.0)

**Likelihood:** HIGH (70%)
**Impact:** CRITICAL (broken workflows, data loss)

**Root Cause:**
- 208 occurrences of `st.session_state` across 28 files
- 15+ state mutations in generation orchestrator alone
- No schema validation (what keys are valid? what types?)

**Mitigation:**
1. ✅ **State audit** (Week 0): Inventory all 208 usages
2. ✅ **State schema:** Create `config/session_state_schema.yaml`
3. ✅ **Enforce validation:** Runtime checks in SessionStateManager
4. ✅ **Gradual migration:** Add schema to current code before refactoring

**Deliverable:** `docs/technical/EPIC-026-state-audit.md` (Week 0)

**Contingency:** If migration fails → UI doesn't update, workflows freeze

---

#### **R4: Breaking Generation Workflow**

**Likelihood:** MEDIUM (with Phase 0)
**Impact:** CRITICAL (core app functionality broken)

**Root Cause:** 380 LOC god method orchestrates 5+ services, 10-step workflow

**Mitigation:**
1. ✅ Phase 0 integration tests (50+ scenarios)
2. ✅ Golden baseline (42 definitions, 100% match required)
3. ✅ Incremental extraction (one step at a time)
4. ✅ Rollback checkpoints (weekly git tags)

---

### High Risks (🟠 Significant Mitigation)

#### **R11: Production Data Regression** (NEW)

**Likelihood:** MEDIUM (40%)
**Impact:** HIGH (incorrect definitions, legal liability)

**Mitigation:**
1. ✅ Export 42 definitions pre-refactor
2. ✅ Re-generate all 42 post-refactor, compare (0% tolerance)
3. ✅ Feature flag: `USE_REFACTORED_ORCHESTRATORS=false` (default)
4. ✅ Parallel run: Old + new code for 1 week

---

#### **R13: Git Rollback Failure** (NEW)

**Likelihood:** MEDIUM (40%)
**Impact:** HIGH (cannot revert, stuck with broken code)

**Mitigation:**
1. ✅ Git tags at EVERY checkpoint (automated hooks)
2. ✅ Granular commits (1 service = 1 commit)
3. ✅ Branch strategy (epic026/week1, epic026/week2, etc.)
4. ✅ Rollback playbook (test rollback in Week 1)

---

#### **R16: Integration Test False Positives** (NEW)

**Likelihood:** HIGH (60%)
**Impact:** HIGH (tests pass but code is broken)

**Mitigation:**
1. ✅ Mutation testing (inject bugs, verify tests catch them)
2. ✅ Golden master baseline (record ACTUAL behavior, not mocked)
3. ✅ Parallel testing (old code + new code in production)
4. ✅ Flaky test quarantine (<5% threshold)

---

### Medium Risks (🟡 Monitor)

#### **R2/R7: Timeline Overrun**

**Original:** 11→20 days
**Revised:** 8→14 weeks (2-week contingency buffer)

**Mitigation:**
1. ✅ Realistic baseline (12 weeks, not 2.5 weeks)
2. ✅ Weekly checkpoints (Go/No-Go every week)
3. ✅ Scope flex (can stop at Phase 1 if needed)
4. ✅ Abort trigger: <50% progress at Week 10

---

#### **R5: Async/Sync Boundary Issues**

**Mitigation:** Clean async design, async_bridge exists (proven pattern)

#### **R6: State Management Bugs**

**Mitigation:** State schema + type-safe wrappers (enhanced with R17 mitigation)

#### **R14: Circular Dependencies**

**Mitigation:** CI check script (trivial to add)

#### **R15: Performance Degradation**

**Mitigation:** Benchmark baselines (Phase 0 Week 5)

---

### Rollback Plan

**Trigger Scenarios:**

| Trigger | Week | Action | Rollback Target |
|---------|------|--------|-----------------|
| Phase 0 < 70% coverage | 5 | Extend 2 weeks OR abort | N/A (no code changes yet) |
| Integration tests fail | 6-13 | Rollback to last week | Previous week tag |
| Golden baseline < 95% match | 13 | STOP deployment | Week 12 (pre-validation) |
| <50% progress at Week 10 | 10 | Abort, deliver partial | Depends (Phase 1 or abort) |
| Developer unavailable >3 days | Any | Pause project | Current week |

**Rollback Procedures:** See `docs/operations/EPIC-026-rollback-playbook.md` (to be created Week 0)

---

## Acceptance Criteria

### Phase 0 Definition of Done (Gate 1)

- [ ] 436+ tests created (85%+ coverage)
- [ ] Test infrastructure operational (pytest-playwright, golden master)
- [ ] Integration test suite: 50+ scenarios, all GREEN
- [ ] Flaky tests: <5% of total tests
- [ ] Golden baseline exported: 42 definitions with validation results
- [ ] Performance benchmarks recorded
- [ ] Business logic extraction document complete
- [ ] State audit complete (208 usages inventoried)

**Gate 1 Decision:** GO to Phase 1 only if ALL criteria met

---

### Phase 1 Definition of Done (Gate 2)

- [ ] definitie_repository split into READ/WRITE/BULK services
- [ ] All 51 existing tests passing
- [ ] 51 new service tests created (102 total)
- [ ] Backward compatibility maintained (facade pattern)
- [ ] No circular dependencies (CI check GREEN)
- [ ] Velocity baseline established (features/week measured)
- [ ] Velocity improvement >= 10% observed (2-week measurement)
- [ ] Code review approved by architecture team

**Gate 2 Decision:** GO to Phase 2 only if velocity >= 10% + stakeholder approval

---

### Phase 2 Definition of Done (Gate 3)

- [ ] Generation Orchestrator extracted (380 LOC → <50 LOC in UI)
- [ ] Regeneration Orchestrator extracted (500 LOC → service)
- [ ] UI files thinned: tabbed_interface <400 LOC, generator_tab <800 LOC
- [ ] 74% LOC reduction in UI layer
- [ ] All 436+ tests passing (100% GREEN)
- [ ] Integration tests: 50+ scenarios GREEN
- [ ] Golden baseline: 100% match for all 42 definitions
- [ ] Performance benchmarks >= baseline (no degradation)
- [ ] Async patterns clean (no asyncio.run nesting)
- [ ] State management centralized (SessionStateManager only)
- [ ] No circular dependencies
- [ ] Code review approved

**Gate 3 Decision:** GO to production only if golden baseline 100% match

---

### Final Epic Definition of Done

- [ ] All 3 phases complete (or Phase 1-2 if Phase 3 skipped)
- [ ] All quantitative targets met (see Goals section)
- [ ] All tests GREEN (436+ tests minimum)
- [ ] Golden baseline 100% match (production validation)
- [ ] Documentation updated:
  - [ ] Architecture diagrams (service boundaries)
  - [ ] Rollback playbook
  - [ ] Business logic extraction document
  - [ ] State audit document
  - [ ] Migration guide
- [ ] Team trained on new architecture
- [ ] Production deployment successful (no regressions for 1 week)
- [ ] Velocity improvement >= 15% sustained (3-month measurement)

---

## Budget & Resource Allocation

### Detailed Cost Breakdown

**Phase 0: Test Foundation (5 weeks)**
- Test Engineer: 5 weeks × €5,000/week = €25,000
- Infrastructure: pytest-playwright, golden master framework = (included)
- **Total Phase 0:** €25,000

**Phase 1: Repository Refactor (3 weeks)**
- Code Architect: 3 weeks × €6,000/week = €18,000
- **Total Phase 1:** €18,000

**Phase 2: Critical Path UI (4 weeks)** - OPTIONAL
- Code Architect: 4 weeks × €6,000/week = €24,000
- **Total Phase 2:** €24,000

**Week 0: Prerequisites**
- Business logic extraction: 1 week × €6,000 = €6,000
- State audit: 3 days × €6,000/week = €2,500
- Backup developer onboarding: 2 days × €5,000/week = €1,500
- **Total Week 0:** €10,000

---

### Investment Scenarios

| Scenario | Phases | Duration | Cost | ROI (3yr) | Recommendation |
|----------|--------|----------|------|-----------|----------------|
| **Minimum** | Phase 0 only | 5 weeks | €25k | N/A (tests only) | If Phase 1 rejected |
| **Hybrid Staged** | Phase 0 + 1 | 8 weeks | €43k | +89% | Default commitment |
| **Hybrid Full** | Phase 0 + 1 + 2 | 12 weeks | €67k | +157% | If Phase 1 successful |
| **Full Scope** | Add 3 more files | 16-20 weeks | €100-150k | +112% | If roadmap requires |

**Recommended Investment:** €67k (Hybrid Full) - Best ROI with manageable risk

---

### Resource Requirements

**Phase 0 (Weeks 1-5):**
- Test Engineer: 100% (40 hrs/week)
- Code Architect: 20% (8 hrs/week - advisory)

**Phase 1 (Weeks 6-8):**
- Code Architect: 100% (40 hrs/week)
- Test Engineer: 20% (8 hrs/week - test maintenance)

**Phase 2 (Weeks 9-13):**
- Code Architect: 100% (40 hrs/week)
- Test Engineer: 20% (8 hrs/week - integration testing)

**Continuous (Weeks 0-13):**
- Backup Developer: 10% (4 hrs/week - knowledge transfer)
- Product Owner: 5% (2 hrs/week - checkpoint reviews)

---

## Notes

### Related Documentation

**Phase 1 Analysis (Already Complete):**
- ✅ `docs/backlog/EPIC-026/phase-1/definitie_repository_responsibility_map.md`
- ✅ `docs/backlog/EPIC-026/phase-1/definition_generator_tab_responsibility_map.md`
- ✅ `docs/backlog/EPIC-026/phase-1/tabbed_interface_responsibility_map.md`
- ✅ `docs/backlog/EPIC-026/phase-1/RECOMMENDATION.md` (9-week orchestrator-first plan)
- ✅ `docs/backlog/EPIC-026/phase-1/BUSINESS_LOGIC_EXTRACTION_PLAN.md` (comprehensive)

**5-Agent Analysis (2025-10-03):**
- Agent 1: Business Impact & ROI Analysis (~40 pages)
- Agent 2: Technical Architecture Analysis (~40 pages)
- Agent 3: User Stories Quality Audit (~40 pages)
- Agent 4: Timeline & Resource Planning (~40 pages)
- Agent 5: Risk & Mitigation Strategy (~50 pages)
- **Total:** ~210 pages comprehensive analysis

**To Be Created (Week 0):**
- `docs/business-logic/EPIC-026-extracted-rules.md` (business logic extraction)
- `docs/technical/EPIC-026-state-audit.md` (208 session_state usages)
- `docs/operations/EPIC-026-rollback-playbook.md` (rollback procedures)
- `config/session_state_schema.yaml` (state validation schema)

**Original v1.0:**
- `docs/backlog/EPIC-025/US-427/US-427-REFACTORING-STRATEGY.md`
- `docs/testing/US-427-coverage-baseline.md`

---

### Key Principles (Revised)

1. **Test-First, Refactor-Second** (not incremental without tests)
2. **Golden Master Protection** (record behavior, validate match)
3. **One Responsibility per Module** (SRP - unchanged)
4. **Dependency Injection** (testability - unchanged)
5. **Honest Estimates** (12 weeks, not 11-16 days)
6. **Checkpoints Every Week** (Go/No-Go decisions)
7. **Scope Flexibility** (can stop at Phase 1 if needed)
8. **Risk-First Approach** (address critical risks in Phase 0)

---

### Lessons Learned from v1.0

**What Went Wrong:**
1. ❌ Assumed "file splitting" (reality: architectural refactoring)
2. ❌ Assumed tests existed (reality: 0-1 tests for god objects)
3. ❌ Underestimated hidden complexity (880 LOC orchestrators)
4. ❌ No Phase 0 (test creation not scoped)
5. ❌ Optimistic timeline (11-16 days vs 12 weeks reality)

**What v2.0 Fixes:**
1. ✅ Phase 0 mandatory (5 weeks test creation)
2. ✅ Realistic timeline (12 weeks with contingency)
3. ✅ All risks documented (17 risks, 6 critical)
4. ✅ Scope flexibility (can stop at Phase 1)
5. ✅ Checkpoints every week (early abort if needed)

---

### Alternative Approaches Considered

**Option A: No Refactoring** (Rejected)
- Keep god objects, accept technical debt
- Pros: €0 cost, no risk
- Cons: Velocity degrades over time, bugs accumulate
- **Verdict:** REJECTED - technical debt compounds

**Option B: Minimal Viable Refactoring** (Fallback)
- Phase 0 + Phase 1 only (repository)
- 8 weeks, €43k, 30% value
- **Verdict:** ACCEPTABLE FALLBACK if Phase 2 rejected

**Option C: Full Scope (All 5 Files)** (Future)
- Add web_lookup + validation_orchestrator (4-8 more weeks)
- 16-20 weeks, €100-150k, 100% value
- **Verdict:** DEFER to future epic, only if hybrid proves ROI

**Option D: Rewrite Instead of Refactor** (Nuclear)
- Throw away, rebuild from scratch
- 6-12 months, €200-500k
- **Verdict:** REJECTED - too risky, lose domain knowledge

**Chosen: Hybrid Staged Approach** (v2.0)
- Phase 0 (tests) + Phase 1 (repository) + Phase 2 (UI orchestrators)
- 12 weeks, €67k, 70% value, MEDIUM risk
- **Verdict:** BEST BALANCE of value, cost, risk, timeline

---

## Stakeholder Communication

### What Changed from v1.0 → v2.0?

**Timeline:**
- v1.0: 11-16 days
- v2.0: 8-12 weeks (Hybrid Staged)
- **Change:** 5-8x longer (but realistic)

**Cost:**
- v1.0: €12.8k
- v2.0: €43-67k (Hybrid)
- **Change:** 3-5x higher (includes Phase 0 tests)

**Scope:**
- v1.0: 3 files (all god objects)
- v2.0: 2 files (deferred repository, focus on UI)
- **Change:** Narrower scope, higher impact

**Risk:**
- v1.0: 3 risks documented
- v2.0: 17 risks identified (6 critical)
- **Change:** Honest assessment, mitigations defined

---

### Why Accept v2.0?

**ROI Improves Despite Higher Cost:**
- v1.0: +341% ROI (unrealistic)
- v2.0: +89% to +157% ROI (realistic, evidence-based)

**Risk Decreases Despite More Risks Identified:**
- v1.0: HIGH risk (no tests, blind refactoring)
- v2.0: MEDIUM risk (Phase 0 provides safety net)

**Value Delivery Earlier:**
- v1.0: All-or-nothing at Week 3
- v2.0: Incremental value (tests Week 5, repository Week 8, UI Week 13)

**Abort Options:**
- v1.0: No safe abort points
- v2.0: Can stop at Phase 1 (30% value) or Phase 2 (70% value)

---

### What's the ROI?

**Investment:** €67k (12 weeks, Hybrid Full)

**Benefits (3-year horizon):**
- Velocity gain: 15-20% (realistic, measured)
- 20 additional features/year × €1,500/feature = €30k/year
- Reduced debugging: 10 hours/month × €100/hr × 12 months = €12k/year
- **Total annual benefit:** €42k/year

**Payback:** €67k / €42k = 1.6 years (19 months)

**3-Year ROI:** (€42k × 3 - €67k) / €67k = **+89%**

---

### Decision Needed

**Option 1:** Approve Hybrid Staged Approach (Recommended)
- Phase 0 (5 weeks, €25k) → Phase 1 (3 weeks, €18k) → Phase 2 (4 weeks, €24k)
- Total: 12 weeks, €67k
- ROI: +89% to +157% (positive)

**Option 2:** Approve Minimum Viable (Fallback)
- Phase 0 (5 weeks, €25k) → Phase 1 (3 weeks, €18k)
- Total: 8 weeks, €43k
- ROI: +30% to +50% (lower but safer)

**Option 3:** Reject Epic (Abort)
- Accept technical debt
- Focus on new features
- Revisit in 6-12 months

**Deadline for Decision:** End of Week 0 (after prerequisites complete)

---

**Status:** PENDING APPROVAL (Revision 2.0)
**Next Action:** Stakeholder review of 5-agent analysis + this revised epic
**Decision Required:**
1. Approve Hybrid Staged Approach (€67k, 12 weeks)?
2. Approve prerequisites (Week 0, €10k)?
3. Assign resources (test engineer, backup developer)?

---

**Prepared By:** Code Architect Team
**Contributors:** 5-Agent Analysis (Business, Architecture, Stories, Timeline, Risk)
**Date:** 2025-10-03
**Version:** 2.0 (Major Revision)
**Approvers Needed:** Product Owner, Tech Lead, Stakeholders
