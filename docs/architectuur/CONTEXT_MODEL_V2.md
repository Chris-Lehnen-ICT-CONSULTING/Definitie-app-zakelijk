---
canonical: true
status: active
owner: architecture
last_verified: 2025-09-13
applies_to: definitie-app@current
---

# Context Model V2 (Canoniek)

Doel: één uniforme, gelijkwaardige representatie voor alle contextvelden van een definitie. Elke definitie heeft minimaal één contextwaarde (ongeacht welke van de drie).

## Canonieke datamodel
- `organisatorische_context: list[str]` (JSON array in DB)
- `juridische_context: list[str]` (JSON array in DB)
- `wettelijke_basis: list[str]` (JSON array in DB)

Eigenschappen:
- Geen primair/speciaalfeld: alle drie contexten zijn even belangrijk.
- Minimaal één context vereist (validatie‑regel in service/validator).
- UI en services werken uitsluitend met lijsten (geen string fallback).

## Database opslag
- Tabel `definities` bevat drie TEXT‑kolommen die JSON arrays opslaan:
  - `organisatorische_context`, `juridische_context`, `wettelijke_basis`.
- Trigger/geschiedenis blijven werken met snapshots op JSON‑string basis.
- Testdata‑reset toegestaan (alle huidige data is testdata en mag verwijderd worden).

## Service/API
- `Definition`/DTO’s: context wordt geleverd/verwacht als lijsten.
- Repositories mappen 1‑op‑1 (geen backward compat voor strings of metadata‑afwijkingen).
- Orchestrator/Validator ontvangen `ValidationRequest.context` met deze drie lijsten.

## UI
- Bewerk‑tab: drie velden, elk multi‑value.
- Context selector(s): beheren lijsten; geen “hoofdcontext”.
- Validatie: minimaal één context ingevuld voordat bewerkingen (of vaststellen) toegestaan zijn.

## Migratie/Reset
- Omdat alle data testdata is: reset DB naar nieuw schema (DROP/CREATE) i.p.v. migratie.

## Acceptatiecriteria
- Alle services/UI werken met lijsten voor de drie contexten.
- Minstens één contextwaarde vereist in create/update flows.
- Geen verwijzingen meer naar `Definition.context` (string) of context in `metadata`.

