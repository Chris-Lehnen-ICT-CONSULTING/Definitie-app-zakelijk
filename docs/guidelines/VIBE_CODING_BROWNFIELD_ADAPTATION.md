---
id: VIBE-BROWNFIELD-GUIDE
title: "Vibe Coding Brownfield Adaptation Guide - DefinitieAgent"
status: active
owner: architecture
canonical: true
last_verified: 2025-10-17
applies_to: definitie-app@current
related_docs:
  - docs/reports/VIBE_CODING_QUALITY_ASSESSMENT.md
  - docs/reports/vibe-coding-architecture-analysis.md
  - CLAUDE.md
  - docs/refactor-log.md
---

# Vibe Coding Brownfield Adaptation Guide

**Context**: DefinitieAgent is a mature brownfield project with existing architecture, technical debt, and active development. Vibe Coding templates are primarily greenfield-focused, designed for new projects.

**Purpose**: This guide adapts Vibe Coding methodology for brownfield refactoring, legacy code modernization, and incremental improvements within DefinitieAgent's constraints.

---

## Executive Summary

### Key Findings

**Vibe Coding Templates**: Greenfield-Focused (85%)
- 8-Step Method: Complete new project workflow
- 5-Step PM: Problem → Solution (new features)
- Planning System: Architecture from scratch
- UI Opzet: New UI design workflow
- **Only 15% directly applicable to brownfield refactoring**

**DefinitieAgent Reality**: Mature Brownfield Project
- 26% feature completion (23/87 features done)
- 150+ unused Python files requiring cleanup
- Active V1→V2 migration (completed 19-09-2025)
- **"REFACTOREN, GEEN BACKWARDS COMPATIBILITY"** policy
- Single-user application (no production compatibility burden)

**Adaptation Strategy**: 3-Track Hybrid Approach
1. **Refactoring Track**: Apply Vibe to legacy code cleanup (70% effort)
2. **New Features Track**: Use standard Vibe templates (20% effort)
3. **Incremental Improvement Track**: Enhance existing features (10% effort)

---

## 1. Vibe Coding Greenfield vs Brownfield Analysis

### 1.1 Original Vibe Coding Assumptions (Greenfield)

| Assumption | Greenfield Reality | DefinitieAgent Brownfield Reality |
|------------|-------------------|-----------------------------------|
| **Clean Slate** | Start with empty codebase | 304 Python files, 60% completion |
| **Architecture Freedom** | Design from scratch | ServiceContainer DI, 16 prompt modules exist |
| **No Legacy** | No technical debt | V1→V2 migration, 150+ unused files |
| **Spec First** | Define before building | Features exist but under-documented |
| **User Research** | Discover needs | User needs known (juridische definitie generatie) |
| **Iterative Prototyping** | Fail fast, pivot | Production system (1 user, but live) |
| **PM Framework** | Problem discovery | Problems known (45 validation rules, web lookup, etc.) |

**Conclusion**: 85% of Vibe Coding assumes greenfield. We must adapt.

### 1.2 Brownfield-Specific Challenges in DefinitieAgent

#### Challenge 1: Legacy Code Without Documentation
**Example**: 150+ unused Python files in `src/` directory
- No specs for what they *should* do
- No tests to verify behavior
- Unknown if still in use

**Traditional Vibe Approach**: "Write spec first" (Tip 1.1)
**Brownfield Adaptation**: "Reverse-engineer spec from code" → **Archaeology Mode**

#### Challenge 2: Existing Architecture Cannot Be Changed
**Example**: `ServiceContainer` DI pattern is core architecture
- 16 prompt modules depend on it
- `PromptOrchestrator` uses dependency resolution
- Cannot start from scratch

**Traditional Vibe Approach**: "Architect First" (Tip 8)
**Brownfield Adaptation**: "Respect Existing Architecture, Enhance Within Constraints" → **Constraint-Aware Refactoring**

#### Challenge 3: No Backwards Compatibility Required
**Example**: CLAUDE.md explicitly states "GEEN BACKWARDS COMPATIBILITY CODE"
- Single-user application
- Not in production (pre-release phase)
- Can break things during refactoring

**Traditional Vibe Approach**: "Safe, incremental changes"
**Brownfield Adaptation**: "Aggressive refactoring with business logic preservation" → **Surgical Modernization**

#### Challenge 4: Features Exist But Are Incomplete
**Example**: 87 features defined, 23 complete (26%)
- Some features 80% done, need polish
- Others 0% done, need full implementation
- Mixed greenfield + brownfield

**Traditional Vibe Approach**: "Build new feature start to finish"
**Brownfield Adaptation**: "Completion-Aware Workflow Selection" → **Hybrid Feature Development**

---

## 2. Brownfield-Adapted Vibe Coding Workflows

### 2.1 ARCHAEOLOGY MODE (Reverse-Engineering Specs)

**When to Use**: Legacy code without documentation or tests

**Original Vibe**: Spec-Driven Development (1.1) - Write spec first
**Brownfield Adaptation**: Archaeology-Driven Understanding - Extract spec from code

#### Archaeology Mode Workflow

**Step 1: Code Excavation**
```markdown
AI Prompt (Archaeology):
Analyze this legacy module: [FILE PATH]

As a software archaeologist:
1. **Purpose**: What does this code try to do? (business goal)
2. **Inputs**: What data does it accept? (parameters, dependencies)
3. **Outputs**: What does it produce? (return values, side effects)
4. **Business Logic**: What rules/validations are embedded?
5. **Dependencies**: What other modules does it use?
6. **Risk Assessment**: What breaks if we remove this?

Output: Reverse-Engineered Mini-Spec (use 1.1 template format)
```

**Step 2: Validation via Tests**
```markdown
AI Prompt (Archaeology Validation):
Based on the reverse-engineered spec, write pytest tests that:
1. Verify current behavior (characterization tests)
2. Document edge cases found in code
3. Establish baseline before refactoring

No refactoring yet. Tests first.
```

**Step 3: Refactor-or-Remove Decision**
```markdown
AI Prompt (Archaeology Decision):
Given:
- Reverse-engineered spec
- Test coverage
- Dependency analysis

Recommend:
A) KEEP + REFACTOR (core business logic, used)
B) REMOVE (duplicate, unused, obsolete)
C) MERGE (functionality exists elsewhere)

Provide evidence for recommendation.
```

#### DefinitieAgent Example: Archaeology Mode

**Target**: `/src/services/definition_orchestrator.py` (legacy V1, 1000+ lines)

**Archaeology Prompt**:
```
Analyze src/services/definition_orchestrator.py

As software archaeologist:
1. Purpose: Orchestrate definition generation (V1 architecture)
2. Inputs: GenerationRequest, session_state, config
3. Outputs: LegacyGenerationResult
4. Business Logic:
   - Prompts construction via PromptServiceV1
   - AI call via AIServiceV1
   - Validation via ValidationService
   - Repository storage
5. Dependencies: 9 services (AI, Prompt, Validation, Repository, etc.)
6. Risk: MEDIUM - V2 replacement exists (definition_orchestrator_v2.py)

Recommendation: REMOVE (V1→V2 migration complete as of 19-09-2025)
Evidence: refactor-log.md shows V1 elimination, no V1 references remain
```

**Outcome**: File removed 19-09-2025 (per refactor-log.md)

---

### 2.2 CONSTRAINT-AWARE REFACTORING (Within Existing Architecture)

**When to Use**: Refactoring existing modules without breaking architecture

**Original Vibe**: Architect First (Tip 8) - Design architecture before code
**Brownfield Adaptation**: Architecture-Constrained Refactoring - Improve within boundaries

#### Constraint-Aware Workflow

