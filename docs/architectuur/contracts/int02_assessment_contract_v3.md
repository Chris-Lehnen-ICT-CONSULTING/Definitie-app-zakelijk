# INT-02 — intern beoordelingscontract `def835-int02-assessment/3`

> **Historisch.** Opgevolgd door `def835-int02-assessment/4` (`int02_assessment_contract_v4.md`, besluiten 16 en 17). Dit document beschrijft /3 ongewijzigd; `src/domain/int02/contract.py` implementeert nu /4 en toetst /3-documenten alleen nog als historisch.

Status: intern domeincontract (DEF-835 WP1, akkoord 26-09-2026; versie /2 na besluit 9 van Chris, 07-10-2026, optie A; versie /3 na besluit 12 van Chris, 07-10-2026, optie A). Norm: `def771-int02/2` (INT-02, N-breed, besluiten B1–B6). Implementatie: `src/domain/int02/contract.py`. Tests: `tests/unit/domain/test_def835_int02_contract.py`, `tests/unit/domain/test_def835_int02_citaatposities.py`, `tests/unit/domain/test_def835_int02_dienstregel.py` en `tests/unit/domain/test_def835_int02_migratie.py`. Ontwikkelgevallen: `tests/fixtures/def835_int02_ontwerpgevallen.json`. Vorige versies: `def835-int02-assessment/1` (`int02_assessment_contract_v1.md`) en `def835-int02-assessment/2` (`int02_assessment_contract_v2.md`), beide historisch en ongewijzigd.

## Wijziging ten opzichte van /2

Eén smalle, deterministische dienstregel: **discretie zonder bedoeling** (besluit 12). Al het overige is gelijk aan /2, ook de citaten en de afgeleide posities.

- **Wanneer.** Alle vier de voorwaarden gelden:
  1. de uitvoer is geldig (structuur, citaten en samenhang zoals onder /2) en heeft verdict `fail`;
  2. de beoordelaar is een model (`Uitvoering.actor == "ai"`);
  3. de bevestigde bedoeling is onbekend (`bedoeling` is `None`; een lege bedoeling kan het invoercontract niet bevatten);
  4. **alle** passages die de fail dragen (functie `actor_prescription` of `discretionary_decision_rule`) hebben functie `discretionary_decision_rule` en als grond uitsluitend het veld `kern` (met of zonder grondcitaat).

  Passages met `criterion`, `derivation` of `unclear` dragen de fail niet en tellen niet mee.
- **Dan.** `status = review_required`, `reden = insufficient_information`, `vraag` = de vaste vraag hieronder, `melding` = de O-melding (zie "Meldingen") en `omzetting = "discretie_zonder_bedoeling"`.
- **Anders blijft het `fail`.** Dat geldt als minstens één dragende passage de fail op een andere manier draagt:
  - een `actor_prescription`, ook met alleen de kern als grond (besluit 1: een expliciet actorvoorschrift in de kern mag een fail dragen);
  - een discretionaire beslisregel met als grond het begrip, de context of een bronpassage.

  Het blijft ook `fail` als de bedoeling bekend is, of als de beoordelaar een mens is.
- **Zichtbaar, nooit stil.** Het bewaarde oordeel (`oordeel_json`) blijft de geaccepteerde modeluitvoer met verdict `fail`, de functie, de grond, de redenering en de afgeleide posities. Het nieuwe documentveld `omzetting` legt vast dat en waarom de uitkomst daarvan afwijkt.
- **Geen nieuw pass-pad.** De regel zet alleen `fail` om in `review_required` en raakt geen ander verdict.
- **Vaste vraag** (invoeronafhankelijk; mechanisch precies één vraag):

  `Is de bedoeling dat deze passage een begripskenmerk beschrijft of de actor een afweging voorschrijft?`

  **Keuze (besluit 12): altijd deze vaste vraag, ook als het model bij zijn fail zelf een vraag gaf.** Reden: bij een fail gaat een vraag volgens de T-tekst over *andere* open punten (SC-C-03: "een zelfstandig aangetoond gebrek blijft zichtbaar als andere vragen openstaan"), niet over de ontbrekende bedoeling waar deze omzetting om draait. De code kan bovendien niet vaststellen of een modelvraag gericht is; de vaste vraag is dat per constructie en geeft bij elke run dezelfde uitkomst. De modelvraag gaat niet verloren: zij blijft zichtbaar in `oordeel["question"]`.
