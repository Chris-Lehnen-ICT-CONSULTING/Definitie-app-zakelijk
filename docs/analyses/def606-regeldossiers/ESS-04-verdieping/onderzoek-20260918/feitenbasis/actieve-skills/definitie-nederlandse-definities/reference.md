# Nederlandse Definities — Volledige Referentie

> On-demand referentie bij `definitie-nederlandse-definities`. Bevat de volledige Nederlandse taal- en definitieregels (ISO 704/1087): theoretisch fundament, genus-differentia, kick-off-richtingen (ESS-02: hulp, geen woordplicht), fout-taxonomie, grammatica, interpunctie, opbouwregels, contextvermelding (CON-01) en beoordelingschecklist.

## Theoretisch Fundament

### ISO 704:2022 en ISO 1087:2019

De DefinitieAgent volgt de internationale standaarden voor terminologie:

**ISO 704:2022 — Terminologiewerk: Principes en methoden**
- Een definitie beschrijft een *begrip* (concept), niet een *term* (woord)
- Elk begrip heeft een *intensie* (kenmerken die het begrip definiëren) en een *extensie* (alle instanties die onder het begrip vallen)
- Definities volgen het genus-differentia-patroon
- Een definitie moet noodzakelijke EN voldoende kenmerken bevatten

**ISO 1087:2019 — Terminologie: Vocabulaire**
- *Term*: talige aanduiding van een begrip ("verdachte")
- *Begrip*: abstracte denkeenheid ("het concept verdachte")
- *Definitie*: beschrijving waarmee een begrip wordt afgebakend van andere begrippen
- *Begripssysteem*: geordend geheel van begrippen met hun onderlinge relaties

### Intensie en Extensie

Dit onderscheid is fundamenteel voor goede definities:

**Intensie** = de verzameling kenmerken die een begrip definiëren
- "Geldboete" heeft als intensie: sanctie + betaling + geldbedrag + aan de staat
- De intensie bepaalt WELKE instanties er wel/niet onder vallen

**Extensie** = de verzameling van alle instanties die onder het begrip vallen
- "Geldboete" heeft als extensie: alle concrete geldboetes die ooit zijn/worden opgelegd
- De extensie is het RESULTAAT van de intensie

**Vuistregel:** een definitie beschrijft de INTENSIE van een begrip. De extensie hoort thuis bij voorbeelden (zie skill `voorbeelden-generatie`).

### Noodzakelijke en Voldoende Voorwaarden

Een goede definitie bevat kenmerken die zowel noodzakelijk als samen voldoende zijn:

**Noodzakelijke voorwaarde**: een kenmerk dat elk lid van de klasse MOET hebben
- "Geldboete" → MOET een sanctie zijn (noodzakelijk)
- "Geldboete" → MOET betaling van een geldbedrag inhouden (noodzakelijk)

**Voldoende voorwaarden**: de kenmerken die samen GENOEG zijn om het begrip te identificeren
- "Sanctie bestaande uit betaling van een geldbedrag aan de staat" → dit is voldoende om een geldboete te onderscheiden van een taakstraf of gevangenisstraf

**Veelvoorkomende fout:** alleen noodzakelijke voorwaarden geven zonder dat ze samen voldoende zijn:
- ❌ `sanctie die door de rechter wordt opgelegd` → dit is ook waar voor een taakstraf → onvoldoende onderscheidend
- ✅ `sanctie bestaande uit betaling van een geldbedrag aan de staat` → onderscheidt geldboete van alle andere sancties

**Zelftest:** "Als iets aan alle kenmerken in mijn definitie voldoet, IS het dan altijd een [begrip]? En als iets een [begrip] IS, heeft het dan altijd al deze kenmerken?"

## Het Genus-Differentia Principe

Elke definitie volgt het Aristotelische patroon: `[begrip]: [genus] + [differentia]`

