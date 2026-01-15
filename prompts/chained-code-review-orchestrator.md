# Code Review Orchestrator - Definitie-app Codebase

## Review Context
**Project**: Dutch AI-powered Definition Generator  
**Codebase**: 86,030 LOC verdeeld over 31 functionele deelgebieden  
**Repository**: Definitie-app via prompt-forge project ID 4  
**Workflow**: Multiagent orchestratie gebaseerd op functionele area-analyse  
**Prerequisites**: Eerst uitvoeren van Prompt #380 voor area definitie

## Review Workflow

### STAP 1: Area Definitie (Prerequisite)
```bash
prompt-forge orchestrate --project-id 4 --prompt 380
```
**Output**: `project-areas.yaml` met 31 functionele deelgebieden

### STAP 2: Multiagent Review Orchestratie
Voor elk functioneel deelgebied uit `project-areas.yaml`:

## Review Checklist per Area

### **Agent 1: Code Reviewer (Weight: 1.0x)**
- [ ] **Code Style & Formatting**
  - Consistente Nederlandse naming voor definitie-gerelateerde termen
  - PEP 8 compliance
  - Type hints aanwezig
  - Docstrings in Nederlands voor definitie functies

- [ ] **Code Quality**
  - DRY principe toegepast
  - YAGNI compliance
  - Code readability voor Dutch AI context
  - Magic numbers geëlimineerd

- [ ] **Error Handling**
  - Graceful handling van definitie parsing errors
  - Appropriate exceptions voor AI model failures
  - User-friendly error messages in Nederlands

### **Agent 2: Full Stack Developer (Weight: 1.0x)**
- [ ] **Implementation Robustness**
  - Edge cases voor Dutch language processing
  - Input validation voor definitie queries
  - Data sanitization voor AI prompts
  - Integration tussen frontend/backend components

- [ ] **Business Logic Verification**
  - 45 validatieregels correct geïmplementeerd
  - Definitie kwaliteit checks functioneren
  - AI model responses worden correct verwerkt

- [ ] **Data Flow Analysis**
  - Request/response cycles optimaal
  - State management consistent
  - Database transactions atomic

### **Agent 3: Architecture Reviewer (Weight: 1.2x)**
- [ ] **Architectural Patterns**
  - SOLID principles toegepast
  - Separation of concerns tussen AI en business logic
  - Clean Architecture layers respecteerd

- [ ] **Scalability & Performance**
  - AI model calls geoptimaliseerd
  - Caching strategy voor definitie results
  - Database query performance
  - Memory usage bij large definitie sets

- [ ] **Design Patterns**
  - Factory pattern voor definitie generators
  - Strategy pattern voor verschillende AI models
  - Observer pattern voor validation workflows

### **Agent 4: Code Simplifier (Weight: 1.5x) - Voor Monster Files**
**Triggered when**: `is_monster_file: true` in area definition

- [ ] **Complexity Reduction**
  - Cyclomatic complexity < 10 per functie
  - Long parameter lists gerefactored
  - Nested loops/conditions simplified
  - God classes opgesplitst

- [ ] **Refactoring Opportunities**
  - Extract Method voor repeated definitie logic
  - Replace Conditional met Strategy voor AI model selection
  - Pull Up Method voor shared validation logic

## TDD Compliance Check

### **TDD Process Verificatie**
- [ ] **Test Coverage per 45 Validatieregels**
  - Elke validatieregel heeft minimaal 5 tests
  - AI model interactions zijn gemocked
  - Dutch language edge cases getest

- [ ] **Test Categorieën Gedekt**
  - **Happy Path**: Correcte definitie generatie
  - **Input Validation**: Malformed Dutch queries
  - **Edge Cases**: Empty definitions, special characters
  - **Error Handling**: AI service downtime
  - **Silent Failure Detection**: Invalid but undetected definitions

### **AI-Specific Test Requirements**
- [ ] Mock responses voor OpenAI/Claude API calls
- [ ] Deterministic tests ondanks AI non-determinisme
- [ ] Performance tests voor batch definitie processing
- [ ] Integration tests voor complete definitie workflows

## Consensus Framework

### **Voting Rules**
- **CRITICAL**: Unanimiteit vereist (4/4 agents)
- **HIGH**: 75% meerderheid (3/4 agents)
- **MEDIUM**: 60% gewogen meerderheid
- **LOW**: Eenvoudige meerderheid (2/4 agents)

### **Weighted Scoring**
```
Total Weight = (Code Reviewer × 1.0) + (Full Stack × 1.0) + (Architecture × 1.2) + (Simplifier × 1.5 if applicable)
Consensus Threshold = Total Weight × 0.6
```

