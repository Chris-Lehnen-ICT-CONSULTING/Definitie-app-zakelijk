# Prompt Generator Subagent Specification

> **Version**: 1.0
> **Status**: Design Specification
> **Purpose**: Subagent that generates structured multiagent prompts following TEMPLATE-deep-analysis.md v2.0

---

## 1. Agent Definition

```yaml
name: prompt-generator
type: general-purpose
model: opus
description: |
  Generates structured multiagent prompts following TEMPLATE-deep-analysis.md.
  Triggered by hookify when user requests analysis, review, implementation, or fix tasks.
  Extracts context from user's original request and fills template sections automatically.
tools:
  - Read      # Read template and existing prompts
  - Write     # Save generated prompt to /prompts/
  - Glob      # Find relevant files for scope
  - Grep      # Search for patterns in codebase
trigger_mode: hookify_injection
output_directory: /prompts/
```

---

## 2. System Prompt

```markdown
# Prompt Generator Agent - System Prompt

Je bent de **Prompt Generator Agent**, een gespecialiseerde agent die gestructureerde multiagent analyse-prompts genereert volgens het TEMPLATE-deep-analysis.md v2.0 framework.

## Jouw Rol

Je ontvangt een gebruikersverzoek (via hookify injectie) en genereert een complete, uitvoerbare prompt die:
1. Het juiste execution mode selecteert (ULTRATHINK, MULTIAGENT, CONSENSUS)
2. De optimale agent configuratie bepaalt op basis van het taaktype
3. Scope en context automatisch afleidt uit het verzoek
4. Vote weights berekent voor consensus framework
5. Output format specificeert op basis van taaktype

## Invoerinterpretatie

### Stap 1: Taaktype Classificatie

Analyseer het gebruikersverzoek en classificeer in een van de volgende categorieeen:

| Categorie | Trefwoorden | Primair Doel |
|-----------|-------------|--------------|
| **Analyse** | analyseer, analyse, audit, onderzoek, evalueer, beoordeel | Begrip en inzicht |
| **Review** | review, code review, PR review, architecture review | Kwaliteitsbeoordeling |
| **Implementatie** | implementeer, bouw, maak, ontwikkel, refactor, migreer | Nieuwe functionaliteit |
| **Fix** | fix, repareer, los op, debug, corrigeer | Probleem oplossen |

### Stap 2: Scope Extractie

Uit het verzoek, extraheer:
- **Onderwerp**: Wat moet geanalyseerd/gereviewd/geimplementeerd/gefixed worden?
- **Bestanden**: Welke bestanden/directories zijn relevant?
- **Diepte**: Oppervlakkig (quick scan), Medium (standaard), Diepgaand (volledig)
- **Output**: Rapport, Recommendations, Roadmap, Code changes

### Stap 3: Context Verzameling

Verzamel context uit:
- CLAUDE.md voor project constraints
- Bestaande Linear issues indien relevant
- Codebase structuur via Glob
- Recent git history voor context

## Agent Selectie Regels

### Taaktype naar Agent Mapping

**Analyse taken:**
```
Primary:   Explorer (0.5x), Architect (2.0x), Code Reviewer (1.5x)
Secondary: Researcher (1.0x), Complexity Checker (1.5x)
Optional:  PM (1.5x) voor business context
```

**Review taken:**
```
Primary:   Code Reviewer (1.5x), Silent Failure Hunter (1.0x), Tester (1.0x)
Secondary: Type Analyst (0.75x), Debug Specialist (0.75x)
Optional:  Complexity Checker (1.5x), Architect (2.0x)
```

**Implementatie taken:**
```
Primary:   Architect (2.0x), Code Reviewer (1.5x), Tester (1.0x)
Secondary: PM (1.5x), Complexity Checker (1.5x)
Optional:  Explorer (0.5x), Researcher (1.0x)
```

**Fix taken:**
```
Primary:   Debug Specialist (0.75x), Silent Failure Hunter (1.0x), Code Reviewer (1.5x)
Secondary: Tester (1.0x), Type Analyst (0.75x)
Optional:  Explorer (0.5x)
```

### Minimum/Maximum Agents

- **Minimum**: 4 agents (voor adequate coverage)
- **Maximum**: 10 agents (volledige analyse)
- **Standaard**: 6 agents voor balans tussen coverage en efficiency

### Vote Weight Berekening

```python
total_weight = sum(agent.weight for agent in selected_agents)
normalized_weight = agent.weight / total_weight * 100  # percentages
```

## Template Filling Instructies

### Sectie: Execution Mode

```markdown
## Execution Mode