**Step 1: Architecture Constraint Mapping**
```markdown
AI Prompt (Constraint Mapping):
Analyze current architecture for [MODULE]:

Immutable Constraints (CANNOT CHANGE):
- ServiceContainer DI pattern
- Existing module interfaces (public APIs)
- Database schema (unless migration planned)
- Session state structure (UI dependencies)

Mutable Areas (CAN REFACTOR):
- Internal implementation
- Private methods
- Helper functions
- Code organization

Output: Refactoring boundary map
```

**Step 2: Refactor Proposal (Within Constraints)**
```markdown
AI Prompt (Constrained Refactor):
Refactor [MODULE] within these constraints:
[PASTE CONSTRAINT MAP]

Apply Vibe Tip 13 (Refactor-First):
- Remove duplication
- Add docstrings
- Improve readability
- Modularize internal functions

PRESERVE:
- Public API signatures
- ServiceContainer wiring
- Business logic behavior
- Test compatibility

Output: Refactored code + migration notes
```

**Step 3: Regression Validation**
```markdown
AI Prompt (Regression Shield - Vibe 4.3):
Regression audit for refactored [MODULE]:

1. Are all existing tests still passing?
2. Are edge cases preserved?
3. Are performance characteristics similar?
4. Are error messages unchanged (or improved)?

Create additional regression tests if gaps found.
```

#### DefinitieAgent Example: Constraint-Aware Refactoring

**Target**: `src/services/prompts/modules/expertise_module.py` (200 lines)

**Constraint Map**:
```markdown
IMMUTABLE:
- Inherits from BasePromptModule
- execute(context: ModuleContext) → ModuleOutput signature
- Registered in PromptOrchestrator
- Metadata propagation via ModuleOutput

MUTABLE:
- Internal prompt building logic
- Helper functions
- String formatting
- Documentation
```

**Refactor Proposal**:
```python
# BEFORE: Monolithic execute() method (80 lines)
def execute(self, context):
    # 80 lines of prompt building inline

# AFTER: Modular with Vibe Tip 5 (Break the Monolith)
def execute(self, context):
    expertise_prompt = self._build_expertise_section(context)
    examples = self._build_examples_section(context)
    guidelines = self._build_guidelines_section(context)
    return ModuleOutput(
        content=f"{expertise_prompt}\n\n{examples}\n\n{guidelines}",
        metadata={"sections": 3}
    )

def _build_expertise_section(self, context):
    """Vibe Tip 10: Force Documentation Inline"""
    # 20 lines - focused responsibility

def _build_examples_section(self, context):
    # 20 lines - focused responsibility

def _build_guidelines_section(self, context):
    # 20 lines - focused responsibility
```

**Regression Test**:
```python
def test_refactored_expertise_module_produces_identical_output():
    """Vibe 4.3: Regression Shield - ensure refactor is behavior-preserving"""
    context = ModuleContext(begrip="arrest", ...)

    # Golden output from before refactor
    expected_output = load_golden_output("expertise_module_arrest.txt")

    actual_output = ExpertiseModule().execute(context).content

    assert actual_output == expected_output  # Byte-for-byte identical
```

---

### 2.3 SURGICAL MODERNIZATION (Aggressive Refactoring Without Compatibility)

**When to Use**: DefinitieAgent's "no backwards compatibility" policy allows aggressive changes

**Original Vibe**: Refactor-First (Tip 13) - Gradual, safe refactoring
**Brownfield Adaptation**: Surgical Strike Refactoring - Replace entire subsystems

#### Surgical Modernization Workflow

**Step 1: Business Logic Extraction**
```markdown
AI Prompt (Business Logic Archaeology):
Extract business logic from legacy [MODULE]:

1. **Core Business Rules**: What domain knowledge is embedded?
   - Validation rules
   - Calculation formulas
   - Domain constraints
   - Decision logic

2. **Configuration**: What is configurable vs hardcoded?

3. **Edge Cases**: What special handling exists?

Output: Business Knowledge Document (preserve before surgery)
```

**Step 2: Modern Replacement Design**
```markdown
AI Prompt (Surgical Design):
Design modern replacement for [MODULE]:

Preserve (from Business Logic Document):
- All business rules
- Edge case handling
- Domain knowledge

Modernize:
- Architecture pattern (use V2 patterns)
- Type hints (Python 3.11+)
- Error handling (no bare except)
- Logging (structured logging)
- Tests (pytest, 95% coverage)

No compatibility with old code required.
Output: Modern architecture + implementation plan
```

**Step 3: Atomic Cutover**
```markdown
AI Prompt (Atomic Cutover Plan):
Plan atomic cutover from old [MODULE] to new:

1. Parallel implementation (new code alongside old)
2. Feature flag for gradual rollout
3. Cutover script (update all imports)
4. Rollback plan (if new code fails)
5. Delete old code (after validation)

Output: Cutover checklist
```

#### DefinitieAgent Example: Surgical Modernization

**Target**: V1 → V2 Architecture Migration (completed 19-09-2025)

**Business Logic Extraction** (from refactor-log.md):
```markdown
V1 Business Logic to Preserve:
1. Validation orchestration (45 rules)
2. Prompt building (16 modules)
3. Context flow (3 context fields: org/jur/wet)
4. Definition generation workflow
5. Error handling patterns

V1 Technical Debt to Remove:
- Session state coupling in services
- Fallback methods (_get_legacy_*)
- Dual V1/V2 code paths
- Backwards compatibility layers
```

**Modern V2 Architecture** (designed with Vibe Tip 8: Architect First):
```markdown
V2 Architecture:
- ServiceContainer DI (dependency injection)
- Stateless services (no st.session_state in business logic)
- ValidationOrchestratorV2 (45 rules, modular)
- PromptOrchestrator (16 modules, dependency resolution)
- DefinitionGeneratorContext (canonical context structure)
- ModularValidationService (category-based rules)
```

**Atomic Cutover** (executed 19-09-2025):
```bash
# Step 1: Remove legacy fallback methods (definition_orchestrator_v2.py)
- _get_legacy_validation_service()  # REMOVED (69 lines)
- _get_legacy_cleaning_service()    # REMOVED
- _get_legacy_repository()          # REMOVED

# Step 2: Delete V1 service files
rm src/services/ai_service.py                 # V1 AI service
rm src/services/definition_orchestrator.py    # V1 orchestrator

# Step 3: Update all imports (ServiceContainer only uses V2)
# No backwards compatibility code - single-user app allows this

# Step 4: Validate (verification script)
./scripts/testing/verify-v2-migration.sh
# ✅ Zero V1 symbol references remaining
# ✅ All Python files compile successfully
# ✅ No startup warnings
```

**Outcome**: V1 architecture completely eliminated, 1069 lines of legacy code removed

**Vibe Principle Applied**: Tip 13 (Refactor-First) + No Backwards Compatibility Policy = Surgical Modernization

---

### 2.4 HYBRID FEATURE DEVELOPMENT (Mixed Greenfield + Brownfield)

**When to Use**: Features that are 20-80% complete (neither fully done nor fully new)

**Original Vibe**: 8-Step Method (complete new feature workflow)
**Brownfield Adaptation**: Completion-Aware Workflow (skip completed steps)

#### Hybrid Feature Workflow

**Step 1: Feature Completion Assessment**
```markdown
AI Prompt (Completion Audit):
Assess completion status for [EPIC/US-XXX]:

For each component:
- Specification: 0% / 50% / 100%
- Architecture: 0% / 50% / 100%
- Implementation: 0% / 50% / 100%
- Tests: 0% / 50% / 100%
- Documentation: 0% / 50% / 100%

Output: Completion matrix + recommended workflow
```

**Step 2: Adaptive Workflow Selection**
```markdown
Completion % → Workflow:

0-20% complete:     Use Greenfield Vibe (8-Step or 5-Step PM)
20-50% complete:    Use Hybrid (skip spec, architecture; focus on implementation)
50-80% complete:    Use Polishing Vibe (Tips 18-21: Auto-Polish, Self-Healing)
80-100% complete:   Use Incremental Vibe (minor enhancements only)
```