- **Replay.** De regel is deterministisch en hoort bij /3. Een omgezet /3-document levert bij hercontrole exact hetzelfde document op. In `toets_actualiteit` gaat een ontbrekende actuele kern of context altijd voor: dan is de uitkomst `not_evaluated`, ook bij een gemanipuleerd document. Anders maakt een ontbrekende, gewijzigde of onterechte `omzetting` het document niet-herleidbaar (`error`). Dat geldt ook voor een andere documentvraag (`vraag`), status, reden of melding.
- **Grens van de hercontrole.** Na een omzetting hangen `vraag` en `melding` niet af van de vraag die het model bij zijn fail gaf. Een consistente wijziging van die bewaarde modelvraag (`oordeel["question"]`, nog steeds precies één vraag) is daardoor niet aan te tonen. De hercontrole toetst samenhang, geen authenticiteit; authenticiteit hoort bij de opslaglaag (DEF-626). Een vormfout in die vraag geeft wel `error`.
- **Migratie.** Een bewaard /1- of /2-document wordt eerst volgens de regels van zijn eigen versie gecontroleerd, zonder dienstregel. Een geldig document is daarna historisch (`review_required` / `historical`) en wordt niet omgezet. Een document met gewijzigde posities, citaten, status of melding geeft `error`, binnen de grens die hierboven en onder "Bewijsgrenzen" staat.

Dit contract is **niet** het publieke resultaatcontract. Dat is `CONTRACT_VERSION = "2.3.0"` in `src/services/validation/interfaces.py`, waarin `rule_results['INT-02']` additief de velden `assessment` (dit document, of null) en `signals` mag dragen. Het documentveld `omzetting` reist binnen `assessment` mee; het resultaatcontract zelf verandert niet. Stand op 07-10-2026:
- de onderdelen rond dit contract bestaan wel:
  - prompt en dienst: `src/services/validation/int02_assessment_service.py`, `def835-int02-prompt/3` (ongewijzigd door /3);
  - evaluator: `decision_rule_assessment`;
  - containerfabriek `int02_assessment_service(profiel=…, budget=…)`, alleen op expliciet verzoek;
  - injectie in `DefinitionOrchestratorV2` en `ValidationOrchestratorV2`;
- het is **niet geactiveerd**:
  - het actieve INT-02-record kiest nog `judgment_review` (O1);
  - de evaluator is geregistreerd maar door geen actief record gekozen;
  - de container bedraadt de dienst niet in `orchestrator()`;
  - er is geen eigen O2-weergave in de UI en geen opslag (DEF-626).

Bronnen:
- `docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/gezamenlijke-synthese-v5.md` §2 (norm) en §4 (T-tekst, appmeldingen, statusmapping);
- `.../gedeeld/besluiten-chris-v1.md`;
- `.../gedeeld/uitvoering/o2/plan-v1.md` §Ontwerpvoorstel;
- `.../gedeeld/uitvoering/o2/besluit-chris-promptcorrectie-en-v3-v1.md` (besluiten 1, 9 en 12).

## Wijziging van /2 ten opzichte van /1 (blijft gelden)

