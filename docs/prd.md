# Definitie‑app — Stabilization MVP PRD (Concept)

- Versie: 0.1
- Datum: 2025-10-13
- Auteur: Product Manager (PM)
- Status: Concept/Voorstel

## 1. Samenvatting

Brownfield project is functioneel maar uit de hand gelopen: overvolle/chaotische backlog, aanwezige god‑objecten die werken maar uitbreidbaarheid blokkeren. Doel van dit Stabilization MVP is focus te herstellen, levercadans terug te brengen (wekelijkse release), en toekomstige verbeteringen mogelijk te maken zonder big‑bang refactors. Security is expliciet geen prioriteit voor dit MVP.

## 2. Context en Probleemdefinitie

- Single developer, single user applicatie.
- Backlog is de grootste bottleneck: te veel items, onduidelijke prioriteit, context switching.
- God‑objecten bestaan; huidige functionaliteit werkt maar is fragiel bij uitbreiding.
- Security: buiten scope voor dit MVP.

## 3. Doelen en KPI’s

- Doel: Stabilisatie + voorspelbare levering met minimale ingreep.
- KPI’s (MVP):
  - KPI1 Lead time per story ≤ 2 dagen door WIP=1.
  - KPI2 Minimaal 1 release per week.
  - KPI3 Regressie: 0 kritieke regressies per release (gedekt door smoke/contract tests).
  - KPI4 Backlog: 80% van Inbox getriaged in week 1; Ready‑kolom ≤ 3.

## 4. Scope

- In scope (MVP):
  - Backlog Reset: Inbox → Triage → Ready(≤3) → Doing(1) → Done workflow.
  - God‑Object Containment: introductie van kleinst mogelijke `Facade/Service` laag rond kritieke god‑object(en).
  - Verticale slice via nieuwe facade (één betekenisvolle gebruikersflow).
  - Lichtgewicht testbasis: smoke + contracttests bij de facadegrenzen.
  - Release‑cadans + changelog per release.
- Buiten scope (MVP):
  - Big‑bang herschrijvingen.
  - Nieuwe grote features die niet bijdragen aan stabilisatie/doorknippen van koppelingen.
  - Security hardening/pen‑tests; performance‑tuning buiten noodzakelijke randvoorwaarden.

## 5. Doelgebruiker en Use‑Cases (MVP)

- Doelgebruiker: interne single user (ontwikkelaar/product).
- Primaire use‑cases voor MVP:
  - UC1 Dagelijks kunnen werken zonder regressies in bestaande kernflow(s).
  - UC2 Snel kunnen leveren (kleine stories, WIP=1) met duidelijke release‑notities.
  - UC3 Nieuwe code kan aangesloten worden op een stabiele facade zonder direct god‑objecten te raken.

## 6. Epics (MVP‑scope)

- E1 Backlog Reset en Workflow
- E2 God‑Object Containment via Facade + Seams
- E3 Verticale Slice door de Facade
- E4 Release‑cadans en Basis Validaties

## 7. Functionele Requirements (FR)

- FR1: Bestaande kernfunctionaliteit blijft werken met ongewijzigd gedrag (backward compatible).
- FR2: Een `Facade/Service` abstraction levert de minimaal benodigde use‑cases voor de eerste verticale slice.
- FR3: Nieuwe/gewijzigde code gebruikt uitsluitend de facade i.p.v. direct god‑objecten.
- FR4: Board/flow aanwezig: Inbox, Triage, Ready(≤3), Doing(1), Done.
- FR5: Release per afgeronde story met korte changelog.

## 8. Niet‑Functionele Requirements (NFR)

- NFR1: Prestatie‑impact van de facade ≤ 10% t.o.v. huidige hot‑paths.
- NFR2: Minimale testset: smoke tests op kritieke flows + contracttests op de facade.
- NFR3: Observability: basislogregels op de facade‑grenzen (start/stop/foutgevallen).
- NFR4: Security: buiten scope voor MVP (geen nieuwe eisen, geen blockers).

## 9. Compatibiliteitseisen (CR)

- CR1: Externe API’s/CLI/UI blijven backward compatible (geen brekende wijzigingen).
- CR2: Database‑schema ongewijzigd voor MVP.
- CR3: Bestands‑/config‑locaties blijven stabiel.
- CR4: Integraties met bestaande modules blijven werken via de facade.

## 10. Architectuur & Implementatie‑Aanpak

- Principe: “Contain, don’t rewrite”. Gebruik Strangler/Seams‑patroon.
- Stap‑voor‑stap:
  1) Snapshot huidig gedrag van de god‑object‑use‑cases via contracttests.
  2) Introduceer `Facade/Service` die exact deze use‑cases exposeert (geen extra scope).
  3) Leid nieuwe en aangepaste code om via de facade (enkel deze laag mag god‑objecten benaderen).
  4) Per story: micro‑refactor achter de facade (extract method/pure function/kleine klasse).
  5) Geen big‑bang; geleidelijke strangling van god‑objecten.
- Codeorganisatie (voorstel, project‑agnostisch):
  - Nieuwe module/namespace: `.../facade` of `.../services` met duidelijke contracten (interfaces/public API).
  - Tests: `tests/.../test_facade_contract.*` + rooktests voor kernflows.
- Releaseproces:
  - Wekelijkse release, of sneller per story zodra tests groen zijn.
  - Changelog per release; tag/versienummering incrementeel.

## 11. Planning & Mijlpalen

- Fase 0 (0,5 dag): Freeze + mini‑oriëntatie; noteer pijnpunten; bepaal eerste verticale slice.
- Fase 1 (0,5 dag): Artefacten (dit PRD), workflow/board, DoR/DoD.
- Fase 2 (1 dag): Backlog Reset (kill/park/keep), Ready maximaal 3.
- Sprint 1 (1 week):
  - Deliverable: 1 verticale slice via facade + contracttests + release + changelog.
- Doorlopend: WIP=1, weekly release, micro‑refactors in de seam (10–20% tijd per story).

## 12. Acceptatiecriteria MVP

- AC1: Board actief met kolommen en WIP‑regels; Ready ≤ 3, Doing = 1.
- AC2: Facade aanwezig en gebruikt door eerste verticale slice; tests groen.
- AC3: Minstens 1 release live met changelog en 0 kritieke regressies.
- AC4: Backlog getriaged; ≥ 80% Inbox opgeschoond.

## 13. Risico’s en Mitigaties

- R1 Scope creep → M1 Strikt MVP, Ready ≤ 3, WIP=1, timeboxing.
- R2 Verborgen koppelingen in god‑objecten → M2 Contracttests + kleine stappen + observability.
- R3 Tijdsdruk single dev → M3 Verticale slices, geen big‑bang, kleine increments.
- R4 Regressies → M4 Smoke + contracttests, release na groen.

## 14. Assumpties en Open Vragen

- Assumpties:
  - A1 Single user context blijft gelden gedurende MVP.
  - A2 Geen nieuwe externe integraties in MVP.
- Open vragen (in te vullen):
  - OV1 Welke specifieke gebruikersflow is de eerste verticale slice?
  - OV2 Welke god‑object(en) prioriteren we voor de eerste facade?
  - OV3 Zijn er kritieke data‑/rapportagepaden die absoluut niet mogen veranderen?

## 15. Bijlagen/Referenties

- Brownfield Recovery plan(nen) in `docs/planning/`.
- Eventuele eerdere PRD’s in `docs/archief/`.

---

Dit document is een voorstel (Concept). Na beantwoording van de open vragen en bevestiging van de scope worden epics en stories uitgewerkt door PO/SM en ingepland volgens WIP=1 en weekly release.
