# BATCH-042 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 7/7 blobs, 3509/3509 fysieke regels en 91/91 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatiebestanden zijn niet gewijzigd.

## Verificatie

- 250 gerichte unit-tests groen (1 skip) en 165 onafhankelijke crosstests groen; provider- en editstatepaden met veilige fakes gereproduceerd; Ruff en Black schoon.
- De onafhankelijke verifier heeft alle kandidaten gedisponeerd en de P1-codepaden opnieuw beoordeeld.

## Bevindingen

### B042-001 — P1 — Provider and API key are process-global across sessions

**Bewijs:** The sidebar mutates os.environ and resets process-global containers from session input.

**Reproductie:** Apply a provider change in one simulated session; a subsequent session reads the same key and provider.

**Aanbevolen oplossing:** Store credentials and clients per authenticated session; never mutate process environment at runtime.

### B042-002 — P1 — Established definitions still allow category mutation

**Bewijs:** Term and text are disabled for established records, but category and Save remain mutable and service guards are absent.

**Reproductie:** Change category on an established fake record and save; the service receives and persists the update.

**Aanbevolen oplossing:** Enforce immutable-state and authorization invariants in the service and disable every mutating control.

### B042-003 — P1 — Undo and revert leave stale widget edits active

**Bewijs:** State replacement does not reset ID-scoped widget keys, allowing autosave to reapply stale values.

**Reproductie:** Set object text ORIGINAL and widget UNSAVED, invoke undo; object resets but widget remains UNSAVED.

**Aanbevolen oplossing:** Centralize hydration for all keys and suppress change tracking until the reset completes.

### B042-004 — P2 — Successful save reruns before refreshing the definition

**Bewijs:** st.rerun halts execution before _refresh_current_definition on the normal validated-save branch.

**Reproductie:** Raise a rerun sentinel in a fake Streamlit call; validation state is set but refresh is never called.

**Aanbevolen oplossing:** Update the current object before rerun or render a next-run transition state.

### B042-005 — P2 — Conflict recovery button is transient and cannot run

**Bewijs:** The recovery button is nested inside the Save click branch and disappears on its own rerun.

**Reproductie:** Trigger a conflict then click refresh; the outer Save condition is false and the handler is skipped.

**Aanbevolen oplossing:** Persist conflict state and render recovery at a stable top-level location.

### B042-006 — P2 — Anthropic example generation is disabled by an OpenAI-only check

**Bewijs:** Capability is inferred only from OPENAI_API_KEY variables despite configured Anthropic support.

**Reproductie:** Render with only ANTHROPIC_API_KEY; the generation button is disabled with an OpenAI warning.

**Aanbevolen oplossing:** Ask the configured provider service for capability instead of reading provider-specific environment names.

### B042-007 — P2 — Definition edit UI exposes backend exceptions and logs raw terms

**Bewijs:** Raw repository errors are interpolated into UI and search terms are logged unredacted.

**Reproductie:** Raise ValueError containing API_KEY=review-secret; the sentinel appears in warning/log output.

**Aanbevolen oplossing:** Show a correlation ID with generic UI text and sanitize structured server-side diagnostics.

### B042-008 — P3 — ui/components.py is shadowed by the components package

**Bewijs:** Python resolves src/ui/components/__init__.py, leaving the 476-line module unreachable.

**Reproductie:** Import src.ui.components and inspect __file__; it points to the package and lacks the module class API.

**Aanbevolen oplossing:** Delete or rename the legacy module after an explicit migration and add an import-contract test.

## Niet getest

- Geen echte multi-session aanval, providercredentials of live database gebruikt.
- Visueel contrast, toetsenbord, screenreader, touch en responsive viewports zijn niet met een browserbackend getest.