| Setting | Value |
|---------|-------|
| **ULTRATHINK** | {Ja voor diepgaande taken, Nee voor quick fixes} |
| **MULTIAGENT** | {aantal} gespecialiseerde agents |
| **CONSENSUS** | {Vereist/Optioneel - Vereist voor architectuur en kritieke wijzigingen} |
```

### Sectie: Agent Configuratie

Genereer tabel met geselecteerde agents:
- Altijd model "opus" gebruiken
- Vote weights uit mapping halen
- Focus area specifiek maken voor de taak

### Sectie: Opdracht

Formuleer de opdracht in 2-3 zinnen:
- Wat moet er gedaan worden?
- Waarom is dit belangrijk?
- Wat is het gewenste resultaat?

### Sectie: Scope

| Aspect | Invulling |
|--------|-----------|
| **Doel** | Extract uit gebruikersverzoek |
| **Bestanden** | Afleiden uit context of vraag aan gebruiker |
| **Diepte** | Bepaal op basis van complexiteit |
| **Output** | Match met taaktype |

### Sectie: Context

- **Huidige Situatie**: Voeg visuele structuur toe indien relevant
- **Probleemstelling**: Extraheer uit verzoek of vraag
- **Gewenste Eindsituatie**: Afleiden uit doel
- **Achtergrond**: Project naam, tech stack, constraints uit CLAUDE.md

### Sectie: Agent Assignments

Per geselecteerde agent, genereer:
```
**Agent {N} ({Role}):**
\```
{Specifieke opdracht voor deze agent}

Focus: {Specifieke focus punten}
Return:
- {Verwachte output 1}
- {Verwachte output 2}
- VOTE op {relevante findings van andere agents}
\```
```

### Sectie: Consensus Framework

Standaard thresholds:
- Critical issues: >=75%
- Important: >=60%
- Suggestions: >=50%

Pas aan op basis van taaktype:
- Architectuur: hogere thresholds (75-80%)
- Quick fixes: lagere thresholds (50-60%)

### Sectie: Output Format

Kies template op basis van taaktype:
- Analyse -> Rapport met bevindingen
- Review -> Kwaliteitsscores + aanbevelingen
- Implementatie -> Design + implementation plan
- Fix -> Root cause + oplossing + preventie

### Sectie: Constraints

Altijd includeren:
- ULTRATHINK indien van toepassing
- Consensus requirement indien van toepassing
- "Solo Developer: Geen team overhead, praktische oplossingen"
- Project-specifieke constraints uit CLAUDE.md

## Output Specificatie

### Bestandsnaam

Format: `{taak-beschrijving-slug}.md`

Voorbeelden:
- `prompt-engineering-analysis.md`
- `validation-service-review.md`
- `dark-mode-implementation.md`
- `race-condition-fix.md`

### Locatie

Altijd opslaan in: `/prompts/`

### Validatie voor Opslaan

Controleer:
1. [ ] Alle [PLACEHOLDERS] zijn ingevuld
2. [ ] Minimum 4 agents geconfigureerd
3. [ ] Vote weights berekend en gedocumenteerd
4. [ ] Consensus thresholds gedefinieerd
5. [ ] Output format gespecificeerd
6. [ ] Execution command aanwezig

## Interactie Protocol

### Bij onduidelijke scope

Vraag gebruiker:
> "Ik heb de volgende scope afgeleid: [scope]. Is dit correct?
> - Ja: Genereer prompt
> - Nee: Welke bestanden/directories moeten meegenomen worden?"

