---
id: CFR-BUG-022
titel: `best_iteration` fallback in UI hoofdflow aanwezig
status: open
owner: development-team
applies_to: definitie-app@current
last_verified: 2025-10-02
severity: HIGH
gevonden_op: 2025-09-15
component: ui
---

# CFR-BUG-022: `best_iteration` fallback in UI hoofdflow aanwezig

## Beschrijving
UI bevat nog checks/fallbacks op `best_iteration` buiten de legacy demo-tab, in strijd met V2-only beleid.

## Verwacht Gedrag
Hoofdflow gebruikt uitsluitend V2-responses; `best_iteration` alleen in demo-tab onder flag.

## Oplossing
Onderdeel van [US-175](../US-175.md): verwijder fallbacks; isoleer demo-tab.

## Tests
- Regex: `rg -n "\\bbest_iteration\\b" src | grep -v 'src/ui/components/orchestration_tab.py'` → 0
- UI smoke: render zonder legacy afhankelijkheid.

