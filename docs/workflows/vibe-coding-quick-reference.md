---
title: Vibe Coding Quick Reference for DefinitieAgent
description: Fast-access guide to Vibe Coding workflows and prompts for brownfield refactoring
author: Claude Code
date: 2025-01-17
status: active
related: [VIBE_CODING_METHODOLOGY_DEEP_ANALYSIS.md]
---

# Vibe Coding Quick Reference for DefinitieAgent

> **Full Analysis**: See `docs/analyses/VIBE_CODING_METHODOLOGY_DEEP_ANALYSIS.md` for comprehensive methodology analysis.

---

## Core Philosophy

**Vibe Coding = Intuitive AI collaboration + Rigorous structure**

Three Pillars:
1. **Spec-Driven**: AI builds only after clear problem/solution definition
2. **PM Framework**: Think problem-first, solution-second
3. **MCP Discipline**: Every feature lives in a ticket, no orphan work

---

## Workflows by Context

### For Refactoring (Brownfield) → Use Planning Systeem

**When**: Refactoring existing code, technical debt cleanup

**Steps**:
```
1. Brownfield Context Priming
   → Load CLAUDE.md constraints + existing architecture

2. Architect Assessment
   → Analyze current code, identify anti-patterns, define refactoring scope

3. Tech Spec (Refactoring-Focused)
   → Refactoring objectives, new architecture, migration strategy, testing

4. Action Plan
   → Granular tasks (max 15 files), tests per task, validation checkpoints
```

**Use For**:
- ✅ ServiceContainer refactoring
- ✅ ValidationOrchestratorV2 improvements
- ✅ Session state management cleanup
- ✅ Anti-pattern removal (god objects, circular dependencies)

---

### For New Features → Use Hybrid 4-Step

**When**: Adding new functionality to existing codebase

**Steps**:
```
1. PM Problem Validation
   → Problem analysis, feature story, acceptance criteria

2. Architecture Integration
   → How does this fit existing architecture? What to reuse vs. create?

3. Implementation Spec
   → Data models, service changes, UI changes, testing approach

4. Action Plan
   → Tasks, file changes, tests, validation checkpoints
```

**Use For**:
- ✅ New validation rules (EPIC-002)
- ✅ New UI tabs/features (EPIC-004)
- ✅ New external integrations (EPIC-003)

---

### For Bug Fixes → Use Debug Detective Pattern

**When**: Fixing bugs, investigating issues

**Steps**:
```
1. Debug Detective Analysis
   → Possible errors, root cause hypotheses, fix proposals (NO code yet)

2. Refactor-First (if code smells detected)
   → Clean up code around bug, improve readability (behavior-preserving)

3. Implement Fix
   → Minimal fix to root cause, add regression test

4. Validate
   → All tests pass, no CLAUDE.md violations, coverage maintained
```

**Use For**:
- ✅ Bug investigations
- ✅ Performance issues
- ✅ Edge case handling

---

## Essential Vibe Coding Tips for DefinitieAgent

### Mandatory (Use Always)

**Tip 7: Confirm Understanding**
```
Vat samen wat je gaat bouwen en waarom. Wacht op mijn GO.
```
→ **Use**: Before ANY code generation (prevents misaligned implementations)

**Tip 13: Refactor-First, Implement-Second**
```
Refactor deze code:
- Verwijder duplicatie
- Docstrings
- Leesbaarheid/modulariteit
Gedrag ongewijzigd.
```
→ **Use**: Separate refactoring from feature work (aligns with "no backwards compatibility" philosophy)

**Tip 15: Add Test Harness**
```
Schrijf unit tests (pytest-stijl):
- Positief
- Negatief
- Edge cases
```
→ **Use**: Every task includes test generation (maintain 60%+ coverage)

### High-Value (Use Frequently)

**Tip 8: Architect First, Code Second**
```
Architect-modus:
1) Mappenstructuur
2) Modules/functies
3) Dataflow
4) Risico's
Geen code. Vraag om GO.
```
→ **Use**: Before any refactoring (prevents spaghetti code)

**Tip 11: AI as Risk Engineer**
```
Noem 3 risico's/edge cases en geef mitigaties. Pas daarna implementatie.
```
→ **Use**: For validation rules, AI service integration, web lookup (critical paths)

**Tip 18: Auto-Polish Loop**
```
Voer polish-pass uit:
- Leesbaarheid
- Naming-conventies
- Foutafhandeling
- Docstrings
Toon alleen verbeterde versie.
```
→ **Use**: Before committing (align with Ruff + Black standards)

### Advanced (Use Strategically)

