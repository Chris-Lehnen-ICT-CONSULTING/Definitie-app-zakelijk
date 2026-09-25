# INT-02 — zelfstandig onderzoek C — v1

25 september 2026 · DEF-771 · fase: onafhankelijke eerste versie · onderzoeker C, Codex-app, sessie `01a0d7b1-e2da-7973-b542-44b023339e89`.

**Advies:** herstel de aansluiting op ASTRA: voorwaardelijke zinsvormen zijn geen verbod op zichzelf; deterministische afleiding en noodzakelijke begripscriteria blijven mogelijk. Beoordeel de functie van de definitie: beschrijft zij een begrip of geeft zij een actor een handelingsopdracht? Behoud voorlopig `judgment_review`, met specifieke passagehulp en een zichtbaar onderbouwd oordeel in de integrale expertbeoordeling. Een eigen AI-beoordelaar is een afzonderlijk productalternatief, geen noodzakelijke uitkomst van dit onderzoek. De precieze verbreding van discretionaire beslisregel naar ieder handelingsvoorschrift blijft Chris' normkeuze.

Dit is een voorstel, geen vastgesteld beleid of implementatie. Mijn v1 is gevormd zonder nieuwe bijdragen uit `a-claude-cli/`, `a-cowork/`, `b-codex-cli/` of de verboden gedeelde conclusie-/reviewbestanden te lezen. De toegestane historische INT-01-synthese is uitsluitend buurregelbron. Ik heb geen agents, andere sessies, issues, PR's of automatisering gestart. Alleen `c-codex-app/` is door mij beschreven; handovers en overige repositorybestanden zijn niet gewijzigd.

## Basis, toegang en bewijsstatus

De volledige `gedeeld/startopdracht-c-v1.md`, `feitenbasis-v1.md`, meegeleverde skill en beide vereiste referenties zijn gelezen. De actuele branch heet `onderzoek/DEF-772-INT-03-20260925`, niet `main`; HEAD is wel exact de opgegeven `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`. Geen branchwissel nodig of uitgevoerd. Eigen sessiemetadata bevestigt **gpt-6-astra / high**, runtime `0.155.0-alpha.16`; dit is geen afleiding uit een standaardconfiguratie. Python tijdens de proeven: **3.13.15**.

Van 57 expliciet gecontroleerde bronpaden zijn 56 leesbaar. Het opgegeven `src/services/definition/cleaning_service.py` bestaat niet. De werkelijke bron is `src/services/cleaning_service.py`, bereikbaar en gelezen. Dit is de enige ontbrekende opgegeven lokale bron in de inventaris. DBT §4.2 is niet als brontekst aangeleverd/gelezen; er is geen directe verificatie van Ross' tekst. Geen Linear- of webactualisering uitgevoerd: de opdracht levert besluiten en ASTRA-bronteksten als vaste onderzoeksbasis. De Ppw- en stelselmatige-daderteksten worden als ASTRA-illustraties onderzocht, niet als actuele juridische norm. De ASTRA-revisie van de op 25 september opgehaalde raw-bestanden is onbekend. Het historische bronrapport van 7 september noemt wel oldid 8695; gelijkheid met de raw-snapshot van 25 september is niet bewezen. [B01–B04]

**Historisch bewijs hergebruikt, niet opnieuw als vers gepresenteerd:** de zes gevallen met manager en cache op `d68a98a9`. Het INT-02-record is bytegelijk aan die commit en inhoudelijk gelijk aan het opgeslagen record, SHA-256 `f4149faae49ccb932b4907fde1c50b5c6503c164d100ce6d08de3e816119a5a2`. Het gehele evaluatorbestand is niet bytegelijk: ESS-01/02/04 kregen aparte takken. `_signalen` is AST-gelijk; INT-02 blijft door de ongewijzigde standaardreden en return lopen. Daardoor blijft het historische regelbewijs bruikbaar binnen zijn oorspronkelijke claimbereik. Voor de actuele servicegrens zijn twee nieuwe gevallen uitgevoerd. [P0, P1, P3]

Bronregister met paden en hashes: [bewijs/bronnen-en-toegang-v1.json](bewijs/bronnen-en-toegang-v1.json). Proefopzet is vóór uitvoering opgeslagen; invoer, grond, script, uitkomsten en exitstatus staan in `bewijs/`. Zes gerichte offline proeven voltooiden; één poging om `cache/` buiten mijn map aan te maken is door de eigen schrijfbeveiliging geblokkeerd, zonder omzeiling. Geen productiegegevens of live modelcalls. Grenzen per proef: [uitvoering-en-grenzen-v1.md](bewijs/uitvoering-en-grenzen-v1.md).

## Q1 — oorspronkelijke norm, lokale toevoegingen en toepasselijkheid

### Bronfeit en interpretatie uit elkaar

**F1 (ASTRA):** de regel luidt: “Een definitie mag niet geformuleerd worden als een beslisregel.” De toelichting koppelt beslisregels aan oordeelsvorming/discretie; een afleidingsregel is een geheel deterministisch algoritme dat een afgeleid feit oplevert. ASTRA staat afleiding uitdrukkelijk toe en verlangt die voor afleidbare begrippen. De gekoppelde afleidingspagina onderscheidt feiten anders voorstellen van oorspronkelijke feiten creëren. De beslisregelpagina illustreert discretionaire evenredigheidsafweging met de Ppw. [B02, velden Regel, Toelichting, Definitie, Voorbeeld]

**F2 (ASTRA):** aanbevolen, prioriteit midden, geldigheid alle, status definitief, type gehele definitie, herkomst DBT 4.2. Het voorbeeldpaar transitie-eis verschilt alleen in `moet`: verplichtend ondersteunen versus ondersteunen. ASTRA's redactie noemt zowel de business-rule-koppeling als het voorbeeld discussiepunten. Een definitief gepubliceerde regel betekent dus niet dat alle theoretische grenzen helder zijn. De verwijzingen naar Ross en DEMO zijn gelezen als ASTRA-tekst, niet onafhankelijk geverifieerd in die werken. [B02]

**F3 (lokaal):** `INT-02.json:4–6` voegt “of voorwaarden” toe, verbiedt geldigheidsvoorwaarden en voorwaardelijke/normatieve formuleringen, en vraagt daarop te toetsen. Zeven patronen zoeken `indien`, `mits`, `alleen als`, `tenzij`, `voor zover`, `op voorwaarde dat`, `in geval dat`. Type is “interne structuur”; brondocument alleen “ASTRA”. Deze toevoegingen zijn geen letterlijke weergave van ASTRA. De huidige evaluator gebruikt ze gelukkig als signalen, niet als afkeurbewijs. De generatie-instructie en skills presenteren ze wel als vermijdingsregel. [B05, B06, B07; P1/P2]

**I1 (interpretatie):** drie functies moeten worden onderscheiden, niet twee woordenlijsten:

1. Een criterium bepaalt het bedoelde begripslidmaatschap, eventueel met noodzakelijke of voldoende voorwaarden.
2. Een afleiding berekent uit gegeven feiten een afgeleid feit. Zij is geen opdracht die zelf een besluit of handeling tot stand brengt.
3. Een handelingsregel schrijft voor wat een actor moet doen; een discretionaire beslisregel is daarvan een duidelijk geval.

Een deterministische procedure kan nog steeds een handeling voorschrijven. “Alle beslissingen zonder discretie zijn toegestaan” volgt dus niet zonder meer uit de afleidingstoelichting. Omgekeerd maakt menselijke bewijswaardering bij een criterium dat criterium niet vanzelf tot een discretionaire opdracht. Ontbrekend bewijs bij een individueel geval betekent niet dat de definitie een beslisregel is. Deze laatste grens voorkomt strijd met ESS-04's kwalitatieve criteria. [B02; B09; C102/C107]

