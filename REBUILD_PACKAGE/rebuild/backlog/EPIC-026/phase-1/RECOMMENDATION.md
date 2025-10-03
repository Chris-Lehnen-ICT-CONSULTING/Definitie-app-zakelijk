---
id: EPIC-026-EXTRACTION-RECOMMENDATION
epic: EPIC-026
phase: 1
created: 2025-10-02
owner: code-architect
status: ready-for-approval
---

# EPIC-026 Extraction Strategy - Team Recommendation

**Date:** 2025-10-02
**Decision Required:** Orchestrator-first vs UI-first extraction strategy
**Deadline:** End of Day 3 (to stay on Phase 1 schedule)

---

## 🎯 Executive Summary

After 2 days of detailed code analysis (Day 1-2 of Phase 1), we have discovered **880 LOC of hidden orchestration logic** in the UI layer, masquerading as presentation code.

**Critical Finding:** Two massive orchestrators are hiding in plain sight:
1. **Generation Orchestrator** (380 LOC god method in `tabbed_interface.py`)
2. **Regeneration Orchestrator** (500 LOC across 8 methods in `definition_generator_tab.py`)

**Strategic Question:** Should we extract orchestrators FIRST, or split UI components first?

**Recommendation:** **EXTRACT ORCHESTRATORS FIRST** ✅

---

## 📊 The Data

### Files Analyzed (Day 1-2)

| File | LOC | Methods | Hidden Orchestrators | Hidden Services |
|------|-----|---------|---------------------|-----------------|
| `definitie_repository.py` | 1,815 | 41 | 0 | 0 |
| `tabbed_interface.py` | 1,793 | 39 | **1 (380 LOC)** | **2 (610 LOC)** |
| `definition_generator_tab.py` | 2,525 | 60 | **1 (500 LOC)** | 0 |
| **TOTAL** | **6,133** | **140** | **2 (880 LOC)** | **2 (610 LOC)** |

### Hidden Complexity Breakdown

```
Total UI LOC: 4,318
  - Actual UI logic: ~1,500 LOC (35%)
  - Hidden orchestrators: 880 LOC (20%)
  - Hidden services: 610 LOC (14%)
  - Hardcoded business logic: 180 LOC (4%)
  - Mixed concerns: ~1,200 LOC (27%)

Business Logic in UI Layer: 1,670 LOC (39% of UI!)
```

**This is why the UI is unmaintainable.**

---

## 🚨 Why This Matters

### The Generation Orchestrator (380 LOC God Method)

**Location:** `tabbed_interface.py::_handle_definition_generation()`

**What it does (in order):**
1. Validates context (min 1 of org/jur/wet required)
2. Determines ontological category (async 6-step protocol + fallbacks)
3. Checks for duplicates (stops generation if found, shows user choice)
4. Integrates document context (uploads → processing → snippet extraction)
5. Handles regeneration override (category changes)
6. Orchestrates definition generation (async via run_async bridge)
7. Stores results in 15+ session state keys
8. Prepares edit tab state
9. Cleans up regeneration context
10. Shows success message

**Services coordinated:** 5+ (Definition, Regeneration, Document, Category, Checker)
**State mutations:** 15+ session state keys
**Async operations:** 2 (category + generation)
**Early exits:** 6 different return paths
**Error handling:** 8+ try/except blocks

**Why it's critical:**
- Contains CORE business logic for entire app
- Breaking this breaks EVERYTHING
- Impossible to test in isolation
- Violates EVERY SOLID principle

---

### The Regeneration Orchestrator (500 LOC, 8 Methods)

**Location:** `definition_generator_tab.py` (lines 2008-2370)

**What it does:**
1. Analyzes category change impact (hardcoded rules for 4 category pairs)
2. Triggers regeneration in 3 modes:
   - **Direct:** Execute regeneration immediately with progress tracking
   - **Manual:** Navigate to generator with pre-filled state
   - **Keep:** Update category only, keep definition
3. Executes definition generation (async via run_async bridge)
4. Extracts context from original generation result
5. Compares old vs new definitions
6. Manages navigation state for manual mode

**Services coordinated:** 4+ (Regeneration, Category, Definition, Workflow)
**State mutations:** 7 session state keys
**Async operations:** 1 (generation via run_async)
**Workflow modes:** 3 (direct, manual, keep)

**Why it's critical:**
- Category change is a key feature
- Complex workflow with 3 different paths
- Hardcoded business rules (not data-driven)
- Scattered across 8 methods in UI component

---

## 💡 The Strategic Choice

### Option A: Extract Orchestrators FIRST ✅ **RECOMMENDED**

