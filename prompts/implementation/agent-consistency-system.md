# Agent Consistency System - Architectuur & Implementatie

> **Doel**: Ontwerp een systeem dat zorgt voor consistente, reproduceerbare output van Claude Code agents
> **Versie**: 2.0 - Volledige implementatie met templates, decision trees, en enforcement
> **Status**: READY FOR EXECUTION

---

## Execution Mode

| Setting | Value |
|---------|-------|
| **ULTRATHINK** | Ja - Extended reasoning voor systeemontwerp |
| **MULTIAGENT** | 6 gespecialiseerde agents |
| **CONSENSUS** | Vereist voor alle design decisions (>=75%) |

---

## Agent Configuratie

| # | Agent Role | Type | Focus Area | Vote Weight |
|---|------------|------|------------|-------------|
| 1 | **Architect** | `feature-dev:code-architect` | Systeem design, component specificaties | 2.0x |
| 2 | **Code Reviewer** | `code-reviewer` | Implementation quality, best practices | 1.5x |
| 3 | **Complexity Checker** | `code-simplifier` | KISS enforcement, MVP scoping | 1.5x |
| 4 | **Explorer** | `Explore` | Bestaande structuur, gap analyse | 1.0x |
| 5 | **Researcher** | `general-purpose` | Industry patterns, Claude Code capabilities | 1.0x |
| 6 | **Product Manager** | `product-manager` | Prioritering, success criteria | 1.5x |

**Totaal Vote Weight: 8.5x**

---

## Opdracht

Ontwerp en lever een compleet **Agent Consistency System** dat de volgende problemen oplost:

| Probleem | Symptoom | Impact |
|----------|----------|--------|
| Inconsistente analyses | 3x zelfde prompt = 3 verschillende outputs | Onbetrouwbare resultaten |
| Willekeurige focus | Agent kiest zelf wat te analyseren | Missende secties |
| Geen output structuur | Elke run andere format | Moeilijk vergelijkbaar |
| Ad-hoc implementaties | 3x zelfde fix = 3 aanpakken | Inconsistente code style |
| Zwakke enforcement | CLAUDE.md is suggestie | Conventies genegeerd |

---

## Context

### Huidige Situatie (Probleem)

```
User Prompt: "Analyseer de validation service"
    |
    v
Claude Code Agent (non-deterministic)
    |
    v
Output (VARIABEL!)
    |-- Run 1: Focus op error handling, mist performance
    |-- Run 2: Focus op architecture, mist error handling
    +-- Run 3: Focus op types, mist architecture
```

### Gewenste Situatie (Oplossing)

```
User Prompt: "Analyseer de validation service"
    |
    v
+-----------------------------------------------+
|  TEMPLATE ENGINE                              |
|  - Detecteert: ANALYSIS taak                  |
|  - Laadt: TEMPLATE-analysis.md                |
|  - Verplicht: 6 secties, checklist, format    |
+-----------------------------------------------+
    |
    v
+-----------------------------------------------+
|  DECISION TREE ENGINE                         |
|  - Bepaalt: scope (klein/medium/groot)        |
|  - Selecteert: 4/6/8 agents                   |
|  - Configureert: consensus thresholds         |
+-----------------------------------------------+
    |
    v
+-----------------------------------------------+
|  MULTI-AGENT EXECUTION                        |
|  +-----+ +-----+ +-----+ +-----+              |
|  | A1  | | A2  | | A3  | | A4  |   parallel   |
|  +--+--+ +--+--+ +--+--+ +--+--+              |
|     |       |       |       |                 |
|     +-------+-------+-------+                 |
|             |                                 |
|             v                                 |
|     CONSENSUS ENGINE                          |
|     - Cross-validation                        |
|     - Voting (weighted)                       |
|     - Conflict resolution                     |
+-----------------------------------------------+
    |
    v
DETERMINISTIC OUTPUT (consistent format)
```

### Bestaande Assets

| Asset | Locatie | Status |
|-------|---------|--------|
| Deep Analysis Template | `prompts/templates/TEMPLATE-deep-analysis.md` | Aanwezig, uitbreiden |
| Hookify rule | `.claude/hookify.prompt-first-workflow.local.md` | Aanwezig, uitbreiden |
| CLAUDE.md | `CLAUDE.md` | Aanwezig, sectie toevoegen |
| Prompt README | `prompts/README.md` | Aanwezig |

