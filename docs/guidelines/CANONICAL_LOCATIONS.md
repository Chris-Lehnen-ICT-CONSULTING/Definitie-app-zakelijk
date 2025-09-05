# Canonieke Documentatie Locaties

Dit document definieert de officiële locaties voor alle documentatie types.
Laatste update: 2025-09-05 (Architectuur Consolidatie Compleet)

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
- **Deployment Guides**: `docs/handleidingen/deployment/`

### 5. Code Analyse & Reviews
- **Performance Analyses**: `docs/code-analyse/performance/`
- **Security Reviews**: `docs/reviews/` ✅ ACTIEF
- **Code Quality Reports**: `docs/code-analyse/quality/`
- **Executive Summaries**: `docs/reviews/` ✅ ACTIEF

### 6. Project Documentatie
- **Requirements**: `docs/requirements/` ✅ ACTIEF
- **Handover Documents**: `docs/handover/` ✅ ACTIEF
- **User Stories**: `docs/stories/` ✅ ACTIEF
- **Epics**: `docs/epics/` ✅ ACTIEF

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

Deze directories bevatten duplicaten en worden gefaseerd verwijderd:
- `docs/active/` - Migreer naar specifieke subdirectories
- `docs/modules/` - Gebruik `docs/technische-referentie/modules/` ✅ Verwijderd
- `docs/analysis/` - Gebruik `docs/code-analyse/`
- `docs/development/` - Gebruik `docs/handleidingen/ontwikkelaars/`
- `docs/reference/setup/` - Gebruik `docs/handleidingen/installatie/` ✅ Verwijderd

## 📋 Migratie Status

- ✅ Backup gemaakt: 2025-08-18
- ✅ Reorganisatie uitgevoerd: 2025-09-03
- ✅ Documenten verplaatst naar canonieke locaties
- ✅ INDEX.md bijgewerkt met nieuwe structuur
- ✅ **Architectuur Consolidatie Compleet: 2025-09-05**
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
