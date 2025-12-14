# Claude Code Subagent Inventory Analysis

> **Doel**: Complete inventarisatie en categorisatie van alle beschikbare agents in Claude Code CLI.
> **Scope**: Plugin marketplace agents, project-specifieke agents, en ingebouwde capabilities.

---

## Execution Mode

| Setting | Value |
|---------|-------|
| **ULTRATHINK** | Ja - Extended reasoning voor volledige discovery |
| **MULTIAGENT** | 4 gespecialiseerde agents |
| **CONSENSUS** | Vereist voor categorisatie en aanbevelingen |

---

## Agent Configuratie

| # | Agent Role | Type | Model | Focus Area | Vote Weight |
|---|------------|------|-------|------------|-------------|
| 1 | **Explorer** | `Explore` | opus | Bestandslocatie, discovery, scanning | 1.5x |
| 2 | **Architect** | `feature-dev:code-architect` | opus | Categorisatie structuur, taxonomie | 2.0x |
| 3 | **Code Reviewer** | `code-reviewer` | opus | Agent description quality, completeness | 1.0x |
| 4 | **Product Manager** | `product-manager` | opus | Use case mapping, prioritering | 1.5x |

**Totaal Vote Weight: 6.0x** (gewogen consensus)

---

## Opdracht

Inventariseer en analyseer ALLE beschikbare agents binnen de Claude Code CLI omgeving, inclusief plugin marketplace agents, project-specifieke agents, en ingebouwde Task tool capabilities. Het exacte aantal agents is onbekend en moet worden ontdekt.

### Scope

| Aspect | Waarde |
|--------|--------|
| **Doel** | Complete inventarisatie van alle agents met metadata |
| **Bestanden** | Alle `.md` files in agent directories + plugin.json manifests |
| **Diepte** | Diepgaand - volledige metadata extractie |
| **Output** | Gecategoriseerde inventory + use case guide + recommendations |

---

## Context

### Bekende Agent Locaties

```
Te Scannen Directories:
├── ~/.claude/plugins/marketplaces/claude-code-plugins/plugins/*/agents/*.md
│   └── Plugin marketplace agents (15+ gevonden)
├── /Users/chrislehnen/Projecten/Definitie-app/.claude/agents/
│   └── Project-specifieke agents (1 gevonden: product-manager.md)
├── ~/.claude/plugins/marketplaces/claude-code-plugins/plugins/*/.claude-plugin/plugin.json
│   └── Plugin manifests voor metadata
└── BMad method (niet aanwezig in dit project)
```

### Preliminaire Inventory (te valideren)

Gevonden plugin agents:
1. `agent-sdk-dev/agents/agent-sdk-verifier-py.md`
2. `agent-sdk-dev/agents/agent-sdk-verifier-ts.md`
3. `feature-dev/agents/code-architect.md`
4. `feature-dev/agents/code-explorer.md`
5. `feature-dev/agents/code-reviewer.md`
6. `hookify/agents/conversation-analyzer.md`
7. `plugin-dev/agents/agent-creator.md`
8. `plugin-dev/agents/plugin-validator.md`
9. `plugin-dev/agents/skill-reviewer.md`
10. `pr-review-toolkit/agents/code-reviewer.md`
11. `pr-review-toolkit/agents/code-simplifier.md`
12. `pr-review-toolkit/agents/comment-analyzer.md`
13. `pr-review-toolkit/agents/pr-test-analyzer.md`
14. `pr-review-toolkit/agents/silent-failure-hunter.md`
15. `pr-review-toolkit/agents/type-design-analyzer.md`

Project-specifiek:
16. `.claude/agents/product-manager.md`

### Gewenste Output Structuur

```
Agent Inventory Report
├── 1. Discovery Summary
│   ├── Total agents found
│   ├── Per-source breakdown
│   └── Scan coverage verification
├── 2. Agent Catalog
│   ├── Per-agent metadata card
│   └── Frontmatter extraction
├── 3. Categorisatie
│   ├── Functionele groepen
│   └── Overlap analyse
├── 4. Use Case Matrix
│   ├── Wanneer welke agent
│   └── Agent chains/combinaties
└── 5. Aanbevelingen
    ├── Gaps in coverage
    └── Custom agents nodig
```

