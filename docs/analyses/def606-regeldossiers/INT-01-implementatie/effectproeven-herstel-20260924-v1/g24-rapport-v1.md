# G24 — nieuwe generatieproef na herstel

24 september 2026 · generatiebron `6c18ce7127f0a785fefdd6bc952175a030be8643`.

**Geen kwaliteitswinst aangetoond; het effectcriterium is niet gehaald.** Van 12 gepaarde vergelijkingen zijn er 6 gelijk, 1 verbeterd, 4 verslechterd en 1 onbeslist. De vier verslechteringen bevatten volgens de onafhankelijke adjudicatie nieuwe bron- of betekenisfouten. Eén dossier verslechtert in beide herhalingen; bij drie dossiers is de gezamenlijke uitkomst onbeslist. Twee dossiers blijven gelijk. Ruwe en opgeschoonde teksten leveren dezelfde paaroordelen op.

## Uitvoering

Zes vooraf vastgelegde synthetische dossiers × oud/nieuw × twee herhalingen: 24 geslaagde aanroepen, allemaal `end_turn`, zonder retries, enhancement of extra betaalde validatiecalls. Beide armen gebruikten `claude-opus-5`, dezelfde bron/context en modelinstellingen, maximaal 1.000 uitvoertokens. Bronvolledigheid is gecontroleerd. Bij alle zes dossiers verschillen de oude en nieuwe prompts daadwerkelijk.

