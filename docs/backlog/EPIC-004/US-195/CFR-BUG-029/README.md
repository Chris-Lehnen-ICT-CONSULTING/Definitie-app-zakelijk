---
id: CFR-BUG-029
titel: Generator‑tab — ‘Minstens 1 context’ niet afgedwongen (kan genereren zonder context)
status: OPEN
severity: HIGH
component: ui-generator
owner: frontend-team
gevonden_op: 2025-09-22
canonical: false
applies_to: definitie-app@current
---

# CFR-BUG-029: Generator‑tab respecteert ‘minstens 1 context’ niet

## Beschrijving
In de Definition Generator‑tab kan de gebruiker definities genereren terwijl alle drie contextvelden leeg zijn (organisatorische_context, juridische_context, wettelijke_basis). Volgens het gate‑beleid en de handover moet “minstens 1 context” verplicht zijn. Het ontbreken van deze vroege afdwinging leidt tot inconsistente UX (pas bij vaststellen wordt geblokkeerd) en tot definities zonder duidelijke context.

## Verwacht gedrag
- De generator‑actie is geblokkeerd zolang alle drie contextlijsten leeg zijn.
- De UI toont een duidelijke melding bij de contextselectie: “Minstens één context is vereist (organisatorisch of juridisch of wettelijk).”
- Zodra minimaal één lijst een waarde bevat, wordt de actie weer ingeschakeld.

## Huidig gedrag
- De gebruiker kan zonder context door naar generatie (en zelfs opslaan als concept) vanuit de Generator‑tab.
- Pas in de gate bij vaststellen (US‑160) wordt “minstens één context” afgedwongen.

## Reproduceren
1) Open de Definition Generator‑tab.
2) Zorg dat de globale context leeg is (geen waarden in alle drie contexten).
3) Start een generatie (of kies “Bewaar als concept en bewerk”).
4) Observeer dat de actie niet wordt tegengehouden en er geen waarschuwing verschijnt.

## Scope fix
- UI (Generator‑tab):
  - Disable/guard de knoppen voor genereren en “Bewaar als concept en bewerk” wanneer `organisatorische_context`, `juridische_context` en `wettelijke_basis` alle drie leeg zijn.
  - Toon een korte waarschuwing naast de contextselector.
- Optioneel service‑guard: early‑return met nette melding wanneer toch zonder context wordt aangeroepen (defensief), zonder gatepolicy te dupliceren.

## Acceptatiecriteria
- [ ] Knoppen voor genereren/opslaan zijn disabled zolang alle contextlijsten leeg zijn.
- [ ] Duidelijke NL‑melding zichtbaar bij lege context (minstens één vereist).
- [ ] Zodra minimaal één context is ingevuld, verdwijnt de melding en worden acties mogelijk.
- [ ] Regressie: duplicate‑precheck (US‑195) blijft werken wanneer contexten wel ingevuld zijn.

## Technische referenties
- Generator‑tab component: `src/ui/components/definition_generator_tab.py`
- Contextbron (UI): `SessionStateManager.get_value("global_context", ...)`
- Gate‑policy (ter referentie): `config/approval_gate.yaml` (`min_one_context_required: true`)

## Relatie
- US-195 — Duplicate‑gate bij genereren definitie met 3‑contextkeuze (zelfde flow, eerdere check)
- US-160 — Validatie‑gate bij Vaststellen (Option B) (harde afdwinging bij vaststellen)

## Testen
- UI/integratie: scenario “alle contexten leeg → genereer disabled + melding”.
- Positief: bij één ingevulde context is genereren weer mogelijk en loopt de duplicate‑precheck.

