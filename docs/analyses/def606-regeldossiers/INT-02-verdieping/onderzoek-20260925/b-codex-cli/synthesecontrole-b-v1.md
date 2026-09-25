# INT-02 — synthesecontrole door onderzoeker B v1

25 september 2026 · DEF-771 · Codex CLI, dezelfde sessie 01a0d783-365b-7d82-81d3-684fd0e016fc. Eén afgesproken synthesecontrole; geen nieuw onderzoek, implementatie, modelcall of agent. **Oordeel: de synthese v1 is nog niet gezamenlijk afgerond.** Zij bevat de hoofdlijn, maar verliest bij het samenvoegen enkele reeds overeengekomen beperkingen en gebruikt een verouderd casusregister. Hieronder staan de benodigde correcties voor v2.

## Leesbasis en bewijsgrens

Volledig gelezen: de drie gezamenlijke v1-documenten, A's onderzoek v2 en verwerking v1, en aanvullend A's gewijzigde casusregister v2. Vergeleken met B's onderzoek/casusregister v3, beide reviews en verwerkingen en het reeds beschikbare proefbewijs. Alle voor deze controle benodigde bestanden zijn leesbaar. Bronbinding: [bewijs/synthese-bronbinding-v1.json](bewijs/synthese-bronbinding-v1.json). HEAD blijft 26f2374d302fc66fc0b12ed29dc34585f7c0a5c3; de feitelijke branchnaam staat in de eerdere onderzoeken. Geen nieuwe appproef: de materiële verschillen zijn met de exacte documentversies en bestaande uitkomsten te beslissen.

Afkortingen en regelverwijzingen betreffen de **beoordeelde, ongewijzigde** bestanden:

| Code | Bestand |
|---|---|
| S | ../gedeeld/gezamenlijke-synthese-v1.md |
| D | ../gedeeld/besluitnotitie-chris-v1.md |
| R | ../gedeeld/gezamenlijk-casusregister-v1.md |
| A2 / AC2 | ../a-claude-cli/onderzoek-a-v2.md / casusregister-a-v2.md |
| VA / RA | ../a-claude-cli/verwerking-a-v1.md / review-a-op-b-v1.md |
| B3 / BC3 | onderzoek-b-v3.md / casusregister-b-v3.md |
| VB / RB | verwerking-b-v1.md / review-b-op-a-v1.md, met erratum |
| CO | ../a-cowork/normlezing-coordinator-v1.md |

“Materieel” betekent: in de gezamenlijke v2 verwerken vóór afronding. De correcties hieronder zijn onderzoeksadvies, geen alsnog genomen Chris-besluit. Waar een volledig contract wordt aangewezen, gaat de genoemde versie vóór de verkorte synthesezin.

## Puntgewijze controle

### SC-01 → S §2 en §7: hoofdnorm, uitzonderingen en regelrelaties → juist

**Bron:** B3:43–78, A2:24–48; VB RA-B-02/03/05/19, VA RB-A-01/02/03/04/08. **Bevestiging, geen wijziging:** het onderscheid tussen een actorvoorschrift en een beschrijvend criterium is behouden; afleiding voldoet, een kwalitatief kenmerk vereist geen universeel determinisme, constitutieve beschrijving mag, en iedere buurregel motiveert haar eigen normdoel. De brede variant blijft een lokale operationalisering met ASTRA-steun en K1 blijft open. Ook de negatie-/doel-/EN-OF-bescherming en de eigen besluitroutes van INT-01 en INT-10 zijn terecht aanwezig. De onderstaande punten beperken deze bevestiging waar verkorte teksten of individuele casussen hiervan afwijken.

### SC-02 → S:28,71,73,84 en D:7,19: verkorte functiegrens → betekenisverlies

**Materieel. Bron:** B3:76 en VB RA-B-02 weigeren juist een losse formulering “de uitkomst hangt niet af van een afweging”; A2:34,114 en VA RB-A-04. S:28 herstelt dit gedeeltelijk met de constitutieve uitzondering, maar de zelfstandig gebruikte recorduitleg, toetsvraag en skillzin laten die bescherming weer weg. D:7 maakt het ASTRA-voorbeeld bovendien tot algemeen bewijs dat een verplichting in een definitiezin fout is. Een constitutief vereiste mag worden beschreven; het woord “moet” beslist de actorfunctie niet.

**Correctie:** gebruik in S:28 voor de verbodszinnen: **“Zij is geen handelingsvoorschrift of procedure voor een actor en bevat geen discretionaire beslisregel die een afweging over handelen of rechtsgevolg voorschrijft.”** Behoud daarna de volledige uitzonderingen. Vervang de toetsvraag door: **“Bakenen de relevante passages het begrip af met criteria of een deterministische afleiding, zonder als handelingsvoorschrift, procedure of discretionaire beslisregel te functioneren?”** Gebruik in recorduitleg/skill dezelfde functieformulering en voeg toe: **“Een bevoegdheid, beslissing, procedure of constitutief rechtsgevolg als begripskenmerk beschrijven is op zichzelf geen overtreding.”** Vervang D:7 slot door: **“ASTRA labelt het transitie-eis-voorbeeld met ‘moet’ ONJUIST. Dat ondersteunt de brede functiegrens bij een bevestigde voorschriftlezing; het bewijst geen algemeen modaliteitsverbod of actorfunctie op grond van dat woord alleen.”**

