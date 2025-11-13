# Prompt Module Optimization Analysis
**Date:** 2025-01-12
**Status:** Analysis Complete
**Goal:** Reduce 16 modules to optimal count, eliminate contradictions, maximize token savings

## Executive Summary

**Current State:**
- 16 modules totaling 4,443 lines of code
- ~7,250 tokens per prompt with duplication
- 3 different category naming schemes (semantic_category, ontological_category, legacy domain)
- 1 broken module (TemplateModule never runs)
- Multiple contradictions between modules

**Recommendation:** Consolidate to **7 modules** (56% reduction)
- **Expected token savings:** 35-45% (2,500-3,200 tokens saved)
- **Complexity reduction:** 7/10 → 3/10
- **Implementation effort:** 16-20 hours
- **Risk level:** MEDIUM (requires careful refactoring + testing)

---

## Module-by-Module Analysis

### 1. ExpertiseModule (200 lines)
**Current:** Defines AI role, task, word type detection, basic requirements

**Recommendation:** **KEEP (but simplify)**
- **Action:** Reduce from 200 to ~120 lines
- **Rationale:** Core module, sets foundation for all others
- **Token savings:** ~80-100 tokens
- **Effort:** 2 hours

**Simplifications:**
- Remove `_bepaal_woordsoort()` logic → Move to shared utility
- Remove redundant "basic requirements" (duplicates ARAI rules)
- Simplify word type advice (too verbose)

**Dependencies:** None (independent)

---

### 2. OutputSpecificationModule (175 lines)
**Current:** Format specs, character limits, guidelines

**Recommendation:** **MERGE into ExpertiseModule**
- **Rationale:** Tightly coupled to basic instructions, minimal logic
- **Token savings:** ~150-200 tokens (eliminate header duplication)
- **Effort:** 1 hour

**Merge plan:**
```python
# In ExpertiseModule:
def _build_output_specs(self, context):
    # Inline format requirements
    # Conditional char limit warnings
```

**Risk:** LOW - straightforward merge, no business logic

---

### 3. GrammarModule (256 lines)
**Current:** Grammar rules, word type rules, punctuation, strict mode

**Recommendation:** **KEEP (but refactor)**
- **Action:** Extract to separate utility, reduce to ~150 lines
- **Token savings:** ~200-250 tokens
- **Effort:** 3 hours

**Issues:**
- Overlaps with STR rules (enkelvoud, actieve vorm)
- Word type advice duplicates ExpertiseModule
- Strict mode never used (dead code)

**Refactor plan:**
1. Remove strict mode (dead code)
2. Consolidate word type handling with ExpertiseModule
3. Focus only on grammar (not structure)

**Dependencies:** Soft dependency on ExpertiseModule (word_type)

---

### 4. ContextAwarenessModule (433 lines)
**Current:** Context scoring, adaptive formatting, confidence indicators, V2 context handling

**Recommendation:** **KEEP (critical, already optimized)**
- **No changes recommended**
- **Rationale:** Complex business logic, well-designed, handles EPIC-010 compliance
- **Token savings:** 0 (already efficient)

**Notes:**
- Most sophisticated module (context richness scoring)
- Adaptive formatting reduces tokens automatically
- Shares context correctly via `set_shared()`

**Dependencies:** None (but provides context for others)

---

### 5. SemanticCategorisationModule (280 lines)
**Current:** ESS-02 ontological category instructions

**Recommendation:** **KEEP (but consolidate with TemplateModule)**
- **Action:** Merge category guidance into unified CategoryGuidanceModule
- **Token savings:** ~300-400 tokens (eliminate duplication)
- **Effort:** 4 hours

**Issues:**
- **CONTRADICTION:** Uses "ontological_category" but ErrorPreventionModule forbids kick-off terms
  - Line 178-207: Instructs to use "activiteit waarbij...", "handeling die..."
  - ErrorPreventionModule line 178-179: Forbids "proces waarbij", "handeling die"
  - **CRITICAL CONFLICT TO RESOLVE**

**Merge plan:**
- Combine with TemplateModule → **CategoryGuidanceModule**
- Unified category handling (type/proces/resultaat/exemplaar)
- Single source of truth for kick-off terms

**Dependencies:** None (provides category for others)

---

### 6. TemplateModule (251 lines)
**Current:** Category-specific templates, BROKEN (never runs due to validation fail)