---

## Consensus Framework

### Consensus Regels

1. **Categorisatie**: Alle 4 agents moeten instemmen met de functionele groepering
2. **Overlap Detection**: Code Reviewer + Architect moeten overlap bevestigen
3. **Use Case Mapping**: PM + Architect bepalen primaire use cases

### Consensus Categorieën

| Categorie | Vereiste Consensus | Betrokken Agents |
|-----------|-------------------|------------------|
| Agent Discovery | >=75% | EX, CR |
| Functional Grouping | >=75% | AR, PM, CR |
| Overlap Detection | >=60% | CR, AR |
| Use Case Recommendations | >=60% | PM, AR |
| Gap Analysis | >=50% | Alle agents |

---

## Fase 1: Discovery (Explorer)

### 1.1 Scan Alle Locaties

```
Explorer Agent Assignment:

SCAN de volgende directories recursief:

1. PLUGIN MARKETPLACE:
   ~/.claude/plugins/marketplaces/claude-code-plugins/plugins/*/agents/*.md

   Voor elke gevonden agent:
   - File path (absoluut)
   - File size
   - Last modified date

2. PROJECT-SPECIFIEK:
   /Users/chrislehnen/Projecten/Definitie-app/.claude/agents/*.md

3. PLUGIN MANIFESTS:
   ~/.claude/plugins/marketplaces/claude-code-plugins/plugins/*/.claude-plugin/plugin.json

   Extraheer:
   - Plugin naam
   - Geregistreerde agents
   - Dependencies

4. SKILLS (kunnen agent-achtige functionaliteit bevatten):
   ~/.claude/plugins/marketplaces/claude-code-plugins/plugins/*/skills/*/SKILL.md

Return:
- Complete file inventory als tabel
- Per-plugin breakdown
- Verificatie dat alle locaties gescand zijn
```

### 1.2 Inventory Validatie

```
Valideer de scan:
- [ ] Alle 15+ plugin agents gevonden
- [ ] Project agent (product-manager.md) gevonden
- [ ] Plugin manifests gelezen
- [ ] Skills geinventariseerd
- [ ] Geen directories overgeslagen
```

---

## Fase 2: Metadata Extraction (Code Reviewer + Explorer)

### 2.1 Agent Frontmatter Parsing

```
Code Reviewer Assignment:

Voor ELKE gevonden agent file, extraheer:

1. YAML FRONTMATTER:
   - name: [agent naam]
   - description: [wanneer te gebruiken]
   - model: [opus/sonnet/haiku/inherit]
   - color: [UI kleur]
   - tools: [beschikbare tools]

2. SYSTEM PROMPT ANALYSE:
   - Core rol/persona
   - Specifieke verantwoordelijkheden
   - Output format vereisten
   - Constraints

3. QUALITY ASSESSMENT:
   - Is description duidelijk genoeg voor auto-trigger?
   - Zijn tools relevant voor de taak?
   - Is model keuze passend?

Return per agent:
| Field | Value | Quality Score (1-5) |
|-------|-------|---------------------|
| name | ... | ... |
| description | ... | ... |
| model | ... | ... |
| tools | ... | ... |
| core_role | ... | ... |
```

### 2.2 Agent Card Template

```markdown
## Agent: [name]

**Source:** [plugin-name/agents/file.md]
**Model:** [opus/sonnet/haiku/inherit]
**Color:** [color]

**Description (trigger criteria):**
> [description uit frontmatter]

**Core Responsibilities:**
- [bullet points uit system prompt]

**Available Tools:**
[tool1], [tool2], [tool3]

**Best Used For:**
- [use case 1]
- [use case 2]

**Quality Notes:**
- Description clarity: [1-5]
- Tool relevance: [1-5]
- Model appropriateness: [1-5]
```

---

## Fase 3: Categorisatie (Architect + PM)

### 3.1 Functionele Groepering

