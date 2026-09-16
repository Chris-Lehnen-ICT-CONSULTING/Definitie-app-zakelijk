# CON-02: 31 brongebonden praktijktestgevallen

14 september 2026 · Ontwerp ter deskundige beoordeling · Niet uitgevoerd

Dit document is de leesweergave van C02-P01–P31 in `casusregister-geintegreerd-v6.json`. De 47 oudere scenario’s en historische waarnemingen blijven behouden; verwachtingen N01/N04/N09 zijn expliciet aangevuld met de nu gelezen verwijseisen. Invoervoorbeelden zijn concrete testdefinities; positieve verwachtingen zijn voorstellen, geen reeds verleende goedkeuring.

Bronnen en geverifieerde tekst staan in `bronmanifest-v3.json` en `fixtures/`. Scores, retrievalrangordes, mutanten en toekomstige reviewvoorwaarden zijn bewust ontworpen testdata. Er zijn geen echte historische wetswijzigingen verzonnen.

## Startset en uitvoering

Begin met P01, P02, P04, P08, P10, P11, P14, P15, P16 en P28. Laat eerst de inhoudelijke orakels adjudiceren; voer daarna gecontroleerde component-/integratietests en vervolgens de volledige gebruikersketen uit. Een niet-uitvoerbare stap is een expliciete blokkade of ontbrekende capability, geen pass.

Gebruik een nieuwe geïsoleerde testdatabase en collection, nooit bestaande productiedata. Bewaar fixturehashes en maak per run een mapping naar werkelijke document- en chunk-IDs. De huidige app uploadt TXT/MD; de JSON-retrievalrecepten zijn voor een toekomstige testadapter, geen bestaande importknop. Exacte scores zijn synthetisch. Voor een echte RAG-run leg je de werkelijke ranking vast en vergelijk je die met de relevante passages; verwacht niet identieke embeddingscores.

De app-routebijlage bevat codegelezen labels, geen live DOM-verificatie. De stappen hieronder beschrijven handelingen en controlepunten zonder verzonnen knoppen. Niet-bestaande bewijs-/reviewvelden moeten in een extern testbewijs worden vastgelegd en als productgat gemeld; dit vervangt de productfunctie niet.

Voor generatie: bewaar prompt en ontvangen broncontext, zet model/instellingen vast en sla het antwoord op. Voor validatie: bied de vermelde vaste definitie expliciet aan; als de UI dat niet kan, leg de benodigde testadapter vast. Een variabel LLM-antwoord is geen uitvoering van dezelfde vaste testcase.

## Te bewaren bewijs bij iedere run

1. Appcommit, datum, testcase-ID, fixturehashes, testomgeving en werkelijk ontvangen invoer.
2. Extractietekst, geselecteerde snippets, raw retrieval, toegepaste filters en werkelijk gebruikte promptcontext.
3. Regelresultaat vóór/na adapters; bron-/definitieversie, locator, passage, oordeel en actor.
4. Opgeslagen record, herladen record, vaststellingsuitkomst en gelabelde draft/niet-draft-export (waar van toepassing).
5. Werkelijke waarneming naast verwachting; deskundig oordeel met onderbouwing. Geen automatische promotie van voorgesteld naar expertbeoordeeld.

Statusnamen bij ontbrekende invoer zijn nog een beleidskeuze (D4b). Toets daarom eerst observeerbaar gedrag en de bestaande DEF-630-poort: vereist actueel bewijs/review ontbreekt → geen vaststelling of niet-draft-export. De D2–D5-voorstellen zijn niet stilzwijgend vastgesteld.

## Actuele normbasis

De actuele primaire ASTRA-pagina is nu gelezen. Naast bronbasis verlangt de toelichting nauwkeurige, beknopte bronvermelding en een specifieke hyperlink. S-ASTRA-ACTUEEL is de normbron, geen automatisch meegegeven domeinbron voor generatie. Menselijke review, hash-/versiecontrole, scoring en exportpoorten blijven afzonderlijke lokale contracten of voorstellen. P29–P31 maken de verwijseisen apart toetsbaar. Oudere ASTRA-revisies spelen geen rol.


## C02-P01 — Volledige Awb-bron, inhoudelijk passende definitie

**Route:** upload · **Prioriteit:** P1 · **Bronnen:** S-AWB13

**Begrip/context:** besluit — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling

**Gegeven:** Upload en selecteer S-AWB13; registreer versie, art. 1:3 lid 1 en passage. Nog geen deskundig oordeel.

**Wanneer:** Genereer/beoordeel de vastgezette definitie met geselecteerde bron.

**Dan (verwachting):** Leg passage, bronhash, locator en betekenisvergelijking vast; markeer zonder echte review nog niet als goedgekeurd.