## Focus Gebieden

### **1. Kritieke Issues (CRITICAL - Blocking)**
- Security vulnerabilities in AI prompt injection
- Data corruption in definitie storage
- Performance degradation > 30%
- Breaking changes in validation rules

### **2. Hoge Prioriteit (HIGH - Should Fix)**
- Maintainability issues in monster files
- Missing test coverage voor edge cases
- Architecture violations in cross-cutting concerns

### **3. Medium Prioriteit (MEDIUM - Nice to Have)**
- Code style inconsistenties
- Minor performance optimizations
- Documentation gaps

### **4. Lage Prioriteit (LOW - Suggestions)**
- Variable naming improvements
- Code comments in Nederlands
- Refactoring opportunities

## Aannames & Context

### **Tech Stack**
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy
- **Frontend**: React/TypeScript, Nederlandse UI
- **AI**: OpenAI GPT-4, Anthropic Claude
- **Database**: PostgreSQL voor definitie storage
- **Testing**: pytest, factory_boy

### **Team Conventions**
- Nederlandse comments voor business logic
- Engelse code/variabele namen
- Type hints verplicht
- 90%+ test coverage vereist

### **Breaking Change Beleid**
- API versioning voor definitie endpoints
- Backward compatibility voor stored definitions
- Migration scripts voor validation rule changes

## Output Formaat

### **Per Area Report Structure**
```markdown
## [Area Name] Review Summary

### Critical Issues (🚨)
- `file.py:123` - [Severity] Description + Solution

### High Priority (⚠️)
- `file.py:456` - [Severity] Description + Solution

### Recommendations (💡)
- `file.py:789` - [Severity] Description + Solution

### Agent Consensus
- Code Reviewer: ✅/❌ + rationale
- Full Stack: ✅/❌ + rationale  
- Architecture: ✅/❌ + rationale
- Simplifier: ✅/❌ + rationale (if applicable)

### Weighted Score: X.X/5.0
```

### **Cross-Cutting Concerns Report**
```markdown
## Cross-Area Findings

### Architecture Patterns
- Inconsistent AI model abstraction across areas
- Missing centralized validation orchestrator

### Performance Hotspots
- Database N+1 queries in definitie retrieval
- Unnecessary AI calls in batch processing

### Security Concerns
- Prompt injection vectors in user input
- Insufficient rate limiting on AI endpoints
```

### **Final Prioritized Action Plan**
```markdown
## Actionable Recommendations

### 🚨 CRITICAL (Fix Immediately)
1. [file:line] - Issue + Solution
2. [file:line] - Issue + Solution

### ⚠️ HIGH PRIORITY (Fix This Sprint)
1. [file:line] - Issue + Solution
2. [file:line] - Issue + Solution

### 💡 MEDIUM/LOW (Backlog)
- Grouped by theme/area
- Effort estimates included
```

## Uitvoering
```bash
# Voer deze workflow uit na area definitie
prompt-forge orchestrate --project-id 4 --use-areas project-areas.yaml --agents code-reviewer,fullstack-dev,architect,simplifier --consensus-threshold 0.6
```
---

## Execution Mode: Multiagent (7 BMAD Agents)

**Je bent de Orchestrator.** Voer deze analyse uit door 7 subagents te spawnen, elk met eigen expertise. Houd je hoofdcontext compact - alleen coordinatie en summaries.

### Orchestrator Protocol

1. **Spawn alle agents parallel** waar mogelijk (gebruik meerdere Task() calls in een message)
2. **Wacht op alle summaries** (max 200 woorden per agent)
3. **Synthetiseer resultaten** in een coherent rapport
4. **Bereken consensus** op basis van gewogen votes

### Context Management

- Elke subagent krijgt ALLEEN de relevante context voor hun analyse
- Subagents retourneren compacte summaries (max 200 woorden)
- De orchestrator combineert summaries tot eindrapport
- Totale context budget: ~4000 tokens voor synthese

### Idee om te Analyseren

> Genereer een Code Review Orchestrator prompt voor de Definitie-app codebase met de volgende workflow:

STAP 1 - AREA DEFINITIE (Prerequisite):
Voer eerst Prompt #380 'Codebase Functionele Area-onderverdeling voor Multiagent Analyse' uit op de target codebase. Dit genereert een project-areas.yaml met functionele deelgebieden.

STAP 2 - CODE REVIEW ORCHESTRATION:
Gebruik de gegenereerde areas uit Stap 1 als input voor een multiagent code review. Per area worden 3 agents gespawned:
- Code Reviewer ...


