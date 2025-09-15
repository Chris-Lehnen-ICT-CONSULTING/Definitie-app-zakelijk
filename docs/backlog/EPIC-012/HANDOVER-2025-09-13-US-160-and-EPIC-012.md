---
canonical: false
status: active
owner: engineering
last_verified: 2025-09-13
applies_to: definitie-app@current
---

# Handover — US‑160 (Context Model V2) + EPIC‑012 (V2 Orchestrator) — Checkpoint 2025‑09‑13

Deze handover vat de laatste wijzigingen samen en geeft concrete vervolgstappen om in een nieuwe sessie/chat het werk direct op te pakken.

## Kernresultaten
- V2 Contextmodel overal: 3 lijsten (organisatorisch/juridisch/wettelijk); min‑1 context enforced; gate‑policy geactiveerd.
- Services async‑hygiëne: `asyncio.run` uit services; UI doet bridging.
- Orchestration‑tab produceert V2 UIResponseDict (demo), standaard verborgen.
- UI generator‑tab is V2‑only (geen legacy best_iteration).
- REQ‑097 (iteratieve verbetering) en US‑170 (koppeling Orchestration‑tab → V2) toegevoegd.

## Wat verifiëren (smoke)
1) DB reset: `bash scripts/db/reset_context_model_v2.sh`
2) Start UI: `PYTHONPATH=. streamlit run src/main.py`
3) Check Edit/Expert/Generator conform handover in EPIC‑004 document (US‑160)
4) Optioneel: `ENABLE_LEGACY_TAB=true` voor demo Orchestration‑tab (geen netwerk nodig)

## Volgende stappen
- US‑170 implementeren: vervang demo‑iteraties door echte call `DefinitionOrchestratorV2.create_definition(...)` via `ui.helpers.async_bridge`.
- Gate‑status + override‑reden in Orchestration‑tab tonen (zelfde UX als Expert‑tab).
- Tests: unskip/selectieve suites voor V2‑contract; netwerk‑afhankelijk mocken of skippen zonder key.
- CI: legacy/secrets/audit‑gates aanscherpen.

## Strict mode (chat)
- `/strict on` (scopes optioneel), `/approve`, `/deny`, `/plan on` — zie Agents guidelines.

## Paden & referenties
- Gate Policy: `config/approval_gate.yaml`, loader: `src/services/policies/approval_gate_policy.py`
- Orchestrator V2: `src/services/orchestrators/definition_orchestrator_v2.py`
- Prompt V2: `src/services/prompts/prompt_service_v2.py`
- Repo adapter: `src/services/definition_repository.py`
- UI tabs: `src/ui/components/*_tab.py`
- Requirements: `docs/backlog/requirements/REQ-097.md`
- Story: `docs/backlog/EPIC-012/US-170/US-170.md`

## Status
- Branch: `main` — alle wijzigingen gepusht.

