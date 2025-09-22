---
id: CFR-BUG-030
titel: Expert Review‑tab omzeilt gate — ‘Minstens 1 context’ niet afgedwongen bij vaststellen
status: OPEN
severity: CRITICAL
component: ui-expert-review
owner: frontend-team
gevonden_op: 2025-09-22
canonical: false
applies_to: definitie-app@current
---

# CFR-BUG-030: Expert Review omzeilt GatePolicy (minstens één context)

## Beschrijving
In de Expert Review‑tab worden statuswijzigingen rechtstreeks via de repository uitgevoerd (`repository.change_status(...)`), waardoor de gate‑enforcement (US‑160, `GatePolicyService`) niet wordt toegepast. Hierdoor kan een definitie zonder context (alle drie lijsten leeg) tóch naar `ESTABLISHED` gaan, terwijl het beleid `min_one_context_required: true` voorschrijft.

## Verwacht gedrag
- Vaststellen in de Review‑tab loopt altijd via `DefinitionWorkflowService` zodat de gate wordt geëvalueerd:
  - Geen context → gate status `blocked` met reden “Geen context ingevuld (minimaal één vereist)”.
  - Soft‑gate → override flow met verplichte reden.
  - Pass → statuswijziging naar `ESTABLISHED`.

## Huidig gedrag
- UI roept direct `repository.change_status(...)` aan en omzeilt de gate‑policy (geen blok/override).

## Reproduceren
1) Maak of selecteer een definitie zonder context (alle drie contextlijsten leeg).
2) Open Expert Review‑tab en kies “Goedkeuren”.
3) Observeer dat de status wijzigt naar `ESTABLISHED` zonder gate‑controle of reden.

## Scope fix
- UI (Expert Review‑tab):
  - Vervang directe repository‑aanroepen door `DefinitionWorkflowService.submit_for_review(...)`/approve‑pad (of bestaande methoden die gate evalueren).
  - Toon gate‑status en redenen in de UI; bij `override_required` verplicht tekstveld (reden) en herhaal actie.
- Service wiring: zorg dat de tab zijn service via DI container ophaalt (zoals in Generator‑tab): `container.definition_workflow_service()`.

## Acceptatiecriteria
- [ ] Review‑tab gebruikt `DefinitionWorkflowService` voor vaststellen en toont gate‑status (pass/override_required/blocked).
- [ ] Hard‑gate bij missende context blokkeert vaststellen met duidelijke reden.
- [ ] Soft‑gate ondersteunt override met verplichte reden (notes) die wordt gelogd.
- [ ] Regressie: bestaande afwijs/terug‑naar‑draft paden blijven werken.

## Technische referenties
- Gate‑policy loader: `src/services/policies/approval_gate_policy.py`
- Gate evaluatie: `src/services/definition_workflow_service.py:_evaluate_gate`
- Huidige (te directe) aanroepen: `src/ui/components/expert_review_tab.py:564, 583` → `repository.change_status(...)`
- Gewenste DI: `src/services/container.py:343` (`definition_workflow_service()`)

## Relatie
- US-160 — Validatie‑gate bij Vaststellen (Option B) (deze bug verhindert correcte afdwinging)
- CFR-BUG-029 — Generator‑tab vereist eveneens ‘minstens 1 context’ (vroegtijdige afdwinging)

## Testen
- UI/integratie: scenario “geen context → blocked”; “alleen high issues/score ≥ soft → override_required met reden”; “pass → established”.

