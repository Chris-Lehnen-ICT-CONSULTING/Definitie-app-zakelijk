# DEF-38, DEF-35, DEF-106, DEF-45: Comprehensive Dependency & Impact Analysis

**Date:** 2025-11-05
**Analyst:** Code Explorer
**Scope:** All 4 issues + coupling analysis
**Status:** Complete codebase mapping

---

## 📊 EXECUTIVE SUMMARY

### Issue Overview

| ID | Title | Type | Status | Est. Effort | Blocker | Blocked By |
|---|---|---|---|---|---|---|
| **DEF-35** | MVP Term-Based Classifier Essentials | Feature | OPEN | 16-20h | DEF-38, DEF-40 | None |
| **DEF-38** | Ontologische Promptinjecties (5 contradictions) | Bug/Fix | OPEN | 6-8h | DEF-40 | DEF-35 |
| **DEF-106** | PromptValidator Integration | Feature | OPEN | 4-6h | None | DEF-35 (partial) |
| **DEF-45** | Voorbeelden consistent met term | Enhancement | OPEN | 4h | None | DEF-69 |

### Critical Dependencies

```
DEF-35 (Classifier MVP)
├── Unblocks: DEF-38 (prompt fixes depend on working classifier)
├── Unblocks: DEF-40 (ontological enhancements)
└── Coupled: DEF-106 (validator needs classifier confidence scores)

DEF-38 (Prompt Contradictions Fix)
├── Blocked By: DEF-35 (can't validate fixes without classifier)
├── Enables: Better prompt quality for DEF-106
└── Coupled: Error prevention module shared with DEF-106

DEF-106 (PromptValidator Integration)
├── Depends On: DEF-35 (for classification metadata)
├── Can run parallel: With DEF-38 (different modules)
└── Shared: prompt_orchestrator, modules

DEF-45 (Voorbeelden Consistency)
├── Independent: Can run anytime
├── Related: Uses classification result from DEF-35
└── Data: Depends on DEF-69 (import service fix)
```

---

## 🔴 ISSUE 1: DEF-35 - MVP Term-Based Classifier

### Status: **CRITICAL BLOCKER** for DEF-38, DEF-40

### What It Is
Improves the ontological classifier used in tabbed_interface.py to better determine TYPE/PROCES/RESULTAAT/EXEMPLAAR categories with 3-context support (organisatorische, juridische, wettelijke).

### Current Implementation
- **Location:** `src/ontologie/improved_classifier.py`
- **Already exists:** Full ImprovedOntologyClassifier with pattern matching
- **Used by:** `src/ui/tabbed_interface.py` lines 251-270 (in `_determine_ontological_category()`)
- **UI Integration:** Lines 283-299 (`_render_category_preview()`)

### Files Affected
```
src/ontologie/improved_classifier.py         ← Main implementation (DONE)
src/ontologie/__init__.py                    ← Exports (DONE)
src/ui/tabbed_interface.py                   ← Integration point (NEEDS UPDATE)
  - Lines 251-270: _determine_ontological_category()
  - Lines 283-299: _render_category_preview()
src/services/container.py                    ← Classifier registration (NEEDS CHECK)
```

### Coupling Points

#### 1. **Tight Coupling: UI → Classifier**
```python
# src/ui/tabbed_interface.py:251
from ontologie.improved_classifier import ImprovedOntologyClassifier
classifier = ImprovedOntologyClassifier()
result = classifier.classify(
    begrip=begrip,
    org_context=org_context,
    jur_context=jur_context,
    wet_context=""
)
```

**Risk:** UI directly instantiates classifier (no DI). If classifier changes, UI breaks.

#### 2. **Semantic Integration: Classifier → SemanticCategorisationModule**
The classifier determines the `ontological_category` which is then:
1. Stored in `SessionStateManager.get_value("determined_category")`
2. Passed as `ontologische_categorie` in GenerationRequest
3. Read by SemanticCategorisationModule (lines 86-90):
```python
categorie = context.get_metadata("ontologische_categorie")
if categorie:
    context.set_shared("ontological_category", categorie)
```

