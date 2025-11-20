---
aangemaakt: '08-09-2025'
applies_to: definitie-app@current
bijgewerkt: '12-09-2025'
canonical: true
last_verified: 12-09-2025
owner: architecture
prioriteit: medium
status: active
---



# Agents Richtlijnen

Dit document beschrijft hoe we gespecialiseerde agents inzetten binnen de Definitie‑app. Het doel is consistente kwaliteit, voorspelbaar gedrag en makkelijk samenwerken tussen mensen en agents.

## 🎯 HARMONISATIE: Alle Agents Volgen Unified Rules

### Verplichte Stappen voor ELKE Agent
1. **Include Preamble**: Start elke agent met `~/.ai-agents/AGENT_PREAMBLE.md`
2. **Load Unified Rules**: Laad `~/.ai-agents/UNIFIED_INSTRUCTIONS.md` bij init
3. **Run Preflight**: Check met `~/.ai-agents/preflight-checks.sh` voor acties
4. **Follow Approval Ladder**: Gebruik approval rules uit unified instructions
5. **Enforce Naming**: Gebruik Nederlandse context namen (organisatorische_context)

### Enforcement Tools
- **Template**: `~/.ai-agents/AGENT_TEMPLATE.md` voor nieuwe agents
- **Validator**: `~/.ai-agents/enforce-harmonization.sh` checkt compliance
- **Preamble**: `~/.ai-agents/AGENT_PREAMBLE.md` moet in elke agent

## Werken met meerdere agents
- Quickstart: [Multi‑Agent Quickstart](../handleidingen/ontwikkelaars/MULTIAGENT_QUICKSTART.md) — script + slash‑commando’s.
- Gids: [Codex Multi‑Agent Gebruik](../handleidingen/ontwikkelaars/codex-multi-agent-gebruik.md) — parallelle agents (worktrees/patches), selectiecriteria, quick‑checks en scoreboard.
- Script: `scripts/multiagent.sh` — init/status/review/teardown van agent‑worktrees.
- Advies‑check voor nut/zin: `bash scripts/multiagent.sh check` (NO bij docs‑only/tiny diffs; `--strict` om init te blokkeren; `--force` om te overriden).

## Claude Code Agents Locatie
- Beschikbare agent‑prompts: `~/.claude/agents/`
  - `code-reviewer.md`
  - `code-simplifier.md`
  - `debug-specialist.md`
  - `full-stack-developer.md`
- Aanroepen via de Task tool in Claude Code; gebruik exacte agent‑namen.

## Standaard Werkwijze
- Context eerst: lees relevante code, config en docs voordat je acties onderneemt.
- Plan klein: beschrijf in 3–6 korte stappen wat je gaat doen.
- Valideer: voer gerichte checks/tests uit op wat je veranderde.
- Logisch koppelen: verwijs naar bestaande documentatie en respecteer canonical locations.
- Minimaal ingrijpen: verander alleen wat nodig is, geen brede refactors zonder opdracht.

## Agent Keuze (zonder router)

- Kies altijd de lichtste passende agent voor de taak.
- Mapping (richtlijn):
  - `code-reviewer`: reviews van code/diffs, quick assessments, feedback.
  - `debug-specialist`: reproduceren/diagnosticeren van bugs en fouten.
  - `code-simplifier`: kleine refactors/opschoning zonder gedragswijziging.
  - `full-stack-developer`: implementatie van gewenste wijzigingen/kleine features.
 - Gebruik test-/lint‑checks proportioneel aan de wijziging; geen centrale router of automatische workflow vereist.

## Algemene Richtlijnen

### 🔍 Preflight Checks (Voor ELKE wijziging)
```bash
# 1. Unieke match check
rg "exact_string_to_change" --files-with-matches | wc -l  # Moet 1 zijn

# 2. Scope check
echo "Wijziging in: path/to/file.py"
echo "Impact op: [list affected components]"

# 3. Forbidden patterns
rg "import streamlit" src/services/ && echo "❌ BLOCKED"
rg "asyncio.run\(" src/services/ && echo "❌ BLOCKED"
rg "from ui\." src/services/ && echo "❌ BLOCKED"

# 4. Approval check
[[ lines > 100 || files > 5 ]] && echo "⚠️ APPROVAL REQUIRED"

# 5. Run automated preflight
~/.ai-agents/preflight-checks.sh .
```

