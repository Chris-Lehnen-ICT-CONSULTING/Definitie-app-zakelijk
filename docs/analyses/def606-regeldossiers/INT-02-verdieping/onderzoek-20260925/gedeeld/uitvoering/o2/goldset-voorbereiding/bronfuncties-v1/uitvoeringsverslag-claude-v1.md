# Uitvoeringsverslag — contract /4 met bronfuncties (besluit 16)

**DEF-835 · INT-02 O2 · 07-10-2026 · Claude**
Branch `feature/DEF-835-int02-o2`, HEAD `5315fa8e0`. Alles staat **ongecommit**. Er zijn geen live calls gedaan, `.env` is niet gelezen en er staat geen `print()` in `src/`.

Opdracht: besluit 16 van Chris. Ontwerp: `goldset-voorbereiding/bronfuncties-ontwerp-v1.md`.

## 1. Resultaat in het kort

- **Contract.** `def835-int02-assessment/4` staat. Het model levert per passage een `kernvorm` en per grondbron een bronfunctie, met het eigen verdict als laatste veld. De dienst leidt de status af volgens de beslisregel van het ontwerp en past de keuzes 1B–6A toe.
- **Omzetting (2A).** Wijkt de afgeleide status af van het modelverdict, dan legt `omzetting` dat vast. Het modelverdict en de afleiding blijven bewaard in het oordeel.
- **Prompt.** `def835-int02-prompt/5` instrueert de nieuwe velden. De dataprompt bevat nu `grondbronnen`. Het schema loopt via de bestaande schemaroute met de nieuwe pin `d3ad029e24b6b96242f4730686d3a4ebfebd9f46993607e41016761bc7fce715`.
- **Runner.** Voor ontwikkeling staat `max_false_pass` nu op 0. ~~Schema, promptversie en identiteit volgen automatisch de imports.~~ *Gecorrigeerd: de contractversie stond niet in de identiteit (Codex P2a). Zie §2 en `uitvoeringsverslag-claude-v2.md`.*
- **Paper test.** De paper test van het ontwerp is met gesynthetiseerde modeluitvoer herhaald op de 27 regressie- en ontwikkelgevallen: **27/27, met 6/6 review**. Hold-out is niet gelezen en niet gebruikt.
- **Tests.**
  - Rood: 312 gefaald en 220 geslaagd (`rood.log`).
  - Groen:
    - 1191/1191 in de 14 nieuwe en gewijzigde bestanden;
    - 1251 geslaagd en 11 overgeslagen voor `-k "def835 or int02"`;
    - 786/786 voor INT-03/ESS-03;
    - ruff en black schoon.
  - Mutatiecontrole: alle 12 naïeve varianten van kernvoorwaarden worden door de tests gevangen (`mutatie.log`).

## 2. Wijzigingen per bestand

Regelnummers gelden voor de eindstand.

### `src/domain/int02/contract.py` (+635/−94)

**Versies en constanten**

| Regel | Wijziging |
|---|---|
| 1–90 | Moduledocstring naar /4: modeluitvoer, dienstafleiding, het blok `dienst` en replay per versie. |
| 111–112 | `_CONTRACTVERSIE_V4`, `CONTRACTVERSIE = _CONTRACTVERSIE_V4`. `_CONTRACTVERSIE_V3` en de bekende versies V1–V4 blijven. |
| 140–150 | `KERNVORMEN` (5), `NIET_KENMERK = "not_a_criterion"`, `ZWIJGT = "not_addressed"`, `BRONFUNCTIES = FUNCTIES ∪ {not_a_criterion, not_addressed}` en `_RICHTING` (B/G/N/O). |
| 193–206 | Regelcodes `REGEL_*`. Elke tak van de beslisregel heeft een eigen code, die ook als `omzetting` dient. |
| 210–222 | Vaste vragen (4A): `VRAAG_FUNCTIE` en `VRAAG_DEKKING`, plus de koppeling regel → vraag. |
| 228–255 | Redensjablonen voor review: conflict, bronvoorschrift niet overgenomen, bronnen open, geen grond zonder bedoeling, onvolledige dekking. Daarnaast `_ROL`, de slotzinnen en `MELDING_OPEN_PUNT`. |
| 257–274 | `_MODELSTATUS`, de veldensets voor de /4-passage en de bronfunctie, en `_DIENSTVELD = "dienst"`. |

