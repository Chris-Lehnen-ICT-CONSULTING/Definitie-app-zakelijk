# BATCH-058 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 6/6 blobs, 1819/1819 fysieke regels en 149/149 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- 319 scoped tests groen voor B056-B058; ingest- en unlinkfouten zijn veilig met tijdelijke bestanden en mocks geïnjecteerd.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.

## Bevindingen

### B058-001 — P2 — Failed RAG ingest leaves the already saved upload orphaned

**Bewijs:** The rollback test verifies only database rows although the UI stores the upload before ingest and rollback never removes that file.

**Reproductie:** Save a temporary upload, make embedding fail and ingest it; the document row is removed but the upload still exists.

**Aanbevolen oplossing:** Use owned staging files and compensating cleanup on every failed ingest without deleting pre-existing or shared paths.

### B058-002 — P2 — RAG deletion reports success after file cleanup fails

**Bewijs:** Tests cover successful unlink only; production commits the DB delete, swallows OSError and the UI unconditionally reports success.

**Reproductie:** Raise PermissionError from unlink; deletion returns True, the database row is gone and the file remains.

**Aanbevolen oplossing:** Return a structured complete or partial outcome and add ownership-aware trash, retry or reconciliation with visible UI feedback.

### B058-003 — P3 — Category service drops the supplied audit reason

**Bewijs:** The test passes a reason but never asserts it; the active service forwards only category and actor and history receives a generic field-change reason.

**Reproductie:** Update a category with reason 'juridische correctie' and capture the repository call; the reason is absent.

**Aanbevolen oplossing:** Persist actor and reason atomically in the category command and assert both in the service test.

## Niet getest

- Geen productieopslag, echte filesystem-permissionomgeving of browserfeedback; alle foutinjecties gebruikten tijdelijke bestanden.
