# Uitvoeringsverslag v2: herstel na Codex-review en besluit 17

DEF-835 · INT-02 O2 · 07-10-2026 · Claude. Werkboom op branch `feature/DEF-835-int02-o2`, HEAD `5315fa8e0`.

**Alles staat nog ongecommit.** Er zijn geen API- of netwerkcalls gedaan, `.env` is niet gelezen en er zijn geen hold-outbestanden geopend. Er staat geen `print()` in `src/`.

Dit verslag volgt op `uitvoeringsverslag-claude-v1.md`. Codex beoordeelde de bouw read-only als "nog niet commitbaar". Chris heeft daarna open punt 1 besloten (besluit 17).

## Herstel na Codex-review en besluit 17

### 1. Per punt: wat er veranderd is

**Besluit 17 (optie A): bij beslissende onzekerheid van het model geen afgeleide pass**

Codewijzigingen:
- `src/domain/int02/contract.py:215`: nieuwe regelcode `REGEL_MODEL_BESLISSEND_ONZEKER = "model_beslissend_onzeker"`.
- `contract.py:232`: de vaste vraag `VRAAG_FUNCTIE` (analoog aan 4A).
- `contract.py:255`: `REDEN_MODEL_BESLISSEND_ONZEKER`, met de grond en de dragende passage.
- `contract.py:1383–1395` in `_leid_af`, vlak vóór de laatste pass-tak: is `uncertainty == "decisive"`, dan volgt `review_required` / `insufficient_information` met O-melding en vaste vraag, afleiding `model_beslissend_onzeker`.

Hoe de regel werkt:
- Een afgeleid gebrek en een eigen reviewgrond (conflict, bronvoorschrift, open bron, onvolledige dekking) gaan voor.
- `omzetting` volgt de bestaande 2A-regel. Ze wordt `model_beslissend_onzeker` als de status afwijkt van het modelverdict: een model-`fail` met twijfel en een kenmerkgrond. Bij een model-`insufficient_information` is de status gelijk, dus is er geen omzetting.
- Het modeloordeel blijft ongewijzigd in `oordeel_json`: verdict, `uncertainty` en de eigen `question`.
- De docstrings van de module (r.26–31) en van `_leid_af` (r.1291–1296) zijn bijgewerkt.

Schema en prompt:
- **Het schema is niet gewijzigd.** `uncertainty` stond er al in, dus de pin blijft `d3ad029e24b6b96242f4730686d3a4ebfebd9f46993607e41016761bc7fce715`.
- **De prompttekst is niet gewijzigd.** De regel zit alleen in de dienst; het model hoeft niets anders te doen.

Tests in `tests/unit/domain/test_def835_int02_bronfuncties.py`:
- De 2A-case "review-naar-pass" (oud r.903) is uit de parametrisatie gehaald. In de plaats komt `test_17_review_naar_pass_wordt_review_met_vaste_vraag` (r.1177): de uitkomst is nu review, zonder omzetting, met de vaste vraag. Het modeloordeel en de eigen vraag blijven zichtbaar.
- Nieuwe sectie H (r.1167–1328):
  - decisive plus kenmerkgrond, bij model-`fail` → review met omzetting (3 varianten: één kenmerkbron, alle bronnen kenmerk, alleen de kern; r.1217);
  - decisive plus een aantoonbaar gebrek → fail (4 varianten, r.1243), en gebrek naast een kenmerkpassage (r.1255);
  - `none` en `non_decisive` plus kenmerk → pass (r.1279);
  - een eigen reviewgrond gaat voor de onzekerheidsregel (r.1289);
  - hercontrole en manipulatie: een vervalste status, of `uncertainty` die naar `none` is gezet, geeft `error` (r.1307).

Vastgelegd:
- `o2/besluit-chris-promptcorrectie-en-v3-v1.md`, "Besluit 17". Daarin staat de Codex-bevinding: 27/27 en de v7-passes blijven gelijk. Besluit 17 kan wel tot 13 passes raken als het model twijfel meldt: C112, G007, G011, G015, G019, G021, G027, G030, G037, G039, G041, G046 en G055.

Mutatiecontrole:
- `mutatie/mutatie_plugin.py`: nieuwe mutant `onzekerheid_genegeerd_17`. Vijf tests vangen hem (`herstel-mutatie.log`).

