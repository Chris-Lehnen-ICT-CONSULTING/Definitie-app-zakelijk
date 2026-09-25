# DEF-770 — herstelanalyse v8 (eindproef-correctie, contract /4)

Aanleiding: `logs/def770-herstel/astra-t24-vervolgbevinding-v1.md` plus de door de coördinator vastgestelde T23-afwijking. Bronnen onder `effectproeven-herstel-20260924-v1/`: `t24-contractcontrole-v1.json` (20/24 conform, bron `6c18ce71`), `t24-adjudicatie-v1.json` en `t24-resultaat-nieuw-v1.json`.

De onafhankelijke T24 is nu ontwikkelbewijs. Proeflabels, de set en de resultaten zijn niet gewijzigd. v1–v7 blijven ongewijzigd. Basis: HEAD `6c18ce7127f0a785fefdd6bc952175a030be8643`.

## Afwijkingen en oorzaak

| Geval | Normatief | Verwacht automatisch | App onder /3 | Oorzaak |
|---|---|---|---|---|
| T18 `register … (De beheerder wist deze na de oefening.)` | fail | review_required | pass | Na het sluitende haakje resteert geen tekst, dus de punt werd als slotteken weggefilterd. Er ontstond geen kandidaat, en daarmee kwam er een zinsstructuur-pass. |
| T23 `vak voor overdracht volgens nvr. Nieuwe routes krijgen voorrang` | review_required | review_required | fail | Een punt na een onbekend woord, gevolgd door een hoofdletter, gaf een zekere grens. Een afkortingsachtige vorm werd niet herkend. |
| T17 `code waarmee een bediener de melding 'De baan is vrij.' bevestigt` | pass | pass | onzeker | `_open_bijzin` keek alleen naar de laatste drie woorden (`bediener de melding`). |
| T20 `kaart bij de oefenhandleiding ‘Waar bleef de boot?’ voor het reconstrueren van een vaarvolgorde` | pass | pass | onzeker | Alleen één korte slotgroep (hooguit drie woorden) gold als bewijs. |

## Herstel (`src/domain/int01/zinsgrenzen.py`)

### 1. Slotteken van een haakjesdeel (T18)

**Regel.** Een `.`, `?` of `!` die direct een haakjesdeel van meer dan één woord sluit, wordt altijd kandidaat, ook als er daarna geen tekst volgt (`_sluit_haakjesdeel`). De classificatie (`_classificeer_haakjesslot`) is dan onzeker, met passage en positie. Er is nooit een automatische fail.

**Wat beschermd blijft:**
- Een punt die aantoonbaar bij een bekende afkorting hoort (functie `titel`, `verwijzing` of `afkorting`, zoals `(max. 5 st.)`) is geen zinspunctuatie.
- Een haakjesdeel van één woord (`(sic!)`) kan geen zelfstandige zin zijn.
- Een punt binnen een getal (`(lengte 2.5 cm)`) wordt niet gevolgd door witruimte of een sluiter en is geen kandidaat.
- Gewone haakjesbepalingen zonder slotteken (`(zonder bijlagen)`) veranderen niet.
- Een kern die geheel tussen haakjes staat telt als geheel, dus niet als ingesloten deel; het gedrag is ongewijzigd.
- Een citaat aan het eind (`… 'De baan is vrij.'`) is ongewijzigd één formulering.

**Bewuste gevolgen:**
- Een slotpunt ná een getal (`(zie art. 3.)`) en de mogelijk-zinsluitende afkortingen (`enz.`, `e.a.`) zijn onzeker. Zo'n punt hoort niet bij het getal en kan een zin tussen haakjes afsluiten.
- De regel geldt ook met vervolgtekst. Een vraag- of uitroepteken dat midden in de tekst een meerwoordig haakjesdeel sluit, was eerder "geen grens" bij een kleine letter erna en is nu onzeker. Dat is conservatief: nooit een fail.

### 2. Afkortingsachtige woordvorm zonder klinker (T23)

**Regel.** Staat vóór een punt met een hoofdletter of cijfer erna een woord van twee of meer kleine letters zonder klinker (a, e, i, o, u, y), dan is de grens onzeker in plaats van zeker (`_ZONDER_KLINKER`). Zo'n vorm is geen gewoon Nederlands woord, dus de punt kan bij een afkorting horen.

**Bewijs van bescherming** (tegenhangers blijven zeker fail):
- `regeling. Nieuwe …` en `rit. Nieuwe …`: woorden met een klinker.
- `NVR. Nieuwe …`: een acroniem in hoofdletters schrijft men zonder punt.

**Wat er niet is:** geen corpuswoord, geen woordenlijst, geen parser.

**Bewust gevolg:** een eenheid als `5 mm. De …` wordt onzeker. Een punt met kleine letter erna bleef al onzeker.

### 3. Ingebed citaat of titel (T17, T20)

**Bijzin vóór het citaat** (`_open_bijzin`, T17). Tussen een bijzinmarkering en het citaat mogen nu één of meer naamwoordgroepen `de`/`een` + één woord staan (`waarmee een bediener de melding`). De onderbouwing blijft die van r4: `de` en `een` kunnen geen zelfstandig voornaamwoord zijn, dus elk woord erna is een naamwoordkern. Elk woord tussen markering en citaat is zo verklaard. Een kernwoord dat zelf een lidwoord, voorzetsel of markering is, telt niet.