- De beoordelaar levert **geen posities** meer. Een passage is `{quote, function, ground}`, een grond `{field, ref, quote}`. Uitvoer met `start` of `end` heeft onbekende velden en geeft `error` / `invalid_output`, ook als de waarden juist zijn.
- De code **leidt de posities af**: een citaat moet precies één keer als exacte substring (Python-codepunten, geen normalisatie van hoofdletters, witruimte, leestekens of Unicode-vorm) voorkomen in de tekst van het opgegeven veld. Dan is `start` die vindplaats en `end = start + len(quote)`, nulgebaseerd, einde exclusief. Nul vindplaatsen, meer dan één vindplaats (ook overlappend) of een leeg citaat geeft `error` / `invalid_citation`.
- Documentveld `foutdetail` bij `invalid_citation`: `niet_gevonden`, `niet_uniek`, `leeg` of `grond_niet_herleidbaar`; anders `None`.
- Het bewaarde oordeel houdt dezelfde vorm als onder /1, mét `start`/`end`, altijd door de code afgeleid. Replay laat de bewaarde posities weg en leidt ze opnieuw af.

## Rolverdeling

De beoordelaar (een model of een mens) bepaalt per relevante passage de functie en de grond. De code controleert alleen wat mechanisch controleerbaar is: structuur, typen, citaatposities, herleidbaarheid van de grond, samenhang tussen verdict en passages, binding en status. **De code bewijst geen semantische juistheid en geen volledigheid.** Een gedeclareerde `coverage: complete` blijft een claim van de beoordelaar. Woorden als "indien" of "moet" hebben in de code geen normatieve rol. De dienstregel van /3 kijkt alleen naar verdict, actor, het al dan niet bekend zijn van de bedoeling, functies en grondvelden; niet naar de tekst.

## API (`domain.int02.contract`)

| Onderdeel | Beschrijving |
|---|---|
| `maak_invoer(*, begrip, kern, bedoeling, organisatorische_context, juridische_context, wettelijke_basis, bronnen) -> Int02Invoer` | Defensieve kopie. Contextlijsten moeten een lijst of tuple zijn en worden tuples. Een bron is een mapping met precies `id` en `tekst` en wordt een `Bronpassage`. |
| `Int02Invoer` (frozen) | Zie de veldtabel hieronder. Ook de directe constructor valideert. |
| `Bronpassage(id, tekst)` (frozen) | `id` is een niet-lege tekst en uniek binnen de invoer; `tekst` is tekst. |
| `ontbrekende_invoer(invoer)` | Geeft `"kern"`, `"context"`, `"kern en context"` of `None`. Een lege kern, een kern met alleen witruimte en een los termlabel (`Toegang:`) gelden als ontbrekende kern; de O1-regel geldt ook voor C23. Context ontbreekt als alle drie de lijsten leeg zijn (K-9). |
| `Configuratie(normhash, promptversie, routeringshash, provider, model, normversie="def771-int02/2")` (frozen) | Hashes zijn SHA-256 in kleine hex. De overige velden zijn niet-lege tekst. `provider` en `model` zijn de **gevraagde** provider en het gevraagde model. |
| `Uitvoering(actor, status, foutcategorie=None, tijdstip, transportpogingen, invoertokens, uitvoertokens, duur_ms, kosten, modelversie)` (frozen) | Uitvoeringsmetadata; zie hieronder. |
| `bereken_binding(invoer, configuratie) -> Binding` | Zie "Versiebinding en replay". |
| `beoordeel(invoer, configuratie, modeluitvoer, uitvoering) -> Beoordelingsdocument` | Valideert en legt vast, inclusief de dienstregel. Repareert nooit en doet zelf geen modelcall. |
| `toets_actualiteit(document \| None, invoer, configuratie) -> Actualiteit(status, reden, melding)` | Past een bewaard document toe op de actuele invoer en configuratie. |
| `OMZETTING_DISCRETIE_ZONDER_BEDOELING`, `VRAAG_DISCRETIE_ZONDER_BEDOELING`, `REDEN_DISCRETIE_ZONDER_BEDOELING` | Constanten van de dienstregel (/3). |
| `Int02ContractError(ValueError)` | Ongeldige invoer, configuratie of metadata van de aanroeper. Een fout in de uitvoer van de beoordelaar is **geen** exceptie: die wordt een document met status `error`. |

