# INT-02 — intern beoordelingscontract `def835-int02-assessment/4`

Status: intern domeincontract.
- DEF-835 WP1, akkoord 26-09-2026.
- Versie /2 na besluit 9 van Chris (07-10-2026, optie A).
- Versie /3 na besluit 12 (07-10-2026, optie A).
- Versie /4 na besluit 16 (07-10-2026; keuzes 1B, 2A, 3A, 4A, 5A, 6A en 7A) en besluit 17 (07-10-2026, optie A).

Norm: `def771-int02/2` (INT-02, N-breed, besluiten B1–B6).

Implementatie: `src/domain/int02/contract.py`. Prompt: `def835-int02-prompt/5` in `src/services/validation/int02_assessment_service.py`.

Tests:
- `tests/unit/domain/test_def835_int02_bronfuncties.py`: /4, besluit 17 en Codex-review P1;
- `tests/unit/domain/test_def835_int02_papertest.py`: de paper test van het ontwerp;
- `tests/unit/validation/test_def835_int02_schemaroute.py`: schema en pin;
- de /3-regels blijven getoetst in `test_def835_int02_{contract,citaatposities,dienstregel,migratie}.py`.

Ontwerp: `docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/bronfuncties-ontwerp-v1.md`.

Vorige versies, alle historisch en inhoudelijk ongewijzigd:
- `def835-int02-assessment/1` (`int02_assessment_contract_v1.md`);
- `def835-int02-assessment/2` (`int02_assessment_contract_v2.md`);
- `def835-int02-assessment/3` (`int02_assessment_contract_v3.md`).

## Wijziging ten opzichte van /3

Onder /3 koos het model zelf per passage één functie en één grond, en volgde de status uit het eigen verdict. Kwalificatieproef v7 fase 2 liet zien waar dat misgaat:
- vijf onterechte goedkeuringen (G042, G045, G060, G070 en G076);
- een niet herkende review in 6 van de 6 gevallen.

Onder /4 legt de beoordelaar zich eerst per grondbron vast. **De code leidt daarna de functie en de status mechanisch af.**

### Modeluitvoer

Per passage levert de beoordelaar:
- een **`kernvorm`**: de zinsvorm van de passage zelf;
- per **grondbron** precies één **bronfunctie**, met een letterlijk citaat waar dat vereist is.

Het eigen **`verdict`** staat als laatste veld.

### Grondbronnen

`grondbronnen(invoer)` geeft de grondbronnen in vaste volgorde:
1. `bedoeling` (alleen als de bevestigde bedoeling bekend is);
2. `organisatorische_context/<i>`;
3. `juridische_context/<i>`;
4. `wettelijke_basis/<i>`;
5. `bron/<id>`.

Begrip en kern zijn geen grondbron. De dataprompt geeft de lijst mee als `"grondbronnen"`.

### De dienst beslist (2A)

Bij een model (actor `ai`) is de afgeleide status leidend.
- Wijkt die af van het eigen modelverdict, dan staat de beslissende afleidingsregel in `Beoordelingsdocument.omzetting`. Dat kan ook fail → pass zijn.
- Het modelverdict, met de eigen vraag en onzekerheid, blijft onveranderd in het oordeel.

Bij een mens (actor `human`) blijft het eigen verdict de status. Het moet dan samenhangen met de afgeleide passages, anders volgt `invalid_output`.

### Vaste vragen (4A)

Bij een door de dienst afgeleide review is de vraag vast en invoeronafhankelijk. De bronnen en citaten staan in de reden.

### Besluit 17

Een afgeleide pass vraagt ook dat de beoordelaar geen beslissende onzekerheid meldt (`uncertainty` ≠ `decisive`). Anders volgt `review_required`:
- afleiding `model_beslissend_onzeker`;
- de vaste vraag `VRAAG_FUNCTIE`.

Een afgeleid gebrek gaat voor: een fail blijft fail.

### Codex-review P1

