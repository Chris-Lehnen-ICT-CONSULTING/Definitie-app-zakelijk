# DEF-155 Context Consolidation - Risk Assessment & FMEA

## Executive Summary

**Assessment Date:** 2025-11-13
**Refactoring Scope:** Consolidate 3 modules into 1 (ContextInstructionModule)
**Code Changes:** ~150 lines across 4 files (1 new, 1 deleted, 2 refactored)
**Overall Risk Level:** 🟡 **MEDIUM-HIGH** (proceed with extreme caution)

**Critical Finding:** The "no backwards compatibility" policy is **APPROPRIATE** for this single-user dev app, but the migration has **HIDDEN LANDMINES** that the implementation plan underestimates.

---

## 1. FAILURE MODE & EFFECTS ANALYSIS (FMEA)

### Risk Scoring Matrix

| Likelihood | Impact | Severity Score | Action Required |
|------------|--------|----------------|-----------------|
| 1-3 (Low) | 1-3 (Low) | 1-9 | Monitor |
| 1-3 (Low) | 4-7 (Medium) | 4-21 | Mitigate |
| 1-3 (Low) | 8-10 (High) | 8-30 | Prevent |
| 4-7 (Medium) | 4-7 (Medium) | 16-49 | **HIGH PRIORITY** |
| 4-7 (Medium) | 8-10 (High) | 32-70 | **CRITICAL** |
| 8-10 (High) | 8-10 (High) | 64-100 | **BLOCKER** |

---

### FMEA Table

| # | Failure Mode | Likelihood (1-10) | Impact (1-10) | Severity | Root Cause | Detection Method | Mitigation |
|---|--------------|-------------------|---------------|----------|------------|------------------|------------|
| **1** | **Silent context loss in prompts** | 7 | 10 | 🔴 **70 CRITICAL** | Inconsistent data access (base_context vs shared_state) | Integration tests fail to detect empty context sections | Add explicit context presence assertions, test with real data |
| **2** | **Module execution order breaks** | 5 | 9 | 🟡 **45 HIGH** | Priority 75 too high, conflicts with existing priorities | Unit tests don't catch orchestrator ordering | Document current execution order, test batch resolution |
| **3** | **Circular reasoning in quality degradation** | 8 | 8 | 🔴 **64 CRITICAL** | Validating new prompts with NEW validators (not baseline) | No baseline comparison tests | **MUST** capture baseline prompts + validation scores BEFORE any changes |
| **4** | **Test false positives masking real issues** | 6 | 8 | 🟡 **48 HIGH** | Mock data doesn't reflect production patterns | Passing tests but real definitions fail | Use real historical context data in tests |
| **5** | **Token reduction not achieved** | 4 | 6 | 🟡 **24 MEDIUM** | Optimistic estimates, hidden duplication | Token counting test uses wrong baseline | Measure tokens in CURRENT system first |
| **6** | **Incomplete business logic migration** | 6 | 9 | 🟡 **54 HIGH** | 433 lines of ContextAwarenessModule, easy to miss edge cases | Code review misses subtle logic | Line-by-line migration checklist with sign-off |
| **7** | **Shared state pollution** | 5 | 7 | 🟡 **35 HIGH** | Multiple modules writing to shared_state, no locking | Intermittent failures, race conditions | Document shared_state contract, single-writer rule |
| **8** | **Error handling creates infinite loops** | 3 | 10 | 🟡 **30 HIGH** | Fallback logic depends on modules that failed | Timeout during execution, stack overflow | Test error scenarios explicitly |
| **9** | **UI doesn't reflect prompt changes** | 7 | 6 | 🟡 **42 HIGH** | No UI smoke tests, only backend tests | Users see old-style prompts | Add UI integration test for Edit tab prompt display |
| **10** | **Rollback impossible due to data migration** | 4 | 9 | 🟡 **36 HIGH** | Database schema changes, no migration scripts | Cannot revert to old code | **VERIFY:** No schema changes planned (plan says no DB changes) |

---

## 2. CRITICAL RISK DEEP DIVE

### 🔴 RISK #1: Silent Context Loss (Severity: 70 - CRITICAL)

**Problem:** DefinitionTaskModule reads base_context DIRECTLY (lines 84-98), while ErrorPreventionModule reads shared_state. New module consolidates to shared_state only.

**What can go wrong:**
```python
# OLD: DefinitionTaskModule (lines 86-98)
base_ctx = context.enriched_context.base_context  # DIRECT ACCESS
jur_contexts = base_ctx.get("juridische_context") or base_ctx.get("juridisch") or []
wet_basis = base_ctx.get("wettelijke_basis") or base_ctx.get("wettelijk") or []

# NEW: ContextInstructionModule (proposed)
jur_contexts = context.get_shared("juridical_contexts", [])  # shared_state only
wet_contexts = context.get_shared("legal_basis_contexts", [])
```

**Failure scenario:**
1. EnrichedContext has `base_context = {"juridische_context": ["Strafrecht"]}`
2. ContextInstructionModule extracts "juridisch" (line 383 in old module)
3. But there's a typo/mismatch in key names ("juridische_context" vs "juridisch")
4. shared_state gets empty list
5. Prompt generation succeeds (no error)
6. Generated definition lacks context guidance
7. User doesn't notice until quality regression shows up days later

**Why implementation plan misses this:**
- Plan assumes `_share_traditional_context()` logic (lines 368-395) will be preserved
- But doesn't test the EXACT key mapping between base_context → shared_state
- Test creates mock data with consistent keys, doesn't catch production variance

**MITIGATION REQUIRED:**
1. Extract real base_context samples from production database
2. Create regression test with ACTUAL historical context data
3. Add assertion: `len(shared_state["juridical_contexts"]) == len(base_context.get("juridisch"))`
4. Add monitoring: Log warning if context extraction produces empty lists when base_context is non-empty

---

### 🔴 RISK #3: Circular Reasoning in Quality Validation (Severity: 64 - CRITICAL)

**Problem:** Implementation plan says "test definition quality maintained" (Phase 9), but HOW?

**Circular reasoning trap:**
```python
# Step 1: Implement new ContextInstructionModule
# Step 2: Generate definitions with new system
# Step 3: Validate with SAME validators
# Step 4: Quality score = 0.8 (good!)
#
# BUT: If the validator uses the SAME context logic you just changed,
#      it will be consistent with itself but WRONG compared to old system!
```

**Concrete example:**
- OLD: Context appears 3 times in prompt (redundant but comprehensive)
- NEW: Context appears 1 time (consolidated)
- Validator: "Context present? ✓ Yes"
- Result: Test passes, but definitions are WORSE (less context guidance)

**Why this is CRITICAL:**
- Implementation plan has NO baseline capture step
- All tests compare new system to... new system
- Quality degradation goes undetected
- Users discover issue after 100+ definitions generated