**Risk:** If classifier output format changes, module breaks.

### What DEF-35 Needs to Complete

1. **Add to ServiceContainer** (src/services/container.py):
   - Register ImprovedOntologyClassifier as singleton
   - Provide `get_ontology_classifier()` method
   
2. **Update UI Integration** (src/ui/tabbed_interface.py):
   - Use container instead of direct import
   - Handle async classification if needed
   
3. **Add Tests**:
   - Pattern matching accuracy tests
   - 3-context scoring tests
   - Edge cases (empty context, ambiguous terms)

---

## 🔴 ISSUE 2: DEF-38 - Ontologische Promptinjecties (5 Contradictions)

### Status: **BLOCKED BY DEF-35**

### What It Is
Fix 5 contradictions in prompt modules where ESS-02 (semantic categorisation) instructions conflict with STR-01 (structure rules) and error prevention modules.

### The 5 Contradictions

| # | Conflict | ESS-02 Says | STR-01/Error Says | Fix Needed |
|---|---|---|---|---|
| 1 | "is" usage | ✅ "Use 'is een activiteit'" | ❌ "Don't start with 'is'" | Exception clause |
| 2 | Container terms | ✅ "Use 'proces', 'activiteit'" | ❌ "Avoid container terms" | Exemption |
| 3 | Relative clauses | ✅ "Use 'die', 'waarbij'" | ❌ "Avoid 'die', 'waarin'" | Conditional |
| 4 | Article "een" | ✅ "Use 'een' in kick-off" | ❌ "No 'een' at start" | Exception |
| 5 | Context usage | ❌ "Don't mention context" | ✅ "Use context-specific" | Operational guide |

### Files Affected

```
src/services/prompts/modules/semantic_categorisation_module.py
  ├─ Lines 140-144: Base section with contradictions
  ├─ Lines 180-197: Category-specific guidance (PROCES example)
  ├─ Lines 182-185: "is een activiteit" injection
  └─ Lines 200+: TYPE, RESULTAAT, EXEMPLAAR guidance

src/services/prompts/modules/structure_rules_module.py
  ├─ Lines 132-151: _build_str01_rule()
  ├─ Line 136: Example with "is een maatregel"
  └─ Line 147: "❌ is een" example

src/services/prompts/modules/error_prevention_module.py
  ├─ Lines 143-153: _build_basic_errors()
  ├─ Line 146: "❌ Begin niet met lidwoorden ('een')"
  ├─ Line 147: "❌ Geen koppelwerkwoord ('is')"
  ├─ Line 150: "❌ Vermijd containerbegrippen"
  ├─ Line 151: "❌ Vermijd bijzinnen ('die', 'waarin')"
  ├─ Lines 155-194: _build_forbidden_starters()
  ├─ Line 157: "is" in forbidden list
  └─ Lines 196-248: _build_context_forbidden()
```

### Coupling Analysis

#### 1. **Module Interdependency**
```
PromptOrchestrator (orchestrator.py:354-372)
├─ semantic_categorisation (Position 5)  ← ESS-02 instructions
├─ structure_rules (Position 10)         ← STR-01 contradicts!
├─ error_prevention (Position 14)        ← FORBIDS what ESS-02 says!
```

**Problem:** Execution order places contradictions in sequence. GPT-4 gets FIRST instruction A, then contradicting instruction NOT-A.

#### 2. **Shared State Channel**
```python
# semantic_categorisation_module.py:90
context.set_shared("ontological_category", categorie)

# definition_task_module.py:82
ontological_category = context.get_shared("ontological_category")
```

All modules read the ontological_category from shared state. If ESS-02 sets a category, BOTH must respect its implications.