S:32 moet “PROCES-label maakt een procedurebeschrijving niet toelaatbaar” vervangen door **“Een PROCES-label rechtvaardigt geen actorvoorschrift als definiens; een proces beschrijven blijft toegestaan.”**

### SC-03 → S:30,32,75,86; R C02/C12/C13/C16/C24/C25/C82/C83/C86 → tegenspraak

**Materieel. Bron:** AC2 gewijzigde rijen C02/C12/C13/C16/C24/C25; A2:32–47; VA RB-A-04/23; B3:64–78 en VB RA-B-01/05. De synthese maakt conditionele referentieoordelen weer absoluut. C13 is in A2 alleen VN bij de actorinstructiepremisse. C16 is niet door “wanneer → wegens” opgelost. R-C24 zegt nog “VN alleen bij afweging”, hoewel A dit expliciet heeft gecorrigeerd. R-C25 mist de bewezen behandelinstructie als brede VN-uitkomst.

**Correctie in de betrokken registercellen en de voorbeeldverwijzingen:**

- **C02:** “ASTRA-label ONJUIST blijft bronfeit. N-breed: VN bij bevestigde actorvoorschriftfunctie. N-eng: geen VN zonder discretionaire grond. Onbesliste functie: O.”
- **C12/C13/C82/C83:** “VN onder beide varianten bij de expliciete synthetische bedoeling als actorinstructie/discretionaire beslisregel; V bij onderbouwde constitutieve beschrijving; O zolang de functie onbeslist is.” C12 heeft de actorinstructiepremisse al in AC2; neem haar zichtbaar over. Bij C82/C83 moet de coördinator de bedoelde premisse vastleggen, geen woordtreffer als bewijs gebruiken.
- **C16:** “V bij onderbouwde beschrijving van de boetegrond; O bij onbesliste functie; onder N-breed VN bij bewezen voorschriftfunctie. ‘Wanneer’ door ‘wegens’ vervangen beslist dit niet.” Bewaar de oorspronkelijke proeftekst.
- **C24/C86:** “O bij onbesliste functie; onder N-breed ook VN mogelijk bij bewezen deterministisch actorvoorschrift; onbepaaldheid alleen is geen INT-02-VN.”
- **C25:** “V bij criteriumfunctie; O bij onbekende functie; N-breed VN bij bewezen toekennings- of behandelinstructie.”

Dit wijzigt semantische referentieverwachtingen, niet de opgeslagen RR-waarnemingen.

### SC-04 → S §§2–6 en R:5,13,22,36,55–56: K1-variantdoorwerking → weglating

**Materieel. Bron:** A2:127; B3:188,243; AC2 C03/C15/C29; BC3 C64/C65. In R betekent “N-A: O” bij C03/C15 ten onrechte dat afwezige discretie automatisch onvoldoende informatie is. C29 mist de variantgrens. C65 krijgt onvoorwaardelijk VN hoewel C64 terecht N-B1 noemt. De exacte G/T/skillteksten zijn breed, maar de variantkeuze is niet overal expliciet verbonden aan die teksten.

**Correctie vóór S §3 en R-tabel:** **“De exacte N/G/T/H- en vervangteksten hieronder zijn het voorstel N-breed. Bij keuze N-eng wordt het zelfstandige actorvoorschriftverbod in alle instructies, meldingen en referentieverwachtingen gezamenlijk verwijderd. Beschrijvende uitzonderingen en betekenisbehoud blijven onder beide varianten gelden.”**

R-C03/C15/C29: **“N-breed VN bij bewezen actorvoorschrift; N-eng geen VN op die grond zonder discretie. Bij voldoende functiegrond en afwezigheid van een discretionaire beslisregel V voor INT-02; bij onbesliste functie O.”** R-C64/C65: **“De voorschrift-VN en daarop gebaseerde H-noodzaak gelden onder N-breed. Onder N-eng volgt zonder discretionaire grond geen INT-02-VN; geen INT-02-herstel laten starten enkel voor dit zelfstandige voorschrift.”** Betekeniswijziging wordt onder geen variant een geslaagde reparatie.

### SC-05 → S:32,34,42; D:40; R:5–7 en alle T-rijen: context en veldrollen → weglating

