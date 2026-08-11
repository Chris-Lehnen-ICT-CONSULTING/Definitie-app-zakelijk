# BATCH-103 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-root`
- Scope: 19/19 blobs, 3979/3979 fysieke regels en 102/102 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- De relevante mypy-ratchettests gaven 34/34 groen; Ruff, Black, Python-compile en bash -n waren schoon voor de toepasselijke scope.
- Object-ID's, EOF-ranges, line owners en symbol-memberships matchten het batchmanifest exact.

## Bevindingen

### B103-001 — P2 — Default migration can self-migrate and report a successful no-op

**Bewijs:** Source and target defaults can resolve to the same database; skipped duplicates and later self-comparison (supporting lines 268-273,336-341,387-435,504-512,567-579) produce a zero-migration success.

**Reproductie:** Run with defaults against a temp copy where source and target resolve identically; observe duplicates skipped, verification against itself and success.

**Aanbevolen oplossing:** Reject identical resolved paths/inodes, require explicit target, and verify copied IDs/counts against a pre-migration snapshot.

### B103-002 — P3 — Migration CLI opens its log before creating logs/

**Bewijs:** FileHandler is configured at import, while logs mkdir happens only at lines 598-604. From a fresh cwd, --help exits 1 before argument parsing.

**Reproductie:** cd to an empty temp directory and invoke the absolute script with --help.

**Aanbevolen oplossing:** Initialize logging after creating an explicit log directory; keep --help side-effect-free.

### B103-003 — P1 — Synonym migration rollback deletes unrelated human data and leaves migrated data behind

**Bewijs:** Rollback is group-based rather than exact-membership based: a later human member in a migration-created group is removed, while a migrated member added to a pre-existing group survives. The resulting state is neither the original nor a full rollback.

**Reproductie:** In temp tables, migrate one term into a new group and one into an existing group, add a human member to the new group, then execute rollback and inspect memberships.

**Aanbevolen oplossing:** Persist an exact migration ledger and reverse only rows created/changed by that run in one transaction, preserving later and pre-existing memberships.

### B103-004 — P2 — Presence of one synonym table skips the entire table migration

**Bewijs:** The all-or-nothing existence guard returns when any expected table already exists; creation logic at lines 145-158 is therefore skipped for the missing tables.

**Reproductie:** Create a temp database with only one of the synonym tables and run the migration; query sqlite_master afterward.

**Aanbevolen oplossing:** Create/check each table and index independently in an idempotent transaction, then validate the complete schema.

### B103-005 — P2 — History-tab maintenance scripts target the original checkout

**Bewijs:** The main fixer hardcodes the original project path; related shell/remove-legacy/verify tools do likewise, so an isolated invocation can mutate another worktree.

**Reproductie:** Invoke from a different temp/worktree in dry/inspection mode and compare cwd with resolved target.

**Aanbevolen oplossing:** Resolve and validate an explicit repository root, prohibit cross-root writes, and test worktree isolation.

### B103-006 — P3 — Monitoring cleanup trap is installed after blocking tail

**Bewijs:** The script begins a blocking tail before registering its cleanup trap, so termination during that phase bypasses scripted cleanup; actual orphan behavior depends on platform/process semantics.

**Reproductie:** Run against a temp log with a stub child process, terminate while in the initial tail, and inspect whether cleanup ran.

**Aanbevolen oplossing:** Install EXIT/INT/TERM traps before starting any child/background/blocking command and track child PIDs explicitly.

## Niet getest

- Geen productie-DB, GitHub writes, externe API, Docker/Redis/launchd of actieve browser; migratie- en recoveryrepro's gebruikten tijdelijke SQLite-data.
