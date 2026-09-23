# DEF-606 — onderzoeksdossiers bespreken, versie 4

11 september 2026 · leidend lokaal vervolgplan · **één toetsregel tegelijk**.

De 53 afzonderlijke regeldossiers zijn uitgewerkt. Chris en Codex lopen ze hierna samen één voor één door. De onderzoeksopdracht is geen bouwopdracht; ook instemming met een inhoudelijke regel is niet automatisch toestemming om app, prompts, skills of configuratie te wijzigen.

Start bij de [index van 53 dossiers](../analyses/def606-regeldossiers/overzicht-v1.md), lees de [samenhang en bewijsgrenzen](../analyses/def606-regeldossiers/samenhang-v1.md) en open vervolgens alleen het actieve dossier. De [eindcontrole](../analyses/def606-regeldossiers/eindcontrole-v1.json) bindt de dossiers aan de onderzochte bron. Alle regelvoorstellen hebben nog de status **met Chris te bespreken**, behalve afzonderlijke eerder vastgelegde besluiten die in de bronnen zijn aangewezen.

## 1. Wat deze versie verandert

| Eerder plan / aanvullende wens | Verwerking in v4 |
|---|---|
| Aangeleverd analyseplan: bestaande basis hergebruiken, geen bouw. | Behouden. Oude bouwconcepten en teruggedraaide tests blijven uitsluitend historisch bewijs. |
| Categorievelden, betrouwbare recordidentiteit en consumerimpact eerst begrijpen. | Behouden in CON-01/DUP_01/ESS-02 en het samenhangrapport. Geen impliciete veldmapping of metadata-ID-policy gekozen. |
| Per toetsregel werken; geen bulk. | 53 afzonderlijke onderzoeken uitgevoerd, ieder na de vorige. Vervolg: één actieve bespreking en één expliciet regelbesluit. |
| Context, definitiebronnen, ontologie en aanvullende informatie meenemen. | Elk dossier behandelt deze in eigen onderdelen, inclusief noodzakelijkheid en bewijsgrens. |
| Claude laten onderzoeken en elkaars resultaten beoordelen. | Ruwe bijdrage per regel bewaard; Codex heeft conclusies geverifieerd, genuanceerd of afgewezen. Een extra samenhangreview is vastgelegd. |
| V3: autonoom verder met volgend onderzoek. | Onderzoeksronde afgerond. Nieuwste aanwijzing van Chris: nu gezamenlijk doorlopen, geen automatische volgende besluit- of bouwstap. |
| In een schone sessie oppakken. | Kopieerbare startopdracht en bronherstel hieronder. Geen nieuwe taak automatisch aangemaakt. |

