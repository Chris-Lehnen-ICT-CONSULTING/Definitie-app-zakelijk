# DEF-835 — WP5a: verslag Claude Code CLI-uitvoerder (v1)

28 september 2026. Uitvoerder: Claude Code CLI, deze sessie. Opdracht: `wp5a-opdracht-claude-v1.md`, besluit `besluit-proef-en-wp5a-v1.md`. Basis `979ca0585100d94b613829d924c6d8bba4f24f1b` op `feature/DEF-835-int02-o2`. **Niets gestaged, gecommit of gepusht.** Geen agents, reviewers of extra CLI-sessies gestart. Geen model- of providercalls, database, UI, opslag of activering.

## Uitkomst

Een expliciet geïnjecteerde O2-dienst brengt het WP1-document nu via de generatie- en de recordroute onveranderd in `rule_results['INT-02']`. Dat gebeurt uitsluitend als de actieve, gevalideerde regelset INT-02 op `decision_rule_assessment` zet. De actieve regelset blijft O1 (`judgment_review`) en doet nul INT-02-aanroepen. De drie nieuwe testbestanden zijn groen (49/49). Er faalt **één bestaande test**: een WP2-tekstguard die precies de geaccordeerde containerfactory verbiedt (open punt 1). Die test valt buiten mijn eigenaarschap; ik heb hem niet aangepast en niet omzeild.

## Wijzigingen (zeven bestanden, werkboom, niet gestaged)

| Bestand | Regels | SHA-256 |
| --- | --- | --- |
| `src/services/container.py` | +30 | `32a5ae789a0f131a036e4f1aa66d98cd05e4ea99ca1e77545529592de781e42a` |
| `src/services/orchestrators/definition_orchestrator_v2.py` | +6 | `db1093e54c6c917fb6b37f49b153cdd1f2465274da94fb1bb74bfe1ef724d4ca` |
| `src/services/orchestrators/validation_orchestrator_v2.py` | +126 | `7faf7380ca1d4a332d0110ddfac53ced9c094223ef533199a87c6229f125f419` |
| `src/services/validation/modular_validation_service.py` | +19 / −1 | `737b86326580d58e0ee86554f2cf42db20c3ac0cf390a237055deb9e7afb9829` |
| nieuw `tests/unit/services/orchestrators/test_def835_int02_wrappers.py` | 670 | `c75f36bd6f6093b15c4753339c8fe25a858a8a21cbc1dfc8ac72747c686e886b` |
| nieuw `tests/unit/validation/test_def835_int02_modular.py` | 333 | `f8e83149f8bebe82fd3f1238b7da1496eebb9396a3b4ea4b902c1450d55b1810` |
| nieuw `tests/unit/services/test_def835_int02_container.py` | 179 | `5048a1c4bf68fe58d8315a85129269e3eff27737e0b833b6bef177e2c3f69ae9` |

Totaal: productie +181/−1, tests 1.182 regels, samen ongeveer 1.363. Dat ligt **boven de raming van 400–650 regels** uit het voorstel. Het verschil zit vrijwel geheel in de tests: elke verplichte case is een eigen, deels geparametriseerde test over beide routes. Geen nieuwe dependency, schemawijziging of resultaatcontractversie (blijft 2.3.0).

### Ontwerp in het kort

