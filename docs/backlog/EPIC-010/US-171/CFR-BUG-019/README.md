---
id: CFR-BUG-019
titel: Sync-bridges aanwezig in services (event-loop bridging)
status: OPEN
severity: HIGH
gevonden_op: 2025-09-15
component: services
---

# CFR-BUG-019: Sync-bridges aanwezig in services (event-loop bridging)

## Beschrijving
Services bevatten sync wrappers met eigen event loops/threads:
- `src/services/service_factory.py:510-530`
- `src/services/prompts/prompt_service_v2.py:339-352`
- `src/services/export_service.py:114-141`
- `src/services/definition_edit_service.py:470-483`

Dit schendt async‑purisme en verhoogt risico op deadlocks en complex error handling.

## Verwacht Gedrag
Service‑laag is async-only; UI gebruikt `ui/helpers/async_bridge.py` indien sync nodig is.

## Reproduceren
`rg -n "(run_coroutine_threadsafe|new_event_loop|run_until_complete)" src/services`

## Oplossing
Onderdeel van [US-171](../US-171.md): verwijder wrappers en gebruik async API’s.

## Tests
- Regex‑test op verboden patronen.
- Unit: async path levert functioneel identieke output.

