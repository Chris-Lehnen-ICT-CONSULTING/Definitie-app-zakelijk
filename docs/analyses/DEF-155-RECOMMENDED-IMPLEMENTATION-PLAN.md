# DEF-155 Recommended Implementation Plan: Phased Hybrid Approach

**Date:** 2025-11-13
**Based on:** Multi-Agent Analysis (4 specialized agents)
**Approach:** Phased Hybrid with Validation Gates
**Total Effort:** 9 hours (Phase 1+2) or 17 hours (all 3 phases)

---

## Quick Reference

```
Phase 0: Pre-Work (1h)       → Baseline capture (MANDATORY)
Phase 1: Fix Bug (3h)        → Data access consistency (LOW risk)
  ├─ Gate 1: Quality check
Phase 2: Consolidate (4h)    → Remove redundancy (MEDIUM risk)
  ├─ Gate 2: Token reduction check
Phase 3: Full Refactor (8h)  → Optional (MEDIUM risk)
  └─ Gate 3: Final validation

Decision Point: After Phase 2 → STOP or proceed to Phase 3?
```

---

## PHASE 0: Pre-Work (MANDATORY) ⏱️ 1 hour

### Goal: Establish Baseline for Validation

**Why Critical:** Without baseline, we can't detect regressions (circular validation trap).

### Tasks:

#### 1. Install tiktoken (5 min)
```bash
pip install tiktoken
echo "tiktoken" >> requirements.txt
git add requirements.txt
git commit -m "build(deps): add tiktoken for token measurement (DEF-155)"
```

#### 2. Create Baseline Generation Script (15 min)
```python
# tests/debug/generate_baseline_def126.py
"""
Generate baseline definitions BEFORE DEF-155 refactor.
Used to detect quality regressions.
"""
import json
from pathlib import Path
from src.services.definition_generator import get_definition_generator

# Test cases covering different context scenarios
TEST_CASES = [
    {
        "begrip": "vergunning",
        "organisatorische_context": ["NP"],
        "juridische_context": ["Strafrecht"],
        "wettelijke_basis": ["Wetboek van Strafrecht"],
        "scenario": "rich_context"
    },
    {
        "begrip": "registratie",
        "organisatorische_context": ["DJI"],
        "juridische_context": [],
        "wettelijke_basis": [],
        "scenario": "moderate_context"
    },
    {
        "begrip": "beoordeling",
        "organisatorische_context": [],
        "juridische_context": ["Bestuursrecht"],
        "wettelijke_basis": [],
        "scenario": "minimal_context"
    },
    {
        "begrip": "aanvraag",
        "organisatorische_context": [],
        "juridische_context": [],
        "wettelijke_basis": [],
        "scenario": "no_context"
    },
    {
        "begrip": "melding",
        "organisatorische_context": ["NP", "OM"],
        "juridische_context": ["Strafrecht", "Bestuursrecht"],
        "wettelijke_basis": ["Wetboek van Strafrecht", "Algemene wet bestuursrecht"],
        "scenario": "multiple_contexts"
    }
]

def main():
    generator = get_definition_generator()
    baseline = []

    print("🔍 Generating baseline definitions (BEFORE DEF-155)...\n")

    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"[{i}/{len(TEST_CASES)}] {test_case['scenario']}: {test_case['begrip']}")

        try:
            result = generator.generate_definition(
                begrip=test_case["begrip"],
                organisatorische_context=test_case["organisatorische_context"],
                juridische_context=test_case["juridische_context"],
                wettelijke_basis=test_case["wettelijke_basis"]
            )

            baseline.append({
                "test_case": test_case,
                "definition": result.definition,
                "quality_score": result.validation_results.overall_score if hasattr(result, 'validation_results') else None,
                "prompt_tokens": len(result.prompt.split()) if hasattr(result, 'prompt') else None,
            })

            print(f"  ✓ Definition: {result.definition[:80]}...")
            print(f"  ✓ Quality: {baseline[-1]['quality_score']}")
            print()

        except Exception as e:
            print(f"  ✗ Error: {e}\n")
            baseline.append({
                "test_case": test_case,
                "error": str(e)
            })

    # Save baseline
    output_path = Path("tests/debug/baseline_def126.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False)

    print(f"✅ Baseline saved to: {output_path}")
    print(f"📊 Total test cases: {len(baseline)}")
    print(f"✓ Successful: {sum(1 for b in baseline if 'error' not in b)}")
    print(f"✗ Failed: {sum(1 for b in baseline if 'error' in b)}")

if __name__ == "__main__":
    main()
```

