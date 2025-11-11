# DEF-101 Technical Complexity & Dependencies Analysis

**Document Status:** Complete - Ready for Implementation Planning
**Date:** 2025-11-10
**Analyst:** Debug Specialist
**Purpose:** Technical debugging assessment for DEF-101 prompt optimization implementation

---

## Executive Summary

### Problem Statement

DEF-101 addresses **5 BLOCKING contradictions** in the prompt generation system that make it currently unusable (100% of definitions violate contradictory rules). This analysis provides the technical dependency graph, risk assessment, and execution strategy from a debugging perspective.

### Key Findings

1. **Architecture Type:** Modular pipeline with dependency injection (PromptOrchestrator + 16 modules)
2. **Critical Path:** 3 modules (error_prevention, semantic_categorisation, arai_rules) contain ALL 5 blockers
3. **Parallel Capability:** HIGH - 60% of issues can run simultaneously
4. **Rollback Complexity:** LOW - Module isolation makes rollback straightforward
5. **Test Coverage:** Currently 33% (test_prompt_orchestrator.py exists, no contradiction tests)

---

## 1. DEPENDENCY GRAPH & BLOCKING ANALYSIS

### 1.1 Issue Dependency Matrix

```
LEGEND:
→ Blocks (must complete before dependent starts)
|| Can run in parallel
⊕ Bundled (no extra cost to do together)

PHASE 1 (CRITICAL - Week 1):
┌─────────────────────────────────────────────────────────────────┐
│ CONTRADICTION FIXES (Day 1 - 3 hours)                           │
├─────────────────────────────────────────────────────────────────┤
│ 1.1: ESS-02 "is" exception      [1h]  →  1.4: Article bundled  │
│ 1.2: Container exemption         [30m] || 1.3: Relative clauses │
│ 1.3: Relative clause clarity     [30m] || 1.2: Container        │
│ 1.4: Article "een" (bundled)     [0h]  ⊕  with 1.1              │
│                                                                   │
│ DEPENDENCIES:                                                    │
│ - 1.4 BLOCKED BY 1.1 (same fix location)                        │
│ - 1.2 || 1.3 (different modules, no conflict)                   │
│ - 4.1/4.2 SHOULD WAIT FOR 1.3 (uses relative clause guidance)   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ COGNITIVE LOAD (Day 2 - 2 hours)                                │
├─────────────────────────────────────────────────────────────────┤
│ 2.1: Categorize 42 patterns      [1h]  →  2.4: Koppelwerkwoord │
│ 2.5: Add 3-tier system           [1h]  || 2.1: Categorize      │
│                                                                   │
│ DEPENDENCIES:                                                    │
│ - 2.4 BLOCKED BY 2.1 (forbidden verb list merges into 2.1)     │
│ - 2.5 || 2.1 (different concerns: organization vs prioritization)│
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STRUCTURE & REDUNDANCY (Day 3 - 3 hours)                        │
├─────────────────────────────────────────────────────────────────┤
│ 3.1: Reorder modules             [1h]  →  3.2: Metadata bundled │
│ 3.2: Move metadata (bundled)     [0h]  ⊕  with 3.1              │
│ 2.2: Consolidate ESS-02          [2h]  || 2.3: Enkelvoud        │
│ 2.3: Consolidate enkelvoud       [30m] || 2.4: Koppelwerkwoord  │
│ 2.4: Consolidate koppelwerkwoord [1h]  WAIT 2.1                 │
│                                                                   │
│ DEPENDENCIES:                                                    │
│ - 3.2 BUNDLED WITH 3.1 (orchestrator config)                    │
│ - 2.2 || 2.3 || 2.4 (different modules)                         │
│ - 2.4 WAITS FOR 2.1 (merge forbidden list)                      │
└─────────────────────────────────────────────────────────────────┘

PHASE 2 (QUALITY - Week 2):
┌─────────────────────────────────────────────────────────────────┐
│ TEMPLATE & VALIDATION (Day 1 - 4 hours)                         │
├─────────────────────────────────────────────────────────────────┤
│ 4.1: Fix template Line 112       [1h]  ⊕  with 4.2              │
│ 4.2: Fix template Line 115       [0h]  (bundled)                │
│ 4.3: Visual priority badges      [1h]  WAIT 2.5                 │
│ 1.5: Clarify context usage       [1h]  || 4.1/4.2               │
│                                                                   │
│ DEPENDENCIES:                                                    │
│ - 4.1 + 4.2 bundled (same file, same pattern)                   │
│ - 4.3 WAITS FOR 2.5 (needs tier definitions)                    │
│ - 1.5 independent (context_awareness_module.py)                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ AUTOMATION (Day 2 - 2 hours)                                    │
├─────────────────────────────────────────────────────────────────┤
│ 5.1: PromptValidator             [2h]  →  5.2: Regression tests │
│                                                                   │
│ DEPENDENCIES:                                                    │
│ - 5.2 BLOCKED BY 5.1 (uses PromptValidator)                     │
└─────────────────────────────────────────────────────────────────┘

PHASE 3 (DOCUMENTATION - Week 3):
┌─────────────────────────────────────────────────────────────────┐
│ TESTING & DOCS (Day 1-2 - 4 hours)                              │
├─────────────────────────────────────────────────────────────────┤
│ 5.2: Regression test suite       [2h]  WAIT 5.1                 │
│ 5.3: Module dependency docs      [1h]  WAIT ALL                 │
│                                                                   │
│ DEPENDENCIES:                                                    │
│ - 5.2 WAITS FOR 5.1 (validator dependency)                      │
│ - 5.3 WAITS FOR ALL (documents final state)                     │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Blocking Chain Analysis

**CRITICAL PATH (Must execute sequentially):**
```
1.1 ESS-02 exception → 1.4 Article bundled → 4.1/4.2 Template fixes

