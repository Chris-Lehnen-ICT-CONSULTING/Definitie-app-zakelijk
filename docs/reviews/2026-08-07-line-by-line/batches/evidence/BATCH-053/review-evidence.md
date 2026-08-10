# BATCH-053 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 10/10 blobs, 2066/2066 fysieke regels en 149/149 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Gecombineerde kandidaatselectie voor B049/B051/B052/B053: 185 groen en 1 verwachte xfail; de unit-markerselectie reproduceerde 24 deselecties en exitcode 5.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: De test die ruwe degraded exceptions verwacht ondersteunt de reeds bestaande B023-006 en is niet opnieuw geteld.

## Bevindingen

### B053-001 — P2 — Multi-collection RAG test never invokes production orchestration

**Bewijs:** The test copies a branch into local test logic and does not import or call the orchestrator method it claims to cover.

**Reproductie:** Break the production multi-collection branch; this test remains green because it executes only its copy.

**Aanbevolen oplossing:** Exercise the real orchestrator with fakes and assert the exact collection routing and result.

### B053-002 — P2 — Definition-task transformation suite is excluded from the unit gate

**Bewijs:** The file is marked only red_phase, so the project's pytest -m unit gate deselects all 24 tests and exits with no tests selected.

**Reproductie:** Run this file with the unit marker; all cases are deselected.

**Aanbevolen oplossing:** Add the unit marker and replace conditional or vacuous assertions with exact behavior checks.

### B053-003 — P3 — Expertise transformation assertions allow unrelated output

**Bewijs:** Broad substring and conditional assertions do not prove the requested expertise transformation contract.

**Reproductie:** Return generic nonempty expertise text containing an accepted token; multiple tests remain green.

**Aanbevolen oplossing:** Assert exact required sections, forbidden legacy wording and deterministic transformations.

## Niet getest

- Geen echte RAG/providerflow; de tests zijn beoordeeld op bereik en bewijskracht.
