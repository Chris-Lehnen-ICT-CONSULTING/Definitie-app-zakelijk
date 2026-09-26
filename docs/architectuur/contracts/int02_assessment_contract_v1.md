# INT-02 — intern beoordelingscontract `def835-int02-assessment/1`

Status: intern domeincontract (DEF-835 WP1, akkoord 26-09-2026). Norm: `def771-int02/2` (INT-02, N-breed, besluiten B1–B6). Implementatie: `src/domain/int02/contract.py`. Tests: `tests/unit/domain/test_def835_int02_contract.py`. Ontwikkelgevallen: `tests/fixtures/def835_int02_ontwerpgevallen.json`.

Dit contract is **niet** het publieke resultaatcontract (`validation_result_contract.md`, 2.2.0) en wijzigt geen record, prompt, service, evaluator, UI, database of schema. Het is niet geactiveerd en er is nog geen app-route die het gebruikt (WP2/WP3 vragen een afzonderlijk besluit).

Bronnen:
- `docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/gezamenlijke-synthese-v5.md` §2 (norm) en §4 (T-tekst, appmeldingen, statusmapping);
- `.../gedeeld/besluiten-chris-v1.md`;
- `.../gedeeld/uitvoering/o2/plan-v1.md` §Ontwerpvoorstel.

## Rolverdeling

De beoordelaar (een model of een mens) bepaalt per relevante passage de functie en de grond. De code controleert alleen wat mechanisch controleerbaar is: structuur, typen, citaatposities, herleidbaarheid van de grond, samenhang tussen verdict en passages, binding en status. **De code bewijst geen semantische juistheid en geen volledigheid.** Een gedeclareerde `coverage: complete` blijft een claim van de beoordelaar. Woorden als "indien" of "moet" hebben in de code geen normatieve rol.

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
| `beoordeel(invoer, configuratie, modeluitvoer, uitvoering) -> Beoordelingsdocument` | Valideert en legt vast. Repareert nooit en doet zelf geen modelcall. |
| `toets_actualiteit(document \| None, invoer, configuratie) -> Actualiteit(status, reden, melding)` | Past een bewaard document toe op de actuele invoer en configuratie. |
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
| `actor` | `ai` of `human` |
| `status` | `completed`, `failed` of `not_executed` |
| `foutcategorie` | alleen bij `failed`: `timeout`, `transport` of `provider` |
| `tijdstip`, `modelversie` | niet-lege tekst of `"unknown"`; `modelversie` is de door de provider **gerapporteerde** versie |
| `transportpogingen`, `invoertokens`, `uitvoertokens`, `duur_ms` | niet-negatieve `int` (geen `bool`) of `"unknown"` |
| `kosten` | eindige, niet-negatieve `Decimal` of `"unknown"`; in `als_dict()` als decimale tekst |

Een meting die niet is gerapporteerd, is `"unknown"`, nooit `0` of `None`. Er worden geen metingen verzonnen.

## Gesloten beoordelaarsuitvoer

De uitvoer is een JSON-object (`dict`) met precies deze velden. Een ontbrekend of onbekend veld, een ander type of een waarde buiten de enum geeft `error` met foutcategorie `invalid_output`. Een `bool` geldt nooit als `int`. Een andere `Mapping` dan `dict` wordt geweigerd.

| Veld | Type / waarden |
|---|---|
| `verdict` | `pass`, `fail`, `insufficient_information`, `not_applicable` |
| `passages` | lijst van passageobjecten (zie hieronder) |
| `reason` | niet-lege tekst |
| `question` | `null` of tekst |
| `uncertainty` | `none`, `non_decisive`, `decisive` |
| `scope_reason` | `null` of tekst |
| `coverage` | `complete`, `partial`, `none` |

Passage: `{quote: str, start: int, end: int, function, ground}`.
- `function` is `criterion` (begripscriterium), `derivation` (deterministische afleiding), `actor_prescription` (actorvoorschrift of procedure), `discretionary_decision_rule` (discretionaire beslisregel) of `unclear`.
- `kern[start:end] == quote`, met `0 <= start < end <= len(kern)`: nulgebaseerd, einde exclusief, zonder normalisatie van hoofdletters of witruimte.

