---
id: EPIC-013
applies_to: definitie-app@current
aangemaakt: 11-09-2025
bijgewerkt: 11-09-2025
canonical: true
owner: architecture
prioriteit: HOOG
status: TE_DOEN
completion: 0%
last_verified: 11-09-2025
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
- [ ] `docs/portal/index.html` bestaat en is interactief (zoek/filter/sort)
- [ ] Generator draait in pre‑commit en CI bij doc‑wijzigingen
- [ ] Config maakt hergebruik in andere repos mogelijk zonder codewijzigingen
- [ ] Documentatie: `docs/portal/README.md` met gebruik/ontwikkeling

## Relaties
- Richtlijnen: `docs/guidelines/CANONICAL_LOCATIONS.md`, `DOCUMENTATION_POLICY.md`
- Architectuur: `docs/architectuur/*ARCHITECTURE.md`
- Traceability: `docs/traceability.json`, `docs/backlog/requirements/REQ-REGISTRY.json`