- **Genus** (geslachtsbegrip): het bredere begrip waartoe het behoort
- **Differentia** (soortverschil): wat het onderscheidt van andere leden van dat genus

Voorbeeld: `geldboete: sanctie bestaande uit betaling van een geldbedrag aan de staat`
- Genus = `sanctie`, Differentia = `bestaande uit betaling van een geldbedrag aan de staat`

### Eisen aan het Genus

1. Het genus moet een **breder begrip** zijn (niet op hetzelfde niveau)
2. Het genus moet **direct boven** het begrip staan in de hiërarchie (niet te hoog, niet te laag)
3. Het genus mag **NIET het begrip zelf** zijn (geen circulaire definitie)
4. Het genus moet **al gedefinieerd zijn** of algemeen bekend zijn

**Genus te hoog:**
- ❌ `geldboete: maatregel bestaande uit...` → "maatregel" is te breed (er zijn ook niet-strafrechtelijke maatregelen)
- ✅ `geldboete: sanctie bestaande uit...` → "sanctie" is het directe genus

**Genus te laag:**
- ❌ `sanctie: geldboete of taakstraf of...` → dit is een opsomming, geen definitie
- ✅ `sanctie: maatregel opgelegd bij overtreding van een norm` → correct genus

### Eisen aan de Differentia

1. De differentia moet het begrip **onderscheiden** van zijn zusterbegrippen (ESS-05)
2. De differentia moet **essentiële kenmerken** bevatten, geen toevallige
3. De differentia mag **NIET herhalen** wat al in het genus zit

## Kick-off Patronen per Richting (ESS-02)

De vier richtingen zijn hulpmiddelen voor generatie, geen afzonderlijke ESS-02-afkeurgrond en geen woordplicht. Zij combineren betekenisniveau (algemeen begrip, of één bepaald ding of voorval) met aard (bijvoorbeeld activiteit of uitkomst) en kunnen overlappen: een algemeen activiteitbegrip is tegelijk algemeen én activiteit. Een passend genus buiten de voorbeelden is even goed. Beoordeel zinsbouw en stijl afzonderlijk volgens hun eigen regels. Volledig contract: [`references/ess02-betekenisniveau.md`](references/ess02-betekenisniveau.md) (kopie van de canonieke bron in `definitie-toetsregels`).

**TYPE** — Bijvoorbeeld een passend genus:
- ✅ `woord dat handelingen of toestanden uitdrukt`
- ✅ `sanctie bestaande uit betaling van een geldbedrag aan de staat`
- `soort woord dat...` of `type document dat...` past niet wanneer woorden of documenten zelf bedoeld zijn; bij een begrip waarvan de instanties soorten zijn, kan zo'n genus wél passen
- ❌ `is een...` (koppelwerkwoord-start, zie Verboden Patronen)

**PROCES** — Bijvoorbeeld `activiteit waarbij …` of `handeling die …`, gevolgd door onderscheidende kenmerken:
- ✅ `activiteit waarbij gegevens worden verzameld door directe waarneming`
- ✅ `handeling die ertoe strekt de identiteit van een persoon vast te stellen`
- Een activiteit mag haar uitkomst noemen zonder van betekenis te veranderen
- ❌ `is een activiteit...` / `het observeren van...`

**RESULTAAT** — Bijvoorbeeld `resultaat van …` of `uitspraak van de rechter …`, wanneer de uitkomst bedoeld is:
- ✅ `resultaat van het uitwerken en analyseren van interviews`
- ✅ `uitspraak van de rechter na behandeling ter terechtzitting`
- Benoem de onderbouwde uitkomst met een passend zelfstandig naamwoord; een uitkomst is niet noodzakelijk een maatregel
- ❌ `is het resultaat van...`