**I2 (lidmaatschap):** noodzakelijke criteria vallen niet onder een algemeen INT-02-verbod. Dat wordt gesteund door de uitdrukkelijke afleidingsuitzondering en de ASTRA-koppeling aan definitional criteria; die theoretische koppeling is redactioneel nog bevraagd. Daarom stel ik de expliciete toelating als lokale operationalisering voor, met registratie onder DEF-625. Een brongebonden kenmerk mag in een conditionele bijzin staan. `indien P, dan Q`, `Q alleen als P` en `Q dan en slechts dan als P` zijn niet zonder meer uitwisselbaar. Bescherm de logische richting. [B02, B08; C04/C05/C106/C115]

**I3 (rechtsgevolg):** het onderwerp kan een verplichting, bevoegdheid, procedure of rechtsgevolg zijn. Een beschrijving daarvan is geen opdracht tot uitvoering ervan. Een begripsomschrijving van “beslisregel” is dus ook niet automatisch uitgesloten. “Komt uit wet/beleid” of “wordt gebruikt om besluiten te nemen” is op zichzelf geen INT-02-afkeurgrond. Bronfunctie, actor, handeling en bedoelde betekenis zijn doorslaggevend. [B02, historisch dossier §3–7/13; C103/C112/C114]

### Exact normvoorstel INT02-C-N1

> **INT-02 — Geen beslisregel.** Een definitie beschrijft de afbakening van het bedoelde begrip en wordt niet als handelingsvoorschrift geformuleerd. Zij schrijft geen procedure, verplichting of discretionaire beslissing voor aan een actor. Een beschrijving van een verplichting, bevoegdheid, procedure of rechtsgevolg als begrip is daarmee niet verboden.
>
> Noodzakelijke begripscriteria en hun toepasselijke voorwaarden blijven behouden, ook in een voorwaardelijke zinsvorm. Een deterministische afleiding die uit gegeven feiten een afgeleid feit bepaalt is toegestaan; bij een afleidbaar begrip wordt die afleidingsrelatie in de definitie uitgedrukt. Een gebonden handelingsopdracht is niet enkel door haar determinisme een afleidingsregel.
>
> Beoordeel de functie op basis van de definitiekern, bedoelde betekenis, context en benodigde bronpassages. Woorden als ‘indien’, ‘mits’, ‘tenzij’ en ‘moet’, de herkomst uit regelgeving en gebruik bij een besluit bewijzen op zichzelf geen overtreding. Menselijke beoordeling van een kwalitatief kenmerk is evenmin op zichzelf een beslisregel. Bij ontbrekende of strijdige beslisgrond blijft het oordeel open; verwijder geen noodzakelijk criterium om een signaal te laten verdwijnen.

Dit is de **brede functievariant**. De eerste alinea operationaliseert het achtergrondbegrip behavioral rule en het ASTRA-voorbeeld; zij is niet als letterlijk ASTRA-citaat te publiceren. Alternatief **N0**: uitsluitend discretionaire beslisregels verbieden. N0 is nauwer verbonden met de gekoppelde definitie “algoritme waarvoor oordeelsvorming nodig is”, maar vangt C102/C105 niet en verklaart het `moet`-voorbeeld minder goed. Handhaaf dit verschil als keuze K1, niet als opgelost bronfeit.

Toepassing: iedere definitiekern, ongeacht gegenereerd/aangeleverd/geïmporteerd. Ondersteunende toelichting wordt niet stil een extra toetsobject; bij promotie naar definitiekern geldt dezelfde norm. Geen algemene uitzondering voor rechtsbegrippen, UFO-categorie of gezaghebbende bron. Deterministische afleiding is toegestane normvorm, niet “niet van toepassing”. Bij lege kern: niet uitgevoerd, geen inhoudelijk oordeel. [N1-voorstel; B02/B10]

Voorgestelde metadata: naam, prioriteit midden, aanbevolen, geldigheid alle behouden; type naar “gehele definitie”; brondocument “ASTRA; aldaar verwijzing naar DBT §4.2” met afzonderlijke normprovenance en lokale uitwerking. Wijzig ASTRA-citaten niet. Behoud het transitie-eispaar als bronvoorbeeld met `review_policy` en expliciete ARAI-04-overlap; voeg functionele afleidings-/voorschriftgevallen toe aan acceptatie, niet stil als vervanging van de bron.

## Q2 — benodigde invoer en veldrollen

**Vereist voor de app:** definitiekern als toetsobject, term/betekenisidentiteit en context volgens het appbrede K-9-besluit. Een contextloze directe serviceproef toont huidig gedrag, geen toestemming om K-9 te negeren. **Conditioneel vereist voor het semantische oordeel:** bronpassage en bedoelde functie wanneer de tekst alleen classificatie en voorschrift niet onderscheidt. Niet voor elk simpel wiskundig criterium een juridische bron verlangen; niet bij een intrinsiek duidelijk voorschrift ontbrekende bronnen gebruiken om VN te ontwijken. [B05, B10; P3]

Een herleidbare gebruikersbevestiging kan bedoeling vastleggen, maar vervangt geen actuele rechtsbron. Bij conflict tussen bedoeling en bron geen willekeurige veldvoorrang. Bij reeds aangetoonde overtreding: VN plus resterende open punten; anders O plus één gerichte vraag. Regelbron (ASTRA/record) en definitiebron (bijvoorbeeld aangeleverde regeling) blijven afzonderlijk. [B11; voorstel T]

| Veld | Zelf toetsobject/criterium | Bewijsfunctie | Invoer G | Mag AI opleveren/wijzigen? | Herkomst, ontbreken en conflict |
|---|---|---|---|---|---|
| Definitiezin | Ja: begripsbeschrijving versus voorschrift volgens N1 | Citaat toont functie/afleiding; niet eigen bronbewijs | Verplicht bij herschrijven, uitvoer bij nieuwe generatie | Nieuwe kandidaat apart; aangeleverd origineel niet wijzigen bij T | Exacte tekstversie; leeg → NB; verschil vóór/na bewaren |
| Term en bedoelde betekenis | Geen tweede definitie; bepaalt toepassingsobject | Onderscheid bijvoorbeeld besluit, besluitvorming en beslisregel | Vereist als betekenisanker | Geen stille term- of betekeniswijziging | Gebruiker/bron; default/modelvoorstel geen bevestiging |
| Context | Geen tekstobject van INT-02 | Domein, actor, toepasselijkheid; contextlabel bewijst functie niet | Appbreed verplicht K-9 | Niet verzinnen of wijzigen om te slagen | Ontbreekt → app niet genereren/toetsen; conflict verduidelijken |
| Definitiebronnen | Geen zelfstandige INT-02-toets van gehele bron | Passages tonen voorschrift, afleiding, scope en modaliteit | Conditioneel nodig; aangeleverde passages ongewijzigd | Geen bronpassage of verwijzing verzinnen; parafrase apart | Passage, locatie, versie en toepasselijkheid bewaren; gezag onder CON-02 |
| Ontologierelaties | Geen categorie-afkeur onder INT-02 | Is-een, kenmerk, actor-handeling, afgeleid-van ondersteunen | Ondersteunend | Alleen herkenbaar onbevestigd voorstel | Geen modelrelatie als onafhankelijke waarheid; ontbreekt ≠ automatisch fout |
| Voorbeelden | Niet stil meertoetsen als kern | Illustreren lidmaatschap bij criteria | Optioneel | Synthetisch en apart gelabeld toegestaan | Gegenereerd voorbeeld geen onafhankelijke normbevestiging |
| Praktijkvoorbeelden | Niet zelf kern | Tonen toepassing/functie in praktijk | Ondersteunend | Geen echte feiten/personen verzinnen; synthetische illustratie markeren | Geen gevalsbewijs ≠ definitieovertreding |
| Tegenvoorbeelden | Niet zelf kern | Onderscheid behouden bij herschrijven | Ondersteunend | Als synthetisch voorstel | Eén tegenvoorbeeld met bevestigd doel kan verlies tonen; label is geen bewijs |
| Grensgevallen | Niet zelf kern | Criterium versus opdracht; discretie versus kwalitatief oordeel | Ondersteunend | Apart voorstel | Onbesliste lezing zichtbaar houden; niet trainen op eigen gewenst oordeel |
| Synoniemen | Geen los modaliteitsverbod | Zelfde begrip anders verwoord kan opdracht verbergen | Optioneel | Voorstel met betekenisbehoud | Bevestigde synonymie nodig; geen termvervanging tijdens T |
| Homoniemen | Geen toetsobject | Onderscheiden normatief begrip van instructie/andere betekenis | Ondersteunend | Betekenisopties voorstellen, niet kiezen zonder grond | Context/bedoeling bepaalt lezing; onduidelijk → vraag |
| Toelichting/verduidelijking | Alleen bewijs, tenzij als kern opgeslagen | Bedoelde functie, logische richting, broninterpretatie | Ondersteunend, conditioneel noodzakelijk | Apart voorstel; geen essentieel kerncriterium hierin verstoppen | Auteur/herkomst vastleggen; tegenstrijdige uitleg herstelt onjuiste kern niet |
| Oordeel en versiegegevens | Geen begripsinhoud | Bewijst wie wat op welke basis heeft beoordeeld | Niet als opdracht om goedkeuring te produceren | Model geen actor, tijd of menselijk akkoord laten verzinnen | App registreert actor/tijd/tekst-, context-, bron-, norm- en promptbinding; wijziging maakt oud oordeel historisch |