2.1 Categorize patterns → 2.4 Koppelwerkwoord consolidation

3.1 Module reorder → 3.2 Metadata move

2.5 Tier system → 4.3 Visual badges

5.1 PromptValidator → 5.2 Regression tests → 5.3 Documentation
```

**PARALLEL TRACKS (Can run simultaneously):**
```
TRACK A: 1.2 Container + 1.3 Relative + 1.5 Context
TRACK B: 2.2 ESS-02 + 2.3 Enkelvoud (until 2.4 ready)
TRACK C: 2.1 Categorize || 2.5 Tier system
```

**Parallelization Potential:** 11 of 18 tasks (61%) can run in parallel

---

## 2. RISK ASSESSMENT PER ISSUE

### 2.1 Risk Scoring Matrix

**Risk Score = (Breaking Potential × Scope × Reversibility) / 10**

| Issue | Breaking Potential | Scope (files) | Reversibility | Risk Score | Rationale |
|-------|-------------------|---------------|---------------|------------|-----------|
| **1.1** ESS-02 "is" | 7/10 (HIGH) | 1 file | 9/10 (EASY) | **6.3 (MEDIUM)** | Changes exception logic, but isolated to error_prevention_module.py. Clear rollback path. |
| **1.2** Container | 5/10 (MED) | 1 file | 10/10 (EASY) | **5.0 (MEDIUM)** | Exempts ontological markers from ARAI-02. Low impact - makes validation more permissive. |
| **1.3** Relative clause | 6/10 (MED-HIGH) | 1 file | 9/10 (EASY) | **5.4 (MEDIUM)** | Clarifies existing ambiguity. Risk: might make AI use relative clauses MORE. |
| **1.4** Article bundled | 2/10 (LOW) | 0 files | 10/10 (EASY) | **2.0 (LOW)** | Bundled with 1.1, no separate risk. |
| **1.5** Context usage | 4/10 (MED-LOW) | 1 file | 8/10 (EASY) | **4.0 (MEDIUM-LOW)** | Guidance only, doesn't change rules. Low breaking potential. |
| **2.1** Categorize 42 | 3/10 (MED-LOW) | 1 file | 7/10 (MEDIUM) | **3.0 (MEDIUM-LOW)** | Reorganizes display, doesn't change rules. Risk: harder to revert (text structure change). |
| **2.2** ESS-02 redundancy | 8/10 (HIGH) | 1 file | 6/10 (MEDIUM) | **8.0 (HIGH)** | Consolidates 38→20 lines. Risk: might lose nuance. NEEDS CAREFUL REVIEW. |
| **2.3** Enkelvoud consolidate | 3/10 (LOW) | 2 files | 8/10 (EASY) | **3.0 (MEDIUM-LOW)** | Cross-references only. Low risk. |
| **2.4** Koppelwerkwoord | 6/10 (MED-HIGH) | 2 files | 7/10 (MEDIUM) | **5.4 (MEDIUM)** | Deletes ARAI-06, merges into STR-01. Risk: lose rule if merge incomplete. |
| **2.5** 3-tier system | 5/10 (MEDIUM) | 1 file + ALL | 8/10 (EASY) | **5.0 (MEDIUM)** | Adds metadata, doesn't remove rules. Risk: AI focuses only on TIER 1. |
| **3.1** Reorder modules | 7/10 (MED-HIGH) | 1 file | 9/10 (EASY) | **6.3 (MEDIUM)** | Changes execution order. Risk: dependency breaks. GOOD TESTS REQUIRED. |
| **3.2** Metadata move | 2/10 (LOW) | 1 file | 10/10 (EASY) | **2.0 (LOW)** | Bundled with 3.1, no separate risk. |
| **4.1/4.2** Template fixes | 4/10 (MED-LOW) | 1 file | 9/10 (EASY) | **4.0 (MEDIUM-LOW)** | Fixes template compliance. Low risk - makes templates BETTER. |
| **4.3** Visual badges | 2/10 (LOW) | 10 files | 8/10 (EASY) | **2.5 (LOW)** | Adds emojis. Risk: visual clutter, but easy to revert. |
| **5.1** PromptValidator | 3/10 (LOW) | 0 files (new) | 10/10 (EASY) | **3.0 (MEDIUM-LOW)** | New code, no existing system changes. Can disable if buggy. |
| **5.2** Regression tests | 1/10 (VERY LOW) | 0 files (new) | 10/10 (EASY) | **1.0 (LOW)** | Tests only. No production code risk. |
| **5.3** Documentation | 0/10 (NONE) | 0 files (new) | 10/10 (EASY) | **0.0 (NONE)** | Documentation only. Zero breaking risk. |

### 2.2 Top 3 Riskiest Changes

**1. Issue 2.2: ESS-02 Consolidation (Risk Score: 8.0)**
- **Risk:** Consolidating 38 lines to 20 might lose critical nuance in category-specific guidance
- **Impact:** TYPE/EXEMPLAAR definitions might become less specific
- **Mitigation:**
  - Create golden reference set of 10 definitions (before consolidation)
  - Re-generate same definitions after change
  - Compare quality scores
  - If quality drops >5%, revert and iterate
- **Rollback:** Git revert straightforward
- **Testing:** MANDATORY A/B testing with real definitions

**2. Issue 3.1: Module Reordering (Risk Score: 6.3)**
- **Risk:** Changing execution order might break module dependencies or shared state
- **Impact:** Modules expecting data from previous modules might get empty context
- **Mitigation:**
  - Audit `get_dependencies()` for ALL modules (already exists in code!)
  - Run `orchestrator.resolve_execution_order()` and validate output
  - Check shared_state access patterns (grep for `context.set_shared` and `context.get_shared`)
- **Rollback:** One-line revert in `_get_default_module_order()`
- **Testing:** Existing test `test_orchestrator_resolves_dependencies_and_builds_prompt()` MUST PASS

**3. Issue 1.1: ESS-02 "is" Exception (Risk Score: 6.3)**
- **Risk:** Exception clause might be misinterpreted by AI, leading to overuse of "is"
- **Impact:** AI might start EVERY definition with "is" thinking it's always allowed
- **Mitigation:**
  - Make exception VERY specific: "ONLY for ontological category marking"
  - Add counter-examples: "❌ is een document (NO! Unless TYPE category)"
  - Test with 20 definitions across all 4 categories
- **Rollback:** Remove exception clause (simple text deletion)
- **Testing:** Validate ESS-02 compliance rate before/after (should go from 0% → 80%+)

---

## 3. PARALLEL EXECUTION STRATEGY

### 3.1 Optimal Execution Batches

**Day 1 (3 hours) - CONTRADICTIONS:**
```
BATCH 1 (Sequential - 1.5h):
└─ 1.1 ESS-02 "is" exception + 1.4 Article bundled