**EXEMPLAAR** — Benoem één bepaald ding (ook abstract) of voorval met de gegeven identificatie:
- ✅ `exemplaar van een adelaar dat op 25 mei 2024 werd waargenomen in de Biesbosch`
- ✅ `meting met identificatie M-17 die op 16 september 2026 om 10:00 is uitgevoerd aan sensor S-4` — het woord "exemplaar" is niet vereist
- ❌ `is een exemplaar van...`

## Definitiefout-taxonomie

Herken en vermijd deze veelvoorkomende definitiefouten:

### Structuurfouten

| Fout | Uitleg | Voorbeeld |
|------|--------|-----------|
| **Circulaire definitie** | Het begrip komt voor in eigen definitie | ❌ "Toezicht: het houden van toezicht op..." |
| **Te breed** | De definitie omvat meer dan het begrip | ❌ "Sanctie: maatregel" (alle maatregelen zijn dan sancties) |
| **Te smal** | De definitie omvat minder dan het begrip | ❌ "Sanctie: geldboete" (taakstraf valt erbuiten) |
| **Negatieve definitie** | Beschrijft wat het NIET is in plaats van wat het IS | ❌ "Vrijspraak: beslissing die geen veroordeling inhoudt" |
| **Syntactische definitie** | Definieert de term in plaats van het begrip | ❌ "Verdachte: woord dat verwijst naar iemand die..." |

### Inhoudsfouten

| Fout | Uitleg | Voorbeeld |
|------|--------|-----------|
| **Doel versus afbakening** | Overig doel hoort buiten de kern; een onderbouwde bepalende functie mag blijven (ESS-01) | Grensgeval: toezicht als activiteit om naleving te waarborgen. Beoordeel of de doelrol de gegeven betekenis bepaalt; zinsvorm alleen rechtvaardigt geen goed/fout-label. |
| **Enumeratieve definitie** | Somt onderdelen op in plaats van het geheel te beschrijven | ❌ "Strafrecht: geldboetes, taakstraffen en gevangenisstraffen" |
| **Metaforische definitie** | Gebruikt beeldspraak | ❌ "Recidive: het draaideureffect in het strafrecht" |
| **Synoniemverklaring** | Geeft alleen een synoniem | ❌ "Gedetineerde: gevangene" |
| **Onderscheidingsfalen** | Onderscheidt niet van zusterbegrippen | ❌ "Geldboete: sanctie opgelegd door de rechter" (geldt ook voor taakstraf) |

### Taalfouten

| Fout | Uitleg | Voorbeeld |
|------|--------|-----------|
| **Containerbegrip** | Vaag genus zonder informatiewaarde | ❌ "Registratie: aspect van gegevensverwerking" |
| **Modale vaagheid** | Gebruik van "kan", "moet", "mag" | ❌ "Sanctie: maatregel die kan worden opgelegd" |
| **Impliciete context** | Verwijst naar niet-genoemde achtergrond | ❌ "Beschikking: beslissing in het kader van het systeem" |

## Grammaticaregels

**Enkelvoud als standaard:**
- ✅ `proces` (niet: `processen`), ✅ `maatregel` (niet: `maatregelen`)
- Uitzondering: plurale tantum (`gegevens`, `kosten`, `notulen`)

**Actieve vorm prefereren:**
- ✅ `instantie die toezicht houdt`
- ❌ `instantie waardoor toezicht wordt gehouden`

**Tegenwoordige tijd:**
- ✅ `proces dat identificeert`
- ❌ `proces dat zal identificeren`

**Werkwoord-termen** — definieer als handeling:
- ✅ `controleren: handeling waarbij naleving wordt geverifieerd`
- ❌ `controleren: het controleren van...`

**Deverbale naamwoorden** — bepaal of de nadruk op het proces of het resultaat ligt:
- Procesnadruk: ✅ `registratie: activiteit waarbij gegevens worden vastgelegd`
- Resultaatnadruk: ✅ `registratie: vastgelegde gegevens in een officieel systeem`
- ❌ `registratie: het registreren` (syntactische definitie)

