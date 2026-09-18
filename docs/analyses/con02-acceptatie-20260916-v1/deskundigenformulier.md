# CON-02 — Deskundigenformulier acceptatiepakket v1

Datum pakket: 2026-09-16 · Basis: `29b0900d4` · Branch: `feature/DEF-743-con02-acceptatie`

**Status: alle 31 casussen PENDING. Geen goldset. Geen appketenuitvoering. Geen modelkwaliteit bewezen.**

Dit formulier bevat per casus (1) de ongewijzigde historische scenario-input, (2) de historische brongebonden onderbouwing en vraag, (3) de exacte bronpassages met locator/hash/link, (4) de huidige laag met de projectbesluiten van 15 september 2026, en (5) lege beoordelingsvelden. Historische verwachtingen zijn ontwerpen; ze zijn nergens gepromoveerd tot 'pass'. Waar een bron een synthetische mutant of testconstructie is, staat dat expliciet.

Onderscheid dat overal geldt: **bestand aanwezig in dit pakket** ≠ **feitelijk door de app/het model ontvangen**. Het tweede is in dit pakket nergens vastgesteld.

## Projectbesluiten (huidige laag)

- **B1 — Deskundige verwijzingsuitzondering — goedgekeurd** (besluiten-20260915-v3.md §1): Alleen voor een bestaande bron ZONDER bruikbare hyperlink; bronversie bewaard, stabiele documentidentificatie en exacte vindplaats vastgelegd, deskundige motiveert en accepteert, app toont herkenbaar als uitzondering. Brongezag/toepasselijkheid en betekenissteun worden onverminderd beoordeeld. Nog geen implementatie.
- **B2 — CON-02-herstel alleen op verzoek — goedgekeurd** (besluiten-20260915-v3.md §2): Een CON-02-failure activeert geen automatische herstelpoging. De app toont probleem en onderbouwing; gebruiker vraagt afzonderlijk een voorstel aan, oorspronkelijke tekst blijft bewaard, overgenomen wijziging wordt opnieuw getoetst. Ontbrekend bewijs, transportverlies of onjuiste beoordeling zijn niet vanzelf fouten in de definitiezin.
- **B3 — Voorlopig geen totaalcijfer — goedgekeurd** (besluiten-20260915-v3.md §3): CON-02 krijgt geen numerieke bijdrage; per regel zichtbaar: voldoet / voldoet niet / nog te beoordelen, plus beoordelingsdekking. Ontbrekende beoordelingen worden niet als nul of volledige score ingevuld. Lagere dekking mag geen hogere kwaliteit suggereren.

## Beoordelingsschaal

Per casus vult de deskundige in: **Acceptatie** (de historische verwachting + huidige laag is juist als acceptatiecriterium) of **Afwijzing** (met motivering), plus actor en datum. Een lege regel is 'pending'. Er is geen cijfer (B3).

Voorgestelde eerste zes: C02-P01, C02-P02, C02-P04, C02-P11, C02-P16, C02-P31. Volgorde daarna: P03–P31 op nummer.

---

## C02-P01 — Volledige Awb-bron, inhoudelijk passende definitie ★ eerste zes

**Route:** upload · **Prioriteit:** P1 · **Bronnen:** S-AWB13 · **scenario_input_sha256:** `1d7a45c007ead39f…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** besluit
- **definitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling
- **context:** Awb / Nederlands bestuursrecht
- **Gegeven:** Upload en selecteer S-AWB13; registreer versie, art. 1:3 lid 1 en passage. Nog geen deskundig oordeel.
- **Wanneer:** Genereer/beoordeel de vastgezette definitie met geselecteerde bron.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-AWB13** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/awb-1-3-20260815.txt` · sha256 `7be6c298370590a6ca51e82d9f6e9f066274e86adc3051037748beb2078e3ec8`
- bronversie: 2026-08-15
- link: <https://wetten.overheid.nl/BWBR0005537/2026-08-15/0?g=2026-09-14&z=2026-09-14#Hoofdstuk1_Titeldeel1.1_Artikel1:3>
- locators (manifest): artikel 1:3 lid 1; artikel 1:3 lid 2; artikel 1:3 lid 3; artikel 1:3 lid 4
- **artikel 1:3 lid 1** — letterlijk:

> Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

- **artikel 1:3 lid 2** — letterlijk:

> Onder beschikking wordt verstaan: een besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan.

- **artikel 1:3 lid 3** — letterlijk:

> Onder aanvraag wordt verstaan: een verzoek van een belanghebbende, een besluit te nemen.

- **artikel 1:3 lid 4** — letterlijk:

> Onder beleidsregel wordt verstaan: een bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, omtrent de afweging van belangen, de vaststelling van feiten of de uitleg van wettelijke voorschriften bij het gebruik van een bevoegdheid van een bestuursorgaan.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Alle kenmerken zijn in lid 1 terug te vinden. Het ontbreken van de naam Awb in de definitiezin maakt de bronsteun niet onjuist. De actuele ASTRA verlangt wél een precieze/korte verwijzing en gerichte hyperlink bij de bronregistratie; ontbreken van bronnaam in de definitiezin is een andere vraag.
- **Historische verwachting (then, v6):** Leg passage, bronhash, locator en betekenisvergelijking vast; markeer zonder echte review nog niet als goedgekeurd.
- **T (GTH-v1):** Voldoet mogelijk na positieve onderbouwde bronbasis, betekenissteun en verwijskwaliteit voor de concrete claim. De casus is nog niet deskundig vastgesteld of uitgevoerd; een eerder verplicht menselijk voorafgaand CON-02-oordeel is vervangen door de expliciete AI-toestemming.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Cowork-aanvulling v1 (historisch):** T: Bronbasis: profiel 1. Betekenissteun: drie kenmerken terugvindbaar. Verwijskwaliteit: op dit moment NIET beoordeelbaar, want de app produceert voor .txt geen locator (G2) en gooit hem in transport weg (G3). Verwacht oordeel: 'nog te beoordelen' op verwijskwaliteit, niet 'voldoet niet'. · H: Geen herstel toegestaan: er is geen vastgestelde inhoudelijke tekortkoming. Wel een technische melding over de ontbrekende locator. · bewijssoort: ontwerp + codelezing; niet uitgevoerd
- **Locatorvoorwaarde (kruisreview-v2):** De invoer noemt bron/versie/artikel of locator; beoordeel die beschikbare informatie. Niet automatisch open op grond van TXT-formaat of een ontbrekend automatisch citation_label.
- **Deskundigenvraag:** Zijn schriftelijk, bestuursorgaan en publiekrechtelijke rechtshandeling volledig en toepasselijk?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P02 — Bron aanwezig maar publiekrechtelijke beperking ontbreekt ★ eerste zes

**Route:** upload · **Prioriteit:** P1 · **Bronnen:** S-AWB13 · **scenario_input_sha256:** `2dbdb03d8b08d364…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** besluit
- **definitie:** beslissing van een bestuursorgaan
- **context:** Awb / Nederlands bestuursrecht
- **Gegeven:** Zelfde bronpakket als P01.
- **Wanneer:** Beoordeel deze ingekorte definitie.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-AWB13** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/awb-1-3-20260815.txt` · sha256 `7be6c298370590a6ca51e82d9f6e9f066274e86adc3051037748beb2078e3ec8`
- bronversie: 2026-08-15
- link: <https://wetten.overheid.nl/BWBR0005537/2026-08-15/0?g=2026-09-14&z=2026-09-14#Hoofdstuk1_Titeldeel1.1_Artikel1:3>
- locators (manifest): artikel 1:3 lid 1; artikel 1:3 lid 2; artikel 1:3 lid 3; artikel 1:3 lid 4
- **artikel 1:3 lid 1** — letterlijk:

> Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

- **artikel 1:3 lid 2** — letterlijk:

> Onder beschikking wordt verstaan: een besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan.

- **artikel 1:3 lid 3** — letterlijk:

> Onder aanvraag wordt verstaan: een verzoek van een belanghebbende, een besluit te nemen.

- **artikel 1:3 lid 4** — letterlijk:

> Onder beleidsregel wordt verstaan: een bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, omtrent de afweging van belangen, de vaststelling van feiten of de uitleg van wettelijke voorschriften bij het gebruik van een bevoegdheid van een bestuursorgaan.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Schriftelijk en publiekrechtelijke rechtshandeling uit lid 1 ontbreken.
- **Historische verwachting (then, v6):** Signaleer ontbrekende kenmerken; bronaanwezigheid mag dit niet als inhoudelijk conform afdoen.
- **T (GTH-v1):** Betekenissteun voldoet niet: schriftelijkheid en publiekrechtelijke rechtshandeling ontbreken, ondanks passende bron. Benoem de twee kenmerken.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld. Concreet te behouden/herstellen: Betekenissteun voldoet niet: schriftelijkheid en publiekrechtelijke rechtshandeling ontbreken, ondanks passende bron. Benoem de twee kenmerken.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Cowork-aanvulling v1 (historisch):** T: Bronbasis positief, betekenissteun 'voldoet niet' met vermelding van de ontbrekende kenmerken. Bronaanwezigheid mag dit niet groen maken. · H: Terugkoppeling met de twee ontbrekende kenmerken en hun locator. Betekenis niet stil verbreden; niets toevoegen wat de passage niet draagt. · bewijssoort: ontwerp; niet uitgevoerd
- **Locatorvoorwaarde (kruisreview-v2):** De invoer noemt bron/versie/artikel of locator; beoordeel die beschikbare informatie. Niet automatisch open op grond van TXT-formaat of een ontbrekend automatisch citation_label.
- **Deskundigenvraag:** Maakt de weglating de afbakening te ruim in het gekozen Awb-profiel?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P03 — Gezaghebbende upload gaat over een ander begrip

**Route:** upload · **Prioriteit:** P1 · **Bronnen:** S-BW3 · **scenario_input_sha256:** `848e83cbdda05d17…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** besluit
- **definitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling
- **context:** Awb / Nederlands bestuursrecht
- **Gegeven:** Selecteer uitsluitend BW3-artikelen 1, 2 en 2a.
- **Wanneer:** Beoordeel besluit.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-BW3** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/bw3-1-2-2a-20250701.txt` · sha256 `cc46ab1cc9b667db076e9003a114b092a16a566c65aa62e256012165378d32ba`
- bronversie: 2025-07-01
- link: <https://wetten.overheid.nl/BWBR0005291/2025-07-01/0?g=2026-09-14&z=2026-09-14#Boek3_Titeldeel1_Afdeling1_Artikel2>
- locators (manifest): artikel 1; artikel 2; artikel 2a lid 1; artikel 2a lid 2
- **artikel 1** — letterlijk:

> Goederen zijn alle zaken en alle vermogensrechten.

- **artikel 2** — letterlijk:

> Zaken zijn de voor menselijke beheersing vatbare stoffelijke objecten.

- **artikel 2a lid 1** — letterlijk:

> Dieren zijn geen zaken.

- **artikel 2a lid 2** — letterlijk:

> Bepalingen met betrekking tot zaken zijn op dieren van toepassing, met in achtneming van de op wettelijke voorschriften en regels van ongeschreven recht gegronde beperkingen, verplichtingen en rechtsbeginselen, alsmede de openbare orde en de goede zeden.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** S-BW3 bevat goederen/zaken/dieren; geen besluitbegrip.
- **Historische verwachting (then, v6):** Registreer dat deze passages de Awb-betekenis niet onderbouwen; brongezag alleen levert geen passend bewijs.
- **T (GTH-v1):** Betekenissteun voldoet niet: de gezaghebbende upload gaat over een ander begrip. Gezag zonder relevantie is onvoldoende.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Cowork-aanvulling v1 (historisch):** T: Bronbasis: gezaghebbend maar niet toepasselijk. Betekenissteun: geen. Verwacht 'nog te beoordelen' met verzoek om een passende bron, niet 'voldoet' op grond van brongezag. · H: Geen tekstherstel; om een passende bron vragen. Een andere bron kiezen is geen automatische herstelactie. · bewijssoort: ontwerp; niet uitgevoerd
- **Locatorvoorwaarde (kruisreview-v2):** De invoer noemt bron/versie/artikel of locator; beoordeel die beschikbare informatie. Niet automatisch open op grond van TXT-formaat of een ontbrekend automatisch citation_label.
- **Deskundigenvraag:** Is er voor deze definitie enige relevante steun in het aangeleverde fragment?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P04 — Bestaand meegegeven tekstbestand zonder eigen herkomst ★ eerste zes