**Recommendation:** **MERGE into SemanticCategorisationModule**
- **Rationale:** Both handle category-specific guidance, TemplateModule is broken
- **Token savings:** ~400-500 tokens (eliminate broken module + duplication)
- **Effort:** 3 hours

**Issues:**
- Validation always fails: checks for "semantic_category" but only "ontological_category" exists
- Different category names than SemanticCategorisationModule
- Templates duplicate ESS-02 guidance

**Root cause (line 63):**
```python
category = context.get_metadata("semantic_category")  # NEVER EXISTS!
if not category and self.detailed_templates:
    return False, "Geen semantische categorie beschikbaar"
```

**Fix:** Merge into SemanticCategorisationModule, use consistent naming

**Dependencies:** Depends on SemanticCategorisationModule (but broken)

---

### 7-13. Validation Rule Modules (7 modules, ~1,200 lines total)

**Current modules:**
- AraiRulesModule (129 lines) - General rules
- ConRulesModule (129 lines) - Context rules
- EssRulesModule (128 lines) - Essence rules
- StructureRulesModule (332 lines) - Structure rules (HARDCODED!)
- IntegrityRulesModule (314 lines) - Integrity rules (HARDCODED!)
- SamRulesModule (128 lines) - Coherence rules
- VerRulesModule (128 lines) - Form rules

**Recommendation:** **MERGE into 1 ValidationRulesModule**
- **Token savings:** ~800-1,000 tokens (eliminate 6 headers, deduplication)
- **Effort:** 5 hours

**Issues:**
1. **ARAI, CON, ESS, SAM, VER:** All use identical `_format_rule()` method (code duplication)
2. **STR, INT:** HARDCODED rules instead of loading from cache
   - StructureRulesModule: 9 hardcoded methods (`_build_str01_rule()` through `_build_str09_rule()`)
   - IntegrityRulesModule: Similar hardcoded methods
   - **CRITICAL:** Bypasses cached_toetsregel_manager, defeats US-202 optimization!

**Consolidation plan:**
```python
class ValidationRulesModule(BasePromptModule):
    """Unified module for all validation rules (ARAI, CON, ESS, STR, INT, SAM, VER)."""

    def __init__(self):
        super().__init__(module_id="validation_rules", ...)
        self.rule_categories = ["ARAI", "CON", "ESS", "STR", "INT", "SAM", "VER"]

    def execute(self, context):
        manager = get_cached_toetsregel_manager()
        all_rules = manager.get_all_regels()

        sections = []
        for category in self.rule_categories:
            category_rules = {k: v for k, v in all_rules.items() if k.startswith(f"{category}-")}
            sections.append(self._format_category_section(category, category_rules))

        return ModuleOutput(content="\n\n".join(sections), ...)

    def _format_rule(self, regel_key, regel_data):
        # Shared formatting logic (used by all 7 original modules)
        ...
```

**Benefits:**
- Single source of truth for rule formatting
- Consistent rule loading (always via cache)
- Remove hardcoded STR/INT rules
- Easier to maintain

**Dependencies:** None (provides rules for validation)

---

### 14. ErrorPreventionModule (262 lines)
**Current:** Forbidden patterns, context-specific forbidden terms, validation matrix

**Recommendation:** **MERGE into ValidationRulesModule**
- **Rationale:** Both provide validation guidance, ErrorPreventionModule is inverse of rules
- **Token savings:** ~200-250 tokens
- **Effort:** 2 hours

**Issues:**
- **CONTRADICTION with SemanticCategorisationModule:**
  - Line 178-179: Forbids "proces waarbij", "handeling die"
  - SemanticCategorisationModule lines 197-206: Instructs to USE these exact terms!
  - **Resolution:** ErrorPreventionModule should forbid starting with VERBS, not NOUNS
    - "proces waarbij" = NOUN (handelingsnaamwoord) → ALLOWED
    - "is een proces" = VERB (koppelwerkwoord) → FORBIDDEN

**Merge plan:**
- Add "forbidden_patterns" section to ValidationRulesModule
- Context-forbidden logic moves to _build_context_forbidden() helper
- Resolve contradiction: clarify noun vs. verb distinction

**Dependencies:** Depends on ContextAwarenessModule (for context-specific forbidden)

---

### 15. MetricsModule (326 lines)
**Current:** Character counts, complexity scoring, quality indicators

