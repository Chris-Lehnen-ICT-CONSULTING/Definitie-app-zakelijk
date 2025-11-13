# Quick Reference: 16 Prompt Modules Analysis

**Full Analysis:** `/docs/analyses/DEF-151_PROMPT_MODULES_ANALYSIS.md`

---

## Module Health Dashboard

| # | Module | Status | Priority | Issues | Tokens | Recommendation |
|---|--------|--------|----------|--------|--------|-----------------|
| 1 | ExpertiseModule | ✅ GOOD | LOW | 1 MEDIUM | 150 | KEEP - refactor word detection util if reused |
| 2 | OutputSpecificationModule | ⚠️ FAIR | MEDIUM | 2 MEDIUM, 1 HIGH | 100 | MERGE with GrammarModule |
| 3 | GrammarModule | ⚠️ FAIR | HIGH | 5 issues (HIGH conflict on haakjes) | 140 | CONSOLIDATE - extract punctuation rules |
| 4 | ContextAwarenessModule | ⚠️ FAIR | MEDIUM | 6 issues (over-engineered) | 230 | SIMPLIFY - remove unused levels |
| 5 | SemanticCategorisationModule | ✅ GOOD | MEDIUM | 3 MEDIUM (verbose) | 180 | KEEP - condense guidance 40% |
| 6 | TemplateModule | 🔴 BROKEN | **CRITICAL** | **CRITICAL: never executes** | 120 | **REMOVE or COMPLETE REWRITE** |
| 7 | ARAI RulesModule | ✅ GOOD | LOW | 0 issues | 200 | KEEP |
| 8 | CON RulesModule | ✅ GOOD | LOW | 0 issues | 80 | KEEP |
| 9 | ESS RulesModule | ✅ GOOD | LOW | 0 issues | 150 | KEEP |
| 10 | StructureRulesModule | 🟡 POOR | **HIGH** | **HARDCODED rules** | 250 | **MIGRATE TO CACHE (150 token savings)** |
| 11 | IntegrityRulesModule | ✅ GOOD | LOW | 1 MEDIUM (dupes) | 200 | KEEP - extract _format_rule |
| 12 | SAM RulesModule | ✅ GOOD | LOW | 0 issues | 60 | KEEP |
| 13 | VER RulesModule | ✅ GOOD | LOW | 0 issues | 50 | KEEP |
| 14 | ErrorPreventionModule | 🔴 BROKEN | **CRITICAL** | **Forbids what SemanticCat recommends** | 200 | **FIX FORBIDDEN LIST (contradictions)** |
| 15 | MetricsModule | ⚠️ FAIR | LOW | 3 MEDIUM (unused) | 200 | SIMPLIFY or REMOVE |
| 16 | DefinitionTaskModule | ⚠️ FAIR | MEDIUM | 3 MEDIUM (duplicates) | 180 | CONSOLIDATE - remove duped hints |

---

## Critical Issues (Fix Immediately)

### Issue #1: Forbidden Patterns Contradict Recommended (SEVERITY: CRITICAL)

**Modules:** ErrorPreventionModule vs. SemanticCategorisationModule

**Problem:** ErrorPreventionModule forbids "proces waarbij", "handeling die" but SemanticCat RECOMMENDS them as kick-off terms.

**Fix Time:** 1 hour
**Token Savings:** 50 tokens

**Action:** Remove contradictory forbidden starters from ErrorPreventionModule OR add exception clause for semantic kick-offs.

---

### Issue #2: Haakjes Rule Contradicts Within Format Guidance (SEVERITY: CRITICAL)

**Modules:** OutputSpecificationModule vs. GrammarModule

**Problem:** OutputSpec says "Geen haakjes voor toelichtingen" but Grammar says "Plaats afkortingen direct na term tussen haakjes".

**Fix Time:** 1 hour
**Token Savings:** 10 tokens + clarification

**Action:** Clarify in OutputSpec that haakjes are forbidden EXCEPT for abbreviations (which are mandatory).

---

### Issue #3: Category Naming Triplication (SEVERITY: CRITICAL)

**Modules:** SemanticCategorisationModule vs. TemplateModule vs. DefinitionTaskModule

**Problem:**
- SemanticCat: "proces", "type", "resultaat", "exemplaar"
- TemplateModule: "Proces", "Object", "Actor", "Toestand", ...
- DefinitionTask: "soort", "exemplaar", "proces", "resultaat"

**Fix Time:** 2 hours
**Impact:** TemplateModule never executes because category names don't match

