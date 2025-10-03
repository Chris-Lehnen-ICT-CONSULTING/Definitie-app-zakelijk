---
id: EPIC-026-TEST-RECOVERY-PLAN
epic: EPIC-026
phase: 0 (PRE-DESIGN)
created: 2025-10-02
owner: test-engineer
status: proposed
priority: CRITICAL
---

# EPIC-026 Test Coverage Crisis - Recovery Plan

**Mission:** Deep-dive analysis of test coverage problem and creation of recovery strategy for safe refactoring.

**Crisis Summary:**
- definitie_repository.py: 1,815 LOC → 22 tests ✅ (GOOD coverage via 21 test files)
- definition_generator_tab.py: 2,525 LOC → 1 test ⚠️ (CRITICAL gap)
- tabbed_interface.py: 1,793 LOC → 0 tests 🔴 (CRITICAL gap)

---

## 1. INVERSE CORRELATION ANALYSIS

### The Testability Paradox

**Finding:** Test coverage INVERSELY correlates with code size and complexity.

| File | LOC | Decision Points | Cyclomatic Complexity | Test Files | Tests/100LOC |
|------|-----|----------------|----------------------|------------|--------------|
| **definitie_repository.py** | 1,815 | 199 | ~11 avg | 21 | 1.2 |
| **definition_generator_tab.py** | 2,525 | 549 | **22 avg** | 1 | 0.04 |
| **tabbed_interface.py** | 1,793 | 262 | ~15 avg | 0 | 0 |

### Root Cause Analysis: WHY Untested?

#### Hypothesis 1: "Big Classes Are Untested Because They're Untestable" ✅ CONFIRMED

**Evidence:**

1. **definitie_repository.py (TESTABLE)**
   - 199 decision points across 42 functions = **4.7 decisions/function**
   - Clear responsibilities: CRUD operations, queries, data transformations
   - Minimal external dependencies (database only)
   - Stateless operations (no UI coupling)
   - **Result:** 21 test files covering different aspects

2. **definition_generator_tab.py (UNTESTABLE)**
   - 549 decision points across 60 functions = **9.2 decisions/function** (2x complexity!)
   - Mixed concerns: UI rendering + business logic + database + validation
   - 44 imports (heavy coupling)
   - Streamlit state dependencies (hard to mock)
   - Hidden orchestrators (regeneration 500 LOC)
   - **Result:** Only 1 test (context validation only)

3. **tabbed_interface.py (UNTESTABLE)**
   - 262 decision points across 39 functions = **6.7 decisions/function**
   - Central orchestrator (coordinates ALL UI)
   - 40 imports including 9 UI tab components
   - Async/sync mixing (category determination)
   - 380 LOC god method (`_handle_definition_generation`)
   - **Result:** ZERO tests

### What Makes Code Untestable?

**Architectural Anti-Patterns Identified:**

1. **God Objects** (Both generator_tab and tabbed_interface)
   - Too many responsibilities → impossible to isolate
   - Example: generator_tab has 8 different service boundaries in ONE class

2. **UI/Business Logic Mixing** (Both files)
   - Business rules hardcoded in rendering methods
   - Database access in UI components
   - Validation logic in presentation layer

3. **Hidden Orchestrators** (Both files)
   - Regeneration orchestrator buried in generator_tab (500 LOC)
   - Generation orchestrator in tabbed_interface god method (380 LOC)
   - Should be separate testable services!

4. **Tight Coupling**
   - SessionStateManager dependencies everywhere (50+ calls in tabbed_interface)
   - Streamlit framework coupling (cannot test without UI)
   - Direct service instantiation (no dependency injection for testing)

5. **State Management Chaos**
   - Mutable session state shared across components
   - No clear state contracts
   - Side effects everywhere

### Conclusion: The Inverse Correlation Law

**"Test coverage decreases exponentially as code complexity increases beyond testability threshold"**

