# EPIC-026: Technical Risk Heatmap

**Date:** 2025-10-03
**Purpose:** Visual risk assessment for refactoring decision

---

## Risk Matrix

```
IMPACT
  ^
H │  6         2,5        1,3
I │
G │
H │
  │
M │  8         9          4
E │
D │
I │
U │  7         10
M │
  │
L │              11
O │
W │
  └──────────────────────────────>
      LOW      MEDIUM     HIGH
           PROBABILITY
```

### Risk Legend

| # | Risk | Probability | Impact | Score |
|---|------|-------------|--------|-------|
| **1** | Break generation flow (Week 4-5) | HIGH | HIGH | 🔴 9 |
| **2** | State management breaks UI | MEDIUM-HIGH | HIGH | 🔴 8 |
| **3** | Integration tests reveal unknowns | MEDIUM-HIGH | HIGH | 🔴 8 |
| **4** | Timeline overrun (9→11 weeks) | HIGH | MEDIUM | 🟡 7 |
| **5** | Async/sync boundary issues | MEDIUM-HIGH | HIGH | 🔴 8 |
| **6** | Test coverage gaps cause regressions | LOW | HIGH | 🟡 6 |
| **7** | Circular dependencies discovered | LOW | MEDIUM | 🟢 3 |
| **8** | Service initialization failures | LOW | MEDIUM | 🟢 3 |
| **9** | Hardcoded patterns remain hardcoded | MEDIUM | MEDIUM | 🟡 5 |
| **10** | Over-engineering (abstraction debt) | MEDIUM | MEDIUM | 🟡 5 |
| **11** | Repository split creates issues | LOW | LOW | 🟢 2 |

**Risk Score:** Probability × Impact (1-9 scale)
- 🔴 **Critical (7-9):** Immediate mitigation required
- 🟡 **Medium (4-6):** Monitor and mitigate
- 🟢 **Low (1-3):** Accept or defer

---

## Critical Risks (Score 7-9)

### 🔴 Risk #1: Break Generation Flow (Score 9)

**Description:** Extracting `_handle_definition_generation` (385 LOC god method) breaks core business logic

**Probability:** HIGH (70%)
- Complex orchestration across 5+ services
- Async/sync boundary mixing
- 15+ session state mutations
- No current test coverage

**Impact:** HIGH
- Application cannot generate definitions
- Blocks entire user workflow
- Requires major rework or rollback

**Mitigation:**
- ✅ Create 15-20 integration tests BEFORE extraction (Week 1)
- ✅ Incremental extraction (one step at a time)
- ✅ Daily testing after each change
- ✅ Rollback checkpoints every 2 days
- ✅ 2-week contingency buffer

**Owner:** Code Architect (Week 4-5)

---

### 🔴 Risk #2: State Management Breaks UI (Score 8)

**Description:** Session state contract changes break entire UI

**Probability:** MEDIUM-HIGH (50%)
- 50+ `SessionStateManager` calls in `tabbed_interface.py`
- 30+ calls in `definition_generator_tab.py`
- 100+ calls across all tabs
- State contracts span entire application

**Impact:** HIGH
- UI doesn't render
- Tab navigation fails
- Generation results lost
- User data corruption

