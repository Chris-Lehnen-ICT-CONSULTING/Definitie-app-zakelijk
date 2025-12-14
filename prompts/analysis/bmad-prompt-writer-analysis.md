# BMAD Prompt-Writer Agent Ontwikkeling

## Execution Mode

**ULTRATHINK**: Activeer extended reasoning voor alle analyses.

**MULTIAGENT STRATEGY**: Lanceer 7 gespecialiseerde agenten parallel.

**CONSENSUS REQUIRED**: Alle aanbevelingen moeten ≥70% consensus hebben tussen relevante agents.

---

## Agent Configuratie

| # | Agent Role | Type | Focus Area | Vote Weight |
|---|------------|------|------------|-------------|
| 1 | **Architect** | `feature-dev:code-architect` | BMAD agent structuur, XML schema patterns | 2.0x |
| 2 | **Tech Writer** | `tech-writer` | Documentatie analyse, template patronen | 1.5x |
| 3 | **Product Manager** | `product-manager` | Use cases, gebruikersbehoefte, prioritering | 1.5x |
| 4 | **Code Reviewer** | `code-reviewer` | Code quality, patronen, best practices | 1.5x |
| 5 | **Complexity Checker** | `code-simplifier` | Simpliciteit, gebruiksvriendelijkheid | 1.0x |
| 6 | **Explorer** | `Explore` | BMAD codebase verkenning, dependency mapping | 1.0x |
| 7 | **BMAD Builder** | `@bmad/bmb/agents/bmad-builder` | BMAD-specifieke kennis, agent creation workflows | 2.0x |

---

## Opdracht

Analyseer de bestaande BMAD agent structuur en creëer een nieuwe **Prompt Writer Agent** die gebruikers helpt bij het genereren van gestructureerde analyse-prompts volgens de multiagent + consensus framework patronen uit `/prompts/`.

### Scope

| Aspect | Waarde |
|--------|--------|
| **Doel** | Analyseer BMAD agents + maak nieuwe prompt-writer agent |
| **Bestanden** | `.bmad/*/agents/*.md`, `.cursor/rules/bmad/`, `prompts/*.md` |
| **Diepte** | Diepgaand - volledige structuur analyse + nieuwe agent implementatie |
| **Output** | BMAD-compliant agent file + documentatie |

---

## Context

**Project**: Definitie-app met BMAD Method integratie

**BMAD Structuur**:
- `.cursor/rules/bmad/` - Cursor rules (.mdc wrappers)
- `.bmad/` - Daadwerkelijke agent/workflow implementaties (.md, .yaml)
- Modules: `core`, `bmb`, `bmm`

**Prompt Framework**:
- Gestructureerde prompts in `/prompts/`
- Template: `TEMPLATE-deep-analysis.md`
- Multiagent + consensus framework
- Agent types: code-reviewer, architect, PM, etc.

**Doel Nieuwe Agent**:
- Gebruiker helpen bij prompt generatie
- Interactieve menu voor verschillende prompt types
- Automatisch juiste agents selecteren op basis van taak
- BMAD-compliant implementatie

---

## Fase 1: BMAD Structuur Analyse

### 1.1 Agent Assignments

**Agent 1 (Architect):**
```
Analyseer BMAD agent architectuur:
- Lees `.bmad/core/agents/bmad-master.md`
- Lees `.bmad/bmb/agents/bmad-builder.md`
- Lees `.bmad/bmm/agents/pm.md`
- Lees `.bmad/bmm/agents/architect.md`

Focus:
- XML schema structuur (<agent>, <activation>, <persona>, <menu>)
- Activation step patterns
- Menu-handler types (workflow, exec, validate-workflow)
- Config integratie patronen

Return:
- Volledige agent structuur blueprint
- Minimale vereiste componenten
- Best practices voor nieuwe agents
- VOTE op structuur van nieuwe agent
```