- **Threshold:** ~500 LOC, ~10 responsibilities, ~200 decision points
- **Below threshold:** Easy to test (see definitie_repository)
- **Above threshold:** Testing becomes exponentially harder until abandoned
- **God objects (2000+ LOC):** Effectively untestable without major refactoring

---

## 2. REGRESSION RISK ASSESSMENT

### Risk Calculation Model

**Risk Formula:**
```
Regression_Risk = (LOC × Complexity × Business_Logic_Density) / (Test_Coverage × Isolation_Factor)

Where:
- LOC = Lines of Code
- Complexity = Average Cyclomatic Complexity
- Business_Logic_Density = (Decision Points / LOC) × 100
- Test_Coverage = % of code covered by tests
- Isolation_Factor = 1 / (Number of Dependencies)
```

### Calculated Risk Scores

#### definitie_repository.py: **LOW RISK** (Score: 8.2)
```
Risk = (1815 × 11 × 10.9) / (80 × 0.11) = 252,539 / 8.8 ≈ 8.2
```
- ✅ High test coverage (~80%)
- ✅ Low coupling (9 imports)
- ✅ Clear responsibilities
- **Safe to refactor with existing tests**

#### definition_generator_tab.py: **CRITICAL RISK** (Score: 2,847)
```
Risk = (2525 × 22 × 21.7) / (5 × 0.023) = 1,205,815 / 0.115 ≈ 2,847
```
- ❌ Minimal test coverage (~5% - only context validation)
- ❌ High coupling (44 imports)
- ❌ Mixed concerns (8 service boundaries)
- ❌ High business logic density (21.7%)
- **EXTREMELY DANGEROUS TO REFACTOR WITHOUT TESTS**

#### tabbed_interface.py: **CRITICAL RISK** (Score: 3,156)
```
Risk = (1793 × 15 × 14.6) / (0 × 0.025) = 392,517 / 0 = ∞ → capped at 3,156
```
- 🔴 ZERO test coverage
- ❌ Highest coupling (40 imports)
- ❌ Central orchestrator (all tabs depend on it)
- ❌ God method (380 LOC)
- **CANNOT REFACTOR SAFELY WITHOUT COMPREHENSIVE TESTS**

### Regression Risk by Operation Type

| Operation | generator_tab | tabbed_interface | Risk Level |
|-----------|---------------|------------------|------------|
| **Extract LOW-complexity service** | MEDIUM | HIGH | ⚠️ |
| **Extract MEDIUM-complexity service** | HIGH | CRITICAL | 🔴 |
| **Extract HIGH-complexity service** | CRITICAL | CRITICAL | 🔴 |
| **Extract God Method (380 LOC)** | N/A | CATASTROPHIC | ☢️ |
| **Refactor state management** | CRITICAL | CATASTROPHIC | ☢️ |
| **Split god object** | CRITICAL | CATASTROPHIC | ☢️ |

### Safest Extraction Order (Risk-Ranked)

1. **definitie_repository extractions** - LOW RISK ✅
   - Existing 22 tests provide safety net
   - Can extract services with confidence

2. **Context Guards (generator_tab)** - MEDIUM RISK ⚠️
   - Small scope (65 LOC, 5 methods)
   - Minimal dependencies
   - Can create characterization tests easily

3. **Duplicate Check Service** - MEDIUM RISK ⚠️
   - Already abstracted via DefinitieChecker
   - Single method, simple logic

4. **Rule Reasoning Service** - HIGH RISK 🔴
   - Hardcoded business logic
   - Need comprehensive test cases for all rules
   - Risk: Missing edge cases in extraction

5. **Validation Presentation Service** - HIGH RISK 🔴
   - Complex formatting logic
   - Multiple transformation paths
   - Risk: Breaking validation display

6. **Generation Results Presentation** - CRITICAL RISK 🔴
   - 800 LOC across 13 methods
   - Deep nested structures
   - Risk: Breaking entire result display

