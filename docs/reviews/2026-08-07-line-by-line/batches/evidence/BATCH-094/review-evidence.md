# BATCH-094 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-root`
- Scope: 10/10 blobs, 850/850 fysieke regels en 47/47 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Veilige smoke-selectie: 9 groen, 2 rood en 1 skip; validatiesmoke was groen, beide UI-modi faalden op dezelfde niet-hermetische standaarddatabase.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.

## Bevindingen

### B094-001 — P2 — Wetgeving smoke tests contradict the disabled runtime provider

**Bewijs:** Runtime configuration disables wetgeving_nl; one context test explicitly accepts no call while health and parked tests require results or attempts.

**Reproductie:** Run the three tests under default config: two fail and one passes without invoking SRU.

**Aanbevolen oplossing:** Test disabled behavior separately and explicitly enable an injected provider for query and parked scenarios.

### B094-002 — P2 — Validation V2 smoke mocks the method it claims to test

**Bewijs:** Cases check imports and local environment expressions; the core case patches orchestrator.validate_text itself and calls the mock.

**Reproductie:** Replace underlying validation with a broken implementation; the smoke still passes because the public method is mocked.

**Aanbevolen oplossing:** Mock only dependencies, invoke the real orchestrator and test actual selection logic with monkeypatch-managed env.

### B094-003 — P3 — UI smoke's legacy and new modes are identical and leak environment state

**Bewijs:** USE_NEW_SERVICES is no longer read by production, both parametrizations construct the same V2 service and the variable is not restored.

**Reproductie:** Search src for the variable and run both cases; no production branch differs, and read-only runs fail on the same default DB path.

**Aanbevolen oplossing:** Remove fictive dual mode, inject hermetic dependencies and add real AppTest/browser assertions.

## Niet getest

- Geen echte Streamlitbrowser, keyboard/screenreader/contrast/responsive test, provider of productie-DB.
