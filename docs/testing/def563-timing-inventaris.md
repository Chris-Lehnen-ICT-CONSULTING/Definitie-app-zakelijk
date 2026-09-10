# DEF-563 — gevalideerde inventaris en eerste beoordeling

Bron: PR #446, commit `523c1d06e6377cf77e8882e398a41021407f294e`.
Dit is meetbewijs en een beschrijving van de controle, geen implementatieplan.
Het live SSOT-masterplan blijft normatief; DEF-563 blijft open.

## Wat de telling betekent

De exacte AST/regex uit de issuecomment van 10 september levert op deze commit
109 assert-statements in 35 bestanden op. Vier daarvan controleren `hit_rate`,
geen tijd: drie in `tests/unit/test_cache_system.py` en één in
`tests/integration/performance/test_performance.py`. Drie andere gebruiken een
gemockte klok in `TestTimerScope.test_timer_resets_per_main_call`.
Daaruit volgt geen exact aantal werkelijk machinegevoelige checks.

De nieuwe scanner leest 409 Pythonbestanden onder `tests/` zonder ze te importeren.
Hij vindt **152 kandidaatvergelijkingen op 121 locaties in 44 bestanden**.
Dit is een andere meeteenheid en methode dan de 109 assert-statements:
samengestelde asserts kunnen meerdere vergelijkingen hebben. Ook symbolische
grenzen en relatieve metingen zijn meegenomen. Deze getallen zijn geen
verwijderdoel, geen bewezen wall-clock-inventaris en geen bewijs van groei.

Herkenning: naamindicaties, bekende `time`-klokken inclusief importaliases en
eenvoudige toekenningsoverdracht binnen één scope. Alleen <, <=, > en >=;
assertion-berichten, hitpercentages, geheugen en zuivere gelijkheidschecks vallen
buiten die herkenning. Een gemockte klok wordt niet automatisch uitgesloten:
die kandidaat vraagt een inhoudelijke dispositie. Helpers worden ook opgenomen.

Beperkingen: geen volledige dataflowanalyse, geen interprocedurele herleiding,
geen automatische bepaling van skips/markers/CI-uitvoering. Een nieuwe obscure
helper of niet-herkende klok kan gemist worden. Conservatieve overdracht kan
juist te veel markeren (bijvoorbeeld het aantal geslaagde latencywaarnemingen).
De oorspronkelijke baseline noemt de overige 116 locaties daarom expliciet
`unreviewed`; de vervolgbeoordeling hieronder verlaagt dit naar 115.

## Eerste beoordeling, bestaande bescherming behouden

| Testlocatie | Dispositie en unieke bescherming | Bewijs / zekerheid |
| --- | --- | --- |
| `test_performance.py::TestPerformanceBenchmarks::test_cache_performance` | `retain-risk`: twee absolute grenzen blijven; waarden per sleutel en exacte hits/misses/entries/evictions beschermen correctheid. Een snelle verkeerde of niet-duurzame cache mag niet voldoen als vervangend bewijs. | CI-incident PR #434, run 34112419429: set 2,82 s bij grens 2 s, geregistreerd in DEF-563. Timinggevoeligheid bekend; oorzaak en gelijkwaardige kalibratie niet bewezen. |
| `test_performance.py::TestLoadTesting::test_stress_testing` | `retain-risk`: >500 ops/s blijft; vaste werklast 2500 met capaciteit 1000, waarden en eviction-statistieken blijven verplicht. | Dezelfde CI-registratie: 185,73 ops/s. Geen representatieve relatieve vervanging bewezen. |
| `test_performance.py::TestPerformanceRegression::test_throughput_regression` | `retain-risk`: >1000 ops/s blijft; vaste 2000 operaties, eviction, writes en alle behouden waarden na reopen zijn essentieel. | Bestaand JUnit van PR #445: push-run 34444974415 poging 1 faalt; PR-run 34445050060 slaagt. Dit betreft de historische testversie, niet de nieuwe werklast uit PR #446. |
| `test_performance_tracking_fix.py::TestTimerScope::test_timer_resets_per_main_call` | `deterministic`: drie grenzen beoordelen de gemockte 50/30 ms en niet-cumulatieve registratie. Geen reden voor verwijdering wegens runnerbelasting. | Bron bevat `[1.0, 1.05, 2.0, 2.03]` en een bestaande skip wegens verouderde main-mocks. Geen actuele CI-bescherming claimen. |
| `utils/test_resilience_timeout.py::test_with_full_resilience_bounds_execution_time` | `contract`: <1,5 s behouden naast TimeoutError bij timeout 0,5 s en een dummycall van 6 s. Beschermt tijdige afbreking van een hang. | Rechtstreeks broncontract DEF-428. In deze ronde niet opnieuw uitgevoerd en geen flakinessuitspraak gedaan. |

De eerste drie paden vallen onder `tests/integration/performance/`. De
canonieke integrationgate selecteert dit pad en is blokkerend; de historische
JUnit bevat alle drie als werkelijk uitgevoerde tests. Bron: `.github/workflows/test.yml`.
De huidige bronbeoordeling is gebonden aan bovenstaande commit. Een groene
herhaling bewijst geen runneroorzaak of opgeloste instabiliteit.