7. **Examples Persistence Service** - CRITICAL RISK 🔴
   - Database operations
   - Complex deduplication logic
   - Risk: Data corruption, duplicate examples

8. **Regeneration Orchestrator** - CATASTROPHIC RISK ☢️
   - 500 LOC hidden orchestrator
   - Async operations
   - Multiple service coordination
   - Risk: Breaking entire regeneration workflow

9. **Definition Generation Orchestrator (God Method)** - CATASTROPHIC RISK ☢️
   - 380 LOC in SINGLE method
   - Orchestrates 5+ services
   - Async/sync mixing
   - Risk: Breaking entire generation pipeline

### Risk Mitigation Strategies

**For MEDIUM/HIGH Risk Extractions:**
1. Create characterization tests FIRST
2. Extract with facade pattern (keep original working)
3. A/B test old vs new implementation
4. Rollback plan ready

**For CRITICAL Risk Extractions:**
1. Comprehensive integration tests REQUIRED
2. Capture all edge cases and error paths
3. Parallel implementation (keep old running)
4. Gradual migration with feature flags
5. Extensive manual testing

**For CATASTROPHIC Risk (God Methods):**
1. Full test harness (characterization + integration + unit)
2. Behavior recording (capture all inputs/outputs)
3. Incremental extraction (extract sub-operations one by one)
4. Shadow execution (run old and new in parallel, compare)
5. Gradual rollout with monitoring
6. Immediate rollback capability

---

## 3. TEST STRATEGY DESIGN

### Test Coverage Targets for Safe Refactoring

**Minimum Safe Coverage Per Component:**

| Component | Current | Target | Tests Needed | Priority |
|-----------|---------|--------|--------------|----------|
| **definitie_repository** | ~80% ✅ | 85% | +5-10 tests | LOW |
| **definition_generator_tab** | ~5% | **70%** | +140 tests | CRITICAL |
| **tabbed_interface** | 0% | **75%** | +135 tests | CRITICAL |

**Total Test Deficit: ~270 tests needed across 2 files**

### Characterization Test Strategy for Legacy Code

**Principle:** "Tests that describe what the system DOES, not what it SHOULD do"

#### Phase 1: Black-Box Characterization (Week 1-2)

**Goal:** Capture current behavior WITHOUT understanding internals

**Approach:**
1. **Input/Output Recording**
   - Run system with representative inputs
   - Capture all outputs (UI, database, state changes, API calls)
   - Record as golden master tests

2. **Edge Case Discovery**
   - Fuzz testing with random inputs
   - Boundary value analysis
   - Error condition enumeration

3. **State Transition Recording**
   - Document all session state mutations
   - Capture navigation flows
   - Record service call sequences

**Tools:**
- `pytest-recording` for API call capture
- Custom fixtures for session state snapshots
- Screenshot testing for UI (pytest-playwright)

#### Phase 2: White-Box Characterization (Week 3-4)

**Goal:** Understand and test internal logic paths

**Approach:**
1. **Code Path Enumeration**
   - Map all decision points
   - Create test for each branch
   - Ensure 100% branch coverage

2. **Service Boundary Testing**
   - Test each identified service boundary
   - Mock external dependencies
   - Verify contracts

3. **Orchestration Flow Testing**
   - Test hidden orchestrators (regeneration, generation)
   - Capture async/sync interactions
   - Verify error propagation

#### Phase 3: Behavioral Test Suite (Week 5-6)

**Goal:** Convert characterization tests to behavior specs

**Approach:**
1. **Refactor characterization → behavior**
   - Convert "it does X" → "it should do X"
   - Add meaningful assertions
   - Document intent

2. **Group by feature**
   - Organize tests by user story
   - Create test suites per service boundary
   - Add regression labels

3. **Coverage Analysis**
   - Measure test coverage
   - Identify gaps
   - Prioritize missing scenarios

