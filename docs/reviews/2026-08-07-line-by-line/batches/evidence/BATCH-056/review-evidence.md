# BATCH-056 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 4/4 blobs, 1493/1493 fysieke regels en 148/148 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- 319 scoped tests groen voor B056-B058; dimensie- en truncatiegrenzen zijn aanvullend met temp-SQLite en mutatieproeven bewezen.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: B058-004 is samengevoegd met bestaande schema-driftfinding B010-005 en niet dubbel geteld.

## Bevindingen

### B056-001 — P2 — Legacy collections accept incompatible embedding dimensions

**Bewijs:** The test codifies dimension-free legacy writes; a 999-dimensional stored vector later crashes a 3072-dimensional search.

**Reproductie:** Create a collection with NULL metadata, store 999 dimensions and search with 3072; storage succeeds and NumPy raises a dimension mismatch.

**Aanbevolen oplossing:** Backfill or atomically infer legacy dimensions and validate every write, query and stored blob before matrix construction.

### B056-002 — P3 — Embedding truncation tests do not inspect provider input

**Bewijs:** The tests assert only a warning, so a truncator that logs but returns all 120000 characters still passes.

**Reproductie:** Patch truncation to warn and return the original text; the existing assertions pass while the API mock receives the oversized input.

**Aanbevolen oplossing:** Assert the exact provider input and token limit for single and batch requests, plus byte-identical short input.

## Niet getest

- Geen echte OpenAI-call, grote legacyproductiedatabase of browserflow; de dimensiecrash is met tijdelijke SQLite bewezen.
