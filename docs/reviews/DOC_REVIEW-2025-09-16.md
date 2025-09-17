---
titel: Documentatie Review Rapport
generated: 2025-09-16
status: draft
owner: documentation-team
applies_to: definitie-app@current
---

# Documentatie Review — Stand van Zaken en Aanpak

Bronnen: `docs/docs-compliance-check.md`, `DOCUMENTATION_COMPLIANCE_REPORT.md`, `docs/INDEX.md`, `README.md`, `CLAUDE.md`.

## Samenvatting
- Compliance‑scan (2025‑09‑08): 272 bestanden gecheckt, 16 volledig compliant, 242 met issues, 191 met warnings, 1 canonical conflict.
- Belangrijkste problemen: ontbrekende frontmatter (veel), gebroken links (oude paden), en overlap/verspreide “canonical” bronnen voor dezelfde thema’s.
- Positief: centrale index en meerdere statusrapporten aanwezig; portal/index bevat zichtbare ankers.

## Detailbevindingen

1) Frontmatter ontbreekt/ontoereikend
- Veel docs missen minimaal: `titel`, `status`, `owner`, `applies_to`, `last_verified`.
- Voorbeelden (uit compliance‑check): `MIGRATION-FINAL-STATUS.md`, `NORMALISATIE_RAPPORT.md`, `refactor-log.md`, veel `requirements/REQ-*.md`, `testing/*`.

2) Gebroken/verouderde links
- Oude mappenamen (bv. `vereisten/` i.p.v. `requirements/`), verplaatste EPIC/US paden, relatieve links naar verplaatste root‑bestanden.
- Voorbeelden: `COMPLIANCE-DASHBOARD.md`, `TRACEABILITY-MATRIX.md`, `DOCUMENTATIE-PLANNING-OVERZICHT.md`, diverse stories.

3) Canonical conflicts
- Meerdere INDEX‑varianten (stories/INDEX.md, epics/INDEX.md) — onduidelijk welke “bron van waarheid” is.

4) Synchronisatie code ↔ docs
- EPIC‑010/V2‑gates zijn beschreven, maar sommige UI/Service‑implementaties wijken af (zie Code Review). Documenten benoemen “geen `asyncio.run` in services” en “V2‑dict‑contracten”; nog inconsistenties in code.

## Aanbevolen Aanpak

Fase 1 — Baseline herstellen (laag risico, hoge impact)
- Voeg minimale frontmatter toe aan top‑level en kernrapporten: `titel`, `status`, `owner`, `applies_to`, `last_verified: 2025-09-16`.
- Fix links in kernindexen en dashboards: pas paden aan naar actuele locaties (`requirements/`, `docs/backlog/...`).
- Markeer “canonical” per thema in frontmatter en verwijder of archiveer duplicaten/alternatieven met verwijzing.

Fase 2 — Themastructuur consolideren
- Source of Truth per domein:
  - Architectuur/EPIC‑010: `README.md` + `docs/EPIC-STORY-MIGRATION-PLAN.md` (canonical)
  - Validatie/Orchestrator: `docs/development/validation_orchestrator_implementation.md`
  - Requirements: `docs/requirements/` (elk REQ‑bestand met `last_verified` en status)
  - Tests/Plans: `docs/testing/` (testplannen, coverage, resultaten) — links corrigeren
- Verplaats verouderde/overlappende docs naar `docs/archief/` met redirect/verwijzing.

Fase 3 — Sync met implementatie (EPIC‑010)
- Documenteer feitelijke V2‑contracten (sleutels: `definitie_gecorrigeerd`, `validation_details`, `voorbeelden`, `metadata`).
- Beschrijf endpoint‑timeouts en rate limiting: verwijs naar `src/config/rate_limit_config.py` en UI‑bridge gebruik.
- Leg vast: geen `asyncio.run` in services; enkel via `ui/helpers/async_bridge.py` — zet dit expliciet in “Coding Standards”.

## Quick‑Win Patches (docs)
- Voeg frontmatter toe aan: `MIGRATION-FINAL-STATUS.md`, `NORMALISATIE_RAPPORT.md`, `refactor-log.md`, `DOCUMENTATION_COMPLIANCE_REPORT.md`, en `EPIC-STORY-*` rapporten.
- Corrigeer links in: `COMPLIANCE-DASHBOARD.md`, `TRACEABILITY-MATRIX*.md`, `DOCUMENTATIE-PLANNING-OVERZICHT.md`, stories met oude `vereisten/` paden.
- Kies en label één `INDEX.md` per categorie als canonical; voeg bovenaan notitie toe in alternatieven: “Zie canonical: <pad>”.

## Acceptatiecriteria (Docs DoD)
- Elk kernbestand heeft frontmatter met `last_verified` ≤ 30 dagen.
- Geen gebroken links in `docs/` (controle via bestaande compliance‑check).
- Eén canonical bron per thema; alternatieven ge‑archiveerd of verwijzen expliciet.
- Docs reflecteren actuele code‑gates: V2‑contracts, central timeouts, geen `asyncio.run` in services.

## Volgende Stappen
1) Draai de bestaande compliance‑check opnieuw na Quick‑Win patches en voeg samenvatting toe aan dit rapport.
2) Werk `docs/INDEX.md` bij met een korte “Waar is wat?” sectie per thema.
3) Borging: voeg pre‑commit check of CI job die frontmatter + linkvalidatie afdwingt.

