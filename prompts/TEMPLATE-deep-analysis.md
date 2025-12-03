# Deep Analysis Template

> **Gebruik**: Kopieer dit template en vul de [PLACEHOLDERS] in voor je specifieke analyse.

---

## Execution Mode

**ULTRATHINK**: Activeer extended reasoning voor alle analyses.

**MULTIAGENT STRATEGY**: Lanceer [AANTAL] gespecialiseerde agenten parallel.

**CONSENSUS REQUIRED**: Alle aanbevelingen moeten consensus hebben tussen relevante agents.

---

## Agent Configuratie

| # | Agent Role | Type | Focus Area | Vote Weight |
|---|------------|------|------------|-------------|
| 1 | **Code Reviewer** | `code-reviewer` | Code quality, patterns, anti-patterns | 1.5x |
| 2 | **Tester** | `pr-review-toolkit:pr-test-analyzer` | Test coverage, edge cases | 1.0x |
| 3 | **Architect** | `feature-dev:code-architect` | Architecture, module design | 2.0x |
| 4 | **Product Manager** | `product-manager` | Business value, prioritering | 1.5x |
| 5 | **Complexity Checker** | `code-simplifier` | Over-engineering, simplificatie | 1.5x |
| 6 | **Silent Failure Hunter** | `pr-review-toolkit:silent-failure-hunter` | Error handling, silent failures | 1.0x |
| 7 | **Type Analyst** | `pr-review-toolkit:type-design-analyzer` | Type safety, data structures | 0.75x |
| 8 | **Debug Specialist** | `debug-specialist` | Logging, observability | 0.75x |
| 9 | **Explorer** | `Explore` | Codebase verkenning, dependencies | 0.5x |
| 10 | **Researcher** | `general-purpose` | Perplexity + Context7 research | 1.0x |

> **Pas aan**: Verwijder agents die niet relevant zijn voor je analyse. Minimum = 4 agents.

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

[BESCHRIJF DE RELEVANTE CONTEXT VOOR DEZE ANALYSE]

- Project: [PROJECTNAAM]
- Technologie: [TECH STACK]
- Constraints: [BEPERKINGEN]

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
- Top 5 issues met severity
- Aanbevolen fixes
- VOTE op findings van andere agents
```

**Agent 3 (Architect):**
```
Analyseer architectuur in:
- [PAD/NAAR/BESTANDEN]

Focus: [SPECIFIEKE FOCUS PUNTEN]
Return:
- Architecture diagram (text)
- Design patterns gevonden
- Architectural debt
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
- Simplificatie mogelijkheden
- VOTE op of changes complexiteit toevoegen
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

Beantwoord de volgende vragen:

1. [VRAAG 1]
2. [VRAAG 2]
3. [VRAAG 3]

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
- Gevonden issues met evidence
- Fix recommendations
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
- Evidence voor/tegen andere findings
```

---

## Fase 4: Consensus Building

### 4.1 Cross-Validation

```
Code Reviewer ↔ Architect (code aspects)
Architect ↔ Complexity Checker (abstractions)
PM reviews: All (priority)
Silent Failure Hunter ↔ Debug Specialist (safety)
```

### 4.2 Voting

Per finding stemmen alle relevante agents:
1. Is dit valide? (JA/NEE/PARTIAL)
2. Severity correct? (AGREE/TOO_HIGH/TOO_LOW)
3. Fix correct? (AGREE/ALTERNATIVE/DISAGREE)
4. Prioriteit? (P1/P2/P3/P4)

### 4.3 Consensus Thresholds

| Type | Minimum |
|------|---------|
| CRITICAL issues | ≥75% |
| IMPORTANT | ≥60% |
| SUGGESTIONS | ≥50% |

### 4.4 Dissent Documentation

Bij <100% consensus:
```markdown
### Dissenting Opinion: [Finding]
**Majority (X%)**: [standpunt]
**Minority**: Agent [X]: [reden]
**Resolution**: [hoe opgelost]
```

---

## Output Format

```markdown
# [ANALYSE TITEL] Report

## Executive Summary
[Key findings - alleen consensus items]

## Consensus Overview
- Total Findings: X
- Full Consensus (100%): Y
- Majority (≥60%): Z
- Rejected (<50%): W

## Agent Scores
| Agent | Score | Findings Accepted |
|-------|-------|-------------------|
| ... | ?/10 | X |

## 1. [SECTIE 1]
**Consensus: X%**
[Bevindingen]

## 2. [SECTIE 2]
**Consensus: X%**
[Bevindingen]

## Recommendations

### Quick Wins (<2h)
| # | Recommendation | Consensus |
|---|----------------|-----------|

### Short Term (2-8h)
| # | Recommendation | Consensus |
|---|----------------|-----------|

### Long Term (>8h)
| # | Recommendation | Consensus |
|---|----------------|-----------|

### Rejected (<50% consensus)
| # | Recommendation | Why |
|---|----------------|-----|

## Implementation Roadmap
[Dependency graph]

## Appendices
- A: Full Agent Reports
- B: Dissenting Opinions
- C: Sources
```

---

## Constraints

- **ULTRATHINK**: Diepgaande analyse vereist
- **CONSENSUS**: Geen recommendations zonder voldoende consensus
- **Solo Developer**: Geen team overhead, praktische oplossingen
- **Budget-bewust**: Token costs zijn relevant
- [EXTRA CONSTRAINTS]

---

## Execution Command

```
Phase 1: Parallel → Agents [NUMMERS] (codebase analyse)
Phase 2: Parallel → Agent 10 (research) [OPTIONEEL]
Phase 3: Parallel → Agents 6, 8 (quality checks)
Phase 4: Sequential → Consensus building
Phase 5: Sequential → Rapport generatie
```

---

## Checklist voor gebruik

- [ ] [PLACEHOLDERS] ingevuld
- [ ] Irrelevante agents verwijderd
- [ ] Specifieke vragen toegevoegd
- [ ] Research queries relevant gemaakt
- [ ] Output secties aangepast aan scope