**P1: een lege of alleen-witruimtebron kan geen betekenisgrond zijn**

- `contract.py:1092–1095`, in de /4-citaatroute (`_met_posities_v4`): bij elke functie behalve `not_addressed` moet de brontekst gevuld zijn (`_gevuld(bronnen[sleutel][2])`). Anders volgt `invalid_citation` / `grond_niet_herleidbaar`, zoals `_grondbron` onder /3.
- `contract.py:1101–1103`: een citaat van alleen witruimte geeft `invalid_citation` / `leeg`, ook in een gevulde bron.
- **De historische invoerconstructors zijn ongewijzigd.** Een witruimtebron mag nog steeds in de invoer staan en mag zwijgen; de volledigheidseis per grondbron blijft gelden.
- De docstrings van de module (r.48–53) en van `_met_posities_v4` zijn bijgewerkt.
- Tests, sectie I (r.1331–1398):
  - de reproductie van Codex: bedoeling onbekend, `descriptive_act`, context zwijgt, B1 = " " als `criterion` met citaat " " gaf eerst pass en geeft nu `error` (r.1338);
  - lege bronnen ("", " ", "\t\n ") met vier functies (r.1356);
  - een lege bron mag zwijgen (r.1370);
  - een citaat van alleen witruimte in een gevulde bron (r.1383).

**P2a: contractversie expliciet in de runner-identiteit**

- `scripts/analysis/def835_int02_modelproef.py:1144,1181`: `"contractversie": CONTRACTVERSIE` in `_ketenidentiteit`. Daarmee staat de versie in beide manifestsoorten, de driecasusmodus en de kwalificatie.
- Tests in `tests/unit/validation/test_def835_int02_modelproef.py`:
  - de combinatie contract /4 + prompt /5 + schemahash `d3ad029e…` in beide identiteiten (r.1758);
  - de identiteit volgt de actieve contractversie, ook als alleen die verandert (r.1776);
  - de identiteitsveldenset van de driecasusmodus kent nu `contractversie` (r.968).
- De onjuiste bewering in v1 ("volgt automatisch") is daar doorgestreept en gecorrigeerd (§1 en §2).

**P2b: tellingen per afleidingsregel en per omzettingsrichting (ontwerp §4.4)**

Runner:
- `def835_int02_modelproef.py:1730–1756` (`_evalueer`): per geval `afleiding`, `modelstatus`, `omzetting` en `omzettingsrichting` (bijvoorbeeld `fail→pass`, `fail→review_required`). Een foutdocument krijgt overal `None`.
- r.1759–1792: `BEWIJSSTATUS` en `BEWIJSTOELICHTING` (7A), plus `_telling` en `_afleidingen`.
- r.1881: `_beoordeel_fase` geeft daarnaast:
  - `afleidingen`: een telling per regel;
  - `omzettingen`: het totaal, per richting en per regel;
  - `bewijsstatus`: `consistentietoets_7a` voor regressie en ontwikkeling, `onafhankelijk_bewijs` voor de hold-out;
  - `bewijstoelichting`.
- r.2255–2265: de CLI-logregel noemt de bewijsstatus en de omzettingen.
- r.54: `import collections`.

Tests (r.1816–1920):
- vastlegging per geval, ook voor een foutdocument;
- de fasetelling met `model_beslissend_onzeker` erin;
- een lege telling;
- de bewijsstatus per fase;
- een integrale kwalificatierun waarin een omgezet pass-geval als `fail→pass` in de uitslag van ontwikkeling landt.

**P3: documentatie en commentaar**

- Nieuw: `docs/architectuur/contracts/int02_assessment_contract_v4.md`, in de stijl van v3. Het bevat:
  - het verschil met /3;
  - de modeluitvoer en de controlevolgorde, inclusief P1;
  - de beslisregel als tabel, met besluit 17;
  - vaste vragen en redenen, statusmapping, replay en runnerrapportage;
  - bewijsgrenzen, waaronder de 13 passes en G045.
