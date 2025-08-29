# 🏗️ DefinitieAgent Architecture Documentation

## 📋 Overview

This directory contains the complete architecture documentation for the DefinitieAgent project, including Enterprise Architecture (EA) and Solution Architecture (SA) documents with automated synchronization and validation.

### Documentatie-organisatie scripts (toelichting)
Deze scripts gaan over documentstructuur en consistentie (niet over applicatiecode):
- `scripts/hooks/check-doc-location.py`: pre-commit controle op juiste mappen + relocatie‑suggesties.
- `scripts/migrate-documents-fase3.sh`: verplaats/hernoem docs volgens structuur. Eerst `--dry-run`, alleen maintainers met `--execute`.
- `scripts/architecture_validator.py`: valideert EA/SA op scheiding van concerns, overlap, templates.
- `scripts/architecture_sync.py`: synchroniseert gedeelde secties/metadata (ADR‑referenties, metrics) tussen EA en SA.
Zie ook: CONTRIBUTING.md → “Documentatie‑organisatie (alleen maintainers)”.

## 🎯 Hoofddocumenten

| Document | Doel | Status | Laatste Update |
|----------|------|--------|----------------|
| **[ENTERPRISE_ARCHITECTURE.md](./ENTERPRISE_ARCHITECTURE.md)** | Strategische business architectuur met product portfolio | ✅ Actief | 2025-08-20 |
| **[SOLUTION_ARCHITECTURE.md](./SOLUTION_ARCHITECTURE.md)** | Technische implementatie met feature registry | ✅ Actief | 2025-08-20 |
| **[PRODUCT_DELIVERY_TRACKER.md](./PRODUCT_DELIVERY_TRACKER.md)** | Live sprint tracking en delivery status | 🔄 Weekly | 2025-08-20 |
| **[ARCHITECTURE_GOVERNANCE.md](./ARCHITECTURE_GOVERNANCE.md)** | Governance processen en richtlijnen | ✅ Actief | 2024-08-19 |
| **[MIGRATION_ROADMAP.md](./MIGRATION_ROADMAP.md)** | Migratie planning naar microservices | ✅ Actief | 2024-08-19 |
| **[GVI-implementation-plan.md](./GVI-implementation-plan.md)** | Praktische quality improvement gids ("kabels aansluiten") | ✅ Actief | 2025-08-20 |
| **[TARGET_ARCHITECTURE.md](./TARGET_ARCHITECTURE.md)** | Doel architectuur definitie | ✅ Actief | 2024-01-18 |
| **[CURRENT_STATE.md](./CURRENT_STATE.md)** | Huidige situatie analyse | ✅ Actief | 2024-01-18 |

## 📁 Directory Structuur

### Core Documenten

- **Enterprise Architecture** - Business view inclusief product portfolio status
- **Solution Architecture** - Technische view met feature implementation details
- **Product Delivery Tracker** - Sprint voortgang en blockers

### [beslissingen/](./beslissingen/)

Architecture Decision Records (ADRs) - Belangrijke architectuur beslissingen

- ADR-001: Monolithische Structuur
- ADR-002: Features First Development
- ADR-003: Legacy Code als Specificatie
- ADR-004: Incrementele Migratie Strategie
- ADR-005: Service Architecture Evolution

### [templates/](./templates/)

Herbruikbare templates en voorbeelden

- Enterprise Architecture Template
- Solution Architecture Template
- Cross-reference Guide

### [_archive/](./archive/)

Gearchiveerde documentatie

- 2024-01-* - Eerdere analyses en reviews
- 2025-08-20-reorganization - Duplicate documenten van reorganisatie

## 🚀 Quick Start

1. **Business Stakeholder?** Begin met [ENTERPRISE_ARCHITECTURE.md](./ENTERPRISE_ARCHITECTURE.md)
2. **Developer?** Start met [SOLUTION_ARCHITECTURE.md](./SOLUTION_ARCHITECTURE.md)
3. **Product Owner?** Check [PRODUCT_DELIVERY_TRACKER.md](./PRODUCT_DELIVERY_TRACKER.md)
4. **Architect?** Lees [ARCHITECTURE_GOVERNANCE.md](./ARCHITECTURE_GOVERNANCE.md)

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

- [Module Analyses](../technische-referentie/modules/) - Gedetailleerde module documentatie
- [Development Guide](../handleidingen/) - Implementatie handleidingen
- [API Documentatie](../../src/services/interfaces.py) - Service interfaces

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

⚠️ **Let op**: Document migratie scripts zijn alleen voor maintainers. Zie [CONTRIBUTING.md](../../CONTRIBUTING.md#documentatie-organisatie-alleen-maintainers) voor details.

## 🚧 Onderhoud

| Document | Laatste Update | Review Cyclus | Owner |
|----------|---------------|---------------|-------|
| ENTERPRISE_ARCHITECTURE.md | 2025-08-20 | Quarterly | Enterprise Architect |
| SOLUTION_ARCHITECTURE.md | 2025-08-20 | Sprint | Solution Architect |
| PRODUCT_DELIVERY_TRACKER.md | 2025-08-20 | Weekly | Product Owner |
| ARCHITECTURE_GOVERNANCE.md | 2024-08-19 | Quarterly | Architecture Board |
| MIGRATION_ROADMAP.md | 2024-08-19 | Bi-weekly | Tech Lead |
| ADRs | Various | As needed | Team |

## 🔄 Recente Updates (2025-08-20)

### Architectuur Reorganisatie Voltooid

- ✅ EA uitgebreid met Product Portfolio Status (Section 8)
- ✅ SA uitgebreid met Feature Registry (Section 12) en Tech Debt (Section 13)
- ✅ Nieuw PRODUCT_DELIVERY_TRACKER.md voor sprint tracking
- ✅ 12 duplicate documenten gearchiveerd
- ✅ Van 30+ naar 15 actieve documenten (50% reductie)

Voor vragen of updates, contact het architecture team via Slack #architecture-discussion.
