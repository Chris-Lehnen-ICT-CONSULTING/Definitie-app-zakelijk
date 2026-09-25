# G24 — definitieve uitkomst na blinde AI-beoordeling

24 september 2026 · DEF-770 · uitgevoerd na merge van app-PR #473 en skills-PR #355.
Dit rapport volgt op de voorbereiding en het daarop gegeven budgetakkoord van Chris.

## Conclusie

**G24 toont geen kwaliteitswinst door de INT-01-wijziging aan. Het vooraf vastgelegde effectcriterium is niet gehaald.** Alle 24 generaties zijn technisch geslaagd. Van de 12 oude/nieuwe vergelijkingen zijn er 8 gelijk, 2 verbeterd en 2 verslechterd. De twee verbeteringen komen uitsluitend voor bij byte-identieke prompts en kunnen daarom niet aan de instructiewijziging worden toegeschreven.

Op dossierniveau zijn er twee gelijke uitkomsten en vier onbesliste uitkomsten. Bij die vier verschillen de twee herhalingen. Er is geen dossier met een herhaalde verbetering. De twee verslechteringen betreffen extra inhoudelijke onzekerheid; er is geen nieuwe zekere onware bronuitspraak vastgesteld. Dat laatste bewijst niet dat de onzekere formuleringen inhoudelijk foutloos zijn.

De eerdere T24-proef blijft **18/24 volledig conform**, met zes bevindingen en één verslechtering van het totale regellabel. De gecombineerde status blijft: geïmplementeerd en gemerged, effectcriteria niet gehaald; kwaliteitswinst niet vastgesteld.

## Uitvoering en kosten

- 6 vooraf verzegelde synthetische dossiers × 2 appvarianten × 2 herhalingen = 24 generatieaanroepen.
- Provider/model: Anthropic `claude-opus-5`; gelijke modelinstellingen, maximaal 1000 uitvoertokens, geen automatische retries of modelvervanging. Geen enhancement of extra betaalde validatieaanroepen.
- Alle 24 antwoorden eindigden met `end_turn`; de generatie-run en beide offline nabewerkingen eindigden met exitcode 0. Geen stopbestand of ontbrekende antwoorden.
- Gebruik: 371.052 invoertokens en 3.399 uitvoertokens; geen cachetokens. Generatiekosten op basis van providergebruik en de vooraf gecontroleerde tarieven: **US$1,940235**, afgerond **US$1,94**. Geen factuurcontrole. De onafhankelijke Codex CLI-beoordelingen vallen niet onder deze Anthropic-generatiekosten.
- Vooraframing US$2,45526; expliciet goedgekeurd plafond US$5. Het akkoord is gebonden aan de hashes van manifest en tokentelling.
- Oude app: `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`; nieuwe app: `ee13ae1d7ce05482bd61f37dd51099b7ba8d23f0`. De appcode, scripts en verzegelde invoer zijn tijdens de proef niet gewijzigd.

## Gepaard resultaat per dossier

Oordeel is steeds **oud → nieuw**. Ruwe kern en opgeschoonde kandidaat leveren dezelfde inhoudelijke paaroordelen op.

| Dossier | Begrip | Herhaling 1 | Herhaling 2 | Gezamenlijk oordeel | Prompts identiek? |
|---|---|---|---|---|---|
| G01 | bakroutekaart | gelijk | gelijk | gelijk | ja |
| G02 | hervatbare aanvraag | gelijk | verslechterd | onbeslist | nee |
| G03 | gezamenlijk routeadvies | gelijk | gelijk | gelijk | nee |
| G04 | overdrachtsset | verbeterd | gelijk | onbeslist | ja |
| G05 | aansluitverschil | gelijk | verbeterd | onbeslist | ja |
| G06 | tijdelijke zichtbeperking | gelijk | verslechterd | onbeslist | nee |

Voor de aggregatie is conservatief alleen een gelijk oordeel in beide herhalingen als stabiele dossieruitkomst aangemerkt. Gelijk plus een verandering blijft onbeslist; de afzonderlijke verbetering of verslechtering blijft hierboven zichtbaar. Dit is geen statistische betrouwbaarheidsuitspraak.

## Inhoudelijke bevindingen

