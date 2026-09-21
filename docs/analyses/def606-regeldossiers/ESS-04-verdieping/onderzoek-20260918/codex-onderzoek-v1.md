# ESS-04 — zelfstandig Codex-onderzoek v1

18 september 2026. Eerste volledige zelfstandige bijdrage, bewaard vóór lezing van nieuwe Cowork-conclusies. **Onderzoek en voorstel; geen normbesluit of implementatie.** Centraal issue DEF-767. Bronverwijzingen S/B/C/P verwijzen naar [bron- en bewijsregister](bron-bewijsregister-v1.md). Nieuwe inhoudelijke casussen staan in [casusregister](casusregister-v1.md); exacte vervangteksten in [instructievoorstellen](instructievoorstellen-v1.md).

Werk-HEAD 50d0770 (21 augustus); historische dossierbasis d68a98a9 (11 september); actuele aanvullende snapshot/proeven **4cdb8ea43aa9b750326cbf8d9c8034db77f6eafb**, lokaal origin/main op 18 september 15:27:24 +0200. De oude werkboom is niet als huidige app gepresenteerd. Codekopieën kwamen via Git uit de eigen worktree; oorspronkelijke projectmap en draaiende app/database zijn ongemoeid.

## Q1 — norm, betekenis, toepasselijkheid

**Voorstel N1:** “De definitie beschrijft kenmerken waarmee binnen de bedoelde betekenis en context navolgbaar kan worden beoordeeld of een geval onder het begrip valt.”

Dit operationaliseert het historische ESS-04-doel (S01), maar is geen bewezen letterlijk ASTRA-voorschrift. De actuele ASTRA-passage was niet toegankelijk (S05). De lokale regeltekst noemt vooral deadlines, aantallen en percentages; het record is bytegelijk aan het historische record. Het oordeelcontract vraagt menselijke review (C01). Definitieve externe herkomst/revisie en eventuele afwijking blijven open onder DEF-625.

Vier vragen moeten afzonderlijk beantwoord worden:

1. **Toetsbaarheid:** is voldoende duidelijk welke eigenschap of relatie op welk object van toepassing moet zijn en hoe relevant bewijs het oordeel draagt?
2. **Numerieke meetbaarheid:** wordt een grootheid gekwantificeerd? Dat is één methode. VIM3 §1.30 behandelt nominale eigenschappen zonder grootte; §2.1 sluit ze uit van meting in metrologische zin (S07). Daarom is “toetsbaar” ruimer dan “numeriek meetbaar”; noem een kwalitatieve beoordeling niet zonder meer een metrologische meting.
3. **Juistheid/bronsteun:** volgt dit criterium uit de bedoelde betekenis en toepasselijke bronnen? Een exact toepasbare maar verkeerde >80%-grens kan ESS-04-technisch bruikbaar zijn terwijl CON-02 faalt (N07).
4. **Essentieel onderscheid:** begrenst het criterium juist dit begrip ten opzichte van verwante begrippen? Lengte kan exact meetbaar zijn en toch niets beslissends zeggen over de bedoelde vakbekwaamheid (N14). ESS-01/05 blijven eigenaar van die betekenisvragen.

**Toepasselijkheid:** dezelfde norm bij generatie, aangeleverde tekst, import en bewerken; geen numerieke stijlvoorkeur als strengere T-eis. Ook abstracte begrippen en één bepaald voorval kunnen navolgbaar beschreven zijn. Een mathematische gelijkheidsvoorwaarde vraagt niet automatisch een fysieke meetopstelling. Bij fysieke toepassingen kunnen meetmethode/tolerantie juist wél nodig zijn. Toepassing bepaalt welke informatie materieel is.

**Geen universele gegarandeerde beslisbaarheid:** norm voor kwaliteit van een begripsbeschrijving is iets anders dan beschikbaarheid van bewijs voor ieder denkbaar geval. Het ontbreken van een foto, document of meetrapport kan het gevalsoordeel open laten bij een goede definitie (N17). Een onbekend geval is geen automatische ESS-04-fail.

