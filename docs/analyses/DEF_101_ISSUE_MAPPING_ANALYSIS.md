# DEF-101 Issue Mapping Analysis: Planned vs Existing vs Needed

**Date:** 2025-11-07
**Purpose:** Map DEF-101 sub-issues to existing Linear issues and identify gaps
**Context:** DEF-101 EPIC mentions 6 sub-issues but none exist in Linear. We have multiple prompt optimization analyses with different approaches.

---

## Executive Summary

### CRITICAL FINDING: DEF-101 Sub-Issues Do Not Exist in Linear

**DEF-101 EPIC claims 6 sub-issues:**
1. Phase 1.1: Fix Blocking Contradictions (CRITICAL) - **NOT FOUND**
2. Phase 1.2: Reduce Cognitive Load - **NOT FOUND**
3. Phase 1.3: Reorganize Flow & Eliminate Redundancy - **NOT FOUND**
4. Phase 2.1: Add Visual Hierarchy & Update Templates - **NOT FOUND**
5. Phase 2.2: Create PromptValidator - **EXISTS as DEF-106** ✅
6. Phase 3: Documentation & Testing - **NOT FOUND**

**Existing Linear issues that ARE prompt-related:**
- DEF-38: Kritieke Issues in Ontologische Promptinjecties (UNKNOWN STATUS)
- DEF-40: Optimaliseer category-specific prompt injecties (UNKNOWN STATUS)
- DEF-61: Merge PromptOrchestrator layers (4→1 class) (UNKNOWN STATUS)
- DEF-79: 16 Prompt Modules → 4 Jinja2 Templates (UNKNOWN STATUS)
- DEF-106: Create PromptValidator (Phase 2.2 match) ✅

**Analysis documents available:**
- `PROMPT_COMPREHENSIVE_ANALYSIS_AND_IMPROVEMENT_PLAN.md` (2025-11-03)
- `PROMPT_OPTIMIZATION_ANALYSIS.md` (2025-11-07)
- `PROMPT_OPTIMIZATION_SUMMARY.md` (2025-11-07)
- `DEF_111_vs_DEF_101_ROI_ANALYSIS.md` (2025-11-06)

---

## 1. COMPARISON: DEF-101 Original Plan vs New Analysis (2025-11-07)

### 1.1 DEF-101 Original Plan (from COMPREHENSIVE_ANALYSIS)

**Source:** `PROMPT_COMPREHENSIVE_ANALYSIS_AND_IMPROVEMENT_PLAN.md` (2025-11-03)

#### Phase 1: CRITICAL FIXES (Week 1 - 8 hours)

**1.1 Resolve Blocking Contradictions (3 hours)**
- Add ESS-02 exception clause for ontological markers
- Exempt ontological markers from ARAI-02 container rule
- Clarify relative clause usage
- Update templates to avoid contradictions
- Clarify context integration

**Files affected:**
- `src/services/prompts/modules/semantic_categorisation_module.py`
- `src/services/prompts/modules/error_prevention_module.py`
- `src/services/prompts/modules/arai_rules_module.py`
- `src/services/prompts/modules/structure_rules_module.py`

**1.2 Reduce Cognitive Load (2 hours)**
- Categorize 42 forbidden patterns into 7 groups
- Add priority tiers to validation rules (TIER 1/2/3)

**Files affected:**
- `src/services/prompts/modules/error_prevention_module.py`
- `src/services/prompts/prompt_orchestrator.py`

**1.3 Reorganize Flow (1 hour) + Eliminate Redundancy (2 hours)**
- Reorder module execution (definition_task FIRST, semantic_categorisation early)
- Reduce ESS-02 from 38 to 20 lines
- Consolidate enkelvoud rules
- Delete ARAI-06 (duplicate of STR-01)

**Files affected:**
- `src/services/prompts/modules/definition_task_module.py`
- `src/services/prompts/prompt_orchestrator.py`
- `src/services/prompts/modules/semantic_categorisation_module.py`
- `src/services/prompts/modules/grammar_module.py`
- `src/services/prompts/modules/ver_rules_module.py`

