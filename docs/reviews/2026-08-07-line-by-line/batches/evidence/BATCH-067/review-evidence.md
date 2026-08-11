# BATCH-067 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 4/4 blobs, 1316/1316 fysieke regels en 102/102 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- 236 scoped tests voor B066-B068: 228 groen en 8 skips; cancellation- en edge-contracten zijn aanvullend offline gereproduceerd.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.

## Bevindingen

### B067-001 — P3 — Batch AI API converts child cancellation into an ordinary service error

**Bewijs:** The regression test requires a child CancelledError returned by gather to be wrapped as AIServiceError; outer task cancellation still propagates and no production caller was found.

**Reproductie:** Make one batch child raise CancelledError; batch_generate raises AIServiceError whose cause is the cancellation.

**Aanbevolen oplossing:** Propagate child cancellation and cancel or await siblings; wrap only ordinary failures.

### B067-002 — P3 — Anders edge-case tests accept mutually incompatible outcomes

**Bewijs:** Command input may remain unchanged, bidi text may be kept or removed, large-output checks require only a nonempty list and the memory test has no assertion.

**Reproductie:** Return the unchanged command and arbitrary nonempty large responses; the named safety and limit tests still pass.

**Aanbevolen oplossing:** Define exact sink-specific contracts, enforce widget limits and add a measured memory bound instead of conditional or disjunctive assertions.

## Niet getest

- Geen production caller voor batch_generate gevonden en geen echte provider, netwerk of credentials gebruikt.