- `int02_assessment_contract_v2.md` en `_v3.md`: alleen een verwijsregel "Historisch. Opgevolgd door …" onder de titel; de inhoud is ongewijzigd.
- Commentaar dat nog /3 noemde, is bijgewerkt (geen code):
  - `src/services/validation/evaluators/decision_rule_assessment.py:5–8`;
  - `src/services/validation/interfaces.py:80–81` en `:288`;
  - `src/toetsregels/runtime_contract.py:124`.

### 2. Testuitkomsten

| Meting | Uitkomst | Log |
|---|---|---|
| Rood, vóór het herstel | 29 gefaald, 335 geslaagd (18 in bronfuncties, 11 in modelproef) | `herstel-rood.log` |
| Gericht (bronfuncties, papertest, modelproef, schemaroute, dienst) | 643 geslaagd | `herstel-groen-0-gericht.log` |
| `-k "def835 or int02" tests/unit` | 1292 geslaagd, 11 overgeslagen (DEF771_SKILLS_ROOT) | `herstel-groen-1-def835-int02.log` |
| INT-03 / ESS-03 | 786 geslaagd | `herstel-groen-2-int03-ess03.log` |
| ruff / black --check | schoon / 264 bestanden ongewijzigd | `herstel-ruff.log`, `herstel-black.log` |
| Papieren toets | 86 geslaagd, waaronder 27/27 met 6/6 review | `herstel-papertest.log` |
| Mutatiecontrole | 13/13 gedood, nulmeting 388/388 | `herstel-mutatie.log`, `mutatie/resultaten/herstel-*.xml` |

### 3. Afwijkingen en beperkingen in de uitvoering

- **Rechten.** In deze sessie werden shellvariabelen en een PYTHONPATH-prefix geweigerd. De mutatieruns starten daarom vanuit de mutatiemap, met `--rootdir` en absolute paden. Eén werkmap-afhankelijke containertest is daarbij gedeselecteerd; vanuit de werkboom is die test groen.
- `ruff` direct aanroepen werd soms geweigerd; `python -m ruff` werkte wel.
- **Niet gedraaid:**
  - pre-commit-ruff v0.16.5 (uvx vraagt toestemming);
  - de volledige unit-suite (`-m unit`) na het herstel. In v1 had die drie fouten zonder verband met deze bouw.
- **Hulpbestanden blijven staan** in `bronfuncties-v1/hulp/`; er is niets verwijderd.

### 4. Open punten

1. **Smalle borging.** De volgorde "gebrek vóór review" (mutant `review_voor_gebrek`) wordt nog steeds door maar één test gevangen.
2. **G045-restrisico.** Ongewijzigd (zie het contractdocument v4, onder "Bewijsgrenzen").
3. **Besluit 17 kan tot 13 passes raken** als het model twijfel meldt. Of en hoe vaak dat gebeurt, blijkt pas in v8. In de runnertelling is dat zichtbaar als `afleidingen.model_beslissend_onzeker` en bij een model-`fail` als omzetting `fail→review_required`.
4. **De variatiemeting** (`variatiemeting-c107-v1`) registreert onder /4 nog steeds geen kernvorm of bronfuncties (zie v1).

### 5. Wat openstaat voor manifest v8

**Nieuwe identiteit.**
- `contractversie` = `def835-int02-assessment/4` staat nu expliciet in de identiteit.
- `profiel.promptversie` = `def835-int02-prompt/5`.
- `router.antwoordschema_sha256` = `d3ad029e…` (ongewijzigd na besluit 17).

**Nieuwe hashes.** Opnieuw te berekenen in de offline dry-run van de runner:
- de bestandshashes van `contract.py` en de runner (die zijn door dit herstel gewijzigd);
- de systeemprompt- en payloadhashes. Die horen gelijk te blijven aan die van de eerste /4-bouw, omdat de prompt niet is gewijzigd, maar ze zijn hier niet berekend.

**Uitslagvorm.** De uitslag per fase bevat nu `afleidingen`, `omzettingen` en `bewijsstatus`. Fase 1 en 2 zijn een consistentietoets (7A).

**Criteria.** `max_false_pass` is 0 in alle fasen. De gevallen zijn ongewijzigd (`af1ab46c…6953`).

**Volgorde.**
1. Een nieuwe Codex-review van de herstelde diff.
2. Commit.
3. Manifest v8 offline.
4. Akkoord v8 van Chris.
5. Fase 1.
6. Fase 2, alleen na een apart akkoord.
7. De hold-out, met een eigen akkoord.

