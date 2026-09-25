# ADR-003: Gestructureerde bewijscontrole voor ESS-05

**Status:** Voorgesteld — ontwerp, geen implementatiebesluit  
**Datum:** 2026-09-25 · **Beslisser:** Chris · **Issue:** DEF-768

## Context

Chris heeft het uitwerken van dit ontwerp toegestaan. Dit document maakt een vervolgbesluit concreet. Er zijn voor dit ontwerp geen appaanroepen gedaan. De app, modelinstructies en skillpakketten zijn niet aangepast.

R7 behaalde 20/20 juiste eerste statussen en 8/8 juiste herhaalstatussen, maar slechts 18/20 en 7/8 volledig juiste antwoorden. R705 bevat een letterlijk maar niet dragend citaat plus een ongegronde uitsluiting; R712 een verkeerde inhoudsindicator; R719 H1 een bronparafrase met een ander onderwerp en ruimere strekking. Deze drie bevindingen blijven open. [R7-eindrapport](../../reports/DEF-768-AI-20260925-R7/uitkomst-en-vervolg-v1.md)

De bestaande code controleert structuur, letterlijke citaten en bindingsgegevens. De prompt vraagt bovendien al een dragend citaat en een consistente indicator. Dat zijn afzonderlijke garanties: een geslaagde letterlijkheidscontrole bewijst geen geldige gevolgtrekking. `_buurdeel` vermeldt zelfs expliciet dat de code betekenis/context niet toetst. Bronnen: [contract](../../src/domain/ess05/contract.py) (`valideer_oordeel`, `_bewijsfouten`, `_buurdeel`) en [toetsdienst](../../src/services/validation/ess05_assessment_service.py) (`_systeemprompt`, `_beoordeel_antwoord`).

Constraints: bestaande ESS-05-norm en statusbetekenissen behouden; geen casuswoorden in productregels; geen automatische tekstcorrectie; geen versoepeling van volledige inhoudelijke acceptatie. Bestaande Python/Streamlit/SQLite-stack en modelrouter gebruiken. Geen nieuwe dependency of databasekolom voorgesteld. De softwarewijziging zal wel schema's, parser, versie-/cachebinding, transport en weergave raken en ruim boven de kleine-wijzigingsgrens uitkomen. Uitvoering vereist een afzonderlijk besluit.

## Voorgestelde beslissing

**Ontwerp optie C: een gestructureerd conceptoordeel, vaste controles in code en één afzonderlijke semantische verificatie voordat het oordeel wordt toegepast.** Begin na goedkeuring met een offline implementatie; bepaal een betaalde proef pas na die technische oplevering.

Dit is een toetsbare betrouwbaarheidshypothese. Een tweede modelcontrole kan dezelfde fout maken en geeft geen garantie op semantische juistheid. Optie B alleen is onvoldoende onderbouwd als oplossing voor R7.

## Opties en trade-offs

| Optie | Werking en voordeel | Complexiteit / vertrouwdheid | Kosten / schaalbaarheid / onderhoud |
|---|---|---|---|
| A. Huidige structuur en extra zelfcontrole-instructies | Kleine wijziging; bestaande keten blijft bruikbaar. Twee R7-fouten schenden echter al expliciete instructies. | Laag; geheel bekend patroon. | Eén modelaanroep per toetsing; groeit lineair met gebruik. Meer instructieonderhoud zonder aangetoonde oplossing voor deze fouten. |
| B. Gestructureerd bewijs en vaste controle | Expliciete kenmerken, bronplaatsen en afgeleide indicator. Maakt tegenstrijdige velden en niet-bestaande verwijzingen controleerbaar. | Middel; sluit aan bij huidige contractvalidatie, maar vereist nieuwe antwoordstructuur. | Eén modelaanroep met meer uitvoer; lineaire groei, meer parser-/render-/versieonderhoud. Geen semantische waarborg voor verkeerde classificatie of niet-dragende citaten. |
| C. B plus afzonderlijke semantische verificatie **(voorkeur)** | Een tweede controle beoordeelt kenmerkclassificatie, gevolgtrekkingen en volledige toelichting tegen het oorspronkelijke materiaal. | Hoog; router en opslag zijn bekend, tweestapsbeoordeling en bewijsbinding zijn nieuw. | Maximaal twee logische modelverzoeken per gewone toetsing; tweede stap is sequentieel. Meer tokens, latency, uitval- en onderhoudspaden. Hergebruik alleen bij volledig gelijke binding. Werkelijke bedragen en responstijden nog niet gemeten. |
| D. Iedere uitkomst handmatig afronden | Mens beslist over alle inhoud en bewijs. | Technisch middel; productproces en bevoegdheden veranderen wezenlijk. | Modelkosten kunnen beperkt blijven; menselijk werk groeit per toetsing. Een nieuwe acceptatie- en bedieningsafspraak is nodig. Geen impliciete keuze in dit voorstel. |

