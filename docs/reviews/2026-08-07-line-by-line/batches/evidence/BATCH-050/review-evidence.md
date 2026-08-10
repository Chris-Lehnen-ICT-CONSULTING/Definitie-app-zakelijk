# BATCH-050 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 2/2 blobs, 172/172 fysieke regels en 2/2 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- 50 relevante tests groen en 7 verouderde skips; destructive execute is niet gebruikt en alle toolreproducties waren dry-run of mocks.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.

## Bevindingen

### B050-001 — P2 — Naming maintenance tool targets the wrong tree and plans breaking renames

**Bewijs:** The documented default directory does not exist and a corrected directory selects 52 JSON files while missing their Python counterparts and active dash-ID consumers.

**Reproductie:** Run documented dry-run; it reports missing directory but exits zero. Point it at src/toetsregels/regels; it plans 52 unsafe renames.

**Aanbevolen oplossing:** Deprecate the tool or require an immutable preflight covering every file and consumer before any rename.

### B050-002 — P2 — Naming maintenance update is non-atomic and hides rename failure

**Bewijs:** JSON content is written before rename and failures are swallowed; main has no nonzero exit contract.

**Reproductie:** Mock rename to fail after JSON dump; the updated ID remains under the old filename and the command exits zero.

**Aanbevolen oplossing:** Stage all outputs, fsync and atomically publish or roll back; return nonzero on any mismatch or failure.

## Niet getest

- Geen --execute, rename of write op de echte regelset; uitsluitend dry-run en mocks.
