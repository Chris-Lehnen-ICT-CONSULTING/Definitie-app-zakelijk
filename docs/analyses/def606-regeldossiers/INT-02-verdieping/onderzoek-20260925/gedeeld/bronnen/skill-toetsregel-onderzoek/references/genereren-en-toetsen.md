# Eén norm, twee toepassingen

Gebruik dit dossiersjabloon bij iedere actieve regel, binnen Q1–Q6 en de bestaande veertien onderdelen. Het is een verplichte inhoudelijke uitsplitsing, geen tweede normstelsel of extra reeks dossiers. Bij bestaand onderzoek volstaat een gerichte aanvulling met verwijzingen. Onderzoek andere regels alleen voor concrete samenhang.

## A. Gedeelde norm en informatie

Leg normdoel, bron/besluit en versie, toepasselijkheid en uitzonderingen vast. Maak expliciet wat slechts een generatiestijlvoorkeur is; maak daarvan geen extra afkeurgrond voor een bestaande definitie. Dezelfde toepasselijke norm en uitzonderingen gelden voor gegenereerde en aangeleverde inhoud. Een regel over registratie of menselijke besluitvorming hoeft geen tekstinstructie voor AI te worden: motiveer dan welke appvoorwaarde nodig is.

Vul per relevant veld deze matrix in; rollen kunnen samen voorkomen. Markeer niet-relevantie met reden.

| Veld | Zelf toetsobject en criterium | Bewijs voor ander oordeel | Invoer bij generatie | Mag AI dit opleveren/wijzigen? | Herkomst, ontbrekend/conflicterend gegeven |
|---|---|---|---|---|---|
| Definitiezin, context, definitiebronnen, ontologierelaties, voorbeelden, praktijkvoorbeelden, tegenvoorbeelden, grensgevallen, synoniemen, homoniemen, toelichting, overige relevante metadata | Per veld invullen, niet als één tekstblok toetsen | Bewijsfunctie en beperking | Verplicht/ondersteunend/niet nodig | Gezaghebbende invoer versus voorstel; afzonderlijke herkomst | Verwachte reactie en eigenaar |

Bron van de regel en bron van een definitie zijn verschillende gegevens. Gegenereerde voorbeelden of modeluitleg zijn geen onafhankelijke bevestiging. AI mag registratiecontext, bronpassages, bronverwijzingen of menselijke beoordelingen niet verzinnen om een toets te laten slagen.

## B. Generatie-instructie — G

Lever concrete instructietekst met vindplaats voor appprompt en betrokken skill. Beschrijf benodigde invoer, brongebruik, gewenste kern en aanvullende uitvoer, uitzonderingen, verboden betekenisverandering en reactie op ontbrekende of strijdige informatie. Benoem wat vooraf de app moet controleren en wat een modelvoorstel blijft. Een verplichte menselijke review kan niet door een generatieprompt worden afgehandeld.

## C. Toetsinstructie — T

Lever concrete instructietekst met vindplaats voor evaluator/skill. Leg de te beoordelen velden en versie vast, benodigde bewijsstukken, methode en beperkingen, afzonderlijke uitkomsten en gebruikersuitleg. Scheid een vastgestelde overtreding van ontbrekende invoer, niet-uitgevoerde controle, semantische twijfel en technische fout, volgens het geldende resultaatcontract. Uitsluitend toetsen wijzigt de oorspronkelijke inhoud niet; een verbetervoorstel staat apart. Alle groene automatische controles vervangen geen vereiste expertbeoordeling of handmatige vaststelling.

## D. Diagnose en terugkoppeling — H

Classificeer een falende gegenereerde definitie vóór een hersteladvies: werkelijke generatieovertreding, instructie-/normconflict, invoer-/transportverlies, foutpositieve evaluator, ontbrekend bewijs of technische storing. Onderbouw de diagnose; een fail alleen beslist de oorzaak niet.

Ontwerp de relevante keten: invoer → generatie → eventuele nabewerking → toetsing van exact de bewaarde kandidaat → gerichte terugkoppeling → eventuele nieuwe kandidaat → hertoetsing → zichtbare bevindingen. Bewaar de oorspronkelijke modeluitvoer en bewerkingen wanneer die nodig zijn om de oorzaak te reconstrueren. Geen stille betekeniswijziging om een patrooncontrole groen te krijgen.

