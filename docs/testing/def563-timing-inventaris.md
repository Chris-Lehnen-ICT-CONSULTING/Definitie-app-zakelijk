# DEF-563 — timinginventaris en onderbouwde gedragscontroles

De timinginventaris bewaakt dat bestaande timingvergelijkingen niet ongemerkt
veranderen. Zij is geen bewijs dat alle grenzen zinvol of alle tests stabiel
zijn. Het [SSOT-masterplan](https://linear.app/definitie-app/document/implementatieplan-definitieagent-kwaliteitsketen-645f1330ac28)
blijft normatief; DEF-563 blijft open voor de overige kandidaten.

## Vier timingtests omgebouwd — 10 september 2026

Chris heeft na het [grenswaardenonderzoek](https://linear.app/definitie-app/document/def-563-onderbouwing-en-dispositieadvies-voor-vier-timingtests-8cb9b4298994)
opdracht gegeven de vier tests om te bouwen en de bijbehorende oude
timingregistraties op te ruimen. De vijf absolute grenzen zijn expliciet
ingetrokken; er is geen claim dat de oude doorvoer of initialisatietijd behouden
of verbeterd is.

| Huidige test | Gedrag dat verplicht blijft | Vervallen grens |
| --- | --- | --- |
| `TestPerformanceBenchmarks::test_cache_roundtrip_at_capacity_without_eviction` | 1000 vaste writes/reads, waarden en exacte cachecijfers, alle waarden na heropenen | set <2 s en get <0,5 s |
| `TestLoadTesting::test_cache_stays_correct_when_workload_exceeds_capacity` | 2500 vaste set/get-paren, waarden, capaciteit 1000 en 1500 evictions | >500 paren/s |
| `TestPerformanceRegression::test_cache_persists_surviving_entries_after_eviction` | 2000 vaste paren, capaciteit/evictions, verdwenen sleutel en alle 1000 overblijvende waarden na heropenen | >1000 paren/s |
| `TestPerformanceRegression::test_tabbed_interface_reuses_prewarmed_container_and_repository` | echte UI-constructie, container-/repositoryhergebruik, componentkoppeling en echte service in een geïsoleerde omgeving | UI-init <200 ms |

De eerste drie staan in `tests/integration/performance/test_performance.py`;
de vierde in `tests/integration/performance/test_def66_lazy_loading.py`.
De tests blijven via hetzelfde pad en dezelfde marker deel van de verplichte
integrationgate. De ongebruikte UI-grensconstante en oude testnamen zijn
verwijderd; overige testfuncties en fixtures blijven behouden.

Cache-writes gebruiken nog steeds de echte serializer, HMAC, fsync en
bestandsvervanging op eigen tijdelijke opslag. Geen versnelling door opslag
over te slaan. De directe tests voor uitgesteld laden, eerste creatie en
hergebruik van PromptServiceV2 blijven afzonderlijk bestaan. De UI-test
registreert opruiming van de editverbindingen die haar eigen instanties openen.

De timing- en doorvoermetingen worden informatief in de JUnit-testsuite
vastgelegd met `record_testsuite_property`, onder unieke `def563_`-namen.
Deze pytestfixture ondersteunt xunit2; de canonieke integrationgate draait
serieel. Onder pytest-xdist is deze meetregistratie niet gegarandeerd. Dat
verandert de gedragsassertions niet en levert geen nieuwe prestatienorm op.

## Actuele inventaris en bronbinding

Na deze vier vervangingen blijven **146 kandidaatvergelijkingen op 116
locaties** over, waarvan **114 locaties onbeoordeeld**. Dit is geen telling
van 114 bewezen instabiele tests en geen doel om alle tijdscontroles te verwijderen.

De vier verdwenen locaties omvatten vijf vergelijkingen. De 13 resterende
locaties in dezelfde twee bestanden houden hun vergelijkingen, status en
reden; alleen hun bestandshash verandert omdat de inventaris de AST van
het hele bestand bindt. Registraties buiten deze twee bestanden blijven gelijk.
Het veld `source_commit` is de historische referentie van de oorspronkelijke
inventaris; de actuele binding gebeurt met `source_sha256`, niet met dat veld.

De twee overige eerder beoordeelde locaties blijven:

- `test_performance_tracking_fix.py::TestTimerScope::test_timer_resets_per_main_call`:
  gemockte klok, geen machinegevoelige stopwatch. De bestaande skip blijft;
  deze registratie claimt geen actuele CI-bescherming.
- `utils/test_resilience_timeout.py::test_with_full_resilience_bounds_execution_time`:
  echte timeoutgrens. De call moet bij 0,5 s timeout afbreken, ruim vóór de
  gesimuleerde hang van 6 s; <1,5 s blijft verplicht.

De eerder onder PR #446 vervangen concurrencyproxy blijft vervangen door
events en resultaatbehoud. Het vijfsecondenvangnet daar begrenst een testhang,
zonder een responstijd of doorvoer voor de app te beloven.

## Gebruik en interpretatie van de ratchet

```sh
python -I -B scripts/ci/test_timing_assert_ratchet.py
python -I -B scripts/ci/timing_assert_ratchet.py .
python -I -B scripts/ci/timing_assert_ratchet.py . --inventory
```

De eerste twee commando's blijven blokkerende preflight-stappen. De derde
toont uitsluitend een inventaris; hij accepteert of wijzigt niets.

Exit 0 betekent gelijk aan de beoordeelde inventaris, 1 betekent review nodig,
2 betekent onbruikbare scope/bron/configuratie. Lege scope en symlinks worden
afgewezen. Er is geen automatische update en geen numerieke nuldoelstelling.

De checker vergelijkt bronhashes en kandidaten met de aangeleverde baseline.
Hij bewijst geen menselijke goedkeuring of inhoudelijke juistheid van een
nieuwe baseline. Daarom moeten nieuwe, verdwenen en gewijzigde registraties
met reden en vervangend bewijs worden beoordeeld. Ook wijzigingen aan andere
functies in hetzelfde bestand veroorzaken terecht herbeoordeling van de
bestandshash, zonder dat daarmee iedere vergelijking inhoudelijk gewijzigd is.

## Bewijs en grenzen van deze deelstap

Het oorspronkelijke rood staat op main `41075246`, Tests-run `34482628145`,
integration-job `102888928590`: vier timingfailures. Een extra proef met
alleen een kunstmatige meetklok laat de oude cachetest falen nadat de
functionele assertions al zijn gepasseerd. Dat is de gereproduceerde testfout;
een groene ongewijzigde herhaling is niet als oplossing gebruikt.

Voor oplevering worden de nieuwe tests op de echte code uitgevoerd én met
gerichte fouten in waarden, opslag, eviction, containerhergebruik, servicekeuze
en lazy loading. Een kunstmatig trage meetklok moet geen vals falen meer geven.
De timingratchet moet vóór de expliciete baseline-aanpassing rood en daarna
groen zijn. De PR vermeldt de daadwerkelijk uitgevoerde proeven en gates.

Deze stap lost niet de hele timinginventaris op. De aanvullende cachetestgaten
van DEF-738 en gedragspunten van DEF-740 blijven afzonderlijk geregistreerd.
Ook het oude alternatieve perf-profiel en overige tests worden hier niet
stil aangepast. Een Fase-0-go vereist een afzonderlijke beoordeling van
actueel gezamenlijk bewijs.

Historische tellingen, afgewezen voorstellen en oorspronkelijke reviewbewijzen
zijn terug te vinden in Git bij PR #446 en in DEF-563. De oude `retain-risk`-tekst
voor deze drie cachetests is door bovenstaande dispositie vervangen en geldt
niet meer als actuele instructie.

Bronnen: [DEF-563](https://linear.app/definitie-app/issue/DEF-563),
[PR #446](https://github.com/Chris-Lehnen-ICT-CONSULTING/Definitie-app-zakelijk/pull/446),
[grenswaardenonderzoek](https://linear.app/definitie-app/document/def-563-onderbouwing-en-dispositieadvies-voor-vier-timingtests-8cb9b4298994).