**Schema**

| Regel | Wijziging |
|---|---|
| 318–360 | `ANTWOORDSCHEMA` is het /4-schema: gesloten objecten, gesorteerde enums, 0 optionele velden en 3 unies (onder de grens van ≤24/≤16), met verdict als laatste veld. `ANTWOORDSCHEMA_SHA256` is vastgepind op `d3ad029e…`. De /3-hulpdelen `_grondvariant`/`_GRONDSCHEMA` zijn verwijderd. |

**Grondbronnen**

| Regel | Wijziging |
|---|---|
| 542–568 | `_grondbronmap` en het publieke `grondbronnen(invoer)` geven de vaste volgorde: bedoeling (alleen als die bekend is), context per index en `bron/<id>`. Begrip en kern zijn geen grondbron. |

**Controles en beslisregel**

| Regel | Wijziging |
|---|---|
| 1034–1054 | `_controleer_structuur_v4`: gesloten vorm, enums en types. |
| 1056–1092 | `_met_posities_v4`: het passagecitaat staat letterlijk en uniek in de kern; daarna volgen per bronfunctie deze controles, in deze volgorde:<br>1. onbekende sleutel → `invalid_citation/grond_niet_herleidbaar`;<br>2. citaatplicht per functie → `invalid_output`;<br>3. letterlijk en uniek in de brontekst, met posities;<br>4. volledig en zonder dubbelingen → `invalid_output`. |
| 1094–1114 | `_controleer_samenhang_v4`: het eigen verdict hangt samen zoals onder /3, zonder de passagefunctie-eisen. Buiten `not_applicable` is minstens één passage vereist (ontwerp §2.2.3). |
| 1117–1130 | `_Afgeleid`. |
| 1132–1182 | `_beoordeel_passage`, de mechanische beslisregel:<br>1. **Stap 1:** `instruction` → gebrek.<br>2. **Stap 2:** een conflict tussen B en G/N → review, tenzij de bedoeling G/N is (1B, 6A).<br>3. **Stap 3:** B → beschrijvend. G/N met een tweede signaal → gebrek, zonder tweede signaal → review (3A). Een tweede signaal is: kernvorm obligation/discretion, G én N samen (6A), of bedoeling G/N. Alleen O → review.<br>4. **Stap 4:** alles zwijgt → de kernvorm beslist. Beschrijvend zonder bedoeling → review (5A); discretion zonder bedoeling → `discretie_zonder_bedoeling` (besluit 12).<br>De grondbronnen worden in vaste volgorde gelezen, niet in de modelvolgorde. |
| 1185–1263 | `_grond_v3`, `_reden_v4` (4A: bronnen en citaten in de reden), `_Uitkomst`, `_vn_melding` en `_o_melding`. |
| 1266–1366 | `_leid_af`. Over de passages gaat gebrek vóór review vóór pass, en pass vereist dekking `complete`. Bij een fail met een reviewpassage krijgt de melding een open punt en één vaste vraag. Actor `human`: het eigen verdict blijft de status, met een consistentie-eis tegen de afleiding. |
| 1369–1390 | `_zonder_afleiding_v4`: replay terug naar de modelvorm. |

**Document en replay**

| Regel | Wijziging |
|---|---|
| 1395–1415 | Docstring van `Beoordelingsdocument` over `omzetting` onder /3 en /4. |
| 1541–1569 | `_beoordeel`, tak /4: `oordeel["dienst"] = {afleiding, modelstatus, passages}`. `omzetting = afleiding` alleen als de actor `ai` is en de status ≠ modelstatus. De /3-dienstregel hangt nu aan `_CONTRACTVERSIE_V3` (r.1583). |
| 1627–1670 | `_herleidbaar`/replay: een /4-document wordt via `_zonder_afleiding_v4` opnieuw afgeleid. /1–/3 blijven volgens hun eigen versie controleerbaar en historisch. |