```
Architect Assignment:

Groepeer alle agents in functionele categorieën.
Elke agent mag in MAX 2 categorieën.

Voorgestelde categorieën (aan te passen):

1. CODE REVIEW & QUALITY
   - Agents voor code review
   - Quality checks
   - Best practices enforcement

2. ARCHITECTURE & DESIGN
   - Feature design
   - System architecture
   - Pattern analysis

3. TESTING & VALIDATION
   - Test analyse
   - Coverage gaps
   - Test generation

4. ERROR HANDLING & RELIABILITY
   - Silent failure detection
   - Error handling review
   - Robustness checks

5. EXPLORATION & DISCOVERY
   - Codebase verkenning
   - Dependency mapping
   - Context gathering

6. DEVELOPMENT WORKFLOW
   - Plugin development
   - SDK development
   - Automation

7. PRODUCT & PLANNING
   - Requirements
   - User stories
   - Prioritering

8. SPECIALIZED
   - Type analysis
   - Complexity checking
   - Comment analysis

Return:
- Categorieën met agent assignments
- Rationale voor elke groupering
- Agents zonder duidelijke categorie (gaps)
```

### 3.2 Overlap Analyse

```
Code Reviewer + Architect:

Identificeer overlappende agents:

1. NAAM DUPLICATEN:
   - code-reviewer (feature-dev) vs code-reviewer (pr-review-toolkit)
   - Wat zijn de verschillen?

2. FUNCTIONELE OVERLAP:
   - Agents met vergelijkbare verantwoordelijkheden
   - Wanneer welke kiezen?

3. COMPLEMENTAIRE AGENTS:
   - Agents die goed samenwerken
   - Aanbevolen chains

Return:
| Agent A | Agent B | Overlap % | Difference | When to Use A | When to Use B |
|---------|---------|-----------|------------|---------------|---------------|
```

---

## Fase 4: Use Case Mapping (PM + Architect)

### 4.1 Task-to-Agent Matrix

```
PM Assignment:

Maak een decision matrix voor veelvoorkomende taken:

| Task | Primary Agent | Secondary Agent | Chain? |
|------|---------------|-----------------|--------|
| Code review van PR | ? | ? | ? |
| Feature design | ? | ? | ? |
| Bug hunting | ? | ? | ? |
| Codebase verkenning | ? | ? | ? |
| Error handling audit | ? | ? | ? |
| Architecture review | ? | ? | ? |
| Test gap analysis | ? | ? | ? |
| Plugin development | ? | ? | ? |
| Product planning | ? | ? | ? |
| Type safety review | ? | ? | ? |
| Complexity reduction | ? | ? | ? |
```

### 4.2 Agent Chain Recommendations

```
Architect + PM:

Definieer effectieve agent chains voor complexe taken:

1. COMPREHENSIVE PR REVIEW:
   Agent 1 → Agent 2 → Agent 3

2. FEATURE IMPLEMENTATION:
   Agent 1 → Agent 2 → Agent 3

3. BUG INVESTIGATION:
   Agent 1 → Agent 2 → Agent 3

4. ARCHITECTURE AUDIT:
   Agent 1 → Agent 2 → Agent 3

Per chain:
- Welke agents
- In welke volgorde
- Waarom deze combinatie
```

---

## Fase 5: Gap Analysis & Recommendations

### 5.1 Coverage Gaps

```
Alle Agents:

Identificeer ontbrekende agent types:

1. NIET GEDEKT:
   - Welke taken hebben geen dedicated agent?
   - Welke domeinen ontbreken?

2. ZWAK GEDEKT:
   - Taken met alleen generieke agents
   - Gebieden waar specialisatie helpt

3. OVER-GEDEKT:
   - Te veel overlappende agents
   - Consolidatie mogelijkheden
```

### 5.2 Custom Agent Recommendations

```
PM + Architect:

Aanbevelingen voor custom agents:

Voor dit project (Definitie-app) specifiek:
- Welke custom agents toevoegen aan .claude/agents/?
- Gebaseerd op project-specifieke taken

Algemeen:
- Welke agent types ontbreken in de marketplace?
- Suggesties voor community
```

