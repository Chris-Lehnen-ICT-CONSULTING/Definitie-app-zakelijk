# DEF-770 — herstelanalyse v5 (r4, derde gerichte herstelpoging R1/R2)

Bron: `logs/def770-herstel/astra-correctiereview-v2.md`. Er waren drie Important-bevindingen: R1, R2 en een IndexError (R3). v1–v4 blijven ongewijzigd. Gewijzigd zijn alleen `src/domain/int01/zinsgrenzen.py` en `tests/unit/validation/test_def770_herstel_zinsgrenzen.py`. Normtekst (JSON, skills, promptbuilder) en historische proeflabels zijn niet gewijzigd.

## Kernoorzaak (R1 en R2)

Beide regels verklaarden onbekende syntaxis zeker via uitsluiting: "geen werkwoordelijke vorm" gold als onderwerp, en "geen herkend werkwoord" gold als voortzetting. r4 vervangt dat door een **positief** patroon, zonder uitzonderingslijst van bijwoorden of proefwoorden. Alles buiten die patronen is onzeker.

## R1 — positief toegelaten onderwerp (`_onderwerp_herkend`)

Een punt met een kleine letter erna telt als zekere grens alleen als naast de bestaande eisen één van deze patronen vóór de persoonsvorm staat. De bestaande eisen zijn: volledig woord vóór de punt, ondubbelzinnig vervoegde persoonsvorm met aanvulling, geen bijzin- of infinitiefmarkering en geen deelwoordvorm.

- **P1 — lidwoordgroep:** `de/het/een/deze/dit/elke/ieder/iedere/alle` plus ten minste één woord (`de controle blijft vereist`).
- **P2 — één woord met een eigen voorzetselgroep:** woord, voorzetsel en ten minste één inhoudswoord (`controle volgens zqv. blijft vereist`, `toezicht op naleving is vereist`). De onderbouwing is dat in een hoofdzin één zinsdeel vóór de persoonsvorm staat. Een bijwoord vormt samen met een voorzetselgroep geen zinsdeel, dus het woord is de kern van een naamwoordgroep.

**Bewust onzeker:** elk kaal woord direct vóór de persoonsvorm, ongeacht de woordsoort. Bijvoorbeeld `opnieuw wordt toegepast`, `nog wordt toegepast`, `daarna wordt controle uitgevoerd` (een echte hoofdzin, toch onzeker) en `toezicht is vereist`. Dit is een grammaticale klasse (onbewezen onderwerp), geen bijwoordenlijst. Ook `toezicht op is vereist` (voorzetsel zonder voorwerp) blijft onzeker.

**Gewijzigde eigen verwachtingen (geen proeflabels):** drie van mijn eigen tegenhangers uit r2/r3 met een kaal onderwerp direct vóór de persoonsvorm zijn nu onzeker. Het gaat om `toezicht is vereist` en `controle blijft vereist`. Ze zijn vervangen door positieve varianten met een lidwoord. T24 (`bundeling. controle volgens zqv. blijft vereist` → 1 zeker, 1 onzeker, `fail`) blijft ongewijzigd via P2.

### Acceptatiegrens R1 (expliciet)

T24 is alleen haalbaar via P2. P2 berust op de aanname dat de tekst een grammaticaal correcte hoofdzin is. Bij ongrammaticale tekst in de vorm "bijwoord + voorzetselgroep + persoonsvorm" (bijvoorbeeld `regeling. opnieuw volgens protocol wordt toegepast`) geeft P2 nog steeds een zekere grens. Lexicaal zijn `controle volgens zqv.` en `opnieuw volgens protocol` zonder woordsoortinformatie niet te onderscheiden.

Dit risico is dus **niet** opgelost. Het ligt uitsluitend bij ongrammaticale invoer met een gefronte voorzetselgroep. Het volledig uitsluiten vraagt een lexicon of woordsoortbepaling (niet toegestaan: geen dependencies) of het loslaten van het T24-label (niet aan mij). Ik heb dit geval niet als test vastgelegd, om geen fout gedrag te betonneren. Keuze voor de coördinator: P2 accepteren met deze grens, of T24 als niet verantwoord haalbaar markeren.

## R2 — positief bewezen voortzetting na een citaatslot

**Open bijzin (`_open_bijzin`).** Alleen markering + `de`/`een` + één woord telt (`die de melding`). `de` en `een` kunnen geen zelfstandig voornaamwoord zijn, dus het woord erna is een naamwoord en niet het werkwoord van de bijzin. `die meldt` en `die het meldt` bewijzen niets meer.

**Vervolg.**
- Na een bewezen open bijzin: het slotwerkwoord alleen (`… toont`), of een vervolg dat met een voorzetsel begint (T17 `… op het oefenscherm laat verschijnen`, `… na gebruik toont`).
- Zonder open bijzin: alleen een volledige korte slotgroep (`op het scherm`, `van de dienst`).

Een herkende persoonsvorm in het vervolg of een vervolg dat eindigt op een los voorzetsel of lidwoord maakt de voortzetting altijd onbewezen.

| Geval | r3 | r4 |
|---|---|---|
| `code die meldt “Gereed.” na gebruik volgt controle` | pass (fout) | onzeker, positie van de punt |
| `code die het meldt “Gereed.” na gebruik volgt` | geen | onzeker |
| `code die het meldt “Gereed.” op het scherm` | geen | geen (korte slotgroep) |
| `code die de melding “Gereed.” na gebruik toont` | geen | geen |
| `code die een melding “Gereed.” toont` | geen | geen |
| T17, `… toont`, `… op het scherm`, `‘Wie betaalt?’ van de commissie` | geen | geen (ongewijzigd) |

**Resterende grens R2.** Na een bewezen open bijzin plus een voorzetselbegin geldt het vervolg als voortzetting. De onderbouwing: een open bijzin vraagt nog haar werkwoord, dus in correcte tekst kan de buitenste zin niet bij het citaat eindigen. Dat berust eveneens op de aanname van een correcte zin.

## R3 — onvolledige voortzetting (`_korte_slotgroep`)

De tokenlengte wordt nu vóór elke index gecontroleerd. Deze gevallen zijn onzeker met passage en positie, zonder uitzondering:
- `… “Gereed.” op`
- `… op de`
- `… op het`
- `… –` (geen woord)

## Bewijs (logs onder `logs/def770-herstel/`)

- **Herstelkopie v4:** `herstelkopie-v4/`, bytegelijk gecontroleerd met `cmp`.
- **RED:** `r4-red-gericht-v1.log` en `.xml` — 99 tests, 13 failures (waaronder de IndexError), exit 1.
- **GREEN:** `r4-green-gericht-v1` en, op de eindbron na een opmaakcorrectie, `r4-green-gericht-v2` — 99 tests, 0 failures, exit 0.
- **Lint:** `r4-make-lint-v1.log` faalde op black-opmaak; na een opmaakcorrectie zonder functiewijziging is `r4-make-lint-v3.log` exit 0.
- **Brede gate:** `r4-make-test-v1.log` (exit 0, 7276 tests, 0 failures) liep vóór die opmaakcorrectie. `r4-make-test-v2.log` op de eindbron: zie het eindrapport.
- **Correctiediffs:** `r4-correctiediff-zinsgrenzen-v1.patch` en `r4-correctiediff-test-v1.patch`.

Geen effectclaim en geen taalgarantie.