### Invoer

| Veld | Type | Regel |
|---|---|---|
| `begrip` | `str` | exact bewaard |
| `kern` | `str` | bytegelijk bewaard, zonder strip of normalisatie; alle posities verwijzen naar deze tekst |
| `bedoeling` | `str \| None` | niet-lege tekst; `None` betekent **expliciet onbekend** |
| `organisatorische_context`, `juridische_context`, `wettelijke_basis` | `tuple[str, ...]` | alleen niet-lege teksten; de volgorde is exact |
| `bronnen` | `tuple[Bronpassage, ...]` | expliciet aangeleverd; geen webophaling of verborgen aanvulling |

### Uitvoeringsmetadata

| Veld | Waarde |
|---|---|
| `actor` | `ai` of `human`; alleen bij `ai` geldt de dienstregel |
| `status` | `completed`, `failed` of `not_executed` |
| `foutcategorie` | alleen bij `failed`: `timeout`, `transport` of `provider` |
| `tijdstip`, `modelversie` | niet-lege tekst of `"unknown"`; `modelversie` is de door de provider **gerapporteerde** versie |
| `transportpogingen`, `invoertokens`, `uitvoertokens`, `duur_ms` | niet-negatieve `int` (geen `bool`) of `"unknown"` |
| `kosten` | eindige, niet-negatieve `Decimal` of `"unknown"`; in `als_dict()` als decimale tekst |

Een meting die niet is gerapporteerd, is `"unknown"`, nooit `0` of `None`. Er worden geen metingen verzonnen.

## Gesloten beoordelaarsuitvoer

Ongewijzigd ten opzichte van /2. De uitvoer is een JSON-object (`dict`) met precies deze velden. Een ontbrekend of onbekend veld, een ander type of een waarde buiten de enum geeft `error` met foutcategorie `invalid_output`. Een `bool` geldt nooit als `int`. Een andere `Mapping` dan `dict` wordt geweigerd.

| Veld | Type / waarden |
|---|---|
| `verdict` | `pass`, `fail`, `insufficient_information`, `not_applicable` |
| `passages` | lijst van passageobjecten (zie hieronder) |
| `reason` | niet-lege tekst |
| `question` | `null` of tekst |
| `uncertainty` | `none`, `non_decisive`, `decisive` |
| `scope_reason` | `null` of tekst |
| `coverage` | `complete`, `partial`, `none` |

Passage: `{quote: str, function, ground}`.
- `function` is `criterion` (begripscriterium), `derivation` (deterministische afleiding), `actor_prescription` (actorvoorschrift of procedure), `discretionary_decision_rule` (discretionaire beslisregel) of `unclear`.
- `quote` komt precies één keer als exacte substring in de kern voor, zonder normalisatie van hoofdletters, witruimte, leestekens of Unicode-vorm. De code leidt `start` (die vindplaats) en `end = start + len(quote)` af, in Python-codepunten, nulgebaseerd, einde exclusief.

Grond: `{field, ref, quote}`.
- `field` is `kern`, `begrip`, `bedoeling`, `organisatorische_context`, `juridische_context`, `wettelijke_basis` of `bron`.
- `ref` hangt af van `field`:
  - `null` bij `kern`, `begrip` en `bedoeling`;
  - een `int`-index bij een contextlijst;
  - een bestaand bron-ID bij `bron`.