#### 3. **Prompt Content Injection**
```
ModuleContext (base_module.py:17-36)
├─ content: str              ← What gets added to prompt
├─ metadata: dict[str, Any]
└─ shared_state: dict        ← Inter-module communication

# All modules execute in isolation but produce ordered sections:
PromptOrchestrator._combine_outputs() → "\n\n".join(all_outputs)
```

**Risk:** Concatenation order matters. If error_prevention (position 14) contradicts semantic_categorisation (position 5), GPT-4 may follow the last instruction (recency bias).

### What DEF-38 Needs to Complete (Per DEF-102 Analysis)

**Priority 1:** Add ESS-02 exception notice
- File: `semantic_categorisation_module.py`
- Lines 180+ (before guidance injection)
- Add: "⚠️ EXCEPTION for Ontological Category (ESS-02)..."

**Priority 2:** Add STR-01 exception clause
- File: `structure_rules_module.py`  
- Lines 132-151
- Add: "⚠️ EXEMPTION: When ontological category marking (ESS-02) is used..."

**Priority 3-5:** Update error_prevention_module.py
- Modify forbidden_starters to note ESS-02 exception
- Add conditions for "die"/"waarbij" usage
- Clarify context usage rules with operational examples

### Validation Requirement
**Cannot be tested without DEF-35:**
- Classifier determines `ontological_category` metadata
- That metadata is read by SemanticCategorisationModule
- Fix validation requires comparing classifier output + prompt output
- Without working classifier, can't validate that exceptions apply correctly

---

## 🟡 ISSUE 3: DEF-106 - PromptValidator Integration

### Status: **PARTIALLY BLOCKED BY DEF-35**

### What It Is
Add a PromptValidator service to validate generated prompts for contradictions, coverage, and quality before sending to GPT-4.

### No Existing Implementation
- **No files found** with "PromptValidator" (grep search returned 0 results)
- Validator doesn't exist yet
- Needs to be built

### Required Architecture

```
PromptValidator (NEW)
├─ Input: Complete prompt string + metadata
├─ Output: ValidationResult with:
│  ├─ is_valid: bool
│  ├─ contradictions: list[str]
│  ├─ coverage: dict[str, bool]  (ESS-02, STR-01, etc.)
│  ├─ warnings: list[str]
│  └─ suggestions: list[str]
└─ Integration point: UnifiedDefinitionGenerator
   (before calling AI service)

Integration Flow:
User Input → ServiceContainer → DefinitionOrchestrator
  ├─ Classifier.classify() → ontological_category
  ├─ PromptOrchestrator.build_prompt() → full prompt
  ├─ PromptValidator.validate() ← NEW! ← Needs DEF-38 validation rules
  └─ (If valid) → AIServiceV2.generate()
     (If invalid) → Return validation errors to UI
```

### Files Needed

```
src/services/validation/prompt_validator.py      ← NEW
  ├─ PromptValidator class
  ├─ PromptValidationResult dataclass
  ├─ Methods:
  │  ├─ validate() → ValidationResult
  │  ├─ _check_contradictions()
  │  ├─ _check_module_coverage()
  │  ├─ _check_semantic_consistency()
  │  └─ _check_injection_safety()
  └─ Tests in tests/services/validation/test_prompt_validator.py

src/services/interfaces.py      ← UPDATE
  ├─ Add PromptValidationResult interface
  └─ Add PromptValidatorInterface (abstract)

src/services/container.py       ← UPDATE
  ├─ Register PromptValidator singleton
  └─ Wire to UnifiedDefinitionGenerator

src/services/definition_generator.py ← UPDATE
  ├─ Call PromptValidator.validate()
  ├─ Handle validation errors
  └─ Return errors to UI if invalid
```

### Coupling Points

#### 1. **Depends on Module Interfaces**
To validate prompt coverage, validator needs to know:
- Which modules MUST be present
- Which modules are optional per category
- What injection points each module has

**Coupled to:**
- `src/services/prompts/modules/prompt_orchestrator.py` (module registry)
- `src/services/prompts/modules/base_module.py` (module interface)