## Q3 — samenhang, conflict en eigenaarschap

| Regel/eigenaar | Concrete relatie | Conflict of overlap; grens |
|---|---|---|
| ARAI-04 en ARAI-04SUB1 | Het ASTRA-paar verschilt alleen in `moet`; modale vormen/uitdrukkingen kunnen plicht maar ook beschrijving van vermogen/bevoegdheid dragen | Overlap, geen exclusief eigenaarschap: ARAI beoordeelt modaliteit; INT-02 tekstfunctie. Beide mogen zelfstandig motiveren (K-8). Geen automatische `moet`-verwijdering. Een INT-02-toelating wijzigt ARAI-norm niet. [B05/B08/B10] |
| ESS-04 | Begripscriteria moeten navolgbaar toepasbaar zijn; kwalitatief kan | Het lokale voorwaardenverbod kan noodzakelijke toetsbare grenzen aantasten. N1 lost die spanning op. Menselijke criteria zijn niet automatisch discretie. ESS-04 zegt rekenmethode naar toelichting; INT-02 vraagt constitutieve afleiding in kern. Onderscheid formule die het begrip definieert van procedure om bewijs te verzamelen. [B09; C107/C116] |
| ESS-05 | Kenmerken onderscheiden verwante begrippen | Voorwaarden schrappen kan het begrip verbreden. ESS-05 bezit de inhoudelijke onderscheidingsvraag; INT-02 de beschrijving/voorschriftfunctie. Context is appbreed verplicht door K-9; ESS-05-keuze voor AI is geen INT-02-besluit. [B10; C04/C110] |
| INT-01 | Dezelfde `indien`-patroonhit | Overlap in implementatie, ander normdoel. Een INT-02-goedgekeurde voorwaardelijke kern kan nog een INT-01-bevinding krijgen. Het 21-septembervoorstel om woordafkeur te schrappen is nog geen Chris-besluit. Geen H-opdracht tot criteriumverlies om deze buur groen te krijgen. [B12] |
| STR-06 / ESS-01 | Transitie-eis bevat doel/functie | Doel is niet hetzelfde als handelingsvoorschrift. ESS-01's besloten functiegrens blijft gelden; INT-02 beslist niet of elk doel essentieel is. STR-06 blijft eigen normdoel met expliciete samenhang. [B08/B09] |
| INT-08 / STR-07 | `tenzij`, negatie en negatieve criteria | Overlap in vorm; negatie kan afbakening dragen. INT-02-V betekent niet automatisch INT-08-V. Geen negatieve kernvoorwaarde wegschrijven. [B11; C113] |
| STR-08/09 | Noodzakelijke/voldoende voorwaarden, en/of | Logische richting en combinaties blijven behouden; patroonvervanging kan implicatie omkeren. Eigenaar van ondubbelzinnige combinatie, geen automatisch oordeel uit woordsoort. [B11; C106/C115] |
| ESS-02, CON-01/02 | Proces/resultaat/rol; context en brongetrouwheid | Een procesdefinitie kan beschrijven; een proceslabel bewijst geen voorschrift. Brongetrouw citeren kan toch INT-02-VN als definitie zijn. CON-01/02-blokkades niet via INT-02 opheffen. [B09/B10; C103/C114] |
| DEF-624/625/626/630/638/815 | Resultaat, herkomst, snapshots, poorten, repair, modelroute | INT-02 krijgt geen eigen totaalscore, bewaart open oordeel, geen stil nieuwe gate. Herstel en modelkeuze vragen eigen opdracht. [B01/B10/B13] |

## Q4 — aangetoond appgedrag per ingang

Bewijsniveaus: **code** = gerichte bronlezing; **functieproef** = echte functie zonder volledige app; **serviceproef** = echte ModularValidationService; **historisch** = opgeslagen eerdere uitkomst. Geen daarvan is een browser-/UI-doorloop of bewezen persistente keten.

