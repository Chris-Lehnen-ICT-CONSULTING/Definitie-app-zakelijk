# Backlog Dashboard – Single-User Focus

De dashboardgegevens zijn gesynchroniseerd met de opgeschoonde backlog (oktober 2025). Prioriteit ligt bij vier epics; overige epics blijven ter naslag actief maar krijgen geen nieuwe work-in-progress.

## Epic Overzicht

| Epic | Status | Belangrijkste Stories | Notities |
|---|---|---|---|
| [EPIC-030](../EPIC-030/EPIC-030.md) | Active | US-143, US-195, US-015, US-227 | Prompt- en definitiekwaliteit, tokenbudget, bronverantwoording |
| [EPIC-006](../EPIC-006/EPIC-006.md) | Active | US-140, US-029, US-030, US-031, US-032 | Security baseline voor single-user deployment |
| [EPIC-028](../EPIC-028/EPIC-028.md) | Ready | US-235, US-236, US-028 | UI vereenvoudiging naar 4 tabbladen + gedeelde validatie |
| [EPIC-003](../EPIC-003/EPIC-003.md) | Active (Light Scope) | US-015 follow-up, US-017 | Lichte contentverrijking zonder enterprise integraties |
| [EPIC-005](../EPIC-005/EPIC-005.md) | Monitoring | US-137 | Export blijft beschikbaar, bulkfeatures gearchiveerd |
| [EPIC-001](../EPIC-001/EPIC-001.md) | Completed | – | Historische referentie, blijft zichtbaar voor traceability |
| [EPIC-002](../EPIC-002/EPIC-002.md) | Completed | – | Validatieregelset klaar, alleen regressies onderhouden |
| [EPIC-007](../EPIC-007/EPIC-007.md) | Monitoring | US-033, US-035 | Performance verbeteringen pas oppakken na EPIC-030 |
| [EPIC-010](../EPIC-010/EPIC-010.md) | Completed | – | Context flow gerefactord |
| [EPIC-011](../EPIC-011/EPIC-011.md) | Backlog | US-301, US-302 | Documentatie-updates wanneer tijd beschikbaar |

> Gearchiveerde enterprise-epics (EPIC-009, EPIC-015) staan nu onder `docs/backlog/_archive/enterprise/` en worden niet meer getoond in dit overzicht.

## Requirements ⇄ Epics

| Requirement | Type | Status | Gelinkte Epics |
|---|---|---|---|
| [REQ-002](../requirements/REQ-002.md) API Key beveiliging | Nonfunctional | Gereed | EPIC-006 |
| [REQ-006](../requirements/REQ-006.md) OWASP Top 10 compliance | Nonfunctional | In Progress | EPIC-006 |
| [REQ-038](../requirements/REQ-038.md) OpenAI GPT-4 Integratie | Functional | Gereed | EPIC-030 |
| [REQ-061](../requirements/REQ-061.md) Graceful Degradation | Nonfunctional | In Progress | EPIC-030 |
| [REQ-082](../requirements/REQ-082.md) Prompt Token Budget | Nonfunctional | Backlog | EPIC-030 |
| [REQ-048](../requirements/REQ-048.md) Responsive Web Design | Nonfunctional | In Progress | EPIC-028 |
| [REQ-052](../requirements/REQ-052.md) Real-time validatie Feedback | Functional | In Progress | EPIC-028 |
| [REQ-021](../requirements/REQ-021.md) Web Lookup Integratie | Functional | Gereed | EPIC-003 |
| [REQ-022](../requirements/REQ-022.md) Export Functionality | Functional | Gereed | EPIC-005 |
| [REQ-073](../requirements/REQ-073.md) CI Testen | Nonfunctional | Gereed | EPIC-006 |

## Workflow Notities

- **WIP Limiet**: maximaal één `DOING` item (zie `ACTIVE.md`).
- **Labeling**: nieuwe issues krijgen één van de vier primaire epics (`EPIC-030`, `EPIC-006`, `EPIC-028`, `EPIC-003`).
- **Archief**: verwijderde stories hebben een `archived_reason` in `docs/backlog/_archive/**`.
- **Dashboard Data**: JSON feed bijgewerkt in `data.json` voor tooling die dit overzicht consumeert.