**Route:** upload · **Prioriteit:** P1 · **Bronnen:** S-UPLOAD32 · **scenario_input_sha256:** `afc66e314fab5116…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** zorgvuldigheidsbeginsel
- **definitie:** plicht van het bestuursorgaan om bij besluitvoorbereiding de nodige kennis over relevante feiten en af te wegen belangen te vergaren
- **context:** Awb / Nederlands bestuursrecht
- **Gegeven:** Gebruik alleen het bestaande uploadbestand; neem het externe manifest niet automatisch als door de app ontvangen bewijs aan.
- **Wanneer:** Upload, selecteer en beoordeel; inspecteer ontvangen bewijsvelden.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-UPLOAD32** · bestaand lokaal uploadbestand (echt, zonder eigen herkomst)

- pakketpad: `bronfixtures/meegegeven-awb-artikel-3-2.txt` · sha256 `73a64ab39bd2c2120adf13d323481153deed88b0a5f38b9e99d494ad0e5b9be0`
- bronversie: onbekend (null)
- herkomst (geen hyperlink): `/Users/chrislehnen/Projecten/Wetsanalyse/test-data/awb-artikel-3-2.txt`
- locators (manifest): wetszin onder beschrijvende kop
- **beschrijvende kop (geen wettekst)** — letterlijk:

> Artikel 3:2 Algemene wet bestuursrecht - Zorgvuldigheidsbeginsel

- **wetszin onder beschrijvende kop** — letterlijk:

> Bij de voorbereiding van een besluit vergaart het bestuursorgaan de nodige kennis omtrent de relevante feiten en de af te wegen belangen.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Wetszin is buiten de app met S-AWB32 vergeleken; het oorspronkelijke bestand zelf mist versie/URL. De kop is geen wettelijke definitie. Het ontbreken van een gecontroleerde gerichte hyperlink/vindplaats is een apart normcontrolepunt; een bestandsnaam vervangt dat niet.
- **Historische verwachting (then, v6):** Tekst kan inhoudelijk bruikbaar zijn, maar URL/versie/review mogen niet worden verzonnen uit de bestandsnaam.
- **T (GTH-v1):** Herkomst/versie nog te beoordelen; een bestandsnaam levert die niet. Betekenissteun en verwijskwaliteit afzonderlijk, geen brongegevens verzinnen.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Kan deze omschrijving uit de normzin worden afgeleid, en welk expliciet bronbewijs is nodig?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B1: de bron mist versie/URL; een verwijzingsuitzondering is NIET automatisch van toepassing. Zij vereist een bewaarde bronversie, stabiele documentidentificatie, exacte vindplaats én deskundige motivering/acceptatie. Zonder dat blijft herkomst 'nog te beoordelen'; een bestandsnaam of externe manifestkoppeling is geen ontvangen bewijs.
- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P05 — Meegegeven bestand gekoppeld aan gecontroleerde wetspassage

**Route:** upload · **Prioriteit:** P1 · **Bronnen:** S-UPLOAD32, S-AWB32 · **scenario_input_sha256:** `c831f223fa98f3af…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** zorgvuldigheidsbeginsel
- **definitie:** plicht van het bestuursorgaan om bij besluitvoorbereiding de nodige kennis over relevante feiten en af te wegen belangen te vergaren
- **context:** Awb / Nederlands bestuursrecht
- **Gegeven:** Zelfde oorspronkelijke bestand als P04; voeg expliciete vergelijking met S-AWB32, versie en art. 3:2 toe.
- **Wanneer:** Beoordeel bronbinding en afgeleide definitie.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-UPLOAD32** · bestaand lokaal uploadbestand (echt, zonder eigen herkomst)

- pakketpad: `bronfixtures/meegegeven-awb-artikel-3-2.txt` · sha256 `73a64ab39bd2c2120adf13d323481153deed88b0a5f38b9e99d494ad0e5b9be0`
- bronversie: onbekend (null)
- herkomst (geen hyperlink): `/Users/chrislehnen/Projecten/Wetsanalyse/test-data/awb-artikel-3-2.txt`
- locators (manifest): wetszin onder beschrijvende kop
- **beschrijvende kop (geen wettekst)** — letterlijk:

> Artikel 3:2 Algemene wet bestuursrecht - Zorgvuldigheidsbeginsel

- **wetszin onder beschrijvende kop** — letterlijk:

> Bij de voorbereiding van een besluit vergaart het bestuursorgaan de nodige kennis omtrent de relevante feiten en de af te wegen belangen.

**S-AWB32** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/awb-3-2-20260815.txt` · sha256 `ad520ff75fb2732204b93c2307e0b1806a400eedfd427cd4c19425e41bbdef97`
- bronversie: 2026-08-15
- link: <https://wetten.overheid.nl/jci1.3:c:BWBR0005537&hoofdstuk=3&afdeling=3.2&artikel=3:2&z=2026-08-15&g=2026-08-15>
- locators (manifest): artikel 3:2
- **artikel 3:2** — letterlijk:

> Bij de voorbereiding van een besluit vergaart het bestuursorgaan de nodige kennis omtrent de relevante feiten en de af te wegen belangen.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Exacte wetszin gelijk; kop Zorgvuldigheidsbeginsel is redactioneel toegevoegd.
- **Historische verwachting (then, v6):** Toon de traceerbare koppeling; onderscheid letterlijke wetszin van afgeleide begripsomschrijving.
- **T (GTH-v1):** Voldoet mogelijk na positieve onderbouwde bronbasis, betekenissteun en verwijskwaliteit voor de concrete claim. De casus is nog niet deskundig vastgesteld of uitgevoerd; een eerder verplicht menselijk voorafgaand CON-02-oordeel is vervangen door de expliciete AI-toestemming.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Accepteert de deskundige de afleiding, met behoud van alle normelementen?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B1: de controle-passage S-AWB32 heeft een bruikbare hyperlink (origin-URL in bronmanifest); de uitzondering is hier niet aan de orde. Of de app die koppeling feitelijk heeft ontvangen is niet vastgesteld.
- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P06 — Hernoemen maakt dezelfde bron niet onafhankelijk

**Route:** upload · **Prioriteit:** P2 · **Bronnen:** S-AWB13, S-RENAME · **scenario_input_sha256:** `0e0c4e0951091ef0…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** besluit
- **definitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling
- **context:** Awb / Nederlands bestuursrecht
- **Gegeven:** Upload beide bestanden met identieke bytes en verschillende namen in testomgeving.
- **Wanneer:** Vergelijk document-IDs en genormaliseerde bronregistratie.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-AWB13** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/awb-1-3-20260815.txt` · sha256 `7be6c298370590a6ca51e82d9f6e9f066274e86adc3051037748beb2078e3ec8`
- bronversie: 2026-08-15
- link: <https://wetten.overheid.nl/BWBR0005537/2026-08-15/0?g=2026-09-14&z=2026-09-14#Hoofdstuk1_Titeldeel1.1_Artikel1:3>
- locators (manifest): artikel 1:3 lid 1; artikel 1:3 lid 2; artikel 1:3 lid 3; artikel 1:3 lid 4
- **artikel 1:3 lid 1** — letterlijk:

> Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

- **artikel 1:3 lid 2** — letterlijk:

> Onder beschikking wordt verstaan: een besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan.

- **artikel 1:3 lid 3** — letterlijk:

> Onder aanvraag wordt verstaan: een verzoek van een belanghebbende, een besluit te nemen.

- **artikel 1:3 lid 4** — letterlijk:

> Onder beleidsregel wordt verstaan: een bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, omtrent de afweging van belangen, de vaststelling van feiten of de uitleg van wettelijke voorschriften bij het gebruik van een bevoegdheid van een bestuursorgaan.

**S-RENAME** · hernoemde byte-identieke kopie (testconstructie) — **SYNTHETISCH (mutant/testconstructie)**

- pakketpad: `bronfixtures/hernoemd/awb-1-3-andere-naam.txt` · sha256 `7be6c298370590a6ca51e82d9f6e9f066274e86adc3051037748beb2078e3ec8`
- bronversie: 2026-08-15
- herkomst (geen hyperlink): `S-AWB13`
- locators (manifest): artikel 1:3
- **artikel 1:3 lid 1** — letterlijk:

> Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

- **artikel 1:3 lid 2** — letterlijk:

> Onder beschikking wordt verstaan: een besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan.

- **artikel 1:3 lid 3** — letterlijk:

> Onder aanvraag wordt verstaan: een verzoek van een belanghebbende, een besluit te nemen.

- **artikel 1:3 lid 4** — letterlijk:

> Onder beleidsregel wordt verstaan: een bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, omtrent de afweging van belangen, de vaststelling van feiten of de uitleg van wettelijke voorschriften bij het gebruik van een bevoegdheid van een bestuursorgaan.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Hashes zijn identiek; bekeken processor-ID is naamafhankelijk.
- **Historische verwachting (then, v6):** Bestands-IDs mogen verschillen; registreer één inhoudelijke bronversie en geen twee onafhankelijke bevestigingen.
- **T (GTH-v1):** Behoud één onderliggende bronversie met meerdere aanvoerroutes; geen onafhankelijk bewijs uit bestands- of kanaalaantal. Inhoudelijke deelcontroles blijven nodig.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Blijft de semantische bronidentiteit duidelijk ondanks twee bestandsrecords?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P07 — Dezelfde bestandsnaam met gewijzigde wetszin

**Route:** upload · **Prioriteit:** P1 · **Bronnen:** S-UPLOAD32, M-UPLOAD · **scenario_input_sha256:** `5b5dca8ebee9af45…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** zorgvuldigheidsbeginsel
- **definitie:** plicht om alleen relevante feiten te onderzoeken
- **context:** Awb / Nederlands bestuursrecht
- **Gegeven:** Gebruik eerst originele upload; bied daarna de gemuteerde kopie met dezelfde basename aan. Dit is testmanipulatie, geen wetswijziging.
- **Wanneer:** Controleer duplicate-handling, inhoudshash en eventuele eerdere reviewbinding.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-UPLOAD32** · bestaand lokaal uploadbestand (echt, zonder eigen herkomst)

- pakketpad: `bronfixtures/meegegeven-awb-artikel-3-2.txt` · sha256 `73a64ab39bd2c2120adf13d323481153deed88b0a5f38b9e99d494ad0e5b9be0`
- bronversie: onbekend (null)
- herkomst (geen hyperlink): `/Users/chrislehnen/Projecten/Wetsanalyse/test-data/awb-artikel-3-2.txt`
- locators (manifest): wetszin onder beschrijvende kop
- **beschrijvende kop (geen wettekst)** — letterlijk:

> Artikel 3:2 Algemene wet bestuursrecht - Zorgvuldigheidsbeginsel

- **wetszin onder beschrijvende kop** — letterlijk:

> Bij de voorbereiding van een besluit vergaart het bestuursorgaan de nodige kennis omtrent de relevante feiten en de af te wegen belangen.

**M-UPLOAD** · SYNTHETISCHE MUTANT — bewust gewijzigde testkopie, geen echte revisie — **SYNTHETISCH (mutant/testconstructie)**

- pakketpad: `bronfixtures/mutanten/meegegeven-awb-artikel-3-2.txt` · sha256 `2a12e4a4b9fab6efe364f59e4547e2bb41034395410fe66e23ec30031f3b34e4`
- bronversie: TEST-MUTATIE, geen wetswijziging
- herkomst (geen hyperlink): `S-UPLOAD32`
- locators (manifest): artikeltekst
- **artikeltekst (GEMUTEERD)** — letterlijk:

> Bij de voorbereiding van een besluit vergaart het bestuursorgaan de nodige kennis omtrent de relevante feiten .

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Mutant verwijdert de af te wegen belangen; naamgelijkheid bewijst geen inhoudsgelijkheid.
- **Historische verwachting (then, v6):** Meld nieuwe/afwijkende inhoud of expliciete afwijzing van vervanging; nooit stil oude review voor nieuwe inhoud laten gelden.
- **T (GTH-v1):** Nieuwe inhoud bij dezelfde naam: oude review is niet actueel; gewijzigde wetszin vergelijken met de werkelijke bron, eventuele betekenisstrijd expliciet melden.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Wordt de cumulatieve norm onterecht beperkt?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P08 — RAG haalt het juiste beleidsregellid op

