# BATCH-044 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 3/3 blobs, 1175/1175 fysieke regels en 56/56 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatiebestanden zijn niet gewijzigd.

## Verificatie

- 176 primaire gerichte tests en 56 onafhankelijke crosstests groen; metrics/AppTest toonde de credential-eager fout; Ruff en Black schoon.
- De onafhankelijke verifier heeft alle kandidaten gedisponeerd en de P1-codepaden opnieuw beoordeeld.

## Bevindingen

### B044-001 — P2 — Empty RAG selection is converted to the default document set

**Bewijs:** An explicit empty selection becomes None, and the orchestrator interprets falsy input as use session defaults.

**Reproductie:** Select no documents while defaults exist; the handler receives None and default documents are included.

**Aanbevolen oplossing:** Preserve tri-state semantics: None means default and an empty list means none.

### B044-002 — P3 — Timeout metric counts events outside the selected time window

**Bewijs:** timeout_count is incremented before timestamp parsing and cutoff filtering.

**Reproductie:** Parse a log containing only a timeout from 2000 with a 24-hour window; total is zero but timeout_count is one.

**Aanbevolen oplossing:** Parse and filter timestamps before updating any metric counter.

### B044-003 — P2 — Tabbed UI exposes raw exception details

**Bewijs:** The general exception wrapper shows type and message to every user and logs exc_info without a role gate.

**Reproductie:** Raise RuntimeError containing API_KEY=review-secret; the sentinel appears in st.code and logs.

**Aanbevolen oplossing:** Show a generic correlation-ID message and restrict sanitized diagnostics to authorized debug tooling.

### B044-004 — P2 — Cache metrics eagerly require an AI credential

**Bewijs:** A cache-only dashboard requests the full synonym orchestrator, which constructs an AI service.

**Reproductie:** Open metrics with a fake registry and no provider keys; initialization raises API key is required.

**Aanbevolen oplossing:** Expose a credential-free metrics/cache service and initialize AI enrichment lazily.

## Niet getest

- Geen externe AI-call of productie-logbestand gebruikt.
- Visueel contrast, toetsenbord, screenreader, touch en responsive viewports zijn niet met een browserbackend getest.
