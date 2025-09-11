# Canonieke Documentatie Locaties

Dit document definieert de officiële locaties voor alle documentatie types.
Laatste update: 05-09-2025 (Architectuur Consolidatie Compleet)

## 🎯 Officiële Locaties

### 0. Root Directory Documenten (Speciale bestanden)
- **README.md**: Project overzicht en installatie instructies
- **CLAUDE.md**: Claude Code AI agent instructies (MOET in root)
- **LICENSE**: Licentie informatie
- **CONTRIBUTING.md**: Bijdrage richtlijnen (optioneel)

### 1. Architectuur Documentatie (Geconsolideerd September 2025)

| Document Type | Canonical Location | Status |
|--------------|-------------------|--------|
| **Enterprise Architecture** | `/docs/architectuur/ENTERPRISE_ARCHITECTURE.md` | ✅ Single Source |
| **Solution Architecture** | `/docs/architectuur/SOLUTION_ARCHITECTURE.md` | ✅ Single Source |
| **Technical Architecture** | `/docs/architectuur/TECHNICAL_ARCHITECTURE.md` | ✅ Single Source |
| Architecture Decisions | `Geïntegreerd in canonical docs` | Gearchiveerd |
| Architecture Templates | `/docs/architectuur/*_TEMPLATE.md` | Active |
| Architecture Reports | `/docs/architectuur/*-REPORT.md` | Active |
| Diagrams | `/docs/architectuur/diagrams/` | Active |
| Contracts | `/docs/architectuur/contracts/` | Active |
| Prompt Refactoring | `/docs/architectuur/prompt-refactoring/` | Active |

### 2. Guidelines & Standards
- **Documentation Guidelines**: `docs/guidelines/` ✅ ACTIEF
- **Dit document zelf**: `docs/guidelines/CANONICAL_LOCATIONS.md`
- **Documentation Policy**: `docs/guidelines/DOCUMENTATION_POLICY.md`
- **Agents Guidelines**: `docs/guidelines/AGENTS.md`
- **Development Workflows**: `docs/guidelines/TDD_TO_DEPLOYMENT_WORKFLOW.md`

### 3. Module Documentatie
- **Module Analyses**: `docs/technische-referentie/modules/` ✅ ACTIEF
- **API Documentatie**: `docs/technische-referentie/api/` ✅ ACTIEF
- **Integraties**: `docs/technische-referentie/integraties/` ✅ ACTIEF
- **Technische Analyses**: `docs/technisch/` ✅

### 4. Handleidingen
- **Ontwikkelaars Handleidingen**: `docs/handleidingen/ontwikkelaars/`
- **Gebruikers Handleidingen**: `docs/handleidingen/gebruikers/`
- **Uitrol Guides**: `docs/handleidingen/deployment/`

### 5. Code Analyse & Reviews
- **Prestaties Analyses**: `docs/code-analyse/performance/`
- **Beveiliging Reviews**: `docs/reviews/` ✅ ACTIEF
- **Code Quality Reports**: `docs/code-analyse/quality/`
- **Executive Summaries**: `docs/reviews/` ✅ ACTIEF

### 6. Backlog Management (Vereenvoudigde Structuur - December 2025)

**🔴 NIEUWE VEREENVOUDIGDE STRUCTUUR:**
```
docs/backlog/
├── EPIC-001/                    # Elke EPIC in eigen directory
│   ├── EPIC-001.md             # Epic documentatie
│   ├── US-001/                 # User stories direct onder EPIC
│   │   └── US-001.md           # Story documentatie
│   ├── US-002/
│   │   └── US-002.md
│   └── bugs/                   # Bugs op EPIC niveau
│       └── BUG-XXX.md          # Bug documentatie
└── EPIC-002/
    └── ...
```

**Canonieke Locaties:**
- **Epic**: `/docs/backlog/EPIC-XXX/EPIC-XXX.md` ✅ ACTIEF
- **User Story**: `/docs/backlog/EPIC-XXX/US-XXX/US-XXX.md` ✅ ACTIEF
- **Bug**: `/docs/backlog/EPIC-XXX/bugs/BUG-XXX.md` ✅ ACTIEF
- **Requirements**: `/docs/backlog/requirements/` ✅ BEHOUDEN (92 requirements)
- **Dashboards**: `/docs/backlog/dashboard/` ✅ BEHOUDEN
  - `index.html` (requirements tabel, zoeken + sorteren)
  - `per-epic.html` (inklappende blokken per epic)
  - `graph.html` (offline REQ ↔ EPIC graph)

**❌ VEROUDERDE LOCATIES (NIET MEER GEBRUIKEN):**
- ~~`/docs/backlog/epics/`~~ → Gebruik `/docs/backlog/EPIC-XXX/`
- ~~`/docs/backlog/stories/`~~ → Gebruik `/docs/backlog/EPIC-XXX/US-XXX/`
- ~~`/docs/backlog/bugs/`~~ → Gebruik `/docs/backlog/EPIC-XXX/bugs/`
- ~~`/docs/backlog/EPIC-XXX/User Stories/`~~ → Stories direct onder EPIC

### 7. Archief
- **Architectuur Consolidatie (Sept 2025)**: `docs/archief/2025-09-architectuur-consolidatie/`
  - EA/SA/TA variants (historische versies)
  - CFR documenten (Context Flow Refactoring)
  - PER-007 documenten (implementatie details)
  - V1/V2 migratie documenten
- **Oude Versies**: `docs/archief/`
- **Referentie Materiaal**: `docs/archief/REFERENTIE/`
- **Historische Beslissingen**: `docs/archief/2025-09-architectuur-consolidatie/beslissingen/`

## ⚠️ Verouderde Locaties (NIET GEBRUIKEN)

⚠️ **BELANGRIJK**: Vanaf 8 september 2025:
- `docs/requirements/` → Gebruik `/docs/backlog/requirements/`
- `docs/epics/` → Gebruik `/docs/backlog/epics/`
- `docs/stories/` → Gebruik `/docs/backlog/stories/`
- `docs/dashboard/` → Gebruik `/docs/backlog/dashboard/`

Deze directories bevatten duplicaten en worden gefaseerd verwijderd:
- `docs/active/` - Migreer naar specifieke subdirectories
- `docs/modules/` - Gebruik `docs/technische-referentie/modules/` ✅ Verwijderd
- `docs/analysis/` - Gebruik `docs/code-analyse/`
- `docs/development/` - Gebruik `docs/handleidingen/ontwikkelaars/`
- `docs/reference/setup/` - Gebruik `docs/handleidingen/installatie/` ✅ Verwijderd

## 📋 Migratie Status

- ✅ Backup gemaakt: 18-08-2025
- ✅ Reorganisatie uitgevoerd: 03-09-2025
- ✅ Documenten verplaatst naar canonieke locaties
- ✅ INDEX.md bijgewerkt met nieuwe structuur
- ✅ **Architectuur Consolidatie Compleet: 05-09-2025**
  - Van 47 documenten → 3 canonical documenten
  - Alle PER-007/CFR fixes geïntegreerd
  - Obsolete documenten gearchiveerd

## 🔍 Bij Twijfel

Als je niet zeker weet waar een document hoort:
1. Check dit document voor de juiste locatie
2. Kijk of het bestand al bestaat op de nieuwe locatie
3. Vraag het team of check de git history

---
Voor vragen: Contact het development team
