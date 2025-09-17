---
titel: Code Review Rapport
generated: 2025-09-16
status: draft
owner: development
applies_to: definitie-app@current
---

# Code Review — Refactorstatus naar Moderne Architectuur (V2)

Doel: actuele status van de refactor (legacy → V2) met concrete bevindingen, risico’s en aanbevelingen. Dit rapport is gebaseerd op quick‑checks, een smoke test baseline en gerichte repo‑scans.

## Samenvatting
- Smoke tests: OK (3 passed). Volledige `pytest -q` time‑out in CLI; lokaal draaien aanbevolen voor volledige dekking.
- V2 aanwezig: `DefinitionOrchestratorV2` en `ValidationOrchestratorV2` worden gebruikt (container + UI wiring).
- Endpoint‑timeouts en rate limiting centraal geregeld: `src/config/rate_limit_config.py`; UI gebruikt `get_endpoint_timeout()`.
- Belangrijkste blockers richting “volledig modern”: wijdverbreide `asyncio.run(...)` buiten de UI‑bridge, enkele legacy markers/compat‑paden, en UI‑code die nog V1‑patroon `best_iteration` aanraakt.

## Quick‑Checks (objectieve signalen)

1) Legacy patronen in `src/`
- `asyncio.run(`: 21 hits (o.a. in validators, voorbeelden, utils, security, UI helpers/components)
  - Voorbeelden:  
    - `src/validation/sanitizer.py:684`  
    - `src/utils/resilience.py:729`  
    - `src/ui/helpers/async_bridge.py:52,53`  
    - `src/ui/tabbed_interface.py:796`  
    - `src/ui/components/monitoring_tab.py:695`
- `best_iteration`: 6 hits (bv. `src/ui/components/orchestration_tab.py` — V1‑achtig aggregatiepatroon)
- V1 result import: 0 hits voor `from src.models.generation_result import` (goed teken)

2) V2‑UI contract keys (indicaties in UI)
- Aanwezig: `definitie_gecorrigeerd` (27), `validation_details` (6), `metadata` (100), `voorbeelden` (120) in `src/ui/`.
- Interpretatie: V2‑shape is breed aanwezig in de UI; controleer consistent gebruik (geen mix met V1‑sleutels).

3) Endpoints/rate limits/timeouts
- Centraal beheerd in `src/config/rate_limit_config.py`; UI‑bridge haalt timeouts op via `get_endpoint_timeout()`.
- Aanbeveling: vervang ad‑hoc timeouts (bv. in `unified_voorbeelden.py`) door centrale lookups waar passend.

4) Legacy/DEPRECATED markers (28 hits)
- Compatibiliteitspaden aanwezig (bv. `definition_orchestrator_v2.py` heeft LEGACY‑compat secties; diverse `DEPRECATED` verwijzingen in services).

## Correctness & Tests
- Smoke: `tests/smoke/test_validation_v2_smoke.py` — 3/3 groen.  
- Volledige suite: time‑out in CLI. Aanbevolen lokaal: `pytest -q && pytest tests/integration -q` met hogere timeout.

## Bevindingen per thema

- Async/Bridging
  - Bevinding: `asyncio.run` komt voor in niet‑UI‑paden (validators/utils). Richtlijn: uitsluitend in `ui/helpers/async_bridge.py` gebruiken, elders async all‑the‑way of via bridge aanroepen.
  - Risico: deadlocks/event‑loop conflicten; moeilijk testbare paden; inconsistent timeouts.

- UI Orchestration
  - Bevinding: `best_iteration` selectie in `orchestration_tab.py` wijst op V1‑achtig aggregatiepad. V2 verwacht duidelijk contract (dict‑shape) i.p.v. losse iteratieselectie in UI.
  - Aanpak: laat services de juiste eindshape leveren; UI alleen presenteren en opslaan.

- Config/Timeouts/Rate limiting
  - Sterk punt: centrale `rate_limit_config.py` met endpoint‑timeouts en rate‑limiting.
  - Verbetering: gebruik centrale timeouts breder (reduceer hardcoded `timeout=10.0` e.d. in `unified_voorbeelden.py`).

- Legacy Compatibiliteit
  - Bevinding: `LEGACY` en `DEPRECATED` markers aanwezig in services en feature flags (LEGACY tabs/agents nog ge‑feature‑flagd).
  - Aanpak: plan gecontroleerde verwijdering (zie Backlog) nadat UI/flows volledig V2 zijn.

## Aanbevolen Aanpak (kort)
1) Async‑schoonmaak: verwijder `asyncio.run` buiten `ui/helpers/async_bridge.py`; migreer validators/utils naar pure async of roep via bridge aan in UI‑laag.
2) UI‑aggregatie moderniseren: elimineer `best_iteration`‑logica uit UI; verplaats selectie naar service/orchestrator en lever V2‑dict.
3) Timeouts harmoniseren: gebruik `get_endpoint_timeout()` in paden met AI/web lookups en voorbeelden‑generaties; vermijd duplicaat/hardcoded timeouts.
4) Legacy feature flags: zet DEPRECATED flags naar off en verwijder codepaden gefaseerd (na testdekking).
5) Testuitvoerbaarheid: splits trage integratiepaden of voeg markers toe; zorg dat `pytest -q` binnen CI‑timeout draait.

## Quick‑Win Patches (minimal diff)
- Verplaats ad‑hoc `asyncio.run(...)` test‑aanroepen in modules (bv. `test_*` hulpfuncties) naar echte testbestanden onder `tests/` of guard ze onder `if __name__ == "__main__":`.
- Introduceer helper(s) die centrale timeouts ophalen en vervang hardcoded waarden in `unified_voorbeelden.py`.
- In `orchestration_tab.py`: vervang `best_iteration`/losse field‑mapping door gebruik van een door services geleverde V2‑dict.

## Backlog (geprioriteerd)
1) Verwijder `asyncio.run` buiten UI‑bridge (validators/utils) — risico: event‑loop conflicten; winst: stabiliteit/testbaarheid.
2) Harmoniseer timeouts via `rate_limit_config` (vooral voorbeelden‑paden) — winst: minder timeouts, voorspelbaar gedrag.
3) UI orchestration V2‑conform maken (weg met `best_iteration`) — winst: duidelijke verantwoordelijkheid, minder UI‑logica.
4) Opruimen DEPRECATED/LEGACY paden + flags — winst: eenvoud, minder onderhoud.
5) Test performance: verdeel suites/scope zodat volledige tests binnen CI‑budget passen; voeg integratielabels toe.

## Acceptatiecriteria (DoD)
- Geen `asyncio.run` in services/validators/utils; alleen via `ui/helpers/async_bridge.py`.
- UI werkt uitsluitend met V2‑dict contract (inclusief `definitie_gecorrigeerd`, `validation_details`, `voorbeelden`, `metadata`).
- Endpoints/AI/web‑lookups gebruiken centrale timeouts/rate limits.
- Smoke + unit/integratie groen binnen overeengekomen timeout.
- Legacy/DEPRECATED codepaden verwijderd of feature‑flagged off, met migratienotities.

## Evidence (bijlage)
- Grep samenvatting: `asyncio.run` (21), `best_iteration` (6), V2‑UI keys aanwezig, V1 result import (0).  
- Smoke test: 3 passed, 0 failed.

