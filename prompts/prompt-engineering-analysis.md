# Prompt Engineering Analysis: Definitie Generator

## Execution Mode

**ULTRATHINK**: Activeer extended reasoning voor alle analyses. Neem de tijd voor diepgaande analyse voordat je conclusies trekt.

**MULTIAGENT STRATEGY**: Lanceer 10 gespecialiseerde agenten parallel voor maximale coverage en diverse perspectieven.

**CONSENSUS REQUIRED**: Alle aanbevelingen moeten consensus hebben tussen relevante agents voordat ze in het eindrapport komen.

---

## Consensus Framework

### Consensus Regels

1. **Unanimiteit vereist voor Critical Issues**: Issues met severity "CRITICAL" moeten door minimaal 3 relevante agents bevestigd worden
2. **Meerderheid voor Recommendations**: Aanbevelingen moeten door >50% van relevante agents ondersteund worden
3. **Conflict Resolution**: Bij tegenstrijdige bevindingen wordt een afweging gemaakt met gewogen stemmen

### Consensus Categorieën

| Categorie | Vereiste Consensus | Betrokken Agents |
|-----------|-------------------|------------------|
| Architecture Changes | 4/5 agents | Architect, Code Reviewer, Complexity Checker, PM, Explorer |
| Code Quality Issues | 3/4 agents | Code Reviewer, Tester, Complexity Checker, Type Analyst |
| Safety/Reliability | 3/3 agents | Silent Failure Hunter, Type Analyst, Debug Specialist |
| Business Priority | 2/2 agents | PM, Architect |
| Quick Wins | 5/10 agents | Alle agents mogen stemmen |

### Consensus Protocol

```
STAP 1: Individuele Agent Analyse
- Elke agent voert onafhankelijke analyse uit
- Output bevat: findings, severity, confidence score (0-100%)

STAP 2: Cross-Validation
- Agents reviewen elkaars findings binnen hun domein
- Markeer: AGREE | PARTIAL | DISAGREE

STAP 3: Conflict Resolution
- Bij DISAGREE: beide agents leveren onderbouwing
- Gewogen stem op basis van:
  * Relevantie voor het onderwerp (weight factor)
  * Confidence score van de finding
  * Evidence quality (code references, research backing)

STAP 4: Consensus Score Berekening
- Per finding: (agreeing_agents / relevant_agents) x 100%
- Threshold voor opname in rapport:
  * Critical: >=75% consensus
  * Important: >=60% consensus
  * Suggestion: >=50% consensus

STAP 5: Dissent Documentation
- Minderheidsstandpunten worden gedocumenteerd in appendix
- "Agent X disagreed because: [reasoning]"
```

### Consensus Voting Matrix Template

```
| Finding | CR | TE | AR | PM | CC | SFH | TA | DS | EX | RS | Consensus |
|---------|----|----|----|----|----|----|----|----|----|----|-----------|
| [desc]  | +  | -- | +  | +  | ?  | -- | -- | -- | +  | -- | 80% (4/5) |
| [desc]  | +  | +  | -- | -- | +  | +  | +  | -- | -- | -- | 100% (5/5)|
| [desc]  | -  | -- | +  | +  | -  | -- | -- | -- | +  | -- | 60% (3/5) |

Legend: CR=Code Reviewer, TE=Tester, AR=Architect, PM=Product Manager,
        CC=Complexity Checker, SFH=Silent Failure Hunter, TA=Type Analyst,
        DS=Debug Specialist, EX=Explorer, RS=Researcher
        -- = Not relevant for this finding
        +  = AGREE, - = DISAGREE, ? = PARTIAL
```

---

## Agent Configuratie

| # | Agent Role | Type | Focus Area | Vote Weight |
|---|------------|------|------------|-------------|
| 1 | **Code Reviewer** | `code-reviewer` | Prompt code quality, patterns | 1.5x |
| 2 | **Tester** | `pr-review-toolkit:pr-test-analyzer` | Test coverage voor prompt modules | 1.0x |
| 3 | **Architect** | `feature-dev:code-architect` | Prompt architectuur en module design | 2.0x |
| 4 | **Product Manager** | `product-manager` | Business value, user impact, prioritering | 1.5x |
| 5 | **Complexity Checker** | `code-simplifier` | Over-engineering detectie, simplificatie | 1.5x |
| 6 | **Silent Failure Hunter** | `pr-review-toolkit:silent-failure-hunter` | Error handling in prompt generation | 1.0x |
| 7 | **Type Design Analyst** | `pr-review-toolkit:type-design-analyzer` | Type safety in prompt data structures | 0.75x |
| 8 | **Debug Specialist** | `debug-specialist` | Logging, observability, debugging | 0.75x |
| 9 | **Codebase Explorer** | `Explore` | Brede codebase verkenning, patterns | 0.5x |
| 10 | **Research Agent** | `general-purpose` | Perplexity + Context7 research | 1.0x |