Automatisch herstel is een appvoorstel totdat uitvoering is opgedragen. Specificeer daarvoor:

- Welke vastgestelde fouten met beschikbare gegevens herstelbaar zijn; ontbrekende context, bronnen of menselijke oordelen niet bijverzinnen.
- Welke inhoud beschermd is: betekenis, brongetrouwheid, noodzakelijke namen, recordidentiteit en gebruikersinvoer.
- Een expliciete, eindige poginglimiet als productkeuze; stoppen bij herhaling, betekenisverlies, bronconflict, foutieve validator of ontbrekend bewijs. Onderzoek hoeft geen universeel aantal pogingen vast te stellen.
- Hertoetsing van de veranderde inhoud plus geraakte buurregels; bij onbekende afhankelijkheden alle toepasselijke controles. Oude oordelen over gewijzigde gegevens worden niet hergebruikt als actuele goedkeuring.
- Wat de gebruiker ontvangt bij succes, open beoordeling, storing of uitgeputte pogingen. Onderscheid toetsresultaat, conceptstatus, expertbeoordeling en vaststelling.

## E. Gekoppelde acceptatiegevallen

Gebruik één casusregister met dezelfde invoer/betekenis voor beide toepassingen. Voeg G/T/H-verwachtingen toe aan bestaande IDs; een nieuw scenario krijgt een nieuw ID. Per geval:

| ID en normversie | Invoer en onafhankelijk onderbouwde bedoeling | G: verwacht voorstel/onthouding | T: verwacht oordeel en reden | H: toegestane herstelactie en stop | Geraakte regels/metadata | Bewijssoort en werkelijk resultaat |
|---|---|---|---|---|---|---|
| Concreet geval | Bron/besluit voor verwachting | Niet alleen gewenste trefwoorden | Ook foutpositieven en gemiste fouten | Betekenisbehoud en herbeoordeling | Geen automatische buurregelbesluiten | Ontwerp, statisch, offline routeproef of echte modelproef |

Neem toepasselijke positieve, negatieve en uitzonderingsgevallen mee; ontbrekende informatie; een onjuiste validatoruitkomst; herstel dat een ander criterium schendt; en stoppen zonder succes. Toon hetzelfde geval als gegenereerde kandidaat en als aangeleverde inhoud: dezelfde norm, terwijl alleen de generatie-/herstelroute een nieuw voorstel mag maken.

Een geïnjecteerde modelrespons bewijst routegedrag, geen generatiekwaliteit. Meet echte generatiekwaliteit alleen met passende autorisatie en een vastgelegd model, prompt-, norm- en invoerversie, steekproef en onafhankelijk vastgelegde verwachtingen. Onderscheid eerste-pogingkwaliteit, resultaat na herstel, foutieve afkeur, gemiste fouten, open beoordelingen en betekenisverlies. Claim geen garantie op foutloze AI-uitvoer of efficiëntiewinst uit alleen een promptwijziging.

### Effectevaluatie van de verbeterslag

Iedere verbeteraanbeveling krijgt een toetsbare effectverwachting en een vergelijking met de bestaande situatie. Gebruik hiervoor het bestaande casusregister en de overdracht; een apart rapport of universele kwaliteitsscore is niet vereist. Houd de omvang passend bij de verandering en de claim.