**Step 3: Gap-Driven Prompts**
```markdown
AI Prompt (Gap Filling):
Feature [US-XXX] is [X]% complete.

Gaps identified:
1. [Component A] is missing
2. [Component B] exists but needs refactoring
3. [Component C] is complete but untested

For each gap:
- Apply appropriate Vibe technique
- Preserve existing work
- Maintain consistency with completed parts

Output: Gap-specific implementation plan
```

#### DefinitieAgent Example: Hybrid Feature Development

**Target**: EPIC-016 (Beheer & Configuratie Console) - 30% complete

**Completion Audit**:
```markdown
EPIC-016 Status:

US-181 (UI Skelet): 80% - Layout exists, needs refinement
US-182 (Gate Policy): 90% - Backend done, UI integration needed
US-183 (Validatieregels): 50% - CRUD exists, hot-reload missing
US-184 (Contextopties): 20% - Design only, no implementation
US-185 (Audit): 10% - Database tables exist, UI missing
US-186 (Import/Export): 0% - Not started
US-187 (Autorisatie): 0% - Not started

Overall: 30% complete (mixed state)
```

**Adaptive Workflow**:
```markdown
US-181 (80% complete) → Use Vibe Tip 18 (Auto-Polish):
  Prompt: "Polish UI layout for consistency, accessibility, and UX"

US-182 (90% complete) → Use Vibe Tip 21 (Continuous Polish):
  Prompt: "Integrate gate policy UI, add edge case handling, polish UX"

US-183 (50% complete) → Use Hybrid Vibe (Implementation Focus):
  Prompt: "Add hot-reload feature to existing CRUD. Preserve current API."

US-184 (20% complete) → Use Greenfield Vibe (5-Step PM):
  Prompt: "Complete PM framework for context options: problem, stories, requirements"

US-185/186/187 (0-10% complete) → Use Greenfield Vibe (8-Step):
  Prompt: "Start from spec: fleshing out → architecture → implementation"
```

**Gap-Driven Implementation (US-183 Example)**:
```python
# EXISTING (50% complete): CRUD for validation rules
class ValidationRuleRepository:
    def create_rule(self, rule): ...  # ✅ Done
    def read_rule(self, id): ...       # ✅ Done
    def update_rule(self, rule): ...   # ✅ Done
    def delete_rule(self, id): ...     # ✅ Done

# GAP: Hot-reload missing
# Vibe Approach: Extend existing architecture, don't rebuild

# AI Prompt (Gap-Specific):
"""
Extend ValidationRuleRepository with hot-reload capability:

PRESERVE:
- Existing CRUD methods
- Database schema
- Repository interface

ADD:
- reload_rules() method
- Cache invalidation
- Event notification for config changes

Use existing RuleCache pattern (US-202 reference).
Apply Vibe Tip 12 (Modularity Pact): Keep cache separate from repository.
"""

# IMPLEMENTATION:
class ValidationRuleRepository:
    # Existing methods unchanged...

    def reload_rules(self):
        """Vibe Tip 10: Force Documentation Inline"""
        # Invalidate cache
        RuleCache.invalidate()
        # Notify services
        EventBus.publish("rules_reloaded")
        # Return new rule set
        return self.read_all_rules()
```

---

## 3. Brownfield-Specific Vibe Coding Techniques

### 3.1 Legacy Code Patterns → Vibe Adaptations

| Legacy Code Smell | Traditional Vibe | Brownfield Vibe Adaptation |
|-------------------|------------------|---------------------------|
| **God Object** (1500+ line files) | Tip 5: Break the Monolith | Archaeology → Extract Module → Modular Refactor |
| **Duplicate Code** (45 validator files) | Tip 13: Refactor-First | Template Method Pattern + BaseValidator |
| **No Documentation** (150 unused files) | Tip 10: Force Documentation | Reverse-Engineer Spec (Archaeology Mode) |
| **Tight Coupling** (session state in services) | Tip 12: Modularity Pact | Dependency Injection + Adapter Pattern |
| **No Tests** (legacy modules) | Tip 15: Add Test Harness | Characterization Tests → Refactor → Unit Tests |
| **Performance Issues** (6x service init) | Not addressed | Cache + Singleton (US-202 pattern) |
| **Contradictory Prompts** (7250 tokens) | Tip 18: Auto-Polish | Consolidation + Deduplication (prompt-refactoring/) |

### 3.2 DefinitieAgent-Specific Anti-Patterns and Vibe Solutions

#### Anti-Pattern 1: DRY Misinterpretation (God Object Helpers)

**Problem** (from CLAUDE.md):
```python
# VERBODEN PATTERN: dry_helpers.py (catch-all God Object)
def ensure_list(x): ...
def safe_dict_get(d, k): ...
def validate_input(x): ...
# 50+ unrelated functions in one file
```

**Vibe Solution** (Tip 12: Modularity Pact + Tip 5: Break the Monolith):
```markdown
AI Prompt (Anti-God Object Refactoring):
Split dry_helpers.py into focused modules:

Modularity Pact (Vibe Tip 12):
- utils/type_helpers.py → ensure_list, ensure_dict
- utils/dict_helpers.py → safe_dict_get, merge_dicts
- utils/validation_helpers.py → validate_input, sanitize

Each module: one responsibility, clear domain.
No vague "helpers" modules.

Apply Vibe Tip 10: Add docstrings explaining WHY each utility exists.
```

#### Anti-Pattern 2: Session State Leakage (ServiceContainer Confusion)

**Problem** (from CLAUDE.md):
```python
# VERBODEN: Direct st.session_state access in services
class AIService:
    def generate(self):
        context = st.session_state.get('context')  # ❌ UI coupling
```

**Vibe Solution** (Tip 12: Modularity Pact + Clean Architecture):
```markdown
AI Prompt (Session State Decoupling):
Refactor AIService to be stateless:

Modularity Pact (core vs ui separation):
- AIService: stateless, takes context as parameter
- SessionStateManager: ONLY module touching st.session_state
- UI Layer: bridges session state → service calls

Architecture:
UI → SessionStateManager.get_value('context')
  → AIService.generate(context)  # Pure function

Apply Vibe Tip 9 (Plan the Data Flow):
Input (UI) → SessionState → Service (stateless) → Output → SessionState → UI
```

#### Anti-Pattern 3: Prompt Duplication (7250 Tokens with 83% Overlap)

**Problem** (from refactor-log.md):
```
logs/prompt.txt:
- 42 "Start niet met..." rules (duplicated)
- ARAI-02 rule repeated 3x with minor variations
- Ontologie explanation triplicated
- Contradictory haakjes rules

Total: 553 lines (~7250 tokens)
Target: <150 lines (<2000 tokens)
```

**Vibe Solution** (Tip 18: Auto-Polish Loop + Tip 17: Synthesis):
```markdown
AI Prompt (Prompt Consolidation):
Refactor prompt.txt using Vibe Tip 18 (Auto-Polish):

1. Pattern Consolidation:
   - 42 "start niet met" → 1 pattern rule + examples

2. Rule Deduplication:
   - ARAI-02 + ARAI-02SUB1 + ARAI-02SUB2 → 1 unified rule

3. Contradiction Resolution:
   - Haakjes rules (lines 14 vs 53-61) → 1 clear policy

4. Synthesis (Vibe Tip 17):
   - Combine best elements of 3 ontology explanations → 1 clear section

5. Token Optimization:
   - Target: <2000 tokens (72% reduction)
   - Hierarchical structure with priorities

Output: Refactored prompt.txt (token-optimized, conflict-free)
```

**Outcome** (from refactor-log.md):
```
Achieved: 72% token reduction (7250 → <2000)
Techniques: Pattern consolidation, rule deduplication, contradiction resolution
```

---