**Action:** Unify on single schema (recommend: lowercase ESS-02 names).

---

### Issue #4: TemplateModule Never Executes (SEVERITY: CRITICAL)

**Module:** TemplateModule

**Problem:** Validates for metadata key "semantic_category" that no upstream module sets. Always returns validation failure, module silently skipped.

**Fix Time:** 1 hour
**Token Savings:** 120 tokens if removed

**Action:** REMOVE module (SemanticCat already provides better examples) OR complete rewrite with proper integration.

---

### Issue #5: StructureRulesModule Hardcodes All Rules (SEVERITY: HIGH)

**Module:** StructureRulesModule

**Problem:** Hardcodes all 9 STR rules (63 lines) when other rule modules load from cache (1-2 lines).

**Fix Time:** 1 hour
**Token Savings:** 150 tokens

**Action:** Migrate to cached loading like ARAI/CON/ESS/SAM/VER modules.

---

### Issue #6: ErrorPreventionModule Forbidden List Too Aggressive (SEVERITY: HIGH)

**Module:** ErrorPreventionModule

**Problem:** Forbids patterns that SemanticCat explicitly recommends (lines 156-191):
- "proces waarbij"
- "handeling die"
- "vorm van", "type van", "soort van"

**Fix Time:** 1 hour
**Token Savings:** 50 tokens

**Action:** Remove contradictory items from forbidden list.

---

### Issue #7: EPIC-010 Context Migration Incomplete (SEVERITY: HIGH)

**Modules:** ContextAwarenessModule, DefinitionTaskModule, ErrorPreventionModule

**Problem:** Scattered fallback logic for legacy "domein" context field indicates incomplete migration to "organisatorisch/juridisch/wettelijk".

**Fix Time:** 2 hours
**Token Savings:** 40 tokens

**Action:** Complete EPIC-010 by removing all fallback logic and standardizing key names.

---

## Token Waste Summary

| Category | Tokens | Can Fix |
|----------|--------|---------|
| Hardcoded StructureRules | 150 | Use cache |
| Duplicate _format_rule (6 modules) | 60 | Extract to base |
| TemplateModule dead code | 120 | Remove |
| Duplicate afkorting rules | 50 | Consolidate |
| Duplicate ontological hints | 40 | Deduplicate |
| Unused shared state | 40 | Simplify |
| Verbose category guidance | 100 | Condense |
| Over-engineered ContextAware | 80 | Simplify |
| Unused confidence indicators | 30 | Remove |
| Extended forbidden list | 80 | Maybe keep |
| **TOTAL AVOIDABLE** | **750** | **YES** |

**Current Prompt:** ~7,500 tokens
**After Fixes:** ~6,750 tokens (10% reduction)

---

## Implementation Priorities

### Phase 1: CRITICAL FIXES (6 hours) - Week 1
- [ ] Fix forbidden vs. recommended contradiction (1h)
- [ ] Clarify haakjes rule (1h)
- [ ] Remove/fix TemplateModule (1h)
- [ ] Migrate StructureRules to cache (1h)
- [ ] Testing (2h)

**Token Impact:** -300 tokens

### Phase 2: DUPLICATION FIXES (8 hours) - Week 2
- [ ] Unify category naming (2h)
- [ ] Extract _format_rule method (2h)
- [ ] Complete EPIC-010 migration (2h)
- [ ] Testing (2h)

**Token Impact:** -200 tokens (cumulative: -500)

### Phase 3: REFACTORING (7 hours) - Week 3
- [ ] Simplify ContextAware (2h)
- [ ] Merge OutputSpec/Grammar (3h)
- [ ] Final testing (2h)

**Token Impact:** -250 tokens (cumulative: -750)

---

## Module Dependency Issues

### Undeclared Hard Dependencies

| Module | Depends On | Declared | Impact |
|--------|-----------|----------|--------|
| GrammarModule | ExpertiseModule (word_type) | NO | Hidden failure if expert runs first? |
| ErrorPreventionModule | ContextAwarenessModule | YES ✅ | Good |
| DefinitionTaskModule | SemanticCategorisationModule | NO | Hidden if semantic doesn't run |
| MetricsModule | Config attributes | NO | Silent failure if config missing |

**Action:** Explicitly declare dependencies in each module's `get_dependencies()` method.

---

## Contradiction Cross-Reference

### Contradiction Matrix

```
                        OutputSpec  Grammar  SemanticCat  ErrorPrev  Integrity
Haakjes usage              NO        YES         —            —         YES
Forbidden starters         —          —          NO           YES        —
Afkorting handling        YES         YES         —            —         YES
Ontological categories     —          —          YES          —          —
Context emphasis          YES          —          YES          YES        —
```