Alleen een gevulde grondbron kan een functie dragen. Een lege bron, of een bron met alleen witruimte, mag alleen zwijgen. Een citaat dat alleen uit witruimte bestaat, is `leeg`.

### Herreview Codex: P1-rest

"Gevuld" bleek te ruim: "." of "…" is geen witruimte en kon toch een pass dragen. Daarom geldt onder /4 de eis **betekenisdragend**: minstens één **zichtbare letter** (herreview 2).
- **Letter** = Unicode-categorie L* (Lu, Ll, Lt, Lm, Lo). Dus ook "é", "ß", "α", "ж" en "日".
- **Onzichtbare letters tellen niet** (`ONZICHTBARE_LETTERS` in `contract.py`). Dat zijn letters van categorie Lo die als leeg renderen:
  - de Hangul-fillers U+115F, U+1160, U+3164 en U+FFA0;
  - de Egyptische hiërogliefen U+13441 (FULL BLANK) en U+13442 (HALF BLANK).

  Een test borgt dat dit precies de letters zijn met FILLER of BLANK in hun Unicode-naam. Andere letters die als leeg renderen zijn niet bekend.
- **Cijfers alleen tellen niet.** Een citaat "7" uit "Artikel 7." toont geen functie; "artikel 7" wel.

Herreview 2 verving de eerdere toets (`str.isalnum`). Die liet de onzichtbare fillers en losse cijfers door, en daarmee een pass zonder zichtbare grond.

De eis geldt op vier plaatsen:
- **Passagecitaat.** Zonder zichtbare letter → `invalid_citation` / `leeg`, vóór de positiecontrole in de kern.
- **Grondcitaat.** Zonder zichtbare letter → `invalid_citation` / `leeg`.
- **Grondbron** (bron, bedoeling, contextitem). Zonder zichtbare letter draagt zij geen functie (`invalid_citation` / `grond_niet_herleidbaar`) en mag zij alleen zwijgen.
- **Stap 4.** Een bedoeling zonder zichtbare letter telt als onbekend. Anders zou een bedoeling "..." een beschrijvende kern zonder grond tot pass maken (5A).

De invoerconstructors en de routes /1–/3 houden de witruimtetoets.

### Schema

`ANTWOORDSCHEMA` is nieuw, met pin `d3ad029e24b6b96242f4730686d3a4ebfebd9f46993607e41016761bc7fce715`. Besluit 17 en P1 veranderen het schema niet: `uncertainty` stond er al in.

### Ongewijzigd

Deze onderdelen werken zoals onder /2 en /3:
- de invoer, binding en uitvoeringsmetadata;
- de door de code afgeleide posities (/2);
- het passagecitaat in de kern;
- de samenhang van het eigen verdict (zonder de passagefunctie-eisen);
- de statusset, de meldingssjablonen uit synthese v5 §4 en de replayvolgorde.

### Normatieve verschuivingen (besluit 16 en 17)

- **Eén bronvoorschrift draagt een fail niet meer zelfstandig.** Daarvoor is een tweede signaal nodig (3A). Dat is smaller dan besluit 1 voor bronnen. Een voorschrift in de kern zelf (`instruction`) blijft fail.
- **De dienst kan fail → pass omzetten** als alle bronnen "kenmerk" zeggen. Dat wijkt af van "geen pass-pad" in besluit 12. Besluit 17 begrenst dit: bij beslissende onzekerheid van het model wordt het geen pass.

## Rolverdeling

**De beoordelaar** kiest per relevante passage:
- de passage zelf;
- de kernvorm;
- per grondbron de functie en het citaat;
- de dekking, de onzekerheid en een eigen verdict.

**De code** controleert en leidt af:
- structuur, citaten, volledigheid en herleidbaarheid van de grondbronnen;
- de samenhang van het eigen verdict;
- de afleiding per passage en de status;
- binding en replay.

**De code bewijst geen semantische juistheid en geen volledigheid.** Ook een verkeerde invulling in één richting geeft een "geldige" afleiding. Een voorbeeld is G045: als het model B1 als `criterion` markeert, blijft dat een onterechte pass. De beslisregel kijkt alleen naar kernvorm, bronfuncties, de onzekerheidsclaim, de dekking en of de bedoeling bekend is; niet naar de tekst.

