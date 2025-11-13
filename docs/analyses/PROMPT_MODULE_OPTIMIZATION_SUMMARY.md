# Prompt Module Optimization - Executive Summary
**Date:** 2025-01-12

## TL;DR

**Consolidate 16 modules → 7 modules**
- **Token savings:** 1,250+ tokens (17% reduction, conservative estimate)
- **Line reduction:** 1,934 lines (44% reduction)
- **Complexity:** 7/10 → 3/10
- **Implementation:** 16-20 hours across 4 phases
- **Risk:** MEDIUM (requires testing, but phased approach minimizes risk)

---

## Quick Win Recommendations

### Phase 1: Critical Fixes (4 hours) - **DO FIRST**
Fix broken module and contradictions:
1. **TemplateModule validation** - Change `semantic_category` → `ontological_category`
2. **Kick-off contradiction** - Clarify noun vs. verb (resolve Semantic ↔ ErrorPrev conflict)
3. **Hardcoded STR/INT rules** - Convert to load from cache (US-202 compliance)

**Impact:** All modules functional, zero contradictions, US-202 compliant

---

## Key Findings

### Critical Issues (Must Fix)
1. **TemplateModule BROKEN** - Never runs due to validation checking non-existent field
2. **Major contradiction** - SemanticCategorisationModule instructs "proces waarbij", ErrorPreventionModule forbids it
3. **Hardcoded rules** - STR and INT modules bypass cache, defeating US-202 optimization
4. **645 lines duplication** - Identical `_format_rule()` method in 5 modules (14.5% of codebase)

### Consolidation Opportunities
1. **OutputSpec → Expertise** (merge) - Tightly coupled, minimal logic
2. **Template → Semantic** (merge) - Template broken, duplicates ESS-02 guidance
3. **7 rule modules → 1** (merge) - Identical structure, single source of truth
4. **ErrorPrev → Validation** (merge) - Inverse of rules, logically grouped

---

## Proposed Architecture (7 Modules)

| Module | Source | Lines | Tokens | Priority |
|--------|--------|-------|--------|----------|
| CoreInstructionsModule | Expertise + OutputSpec | 250 | 800 | 100 |
| ContextAwarenessModule | (unchanged) | 433 | 1,200 | 80 |
| CategoryGuidanceModule | Semantic + Template | 350 | 900 | 70 |
| GrammarModule | (simplified) | 150 | 400 | 70 |
| ValidationRulesModule | 7 rules + ErrorPrev | 800 | 2,200 | 65 |
| DefinitionTaskModule | (simplified) | 200 | 500 | 50 |
| MetricsModule | (optional) | 326 | 400 | 30 |
| **TOTAL** | | **2,509** | **6,400** | |

**vs. Current:** 4,443 lines, ~7,250 tokens

---

## Contradictions to Resolve

### 1. Kick-off Terms (CRITICAL)
**Problem:** SemanticCategorisationModule instructs "proces waarbij", ErrorPreventionModule forbids it

**Resolution:**
- **Clarify:** "proces" is a NOUN (handelingsnaamwoord), not a VERB
- **Forbidden:** VERBS like "is", "betekent", "omvat"
- **Allowed:** NOUNS like "proces", "activiteit", "handeling"
- **Update:** ErrorPreventionModule forbidden list to specify verbs only

### 2. Category Naming (MEDIUM)
**Problem:** 3 incompatible naming schemes (ontological_category, semantic_category, domain_contexts)

**Resolution:**
- **PRIMARY:** `ontological_category` (lowercase)
- **VALUES:** `proces`, `type`, `resultaat`, `exemplaar`
- **DEPRECATED:** `semantic_category`, `domain_contexts`

### 3. Hardcoded Rules (HIGH)
**Problem:** STR and INT modules bypass cached_toetsregel_manager

**Resolution:**
- Convert all rule modules to load from cache
- Single source of truth (JSON definitions)
- US-202 compliant (no duplicate loading)

---