**Route:** RAG · **Prioriteit:** P1 · **Bronnen:** S-AWB13 · **scenario_input_sha256:** `4b79280c329c7106…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** beleidsregel
- **definitie:** bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, over belangenafweging, feitenvaststelling of uitleg van wettelijke voorschriften bij het gebruik van een bestuursbevoegdheid
- **context:** Awb / Nederlands bestuursrecht
- **Gegeven:** Indexeer S-AWB13; gebruik gecontroleerde retrieval R-BELEID.
- **Wanneer:** Beoordeel de vaste definitie en volg lid 4 door prompt en bewijsregistratie.
- **Retrievalrecept R-BELEID** — SYNTHETISCHE rangorde/score — geen echte retrievalrun (retrieval-fixtures-v1.json: synthetic_ranking=true, live_retrieval_executed=false)
  - rangorde (synthetisch): AWB13-L4=0.88
  - top_k=5, min_score=0.3, verwacht teruggegeven: AWB13-L4

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-AWB13** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/awb-1-3-20260815.txt` · sha256 `7be6c298370590a6ca51e82d9f6e9f066274e86adc3051037748beb2078e3ec8`
- bronversie: 2026-08-15
- link: <https://wetten.overheid.nl/BWBR0005537/2026-08-15/0?g=2026-09-14&z=2026-09-14#Hoofdstuk1_Titeldeel1.1_Artikel1:3>
- locators (manifest): artikel 1:3 lid 1; artikel 1:3 lid 2; artikel 1:3 lid 3; artikel 1:3 lid 4
- **artikel 1:3 lid 1** — letterlijk:

> Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

- **artikel 1:3 lid 2** — letterlijk:

> Onder beschikking wordt verstaan: een besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan.

- **artikel 1:3 lid 3** — letterlijk:

> Onder aanvraag wordt verstaan: een verzoek van een belanghebbende, een besluit te nemen.

- **artikel 1:3 lid 4** — letterlijk:

> Onder beleidsregel wordt verstaan: een bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, omtrent de afweging van belangen, de vaststelling van feiten of de uitleg van wettelijke voorschriften bij het gebruik van een bevoegdheid van een bestuursorgaan.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Steun in volledig lid 4; algemene regel is niet hetzelfde als algemeen verbindend voorschrift.
- **Historische verwachting (then, v6):** Alle kenmerken en uitsluiting blijven controleerbaar; retrievalscore vervangt review niet.
- **T (GTH-v1):** Voldoet mogelijk na positieve onderbouwde bronbasis, betekenissteun en verwijskwaliteit voor de concrete claim. De casus is nog niet deskundig vastgesteld of uitgevoerd; een eerder verplicht menselijk voorafgaand CON-02-oordeel is vervangen door de expliciete AI-toestemming.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Is de parafrase van lid 4 inhoudelijk equivalent?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P09 — Hoge RAG-score met verkeerd lid

**Route:** RAG · **Prioriteit:** P1 · **Bronnen:** S-AWB13 · **scenario_input_sha256:** `7d2e2ff691e4823b…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** beleidsregel
- **definitie:** algemeen verbindend voorschrift van een bestuursorgaan
- **context:** Awb / Nederlands bestuursrecht
- **Gegeven:** Retrieval R-VERKEERD-LID geeft alleen besluit/lid 1 met score 0.99.
- **Wanneer:** Beoordeel bronsteun voor beleidsregel.
- **Retrievalrecept R-VERKEERD-LID** — SYNTHETISCHE rangorde/score — geen echte retrievalrun (retrieval-fixtures-v1.json: synthetic_ranking=true, live_retrieval_executed=false)
  - rangorde (synthetisch): AWB13-L1=0.99
  - top_k=5, min_score=0.3, verwacht teruggegeven: AWB13-L1

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-AWB13** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/awb-1-3-20260815.txt` · sha256 `7be6c298370590a6ca51e82d9f6e9f066274e86adc3051037748beb2078e3ec8`
- bronversie: 2026-08-15
- link: <https://wetten.overheid.nl/BWBR0005537/2026-08-15/0?g=2026-09-14&z=2026-09-14#Hoofdstuk1_Titeldeel1.1_Artikel1:3>
- locators (manifest): artikel 1:3 lid 1; artikel 1:3 lid 2; artikel 1:3 lid 3; artikel 1:3 lid 4
- **artikel 1:3 lid 1** — letterlijk:

> Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

- **artikel 1:3 lid 2** — letterlijk:

> Onder beschikking wordt verstaan: een besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan.

- **artikel 1:3 lid 3** — letterlijk:

> Onder aanvraag wordt verstaan: een verzoek van een belanghebbende, een besluit te nemen.

- **artikel 1:3 lid 4** — letterlijk:

> Onder beleidsregel wordt verstaan: een bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, omtrent de afweging van belangen, de vaststelling van feiten of de uitleg van wettelijke voorschriften bij het gebruik van een bevoegdheid van een bestuursorgaan.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Lid 1 definieert besluit; lid 4 sluit algemeen verbindend voorschrift expliciet uit.
- **Historische verwachting (then, v6):** Geen inhoudelijke goedkeuring op score of alleen artikelnummer; markeer verkeerde passage en ontbrekend lid 4.
- **T (GTH-v1):** Geen pass op hoge score/verkeerd lid. De aangeleverde passage draagt de gewenste betekenis niet; ontbrekend juiste lid en aantoonbare betekenisverwisseling afzonderlijk melden.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Welke passage is werkelijk gebruikt, en waaruit blijkt de inhoudelijke tegenspraak?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: een retrievalscore (synthetisch 0.99) is geen regelcijfer en geen passagebewijs; het regeloordeel volgt uit de passage, niet uit de score.
- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P10 — Dierenuitzondering aanwezig in corpus maar buiten top vijf

**Route:** RAG · **Prioriteit:** P1 · **Bronnen:** S-AWB13, S-BW3 · **scenario_input_sha256:** `ea56a44e6382e648…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** zaak
- **definitie:** voor menselijke beheersing vatbaar stoffelijk object, waaronder een dier
- **context:** BW Boek 3 / Nederlands vermogensrecht
- **Gegeven:** Gebruik R-DIER-BUITEN-TOP5; art. 2a staat als kandidaat op rang 6 en 7.
- **Wanneer:** Laat top_k=5 ophalen en beoordeel de vaste definitie.
- **Retrievalrecept R-DIER-BUITEN-TOP5** — SYNTHETISCHE rangorde/score — geen echte retrievalrun (retrieval-fixtures-v1.json: synthetic_ranking=true, live_retrieval_executed=false)
  - rangorde (synthetisch): BW3-A2=0.99, BW3-A1=0.9, AWB13-L1=0.86, AWB13-L2=0.8, AWB13-L3=0.75, BW3-A2A-L1=0.74, BW3-A2A-L2=0.73
  - top_k=5, min_score=0.3, verwacht teruggegeven: BW3-A2, BW3-A1, AWB13-L1, AWB13-L2, AWB13-L3

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-AWB13** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/awb-1-3-20260815.txt` · sha256 `7be6c298370590a6ca51e82d9f6e9f066274e86adc3051037748beb2078e3ec8`
- bronversie: 2026-08-15
- link: <https://wetten.overheid.nl/BWBR0005537/2026-08-15/0?g=2026-09-14&z=2026-09-14#Hoofdstuk1_Titeldeel1.1_Artikel1:3>
- locators (manifest): artikel 1:3 lid 1; artikel 1:3 lid 2; artikel 1:3 lid 3; artikel 1:3 lid 4
- **artikel 1:3 lid 1** — letterlijk:

> Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

- **artikel 1:3 lid 2** — letterlijk:

> Onder beschikking wordt verstaan: een besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan.

- **artikel 1:3 lid 3** — letterlijk:

> Onder aanvraag wordt verstaan: een verzoek van een belanghebbende, een besluit te nemen.

- **artikel 1:3 lid 4** — letterlijk:

> Onder beleidsregel wordt verstaan: een bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, omtrent de afweging van belangen, de vaststelling van feiten of de uitleg van wettelijke voorschriften bij het gebruik van een bevoegdheid van een bestuursorgaan.

