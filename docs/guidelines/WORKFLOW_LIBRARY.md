---
aangemaakt: '08-09-2025'
applies_to: definitie-app@current
bijgewerkt: '08-09-2025'
canonical: true
last_verified: 05-09-2025
owner: architecture
prioriteit: medium
status: active
---



# Werkstroom Library

Doel: meerdere, doelgerichte workflows naast de bestaande TDD→Uitrol creëren, zodat we niet elke opdracht door hetzelfde zware pad sturen. Dit document beschrijft de beschikbare workflows, hun fasen, agents, en wanneer je welke inzet.

## Overzicht (wanneer welke workflow?)
- Analyse: wanneer de vraag nog niet klaar is voor implementatie; we willen user story, acceptatiecriteria en architectuur vormen.
- Review: wanneer er al code/diffs zijn en er een gestructureerde review nodig is zonder implementatie.
- Document Cleanup: wanneer documentatie opgeschoond, gestandaardiseerd en geherstructureerd moet worden.
- Refactor Only: wanneer gedrag ongewijzigd blijft en we enkel kwaliteit/structuur verbeteren.
- Hotfix: wanneer er een urgente productie‑bug is met versnelde route en gecontroleerde risico’s.
- Full TDD: wanneer we een complete feature/fix van A tot Z implementeren met zware kwaliteitsgates.

## 1) Analyse Werkstroom
- Doel: van vraag → user story met SMART criteria → EA/SA/TA artefacten.
- Fasen en agents:
  - ANALYSIS: business-analyst-justice (output: user story + BDD acceptatiecriteria)
  - DESIGN: justice-architecture-designer (output: EA/SA/TA, API contracten, NFRs)
  - DOC-CHECK: doc-standards-guardian (output: canonical locaties, frontmatter, index updates)
- Gates (per fase): SMART criteria, BDD compleet; EA/SA/TA aanwezig; docs conform policy.
- Exit: story is KLAAR FOR DEV, geen tests/code vereist.

## 2) Review Werkstroom
- Doel: systematische review van code/diff met oordeel en suggesties; geen implementatie.
- Fasen en agents:
  - REVIEW: code-reviewer-comprehensive (output: reviewrapport, verdict)
  - OPTIONAL-FOLLOWUP: refactor-specialist (micro‑refactors met tests groen)
- Gates: reviewrapport volledig, geen 🔴 blockers; bij follow‑up blijven alle tests groen.
- Exit: reviewrapport + aanbevelingen; implementatie is optioneel en separaat.

## 3) Document Cleanup Werkstroom
- Doel: documentatie standaardiseren, ontdubbelen, frontmatter/links repareren en canonical structuur herstellen.
- Fasen en agents:
  - AUDIT: doc-standards-guardian (detecteer ontbrekende frontmatter, broken links, duplicaten)
  - FIX: doc-standards-guardian (+ prompt-engineer support) (auto‑fix en herstructurering)
  - VERIFY: quality-assurance-tester (linkcheck, structuurvalidatie)
- Gates: mandatory files aanwezig; canonical paths; geen broken links; index/overzichten geüpdatet.
- Exit: schone, consistente docs; geen code of CI nodig.

## 4) Refactor Only Werkstroom
- Doel: kwaliteit/structuur verbeteren zonder gedrag te wijzigen.
- Fasen en agents:
  - PLAN: refactor-specialist (scope, micro‑refactors, impact)
  - APPLY: refactor-specialist (kleine, atomaire refactors)
  - VERIFY: quality-assurance-tester (alle tests nog groen, coverage ≥ baseline)
- Gates: geen gedragswijziging; tests blijven groen; refactor‑log bijgewerkt.
- Exit: code schoner, prestaties en leesbaarheid verbeterd, zonder functionele impact.

## 5) Hotfix Werkstroom
- Doel: snelle, gecontroleerde fix voor productie‑incidenten met minimale vertraging en maximale veiligheid.
- Fasen en agents:
  - TRIAGE: tdd-orchestrator (OVERRIDE protocol; classificatie P1/P2, blast‑radius)
  - FIX: developer-implementer (+ minimal test bij voorkeur) (patch gericht; geen scope‑creep)
  - REVIEW-LIGHT: code-reviewer-comprehensive (snelle controlerapportage, security check)
  - DEPLOY: devops-pipeline-orchestrator (staging→prod met handmatige approval; rollback klaar)
- Gates: issue gereproduceerd of helder; minimal test of reproduceerbaar scenario; manual approval voor prod; rollback‑plan aanwezig.
- Exit: productie hersteld; incidentrapport en post‑mortem gepland.

## 6) Full TDD Werkstroom (Bestaand)
- Doel: volledige implementatie van feature/fix met RED→GREEN→REFACTOR en streng bewaakte gates.
- Verwijzing: docs/guidelines/TDD_TO_DEPLOYMENT_WORKFLOW.md
- Let op: gebruik deze niet standaard voor documentatie/kleine wijzigingen; kies een lichtere workflow als passend.

## Artefacten en Locaties (samengevat)
- User stories: docs/backlog/stories/MASTER-EPICS-USER-STORIES.md
- Architectuur: docs/architectuur/
- Reviews: docs/reviews/<ID>-review.md
- Refactor log: docs/refactor-log.md
- Deployments: docs/deployments/<date>.md
- Index: docs/INDEX.md, docs/guidelines/CANONICAL_LOCATIONS.md