BATCH 2 (Parallel - 1h):
├─ Developer A: 1.2 Container exemption
└─ Developer B: 1.3 Relative clause clarity

BATCH 3 (Sequential - 0.5h):
└─ 4.1 + 4.2 Template fixes (bundled)
```

**Day 2 (2 hours) - COGNITIVE LOAD:**
```
BATCH 4 (Parallel - 1h):
├─ Developer A: 2.1 Categorize 42 patterns
└─ Developer B: 2.5 Add 3-tier system

BATCH 5 (Sequential - 1h):
└─ 2.4 Koppelwerkwoord consolidation (waits for 2.1)
```

**Day 3 (3 hours) - STRUCTURE:**
```
BATCH 6 (Sequential - 1.5h):
└─ 3.1 Module reorder + 3.2 Metadata move (bundled)

BATCH 7 (Parallel - 1.5h):
├─ Developer A: 2.2 ESS-02 consolidation (HIGH RISK - needs careful review)
├─ Developer B: 2.3 Enkelvoud consolidation
└─ (2.4 already done in Day 2)
```

**Week 2 - QUALITY:**
```
BATCH 8 (Parallel - 2h):
├─ Developer A: 1.5 Context usage clarity
└─ Developer B: 4.3 Visual priority badges (waits for 2.5)

BATCH 9 (Sequential - 2h):
└─ 5.1 PromptValidator automation
```

**Week 3 - TESTING:**
```
BATCH 10 (Sequential - 2h):
└─ 5.2 Regression test suite (waits for 5.1)

