# Canonieke Documentatie Locaties

Dit document definieert de officiële locaties voor alle documentatie types.
Laatste update: 2025-09-03

## 🎯 Officiële Locaties

### 0. Root Directory Documenten (Speciale bestanden)
- **README.md**: Project overzicht en installatie instructies
- **CLAUDE.md**: Claude Code AI agent instructies (MOET in root)
- **LICENSE**: Licentie informatie
- **CONTRIBUTING.md**: Bijdrage richtlijnen (optioneel)

### 1. Architectuur Documentatie
- **ADRs (Architecture Decision Records)**: `docs/architectuur/beslissingen/` ✅
  - ADR-015: Context Flow Refactoring ✅ CRITICAL
  - ADR-CFR-001: CFR Implementation ✅ CRITICAL
- **Architectuur Overzichten**: `docs/architectuur/` ✅
  - Enterprise Architecture (EA.md)
  - Solution Architecture (SA.md)
  - Technical Architecture (TA.md)
- **Context Flow Refactoring (CFR)**: `docs/architectuur/` ✅ CRITICAL
  - CFR-SOLUTION-OVERVIEW.md (Master document)
  - EA-CFR.md (Enterprise view)
  - SA-CFR.md (Solution design)
  - TA-CFR.md (Technical specs)
  - CFR-MIGRATION-STRATEGY.md (Rollout plan)
- **Diagrammen**: `docs/architectuur/diagrammen/`
- **Prompt Refactoring**: `docs/architectuur/prompt-refactoring/` ✅ NIEUW

### 2. Module Documentatie
- **Module Analyses**: `docs/technische-referentie/modules/` ✅ ACTIEF
- **API Documentatie**: `docs/technische-referentie/api/` ✅ ACTIEF
- **Integraties**: `docs/technische-referentie/integraties/` ✅ ACTIEF
- **Technische Analyses**: `docs/technisch/` ✅

### 3. Handleidingen
- **Ontwikkelaars Handleidingen**: `docs/handleidingen/ontwikkelaars/`
- **Gebruikers Handleidingen**: `docs/handleidingen/gebruikers/`
- **Deployment Guides**: `docs/handleidingen/deployment/`

### 4. Code Analyse & Reviews
- **Performance Analyses**: `docs/code-analyse/performance/`
- **Security Reviews**: `docs/reviews/` ✅ ACTIEF
- **Code Quality Reports**: `docs/code-analyse/quality/`
- **Executive Summaries**: `docs/reviews/` ✅ ACTIEF

### 5. Project Documentatie
- **Requirements**: `docs/requirements/` ✅ ACTIEF
- **Handover Documents**: `docs/handover/` ✅ ACTIEF
- **User Stories**: `docs/stories/` ✅ ACTIEF
- **Epics**: `docs/epics/` ✅ ACTIEF

### 6. Archief
- **Oude Versies**: `docs/archief/`
- **Referentie Materiaal**: `docs/archief/REFERENTIE/`
- **Historische Beslissingen**: `docs/archief/beslissingen/`

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

## 🔍 Bij Twijfel

Als je niet zeker weet waar een document hoort:
1. Check dit document voor de juiste locatie
2. Kijk of het bestand al bestaat op de nieuwe locatie
3. Vraag het team of check de git history

---
Voor vragen: Contact het development team
