# 🏗️ DefinitieAgent Architecture Documentation

## 📋 Overview

This directory contains the complete architecture documentation for the DefinitieAgent project, including Enterprise Architecture (EA) and Solution Architecture (SA) documents with automated synchronization and validation.

### Documentatie-organisatie scripts (toelichting)
Deze scripts gaan over documentstructuur en consistentie (niet over applicatiecode):
- `scripts/hooks/check-doc-location.py`: pre-commit controle op juiste mappen + relocatie‑suggesties.
- `scripts/migrate-documents-fase3.sh`: verplaats/hernoem docs volgens structuur. Eerst `--dry-run`, alleen maintainers met `--execute`.
- `scripts/architecture_validator.py`: valideert EA/SA op scheiding van concerns, overlap, templates.
- `scripts/architecture_sync.py`: synchroniseert gedeelde secties/metadata (ADR‑referenties, metrics) tussen EA en SA.
Zie ook: CONTRIBUTING.md (root) → “Documentatie‑organisatie (alleen maintainers)”.

## 🎯 Hoofddocumenten

| Document | Doel | Status | Laatste Update |
|----------|------|--------|----------------|
| **[ENTERPRISE_ARCHITECTURE.md](./ENTERPRISE_ARCHITECTURE.md)** | Strategische business architectuur met product portfolio | ✅ Actief | 2025-08-20 |
| **[SOLUTION_ARCHITECTURE.md](./SOLUTION_ARCHITECTURE.md)** | Technische implementatie met feature registry | ✅ Actief | 2025-08-20 |
| **[TECHNICAL_ARCHITECTURE.md](./TECHNICAL_ARCHITECTURE.md)** | Technische implementatie details | ✅ Actief | 2025-09-04 |

## 📁 Directory Structuur

### Core Documenten

- **Enterprise Architecture** - Business view inclusief product portfolio status
- **Solution Architecture** - Technische view met feature implementation details
- **Product Delivery Tracker** - Sprint voortgang en blockers

### Architecture Decisions

Belangrijke architectuur beslissingen zijn opgenomen in de hoofddocumenten:
- Zie ENTERPRISE_ARCHITECTURE.md sectie 5 voor strategische beslissingen
- Zie SOLUTION_ARCHITECTURE.md sectie 7 voor solution beslissingen
- Zie TECHNICAL_ARCHITECTURE.md sectie 3 voor technische beslissingen

### [templates/](./templates/)

Herbruikbare templates en voorbeelden

- Enterprise Architecture Template
- Solution Architecture Template
- Cross-reference Guide

### Gearchiveerde Documentatie

Gearchiveerde documentatie is te vinden in:
- `/docs/archief/2025-09-architectuur-consolidatie/` - Architectuur consolidatie september 2025
- `/docs/archief/` - Oudere gearchiveerde documenten

## 🚀 Quick Start

1. **Business Stakeholder?** Begin met [ENTERPRISE_ARCHITECTURE.md](./ENTERPRISE_ARCHITECTURE.md)
2. **Developer?** Start met [SOLUTION_ARCHITECTURE.md](./SOLUTION_ARCHITECTURE.md)
3. **Technical Lead?** Check [TECHNICAL_ARCHITECTURE.md](./TECHNICAL_ARCHITECTURE.md)
4. **Architect?** Lees alle drie canonical documenten

## 📊 Product & Architectuur Status

### Overall Product Completion: 26%

```text
Features: 23/87 complete (26%)
Epics Status:
├─ Basis Definitie: ████████░░ 80% ✅
├─ Kwaliteit:       ███████░░░ 75% ✅
├─ UI:              ██░░░░░░░░ 20% 🔴
├─ Security:        ░░░░░░░░░░  0% 🔴
├─ Performance:     ██░░░░░░░░ 20% 🟠
├─ Export/Import:   █░░░░░░░░░ 14% 🟠
├─ Web Lookup:      ░░░░░░░░░░  0% 🔴
├─ Monitoring:      ████░░░░░░ 40% 🟡
└─ Content:         ██████░░░░ 67% ✅
```

### Critical Blockers

- 🔴 No Authentication (cannot deploy)
- 🔴 Single-user database (SQLite locks)
- 🔴 Missing Web Lookup (core feature)
- 🟠 Performance 8-12s (target <5s)

## 🔗 Gerelateerde Documentatie

- [Technical Documentation](../technisch/) - Technische analyses en rapporten
- [Development Workflows](../workflows/) - Development workflows
- [Testing Documentation](../testing/) - Test plannen en scenarios

## 📝 Conventies

- **Hoofddocumenten**: UPPERCASE.md voor zichtbaarheid
- **ADRs**: `ADR-XXX-titel.md` formaat
- **Diagrammen**: Mermaid (.mmd) of PlantUML (.puml)
- **Updates**: Altijd versie en datum bijwerken

## 📝 Voor Documentatie Schrijvers

### Belangrijke Richtlijnen

- **Geen code in deze directory** - alleen documentatie
- Gebruik de juiste subdirectory voor je document type
- ADRs volgen het ADR-XXX-titel.md formaat
- Contracts hebben altijd een versienummer

### Document Validatie Tools

Voor maintainers zijn er hulpscripts beschikbaar om documentatie kwaliteit te waarborgen:

- **Locatie check**: De pre-commit hook controleert automatisch of documenten in de juiste directories staan
- **EA/SA validatie**: `python scripts/architecture_validator.py` controleert scheiding van concerns
- **Synchronisatie**: `python scripts/architecture_sync.py` houdt gedeelde secties consistent

⚠️ **Let op**: Document migratie scripts zijn alleen voor maintainers. Zie CONTRIBUTING.md (root) voor details.

## 🚧 Onderhoud

| Document | Laatste Update | Review Cyclus | Owner |
|----------|---------------|---------------|-------|
| ENTERPRISE_ARCHITECTURE.md | 2025-08-20 | Quarterly | Enterprise Architect |
| SOLUTION_ARCHITECTURE.md | 2025-08-20 | Sprint | Solution Architect |
| TECHNICAL_ARCHITECTURE.md | 2025-09-04 | Sprint | Technical Lead |
| ADRs | Various | As needed | Team |

## 🔄 Recente Updates (2025-08-20)

### Architectuur Reorganisatie Voltooid

- ✅ EA uitgebreid met Product Portfolio Status (Section 8)
- ✅ SA uitgebreid met Feature Registry (Section 12) en Tech Debt (Section 13)
- ✅ Nieuw PRODUCT_DELIVERY_TRACKER.md voor sprint tracking
- ✅ 12 duplicate documenten gearchiveerd
- ✅ Van 30+ naar 15 actieve documenten (50% reductie)

Voor vragen of updates, contact het architecture team via Slack #architecture-discussion.
