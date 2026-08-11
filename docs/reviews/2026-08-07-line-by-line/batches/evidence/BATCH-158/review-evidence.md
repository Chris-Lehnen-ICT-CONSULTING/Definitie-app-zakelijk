# BATCH-158 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 29/29 bereiken, 5986/5986 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable archiefdocumenten zijn gelezen; OID-, UTF-8-, link-, credential-, policy- en documentstructuurcontroles reproduceerden de geregistreerde grenzen.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B158-001 — P3 — Archived active API reference describes interfaces that do not exist

**Bewijs:** The document claims the API is used internally by the Streamlit UI, imports services.unified_definition_service, documents validation, document-upload and lookup endpoints, and says validation uses 46 rules. At the immutable base, src/services/unified_definition_service.py does not exist, src/api contains only feature_status_api.py with four GET feature-status routes, none of the documented endpoint strings occurs in src or tests, and src/toetsregels/regels contains 53 JSON rules. Although the outer path is archived, the inner directory is named active and the page has no archive/deprecation banner.

**Reproductie:** At base b958ddb, run git cat-file -e for src/services/unified_definition_service.py and git grep for /api/validation/rules, /api/documents/upload and /api/lookup/definition under src/tests; no targets are found. List src/api routes and count src/toetsregels/regels/*.json to obtain only the feature-status GET API and 53 rule files.

**Aanbevolen oplossing:** Add a prominent historical/deprecated banner and move it out of the active subtree, or regenerate an API reference from the actual FastAPI/OpenAPI and Python interfaces. Gate published API docs against route discovery and the canonical rule inventory.

## Deduplicaties en afwijzingen

- Stale web- en API-documentatie is alleen zelfstandig geteld waar een concrete active/UI-claim aantoonbaar onjuist is.

## Niet getest

- Geen browserweergave, echte Claude-instructieprecedence, netwerk, deployments, credentials of uitvoering van archiefvoorbeelden.
