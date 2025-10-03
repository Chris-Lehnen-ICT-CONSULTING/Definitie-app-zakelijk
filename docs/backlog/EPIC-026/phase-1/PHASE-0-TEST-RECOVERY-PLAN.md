---
id: EPIC-026-PHASE-0-PLAN
epic: EPIC-026
phase: 0
titel: Test Recovery Plan (5 weeks)
owner: test-engineer
created: 2025-10-03
status: pending-approval
budget: €25,000
---

# EPIC-026 Phase 0: Test Recovery Plan

**Phase:** 0 (Test Foundation)
**Duration:** 5 weeks (25 days)
**Budget:** €25,000
**Owner:** Test Engineer
**Priority:** CRITICAL (blocks all refactoring)

---

## Executive Summary

### The Crisis

**Current State:**
- tabbed_interface.py: **0 tests** for 1,793 LOC (Regression Risk: 3,156 ☢️)
- definition_generator_tab.py: **1 test** for 2,525 LOC (Regression Risk: 2,847 🔴)
- **Combined:** 0.02% test coverage for 4,318 LOC being refactored

**The Risk:**
Refactoring without tests = **guaranteed regressions**. 380 LOC god method with 15 state mutations, 6 early exits, 8 try/except blocks cannot be safely extracted blind.

---

### The Solution: Phase 0

**5-Week Test Recovery:**
1. **Week 1:** Build test infrastructure (pytest-playwright, golden master)
2. **Week 2-3:** Create 368 critical path tests (orchestrators)
3. **Week 4:** Create 68 coverage gap tests (UI, edge cases)
4. **Week 5:** Validate, fix flaky tests, export golden baseline

**Deliverable:** 436+ tests, 85% coverage, <5% flaky, golden baseline (42 definitions)

**Gate 1 (Week 5):** Cannot proceed to Phase 1 without 85% coverage

---

### Investment & ROI

**Cost:** €25,000 (5 weeks × €5,000/week test engineer)

**Value:**
- Prevents 10-20 regressions (€2,000/regression × 15 avg = €30k saved)
- Enables safe refactoring (prevents project failure)
- Creates reusable test suite (protects future changes)

**ROI:** 120% immediate (€30k saved / €25k invested)

---

## Week-by-Week Plan

### Week 1: Test Infrastructure Setup

**Goal:** Operational test harness for Streamlit + Golden Master framework

**User Story:** US-640 (Set up Test Infrastructure)

---

#### Day 1-2: Streamlit Test Harness

**Tasks:**
1. Install pytest-playwright, pytest-asyncio, pytest-mock
2. Configure playwright (chromium browser)
3. Create `tests/epic-026/conftest.py` with fixtures
4. Write 5 basic tests (app launches, navigation, session state)

**Deliverables:**
```python
# tests/epic-026/conftest.py
@pytest.fixture
def streamlit_app():
    """Launch Streamlit app in test mode"""
    proc = subprocess.Popen(
        ["streamlit", "run", "src/main.py", "--server.headless=true"],
        env={"TESTING": "true"}
    )
    page = playwright.chromium.launch().new_page()
    page.goto("http://localhost:8501")
    yield page
    page.close()
    proc.terminate()

# tests/epic-026/infrastructure/test_harness.py
def test_app_launches(streamlit_app):
    """Streamlit app starts without errors"""
    assert streamlit_app.title() == "DefinitieAgent"

def test_navigate_to_generator(streamlit_app):
    """Can navigate to definition generator tab"""
    streamlit_app.click("text=Definitie Genereren")
    assert streamlit_app.is_visible("text=Begrip")
```

**Success Criteria:**
- [ ] 5 basic tests passing
- [ ] Tests run in CI/CD
- [ ] Test execution time <30 seconds

---

#### Day 3-4: Golden Master Framework

**Tasks:**
1. Install pytest-golden or custom implementation
2. Create golden baseline directory structure
3. Write golden master helper functions
4. Test with 5 definition generation scenarios

