# BATCH-061 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 10/10 blobs, 1927/1927 fysieke regels en 126/126 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Cross-selectie 133 groen en 1 skip; CWD-variant reproduceerde één rankingfailure en credentialvrije containerproeven bevestigden bestaande dedupes.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: Cross-requestdebug escaleert bestaande B035-008 naar P1; teardown, credential- en sys.pathbevindingen blijven dedupes van B012/PILOT/B052.

## Bevindingen

### B061-001 — P3 — Concurrent validation test does not force coroutine overlap

**Bewijs:** The shared service has cleaning disabled and its validation path has no active await, so asyncio.gather executes each coroutine to completion sequentially.

**Reproductie:** Instrument entry and exit around validate_definition; no two validations overlap although the race assertions pass.

**Aanbevolen oplossing:** Inject a deterministic async barrier before state use and assert actual overlap plus isolated results.

### B061-002 — P3 — Pandas missing-value test copies rather than calls production logic

**Bewijs:** The test duplicates the nested predicate from the import service, so production can change or disappear while the copied logic stays green.

**Reproductie:** Mutate the production predicate; the test remains green because it imports no production behavior.

**Aanbevolen oplossing:** Extract and test a production helper or drive the real CSV-row import with NaN, pd.NA, None, blank and populated values.

### B061-003 — P3 — Web lookup defaults depend on the process working directory

**Bewijs:** The test passes from the repository root but fails from a temporary working directory because config loading resolves a relative default and silently changes ranking weights.

**Reproductie:** Run test_ranking_relevance_based from a temporary cwd; configuration is absent and Overheid wins instead of the asserted Wikipedia result.

**Aanbevolen oplossing:** Resolve packaged defaults from a module or explicit project resource and add a chdir-independent regression test.

## Niet getest

- Geen echte multisessie, provider of browser; cross-requestdebug is al onder B035-008 vastgelegd en met gecontroleerde interleaving bewezen.
