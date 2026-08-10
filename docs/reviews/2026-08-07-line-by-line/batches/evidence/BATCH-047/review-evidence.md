# BATCH-047 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 15/15 blobs, 3441/3441 fysieke regels en 147/147 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Gerichte primaire reproducties uitgevoerd; onafhankelijke selectie 31 groen en 1 skip. De feature-flagfocus gaf bewust 1 groen en 2 contractfailures als defectbewijs.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.

## Bevindingen

### B047-001 — P1 — JSON export fails on aggregated datetime metadata

**Bewijs:** The aggregator places a datetime in metadata and the real JSON export uses json.dump without an encoder.

**Reproductie:** Aggregate a record with a datetime created_at and export it as JSON; TypeError says datetime is not serializable.

**Aanbevolen oplossing:** Serialize metadata to the export schema at the boundary and add an end-to-end JSON export test.

### B047-002 — P1 — Definition edits erase process explanation

**Bewijs:** Reconstruction omits toelichting_proces and the repository explicitly writes the resulting None.

**Reproductie:** Edit an existing definition with toelichting_proces populated; the saved object has that field set to None.

**Aanbevolen oplossing:** Use dataclasses.replace or a complete patch model and test preservation of every non-edited field.

### B047-003 — P1 — Invalid approval thresholds can bypass quality gates

**Bewijs:** NaN, negative and unbounded thresholds are accepted; comparisons with NaN can make low scores pass.

**Reproductie:** Configure a NaN soft threshold and evaluate score 0; the approval gate passes.

**Aanbevolen oplossing:** Validate finite ordered thresholds with 0 <= soft <= hard <= 1 and fail closed.

### B047-004 — P2 — Feature-flag rollout API contradicts its own tests

**Bewijs:** Focused flag tests produce one pass and two failures; percentage parsing and canary behavior do not meet the asserted API contract.

**Reproductie:** Run the focused feature-flag tests; two contract assertions fail.

**Aanbevolen oplossing:** Choose one public rollout contract, implement it consistently and add deterministic golden cases.

### B047-005 — P2 — AI token and cost accounting omits the system prompt

**Bewijs:** Usage estimation counts user content but not the system prompt sent to the provider.

**Reproductie:** Send a large system prompt with a small user prompt and inspect recorded tokens and cost; the system portion is absent.

**Aanbevolen oplossing:** Measure provider-reported usage or count every transmitted message and test cost reconciliation.

### B047-006 — P2 — Context update deadlocks on its own non-reentrant lock

**Bewijs:** update_context acquires Lock and calls set_context, which tries to acquire the same lock again.

**Reproductie:** Call update_context on the public manager under a timeout; the call never returns.

**Aanbevolen oplossing:** Avoid nested acquisition or use one locked private mutation primitive; add a timeout regression.

### B047-007 — P2 — Bulk definition replacement can partially save destructive edits

**Bewijs:** Empty search terms expand replacement positions and individual saves are not one transaction.

**Reproductie:** Call the public replacement method with an empty search term and make a later save fail; earlier changes remain.

**Aanbevolen oplossing:** Reject empty search input and execute the batch atomically with rollback and a structured result.

### B047-008 — P3 — Feature canaries depend on process-random hash state

**Bewijs:** Built-in hash changes across processes and a numeric percentage environment value does not enable the feature as expected.

**Reproductie:** Evaluate the same canary key in processes with different hash seeds; assignments differ.

**Aanbevolen oplossing:** Use a stable cryptographic hash and a validated percentage configuration schema.

### B047-009 — P3 — A/B framework fabricates legacy comparison results

**Bewijs:** The legacy arm and recommendations are synthesized rather than produced by a real comparable implementation.

**Reproductie:** Run a comparison with a controlled treatment; the legacy result is a generated placeholder.

**Aanbevolen oplossing:** Require two real implementations or label the framework as a simulation and exclude it from quality decisions.

### B047-010 — P3 — Service context adapter silently drops arbitrary context

**Bewijs:** The adapter maps a fixed subset and ignores the supplied key and unknown context fields.

**Reproductie:** Provide an extra context key through the public adapter; it is absent from the output.

**Aanbevolen oplossing:** Define a strict input schema or preserve documented extension fields and test round trips.

## Niet getest

- Geen echte AI-provider, productie-DB-mutatie of browserflow; dormant feature-, context- en A/B-API's zijn geïsoleerd beoordeeld.