**Approach:**
```
Week 1:  Preparation (integration tests, pattern config, state docs)
Week 2:  Extract OntologicalCategoryService (~260 LOC from UI)
Week 3:  Extract DocumentContextService (~350 LOC from UI)
Week 4-5: Extract DefinitionGenerationOrchestrator (~380 LOC from UI)
Week 6-7: Extract RegenerationOrchestrator (~500 LOC from UI)
Week 8:  Thin UI layer (reduce to <1,200 LOC total)
Week 9:  Cleanup & documentation

Total: 9 weeks (6 weeks active extraction, 3 weeks prep/cleanup)
```

**Pros:**
- ✅ **Preserves business logic integrity** - Orchestrators extracted as coherent units
- ✅ **Reduces risk** - Clear service boundaries, easier rollback
- ✅ **Immediate impact** - 74% LOC reduction in UI after Week 8
- ✅ **Enables testing** - Orchestrators testable in isolation from day 1
- ✅ **Better architecture** - Services become source of truth
- ✅ **Parallel work** - After Week 5, UI and services can evolve independently
- ✅ **Shorter timeline** - 9 weeks vs 11+ weeks for UI-first

**Cons:**
- ⚠️ Requires comprehensive integration tests upfront (Week 1)
- ⚠️ Async pattern refactoring complexity (Week 4-5)
- ⚠️ State management migration (all weeks)

**Risk Level:** MEDIUM (with mitigation)

---

### Option B: Split UI Components FIRST ❌ **NOT RECOMMENDED**

**Approach:**
```
Week 1-2:  Split tabbed_interface.py into 7 tab components
Week 3-4:  Split definition_generator_tab.py into 8 rendering components
Week 5-8:  Extract orchestrators from split components (harder now!)
Week 9-10: Extract remaining services
Week 11:   Cleanup & documentation

Total: 11 weeks (longer due to double refactoring)
```

**Pros:**
- ✅ Smaller, more manageable files earlier
- ✅ Clear tab boundaries from start

**Cons:**
- ❌ **Scatters orchestration logic** - 380 LOC god method split across components
- ❌ **Harder to preserve business logic** - Workflow gets fragmented
- ❌ **Double refactoring** - Split UI, THEN extract orchestrators
- ❌ **Longer timeline** - 11+ weeks vs 9 weeks
- ❌ **More risk** - Breaking workflows during UI split
- ❌ **Delays testability** - Can't test orchestrators until Week 5+
- ❌ **Architecture debt** - UI components still contain business logic weeks 1-8

**Risk Level:** HIGH

---

## 🎯 Recommendation: Option A (Orchestrators First)

### Why This Is The Right Choice

1. **Business Logic Integrity**
   - Orchestrators contain the CORE workflows
   - Extracting them preserves the logic as coherent units
   - Splitting UI first fragments the workflows

2. **Risk Reduction**
   - Integration tests protect existing behavior
   - Rollback points every week
   - Service boundaries are clear once extracted

3. **Architectural Excellence**
   - Services layer becomes source of truth
   - UI becomes thin presentation layer
   - Clean separation of concerns

4. **Testability**
   - Orchestrators testable in isolation from Week 4
   - 90%+ coverage target achievable
   - Business logic no longer trapped in UI

5. **Faster Delivery**
   - 9 weeks vs 11+ weeks
   - Parallel work after Week 5
   - Immediate value (UI reduction after Week 8)

---

## 📋 Deliverables (Created Today)

**Analysis Documents:**
1. ✅ `orchestrator_extraction_plan.md` (40+ pages, complete extraction guide)
2. ✅ `orchestrator_extraction_summary.md` (executive summary)
3. ✅ `orchestrator_extraction_visual.md` (visual diagrams and flow charts)
4. ✅ `RECOMMENDATION.md` (this document)

**Supporting Analysis (Day 1-2):**
5. ✅ `definitie_repository_responsibility_map.md`
6. ✅ `definition_generator_tab_responsibility_map.md`
7. ✅ `tabbed_interface_responsibility_map.md`

**Total Documentation:** 7 comprehensive documents, ~150 pages

---

## 🗺️ The Roadmap (if Approved)

### Phase 1: Design (Current) - Day 1-5

- **Day 1:** ✅ Map definitie_repository.py
- **Day 2:** ✅ Map definition_generator_tab.py + tabbed_interface.py
- **Day 3:** Map web_lookup_service.py + validation_orchestrator_v2.py
- **Day 4:** Service boundary design across all 5 files
- **Day 5:** Extraction plan + migration strategy

**Checkpoint 1 (End Day 5):** Approve extraction strategy

---

### Phase 2: Extraction (if Approved) - Week 1-9