**Deliverables:**
```python
# tests/epic-026/fixtures/golden_master.py
def assert_golden_match(result, baseline_file, tolerance=0.0):
    """Compare result against golden baseline"""
    baseline_path = Path("tests/epic-026/fixtures/golden_baselines") / baseline_file

    if not baseline_path.exists():
        # First run: record baseline
        baseline_path.write_text(json.dumps(result, indent=2))
        pytest.skip("Golden baseline recorded, run again to validate")

    baseline = json.loads(baseline_path.read_text())

    # Compare
    diff = DeepDiff(baseline, result, ignore_order=True)

    if diff and not within_tolerance(diff, tolerance):
        pytest.fail(f"Golden baseline mismatch:\n{diff}")

# tests/epic-026/integration/test_golden_master.py
def test_definition_generation_golden_master():
    """Definition generation matches golden baseline"""
    result = generate_definition("Toezicht", org=["IGJ"])
    assert_golden_match(result, "test_generation_toezicht.json", tolerance=0.05)
```

**Success Criteria:**
- [ ] Golden master framework operational
- [ ] 5 golden baselines recorded
- [ ] Comparison logic working (diff detection)

---

#### Day 5: Async Test Patterns + Integration PoC

**Tasks:**
1. Create async test fixtures (event loop, async mocks)
2. Test asyncio.run() bridge pattern
3. Write 5 integration tests (end-to-end scenarios)

**Deliverables:**
```python
# tests/epic-026/infrastructure/test_async.py
@pytest.mark.asyncio
async def test_async_category_determination():
    """Async category determination works without race conditions"""
    mock_ai = MockAIService(response="Toezicht")
    category_service = CategoryService(ai_service=mock_ai)

    result = await category_service.determine("Verificatie")

    assert result.category == "Toezicht"
    assert result.method == "6-step-protocol"

# tests/epic-026/integration/test_generation_flow.py
def test_full_generation_flow():
    """End-to-end: Generate definition (happy path)"""
    page = launch_streamlit_app()

    # Fill form
    page.fill("input[aria-label='Begrip']", "Toezicht")
    page.select_option("select[aria-label='Organisatie']", "IGJ")

    # Generate
    page.click("button:has-text('Genereer Definitie')")

    # Wait for result
    page.wait_for_selector("text=Definitie gegenereerd", timeout=10000)

    # Verify
    definition = page.text_content(".generated-definition")
    assert "toezicht" in definition.lower()
    assert len(definition) >= 50  # ARAI-01: min length
```

**Success Criteria:**
- [ ] Async tests run without flakiness
- [ ] 5 integration tests passing
- [ ] CI/CD pipeline configured

---

**Week 1 Checkpoint:**
- Infrastructure: ✅ Operational
- Basic tests: ✅ 15 tests passing (5 harness + 5 golden + 5 integration)
- CI/CD: ✅ Automated
- **GO/NO-GO:** If infrastructure not working by Day 5 → Extend Week 1 by 2 days

---

### Week 2-3: Critical Path Tests (368 tests)

**Goal:** 85% coverage for generation + regeneration orchestrators

**User Story:** US-454 (Create Generation Orchestrator Tests)

---

#### Week 2 Focus: Generation Orchestrator (150 tests)

**Day 6-7: 10-Step Workflow Tests (50 tests)**

**Test Matrix:**
- 10 steps × 5 scenarios each = 50 tests

**Scenarios per step:**
1. Happy path (step succeeds)
2. Step fails (exception thrown)
3. Step returns empty (edge case)
4. Step times out (async)
5. Invalid input (validation)

**Example:**
```python
# Step 2: Category Determination
def test_step2_category_determination_happy_path():
    """Category determination succeeds (6-step protocol)"""
    # Test implementation

def test_step2_category_determination_timeout():
    """Category determination times out, falls back to quick analyzer"""
    # Test implementation

def test_step2_category_determination_all_fallbacks_fail():
    """All category determination methods fail, use default"""
    # Test implementation
```

**Success Criteria:** 50 tests passing by end of Day 7

---

**Day 8-9: State Mutation Tests (45 tests)**

**15 state mutations × 3 states each:**
- Before mutation (state = A)
- After mutation (state = B)
- Rollback on error (state = A again)

**Example:**
```python
def test_state_mutation_category():
    """Category is stored in session state"""
    state = MockSessionState()
    orchestrator = GenerationOrchestrator(state_manager=state)

    result = orchestrator.generate(request)

    assert state.get("category") == "Toezicht"
    assert state.get("category_confidence") == 0.85

def test_state_mutation_rollback_on_error():
    """State mutations rollback if generation fails"""
    state = MockSessionState({"category": "Old"})
    orchestrator = GenerationOrchestrator(state_manager=state)

    with pytest.raises(GenerationError):
        orchestrator.generate(invalid_request)

    # State unchanged (rollback)
    assert state.get("category") == "Old"
```