### Bij complexe taken

Suggereer opsplitsing:
> "Dit verzoek lijkt meerdere taken te bevatten:
> 1. [Taak A]
> 2. [Taak B]
> Wil je dat ik aparte prompts genereer, of alles in een prompt?"

### Na generatie

Bevestig:
> "Prompt opgeslagen in `/prompts/{bestandsnaam}.md`
>
> **Samenvatting:**
> - Taaktype: {type}
> - Agents: {aantal} ({namen})
> - Consensus: {threshold}%
>
> Wil je de prompt nu uitvoeren?"
```

---

## 3. Input/Output Contract

### Input

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_request` | string | Yes | Originele gebruikersboodschap (via hookify) |
| `trigger_keywords` | string[] | Yes | Keywords die hook triggerde |
| `project_root` | string | Yes | Pad naar project root |
| `claude_md_path` | string | No | Pad naar CLAUDE.md (default: {project_root}/CLAUDE.md) |

### Output

| Field | Type | Description |
|-------|------|-------------|
| `prompt_path` | string | Absoluut pad naar gegenereerde prompt |
| `task_type` | enum | Analyse, Review, Implementatie, Fix |
| `selected_agents` | object[] | Lijst van geselecteerde agents met weights |
| `scope_summary` | object | Doel, Bestanden, Diepte, Output |
| `execution_ready` | boolean | True als prompt direct uitvoerbaar is |

### Generated Prompt Structure

```markdown
# {Titel}

## Execution Mode
[Execution settings tabel]

## Agent Configuratie
[Agent tabel met roles, types, focus, weights]

## Opdracht
[2-3 zinnen taakbeschrijving]

### Scope
[Scope tabel]

## Context
[Huidige situatie, Probleemstelling, Gewenste eindsituatie, Achtergrond]

## Consensus Framework
[Regels, Categorieen, Voting Matrix, Thresholds]

## Fase 1-N: [Fase namen]
[Agent assignments per fase]

## Output Format
[Verwacht output formaat]

## Constraints
[Project en taak constraints]

## Input Bestanden
[Relevante bestanden]

## Execution Command
[Fase-gebaseerde uitvoering instructies]
```

---

## 4. Agent Selection Matrix

| Task Type | Detection Keywords | Primary Agents | Secondary Agents | Optional Agents | Min Weight | Max Weight |
|-----------|-------------------|----------------|------------------|-----------------|------------|------------|
| **Analyse** | analyseer, analyse, audit, onderzoek, evalueer, beoordeel | Explorer, Architect, Code Reviewer | Researcher, Complexity Checker | PM | 4.0x | 9.0x |
| **Review** | review, code review, PR review, architecture review | Code Reviewer, Silent Failure Hunter, Tester | Type Analyst, Debug Specialist | Complexity Checker, Architect | 3.5x | 9.5x |
| **Implementatie** | implementeer, bouw, maak, ontwikkel, refactor, migreer | Architect, Code Reviewer, Tester | PM, Complexity Checker | Explorer, Researcher | 4.5x | 10.0x |
| **Fix** | fix, repareer, los op, debug, corrigeer | Debug Specialist, Silent Failure Hunter, Code Reviewer | Tester, Type Analyst | Explorer | 3.0x | 6.25x |

### Agent Reference

| Agent Name | Type Identifier | Default Weight | Best For |
|------------|-----------------|----------------|----------|
| Code Reviewer | `code-reviewer` | 1.5x | Code quality, patterns, anti-patterns |
| Tester | `pr-review-toolkit:pr-test-analyzer` | 1.0x | Test coverage, edge cases |
| Architect | `feature-dev:code-architect` | 2.0x | Architecture, module design |
| Product Manager | `product-manager` | 1.5x | Business value, prioritering |
| Complexity Checker | `code-simplifier` | 1.5x | Over-engineering, simplificatie |
| Silent Failure Hunter | `pr-review-toolkit:silent-failure-hunter` | 1.0x | Error handling, silent failures |
| Type Analyst | `pr-review-toolkit:type-design-analyzer` | 0.75x | Type safety, data structures |
| Debug Specialist | `debug-specialist` | 0.75x | Logging, observability |
| Explorer | `Explore` | 0.5x | Codebase verkenning, dependencies |
| Researcher | `general-purpose` | 1.0x | Perplexity + Context7 research |

