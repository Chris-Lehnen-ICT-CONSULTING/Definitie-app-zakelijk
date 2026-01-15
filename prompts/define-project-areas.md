# Codebase Functionele Area-onderverdeling voor Multiagent Analyse

## 1. Analyse Doelstelling

Analyseer een complete codebase om een intelligente functionele onderverdeling te creëren die optimaal werkt met multiagent analyse systemen. Het doel is om cohesieve, logisch gegroepeerde code areas te identificeren die parallel door AI agents geanalyseerd kunnen worden, onafhankelijk van de bestaande directory structuur.

## 2. Scope

### Binnen scope:
- Complete codebase analyse (alle source code bestanden)
- LOC (Lines of Code) tellingen per bestand en directory
- Functionele cohesie identificatie op basis van:
  - Code dependencies en imports
  - Gedeelde interfaces en data structuren
  - Business logic samenhang
  - Technische verantwoordelijkheden
- Monster files (>1000 LOC) detectie en isolatie
- Generatie van project-areas.yaml configuratie
- Optionele registratie via prompt-forge API

### Buiten scope:
- Code kwaliteit beoordeling (dat komt later via de areas)
- Performance analyse van individuele componenten
- Security audit van specifieke code onderdelen
- Documentatie analyse (focus op source code)

### Diepte niveau:
Diepgaand - volledige codebase verkenning met functionele analyse

## 3. Analyse Criteria

### Code Structuur Analyse:
- **LOC Metrics**: Exacte telling per bestand, cumulatief per logische groep
- **Dependency Mapping**: Import/require statements, function calls, class inheritance
- **Interface Cohesie**: Gedeelde types, interfaces, data models
- **Functionele Verantwoordelijkheden**: Business logic clusters, technical concerns

### Area Formatie Criteria:
- **Cohesie Score**: Hoe sterk gerelateerd zijn bestanden binnen een area
- **Size Optimization**: Areas tussen 1000-4000 LOC voor effectieve AI analyse
- **Monster File Detection**: Bestanden >1000 LOC als separate areas
- **Logical Boundaries**: Respect voor natuurlijke code grenzen

### Kwaliteit Validatie:
- **Coverage**: Alle source files zijn toegewezen aan een area
- **Overlap**: Minimale file overlap tussen areas
- **Balance**: Redelijke verdeling van LOC over areas
- **Maintainability**: Areas volgen logische functionele lijnen

## 4. Verwachte Output

### Primaire Output: project-areas.yaml
```yaml
project_info:
  name: "Project Naam"
  total_loc: 15847
  total_files: 127
  analysis_timestamp: "2024-01-15T14:30:00Z"

areas:
  - area_id: "auth-system"
    name: "Authentication & Authorization"
    description: "User authentication, JWT handling, permission management"
    file_patterns:
      - "src/auth/**/*.ts"
      - "src/middleware/auth.ts"
      - "src/models/user.ts"
    estimated_loc: 1547
    is_monster_file: false
    focus_areas:
      - "security"
      - "user-management"
      - "session-handling"
  
  - area_id: "monster-api-handler"
    name: "Large API Handler File"
    description: "Single large file containing multiple API endpoints"
    file_patterns:
      - "src/api/handlers.ts"
    estimated_loc: 1203
    is_monster_file: true
    focus_areas:
      - "code-splitting"
      - "refactoring"
      - "api-design"
```

### Analyse Samenvatting:
- **Totaal Areas**: X functionele areas + Y monster files
- **LOC Verdeling**: Breakdown per area met percentages
- **Cohesie Score**: Gemiddelde functionele samenhang per area
- **Optimization Opportunities**: Areas die verder opgesplitst kunnen worden

### Aanbevelingen:
1. **Prioriteit Hoog**: Monster files die onmiddellijk gesplitst moeten worden
2. **Prioriteit Normaal**: Areas met suboptimale cohesie
3. **Prioriteit Laag**: Kleine optimalisaties voor betere balans

### API Registratie Output:
- Succesvolle registratie bevestiging
- Area IDs en namen zoals geregistreerd in prompt-forge
- Instructies voor gebruik met `prompt-forge orchestrate --project-id`

## 5. Context & Constraints