**S-BW3** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/bw3-1-2-2a-20250701.txt` · sha256 `cc46ab1cc9b667db076e9003a114b092a16a566c65aa62e256012165378d32ba`
- bronversie: 2025-07-01
- link: <https://wetten.overheid.nl/BWBR0005291/2025-07-01/0?g=2026-09-14&z=2026-09-14#Boek3_Titeldeel1_Afdeling1_Artikel2>
- locators (manifest): artikel 1; artikel 2; artikel 2a lid 1; artikel 2a lid 2
- **artikel 1** — letterlijk:

> Goederen zijn alle zaken en alle vermogensrechten.

- **artikel 2** — letterlijk:

> Zaken zijn de voor menselijke beheersing vatbare stoffelijke objecten.

- **artikel 2a lid 1** — letterlijk:

> Dieren zijn geen zaken.

- **artikel 2a lid 2** — letterlijk:

> Bepalingen met betrekking tot zaken zijn op dieren van toepassing, met in achtneming van de op wettelijke voorschriften en regels van ongeschreven recht gegronde beperkingen, verplichtingen en rechtsbeginselen, alsmede de openbare orde en de goede zeden.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Volledige corpus bevat Dieren zijn geen zaken; top vijf mist deze beperking.
- **Historische verwachting (then, v6):** Bewaar werkelijk ontvangen chunks; claim niet dat art. 2a is meegenomen omdat het is geïndexeerd. Onvoldoende/tegenstrijdig bewijs moet review uitlokken.
- **T (GTH-v1):** Geen volledige betekenissteun claimen uit corpusaanwezigheid: noodzakelijke uitzondering ontbreekt in ontvangen passages. Nog te beoordelen voor onvolledige dekking; een feitelijk vastgestelde strijd apart afkeuren.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Herkent men dat de gekozen bronset onvoldoende is om inclusief dieren te bevestigen?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: ontbrekende relevante passage buiten top-5 mag niet leiden tot een positief oordeel door hogere 'dekking' te suggereren; 'nog te beoordelen' of 'voldoet niet' met onderbouwing, nooit stil pass.
- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P11 — Zelfde dierencasus met volledige relevante retrieval ★ eerste zes

**Route:** RAG · **Prioriteit:** P1 · **Bronnen:** S-BW3 · **scenario_input_sha256:** `fee5ce84b340f55f…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** zaak
- **definitie:** voor menselijke beheersing vatbaar stoffelijk object, waaronder een dier
- **context:** BW Boek 3 / Nederlands vermogensrecht
- **Gegeven:** Gebruik R-DIER-VOLLEDIG met art. 2 en beide leden van 2a.
- **Wanneer:** Beoordeel dezelfde definitie als P10.
- **Retrievalrecept R-DIER-VOLLEDIG** — SYNTHETISCHE rangorde/score — geen echte retrievalrun (retrieval-fixtures-v1.json: synthetic_ranking=true, live_retrieval_executed=false)
  - rangorde (synthetisch): BW3-A2=0.99, BW3-A2A-L1=0.96, BW3-A2A-L2=0.95
  - top_k=5, min_score=0.3, verwacht teruggegeven: BW3-A2, BW3-A2A-L1, BW3-A2A-L2

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-BW3** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/bw3-1-2-2a-20250701.txt` · sha256 `cc46ab1cc9b667db076e9003a114b092a16a566c65aa62e256012165378d32ba`
- bronversie: 2025-07-01
- link: <https://wetten.overheid.nl/BWBR0005291/2025-07-01/0?g=2026-09-14&z=2026-09-14#Boek3_Titeldeel1_Afdeling1_Artikel2>
- locators (manifest): artikel 1; artikel 2; artikel 2a lid 1; artikel 2a lid 2
- **artikel 1** — letterlijk:

> Goederen zijn alle zaken en alle vermogensrechten.

- **artikel 2** — letterlijk:

> Zaken zijn de voor menselijke beheersing vatbare stoffelijke objecten.

- **artikel 2a lid 1** — letterlijk:

> Dieren zijn geen zaken.

- **artikel 2a lid 2** — letterlijk:

> Bepalingen met betrekking tot zaken zijn op dieren van toepassing, met in achtneming van de op wettelijke voorschriften en regels van ongeschreven recht gegronde beperkingen, verplichtingen en rechtsbeginselen, alsmede de openbare orde en de goede zeden.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Art. 2a lid 1 sluit dieren uit; lid 2 regelt toepasselijkheid van bepalingen met beperkingen.
- **Historische verwachting (then, v6):** Signaleer expliciete strijd met art. 2a lid 1; lid 2 maakt dieren niet alsnog zaken.
- **T (GTH-v1):** Betekenissteun voldoet niet: de volledige bron sluit dieren uit als zaken; de aanvullende toepasselijkheidsbepaling heft die uitsluiting niet op.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld. Concreet te behouden/herstellen: Betekenissteun voldoet niet: de volledige bron sluit dieren uit als zaken; de aanvullende toepasselijkheidsbepaling heft die uitsluiting niet op.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Bevestigt de deskundige het onderscheid kwalificatie versus toepasselijke bepalingen?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P12 — Begripsnaam staat niet letterlijk in de ondersteunende wetszin

**Route:** upload · **Prioriteit:** P1 · **Bronnen:** S-AWB32 · **scenario_input_sha256:** `74724c47b92de324…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** zorgvuldigheidsbeginsel
- **definitie:** plicht van het bestuursorgaan om bij besluitvoorbereiding kennis over relevante feiten en af te wegen belangen te vergaren
- **context:** Awb / Nederlands bestuursrecht
- **Gegeven:** Upload S-AWB32 met kop Artikel 3:2; het woord zorgvuldigheidsbeginsel komt er niet in voor.
- **Wanneer:** Inspecteer letterlijke snippetselectie en werkelijk aan generatie/validatie doorgegeven tekst.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-AWB32** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/awb-3-2-20260815.txt` · sha256 `ad520ff75fb2732204b93c2307e0b1806a400eedfd427cd4c19425e41bbdef97`
- bronversie: 2026-08-15
- link: <https://wetten.overheid.nl/jci1.3:c:BWBR0005537&hoofdstuk=3&afdeling=3.2&artikel=3:2&z=2026-08-15&g=2026-08-15>
- locators (manifest): artikel 3:2
- **artikel 3:2** — letterlijk:

> Bij de voorbereiding van een besluit vergaart het bestuursorgaan de nodige kennis omtrent de relevante feiten en de af te wegen belangen.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Relevante wetszin bestaat, maar de term ontbreekt letterlijk. Dit onderscheidt vindbaarheid van normsteun.
- **Historische verwachting (then, v6):** Rapporteer werkelijk wel/geen passage; geen bronbewijs claimen op basis van alleen een upload of documentaantal.
- **T (GTH-v1):** Invoer-/transportverlies afzonderlijk lokaliseren; ontvangende stap heeft onvoldoende bewijs en mag niet positief oordelen. Dit is geen bewijs dat de generator de betekenis heeft geschonden.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Herstel de aantoonbare invoer-/transportonderbreking; vraag niet om een nieuwe betekenis of cosmetische tekstwijziging. Hertoets met teruggevonden echte brongegevens.
- **Deskundigenvraag:** Is de afgeleide omschrijving passend, ook zonder letterlijke naam in de bron?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P13 — Artikel/lid en chunk-ID door normalisatie en opslag

**Route:** RAG · **Prioriteit:** P1 · **Bronnen:** S-AWB13 · **scenario_input_sha256:** `caa28b43ad23dee6…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** aanvraag
- **definitie:** verzoek van een belanghebbende om een besluit te nemen
- **context:** Awb / Nederlands bestuursrecht
- **Gegeven:** Gebruik een echte geïndexeerde lid-3-passage met werkelijke document-ID, chunk-ID en lidmetadata. Bronversie/hash zijn geen aangetoond ingestcontract: lever deze afzonderlijk via de voorgestelde testadapter aan en leg dat als nieuwe testvoorwaarde vast.
- **Wanneer:** Leg raw retrieval, prompt, provenance, opslag, herladen en export naast elkaar.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-AWB13** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/awb-1-3-20260815.txt` · sha256 `7be6c298370590a6ca51e82d9f6e9f066274e86adc3051037748beb2078e3ec8`
- bronversie: 2026-08-15
- link: <https://wetten.overheid.nl/BWBR0005537/2026-08-15/0?g=2026-09-14&z=2026-09-14#Hoofdstuk1_Titeldeel1.1_Artikel1:3>
- locators (manifest): artikel 1:3 lid 1; artikel 1:3 lid 2; artikel 1:3 lid 3; artikel 1:3 lid 4
- **artikel 1:3 lid 1** — letterlijk:

> Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

- **artikel 1:3 lid 2** — letterlijk:

> Onder beschikking wordt verstaan: een besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan.

- **artikel 1:3 lid 3** — letterlijk:

> Onder aanvraag wordt verstaan: een verzoek van een belanghebbende, een besluit te nemen.

- **artikel 1:3 lid 4** — letterlijk:

> Onder beleidsregel wordt verstaan: een bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, omtrent de afweging van belangen, de vaststelling van feiten of de uitleg van wettelijke voorschriften bij het gebruik van een bevoegdheid van een bestuursorgaan.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Codebijlage toont document-/chunk-ID en lid in raw retrieval en verlies daarvan in de provenanceprojectie. Bronversie/hash ontbreken als expliciet ingestcontract; er kan pas transportverlies worden getest nadat ze aantoonbaar zijn aangeleverd. Latere opslag-/exportstappen zijn nog niet getest.
- **Historische verwachting (then, v6):** Dezelfde gekozen passage en bronversie moeten terugvindbaar blijven; noteer exact eerste verliespunt.
- **T (GTH-v1):** Invoer-/transportverlies afzonderlijk lokaliseren; ontvangende stap heeft onvoldoende bewijs en mag niet positief oordelen. Dit is geen bewijs dat de generator de betekenis heeft geschonden.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Herstel de aantoonbare invoer-/transportonderbreking; vraag niet om een nieuwe betekenis of cosmetische tekstwijziging. Hertoets met teruggevonden echte brongegevens.
- **Deskundigenvraag:** Kan een andere reviewer exact dezelfde passage terugvinden?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P14 — Alleen een reviewed/high-wikipagina

**Route:** LLM-WIKI · **Prioriteit:** P1 · **Bronnen:** S-WIKI · **scenario_input_sha256:** `84c8d56cdb14d747…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** LLM-wiki
- **definitie:** kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling onveranderlijke bronnen
- **context:** Karpathy LLM-wiki-patroon
- **Gegeven:** Upload alleen de echte begrippenpagina, zonder bronpagina of raw.
- **Wanneer:** Beoordeel bewijs en frontmatter.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-WIKI** · afgeleide wikipagina (echt, lokaal)

- pakketpad: `bronfixtures/wiki/LLM-wiki.md` · sha256 `4704009b44d40c13904afd8018c4f35e9c1257c3f05c11291b8e157af764d966`
- bronversie: last_updated 2026-08-03
- herkomst (geen hyperlink): `/Users/chrislehnen/Documents/Claude/Projects/Wiki Karpaty style/llm-wiki-kennis/wiki/begrippen/LLM-wiki.md`
- locators (manifest): frontmatter; Definitie
- **frontmatter: confidence** — letterlijk:

> confidence: high

- **frontmatter: lifecycle** — letterlijk:

> lifecycle: reviewed

- **Definitie** — letterlijk:

> kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling onveranderlijke bronnen

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** De pagina noemt twee sources; die zijn niet automatisch opgehaald door deze upload.
- **Historische verwachting (then, v6):** Reviewed/high gelden als beweringen van dit bestand; geen daadwerkelijke onafhankelijke review of volledig primaire keten afleiden.
- **T (GTH-v1):** Nog te beoordelen: reviewed/high/verified-verklaring zonder bewijs is geen inhoudelijk oordeel of menselijke review. AI mag pas positief oordelen met concrete gecontroleerde onderbouwing.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Welke concrete claim kan worden vastgesteld zonder de onderliggende bronnen?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P15 — Wiki met navolgbare raw-steun voor afgebakende definitieclaim

**Route:** LLM-WIKI · **Prioriteit:** P1 · **Bronnen:** S-WIKI, S-WIKISOURCE, S-RAW, S-RAWREGISTER · **scenario_input_sha256:** `07ae63a613a03cd8…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** LLM-wiki
- **definitie:** kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling onveranderlijke bronnen
- **context:** Karpathy LLM-wiki-patroon
- **Gegeven:** Bied pagina, bronpagina, raw en register-uittreksel samen aan; controleer raw-hash en Architecture/Core idea.
- **Wanneer:** Maak voor alleen deze definitie een claim-passagekoppeling.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-WIKI** · afgeleide wikipagina (echt, lokaal)

- pakketpad: `bronfixtures/wiki/LLM-wiki.md` · sha256 `4704009b44d40c13904afd8018c4f35e9c1257c3f05c11291b8e157af764d966`
- bronversie: last_updated 2026-08-03
- herkomst (geen hyperlink): `/Users/chrislehnen/Documents/Claude/Projects/Wiki Karpaty style/llm-wiki-kennis/wiki/begrippen/LLM-wiki.md`
- locators (manifest): frontmatter; Definitie
- **frontmatter: confidence** — letterlijk:

> confidence: high

- **frontmatter: lifecycle** — letterlijk:

> lifecycle: reviewed

- **Definitie** — letterlijk:

> kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling onveranderlijke bronnen

**S-WIKISOURCE** · afgeleide bronpagina (echt, lokaal)

- pakketpad: `bronfixtures/wiki/karpathy-llm-wiki-gist.md` · sha256 `b918678627ab4c9027fbcd9869f7db6dfe3c7d567c8340a0c08bdfff682a7253`
- bronversie: gedeclareerd last_updated 2026-08-03
- herkomst (geen hyperlink): `/Users/chrislehnen/Documents/Claude/Projects/Wiki Karpaty style/llm-wiki-kennis/wiki/sources/karpathy-llm-wiki-gist.md`
- locators (manifest): samenvatting; verwijzingen naar raw
- **Samenvatting** — letterlijk:

> Het oorspronkelijke "idea file" van het [[LLM-Wiki-patroon]]: een taalmodel bouwt en onderhoudt
> incrementeel een persistente markdown-wiki bovenop onveranderlijke bronnen, als alternatief voor
> RAG-herafleiding per vraag. Beschrijft drie lagen, drie operaties, twee navigatiebestanden,
> optionele tooling en de rolverdeling mens/model. Bewust abstract: de agent van de lezer bouwt de
> specifieke variant.

**S-RAW** · historische primaire capture (echt, lokaal)

- pakketpad: `bronfixtures/raw/2026-07-08-karpathy-llm-wiki-gist.md` · sha256 `dc3efe98ae62f23dd08acad13aba2e95287beb20b6bec2f4af0423557fe37401`
- bronversie: capture 2026-07-08
- herkomst (geen hyperlink): `/Users/chrislehnen/Documents/Claude/Projects/Wiki Karpaty style/llm-wiki-kennis/raw/2026-07-08-karpathy-llm-wiki-gist.md`
- locators (manifest): The core idea; Architecture / Raw sources
- **The core idea (eerste alinea)** — letterlijk:

> Most people's experience with LLMs and documents looks like RAG: you upload a collection of files, the LLM retrieves relevant chunks at query time, and generates an answer. This works, but the LLM is rediscovering knowledge from scratch on every question. There's no accumulation. Ask a subtle question that requires synthesizing five documents, and the LLM has to find and piece together the relevant fragments every time. Nothing is built up. NotebookLM, ChatGPT file uploads, and most RAG systems work this way.

- **Architecture / Raw sources** — letterlijk:

> **Raw sources** — your curated collection of source documents. Articles, papers, images, data files. These are immutable — the LLM reads from them but never modifies them. This is your source of truth.

**S-RAWREGISTER** · uittreksel uit lokaal bronregister (echt, gedeeltelijk)

- pakketpad: `bronfixtures/raw/register-uittreksel.md` · sha256 `e7500aa7bad7c12ec056f8c6bb356e14bb85d9946bc91dde10224144e3fd0f33`
- bronversie: onbekend (null)
- herkomst (geen hyperlink): `/Users/chrislehnen/Documents/Claude/Projects/Wiki Karpaty style/llm-wiki-kennis/raw/BRONNEN.md`
- locators (manifest): rij 2026-07-08-karpathy-llm-wiki-gist.md
- **rij 2026-07-08-karpathy-llm-wiki-gist.md** — letterlijk:

> | 2026-07-08-karpathy-llm-wiki-gist.md | https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f | 2026-07-08 | dc3efe98ae62f23dd08acad13aba2e95287beb20b6bec2f4af0423557fe37401 |

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Raw beschrijft persistente interlinked markdown-wiki, LLM-onderhoud en immutable raw sources. De tweede pluginbron en andere claims zijn hier niet geverifieerd.
- **Historische verwachting (then, v6):** Bewaar afgeleide/ruwe bronrol en capturedatum; markeer geen totale wikivalidatie. Overige bronnen in pagina blijven buiten gecontroleerde scope.
- **T (GTH-v1):** Voldoet mogelijk na positieve onderbouwde bronbasis, betekenissteun en verwijskwaliteit voor de concrete claim. De casus is nog niet deskundig vastgesteld of uitgevoerd; een eerder verplicht menselijk voorafgaand CON-02-oordeel is vervangen door de expliciete AI-toestemming.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Zijn de vier kenmerken voldoende ondersteund en correct afgebakend tot het patroon?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P16 — Wiki wijzigt betekenis maar behoudt reviewed-label ★ eerste zes

**Route:** LLM-WIKI · **Prioriteit:** P1 · **Bronnen:** M-WIKI, S-RAW · **scenario_input_sha256:** `71f98311ead72bdd…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** LLM-wiki
- **definitie:** kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling bronnen die het taalmodel tijdens onderhoud herschrijft
- **context:** Karpathy LLM-wiki-patroon
- **Gegeven:** Gebruik alleen de duidelijk als mutant geregistreerde wikikopie naast originele raw.
- **Wanneer:** Vergelijk gewijzigde definitie met Architecture / Raw sources.

