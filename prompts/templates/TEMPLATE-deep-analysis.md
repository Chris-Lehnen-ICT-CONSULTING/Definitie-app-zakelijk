# Deep Analysis Template v2.0

> **Gebruik**: Kopieer dit template en vul de [PLACEHOLDERS] in voor je specifieke analyse.
> **Versie**: 2.0 - Best of both worlds (model selectie + voting matrix + visuele diagrams)

---

## Execution Mode

| Setting | Value |
|---------|-------|
| **ULTRATHINK** | Ja - Extended reasoning voor alle analyses |
| **MULTIAGENT** | [AANTAL] gespecialiseerde agents |
| **CONSENSUS** | Vereist voor alle aanbevelingen |

---

## Agent Configuratie

| # | Agent Role | Type | Model | Focus Area | Vote Weight |
|---|------------|------|-------|------------|-------------|
| 1 | **Code Reviewer** | `code-reviewer` | opus | Code quality, patterns, anti-patterns | 1.5x |
| 2 | **Tester** | `pr-review-toolkit:pr-test-analyzer` | opus | Test coverage, edge cases | 1.0x |
| 3 | **Architect** | `feature-dev:code-architect` | opus | Architecture, module design | 2.0x |
| 4 | **Product Manager** | `product-manager` | opus | Business value, prioritering | 1.5x |
| 5 | **Complexity Checker** | `code-simplifier` | opus | Over-engineering, simplificatie | 1.5x |
| 6 | **Silent Failure Hunter** | `pr-review-toolkit:silent-failure-hunter` | opus | Error handling, silent failures | 1.0x |
| 7 | **Type Analyst** | `pr-review-toolkit:type-design-analyzer` | opus | Type safety, data structures | 0.75x |
| 8 | **Debug Specialist** | `debug-specialist` | opus | Logging, observability | 0.75x |
| 9 | **Explorer** | `Explore` | opus | Codebase verkenning, dependencies | 0.5x |
| 10 | **Researcher** | `general-purpose` | opus | Perplexity + Context7 research | 1.0x |

**Totaal Vote Weight: 11.5x** (gewogen consensus)

> **Standaard**: Alle agents draaien op **opus** voor maximale kwaliteit.
> **Pas aan**: Verwijder agents die niet relevant zijn (minimum = 4 agents).
> Herbereken totaal weight na aanpassingen.

---

## Opdracht

[BESCHRIJF DE ANALYSE OPDRACHT IN 2-3 ZINNEN]

### Scope

| Aspect | Waarde |
|--------|--------|
| **Doel** | [WAT MOET ER GEANALYSEERD WORDEN?] |
| **Bestanden** | [WELKE BESTANDEN/DIRECTORIES?] |
| **Diepte** | [OPPERVLAKKIG / MEDIUM / DIEPGAAND] |
| **Output** | [RAPPORT / RECOMMENDATIONS / ROADMAP] |

---

## Context

### Huidige Situatie

```
[VISUELE WEERGAVE VAN HUIDIGE STRUCTUUR]
├── [Component 1]
│   ├── [Subcomponent]
│   └── [Subcomponent]
├── [Component 2]
└── [Component 3] (probleem!)
```

### Probleemstelling

1. **[PROBLEEM 1]**: [Beschrijving]
2. **[PROBLEEM 2]**: [Beschrijving]
3. **[PROBLEEM 3]**: [Beschrijving]

### Gewenste Eindsituatie

```
[DIAGRAM VAN GEWENSTE WORKFLOW/STRUCTUUR]
User: "[actie]"
    ↓
[Stap 1]
    ↓
[Stap 2]
    ↓
[Resultaat]
```

### Achtergrond

- **Project**: [PROJECTNAAM]
- **Technologie**: [TECH STACK]
- **Constraints**: [BEPERKINGEN]

---

## Consensus Framework

### Consensus Regels

