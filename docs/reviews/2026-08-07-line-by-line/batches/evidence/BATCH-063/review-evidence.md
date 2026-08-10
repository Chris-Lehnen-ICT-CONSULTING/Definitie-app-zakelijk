# BATCH-063 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-root`
- Scope: 11/11 blobs, 2047/2047 fysieke regels en 120/120 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- 267 van 273 scoped tests groen; roleless archive/restore is direct en via de publieke workflowservice gereproduceerd.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: B063-001 betreft de fail-open policy-API; de directe statusadapteromzeiling blijft afzonderlijk gedekt door B039-001.

## Bevindingen

### B063-001 — P1 — Workflow policy treats a missing role as archive authorization

**Bewijs:** Tests require archive and restore without a role to pass while saying those transitions are admin-only; the public policy and reject service fail open on None.

**Reproductie:** Call can_change_status for draft-to-archived and archived-to-draft with None; both return True, and a direct reject of an archived record changes it to draft.

**Aanbevolen oplossing:** Require a role for sensitive transitions at the authoritative service boundary and propagate authenticated roles through every command.

## Niet getest

- Geen geauthenticeerde end-to-end browsersessie; de policy en publieke service zijn met mocks/directe calls gereproduceerd.
