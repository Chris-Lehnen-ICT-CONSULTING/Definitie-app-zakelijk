# Testgates (DEF-519)

De verplichte gates draaien via één bewaakte runner,
`scripts/testing/run_profile.py`. Make en CI roepen dezelfde profielnamen aan,
zodat er geen tweede, verborgen selectie naast de Makefile kan bestaan.

## Hoofdcommando's

| Commando | Profiel | CI-job/stap |
|----------|---------|-------------|
| `make test-unit` | `unit` | job `test` (via `make test-cov-ci`) |
| `make test-integration` | `integration` | job `integration-tests` |
| `make test-acceptance` | `acceptance-smoke` | job `test`, blokkerende stap |

Aliassen: `make test` = `test-unit` (plus `test-markers-check`),
`make test-smoke` = `test-acceptance`.

Daarnaast `make test-contract` (profiel `contract`) voor de bestaande required
check **Validation Contract Tests** in `.github/workflows/contract-tests.yml`.
Die nodes blijven ook deel van de integrationunie.

Interpreter: `PY` wijst standaard naar `.venv/bin/python`, met terugval op
`python3`; override met `make PY=/pad/naar/python <target>`. `check-python`
eist Python 3.13 en faalt anders hard.

Configureerbaar zijn alleen `GATE_REPORTS` (rapportlocatie, standaard
`reports/gates`) en `GATE_BUDGET` (eindig procesbudget in seconden, standaard
900). Er is bewust géén doorgeefluik voor vrije pytest-argumenten: daarmee
zouden scope of coveragevloer via de omgeving kunnen krimpen. `PYTEST_ADDOPTS`
wordt door de runner uit de omgeving verwijderd.

## Profielschema

| Profiel | Selectie |
|---------|----------|
| `unit` | `unit` — álle unittests, inclusief `slow` |
| `integration` | `integration and not (advisory or future or live)`, verenigd met álles onder `tests/integration/` |
| `acceptance-smoke` | `(acceptance or smoke) and not (advisory or future or live)` |
| `contract` | `contract and not (advisory or future or live)` |
| `advisory` | `advisory` — optioneel, niet verplicht |
| `future` | `future` — optioneel, niet verplicht |
| `live` | geen profiel; geen enkel canoniek profiel selecteert deze nodes |

De integrationgate telt het hele integratiepad mee, óók bestanden die alleen een
`contract`-, `regression`- of `compliance`-marker dragen. Uitsluiting gebeurt
uitsluitend op eigen verklaring van een node (`advisory`, `future`, `live`) —
niet op bestandsnamen en niet via een deselect-lijst. `slow`, `performance` en
`red_phase` blijven binnen de gates.

`advisory` en `future` zijn geen vrijbrief: een echte assertiefout daar levert
net zo goed `status=testfalen` en nonzero op. `live`-nodes raken een echte
externe dienst en worden door geen enkel profiel geselecteerd; de runner vraagt
of verleent geen netwerk-, kosten- of providertoegang.

Dat is selectiegedrag van de runner, geen garantie over elke omgeving. De
aparte, bestaande pre-commithook draait `pytest -m smoke` zonder `not live` en
selecteert de AI-node dus wél. Daar is de eigen `skipif` van die node de rem:
`tests/conftest.py` installeert de offline-bootstrap vóór de applicatie-imports
en forceert dummy providerkeys, en de guard weigert die vorm vóór de testbody.
De sleutelvórm is geen uitspraak over geldigheid of budget.

## Coverage

`make test-cov-ci` meet dezelfde unitselectie (inclusief `slow`) tegen de
ratchet-vloer **45%** over `src/`, via de seriële Coverage-API-route van de
runner (geen pytest-cov-combine, geen xdist). `make test-cov` is de lokale
variant zonder vloer — dat is nadrukkelijk geen CI-ratchet.

De datafile staat in de verse sessieroot van de run; het `.coverage` van de
checkout wordt nooit gelezen of overschreven. Het werkelijke pad staat in de
inventaris onder `coverage_artefacten`, zodat CI precies dát bestand kopieert
en archiveert. XML en `term-missing` zijn ondersteund; HTML wordt niet
geclaimd.

## Outputs

Per gate, in `$(GATE_REPORTS)`:

- `<profiel>-inventaris.json` — geselecteerde nodes, de tellingen hieronder en
  het bootstrapbewijs (`bootstrap.gate_actief`, `bootstrap.sessieroot`);