---

## 5. Template Filling Algorithm

```
ALGORITHM: GeneratePrompt(user_request)

INPUT: user_request (string)
OUTPUT: prompt_content (markdown string), prompt_path (string)

1. CLASSIFY task_type
   keywords = EXTRACT_KEYWORDS(user_request)
   task_type = MATCH_TASK_TYPE(keywords)
   # Returns: Analyse | Review | Implementatie | Fix

2. EXTRACT scope
   subject = EXTRACT_SUBJECT(user_request)
   files = INFER_FILES(user_request) OR ASK_USER()
   depth = DETERMINE_DEPTH(user_request)  # Oppervlakkig | Medium | Diepgaand
   output_type = MAP_OUTPUT_TYPE(task_type)  # Rapport | Recommendations | Code

3. SELECT agents
   primary_agents = GET_PRIMARY_AGENTS(task_type)
   secondary_agents = GET_SECONDARY_AGENTS(task_type)

   IF depth == "Diepgaand":
       optional_agents = GET_OPTIONAL_AGENTS(task_type)
       selected_agents = primary + secondary + optional
   ELSE IF depth == "Medium":
       selected_agents = primary + secondary
   ELSE:
       selected_agents = primary

   ENSURE len(selected_agents) >= 4

4. CALCULATE vote weights
   total_weight = SUM(agent.weight for agent in selected_agents)
   FOR agent in selected_agents:
       agent.normalized_weight = agent.weight / total_weight * 100

5. LOAD template
   template = READ("/prompts/TEMPLATE-deep-analysis.md")

6. FILL template sections

   6.1 Execution Mode
       ultrathink = task_type IN [Analyse, Review] OR depth == "Diepgaand"
       multiagent_count = len(selected_agents)
       consensus = task_type != Fix AND depth != "Oppervlakkig"

   6.2 Agent Configuratie
       FOR i, agent in ENUMERATE(selected_agents):
           FILL agent_row(i+1, agent.role, agent.type, agent.focus, agent.weight)
       CALCULATE total_vote_weight

   6.3 Opdracht
       GENERATE_TASK_DESCRIPTION(task_type, subject)

   6.4 Scope
       FILL scope_table(subject, files, depth, output_type)

   6.5 Context
       project_info = READ_CLAUDE_MD()
       current_state = ANALYZE_CODEBASE(files) IF files ELSE "Te bepalen"
       problem = EXTRACT_PROBLEM(user_request)
       desired_state = INFER_DESIRED_STATE(task_type, problem)

   6.6 Consensus Framework
       thresholds = GET_THRESHOLDS(task_type, depth)
       voting_matrix = GENERATE_VOTING_MATRIX(selected_agents)

   6.7 Agent Assignments (per fase)
       phases = DETERMINE_PHASES(task_type)
       FOR phase in phases:
           relevant_agents = GET_PHASE_AGENTS(phase, selected_agents)
           FOR agent in relevant_agents:
               GENERATE_AGENT_ASSIGNMENT(agent, subject, phase)

   6.8 Output Format
       output_template = GET_OUTPUT_TEMPLATE(task_type)
       FILL output_format_section(output_template)

   6.9 Constraints
       standard_constraints = ["Solo Developer", "Praktische oplossingen"]
       IF ultrathink:
           ADD "ULTRATHINK: Diepgaande analyse vereist"
       IF consensus:
           ADD "CONSENSUS: Geen recommendations zonder voldoende consensus"
       project_constraints = EXTRACT_CONSTRAINTS(CLAUDE.md)
       COMBINE all_constraints

   6.10 Execution Command
        GENERATE_PHASE_COMMANDS(phases, selected_agents)

7. GENERATE filename
   slug = SLUGIFY(subject)
   filename = f"{slug}.md"
   prompt_path = f"/prompts/{filename}"

8. VALIDATE prompt
   validation_result = VALIDATE_PROMPT(prompt_content)
   IF NOT validation_result.valid:
       REPORT validation_result.errors
       RETURN ERROR

9. SAVE prompt
   WRITE(prompt_path, prompt_content)

10. RETURN prompt_content, prompt_path
```

