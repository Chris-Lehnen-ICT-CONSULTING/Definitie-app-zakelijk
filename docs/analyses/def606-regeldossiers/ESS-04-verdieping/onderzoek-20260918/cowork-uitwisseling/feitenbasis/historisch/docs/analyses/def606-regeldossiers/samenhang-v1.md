# DEF-606 — samenhang en bespreekpunten na 53 dossiers

11 september 2026 · onderzoeksbasis `d68a98a909630e15db6e1cb9c9c8171f957bff9d`.

De 53 afzonderlijke onderzoeken zijn uitgewerkt. De volgende fase is **samen met Chris één toetsregel bespreken**, niet implementeren. De [index](overzicht-v1.md) wijst de nieuwste versies aan; [plan v4](../../plans/2026-09-11-def606-analyseplan-v4.md) beschrijft de werkwijze. Dit rapport benoemt afhankelijkheden; het vormt geen opdracht om meerdere regels tegelijk te veranderen.

## Productbedoeling als beoordelingsmaatstaf

DefinitieAgent hoort te helpen een begrip in zijn bedoelde context af te bakenen, een onderbouwde definitie te formuleren, die te toetsen en een mens een verantwoord vaststelbesluit te laten nemen. Een goede tekstscore alleen is daarvoor onvoldoende. Dit volgt uit het eerder opgehaalde masterplan en de productscope, vastgelegd in het [productonderzoek](../2026-09-11-DEF-606-productbedoeling-toetsregels-skills-v1.md) en [bronarchief](../2026-09-11-def606-productonderzoek-bewijs/bronnen-en-verificatie-v1.json).

De dossiers toetsen daarom meer dan de regex: ook invoer, context, definitiebronnen, begripsrelaties, aanvullende informatie, werkelijke resultaatstatus en toepasselijkheid. Er is geen nieuwe productscope of formele ISO/UFO/ASTRA-conformiteit vastgesteld.

## Betekenis van de onderzoeksstatus

| Wel geleverd | Nog niet geleverd |
|---|---|
| Per regel 14 ingevulde dossieronderdelen, gerichte offline proeven, ruwe Claude-bijdrage en Codex-beoordeling. | Chris’ inhoudelijke goedkeuring van alle regelinterpretaties en nieuwe beleidsvoorstellen. |
| Werkelijk direct servicegedrag via manager én cache op een vastgelegde commit. | 53 volledige UI-doorlopen of bewezen correcte import/edit/review/opslagketen per regel. |
| Geconstateerde gaten, foutpositieven, gemiste gevallen en toekomstige acceptatiegevallen. | Onafhankelijk door mensen gelabelde volledige goldset of gemeten foutpercentages. |
| Bronnen en grenzen van de claims, plus correcties van ondeugdelijke reviewadviezen. | Actuele verificatie van alle externe ASTRA-detailpagina’s of complete juridische skillinhoud. |

De records declareren 37 automated, 12 review_required en 4 not_evaluated. Dat zijn **automatiseringsdeclaraties**, geen telling van inhoudelijk juiste regels. De [eindcontrole](eindcontrole-v1.json) bevestigt 53 dossiers, nummering 1–14, lokale dossierlinks, bronbinding, ruwe reviews en routegelijkheid. Zij telt 59 bewaarde proefbestanden met 856 route-uitkomsten, inclusief eerdere proefversies en tweemaal dezelfde casus via verschillende routes. Dit is uitdrukkelijk geen omvang van een onafhankelijke normtestset. CON-01/DUP_01 hadden commitbinding; hun recordhash staat aanvullend in de eindcontrole. De onderzoeksclone was daarbij schoon.

De eerdere 803 groene gerichte tests blijven bewijs van hun eigen contractscope. Ze zijn niet opnieuw uitgevoerd voor deze documentoplevering en bewijzen geen gerepareerde app. Nieuwe proeven zijn diagnostiek: een geslaagde uitvoering kan juist een productfout aantonen.

## Vier informatiegebieden die expliciet moeten blijven

| Gebied | Wat de app ermee behoort te kunnen onderbouwen | Grens die per regel moet worden besproken |
|---|---|---|
| Context | Bedoelde betekenis, doelgroep, organisatie/rechtsgebied en toepasselijkheid. | Een contextlabel is geen volledige betekenisomschrijving; een ingevuld veld bewijst geen inhoudelijke verwerking. |
| Definitiebronnen | De passage, versie en scope waarop genus/kenmerken/voorwaarden berusten. | Regelbron en definitiebron zijn verschillend. ‘Volgens’ of een brontitel bewijst geen authenticiteit of inhoudelijke steun. |
| Ontologie | Bovenbegrip, relaties, identiteit, rol, proces/resultaat en naburige begrippen. | Een categorie- of markerkeuze bewijst niet dat de tekst daarmee overeenstemt. Volledige ontologie is niet voor iedere taal- of aanwezigheidscontrole noodzakelijk. |
| Aanvullende informatie | Voorbeelden, praktijkgevallen, tegenvoorbeelden en grensgevallen toetsen de afbakening; synoniemen/homoniemen verduidelijken labels en lezingen; toelichting verantwoordt keuzes. | Aanvullende velden vervangen niet stil de kern. Uit dezelfde gebrekkige definitie gegenereerde voorbeelden zijn geen onafhankelijk bewijs. |