**Brongebonden onderbouwing:** Alle kenmerken zijn in lid 1 terug te vinden. Het ontbreken van de naam Awb in de definitiezin maakt de bronsteun niet onjuist. De actuele ASTRA verlangt wél een precieze/korte verwijzing en gerichte hyperlink bij de bronregistratie; ontbreken van bronnaam in de definitiezin is een andere vraag.

**Deskundige beoordeelt:** Zijn schriftelijk, bestuursorgaan en publiekrechtelijke rechtshandeling volledig en toepasselijk?

**Beleidsbasis/open keuze:** D1; D3: bron bij record versus inline; D5

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P02 — Bron aanwezig maar publiekrechtelijke beperking ontbreekt

**Route:** upload · **Prioriteit:** P1 · **Bronnen:** S-AWB13

**Begrip/context:** besluit — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** beslissing van een bestuursorgaan

**Gegeven:** Zelfde bronpakket als P01.

**Wanneer:** Beoordeel deze ingekorte definitie.

**Dan (verwachting):** Signaleer ontbrekende kenmerken; bronaanwezigheid mag dit niet als inhoudelijk conform afdoen.

**Brongebonden onderbouwing:** Schriftelijk en publiekrechtelijke rechtshandeling uit lid 1 ontbreken.

**Deskundige beoordeelt:** Maakt de weglating de afbakening te ruim in het gekozen Awb-profiel?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P03 — Gezaghebbende upload gaat over een ander begrip

**Route:** upload · **Prioriteit:** P1 · **Bronnen:** S-BW3

**Begrip/context:** besluit — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling

**Gegeven:** Selecteer uitsluitend BW3-artikelen 1, 2 en 2a.

**Wanneer:** Beoordeel besluit.

**Dan (verwachting):** Registreer dat deze passages de Awb-betekenis niet onderbouwen; brongezag alleen levert geen passend bewijs.

**Brongebonden onderbouwing:** S-BW3 bevat goederen/zaken/dieren; geen besluitbegrip.

**Deskundige beoordeelt:** Is er voor deze definitie enige relevante steun in het aangeleverde fragment?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P04 — Bestaand meegegeven tekstbestand zonder eigen herkomst

**Route:** upload · **Prioriteit:** P1 · **Bronnen:** S-UPLOAD32

**Begrip/context:** zorgvuldigheidsbeginsel — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** plicht van het bestuursorgaan om bij besluitvoorbereiding de nodige kennis over relevante feiten en af te wegen belangen te vergaren

**Gegeven:** Gebruik alleen het bestaande uploadbestand; neem het externe manifest niet automatisch als door de app ontvangen bewijs aan.

**Wanneer:** Upload, selecteer en beoordeel; inspecteer ontvangen bewijsvelden.

**Dan (verwachting):** Tekst kan inhoudelijk bruikbaar zijn, maar URL/versie/review mogen niet worden verzonnen uit de bestandsnaam.

**Brongebonden onderbouwing:** Wetszin is buiten de app met S-AWB32 vergeleken; het oorspronkelijke bestand zelf mist versie/URL. De kop is geen wettelijke definitie. Het ontbreken van een gecontroleerde gerichte hyperlink/vindplaats is een apart normcontrolepunt; een bestandsnaam vervangt dat niet.

**Deskundige beoordeelt:** Kan deze omschrijving uit de normzin worden afgeleid, en welk expliciet bronbewijs is nodig?

**Beleidsbasis/open keuze:** D4b: ontbrekende essentiële invoer Codex not_evaluated / Cowork review_required of fail; D5

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P05 — Meegegeven bestand gekoppeld aan gecontroleerde wetspassage

**Route:** upload · **Prioriteit:** P1 · **Bronnen:** S-UPLOAD32, S-AWB32

**Begrip/context:** zorgvuldigheidsbeginsel — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** plicht van het bestuursorgaan om bij besluitvoorbereiding de nodige kennis over relevante feiten en af te wegen belangen te vergaren

**Gegeven:** Zelfde oorspronkelijke bestand als P04; voeg expliciete vergelijking met S-AWB32, versie en art. 3:2 toe.

**Wanneer:** Beoordeel bronbinding en afgeleide definitie.

**Dan (verwachting):** Toon de traceerbare koppeling; onderscheid letterlijke wetszin van afgeleide begripsomschrijving.

**Brongebonden onderbouwing:** Exacte wetszin gelijk; kop Zorgvuldigheidsbeginsel is redactioneel toegevoegd.

**Deskundige beoordeelt:** Accepteert de deskundige de afleiding, met behoud van alle normelementen?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P06 — Hernoemen maakt dezelfde bron niet onafhankelijk

**Route:** upload · **Prioriteit:** P2 · **Bronnen:** S-AWB13, S-RENAME