## API (`domain.int02.contract`)

Als onder /3. Nieuw of gewijzigd:

| Onderdeel | Beschrijving |
|---|---|
| `CONTRACTVERSIE` | `def835-int02-assessment/4`. De regels van /1–/3 hangen aan hun vaste versienaam, niet aan deze constante. |
| `KERNVORMEN` | `instruction`, `obligation_form`, `discretion_form`, `descriptive_act`, `no_act`. |
| `BRONFUNCTIES` | De functies van /3 (`criterion`, `derivation`, `actor_prescription`, `discretionary_decision_rule`, `unclear`), plus `not_a_criterion` (6A) en `not_addressed` (de bron zwijgt). |
| `grondbronnen(invoer) -> tuple[str, ...]` | De grondbronsleutels in vaste volgorde (zie hierboven). |
| `ANTWOORDSCHEMA`, `ANTWOORDSCHEMA_SHA256` | Het /4-schema en de pin. |
| `REGEL_*` | De afleidingsregels (zie "Beslisregel"); zij dienen ook als `omzetting`. |
| `VRAAG_FUNCTIE`, `VRAAG_DEKKING` (+ `VRAAG_DISCRETIE_ZONDER_BEDOELING` van /3) | Vaste vragen (4A). |
| `REDEN_*`, `MELDING_OPEN_PUNT` | Redensjablonen voor een afgeleide review en het open punt bij een fail. |

## Gesloten beoordelaarsuitvoer

De uitvoer is een JSON-object met precies deze velden, in deze schemavolgorde:

| Veld | Type / waarden |
|---|---|
| `passages` | lijst van passageobjecten |
| `reason` | niet-lege tekst |
| `question` | `null` of tekst |
| `uncertainty` | `none`, `non_decisive`, `decisive` |
| `coverage` | `complete`, `partial`, `none` |
| `scope_reason` | `null` of tekst |
| `verdict` | `pass`, `fail`, `insufficient_information`, `not_applicable` (als laatste) |

**Passage:** `{quote, kernvorm, bronfuncties}`.
- `quote` komt precies één keer exact voor in de kern. De code leidt `start`/`end` af, zoals onder /2.
- `kernvorm` is de zinsvorm van de passage zelf:
  - `instruction`: een zelfstandig voorschrift aan een actor;
  - `obligation_form`: een plichtvorm;
  - `discretion_form`: een afwegings- of bevoegdheidsvorm;
  - `descriptive_act`: een beschreven handeling;
  - `no_act`: geen handeling.
- `bronfuncties` bevat per sleutel uit `grondbronnen` precies één object `{bron, function, quote}`.

**Bronfunctie:**
- `function` is de functie die die grondbron geeft aan de inhoud van deze passage.
- Het citaat (`quote`) hangt af van de functie:
  - **verplicht** bij `criterion`, `derivation`, `actor_prescription`, `discretionary_decision_rule` en `not_a_criterion`;
  - **optioneel** bij `unclear`;
  - **`null`** bij `not_addressed`.

  Een citaat staat precies één keer exact in de tekst van die grondbron. De code leidt de posities af.
- De volgorde van de bronfuncties wordt niet afgedwongen (dat kan het schema niet). De afleiding leest altijd in de vaste volgorde van `grondbronnen`.

**Volgorde van controle:**
1. De structuur, gesloten en met enums (`invalid_output`).
2. Per passage het passagecitaat (`invalid_citation`). Een citaat zonder zichtbare letter geeft `leeg` (P1-rest, herreview 2). Daarna volgt de positie: niet gevonden of niet uniek.
3. Per bronfunctie:
   1. Een onbekende sleutel geeft `invalid_citation` / `grond_niet_herleidbaar`. Dat geldt ook voor `bedoeling` als de bedoeling onbekend is.
   2. Een andere functie dan `not_addressed` op een bron zonder zichtbare letter geeft `invalid_citation` / `grond_niet_herleidbaar` (P1, P1-rest, herreview 2). Voorbeelden van zo'n bron: leeg, alleen witruimte, "...", een Hangul-filler of alleen cijfers.
   3. Een citaatplicht die niet is nagekomen, geeft `invalid_output`.
   4. Een citaat zonder zichtbare letter geeft `invalid_citation` / `leeg` (P1, P1-rest, herreview 2). Een citaat dat niet voorkomt of niet uniek is, geeft `niet_gevonden` / `niet_uniek`.
