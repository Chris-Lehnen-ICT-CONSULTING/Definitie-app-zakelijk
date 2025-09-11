---
canonical: true
status: active
owner: documentation-team
last_verified: 2025-09-11
applies_to: definitie-app@current
title: Kennisoverzicht – Eerdere Backlog Dashboards
---

# Kennisoverzicht – Eerdere Backlog Dashboards

Dit document vat de functionele inzichten (kennis) samen die in de oude dashboards zaten, zodat we zonder dubbel onderhoud alles in de nieuwe Portal kunnen terugvinden.

## Wat zat er in de oude dashboards?
- Requirements Dashboard (`docs/backlog/dashboard/index.html`)
  - Tabelweergave van vereisten met zoeken/sorteren.
  - Quick‑links naar REQ‑bestanden en gerelateerde epics/stories.
- Per‑Epic Overzicht (`docs/backlog/dashboard/per-epic.html`)
  - In-/uitklapbare blokken per EPIC met gekoppelde stories/vereisten.
  - Statusindicatie per EPIC (visueel overzicht).
- Grafisch Overzicht (`docs/backlog/dashboard/graph.html`)
  - Bipartite graaf REQ ↔ EPIC (soms aangevuld met US), voor snelle oriëntatie op dekking.

## Hoe vind je dit terug in de Portal?
- Portal lijst (docs/portal/index.html):
  - Toont alle documenten (REQ/EPIC/US/BUG/ARCH/GUIDE/TEST/COMP) met zoek/filter/sort.
  - Vervangt het Requirements Dashboard en Per‑Epic Overzicht door één uniforme lijst met filters.
- Visuele grafiek (optioneel vervolg):
  - Kan als subview aan de Portal worden toegevoegd (bijv. met mermaid/D3), gevoed door dezelfde portal‑index.json.

## Bronnen en data
- De Portal gebruikt frontmatter uit de bronbestanden en kan worden uitgebreid met traceability/registry data, zodat alle dashboards dezelfde dataset gebruiken.

## Aanpak consolidatie
1. Portal is de primaire ingang (docs/portal/index.html).
2. Oude dashboards worden gearchiveerd; geen aparte data‑generatie meer.
3. Eventuele unieke visualisaties worden als Portal‑subview teruggebracht.