**Data needed:**
```python
# From PromptOrchestrator
modules = orchestrator.get_registered_modules()
# Returns: [
#   {module_id, module_name, priority, dependencies, info}
# ]

# Validator extracts:
required_modules = {m["module_id"] for m in modules if m["priority"] > 70}
optional_modules = {m["module_id"] for m in modules if m["priority"] <= 70}
```

#### 2. **Depends on Validation Rules (DEF-38)**
To check for contradictions, validator needs rules from DEF-38:

```python
# Examples from DEF-102 analysis
CONTRADICTION_RULES = {
    "is_usage": {
        "allows": ["semantic_categorisation"],  # ESS-02
        "forbids": ["error_prevention", "structure_rules"],
        "exception": "Only when ontological_category is set"
    },
    "container_terms": {
        "allows": ["semantic_categorisation"],
        "forbids": ["error_prevention"],
        "terms": ["proces", "activiteit"]
    },
    # ... etc
}
```

**If DEF-38 not fixed yet:**
- Validator has outdated contradiction rules
- False positives on valid prompts
- **SOLUTION:** DEF-35 + DEF-38 must complete first, then DEF-106 adds validation rules

#### 3. **Depends on Classifier (DEF-35)**
```python
# PromptValidator needs to know:
# - Which category was determined
# - Confidence level of determination
# - Context used for determination

# For validation like:
def _check_semantic_consistency(prompt, metadata):
    category = metadata.get("ontological_category")
    if category == "proces":
        # Check that prompt uses "activiteit"/"handeling" pattern
        if "is een" not in prompt:
            return Warning("ESS-02 PROCES pattern missing")
```

**Blocked by:** DEF-35 (needs classifier metadata format)

### What DEF-106 Needs to Complete

1. **Analyze existing validation patterns** (from DEF-38 analysis)
2. **Design PromptValidator interface**
3. **Implement contradiction detection**
4. **Implement module coverage checking**
5. **Integrate with GenerationRequest flow**
6. **Add comprehensive tests**
7. **Handle validation errors in UI**

### Can Run Parallel With
- DEF-38 (different concern: validation rules vs. prompt fixes)
- However, should wait for DEF-38 completion to avoid duplicate work

---

## 🟠 ISSUE 4: DEF-45 - Voorbeelden Consistent with Term

### Status: **INDEPENDENT** (no blockers)

### What It Is
Ensure voorbeeldzinnen (example sentences) are generated using the same ontological category and context as the definition itself.

### Current State

```
Definition Generation Flow:
User Input (Begrip + Context)
  ↓
Classifier determines ontological_category
  ↓
GenerationRequest created with ontologische_categorie
  ↓
DefinitionOrchestrator.create_definition()
  ├─ Generates definition via PromptOrchestrator
  └─ Generates voorbeelden via unified_voorbeelden.py ← HERE!
```

### Files Affected

```
src/voorbeelden/unified_voorbeelden.py
  ├─ Lines 75+: class ExampleRequest
  └─ Lines 100+: generate_examples()
  └─ NEEDS: ontologische_categorie field + context awareness

src/services/orchestrators/definition_orchestrator_v2.py
  ├─ create_definition() method
  └─ NEEDS: Pass classifier result to voorbeelden generation

src/ui/components/definition_generator_tab.py
  ├─ NEEDS: Display voorbeelden with category context

tests/unit/voorbeelden_functionality_tests.py
  ├─ NEEDS: Tests for category-aware voorbeelden
```

### Coupling Analysis

#### 1. **Weak Coupling: Optional Enhancement**
Voorbeelden generation is separate from definition generation. Can work with/without category awareness.

#### 2. **Data Flow Dependency**
```python
# Current (lacks context):
request = ExampleRequest(
    definitie=definition_text,
    term=term,
    context=generic_context
)
voorbeelden = example_generator.generate_examples(request)

# Needs DEF-35 for category:
request = ExampleRequest(
    definitie=definition_text,
    term=term,
    context=generic_context,
    ontologische_categorie=category,  ← From classifier (DEF-35)
    organisatorische_context=org_ctx,
    juridische_context=jur_ctx,
    wettelijke_basis=wet_ctx
)
```