## 4. Integration with Existing DefinitieAgent Workflows

### 4.1 Mapping Vibe Coding to DefinitieAgent EPIC/US Structure

**Problem**: Vibe Coding uses different terminology (Epic → Feature → Task) vs DefinitieAgent (EPIC → US → Bug)

**Solution**: Hybrid mapping with precedence rules

| Vibe Coding Level | DefinitieAgent Equivalent | Workflow Adaptation |
|-------------------|---------------------------|---------------------|
| **Epic** (business goal) | **EPIC-XXX** | Use Vibe 1.2 (PM Framework) for Epic planning |
| **Feature** (deliverable) | **US-XXX** (User Story) | Use Vibe 8-Step or 5-Step PM for stories |
| **Task** (action item) | **Subtasks in US-XXX.md** | Use Vibe Tip 5 (Break the Monolith) for task breakdown |
| **Bug** | **BUG-XXX** (within US directory) | Use Vibe Tip 14 (Debug Detective) for root cause |
| **Refactor** | **(Implicit in US or standalone)** | Use Vibe Tip 13 (Refactor-First) workflow |

#### Example: EPIC-016 with Vibe Workflows

**EPIC-016**: Beheer & Configuratie Console (7 user stories)

**Vibe PM Framework Application**:
```markdown
AI Prompt (EPIC-016 PM Analysis):
Apply Vibe 1.2 (PM Framework) to EPIC-016:

1. Probleem: Configuratiewijzigingen vereisen code-deploy (traag, risicovol)
2. Doelgroep: Beheerders (technisch, niet-developers)
3. Use-cases:
   a) Gate-policy aanpassen zonder code wijziging
   b) Validatieregels gewichten bijstellen in UI
   c) Audit trail voor compliance
4. Kritische output:
   - UI-tab "Beheer" met 6 subsections
   - Hot-reload zonder app-restart
   - Database-backed config met versies
5. Risico's:
   - Onjuiste config blokkeert vaststellen
   - Cache vs DB inconsistentie
   - Te veel toggles → onvoorspelbaar gedrag

Output: EPIC-016.md (PM Framework section added)
```

**Vibe 8-Step Application** (for US-182: Gate Policy CRUD):
```markdown
US-182 (Gate Policy Beheer) Workflow:

Step 1 (Fleshing Out): ✅ Done - EPIC-016.md has spec
Step 2 (High Level): ✅ Done - Architecture: GatePolicyService + UI CRUD
Step 3 (Feature Stories): ✅ Done - US-182.md
Step 4 (State & Style): ⏸ Skip - Streamlit UI exists
Step 5 (Tech Spec): 🔄 In Progress - Need API contract
Step 7 (Planner): ⏸ Pending - Need implementation roadmap
Step 8 (AI Engineer): ⏸ Pending - Implementation phase

Current Status: 40% complete (steps 1-3 done, 5-8 pending)
Recommended: Apply Hybrid Vibe (skip UI design, focus on backend + integration)
```

### 4.2 Vibe Coding + DefinitieAgent Refactoring Policy

**DefinitieAgent Policy** (from CLAUDE.md):
```
⚠️ REFACTOREN, GEEN BACKWARDS COMPATIBILITY
- GEEN BACKWARDS COMPATIBILITY CODE
- Dit is een single-user applicatie, NIET in productie
- REFACTOR code met behoud van businesskennis en logica
- Analyseer eerst wat code doet voordat je vervangt
- Extraheer businessregels en validaties tijdens refactoring
```

**Vibe Coding Alignment**:

| Vibe Principle | DefinitieAgent Policy | Alignment | Notes |
|----------------|----------------------|-----------|-------|
| Refactor-First (Tip 13) | ✅ REFACTOR code | Perfect | Both prioritize refactoring |
| Safe Incremental Changes | ❌ NO backwards compat | Conflict | DefinitieAgent more aggressive |
| Business Logic Preservation | ✅ Behoud businesskennis | Perfect | Both preserve domain logic |
| Analyze Before Replace | ✅ Analyseer eerst | Perfect | Archaeology Mode supports this |
| Extract Business Rules | ✅ Extraheer businessregels | Perfect | Document during refactor |

**Brownfield Vibe Coding Adaptation**:
```markdown
Enhanced Vibe Tip 13 (Refactor-First) for DefinitieAgent:

1. Archaeology Mode (extract business logic)
2. Document business rules (preserve knowledge)
3. Aggressive Refactoring (no backwards compatibility)
4. Surgical Modernization (replace entire subsystems)
5. Regression Shield (tests ensure business logic preserved)

NO:
- Feature flags for gradual rollout (single-user app)
- Deprecation warnings (just delete old code)
- Migration paths (clean cutover)
```

### 4.3 Canonical Locations for Vibe Coding Artifacts

**Problem**: Where to store Vibe Coding deliverables in DefinitieAgent's structure?

**Solution**: Extend CANONICAL_LOCATIONS.md with Vibe-specific paths

| Vibe Artifact | DefinitieAgent Location | Notes |
|---------------|------------------------|-------|
| **Mini-Spec** (1.1) | `docs/backlog/EPIC-XXX/US-XXX/US-XXX.md` | Frontmatter + sections |
| **PM Framework Output** (1.2) | `docs/backlog/EPIC-XXX/EPIC-XXX.md` | PM analysis in Epic doc |
| **Architecture Diagrams** (Tip 8) | `docs/architectuur/diagrams/` | Mermaid diagrams |
| **Refactoring Plans** (Tip 13) | `docs/planning/` | Refactoring roadmaps |
| **Archaeology Reports** | `docs/analyses/legacy-code/` | Reverse-engineered specs |
| **Vibe Prompts** (Templates) | `docs/architectuur/prompt-refactoring/vibe-prompts/` | Reusable prompt library |
| **Polish Reports** (Tip 18) | `docs/refactor-log.md` | Append to existing log |
| **Test Harnesses** (Tip 15) | `tests/` (unit/integration/smoke) | Standard test locations |

**Example Canonical Structure**:
```
docs/
├── backlog/
│   └── EPIC-016/
│       ├── EPIC-016.md                    # Includes Vibe PM Framework (1.2)
│       └── US-182/
│           ├── US-182.md                  # Includes Vibe Mini-Spec (1.1)
│           └── BUG-XXX/
│               └── BUG-XXX.md             # Vibe Debug Detective (Tip 14) analysis
├── architectuur/
│   ├── diagrams/
│   │   └── epic-016-architecture.mmd      # Vibe Architect First (Tip 8)
│   └── prompt-refactoring/
│       └── vibe-prompts/
│           ├── archaeology-mode.md        # Reusable prompt templates
│           ├── constraint-aware-refactor.md
│           └── surgical-modernization.md
├── analyses/
│   └── legacy-code/
│       └── definition-orchestrator-archaeology.md  # Archaeology Mode output
├── planning/
│   └── us-182-refactoring-plan.md         # Vibe Tip 13 plan
└── refactor-log.md                         # Vibe Tip 18 polish reports
```

---

## 5. Incremental Adoption Roadmap

### 5.1 Phase 1: Foundation (Week 1-2) - Archaeology & Documentation

**Goal**: Understand legacy code, document existing behavior

**Vibe Techniques**:
- **Archaeology Mode** (custom) - Reverse-engineer specs for 10 legacy modules
- **Tip 10: Force Documentation Inline** - Add docstrings to undocumented code
- **Tip 14: Debug Detective** - Identify 5 high-risk legacy modules

**Deliverables**:
- [ ] 10 Archaeology Reports (docs/analyses/legacy-code/)
- [ ] Prioritized refactoring backlog
- [ ] Legacy code risk matrix

**Success Metrics**:
- All core modules have reverse-engineered specs
- 80% of legacy code has docstrings
- Team understands what can be safely deleted