**Begrip/context:** besluit — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling

**Gegeven:** Upload beide bestanden met identieke bytes en verschillende namen in testomgeving.

**Wanneer:** Vergelijk document-IDs en genormaliseerde bronregistratie.

**Dan (verwachting):** Bestands-IDs mogen verschillen; registreer één inhoudelijke bronversie en geen twee onafhankelijke bevestigingen.

**Brongebonden onderbouwing:** Hashes zijn identiek; bekeken processor-ID is naamafhankelijk.

**Deskundige beoordeelt:** Blijft de semantische bronidentiteit duidelijk ondanks twee bestandsrecords?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

**Uitgevoerde deelproef:** Gelijke bytes leverden verschillende document-IDs op via de echte processorfunctie. Zie `proeven-20260914-v1/uitkomst-v1.json`. Dit is geen volledige case-uitvoering.


## C02-P07 — Dezelfde bestandsnaam met gewijzigde wetszin

**Route:** upload · **Prioriteit:** P1 · **Bronnen:** S-UPLOAD32, M-UPLOAD

**Begrip/context:** zorgvuldigheidsbeginsel — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** plicht om alleen relevante feiten te onderzoeken

**Gegeven:** Gebruik eerst originele upload; bied daarna de gemuteerde kopie met dezelfde basename aan. Dit is testmanipulatie, geen wetswijziging.

**Wanneer:** Controleer duplicate-handling, inhoudshash en eventuele eerdere reviewbinding.

**Dan (verwachting):** Meld nieuwe/afwijkende inhoud of expliciete afwijzing van vervanging; nooit stil oude review voor nieuwe inhoud laten gelden.

**Brongebonden onderbouwing:** Mutant verwijdert de af te wegen belangen; naamgelijkheid bewijst geen inhoudsgelijkheid.

**Deskundige beoordeelt:** Wordt de cumulatieve norm onterecht beperkt?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P08 — RAG haalt het juiste beleidsregellid op

**Route:** RAG · **Prioriteit:** P1 · **Bronnen:** S-AWB13

**Begrip/context:** beleidsregel — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, over belangenafweging, feitenvaststelling of uitleg van wettelijke voorschriften bij het gebruik van een bestuursbevoegdheid

**Gegeven:** Indexeer S-AWB13; gebruik gecontroleerde retrieval R-BELEID.

**Wanneer:** Beoordeel de vaste definitie en volg lid 4 door prompt en bewijsregistratie.

**Dan (verwachting):** Alle kenmerken en uitsluiting blijven controleerbaar; retrievalscore vervangt review niet.

**Brongebonden onderbouwing:** Steun in volledig lid 4; algemene regel is niet hetzelfde als algemeen verbindend voorschrift.

**Deskundige beoordeelt:** Is de parafrase van lid 4 inhoudelijk equivalent?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Retrievalrecept:** `R-BELEID` in `retrieval-fixtures-v1.json`.

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P09 — Hoge RAG-score met verkeerd lid

**Route:** RAG · **Prioriteit:** P1 · **Bronnen:** S-AWB13

**Begrip/context:** beleidsregel — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** algemeen verbindend voorschrift van een bestuursorgaan

**Gegeven:** Retrieval R-VERKEERD-LID geeft alleen besluit/lid 1 met score 0.99.

**Wanneer:** Beoordeel bronsteun voor beleidsregel.

**Dan (verwachting):** Geen inhoudelijke goedkeuring op score of alleen artikelnummer; markeer verkeerde passage en ontbrekend lid 4.

**Brongebonden onderbouwing:** Lid 1 definieert besluit; lid 4 sluit algemeen verbindend voorschrift expliciet uit.

**Deskundige beoordeelt:** Welke passage is werkelijk gebruikt, en waaruit blijkt de inhoudelijke tegenspraak?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Retrievalrecept:** `R-VERKEERD-LID` in `retrieval-fixtures-v1.json`.

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P10 — Dierenuitzondering aanwezig in corpus maar buiten top vijf

**Route:** RAG · **Prioriteit:** P1 · **Bronnen:** S-AWB13, S-BW3

**Begrip/context:** zaak — BW Boek 3 / Nederlands vermogensrecht

**Vaste testdefinitie:** voor menselijke beheersing vatbaar stoffelijk object, waaronder een dier

**Gegeven:** Gebruik R-DIER-BUITEN-TOP5; art. 2a staat als kandidaat op rang 6 en 7.

**Wanneer:** Laat top_k=5 ophalen en beoordeel de vaste definitie.

**Dan (verwachting):** Bewaar werkelijk ontvangen chunks; claim niet dat art. 2a is meegenomen omdat het is geïndexeerd. Onvoldoende/tegenstrijdig bewijs moet review uitlokken.