### 📝 Naming & Import Canon

#### ✅ VERPLICHTE Namen (Canonical)
| Concept | MOET zijn | NOOIT |
|---------|-----------|-------|
| Context velden | `organisatorische_context` | `organizational_context` |
| Context velden | `juridische_context` | `legal_context` |
| Orchestrator | `ValidationOrchestratorV2` | `ValidationOrchestrator` |
| Generator | `UnifiedDefinitionGenerator` | `DefinitionGenerator` |
| Service | `ModularValidationService` | `ValidationService` |

#### 🚫 VERBODEN Import Patterns
| In Directory | Verboden | Alternatief |
|--------------|----------|-------------|
| `src/services/` | `import streamlit` | Use `async_bridge` |
| `src/services/` | `from ui.*` | Use service layer |
| `src/services/` | `asyncio.run()` | Use `await` |
| `src/ui/` | `from repositories.*` | Use service facade |
| `src/ui/` | `ServiceContainer()` | Use `get_service_container()` |

Voor volledig overzicht: zie `~/.ai-agents/quality-gates.yaml`

- Veiligheid: geen secrets loggen; respecteer `vereistes*.txt` en netwerkbeperkingen.
- Stijl: volg bestaande structuur, import‑volgorde, en tooling (ruff/black waar geconfigureerd).
- Documentatie: update relevante docs bij functionele wijzigingen; plaats documenten op de juiste plek (zie `docs/CANONICAL_LOCATIONS.md`).
- Tests: maak/actualiseer tests bij nieuw gedrag; run gerichte suites waar mogelijk.

## No‑Assumptions / Strict Mode & Approval Ladder

### 🎯 Approval Ladder (Wanneer toestemming vragen)

#### ✅ AUTO-APPROVE (Geen bevestiging nodig)
| Operatie | Voorwaarde | Voorbeelden |
|----------|------------|-------------|
| Lezen/Zoeken | Altijd | `grep`, `rg`, `find`, `cat` |
| Tests draaien | < 10 files | `pytest tests/unit/` |
| Linting/Formatting | Bestaande files | `ruff check`, `black` |
| Documentatie | < 100 regels EN geen structuur | Typos, comments |
| Git status/diff | Altijd | `git status`, `git diff` |

#### 🔴 APPROVAL VEREIST (Moet vragen)
| Operatie | Trigger | Rationale |
|----------|---------|-----------|
| Code patches | > 100 regels OF > 5 files | Grote impact |
| Verwijderen | > 5 files OF kritieke paden | Data verlies risico |
| Netwerk calls | Externe APIs | Security/kosten |
| Schema wijzigingen | Database structuur | Breaking changes |
| Dependencies | pip install/remove | Supply chain |
| Git push/deploy | Productie impact | Permanente wijziging |

### Strict Mode Proces
- Doel: aannames elimineren door beslissingen expliciet te maken en goedkeuring te vragen op tussenstappen.
- Strict proces:
  - Start elk werk met `update_plan` + lijst "open vragen/unknowns"; pauzeer tot goedkeuring.
  - Plaats approval gates volgens ladder hierboven.
  - Houd een Decision Log bij: beslissingen (geen aannames), motivatie en akkoordmoment.
- Vereiste input (voorkomt aannames):
  - Doel & scope, Definition of Done, acceptatiecriteria.
  - API/contracten en wijzigingsruimte (wat wel/niet aanpassen).
  - Randvoorwaarden: security, performance, UX/i18n/a11y, foutafhandeling.
  - Voorbeelden/tegenvoorbeelden + testdata (happy/edge/error cases).
  - Bron van waarheid en conflictbeleid bij inconsistenties.