## Herstel na herreview

07/08-10-2026 · Claude. Codex keurde in de herreview besluit 17, P2a en P2b goed. Commitbaar was het nog niet, door een rest van P1: inhoudsloze tekst kon nog een pass dragen. Deze ronde herstelt dat en neemt P3 mee. Alles staat nog ongecommit en is offline gedaan. Er is geen `.env` gelezen, geen hold-outbestand geopend en geen prompttekst gewijzigd.

### 1. P1-rest: alleen betekenisdragende tekst draagt een oordeel

**Het probleem.** Codex gaf twee reproducties:
- (a) Een grondcitaat "." doorstond `_gevuld`. Met `criterion` op alleen die punt werd het pass, waar het zonder grond `review_required` was (5A).
- (b) Een unieke tab als passagecitaat, met `no_act` en zwijgende bronnen, gaf pass. `_positie` controleert alleen `bool(citaat)`.

Beide valse passes bleven bij hercontrole geldig.

**Het herstel** (`src/domain/int02/contract.py`):
- r.435: één hulpfunctie, `_betekenisdragend`: minstens één teken waarvoor `str.isalnum()` waar is (Unicode-bewust).
- r.1097: het passagecitaat wordt eerst hierop getoetst, vóór `_positie`. Zonder letter of cijfer volgt `invalid_citation` / `leeg`.
- r.1110: een grondbron (bron, bedoeling of contextitem) zonder letter of cijfer draagt geen functie: `invalid_citation` / `grond_niet_herleidbaar`. Zwijgen mag wel.
- r.1118: een grondcitaat zonder letter of cijfer geeft `invalid_citation` / `leeg`.
- Er zijn geen nieuwe foutcodes. De docstrings van de module (r.47–57) en van `_met_posities_v4` (r.1083–1093) zijn bijgewerkt.
- Ongemoeid blijven:
  - de invoerconstructors (`_gevuld`, r.429);
  - de /3-route (`_grondbron`, `_met_posities`, `_discretie_zonder_bedoeling`);
  - de historische routes /1–/2.

**Bijvangst: stap 4 (r.1213).** Een bedoeling "..." komt door de constructor en telde in stap 4 als bekend (`invoer.bedoeling is None` was onwaar). Daardoor gaf een `descriptive_act` zonder grond een pass (`alleen_kern`), waar 5A review vraagt. Een `discretion_form` gaf een fail, waar besluit 12 review vraagt. Dat is dezelfde fout als (a), via een andere weg; eerst rood aangetoond in `herstel2-rood-3-bedoeling.log`. Nu geldt: `onbekend = not _betekenisdragend(invoer.bedoeling)`. **Dit gaat iets verder dan de letterlijke opdracht. Chris kan het terugdraaien als het niet gewenst is.** Het raakt alleen de /4-route.

**Tests** (`tests/unit/domain/test_def835_int02_bronfuncties.py`, sectie J vanaf r.1425):
- Beide reproducties van Codex: r.1439 (grondcitaat ".") en r.1451 (tab als passage). Beide geven `error` / `invalid_citation` / `leeg`.
- Inhoudsloze varianten: "...", "—", ".", " - ", alleen tabs, alleen newlines, "?!" en "-–—":
  - als bron, als bedoeling en als contextitem → `grond_niet_herleidbaar`;
  - als grondcitaat in een gevulde bron en als passagecitaat in de kern → `leeg`;
  - een inhoudsloze bron mag wel zwijgen.
- Stap 4 met een inhoudsloze bedoeling: r.1501.
- Een geldige niet-ASCII-letter: "é" als passage, bron en citaat geeft pass `bronnen_beschrijvend`, en een cijfer "7" ook. De helpertest dekt é, 7, a, ß, 日 en ٣ (ook omringd door "—…"), en negatief "", " ", "...", "—", "\t\n", "?!", "_", `None` en `7` (int).
- Hercontrole van een gemanipuleerd /4-document (r.1580), voor beide reproducties:
  1. bouw met de oude, te ruime controle een volledig consistent pass-document;
  2. `toets_actualiteit` met de echte code geeft `error`.
