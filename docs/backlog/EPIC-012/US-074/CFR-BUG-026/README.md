---
id: CFR-BUG-026
titel: Importpad inconsistenties (ModernWebLookupService) en package‑exports → fragiele tests
status: RESOLVED
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
Historische analyse wees op wisselende verwijzingen naar `ModernWebLookupService`. De huidige codebase gebruikt echter consistent `services.modern_web_lookup_service` en er zijn geen alternatieve pad‑imports meer in runtime code/tests.

## Verwacht gedrag
Eenduidige importstrategie met absolute pad `from services.modern_web_lookup_service import ModernWebLookupService`.

## Oplossing
- Code en tests gebruiken al het consistente pad `services.modern_web_lookup_service`.
- Geen runtime inconsistenties aangetroffen; enkel documentatie‑voorbeeld verwees nog naar een submap‑pad.

## Acceptatiecriteria
- Geen alternatieve/relatieve pad‑imports in code/tests — voldaan
- Tests vinden `ModernWebLookupService` zonder `sys.path` hacks — voldaan

## Relatie
- US-074 (Import‑hygiëne)
- US-219 (Web Lookup test coverage)

## Tests / Bewijs
- Container/usage: `src/services/container.py:29` gebruikt `services.modern_web_lookup_service`
- Tests: `tests/test_regression_suite.py:485`, `tests/services/test_web_lookup_wrapper_fallback.py:32` gebruiken hetzelfde pad
- Zoekactie toont géén alternatieve importpaden in code/tests; alleen een document (SOLUTION_PLAN) bevatte een voorbeeld met subpad.
