# ADOPTING.md — Portal & Generator Integratie

Deze handleiding beschrijft hoe je de Portal en Generator in een ander (of dit) project adopteert.

## Contract (frontmatter)
Elke doc (REQ/EPIC/US/BUG/…) heeft YAML‑achtige frontmatter:

```
---
id: REQ-021 | EPIC-003 | US-015 | BUG-001
status: TE_DOEN | IN_UITVOERING | GEREED | VOLTOOID | archived
prioriteit: KRITIEK | HOOG | GEMIDDELD | LAAG
owner: <team-of-persoon>
canonical: true|false
sprint: <label>
story_points: <int>
last_verified: <dd-mm-jjjj>
---
```

ID‑conventies en paden (canoniek):
- EPIC: `docs/backlog/EPIC-XXX/EPIC-XXX.md`
- US:   `docs/backlog/EPIC-XXX/US-YYY/US-YYY.md`
- BUG:  `docs/backlog/EPIC-XXX/US-YYY/BUG-ZZZ/BUG-ZZZ.md`
- REQ:  `docs/backlog/requirements/REQ-XXX.md`

## Configuratie
- Standaard web‑lookup providers en gewichten: `config/web_lookup_defaults.yaml`
- Traceability relaties: `docs/traceability.json` (REQ↔EPIC↔US)
- Portal bronnen: `docs/portal/config/sources.yaml`

## Generator draaien
```
python scripts/docs/generate_portal.py
```
- Schrijft `docs/portal/portal-index.json` + injecteert inline JSON in `docs/portal/index.html`

## Pre‑commit/CI snippets
- Pre‑commit (voorbeeld entry in `.pre-commit-config.yaml`):
```
- id: generate-portal-on-docs-change
  name: Generate portal (docs → portal)
  entry: bash scripts/docs/run_portal_generator.sh
  language: system
  pass_filenames: false
  files: ^docs/(?!portal/).+\.md$
  stages: [pre-commit]
```
- CI: zie voorbeeld `.github/workflows/portal.yml` (regenereren + commit/PR)

## Privacy & NFR’s
- Geen PII/secrets in portaldata of logs
- Sanitization toepassen op externe content (zie EPIC‑003 NFR’s)
- Respecteer canonical/archived flags in weergave/exports

## Veelgemaakte fouten
- Verkeerde paden (gebruik canonieke structuur)
- Vergeten traceability (REQ‑links in frontmatter/body)
- Broken links (draai de generator; linkscan staat in het project)