- Verificatie en bewijs:
  - Lever testopdracht/scenario’s; draai tests en toon resultaten (logs/diff/screenshot waar passend).
  - Per planstap een kort verificatieblok: wat geverifieerd, hoe, en met welk bewijs.
- Alternatieven en keuzes:
  - Geef per ontwerpbesluit 2–3 alternatieven met trade‑offs; vraag om keuze vóór implementatie.
- Scope‑bescherming:
  - Stel wijzigingsgrenzen: enkel paden X/Y, maximaal N regels diff, geen hernoem/format buiten scope.
  - Benoem welke feature flags/env‑vars gebruikt mogen worden.
- Templates (handig):
  - Opdrachtbrief: doel, scope, DoD, constraints, risico’s, testcases, SSoT.
  - Review‑gate: beslissingen ter goedkeuring, impact, rollback, testplan.
- Direct toepasbaar (in deze repo):
  - Zet “no‑assumptions” actief: agent stopt bij unknowns en vraagt eerst om akkoord.
  - Start met een unknowns‑lijst en laat die expliciet goedkeuren vóór implementatie.

### Slash Commands (toggles)
- Gebruik onderstaande slash‑commando’s in je chat met de agent:
  - `\/strict on` — activeer strict mode (geen aannames; agent pauzeert voor akkoord bij patches, tests, netwerk, DB‑reset).
  - `\/strict off` — deactiveer strict mode.
  - `\/approve` — geef akkoord voor de volgende geblokkeerde stap (patch/test/netwerk/DB). Optioneel: `\/approve all` voor alle huidige blokkers.
  - `\/deny` — weiger de volgende geblokkeerde stap; agent biedt alternatief of vraagt om herplanning.
  - `\/plan on` — dwing update_plan per stap (blijft al actief in strict mode).
  - `\/plan off` — planmodus loslaten (niet aanbevolen).
  - Optioneel scopes: `\/strict on patch,test` (alleen patches en tests onder gate). Scopes: `patch`, `test`, `network`, `db`, `all` (default `all`).

Opmerking: Dit is een gedragsconventie van de agent (soft‑gate). Voor harde system‑gates gebruik je de sandbox/approval policy van de CLI (bijv. on‑request).

### Backlog ID Uniciteit (Quality Gate)
- User stories (frontmatter `id: US-XXX`) zijn GLOBAAL uniek over de backlog (niet alleen per EPIC).
- Bugs (`id: BUG-XXX`/`CFR-BUG-XXX`) zijn GLOBAAL uniek.
- Voordat je een US/BUG aanmaakt of wijzigt: check duplicaten en kies het eerstvolgende vrije nummer.
- Bij ID‑duplicaten: corrigeer altijd door te renummeren en referenties bij te werken.

## Specifieke Agents (beschikbaar)

### code-reviewer
- Doel: Code‑reviews van commits/diffs, genereren van concrete feedback en verbeterpunten.
- Locatie: `~/.claude/agents/code-reviewer.md`
- Typische inzet: PR‑beoordeling, quick sanity checks, style & security hints.

### full-stack-developer
- Doel: Implementeren van gewenste wijzigingen/kleine features volgens bestaande projectstandaarden.
- Locatie: `~/.claude/agents/full-stack-developer.md`
- Typische inzet: Code‑aanpassingen met tests waar passend; houdt coverage ≥ bestaande baseline.

### debug-specialist
- Doel: Reproduceren en diagnosticeren van bugs, minimale fixes voorbereiden.
- Locatie: `~/.claude/agents/debug-specialist.md`
- Typische inzet: Repro‑stappen vastleggen, root cause aanwijzen, fix‑plan voorstellen.

### code-simplifier
- Doel: Kleine refactors en opschoning zonder gedragswijziging (DRY, leesbaarheid, complexiteit omlaag).
- Locatie: `~/.claude/agents/code-simplifier.md`
- Typische inzet: Extract method, naamgeving verbeteren, dode code verwijderen met tests groen.

## Verouderde Agents (niet geïnstalleerd)