### Technische Constraints:
- **Area Size**: Ideaal 1000-4000 LOC per area voor AI efficiëntie
- **Monster Threshold**: Files >1000 LOC worden altijd apart behandeld
- **File Patterns**: Gebruik glob patterns compatible met prompt-forge
- **YAML Format**: Strict adherence aan prompt-forge schema

### Analyse Constraints:
- **Language Agnostic**: Moet werken voor TypeScript, Python, Java, etc.
- **Framework Independence**: Werkt onafhankelijk van specifieke frameworks
- **Git Awareness**: Respecteer .gitignore en focus op tracked files
- **Binary Exclusion**: Skip binaries, images, generated code

### Business Constraints:
- **Multiagent Compatible**: Areas moeten parallel analyseerbaar zijn
- **Review Friendly**: Logische groepering voor code review workflows
- **Maintenance Focused**: Areas die stabiel blijven bij code wijzigingen
- **Team Alignment**: Areas volgen team responsibilities waar mogelijk

### Prompt-forge Integration:
- **API Compatibility**: Output moet direct werken met prompt-forge CLI
- **Orchestrator Support**: Areas geschikt voor code-review, bug-hunt, architecture-analysis
- **Project Isolation**: Elke analyse genereert unieke project configuratie
- **Version Control**: Ondersteuning voor configuratie updates over tijd

**Success Criteria**: Een werkende project-areas.yaml die 100+ parallelle AI agents effectief kan verdelen over logische code onderdelen, resulterend in betere analyse kwaliteit dan directory-gebaseerde verdelingen.
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

> Analyseer een codebase en genereer een functionele area-onderverdeling voor multiagent analyse. De prompt moet: (1) De codebase verkennen en LOC per bestand/directory tellen, (2) Functionele groepen identificeren op basis van cohesie en verantwoordelijkheid - NIET op directory structuur, (3) Monster files (>1000 LOC) isoleren als aparte areas, (4) Een project-areas.yaml genereren met area_id, name, description, file_patterns, estimated_loc, is_monster_file, en focus_areas, (5) Areas tussen 1000-...


---

## Subagent Spawn Instructions

Spawn de volgende agents parallel. Elke agent analyseert vanuit hun expertise.

### Agent 1: Explorer

**Role:** Codebase Navigation Expert
**Weight:** 0.5x
**Focus:** Codebase exploration, File discovery, Pattern recognition