#### 3. **Related to DEF-69 (Data Loss)**
The dependency graph shows DEF-45 blocked by DEF-69 (import service data loss).

This suggests: voorbeelden consistency depends on voorbeelden being saved correctly first.

### What DEF-45 Needs

1. **Update ExampleRequest** (voorbeelden.py:75)
   - Add `ontologische_categorie` field
   - Add context fields (organisatorische, juridische, wettelijke)

2. **Update example generator** (unified_voorbeelden.py)
   - Use category to guide example generation
   - Ensure examples match definition structure

3. **Update orchestrator** (definition_orchestrator_v2.py)
   - Pass classifier result to voorbeelden generation
   - Maintain consistency between definition + examples

4. **Add tests**
   - Examples match term category
   - Examples use correct context
   - Examples structure matches definition

### No Direct Blockers
- Can implement independently
- Just needs classifier metadata available
- DEF-69 fix ensures voorbeelden are saved (separate concern)

---

## 📋 DEPENDENCY GRAPH

```
┌─────────────────────────────────────────────┐
│  DEF-35: Classifier MVP (16-20h)           │
│  ✓ Implementation: Done                    │
│  ✗ Integration: Needs ServiceContainer DI  │
│  ✗ Tests: Needs unit tests                 │
└────────────┬────────────────────────────────┘
             │
             ├──────→ DEF-38 (Prompt Fixes: 6-8h)
             │        └─ BLOCKED: Needs classifier working
             │           ├─ Validate fixes with real classifier
             │           ├─ Check prompt generation quality
             │           └─ Contradiction detection
             │
             ├──────→ DEF-40 (Ontological Enhancements)
             │        └─ BLOCKED: Needs classifier
             │           └─ Enhancement to semantic rules
             │
             ├──────→ DEF-106 (PromptValidator: 4-6h)
             │        └─ PARTIALLY BLOCKED: Needs DEF-35 + DEF-38
             │           ├─ Needs classifier metadata format
             │           ├─ Needs contradiction rules from DEF-38
             │           └─ Can implement in parallel with DEF-38
             │
             └──────→ DEF-45 (Voorbeelden Consistency: 4h)
                      └─ INDEPENDENT: No blockers
                         ├─ Uses classifier result from DEF-35
                         ├─ Related to (not blocked by) DEF-69
                         └─ Can start anytime
```

---

## 🎯 RECOMMENDED IMPLEMENTATION ORDER

### Phase 1: Foundation (DEF-35) - Week 1
**Duration:** 16-20 hours
**Deliverable:** Working classifier in ServiceContainer

1. **Finalize DEF-35**
   - Add ImprovedOntologyClassifier to ServiceContainer
   - Update UI to use DI instead of direct import
   - Add unit tests for classifier accuracy
   - Validate pattern matching on test corpus

2. **Validation Gate:** Classifier must correctly classify 90%+ of test cases

### Phase 2: Bug Fixes (DEF-38) - Week 1-2
**Duration:** 6-8 hours
**Prerequisite:** DEF-35 complete
**Deliverable:** No contradictions in generated prompts

1. **Add Exception Clauses** (in dependency order):
   - SemanticCategorisationModule: Add ESS-02 exception notice
   - StructureRulesModule: Add STR-01 exemption clause
   - ErrorPreventionModule: Add conditions (3 updates)

2. **Testing Strategy:**
   - Generate prompts for each category (TYPE, PROCES, RESULTAAT, EXEMPLAAR)
   - Check for contradictions in output
   - Compare with DEF-102 contradiction checklist

3. **Validation Gate:** Zero contradictions in test prompts

### Phase 3A: Validation Layer (DEF-106) - Week 2
**Duration:** 4-6 hours
**Prerequisites:** DEF-35 (for metadata), DEF-38 (for contradiction rules)
**Can run:** PARALLEL with Phase 2 (different layers)
**Deliverable:** Validator service + tests