**Success Criteria:** 45 tests passing by end of Day 9

---

**Day 10: Error Paths + Edge Cases (55 tests)**

**Error paths (24 tests):**
- 8 try/except blocks × 3 exception types each = 24 tests

**Edge cases (31 tests):**
- Empty inputs (5 tests)
- Very large inputs (5 tests)
- Special characters (5 tests)
- Concurrent requests (5 tests)
- Network failures (5 tests)
- State corruption (6 tests)

**Success Criteria:** 55 tests passing by end of Day 10

---

**Week 2 Checkpoint:**
- Generation Orchestrator: ✅ 150 tests passing
- Coverage: ⚠️ Target 85%, acceptable 70%
- Flaky tests: ⚠️ <10% (goal: <5%)

---

#### Week 3 Focus: Category + Document Services (218 tests)

**Day 11-12: Category Determination Tests (100 tests)**

**6-Step Protocol (30 tests):**
- Full ontological analysis (10 tests)
- Quick analyzer fallback (10 tests)
- Legacy pattern matching (10 tests)

**Pattern Matching (40 tests):**
- 4 categories × 10 patterns each = 40 tests

**Scoring Algorithm (15 tests):**
- Pattern count weighting (5 tests)
- Confidence thresholds (5 tests)
- Tie-breaking (5 tests)

**Reasoning Generation (15 tests):**
- Generate explanation for category choice

**Success Criteria:** 100 tests passing by end of Day 12

---

**Day 13-14: Document Context Tests (118 tests)**

**Upload & Processing (40 tests):**
- Single/multiple PDFs (10 tests)
- Large PDFs (>10 pages) (10 tests)
- Corrupt PDFs (5 tests)
- Non-PDF files (5 tests)
- Empty PDFs (5 tests)
- Security (5 tests: malicious PDFs, XSS)

**Snippet Extraction (48 tests):**
- Begriff occurs 0x, 1x, 5x, 10x in document (16 tests)
- 280 character window (16 tests: before/after variations)
- Edge positions (16 tests: start/end of document)

**Context Aggregation (30 tests):**
- 1-5 documents × 1-2 snippets each (15 tests)
- Deduplication (10 tests)
- Max snippets limit (5 tests)

**Success Criteria:** 118 tests passing by end of Day 14

---

**Day 15: Integration Tests (30 scenarios)**

**End-to-End Scenarios:**
1. Generate definition (Toezicht, org=IGJ) - success
2. Generate definition (duplicate found) - show dialog, user cancels
3. Generate definition (duplicate found) - user chooses "edit existing"
4. Generate definition (category change) - trigger regeneration direct mode
5. Generate definition (category change) - trigger regeneration manual mode
6. Generate definition (with 2 PDFs) - context included in prompt
7. Generate definition (validation fails) - show errors, allow retry
8. Generate definition (AI service timeout) - retry logic
9. Generate definition (concurrent requests) - queue handling
10. Generate definition (empty begrip) - validation error
11-30: Additional scenarios (see test suite)

**Success Criteria:** 30 integration scenarios passing by end of Day 15

---

**Week 3 Checkpoint:**
- Total tests: ✅ 368+ tests (150 + 100 + 118 + 30)
- Coverage: ⚠️ Target 85%, minimum 75%
- Flaky tests: ⚠️ <10% (still above goal)
- **GO/NO-GO:** If <250 tests or <70% coverage → Extend to Week 4

---

### Week 4: Coverage Gaps (68 tests)

**Goal:** Fill coverage gaps in UI, error paths, edge cases

---

#### Day 16-17: UI Rendering Tests (40 tests)

**Navigation (10 tests):**
- Tab switching (7 tabs)
- Back/forward navigation
- State preservation across tabs

**Rendering (15 tests):**
- Definition display formatting
- Validation results display (colors, icons)
- Error messages
- Success notifications
- Loading spinners

**Form Validation (15 tests):**
- Required fields (begrip, context)
- Input sanitization (XSS prevention)
- Max lengths (begrip: 100 chars)
- Special characters handling