- Mutanten (mutatie/mutatie_plugin.py r.101–117):
  - `betekenisdragend_weg_p1rest` valt terug op `_gevuld`;
  - `passagecitaat_ongetoetst_p1rest` haalt de passagetoets weg;
  - `inhoudsloze_bedoeling_bekend_p1rest` herstelt de oude stap-4-regel.

  Alle drie worden gedood: er vallen 32, 7 en 5 tests (zie `herstel2-mutatie.log`). Bij de eerste mutant zijn 28 van de 32 gedragstests; de andere 4 zijn helpertests.

### 2. P3

- **Contractdocument v4, replay** (`docs/architectuur/contracts/int02_assessment_contract_v4.md:280–292`). De oude tekst zei dat elke gewijzigde onzekerheid `error` geeft; dat klopte niet. Nu staat er:
  - replay toetst samenhang met de bewaarde modelvorm, niet de echtheid van het modelantwoord (dat hoort bij de opslaglaag, DEF-626);
  - een gewijzigde onzekerheid geeft alleen `error` als de afgeleide uitkomst erdoor verandert;
  - met drie voorbeelden. De twee van Codex (`none → non_decisive` op een pass, `decisive → none` op een kernvoorschrift-fail) staan vast in `test_17_replay_toetst_samenhang_niet_de_echtheid_van_de_onzekerheid` (bronfuncties r.1339) en zijn groen.
- **Contractdocument v4, P1-rest.**
  - Nieuwe sectie "Herreview Codex: P1-rest" (r.77).
  - Controlevolgorde stap 2 en 3 (r.172–177).
  - De replay-alinea noemt nu ook een modelvorm die de /4-controles niet meer doorstaat.
  - Een noot bij stap 4 van de beslisregel (r.221).
- **Exacte pin op de systeemprompt /5**: `3047bb1a34f878e77bd434d668d870f0dfcfb92e3e948ac0caee77af9c2d2b70`.
  - `test_def835_int02_dienstregel.py:97` (constante) en `:763` (assert);
  - `test_def835_int02_schemaroute.py:87` en `:696`;
  - de controle "≠ hash van /3" blijft staan.

  Eerst rood bewezen met een placeholder. Beide routes (direct en via de schemaroute) gaven dezelfde digest.
- **Variatiemeting.** Het afgeronde meetscript `variatiemeting-c107-v1/variatiemeting.py` is niet gewijzigd. **Onder /4 registreert de variatiemeting géén bronfuncties en géén kernvorm.** Het script legt alleen de /3-velden `function` en `ground` vast, en onder /4 is `function` dus `None`. Dat staat vast in `tests/unit/validation/test_def835_int02_variatiemeting.py:357–360`. Een meting met dit script zegt daarom niets over de stabiliteit van kernvorm of bronfuncties.

### 3. Testuitkomsten

| Meting | Uitkomst | Log |
|---|---|---|
| Rood, eerste poging | ongeldig: de helper `_fout` overschaduwde een bestaande helper (91 gefaald) | `herstel2-rood.log` |
| Rood, na hernoemen (`_uitslag`) | 44 gefaald, alle bedoeld: 42 in sectie J, 2 prompt-pins | `herstel2-rood-2.log` |
| Rood, bijvangst stap 4 | 5 gefaald | `herstel2-rood-3-bedoeling.log` |
| Gericht (bronfuncties, papertest, dienstregel, modelproef, schemaroute, dienst) | 759 geslaagd | `herstel2-groen-0-gericht.log` |
| `-k "def835 or int02" tests/unit` | 1353 geslaagd, 11 overgeslagen (DEF771_SKILLS_ROOT) | `herstel2-groen-1-def835-int02.log` |
| INT-03 / ESS-03 | 786 geslaagd (ongewijzigd) | `herstel2-groen-2-int03-ess03.log` |
| ruff / black --check | schoon / 265 bestanden ongewijzigd | `herstel2-ruff.log`, `herstel2-black.log` |
| Papieren toets | 86 geslaagd, waaronder 27/27 met 6/6 review | `herstel2-papertest.log` |
| Mutatiecontrole | 16/16 gedood; nulmeting 447/447, eind-nulmeting 449/449 | `herstel2-mutatie.log`, `mutatie/resultaten/herstel2-*.xml` |