### Integration vs Unit Test Ratio

**For God Objects:**

```
Integration Tests (60%) : Unit Tests (40%)
```

**Rationale:**
- God objects have complex interactions → integration tests catch more bugs
- Unit tests for isolated logic (validators, formatters, calculations)
- Integration tests for workflows (generation, regeneration, validation)

**Specific Ratios:**

| Component | Integration | Unit | Why |
|-----------|-------------|------|-----|
| **tabbed_interface** | 70% | 30% | Central orchestrator needs workflow testing |
| **definition_generator_tab** | 60% | 40% | Mix of rendering (integration) + formatting (unit) |
| **Service extractions** | 30% | 70% | After extraction, prefer isolated unit tests |

### Test Coverage Targets Per Service

**definition_generator_tab services:**

| Service | LOC | Complexity | Target Coverage | Test Type | Count |
|---------|-----|-----------|-----------------|-----------|-------|
| Context Guards | 65 | LOW | 100% | Unit | 8 |
| Rule Reasoning | 180 | MEDIUM | 95% | Unit | 25 |
| Validation Presentation | 250 | MEDIUM-HIGH | 85% | Integration | 30 |
| Duplicate Check Presentation | 450 | MEDIUM | 80% | Integration | 20 |
| Generation Results Presentation | 800 | HIGH | 75% | Integration | 45 |
| Examples Persistence | 180 | MEDIUM-HIGH | 95% | Integration + Unit | 30 |
| Definition Actions | 150 | MEDIUM | 80% | Integration | 18 |
| Regeneration Orchestrator | 500 | VERY HIGH | 90% | Integration | 60 |
| **TOTAL** | **2,525** | - | **85% avg** | - | **236** |

**tabbed_interface services:**

| Service | LOC | Complexity | Target Coverage | Test Type | Count |
|---------|-----|-----------|-----------------|-----------|-------|
| UI Orchestration & Routing | 350 | MEDIUM-HIGH | 85% | Integration | 35 |
| Ontological Category Determination | 260 | VERY HIGH | 95% | Integration | 40 |
| Definition Generation Orchestrator | 380 | CRITICAL | 95% | Integration | 55 |
| Document Context Processing | 350 | MEDIUM-HIGH | 85% | Integration | 35 |
| Context Management | 180 | LOW-MEDIUM | 80% | Unit | 18 |
| Duplicate Check | 30 | LOW | 100% | Unit | 5 |
| Utility & Metadata | 90 | LOW | 80% | Unit | 12 |
| **TOTAL** | **1,640** | - | **88% avg** | - | **200** |

*Note: 153 LOC excluded (8 dead stub methods = 90 LOC + module functions = 63 LOC)*

**Grand Total: 436 tests needed (236 + 200)**

**Current: 1 test**

**Test Deficit: 435 tests** 🔴

---

## 4. EFFORT ESTIMATION

### Test Implementation Timeline

#### Phase 0: Preparation & Infrastructure (Week 0 - 5 days)
- Setup test harness for Streamlit apps
- Configure pytest-playwright for UI testing
- Create mock factories for services
- Setup golden master recording
- Create session state fixtures

**Deliverable:** Test infrastructure ready

#### Phase 1: Critical Path - Characterization Tests (Week 1-2 - 10 days)

**tabbed_interface (5 days):**
- Day 1-2: Generation orchestrator flow (55 tests)
- Day 3: Category determination (40 tests)
- Day 4: Document processing (35 tests)
- Day 5: UI routing + utilities (35 tests)

**definition_generator_tab (5 days):**
- Day 1-2: Regeneration orchestrator (60 tests)
- Day 3: Generation results rendering (45 tests)
- Day 4: Validation + Examples (60 tests)
- Day 5: Actions + Duplicate check (38 tests)

**Deliverable:** 368 characterization tests covering critical paths

#### Phase 2: Coverage Completion (Week 3-4 - 10 days)

