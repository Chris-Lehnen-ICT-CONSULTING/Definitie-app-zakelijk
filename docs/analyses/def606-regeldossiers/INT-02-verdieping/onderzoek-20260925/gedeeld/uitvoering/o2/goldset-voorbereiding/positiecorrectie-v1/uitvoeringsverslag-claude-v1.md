# INT-02 O2 — positiecorrectie v1: citaatposities door de dienst (uitvoeringsverslag Claude)

7 oktober 2026. Opdracht van Chris (besluit 9, optie A). Werkboom `.claude/worktrees/DEF-835-int02-o2`, branch `feature/DEF-835-int02-o2`, basis-HEAD `3ba526daefe7da71d8332faba9e5d25fb1df06a3`. **Niet gecommit, niet gepusht, geen live call, `.env` niet gelezen.** Geen andere toetsregels of evaluators gewijzigd en de O1-route niet aangeraakt.

## Kern van de wijziging

Het model levert per passage- en grondcitaat alleen nog het letterlijke citaat en het veld. De code bepaalt `start`/`end`: het citaat moet **precies één keer** als exacte substring (Python-codepunten, geen normalisatie) in de tekst van het opgegeven veld staan. Dan geldt `start` = die vindplaats en `end = start + len(quote)`. Nul vindplaatsen, meer dan één vindplaats (ook overlappend) of een leeg citaat geeft `invalid_citation` met een onderscheidbaar `foutdetail`. De letterlijkheidseis is even streng als voorheen; alleen het rekenwerk verhuist naar code. Het model levert geen posities meer, dus er wordt ook niets gerepareerd.

De afleiding zit in het domeincontract (`domain.int02.contract.beoordeel`) en niet in de AI-dienst. Daardoor gelden dezelfde regels voor elke beoordelaar (model of mens), voor de dienst, voor het proefscript en voor replay (`toets_actualiteit`). "De dienst" uit het besluit is hier dus de code tegenover het model.

## Versiekeuzes

| Wat | Oud | Nieuw | Waarom |
|---|---|---|---|
| Resultaatcontract / modelschema | `def835-int02-assessment/1` | `def835-int02-assessment/2` | Het uitvoerschema verandert: `start`/`end` zijn geen modelvelden meer en het document krijgt `foutdetail`. Het bestaande naamschema `/N` is opgehoogd. |
| Promptversie | `def835-int02-prompt/2` | `def835-int02-prompt/3` | De citaataanwijzing en het uitvoerschema in de systeemprompt veranderen. |
| Contractdocument | `docs/architectuur/contracts/int02_assessment_contract_v1.md` | nieuw `int02_assessment_contract_v2.md` | v1 blijft ongewijzigd als historisch document; v2 begint met een paragraaf "Wijziging ten opzichte van /1". |

Oude documenten blijven historisch via het bestaande mechanisme. `contractversie` en `promptversie` zitten in de `Binding`, dus een document onder /1 of prompt /2 wijkt af van de actuele binding en geeft bij `toets_actualiteit` `review_required` / `historical`.

**Vastlegging dat posities zijn afgeleid.** Het contract heeft geen bestaand veld voor de herkomst van posities. Ik heb er ook geen extra oordeelveld voor toegevoegd, want dat zou de opgeslagen vorm voor UI en export wijzigen. De vastlegging volgt uit `contractversie = def835-int02-assessment/2`: onder /2 zijn `start`/`end` in het bewaarde oordeel per definitie door de code afgeleid. Dat staat in de moduledocstring, in het commentaar bij `CONTRACTVERSIE` en in contractdocument v2. Replay controleert het ook: de bewaarde posities worden weggelaten en opnieuw afgeleid, en elke afwijking maakt het document niet-herleidbaar.

## Gedrag bij modeluitvoer die toch `start`/`end` bevat

**Keuze: weigeren als onbekend veld (`error` / `invalid_output`, `foutdetail` None, geen oordeel).** Dat geldt ook als de meegeleverde waarden juist zijn. Ook `start: null`/`end: null` in een grond wordt geweigerd.