### `src/services/validation/int02_assessment_service.py` (+~150/−~65)

| Regel | Wijziging |
|---|---|
| 1–40 | Docstring naar /4 en /5. |
| 106–126 | Imports `BRONFUNCTIES`, `KERNVORMEN` en `grondbronnen` (`FUNCTIES` vervalt). |
| 157–159 | `PROMPT_VERSION = "def835-int02-prompt/5"`. |
| 356–423 | `_KERNVORMBETEKENIS` (r.356), `_BRONFUNCTIEBETEKENIS` (r.382) en `_betekenis()` (r.421), met casusvrije betekenisteksten per enumwaarde. |
| 425–558 | `_systeemprompt`, versie /5:<br>- de invoer noemt `grondbronnen` (r.443–450), met het sleutelformaat (r.456–462);<br>- de fail-aanwijzing is ongewijzigd (r.470–481);<br>- een citaataanwijzing voor passage- en bronfunctiecitaten (r.482–490) en een bronnenaanwijzing (r.491–496);<br>- "Antwoord met … in deze volgorde": passages → kernvorm → bronfuncties (per sleutel, in de volgorde van `grondbronnen`) → function/quote → reason → question → uncertainty → coverage → scope_reason → verdict als laatste (r.498–538);<br>- "Samenhang van je eigen verdict" (r.540–556), zonder functievoorwaarden. |
| 561–570 | `bouw_int02_prompt`: de dataprompt is `{"invoer": …, "grondbronnen": [...]}` (r.568). |

### `scripts/analysis/def835_int02_modelproef.py` (+2/−1)

| Regel | Wijziging |
|---|---|
| 307–314 | Bij `FASECRITERIA["ontwikkeling"]` staat `"max_false_pass": 0` (r.312; was `None`), met commentaar dat verwijst naar besluit 16. Regressie (r.303) en hold-out (r.320) waren al 0. |

~~Schema, promptversie en identiteit volgen automatisch via de imports (`ANTWOORDSCHEMA`, `PROMPT_VERSION` en `CONTRACTVERSIE`).~~

**Correctie (Codex-review P2a, 07-10-2026): deze bewering klopte niet.** Schemahash en promptversie volgden de imports wel, maar `CONTRACTVERSIE` stond niet in de runner-identiteit. De contractversie was alleen indirect gebonden, via de bestandshash van `contract.py` in `bestanden`. Sinds het herstel staat `contractversie` expliciet in de identiteit (`def835_int02_modelproef.py:1181`), en een test toetst de volledige combinatie: contract /4, prompt /5 en schemahash. Zie `uitvoeringsverslag-claude-v2.md` §1.

### Documenten

- `o2/besluit-chris-promptcorrectie-en-v3-v1.md`, r.244 en verder: **Besluit 16**. Het bevat:
  - de uitslag van v7 fase 2: 18/24, 0/6 review, vijf onterechte passes (G042, G045, G060, G070, G076) en één fail (G047);
  - keuze A;
  - de 7 keuzes letterlijk;
  - `max_false_pass` = 0 voor ontwikkeling;
  - de normatieve verschuivingen expliciet.
- `goldset-voorbereiding/bronfuncties-ontwerp-v1.md`, bovenaan: "Status: keuzes Chris 07-10 vastgelegd in besluit 16".

### Tests en fixtures