#### 3. Generate Baseline (20 min)
```bash
python tests/debug/generate_baseline_def126.py

# Verify output
cat tests/debug/baseline_def126.json | head -50
```

**Expected Output:** JSON file with 5 baseline definitions.

#### 4. Measure Token Counts (20 min)
```python
# tests/debug/measure_tokens_def126.py
"""Measure current token usage (BEFORE DEF-155)."""
import json
import tiktoken
from src.services.prompts.prompt_service_v2 import PromptServiceV2

def count_tokens(text: str) -> int:
    """Count tokens using GPT-4 tokenizer."""
    encoder = tiktoken.encoding_for_model("gpt-4")
    return len(encoder.encode(text))

def main():
    service = PromptServiceV2()

    # Load test cases
    with open("tests/debug/baseline_def126.json") as f:
        baseline = json.load(f)

    measurements = []

    print("📊 Measuring token usage (BEFORE DEF-155)...\n")

    for entry in baseline:
        if "error" in entry:
            continue

        test_case = entry["test_case"]

        # Generate prompt (don't call API)
        prompt = service.build_prompt(
            begrip=test_case["begrip"],
            organisatorische_context=test_case["organisatorische_context"],
            juridische_context=test_case["juridische_context"],
            wettelijke_basis=test_case["wettelijke_basis"]
        )

        tokens = count_tokens(prompt)

        measurements.append({
            "scenario": test_case["scenario"],
            "begrip": test_case["begrip"],
            "tokens": tokens
        })

        print(f"{test_case['scenario']:20} | {test_case['begrip']:15} | {tokens:4} tokens")

    # Calculate statistics
    total_tokens = sum(m["tokens"] for m in measurements)
    avg_tokens = total_tokens / len(measurements)

    print(f"\n{'─' * 60}")
    print(f"Average tokens: {avg_tokens:.1f}")
    print(f"Total tokens (5 cases): {total_tokens}")
    print(f"\n✅ Baseline measurements saved")

if __name__ == "__main__":
    main()
```

```bash
python tests/debug/measure_tokens_def126.py > baseline_tokens_def126.txt
cat baseline_tokens_def126.txt
```

**Expected Output:** Token counts per scenario (baseline for comparison).

### Acceptance Criteria:
- ✅ `tiktoken` installed
- ✅ `baseline_def126.json` exists with 5 definitions
- ✅ `baseline_tokens_def126.txt` shows token counts
- ✅ All 5 test cases generated successfully

**Time Checkpoint:** Should complete in 1 hour. If >1.5h → investigate blockers.

---

## PHASE 1: Fix Data Access Bug ⏱️ 3 hours

### Goal: Make DefinitionTaskModule use shared_state consistently

**Risk Level:** 🟢 LOW (using existing pattern, minimal changes)
**Token Impact:** ~5% (minimal, sets foundation for Phase 2)

### The Bug:

```python
# definition_task_module.py lines 84-104 (CURRENT - BUGGY)
base_ctx = context.enriched_context.base_context  # ⚠️ BYPASSES shared_state!
jur_contexts = base_ctx.get("juridische_context") or base_ctx.get("juridisch") or []
wet_basis = base_ctx.get("wettelijke_basis") or base_ctx.get("wettelijk") or []

# Meanwhile, ErrorPreventionModule uses:
jur_contexts = context.get_shared("juridical_contexts", [])  # Different name!

# Result: INCONSISTENT DATA ACCESS
```

### Tasks:

#### 1. Update DefinitionTaskModule (1 hour)

**File:** `src/services/prompts/modules/definition_task_module.py`

**Change lines 84-104:**

```python
# BEFORE (DELETE):
# Derive juridical and legal-basis contexts from enriched base_context
base_ctx = (
    context.enriched_context.base_context
    if context and context.enriched_context
    else {}
)
jur_contexts = (
    base_ctx.get("juridische_context")
    or base_ctx.get("juridisch")
    or []
)
wet_basis = (
    base_ctx.get("wettelijke_basis")
    or base_ctx.get("wettelijk")
    or []
)

# AFTER (REPLACE WITH):
# Use shared_state for consistency (DEF-155 Phase 1)
org_contexts = context.get_shared("organization_contexts", [])
jur_contexts = context.get_shared("juridical_contexts", [])
wet_basis = context.get_shared("legal_basis_contexts", [])
```