```python
Task(
    subagent_type="Explore",
    prompt="""
Je bent een **Codebase Navigation Expert** met expertise in Codebase exploration, File discovery, Pattern recognition.

## TAAK
Analyseer het volgende idee vanuit jouw expertise:

> Analyseer een codebase en genereer een functionele area-onderverdeling voor multiagent analyse. De prompt moet: (1) De codebase verkennen en LOC per bestand/directory tellen, (2) Functionele groepen identificeren op basis van cohesie en verantwoordelijkheid - NIET op directory structuur, (3) Monster...

Context: Context: Dit is voor de prompt-forge CLI tool die multiagent orchestratie ondersteunt. Areas worden gebruikt door code-review, bug-hunt, architecture-analysis orchestrators. Target audience: developer...

## ANALYSEER
Focus op je kernexpertise: Codebase exploration, File discovery, Pattern recognition

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

### Agent 2: Architect

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

> Analyseer een codebase en genereer een functionele area-onderverdeling voor multiagent analyse. De prompt moet: (1) De codebase verkennen en LOC per bestand/directory tellen, (2) Functionele groepen identificeren op basis van cohesie en verantwoordelijkheid - NIET op directory structuur, (3) Monster...

Context: Context: Dit is voor de prompt-forge CLI tool die multiagent orchestratie ondersteunt. Areas worden gebruikt door code-review, bug-hunt, architecture-analysis orchestrators. Target audience: developer...

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

### Agent 3: Code Reviewer

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

> Analyseer een codebase en genereer een functionele area-onderverdeling voor multiagent analyse. De prompt moet: (1) De codebase verkennen en LOC per bestand/directory tellen, (2) Functionele groepen identificeren op basis van cohesie en verantwoordelijkheid - NIET op directory structuur, (3) Monster...

Context: Context: Dit is voor de prompt-forge CLI tool die multiagent orchestratie ondersteunt. Areas worden gebruikt door code-review, bug-hunt, architecture-analysis orchestrators. Target audience: developer...

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

> Analyseer een codebase en genereer een functionele area-onderverdeling voor multiagent analyse. De prompt moet: (1) De codebase verkennen en LOC per bestand/directory tellen, (2) Functionele groepen identificeren op basis van cohesie en verantwoordelijkheid - NIET op directory structuur, (3) Monster...

Context: Context: Dit is voor de prompt-forge CLI tool die multiagent orchestratie ondersteunt. Areas worden gebruikt door code-review, bug-hunt, architecture-analysis orchestrators. Target audience: developer...

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

### Agent 5: Researcher

**Role:** Research & Documentation Expert
**Weight:** 1.0x
**Focus:** Research, Documentation, Best practices

```python
Task(
    subagent_type="general-purpose",
    prompt="""
Je bent een **Research & Documentation Expert** met expertise in Research, Documentation, Best practices.

## TAAK
Analyseer het volgende idee vanuit jouw expertise:

> Analyseer een codebase en genereer een functionele area-onderverdeling voor multiagent analyse. De prompt moet: (1) De codebase verkennen en LOC per bestand/directory tellen, (2) Functionele groepen identificeren op basis van cohesie en verantwoordelijkheid - NIET op directory structuur, (3) Monster...

Context: Context: Dit is voor de prompt-forge CLI tool die multiagent orchestratie ondersteunt. Areas worden gebruikt door code-review, bug-hunt, architecture-analysis orchestrators. Target audience: developer...

## ANALYSEER
Focus op je kernexpertise: Research, Documentation, Best practices

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

### Agent 6: Product Manager

**Role:** Product Owner & Business Value Expert
**Weight:** 1.5x
**Focus:** Business value, User experience, Requirements clarity

```python
Task(
    subagent_type="product-manager",
    prompt="""
Je bent een **Product Owner & Business Value Expert** met expertise in Business value, User experience, Requirements clarity.

## TAAK
Analyseer het volgende idee vanuit jouw expertise:

> Analyseer een codebase en genereer een functionele area-onderverdeling voor multiagent analyse. De prompt moet: (1) De codebase verkennen en LOC per bestand/directory tellen, (2) Functionele groepen identificeren op basis van cohesie en verantwoordelijkheid - NIET op directory structuur, (3) Monster...

Context: Context: Dit is voor de prompt-forge CLI tool die multiagent orchestratie ondersteunt. Areas worden gebruikt door code-review, bug-hunt, architecture-analysis orchestrators. Target audience: developer...

## ANALYSEER
Focus op je kernexpertise: Business value, User experience, Requirements clarity

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

### Agent 7: Type Analyst

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

> Analyseer een codebase en genereer een functionele area-onderverdeling voor multiagent analyse. De prompt moet: (1) De codebase verkennen en LOC per bestand/directory tellen, (2) Functionele groepen identificeren op basis van cohesie en verantwoordelijkheid - NIET op directory structuur, (3) Monster...

Context: Context: Dit is voor de prompt-forge CLI tool die multiagent orchestratie ondersteunt. Areas worden gebruikt door code-review, bug-hunt, architecture-analysis orchestrators. Target audience: developer...

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


---

## Synthesis Instructions

Na ontvangst van alle 7 agent summaries:

### Stap 1: Verzamel Resultaten
Wacht tot alle agents hun summary hebben gegeven:
- Explorer, Architect, Code Reviewer, Simplicity Enforcer, Researcher, Product Manager en Type Analyst

### Stap 2: Bereken Consensus
| Agent | Score | Vote | Weight | Weighted Score |
|-------|-------|------|--------|----------------|
| Explorer | X/10 | AGREE/PARTIAL/DISAGREE | 0.5x | X |
| Architect | X/10 | AGREE/PARTIAL/DISAGREE | 2.0x | X |
| Code Reviewer | X/10 | AGREE/PARTIAL/DISAGREE | 1.5x | X |
| Simplicity Enforcer | X/10 | AGREE/PARTIAL/DISAGREE | 2.0x | X |
| Researcher | X/10 | AGREE/PARTIAL/DISAGREE | 1.0x | X |
| Product Manager | X/10 | AGREE/PARTIAL/DISAGREE | 1.5x | X |
| Type Analyst | X/10 | AGREE/PARTIAL/DISAGREE | 0.8x | X |

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
| **Task Type** | analyse |
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
prompt-forge forge --type analyse --multiagent --depth deep --ultrathink "[your idea]"
```