**Week 1: Preparation**
- Create 10+ integration tests (full generation flow, duplicate check, regeneration)
- Extract patterns to `config/ontological_patterns.yaml`
- Document session state contracts
- Create type-safe state wrappers

**Week 2: OntologicalCategoryService**
- Extract 260 LOC from tabbed_interface.py
- 3-layer fallback (6-step → quick → pattern)
- 90%+ unit test coverage

**Week 3: DocumentContextService**
- Extract 350 LOC from tabbed_interface.py
- Context aggregation + snippet extraction
- 85%+ unit test coverage

**Week 4-5: DefinitionGenerationOrchestrator ⚠️ CRITICAL**
- Extract 380 LOC god method
- 7-step workflow implementation
- Clean async patterns (no asyncio.run nesting)
- 95%+ unit test coverage

**Week 6-7: RegenerationOrchestrator ⚠️ CRITICAL**
- Extract 500 LOC regeneration logic
- 3 modes (direct, manual, keep)
- Impact analysis (data-driven)
- 90%+ unit test coverage

**Week 8: Thin UI Layer**
- Reduce tabbed_interface.py to <400 LOC
- Reduce definition_generator_tab.py to <800 LOC
- Remove all business logic
- Total UI: <1,200 LOC (74% reduction!)

**Week 9: Cleanup & Documentation**
- Remove scaffolding
- Update architecture diagrams
- Write migration guide
- Final test pass

**Checkpoint 2 (End Week 9):** Phase 2 complete, ready for Phase 3 (Validation)

---

### Phase 3: Validation (Future) - Week 10-12

- Integration testing at scale
- Performance benchmarking
- UI regression testing
- Documentation finalization
- Team training

---

## ✅ Success Criteria

### Quantitative

- [ ] UI layer reduced from 4,318 → <1,200 LOC (74% reduction)
- [ ] Largest method reduced from 380 → <50 LOC (87% reduction)
- [ ] Test coverage for orchestrators: 90%+
- [ ] All integration tests GREEN
- [ ] Zero functional regressions

### Qualitative

- [ ] UI is pure presentation (no business logic)
- [ ] Orchestrators are testable in isolation
- [ ] Service boundaries are clear and documented
- [ ] Async patterns are clean (no hacks/bridges)
- [ ] State management is centralized
- [ ] Code is maintainable (future devs understand)

---

## ⚠️ Risk Management

### Mitigation Strategies

| Risk | Mitigation | Owner |
|------|-----------|-------|
| **Breaking generation workflow** | Comprehensive integration tests Week 1 | code-architect |
| **Async/sync boundary issues** | Clean async design, proper wrappers | code-architect |
| **State management bugs** | Type-safe wrappers, schema validation | code-architect |
| **Timeline slip** | 2-week contingency buffer (11 weeks max) | project-manager |
| **Team availability** | Parallel work after Week 5 | project-manager |

### Rollback Strategy

- **Git tags** at end of each week
- **Integration tests** must be GREEN before proceeding
- **Maximum rollback window:** 2 weeks (to previous checkpoint)
- **Data loss risk:** NONE (no DB schema changes)

---

## 🏁 Decision Point

### What We Need From The Team

**Decision Required:** Approve orchestrator-first extraction strategy

**Options:**
1. ✅ **APPROVE** - Proceed with Option A (orchestrators first, 9 weeks)
2. ❌ **REVISE** - Choose Option B (UI-first, 11+ weeks) or alternative approach
3. ⏸️ **DEFER** - More analysis needed (Day 6 deep dive)

**Timeline Impact:**
- Approve today (Day 2): Start Week 1 prep on Day 4-5, extraction Week 2
- Revise today: Adjust plan Day 3-5, extraction Week 2
- Defer: Add Day 6 analysis, extraction Week 3 (1 week slip)

---

## 📞 Next Steps (if Approved)

### Immediate (Day 3)
1. Complete remaining responsibility maps (web_lookup_service, validation_orchestrator_v2)
2. Team review of this recommendation
3. **DECISION:** Approve orchestrator-first strategy

### Day 4-5 (Prep for Week 1)
1. Set up project tracking (EPIC-026 Phase 2, user stories per week)
2. Set up CI/CD for integration tests
3. Assign owners for Week 1 tasks

### Week 1 (if approved)
1. Create integration test suite (10+ scenarios)
2. Extract patterns to config
3. Document state contracts
4. Create type-safe wrappers

### Week 2+ (Execution)
1. Execute extraction plan week-by-week
2. Daily standups for progress tracking
3. Weekly reviews for risk assessment
4. Adjust as needed (stay within 11-week buffer)

---

## 💬 Questions & Answers

### Q: Why can't we do UI splitting and orchestrator extraction in parallel?