Reden: het schema was al gesloten, want elk onbekend veld (bijvoorbeeld `score` of `confidence`) gaf `invalid_output`. Een uitzondering voor posities zou die strengheid verzwakken. Juiste posities stil overnemen of foute stil negeren zou bovendien weer een vorm van modelpositie-acceptatie of -reparatie zijn. Prompt /3 vraagt geen posities en noemt `start`/`end` niet meer, en de bestaande regel "zonder extra velden" blijft staan.

Gevolg: de ruwe v4-uitvoer van C112, mét de foute posities 71/46, blijft afgewezen, nu als `invalid_output` in plaats van `invalid_citation`. Getest in `test_c112_ruwe_v4_uitvoer_met_te_korte_posities_wordt_geweigerd`.

## Gewijzigde bestanden (bestand:regel, stand na wijziging)

**`src/domain/int02/contract.py`** (SHA-256 `e867bb0e8584eaeff2ecf65dec78ac970d0d4cd1f6e4c486fde9aaa467a866f3`)

- r.1–35: moduledocstring naar /2, met de afleidingsregel, `foutdetail` en de bewaarde vorm.
- r.62–64: `CONTRACTVERSIE = "def835-int02-assessment/2"`, met een versieopmerking.
- r.89–94: `foutdetail`-waarden `niet_gevonden`, `niet_uniek`, `leeg` en `grond_niet_herleidbaar`.
- r.100–103: `_PASSAGEVELDEN = {quote, function, ground}`, `_GRONDVELDEN = {field, ref, quote}` en `_POSITIEVELDEN = ("start", "end")`.
- r.441–457: `_AfwijzingError` krijgt `detail`; `_citaat(voorwaarde, detail)`.
- r.464–475: nieuw `_positie(tekst, citaat)` met de enige exacte vindplaats. Het zoekt via `find` en daarna `find(…, start + 1)`, zodat ook een overlappende tweede vindplaats telt. Het oude `_staat_op` is vervallen.
- r.487: een grondcitaat is `None` of tekst; de positietypecontrole is vervallen (r.~483 oud).
- r.507–527: `_grondbron` geeft `grond_niet_herleidbaar` als detail (r.519–525).
- r.530–549: `_met_posities(uitvoer, invoer)` vervangt `_controleer_citaten`. Het levert een nieuwe kopie met afgeleide posities op; een grond zonder citaat krijgt `start`/`end` None. De invoer wordt niet gemuteerd.
- r.671–678 en r.691, r.709: `Beoordelingsdocument` krijgt `foutdetail: str | None = None` (laatste veld met default) en `als_dict()` toont het.
- r.731–797: `beoordeel` volgt structuur → `_met_posities` → samenhang → status op het verrijkte oordeel. Het bewaarde `oordeel_json` bevat de afgeleide posities en `foutdetail` komt uit de afwijzing.
- r.802–824: `_zonder_posities(oordeel)`, alleen voor replay.
- r.831–861: `_herleidbaar` hervalideert met `_zonder_posities(oordeel)`, zodat bewaarde posities exact moeten overeenkomen met een nieuwe afleiding.

**`src/services/validation/int02_assessment_service.py`** (SHA-256 `4d9d7200bb20616c541a9b12e5957addac085957725ab4cfa2c5856be9834a47`)

- r.1 en r.18–21: docstring naar contract /2 en de positieafleiding door het contract.
- r.128–131: `PROMPT_VERSION = "def835-int02-prompt/3"`, met een versieopmerking.
- r.386–393: citaataanwijzing /3. Het citaat moet letterlijk zijn, zonder normalisatie, en precies één keer in het veld voorkomen; zo nodig wordt meer aangrenzende tekst meegenomen. Het model geeft geen posities, want de dienst zoekt het citaat zelf op. De rekeninstructie van /2 is vervallen, net als de hele sectie "Posities:" (r.~390–396 oud).
- r.400–404 en r.406–415: het uitvoerschema in de prompt noemt alleen `quote`, `function` en `ground`, en voor de grond `field`, `ref` en `quote`. Elk citaat moet "precies één keer" voorkomen.
- De fail-aanwijzing uit /2 is **ongewijzigd** (r.374–385). Parser, aanroep, cache en binding zijn niet gewijzigd.