---

## Subagent Spawn Instructions

Spawn de volgende agents parallel. Elke agent analyseert vanuit hun expertise.

### Agent 1: Code Reviewer

**Role:** Senior Developer & Code Quality Expert
**Weight:** 1.5x
**Focus:** Code quality, Best practices, Naming conventions

```python
Task(
    subagent_type="code-reviewer",
    prompt="""
Je bent een **Senior Developer & Code Quality Expert** met expertise in Code quality, Best practices, Naming conventions.

## TAAK
Analyseer het volgende idee vanuit jouw expertise:

> Genereer een Code Review Orchestrator prompt voor de Definitie-app codebase met de volgende workflow:

STAP 1 - AREA DEFINITIE (Prerequisite):
Voer eerst Prompt #380 'Codebase Functionele Area-onderverdeling voor Multiagent Analyse' uit op de target codebase. Dit genereert een project-areas.yaml met...

Context: Context: De Definitie-app heeft 31 functionele deelgebieden (86,030 LOC) gedefinieerd in prompt-forge project ID 4. Prompt #380 bevat de area definition workflow. De code review moet werken met prompt...

## ANALYSEER
Focus op je kernexpertise: Code quality, Best practices, Naming conventions

1. Wat zijn de sterke punten vanuit jouw perspectief?
2. Welke risico's of aandachtspunten zie je?
3. Welke concrete verbeteringen stel je voor?

## OUTPUT FORMAT
Max 200 woorden samenvatting met:
- Score: X/10
- Top 3 bevindingen (bullet points)
- Concrete aanbeveling (1 zin)
""",
    model="opus", thinking="extended"
)
```

### Agent 2: Silent Failure Hunter

**Role:** Error Handling & Observability Expert
**Weight:** 1.0x
**Focus:** Error handling, Silent failures, Fallback behavior

```python
Task(
    subagent_type="pr-review-toolkit:silent-failure-hunter",
    prompt="""
Je bent een **Error Handling & Observability Expert** met expertise in Error handling, Silent failures, Fallback behavior.

## TAAK
Analyseer het volgende idee vanuit jouw expertise:

> Genereer een Code Review Orchestrator prompt voor de Definitie-app codebase met de volgende workflow:

STAP 1 - AREA DEFINITIE (Prerequisite):
Voer eerst Prompt #380 'Codebase Functionele Area-onderverdeling voor Multiagent Analyse' uit op de target codebase. Dit genereert een project-areas.yaml met...

Context: Context: De Definitie-app heeft 31 functionele deelgebieden (86,030 LOC) gedefinieerd in prompt-forge project ID 4. Prompt #380 bevat de area definition workflow. De code review moet werken met prompt...

## ANALYSEER
Focus op je kernexpertise: Error handling, Silent failures, Fallback behavior

1. Wat zijn de sterke punten vanuit jouw perspectief?
2. Welke risico's of aandachtspunten zie je?
3. Welke concrete verbeteringen stel je voor?

## OUTPUT FORMAT
Max 200 woorden samenvatting met:
- Score: X/10
- Top 3 bevindingen (bullet points)
- Concrete aanbeveling (1 zin)
""",
    model="sonnet", thinking="extended"
)
```

### Agent 3: Tester

**Role:** QA Engineer & Test Strategy Expert
**Weight:** 1.0x
**Focus:** Test coverage, Edge cases, Testability

```python
Task(
    subagent_type="pr-review-toolkit:pr-test-analyzer",
    prompt="""
Je bent een **QA Engineer & Test Strategy Expert** met expertise in Test coverage, Edge cases, Testability.

## TAAK
Analyseer het volgende idee vanuit jouw expertise:

> Genereer een Code Review Orchestrator prompt voor de Definitie-app codebase met de volgende workflow:

STAP 1 - AREA DEFINITIE (Prerequisite):
Voer eerst Prompt #380 'Codebase Functionele Area-onderverdeling voor Multiagent Analyse' uit op de target codebase. Dit genereert een project-areas.yaml met...

Context: Context: De Definitie-app heeft 31 functionele deelgebieden (86,030 LOC) gedefinieerd in prompt-forge project ID 4. Prompt #380 bevat de area definition workflow. De code review moet werken met prompt...

## ANALYSEER
Focus op je kernexpertise: Test coverage, Edge cases, Testability

1. Wat zijn de sterke punten vanuit jouw perspectief?
2. Welke risico's of aandachtspunten zie je?
3. Welke concrete verbeteringen stel je voor?

## OUTPUT FORMAT
Max 200 woorden samenvatting met:
- Score: X/10
- Top 3 bevindingen (bullet points)
- Concrete aanbeveling (1 zin)
""",
    model="sonnet", thinking="extended"
)
```