BATCH 11 (Solo - 1h):
└─ 5.3 Documentation (waits for all)
```

### 3.2 Single Developer vs Multi-Developer

**Single Developer Timeline (Sequential):**
- Week 1: 8 hours (as planned)
- Week 2: 4 hours
- Week 3: 3 hours
- **Total: 15 hours**

**Two Developer Timeline (Optimal Parallel):**
- Week 1: 5.5 hours (save 2.5h via parallel execution)
- Week 2: 3 hours (save 1h)
- Week 3: 3 hours (no parallelization benefit)
- **Total: 11.5 hours**

**Recommendation:** SINGLE DEVELOPER execution acceptable
- Parallelization saves only 3.5 hours (23%)
- Coordination overhead: 1-2 hours
- Net benefit: 1.5-2.5 hours
- **NOT WORTH** the merge conflict risk for this scope

---

## 4. TESTING STRATEGY

### 4.1 Minimum Viable Test Coverage

**CRITICAL (Must have before merge):**

1. **Contradiction Detection Tests (5.2)** - 2 hours
   ```python
   # tests/services/prompts/test_prompt_contradictions.py
   def test_ess02_exception_present():
       """Verify ESS-02 exception clause exists."""
       prompt = generate_prompt("vermogen", "resultaat")
       assert "EXCEPTION voor Ontologische Categorie" in prompt

   def test_no_container_contradiction():
       """Verify proces/activiteit allowed for ESS-02."""
       prompt = generate_prompt("onderzoek", "proces")
       assert "proces waarbij" in prompt  # Should be allowed
       # Should have exception clause if forbidden elsewhere
       if "❌ Vermijd containerbegrippen ('proces'" in prompt:
           assert "EXCEPTION" in prompt

   def test_relative_clause_guidance():
       """Verify relative clauses have usage guidance."""
       prompt = generate_prompt("test", "type")
       assert "Beperk relatieve bijzinnen" in prompt
       assert "ALLEEN wanneer" in prompt  # Should have conditional

   def test_redundancy_below_threshold():
       """Verify critical rules not repeated >3 times."""
       prompt = generate_prompt("test", "type")
       assert prompt.count("enkelvoud") <= 3
       assert prompt.count("koppelwerkwoord") <= 3

   def test_module_order_correct():
       """Verify semantic_categorisation before line 50."""
       prompt = generate_prompt("test", "proces")
       ess02_line = find_line_number(prompt, "Ontologische categorie")
       assert ess02_line < 50, f"ESS-02 at line {ess02_line}, should be <50"
   ```

2. **Module Dependency Tests** - 30 minutes
   ```python
   # tests/services/prompts/test_module_dependencies.py
   def test_resolve_execution_order_no_cycles():
       """Verify no circular dependencies after reorder."""
       orchestrator = PromptOrchestrator()
       # Register all modules
       batches = orchestrator.resolve_execution_order()
       assert len(batches) > 0  # Should complete without DependencyCycleError

   def test_metadata_available_early():
       """Verify definition_task module runs first."""
       orchestrator = PromptOrchestrator()
       order = orchestrator.get_modules_by_priority()
       assert order[0] == "definition_task"
   ```

3. **Golden Reference Comparison** - 1 hour
   ```python
   # tests/services/prompts/test_golden_references.py
   GOLDEN_DEFINITIONS = {
       "vermogen": {
           "category": "resultaat",
           "expected_keywords": ["resultaat", "maatregel", "toegepast"],
           "forbidden_patterns": ["is een", "de vermogen"],
           "min_quality_score": 80
       },
       "onderzoek": {
           "category": "proces",
           "expected_keywords": ["activiteit", "waarbij", "verzamelen"],
           "forbidden_patterns": ["is", "het onderzoek"],
           "min_quality_score": 85
       }
   }

   def test_golden_definition_quality_maintained():
       """Verify quality doesn't degrade after changes."""
       for term, spec in GOLDEN_DEFINITIONS.items():
           definition = generate_definition(term, spec["category"])

           # Check expected patterns present
           for keyword in spec["expected_keywords"]:
               assert keyword in definition.lower()

           # Check forbidden patterns absent
           for forbidden in spec["forbidden_patterns"]:
               assert forbidden not in definition.lower()

           # Check quality score
           score = validate_definition(definition)
           assert score >= spec["min_quality_score"]
   ```

**NICE TO HAVE (Post-merge validation):**

4. **Integration Tests** - 2 hours
   - Full prompt generation with all 16 modules
   - Token count validation (<10,000 tokens)
   - Generation time (<500ms)

5. **Prompt Validator Automation** - 2 hours
   - Run PromptValidator on every commit (CI/CD)
   - Fail build if contradictions detected

### 4.2 Test Execution Order

```
PRE-MERGE (MANDATORY):
1. Run existing tests: pytest tests/services/prompts/
2. Add contradiction tests (test_prompt_contradictions.py)
3. Add dependency tests (test_module_dependencies.py)
4. Run golden reference tests (generate 10 definitions, compare before/after)
5. Manual review: Generate 5 definitions per category (20 total), check quality