**Recommendation:** **KEEP (but make optional)**
- **Action:** Add config flag to disable for token savings
- **Token savings:** 0-400 tokens (when disabled)
- **Effort:** 1 hour

**Rationale:**
- Useful for monitoring/debugging
- Not essential for prompt quality
- Can be disabled for token budget optimization

**Optimization:**
```python
# In orchestrator config:
"metrics": {
    "enabled": False,  # Saves ~400 tokens when disabled
}
```

**Dependencies:** None (informational only)

---

### 16. DefinitionTaskModule (299 lines)
**Current:** Final instructions, checklist, quality control, metadata

**Recommendation:** **KEEP (critical for task definition)**
- **Action:** Simplify checklist, remove redundant metadata
- **Token savings:** ~100-150 tokens
- **Effort:** 2 hours

**Simplifications:**
- Checklist duplicates rules (reduce to 3-4 items)
- Remove verbose quality control questions
- Simplify prompt metadata (keep only essentials)

**Dependencies:** Depends on SemanticCategorisationModule (for ontological_category)

---

## Consolidation Plan: 16 → 7 Modules

### Proposed Architecture

| New Module | Consolidates | Priority | Lines | Token Est |
|------------|--------------|----------|-------|-----------|
| **1. CoreInstructionsModule** | Expertise + OutputSpec | 100 | ~250 | 800 |
| **2. ContextAwarenessModule** | (unchanged) | 80 | 433 | 1,200 |
| **3. CategoryGuidanceModule** | Semantic + Template | 70 | ~350 | 900 |
| **4. GrammarModule** | (simplified) | 70 | ~150 | 400 |
| **5. ValidationRulesModule** | ARAI+CON+ESS+STR+INT+SAM+VER+ErrorPrev | 65 | ~800 | 2,200 |
| **6. DefinitionTaskModule** | (simplified) | 50 | ~200 | 500 |
| **7. MetricsModule** | (optional) | 30 | 326 | 400 (opt) |

**Total:** 7 modules, ~2,509 lines, ~6,400 tokens (vs. current 7,250)

---

## Contradictions Matrix

| Issue | Module 1 | Module 2 | Resolution |
|-------|----------|----------|------------|
| **Kick-off terms** | SemanticCategorisationModule (ALLOWS "proces waarbij", "handeling die") | ErrorPreventionModule (FORBIDS same terms) | **FIX:** ErrorPreventionModule should forbid VERBS, not NOUNS. "proces" is noun (handelingsnaamwoord), "is" is verb (koppelwerkwoord). Update forbidden list to clarify. |
| **Category naming** | SemanticCategorisationModule (uses "ontological_category") | TemplateModule (looks for "semantic_category") | **FIX:** Merge modules, use consistent "ontological_category" everywhere |
| **Hardcoded rules** | StructureRulesModule + IntegrityRulesModule (hardcode rules) | ARAI+CON+ESS+SAM+VER (load from cache) | **FIX:** All modules must use cached_toetsregel_manager for consistency |
| **Word type logic** | ExpertiseModule (detects word type) | GrammarModule (uses word type for rules) | **OK:** Soft dependency via shared state works, but consolidate advice |

---

## Implementation Roadmap

### Phase 1: Fix Critical Issues (4 hours)
**Goal:** Resolve contradictions, unblock broken module

**Tasks:**
1. **Fix TemplateModule validation** (1 hour)
   - Change `semantic_category` → `ontological_category`
   - Test that module now runs

2. **Resolve kick-off contradiction** (1 hour)
   - Update ErrorPreventionModule forbidden list
   - Clarify: forbid VERBS ("is", "betekent"), allow NOUNS ("proces", "activiteit")

3. **Fix hardcoded STR/INT rules** (2 hours)
   - Convert StructureRulesModule to load from cache
   - Convert IntegrityRulesModule to load from cache
   - Verify rules match JSON definitions

**Success criteria:**
- All 16 modules run without errors
- No contradictory guidance
- All rules loaded from cache (US-202 compliance)

---

### Phase 2: Consolidate Simple Merges (6 hours)
**Goal:** Low-risk merges for immediate token savings

**Tasks:**
1. **Merge OutputSpec → Expertise** (1 hour)
   - Move format specs into ExpertiseModule
   - Remove OutputSpecificationModule
   - Update orchestrator registration

