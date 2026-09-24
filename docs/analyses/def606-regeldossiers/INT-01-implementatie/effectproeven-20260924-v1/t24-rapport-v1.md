# T24 — resultaat van de onafhankelijke AI-beoordeelde proef

24 september 2026 · DEF-770 · uitgevoerd na merge van app-PR #473 en skills-PR #355.

## Uitkomst

**Het vooraf vastgelegde criterium van 24/24 is niet gehaald: 18/24 voldoen aan het volledige toetscontract.** Er zijn zes bevindingen. De app en de vooraf verzegelde referenties zijn tijdens deze proef niet aangepast.

| Onderdeel | Resultaat |
|---|---|
| Overeenkomst van het totale regellabel | 23/24 |
| Overeenkomst van de zinsstructuurdeelbeoordeling | 19/24, inclusief het lege geval; 18/23 niet-lege gevallen |
| Volledig toetscontract, inclusief open broncitaatonderdeel | 18/24 |
| INT-01 onterecht als volledig geslaagd opgenomen | 0/24 |
| Compactheid en begrijpelijkheid afzonderlijk open | 23/23 niet-lege gevallen |
| Twee laadpaden geven identieke INT-01-uitvoer | 24/24 per variant |
| Nieuwe niet-lege opslag en teruglezen | 23/23 identieke status en onderdelen; tekst gelijk |

Bij het lege geval is de service-uitkomst `not_evaluated` zonder `rule_result`; de repository bewaart een eigen `not_evaluated`-beoordeling. Hiervoor is geen gelijkheid van onderdelen geclaimd. Beide runners eindigden met exitcode 0 en nul uitvoeringsfouten. Dat betekent dat de proef technisch is uitgevoerd; de inhoudelijke toets slaagt daarmee niet automatisch.

## Bevindingen

| Geval | Afwijking ten opzichte van de vaste referentie |
|---|---|
| T15 | Opsomming binnen één kern wordt onzeker beoordeeld. |
| T17 | Ingesloten citaat leidt tot onzekerheid over de buitenste zin. |
| T19 | Bij een gehele kern tussen typografische aanhalingstekens ontbreekt het open onderdeel `broncitaat`. |
| T22 | Los label krijgt een te stellig positief zinsstructuuroordeel. |
| T23 | Beletselteken met voortzetting mist de verwachte onzekerheid. |
| T24 | Zekere tweede zin met kleine beginletter wordt onzeker beoordeeld; het oude regellabel was hier wel passend `fail`. |

Alle zes zijn vastgelegd voor vervolg. T24 is een verslechtering van het regellabel ten opzichte van de vaste referentie. De nieuwe totale oordelen blijven open; er is in deze proef geen onterechte volledige INT-01-goedkeuring. De bevindingen zijn niet achteraf weggelabeld of stil gerepareerd.

## Alle 24 gevallen

| Geval | Referentie zinsstructuur | Nieuwe zinsstructuur | Nieuw volledig conform |
|---|---|---|---|
| T01 | pass | pass | ja |
| T02 | pass | pass | ja |
| T03 | pass | pass | ja |
| T04 | pass | pass | ja |
| T05 | pass | pass | ja |
| T06 | pass | pass | ja |
| T07 | pass | pass | ja |
| T08 | fail | fail | ja |
| T09 | pass | pass | ja |
| T10 | fail | fail | ja |
| T11 | fail | fail | ja |
| T12 | fail | fail | ja |
| T13 | pass | pass | ja |
| T14 | fail | fail | ja |
| T15 | pass | review_required | nee |
| T16 | pass | pass | ja |
| T17 | pass | review_required | nee |
| T18 | pass | pass | ja |
| T19 | pass | pass | nee |
| T20 | pass | pass | ja |
| T21 | not_evaluated | not_evaluated | ja |
| T22 | review_required | pass | nee |
| T23 | review_required | pass | nee |
| T24 | fail | review_required | nee |

## Werkwijze en beperkingen

- Maker, twee beoordelaars en adjudicator: vier afzonderlijke Astra/high-sessies, expliciet goedgekeurd door Chris. Hun referentievorming gebruikte geen tools of inzage in de appcode/uitkomsten. Dit is AI-beoordeling, geen menselijke validatie.
- De 24 nieuwe synthetische gevallen en referenties zijn vóór uitvoering gehasht. Alle 24 waren eenduidig gelabeld; geen disputen zijn uit de noemer verwijderd.
- Oude app: `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`; nieuwe gemergde app: `ee13ae1d7ce05482bd61f37dd51099b7ba8d23f0`. Beide varianten zijn offline via de gewone en gecachte laadroute uitgevoerd, met tijdelijke opslag.
- Claude Code CLI maakte de proefscripts. Codex CLI (Astra/high) gaf T24 vrij na correctie van de invoerpadregistratie en geslaagde smokes op beide versies.
- De oude app mist het nieuwe deelcontract. De oude 5/24 overeenkomst op het totale regellabel mag daarom niet worden vergeleken met de nieuwe 19/24 zinsstructuurovereenkomst als zuivere classifierwinst.
- Kleine synthetische set, dezelfde modelfamilie voor alle inhoudelijke rollen en geen menselijke gebruikers: geen algemene nauwkeurigheids- of kwaliteitswinstclaim. Compactheid, begrijpelijkheid en generatiekwaliteit zijn hier niet beoordeeld.
- Een latere appcorrectie maakt deze set ontwikkelmateriaal; voor een nieuwe onafhankelijke effectclaim is een nieuwe eindset nodig.

## Bewijs

- [Onafhankelijke eindbeoordeling met motivering per geval](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/t24-eindbeoordeling-v1.json)
- [Alle gevallen, vaste referenties en gepaarde uitkomsten](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/t24-vergelijkingsinvoer-v1.json)
- [Ruwe oude appuitvoer](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/t24-resultaat-oud-v1.json)
- [Ruwe nieuwe appuitvoer](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/t24-resultaat-nieuw-v1.json)
- [Verzegeling vóór uitvoering](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/verzegeling-voor-uitvoering.json)
- [Afzonderlijke sessies en herkomst](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/rollen-v1.json)
- [Bronversies en vooraf vastgelegde criteria](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/bronmanifest-v1.json)
- [Vrijgave T24-runner](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/logs/def770-effectproeven/astra-t24-herreview.md)