| Ingang | Waargenomen gedrag en vindplaats | Bewijsgrens / ontbrekend |
|---|---|---|
| Genereren | Adapter `modular_prompt_adapter.py:70–130` registreert `JSONBasedRulesModule` met INT-prefix. P2 rendert daadwerkelijk uitleg + vermijdingsinstructie + optionele voorbeelden. Toetsvraag komt niet mee; toelichting met semantische nuance zou ook niet vanzelf als G komen. `IntegrityRulesModule` is alleen gedefinieerd/geëxporteerd, geen gevonden productie-instantiatie. | P2 voert formatter uit, niet hele orchestrator. Geen werkelijke modeluitvoer of generatiekwaliteitsbewijs. Alleen dode module aanpassen heeft op deze geregistreerde route geen effect. |
| Generatieopschoning | Orchestrator `definition_orchestrator_v2.py:1154–1168` gebruikt CleaningService. Service roept enhanced opschoning aan en bewaart metadata. P4 verwijdert label uit C100; afleiding en `indien` blijven; C03 blijft exact gelijk. | Twee teksten, geen universele garantie. `original_text` wordt al gestript; voor exact ruwe modeluitvoer afzonderlijk stadium bewaren. Metadata zoals “capitalized_first_letter” is geen onafhankelijke diffvaststelling. |
| Uitsluitend toetsen | Directe service met cleaning=None geeft C100/C104 RR met reden en indien-signaal, geen INT-02-violation, overall_score None. Evaluator P1 reageert niet inhoudelijk op meegegeven bedoeling. `required_inputs` alleen definition_text. | Geen werkelijke UI-/V2-ingang getest. P3 las runstatus per abuis onder `status`; null zegt niets over het echte `validation_status`-veld. Regelvelden zijn correct gemeten. |
| Optionele cleaning vóór servicebeoordeling | `modular_validation_service.py:878–910` gebruikt een optionele `clean_text(text)`. De concrete CleaningService vraagt ook `term`; foutpad valt terug op raw. | Latente signatuurkwestie uit INT-01 bevestigd als codeverschil, niet als actieve routebug geclaimd. Bij toetsen blijft ongewijzigde invoer het beleidscontract; DI-/adapterdoorloop ontbreekt. |
| Import CSV | `csv_importer.py:264–275` slaat op; auto_validate heeft alleen `pass`. | Codebewijs voor déze importroute; geen nieuwe DB-proef. |
| Import afzonderlijk | `definition_import_service.py:67–96,112` roept validator aan; import_single wacht tot 2 seconden op validate_single. | Corrigeert algemene uitspraak “import valideert niet”. Geen bereikbaarheid/UI-configuratie of INT-02-resultaatdoorgifte door deze route bewezen. |
| Bewerken | Historische INT-01-overdracht meldt validate_text zonder opschoning; huidige service kan ongewijzigde tekst beoordelen. | Editor-splitting, volledig contexttransport en binding van INT-02 op bewerkte versie niet vers functioneel bewezen. Niet als gerepareerd/gebroken bestempelen. |
| Opslaan/snapshot | `definition_repository.py:940` bewaart legacy score; `1030–1080` bevat bronbewijs/tekststadia en ESS-03-beoordeling. Dat bewijst geen versiegebonden INT-02-review. | Geen INT-02-snapshot heen-en-terug getest; onder DEF-626 vereist: tekst/context/bronnen/norm plus reden/signalen/oordeel en auteur/tijd. Geen totale afwezigheid van alle opslag claimen op basis van gerichte zoekactie. |
| UI/review | `validation_view.py:803–808` toont redenen alleen voor ESS-01/02/04. Detailpad `:834–867` gebruikt `_statuslijst_regels`; P5 levert uitsluitend “Nog te beoordelen: INT-02”. Geen reden/signaal of expander voor zo'n statusregel. Expert-tab gebruikt dezelfde renderer (`:1664–1675`). | Functieproef en code, geen schermtest. INT-02 bestaat in overzicht als code; niet beweren dat hij geheel onzichtbaar is. |
| Review na herladen | `expert_review_tab.py:_v2_uit_opgeslagen_validatie` bouwt violations uit legacy issues, geen rule_statuses/review_required; bij lege issues None. | Deze fallback reconstrueert geen open INT-02-oordeel. Geen bewijs dat elke andere actuele opslag-/herlaadroute dat verliest. |
| Vaststellen | `_evaluate_gate:715–833` leest score, context en issues, plus CON-01/02; geen INT-02-reviewcriterium. P6: met gecontroleerde overige voorwaarden geen verschil tussen wel/geen INT-02-RR; score None blokkeert. | Geïsoleerde functie, CON-01/02-hulp gestubd; geen bevoegdheids-/DB-/UI-doorloop. Afwezigheid van INT-02-gate betekent niet dat echte vaststelling lukt. Algemene scoregate blijft DEF-630. |
| Exporteren | `export_service.py:425–476` heeft optionele gate (constructor standaard uit), toetst opgeslagen/expliciet aangepaste tekst, vereist uitgevoerde run en is_acceptable. JSON bevat toetsresultaten (`:531`). | Geen daadwerkelijke TXT/CSV/JSON-export van INT-02-status/reden/binding aangetoond. Geen specifieke INT-02-blokkade in gelezen gate; huidige algemene gate mag niet als regelbesluit gelden. |

**Restanten:** `regels/INT-02.py` en `validators/INT_02.py` bevatten eigen voorbeeldsubstring- en patroonpass/fail-logica. `rg` vond INT02Validator alleen in deze definities/factories, niet in actieve consumers. Ze zijn geen bewijs van het huidige oordeelpad. Geen INT-02-vermelding in `additional_patterns.py`, `rule_reasoning_config.yaml` en `.claude/rules/patterns.md` gevonden. De completeness-enhancer heeft wel woorden `voorwaarde/vereiste/criteria`, maar die zijn generieke trefwoordhints, geen inhoudelijke INT-02-controle; geen actieve herstelroute daaruit afgeleid. [B06/B14]

## Q5 — concrete norm-, app-, prompt- en skillvoorstellen

### Strategie en resultaatcontract

| Optie | Gedrag | Voordeel | Risico/voorwaarde | C-advies |
|---|---|---|---|---|
| O1: judgment_review + specifieke passagehulp | Altijd RR tot menselijke inhoudelijke beoordeling; signalen wijzen passages aan; volledige kern beoordelen ook zonder hits | Kleinste inhoudelijk verantwoorde stap; sluit aan op huidige evaluator en ESS-04 | Meer bruikbare hulp is pas bewezen met echte reviewers; UI/opslag moeten oordeel en grond dragen | Voorkeur nu; geen nieuwe verplichte LLM-toets |
| O2: scoreloze AI-beoordeling | Op aangeleverd materiaal V/VN/O plus alleen indien gemotiveerd niet-van-toepassing; één vraag bij O; technische fout apart | Kan onderbouwde functiebeoordeling in app bieden naar ESS-03/ESS-05-K1 | Vraagt Chris-besluit, brontransport, citaatcontrole, versiebinding en effectproef. Zelfde fouten als model kan maken; geen model gekozen, DEF-815 | Reëel alternatief, niet stil verplicht stellen |
| O3: deterministische deelcontrole + review | Alleen zeker beslisbare invoer-/vormfeiten automatisch: ontbrekende kern/context, tekstwijziging, letterlijke passagepositie; semantiek blijft open | Reproduceerbare grensbewaking en bruikbare signalen | Een frase “wordt afgewezen indien” kan een klasse beschrijven; regex→VN of nul hits→V is niet verantwoord. Determinisme van getoetste afleiding ≠ determinisme van taalbeoordeling | Ondersteunende laag binnen O1/O2; geen generieke semantische regexpoort |

Voorgesteld contract O1: `judgment_review`, inhoudelijke beoordeling door mens, geen cijfer; bestaande `excluded_from_score` voorlopig behouden. Appbreed totaalscorebesluit wijzigt de enum niet automatisch. Voor O2 is `no_score` passend maar afzonderlijk te besluiten. Vereiste invoer definition_text/term/context_lists expliciteren; bronpassages conditioneel nodig, niet universeel verplicht. `review_policy` bij historisch voorbeeldpaar behouden.

De actuele enum heeft **zes** technische statussen: pass, fail, review_required, not_evaluated, error én not_applicable (`runtime_contract.py:174–197`). De feitenbasis somde slechts vijf op. Vier inhoudelijke AI-uitkomsten zijn geen opdracht om voor INT-02 een fictieve vrijstellingsklasse te maken. ASTRA geldt voor alle definities; afleiding is V, leegte NB. “Niet van toepassing” alleen bij aantoonbaar buiten scope getoetst object en expliciete motivering; reguliere INT-02-definities hebben geen vooraf vastgelegde NA-categorie.

Maak binnen `review_required` onderscheid tussen **review nog niet uitgevoerd** en **inhoudelijk onvoldoende informatie**. Alleen bij de tweede precies één gerichte vraag, bijvoorbeeld: “Beschrijft deze passage het bedoelde begrip, of schrijft zij voor wat de actor moet doen?” Geen verplichte vraag bij een al bewezen overtreding. Een technische fout blijft error, geen semantische onzekerheid. Een expliciete VN blijft bestaan als andere passages nog open zijn.

**Exacte meldingen (voorstel):**