**Legend:**
- YES = module enforces this rule
- NO = module forbids this
- — = not relevant to module
- Red = conflict

---

## Before/After Example: StructureRulesModule

### BEFORE (250 tokens, hardcoded)
```python
def execute(self, context: ModuleContext) -> ModuleOutput:
    sections = []
    sections.append("### 🏗️ Structuur Regels (STR):")
    sections.extend(self._build_str01_rule())  # 54 lines...
    sections.extend(self._build_str02_rule())  # 54 lines...
    sections.extend(self._build_str03_rule())  # 54 lines...
    # ... 6 more builders...
    content = "\n".join(sections)
    return ModuleOutput(content=content, metadata={"rules_count": 9})

def _build_str01_rule(self) -> list[str]:
    """54 lines of hardcoded STR-01 content..."""
def _build_str02_rule(self) -> list[str]:
    """54 lines of hardcoded STR-02 content..."""
# ... 7 more methods...
```

### AFTER (100 tokens, cached)
```python
def execute(self, context: ModuleContext) -> ModuleOutput:
    sections = []
    sections.append("### 🏗️ Structuur Regels (STR):")

    from toetsregels.cached_manager import get_cached_toetsregel_manager
    manager = get_cached_toetsregel_manager()
    all_rules = manager.get_all_regels()
    str_rules = {k: v for k, v in all_rules.items() if k.startswith("STR-")}

    for regel_key, regel_data in sorted(str_rules.items()):
        sections.extend(self._format_rule(regel_key, regel_data))

    content = "\n".join(sections)
    return ModuleOutput(content=content, metadata={"rules_count": len(str_rules)})
```

**Savings:** 150 tokens (60% reduction)
**Maintenance:** Better (rules in config, not code)
**Consistency:** Better (same loading pattern as other rule modules)

---

## Module Interaction Sequence

```
PromptOrchestrator.build_prompt()
│
├─> Batch 1 (root modules, parallel):
│   ├─> ExpertiseModule         → sets shared["word_type"]
│   ├─> OutputSpecificationModule
│   ├─> GrammarModule           ← reads shared["word_type"]
│   ├─> ContextAwarenessModule  → sets shared[context keys]
│   └─> SemanticCategorisationModule → sets shared["ontological_category"]
│
├─> Batch 2 (dependent on batch 1, parallel):
│   ├─> TemplateModule          ❌ FAILS validation (missing metadata)
│   ├─> ARAI/CON/ESS/STR/INT/SAM/VER RulesModules
│   ├─> ErrorPreventionModule   ← reads shared[context keys]
│   ├─> MetricsModule
│   └─> DefinitionTaskModule    ← reads shared[ontological_category]
│
└─> Combine outputs in order
```

**Issues:**
1. TemplateModule silently fails (validation always returns False)
2. No error handling if shared state keys missing
3. GrammarModule soft dependency on word_type not enforced

---

## Configuration Review

### Key Configuration Points

**OutputSpecificationModule:**
- `default_min_chars` = 150
- `default_max_chars` = 350

**GrammarModule:**
- `include_examples` = True
- `strict_mode` = False

**ContextAwarenessModule:**
- `adaptive_formatting` = True
- `confidence_indicators` = True
- `include_abbreviations` = True

**ErrorPreventionModule:**
- `include_validation_matrix` = True
- `extended_forbidden_list` = True

**Action Items:**
1. Verify character limits are consistent across OutputSpec, Metrics, DefinitionTask
2. Consider token-saving config: set `extended_forbidden_list` = False by default
3. Make `confidence_indicators` = False by default (unused by downstream)

---

## Testing Checklist

### Critical Tests to Add

- [ ] Test: Forbidden patterns don't conflict with SemanticCat kick-offs
- [ ] Test: Haakjes rule consistent across all format guidance
- [ ] Test: All modules use same category naming schema
- [ ] Test: TemplateModule either removed or validation fixed
- [ ] Test: StructureRulesModule loads from cache
- [ ] Test: No forbidden patterns are recommended in other sections
- [ ] Test: Shared state keys consistent across modules
- [ ] Test: All rule modules load same format-rule logic
- [ ] Test: EPIC-010 context keys used consistently
- [ ] Test: Full prompt generation with all 16 modules

### LLM Behavior Tests

- [ ] Generate 10 definitions with same term; check consistency
- [ ] Verify definitions follow forbidden patterns list
- [ ] Check category application matches ESS-02 guidance
- [ ] Verify abbreviations have haakjes when present

