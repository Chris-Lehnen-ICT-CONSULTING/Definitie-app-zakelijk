---
id: EPIC-022
titel: "EPIC-022: Externe Bronnen Import - Adapter framework voor bulk import met validatie (DEFERRED: 95% overlap Export)"
type: epic
status: deferred
prioriteit: LOW
aangemaakt: 2025-09-29
bijgewerkt: 2025-09-29
owner: product-owner
applies_to: definitie-app@future
canonical: true
last_verified: 2025-09-29
vereisten:
  - REQ-043
  - REQ-102
  - REQ-103
  - REQ-104
  - REQ-105
  - REQ-106
  - REQ-107
stories:
  - US-413
  - US-414
  - US-415
  - US-416
  - US-440
  - US-418
stakeholders:
  - juridisch-professional
  - data-steward
  - integratie-specialist
  - security-officer
uitgesteld: 2025-09-29
reden_uitstel: Functionaliteit heeft 95% overlap met Export tab, geen meerwaarde voor single-user applicatie
target_release: TBD
---



# EPIC-022: Externe Bronnen Integratie & Import

## Executive Summary

Deze epic levert de volledige ‘🔌 Externe Bronnen’ functionaliteit in de UI, inclusief beheer van bronnen, zoeken in alle geregistreerde bronnen, (bulk) importeren van definities met validatie en mapping, en configuratie‑export/import. De implementatie rust op een adapter‑framework (ExternalSourceAdapter) zodat nieuwe bronnen eenvoudig zijn toe te voegen (mock, file system, REST API, etc.).

## Businesswaarde

- Verkort doorlooptijd om bestaande definities te benutten (migratie en hergebruik)
- Borgt kwaliteit door importvalidatie en status‑mapping naar interne workflow
- Verlaagt implementatierisico via mock/file‑adapters en duidelijke configuratie
- Schaalbaar: toevoeging van nieuwe bronnen zonder UI‑aanpassingen

## Scope

In scope:
- UI‑tab ‘Externe Bronnen’ met subviews: Bronnen • Zoeken • Import • Configuratie
- Adapter framework (registratie, test, connect/disconnect, search API)
- Individuele en bulk import (met opties, geschiedenis, voortgang)
- Configuratiebeheer (handmatige bronconfiguratie, export/import JSON)
- Basis NFR’s: timeouts, retries, rate limits, audit/trace voor import

Out of scope:
- Provider‑specifieke deep features (worden later per provider uitgewerkt)
- Volledige enterprise secrets‑vault integratie (future EPIC)

## Succescriteria (SMART)

- Specifiek: 100% van tabfuncties beschikbaar en gedekt door stories/REQs
- Meetbaar: zoek in ≤ 3s over ≥ 2 bronnen; bulk import 100 items ≤ 30s
- Acceptabel: validatiefouten duidelijk zichtbaar; rollback bij mislukte batch
- Relevant: sluit aan op migratie‑ en verrijkingsdoelen (EPIC‑003)
- Tijdgebonden: MVP in release v1.5

## Relaties

- Ondersteunt: REQ‑043 (Import from External Sources)
- Aanvullend op: EPIC‑003 (Web Lookup) — verrijking vs. importeren
- Beleid/Compliance: REQ‑092 (External Sources Governance Policy), EPIC‑006 (Beveiliging)

## Definition of Done (EPIC)

- Alle stories voltooid en gedemonstreerd in UI
- Adapter‑framework gedocumenteerd; mock + file adapter beschikbaar
- Importrapport en ‑geschiedenis zichtbaar; export/import config werkt
- Portal (docs/portal) toont EPIC + stories en traceability naar REQs

## Status Update - 2025-09-29

### Implementatie Verwijderd
De External Sources tab implementatie is verwijderd uit de codebase omdat:
1. **95% overlap** met bestaande Export tab functionaliteit
2. **85% overlap** met Web Lookup tab voor externe bronnen
3. **Geen meerwaarde** voor single-user applicatie
4. **1291 regels code** zonder realistische use cases

### Wat is gedocumenteerd
- **Business kennis bewaard** in `BUSINESS-KNOWLEDGE.md`
- **Status mapping logica** voor toekomstig gebruik
- **Import validatie regels** gedocumenteerd
- **Mock data voorbeelden** als referentie bewaard

### Verwijderde bestanden
- `src/ui/components/external_sources_tab.py` (734 regels)
- `src/external/external_source_adapter.py` (557 regels)
- Verwijzingen uit `src/ui/tabbed_interface.py`

### Toekomstige implementatie
Als External Sources functionaliteit in de toekomst nodig is:
1. **Use case**: Multi-user deployment of enterprise integratie
2. **Focus**: Juridische databases (Rechtspraak.nl, EUR-Lex)
3. **Basis**: Gebruik bewaard business kennis document
4. **Pattern**: Hergebruik Web Lookup adapter pattern (al werkend)