---

## Fasen

### Fase 1: Discovery & Research (Parallel)

**Agent 4 (Explorer):**
```
VERKEN bestaande structuur:
1. ~/.claude/plugins/marketplaces/claude-code-plugins/plugins/
   - Inventariseer alle beschikbare agents
   - Map trigger conditions
   - Documenteer output variaties

2. Project prompts/
   - Analyseer bestaande templates
   - Identificeer gaps in coverage
   - Check consistency tussen templates

DELIVERABLE:
- Agent inventory tabel
- Template gap analyse
- Aanbevelingen voor standaardisatie
```

**Agent 5 (Researcher):**
```
RESEARCH via Perplexity:
1. "Claude Code plugin best practices for consistent output 2024"
2. "LLM prompt engineering deterministic output techniques"
3. "Multi-agent consensus frameworks implementation patterns"

RESEARCH via Context7:
1. Claude Code SDK documentation
2. Hookify plugin capabilities

DELIVERABLE:
- Best practices samenvatting
- Applicable patterns voor dit project
- Limitations en workarounds
```

---

### Fase 2: Architecture Design (Sequential)

**Agent 1 (Architect):**
```
ONTWERP het Agent Consistency System met 3 componenten:

COMPONENT 1: TEMPLATE ENGINE
- Template per taaktype (analyse/review/implementatie/fix)
- Verplichte secties per template
- Output schema validation
- Pre-execution checklist

COMPONENT 2: DECISION TREE FRAMEWORK
- Scope detectie (klein/medium/groot)
- Agent selectie matrix
- Consensus threshold bepaling
- Implementation pattern matching

COMPONENT 3: ENFORCEMENT LAYER
- Hookify rules voor template enforcement
- CLAUDE.md integration
- Validation hooks

DELIVERABLE:
- Component diagram (text-based)
- Interface specificaties
- Data flow beschrijving
- Integration points
```

**Agent 3 (Complexity Checker):**
```
REVIEW het architectuurvoorstel:
- Identificeer over-engineering risico's
- Bepaal MVP vs nice-to-have
- Schat implementation effort
- Check solo developer haalbaarheid

DELIVERABLE:
- Simplificatie aanbevelingen
- MVP scope definitie
- Effort matrix (uren per component)
- Risk assessment
```

---

### Fase 3: Implementation Design (Parallel)

**Agent 2 (Code Reviewer):**
```
SPECIFICEER de concrete deliverables:

FILE 1: prompts/TEMPLATE-analysis.md
- 6 verplichte secties
- Pre-execution checklist
- Output format met placeholders
- Agent selectie guidance

FILE 2: prompts/TEMPLATE-implementation.md
- Decision tree voor aanpak selectie
- Verplichte acceptatie criteria
- Test requirements
- Rollback plan template

FILE 3: prompts/TEMPLATE-review.md
- Checklist-driven review process
- Severity classification
- Blocking vs non-blocking issues
- Consensus verdeling

FILE 4: prompts/TEMPLATE-fix.md
- Root cause analyse template
- Regression test requirements
- Monitoring additions
- Post-mortem format

DELIVERABLE:
- Volledige template inhoud per file
- Validation rules per template
- Example filled-in version
```

**Agent 6 (Product Manager):**
```
DEFINIEER success criteria en prioritering:

SUCCESS METRICS:
- Analyse consistentie: 3x zelfde prompt = >=80% output overlap
- Template compliance: 100% verplichte secties aanwezig
- Decision tree coverage: top 10 common patterns
- Enforcement effectiviteit: <5% bypass rate

PRIORITERING:
- P0: Templates (direct waarde)
- P1: Decision trees (consistentie)
- P2: Hookify enforcement (preventie)
- P3: Multi-agent consensus (kwaliteit)

DELIVERABLE:
- Success criteria tabel
- Prioritering matrix met rationale
- Rollout plan
- Risk/mitigation mapping
```

---

### Fase 4: Decision Tree Specification

