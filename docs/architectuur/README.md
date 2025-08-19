# Architectuur Documentatie

Dit directory bevat de geconsolideerde architectuur documentatie voor het Definitie-app project.

## 🎯 Hoofddocumenten

| Document | Doel | Status |
|----------|------|--------|
| **[TARGET_ARCHITECTURE.md](./TARGET_ARCHITECTURE.md)** | Complete gewenste (TO-BE) architectuur | ✅ Compleet |
| **[CURRENT_STATE.md](./CURRENT_STATE.md)** | Huidige (AS-IS) architectuur analyse | ✅ Compleet |
| **MIGRATION_ROADMAP.md** | Stapsgewijze migratie planning | 🚧 In ontwikkeling |

## 📁 Directory Structuur

### [beslissingen/](./beslissingen/)
Architecture Decision Records (ADRs) - Belangrijke architectuur beslissingen
- ADR-001: Monolithische Structuur
- ADR-002: Features First Development
- ADR-003: Legacy Code als Specificatie
- ADR-004: Incrementele Migratie Strategie
- ADR-005: Service Architecture Evolution

### [diagrams/](./diagrams/)
Architectuur diagrammen en visualisaties
- deployment-architecture.mmd
- Component diagrammen
- Flow diagrammen

### [_archive/](./archive/)
Gearchiveerde documentatie van eerdere analyses en plannen

## 🚀 Quick Start

1. **Nieuw op het project?** Begin met [CURRENT_STATE.md](./CURRENT_STATE.md)
2. **Wil je de visie begrijpen?** Lees [TARGET_ARCHITECTURE.md](./TARGET_ARCHITECTURE.md)
3. **Klaar om te bouwen?** Check MIGRATION_ROADMAP.md (komt eraan)

## 📊 Architectuur Status

```
Current State ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 60% ━━━━━━━━━━━━━━━━ Target State
              ├─ Services: 90% ─────────────────────┤
              ├─ Database: 20% ──┤
              ├─ API Layer: 0% ┤
              ├─ UI: 30% ────────┤
              ├─ Security: 0% ┤
              └─ Testing: 11% ───┤
```

## 🔗 Gerelateerde Documentatie

- [Module Analyses](../technische-referentie/modules/) - Gedetailleerde module documentatie
- [Development Guide](../handleidingen/) - Implementatie handleidingen
- [API Documentatie](../../src/services/interfaces.py) - Service interfaces

## 📝 Conventies

- **Hoofddocumenten**: UPPERCASE.md voor zichtbaarheid
- **ADRs**: `ADR-XXX-titel.md` formaat
- **Diagrammen**: Mermaid (.mmd) of PlantUML (.puml)
- **Updates**: Altijd versie en datum bijwerken

## 🚧 Onderhoud

| Document | Laatste Update | Review Cyclus | Owner |
|----------|---------------|---------------|-------|
| TARGET_ARCHITECTURE.md | 2024-01-18 | Quarterly | Architect |
| CURRENT_STATE.md | 2024-01-18 | Monthly | Tech Lead |
| MIGRATION_ROADMAP.md | TBD | Bi-weekly | Project Manager |
| ADRs | Various | As needed | Team |

Voor vragen of updates, contact het architecture team via Slack #architecture-discussion.