**Bijzinnen met "dat/die":**
- ✅ `persoon die wordt verdacht van een strafbaar feit` (betrekkelijke bijzin correct gebruikt)
- ❌ `persoon, verdacht van een strafbaar feit` (losse bijstelling; onduidelijkere structuur)

## Verboden Patronen

**Nooit starten met:**
- Lidwoorden: `de`, `het`, `een`
- Koppelwerkwoorden: `is`, `betekent`, `omvat`, `betreft`, `houdt in`
- Vage metaconstructies: `soort van`, `type van`, `vorm van`, `manier van` — een stijlpatroon (STR/ARAI), geen ESS-02-oordeel; `soort` of `type` als inhoudelijk passend genus blijft toegestaan (zie Kick-off Patronen)
- Herhaling van het begrip: `toezicht is het houden van toezicht`

**Vermijden:**
- Vage containerbegrippen: `aspect`, `element`, `factor`, `ding`, `iets`, `zaak`
- Subjectieve bijvoeglijke naamwoorden: `belangrijk`, `essentieel`, `groot`, `veelvuldig`
- Modale hulpwerkwoorden: `kan`, `moet`, `mag`, `zal`, `dient te`; `dient als/tot` is een functie- of gebruiksaanduiding, inhoudelijk te beoordelen onder ESS-01
- Impliciete verwijzingen: `deze`, `dit`, `die`, `dat` zonder duidelijk antecedent
- Voorwaardelijke formuleringen: `indien`, `mits`, `tenzij`, `alleen als`
- Toelichtende formuleringen: `bijvoorbeeld`, `zoals`, `onder andere`, `namelijk`
- Afkortingen zonder toelichting: `DJI` zonder `(Dienst Justitiële Inrichtingen)`

## Interpunctie

- Geen punt aan het einde van de definitie
- Komma's spaarzaam, alleen voor duidelijkheid
- Haakjes ALLEEN voor afkortingen: `Dienst Justitiële Inrichtingen (DJI)`
- ❌ Geen haakjes voor uitleg: `maatregel (corrigerend of preventief)`
- Puntkomma's voor limitatieve opsommingen binnen de zin
- ❌ Geen opsommingstekens, nummering of alinea-indeling — het is één zin

## Opbouwregels

| Regel | Instructie | Toetsregel |
|-------|-----------|------------|
| Eén zin | Formuleer als één enkele, begrijpelijke zin | INT-01 |
| Compact | 150–350 tekens als richtlijn | — |
| Essentie | Begripsafbakening; onderbouwde bepalende functie behouden; overig doel buiten de kern | ESS-01 |
| Niveau en aard | Kern maakt duidelijk of een algemeen begrip dan wel één bepaald ding of voorval bedoeld is, en waar relevant activiteit of uitkomst; geen markerplicht, label is geen bewijs | ESS-02 |
| Aard, niet doel | Beschrijf de natuur, niet het doel | STR-06 |
| Positief | Zeg wat het IS, niet wat het NIET is | INT-08 |
| Geen circulariteit | Het begrip mag niet in de eigen definitie voorkomen | SAM-05 |
| Genus ≠ term | De kick-off mag niet het begrip zelf zijn | STR-02 |
| Onderscheidend | Onderscheid van zusterbegrippen | ESS-05 |
| Noodzakelijk + voldoende | Kenmerken zijn noodzakelijk EN samen voldoende | — |
| Zelfstandig | De definitie is begrijpelijk zonder specialistische kennis | INT-10 |
| Context buiten de zin | Registratiecontext in het contextveld; een naam alleen als die de afbakening draagt | CON-01 |

## Contextvermelding (CON-01)

