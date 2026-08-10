# BATCH-049 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 7/7 blobs, 1454/1454 fysieke regels en 80/80 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Gecombineerde kandidaatselectie voor B049/B051/B052/B053: 185 groen en 1 verwachte xfail; offline reproducties bevestigden de queue-, logging-, HMAC- en cachegevallen.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.

## Bevindingen

### B049-001 — P2 — Durable retry queue cannot persist or replay failed requests

**Bewijs:** FailedRequest is not serializable, loaded dictionaries are treated as objects and background retry only increments retry_count.

**Reproductie:** Persist a failed request or load a queue row and run background retry; serialization or attribute access fails and no real replay occurs.

**Aanbevolen oplossing:** Define a versioned durable schema and a real replay callback with atomic state transitions and recovery tests.

### B049-002 — P2 — Repeated logging bootstrap installs duplicate handlers

**Bewijs:** Each setup call adds another structured FileHandler without detecting an equivalent existing handler.

**Reproductie:** Call logging bootstrap twice and emit one message; two structured handlers produce duplicate output.

**Aanbevolen oplossing:** Make setup idempotent by resolved target and handler type, close replaced handlers and test reruns.

### B049-003 — P2 — Concurrent serializer startup creates incompatible HMAC keys

**Bewijs:** Key creation is a check-then-write race; concurrent initializers can return different keys while only one remains on disk.

**Reproductie:** Start two initializers at the missing-key barrier; compare both returned keys with the persisted key.

**Aanbevolen oplossing:** Create the key atomically with exclusive open, verify permissions and reread the winning key.

### B049-004 — P3 — Fallback cache keys collide across functions

**Bewijs:** The cache key contains only func.__name__ and arguments, not the module or qualified name.

**Reproductie:** Decorate two same-named functions with equal arguments; one can receive the other's cached fallback.

**Aanbevolen oplossing:** Include module, qualname, schema version and canonical arguments in the key.

## Niet getest

- Geen duurzame productiequeue, multiprocess sleutelrotatie of live fallbackverkeer; alle concurrencygevallen zijn hermetisch gereproduceerd.