**Totaal Vote Weight: 11.5x** (gewogen consensus)

---

## Parallel Execution Strategy

```
Phase 1 (Parallel): Agents 1-5 + 9 lanceren voor codebase analyse
Phase 2 (Parallel): Agent 10 voor externe research
Phase 3 (Parallel): Agents 6-8 voor quality checks
Phase 4 (Sequential): CONSENSUS BUILDING - Cross-validation & voting
Phase 5 (Sequential): Consolidatie van alle bevindingen met consensus scores
```

---

## Opdracht

Voer een diepgaande analyse uit van de prompt-generatie architectuur in de Definitie-app codebase. Identificeer verbeterpunten en maak concrete aanbevelingen op basis van:
1. Huidige codebase analyse
2. Bestaande Linear issues
3. Best practices uit prompt engineering research

**Alle aanbevelingen moeten consensus hebben tussen de relevante agents.**

## Context

De Definitie-app is een Dutch AI-powered Definition Generator die GPT-4 gebruikt met 45 validatieregels (toetsregels) om juridische definities te genereren. De kwaliteit van de gegenereerde definities hangt direct af van de prompt architectuur.

---

## Fase 1: Codebase Analyse (Agents 1-5, 9)

### Agent Assignments

**Agent 1 (Code Reviewer):**
```
Analyseer prompt code quality in:
- src/services/prompts/*.py
- src/services/definition_generator_prompts.py
- config/prompt_modules/*.yaml (indien aanwezig)

Focus: Code smells, duplication, naming conventions, SOLID principles
Return:
- Quality score (1-10) with confidence %
- Top 5 issues with severity (CRITICAL/HIGH/MEDIUM/LOW)
- Recommended fixes
- VOTE on findings from other agents in your domain
```

**Agent 2 (Tester):**
```
Analyseer test coverage voor prompt-gerelateerde code:
- tests/**/test_*prompt*.py
- tests/**/test_*generation*.py

Focus: Coverage gaps, missing edge cases, test quality
Return:
- Coverage % with confidence
- Untested scenarios (severity rated)
- Test recommendations
- VOTE on code quality findings that affect testability
```

**Agent 3 (Architect):**
```
Analyseer de prompt architectuur:
- src/services/prompts/modules/prompt_orchestrator.py
- src/services/prompts/modular_prompt_adapter.py
- src/services/definition_generator_context.py

Focus: Module design, data flow, coupling, extensibility
Return:
- Architecture diagram (text)
- Design patterns used
- Architectural debt with severity
- VOTE on all architecture-related findings from other agents
```

**Agent 4 (Product Manager):**
```
Analyseer business impact van prompt kwaliteit:
- Haal Linear issues op met "prompt", "generatie", "definitie", "kwaliteit"
- Categoriseer in bugs/enhancements/tech debt
- Prioriteer op business value

Focus: User impact, ROI van verbeteringen, roadmap alignment
Return:
- Prioritized issue list
- Business case voor top 3 improvements
- VOTE on priority of all findings from other agents
```

**Agent 5 (Complexity Checker):**
```
Analyseer complexiteit en over-engineering:
- src/services/prompts/ (alle bestanden)
- Cyclomatic complexity
- Lines of code vs functionality

Focus: Onnodige abstracties, simplificatie mogelijkheden, KISS violations
Return:
- Complexity score (1-10)
- Simplification opportunities with effort estimate
- VOTE on whether proposed changes add unnecessary complexity
```

**Agent 9 (Codebase Explorer):**
```
Brede verkenning van prompt-gerelateerde code:
- Zoek alle bestanden met "prompt" in naam of inhoud
- Map dependencies tussen prompt modules
- Identificeer de 15 geregistreerde modules in PromptOrchestrator

Focus: Complete picture, hidden dependencies, documentation gaps
Return:
- File inventory
- Dependency graph
- Documentation status
- PROVIDE CONTEXT for other agents' findings
```

### 1.1 Prompt Architectuur Mapping

Analyseer de volgende bestanden en documenteer de huidige architectuur:

```
src/services/prompts/
├── modular_prompt_adapter.py      # Adapter naar modulaire architectuur
├── prompt_service_v2.py           # V2 prompt service
└── modules/
    └── prompt_orchestrator.py     # Orchestratie van prompt modules

src/services/
├── definition_generator_prompts.py  # UnifiedPromptBuilder
├── definition_generator_context.py  # Context management
└── generation/
    └── unified_definition_generator.py  # Core generation
```

Beantwoord:
- Hoe worden prompts opgebouwd (welke modules, volgorde)?
- Welke 15 modules zijn geregistreerd in PromptOrchestrator?
- Hoe wordt ontologische categorie (type/proces/resultaat/exemplaar) verwerkt?
- Hoe worden de 45 toetsregels in de prompt geïnjecteerd?
- Waar zit de meeste complexiteit/duplicatie?

### 1.2 Token Efficiency Analyse

Onderzoek token usage:
- Meet/schat prompt lengte voor typische generatie requests
- Identificeer redundante of overbodige prompt secties
- Analyseer de verhouding instructies vs context vs voorbeelden

### 1.3 Prompt Quality Indicators

Check de huidige prompts op:
- Duidelijkheid van instructies
- Consistentie in formatting
- Effectiviteit van few-shot examples
- Handling van edge cases
- Nederlandse taalspecifieke overwegingen

---

## Fase 2: Quality & Safety Checks (Agents 6-8)

### Agent Assignments

**Agent 6 (Silent Failure Hunter):**
```
Zoek silent failures in prompt generatie:
- Exception handling in prompt builders
- Fallback logic bij missing context
- Error propagation naar UI

Focus: Silent failures, swallowed exceptions, missing error feedback
Return:
- Risk assessment (LOW/MEDIUM/HIGH/CRITICAL)
- Found issues with evidence
- Fix recommendations
- VOTE on safety-related findings from other agents
```

**Agent 7 (Type Design Analyst):**
```
Analyseer type safety in prompt data structures:
- PromptContext types
- Module input/output types
- Configuration types

Focus: Type coverage, invariant enforcement, runtime safety
Return:
- Type design score (1-10)
- Unsafe patterns found
- Improvement suggestions
- VOTE on type-related issues found by Code Reviewer
```

**Agent 8 (Debug Specialist):**
```
Analyseer debugging & observability:
- Logging in prompt generation
- Traceability van prompt components
- Performance monitoring

Focus: Debug capability, logging quality, observability gaps
Return:
- Debugging score (1-10)
- Logging recommendations
- Monitoring suggestions
- VOTE on observability-related findings
```

---

## Fase 3: Research & Best Practices (Agent 10)

### Agent Assignment

**Agent 10 (Research Agent):**
```
Voer externe research uit met Perplexity en Context7:

PERPLEXITY QUERIES:
1. "Best practices for GPT-4 prompt engineering for structured text generation 2024"
2. "Prompt optimization techniques for reducing token usage while maintaining quality"
3. "Chain-of-thought prompting vs direct instruction for definition generation"
4. "Dutch language NLP prompt engineering considerations"
5. "Modular prompt architecture patterns for enterprise applications"

CONTEXT7 LOOKUPS:
1. OpenAI API documentation - prompt best practices
2. Anthropic prompt engineering guide
3. LangChain prompt templates (indien relevant)

Focus: Industry best practices, academic research, proven patterns
Return:
- Synthesized findings with sources
- Applicable recommendations
- PROVIDE EVIDENCE for/against findings from other agents
```

### 3.1 Linear Issues Ophalen

Gebruik `mcp__linear-mcp__linear_search_issues` met query termen:
- "prompt"
- "generatie"
- "definitie"
- "GPT"
- "token"
- "kwaliteit"

### 3.2 Categoriseer & Prioriteer

Groepeer gevonden issues en maak prioriteitsmatrix (impact vs effort).

---

## Fase 4: Consensus Building

### 4.1 Cross-Validation Round

Elke agent reviewt findings van andere agents binnen hun domein:

```
Code Reviewer reviews: Architect (code aspects), Tester (test recommendations)
Architect reviews: Code Reviewer (patterns), Complexity Checker (abstractions)
PM reviews: All agents (priority/business value)
Complexity Checker reviews: Architect (over-engineering), Code Reviewer (simplicity)
Tester reviews: Code Reviewer (testability)
Silent Failure Hunter reviews: Type Analyst, Debug Specialist
Type Analyst reviews: Code Reviewer (type issues)
Debug Specialist reviews: Silent Failure Hunter (logging)
Explorer: Provides context for all
Researcher: Provides evidence for all
```