**Materieel. Bron:** B3:84–109,188; A2:52–74; AC2 algemene voorwaarden. S verwijst naar B-v2 in plaats van v3 en verliest de beperking van afzonderlijke informatiekanalen. R vergeet de algemene contextvoorwaarde uit AC2: 24 van A's 25 P1-invoeren hebben context={}, terwijl de referentiekolom V/VN geeft. Die semantische oordelen zijn alleen zinvol als projectie onder een aanwezige context, niet als gewenste appuitkomst op exact die proefinvoer. D noemt K-9 alleen vóór toetsen, terwijl het ook vóór genereren geldt. Leegtebeleid volgt niet uit K-9 zelf.

**Correctie:** wijs de volledige **B3 Q2/V02-matrix, inclusief RA-B-12/13-scopezin**, als leidende bijlage aan; geen extra G-uitvoerkanaal afleiden uit de kolom met mogelijke AI-voorstellen. Voeg aan R toe: **“Alle inhoudelijke T-referenties veronderstellen een herkende kern en aanwezige vereiste context. Ontbreekt die context in de feitelijke proefinvoer, dan is de gewenste appuitkomst NE; de historische RR-meting blijft afzonderlijk staan. Een intrinsiek helder criterium kan zonder externe bron inhoudelijk beoordeelbaar zijn, maar dat heft K-9 niet op.”**

D:40: **“K-9 verplicht context vóór genereren én toetsen. Zonder context geen uitvoering. Ontbrekende kern wordt in het voorgestelde uitvoeringscontract eveneens NE; dit is geen inhoudelijk normoordeel.”** Bronpassages blijven noodzakelijk wanneer de functie daarvan afhangt, niet verplicht voor ieder helder criterium.

### SC-06 → R:3 en C28/C33; S §12: actuele casusdekking en G/H → betekenisverlies

**Materieel. Bron:** A2:5,167–172; AC2 C04/C10/C11/C17/C18/C33; BC3 algemene G-regel en C03/C50/C51/C60/C64; VB RA-B-13. R verwijst voor alle G/H-verwachtingen naar A-v1 en B-v2. Daarmee worden precies de ingetrokken herstelvoorstellen en het ongedekte extra G-uitvoerkanaal opnieuw leidend. R-C28 staat nog toe dat G C05-vorm voorstelt als gewone omzetting; AC2 noemt C28 wel ongewijzigd maar trekt elders de onderliggende equivalentie terecht in. Dit is dus ook een resterende interne inconsistentie van A's bijlagen.

**Correctie:** vermeld **A-casusregister v2 als delta op v1, met voorrang van A2 §5.4 en deze controle bij C28, en B-casusregister v3**. Neem in het gezamenlijke register de actuele G/H-cellen over, of leg per ID een ondubbelzinnige actuele broncel én expliciete delta vast. Alleen verwijzen naar het oude register volstaat niet.

R-C28: **“Voor dezelfde bewaarde kandidaat gelden dezelfde norm en T-verwachting, ongeacht gegenereerd of aangeleverd. G mag alleen onderbouwd formuleren; C04→C05 is geen bewezen betekenisgelijke stijlvariant. T wijzigt niets. Geen routegelijkheid gemeten.”** R-C33: **“G verzint geen kern. Een voorlopige kern mag uitsluitend voor zover de beschikbare betekenisgrond die zelfstandig draagt; geen extra melding in de één-zin-uitvoer. Zonder gedragen kern volgt zichtbare appafhandeling, geen fictief succes.”**

### SC-07 → S §3: G bij ontbrekende of strijdige betekenisgrond → weglating

**Materieel. Bron:** B3:186–188; A2:134–136; VB RA-B-13; VA RB-A-19. De één-zin-kop is goed, maar de exacte vervanging verliest het expliciete verbod een bronconflict stil op te lossen, de status van een voorlopige kandidaat en de nog onontworpen afhandeling zonder gedragen kern. “Vraag via T” garandeert die afhandeling niet: bij ontbrekende kern is er NE, en O1 geeft vandaag nog geen inhoudelijke O-vraag.

**Exact toe te voegen aan G:** **“Lever uitsluitend de definitiekern als één zin, zonder vraag, bronverantwoording, onzekerheidsmelding of toelichting. Geef bij ontbrekende maar niet strijdige betekenisgrond alleen een voorlopige kern voor zover de beschikbare grond die draagt. Leg bij strijdige grond geen betwiste betekenis stil in de kern vast.”**

**Apptekst na G:** **“De voorlopige status en één noodzakelijke verduidelijkingsvraag horen bij afzonderlijke beoordeling en appweergave: menselijke reviewerhulp bij O1, O-uitkomst bij gekozen O2. De huidige evaluator realiseert dat nog niet. Zonder gedragen kern moet een latere uitvoering veilig onthouden en de ontbrekende keuze zichtbaar maken; geen fictieve definitie als succes opslaan. De precieze afhandeling is uitvoeringsacceptatie, geen nieuw modeluitvoerformaat.”** Dit behoudt V05 zonder extra veld uit de generatieaanroep te eisen.

