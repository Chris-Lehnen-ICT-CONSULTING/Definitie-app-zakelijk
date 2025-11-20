# DEF-155 Context Consolidation - Action Checklist

**Purpose:** Quick reference for developer implementing context consolidation
**Status:** Ready to use - follow in order
**Last Updated:** 2025-11-13

---

## ⚡ Quick Start

**Before you do ANYTHING:**
1. Read `DEF-155-EXECUTIVE-RISK-SUMMARY.md` (5 minutes)
2. Complete "Pre-Flight Checklist" below
3. Only proceed if all ✓

---

## 🚦 Pre-Flight Checklist (MANDATORY)

**Do NOT start implementation until ALL items are ✓**

### Planning
- [ ] Read executive risk summary
- [ ] Understand 11.5-hour timeline (not 6 hours)
- [ ] Understand blocking condition: quality ≥95% of baseline
- [ ] User approval obtained (>100 lines)
- [ ] Schedule available (11.5 hours over 2 days)

### Preparation
- [ ] Git branch created: `feature/DEF-155-context-consolidation`
- [ ] Baseline capture plan understood (Phase 0)
- [ ] Real context samples available (from database)
- [ ] Test fixtures directory created: `tests/fixtures/DEF-155-baseline/`

### Risk Understanding
- [ ] Understand Risk #1: Silent context loss
- [ ] Understand Risk #3: Circular validation trap
- [ ] Understand Risk #4: Test false positives
- [ ] Know that skipping Phase 0 or 9.5 = FAILURE

**If any item is ☐:** STOP - address gaps first

**If all items are ✓:** ✅ PROCEED to Phase 0

---

## 📋 Phase-by-Phase Checklist

### Phase 0: Baseline Capture (1 hour) ⭐ MANDATORY

**Purpose:** Capture current system output for comparison

- [ ] **0.1** Select 20 test cases
  - [ ] 5 with org context only
  - [ ] 5 with juridical context only
  - [ ] 5 with legal basis context only
  - [ ] 3 with multiple contexts
  - [ ] 2 with no context
- [ ] **0.2** Create test script: `tests/debug/capture_baseline.py`
- [ ] **0.3** Run script: Generate prompts with CURRENT system
- [ ] **0.4** Save prompts to `tests/fixtures/DEF-155-baseline/prompts/`
- [ ] **0.5** Generate definitions with CURRENT system
- [ ] **0.6** Save definitions to `tests/fixtures/DEF-155-baseline/definitions/`
- [ ] **0.7** Run validation on all 20 definitions
- [ ] **0.8** Save scores to `tests/fixtures/DEF-155-baseline/scores.csv`
- [ ] **0.9** Verify all files created correctly
- [ ] **0.10** Git commit: `test(DEF-155): baseline capture for migration validation`