**Tip 16-17: Parallel Prompts + Synthesis**
```
Geef 3 verschillende oplossingen:
A) Minimalistisch
B) Robuust/Redundant
C) Creatief/Out-of-the-box

[Review A/B/C]

Combineer de beste elementen van A/B/C tot één finale versie.
```
→ **Use**: For architectural decisions, complex refactorings (explore solution space)

---

## Brownfield Context Template

**Use this at the start of EVERY AI interaction for DefinitieAgent**:

```markdown
<context>
Project: DefinitieAgent (Dutch legal definition generator)
Type: BROWNFIELD refactoring
Guidelines: /Users/chrislehnen/Projecten/Definitie-app/CLAUDE.md

## Existing Architecture (DO NOT REINVENT)

Core Pattern: Service-Oriented with Dependency Injection (ServiceContainer)

Key Services:
- ValidationOrchestratorV2: Main validation orchestration
- ModularValidationService: 45 validation rules in 7 categories
- UnifiedDefinitionGenerator: Core definition generation
- AIServiceV2: OpenAI GPT-4 integration with rate limiting
- PromptServiceV2: Modular prompt building
- ModernWebLookupService: Wikipedia/SRU integration
- SessionStateManager: SOLE source of truth for st.session_state

Established Patterns (MUST FOLLOW):
1. Dependency injection via ServiceContainer
2. Session state ONLY via SessionStateManager (NO direct st.session_state access)
3. Separation: core/ui/logging (NO mixing)
4. Type hints required (Python 3.11+)
5. Ruff + Black formatting (88 char lines)
6. pytest for testing (60%+ coverage target)

## CRITICAL ANTI-PATTERNS (FORBIDDEN)

❌ dry_helpers.py or catch-all utility modules
   → Split by specific purpose: type_helpers, dict_helpers, validation_helpers

❌ Direct st.session_state access outside SessionStateManager
   → Use SessionStateManager.get_value() / set_value()

❌ Mixing core/ui/logging (god objects)
   → Enforce Modularity Pact (Tip 12)

❌ Backwards compatibility code
   → REFACTOR cleanly, preserve business logic, no legacy support code

## Refactoring Constraints

- PRESERVE: Business logic, validation rules, API contracts
- MAINTAIN: Test coverage (60%+), performance (< 1s validation)
- EXTRACT: Business knowledge during refactoring
- DOCUMENT: Design decisions, architectural changes

## Current Task
[PLACEHOLDER - Insert specific refactoring or feature task here]
</context>
```

---

## Planning Systeem Workflow (Detailed)

### Step 1: Architect Assessment

**Prompt Template**:
```markdown
<goal>
You're a Senior Software Engineer analyzing EXISTING code for refactoring.
This is BROWNFIELD, not greenfield.
</goal>

<brownfield-context>
[Use Brownfield Context Template above]
</brownfield-context>

<task>
Assess current architecture of [MODULE NAME]:

Current Location: [file path]
Current Tests: [test file path, current coverage]
Current Documentation: [docs path]

ANALYSIS REQUIRED:
1. Current Architecture
   - Component structure (Mermaid diagram)
   - Dependencies and coupling
   - Data flow

2. Identified Issues
   - Anti-patterns (god objects, tight coupling, etc.)
   - CLAUDE.md violations
   - Testability problems
   - Maintainability issues

3. Proposed Architecture
   - Refactoring pattern (e.g., CategoryOrchestrator, Strategy, etc.)
   - New module structure
   - Before/after architecture diagrams

4. Refactoring Scope
   - What to preserve (business logic, APIs)
   - What to change (internal structure)
   - Migration strategy (if schema changes)

5. Risk Assessment
   - What could break?
   - Mitigation strategies
   - Performance impact
</task>

<format>
Return as Markdown with:
- Clear section headings
- Mermaid diagrams for architecture
- Risk/mitigation table
- Questions for clarification (if any)
</format>
```

**Output Location**: `docs/backlog/EPIC-XXX/US-XXX/architecture-assessment.md`

---

### Step 2: Tech Spec (Refactoring-Focused)

