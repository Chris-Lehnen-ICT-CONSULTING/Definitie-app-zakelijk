# BATCH-077 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 3/3 blobs, 1460/1460 fysieke regels en 128/128 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Exacte scope-run: 24 groen, 12 rood en één collection error; de US042-suite verzamelde nul tests.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.

## Bevindingen

### B077-001 — P2 — US042 suite cannot be collected because it imports a removed module

**Bewijs:** The suite imports ui.components.context_selector, which does not exist; production uses EnhancedContextManagerSelector under a different module.

**Reproductie:** Run pytest --collect-only for the file: collection exits 2 with ModuleNotFoundError and zero tests are collected.

**Aanbevolen oplossing:** Target the current selector and add real Streamlit/AppTest coverage for selection, custom values, persistence and error feedback.

### B077-002 — P2 — US043 suite exercises removed and fabricated contracts

**Bewijs:** Cases omit required request IDs, call removed synchronous routes and nonexistent formatting, monitoring and rollout APIs, and one performance claim measures only test sleeps.

**Reproductie:** Run the file on the base: 13 tests pass and 12 fail across those stale contracts.

**Aanbevolen oplossing:** Rebuild the suite around current async APIs, valid requests and injected offline services, and measure actual production paths.

### B077-003 — P3 — Failing feature-flag test leaks process environment state

**Bewijs:** The test mutates os.environ directly and fails before restoring the value, leaving USE_MODERN_CONTEXT_FLOW=true for later tests.

**Reproductie:** Run the failing feature-flag case and inspect os.environ afterwards; the true value remains.

**Aanbevolen oplossing:** Use monkeypatch.setenv with the current enum/API and assert suite-level environment restoration.

### B077-004 — P3 — Interface compatibility tests never inspect concrete signatures

**Bewijs:** The tests create MagicMock(spec=Interface) and check hasattr/callable only; concrete services with incompatible parameters still satisfy the gate.

**Reproductie:** Substitute a concrete implementation whose method name exists but signature is incompatible; the assertions remain green.

**Aanbevolen oplossing:** Parameterize over container-registered implementations, compare inspect.signature and execute minimal contract calls.

## Niet getest

- Geen live Streamlit-browser, keyboard/screenreader/contrast/responsive test en geen echte provider of netwerk.