1. **Bepaal vooraf de gewenste verbetering.** Benoem welke inhoudelijke fouten in definities of beoordelingen moeten afnemen, welke goede uitkomsten behouden moeten blijven en welke verslechtering onaanvaardbaar is. Leg regelspecifieke acceptatiecriteria en hun normgrond vóór de uitkomsten vast. Meer groene toetsen, minder open oordelen of onderlinge modelovereenstemming zijn op zichzelf geen kwaliteitswinst; terecht onthouden of gericht verduidelijken kan de juiste uitkomst zijn.
2. **Ontwerp de vergelijking vóór/na.** Gebruik dezelfde representatieve invoer, betekenis en onafhankelijk onderbouwde verwachtingen voor de oude en nieuwe variant. Neem positieve, negatieve, grens- en ontbrekende-informatiegevallen op waar relevant, plus gevallen die niet zijn gebruikt om de wijziging te ontwerpen of bij te stellen. Leg selectie, omvang en versies vast; houd model, bronnen en instellingen gelijk voor zover zij niet de onderzochte wijziging zijn. Gebruik waar nodig herhaalde modelruns om toeval te onderscheiden van een consistent effect. Maak onvergelijkbare omstandigheden, ontbrekend oud bewijs en onbesliste verwachtingen expliciet; stel verwachtingen niet achteraf bij om de nieuwe variant te laten slagen.
3. **Beoordeel echte uitkomsten.** Beoordeel voor G de werkelijk gegenereerde definities, voor T de oordelen én motiveringen, voor H het betekenisbehoud van voorstellen en voor menselijke beoordelingshulp de beoordelingen die gebruikers met die hulp maken. Beoordeel zo mogelijk zonder kennis van de gebruikte variant, tegen de vooraf vastgelegde norm en verwachtingen; gebruik de gewijzigde evaluator niet als enige maatstaf voor zijn eigen kwaliteit. Een deskundige of onderbouwde referentiebeoordeling behandelt semantische twijfel en meningsverschillen expliciet. Een modelproef bewijst geen gebruikersverbetering, een gebruikersproef geen modelverbetering en simulaties, tekstvergelijkingen, correcte installatie en groene softwaretests bewijzen geen daadwerkelijk kwaliteitseffect. Rapporteer verbeterde, gelijkgebleven, verslechterde en onbesliste gevallen met onderbouwing; vermeld aantallen en steekproefgrenzen zonder ongefundeerde generalisatie.
4. **Draag effectbewijs verplicht over en volg het op.** Onderzoek levert het evaluatieontwerp en de beschikbare nulmeting; voer toegestane proeven uit zodra de te vergelijken varianten beschikbaar zijn. Na implementatie wordt de evaluatie op de werkelijk opgeleverde versies uitgevoerd. Als uitvoering nog niet mogelijk of geautoriseerd is, leg vast: ontbrekend bewijs, eigenaar of nog toe te wijzen eigenaar, concrete volgende actie, benodigde toegang/toestemming en uitvoeringsmoment of afhankelijkheid. Neem dit over in de implementatieopdracht en opleveracceptatie; alleen 'later meten' of 'buiten scope' volstaat niet. Deze overdracht start zelf geen implementatie, modelcalls of gebruikersonderzoek.

Houd **onderzoek afgerond**, **technisch opgeleverd** en **kwaliteitswinst aangetoond** afzonderlijk bij. Zonder passend effectbewijs luidt de status na implementatie: **geïmplementeerd; kwaliteitswinst nog niet vastgesteld**. Een uitgevoerde proef kan ook geen verbetering, verslechtering of onvoldoende bewijs opleveren: rapporteer dat als uitkomst, benoem de consequentie voor de aanbeveling en claim geen succes omdat de proef is uitgevoerd. Trek de conclusie alleen voor de onderzochte doelgroep, gevallen en versies. Voor bestaande dossiers blijft geldig onderzoek behouden; vul het ontbrekende effectontwerp of effectbewijs gericht aan.

## F. Onderzoek en beoordeling

Beide onderzoekers beantwoorden zelfstandig G/T/H, de veldmatrix en de effectevaluatie als onderdeel van dezelfde Q1–Q6. Geef beiden dit sjabloon vóór hun nieuwe conclusies. Laat hun review expliciet toetsen op normgelijkheid, uitzonderingen, brongebruik, volledige dossierdekking, juiste foutdiagnose, herstel zonder betekenisverlies en of de vergelijking de beoogde kwaliteitswinst én verslechtering kan vaststellen. Leg overeenstemming én tegenbewijs vast. Een oude kruisreview dekt een nieuwe aanvulling niet automatisch.

Bij een afgerond dossier: behoud afgeronde bijdragen en actuele besluiten; onderzoek uitsluitend de nieuwe G/T/H-vragen. Leg vast welke aanvulling zelfstandig of gezamenlijk is beoordeeld. Nieuwe CON-01-besluiten zijn geen vooraf bepaalde uitkomst voor andere regels.

Sluit af met regel-, app- en skillvoorstellen, bewijsgrenzen en concrete open productkeuzes. De methode wijzigen autoriseert geen appimplementatie, normwijziging, nieuwe sessie, bulkonderzoek of overgang naar de volgende regel.