Grond: `{field, ref, quote, start, end}`.
- `field` is `kern`, `begrip`, `bedoeling`, `organisatorische_context`, `juridische_context`, `wettelijke_basis` of `bron`.
- `ref` hangt af van `field`:
  - `null` bij `kern`, `begrip` en `bedoeling`;
  - een `int`-index bij een contextlijst;
  - een bestaand bron-ID bij `bron`.
- `quote`, `start` en `end` zijn samen `null`, of samen een exact citaat in de tekst waarnaar de grond verwijst, met dezelfde positieregel.
- Een grond op een onbekende bedoeling (`None`), een onbekend bron-ID, een index buiten de lijst of een citaat dat niet op zijn positie staat, geeft `error` met foutcategorie `invalid_citation`.

Volgorde van controle: eerst de volledige structuur (`invalid_output`), dan alle citaten en gronden (`invalid_citation`), dan de samenhang (`invalid_output`).

### Samenhangsregels

| Verdict | Vereist; anders `error` / `invalid_output` |
|---|---|
| `pass` | Minstens één passage. Alleen `criterion`/`derivation`. `coverage = complete`. `uncertainty ≠ decisive`. Geen vraag, geen `scope_reason`. |
| `fail` | Minstens één `actor_prescription` of `discretionary_decision_rule`. Geen `scope_reason`. Een vraag is toegestaan, maar dan precies één. Andere open punten, onzekerheid en gedeeltelijke dekking laten het verdict fail. |
| `insufficient_information` | Geen `actor_prescription`/`discretionary_decision_rule`. Precies één vraag. `uncertainty = decisive`. Geen `scope_reason`. |
| `not_applicable` | Niet-lege `scope_reason` (reikwijdtegrond buiten het definitietoetsbereik). Geen passages, `coverage = none`, `uncertainty = none`, geen vraag. Een afleiding is dus nooit NA, maar pass. |

"Precies één vraag" wordt mechanisch gecontroleerd: één niet-lege tekst die eindigt op het enige vraagteken. De code stelt niet vast dat de vraag gericht of juist is.

## Statusmapping (synthese v5 §4)

| Situatie | `status` | `reden` | Melding |
|---|---|---|---|
| Kern en/of context ontbreekt (ook als uitvoer is meegegeven, ook bij een NA-verdict) | `not_evaluated` | — | NE |
| Uitvoering `failed` (timeout/transport/provider); meegegeven uitvoer wordt genegeerd | `error` | — | E (foutcategorie = gemelde categorie) |
| Uitvoering `not_executed`, geen uitvoer | `review_required` | `not_assessed` | nog niet beoordeeld |
| Ongeldige structuur of samenhang; voltooid zonder uitvoer; `not_executed` mét uitvoer | `error` | — | E (`invalid_output`) |
| Onjuist citaat of niet-herleidbare grond (C117) | `error` | — | E (`invalid_citation`) |
| `pass` | `pass` | — | V |
| `fail` | `fail` | — | VN (bij discretie: VN + discretievariant) |
| `insufficient_information` | `review_required` | `insufficient_information` | O |
| `not_applicable` | `not_applicable` | — | NA |
| Replay: andere binding | `review_required` | `historical` | Historisch |
| Replay: geen document | `review_required` | `not_assessed` | nog niet beoordeeld |

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

### Invulling van de plaatshouders

- `{passage}` / `{citaat}`: het exacte citaat. Bij V is dat de eerste passage, bij VN de eerste gebrekkige passage, beide gerekend op `start`.
- `{criterium/afleiding/kenmerk}`: "een criterium" (`criterion`) of "een afleiding" (`derivation`).
- `{handeling/afweging}`: "een handeling" (`actor_prescription`) of "een afweging" (`discretionary_decision_rule`).
- `{grond}`: het veldlabel, met `('<citaat>')` erachter bij een geciteerde grond. Veldlabels: "de kern", "het begrip", "de bevestigde bedoeling", "de organisatorische context", "de juridische context", "de wettelijke basis", "bronpassage <ID>".
- `{ontbrekende of strijdige betekenisgrond}` = `reason` en `{reikwijdtegrond}` = `scope_reason`, beide zonder afsluitende punt; `{één vraag}` = `question`.
- `{kern/context}`: "kern", "context" of "kern en context".

