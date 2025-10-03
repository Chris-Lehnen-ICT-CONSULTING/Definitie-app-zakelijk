---
canonical: true
status: active
owner: architecture
last_verified: 2025-09-15
applies_to: definitie-app@current
titel: "EPIC-017: Iteratieve Verbeteringen - V2 feedback-loop met max 3 iteraties, FeedbackBuilder en stopcriteria (0.05 threshold)"
---

> **Statusupdate (2025-10-03):** Story US-170 is verplaatst naar [EPIC-026](../EPIC-026/US-170/US-170.md) en leeft daar verder als refactor-item.

# EPIC-017: Iteratieve Verbeteringen (V2 Orchestrator)

## Epic Overview
ID: EPIC-017
Titel: Iteratieve verbetering en feedbackloop voor definitiegeneratie (V2)
Status: ACTIVE (nieuw)
Priority: HIGH
Created: 2025-09-15
Updated: 2025-09-15
Owner: Architecture/Engineering
stories:
- US-188
- US-189

Doel: de iteratieve verbeteringscyclus (feedbackloop) realiseren bovenop de V2‑orchestrator, losgekoppeld van EPIC‑012, zodat EPIC‑012 kan worden afgerond zonder de iteratieve component. Deze epic bundelt REQ‑097 en de UI‑koppeling (voorheen US‑170 in EPIC‑012) plus relevante businesskennis uit US‑061.

## Business Value
- Verhoogde kwaliteit door gecontroleerde iteraties (max 3) met duidelijke stopcriteria.
- Transparante feedback (Violation→Feedback mapping) en learning‑loop zonder legacy afhankelijkheden.
- Meetbare voortgang per iteratie (scores, violaties, gate‑status) en UX‑inzicht via grafieken.

## Scope
### In Scope
- Iteratieve loop bovenop V2 (acceptatie ≥ 0.80 overall; category ≥ 0.75; improvement threshold 0.05; max 3 iteraties).
- FeedbackBuilder V2 (11+ mappings) als aparte service/module aan Orchestrator V2.
- UI‑koppeling (orchestration tab) naar V2 voor demo/visualisatie (achter feature flag).
- Telemetrie/metrics per iteratie; caching/hergebruik van voorbeelden waar zinvol.

### Out of Scope
- Backwards compatibility met legacy agent/iteraties in runtime.
- Security integratie (EPIC‑006) buiten minimale hooks.
- Database migraties buiten bestaande schema’s (schema.sql blijft bron).

## Dependencies
- V2 Orchestrator: `src/services/orchestrators/definition_orchestrator_v2.py`
- Businesskennis geëxtraheerd (US‑061) ✅
- Validation V2 contracten vastgesteld (UIResponse/ValidationDetails) ✅

## Requirements
- REQ‑097: Iteratieve Verbetering van Definities (V2 Orchestrator)
  - Path: `docs/backlog/requirements/REQ-097.md`

## Technical Context
- Stopcriteria: max 3 iteraties; stop bij acceptatie of bij < 0.05 scoreverbetering.
- Drempels: overall ≥ 0.80; categorie ≥ 0.75; geen kritieke violations.
- Voorbeelden optimalisatie: voorbeelden alleen in 1e iteratie genereren en hergebruiken.
- FeedbackBuilder: prioritering (kritiek → suggesties → overig), max 5 items/iteratie, deduplicatie.
- UI: grafieken voor score per iteratie, violations per severiteit, diff t.o.v. vorige iteratie.

Bronnen:
- US‑061 Business Knowledge Extraction: `docs/backlog/EPIC-026/US-061/BUSINESS_KNOWLEDGE_EXTRACTION.md`
- EPIC‑012 (context en verwijzingen): `docs/backlog/EPIC-012/EPIC-012.md`

## Acceptatiecriteria (Epic)
- Iteratieloop en stopcriteria werken contract‑conform (zonder legacy best_iteration).
- FeedbackBuilder V2 levert deterministische, prioriteerde feedback per iteratie.
- UI orchestration tab (V2) toont iteratie‑metrics; flag‑beschermd; geen legacy imports.
- Tests (unit/integratie) en determinisme gegarandeerd; CI‑gates blijven groen.

## Definition of Done (Epic)
- US‑188..US‑190 gerealiseerd en getest.
- Documentatie en portal bijgewerkt; geen broken links.

## Risks & Mitigations
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Performance door extra iteraties | Medium | Medium | Voorbeelden caching, early‑stop, mock validatie voor offline test |
| Feedback duplicatie/ruis | Medium | Low | Deduplicatie + mapping‑prioriteit |
| Contract drift met UI | Medium | Low | Strikte V2‑UIResponse + contracttests |

## Implementation Plan
### Fase 1 — FeedbackBuilder V2 (US‑189)
- Port violation→feedback mappings (US‑061) naar service/module; deterministische selectie/prioritering; API voor “next feedback set”.

### Fase 2 — Iteration Controller (US‑188)
- Voeg iteratielus toe rond generate→validate→feedback; stopcriteria/drempels; telemetry hooks; hergebruik voorbeelden.

### Fase 3 — UI Wiring (US‑170)
- Orchestration tab aan V2 koppelen; grafieken/metrics; flag‑achter de schermen; geen legacy imports.

### Fase 4 — Tests & Gates
- Unit/integratie; determinisme asserts; CI‑gates voor legacy‑patronen blijven actief.

## Notes
- EPIC‑012 kan worden afgerond zonder deze epic; iteratieve verbeteringen leven hier.
- Legacy DefinitieAgent blijft gearchiveerd of strikt achter demo‑flag; geen runtime‑pad in hoofdflow.

## Legacy Business Knowledge (geconsolideerd in deze EPIC)
Deze sectie maakt de EPIC de canonieke plek voor de iteratieve businesskennis, zodat er geen broncode uit archief nodig is om het ontwerp te begrijpen.

- Stopcriteria en drempels (uit US‑061):
  - max_iter: 3 (configurabel)
  - improvement_threshold: 0.05 (stagnatie)
  - acceptance_threshold (overall): 0.80 (policy‑gedreven)
  - category_threshold: 0.75 (policy‑gedreven)
  - forbid_critical: true (policy)

- Iteratie‑pseudocode (V2‑ontwerp):
  - init = generate(); score0 = validate(init)
  - if gate_pass(score0): return init
  - for i in 2..max_iter:
    - feedback = FeedbackBuilderV2(score(i‑1), violations(i‑1), history)
    - candidate = generate(feedback, reuse_examples= i>1)
    - score = validate(candidate)
    - if score.overall - best.overall < improvement_threshold: break
    - update best = max(best, candidate, key=score)
    - if gate_pass(score): break
  - return best

- FeedbackBuilder (samenvatting):
  - Inputs: violations (V2 schema), iteration, history
  - Mapping prioriteit: kritiek → suggesties → overig
  - Deduplicatie; max 5 feedbackitems/iteratie; deterministische sortering
  - Voorbeeldregels (uit US‑061): CON‑01 (context‑specifiek), ESS‑01..05 (essentie/kenmerken), INT‑01/03 (formulering), STR‑01/02 (structuur)

- Voorbeelden (prestatie):
  - Genereer voorbeelden in iteratie 1; hergebruik in latere iteraties, tenzij feedback expliciet om nieuwe voorbeelden vraagt.

- Telemetrie/UX:
  - Bewaar per iteratie: overall_score, violations, duration, feedback_used, reused_examples
  - UI toont score per iteratie, violations per severity en diff t.o.v. vorige iteratie

Referentie (historische code, niet leidend): `docs/archief/legacy/orchestration/definitie_agent.py`