### workflow-router
- **Doel**: Classificeert opdrachten en kiest de juiste workflow, orkestreert handoffs tussen agents volgens `workflows.yaml`.
- **Locatie**: `~/\.claude/agents/workflow-router.md`
- **Input**: Intent/beschrijving, betrokken bestanden/diff, labels/urgentie
- **Output**: Routeringsbesluit, handoff‑payload (work_unit_id, workflow, phase, gate_conditions, artifacts)
- **Commando’s**:
  - `ROUTE <beschrijving>`: automatische workflowselectie
  - `START-AS <workflow> <beschrijving>`: forceer specifieke workflow
  - `SUGGEST <beschrijving>`: suggesties met motivatie
- **Workflows**: Zie overzicht hieronder; bronconfig: `~/\.claude/agents/workflows/workflows.yaml`

### developer-implementer
- **Doel**: Architectuur (SA/TA) vertalen naar productie‑klare code, inclusief basis‑tests en integratie
- **Model**: opus
- **Color**: blue
- **Input**: Goedgekeurde SA/TA‑documentatie, user stories met acceptatiecriteria
- **Output**: Werkende modules/classes/functies met type hints en docstrings, basis unit‑ en integratietests
- **Core Verantwoordelijkheden**:
  1. Code Generatie: SA/TA naar modules volgens PEP8, SOLID principes
  2. Test Foundation: Min. 1 unit + 1 integration test per feature, AAA patroon
  3. Validatie: Linting (black/ruff), pytest runs, type checking
  4. Documentatie: Comprehensive docstrings (Google/NumPy format)
  5. Versie Control: Atomic commits met conventional format (feat:, fix:, etc.)
- **Werkstroom**: Analyze → Plan → Implement → Test → Validate → Document → Commit → Verify
- **Quality Standards**:
  - Elke publieke functie heeft docstring
  - Min. 80% test coverage per module
  - Geen lint warnings
  - Type hints verplicht
  - Geen hardcoded values
  - DRY principe
- **MCP Tools**: Filesystem, Pytest, Git, Docs/Markdown, HTTP (when available)

### business-analyst-justice
- **Doel**: Business/ketenwensen vertalen naar uitvoerbare artefacten binnen Nederlandse justitiedomein
- **Model**: opus
- **Color**: orange
- **Input**: Klantvraag/ketenbehoefte, betrokken organisaties (OM/DJI/Justid/Rechtspraak)
- **Output**: User stories met SMART acceptatiecriteria in `docs/backlog/stories/MASTER-EPICS-USER-STORIES.md`
- **Core Verantwoordelijkheden**:
  1. Intake & Analyse: US-XXX format, scope, domeinregels, constraints
  2. Domeinintegratie: ASTRA/NORA/GEMMA koppeling, terminologie consistentie
  3. Bridge Function: Coördinatie tussen alle agents
  4. Acceptatie Test Prep: Gegeven-Wanneer-Dan format (BDD)
  5. Validatie & Compliance: Reports in `docs/reports/<ID>.md`
- **Enhanced Capabilities**:
  - ASTRA Template Library
  - Chain Impact Analyzer
  - Vereisten Database Integration
  - Traceability Matrix Generator
- **Domain Expertise**: OM processen, DJI operaties, Justid standards, Rechtspraak procedures
- **Template**: Gebruikersverhaal (As/I want/So that), Acceptatiecriteria (BDD), Domeinregels, Implementatie Notities

### justice-architecture-designer
- **Doel**: EA/SA/TA‑documentatie opstellen voor justitieketen systemen conform overheidsstandaarden
- **Model**: opus
- **Color**: red
- **Input**: User story/vereistes, betrokken organisaties, compliance‑eisen
- **Output**: Formele architectuurartefacten in `docs/architectuur/`
- **Core Verantwoordelijkheden**:
  1. Enterprise Architecture (EA): Ketencontext, capabilities, stakeholders, ASTRA/NORA/GEMMA alignment
  2. Solution Architecture (SA): Component diagrammen, use cases, API contracts, datastromen
  3. Technical Architecture (TA): Framework keuzes, infrastructuur, NFRs, performance budgets
