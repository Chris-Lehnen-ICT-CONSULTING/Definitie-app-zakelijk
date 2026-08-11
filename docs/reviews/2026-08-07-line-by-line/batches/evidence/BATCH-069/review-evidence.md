# BATCH-069 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 5/5 blobs, 1548/1548 fysieke regels en 147/147 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- 234 scoped tests voor B069-B071 groen, 24 contextschematests skipped; cache- en classificatiefoutinjecties zijn afzonderlijk bewezen.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: Rauwe UI-exceptions, containerteardown en helpercache-reset blijven bestaande PILOT/B012/B044-dedupes.

## Bevindingen

### B069-001 — P2 — FileCache reports success when persistence failed

**Bewijs:** Tests codify True for every write failure; production has no memory fallback, so the value is absent immediately after the claimed success.

**Reproductie:** Make safe_save raise disk-full; set returns true, get returns None and metadata is empty.

**Aanbevolen oplossing:** Return false or a typed degraded result, or implement a real memory fallback; assert set-success implies an immediately readable value.

### B069-002 — P2 — Classification single-path tests swallow crashes and fabricate state

**Bewijs:** Broad catches allow early crashes; tests accept either a call or a state write and one complete-flow case writes the expected classification after ignoring a preview error.

**Reproductie:** Raise from the preview or classification path; selected tests still pass or create the expected state themselves.

**Aanbevolen oplossing:** Use correct async Streamlit fakes, remove catch-all blocks and assert the exact classifier call and resulting state from the production handler.

### B069-003 — P3 — Cache cleanup tests inspect the obsolete pickle suffix

**Bewijs:** Delete and clear tests check .pkl paths although production persists HMAC-signed .json files, so orphaned real cache files are not detected.

**Reproductie:** Leave the production .json file in place while ensuring the asserted .pkl path is absent; the tests remain green.

**Aanbevolen oplossing:** Assert creation and deletion of the actual backend path and verify metadata and file state together.

### B069-004 — P3 — Classification recovery message relies on spatial navigation

**Bewijs:** The test locks in 'scroll naar boven' instead of an explicit focusable recovery action; actual keyboard and screen-reader impact was not runtime tested.

**Reproductie:** Trigger generation without a category and inspect the message; it directs the user spatially but provides no anchor or focus move.

**Aanbevolen oplossing:** Name the exact control, expose a labelled action or anchor and move focus to it; verify with keyboard and a screen reader.

## Niet getest

- Geen echte provider, productiedatabase of interactieve Streamlit/a11y-run; de ruimtelijke foutmelding blijft suspected.