## Werking van de ratchet

```sh
python -I -B scripts/ci/test_timing_assert_ratchet.py
python -I -B scripts/ci/timing_assert_ratchet.py .
python -I -B scripts/ci/timing_assert_ratchet.py . --inventory
```

De eerste twee commando's staan als blokkerende stappen in de bestaande
`preflight-checks`-job van `quality-gates.yml`, op PR en push naar main.
De eigen proeven gebruiken uitsluitend synthetische bron en tijdelijke opslag.
Het laatste commando schrijft alleen JSON naar stdout; het accepteert niets.

De baseline bevat concrete scope-identiteiten, vergelijkingen en een AST-hash
van het hele betrokken testbestand. Nieuwe locaties, verdwenen assertions en
gewijzigde bron vragen review, ook wanneer het aantal gelijk blijft of daalt.
De bestandshash bewaakt ook gewijzigde moduleconstanten, fixtures en skipmarkers.
Comments en opmaak veranderen de hash niet; andere wijzigingen in zo'n bestand
kunnen meerdere bestaande locaties opnieuw laten signaleren. Dat is een bewuste
onderhoudsafweging om gewijzigde context niet stil onder een oud oordeel te laten vallen.

Gecontroleerd dummyvoorbeeld: een bestand bevat `test_timing` met
`assert elapsed < 1` en een onafhankelijke `test_value` met `assert 1 == 1`.
Alleen die laatste assertion veranderen naar `assert 2 == 2` geeft exit 1 en
een melding voor `test_timing`. De reviewlast geldt dus ook voor gewone
correctheidstests in hetzelfde bestand; dit is geen bewijs van gewijzigde timing.

Exit 0 = gelijk aan vastgelegde inventaris; 1 = review nodig;
2 = ongeldige scope, onleesbare/ongeldige bron of onbruikbare baseline.
Lege Python-scope en symlinks worden afgewezen. Geen app-, provider- of databasecalls.

Er is **geen automatische `--update` en geen numerieke nuldoelstelling**.
Een baselinewijziging hoort bij de inhoudelijke review: leg bij nieuwe of
gewijzigde kandidaten de reden, unieke bescherming en vervangend bewijs vast;
verwijderen of hernoemen is geen automatische schuldreductie. `unreviewed` is
de expliciete beginschuld, geen toestemming om nieuwe schuld toe te voegen.
De checker valideert het formaat en de bronbinding; hij kan menselijke
goedkeuring of de inhoudelijke juistheid van een gewijzigde baseline niet bewijzen.

Concreet: een nieuwe kandidaat toevoegen geeft exit 1. Die kandidaat vervolgens
met de actuele hash, `status: unreviewed` en een generieke niet-lege reden in de
baseline opnemen geeft exit 0. Dit is met dummybron gereproduceerd. De menselijke
review moet daarom de baselinediff zelf beoordelen; geen automatische `--update`
hebben verhindert handmatige acceptatie niet. `source_commit` is bronregistratie:
de checker valideert alleen het SHA-formaat, niet het bestaan of de Git-herkomst
van die commit. De automatische bronbinding vergelijkt de actuele AST met de
hashes en vergelijkingen in de aangeleverde baseline.

## Verificatie en grenzen van deze levering

CLI-regressieproeven dekken klokaliases/afgeleide snelheid, symbolische en
samengestelde grenzen, niet-timinggevallen, gemockte klokken, wijzigingen bij
gelijkblijvend aantal, verwijdering, veranderde moduleconstanten, nieuwe locaties,
opmaakstabiliteit, geneste scopes zonder uitvoering, lege/kapotte scope,
symlinks en ongeldige/dubbele baselinevelden. De proeven zijn eerst rood gemeten.

Lokaal eindbewijs van de eerste inventarisstap: 11 CLI-tests groen; checker op de echte bron exit 0 met
121 locaties en nul wijzigingen ten opzichte van de baseline; Ruff en Black
schoon. Twee fouten in geïsoleerde kopieën worden gedetecteerd: alle wijzigingen
accepteren en de context-hash negeren. Op dat moment was nog geen onafhankelijke
review of GitHub-CI-uitvoering beschikbaar; de latere review staat hieronder.
Geen volledige applicatiesuite gedraaid.

De eerste inventarisstap veranderde geen applicatietest. Het hieronder beschreven
vervolg vervangt één timingproxy met gedragsbewijs. De cachebenchmarks en hun
grenzen zijn ongewijzigd, evenals markers, benchmarkfixture en productiecode. De grotere
clusters zijn niet inhoudelijk afgedaan. De ontbrekende benchmarkguard blijft
een afzonderlijk bekend punt; de geïnstalleerde plugin heeft al een consument
in `test_validation_performance_baseline.py::test_validation_throughput`.