Een definitie beschrijft het begrip; de context waarbinnen de definitie geldt (rechtsgebied, organisatie, wet, project) wordt gestructureerd vastgelegd in het contextveld van het record — niet in de definitiezin. Een naam die inhoudelijk nodig is om het begrip af te bakenen of te identificeren mag wél in de zin staan; de grond daarvoor hoort in de toelichting bij de toetsuitleg, niet in een apart in te vullen veld. Een letterlijke treffer op een contextnaam is een signaal voor menselijke beoordeling, geen automatische overtreding.

### Vier onderscheidingen

| Onderscheid | Kenmerk | Bij formuleren | Bij toetsen (CON-01) |
|-------------|---------|----------------|----------------------|
| **Registratievermelding** | De naam zegt alleen "dit geldt binnen context X"; zonder de naam blijft de afbakening intact | Laat de naam weg; leg de context vast in het contextveld | Voldoet niet op onderdeel — verplaats de registratie naar het contextveld |
| **Noodzakelijke naam** | Een gegeven domeinfeit (vastgelegde afbakening of identificatie) maakt de naam nodig; zonder de naam is het een ander begrip | Behoud de naam en noteer de grond (het domeinfeit) | Voldoet op onderdeel — met motivering van de grond in de toetsuitleg |
| **Foutief signaal** | Het woord matcht letterlijk, maar verwijst niet naar de context | Behoud het woord | Voldoet op onderdeel — gemotiveerd "geen contextvermelding" |
| **Onduidelijk** | De functie van de naam is uit de zin niet vast te stellen | Vraag naar de functie/grond vóór je kiest | Nog te beoordelen — geen automatische verwijdering, geen automatische pass |

### Voorbeelden (fictief)

De organisaties Prisma, Lumen en Vega zijn verzonnen. Niet de naam zelf, maar het erbij gegeven domeinfeit draagt de beoordeling — een organisatienaam is niet "dus" noodzakelijk omdat de zin zonder die naam algemener wordt.

**Registratievermelding** — context: Prisma (registratieorganisatie); begrip: dossierstuk. Gegeven: een dossierstuk is buiten Prisma hetzelfde begrip; Prisma is alleen de plaats waar deze definitie is geregistreerd
- ❌ `document dat bij Prisma is opgenomen in een dossier en de behandeling van een zaak ondersteunt` — "bij Prisma" zegt alleen waar de definitie geldt; de afbakening blijft zonder de naam intact
- ✅ `document dat is opgenomen in een dossier en de behandeling van een zaak ondersteunt` + contextveld: Prisma

**Noodzakelijke naam** — context: Lumen (uitgever); begrip: pas. Gegeven: volgens de vastgelegde domeinafbakening behoren alleen passen van uitgever Lumen tot het begrip
- ✅ `toegangsbewijs dat door uitgever Lumen is verstrekt en de houder toegang geeft tot een aangesloten locatie` — zonder "Lumen" vallen ook passen van andere uitgevers onder de zin, in strijd met de vastgelegde afbakening
- Grond bij de toetsuitleg: *vastgelegde domeinafbakening: alleen passen van Lumen behoren tot het begrip; de naam draagt die afbakening*

**Foutief signaal** — context: OM; begrip: verzoek
- ✅ `schriftelijke vraag aan een instantie om een besluit te nemen` — "om" is hier een voegwoord in "om … te", geen verwijzing naar de context OM
- Motivering: *geen contextvermelding*. Claim níet dat "om" een noodzakelijke naam is, en leid uit hoofdletter of kleine letter niets automatisch af — beoordeel de functie van het woord in de zin

**Onduidelijk** — context: Vega; begrip: bevestiging. Gegeven: er is geen vastgelegde afbakening of toelichting over de functie van de naam
- ❓ `bericht van Vega waarmee de ontvangst van een aanvraag wordt vastgelegd` — bakent "van Vega" het begrip af (alleen berichten van Vega tellen als bevestiging), of registreert het alleen waar de definitie geldt? Uit de zin is dat niet vast te stellen
- Uitkomst: Nog te beoordelen. Vraag: *welke functie heeft de naam in de zin — is er zonder de naam een ander begrip, en is dat ergens vastgelegd?* Verwijder de naam niet automatisch en keur hem niet automatisch goed