Dit plan vervangt [v3](2026-09-11-def606-analyseplan-v3.md) voor de volgende lokale werkfase. V3 en de oudere aangeleverde plannen blijven onderzoeksverleden. Het [Linear-masterplan](https://linear.app/definitie-app/document/implementatieplan-definitieagent-kwaliteitsketen-645f1330ac28) blijft de normatieve programmavolgorde; dit lokale plan verandert geen issue-afhankelijkheid of acceptatiecriterium. De link is eerder in deze sessie opgehaald; lees bij een latere sessie de relevante actuele besluiten opnieuw.

## 2. Scope van het geleverde onderzoek

Per regel zijn veertien onderdelen uitgewerkt:

1. Doel en betekenis van de regel.
2. Regelbron, herkomst, voorbeelden en bestaande/open besluiten.
3. Toepasselijkheid bij genereren, uitsluitend toetsen, import, bewerken, review en vaststelling.
4. Rol en vereiste kwaliteit van context.
5. Bronnen die de definitie zelf onderbouwen, los van de regelbron.
6. Genus, identiteit, categorie en relevante ontologische relaties.
7. Voorbeelden, praktijkvoorbeelden, tegenvoorbeelden, grensgevallen, synoniemen, homoniemen en toelichting.
8. Werkelijk appgedrag en grenzen van het onderzochte pad.
9. Betrokken skills en generatie-instructies, inclusief verschillen.
10. Resultaatstatus, score, dekking en gevolgen voor vervolghandelingen.
11. Concrete proefgevallen met waargenomen uitkomsten en inhoudelijke duiding.
12. Raakvlakken en spanningen met andere regels.
13. Verbeteringsrichting, open keuzes, Claude-bijdrage en Codex-beoordeling.
14. Toekomstige acceptatie en overdracht.

Deze structuur is een onderzoekshulpmiddel. Zij bewijst niet dat alle mogelijke gevallen gedekt zijn. Bij bespreking kan een dossier aanvullende vragen krijgen; die blijven bij de actieve regel. Niet vooraf alle dossiers opnieuw onderzoeken.

De proeven zijn offline, op één onderzoekscommit, met manager en productiecache en waar nodig verse eigen opslag. Zij tonen direct servicegedrag. Ketenproblemen uit de oorspronkelijke analyse zijn apart gekoppeld; er zijn geen 53 nieuwe volledige UI-tests uitgevoerd. De verwachte inhoudelijke labels en beleidsvoorstellen zijn nog geen door Chris goedgekeurde goldset.

## 3. Eén gezamenlijke bespreking

**Eerste voorgestelde regel: CON-01.** Chris kan een andere kiezen. De historische onderzoeksvolgorde staat in v3; de index is een vindlijst, geen opdracht om alle regels in één gesprek af te handelen.

Voor de actieve regel:

1. Lees het nieuwste dossier, de aangewezen bewijsbestanden en alleen de relevante skillpassages. Controleer de bronbinding en eventuele wijzigingen sinds het onderzoek.
2. Leg in gewone taal uit wat de regel de gebruiker moet opleveren. Toon het relevante verschil tussen norm, appgedrag en skill/prompt.
3. Bespreek een inhoudelijk goed geval, een onjuist geval en de beslissende grensgevallen. Geef aan welke verwachte uitkomsten al uit een besluit volgen en welke een nieuw oordeel vragen. Geen willekeurig minimumaantal als bewijs van volledigheid.
4. Maak per informatiegebied duidelijk wat noodzakelijk, ondersteunend of niet nodig is. Bespreek ontbrekende context, bronnen, relaties en aanvullende velden waar die de uitkomst veranderen.
5. Leg een concreet voorkeursvoorstel en reële alternatieven voor: regelbetekenis, toepasselijkheid, uitzonderingen, evaluatie en de betekenis van de uitkomst. Benoem gevolgen voor score, review, blokkade en betrokken andere regels.
6. Laat Chris het inhoudelijke besluit nemen. Registreer zijn daadwerkelijke keuze en resterende vragen in een nieuwe dossierversie of afzonderlijk besluitblad. Een onbeantwoorde vraag, verstreken tijd of Claude-instemming is geen besluit.
7. Sluit de bespreking af met wat besloten en nog open is. Ga pas naar de volgende regel volgens de gezamenlijke voortgang. Geen implementatie starten zonder aparte opdracht voor de betreffende afbakening.

Bij een nieuw feitelijk gat: gericht nader onderzoek en hooguit een benodigde geïsoleerde proef. Bij een inhoudelijke keuze: concrete opties bespreken. Niet de hele app herontwerpen om één dossier rond te maken.

## 4. Vorm van een regelbesluit

Maak pas bij een daadwerkelijk besluit een nieuw bestand of dossierversie. Leg minimaal vast:

- Regel-ID, besproken versie, datum en Chris’ besluit in eigen woorden of korte exacte formulering.
- Doel, toepasselijkheid, benodigde invoer en toegestane uitzonderingen.
- Regelbron versus definitiebronnen en eventuele expliciet goedgekeurde lokale afwijking.
- Betekenis van pass, fail, review_required, not_evaluated en error voor deze regel; scheid score, dekking en handelingspoort.
- Beslissende positieve, negatieve, grens- en ontbrekende-invoergevallen met onderbouwde verwachte uitkomst.
- Gevolgen voor skills/prompts/consumerketen en andere regels, zonder hun besluit alvast te nemen.
- Open bewijs, alternatieven die niet gekozen zijn en redenen.
- Afzonderlijk: wel/geen implementatieopdracht en de precieze omvang daarvan.

Een inhoudelijk oordeel hoort bij de beoordeelde tekst, context, bronnen, relaties en regelversie. Relevante wijziging maakt gerichte herbeoordeling nodig; dat is geen opdracht voor automatische monitoring.

## 5. Afhankelijkheden en eigenaarschap behouden

| Bestaand eigenaarschap | Wat deze bespreekronde voorbereidt |
|---|---|
| DEF-622 | Context-/categorie-/identiteitstransport, contextminimum, duplicaten en force-auditreden. Geen blinde categorievoorrang of zelfuitsluiting op vrij metadata-ID. |
| DEF-623 | VER/SAM-toepasselijkheid, taalbeoordeling, benodigde corpusrelaties en werkelijk uitvoerbare vergelijking. Geen nieuwe dependency of NLP-keuze zonder eigen opdracht. |
| DEF-624 | Inhoudelijke voorbeeldparen, uitzonderingen, review/dekking en volledig resultaat naar consumers. Resultaatmigratie blijft een afzonderlijk onderbouwd besluit. |
| DEF-625 | Normherkomst, bronversie en goedgekeurde lokale afwijking. Het gerichte ARAI-06-besluit is geen akkoord op alle 17 eigen voorstellen. |
| DEF-464 | Alleen relevante legacybetekenis vergelijken; geen ongebruikte validator aansluiten of verwijderen. |
| DEF-626 / DEF-630 | Raakvlakken met append-only bewijsopslag en volledige vaststel-/exportpolicy benoemen; hun uitvoering niet vervroegen. |

De belangrijkste samenhangvragen staan in het [samenhangrapport](../analyses/def606-regeldossiers/samenhang-v1.md): functie/essentie, genuscategorie, context/identiteit, negatie, en/of, labelbereik, minimum-/maximumlengte en zichtbare onvolledige beoordeling. Ze zijn afhankelijkheden, geen bulkwerkpakketten.

## 6. Schone sessie: bronnen en herstel

Gebruik **analysis-mode**, **verification-before-completion** en waar nodig **wip-tracker**. Lees de relevante definitie-skills als methode én onderzoeksobject. Gebruik geen executing-plans- of implementatieworkflow voor deze gezamenlijke analyse.

De onderzoeksbasis is `d68a98a909630e15db6e1cb9c9c8171f957bff9d` in `/private/tmp/def606-analyse-20260911`. De gebruikerswerkboom staat op `feature/DEF-700-ui-smoke-prototypes`, `92b870d8fc3c6d3818aec7d643683e29110b5d39`, met bestaand ongetrackt werk. Laat die werkboom intact.

Controleer read-only branch, HEAD en status van beide mappen. Ontbreekt de tijdelijke clone, herstel een geïsoleerde leesbasis op de vastgelegde commit. Controleer actuele main en relevante Linear-besluiten bij een later hervatmoment; behandel oud bewijs alleen als bewijs voor zijn eigen commit. Onderzoek bij bronwijziging alleen de impact op de actieve regel en haar concrete afhankelijkheden.

Bewijs en achtergrond:

- [Basisanalyse en DEF-606-acceptatiematrix](../analyses/2026-09-11-DEF-606-analyserapport-v2.md).
- [Productbedoeling en zes definitie-skills](../analyses/2026-09-11-DEF-606-productbedoeling-toetsregels-skills-v1.md).
- [Oorspronkelijk categorie-/identiteitsplan](../analyses/2026-09-11-DEF-606-analyseplan-v1.md).
- [Bronnen, regelrecords en skillsnapshots](../analyses/2026-09-11-def606-productonderzoek-bewijs/bronnen-en-verificatie-v1.json).
- [Oorspronkelijke ketenproeven](../analyses/2026-09-11-def606-productonderzoek-bewijs/proeven-v1.json).
- [Terugdraaibewijs van onbedoelde eerdere bouw](../analyses/2026-09-11-def622-uitvoering-bewijs/terugdraai-verificatie.json).
- [Actuele werkstaat](/Users/chrislehnen/Projecten/Definitie-app/.claude/handovers/WIP-active.md).

De zes definitie-skills zijn onderzocht, niet gewijzigd. Claude is gebruikt via de webresearchtool binnen Chris’ expliciete toestemming voor interne analysebevindingen en synthetische gevallen. Deel geen sleutels, persoonsgegevens of productiedata. Een latere Claude-bijdrage is alleen nodig bij een concrete nieuwe onderzoeksvraag; niet opnieuw alle reviews draaien.

## 7. Kopieerbare startopdracht

> Lees `docs/plans/2026-09-11-def606-analyseplan-v4.md`, de index `docs/analyses/def606-regeldossiers/overzicht-v1.md` en de werkstaat. We gaan de toetsregels samen één voor één bespreken, te beginnen met CON-01 tenzij ik een andere regel kies. Gebruik het nieuwste dossier en bestaand bewijs; verifieer bronbinding en lees relevante skills. Leg eerst normdoel, werkelijk appgedrag, context, definitiebronnen, ontologie, aanvullende informatie en open keuzes helder uit. Geef een concreet voorstel met alternatieven en beslissende gevallen. Leg mijn daadwerkelijke besluit vast, maar bouw niets zonder afzonderlijke opdracht. Geen bulk, geen automatische normwijzigingen, geen commit/push/PR of externe publicatie. Oude bouwconcepten blijven archief.

## 8. Eindgrens van deze opdracht

Onderzoeksmateriaal, samenhang, index en vervolgplan zijn het product. DEF-606 wordt hiermee niet als opgeleverd issue gemarkeerd. De volgende actie is een gezamenlijke bespreking; er wordt geen sessie, monitoring, implementatie of publicatie automatisch gestart.