- Nog niet beoordeeld: `INT-02 — Nog te beoordelen: beschrijft de definitie het begrip of schrijft zij een handeling of beslissing voor? Een voorwaardelijke zinsvorm is op zichzelf geen overtreding.`
- Passagehulp: `Te beoordelen passage: “{letterlijke passage}”. Onderzoek of dit een begripscriterium, afleiding of handelingsvoorschrift is. Dit signaal geeft nog geen inhoudelijk oordeel.`
- Geen treffer: `Geen signaalpassage gevonden. De inhoudelijke INT-02-beoordeling blijft nodig.`
- V: `INT-02 — Voldoet: de beoordeelde kern beschrijft het begrip of een toegestane afleiding. Grond: {passage en motivering}.`
- VN: `INT-02 — Voldoet niet: “{passage}” schrijft {handeling of discretionaire beslissing} voor, in plaats van het begrip af te bakenen. Grond: {bewijs}. De tekst is niet gewijzigd.`
- O: `INT-02 — Onvoldoende informatie om de functie van “{passage}” te bepalen. {één gerichte vraag}`
- NB: `INT-02 — Niet uitgevoerd: {definitietekst of verplichte context ontbreekt}. Er is geen inhoudelijk oordeel.`
- Error: `INT-02 — De controle kon technisch niet worden uitgevoerd. Er is geen inhoudelijk oordeel. {technische oorzaak zonder persoonsdata}`

Toon reden/passages ook voor INT-02 in de gewone weergave; regexstrings alleen diagnostisch. Sla een menselijk oordeel met actor/tijd en inhoudelijke grond op de exacte beoordeelde basis op, of meld eerlijk dat registratie nog niet beschikbaar is. Geen “beoordeeld” uit aanwezigheid van het reviewformulier afleiden. Voorstel: geen zelfstandige INT-02-vaststel-/exportblokkade en geen apart akkoord naast integrale expertbeoordeling; open/negatief blijft zichtbaar. Dit is een expliciete productkeuze (K4), niet afgeleid uit de huidige gaten in de gate. CON-01/02 en algemene voorwaarden blijven apart gelden.

### Exact G — generatie-instructie

> Beschrijf de afbakening van het bedoelde begrip. Formuleer geen opdracht aan een actor om een procedure, verplichting of discretionaire beslissing uit te voeren. Een beschrijving van zo'n zaak als begrip is wel mogelijk. Behoud onderbouwde begripscriteria, voorwaarden, negaties, tijdgrenzen en hun logische richting; woorden als ‘indien’, ‘mits’ en ‘tenzij’ zijn niet op zichzelf verboden. Druk bij een afleidbaar begrip de onderbouwde deterministische afleidingsrelatie uit. Verwar een gebonden handelingsopdracht niet met een afgeleid feit.
>
> Gebruik de aangeleverde betekenis, context en relevante bronpassages. Verzin geen criterium, discretie, bron, context of menselijke beoordeling. Houd procedurele achtergrond en toelichting apart, zonder een noodzakelijk criterium uit de kern te halen. Bij ontbrekende verplichte context genereert de app niet. Ontbreekt andere noodzakelijke betekenisgrond of spreken bronnen elkaar tegen, maak dit apart zichtbaar en stel één gerichte vraag; lever alleen een als voorlopig gemarkeerde kandidaat wanneer de beschikbare grond die draagt. Verander de term en registratiecontext niet en behoud inhoudelijk noodzakelijke namen. Een generatievoorstel is geen toetsuitkomst of vaststelling.

Vooraf door app controleren: term/context en beschikbare passageversies gaan werkelijk mee; onderscheid ruwe modeluitvoer, geëxtraheerde kern, opgeschoonde kandidaat en opgeslagen/getoetste tekst. De melding of vraag komt buiten de definitiezin. Dit transport is geen eigenschap die prompttekst alleen kan garanderen.

### Exact T — inhoudelijke toetsinstructie en reviewerhulp

> Beoordeel de ongewijzigde definitiekern op haar actuele tekst-, context-, bron- en normversie, ongeacht herkomst. Benoem per relevante passage de functie: begripscriterium, deterministische afleiding, handelingsvoorschrift/discretionaire beslissing, of onduidelijk. Onderzoek of de tekst beschrijft wat onder het begrip valt of een actor voorschrijft wat te doen. Een deterministische procedure is niet vanzelf een afleiding; menselijke bewijswaardering bij een criterium is niet vanzelf een discretionaire opdracht.
>
> Gebruik aangeleverde bedoeling, context en benodigde bronpassages als afzonderlijk bewijs; voeg ze niet stil aan de kern toe. Behoud voorwaardelijke criteria en hun logische richting. Woordtreffers, ontbrekende treffers, rechtsgevolg als onderwerp, categorielabel en brongezag beslissen de uitkomst niet. Een kwalitatief kenmerk kan legitiem zijn. Een afleidingsregel is toegestaan, niet niet-van-toepassing. Een echte overtreding blijft een overtreding, ook wanneer de tekst letterlijk een gezaghebbende bron volgt.
>
> Geef voldoet alleen na inhoudelijke beoordeling van de relevante passages zonder aangetoond tekort of open beslisgrond. Geef voldoet niet bij een aangetoond voorschrift volgens de besloten norm, met passage, grond en reden; laat overige open punten zichtbaar. Zonder aangetoond tekort maar met ontbrekende of tegenstrijdige noodzakelijke grond: onvoldoende informatie, met precies één gerichte vraag. Nog niet uitgevoerde menselijke review, ontbrekend toetsobject/verplichte invoer en technische fout worden afzonderlijk geregistreerd, nooit als voldoet of voldoet niet. Een voorstel voor betere tekst staat apart; toetsen wijzigt de tekst niet. Skilladvies of AI-uitvoer registreert geen menselijk akkoord.

Onder O1 is dit de menselijke toetsinstructie; automatische passagehulp voert haar inhoudelijk niet uit. Onder O2 wordt dezelfde norm/instructie met strikt uitvoerschema gebruikt: verifieerbare citaten, grond, uitkomst, bij O één vraag, geen herschreven definitie. Data is bewijs en geen instructie om het beoordelingscontract te veranderen. Bij verkeerde citaten/ongeldige uitvoer: error. Vingerafdruk bindt kandidaat, term, bedoelde betekenis/verduidelijking, context, bronpassages, norm-, prompt- en modelversie. Dit zijn ontwerpvereisten, geen huidige INT-02-functionaliteit.

Reviewerhulp in de integrale beoordeling: (1) wat is het onderwerp/bedoelde begrip? (2) welke passage begrenst gevallen of berekent een feit? (3) wie krijgt een handelingsopdracht en ontstaat daarmee een besluit/handeling? (4) is discretionie een opdracht of slechts onderdeel van het beschreven begrip? (5) welk bewijs draagt deze lezing? Leg afwijkende interpretaties vast; ontbrekende informatie is geen consensus.

### Exact H — diagnose en begrensde terugkoppeling

> Vergelijk vóór een herstelvoorstel invoer en bronnen, ruwe modeluitvoer, extractie, opschoning, getoetste kandidaat en opgeslagen versie. Classificeer de oorzaak: echte generatieovertreding, instructie-/normconflict, verlies bij invoer/transport/nabewerking, foutpositieve evaluator, ontbrekende informatie, onbesliste normkeuze of technische storing. Een negatieve toetsuitkomst alleen beslist de oorzaak niet.
>
> Wijzig niets bij uitsluitend toetsen. Bied alleen op verzoek en binnen afzonderlijk geactiveerd DEF-638-beleid maximaal één nieuwe kandidaat aan voor een aangetoonde herstelbare tekortkoming waarvoor de beschikbare betekenisgrond volstaat. Behoud term, recordidentiteit, registratiecontext, noodzakelijke namen, criteria, drempels, negaties, logische richting en bronbetekenis. Verplaats alleen aantoonbaar niet-begripsbepalende procedurele achtergrond naar een afzonderlijk toelichtingsvoorstel. Geen schrappen van ‘indien’, ‘tenzij’ of ‘moet’ als herstel op zichzelf; geen voorschrift ongemerkt tot feitelijke beschrijving maken.
>
> Bewaar origineel, voorstel, verschil, reden en gebruikte grond. Stop bij bronconflict, ontbrekende betekenisgrond, onbesliste norm, foutieve validator, technische storing, betekenisverlies, herhaalde fout of uitgeputte poging. Vraag benodigde informatie in plaats van die te verzinnen. Hertoets de nieuwe kandidaat en de geraakte buurregels; bij onbekende afhankelijkheden alle toepasselijke controles. Oude oordelen blijven historie en gelden niet als actuele goedkeuring. Toon succes als nieuwe conceptkandidaat met resterende bevindingen; bij open oordeel, storing of stop behoud het origineel en de reden. Geen totaalscore als trigger of succescriterium.