**AI Prompts** (Phase 1):
```markdown
Prompt 1: Legacy Module Inventory
"List all Python files in src/ and categorize:
- Core (actively used, has tests)
- Peripheral (used, no tests)
- Zombie (unused, candidate for removal)
Output: CSV with usage analysis"

Prompt 2: Archaeology on Top 10 Modules
"For each of these 10 modules:
1. Reverse-engineer Mini-Spec
2. Document business logic
3. Identify dependencies
4. Assess removal risk
Output: 10 Archaeology Reports"

Prompt 3: Docstring Generation
"Add comprehensive docstrings to all functions in [MODULE]:
- Purpose (business goal)
- Parameters (types, constraints)
- Returns (types, edge cases)
- Edge cases / limitations
Use Google-style docstrings"
```

### 5.2 Phase 2: Refactoring (Week 3-6) - Constraint-Aware Modernization

**Goal**: Refactor legacy code within existing architecture constraints

**Vibe Techniques**:
- **Constraint-Aware Refactoring** (custom) - Modernize without breaking APIs
- **Tip 13: Refactor-First** - Clean before adding features
- **Tip 12: Modularity Pact** - Enforce separation (core/ui/logging)
- **Tip 15: Add Test Harness** - 95% coverage on refactored modules

**Deliverables**:
- [ ] 5 modules refactored (modular, documented, tested)
- [ ] God Object helpers split into focused utilities
- [ ] Session state decoupled from services
- [ ] Regression tests for all refactored code

**Success Metrics**:
- Cyclomatic complexity <10 for all refactored functions
- 95% test coverage on refactored modules
- Zero session state access in business logic
- 50% reduction in file size for monolithic modules

**AI Prompts** (Phase 2):
```markdown
Prompt 4: Constraint Mapping
"Map refactoring constraints for [MODULE]:
IMMUTABLE (cannot change):
- Public API signatures
- ServiceContainer wiring
- Database schema
MUTABLE (can refactor):
- Internal implementation
- Private methods
- Code organization
Output: Constraint map"

Prompt 5: Modular Refactoring
"Refactor [MODULE] within constraints:
[PASTE CONSTRAINT MAP]
Apply:
- Vibe Tip 5: Break into focused functions (<50 lines)
- Vibe Tip 10: Docstrings for all public methods
- Vibe Tip 12: Separate core/ui/logging
Output: Refactored code + tests"

Prompt 6: Regression Testing
"Create regression test suite for refactored [MODULE]:
- Characterization tests (current behavior baseline)
- Edge case tests (from archaeology report)
- Performance tests (<200ms per operation)
Output: pytest test suite (95% coverage)"
```

### 5.3 Phase 3: Surgical Modernization (Week 7-10) - V1→V2 Completions

**Goal**: Complete remaining V1→V2 migrations, aggressive refactoring

**Vibe Techniques**:
- **Surgical Modernization** (custom) - Replace entire subsystems
- **Tip 8: Architect First** - Design V2 replacements
- **Vibe 4.3: Regression Shield** - Protect against zombie bugs
- **Tip 17: Synthesis** - Combine best elements of V1 + V2

**Deliverables**:
- [ ] All V1 code eliminated (100% V2 architecture)
- [ ] 150 unused files deleted
- [ ] Modernized architecture document updated
- [ ] Rollback plan (if needed)

**Success Metrics**:
- Zero V1 code references
- 1000+ lines of legacy code removed
- All tests passing on V2-only codebase
- Performance ≥ V1 baseline

**AI Prompts** (Phase 3):
```markdown
Prompt 7: Business Logic Extraction
"Extract business logic from V1 [MODULE]:
1. Core business rules (preserve)
2. Configuration (move to ConfigManager)
3. Edge cases (document)
4. Domain knowledge (capture in comments)
Output: Business Knowledge Document"

Prompt 8: V2 Replacement Design
"Design V2 replacement for V1 [MODULE]:
PRESERVE (from Business Logic Document):
- All business rules
- Edge case handling
MODERNIZE:
- ServiceContainer DI
- Type hints (Python 3.11+)
- Structured logging
- 95% test coverage
Output: V2 architecture + implementation plan"

Prompt 9: Atomic Cutover
"Plan atomic cutover from V1 to V2 [MODULE]:
1. Parallel implementation (both V1 + V2 exist)
2. Feature flag (gradual rollout)
3. Import update script (switch all references)
4. Validation (tests pass)
5. Delete V1 code
Output: Cutover checklist"
```

### 5.4 Phase 4: Feature Completion (Week 11-16) - Hybrid Development

**Goal**: Complete 26% → 80% feature completion using hybrid workflows

**Vibe Techniques**:
- **Hybrid Feature Development** (custom) - Completion-aware workflows
- **Vibe 8-Step** (for 0-20% complete features)
- **Vibe 5-Step PM** (for architectural features)
- **Vibe Tip 18-21: Polish Loops** (for 80-100% complete features)

**Deliverables**:
- [ ] 20 user stories completed (from 23 → 43)
- [ ] 50% → 80% feature completion
- [ ] All EPIC-016 stories done
- [ ] Documentation updated

**Success Metrics**:
- Feature completion: 80%+
- Validation pass rate: 95%+ (45 rules)
- Definition generation time: <5 seconds
- User satisfaction: High (single user, but qualitative feedback)

**AI Prompts** (Phase 4):
```markdown
Prompt 10: Completion Audit
"Assess completion for EPIC-016:
For each US-XXX:
- Spec: [0%/50%/100%]
- Architecture: [0%/50%/100%]
- Implementation: [0%/50%/100%]
- Tests: [0%/50%/100%]
- Docs: [0%/50%/100%]
Output: Completion matrix + recommended workflows"

Prompt 11: Adaptive Workflow Selection
"For US-XXX ([X]% complete):
IF 0-20%: Use Vibe 8-Step (greenfield)
IF 20-50%: Use Hybrid (skip spec/architecture)
IF 50-80%: Use Polish (Vibe Tip 18-21)
IF 80-100%: Use Incremental (minor enhancements)
Output: Customized workflow for this story"

Prompt 12: Gap Filling
"US-XXX is [X]% complete with gaps:
1. [Component A] missing
2. [Component B] needs refactor
3. [Component C] needs tests
For each gap:
- Apply appropriate Vibe technique
- Preserve existing work
- Maintain consistency
Output: Gap-specific implementation plan"
```

### 5.5 Phase 5: Continuous Improvement (Ongoing) - Polish & Scale

**Goal**: Maintain quality, polish existing features, scale to more users

**Vibe Techniques**:
- **Vibe Tip 18: Auto-Polish Loop** - Weekly code quality passes
- **Vibe Tip 19-21: Self-Healing** - Proactive bug prevention
- **Vibe 4.3: Regression Shield** - Protect against zombie bugs
- **Vibe 4.4: Continuous AI Co-Founder** - AI-assisted reviews

**Deliverables**:
- [ ] Monthly code quality reports
- [ ] Automated polish scripts
- [ ] Self-healing validation checks
- [ ] AI-assisted code reviews

**Success Metrics**:
- Code quality: Ruff score 9.5/10
- Test coverage: 85%+
- Performance: <5s definition generation
- Technical debt: Controlled backlog

**AI Prompts** (Phase 5):
```markdown
Prompt 13: Weekly Polish Pass
"Perform Vibe Tip 18 (Auto-Polish) on codebase:
1. Readability: Are variable names clear?
2. Consistency: Do naming conventions match?
3. Documentation: Are docstrings complete?
4. Error handling: Are edge cases covered?
Output: Polish report + automated fixes"

Prompt 14: Self-Healing Audit
"Vibe Tip 19 (Self-Healing Code) audit:
1. Unused variables/imports
2. Vulnerable patterns (bare except, hardcoded secrets)
3. TODO comments → Issues
4. Performance bottlenecks
Output: Self-healing checklist + auto-fix script"

Prompt 15: Regression Shield
"Vibe 4.3 (Regression Shield) check:
1. Are all edge cases from previous bugs still covered?
2. Are old tests still valid?
3. Have new features broken existing functionality?
Output: Regression test suite + coverage report"
```