**Lines removed:** ~20 lines
**Lines added:** ~3 lines

#### 2. Update Tests (1 hour)

**File:** `tests/services/prompts/modules/test_definition_task_module.py`

**Add new test:**

```python
def test_uses_shared_state_not_direct_access():
    """
    Verify module uses shared_state for context (DEF-155 Phase 1).

    Previously, DefinitionTaskModule read directly from base_context,
    bypassing the shared_state pattern. This caused inconsistencies.
    """
    module = DefinitionTaskModule()
    module.initialize({})

    # Create context with shared_state ONLY
    context = create_test_context(begrip="vergunning")
    context.set_shared("juridical_contexts", ["Strafrecht"])
    context.set_shared("legal_basis_contexts", ["Wetboek van Strafrecht"])

    # DO NOT set enriched_context.base_context
    # Module should use shared_state ONLY

    output = module.execute(context)

    # Verify context metadata includes Strafrecht
    assert "Strafrecht" in output.content or "Strafrecht" in str(output.metadata)
```

**Run existing tests:**
```bash
pytest tests/services/prompts/modules/test_definition_task_module.py -v
```

**Expected:** All tests pass (no regressions).

#### 3. Validation (1 hour)

**Run baseline comparison:**
```bash
# Generate definitions with Phase 1 changes
python tests/debug/generate_baseline_def126.py > after_phase1.json

# Compare to baseline
python tests/debug/compare_baselines.py baseline_def126.json after_phase1.json
```

**Expected Results:**
- ✅ Definitions IDENTICAL or BETTER quality
- ✅ No new validation failures
- ✅ Context still appears in metadata

**Manual QA:**
1. Start app: `bash scripts/run_app.sh`
2. Generate 2-3 definitions with context
3. Verify: Context metadata still visible? YES/NO
4. Verify: Definition quality acceptable? YES/NO

### Acceptance Criteria:
- ✅ DefinitionTaskModule uses `shared_state` (not `base_context`)
- ✅ All existing tests pass
- ✅ New test `test_uses_shared_state_not_direct_access()` passes
- ✅ Baseline comparison shows no quality regression
- ✅ Manual QA confirms context metadata still works

**Time Checkpoint:** Should complete in 3 hours. If >4h → investigate test failures.

---

## DECISION GATE 1: Quality Check ⏱️ 30 min

**BLOCKING:** Must pass before proceeding to Phase 2.

### Validation Steps:

1. **Compare Baselines:**
```bash
python tests/debug/compare_baselines.py baseline_def126.json after_phase1.json
```

**Expected:** Quality scores within ±5% of baseline.

2. **Manual Review (5 definitions):**
   - Generate 5 definitions (mix of context scenarios)
   - Compare to baseline definitions
   - Rate quality: BETTER / SAME / WORSE

3. **Decision:**
   - ✅ **PASS:** Quality maintained → Proceed to Phase 2
   - ❌ **FAIL:** Quality degraded → Investigate root cause, fix, re-validate

**Success Criteria:**
- Quality score ≥95% of baseline
- No new validation failures
- User confirms quality acceptable

---

## PHASE 2: Consolidate Redundancy ⏱️ 4 hours

### Goal: Remove duplicate "gebruik context" instructions

**Risk Level:** 🟡 MEDIUM (changes prompt generation logic)
**Token Impact:** ~5% total prompt reduction (~60% of context section = 120 tokens saved)

### Current Redundancy:

```python
# ContextAwarenessModule line 242 (moderate):
"Gebruik onderstaande context om de definitie specifiek te maken..."

# ContextAwarenessModule line 64 (rich):
"Gebruik onderstaande context om de definitie specifiek te maken..."  # DUPLICATE!

# DefinitionTaskModule line 204 (checklist):
"→ Context verwerkt zonder expliciete benoeming"  # DUPLICATE!
```

### Tasks:

#### 1. Refactor ContextAwarenessModule (2 hours)

**File:** `src/services/prompts/modules/context_awareness_module.py`

**Create new method:**