**Open normen:** een kwalitatief of contextafhankelijk criterium kan navolgbaar worden toegepast via een gezaghebbende beoordelingsmaatstaf met motivering. “Zo snel mogelijk” als compleet criterium voor een harde termijnklasse is onvoldoende, maar een bedoelde open norm mag niet tot een verzonnen drie dagen worden vernauwd. Eerst vaststellen welke betekenis de bron werkelijk geeft. Geen algemene juridische vrijstelling, geen universele numerieke vervanging. Geen juridisch praktijkoordeel in deze synthetische cases.

**Leegte:** VAL-EMP kan leegte afkeuren; ESS-04 heeft dan geen inhoud om te beoordelen. De historische lege-text review_required is uitvoeringsgedrag, geen bewijs dat een lege definitie inhoudelijk beoordeelbaar is.

## Q2 — informatie en bewijs

Gebruik alleen gegevens die een andere uitkomst mogelijk maken of de uitgevoerde beoordeling herleidbaar maken. Drie informatielagen:

- **Betekenisgrond:** welk begrip, welke context, welke bepalende criteria en bronbeperkingen?
- **Toepassingsgrond:** welke concrete gegevens van het geval maken het criterium toepasbaar?
- **Beoordelingsregistratie:** welke versie, wie, wanneer, wat onderzocht en waarom dat oordeel?

Geen van deze lagen mag stil de andere vervangen. Een bronverwijzing bewijst niet dat de bron de betekenis ondersteunt. Een verzonnen reviewer/pass-label is geen review (P01). Toelichting kan de methode uitleggen, maar mag een ontbrekend begripsbepalend criterium niet onzichtbaar repareren. NL-SBB onderscheidt termen, definitie, toelichting en voorbeelden (§2.4.1.1–2.4.1.2; S06); de precieze veldpolicy hieronder is lokale uitwerking.

### Veldrollen

TO = toetsobject; B = bewijs; G = generatie-invoer; P = presentatie. Voor alle AI-voorstellen geldt herkenbare herkomst; gezaghebbende input en menselijke beoordeling niet bijverzinnen.

| Veld | Rol voor ESS-04 / criterium | Noodzakelijkheid / AI-bevoegdheid / ontbreken |
|---|---|---|
| Definitiekern | TO; expliciete kenmerken en hun toepassing | Altijd nodig. G mag kandidaat voorstellen; T behoudt oorspronkelijke tekst; H aparte variant |
| Context | B/G; bepaalt bedoelde betekenis en toepassingsbereik | Relevante context noodzakelijk; drie bestaande CON-01-lijsten behouden. Geen registercontext in kern plakken om ESS-04 groen te maken |
| Definitiebronnen | B/G; grond voor kenmerken, grens en conventie | Vereist wanneer criterium daarvan afhangt; bronversie en passage waar relevant. CON-02-bronuitzondering bewijst geen grenssteun. AI verzint geen bron |
| Ontologierelaties | B/G; eigenschap van welk object, welke populatie/relatie | Ondersteunend of noodzakelijk bij ambigu meetobject. Geen verplicht compleet UFO-model voor eenvoudige definitie; relaties blijven voorstellen |
| Voorbeelden | B/G/P; laten toepassing zien | Ondersteunend, geen volledige bewijsbasis. Modelvoorbeelden niet als onafhankelijke validatie gebruiken |
| Praktijkvoorbeelden | B; werkelijk geval met controleerbare gegevens | Nodig bij praktijkclaim; gebruik bron/toegang passend, geen productiegegevens hier. Een synthetisch geval blijft synthetisch |
| Tegenvoorbeelden | B/G; minstens één bepalend criterium faalt | Gericht op verwarring; geen willekeurig totaal verschillend begrip. AI-label heeft review nodig |
| Grensgevallen | B/G; exact op en naast grens of interpretatiepunt | Nodig waar onderscheidend. Een eenduidig grensgeval is nog steeds grensgeval; onenigheid niet als definitie gebruiken |
| Synoniemen | B/G/P; gedeelde betekenis en criteria | Geen ESS-04-verplichting om synoniemen te verzamelen. Betekenisgebonden equivalentie, geen simpel trefwoordbewijs |
| Homoniemen | B/G; dezelfde term met verschillende betekenissen | Relevant om verkeerd meetobject te voorkomen (bank). Betekenissen afzonderlijk; AI kiest niet stil een andere |
| Toelichting | B/P en soms G; methode, grond, beperking | Methode kan hier; essentiale beperking niet uitsluitend hier verstoppen. Niet samengevoegd met kern toetsen |
| Meetmetadata | B; noemer, eenheid, methode, inclusie, tijd | Alleen waar onderscheidend. Geen algemene verplichte checklist van alle velden |
| Review-/versiemetadata | B/P; oordeel over exact onderzochte invoer/norm | Voor vertrouwen/hergebruik nodig: passage, grond, actor/rol, tijd, tekst/context/bron/normversie. Geen AI-actorfabricatie |