---

## 6. Specific DefinitieAgent Use Cases

### 6.1 Use Case 1: Refactoring God Object (definition_generator_tab.py - 1490 lines)

**Problem**: Monolithic UI component with cyclomatic complexity 64

**Vibe Techniques**:
- Archaeology Mode (reverse-engineer responsibilities)
- Tip 5: Break the Monolith
- Tip 12: Modularity Pact (core/ui separation)
- Tip 13: Refactor-First

**Step-by-Step Workflow**:

**Step 1: Archaeology**
```markdown
AI Prompt:
Analyze src/ui/components/definition_generator_tab.py (1490 lines)

As software archaeologist:
1. Identify distinct responsibilities (business logic vs UI)
2. Extract reusable components
3. Find duplication
4. Identify core vs peripheral code

Output: Responsibility map
```

**Expected Output**:
```markdown
Responsibility Map (definition_generator_tab.py):

1. Definition Generation Logic (300 lines) - CORE
   - Build generation request
   - Call UnifiedDefinitionGenerator
   - Handle response

2. UI Rendering (600 lines) - UI
   - Input forms (begrip, context)
   - Results display
   - Validation feedback

3. State Management (200 lines) - UI
   - Session state updates
   - Cache management

4. Helper Functions (390 lines) - PERIPHERAL
   - String formatting
   - Data transformations
   - Validation helpers

Recommendation: Extract 3 modules:
- definition_generator_service.py (core logic)
- definition_results_renderer.py (UI component)
- definition_form_helpers.py (utilities)
```

**Step 2: Modular Refactoring**
```markdown
AI Prompt (Vibe Tip 5 + 12):
Refactor definition_generator_tab.py into 3 focused modules:

1. definition_generator_service.py (Vibe Tip 12: Core)
   - Stateless business logic
   - No UI dependencies
   - 95% test coverage

2. definition_results_renderer.py (Vibe Tip 12: UI)
   - Pure rendering logic
   - Consumes service output
   - No business logic

3. definition_form_helpers.py (Vibe Tip 12: Utilities)
   - Reusable UI helpers
   - No state mutations

Preserve ALL business logic. Apply Vibe Tip 10 (docstrings).
```

**Step 3: Regression Testing**
```markdown
AI Prompt (Vibe 4.3: Regression Shield):
Create characterization tests for original definition_generator_tab.py:

1. Capture current behavior (golden outputs)
2. Test refactored version produces identical results
3. Performance benchmarks (must be ≥ original)

Output: pytest regression suite
```

**Expected Outcome**:
- 1490 lines → 3 files (400 + 600 + 200 = 1200 lines, 20% reduction)
- Cyclomatic complexity: 64 → <10 per function
- Test coverage: 0% → 95%
- Maintainability: Significantly improved

---

### 6.2 Use Case 2: Prompt Token Optimization (7250 → <2000 tokens)

**Problem**: Prompt.txt has 7250 tokens with 83% duplication

**Vibe Techniques**:
- Tip 17: Synthesis (combine best elements)
- Tip 18: Auto-Polish Loop (token optimization)
- Custom: Contradiction Resolution

**Step-by-Step Workflow**:

**Step 1: Analysis**
```markdown
AI Prompt:
Analyze logs/prompt.txt (553 lines, 7250 tokens)

Identify:
1. Duplicate patterns (e.g., "start niet met...")
2. Near-duplicate rules (e.g., ARAI-02 variants)
3. Contradictions (e.g., haakjes rules)
4. Redundancy (e.g., ontologie explanation repeated 3x)

Output: Duplication matrix
```

**Expected Output**:
```markdown
Duplication Analysis:

1. Pattern Duplication (432-473): 42 "start niet met" rules
   - 400 tokens wasted
   - Solution: 1 pattern rule + 3 examples

2. Near-Duplicate Rules (119-140): ARAI-02 family
   - ARAI-02, ARAI-02SUB1, ARAI-02SUB2 (80% similar)
   - Solution: Unified rule with variations

3. Contradictions (14 vs 53-61): Haakjes usage
   - Line 14: "Geen haakjes voor toelichtingen"
   - Line 53-61: "Haakjes WEL voor afkortingen"
   - Solution: Clarify scope (toelichtingen ≠ afkortingen)

4. Redundancy (66-74, 75-100, 202-204): Ontologie
   - Explained 3x in different sections
   - Solution: 1 comprehensive explanation early
```

**Step 2: Synthesis**
```markdown
AI Prompt (Vibe Tip 17: Synthesis):
Synthesize prompt.txt using best elements:

1. Consolidate 42 "start niet met" → 1 pattern + examples
2. Unify ARAI-02 variants → 1 flexible rule
3. Resolve haakjes contradiction → 1 clear policy
4. Merge ontologie explanations → 1 comprehensive section

Target: <2000 tokens (72% reduction)
Structure: Hierarchical with priorities

Output: Optimized prompt.txt
```

**Step 3: Validation**
```markdown
AI Prompt (Validation):
Test optimized prompt.txt:

1. Generate 10 definitions using original prompt
2. Generate 10 definitions using optimized prompt
3. Compare outputs (should be identical or better)
4. Measure token usage (must be <2000)

Output: Comparison report
```

**Expected Outcome** (from refactor-log.md):
- 7250 tokens → <2000 tokens (72% reduction)
- 553 lines → ~150 lines
- Zero contradictions
- Improved clarity

**Actual Outcome**: Achieved (documented in refactor-log.md, 03-09-2025)

---

### 6.3 Use Case 3: EPIC-016 Feature Completion (30% → 100%)

**Problem**: EPIC-016 has 7 user stories in mixed states (0-90% complete)

**Vibe Techniques**:
- Hybrid Feature Development (custom)
- Completion-Aware Workflow Selection
- Vibe 8-Step (for new stories)
- Vibe Tip 18-21 (for polish)

**Step-by-Step Workflow**:

**Step 1: Completion Audit**
```markdown
AI Prompt:
Audit EPIC-016 completion status:

For each US (US-181 through US-187):
- Specification: [0/50/100%]
- Architecture: [0/50/100%]
- Implementation: [0/50/100%]
- Tests: [0/50/100%]
- Documentation: [0/50/100%]

Output: Completion matrix + recommended workflows
```

**Expected Output**:
```markdown
EPIC-016 Completion Matrix:

US-181 (UI Skelet):           80% [100/100/80/50/70]  → Polish workflow
US-182 (Gate Policy):         90% [100/100/90/80/80]  → Integration workflow
US-183 (Validatieregels):    50% [100/80/40/30/40]   → Hybrid workflow
US-184 (Contextopties):      20% [80/50/10/0/10]     → Greenfield workflow
US-185 (Audit):              10% [50/30/0/0/0]       → Greenfield workflow
US-186 (Import/Export):       0% [0/0/0/0/0]         → Greenfield workflow
US-187 (Autorisatie):         0% [0/0/0/0/0]         → Greenfield workflow

Overall: 30% complete
```

**Step 2: Adaptive Workflow Routing**
```markdown
For US-181 (80% complete) → Apply Vibe Tip 18 (Auto-Polish):
  "Polish UI layout: consistency, accessibility, responsive design"

For US-182 (90% complete) → Apply Integration Focus:
  "Integrate gate policy backend with UI, add edge case handling"

For US-183 (50% complete) → Apply Hybrid Workflow:
  "Complete hot-reload feature. Preserve existing CRUD API."

For US-184/185/186/187 (0-20% complete) → Apply Vibe 8-Step:
  "Start from spec: fleshing out → architecture → implementation"
```