**MITIGATION REQUIRED (BLOCKING):**
```bash
# STEP 0: BEFORE ANY CODE CHANGES
pytest tests/services/test_definition_generator.py --baseline-capture
# Captures: prompts, definitions, validation scores for 20 test cases

# STEP 10: AFTER IMPLEMENTATION
pytest tests/services/test_definition_generator.py --baseline-compare
# Compares: new prompts vs baseline, new definitions vs baseline
# Fails if: validation score drops >5%, prompt structure changes unexpectedly
```

**Implementation gap:** Plan has no "Step 0" or baseline capture phase!

---

### 🟡 RISK #2: Module Execution Order Breaks (Severity: 45 - HIGH)

**Problem:** New ContextInstructionModule priority = 75 (high), but existing modules have:

```python
# Current priorities (from modular_prompt_adapter.py lines 60-78)
ExpertiseModule()                  # Priority: ? (need to check)
OutputSpecificationModule()        # Priority: ?
GrammarModule()                    # Priority: ?
ContextAwarenessModule()           # Priority: 70 ← OLD
SemanticCategorisationModule()     # Priority: ?
TemplateModule()                   # Priority: ?
ErrorPreventionModule()            # Depends on: ["context_awareness"]
```

**Failure scenario:**
1. Set ContextInstructionModule priority = 75
2. But ExpertiseModule priority = 80 (hypothetical)
3. Expertise runs first, expects shared_state data
4. shared_state is empty
5. Expertise module behaves differently
6. Prompt is malformed
7. GPT-4 generates nonsense

**Why implementation plan misses this:**
- Plan says "no dependencies" (Phase 1, line 375) ← CORRECT for ContextInstruction
- But doesn't document REVERSE dependencies (who depends on IT)
- ErrorPreventionModule depends on "context_awareness" → needs UPDATE to "context_instruction"
- Plan mentions updating ErrorPreventionModule dependencies (Phase 5, line 699) ← GOOD
- But doesn't verify no OTHER modules depend on context_awareness

**MITIGATION:**
```bash
# Search for hidden dependencies
grep -r "context_awareness" src/services/prompts/ --include="*.py"
# Found: error_prevention_module.py line 141 ← Known, covered in plan
# Found: modular_prompt_adapter.py line 18 ← Import statement (need to update)
# Found: 84 other files (mostly docs) ← Need to verify no code dependencies
```

**ACTION REQUIRED:**
1. Document CURRENT execution order (batch 1, batch 2, etc.)
2. Document EXPECTED execution order after change
3. Test that ErrorPreventionModule runs AFTER ContextInstructionModule
4. Update import in modular_prompt_adapter.py line 18

---

### 🟡 RISK #4: Test False Positives (Severity: 48 - HIGH)

**Problem:** Proposed test suite uses mocked/synthetic data:

```python
# From implementation plan (lines 906-950)
def create_test_context(
    begrip="vergunning",
    org=None,
    jur=None,
    wet=None,
):
    """Helper to create test context."""
    base_context = {}
    if org:
        base_context["organisatorisch"] = org  # ← CLEAN mock data
```

**Why this is dangerous:**
1. Real production data has inconsistencies:
   - Sometimes "organisatorisch", sometimes "organisatie"
   - Sometimes list of strings, sometimes single string
   - Sometimes empty list `[]`, sometimes `None`, sometimes `False` (legacy)
2. Mocked data has NONE of these edge cases
3. Tests pass with mocked data
4. Production fails with real data

**Evidence from code:**
```python
# context_awareness_module.py lines 396-423
def _extract_contexts(self, context_value: Any) -> list[str]:
    """Extract context lijst uit verschillende input formaten."""
    if not context_value:
        return []

    if isinstance(context_value, bool):  # ← Legacy support!
        return []  # True means no specific context
    if isinstance(context_value, str):   # ← Single string
        return [context_value]
    if isinstance(context_value, list):  # ← List of items
        return [str(item) for item in context_value if item]
```

**This logic must be preserved**, but tests don't verify it!

**MITIGATION:**
```python
# Add to test suite
def test_context_extraction_edge_cases():
    """Test real-world context data formats."""
    module = ContextInstructionModule()

    # Test case 1: Legacy boolean (from old system)
    ctx1 = create_test_context_raw({"organisatorisch": True})
    out1 = module.execute(ctx1)
    assert ctx1.get_shared("organization_contexts") == []  # Not crash!

    # Test case 2: Single string (not list)
    ctx2 = create_test_context_raw({"organisatorisch": "NP"})
    out2 = module.execute(ctx2)
    assert ctx2.get_shared("organization_contexts") == ["NP"]

    # Test case 3: None vs empty list
    ctx3 = create_test_context_raw({"organisatorisch": None})
    out3 = module.execute(ctx3)
    assert ctx3.get_shared("organization_contexts") == []

    # Test case 4: Mixed types in list
    ctx4 = create_test_context_raw({"organisatorisch": ["NP", None, "", "OM"]})
    out4 = module.execute(ctx4)
    assert ctx4.get_shared("organization_contexts") == ["NP", "OM"]  # Filtered!
```

**ACTION:** Extract 20 real base_context samples from database, add to test fixtures.

---

### 🟡 RISK #6: Incomplete Business Logic Migration (Severity: 54 - HIGH)

**Problem:** ContextAwarenessModule is 433 lines. Implementation plan says "migrate business logic" but doesn't detail EVERY method.

**Evidence of complexity:**
```python
# context_awareness_module.py methods (not all in plan!)
- __init__()                          ✓ Covered in plan
- initialize()                        ✓ Covered
- validate_input()                    ✓ Covered
- execute()                           ✓ Covered
- get_dependencies()                  ✓ Covered
- _calculate_context_score()          ✓ Covered (Phase 2.1)
- _build_rich_context_section()       ✓ Covered (Phase 2.2)
- _build_moderate_context_section()   ✓ Covered (Phase 2.2)
- _build_minimal_context_section()    ✓ Covered (Phase 2.2)
- _format_detailed_base_context()     ⚠️  Helper method - mentioned but no test
- _format_sources_with_confidence()   ⚠️  Helper method - mentioned but no test
- _format_abbreviations_detailed()    ⚠️  Helper method - no explicit test
- _format_abbreviations_simple()      ⚠️  Helper method - no explicit test
- _share_traditional_context()        ✓ Covered (Phase 2)
- _extract_contexts()                 ⚠️  CRITICAL HELPER - no explicit test plan!
- _build_fallback_context_section()   ⚠️  Error handling - no test coverage!
```

