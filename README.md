# DefinitieAgent 2.3 🚀

**Nederlandse AI-powered Definitie Generator voor Juridische en Overheidscontexten**

[![Version](https://img.shields.io/badge/version-2.3.0-blue.svg)](./CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=flat-square)](https://pre-commit.com/)
[![Tests](https://img.shields.io/badge/tests-919%20tests-yellow.svg)](./tests/)
[![Code Quality](https://img.shields.io/badge/ruff-960%20issues-orange.svg)](./docs/architectuur/)
[![Security](https://img.shields.io/badge/security-basic%20only-red.svg)](./docs/architectuur/)
[![License](https://img.shields.io/badge/license-Private-red.svg)]()

> **✅ Status Update (2025-09-12)**: US-064 Definition Edit Interface volledig geïmplementeerd met version history, auto-save en 100% test coverage
> **✅ Status Update (2025-09-11)**: EPIC-010 Context Flow 100% completed, CI/CD gates geïmplementeerd tegen legacy patterns

## 🧾 Snelstart Cheatsheet

```bash
# Start app met automatische env-mapping (aanbevolen)
bash scripts/run_app.sh

# Alternatief: direct via Streamlit (gebruik omgeving)
OPENAI_API_KEY="$OPENAI_API_KEY_PROD" streamlit run src/main.py

# Componentstatus genereren
make validation-status

# Tests draaien (quiet)
pytest -q
```

### 🔒 Codekwaliteit en Backlog‑discipline
- Geen TODO/FIXME/XXX/TBD/HACK/@todo/@fixme in code — alle werk loopt via backlog.
- Zie CONTRIBUTING.md voor richtlijnen. CI blokkeert PR's met TODO‑achtige comments.
- Lokale check: `pip install pre-commit && pre-commit install` of `bash scripts/ci/check_no_todo_markers.sh`.

### 🛡️ CI/CD Legacy Pattern Gates (NIEUW - Sept 2025)
- **GitHub Actions**: `.github/workflows/epic-010-gates.yml` blokkeert legacy patterns
- **Lokale check**: `bash scripts/check-legacy-patterns.sh` voor het pushen
- **7 patterns geblokkeerd**: generation_result imports, .best_iteration, string context, domein field, asyncio.run in services, streamlit in services
- **Status**: ✅ Actief sinds 11-09-2025 (EPIC-010 completed)

### 🔧 Wijzigingen P1 (2025‑09‑15)
- Services async‑only: sync wrappers in services verwijderd. UI gebruikt `src/ui/helpers/async_bridge.py` voor sync↔async bridging.
- PromptServiceV2: `build_prompt` (sync) verwijderd → gebruik `build_generation_prompt` (async) via UI‑bridge.
- ExportService: validation‑gate alleen in async pad (`export_definitie_async`). Sync pad faalt wanneer gate is ingeschakeld.
- Feature flags: `show_legacy_warning` verplaatst naar `ui/helpers/feature_toggle.py`; `config/feature_flags.py` is UI‑vrij.
- CategoryStateManager: nu pure helpers (geen `ui.session_state` import). UI schrijft zelf sessiestatus.
- Expert‑tab: bij “Vaststellen” kan je nu ketenpartners selecteren; worden persistent opgeslagen in DB en komen mee in export.
- Integratie: `datum_voorstel` wordt bij create gezet op `datetime.now(UTC)` (geen UI‑dependency meer).

Let op voor ontwikkelaars:
- Tests of code die `ServiceFactory.genereer_definitie(...)` of `PromptServiceV2.build_prompt(...)` aanroepen krijgen nu `NotImplementedError`. Migreer naar async paden + UI‑bridge.
- Services mogen geen `streamlit`/`ui.*` importeren. CI‑gates worden uitgebreid om dit te bewaken.

### 📚 Portal (Backlog & Docs)
- Open de centrale portal: `docs/portal/index.html` (dubbelklik; werkt offline).
- Zoek/filter/sorteer over REQ/EPIC/US/BUG en relevante documentatie.
- Documenten openen via een viewer met “Terug naar Portal”‑knop; Markdown wordt netjes gerenderd met portal‑stijl.
- Portaldata wordt automatisch gegenereerd vóór commit en in CI gevalideerd (drift‑guard).

### 🌐 Web Lookup Config (Epic 3)
- De applicatie gebruikt één configbestand: `config/web_lookup_defaults.yaml` (prompt‑augmentatie staat standaard aan).
- Optioneel kun je een eigen config gebruiken via `WEB_LOOKUP_CONFIG=/pad/naar/config.yaml`.
- Zie ook: [Web Lookup Configuratie](docs/technisch/web_lookup_config.md)

## 🎯 Overzicht

DefinitieAgent is een AI-applicatie voor het genereren van hoogwaardige Nederlandse definities volgens strenge overheidsstandaarden. Het systeem gebruikt GPT-4 met 45 kwaliteitsregels en biedt een modulaire architectuur voor uitbreidbaarheid.

### ✨ Kernfuncties

- 🤖 **AI Definitie Generatie** met GPT-4 (✅ 99% test coverage, temp=0 consistentie)
- ✏️ **Definition Edit Interface** ✅ NIEUW - Rich text editor met version history en auto-save
- 🧭 **Radio‑tabs navigatie** ✅ NIEUW – Sneller schakelen tussen tabs (zonder JS‑workarounds)
- 🔗 **Generator → Bewerk** ✅ Eén‑klik doorsturen met de juiste definitie
- ⭐ **Expert Prefill** ✅ Expert‑tab toont direct de laatst gegenereerde definitie (alleen lezen)
- 📋 **45 Kwaliteitsregels** voor validatie (Python modules in src/toetsregels/regels/)
- 🏗️ **Modulaire Architectuur** ValidationOrchestratorV2 + PromptServiceV2
- 🌐 **Web Lookup Epic 3** Backend werkt, prompt augmentatie geïntegreerd
- 📄 **Document Upload** voor kennisbasis uitbreiding
- ⚡ **Performance Issues** 6x service init, 45x regel laden, 7.250 prompt tokens
- 🖥️ **11 Streamlit UI Tabs** (inclusief nieuwe Edit tab)
- 🔒 **Security** ❌ Geen authentication/encryption (productie blocker)
- 📦 **Single Source of Truth** (voorstel) voor toetsregels = prompt instructies

## 🚀 Quick Start

```bash
# Clone repository
git clone <repository-url>
cd Definitie-app

# Setup environment
cp .env.example .env
# Edit .env met je OpenAI API key

# Install dependencies
pip install -r requirements.txt

# Voor development (optioneel)
pip install -r requirements-dev.txt

# Start applicatie
streamlit run src/main.py
```

### 🔑 Environment-variabelen (geen .env)
- De app leest `OPENAI_API_KEY` rechtstreeks uit de omgeving.
- In VS Code mappen we `OPENAI_API_KEY` vanuit `OPENAI_API_KEY_PROD` via de launch-config.
- In de terminal kun je hetzelfde doen met het script of een inline export:

```bash
# VS Code (launch): OPENAI_API_KEY <- ${env:OPENAI_API_KEY_PROD}

# Terminal (script):
bash scripts/run_app.sh

# Terminal (inline):
OPENAI_API_KEY="$OPENAI_API_KEY_PROD" streamlit run src/main.py
```

Let op: we laden geen `.env`; stel je sleutel in via je shell of VS Code.

## 🧭 Nieuwe UI‑navigatie

- De hoofdnavigatie gebruikt radio‑tabs (bovenaan). De geselecteerde tab wordt onthouden; schakelen is direct.
- Vanuit de Generator kun je via “📝 Bewerk” direct naar de Bewerk‑tab met de juiste definitie.
- De Expert‑tab toont (indien beschikbaar) bovenaan automatisch de laatst gegenereerde definitie met alle context (read‑only). 

## 🔒 Statusbescherming en bewerken

- Statuslabels in de UI: Concept (draft), In review (review), Vastgesteld (established), Gearchiveerd (archived).
- Een definitie met status “Vastgesteld” is read‑only in de Bewerk‑tab (velden disabled). 
- Wil je een vastgestelde definitie toch aanpassen? Zet in de Expert‑tab de status expliciet terug (actie “Maak bewerkbaar”, reden verplicht). Logging wordt vastgelegd in de geschiedenis.
- De zoekfunctie ondersteunt filteren op status (incl. “Vastgesteld”). 

## ✅ Vaststellen (Gate) — US‑160

De applicatie hanteert een validatie‑gate bij het vaststellen (Option B). De gate is centraal configureerbaar en wordt in de service afgedwongen; de UI toont de status en vereiste actie (eventuele override).

- Policyconfiguratie: `config/approval_gate.yaml` (env‑overlay via `APPROVAL_GATE_CONFIG_OVERLAY`).
- Default policy:
  - Hard: `require_org_context=true`, `require_jur_context=true`, `forbid_critical_issues=true`, `hard_min_score=0.75`.
  - Soft: `soft_min_score=0.65`, `allow_high_issues_with_override=true`, `missing_wettelijke_basis_soft=true`.
- DI: `GatePolicyService` met TTL‑cache (60s) beschikbaar via `ServiceContainer.gate_policy()`.
- Workflow: `DefinitionWorkflowService` voert gate‑check uit vóór overgang naar `ESTABLISHED` en vereist bij soft‑gate een override‑reden (`notes`).
- UI (Expert‑tab): toont indicator (groen=pass, oranje=override vereist, grijs=geblokkeerd) en handhaaft knoppenstate conform service‑uitkomst.

Belangrijk: status “ESTABLISHED” is leidend. Eventuele verwijzingen naar “APPROVED” worden uitgefaseerd (US‑174).

## 🧩 Contextbeleid (V2)

- Alle drie contexten zijn gelijkwaardig en verplicht in totaliteit: minimaal één van de drie moet gevuld zijn.
- Opslag is canoniek als lijsten (JSON arrays) voor:
  - Organisatorische context, Juridische context, Wettelijke basis.
- De UI toont uitsluitend de bij de definitie vastgelegde context; “—” indien leeg.
- De globale context (Context Selector) is voor generatie/validatie/web‑lookup en is geen fallback voor opslag.
- Zie ook: docs/architectuur/CONTEXT_MODEL_V2.md

## 📖 Documentatie Richtlijnen

### 🎯 Single Source of Truth Policy

Elk document moet frontmatter bevatten:
```yaml
---
canonical: true|false      # Is dit de officiële bron?
status: active|draft|archived
owner: architecture|product|validation|platform
last_verified: 2025-09-03  # Laatste controle datum
applies_to: definitie-app@v2
---
```

### 📂 Waar plaats je documenten?

Zie [CANONICAL_LOCATIONS.md](docs/guidelines/CANONICAL_LOCATIONS.md) voor de juiste locaties:

| Type Document | Locatie | Voorbeeld |
|--------------|---------|----------|
| **Architectuur** | `docs/architectuur/` | EA.md, SA.md |
| **Beslissingen** | `docs/architectuur/beslissingen/` | ADR-XXX-*.md |
| **Requirements** | `docs/` | REQUIREMENTS_AND_FEATURES_COMPLETE.md |
| **User Stories** | `docs/backlog/stories/` | epic-X-story-Y.md |
| **Technisch** | `docs/technisch/` | web_lookup_config.md |
| **Archief** | `docs/archief/` | Verouderde docs |

### ✏️ Bij wijzigingen

1. **Update `last_verified`** datum in frontmatter
2. **Check duplicaten** - gebruik bestaande docs i.p.v. nieuwe maken
3. **Link naar canoniek** - verwijs altijd naar de officiële bron
4. **Archiveer oude versies** - zet `status: archived` met verwijzing

Zie [DOCUMENTATION_POLICY.md](docs/guidelines/DOCUMENTATION_POLICY.md) voor complete richtlijnen.

## 📁 Project Structuur

```
definitie-app/
├── 📄 README.md              # Dit bestand
├── 📄 CLAUDE.md              # AI Assistant guidelines
├── 📄 CHANGELOG.md           # Version history
├── 📄 CLAUDE.md              # AI coding standards
├── 🔧 .env.example           # Environment template
│
├── 📁 src/                   # Source code
│   ├── services/             # Service layer met DI
│   ├── toetsregels/          # 45 validatie regels
│   ├── ui/                   # Streamlit UI componenten
│   └── main.py               # Main entry
│
├── 📁 docs/                  # Documentatie
│   ├── INDEX.md              # Docs index
│   ├── architectuur/         # EA/SA/TA docs
│   ├── requirements/         # Requirements
│   └── stories/              # User stories & epics
│
├── 📁 tests/                 # Test suites
└── 📁 data/                  # Database & uploads

### 🧰 Handige scripts
- `scripts/run_app.sh`: start de app en mapt automatisch `OPENAI_API_KEY` vanuit `OPENAI_API_KEY_PROD` indien nodig.
- `scripts/validation/validation-status-updater.py`: draait component-checks en schrijft status naar `reports/status/validation-status.json`.
- `make validation-status`: kortere alias voor de status-updater.
- `scripts/ai-agent-wrapper.py`: snelle AI‑kwaliteitsronde (probeert Ruff/Black/Pytest; auto‑fix waar mogelijk).
```

## 📊 Project Status (Updated 2025-09-03)

### ✅ Werkend & Geverifieerd (48% production ready)
- **Core Services**: DefinitionGenerator (99%), Validator (98%), Repository (100%)
- **Database**: Schema, migrations, UTF-8 encoding ✅
- **Toetsregels**: 45/46 modulaire regels werkend
- **Architecture**: Basis service layer geïmplementeerd
- **Codebase**: 68.834 regels productie code, 31.940 regels tests
- **Code Quality**: F821 undefined name errors (38→0) ✅ NIEUW
- **Import Hygiene**: I001 unsorted imports (46→0) ✅ NIEUW
- **Datetime Safety**: DTZ errors grotendeels opgelost ✅ NIEUW

### ❌ KRITIEKE BLOCKERS - Productie
- **Performance**: Services worden 6x geïnitialiseerd door Streamlit reruns (20s startup)
- **Prompt Inefficiëntie**: 7.250 tokens met duplicaties/tegenstrijdigheden (83% reductie mogelijk)
- **Authentication/Authorization**: Geen security layer (OWASP A07:2021)
- **Data Encryption**: SQLite databases unencrypted (OWASP A02:2021)
- **Web Lookup**: SRU Rechtspraak 404 errors, beperkte bronnen
- **Toetsregels**: 45x herladen per sessie, geen caching

### 🚧 Performance & Quality Issues
- **Database**: N+1 queries in voorbeelden system
- **Memory**: Cache system unlimited growth (memory leaks)
- **Test Infrastructure**: 26% test-to-code ratio, import failures
- **Code Quality**: 92 important issues, 175 suggestions (AI review)

### 📈 HERZIENE Roadmap (Post-Codex Review 2025-09-03)

Week 1: **🚨 QUICK WINS (80% impact, 20% effort)**
- Streamlit caching: @st.cache_resource voor ServiceContainer (6x→1x init)
- Prompt refactoring: 7.250→1.250 tokens implementatie (83% reductie)
- Toetsregels caching: @st.cache_data voor 45x→1x loading
- Config security: WEB_LOOKUP_CONFIG path validation

Week 2-3: **🏗️ TOETSREGEL-PROMPT MODULE PILOT**
- Implementeer ToetsregelModule base class
- Pilot met 5 regels (ARAI-01 t/m ARAI-05)
- Single Source of Truth: validate() + get_prompt_instruction()
- Test token reductie en consistency

Week 4-6: **📦 FULL MIGRATION & INTEGRATION**
- Migreer alle 45 toetsregels naar modules
- Context-aware prompt compositie
- Integratie met ModularValidationService
- A/B testing oude vs nieuwe prompt

Week 9-12: **🎯 PRODUCTION READINESS**
- Security hardening (OWASP compliance)
- Advanced monitoring & alerting
- Complete legacy elimination
- Enterprise features planning


## 🧪 Testing (Quinn Assessment)

**Status**: 919 tests, 46% test-to-code ratio

### ✅ Werkende Test Modules
```bash
# Core services (hoge coverage)
pytest tests/services/test_definition_generator.py    # 99% coverage
pytest tests/services/test_definition_validator.py    # 98% coverage
pytest tests/services/test_definition_repository.py   # 100% coverage

# Integration tests
pytest tests/integration/test_comprehensive_system.py
```

### ❌ Problematische Tests
```bash
# AI Toetser (5% coverage - 983 statements, 929 missed)
pytest tests/unit/test_ai_toetser.py                  # Import failures

# Config system (multiple failures)
pytest tests/unit/test_config_system.py               # NameError issues

# 6 disabled test files
# test_performance.py.disabled, test_cache_system.py.disabled, etc.
```

### 🎯 Test Strategy
- **Target Coverage**: 75% voor kritieke modules (nu: AI Toetser 5%)
- **Priority 1**: Fix import issues in test infrastructure
- **Priority 2**: Re-enable 6 disabled test bestanden
- **Continuous**: AI Code Review integration voor quality gates

## 📖 Documentatie


### Requirements & Features
- **[Complete Requirements & Features](docs/backlog/requirements/)** - Alle user stories, epics en feature status
  - 46 user stories gedefinieerd
  - 9 epics met acceptance criteria
  - Real-time status tracking

### Technische Architectuur
- **[Architectuur Overzicht](docs/architectuur/README.md)** - Index van alle architectuur documentatie
- **[Enterprise Architecture](docs/architectuur/ENTERPRISE_ARCHITECTURE.md)** - Business & strategie alignment
- **[Solution Architecture](docs/architectuur/SOLUTION_ARCHITECTURE.md)** - Technische implementatie details

### Quick Links
- 🎯 [Wat moet er nog gebeuren?](docs/backlog/epics/INDEX.md) - 60% features nog niet gestart
- 🔒 [Security Requirements](docs/backlog/EPIC-006/EPIC-006.md) - KRITIEK: 0% geïmplementeerd
- 🚀 [Roadmap](docs/backlog/epics/INDEX.md) - 4 fasen implementatie plan

### Overige Documentatie
- [User Stories](docs/backlog/stories/MASTER-EPICS-USER-STORIES.md) - Single source of truth voor alle epics en stories
- [Analyses](docs/architectuur/) - Technische documentatie

## 🤝 Contributing (Quinn Reviewed)

Zie de documentatie in `docs/guidelines/` voor development guidelines.

### 🚨 **CRITICAL FIXES - Immediate Impact**
- **Bare except clauses** elimineren (security) - 2 uur
- **E402 import errors** fixen main.py - 1 uur
- **Feature flags implementatie** - 4 uur
- **Test import issues** repareren - 3 uur

### ⚡ **HIGH PRIORITY - This Week**
- **Authentication basic setup** - 8 uur
- **WebLookupService debug** - 16 uur
- **Memory leak fixes** cache system - 4 uur
- **Database N+1 queries** optimalisatie - 6 uur

### 🎯 **MEDIUM PRIORITY - Next Weeks**
- GPT temperatuur configureerbaar maken - 2 uur
- Streamlit widget key generator - 2 uur
- Plain text export verbetering - 4 uur
- Help tooltips UI enhancement - 3 uur

### 📖 **Voor Nieuwe Contributors**
1. **Start met**: Critical fixes (immediate impact)
2. **Test je werk**: `python scripts/ai_code_reviewer.py`
3. **Check documentatie**: Zie [docs/INDEX.md](docs/INDEX.md) voor overzicht

## 🔧 Development (Updated by Quinn QA)

### 🧪 Quality-First Aanpak (POST-QUINN REVIEW)
- **Legacy refactoring = PRIORITEIT 1** (blokkeert alle verbeteringen)
- **Security & Performance** voor production readiness
- **Test-driven development** voor stability confidence
- **Code quality gates** via AI review automation

### 🎯 Development Priorities
1. **Foundation Stabiliteit**: Import fixes, bare except elimination
2. **Security Implementation**: Authentication, encryption, input validation
3. **Performance Optimization**: N+1 queries, memory leaks, caching
4. **Test Infrastructure**: Import issues, coverage improvement

### 📋 Coding Standards (Enhanced)
- **Nederlandse comments** voor business logica, **Engels** voor technical
- **Type hints VERPLICHT** voor alle nieuwe code
- **No bare except clauses** (security risk)
- **Import order**: Module-level imports bovenaan (E402 compliance)
- **Error handling**: Specific exceptions, proper logging
- **Test coverage**: Minimaal 60% voor nieuwe modules

### 🤖 AI Code Review Integration
- **Automated quality checks** via `scripts/ai_code_reviewer.py`
- **BMAD framework** voor development workflow
- **Quinn QA agent** voor architecture reviews

## 📁 Project Structuur (Voor Claude Code)

```
/
├── src/                    # Alleen broncode
├── tests/                  # Alleen test bestanden
├── docs/                   # Alle documentatie
│   ├── architectuur/       # Architectuur docs
│   ├── workflows/          # Workflow docs
│   ├── analyse/            # Analyse rapporten
│   ├── technisch/          # Technische documentatie
│   ├── reviews/            # Review rapporten
│   └── requirements/       # Requirements & features
├── scripts/                # Hulp scripts
│   ├── analyse/            # Analyse scripts
│   ├── analysis/           # Engelse legacy scripts
│   ├── hooks/              # Pre-commit hooks
│   └── maintenance/        # Onderhoud scripts
├── reports/                # Gegenereerde rapporten (git-ignored)
├── config/                 # Configuratie bestanden
├── data/                   # Database & data bestanden
├── logs/                   # Log bestanden
├── cache/                  # Tijdelijke cache bestanden
├── exports/                # Gegenereerde exports
└── static/                 # Statische assets
```

**Bestand Plaatsingsregels:**
- ❌ GEEN documenten in root (behalve README, LICENSE, etc.)
- ❌ GEEN test bestanden in root → gebruik `tests/`
- ❌ GEEN scripts in root → gebruik `scripts/`
- ✅ Alleen Nederlandse bestandsnamen (nieuwe bestanden)
- ✅ kleine-letters-met-streepjes naamgeving
- ✅ Rapporten naar `reports/` (automatisch genegeerd)
- ✅ Logs naar `logs/` directory
- **Pre-commit hooks** controleren automatisch bestand locaties

## 📞 Support

- Check [Quick Start](#-quick-start) sectie voor installatie
- Browse [Architecture](docs/architectuur/) voor technische details
- Zie [User Stories](docs/backlog/stories/MASTER-EPICS-USER-STORIES.md) voor features

## 🗄️ Database Richtlijnen (Nieuw)

- Enige actieve database: `data/definities.db`.
- Initialisatie/migratie via `src/database/schema.sql` en `python src/database/migrate_database.py`.
- Geen DB-bestanden in de root of elders; verwijder stray `*.db`, `*.db-shm`, `*.db-wal` buiten `data/`.
- Backups (optioneel) onder `data/backups/` (niet onder versiebeheer).
- Fallback-schema in code is noodpad; voorkeur is altijd laden vanaf `schema.sql`.
- Richtlijnen: zie `docs/guidelines/DATABASE_GUIDELINES.md`.

## 📜 License

Private project. All rights reserved.

---

**DefinitieAgent v2.3** - Features First Development
*"Legacy code is de specificatie"* 🚀

## 🧭 Docs Integrity & Health Report

- CI workflow: `.github/workflows/docs-integrity.yml`
  - Draait integriteitscheck op elke push/PR.
  - Faalt bij:
    - Dubbele US/BUG‑IDs (frontmatter `id:`) in de héle backlog
    - Broken links in canonical docs (archief geeft alleen warnings)
  - Genereert portal (docs/portal) en een health‑rapport.

- Lokaal draaien:
  - Integriteitscheck: `python3 scripts/docs/check_backlog_integrity.py`
  - Health report (JSON): `python3 scripts/docs/report_backlog_health.py --out docs/reports/backlog-health.json`
  - Portal genereren: `bash scripts/docs/run_portal_generator.sh`

- Rapport & gedrag:
  - JSON rapport: `docs/reports/backlog-health.json`
  - Canonical docs: strikte validatie (ID‑uniciteit + links)
  - Archief/non‑canonical: alleen waarschuwingen voor broken links
