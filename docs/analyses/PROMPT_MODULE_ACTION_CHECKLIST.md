# Prompt Module Optimization - Action Checklist
**Date:** 2025-01-12
**Status:** Ready to implement

## Phase 1: Critical Fixes (START HERE)
**Goal:** Fix broken module + resolve contradictions
**Time:** 4 hours
**Risk:** LOW (fixes only, no major refactoring)

### Task 1.1: Fix TemplateModule Validation (1 hour)

**File:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/template_module.py`

**Changes:**
```python
# Line 63: BEFORE
category = context.get_metadata("semantic_category")

# Line 63: AFTER
category = context.get_metadata("ontologische_categorie")
```

**Additional change:**
```python
# Line 81: BEFORE
category = context.get_metadata("semantic_category", "algemeen")

# Line 81: AFTER
category = context.get_metadata("ontologische_categorie", "algemeen")
```

**Test:**
```bash
pytest tests/services/prompts/test_modules_basic.py::test_template_module_runs -v
```

**Verification:**
- [ ] Module validation passes
- [ ] Module executes without errors
- [ ] Category-specific templates generated
- [ ] Test passes

---

### Task 1.2: Resolve Kick-off Contradiction (1 hour)

**File:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/error_prevention_module.py`

**Problem:** Line 178-179 forbids "proces waarbij", "handeling die" which SemanticCategorisationModule instructs to use

**Change 1 - Update forbidden_starters list (line 156-191):**
```python
# BEFORE: Includes noun phrases
forbidden_starters = [
    "proces waarbij",       # ❌ REMOVE (noun, not verb)
    "handeling die",        # ❌ REMOVE (noun, not verb)
    ...
]

# AFTER: Only verb phrases
forbidden_starters = [
    "is",                   # ✓ KEEP (verb)
    "betreft",              # ✓ KEEP (verb)
    "omvat",                # ✓ KEEP (verb)
    "betekent",             # ✓ KEEP (verb)
    "verwijst naar",        # ✓ KEEP (verb phrase)
    "houdt in",             # ✓ KEEP (verb phrase)
    "heeft betrekking op",  # ✓ KEEP (verb phrase)
    "duidt op",             # ✓ KEEP (verb phrase)
    "staat voor",           # ✓ KEEP (verb phrase)
    "impliceert",           # ✓ KEEP (verb)
    "definieert",           # ✓ KEEP (verb)
    "beschrijft",           # ✓ KEEP (verb)
    "wordt",                # ✓ KEEP (verb)
    "zijn",                 # ✓ KEEP (verb)
    "was",                  # ✓ KEEP (verb)
    "waren",                # ✓ KEEP (verb)
    "behelst",              # ✓ KEEP (verb)
    "bevat",                # ✓ KEEP (verb)
    "bestaat uit",          # ✓ KEEP (verb phrase)
    "de",                   # ✓ KEEP (article)
    "het",                  # ✓ KEEP (article)
    "een",                  # ✓ KEEP (article)
    # REMOVED: "proces waarbij", "handeling die", "activiteit waarbij" (nouns)
    "vorm van",             # ✓ KEEP (meta-word)
    "type van",             # ✓ KEEP (meta-word)
    "soort van",            # ✓ KEEP (meta-word)
    "methode voor",         # ✓ KEEP (too generic)
    "wijze waarop",         # ✓ KEEP (too generic)
    "manier om",            # ✓ KEEP (too generic)
    "een belangrijk",       # ✓ KEEP (subjective)
    "een essentieel",       # ✓ KEEP (subjective)
    "een vaak gebruikte",   # ✓ KEEP (subjective)
    "een veelvoorkomende",  # ✓ KEEP (subjective)
]
```

**Change 2 - Add clarification comment (after line 191):**
```python
# BELANGRIJK: Deze lijst verbiedt WERKWOORDEN en META-WOORDEN.
# Zelfstandige naamwoorden zoals "proces", "activiteit", "handeling"
# zijn TOEGESTAAN als kick-off (handelingsnaamwoorden, niet werkwoorden).
#
# ✅ GOED: "proces dat...", "activiteit waarbij...", "handeling die..."
# ❌ FOUT: "is een proces", "betekent een activiteit"
```

**Test:**
```bash
# Test that noun kick-offs are not flagged as errors
pytest tests/services/prompts/test_modules_basic.py::test_error_prevention_noun_kickoffs -v
```

**Verification:**
- [ ] "proces waarbij" removed from forbidden list
- [ ] "handeling die" removed from forbidden list
- [ ] "activiteit waarbij" removed from forbidden list
- [ ] Verbs still forbidden ("is", "betekent", etc.)
- [ ] Clarification comment added
- [ ] Test passes

---

### Task 1.3: Fix Hardcoded STR Rules (1 hour)

**File:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/structure_rules_module.py`

**Problem:** Lines 80-332 hardcode rules instead of loading from cache

**Change - Replace hardcoded methods with cache loading:**

```python
# BEFORE (lines 70-332): 9 hardcoded _build_str0X_rule() methods

