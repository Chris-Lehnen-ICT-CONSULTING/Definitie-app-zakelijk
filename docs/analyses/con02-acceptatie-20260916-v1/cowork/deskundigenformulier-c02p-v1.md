# Deskundigenformulier CON-02 / DEF-743 — 31 C02-P-praktijkgevallen

**Versie** deskundigenformulier-c02p-v1 · **Datum** 2026-09-16 · **Opsteller** Cowork (Claude), onafhankelijk

> **Aard van dit stuk.** Dit is een **AI-voorbeoordeling** op de reeds geleverde 94 scenario's en bronfixtures. Het is **geen deskundige goldset**, **geen uitgevoerde app-test** en **geen gemeten regeluitkomst**. Alle velden onder *menselijk besluit* zijn leeg en blijven leeg tot een bevoegde beoordelaar ze invult. Case-ID's, begrip, definitie en context zijn ongewijzigd overgenomen uit `casusregister-geintegreerd-v6.json`.

## Grondslag en projectie

| | |
|---|---|
| Norm | `fixtures/astra-actueel-20260914.md`: *"De definitie moet zoveel mogelijk gebaseerd zijn op een authentieke bron."* |
| Casussen | `casusregister-geintegreerd-v6.json`, 31 rijen C02-P01 t/m C02-P31 |
| Bronnen | `bronmanifest-v3.json`, 13 fixtures met sha256, bytes, bronversie en locators |
| Retrieval | `retrieval-fixtures-v1.json` — `synthetic_ranking: true`, `live_retrieval_executed: false` |

De drie besloten productkeuzes zijn **als projectie** toegepast, zonder historische invoer te wijzigen:

1. **Drie onafhankelijke deeloordelen** — bronbasis, betekenissteun, herleidbaarheid. "Geen geschikte bron" alleen als expliciet deskundig geaccepteerde uitzondering met zoekbewijs; ontbrekende hyperlink bij een bestaande bron alleen met bewaarde versie, stabiele ID, exacte locator én expliciete actor, motivering en acceptatie.
2. **Herstel** uitsluitend op expliciet verzoek, duurzaam maximaal één poging per oorspronkelijke generatie, diagnose vooraf, apart voorstel, menselijk toepassen, volledig hertoetsen. **Dit formulier bevat daarom geen herstelvoorstellen.**
3. **Geen numerieke totaalscore** en geen vervangende gedeeltelijke totaalscore; zichtbaar zijn de afzonderlijke regeluitkomsten en de dekking. Dit formulier telt dus niet op en rangschikt niet.

Oordeelwaarden: `voldoet` · `voldoet niet` · `nog te beoordelen`.

## Eén correctie die ik zelf heb moeten terugnemen

Bij een eerste doorloop nam ik aan dat een gerichte hyperlink in het pakket ontbrak. Dat is onjuist: `bronmanifest-v3.json` legt voor **S-AWB13**, **S-AWB32** en **S-BW3** een artikelgerichte hyperlink naar wetten.overheid.nl vast. De herleidbaarheidsoordelen zijn daarop gecorrigeerd. Wat wél onbewezen blijft: dat het bronverwijzingsveld van het app-record diezelfde link draagt — dat is niet gemeten.

---

## Deel A — 6 representatieve gevallen ter beoordeling

Twee positieve, twee negatieve en twee grensgevallen, zo gekozen dat elk van de drie deeloordelen minstens één keer beslissend is.

### C02-P01 — Volledige Awb-bron, inhoudelijk passende definitie

*Rol in de startset: positief — schone bronbasis en betekenissteun · route `upload` · prioriteit P1*

**Begrip** besluit  
**Definitie (ongewijzigde invoer)** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling  
**Context** Awb / Nederlands bestuursrecht

**Bronpassage(s)**

- `S-AWB13` — fixtures/awb-1-3-20260815.txt · bronversie **2026-08-15** · sha256 `7be6c2983705…` · locator **artikel 1:3 lid 1**  
  > Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

