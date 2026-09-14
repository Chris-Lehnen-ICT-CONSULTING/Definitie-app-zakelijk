# DEF-622 — eerste vaststeldelta

Dezelfde onafhankelijke reviewer beoordeelde `c8879ec70..e9ecf6c09`.
V1 (synoniemenuniciteit), V3 (actorherkomst) en V4 (dubbele/misvormde markers)
zijn opgelost binnen hun oorspronkelijke scope. V2 blijft Important en krijgt
opnieuw dispositie **fix nu**, met drie concrete resterende gevallen:

| ID | Gedrag op e9ecf6c09 | Herstel |
|---|---|---|
| V2a | Oude reviewversie 2 wordt na tekst wijzigen/terugzetten op recordversie 4 opnieuw aangeboden; opslag stempelt versie 5 en vaststelling slaagt. | Oorspronkelijke beoordeelde versie onder de lock controleren vóór mutatie. |
| V2b | Publieke update slaat een verder geldige marker met ontbrekende versie, None, True, lijst, dict, ongeldige tekst of 2.5 op; vaststelling slaagt. | Bij een versiegebonden record is ontbrekende/ongeldige reviewversie blokkerend. |
| V2c | Review/record 2/2 geeft pass; na vaststelling record 3/review 2 en CON-gate blocked. | Consistente lokale reviewbinding atomair behouden bij uitsluitend de statusversiebump. |

Dit betreft lokale CON-reviewopslag/readback, geen nieuwe algemene
DEF-630-snapshot- of exportvoorwaarde. Nieuwe reviewopslag is wel bruikbaar;
wijzigen en terugzetten blokkeert het opgeslagen oordeel totdat V2a het onterecht
opnieuw geldig maakt. Een andere latere vaststeller blijft toegestaan.

Concurrencybewijs is nu onderscheidend: A houdt de schrijftransactie vast tot
B zijn BEGIN IMMEDIATE bereikt; geen sleeps, beide threads eindigen, alleen A
slaagt en één leider blijft over. Coördinator: 84 tests, nul failures/errors/skips,
exit 0 op exacte snapshot (bronbinding `coordinator-establish-fix-source.json`,
JUnit/log `coordinator-establish-fix.xml`/`.log` onder `reports/def622`).
Reviewer controleerde 491 bytegelijke bestanden en deed eigen geheugenproeven.

Volledig lokaal oordeel:
`/private/tmp/DEF-622-codex-establish-deltareview-v1-result.md`.
V2a–V2c zijn aan dezelfde Claude-sessie toegewezen; andere gesloten bevindingen
worden niet opnieuw uitgewerkt. Na herstel volgt beperkte deltaverificatie.