- **G02, hervatbare aanvraag:** beide varianten schrijven dat de behandeling wordt voortgezet, terwijl de bron slechts zegt dat zij kan worden voortgezet. In herhaling 2 bewaart de oude formulering ‘uitsluitend doordat’ de exclusieve oorzaak duidelijker dan de nieuwe formulering ‘doordat uitsluitend’. De nieuwe formulering laat een bijkomende capaciteitsreden onzeker. Bron: G02-B01; vergelijking P08.
- **G06, tijdelijke zichtbeperking:** beide varianten missen lopend onderzoek als toepassingsvoorwaarde en de beschermde beperkingen over inhoudelijke juistheid en aanvraaguitkomst. In herhaling 2 maakt de nieuwe verwijzing ‘die voortduurt’ onzeker of de eindvoorwaarde op de maatregel of de aanwijzing slaat. Bron: G06-B01; vergelijking P11.
- **G05, aansluitverschil:** beide varianten missen dat een verschil op zichzelf geen bewijs van verlies is. De geneste rekenomschrijving blijft moeilijk voor de opgegeven vrijwilligersdoelgroep. De extra tekenuitleg is in één vergelijking als verbetering beoordeeld, maar de prompts waren identiek. Bron: G05-B01; P03/P04.
- **G04, overdrachtsset:** één nieuwe generatie koppelt de drie stukken duidelijker aan dezelfde kast en hetzelfde moment dan de oude generatie. Ook hier waren de prompts identiek; de andere herhaling is gelijk beoordeeld. Bron: G04-B01; P09/P02.
- **G01 en G03:** beide herhalingen gelijk; de beschermde afbakening blijft behouden. G01 heeft identieke prompts en teksten; G03 heeft verschillende prompts, zonder vastgestelde inhoudelijke winst. Bronnen: G01-B01 en G03-B01.

Dit zijn AI-beoordeelde tekstbevindingen. De proef wijst geen eenduidige technische oorzaak toe aan generatieverschillen. De app is niet tussentijds aangepast om deze set passend te krijgen.

## Beoordeling, opschoning en automatische toets

Twee onafhankelijke Astra/high-sessies beoordeelden alle 24 teksten op zinsstructuur, compactheid, doelgroepbegrijpelijkheid, bronsteun en betekenisbehoud. Zij kregen uitsluitend brongegevens en gerandomiseerde tekstlabels, zonder variantidentiteit, prompts, appcode of elkaars eerste conclusies. Zij waren het over 10/12 paaroordelen eens. Een afzonderlijke Astra/high-adjudicator besliste de verschillen vóór deblindering; er zijn geen onopgeloste beoordelaarsdisputen. Lokale tekstuele onzekerheden zijn wel behouden.

De adjudicator wijzigde ook het gezamenlijke onbesliste oordeel voor P04 gemotiveerd naar een relatieve verbetering: de expliciete tekenuitleg kan de doelgroep helpen ondanks gedeelde tekorten. De beide oorspronkelijke oordelen blijven bewaard. Dit oordeel levert geen bewijs voor een instructie-effect op, omdat de prompts identiek waren.

Opschoning voegde bij alle 24 antwoorden een eindpunt toe en bij drie antwoorden ook een beginhoofdletter. Er is geen inhoudelijk herstel of verlies door opschoning vastgesteld.

Daarnaast draaide de nieuwe evaluator offline op alle 48 tekstvormen via beide laadpaden: 96 serviceobservaties, nul uitvoeringsfouten, 48/48 identieke uitkomsten tussen laadpaden. Alle zinsstructuurdeeluitslagen waren `pass`; alle totale INT-01-uitslagen bleven `review_required`, compactheid en begrijpelijkheid afzonderlijk open. INT-01 stond nergens in `passed_rules`. Deze automatische zinsstructuuruitkomst vervangt de inhoudelijke beoordeling niet.

## Grenzen en vervolgdispositie

