# 📚 Definitie-app Documentatie Index

> **Status:** Documentatie Audit Uitgevoerd - 2025-01-29
> **Doel:** Navigatie en reorganisatie planning voor 274 documenten
> **Actie:** Van chaos naar structuur - 45 essentiële docs identificeren

## 🚨 Huidige Situatie

| Metric | Waarde | Status |
|--------|--------|--------|
| **Totaal documenten** | 274 | ⚠️ Te veel |
| **Directories** | 17 | ⚠️ Te verspreid |
| **Archief directory** | 125 docs | 🔄 Moet zelf gearchiveerd |
| **Duplicaten/Overlap** | ~15+ | ❌ Verwarrend |

## 🚀 Active Development

- **[Story 3.1: Metadata First, Prompt Second](./stories/story-3.1-implementation-status.md)** 🔄 **IN PROGRESS**
  - Status: Implementing legacy wrapper removal
  - Target: Sources zichtbaar in UI preview
  - ETA: 4-6 uur

## 🎯 Quick Links - Essentiële Documenten

### Product & Requirements
- [Product Requirements (PRD)](./prd.md) ✅
- [Project Brief](./brief.md) ✅
- [Requirements Compleet](./requirements/REQUIREMENTS_AND_FEATURES_COMPLETE.md) ✅ **[VERPLAATST]**
- [User Stories](./stories/) 📁
  - **[Epic 3 User Stories](./stories/epic-3-user-stories.md)** 🆕 ✅ **UAT PRIORITY**
  - **[Epic 3 Implementation Tracker](./stories/epic-3-implementation-tracker.md)** 🆕 📊 **DAILY UPDATE**
  - **[Story 3.1 Implementation Status](./stories/story-3.1-implementation-status.md)** 🔄 **ACTIVE**
  - [Story 3.1 Design](./stories/story-3.1-metadata-first-prompt-second.md) ✅
  - [Epic 3 Web Lookup](./stories/epic-3-web-lookup-modernization.md) 🔄
- **[UAT Readiness Assessment 2025](./requirements/uat/UAT_READINESS_ASSESSMENT_2025.md)** 🆕 ✅ (canonical)

### Architectuur
- [Huidige Architectuur Overzicht](./architectuur/CURRENT_ARCHITECTURE_OVERVIEW.md) ✅ (canonical) **[VERPLAATST]**
- [Enterprise Architecture (EA)](./architectuur/EA.md) ✅ **[VERPLAATST]**
- [Solution Architecture (SA)](./architectuur/SA.md) ✅ **[VERPLAATST]**
- [Technical Architecture (TA)](./architectuur/TA.md) ✅ **[VERPLAATST]**
- [Solution Architecture](./architectuur/SOLUTION_ARCHITECTURE.md) ✅ (canonical)
- [Modernization Plan 2025](./architectuur/MODERNIZATION_PLAN_2025.md) ✅ **[VERPLAATST]**
- [Services Dependency Analysis](./architectuur/SERVICES_DEPENDENCY_ANALYSIS.md) ✅ **[VERPLAATST]**
- [Services Dependency Graph](./architectuur/SERVICES_DEPENDENCY_GRAPH.md) ✅ **[VERPLAATST]**
- [V1 Elimination Rollback](./architectuur/V1_ELIMINATION_ROLLBACK.md) ✅ **[VERPLAATST]**
- [True Modular System Deployment](./architectuur/TRUE_MODULAR_SYSTEM_DEPLOYMENT.md) ✅ **[VERPLAATST]**
- [Architecture Decision Records](./architectuur/beslissingen/) 📁
  - [ADR-001: Monolithische structuur](./architectuur/beslissingen/ADR-001-monolithische-structuur.md)
  - [ADR-002: Features-first development](./architectuur/beslissingen/ADR-002-features-first-development.md)
  - [ADR-003: Legacy code als specificatie](./architectuur/beslissingen/ADR-003-legacy-code-als-specificatie.md)
  - [ADR-004: Incrementele migratie](./architectuur/beslissingen/ADR-004-incrementele-migratie-strategie.md)
  - [ADR-005: Service architecture evolution](./architectuur/beslissingen/ADR-005-service-architecture-evolution.md)

