# Claude Code Agents Analyse & Optimalisatie

> **Doel**: Analyseer de beschikbare Claude Code agents, optimaliseer hun organisatie, en ontwerp een subagent workflow voor prompt generatie via hookify.
> **Versie**: 2.0 - Upgraded met voting matrix, cross-validation, en dissent documentation

---

## Execution Mode

| Setting | Value |
|---------|-------|
| **ULTRATHINK** | Ja - Extended reasoning voor architecture decisions |
| **MULTIAGENT** | 6 gespecialiseerde agents |
| **CONSENSUS** | Vereist voor alle aanbevelingen |

---

## Agent Configuratie

| # | Agent Role | Type | Model | Focus Area | Vote Weight |
|---|------------|------|-------|------------|-------------|
| 1 | **Architecture Analyst** | `feature-dev:code-architect` | opus | Agent taxonomie, hiërarchie, dependencies | 2.0x |
| 2 | **Efficiency Expert** | `code-simplifier` | opus | Token optimalisatie, parallelisatie, performance | 1.5x |
| 3 | **Hookify Specialist** | `general-purpose` | opus | Hookify workflow, trigger patterns, subagent integratie | 1.5x |
| 4 | **Prompt Engineer** | `general-purpose` | opus | Prompt kwaliteit, template design, consensus frameworks | 2.0x |
| 5 | **Documentation Scout** | `claude-code-guide` | opus | Claude Code docs, best practices, agent capabilities | 1.0x |
| 6 | **Integration Tester** | `debug-specialist` | opus | Workflow validatie, edge cases, failure modes | 1.0x |

**Totaal Vote Weight: 9.0x** (gewogen consensus)

---

## Opdracht

Voer een diepgaande analyse uit van het Claude Code agent ecosysteem met drie doelen:

1. **Agent Organisatie**: Breng alle beschikbare agents in kaart, categoriseer ze, en identificeer overlap/gaps
2. **Opus Optimalisatie**: Bepaal hoe opus optimaal te gebruiken voor alle agents (parallelisatie, chaining, efficiency)
3. **Hookify Subagent Workflow**: Ontwerp een workflow waarbij hookify een subagent triggert om gestructureerde prompts te genereren

### Scope