C pakt het ontbrekende type controle rechtstreeks aan. De prijs is extra runtimecomplexiteit en kans op onterechte weigering. Daarom telt het tegenhouden van een fout antwoord niet als een geslaagde inhoudelijke toetsing. Een nieuw traject moet zowel juiste eindantwoorden als onterechte weigeringen meten.

## Ontwerp van het contract

Onderstaande velden zijn een voorgesteld logisch contract, nog geen geïmplementeerd JSON-schema. De implementatie moet dit gesloten en versiegebonden maken. Geen vrije extra sleutels of reparatie van ongeldige uitvoer.

### 1. Conceptoordeel van de eerste stap

| Onderdeel | Voorgestelde inhoud en vaste controle | Wat semantisch blijft |
|---|---|---|
| `core_features` | Lijst van unieke ID's met één letterlijk kernfragment per genoemd inhoudelijk kenmerk. Genus kan afzonderlijk als kernfragment worden aangewezen. | Of een fragment werkelijk een kenmerk naast het genus benoemt. Voor `false` volstaat minstens één echt kenmerk; geen nieuwe eis om alle kenmerken op te sommen. Een lege lijst vereist controle van de hele kern. |
| `claims` | Korte inhoudelijke uitspraken met unieke ID, afgebakende strekking en verwijzingen naar materiaalplaatsen. Alle algemene/buurredenen, ontbrekende kenmerken, onzekerheden en voorstelredenen lopen via deze lijst. | Of iedere uitspraak klopt, geen andere drager gebruikt, geen geldige doelgevallen uitsluit en de bron niet sterker maakt. |
| `evidence` | Materiaal-ID, materiaalhash, begin/eindpositie en citaat. Posities verwijzen naar de exact gebonden tekst, niet naar een nieuw genormaliseerde kopie. Controle op bereik en gelijkheid met die tekst. | Relevantie en bewijskracht. Een citaat dat bestaat kan de claim alsnog niet dragen. |
| `neighbours` | Exact de verwachte buur-ID's; per buur bestaand onderscheidlabel, verwijzingen naar claims en waar vereist een aaneengesloten kerncitaat. Bestaande verplichtingen voor ontbrekend kenmerk/onzekerheid behouden. | Geldigheid van de afgrenzing, overlap en informatielacune. Het onderscheidende fragment mag het genus omvatten wanneer dát de brongebonden afgrenzing draagt. |
| `proposals` | Bestaande herkomstregels behouden; elk voorstel heeft redenclaims. Bronherkomst eist passende bronverwijzing. Een modelvoorstel behoudt herkenbare modelherkomst. | Werkelijke kandidaatstatus en relevantie binnen dezelfde vergelijkingsruimte. Een genoemd gegeven is niet automatisch een zelfstandige buur. |
| `question` | Bestaande ene gerichte vraag en prioriteit behouden. Ingebedde feitelijke aannames verwijzen ook naar gecontroleerde claims. | Of de vraag nodig is en geen onjuist uitgangspunt bevat. |