**Voorgestelde deeloordelen (AI, niet geaccepteerd)**

| Deeloordeel | Voorstel | Motivering |
|---|---|---|
| Bronbasis | voldoet | S-AWB13 is een primaire wetstranscriptie (wetten.overheid.nl, versie 2026-08-15) en lid 1 definieert precies het begrip 'besluit'. |
| Betekenissteun | voldoet | Alle drie kenmerken staan letterlijk in lid 1: 'schriftelijke beslissing', 'van een bestuursorgaan', 'inhoudende een publiekrechtelijke rechtshandeling'. Geen kenmerk toegevoegd of weggelaten. |
| Herleidbaarheid | voldoet | Stabiele bron-ID, bewaarde bronversie en exacte locator zijn aanwezig, en het bronmanifest legt een artikelgerichte hyperlink naar wetten.overheid.nl vast (anker Artikel 1:3). Daarmee is de verwijzing nauwkeurig, beknopt en gericht bereikbaar; de uitzonderingsroute voor een ontbrekende hyperlink uit besluit (1) is hier niet nodig. |

**Onzekerheid en ontbrekende gegevens**

- Geen app-uitvoering: dit is AI-voorbeoordeling op de fixtures, geen gemeten regeluitkomst.
- De gerichte hyperlink is vastgelegd in het bronmanifest van dit onderzoekspakket; dat het bronverwijzingsveld van het app-record dezelfde link draagt, is niet gemeten. De link wijst naar het artikel, het lid volgt uit de locator.

**Menselijk besluit** — in te vullen door bevoegde beoordelaar

| Veld | Invullen |
|---|---|
| Beoordelaar / bevoegdheid / datum | ☐ … |
| Beoordeelde bronhash(es) en definitieversie | ☐ … |
| Bronbasis | ☐ voldoet ☐ voldoet niet ☐ nog te beoordelen — motivering: … |
| Betekenissteun | ☐ voldoet ☐ voldoet niet ☐ nog te beoordelen — motivering: … |
| Herleidbaarheid | ☐ voldoet ☐ voldoet niet ☐ nog te beoordelen — motivering: … |
| Uitzondering *geen geschikte bron* | ☐ ingeroepen — zoekbewijs / actor / motivering: … |
| Uitzondering *ontbrekende hyperlink* | ☐ ingeroepen — bewaarde versie / stabiele ID / exacte locator / actor / motivering: … |
| Eindoordeel en opmerkingen | ☐ … |

### C02-P15 — Wiki met navolgbare raw-steun voor afgebakende definitieclaim

*Rol in de startset: positief — enige casus waarin alle drie deeloordelen voldoen · route `LLM-WIKI` · prioriteit P1*

**Begrip** LLM-wiki  
**Definitie (ongewijzigde invoer)** kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling onveranderlijke bronnen  
**Context** Karpathy LLM-wiki-patroon

**Bronpassage(s)**

- `S-RAW` — fixtures/raw/2026-07-08-karpathy-llm-wiki-gist.md · bronversie **capture 2026-07-08** · sha256 `dc3efe98ae62…` · locator **Architecture - Raw sources**  
  > **Raw sources** - your curated collection of source documents. Articles, papers, images, data files. These are immutable - the LLM reads from them but never modifies them. This is your source of truth.
- `S-RAW` — fixtures/raw/2026-07-08-karpathy-llm-wiki-gist.md · bronversie **capture 2026-07-08** · sha256 `dc3efe98ae62…` · locator **The core idea**  
  > Instead of just retrieving from raw documents at query time, the LLM **incrementally builds and maintains a persistent wiki** - a structured, interlinked collection of markdown files that sits between you and the raw sources. ... You never (or rarely) write the wiki yourself - the LLM writes and maintains all of it.