### SC-08 → S:53–57; R:7: T-status en betekenisgrond → weglating

**Materieel. Bron:** B3:196–215; A2:140–155; VA RB-A-18, VB RA-B-12/15. De vier uitkomsten zijn elders genoemd, maar de exacte T-tekst laat NA-grond en drie inhoudelijke waarborgen weg. R verenigt semantisch O met een nog niet uitgevoerde menselijke beoordeling.

**Voeg aan T toe:** **“Voldoet vereist dat geen INT-02-gebrek of beslissende onzekerheid resteert. Een zelfstandig aangetoond gebrek blijft zichtbaar als andere vragen openstaan. Onbekende feiten over één concreet geval zijn niet automatisch ontbrekende betekenisgrond van de definitie. Niet van toepassing vereist een gemotiveerde reikwijdtegrond buiten het definitietoetsbereik; een afleidingsregel voldoet en een ontbrekende kern is niet uitgevoerd.”**

**R-legenda:** **“O = inhoudelijk onvoldoende informatie met één vraag. Een nog niet gedane menselijke beoordeling blijft apart ‘nog te beoordelen — beoordeling niet uitgevoerd’. Beide kunnen technisch review_required gebruiken, met verschillende reden en uitvoeringsmetadata. NA alleen met reikwijdtegrond; NE/E zonder inhoudelijk oordeel.”** V-melding vermeldt dat andere regels niet zijn beoordeeld. NE/E-meldingen behouden expliciet “Er is geen inhoudelijk oordeel”.

### SC-09 → S:53,57,65; R-C67: versie- en bronbinding → betekenisverlies

**Materieel. Bron:** B3:96,110,163,196,213–215; A2:74,153; VA RB-A-16/22. De historische melding laat bronversie weg; T noemt ook de vastgelegde betekenis niet. Een bron kan wijzigen zonder tekstwijziging. Dat kan een eerdere functiebeoordeling ongeldig maken.

**Correctie:** **“Bind kern, bedoelde betekenis, context, gebruikte bronpassages en normversie aan het oordeel; bewaar passage, grond, uitkomst, actor en uitvoeringsstatus. Een verandering in een van die beoordelingsgronden maakt het eerdere oordeel historisch.”** Historisch-melding: **“INT-02 — Eerdere beoordeling hoort bij een andere tekst-, betekenis-, context-, bron- of normversie. Opnieuw beoordelen is nodig.”** Breid R-C67 uit met wijziging van bron- en normversie. Dit betreft gewenste binding, niet reeds bewezen opslag.

### SC-10 → S §5: H-stopregels en diagnose → weglating

**Materieel. Bron:** B3:219–227; A2:160–174; VA RB-A-21/22; VB RA-B-08/18. Eén poging, origineel/diff en betekenisbehoud zijn goed overgenomen. Weggevallen zijn de volledige diagnoseketen, expliciet stoppen bij technische fout/ontbrekende grond, noodzakelijke namen en de terugval naar alle toepasselijke regels als afhankelijkheden onbekend zijn.

**Toevoegen:** **“Vergelijk waar nodig ruwe modeluitvoer, geëxtraheerde kern, opgeschoonde kandidaat, exact getoetste tekst en opgeslagen tekst, met bron- en normversie. Stop zonder herschrijving bij ontbrekende betekenisgrond of technische fout. Bescherm ook noodzakelijke namen en de referent. Hertoets alle geraakte regels; bij onbekende afhankelijkheden alle toepasselijke regels. Toon een geslaagd voorstel uitsluitend als nieuw concept met werkelijke uitkomsten en resterende open punten.”**

Behoud C64 als positief, voorwaardelijk herstelgeval en C63/C65 als stopgevallen. Maak expliciet: **“Een apart toelichtingsvoorstel behoort tot de afzonderlijk gevraagde H-taak, niet tot G's één-zin-uitvoer. Menselijke toestemming voor een betekeniswijziging maakt die wijziging niet tot betekenisbehoudend herstel.”** De algemene normgrondvoorwaarde is geen afhankelijkheid van een INT-10-wijziging.

### SC-11 → S §8: effectevaluatie → weglating

**Materieel. Bron:** A2:189–193, VA RB-A-24; B3:265–277. De toegevoegde H-effectvergelijking uit beide adviezen is verdwenen. Ook routeacceptatie voor transport/snapshot en registratie van de bestaande buurconfiguratie zijn niet concreet meegenomen.

**Voeg aan §8 toe:** **“H wordt vóór en na herstel afzonderlijk beoordeeld op betekenisbehoud, bronsteun en terecht stoppen: C02/C12/C14/C31/C32/C33 en C63/C64/C65. Bewaar de eerste kandidaat, diagnose, voorstel en verschil; één groene regel is geen herstelbewijs. Voor invoer/transport/snapshot worden C56/C61/C67 per relevante ingang uitgevoerd, met teruglezen van opslag en controle van UI/export en gewijzigde bron-/normbinding. Houd bij de INT-02-vergelijking buurconfiguratie constant en rapporteer buurafkeur apart. INT-10 blijft geparkeerd; geen eis of interventie om dat eerst te wijzigen.”**

