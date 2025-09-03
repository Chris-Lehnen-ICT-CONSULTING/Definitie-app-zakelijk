# DefinitieAgent 2.3 🚀

**Nederlandse AI-powered Definitie Generator voor Juridische en Overheidscontexten**

[![Version](https://img.shields.io/badge/version-2.3.0-blue.svg)](./CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=flat-square)](https://pre-commit.com/)
[![Tests](https://img.shields.io/badge/tests-522%20tests-yellow.svg)](./tests/)
[![Code Quality](https://img.shields.io/badge/ruff-799%20issues-orange.svg)](./docs/architectuur/)
[![Security](https://img.shields.io/badge/security-basic%20only-red.svg)](./docs/architectuur/)
[![License](https://img.shields.io/badge/license-Private-red.svg)]()

> **🧪 Status Update (2025-08-19)**: F821 undefined name errors opgelost, imports gesorteerd, 84 kritieke errors gefixt

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

### 🌐 Web Lookup Config (Epic 3)
- De applicatie gebruikt één configbestand: `config/web_lookup_defaults.yaml` (prompt‑augmentatie staat standaard aan).
- Optioneel kun je een eigen config gebruiken via `WEB_LOOKUP_CONFIG=/pad/naar/config.yaml`.
- Zie ook: [Web Lookup Configuratie](docs/technisch/web_lookup_config.md)

## 🎯 Overzicht

DefinitieAgent is een AI-applicatie voor het genereren van hoogwaardige Nederlandse definities volgens strenge overheidsstandaarden. Het systeem gebruikt GPT-4 met 46 kwaliteitsregels en biedt een modulaire architectuur voor uitbreidbaarheid.

### ✨ Kernfuncties

- 🤖 **AI Definitie Generatie** met GPT-4 (✅ 99% test coverage, temp=0 consistentie)
- 📋 **45/46 Kwaliteitsregels** voor validatie (INT-05 ontbreekt)
- 🏗️ **Hybride Architectuur** UnifiedDefinitionService + moderne services
- 🌐 **Web Lookup** ⚠️ DEELS WERKEND - Backend werkt (28 tests), UI tab niet geïntegreerd
- 📄 **Document Upload** voor kennisbasis uitbreiding
- ⚡ **Smart Caching** ⚠️ memory leaks geïdentificeerd
- 🖥️ **10 Streamlit UI Tabs** (alle importeren succesvol)
- 🔒 **Security** ❌ Geen authentication/encryption (productie blocker)
- 🧪 **AI Code Review** ✅ Geautomatiseerd met 235 issues geïdentificeerd

## 🚀 Quick Start

Zie [Quick Start Guide](docs/setup/quick-start.md) voor gedetailleerde installatie instructies.

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

## 📁 Project Structuur

```
definitie-app/
├── 📄 README.md              # Dit bestand
├── 📄 SETUP.md               # Quick start guide
├── 📄 CONTRIBUTING.md        # Development guidelines
├── 📄 CHANGELOG.md           # Version history
├── 📄 CLAUDE.md              # AI coding standards
├── 🔧 .env.example           # Environment template
│
├── 📁 src/                   # Source code
│   ├── services/             # UnifiedDefinitionService
│   ├── ai_toetsing/          # 46 validators
│   ├── tabs/                 # 10 UI tabs
│   └── main.py               # Main entry
│
├── 📁 docs/                  # Documentatie
│   ├── README.md             # Docs index
│   ├── brownfield-architecture.md
│   ├── requirements/         # Roadmap & backlog
│   └── analysis/             # Technische analyses
│
├── 📁 tests/                 # Test suites (87% broken)
└── 📁 data/                  # Database & uploads

### 🧰 Handige scripts
- `scripts/run_app.sh`: start de app en mapt automatisch `OPENAI_API_KEY` vanuit `OPENAI_API_KEY_PROD` indien nodig.
- `scripts/validation/validation-status-updater.py`: draait component-checks en schrijft status naar `reports/status/validation-status.json`.
- `make validation-status`: kortere alias voor de status-updater.
```

## 📊 Project Status (Updated 2025-08-19)

### ✅ Werkend & Geverifieerd (48% production ready)
- **Core Services**: DefinitionGenerator (99%), Validator (98%), Repository (100%)
- **Database**: Schema, migrations, UTF-8 encoding ✅
- **Toetsregels**: 45/46 modulaire regels werkend
- **Architecture**: Basis service layer geïmplementeerd
- **Codebase**: 59.783 regels productie code, 15.526 regels tests
- **Code Quality**: F821 undefined name errors (38→0) ✅ NIEUW
- **Import Hygiene**: I001 unsorted imports (46→0) ✅ NIEUW
- **Datetime Safety**: DTZ errors grotendeels opgelost ✅ NIEUW

### ❌ KRITIEKE BLOCKERS - Productie
- **Authentication/Authorization**: Geen security layer (OWASP A07:2021)
- **Data Encryption**: SQLite databases unencrypted (OWASP A02:2021)
- **Web Lookup UI**: Tab toont geen resultaten - integratie ontbreekt
- **Legacy Refactoring**: UnifiedDefinitionService (698 regels) nog niet opgesplitst
- **Import Architecture**: E402 errors in main.py en legacy modules
- **Error Handling**: 8 bare except clauses maskeren critical errors

### 🚧 Performance & Quality Issues
- **Database**: N+1 queries in voorbeelden system
- **Memory**: Cache system unlimited growth (memory leaks)
- **Test Infrastructure**: 26% test-to-code ratio, import failures
- **Code Quality**: 92 important issues, 175 suggestions (AI review)

### 📈 HERZIENE Roadmap (Post-Quinn Review)

Week 1-2: **🚨 FOUNDATION STABILITEIT (PRIO 1)**
- Legacy refactoring: UnifiedDefinitionService échte split
- Import architecture fix: E402 errors main.py/legacy
- Eliminate 8 bare except clauses (security risk)
- Feature flags implementatie (nu gedocumenteerd maar bestaat niet)

Week 3-4: **🔒 SECURITY & TESTING**
- Authentication/authorization systeem implementeren
- Database encryption voor sensitive data
- Test infrastructure fix (import issues)
- WebLookupService complete rebuild starten

Week 5-8: **⚡ PERFORMANCE & QUALITY**
- Database N+1 queries optimalisatie
- Memory leak fixes in cache system
- Code quality: 92 important issues → <10
- Performance monitoring implementatie

Week 9-12: **🎯 PRODUCTION READINESS**
- Security hardening (OWASP compliance)
- Advanced monitoring & alerting
- Complete legacy elimination
- Enterprise features planning

Zie [docs/requirements/ROADMAP.md](docs/requirements/ROADMAP.md) voor details.

## 🧪 Testing (Quinn Assessment)

**Status**: 522 tests in 62 bestanden, 26% test-to-code ratio

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

> **📋 TODO**: Documentatie reorganisatie plan uitvoeren - zie [DOCUMENTATIE_REORGANISATIE_PLAN.md](DOCUMENTATIE_REORGANISATIE_PLAN.md)

### Requirements & Features
- **[Complete Requirements & Features](docs/REQUIREMENTS_AND_FEATURES_COMPLETE.md)** - Alle user stories, epics en feature status
  - 87 features gedefinieerd
  - 9 epics met acceptance criteria
  - Real-time status tracking

### Technische Architectuur
- **[Architectuur Overzicht](docs/architectuur/README.md)** - Index van alle architectuur documentatie
- **[Enterprise Architecture](docs/architectuur/ENTERPRISE_ARCHITECTURE.md)** - Business & strategie alignment
- **[Solution Architecture](docs/architectuur/SOLUTION_ARCHITECTURE.md)** - Technische implementatie details
- **[Product Delivery Tracker](docs/architectuur/PRODUCT_DELIVERY_TRACKER.md)** - Sprint voortgang & metrics
- **[Legacy Migratie](docs/LEGACY_CODE_MIGRATION_ROADMAP.md)** - 10-weken migratie roadmap

### Quick Links
- 🎯 [Wat moet er nog gebeuren?](docs/REQUIREMENTS_AND_FEATURES_COMPLETE.md#epic-overview) - 60% features nog niet gestart
- 🔒 [Security Requirements](docs/REQUIREMENTS_AND_FEATURES_COMPLETE.md#epic-6-security--auth) - KRITIEK: 0% geïmplementeerd
- 🚀 [Roadmap](docs/REQUIREMENTS_AND_FEATURES_COMPLETE.md#implementation-roadmap) - 4 fasen implementatie plan

### Overige Documentatie
- [Roadmap](docs/requirements/ROADMAP.md) - 6-weken development plan
- [Backlog](docs/BACKLOG.md) - 77+ items met quick wins
- [Analyses](docs/analysis/) - Technische documentatie

## 🤝 Contributing (Quinn Reviewed)

Zie [CONTRIBUTING.md](CONTRIBUTING.md) voor development guidelines.

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
1. **Lees eerst**: Quinn QA review in [MASTER-TODO.md](MASTER-TODO.md)
2. **Start met**: Critical fixes (immediate impact)
3. **Test je werk**: `python scripts/ai_code_reviewer.py`
4. **Ask questions**: Check [docs/development/](docs/development/) guides

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
- Zie [docs/development/code-review-workflow.md](docs/development/code-review-workflow.md)

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

- Check [Setup Guide](SETUP.md) voor installatie
- Zie [Roadmap](docs/requirements/ROADMAP.md) voor planning
- Browse [Architecture](docs/architectuur/README.md) voor technische details
- Review [Backlog](docs/BACKLOG.md) voor open taken

## 📜 License

Private project. All rights reserved.

---

**DefinitieAgent v2.3** - Features First Development
*"Legacy code is de specificatie"* 🚀