Bij fail blijft een open vraag zichtbaar in `Beoordelingsdocument.vraag`. De melding blijft het VN-sjabloon; er wordt geen extra meldtekst verzonnen.

## Versiebinding en replay

`Binding` bevat:
- `contractversie` (`def835-int02-assessment/1`);
- uit de configuratie: `normversie`, `normhash`, `promptversie`, `routeringshash`, `provider` en `model`;
- de hashes `begrip_hash`, `kern_hash`, `bedoeling_hash`, `context_hash` (de drie lijsten per veldnaam) en `bronnen_hash` (ID én tekst, in de gegeven volgorde).

Elke hash is SHA-256 over canonieke JSON. Elke component afzonderlijk wijzigt precies zijn eigen bindingsveld; dat is per component getest, ook een wijziging die alleen witruimte in de kern betreft.

De gerapporteerde modelversie staat in `Uitvoering` en maakt deel uit van het document. Zij hoort niet bij de replayvergelijking, omdat zij vóór een nieuwe beoordeling onbekend is.

`Beoordelingsdocument` (frozen) bevat:
- `contractversie`, `invoer` (snapshot), `binding` en `uitvoering`;
- `status`, `reden`, `melding`, `vraag` en `foutcategorie`;
- `oordeel_json`: de canonieke JSON van de geaccepteerde uitvoer, of `None`.

`oordeel` levert telkens een verse kopie en `als_dict()` een JSON-serialiseerbare weergave. De meegegeven uitvoer wordt niet gemuteerd. Een afgewezen uitvoer wordt niet bewaard: `oordeel` is dan `None`.

`toets_actualiteit` volgt deze volgorde:
1. De actuele kern of context ontbreekt → NE.
2. Er is geen document → nog niet beoordeeld.
3. Het document is een technische fout, of **niet herleidbaar** → `error`. Herleidbaar betekent: de onderdelen worden opnieuw via hun constructors gevalideerd en `beoordeel` levert op de eigen invoer, de uit de binding afgeleide configuratie, de uitvoering en het oordeel exact hetzelfde document op. Een direct samengesteld document, een gewijzigde status, melding, invoer of binding, of een corrupte `oordeel_json` wordt zo nooit stil actueel.
4. De binding wijkt af van `bereken_binding(invoer, configuratie)` → historisch.
5. Anders → het bewaarde oordeel.

Het document zelf wordt nooit gewijzigd. Een recordidentiteit speelt geen rol: C118 laat zien dat een nieuwe tekstversie onder hetzelfde record het oude oordeel historisch maakt.

## Bewijsgrenzen

- **Geen persistentie.** Er is geen database, geen append-only historie en geen save/reload (DEF-626, WP5). De integriteitscontrole ontdekt incoherentie en gedeeltelijke mutatie. Een volledig consistent vervalst document is niet te onderscheiden van een document dat met hetzelfde oordeel opnieuw via `beoordeel` is gemaakt. Authenticiteit en herkomst zijn een verantwoordelijkheid van de opslaglaag.
- **Geen semantische modelkwaliteit.** De gevallen C06/C23/C56, C101, C105, C107, C112, C115, C116, C117 en C118 zijn ontwikkelgevallen met handmatig ingevulde responsen, geen goldset of hold-out. Een groene test bewijst contractgedrag, niet dat een model de juiste functie, passage, vraag of dekking kiest (WP4).
- **Geen app-route.** Er zijn geen prompt, service, evaluator, UI, publiek resultaatveld of schema; niets is geactiveerd. Actions blijven uit.
- **Mechanische vraagcontrole.** "Precies één vraag" is een vormcontrole; de code bewijst niet dat de vraag gericht is.
