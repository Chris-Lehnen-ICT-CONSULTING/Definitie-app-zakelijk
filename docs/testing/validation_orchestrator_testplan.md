# Validation Orchestrator V2 — Testplan (Contract & Interface)

Status: CONCEPT
Eigenaar: QA Lead
Laatst Bijgewerkt: 29-08-2025

## Doel
Dit testplan borgt dat de ValidationOrchestratorV2 interface en resultaten volledig conform het JSON Schema contract functioneren, inclusief degraded‑paden en batchgedrag. Het sluit aan op Story 2.1 (interface) en het `ValidationResult` contract.

## Scope
- Interface methods: `validate_text`, `validate_definition`, `batch_validate`
- Resultaatcontract: `docs/architectuur/contracts/schemas/validation_result.schema.json`
- Foutpad: degraded resultaten volgens error‑catalogus (SYS‑… codes)
 - Policy: aanwezigheid van `system.correlation_id` (UUID) wordt getest als teambeleid, niet als schema‑verplichte eis

## Testsoorten
- Contracttests: JSON Schema validatie tegen `contracts/schemas/validation_result.schema.json`.
- Unit (interface‑niveau, met mocks): parameter validatie, context‑gedrag, error‑mapping.
- Integratie (licht): feature‑flag toggle en basisrooktests (optioneel in latere stories).

## Benodigdheden
- JSON Schema: `docs/architectuur/contracts/schemas/validation_result.schema.json`.
- Fixtures: geldige `ValidationResult` voorbeelden met echte UUID’s voor `system.correlation_id`.
- Mock orchestrator die schema‑conforme resultaten teruggeeft (happy/edge/degraded).

## Testgevallen (uittreksel)

1) Contract — Happy path (text)
- Call: `validate_text(begrip, text, ontologische_categorie, context)`
- Verwacht: schema‑conform; verplichte velden gevuld; `system.correlation_id` is UUID.

2) Contract — Happy path (definition)
- Call: `validate_definition(definition, context)`
- Verwacht: schema‑conform; scores in [0,1]; `violations` array aanwezig (mag leeg).

3) Context — Optioneel
- Call: `validate_text(..., context=None)`
- Verwacht: implementatie genereert `system.correlation_id` en vult `version`.

4) Edge — Lege tekst
- Call: `validate_text(begrip, text="", ...)`
- Verwacht: `is_acceptable == False` (of relevante rule violation); schema‑conform.

5) Batch — Sequentieel
- Call: `batch_validate(items=[ValidationRequest(...)] * N, max_concurrency=1)`
- Verwacht: lengte N; elk item schema‑conform; geen exceptions.

6) Degraded — Timeout/Upstream failure
- Simuleer service failure.
- Verwacht: geen exception; `violations[0].code` begint met `SYS-`; `system.error` gevuld.

7) Error codes — Patroon
- Verifieer `violations[*].code` matcht `^[A-Z]{3}-[A-Z]{3}-\d{3}$`.

## Niet‑functioneel (indicatief)
- Prestaties: single call P95 < 1s (met mocks), batch 100 items binnen acceptabele tijd.
- Memory: geen lek bij 1.000 calls (smoke).

## CI Integratie
- Pytest mark: `@pytest.mark.contract` voor schema‑checks.
- Faal build bij schema‑violatie of ontbrekende verplichte velden.
- (Optioneel) JSON Schema validatie als pre‑merge stap op sample‑responses.

## Relaties
- Contract: `docs/architectuur/contracts/validation_result_contract.md`
- Schema: `docs/architectuur/contracts/schemas/validation_result.schema.json`
- Error catalogus: `docs/technisch/error_catalog_validation.md`
- Story 2.1: `docs/backlog/stories/epic-2-story-2.1-validation-interface.md`
- Story 2.3 Tests: `docs/testing/story-2.3-test-implementation.md`