4. Volledigheid: elke sleutel precies één keer, anders `invalid_output`.
5. De samenhang van het eigen verdict.
6. De afleiding.

Ongeldige uitvoer wordt nooit gerepareerd of omgezet: zij blijft `error`.

### Samenhang van het eigen verdict

Zoals onder /3, zonder de eisen aan passagefuncties.
- Buiten `not_applicable` is minstens één passage vereist.
- `pass`: `coverage = complete`, `uncertainty ≠ decisive`, geen vraag.
- `fail`: geen vraag, of precies één vraag.
- `insufficient_information`: precies één vraag en `uncertainty = decisive`.
- `not_applicable`: niet-lege `scope_reason`, geen passages, `coverage = none`, `uncertainty = none` en geen vraag.

## Beslisregel

**Richtingen.** Een bronfunctie telt in een van vier richtingen:
- **B**: `criterion` of `derivation`;
- **G**: `actor_prescription` of `discretionary_decision_rule`;
- **N**: `not_a_criterion`;
- **O**: `unclear`.

`not_addressed` telt niet mee.

### Per passage

De stappen worden in deze volgorde doorlopen; de eerste die past, beslist.

| Stap | Situatie | Uitkomst | Regel (`afleiding`) |
|---|---|---|---|
| 1 | kernvorm `instruction` | gebrek (`actor_prescription`) | `voorschrift_in_kern` |
| 2 | B naast G of N, en de bedoeling is G of N | gebrek | `bedoeling_beslist` (1B: alleen naar gebrek) |
| 2 | B naast G of N, overig | review | `conflict` |
| 3 | alleen B | beschrijvend | `bronnen_beschrijvend` |
| 3 | G of N, met een tweede signaal: kernvorm `obligation_form`/`discretion_form`, G én N samen (6A), of een bedoeling die G of N is | gebrek | `voorschrift_bevestigd` |
| 3 | G of N, zonder tweede signaal | review | `bronvoorschrift_niet_overgenomen` (3A) |
| 3 | alleen O | review | `bronnen_open` |
| 4 | alles zwijgt, kernvorm `no_act`, of `descriptive_act` met bekende bedoeling | beschrijvend | `alleen_kern` |
| 4 | alles zwijgt, `descriptive_act`, bedoeling onbekend | review | `geen_grond_zonder_bedoeling` (5A) |
| 4 | alles zwijgt, `discretion_form`, bedoeling onbekend | review | `discretie_zonder_bedoeling` (besluit 12) |
| 4 | alles zwijgt, overig (`obligation_form`, of `discretion_form` met bedoeling) | gebrek | `voorschrift_in_kern` |

In stap 4 is een bedoeling alleen bekend als zij een zichtbare letter bevat (P1-rest, herreview 2); "..." telt als onbekend.

**Discretionair gebrek.** Een gebrek is discretionair (`discretionary_decision_rule`, met de VN-discretievariant) als de kernvorm `discretion_form` is, of als de eerste G-bron `discretionary_decision_rule` zegt.

### Over passages en over het geheel

