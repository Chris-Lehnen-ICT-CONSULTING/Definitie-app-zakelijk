# BATCH-085 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 13/13 blobs, 2536/2536 fysieke regels en 135/135 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Exacte run: 62 groen, 15 rood, 2 skips en 5 xfails; correct-root compliance gaf 6 groen/14 rood en CI-contracten 27 groen/2 skips.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: Migratie-009-testschuld is thematisch verwant aan B051 maar betreft een afzonderlijk script en suite.

## Bevindingen

### B085-001 — P2 — Documentation compliance suites resolve the repository root incorrectly

**Bewijs:** Both compliance suites resolve tests/integration as the base, vacuously pass several missing-directory checks and are explicitly deselected in CI; correcting the root exposes stale expectations too.

**Reproductie:** Base run returns 15 failures and 5 passes; correct the root at runtime and it returns 14 failures and 6 passes, while CI deselects both files.

**Aanbevolen oplossing:** Use a central asserted repository root, fail broken links, update the actual documentation contract and remove CI deselection.

### B085-002 — P2 — ASTRA/NORA compliance suite contains assertion-free security claims

**Bewijs:** Twelve tests contain only a docstring, pass or bare literal; input and injection loops make no assertions, and five stale contracts are non-strict xfail.

**Reproductie:** The suite reports 18 passes and 5 xfails while script HTML round-trips unchanged and invalid values are coerced or ignored without a failing assertion.

**Aanbevolen oplossing:** Bind every compliance claim to production behavior, add exact assertions and make any remaining xfails strict and current.

### B085-003 — P2 — Required contract job remains green when fixtures and offline tests skip

**Bewijs:** The golden fixture is absent and triggers skip; a module-level dummy-key skip also removes five examples tests, including three that need no provider, with no unexpected-skip gate.

**Reproductie:** Run the CI-like contract subset with dummy keys: 27 pass and two module skips while the required contracts are not executed.

**Aanbevolen oplossing:** Commit and require the fixture, import mandatory modules directly, split online smoke from offline contracts and fail CI on unexpected skips.

### B085-004 — P2 — Degraded validation contract swallows schema rejection

**Bewijs:** A broad exception handler catches jsonschema validation failures, so malformed results do not fail the contract test.

**Reproductie:** Patch jsonschema.validate to raise ValidationError; the test prints the rejection marker and exits green.

**Aanbevolen oplossing:** Make jsonschema mandatory, assert the schema is loaded and execute validation outside broad catches.

### B085-005 — P2 — Migration 009 suite never executes the migration it names

**Bewijs:** Fixtures create the current schema directly and never read or run 009_remove_unique_index.sql; the force-generate case calls production but has no assertions that generation or save succeeded.

**Reproductie:** Run all 13 tests with the migration SQL empty or untouched; they pass because the file is never opened, and force generation can finish green with no saved record.

**Aanbevolen oplossing:** Build a pre-009 database, execute the exact migration blob and assert index/data/rollback/idempotence; use offline fakes and assert force generation and persistence.

## Niet getest

- Geen echte provider, netwerk, productie-DB-migratie of browser; één providerpad werd onbedoeld aangeroepen maar sandbox/DNS blokkeerde alle outbound verbindingen.