1. **Unanimiteit voor Critical**: Issues met severity "CRITICAL" moeten door ≥3 relevante agents bevestigd
2. **Meerderheid voor Recommendations**: Aanbevelingen vereisen >50% van relevante agents
3. **Conflict Resolution**: Bij tegenstrijdigheden → gewogen stemmen op basis van relevantie

### Consensus Categorieën

| Categorie | Vereiste Consensus | Betrokken Agents |
|-----------|-------------------|------------------|
| Architecture Changes | ≥75% | AR, CR, CC, PM |
| Code Quality Issues | ≥60% | CR, TE, CC, TA |
| Safety/Reliability | ≥75% | SFH, TA, DS |
| Business Priority | ≥60% | PM, AR |
| Quick Wins | ≥50% | Alle agents |

### Voting Matrix Template

```
| Finding | CR | TE | AR | PM | CC | SFH | TA | DS | EX | RS | Consensus |
|---------|----|----|----|----|----|----|----|----|----|----|-----------|
| [desc]  | +  | -- | +  | +  | ?  | -- | -- | -- | +  | -- | 80% (4/5) |
| [desc]  | +  | +  | -- | -- | +  | +  | +  | -- | -- | -- | 100% (5/5)|
| [desc]  | -  | -- | +  | +  | -  | -- | -- | -- | +  | -- | 60% (3/5) |

Legend:
  CR=Code Reviewer, TE=Tester, AR=Architect, PM=Product Manager
  CC=Complexity Checker, SFH=Silent Failure Hunter, TA=Type Analyst
  DS=Debug Specialist, EX=Explorer, RS=Researcher
  -- = Not relevant | + = AGREE | - = DISAGREE | ? = PARTIAL
```

### Consensus Score Berekening

```python
def calculate_consensus(finding, votes, weights):
    weighted_agree = sum(w for agent, vote, w in zip(agents, votes, weights)
                        if vote == 'AGREE')
    weighted_total = sum(w for agent, w in zip(agents, weights)
                        if agent.is_relevant(finding))
    return weighted_agree / weighted_total * 100

# Thresholds
CRITICAL_THRESHOLD = 75%
IMPORTANT_THRESHOLD = 60%
SUGGESTION_THRESHOLD = 50%
```

---

## Fase 1: Codebase Analyse

### 1.1 Agent Assignments

**Agent 1 (Code Reviewer):**
```
Analyseer code quality in:
- [PAD/NAAR/BESTANDEN]

Focus: [SPECIFIEKE FOCUS PUNTEN]
Return:
- Quality score (1-10) met confidence %
- Top 5 issues met severity (CRITICAL/HIGH/MEDIUM/LOW)
- Aanbevolen fixes
- VOTE op findings van andere agents in jouw domein
```

**Agent 3 (Architect):**
```
Analyseer architectuur in:
- [PAD/NAAR/BESTANDEN]

Focus: [SPECIFIEKE FOCUS PUNTEN]
Return:
- Architecture diagram (text-based)
- Design patterns gevonden
- Architectural debt met severity
- VOTE op architecture-related findings
```

**Agent 4 (Product Manager):**
```
Analyseer business impact:
- Haal Linear issues op met: [ZOEKTERMEN]
- Categoriseer en prioriteer

Focus: User impact, ROI
Return:
- Geprioriteerde issue lijst
- Business case voor top 3 improvements
- VOTE op prioriteit van alle findings
```

**Agent 5 (Complexity Checker):**
```
Analyseer complexiteit in:
- [PAD/NAAR/BESTANDEN]

Focus: Over-engineering, KISS violations
Return:
- Complexity score (1-10)
- Simplificatie mogelijkheden met effort estimate
- VOTE op of proposed changes complexiteit toevoegen
```

**Agent 9 (Explorer):**
```
Verken de codebase:
- Zoek bestanden met [ZOEKTERMEN]
- Map dependencies
- Identificeer documentatie gaps

Return:
- File inventory
- Dependency graph
- PROVIDE CONTEXT voor andere agents
```

