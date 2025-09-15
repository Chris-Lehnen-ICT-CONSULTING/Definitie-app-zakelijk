---
canonical: false
status: active
owner: engineering
last_verified: 2025-09-13
applies_to: definitie-app@current
---

# Handover — US‑160 (Context Model V2) + EPIC‑012 (V2 Orchestrator) — Checkpoint 2025‑09‑13

Doel: overdraagbare snapshot om in een nieuwe sessie/chat direct verder te kunnen met validatie, afronding en vervolgstappen.

## Scope (deze handover)
- US‑160: Gate + Context Model V2 (drie lijsten; min‑1 context; gate‑policy)
- UI + services harmonisatie naar V2 (geen legacy objectvormen, geen `asyncio.run` in services)
- Orchestration‑tab: V2‑responsevorm (demo) en verborgen achter feature‑flag; vervolgwerk vastgelegd in US‑170

## Wat is gedaan
- Repository adapter
  - Updates via dict i.p.v. record; wettelijke_basis als JSON; toelichting wordt bij update behouden.
  - Bestanden: `src/services/definition_repository.py` (+ compat: `get_definitie`, `change_status`).
- Gate policy + preview
  - Config: `config/approval_gate.yaml`; loader: `src/services/policies/approval_gate_policy.py` (TTL‑cache, env overlay)
  - Preview gebruikt robuuste repo‑call; `_evaluate_gate` implementeert pass/override_required/blocked.
- UI Edit/Expert/Generator
  - Edit: 3 contextlijsten + Anders…; min‑1 context enforced; validatie gebruikt V2 context.
  - Generator: prompt debug V2‑only; geen legacy best_iteration pad meer.
  - Expert: gate‑preview zichtbaar; approve/override gedrag.
- Orchestration‑tab (demo)
  - V2 UIResponseDict output; iteraties in `metadata.iterations` voor grafieken; default verborgen achter `ENABLE_LEGACY_TAB=false`.
- Async hygiene (services)
  - `asyncio.run` verwijderd uit services; UI doet bridging (thread/loop safe).
- “Domein” verwijderd uit base_context
  - `src/services/definition_generator_context.py`: geen `domein` key meer.
- Verboden woorden decoupled van Streamlit
  - `src/config/verboden_woorden.py` laadt JSON (UI‑overrides in UI, niet in services).

## Nieuwe items (requirements/stories)
- REQ‑097: “Iteratieve Verbetering van Definities (V2 Orchestrator)”
  - Document: `docs/backlog/requirements/REQ-097.md`
- US‑170: “Koppel Orchestration‑tab aan V2 Orchestrator (productiepad)”
  - Document: `docs/backlog/EPIC-012/US-170/US-170.md`
  - Toegevoegd aan EPIC‑012 tabel.

## Hoe verder (volgorde en checks)
1) Snelle smoke (zonder netwerk)
   - Reset DB: `bash scripts/db/reset_context_model_v2.sh`
   - Start UI: `PYTHONPATH=. streamlit run src/main.py`
   - Verify:
     - Edit‑tab: min‑1 context, Anders…, opslaan + toelichting zichtbaar.
     - Expert‑tab: gate‑preview (pass/override/blocked); approve werkt met/zonder override reden.
     - Generator‑tab: V2 keys in debug (prompt via saved_record metadata als beschikbaar).
2) Optioneel demo Orchestration‑tab
   - `ENABLE_LEGACY_TAB=true PYTHONPATH=. streamlit run src/main.py`
   - Tab is V2‑vormig, maar gebruikt demo‑iteraties (geen netwerk/AI calls).
   - Volledige koppeling volgt onder US‑170.
3) Tests (zonder netwerk)
   - Draai selectief repository/workflow/gate suites; netwerk‑afhankelijke tests skippen zonder `OPENAI_API_KEY`.
   - Voorbeeld: `pytest -q tests/services -k "definition_repository or workflow or gate"`
4) CI gates aanscherpen (volgende sprint)
   - Legacy‑pattern script hard laten falen; secret scan; pip‑audit.

## Strict mode / slash‑commands (voor nieuwe chat)
- `/strict on` | `/strict off` — strikte modus (pauzeer vóór patches/tests/netwerk/DB‑reset; geen aannames).
- `/approve` | `/approve all` — akkoord voor geblokkeerde stap(pen).
- `/deny` — weiger volgende geblokkeerde stap.
- `/plan on` | `/plan off` — planmodus aan/uit.
- Scopes: `/strict on patch,test` (scopes: `patch`, `test`, `network`, `db`, `all`).

## Openstaande punten (kort)
- UI restanten: comments/labels verder V2‑maken (grotendeels gedaan; alleen cosmetisch).
- Tests uitbreiden/activeren voor V2‑contract (validation_details/voorbeelden/sources rendering).
- Security middleware minimaal koppelen (headers, redactie; zie EPIC‑006 referenties).

## Referenties
- Gate Policy: `config/approval_gate.yaml`, service: `src/services/policies/approval_gate_policy.py`
- DB Schema V2: `src/database/schema.sql` (JSON arrays, defaults `[]`)
- Reset script: `scripts/db/reset_context_model_v2.sh`
- V2 Orchestrator: `src/services/orchestrators/definition_orchestrator_v2.py`
- Prompt Service V2: `src/services/prompts/prompt_service_v2.py`

## Laatste status
- Branch: `main` (gepusht)
- Laatste commits omvatten: US‑160 fixes, async‑cleanup, V2 UI harmonisatie, REQ‑097/US‑170 toevoegingen.