| Bestand | Wat |
|---|---|
| `tests/fixtures/def835_int02_v4.py` (nieuw) | Bouwstenen voor /4: `grondbronnen`, `bronfuncties`, `passage`, `uitvoer` en `respons_voor_status`. Daarnaast `naar_v4`, die een /3-respons van de ongewijzigde ontwerpgevallen-fixture omzet. Die fixture is manifestinvoer en blijft daarom ongewijzigd. |
| `tests/unit/domain/test_def835_int02_bronfuncties.py` (nieuw, 132 tests) | Secties A–G: versie en grondbronnen; structuur en citaten; elke beslisregeltak; 1B/3A/5A/6A positief en negatief; 2A-omzettingen in alle zes richtingen (inclusief fail→pass); actor mens; 4A vaste vragen; manipulatie bij hercontrole (8 varianten → error); migratie /3→/4 historisch. |
| `tests/unit/domain/test_def835_int02_papertest.py` (nieuw, 86 tests) | Paper test op de 27 gevallen: invoer uit `kwalificatieproef-v7/regressie-bundel.json` (C105/C107/C112) en `ontwikkeling-v1.json` (24 G-gevallen). Elk geval draait met drie modelverdicten (label/pass/fail) en moet het label en het ontwerppad opleveren. Daarnaast diagnostische gevoeligheidstests: 1B beschermt G036/G047, 5A beschermt C107, en G045 met B1 C blijft een bekend restrisico. |
| `domain/test_def835_int02_{contract,citaatposities,migratie,dienstregel}.py` | Deze tests toetsen de regels van /3 en zijn daarom via een autouse-fixture aan `CONTRACTVERSIE = /3` gebonden. Dienstregel heeft er één test bij: de ruwe v5-tekst onder /4 geeft `invalid_output`. |
| `validation/test_def835_int02_schemaroute.py` | Bevat:<br>- het letterlijke /4-schema;<br>- de grenzen;<br>- de pin;<br>- de vorige hashes;<br>- 8 seeds;<br>- een gelijkheidsmatrix van schema en contract voor bronfunctie en kernvorm;<br>- de v6-respons van C105, die ongeldig is. |
| `services/prompts/test_def835_int02_prompt.py` | Prompt /5 (velden, volgorde, betekenissen, aanwijzingen) en een n-gramtoets: de prompt bevat geen casustekst uit `ontwikkeling-v1.json`. |
| `validation/test_def835_int02_modelproef.py` | Runner op /4 en /5, plus 2 nieuwe tests: `max_false_pass` is 0 in elke fase, en een onterechte pass in ontwikkeling telt als reden. |
| `validation/test_def835_int02_{assessment_service,evaluator,modular,variatiemeting}.py`, `orchestrators/test_def835_int02_wrappers.py` | Fake-responsen omgezet naar /4 (`_volledig`, `respons_voor_status`, `naar_v4`). De payload bevat `grondbronnen`, de verwachtingen gaan uit van prompt /5 en contract /4, en het oordeel bevat het blok `dienst`. |

## 3. Keuzes en interpretaties tijdens de bouw

1. **Omzettingscode = regelcode.** `omzetting` is de code van de beslissende regel, bijvoorbeeld `bronvoorschrift_niet_overgenomen` of `bronnen_beschrijvend`. Het modelverdict staat in het oordeel en `dienst.modelstatus` legt de status van het modelverdict vast. Een hercontrole leidt alles opnieuw af; elke manipulatie wordt `error`.
2. **Actor mens.** "De dienst beslist" (2A) geldt alleen voor actor `ai`. Bij een mens blijft het eigen verdict de status. Het verdict moet dan wel samenhangen met de afgeleide passages, net als de samenhangseis van /3; anders volgt `invalid_output`.
3. **Fail met tegelijk een reviewpassage.** Het document wordt `fail`. De melding noemt het open punt met één vaste vraag (`MELDING_OPEN_PUNT`), zodat de reviewgrond niet verloren gaat.
4. **Vaste vragen (4A).** `VRAAG_FUNCTIE` voor alle functietwijfel en `VRAAG_DEKKING` voor onvolledige dekking. Beide zijn invoeronafhankelijk; de casusgegevens staan in de reden.
5. **Tweede signaal.** Twee G-bronnen zonder ander signaal geven review, letterlijk volgens het ontwerp: "G én N" telt wel als tweede signaal, "G én G" niet.
6. **Volgorde van bronfuncties.** Die wordt niet afgedwongen (het schema kan geen permutatie eisen). De afleiding leest altijd in de vaste volgorde van `grondbronnen`; een test borgt dat.
7. **Minstens één passage.** Buiten `not_applicable` is minstens één passage vereist (ontwerp §2.2.3). Onder /3 mocht `insufficient_information` zonder passages; de oude testrespons in `test_def835_int02_modular.py` heeft daarom één passage gekregen.
8. **De ontwerpgevallen-fixture blijft ongewijzigd** (manifestinvoer). Tests die haar gebruiken, zetten de /3-respons met `naar_v4` om naar /4.
9. **/3-domeintests via monkeypatch.** In plaats van ongeveer 300 bestaande regels te herschrijven, draaien die vier bestanden met `CONTRACTVERSIE = /3`. Daarmee blijft ook bewezen dat /3-documenten historisch controleerbaar zijn.