1. **Implement PromptValidator**
   - Create prompt_validator.py
   - Implement contradiction detection
   - Implement module coverage checking
   - Add to ServiceContainer

2. **Integrate with DefinitionGenerator**
   - Call validator before AI service
   - Return validation errors to UI
   - Add error handling

3. **Testing:** Validator catches 100% of known contradictions

### Phase 3B: Enhancement (DEF-45) - Week 2
**Duration:** 4 hours
**Prerequisites:** DEF-35 (for category metadata)
**Can run:** PARALLEL with Phase 3A (independent concern)
**Deliverable:** Category-aware voorbeelden

1. **Update ExampleRequest** with category + context fields
2. **Update example generator** to use category
3. **Update orchestrator** to pass category
4. **Add tests** for consistency

---

## ⚠️ CRITICAL RISKS

### Risk 1: Contradictions Persist After DEF-38
**Impact:** MEDIUM
**Likelihood:** LOW
**Mitigation:** DEF-106 validator catches contradictions; can return error instead of calling AI

### Risk 2: Classifier Output Format Changes
**Impact:** HIGH
**Likelihood:** MEDIUM
**Mitigation:** Lock classifier interface early; add backward compatibility layer

### Risk 3: Prompt Quality Gets Worse
**Impact:** HIGH
**Likelihood:** LOW
**Mitigation:** Compare generation quality before/after fixes using scoring metrics

### Risk 4: Data Loss During voorbeelden Update (DEF-45)
**Impact:** MEDIUM
**Likelihood:** MEDIUM
**Mitigation:** Fix DEF-69 first (import service data loss), then update voorbeelden

---

## 📊 COUPLING STRENGTH MATRIX

```
        DEF-35  DEF-38  DEF-106  DEF-45
DEF-35   -      🔴      🔴       🟡
DEF-38  🔴      -       🟡       ❌
DEF-106 🔴      🟡      -        ❌
DEF-45  🟡      ❌      ❌       -

Legend:
🔴 Strong coupling (blocks implementation)
🟡 Weak coupling (uses but can work around)
❌ No coupling
```

### Coupling Details

#### DEF-35 ↔ DEF-38 (STRONG)
- **Direction:** DEF-35 → DEF-38
- **Type:** Data dependency
- **Why:** Classifier generates ontological_category that DEF-38 fixes depend on
- **Mitigation:** Test DEF-38 fixes against classifier output

#### DEF-35 ↔ DEF-106 (STRONG)
- **Direction:** DEF-35 → DEF-106
- **Type:** Metadata dependency
- **Why:** Validator needs classifier metadata format
- **Mitigation:** Define metadata interface early

#### DEF-38 ↔ DEF-106 (WEAK)
- **Direction:** DEF-38 → DEF-106
- **Type:** Rule dependency
- **Why:** Validator needs contradiction rules from fixes
- **Mitigation:** Can implement validator rules as DEF-38 completes

#### DEF-35 ↔ DEF-45 (WEAK)
- **Direction:** DEF-35 → DEF-45
- **Type:** Data source
- **Why:** DEF-45 uses category from classifier
- **Mitigation:** Can use fallback category if classifier not ready

---

## 🔍 SHARED CODE ELEMENTS

### Files Used by Multiple Issues

```
src/services/prompts/modules/prompt_orchestrator.py
├─ DEF-35: Reads registered modules
├─ DEF-38: Executes module with changes
├─ DEF-106: Analyzes module coverage
└─ DEF-45: Passes context through modules

src/services/prompts/modules/semantic_categorisation_module.py
├─ DEF-35: Reads ontological_category from context
├─ DEF-38: Gets modified (exception clauses added)
└─ DEF-106: Validates semantic consistency

src/services/interfaces.py
├─ DEF-35: GenerationRequest.ontologische_categorie
├─ DEF-38: No changes
├─ DEF-106: Needs PromptValidationResult (NEW)
└─ DEF-45: ExampleRequest (updates needed)

src/services/container.py
├─ DEF-35: Register classifier (NEW)
├─ DEF-106: Register validator (NEW)
└─ DEF-45: Updates to flow (minor)

src/ui/tabbed_interface.py
├─ DEF-35: Use container instead of direct import
├─ DEF-38: No changes (fixes are in modules)
├─ DEF-106: Handle validation errors from prompt
└─ DEF-45: Display category-aware voorbeelden
```