**Success Criteria:** 40 tests passing by end of Day 17

---

#### Day 18-19: Edge Case Tests (28 tests)

**Boundary Values (10 tests):**
- Definition length: exactly 50 chars (ARAI-01 min)
- Definition length: exactly 500 chars (ARAI-01 max)
- Sentence count: exactly 3 sentences (SAM-01 max)
- Document size: exactly 10 pages
- Snippet window: exactly 280 chars

**Race Conditions (8 tests):**
- Concurrent definition generation
- State updates during async operations
- User navigates away during generation
- Browser back button during async

**Unicode & Special Chars (10 tests):**
- Emoji in begrip (🔍 Toezicht)
- Special chars (ä, ü, ñ, €, ©)
- RTL text (Hebrew, Arabic)
- Zero-width characters
- Control characters

**Success Criteria:** 28 tests passing by end of Day 19

---

#### Day 20: Mutation Testing

**Goal:** Validate that tests actually catch bugs

**Process:**
1. Introduce bugs in code (mutate: `if x > 0` → `if x >= 0`)
2. Run tests, verify they fail
3. If tests pass → False positive! (test is wrong)

**Mutation Operators:**
- Boundary mutations (`>` → `>=`, `<` → `<=`)
- Arithmetic mutations (`+` → `-`, `*` → `/`)
- Boolean mutations (`and` → `or`, `not x` → `x`)
- Return value mutations (`return True` → `return False`)

**Target:** 80%+ mutation score (80% of mutants killed by tests)

**Success Criteria:**
- [ ] Mutation score: 80%+
- [ ] False positives identified and fixed
- [ ] Weak tests strengthened

---

**Week 4 Checkpoint:**
- Coverage gap tests: ✅ 68 tests passing
- Total tests: ✅ 436+ tests (368 + 68)
- Mutation score: ✅ 80%+
- Coverage: ⚠️ Target 85%, minimum 80%

---

### Week 5: Validation & Golden Baseline

**Goal:** Fix flaky tests, export golden baseline, final validation

---

#### Day 21-22: Flaky Test Cleanup

**Current State:** ~10% flaky tests (goal: <5%)

**Common Causes:**
1. **Race conditions** (async timing)
2. **Implicit waits** (time.sleep instead of explicit wait)
3. **Shared state** (tests pollute each other)
4. **Network flakiness** (external API calls)
5. **Resource leaks** (unclosed connections)

**Remediation:**
```python
# BAD: Implicit wait
def test_generation_flaky():
    page.click("Generate")
    time.sleep(2)  # Race condition!
    assert page.is_visible("Result")

# GOOD: Explicit wait
def test_generation_reliable():
    page.click("Generate")
    page.wait_for_selector("Result", timeout=10000)  # Explicit wait
    assert page.is_visible("Result")

# BAD: Shared state
def test_shared_state_flaky():
    generate_definition("Toezicht")  # Mutates global state
    # Another test fails if run after this

# GOOD: Isolated state
def test_isolated_state_reliable(clean_session_state):
    with isolated_state():
        generate_definition("Toezicht")
    # State cleaned up automatically
```

**Process:**
1. Identify flaky tests (run suite 100x, track failures)
2. Fix flaky tests (add explicit waits, isolate state)
3. Re-run 100x to verify fix
4. Goal: <5% flakiness rate

**Success Criteria:**
- [ ] Flaky tests identified: 40-50 tests (10% of 436)
- [ ] Flaky tests fixed: 20-30 tests (reduce to 5%)
- [ ] Test suite runs 100x with <5% failures

---

#### Day 23: Performance Benchmarks

**Goal:** Establish performance baselines (prevent degradation during refactoring)

**Benchmarks:**
1. **Definition generation time:** < 5 seconds (mean)
2. **Validation time:** < 1 second (mean)
3. **Duplicate check time:** < 500ms (mean)
4. **Category determination:** < 3 seconds (mean)
5. **Document processing:** < 10 seconds per PDF (mean)

**Tool:** pytest-benchmark

```python
def test_benchmark_definition_generation(benchmark):
    """Benchmark definition generation performance"""
    result = benchmark(
        generate_definition,
        begrip="Toezicht",
        context={"org": ["IGJ"]}
    )

    assert benchmark.stats.mean < 5.0  # < 5 seconds
    assert result.success is True
```

