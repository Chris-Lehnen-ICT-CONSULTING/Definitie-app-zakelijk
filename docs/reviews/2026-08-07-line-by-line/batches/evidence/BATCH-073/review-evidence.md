# BATCH-073 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 8/8 blobs, 1257/1257 fysieke regels en 145/145 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Crossselectie 36 groen en 7 skips; pad- en gateproeven zijn tegen de immutable bronnen uitgevoerd.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.

## Bevindingen

### B073-001 — P3 — Forbidden-symbol gate is fail-open for paths and unreadable files

**Bewijs:** Allowlisting uses suffix and substring checks, unreadable files are skipped, source is scanned as raw text and one named test is a no-op.

**Reproductie:** Check a nested path ending in src/services/ai_service.py or a path containing .DEPRECATED; both are allowed despite not being exact exceptions.

**Aanbevolen oplossing:** Use exact normalized repository paths, fail on unreadable source and inspect tokens or AST instead of raw comments and strings.

## Niet getest

- Geen echte onleesbare projectbron gecreëerd; padspoofing en fail-open selectie zijn met veilige bronstrings gereproduceerd.