**Brongebonden onderbouwing:** Volledige corpus bevat Dieren zijn geen zaken; top vijf mist deze beperking.

**Deskundige beoordeelt:** Herkent men dat de gekozen bronset onvoldoende is om inclusief dieren te bevestigen?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Retrievalrecept:** `R-DIER-BUITEN-TOP5` in `retrieval-fixtures-v1.json`.

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P11 — Zelfde dierencasus met volledige relevante retrieval

**Route:** RAG · **Prioriteit:** P1 · **Bronnen:** S-BW3

**Begrip/context:** zaak — BW Boek 3 / Nederlands vermogensrecht

**Vaste testdefinitie:** voor menselijke beheersing vatbaar stoffelijk object, waaronder een dier

**Gegeven:** Gebruik R-DIER-VOLLEDIG met art. 2 en beide leden van 2a.

**Wanneer:** Beoordeel dezelfde definitie als P10.

**Dan (verwachting):** Signaleer expliciete strijd met art. 2a lid 1; lid 2 maakt dieren niet alsnog zaken.

**Brongebonden onderbouwing:** Art. 2a lid 1 sluit dieren uit; lid 2 regelt toepasselijkheid van bepalingen met beperkingen.

**Deskundige beoordeelt:** Bevestigt de deskundige het onderscheid kwalificatie versus toepasselijke bepalingen?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Retrievalrecept:** `R-DIER-VOLLEDIG` in `retrieval-fixtures-v1.json`.

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P12 — Begripsnaam staat niet letterlijk in de ondersteunende wetszin

**Route:** upload · **Prioriteit:** P1 · **Bronnen:** S-AWB32

**Begrip/context:** zorgvuldigheidsbeginsel — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** plicht van het bestuursorgaan om bij besluitvoorbereiding kennis over relevante feiten en af te wegen belangen te vergaren

**Gegeven:** Upload S-AWB32 met kop Artikel 3:2; het woord zorgvuldigheidsbeginsel komt er niet in voor.

**Wanneer:** Inspecteer letterlijke snippetselectie en werkelijk aan generatie/validatie doorgegeven tekst.

**Dan (verwachting):** Rapporteer werkelijk wel/geen passage; geen bronbewijs claimen op basis van alleen een upload of documentaantal.

**Brongebonden onderbouwing:** Relevante wetszin bestaat, maar de term ontbreekt letterlijk. Dit onderscheidt vindbaarheid van normsteun.

**Deskundige beoordeelt:** Is de afgeleide omschrijving passend, ook zonder letterlijke naam in de bron?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

**Uitgevoerde deelproef:** Werkelijke TXT-extractor en snippetfunctie: 0 snippets zonder begripsnaam, 1 met begripsnaam in kop. Zie `proeven-20260914-v1/uitkomst-v1.json`. Dit is geen volledige case-uitvoering.


## C02-P13 — Artikel/lid en chunk-ID door normalisatie en opslag

**Route:** RAG · **Prioriteit:** P1 · **Bronnen:** S-AWB13

**Begrip/context:** aanvraag — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** verzoek van een belanghebbende om een besluit te nemen

**Gegeven:** Gebruik een echte geïndexeerde lid-3-passage met werkelijke document-ID, chunk-ID en lidmetadata. Bronversie/hash zijn geen aangetoond ingestcontract: lever deze afzonderlijk via de voorgestelde testadapter aan en leg dat als nieuwe testvoorwaarde vast.

**Wanneer:** Leg raw retrieval, prompt, provenance, opslag, herladen en export naast elkaar.

**Dan (verwachting):** Dezelfde gekozen passage en bronversie moeten terugvindbaar blijven; noteer exact eerste verliespunt.

**Brongebonden onderbouwing:** Codebijlage toont document-/chunk-ID en lid in raw retrieval en verlies daarvan in de provenanceprojectie. Bronversie/hash ontbreken als expliciet ingestcontract; er kan pas transportverlies worden getest nadat ze aantoonbaar zijn aangeleverd. Latere opslag-/exportstappen zijn nog niet getest.

**Deskundige beoordeelt:** Kan een andere reviewer exact dezelfde passage terugvinden?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P14 — Alleen een reviewed/high-wikipagina

**Route:** LLM-WIKI · **Prioriteit:** P1 · **Bronnen:** S-WIKI

**Begrip/context:** LLM-wiki — Karpathy LLM-wiki-patroon

**Vaste testdefinitie:** kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling onveranderlijke bronnen

**Gegeven:** Upload alleen de echte begrippenpagina, zonder bronpagina of raw.

**Wanneer:** Beoordeel bewijs en frontmatter.

**Dan (verwachting):** Reviewed/high gelden als beweringen van dit bestand; geen daadwerkelijke onafhankelijke review of volledig primaire keten afleiden.