- Kleine synthetische set, twee herhalingen, AI-beoordelaars uit dezelfde modelfamilie; geen menselijke of doelgroepvalidatie en geen algemene kwaliteitsclaim.
- Bij G01/G04/G05 zijn oude en nieuwe prompts byte-identiek. De oorzaak daarvan is in deze effectproef niet onderzocht. Bij G02/G03/G06 verschillen de prompts. Variatie bij identieke prompts illustreert dat generatieverschillen ook zonder instructiewijziging optreden.
- De generatievolgorde was eerst de twaalf oude, daarna de twaalf nieuwe aanroepen; alleen de beoordelingslabels en presentatievolgorde zijn gerandomiseerd. De proef is geen sterk causaal experiment.
- Bronvolledigheid is in beide armen verzekerd met dezelfde ondersteunde documentinstellingen 200 fragmenten/40.000 tekens en fragmenten van maximaal 450 tekens, na vastgelegde witruimtenormalisatie. Dit wijkt af van de normale documentlimieten. De doelgroep is als extra document aangeleverd omdat de app geen doelgroepveld heeft. De productieconfig is niet gewijzigd.
- App- en skills-PR zijn gemerged; de skills zijn niet lokaal geactiveerd en de bestaande ALG-391-activatiestop blijft gelden. Deze appproef bewijst geen effect van geïnstalleerde skills.
- De zes T24-bevindingen, G24-tekortkomingen en promptgelijkheid zijn expliciet open vervolgpunten. Binnen deze bevroren effectproef zijn geen correcties uitgevoerd en geen algemene effectclaim vrijgegeven. Dit is een gemotiveerd uitstel van herstel binnen deze proef, geen verklaring dat de bevindingen acceptabel zijn. Voor herstel zijn gerichte analyse/implementatie en daarna een nieuwe onafhankelijke eindset nodig; de huidige gevallen worden dan ontwikkelmateriaal.

## Uitvoerders en bewijs

Claude Code CLI implementeerde en corrigeerde de proefscripts: sessie `442a98fb-a377-403f-996e-433cf4a664fc`. Dezelfde onafhankelijke Codex CLI-reviewer op Astra/high sloot de vijf scriptbevindingen: sessie `01a0cfac-ea05-7700-ba73-8b5659751c1c`. Het harnas heeft SHA256 `2ec4388d7a60350855ee85dfcef997938eda34f6cc858dd9359569518ef15709`; 19/19 offline regressies waren groen vóór de betaalde run. De coördinator voerde de vrijgegeven scripts uit en stelde het rapport op.

Inhoudelijke rollen: maker `01a0d327-8e89-7470-bd40-3980715d885f`; beoordelaar A `01a0d32b-97d9-7ad0-afe6-6b8beb1ba821`; beoordelaar B `01a0d32b-8074-7fe1-915f-4d9930ed41f5`; adjudicator `01a0d32e-87c3-7a83-822d-aff7a14d9086`. De G24-beoordelingen eindigden alle met CLI-exitcode 0 en zonder toolgebruik.

- [Einduitkomst met alle 12 vergelijkingen](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/g24-einduitkomst-v1.json)
- [Volledige blinde adjudicatie: alle 24 teksten en discrepanties](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/g24-adjudicatie-v1.json)
- [Beoordelaar A](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/g24-beoordeling-A-v1.json)
- [Beoordelaar B](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/g24-beoordeling-B-v1.json)
- [Blinde set met ruwe en opgeschoonde tekst](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/g24-blind-v1.json)
- [Deblinderingssleutel](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/g24-blind-sleutel-v1.json)
- [Verzegeling adjudicatie vóór deblindering](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/g24-adjudicatie-verzegeling-v1.json)
- [Bronnen en beschermde kenmerken](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/g24-invoer.json)
- [Uitvoeringsmanifest met exacte prompts](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/g24-manifest-v1.json)
- [Budgetakkoord](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/g24-budgetgoedkeuring-v1.json)
- [Providergebruik en kosten per aanroep](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/g24-gebruik-v1.json)
- [Nieuwe evaluator: ruwe uitvoer](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/g24-evaluator-nieuw-v1.json)
- [T24-rapport](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/t24-rapport-v1.md)
- [Vrijgave harnas en testbewijs](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/logs/def770-effectproeven/astra-g24-herreview.md)

De oorspronkelijke providerresponses, aanvraagregistraties en runbinding staan in `g24-generaties-v1/` naast dit rapport; nabewerking, uitvoeringslogs en CLI-beoordelingstranscripts zijn eveneens hier opgeslagen. De eerdere voorbereiding met open budgetstatus blijft als historisch document behouden en is voor de actuele status vervangen door dit rapport en het budgetakkoord.