**Hashes:**
- ANTWOORDSCHEMA: `d3ad029e24b6b96242f4730686d3a4ebfebd9f46993607e41016761bc7fce715`, ongewijzigd.
- Systeemprompt /5: `3047bb1a34f878e77bd434d668d870f0dfcfb92e3e948ac0caee77af9c2d2b70`.

### 4. Afwijkingen en beperkingen

- **De `.venv`-symlink in de worktree was verdwenen.** Ik heb niets verwijderd. Alle runs gebruikten daarom de interpreter van de hoofdrepo: `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python`. Dat de worktree-`src` geladen werd, blijkt uit de nieuwe tests (die zonder deze `src` falen) en uit de fragmentcontrole van de mutatieplugin.
- **Mutatieruns.** Ze draaiden zonder env-prefix, vanuit de mutatiemap, met dezelfde deselect als in de vorige ronde.
- **Hulpbestand.** `mutatie/vat_xml_samen.py` is aangemaakt maar niet gebruikt, omdat het starten ervan om toestemming vroeg. Het blijft staan.
- **Niet gedraaid:**
  - pre-commit-ruff v0.16.5;
  - de volledige unit-suite (`-m unit`).
- **De /5-prompthash heeft geen externe referentie;** er is nog geen manifest voor /5. De pin legt de huidige tekst vast, niet of die tekst juist is. De hash hoort in manifest v8 terug te komen.

### 5. Volgende stap

1. Een nieuwe Codex-review van deze diff, met aandacht voor de bijvangst in stap 4.
2. Commit, na akkoord.
3. Manifest v8 offline.

## Herstel na herreview 2

08-10-2026 · Claude. In de tweede herreview keurde Codex de stap-4-wijziging en de P3-punten goed. Er bleef één rest van P1 over: de toets `isalnum()` liet onzichtbare Hangul-fillers en losse cijfers door. Besluit van Chris: **betekenisdragend = minstens één zichtbare letter**. Alles staat nog ongecommit en is offline gedaan. Er is geen `.env` gelezen, geen hold-outbestand geopend en geen prompttekst gewijzigd.

### 1. Wat er veranderd is

**Code** (`src/domain/int02/contract.py`)
- r.85: `import unicodedata`.
- r.443: de benoemde constante `ONZICHTBARE_LETTERS`. De commentaar erboven (r.436–442) legt uit waarom: deze tekens zijn letters (categorie Lo), maar renderen als leeg. Het gaat om:
  - de Hangul-fillers U+115F, U+1160, U+3164 en U+FFA0;
  - de Egyptische hiërogliefen U+13441 (FULL BLANK) en U+13442 (HALF BLANK).

  De tekens staan als codepunt (`chr(0x…)`), omdat ze letterlijk onzichtbaar zijn in de bron.
- r.448: `_zichtbare_letter` = Unicode-categorie L* (Lu, Ll, Lt, Lm, Lo) en niet in de constante. Cijfers (Nd) tellen dus niet.
- r.454–463: `_betekenisdragend` gebruikt nu `_zichtbare_letter`. De vier routes van herstel 1 lopen al via deze helper en zijn niet veranderd: passagecitaat, grondbron, grondcitaat en stap 4.
- De docstrings van de module en van `_met_posities_v4` en drie commentaarregels zeggen nu "zichtbare letter".

**Extra gevonden.** De Unicode-borgingstest vond naast de vier fillers ook U+13441 en U+13442. Mij zijn geen andere letters bekend die leeg renderen. Die borging is naamgebaseerd: ze vindt alleen letters met FILLER of BLANK in hun naam.

**Tests** (`tests/unit/domain/test_def835_int02_bronfuncties.py`, sectie J)
- r.1435–1446: de testlijsten bevatten nu alle zes onzichtbare letters en de cijferreeksen "7", "٣" en "12". Daarmee draaien ze in alle routes mee:
  - bron r.1504;
  - bedoeling als grondbron r.1515;
  - contextitem r.1526;
  - zwijgen mag r.1538;
  - stap 4 r.1547;
  - grondcitaat r.1562;
  - passage r.1574.