- `S-RAWREGISTER` — fixtures/raw/register-uittreksel.md · bronversie **ONTBREKEND** · sha256 `e7500aa7bad7…` · locator **registerrij met canonieke URL en sha256**  
  > | 2026-07-08-karpathy-llm-wiki-gist.md | https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f | 2026-07-08 | dc3efe98ae62f23dd08acad13aba2e95287beb20b6bec2f4af0423557fe37401 |
- `S-WIKISOURCE` — fixtures/wiki/karpathy-llm-wiki-gist.md · bronversie **gedeclareerd last_updated 2026-08-03** · sha256 `b918678627ab…` · locator **Kernclaims - bronpositie**  
  > Kernclaims (bronpositie): 'Drie lagen: Raw-laag (immutable, source of truth), Wiki-laag (volledig model-eigendom), Onderhoudscontract'.

**Voorgestelde deeloordelen (AI, niet geaccepteerd)**

| Deeloordeel | Voorstel | Motivering |
|---|---|---|
| Bronbasis | voldoet | S-RAW is een historische primaire capture (2026-07-08) van de gist; het register-uittreksel bindt bestand, canonieke URL en sha256 (dc3efe98...7401) en die hash komt overeen met het aangeleverde exemplaar. |
| Betekenissteun | voldoet | Alle vier kenmerken zijn in de raw terug te vinden: 'interlinked collection of markdown files' (onderling gelinkte markdown-pagina's), 'the LLM writes and maintains all of it' (geschreven en onderhouden door een taalmodel), 'persistent wiki' / 'persistent, compounding artifact' (kennisbank), en 'These are immutable' (onveranderlijke bronnen). De definitie blijft afgebakend tot het patroon. |
| Herleidbaarheid | voldoet | Stabiele bron-ID, bewaarde capture met datum, exacte locator (Architecture / The core idea) en een canonieke hyperlink naar de gist in het register-uittreksel. Hiermee is de verwijzing nauwkeurig, beknopt en bereikbaar. |

**Onzekerheid en ontbrekende gegevens**

- De tweede bron (praneybehl-plugin) is niet geverifieerd; claims die daarop steunen vallen buiten dit oordeel.
- Het register-uittreksel is een lokale kopie zonder upstream-hercontrole (gekopieerd 2026-09-14).
- Geen app-uitvoering: dit is AI-voorbeoordeling op de fixtures, geen gemeten regeluitkomst.

**Menselijk besluit** — in te vullen door bevoegde beoordelaar

| Veld | Invullen |
|---|---|
| Beoordelaar / bevoegdheid / datum | ☐ … |
| Beoordeelde bronhash(es) en definitieversie | ☐ … |
| Bronbasis | ☐ voldoet ☐ voldoet niet ☐ nog te beoordelen — motivering: … |
| Betekenissteun | ☐ voldoet ☐ voldoet niet ☐ nog te beoordelen — motivering: … |
| Herleidbaarheid | ☐ voldoet ☐ voldoet niet ☐ nog te beoordelen — motivering: … |
| Uitzondering *geen geschikte bron* | ☐ ingeroepen — zoekbewijs / actor / motivering: … |
| Uitzondering *ontbrekende hyperlink* | ☐ ingeroepen — bewaarde versie / stabiele ID / exacte locator / actor / motivering: … |
| Eindoordeel en opmerkingen | ☐ … |

### C02-P03 — Gezaghebbende upload gaat over een ander begrip

*Rol in de startset: negatief — beslissend op **bronbasis** · route `upload` · prioriteit P1*

**Begrip** besluit  
**Definitie (ongewijzigde invoer)** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling  
**Context** Awb / Nederlands bestuursrecht

**Bronpassage(s)**

- `S-BW3` — fixtures/bw3-1-2-2a-20250701.txt · bronversie **2025-07-01** · sha256 `cc46ab1cc9b6…` · locator **artikel 1**  
  > Goederen zijn alle zaken en alle vermogensrechten.
- `S-BW3` — fixtures/bw3-1-2-2a-20250701.txt · bronversie **2025-07-01** · sha256 `cc46ab1cc9b6…` · locator **artikel 2**  
  > Zaken zijn de voor menselijke beheersing vatbare stoffelijke objecten.
- `S-BW3` — fixtures/bw3-1-2-2a-20250701.txt · bronversie **2025-07-01** · sha256 `cc46ab1cc9b6…` · locator **artikel 2a lid 1**  
  > Dieren zijn geen zaken.

**Voorgestelde deeloordelen (AI, niet geaccepteerd)**

| Deeloordeel | Voorstel | Motivering |
|---|---|---|
| Bronbasis | **voldoet niet** | De enige aangeleverde bron (BW Boek 3, art. 1/2/2a) gaat over goederen, zaken en dieren. Zij bevat geen enkele bepaling over het begrip 'besluit'. Er is dus geen geschikte authentieke bron voor deze definitie aangeleverd. |
| Betekenissteun | **voldoet niet** | Geen enkel kenmerk van de definitie (schriftelijk, bestuursorgaan, publiekrechtelijke rechtshandeling) komt in het fragment voor; er is geen betekenissteun, ook geen gedeeltelijke. |
| Herleidbaarheid | *nog te beoordelen* | De verwijzing naar S-BW3 is formeel volledig (ID, versie 2025-07-01, locators, artikelgerichte hyperlink), maar zij leidt naar een passage die de definitie niet draagt. Een nauwkeurige verwijzing naar een niet-steunende bron levert geen bruikbare herleiding; de deskundige stelt vast of dit deeloordeel nog zelfstandig betekenis heeft zodra de bronbasis is afgekeurd. |

**Onzekerheid en ontbrekende gegevens**

- Koppeling deeloordelen: als bronbasis wordt afgekeurd, is de vraag of herleidbaarheid nog zelfstandig betekenis heeft. Dat is een openstaande formuliervraag, geen bronfeit.
- Geen app-uitvoering: dit is AI-voorbeoordeling op de fixtures, geen gemeten regeluitkomst.

**Menselijk besluit** — in te vullen door bevoegde beoordelaar

| Veld | Invullen |
|---|---|
| Beoordelaar / bevoegdheid / datum | ☐ … |
| Beoordeelde bronhash(es) en definitieversie | ☐ … |
| Bronbasis | ☐ voldoet ☐ voldoet niet ☐ nog te beoordelen — motivering: … |
| Betekenissteun | ☐ voldoet ☐ voldoet niet ☐ nog te beoordelen — motivering: … |
| Herleidbaarheid | ☐ voldoet ☐ voldoet niet ☐ nog te beoordelen — motivering: … |
| Uitzondering *geen geschikte bron* | ☐ ingeroepen — zoekbewijs / actor / motivering: … |
| Uitzondering *ontbrekende hyperlink* | ☐ ingeroepen — bewaarde versie / stabiele ID / exacte locator / actor / motivering: … |
| Eindoordeel en opmerkingen | ☐ … |

### C02-P20 — Aanvraag zonder belanghebbende-eis

*Rol in de startset: negatief — beslissend op **betekenissteun** · route `wettekst` · prioriteit P1*

**Begrip** aanvraag  
**Definitie (ongewijzigde invoer)** verzoek van een willekeurige persoon om een besluit te nemen  
**Context** Awb / Nederlands bestuursrecht

**Bronpassage(s)**

- `S-AWB13` — fixtures/awb-1-3-20260815.txt · bronversie **2026-08-15** · sha256 `7be6c2983705…` · locator **artikel 1:3 lid 3**  
  > Onder aanvraag wordt verstaan: een verzoek van een belanghebbende, een besluit te nemen.

**Voorgestelde deeloordelen (AI, niet geaccepteerd)**

| Deeloordeel | Voorstel | Motivering |
|---|---|---|
| Bronbasis | voldoet | Primaire wetsbron; lid 3 definieert 'aanvraag'. |
| Betekenissteun | **voldoet niet** | Lid 3 spreekt van 'een verzoek van een belanghebbende'. De definitie vervangt dat door 'een willekeurige persoon' en laat daarmee de belanghebbende-eis vallen; de extensie wordt ruimer dan de bron toestaat. |
| Herleidbaarheid | voldoet | Stabiele bron-ID, bewaarde bronversie en exacte locator zijn aanwezig, en het bronmanifest legt een artikelgerichte hyperlink naar wetten.overheid.nl vast (anker Artikel 1:3). Daarmee is de verwijzing nauwkeurig, beknopt en gericht bereikbaar; de uitzonderingsroute voor een ontbrekende hyperlink uit besluit (1) is hier niet nodig. |

**Onzekerheid en ontbrekende gegevens**

- Geen app-uitvoering: dit is AI-voorbeoordeling op de fixtures, geen gemeten regeluitkomst.
- De gerichte hyperlink is vastgelegd in het bronmanifest van dit onderzoekspakket; dat het bronverwijzingsveld van het app-record dezelfde link draagt, is niet gemeten. De link wijst naar het artikel, het lid volgt uit de locator.

**Menselijk besluit** — in te vullen door bevoegde beoordelaar

| Veld | Invullen |
|---|---|
| Beoordelaar / bevoegdheid / datum | ☐ … |
| Beoordeelde bronhash(es) en definitieversie | ☐ … |
| Bronbasis | ☐ voldoet ☐ voldoet niet ☐ nog te beoordelen — motivering: … |
| Betekenissteun | ☐ voldoet ☐ voldoet niet ☐ nog te beoordelen — motivering: … |
| Herleidbaarheid | ☐ voldoet ☐ voldoet niet ☐ nog te beoordelen — motivering: … |
| Uitzondering *geen geschikte bron* | ☐ ingeroepen — zoekbewijs / actor / motivering: … |
| Uitzondering *ontbrekende hyperlink* | ☐ ingeroepen — bewaarde versie / stabiele ID / exacte locator / actor / motivering: … |
| Eindoordeel en opmerkingen | ☐ … |

### C02-P12 — Begripsnaam staat niet letterlijk in de ondersteunende wetszin

*Rol in de startset: grensgeval — begripsnaam staat niet letterlijk in de bron · route `upload` · prioriteit P1*

**Begrip** zorgvuldigheidsbeginsel  
**Definitie (ongewijzigde invoer)** plicht van het bestuursorgaan om bij besluitvoorbereiding kennis over relevante feiten en af te wegen belangen te vergaren  
**Context** Awb / Nederlands bestuursrecht

**Bronpassage(s)**

- `S-AWB32` — fixtures/awb-3-2-20260815.txt · bronversie **2026-08-15** · sha256 `ad520ff75fb2…` · locator **artikel 3:2**  
  > Bij de voorbereiding van een besluit vergaart het bestuursorgaan de nodige kennis omtrent de relevante feiten en de af te wegen belangen.

**Voorgestelde deeloordelen (AI, niet geaccepteerd)**

| Deeloordeel | Voorstel | Motivering |
|---|---|---|
| Bronbasis | voldoet | S-AWB32 is een primaire wetstranscriptie met versie 2026-08-15 en exacte locator artikel 3:2. |
| Betekenissteun | voldoet | De omschrijving is een getrouwe afleiding van de normzin, met alle elementen behouden. Dat het woord 'zorgvuldigheidsbeginsel' niet letterlijk in de bron staat, raakt de vindbaarheid van de term, niet de betekenissteun voor de inhoud. |
| Herleidbaarheid | voldoet | Stabiele bron-ID, bewaarde bronversie en exacte locator zijn aanwezig, en het bronmanifest legt een artikelgerichte hyperlink naar wetten.overheid.nl vast (jci-link artikel 3:2). Daarmee is de verwijzing nauwkeurig, beknopt en gericht bereikbaar; de uitzonderingsroute voor een ontbrekende hyperlink uit besluit (1) is hier niet nodig. |

**Onzekerheid en ontbrekende gegevens**

- Grensgeval: letterlijke term-afwezigheid mag niet als ontbrekende bronbasis worden gelezen.
- Geen app-uitvoering: dit is AI-voorbeoordeling op de fixtures, geen gemeten regeluitkomst.
- De gerichte hyperlink is vastgelegd in het bronmanifest van dit onderzoekspakket; dat het bronverwijzingsveld van het app-record dezelfde link draagt, is niet gemeten. De link wijst naar het artikel, het lid volgt uit de locator.

**Menselijk besluit** — in te vullen door bevoegde beoordelaar

| Veld | Invullen |
|---|---|
| Beoordelaar / bevoegdheid / datum | ☐ … |
| Beoordeelde bronhash(es) en definitieversie | ☐ … |
| Bronbasis | ☐ voldoet ☐ voldoet niet ☐ nog te beoordelen — motivering: … |
| Betekenissteun | ☐ voldoet ☐ voldoet niet ☐ nog te beoordelen — motivering: … |
| Herleidbaarheid | ☐ voldoet ☐ voldoet niet ☐ nog te beoordelen — motivering: … |
| Uitzondering *geen geschikte bron* | ☐ ingeroepen — zoekbewijs / actor / motivering: … |
| Uitzondering *ontbrekende hyperlink* | ☐ ingeroepen — bewaarde versie / stabiele ID / exacte locator / actor / motivering: … |
| Eindoordeel en opmerkingen | ☐ … |

### C02-P31 — Vindplaats compleet, beschikbare hyperlink ontbreekt

*Rol in de startset: grensgeval — beslissend op **herleidbaarheid**, met uitzonderingsroute · route `bronverwijzing` · prioriteit P2*

**Begrip** besluit  
**Definitie (ongewijzigde invoer)** schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling  
**Context** Awb / Nederlands bestuursrecht

**Bronpassage(s)**

- `S-AWB13` — fixtures/awb-1-3-20260815.txt · bronversie **2026-08-15** · sha256 `7be6c2983705…` · locator **artikel 1:3 lid 1 (kort label en vaste bronversie aanwezig, hyperlinkveld leeg)**  
  > Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.

**Voorgestelde deeloordelen (AI, niet geaccepteerd)**

| Deeloordeel | Voorstel | Motivering |
|---|---|---|
| Bronbasis | voldoet | Primaire wetsbron; bron en bronversie zijn aanwezig en vastgelegd. |
| Betekenissteun | voldoet | Betekenissteun gelijk aan P01. |
| Herleidbaarheid | **voldoet niet** | Besluit (1) staat een ontbrekende hyperlink bij een bestaande bron alleen toe met bewaarde versie, stabiele ID, exacte locator én expliciete actor, motivering en acceptatie. De eerste drie zijn aanwezig, de acceptatieroute is niet doorlopen. Bovendien is de primaire online wet in deze casus gevonden en is geen offline-uitzondering van toepassing verklaard. |

**Onzekerheid en ontbrekende gegevens**

- Grensgeval: dit oordeel kan door de deskundige worden omgezet naar 'voldoet' door de uitzondering expliciet te aanvaarden met actor en motivering. Dat veld staat hieronder leeg.
- Onderscheid met P01: daar is de hyperlinkstatus onbekend, hier aantoonbaar leeg.
- Geen app-uitvoering: dit is AI-voorbeoordeling op de fixtures, geen gemeten regeluitkomst.

**Menselijk besluit** — in te vullen door bevoegde beoordelaar

| Veld | Invullen |
|---|---|
| Beoordelaar / bevoegdheid / datum | ☐ … |
| Beoordeelde bronhash(es) en definitieversie | ☐ … |
| Bronbasis | ☐ voldoet ☐ voldoet niet ☐ nog te beoordelen — motivering: … |
| Betekenissteun | ☐ voldoet ☐ voldoet niet ☐ nog te beoordelen — motivering: … |
| Herleidbaarheid | ☐ voldoet ☐ voldoet niet ☐ nog te beoordelen — motivering: … |
| Uitzondering *geen geschikte bron* | ☐ ingeroepen — zoekbewijs / actor / motivering: … |
| Uitzondering *ontbrekende hyperlink* | ☐ ingeroepen — bewaarde versie / stabiele ID / exacte locator / actor / motivering: … |
| Eindoordeel en opmerkingen | ☐ … |

---

## Deel B — overige dekking (25 casussen)

Alle 31 rijen staan volledig, met dezelfde velden en dezelfde lege besluitvelden, in `deskundigenformulier-c02p-v1.json`. Hieronder de resterende 25 in overzicht.

| ID | Titel | Route | Bronbasis | Betekenissteun | Herleidbaarheid |
|---|---|---|---|---|---|
| C02-P02 | Bron aanwezig maar publiekrechtelijke beperking ontbreekt | upload | voldoet | **voldoet niet** | voldoet |
| C02-P04 | Bestaand meegegeven tekstbestand zonder eigen herkomst | upload | *nog te beoordelen* | voldoet | **voldoet niet** |
| C02-P05 | Meegegeven bestand gekoppeld aan gecontroleerde wetspassage | upload | voldoet | voldoet | voldoet |
| C02-P06 | Hernoemen maakt dezelfde bron niet onafhankelijk | upload | voldoet | voldoet | *nog te beoordelen* |
| C02-P07 | Dezelfde bestandsnaam met gewijzigde wetszin | upload | **voldoet niet** | **voldoet niet** | **voldoet niet** |
| C02-P08 | RAG haalt het juiste beleidsregellid op | RAG | voldoet | voldoet | *nog te beoordelen* |
| C02-P09 | Hoge RAG-score met verkeerd lid | RAG | **voldoet niet** | **voldoet niet** | *nog te beoordelen* |
| C02-P10 | Dierenuitzondering aanwezig in corpus maar buiten top vijf | RAG | voldoet | **voldoet niet** | *nog te beoordelen* |
| C02-P11 | Zelfde dierencasus met volledige relevante retrieval | RAG | voldoet | **voldoet niet** | voldoet |
| C02-P13 | Artikel/lid en chunk-ID door normalisatie en opslag | RAG | voldoet | voldoet | *nog te beoordelen* |
| C02-P14 | Alleen een reviewed/high-wikipagina | LLM-WIKI | **voldoet niet** | **voldoet niet** | **voldoet niet** |
| C02-P16 | Wiki wijzigt betekenis maar behoudt reviewed-label | LLM-WIKI | voldoet | **voldoet niet** | **voldoet niet** |
| C02-P17 | Raw-bestand gewijzigd zonder registerhash te actualiseren | LLM-WIKI | **voldoet niet** | *nog te beoordelen* | **voldoet niet** |
| C02-P18 | Niet-aangeleverde wiki-bron niet als gelezen registreren | LLM-WIKI | voldoet | voldoet | **voldoet niet** |
| C02-P19 | Beschikking omvat ook afwijzing | wettekst | voldoet | voldoet | voldoet |
| C02-P21 | Goed is ruimer dan alleen stoffelijk object | wettekst | voldoet | **voldoet niet** | voldoet |
| C02-P22 | Geen zaken betekent niet dat zakenbepalingen nooit gelden | wettekst | voldoet | **voldoet niet** | voldoet |
| C02-P23 | Dezelfde bron via upload, RAG en wiki telt niet driemaal | keten | voldoet | voldoet | voldoet |
| C02-P24 | Bron wijzigt na deskundige beoordeling | keten | *nog te beoordelen* | voldoet | **voldoet niet** |
| C02-P25 | Definitie wijzigt na deskundige beoordeling | keten | voldoet | **voldoet niet** | voldoet |
| C02-P26 | Boolean reviewed=true is geen beoordelaarsbewijs | keten | voldoet | voldoet | voldoet |
| C02-P27 | Bewijspakket blijft inspecteerbaar na opslaan/herladen/export | keten | voldoet | voldoet | *nog te beoordelen* |
| C02-P28 | Hoge totaalscore heft ontbrekend bronbewijs niet op | keten | **voldoet niet** | **voldoet niet** | **voldoet niet** |
| C02-P29 | Juiste betekenis, maar verwijzing slechts naar wetten-startpagina | bronverwijzing | voldoet | voldoet | **voldoet niet** |
| C02-P30 | Precieze bron met onnodig lange citeervorm | bronverwijzing | voldoet | voldoet | *nog te beoordelen* |

### Wat die 25 afdekken, per thema

- **Upload en bronherkomst (P02, P04–P07)** — ontbrekende publiekrechtelijke beperking; meegegeven bestand zonder eigen herkomst, los en gekoppeld aan de gecontroleerde wetszin; hernoemen van identieke bytes; dezelfde bestandsnaam met gewijzigde wetszin.
- **RAG-selectie (P08–P11, P13)** — juist lid opgehaald; hoge score met verkeerd lid; beslissende bepaling buiten top-5; volledige retrieval; verlies van artikel/lid en chunk-ID in de provenanceprojectie.
- **Wiki-keten (P14, P16–P18, P23)** — alleen een afgeleide reviewed-pagina; omgekeerd kenmerk met behouden reviewlabel; gewijzigde raw tegen niet-geactualiseerde registerhash; niet-aangeleverde bron niet als gelezen registreren; dezelfde bron via drie routes telt eenmaal.
- **Wettekst en afbakening (P19, P21, P22)** — inclusie van de afwijzing bij beschikking; goed ruimer dan zaak; kwalificatie versus toepasselijke bepalingen bij dieren.
- **Acceptatie- en bewijsketen (P24–P28)** — bron wijzigt na review; definitie wijzigt na review; `reviewed=true` zonder beoordelaarsbewijs; bewijspakket na opslaan/herladen/export; hoge testscore die ontbrekend bronbewijs niet opheft.
- **Bronverwijzing (P29, P30)** — label zonder artikel/lid met hyperlink naar de startpagina; correcte vindplaats en artikelhyperlink met onnodig lange citeervorm.

### Verdeling van de voorstellen over 31 casussen

| Deeloordeel | voldoet | voldoet niet | nog te beoordelen |
|---|---|---|---|
| Bronbasis | 23 | 6 | 2 |
| Betekenissteun | 17 | 13 | 1 |
| Herleidbaarheid | 13 | 10 | 8 |

Dit is een verdeling, **geen score**: er wordt niet opgeteld, gewogen of gerangschikt (besluit 3).

## Bewijsgrenzen

- Geen enkele regeluitkomst in dit formulier is door de app geproduceerd; alles is afgeleid uit de fixtures.
- De retrievalvolgorde is een gecontroleerde stub, geen uitgevoerde retrieval; echte document- en chunk-ID's ontbreken.
- Waar broninhoud ontbreekt, staat dat als **ONTBREKEND** in de JSON; er is niets aangevuld of verzonnen.
- De merge van app-PR454 is context, geen door mij geverifieerd bewijs. Het afgeronde onderzoek is niet heropend.
- Herstelvoorstellen zijn bewust afwezig (besluit 2: alleen op expliciet verzoek, met diagnose vooraf en apart voorstel).