---

## 6. Quality Validation Checklist

### Structural Validation

| Check | Rule | Severity |
|-------|------|----------|
| Placeholders filled | No `[PLACEHOLDER]` text remaining | BLOCK |
| Minimum agents | At least 4 agents configured | BLOCK |
| Vote weights present | All agents have vote weight | BLOCK |
| Total weight calculated | "Totaal Vote Weight: Xx" present | WARN |
| Execution Mode complete | All 3 settings filled | BLOCK |
| Scope table complete | All 4 aspects filled | WARN |
| Output format specified | Non-empty output section | BLOCK |
| Execution command present | Phase-based commands defined | WARN |

### Content Validation

| Check | Rule | Severity |
|-------|------|----------|
| Relevant agents | Agents match task type | WARN |
| Consensus thresholds | Thresholds defined for task type | WARN |
| Context provided | At least problem statement present | WARN |
| Agent assignments specific | Each agent has specific focus | WARN |
| Files identified | Either specified or marked "Te bepalen" | INFO |

### Consistency Validation

| Check | Rule | Severity |
|-------|------|----------|
| Agent count matches | Multiagent count = len(agents) | BLOCK |
| Weights sum correctly | Individual weights = total | WARN |
| Phases reference correct agents | Agent numbers in phases exist | BLOCK |
| Voting matrix agents match | Matrix columns = selected agents | WARN |

### Quality Validation

| Check | Rule | Severity |
|-------|------|----------|
| Dutch language | Prompt in Dutch (except technical terms) | INFO |
| Clear opdracht | Task description is actionable | WARN |
| Appropriate depth | Depth matches task complexity | INFO |
| Reasonable scope | Not too broad, not too narrow | INFO |

---

## 7. Example Generated Prompts

### Example 1: Analyse Task

**User Request**: "Analyseer de validation service architectuur"

**Generated Prompt**:

```markdown
# Validation Service Architectuur Analyse

## Execution Mode

| Setting | Value |
|---------|-------|
| **ULTRATHINK** | Ja - Extended reasoning voor architectuur analyse |
| **MULTIAGENT** | 6 gespecialiseerde agents |
| **CONSENSUS** | Vereist voor alle aanbevelingen |

## Agent Configuratie

| # | Agent Role | Type | Model | Focus Area | Vote Weight |
|---|------------|------|-------|------------|-------------|
| 1 | **Explorer** | `Explore` | opus | Codebase mapping, dependencies | 0.5x |
| 2 | **Architect** | `feature-dev:code-architect` | opus | Architecture patterns, module design | 2.0x |
| 3 | **Code Reviewer** | `code-reviewer` | opus | Code quality, SOLID principles | 1.5x |
| 4 | **Complexity Checker** | `code-simplifier` | opus | Over-engineering detectie | 1.5x |
| 5 | **Researcher** | `general-purpose` | opus | Best practices research | 1.0x |
| 6 | **PM** | `product-manager` | opus | Business value, prioritering | 1.5x |

**Totaal Vote Weight: 8.0x**

## Opdracht

Voer een diepgaande analyse uit van de validation service architectuur in de Definitie-app. Identificeer architectural patterns, module structuur, en mogelijke verbeterpunten. Lever concrete aanbevelingen gebaseerd op consensus tussen agents.

### Scope

| Aspect | Waarde |
|--------|--------|
| **Doel** | Architectuur analyse van validation services |
| **Bestanden** | `src/services/validation/`, `src/toetsregels/` |
| **Diepte** | Diepgaand - Volledige architectuur analyse |
| **Output** | Rapport met architecture diagrams + recommendations |

## Context

### Huidige Situatie

```
src/services/validation/
├── validation_orchestrator_v2.py    # Main orchestration
├── modular_validation_service.py    # 45 rules management
└── ...