**Agent 1 (Architect) + Agent 2 (Code Reviewer):**
```
SPECIFICEER decision tree voor implementation patterns:

ROOT: Wat is het type wijziging?
|
+-- BUG FIX
|   +-- Severity?
|   |   +-- P0 (production down): Hotfix pattern
|   |   +-- P1 (major broken): Standard fix + tests
|   |   +-- P2/P3 (minor): Batch met andere fixes
|   +-- Root cause bekend?
|       +-- Ja: Direct fixen
|       +-- Nee: Debug-first pattern
|
+-- NEW FEATURE
|   +-- Scope?
|   |   +-- <50 LOC: Inline implementatie
|   |   +-- 50-200 LOC: Module toevoegen
|   |   +-- >200 LOC: Refactor-first pattern
|   +-- Heeft dependencies?
|       +-- Ja: Dependency-injection pattern
|       +-- Nee: Direct implementatie
|
+-- REFACTORING
|   +-- Backwards compatible?
|   |   +-- Ja: Incremental pattern
|   |   +-- Nee: Migration pattern
|   +-- Test coverage?
|       +-- >=80%: Refactor direct
|       +-- <80%: Tests-first pattern
|
+-- MIGRATION
    +-- Database?
    |   +-- Schema: Migration script pattern
    |   +-- Data: ETL pattern
    +-- Code?
        +-- Breaking: Deprecation pattern
        +-- Non-breaking: Shadow pattern

DELIVERABLE:
- Complete decision tree YAML
- Pattern descriptions
- Example per pattern
```

---

### Fase 5: Enforcement Specification

**Agent 2 (Code Reviewer):**
```
SPECIFICEER hookify enforcement rules:

RULE 1: Template Compliance Check
- Trigger: PostToolUse op Write naar prompts/
- Validation: Alle verplichte secties aanwezig
- Action: Warn als secties missen

RULE 2: Output Format Enforcement
- Trigger: Stop event
- Validation: Output bevat verwachte headers
- Action: Suggest missing sections

RULE 3: Decision Tree Adherence
- Trigger: PreToolUse op Edit voor implementation
- Validation: Pattern gekozen via decision tree
- Action: Prompt voor pattern selectie

DELIVERABLE:
- Hookify rule YAML per regel
- Test scenarios
- Bypass conditions (wanneer mag het overgeslagen worden)
```

---

### Fase 5B: Agent Output Consistency Rules

**Agent 1 (Architect) + Agent 2 (Code Reviewer):**
```
SPECIFICEER output consistency regels per agent type:

PROBLEEM: Agents returnen inconsistente output
- Soms volledige content, soms samenvatting
- Soms alleen bestand opslaan, soms ook CLI tonen
- Geen standaard output format

ONTWERP regels voor:

1. PROMPT-WRITER agent:
   - MOET: Volledige prompt returnen in final report
   - MOET: Tonen in CLI (niet alleen samenvatting)
   - MAG: Ook opslaan in bestand

2. EXPLORE agent:
   - MOET: Gestructureerde inventory tabel
   - MOET: Antwoord op specifieke vragen
   - MAG NIET: Alleen "ik heb X gevonden" zonder details

3. CODE-REVIEWER agent:
   - MOET: Alle findings met file:line references
   - MOET: Severity per finding
   - MOET: Concrete fix suggestions

4. GENERAL-PURPOSE (Researcher) agent:
   - MOET: Bronvermelding bij elke claim
   - MOET: Samenvatting + details (niet alleen één van beide)
   - MOET: Applicable recommendations

5. ALLE agents:
   - MOET: Output in markdown format
   - MOET: Tabellen waar data vergelijkbaar is
   - MOET: Code blocks voor code/config
   - MAG NIET: Alleen verwijzen naar opgeslagen bestand

DELIVERABLE:
- Agent output rules YAML config
- Per-agent output template
- Validation criteria
- Hookify enforcement rule voor output compliance
```

---

### Fase 6: Consensus Building

**Cross-Validation Matrix:**
```
Architect        validates: Code Reviewer (implementability), Complexity (feasibility)
Code Reviewer    validates: Architect (patterns), Explorer (completeness)
Complexity       validates: Architect (simplicity), PM (scope)
Explorer         provides:  Context for all agents
Researcher       provides:  Evidence for design decisions
PM               validates: All agents (business value)
```

**Consensus Questions:**