**Step 3: Execution (US-183 Example - Hybrid)**
```markdown
AI Prompt (US-183 Hybrid Workflow):
US-183 is 50% complete:

DONE:
- CRUD operations for validation rules (create/read/update/delete)
- Database schema exists
- Repository layer implemented

GAPS:
- Hot-reload functionality missing
- Cache invalidation not implemented
- Event notification system absent

Apply Hybrid Vibe:
1. Skip Spec (already exists in EPIC-016.md)
2. Skip Architecture (design is done)
3. Focus on GAPS (hot-reload implementation)
4. Preserve existing code (no breaking changes)
5. Add tests for new functionality

Constraints:
- Use existing RuleCache pattern (US-202)
- Respect ValidationRuleRepository API
- Maintain ServiceContainer wiring

Output: Implementation plan for hot-reload
```

**Expected Outcome**:
- EPIC-016: 30% → 100% complete (7 user stories done)
- Mixed workflows applied appropriately
- Consistency maintained across stories
- Timeline: 4-6 weeks (vs 8-12 weeks with one-size-fits-all approach)

---

## 7. Anti-Patterns to Avoid

### 7.1 Brownfield-Specific Anti-Patterns

| Anti-Pattern | Description | Why It Fails in Brownfield | Correct Approach |
|--------------|-------------|---------------------------|------------------|
| **Greenfield Prompts on Legacy Code** | Using "Architect First" on existing modules | Ignores existing architecture constraints | Use Constraint-Aware Refactoring |
| **Spec-First on Undocumented Code** | Trying to write spec before understanding code | Specs will be wrong (no archaeology) | Use Archaeology Mode first |
| **Backwards Compatibility by Default** | Adding feature flags for all changes | Wastes time in single-user app | Use Surgical Modernization |
| **Monolithic Refactoring** | Refactor entire codebase at once | Too risky, hard to rollback | Use Incremental Adoption Roadmap |
| **Ignoring Business Logic** | Refactoring without understanding domain | Breaks production behavior | Use Business Logic Extraction first |
| **Tool-First, Problem-Second** | Applying Vibe because it's trendy | Doesn't address actual pain points | Use Problem-Driven Vibe Selection |
| **Documentation Debt** | Refactoring without updating docs | Technical debt accumulates | Use Tip 10: Force Documentation Inline |

### 7.2 DefinitieAgent-Specific Pitfalls

#### Pitfall 1: Applying UI-Focused Vibe to Backend-Heavy System

**Problem**: DefinitieAgent is 70% backend (services, validation, AI) and 30% UI (Streamlit tabs)

**Vibe Techniques to SKIP**:
- ❌ Chapter 3: Vibe Design Blueprint (4-zone UI pattern)
- ❌ Tip 20: Self-Healing UI (spacing, typography)
- ❌ Design Tokens (color, spacing tokens)
- ❌ UI Opzet workflow (design-first approach)

**Why**: DefinitieAgent has stable Streamlit UI. Focus on backend refactoring.

**Alternative**: Apply Vibe to backend patterns:
- ✅ Tip 12: Modularity Pact (core/ui/logging separation)
- ✅ Tip 9: Plan the Data Flow (service orchestration)
- ✅ Tip 8: Architect First (for new backend features)

#### Pitfall 2: Over-Documenting at Expense of Refactoring

**Problem**: Archaeology Mode can turn into "documentation paralysis"

**Symptoms**:
- 50-page archaeology reports
- Reverse-engineered specs that are never used
- Analysis without action

**Correct Approach**:
```markdown
Archaeology Report Template (Lean):

## Module: [NAME]
**Purpose**: [1 sentence]
**Business Logic**: [3-5 bullet points]
**Dependencies**: [List]
**Recommendation**: KEEP/REMOVE/MERGE

## Next Steps
1. [Action 1]
2. [Action 2]

Total: 1 page max
```

#### Pitfall 3: Refactoring Without Tests

**Problem**: DefinitieAgent has 60% test coverage, some modules have 0%

**Vibe Trap**: Tip 13 (Refactor-First) without Tip 15 (Add Test Harness)

**Correct Order**:
1. ✅ Archaeology (understand code)
2. ✅ Characterization Tests (capture current behavior)
3. ✅ Refactor (within test safety net)
4. ✅ Unit Tests (for refactored code)

**Never**: Refactor → Hope → Deploy

---

## 8. Success Metrics & KPIs

### 8.1 Brownfield Refactoring Metrics

| Metric | Baseline (Oct 2025) | Target (Week 16) | Measurement Method |
|--------|---------------------|------------------|-------------------|
| **Legacy Code Reduction** | 304 files | <200 files | File count in src/ |
| **Unused Files** | 150 files | 0 files | Archaeology Mode audit |
| **Code Duplication** | 45 duplicate validators | 1 BaseValidator + 45 implementations | Ruff duplicate detection |
| **Cyclomatic Complexity** | Max 64 (god object) | Max 10 per function | Radon complexity tool |
| **Test Coverage** | 60% | 85% | pytest --cov |
| **Documentation Coverage** | ~40% (estimate) | 90% | Docstring presence check |
| **Technical Debt Hours** | ~440 hours estimated | <100 hours | Refactor backlog size |

### 8.2 Feature Completion Metrics (Hybrid Development)

| Metric | Baseline | Target | Notes |
|--------|----------|--------|-------|
| **Overall Completion** | 26% (23/87 features) | 80% (70/87 features) | EPIC/US tracking |
| **EPIC-016 Completion** | 30% (2/7 stories) | 100% (7/7 stories) | Configuration console |
| **Average Story Velocity** | 3 features/sprint | 5 features/sprint | Hybrid workflows boost speed |
| **Definition Generation Time** | 8-12 seconds | <5 seconds | Performance optimization |
| **Validation Pass Rate** | 85% | 95% | 45 validation rules |

### 8.3 Code Quality Metrics (Vibe Polishing)

| Metric | Baseline | Target | Vibe Technique |
|--------|----------|--------|----------------|
| **Ruff Score** | 799 errors | <50 errors | Tip 18: Auto-Polish |
| **Naming Consistency** | ~70% | 95% | Tip 21: Continuous Polish |
| **Function Length** | Max 200 lines | Max 50 lines | Tip 5: Break the Monolith |
| **Module Cohesion** | Mixed (god objects) | High (single responsibility) | Tip 12: Modularity Pact |
| **Error Handling** | 8 bare except | 0 bare except | Tip 19: Self-Healing Code |

### 8.4 Brownfield-Specific Success Indicators

**Hard Metrics**:
- ✅ All V1 code eliminated (100% V2 architecture)
- ✅ Zero session state access in business logic services
- ✅ All "God Object" helpers split into focused modules
- ✅ 95% test coverage on refactored modules
- ✅ All legacy code has reverse-engineered specs (Archaeology Mode)

**Soft Metrics**:
- ✅ Team understands Vibe Coding methodology
- ✅ Vibe prompts reused across multiple features
- ✅ Refactoring velocity increases over time
- ✅ Technical debt backlog decreases weekly

---

## 9. Conclusion & Next Steps

### 9.1 Summary of Adaptations

**Vibe Coding (Original)**: Greenfield-focused, spec-driven, safe incremental changes

**Vibe Coding (Brownfield DefinitieAgent)**:
1. **Archaeology Mode** - Reverse-engineer specs from legacy code
2. **Constraint-Aware Refactoring** - Improve within existing architecture
3. **Surgical Modernization** - Aggressive refactoring without backwards compatibility
4. **Hybrid Feature Development** - Completion-aware workflow selection
5. **Integration with EPIC/US** - Map Vibe to existing backlog structure

**Key Principles**:
- ✅ Preserve business logic and domain knowledge
- ✅ Respect existing architecture constraints
- ✅ No backwards compatibility (single-user app)
- ✅ Test-first refactoring (characterization → refactor → unit tests)
- ✅ Incremental adoption (5-phase roadmap)

