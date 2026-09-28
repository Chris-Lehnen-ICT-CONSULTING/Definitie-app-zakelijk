**WP5a is nog niet akkoord:** twee bevestigde contractproblemen en één open testpoortprobleem. Review uitgevoerd als toegewezen Codex CLI-reviewer, zonder herdelegatie of wijzigingen aan bronbestanden/tests.

Beoordeelde identiteit, vóór en na verificatie gecontroleerd:

- Basis: `979ca0585100d94b613829d924c6d8bba4f24f1b`.
- Manifest: `bewijs/wp5a-reviewmanifest-v1.json`, SHA256 `4d1e9b2b3f112a542815c363192907e7a28d430a8d452b00220dfe3fc5ac644c`.
- Zeven bestandshashes: **7/7 gelijk** aan manifest én de `before`/`after`-hashes van `wp5a-coordinator-v1.json`.
- Volledige zevenbestandenpatch gereconstrueerd, inclusief ongetrackte tests: SHA256 `aeaa6dce27700c0b19eaf771a899e7a1362d176a05fc2f418746307f82a57e48`, exact gelijk aan de aangeleverde patch.
- Geen verwijderde bestanden, stage-, commit-, push-, merge- of Actions-handelingen.

1. **F1 — Important; dispositievoorstel: fix nu. Het bestaande NE-pad omzeilt het O2-contract.**

   Locatie: [modular_validation_service.py:1483](/private/tmp/def835-wp2-review-20260927/src/services/validation/modular_validation_service.py:1483). De voorafgaande invoercontrole retourneert voor INT-02 de oude DEF-771-uitkomst, voordat `decision_rule_assessment` draait. Zij gebruikt `ctx.cleaned_text`.

   De zelfstandige [offline repro](/private/tmp/wp5a-codex-repro-20260928-v1.py) bevestigt:

   - Gevulde oorspronkelijke kern, ontbrekende context, cleaning naar `""`: melding **“kern en context ontbreekt”**, terwijl alleen context ontbreekt.
   - Lege oorspronkelijke kern, ontbrekende context, cleaning naar gevulde tekst: melding **“context ontbreekt”**, terwijl beide ontbreken.
   - Zonder cleaning blijft de documentvorm afwijkend: `contract_version="def771-int02/2"`, `review=null`, geen `assessment`, onderdeel `invoer`.
   - Een aanwezige ongeldige recordkern `None` met ontbrekende context wordt **NE in plaats van error**. Hetzelfde gebeurt met een ongeldige `int02_bedoeling=42`.

   Alle gevallen maken nul dienstaanroepen. De tekortkoming betreft dus de melding, foutclassificatie en resultaatvorm. Het actuele publieke contract beschrijft voor O2 juist `def835-int02-assessment/1`, onderdeel `beoordeling`, `review.actuality` en de evaluatorvelden; ongeldige metadata moet `error` geven. Zie [resultaatcontract:45](/private/tmp/def835-wp2-review-20260927/docs/architectuur/contracts/validation_result_contract.md:45).

   **Minimale correctie:** laat uitsluitend de O2-evaluator zijn eigen WP1-invoercontrole en NE-uitkomst verzorgen. Behoud het O1-pad. Voeg gerichte regressies toe voor bovenstaande combinaties. Dit hoort bij de geaccordeerde modular-integratie; het is geen vrijblijvende uitbreiding buiten WP5a.

2. **F2 — Important; dispositievoorstel: fix nu. De configuratiebinding wordt tegen zichzelf gecontroleerd.**

   Locatie: [validation_orchestrator_v2.py:737](/private/tmp/def835-wp2-review-20260927/src/services/orchestrators/validation_orchestrator_v2.py:737), vooral regel 740.

   De wrapper vergelijkt de ontvangen invoer met zijn verse invoer, maar haalt de verwachte configuratie vervolgens uit `document.binding.configuratie()`. Daardoor kan de evaluator geen afwijking ontdekken tussen de documentconfiguratie en de werkelijk bedoelde actuele configuratie.

   De repro gebruikt een expliciet geïnjecteerde dienst met profiel `fake-new-model`, waarvan de `assess`-grens bewust een eerder coherent document voor `fake-int02-model` teruggeeft:

   - Rechtstreekse WP1-controle tegen de actuele dienstconfiguratie: `review_required/historical`.
   - Via wrapper en echte ModularValidationService: **`pass/current`**, met het oude model in het document.
   - Geen echte modelcalls; de nieuwe FakeAI wordt niet aangeroepen.

   Dit bewijst de ontbrekende bindingscontrole op de integratiegrens. Het bewijst **geen bestaande cachefout in WP2**; het is gerichte foutinjectie, vergelijkbaar met de bestaande test voor verkeerde invoerbinding.

   **Minimale correctie:** verkrijg een onafhankelijke, voor de aanroep vastgelegde configuratie en controleer de volledige binding. Een afwijkend document uit een verse dienstaanroep moet volgens deze opdracht `error` opleveren. Een publieke configuratie-interface kan daarvoor passend zijn, maar moet een consistente snapshot leveren. Als daarvoor het WP2-bestand moet worden uitgebreid, moet de coördinator die minimale scope-uitbreiding organiseren. Private attributen uitlezen of het retourdocument als verwachting gebruiken sluit dit punt niet.