- r.1469–1500: de reproducties van Codex. U+1160 als grondcitaat, als passage en als bedoeling, en "7" als enig grondcitaat. Ze geven `leeg` of review, nooit pass.
- **Oude test :1545 vervangen.** "7" uit "Artikel 7." gaf pass en is nu `leeg` (r.1492). Een citaat "artikel 7" blijft geldig (r.1603).
- r.1603: geldige gevallen met een zichtbare letter, met pass `bronnen_beschrijvend`: "artikel 7", een Grieks citaat ("εγγραφή") en een Cyrillisch citaat ("Регистрация"). "é" stond er al.
- r.1616 en r.1632: de helpertests.
  - Positief: é, a, ß, 日, α, Ω, ж, Я, "artikel 7" en filler+letter.
  - Negatief: cijfers, "7.", alle onzichtbare letters, alle onzichtbare letters samen, en filler+cijfer.
- r.1636: de namen en categorie van de twee blanco-hiërogliefen liggen vast.
- r.1644: Unicode-borging. Precies de letters met FILLER of BLANK in hun naam vormen de constante.
- r.1696: hercontrole na consistente manipulatie geeft `error`. Dat geldt nu ook voor een filler als grondcitaat, als passage en als bedoeling, en voor "7" als grondcitaat.

**Mutanten** (`mutatie/mutatie_plugin.py`)
- r.104: het fragment van `betekenisdragend_weg_p1rest` is aangepast.
- r.120: nieuw is `isalnum_p1rest2`, de terugval op `isalnum`. Hij wordt gedood door 70 tests, waaronder alle vier routes, de Codex-reproducties en de hercontrole.
- r.125: nieuw (extra) is `onzichtbaar_vergeten_p1rest2`. Hij wordt gedood door 50 tests.

**Contractdocument v4**
- r.77–96: de sectie "Herreview Codex: P1-rest" beschrijft nu de zichtbare letter, de constante, de cijfers en de vervangen `isalnum`-toets.
- De controlevolgorde (r.183–188), de noot bij stap 4 (r.232) en de replay-alinea (r.294) zeggen nu "zichtbare letter".

### 2. Testuitkomsten

| Meting | Uitkomst | Log |
|---|---|---|
| Rood | 57 gefaald, 238 geslaagd; de geldige letter-gevallen waren al groen | `herstel3-rood.log` |
| Gericht (bronfuncties, papertest, dienstregel, modelproef, schemaroute, dienst) | 847 geslaagd | `herstel3-groen-0-gericht.log` |
| `-k "def835 or int02" tests/unit` | 1441 geslaagd, 11 overgeslagen (DEF771_SKILLS_ROOT) | `herstel3-groen-1-def835-int02.log` |
| INT-03 / ESS-03 | 786 geslaagd | `herstel3-groen-2-int03-ess03.log` |
| ruff / black --check | schoon | `herstel3-ruff.log`, `herstel3-black.log` |
| Papieren toets | 86 geslaagd, waaronder 27/27 met 6/6 review | `herstel3-papertest.log` |
| Mutatiecontrole | 18/18 gedood, nulmeting 537/537 | `herstel3-mutatie.log`, `mutatie/resultaten/herstel3-*.xml` |

**Hashes**, beide ongewijzigd en groen gepind:
- ANTWOORDSCHEMA: `d3ad029e24b6b96242f4730686d3a4ebfebd9f46993607e41016761bc7fce715`.
- Systeemprompt /5: `3047bb1a34f878e77bd434d668d870f0dfcfb92e3e948ac0caee77af9c2d2b70`.

### 3. Afwijkingen en beperkingen

- **De blanco-hiërogliefen kwamen later.** Ze zijn pas na de eerste implementatie toegevoegd, toen de borgingstest rood bleef. Hun eigen rood is dus niet apart gelogd. De mutant `isalnum_p1rest2` laat wel zien dat hun tests falen zonder de nieuwe controle.
- **Onzichtbare tekens.** De Edit-tool zette `\uXXXX`-escapes om in letterlijke onzichtbare tekens. Alles staat nu als `chr(0x…)`, en een bytecontrole vindt geen letterlijke tekens meer.
- **Niet gedraaid:** pre-commit-ruff v0.16.5 en de volledige unit-suite (`-m unit`).

### 4. Volgende stap

1. Een Codex-review van deze ronde.
2. Commit, na akkoord.
3. Manifest v8 offline.
