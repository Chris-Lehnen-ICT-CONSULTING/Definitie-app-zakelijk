# BATCH-076 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 5/5 blobs, 1513/1513 fysieke regels en 117/117 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Exacte scope-run: 64 groen, 14 rood en 2 skips; de actuele async prompt-API en metadata-/exceptionrepro's zijn afzonderlijk uitgevoerd.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: Het ruwe validatie-exceptionpad is exact gededupliceerd naar B023-006 en daarom niet opnieuw als B076-finding geteld.

## Bevindingen

### B076-001 — P2 — US041 tests invoke the intentionally removed synchronous prompt API

**Bewijs:** Fourteen cases call PromptServiceV2.build_prompt, which intentionally raises NotImplementedError; the current API is async build_generation_prompt.

**Reproductie:** Run the file against the immutable base: 6 tests pass and 14 fail on the removed route, while the current async API produces the expected context prompt.

**Aanbevolen oplossing:** Rewrite the suite as async contract tests for build_generation_prompt and assert PromptResult text, truncation and deduplication behavior.

### B076-002 — P2 — Rechtspraak ECLI metadata is dropped before provenance construction

**Bewijs:** The active orchestrator drops result metadata and lowercases Rechtspraak.nl to an unrecognized provider value, while provenance requires canonical rechtspraak plus metadata.dc_identifier.

**Reproductie:** Offline provenance outputs were ECLI, None and None for canonical input, metadata removed and provider mis-normalized respectively.

**Aanbevolen oplossing:** Preserve bounded legal metadata, canonicalize provider identities and test a real Rechtspraak LookupResult through the full provenance path.

## Niet getest

- Geen echte provider, webbron, credential, browser of productie-DB; ECLI- en geheimrepro's waren volledig offline.