# AFTER: Replace execute() method with cache loading
def execute(self, context: ModuleContext) -> ModuleOutput:
    """Genereer STR validatieregels."""
    try:
        sections = []
        sections.append("### 🏗️ Structuur Regels (STR):")
        sections.append("")

        # Load toetsregels on-demand from cached singleton
        from toetsregels.cached_manager import get_cached_toetsregel_manager

        manager = get_cached_toetsregel_manager()
        all_rules = manager.get_all_regels()

        # Filter alleen STR regels
        str_rules = {k: v for k, v in all_rules.items() if k.startswith("STR-")}

        # Sorteer regels
        sorted_rules = sorted(str_rules.items())

        for regel_key, regel_data in sorted_rules:
            sections.extend(self._format_rule(regel_key, regel_data))

        content = "\n".join(sections)

        return ModuleOutput(
            content=content,
            metadata={
                "rules_count": len(str_rules),
                "include_examples": self.include_examples,
                "rule_prefix": "STR",
            },
        )

    except Exception as e:
        logger.error(f"StructureRulesModule execution failed: {e}", exc_info=True)
        return ModuleOutput(
            content="",
            metadata={"error": str(e)},
            success=False,
            error_message=f"Failed to generate STR rules: {e!s}",
        )

def _format_rule(self, regel_key: str, regel_data: dict) -> list[str]:
    """Formateer een regel uit JSON data."""
    lines = []

    # Header met emoji
    naam = regel_data.get("naam", "Onbekende regel")
    lines.append(f"🔹 **{regel_key} - {naam}**")

    # Uitleg
    uitleg = regel_data.get("uitleg", "")
    if uitleg:
        lines.append(f"- {uitleg}")

    # Toetsvraag
    toetsvraag = regel_data.get("toetsvraag", "")
    if toetsvraag:
        lines.append(f"- Toetsvraag: {toetsvraag}")

    # Voorbeelden (indien enabled)
    if self.include_examples:
        # Goede voorbeelden
        goede_voorbeelden = regel_data.get("goede_voorbeelden", [])
        for goed in goede_voorbeelden:
            lines.append(f"  ✅ {goed}")

        # Foute voorbeelden
        foute_voorbeelden = regel_data.get("foute_voorbeelden", [])
        for fout in foute_voorbeelden:
            lines.append(f"  ❌ {fout}")

    lines.append("")  # Empty line between rules
    return lines

# REMOVE: All 9 _build_str0X_rule() methods (lines 132-332)
```

**Test:**
```bash
# Verify all STR rules load correctly
pytest tests/services/prompts/test_modules_basic.py::test_structure_rules_from_cache -v

# Compare output before/after
python scripts/compare_str_rules_output.py
```

**Verification:**
- [ ] All 9 STR rules present in output
- [ ] Rules loaded from cache (no hardcoded)
- [ ] Format matches original output
- [ ] Examples included (if enabled)
- [ ] Test passes

---

### Task 1.4: Fix Hardcoded INT Rules (1 hour)

**File:** `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/integrity_rules_module.py`

**Problem:** Similar to STR, hardcoded instead of loading from cache

**Change - Apply same pattern as Task 1.3:**

```python
# Replace execute() method with cache loading (same pattern as STR)
# Replace _format_rule() method (same as STR)
# Remove all hardcoded _build_intXX_rule() methods
```

**Test:**
```bash
# Verify all INT rules load correctly
pytest tests/services/prompts/test_modules_basic.py::test_integrity_rules_from_cache -v

# Compare output before/after
python scripts/compare_int_rules_output.py
```

**Verification:**
- [ ] All INT rules present in output
- [ ] Rules loaded from cache (no hardcoded)
- [ ] Format matches original output
- [ ] Examples included (if enabled)
- [ ] Test passes

---

### Phase 1 Completion Checklist

**Before proceeding to Phase 2, verify:**

- [ ] All 16 modules execute without errors
- [ ] TemplateModule validation passes
- [ ] Zero contradictions between modules
- [ ] All STR rules loaded from cache
- [ ] All INT rules loaded from cache
- [ ] US-202 compliant (no duplicate loading)
- [ ] All existing tests pass
- [ ] No regression in definition quality

**Commit:**
```bash
git add src/services/prompts/modules/template_module.py
git add src/services/prompts/modules/error_prevention_module.py
git add src/services/prompts/modules/structure_rules_module.py
git add src/services/prompts/modules/integrity_rules_module.py
git commit -m "fix(prompts): resolve critical module issues

- Fix TemplateModule validation (ontologische_categorie)
- Resolve kick-off contradiction (noun vs verb)
- Convert STR rules to cache loading (US-202)
- Convert INT rules to cache loading (US-202)