### Agent 4: Simplicity Enforcer

**Role:** Anti-Over-Engineering Guardian
**Weight:** 2.0x
**Focus:** Over-engineering detection, YAGNI enforcement, Scope creep prevention

```python
Task(
    subagent_type="code-simplifier",
    prompt="""
Je bent een **Anti-Over-Engineering Guardian** met expertise in Over-engineering detection, YAGNI enforcement, Scope creep prevention.

## TAAK
Analyseer het volgende idee vanuit jouw expertise:

> Genereer een Code Review Orchestrator prompt voor de Definitie-app codebase met de volgende workflow:

STAP 1 - AREA DEFINITIE (Prerequisite):
Voer eerst Prompt #380 'Codebase Functionele Area-onderverdeling voor Multiagent Analyse' uit op de target codebase. Dit genereert een project-areas.yaml met...

Context: Context: De Definitie-app heeft 31 functionele deelgebieden (86,030 LOC) gedefinieerd in prompt-forge project ID 4. Prompt #380 bevat de area definition workflow. De code review moet werken met prompt...

## ANALYSEER
Focus op je kernexpertise: Over-engineering detection, YAGNI enforcement, Scope creep prevention

1. Wat zijn de sterke punten vanuit jouw perspectief?
2. Welke risico's of aandachtspunten zie je?
3. Welke concrete verbeteringen stel je voor?

## OUTPUT FORMAT
Max 200 woorden samenvatting met:
- Score: X/10
- Top 3 bevindingen (bullet points)
- Concrete aanbeveling (1 zin)
""",
    model="opus", thinking="extended"
)
```

### Agent 5: Type Analyst

**Role:** Type Safety & Data Structure Expert
**Weight:** 0.8x
**Focus:** Type safety, Data structures, Invariants

```python
Task(
    subagent_type="pr-review-toolkit:type-design-analyzer",
    prompt="""
Je bent een **Type Safety & Data Structure Expert** met expertise in Type safety, Data structures, Invariants.

## TAAK
Analyseer het volgende idee vanuit jouw expertise:

> Genereer een Code Review Orchestrator prompt voor de Definitie-app codebase met de volgende workflow:

STAP 1 - AREA DEFINITIE (Prerequisite):
Voer eerst Prompt #380 'Codebase Functionele Area-onderverdeling voor Multiagent Analyse' uit op de target codebase. Dit genereert een project-areas.yaml met...

Context: Context: De Definitie-app heeft 31 functionele deelgebieden (86,030 LOC) gedefinieerd in prompt-forge project ID 4. Prompt #380 bevat de area definition workflow. De code review moet werken met prompt...

## ANALYSEER
Focus op je kernexpertise: Type safety, Data structures, Invariants

1. Wat zijn de sterke punten vanuit jouw perspectief?
2. Welke risico's of aandachtspunten zie je?
3. Welke concrete verbeteringen stel je voor?

## OUTPUT FORMAT
Max 200 woorden samenvatting met:
- Score: X/10
- Top 3 bevindingen (bullet points)
- Concrete aanbeveling (1 zin)
""",
    model="sonnet", thinking="extended"
)
```

### Agent 6: Debug Specialist

**Role:** Debugging & Observability Expert
**Weight:** 0.8x
**Focus:** Debugging, Logging, Observability

```python
Task(
    subagent_type="debug-specialist",
    prompt="""
Je bent een **Debugging & Observability Expert** met expertise in Debugging, Logging, Observability.

## TAAK
Analyseer het volgende idee vanuit jouw expertise:

> Genereer een Code Review Orchestrator prompt voor de Definitie-app codebase met de volgende workflow:

STAP 1 - AREA DEFINITIE (Prerequisite):
Voer eerst Prompt #380 'Codebase Functionele Area-onderverdeling voor Multiagent Analyse' uit op de target codebase. Dit genereert een project-areas.yaml met...

Context: Context: De Definitie-app heeft 31 functionele deelgebieden (86,030 LOC) gedefinieerd in prompt-forge project ID 4. Prompt #380 bevat de area definition workflow. De code review moet werken met prompt...

## ANALYSEER
Focus op je kernexpertise: Debugging, Logging, Observability

1. Wat zijn de sterke punten vanuit jouw perspectief?
2. Welke risico's of aandachtspunten zie je?
3. Welke concrete verbeteringen stel je voor?

## OUTPUT FORMAT
Max 200 woorden samenvatting met:
- Score: X/10
- Top 3 bevindingen (bullet points)
- Concrete aanbeveling (1 zin)
""",
    model="sonnet", thinking="extended"
)
```