- **Werkstroom**: Vereisten Analysis → Layered Design (EA→SA→TA) → Standards Compliance → Documentation
- **Standards**: NORA principes, GEMMA referentie, ASTRA guidelines, AVG/GDPR, BIO
- **Documentation Format**:
  - Verplichte frontmatter (canonical, status, owner, last_verified, applies_to)
  - Executive Summary, Context & Scope, Architecture Decisions, Components/Design
  - Standards & Compliance, Risks & Mitigations, References
- **Decision Framework**: Beveiliging/privacy eerst, auditability, proven tech, 10+ jaar maintainability

### refactor-specialist
- **Doel**: Code‑opschoning en optimalisatie zonder gedragswijziging
- **Model**: opus
- **Color**: pink
- **Input**: Doelmodule(s), code smells, performance metrics
- **Output**: Kleine atomische refactors met rationale in `docs/refactor-log.md`
- **Core Verantwoordelijkheden**:
  1. Code Smell Detection: Functies >30 regels, duplicatie, hoge complexiteit, anti-patterns
  2. Micro-Refactoring: Extract Method, Introduce Interface, Replace Conditional, Rename, Move
  3. Module Organization: Domain-driven design, clean boundaries, logical grouping
  4. Testen Protocol: Test-first refactoring, snapshot testing waar nodig
  5. Documentation: Refactor-log met before/after, CHANGELOG updates
- **Operating Principles**:
  - Incremental progress
  - Behavior preservation
  - Test-first approach
  - Clear communication
  - Prestaties aware
  - Behoud domeinbegrippen
- **Quality Gates**: Tests groen, coverage gelijk/hoger, geen lint errors, docs updated

### code-reviewer-comprehensive
- **Doel**: Grondige, systematische code review van wijzigingen
- **Model**: opus
- **Color**: purple
- **Input**: Code diffs, user story context, test resultaten
- **Output**: Gestructureerde review met categorized findings
- **Review Checklist**:
  1. Correctness & Logic: Vereisten implementatie, edge cases, error handling
  2. Testen: Coverage adequaat, meaningful assertions, edge cases tested
  3. Beveiliging & Privacy: Geen secrets/PII, input validation, OWASP checks
  4. Prestaties: Efficiency, memory leaks, query optimization, complexity
  5. Style & Readability: Naming conventions, DRY, modularization, type hints
  6. Documentation: README updates, API docs, CHANGELOG, inline comments
  7. Domain Compliance: Check tegen BA domeinregels
- **Output Structure**:
  - Summary: Overview en assessment
  - Critical Issues (🔴): Blocking - must fix
  - Recommendations (🟡): Non-blocking improvements
  - Positive Observations (🟢): Good practices
  - Code Suggestions: Concrete patches
- **Final Verdict**: ✅ APPROVED | ⚠️ APPROVED WITH CONDITIONS | ❌ CHANGES REQUESTED
- **Communication**: Constructive, educational, concrete examples, pragmatic

### quality-assurance-tester
- **Doel**: Proactief testbeheer en quality assurance
- **Model**: opus
- **Color**: green
- **Input**: Nieuwe/gewijzigde code, BA acceptatiecriteria, coverage reports
- **Output**: Comprehensive test suites, coverage reports, failure analyses
- **Core Verantwoordelijkheden**:
  1. Test Creation: Unit/integration/property-based tests, AAA pattern, BA criteria validatie
  2. Test Execution: Pytest runs, failure categorization (KRITIEK/FLAKY/MINOR)
  3. Coverage Metrics: Min. 80% algemeen, 95%+ critical paths, reports in `docs/test-coverage.md`
  4. Continuous Maintenance: Sync tests met code changes, update/remove obsolete tests
- **Test Standards**:
  - Naming: `test_[what]_[condition]_[expected_result]`
  - Independence: Isolated tests
  - Clear assertions: One logical assertion per test
  - Fixtures voor common setup
  - Parametrization voor scenarios
  - Mock external afhankelijkheden