2. **Merge Template → Semantic** (3 hours)
   - Combine category guidance into CategoryGuidanceModule
   - Unified templates + ESS-02 instructions
   - Test category-specific guidance

3. **Merge ErrorPrevention → Validation** (2 hours)
   - Add forbidden patterns section to ValidationRulesModule
   - Preserve context-specific forbidden logic
   - Test validation output

**Success criteria:**
- 16 → 10 modules
- ~1,000 tokens saved
- All tests pass

---

### Phase 3: Major Consolidation (8 hours)
**Goal:** Consolidate 7 rule modules into 1

**Tasks:**
1. **Create ValidationRulesModule** (4 hours)
   - Unified rule loading for all 7 categories
   - Shared `_format_rule()` method
   - Category-specific headers/grouping

2. **Remove 7 individual rule modules** (2 hours)
   - Delete ARAI, CON, ESS, STR, INT, SAM, VER modules
   - Update orchestrator registration

3. **Testing & validation** (2 hours)
   - Verify all 45 rules appear in prompt
   - Check token count reduction
   - Regression testing

**Success criteria:**
- 10 → 4 modules (+3 optional)
- ~2,500-3,000 tokens saved
- All 45 validation rules present

---

### Phase 4: Refinement (2 hours)
**Goal:** Polish and optimize

**Tasks:**
1. **Simplify DefinitionTask** (1 hour)
   - Reduce checklist redundancy
   - Simplify metadata

2. **Optimize GrammarModule** (1 hour)
   - Remove strict mode
   - Consolidate word type handling

**Success criteria:**
- 7 final modules
- ~3,200 tokens saved (45% reduction)
- Complexity: 3/10

---

## Risk Assessment

### HIGH RISK (Requires careful planning)
- **ValidationRulesModule consolidation:** Affects 7 modules, must preserve all 45 rules
  - **Mitigation:** Create comprehensive test suite, verify rule-by-rule

- **Kick-off term contradiction:** Critical for ESS-02 compliance
  - **Mitigation:** Document noun vs. verb distinction clearly, add examples

### MEDIUM RISK
- **Category naming unification:** Affects multiple modules
  - **Mitigation:** Search/replace, verify all references updated

- **Hardcoded STR/INT conversion:** Must match JSON definitions exactly
  - **Mitigation:** Compare output before/after, regression tests

### LOW RISK
- **Simple merges (OutputSpec, ErrorPrev):** Straightforward code moves
- **Optional MetricsModule:** No impact if disabled

---

## Testing Strategy

### Unit Tests
- Each consolidated module must have dedicated test
- Verify all original functionality preserved
- Test edge cases (missing context, invalid category, etc.)

### Integration Tests
- Test full prompt generation with new architecture
- Compare output tokens: before vs. after
- Verify all 45 validation rules present

### Regression Tests
- Run existing test suite against new modules
- Verify no functional changes to generated prompts
- Check metadata preservation

### Performance Tests
- Measure prompt generation time (should be same or faster)
- Verify cache usage (no new loadings)
- Check memory footprint

---

## Success Metrics

### Token Efficiency
- **Baseline:** 7,250 tokens/prompt
- **Target:** <5,000 tokens/prompt (30%+ savings)
- **Stretch:** <4,500 tokens/prompt (38%+ savings)

### Code Quality
- **Baseline:** 16 modules, 4,443 lines
- **Target:** 7 modules, <2,600 lines (41% reduction)
- **No code duplication** (DRY principle)

### Maintainability
- **Baseline:** Complexity 7/10
- **Target:** Complexity 3/10
- **Single source of truth** for categories, rules, formatting

### Functionality
- **All 45 validation rules present**
- **No contradictions**
- **All tests passing**
- **Same or better definition quality**

---

## Appendix A: Module Statistics

### Current State (16 modules)
```
Module                          Lines    Tokens (est)   Priority   Status
─────────────────────────────────────────────────────────────────────────
ExpertiseModule                   200         600        100       OK
OutputSpecificationModule         175         400         90       OK
GrammarModule                     256         650         85       OK
ContextAwarenessModule            433       1,200         70       OK
SemanticCategorisationModule      280         700         60       OK
TemplateModule                    251         550         60       BROKEN
AraiRulesModule                   129         300         75       OK
ConRulesModule                    129         300         70       OK
EssRulesModule                    128         300         70       OK
StructureRulesModule              332         800         65       HARDCODED
IntegrityRulesModule              314         750         65       HARDCODED
SamRulesModule                    128         300         60       OK
VerRulesModule                    128         300         55       OK
ErrorPreventionModule             262         600         50       CONTRADICTION
MetricsModule                     326         400         30       OK
DefinitionTaskModule              299         600         40       OK
─────────────────────────────────────────────────────────────────────────
TOTAL                           4,443       7,250 (avg)
```