| Aspect | Waarde |
|--------|--------|
| **Doel** | Agent taxonomie + opus optimalisatie + hookify prompt-generatie workflow |
| **Bestanden** | Task tool definitie, ~/.claude/plugins/, prompts/*.md, CLAUDE.md |
| **Diepte** | DIEPGAAND |
| **Output** | Agent catalogus + Opus guidelines + Hookify subagent design |

---

## Context

### Huidige Situatie

```
Beschikbare Agents (uit Task tool):
├── Algemeen
│   ├── general-purpose
│   ├── Explore
│   └── Plan
├── Feature Development (feature-dev:)
│   ├── code-architect
│   ├── code-explorer
│   └── code-reviewer
├── PR Review (pr-review-toolkit:)
│   ├── code-reviewer      ← OVERLAP!
│   ├── code-simplifier    ← OVERLAP!
│   ├── comment-analyzer
│   ├── pr-test-analyzer
│   ├── silent-failure-hunter
│   └── type-design-analyzer
├── Plugin Development (plugin-dev:)
│   ├── agent-creator
│   ├── plugin-validator
│   └── skill-reviewer
├── Agent SDK (agent-sdk-dev:)
│   ├── agent-sdk-verifier-py
│   └── agent-sdk-verifier-ts
├── Hookify
│   └── conversation-analyzer
└── Standalone
    ├── debug-specialist
    ├── full-stack-developer
    ├── code-reviewer      ← 3x OVERLAP!
    ├── code-simplifier    ← 2x OVERLAP!
    └── product-manager
```

### Probleemstelling

1. **Onduidelijke taxonomie**: Sommige agents bestaan meerdere keren (code-reviewer 3x)
2. **Opus optimalisatie**: Hoe maximaliseren we kwaliteit bij opus-only strategie?
3. **Hookify-to-subagent gap**: Hoe trigger je een prompt-generatie subagent via hookify?
4. **Prompt kwaliteit**: Hoe garandeer je dat gegenereerde prompts het multiagent template volgen?

### Gewenste Eindsituatie

```
User typt: "analyseer de performance van de validation service"
    ↓
Hookify detecteert "analyse" keyword
    ↓
Hookify vraagt: "Wil je een gestructureerde prompt genereren?"
    ↓
Bij "Ja": Subagent genereert prompt volgens TEMPLATE-deep-analysis.md
    ↓
Prompt wordt opgeslagen in /prompts/
    ↓
User kan prompt reviewen en uitvoeren
```

---

## Consensus Framework

### Consensus Regels

1. **Unanimiteit voor Critical**: Issues met severity "CRITICAL" moeten door ≥3 relevante agents bevestigd
2. **Meerderheid voor Recommendations**: Aanbevelingen vereisen >50% van relevante agents
3. **Conflict Resolution**: Bij tegenstrijdigheden → gewogen stemmen op basis van relevantie

### Consensus Categorieën

| Categorie | Vereiste Consensus | Betrokken Agents |
|-----------|-------------------|------------------|
| Agent Taxonomie | ≥75% | AA, DS, PE |
| Architecture Changes | ≥75% | AA, EE, PE |
| Hookify Workflow | ≥70% | HS, PE, IT |
| Opus Optimalisatie | ≥60% | EE, AA, IT |
| Quick Wins | ≥50% | Alle agents |

### Voting Matrix Template

```
| Finding | AA | EE | HS | PE | DS | IT | Consensus |
|---------|----|----|----|----|----|----|-----------|
| [desc]  | +  | +  | +  | +  | ?  | +  | 92% (5.5/6) |
| [desc]  | +  | +  | -- | +  | -- | +  | 100% (4/4) |
| [desc]  | -  | +  | +  | +  | -- | -  | 60% (3/5) |

Legend:
  AA=Architecture Analyst, EE=Efficiency Expert, HS=Hookify Specialist
  PE=Prompt Engineer, DS=Documentation Scout, IT=Integration Tester
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

## Fase 1: Agent Taxonomie Analyse

### 1.1 Agent Assignments

**Agent 1 (Architecture Analyst):**
```
Analyseer de complete agent structuur:
- Map alle agents naar categorieën
- Identificeer overlap (bijv. 3x code-reviewer)
- Bepaal hiërarchie en dependencies
- Identificeer gaps (ontbrekende agents)

Focus: Taxonomie, overlap resolutie, categorisatie
Return:
- Taxonomie diagram (text-based)
- Overlap analyse met aanbevelingen
- Gap analyse
- Confidence score (0-100%)
- VOTE op categorisatie voorstellen van andere agents
```

**Agent 5 (Documentation Scout):**
```
Raadpleeg Claude Code documentatie voor:
- Officiële agent best practices
- Model selectie richtlijnen (wanneer opus vs sonnet vs haiku)
- Subagent capabilities en limitaties
- Hookify-agent integratie mogelijkheden

Focus: Documentatie, officiële richtlijnen
Return:
- Documentatie samenvatting met bronnen
- Officiële richtlijnen
- Confidence score (0-100%)
- PROVIDE CONTEXT voor andere agents
```

### 1.2 Specifieke Vragen

| # | Vraag | Minimum Consensus | Betrokken Agents |
|---|-------|-------------------|------------------|
| 1 | Welke agents zijn duplicaten en kunnen geconsolideerd worden? | ≥75% | AA, DS, PE |
| 2 | Welke agents missen we voor Definitie-app specifieke workflows? | ≥60% | AA, PE, IT |
| 3 | Hoe verhouden de plugin agents zich tot de ingebouwde agents? | ≥60% | DS, AA |

---

## Fase 2: Opus Optimalisatie

**Agent 2 (Efficiency Expert):**
```
Analyseer hoe opus optimaal te gebruiken voor alle agents:

UITGANGSPUNT:
- Alle agents draaien op opus (kwaliteit boven kosten)
- Focus op maximale waarde uit elk opus request

ANALYSEER:
- Prompt efficiency (minimaliseer tokens, maximaliseer output)
- Parallel execution opportunities (meerdere agents tegelijk)
- Caching mogelijkheden (hergebruik van context)
- Agent chaining patterns (output A → input B)

Focus: Performance, efficiency, parallelisatie
Return:
- Opus optimalisatie strategie
- Parallelisatie mogelijkheden met dependencies
- Token efficiency tips
- Confidence score (0-100%)
- VOTE op efficiency voorstellen van andere agents
```

### 2.1 Opus Maximalisatie Principes

| Principe | Strategie |
|----------|-----------|
| **Kwaliteit** | Opus voor alle agents = consistente hoge kwaliteit |
| **Parallelisatie** | Onafhankelijke agents tegelijk lanceren |
| **Context Sharing** | Agents delen relevante context via prompts |
| **Focused Prompts** | Specifieke opdrachten = betere opus output |

### 2.2 Specifieke Vragen

| # | Vraag | Minimum Consensus | Betrokken Agents |
|---|-------|-------------------|------------------|
| 1 | Welke agents kunnen parallel draaien voor snelheid? | ≥60% | EE, AA, IT |
| 2 | Hoe maximaliseren we opus output kwaliteit per agent? | ≥60% | EE, PE |
| 3 | Welke agent combinaties leveren de beste synergie? | ≥50% | AA, EE, PE |

---

## Fase 3: Hookify Subagent Workflow Design

**Agent 3 (Hookify Specialist):**
```
Ontwerp de hookify → subagent workflow:

ANALYSE:
1. Huidige hookify capabilities (events, actions)
2. Hoe trigger je een Task tool aanroep vanuit hookify?
3. Welke event type past best (prompt/stop)?

DESIGN:
- Hookify rule die prompt-generatie triggert
- Subagent specificatie voor prompt generatie
- Integratie met prompts/TEMPLATE-deep-analysis.md

Focus: Hookify mechanics, workflow design
Return:
- Workflow diagram (ASCII)
- Hookify rule YAML
- Subagent prompt specificatie
- Confidence score (0-100%)
- VOTE op haalbaarheid van voorstellen
```

**Agent 4 (Prompt Engineer):**
```
Ontwerp de prompt-generatie subagent:

REQUIREMENTS:
- Moet TEMPLATE-deep-analysis.md v2.0 volgen
- Moet context van user vraag extraheren
- Moet juiste agents selecteren per taak type
- Moet output opslaan in /prompts/

DESIGN:
- Subagent system prompt
- Input/output specificatie
- Template selection logic
- Quality assurance checks

Focus: Prompt kwaliteit, template adherence
Return:
- Complete subagent definitie
- Voorbeeld gegenereerde prompts
- Confidence score (0-100%)
- VOTE op template adherence
```

### 3.1 Hookify Constraint Analysis

| Capability | Beschikbaar? | Workaround |
|------------|--------------|------------|
| Direct Task tool call | ❌ Nee | Via prompt injection |
| Subagent spawning | ❌ Nee | Instructie in response |
| File writing | ⚠️ Indirect | Via instructie |
| User choice | ✅ Ja | Via action: warn |

### 3.2 Specifieke Vragen

| # | Vraag | Minimum Consensus | Betrokken Agents |
|---|-------|-------------------|------------------|
| 1 | Kan hookify direct een subagent starten, of moet dit via instructies? | ≥75% | HS, PE, DS |
| 2 | Hoe krijgt de subagent context over de originele user vraag? | ≥70% | HS, PE |
| 3 | Hoe valideert de subagent dat de gegenereerde prompt correct is? | ≥60% | PE, IT |

---

## Fase 4: Integration Testing

**Agent 6 (Integration Tester):**
```
Valideer de voorgestelde workflow:

TEST SCENARIOS:
1. User typt "analyseer de database performance"
2. User typt "fix de bug in validation_orchestrator"
3. User typt "review mijn PR"
4. User typt "help" (geen trigger)

EDGE CASES:
- Wat als user "Nee" kiest?
- Wat als prompt generatie faalt?
- Wat als template niet gevonden wordt?

Focus: Workflow validatie, failure modes
Return:
- Test resultaten per scenario
- Failure mode analyse
- Recovery procedures
- Confidence score (0-100%)
- VOTE op production-readiness
```

---

## Fase 5: Consensus Building

### 5.1 Cross-Validation Matrix

```
Architecture Analyst  reviews: Efficiency Expert (parallelisatie), Prompt Engineer (agent selectie)
Efficiency Expert     reviews: Architecture Analyst (complexity), Integration Tester (performance)
Hookify Specialist    reviews: Prompt Engineer (workflow integration)
Prompt Engineer       reviews: Hookify Specialist (template adherence), Architecture Analyst (agent design)
Documentation Scout   provides: Context for all (officiële docs)
Integration Tester    reviews: Hookify Specialist (workflow), Efficiency Expert (edge cases)
```

### 5.2 Voting Protocol

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
  * Evidence quality (code references, documentation)

STAP 4: Consensus Score Berekening
- Per finding: (agreeing_weight / relevant_weight) × 100%
- Threshold voor opname in rapport:
  * Critical: ≥75% consensus
  * Important: ≥60% consensus
  * Suggestion: ≥50% consensus

STAP 5: Dissent Documentation
- Minderheidsstandpunten worden gedocumenteerd in appendix
```

### 5.3 Consensus Thresholds

| Type | Minimum | Vereiste Agents |
|------|---------|-----------------|
| Architecture changes | ≥75% | Min. 3 relevante agents |
| Workflow design | ≥70% | Min. 3 relevante agents |
| Optimalisatie | ≥60% | Min. 2 relevante agents |
| Nice-to-haves | ≥50% | Min. 2 relevante agents |

### 5.4 Dissent Documentation Template

Bij <100% consensus, documenteer:

```markdown
### Dissenting Opinion: [Finding Title]

**Majority View (X agents, Y% consensus):**
[Description of majority position]

**Minority View (Z agents):**
- Agent [Name]: [Reasoning for disagreement]

**Resolution:** [How this was handled in final recommendations]
```

---

## Output Format

```markdown
# Claude Code Agents Analyse Report

## Executive Summary
[3-5 bullet points met key findings - alleen consensus items]

## Consensus Overview
- Total Findings Analyzed: X
- Full Consensus (100%): Y
- Majority Consensus (≥60%): Z
- Rejected (<50%): W
- Overall Consensus Rate: X%

## Agent Scores Overview

| Agent | Focus | Score | Weight | Findings Accepted |
|-------|-------|-------|--------|-------------------|
| Architecture Analyst | Taxonomie | ?/10 | 2.0x | X |
| Efficiency Expert | Optimalisatie | ?/10 | 1.5x | X |
| Hookify Specialist | Workflow | ?/10 | 1.5x | X |
| Prompt Engineer | Templates | ?/10 | 2.0x | X |
| Documentation Scout | Docs | ?/10 | 1.0x | X |
| Integration Tester | Testing | ?/10 | 1.0x | X |

**Gewogen Totaal Score: ?/10**

---

## 1. Agent Taxonomie
**Consensus: X%** | Dissent: [if any]

### 1.1 Geoptimaliseerde Categorisatie
[Visuele taxonomie]

### 1.2 Overlap Resolutie
| Duplicate | Aanbeveling | Consensus |
|-----------|-------------|-----------|

### 1.3 Gap Analyse
| Missing Agent | Use Case | Priority |
|---------------|----------|----------|

---

## 2. Opus Optimalisatie Guidelines
**Consensus: X%** | Dissent: [if any]

### 2.1 Parallelisatie Matrix
| Fase | Parallel Agents | Dependencies |
|------|-----------------|--------------|

### 2.2 Agent Chaining Patterns
[Optimale volgorde voor agent chains]

### 2.3 Token Efficiency
| Agent Type | Prompt Strategie | Max Tokens |
|------------|------------------|------------|

---

## 3. Hookify Subagent Workflow
**Consensus: X%** | Dissent: [if any]

### 3.1 Workflow Diagram
[ASCII workflow diagram]

### 3.2 Hookify Rule
```yaml
name: prompt-generator-trigger
enabled: true
event: prompt
pattern: [pattern]
action: warn
```

### 3.3 Subagent Specificatie
```markdown
---
name: prompt-generator
type: general-purpose
model: opus
---
[System prompt voor de subagent]
```

### 3.4 Integratie met Templates
| User Intent | Detected Keywords | Template | Agents |
|-------------|-------------------|----------|--------|

---

## 4. Implementation Roadmap

### Quick Wins (<2h) - ≥50% consensus
| # | Action | Consensus | Dissent |
|---|--------|-----------|---------|

### Short Term (2-8h) - ≥60% consensus
| # | Action | Consensus | Dissent |
|---|--------|-----------|---------|

### Long Term (>8h) - ≥75% consensus
| # | Action | Consensus | Dissent |
|---|--------|-----------|---------|

### Rejected (<50% consensus)
| # | Recommendation | Consensus | Why Rejected |
|---|----------------|-----------|--------------|

---

## Voting Matrix (Full)

| Finding | AA | EE | HS | PE | DS | IT | Consensus |
|---------|----|----|----|----|----|----|-----------|
| ... | ... | ... | ... | ... | ... | ... | ... |

---

## Appendices
### A. Complete Agent Catalogus
### B. Opus Optimalisatie Evidence
### C. Hookify Rule Examples
### D. Dissenting Opinions (Full Detail)
```

---

## Constraints

- **ULTRATHINK**: Gebruik extended reasoning voor architecture decisions
- **CONSENSUS**: Geen recommendations zonder voldoende consensus
- **Solo Developer**: Geen complexe multi-service architectuur
- **Praktisch**: Oplossingen moeten direct implementeerbaar zijn
- **Opus-only**: Alle agents draaien op opus voor maximale kwaliteit
- **Backward Compatible**: Bestaande hookify rules moeten blijven werken

---

## Input Bestanden

1. Task tool definitie (uit system prompt)
2. `~/.claude/plugins/` - Geïnstalleerde plugins en agents
3. `prompts/TEMPLATE-deep-analysis.md` - Basis template v2.0
4. `prompts/README.md` - Prompt workflow documentatie
5. `CLAUDE.md` - Project instructies
6. `~/.ai-agents/UNIFIED_INSTRUCTIONS.md` - Globale instructies

---

## Execution Command

```
Phase 1: Parallel → Agents 1, 5 (taxonomie + docs research)
Phase 2: Parallel → Agent 2 (opus optimalisatie)
Phase 3: Parallel → Agents 3, 4 (hookify + prompt design)
Phase 4: Sequential → Agent 6 (integration testing)
Phase 5: Sequential → CONSENSUS BUILDING
  - Cross-validation tussen agents
  - Voting round op alle findings
  - Consensus score berekening
  - Dissent documentation
Phase 6: Sequential → Report generatie met consensus filtering
```

---

## Success Criteria

- [ ] Complete agent catalogus met duidelijke categorisatie
- [ ] Opus optimalisatie strategie (parallelisatie, chaining, efficiency)
- [ ] Werkende hookify rule voor prompt-generatie trigger
- [ ] Subagent specificatie (opus-based) die TEMPLATE-deep-analysis.md v2.0 volgt
- [ ] Minimaal 60% consensus op alle aanbevelingen
- [ ] Voting matrix met alle findings
- [ ] Dissenting opinions gedocumenteerd
- [ ] Implementation roadmap met concrete stappen
