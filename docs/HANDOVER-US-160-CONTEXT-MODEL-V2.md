---
canonical: true
status: active
owner: engineering
last_verified: 2025-09-13
applies_to: definitie-app@current
---

# Handover — US‑160 Gate + Context Model V2 cutover

Doel: afronding van US‑160 (Gate bij Vaststellen) én uniformering van context (V2) naar drie gelijkwaardige lijsten: organisatorische_context, juridische_context, wettelijke_basis.

## Samenvatting
- Context Model V2 geïmplementeerd (canoniek: drie lijsten overal; legacy `Definition.context` verwijderd).
- Gate‑policy aangepast: “minimaal één context vereist” (i.p.v. org+jur verplicht).
- UI (Bewerk/Expert/Generator) geharmoniseerd; “Anders…” werkt voor alle drie contexten.
- Export/Repository/Orchestrator/Duplicate detection aangepast naar V2.
- Documentatie geüpdatet; reset‑script toegevoegd.

## Belangrijkste paden
- Datamodel: `src/services/interfaces.py::Definition`
- Repository mapping: `src/services/definition_repository.py`
- DB‑schema: `src/database/schema.sql` (JSON arrays, default `[]`)
- Gate‑policy: `config/approval_gate.yaml` (min_one_context_required)
- Gate‑enforcement: `src/services/definition_workflow_service.py::_evaluate_gate`
- UI tabs:
  - Bewerk: `src/ui/components/definition_edit_tab.py` (3 multiselects + Anders…, min‑1 context)
  - Expert: `src/ui/components/expert_review_tab.py` (geharmoniseerde weergave + 3 filters)
  - Generator: `src/ui/components/definition_generator_tab.py` (geharmoniseerde weergave)
- Orchestrator: `src/services/orchestrators/definition_orchestrator_v2.py` (V2 lijsten + UUID tolerant)
- Prompt: `src/services/prompts/prompt_service_v2.py` (HybridContextManager)
- Duplicate detection: `src/services/duplicate_detection_service.py` (exact op 3 lijsten, fuzzy tokenisatie/stemming)
- Export: `src/services/data_aggregation_service.py`, `src/services/export_service.py`

## Database reset (alle huidige data is testdata)
- Script: `scripts/db/reset_context_model_v2.sh`
- Voert uit: verwijderen `data/definities.db` + toepassen `src/database/schema.sql`.

## Config & omgeving
- OpenAI key via env: `OPENAI_API_KEY` (optioneel: `OPENAI_API_KEY_PROD`).
- Gate‑policy overlay optioneel via env: `APPROVAL_GATE_CONFIG_OVERLAY`.

## Testen (lokaal, met netwerk)
1) Reset DB: `bash scripts/db/reset_context_model_v2.sh`
2) Exporteer prod key: `export OPENAI_API_KEY="sk-..."`
3) Draai suite: `pytest -q`

Opmerking: in sandbox zonder netwerk falen netwerkafhankelijke tests; lokaal met key draaien.

## UI veranderingen
- Bewerk‑tab
  - Drie multiselects (Organisatorisch/Juridisch/Wettelijk) met “Anders…”.
  - Opslaan vereist dat minimaal één contextlijst niet leeg is.
- Expert‑tab
  - Consistente contextweergave (org/jur/wet).
  - Filters per contextsoort (multiselect, inclusieve overlap; AND tussen categorieën).
- Generator‑tab
  - Consistente contextweergave (org/jur/wet).

## Gate‑policy & enforcement
- `config/approval_gate.yaml`:
  - `hard_requirements.min_one_context_required: true`
  - `hard_min_score: 0.75`, `soft_min_score: 0.65`, `forbid_critical_issues: true`.
- Service‑gate afdwinging vóór statuswijziging in `DefinitionWorkflowService.approve()`.

## Export
- JSON: context_dict bevat drie lijsten.
- CSV: extra kolommen `organisatorische_context`, `juridische_context`, `wettelijke_basis` (stringrepresentatie).

## Bekende aandachtspunten
- Unieke constraint gebruikt JSON‑strings (ordegevoelig). In de praktijk zelden een probleem; normalisatie (gesorteerde serialisatie) kan later.
- Enkele performance/benchmark tests hebben strikte timing‑assumpties; lokaal kunnen ze variëren.

## Quick smoke (functioneel)
- Maak definitie met alleen juridisch (bijv. “Strafrecht”) → opslaan OK, vaststellen mogelijk indien gate/score OK.
- Maak definitie zonder context → opslaan blokkeert; gate blokkeert vaststellen met melding.
- “Anders…” toevoegen bij alle drie contexten, opslaan, heropen: waarden zichtbaar.
- Expert‑wachtrij: filter op Organisatorisch/Juridisch/Wettelijk; controleer dat filters contextgevoelig werken.

## Wijzigingslog (kernbestanden)
- Toegevoegd: `docs/architectuur/CONTEXT_MODEL_V2.md`, `docs/HANDOVER-US-160-CONTEXT-MODEL-V2.md`, `scripts/db/reset_context_model_v2.sh`
- Aangepast: zie “Belangrijkste paden”.

## Contact / Owner
- Engineering — Context Model V2 / US‑160 implementatie

