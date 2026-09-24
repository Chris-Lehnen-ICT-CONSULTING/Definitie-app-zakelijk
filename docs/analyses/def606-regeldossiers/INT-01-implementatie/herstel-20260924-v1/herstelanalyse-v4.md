# DEF-770 — herstelanalyse v4 (afhandeling Astra/high-correctiereview)

Bron: `logs/def770-herstel/astra-correctiereview-v1.md`. R1 en R2 waren nog gedeeltelijk open (Important, fix-nu), met vier nabije tegenvoorbeelden. v1–v3 blijven ongewijzigd als bewijs. Gewijzigd zijn alleen `src/domain/int01/zinsgrenzen.py` en `tests/unit/validation/test_def770_herstel_zinsgrenzen.py`. De INT-01-normtekst (record, skills) veranderde niet.

## Gemeenschappelijke oorzaak

Beide regels behandelden het **ontbreken** van tegenbewijs als bewijs:
- **R1:** een onbekend eerste woord plus een werkwoordtoken gold als onderwerp plus persoonsvorm.
- **R2:** een voorzetselbegin, of een bijzinmarkering zonder herkende persoonsvorm, gold als voortzetting.

In beide gevallen bepaalde de woordlijst wat ontbrak, en dat is geen bewijs.

## R1 — correctie (`_bewezen_persoonsvorm`)

Een zekere grens na een punt met een kleine letter vraagt nu, naast de bestaande eisen (volledig woord ervoor, geen persoonsvorm of functiewoord vooraan, geen bijzinmarkering vóór de persoonsvorm), drie positieve kenmerken van een hoofdzin:
1. De persoonsvorm is ondubbelzinnig vervoegd. Tegenwoordige meervoudsvormen zijn gelijk aan de infinitief (`worden`, `kunnen`, …) en bewijzen dat niet.
2. Na de persoonsvorm volgt een aanvulling (hoofdzinvolgorde). `controle nodig is` kan een bijzinrest zijn.
3. Vóór de persoonsvorm staat geen werkwoordelijke woordvorm: geen voltooid deelwoord met `ge` (`toegepast`) en geen onvoltooid deelwoord op `-end(e)` (`uitsluitend`). Dit is een vormkenmerk, geen lijst met proefwoorden.

| Geval | v3 | v4 | Grond |
|---|---|---|---|
| `regeling. toegepast worden` | zeker (fout) | onzeker | 1 en 3 |
| `regeling. uitsluitend worden toegepast` | zeker (fout) | onzeker | 1 en 3 |
| `regeling. controles kunnen volgen` | zeker | onzeker | 1 |
| `regeling. uitsluitend wordt toegepast` | zeker | onzeker | 3 |
| `regeling. controle nodig is` | zeker | onzeker | 2 |
| `regeling. de controles werden uitgevoerd` | zeker | zeker | verleden meervoud is ondubbelzinnig |
| `regeling. toezicht is vereist` | zeker | zeker | positief |
| T24 `bundeling. controle volgens zqv. blijft vereist` | 1 zeker + 1 onzeker | ongewijzigd | positief |

## R2 — correctie (`_classificeer_citaatslot`, `_open_bijzin`)

Een slotteken direct vóór het sluitende aanhalingsteken, gevolgd door een kleine letter, geldt nu alleen als één formulering bij een **aantoonbare** voortzetting. Een herkende persoonsvorm in het vervolg sluit dat altijd uit. Twee vormen tellen als bewijs:
- **Korte slotwoordgroep:** een voorzetsel, hooguit een lidwoord en één woord (`“Gereed.” op het scherm`, `‘Wie betaalt?’ van de commissie`).
- **Bijzin vlak vóór het citaat**, met daarin tot het citaat alleen een lijdend voorwerp (markering plus hooguit lidwoord en één woord: `die de melding`). Het vervolg is dan alleen het slotwerkwoord (`… toont`) of begint met een voorzetsel (T17: `… op het oefenscherm laat verschijnen`).

Een onbekende persoonsvorm maakt zo geen voortzetting meer. `die eindigt met de melding` telt niet als open bijzin: het tussenliggende woord kan het werkwoord al zijn. Al het andere blijft onzeker, met passage en de positie van de punt.

| Geval | v3 | v4 |
|---|---|---|
| `… “Gereed.” voor gebruik is controle vereist` | geen grens, zinsstructuur pass (fout) | onzeker, positie van de punt |
| `code die eindigt met de melding “Gereed.” de controle volgt later` | geen grens, pass (fout) | onzeker |
| `code die de melding “Gereed.” de controle volgt later` | geen | onzeker |
| `code die de melding “Gereed.” voor gebruik is controle vereist` | geen | onzeker |
| `… “Gereed.” op het grote scherm` | geen | onzeker (conservatief) |
| `… “Gereed.” toont`, `… “Gereed.” op het scherm`, `“Gereed.” van de dienst` | geen | geen |
| T17, interne citaatpunctuatie, `‘Wie betaalt?’ van de commissie` | geen | geen (bestaande referenties) |

## Bewijs

- **Herstelkopie v3:** `logs/def770-herstel/herstelkopie-v3/`, bytegelijk gecontroleerd met `cmp`.
- **RED:** `r3-red-gericht-v1.log` en `.xml` — 81 tests, 11 failures, exit 1. Alle nieuwe negatieve gevallen falen; de positieve tegenhangers slagen.
- **GREEN:** `r3-green-gericht-v1.log` en `.xml` — 81 tests, 0 failures, exit 0.
- **Brede gate:** `r3-make-test-v1.log` en `r3-unit-junit-v1.xml` — exit 0, 7258 tests, 0 failures, 0 errors. `r3-make-lint-v1.log` — exit 0.
- **Correctiediffs:** `r3-correctiediff-zinsgrenzen-v1.patch` en `r3-correctiediff-test-v1.patch`.

## Grenzen (geen effectclaim, geen taalgarantie)

- Het blijft een conservatieve heuristiek op woordvormen. Een echte tweede zin zonder deze positieve kenmerken blijft onzeker. Voorbeelden: een persoonsvorm buiten de lijst, een onderwerp met een `ge`-vorm zoals `gebied`, een langere slotwoordgroep. Dat is bewust: zichtbaar onzeker in plaats van stil één zin of vals afgekeurd.
- De vormtest voor werkwoordelijke vormen kan een zelfstandig naamwoord als werkwoordelijk zien. Het effect is alleen een onzekere in plaats van een zekere grens.
- Bewijs van voortzetting na een citaat dekt alleen de twee beschreven vormen. Andere geldige voortzettingen worden onzeker getoond.