**`src/services/validation/evaluators/decision_rule_assessment.py`** r.6: alleen de docstringverwijzing gaat van /1 naar /2. Het gedrag is ongewijzigd.

**`docs/architectuur/contracts/int02_assessment_contract_v2.md`** (nieuw, kopie van v1 met aanpassingen): een wijzigingsparagraaf, het passage- en grondschema, de foutdetails, de statusmapping, de plaatshouder `{passage}` (afgeleide `start`), de binding, de documentvelden en de replay.

**`tests/fixtures/def835_int02_ontwerpgevallen.json`**: `contract` gaat naar /2. Uit alle 9 modelresponsen zijn alleen de regels `start`/`end` en de grondposities verwijderd (18 regels en 9 grondobjecten); verder is niets gewijzigd. C117 "verzonnen-citaat" blijft `invalid_citation`, nu als `niet_gevonden`.

**Tests**

- Nieuw: `tests/unit/domain/test_def835_int02_citaatposities.py`, 41 tests:
  - uniek citaat met afgeleide posities aan begin, midden en eind van het veld, het hele veld, met diacrieten (NFC) en astrale tekens;
  - grondcitaat in bedoeling, bron, context en kern, en een grond zonder citaat;
  - `niet_gevonden` bij leesteken, hoofdletter, witruimte, NFD-vorm, verzonnen tekst en een citaat dat alleen in een ander veld staat;
  - `niet_uniek` bij twee en bij overlappende vindplaatsen, ook voor een grond;
  - `leeg` voor passage en grond, en `grond_niet_herleidbaar`;
  - vijf varianten met meegeleverde posities die als `invalid_output` worden geweigerd;
  - C112-regressie, ruw en zonder posities;
  - replay, met gemanipuleerde en met ontbrekende posities;
  - geen mutatie van de invoer en de meldingsvolgorde op de afgeleide `start`.

  De verwachte posities zijn met de hand uitgeschreven. Uit v4 zijn alleen de kern- en bedoelingstekst van C112 en de ruwe modeluitvoer overgenomen.
- `tests/unit/services/prompts/test_def835_int02_prompt.py`:
  - versie /3 en de nieuwe citaatregel, die precies één keer tussen "Invoer:" en het uitvoerschema staat;
  - geen positie-instructie meer (`"start"`, `"end"`, `len(`, `tekst[start:end]`, nulgebaseerd, einde exclusief, codepoint, "Posities:") en de /2-regel is weg;
  - het schema noemt alleen citaat en veld;
  - de fail-aanwijzing staat er letterlijk ongewijzigd in;
  - de lijst casusfragmenten is uitgebreid (C105/C107/C112-teksten).
- `tests/unit/validation/test_def835_int02_assessment_service.py`:
  - testhelpers zonder posities;
  - 5 nieuwe dienst-tests: posities via de echte dienst, `foutdetail` per fouttype met servicereden `invalid_citation`, en modelposities als `invalid_output`;
  - herijkt: oordeel met afgeleide posities, codepunttest (17/45 en niet UTF-16 19), witruimtecitaat en de cijferlimiettest op een ander getalveld.
- Herijkt naar vorm /2, zonder positievelden in de modelresponsen, met de bewering ongewijzigd: `test_def835_int02_contract.py`, `test_def835_int02_evaluator.py`, `test_def835_int02_modular.py`, `test_def835_int02_wrappers.py` en `test_def835_int02_modelproef.py`. In de modelprooftests is een citaatfout nu een citaat dat niet in de kern staat, in plaats van een verschoven `start`.

## Script `scripts/analysis/def835_int02_modelproef.py`

