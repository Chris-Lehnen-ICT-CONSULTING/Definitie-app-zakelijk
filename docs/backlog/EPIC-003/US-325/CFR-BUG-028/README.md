---
id: CFR-BUG-028
titel: Ontbrekende testbestanden/fixtures voor ModernWebLookupService en providers
status: open
owner: qa-team
applies_to: definitie-app@v2
canonical: false
last_verified: 2025-09-19
severity: MEDIUM
component: testing
gevonden_op: 2025-09-19
---

# CFR-BUG-028: Ontbrekende testbestanden/fixtures (Web Lookup)

## Beschrijving
Er ontbreken unit/integratietests en mock‑fixtures voor Web Lookup, waardoor regressies onopgemerkt blijven en documentatie verwijzingen naar tests (coverage) niet aansluiten op de feitelijke projectstructuur.

## Verwacht gedrag
Volwaardige tests en fixtures voor `ModernWebLookupService` en providers (Wikipedia, SRU, …) met gemockte I/O en duidelijke performance/assertie‑criteria.

## Oplossing
- Voeg directorystructuur toe zoals in docs beschreven (unit/integration)
- Maak reusable fixtures/mocks (timeouts, errors, parallelisme)
- Dekking >80% voor Web Lookup modules

## Acceptatiecriteria
- Unit: parallel lookup, timeout‑budget, error handling
- Integratie: end‑to‑end flow met gemockte providers
- Performance: eenvoudige tijdslimiet (<2s) in gemockte omgeving

## Relatie
- US-325 (Basic Web Lookup Test Coverage)
- US-074 (Import‑hygiëne) voor padconsistentie

## Tests
- pytest markers voor performance, unit, integration
- Geen netwerk‑calls in tests (volledig gemockt)

