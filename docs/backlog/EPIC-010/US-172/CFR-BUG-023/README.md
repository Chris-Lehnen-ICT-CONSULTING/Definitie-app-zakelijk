---
id: CFR-BUG-023
titel: UI dependencies buiten UI (services/config/utils)
status: OPEN
severity: HIGH
gevonden_op: 2025-09-15
component: laaggrenzen
---

# CFR-BUG-023: UI dependencies buiten UI (services/config/utils)

## Beschrijving
Niet‑UI modules importeren UI/Streamlit:
- `src/config/feature_flags.py:199-211` → `show_legacy_warning` importeert Streamlit
- `src/services/category_state_manager.py:7,28` → importeert `ui.session_state`
- `src/services/container.py:419` → importeert `ui.services.definition_ui_service`
- `src/utils/voorbeelden_debug.py:14` → importeert Streamlit
- `src/integration/definitie_checker.py:407` → importeert `ui.session_state`

## Verwacht Gedrag
Geen UI/Streamlit imports buiten `src/ui/**` (uitzondering: `src/main.py`).

## Oplossing
Onderdeel van [US-172](../US-172.md): functies verplaatsen naar UI, services puur maken, UI‑container introduceren.

## Acceptatie
- `rg -n "\\b(import|from)\\s+streamlit" src | grep -v '^src/ui/' | grep -v '^src/main.py'` → 0
- `rg -n "\\bfrom\\s+ui\\.|\\bimport\\s+ui\\b" src | grep -v '^src/ui/' | grep -v '^src/main.py'` → 0