Concreet: C111 is een validatorprobleem, C109 transport/nabewerking, C108 ontbrekende conflictoplossing, C102 een normkeuze totdat K1 is besloten, C101 kan een generatorfout zijn als opdracht/invoer een beschrijving vroegen en de ruwe uitvoer de opdracht toevoegde. C02 kan instructieconflict of bedoeld normatief begrip zijn; zonder tekststadia/betekenis geen generatieschuld vaststellen. C110 is schadelijk herstel, ook als een andere toets daarna groener wordt. H is nu niet uitgevoerd of geactiveerd.

### Huidige passage → probleem → exacte vervanging → acceptatie

| Vindplaats en huidige inhoud | Probleem | Voorgestelde exacte tekst / plaats | Casus |
|---|---|---|---|
| `INT-02.json:4`: “Een definitie bevat geen beslisregels of voorwaarden.” | Breder dan ASTRA, bedreigt afleiding | Uitleg: `Een definitie beschrijft het begrip en bevat geen handelingsvoorschrift; begripscriteria en deterministische afleidingsrelaties blijven toegestaan.` Volledige N1 in toelichting met lokale provenance, na K1-besluit. | C04/C100/C102 |
| `INT-02.json:5`: voorwaarden geldig, indien/mits/tenzij naar regelgeving | Vorm wordt functieoordeel | Vervang toelichting door N1-alinea's 2–3 plus: `Dit is een lokale operationalisering van ASTRA; de grens met gebonden handelingsvoorschriften volgt besluit K1.` Na besluit vervangt concrete besluitreferentie deze ontwerpverwijzing. | C102/C107/C115 |
| `INT-02.json:6`: “Bevat ... geen voorwaardelijke of normatieve formuleringen ...?” | Stuurt reviewer naar breed vormverbod | `Beschrijft de definitie het bedoelde begrip of een toegestane afleiding, zonder een handelingsvoorschrift te geven, en welke passage en grond onderbouwen dit oordeel?` | C101/C103/C112 |
| `INT-02.json:7–15`: zeven regexen | Alleen aanwijzing, mist moet/woordloos voorschrift | Behoud desgewenst als signaalgegevens; UI toont echte passage plus vaste passagehulp hierboven, nooit verboden-label. Geen semantische regexafkeur toevoegen. | C02/C105/C111 |
| `json_based_rules_module.py:_get_instruction_for_rule`, INT-02: “Vermijd voorwaardelijke formuleringen ...” | Actieve G spreekt uitzonderingen tegen | Vervang volledige INT-02-instructiewaarde door **Exact G** hierboven; kortere tekst mag uitzonderingen en ontbrekende-grondbeleid niet verliezen. Record-uitleg moet gelijktijdig dezelfde norm dragen. | C100/C106/C108 |
| `judgment_review.py:evaluate`: alleen generieke toetsvraag; signalen als regexstrings | Geen functiehulp, nul hits oninformatief | Nieuwe INT-02-redentekst is exact melding “Nog niet beoordeeld”, gevolgd door passagehulp of “Geen treffer”; menselijke T blijft apart. | C02/C105 |
| `validation_view.py:803–808` en statuslijst; INT-02 alleen code | Reden niet aan gebruiker aangeboden in gelezen detailroute | Toon bovenstaande reden en letterlijke passage via tekstweergave; voeg geen ongefundeerd inhoudelijk verdict toe. | C100/C105 |
| Toetsregels-skill `reference.md:63`, INT-02-rij | Kopie van absolute G-voorkeur | `Beschrijf het begrip; geef geen handelingsvoorschrift. Behoud onderbouwde begripscriteria en deterministische afleidingen, ook in voorwaardelijke vorm. Woorden zijn signalen, geen oordeel; volg references/int02-beschrijving-en-voorschrift.md voor N/G/T/H.` | C04/C100/C102 |
| Nederlandse-definities `reference.md`, Verboden Patronen → Vermijden: “Voorwaardelijke formuleringen: indien, mits, tenzij, alleen als” | Zelfde skill vraagt noodzakelijke/voldoende voorwaarden, maar ontmoedigt vorm daarvan absoluut | `Voorwaardelijke zinsvormen zijn toegestaan wanneer zij onderbouwde begripscriteria of deterministische afleidingen uitdrukken. Vermijd handelingsvoorschriften; behoud noodzakelijke voorwaarden en hun logische richting. Zie references/int02-beschrijving-en-voorschrift.md.` | C106/C115 |
| Beide skill-SKILL.md's: nog geen INT-02-contractblok | Geen gedeelde G/T/H-grens | Toevoegen: `Gebruik voor INT-02 het versiegebonden N/G/T/H-contract references/int02-beschrijving-en-voorschrift.md. Dezelfde norm geldt voor gegenereerde en aangeleverde inhoud. Toets ongewijzigde tekst; een signaal is geen oordeel. De mens beoordeelt de functie binnen de integrale expertbeoordeling; het skilladvies registreert geen review of vaststelling. Herstel is uitsluitend een afzonderlijk voorstel binnen DEF-638.` | C111/C114/C118 |
| Nieuw contractbestand in beide skills | Ontbreekt | Inhoud = N1 + veldrollen + Exact G/T/H + meldingen + voorbeelden C100 (afleiding), C101 (discretie), C102 (gebonden voorschrift na K1), C107 (grens), C112 (normatief begrip). Canoniek bij toetsregels; versiegebonden identieke kopie bij definities zoals ESS-03. | Hele register |
| Toetsregels-SKILL.md:39 en :97: Pythonvalidator per regel, gewogen scoring / totaalscore tijdelijk | Algemene documentatiedrift | Gerichte vervanging van deze claims: `Het actuele runtimecontract bepaalt per regel evaluator, vereiste invoer en mogelijke uitkomsten. INT-02 vraagt voorlopig menselijke inhoudelijke beoordeling en levert geen cijfer. Er is appbreed geen totaalscore als kwaliteitscijfer, acceptatiegrond of hersteldriver; ontbrekende beoordeling is noch geslaagd noch inhoudelijk fout.` Overige regels niet ongemerkt opnieuw definiëren. | C06/C118 |

Dode IntegrityRulesModule en losse validators niet als primaire wijzigingsplek gebruiken. Eventuele archivering/opruiming vraagt afzonderlijke uitvoering; deze opdracht verwijdert niets. Geen generiek actualiseren van andere skills of buurregelnormen in dit onderzoek.

## Q6 — acceptatie, effectvergelijking, besluiten en overdracht

Alle **25 casussen** staan in [casusregister-c-v1.md](casusregister-c-v1.md), één tabel met G/T/H en bewijs. C01–C06 zijn de vaste historische IDs; C100–C118 nieuw. C04/C05 zijn geen perfecte equivalente formuleringen: “Getal” versus “Geheel getal” en de logische vorm verschillen. Daarom is C106 toegevoegd met expliciet bevestigd domein en equivalentie. C100 houdt de ASTRA-afleidingsfunctie vast maar is synthetisch geparafraseerd met lemmaherhaling; geen algehele definitiegoedkeuring.

### Beschikbare nulmeting