- `quote` is `null`, of een citaat dat precies één keer exact voorkomt in de tekst waarnaar de grond verwijst, met dezelfde afleiding van `start`/`end`. Zonder grondcitaat zijn `start` en `end` in het bewaarde oordeel `null`.
- De tekst waarnaar de grond verwijst, moet gevuld zijn, ook zonder grondcitaat. Bij de volgende gronden volgt `error` met foutcategorie `invalid_citation`:
  - een onbekende bedoeling (`None`), een leeg begrip of een begrip met alleen witruimte, een lege bron of een bron met alleen witruimte, een onbekend bron-ID of een index buiten de lijst (`foutdetail` `grond_niet_herleidbaar`);
  - een citaat dat niet voorkomt (`niet_gevonden`), meer dan eens voorkomt, ook overlappend (`niet_uniek`), of leeg is (`leeg`); dat geldt ook voor het passagecitaat in de kern.

  Zo kan lege bewijsvoering geen pass of fail dragen. Een onbekende bedoeling is dus nooit een grond; de dienstregel ziet daardoor bij een onbekende bedoeling alleen de gronden kern, begrip, context en bron.

Volgorde van controle: eerst de volledige structuur (`invalid_output`, ook bij meegeleverde `start`/`end`), dan per passage het passagecitaat, de herleidbaarheid van de grond en het grondcitaat (`invalid_citation`), dan de samenhang (`invalid_output`), dan de status en ten slotte de dienstregel. Ongeldige uitvoer wordt dus nooit omgezet: zij blijft `error`.

### Samenhangsregels

| Verdict | Vereist; anders `error` / `invalid_output` |
|---|---|
| `pass` | Minstens één passage. Alleen `criterion`/`derivation`. `coverage = complete`. `uncertainty ≠ decisive`. Geen vraag, geen `scope_reason`. |
| `fail` | Minstens één `actor_prescription` of `discretionary_decision_rule`. Geen `scope_reason`. Een vraag is toegestaan, maar dan precies één. Andere open punten, onzekerheid en gedeeltelijke dekking laten het verdict fail. |
| `insufficient_information` | Geen `actor_prescription`/`discretionary_decision_rule`. Precies één vraag. `uncertainty = decisive`. Geen `scope_reason`. |
| `not_applicable` | Niet-lege `scope_reason` (reikwijdtegrond buiten het definitietoetsbereik). Geen passages, `coverage = none`, `uncertainty = none`, geen vraag. Een afleiding is dus nooit NA, maar pass. |

"Precies één vraag" wordt mechanisch gecontroleerd: één niet-lege tekst die eindigt op het enige vraagteken. De code stelt niet vast dat de vraag gericht of juist is. De samenhang geldt voor de modeluitvoer; een omgezette fail hoeft niet aan de regels voor `insufficient_information` te voldoen, omdat het oordeel zelf `fail` blijft.

## Statusmapping (synthese v5 §4, plus de dienstregel)

| Situatie | `status` | `reden` | Melding | `omzetting` |
|---|---|---|---|---|
| Kern en/of context ontbreekt (ook als uitvoer is meegegeven, ook bij een NA-verdict) | `not_evaluated` | — | NE | — |
| Uitvoering `failed` (timeout/transport/provider); meegegeven uitvoer wordt genegeerd | `error` | — | E (foutcategorie = gemelde categorie) | — |
| Uitvoering `not_executed`, geen uitvoer | `review_required` | `not_assessed` | nog niet beoordeeld | — |
| Ongeldige structuur of samenhang; voltooid zonder uitvoer; `not_executed` mét uitvoer | `error` | — | E (`invalid_output`) | — |
| Citaat niet gevonden, niet uniek of leeg, of niet-herleidbare grond (C117) | `error` | — | E (`invalid_citation`, met `foutdetail`) | — |
| `pass` | `pass` | — | V | — |
| `fail`, dienstregel geldt niet | `fail` | — | VN (bij discretie: VN + discretievariant) | — |
| `fail`, dienstregel geldt (model, bedoeling onbekend, alle dragende passages discretionair op grond van de kern) | `review_required` | `insufficient_information` | O met de vaste reden en vraag | `discretie_zonder_bedoeling` |
| `insufficient_information` | `review_required` | `insufficient_information` | O | — |
| `not_applicable` | `not_applicable` | — | NA | — |
| Replay: andere binding (ook een /1- of /2-document) | `review_required` | `historical` | Historisch | — |
| Replay: geen document | `review_required` | `not_assessed` | nog niet beoordeeld | — |

