# BATCH-051 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 13/13 blobs, 1644/1644 fysieke regels en 148/148 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Gecombineerde kandidaatselectie voor B049/B051/B052/B053: 185 groen en 1 verwachte xfail; tijdelijke testisolatie bewees de metadatawrite.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.

## Bevindingen

### B051-001 — P2 — Dotenv guard misses common load_dotenv call shapes

**Bewijs:** The guard recognizes a narrow imported name but misses dotenv.load_dotenv and aliases.

**Reproductie:** Add a source call through the module attribute or an alias; the guard remains green.

**Aanbevolen oplossing:** Resolve imports and qualified calls or use a repository-wide behavior guard with adversarial fixtures.

### B051-002 — P2 — V6 verifier accepts rows with NULL metadata

**Bewijs:** The verifier checks schema presence but not that migrated rows satisfy the non-null metadata contract.

**Reproductie:** Run the verifier against a post-schema database containing a NULL metadata row; it reports success.

**Aanbevolen oplossing:** Assert row-level postconditions and make verification independently detect incomplete backfills.

### B051-003 — P3 — Document-processor exception tests contain vacuous alternatives

**Bewijs:** Assertions such as len(result) >= 0 and broad log-or-result alternatives cannot fail for the intended behavior.

**Reproductie:** Break the fallback extraction while returning any list; the tests still satisfy the alternatives.

**Aanbevolen oplossing:** Assert exact fallback values, exact logs and negative cases without tautological branches.

### B051-004 — P3 — Placeholder test writes persistent metadata to a hardcoded data path

**Bewijs:** The test uses the default document storage instead of tmp_path and creates documents_metadata.json in the current data tree.

**Reproductie:** Run the test from an empty temporary working directory; a 559-byte metadata file appears.

**Aanbevolen oplossing:** Inject tmp_path for every filesystem test and assert no writes outside it.

### B051-005 — P3 — RAG budget tests permit an oversized first chunk

**Bewijs:** The budget-break assertion allows one chunk even when that chunk alone exceeds the configured total budget.

**Reproductie:** Make the implementation always include the first oversized chunk; the test still passes with count <= 1.

**Aanbevolen oplossing:** Assert the actual estimated token sum and require every included chunk and the total to fit the budget.

## Niet getest

- Geen productie-DB-migratie of writes buiten tijdelijke directories; testgedrag is statisch en hermetisch beoordeeld.