| Bewijs | Werkelijke uitkomst | Wat het bewijst |
|---|---|---|
| P0 historisch hergebruik | 12 uitkomsten, zes gevallen × manager/cache: RR; C03/C04 indien-signaal, overige zonder | Historisch routegedrag plus actuele broncontinuïteit van INT-02; geen inhoudelijke goldlabels |
| P1 nieuwe evaluatorproef | Zes C100–C105: allemaal RR, score null; C100/102/104 indien, C101 tenzij, C103/105 geen signaal | Huidige semantische neutraliteit en grenzen van signalering; geen pass/fail-kwaliteit |
| P2 formatter | Actieve INT-02-uitleg en vermijdingsinstructie, voorbeelden aan/uit; geen toetsvraag | Werkelijke lokale rendering; geen totale prompt-, tokenbudget- of modelkwaliteit |
| P3 service | C100 en C104 RR + indien, geen INT-02-violation; overall_score null | Actueel INT-02-resultaat ook zonder context; geen hele UI- of opslagroute |
| P4 cleaning | Label C100 verwijderd, criterium intact; C03 ongewijzigd | Behoud op deze twee inputs; geen algemene veilige-opschoningsgarantie |
| P5 UI-helper | Alleen open status met code INT-02 | Geïsoleerde statuslijst verliest tekstuele reden door ontwerp; gewone renderpad statisch onderzocht |
| P6 gatefunctie | Met gesimuleerde score .9 pass ongeacht INT-02-reviewitem; bij None blocked | Geen directe review-iteminvloed in deze gatefunctie; geen bewijs van werkelijk vaststelbare definitie |

**Niet uitgevoerd:** echte generatie, nieuwe semantische evaluator, herstel, gebruikersreview, editor-/import-/opslag-/export-doorloop. Geen nieuwe variant beschikbaar/geautoriseerd. Een lagere RR-telling is geen kwaliteitswinst; de huidige evaluator maakt juist geen automatische semantische afkeur. De beoogde winst is helderder instructie en betrouwbaarder inhoudelijk oordeel, niet willekeurig meer groene regels.

### Effectontwerp vóór uitvoering

| Aanbeveling | Te verbeteren / te behouden | Vergelijking vóór/na en acceptatie | Ontbrekend bewijs, eigenaar en moment |
|---|---|---|---|
| N/G en skillcorrectie | Minder verloren criteria/afleiding; voorschriften niet als kern produceren | Dezelfde bron-/contextinputs, oude versus nieuwe G; 12 doelgerichte scenario's uit register (C01/02/100/101/102/103/106/107/108/112/115/116), elk 3 echte runs per variant bij gelijk model/instellingen. Vier extra niet voor ontwerp gebruikte gevallen vooraf door expert vastleggen in vrije IDs. Geen percentageclaim op kleine set. Rapporteer eerste poging, onthouding en betekenisverlies apart. | Geen live calls nu; A draagt over, product-/materiedeskundige bevestigt referentie, uitvoerder/modelroute-eigenaar voert uit na autorisatie en K1/K2. Modelkeuze blijft DEF-815. |
| O1 passagehulp/UI | Reviewers herkennen functie en missen criteriumuitzonderingen minder; nul hits blijft beoordeelbaar | Twee materiedeskundigen beoordelen dezelfde geselecteerde gevallen geblindeerd met oude/nieuwe hulp in gevarieerde volgorde. Vaste referentie per geval, verschillen gemotiveerd adjudiceren. Meer terecht oordeel én minder betekenisverlies; geen winst uit overeenstemming alleen. Tijd registreren als waarneming, niet vooraf als besparing claimen. | Geen gebruikersproef nu. A moet deelnemers/eigenaar laten aanwijzen; na werkende UI-opslag en normbesluit. Zonder deze proef alleen technisch opgeleverd, geen gebruikerswinst. |
| Optioneel O2 | Juiste V/VN/O, geen ongefundeerde afkeur van afleiding of pass van voorschrift | Exactzelfde tekst/bewijsset als O1; vooraf labels en onbesliste labels bevriezen. Rapporteer juiste oordelen, foutpositieven, gemiste fouten, terecht open, foutieve citaten en technische fouten afzonderlijk. Referentie niet door nieuwe evaluator zelf laten vaststellen; 3 runs waar stochasticiteit relevant is. | Alleen na O2-keuze en transport-/bindingswerk. A/coördinator + aangestelde materiedeskundige; uitvoerder volgt gekozen modelroute. |
| Resultaat/opslag/export/gatecontract | Geen verloren redenen, geen stale goedkeuring, geen fictief pass | C104/C118 plus C100/RR en C101/VN door alle werkelijke ingangen; exacte tekst, norm en context teruglezen. Conceptopslag en adviesstatus zichtbaar; algemene poorten afzonderlijk testen. | Nu alleen beperkte routebewijzen. DEF-624/626/630-eigenaren na afzonderlijke opdracht, vóór technische oplevering. |
| H | Eén herstelbare fout herstellen zonder criteriumverlies; juiste stop | C109/110/111/114/117: echte ruwe tekststadia vergelijken, herstel uitsluitend met aanwezige grond. Elke betekeniswijziging of ongeautoriseerde tekstmutatie is regressie. Eerste poging en na-H afzonderlijk rapporteren; geen score als doel. | H niet geactiveerd; DEF-638-eigenaar na aparte activering, samen met bronexpert. Tot dan uitsluitend acceptatieontwerp. |

Voor elke vergelijking bron-, norm-, prompt-, model-, configuratie- en codeversies vastleggen; bronconflicten en onbesliste K1/K2-casussen vóór vergelijking oplossen of expliciet als onbeslist uitsluiten van juist/fout-telling. Uitkomsten per geval: verbeterd, gelijk, verslechterd, onbeslist met grond. Een inhoudelijk ernstige verslechtering (criteria verdwijnen, discretionie toegevoegd, passagebewijs verzonnen) blokkeert een positieve effectclaim. Bij geen verbetering aanbeveling heroverwegen. Geen experts opgevoerd alsof zij al deelnamen; A draagt de benoeming en uitvoering als open werkpunt over. Na implementatie zonder dit bewijs: **geïmplementeerd; kwaliteitswinst nog niet vastgesteld**.

### Concrete keuzes voor Chris

| Keuze | Mijn voorkeur | Alternatief en gevolg | Onderscheidende casussen |
|---|---|---|---|
| K1 — Normgrens | N1: beschrijving tegenover handelingsvoorschrift, inclusief gebonden procedure; lokale operationalisering expliciet | N0: alleen discretie verbieden; deterministisch voorschrift blijft buiten INT-02. Geen algemeen voorwaardenverbod behouden zonder expliciete afwijking van ASTRA. | C102/C105 versus C100 |
| K2 — Criteria en grensgevallen | Conditionele lidmaatschapscriteria/afleiding toestaan; kwalitatief criterium niet op menselijke beoordeling afkeuren; functie-onzekerheid O | Alle normatieve/kwalitatieve criteria als beslisregel behandelen veroorzaakt spanning met ESS-04/05; daarvoor ontbreekt hier overtuigende normgrond | C104/C107/C112/C115 |
| K3 — Evaluator | O1 met passagehulp, integrale menselijke beoordeling; deterministische grensbewaking ondersteunend | O2 naar ESS-03-patroon kan sneller inhoudelijk adviseren, maar vereist eigen besluit/uitvoering/effectbewijs. Geen modelkeuze hier. | C02/C100/C105/C117 |
| K4 — Uitkomst en poort | Scoreloos in gebruik, `excluded_from_score` voorlopig; geen zelfstandige INT-02-blokkade of extra akkoord; open/negatief zichtbaar en versiegebonden | Een verplichte INT-02-gate is nieuwe productkeuze en vraagt eerst betrouwbaar oordeel/resultaattransport; huidige gatelek is geen argument voor succes | C06/C118, P6 |
| K5 — Herstel | Geen automatische activatie; alleen op verzoek maximaal één voorstel na diagnose en met betekenisbehoud | Nu automatisch herschrijven op RR of trefwoord: afwijzen wegens ontbrekend foutbewijs en risico op criteriumverlies | C109/C110/C111/C114 |