Er is geen score of cijfer: het document heeft geen scoreveld en een `score`-veld in de uitvoer is een onbekend veld (`invalid_output`). Er is geen poort en geen herstel.

## Meldingen

### Letterlijke sjablonen uit synthese v5 §4 (B3 V06)

- V: `INT-02 — Voldoet. '{passage}' beschrijft {criterium/afleiding/kenmerk}; grond: {grond}. Andere toetsregels zijn hiermee niet beoordeeld.`
- VN: `INT-02 — Voldoet niet. '{passage}' schrijft {handeling/afweging} voor in plaats van het begrip af te bakenen. Grond: {grond}. De tekst is ongewijzigd.`
- Discretievariant: `Deze passage functioneert als discretionaire beslisregel voor het handelen: '{citaat}'. Dat is onder de gekozen INT-02-norm geen beschrijvende afbakening van dit begrip. Het enkele beschrijven van een bevoegdheid of besluit is geen overtreding.`
- O: `INT-02 — Onvoldoende informatie. {ontbrekende of strijdige betekenisgrond}. Vraag: {één vraag}`
- NE: `INT-02 — Niet uitgevoerd: {kern/context} ontbreekt. Er is geen inhoudelijk oordeel.`
- E: `INT-02 — De beoordeling kon niet worden uitgevoerd door een technische fout. Er is geen inhoudelijk oordeel; de tekst is ongewijzigd.`
- Historisch: `INT-02 — Eerdere beoordeling hoort bij een andere tekst-, betekenis-, context-, bron- of normversie. Opnieuw beoordelen is nodig.`

### Uitvoeringstekst van dit contract, geen sjabloon uit synthese §4

- Nog niet beoordeeld volgt letterlijk de T-toestand "nog te beoordelen — beoordeling niet uitgevoerd": `INT-02 — Nog te beoordelen — beoordeling niet uitgevoerd.`
- Niet van toepassing, alleen met reikwijdtegrond: `INT-02 — Niet van toepassing. {reikwijdtegrond}. Er is geen oordeel over de definitiekern.` §4 noemt alleen "NA→not_applicable … alleen met grond".
- Discretie: de VN-basistekst met `{handeling/afweging}` = "een afweging", met geldig citaat en grond, gevolgd door een spatie en de letterlijke discretievariant. Dit is een weergavekeuze en geen nieuwe norm.
- Omzetting discretie zonder bedoeling (/3): het O-sjabloon met als `{ontbrekende of strijdige betekenisgrond}` de vaste reden `De bevestigde bedoeling is onbekend; alleen de kern zelf draagt de lezing van '{citaat}' als discretionaire beslisregel` (`{citaat}` = het citaat van de eerste dragende passage, gerekend op de afgeleide `start`) en als `{één vraag}` de vaste vraag `Is de bedoeling dat deze passage een begripskenmerk beschrijft of de actor een afweging voorschrijft?`. De redenering van het model staat niet in de melding; zij blijft in `oordeel["reason"]`.

### Invulling van de plaatshouders

- `{passage}` / `{citaat}`: het exacte citaat. Bij V is dat de eerste passage, bij VN de eerste gebrekkige passage, beide gerekend op de afgeleide `start`.
- `{criterium/afleiding/kenmerk}`: "een criterium" (`criterion`) of "een afleiding" (`derivation`).
- `{handeling/afweging}`: "een handeling" (`actor_prescription`) of "een afweging" (`discretionary_decision_rule`).
- `{grond}`: het veldlabel, met `('<citaat>')` erachter bij een geciteerde grond. Veldlabels: "de kern", "het begrip", "de bevestigde bedoeling", "de organisatorische context", "de juridische context", "de wettelijke basis", "bronpassage <ID>".
- `{ontbrekende of strijdige betekenisgrond}` = `reason` en `{reikwijdtegrond}` = `scope_reason`, beide zonder afsluitende punt; `{één vraag}` = `question`. Bij de omzetting gelden de vaste reden en vraag hierboven.
- `{kern/context}`: "kern", "context" of "kern en context".