- **ModularValidationService.** `DECISION_RULE_ASSESSMENT` staat nu in `_EVALUATORS_MET_DEELUITKOMST`. Daarnaast is er een nieuwe publieke leesfunctie `evaluator_voor(code)`. Die leest het gevalideerde regelrecord uit dezelfde, zo nodig ververste snapshot als de evaluatie. Als de regelset niet gereed is, geeft zij `None`.
- **ValidationOrchestratorV2.** Er is een optionele `int02_assessment_service` bijgekomen (default `None`). `_beoordeel_int02` draait in beide routes na INT-03 en doet het volgende:
  1. Het gooit altijd weg wat de aanroeper meegeeft onder `int02_document`, `int02_configuratie` en `int02_assessment`.
  2. Het stopt zonder aanroep als er geen dienst is of als `evaluator_voor("INT-02")` niet O2 is.
  3. Het bouwt de WP1-invoer met `maak_invoer` uit exact `record_text` en de context, dezelfde lezing als de evaluator.
  4. Bij ongeldige invoer volgt een technische fout, bij een lege kern of ontbrekende context NE. In beide gevallen wordt de dienst niet aangeroepen.
  5. Het roept de dienst precies één keer aan.
  6. Het document wordt alleen geaccepteerd als het een `Beoordelingsdocument` is waarvan `invoer` gelijk is aan de verse invoer. In elk ander geval volgt een technische fout.
  7. Bij een technische fout zet het een bewuste niet-`Configuratie` als markering. Daarvan maakt de WP3-evaluator `error`, zonder oordeel.
  8. Er wordt alleen een foutsoort of uitzonderingstype gelogd.
- **DefinitionOrchestratorV2.** Er is een optionele `int02_assessment_service` bijgekomen als gewoon attribuut. Er is bewust geen lazy property en geen default; de dienst wordt doorgegeven aan de lazy gebouwde validatiewrapper.
- **ServiceContainer.** De nieuwe factory `int02_assessment_service(*, profiel, budget)` accepteert alleen keyword-only argumenten zonder default. Iets anders dan een `Modelprofiel` of `Budget` geeft `Int02ServiceConfigError`. De factory is geen singleton, registreert niets en is niet bedraad in `orchestrator()`.

## Acceptatiepunten