**Mitigation:**
- ✅ Document state schema (Week 1)
- ✅ Create type-safe state wrappers (Week 1)
- ✅ Schema validation at runtime
- ✅ Incremental migration (don't change all at once)
- ✅ State contract tests

**Owner:** Code Architect (All weeks)

---

### 🔴 Risk #3: Integration Tests Reveal Unknowns (Score 8)

**Description:** Creating integration tests (Week 1) uncovers hidden dependencies

**Probability:** MEDIUM-HIGH (40%)
- Current test coverage: 1 test for 4,318 LOC UI code
- Unknown coupling between components
- Undocumented session state contracts
- Hidden service dependencies

**Impact:** HIGH
- Week 1 takes 2 weeks instead of 1
- +1-2 weeks timeline slip
- May discover blockers for extraction
- Could require plan revision

**Mitigation:**
- ✅ Allocate 7 days for Week 1 (not 5)
- ✅ Focus first 3 days on test creation
- ✅ Early escalation if unknowns found
- ✅ Go/No-Go decision at end of Week 1

**Owner:** Code Architect (Week 1)

---

### 🔴 Risk #5: Async/Sync Boundary Issues (Score 8)

**Description:** Clean async patterns impossible in sync Streamlit framework

**Probability:** MEDIUM-HIGH (50%)
- Streamlit is synchronous
- Category determination is async
- Generation is async (via run_async)
- Cannot eliminate asyncio.run() bridge

**Impact:** HIGH
- Concurrency bugs
- Race conditions
- Error handling complexity
- Performance issues

**Mitigation:**
- ✅ Accept async/sync bridge as architectural constraint
- ✅ Focus on clean boundaries, not elimination
- ✅ Comprehensive async error handling
- ✅ Use existing `run_async()` pattern

**Owner:** Code Architect (Week 4-5)

---

## Medium Risks (Score 4-6)

### 🟡 Risk #4: Timeline Overrun (Score 7)

**Description:** 9 weeks → 11-12 weeks due to complexity

**Probability:** HIGH (60%)
- Proposed plan has tight timeline
- No buffer for unknowns
- Complex orchestrator extraction
- State management migration

**Impact:** MEDIUM
- +2-3 weeks delay
- Budget overrun
- Blocks other work
- Stakeholder frustration

**Mitigation:**
- ✅ **Use 4-5 week alternative plan** (44% faster)
- ✅ Weekly reassessment
- ✅ Parallel work after Week 3
- ✅ Deliver partial if needed

**Owner:** Project Manager

---

### 🟡 Risk #6: Test Coverage Gaps (Score 6)

**Description:** Insufficient tests allow regressions

**Probability:** LOW (20%)
- Plan includes comprehensive testing
- 15-20 integration tests
- 90%+ coverage for services

**Impact:** HIGH
- Bugs in production
- User-facing errors
- Rollback required

**Mitigation:**
- ✅ Test coverage requirement: 90%+
- ✅ Integration tests must pass
- ✅ Manual QA after each week
- ✅ Smoke tests in CI/CD

**Owner:** Code Architect + QA

---

### 🟡 Risk #9: Hardcoded Patterns Remain (Score 5)

**Description:** Proposed plan moves patterns to services (still hardcoded)

**Probability:** MEDIUM (40%)
- `OntologicalCategoryService` just moves code
- Patterns not in config
- Not data-driven

**Impact:** MEDIUM
- Maintenance burden remains
- Inconsistency risk
- Not extensible

**Mitigation:**
- ✅ **Use alternative plan** (extract to config)
- ✅ Create `config/ontological_patterns.yaml`
- ✅ Make services read from config

**Owner:** Code Architect (Week 1-2)

---

### 🟡 Risk #10: Over-Engineering (Score 5)

**Description:** Creating unnecessary abstraction layers

**Probability:** MEDIUM (40%)
- 7 new services (5 unnecessary)
- 4 layers instead of 3
- Orchestrator proliferation

**Impact:** MEDIUM
- Maintenance burden
- Complexity increase
- Slower development
- Technical debt

**Mitigation:**
- ✅ **Use alternative plan** (2 new services, 3 layers)
- ✅ Reuse existing services
- ✅ YAGNI principle
- ✅ Architecture review before Week 2

**Owner:** Technical Architect

---

## Low Risks (Score 1-3)

### 🟢 Risk #7: Circular Dependencies (Score 3)

**Description:** Circular dependencies block refactoring

**Probability:** LOW (10%)
- Only 2 lazy imports in codebase
- No evidence of pervasive circular deps
- Clear service boundaries

**Impact:** MEDIUM
- Requires architectural changes
- Could block extraction

**Mitigation:**
- ✅ Dependency injection
- ✅ Interface-based abstractions
- ✅ Import graph analysis

**Owner:** Code Architect

---

### 🟢 Risk #8: Service Initialization Failures (Score 3)

**Description:** Service initialization fails in production

**Probability:** LOW (10%)
- ServiceContainer pattern already works
- DI well-established
- 89 services already working

**Impact:** MEDIUM
- Application doesn't start
- Fallback to dummy services

**Mitigation:**
- ✅ Initialization tests
- ✅ Graceful fallbacks
- ✅ CI/CD checks

**Owner:** DevOps

---

### 🟢 Risk #11: Repository Split Issues (Score 2)

**Description:** Splitting `definitie_repository.py` causes problems

**Probability:** LOW (5%)
- Not a god object (complexity 4.7)
- 51 tests (excellent coverage)
- Well-structured

**Impact:** LOW
- Easy rollback
- Not critical path

**Mitigation:**
- ✅ **DEFER to later epic** (not in scope)
- ✅ Keep as-is (low priority)

**Owner:** N/A (deferred)

---

## Risk Comparison: Proposed vs Alternative

### Proposed Plan Risk Profile

| Risk Category | Count | Total Score |
|---------------|-------|-------------|
| 🔴 Critical (7-9) | 5 | 41 |
| 🟡 Medium (4-6) | 4 | 23 |
| 🟢 Low (1-3) | 2 | 5 |
| **TOTAL** | **11** | **69** |

**Overall Risk:** MEDIUM-HIGH

---

### Alternative Plan Risk Profile

| Risk Category | Count | Total Score |
|---------------|-------|-------------|
| 🔴 Critical (7-9) | 3 | 25 |
| 🟡 Medium (4-6) | 2 | 11 |
| 🟢 Low (1-3) | 2 | 5 |
| **TOTAL** | **7** | **41** |

**Overall Risk:** MEDIUM

**Risk Reduction:** 41% (69 → 41 total score)

---

### Mitigated Risks (Alternative Plan)

✅ **Risk #4 (Timeline Overrun)** - Reduced from 60% to 30% probability
  - Reason: 4-5 weeks vs 9 weeks (less time to overrun)

✅ **Risk #9 (Hardcoded Patterns)** - Eliminated (0% probability)
  - Reason: Patterns extracted to config (data-driven)

✅ **Risk #10 (Over-Engineering)** - Reduced from 40% to 10% probability
  - Reason: Only 2 new services, 3 layers (not 4)

✅ **Risk #11 (Repository Split)** - Eliminated (0% probability)
  - Reason: Deferred (not in scope)

---

## Risk Mitigation Strategy

### Week-by-Week Risk Management

**Week 1: Foundation (CRITICAL PHASE)**
- **Primary Risks:** #3 (integration tests reveal unknowns)
- **Mitigation:** 7 days (not 5), early escalation
- **Go/No-Go Decision:** End of Week 1

**Week 2: Business Logic Extraction**
- **Primary Risks:** #9 (hardcoded patterns), #10 (over-engineering)
- **Mitigation:** Extract to config, reuse existing services

**Week 3: UI Component Splitting**
- **Primary Risks:** #2 (state management)
- **Mitigation:** Type-safe wrappers, incremental migration

**Week 4: Orchestration Extraction (CRITICAL PHASE)**
- **Primary Risks:** #1 (break generation), #5 (async/sync)
- **Mitigation:** Comprehensive tests, daily testing, rollback points

**Week 5: Cleanup**
- **Primary Risks:** None (low-risk cleanup work)

---

## Risk Acceptance Criteria

### Go/No-Go Gates

**Week 1 Gate:**
- ✅ 15-20 integration tests created and passing
- ✅ State schema documented
- ✅ No critical unknowns discovered
- ❌ **STOP if:** >5 critical unknowns, timeline slip >1 week

**Week 4 Gate:**
- ✅ Orchestrator extraction complete
- ✅ All integration tests passing
- ✅ No functional regressions
- ❌ **STOP if:** Tests fail, generation broken, >3 days blocked

**Final Gate:**
- ✅ UI reduced to <1,200 LOC
- ✅ All tests passing (90%+ coverage)
- ✅ No performance degradation
- ✅ Documentation complete

---

## Rollback Strategy

### Rollback Triggers

| Trigger | Action | Owner |
|---------|--------|-------|
| **Integration tests fail (Week 1)** | Reassess plan, add 1 week | PM |
| **Generation broken (Week 4)** | Rollback to Week 3 checkpoint | Code Architect |
| **Timeline slip >2 weeks** | Deliver partial (1-2 files) | PM |
| **<50% progress at Week 3** | Abort, rescope to MVP | Stakeholders |

### Checkpoint Strategy

**Git Tags at End of Each Week:**
- `epic-026-week-1-foundation`
- `epic-026-week-2-business-logic`
- `epic-026-week-3-ui-split`
- `epic-026-week-4-orchestration`
- `epic-026-week-5-cleanup`

**Rollback Command:**
```bash
git checkout epic-026-week-N-<name>
pytest -q  # Verify tests pass
```

**Maximum Rollback Window:** 2 weeks (to previous checkpoint)

---

## Risk Dashboard (For Monitoring)

### KPIs to Track

| KPI | Target | Alert Threshold |
|-----|--------|-----------------|
| **Test Coverage** | >90% | <80% |
| **Integration Tests Passing** | 100% | <95% |
| **Timeline Variance** | ±0 weeks | >+1 week |
| **God Method LOC** | <50 LOC | >100 LOC |
| **New Services Created** | 2 | >3 |
| **Hardcoded Patterns** | 0 | >1 |
| **Complexity (Max)** | <15 | >25 |

### Weekly Risk Review

**Questions to Ask:**
1. Are all integration tests passing?
2. Is timeline on track?
3. Are we creating unnecessary services?
4. Are patterns in config (not code)?
5. Is UI getting thinner?

**Escalation Path:**
- Week variance >3 days → PM notified
- Critical risk triggered → Stakeholders notified
- Rollback needed → Architecture review

---

## Recommendation

### Risk-Based Decision

**Proposed Plan:**
- Total Risk Score: 69
- Critical Risks: 5
- Overall Risk: MEDIUM-HIGH

**Alternative Plan:**
- Total Risk Score: 41
- Critical Risks: 3
- Overall Risk: MEDIUM

**Risk Reduction:** 41% with alternative approach

### ⚠️ APPROVE ALTERNATIVE PLAN

**Reasons:**
1. Lower overall risk (41 vs 69)
2. Fewer critical risks (3 vs 5)
3. Mitigates hardcoded patterns (config-driven)
4. Shorter timeline = less time to derail
5. Simpler architecture = less risk surface

---

**Status:** READY FOR DECISION
**Next Action:** Present to stakeholders with risk assessment
**Decision Required:** Accept MEDIUM risk (alternative) vs MEDIUM-HIGH risk (proposed)?

---

**Prepared by:** Technical Architecture Analyst (Agent 2)
**Date:** 2025-10-03