Bronregistratie: [DEF-563](https://linear.app/definitie-app/issue/DEF-563),
[PR #446](https://github.com/Chris-Lehnen-ICT-CONSULTING/Definitie-app-zakelijk/pull/446).

## Vervolg: concurrency aantonen zonder stopwatch

Beoordeelde en vervangen kandidaat:
`tests/unit/services/test_modern_web_lookup_service_unit.py::test_parallel_lookup_concurrency_and_timeout`.
De oorspronkelijke grens `elapsed < 0.55` schatte parallelle uitvoering af uit
twee fakeproviders met elk 0,3 seconde slaap. Het overige bewijs (`list` en
minstens één resultaat) liet verlies van één providerresultaat toe.

Vervanging: `test_parallel_lookup_waits_for_both_providers` gebruikt twee events.
Beide fakeproviders moeten zijn gestart vóór de test ze vrijgeeft. De lookup
mag vóór die vrijgave niet klaar zijn en moet daarna beide verwachte definities
met bronnaam teruggeven, in een lijst met exact twee elementen. De echte
`ModernWebLookupService.lookup` en providerdispatch/ranking blijven draaien.
Er zijn geen providercalls naar buiten. Het vijfsecondenvangnet begrenst een
testhang bij een seriële regressie; het is geen doorvoer- of responstijdeis.
De test ruimt uitsluitend zijn eigen async taak op, ook bij falen.
De oude totale grens van 0,55 seconde vervalt daarmee daadwerkelijk: tragere
maar gelijktijdige uitvoering kan slagen. De vervanging bewijst concurrency en
resultaatbehoud, geen behoud van die oude prestatienorm.

Gericht foutbewijs, met proceslokale mutanten en geïsoleerde dummy-opslag:

- De oude test slaagt wanneer na de gather bewust maar één resultaat overblijft.
- De nieuwe test faalt op diezelfde fout, met `len(results) == 2`.
- De nieuwe test faalt als de twee lookups serieel worden afgewacht: de tweede
  provider bereikt de barrier niet. De proef stopt via het hangvangnet.
- Het volledige gewijzigde testbestand slaagt op de echte ongewijzigde service:
  zes tests groen. Ruff en Black zijn schoon. De checker slaagt op de aangepaste
  baseline met 120 locaties en nul afwijkingen van de vastgelegde inventaris.

De ratchet signaleerde eerst exact de verdwenen oude locatie (exit 1).
Pas na dit vervangende bewijs is die ene entry expliciet verwijderd uit de
baseline. Actuele stand na deze wijziging: **151 kandidaatvergelijkingen op
120 locaties in 43 bestanden**, waarvan 115 locaties nog onbeoordeeld zijn.
De vijf eerdere beoordelingen blijven behouden. Dit bewijst geen algemene
afname van machinegevoelige tests buiten deze ene beoordeelde wijziging.

Voor de drie cachebenchmarks blijft `retain-risk` gelden. Hun set-pad omvat
HMAC-serialisatie, een atomische bestandsvervanging en `fsync`. Er is geen
gelijkwaardige relatieve meting bewezen; hun vier absolute grenzen blijven staan.

## Onafhankelijke review en afronding — 10 september 2026

De zes lokale wijzigingsbestanden zijn onafhankelijk beoordeeld vanaf
`523c1d06e6377cf77e8882e398a41021407f294e`. Geen blokkerende codefout gevonden.
Expliciete waivers voor deze levering: de extra reviewlast van de bestandshash
en het vertrouwen op inhoudelijke menselijke baselinereview. De hierboven
beschreven dummyproeven onderbouwen beide beperkingen; dit zijn geen claims
van automatische goedkeuring of volledige detectie van timingafhankelijkheden.

Opnieuw gemeten: 11 checker-tests en zes weblookup-tests groen; beide
checkermutanten gedetecteerd; de nieuwe weblookup-test detecteert seriële
uitvoering en resultaatverlies, terwijl de oude test resultaatverlies accepteert.
Bij een geïnjecteerde fout terwijl beide fakeproviders geblokkeerd waren bleven
na de testopruiming nul nieuwe actieve taken over. Dit bewijst dat foutpad,
niet alle mogelijke providerfouten. Alle uitvoeringsproeven gebruikten
dummybron of fakeproviders, met geïsoleerde opslag en offline-bootstrap voor
applicatie-imports. Ruff en `git diff --check` zijn schoon. Black is na een
sandboxweigering via de normale goedkeuringsroute opnieuw uitgevoerd: exit 0,
alle drie gewijzigde Pythonbestanden blijven ongewijzigd.

PR #446 was bij de review OPEN en draft, met bovengenoemde commit als head;
de groene PR-checks gelden niet voor deze ongepubliceerde wijzigingen. De
nieuwe checker en regressietests zijn blokkerende preflight-stappen en werken
door naar de verplicht gestelde `Quality Gate Summary`. Vóór merge blijven
inhoudelijke goedkeuring van de baselinediff en groene verplichte CI op de
daadwerkelijk gepubliceerde eindversie nodig. De review zelf is uitgevoerd zonder
commit, push of merge; de latere publicatie- en mergestatus volgen uit PR #446.
Het live SSOT-masterplan en de open DEF-563-scope blijven ongewijzigd.