### 2. Bronnen — exacte inhoud, locator, versie, link

**M-WIKI** · SYNTHETISCHE MUTANT — bewust gewijzigde testkopie, geen echte revisie — **SYNTHETISCH (mutant/testconstructie)**

- pakketpad: `bronfixtures/mutanten/LLM-wiki-onjuist.md` · sha256 `05b9d41bdfb27160c30724616e0ba44370973343f4fbcfd14af45fcad7e471dd`
- bronversie: TEST-MUTATIE, geen echte wiki-revisie
- herkomst (geen hyperlink): `S-WIKI`
- locators (manifest): Definitie
- **frontmatter: confidence** — letterlijk:

> confidence: high

- **frontmatter: lifecycle** — letterlijk:

> lifecycle: reviewed

- **Definitie** — letterlijk:

> kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling bronnen die het taalmodel tijdens onderhoud herschrijft

**S-RAW** · historische primaire capture (echt, lokaal)

- pakketpad: `bronfixtures/raw/2026-07-08-karpathy-llm-wiki-gist.md` · sha256 `dc3efe98ae62f23dd08acad13aba2e95287beb20b6bec2f4af0423557fe37401`
- bronversie: capture 2026-07-08
- herkomst (geen hyperlink): `/Users/chrislehnen/Documents/Claude/Projects/Wiki Karpaty style/llm-wiki-kennis/raw/2026-07-08-karpathy-llm-wiki-gist.md`
- locators (manifest): The core idea; Architecture / Raw sources
- **The core idea (eerste alinea)** — letterlijk:

> Most people's experience with LLMs and documents looks like RAG: you upload a collection of files, the LLM retrieves relevant chunks at query time, and generates an answer. This works, but the LLM is rediscovering knowledge from scratch on every question. There's no accumulation. Ask a subtle question that requires synthesizing five documents, and the LLM has to find and piece together the relevant fragments every time. Nothing is built up. NotebookLM, ChatGPT file uploads, and most RAG systems work this way.

- **Architecture / Raw sources** — letterlijk:

> **Raw sources** — your curated collection of source documents. Articles, papers, images, data files. These are immutable — the LLM reads from them but never modifies them. This is your source of truth.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Raw zegt immutable en never modifies; mutant zegt herschrijven.
- **Historische verwachting (then, v6):** Detecteer inhoudelijke tegenspraak ondanks ongewijzigde reviewed/high-frontmatter.
- **T (GTH-v1):** Betekenissteun voldoet niet: wiki keert onveranderlijke raw-bronnen om naar herschrijfbare bronnen; reviewed-label verandert dit niet.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld. Concreet te behouden/herstellen: Betekenissteun voldoet niet: wiki keert onveranderlijke raw-bronnen om naar herschrijfbare bronnen; reviewed-label verandert dit niet.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Welk kenmerk is omgekeerd, en waarom is oude frontmatter geen actuele review?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P17 — Raw-bestand gewijzigd zonder registerhash te actualiseren

**Route:** LLM-WIKI · **Prioriteit:** P1 · **Bronnen:** S-WIKI, M-RAW, S-RAWREGISTER · **scenario_input_sha256:** `13cfa284cfeb79ef…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** LLM-wiki
- **definitie:** kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling onveranderlijke bronnen
- **context:** Karpathy LLM-wiki-patroon
- **Gegeven:** Gebruik M-RAW met de verwachte registerhash van S-RAW.
- **Wanneer:** Herbereken hash vóór claimbeoordeling.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-WIKI** · afgeleide wikipagina (echt, lokaal)

- pakketpad: `bronfixtures/wiki/LLM-wiki.md` · sha256 `4704009b44d40c13904afd8018c4f35e9c1257c3f05c11291b8e157af764d966`
- bronversie: last_updated 2026-08-03
- herkomst (geen hyperlink): `/Users/chrislehnen/Documents/Claude/Projects/Wiki Karpaty style/llm-wiki-kennis/wiki/begrippen/LLM-wiki.md`
- locators (manifest): frontmatter; Definitie
- **frontmatter: confidence** — letterlijk:

> confidence: high

- **frontmatter: lifecycle** — letterlijk:

> lifecycle: reviewed

- **Definitie** — letterlijk:

> kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling onveranderlijke bronnen

**M-RAW** · SYNTHETISCHE MUTANT — bewust gewijzigde testkopie, geen echte revisie — **SYNTHETISCH (mutant/testconstructie)**

- pakketpad: `bronfixtures/mutanten/karpathy-raw-gewijzigd.md` · sha256 `addb6e3a4034d12ab178044bef2bec643b0d8f17a2a5487fafdbede31355e3df`
- bronversie: TEST-MUTATIE, geen auteursrevisie
- herkomst (geen hyperlink): `S-RAW`
- locators (manifest): Architecture / Raw sources
- **Architecture / Raw sources (GEMUTEERD)** — letterlijk:

> **Raw sources** — your curated collection of source documents. Articles, papers, images, data files. These are mutable — the LLM reads from them but never modifies them. This is your source of truth.

**S-RAWREGISTER** · uittreksel uit lokaal bronregister (echt, gedeeltelijk)

- pakketpad: `bronfixtures/raw/register-uittreksel.md` · sha256 `e7500aa7bad7c12ec056f8c6bb356e14bb85d9946bc91dde10224144e3fd0f33`
- bronversie: onbekend (null)
- herkomst (geen hyperlink): `/Users/chrislehnen/Documents/Claude/Projects/Wiki Karpaty style/llm-wiki-kennis/raw/BRONNEN.md`
- locators (manifest): rij 2026-07-08-karpathy-llm-wiki-gist.md
- **rij 2026-07-08-karpathy-llm-wiki-gist.md** — letterlijk:

> | 2026-07-08-karpathy-llm-wiki-gist.md | https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f | 2026-07-08 | dc3efe98ae62f23dd08acad13aba2e95287beb20b6bec2f4af0423557fe37401 |

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** immutable is in testkopie mutable geworden; hash verschilt aantoonbaar.
- **Historische verwachting (then, v6):** Meld integriteitsafwijking; verwijs niet stil naar oorspronkelijke capture als bewijs voor andere bytes.
- **T (GTH-v1):** Bronintegriteit wijkt aantoonbaar af van registerhash; oude binding ongeldig. Geen herkomst/gezag afleiden uit hash alleen, geen nieuwe bytes als oude capture behandelen.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Welk bronexemplaar is beoordeeld en kan dat nog aan het register worden gebonden?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P18 — Niet-aangeleverde wiki-bron niet als gelezen registreren

**Route:** LLM-WIKI · **Prioriteit:** P2 · **Bronnen:** S-WIKI, S-RAW · **scenario_input_sha256:** `3a8bf6bef1a148c9…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** LLM-wiki
- **definitie:** kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling onveranderlijke bronnen
- **context:** Karpathy LLM-wiki-patroon
- **Gegeven:** Pagina noemt Karpathy en praneybehl; alleen Karpathy-raw is meegeleverd.
- **Wanneer:** Controleer sources-resolutie en gebruikte bewijsclaims.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-WIKI** · afgeleide wikipagina (echt, lokaal)

- pakketpad: `bronfixtures/wiki/LLM-wiki.md` · sha256 `4704009b44d40c13904afd8018c4f35e9c1257c3f05c11291b8e157af764d966`
- bronversie: last_updated 2026-08-03
- herkomst (geen hyperlink): `/Users/chrislehnen/Documents/Claude/Projects/Wiki Karpaty style/llm-wiki-kennis/wiki/begrippen/LLM-wiki.md`
- locators (manifest): frontmatter; Definitie
- **frontmatter: confidence** — letterlijk:

> confidence: high

- **frontmatter: lifecycle** — letterlijk:

> lifecycle: reviewed

- **Definitie** — letterlijk:

> kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling onveranderlijke bronnen

**S-RAW** · historische primaire capture (echt, lokaal)

- pakketpad: `bronfixtures/raw/2026-07-08-karpathy-llm-wiki-gist.md` · sha256 `dc3efe98ae62f23dd08acad13aba2e95287beb20b6bec2f4af0423557fe37401`
- bronversie: capture 2026-07-08
- herkomst (geen hyperlink): `/Users/chrislehnen/Documents/Claude/Projects/Wiki Karpaty style/llm-wiki-kennis/raw/2026-07-08-karpathy-llm-wiki-gist.md`
- locators (manifest): The core idea; Architecture / Raw sources
- **The core idea (eerste alinea)** — letterlijk:

> Most people's experience with LLMs and documents looks like RAG: you upload a collection of files, the LLM retrieves relevant chunks at query time, and generates an answer. This works, but the LLM is rediscovering knowledge from scratch on every question. There's no accumulation. Ask a subtle question that requires synthesizing five documents, and the LLM has to find and piece together the relevant fragments every time. Nothing is built up. NotebookLM, ChatGPT file uploads, and most RAG systems work this way.

- **Architecture / Raw sources** — letterlijk:

> **Raw sources** — your curated collection of source documents. Articles, papers, images, data files. These are immutable — the LLM reads from them but never modifies them. This is your source of truth.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Een identifier in frontmatter is geen gelezen document. Het voorbeeld met 100 artikelen/400K woorden valt buiten deze onderbouwde claim.
- **Historische verwachting (then, v6):** Ontbrekende tweede bron blijft expliciet onopgelost; geen verzonnen passage/URL-inhoud. Afgebakende claim mag afzonderlijk worden beoordeeld met S-RAW.
- **T (GTH-v1):** Niet ontvangen tweede bron blijft niet gelezen/onbeoordeeld. Afgebakende claim met werkelijk beschikbare raw-bron kan wel afzonderlijk worden beoordeeld; geen totale wikivalidatie claimen.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Is duidelijk welke claims wél en niet door de beschikbare bron worden gedragen?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P19 — Beschikking omvat ook afwijzing