`lacks_differentia` vervalt als zelfstandig door het model aangeleverd invoerveld. De app leidt het af uit de **goedgekeurde** kenmerkenlijst: leeg → true, niet leeg → false. Het blijft beschikbaar in het toegepaste oordeel voor de bestaande statusberekening. Een leeg lijstje is dus geen zelfstandig bewijs dat inhoud ontbreekt.

Materiaal kan de definitiekern, bevestigde buurdefinitie, context, betekenisafspraak of aangeleverde bron zijn. Niet iedere geldige beoordeling heeft een externe bron nodig. Claims over afwezigheid verwijzen naar de volledige gecontroleerde materiaalset met strekking `absence_in_supplied_material`; ze vereisen geen verzonnen letterlijk citaat voor iets dat er juist niet staat. Afwezigheid van broninformatie geldt nooit als bewijs van een ontkenning. Gevolgtrekkingen krijgen de rol `inference` met hun premissen; zij worden niet gepresenteerd als letterlijke bronuitspraken.

De app bouwt de zichtbare onderbouwing uit vaste verbindende tekst en de gecontroleerde claims/citaten. Geen extra vrije modelparagraaf daarna. Ook `missing_feature`, onzekerheid en vragen vallen onder verificatie. Het weglaten van een foutieve noodzakelijke onderbouwing om een geval te laten slagen is geen geldige reparatie. Een correct nieuw antwoord hoeft daarentegen geen overbodige bronparafrase te produceren.

### 2. Semantische verificatie

Eén afzonderlijk verzoek ontvangt de oorspronkelijke norm, volledige gebonden invoer, het conceptoordeel en zijn exact berekende hash. Geen modelgesprek of zelfcontrole uit de eerste stap, geen R7-labels, geen voorgaande verwachtingen of voorbeeldantwoord. Het controleert:

1. Of de kenmerkenclassificatie klopt, inclusief lege verwijzingen, concrete maar gedeelde kenmerken en afwezigheid van enig kenmerk naast het genus.
2. Of ieder aangehaald kernfragment de bedoelde afgrenzing zelf bevat. Een andere goede reden elders mag een niet-dragend citaat niet redden.
3. Of alle claims gedragen zijn, inclusief onderwerp, relaties, modaliteit, reikwijdte en alternatieven. Een onjuiste deelzin maakt het geheel niet volledig correct.
4. Of relevante gegevens zijn gemist: volledige vergelijking met alle actieve buren, juiste omgang met doel-/buurgevallen en overlap, geen vernauwing of onterecht `unclear`.
5. Of voorstellen en vraag inhoudelijk gerechtvaardigd zijn. Geen bron van een afzonderlijke objectsoort maken uit uitsluitend een registratiefeit.

Het verificatieantwoord bevat `candidate_hash`, een versie, per verplicht onderdeel/claim/kenmerk/buur/voorstel/vraag een uitkomst `supported`, `unsupported` of `undetermined`, plus een korte aan het materiaal gebonden bevinding. Vaste code eist volledige, unieke dekking en leidt de eindbeslissing af: alleen alle verplichte controles `supported` geeft vrijgave. Een losse algemene `approved=true` kan ontbrekende controles niet vervangen. Ook de conclusie dat een lege kenmerkenlijst volledig is krijgt een verplicht controle-item.

De verifier mag een **correct geformuleerd** `unclear` ondersteunen wanneer de bron echt te weinig informatie bevat. `undetermined` betekent hier dat de verifier de juistheid van het conceptoordeel niet kan vaststellen. Dit zijn verschillende lagen.

Gebruik aanvankelijk dezelfde geconfigureerde modelkeuze via de router, met een eigen verificatietaak en promptbinding. Dit geeft scheiding van verzoeken, geen onafhankelijkheid van modelfouten. Een ander model of een menselijke beslisser is een aanvullende ontwerpkeuze; daar is nu geen bewijs voor verzameld. Geen automatische consensus-, herstel- of retrylus bij inhoudelijke afwijzing. De tweede stap schrijft het eerste antwoord nooit om.

### 3. Versies, opslag en afleiding

