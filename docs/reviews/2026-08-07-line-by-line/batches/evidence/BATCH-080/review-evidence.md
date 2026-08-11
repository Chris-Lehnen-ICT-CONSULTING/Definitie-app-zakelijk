# BATCH-080 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-root`
- Scope: 5/5 blobs, 1503/1503 fysieke regels en 128/128 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Volledige B079-B081-selectie gaf 330 groen; twee verschillende 120-ms cachekeys namen onafhankelijk circa 251 ms door globale serialisatie.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.

## Bevindingen

### B080-001 — P2 — Autouse cache fixture clears the repository-relative runtime cache

**Bewijs:** Every test configures the global cache at literal cache and calls clear_cache before and after, so running from the repository can remove real ignored cache entries.

**Reproductie:** Place a cache entry in an isolated repository-shaped directory and run the fixture; the entry is removed during setup or teardown.

**Aanbevolen oplossing:** Use tmp_path and restore the previous global backend without touching repository-relative runtime state.

### B080-002 — P3 — Cached decorator serializes independent cache keys

**Bewijs:** The test explicitly calls function-level serialization acceptable and asserts only that both keys execute; production uses one lock for every key of a decorated function.

**Reproductie:** Run two uncached keys whose bodies each sleep 120 ms; total elapsed is about 251 ms instead of one parallel interval.

**Aanbevolen oplossing:** Use per-key single-flight locks with bounded lifecycle and assert different keys overlap while identical keys execute once.

## Niet getest

- Geen multiprocess cacheload of grote performancebenchmark; threadtiming en testpaden zijn lokaal bewezen.