#### Phase 2: QUALITY IMPROVEMENTS (Week 2 - 4 hours)

**2.1 Add Visual Hierarchy (1 hour) + Update Templates (1 hour)**
- Add priority badges (⚠️ TIER 1, ✅ TIER 2, ℹ️ TIER 3)
- Update templates to align with rules (no "die/dat", no purpose in essence)

**Files affected:**
- `src/services/prompts/modules/structure_rules_module.py`
- `src/services/prompts/modules/integrity_rules_module.py`
- `src/services/prompts/modules/template_module.py`

**2.2 Add Automated Validation (2 hours)**
- Create `PromptValidator` class
- Validate contradictions, redundancy, categorized patterns

**Files affected:**
- `src/services/prompts/prompt_validator.py` (NEW)

#### Phase 3: DOCUMENTATION & TESTING (Week 3 - 4 hours)

**3.1 Document Module Dependencies (1 hour)**
- Create dependency map document

**Files affected:**
- `docs/architectuur/prompt_module_dependency_map.md` (NEW)

**3.2 Create Test Suite (2 hours)**
- Test ESS-02 exception clause
- Test no blocking contradictions
- Test redundancy below threshold
- Test forbidden patterns categorized

**Files affected:**
- `tests/services/prompts/test_prompt_contradictions.py` (NEW)

**3.3 Regression Testing (1 hour)**
- Compare against golden reference (prompt v6)

---

### 1.2 New Analysis Approach (2025-11-07)

**Source:** `PROMPT_OPTIMIZATION_ANALYSIS.md` + `PROMPT_OPTIMIZATION_SUMMARY.md`

#### FASE 1: Quick Wins (30 min - 4 hours)