Voorstel: ESS-05-contract naar `ess05/2`, met afzonderlijke schema-, beoordelingsprompt-, verificatieprompt- en rendererversie. De norminhoud blijft gelijk. Bind beide stappen aan materiaalhashes, buurstatussen, afgewezen voorstellen, bedoelde betekenis en beide provider/modelidentiteiten. De verificatie bindt daarnaast aan het exacte concept. Cache en replay moeten alle relevante bindingsvelden vergelijken; een gelijk inputfingerprint alleen volstaat niet.

Bewaar concept, verificatie en toegepast oordeel gescheiden in het bestaande beoordelingsdocument, met twee attributies, antwoordhashes, tijdstippen en token-/callregistratie. Alleen de goedgekeurde combinatie krijgt `status=assessed`. Fouten hebben geen toepasbaar oordeel en worden niet als succes gecachet. Publieke uitvoer, opslag, readback en UI mogen nooit rechtstreeks een ongoedgekeurd concept tonen als geldige motivering.

De bestaande opslag gebruikt JSON in `generation_prompt_data` en bewaart het vorige document bij wijziging in historie; de replay beslist actualiteit. Een nieuwe SQL-kolom is daarom niet het uitgangspunt. [Registratie](../../src/database/ess05_registratie.py)

Oude `/1`-documenten blijven ongewijzigde historie. Geen synthetische verificatie aan historische antwoorden toevoegen en geen automatische herbeoordeling met betaalde calls bij inlezen. Refactor de actieve keten naar `/2`; geen parallelle legacy-engine. Een oude lege-ruimtebevestiging heeft ook contract-/fingerprintbinding: bij afwijking niet stilzwijgend herbevestigen. Bestaande geldige expertbesluiten blijven volgens hun eigen actualiteitsregels behandeld.

## Status- en foutafhandeling

De huidige code scheidt een technische beoordelingsstatus van de ESS-05-normstatus. Structuurfout geeft `malformed_response`, niet-verifieerbaar citaat `unverifiable_evidence`; `status=error` wordt als publieke `error` weergegeven. Ontbrekende/historische beoordeling geeft nu `review_required`. [Toetsdienst](../../src/services/validation/ess05_assessment_service.py) en [contract](../../src/domain/ess05/contract.py), `_uitkomst_uit_oordeel`.

| Situatie in het ontwerp | Voorgestelde afhandeling |
|---|---|
| Ongeldig schema, onbekende ID, niet-bestaand citaat | Bestaand structuur-/bewijserrorpad; geen semantische verifier starten als de vaste controle al faalt. |
| Verifier wijst inhoud af of kan juistheid niet vaststellen | Beoordelingsdocument `error`, voorstel nieuw subtype `semantic_verification_failed` met fase en bevinding. Geen inhoudelijke fail/open/pass en geen herschrijving. |
| Timeout, onleesbaar of verkeerd gebonden verificatieantwoord | Technische error met fase `verification`; geen terugval op het ongetoetste eerste antwoord. |
| Juist maar inhoudelijk onzeker conceptoordeel | Na positieve verificatie de bestaande `unclear`-/vraagroute toepassen; onzekerheid niet bestraffen als uitvoerfout. |
| Volledig gecontroleerd oordeel | Bestaande prioriteit behouden: ontbreken differentia → fail; bevestigde niet-onderscheiden buur → fail; geldige open vraag → review_required; anders pass. Bestaande lege-ruimte-/invoerregels behouden. |
| Historisch of gewijzigd materiaal | Historisch/niet actueel volgens bestaande replay; niet als verse verificatiefout of geldige pass tonen. |

Het nieuwe errorsubtype is onderdeel van het voorgestelde contractbesluit. Het betekent dat de modeluitvoer onbruikbaar is, niet dat de definitie onjuist is. UI-actie: opnieuw toetsen of de fout melden, zonder te suggereren dat de gebruiker de definitie moet veranderen. Een tweede poging gebeurt alleen via een nieuwe expliciete toetsactie; nooit heimelijk om de acceptatiescore te verhogen.

