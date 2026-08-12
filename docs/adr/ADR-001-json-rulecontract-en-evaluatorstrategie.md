# ADR-001: JSON-rulecontract met expliciete evaluatorstrategieën

**Status:** Geaccepteerd · **Datum:** 2026-08-11 · **Beslisser:** Chris

## Context

DefinitieAgent bevat 53 JSON-regelrecords en twee niet-productieve Pythonlagen
onder `src/toetsregels/validators/` en `src/toetsregels/regels/`. De actieve
V2-keten laadt JSON en voert regels uit via `ModularValidationService`, met een
generieke evaluator en hardcoded uitzonderingen.

De Pythonlagen stammen uit een eerdere hybride architectuur. Zij zijn geen
onafgemaakte opvolger van `_evaluate_json_rule`: het expliciete V2-plan koos
later voor JSON-leidende validatie zonder legacy `.py`-aanroepen. De Pythonlagen
bevatten bovendien verkeerd genummerde of inhoudelijk afwijkende validators.

Tegelijk implementeert de actieve generieke evaluator niet alle regelbetekenissen
volledig. Onder meer voorkeurstermen, definitietekst-overlap, kwalificaties en
cycli tussen meerdere definities vereisen andere invoer of algoritmen dan een
regex op één tekst.

Het inhoudelijke Cowork-onderzoek toont daarnaast dat 44 JSON-records een goed
en fout voorbeeld bevatten, terwijl de live evaluator in de gemeten eerste
voorbeeldparen 24 keer onderscheidde, 19 keer dezelfde score gaf en één keer
omgekeerd scoorde. Dit bewijst drift tussen voorbeelden en evaluatorsemantiek.
Het bewijst niet dat iedere betrokken regel universeel inert is: de gerichte
runtime-matrix bereikt voor meerdere van die regels met andere fixtures wel een
failure. Beide soorten tests zijn daarom nodig.

Voor CON-01 geldt de volgende productnorm:

- iedere definitie heeft minimaal één gestructureerde contextwaarde;
- context wordt opgeslagen als `organisatorische_context`,
  `juridische_context` en/of `wettelijke_basis`;
- de contextnaam of het contextlabel mag geen onderdeel zijn van de
  definitietekst;
- dezelfde term mag per verschillende context een eigen definitie hebben;
- term plus genormaliseerde context bepaalt duplicaatidentiteit.

## Beslissing

`config/toetsregels/toetsregels_config.yaml` blijft de gezaghebbende root-SSOT
voor het validatiesysteem. Deze configuratie registreert uitsluitend het actieve
JSON-formaat, de verplichte contractvelden, laad- en foutbeleid, categorieën en
scoringpolicy. De 53 JSON-bestanden zijn de versioned uitvoerbare regelrecords
die door deze rootconfig worden aangewezen. Bij afwijking tussen rootconfig,
record en runtime faalt het laden zichtbaar; geen van deze lagen mag stil een
tweede waarheid introduceren.

Ieder JSON-regelrecord wijst naar precies één evaluatorstrategie en declareert
welke invoer die strategie vereist. Eenvoudige declaratieve regels gebruiken een
generieke evaluator; semantische, taalkundige, context- of repositoryafhankelijke
regels gebruiken kleine gespecialiseerde evaluators achter één register.

Ieder regelrecord declareert daarnaast zijn uitvoerbaarheidsklasse,
automatiseringsstatus en scorepolicy. Het resultaatmodel onderscheidt minimaal
`pass`, `fail`, `review_required`, `not_evaluated` en `error`. Alleen een werkelijk
uitgevoerde betrouwbare beoordeling mag als pass meetellen. Niet-uitgevoerde of
reviewplichtige regels krijgen dus nooit stil score 1,0; score en
evaluatiedekking worden afzonderlijk gerapporteerd.

Voor oordeelafhankelijke regels wordt per regel expliciet gekozen voor een
gecontroleerde AI-jury of menselijke review. Een AI-jury wordt niet als generieke
fallback ingevoerd zonder afzonderlijk besluit over prompt/modelversie,
goldset, privacy, kosten en foutbeleid.

De bestaande dubbele Pythonvalidatorlagen worden niet aangesloten. Bruikbare
logica wordt eerst semantisch beoordeeld en zo nodig geport naar de nieuwe
evaluatorstrategieën. De lagen worden pas daarna, met expliciete toestemming van
Chris, verwijderd.

De Pythonformatconfiguratie, `require_both_formats` en Python-consistencychecks
worden pas in de implementatiefase omgezet naar het gekozen JSON-only
runtimecontract. De oude bestanden blijven tot de afzonderlijk goedgekeurde
verwijderingsfase fysiek aanwezig, maar zijn geen bron voor runtimegedrag.

ASTRA is de externe normbron voor de overgenomen regels. De rootconfig en
regelrecords leggen bronregel, peildatum/status en eventuele lokale afwijking
expliciet vast. Projecttoevoegingen blijven herkenbaar als projectregels.
Bronwijzigingen worden via een reproduceerbare offline driftcontrole gesignaleerd
en nooit automatisch in productieconfiguratie overgenomen.

## Opties

### Optie A — Oude Pythonvalidatorlaag alsnog aansluiten

