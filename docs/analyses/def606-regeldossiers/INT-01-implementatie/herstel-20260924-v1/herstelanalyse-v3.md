# DEF-770 — herstelanalyse v3 (afhandeling Astra/high-appreview)

Bron: `logs/def770-herstel/astra-appreview-v1.md`, met twee bevestigde Important-regressies (R1, R2), beide fix-nu. v1 en v2 blijven ongewijzigd als bewijs. v3 vervangt uit v2 alleen de beschrijving van de kleine-letterregel (§2, voorwaarde 2) en de citaatregel. De rest van v2 blijft geldig.

## R1 — een werkwoordtoken bewijst geen zelfstandige zin

**Oorzaak.** In v2 gold ieder genoemd werkwoord na het eerste token als bewijs van een eigen onderwerp. Daardoor werden `regeling. om te worden toegepast` (infinitief), `regeling. die kan worden toegepast` (bijzin) en `regeling. zonder de verplichting die blijft gelden` (voorzetselvervolg met betrekkelijke bijzin) een zekere tweede zin.

**Correctie** (`_eigen_onderwerp_en_persoonsvorm`). De zekerheid vraagt nu positief bewijs. Het vervolg begint met een onderwerp, dus niet met een persoonsvorm, voorzetsel, voegwoord, betrekkelijk voornaamwoord of `om`/`te`. De eerste persoonsvorm volgt bovendien zonder tussenliggende bijzin- of infinitiefmarkering, en staat niet direct na `te`. In alle andere gevallen blijft de grens onzeker. Het blijft een conservatieve heuristiek op woordvormen, geen taalgarantie.

| Geval | v2 | v3 |
|---|---|---|
| `regeling. om te worden toegepast` | zeker (fout) | onzeker |
| `regeling. die kan worden toegepast` | zeker (fout) | onzeker |
| `regeling. zonder de verplichting die blijft gelden` | zeker (fout) | onzeker |
| `regeling. controle die blijft vereist` | zeker | onzeker |
| `regeling. de controle blijft vereist` | zeker | zeker |
| T24 `bundeling. controle volgens zqv. blijft vereist` | 1 zeker + 1 onzeker | ongewijzigd |
| `voorz.`-gevallen, `object. heeft …`, `proefwand. …` | onzeker | ongewijzigd |

## R2 — citaatafsluiting kan ook een buitenste grens zijn

**Oorzaak.** In v2 gold elk slotteken binnen een ingesloten citaat als "geen grens" zodra het vervolg klein begon, ook als het direct vóór het sluitende aanhalingsteken stond. Daardoor kreeg `code met de melding “Gereed.” controle blijft vereist` nul grenzen, en werd het zinsstructuurdeel `pass`.

**Correctie.** Het onderscheid is nu:
- **Interne citaatpunctuatie** (het slotteken staat niet direct vóór het sluitende aanhalingsteken): geen grens (T17, `“Beleid. Uitvoering”`).
- **Citaatafsluiting met een kleine letter erna** (`_classificeer_citaatslot`): alleen één formulering bij een duidelijke voortzetting. Dat is een vervolg dat met een voorzetsel, voegwoord of bijzinmarkering begint, of een buitenste bijzin die vóór het citaat is geopend en nog op haar persoonsvorm wacht (`code die de melding “Gereed.” toont`). Een vervolg met eigen onderwerp en persoonsvorm en elk onbeslist vervolg blijven **onzeker**, met passage en reden.
- **Citaatafsluiting met een hoofdletter of cijfer erna**: ongewijzigd onzeker.

| Geval | v2 | v3 |
|---|---|---|
| `code met de melding “Gereed.” controle blijft vereist` | geen grens, zinsstructuur pass (fout) | onzeker |
| `code met de melding “Gereed.” controle volgens protocol` | geen grens | onzeker |
| `code met de melding “Gereed.” Controle blijft vereist` | onzeker | onzeker |
| `code die de melding “Gereed.” toont` | geen | geen |
| `code met de melding “Gereed.” op het scherm` | geen | geen |
| T17, `'Stop. Ga.' op het scherm toont`, `‘Wie betaalt?’ van de commissie` | geen | geen (bestaande referenties) |

## Tekstafstemming

- App: de moduledocstring van `zinsgrenzen.py` en de toelichting in `INT-01.json` beweren niet meer dat leestekens in een citaat nooit een buitenste grens zijn. Ze onderscheiden interne punctuatie van de afsluiting, en de docstring noemt de kleine-letterregel een heuristiek.
- Skills: in beide `reference.md`'s dezelfde citaatnuance. In `toetsregels/reference.md` staat nu "moet opnieuw worden getoetst voordat zij als actueel kan gelden", omdat de app bij alleen lezen niet automatisch opnieuw toetst.
- Contractversie blijft `def770-int01/2`: de herstelversie is nog niet gecommit of uitgerold.
- Beide `SKILL.md`'s: gecontroleerd en ongewijzigd gelaten. Ze verwijzen voor INT-01 naar de referentie en bevatten geen tegenstrijdige citaat- of hertoetstekst.

## Resterende grenzen (niet opgelost, geen effectclaim)

- De onderwerp- en persoonsvormbepaling werkt met gesloten woordlijsten. Een zelfstandige zin met een persoonsvorm buiten de lijst, of met een onderwerp dat met een lijstwoord begint (`volgens de wet blijft …`), blijft onzeker. Dat is bewust conservatief.
- `_open_bijzin` herkent een geopende bijzin aan een markering zonder persoonsvorm uit de lijst erna. Staat de persoonsvorm van die bijzin niet in de lijst, dan kan een citaatafsluiting ten onrechte als voortzetting gelden, maar alleen als het vervolg zelf geen eigen onderwerp en persoonsvorm draagt.
