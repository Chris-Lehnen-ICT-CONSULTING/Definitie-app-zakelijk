# BATCH-074 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 10/10 blobs, 2045/2045 fysieke regels en 145/145 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- PER-007 direct 5 groen en 5 xfail maar nul unit-gateselecties; de echte PerformanceTracker-sibling suite gaf 22 groen.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: SQLite-resourcewaarschuwingen en eager credentials zijn bestaande B046/B012/PILOT-bevindingen.

## Bevindingen

### B074-001 — P2 — PER-007 anti-pattern gate is excluded from the blocking unit suite

**Bewijs:** The file has only the antipattern marker while make test selects unit; five cases are stale xfails and the passing cases largely inspect local simulations.

**Reproductie:** Run with the unit marker expression: zero tests are selected; run directly: five pass and five xfail.

**Aanbevolen oplossing:** Add the blocking marker and replace local simulations and stale xfails with current production or AST contracts.

### B074-002 — P2 — RAG provenance normalization tests copy rather than call production

**Bewijs:** Three normalization tests rebuild the provenance dictionary locally and never import the active orchestrator branch; the separate renderer tests are valid.

**Reproductie:** Break or remove orchestrator RAG-to-provenance normalization; the three copied normalization tests remain green.

**Aanbevolen oplossing:** Extract one production normalizer and test it directly, plus an orchestrator-to-renderer integration with fake RAG results.

### B074-003 — P3 — Current Streamlit metric wiring is covered only by stale or source-level checks

**Bewijs:** Seven of fifteen wiring cases are skipped for old APIs; active cases mostly search source text and none executes the current _track_streamlit_metrics flow. Separate PerformanceTracker tests remain valid.

**Reproductie:** Run the file and inspect collection: seven cases skip and no test invokes the current main wiring across two reruns.

**Aanbevolen oplossing:** Drive _track_streamlit_metrics with a fake tracker and session state across deterministic reruns and assert exact names, values and regression calls.

## Niet getest

- Geen live Streamlit-reruns, echte RAG/provider of browser/a11y; alleen testwiring en productiecallers zijn gevolgd.