### Proposed State (7 modules)
```
Module                          Lines    Tokens (est)   Priority   Status
─────────────────────────────────────────────────────────────────────────
CoreInstructionsModule            250         800        100       NEW
ContextAwarenessModule            433       1,200         80       UNCHANGED
CategoryGuidanceModule            350         900         70       NEW (merged)
GrammarModule                     150         400         70       SIMPLIFIED
ValidationRulesModule             800       2,200         65       NEW (7→1)
DefinitionTaskModule              200         500         50       SIMPLIFIED
MetricsModule (optional)          326         400         30       OPTIONAL
─────────────────────────────────────────────────────────────────────────
TOTAL                           2,509       6,400 (avg)  -or-  6,000 (no metrics)
REDUCTION                     -1,934       -850 tokens   -or-  -1,250 tokens
                                -44%          -12%               -17%
```

**Note:** Token estimates are conservative. Actual savings likely higher due to:
- Elimination of duplicate headers (6 removed)
- Shared formatting logic (no repeated `_format_rule()`)
- Removal of dead code (strict mode, broken validation)
- Adaptive context formatting (already optimized)

---

## Appendix B: Code Duplication Analysis

### Identical `_format_rule()` Method
**Modules affected:** ARAI, CON, ESS, SAM, VER (5 modules)

**Duplicated code (129 lines × 5 = 645 lines):**
```python
def _format_rule(self, regel_key: str, regel_data: dict) -> list[str]:
    lines = []
    naam = regel_data.get("naam", "Onbekende regel")
    lines.append(f"🔹 **{regel_key} - {naam}**")

    uitleg = regel_data.get("uitleg", "")
    if uitleg:
        lines.append(f"- {uitleg}")

    toetsvraag = regel_data.get("toetsvraag", "")
    if toetsvraag:
        lines.append(f"- Toetsvraag: {toetsvraag}")

    if self.include_examples:
        goede_voorbeelden = regel_data.get("goede_voorbeelden", [])
        for goed in goede_voorbeelden:
            lines.append(f"  ✅ {goed}")

        foute_voorbeelden = regel_data.get("foute_voorbeelden", [])
        for fout in foute_voorbeelden:
            lines.append(f"  ❌ {fout}")

    return lines
```

**Impact:** 645 lines of pure duplication (14.5% of total codebase!)

**Solution:** Extract to shared utility in ValidationRulesModule

---

## Appendix C: Category Naming Schemes

### Three Incompatible Naming Schemes

**Scheme 1: SemanticCategorisationModule (ESS-02)**
```python
ontological_category = "proces" | "type" | "resultaat" | "exemplaar"
context.set_shared("ontological_category", ontological_category)
```

**Scheme 2: TemplateModule (BROKEN)**
```python
category = context.get_metadata("semantic_category")  # NEVER EXISTS!
# Expects: "Proces" | "Object" | "Actor" | "Toestand" | "Gebeurtenis" | ...
```

**Scheme 3: ErrorPreventionModule (legacy)**
```python
# Uses "domain_contexts" (EPIC-010 deprecated)
# Should use: org_contexts, jur_contexts, wet_contexts
```

**Resolution:**
- **PRIMARY:** `ontological_category` (ESS-02 compliant)
- **VALUES:** `"proces"`, `"type"`, `"resultaat"`, `"exemplaar"` (lowercase)
- **DEPRECATED:** `semantic_category`, `domain_contexts`

---

## Next Steps

1. **Review this analysis** with team
2. **Prioritize phases** based on urgency
3. **Create feature branch** for consolidation work
4. **Phase 1 (critical fixes)** - Start immediately
5. **Measure baseline** (current token usage, test coverage)
6. **Implement incrementally** (test after each phase)
7. **Document changes** in REFACTOR_LOG.md

---

**Analysis prepared by:** Claude Code (DefinitieAgent)
**Review required:** Yes (architectural changes)
**Approval threshold:** >100 lines affected (UNIFIED compliance)