**Agent 2 (Tech Writer):**
```
Analyseer documentatie patronen:
- Lees `prompts/README.md`
- Lees `prompts/TEMPLATE-deep-analysis.md`
- Lees `prompts/prompt-engineering-analysis.md`

Focus:
- Template structuur patronen
- Prompt secties (Execution Mode, Agent Config, Fasen, etc.)
- Multiagent configuratie opties
- Output format conventies

Return:
- Template patronen overzicht
- Herbruikbare prompt componenten
- Documentatie voor nieuwe agent
- VOTE op gebruiksvriendelijkheid nieuwe agent
```

**Agent 3 (Product Manager):**
```
Analyseer use cases:
- Welke prompt types worden het meest gebruikt?
- Wat zijn de pijnpunten bij handmatig prompts schrijven?
- Welke features moet de prompt-writer agent hebben?

Focus:
- Gebruikersbehoefte
- Prioritering van features
- MVP scope

Return:
- Use case overzicht
- Geprioriteerde feature lijst
- MVP definitie voor prompt-writer agent
- VOTE op business value van features
```

**Agent 4 (Code Reviewer):**
```
Analyseer bestaande agent kwaliteit:
- Lees 3-4 verschillende BMAD agents
- Identificeer code quality patterns
- Spot inconsistenties

Focus:
- XML structuur consistentie
- Error handling
- User experience
- Activation step duidelijkheid

Return:
- Quality checklist voor nieuwe agent
- Aanbevolen improvements
- VOTE op code quality nieuwe agent
```

**Agent 6 (Explorer):**
```
Verken BMAD codebase:
- Map directory structuur `.bmad/`
- Identificeer alle agent bestanden
- Map workflow dependencies
- Vind config bestanden

Return:
- BMAD directory map
- Agent inventory (core, bmb, bmm)
- Config locaties
- Dependencies voor nieuwe agent
```

**Agent 7 (BMAD Builder):**
```
Activeer @bmad/bmb/agents/bmad-builder
Gebruik interne kennis van BMAD agent creation workflow

Focus:
- Agent compilation proces
- Module integratie
- Best practices vanuit bmad-builder perspectief

Return:
- BMAD-specifieke requirements
- Integration checklist
- VOTE op BMAD compliance nieuwe agent
```

### 1.2 Specifieke Analyse Vragen

1. Wat zijn de essentiële componenten van een BMAD agent?
2. Hoe integreren agents met workflows?
3. Welke menu-handler types zijn beschikbaar?
4. Hoe wordt config geladen en gebruikt?
5. Wat is het patroon voor persona definitie?

---

## Fase 2: Prompt-Writer Agent Design

**Agent 1 (Architect):**
```
Design de agent architectuur:
- XML structuur met alle vereiste secties
- Activation steps
- Menu items voor verschillende prompt types
- Integration met bestaande prompt templates

Return:
- Complete agent XML schema
- Menu structuur
- Workflow integratie plan
```

**Agent 2 (Tech Writer):**
```
Schrijf agent persona en communicatie:
- Naam en icon voor prompt-writer agent
- Persona beschrijving (role, identity, communication_style, principles)
- Help teksten
- User guidance

Return:
- Persona sectie
- Help documentatie
- User interaction flows
```

**Agent 3 (Product Manager):**
```
Prioriteer features:
- Welke prompt types in MVP?
- Welke menu items zijn essentieel?
- Wat kan later toegevoegd worden?

Return:
- MVP feature set
- Nice-to-have features
- Future roadmap
```

---

## Fase 3: Implementatie

**Agent 4 (Code Reviewer) + Agent 1 (Architect):**
```
Implementeer de agent:
- Schrijf complete `.md` bestand
- Volg BMAD patterns exact
- Implementeer menu items
- Schrijf activation steps

Validation:
- ✓ Volgt XML schema?
- ✓ Config integratie correct?
- ✓ Menu-handlers compleet?
- ✓ Persona duidelijk?
- ✓ Help teksten aanwezig?

Return:
- Complete agent file
- Implementation notes
```

---

## Fase 4: Consensus Building

### 4.1 Cross-Validation

```
Architect ↔ BMAD Builder (structuur compliance)
Tech Writer ↔ PM (gebruiksvriendelijkheid)
Code Reviewer ↔ Architect (implementatie kwaliteit)
Complexity Checker reviews: All (simpliciteit)
```

### 4.2 Voting

