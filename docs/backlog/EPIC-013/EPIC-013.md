---
id: EPIC-013
applies_to: definitie-app@current
aangemaakt: 11-09-2025
bijgewerkt: 11-09-2025
canonical: true
owner: architecture
prioriteit: HOOG
status: IN_UITVOERING
completion: 10%
last_verified: 13-09-2025
stakeholders:
- Product (PO)
- Architectuur
- Documentation-team
- DevOps/CI
stories:
- US-090
- US-091
- US-092
- US-093
- US-094
- US-095
- US-096
- US-097
- US-098
- US-099
- US-100
- US-101
- US-102
- US-103
- US-104
- US-105
- US-106
- US-107
- US-168
- US-169
target_release: v1.5
titel: Centrale Documentatie‑Portal (Interactief & Auto‑sync)
vereisten:
- REQ-088
- REQ-089
- REQ-090
---

# EPIC-013: Centrale Documentatie‑Portal (Interactief & Auto‑sync)

## Managementsamenvatting

Eén centrale, interactieve portalpagina (browser) voor de héle backlog én relevante documentatie (architectuur, richtlijnen, testing, compliance). De portal wordt automatisch bijgewerkt bij iedere wijziging (status, verplaatsen, toevoegen/verwijderen) en is als herbruikbare oplossing in te zetten voor andere projecten.

## Doelen
- Single pane of glass voor backlog + documentatie
- Directe navigatie, zoek/filter/sort, statusbadges
- Auto‑sync vanuit frontmatter/registry/traceability
- Herbruikbaar in andere repositories (configurabel)

## Succesmetrieken (SMART)
- Portal opent lokaal via `docs/portal/index.html` en toont actuele data (< 2s generatie)
- 0 verouderde verwijzingen naar niet‑canonieke paden
- 100% van doc‑wijzigingen gereflecteerd binnen 1 CI‑run of pre‑commit
- 1 gedeelde generator (config‑gedreven) bruikbaar in ≥ 2 andere projecten

## Scope
- Generator CLI die frontmatter + registry + traceability inleest en `portal-index.json` + `index.html` rendeert
- Pre‑commit/CI‑hooking voor automatische updates
- Portal UI met zoek/filter/sort en klikbare links
- Configuratie voor andere projecten (padmapping, categorieën)

## Niet in scope (nu)
- Complexe workflow‑automatisering (bv. tests/metrics naar stories terugschrijven)
- Externe hosting/publicatie

## Acceptatiecriteria (epic)
- [x] `docs/portal/index.html` bestaat en is interactief (zoek/filter/sort)
- [x] Generator draait in pre‑commit en CI bij doc‑wijzigingen (incl. CI drift‑guard)
- [ ] Config maakt hergebruik in andere repos mogelijk zonder codewijzigingen
- [x] Documentatie: `docs/portal/README.md` met gebruik/ontwikkeling (inclusief viewer & rendering)
- [x] Zoekoperators (MVP) en bookmarkbare query `#q=…` beschikbaar in portal
 - [x] Planningweergave polish (basis): hiërarchie, sprintfilter, tellers en SP‑subtotaal
 - [x] A11y (basis) en chip‑deeplinks (🔎/Alt‑klik) in views

## Relaties
- Richtlijnen: `docs/guidelines/CANONICAL_LOCATIONS.md`, `DOCUMENTATION_POLICY.md`
- Architectuur: `docs/architectuur/*ARCHITECTURE.md`
- Traceability: `docs/traceability.json`, `docs/backlog/requirements/REQ-REGISTRY.json`
 - Broninput (business kennis): [US-061 – Extract en documenteer business kennis](../EPIC-012/US-061/US-061.md)