All 16 modules now functional, zero contradictions.
Refs: DEF-XXX"
```

---

## Phase 2: Simple Merges (6 hours)
**Status:** Ready after Phase 1 complete

### Task 2.1: Merge OutputSpec → Expertise (1 hour)

**Steps:**
1. Read `/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules/output_specification_module.py`
2. Extract format methods
3. Integrate into ExpertiseModule
4. Remove OutputSpecificationModule
5. Update orchestrator registration
6. Test prompt generation

**Files affected:**
- `src/services/prompts/modules/expertise_module.py` (edit)
- `src/services/prompts/modules/output_specification_module.py` (delete)
- `src/services/prompts/modules/prompt_orchestrator.py` (edit - registration)

---

### Task 2.2: Merge Template → Semantic (3 hours)

**Steps:**
1. Read both modules
2. Extract template methods from TemplateModule
3. Integrate into SemanticCategorisationModule → CategoryGuidanceModule
4. Unify category guidance (ESS-02 + templates)
5. Remove TemplateModule
6. Update orchestrator registration
7. Test all 4 categories (proces, type, resultaat, exemplaar)

**Files affected:**
- `src/services/prompts/modules/semantic_categorisation_module.py` (edit + rename)
- `src/services/prompts/modules/template_module.py` (delete)
- `src/services/prompts/modules/prompt_orchestrator.py` (edit)

---

### Task 2.3: Merge ErrorPrev → Validation (prep) (2 hours)

**Steps:**
1. Document ErrorPreventionModule structure
2. Identify forbidden patterns logic
3. Prepare integration plan for Phase 3
4. Keep module for now (merge in Phase 3)

**Note:** This is preparation only, actual merge happens in Phase 3

---

## Phase 3: Major Consolidation (8 hours)
**Status:** Ready after Phase 2 complete

### Task 3.1: Create ValidationRulesModule (4 hours)

**Goal:** Consolidate 7 rule modules + ErrorPrev into 1

**Steps:**
1. Create new ValidationRulesModule
2. Implement unified rule loading (all categories)
3. Add forbidden patterns section (from ErrorPrev)
4. Test with subset of categories (ARAI, CON, ESS)
5. Add remaining categories (STR, INT, SAM, VER)
6. Full testing (45 rules present)

---

### Task 3.2: Remove 7 old rule modules (2 hours)

**Steps:**
1. Delete individual rule modules
2. Update orchestrator registration
3. Run regression tests
4. Verify token count reduction

**Files to delete:**
- `arai_rules_module.py`
- `con_rules_module.py`
- `ess_rules_module.py`
- `structure_rules_module.py`
- `integrity_rules_module.py`
- `sam_rules_module.py`
- `ver_rules_module.py`
- `error_prevention_module.py`

---

## Phase 4: Refinement (2 hours)
**Status:** Ready after Phase 3 complete

### Task 4.1: Simplify GrammarModule (1 hour)

**Changes:**
- Remove strict mode (dead code)
- Remove word type duplication
- Focus on grammar only

---

### Task 4.2: Simplify DefinitionTaskModule (1 hour)

**Changes:**
- Reduce checklist (6→4 items)
- Simplify metadata
- Remove redundant sections

---

## Testing Strategy

### After each phase:

```bash
# Unit tests
pytest tests/services/prompts/ -v

# Integration tests
pytest tests/integration/test_prompt_generation.py -v

# Regression tests
pytest tests/regression/ -v

# Token count measurement
python scripts/measure_prompt_tokens.py
```

---

## Success Criteria

### Phase 1 (Critical Fixes)
- [ ] All 16 modules functional
- [ ] Zero contradictions
- [ ] US-202 compliant (all rules from cache)
- [ ] All tests passing

### Phase 2 (Simple Merges)
- [ ] 16 → 10 modules
- [ ] ~1,000 tokens saved
- [ ] All tests passing

### Phase 3 (Major Consolidation)
- [ ] 10 → 7 modules
- [ ] ~2,500 tokens saved
- [ ] All 45 rules present
- [ ] All tests passing

### Phase 4 (Refinement)
- [ ] Final optimization
- [ ] Complexity: 3/10
- [ ] All documentation updated

---

## Rollback Plan

If issues occur:

```bash
# Rollback last phase
git revert HEAD

# Or reset to before consolidation
git reset --hard <commit-before-phase-X>

# Feature flag fallback (if implemented)
export USE_LEGACY_MODULES=true
```

---

## Documentation Updates

After completion:

- [ ] Update `docs/refactor-log.md`
- [ ] Update module documentation
- [ ] Update architecture diagrams
- [ ] Create PR with summary
- [ ] Update `CLAUDE.md` if needed

---

**Analysis files:**
1. `PROMPT_MODULE_OPTIMIZATION_ANALYSIS.md` - Detailed analysis
2. `PROMPT_MODULE_CONSOLIDATION_VISUAL.md` - Visual guide
3. `PROMPT_MODULE_OPTIMIZATION_SUMMARY.md` - Executive summary
4. `PROMPT_MODULE_ACTION_CHECKLIST.md` - This file (action steps)

**Ready to implement:** Phase 1 can start immediately (4 hours, low risk)