| # | Question | Required Consensus | Relevant Agents |
|---|----------|-------------------|-----------------|
| 1 | Is template-driven approach voldoende voor MVP? | >=75% | AR, CR, CC, PM |
| 2 | Hoeveel verplichte secties per template type? | >=60% | AR, CC |
| 3 | Decision tree: YAML config vs hardcoded logic? | >=75% | AR, CR, CC |
| 4 | Enforcement: hookify-only vs CLAUDE.md + hookify? | >=75% | CR, CC, PM |
| 5 | MVP scope: welke 2 templates eerst? | >=60% | PM, AR, CC |
| 6 | Agent output: altijd CLI tonen + bestand, of keuze aan agent? | >=75% | AR, CR, CC, PM |
| 7 | Output format: strikte YAML schema of loose markdown? | >=60% | AR, CR |

---

## Output Format

```markdown
# Agent Consistency System - Design Document

## Executive Summary
[2-3 paragrafen met gekozen aanpak, MVP scope, en expected impact]

## Consensus Overview
| Metric | Value |
|--------|-------|
| Design Decisions Analyzed | X |
| Full Consensus (100%) | Y |
| Majority Consensus (>=60%) | Z |
| Rejected (<50%) | W |
| Overall Agreement Rate | X% |

## 1. System Architecture

### 1.1 Component Overview
[Text-based diagram]

### 1.2 Data Flow
[Sequence diagram in text]

### 1.3 Integration Points
[Table met bestaande systemen]

## 2. Template Specifications

### 2.1 TEMPLATE-analysis.md
```markdown
[VOLLEDIGE TEMPLATE INHOUD - COPY-PASTE READY]
```

### 2.2 TEMPLATE-implementation.md
```markdown
[VOLLEDIGE TEMPLATE INHOUD - COPY-PASTE READY]
```

### 2.3 TEMPLATE-review.md
```markdown
[VOLLEDIGE TEMPLATE INHOUD - COPY-PASTE READY]
```

### 2.4 TEMPLATE-fix.md
```markdown
[VOLLEDIGE TEMPLATE INHOUD - COPY-PASTE READY]
```

## 3. Decision Tree Framework

### 3.1 Implementation Patterns Tree
```yaml
[VOLLEDIGE DECISION TREE - COPY-PASTE READY]
```

### 3.2 Agent Selection Matrix
[Table met scope -> agents mapping]

### 3.3 Consensus Threshold Matrix
[Table met decision type -> threshold]

## 4. Enforcement Layer

### 4.1 Hookify Rules
```yaml
[VOLLEDIGE HOOKIFY CONFIG - COPY-PASTE READY]
```

### 4.2 CLAUDE.md Additions
```markdown
[EXACTE TOEVOEGINGEN - COPY-PASTE READY]
```

## 5. Agent Output Consistency Rules

### 5.1 Per-Agent Output Rules
```yaml
[AGENT OUTPUT RULES - COPY-PASTE READY]

# Format:
# agent_type:
#   must:
#     - rule 1
#     - rule 2
#   must_not:
#     - anti-pattern 1
#   format:
#     - format requirement
```

### 5.2 Output Validation Hookify Rule
```yaml
[HOOKIFY RULE VOOR OUTPUT COMPLIANCE - COPY-PASTE READY]
```

## 6. Implementation Roadmap

### Phase 1: MVP (Week 1)
| # | Deliverable | Effort | Owner |
|---|-------------|--------|-------|
| 1 | TEMPLATE-analysis.md | 2h | - |
| 2 | TEMPLATE-implementation.md | 2h | - |
| 3 | Basic hookify enforcement | 1h | - |
| 4 | CLAUDE.md updates | 30m | - |

### Phase 2: Enhancement (Week 2)
| # | Deliverable | Effort | Owner |
|---|-------------|--------|-------|

### Phase 3: Full System (Backlog)
| # | Deliverable | Effort | Owner |
|---|-------------|--------|-------|

## 7. Voting Matrix

| Decision | AR | CR | CC | EX | RS | PM | Consensus |
|----------|----|----|----|----|----|----|-----------|
| [desc] | + | + | + | -- | -- | + | 100% (4/4) |

Legend: + = AGREE | - = DISAGREE | ? = PARTIAL | -- = Not relevant

## 8. Dissenting Opinions
[Documentatie van minderheidsstandpunten per afgewezen beslissing]

## 9. Success Criteria

| Criterium | Target | Measurement |
|-----------|--------|-------------|
| Analyse consistentie | >=80% overlap bij 3x run | Manual comparison |
| Template compliance | 100% verplichte secties | Hookify validation |
| Decision tree coverage | Top 10 patterns | Pattern usage tracking |
| Enforcement bypass | <5% | Hookify logs |

## 10. Appendices

### A. Full Agent Reports
[Per agent: volledige analyse output]

### B. Research Findings
[Perplexity + Context7 resultaten]

### C. Rejected Alternatives
[Overwogen maar afgewezen opties met rationale]
```