## Token Savings Breakdown

| Source | Before | After | Savings |
|--------|--------|-------|---------|
| Module headers (9 eliminated) | 450 | 0 | -450 ✓ |
| Code duplication | 645 | 80 | -565 ✓ |
| OutputSpec merge | 400 | 200 | -200 ✓ |
| Template merge | 550 | 0 | -550 ✓ |
| 7 rule module consolidation | 2,100 | 900 | -1,200 ✓ |
| ErrorPrevention merge | 600 | 0 | -600 ✓ |
| Grammar simplification | 650 | 400 | -250 ✓ |
| DefinitionTask simplification | 600 | 500 | -100 ✓ |
| **TOTAL SAVINGS** | | | **-3,915** |

**Conservative estimate:** ~1,250 tokens saved (17% reduction)
**Stretch goal:** ~2,500 tokens saved (35% reduction with aggressive optimization)

---

## Implementation Phases

### Phase 1: Fix Critical Issues (4 hours)
- Fix TemplateModule validation
- Resolve kick-off contradiction
- Convert STR/INT to cache loading
- **Result:** All modules functional, zero contradictions

### Phase 2: Simple Merges (6 hours)
- Merge OutputSpec → Expertise
- Merge Template → Semantic
- Merge ErrorPrev → Validation (prep)
- **Result:** 16 → 10 modules, ~1,000 tokens saved

### Phase 3: Major Consolidation (8 hours)
- Create ValidationRulesModule (7→1)
- Remove 7 individual rule modules
- **Result:** 10 → 7 modules, ~2,500 tokens saved

### Phase 4: Refinement (2 hours)
- Simplify GrammarModule
- Simplify DefinitionTaskModule
- **Result:** Polish, final optimization

**Total:** 20 hours (~3 weeks part-time or 3 days full-time)

---

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| ValidationRules consolidation (7→1) | HIGH | Rule inventory, diff check, regression tests |
| Category naming unification | MEDIUM | Global search/replace, test all 4 categories |
| TemplateModule merge | MEDIUM | Export templates first, test each category |
| Simple merges (OutputSpec, ErrorPrev) | LOW | Unit tests, clean git history |

**Rollback plan:** Git revert, feature flag, parallel run (old + new)

---

## Success Metrics

### Token Efficiency
- **Baseline:** 7,250 tokens/prompt
- **Target:** <6,000 tokens/prompt (17% savings)
- **Stretch:** <5,000 tokens/prompt (31% savings)

### Code Quality
- **Baseline:** 16 modules, 4,443 lines, complexity 7/10
- **Target:** 7 modules, <2,600 lines, complexity 3/10
- **No code duplication** (DRY principle)

### Functionality
- **All 45 validation rules present**
- **Zero contradictions**
- **All tests passing**
- **Same or better definition quality**

---

## Next Steps

1. **Review** this analysis with team
2. **Approve** Phase 1 (critical fixes) to start immediately
3. **Create** feature branch: `feature/prompt-module-consolidation`
4. **Measure** baseline (current token usage, test coverage)
5. **Implement** Phase 1 (4 hours) - Fix critical issues
6. **Validate** improvements before proceeding to Phase 2
7. **Document** all changes in `docs/refactor-log.md`

---

## Files Created

1. `/docs/analyses/PROMPT_MODULE_OPTIMIZATION_ANALYSIS.md` - Detailed analysis (16 modules breakdown)
2. `/docs/analyses/PROMPT_MODULE_CONSOLIDATION_VISUAL.md` - Visual guide (diagrams, flow charts)
3. `/docs/analyses/PROMPT_MODULE_OPTIMIZATION_SUMMARY.md` - This executive summary (TL;DR)

---

**Analysis completed:** 2025-01-12
**Prepared by:** Claude Code (DefinitieAgent)
**Approval required:** Yes (>100 lines affected, architectural changes)
**UNIFIED compliance:** ✅ Follows APPROVAL LADDER, REFACTOR principles
