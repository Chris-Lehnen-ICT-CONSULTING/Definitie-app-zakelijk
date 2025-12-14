# Agent & Workflow Optimization Research

> **Doel**: Onderzoek hoe prompts en workflows efficiënt toe te passen, waarbij multiagent taken altijd echte agents (met eigen context) gebruiken
> **Type**: ANALYSIS (deep research)
> **Status**: READY FOR EXECUTION

---

## Onderzoeksvragen

### Hoofdvraag
Hoe kan ik prompts en workflows zo efficiënt mogelijk inzetten, waarbij multiagent taken altijd via echte agents (met eigen context) worden uitgevoerd?

### Deelvragen

1. **Agent Inventory**: Welke agents heb ik beschikbaar en wat zijn hun capabilities?
2. **Activatie Mechanismen**: Hoe worden verschillende agent types geactiveerd (BMAD vs Task tool vs andere)?
3. **Context Isolatie**: Welke agents hebben echte eigen context vs gedeelde context?
4. **Workflow Patterns**: Wat zijn effectieve patterns voor multiagent orchestratie?
5. **Efficiency**: Waar zit overhead en hoe te minimaliseren?

---

## Fase 1: Agent Inventory (Verkenning)

### Te Onderzoeken Locaties

| Locatie | Type | Verwachte Agents |
|---------|------|------------------|
| `.bmad/` | BMAD agents | core, bmm, cis, bmb modules |
| `~/.claude/plugins/marketplaces/` | Marketplace plugins | feature-dev, pr-review-toolkit, hookify, etc. |
| `.claude/agents/` | Project-specifieke agents | Custom agents |
| Built-in Task tool | Claude Code subagents | Explore, general-purpose, Plan, etc. |

### Per Agent Documenteren

```markdown
| Agent | Bron | Activatie | Eigen Context? | Use Case |
|-------|------|-----------|----------------|----------|
| [naam] | BMAD/Marketplace/Built-in | SlashCommand/Task tool | Ja/Nee | [beschrijving] |
```

---

## Fase 2: Activatie Mechanismen Analyse

### Vergelijking Activatie Types

| Mechanisme | Hoe | Context Isolatie | Parallellisatie |
|------------|-----|------------------|-----------------|
| **BMAD SlashCommand** | `/bmad:module:agents:name` | ? | ? |
| **Task tool** | `Task(subagent_type=...)` | ? | ? |
| **Skill** | `Skill(skill=...)` | ? | ? |
| **Direct prompt** | Persona in system prompt | Nee (zelfde sessie) | Nee |

### Te Beantwoorden

1. Heeft een BMAD agent via SlashCommand een eigen context window?
2. Heeft een Task tool subagent een eigen context window?
3. Kunnen BMAD agents parallel draaien?
4. Wat is het verschil tussen een BMAD agent en een Task tool agent qua isolation?

---

## Fase 3: Context Isolatie Deep Dive

### Hypothese Te Testen

| Claim | Test Methode |
|-------|--------------|
| "Task tool agents hebben eigen context" | Vergelijk output van 2 parallelle Task calls |
| "BMAD agents hebben eigen context" | Activeer 2 BMAD agents, check of ze elkaars state zien |
| "SlashCommand start fresh session" | Check of vorige conversatie zichtbaar is na /bmad:... |

### Relevante Documentatie Te Raadplegen

- Claude Code SDK docs (via claude-code-guide agent)
- BMAD method documentation (`.bmad/` bestanden)
- Task tool definitie in system prompt

---

## Fase 4: Workflow Patterns Identificatie

### Te Onderzoeken Patterns

1. **Sequential BMAD**: architect → developer → tester (hoe context doorgeven?)
2. **Parallel Task agents**: Meerdere Task calls in één message
3. **Hybrid**: BMAD voor design, Task tool voor implementatie
4. **Orchestrated**: bmad-master als coordinator

### Per Pattern Documenteren

```markdown
## Pattern: [naam]

**Wanneer gebruiken**: [criteria]
**Activatie**: [stappen]
**Context flow**: [hoe gaat context tussen agents]
**Voordelen**: [lijst]
**Nadelen**: [lijst]
**Voorbeeld workflow**: [concreet]
```