### Meerdere treffers

Beoordeel elke treffer afzonderlijk. Een noodzakelijke naam op de ene plek maakt een registratievermelding elders in dezelfde zin niet geldig; een open treffer blijft zichtbaar als "Nog te beoordelen". Maak geen nieuwe aggregatie- of scoreformule over de treffers heen.

- Gemengd — context: Prisma, Lumen; begrip: pas (zelfde gegeven als hierboven): `toegangsbewijs dat bij Prisma is geregistreerd en door uitgever Lumen is verstrekt aan de houder` → "Lumen": noodzakelijk (behouden, grond: vastgelegde afbakening); "bij Prisma": registratie → Voldoet niet op onderdeel, verplaats naar het contextveld

### Technische fout

Kan CON-01 niet worden uitgevoerd (bijvoorbeeld ontbrekende invoer of een fout in de regel), dan wordt dat afzonderlijk als technische fout getoond. Een technische fout levert geen inhoudelijke uitkomst (Voldoet / Voldoet niet / Nog te beoordelen) en geen cijfer op.

### Domeinvocabulaire (voorkeur, geen verbod)

De vakinhoud komt tot uiting in de woordkeus, niet in een contextlabel. Kies waar mogelijk de preciezere domeinterm; de algemenere term is niet fout, maar minder onderscheidend:

- Vocabulaire: `persoon` → `verdachte` (strafrecht); `gebouw` → `penitentiaire inrichting` (DJI); `medewerker` → `ambtenaar` (bestuursrecht)
- Scope: `regels` → `gedragsregels`; `beslissing` → `beschikking`; `straf` → `hoofdstraf` of `bijkomende straf`
- Relaties: `herhaling` → `recidive`; `begeleiding` → `reclasseringstoezicht`; `overplaatsing` → `selectie en plaatsing`

### Grenzen

- **Zelftest:** "Welke functie heeft elke naam in de zin — registratie (naar het contextveld), afbakening/identificatie (behouden + grond) of geen contextverwijzing (behouden + motivering)? Kan ik dat niet bepalen → Nog te beoordelen."
- CON-01 levert geen cijfer en geen 0/1, alleen een uitkomst per treffer; de gewichten en drempels van de andere toetsregels gelden er niet voor (zie **definitie-toetsregels**).
- Dit advies is geen opgeslagen review: de menselijke beoordeling met actor, motivering en versiebinding vindt plaats in de app en wordt hier niet vervangen, vastgesteld of goedgekeurd voor export. Verwijder of herschrijf een treffer niet automatisch (geen automatische CON-repair, DEF-638).
- Of de definitie inhoudelijk *past* bij de context (algemene contextpassendheid) is een andere vraag dan CON-01 en valt onder DEF-742.

## Checklist voor het Beoordelen van een Definitie

1. ☐ Begint met een zelfstandig naamwoord (geen lidwoord, werkwoord of meta-woord)
2. ☐ Volgt genus-differentia structuur
3. ☐ Genus is direct bovenliggend begrip (niet te hoog, niet te laag)
4. ☐ Differentia onderscheidt van zusterbegrippen
5. ☐ Bevat noodzakelijke EN voldoende kenmerken
6. ☐ Eén begrijpelijke zin
7. ☐ Geen circulaire verwijzing
8. ☐ Afbakening en functiegrond beoordeeld, betekenis behouden (ESS-01)
9. ☐ Geen vage of subjectieve termen
10. ☐ Geen registratiecontext in de zin; een opgenomen naam is noodzakelijk en gemotiveerd (CON-01)
11. ☐ Betekenisniveau en aard blijken uit de kern, niet uit een label of markerwoord; inhoudelijk oordeel blijft "nog te beoordelen" tot menselijke beoordeling (ESS-02)
