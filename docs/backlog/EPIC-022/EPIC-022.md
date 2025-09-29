---
id: EPIC-022
titel: Externe Bronnen Integratie & Import
type: epic
status: TE_DOEN
prioriteit: HOOG
owner: product-owner
stakeholders:
  - juridisch-professional
  - data-steward
  - integratie-specialist
  - security-officer
aangemaakt: 2025-09-29
bijgewerkt: 2025-09-29
target_release: v1.5
canonical: true
stories:
  - US-413
  - US-414
  - US-415
  - US-416
  - US-417
  - US-418
vereisten:
  - REQ-043
  - REQ-102
  - REQ-103
  - REQ-104
  - REQ-105
  - REQ-106
  - REQ-107
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