### 4.2 Voting Round

Alle agents stemmen op de gecombineerde findings:

```
Voor elke finding:
1. Is dit een valide issue? (JA/NEE/PARTIAL)
2. Is de severity correct? (AGREE/TOO_HIGH/TOO_LOW)
3. Is de voorgestelde fix correct? (AGREE/ALTERNATIVE/DISAGREE)
4. Wat is de prioriteit? (P1/P2/P3/P4)
```

### 4.3 Consensus Score Berekening

```python
def calculate_consensus(finding, votes, weights):
    weighted_agree = sum(w for agent, vote, w in zip(agents, votes, weights) if vote == 'AGREE')
    weighted_total = sum(w for agent, w in zip(agents, weights) if agent.is_relevant(finding))
    return weighted_agree / weighted_total * 100

# Thresholds
CRITICAL_THRESHOLD = 75%
IMPORTANT_THRESHOLD = 60%
SUGGESTION_THRESHOLD = 50%
```

### 4.4 Dissent Documentation

Voor findings waar consensus <100%:
```markdown
### Dissenting Opinion: [Finding Title]

**Majority View (X agents, Y% consensus):**
[Description of majority position]

**Minority View (Z agents):**
- Agent [Name]: [Reasoning for disagreement]
- Agent [Name]: [Reasoning for disagreement]

**Resolution:** [How this was handled in final recommendations]
```

---

## Fase 5: Consolidatie & Synthese

### Multi-Agent Consensus Report

Na alle agent outputs en voting:

1. **Filter by Consensus**: Alleen findings met voldoende consensus
2. **Rank by Priority**: Gewogen combinatie van severity + business value
3. **Group by Theme**: Cluster gerelateerde findings
4. **Document Dissent**: Appendix met minderheidsstandpunten

### Final Score Aggregatie

| Agent | Focus | Score | Weight | Consensus Contribution |
|-------|-------|-------|--------|------------------------|
| Code Reviewer | Quality | ?/10 | 15% | X findings accepted |
| Tester | Coverage | ?/10 | 10% | X findings accepted |
| Architect | Design | ?/10 | 20% | X findings accepted |
| PM | Business Value | ?/10 | 15% | X findings accepted |
| Complexity Checker | Simplicity | ?/10 | 15% | X findings accepted |
| Silent Failure Hunter | Safety | ?/10 | 10% | X findings accepted |
| Type Analyst | Type Safety | ?/10 | 5% | X findings accepted |
| Debug Specialist | Observability | ?/10 | 5% | X findings accepted |
| Explorer | Completeness | ?/10 | 2.5% | Context provided |
| Researcher | Best Practices | ?/10 | 2.5% | Evidence provided |

**Gewogen Totaal Score: ?/10**
**Overall Consensus Rate: ?%**

---

## Concrete Aanbevelingen (Consensus Required)

### Deliverables

1. **Architecture Diagram**: Visuele weergave van huidige prompt flow
2. **Gap Analysis**: Tabel met huidige staat vs best practices
3. **Improvement Roadmap**: Geprioriteerde lijst van verbeteringen met:
   - Beschrijving
   - Impact (1-5)
   - Effort (1-5)
   - Dependencies
   - Gerelateerde Linear issues
   - **Consensus Score (%)**
   - **Dissenting Opinions (indien van toepassing)**

4. **Quick Wins**: 3-5 verbeteringen die <2 uur kosten (>=50% consensus)
5. **Strategic Recommendations**: Grotere architectural changes (>=75% consensus)

### Specifieke Vragen te Beantwoorden (Consensus Required)

| Vraag | Minimum Consensus |
|-------|-------------------|
| 1. Moeten we de 15 prompt modules consolideren of verder opsplitsen? | 75% (Architect, CR, CC, PM) |
| 2. Is de huidige token usage acceptabel of moet dit geoptimaliseerd? | 60% (All agents) |
| 3. Hoe kunnen we de ontologische classificatie beter in de prompt verwerken? | 75% (Architect, CR, Researcher) |
| 4. Zijn er toetsregels die conflicteren of redundant zijn in de prompt? | 60% (CR, Tester, Architect) |
| 5. Hoe kunnen we prompt-kwaliteit meten en monitoren? | 60% (PM, DS, Tester) |
| 6. Moet er een A/B testing framework komen voor prompt varianten? | 75% (PM, Architect, Tester, CR) |