## Toetsing van het ontwerp aan de drie ruwe R7-antwoorden

Bron: [oorspronkelijke invoer en alle antwoorden](../../reports/DEF-768-AI-20260925-R7/inhoudelijke-beoordeling-invoer-t-v1.json). Onderstaande beoordeling is een handmatige ontwerpdoorloop, **geen uitgevoerde implementatie- of modeltest**. Het afwijzen van oud JSON omdat `/2` andere velden heeft, telt niet als inhoudelijke detectie.

| Ruw antwoord | Wat vaste code wel/niet kan | Vereiste semantische bevinding en correcte uitkomst |
|---|---|---|
| `t_eind\|R705\|1`: citaat “de vrijgavecode voor een sluiting bevat”; reden stelt dat geen draaihaak dat kenmerk kan dragen | Het fragment komt letterlijk voor. Ook met een citaat over verschillende objectsoorten erbij kan een ongeldige gevolgtrekking structureel voldoen. **Geen harde detectie.** | Afwijzen: onderscheid gegevensobject/werktuig bewijst niet dat een werktuig geen code kan bevatten. Het fragment mist het dragende objecttype. Een nieuw volledig juist antwoord kan een fragment met “gegevensobject” citeren en die typegrens uitleggen. Dan pass; de oorspronkelijke fout weigeren blijft een mislukte toetsing in acceptatie. |
| `t_eind\|R712\|1`: reden erkent alleen onbenoemde profieleigenschappen, indicator toch false | Bij een terecht lege kenmerkenlijst kan de indicator niet meer false worden. Zet het model de profielverwijzing onterecht in de lijst, dan accepteert een letterlijkheidscheck die gewoon. **Alleen de afleiding is hard.** | Verifier moet de lege verwijzing herkennen; het kenmerk uit de bron mag niet ongemerkt in de kern worden gelezen. Een nieuw juist concept bevat geen inhoudelijk kernkenmerk; app leidt true af en komt op fail. Geen reparatie van een fout geclassificeerd lijstje. |
| `t_herhaling\|R719\|herhaling-1`: “de vastlegging van het tijdstip is volgens de bron een attribuut en geen afzonderlijk begrip” | Een letterlijk broncitaat naast deze parafrase detecteert de betekenisfout niet. Vaste rendering voorkomt wel dat na verificatie een nieuwe, ongecontroleerde zin ontstaat. | Afwijzen: bron noemt **tijdstip** een attribuut; zij ontkent een afzonderlijk registratieobject of extra verwerkingsgangsoort, niet ieder begrip. Een nieuw juist antwoord kan de routevolgorde en ontbrekende buur benoemen, eventueel letterlijk citeren. Dat blijft review_required, zonder verzonnen buur. |

R705 H1/H2 en R719 eerste/H2 waren volledig correct. Die antwoorden zijn belangrijke positieve controles tegen onterechte afwijzing. De voorgestelde verifier is nog niet op deze antwoorden aangeroepen; zijn gevoeligheid en onterechte weigeringen zijn onbekend.

## Historische foutklassen R1–R7

Onderstaande classificatie gebruikt de behouden eindrapporten; zij is geen nieuwe volledige grading van alle ruwe antwoorden. Geen enkele semantische rij is met dit ontwerp al aantoonbaar automatisch opgelost.