**Brongebonden onderbouwing:** De pagina noemt twee sources; die zijn niet automatisch opgehaald door deze upload.

**Deskundige beoordeelt:** Welke concrete claim kan worden vastgesteld zonder de onderliggende bronnen?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P15 — Wiki met navolgbare raw-steun voor afgebakende definitieclaim

**Route:** LLM-WIKI · **Prioriteit:** P1 · **Bronnen:** S-WIKI, S-WIKISOURCE, S-RAW, S-RAWREGISTER

**Begrip/context:** LLM-wiki — Karpathy LLM-wiki-patroon

**Vaste testdefinitie:** kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling onveranderlijke bronnen

**Gegeven:** Bied pagina, bronpagina, raw en register-uittreksel samen aan; controleer raw-hash en Architecture/Core idea.

**Wanneer:** Maak voor alleen deze definitie een claim-passagekoppeling.

**Dan (verwachting):** Bewaar afgeleide/ruwe bronrol en capturedatum; markeer geen totale wikivalidatie. Overige bronnen in pagina blijven buiten gecontroleerde scope.

**Brongebonden onderbouwing:** Raw beschrijft persistente interlinked markdown-wiki, LLM-onderhoud en immutable raw sources. De tweede pluginbron en andere claims zijn hier niet geverifieerd.

**Deskundige beoordeelt:** Zijn de vier kenmerken voldoende ondersteund en correct afgebakend tot het patroon?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P16 — Wiki wijzigt betekenis maar behoudt reviewed-label

**Route:** LLM-WIKI · **Prioriteit:** P1 · **Bronnen:** M-WIKI, S-RAW

**Begrip/context:** LLM-wiki — Karpathy LLM-wiki-patroon

**Vaste testdefinitie:** kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling bronnen die het taalmodel tijdens onderhoud herschrijft

**Gegeven:** Gebruik alleen de duidelijk als mutant geregistreerde wikikopie naast originele raw.

**Wanneer:** Vergelijk gewijzigde definitie met Architecture / Raw sources.

**Dan (verwachting):** Detecteer inhoudelijke tegenspraak ondanks ongewijzigde reviewed/high-frontmatter.

**Brongebonden onderbouwing:** Raw zegt immutable en never modifies; mutant zegt herschrijven.

**Deskundige beoordeelt:** Welk kenmerk is omgekeerd, en waarom is oude frontmatter geen actuele review?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P17 — Raw-bestand gewijzigd zonder registerhash te actualiseren

**Route:** LLM-WIKI · **Prioriteit:** P1 · **Bronnen:** S-WIKI, M-RAW, S-RAWREGISTER

**Begrip/context:** LLM-wiki — Karpathy LLM-wiki-patroon

**Vaste testdefinitie:** kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling onveranderlijke bronnen

**Gegeven:** Gebruik M-RAW met de verwachte registerhash van S-RAW.

**Wanneer:** Herbereken hash vóór claimbeoordeling.

**Dan (verwachting):** Meld integriteitsafwijking; verwijs niet stil naar oorspronkelijke capture als bewijs voor andere bytes.

**Brongebonden onderbouwing:** immutable is in testkopie mutable geworden; hash verschilt aantoonbaar.

**Deskundige beoordeelt:** Welk bronexemplaar is beoordeeld en kan dat nog aan het register worden gebonden?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

**Uitgevoerde deelproef:** Externe SHA256-proef: originele raw komt overeen met register; gemuteerde raw wijkt af. Geen automatische wiki-productcontrole bewezen. Zie `proeven-20260914-v1/uitkomst-v1.json`. Dit is geen volledige case-uitvoering.


## C02-P18 — Niet-aangeleverde wiki-bron niet als gelezen registreren

**Route:** LLM-WIKI · **Prioriteit:** P2 · **Bronnen:** S-WIKI, S-RAW

**Begrip/context:** LLM-wiki — Karpathy LLM-wiki-patroon

**Vaste testdefinitie:** kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling onveranderlijke bronnen

**Gegeven:** Pagina noemt Karpathy en praneybehl; alleen Karpathy-raw is meegeleverd.

**Wanneer:** Controleer sources-resolutie en gebruikte bewijsclaims.

**Dan (verwachting):** Ontbrekende tweede bron blijft expliciet onopgelost; geen verzonnen passage/URL-inhoud. Afgebakende claim mag afzonderlijk worden beoordeeld met S-RAW.

**Brongebonden onderbouwing:** Een identifier in frontmatter is geen gelezen document. Het voorbeeld met 100 artikelen/400K woorden valt buiten deze onderbouwde claim.

**Deskundige beoordeelt:** Is duidelijk welke claims wél en niet door de beschikbare bron worden gedragen?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P19 — Beschikking omvat ook afwijzing

