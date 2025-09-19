---
id: CFR-BUG-026
titel: Importpad inconsistenties (ModernWebLookupService) en package‑exports → fragiele tests
status: OPEN
severity: MEDIUM
component: imports
owner: platform
gevonden_op: 2025-09-19
canonical: false
last_verified: 2025-09-19
applies_to: definitie-app@v2
---

# CFR-BUG-026: Importpad inconsistenties (ModernWebLookupService)

## Beschrijving
Tests en documentatie refereren wisselend aan `services.modern_web_lookup_service` en alternatieve package‑paden/exports. Gebrek aan gecentraliseerde exports maakt imports in tests fragiel en foutgevoelig.

## Verwacht gedrag
Eén eenduidige importstrategie met centrale export in `src/services/__init__.py` (bijv. `from .modern_web_lookup_service import ModernWebLookupService`) en consistente absolute imports in code en tests.

## Oplossing
- Voeg expliciete export toe in `src/services/__init__.py`
- Normaliseer imports in tests/code naar `from services.modern_web_lookup_service import ModernWebLookupService` of via package‑export
- Update examples/docs waar nodig

## Acceptatiecriteria
- `rg` op alternatieve/relatieve imports levert geen hits meer
- Tests vinden ModernWebLookupService zonder `sys.path` hacks

## Relatie
- US-074 (Import‑hygiëne) — standaardiseer absolute imports
- US-219 (Web Lookup test coverage) — vereenvoudigt mocking/fixtures

## Tests
- Contract‑test: importeren ModernWebLookupService via package‑export werkt
- Smoke: tests draaien zonder import‑fouten of pad‑workarounds