POST-MERGE (Week 3):
6. Add integration tests
7. Add PromptValidator to CI/CD
8. Performance benchmarking (token count, generation time)
```

**Coverage Target:** 80%+ for modified modules

---

## 5. ROLLBACK COMPLEXITY ANALYSIS

### 5.1 Rollback Difficulty Ranking

| Issue | Rollback Method | Time to Rollback | Data Loss Risk | Difficulty |
|-------|----------------|------------------|----------------|------------|
| 1.1 ESS-02 | `git revert <commit>` | 2 min | NONE | ⭐ EASY |
| 1.2 Container | `git revert <commit>` | 2 min | NONE | ⭐ EASY |
| 1.3 Relative | `git revert <commit>` | 2 min | NONE | ⭐ EASY |
| 1.4 Article | Bundled with 1.1 | 2 min | NONE | ⭐ EASY |
| 1.5 Context | `git revert <commit>` | 2 min | NONE | ⭐ EASY |
| 2.1 Categorize | `git revert <commit>` | 2 min | NONE | ⭐ EASY |
| 2.2 ESS-02 consolidate | `git revert <commit>` | 2 min | **Possible nuance loss** | ⭐⭐ MEDIUM |
| 2.3 Enkelvoud | `git revert <commit>` | 2 min | NONE | ⭐ EASY |
| 2.4 Koppelwerkwoord | Manual restore ARAI-06 | 10 min | **Rule deletion** | ⭐⭐ MEDIUM |
| 2.5 Tier system | `git revert <commit>` | 2 min | NONE | ⭐ EASY |
| 3.1 Module reorder | Revert one line | 1 min | NONE | ⭐ EASY |
| 3.2 Metadata | Bundled with 3.1 | 1 min | NONE | ⭐ EASY |
| 4.1/4.2 Templates | `git revert <commit>` | 2 min | NONE | ⭐ EASY |
| 4.3 Visual badges | `git revert <commit>` (10 files) | 5 min | NONE | ⭐⭐ MEDIUM |
| 5.1 Validator | Delete file | 1 min | NONE (new code) | ⭐ EASY |
| 5.2 Tests | Delete file | 1 min | NONE (tests) | ⭐ EASY |
| 5.3 Docs | Delete file | 1 min | NONE (docs) | ⭐ EASY |

### 5.2 Emergency Rollback Procedure

**SCENARIO: Major issue discovered post-merge (Week 1 deployment)**

**Option 1: Full Rollback (5 minutes)**
```bash
# Identify merge commit
git log --oneline --grep="DEF-101" -n 5

# Full revert
git revert <merge-commit-hash>
git push origin main

# Redeploy previous version
./scripts/deploy.sh
```

**Option 2: Selective Rollback (10 minutes)**
```bash
# Keep safe changes, revert problematic ones
git revert <commit-2.2>  # Revert ESS-02 consolidation (high risk)
git revert <commit-3.1>  # Revert module reorder (if dependency issue)

# Keep other changes (contradiction fixes, categorization)
git push origin main
```

**Option 3: Feature Flag (0 downtime)**
```python
# Add to prompt_orchestrator.py BEFORE merge
USE_LEGACY_PROMPT = os.getenv("USE_LEGACY_PROMPT", "false") == "true"

def build_prompt(...):
    if USE_LEGACY_PROMPT:
        return self._legacy_prompt_builder(...)
    else:
        return self._new_modular_prompt(...)
```
**Deploy with:** `USE_LEGACY_PROMPT=false` (new prompt)
**Rollback with:** `USE_LEGACY_PROMPT=true` (old prompt)

**Recommendation:** Use Feature Flag for Week 1 deployment, remove after Week 2 validation

---

## 6. TECHNICAL IMPLEMENTATION NOTES

### 6.1 Module Architecture Understanding

**PromptOrchestrator Pattern:**
```python
# From prompt_orchestrator.py analysis:

class PromptOrchestrator:
    def __init__(self, max_workers=4, module_order=None):
        self.modules = {}  # Registry
        self.dependency_graph = defaultdict(set)  # Dependency tracking
        self.module_order = module_order or self._get_default_module_order()

    def register_module(self, module: BasePromptModule):
        self.modules[module.module_id] = module
        self.dependency_graph[module.module_id] = set(module.get_dependencies())

    def resolve_execution_order(self) -> list[list[str]]:
        # Kahn's algorithm for topological sort
        # Returns batches: [[batch1_modules], [batch2_modules], ...]

    def build_prompt(self, begrip, context, config) -> str:
        # 1. Create ModuleContext (shared state container)
        # 2. Execute modules in batches (parallel where possible)
        # 3. Combine outputs via _combine_outputs()
        # 4. Return complete prompt string