De plaatshouders worden in één doorgang ingevuld, en alleen in het oorspronkelijke sjabloon. Een ingevoegde waarde wordt nooit opnieuw geïnterpreteerd. Een citaat, grond, reden of vraag die zelf bijvoorbeeld `{grond}` of `{één vraag}` bevat, verschijnt daardoor letterlijk en onveranderd in de melding.

Bij fail blijft een open vraag zichtbaar in `Beoordelingsdocument.vraag`. De melding blijft het VN-sjabloon; er wordt geen extra meldtekst verzonnen. Bij een omzetting is `Beoordelingsdocument.vraag` de vaste vraag.

## Versiebinding en replay

`Binding` bevat:
- `contractversie` (`def835-int02-assessment/3`);
- uit de configuratie: `normversie`, `normhash`, `promptversie`, `routeringshash`, `provider` en `model`;
- de hashes `begrip_hash`, `kern_hash`, `bedoeling_hash`, `context_hash` (de drie lijsten per veldnaam) en `bronnen_hash` (ID én tekst, in de gegeven volgorde).

Elke hash is SHA-256 over canonieke JSON. Elke component afzonderlijk wijzigt precies zijn eigen bindingsveld; dat is per component getest, ook een wijziging die alleen witruimte in de kern betreft.

De gerapporteerde modelversie staat in `Uitvoering` en maakt deel uit van het document. Zij hoort niet bij de replayvergelijking, omdat zij vóór een nieuwe beoordeling onbekend is.

`Beoordelingsdocument` (frozen) bevat:
- `contractversie`, `invoer` (snapshot), `binding` en `uitvoering`;
- `status`, `reden`, `melding`, `vraag`, `foutcategorie`, `foutdetail` en (nieuw in /3) `omzetting`: `"discretie_zonder_bedoeling"` na een omzetting, anders `None` (ook bij elk /1- en /2-document);
- `oordeel_json`: de canonieke JSON van de geaccepteerde uitvoer met de door de code afgeleide `start`/`end` per passage en grond, of `None`. Bij een omzetting is dat de modeluitvoer met verdict `fail`.

`oordeel` levert telkens een verse kopie en `als_dict()` een JSON-serialiseerbare weergave, met de sleutel `omzetting`. De meegegeven uitvoer wordt niet gemuteerd. Een afgewezen uitvoer wordt niet bewaard: `oordeel` is dan `None`.

`toets_actualiteit` volgt deze volgorde:
1. De actuele kern of context ontbreekt → NE.
2. Er is geen document → nog niet beoordeeld.
3. Het document is een technische fout, of **niet herleidbaar** → `error`. Herleidbaar betekent: de onderdelen worden opnieuw via hun constructors gevalideerd en het document wordt gecontroleerd volgens de regels van zijn eigen contractversie.
   - Bij /3 levert `beoordeel` op de eigen invoer, de uit de binding afgeleide configuratie, de uitvoering en het oordeel zonder zijn afgeleide posities exact hetzelfde document op: dezelfde posities en dezelfde dienstregeluitkomst (`status`, `reden`, `vraag`, `melding`, `omzetting`).
   - Bij /2 gebeurt hetzelfde volgens de /2-regels, dus zonder dienstregel.
   - Bij /1 blijven de opgeslagen posities behouden en wordt het document exact volgens de /1-regels gecontroleerd.

   Een direct samengesteld document, een gewijzigde status, melding, documentvraag, omzetting, invoer, uitvoering of binding, of een corrupte `oordeel_json` wordt zo nooit stil actueel. Een gewijzigd deel van het oordeel dat de uitkomst niet bepaalt, valt daar niet onder; dat geldt bijvoorbeeld voor de bewaarde modelvraag na een omzetting (zie "Grens van de hercontrole"). Een `oordeel_json` die niet te decoderen is, geeft `error` en breekt de aanroep niet af. Alleen die decoderfouten (`ValueError`, `RecursionError`) worden afgevangen; er is geen catch-all.