**Niet gewijzigd.** Het script gebruikt geen posities. Het leest `PROMPT_VERSION`, de systeemprompt (voor de hash), `document.foutcategorie == FOUT_CITAAT` en `oordeel["verdict"]`; die blijven werken. `_stopreden` geeft `beoordeling.reden`, en dat blijft `invalid_citation` bij een citaatfout. Het nieuwe `foutdetail` staat in `document.als_dict()` en komt dus in `_samenvatting` mee. Het script breekt niet, maar het manifest moet opnieuw (zie hieronder).

## Testuitkomsten

| Run | Commando | Uitkomst | Log (SHA-256) |
|---|---|---|---|
| Rood, vóór productiewijziging | nieuwe en gewijzigde tests in drie bestanden (zie logkop) | **51 failed, 59 passed** | `rood.log` `0a15cc09d5703b5a084683d618bc40c4a663e1b1a076b5b52a91076123b5994f` |
| Groen 1 | alle 8 nieuwe en gewijzigde testbestanden | **770 passed** | `groen-1-gewijzigde-tests.log` `19044c047cbe18025cd3f1a9c4164478e095bd21e46a0cf1d726438d5682fa27` |
| Groen 2 | `python -m pytest -o addopts="" --import-mode=importlib -q -k "def835 or int02" tests/unit` | **830 passed, 11 skipped**, 0 failed (was 783 passed / 11 skipped) | `groen-2-def835-int02.log` `f7f043358f869995f6b468b3afc561ba3d4719f45379d4a6de46fe1cc355f341` |
| Groen 3 | gerichte selectie takenlijst-v51 (vier bestanden, zie `promptcorrectie-testbinding-v1.md`) | **459 passed** (was 452; +2 prompt- en +5 dienst-tests) | `groen-3-gerichte-selectie-v51.log` `cc987b89cceeeac0d3269ded41be7b5c3b6061d32287e6d660b50e1bee22b206` |
| Extra | `tests/integration/contracts/test_validation_result_schema.py -k int02`: echte evaluatoruitkomst (nu met `foutdetail` in `assessment`) tegen het echte schema | **22 passed** | niet gelogd |

De 59 tests die in de rode run slaagden, zijn bestaande prompttests plus enkele nieuwe die onder /1 toevallig ook al `invalid_output` gaven, omdat die uitvoer geen grondposities had. Na de implementatie bewaken ze dat een naïeve implementatie, die modelposities accepteert, faalt.

Lint op de 11 gewijzigde Python-bestanden: `ruff check` (venv, 0.15.17) `All checks passed!`; `black --check` (26.5.1, gelijk aan de hook): ongewijzigd na één herformattering van het nieuwe testbestand. `git diff --check` is schoon. In `src/` zijn geen `print()`-aanroepen toegevoegd.

Let op: `*.log` staat in `.gitignore`, dus de logs worden zonder `git add -f` niet meegecommit, net als de eerdere promptcorrectie-logs. Daarom staan de hashes hierboven.

## Gevolgen voor het kwalificatiemanifest: v5 nodig

Manifest v4 (`57a988de…364a`, identiteit `0a095697…d644`) is na deze wijziging **niet meer bruikbaar**. De runner weigert het terecht met een identiteitsafwijking. Wat verandert:

- `identiteit.profiel.promptversie`: `def835-int02-prompt/2` → `def835-int02-prompt/3`.
- `systeemprompt_sha256` per geval: `92deecb85fecb180136a12983dc544d98e03f010bd9cc1446d342ce2bd82da7c` → `da4a4112b580da2924b5940ac2723ef5e177ad48ef15890b66d8d91f285a7ca6` (7.904 tekens; offline nagerekend met `bouw_int02_prompt` en `laad_int02_norm`). Het modelschema staat in de systeemprompt en in `contract.py`; een aparte schemahash heeft het manifest niet. De schemawijziging zit dus in deze twee hashes.
- `identiteit.bestanden` (stand na de reviewcorrectie hieronder):
  - `src/domain/int02/contract.py`: `6dcae57b…` → `c20543f0…`;
  - `src/services/validation/int02_assessment_service.py`: `1b7144c5…` → `4d9d7200…`;
  - `src/toetsregels/runtime_contract.py`: `e138b83c…` → `205c8bdb…` (alleen commentaar).

  Het script `def835_int02_modelproef.py` en de overige ketenbestanden zijn ongewijzigd. De ontwerpgevallen-fixture (`d20b9246…`) staat in `KETENBESTANDEN` van het script, maar niet in `identiteit.bestanden` van v4.