---

## Fase 5: Efficiency Analyse

### Metrics Te Verzamelen

| Metric | Hoe Meten |
|--------|-----------|
| Token usage per agent type | Vergelijk BMAD vs Task tool voor zelfde taak |
| Latency | Tijd tot eerste output |
| Context window usage | Hoeveel van 200K wordt gebruikt |
| Overhead | Activatie tijd, system prompt size |

### Optimalisatie Vragen

1. Wanneer is BMAD overkill? (kleine taken)
2. Wanneer is Task tool overkill? (hele kleine taken)
3. Wat is de sweet spot per taak grootte?
4. Hoe voorkom je dubbel werk tussen agents?

---

## Deliverables

### 1. Agent Capabilities Matrix

```markdown
| Agent | Bron | Activatie | Context | Parallel | Best Voor |
|-------|------|-----------|---------|----------|-----------|
| ... | ... | ... | ... | ... | ... |
```

### 2. Decision Framework

```markdown
## Wanneer Welk Agent Type

### Gebruik BMAD agents wanneer:
- [criteria]

### Gebruik Task tool agents wanneer:
- [criteria]

### Gebruik geen agents (direct) wanneer:
- [criteria]
```

### 3. Workflow Templates

Per common scenario een concrete workflow:
- Analysis workflow
- Implementation workflow
- Review workflow
- Fix workflow

### 4. Efficiency Guidelines

- Token budget per taak type
- Wanneer parallel vs sequential
- Context handoff patterns

### 5. CLAUDE.md Update Voorstel

Concrete toevoegingen voor agent routing rules.

---

## Uitvoering

### Optie A: BMAD Multiagent (Aanbevolen)

Gebruik BMAD agents sequentieel:

1. `/bmad:bmm:agents:analyst` - Inventory en gap analyse
2. `/bmad:bmm:agents:architect` - Workflow patterns design
3. `/bmad:core:agents:bmad-master` - Synthese en recommendations

### Optie B: Hybrid

1. `Task(Explore)` - Snelle inventory van bestanden
2. `/bmad:bmm:agents:architect` - Design analysis
3. `Task(general-purpose)` - Research via Perplexity

### Optie C: Single Agent Deep Dive

1. `/bmad:bmm:agents:analyst` - Volledige analyse in één sessie

---

## Input Context

### Bekende Agent Inventory (uit eerdere analyse)

**BMAD Agents (19)**:
- core: bmad-master, prompt-writer
- bmm: pm, architect, dev, analyst, sm, ux-designer, tech-writer, tea, quick-flow-solo-dev
- cis: innovation-strategist, design-thinking-coach, creative-problem-solver, storyteller, presentation-master, brainstorming-coach
- bmb: bmad-builder

**Marketplace Agents (15)**:
- feature-dev: code-architect, code-explorer, code-reviewer
- pr-review-toolkit: code-reviewer, code-simplifier, comment-analyzer, pr-test-analyzer, silent-failure-hunter, type-design-analyzer
- hookify: conversation-analyzer
- plugin-dev: agent-creator, plugin-validator, skill-reviewer
- agent-sdk-dev: agent-sdk-verifier-py, agent-sdk-verifier-ts

**Built-in Task Tool Subagents**:
- Explore, Plan, general-purpose, claude-code-guide, debug-specialist, full-stack-developer, code-reviewer, code-simplifier, prompt-writer

**Project Agent (1)**:
- product-manager

---

## Success Criteria

Na dit onderzoek heb ik:

- [ ] Complete agent inventory met capabilities per agent
- [ ] Duidelijkheid over context isolatie per agent type
- [ ] Concrete decision framework: wanneer welk type
- [ ] 4 workflow templates voor common scenarios
- [ ] CLAUDE.md update voorstel voor agent routing

---

## Pre-Execution Checklist

- [ ] BMAD config geladen (`.bmad/core/config.yaml`)
- [ ] Toegang tot alle agent locaties
- [ ] Perplexity/Context7 beschikbaar voor research
- [ ] Output folder: `prompts/research/`