- **Voordelen:** bestaande classes en loader kunnen deels worden hergebruikt.
- **Nadelen:** activeert 12.893 regels gedupliceerde code; minimaal acht
  validators hebben een ander regeldoel; de laag mist zeven baseline-regels;
  onderhoud en drift blijven per regel verdubbeld.
- **Beoordeling:** hoge migratie- en onderhoudslast, lage betrouwbaarheid.

### Optie B — Alle regels in `_evaluate_json_rule` houden

- **Voordelen:** minimale structurele wijziging; huidig productiepad blijft
  intact.
- **Nadelen:** vergroot het bestaande god-object; repository- en contextregels
  blijven impliciet; vereiste invoer en evaluatorbereikbaarheid zijn niet als
  contract afdwingbaar.
- **Beoordeling:** lage korte-termijnkosten, hoge structurele onderhoudslast.

### Optie C — JSON-rulecontract plus evaluatorstrategieën

- **Voordelen:** één normatieve regelbron; expliciete invoercontracten;
  eenvoudige regels blijven declaratief; complexe logica is afzonderlijk
  testbaar; oude duplicatie kan verdwijnen.
- **Nadelen:** vraagt een contractmigratie voor 53 records en gerichte
  evaluators voor de semantisch complexe regels; repositoryregels kunnen meer
  rekentijd vragen.
- **Beoordeling:** middelgrote migratielast, laagste blijvende onderhoudslast.

## Trade-offs

Optie C wordt gekozen. Zij kost meer dan het laten staan van de huidige switch,
maar voorkomt zowel een heropleving van dode code als verdere groei van het
god-object. Niet iedere ASTRA-regel wordt automatisch toetsbaar verklaard: als
een betrouwbare automatische evaluator ontbreekt, moet het regelrecord dit
expliciet aangeven en een zichtbare reviewpolicy hebben.

De productnorm voor CON-01 wijkt in vorm af van de letterlijke ASTRA-presentatie:
context wordt niet in de definitietekst vermeld, maar als gestructureerde data
aan het definitierecord gekoppeld. Die lokale norm is leidend.

## Consequenties

Makkelijker:

- contracttests kunnen ontbrekende of dubbele evaluators bij CI/startup afvangen;
- iedere regel krijgt expliciete vereiste invoer en een aantoonbaar runtimepad;
- score en evaluatiedekking kunnen niet meer door default-pass worden vermengd;
- DEF-424 kan evaluators uit `ModularValidationService` halen zonder legacycode
  opnieuw te activeren;
- tests kunnen normatief gedrag toetsen in plaats van alleen bereikbaarheid.

Moeilijker:

- SAM-02 tot en met SAM-05 vereisen begrips- of repositorycontext;
- SAM-01, SAM-08 en DUP-01 vereisen eveneens repository-/relatiegegevens;
- VER-01 tot en met VER-03 vragen betere Nederlandse woordvormheuristiek;
- oordeelregels vragen een expliciet AI- of menselijk reviewcontract;
- ontbrekende context moet fail-closed worden behandeld;
- verwijdering is geblokkeerd tot semantische pariteit aantoonbaar is.

## Acties

1. Werk DEF-606 bij als overkoepelend besluit- en consolidatie-issue.
2. Voeg een child issue toe voor het contextcontract en CON-01.
3. Voeg een child issue toe voor semantische pariteit van VER-01–03 en
   SAM-02–06.
4. Classificeer via DEF-624 alle 53 regels en herstel uitkomst-/scorebeleid.
5. Leg via DEF-625 ASTRA-herkomst, bronstatus en lokale afwijkingen vast.
6. Breid DEF-503 uit van reachability naar semantische gedragstests.
7. Laat DEF-621 de reeds bewezen runtime-defecten herstellen.
8. Voer DEF-424 pas uit nadat het regelcontract en gedrag stabiel zijn.
9. Sluit DEF-464 via de uiteindelijke, expliciet goedgekeurde verwijdering.

## Verwijderingsgate

De twee Pythonlagen mogen pas worden verwijderd wanneer:

- alle 53 JSON-regels schema-valid zijn;
- de root-SSOT uitsluitend JSON als actief runtimeformaat aanwijst;
- iedere regel precies één bekende evaluatorstrategie heeft;
- iedere regel een goedgekeurde uitvoerbaarheidsklasse en scorepolicy heeft;
- vereiste invoer niet stil kan ontbreken;
- positieve, negatieve en grensgevallen per automatisch getoetste regel slagen;
- de 44 aanwezige JSON goed/fout-paren als contractcases zijn beoordeeld;
- `review_required`, `not_evaluated` en `error` niet als pass meetellen;
- score en evaluatiedekking afzonderlijk zichtbaar zijn;
- repository- en contextregels end-to-end zijn getest;
- productiecode nul imports naar de oude loader/lagen bevat;
- Chris expliciet toestemming geeft voor de bestandsverwijdering.

## Bronnen

- `docs/planning/V2_VALIDATOR_VOLLEDIG_IMPLEMENTATIEPLAN.md`
- `src/services/validation/modular_validation_service.py`
- `src/services/orchestrators/validation_orchestrator_v2.py`
- `src/toetsregels/regels/*.json`
- `tests/fixtures/toetsregels/runtime_cases.yaml`
- ASTRA-regelpagina's voor VER-01–03, SAM-02–06 en CON-01