**Deliverable:** `docs/testing/EPIC-026-performance-baselines.md`

**Success Criteria:**
- [ ] 10 benchmarks recorded
- [ ] Baseline thresholds defined
- [ ] CI/CD performance regression check

---

#### Day 24: Export Golden Baseline

**Goal:** Export 42 existing definitions (pre-refactor baseline)

**Process:**
1. Export all 42 definitions from `data/definities.db`
2. For each definition, record:
   - Begrip, definitie, category, context
   - Validation results (all 46 rules)
   - Voorbeelden (examples)
   - Metadata (created date, status)
3. Save to `data/golden_baseline_epic026/`
4. Create validation script (compares post-refactor)

**Script:**
```bash
# scripts/export_golden_baseline.py
python scripts/export_golden_baseline.py \
  --output data/golden_baseline_epic026/ \
  --format json \
  --include-validation \
  --include-voorbeelden

# Output:
# data/golden_baseline_epic026/
# ├── definitions/
# │   ├── def_001_toezicht.json
# │   ├── def_002_sanctionering.json
# │   └── ... (42 total)
# ├── validation_results/
# │   ├── def_001_validation.json
# │   └── ... (42 total)
# └── manifest.json (metadata)
```

**Validation Script:**
```python
# tests/epic-026/validation/test_golden_baseline.py
def test_golden_baseline_all_definitions():
    """All 42 definitions match golden baseline after refactoring"""
    baseline = load_golden_baseline()

    for definition in baseline:
        # Re-generate definition
        result = generate_definition(
            begrip=definition.begrip,
            context=definition.context
        )

        # Compare
        assert_golden_match(result, definition, tolerance=0.05)
        # 0% tolerance for business logic
        # 5% tolerance for LLM variance (wording differences)
```

**Success Criteria:**
- [ ] 42 definitions exported
- [ ] Validation results included
- [ ] Manifest created (metadata)
- [ ] Validation script ready

---

#### Day 25: Final Validation & Gate 1 Review

**Goal:** Verify all Phase 0 success criteria met

**Checklist:**

**Test Coverage:**
- [ ] 436+ tests created
- [ ] 85%+ coverage for god objects (generator_tab, tabbed_interface)
- [ ] 368 critical path tests (orchestrators)
- [ ] 68 coverage gap tests (UI, edge cases)

**Test Quality:**
- [ ] <5% flaky tests (40-50 → 20-30 fixed)
- [ ] 80%+ mutation score
- [ ] All integration tests passing (30 scenarios)

**Infrastructure:**
- [ ] Streamlit test harness operational
- [ ] Golden master framework working
- [ ] CI/CD pipeline configured
- [ ] Performance benchmarks recorded

**Golden Baseline:**
- [ ] 42 definitions exported
- [ ] Validation results included
- [ ] Validation script ready

**Documentation:**
- [ ] Test infrastructure guide (`docs/testing/EPIC-026-test-infrastructure.md`)
- [ ] Performance baselines (`docs/testing/EPIC-026-performance-baselines.md`)
- [ ] Golden baseline manifest (`data/golden_baseline_epic026/manifest.json`)

---

**Gate 1 Decision:**

✅ **GO to Phase 1:** If ALL criteria met
⚠️ **EXTEND Phase 0:** If 70-85% coverage (add 1-2 weeks)
❌ **ABORT Epic:** If <70% coverage (god objects too complex to test)

---

## Success Metrics

### Quantitative

| Metric | Baseline | Target | Validation |
|--------|----------|--------|------------|
| **Test count** | 1 test | 436+ tests | pytest --count |
| **Coverage** | 0.02% | 85%+ | pytest --cov |
| **Flaky tests** | N/A | <5% | 100x run |
| **Mutation score** | N/A | 80%+ | mutmut |
| **Integration tests** | 0 | 30 scenarios | pytest -m integration |
| **Performance** | Unknown | <5s generation | pytest-benchmark |
| **Golden baseline** | 0 | 42 definitions | manifest.json |

### Qualitative

- [ ] Test infrastructure is production-ready
- [ ] Tests are maintainable (clear, documented)
- [ ] Tests are fast (<5 minutes for full suite)
- [ ] Tests catch regressions (mutation testing proves)
- [ ] Team is trained on test patterns (1 hour session)

