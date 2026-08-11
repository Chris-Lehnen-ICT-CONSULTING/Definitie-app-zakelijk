# BATCH-092 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-root`
- Scope: 10/10 blobs, 2895/2895 fysieke regels en 149/149 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Zonder het reeds bekende import-time logblok: 69 groen, 12 rood, 1 skip en 3 xfails; de synoniemenvalidator gaf 30 groen/1 rood.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: De import-time synonym-logfile is exact B017-001 en daarom niet opnieuw als B092-finding geregistreerd.

## Bevindingen

### B092-001 — P2 — UI integration module executes side effects but collects zero tests

**Bewijs:** All imports and constructions run at module scope, exceptions are printed and no test_* function exists.

**Reproductie:** pytest --collect-only exits 5 with zero tests and an unclosed SQLite ResourceWarning.

**Aanbevolen oplossing:** Write real fixture-based tests with assertions and resource teardown or move the script to manual diagnostics.

### B092-003 — P2 — Synonym validator coerces non-string entries before type checking

**Bewijs:** parse_synonym_entry turns integer 123 into string before the later non-string validation, making the error branch unreachable.

**Reproductie:** validate_duplicates_within_hoofdterm with [valid, 123, also valid] returns no errors; the focused test fails.

**Aanbevolen oplossing:** Preserve original types and accept only strings or a strict weighted-entry schema.

### B092-004 — P3 — Example validation chain listens to the wrong logger

**Bewijs:** The tests capture database.definitie_repository while save_voorbeelden logs through the examples repository.

**Reproductie:** Run the two logging cases: records save successfully but expected messages are absent.

**Aanbevolen oplossing:** Capture the actual logger and prioritize database/audit invariants over stale logger names.

## Niet getest

- Geen echte provider, netwerk, productie-DB of browser; import-time side effects zijn niet opnieuw geactiveerd buiten veilige isolatie.