---

## Output Format

```markdown
# Definitie Generator Prompt Analysis Report

## Executive Summary
[2-3 alinea's met key findings - alleen consensus items]

## Consensus Overview
- Total Findings Analyzed: X
- Findings with Full Consensus (100%): Y
- Findings with Majority Consensus (>=60%): Z
- Findings Rejected (<50% consensus): W
- Overall Consensus Rate: X%

## Agent Scores Overview
[Tabel met alle 10 agent scores, gewogen totaal, en consensus contributions]

## 1. Current Architecture (Architect + Explorer)
### 1.1 Component Overview
### 1.2 Data Flow Diagram
### 1.3 Module Inventory (15 modules)
### 1.4 Strengths & Weaknesses
**Consensus: X%** | Dissent: [if any]

## 2. Code Quality Analysis (Code Reviewer + Complexity Checker)
### 2.1 Quality Score
### 2.2 Complexity Assessment
### 2.3 Technical Debt Identified
### 2.4 Refactoring Opportunities
**Consensus: X%** | Dissent: [if any]

## 3. Safety & Reliability (Silent Failure Hunter + Type Analyst + Debug Specialist)
### 3.1 Error Handling Assessment
### 3.2 Type Safety Analysis
### 3.3 Observability Gaps
**Consensus: X%** | Dissent: [if any]

## 4. Test Coverage (Tester)
### 4.1 Current Coverage
### 4.2 Missing Test Scenarios
### 4.3 Test Quality
**Consensus: X%** | Dissent: [if any]

## 5. Linear Issues Overview (PM)
### 5.1 Related Issues Found
### 5.2 Issue Categorization
### 5.3 Business Priority Matrix
**Consensus: X%** | Dissent: [if any]

## 6. Research Findings (Researcher)
### 6.1 Industry Best Practices
### 6.2 Gap Analysis vs Best Practices
### 6.3 Dutch Language Considerations
### 6.4 Sources & Citations

## 7. Recommendations (CONSENSUS REQUIRED)

### 7.1 Quick Wins (This Week) - <2h each
| # | Recommendation | Consensus | Dissent |
|---|----------------|-----------|---------|
| 1 | [desc] | 85% (8/10) | Agent X: [reason] |
| 2 | [desc] | 100% (10/10) | None |

### 7.2 Short Term (This Month) - 2-8h each
[Same format with consensus scores]

### 7.3 Long Term (This Quarter) - >8h each
[Same format with consensus scores]

### 7.4 Rejected Recommendations (<50% consensus)
| # | Recommendation | Consensus | Why Rejected |
|---|----------------|-----------|--------------|
| 1 | [desc] | 40% | [summary of objections] |

## 8. Implementation Roadmap
[Dependency graph of improvements - consensus items only]

## 9. Metrics & Success Criteria
[How to measure improvement]

## 10. Consensus Voting Matrix
[Full voting matrix for all findings]

## Appendices
- A: Full Agent Reports
- B: Dissenting Opinions (Full Detail)
- C: Linear Issues List
- D: Research Sources
- E: Token Analysis Data
- F: Architecture Diagrams
```

---

## Constraints

- **ULTRATHINK**: Neem de tijd voor diepgaande analyse
- **CONSENSUS REQUIRED**: Geen aanbevelingen zonder voldoende agent consensus
- **Parallel Execution**: Maximaliseer efficientie met parallel agents
- Focus op actionable recommendations, niet alleen beschrijvend
- Houd rekening met solo developer context (geen team overhead)
- Prioriteer kwaliteit boven complexiteit
- Nederlandse context is belangrijk (juridische termen, taalspecifiek)
- Budget-bewust: token costs zijn relevant

## Tools Beschikbaar

- File reading (Read, Glob, Grep)
- Task tool voor multiagent orchestratie
- Linear MCP (issues ophalen)
- Perplexity MCP (research)
- Context7 MCP (documentation)
- Bash (git history, stats)

---

## Execution Command

```
Phase 1: Parallel lanceren van Agents 1-5 en 9 (codebase analyse)
Phase 2: Parallel lanceren van Agent 10 (research)
Phase 3: Parallel lanceren van Agents 6-8 (quality checks)
Phase 4: CONSENSUS BUILDING
  - Cross-validation tussen agents
  - Voting round op alle findings
  - Consensus score berekening
  - Dissent documentation
Phase 5: Consolidatie met consensus filtering
Phase 6: Genereer finale rapport met consensus scores
```