### 1.2 Specifieke Vragen

| # | Vraag | Minimum Consensus | Betrokken Agents |
|---|-------|-------------------|------------------|
| 1 | [VRAAG 1] | [X%] | [AGENTS] |
| 2 | [VRAAG 2] | [X%] | [AGENTS] |
| 3 | [VRAAG 3] | [X%] | [AGENTS] |

---

## Fase 2: Quality & Safety Checks

**Agent 6 (Silent Failure Hunter):**
```
Zoek silent failures:
- Exception handling
- Fallback logic
- Error propagation

Return:
- Risk assessment (LOW/MEDIUM/HIGH/CRITICAL)
- Gevonden issues met evidence (code references)
- Fix recommendations
- VOTE op safety-related findings van andere agents
```

**Agent 7 (Type Analyst):**
```
Analyseer type safety:
- Data structures
- Input/output types
- Runtime safety

Return:
- Type design score (1-10)
- Unsafe patterns found
- Improvement suggestions
- VOTE op type-related issues van Code Reviewer
```

**Agent 8 (Debug Specialist):**
```
Analyseer debugging capabilities:
- Logging coverage
- Traceability
- Performance monitoring

Return:
- Debugging score (1-10)
- Logging recommendations
- Monitoring gaps
- VOTE op observability-related findings
```

---

## Fase 3: Research (Optioneel)

**Agent 10 (Researcher):**
```
PERPLEXITY QUERIES:
1. "[RESEARCH VRAAG 1]"
2. "[RESEARCH VRAAG 2]"

CONTEXT7 LOOKUPS:
1. [LIBRARY/FRAMEWORK DOCUMENTATIE]

Return:
- Synthesized findings met bronnen
- Applicable recommendations
- PROVIDE EVIDENCE voor/tegen findings van andere agents
```

---

## Fase 4: Consensus Building

### 4.1 Cross-Validation Matrix

```
Code Reviewer    reviews: Architect (code aspects), Tester (test recommendations)
Architect        reviews: Code Reviewer (patterns), Complexity Checker (abstractions)
PM               reviews: All agents (priority/business value)
Complexity       reviews: Architect (over-engineering), Code Reviewer (simplicity)
Tester           reviews: Code Reviewer (testability)
Silent Failure   reviews: Type Analyst, Debug Specialist
Type Analyst     reviews: Code Reviewer (type issues)
Debug Specialist reviews: Silent Failure Hunter (logging)
Explorer         provides: Context for all
Researcher       provides: Evidence for all
```

### 4.2 Voting Protocol

```
STAP 1: Individuele Agent Analyse
- Elke agent voert onafhankelijke analyse uit
- Output bevat: findings, severity, confidence score (0-100%)

STAP 2: Cross-Validation
- Agents reviewen elkaars findings binnen hun domein
- Markeer: AGREE (+) | PARTIAL (?) | DISAGREE (-)

STAP 3: Conflict Resolution
- Bij DISAGREE: beide agents leveren onderbouwing
- Gewogen stem op basis van:
  * Relevantie voor het onderwerp (weight factor)
  * Confidence score van de finding
  * Evidence quality (code references, research backing)

STAP 4: Consensus Score Berekening
- Per finding: (agreeing_agents / relevant_agents) × 100%
- Threshold voor opname in rapport:
  * Critical: ≥75% consensus
  * Important: ≥60% consensus
  * Suggestion: ≥50% consensus

STAP 5: Dissent Documentation
- Minderheidsstandpunten worden gedocumenteerd
```

### 4.3 Consensus Thresholds

| Type | Minimum | Vereiste Agents |
|------|---------|-----------------|
| CRITICAL issues | ≥75% | Min. 3 relevante agents |
| IMPORTANT | ≥60% | Min. 2 relevante agents |
| SUGGESTIONS | ≥50% | Min. 2 relevante agents |