**Prompt Template**:
```markdown
<goal>
Create technical specification for refactoring [MODULE NAME] based on architect assessment.
</goal>

<input>
[Paste architect assessment output from Step 1]
</input>

<spec-structure>
## 1. Refactoring Objectives

PRESERVE:
- Business logic: [list specific rules/logic]
- API contracts: [list public APIs that callers depend on]
- Test coverage: [current coverage %, target coverage %]
- Performance: [current benchmarks, target benchmarks]

CHANGE:
- Internal structure: [what architectural changes]
- Test organization: [new test structure]
- Module organization: [new directory structure]

## 2. New Module Structure

[Show new directory tree]

src/services/[domain]/
├── __init__.py
├── [new modules]
└── [refactored modules]

## 3. Data Flow Changes

BEFORE:
[ASCII or Mermaid diagram]

AFTER:
[ASCII or Mermaid diagram]

## 4. Testing Approach

- Test organization: [new test files and structure]
- Coverage target: [e.g., maintain 98%]
- Test strategy:
  - Unit tests: [what to test in isolation]
  - Integration tests: [what to test end-to-end]
  - Regression tests: [new tests to prevent breaking existing behavior]

## 5. Migration Strategy

- Database changes: [if applicable, schema migrations]
- Configuration changes: [if applicable, config file updates]
- Deployment considerations: [rollout strategy, rollback plan]

## 6. Performance Targets

- Validation time: [target, e.g., ≤ current baseline]
- Memory usage: [target, e.g., ≤ current baseline]
- Benchmarking approach: [how to measure performance]

## 7. Risk Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| [risk] | [H/M/L] | [H/M/L] | [mitigation strategy] |

## 8. CLAUDE.md Compliance

- [ ] No god objects or catch-all helpers
- [ ] SessionStateManager used for all session state
- [ ] Core/UI/logging separation maintained
- [ ] No backwards compatibility code
- [ ] Business logic preserved and documented

</spec-structure>

<format>
Return complete tech spec in Markdown, ready for implementation planning.
</format>
```

**Output Location**: `docs/backlog/EPIC-XXX/US-XXX/tech-spec.md`

---

### Step 3: Action Plan

**Prompt Template**:
```markdown
<goal>
Create granular, step-by-step action plan for implementing refactoring based on tech spec.
</goal>

<input>
[Paste tech spec from Step 2]
</input>

<action-plan-structure>
## Task [N]: [Brief Title]

**Task**: [Detailed explanation of what needs to be implemented]

**Files** (max 15):
- `path/to/file1.py`: [Description of changes]
- `path/to/file2.py`: [Description of changes]
- `tests/path/to/test_file.py`: [New tests or test updates]

**Implementation Steps**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Tests**:
- Positive: [happy path test cases]
- Negative: [error handling test cases]
- Edge cases: [boundary condition test cases]

**Validation**:
- [ ] All tests pass (pytest)
- [ ] Coverage ≥ [target %] (pytest --cov)
- [ ] No CLAUDE.md violations
- [ ] Performance ≥ baseline (if applicable)

**Step Dependencies**: [List task IDs this depends on, or "None"]

**User Instructions**:
1. [Instruction for developer review/action]
2. [Instruction for validation]

---

[Repeat for each task]
</action-plan-structure>

<guidelines>
- Each task must modify ≤ 15 files
- Each task must include tests
- Tasks should be independently validatable (run tests after each)
- Mark dependencies clearly
- Order tasks by: setup → implementation → integration → validation
</guidelines>

<format>
Return complete action plan in Markdown, ready for task-by-task execution.
</format>
```

**Output Location**: `docs/backlog/EPIC-XXX/US-XXX/action-plan.md`

---

## Hybrid 4-Step Workflow (Detailed)

### Step 1: PM Problem Validation

**Prompt Template**:
```markdown
<goal>
You are an expert Product Manager analyzing a new feature request for DefinitieAgent.
Apply problem-first thinking before jumping to solutions.
</goal>

<pm-framework>
1. Problem Analysis
   - What specific problem does this solve?
   - Who experiences this problem most acutely?
   - What are the consequences of NOT solving this?

2. Solution Validation
   - Why is this the right solution?
   - What alternatives exist? Why not those?
   - What is the minimum viable version?

3. Impact Assessment
   - How will we measure success?
   - What changes for users?
   - What are unintended consequences?
</pm-framework>

<feature-request>
[Paste user's feature request here]
</feature-request>

<output-format>
## Problem Analysis
[Answer questions from PM framework #1]

## Solution Validation
[Answer questions from PM framework #2]

## Feature Story

**Feature**: [Feature name]

**User Story**: As a [persona], I want to [action], so that I can [benefit]

**Acceptance Criteria**:
- Given [context], when [action], then [outcome]
- Given [edge case context], when [action], then [edge case outcome]

**Priority**: P0/P1/P2 ([Justification based on impact analysis])

**Dependencies**: [List any blockers or prerequisites]

**Technical Constraints**: [Any known limitations from existing architecture]

**UX Considerations**: [Key interaction points, user flow]

## Success Metrics
[How we'll measure if this solved the problem]

## Critical Questions
- [ ] [Question 1 for clarification]
- [ ] [Question 2 for clarification]
</output-format>
```

