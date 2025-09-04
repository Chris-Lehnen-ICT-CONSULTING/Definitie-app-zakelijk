# CHANGELOG

## [Unreleased]

### Added
- Component-specific AI configuration system via ConfigManager
- DevOps Pipeline Orchestrator agent for CI/CD automation
- Comprehensive documentation audit and compliance reporting
- AI_CONFIGURATION_GUIDE.md for centralized AI configuration documentation
- Context Flow Refactoring (CFR) architecture documentation suite
- Justice sector context in Enterprise/Solution/Technical Architecture
- ASTRA compliance assessment documentation

### Changed
- **BREAKING**: Complete migration to V2-only architecture - all V1 services removed
- Centralized all AI model configuration - removed all hardcoded defaults
- Updated CURRENT_ARCHITECTURE_OVERVIEW.md to reflect V2-only status
- Major architecture documentation overhaul with justice sector integration
- Consolidated user stories into single MASTER-EPICS-USER-STORIES.md

### Fixed
- CRITICAL SECURITY: Removed exposed API key from config
- Ruff configuration to ignore all archive directories
- Test compatibility with V2 orchestrator

### Removed
- All V1 service implementations (ValidationOrchestrator, AIService, PromptService)
- Legacy migration documentation (now in archive)
- Duplicate epic/story documents (consolidated to master document)

## [2.4.0] - 2025-09-04

### Added
- VS Code Run & Debug profiel dat `OPENAI_API_KEY` mapt vanuit `OPENAI_API_KEY_PROD`.
- Makefile targets: `dev`, `lint`, `test`, `status` voor snelle DX.
- README cheatsheet met 4 kerncommando's (run app, mapping, status, tests).

### Changed
- Runtime: geen `dotenv` meer; config leest direct uit environment variables.
- Environment: fallback naar `OPENAI_API_KEY_PROD` als `OPENAI_API_KEY` ontbreekt (dev‑vriendelijk, geen .env nodig).
- Pre-commit: Ruff/Black alleen op gewijzigde Python‑bestanden onder `src/` en `config/` via lokale hooks.
- Status-updater: verplaatst naar `scripts/validation/` en schrijft naar `reports/status/validation-status.json`.
- Documentatie: README en CONTRIBUTING bijgewerkt (run policy, env mapping, pre-commit policy, scripts/Makefile).
- .gitignore: archief/QA mappen genegeerd (`archive/`, `archived/`, `archief/`, `docs/archief/`, `qa.qaLocation/`).

### Removed
- macOS LaunchAgent setup script (niet meer nodig door fallback/mapping).

## [2.3.0] - 2025-07-17

### Added
- 📚 Complete documentatie reorganisatie en cleanup
- 📋 Geconsolideerde 6-weken Features First roadmap
- 🗂️ Gestructureerde backlog met 77+ items en quick wins
- 📝 SETUP.md quick start guide voor nieuwe developers
- 🤝 CONTRIBUTING.md met development guidelines
- 🔧 .env.example environment template
- 📁 Nieuwe documentatie structuur in docs/

### Changed
- 🏗️ Services consolidatie voltooid (3→1 UnifiedDefinitionService)
- 📊 23 roadmap documenten → 1 coherente ROADMAP.md
- 🗃️ 50+ losse backlog items → gestructureerde BACKLOG.md
- 🧹 Root directory cleanup - alleen essentiële files
- 📂 Test files georganiseerd in proper subfolders
- 🗑️ 3 archive folders verwijderd voor overzicht

### Fixed
- ✅ Import path chaos gestandaardiseerd
- ✅ Documentatie duplicatie opgelost
- ✅ .gitignore updated voor SQLite temp files

### Removed
- 🗑️ Verouderde roadmap versies (gearchiveerd)
- 🗑️ Duplicate archive folders
- 🗑️ Browser Test Checklist files
- 🗑️ .DS_Store files throughout project

## [2.2.0] - 2025-07-16

### Added
- 🚀 Context prohibition enforcement voor CON-01 compliance
- 📋 Modulaire toetsregels architectuur met 46 validators
- 🔄 Unified voorbeelden systeem met 4 generation modes (SYNC, ASYNC, CACHED, RESILIENT)
- 🗄️ Database persistence layer met duplicate detection
- 🎯 DefinitieAgent orchestrator voor iteratieve verbetering
- 🧪 Uitgebreide test suite (63 tests, 85% coverage)

### Fixed
- ✅ Async event loop conflict in unified_voorbeelden systeem
- ✅ String naar enum conversie bug in definitie_checker
- ✅ Context termen verschijnen niet meer in definities (CON-01)
- ✅ Test suite volledig werkend met backward-compatible database schema

### Changed
- 📦 Gerefactored naar modulaire architectuur
- 🔧 Verbeterde prompt building met expliciete context verboden
- 📊 Test coverage verhoogd van 14% naar 85%
- 🏗️ Repository pattern voor database operaties

### Technical Details
- Implementatie van CONTEXT_AFKORTINGEN mapping
- _genereer_context_verboden() methode toegevoegd
- _voeg_contextverbod_toe() voor term varianten detectie
- Async-safe execution met event loop detectie
- Maintenance scripts organisatie volgens best practices

## [2.1.0] - 2025-07-15

### Added
- Document upload functionaliteit (PDF, DOCX, TXT)
- Hybrid context enhancement
- Security middleware
- Performance optimalisaties

## [2.0.0] - 2025-07-14

### Added
- Complete architectuur redesign
- AI-powered definitie generatie
- Streamlit UI interface
- Basis test framework