- **Quality Gates**: No merge zonder tests, coverage mag niet dalen, all tests green
- **MCP Integration**: Filesystem (tests/), Pytest, Git (test: prefix), Logging

### tdd-orchestrator
- **Doel**: Strikte TDD‑workflow orkestratie van TODO tot DONE
- **Model**: opus
- **Color**: yellow
- **Input**: BA‑goedgekeurde user story/bug met ID
- **Output**: Complete TDD trail met alle artifacts
- **Werkstroom States**:
  1. TODO → ANALYSIS (BA): Story in MASTER-EPICS-USER-STORIES.md
  2. DESIGN (Architect): EA/SA/TA docs, API contracts
  3. TEST-RED (Tester): Failing tests, commit `test(<ID>): ...`
  4. DEV-GREEN (Developer): Minimal implementation, commit `feat(<ID>): ...`
  5. REVIEW (Reviewer): Review report in docs/reviews/
  6. REFACTOR (Refactor): Micro-refactors, commit `refactor(<ID>): ...`
  7. TEST-CONFIRM: All tests green
  8. DONE/BLOCKED: Final status update
- **Critical Rule**: NO DEV without preceding RED tests
- **Required Artifacts per ID**:
  - Architecture docs (EA/SA/TA)
  - Unit & integration tests
  - Review reports
  - Refactor log entries
  - CHANGELOG entry
  - Status in MASTER-EPICS-USER-STORIES.md
- **Quality Gates**: Strict phase progression, coverage standards, complete docs
- **Status Format**: `ID: <ID> | State: <STATE> | Eigenaar: <AGENT> | Next: <ACTION> | Blockers: <ANY>`

### devops-pipeline-orchestrator
- **Doel**: CI/CD orkestreren vanaf branch/commit/PR tot release/deployment
- **Locatie**: `~/\.claude/agents/devops-pipeline-orchestrator.md`
- **Kern**: Branch management, semantische commits, PR lifecycle, CI‑validatie, release tagging, staged→prod deployment met rollback
- **Triggers**: DONE in TDD, handmatig verzoek, GitHub events (PR approval/merge)
- **Output**: Release tags, changelog/notes, deploymentstatus, post‑deploy checks
- **Commando’s**: `git`, `gh`, `pytest`, `ruff`, `black`, `make deploy-*`

### prompt-engineer
- **Doel**: Ondersteunende agent voor prompt‑optimalisatie, outputstructuur en token‑efficiëntie
- **Locatie**: `~/\.claude/agents/prompt-engineer.md`
- **Gebruik**: Als support in fases die baat hebben bij betere prompts (Analysis, Test‑Red, Dev‑Green, Review)
- **Output**: Verbeterde prompts/templates, duidelijkere outputformaten, lagere kans op hallucinaties

### doc-standards-guardian
- **Doel**: Bewaken en afdwingen van documentatiestandaarden
- **Model**: opus
- **Color**: cyan
- **Input**: Recente wijzigingen, agent outputs, project standards
- **Output**: Updated/generated docs, compliance reports, auto-fixes
- **Core Verantwoordelijkheden**:
  1. Document Presence: Ensure mandatory files exist (README, CLAUDE.md, INDEX.md, etc.)
  2. Standards Enforcement: Frontmatter vereistes, single source of truth, ID references
  3. Cross-Agent Sync: Update docs based on other agent outputs
  4. Automated Updates: CHANGELOG generation, API contracts, test coverage
  5. Navigation: Maintain docs/INDEX.md as central hub
  6. Validation: Audit compliance, check links, detect duplicates
- **Mandatory Files**:
  - README.md (root)
  - CLAUDE.md (root - voor Claude Code)
  - docs/INDEX.md
  - docs/CANONICAL_LOCATIONS.md
  - docs/DOCUMENTATION_POLICY.md
  - docs/backlog/stories/MASTER-EPICS-USER-STORIES.md
- **Kritieke Regels**:
  - ALTIJD: `/docs/archief/` voor archivering
  - NOOIT: Nieuwe archive directories
  - VERPLICHT: Check eerst of document bestaat
  - UPDATE: Bestaande docs, geen duplicaten
