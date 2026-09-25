# T24 — verse onafhankelijke proef van contract /4

24 september 2026 · bron `c7f5d7dc921740f85a10d932480da338f9c2c276`.

**22/24 volledig conform; 23/24 juiste automatische statuslabels. Het vooraf vastgelegde 24/24-criterium is niet gehaald.** Er zijn in deze set geen onterechte zekere automatische zinsbesluiten. De referenties, criteria en invoer zijn na uitvoering niet aangepast.

## Opzet en afbakening

Een nieuwe Astra/high-maker stelde 24 nieuwe synthetische gevallen op, verdeeld over zes strata. De maker kende de code en eerdere mislukkingen niet. De set ging pas na bronbevriezing naar twee nieuwe onafhankelijke Astra/high-beoordelaars, die uitsluitend het generieke contract en de teksten kregen. Een nieuwe adjudicator beslechtte de verschillen vóór appuitvoering. Alle vier rollen gebruikten geen tools. Er zijn geen onopgeloste referentiedisputen. Dit zijn AI-beoordeelde gevallen, geen menselijke validatie.

De ongewijzigde, eerder gereviewde runner voerde oud en nieuw uit op bronarchieven met vastgelegde commits. De oude arm is `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`. Die mist het nieuwe deelcontract; de oude regelstatussen staan in het bewijs, maar worden niet als rechtstreeks vergelijkbare volledige contractscore gepresenteerd.

## Uitkomsten

- 10 automatische zins-passes en 8 automatische fails: **18/23 automatische dekking, 78,26%** van de niet-lege teksten. Alle 18 sluiten aan bij de normatieve referentie.
- 5 doorverwijzingen: normatief 2 eenzinsgevallen, 1 meerzinsgeval en 2 onzekere gevallen. Eén tekst is leeg en wordt niet beoordeeld.
- 48 serviceobservaties: beide laadpaden bij 24/24 gelijk. Opslag en teruglezen bij 24/24 conform, inclusief tekstbinding en contract `/4`.
- Geen uitvoeringsfouten; nergens volledige INT-01-pass. Compactheid en begrijpelijkheid blijven afzonderlijk open. Een zins-pass bewijst die niet.

| Geval | Normatief | Automatisch verwacht | App | Volledig conform |
|---|---|---|---|---|
| T01 | pass | pass | pass | ja |
| T02 | pass | pass | pass | ja |
| T03 | pass | pass | pass | ja |
| T04 | fail | fail | fail | ja |
| T05 | pass | pass | pass | ja |
| T06 | fail | fail | fail | ja |
| T07 | pass | pass | pass | ja |
| T08 | fail | fail | fail | ja |
| T09 | pass | pass | pass | ja |
| T10 | fail | fail | fail | ja |
| T11 | fail | fail | fail | ja |
| T12 | fail | fail | fail | ja |
| T13 | pass | pass | pass | ja |
| T14 | fail | fail | fail | ja |
| T15 | pass | pass | pass | ja |
| T16 | pass | pass | pass | ja |
| T17 | pass | review_required | review_required | ja |
| T18 | fail | fail | fail | ja |
| T19 | pass | pass | pass | ja |
| T20 | pass | pass | review_required | nee |
| T21 | not_evaluated | not_evaluated | not_evaluated | ja |
| T22 | review_required | review_required | review_required | ja |
| T23 | fail | review_required | review_required | ja |
| T24 | review_required | review_required | review_required | nee |

## Resterende afwijkingen

### T20 — onnodige inhoudelijke beoordeling

> Spelkaart met de titel ‘Wie woont hier?’ waarop aanwijzingen voor een fictief dierverblijf staan.

Beide referenties en adjudicatie verwachten een zins-pass: de vraag is expliciet een titel binnen één doorlopende formulering. De app meldt onzekerheid bij het citaatslot. Dit veroorzaakt extra beoordeling, geen onterechte zekere afkeur. Het blijft een onvervulde acceptatieverwachting.

### T24 — status klopt, reden niet

> Bak voor onderdelen met een vakcode (v.qr. = vakcodering voor quicksortering) v.qr. bepaalt het sorteervak

De referentie verlangt inhoudelijke beoordeling vanwege de onduidelijke aansluiting tussen de naamwoordelijke kern en het vervolg. De afkorting is in de tekst verklaard; adjudicatie sluit de interne afkortingspunten uit als zelfstandige grensargumenten. De app verwijst wel door, maar motiveert dat juist met deze punten: een punt vóór `=` en een punt vóór een kleine letter. Daarom is alleen het statuslabel conform. De gebruiker krijgt een verkeerde verklaring van de twijfel.

### T18 — extra signaal naast juiste fail

De gewone grens in `zaaibak. (De omhulling` levert terecht fail op. Daarnaast meldt de app een onzekerheid bij het einde van het haakjesdeel. Dit verandert de uitkomst niet. De gerichte reviewerdispositie is afzonderlijk opgenomen; deze dubbele diagnostiek is niet stilzwijgend als een derde fout meegeteld.

## Betekenis voor oplevering

De eerdere bekende herstelset haalt op `/4` 24/24 **statuslabels**. Dat is ontwikkelregressie en geen onafhankelijke effectwinst. Deze verse set is de eindproef; de score wordt niet vervangen door die van de bekende set. De kleine, verschillend samengestelde sets leveren geen trend of algemene nauwkeurigheid op.

De code is gereviewd en technisch getest, maar acceptatievrijgave is niet bereikt. Daarnaast faalt G24 op betekenisbehoud. Er volgt geen merge, liveactivatie of algemene kwaliteitsclaim op basis van dit bewijs. De beoordelingscriteria blijven staan.

## Bewijs

- [Bron en set](bron-en-setbinding-v1.json), [verzegeling vóór uitvoering](verzegeling-v1.json), [adjudicatie](adjudicatie-v1.json)
- [Appuitvoer nieuw](resultaat-nieuw-v1.json), [appuitvoer oud](resultaat-oud-v1.json), [volledige vergelijking](contractcontrole-v1.json)
- [Gerichte bevindingstoets door dezelfde Codex CLI-reviewer](bevindingstoets-v1.md)
- [G24-uitkomst](../g24-rapport-v1.md) en [herbinding aan contract /4](../g24-contract4-binding-v1.json)