---

## Constraints

| Constraint | Impact |
|------------|--------|
| **Solo Developer** | Geen team overhead, max 8h implementation per fase |
| **MVP First** | Alleen essentials in Phase 1 |
| **Backwards Compatible** | Bestaande prompts blijven werken |
| **KISS** | Geen custom tooling als hookify/prompts voldoen |
| **Copy-Paste Ready** | Alle deliverables direct bruikbaar |

---

## Input Files

| File | Purpose |
|------|---------|
| `~/.claude/plugins/marketplaces/claude-code-plugins/` | Agent inventory |
| `prompts/templates/TEMPLATE-deep-analysis.md` | Bestaand template als basis |
| `prompts/README.md` | Huidige documentatie |
| `CLAUDE.md` | Project conventions |
| `.claude/hookify.*.local.md` | Bestaande hookify rules |
| `prompts/implementation/implementation-plan-claude-agents.md` | Eerder werk |

---

## Execution Command

```
PHASE 1: PARALLEL
  - Agent 4 (Explorer): Inventory bestaande structuur
  - Agent 5 (Researcher): Best practices research
  [Wait for completion - context needed for design]

PHASE 2: SEQUENTIAL
  - Agent 1 (Architect): System design
  - Agent 3 (Complexity Checker): Review design
  [Wait for consensus on architecture]

PHASE 3: PARALLEL
  - Agent 2 (Code Reviewer): Template specifications
  - Agent 6 (PM): Success criteria + prioritering
  - Agent 1 (Architect): Decision tree specification
  [Wait for completion]

PHASE 4: SEQUENTIAL
  - Agent 2 (Code Reviewer): Enforcement specification
  [Wait for completion]

PHASE 5: CONSENSUS BUILDING
  - Cross-validation round
  - Voting on 5 key decisions
  - Conflict resolution
  - Dissent documentation

PHASE 6: DELIVERABLES GENERATION
  - Generate all templates (copy-paste ready)
  - Generate decision tree YAML
  - Generate hookify rules
  - Generate CLAUDE.md additions
```

---

## Success Definition

Na uitvoering van deze prompt zijn de volgende deliverables KLAAR VOOR IMPLEMENTATIE:

| # | Deliverable | Format | Location |
|---|-------------|--------|----------|
| 1 | TEMPLATE-analysis.md | Markdown | `prompts/templates/` |
| 2 | TEMPLATE-implementation.md | Markdown | `prompts/templates/` |
| 3 | TEMPLATE-review.md | Markdown | `prompts/templates/` |
| 4 | TEMPLATE-fix.md | Markdown | `prompts/templates/` |
| 5 | Decision Tree Config | YAML | `prompts/templates/decision-trees/` |
| 6 | Hookify Enforcement Rules | YAML frontmatter | `.claude/` |
| 7 | CLAUDE.md Updates | Markdown section | Root |
| 8 | Agent Output Rules | YAML | `prompts/templates/decision-trees/` |

---

## Pre-Execution Checklist

| Check | Status |
|-------|--------|
| [ ] Alle agents beschikbaar in Claude Code | |
| [ ] Perplexity MCP geconfigureerd voor Researcher | |
| [ ] Context7 beschikbaar voor documentation lookup | |
| [ ] Write access tot prompts/ directory | |
| [ ] Geen uncommitted changes in target files | |

---

## Post-Execution Validation

Na completion, valideer:

| Validation | Method |
|------------|--------|
| Templates syntactically correct | Markdown lint |
| Decision tree parseable | YAML validation |
| Hookify rules loadable | Restart Claude Code |
| No regression in existing prompts | Run existing prompt |
| CLAUDE.md still valid | Read and verify |