Noem per latere uitvoering de nog toe te wijzen eigenaar en autorisatie, zoals B3/V09 doet. De set voor referentieontwerp is geen onafhankelijke hold-out. Dit is een ontbrekend evaluatieontwerp, geen reden nu model-, herstel- of routeproeven uit te voeren.

### SC-12 → S:59,107; D-K2b: onderzoekersstandpunten en signaalkeuze → onjuiste weergave

**Materieel. Bron:** B3:169 en VB RA-B-17; A2:125,207; VA RB-A-19 en Open punten; CO:42. B kiest S1 als voorkeur ter besluitvorming, niet als reeds besloten beleid. B verwerpt uitdrukkelijk dat overlap met ARAI-04 een principieel verbod op “moet” als leeshulp is. A laat behouden/uitbreiden/vervangen open; de coördinator stelde vervangen voor. “A én B kiezen S1 zonder moet; alleen markerselectie open” is dus geen getrouwe verwerking.

**Vervang S:59 en de K2b-rij:** **“Signaalbeleid blijft onderdeel van K2: S0 behoudt de bestaande vindhulp met beoordeling van de gehele kern; S1 voegt beperkte zinsdeelmarkers toe; vervangen van de bestaande signalen is het coördinatoralternatief. B heeft voorkeur voor S1 met citaat/positie; A ondersteunt beperkte uitbreiding als richting maar laat de keuze open. Geen signaal geeft zelfstandig VN en geen ontbrekend signaal geeft V. Overlap met ARAI-04 sluit een eigen INT-02-leeshulp niet principieel uit. Chris kiest het signaalbeleid en vervolgens de concrete selectie; bruikbaarheid is nog niet gemeten.”**

S:107: **“Geen inhoudelijk verbod van B op signaaluitbreiding; B heeft dit in v3 als expliciete S1-voorkeur uitgewerkt. Verschil behouden/uitbreiden/vervangen en markerselectie blijven K2b.”** C83 bevat “naar eigen inzicht”, maar C13 bevat niet de twee genoemde S1-voorbeeldmarkers; uitbreiding daarmee bewijst dus geen treffer op C13. C59 bevat die markers evenmin: een aanvullende beschrijvende bevoegdheidspassage mét dezelfde gekozen marker moet het vals-alarmrisico toetsen. Geen claim dat die markerproef al is uitgevoerd.

### SC-13 → S:50; D:34–40: gate, bestaand beleid en nieuw besluit → tegenspraak

**Materieel. Bron:** A2:101,155,204–218; B3:163,175, V10; VB RA-B-25; besluit 15 september:27. K4 staat terecht open, maar O2 krijgt in S:50 alvast “geen gate”. D:40 benoemt O1 en UI-zichtbaarheid als geen keuze, ondanks K2. Een product-/uitvoeringsbesluit is bovendien niet hetzelfde als een nieuw normbesluit.

**Correctie S:50:** vervang “geen gate” door **“poortbeleid volgt het afzonderlijke K4-besluit; deze evaluatoroptie introduceert geen verplichte gate”**.

**Vervang D:40:** **“Bestaand beleid: context verplicht vóór G en T (K-9), geen totaalscore, toetsen wijzigt geen tekst. Dit onderzoek stelt uitvoering daarvan en expliciete NE-afhandeling bij ontbrekende kern/context voor. K1 is de open normkeuze. K2/K2b betreffen beoordelings- en signaalhulp; K3 de samenhangende contractpublicatie; K4 het productbeleid voor vaststellen/export; K5 de afzonderlijke hersteluitvoering. O1 en zichtbare INT-02-passagehulp zijn gezamenlijke uitvoeringsvoorstellen, geen reeds genomen Chris-besluit of automatische nieuwe LLM-plicht.”**

Herstel van het ongegronde algemene voorwaardenverbod en metadata kan als broncorrectie worden beschreven, maar de precieze brede vervangnorm mag niet langs die weg als besloten gelden. “Restanten markeren” blijft, conform S:85, afzonderlijk onderhoud. K4 mag evenmin worden afgeleid uit het ontbreken van huidige gatecode of uit het verbod op totaalscores.

### SC-14 → S:76,108; D-K3: example_pair_reason → onjuiste weergave

**Materieel. Bron:** B3:231; VB RA-B-21/22; A2:124; VA RB-A-05. A heeft de tekst uit B's review overgenomen. B3 heeft daarna een expliciete variantgebonden reden toegevoegd. Dat is geen onoplosbaar normverschil, maar “tekst van B, geen keuze meer” verliest de latere precisering en verwart onderzoekersovereenstemming met K3.