### Voorwaardelijke bewijsvereisten

Bij percentage: teller, noemer, relevante populatie/uitsluitingen, periode en eventueel weging/afronding. “8/10 ontvangen” mag niet stil “8/8 geïnspecteerd” worden. Lege populatie kan buiten scope liggen; zo niet, dan vraagt 0/0 een expliciete conventie. Geen universeel 0%- of 100%-antwoord.

Bij grenzen: onderscheid minimaal (≥), meer dan (>), maximaal (≤), minder dan (<); betekenis van “binnen” en begin/eindmoment uit bron/context bepalen. Bij fysieke metingen kunnen meetonzekerheid en afrondingsregels de grens beslissen; verzin geen tolerantie uit een abstract geometrisch geval.

Bij termijnen: referentiegebeurtenis, kalender-/werkdagen of verstreken uren, telconventie en tijdzone uitsluitend waar die de uitkomst veranderen. Geen jurisdictieregel uit algemeen geheugen importeren. Historische onjuiste 65-uursberekening uit S03 niet gebruiken.

Bij versies/conflicten: onderscheid publicatiedatum, ingangsdatum en gevalstijd. Bronrecency is niet vanzelf voorrang. Twee goed meetbare maar strijdige criteria vragen een betekenis-/bronbesluit, geen gemiddelde of meerderheidsstem.

## Q3 — relaties zonder buurregelbesluiten

| Regel | Concrete relatie / grens |
|---|---|
| ARAI-03 | “Belangrijk” kan zonder grond vaag zijn; “blauw” kan binnen passende conventie toetsbaar zijn. Bijvoeglijk naamwoord niet generiek vervangen door cijfer |
| ESS-01 | Functie/rol/bestemming kan begripsbepalend zijn volgens vastgesteld besluit. ESS-04 onderzoekt toepasbaarheid ervan, verbiedt functie niet opnieuw |
| ESS-02 | Niveau en aard bepalen waarop criteria slaan; categorielabel bewijst kern niet. Vastgestelde overlappende richtingen, menselijke review en geen zelfstandige ESS-02-poort blijven behouden |
| ESS-03 | Instance-identiteit/telbaarheid helpt populatie, teller en dubbel tellen controleren. Een record-ID bewijst geen begripslidmaatschap |
| ESS-05 | Essentieel onderscheid en voldoende afbakening blijven apart van toepasbaarheid; exact maar irrelevant criterium is tegenvoorbeeld tegen getal=kwaliteit |
| CON-01 | Gestructureerde context en noodzakelijke namen behouden. ESS-04 laat geen verzonnen meetcontext toe en heropent context-/identiteitsbeleid niet |
| CON-02 | Draagt brongezag, betekenissteun en verwijzing. Vindbare/authentieke bron is niet automatisch bruikbaar criterium; CON-02-AI-toestemming geldt niet automatisch voor ESS-04 |
| INT-02/06 | Methode of procedure niet als uitvoeringsinstructie in kern plakken; criterium kan noodzakelijk zijn, toelichting blijft apart. Geen woordverbod op “als” invoeren |