**Output Location**: `docs/backlog/EPIC-XXX/US-XXX/problem-analysis.md`

---

### Step 2: Architecture Integration

**Prompt Template**:
```markdown
<goal>
Determine how this new feature integrates with existing DefinitieAgent architecture.
REUSE before CREATE.
</goal>

<brownfield-context>
[Use Brownfield Context Template from above]
</brownfield-context>

<feature-story>
[Paste feature story from Step 1]
</feature-story>

<integration-analysis>
## 1. Existing Architecture Fit

Which existing services/patterns can we reuse?
- [ ] ServiceContainer (dependency injection)
- [ ] ValidationOrchestratorV2 (validation flow)
- [ ] ModularValidationService (validation rules)
- [ ] AIServiceV2 (AI integration)
- [ ] PromptServiceV2 (prompt building)
- [ ] ModernWebLookupService (external data)
- [ ] SessionStateManager (UI state)
- [ ] Other: [specify]

## 2. New Components Needed

What must be created (cannot reuse existing)?
- [ ] New service: [name and purpose]
- [ ] New validation rule: [category and purpose]
- [ ] New UI component: [location and purpose]
- [ ] New configuration: [type and purpose]
- [ ] Other: [specify]

## 3. Integration Points

How does this connect to existing architecture?
- Entry point: [where does this feature hook into the app?]
- Data flow: [input → processing → output]
- Dependencies: [what existing services does this depend on?]
- Dependents: [what will depend on this feature?]

## 4. Impact Assessment

What existing components are affected?
- Modified services: [list with justification]
- Modified UI: [list with justification]
- Modified configuration: [list with justification]
- Modified tests: [list with justification]

## 5. Architecture Diagram

[Mermaid diagram showing how new feature integrates with existing architecture]
</integration-analysis>

<format>
Return integration analysis in Markdown, ready for implementation spec.
</format>
```

**Output Location**: `docs/backlog/EPIC-XXX/US-XXX/architecture-integration.md`

---

### Step 3: Implementation Spec

**Prompt Template**:
```markdown
<goal>
Create implementation specification for new feature based on architecture integration.
</goal>

<input>
Feature Story: [from Step 1]
Architecture Integration: [from Step 2]
</input>

<spec-structure>
## 1. Data Model Changes

[If applicable, new entities or modifications to existing entities]

### New Entity: [Name]
```python
# Prisma/SQLAlchemy model or Python dataclass
```

### Modified Entity: [Name]
```python
# Show changes to existing model
```

## 2. Service Changes

### New Service: [Name]
**Purpose**: [What this service does]
**Location**: `src/services/[domain]/[service_name].py`
**Dependencies**: [List services this depends on]
**Interface**:
```python
class [ServiceName]:
    def __init__(self, ...):
        ...

    def [method_name](self, ...) -> ...:
        """[Docstring with purpose, params, returns]"""
        ...
```

### Modified Service: [Name]
**Changes**: [What's being added/modified]
**Location**: `src/services/[domain]/[service_name].py`
**New Methods**:
```python
def [method_name](self, ...) -> ...:
    """[Docstring]"""
    ...
```

## 3. Configuration Changes

[If applicable, new config files or modifications]

### New Config: [Name]
**Location**: `config/[domain]/[config_name].json` or `.yaml`
**Structure**:
```json
{
  "key": "value"
}
```

## 4. UI Changes

[If applicable, new tabs/components or modifications]

### New UI Component: [Name]
**Location**: `src/ui/tabs/[tab_name].py` or `src/ui/components/[component_name].py`
**Purpose**: [What this UI does]
**State Requirements**: [Session state variables needed]
**Integration**: [How this hooks into existing UI]

### Modified UI Component: [Name]
**Changes**: [What's being added/modified]

## 5. Testing Approach

### Unit Tests
- Test files: [list new test files]
- Coverage target: [e.g., 80%+ for new code]
- Key test cases:
  - Positive: [happy path scenarios]
  - Negative: [error handling scenarios]
  - Edge cases: [boundary conditions]

### Integration Tests
- Test files: [list integration test files]
- Test scenarios: [end-to-end scenarios to validate]

### Manual Testing
- [ ] [Manual test step 1]
- [ ] [Manual test step 2]

## 6. Migration Strategy

[If applicable, how to migrate existing data/config]

## 7. Rollback Plan

[How to safely rollback if this feature causes issues]

</spec-structure>

<format>
Return implementation spec in Markdown, ready for action plan generation.
</format>
```

