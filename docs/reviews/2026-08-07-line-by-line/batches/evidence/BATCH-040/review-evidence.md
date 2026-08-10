# BATCH-040 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 7/7 blobs, 3368/3368 fysieke regels en 136/136 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatiebestanden zijn niet gewijzigd.

## Verificatie

- 253 relevante unit-tests groen (7 skips), 23 integratietests groen (2 skips); cache- en voorbeeldreproducties op tijdelijke data; Ruff en Black schoon.
- De onafhankelijke verifier heeft alle kandidaten gedisponeerd en de P1-codepaden opnieuw beoordeeld.

## Bevindingen

### B040-001 — P2 — Cache deserializes pickle payloads

**Bewijs:** Cache reads pass stored bytes to pickle.load, which executes reducer code before error handling.

**Reproductie:** Load a benign reducer payload from a temporary cache and observe its marker execute.

**Aanbevolen oplossing:** Replace pickle with a versioned strict data schema; treat cache write access as a security boundary.

### B040-002 — P3 — Raw cache keys can escape the cache directory

**Bewijs:** The public cache API joins caller-controlled keys into filesystem paths without containment checks.

**Reproductie:** Call the low-level API with a ../ key against a temporary root and inspect the resolved outside path.

**Aanbevolen oplossing:** Hash keys or reject separators and verify the resolved path remains under the cache root.

### B040-003 — P3 — Expired cache cleanup leaves payload orphans

**Bewijs:** Expiry handling removes metadata but not the associated payload file.

**Reproductie:** Create an expired entry in a temporary cache and read it; its payload remains on disk.

**Aanbevolen oplossing:** Delete metadata and payload atomically and add orphan reconciliation.

### B040-005 — P2 — Example comparison repeatedly persists unchanged examples

**Bewijs:** Canonicalized and stored example representations are compared with incompatible shapes.

**Reproductie:** Render and save an unchanged example set twice; the second pass still reports and writes a change.

**Aanbevolen oplossing:** Normalize both sides to one stable schema before equality and persistence.

### B040-006 — P2 — Async example batches bypass temperature and observability

**Bewijs:** The async batch path skips configured temperature, statistics and debug accounting used by the single path.

**Reproductie:** Run equivalent single and async requests with a captured client; batch options and counters differ.

**Aanbevolen oplossing:** Route both through one request builder and one instrumentation path.

### B040-007 — P2 — Duplicate display labels export the wrong definition

**Bewijs:** Selection maps human-readable labels back to records, so duplicate labels collide and defaults can stay stale.

**Reproductie:** Provide two definitions with the same label and select the second; the first mapping is exported.

**Aanbevolen oplossing:** Use stable record IDs as widget values and refresh selection state when data changes.

### B040-008 — P2 — Async cache misses stampede the producer

**Bewijs:** Concurrent misses check and compute independently without a per-key single-flight guard.

**Reproductie:** Launch concurrent awaits for one uncached key and count producer calls; it runs multiple times.

**Aanbevolen oplossing:** Add per-key async single-flight locking and propagate one result or exception.

### B040-009 — P3 — Timeout can leave example worker running

**Bewijs:** Timeout handling returns while worker cancellation and teardown are not proven to stop the underlying provider call.

**Reproductie:** A real blocking provider cancellation test was not run; code inspection shows no cooperative stop contract.

**Aanbevolen oplossing:** Use cancellable async provider calls and verify bounded teardown under timeout.

### B040-011 — P3 — Example success rate can become negative

**Bewijs:** Failure accounting can exceed the denominator and the percentage is not clamped or invariant-checked.

**Reproductie:** Feed counters with retries/failures exceeding completed requests; the calculated rate is below zero.

**Aanbevolen oplossing:** Define counter invariants and clamp only after rejecting inconsistent state.

## Niet getest

- Geen echte providercall; workerstranding bij een echte niet-coöperatieve SDK bleef suspected.
- Visueel contrast, toetsenbord, screenreader, touch en responsive viewports zijn niet met een browserbackend getest.
