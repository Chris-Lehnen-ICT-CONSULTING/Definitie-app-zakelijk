# BATCH-081 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-root`
- Scope: 10/10 blobs, 1745/1745 fysieke regels en 147/147 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Volledige B079-B081-selectie gaf 330 groen; geïsoleerde focusrun gaf 53 groen maar schreef cache- en databaseartefacten en emitteerde SQLite ResourceWarnings.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: De DB-lifecyclewaarschuwingen zijn gededupliceerd; alleen de concrete testisolatie- en false-confidencegaten zijn nieuw.

## Bevindingen

### B081-001 — P2 — Resilience unit tests persist process state under repository cache

**Bewijs:** Starting and stopping real resilience components loads and writes fixed cache paths for retry, rate-limit and resilience state; no temporary path is injected.

**Reproductie:** Run the scoped resilience tests from an isolated base and list cache afterwards: .hmac_key, rate_limit_history.json, resilience_state.json and retry_history.json exist.

**Aanbevolen oplossing:** Inject a state directory or disable persistence for unit tests and assert the repository tree remains unchanged.

### B081-002 — P2 — DUP01 tests initialize the real container before replacing its repository

**Bewijs:** DUP01.__init__ resolves the real container and repository; fixtures replace repository only after construction, causing database creation and connection leaks.

**Reproductie:** Run the file in an isolated base: data/definities.db is created and numerous unclosed SQLite ResourceWarnings appear although tests later use a mock repository.

**Aanbevolen oplossing:** Inject the repository through the constructor or patch container lookup before construction and treat ResourceWarnings as failures.

### B081-003 — P2 — XML source integration suite reimplements instead of calling production

**Bewijs:** The file imports only format_bron and wrap_bronnen and tests a local _simulate_collect_bronnen copy; PromptServiceV2._collect_and_inject_bronnen is never invoked.

**Reproductie:** Break the production collection method while leaving the helper functions unchanged; the six integration-named tests remain green.

**Aanbevolen oplossing:** Test PromptServiceV2 directly with EnrichedContext fixtures and assert the full prompt-to-XML output.

## Niet getest

- Geen echte provider of productie-DB; filesystembijwerkingen en resourcewarnings kwamen uit een geïsoleerde base-export.