**Actuele buurregelstatus:** ESS-02 PR461 en PR464 zijn geregistreerd/gemerged; dit is geen bewijs dat alle review-, opslag-, export- en Cowork-criteria voltooid zijn. DEF-752 bevat een expliciete gedeelde-opslaguitvoeringsspecificatie; in de voor ESS-04 gelezen actuele route is geen aangesloten ESS-04-oordeel gevonden. Eerdere globale uitspraak dat “alle gedeelde voorzieningen ontbreken” zou te breed zijn: CON-01/CON-02 hebben concrete routes en recente resultaatnormalisatie is geleverd. Behoud bestaande owners, onderzoek alleen de ontbrekende aansluiting. DEF-745-statusveld Done versus nieuwste comment over open restscope is broninconsistentie; normbesluiten blijven vast.

## Q4 — werkelijk gedrag en actuele menselijke route

### Bewijsactualisatie

P01–P04 zijn offline uitgevoerd, vooraf beschreven en gebonden aan bron/runtime (register). Ze bewijzen geen generatiekwaliteit, volledige UI-keten of menselijke beoordeling.

- ESS-04-record en oordeelklasse zijn behouden; ‘objectief toetsbaar’ levert signaal plus review_required, ook als caller metadata pass/reviewer bevat.
- **Oude P02-transportfout is in actuele tegenproef niet aanwezig.** Beide normalisatieroutes behouden de drie review-/status-/dekkingsvelden. Ontbrekende runstatus geeft validation_unknown en is_acceptable=false; de oude BASIC-passes worden niet verzonnen. De technische nul in unknown-output is geen kwaliteitscijfer of inhoudelijke fail; consumerweergave blijft afzonderlijk te beoordelen.
- De daadwerkelijke ESS-04-mapping noemt nog aantallen/deadlines/percentages. Dat toont promptdruk, niet een werkelijk model dat een drempel verzon.
- De ene geteste partijzin behoudt na extractie/cleaning 80%, minimaal, noemer en peildatum. **Geen schadelijke nabewerking aangetoond in dit geval.** Opslag ontbreekt in deze proef; ruwe output en opgeslagen tekst niet als gelijk bewezen.

### Routes

| Ingang | Aangetoond / bron | Nog open |
|---|---|---|
| G — generatie | Actuele modulefunctie P03; codeketen definition_orchestrator_v2, ruwe generatie→cleaning→validatie→repository | Volledige eindprompt, werkelijk verzonden bronnen/taak, modeloutput en opslag van ESS-04-cases niet uitgevoerd |
| T — losse tekst / Definition | Actuele validation_orchestrator_v2:128,174,224 behoudt tekst zonder cleaning; P01 direct oordeel | Geen nieuwe echte UI-ingang of volledig brontransport bewezen. Oude cleaning-in-T-kloof niet als actuele fout opvoeren |
| Import | Bestaande importservice/codebasis beschikbaar; bronstatus verandert de ESS-04-norm niet | ESS-04-invoer/status/opslag/readback/import-UI niet proefondervindelijk gevolgd |
| Bewerken | Algemene edit-/reviewroutes bestaan; gewijzigde kern vereist versiebinding | Geen actuele ESS-04-review die na wijziging correct stale wordt functioneel aangetoond |
| Review | judgment_review geeft eis/signaal; expert_review_tab bevat CON-context-/bronbeoordeling en algemene reviewactie | Geen aangesloten ESS-04-specifieke beoordelingsschrijfroute gevonden in de gelezen UI/evaluator; geen twee uitgevoerde reviewers |
| Conceptopslag | Algemene conceptroute code aanwezig; beleid onderscheidt concept en vaststelling | Geen ESS-04-opslag/herlaadproef; note of validation_issues is niet op zichzelf versiegebonden ESS-04-oordeel |
| Vaststellen | Algemene handmatige actie en CON-voorwaarden vastgelegd; ESS-04-runtime open | Geen ESS-04-poortbesluit afleiden uit excluded_from_score of severity; algemene DEF-630 niet opnieuw opgelost/gebouwd |
| Export/herbeoordeling | Bestaande service/exportcode en snapshotcontracten onderscheiden | ESS-04-oordeel/grond/versie in echte export en herbeoordeling niet aangetoond |

### Wat menselijke beoordeling werkelijk moet aantonen (voorstel)