```python
def _build_unified_context_section(
    self,
    context: ModuleContext,
    context_score: float,
) -> str:
    """
    Build unified context section (DEF-155 Phase 2).

    Single instruction, formatting varies by score.
    Eliminates redundancy from rich/moderate/minimal variants.
    """
    sections = []

    # Get contexts from enriched_context
    base_ctx = context.enriched_context.base_context
    org_contexts = self._extract_contexts(base_ctx.get("organisatorisch"))
    jur_contexts = self._extract_contexts(base_ctx.get("juridisch"))
    wet_contexts = self._extract_contexts(base_ctx.get("wettelijk"))

    # Share via shared_state for other modules
    self._share_traditional_context(context)

    # ONE instruction (not multiple)
    sections.append("📌 VERPLICHTE CONTEXT INFORMATIE:")
    sections.append(
        "⚠️ Gebruik onderstaande context om de definitie specifiek te maken "
        "voor deze organisatorische, juridische en wettelijke setting, "
        "zonder de context expliciet te benoemen."
    )

    # Vary ONLY the formatting based on score
    if context_score >= 0.8:
        # Rich: Detailed with emoji categories
        sections.extend(self._format_rich_context(org_contexts, jur_contexts, wet_contexts))
    elif context_score >= 0.5:
        # Moderate: Standard listing
        sections.extend(self._format_moderate_context(org_contexts, jur_contexts, wet_contexts))
    else:
        # Minimal: Compact inline
        sections.extend(self._format_minimal_context(org_contexts, jur_contexts, wet_contexts))

    return "\n".join(sections)
```

**Refactor existing methods:**
- `_build_rich_context_section()` → `_format_rich_context()` (formatting only)
- `_build_moderate_context_section()` → `_format_moderate_context()` (formatting only)
- `_build_minimal_context_section()` → `_format_minimal_context()` (formatting only)

**Update execute():**

```python
def execute(self, context: ModuleContext) -> ModuleOutput:
    # Calculate score
    context_score = self._calculate_context_score(context.enriched_context)

    # NEW: Single unified section
    content = self._build_unified_context_section(context, context_score)

    return ModuleOutput(
        content=content,
        metadata={"context_score": context_score}
    )
```

#### 2. Update DefinitionTaskModule Checklist (0.5 hour)

**File:** `src/services/prompts/modules/definition_task_module.py`

**Change line 204 in `_build_checklist()`:**

```python
# BEFORE:
return f"""📋 **CONSTRUCTIE GUIDE - Bouw je definitie op:**
→ Begint met zelfstandig naamwoord (geen lidwoord/koppelwerkwoord)
→ Eén enkele zin zonder punt aan het einde
→ Geen toelichting, voorbeelden of haakjes
→ Ontologische categorie is duidelijk{ont_cat}
→ Geen verboden woorden (aspect, element, kan, moet, etc.)
→ Context verwerkt zonder expliciete benoeming"""  # ← REMOVE THIS LINE

# AFTER:
return f"""📋 **CONSTRUCTIE GUIDE - Bouw je definitie op:**
→ Begint met zelfstandig naamwoord (geen lidwoord/koppelwerkwoord)
→ Eén enkele zin zonder punt aan het einde
→ Geen toelichting, voorbeelden of haakjes
→ Ontologische categorie is duidelijk{ont_cat}
→ Geen verboden woorden (aspect, element, kan, moet, etc.)"""
```

**Rationale:** "Context verwerkt..." is now stated ONCE in ContextAwarenessModule.

#### 3. Update Tests (1 hour)

**File:** `tests/services/prompts/modules/test_context_awareness_module.py`

**Add test:**

```python
def test_single_context_instruction_phase2():
    """
    Verify context instruction appears ONCE (DEF-155 Phase 2).

    Previously, "Gebruik onderstaande context..." appeared 2-3 times.
    Now it should appear exactly ONCE.
    """
    module = ContextAwarenessModule()
    module.initialize({})

    context = create_test_context(org=["NP"], jur=["Strafrecht"])

    output = module.execute(context)

    # Count occurrences of instruction
    instruction = "Gebruik onderstaande context"
    count = output.content.count(instruction)

    assert count == 1, f"Instruction should appear ONCE, found {count} times"

    # Verify formatting still varies by score
    score = output.metadata.get("context_score", 0)
    if score >= 0.8:
        assert "🎯 ORGANISATORISCHE CONTEXT:" in output.content
    elif score >= 0.5:
        assert "📌 VERPLICHTE CONTEXT" in output.content
```

#### 4. Measure Token Reduction (0.5 hour)