### 4.4 Dissent Documentation Template

Bij <100% consensus, documenteer:

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

## Output Format

```markdown
# [ANALYSE TITEL] Report

## Executive Summary
[2-3 alinea's met key findings - alleen consensus items]

## Consensus Overview
- Total Findings Analyzed: X
- Full Consensus (100%): Y
- Majority Consensus (≥60%): Z
- Rejected (<50%): W
- Overall Consensus Rate: X%

## Agent Scores Overview

| Agent | Focus | Score | Weight | Findings Accepted |
|-------|-------|-------|--------|-------------------|
| Code Reviewer | Quality | ?/10 | 1.5x | X |
| Tester | Coverage | ?/10 | 1.0x | X |
| Architect | Design | ?/10 | 2.0x | X |
| PM | Business | ?/10 | 1.5x | X |
| ... | ... | ... | ... | ... |

**Gewogen Totaal Score: ?/10**

---

## 1. [SECTIE 1]
**Consensus: X%** | Dissent: [if any]
[Bevindingen]

## 2. [SECTIE 2]
**Consensus: X%** | Dissent: [if any]
[Bevindingen]

---

## Recommendations (Consensus Required)

### Quick Wins (<2h) - ≥50% consensus
| # | Recommendation | Consensus | Dissent |
|---|----------------|-----------|---------|
| 1 | [desc] | 85% (8/10) | Agent X: [reason] |
| 2 | [desc] | 100% (10/10) | None |

### Short Term (2-8h) - ≥60% consensus
| # | Recommendation | Consensus | Dissent |
|---|----------------|-----------|---------|

### Long Term (>8h) - ≥75% consensus
| # | Recommendation | Consensus | Dissent |
|---|----------------|-----------|---------|

### Rejected (<50% consensus)
| # | Recommendation | Consensus | Why Rejected |
|---|----------------|-----------|--------------|
| 1 | [desc] | 40% | [summary of objections] |

---

## Voting Matrix (Full)

| Finding | CR | TE | AR | PM | CC | SFH | TA | DS | EX | RS | Consensus |
|---------|----|----|----|----|----|----|----|----|----|----|-----------|
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

---

## Implementation Roadmap
[Dependency graph - consensus items only]

## Appendices
- A: Full Agent Reports
- B: Dissenting Opinions (Full Detail)
- C: Sources & Research
- D: Voting Evidence
```

---

## Constraints

- **ULTRATHINK**: Diepgaande analyse vereist
- **CONSENSUS**: Geen recommendations zonder voldoende consensus
- **Opus-only**: Alle agents draaien op opus voor maximale kwaliteit
- **Solo Developer**: Geen team overhead, praktische oplossingen
- [EXTRA CONSTRAINTS]

---

## Input Bestanden

1. [BESTAND 1]
2. [BESTAND 2]
3. [BESTAND 3]

---

## Execution Command

```
Phase 1: Parallel → Agents [NUMMERS] (codebase analyse)
Phase 2: Parallel → Agent 10 (research) [OPTIONEEL]
Phase 3: Parallel → Agents 6-8 (quality checks)
Phase 4: Sequential → CONSENSUS BUILDING
  - Cross-validation tussen agents
  - Voting round op alle findings
  - Consensus score berekening
  - Dissent documentation
Phase 5: Sequential → Rapport generatie met consensus filtering
```

---

## Checklist voor gebruik

- [ ] [PLACEHOLDERS] ingevuld
- [ ] Irrelevante agents verwijderd (alle behouden agents draaien op opus)
- [ ] Vote weights herberekend na agent wijzigingen
- [ ] Specifieke vragen toegevoegd met consensus thresholds
- [ ] Research queries relevant gemaakt
- [ ] Visuele diagrams toegevoegd (huidige/gewenste situatie)
- [ ] Output secties aangepast aan scope