ASTRA-uitzondering en geen-totaalscore zijn bestaande bron/besluitgrenzen; de exacte N1-operationalisering, O1/O2-keuze en poortcontract zijn voorstellen. K-9-contextplicht uit ESS-05 is appbreed vastgelegd en wordt hier niet opnieuw ter stemming gezet. Geen van deze voorstellen is uitgevoerd.

### Overdracht en dekkingscontrole

Mijn eerstvolgende bijdrage na expliciete overdracht is de volledige inhoudelijke kruisreview van A met claim/versie, oordeel, bron/tegenbewijs, gevolg en correctie. A moet daarvoor zijn volledige eigen onderzoek en relevante bijlagen aanwijzen, en vervolgens zijn review van deze v1 aanleveren. Ik verwerk die punten in een nieuwe versie met dispositie per punt, behoud deze v1 en voer daarna op verzoek één synthesecontrole uit op G/T-aansluiting, weglatingen, standpuntweergave en herstel zonder betekenisverlies. Geen stilzwijgende ontvangst of gezamenlijke afronding geclaimd.

| Dossieronderdelen | Vindplaats |
|---|---|
| 1 doel, 2 norm/besluiten, 3 toepasselijkheid | Q1, basis, K1/K2 |
| 4 context, 5 definitiebronnen, 6 ontologie, 7 aanvullingen | Q2-veldmatrix, Q3 |
| 8 appgedrag, 10 status/score/poorten, 11 proeven | Q4, Q5-strategie, Q6-nulmeting + bewijs |
| 9 skills/prompts, 13 verbeteringen/review | Q5 exact N/G/T/H, vervangingstabel; kruisreview/verwerking nog te ontvangen |
| 12 samenhang, 14 acceptatie/overdracht | Q3; register; Q6-effectontwerp, keuzes en volgende overdracht |

Procesgegevens: zes Q-vragen behandeld; zes historische gevallen/twaalf route-uitkomsten hergebruikt; zes nieuwe afgebakende proeven; vijf open productkeuzes; nul ontvangen nieuwe kruisreviews of verwerkingen; nul extra onderzoeksrondes zonder open vraag. Dit zijn activiteiten, geen efficiëntie- of kwaliteitspercentages.

## Bronnen en concrete beperkingen

Paden hieronder zijn relatief aan `/Users/chrislehnen/Projecten/Definitie-app`, tenzij een skillpad is genoemd. Volledige paden/hashes staan in het bronregister; codeclaims gelden voor HEAD hierboven. Broninventarisatie bewijst toegang, niet dat ieder groot bestand integraal inhoudelijk is beoordeeld; de hier aangehaalde passages zijn gericht gelezen.

- **B01:** `.../INT-02-verdieping/onderzoek-20260925/gedeeld/{startopdracht-c-v1.md,feitenbasis-v1.md}`. Procesopdracht en aangeleverde besluitfeiten; geen vervanging van codeproeven.
- **B02:** dezelfde gedeelde map, `bronnen/astra-{INT-02,Beslisregel,Afleidingsregel}-raw.wikitext`. Primaire aangeleverde normteksten; revisie op 25 september onbekend.
- **B03:** `INT-02-v1.md` en `INT-02-bewijs-v1/{gevallen,uitkomsten,claude-review}.json` onder `docs/analyses/def606-regeldossiers/`. Historische duiding/proeven; historische Claude-review is geen review van deze v1.
- **B04:** `docs/analyses/2026-09-07-DEF-625-astra-bronaanvulling-v2.md`, INT-02-rij en normsamenvatting; historische oldid 8695, DBT-verwijzing.
- **B05:** `src/toetsregels/regels/INT-02.json`, `runtime_contract.py`; root-SSOT `config/toetsregels/toetsregels_config.yaml` wordt door echt build_rule_record/MVS geladen. Geen norm uit regex afgeleid.
- **B06:** `judgment_review.py`, `modular_validation_service.py`, `types_internal.py`, `evaluators/base.py`, `additional_patterns.py`; bronplaats zoals Q4/P1/P3.
- **B07:** `json_based_rules_module.py:_format_rule/_get_instruction_for_rule`, `modular_prompt_adapter.py:70–130`, `integrity_rules_module.py`, modules-exports. Formatterproef P2.
- **B08:** `ARAI-04-v1.md`, `ESS-04-v1.md`, `ESS-05-v1.md`, `overzicht-v1.md`, `samenhang-v1.md`; alleen relevante norm-/relatiepassages, oude oordelen vervangen geen latere besluiten.
- **B09:** `/Users/chrislehnen/.agents/skills/definitie-toetsregels/references/{ess01-functiegrens,ess03-eenheid-identiteit,ess04-toetsbaarheid}.md`; actuele vastgelegde richting/contractvorm. Skills zijn implementatie/beleidsweergave, geen onafhankelijke ASTRA-normbron. ESS-03-appgedrag daarnaast uit `evaluators/countability_assessment.py`.
- **B10:** `ESS-05-verdieping/onderzoek-20260921/gedeeld/besluiten-v1.md`, in het bijzonder K1/K4/K7/K8/K9. Geen INT-02-keuze voor AI/gate daaruit overgenomen.
- **B11:** `docs/analyses/2026-09-11-DEF-606-productbedoeling-toetsregels-skills-v1.md` (bedoeling, tekstbehoud, bewijsgrenzen), `samenhang-v1.md` (voorwaarden/negatie).
- **B12:** `INT-01-v2.md`, `INT-01-verdieping/onderzoek-20260921/{besluitnotitie-chris-v1.md,gezamenlijke-synthese-v2.md}`. Historische buurregel; keuzes niet als besloten voorgesteld. Niet de nieuwe INT-02-conclusies van A/B.
- **B13:** `docs/analyses/2026-09-15-DEF-606-besluit-geen-totaalscore-v1.md`; code `definition_workflow_service.py:715–833`, `policies/approval_gate_policy.py`, `export_service.py:425–476`.
- **B14:** `cleaning_service.py`, `opschoning/{opschoning,opschoning_enhanced}.py`, `definition_orchestrator_v2.py:1154–1168`, import-/repository-/UI-bronnen in Q4; legacy INT-02-validators en completeness-enhancer als restanten/onderzoeksobject.
- **B15:** beide actuele skills `definitie-toetsregels/{SKILL.md,reference.md}` en `definitie-nederlandse-definities/{SKILL.md,reference.md}`; precieze vervangingsplaatsen Q5. Niet gewijzigd.
- **P0:** `bewijs/historisch-hergebruik-v1.json` + `historische-diff-v1.txt`; recordgelijkheid en relevant evaluatorpad gecontroleerd.
- **P1–P6:** `bewijs/proefopzet-v1.json`, `proeven-c-v1.py`, `proefuitkomsten-v1.json`, `proefuitvoer-v1.log`, `exitstatus-v1.txt`, `uitvoering-en-grenzen-v1.md`.

Beperkingen met gevolg: geen DBT-tekst → geen rechtstreekse Ross-exegese; geen ASTRA-revisievergelijking → claim alleen aangeleverde snapshot; geen live rechtsbron → geen rechtsadvies; geen volledige UI/opslag/exportdoorloop → ketenacceptatie blijft open; geen model-/gebruikersproef → geen aangetoonde kwaliteitswinst; geen ontvangen kruisreview/verwerking/synthesecontrole → uitsluitend **onafhankelijke v1 opgeleverd**, geen gezamenlijk afgerond onderzoek.