- Alle 43 payloads bevatten de systeemprompt, dus alle payloadhashes en het payloadbestand veranderen, en daarmee `identiteit_sha256`.
- Ongewijzigd: `kwalificatie-gevallen-v1.json` (`af1ab46c…6953`), norm en normhash, T-tekst, limieten, prijzen, router, transport en versies.

Dus: offline manifest v5 en payloads v5 aanmaken, daarna een nieuw exact akkoord van Chris op de v5-hashes, en pas dan opnieuw alleen fase 1 (C105/C107/C112).

## Open punten

1. **Codex-review** van deze diff, tegen het besluit, T-tekst, contract v2 en de v4-uitslag, staat nog open. Aandachtspunten: de keuze voor `invalid_output` bij meegeleverde posities, en de plaats van de afleiding in het contract in plaats van in de AI-dienst.
2. **ruff 0.16.5 (pre-commit-hook) niet gedraaid.** `uvx ruff@0.16.5` vroeg goedkeuring die in deze sessie niet beschikbaar was. Venv-ruff 0.15.17 en black 26.5.1 zijn schoon. De hook kan bij de commit nog strengere regels toepassen.
3. **Volledige `make test` niet gedraaid.** Alleen de def835/int02-selectie, de gerichte v51-selectie en de INT-02-schema-integratietests. Buiten deze selectie importeert geen enkele test het INT-02-contract, de dienst, de evaluator of de fixture (via grep gecontroleerd).
4. ~~Verouderde verwijzingen naar /1 in commentaar~~: bijgewerkt in de reviewcorrectie hieronder.
5. **Aandachtspunt 3 (besluit 3, meerdere passages)** blijft ongemoeid. Prompt /3 raakt alleen de citaatregel en het schema.
6. Een **in het veld niet-uniek citaat** wordt nu `invalid_citation` / `niet_uniek`, ook als het model "de juiste" vindplaats bedoelde. Dat is bewust: prompt /3 vraagt om zo nodig meer aangrenzende tekst te citeren. Of dit in de praktijk vaker stopt dan de oude telfout, blijkt pas uit fase 1.

## Reviewcorrectie (Codex, 07-10)

De onafhankelijke Codex-review gaf "commit verantwoord: nee". Opnieuw is er niets gecommit of gepusht, geen live call gedaan en `.env` niet gelezen. Regelnummers en de hash van `contract.py` in de secties hierboven horen bij de stand vóór deze correctie. De actuele stand staat hieronder en in de manifestsectie.

### Bevindingen

1. **Belangrijk: geldig /1-document werd `error`.** De hercontrole (`_herleidbaar`) bouwde altijd een /2-document. Een geldig bewaard /1-document, met posities van het model, faalde daardoor bij de vergelijking. `toets_actualiteit` gaf `error` vóór de historische bindingstoets, terwijl `review_required` / `historical` vereist is. Ik heb dit gereproduceerd met negen echte /1-documenten (zie de rode run).
2. **Klein:** contractdocument v2 bevatte achterhaalde WP1-tekst. Er stond publiek contract 2.2.0 en "geen prompt, service of evaluator".
3. **Klein:** commentaar in `interfaces.py` en `runtime_contract.py` noemde nog /1.

### Fix

**`src/domain/int02/contract.py`** (SHA-256 `c20543f09479b5ae3b079aed6d2ff13f40ee01525875313aa33766d823bf9747`)