**Route:** wettekst · **Prioriteit:** P1 · **Bronnen:** S-AWB13

**Begrip/context:** beschikking — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan

**Gegeven:** Gecontroleerde Awb-art. 1:3 lid 2 beschikbaar.

**Wanneer:** Vergelijk definitie en expliciete randcasus afwijzing van een aanvraag om zo een besluit.

**Dan (verwachting):** Behoud afwijzing in afbakening; niet alleen positieve/toewijzende besluiten accepteren.

**Brongebonden onderbouwing:** De gekozen definitie volgt lid 2 inclusief de expliciete inclusie.

**Deskundige beoordeelt:** Klopt afbakening in het Awb-profiel, zonder ononderzochte praktijkuitzonderingen te verzinnen?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P20 — Aanvraag zonder belanghebbende-eis

**Route:** wettekst · **Prioriteit:** P1 · **Bronnen:** S-AWB13

**Begrip/context:** aanvraag — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** verzoek van een willekeurige persoon om een besluit te nemen

**Gegeven:** Gecontroleerde Awb-art. 1:3 lid 3 beschikbaar.

**Wanneer:** Beoordeel definitie en grenscasus verzoeker zonder belanghebbendheid.

**Dan (verwachting):** Markeer verbreding van het wettelijke begrip; bepaal belanghebbendheid niet automatisch op fictieve persoonsgegevens.

**Brongebonden onderbouwing:** Lid 3 noemt een belanghebbende, niet iedere willekeurige persoon.

**Deskundige beoordeelt:** Welke betekenisbeperking gaat verloren?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P21 — Goed is ruimer dan alleen stoffelijk object

**Route:** wettekst · **Prioriteit:** P1 · **Bronnen:** S-BW3

**Begrip/context:** goed — BW Boek 3 / Nederlands vermogensrecht

**Vaste testdefinitie:** voor menselijke beheersing vatbaar stoffelijk object

**Gegeven:** Gebruik BW3-art. 1 en 2 naast elkaar.

**Wanneer:** Vergelijk definitie en grenscasus vermogensrecht.

**Dan (verwachting):** Signaleer verwisseling van goed en zaak; behoud vermogensrechten in goederenbegrip.

**Brongebonden onderbouwing:** Art. 1 omvat zaken én vermogensrechten; art. 2 definieert zaken.

**Deskundige beoordeelt:** Is de extensie door deze begripsverwisseling te beperkt?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P22 — Geen zaken betekent niet dat zakenbepalingen nooit gelden

**Route:** wettekst · **Prioriteit:** P1 · **Bronnen:** S-BW3

**Begrip/context:** dier — BW Boek 3 / Nederlands vermogensrecht

**Vaste testdefinitie:** levend wezen waarop geen bepalingen met betrekking tot zaken van toepassing zijn

**Gegeven:** Gebruik beide leden van BW3-art. 2a; beoordeling beperkt tot de juridische toevoeging aan de definitie.

**Wanneer:** Beoordeel de absolute uitsluiting.

**Dan (verwachting):** Verwerp nooit-bepalingen-van-toepassing als strijdig met lid 2; claim niet dat de wet hier een volledige biologische definitie geeft.

**Brongebonden onderbouwing:** Lid 2 verklaart bepalingen met beperkingen van toepassing.

**Deskundige beoordeelt:** Blijft het onderscheid tussen juridische kwalificatie en toepasselijkheid correct?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P23 — Dezelfde bron via upload, RAG en wiki telt niet driemaal

**Route:** keten · **Prioriteit:** P1 · **Bronnen:** S-WIKI, S-RAW

**Begrip/context:** LLM-wiki — Karpathy LLM-wiki-patroon

**Vaste testdefinitie:** kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling onveranderlijke bronnen

**Gegeven:** Bied S-RAW aan via upload én RAG; S-WIKI citeert dezelfde raw-capture.

**Wanneer:** Vergelijk evidencegraph en aantallen onafhankelijke bronnen.

**Dan (verwachting):** Behoud de drie routes maar één onderliggende capture; geen onafhankelijkheid uit kanaalaantal afleiden.

**Brongebonden onderbouwing:** Alle routes komen uit dezelfde oorspronkelijke tekst, gekoppeld op hash/canonieke URL.

**Deskundige beoordeelt:** Is brononafhankelijkheid inhoudelijk onderbouwd in plaats van geteld?

**Beleidsbasis/open keuze:** D1/D3/D5: voorgestelde bron- en betekeniscontrole; nog vast te stellen

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P24 — Bron wijzigt na deskundige beoordeling

**Route:** keten · **Prioriteit:** P1 · **Bronnen:** S-UPLOAD32, M-UPLOAD