| Historische voorbeelden | Vaste controle | Te bewijzen inhoudelijke controle |
|---|---|---|
| R1 E06; R5 ontwikkeling R313: ongeldige JSON/sleutel | Bestaande parser weigert; behouden. | Inhoudsverificatie vervangt deze gate niet. |
| R1 E10/E13/E15; R4 R411; R7 R712: kenmerkenindicator | Verwijdert apart tegensprekende modelboolean. | Lege verwijzing versus werkelijk, mogelijk gedeeld kenmerk. |
| R1 E16; R7 R705: niet-dragend citaat | Alleen aanwezigheid en binding. | De geciteerde afgrenzing zelf draagt de conclusie. |
| R1 E06/E09; R2 R215/R220; R3 R312: ongegronde kandidaat/bronherkomst | ID/citaat en volledigheid van voorstelclaims. | Zelfstandige soort, juiste drager en relevante vergelijkingsruimte. |
| R1 E14; R3 R313; R4 R410: verzonnen ontkenning/onterecht unclear | Geen algemene semantische detectie. | Volledig materiaal, onderscheid gebrek in kern versus gebrek in bron. |
| R3 R308; R4 R414; R5 R508; R6 R614; R7 R719: onjuiste aanvullende reden/vernauwing | Alle zichtbare claims moeten door controle lopen. | Overlapdrager, juiste deelredenen en behoud van geldige doelgevallen; ook alternatieven. |
| R5 R514: onterechte pass ondanks buurgeval buiten doelbegrip binnen kern | Status afleiden uit labels lost verkeerde labels niet op. | Brongebonden tegengevallen; overlap rechtvaardigt geen te ruime definitie. |
| R1–R4 G-fouten: relaties, vermogen, betekenisdrager | Buiten het voorgestelde T-verificatiepad. | Geen herstelclaim voor generatie; behouden G-bewijs alleen binnen aantoonbaar gelijk gebleven scope. |

Bronnen: [R1](../../reports/DEF-768-AI-20260924/uitkomst-en-vervolg-v1.md), [R2](../../reports/DEF-768-AI-20260924-R2/uitkomst-en-vervolg-v1.md), [R3](../../reports/DEF-768-AI-20260924-R3/uitkomst-en-vervolg-v1.md), [R4](../../reports/DEF-768-AI-20260924-R4/uitkomst-en-vervolg-v1.md), [R5](../../reports/DEF-768-AI-20260925-R5/uitkomst-en-vervolg-v1.md), [R6](../../reports/DEF-768-AI-20260925-R6/uitkomst-en-vervolg-v1.md), [R7](../../reports/DEF-768-AI-20260925-R7/uitkomst-en-vervolg-v1.md).

## App, skills en gevolgen

**Appimpact:** ESS-05-contract en toetsdienst; eigen verificatietaak in router/config; serviceconstructie; bindings-/cache-/replaycontrole; beoordelingsdocument en doorgeefschema; opslag/readback; UI voor foutfase en gecontroleerde onderbouwing; proefrunner/grootboek; bijbehorende tests. De huidige `Beoordelingsbinding` wordt uit ESS-03 geïmporteerd: voorkom dat uitbreiding voor twee ESS-05-stappen de ESS-03-contracten verandert. Exacte bestandsselectie hoort bij het implementatieplan. Geen norm- of G-promptwijziging in dit voorstel.

**Skills:** dezelfde norm, onderscheid tussen letterlijke aanwezigheid en inhoudelijk dragen, bronherkomst en complete onderbouwing opnemen. Een tekstskill heeft niet vanzelf de parser, bindingscontrole en aparte runtimeaanroep van de app. Geef een standalone skill daarom geen label “technisch geverifieerd” na alleen zelfcontrole. Voor gelijkwaardige automatische acceptatie moet hij de geverifieerde appketen gebruiken; een zelfstandige tweestapsrunner bouwen is een afzonderlijke scope. Totdat zo'n route beschikbaar en getest is, is de standalone uitkomst een herkenbaar ongeverifieerd voorstel, geen bewijs dat appacceptatie gehaald is. Dit beperkt de claim; het vervangt geen oorspronkelijke acceptatie-eis voor skills.

**Moeilijker:** groter antwoordcontract, extra tokens en latency, meer mogelijkheden voor malformed uitvoer, strengere actualiteitsbinding en meer historie. Onterechte verifierafwijzingen kunnen bruikbare antwoorden blokkeren. Bronmateriaal kan beide stappen dezelfde verkeerde interpretatie geven. Brontekst en conceptoordeel blijven onbetrouwbare invoer voor de verifier en mogen zijn instructies niet wijzigen; dit moet expliciet worden getest.