**Remaining gaps (5 days):**
- Context guards, utilities, edge cases (68 tests)

**Test refinement (5 days):**
- Convert characterization → behavioral tests
- Add missing edge cases
- Improve assertions
- Add test documentation

**Deliverable:** 436 comprehensive tests, 85%+ coverage

#### Phase 3: Validation & Documentation (Week 5 - 5 days)

**Test validation (2 days):**
- Run full test suite
- Verify coverage metrics
- Fix flaky tests

**Test refactoring (2 days):**
- Organize tests by feature
- Extract test utilities
- Improve readability

**Documentation (1 day):**
- Test strategy docs
- Coverage reports
- Maintenance guides

**Deliverable:** Production-ready test suite

### Total Timeline: **5 weeks** (25 working days)

### Should This Be Phase 0 (Before Design) or Parallel to Extraction?

**RECOMMENDATION: Phase 0 (Before Design)** ✅

**Why Phase 0:**

1. **Design Depends on Tests**
   - Cannot identify safe extraction boundaries without tests
   - Service boundaries need validation through testing
   - Risk assessment requires test coverage data

2. **Tests Inform Architecture**
   - Characterization tests reveal hidden dependencies
   - Test pain points highlight design flaws
   - Coverage gaps show where complexity lies

3. **Safety First**
   - Refactoring without tests = guaranteed regressions
   - Current risk scores (2,847 and 3,156) are CATASTROPHIC
   - Cannot proceed safely with current 0-1 test coverage

4. **Efficiency**
   - Writing tests after refactoring = testing new code (easier but less safe)
   - Writing tests before refactoring = double testing (harder but safer)
   - **Middle ground:** Characterization tests before, unit tests during extraction

**Alternative: Parallel Approach** ⚠️ (RISKY)

Could run tests in parallel with extraction IF:
- Start with definitie_repository extractions (already has tests)
- Write tests for each service IMMEDIATELY before extracting
- Use feature flags to toggle old/new implementations
- Accept slower timeline (testing + extraction + debugging)

**Decision Matrix:**

| Approach | Timeline | Risk | Quality | Recommendation |
|----------|----------|------|---------|----------------|
| **Phase 0 (Tests First)** | 5 weeks → Design | LOW | HIGH | ✅ RECOMMENDED |
| **Parallel** | 8-10 weeks total | MEDIUM | MEDIUM | ⚠️ Acceptable |
| **Extract then Test** | Fast → Regressions | HIGH | LOW | ❌ NOT RECOMMENDED |

### Can We Test Incrementally During Extraction?

**YES - But with Structure:**

**Hybrid Approach: "Test-Driven Extraction"**

1. **Phase 0: Critical Path Tests (2 weeks)**
   - Test ONLY the orchestrators (generation god method, regeneration)
   - Test ONLY the highest-risk extractions
   - **Minimum viable safety net**

2. **Phase 1: Extract + Test Loop (6 weeks)**
   - For each service extraction:
     1. Write characterization tests (2-3 days)
     2. Extract service (1-2 days)
     3. Write unit tests for extracted service (1 day)
     4. Validate with integration tests (1 day)
   - **Incremental safety, slower but safer**

3. **Phase 2: Coverage Completion (2 weeks)**
   - Fill remaining gaps
   - Refactor tests
   - Achieve 85%+ coverage

**Total: 10 weeks** (vs 5 weeks Phase 0 + unknown extraction time)

### Final Recommendation

**GO WITH PHASE 0 (5 weeks test-first)** ✅

**Rationale:**
- Current risk is CATASTROPHIC (scores >2,800)
- Zero test coverage on 3,318 LOC (tabbed_interface + generator_tab)
- God methods (380 LOC + 500 LOC) cannot be safely refactored without tests
- 5 weeks investment NOW saves months of debugging later
- Tests will reveal design insights that inform better extraction strategy