| Punt | Bewezen door (test) | Beperking |
| --- | --- | --- |
| O1 doet nul INT-02-calls, ook met een losse dienst of een los assessment in de metadata | `test_o1_regelset_doet_nul_int02_aanroepen[tekst,record]`: actieve regelset, geïnjecteerde dienst plus `int02_document`, `int02_configuratie`, `int02_assessment` en `int02_assessment_service` in de metadata → beide fakes 0 calls; INT-02 geen pass, geen assessment. `test_normale_orchestrator_blijft_o1_zonder_int02_dienst` en `test_actieve_ssot_houdt_int02_op_o1` | — |
| Alleen een expliciete O2-configuratie maakt de route bereikbaar; de echte SSOT wordt gelezen | `test_evaluator_voor_leest_actieve_o1_en_expliciete_o2_regelset`, `test_evaluator_voor_zonder_geldige_regelset_is_none`. De O2-regelset is een tijdelijke kopie van alle 53 regelbestanden waarin alleen het INT-02-runtimecontract is gewijzigd | Het actieve `INT-02.json` is niet gewijzigd |
| Kern bytegelijk, zonder cleaning | `test_kern_is_bytegelijk_de_getoetste_tekst_zonder_cleaning`: kern met voorloop- en naloopspatie, NBSP en dubbele spatie; een agressieve cleaningservice in de modulaire service; een afwijkende aanroeper-`record_text` → de dienst ontvangt exact de tekst, en het assessment in `rule_results` bevat die tekst | — |
| Recordkern gezaghebbend; een aanwezige ongeldige recordkern is een fout, geen terugval | `test_recordkern_is_gezaghebbend`, `test_ongeldige_recordkern_is_fout_zonder_terugval` (`None` → INT-02 `error`, 0 calls), `test_recordkern_van_verkeerd_type_bereikt_de_dienst_niet` (`42` → de bestaande modulaire service degradeert zelf, 0 calls) | Bij `42` komt de fout uit de bestaande service (`len(int)`), niet uit INT-02 |
| Onbetrouwbaar meegegeven assessment weg; geen caller-pass | **Tussen-RED**: met alleen de modular-wijziging gaf een meegegeven, aan exact deze invoer gebonden document **pass** (`wp5a-rood-na-modular-v1.log`). Na de wijziging: `test_meegegeven_document_zonder_dienst_geeft_nooit_een_oordeel` → `review_required/not_assessed`. `test_verse_beoordeling_vervangt_meegegeven_document` → vers fail-document, 1 call | — |
| Lege kern of ontbrekende context → NE zonder call | `test_lege_kern_of_ontbrekende_context_is_ne_zonder_aanroep` (lege kern, label zonder kern, geen context); modular: `test_ontbrekende_kern_of_context_is_ne_zonder_oordeel` | Zie open punt 2 (NE-pad bij ontbrekende context) |
| Ontbrekende dienst of ontbrekend profiel → expliciet open | `test_meegegeven_document_zonder_dienst…`, `test_ontbrekend_profiel_blijft_expliciet_open_zonder_modelaanroep` (echte WP2-dienst, `profiel=None`, FakeAI 0 calls); modular: `test_zonder_document_blijft_int02_expliciet_open` | — |
| Fout in binding, dienst of vorm → error, nooit pass/fail | `test_dienst_vorm_en_bindingsfout_zijn_error` × {uitzondering, dict in plaats van document, document `None`, document voor andere invoer} × {tekst, record}: status `error`, `MELDING_E`, assessment `None`, precies 1 call | — |
| Pass, adviserende fail, review_required, not_evaluated, not_applicable en error via de echte ModularValidationService in `rule_results` | `test_elke_o2_status_landt_in_rule_results` (C112 pass, C105 fail, C107 review, NA, C117 error): exacte WP1-melding, `score` `None`, en het `assessment` is gelijk aan `document.als_dict()` voor aanvaarde documenten. Verder de NE-test, `test_not_applicable_komt_via_de_wrapper_in_rule_results` en `test_adviserende_fail_is_een_zichtbare_violation_zonder_poort` (warning, `advisory: True`) | — |
| Geen cijfer en geen poort; `excluded_from_score` | `test_int02_geeft_geen_cijfer_en_geen_poort`: zelfde kern, pass/fail/review/NA → `overall_score`, `detailed_scores`, `is_acceptable` en `acceptance_gate` zijn identiek. RED vóór de wijziging: de categoriescore `structuur` ging van 0,97 naar 0,87 bij fail | Een INT-02-`error` blokkeert wel de acceptatie via de generieke DEF-624-regel (open punt 5) |
| Geen raw exception, payload of secret in nieuwe logs | Foutentest met `caplog` op DEBUG: de synthetische uitzonderingstekst staat niet in de log en niet in het resultaat. In de code worden alleen de foutsoort en `type(exc).__name__` gelogd | Getoetst op de nieuwe paden; bestaande logregels van andere wrappers zijn niet herzien |
| Geen herstelcall; geen modelcall bij herladen | `test_ontwerpgevallen_via_echte_dienst_en_modulaire_service`: precies 1 FakeAI-call per toetsing. Bij opnieuw toetsen met dezelfde invoer komt een aanvaard oordeel uit de dienstcache (nog steeds 1 call). De modulaire service zelf kent geen dienst | Herladen/opslag (C118) valt buiten dit pakket en is **niet** bewezen. Een fout (C117) wordt door het WP2-ontwerp niet gecachet, dus een nieuwe toetsing roept opnieuw aan. Dat is geen herstel binnen één toetsing |
| C105/C107/C112 via handmatige fake-respons; C117 ongeldig citaat blijft error | Dezelfde test met de echte `Int02AssessmentService`, FakeRouter, een expliciet testprofiel en -budget en de fixture-modelrespons: status gelijk aan het `verwacht` uit de fixture. Voor C117 `foutcategorie` `invalid_citation` en assessment `None` | Bewijst alleen de ketenmapping, **geen modelkwaliteit**. De echte proef (C107 afwijkend, C112 ongeldig citaat) staat ongewijzigd in `modelproef-live-verslag-v1.md`. Prompts, norm en fixturelabels zijn niet aangeraakt |
| Generatieroute | `test_generatieroute_toetst_exact_de_kandidaat` (`DefinitionOrchestratorV2._toets_kandidaat`), `test_definitie_orchestrator_geeft_int02_dienst_door_zonder_default` | Via `_toets_kandidaat` met een geïnjecteerde wrapper, niet via een volledige `create_definition` |
| Container alleen op expliciet verzoek, profiel en budget verplicht | `test_factory_vereist_expliciet_profiel_en_budget_zonder_default`, `test_factory_bouwt_op_expliciet_verzoek_zonder_modelaanroep`, `test_expliciet_gebouwde_dienst_bereikt_de_validatiewrapper` | — |
| Geen profiel of budget van andere regels overgenomen | Geen defaults in de factory; `test_wp2_dienst_kent_geen_default_profiel_of_budget` | Bewijst niet dat een aanroeper geen ander profiel meegeeft; dat is diens expliciete keuze |
| INT-03-, ESS-03- en bronbeoordelingswrappers ongewijzigd | Gerichte regressie over alle `tests/unit/services/orchestrators` (DEF-743/766/772/622/747/751) en de containertests: groen | — |