- r.68–70: `_CONTRACTVERSIE_V1` en `_BEKENDE_CONTRACTVERSIES` = {/1, /2}.
- r.112–113: `_PASSAGEVELDEN_V1` en `_GRONDVELDEN_V1`, het /1-schema met verplichte `start`/`end`.
- r.428–436: `bereken_binding` (publiek, altijd /2) delegeert aan `_bereken_binding(…, contractversie)`.
- r.493–495: `_staat_op` keert terug. Dit is de regel van /1, letterlijk zoals in HEAD.
- r.498–519 en r.522–543: `_controleer_grondvorm(grond, v1)` en `_controleer_structuur(uitvoer, v1)`. Met `v1` gelden exact de /1-typeregels uit HEAD; zonder `v1` het /2-schema.
- r.589–609: `_controleer_citaten_v1`, de /1-citaatcontrole uit HEAD (`tekst[start:end] == quote` op de opgeslagen posities). Het oordeel blijft dan de uitvoer zelf.
- r.793–807: het publieke `beoordeel` maakt altijd een /2-document en roept `_beoordeel(…, CONTRACTVERSIE)` aan.
- r.809–880: `_beoordeel(…, contractversie)`. Onder /1 gelden de /1-structuur en -citaatcontrole (r.866), zonder `foutdetail` (r.871), omdat /1 dat veld niet kende. Onder /2 geldt de afleiding.
- r.912–957: `_herleidbaar` volgt de **originele** contractversie van het document:
  - een onbekende versie geeft `False`, dus `error` (r.928);
  - onder /2 worden de posities weggelaten en opnieuw afgeleid (r.948);
  - onder /1 wordt het bewaarde oordeel ongewijzigd met de /1-regels herbouwd (r.951).

  Daarna volgt ongewijzigd de bestaande historische bindingstoets in `toets_actualiteit`. Die toets is **niet** naar voren geschoven en de manipulatiecontrole is niet verzwakt: een document is alleen herleidbaar als `_beoordeel` onder zijn eigen versie exact hetzelfde document oplevert. Dat geldt ook voor de binding met haar `contractversie`.

**`docs/architectuur/contracts/int02_assessment_contract_v2.md`**

- De statusalinea onder de kop is bijgewerkt. Het publieke resultaatcontract is `CONTRACT_VERSION = "2.3.0"` (`src/services/validation/interfaces.py:85`), met `assessment`/`signals` voor INT-02.
- Aanwezige onderdelen: de dienst met prompt /3, evaluator `decision_rule_assessment`, de containerfabriek `int02_assessment_service(profiel, budget)` (`container.py:356`) en injectie in `DefinitionOrchestratorV2`/`ValidationOrchestratorV2`.
- Niet actief: het INT-02-record kiest `judgment_review` (`INT-02.json:48`), er is geen bedrading in `orchestrator()`, geen eigen O2-UI en geen opslag.
- Bewijsgrens "Geen app-route" is vervangen door "Niet geactiveerd".
- Toegevoegd: een migratiebullet (/1 → /2) en een zin in de wijzigingsparagraaf.

**Commentaar:**
- `src/services/validation/interfaces.py` r.79–81 en r.287–290: contract /2, en een aanvaard historisch document kan nog /1 zijn.
- `src/toetsregels/runtime_contract.py` r.124: /2. Dit is een ketenbestand; de hash staat in de manifestsectie.

### Referentiemateriaal en tests