Negatieve tegenhangers (alle onzeker):
- `een bediener meldt` (los woord, mogelijk werkwoord);
- `het team` (`het` kan een voornaamwoord zijn);
- geen markering (`met een bediener …`);
- een nieuwe woordgroep na het citaat (`… de controle volgt`).

**Vervolg na het citaat** (`_voorzetselgroepen`, vervangt `_korte_slotgroep`, T20). Het vervolg mag bestaan uit één of meer voorzetselgroepen: telkens een voorzetsel, hooguit een lidwoord en één kernwoord. Elk woord is dan verklaard en er is geen plek voor een persoonsvorm. De uitsluiting van een herkende persoonsvorm blijft gelden.

Negatieve tegenhangers (alle onzeker):
- `… voor het reconstrueren is controle vereist`;
- een onvolledige groep (`… van een`);
- een woord buiten een groep (`voor de oefening volgt de controle`);
- een bijvoeglijk naamwoord in de groep (`voor het grote reconstrueren`, zoals de bestaande r3-lange-pp).

**Wat er niet is:** geen verruimd venster, geen lengtegrens, geen corpuswoorden. De grens is structureel: alleen de reeks `(voorzetsel [lidwoord] kern)+`, respectievelijk markering + `(de|een kern)+`.

**Grens die bewust niet is overschreden:**
- Naamwoordgroepen met een bijvoeglijk naamwoord of een meerwoordige kern (`op het grote scherm`, `die de rode melding …`) blijven onzeker.
- Er is geen woordsoortkennis om een bijvoeglijk naamwoord van een werkwoord te onderscheiden. Een verdere verbreding valt buiten dit conservatieve mandaat.

### 4. Contractversie

`CONTRACTVERSIE = "def770-int01/4"`: /3 is gepusht en proefbron, en de beslisbetekenis wijzigt. Opgeslagen uitkomsten onder /1, /2 en /3 gelden via de bestaande binding niet als actueel. Dat is getest, onder meer op E_T18 (onder /3 zinsstructuur-pass) en E_T23 (onder /3 fail).

De punt+kleineletteronzekerheid uit uitwerking-v2 is ongewijzigd.

## Tests (`tests/unit/validation/test_def770_herstel_zinsgrenzen.py`)

- **Segmentatie:** de vier T24-teksten, met per geval de tegenhangers hierboven (sectie `e1-*`).
- **Passage en positie:**
  - `test_e1_t18_…`: de positie op `.` in `.)`, passage `oefening.)`, en de reden noemt haakjes.
  - `test_e1_t23_…`: de positie na `nvr`, en de reden noemt de afkorting.
- **Service, beide laadpaden:** E_T17 en E_T20 geven zinsstructuur-pass, E_T18 en E_T23 een onzekere grens; de regelstatus is steeds `review_required`.
- **Opslag en teruglezen:** alle vier.
- **Oude contractversie:** /1, /2 en /3 × {T24, zeker-fail, E_T18, E_T23} gelden niet als actueel.
- **Contractversie:** `test_contractversie_is_4_…`.

`test_def770_int01_zinsgrenzen.py` is niet gewijzigd (bytegelijk aan de herstelkopie) en is groen.

## Bewijs (logs onder `logs/def770-herstel/`)

- **Herstelkopie:** `herstelkopie-eindproef-correctie-v1/`, met zinsgrenzen.py, twee testbestanden en de toetsregels-reference; vier bestanden `cmp`-gelijk vóór de edits.
- **RED** op de ongewijzigde bron: `eindproef-correctie-v1-red.log` en `.xml` — 239 tests, 25 failures, exit 1. Alle failures zitten op de nieuwe verwachtingen; de negatieve tegenhangers slaagden al.
  - Na RED zijn twee testverwachtingen aangepast. `(zie art. 3.)` ging van 0/0 naar 0/1, omdat een slotpunt ná een getal geen getalpunt is. Er kwamen twee beschermingsgevallen bij: `(lengte 2.5 cm)` en `(max. 5 st.) per proef`.
  - Dat die aangepaste verwachting op de oude bron faalt, is afgeleid (de oude bron maakt aan het eind geen kandidaat) en niet afzonderlijk gemeten.
- **GREEN:** `eindproef-correctie-v1-green.log` en `.xml` (241 tests, 0 failures). Na de opmaakaanpassing: `eindproef-correctie-v1-green-definitief.log` en `.xml` — 241 tests, 0 failures, exit 0.
- **Lint:** `eindproef-correctie-v1-make-lint.log` — ruff en black op `src/` en `config/`, exit 0.
- **Diffs:** `eindproef-correctie-v1-appdiff.patch` (ten opzichte van `6c18ce71`) en `eindproef-correctie-v1-skillsdiff.patch`.
- **Skills:** in `definitie-toetsregels/reference.md` is de versieregel `/3` → `/4` gewijzigd; de rest van de zin blijft juist.

## Niet gedaan / voor root

- Ruff en black op het testbestand (de uvx-commando's vragen goedkeuring); de brede gate; de herbouw van de skillsbundels.
- De offline evaluator opnieuw toetsen op T24 (contractcontrole) en G24 met de /4-bron. De G24-prompts, -instellingen en -providerantwoorden blijven onveranderd. Ik heb geen proefdata buiten de genoemde T24-bestanden ingezien, geen generatiecalls gedaan en geen nieuwe set gemaakt.
- Geen effectclaim. Het herstel is gericht op de vier afwijkingen; of de volledige T24 nu conform is, moet de rootcontrole vaststellen.