src/toetsregels/
├── regels/                          # Rule implementations
└── rule_cache.py                    # TTL caching
```

### Probleemstelling

1. **Onduidelijke architectuur**: Hoe zijn de 45 validatieregels georganiseerd?
2. **Performance**: Is de caching strategie optimaal?
3. **Extensibility**: Hoe makkelijk zijn nieuwe regels toe te voegen?

### Achtergrond

- **Project**: Definitie-app (Dutch AI Definition Generator)
- **Technologie**: Python 3.11+, Streamlit
- **Constraints**: Solo developer, geen backwards compatibility nodig

## Fase 1: Codebase Analyse

**Agent 1 (Explorer):**
```
Verken de validation codebase:
- Map alle bestanden in src/services/validation/
- Identificeer dependencies tussen modules
- Documenteer de 45 regels structuur

Return:
- Complete file inventory
- Dependency graph
- PROVIDE CONTEXT voor andere agents
```

**Agent 2 (Architect):**
```
Analyseer de validation architectuur:
- Identificeer design patterns gebruikt
- Evalueer module separation
- Beoordeel extensibility

Focus: Layer separation, coupling, cohesion
Return:
- Architecture diagram (text-based)
- Pattern inventory
- Architectural debt assessment
- VOTE op architecture-related findings
```

[... rest of agent assignments ...]

## Consensus Framework

### Consensus Thresholds

| Type | Minimum | Vereiste Agents |
|------|---------|-----------------|
| Architecture Changes | >=75% | Min. 3 agents |
| Quick Wins | >=50% | Min. 2 agents |

## Output Format

```markdown
# Validation Service Architecture Analysis

## Executive Summary
[Key findings - alleen consensus items]

## Architecture Overview
[Diagrams en patterns]

## Recommendations (Consensus Required)
### Quick Wins (<2h) - >=50% consensus
### Short Term (2-8h) - >=60% consensus
### Long Term (>8h) - >=75% consensus
```

## Constraints

- **ULTRATHINK**: Diepgaande analyse vereist
- **CONSENSUS**: Geen recommendations zonder voldoende consensus
- **Solo Developer**: Praktische oplossingen
- **Focus op actionable insights**

## Execution Command

```
Phase 1: Parallel -> Agent 1 (exploration)
Phase 2: Parallel -> Agents 2,3,4 (analysis)
Phase 3: Parallel -> Agent 5 (research)
Phase 4: Sequential -> CONSENSUS BUILDING
Phase 5: Sequential -> Rapport generatie
```
```

---

### Example 2: Fix Task

**User Request**: "Fix de race condition in SessionStateManager"

**Generated Prompt**:

```markdown
# Race Condition Fix - SessionStateManager

## Execution Mode

| Setting | Value |
|---------|-------|
| **ULTRATHINK** | Nee - Gerichte fix |
| **MULTIAGENT** | 4 gespecialiseerde agents |
| **CONSENSUS** | Optioneel - Fix vereist snelle actie |

## Agent Configuratie

| # | Agent Role | Type | Model | Focus Area | Vote Weight |
|---|------------|------|-------|------------|-------------|
| 1 | **Debug Specialist** | `debug-specialist` | opus | Root cause analysis, logging | 0.75x |
| 2 | **Silent Failure Hunter** | `pr-review-toolkit:silent-failure-hunter` | opus | Error handling, race conditions | 1.0x |
| 3 | **Code Reviewer** | `code-reviewer` | opus | Fix quality, patterns | 1.5x |
| 4 | **Tester** | `pr-review-toolkit:pr-test-analyzer` | opus | Test coverage voor fix | 1.0x |

**Totaal Vote Weight: 4.25x**

## Opdracht

Identificeer en fix de race condition in SessionStateManager. Zorg voor een robuuste oplossing die toekomstige race conditions voorkomt en voeg tests toe om regressie te detecteren.

### Scope

| Aspect | Waarde |
|--------|--------|
| **Doel** | Race condition in SessionStateManager fixen |
| **Bestanden** | `src/ui/session_state.py` |
| **Diepte** | Medium - Gerichte analyse + fix |
| **Output** | Root cause + Fix + Tests |

## Fase 1: Root Cause Analysis

**Agent 1 (Debug Specialist):**
```
Analyseer de race condition:
- Identificeer de exacte locatie
- Bepaal de trigger conditions
- Trace de execution flow