**Route:** wettekst · **Prioriteit:** P1 · **Bronnen:** S-AWB13 · **scenario_input_sha256:** `9585f71127918d20…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** beschikking
- **definitie:** besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan
- **context:** Awb / Nederlands bestuursrecht
- **Gegeven:** Gecontroleerde Awb-art. 1:3 lid 2 beschikbaar.
- **Wanneer:** Vergelijk definitie en expliciete randcasus afwijzing van een aanvraag om zo een besluit.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-AWB13** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/awb-1-3-20260815.txt` · sha256 `7be6c298370590a6ca51e82d9f6e9f066274e86adc3051037748beb2078e3ec8`
- bronversie: 2026-08-15
- link: <https://wetten.overheid.nl/BWBR0005537/2026-08-15/0?g=2026-09-14&z=2026-09-14#Hoofdstuk1_Titeldeel1.1_Artikel1:3>
- locators (manifest): artikel 1:3 lid 1; artikel 1:3 lid 2; artikel 1:3 lid 3; artikel 1:3 lid 4
- **artikel 1:3 lid 1** — letterlijk:

> Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

- **artikel 1:3 lid 2** — letterlijk:

> Onder beschikking wordt verstaan: een besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan.

- **artikel 1:3 lid 3** — letterlijk:

> Onder aanvraag wordt verstaan: een verzoek van een belanghebbende, een besluit te nemen.

- **artikel 1:3 lid 4** — letterlijk:

> Onder beleidsregel wordt verstaan: een bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, omtrent de afweging van belangen, de vaststelling van feiten of de uitleg van wettelijke voorschriften bij het gebruik van een bevoegdheid van een bestuursorgaan.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** De gekozen definitie volgt lid 2 inclusief de expliciete inclusie.
- **Historische verwachting (then, v6):** Behoud afwijzing in afbakening; niet alleen positieve/toewijzende besluiten accepteren.
- **T (GTH-v1):** Voldoet mogelijk na positieve onderbouwde bronbasis, betekenissteun en verwijskwaliteit voor de concrete claim. De casus is nog niet deskundig vastgesteld of uitgevoerd; een eerder verplicht menselijk voorafgaand CON-02-oordeel is vervangen door de expliciete AI-toestemming.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Klopt afbakening in het Awb-profiel, zonder ononderzochte praktijkuitzonderingen te verzinnen?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P20 — Aanvraag zonder belanghebbende-eis

**Route:** wettekst · **Prioriteit:** P1 · **Bronnen:** S-AWB13 · **scenario_input_sha256:** `73be814f056b13ff…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** aanvraag
- **definitie:** verzoek van een willekeurige persoon om een besluit te nemen
- **context:** Awb / Nederlands bestuursrecht
- **Gegeven:** Gecontroleerde Awb-art. 1:3 lid 3 beschikbaar.
- **Wanneer:** Beoordeel definitie en grenscasus verzoeker zonder belanghebbendheid.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-AWB13** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/awb-1-3-20260815.txt` · sha256 `7be6c298370590a6ca51e82d9f6e9f066274e86adc3051037748beb2078e3ec8`
- bronversie: 2026-08-15
- link: <https://wetten.overheid.nl/BWBR0005537/2026-08-15/0?g=2026-09-14&z=2026-09-14#Hoofdstuk1_Titeldeel1.1_Artikel1:3>
- locators (manifest): artikel 1:3 lid 1; artikel 1:3 lid 2; artikel 1:3 lid 3; artikel 1:3 lid 4
- **artikel 1:3 lid 1** — letterlijk:

> Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

- **artikel 1:3 lid 2** — letterlijk:

> Onder beschikking wordt verstaan: een besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan.

- **artikel 1:3 lid 3** — letterlijk:

> Onder aanvraag wordt verstaan: een verzoek van een belanghebbende, een besluit te nemen.

- **artikel 1:3 lid 4** — letterlijk:

> Onder beleidsregel wordt verstaan: een bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, omtrent de afweging van belangen, de vaststelling van feiten of de uitleg van wettelijke voorschriften bij het gebruik van een bevoegdheid van een bestuursorgaan.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Lid 3 noemt een belanghebbende, niet iedere willekeurige persoon.
- **Historische verwachting (then, v6):** Markeer verbreding van het wettelijke begrip; bepaal belanghebbendheid niet automatisch op fictieve persoonsgegevens.
- **T (GTH-v1):** Betekenissteun voldoet niet: belanghebbende-eis ontbreekt. Geen beoordeling van echte personen of fictieve persoonsgegevens nodig.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld. Concreet te behouden/herstellen: Betekenissteun voldoet niet: belanghebbende-eis ontbreekt. Geen beoordeling van echte personen of fictieve persoonsgegevens nodig.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Welke betekenisbeperking gaat verloren?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P21 — Goed is ruimer dan alleen stoffelijk object

**Route:** wettekst · **Prioriteit:** P1 · **Bronnen:** S-BW3 · **scenario_input_sha256:** `0f12d9e87b82773e…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** goed
- **definitie:** voor menselijke beheersing vatbaar stoffelijk object
- **context:** BW Boek 3 / Nederlands vermogensrecht
- **Gegeven:** Gebruik BW3-art. 1 en 2 naast elkaar.
- **Wanneer:** Vergelijk definitie en grenscasus vermogensrecht.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-BW3** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/bw3-1-2-2a-20250701.txt` · sha256 `cc46ab1cc9b667db076e9003a114b092a16a566c65aa62e256012165378d32ba`
- bronversie: 2025-07-01
- link: <https://wetten.overheid.nl/BWBR0005291/2025-07-01/0?g=2026-09-14&z=2026-09-14#Boek3_Titeldeel1_Afdeling1_Artikel2>
- locators (manifest): artikel 1; artikel 2; artikel 2a lid 1; artikel 2a lid 2
- **artikel 1** — letterlijk:

> Goederen zijn alle zaken en alle vermogensrechten.

- **artikel 2** — letterlijk:

> Zaken zijn de voor menselijke beheersing vatbare stoffelijke objecten.

- **artikel 2a lid 1** — letterlijk:

> Dieren zijn geen zaken.

- **artikel 2a lid 2** — letterlijk:

> Bepalingen met betrekking tot zaken zijn op dieren van toepassing, met in achtneming van de op wettelijke voorschriften en regels van ongeschreven recht gegronde beperkingen, verplichtingen en rechtsbeginselen, alsmede de openbare orde en de goede zeden.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Art. 1 omvat zaken én vermogensrechten; art. 2 definieert zaken.
- **Historische verwachting (then, v6):** Signaleer verwisseling van goed en zaak; behoud vermogensrechten in goederenbegrip.
- **T (GTH-v1):** Betekenissteun voldoet niet: goed is vernauwd tot zaak en laat vermogensrechten weg.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld. Concreet te behouden/herstellen: Betekenissteun voldoet niet: goed is vernauwd tot zaak en laat vermogensrechten weg.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Is de extensie door deze begripsverwisseling te beperkt?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P22 — Geen zaken betekent niet dat zakenbepalingen nooit gelden

**Route:** wettekst · **Prioriteit:** P1 · **Bronnen:** S-BW3 · **scenario_input_sha256:** `5b29f7bb529168a3…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** dier
- **definitie:** levend wezen waarop geen bepalingen met betrekking tot zaken van toepassing zijn
- **context:** BW Boek 3 / Nederlands vermogensrecht
- **Gegeven:** Gebruik beide leden van BW3-art. 2a; beoordeling beperkt tot de juridische toevoeging aan de definitie.
- **Wanneer:** Beoordeel de absolute uitsluiting.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-BW3** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/bw3-1-2-2a-20250701.txt` · sha256 `cc46ab1cc9b667db076e9003a114b092a16a566c65aa62e256012165378d32ba`
- bronversie: 2025-07-01
- link: <https://wetten.overheid.nl/BWBR0005291/2025-07-01/0?g=2026-09-14&z=2026-09-14#Boek3_Titeldeel1_Afdeling1_Artikel2>
- locators (manifest): artikel 1; artikel 2; artikel 2a lid 1; artikel 2a lid 2
- **artikel 1** — letterlijk:

> Goederen zijn alle zaken en alle vermogensrechten.

- **artikel 2** — letterlijk:

> Zaken zijn de voor menselijke beheersing vatbare stoffelijke objecten.

- **artikel 2a lid 1** — letterlijk:

> Dieren zijn geen zaken.

- **artikel 2a lid 2** — letterlijk:

> Bepalingen met betrekking tot zaken zijn op dieren van toepassing, met in achtneming van de op wettelijke voorschriften en regels van ongeschreven recht gegronde beperkingen, verplichtingen en rechtsbeginselen, alsmede de openbare orde en de goede zeden.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Lid 2 verklaart bepalingen met beperkingen van toepassing.
- **Historische verwachting (then, v6):** Verwerp nooit-bepalingen-van-toepassing als strijdig met lid 2; claim niet dat de wet hier een volledige biologische definitie geeft.
- **T (GTH-v1):** Betekenissteun voldoet niet: stelling dat zakenbepalingen nooit van toepassing zijn strijdt met de gegeven wettelijke uitzondering. Geen volledige biologische definitie uit de bron afleiden.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld. Concreet te behouden/herstellen: Betekenissteun voldoet niet: stelling dat zakenbepalingen nooit van toepassing zijn strijdt met de gegeven wettelijke uitzondering. Geen volledige biologische definitie uit de bron afleiden.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Blijft het onderscheid tussen juridische kwalificatie en toepasselijkheid correct?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P23 — Dezelfde bron via upload, RAG en wiki telt niet driemaal

**Route:** keten · **Prioriteit:** P1 · **Bronnen:** S-WIKI, S-RAW · **scenario_input_sha256:** `7b0a633d7d70aa7f…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** LLM-wiki
- **definitie:** kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling onveranderlijke bronnen
- **context:** Karpathy LLM-wiki-patroon
- **Gegeven:** Bied S-RAW aan via upload én RAG; S-WIKI citeert dezelfde raw-capture.
- **Wanneer:** Vergelijk evidencegraph en aantallen onafhankelijke bronnen.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-WIKI** · afgeleide wikipagina (echt, lokaal)

- pakketpad: `bronfixtures/wiki/LLM-wiki.md` · sha256 `4704009b44d40c13904afd8018c4f35e9c1257c3f05c11291b8e157af764d966`
- bronversie: last_updated 2026-08-03
- herkomst (geen hyperlink): `/Users/chrislehnen/Documents/Claude/Projects/Wiki Karpaty style/llm-wiki-kennis/wiki/begrippen/LLM-wiki.md`
- locators (manifest): frontmatter; Definitie
- **frontmatter: confidence** — letterlijk:

> confidence: high

- **frontmatter: lifecycle** — letterlijk:

> lifecycle: reviewed

- **Definitie** — letterlijk:

> kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling onveranderlijke bronnen

**S-RAW** · historische primaire capture (echt, lokaal)

- pakketpad: `bronfixtures/raw/2026-07-08-karpathy-llm-wiki-gist.md` · sha256 `dc3efe98ae62f23dd08acad13aba2e95287beb20b6bec2f4af0423557fe37401`
- bronversie: capture 2026-07-08
- herkomst (geen hyperlink): `/Users/chrislehnen/Documents/Claude/Projects/Wiki Karpaty style/llm-wiki-kennis/raw/2026-07-08-karpathy-llm-wiki-gist.md`
- locators (manifest): The core idea; Architecture / Raw sources
- **The core idea (eerste alinea)** — letterlijk:

> Most people's experience with LLMs and documents looks like RAG: you upload a collection of files, the LLM retrieves relevant chunks at query time, and generates an answer. This works, but the LLM is rediscovering knowledge from scratch on every question. There's no accumulation. Ask a subtle question that requires synthesizing five documents, and the LLM has to find and piece together the relevant fragments every time. Nothing is built up. NotebookLM, ChatGPT file uploads, and most RAG systems work this way.

- **Architecture / Raw sources** — letterlijk:

> **Raw sources** — your curated collection of source documents. Articles, papers, images, data files. These are immutable — the LLM reads from them but never modifies them. This is your source of truth.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Alle routes komen uit dezelfde oorspronkelijke tekst, gekoppeld op hash/canonieke URL.
- **Historische verwachting (then, v6):** Behoud de drie routes maar één onderliggende capture; geen onafhankelijkheid uit kanaalaantal afleiden.
- **T (GTH-v1):** Behoud één onderliggende bronversie met meerdere aanvoerroutes; geen onafhankelijk bewijs uit bestands- of kanaalaantal. Inhoudelijke deelcontroles blijven nodig.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Is brononafhankelijkheid inhoudelijk onderbouwd in plaats van geteld?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P24 — Bron wijzigt na deskundige beoordeling

**Route:** keten · **Prioriteit:** P1 · **Bronnen:** S-UPLOAD32, M-UPLOAD · **scenario_input_sha256:** `ab0984bb9fc94a96…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** zorgvuldigheidsbeginsel
- **definitie:** plicht om de nodige kennis over relevante feiten en af te wegen belangen te vergaren
- **context:** Awb / Nederlands bestuursrecht
- **Gegeven:** Voor uitvoering is een echte review van exact origineel vereist; testkopie krijgt daarna gewijzigde bytes. Geen review is nu aanwezig.
- **Wanneer:** Bied mutant aan onder gelijknamig bronrecord en probeer vaststelling/niet-draft-export.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-UPLOAD32** · bestaand lokaal uploadbestand (echt, zonder eigen herkomst)

