---
aangemaakt: '08-09-2025'
applies_to: definitie-app@current
bijgewerkt: '08-09-2025'
canonical: true
last_verified: 05-09-2025
owner: architecture
prioriteit: medium
status: active
---



# Agents Richtlijnen

Dit document beschrijft hoe we gespecialiseerde agents inzetten binnen de Definitie‑app. Het doel is consistente kwaliteit, voorspelbaar gedrag en makkelijk samenwerken tussen mensen en agents.

## Claude Code Agents Locatie
- Primaire agent‑prompts: `~/\.claude/agents/` (lokaal bij jou)
- Router + workflows: `~/\.claude/agents/workflow-router.md` en `~/\.claude/agents/workflows/workflows.yaml`
- Aanroepen via de Task tool in Claude Code; gebruik exacte agent‑namen.

## Standaard Werkwijze
- Context eerst: lees relevante code, config en docs voordat je acties onderneemt.
- Plan klein: beschrijf in 3–6 korte stappen wat je gaat doen.
- Valideer: voer gerichte checks/tests uit op wat je veranderde.
- Logisch koppelen: verwijs naar bestaande documentatie en respecteer canonical locations.
- Minimaal ingrijpen: verander alleen wat nodig is, geen brede refactors zonder opdracht.

## Werkstroom Selectie
- Gebruik niet standaard de Full TDD workflow voor elke opdracht.
- Kies de lichtste passende workflow met de router of handmatig:
  - Analysis, Review Cycle, Documentation, Debug, Maintenance, Refactor Only, Hotfix, Spike, Full TDD.
- Documentatie: [Werkstroom Library](./WORKFLOW_LIBRARY.md) en [Werkstroom Routing](./WORKFLOW_ROUTING.md)
- Router (lokaal): `~/\.claude/agents/workflow-router.md` + config `~/\.claude/agents/workflows/workflows.yaml`
- Router‑commando’s: `ROUTE <beschrijving>`, `START-AS <workflow> <beschrijving>`, `SUGGEST <beschrijving>`

## Algemene Richtlijnen
- Veiligheid: geen secrets loggen; respecteer `vereistes*.txt` en netwerkbeperkingen.
- Stijl: volg bestaande structuur, import‑volgorde, en tooling (ruff/black waar geconfigureerd).
- Documentatie: update relevante docs bij functionele wijzigingen; plaats documenten op de juiste plek (zie `docs/CANONICAL_LOCATIONS.md`).
- Tests: maak/actualiseer tests bij nieuw gedrag; run gerichte suites waar mogelijk.

## Specifieke Agents

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

## Workflows Overzicht (Router)
- Configuratiebron: `~/\.claude/agents/workflows/workflows.yaml`
- Beschikbare workflows (kies de lichtste passende):
  - **analysis**: Onderzoek zonder wijzigingen → rapport + aanbevelingen
  - **review_cycle**: Code review met verdict → optionele refactor‑suggesties
  - **documentation**: Documentupdates/cleanup → frontmatter/canonical/links + verificatie
  - **debug**: Reproduce→Diagnose→Fix→Verify voor bugs
  - **maintenance**: Afhankelijkheden/configs/opschoon → validate light
  - **hotfix**: Versnelde kritieke fix met safety gates en rollback
  - **refactor_only**: Kwaliteitsverbetering zonder gedrag te wijzigen (tests groen)
  - **spike**: Technisch onderzoek/POC met bevindingen
  - **full_tdd**: Volledige TDD→Uitrol (alleen bij end‑to‑end levering)

### Routingregels (samenvatting)
- Intent “review/diff/PR” → review_cycle
- “analyse/understand/why” → analysis
- “docs/*.md” only → documentation
- “refactor/clean/optimize” zonder feature‑scope → refactor_only
- “hotfix/urgent/incident/p1/p2” → hotfix
- “research/spike/POC/experiment” → spike
- “implement/add/feature/build” → full_tdd
- Anders: default naar full_tdd; overrides toegestaan met `START-AS ...`

## Aanroepen en Namen
- Agent‑namen: gebruik exact de namen hierboven zodat tooling en documentatie overeenkomen.
- Overdracht: leg kort de context, doel, scope, en "done"‑criteria vast voordat je de agent start.
- Artefacten: link naar relevante bestanden (code, config, docs) en verwachte outputlocaties.

## Kwaliteitschecklist (voor elke agent)
- Context verzameld en gelinkt?
- Scope en aannames expliciet?
- Output voldoet aan gevraagde vorm/locatie?
- Tests/validatie uitgevoerd waar passend?
- Documentatie bijgewerkt en indexen geüpdatet?

## Verwijzingen
- Canonical Locations: `docs/CANONICAL_LOCATIONS.md`
- Documentatie Index: `docs/INDEX.md`
- Architectuur: `docs/architectuur/`
- Testen: `docs/testing/`
- Projectkaders: `README.md`, `CLAUDE.md`
- Claude Code Agents: `~/\.claude/agents/` (inclusief `workflow-router.md` en `workflows/workflows.yaml`)

---

Laatste update: 05-09-2025
Voor vragen over agents, zie de individuele agent definities in `/Users/chrislehnen/.claude/agents/`.