Een zichtbaar label review_required zegt uitsluitend dat een inhoudelijk oordeel nodig is. Voor een bruikbaar ESS-04-oordeel: benoem criterium/passage, bedoelde betekenis, relevante context/bronversie, gebruikte gevalsgegevens/methode, oordeel en motivering, onzekerheid en eventuele strijdigheid. Bind dat aan tekst- en normversie plus werkelijke beoordelaar/rol en tijd. Bewaar historie en invalideer toepasselijkheid gericht na materiële wijziging. Caller-strings of model-generated reviewvelden zijn geen vertrouwde actor.

Gebruik de gedeelde beoordelings-/snapshotvoorzieningen zodra hun concrete interfaces geleverd en bruikbaar zijn. Geen ESS-04-eigen database of CON-02-veld als verborgen ESS-container. Maak per oplevering opslag, sluiten/heropenen, readback, gewijzigde tekst/context/bron/norm, onbevoegde actor en export aantoonbaar.

**Twee beoordelaars:** aanbevolen voor kalibratie van risicovolle/grenscases, niet als universele extra productpoort. Beiden eerst onafhankelijk met dezelfde bevroren casus, norm en bronnen. Registreer oorspronkelijke oordelen en redenen; onderscheid (a) verschil over bedoelde betekenis/bron, (b) verschil in gevalsbewijs, (c) lees-/toepassingsfout, (d) resterende beoordelingsruimte. Los feitelijke tegenspraak op via broncontrole; beleidskeuze naar Chris. Een consensuspercentage toont hoogstens overeenstemming, geen juistheid of ESS-04-score. De gevraagde Codex/Cowork-kruisreview is evenmin automatisch deskundige praktijkvalidatie.

## Q5 — app-, regel- en instructievoorstel

Volledige N1, G1, T1, H1, positieve/negatieve/grensvoorbeelden, huidige passages en exacte vervangteksten staan in instructievoorstellen-v1.md.

**G:** navolgbaar criterium op aangeleverde betekenisgrond, kwalitatief toegestaan; relevante grens/noemer/tijd behouden. Verduidelijk ontbrekende/conflicterende grond via ondersteunde appflow. Geen fictieve bronnen of drempels.

**T:** kern ongewijzigd; aanvullende velden afzonderlijk als bewijs; daadwerkelijk menselijk oordeel scheiden van indicatoren, onbekend bewijs, niet-uitvoering en technische fout. Bekende overtreding én resterende onzekerheden kunnen naast elkaar zichtbaar zijn. Geen willekeurig numeriek ESS-04-cijfer.

**H:** eerst oorzaak, daarna eventueel afzonderlijk voorstel:

| Diagnose | Benodigd onderscheidend bewijs | Gevolg |
|---|---|---|
| Generatieovertreding | Geldige bron/instructie aantoonbaar ontvangen; ruwe modeltekst wijkt af | Gericht voorstel mogelijk met bekende grond |
| Tegenstrijdige instructies | Volledige eindprompt eist tegelijk onverenigbare vormen/criteria | Eerst promptcontract corrigeren, geen model schuld toeschrijven |
| Invoer-/transportverlies | Invoer verschilt van verzonden prompt of toets-/opslagobject | Transport herstellen; geen nieuwe bron verzinnen |
| Foutpositieve evaluator | Navolgbaar kwalitatief criterium afgekeurd vanwege ontbreken cijfer | Evaluatoruitkomst corrigeren; tekst behouden |
| Ontbrekend bewijs | Nodige bron, meetconventie of gevalsdata niet beschikbaar | Open vraag; geen inhoudelijke repair |
| Technische fout | Dienst-/schema-/runtimefout | Error apart, origineel behouden |
| Schadelijke nabewerking | Ruwe output correct, latere kandidaat verschuift grens of betekenis | Behandeling van verschil en versie; hertoets werkelijk opgeslagen kandidaat |

Een gewijzigde kandidaat vraagt hertoetsing van ESS-04 plus geraakte betekenis-/bronregels; bij onbekende afhankelijkheden alle toepasselijke controles. Automatisch herstel is hier niet geactiveerd. Bestaande DEF-638-grens maximaal één poging blijft bij latere implementatie, met stop bij conflict, ontbrekend bewijs, betekenisverlies of herhaalde fout. Geen totaalscore als sturing.

