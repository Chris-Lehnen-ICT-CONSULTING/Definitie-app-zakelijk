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

## 🎯 Quick Links - Essentiële Documenten

### Product & Requirements
- [Product Requirements (PRD)](./prd.md) ✅
- [Project Brief](./brief.md) ✅
- [Requirements Compleet](./REQUIREMENTS_AND_FEATURES_COMPLETE.md) ✅
- [User Stories](./stories/) 📁

### Architectuur
- [Huidige Architectuur Overzicht](./CURRENT_ARCHITECTURE_OVERVIEW.md) ✅ (canonical)
- [Solution Architecture](./architectuur/SOLUTION_ARCHITECTURE.md) ✅ (canonical)
- [Architecture Decision Records](./architectuur/beslissingen/) 📁
  - [ADR-001: Monolithische structuur](./architectuur/beslissingen/ADR-001-monolithische-structuur.md)
  - [ADR-002: Features-first development](./architectuur/beslissingen/ADR-002-features-first-development.md)
  - [ADR-003: Legacy code als specificatie](./architectuur/beslissingen/ADR-003-legacy-code-als-specificatie.md)
  - [ADR-004: Incrementele migratie](./architectuur/beslissingen/ADR-004-incrementele-migratie-strategie.md)
  - [ADR-005: Service architecture evolution](./architectuur/beslissingen/ADR-005-service-architecture-evolution.md)

### Technische Documentatie
- [Services Dependency Analysis](./SERVICES_DEPENDENCY_ANALYSIS.md) ✅
- [Session-State Eliminatie Strategie](./architectuur/SESSION_STATE_ELIMINATION_STRATEGY.md) ✅ (canonical)
- [Toetsregels Module Guide](./TOETSREGELS_MODULE_GUIDE.md) ✅ (canonical)
- [Categorie Refactoring Plan](./architectuur/CATEGORY-REFACTORING-PLAN.md) ✅ (canonical)
- [Technische Referentie](./technisch/) 📁
- [Web Lookup Configuratie](./technisch/web_lookup_config.md) ✅ (canonical)
- [Module Documentatie](./modules/) 📁

### Workflows & Handleidingen
- [Actieve Workflows](./workflows/) 📁
- [Frontend Guide](./frontend/AI-FRONTEND-PROMPT-NL.md) ✅
- [Compliance](./compliance/) 📁

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

*Laatste update: 2025-01-29 door BMad Orchestrator*