**Gebruik voor de gezamenlijke exacte reden de actuele B3-tekst:** **“Het ASTRA-paar verschilt in het modale werkwoord moet. Dat raakt ARAI-04 en kan onder de bevestigde voorschriftlezing ook de lokale INT-02-functiegrens raken. Onder de enge discretionaire variant is zonder discretionaire grond geen INT-02-afkeur bewezen. Het paar blijft een reviewgeval; ASTRA noemt het weinig sprekend. Het woord bewijst op zichzelf geen actorfunctie, rolomkering of betekenisbehoud bij verwijdering.”**

Behoud review_policy en het letterlijke bronpaar. Vermeld in §9: **“Overeenstemming over behoud plus gecorrigeerde reden; de gezamenlijke tekst verwerkt B3's latere variant- en rolprecisering. Publicatie als onderdeel van K3 blijft voor Chris.”** Noch CO's rolomkering, noch de stellige lezing dat de organisatie noodzakelijk onderwerp is, wordt bronfeit.

### SC-15 → S:19,34, §12; D:42: route- en dossierdekking → weglating

**Materieel. Bron:** B3:148–163,270; A2:93–102; VA RB-A-16; VB RA-B-11/23. Het beperkte issues-kanaal is terecht genoemd; dit bewijst geen verlies in ieder contract. De verkorte keten laat bewerken, de optionele exportgate en het onderscheid tussen CON-02-expertbediening en een bewezen INT-02-reviewroute weg. De veertienonderdelentabel is een vindlijst, geen bewijs dat die ketenpunten integraal zijn verwerkt.

**Correctie:** wijs B3/F04 met alle acht ingangen en A2/§4 expliciet aan als **normatieve onderzoeksbijlage voor de routebevindingen en hun bewijsgrenzen**; neem compact op: **“Het resultaatcontract kan review_required transporteren, terwijl de genoemde issues-helper dat niet doet. Een gebonden INT-02-expertregistratie en volledige persistentie zijn niet bewezen. Bewerken en export hebben eigen routes; export kent een optionele async gate op uitgevoerde validatie/is_acceptable. De huidige gate leest geen zelfstandige INT-02-reviewlijst, maar andere blokkades kunnen vaststellen verhinderen.”**

D:42 mag implementatie-eigenaarschap bij DEF-626 laten, maar moet toevoegen: **“Betrouwbare versiegebonden doorgifte van INT-02-uitkomsten blijft uitvoeringsacceptatie; parkeren van de implementatie sluit de bewijsleemte niet.”** Vermeld ook dat definitie_origineel al opgeschoond kan zijn en dus geen bewijs van bewaarde ruwe modeluitvoer is. Geen route als werkend getest presenteren.

### SC-16 → D:11–13; S:15–17, §7; R:72,74–75: sterkte van waarnemingen → bewijsclaim te sterk

**Materieel. Bron:** A-P1 C03 en C12 hebben respectievelijk indien- en tenzij-signalen; B-P1 C51 heeft een tenzij-signaal. A2:190 en B3:140–142,261–263 begrenzen deze bewijsclaims. “Missen álle echte overtredingsvormen” is feitelijk onjuist. Signalen op toegestane criteria zijn bij neutrale vindhulp ook niet vanzelf foutpositieve afkeur. Geen menselijk aandachtseffect of generatorfout is gemeten.

**Vervang de signaalconclusie:** **“De bestaande signalen onderscheiden toegestane criteria niet van voorschriften/discretie: beide kunnen een treffer krijgen. Sommige onder de vastgelegde actorlezing overtredende voorbeelden blijven signaalloos, zoals C02/C13/C15/C52/C83. De evaluator geeft voor beide groepen uitsluitend RR; dit is geen gemeten semantische foutscore.”**

**Promptclaim:** **“De standaard geregistreerde module-uitvoer bevat tegenstrijdige instructies/voorbeelden over voorwaarden. Dat geeft risico op criteriumverlies; de volledige verzonden prompt, modelrespons en kwaliteitswinst zijn niet gemeten.”** **Cleaningclaim:** **“In twee B-P3-gevallen bleven indien, moet en de onderzochte criteria behouden; dit is geen algemene cleaninggarantie.”** D's UI-claim krijgt net als S het label codelezing. Zonder-contextgedrag is daarentegen wel direct op serviceniveau gemeten; “alle codelezing” is daarvoor te zwak.

### SC-17 → S:13,113,132; D:9; R:69–71: aantallen en exitstatus → bewijsclaim te sterk

**Materieel. Bron:** A-P1-uitkomsten bevat 25 records, B-P1 zeven, CO-C1 dertien. Hun ID-unie is 39, waarvan zes de bestaande C01–C06 zijn; 45 is het aantal servicewaarnemingen. A-P3 voegt twee waarnemingen toe, geen nieuwe casus-ID's. A2:14/198–200 rapporteert afgeleide exitstatus. CO-C1-uitkomsten bevat 13 matches en geen fouten, maar geen machinevastgelegde procesexit; script:155 return 0 bewijst geen waargenomen processtatus. De opgeleverde stukken onderbouwen S:113 “coördinator machinaal” niet.