### Agent 7: Architect

**Role:** Senior Software Architect
**Weight:** 2.0x
**Focus:** System scalability, Design patterns, Technical debt

```python
Task(
    subagent_type="feature-dev:code-architect",
    prompt="""
Je bent een **Senior Software Architect** met expertise in System scalability, Design patterns, Technical debt.

## TAAK
Analyseer het volgende idee vanuit jouw expertise:

> Genereer een Code Review Orchestrator prompt voor de Definitie-app codebase met de volgende workflow:

STAP 1 - AREA DEFINITIE (Prerequisite):
Voer eerst Prompt #380 'Codebase Functionele Area-onderverdeling voor Multiagent Analyse' uit op de target codebase. Dit genereert een project-areas.yaml met...

Context: Context: De Definitie-app heeft 31 functionele deelgebieden (86,030 LOC) gedefinieerd in prompt-forge project ID 4. Prompt #380 bevat de area definition workflow. De code review moet werken met prompt...

## ANALYSEER
Focus op je kernexpertise: System scalability, Design patterns, Technical debt

1. Wat zijn de sterke punten vanuit jouw perspectief?
2. Welke risico's of aandachtspunten zie je?
3. Welke concrete verbeteringen stel je voor?

## OUTPUT FORMAT
Max 200 woorden samenvatting met:
- Score: X/10
- Top 3 bevindingen (bullet points)
- Concrete aanbeveling (1 zin)
""",
    model="opus", thinking="extended"
)
```


---

## Synthesis Instructions

Na ontvangst van alle 7 agent summaries:

### Stap 1: Verzamel Resultaten
Wacht tot alle agents hun summary hebben gegeven:
- Code Reviewer, Silent Failure Hunter, Tester, Simplicity Enforcer, Type Analyst, Debug Specialist en Architect

### Stap 2: Bereken Consensus
| Agent | Score | Vote | Weight | Weighted Score |
|-------|-------|------|--------|----------------|
| Code Reviewer | X/10 | AGREE/PARTIAL/DISAGREE | 1.5x | X |
| Silent Failure Hunter | X/10 | AGREE/PARTIAL/DISAGREE | 1.0x | X |
| Tester | X/10 | AGREE/PARTIAL/DISAGREE | 1.0x | X |
| Simplicity Enforcer | X/10 | AGREE/PARTIAL/DISAGREE | 2.0x | X |
| Type Analyst | X/10 | AGREE/PARTIAL/DISAGREE | 0.8x | X |
| Debug Specialist | X/10 | AGREE/PARTIAL/DISAGREE | 0.8x | X |
| Architect | X/10 | AGREE/PARTIAL/DISAGREE | 2.0x | X |

**Gewogen Gemiddelde:** [sum(weighted_scores) / sum(weights)]

### Stap 3: Genereer Rapport

```markdown
# Multiagent Analyse Rapport

## Executive Summary
[3-5 zinnen: consensus, key findings, aanbeveling]

## Consensus Assessment
**Consensus:** X% | **Gewogen Score:** X/10

## Per-Agent Bevindingen
[Korte samenvatting per agent]

## Discussiepunten
[Waar zijn agents het oneens?]

## Finale Aanbeveling
[GO / CONDITIONAL GO / NO GO met rationale]
```

### Stap 4: Update Status
Als de analyse is voltooid, update de relevante Linear issue met de bevindingen.


---

## Configuration Summary

| Setting | Value |
|---------|-------|
| **Mode** | Multiagent Consensus Framework |
| **Task Type** | review |
| **Depth** | deep (7 agents) |
| **Ultrathink** | ENABLED - Use extended thinking for deep analysis |
| **Consensus** | Required - synthesize all agent perspectives |

### Ultrathink Protocol

Extended thinking is **ENABLED**. Each agent should:

1. **Think deeply** before responding (use internal reasoning)
2. **Consider edge cases** and failure modes
3. **Challenge assumptions** in the prompt
4. **Provide detailed rationale** for each recommendation
5. **Score confidence levels** for uncertain conclusions
6. **Document assumptions** expliciet

### Alternative Execution Methods

**Via CLI:**
```bash
prompt-forge forge --type review --multiagent --depth deep --ultrathink "[your idea]"
```
