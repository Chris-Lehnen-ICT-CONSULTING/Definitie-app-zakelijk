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

## F. Onderzoek en beoordeling

Beide onderzoekers beantwoorden zelfstandig G/T/H en de veldmatrix als onderdeel van dezelfde Q1–Q6. Geef beiden dit sjabloon vóór hun nieuwe conclusies. Laat hun review expliciet toetsen op normgelijkheid, uitzonderingen, brongebruik, volledige dossierdekking, juiste foutdiagnose en herstel zonder betekenisverlies. Leg overeenstemming én tegenbewijs vast. Een oude kruisreview dekt een nieuwe aanvulling niet automatisch.

Bij een afgerond dossier: behoud afgeronde bijdragen en actuele besluiten; onderzoek uitsluitend de nieuwe G/T/H-vragen. Leg vast welke aanvulling zelfstandig of gezamenlijk is beoordeeld. Nieuwe CON-01-besluiten zijn geen vooraf bepaalde uitkomst voor andere regels.

Sluit af met regel-, app- en skillvoorstellen, bewijsgrenzen en concrete open productkeuzes. De methode wijzigen autoriseert geen appimplementatie, normwijziging, nieuwe sessie, bulkonderzoek of overgang naar de volgende regel.
