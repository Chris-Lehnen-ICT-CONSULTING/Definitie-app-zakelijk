---
id: CFR-BUG-019
titel: Sync-bridges aanwezig in services (event-loop bridging)
status: RESOLVED
owner: development-team
applies_to: definitie-app@current
last_verified: 2025-10-02
severity: HIGH
gevonden_op: 2025-09-15
component: services
---

# CFR-BUG-019: Sync-bridges aanwezig in services (event-loop bridging)

## Beschrijving
Historisch waren er sync‑wrappers met eigen event loops/threads in services. Deze zijn verwijderd.

Huidige situatie (gecontroleerd):
- Geen `run_coroutine_threadsafe`, `new_event_loop`, `run_until_complete`, of `asyncio.run(` in `src/services/**`.
- `PromptServiceV2.build_prompt` (sync) geeft `NotImplementedError` met instructie om async‑pad te gebruiken via UI‑bridge.

## Verwacht Gedrag
Service‑laag is async-only; UI gebruikt `ui/helpers/async_bridge.py` indien sync nodig is.

## Reproduceren
Controle:
`rg -n "(run_coroutine_threadsafe|new_event_loop|run_until_complete|asyncio\.run\()" src/services` → geen hits

## Oplossing
Onderdeel van [US-171](../US-171.md): wrappers verwijderd; services zijn async‑only, UI gebruikt async‑bridge.

## Tests
Bewijs
- Legacy‑gates en regex‑check: geen hits in `src/services/**`.
- `scripts/check-legacy-patterns.sh`: Services Architecture Check (asyncio.run in services) → PASS.
