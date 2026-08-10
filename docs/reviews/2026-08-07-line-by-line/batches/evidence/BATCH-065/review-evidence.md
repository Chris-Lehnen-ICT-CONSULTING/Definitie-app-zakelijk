# BATCH-065 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 4/4 blobs, 2316/2316 fysieke regels en 149/149 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- 107 van 107 scoped tests groen; vier circuitcases gaven unawaited-coroutinewaarschuwingen en een correct contextmanagermodel bewees het verschil.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: Hostnamespoofing en SQLite ResourceWarnings leveren aanvullend bewijs voor B007/B016 en B010, zonder nieuwe finding-ID.

## Bevindingen

### B065-001 — P2 — Ranker tests codify invalid duplicated ordinal lid references

**Bewijs:** Tests explicitly require 'eerste lid eerste'; the active ranker therefore misses normal 'eerste lid' and 'tweede lid' citations.

**Reproductie:** Check eerste lid bepaalt, tweede lid bepaalt, eerste lid eerste and lid 2; only the duplicated ordinal and numeric form match.

**Aanbevolen oplossing:** Use explicit alternatives for lid plus number or ordinal and ordinal plus lid, with canonical positive and negative tests.

### B065-002 — P2 — Circuit-breaker tests pass through a broken async HTTP mock

**Bewijs:** Four tests make session.get an AsyncMock although async-with expects a synchronously returned async context manager, so they exercise error retries and emit unawaited-coroutine warnings.

**Reproductie:** Run the trigger case: it passes with six calls and error attempts; a correct MagicMock context manager uses two real empty-200 attempts.

**Aanbevolen oplossing:** Mock get synchronously, keep async methods as AsyncMock and assert exact calls, parser use, attempt errors and warning-free execution.

### B065-003 — P3 — Web lookup assertions do not prove their stated behavior

**Bewijs:** Tests check only a bool, boost >= 1, or two independent scores above a floor; the namespace diagnostic test patches logging without asserting it.

**Reproductie:** Remove cap or context behavior, or omit diagnostic logging; the broad assertions still pass.

**Aanbevolen oplossing:** Assert exact booleans and boost values, compare with-context above without-context and verify diagnostic message metadata; mark only the timing test slow.

## Niet getest

- Geen live SRU/Brave-netwerk, echte latency, browser, a11y of responsive test; de batch bevat uitsluitend unit-tests.