4. De binding wijkt af van `bereken_binding(invoer, configuratie)` → historisch. Een herleidbaar /1- of /2-document valt hier altijd onder, omdat `contractversie` deel is van de binding.
5. Anders → het bewaarde oordeel.

Het document zelf wordt nooit gewijzigd. Een recordidentiteit speelt geen rol: C118 laat zien dat een nieuwe tekstversie onder hetzelfde record het oude oordeel historisch maakt.

## Bewijsgrenzen

- **Geen persistentie.** Er is geen database, geen append-only historie en geen save/reload (DEF-626, WP5). De integriteitscontrole ontdekt incoherentie en gedeeltelijke mutatie, maar alleen in wat de uitkomst bepaalt. De bewaarde modelvraag na een omzetting bepaalt de uitkomst niet; een consistente wijziging ervan valt dus niet op. Een volledig consistent vervalst document is niet te onderscheiden van een document dat met hetzelfde oordeel opnieuw via `beoordeel` is gemaakt. Authenticiteit en herkomst zijn een verantwoordelijkheid van de opslaglaag.
- **Geen semantische modelkwaliteit.** De gevallen C06/C23/C56, C101, C105, C107, C112, C115, C116, C117 en C118 zijn ontwikkelgevallen met handmatig ingevulde responsen, geen goldset of hold-out. Een groene test bewijst contractgedrag, niet dat een model de juiste functie, passage, vraag of dekking kiest (WP4).
- **Dienstregel.** De regel is een vangnet voor één vastgesteld foutpatroon (C107: 1 van 6 keer `fail` op prompt /3, kwalificatieproef v5 en variatiemeting C107). Hij maakt geen modeloordeel juist. Hij kan ook een terechte fail van het model omzetten als de kern alleen een discretionaire beslisregel draagt en de bedoeling onbekend is. Dat is de bewuste keuze van besluit 12: zonder bevestigde bedoeling vraagt de dienst het na in plaats van af te keuren. Een actorvoorschrift in de kern valt er niet onder (besluit 1).
- **Niet geactiveerd.** Wat bestaat:
  - prompt en dienst;
  - evaluator `decision_rule_assessment`;
  - containerfabriek;
  - orchestrator-injectie;
  - de publieke resultaatvelden `assessment`/`signals` voor INT-02 (resultaatcontract 2.3.0).

  Toch is niets actief. Het INT-02-record blijft O1 (`judgment_review`) en de dienst ontstaat alleen op expliciet verzoek met een vooraf vastgelegd profiel en budget. Er is geen eigen O2-weergave in de UI en geen opslag. Actions blijven uit.
- **Migratie /1 en /2 → /3.** Een bewaard /1-document wordt bij replay volgens de /1-regels op integriteit getoetst (opgeslagen posities, `tekst[start:end] == quote` exact), een /2-document volgens de /2-regels (afgeleide posities, geen dienstregel). Een herleidbaar document wordt `review_required` / `historical`, een gemanipuleerd document `error`. Een onbekende contractversie is nooit herleidbaar (`error`). Getest met referentiedocumenten uit de /1-code (`tests/fixtures/def835_int02_contract_v1_documenten.json`) en met het in kwalificatieproef v5 door de /2-code bewaarde C107-document (`kwalificatieproef-v5/regressie-resultaat.json`).
- **Mechanische vraagcontrole.** "Precies één vraag" is een vormcontrole; de code bewijst niet dat de vraag gericht is.