## TDD-bewijs (dossier `bewijs/`)

| Log | Wat | Uitkomst | SHA-256 |
| --- | --- | --- | --- |
| `wp5a-rood-v1.log` | **Mislukte aanroep** (zsh splitste de testlijst niet; er is niets gedraaid) | exit 4, geen tests. Blijft staan volgens de file-protection-regel; ongeldig als bewijs | `6244086362bcaddcfa051cafffbe5413549d332982ec8ba4f0e058e86c0d5fe3` |
| `wp5a-rood-v2.log` | Eerste testversie tegen ongewijzigde productiecode (`git diff --quiet` exit 0) | 44 failed, 5 passed, exit 1 | `a074151bee533f73f2f5bfa256f38781df1e8c43d9348614c46bcf2ae7199179` |
| `wp5a-rood-na-modular-v1.log` | Alleen de modular-wijziging: bewijs van de caller-pass | 2 failed (`'pass' == 'review_required'`), 14 passed, exit 1 | `d9ce579afeafa545f1a5334e82377a5905f4f9a48fa19b782b20b029e7b06d34` |
| `wp5a-rood-eindtests-v1.log` | **Definitieve** testversies (na black en na het splitsen van de recordkerntest) tegen een volledige `git archive HEAD`-export in `/tmp/wp5a-head-src`; werkboom en index niet aangeraakt | 44 failed, 5 passed, exit 1 | `c68e419e05bcbe822ab714f0a0a806d220d449e3d4ee32186dcb27cc709ae0d7` |
| `wp5a-groen-nieuwe-tests-v1.log` | De drie nieuwe bestanden op de eindstand | **49 passed, exit 0** | `e44bd9c38572514a461333c429b18aadf9e396591706604f2c8f494bacd30ff0` |
| `wp5a-groen-v1.log` | Nieuwe tests plus gerichte regressie (orchestrators, `tests/unit/validation`, containers, modular, INT-01/03/ESS-03-ketens, DEF-771-view) | 2.898 passed, 11 skipped, **1 failed** (open punt 1), exit 1 | `97502d0fb922b5a889b5db464128928319302900152373055d3e2d8187f2f91f` |
| `wp5a-unit-suite-v1.log` | Volledige unit-suite (`-m unit -n auto`), samenvatting | 8.554 passed, 86 skipped, 1 xfailed, **3 failed**: open punt 1, plus 2× `test_performance_tracker` (OfflineGateError op `data/definities.db`, identiek op de `HEAD`-export → reeds bestaand) | `d6da3f672f51e3515d14bdb620630a7edbd50b0d7fa54f663315f926713c2bdb` |
| `wp5a-lint-v1.log` | black 26.5.1, ruff 0.15.17 (venv), ruff 0.16.5 (pre-commit-rev), mypy | black, ruff en ruff exit 0. mypy: 13 fouten in 2 bestanden, **identiek op HEAD** (`contract.py`, `int02_assessment_service.py`); 0 in mijn vier bestanden | `2a97e39d8f7809ad9da5ea46ef7f245d6c6950cfb19410e922fba1bf69311e95` |