---

## Risk Management

### Critical Risks

**R10: Test Coverage Catastrophe**
- **Mitigation:** Phase 0 addresses directly
- **Residual Risk:** MEDIUM (what if 85% not achievable?)
- **Contingency:** If <85% after Week 5 → Extend 2 weeks or abort

**R16: Integration Test False Positives**
- **Mitigation:** Mutation testing (Day 20)
- **Residual Risk:** MEDIUM (complex workflows hard to test)
- **Contingency:** Golden master testing catches what integration tests miss

**R2: Timeline Overrun**
- **Likelihood:** MEDIUM (5 weeks → 6-7 weeks)
- **Mitigation:** Weekly checkpoints, can extend Week 1 by 2 days
- **Contingency:** 2-week buffer budgeted

---

### High Risks

**Flaky Tests:**
- Target: <5%, likely: 10%
- Impact: Blocks Gate 1
- Mitigation: Day 21-22 dedicated to fixing

**God Methods Too Complex:**
- 380 LOC method may be untestable in isolation
- Mitigation: Characterization tests + golden master
- Contingency: Test at integration level (not unit level)

**Async Test Flakiness:**
- Async + UI = high flakiness risk
- Mitigation: Explicit waits, isolated event loops
- Contingency: Increase timeout thresholds (trade speed for reliability)

---

## Budget Breakdown

**Total: €25,000**

| Week | Activity | Cost | Cumulative |
|------|----------|------|------------|
| Week 1 | Infrastructure setup | €5,000 | €5,000 |
| Week 2 | Generation orchestrator tests | €5,000 | €10,000 |
| Week 3 | Category + document tests | €5,000 | €15,000 |
| Week 4 | Coverage gaps + mutation | €5,000 | €20,000 |
| Week 5 | Validation + golden baseline | €5,000 | €25,000 |

**Resource:** Test Engineer (40 hrs/week × 5 weeks = 200 hours @ €125/hr)

**Contingency:** €5,000 (Week 6-7 if extension needed)

---

## Deliverables

### Code Deliverables

**Test Suite:**
- `tests/epic-026/` (436+ tests)
- `tests/epic-026/conftest.py` (shared fixtures)
- `tests/epic-026/infrastructure/` (harness, golden master, async)
- `tests/epic-026/integration/` (30 scenarios)
- `tests/epic-026/fixtures/` (mocks, golden baselines)

**Scripts:**
- `scripts/export_golden_baseline.py` (export 42 definitions)
- `scripts/validate_golden_baseline.py` (compare post-refactor)
- `scripts/run_mutation_tests.sh` (mutation testing)

---

### Documentation Deliverables

**Guides:**
- `docs/testing/EPIC-026-test-infrastructure.md` (how to write tests)
- `docs/testing/EPIC-026-performance-baselines.md` (benchmarks)
- `docs/testing/EPIC-026-golden-baseline-guide.md` (golden master usage)

**Data:**
- `data/golden_baseline_epic026/manifest.json` (42 definitions metadata)
- `data/golden_baseline_epic026/definitions/*.json` (42 definition files)
- `data/golden_baseline_epic026/validation_results/*.json` (validation results)

---

## Next Steps After Phase 0

**If Gate 1 PASSED (85%+ coverage):**
1. Proceed to Phase 1 (Repository Refactor, 3 weeks)
2. Measure velocity improvement after Phase 1
3. Decide: Continue to Phase 2 (UI Orchestrators) or stop?

**If Gate 1 EXTENDED (70-85% coverage):**
1. Extend Phase 0 by 1-2 weeks (target 85%)
2. Re-assess at end of Week 6-7
3. If still <85%: Accept 75-80% coverage, proceed with caution

**If Gate 1 FAILED (<70% coverage):**
1. Abort EPIC-026 (god objects too complex to test safely)
2. Alternative: Incremental strangler pattern (build new, deprecate old)
3. Alternative: Accept technical debt, focus on new features

---

**Status:** Pending Approval
**Next Action:** Stakeholder review, approve €25k budget for Phase 0
**Start Date:** TBD (after approval + test engineer assignment)
**End Date:** Start + 5 weeks (Gate 1 review)