De standaardtarieven zijn vooraf opnieuw gecontroleerd bij [Anthropic](https://platform.claude.com/docs/en/about-claude/pricing): US$5 per miljoen invoertokens en US$25 per miljoen uitvoertokens voor Opus 5. De provider rapporteerde 337.488 invoertokens en 3.511 uitvoertokens, zonder cachegebruik. Daarmee kost deze run **US$1,775215**. Cumulatief met de eerste proef: **US$3,71545**, binnen het bestaande plafond van US$5. Dit is een berekening uit providergebruik, geen factuurcontrole. Vooraf was maximaal US$2,28744 geraamd; het resterende budget was US$3,059765.

## Gepaard resultaat

| Dossier | Begrip | Herhaling 1 | Herhaling 2 | Gezamenlijk |
|---|---|---|---|---|
| G01 | verplaatsingsbericht | gelijk | gelijk | gelijk |
| G02 | aansluitverzoek | verslechterd | verbeterd | onbeslist |
| G03 | spiegelinschrijving | verslechterd | gelijk | onbeslist |
| G04 | herstelgrond | gelijk | onbeslist | onbeslist |
| G05 | nulpaar | verslechterd | verslechterd | verslechterd |
| G06 | routepauze | gelijk | gelijk | gelijk |

Gelijke oordelen in beide herhalingen gelden als stabiele dossieruitkomst. Verschillende richtingen blijven onbeslist; individuele verslechteringen verdwijnen daardoor niet.

## Inhoudelijke bevindingen

- **G02 — aansluitverzoek:** in herhaling 1 verliest de nieuwe tekst de expliciete afhankelijkheid van *aansluiting op* een andere bevestigde rit. In herhaling 2 is die verhouding omgekeerd. Daarom is het dossier onbeslist, met zowel een verbetering als een verslechtering. Bron G02-B01; paren P03/P10.
- **G03 — spiegelinschrijving:** de nieuwe tekst in herhaling 1 eist dat de eigen invoertijd afwijkt van het oorspronkelijke record. De bron zegt dat deze niet gelijk hoeft te zijn; afwijking is geen verplichte voorwaarde. De nieuwe definitie vernauwt dus de categorie. De tweede herhaling is gelijk. Bron G03-B01; P05/P12.
- **G05 — nulpaar:** beide nieuwe teksten zeggen dat de twee meetuitkomsten samenhoren, maar bewaren niet de eis dat zij samen worden bewaard. Beide oude teksten doen dat wel. Dit dossier verslechtert in beide herhalingen. Bron G05-B01; P04/P01.
- **G04 — herstelgrond:** in herhaling 2 blijft onzeker of de nieuwe tekst een aanvullende verplichting tot afzonderlijke registratie introduceert. Adjudicatie behoudt dat dispuut; het paar blijft onbeslist. De andere herhaling is gelijk. Bron G04-B01; P06/P09.
- **G01 en G06:** beide herhalingen gelijk; geen aangetoonde inhoudelijke verbetering of verslechtering.

Dit zijn AI-beoordeelde tekstverschillen. De proef bewijst niet welke specifieke promptzin een verschil veroorzaakte.

## Beoordeling en automatische controle

Twee afzonderlijke Astra/high-sessies beoordeelden alle 24 teksten en 12 paren blind, zonder variantidentiteit, prompts, code, automatische uitslagen of elkaars eerste oordeel. De onafhankelijke adjudicator behandelde discrepanties en legde het oordeel vast vóór deblindering. De onzekerheid over B21/P06 bleef expliciet behouden. De bron- en betekenisbevindingen hierboven zijn gecontroleerd tegen de synthetische dossiers en de feitelijke uitvoerteksten.

De automatische `/3`-evaluator is offline op 48 tekstvormen (ruw/opgeschoond) via twee laadpaden uitgevoerd: 96 observaties, geen uitvoeringsfouten, gelijke uitkomsten tussen laadpaden. Alle zinsstructuurdeeluitslagen zijn pass; alle volledige INT-01-uitslagen blijven review_required, met compactheid en begrijpelijkheid afzonderlijk open. De automatische zinscheck vindt de inhoudelijke betekenisfouten dus niet.

Een latere correctie van uitsluitend de classifier verandert deze bevroren generatieprompts en providerantwoorden niet. De inhoudelijke G24 blijft dit resultaat houden; een nieuwe automatische beoordeling onder een andere contractversie wordt afzonderlijk gebonden en gerapporteerd. Er zijn voor die offline herbeoordeling geen extra generatiecalls nodig.

## Grenzen en vervolg

Kleine synthetische set, twee herhalingen en AI-beoordelaars uit dezelfde modelfamilie; geen menselijke of doelgroepvalidatie en geen statistische betrouwbaarheidsclaim. De volgorde van generatieaanroepen was eerst oud, daarna nieuw; alleen beoordeling en paarlabels zijn gerandomiseerd. De ondersteunde proefconfiguratie gebruikt 200 bronfragmenten/40.000 tekens met fragmenten tot 450 tekens. Dat wijkt af van de normale documentlimieten; de productieconfiguratie is niet gewijzigd. De doelgroep is als document aangeleverd omdat de app geen doelgroepveld heeft. Geen bewijs van effect van lokaal geïnstalleerde skills; activatie blijft bevroren onder ALG-391.

De generatie-instructie is op grond van deze proef niet vrijgegeven als verbetering. De gevonden fouten blijven binnen DEF-770 open; de concept-PR’s worden niet gemerged. Een vervolg moet brongetrouwheid en de bescherming van modaliteit, relaties en voorwaarden gericht adresseren, met een nieuwe onafhankelijke generatieproef en vooraf passend kostenmandaat. Deze uitgevoerde proef wordt niet door nieuwe labels of extra herhalingen gunstiger gemaakt.

## Bewijs

[Einduitkomst en deblinderingsmapping](g24-einduitkomst-v1.json) · [blinde adjudicatie](g24-adjudicatie-v1.json) · [verzegeling vóór deblindering](g24-adjudicatie-verzegeling-v1.json) · [A](g24-beoordeling-A-v1.json) · [B](g24-beoordeling-B-v1.json) · [brondossiers](g24-invoer-v1.json) · [blinde set](g24-blind-v1.json) · [manifest](g24-manifest-v1.json) · [budgetbinding](g24-budgetbinding-v1.json) · [providergebruik](g24-gebruik-v1.json) · [automatische uitvoer /3](g24-evaluator-nieuw-v1.json).

Volledige CLI-briefings en sessielogs staan onder `logs/def770-eindproeven/`. Rollen en bronbinding staan in `bron-en-setbinding-v1.json`, `t24-referentierollen-v1.json` en de adjudicatieverzegeling. De vooraf verzegelde dossiers, beoordelingen en historische proefresultaten zijn behouden.