- **Quality Gates**: No multiple canonical:true, complete frontmatter, no broken links

## Gebruikspatronen (zonder workflow‑router)
- Geen centrale router/workflows in gebruik; kies handmatig de agent:
  - Review/diff/PR → `code-reviewer`
  - Bug reproduceren/diagnosticeren → `debug-specialist`
  - Kleine refactor/opschoning → `code-simplifier`
  - Implementatie/kleine feature → `full-stack-developer`

## Aanroepen en Namen
- Agent‑namen: gebruik exact: `code-reviewer`, `code-simplifier`, `debug-specialist`, `full-stack-developer`.
- Overdracht: leg kort de context, doel, scope, en "done"‑criteria vast voordat je de agent start.
- Artefacten: link naar relevante bestanden (code, config, docs) en verwachte outputlocaties.

## Kwaliteitschecklist (voor elke agent)
- Context verzameld en gelinkt?
- Scope en aannames expliciet?
- Output voldoet aan gevraagde vorm/locatie?
- Tests/validatie uitgevoerd waar passend?
- Documentatie bijgewerkt en indexen geüpdatet?

## Single Source of Truth (SSoT) Matrix

| Onderwerp | ENIGE Canonieke Bron | Doel |
|-----------|---------------------|------|
| **Backlog Structuur** | `docs/guidelines/CANONICAL_LOCATIONS.md` | EPIC→US→BUG hiërarchie |
| **Agent Gedrag** | `docs/guidelines/AGENTS.md` (dit document) | Approval gates, workflows |
| **Database Schema** | `src/database/schema.sql` | Tabellen, migraties |
| **Database Beleid** | `docs/guidelines/DATABASE_GUIDELINES.md` | Connection, pooling, backup |
| **Validatieregels** | `config/toetsregels/regels/*.json` | Regel definities & prioriteit |
| **Test Strategie** | `docs/guidelines/TDD_TO_DEPLOYMENT_WORKFLOW.md` | Coverage targets, TDD flow |
| **Documentatie Beleid** | `docs/guidelines/DOCUMENTATION_POLICY.md` | Formatting, structuur |
| **Import/Naming Rules** | `~/.ai-agents/quality-gates.yaml` | Forbidden patterns |
| **Approval Requirements** | `~/.ai-agents/UNIFIED_INSTRUCTIONS.md` | Approval ladder detail |
| **API Configuratie** | `config/rate_limit_config.py` | Timeouts, rate limits |
| **Architectuur** | `docs/architectuur/SOLUTION_ARCHITECTURE.md` | Service design, patterns |
| **CI/CD Gates** | `.github/workflows/epic-010-gates.yml` | Automated checks |

⚠️ **NOOIT dupliceren, ALTIJD verwijzen naar canonieke bron**

## Verwijzingen
- Canonical Locations: `docs/CANONICAL_LOCATIONS.md`
- Documentatie Index: `docs/INDEX.md`
- Architectuur: `docs/architectuur/`
- Testen: `docs/testing/`
- Projectkaders: `README.md`, `CLAUDE.md`
- Harmonisatie Instructies: `~/.ai-agents/UNIFIED_INSTRUCTIONS.md`
- Quality Gates: `~/.ai-agents/quality-gates.yaml`
- Preflight Script: `~/.ai-agents/preflight-checks.sh`
- Claude Code Agents (beschikbaar): `~/.claude/agents/` → `code-reviewer.md`, `code-simplifier.md`, `debug-specialist.md`, `full-stack-developer.md`
- Multi‑Agent gids: `docs/handleidingen/ontwikkelaars/codex-multi-agent-gebruik.md`
- Multi‑Agent Cheatsheet & Prompt Presets: `docs/snippets/CODEX_PROMPT_PRESETS.md`

---

Laatste update: 18-09-2025 (Harmonisatie update)
Voor vragen over agents, zie de individuele agent definities in `/Users/chrislehnen/.claude/agents/`.
