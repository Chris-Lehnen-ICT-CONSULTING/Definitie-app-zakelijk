# DEF-768 — ESS-05-bewijsregelroute aansluiten in de app (stap 2) — plan v1

29-09-2026 · basis `667f1d484` · uitvoerder Claude Code, zelf, geen agents · akkoord Chris op stap 2:
de nieuwe route vervangt `Ess05AssessmentService` (`ess05-assess/19`), zonder schakelaar. ESS-05 blijft
`no_score` (`distinction_assessment`) en de oude code blijft staan.

**Status: STOP na dit plan.** De nieuwe service kan niet alle huidige contractvelden leveren, en
drie ontwerpkeuzes veranderen wat de gebruiker ziet. Chris moet ze nemen; zie §4. Er is nog geen code gewijzigd.

## 1. Keten na de aansluiting

1. **Invoer.** `validation_orchestrator_v2._beoordeel_onderscheid` stelt de actieve buren samen, net als nu.
   - Bronnen: opgeslagen besluiten, verse repository en `gerelateerde_begrippen`.
   - Vingerafdruk en bindingscontext worden berekend zoals nu.
   - `contract.beoordelingsmateriaal(...)` levert `{definition, context, meaning, source:<id>, neighbour:<id>}`, hetzelfde formaat als de proeven.
   - Daarvan maakt de orchestrator `br.Vergelijkingsinvoer(term, materiaal, buren=((id, term), …), onvolledig=∅)`.
   - `onvolledig=∅` mag, omdat de app nooit afkapt: een passage langer dan 8000 tekens blijft zoals nu een technische fout (`input_truncated`). Die grens verhuist mee naar de adapter.
2. **Interpretatie.** `Ess05BewijsregelService.beoordeel` doet één aanroep (prompt `ess05-interpretatie-prompt/4`, `task_type="validation"`) via het bestaande transport (`eenmalige_aanroep` / `ai_beoordeling_transport.py`). Retry- en cachegedrag blijven ongewijzigd.
3. **Deterministische regels.** `valideer_interpretatie` en daarna `controle_eenheden`: kern, doel en één eenheid per buur.
4. **Lokale controles.** Per eenheid volgt één aanroep van `Ess05LocalVerificationService` (`ess05-local-verify/1`). De eerste die niet `supported` is, geeft `error`/`semantische_controle_mislukt`.
5. **Uitkomst.** `pas_regels_toe` geeft `pass`, `fail`, `review_required` of `error`. F7 (buurnaam draagt betekenis) en het casus-E-besluit (voorwaarde als niet-kernkenmerk → `review_required`) zitten al in de regels (bewijsregels/6); de app voegt er niets aan toe.

**Scherm.** Het document komt op de bestaande plek: `ess05_assessment`, en per buur `ess05_actieve_buren`.
- `distinction_assessment` herleidt het tot een `Ess05Uitkomst` en daarna een `RuleOutcome`:
  - pass → PASS
  - fail → FAIL, adviserend (`no_score`)
  - error → ERROR
  - anders → REVIEW_REQUIRED
- De editor (`definition_edit_tab.py`), `validation_view._ess05_regels` en `validation_renderer` tonen verder, net als nu:
  - het oordeel per buur;
  - de ene vraag;
  - de herkomst en bevestiging;
  - de knoppen voor bevestigen en afwijzen.

## 2. Aansluiting per laag (kleinste reikwijdte)

| Laag | Wijziging |
|---|---|
| `Ess05BewijsregelService` | Nieuwe app-adapter `assess(begrip, tekst, contexten, bronnen, *, buren, intentie, uitgesloten_termen, correlation_id)` plus `binding()`. De adapter bouwt de invoer, draait `beoordeel` en geeft een document `contract_version: "ess05/3"` terug. Inhoud: vingerafdruk, status, fout, versies/binding, ruwe interpretatie plus sha, per controle de pakket-sha en uitkomst, regelsamenvatting per buur en rendertekst. De docstring "de standaard ESS-05-keten gebruikt haar niet" vervalt. |
| `services/container.py` | `ess05_assessment_service` levert voortaan de bewijsregelservice, met een `Ess05LocalVerificationService` erbij. Er komt geen tweede property en geen schakelaar. |
| `definition_orchestrator_v2.py` | Ongewijzigd: de orchestrator krijgt de dienst uit de container. De generatieburen blijven zoals ze zijn. |
| `validation_orchestrator_v2.py` | Ongewijzigd, afgezien van de naam en het type in de logmelding. De aanroepvorm `assess(...)` en `binding().als_dict()` blijven gelijk. |
| `domain/ess05/contract.py` / `distinction_assessment` | `_valideer_beoordeling` splitst op `contract_version`. **ess05/3** krijgt een nieuwe replay: <ul><li>controle op vingerafdruk, binding en bindingscontext;</li><li>de uitkomst opnieuw afleiden met `valideer_interpretatie` en `pas_regels_toe` uit de opgeslagen interpretatie;</li><li>de opgeslagen controles moeten gelijk zijn aan de herberekende `controle_eenheden`-pakketten, en alle moeten `supported` zijn.</li></ul> **ess05/2** wordt "verouderd — toets opnieuw" (open). Buuroordelen worden per buur onderdelen van de bestaande `Ess05Uitkomst`; zie keuze B. |
| Schema 2.4.0 | `ess05_assessment` is vrij van vorm: alleen `status` en `fingerprint` zijn verplicht. Alleen de beschrijvingstekst gaat van ess05/2 naar ess05/3. Omdat 2.4.0 nog niet op main staat, is geen nieuwe versie nodig. |
| UI | Structureel ongewijzigd. De voorstelknoppen blijven leeg (keuze A). |