**Grenzen:** de huidige R7-acceptatie blijft niet gehaald. Geen zekerheid over minder fouten tot echte modelproeven. Skills v11 blijven alleen voorbereid; liveactivatie vereist nog appmerge én ALG-391 Task10 A–E. Dit ontwerp activeert niets en verandert geen bestaande automation.

## Verificatie en kosten vóór een echte proef

Na een implementatiebesluit eerst offline: gesloten schema's, afleiding, citaat-/ID-/dekkingsfouten, gewijzigd concept of materiaal, verkeerde verifierbinding, geen ongetoetste uitvoer, geen verborgen herstelcalls, opslag→readback→UI en behoud van bestaande statusprioriteit. Test zowel afgewezen negatieve antwoorden als positieve controles. Gecorrigeerde `/2`-fixtures zijn expliciet nieuw ontworpen; bewaar oorspronkelijke R1–R7-antwoorden ongewijzigd. Stubs bewijzen ketengedrag, niet dat een model semantische fouten vindt.

Vervolgens een afzonderlijk proefvoorstel met twee onderscheiden vragen: (1) vindt de verifier bekende verkeerde claims zonder juiste controles af te wijzen; (2) levert de volledige keten nieuwe, geheel correcte antwoorden? Eerste poging blijft eerste poging. Geen moeilijke gevallen wegfilteren, geen error als inhoudelijk succes meetellen. Behoud 20/20 volledige nieuwe eindantwoorden en 8/8 volledige vooraf gekozen herhalingen, nul onterechte goedkeuringen/afkeuringen, nul onnodig open, geen betekenisverlies en geen pass met ondeugdelijke onderbouwing. Nieuwe errors tellen als mislukte afleveringen; rapporteer malformed en semantische weigeringen apart.

Voor N volledige nieuwe toetsingen vraagt optie C maximaal 2N logische modelverzoeken, vóór expliciet begrote transportpogingen; een vroeg parserfalen kan de tweede stap voorkomen. Verifier-only proeven vragen daarnaast eigen aanroepen. Registreer iedere feitelijke SDK-aanroep per fase en reserveer budget vóór elke stap, inclusief eventuele providerretries. Bedrag = werkelijk eerste-stapgebruik plus verificatiegebruik tegen de geldende routertarieven; geen verdubbeling van een oud bedrag als vermeende exacte raming. Een timeout-/tokenplafond moet vóór een proef worden vastgelegd; afgekapt materiaal is geen geldige verificatie.

De eerdere suggestie “35 extra calls” hoort bij een andere opzet en is hiervoor geen passend budget. Cumulatief blijft de actuele teller 359. De drie ongebruikte R7-reservecalls zijn uitsluitend transportreserve van R7. Er is nu geen nieuwe betaalde ronde of callbudget toegestaan.

## Acties en beslisgrens

1. Dit ontwerp op concrete tegenvoorbeelden, statusroutes, binding en skillclaims laten controleren; ontwerpbevindingen verwerken zonder productcode of appaanroepen.
2. **Eerstvolgend besluit voor Chris:** optie C als richting en de afgebakende offline implementatie van bovenstaande keten goedkeuren. Dit omvat de benodigde contract-/parser-/consumerwijzigingen en bijbehorende voorbereiding van skillinstructies. Geen nieuw model, betaalde proef of liveactivatie daarin inbegrepen.
3. Bij dat besluit: concreet implementatieplan en acceptatiegevallen vastleggen. Coördinator organiseert; dezelfde echte Claude Code CLI implementeert en corrigeert; dezelfde onafhankelijke Codex CLI reviewt de concrete diff. Coördinator schrijft de software/tests/bijbehorende prompts niet zelf. TDD, relevante lint en projectgates; eindbewijs aan de exacte versie binden.
4. Pas na die offline oplevering een onderbouwd, begrensd proefplan en budget ter beslissing aanbieden. Bij onbewezen of onvoldoende semantische werking blijven R7-E01/E02/E03 open. Geen automatische volgende ronde.

ADR-001 en ADR-002 worden niet vervangen. DEF-768 blijft In Progress.