```

**Key Insight:** Modules are LOOSELY COUPLED
- Each module receives `ModuleContext` (shared state container)
- Modules can `set_shared()` and `get_shared()` data
- Dependencies declared via `get_dependencies()` method
- **Rollback impact:** Changing ONE module doesn't affect others (unless dependency)

### 6.2 Critical Code Paths

**Issue 1.1 (ESS-02 Exception) - Implementation:**
```python
# File: src/services/prompts/modules/error_prevention_module.py
# Line: ~145 (in _build_basic_errors method)

def _build_basic_errors(self) -> list[str]:
    return [
        "- ❌ Begin niet met lidwoorden ('de', 'het', 'een')",
        "- ❌ Gebruik geen koppelwerkwoord aan het begin ('is', 'betekent', 'omvat')",
        # ADD HERE:
        "\n⚠️ **EXCEPTION voor Ontologische Categorie (ESS-02):**",
        "Bij het markeren van ontologische categorie MAG je starten met:",
        "- 'activiteit waarbij...' (PROCES)",
        "- 'resultaat van...' (RESULTAAT)",
        "- [kernwoord] dat/die... (TYPE)",
        "- 'exemplaar van...' (EXEMPLAAR)",
        "Dit is de ENIGE uitzondering op de 'geen werkwoord/lidwoord aan start' regel.\n",

        "- ❌ Herhaal het begrip niet letterlijk",
        # ... rest of rules
    ]
```

**Issue 3.1 (Module Reorder) - Implementation:**
```python
# File: src/services/prompts/modules/prompt_orchestrator.py
# Line: 347-372 (_get_default_module_order method)

def _get_default_module_order(self) -> list[str]:
    # CURRENT (BAD):
    return [
        "expertise",
        "output_specification",
        "grammar",
        "context_awareness",
        "semantic_categorisation",  # Line 71! TOO LATE
        ...
    ]

    # NEW (GOOD):
    return [
        "definition_task",          # 1. TASK METADATA FIRST
        "expertise",                # 2. Role
        "semantic_categorisation",  # 3. ONTOLOGICAL (most critical!)
        "output_specification",     # 4. Format
        "grammar",                  # 5. Grammar baseline
        "context_awareness",        # 6. Context details
        "structure_rules",          # 7. Structural (TIER 1)
        "template",                 # 8. Templates (AFTER rules!)
        "ess_rules", "integrity_rules", "arai_rules",
        "con_rules", "sam_rules", "ver_rules",
        "error_prevention",         # 15. Forbidden (categorized)
        "metrics",                  # 16. Metrics (APPENDIX)
    ]
```

**Issue 2.1 (Categorize 42 Patterns) - Implementation:**
```python
# File: src/services/prompts/modules/error_prevention_module.py
# Line: 155-194 (_build_forbidden_starters method)

def _build_forbidden_starters(self) -> list[str]:
    # CURRENT (BAD): 42 individual bullets
    return [f"- ❌ Start niet met '{starter}'" for starter in forbidden_starters]

    # NEW (GOOD): 7 categories
    forbidden_categories = {
        "KOPPELWERKWOORDEN": ["is", "betreft", "omvat", "betekent", ...],
        "CONSTRUCTIES": ["bestaat uit", "bevat", "behelst", ...],
        "LIDWOORDEN": ["de", "het", "een"],
        "PROCES-FRAGMENTEN": ["proces waarbij", "handeling die", ...],
        "EVALUATIEVE TERMEN": ["een belangrijk", "een essentieel", ...],
        "TIJD-VORMEN": ["wordt", "zijn", "was", "waren"],
        "OVERIGE": ["methode voor", "manier om", ...]
    }

    result = ["### ⚠️ Veelgemaakte fouten (CATEGORIZED):"]
    for category, patterns in forbidden_categories.items():
        result.append(f"**{category}:** ❌ {', '.join(patterns)}")
    return result
```

### 6.3 Testing Hooks

**Existing Test Infrastructure:**
```python
# tests/services/prompts/test_prompt_orchestrator.py
# Tests already exist for:
- Module registration
- Dependency resolution (test_orchestrator_resolves_dependencies_and_builds_prompt)
- Execution order validation
- Module skipping (test_orchestrator_skips_invalid_module_and_keeps_content)

