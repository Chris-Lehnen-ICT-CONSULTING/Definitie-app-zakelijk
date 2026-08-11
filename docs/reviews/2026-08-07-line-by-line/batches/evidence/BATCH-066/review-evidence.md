# BATCH-066 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 3/3 blobs, 1886/1886 fysieke regels en 120/120 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- 236 scoped tests voor B066-B068: 228 groen en 8 expliciete skips; Wikipedia-mocks produceerden 13 relevante async/resourcewaarschuwingen.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.

## Bevindingen

### B066-001 — P3 — Wikipedia limiter releases concurrent requests together

**Bewijs:** The sequential timing test misses that the shared timestamp is read and updated without a lock; four concurrent admissions complete in one interval.

**Reproductie:** Gather four _rate_limit calls with a 50 ms delay; all complete in 0.051 seconds instead of being spaced across about 0.20 seconds.

**Aanbevolen oplossing:** Protect admission with an asyncio lock and monotonic next-allowed timestamp, then test concurrent spacing.

### B066-002 — P3 — Empty Wikipedia term still invokes both source paths

**Bewijs:** The permissive empty-input test opens the extractor; production has no whitespace guard and calls both redirect and disambiguation methods.

**Reproductie:** Mock both source methods and call extract_synonyms with an empty term; each is awaited once.

**Aanbevolen oplossing:** Return an empty result before session or network work for blank terms and assert zero source calls.

### B066-003 — P2 — Wikipedia tests pass through broken async HTTP mocks and leaked sessions

**Bewijs:** Tests replace an entered real ClientSession and make session.get an AsyncMock although async-with requires a synchronously returned context manager; errors become empty lists and assertions pass vacuously.

**Reproductie:** Run the file with warnings visible; it passes while emitting unawaited-coroutine and unclosed-client-session warnings.

**Aanbevolen oplossing:** Inject a session factory, use a synchronous get mock returning an async context manager and require exact nonempty results and close calls.

### B066-004 — P3 — Synonym facade tests leave the process singleton bound to a fake

**Bewijs:** Singleton tests clear before construction but never restore afterwards; the suite-wide reset fixture does not reset synonym_service._singleton.

**Reproductie:** Create the facade with a fake orchestrator and request it later with a replacement; the same facade and original fake remain.

**Aanbevolen oplossing:** Use a yield fixture that restores the singleton before and after each test or remove the redundant global cache.

### B066-005 — P3 — Supported FAST_SLEEP mode invalidates an unmarked wall-clock test

**Bewijs:** The test requires a real 200 ms sleep but is not marked slow or performance, while the supported FAST_SLEEP fixture reduces unmarked sleeps to zero.

**Reproductie:** Run the test with FAST_SLEEP=1; elapsed time is near zero and the lower-bound assertion fails.

**Aanbevolen oplossing:** Use a fake monotonic clock and sleep-call assertions, or correctly exempt the timing test from FAST_SLEEP.

## Niet getest

- Geen echte Wikipedia-, AI- of providercall; lege-term- en limiterproeven waren volledig gemockt. Geen browser/a11y/responsive test.