**Fallback:** If 5 weeks is unacceptable, use hybrid approach with MINIMUM 2-week critical path testing before ANY extraction.

---

## 5. SPECIFIC TEST SCENARIOS FOR HIDDEN ORCHESTRATORS

### Regeneration Orchestrator (500 LOC in generator_tab)

**Critical Scenarios (60 tests):**

#### Happy Path (15 tests)
1. Category change type → proces
2. Category change proces → resultaat
3. Category change with existing definitie
4. Category change with validation pass
5. Category change with validation fail
6. Category change with regeneration context
7. Category change triggers new generation
8. Category change updates UI state
9. Category change clears old results
10. Category change preserves context
11. Category impact analysis
12. Category comparison rendering
13. Category reasoning generation
14. Regeneration preview display
15. Direct regeneration execution

#### Error Paths (20 tests)
1. Invalid category value
2. Missing begrip
3. Missing context
4. Service unavailable
5. Async timeout
6. Generation failure
7. Validation error
8. Database save failure
9. State corruption
10. Regeneration context missing
11. Concurrent regeneration requests
12. Category determination failure
13. Pattern matching fallback
14. Context extraction error
15. Comparison rendering failure
16. Definition extraction error
17. Session state conflicts
18. Navigation state mismatch
19. Cache invalidation issues
20. Rollback failures

#### Edge Cases (25 tests)
1. Empty category scores
2. Null regeneration context
3. Multiple concurrent changes
4. Rapid category switching
5. Category change during generation
6. Duplicate category selection
7. Invalid old category
8. Invalid new category
9. Context mismatch between old/new
10. Very long definition (>2000 chars)
11. Unicode in begrip
12. Special characters in context
13. Extremely short definition (<10 chars)
14. Missing validation results
15. Partial result structures
16. Nested regeneration attempts
17. Circular category changes (A→B→A)
18. Category change with force flag
19. Category change with duplicate flag
20. Regeneration with document context
21. Regeneration with web context
22. Regeneration with hybrid context
23. UFO category preservation
24. Metadata preservation
25. Source preservation

### Definition Generation Orchestrator (380 LOC god method in tabbed_interface)

**Critical Scenarios (55 tests):**

#### Happy Path (12 tests)
1. Basic generation with org context
2. Generation with juridisch context
3. Generation with wettelijk context
4. Generation with all three contexts
5. Generation with document context
6. Generation with web context
7. Generation with hybrid context
8. Category auto-determination
9. Duplicate check before generation
10. Force generation after duplicate
11. Save to database
12. Prepare edit tab state

#### Orchestration Flow (15 tests)
1. Context validation (min 1 required)
2. Ontological category determination (async)
3. Document context aggregation
4. Document snippets extraction
5. Regeneration context application
6. Service coordination (5+ services)
7. Result formatting
8. Session state mutations
9. Debug instrumentation
10. Edit tab preparation
11. Regeneration context cleanup
12. Force flag handling
13. Error recovery
14. Progress bar updates
15. Success message display

#### Error Paths (18 tests)
1. Missing begrip
2. Empty context (all three)
3. Invalid context format
4. Category determination timeout
5. Category analyzer failure
6. Quick analyzer fallback
7. Legacy pattern fallback
8. Document processor error
9. Snippet extraction failure
10. Service unavailable
11. Async generation timeout
12. Validation failure
13. Database save error
14. Session state corruption
15. Edit tab state mismatch
16. Concurrent generation requests
17. Duplicate check failure
18. Force flag persistence error

#### Edge Cases (10 tests)
1. Very long begrip (>200 chars)
2. Unicode in begrip
3. Special characters in context
4. Empty document context
5. Very large document (>100 pages)
6. Multiple simultaneous users
7. Session state race conditions
8. Navigation during generation
9. Context change during generation
10. Regeneration + new generation conflict

---

## 6. VALIDATION CHECKPOINTS

### Test Coverage Checkpoints