**Vervang tellingen door:** **“A-P1, B-P1 en CO-C1 bevatten samen 45 servicewaarnemingen over 39 unieke casus-ID's, inclusief zes historische ID's; dus 33 nieuwe ID's binnen deze drie sets. A-P3 bevat twee aanvullende servicewaarnemingen van C04/C05. Het totale ontwerpregister omvat 57 ID's, niet alle uitgevoerd.”**

**Exittekst:** **“B's procesexit is machinevastgelegd. A rapporteert/leidt exit 0 af uit tooluitvoer. CO-C1 toont een voltooid resultaatbestand met 13 matches en geen geregistreerde casusfouten; een onafhankelijk vastgelegde procesexit is in de aangeleverde bijlagen niet aangetoond.”** Als de coördinator een bestaand executionrecord heeft, kan een exacte verwijzing dit laatste punt oplossen; geen herhaling nodig. Behoud de smalle historische hergebruikgrens en de beperking van voorafhash/tijdsbewijs; eindhashes bewijzen geen volgorde vóór de run.

### SC-18 → S:16,20,63,65; D:15,42: INT-10 en latente herstelketen → onjuiste weergave

**Materieel voor de scopezin; overige parkeerstatus juist. Bron:** B3:53,192,219; A2:83,164,218; VB RA-B-07/08/14/24. S citeert nog “Codex: G verbiedt vorm, T signaleert alleen” zonder de beperking tot de INT-02-evaluator, terwijl B3 dit heeft gecorrigeerd. De parkeerstatus is verder juist: geen INT-10-besluit en geen wijzigingsvoorwaarde.

**Correctie S:16:** **“De INT-02-generatie-instructie verbiedt de vorm; de INT-02-evaluator zelf geeft alleen open review. De service kan daarnaast buurafkeur geven, zoals A-P3 voor INT-01/INT-10 toont. Dat beslist de normjuistheid van die buurafkeur niet.”**

S:63: vervang de onvoorwaardelijke diagnose “foutpositieve buurregel” door **“mogelijk onjuist of anders gemotiveerd buurresultaat; INT-02-V bewijst geen buurregelfout”**. S:65 benoemt **latent** risico: enhancement vereist zowel enable_enhancement als een service; de container levert None. Er is geen uitgevoerd herstel of daaruit voortgekomen betekenisverlies aangetoond. Het algemene verbod op herstel zonder normgrond blijft gelden, zonder afhankelijkheid van INT-10-werk.

### SC-19 → S §9, §13 en bronannotaties → onjuiste weergave

**Redactioneel, behoudens de materiële standpuntcorrecties SC-12/14/18. Bron:** A2:30,32,45; VA RB-A-02/05/20; CO:9,15; VB RA-B-02/22. De kolom “A: ja” bij universeel determinisme maakt een bestreden formulering ten onrechte tot een bewuste eindpositie. CO stelde dit expliciet; A verduidelijkt dat “vaststaan” niet als universele determinisme-eis was bedoeld. Rolomkering betrof CO; A had deze ook al onvoldoende bewezen genoemd. Bij C10/C11 gaat het niet om hetzelfde toegevoegde domein als bij C04/C05, maar om de richting van de voorwaarde; C17/C18 voegt bovendien een verenigingsjaar toe.

**Correctie §9:** **“CO expliciet; A-v1 ambigu, A-v2 verduidelijkt; gezamenlijke tekst stelt geen universele determinisme-eis.”** En: **“CO's rolomkering door A en B niet bewezen geacht; B3 verwerpt ook de stellige onderwerpclaim. C04/C05, C10/C11 en C17/C18 verschillen of zijn niet equivalent bewezen om de afzonderlijk genoemde logische redenen.”**

S:26 verwijst naar de actuele N-A2 en N-B1, niet N-A1. S:9/30: ASTRA **vraagt of** de categorieverhouding voldoende omlijnd is; zij constateert daar niet letterlijk dat dit niet zo is. S:132 vervangt “alle verwerkt” door **“beide verwerkingen ontvangen; deze synthesecontrole identificeert nog te herstellen samenvoegingsverliezen”** en schrapt ongefundeerde afgeronde aantallen “materiële correcties”.

### SC-20 → R kolommen Onderscheidt/Herkomst; S:117 → onjuiste weergave

**Materieel voor besluitkoppeling; redactioneel voor gevalfamilies. Bron:** A2:204–218; B3/V10, VB RA-B-25. Het register gebruikt nog oude A-besluitnummers als K-nummers: K-2 voor lidmaatschap, K-4 voor evaluator, K-6 voor rechtsgevolg, K-7 voor INT-10 en K-8 voor leegte. Dit strookt niet met de beloofde gezamenlijke K1–K5-nummering.