Return:
- Root cause beschrijving
- Reproduction steps
- Logging recommendations
```

**Agent 2 (Silent Failure Hunter):**
```
Zoek gerelateerde issues:
- Andere potential race conditions
- Thread-safety issues
- State corruption scenarios

Return:
- Risk assessment
- Additional issues found
- Prevention recommendations
```

## Fase 2: Fix Implementation

**Agent 3 (Code Reviewer):**
```
Review de fix:
- Is de oplossing thread-safe?
- Volgt het project patterns?
- Zijn er side effects?

Return:
- Code quality assessment
- Alternative approaches
- VOTE op fix acceptatie
```

## Fase 3: Test Coverage

**Agent 4 (Tester):**
```
Schrijf tests voor de fix:
- Unit tests voor de fix
- Edge case coverage
- Regression prevention

Return:
- Test scenarios
- Coverage assessment
```

## Output Format

```markdown
# Race Condition Fix Report

## Root Cause
[Beschrijving van het probleem]

## Fix
[Code changes]

## Tests
[Test scenarios + code]

## Prevention
[Hoe dit in de toekomst te voorkomen]
```

## Constraints

- **Minimale impact**: Geen onnodige wijzigingen
- **Test coverage**: Fix MOET getest worden
- **Solo Developer**: Snelle, effectieve oplossing

## Execution Command

```
Phase 1: Sequential -> Agent 1 (debug)
Phase 2: Parallel -> Agent 2 (safety check)
Phase 3: Sequential -> Agent 3 (review fix)
Phase 4: Sequential -> Agent 4 (tests)
```
```

---

## Key Findings

1. **Template coverage is comprehensive** (Confidence: 95%)
   - TEMPLATE-deep-analysis.md v2.0 provides all necessary sections for prompt generation

2. **Agent selection can be deterministic** (Confidence: 90%)
   - Task type keywords reliably map to appropriate agent combinations
   - Weight calculations are straightforward

3. **Context extraction requires hybrid approach** (Confidence: 85%)
   - Some context can be auto-extracted (project info, file structure)
   - Scope often requires user confirmation

4. **Validation is critical for quality** (Confidence: 95%)
   - Incomplete prompts lead to poor execution
   - Checklist-based validation prevents common errors

5. **Hookify integration is straightforward** (Confidence: 90%)
   - Single trigger point (user prompt matching keywords)
   - Clear handoff to subagent with context

---

## Vote Readiness

### Ready to Vote On:
- Agent selection matrix (complete)
- Template filling algorithm (complete)
- Validation checklist (complete)
- Example prompts (complete)

### Confidence Score: 92/100

### Remaining Items:
- Hookify integration specifics (depends on hookify plugin capabilities)
- Error handling for edge cases
- User interaction flow for ambiguous requests

---

## Implementation Notes

### Integration with Hookify

The prompt-generator subagent should be triggered by a hookify rule with:
- **Event**: `prompt`
- **Pattern**: `\b(analyseer|analyse|audit|onderzoek|review|code review|PR review|implementeer|bouw|maak|ontwikkel|refactor|migreer|fix|repareer|debug)\b`
- **Action**: `spawn-agent` (or equivalent hookify mechanism)

### Handoff Protocol

1. Hookify detects trigger keyword
2. Hookify injects prompt-generator system prompt
3. Subagent receives `user_request` and context
4. Subagent generates prompt
5. Subagent saves to `/prompts/`
6. Subagent asks user: "Prompt generated. Execute now?"
7. If yes: Main agent executes the generated prompt
