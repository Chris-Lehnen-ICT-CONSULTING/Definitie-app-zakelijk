# Contributing Guidelines

Welkom! Dit document beschrijft hoe we bijdragen leveren en kwaliteitsregels handhaven.

## Kernprincipes
- Backlog-first: Werk-items gaan altijd via epics/user stories/bugs.
- Geen TODO-achtige comments in code: geen `TODO`, `FIXME`, `XXX`, `TBD`, `HACK`, `@todo`, `@fixme` in `src/`, `tests/`, `scripts/`.
- Traceability: Koppel elke wijziging aan een US/CFR-BUG/Epic in de PR.

## Workflow
1. Maak of link een issue/story/bug in `docs/backlog/…`.
2. Ontwikkel met kleine, gerichte wijzigingen.
3. Update relevante documentatie (story, mapping, arch docs) indien nodig.
4. Voeg tests toe of werk ze bij waar logisch.
5. Open een PR met verwijzing naar US/CFR-BUG en voldoe aan de checklist.

## Pre-commit en CI checks
- Pre-commit (lokaal):
  - `pip install pre-commit`
  - `pre-commit install`
  - Handmatige check: `bash scripts/ci/check_no_todo_markers.sh`
  - Backlog‑integriteit draait automatisch vóór commit: `scripts/docs/check_backlog_integrity.py` (faalt bij dubbele IDs of gebroken interne links).
  - Portaldata wordt automatisch gegenereerd vóór commit: `python scripts/docs/generate_portal.py` (wijzigingen aan `docs/**` regenereert `docs/portal/*`).
- CI gates:
  - No‑TODO gate: `.github/workflows/no-todo-markers.yml` blokkeert TODO‑achtige comments in code.
  - Docs‑integriteit: `.github/workflows/docs-integrity.yml` draait backlog‑integriteit + portal‑generatie met drift‑guard (faalt als portal‑outputs niet up‑to‑date zijn) en uploadt portal‑artefacten.

## PR Richtlijnen
- Voeg link toe naar relevante story/bug/epic (bijv. `US-041`, `CFR-BUG-015`).
- Beschrijf functionele impact en testdekking kort.
- Geen secrets/PII in code of logs.

## Documentatie & Locaties
- Stories: `docs/backlog/stories/US-XXX.md`
- Bugs: `docs/backlog/bugs/CFR-XXX-*.md`
- Epics: `docs/backlog/epics/`
- TODO Mapping: `docs/backlog/TODO-MAPPING.md`

Dank voor je bijdrage! ✨