**Correctie:** criteria/lidmaatschap/rechtsgevolg → **K1**; evaluator → **K2**, signalen → **K2b**; bronpaar/contract → **K3**; alleen poortbeleid → **K4**; herstel → **K5**. INT-10 → **“geparkeerde waarneming”**. Leegte → **“uitvoeringsacceptatie”**; K-9 blijft herkenbaar het bestaande **ESS-05-K-9**, geen zesde INT-02-keuze. Pas dit per rij toe, niet met een blinde nummervervanging.

Behoud in de besluitnotitie de expliciete concordantie: **K1 ↔ A B-1/B-2/B-3/B-6; K2/K2b ↔ B-4 en uitvoeringsaspect B-9; K3 ↔ B-5; K4 = toegevoegde poortkeuze; K5 ↔ A §5.4; B-7 geparkeerd, B-8 lege-kernuitvoering.**

De gelijktekens tussen C10/C80, C11/C81/C50 en C12/C82 duiden niet zonder meer bytegelijke input/context aan. Gebruik **“zelfde gevalfamilie; exacte proefinvoer in eigen bewijsbestand”** en laat de eigen ID's staan. Bij C27: “synthetische concretisering van ASTRA's leeftijdvoorbeeld”, niet een letterlijk broncitaat.

### SC-21 → S §6: gerichte skillduiding bij score/runtime → weglating

**Materieel als contractdekking. Bron:** B3:242–246; A2:181–185; RB/VA RB-A-19. S noemt het nieuwe contract, maar de gerichte duiding bij bestaande skillclaims over een voorlopig ontbrekend totaalcijfer en losse Python-validators ontbreekt. Dat laat de voorgestelde INT-02-instructie botsen met de algemene tekst in dezelfde skill.

**Aanvullende vervangtabelrij, zoals B3/V08:** **“INT-02 levert geen kwaliteitscijfer; de huidige appuitkomst is een open beoordeling. De totaalscore is bij besluit van 15 september 2026 definitief vervallen als kwaliteitscijfer, acceptatiegrond en hersteldriver. Het actieve JSON-runtimecontract bepaalt de evaluator; de losse INT02Validator is geen bewijs van de actieve uitvoering.”** Algemene skillsanering blijft bij de bestaande eigenaar; dit onderzoek geeft alleen de gerichte duiding, geen bulkherziening of implementatieopdracht.

## Dekkingscontrole en afronding

De veertien dossieronderdelen zijn inhoudelijk nagelopen: doel/norm/toepasselijkheid via SC-01–04; context, bronnen, ontologie en aanvullende informatie via SC-05/08/09; appketen en status/score/poort via SC-09/13/15/18; skills/prompts via SC-02/06/07/14/21; proeven via SC-16/17; samenhang via SC-01/18; reviewverwerking via SC-12/14/19; acceptatie/overdracht via SC-06/10/11/20. Daarmee is “dekking” niet gelijkgesteld aan geleverd runtime- of effectbewijs.

- **Materieel voor v2:** SC-02 t/m SC-18, SC-20 voor de besluitkoppelingen, SC-21. De kernclusters zijn: actuele casussen en variantpremissen; constitutieve uitzondering en G/T/H-bescherming; open signaal-/poortkeuzes; bronbinding; bewijs- en tellingcorrecties. Meerdere SC-punten kunnen in één gerichte tekstcorrectie worden afgehandeld.
- **Redactioneel:** SC-19 en de gevalfamilie-/bronlabelcorrecties binnen SC-20. SC-01 bevestigt de reeds juiste hoofdlijn.
- **Keuzes van Chris:** K1 breed/eng; K2 O1 nu tegenover apart te kiezen O2; K2b signaalbeleid/selectie; K3 één versiegebonden contract met bronpaarreden; K4 zelfstandige vaststel-/exportpoort; K5 afzonderlijke begrensde hersteluitvoering. Onderzoekersvoorkeuren sluiten deze keuzes niet. Geen INT-10-keuze in dit dossier.

**Eindoordeel:** beide onafhankelijke onderzoeken, beide reviews en beide verwerkingen zijn aanwezig; deze bijdrage voltooit B's eerste synthesecontrole. De huidige gezamenlijke v1 kan niet als afgerond gelden door de materiële samenvoegingsverliezen. Na traceerbare verwerking van de materiële punten in synthese, besluitnotitie én register kan het gezamenlijke onderzoek inhoudelijk worden afgerond, met open beleidskeuzes en expliciete bewijsleemten. Nog nodig is die verwerking door de coördinator en uitsluitend een gerichte controle van de materieel gewijzigde passages; geen tweede volledige review of nieuw onafhankelijk onderzoek. Ontbrekend app-/model-/UI-/herstelbewijs blijft een grens van dit onderzoek en wordt niet stil alsnog verplicht gesteld of als geleverd geboekt.