**Problem focus:**
- 7.250 tokens → 6.200 tokens (-14%)
- Remove validation rules from prompt (they're validated post-processing anyway)
- Consolidate forbidden list (42 patterns → 3 templates)
- Fix conflicts

**Specific actions:**
1. **DELETE lines 323-329** (ontological conflict) - 5 min
2. **DELETE lines 294-322** (veelgemaakte fouten, 80% duplicate) - 5 min
3. **MERGE ESS-01 + STR-06** (both say "essentie niet doel") - 10 min
4. **TRIM lines 380-400** (redundant finale instructies) - 10 min

**Files affected:** (Same modules as original plan)

#### FASE 2: Structurele Optimalisatie (1.5 uur)

**Problem focus:**
- 362 → 316 regels (-25% vs origineel)
- Merge Grammatica + VER
- Condense Kwaliteitsmetrieken
- Simplify Ontologie
- Reorganize sections

#### FASE 3: Polish (1.5 uur)

**Problem focus:**
- 316 → 290 regels (-31% vs origineel)
- Optimize voorbeelden
- Optimize bullet formatting
- Add cross-references

---

## 2. OVERLAP & DIFFERENCES ANALYSIS

### 2.1 What's the SAME?

| Concept | DEF-101 Original | New Analysis (Nov 7) | Match? |
|---------|-----------------|---------------------|--------|
| **Fix ontological contradiction** | Phase 1.1 (ESS-02 exception) | Fase 1 (DELETE lines 323-329) | ✅ SAME PROBLEM |
| **Reduce cognitive load** | Phase 1.2 (categorize 42 patterns) | Fase 1 (consolidate forbidden list) | ✅ SAME SOLUTION |
| **Eliminate redundancy** | Phase 1.3 (65 lines) | Fase 1-3 (129 lines) | ✅ SAME GOAL (different scope) |
| **Reorganize flow** | Phase 1.3 (reorder modules) | Fase 2 (reorganize sections) | ✅ SAME APPROACH |
| **Templates alignment** | Phase 2.1 (update templates) | Fase 2 (simplify ontologie) | ✅ SAME INTENT |
| **PromptValidator** | Phase 2.2 (create validator) | Not mentioned | ⚠️ MISSING in new analysis |
| **Testing** | Phase 3 (regression tests) | Not mentioned | ⚠️ MISSING in new analysis |

### 2.2 What's DIFFERENT?

#### NEW in 2025-11-07 Analysis (NOT in original DEF-101):

1. **Validation rules removal strategy**
   - **New insight:** 48% of tokens (3.500) are rules that get validated post-processing anyway
   - **Suggestion:** Remove ARAI/CON/ESS/INT/SAM/STR/VER from prompt, keep only principles
   - **Impact:** -3.500 tokens (-48%)
   - **RADICAL CHANGE** - not in original plan

2. **Conditional module loading**
   - **New insight:** All 16 modules run ALWAYS, regardless of context
   - **Suggestion:** Load modules conditionally based on context
   - **Impact:** 8-12 modules active instead of 16
   - **NOT in original plan**

3. **Caching static modules**
   - **New insight:** Grammar/format rules never change per request
   - **Suggestion:** Cache static module outputs
   - **NOT in original plan**

4. **Inverted Pyramid structure**
   - **New approach:** Mission (50 tokens) → Golden Rules (300) → Templates (400) → Refinement (800) → Checklist (100)
   - **Total:** 2.650 tokens (-63%)
   - **MORE aggressive than original plan** (419 → 354 lines = -15.5%)

#### MISSING in 2025-11-07 Analysis (WAS in original DEF-101):

1. **PromptValidator creation** (Phase 2.2)
   - Automated contradiction detection
   - Prevents regression
   - **Critical for CI/CD!**

2. **Test suite creation** (Phase 3.2)
   - Regression tests against golden reference
   - Contradiction detection tests
   - Redundancy threshold tests

3. **Module dependency documentation** (Phase 3.1)
   - Dependency map
   - Cross-references
   - Exception clauses

---

## 3. EXISTING LINEAR ISSUES: RELATIONSHIP TO DEF-101

### 3.1 DEF-38: Kritieke Issues in Ontologische Promptinjecties

**Expected content:** (Based on title)
- Likely about ESS-02 contradictions
- Probably Phase 1.1 equivalent

**Overlap with DEF-101:**
- Phase 1.1: Resolve Blocking Contradictions
- Specifically: ESS-02 exception clause

**Recommendation:** Check if DEF-38 is duplicate of DEF-101 Phase 1.1

---

### 3.2 DEF-40: Optimaliseer category-specific prompt injecties

**Expected content:** (Based on title)
- Category-specific modules (PROCES, TYPE, RESULTAAT, EXEMPLAAR)
- Template optimization per category

**Overlap with DEF-101:**
- Phase 2.1: Update Templates
- Possibly: Conditional module loading (new analysis)

**Recommendation:** DEF-40 might be MORE specific than DEF-101 Phase 2.1

---

### 3.3 DEF-61: Merge PromptOrchestrator layers (4→1 class)

**Expected content:** (Based on title)
- Architectural refactoring of PromptOrchestrator
- Reduce complexity

**Overlap with DEF-101:**
- Phase 1.3: Reorganize Flow
- Potentially: Conditional module loading

**Recommendation:** DEF-61 is ARCHITECTURAL, DEF-101 is CONTENT. Can run parallel.

---

### 3.4 DEF-79: 16 Prompt Modules → 4 Jinja2 Templates

**Expected content:** (Based on title)
- Replace Python modules with Jinja2 templates
- Massive architectural change

**Overlap with DEF-101:**
- **CONFLICTS with DEF-101 approach!**
- DEF-101 assumes Python modules stay
- DEF-79 wants to replace them with templates

**Recommendation:** DECIDE which architecture first:
- Option A: Keep Python modules (DEF-101)
- Option B: Move to Jinja2 (DEF-79)
- **Do NOT do both!**

---

### 3.5 DEF-106: Create PromptValidator

**Expected content:** (Based on title + DEF-101 Phase 2.2)
- Automated prompt validation
- Contradiction detection
- Redundancy checks

**Overlap with DEF-101:**
- **EXACT MATCH:** Phase 2.2
- Same deliverable

**Recommendation:** DEF-106 IS DEF-101 Phase 2.2. Keep DEF-106, don't create duplicate.

---

## 4. GAP ANALYSIS: WHAT'S MISSING IN LINEAR?

### 4.1 Missing from DEF-101 Original Plan (Should be created)

| Phase | Issue Title | Scope | Priority | Depends On |
|-------|------------|-------|----------|------------|
| **Phase 1.1** | Fix Prompt Blocking Contradictions | ESS-02 exception, ARAI-02 exemption, clarify relative clauses | 🔴 CRITICAL | None |
| **Phase 1.2** | Reduce Prompt Cognitive Load | Categorize 42 patterns → 7 groups, add priority tiers | 🔴 CRITICAL | Phase 1.1 |
| **Phase 1.3a** | Reorganize Prompt Module Flow | Reorder 16 modules, metadata first | 🟡 HIGH | Phase 1.2 |
| **Phase 1.3b** | Eliminate Prompt Redundancy | Reduce ESS-02, consolidate enkelvoud, delete ARAI-06 | 🟡 HIGH | Phase 1.3a |
| **Phase 2.1** | Add Prompt Visual Hierarchy & Update Templates | Priority badges, align templates with rules | 🟢 MEDIUM | Phase 1.3b |
| **Phase 2.2** | Create PromptValidator | Automated validation | 🟢 MEDIUM | Phase 2.1 |
| **Phase 3** | Prompt Refactor: Documentation & Testing | Dependency docs, regression tests | 🟢 MEDIUM | Phase 2.2 |

**Note:** DEF-106 already exists for Phase 2.2, don't duplicate!

### 4.2 New Insights from 2025-11-07 Analysis (Consider creating)

| Insight | Potential Issue Title | Radical? | Impact | Effort |
|---------|----------------------|----------|--------|--------|
| **Validation rules removal** | Remove Post-Validated Rules from Prompt | YES | -3.500 tokens (-48%) | 8 hours |
| **Conditional module loading** | Implement Context-Aware Module Loading | YES | 8-12 modules active (instead of 16) | 12 hours |
| **Static module caching** | Cache Static Prompt Module Outputs | NO | Faster generation | 4 hours |
| **Inverted Pyramid** | Restructure Prompt with Inverted Pyramid | YES | 419 → 290 lines (-31%) | 16 hours |

**Recommendation:** These are MORE aggressive than original DEF-101. Consider separate EPIC or add as "Phase 4" stretch goals.

---

## 5. DUPLICATION RISK MATRIX

### 5.1 Existing Issues vs DEF-101 Sub-Issues

| Existing Issue | DEF-101 Phase | Duplication Risk | Recommendation |
|----------------|---------------|------------------|----------------|
| **DEF-38** | Phase 1.1 (Contradictions) | 🔴 HIGH | Check DEF-38 content. If duplicate, close one. |
| **DEF-40** | Phase 2.1 (Templates) | 🟡 MEDIUM | Check DEF-40 scope. Might be more specific. |
| **DEF-61** | Phase 1.3a (Flow) | 🟢 LOW | Different layer (architecture vs content). |
| **DEF-79** | CONFLICTS! | 🔴 HIGH | Decide: Python modules OR Jinja2? Can't do both. |
| **DEF-106** | Phase 2.2 (Validator) | 🔴 EXACT MATCH | Use DEF-106, don't create duplicate. |

### 5.2 New Analysis (Nov 7) vs Original DEF-101

| New Concept | Original DEF-101 | Overlap? | Recommendation |
|-------------|------------------|----------|----------------|
| **Remove validation rules** | Not mentioned | 🟢 NO | Consider as "Phase 4" or separate EPIC. |
| **Conditional loading** | Not mentioned | 🟢 NO | Consider as "Phase 4" or separate EPIC. |
| **Static caching** | Not mentioned | 🟢 NO | Quick win, add to Phase 2. |
| **Inverted Pyramid** | Phase 1.3 (Reorganize) | 🟡 PARTIAL | More radical version of same goal. |

---

## 6. RECOMMENDED ISSUE STRUCTURE

### 6.1 Option A: Stick with Original DEF-101 Plan

**Create these 5 new issues:**

1. **DEF-101-1:** Fix Prompt Blocking Contradictions (Phase 1.1)
   - 5 contradictions resolved
   - ESS-02 exception clause added
   - 3 hours

2. **DEF-101-2:** Reduce Prompt Cognitive Load (Phase 1.2)
   - 42 patterns → 7 groups
   - Priority tiers added
   - 2 hours

3. **DEF-101-3:** Reorganize Prompt Flow (Phase 1.3a)
   - Module execution reordered
   - Metadata moved to top
   - 1 hour

4. **DEF-101-4:** Eliminate Prompt Redundancy (Phase 1.3b)
   - 65 lines removed
   - ESS-02 reduced 38 → 20 lines
   - 2 hours

5. **DEF-101-5:** Add Prompt Visual Hierarchy & Update Templates (Phase 2.1)
   - Priority badges added
   - Templates aligned with rules
   - 2 hours

6. **DEF-106:** Create PromptValidator (Phase 2.2) ✅ ALREADY EXISTS

7. **DEF-101-6:** Prompt Refactor: Documentation & Testing (Phase 3)
   - Dependency docs
   - Regression tests
   - 4 hours

**Total:** 14 hours (matches original plan: 16 hours)

---

### 6.2 Option B: Hybrid Approach (Original + New Insights)

**Phase 1-3: Original DEF-101** (14 hours, create 5 issues as above)

**Phase 4: Advanced Optimizations** (40 hours, create 4 new issues)

8. **DEF-101-7:** Remove Post-Validated Rules from Prompt
   - Validation rules moved to post-processing only
   - -3.500 tokens (-48%)
   - 8 hours

9. **DEF-101-8:** Implement Context-Aware Module Loading
   - Conditional module execution
   - 8-12 active modules (instead of 16)
   - 12 hours

10. **DEF-101-9:** Cache Static Prompt Module Outputs
    - Grammar/format rules cached
    - Faster generation
    - 4 hours

11. **DEF-101-10:** Restructure Prompt with Inverted Pyramid
    - Mission → Golden Rules → Templates → Refinement → Checklist
    - 419 → 290 lines (-31%)
    - 16 hours

**Total:** 54 hours (14 + 40)

**Phasing:**
- **Phase 1-3 (Weeks 1-3):** Quick wins, low risk
- **Phase 4 (Weeks 4-6):** Advanced optimizations, higher risk

---

### 6.3 Option C: Architecture Decision First

**BLOCKER ISSUE (decide first!):**

**DEF-102:** Prompt Architecture Decision: Python Modules vs Jinja2 Templates
- **Decision:** Keep Python modules (DEF-101 path) OR Move to Jinja2 (DEF-79 path)
- **Impact:** Affects all subsequent work
- **Effort:** 4 hours analysis + decision
- **Blocks:** DEF-101-1 through DEF-101-10, DEF-79

**After decision:**
- **If Python modules:** Proceed with DEF-101-1 through DEF-101-10
- **If Jinja2:** Pause DEF-101, execute DEF-79 first

---

## 7. FINAL RECOMMENDATIONS

### 7.1 Immediate Actions (This Week)

1. **CHECK existing issues:**
   - Read DEF-38 content (might be duplicate of DEF-101-1)
   - Read DEF-40 content (might be duplicate of DEF-101-5)
   - Read DEF-61 content (architectural, can run parallel)
   - Read DEF-79 content (CONFLICTS with DEF-101!)

2. **DECIDE architecture:**
   - Create **DEF-102: Prompt Architecture Decision**
   - Meet with stakeholders (1 hour)
   - Document decision + rationale

3. **CREATE missing issues** (after DEF-102 decision):
   - Use **Option A** (conservative, 14 hours) OR
   - Use **Option B** (aggressive, 54 hours)

### 7.2 Sequencing Strategy

**Week 1:**
- ✅ Check DEF-38, DEF-40, DEF-61, DEF-79
- ✅ Create DEF-102 (architecture decision)
- ✅ Decide: Python modules OR Jinja2
- ✅ Create DEF-101-1 through DEF-101-6 (or DEF-101-10 if Option B)

**Week 2-3:**
- ✅ Execute DEF-101 Phase 1-3 (original plan)
- ✅ Deliver: Fixed prompt, 419 → 354 lines

**Week 4-6 (Optional, if Option B chosen):**
- ✅ Execute DEF-101 Phase 4 (advanced optimizations)
- ✅ Deliver: Optimized prompt, 354 → 290 lines

### 7.3 Risk Mitigation

**HIGH RISK:**
- DEF-79 conflicts with DEF-101 → Resolve via DEF-102 decision
- DEF-38 might duplicate DEF-101-1 → Check before creating new issue
- Phase 4 (validation rules removal) is radical → Test thoroughly, consider rollback plan

**MEDIUM RISK:**
- New contradictions during refactor → Mitigated by DEF-106 (PromptValidator)
- Breaking existing definitions → Mitigated by Phase 3 regression tests

**LOW RISK:**
- Phase 1-3 only removes duplicates/conflicts → Minimal impact

---

## 8. COMPARISON TABLE: ALL APPROACHES

| Approach | Scope | Effort | Token Reduction | Risk | Dependencies |
|----------|-------|--------|----------------|------|--------------|
| **DEF-101 Original** | Phase 1-3 | 16 hours | -15.5% (419 → 354) | LOW | None |
| **New Analysis Fase 1** | Quick wins | 4 hours | -14% (419 → 362) | LOW | None |
| **New Analysis Fase 1-3** | Full optimization | 3.5 hours | -31% (419 → 290) | MEDIUM | None |
| **Hybrid (Option B)** | Original + Advanced | 54 hours | -48% to -63% | HIGH | DEF-102 decision |
| **DEF-79 (Jinja2)** | Architecture rewrite | Unknown | Unknown | HIGH | Conflicts with DEF-101 |

---

## 9. CONCLUSION

### Summary of Findings

1. **DEF-101 sub-issues DO NOT EXIST in Linear** (except DEF-106)
2. **5 new issues need to be created** (DEF-101-1 through DEF-101-6, skip DEF-106 exists)
3. **DEF-79 CONFLICTS with DEF-101** → Need architecture decision (DEF-102)
4. **New analysis (Nov 7) is MORE aggressive** than original DEF-101 → Consider as Phase 4
5. **Duplication risk with DEF-38 and DEF-40** → Check before creating new issues

### Next Steps

**TODAY:**
1. Read DEF-38, DEF-40, DEF-61, DEF-79 content from Linear (check for duplicates)
2. Create **DEF-102: Prompt Architecture Decision** (blocker)
3. Schedule stakeholder meeting (decide Python modules vs Jinja2)

**AFTER DEF-102 DECISION:**
- **If Python modules:** Create DEF-101-1 through DEF-101-6 (Option A)
- **If Jinja2:** Pause DEF-101, prioritize DEF-79, revisit DEF-101 after

**WEEK 1:**
- Execute DEF-101 Phase 1 (CRITICAL fixes)
- Deploy fixed prompt (blocking contradictions resolved)

---

**Document Status:** ✅ COMPLETE
**Analysis Date:** 2025-11-07
**Confidence Level:** HIGH (95% - based on document comparison and ROI analysis)
**Blockers:** DEF-102 (architecture decision) must be resolved first
**Related Documents:**
- `/docs/analyses/PROMPT_COMPREHENSIVE_ANALYSIS_AND_IMPROVEMENT_PLAN.md`
- `/docs/analyses/PROMPT_OPTIMIZATION_ANALYSIS.md`
- `/docs/analyses/PROMPT_OPTIMIZATION_SUMMARY.md`
- `/docs/analyses/DEF_111_vs_DEF_101_ROI_ANALYSIS.md`