**Begrip/context:** zorgvuldigheidsbeginsel — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** plicht om de nodige kennis over relevante feiten en af te wegen belangen te vergaren

**Gegeven:** Voor uitvoering is een echte review van exact origineel vereist; testkopie krijgt daarna gewijzigde bytes. Geen review is nu aanwezig.

**Wanneer:** Bied mutant aan onder gelijknamig bronrecord en probeer vaststelling/niet-draft-export.

**Dan (verwachting):** Oud oordeel geldt niet automatisch voor nieuwe bronhash; markeer ontbrekende actuele binding en blokkeer zolang vereist bewijs ontbreekt.

**Brongebonden onderbouwing:** P07-mutatie verandert de norminhoud; eerdere review bindt aan eerdere bytes.

**Deskundige beoordeelt:** Is review zichtbaar gekoppeld aan de beoordeelde bron én definitieversie?

**Beleidsbasis/open keuze:** Bestaand DEF-630: actueel bewijs/review; D5: nieuw versiecontract

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P25 — Definitie wijzigt na deskundige beoordeling

**Route:** keten · **Prioriteit:** P1 · **Bronnen:** S-AWB13

**Begrip/context:** besluit — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** beslissing van een bestuursorgaan

**Gegeven:** Vereist bij uitvoering echte review van P01; wijzig daarna definitie naar P02 zonder review.

**Wanneer:** Sla op, herlaad en probeer vaststelling/niet-draft-export.

**Dan (verwachting):** Eerder oordeel mag de nieuwe definitie niet afdekken; status/gate blijven na herladen consistent.

**Brongebonden onderbouwing:** Nieuwe tekst mist kenmerken die oude beoordeelde tekst wel had.

**Deskundige beoordeelt:** Is definitiehash/revisie onderdeel van de reviewbinding?

**Beleidsbasis/open keuze:** Bestaand DEF-630: actueel snapshot/evidence/actor/review

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P26 — Boolean reviewed=true is geen beoordelaarsbewijs

**Route:** keten · **Prioriteit:** P1 · **Bronnen:** S-AWB13

**Begrip/context:** besluit — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling

**Gegeven:** Voer bij testadapter alleen reviewed=true op zonder reviewer-identiteit, bevoegdheid, passage en datum. Gebruik geen echte identiteit als fictie.

**Wanneer:** Valideer en probeer vaststelling/niet-draft-export.

**Dan (verwachting):** Geen bevoegde review fabriceren; ontbrekende actor/evidencevelden blijven een blokkade.

**Brongebonden onderbouwing:** Boolean zegt niets over wie welke versie heeft beoordeeld.

**Deskundige beoordeelt:** Zijn identiteit, bevoegdheid, oordeel en exacte beoordeelde inhoud aantoonbaar?

**Beleidsbasis/open keuze:** Bestaand DEF-630: actor/review; D4b-statuskeuze nog open

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P27 — Bewijspakket blijft inspecteerbaar na opslaan/herladen/export

**Route:** keten · **Prioriteit:** P1 · **Bronnen:** S-AWB13

**Begrip/context:** besluit — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling

**Gegeven:** Uitvoering vereist echt volledig beoordeeld P01-record; zonder dat alleen gelabelde draft.

**Wanneer:** Leg vóór opslag en na herladen/export bron, lid, passage, definitieversie, reviewer en uitkomst vast.

**Dan (verwachting):** Vergelijk dezelfde bindingsvelden; export zonder nodig bewijs is geen geslaagde overdracht. CON-02-conform is geen algemene exporttoestemming. Controleer ook behoud van de korte citeervorm en gerichte hyperlink in de bronpresentatie.

**Brongebonden onderbouwing:** Primaire vindplaats art. 1:3 lid 1 en bronversie zijn reproduceerbaar vastgelegd.

**Deskundige beoordeelt:** Kan een tweede reviewer uitsluitend met export exact de beoordeling reconstrueren?

**Beleidsbasis/open keuze:** Bestaand DEF-630; D3: recordgebonden bewijscontract

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P28 — Hoge totaalscore heft ontbrekend bronbewijs niet op

**Route:** keten · **Prioriteit:** P1 · **Bronnen:** S-BW3

**Begrip/context:** besluit — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling

**Gegeven:** Gebruik niet-passende bron P03 en een gecontroleerde testscore 0.99; essentiële actuele evidence/review ontbreekt.

**Wanneer:** Volg regelstatus door adapters, UI, opslag, herladen en vaststelling/niet-draft-export.

**Dan (verwachting):** Geen toestemming op basis van score; ontbrekende vereisten blijven blokkerend. Concept mag alleen herkenbaar concept blijven.

**Brongebonden onderbouwing:** BW3-fragment ondersteunt besluit niet; ranking/score is geen passagebewijs.