**Output Location**: `docs/backlog/EPIC-XXX/US-XXX/implementation-spec.md`

---

### Step 4: Action Plan

**Same as Planning Systeem Step 3** (see above)

---

## Quick Decision Tree

```
┌─────────────────────────────────────┐
│  What type of work is this?         │
└─────────────┬───────────────────────┘
              │
         ┌────┴────┐
         │         │
    Refactoring   New Feature
         │         │
         v         v
   Planning    Hybrid 4-Step
   Systeem
         │         │
         v         v
   ┌─────────────────────────┐
   │ Brownfield Context      │
   │ Priming (ALWAYS)        │
   └─────────────────────────┘
         │
         v
   ┌─────────────────────────┐
   │ Execute Workflow        │
   │ Task-by-Task            │
   └─────────────────────────┘
         │
         v
   ┌─────────────────────────┐
   │ Validate (Tip 15)       │
   │ - Tests pass            │
   │ - CLAUDE.md compliance  │
   │ - Coverage ≥ 60%        │
   └─────────────────────────┘
```

---

## Common Patterns

### Pattern 1: Adding New Validation Rule

**Workflow**: Hybrid 4-Step (abbreviated)

**Quick Steps**:
1. **Problem**: What clarity/quality issue does this rule address?
2. **Integration**: Which category (ARAI/CON/ESS/INT/SAM/STR/VER)?
3. **Implementation**:
   - Create `config/toetsregels/regels/[CAT]/[CAT]-00X-[name].json`
   - Create `src/toetsregels/regels/[CAT]/[name]_rule.py`
   - Register in `config/toetsregels.json`
4. **Tests**:
   - Create `tests/toetsregels/regels/[CAT]/test_[name]_rule.py`
   - Test positive/negative/edge cases
5. **Validate**: Run `pytest tests/toetsregels/` and verify coverage

---

### Pattern 2: Refactoring Service

**Workflow**: Planning Systeem (full)

**Quick Steps**:
1. **Context Priming**: Load brownfield context + current service architecture
2. **Architect Assessment**: Analyze current structure, identify issues, propose refactoring
3. **Tech Spec**: Define refactoring objectives, new structure, migration, testing
4. **Action Plan**: Break into tasks (max 15 files each), include tests
5. **Execute**: Task-by-task with validation after each

---

### Pattern 3: Fixing Bug

**Workflow**: Debug Detective Pattern

**Quick Steps**:
1. **Debug Analysis**: Hypothesize root causes (NO code yet)
2. **Refactor-First**: Clean up code around bug (if smelly)
3. **Fix**: Minimal change to address root cause
4. **Regression Test**: Add test that would have caught this bug
5. **Validate**: All tests pass, coverage maintained

---

## Tooling Scripts (Recommended)

Create these in `scripts/vibe-coding/`:

### `init-refactor.sh`
```bash
#!/bin/bash
# Usage: scripts/vibe-coding/init-refactor.sh <module-name>

MODULE=$1
EPIC=$2
US=$3

# Create documentation structure
mkdir -p "docs/backlog/${EPIC}/${US}"

# Generate brownfield context template
cat > "docs/backlog/${EPIC}/${US}/brownfield-context.md" <<EOF
[Brownfield Context Template - auto-populated]
EOF

# Launch architect assessment prompt
echo "Brownfield context created. Next: Run architect assessment."
```

### `next-task.sh`
```bash
#!/bin/bash
# Usage: scripts/vibe-coding/next-task.sh <US-XXX>

US=$1
ACTION_PLAN="docs/backlog/${EPIC}/${US}/action-plan.md"

# Parse action plan, find next pending task
# Mark as in-progress
# Display task details
```

### `validate-task.sh`
```bash
#!/bin/bash
# Usage: scripts/vibe-coding/validate-task.sh

# Run tests
pytest -v

# Check coverage
pytest --cov=src --cov-report=term-missing

# Check CLAUDE.md compliance (custom script)
python scripts/check-claude-compliance.py

# If all pass, mark task complete
```

---

## Resources

**Full Analysis**: `docs/analyses/VIBE_CODING_METHODOLOGY_DEEP_ANALYSIS.md`

**Templates**:
- Brownfield Context: See above
- Planning Systeem: Steps 1-3 above
- Hybrid 4-Step: Steps 1-4 above

**Examples** (to be created):
- ValidationOrchestratorV2 refactoring case study
- New validation rule implementation walkthrough
- Bug fix using Debug Detective pattern

---

**Last Updated**: 2025-01-17
**Status**: Active
**Maintained By**: Development Team
