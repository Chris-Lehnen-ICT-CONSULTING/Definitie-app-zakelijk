# 📚 Definitie-app Documentatie Index

> **Status:** Documentatie Opgeschoond - 2025-09-04
> **Doel:** Centraal navigatiepunt voor actieve documentatie
> **Laatst bijgewerkt door:** Document Standards Guardian

## 📊 Documentatie Status

| Metric | Waarde | Status |
|--------|--------|--------|
| **Actieve documenten** | ~100 | ✅ Georganiseerd |
| **Archief documenten** | 200+ | ✅ In `/docs/archief/` |
| **Master Stories Doc** | 1 | ✅ Single source of truth |
| **Laatste opschoning** | 2025-09-04 | ✅ Actueel |

## 🚀 Active Development

- **[🔥 MASTER EPICS & USER STORIES](./stories/MASTER-EPICS-USER-STORIES.md) - SINGLE SOURCE OF TRUTH**
  - 86 User Stories met complete implementatie details
  - Vervangt ALLE individuele epic/story documenten

## 🎯 Essentiële Documenten

### 📝 Belangrijkste Documenten
- **[🔥 MASTER EPICS & USER STORIES](./stories/MASTER-EPICS-USER-STORIES.md)** - **SINGLE SOURCE OF TRUTH**
- **[🚫 DOCUMENT CREATION WORKFLOW](./DOCUMENT-CREATION-WORKFLOW.md)** - **VERPLICHT TE VOLGEN**
- **[📋 DOCUMENTATION POLICY](./DOCUMENTATION_POLICY.md)** - Documentatie beleid
- **[📁 CANONICAL LOCATIONS](./CANONICAL_LOCATIONS.md)** - Officiële document locaties

### Project Documenten
- [Product Requirements (PRD)](./prd.md) ✅
- [Project Brief](./brief.md) ✅
- [Refactor Log](./refactor-log.md) ✅
- [Migration Report](./MIGRATION_REPORT_2025-09-03.md) ✅
- [UAT Readiness Assessment](./requirements/uat/UAT_READINESS_ASSESSMENT_2025.md) ✅

### Architectuur
- [Huidige Architectuur Overzicht](./architectuur/CURRENT_ARCHITECTURE_OVERVIEW.md) ✅
- [Enterprise Architecture (EA)](./architectuur/EA.md) ✅
- [Solution Architecture (SA)](./architectuur/SA.md) ✅
- [Technical Architecture (TA)](./architectuur/TA.md) ✅
- [Solution Architecture Detail](./architectuur/SOLUTION_ARCHITECTURE.md) ✅
- [Architecture Decision Records](./architectuur/beslissingen/) 📁
  - [ADR-001: Monolithische structuur](./architectuur/beslissingen/ADR-001-monolithische-structuur.md)
  - [ADR-002: Features-first development](./architectuur/beslissingen/ADR-002-features-first-development.md)
  - [ADR-003: Legacy code als specificatie](./architectuur/beslissingen/ADR-003-legacy-code-als-specificatie.md)
  - [ADR-004: Incrementele migratie](./architectuur/beslissingen/ADR-004-incrementele-migratie-strategie.md)
  - [ADR-005: Service architecture evolution](./architectuur/beslissingen/ADR-005-service-architecture-evolution.md)
  - [ADR-006: Validation orchestrator V2](./architectuur/beslissingen/ADR-006-validation-orchestrator-v2.md)

### Technische Documentatie
- [Session-State Eliminatie Strategie](./architectuur/SESSION_STATE_ELIMINATION_STRATEGY.md) ✅
- [Toetsregels Module Guide](./technische-referentie/modules/TOETSREGELS_MODULE_GUIDE.md) ✅
- [Categorie Refactoring Plan](./architectuur/CATEGORY-REFACTORING-PLAN.md) ✅
- [Web Lookup Configuratie](./technisch/web_lookup_config.md) ✅
- [Module Dependencies](./technisch/module-afhankelijkheid-rapport.md) ✅
- [Validation Orchestrator V2](./architectuur/validation_orchestrator_v2.md) ✅
- [Modular Validation Service API](./api/modular-validation-service-api.md) ✅
- [Validation Result Migration Guide](./api/migration-guide-validation-result.md) ✅

### Prompt Refactoring & Analysis
- [Prompt Analysis](./architectuur/prompt-refactoring/PROMPT_ANALYSIS_DUPLICATES_CONTRADICTIONS.md) ✅
- [Prompt Generation Fixes](./architectuur/prompt-refactoring/PROMPT_GENERATION_FIXES.md) ✅
- [Prompt Refactoring Implementation](./architectuur/prompt-refactoring/PROMPT_REFACTORING_IMPLEMENTATION.md) ✅
- [Prompt System Runtime Analysis](./architectuur/prompt-refactoring/PROMPT_SYSTEM_RUNTIME_ANALYSIS.md) ✅

