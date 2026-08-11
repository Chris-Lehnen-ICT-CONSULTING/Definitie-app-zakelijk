# BATCH-082 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 20/20 blobs, 1666/1666 fysieke regels en 123/123 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Normaal discoverable scope: 175 groen en 3 skips; expliciete verborgen voorbeeldenfile voegde 12 groen en 3 rood toe.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.

## Bevindingen

### B082-001 — P1 — Hidden voorbeelden suite masks overwrite that inherits prior approval

**Bewijs:** The filename misses pytest's test_*.py glob and marker guard. Production updates an existing slot without resetting review fields, so new unreviewed text inherits approved/rating/reviewer state.

**Reproductie:** Explicit execution returns 12 passes and 3 failures; replace an OLD APPROVED example with NEW UNREVIEWED in the same slot and the same ID retains beoordeeld=true, rating=goed and reviewer=expert.

**Aanbevolen oplossing:** Store a revision/new row or atomically reset every review field on content replacement, then rename and activate the full regression suite.

### B082-002 — P3 — All-validator gate tolerates eight missing rules and a crashing validator

**Bewijs:** The gate requires only 45 rules instead of the canonical 53 and allows a nonzero crash percentage.

**Reproductie:** Remove eight non-hardcoded rules or make one validator raise; the mutated gate still passes.

**Aanbevolen oplossing:** Derive the exact expected ID set from the canonical rule config and require every rule to load and execute without tolerance.

### B082-003 — P3 — Externalized category mapping test duplicates the configuration in code

**Bewijs:** The test promises config-only extensibility but requires exact equality with hardcoded _CATEGORY_PREFIXES, so a valid config extension still requires a code edit.

**Reproductie:** Add a valid prefix to the canonical configuration; the exact-equality assertion fails despite valid runtime data.

**Aanbevolen oplossing:** Test schema and behavior invariants instead of duplicate values, or generate the fallback from the same source.

### B082-004 — P3 — Violation description test inspects only the first matching violation

**Bewijs:** The assertion selects one arbitrary message-bearing violation although the contract applies to every violation and mentions a specific rule.

**Reproductie:** Return a valid first violation and a second violation without description; the test remains green.

**Aanbevolen oplossing:** Assert every message-bearing violation and explicitly target the intended STR-01 record.

## Niet getest

- Geen volledige 317-file suite, echte multi-thread databasebelasting, browser of netwerk.