**Missing from plan:**
1. Test for `_extract_contexts()` (handles bool/str/list) ← CRITICAL for backwards compat
2. Test for `_format_sources_with_confidence()` (emoji logic)
3. Test for `_build_fallback_context_section()` (error paths)
4. Test for confidence indicators toggle (`self.confidence_indicators`)
5. Test for abbreviations toggle (`self.include_abbreviations`)

**MITIGATION:**
Add Phase 2.5: "Migrate and test helper methods" (1 hour)
- Test each format helper with real data
- Test toggles (adaptive_formatting, confidence_indicators, include_abbreviations)
- Test fallback/error paths

---

### 🟡 RISK #7: Shared State Pollution (Severity: 35 - HIGH)

**Problem:** Multiple modules can write to shared_state, no locking mechanism.

**Scenario:**
```python
# ContextInstructionModule (Priority 75)
context.set_shared("context_richness_score", 0.65)
context.set_shared("organization_contexts", ["NP"])

# Hypothetical: Another module (Priority 76) runs first
# (if priorities are wrong)
context.set_shared("organization_contexts", ["ERROR"])

# ErrorPreventionModule reads shared_state
org_contexts = context.get_shared("organization_contexts")  # Gets ["ERROR"]!
```

**Why this matters:**
- PromptOrchestrator resolves execution order by priority + dependencies
- If priorities are wrong (see Risk #2), execution order breaks
- shared_state becomes corrupted
- Symptoms appear in LATER modules (hard to debug)

**Current safeguard:**
- Dependencies force ordering: ErrorPreventionModule depends on ["context_awareness"]
- This ensures context_awareness runs first
- **BUT:** After refactor, dependency changes to ["context_instruction"]?
  - Plan says yes (Phase 5, line 699)
  - But doesn't verify no OTHER modules write to same keys

**MITIGATION:**
1. Audit all modules: who writes to organization_contexts, juridical_contexts, legal_basis_contexts?
2. Enforce single-writer rule: ONLY ContextInstructionModule writes these keys
3. Add debug logging: `logger.debug(f"Setting shared_state: {key}={value}")`
4. Add assertion in ErrorPreventionModule: verify shared_state is populated before use

---

### 🟡 RISK #9: UI Doesn't Reflect Prompt Changes (Severity: 42 - HIGH)

**Problem:** All tests are backend-only. No UI integration tests.

**Failure scenario:**
1. Backend prompt generation works perfectly
2. User opens Edit tab → clicks "View Generated Prompt"
3. Sees old-style prompt (cached? stale state?)
4. User reports: "consolidation didn't work"
5. Developer confused: tests pass!

**Root cause possibilities:**
- Streamlit session state caching old prompts
- UI component not refreshed after prompt generation
- Edit tab displays cached prompt metadata (see DEF-151 recent fix)

**Evidence from git history:**
```
266dab91 fix(DEF-151): enable generation prompt viewing in edit tab
9bf74c88 fix(DEF-151): add missing generation metadata to prompt storage
```

Recent fixes to prompt display in Edit tab! This area is fragile.

**MITIGATION:**
```python
# Add UI smoke test (manual checklist)
def test_ui_displays_new_prompt_format():
    """
    Manual test checklist for UI verification:
    1. Generate definition with context (org=["NP"], jur=["Strafrecht"])
    2. Navigate to Edit tab
    3. Select generated definition
    4. Click "View Generated Prompt"
    5. Verify prompt contains:
       - ✓ Single "📌 VERPLICHTE CONTEXT" section (not 3 sections)
       - ✓ "🚨 CONTEXT-SPECIFIEKE VERBODEN" section
       - ✓ "NP" and "Nederlands Politie" mentioned
       - ✓ No duplicate context listings
    6. Compare token count vs baseline
    """
    pass
```

**ACTION:** Add manual UI test checklist to Phase 9 (Integration testing).

---

## 3. EVALUATION OF "NO BACKWARDS COMPATIBILITY" POLICY

### Is This Approach Appropriate? ✅ **YES, BUT...**

**Justification for "no rollback":**
1. Single-user application ✓
2. Not in production ✓
3. Developer has full control ✓
4. Can test thoroughly before merging ✓
5. Git provides version control ✓

**Per CLAUDE.md:**
> ⚠️ GEEN BACKWARDS COMPATIBILITY CODE
> Dit is een single-user applicatie, NIET in productie
> REFACTOR code met behoud van businesskennis en logica

**This policy is CORRECT** for this scenario.

**HOWEVER, major risks remain:**

### Risk: "Refactor met behoud van businesskennis"

**Problem:** 433 lines of ContextAwarenessModule contain subtle business logic:
- Confidence scoring algorithm (lines 143-184)
- Legacy format support (bool/str/list in `_extract_contexts`)
- Emoji indicator thresholds (0.5, 0.8)
- Organization code mappings (NP → Nederlands Politie)

**If ANY of this is lost:**
- Tests might pass (if tests don't cover edge cases)
- Quality degrades silently
- User discovers issue later (possibly weeks/months)
- Rollback is painful (definitions generated in between)

**Policy compliance:**
✅ "No backwards compatibility" ← Applied correctly
⚠️ "Met behoud van businesskennis" ← **THIS is the risk**

**Recommendation:** Implementation plan needs **explicit business logic preservation checklist**.

---

### Should We Keep ContextAwarenessModule as Fallback? ❌ **NO**

**Arguments AGAINST keeping old module:**
1. Code duplication (433 lines duplicated)
2. Maintenance nightmare (which version is truth?)
3. Risk of accidentally calling old module
4. Goes against "no backwards compatibility" policy

**Arguments FOR keeping old module:**
1. Safety net if new module fails
2. Can compare outputs side-by-side
3. Easy rollback (just swap registrations)

**Verdict: Don't keep old module, BUT:**
- ✅ Keep old file as `.bak` during development
- ✅ Git preserves history (can revert)
- ✅ Feature branch allows testing before merge
- ❌ Don't keep in production codebase

**Implementation:**
```bash
# During Phase 7 (Delete ContextAwarenessModule)
git mv src/services/prompts/modules/context_awareness_module.py \
       src/services/prompts/modules/context_awareness_module.py.bak

# Test everything
pytest tests/ -v

# If all good, delete .bak file
git rm src/services/prompts/modules/context_awareness_module.py.bak

# If problems, restore
git mv src/services/prompts/modules/context_awareness_module.py.bak \
       src/services/prompts/modules/context_awareness_module.py
```

---

## 4. TEST COVERAGE GAPS ANALYSIS

### Current Test Plan (from implementation doc lines 906-1246)

**Unit tests planned:** ✓ Good coverage
- Initialization
- No dependencies
- Validate input always true
- Context richness scoring
- Context data sharing
- Rich/moderate/minimal formatting
- Context forbidden patterns
- Organization mapping
- Context metadata
- No context scenario
- Error handling

**Integration tests planned:** ✓ Basic coverage
- Orchestrator includes new module
- Full prompt generation with context
- Token reduction verification

**Validation tests planned:** ⚠️ **WEAK**
- Definition quality maintained (how?)
- Compare quality scores (to what baseline?)

### MISSING Test Scenarios

#### 1. Edge Case Tests (CRITICAL)
```python
# NOT in plan!
def test_context_with_legacy_formats():
    """Test backwards compatibility with old context formats."""
    # Boolean context (legacy)
    # Single string vs list
    # None vs empty list
    # Mixed types in list
```

#### 2. Error Path Tests (HIGH)
```python
# NOT in plan!
def test_context_instruction_with_invalid_enriched_context():
    """Test error handling when enriched_context is malformed."""
    # None enriched_context
    # Missing base_context
    # Invalid base_context structure
```

#### 3. Configuration Toggle Tests (MEDIUM)
```python
# NOT in plan!
def test_adaptive_formatting_toggle():
    """Test adaptive_formatting can be disabled."""
    module = ContextInstructionModule()
    module.initialize({"adaptive_formatting": False})
    # Should always use same format regardless of score
```

#### 4. Shared State Contract Tests (HIGH)
```python
# NOT in plan!
def test_shared_state_keys_match_expected():
    """Verify exact shared_state keys produced."""
    module = ContextInstructionModule()
    context = create_test_context(org=["NP"])
    module.execute(context)

    # Exact keys (no typos!)
    assert "context_richness_score" in context.shared_state
    assert "organization_contexts" in context.shared_state  # Not "organisational"!
    assert "juridical_contexts" in context.shared_state     # Not "juridische"!
    assert "legal_basis_contexts" in context.shared_state   # Not "wettelijke"!
```

#### 5. Module Dependency Graph Tests (HIGH)
```python
# NOT in plan!
def test_error_prevention_depends_on_context_instruction():
    """Verify dependency graph updated correctly."""
    from services.prompts.modules.error_prevention_module import ErrorPreventionModule

    module = ErrorPreventionModule()
    deps = module.get_dependencies()

    assert "context_instruction" in deps
    assert "context_awareness" not in deps  # Old module removed!
```

#### 6. Execution Order Tests (CRITICAL)
```python
# NOT in plan!
def test_orchestrator_execution_order_after_refactor():
    """Verify ContextInstructionModule runs before ErrorPreventionModule."""
    orchestrator = get_cached_orchestrator()

    # Get execution order
    batches = orchestrator.resolve_execution_order()

    # Find modules
    context_batch = None
    error_batch = None
    for i, batch in enumerate(batches):
        if "context_instruction" in batch:
            context_batch = i
        if "error_prevention" in batch:
            error_batch = i

    assert context_batch is not None
    assert error_batch is not None
    assert context_batch < error_batch  # Context MUST run first!
```

#### 7. Real Data Regression Tests (CRITICAL)
```python
# NOT in plan!
def test_with_real_production_context_samples():
    """Test with 20 real context samples from production database."""
    # Load real samples from data/test_fixtures/real_contexts.json
    # Samples extracted from production definitions
    # Includes all weird edge cases we've seen

    for sample in load_real_context_samples():
        module = ContextInstructionModule()
        context = create_context_from_sample(sample)

        output = module.execute(context)

        # Should not crash
        assert output.success is True

        # Should produce context output if context exists
        if sample.has_context:
            assert len(output.content) > 50  # Non-trivial output
```

**ACTION:** Add 30-40 additional tests to cover these gaps.

---

## 5. DATA CONSISTENCY RISKS

### Scenario: shared_state Out of Sync

**How it happens:**
1. ContextInstructionModule extracts contexts from base_context
2. Stores in shared_state: `{"organization_contexts": ["NP"]}`
3. Later module reads: `context.get_shared("organization_contexts")`
4. **BUT:** What if base_context is MUTATED after extraction?

**Code inspection:**
```python
# context_awareness_module.py lines 379-384
base_context = context.enriched_context.base_context

# Extract alle ACTIEVE contexten
org_contexts = self._extract_contexts(base_context.get("organisatorisch"))
# ↑ This reads base_context ONCE
# ↓ Stores in shared_state
context.set_shared("organization_contexts", org_contexts)
```

**Is base_context mutable?** Let's check:
```python
# definition_generator_context.py (not read yet)
class EnrichedContext:
    def __init__(self, base_context: dict, ...):
        self.base_context = base_context  # ← Reference or copy?
```

**RISK:** If base_context is mutable dict (not frozen), later modules could modify it.

**Likelihood:** LOW (no evidence of modules modifying base_context)
**Impact:** HIGH (would cause subtle bugs)
**Severity:** 🟡 **MEDIUM (3 × 8 = 24)**

**MITIGATION:**
1. Verify EnrichedContext freezes base_context (or uses dataclass with frozen=True)
2. Add assertion in tests: `base_context_before == base_context_after`
3. Document in code: "base_context is immutable, safe to cache extractions"

---

### Scenario: Module Execution Order Changes

**PromptOrchestrator uses topological sort** (lines 354-372 in modular_prompt_adapter.py).

**Current order:**
```
Batch 1 (no dependencies): ExpertiseModule, OutputSpec, Grammar, ContextAwareness, ...
Batch 2 (depends on batch 1): SemanticCategorisation?, Template?, ...
Batch N (depends on context): ErrorPrevention, DefinitionTask
```

**After refactor:**
```
Batch 1: ExpertiseModule, OutputSpec, Grammar, ContextInstruction, ...
          ↑ Changed from ContextAwareness to ContextInstruction
Batch N: ErrorPrevention (depends on context_instruction)
```

**What if priorities cause different ordering?**
- Example: If ContextInstruction priority = 75 but Grammar priority = 80
- Grammar might run first (depends on orchestrator's tiebreaker logic)
- If Grammar depends on shared_state data... boom!

**Likelihood:** MEDIUM (priorities are easy to get wrong)
**Impact:** HIGH (prompt generation fails)
**Severity:** 🟡 **MEDIUM-HIGH (5 × 9 = 45)**

**MITIGATION:**
1. Test execution order explicitly (see Test Coverage Gap #6)
2. Document priorities for all modules
3. Add assertion: verify no module with priority > 75 depends on context data

---

### Scenario: Race Conditions (if multi-threading)

**PromptOrchestrator has `max_workers=4`** (line 57 in modular_prompt_adapter.py).

**Does this mean parallel execution?** Need to check:
```python
# modular_prompt_adapter.py line 57
orchestrator = PromptOrchestrator(max_workers=4)
```

**If modules run in parallel:**
- Batch 1 modules could run simultaneously
- All writing to shared_state at same time
- **Potential data race!**

**Likelihood:** UNKNOWN (need to check PromptOrchestrator implementation)
**Impact:** HIGH (corrupted shared_state)
**Severity:** 🟡 **POTENTIALLY HIGH**

**ACTION REQUIRED:** Check if PromptOrchestrator actually uses threading/multiprocessing.

**If yes:**
- Add locking around shared_state writes
- Or serialize shared_state writes
- Or disable parallelism (max_workers=1)

**If no:** Risk is zero.

---

## 6. ROLLBACK STRATEGY (Even Though Policy Says "No Rollback")

### Why We Need a Rollback Plan Anyway

**Reasons:**
1. **Principle of least surprise:** Users expect to revert bad changes
2. **Risk management:** Even with perfect testing, production issues occur
3. **Compliance:** "No backwards compatibility" ≠ "No rollback"
4. **Safety net:** Developer confidence increases with safety net

### Level 1: Code Rollback (Easy)

**Scenario:** New code has bugs, old code worked fine.

**Steps:**
```bash
# 1. Revert git commits
git log --oneline  # Find commit hash before DEF-155
git revert <commit-hash>
# Or: git reset --hard <commit-hash> (if not pushed)

# 2. Re-run tests
pytest tests/ -v

# 3. Restart Streamlit app
bash scripts/run_app.sh

# Time: 5 minutes
# Success rate: 99%
```

**Caveats:**
- ✅ Code reverts cleanly
- ✅ No database changes (plan says no schema changes)
- ⚠️ Definitions generated with new system remain in database (see Level 2)

---

### Level 2: Data Rollback (Medium)

**Scenario:** Definitions generated with new system are lower quality, need to discard.

**Problem:** Plan says "no database changes", but definitions ARE database records!

**Steps:**
```bash
# 1. Identify definitions generated with new system
# Assumption: generation_metadata.prompt_version or timestamp
sqlite3 data/definities.db << EOF
SELECT id, begrip, created_at
FROM definities
WHERE created_at > '2025-11-13 12:00:00'  -- Time of deployment
  AND generation_metadata LIKE '%ContextInstructionModule%'
LIMIT 10;
EOF

# 2. Backup these definitions (don't delete yet!)
sqlite3 data/definities.db << EOF
CREATE TABLE IF NOT EXISTS definities_rollback_backup AS
SELECT * FROM definities
WHERE created_at > '2025-11-13 12:00:00';
EOF

# 3. Mark as "needs regeneration" (don't delete!)
sqlite3 data/definities.db << EOF
UPDATE definities
SET status = 'needs_regeneration',
    notes = 'DEF-155 rollback - generated with v2 context module'
WHERE created_at > '2025-11-13 12:00:00';
EOF

# 4. Regenerate with old system
# (Now that code is rolled back)
python scripts/regenerate_definitions.py --filter "needs_regeneration"

# Time: 30-60 minutes (depending on definition count)
# Success rate: 80%
```

**Caveats:**
- ⚠️ Requires definitions have created_at timestamp
- ⚠️ Requires generation_metadata to identify module version
- ⚠️ User might have edited definitions (lose edits!)
- ✅ No data loss (backup table preserves originals)

---

### Level 3: Emergency Abort (Hard)

**Scenario:** Production is completely broken, need to abort mid-migration.

**If caught during Phase 1-6 (before deletion):**
```bash
# 1. Git stash changes
git stash save "DEF-155 partial implementation - aborting"

# 2. Verify old code still works
pytest tests/services/prompts/test_context_awareness_module.py -v

# 3. Restart app
bash scripts/run_app.sh

# Time: 2 minutes
# Success rate: 95%
```

**If caught during/after Phase 7 (ContextAwarenessModule deleted):**
```bash
# 1. Restore from git history
git checkout HEAD~1 -- src/services/prompts/modules/context_awareness_module.py

# 2. Undo orchestrator registration changes
git checkout HEAD~1 -- src/services/prompts/modular_prompt_adapter.py

# 3. Run tests
pytest tests/ -v

# 4. If tests fail: keep reverting commits until tests pass
git log --oneline
git checkout <working-commit-hash> -- .

# Time: 10-30 minutes
# Success rate: 70% (depends on how many commits)
```

---

### Detection: How to Know We Need Rollback

**Automated detection:**
```python
# Add to CI/CD pipeline
def test_definition_quality_regression():
    """Smoke test: generate 10 definitions, check quality."""
    generator = get_definition_generator()
    validator = get_validator()

    test_terms = [
        ("vergunning", ["NP"], ["Strafrecht"]),
        ("registratie", ["DJI"], []),
        # ... 8 more
    ]

    scores = []
    for begrip, org, jur in test_terms:
        definition = generator.generate(begrip, org, jur)
        result = validator.validate(definition)
        scores.append(result.overall_score)

    avg_score = sum(scores) / len(scores)

    # Compare to baseline
    BASELINE_SCORE = 0.82  # From last known good version
    assert avg_score >= BASELINE_SCORE * 0.95, \
        f"Quality regression detected: {avg_score:.2f} < {BASELINE_SCORE * 0.95:.2f}"
```

**Manual detection signs:**
1. User reports: "Definitions are lower quality"
2. Definitions missing context-specific phrasing
3. Validation scores drop below 0.7
4. Increased validation failures
5. GPT-4 generates generic definitions (not context-specific)

**Response time target:** Detect within 24 hours, rollback within 2 hours.

---

## 7. MIGRATION SEQUENCING EVALUATION

### Is 10-Phase Order Optimal? ⚠️ **NO - MISSING PHASES**

**Current plan:**
1. Create skeleton (30 min)
2. Migrate business logic (2 hours)
3. Implement execute() (30 min)
4. Update orchestrator (30 min)
5. Refactor ErrorPreventionModule (45 min)
6. Refactor DefinitionTaskModule (45 min)
7. Delete ContextAwarenessModule (15 min)
8. Unit testing (1 hour)
9. Integration testing (45 min)
10. Documentation (30 min)

**MISSING PHASES:**

#### Phase 0: Baseline Capture (CRITICAL - ADD BEFORE PHASE 1)

**Duration:** 1 hour
**Why:** Without baseline, cannot validate quality maintained

**Steps:**
1. Select 20 representative test cases (diverse contexts)
2. Generate prompts with CURRENT system
3. Generate definitions with CURRENT system
4. Run validation on definitions
5. Capture: prompts (text files), definitions (JSON), scores (CSV)
6. Store in `tests/fixtures/DEF-155-baseline/`
7. Commit to git (so it's preserved)

**Acceptance criteria:**
- ✓ 20 prompt files saved
- ✓ 20 definition JSON files saved
- ✓ scores.csv with 20 rows
- ✓ Git commit: "test(DEF-155): baseline capture for migration validation"

---

#### Phase 2.5: Migrate and Test Helper Methods (ADD BETWEEN 2 & 3)

**Duration:** 1 hour
**Why:** Implementation plan mentions helpers but doesn't test them

**Steps:**
1. Migrate `_format_detailed_base_context()`
2. Test with real base_context samples
3. Migrate `_format_sources_with_confidence()`
4. Test with real ContextSource objects
5. Migrate `_format_abbreviations_detailed()` and `_format_abbreviations_simple()`
6. Test abbreviation handling
7. Migrate `_extract_contexts()` ← CRITICAL
8. Test with bool/str/list/None inputs
9. Migrate `_build_fallback_context_section()`
10. Test error path

**Acceptance criteria:**
- ✓ All helper methods migrated
- ✓ Each helper has dedicated unit test
- ✓ Edge cases covered (empty input, invalid input, None)
- ✓ Backwards compatibility verified (legacy formats)

---

#### Phase 7.5: Verify No Hidden Dependencies (ADD AFTER PHASE 7)

**Duration:** 30 min
**Why:** Ensure no other modules depend on ContextAwarenessModule

**Steps:**
```bash
# 1. Search codebase for references
grep -r "ContextAwarenessModule" src/ tests/ --include="*.py"
grep -r "context_awareness" src/ tests/ --include="*.py"

# 2. Check imports
grep -r "from.*context_awareness_module" src/ --include="*.py"

# 3. Verify orchestrator registration updated
grep -r "ContextAwarenessModule()" src/ --include="*.py"

# 4. Check shared_state keys
grep -r "get_shared.*context_richness_score" src/ --include="*.py"
```

**Expected results:**
- ✅ No imports of ContextAwarenessModule (except in deleted file)
- ✅ No instantiation of ContextAwarenessModule()
- ✅ ErrorPreventionModule updated to use context_instruction dependency
- ✅ All shared_state readers updated to new keys (if changed)

**Acceptance criteria:**
- ✓ Zero references to old module (except docs/history)
- ✓ All dependencies updated
- ✓ All imports updated

---

#### Phase 9.5: Baseline Comparison (ADD AFTER PHASE 9)

**Duration:** 1 hour
**Why:** Validate quality maintained vs baseline

**Steps:**
1. Load baseline test cases from Phase 0
2. Generate prompts with NEW system (same 20 test cases)
3. Generate definitions with NEW system
4. Run validation on new definitions
5. Compare:
   - Prompt token counts (expect 50-65% reduction)
   - Definition quality scores (expect ≥95% of baseline)
   - Validation pass rate (expect 100% if baseline passed)
6. Manual inspection: read 5 definitions, verify context-specific phrasing

**Acceptance criteria:**
- ✓ Token reduction ≥50% (380 → ≤190)
- ✓ Quality scores ≥95% of baseline
- ✓ No critical validation failures
- ✓ Manual review: definitions are context-specific

**If fails:** Investigate, fix, re-test. DO NOT merge.

---

### Revised Timeline

| Phase | Original Est. | Revised Est. | Total (Cumulative) |
|-------|---------------|--------------|-------------------|
| **0** (Baseline) | — | **1 hour** | 1 hour |
| **1** (Skeleton) | 30 min | 30 min | 1.5 hours |
| **2** (Business logic) | 2 hours | 2 hours | 3.5 hours |
| **2.5** (Helper tests) | — | **1 hour** | 4.5 hours |
| **3** (Execute) | 30 min | 30 min | 5 hours |
| **4** (Orchestrator) | 30 min | 30 min | 5.5 hours |
| **5** (ErrorPrevention) | 45 min | 45 min | 6.25 hours |
| **6** (DefinitionTask) | 45 min | 45 min | 7 hours |
| **7** (Delete) | 15 min | 15 min | 7.25 hours |
| **7.5** (Verify deps) | — | **30 min** | 7.75 hours |
| **8** (Unit tests) | 1 hour | **1.5 hours** | 9.25 hours |
| **9** (Integration) | 45 min | 45 min | 10 hours |
| **9.5** (Baseline compare) | — | **1 hour** | 11 hours |
| **10** (Documentation) | 30 min | 30 min | 11.5 hours |

**Original estimate:** 6 hours
**Revised estimate:** **11.5 hours** (+5.5 hours, +92%)

**Recommendation:** Budget 2 days (2x 6-hour sessions) instead of 1 day.

---

### Should We Do Incremental Releases? ⚠️ **NOT NECESSARY, BUT CONSIDER CHECKPOINTS**

**Arguments AGAINST incremental releases:**
1. Single-user dev app (no users to disrupt)
2. Feature branch allows full testing before merge
3. Incremental releases complicate rollback
4. Git commits provide checkpoints anyway

**Arguments FOR incremental releases:**
1. Earlier detection of issues
2. Can test parts of system in isolation
3. Smaller changes easier to debug

**Verdict: Use feature branch + git commits as checkpoints**

**Strategy:**
```bash
# Feature branch for full development
git checkout -b feature/DEF-155-context-consolidation

# Commit after EACH phase
git add -A
git commit -m "feat(DEF-155): Phase 1 - Create ContextInstructionModule skeleton"
# ... work ...
git commit -m "feat(DEF-155): Phase 2.1 - Migrate context richness scoring"
# ... etc ...

# When all phases done + tests pass
git checkout main
git merge feature/DEF-155-context-consolidation --squash
git commit -m "feat(DEF-155): consolidate context handling into single module"
```

**Checkpoints = commits, not releases.**

**If issue found:** `git reset --hard HEAD~3` to go back 3 commits.

---

### Feature Flags Despite "No Backwards Compatibility"? ❌ **NO**

**Arguments AGAINST feature flags:**
1. Policy explicitly says "no feature flags" (CLAUDE.md line 23)
2. Adds complexity (2 code paths to maintain)
3. Risk of "flag stays on forever" (tech debt)
4. Single-user app doesn't need gradual rollout

**Arguments FOR feature flags:**
1. Can toggle new module on/off for testing
2. Easy A/B comparison (old vs new prompts)
3. Safety net (flip flag if production breaks)

**Verdict: NO feature flags, stick to policy**

**Alternative: Use git branches for A/B testing**
```bash
# Test old system
git checkout main
bash scripts/run_app.sh
# Generate definition, note prompt

# Test new system
git checkout feature/DEF-155-context-consolidation
bash scripts/run_app.sh
# Generate same definition, compare prompts
```

**This achieves same goal without code complexity.**

---

## 8. RECOMMENDED SAFETY MEASURES

### Pre-Implementation Checklist (MANDATORY)

**Before writing any code:**

- [ ] **Baseline Capture**
  - [ ] Extract 20 real context samples from production database
  - [ ] Generate prompts with current system
  - [ ] Generate definitions with current system
  - [ ] Run validation, capture scores
  - [ ] Store in `tests/fixtures/DEF-155-baseline/`
  - [ ] Commit to git

- [ ] **Current System Documentation**
  - [ ] Document current module execution order
  - [ ] Document current priorities
  - [ ] Document shared_state keys (exact spellings!)
  - [ ] Document token counts (measure, don't estimate)

- [ ] **Dependency Audit**
  - [ ] List all modules that depend on context_awareness
  - [ ] List all modules that read shared_state keys
  - [ ] Verify no hidden dependencies

- [ ] **Test Fixture Preparation**
  - [ ] Extract real base_context samples (20+)
  - [ ] Extract real ContextSource objects (10+)
  - [ ] Extract real abbreviation examples (5+)
  - [ ] Store in `tests/fixtures/real_context_data/`

---

### During Implementation (MANDATORY)

**After each phase:**

- [ ] **Git Commit**
  - Commit message: `feat(DEF-155): Phase X - [description]`
  - Allows rollback to specific phase

- [ ] **Smoke Test**
  - Run relevant unit tests
  - Verify no import errors
  - Verify app still starts

- [ ] **Progress Log**
  - Update implementation tracker
  - Note any deviations from plan
  - Note any issues discovered

**After Phase 3 (execute() implemented):**

- [ ] **Integration Smoke Test**
  - Register new module in test orchestrator
  - Generate ONE test prompt
  - Verify output looks reasonable
  - Verify shared_state populated

**After Phase 7 (deletion):**

- [ ] **Comprehensive Grep**
  - `grep -r ContextAwarenessModule src/`
  - Should return zero results

**After Phase 9 (integration tests):**

- [ ] **Baseline Comparison** (Phase 9.5)
  - Run full baseline comparison
  - If quality < 95%: STOP, debug before proceeding
  - If token reduction < 50%: investigate (not blocking, but worth checking)

---

### Post-Implementation (MANDATORY)

**Before merging to main:**

- [ ] **Full Test Suite**
  - [ ] All unit tests pass: `pytest tests/services/prompts/modules/ -v`
  - [ ] All integration tests pass: `pytest tests/integration/ -v`
  - [ ] Smoke tests pass: `pytest tests/smoke/ -v`

- [ ] **Baseline Validation**
  - [ ] Quality scores ≥95% of baseline (BLOCKING)
  - [ ] Token reduction ≥50% (not blocking, but investigate if not met)
  - [ ] No critical validation failures

- [ ] **Manual UI Test**
  - [ ] Generate definition with context
  - [ ] Navigate to Edit tab
  - [ ] View generated prompt
  - [ ] Verify single context section (not 3)
  - [ ] Verify forbidden patterns section
  - [ ] Verify no duplication

- [ ] **Code Review**
  - [ ] Self-review: line-by-line check vs old code
  - [ ] Verify all business logic migrated
  - [ ] Verify all helper methods tested
  - [ ] Verify error paths covered

- [ ] **Documentation**
  - [ ] Update CLAUDE.md (module references)
  - [ ] Update architecture docs
  - [ ] Add DEF-155 entry to refactor-log.md

**After merging to main:**

- [ ] **Monitor First 10 Definitions**
  - Generate 10 definitions with various contexts
  - Manually review quality
  - Check validation scores
  - If issues: consider rollback

- [ ] **User Notification**
  - Inform user: "Context handling improved, expect slightly different prompts"
  - Ask user to report any quality issues
  - Monitor for 48 hours

---

### Circuit Breakers (Automated Monitoring)

**Add to CI/CD pipeline:**

```python
# tests/smoke/test_definition_quality_circuit_breaker.py
def test_quality_circuit_breaker():
    """Fail CI if definition quality drops below threshold."""
    # Generate 5 test definitions
    # Validate all 5
    # If any score < 0.7: FAIL
    # If average < 0.75: WARN
    pass
```

**Run on every commit in feature branch.**

---

## 9. MITIGATION STRATEGIES BY RISK CATEGORY

### CRITICAL Risks (Severity ≥ 60)

#### RISK #1: Silent Context Loss (Severity: 70)

**Mitigation:**
1. ✅ **Phase 0:** Capture baseline with real context data
2. ✅ **Phase 2.5:** Test `_extract_contexts()` with all input types
3. ✅ **Phase 8:** Add explicit context presence assertions
4. ✅ **Phase 9.5:** Baseline comparison detects missing context
5. ✅ **Monitoring:** Log warning if base_context non-empty but shared_state empty

**Residual risk:** LOW (after mitigations)

---

#### RISK #3: Circular Reasoning in Quality Validation (Severity: 64)

**Mitigation:**
1. ✅ **Phase 0:** Capture baseline with CURRENT system (MANDATORY)
2. ✅ **Phase 9.5:** Compare NEW scores to BASELINE scores (MANDATORY)
3. ✅ **Blocking condition:** Quality < 95% of baseline = DO NOT MERGE
4. ✅ **Manual review:** Developer reads 5 definitions, verifies quality

**Residual risk:** LOW (after mitigations)

---

### HIGH Risks (Severity 40-59)

#### RISK #2: Module Execution Order Breaks (Severity: 45)

**Mitigation:**
1. ✅ **Phase 4:** Document current and expected execution order
2. ✅ **Phase 5:** Update ErrorPreventionModule dependency to "context_instruction"
3. ✅ **Phase 7.5:** Verify no other modules depend on context_awareness
4. ✅ **Phase 8:** Add execution order test (Test Coverage Gap #6)

**Residual risk:** LOW (after mitigations)

---

#### RISK #4: Test False Positives (Severity: 48)

**Mitigation:**
1. ✅ **Phase 0:** Extract real context samples from database
2. ✅ **Phase 2.5:** Test helpers with real data (not mocks)
3. ✅ **Phase 8:** Add edge case tests (bool/str/list/None)
4. ✅ **Phase 9:** Integration tests use real context samples

**Residual risk:** MEDIUM (some edge cases may remain undiscovered)

---

#### RISK #6: Incomplete Business Logic Migration (Severity: 54)

**Mitigation:**
1. ✅ **Phase 2.5:** Migrate and test ALL helper methods
2. ✅ **Line-by-line review:** Developer checks every line of old module
3. ✅ **Checklist:** Mark each method as "migrated" or "N/A" with reason
4. ✅ **Sign-off:** Developer signs off that all business logic preserved

**Residual risk:** LOW (after careful review)

---

#### RISK #9: UI Doesn't Reflect Prompt Changes (Severity: 42)

**Mitigation:**
1. ✅ **Post-merge:** Manual UI test checklist (mandatory)
2. ✅ **Monitor:** Check Edit tab after first definition generated
3. ✅ **User testing:** Ask user to verify prompt display works

**Residual risk:** LOW (manual test catches most issues)

---

### MEDIUM Risks (Severity 20-39)

#### RISK #5: Token Reduction Not Achieved (Severity: 24)

**Mitigation:**
1. ✅ **Phase 0:** Measure current token usage (don't estimate)
2. ✅ **Phase 9.5:** Measure new token usage
3. ✅ **Compare:** Calculate actual reduction percentage
4. ✅ **If < 50%:** Investigate (but don't block merge)

**Residual risk:** LOW (not blocking issue)

---

#### RISK #7: Shared State Pollution (Severity: 35)

**Mitigation:**
1. ✅ **Phase 7.5:** Audit all modules for shared_state writes
2. ✅ **Single-writer rule:** Document that only ContextInstruction writes context keys
3. ✅ **Debug logging:** Add log statement for all shared_state writes
4. ✅ **Check threading:** Verify PromptOrchestrator threading behavior

**Residual risk:** LOW (after audit)

---

#### RISK #10: Rollback Impossible (Severity: 36)

**Mitigation:**
1. ✅ **Verify:** Plan says no database schema changes ← confirm this
2. ✅ **Feature branch:** Full development on feature branch
3. ✅ **Git commits:** Checkpoint after each phase
4. ✅ **Database backup:** Backup before first definition generated with new system

**Residual risk:** LOW (git provides rollback)

---

## 10. FINAL RISK VERDICT

### Overall Risk Assessment: 🟡 **MEDIUM-HIGH**

**Risk Distribution:**
- 🔴 **CRITICAL** (≥60): 2 risks
- 🟡 **HIGH** (40-59): 5 risks
- 🟡 **MEDIUM** (20-39): 3 risks

**Mitigated Risk Distribution (after implementing recommendations):**
- 🟢 **LOW** (residual): 8 risks
- 🟡 **MEDIUM** (residual): 2 risks

### Should We Proceed? ✅ **YES, BUT WITH CONDITIONS**

**Proceed ONLY IF:**
1. ✅ **Phase 0 (Baseline Capture) is MANDATORY** - add before Phase 1
2. ✅ **Phase 2.5 (Helper Tests) is MANDATORY** - add between Phase 2 and 3
3. ✅ **Phase 7.5 (Dependency Verify) is MANDATORY** - add after Phase 7
4. ✅ **Phase 9.5 (Baseline Compare) is MANDATORY** - add after Phase 9
5. ✅ **Budget 11.5 hours** (not 6 hours) - realistic timeline
6. ✅ **Blocking condition:** Quality ≥95% of baseline - no exceptions
7. ✅ **Manual UI test** - mandatory before merge

**DO NOT proceed if:**
- ❌ Timeline pressure forces cutting corners
- ❌ Baseline capture skipped
- ❌ Test coverage gaps accepted as "good enough"
- ❌ Developer lacks time for line-by-line review

### Recommendation: **PROCEED with enhanced plan**

**Implementation plan is GOOD, but needs 4 additional phases:**
1. Phase 0: Baseline Capture
2. Phase 2.5: Helper Method Tests
3. Phase 7.5: Dependency Verification
4. Phase 9.5: Baseline Comparison

**Expected outcome:**
- ✅ 50-65% token reduction
- ✅ Quality maintained (≥95% of baseline)
- ✅ Single source of truth for context
- ✅ Improved maintainability
- ✅ Clean architecture

**Risk level after mitigations:** 🟢 **LOW-MEDIUM** (acceptable for dev environment)

---

## 11. IMPLEMENTATION READINESS CHECKLIST

**Before starting Phase 1:**

- [ ] User approval obtained (>100 lines = requires approval per UNIFIED)
- [ ] 11.5 hours budgeted (not 6 hours)
- [ ] Test fixtures prepared (real context samples)
- [ ] Baseline captured and committed to git
- [ ] Current system documented (execution order, priorities, tokens)
- [ ] Dependencies audited (no hidden context_awareness dependencies)
- [ ] Developer has read this risk assessment
- [ ] Developer commits to NOT skipping phases

**If all checkboxes are ✓:** **PROCEED with implementation**

**If any checkbox is ☐:** **STOP - address gap before proceeding**

---

## APPENDIX A: Quick Reference - Risk Scores

| Risk | Severity | Status | Phase | Blocker? |
|------|----------|--------|-------|----------|
| 1. Silent context loss | 🔴 70 | Mitigated | 0, 2.5, 8, 9.5 | If not mitigated |
| 2. Execution order breaks | 🟡 45 | Mitigated | 4, 5, 7.5, 8 | No |
| 3. Circular validation | 🔴 64 | Mitigated | 0, 9.5 | **YES** |
| 4. Test false positives | 🟡 48 | Partial | 0, 2.5, 8, 9 | If quality fails |
| 5. Token reduction not met | 🟡 24 | Low priority | 0, 9.5 | No |
| 6. Incomplete migration | 🟡 54 | Mitigated | 2.5, review | If not reviewed |
| 7. Shared state pollution | 🟡 35 | Mitigated | 7.5, audit | No |
| 8. Error loops | 🟡 30 | Low likelihood | 8, error tests | No |
| 9. UI not updated | 🟡 42 | Mitigated | Post-merge | No |
| 10. Rollback impossible | 🟡 36 | Low likelihood | Git, backup | No |

**Blocking risks:** #3 (circular validation)
**Critical mitigations:** Phase 0 (baseline), Phase 9.5 (comparison)

---

## APPENDIX B: Comparison with Implementation Plan Claims

| Implementation Plan Claim | Risk Assessment Verdict | Notes |
|---------------------------|-------------------------|-------|
| "Low Risk: No backwards compatibility" | ✅ **AGREE** | Appropriate for single-user dev app |
| "4-5 hours implementation" | ❌ **DISAGREE** | 11.5 hours realistic (see revised timeline) |
| "Comprehensive unit tests" | ⚠️ **PARTIAL** | Good coverage but missing edge cases |
| "Integration tests verify context presence" | ⚠️ **WEAK** | Tests don't verify CORRECT context data |
| "Definition quality maintained" | ❌ **UNVERIFIABLE** | No baseline comparison planned |
| "No rollback mechanism needed" | ⚠️ **MISLEADING** | Rollback via git is fine, but need detection strategy |
| "Token reduction 50-65%" | ⚠️ **UNVERIFIED** | Estimate not measured, need baseline |
| "All tests pass = success" | ❌ **INSUFFICIENT** | Tests can pass with false positives |

**Overall assessment:** Plan is **GOOD foundation** but **underestimates risks** and **missing critical phases**.

---

**Document Status:** ✅ COMPLETE
**Created:** 2025-11-13
**Risk Assessment:** MEDIUM-HIGH → LOW-MEDIUM (after mitigations)
**Recommendation:** PROCEED with enhanced 11.5-hour plan including 4 additional phases