### Technische Documentatie
- [Session-State Eliminatie Strategie](./architectuur/SESSION_STATE_ELIMINATION_STRATEGY.md) ✅ (canonical)
- [Toetsregels Module Guide](./technische-referentie/modules/TOETSREGELS_MODULE_GUIDE.md) ✅ (canonical) **[VERPLAATST]**
- [Categorie Refactoring Plan](./architectuur/CATEGORY-REFACTORING-PLAN.md) ✅ (canonical)
- [Technical Analysis Prompt Generation](./technisch/TECHNICAL_ANALYSIS_PROMPT_GENERATION.md) ✅ **[VERPLAATST]**
- [Technische Referentie](./technisch/) 📁
- [Technische-Referentie Modules](./technische-referentie/) 📁 **[NIEUW]**
- [Web Lookup Configuratie](./technisch/web_lookup_config.md) ✅ (canonical)
- [Module Documentatie](./modules/) 📁

### Prompt Refactoring & Analysis
- [Prompt Analysis Duplicates & Contradictions](./architectuur/prompt-refactoring/PROMPT_ANALYSIS_DUPLICATES_CONTRADICTIONS.md) ✅ **[VERPLAATST]**
- [Prompt Refactoring Comparison](./architectuur/prompt-refactoring/PROMPT_REFACTORING_COMPARISON.md) ✅ **[VERPLAATST]**
- [Prompt Refactoring Implementation](./architectuur/prompt-refactoring/PROMPT_REFACTORING_IMPLEMENTATION.md) ✅ **[VERPLAATST]**
- [Prompt Refactoring Summary](./architectuur/prompt-refactoring/PROMPT_REFACTORING_SUMMARY.md) ✅ **[VERPLAATST]**
- [Prompt Generation Fixes](./architectuur/prompt-refactoring/PROMPT_GENERATION_FIXES.md) ✅ **[VERPLAATST]**
- [Prompt System Runtime Analysis](./architectuur/prompt-refactoring/PROMPT_SYSTEM_RUNTIME_ANALYSIS.md) ✅ **[VERPLAATST]**

### Reviews & Code Analysis
- [Codex Reviews Executive Summary](./reviews/CODEX_REVIEWS_EXECUTIVE_SUMMARY.md) ✅ **[VERPLAATST]**
- [Security and Feedback Analysis](./reviews/SECURITY_AND_FEEDBACK_ANALYSIS.md) ✅ **[VERPLAATST]**
- [Full Code Review 2025-08-28](./reviews/2025-08-28_full_code_review/) 📁
- **[Technical Debt Assessment 2025](./code-analyse/quality/TECHNICAL_DEBT_ASSESSMENT_2025.md)** 🆕 ✅ (canonical)

### Workflows & Handleidingen
- [Actieve Workflows](./workflows/) 📁
- [Frontend Guide](./frontend/AI-FRONTEND-PROMPT-NL.md) ✅
- [Compliance](./compliance/) 📁
- [Handover Story 2.4](./handover/HANDOVER_STORY_2.4.md) ✅ **[VERPLAATST]**
- [Handover Web Lookup Epic 3](./handover/HANDOVER_WEB_LOOKUP_EPIC3.md) ✅ **[VERPLAATST]**

## 📂 Huidige Directory Structuur

```
docs/
├── 📁 archief/          (125 docs) ⚠️ Ironisch - moet zelf gearchiveerd
├── 📁 architectuur/     (79 docs)  🔄 90% kan gearchiveerd
├── 📁 architecture/     (12 docs)  ❓ Duplicaat van architectuur?
├── 📁 analyse/          (3 docs)   🗄️ Verouderd
├── 📁 analysis/         (0 docs)   ❓ Waarom leeg?
├── 📁 api/              (0 docs)   ❓ Waarom leeg?
├── 📁 compliance/       (1 doc)    ✅ Behouden
├── 📁 evaluations/      (1 doc)    🗄️ Oud
├── 📁 frontend/         (1 doc)    ✅ Behouden
├── 📁 guides/           (0 docs)   ❓ Waarom leeg?
├── 📁 meeting-notes/    (0 docs)   ❓ Waarom leeg?
├── 📁 modules/          (9 docs)   🔄 Consolideren
├── 📁 requirements/     (0 docs)   ❓ Waarom leeg?
├── 📁 reviews/          (8 docs)   🗄️ Afgerond
├── 📁 stories/          (1 doc)    ✅ Actief
├── 📁 technisch/        (4 docs)   ✅ Behouden
├── 📁 workflows/        (10 docs)  🔄 3 actief, 7 archief
└── 📄 Root bestanden    (25 docs)  🔄 Mix essentieel/archief
```

