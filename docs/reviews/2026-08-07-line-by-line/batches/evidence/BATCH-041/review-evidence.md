# BATCH-041 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 17/17 blobs, 3994/3994 fysieke regels en 148/148 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatiebestanden zijn niet gewijzigd.

## Verificatie

- 250 gerichte unit-tests groen (1 skip) en 165 onafhankelijke crosstests groen; UI-helpers met mocks en tijdelijke bestanden gereproduceerd; Ruff en Black schoon.
- De onafhankelijke verifier heeft alle kandidaten gedisponeerd en de P1-codepaden opnieuw beoordeeld.

## Bevindingen

### B041-001 — P2 — RAG uploads can overwrite files across collections

**Bewijs:** Filename uses second-level time plus sanitized basename in one global directory while duplicate checks are collection-local.

**Reproductie:** Upload the same name to two collections in one second; both paths are equal and the second bytes replace the first.

**Aanbevolen oplossing:** Use an immutable UUID or content hash with exclusive atomic creation and ownership-aware cleanup.

### B041-002 — P1 — Examples from the last generation leak into another record

**Bewijs:** last_generation_result is preferred without matching saved definition ID or term.

**Reproductie:** Open record 101 while session result belongs to 202; examples from 202 are cached under 101 without a DB read.

**Aanbevolen oplossing:** Require stable ID/term equality and prefer the target record's persisted examples.

### B041-003 — P2 — Async bridge timeout still waits for the worker

**Bewijs:** future.result times out but leaving the executor context waits for the running task.

**Reproductie:** Run a 0.20-second coroutine with a 0.01-second timeout; TimeoutError returns only after about 0.20 seconds.

**Aanbevolen oplossing:** Keep the path async or use a cancellable persistent worker with nonblocking shutdown.

### B041-004 — P2 — RAG search results persist across collection changes

**Bewijs:** Results use one global session key and are not tagged or cleared by collection.

**Reproductie:** Search collection A then select B; A chunks remain visible under B.

**Aanbevolen oplossing:** Key results by collection and validate the collection ID before rendering.

### B041-005 — P2 — Document filtering happens after the collection result limit

**Bewijs:** The query fetches the top 20 collection chunks before filtering to the selected document.

**Reproductie:** Seed more than 20 earlier matches in another document; the selected document match is reported absent.

**Aanbevolen oplossing:** Filter by document in SQL and use an independent count with real pagination.

### B041-006 — P2 — Category workflow records every actor as web_user

**Bewijs:** Persisted category actions pass the literal web_user instead of the authenticated principal.

**Reproductie:** Invoke the action for two distinct session users and capture identical actor arguments.

**Aanbevolen oplossing:** Require a principal at the service boundary and reject audit mutations without one.

### B041-007 — P2 — Category UI ignores failed writes

**Bewijs:** The immediate update ignores a false result and logs exceptions without reverting or notifying the user.

**Reproductie:** Use a repository returning false or raising; the selected category remains and no UI error appears.

**Aanbevolen oplossing:** Use a structured workflow result, revert the widget on failure and show actionable feedback.

### B041-008 — P2 — UI context flow logs raw user terms

**Bewijs:** Information and error logs include the raw begrip value.

**Reproductie:** Render with review.user@example.test and capture logs; the exact value is present.

**Aanbevolen oplossing:** Log only request/definition IDs or a keyed hash and sanitize exception text.

### B041-009 — P3 — Transient confirmation checkbox cannot complete an action

**Bewijs:** The checkbox exists only inside the button-click branch; checking it reruns with the outer button false.

**Reproductie:** Render the helper, click the action then check confirmation; the callback is never reached.

**Aanbevolen oplossing:** Persist a pending-confirmation state and render confirmation outside the transient branch.

### B041-010 — P3 — Emoji-only delete button may lack an accessible name

**Bewijs:** The visible button label is only a trash emoji; browser accessibility semantics were unavailable.

**Reproductie:** Static inspection found no descriptive visible label; screenreader verification could not be run.

**Aanbevolen oplossing:** Use a descriptive label such as Verwijder <bestand> and verify keyboard and screenreader output.

## Niet getest

- Geen echte multi-user browser, bestandsdelete in productie of screenreadercontrole.
- Visueel contrast, toetsenbord, screenreader, touch en responsive viewports zijn niet met een browserbackend getest.