Eerlijke beperkingen van de RED:

- 27 van de 44 RED-failures zijn de `TypeError` op de nieuwe constructorparameter (26 bij `ValidationOrchestratorV2`, 1 bij `DefinitionOrchestratorV2`). Dat is niet het enige RED:
  - 8 zijn `KeyError: 'INT-02'` doordat `rule_results` de O2-statussen niet boekt.
  - 1 is het cijferlek (0,97 → 0,87).
  - 3 zijn een ontbrekende `evaluator_voor`.
  - 1 is `_EVALUATORS_MET_DEELUITKOMST`.
  - 4 komen van de ontbrekende factory.
  - De caller-pass is apart aangetoond in de tussen-RED.
- 5 tests waren al groen vóór de wijziging. Dat zijn guards: de adviserende violation, de drie NE-varianten in modular en de check op de WP2-module zonder default.
- Na de eerste GREEN-run heb ik de recordkerntest in twee strikte tests gesplitst en black toegepast. Daarom is RED opnieuw gedraaid met de eindversies (`wp5a-rood-eindtests-v1.log`).
- De randomisatie-plugin is uitgezet met `-p no:randomly` voor reproduceerbaarheid.

## Reviewdiff-identiteit

- Base: `979ca0585100d94b613829d924c6d8bba4f24f1b`; ongestagede werkboomdiff van precies de zeven bestanden hierboven.
- Patch: `bewijs/wp5a-werkboomdiff-v1.patch` (1.514 regels, 7 bestanden), SHA-256 `aeaa6dce27700c0b19eaf771a899e7a1362d176a05fc2f418746307f82a57e48`. Reproductie: `git diff --no-color HEAD -- <4 bronbestanden>` gevolgd door `git diff --no-color --no-index /dev/null <nieuw bestand>` per testbestand.
- De hashes in `wp5a-groen-v1.log` en `wp5a-rood-eindtests-v1.log` zijn met `shasum -c` tegen de huidige bestanden gecontroleerd: OK.

## Git-staat

De index is exact intact. Het zijn dezelfde 38 dossierbestanden, met een namenlijst identiek aan die bij de start. De hash van `git diff --cached` is `941070627b508626b13b3c4d13b00bf5000966a8f728d0425802ed7b9fd5d214`, gelijk aan de sessiestart. Er is niets gestaged, ge-unstaged, gecommit of gepusht; de allowlist is niet gewijzigd en er is geen bypass gebruikt. Nieuwe bestanden van mij staan alleen onder `bewijs/wp5a-*` (acht stuks, zie hierboven) en in dit verslag. De bestaande `wp5a-claude-stream-v1.jsonl`, `wp5a-index-behoud-v1.json` en `wp5a-opdracht-codex-review-v1.md` zijn niet aangeraakt. Buiten de repository staan de hulpartefacten `/tmp/wp5a-head-src` en `/tmp/wp5a_probe.py`; die zijn niet opgeruimd, want verwijderen valt buiten het mandaat.

## Open punten

1. **Besluit nodig: bestaande WP2-guard is in strijd met het geaccordeerde voorstel.** `tests/unit/validation/test_def835_int02_assessment_service.py:305-308` (`test_dienst_wordt_niet_door_de_container_aangemaakt`) eist dat `container.py` de teksten `int02_assessment` en `Int02AssessmentService` niet bevat. De geaccordeerde factory maakt die test rood. Het bestand valt buiten mijn eigenaarschap en testgevallen mogen niet verdwijnen. Een hernoeming om de guard te ontlopen zou het doel van de guard misleiden; die heb ik niet gedaan.
   - Minimaal voorstel: herijk de test naar de gedragsintentie (vergelijkbaar met de WP3-testherijking). De container bouwt de dienst niet vanzelf: `orchestrator()` injecteert niets en de factory heeft geen default voor profiel en budget. Dat is inhoudelijk al gedekt in `test_def835_int02_container.py`.
   - Dit vraagt een apart mandaat voor dat ene bestand.