- **`tests/fixtures/def835_int02_contract_v1_documenten.json`** (SHA-256 `49ae87d7…28a2`) bevat negen geldige /1-documenten: C105, C107, C112, C115, C116, C101, C118-v1, C118-v2 en het synthetische `SYN-niet-uniek`. Het laatste citaat komt twee keer in de kern voor en is onder /1 geldig op de tweede vindplaats. De documenten zijn **gemaakt met de /1-code zelf**, letterlijk uit git geladen (revisie `3ba526dae`, `contract.py` SHA-256 `6dcae57b…`, gelijk aan de v4-manifesthash), op basis van de ontwerpgevallen uit dezelfde revisie. Dit zijn ontwikkelgevallen, geen goldset of hold-out.
- **Generator** `scripts/analysis/def835_int02_v1_referentiedocumenten.py` (SHA-256 `f7a13de8…9c10`). Geen netwerk, model of sleutel; de herkomsthashes staan in de fixture. Hij staat in `scripts/analysis/` omdat scriptuitvoering vanuit de docs-map in deze sessie goedkeuring vroeg.
- **`tests/unit/domain/test_def835_int02_migratie.py`**, 36 tests:
  - (a) elk geldig /1-document wordt `review_required` / `historical` met de historische melding, ook het niet-unieke geval; het document blijft ongewijzigd;
  - (b) een /1-document met gemanipuleerde `start`, `end`, grondpositie of zonder posities geeft `error`;
  - (c) een /1-document met gewijzigde quote (hoofdletters, een ander citaat op consistente posities, grondcitaat) of gewijzigde status of melding geeft `error`;
  - (d) een gemanipuleerd /2-document (positie, quote, status, melding, /1-label zonder posities) geeft `error`, terwijl het ongemanipuleerde document actueel `fail` is;
  - (e) een onbekende contractversie (/0, /9, "onbekend", op /1- en /2-basis) of een document en binding met verschillende versies geeft `error`.

  Niet getoetst en bewust zo: een /1-document dat volledig consistent is herschreven, bijvoorbeeld naar de andere geldige vindplaats van een niet-uniek citaat, is niet te onderscheiden van een echt document. Dit staat al als bewijsgrens in het contract (authenticiteit hoort bij de opslaglaag).

### Testuitkomsten

| Run | Uitkomst | Log |
|---|---|---|
| Rood, vóór de fix | **10 gefaald** (alle (a)-tests), 26 geslaagd. De (b)–(e)-tests slaagden al, omdat de bug elk /1-document `error` maakte; ze dienen als vangnet tegen een te soepele fix. | `rood-migratie.log` `794196df7af8a25582ef4fa2c66921212df607c5bb15f0d224507b8d86458510` |
| Mutatiecontrole in het geheugen (geen bestand gewijzigd): `_herleidbaar` als "/1 altijd herleidbaar" | 13 van 36 gefaald | niet gelogd |
| Mutatiecontrole in het geheugen: historische toets vóór de integriteitscontrole | 19 van 36 gefaald | niet gelogd |
| Groen 1: alle nieuwe en gewijzigde testbestanden (9) | **806 geslaagd** | `groen-migratie.log` |
| Groen 2: `-k "def835 or int02" tests/unit` | **866 geslaagd, 11 overgeslagen**, 0 gefaald (was 830 + 11) | `groen-migratie.log` |
| Groen 3: gerichte selectie takenlijst-v51 | **459 geslaagd** | `groen-migratie.log` |
| Lint: `ruff check` (0.15.17) en `black --check` (26.5.1) op alle 15 gewijzigde of nieuwe `.py`-bestanden | `All checks passed!`; 15 bestanden ongewijzigd (na black-herformattering van `contract.py` en het migratietestbestand) | `groen-migratie.log` |
| Extra: INT-02-schema-integratie (`tests/integration/contracts/test_validation_result_schema.py -k int02`) | 22 geslaagd | niet gelogd |

`groen-migratie.log` SHA-256: `fb8b2137d5762dcc911ee7ac0120d8f8fe5349229228ef649fe5bbca19f817b2`. `git diff --check` is schoon.

### Gevolg voor manifest v5

Naast de punten in de manifestsectie verandert ook de hash van `src/toetsregels/runtime_contract.py`, omdat het commentaar is bijgewerkt. De systeemprompt verandert door deze correctie niet: `da4a4112…` blijft gelijk, want de dienst is niet aangeraakt. De open punten 1 (Codex-herreview), 2 (ruff 0.16.5 niet gedraaid) en 3 (geen volledige `make test`) blijven staan.