## 🎯 Voorgestelde Nieuwe Structuur

```
docs/
├── 📌 ESSENTIEEL/           (45 docs totaal)
│   ├── product/            # PRD, requirements, stories
│   ├── architectuur/       # ADRs, actuele architectuur
│   ├── handleidingen/      # Gebruiker & developer docs
│   └── projectdocs/        # Planning, compliance
│
├── 🗄️ ARCHIEF/             (229 docs)
│   └── 2025-Q1/           # Huidige archivering
│
└── 📋 INDEX.md            # Dit document
```

## 🔍 Gevonden Problemen

### 🔴 Kritiek
1. **Reorganisatie Recursie**: 6+ verschillende reorganisatie plannen gevonden!
2. **Duplicaat Directories**: ✅ OPGELOST - `architectuur` is canonical, `architecture` bevat technische specs
3. **Lege Directories**: ✅ OPGELOST - `docs/reviews` verwijderd, archief dirs behouden voor structuur
4. **Geen Scheiding**: Actuele en verouderde docs door elkaar

### 🟡 Belangrijke Observaties
- `docs/archief/` bevat 125 docs die al gearchiveerd zijn
- Meerdere LEGACY_, DEPRECATED_, OLD_ prefixes overal
- Veel "REORGANIZATION" documenten (ironisch!)
- Meeting notes en evaluaties zijn verouderd
- **Opgelost:** `architecture` en `architectuur` directories geconsolideerd

## 📊 Impact van Reorganisatie

| Aspect | Voor | Na | Verbetering |
|--------|------|-----|-------------|
| **Vindbaarheid** | 😵 Chaos | ✅ Gestructureerd | 100% |
| **Essentiële docs** | Verspreid | Gecentraliseerd | 45 docs |
| **Archief** | Overal | Één locatie | 229 docs |
| **Duplicaten** | 15+ | 0 | 100% |
| **Lege dirs** | 5 | 0 | 100% |

## 📌 Canonical Mapping (Single Source of Truth)

- Architectuur Overzicht → `CURRENT_ARCHITECTURE_OVERVIEW.md` (owner: architecture)
- Solution Architecture Detail → `architectuur/SOLUTION_ARCHITECTURE.md` (owner: architecture)
- Validatie Orchestrator Story → `stories/epic-2-story-2.4-integration-migration.md` (owner: validation)
- Toetsregels/Validators → `TOETSREGELS_MODULE_GUIDE.md` (owner: validation)
- Session-State Eliminatie → `architectuur/SESSION_STATE_ELIMINATION_STRATEGY.md` (owner: platform)
- Categorie Refactor → `architectuur/CATEGORY-REFACTORING-PLAN.md` (owner: domain)
- Health/Status (canonical) → `../validation-status.json`

## 🧰 Tasks & Checklists

- Backend Refactor Checklist → `tasks/backend-refactor-checklist.md`

Zie ook: `DOCUMENTATION_POLICY.md` voor labels, archivering en reviewregels.

## 🚀 Volgende Stappen (PR’s)

1) Canonicaliseren & labelen (deze stap) – frontmatter + INDEX + policy.
2) Consolidatie & redirects – duplicaten archiveren en samenvatten in canonieke docs.
3) CI‑bewaking – doc‑lint (canonical duplicaten, stalen verificatie, linkcheck).

## 📝 Notities

- **Niets wordt verwijderd**: Alles wordt bewaard in ARCHIEF/
- **Reversibel**: Script kan teruggedraaid worden
- **Gefaseerd**: Stap voor stap uitvoeren met controle

---

*Laatste update: 2025-09-03 - Documentatie reorganisatie uitgevoerd*
*Door: Documentation Standards Guardian*