Per component stemmen relevante agents:
1. Is de structuur BMAD-compliant? (JA/NEE/WIJZIGINGEN_NODIG)
2. Is de persona geschikt? (AGREE/SUGGEST_CHANGES)
3. Zijn de menu items compleet voor MVP? (AGREE/ADD/REMOVE)
4. Is de documentatie duidelijk? (JA/NEE/VERBETERINGEN)

### 4.3 Consensus Thresholds

| Component | Minimum Consensus |
|-----------|-------------------|
| BMAD Compliance | ≥75% |
| Persona Design | ≥70% |
| Menu Items | ≥70% |
| Documentatie | ≥60% |

---

## Output Format

### Deliverable 1: Analyse Rapport

```markdown
# BMAD Agent Structuur Analyse

## Executive Summary
[Key findings over BMAD agent patterns]

## Agent Structuur Blueprint
[Volledige breakdown van BMAD agent componenten]

## Best Practices
[Consensus-based best practices]

## Prompt Template Patronen
[Overzicht van prompt structuur patronen]
```

### Deliverable 2: Prompt-Writer Agent

**Locatie**: `/Users/chrislehnen/Projecten/Definitie-app/.bmad/core/agents/prompt-writer.md`

**Structuur**:
```markdown
---
name: "prompt-writer"
description: "Prompt Writer Agent"
---

[Agent activation instructies + XML structuur]

<agent id=".bmad/core/agents/prompt-writer.md" name="Prompt Writer" title="Prompt Writer" icon="✍️">
  <activation critical="MANDATORY">
    [Activation steps]
  </activation>

  <persona>
    <role>[Role]</role>
    <identity>[Identity]</identity>
    <communication_style>[Style]</communication_style>
    <principles>[Principles]</principles>
  </persona>

  <menu>
    <item cmd="*help">Show menu</item>
    <item cmd="*create-analysis-prompt">Generate deep analysis prompt</item>
    <item cmd="*create-review-prompt">Generate code review prompt</item>
    <item cmd="*create-implementation-prompt">Generate implementation prompt</item>
    <item cmd="*create-fix-prompt">Generate bug fix prompt</item>
    <item cmd="*list-templates">List available prompt templates</item>
    <item cmd="*exit">Exit</item>
  </menu>
</agent>
```

### Deliverable 3: Integratie Documentatie

```markdown
# Prompt-Writer Agent - Gebruikshandleiding

## Installatie
[Hoe de agent te activeren]

## Gebruik
[Voorbeelden per menu item]

## Integratie met Prompts
[Hoe de agent prompts genereert en opslaat]
```

---

## Constraints

- **BMAD Compliance**: Agent MOET voldoen aan BMAD Core standards
- **ULTRATHINK**: Diepgaande analyse van bestaande patronen vereist
- **CONSENSUS**: Geen implementatie zonder ≥70% agent consensus
- **Solo Developer**: Agent moet praktisch en gebruiksvriendelijk zijn
- **No Dependencies**: Agent moet standalone werken zonder extra configuratie
- **Dutch Language**: Agent moet Nederlands ondersteunen (via config)
- **Reusability**: Templates moeten herbruikbaar zijn

---

## Execution Command

```
Phase 1: Parallel → Agents 1,2,6 (BMAD structuur analyse)
Phase 1: Parallel → Agent 7 (BMAD Builder activatie)
Phase 1: Sequential → Agents 3,4,5 (use cases + quality check)
Phase 2: Sequential → Agents 1,2,3 (design nieuwe agent)
Phase 3: Sequential → Agents 1,4 (implementatie + review)
Phase 4: Sequential → Consensus building
Phase 5: Sequential → Deliverables generatie
```

---

## Success Criteria

- [ ] Volledige BMAD agent structuur geanalyseerd
- [ ] Best practices gedocumenteerd
- [ ] Nieuwe prompt-writer agent voldoet aan BMAD Core standards
- [ ] Agent heeft werkende menu items voor alle prompt types
- [ ] Consensus ≥70% op alle componenten
- [ ] Agent getest en gedocumenteerd
- [ ] Integratie met bestaande prompts gevalideerd