Voorstel voor de bespreking: bepaal bij de actieve regel welke informatie **noodzakelijk**, **ondersteunend** of **niet nodig** is, waarom, en wat ontbrekende of tegenstrijdige informatie betekent. Geen verplichting om bij iedere regel elk veld te vullen. De dossiers geven hiervoor een regelgebonden rationale.

## Onderlinge spanningen die niet als losse fouten mogen verdwijnen

| Vraag | Concrete dossiers | Bespreekbaar voorstel, nog geen nieuw besluit |
|---|---|---|
| Waar begint de definiens? | [STR-02](STR-02-v1.md), [STR-04](STR-04-v1.md), [CON-CIRC](CON-CIRC-001-v1.md), [VAL-LEN-001](VAL-LEN-001-v1.md) | Lemma-label en kern expliciet onderscheiden; originele tekst en bereik behouden. Een label kan nu herhaling veroorzaken én een minimumlengte halen. |
| Welke stijl telt als inhoudsfout? | [ARAI-06](ARAI-06-v1.md), [STR-01](STR-01-v1.md), [INT-01](INT-01-v2.md) | Bestaand ARAI-06-besluit over genereren/uitsluitend toetsen ook bij overlappende controles respecteren. Geen indirecte scorestraf verbergen. |
| Wat is essentiële functie? | [ESS-01](ESS-01-v1.md), [STR-05](STR-05-v1.md), [STR-06](STR-06-v1.md), [ARAI-04](ARAI-04-v1.md) | Constitutieve functie, capaciteit, feitelijk effect en incidentele behoefte afzonderlijk bespreken. Niet ‘om te’ blind veranderen in ‘doet’. |
| Wanneer is negatie nodig? | [INT-08](INT-08-v1.md), [STR-07](STR-07-v1.md) | Bestaande uitzonderingen behouden; scope, morfologie en betekenisbehoud beoordelen. Geen mechanische positieve herschrijving. |
| Hoe bewijzen we logische voorwaarden? | [STR-08](STR-08-v1.md), [STR-09](STR-09-v1.md), [INT-02](INT-02-v1.md) | Bedoelde combinaties vóór herschrijven vastleggen. Collectiviteit, equivalentie en fallback onderscheiden van simpele AND/OR. |
| Wat betekenen context en categorie voor identiteit? | [CON-01](CON-01-v1.md), [ESS-02](ESS-02-v1.md), [DUP_01](DUP_01-v1.md) | Geen blinde veldvoorrang, geen zelfuitsluiting op onbewezen ID en geen gelijkstelling tussen vier lokale labels en volledig UFO. |
| Wat bewijst een repository? | [SAM-03](SAM-03-v1.md), [SAM-05](SAM-05-v1.md), [SAM-06](SAM-06-v2.md), [SAM-08](SAM-08-v1.md) | Alleen beschikbaarheid is geen uitgevoerde vergelijking. Onderscheid conceptidentiteit, synoniemrelatie en tekstverwijzing. Een aangetoonde cyclus vereist minder volledigheid dan bewijs dat nergens een cyclus bestaat. |
| Hoe hangen lengteadviezen samen? | [ESS-CONT](ESS-CONT-001-v1.md), [VAL-LEN-001](VAL-LEN-001-v1.md), [STR-ORG](STR-ORG-001-v1.md), [VAL-LEN-002](VAL-LEN-002-v1.md) | Zes tegenover vijf woorden; 300 tegenover 600 tekens/80 woorden. Leg doel, telcontract, score en poort per regel vast; vulwoorden of betekenisverlies niet belonen. |
| Wat doet de app bij te weinig bewijs? | [VAL-EMP](VAL-EMP-001-v2.md), [CON-02](CON-02-v1.md), alle review-/uitgestelde dossiers | Leegte, ontbrekende invoer, onzeker oordeel, bewezen fout en technische error afzonderlijk tonen. Score-uitsluiting zegt niet zelfstandig of vaststellen mag. |

## Ketenbewijs en grenzen per soort regel