## 3. Tests (TDD, alleen stubs)

De nieuwe tests zijn eerst rood en worden daarna groen. Ze dekken:
- de container levert de bewijsregelservice;
- de validatie-orchestrator roept die aan en roept `ess05-assess/19` nooit aan;
- het document is ess05/3;
- de evaluator zet elk van de vier uitkomsten om;
- een opgeslagen ess05/2-document geeft "toets opnieuw";
- de weergave in `validation_view` en de editor klopt.

Een stubmodel geeft de interpretatie en de controleantwoorden. Er is geen netwerk. De bestaande tests van de oude route op de app-keten (onder andere `test_def768_ess05_evaluator`, `…_wrapper`, `…_editservice`, `conftest` bevroren antwoorden, offline journey) gaan mee naar de nieuwe route. De tests van de oude service zelf blijven staan, omdat de code blijft.

## 4. Keuzes voor Chris (reden voor de STOP) — met advies

**A. Modelvoorstellen voor buren vervallen.** De oude route laat het model buren voorstellen (`review.proposals`, knop "➕ Neem voorstel over", `definition_edit_tab.py:1744`). De bewijsregelroute doet geen voorstellen: het veld kan niet meer worden gevuld.
*Advies:* accepteren. Het veld blijft in het contract maar is altijd leeg, en de UI verbergt de knop dan vanzelf. Buren komen uit de repository, de generatieburen en `gerelateerde_begrippen`. Een aparte voorstelaanroep zou weer een tweede prompt en route zijn.

**B. Bevestigingsbeleid.** Nieuwe repository-buren zijn onbevestigd (`contract.py:327`). In de oude app telt `niet onderscheiden` alleen als fail bij een **bevestigde** buur; anders blijft het open met de vraag om te bevestigen (`_buurstatus`, `contract.py:1233`). Een pass vereist minstens één bevestigde buur. De bewijsregels kennen geen bevestiging: `niet_onderscheiden` is daar altijd fail.
*Advies:* het app-beleid houden als dunne afbeelding na `pas_regels_toe`:

| Buuroordeel | Buur | Wordt |
|---|---|---|
| `niet_onderscheiden` | bevestigd | fail |
| `niet_onderscheiden` | onbevestigd | open, met de vraag om de buur te bevestigen of af te wijzen |
| `onderscheiden` | — | voldoet |
| `open` | — | open |
| geen bevestigde buur | — | open |

Een kern zonder kenmerk blijft fail. Een onbevestigde repositoryterm is geen vastgesteld begrip (K-1), en met dit beleid blijft de bevestigknop in de UI zinvol. Alternatief: de regeluitkomst ongewijzigd doorgeven, maar dan geeft elke gelijkende repositoryterm direct een (adviserende) fail.

**C. Aantal aanroepen en wachttijd.** De oude route doet 2 aanroepen (beoordeling + verificatie). De nieuwe doet 1 interpretatie + 2 (kern, doel) + 1 per buur, na elkaar. Bij drie buren zijn dat er 6. Dat ligt ver boven de UI-norm en raakt het kostenkader. Parallel draaien of cachen valt buiten deze stap, want retry/cache blijven ongewijzigd.
*Advies:* voor nu accepteren (ESS-05 draait alleen bij expliciet valideren). Meet het na aansluiting met de stubtelling en maak een apart issue voor parallelle lokale controles.

**D. (bevestiging gevraagd, geen nieuwe keuze)**
- Lege-ruimte-bevestiging door een deskundige blijft een pass zonder AI-aanroep.
- Zonder actieve buren is er geen AI-aanroep: de uitkomst is open met de bestaande vraag "voeg verwante begrippen toe".
- Opgeslagen ess05/2-documenten worden niet meer afgespeeld via de oude route. Ze tonen "verouderd — toets opnieuw", in lijn met één route.

## 5. Niet in deze stap

- Geen verwijdering; de verwijderlijst volgt ná de aansluiting, omdat het grep-bewijs "ongebruikt" pas dan klopt.
- Geen wijziging aan `ESS-05.json`, R1–R18 of hun grootboeken, en geen retry/cache.
