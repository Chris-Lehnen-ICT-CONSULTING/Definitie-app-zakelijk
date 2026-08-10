# BATCH-059 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 7/7 blobs, 1205/1205 fysieke regels en 100/100 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Primaire dummy-clientrun over B059-B061: 251 groen, 1 skip en 1 verwachte xfail; onafhankelijke kandidaatselectie 133 groen en 1 skip.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: Contextfilterfinding B059-003 is verwant maar niet identiek aan B035-007; het betreft een andere actieve classifierfunctie.

## Bevindingen

### B059-001 — P2 — Cleaning feature flags are stored but ignored

**Bewijs:** Tests check only stored config values; cleaning still changes text and records rules when enable_cleaning and track_changes are false.

**Reproductie:** Construct disabled cleaning config with a fake cleaner; cleaned_text changes and was_cleaned remains true.

**Aanbevolen oplossing:** Return unchanged text when cleaning is disabled and condition change metadata on track_changes; add behavioral flag tests.

### B059-002 — P2 — Context conversion silently turns JSON objects into key lists

**Bewijs:** The malformed-context test accepts any list; production list(json.loads(value)) converts an object to keys and discards values.

**Reproductie:** Load {"OM":true,"DJI":false}; the repository returns ['OM','DJI'] as valid context.

**Aanbevolen oplossing:** Accept only JSON arrays of strings and quarantine or report objects, scalars and invalid elements with exact regression assertions.

### B059-003 — P2 — Context filter cross-matches unrelated legal domains and short codes

**Bewijs:** Positive-only tests miss that Strafrecht matches civil or administrative text and that a one-letter token matches Sv.

**Reproductie:** Match burgerlijk-recht text with jur_context=['Strafrecht'] and Sr text with wet_context=['S']; both report legal matches.

**Aanbevolen oplossing:** Map each normalized token to one canonical domain or statute with word boundaries and add cross-domain and short-token negatives.

### B059-004 — P3 — Container cutover test permanently expects the wrong outer service

**Bewijs:** The xfail expects the returned DefinitionOrchestratorV2 itself to be ValidationOrchestratorV2 instead of inspecting its nested validation service.

**Reproductie:** Run with --runxfail; the assertion fails while the nested validation service is correctly wired.

**Aanbevolen oplossing:** Assert the correct outer orchestrator and nested validator chain, then remove the stale xfail.

## Niet getest

- Geen echte provider, netwerk, productiedatabase of browser/a11y/responsivetest; tests en actieve servicecallers zijn offline gevolgd.
