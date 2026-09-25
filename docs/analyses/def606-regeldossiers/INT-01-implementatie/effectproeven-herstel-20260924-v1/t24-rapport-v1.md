# T24 — eerste proef van de conservatieve kandidaat /3

24 september 2026 · bron `6c18ce7127f0a785fefdd6bc952175a030be8643`.

**20/24 conform; de criteria zijn niet gehaald.** De vooraf verzegelde normatieve en automatische referenties blijven ongewijzigd. Dit is een synthetische proef, beoordeeld door afzonderlijke Astra/high-sessies voor maker, A, B en adjudicator. Er is geen menselijke validatie.

## Resultaat

De app neemt 19 automatische beslissingen op 23 niet-lege teksten (82,61%): 13 zins-passes en 6 fails. Vier gevallen worden doorverwezen; één lege tekst wordt niet beoordeeld. Van de 19 automatische beslissingen sluiten er 17 aan bij de normatieve referentie. T18 is ten onrechte pass en T23 onvoldoende onderbouwd fail. Deze kleine steekproef geeft geen algemene betrouwbaarheidsclaim.

De vier doorverwijzingen betreffen normatief twee eenzinsgevallen, één onzeker geval en één meerzinsgeval. Dat laatste (T24, kleinelettergrens) volgt het vooraf afgesproken conservatieve beleid. Bij T17/T20 verwijst de app meer door dan vooraf verwacht. De beoordelaars waren het over alle statussen eens; adjudicatie koos bij twee gevallen een ruimere exacte passage. Er zijn geen onopgeloste disputen.

Beide laadpaden geven bij 24/24 gevallen dezelfde uitkomst. Opslag en teruglezen zijn bij 24/24 conform. Er zijn geen uitvoeringsfouten en nergens een volledige INT-01-pass. Compactheid en begrijpelijkheid blijven afzonderlijk open; deze proef beoordeelt die niet.

| Geval | Normatief | Automatisch verwacht | App |
|---|---|---|---|
| T01 | pass | pass | pass |
| T02 | pass | pass | pass |
| T03 | pass | pass | pass |
| T04 | pass | pass | pass |
| T05 | pass | pass | pass |
| T06 | pass | pass | pass |
| T07 | pass | pass | pass |
| T08 | fail | fail | fail |
| T09 | pass | pass | pass |
| T10 | fail | fail | fail |
| T11 | fail | fail | fail |
| T12 | fail | fail | fail |
| T13 | pass | pass | pass |
| T14 | fail | fail | fail |
| T15 | pass | pass | pass |
| T16 | pass | pass | pass |
| T17 | pass | pass | review_required |
| T18 | fail | review_required | pass |
| T19 | pass | pass | pass |
| T20 | pass | pass | review_required |
| T21 | not_evaluated | not_evaluated | not_evaluated |
| T22 | review_required | review_required | review_required |
| T23 | review_required | review_required | fail |
| T24 | fail | review_required | review_required |

## Bevindingen en dispositie

- **T17:** expliciet ingebedde melding; app onzeker waar pass verwacht. Conservatieve dekkingsgrens, wel een onvervulde proefverwachting.
- **T18:** zelfstandige zin tussen afsluitende haakjes verdwijnt uit de kandidaatselectie doordat buiten het haakje geen tekst meer volgt; onterechte zins-pass. Important, fix-nu, bevestigd door dezelfde Codex CLI-reviewer.
- **T20:** titel gevolgd door een langere bepalende woordgroep; app onzeker waar pass verwacht. Conservatieve dekkingsgrens, wel een onvervulde proefverwachting.
- **T23:** onbekende afkorting voor een hoofdletter wordt zeker fail; onzekerheid is vereist volgens beide referenties en de adjudicator. Fix-nu aan Claude toegewezen.

Claude kreeg deze vier concrete bevindingen in `logs/def770-herstel/claude-eindproef-correcties-opdracht-v1.md`. Een correctie maakt deze set ontwikkelbewijs; een verse onafhankelijke T24 is dan nodig. Geen resultaten of referenties worden achteraf aangepast. De inhoudelijke G24 blijft gebonden aan dezelfde ongewijzigde generatieprompts en antwoorden. Bij een classifiercorrectie wordt de automatische beoordeling afzonderlijk opnieuw uitgevoerd.

## Bewijs

- [Verzegeling vóór uitvoering](t24-verzegeling-v1.json)
- [Onafhankelijke adjudicatie](t24-adjudicatie-v1.json)
- [Nieuwe appuitvoer](t24-resultaat-nieuw-v1.json) en [oude appuitvoer](t24-resultaat-oud-v1.json)
- [Vergelijking per geval](t24-contractcontrole-v1.json)
- [Bron- en setbinding](bron-en-setbinding-v1.json)
- [Gerichte onafhankelijke bevindingstoets](../herstel-20260924-v1/astra-t24-vervolgbevinding-v1.md)

De historische eerste proef (18/24) is niet herberekend of vervangen. Deze proef hanteert de vooraf vastgelegde scheiding tussen normatieve waarheid en automatische verwachting; de scores zijn daarom geen rechtstreekse vergelijking van dezelfde maatstaf.