### Shared Module Dependencies

```
src/services/prompts/modules/error_prevention_module.py
├─ DEF-38: Gets modified (3 exception clauses)
└─ DEF-106: Validator needs to know about these rules

src/services/prompts/modules/structure_rules_module.py
├─ DEF-38: Gets modified (1 exception clause)
└─ DEF-106: Validator checks this rule

src/ontologie/improved_classifier.py
├─ DEF-35: Core implementation (mostly done)
├─ DEF-38: Classifier must work to test fixes
├─ DEF-106: Validator reads classifier output
└─ DEF-45: Uses classifier category
```

---

## 📋 IMPLEMENTATION CHECKLIST

### DEF-35: Classifier MVP

- [ ] Move ImprovedOntologyClassifier to ServiceContainer
- [ ] Remove direct imports in tabbed_interface.py
- [ ] Add unit tests (90%+ accuracy target)
- [ ] Test with database corpus
- [ ] Validate metadata format output
- [ ] Document classifier interface

### DEF-38: Prompt Contradictions

- [ ] Add ESS-02 exception notice (semantic_categorisation_module.py)
- [ ] Add STR-01 exemption clause (structure_rules_module.py)
- [ ] Modify error_prevention_module.py (3 updates)
- [ ] Generate test prompts for each category
- [ ] Compare against DEF-102 checklist
- [ ] Manual validation with GPT-4
- [ ] Update documentation

### DEF-106: PromptValidator

- [ ] Design validator interface
- [ ] Implement contradiction detection
- [ ] Implement module coverage checking
- [ ] Add to ServiceContainer
- [ ] Integrate with DefinitionGenerator
- [ ] Write comprehensive tests
- [ ] Add error handling in UI

### DEF-45: Voorbeelden Consistency

- [ ] Update ExampleRequest dataclass
- [ ] Update unified_voorbeelden.py
- [ ] Update definition_orchestrator_v2.py
- [ ] Add category-aware logic to example generator
- [ ] Write tests for consistency
- [ ] Test with various categories

---

## 📚 Related Documentation

- **DEF-102:** Injection Call Stack Analysis
  - Details all 5 contradictions with exact line numbers
  
- **ONTOLOGICAL_CATEGORIE_COMPREHENSIVE_EXPLORATION.md**
  - Classification system architecture
  - Pattern coverage bias analysis
  - Database distribution of categories

- **LINEAR_ISSUES_DEPENDENCY_RISK_ANALYSIS.md**
  - Broader dependency chains
  - Data loss risks (DEF-68, DEF-69, DEF-74)
  - Implementation roadmap

---

## ✅ SUCCESS CRITERIA

### DEF-35 Success
- [ ] Classifier in ServiceContainer
- [ ] 90%+ accuracy on test corpus
- [ ] No direct imports in UI
- [ ] All tests pass

### DEF-38 Success
- [ ] Zero contradictions in generated prompts
- [ ] All 5 contradiction fixes in place
- [ ] Definition quality maintained/improved

### DEF-106 Success
- [ ] Validator catches 100% of known contradictions
- [ ] No false positives on valid prompts
- [ ] < 100ms validation time

### DEF-45 Success
- [ ] Examples use correct category patterns
- [ ] Examples use specified context
- [ ] 100% voorbeelden consistency with definition

---

**Analysis Complete** ✅
Generated: 2025-11-05
Thoroughness: Comprehensive codebase mapping with all coupling points identified