## 4. Testaantallen

| Meting | Uitkomst | Log |
|---|---|---|
| Nulmeting vóór de bouw | groen | `nulmeting.log` |
| Rood (na de nieuwe tests, vóór de implementatie) | 312 gefaald, 220 geslaagd | `rood.log` |
| Nieuwe en gewijzigde tests (14 bestanden) | 1191 geslaagd | `groen-0-gewijzigde-tests.log` |
| `-k "def835 or int02" tests/unit` | 1251 geslaagd, 11 overgeslagen (DEF771_SKILLS_ROOT) | `groen-1-def835-int02.log` |
| INT-03 / ESS-03 (`-k "int03 or ess03"`) | 786 geslaagd | `groen-2-int03-ess03.log` |
| ruff (venv) | schoon | `groen-3-ruff.log` |
| black --check | schoon (261 bestanden) | `groen-4-black.log` |
| Mutatiecontrole | 12/12 gedood, nulmeting 358/358 | `mutatie.log`, `mutatie/resultaten/*.xml` |
| Volledige unit-suite (`-n auto`, extra) | 9048 geslaagd, 3 gefaald, los van deze bouw (zie §5) | — |

## 5. Open punten

1. **Een "decisive"-onzekerheid van het model blokkeert een afgeleide pass niet.** Onder 2A beslist de dienst. Als alle bronnen "kenmerk" zeggen maar het model `uncertainty: decisive` meldt, wordt het toch `pass`, mits de dekking `complete` is. Dat volgt letterlijk uit 2A, maar staat op gespannen voet met de T-tekst (“bij twijfel review”). **Voorleggen aan Chris.** *Besloten: besluit 17, optie A (07-10-2026); uitgevoerd, zie `uitvoeringsverslag-claude-v2.md`.*
2. **G045-restrisico.** Als het model B1 als `criterion` markeert, blijft G045 een onterechte pass; dat is per constructie zo. Dit is bekend uit ontwerp §3.2 en wordt zichtbaar getest. Alleen het modelgedrag in v8 kan dit oplossen.
3. **Smalle borging van twee voorwaarden.** De dekkingseis en de volgorde "gebrek vóór review" worden elk door precies één test gevangen.
4. **Pre-commit-ruff v0.16.5 niet gedraaid.** `uvx` vroeg om toestemming. Venv-ruff en black zijn schoon. ISC001 (impliciete concatenatie op één regel) is wel gevonden en opgelost.
5. **Volledige unit-suite: drie fouten zonder verband met deze bouw.**
   - `test_def835_int02_modelproef.py::test_f3_…afronding_onvolledig` faalt alleen onder xdist en is serieel groen.
   - De 2× `test_performance_tracker.py` falen door een `OfflineGateError` op `data/definities.db` in deze werkboom; ze falen ook geïsoleerd en hun bestanden zijn niet gewijzigd.