- pakketpad: `bronfixtures/meegegeven-awb-artikel-3-2.txt` · sha256 `73a64ab39bd2c2120adf13d323481153deed88b0a5f38b9e99d494ad0e5b9be0`
- bronversie: onbekend (null)
- herkomst (geen hyperlink): `/Users/chrislehnen/Projecten/Wetsanalyse/test-data/awb-artikel-3-2.txt`
- locators (manifest): wetszin onder beschrijvende kop
- **beschrijvende kop (geen wettekst)** — letterlijk:

> Artikel 3:2 Algemene wet bestuursrecht - Zorgvuldigheidsbeginsel

- **wetszin onder beschrijvende kop** — letterlijk:

> Bij de voorbereiding van een besluit vergaart het bestuursorgaan de nodige kennis omtrent de relevante feiten en de af te wegen belangen.

**M-UPLOAD** · SYNTHETISCHE MUTANT — bewust gewijzigde testkopie, geen echte revisie — **SYNTHETISCH (mutant/testconstructie)**

- pakketpad: `bronfixtures/mutanten/meegegeven-awb-artikel-3-2.txt` · sha256 `2a12e4a4b9fab6efe364f59e4547e2bb41034395410fe66e23ec30031f3b34e4`
- bronversie: TEST-MUTATIE, geen wetswijziging
- herkomst (geen hyperlink): `S-UPLOAD32`
- locators (manifest): artikeltekst
- **artikeltekst (GEMUTEERD)** — letterlijk:

> Bij de voorbereiding van een besluit vergaart het bestuursorgaan de nodige kennis omtrent de relevante feiten .

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** P07-mutatie verandert de norminhoud; eerdere review bindt aan eerdere bytes.
- **Historische verwachting (then, v6):** Oud oordeel geldt niet automatisch voor nieuwe bronhash; markeer ontbrekende actuele binding en blokkeer zolang vereist bewijs ontbreekt.
- **T (GTH-v1):** Eerder oordeel geldt niet automatisch voor gewijzigde definitie/bron/context. Beoordeling zichtbaar verouderd en opnieuw uitvoeren op actuele binding; eventuele nu zichtbare betekenisfout afzonderlijk melden.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Is review zichtbaar gekoppeld aan de beoordeelde bron én definitieversie?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P25 — Definitie wijzigt na deskundige beoordeling

**Route:** keten · **Prioriteit:** P1 · **Bronnen:** S-AWB13 · **scenario_input_sha256:** `696e6e1da8885b0a…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** besluit
- **definitie:** beslissing van een bestuursorgaan
- **context:** Awb / Nederlands bestuursrecht
- **Gegeven:** Vereist bij uitvoering echte review van P01; wijzig daarna definitie naar P02 zonder review.
- **Wanneer:** Sla op, herlaad en probeer vaststelling/niet-draft-export.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-AWB13** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/awb-1-3-20260815.txt` · sha256 `7be6c298370590a6ca51e82d9f6e9f066274e86adc3051037748beb2078e3ec8`
- bronversie: 2026-08-15
- link: <https://wetten.overheid.nl/BWBR0005537/2026-08-15/0?g=2026-09-14&z=2026-09-14#Hoofdstuk1_Titeldeel1.1_Artikel1:3>
- locators (manifest): artikel 1:3 lid 1; artikel 1:3 lid 2; artikel 1:3 lid 3; artikel 1:3 lid 4
- **artikel 1:3 lid 1** — letterlijk:

> Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

- **artikel 1:3 lid 2** — letterlijk:

> Onder beschikking wordt verstaan: een besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan.

- **artikel 1:3 lid 3** — letterlijk:

> Onder aanvraag wordt verstaan: een verzoek van een belanghebbende, een besluit te nemen.

- **artikel 1:3 lid 4** — letterlijk:

> Onder beleidsregel wordt verstaan: een bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, omtrent de afweging van belangen, de vaststelling van feiten of de uitleg van wettelijke voorschriften bij het gebruik van een bevoegdheid van een bestuursorgaan.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Nieuwe tekst mist kenmerken die oude beoordeelde tekst wel had.
- **Historische verwachting (then, v6):** Eerder oordeel mag de nieuwe definitie niet afdekken; status/gate blijven na herladen consistent.
- **T (GTH-v1):** Eerder oordeel geldt niet automatisch voor gewijzigde definitie/bron/context. Beoordeling zichtbaar verouderd en opnieuw uitvoeren op actuele binding; eventuele nu zichtbare betekenisfout afzonderlijk melden.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Is definitiehash/revisie onderdeel van de reviewbinding?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P26 — Boolean reviewed=true is geen beoordelaarsbewijs

**Route:** keten · **Prioriteit:** P1 · **Bronnen:** S-AWB13 · **scenario_input_sha256:** `ecf8257bc53b887b…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** besluit
- **definitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling
- **context:** Awb / Nederlands bestuursrecht
- **Gegeven:** Voer bij testadapter alleen reviewed=true op zonder reviewer-identiteit, bevoegdheid, passage en datum. Gebruik geen echte identiteit als fictie.
- **Wanneer:** Valideer en probeer vaststelling/niet-draft-export.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-AWB13** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/awb-1-3-20260815.txt` · sha256 `7be6c298370590a6ca51e82d9f6e9f066274e86adc3051037748beb2078e3ec8`
- bronversie: 2026-08-15
- link: <https://wetten.overheid.nl/BWBR0005537/2026-08-15/0?g=2026-09-14&z=2026-09-14#Hoofdstuk1_Titeldeel1.1_Artikel1:3>
- locators (manifest): artikel 1:3 lid 1; artikel 1:3 lid 2; artikel 1:3 lid 3; artikel 1:3 lid 4
- **artikel 1:3 lid 1** — letterlijk:

> Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

- **artikel 1:3 lid 2** — letterlijk:

> Onder beschikking wordt verstaan: een besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan.

- **artikel 1:3 lid 3** — letterlijk:

> Onder aanvraag wordt verstaan: een verzoek van een belanghebbende, een besluit te nemen.

- **artikel 1:3 lid 4** — letterlijk:

> Onder beleidsregel wordt verstaan: een bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, omtrent de afweging van belangen, de vaststelling van feiten of de uitleg van wettelijke voorschriften bij het gebruik van een bevoegdheid van een bestuursorgaan.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Boolean zegt niets over wie welke versie heeft beoordeeld.
- **Historische verwachting (then, v6):** Geen bevoegde review fabriceren; ontbrekende actor/evidencevelden blijven een blokkade.
- **T (GTH-v1):** reviewed=true bewijst geen herleidbare beoordeling. AI-oordeel kan zelfstandig positief worden bij echt bewijs; menselijke vaststelreview mag niet uit de boolean worden gefabriceerd.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Zijn identiteit, bevoegdheid, oordeel en exacte beoordeelde inhoud aantoonbaar?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3/B2: een boolean reviewed=true is geen beoordelaarsbewijs en geen dekkingsbewijs; er is geen automatische correctie.
- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P27 — Bewijspakket blijft inspecteerbaar na opslaan/herladen/export

**Route:** keten · **Prioriteit:** P1 · **Bronnen:** S-AWB13 · **scenario_input_sha256:** `e5f96ae462316e01…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** besluit
- **definitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling
- **context:** Awb / Nederlands bestuursrecht
- **Gegeven:** Uitvoering vereist echt volledig beoordeeld P01-record; zonder dat alleen gelabelde draft.
- **Wanneer:** Leg vóór opslag en na herladen/export bron, lid, passage, definitieversie, reviewer en uitkomst vast.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-AWB13** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/awb-1-3-20260815.txt` · sha256 `7be6c298370590a6ca51e82d9f6e9f066274e86adc3051037748beb2078e3ec8`
- bronversie: 2026-08-15
- link: <https://wetten.overheid.nl/BWBR0005537/2026-08-15/0?g=2026-09-14&z=2026-09-14#Hoofdstuk1_Titeldeel1.1_Artikel1:3>
- locators (manifest): artikel 1:3 lid 1; artikel 1:3 lid 2; artikel 1:3 lid 3; artikel 1:3 lid 4
- **artikel 1:3 lid 1** — letterlijk:

> Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

- **artikel 1:3 lid 2** — letterlijk:

> Onder beschikking wordt verstaan: een besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan.

- **artikel 1:3 lid 3** — letterlijk:

> Onder aanvraag wordt verstaan: een verzoek van een belanghebbende, een besluit te nemen.

- **artikel 1:3 lid 4** — letterlijk:

> Onder beleidsregel wordt verstaan: een bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, omtrent de afweging van belangen, de vaststelling van feiten of de uitleg van wettelijke voorschriften bij het gebruik van een bevoegdheid van een bestuursorgaan.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** Primaire vindplaats art. 1:3 lid 1 en bronversie zijn reproduceerbaar vastgelegd.
- **Historische verwachting (then, v6):** Vergelijk dezelfde bindingsvelden; export zonder nodig bewijs is geen geslaagde overdracht. CON-02-conform is geen algemene exporttoestemming. Controleer ook behoud van de korte citeervorm en gerichte hyperlink in de bronpresentatie.
- **T (GTH-v1):** Controleer dezelfde bron-/kandidaat-/beoordelingsbinding na opslaan, herladen en export zonder sessie. Geen succesvolle overdracht als bewijs verloren gaat; geen algemene exporttoestemming uit CON-02-voldoet.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Kan een tweede reviewer uitsluitend met export exact de beoordeling reconstrueren?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P28 — Hoge totaalscore heft ontbrekend bronbewijs niet op

**Route:** keten · **Prioriteit:** P1 · **Bronnen:** S-BW3 · **scenario_input_sha256:** `04d8dff7d207cdca…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** besluit
- **definitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling
- **context:** Awb / Nederlands bestuursrecht
- **Gegeven:** Gebruik niet-passende bron P03 en een gecontroleerde testscore 0.99; essentiële actuele evidence/review ontbreekt.
- **Wanneer:** Volg regelstatus door adapters, UI, opslag, herladen en vaststelling/niet-draft-export.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-BW3** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/bw3-1-2-2a-20250701.txt` · sha256 `cc46ab1cc9b667db076e9003a114b092a16a566c65aa62e256012165378d32ba`
- bronversie: 2025-07-01
- link: <https://wetten.overheid.nl/BWBR0005291/2025-07-01/0?g=2026-09-14&z=2026-09-14#Boek3_Titeldeel1_Afdeling1_Artikel2>
- locators (manifest): artikel 1; artikel 2; artikel 2a lid 1; artikel 2a lid 2
- **artikel 1** — letterlijk:

> Goederen zijn alle zaken en alle vermogensrechten.

- **artikel 2** — letterlijk:

> Zaken zijn de voor menselijke beheersing vatbare stoffelijke objecten.

- **artikel 2a lid 1** — letterlijk:

> Dieren zijn geen zaken.

- **artikel 2a lid 2** — letterlijk:

> Bepalingen met betrekking tot zaken zijn op dieren van toepassing, met in achtneming van de op wettelijke voorschriften en regels van ongeschreven recht gegronde beperkingen, verplichtingen en rechtsbeginselen, alsmede de openbare orde en de goede zeden.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** BW3-fragment ondersteunt besluit niet; ranking/score is geen passagebewijs.
- **Historische verwachting (then, v6):** Geen toestemming op basis van score; ontbrekende vereisten blijven blokkerend. Concept mag alleen herkenbaar concept blijven.
- **T (GTH-v1):** Een oude pass of hoge totaalscore geeft geen actueel bronbewijs/vaststeltoestemming. CON-02 zonder cijfer moet samen met resultaat-/poortdoorwerking worden ingevoerd; concept blijft herkenbaar concept.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Eerst oorzaak vaststellen met ruwe output, nabewerking en brondoorgifte. Alleen een afzonderlijk, brongetrouw voorstel maken wanneer de benodigde gegevens bestaan. Bij ontbrekend bewijs/technische fout/bronconflict stoppen en dat tekort oplossen; geen bronwoorden toevoegen als reparatie. Elke wijziging hertoetsen met geraakte regels.
- **Deskundigenvraag:** Blijft de beslispoort gekoppeld aan bewijsstatus op alle stappen?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B3: de historische 'testscore 0.99' is synthetische scenario-input en blijft ongewijzigd in het historische record. De huidige verwachting toont GEEN totaalcijfer; er is dus ook geen cijfer dat ontbrekend bronbewijs zou kunnen opheffen. Ontbrekend bewijs/review blijft blokkerend voor vaststelling en niet-draft-export (bestaand DEF-630-contract) en vervalt niet.
- B2: geen automatische herstelpoging; het ontbreken van bewijs is geen fout in de definitiezin.
- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P29 — Juiste betekenis, maar verwijzing slechts naar wetten-startpagina

**Route:** bronverwijzing · **Prioriteit:** P2 · **Bronnen:** S-AWB13 · **scenario_input_sha256:** `f1b60c9995574f83…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** besluit
- **definitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling
- **context:** Awb / Nederlands bestuursrecht
- **citation_display:** Awb
- **source_hyperlink:** https://wetten.overheid.nl/
- **Gegeven:** Zelfde definitie/passage als P01; bronlabel Awb zonder artikel/lid en hyperlink alleen naar de startpagina.
- **Wanneer:** Controleer inhoudelijke bronsteun en verwijskwaliteit afzonderlijk in het vastgezette testrecord.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-AWB13** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/awb-1-3-20260815.txt` · sha256 `7be6c298370590a6ca51e82d9f6e9f066274e86adc3051037748beb2078e3ec8`
- bronversie: 2026-08-15
- link: <https://wetten.overheid.nl/BWBR0005537/2026-08-15/0?g=2026-09-14&z=2026-09-14#Hoofdstuk1_Titeldeel1.1_Artikel1:3>
- locators (manifest): artikel 1:3 lid 1; artikel 1:3 lid 2; artikel 1:3 lid 3; artikel 1:3 lid 4
- **artikel 1:3 lid 1** — letterlijk:

> Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

- **artikel 1:3 lid 2** — letterlijk:

> Onder beschikking wordt verstaan: een besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan.

- **artikel 1:3 lid 3** — letterlijk:

> Onder aanvraag wordt verstaan: een verzoek van een belanghebbende, een besluit te nemen.

- **artikel 1:3 lid 4** — letterlijk:

> Onder beleidsregel wordt verstaan: een bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, omtrent de afweging van belangen, de vaststelling van feiten of de uitleg van wettelijke voorschriften bij het gebruik van een bevoegdheid van een bestuursorgaan.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** De beschikbare bronpassage ondersteunt besluit. De verwijzing leidt niet specifiek naar art. 1:3 lid 1.
- **Historische verwachting (then, v6):** Markeer onvoldoende precieze verwijzing; leid daaruit niet af dat de definitie inhoudelijk onjuist is.
- **T (GTH-v1):** Verwijskwaliteit voldoet niet: startpagina is aantoonbaar minder precies dan beschikbare bronlink. Betekenissteun kan tegelijk positief zijn.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Pas uitsluitend de bronverwijzing aan op basis van de bekende vindplaats; behoud definitiezin en bronpassage exact. Hertoets verwijskwaliteit en de gewijzigde bronbinding. Geen link/afkorting verzinnen.
- **Deskundigenvraag:** Is de bronverwijzing nauwkeurig, kort en bereikbaar volgens de actuele norm, los van de juistheid van de definitie?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B1: er bestaat een gerichte primaire online vindplaats (origin-URL S-AWB13); een verwijzing naar alleen de startpagina valt niet onder de uitzondering. De uitzondering is niet automatisch van toepassing.
- B2: aanpassing van de verwijzing alleen op verzoek; definitiezin en passage blijven bewaard.
- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P30 — Precieze bron met onnodig lange citeervorm

**Route:** bronverwijzing · **Prioriteit:** P2 · **Bronnen:** S-AWB13 · **scenario_input_sha256:** `70bd427c8fbc722f…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** besluit
- **definitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling
- **context:** Awb / Nederlands bestuursrecht
- **citation_display:** artikel 1:3 lid 1 van de Algemene wet bestuursrecht
- **source_hyperlink:** https://wetten.overheid.nl/jci1.3:c:BWBR0005537&hoofdstuk=1&titeldeel=1.1&artikel=1:3&z=2026-08-15&g=2026-08-15
- **Gegeven:** Zelfde definitie/passage als P01; correcte artikel/lid/versie en artikelhyperlink, maar uitgeschreven wetsnaam in het bronlabel.
- **Wanneer:** Controleer inhoudelijke bronsteun en verwijskwaliteit afzonderlijk in het vastgezette testrecord.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-AWB13** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/awb-1-3-20260815.txt` · sha256 `7be6c298370590a6ca51e82d9f6e9f066274e86adc3051037748beb2078e3ec8`
- bronversie: 2026-08-15
- link: <https://wetten.overheid.nl/BWBR0005537/2026-08-15/0?g=2026-09-14&z=2026-09-14#Hoofdstuk1_Titeldeel1.1_Artikel1:3>
- locators (manifest): artikel 1:3 lid 1; artikel 1:3 lid 2; artikel 1:3 lid 3; artikel 1:3 lid 4
- **artikel 1:3 lid 1** — letterlijk:

> Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

- **artikel 1:3 lid 2** — letterlijk:

> Onder beschikking wordt verstaan: een besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan.

- **artikel 1:3 lid 3** — letterlijk:

> Onder aanvraag wordt verstaan: een verzoek van een belanghebbende, een besluit te nemen.

- **artikel 1:3 lid 4** — letterlijk:

> Onder beleidsregel wordt verstaan: een bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, omtrent de afweging van belangen, de vaststelling van feiten of de uitleg van wettelijke voorschriften bij het gebruik van een bevoegdheid van een bestuursorgaan.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** De actuele toelichting onderscheidt compacte wetsafkorting van lange wetsnaam. De broninhoud verandert niet door deze redactie.
- **Historische verwachting (then, v6):** Geef gerichte verkorting van het bronlabel naar art. 1:3 lid 1 Awb; behoud vindplaats en hyperlink. Geen semantische afkeuring uitsluitend vanwege citeerlengte.
- **T (GTH-v1):** Verwijskwaliteit heeft een tekortkoming door onnodig lange citeerwijze; betekenissteun wordt daarom niet afgekeurd. Totaal volgt ontbreken van volledige conformiteit, zonder cijfer.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Pas uitsluitend de bronverwijzing aan op basis van de bekende vindplaats; behoud definitiezin en bronpassage exact. Hertoets verwijskwaliteit en de gewijzigde bronbinding. Geen link/afkorting verzinnen.
- **Deskundigenvraag:** Is de bronverwijzing nauwkeurig, kort en bereikbaar volgens de actuele norm, los van de juistheid van de definitie?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B1: niet van toepassing (link en vindplaats aanwezig). Alleen de citeervorm is aan de orde; dat is verwijskwaliteit, geen betekenissteun.
- B2: inkorting van de citeervorm alleen als afzonderlijk voorstel op verzoek.
- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---

## C02-P31 — Vindplaats compleet, beschikbare hyperlink ontbreekt ★ eerste zes

**Route:** bronverwijzing · **Prioriteit:** P2 · **Bronnen:** S-AWB13 · **scenario_input_sha256:** `7603e6d3efdb732c…`

### 1. Historische scenario-input (ongewijzigd)

- **begrip:** besluit
- **definitie:** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling
- **context:** Awb / Nederlands bestuursrecht
- **citation_display:** art. 1:3 lid 1 Awb
- **source_hyperlink:** null
- **Gegeven:** Zelfde definitie/passage als P01; kort label en vaste bronversie aanwezig, maar hyperlinkveld leeg terwijl de primaire online wet is gevonden.
- **Wanneer:** Controleer inhoudelijke bronsteun en verwijskwaliteit afzonderlijk in het vastgezette testrecord.

### 2. Bronnen — exacte inhoud, locator, versie, link

**S-AWB13** · primaire wetstranscriptie (echt)

- pakketpad: `bronfixtures/awb-1-3-20260815.txt` · sha256 `7be6c298370590a6ca51e82d9f6e9f066274e86adc3051037748beb2078e3ec8`
- bronversie: 2026-08-15
- link: <https://wetten.overheid.nl/BWBR0005537/2026-08-15/0?g=2026-09-14&z=2026-09-14#Hoofdstuk1_Titeldeel1.1_Artikel1:3>
- locators (manifest): artikel 1:3 lid 1; artikel 1:3 lid 2; artikel 1:3 lid 3; artikel 1:3 lid 4
- **artikel 1:3 lid 1** — letterlijk:

> Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

- **artikel 1:3 lid 2** — letterlijk:

> Onder beschikking wordt verstaan: een besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan.

- **artikel 1:3 lid 3** — letterlijk:

> Onder aanvraag wordt verstaan: een verzoek van een belanghebbende, een besluit te nemen.

- **artikel 1:3 lid 4** — letterlijk:

> Onder beleidsregel wordt verstaan: een bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, omtrent de afweging van belangen, de vaststelling van feiten of de uitleg van wettelijke voorschriften bij het gebruik van een bevoegdheid van een bestuursorgaan.

### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)

- **Onderbouwing (source_based_oracle):** De actuele toelichting vraagt een gerichte hyperlink. In deze casus bestaat een primaire online bron; een eventuele offline uitzondering is niet van toepassing verklaard.
- **Historische verwachting (then, v6):** Meld de ontbrekende gerichte hyperlink als apart verwijskwaliteitsgebrek. Een algemene claim dat CON-02 geen hyperlink verlangt is hier onvoldoende.
- **T (GTH-v1):** Verwijskwaliteit voldoet niet: een beschikbare gerichte hyperlink ontbreekt. Geen beroep op nog open offline-uitzondering waar een bruikbare link bestaat.
- **G (GTH-v1):** Gebruik dezelfde aangewezen betekenis/context en werkelijk beschikbare bronpassages. Behoud alle bepalende kenmerken en uitzonderingen; ontbrekend gezag of bronbewijs afzonderlijk melden, nooit fabriceren. De in T benoemde fout mag niet als geslaagde generatie worden voorgesteld.
- **H (GTH-v1, alleen op verzoek — B2):** Pas uitsluitend de bronverwijzing aan op basis van de bekende vindplaats; behoud definitiezin en bronpassage exact. Hertoets verwijskwaliteit en de gewijzigde bronbinding. Geen link/afkorting verzinnen.
- **Deskundigenvraag:** Is de bronverwijzing nauwkeurig, kort en bereikbaar volgens de actuele norm, los van de juistheid van de definitie?

### 4. Huidige laag — projectbesluiten 15-09-2026

- B1: de deskundige verwijzingsuitzondering is NIET automatisch van toepassing. Zij geldt uitsluitend voor een bestaande bron zonder bruikbare hyperlink; in deze casus is de gerichte primaire online link beschikbaar (origin-URL S-AWB13, wetten.overheid.nl art. 1:3). Een leeg hyperlinkveld terwijl de link bestaat blijft een verwijskwaliteitsgebrek, tenzij een deskundige expliciet en gemotiveerd anders vaststelt — dat oordeel is niet gegeven.
- B2: aanvulling van de hyperlink alleen als afzonderlijk voorstel op verzoek; definitiezin en bronpassage exact behouden.
- B3: geen cijfer; verwachte weergave is 'verwijskwaliteit: voldoet niet' naast afzonderlijke bronbasis/betekenissteun-oordelen — als ontwerpverwachting, niet als vastgestelde uitkomst.
- B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.
- B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.
- De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.

### 5. Bewijsstatus

- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee

### 6. Deskundig oordeel (in te vullen)

- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium
- [ ] **Afwijzing** — zie motivering
- **Motivering:** 
- **Actor (naam/rol):** 
- **Datum:** 

---