**Poortkeuze voor Chris:** aanbeveling is geen nieuwe zelfstandige ESS-04-blokkade of aparte akkoordknop nu afleiden. Houd open/negatief zichtbaar binnen bestaande expertbeoordeling; negatieve uitkomst wordt door vaststelling niet positief. Alternatief is een expliciete strengere ESS-04-poort zodra betekenis/bewijscontract en keten geleverd zijn; dat vraagt een nieuw regellokaal besluit met impactanalyse. De keuze “geen zelfstandige poort” van ESS-01/02 is niet vanzelf reeds voor ESS-04 vastgesteld.

## Q6 — acceptatie, keuzes, risico's

De zeven historische scenario's zijn behouden; 23 nieuwe onderscheidende scenario's hebben G/T/H en bewijsstatus. N01–04 zijn beperkt functioneel onderzocht; de overige verwachtingen zijn voorstellen. Voor daadwerkelijke acceptatie: norm-/bronversie bevestigen, verwachtingen onafhankelijk deskundig labelen, route-/storage-/reviewproof uitvoeren waar ontbrekend, UI en export met open/negatief/oordeel controleren, actieve instructies en volledige prompt controleren.

Chris kan na kruisreview kiezen:

1. N1 vaststellen: kwalitatieve toepasbaarheid zonder cijferplicht; open normen behouden waar onderbouwd, geen willekeurige drempels.
2. Relevante context per criterium eisen, zonder universele metadataverplichting; gevalsbewijs en definitiefout onderscheiden.
3. Menselijk ESS-04-oordeel geïntegreerd in bestaande review, signalen niet beslissend; voorgesteld geen nieuwe zelfstandige poort. Geen ESS-04-AI-jury zonder eigen besluit.
4. Twee beoordelaars inzetten voor gerichte kalibratie/acceptatie, niet alle records automatisch tweepersoons maken.
5. Concrete instructie-/appverbeteringen laten specificeren onder bestaande owners; daarna afzonderlijke uitvoeringsopdracht.

Belangrijkste risico's: meetbaarheid verwarren met juistheid; bronversie/populatie verschuiven; hoofdkenmerk alleen in toelichting; oude review op nieuwe kandidaat; herstel dat semantiek verengt; actuele levering verwarren met oud codebewijs; cijfers uit technische contractvelden als kwaliteit tonen.

Bewijsgaten: actuele ASTRA-revisie; werkelijk menselijk ESS-04-oordeel inclusief opslag/readback/stale/export; volledige G/T/H/UI-route; deskundige verwachtingen; Cowork-bijdrage/reviews/verwerkingen/synthesecontrole. Geen nieuwe implementatie of issue nodig om deze open punten eerlijk te registreren.

## Dekking van de 14 dossieronderdelen

| Onderdeel | Vindplaats |
|---|---|
| 1 doel/betekenis | Q1, N1 |
| 2 norm/besluiten | Q1, bronregister B01–B07/S05–S07 |
| 3 toepasselijkheid | Q1 en routetabel Q4 |
| 4 context | Q2 veldmatrix en voorwaardelijk bewijs |
| 5 definitiebronnen | Q2, CON-02-relatie, N12/13 |
| 6 ontologie/relaties | Q2/Q3, N14/19 |
| 7 aanvullingen | Q2 veldmatrix, voorbeelden-skillvoorstel |
| 8 appgedrag | Q4, P01–P04 oud en actueel |
| 9 skills/prompts | Q5 en instructievoorstellen-v1 |
| 10 status/score/poorten | B01, Q4/Q5 poortkeuze |
| 11 proeven | bronregister, verwachting/uitvoer/script |
| 12 samenhang | Q3 |
| 13 verbeteringen/review | Q5; eigen voorstel gereed, wederzijdse review nog niet uitgevoerd |
| 14 acceptatie/overdracht | Q6, casusregister, Cowork-opdracht en statusmanifest |

De zelfstandige eerste bijdrage is hiermee inhoudelijk uitgewerkt, inclusief expliciete hiaten. Dit is geen gezamenlijke eindoplevering en geen claim dat ESS-04 werkt in de productieapp.