6. **Afgerond meetscript `variatiemeting-c107-v1/variatiemeting.py`.** Ongewijzigd gelaten. Het registreert onder /4 geen `kernvorm` of `bronfuncties` (`function` = None). De test legt die beperking vast. Voor een nieuwe variatiemeting is een v2 van het script nodig.
7. **Commentaar dat nog /3 noemt.** `decision_rule_assessment.py`, `services/validation/interfaces.py` en `toetsregels/runtime_contract.py` noemen in commentaar of docstring nog /3. Ik heb ze niet aangepast om de scope (O1/INT-03/ESS-03-raakvlak) klein te houden.
8. **Contractdocument v4.** `docs/architectuur/contracts/int02_assessment_contract_v4.md` is nog niet geschreven.
9. **Hulpbestanden niet verwijderd.** In `bronfuncties-v1/hulp/` staan `inventaris_ontwikkeling.py` (niet uitgevoerd) en `schemaroute-sectie3-4.txt` (tijdelijk). Ik heb ze niet verwijderd: verwijderen gebeurt alleen op expliciete opdracht van Chris, en de eerdere poging werd door de beveiligingshook geblokkeerd.
10. **Hostnaam in junit-XML.** Het pytest-standaardveld in `mutatie/resultaten/*.xml` bevat de hostnaam van de meetmachine.

## 6. Gevolgen voor manifest v8

**Moet opnieuw worden vastgelegd** (de dry-run van de runner berekent ze):

- `contractversie` = `def835-int02-assessment/4`;
- `promptversie` = `def835-int02-prompt/5`;
- de hashes van `contract.py`, `int02_assessment_service.py` en de runner, de systeemprompt en de payload per geval.

Deze hashes zijn hier niet berekend: losse hash- en scriptcommando's vroegen om toestemming.

**Schema:** de pin is `d3ad029e24b6b96242f4730686d3a4ebfebd9f46993607e41016761bc7fce715`. De vorige pins staan als historisch in `VORIGE_SCHEMA_SHA256` (schemaroute-test).

**Payload:** het gebruikersbericht bevat nu `grondbronnen`, en de systeemprompt is nieuw (/5). Model, limieten en sampling zijn bytegelijk aan de vastgelegde v5-payload; de variatiemetingtest bewijst dat voor C107. Ten opzichte van v7 is dat niet apart getoetst.

**Criteria:** voor ontwikkeling is `max_false_pass` 0. Regressie en hold-out blijven 0.

**Ongewijzigd:**

- de gevallen zelf (gevallenhash `af1ab46c…6953`);
- de goldset-freeze;
- de ontwerpgevallen-fixture.

**Status van het bewijs (7A):** fase 1 en 2 van v8 zijn een consistentietoets. Het ontwerp is op die gevallen afgestemd (paper test 27/27). Alleen de hold-out, met apart akkoord, is onafhankelijk bewijs.

## 7. Kosten- en tokenschatting (volgens ontwerp §4.3)

| Post | Schatting |
|---|---|
| Extra invoertokens per call (systeemprompt /5 + grondbronnen) | +700 tot +900 |
| Extra uitvoertokens per call (kernvorm + bronfuncties met citaten) | +150 tot +350 |
| Kosten per call (Opus 5, conservatief) | ≈ US$ 0,045–0,050 |
| v8 fase 1 + 2 (43 calls) | ≈ US$ 2,0–2,2 |

Dit zijn schattingen op basis van het ontwerp; er is niets gemeten (geen live calls). `max_uitvoertokens` 6000 in het proefprofiel laat ruim marge. Het werkelijke verbruik volgt uit de `usage`-velden van de v8-run.

## 8. Wat níet is gedaan

- Geen commit en geen push.
- Geen live calls.
- `.env` niet gelezen.
- Geen hold-outgeval gelezen of gebruikt: de paper test leest alleen `ontwikkeling-v1.json` en de regressiebundel van v7, en de n-gramtoets alleen `ontwikkeling-v1.json`.
- ESS-03, INT-03, generatie en O1 functioneel ongemoeid; hun tests zijn groen.