---

## Output Format

```markdown
# Claude Code Agent Inventory Report

**Generated:** [datum]
**Total Agents Found:** [aantal]
**Sources Scanned:** [lijst]

---

## Executive Summary

[2-3 paragrafen met key findings]

### Key Numbers
- Plugin Marketplace Agents: [X]
- Project-Specific Agents: [Y]
- Skills with Agent-like Behavior: [Z]
- Total: [X+Y+Z]

---

## 1. Complete Agent Catalog

### 1.1 Code Review & Quality Agents

[Agent cards voor deze categorie]

### 1.2 Architecture & Design Agents

[Agent cards voor deze categorie]

[etc. voor alle categorieën]

---

## 2. Overlap Analysis

| Agent A | Agent B | Overlap | Key Difference |
|---------|---------|---------|----------------|

---

## 3. Use Case Quick Reference

### For Code Review
| Scenario | Use This Agent | Rationale |
|----------|----------------|-----------|

### For Feature Development
[etc.]

---

## 4. Recommended Agent Chains

### Chain 1: Comprehensive PR Review
```
[visual chain diagram]
```

[etc. voor andere chains]

---

## 5. Gap Analysis

### Missing Agents
[lijst]

### Recommendations for Custom Agents
[lijst met beschrijvingen]

---

## 6. Consensus Report

### Voting Matrix

| Finding | EX | AR | CR | PM | Consensus |
|---------|----|----|----|----|-----------|

### Dissenting Opinions
[indien van toepassing]

---

## Appendices

### A. Raw File Inventory
[complete lijst van alle gescande bestanden]

### B. Agent Frontmatter Data
[complete YAML extractie per agent]

### C. Plugin Manifest Summary
[relevante data uit plugin.json bestanden]
```

---

## Constraints

- **Discovery First**: Geen aannames over aantallen - scan eerst, tel daarna
- **ULTRATHINK**: Diepgaande analyse van elke agent
- **Opus-only**: Alle agents draaien op opus voor maximale kwaliteit
- **Consensus**: Categorisatie vereist cross-validatie
- **Praktisch**: Output moet direct bruikbaar zijn als reference guide

---

## Input Bestanden

### Te Lezen Agent Files

1. `~/.claude/plugins/marketplaces/claude-code-plugins/plugins/agent-sdk-dev/agents/*.md`
2. `~/.claude/plugins/marketplaces/claude-code-plugins/plugins/feature-dev/agents/*.md`
3. `~/.claude/plugins/marketplaces/claude-code-plugins/plugins/hookify/agents/*.md`
4. `~/.claude/plugins/marketplaces/claude-code-plugins/plugins/plugin-dev/agents/*.md`
5. `~/.claude/plugins/marketplaces/claude-code-plugins/plugins/pr-review-toolkit/agents/*.md`
6. `/Users/chrislehnen/Projecten/Definitie-app/.claude/agents/*.md`

### Plugin Manifests

7. Alle `.claude-plugin/plugin.json` bestanden

### Skills (optioneel)

8. Alle `SKILL.md` bestanden voor agent-achtige functionaliteit

---

## Execution Command

```
Phase 1: Explorer → Scan alle locaties, genereer file inventory
Phase 2: Parallel → Code Reviewer + Explorer extractie metadata
Phase 3: Parallel → Architect + PM categorisatie en use case mapping
Phase 4: Sequential → CONSENSUS BUILDING
  - Cross-validatie van categorisatie
  - Voting op overlaps en gaps
  - Consensus score berekening
Phase 5: Sequential → Rapport generatie met alle secties
```

---

## Checklist voor gebruik

- [x] Template ingevuld met specifieke paden
- [x] 4 agents geselecteerd (Explorer, Architect, Code Reviewer, PM)
- [x] Vote weights berekend (6.0x totaal)
- [x] Specifieke vragen toegevoegd met consensus thresholds
- [x] Discovery-first approach gedefinieerd
- [x] Output format gespecificeerd
- [x] Agent file locaties opgegeven