### Reviews & Code Analysis
- [Code Reviews](./reviews/) 📁
- [Code Analyse](./code-analyse/) 📁
- [Performance Analyses](./code-analyse/performance/) 📁

### Testing
- [Testing Strategy](./testing/README.md) ✅
- [Test Coverage Analysis](./TEST_COVERAGE_ANALYSIS_UAT.md) ✅
- [Critical Test Implementation Plan](./CRITICAL_TEST_IMPLEMENTATION_PLAN.md) ✅
- [Validation Orchestrator Testplan](./testing/validation_orchestrator_testplan.md) ✅

### Workflows & Handleidingen
- [Document Creation Workflow](./DOCUMENT-CREATION-WORKFLOW.md) ✅
- [Frontend Guide](./frontend/AI-FRONTEND-PROMPT-NL.md) ✅
- [Compliance](./compliance/) 📁
- [Handover Documenten](./handover/) 📁
- [Workflows](./workflows/) 📁

## 📂 Actieve Directory Structuur

```
docs/
├── 📁 stories/                    → MASTER-EPICS-USER-STORIES.md (single source of truth)
├── 📁 architectuur/               → Architectuur documenten
│   ├── beslissingen/             → ADRs (Architecture Decision Records)
│   ├── prompt-refactoring/       → Prompt systeem analyses
│   └── contracts/                → API contracts
├── 📁 technisch/                  → Technische documentatie
├── 📁 technische-referentie/      → Module referenties
│   └── modules/                  → Module guides
├── 📁 api/                        → API documentatie
├── 📁 requirements/               → Requirements en UAT
│   └── uat/                      → UAT documentatie
├── 📁 reviews/                    → Code reviews
├── 📁 testing/                    → Test documentatie
├── 📁 code-analyse/               → Code analyses
│   └── performance/              → Performance analyses
├── 📁 frontend/                   → Frontend guides
├── 📁 compliance/                 → Compliance documenten
├── 📁 handover/                   → Overdracht documenten
├── 📁 workflows/                  → Workflow documentatie
└── 📁 archief/                    → Gearchiveerde documenten (200+)
```

## 📌 Belangrijke Documenten Mapping

### Single Source of Truth Documenten
- **User Stories & Epics** → `stories/MASTER-EPICS-USER-STORIES.md` ✅
- **Architectuur Overzicht** → `architectuur/CURRENT_ARCHITECTURE_OVERVIEW.md` ✅
- **Solution Architecture** → `architectuur/SOLUTION_ARCHITECTURE.md` ✅
- **Toetsregels Guide** → `technische-referentie/modules/TOETSREGELS_MODULE_GUIDE.md` ✅
- **Session-State Eliminatie** → `architectuur/SESSION_STATE_ELIMINATION_STRATEGY.md` ✅
- **Categorie Refactoring** → `architectuur/CATEGORY-REFACTORING-PLAN.md` ✅
- **Validation Status** → `../validation-status.json` ✅

## 📋 Documentatie Beleid

- [Documentation Policy](./DOCUMENTATION_POLICY.md) - Labels, archivering en review regels
- [Canonical Locations](./CANONICAL_LOCATIONS.md) - Officiële document locaties
- [Document Creation Workflow](./DOCUMENT-CREATION-WORKFLOW.md) - Workflow voor nieuwe documenten

## 🔗 Externe Resources

- **CI/CD Pipeline**: GitHub Actions workflows voor tests en documentatie checks
- **Monitoring**: `validation-status.json` voor systeem health monitoring
- **API Documentatie**: Zie `/docs/api/` voor API contracts en migration guides

## ⚠️ Belangrijke Richtlijnen

### Voor nieuwe documenten:
1. **Check eerst** `CANONICAL_LOCATIONS.md` voor de juiste locatie
2. **Gebruik** `DOCUMENT-CREATION-WORKFLOW.md` voor het aanmaken proces
3. **Update** dit INDEX.md document wanneer je nieuwe documenten toevoegt

### Voor archivering:
1. **Verplaats** oude documenten naar `/docs/archief/`
2. **Behoud** de directory structuur in het archief
3. **Update** dit INDEX document om verwijzingen te verwijderen

---

*Laatste update: 2025-09-04 - Documentatie index opgeschoond*
*Door: Document Standards Guardian*
