# BATCH-048 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-root`
- Scope: 17/17 blobs, 3870/3870 fysieke regels en 149/149 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- 135 write-safe primaire tests groen; onafhankelijke selectie 99 groen en 2 uitsluitend door ontbrekende providercredentials rood.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: Dubbele logginghandlers zijn canoniek vastgelegd als B049-002; stale helper-LRU's blijven gedekt door B012/PILOT en zijn niet dubbel geteld.

## Bevindingen

### B048-001 — P2 — Structured logging extras bypass PII redaction

**Bewijs:** The filter redacts message fields but the JSON formatter serializes arbitrary LogRecord extras unchanged.

**Reproductie:** Log a neutral message with extra begrip containing an email; the full address appears in JSON.

**Aanbevolen oplossing:** Recursively redact non-standard extras through a schema or sensitive-key policy before formatting.

### B048-002 — P2 — Async rate limiter admits requests too early after a wait

**Bewijs:** The limiter records the timestamp captured before sleep instead of recomputing admission time.

**Reproductie:** With one request per minute and a fake clock, three admissions occur at [0, 60, 60].

**Aanbevolen oplossing:** Recompute monotonic time after every wait and append the actual admission timestamp.

### B048-003 — P2 — Open circuit breaker still invokes the provider once

**Bewijs:** Circuit admission is checked only in the retry decision after the initial attempt.

**Reproductie:** Force the breaker OPEN and call a decorated provider; the provider is invoked once.

**Aanbevolen oplossing:** Check circuit admission before attempt zero and tightly control HALF_OPEN probes.

### B048-004 — P2 — Adaptive retry history omits failed requests

**Bewijs:** Failures increment counters but never create RequestMetrics in request_history.

**Reproductie:** Record one failure and one success; total success is 0.5 while recent success is 1.0 and recent_errors is empty.

**Aanbevolen oplossing:** Record every outcome in one event stream and derive all retry statistics from it.

### B048-005 — P2 — RAG smoke test can reuse unrelated stale chunks

**Bewijs:** A fixed collection name is reused whenever its chunk count is nonzero without source or content validation.

**Reproductie:** Preload the collection with chunks for another source; ingestion is skipped and the stale chunks are tested.

**Aanbevolen oplossing:** Key collections by source/content hash and validate document metadata or create isolated run collections.

### B048-006 — P2 — RAG smoke test can report GO after provider failures

**Bewijs:** Provider errors become text and score zero but do not populate TermResult.error, so failed pairs count as improvements.

**Reproductie:** Return five baseline errors and five RAG successes; analysis reports GO and five improvements.

**Aanbevolen oplossing:** Use typed success/error results and require enough complete, provenance-backed pairs before a verdict.

### B048-007 — P2 — Definition manager exits successfully after failed mutations

**Bewijs:** False mutation outcomes are logged but do not raise or produce a nonzero main result.

**Reproductie:** Mock approve to return False and invoke main; the natural process status is zero.

**Aanbevolen oplossing:** Return typed command results and map false, partial and exceptional outcomes to nonzero exits.

### B048-008 — P2 — Database setup reports ready after every seed insert fails

**Bewijs:** Each insert exception is swallowed and unconditional completion messages follow.

**Reproductie:** Make all seed inserts raise; the function returns normally and logs that the database is ready.

**Aanbevolen oplossing:** Use a transaction or explicit partial result and exit nonzero without a readiness claim.

### B048-009 — P3 — Async batch helper returns completion order

**Bewijs:** The docstring promises input order but results are appended from asyncio.as_completed.

**Reproductie:** Run a slow item followed by a fast item; output is ['fast', 'slow'].

**Aanbevolen oplossing:** Index tasks and preallocate results or use gather; test order and exceptions.

### B048-010 — P3 — Example alias selection depends on hash seed

**Bewijs:** Alias selection and iteration use sets, so precedence and list order vary by process hash seed.

**Reproductie:** Format a dict with canonical and alternate aliases in multiple hash-seeded processes; different values win.

**Aanbevolen oplossing:** Use ordered alias tuples with canonical precedence and deterministic iteration.

### B048-011 — P3 — Definition manager renders a valid zero score as missing

**Bewijs:** Truthiness is used instead of a None check for numeric scores.

**Reproductie:** Render score 0.0; the CLI shows Score: N/A.

**Aanbevolen oplossing:** Use is not None and test zero, None and positive values.

## Niet getest

- Geen echte AI/429, persistente CLI/DB/RAG-mutatie, multiprocess logrotatie of OS-subprocesexit; geen UI-bestanden in scope.