De oorspronkelijke [ketenproeven](../2026-09-11-def606-productonderzoek-bewijs/proeven-v1.json) tonen contextverlies in de V2-wrapper en verlies van regelstatus/dekking/reviews in normalisatie. Deze gezamenlijke breuken maken direct servicebewijs niet waardeloos, maar beperken een appbrede claim.

| Regelsoort | Direct bewijs | Nog te bewijzen bij latere uitvoering van de actieve regel |
|---|---|---|
| Tekstpatroon/lengte | Ontvangen tekst en gerichte uitslag op beide laadpaden. | Welke tekst via generatie/toets/import/edit aankomt; eventuele cleaning, offsets en behoud origineel. |
| Context/identiteit | CON-01/DUP directe gevallen en eigen verse opslag. | Context, categorie en vertrouwd record-ID op elke relevante grens; tweede echt duplicaat; force-auditreden. |
| Bron/ontologie | Trefwoord-/markerbeperkingen en eigen metadatafixtures. | Inhoudelijk bewijscontract en tegenstrijdige/ontbrekende input, zonder marker als vrijstelling. |
| Corpusrelaties | Waar passend echte verse repositoryfixtures; deferred blijft deferred. | Relaties daadwerkelijk lezen en betekenisgebonden vergelijken; corpusversie en ontbrekende gegevens zichtbaar. |
| Inhoudelijke review | Review_required met eventuele signalen. | Reviewer kan oordeel/motivering vastleggen; consumer bewaart die en toont onvolledige dekking. |

Bewijs dat een resultaat de UI bereikt staat los van bewijs dat de definitie juist is. Een menselijke beoordelaar moet de inhoudelijke verwachte uitkomsten nog bevestigen. Het aantal voorbeelden dat daarvoor nodig is volgt uit de concrete risico’s, niet uit een magisch minimum.

## Skills: meenemen bij de actieve regel

Het [skillonderzoek](../2026-09-11-DEF-606-productbedoeling-toetsregels-skills-v1.md) blijft leidend bewijs voor de zes onderzochte definitie-skills. Per dossier staat hun toepasselijke rol. Nog te beoordelen correcties: oude validator-/scorebeschrijving in toetsregels; stijl versus inhoud in Nederlandse-definities; de gericht aangetoonde juridische voorbeeldfout; UFO-theorie versus lokale mapping; term versus concept/homoniem bij ontologisch-modelleren; en de onzuivere intensie/extensie-notatie bij voorbeelden-generatie. Ook DUP-originaliteit, SAM-08 ‘zelfde structuur’ en INT-08-uitzonderingen moeten niet ongecontroleerd in prompts terugkomen.

Wijzig skills niet los vooruit. Bespreek eerst de betreffende regelbetekenis en bron; leg daarna een concreet tekstvoorstel naast appgedrag en acceptatiegevallen. Er is in deze opdracht geen skill geïnstalleerd of aangepast.

## Wederzijdse eindbeoordeling

[Claude’s samenhangreview](claude-samenhangreview-v1.json) vraagt terecht expliciete semantische acceptatiecriteria, menselijke beoordeling, ketenbegrenzing en bronwijziging als herbeoordelingsaanleiding. Dit is verwerkt in plan v4: de bestaande dossiergevallen worden samen beoordeeld en een besluit wordt gekoppeld aan tekst/context/bron/regelversie.

Codex neemt drie conclusies van Claude niet over. De 37 automatische declaraties zijn niet als werkende regels ‘afgesloten’; alleen hun onderzoek is uitgewerkt. Contextverlies in de wrapper maakt het afzonderlijk vastgelegde directe servicebewijs niet ongeldig. En de 14 dossieronderdelen zijn een afgesproken onderzoekstructuur, geen nieuwe ontologie of bewijs van semantische volledigheid. De review is geen onafhankelijke codeverificatie en vraagt geen ongevraagde bouw of monitoring. Bronwijziging is een trigger voor gerichte herbeoordeling; er is geen automatische periodieke taak ingericht.

De correcties in individuele dossiers zijn behouden als nieuwe versies. De index selecteert INT-01-v2, ARAI-05-v2, SAM-02-v2, SAM-06-v2 en VAL-EMP-001-v2; eerdere versies blijven historisch bewijs. Lokale links en hashes zijn gecontroleerd. Open normen zijn nergens door een Claude-instemming vastgesteld.

## Eerstvolgende gezamenlijke bespreking

Begin voorgesteld met **CON-01**: contextbetekenis, aanwezigheid, expliciete labels en doorgifte. Houd DUP-identiteit en ontologische categorie als zichtbare afhankelijkheden; beslis ze niet stil binnen CON-01. Presenteer het concrete voorstel met alternatieven en laat Chris het inhoudelijke oordeel vastleggen. Daarna pas de volgende regel, tenzij Chris een andere volgorde kiest.