```bash
# Generate prompts with Phase 2 changes
python tests/debug/measure_tokens_def126.py > after_phase2_tokens.txt

# Compare to baseline
python tests/debug/compare_token_counts.py baseline_tokens_def126.txt after_phase2_tokens.txt
```

**Expected Results:**
```
Scenario              | Before | After  | Reduction
─────────────────────────────────────────────────────
rich_context          | 290    | 120    | 58.6%
moderate_context      | 240    | 92     | 61.7%
minimal_context       | 180    | 45     | 75.0%
no_context            | 38     | 10     | 73.7%
multiple_contexts     | 310    | 135    | 56.5%
─────────────────────────────────────────────────────
AVERAGE               | 212    | 80     | 62.3%
```

**Target:** ≥100 tokens reduction (≥26%)

### Acceptance Criteria:
- ✅ Context instruction appears ONCE (not 2-3x)
- ✅ Token reduction ≥100 tokens (26%+)
- ✅ All tests pass
- ✅ Formatting still varies by context score
- ✅ No quality regression

**Time Checkpoint:** Should complete in 4 hours. If >5h → simplify formatting changes.

---

## DECISION GATE 2: Token Reduction Check ⏱️ 30 min

**BLOCKING:** Determines if Phase 3 is needed.

### Validation Steps:

1. **Measure Token Reduction:**
```bash
python tests/debug/compare_token_counts.py baseline_tokens_def126.txt after_phase2_tokens.txt
```

**Expected:** ≥100 tokens reduction (26%+)

2. **Quality Validation:**
```bash
python tests/debug/compare_baselines.py baseline_def126.json after_phase2.json
```

**Expected:** Quality ≥95% of baseline

3. **User Decision:**

**If token reduction ≥150 tokens (39%+):**
```
✅ SUFFICIENT - Phase 1+2 achieved significant impact
Decision: STOP HERE (9 hours total)
```

**If token reduction 100-150 tokens (26-39%):**
```
🟡 MODERATE - Some improvement, more possible
Decision: User choice (STOP or proceed to Phase 3)
```

**If token reduction <100 tokens (<26%):**
```
❌ INSUFFICIENT - Expected benefit not achieved
Decision: MUST proceed to Phase 3 OR investigate issues
```

### Success Criteria:
- Token reduction ≥26% (100+ tokens)
- Quality maintained (≥95% of baseline)
- User decision: STOP or CONTINUE?

---

## PHASE 3: Full Consolidation (OPTIONAL) ⏱️ 8 hours

**ONLY execute if Phase 2 token reduction insufficient OR user wants best architecture.**

### Goal: Create single ContextInstructionModule

**Risk Level:** 🟡 MEDIUM (major refactor, deletes entire module)
**Token Impact:** +20-30% beyond Phase 2 (total 50-68%)

### Approach: Follow Architecture Agent's ContextOrchestrator Pattern

**Instead of monolithic module (god object), use 4 specialized modules:**

1. **ContextExtractor** (120 lines) - Scoring + extraction
2. **ContextFormatter** (100 lines) - Adaptive formatting
3. **ContextConstraintBuilder** (80 lines) - Forbidden patterns
4. **ContextMetadataBuilder** (60 lines) - Optional metadata

**See:** `DEF-155-ARCHITECTURE-EVALUATION.md` Section 3 for detailed design.

### Tasks (High-Level):

1. **Create 4 new modules** (3 hours)
   - Migrate business logic from existing modules
   - Implement shared_state communication
   - Unit tests per module

2. **Register modules in orchestrator** (0.5 hour)
   - Update prompt service
   - Configure priorities + dependencies

3. **Refactor existing modules** (2 hours)
   - ErrorPreventionModule: Remove context logic
   - DefinitionTaskModule: Remove metadata logic

4. **Delete ContextAwarenessModule** (0.5 hour)
   - Remove file
   - Update imports
   - Verify no references remain

5. **Integration testing** (1.5 hours)
   - Full prompt generation test
   - Token measurement
   - Quality validation

6. **Documentation** (0.5 hour)
   - Update architecture docs
   - Document new modules
   - Update CLAUDE.md

**Total:** 8 hours

### Acceptance Criteria:
- ✅ Token reduction 50-68% (total, including Phase 1+2)
- ✅ All 4 modules follow SRP
- ✅ No god object anti-pattern
- ✅ Quality ≥95% of baseline
- ✅ Test coverage ≥80%