3. **F3 — Important voor de testpoort; dispositievoorstel: fix nu binnen het afzonderlijke testmandaat.**

   Locatie: [test_def835_int02_assessment_service.py:305](/private/tmp/def835-wp2-review-20260927/tests/unit/validation/test_def835_int02_assessment_service.py:305), veroorzaakt door de geaccordeerde [containerfactory:356](/private/tmp/def835-wp2-review-20260927/src/services/container.py:356).

   Vers gereproduceerd: `assert "int02_assessment" not in container` faalt. De test verbiedt iedere vermelding, terwijl het akkoord expliciete constructie met verplicht profiel en budget toestaat.

   Dit is **geen bewijs dat de factory onbedoeld activeert**: de nieuwe gedragstests bevestigen juist geen automatische constructie/injectie. De testpoort blijft echter rood.

   **Minimale correctie:** herijk de bestaande test naar die gedragsintentie, zonder het testgeval te verwijderen of de guard door hernoeming te ontwijken. Het achtste bestand is al voorgelegd; ik heb het niet gewijzigd en vraag geen hernieuwd akkoord.

De acht uitvoerderspunten zijn als volgt geclassificeerd:

| Punt | Beoordeling en dispositie |
|---|---|
| 1. WP2-tekstguard | Bevestigd testpoortprobleem, F3. Factory behouden; guard gericht herijken binnen het afzonderlijke mandaat. |
| 2. NE vóór evaluator | Bevestigde contractfout, F1. Valt binnen de integratieverplichtingen van WP5a. |
| 3. Configuratie uit documentbinding | Bevestigde ontbrekende controle, F2. Geen uitsluitend theoretische opmerking of opslagvraag. |
| 4. Bedoeling/bronnen uit metadata | Geen bevestigde WP5a-fout: deze invoerkanalen staan in het O2-contract en worden gebonden. Dit bewijst geen duurzame recordherkomst; die blijft bij DEF-626/opslag. |
| 5. `error` blokkeert acceptatie | Bestaande generieke DEF-624-werking via `evaluation_error`; geen aangetoonde nieuwe INT-02-`fail`-poort. Binnen deze review geen correctie voorgesteld. De bredere poortbeslissing blijft afzonderlijk; hiermee wordt die niet gesloten. |
| 6. Dertien mypy-fouten | Behouden bewijs vermeldt dezelfde fouten op HEAD in WP1/WP2. Geen nieuwe WP5a-bevinding; mypy blijft rood en wordt niet als geslaagd gerapporteerd. |
| 7. Grotere omvang | Zeven bestanden, 1.363 toevoegingen en één verwijderde regel, vooral tests. De raming was geen harde limiet in het mandaat; geen inhoudelijke scope-uitbreiding vastgesteld. |
| 8. Opslag/UI/C118/activering | Expliciet buiten dit pakket. Terecht onbewezen gelaten; geen WP5a-bevinding en geen bewijs dat heel O2 af is. |

De uitgevoerde verificatie:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 \
/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python \
/private/tmp/wp5a-codex-repro-20260928-v1.py
```

Resultaat: exit 0; vijf NE-/invoerscenario’s en de configuratierepro bevestigen de beschreven afwijkingen. Script-SHA256: `e349338bff6841159970546dac27e99f5d3132e2e6a87663cf9ed9d843ebb783`.

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 \
/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest \
-q -p no:cacheprovider -p no:randomly -o addopts='' \
tests/unit/services/orchestrators/test_def835_int02_wrappers.py \
tests/unit/validation/test_def835_int02_modular.py \
tests/unit/services/test_def835_int02_container.py \
tests/unit/validation/test_def835_int02_assessment_service.py::test_dienst_wordt_niet_door_de_container_aangemaakt
```

Resultaat: **exit 1 — 49 passed, 1 failed**, uitsluitend F3.

Daarnaast heb ik het behouden bewijs gecontroleerd:

- RED-loghashes kloppen; de definitieve RED-productiehashes horen bij de basis en de testhashes bij deze snapshot. **44 failed, 5 passed**, exit 1. Het rood bevat werkelijk gedrag: ontbrekende `rule_results`, een categoriescorelek en afzonderlijk aangetoonde caller-pass. Constructorfouten vormen wel een aanzienlijk deel.
- GREEN: **49 passed**, exit 0.
- Gerichte bestaande regressie: **2.898 passed, 11 skipped, 1 failed**, exit 1; alleen F3 faalt. De commandolijst omvat de bestaande INT-03-, ESS-03-, bron-, orchestrator-, container- en modular-routes.
- Coördinatorbewijs voor Ruff en Black: exit 0, met exact passende bestandshashes.
- De twee `performance_tracker`-fouten en dertien mypy-fouten zijn volgens het behouden HEAD-vergelijkingsbewijs bestaand. Geen volledige suite of mypy-matrix herhaald.

O1-afscherming, expliciete DI, bescherming tegen caller-assessments, bytegelijke kern bij geldige invoer, adviserende fail zonder scoreverschil en C117-afwijzing zijn binnen de geteste routes onderbouwd. C105/C107/C112 blijven mappingtests met handmatige responsen. De eerdere liveproef kwalificeert het model niet; deze review verandert dat niet.