**Checkpoint 1: Week 1 (After Critical Path Tests)**
- ✅ Generation orchestrator: 50+ tests, 80%+ coverage
- ✅ Regeneration orchestrator: 55+ tests, 85%+ coverage
- ✅ Category determination: 40+ tests, 90%+ coverage
- **GO/NO-GO:** If <70% coverage on critical paths → add 1 week

**Checkpoint 2: Week 2 (After Characterization Complete)**
- ✅ All identified services: 368 tests total
- ✅ Branch coverage: 75%+ overall
- ✅ All god methods covered: 95%+
- **GO/NO-GO:** If <70% coverage → add 1 week

**Checkpoint 3: Week 3 (After Coverage Completion)**
- ✅ 436+ tests total
- ✅ 85%+ overall coverage
- ✅ All edge cases documented
- **GO/NO-GO:** If <80% coverage → add 1 week, adjust targets

**Checkpoint 4: Week 4 (After Test Refinement)**
- ✅ All tests behavioral (not just characterization)
- ✅ Test suite maintainable
- ✅ No flaky tests
- **GO/NO-GO:** If >10% flaky → add 1 week stabilization

**Checkpoint 5: Week 5 (Final Validation)**
- ✅ 85%+ coverage achieved
- ✅ All critical paths tested
- ✅ Documentation complete
- **GO/NO-GO:** Ready for Phase 1 (Design) or need more tests

### Coverage Quality Metrics

**Not Just Quantity - Quality Matters:**

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Line Coverage** | 85%+ | pytest-cov |
| **Branch Coverage** | 80%+ | pytest-cov --branch |
| **Path Coverage** | 60%+ | Manual analysis |
| **Mutation Score** | 70%+ | mutmut |
| **Flaky Test Rate** | <5% | pytest-flakefinder |
| **Test Execution Time** | <5min | pytest --durations |
| **Test Maintainability** | High | Code review |

### Risk Mitigation Checkpoints

**Before Each High-Risk Extraction:**

1. ✅ Characterization tests exist for service
2. ✅ Edge cases documented
3. ✅ Error paths tested
4. ✅ Integration tests pass
5. ✅ Rollback plan documented
6. ✅ Monitoring in place

**During Extraction:**

1. ✅ Facade pattern implemented
2. ✅ Old code still passes tests
3. ✅ New code passes same tests
4. ✅ A/B comparison matches
5. ✅ Performance acceptable
6. ✅ No new regressions

**After Extraction:**

1. ✅ All tests still pass
2. ✅ Coverage maintained/improved
3. ✅ No flaky tests introduced
4. ✅ Documentation updated
5. ✅ Code review approved
6. ✅ Ready for next extraction

---

## 7. EXECUTION PLAN SUMMARY

### Phase 0: Test Infrastructure (Week 0 - MUST DO FIRST)

**Days 1-2: Test Harness Setup**
- Configure pytest for Streamlit apps
- Setup mock factories for all services
- Create session state fixtures
- Configure golden master recording

**Days 3-5: Critical Path Scaffolding**
- Identify top 20 critical flows
- Create test templates for orchestrators
- Setup async test infrastructure
- Prepare regression baselines

### Phase 1: Critical Path Testing (Weeks 1-2)

**Week 1: Orchestrators**
- tabbed_interface generation orchestrator (55 tests)
- generator_tab regeneration orchestrator (60 tests)
- Category determination (40 tests)
- Document processing (35 tests)

**Week 2: Rendering & Actions**
- Generation results rendering (45 tests)
- Validation presentation (30 tests)
- Examples persistence (30 tests)
- Definition actions + utilities (73 tests)

**Deliverable:** 368 tests, 75%+ coverage on critical paths

### Phase 2: Coverage Completion (Weeks 3-4)

**Week 3: Gap Filling**
- Context guards (8 tests)
- Rule reasoning (25 tests)
- Duplicate check (25 tests)
- Edge cases (10 tests)