De afleiding loopt in deze volgorde (actor `ai`):
1. **Gebrek.** Er is een gebrekpassage → `fail`. De melding is VN over de eerste gebrekpassage, gerekend op de afgeleide `start`. Is er ook een reviewpassage, dan volgt daarachter `MELDING_OPEN_PUNT` met één vaste vraag (SC-C-03), en is `vraag` die vraag.
2. **Reviewpassage.** Er is een reviewpassage → `review_required` / `insufficient_information`. De reden is het redensjabloon van de eerste reviewpassage en de vraag de vaste vraag van die regel.
3. **Onvolledige dekking.** De dekking is niet `complete` → `review_required`, met regel `onvolledige_dekking` en `VRAAG_DEKKING`.
4. **Beslissende onzekerheid (besluit 17).** De beoordelaar meldt `uncertainty = decisive` → `review_required`, met regel `model_beslissend_onzeker` en `VRAAG_FUNCTIE`.
5. **Pass.** Anders `pass`, met de V-melding over de eerste beschrijvende passage. De regel is die van die passage (`bronnen_beschrijvend` of `alleen_kern`).

Bij `not_applicable` blijft het eigen verdict staan, met regel `niet_van_toepassing`.

**Besluit 17 in het kort.**
- Een eigen reviewgrond (stap 2–3) houdt haar eigen code.
- Stap 4 geldt alleen als de dienst anders pass zou afleiden.
- Omdat `insufficient_information` altijd `decisive` is, kan een model-review onder /4 nooit pass worden. Een model-fail met `decisive` en een kenmerkgrond wordt review, met `omzetting = model_beslissend_onzeker`.

### Vaste vragen en redenen (4A)

**Vragen:**
- `VRAAG_FUNCTIE`: `Bepaalt deze passage wat tot het begrip behoort, of schrijft zij een actor een handeling of afweging voor?`
  Gebruikt bij `conflict`, `bronvoorschrift_niet_overgenomen`, `bronnen_open`, `geen_grond_zonder_bedoeling` en `model_beslissend_onzeker`.
- `VRAAG_DEKKING`: `Welke nog niet beoordeelde passage van de kern bepaalt mede wat tot het begrip behoort?`
- `discretie_zonder_bedoeling`: de vaste vraag van /3.

**Redenen.** Elke reden noemt de passage en de grondbronnen met hun citaten:
- `conflict`: `Strijdige betekenisgrond voor '{passage}': {voor} gebruikt de inhoud als kenmerk van het begrip; {tegen} {rol}; {slot}`
- `bronvoorschrift_niet_overgenomen`: `Alleen {tegen} {rol} bij '{passage}'; de kern neemt dat niet in voorschrijvende vorm over en geen tweede grond bevestigt het`
- `bronnen_open`: `{open} laat open welke functie '{passage}' heeft; geen andere grond beslist dat`
- `geen_grond_zonder_bedoeling`: `De bevestigde bedoeling is onbekend en geen aangeleverde grond zegt iets over de functie van '{passage}'`
- `onvolledige_dekking`: `Niet alle relevante passages van de kern zijn beoordeeld (dekking: {dekking})`
- `model_beslissend_onzeker` (besluit 17): `Volgens {grond} is '{passage}' een kenmerk van het begrip, maar de beoordelaar meldt beslissende onzekerheid; dat volstaat niet voor een goedkeuring`

De modelvraag gaat niet verloren: zij blijft zichtbaar in `oordeel["question"]`.

## Statusmapping

Als onder /3 (NE, E, nog niet beoordeeld, historisch en NA). Voor geldige /4-uitvoer:

| Situatie | `status` | `reden` | Melding | `omzetting` (alleen actor `ai`) |
|---|---|---|---|---|
| gebrekpassage | `fail` | — | VN (+ discretievariant; + open punt bij een reviewpassage) | de regel, als het modelverdict geen `fail` was |
| reviewpassage of onvolledige dekking | `review_required` | `insufficient_information` | O met vaste reden en vraag | de regel, als het modelverdict geen `insufficient_information` was |
| anders pass, maar `uncertainty = decisive` | `review_required` | `insufficient_information` | O met de reden van besluit 17 en `VRAAG_FUNCTIE` | `model_beslissend_onzeker`, als het modelverdict `fail` was |
| anders | `pass` | — | V | de regel, als het modelverdict geen `pass` was (2A, bijvoorbeeld fail → pass) |
| verdict `not_applicable` | `not_applicable` | — | NA | — |