2. **NE bij ontbrekende context loopt via het bestaande DEF-771-pad** (`modular_validation_service.py:1465-1473`), vóór de O2-evaluator. De status en de exacte melding kloppen, maar er zijn drie afwijkingen:
   - `contract_version` is de record-contractversie (`def771-int02/2`) in plaats van `def835-int02-assessment/1`.
   - `review` is `None` en het veld `assessment` ontbreekt.
   - De kerncontrole in dat pad gebruikt `cleaned_text`. Met een cleaningservice kan de melding "kern en context" dus afwijken van de `record_text` die O2 beoordeelt.

   Een lege kern mét context loopt wél via de O2-evaluator. Ik heb dit niet gewijzigd omdat het buiten de minimale scope valt. Voorstel: bij `DECISION_RULE_ASSESSMENT` de NE aan de evaluator laten.
3. **De configuratie komt uit de binding van het zojuist verkregen document** (`document.binding.configuratie()`).
   - Wat wel onafhankelijk getoetst wordt: de invoerbinding. De wrapper vergelijkt `document.invoer` met de verse invoer, en de evaluator herberekent de binding uit verse metadata.
   - Wat niet onafhankelijk getoetst wordt: de configuratiehelft (norm-, prompt- en routeringshash, provider/model). Die volgt uit de dienst zelf.
   - WP2 heeft daarvoor geen publieke interface; `_configuratie` en `_route` zijn privé.
   - Minimaal voorstel (buiten mandaat, WP2-bestand): een publieke methode `Int02AssessmentService.configuratie()`, die de wrapper naast het document aan de evaluator geeft.
4. **Bedoeling en bronnen op de recordroute komen uit aanroepermetadata** (`int02_bedoeling`, `int02_bronnen`), omdat het record daar geen veld voor heeft. Ze worden wel in het document gebonden, zodat een latere wijziging het oordeel historisch maakt. Maar ze zijn niet recordgezaghebbend zoals de INT-03-toelichting. Dit hoort bij DEF-626/opslag.
5. **Een INT-02-`error` blokkeert de acceptatie** via de generieke DEF-624-regel (`evaluation_error`), net als bij elke andere regel met een evaluatorfout. Pass, fail, review, NA en NE raken score en acceptatie niet (bewezen). Ik heb dit niet gewijzigd; ter kennisneming bij B5/B6.
6. **De mypy-ratchet (`make mypy-check`) faalt al op HEAD**: baseline 0, maar er zijn 13 fouten uit WP1/WP2. Niet in mijn bestanden; mijn eigen mypy-fout (`kern`) is hersteld.
7. De omvang is groter dan geraamd (zie boven), vooral door tests.
8. Opslag, herladen en C118, UI-presentatie en activering zijn niet in dit pakket gedaan of bewezen.

## Bronnen

- `wp5a-integratievoorstel-v1.md`, `besluit-proef-en-wp5a-v1.md`, `wp5a-opdracht-claude-v1.md`
- `src/domain/int02/contract.py` (`maak_invoer`, `ontbrekende_invoer`, `beoordeel`, `toets_actualiteit`)
- `src/services/validation/int02_assessment_service.py` (`assess`, `_configuratie` privé)
- `src/services/validation/evaluators/decision_rule_assessment.py:107-148`
- `src/services/validation/modular_validation_service.py:1465-1473` (DEF-771-NE-pad), `:1640` (boeking)
- `tests/fixtures/def835_int02_ontwerpgevallen.json` (C56, C105, C107, C112, C117)
- `tests/unit/validation/test_def835_int02_assessment_service.py:305-308`
