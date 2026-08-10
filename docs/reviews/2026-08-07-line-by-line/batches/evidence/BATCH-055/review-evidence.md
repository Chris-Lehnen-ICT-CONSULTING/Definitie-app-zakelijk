# BATCH-055 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 5/5 blobs, 1394/1394 fysieke regels en 146/146 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Exacte batchselectie: 114 groen; aanvullende synonym-suggesterselectie 10 groen maar zonder de lege-termgrens.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: De tolerante hard-captests leveren aanvullend bewijs voor B035-005 en zijn niet als tweede productdefect geteld.

## Bevindingen

### B055-001 — P2 — Blank synonym term escapes error handling and corrupts stats

**Bewijs:** Prompt construction occurs before try; a blank term raises while total_calls increments and failure_count does not.

**Reproductie:** Call the real suggester with whitespace; ValueError escapes, AI is not called and failure_count remains zero.

**Aanbevolen oplossing:** Validate before accounting or include prompt construction in the guarded path and record a consistent failure.

### B055-002 — P2 — Merged legal chunks lose article provenance

**Bewijs:** The required test accepts the absorbed article's number; production persists and returns only that single value for text containing two articles.

**Reproductie:** Merge article 1 and 2 chunks; text contains both while metadata artikel_nummer is only '2'.

**Aanbevolen oplossing:** Do not merge across article boundaries or store and propagate multivalued provenance.

### B055-003 — P3 — Synonym response parser stops at the first malformed candidate

**Bewijs:** Candidate selection stops on the first object containing synoniemen before validating that value as a list.

**Reproductie:** Return a malformed first candidate followed by a valid object; the parser returns an empty list.

**Aanbevolen oplossing:** Scan all candidate objects and stop only after a complete valid schema is found.

### B055-004 — P3 — Synonym prompt truncates context before removing blanks

**Bewijs:** Context is sliced to twenty entries before whitespace normalization and filtering.

**Reproductie:** Supply twenty whitespace entries followed by Awb; Awb is absent from the built prompt.

**Aanbevolen oplossing:** Normalize and remove blank entries before applying item and token limits.

### B055-005 — P3 — Chunking tests contain vacuous and partial assertions

**Bewijs:** Abbreviation coverage can pass on unrelated overlap, minimum-size checks only one chunk and overlap checks are conditional.

**Reproductie:** Produce chunks [9, 232] or a single chunk; the minimum and conditional overlap tests still pass.

**Aanbevolen oplossing:** Assert exact abbreviation content, every non-exempt chunk and a guaranteed multi-chunk fixture.

## Niet getest

- Geen echte AI-call of live RAG-ingestie; tokentelling gebruikte dezelfde hermetische fake encoder als de projectsuite.