# LEVERAGE THESE for regression testing!
```

**Where to Add New Tests:**
```
tests/services/prompts/
├── test_prompt_orchestrator.py          (existing - add reorder test)
├── test_prompt_contradictions.py        (NEW - Issue 5.2)
├── test_module_dependencies.py          (NEW - validate no cycles)
├── test_golden_references.py            (NEW - quality comparison)
└── test_prompt_validator.py             (NEW - Issue 5.1)
```

---

## 7. EXECUTION RECOMMENDATION

### 7.1 Phased Deployment Strategy

**PHASE 1: CRITICAL FIXES (Week 1) - Deploy to Staging**
```
Day 1-3: Implement Issues 1.1-4.2, 2.1-2.5, 3.1-3.2
Day 4: Deploy to staging, run smoke tests
Day 5: A/B test (10 definitions old vs new prompt)
Weekend: Monitor staging, collect feedback
```
**GO/NO-GO Decision:** If quality score ≥80% on 10 test definitions → Deploy to prod Monday

**PHASE 2: QUALITY IMPROVEMENTS (Week 2) - Feature Flag**
```
Day 1-2: Implement Issues 1.5, 4.3, 5.1
Deploy with feature flag: 50% traffic to new prompt
Monitor: Definition quality, user feedback, error rate
Day 3-5: Ramp to 100% if no issues
```

**PHASE 3: VALIDATION & DOCS (Week 3) - Stabilization**
```
Day 1-2: Implement Issues 5.2, 5.3
Run full regression suite
Remove feature flag (new prompt becomes default)
Archive legacy prompt code
```

### 7.2 Success Criteria Per Phase

**Phase 1 (Week 1):**
- ✅ Zero blocking contradictions (PromptValidator passes)
- ✅ ESS-02 compliance rate: 0% → 80%+
- ✅ Cognitive load: 9/10 → 6/10 (measurable: rule count, redundancy)
- ✅ All existing tests pass
- ✅ 10 golden reference definitions maintain quality ≥80%

**Phase 2 (Week 2):**
- ✅ Visual hierarchy improves scanning time (manual test: <30s to find TIER 1 rule)
- ✅ Context usage clarity: <5% user questions about context (vs current 50%)
- ✅ PromptValidator catches new contradictions (CI/CD integration)

**Phase 3 (Week 3):**
- ✅ Regression test suite: 0 failures
- ✅ Documentation complete (dependency map, testing guide)
- ✅ Token count reduced by 15% (measure: avg prompt length before/after)
- ✅ 4-week uptime with zero critical issues

### 7.3 Final Recommendation

**PROCEED WITH DEF-101 IMMEDIATELY**

**Rationale:**
1. **Risk is MANAGEABLE:** 82% of issues are LOW-MEDIUM risk (≤5.4 score)
2. **Architecture supports safe rollback:** Modular design, feature flags available
3. **Parallelization possible:** 61% of tasks can run simultaneously
4. **Testing infrastructure exists:** Leverage existing test_prompt_orchestrator.py
5. **Impact is HIGH:** System currently UNUSABLE (5 blocking contradictions)

**Confidence Level:** 85% (High confidence)
- 15% uncertainty due to ESS-02 consolidation (Issue 2.2) - NEEDS CAREFUL A/B TESTING

**Recommended Start:** Week of 2025-11-11 (this week)

---

## 8. APPENDIX: FILE IMPACT SUMMARY

### 8.1 Files to Modify (10 files)

| File | Issues | Lines Changed | Risk | Dependencies |
|------|--------|---------------|------|--------------|
| `error_prevention_module.py` | 1.1, 1.3, 2.1 | ~50 lines | MEDIUM | None |
| `semantic_categorisation_module.py` | 2.2 | ~18 lines | HIGH | None |
| `arai_rules_module.py` | 1.2, 2.4 | ~10 lines | MEDIUM | None |
| `prompt_orchestrator.py` | 2.5, 3.1 | ~30 lines | MEDIUM | All modules |
| `template_module.py` | 4.1, 4.2 | ~5 lines | LOW | None |
| `ver_rules_module.py` | 2.3 | ~5 lines | LOW | grammar_module |
| `grammar_module.py` | 2.3 | ~0 lines (ref only) | LOW | None |
| `definition_task_module.py` | 3.2 | ~10 lines | LOW | None |
| `context_awareness_module.py` | 1.5 | ~20 lines | LOW | None |
| `structure_rules_module.py` | 4.3 | ~2 lines/rule | LOW | None |

**Total Estimated Lines Changed:** ~150 lines across 10 files

### 8.2 Files to Create (3 files)

| File | Purpose | Size | Dependencies |
|------|---------|------|--------------|
| `prompt_validator.py` | Contradiction detection | ~200 lines | None (standalone) |
| `test_prompt_contradictions.py` | Regression tests | ~300 lines | PromptValidator, pytest |
| `prompt_module_dependency_map.md` | Documentation | ~150 lines | None (docs) |

### 8.3 Dependency Impact Map

```
┌─────────────────────────────────────────────────────────┐
│ HIGH IMPACT (10+ dependent modules)                     │
├─────────────────────────────────────────────────────────┤
│ prompt_orchestrator.py (3.1) → ALL 16 modules           │
│   Risk: Module reorder could break execution flow       │
│   Mitigation: Validate with resolve_execution_order()   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ MEDIUM IMPACT (1-3 dependent modules)                   │
├─────────────────────────────────────────────────────────┤
│ error_prevention_module.py (1.1, 1.3, 2.1)              │
│   Depends on: context_awareness (for context data)      │
│   Risk: Exception clause might conflict with other mods │
│                                                          │
│ semantic_categorisation_module.py (2.2)                 │
│   Depends on: None                                       │
│   Used by: template_module, definition_task_module      │
│   Risk: Consolidation might remove data other mods use  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ LOW IMPACT (0 dependencies)                             │
├─────────────────────────────────────────────────────────┤
│ All other modules: Standalone changes, no dependencies  │
└─────────────────────────────────────────────────────────┘
```

---

## 9. DEBUGGING CHECKLIST (Pre-Implementation)

**Before starting ANY issue:**

- [ ] Read module source code (understand current logic)
- [ ] Check `get_dependencies()` method (understand data flow)
- [ ] Grep for `set_shared()` calls (what data does this module provide?)
- [ ] Grep for `get_shared()` calls (what data does this module consume?)
- [ ] Run existing tests for this module (establish baseline)
- [ ] Create branch: `feature/DEF-101-issue-X.X`

**After implementing issue:**

- [ ] Run module-specific tests (if exist)
- [ ] Run full test suite: `pytest tests/services/prompts/`
- [ ] Generate 5 test definitions (manual quality check)
- [ ] Check prompt length (shouldn't increase >5%)
- [ ] Validate no new warnings in logs
- [ ] Git commit with conventional format: `fix(DEF-101): [description]`

**Before merging to main:**

- [ ] All tests pass (pytest exit code 0)
- [ ] Code review completed (or self-review checklist)
- [ ] Golden reference comparison (10 definitions before/after)
- [ ] No blocking contradictions (run PromptValidator if available)
- [ ] Documentation updated (if architecture changed)

---

## 10. CONCLUSION

### Key Takeaways

1. **Feasibility:** DEF-101 is HIGHLY FEASIBLE with current codebase architecture
2. **Risk:** MANAGEABLE - 82% of issues are low-medium risk, rollback is straightforward
3. **Parallelization:** 61% of tasks can run simultaneously (but single dev is fine)
4. **Testing:** Leverage existing infrastructure, add 3 new test files
5. **Timeline:** 3 weeks is REALISTIC (8h + 4h + 3h = 15h total effort)

### Confidence Assessment

**Overall Implementation Confidence: 85%**

**Breakdown:**
- Architecture understanding: 95% (code is clear, well-modularized)
- Risk mitigation: 85% (rollback straightforward, tests available)
- Issue 2.2 (ESS-02 consolidation): 65% (needs careful A/B testing)
- Timeline accuracy: 90% (effort estimates are conservative)
- Parallel execution: 75% (dependencies well-understood, but some unknowns)

**Recommendation:** PROCEED with implementation, but:
- Deploy Phase 1 to staging FIRST (not prod)
- Use feature flags for Week 2 deployment
- Run A/B tests on Issue 2.2 (ESS-02 consolidation) before full rollout

### Next Steps

1. **This week:** Stakeholder approval for DEF-101 start
2. **Monday 2025-11-11:** Create Linear Epic + sub-issues
3. **Tuesday 2025-11-12:** Start Phase 1 - Day 1 (Issues 1.1-1.4, 4.1-4.2)
4. **Friday 2025-11-15:** Deploy to staging, weekend smoke test
5. **Monday 2025-11-18:** Production deployment (if staging green)

---

**Document Status:** ✅ COMPLETE
**Created:** 2025-11-10
**Analyst:** Debug Specialist (AI-assisted)
**Review Required:** Lead Developer, Product Owner
**Next Action:** Stakeholder approval → Linear Epic creation → Start implementation

**Related Documents:**
- `docs/planning/CONSENSUS_IMPLEMENTATION_PLAN.md` (source)
- `docs/analyses/DEF_111_vs_DEF_101_ROI_ANALYSIS.md` (ROI analysis)
- `docs/analyses/PROMPT_COMPREHENSIVE_ANALYSIS_AND_IMPROVEMENT_PLAN.md` (detailed issues)