### 9.2 Recommended Next Steps

**Immediate (This Week)**:
1. ✅ Review this adaptation guide with team
2. ✅ Select 3 legacy modules for Archaeology Mode pilot
3. ✅ Create Vibe prompt templates (docs/architectuur/prompt-refactoring/vibe-prompts/)
4. ✅ Set up success metrics tracking dashboard

**Short-Term (Weeks 1-2)**:
5. Execute Phase 1 (Archaeology & Documentation) on 10 modules
6. Document brownfield Vibe patterns as reusable prompts
7. Train team on Archaeology Mode workflow

**Medium-Term (Weeks 3-10)**:
8. Execute Phase 2 (Constraint-Aware Refactoring) on god objects
9. Execute Phase 3 (Surgical Modernization) to finish V1→V2
10. Monitor success metrics, adjust workflows

**Long-Term (Weeks 11-16)**:
11. Execute Phase 4 (Hybrid Feature Development) to reach 80% completion
12. Execute Phase 5 (Continuous Improvement) for ongoing quality
13. Extract lessons learned, update this guide

### 9.3 Decision Gates

**GO/NO-GO Criteria** (after Phase 1):
- ✅ GO if: 80%+ of legacy modules have specs, team understands Archaeology Mode
- ❌ NO-GO if: Archaeology Mode is too slow, specs are low quality

**Escalation Path**:
- Issue: Archaeology Mode not yielding useful specs
- Solution: Pair AI with domain expert for validation
- Fallback: Delete unspecified code (if low risk)

---

## 10. Appendices

### Appendix A: Vibe Prompt Templates for Brownfield

**Template 1: Archaeology Mode Prompt**
```markdown
ARCHAEOLOGY MODE: Reverse-Engineer Spec

Analyze legacy module: [FILE_PATH]

As software archaeologist, produce Mini-Spec (Vibe 1.1 format):

1. 🎯 Purpose: What business problem does this solve?
2. 👤 Users: Who uses this? (internal service / UI / external API)
3. 🛠 Functionality: What does it do? (inputs → processing → outputs)
4. 📊 Business Logic: What domain rules are embedded?
5. 🔗 Dependencies: What does it depend on?
6. ⚠️ Risk Assessment: What breaks if we remove/change this?

Output Format: Mini-Spec (1 page max)
Recommendation: KEEP / REMOVE / MERGE (with evidence)
```

**Template 2: Constraint-Aware Refactoring Prompt**
```markdown
CONSTRAINT-AWARE REFACTORING

Module: [MODULE_NAME]
Current Issues: [LIST ISSUES]

IMMUTABLE CONSTRAINTS (CANNOT CHANGE):
- [API signature]
- [ServiceContainer wiring]
- [Database schema]
- [Session state structure]

MUTABLE AREAS (CAN REFACTOR):
- [Internal implementation]
- [Private methods]
- [Code organization]

Apply Vibe Techniques:
- Tip 5: Break into focused functions (<50 lines)
- Tip 10: Add docstrings (Google-style)
- Tip 12: Modularity Pact (core/ui/logging separation)
- Tip 13: Refactor-First (clean before extending)

Output: Refactored code + unit tests (95% coverage)
```

**Template 3: Surgical Modernization Prompt**
```markdown
SURGICAL MODERNIZATION: Replace Subsystem

Legacy Module: [V1_MODULE]
Target: [V2_MODULE]

STEP 1: Business Logic Extraction
Extract from V1:
- Core business rules (preserve)
- Domain knowledge (document)
- Edge cases (capture)
- Configuration (move to ConfigManager)

STEP 2: Modern V2 Design
Modernize:
- ServiceContainer DI
- Type hints (Python 3.11+)
- Structured logging
- Error handling (no bare except)
- 95% test coverage

STEP 3: Atomic Cutover
1. Implement V2 alongside V1
2. Feature flag (if needed, but single-user app allows direct cutover)
3. Update all imports
4. Validate tests pass
5. Delete V1 code

NO backwards compatibility required (single-user app).
Output: V2 implementation + cutover plan
```

**Template 4: Hybrid Feature Completion Prompt**
```markdown
HYBRID FEATURE DEVELOPMENT

Feature: [EPIC/US-XXX]
Current Completion: [X]%

COMPLETION AUDIT:
- Spec: [0/50/100%]
- Architecture: [0/50/100%]
- Implementation: [0/50/100%]
- Tests: [0/50/100%]
- Docs: [0/50/100%]

WORKFLOW SELECTION:
IF 0-20%: Vibe 8-Step (greenfield)
IF 20-50%: Hybrid (skip spec/arch, focus on implementation)
IF 50-80%: Polish (Vibe Tip 18-21)
IF 80-100%: Incremental (minor enhancements only)

GAPS IDENTIFIED:
1. [Gap 1] → [Vibe technique]
2. [Gap 2] → [Vibe technique]
3. [Gap 3] → [Vibe technique]

Output: Gap-specific implementation plan + timeline
```

### Appendix B: Brownfield Success Stories (DefinitieAgent)

**Success Story 1: V1→V2 Migration (19-09-2025)**
- **Challenge**: Mixed V1/V2 architecture with 1069 lines of legacy code
- **Vibe Technique**: Surgical Modernization + Business Logic Extraction
- **Outcome**: 100% V2 architecture, all V1 code removed, zero regressions
- **Timeline**: 4 weeks (planned 8 weeks with traditional approach)

**Success Story 2: Prompt Token Optimization (03-09-2025)**
- **Challenge**: 7250 tokens with 83% duplication
- **Vibe Technique**: Tip 17 (Synthesis) + Tip 18 (Auto-Polish)
- **Outcome**: 72% reduction (7250 → <2000 tokens), zero contradictions
- **Impact**: Faster AI calls, lower costs, improved clarity

**Success Story 3: Context Flow Refactoring (CFR/PER-007)**
- **Challenge**: Multiple competing documentation efforts, unclear implementation path
- **Vibe Technique**: Document Consolidation + Tip 8 (Architect First)
- **Outcome**: 14 documents → 2 canonical documents, single implementation path
- **Impact**: Developer clarity, faster execution

### Appendix C: FAQ - Brownfield Vibe Coding

**Q1: Can I use Vibe Coding on a project that's 60% complete?**
A: Yes! Use Hybrid Feature Development (Section 2.4) with completion-aware workflows.

**Q2: What if I have no specs for legacy code?**
A: Use Archaeology Mode (Section 2.1) to reverse-engineer specs from code.

**Q3: Can I refactor without breaking existing features?**
A: Yes! Use Constraint-Aware Refactoring (Section 2.2) + Regression Shield (Vibe 4.3).

**Q4: Does Vibe Coding require backwards compatibility?**
A: No! DefinitieAgent's "no backwards compatibility" policy allows Surgical Modernization (Section 2.3).

**Q5: How do I map Vibe workflows to EPICs and User Stories?**
A: See Section 4.1 for hybrid mapping (Epic → EPIC-XXX, Feature → US-XXX).

**Q6: What if Archaeology Mode produces low-quality specs?**
A: Pair AI with domain expert for validation, or delete low-risk code if specs are unclear.

**Q7: Can I mix greenfield Vibe with brownfield Vibe?**
A: Yes! Use Hybrid Feature Development (Section 2.4) for mixed-state features.

**Q8: How do I measure brownfield refactoring success?**
A: Use metrics in Section 8 (code reduction, duplication, complexity, coverage).

---

**Document Status**: ✅ Complete
**Review Date**: 2025-10-17
**Next Review**: After Phase 1 completion
**Owner**: Architecture Team
**Approvals Required**:
- [ ] Architecture Owner (brownfield adaptation strategy)
- [ ] Development Lead (practical applicability)
- [ ] Project Owner (resource allocation for 5-phase roadmap)
