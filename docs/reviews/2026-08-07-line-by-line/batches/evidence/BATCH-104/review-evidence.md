# BATCH-104 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-root`
- Scope: 20/20 blobs, 2728/2728 fysieke regels en 64/64 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- De relevante mypy-ratchettests gaven 34/34 groen; Ruff, Black, Python-compile en bash -n waren schoon voor de toepasselijke scope.
- Object-ID's, EOF-ranges, line owners en symbol-memberships matchten het batchmanifest exact.

## Bevindingen

### B104-001 — P1 — Orphan cleanup drops backup tables even when restore refused rows

**Bewijs:** Restore skips rows whose destination IDs already exist, but --cleanup then drops old/old2 tables without proving every backup row was restored. The primary temp repro confirmed skipped rows followed by table deletion (setup/selection at lines 28-50).

**Reproductie:** Create destination and old backup tables with a colliding ID, run --cleanup, and verify the backup table is gone while its distinct backup content was not restored.

**Aanbevolen oplossing:** Create an exact restore ledger, refuse cleanup unless every row is verified equivalent/restored, and keep backup tables on any skip/error.

### B104-002 — P2 — Recovery tool auto-confirms live writes in non-interactive sessions

**Bewijs:** The confirmation path treats non-TTY input as approval, so running from CI/redirected stdin performs database writes without an explicit --execute flag.

**Reproductie:** Run the tool against temp data with stdin redirected from /dev/null and no execute flag; inspect changed rows.

**Aanbevolen oplossing:** Default non-interactive mode to refusal/dry-run and require --execute plus explicit target confirmation for writes.

### B104-003 — P2 — Endpoint smoke script prints total failures but exits zero

**Bewijs:** Endpoint/classifier/export/live-probe errors and empty results are accumulated/printed, but no failing exit is propagated (setup/request paths at lines 32-54).

**Reproductie:** Stub every request to fail or return empty, run the script offline, and compare the printed failures with exit code 0.

**Aanbevolen oplossing:** Return nonzero for any required endpoint failure/empty contract, separate optional live probes, and add mocked deterministic assertions.

### B104-004 — P3 — Monitoring test runner targets a nonexistent test directory

**Bewijs:** The runner invokes pytest on tests/monitoring/, absent in the immutable base; pytest reports no collection/exit 4 while the wrapper does not provide a meaningful monitoring test result.

**Reproductie:** Run the script or its pytest command from the immutable base and inspect collected tests and exit status.

**Aanbevolen oplossing:** Point to maintained tests, fail clearly when zero tests collect, and cover the runner in CI.

### B104-005 — P3 — MVP test ignores --no-cleanup and lacks signal cleanup traps

**Bewijs:** The parsed no-cleanup state is never consulted; lines 291-329 always stop services, and no EXIT/INT/TERM trap guarantees cleanup on interruption.

**Reproductie:** Run with --no-cleanup using stub service commands, and interrupt during a test; inspect stop calls/remaining processes.

**Aanbevolen oplossing:** Honor the option, register cleanup traps before startup, track PIDs, and test normal and interrupted lifecycles.

### B104-006 — P3 — Rebuild dashboard is placeholder-only and keyboard-inaccessible

**Bewijs:** Search has no filtering behavior, sortable headers are click-only th elements without keyboard semantics, SVG lacks an accessible name, and fixed widths/overflow impair responsive use. The rebuild UI is dormant; browser and screen-reader behavior were not executed.

**Reproductie:** Open the static file offline, type in search, tab through sort controls, inspect the accessibility tree and resize to a narrow viewport.

**Aanbevolen oplossing:** Implement filtering, use buttons inside headers with aria-sort and keyboard support, name decorative/informative SVG correctly, and use responsive CSS plus automated/manual a11y tests.

## Niet getest

- Geen productie-DB, GitHub writes, externe API, Docker/Redis/launchd of actieve browser; migratie- en recoveryrepro's gebruikten tijdelijke SQLite-data.
