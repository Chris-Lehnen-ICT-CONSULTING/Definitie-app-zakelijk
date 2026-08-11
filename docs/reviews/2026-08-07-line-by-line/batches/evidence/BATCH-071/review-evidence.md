# BATCH-071 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 7/7 blobs, 1849/1849 fysieke regels en 132/132 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- 234 scoped tests groen en 24 skips; het timeoutbestand rapporteerde 5 groen ondanks twee zichtbare AttributeError-tracebacks.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: CSV auto-validatie en nul-succesfeedback zijn bestaande B039-005/B039-008 en niet opnieuw geteld.

## Bevindingen

### B071-001 — P2 — Container tests depend on prior configuration and environment order

**Bewijs:** Session-scoped ConfigManager warming runs before function-scoped dummy keys, and tests patch OpenAI although Anthropic is default. CI job keys mask the defect.

**Reproductie:** Run the affected tests credential-free in isolation: they fail for a missing Anthropic key; preseed process dummy keys and they pass.

**Aanbevolen oplossing:** Install hermetic keys before session warming, reset ConfigManager per contract and inject fake AI and database dependencies.

### B071-002 — P2 — CSV timeout tests pass after the main flow crashes

**Bewijs:** Tests call a nonexistent container.definition_import attribute, catch and print AttributeError and make no timeout-result or elapsed-time assertion.

**Reproductie:** Run with stdout visible; two tracebacks are printed while all five tests pass.

**Aanbevolen oplossing:** Call import_service with injected dependencies, let unexpected exceptions fail and assert a hard elapsed and cancellation bound plus structured outcome.

### B071-003 — P2 — Entire context payload schema suite is stale and disabled

**Bewijs:** All 24 tests are unconditionally skipped; the schema exists only in tests and fixtures already omit the current required GenerationRequest id.

**Reproductie:** Run the file; 24 tests skip and zero schema assertions execute.

**Aanbevolen oplossing:** Create one runtime schema as the source of truth, derive current fixtures from it and remove the unconditional skips.

### B071-004 — P3 — Metric and container checks claim success without executing behavior

**Bewijs:** The metric test only checks that a callable exists, while a container smoke catches generation failures; neither proves the named behavior.

**Reproductie:** Replace the target body with a failing implementation; the callable-only metric check still passes.

**Aanbevolen oplossing:** Invoke the real metric render and assert output; require container smoke to complete a fake generation without broad exception swallowing.

## Niet getest

- Geen echte CSV-productieimport, credentials of browserfeedback; timeout- en fixturegaten zijn in tijdelijke omgevingen bewezen.