**Time Checkpoint:** Should complete in 8 hours. If >10h → consider simplifications.

---

## DECISION GATE 3: Final Validation ⏱️ 30 min

### Comprehensive Validation:

1. **Token Reduction:**
```bash
python tests/debug/measure_tokens_def126.py > after_phase3_tokens.txt
python tests/debug/compare_token_counts.py baseline_tokens_def126.txt after_phase3_tokens.txt
```

**Expected:** 50-68% reduction (200-250 tokens)

2. **Quality Validation:**
```bash
pytest tests/services/test_definition_generator.py -v
python tests/debug/compare_baselines.py baseline_def126.json after_phase3.json
```

**Expected:** ≥95% quality maintained

3. **Architecture Review:**
   - ✅ No god objects (modules <200 lines each)
   - ✅ SRP compliance (each module has 1 clear responsibility)
   - ✅ Test coverage ≥80%

### Success Criteria:
- Token reduction ≥50%
- Quality ≥95% baseline
- Architecture improved
- All tests pass

---

## ROLLBACK PROCEDURES

### Phase 1 Rollback:
```bash
git revert <phase1-commit-sha>
# DefinitionTaskModule reverts to direct base_context access
```

### Phase 2 Rollback:
```bash
git revert <phase2-commit-sha>
# ContextAwarenessModule reverts to rich/moderate/minimal variants
```

### Phase 3 Rollback:
```bash
git revert <phase3-commit-sha>
# Restore ContextAwarenessModule from git history
git checkout <before-phase3> -- src/services/prompts/modules/context_awareness_module.py
```

**App restart required** after rollback (singleton cache).

---

## TIMELINE & RESOURCE PLANNING

### Option A: Phase 1+2 Only (9 hours)

**Day 1 (Morning - 5h):**
- 08:00-09:00: Phase 0 (Pre-work)
- 09:00-12:00: Phase 1 (Fix bug)
- 12:00-12:30: Gate 1 (Quality check)

**Day 1 (Afternoon - 4.5h):**
- 13:00-17:00: Phase 2 (Consolidate)
- 17:00-17:30: Gate 2 (Token check + DECISION)

**Total: 1.5 days**

---

### Option B: All 3 Phases (17 hours)

**Day 1 (Morning - 5h):**
- Phase 0 + Phase 1 + Gate 1

**Day 1 (Afternoon - 4.5h):**
- Phase 2 + Gate 2 (DECISION: Proceed to Phase 3)

**Day 2 (Full day - 8h):**
- 08:00-16:00: Phase 3 (Full consolidation)
- 16:00-16:30: Gate 3 (Final validation)

**Total: 2 days**

---

## METRICS & REPORTING

### Track Throughout Implementation:

```bash
# Token counts
echo "$(python tests/debug/measure_tokens_def126.py)" > progress_tokens.txt

# Quality scores
echo "$(python tests/debug/compare_baselines.py baseline_def126.json current.json)" > progress_quality.txt

# Test coverage
pytest --cov=src/services/prompts/modules --cov-report=term-missing

# Time tracking
echo "Phase 1 started: $(date)" >> time_tracking.txt
echo "Phase 1 completed: $(date)" >> time_tracking.txt
```

### Final Report (after completion):

```markdown
# DEF-155 Implementation Report

**Completed Phases:** 1+2 (or 1+2+3)
**Total Time:** X hours (budget: Y hours)
**Token Reduction:** A → B tokens (C% reduction)
**Quality Score:** Before: X, After: Y (Z% change)
**Tests:** X/Y passing
**Risk Level:** LOW/MEDIUM (all gates passed)

**Conclusion:** SUCCESS/PARTIAL/FAILURE
**Next Steps:** ...
```

---

## APPROVAL CHECKLIST

**Before starting implementation:**

- [ ] User approved Phased Hybrid approach
- [ ] User reviewed timeline (9h or 17h)
- [ ] User aware of validation gates (can block progress)
- [ ] Team capacity available (1-2 days dedicated time)
- [ ] Backup/rollback strategy understood

**Ready to start?** YES / NO

---

**Document Status:** ✅ READY FOR IMPLEMENTATION
**Recommendation:** Start with Phase 0+1+2 (9 hours)
**Risk:** LOW-MEDIUM (with validation gates)
**Expected Impact:** 26-68% token reduction, improved architecture

**Next Step:** User approval → Execute Phase 0