**A:** The 380 LOC god method contains the orchestration logic. If we split the UI first, we have to decide:
- Duplicate the orchestration logic across split components? (duplication debt)
- Keep it in one component? (still a god object, just in a different file)
- Split the orchestration logic? (fragments the workflow, harder to extract later)

Extracting orchestrators FIRST means we remove the complexity before splitting, making UI splitting trivial.

---

### Q: What if the integration tests reveal unknown dependencies?

**A:** Week 1 is specifically for discovering these issues. If we find unexpected dependencies:
1. Document them
2. Adjust extraction plan (might add 1-2 weeks)
3. Still better than discovering mid-extraction

This is why Week 1 prep is CRITICAL.

---

### Q: How confident are you in the 9-week estimate?

**A:** Confidence level: **MEDIUM-HIGH**

**Conservative estimate:**
- 2 weeks contingency built in (11 weeks max)
- Based on detailed LOC analysis (not guessing)
- Clear checkpoints for reassessment

**Risks to timeline:**
- Week 4-5 (Generation Orchestrator) is most complex - might need extra week
- Week 6-7 (Regeneration Orchestrator) might need extra week
- If both slip: 11 weeks total (still acceptable)

**Acceleration opportunities:**
- Parallel work after Week 5 could save 1-2 weeks
- If services extract cleanly, could finish Week 8 early

---

### Q: What's the biggest risk?

**A:** **Breaking the generation workflow during orchestrator extraction (Week 4-5).**

**Why it's risky:**
- 380 LOC god method with 15+ state mutations
- Complex async/sync mixing
- Touches 5+ services
- Core business logic for entire app

**Mitigation:**
- Week 1: Comprehensive integration tests (10+ scenarios)
- Week 4-5: Incremental extraction (one step at a time)
- Daily testing after each change
- Rollback checkpoints every 2 days
- 2-week buffer in timeline

---

### Q: What if we need to pause mid-extraction?

**A:** Every week is a safe rollback checkpoint:

- Week 1: Can pause with tests in place, no code changes
- Week 2: Can pause with Category service extracted, UI still works
- Week 3: Can pause with Document service extracted, UI still works
- Week 5: Can pause with Generation Orchestrator extracted, UI still works
- Week 7: Can pause with Regeneration Orchestrator extracted, UI still works

**We NEVER leave code in a broken state.**

---

## 🎯 The Bottom Line

### We have 880 LOC of business logic hiding in UI components.

**This is why:**
- UI is unmaintainable (god objects)
- Testing is impossible (logic trapped in UI)
- Features are hard to add (everything is coupled)
- Bugs are frequent (complex state management)

**The solution:**
- Extract orchestrators FIRST (Week 4-7)
- Extract services (Week 2-3)
- Thin UI layer (Week 8)
- Clean architecture (Week 9)

**The result:**
- 74% LOC reduction in UI
- 90%+ test coverage for orchestrators
- Clean, maintainable, testable code
- Faster feature development

---

## 📋 Approval Checklist

**Before approving, confirm:**
- [ ] Team has reviewed all 4 extraction documents
- [ ] Questions answered
- [ ] Risks understood and acceptable
- [ ] Timeline is realistic (9-11 weeks)
- [ ] Resources available (code-architect lead, team support)
- [ ] Stakeholders informed

**If all checked, recommend:** ✅ **APPROVE ORCHESTRATOR-FIRST STRATEGY**

---

**Status:** ✅ READY FOR TEAM DECISION
**Deadline:** End of Day 3
**Fallback:** If not approved, add Day 6 for alternative approach

---

**Prepared by:** Code Architect
**Date:** 2025-10-02
**EPIC:** EPIC-026 Phase 1 (Design)
**Phase:** Day 2 of 5 (40% complete)

---

## 📚 Appendix: Document Index

**Analysis Documents (Day 2):**
1. `orchestrator_extraction_plan.md` - Complete 9-week extraction guide (40+ pages)
2. `orchestrator_extraction_summary.md` - Executive summary (15 pages)
3. `orchestrator_extraction_visual.md` - Visual diagrams and flows (20 pages)
4. `RECOMMENDATION.md` - This document (team decision)

**Responsibility Maps (Day 1-2):**
5. `definitie_repository_responsibility_map.md` (Day 1)
6. `definition_generator_tab_responsibility_map.md` (Day 2)
7. `tabbed_interface_responsibility_map.md` (Day 2)

**To be created (Day 3):**
8. `web_lookup_service_responsibility_map.md`
9. `validation_orchestrator_v2_responsibility_map.md`

**All documents available in:** `/docs/backlog/EPIC-026/phase-1/`