**Acceptance:**
- ✓ 20 prompt files exist
- ✓ 20 definition JSON files exist
- ✓ scores.csv has 20 rows with scores
- ✓ Committed to git (so it's preserved)

**Time checkpoint:** Should take ~1 hour. If longer, you're doing too much manual work.

---

### Phase 1: Create Skeleton (30 min)

**Purpose:** Create new module structure

- [ ] **1.1** Create file: `src/services/prompts/modules/context_instruction_module.py`
- [ ] **1.2** Copy skeleton from implementation plan (lines 314-378)
- [ ] **1.3** Implement `__init__()` with priority=75
- [ ] **1.4** Implement `initialize()` with config handling
- [ ] **1.5** Implement `validate_input()` (always returns True)
- [ ] **1.6** Implement stub `execute()` (return empty ModuleOutput)
- [ ] **1.7** Implement `get_dependencies()` (return empty list)
- [ ] **1.8** Add docstring explaining Single Source of Truth
- [ ] **1.9** Test: `python -m py_compile src/services/prompts/modules/context_instruction_module.py`
- [ ] **1.10** Git commit: `feat(DEF-155): Phase 1 - Create ContextInstructionModule skeleton`

**Acceptance:**
- ✓ File compiles without errors
- ✓ Module has all required methods
- ✓ Docstring explains responsibility

---

### Phase 2: Migrate Business Logic (2 hours)

#### Phase 2.1: Context Richness Scoring (30 min)

- [ ] **2.1.1** Copy `_calculate_context_score()` from context_awareness_module.py (lines 143-184)
- [ ] **2.1.2** Paste into ContextInstructionModule
- [ ] **2.1.3** Verify imports (EnrichedContext accessible)
- [ ] **2.1.4** Update execute() to call this method
- [ ] **2.1.5** Update execute() to store score in shared_state
- [ ] **2.1.6** Test: Create test_context_instruction_module.py
- [ ] **2.1.7** Write test_context_richness_scoring()
- [ ] **2.1.8** Run: `pytest tests/.../test_context_instruction_module.py::test_context_richness_scoring -v`
- [ ] **2.1.9** Verify score between 0.0-1.0
- [ ] **2.1.10** Git commit: `feat(DEF-155): Phase 2.1 - Migrate context richness scoring`

#### Phase 2.2: Adaptive Formatting (30 min)

- [ ] **2.2.1** Copy rich/moderate/minimal section methods (lines 186-280)
- [ ] **2.2.2** Copy helper methods: `_format_detailed_base_context()`, etc.
- [ ] **2.2.3** Consolidate into single `_build_context_instructions()` method
- [ ] **2.2.4** Use score-based switch: if score >= 0.8: rich, elif >= 0.5: moderate, else: minimal
- [ ] **2.2.5** Update execute() to call `_build_context_instructions()`
- [ ] **2.2.6** Write test_adaptive_formatting_rich/moderate/minimal()
- [ ] **2.2.7** Run tests: verify correct formatting for each level
- [ ] **2.2.8** Git commit: `feat(DEF-155): Phase 2.2 - Migrate adaptive formatting`

#### Phase 2.3: Context Forbidden Patterns (30 min)

- [ ] **2.3.1** Copy `_build_context_forbidden()` from error_prevention_module.py (lines 193-245)
- [ ] **2.3.2** Move ORGANIZATION_MAPPINGS to module-level constant
- [ ] **2.3.3** Update method to use shared_state data
- [ ] **2.3.4** Integrate into execute(): add forbidden section to output
- [ ] **2.3.5** Write test_context_forbidden_patterns()
- [ ] **2.3.6** Write test_organization_mapping()
- [ ] **2.3.7** Run tests: verify forbidden patterns generated
- [ ] **2.3.8** Git commit: `feat(DEF-155): Phase 2.3 - Migrate context forbidden patterns`

#### Phase 2.4: Context Metadata (30 min)

- [ ] **2.4.1** Copy `_build_prompt_metadata()` from definition_task_module.py (lines 259-299)
- [ ] **2.4.2** Rename to `_build_context_metadata()`
- [ ] **2.4.3** Update to use shared_state (not direct base_context access)
- [ ] **2.4.4** Make conditional on `self.include_metadata` flag
- [ ] **2.4.5** Integrate into execute(): add metadata as footer
- [ ] **2.4.6** Write test_context_metadata()
- [ ] **2.4.7** Run tests: verify metadata present when enabled
- [ ] **2.4.8** Git commit: `feat(DEF-155): Phase 2.4 - Migrate context metadata`

---

### Phase 2.5: Helper Method Tests (1 hour) ⭐ NEW MANDATORY

**Purpose:** Test business logic edge cases

- [ ] **2.5.1** Write test_extract_contexts_with_bool() (legacy format)
- [ ] **2.5.2** Write test_extract_contexts_with_string() (single string)
- [ ] **2.5.3** Write test_extract_contexts_with_list() (list format)
- [ ] **2.5.4** Write test_extract_contexts_with_none() (None handling)
- [ ] **2.5.5** Write test_extract_contexts_with_empty_list() ([] handling)
- [ ] **2.5.6** Write test_extract_contexts_mixed_types() ([str, None, str])
- [ ] **2.5.7** Write test_format_sources_with_confidence() (emoji logic)
- [ ] **2.5.8** Write test_format_abbreviations() (both detailed and simple)
- [ ] **2.5.9** Write test_build_fallback_context_section() (error path)
- [ ] **2.5.10** Write test_configuration_toggles() (adaptive_formatting, etc.)
- [ ] **2.5.11** Run all helper tests: `pytest tests/.../test_context_instruction_module.py -v`
- [ ] **2.5.12** Verify 100% pass rate
- [ ] **2.5.13** Git commit: `test(DEF-155): Phase 2.5 - Add helper method tests`

**Acceptance:**
- ✓ All edge cases covered
- ✓ Legacy formats tested
- ✓ Error paths tested
- ✓ All tests pass

---

### Phase 3: Complete execute() (30 min)

- [ ] **3.1** Implement orchestration logic (see plan lines 518-569)
- [ ] **3.2** Step 1: Calculate score
- [ ] **3.3** Step 2: Extract and share context data
- [ ] **3.4** Step 3a: Generate context instructions
- [ ] **3.5** Step 3b: Generate forbidden patterns
- [ ] **3.6** Step 3c: Generate metadata (if enabled)
- [ ] **3.7** Step 4: Combine sections with proper formatting
- [ ] **3.8** Add error handling (try/except)
- [ ] **3.9** Write test_complete_context_output()
- [ ] **3.10** Run: `pytest tests/.../test_context_instruction_module.py -v`
- [ ] **3.11** Verify all sections present in output
- [ ] **3.12** Verify shared_state populated correctly
- [ ] **3.13** Git commit: `feat(DEF-155): Phase 3 - Implement complete execute() orchestration`

---

### Phase 4: Update Orchestrator (30 min)

- [ ] **4.1** Open `src/services/prompts/modular_prompt_adapter.py`
- [ ] **4.2** Add import: `from .modules import ContextInstructionModule`
- [ ] **4.3** Find `get_cached_orchestrator()` function (line 42)
- [ ] **4.4** Add to modules list: `ContextInstructionModule()`
- [ ] **4.5** Remove: `ContextAwarenessModule()` (comment out for now)
- [ ] **4.6** Test: `python -c "from services.prompts.modular_prompt_adapter import get_cached_orchestrator; o = get_cached_orchestrator(); print(o.modules.keys())"`
- [ ] **4.7** Verify "context_instruction" in output
- [ ] **4.8** Write test_orchestrator_includes_context_instruction()
- [ ] **4.9** Run orchestrator tests: `pytest tests/.../test_prompt_orchestrator.py -v`
- [ ] **4.10** Git commit: `feat(DEF-155): Phase 4 - Register ContextInstructionModule in orchestrator`

---

### Phase 5: Refactor ErrorPreventionModule (45 min)

- [ ] **5.1** Open `src/services/prompts/modules/error_prevention_module.py`
- [ ] **5.2** Document CURRENT state: copy execute() method to comment
- [ ] **5.3** Remove lines 75-79 (context retrieval from shared_state)
- [ ] **5.4** Remove lines 95-100 (context forbidden section injection)
- [ ] **5.5** Remove method: `_build_context_forbidden()` (lines 193-245)
- [ ] **5.6** Remove constant: organization mappings (lines 209-219)
- [ ] **5.7** Update execute(): keep basic errors, forbidden starters, validation matrix
- [ ] **5.8** Add generic warning: "context en bronnen mogen niet letterlijk..."
- [ ] **5.9** Update get_dependencies(): return [] (not ["context_awareness"])
- [ ] **5.10** Write test_error_prevention_no_context_logic()
- [ ] **5.11** Run: `pytest tests/.../test_error_prevention_module.py -v`
- [ ] **5.12** Verify context logic removed, generic logic preserved
- [ ] **5.13** Git commit: `refactor(DEF-155): Phase 5 - Remove context logic from ErrorPreventionModule`

---

### Phase 6: Refactor DefinitionTaskModule (45 min)

- [ ] **6.1** Open `src/services/prompts/modules/definition_task_module.py`
- [ ] **6.2** Document CURRENT state: copy relevant methods to comment
- [ ] **6.3** Remove lines 84-104 (context detection from base_context)
- [ ] **6.4** Update execute(): remove has_context variable
- [ ] **6.5** Update `_build_quality_control()`: remove has_context parameter
- [ ] **6.6** Make quality control generic (remove context-aware adaptation)
- [ ] **6.7** Remove method: `_build_metadata()` (lines 225-246)
- [ ] **6.8** Remove method: `_build_prompt_metadata()` (lines 259-299)
- [ ] **6.9** Update `_build_checklist()`: remove line "Context verwerkt zonder..." (line 204)
- [ ] **6.10** Write test_definition_task_no_context_logic()
- [ ] **6.11** Run: `pytest tests/.../test_definition_task_module.py -v`
- [ ] **6.12** Verify context metadata removed, final instructions preserved
- [ ] **6.13** Git commit: `refactor(DEF-155): Phase 6 - Remove context metadata from DefinitionTaskModule`

---

### Phase 7: Delete ContextAwarenessModule (15 min)

- [ ] **7.1** Verify Phases 5-6 complete (other modules refactored)
- [ ] **7.2** Backup old module: `cp src/.../context_awareness_module.py src/.../context_awareness_module.py.bak`
- [ ] **7.3** Git rm: `git rm src/services/prompts/modules/context_awareness_module.py`
- [ ] **7.4** Update `src/services/prompts/modules/__init__.py`: remove ContextAwarenessModule export
- [ ] **7.5** Update imports in modular_prompt_adapter.py (line 18)
- [ ] **7.6** Search: `grep -r "ContextAwarenessModule" src/ --include="*.py"`
- [ ] **7.7** Verify zero results (except .bak file)
- [ ] **7.8** Test: `python -m py_compile src/services/prompts/modular_prompt_adapter.py`
- [ ] **7.9** Test: `python -c "from services.prompts.modules import *"`
- [ ] **7.10** Git commit: `refactor(DEF-155): Phase 7 - Delete ContextAwarenessModule`

---

### Phase 7.5: Verify Dependencies (30 min) ⭐ NEW MANDATORY

**Purpose:** Ensure no hidden references to old module

- [ ] **7.5.1** Search: `grep -r "ContextAwarenessModule" src/ tests/ --include="*.py"`
- [ ] **7.5.2** Document results (should be zero except docs/tests)
- [ ] **7.5.3** Search: `grep -r "context_awareness" src/ tests/ --include="*.py"`
- [ ] **7.5.4** Verify ErrorPreventionModule dependency is "context_instruction" (not "context_awareness")
- [ ] **7.5.5** Verify orchestrator registration list (should have ContextInstructionModule)
- [ ] **7.5.6** Search: `grep -r "get_shared.*organization_contexts" src/ --include="*.py"`
- [ ] **7.5.7** Verify only ErrorPreventionModule reads this key
- [ ] **7.5.8** Search: `grep -r "set_shared.*organization_contexts" src/ --include="*.py"`
- [ ] **7.5.9** Verify ONLY ContextInstructionModule writes this key
- [ ] **7.5.10** Write test_module_dependency_graph()
- [ ] **7.5.11** Write test_shared_state_single_writer()
- [ ] **7.5.12** Run tests: verify dependency graph correct
- [ ] **7.5.13** Git commit: `test(DEF-155): Phase 7.5 - Verify no hidden dependencies on old module`

**Acceptance:**
- ✓ Zero old module references (except docs/history)
- ✓ All dependencies updated
- ✓ Single-writer rule enforced

---

### Phase 8: Unit Testing (1.5 hours)

**Purpose:** Comprehensive unit test coverage

#### Core Functionality Tests

- [ ] **8.1** Write test_initialization()
- [ ] **8.2** Write test_no_dependencies()
- [ ] **8.3** Write test_validate_input_always_true()
- [ ] **8.4** Write test_context_richness_score_calculation()
- [ ] **8.5** Write test_context_data_shared()

#### Formatting Tests

- [ ] **8.6** Write test_rich_context_formatting() (score >= 0.8)
- [ ] **8.7** Write test_moderate_context_formatting() (0.5 <= score < 0.8)
- [ ] **8.8** Write test_minimal_context_formatting() (score < 0.5)

#### Edge Case Tests ⭐ CRITICAL

- [ ] **8.9** Write test_no_context_scenario() (empty context)
- [ ] **8.10** Write test_error_handling() (invalid enriched_context)
- [ ] **8.11** Write test_shared_state_keys_exact() (no typos!)
- [ ] **8.12** Write test_context_extraction_edge_cases() (bool/str/list/None)

#### Integration Tests

- [ ] **8.13** Write test_error_prevention_no_longer_depends()
- [ ] **8.14** Write test_definition_task_no_context_logic()
- [ ] **8.15** Write test_execution_order_correct()

#### Real Data Tests ⭐ CRITICAL

- [ ] **8.16** Extract 20 real context samples: `python scripts/extract_real_contexts.py`
- [ ] **8.17** Write test_with_real_production_samples()
- [ ] **8.18** Test all 20 samples: verify no crashes

#### Run All Tests

- [ ] **8.19** Run: `pytest tests/.../test_context_instruction_module.py -v`
- [ ] **8.20** Verify 100% pass rate
- [ ] **8.21** Run: `pytest tests/.../test_error_prevention_module.py -v`
- [ ] **8.22** Run: `pytest tests/.../test_definition_task_module.py -v`
- [ ] **8.23** Check coverage: `pytest tests/.../test_context_instruction_module.py --cov=src/.../context_instruction_module --cov-report=term-missing`
- [ ] **8.24** Verify coverage ≥80%
- [ ] **8.25** Git commit: `test(DEF-155): Phase 8 - Comprehensive unit test suite`

---

### Phase 9: Integration Testing (45 min)

- [ ] **9.1** Write test_orchestrator_with_context_instruction_module()
- [ ] **9.2** Verify module registered correctly
- [ ] **9.3** Verify execution order (context_instruction before error_prevention)
- [ ] **9.4** Write test_full_prompt_generation_with_context()
- [ ] **9.5** Generate full prompt with test context
- [ ] **9.6** Verify context appears ONCE (not 3 times)
- [ ] **9.7** Verify forbidden patterns section exists
- [ ] **9.8** Verify metadata section exists (if enabled)
- [ ] **9.9** Write test_prompt_structure_maintained()
- [ ] **9.10** Verify all required sections present
- [ ] **9.11** Run: `pytest tests/integration/test_prompt_module_pipeline.py -v`
- [ ] **9.12** Verify 100% pass rate
- [ ] **9.13** Git commit: `test(DEF-155): Phase 9 - Integration tests with full orchestrator`

---

### Phase 9.5: Baseline Comparison (1 hour) ⭐ MANDATORY BLOCKING

**Purpose:** Validate quality maintained vs baseline

- [ ] **9.5.1** Load baseline from Phase 0: `tests/fixtures/DEF-155-baseline/`
- [ ] **9.5.2** Create comparison script: `tests/debug/compare_to_baseline.py`
- [ ] **9.5.3** Generate prompts with NEW system (same 20 test cases)
- [ ] **9.5.4** Count tokens: new vs baseline
- [ ] **9.5.5** Calculate token reduction: `(baseline - new) / baseline * 100`
- [ ] **9.5.6** Generate definitions with NEW system (same 20 test cases)
- [ ] **9.5.7** Run validation on new definitions
- [ ] **9.5.8** Compare scores: `new_score / baseline_score`
- [ ] **9.5.9** Calculate average quality ratio
- [ ] **9.5.10** Check blocking condition: **quality ratio >= 0.95** ⭐
- [ ] **9.5.11** If quality < 0.95: STOP, investigate, fix, re-test
- [ ] **9.5.12** If quality >= 0.95: Manually review 5 definitions
- [ ] **9.5.13** Verify definitions are context-specific (not generic)
- [ ] **9.5.14** Document results in `docs/analyses/DEF-155-BASELINE-COMPARISON-RESULTS.md`
- [ ] **9.5.15** Git commit: `test(DEF-155): Phase 9.5 - Baseline comparison (quality maintained)`

**BLOCKING CONDITION:**
- ⛔ If quality < 95% of baseline: **DO NOT PROCEED**
- ✅ If quality >= 95% of baseline: **PROCEED to Phase 10**

**Acceptance:**
- ✓ Token reduction ≥50% (info only)
- ✓ **Quality ≥95% of baseline (BLOCKING)**
- ✓ No new critical failures
- ✓ Manual review confirms quality

---

### Phase 10: Documentation (30 min)

- [ ] **10.1** Create `docs/technisch/context_instruction_module.md`
- [ ] **10.2** Document module responsibilities
- [ ] **10.3** Document data flow
- [ ] **10.4** Document configuration options
- [ ] **10.5** Document token optimization strategy
- [ ] **10.6** Document migration from old modules
- [ ] **10.7** Update `CLAUDE.md`: add ContextInstructionModule reference
- [ ] **10.8** Update `CLAUDE.md`: remove ContextAwarenessModule references
- [ ] **10.9** Update `docs/architectuur/PROMPT_SYSTEM_ARCHITECTURE.md`
- [ ] **10.10** Update module diagram
- [ ] **10.11** Add entry to `docs/refactor-log.md`
- [ ] **10.12** Document lessons learned
- [ ] **10.13** Git commit: `docs(DEF-155): Phase 10 - Update documentation for context consolidation`

---

## 🎯 Post-Implementation Checklist

**Before merging to main:**

### Test Verification
- [ ] All unit tests pass: `pytest tests/services/prompts/modules/ -v`
- [ ] All integration tests pass: `pytest tests/integration/ -v`
- [ ] Smoke tests pass: `pytest tests/smoke/ -v`
- [ ] Coverage ≥80%: `pytest tests/.../test_context_instruction_module.py --cov --cov-report=term`

### Quality Verification ⭐ BLOCKING
- [ ] Baseline comparison complete (Phase 9.5)
- [ ] **Quality ratio ≥0.95** (MANDATORY)
- [ ] Token reduction ≥50% (info only)
- [ ] No new critical validation failures

### Manual Testing
- [ ] App starts without errors: `bash scripts/run_app.sh`
- [ ] Generate definition with org context (e.g., NP)
- [ ] Navigate to Edit tab
- [ ] View generated prompt
- [ ] Verify single context section (not 3 duplicate sections)
- [ ] Verify forbidden patterns section exists
- [ ] Verify "NP" and "Nederlands Politie" mentioned

### Code Review
- [ ] Self-review: line-by-line comparison vs old code
- [ ] All business logic migrated from ContextAwarenessModule
- [ ] All helper methods tested
- [ ] Error paths covered
- [ ] No hardcoded values (use constants)

### Documentation
- [ ] CLAUDE.md updated
- [ ] Architecture docs updated
- [ ] Refactor log updated
- [ ] Technical docs created

**If all checked:** ✅ **READY TO MERGE**

**If any unchecked:** ⛔ **STOP** - complete missing items

---

## 🚨 Emergency Procedures

### If Tests Fail During Implementation

**Step 1: Identify phase**
- Which phase were you in? (1-10)
- What was the last successful commit?

**Step 2: Isolate failure**
```bash
# Run specific test
pytest tests/.../test_file.py::test_function -v

# Check for import errors
python -m py_compile src/.../module.py

# Check for syntax errors
python -c "import module"
```

**Step 3: Rollback to last good commit**
```bash
# See recent commits
git log --oneline -10

# Reset to last good commit
git reset --hard <commit-hash>

# Verify tests pass
pytest tests/ -v
```

**Step 4: Re-attempt phase**
- Review phase checklist
- Follow steps carefully
- Test after each sub-step

---

### If Baseline Comparison Fails (Phase 9.5)

**Symptoms:**
- Quality ratio < 0.95
- Critical validation failures
- Definitions are generic (not context-specific)

**Investigation:**
```bash
# Compare prompts manually
diff tests/fixtures/DEF-155-baseline/prompts/case001.txt \
     tests/fixtures/DEF-155-baseline/prompts-new/case001.txt

# Check for missing context
grep "CONTEXT" tests/fixtures/DEF-155-baseline/prompts-new/*.txt

# Check shared_state
pytest tests/.../test_context_instruction_module.py::test_context_data_shared -v -s
```

**Fixes:**
1. **Context not appearing:**
   - Check `_share_traditional_context()` method
   - Verify shared_state keys correct
   - Add debug logging

2. **Quality lower:**
   - Compare prompt structure old vs new
   - Check for missing instructions
   - Verify all helpers migrated

3. **If cannot fix in 2 hours:**
   - **ABORT** implementation
   - Rollback to main branch
   - Document findings in issue

---

### If Production Breaks After Merge

**Symptoms:**
- App crashes on startup
- Definitions are low quality
- Users report issues

**Immediate actions:**
```bash
# 1. Rollback code
git revert <merge-commit-hash>

# 2. Verify rollback worked
pytest tests/ -v
bash scripts/run_app.sh

# 3. Notify user
# "Rolled back DEF-155 due to issue X. Investigating."

# 4. Investigate offline
git checkout feature/DEF-155-context-consolidation
# ... debug ...
```

**Don't panic:**
- Git preserves all history
- Database is unaffected (no schema changes)
- Rollback is straightforward
- Learn from the issue

---

## 📊 Progress Tracking

**Use this table to track progress:**

| Phase | Status | Time | Issues | Notes |
|-------|--------|------|--------|-------|
| 0 | ☐ | ___ min | | Baseline capture |
| 1 | ☐ | ___ min | | Skeleton |
| 2.1 | ☐ | ___ min | | Richness scoring |
| 2.2 | ☐ | ___ min | | Adaptive formatting |
| 2.3 | ☐ | ___ min | | Forbidden patterns |
| 2.4 | ☐ | ___ min | | Metadata |
| 2.5 | ☐ | ___ min | | Helper tests |
| 3 | ☐ | ___ min | | Execute() |
| 4 | ☐ | ___ min | | Orchestrator |
| 5 | ☐ | ___ min | | ErrorPrevention |
| 6 | ☐ | ___ min | | DefinitionTask |
| 7 | ☐ | ___ min | | Delete old |
| 7.5 | ☐ | ___ min | | Verify deps |
| 8 | ☐ | ___ min | | Unit tests |
| 9 | ☐ | ___ min | | Integration |
| 9.5 | ☐ | ___ min | | Baseline compare |
| 10 | ☐ | ___ min | | Documentation |

**Total time:** ____ min / 690 min (11.5 hours)

**Update this table as you complete each phase.**

---

## ✅ Success Confirmation

**After completing all phases, verify:**

- [ ] All phases marked complete (✓)
- [ ] Total time within 11.5 hours (or note why longer)
- [ ] All tests passing
- [ ] **Quality ≥95% of baseline** (MOST IMPORTANT)
- [ ] Token reduction achieved
- [ ] UI working correctly
- [ ] Documentation updated
- [ ] Git history clean (meaningful commits)
- [ ] Ready to merge to main

**If all verified:** 🎉 **SUCCESS - Merge to main**

---

**Document Status:** ✅ READY TO USE
**Last Updated:** 2025-11-13
**Use:** Follow step-by-step during implementation
**Priority:** 🔴 CRITICAL - Do not skip any mandatory phases