**Deskundige beoordeelt:** Blijft de beslispoort gekoppeld aan bewijsstatus op alle stappen?

**Beleidsbasis/open keuze:** Bestaand DEF-630; D4a scorekeuze open; D4b statusnaam open

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P29 — Juiste betekenis, maar verwijzing slechts naar wetten-startpagina

**Route:** bronverwijzing · **Prioriteit:** P2 · **Bronnen:** S-AWB13

**Begrip/context:** besluit — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling

**Bronlabel:** Awb

**Hyperlinkveld:** https://wetten.overheid.nl/

**Gegeven:** Zelfde definitie/passage als P01; bronlabel Awb zonder artikel/lid en hyperlink alleen naar de startpagina.

**Wanneer:** Controleer inhoudelijke bronsteun en verwijskwaliteit afzonderlijk in het vastgezette testrecord.

**Dan (verwachting):** Markeer onvoldoende precieze verwijzing; leid daaruit niet af dat de definitie inhoudelijk onjuist is.

**Brongebonden onderbouwing:** De beschikbare bronpassage ondersteunt besluit. De verwijzing leidt niet specifiek naar art. 1:3 lid 1.

**Deskundige beoordeelt:** Is de bronverwijzing nauwkeurig, kort en bereikbaar volgens de actuele norm, los van de juistheid van de definitie?

**Beleidsbasis/open keuze:** Actuele ASTRA-toelichting: vindplaats, citeervorm, hyperlink; Status-/scorevertaling blijft D4-keuze

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P30 — Precieze bron met onnodig lange citeervorm

**Route:** bronverwijzing · **Prioriteit:** P2 · **Bronnen:** S-AWB13

**Begrip/context:** besluit — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling

**Bronlabel:** artikel 1:3 lid 1 van de Algemene wet bestuursrecht

**Hyperlinkveld:** https://wetten.overheid.nl/jci1.3:c:BWBR0005537&hoofdstuk=1&titeldeel=1.1&artikel=1:3&z=2026-08-15&g=2026-08-15

**Gegeven:** Zelfde definitie/passage als P01; correcte artikel/lid/versie en artikelhyperlink, maar uitgeschreven wetsnaam in het bronlabel.

**Wanneer:** Controleer inhoudelijke bronsteun en verwijskwaliteit afzonderlijk in het vastgezette testrecord.

**Dan (verwachting):** Geef gerichte verkorting van het bronlabel naar art. 1:3 lid 1 Awb; behoud vindplaats en hyperlink. Geen semantische afkeuring uitsluitend vanwege citeerlengte.

**Brongebonden onderbouwing:** De actuele toelichting onderscheidt compacte wetsafkorting van lange wetsnaam. De broninhoud verandert niet door deze redactie.

**Deskundige beoordeelt:** Is de bronverwijzing nauwkeurig, kort en bereikbaar volgens de actuele norm, los van de juistheid van de definitie?

**Beleidsbasis/open keuze:** Actuele ASTRA-toelichting: vindplaats, citeervorm, hyperlink; Status-/scorevertaling blijft D4-keuze

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.

## C02-P31 — Vindplaats compleet, beschikbare hyperlink ontbreekt

**Route:** bronverwijzing · **Prioriteit:** P2 · **Bronnen:** S-AWB13

**Begrip/context:** besluit — Awb / Nederlands bestuursrecht

**Vaste testdefinitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling

**Bronlabel:** art. 1:3 lid 1 Awb

**Hyperlinkveld:** (leeg)

**Gegeven:** Zelfde definitie/passage als P01; kort label en vaste bronversie aanwezig, maar hyperlinkveld leeg terwijl de primaire online wet is gevonden.

**Wanneer:** Controleer inhoudelijke bronsteun en verwijskwaliteit afzonderlijk in het vastgezette testrecord.

**Dan (verwachting):** Meld de ontbrekende gerichte hyperlink als apart verwijskwaliteitsgebrek. Een algemene claim dat CON-02 geen hyperlink verlangt is hier onvoldoende.

**Brongebonden onderbouwing:** De actuele toelichting vraagt een gerichte hyperlink. In deze casus bestaat een primaire online bron; een eventuele offline uitzondering is niet van toepassing verklaard.

**Deskundige beoordeelt:** Is de bronverwijzing nauwkeurig, kort en bereikbaar volgens de actuele norm, los van de juistheid van de definitie?

**Beleidsbasis/open keuze:** Actuele ASTRA-toelichting: vindplaats, citeervorm, hyperlink; Status-/scorevertaling blijft D4-keuze

**Volledige case-uitvoering:** niet uitgevoerd. **Deskundig oordeel:** nog niet aanwezig. Afzonderlijke componentproeven gelden uitsluitend voor hun beschreven grens.