## Bewaard oordeel en replay

`oordeel_json` is de geaccepteerde modeluitvoer met de afgeleide `start`/`end`, per passage en per bronfunctie met citaat. Daarnaast bevat het een blok `dienst`:
- `afleiding`: de beslissende regel;
- `modelstatus`: de status van het eigen modelverdict;
- `passages`: per passage de afgeleide functie en grond in /3-vorm, met `uitkomst` (gebrek, review of beschrijvend) en `regel`.

`Binding.contractversie` is `def835-int02-assessment/4`.

**Replay.** `toets_actualiteit` leidt een /4-document opnieuw af uit de bewaarde modelvorm: zonder `dienst` en zonder posities. Daarna vergelijkt het die afleiding met wat er bewaard is. Het document wordt niet-herleidbaar (`error`) bij:
- een gewijzigde of ontbrekende `omzetting`, status, vraag, melding, afleiding, modelstatus of dienstfunctie;
- een ontbrekend dienstblok;
- een modelvorm die de controles van /4 niet meer doorstaat, bijvoorbeeld een citaat zonder zichtbare letter (P1-rest, herreview 2).

**Replay toetst samenhang, niet echtheid.** Replay controleert of het bewaarde document past bij de bewaarde modelvorm. Of die modelvorm het echte antwoord van het model is, controleert replay niet; dat hoort bij de opslaglaag (DEF-626).

Een gewijzigde onzekerheid geeft daarom alleen `error` als de afgeleide uitkomst erdoor verandert. Voorbeelden:
- `decisive → none` op een omgezette kenmerk-fail geeft `error`, want de dienst zou dan pass afleiden.
- `none → non_decisive` op een pass blijft geldig.
- `decisive → none` op een fail door een voorschrift in de kern blijft geldig.

Zie `test_17_replay_toetst_samenhang_niet_de_echtheid_van_de_onzekerheid`.

**Historische documenten.** Een bewaard /1-, /2- of /3-document wordt volgens de regels van zijn eigen versie gecontroleerd en is daarna historisch (`review_required` / `historical`). De dienstregel van /3 blijft daarvoor bestaan.

## Rapportage in de proefrunner

`scripts/analysis/def835_int02_modelproef.py` legt het volgende vast (ontwerp §4.4, Codex-review P2):

**Identiteit:**
- `contractversie`;
- `profiel.promptversie`;
- `router.antwoordschema_sha256`.

**Per geval:**
- `afleiding`;
- `modelstatus`;
- `omzetting`;
- `omzettingsrichting` (bijvoorbeeld `fail→pass`).

**Per fase:**
- `afleidingen` (telling per regel);
- `omzettingen` (totaal, per richting en per regel);
- `bewijsstatus`.

Fase 1 en 2 van v8 (regressie en ontwikkeling) zijn een **consistentietoets** (keuze 7A): het ontwerp is op die gevallen afgestemd. Alleen de hold-out, met apart akkoord, is onafhankelijk bewijs.

## Bewijsgrenzen

- **Geen semantische modelkwaliteit.** De paper test (27/27 op de regressie- en ontwikkelgevallen, met gesynthetiseerde modeluitvoer) toetst de beslisregel, niet het model. Hij is per constructie op die gevallen afgestemd.
- **Besluit 17 raakt mogelijke passes.** Codex-review, 07-10-2026: het 27/27-resultaat en de v7-passes veranderen niet. De regel kan wel tot 13 passes raken als het model twijfel meldt: C112, G007, G011, G015, G019, G021, G027, G030, G037, G039, G041, G046 en G055. Dat is de bedoelde prijs van "bij twijfel review".
- **Restrisico G045.** Een volledig verkeerde invulling in één richting (B1 als `criterion`) blijft een onterechte pass. De regel kan geen grond verzinnen die het model niet geeft.
- **Niet geactiveerd** en **geen persistentie**: zoals onder /3.
- **Mechanische vraagcontrole.** "Precies één vraag" is een vormcontrole.