- `<profiel>-junit.xml` — JUnit-rapport;
- `unit-coverage.xml` + `coverage_artefacten` — alleen voor `test-cov-ci`.

Elke gate schrijft naar eigen paden; een latere gate kan de meting van de
ratchet niet overschrijven (het patroon uit DEF-679).

### Inventaristellingen

De inventaris scheidt de overslag-soorten die pytest zelf ook scheidt. Elke
telling staat naast haar node-ids, zodat zij per node tegen de JUnit van
dezelfde run te leggen is:

| Veld | Betekenis |
|------|-----------|
| `uitgevoerd` | calls die de testbody bereikten en als passed of failed eindigden |
| `overgeslagen` + `overgeslagen_nodes` | skips per unieke node, uit setup of uit de body |
| `collectie_overgeslagen` + `..._nodes` | modules die zichzelf bij collectie overslaan; die leveren nooit een node op en staan dus niet in `items` |
| `xfail` + `xfail_nodes` | verwachte fouten (JUnit: `type="pytest.xfail"`) |
| `xpassed` + `xpassed_nodes` | niet-strikte XPASS; JUnit meldt die als gewone pass |
| `collectiefouten` | niet-importeerbare of anderszins gefaalde collectie |

Een xfail bereikt zijn body wel, maar bewijst geen assertie van de suite; hij
telt daarom niet als `uitgevoerd`, waardoor een xfail-only selectie
`geen-uitvoering` blijft. Een niet-strikte XPASS is een echte, geslaagde call en
telt wél mee — hij staat apart in de inventaris omdat JUnit hem niet van een
gewone pass onderscheidt. Een strikte XPASS is bij pytest een gewone `failed` en
blijft dus testfalen. De statusregel meldt dezelfde tellingen (`uitgevoerd=`,
`overgeslagen=`, `collectie-overgeslagen=`, `xfail=`, `xpassed=`).

## Nonzero en budget

`status=ok` wordt pas gemeld als de inventaris leesbaar is, de offline-bootstrap
aantoonbaar actief was op déze sessieroot, en er minstens één werkelijk
uitgevoerde, niet-overgeslagen testcall was. Een niet-lege collectie is
uitdrukkelijk niet genoeg.

Elk van deze uitkomsten is nonzero en heeft een eigen `status=`-regel:
`testfalen` (1), `collectiefout` (2), `toolfout` (4), `lege-selectie` (5),
`verboden-optie` (8), `ongeldig-budget` (9), `geen-inventaris` (10),
`geen-bootstrapbewijs` (11), `geen-uitvoering` (12), `bootstrapfout` (13), de
coveragestatussen (14–19, waaronder `coverage-onder-vloer`) en
`budget-overschreden` (124). Er is geen fallback, geen tweede aanroep en geen
route waarlangs een ontbrekende map of lege selectie stil groen wordt.

Het budget moet eindig en positief zijn; bij overschrijding gaat de hele
procesgroep neer, zodat er geen weeskinderen achterblijven.

De `status=`-regel begint altijd op een eigen nieuwe regel. De runner deelt zijn
stdout met het pytest-kind, en dat schrijft voortgangstekens zonder afsluitende
newline; bij een afgekapte of hard geëindigde run zou de status daar anders
achter plakken (`..[run_profile] status=…`) en voor elke regelgebaseerde lezer
onvindbaar worden. De kolompositie van het kind is niet uit te lezen, dus de
newline is onvoorwaardelijk — status, exitcode en velden blijven ongewijzigd.

## Bekende beperking

De native SQLite-runtimevergelijking is buiten scope gelaten (download door
Chris overgeslagen). De bekende 3.51.1-closehang wordt hier niet als opgelost
geclaimd.

## Verwijzing

Per-bestand- en per-node-disposities, met eigenaar, reden, trigger en
herbeoordelingsdatum, staan in
[`def519-testdispositions.json`](def519-testdispositions.json). Dat document is
bewijs- en crosswalkadministratie — geen runnerselectie en geen ignorelijst.

Bewijs van dit gedrag staat in `tests/ci/test_canonical_gate_recipes.py` (echte
`make`-aanroepen op een miniatuur-checkout) en
`tests/ci/test_run_profile_fail_closed.py` (de runner zelf).
