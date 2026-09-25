# G24 — effectmeting gerichte restcorrecties

**Het vooraf afgesproken effectcriterium is in deze kleine proef gehaald:** drie paren inhoudelijk beter, negen gelijk, geen waargenomen verslechtering en geen aangetoonde nieuwe bron- of betekenisfout. Ruwe en opgeschoonde uitvoer krijgen dezelfde gepaarde oordelen. Dit is geen uitspraak dat alle definities volledig correct zijn.

## Uitvoering en onafhankelijkheid

Zes nieuwe synthetische brondossiers × twee armen × twee herhalingen = 24 generaties. Model `claude-opus-5`, dezelfde instellingen en vooraf bevroren verzoeken. Oude bron `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`; nieuwe gereviewde bron `108f38a3933cfe1335908d77a1aaadf0f8f36cc3`. Alle bronnen stonden in beide armen volledig in de daadwerkelijke APIverzoeken.

Twee afzonderlijke Astra/high-sessies beoordeelden alle teksten onafhankelijk, zonder tools, appcode, prompts of oud/nieuw-sleutel. Zij verschilden op vijf paaroordelen. Een derde onafhankelijke sessie adjudiceerde op broninhoud. Eerste oordelen en adjudicatie zijn verzegeld vóór ontblinding. Geen beoordelaar veranderde de teksten.

## Resultaten

| Paar | Dossier | Herhaling | Ruw én opgeschoond | Nieuwe betekenisfout |
|---|---|---:|---|---|
| P01 | G04 | 2 | gelijk | geen aangetoond |
| P02 | G01 | 2 | gelijk | geen aangetoond |
| P03 | G01 | 1 | gelijk | geen aangetoond |
| P04 | G06 | 2 | gelijk | geen aangetoond |
| P05 | G03 | 2 | gelijk | geen aangetoond |
| P06 | G05 | 2 | gelijk | geen aangetoond |
| P07 | G02 | 1 | nieuw beter | geen aangetoond |
| P08 | G04 | 1 | gelijk | geen aangetoond |
| P09 | G02 | 2 | nieuw beter | geen aangetoond |
| P10 | G05 | 1 | gelijk | geen aangetoond |
| P11 | G06 | 1 | nieuw beter | geen aangetoond |
| P12 | G03 | 1 | gelijk | geen aangetoond |

G02 verbetert in beide herhalingen de duidelijkheid van de afbakening: de nieuwe formuleringen vermijden een onduidelijke slotverwijzing en mogelijke extra koppelingseis. De onduidelijkheid over de medewerker als afbakenende actor blijft in beide armen bestaan.

G06 verbetert in herhaling 1 twee inhoudelijke punten: de openstaande inventariscontrole is de toestand bij verlening, niet een voortdurende voorwaarde met “zolang”; volledige vrijgave vereist een afzonderlijke bevestiging ná de inventariscontrole. Herhaling 2 is gelijkwaardig. Geen dossier heeft tegengestelde winstrichtingen tussen herhalingen.

## Resterende inhoudelijke beperkingen

- G04: beide armen verliezen voorwaarden bij intrekking en samenvoeging (uitdrukkelijk intrekkingsbericht; verdere behandeling onder een ander aanvraagnummer). Dit is gedeeld betekenisverlies, geen verbetering door deze kandidaat.
- G02: gedeelde onzekerheid over de medewerker als afbakenende actor. In de oude variant blijft daarnaast onzeker of administratieve koppeling ten onrechte als categorievoorwaarde wordt gelezen.
- De oordelen zijn AI-beoordelingen van zes synthetische dossiers. Begrijpelijkheid is niet met doelgroepgebruikers getest.
- De vergelijking betreft het gehele oude en huidige instructiepakket. Zij bewijst geen algemene betrouwbaarheid of causaliteit van één afzonderlijke promptzin.

## Kosten en keten

Werkelijke runkosten US$1.818475; cumulatief US$7.533075; restant US$0.566925 onder het expliciet goedgekeurde plafond US$8,10. Raming maximaal US$2,3439; alle 24 aanroepen voltooid zonder nieuwe pogingen.

Offline ketencontrole:48 ruwe/opgeschoonde teksten,96 serviceobservaties,48 opslag- en terugleescontroles. Geen fouten; beide laadpaden, onderdelen/status en oorspronkelijke tekstbinding consistent. Geen volledige INT-01-pass. De opschoning verandert hoofdletters/eindpunctuatie, geen betekenis of syntactische relaties volgens de onafhankelijke inhoudsbeoordeling.

## Bewijs

g24-manifest-v1.json, g24-tokentelling-v1.json, g24-budgetbinding-v1.json, g24-generaties-v1/, g24-nabewerking-oud/nieuw-v1.json, g24-blind-v1.json, g24-blind-sleutel-v1.json, g24-beoordeling-A/B-v1.json, g24-adjudicatie-v1.json, bijbehorende verzegelingen, g24-ontblinding-v1.json, g24-evaluator-v1.json en g24-evaluator-controle-v1.json. De gedeelde tekorten en onopgeloste interpretatievragen staan integraal in de adjudicatie.
