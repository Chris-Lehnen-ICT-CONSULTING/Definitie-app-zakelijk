# BATCH-037 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-root`
- Scope: 6/6 blobs, 3206/3206 fysieke regels en 101/101 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatiebestanden zijn niet gewijzigd.

## Verificatie

- Onderdeel van 400 relevante unit-tests (1 expliciete skip); tijdelijke upload- en mockservice-reproducties uitgevoerd; Ruff en Black schoon.
- De onafhankelijke verifier heeft alle kandidaten gedisponeerd en de P1-codepaden opnieuw beoordeeld.

## Bevindingen

### B037-001 — P2 — Upload lookup can bind a document to the wrong file

**Bewijs:** Suffix-based matching is ambiguous when different uploads share a basename or suffix.

**Reproductie:** Create two candidate paths with the same suffix and resolve the later document; the first matching file can be selected.

**Aanbevolen oplossing:** Persist and use a stable document-to-path identifier rather than suffix matching.

### B037-002 — P2 — Document deletion leaves the original upload on disk

**Bewijs:** The UI removes document metadata but does not unlink the source upload.

**Reproductie:** Delete a temporary uploaded document through the renderer path; metadata is removed while the file still exists.

**Aanbevolen oplossing:** Delete or securely retain the original under an explicit lifecycle policy and report partial failures.

### B037-003 — P3 — Dormant jurisprudence helper targets a removed endpoint

**Bewijs:** The helper builds requests for an endpoint no longer supported by the surrounding service contract.

**Reproductie:** Invoke the helper with a mocked client and inspect the generated obsolete endpoint.

**Aanbevolen oplossing:** Remove the dormant helper or migrate it to the supported API with a contract test.

### B037-004 — P3 — Wikipedia include_extract option is ignored

**Bewijs:** The request and result path still fetch and return extract content when include_extract is false.

**Reproductie:** Call the service with include_extract=False and a mocked response; extract processing still occurs.

**Aanbevolen oplossing:** Condition request fields and output mapping on include_extract and add both-mode tests.

## Niet getest

- Geen externe Wikipedia/SRU/Wiktionary-call en geen echte gebruikersuploads gebruikt.
- Visueel contrast, toetsenbord, screenreader, touch en responsive viewports zijn niet met een browserbackend getest.