---

## Quick Decision Matrix

### Should I keep this module?

**ExpertiseModule:**
- ✅ YES - Core role definition
- Recommendation: KEEP

**OutputSpecificationModule:**
- ⚠️ MAYBE - Can merge with GrammarModule
- Recommendation: MERGE

**GrammarModule:**
- ✅ YES - Core language rules
- Recommendation: CONSOLIDATE (extract punctuation to shared)

**ContextAwarenessModule:**
- ✅ YES - Context is crucial
- Recommendation: SIMPLIFY

**SemanticCategorisationModule:**
- ✅ YES - ESS-02 is core
- Recommendation: CONDENSE

**TemplateModule:**
- ❌ NO - Never executes, duplicates SemanticCat
- Recommendation: REMOVE

**ARAI/CON/ESS/SAM/VER RulesModules:**
- ✅ YES - Validation rules essential
- Recommendation: KEEP

**StructureRulesModule:**
- ✅ YES - Structural rules essential
- Recommendation: REFACTOR (migrate to cache)

**IntegrityRulesModule:**
- ✅ YES - Integrity rules essential
- Recommendation: KEEP

**ErrorPreventionModule:**
- ✅ YES - Error prevention essential
- Recommendation: FIX (remove contradictions)

**MetricsModule:**
- ⚠️ MAYBE - Informational, unused by downstream
- Recommendation: SIMPLIFY or REMOVE

**DefinitionTaskModule:**
- ✅ YES - Final instructions essential
- Recommendation: CONSOLIDATE (remove dupes)

---

## File Locations

| File | Type | Status | Action |
|------|------|--------|--------|
| `/src/services/prompts/modules/expertise_module.py` | module | ✅ GOOD | KEEP |
| `/src/services/prompts/modules/output_specification_module.py` | module | ⚠️ FAIR | MERGE |
| `/src/services/prompts/modules/grammar_module.py` | module | ⚠️ FAIR | CONSOLIDATE |
| `/src/services/prompts/modules/context_awareness_module.py` | module | ⚠️ FAIR | SIMPLIFY |
| `/src/services/prompts/modules/semantic_categorisation_module.py` | module | ✅ GOOD | CONDENSE |
| `/src/services/prompts/modules/template_module.py` | module | 🔴 BROKEN | REMOVE |
| `/src/services/prompts/modules/arai_rules_module.py` | module | ✅ GOOD | KEEP |
| `/src/services/prompts/modules/con_rules_module.py` | module | ✅ GOOD | KEEP |
| `/src/services/prompts/modules/ess_rules_module.py` | module | ✅ GOOD | KEEP |
| `/src/services/prompts/modules/structure_rules_module.py` | module | 🟡 POOR | REFACTOR |
| `/src/services/prompts/modules/integrity_rules_module.py` | module | ✅ GOOD | KEEP |
| `/src/services/prompts/modules/sam_rules_module.py` | module | ✅ GOOD | KEEP |
| `/src/services/prompts/modules/ver_rules_module.py` | module | ✅ GOOD | KEEP |
| `/src/services/prompts/modules/error_prevention_module.py` | module | 🔴 BROKEN | FIX |
| `/src/services/prompts/modules/metrics_module.py` | module | ⚠️ FAIR | REMOVE or SIMPLIFY |
| `/src/services/prompts/modules/definition_task_module.py` | module | ⚠️ FAIR | CONSOLIDATE |
| `/src/services/prompts/modules/prompt_orchestrator.py` | orchestrator | ✅ GOOD | KEEP |
| `/src/services/prompts/modules/base_module.py` | base | ✅ GOOD | KEEP |

---

## Next Steps

1. **Read Full Analysis:** `/docs/analyses/DEF-151_PROMPT_MODULES_ANALYSIS.md`
2. **Review Recommendations:** Check phase-by-phase implementation plan
3. **Start Phase 1:** Execute critical fixes immediately
4. **Track Progress:** Update checklist above as you complete items

---

**Quick Stats:**
- **Total Modules:** 16
- **Status:** 8 good, 5 fair, 2 broken, 1 poor
- **Critical Issues:** 7
- **Token Waste:** 750 tokens (10% of prompt)
- **Potential Savings:** 6,750 tokens target (8,000 → 7,250)
- **Implementation Time:** 21 hours (3 phases)

---

*Last Updated: 2025-11-11*
*Analysis Scope: Complete module audit + cross-module contradiction analysis*
*Status: Ready for implementation*
