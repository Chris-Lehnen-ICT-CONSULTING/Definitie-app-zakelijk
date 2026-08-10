# BATCH-039 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 14/14 blobs, 3998/3998 fysieke regels en 125/125 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatiebestanden zijn niet gewijzigd.

## Verificatie

- 253 relevante unit-tests groen (7 skips), 23 integratietests groen (2 skips); workflow- en exportreproducties offline uitgevoerd; Ruff en Black schoon.
- De onafhankelijke verifier heeft alle kandidaten gedisponeerd en de P1-codepaden opnieuw beoordeeld.

## Bevindingen

### B039-001 — P1 — Direct status adapter bypasses workflow transition policy

**Bewijs:** A public adapter mutates status without enforcing the role and transition checks used by the workflow path.

**Reproductie:** Call the adapter with a transition rejected by the policy API; the direct update path accepts it.

**Aanbevolen oplossing:** Expose one authoritative transition command and enforce role, state and audit invariants at the service boundary.

### B039-002 — P1 — Critical workflow validation issues can pass the gate

**Bewijs:** The gate reads severity while validation results expose severity_level, so critical results are not recognized.

**Reproductie:** Pass a result containing only severity_level=critical; the gate does not block it.

**Aanbevolen oplossing:** Use one typed validation result schema and fail closed on unknown or critical severities.

### B039-003 — P2 — Configured soft score gate is unreachable

**Bewijs:** Earlier branches return before the configurable soft-score path, contradicting the documented policy.

**Reproductie:** Exercise scores around the configured threshold and trace the returned branch; the soft gate is never authoritative.

**Aanbevolen oplossing:** Define one ordered gate policy and cover every configured threshold boundary.

### B039-004 — P2 — Workflow mutation commits before audit and can return false failure

**Bewijs:** The definition update is committed before audit/event writes that can fail independently.

**Reproductie:** Make the audit writer fail after a successful update; the method reports failure although the mutation persists.

**Aanbevolen oplossing:** Write state, history and event atomically or return a structured partial-commit result with reconciliation.

### B039-005 — P2 — CSV auto-validation does not enforce preview outcomes

**Bewijs:** The active UI path labels the import auto-validated but does not reject invalid previews; the dormant service also ignores preview outcome.

**Reproductie:** Import a row whose preview reports invalid and observe that processing continues.

**Aanbevolen oplossing:** Make preview validity and conflict strategy explicit preconditions for every persisted row.

### B039-006 — P2 — TXT export ignores output directory and fails on slash terms

**Bewijs:** TXT path creation uses the raw term and bypasses the configured export directory.

**Reproductie:** Export a term containing a slash with a temporary configured directory; path creation escapes the expected filename structure and fails.

**Aanbevolen oplossing:** Use the configured directory, a shared safe slug function and atomic writes.

### B039-007 — P3 — Export drops zero scores and uses inconsistent history slugs

**Bewijs:** Falsy-value handling converts 0.0 to missing and history naming differs from the main export slug.

**Reproductie:** Export a record with score 0.0 and compare current/history filenames; the score is absent and slugs diverge.

**Aanbevolen oplossing:** Distinguish None from zero and reuse one canonical filename builder.

### B039-008 — P3 — Partial CSV import is announced as full success

**Bewijs:** Any nonzero success count triggers a success message even when other rows fail.

**Reproductie:** Process one valid and one invalid row; the UI announces success without an overall partial-failure state.

**Aanbevolen oplossing:** Report succeeded, failed and skipped counts and retain per-row errors before rerun.

### B040-004 — P3 — Cache dashboard expects an incompatible statistics schema

**Bewijs:** The UI reads field names and nesting not returned by the cache implementation.

**Reproductie:** Render the dashboard with real cache statistics; expected values are missing or defaulted.

**Aanbevolen oplossing:** Define a typed shared statistics contract and render unavailable fields explicitly.

### B040-012 — P3 — Cache UI is English and clears data without confirmation

**Bewijs:** The Dutch application exposes English labels and a destructive clear action without a stable confirmation step.

**Reproductie:** Render the dormant cache manager and click clear; deletion is invoked immediately.

**Aanbevolen oplossing:** Localize the UI and require a persistent, descriptive confirmation state.

## Niet getest

- Geen productie-DB, echte importbestanden of muterende gebruikersdata gebruikt.
- Visueel contrast, toetsenbord, screenreader, touch en responsive viewports zijn niet met een browserbackend getest.