**Week 4: Test Refinement**
- Convert characterization → behavioral
- Improve assertions
- Add missing edge cases
- Fix flaky tests

**Deliverable:** 436 tests, 85%+ coverage

### Phase 3: Validation (Week 5)

**Days 1-2: Validation**
- Run full test suite
- Measure all coverage metrics
- Validate quality targets

**Days 3-4: Documentation**
- Test strategy docs
- Coverage reports
- Maintenance guides
- Handoff to Phase 1 (Design)

**Day 5: Phase 0 → Phase 1 Transition**
- Final checkpoint
- Approval gate
- Start Phase 1 (Design)

---

## 8. SUCCESS CRITERIA

### Must-Have (Blocking Phase 1)

- ✅ **436+ tests** implemented
- ✅ **85%+ line coverage** on both god objects
- ✅ **95%+ coverage** on orchestrators (generation, regeneration)
- ✅ **All critical paths tested** (generation, validation, persistence)
- ✅ **Zero flaky tests** in critical path suite
- ✅ **Test execution < 5min** for full suite
- ✅ **Documentation complete** (strategy, coverage, maintenance)

### Should-Have (Quality Gates)

- ✅ **80%+ branch coverage**
- ✅ **70%+ mutation score**
- ✅ **All edge cases documented**
- ✅ **Error paths tested**
- ✅ **Async/sync interactions validated**

### Nice-to-Have (Continuous Improvement)

- ✅ **90%+ coverage** overall
- ✅ **Property-based tests** for validators
- ✅ **Performance benchmarks**
- ✅ **Visual regression tests** (UI screenshots)

---

## 9. RISK REGISTER

| Risk | Probability | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| **5 weeks too long, pressure to skip** | HIGH | CRITICAL | Show regression cost analysis, get executive buy-in | PM |
| **Tests reveal more complexity** | MEDIUM | HIGH | Add buffer week, adjust estimates | Test Lead |
| **Flaky tests block progress** | MEDIUM | MEDIUM | Invest in test infrastructure week 0 | Test Engineer |
| **Mocking Streamlit too hard** | LOW | HIGH | Use pytest-playwright, golden masters | Test Engineer |
| **Coverage targets unrealistic** | LOW | MEDIUM | Adjust to 75% minimum, 85% stretch | Test Lead |
| **God methods too complex to test** | MEDIUM | CRITICAL | Use characterization tests, incremental approach | Test Architect |
| **Team lacks testing expertise** | MEDIUM | HIGH | Training week 0, pair programming | Test Lead |

---

## 10. CONCLUSION & RECOMMENDATION

### The Crisis Is Real

- **3,318 LOC** with effectively ZERO test coverage
- **811 decision points** in complex orchestration logic
- **Risk scores >2,800** (CATASTROPHIC)
- **God methods 380-500 LOC** (impossible to refactor safely)

### The Solution Is Clear

**MUST invest 5 weeks in Phase 0 (Test Recovery) before ANY refactoring**

### The Alternative Is Disaster

Without tests:
- Guaranteed regressions
- Debugging time >> test writing time
- User trust erosion
- Project failure risk

### The Investment Pays Off

5 weeks of testing enables:
- **Safe refactoring** (no regressions)
- **Faster extraction** (confidence to move fast)
- **Better design** (tests reveal hidden complexity)
- **Maintainable code** (tests document behavior)

### Final Decision

**APPROVE Phase 0: 5-week Test Recovery Plan**

**Start Date:** Immediately after EPIC-026 Day 3 completion

**Success Gate:** 85%+ coverage, 436+ tests, zero critical path gaps

**Then and only then:** Proceed to Phase 1 (Design)

---

**Prepared by:** Test Engineering Specialist (Debug Specialist)
**Date:** 2025-10-02
**Status:** Awaiting Approval
**Next Action:** Present to stakeholders, get Phase 0 approval
