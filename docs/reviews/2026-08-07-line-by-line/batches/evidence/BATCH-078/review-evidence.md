# BATCH-078 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 4/4 blobs, 1722/1722 fysieke regels en 146/146 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Alle 101 scopetests groen; backupcollision, foutinjectie en gelijkgrote corrupte backup zijn aanvullend gereproduceerd.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: V5-backupcollision is onderscheiden van B010-007, dat ontbrekende WAL-data betreft.

## Bevindingen

### B078-001 — P2 — V5 migration backups overwrite each other within one second

**Bewijs:** Migration backup names have second resolution and every run creates one before checking idempotence; tests assert only that at least one backup exists.

**Reproductie:** Freeze the clock and create two backups after changing the database: paths are equal, the hash changes and only one backup remains.

**Aanbevolen oplossing:** Use exclusive collision-proof names and avoid a backup when the migration is already applied; assert original backup immutability.

### B078-002 — P3 — Working-system tests convert arbitrary total failures into passes

**Bewijs:** Broad catches and tautological assertions accept failures from the validator loader and configuration manager as successful outcomes.

**Reproductie:** Patch either dependency to raise an arbitrary RuntimeError; the named working-system tests still pass.

**Aanbevolen oplossing:** Remove catch-all blocks, use targeted pytest.raises only for documented failures and assert semantic results.

### B078-003 — P3 — Backup verification leaks SQLite connections on corrupt input

**Bewijs:** verify_backup closes its connection only on success, while the existing corrupt-file test fails at the earlier size check.

**Reproductie:** Supply a corrupt database with the expected size; verify_backup returns false and garbage collection emits an unclosed-connection ResourceWarning.

**Aanbevolen oplossing:** Use a closing context manager or finally block and test the equal-size corruption path with warnings treated as errors.

## Niet getest

- Geen productie-DB-migratie of echte deploybackup; alleen tijdelijke SQLite-kopieën en foutinjecties.
