# INT-02 — review van onderzoekslijn A op onderzoek B (v1)

25 september 2026 · DEF-771 · fase **wederzijdse review** · reviewer: onderzoekslijn A (Claude Code CLI). A's eigen v1 (`onderzoek-a-v1.md`, SHA-256 `ea59e45b…`) was opgeslagen vóór het lezen van B.

**Beoordeelde versies** (SHA-256 door A nagerekend. Alle B-bestanden komen overeen met `manifest-b-v1.json`):

| Bestand | SHA-256 |
|---|---|
| `b-codex-cli/onderzoek-b-v2.md` (leidend) | `8312616f41ed56039530a838e04572155598f7000f09b8333adaaa9e2652474f` |
| `b-codex-cli/casusregister-b-v2.md` | `1ad33b10aabd57d5f612035d046a8af4cb5d0333546ca1d6d5afcdaa2683865e` |
| `b-codex-cli/manifest-b-v1.json` | `fcac4dd19424fac5a1de12deebb79960a39d8f5465618b304f5c80b8a83b0b0a` |
| `b-codex-cli/bewijs/proefplan-v1.md` · `proeven-b-v1.py` · `proefuitkomsten-v1.json` · `uitvoering-v1.json` | `945a7e32…` · `ab96c3a1…` · `87469133…` · (manifest `3ae91ec8…`) |
| `a-cowork/normlezing-coordinator-v1.md` · `a-cowork/bewijs/proef-c1-uitkomsten.json` | `d48f0e2c…` · `25a333e7…` |

Bronextracten van B zijn niet volledig gelezen; waar nodig is gericht in de repo nagekeken. Nieuwe proef P3 (klein, offline, verwachting vooraf): [`bewijs/proef-p3-int10-melding.py`](bewijs/proef-p3-int10-melding.py), [`bewijs/p3-uitkomsten.json`](bewijs/p3-uitkomsten.json), [`bewijs/proeflog-a-v2-p3.md`](bewijs/proeflog-a-v2-p3.md).

Formaat per punt: **punt-ID → beoordeelde claim/sectie/versie → oordeel → bron of tegenbewijs → gevolg/correctie**.

## A. Norm en besluitstatus

**RA-B-01** → B v2 §Q1 F01/I01/V01 en casusregister C02 tegenover C52/C03 → **tegengesproken (interne inconsistentie)** → B zet C02 (ASTRA-ONJUIST, "moet ondersteunen") op VN "in de bedoelde ASTRA-voorbeeldlezing" zonder normvoorbehoud (`casusregister-b-v2.md:14`). C52 ("die de behandelaar moet afwijzen") en C03 zijn alleen VN onder N-B1 en open onder N-A (r. 15, 21). C02 is echter precies een verplichting **zonder** discretie: onder B's eigen N-A ("alleen discretionaire beslisregels", §Q1 r. 64) is C02 dus geen INT-02-VN. ASTRA's enige ONJUIST-voorbeeld bij INT-02 (`astra-INT-02-raw.wikitext`, `Voorbeelden=`) illustreert dus een gedragsverplichting, geen afweging → **gevolg:** (1) de C02-rij krijgt dezelfde varianttekst als C52: "VN onder N-B1; onder N-A geen INT-02-VN". (2) De synthese moet benoemen dat N-A het eigen ASTRA-voorbeeld van de regel niet dekt. Dat is een sterker argument voor N-B1 dan "ASTRA-achtergrond". De bronredactie noemt het voorbeeld wel "niet erg sprekend". **Beslissende casus: C02.**

**RA-B-02** → B §Q1 V01 (N-B1) tegenover A's N-A1 (`onderzoek-a-v1.md` §1.2/§5.1) en de normlezing van de coördinator (§1, §4) → **bevestigd (inhoudelijk gelijk), aangevuld op formulering** → Alle drie onderscheiden twee verboden functies: voorschrift/procedure en discretionaire afweging. Afleiding en criteria in voorwaardelijke vorm staan ze toe. B's N-B1 = A's N-a + N-b. Verschil in formulering: A zegt "kenmerken die voor elke instantie vaststaan". De coördinator zegt "deterministisch toepasbaar … zó dat twee bevoegde lezers tot hetzelfde antwoord komen" (`normlezing-coordinator-v1.md:9, 40`). B's C55 ("voorwerp met een waarneembare onderbreking van het oppervlak": menselijke waarneming is geen actordiscretie) en ESS-04-besluit N2 (kwalitatieve criteria kunnen volstaan) laten zien dat een determinisme- of eensluidendheidseis INT-02 in ESS-04-toetsbaarheid verandert → **gevolg:** de synthese neemt B's onderscheid over: epistemisch oordeel ≠ actorafweging. De formuleringen van A en de coördinator moeten vervallen voor zover ze meetbaarheid of eensluidendheid suggereren. Voorstel voor de normzin: "…kenmerken die bepalen wat tot het begrip behoort; de uitkomst hangt niet af van een afweging die aan een actor is overgelaten". **Beslissende casus: C55** (V onder B; onder een strikte determinismelezing mogelijk VN).

**RA-B-03** → B §Q1 F01, laatste alinea (gelijkstelling "beslisregel = ieder voorschrift" niet als letterlijke bronregel presenteren; N-B1 = lokale operationalisering) → **bevestigd; corrigeert A** → ASTRA gebruikt "Dat lijkt op" en de Redactieopmerking vraagt of de afbakening "voldoende omlijnd" is (feitenbasis §1). A v1 §1.2 labelde N-b als interpretatie [I], maar formuleerde "uit de drie pagina's volgen twee verboden functies" te stellig → **gevolg:** de synthese labelt N-b als "lokale operationalisering met ASTRA-steun (voorbeeldpaar + Achtergrond)", met RA-B-01 als belangrijkste steun.

**RA-B-04** → B §Q1 I01 en casusregister C04/C05/C57 (v2-correctie) → **bevestigd; corrigeert A** → C57: "even ⇔ deelbaar door twee" is waar voor élk geheel getal. Die definitie bakent dus alle gehele getallen af, geen even getallen. De logica van B klopt. Hetzelfde geldt voor het paar C04/C05: C04 zegt "Getal", C05 "Geheel getal", dus geen bewezen gelijke betekenis. A v1 noemde C05 "zelfde betekenis zonder indien" en C04→C05 een "stijlvoorstel" (casusregister-a-v1 rij C04/C05; §5.4) → **gevolg:** A trekt de equivalentieclaim in. In H wordt C04→C05 een betekenisveranderend voorstel (klassebeperking toegevoegd) dat menselijke bevestiging vraagt. Het is geen stilistische omzetting.

**RA-B-05** → B §Q1/§Q3 (rechtsgevolg beschrijven ≠ voorschrijven; C53, C69, C59) → **bevestigd** → Dit komt overeen met A's voorkeur bij B-6 (C16, C30). B maakt het scherper met C69 ("aanvraag waarover een besluit tot afwijzing is genomen") en C59 (het begrip beslisregel definiëren is geen beslisregel) → **gevolg:** B-6 van A is geen open keuze meer tussen A en B. Beiden kiezen "beschrijven = V". Alleen de grenscasus C16 ("wordt opgelegd wanneer") blijft een reviewervoorbeeld.

**RA-B-06** → B §Q2 B01 (K-9 appbreed: zonder context niet genereren en niet toetsen; C56 → NE) → **bevestigd; corrigeert A materieel** → `ESS-05-verdieping/onderzoek-20260921/gedeeld/besluiten-v1.md:16`: "K-9 | Context is op appniveau verplicht: zonder context wordt niet gegenereerd en niet getoetst." A v1 §2 (veldrollenmatrix, rij context) schreef "Zonder context mag het INT-02-oordeel wel (intrinsiek). Algemene contextplicht = ESS-05-K-9/CON-01, niet INT-02". Dat botst met een bestaand appbreed besluit → **gevolg:** A neemt B's positie over. Ontbrekende context betekent `not_evaluated` vóór de INT-02-beoordeling. Dit is uitvoering van bestaand beleid, geen nieuwe keuze voor Chris. A-casus C29 blijft geldig; A-casussen zonder context (C01–C27 in P1) zijn alleen routebewijs. Inhoudelijk wordt de context-onafhankelijkheid van het INT-02-oordeel onderscheiden van de appvoorwaarde.

## B. Proeven, bronbinding en hergebruik

**RA-B-07** → B P1 (`proeven-b-v1.py:35`, `proefuitkomsten-v1.json` "violations": []) en §Q1 F02: "'De app verbiedt indien' is dus te ongenuanceerd: G verbiedt het, T signaleert het en laat het oordeel open." → **tegengesproken (voor de app als geheel), aangevuld** → B filtert violations op `code == "INT-02"`, waardoor buurregels buiten beeld blijven. A-P1 (`bewijs/p1-uitkomsten.json`): alle 8 `indien`-teksten krijgen een **gescoorde INT-10-fail**, geen enkele tekst zonder `indien`. A-P3 (`bewijs/p3-uitkomsten.json`, met context): C04 geeft INT-10 `severity "error"`/`severity_level "critical"`, message "Verboden patroon gedetecteerd: \bindien\b", suggestion **"Herschrijf de zin zodat de gedetecteerde patronen niet voorkomen."** INT-01 geeft `warning`. C05 geeft beide pass. Oorzaak: `INT-10.json:15` (`\bindien\b`, generic/automated/scored) → **gevolg:** de claim van B klopt voor de INT-02-evaluator, maar niet voor de gebruiker. De app keurt `indien` af met score en ❌-melding en adviseert het woord te verwijderen. Dat is een verkapt woordverbod buiten INT-02, dat tegen N-B1 én N-A1 ingaat. De synthese moet dit als **materieel ketenfeit** opnemen (A's B-7). Het is een punt voor de eigenaar van INT-10 en INT-01, geen INT-02-normbesluit.

**RA-B-08** → B §Q5 V07, laatste alinea ("De huidige INT-02-review creëert geen violation voor de bestaande enhancement; dat is geen bewijs van een volwaardig H-contract") → **bevestigd, aangevuld** → `definition_orchestrator_v2.py:1263-1275, 1976-1999`: gewone violations (dus ook INT-10/INT-01 op `indien`) zijn "herstelbare overtredingen" voor de enhancement-service. Die staat nu op `None` (`container.py:384`) → **gevolg:** latent H-risico. Bij activering (DEF-638) stuurt een `indien`-violation een herschrijving aan die een criterium kan schrappen (A-C31, B-C63-type). Opnemen als stopvoorwaarde en als voorwaarde vóór activering: patroonviolations zonder normgrond mogen geen herstel aansturen. Codelezing; niet uitgevoerd.

**RA-B-09** → B §Q4 W01/P4 (hergebruikgrens: record bytegelijk, `_signalen` AST-gelijk, `evaluate` niet) → **bevestigd** → `uitvoering-v1.json`: exit_status 0, start/end UTC, stdout en stderr bewaard. A deed dezelfde vaststelling met `git diff` en herhaalde C01–C06 met identieke uitkomst (A-proeflog V7). Twee onafhankelijke routes komen dus tot dezelfde hergebruikgrens → **gevolg:** geen. De bronbinding van B is sterker dan die van A (exit en stdout machinaal vastgelegd; bij A overgenomen uit de tooluitvoer).

**RA-B-10** → B proefplan "vooraf" (`proefplan-v1.md`) → **onvoldoende bewezen (alleen de volgorde)** → Het proefplan heeft geen tijdstempel of hash van vóór de run. Het manifest geeft alleen de eindhash. Hetzelfde geldt voor A (`verwachtingen-a-v1.md`). Mtime is geen bewijs → **gevolg:** niet materieel. Aanbeveling voor volgende rondes: verwachtingsbestand hashen en de hash in de uitvoeringslog opnemen vóór de run.

**RA-B-11** → B §Q4 F04: routes voor import, opslag, expertreview en status → **grotendeels bevestigd; corrigeert A** →
- Import: `csv_importer.py:273-275` (`if auto_validate: … pass`) bevestigd. A v1 §4 nam "import valideert niet" over uit de feitenbasis. B's onderscheid tussen twee codepaden is juister.
- Opslag: `models.py:136-162` vertaalt alleen `violations` naar `validation_issues`; review_required reist niet mee. Bevestigd.
- Status: `not_applicable` bestaat (`validation_view.py:325`). A gebruikte de vijfstatuslijst uit de feitenbasis.
- `expert_review_tab.py:1079` = CON-02-correctie: niet door A nagekeken.
- `definitie_origineel` is al opgeschoond (F04, genereren): niet door A nagekeken.

→ **gevolg:** de synthese neemt de routetabel van B als basis en voegt uit A toe: (a) de gate leest `severity` en niet `severity_level` (`definition_workflow_service.py:741`; P3: INT-10 `error`, dus "Kritieke issues" wordt niet geraakt; codelezing), (b) RA-B-07/08.

## C. Veldrollen, G, T en H

**RA-B-12** → B §Q2 V02 (veldrollenmatrix) → **bevestigd; vollediger dan A** → B voegt regelbron/normversie en review/status/actor als eigen velden toe en onderscheidt betekenisgrond van gevalsbewijs (C50). A's matrix mist deze → **gevolg:** de synthese gebruikt de matrix van B, met de correctie uit RA-B-06 (die B al toepast).

**RA-B-13** → B §Q5 V05 (G) → **aangevuld (materieel voor G)** → B's G vraagt om "Lever bronverantwoording en eventuele procesinformatie afzonderlijk" en "meld de ontbrekende keuze afzonderlijk … de voorlopigheid buiten de definitiezin zichtbaar". Het bestaande uitvoercontract van de generatie is één zin, alleen de kern. ESS-03-G heeft dit bewust zo opgelost: "De gerichte verduidelijkingsvraag … loopt binnen het bestaande uitvoercontract (één zin, alleen de definitiekern) via de ESS-03-beoordeling" en "zonder melding of toelichting in de zin" (`json_based_rules_module.py:335-339, 348-354`). A's G heeft hetzelfde gebrek ("hoogstens als afzonderlijk toelichtingsvoorstel") → **gevolg:** G van beide aanpassen aan het ESS-03-patroon. Het model levert één kern zonder procesregel. De vraag naar een ontbrekende keuze loopt via T (uitkomst O met één vraag). Een afzonderlijk toelichtingskanaal alleen als het apart wordt ontworpen en besloten. Geen ongedekte uitvoerwens in de prompt.

**RA-B-14** → aansluiting G↔T↔H bij B (V05/V06/V07) → **bevestigd, met één ketenvoorbehoud** → Dezelfde functiegrens en dezelfde uitzonderingen (afleiding, criteria, constitutief rechtsgevolg) in alle drie. H "zet een plicht niet om in een feit" sluit aan op T C63 ("niet als bewezen V") en op G "vermijd ze niet ten koste van betekenis". Geen betekenisverlies in het ontwerp. Voorbehoud: G zegt "'indien' … toegestaan", terwijl de app-T via INT-10/INT-01 `indien` afkeurt en adviseert het te verwijderen (RA-B-07). Zolang dat bestaat, sluiten G en de feitelijke toetsing niet op elkaar aan → **gevolg:** in de synthese G-wijziging en INT-10/INT-01-behandeling koppelen, of het G-effect meten met en zonder die buurafkeur.

**RA-B-15** → B §Q5 V06 (T, uitkomsten, statusmapping) → **bevestigd; beter dan A** → B onderscheidt O (inhoudelijk onvoldoende grond), "nog te beoordelen — beoordeling niet uitgevoerd", NE (ontbrekende kern of context), E en NA (alleen met grond; afleiding is V, niet NA). A's NB valt samen met NE → **gevolg:** de synthese neemt B's uitkomstenschema en meldingen over. A's gebruikersformuleringen voor VN(N-a) en VN(N-b) kunnen als varianten van B's VN-melding dienen.

**RA-B-16** → B V06 reviewerhulp (volledig relevant zinsdeel citeren, geen losse regextreffer) → **bevestigd** → `judgment_review.py:176-192` citeert alleen `hit.group()`, dus bij INT-02 het woord "indien". A's O1-tekst erfde dat gedrag → **gevolg:** in O1 de omringende bijzin of zin citeren (met positie). Niet materieel voor de norm, wel voor de bruikbaarheid.

**RA-B-17** → B V04/V08 (patronen alleen als hulpmiddel; geen nieuwe signalen) tegenover A §5.1 en coördinator §4 (nieuwe voorschrift- en discretiesignalen) → **beleidskeuze** → C1 (coördinator) en A-P1: C02, C13/C83, C14 en C15/C52 geven geen signaal; nieuwe signalen zouden die aanwijzen. Tegenargument van B (K-8, §Q3): "moet" als signaal verdubbelt ARAI-04. "redelijk" en "passend" raken ARAI-03 → **gevolg:** aan Chris voorleggen als O1-detail. Voorkeur A blijft: beperkte uitbreiding met discretiemarkers ("van oordeel", "naar eigen inzicht", "acht"), zonder "moet". **Beslissende casussen: C13, C83** (discretie zonder woord) en C52 (verplichting, al gedekt door ARAI-04).

**RA-B-18** → B §Q5 V07 (H) → **bevestigd** → Diagnose vóór advies, één poging, het origineel bewaren, stoppen bij grond- of betekenisverlies. C63/C64/C65 zijn beter onderscheidend dan A's C31/C32 (C64 is een positief herstelgeval, dat A mist) → **gevolg:** de synthese gebruikt C64 als positief H-geval en voegt RA-B-08 toe als activeringsvoorwaarde.

## D. Relaties, voorstellen en dekking

**RA-B-19** → B §Q3 (ARAI-04SUB1 "verwijst zelf naar Geen beslisregel") → **bevestigd** → `ARAI-04SUB1.json:31-32` (`relatie` → "Geen beslisregel") → **gevolg:** extra steun voor overlap zonder conflict (moet-vorm bij ARAI-04, functie bij INT-02).

**RA-B-20** → B §Q3 (relatietabel) → **aangevuld** → B noemt INT-10 niet (zie RA-B-07). B noemt ook niet dat het generatieprompt-voorbeeld van STR-09 ✅ `indien` bevat, of dat de ESS-03-G "behoud … voorwaarden" in dezelfde prompt staat als INT-02 "vermijd indien" (A-P2 `p2-uitkomsten.json`; de coördinator noemt het conflict met ESS-03/04/05 ook, §3) → **gevolg:** in de synthese opnemen als bewezen G-context. Onder N-B1 verdwijnen beide spanningen.

**RA-B-21** → B §Q5 V08 (vervangtabel skills, prompt, record) → **bevestigd, nagenoeg gelijk aan A §5.5** → Zelfde vindplaatsen (`json_based_rules_module.py:377`, `reference.md:63`, `definitie-nederlandse-definities/reference.md:186`, nieuw `references/int02-beslisregel.md`). B voegt een SKILL.md-blok en de canonieke-kopieregel toe, net als bij ESS-03. Verschil: B behoudt `review_policy` zonder de `example_pair_reason` te corrigeren. A corrigeert die. De coördinator schrijft dat de reden het paar "terecht" als ARAI-04- én INT-02-geval ziet (`normlezing-coordinator-v1.md:32`) → **beleidskeuze (klein)** → de huidige tekst "verschilt uitsluitend in het modale werkwoord moet, wat de norm van ARAI-04 is" legt de INT-02-functie niet uit. **Beslissende casus: C02** (samen met RA-B-01).

**RA-B-22** → coördinator §1 "het 'moet' draait ook de rollen om (organisatie moet de eis steunen ↔ de eis steunt de organisatie)" → **onvoldoende bewezen** → "eis die een organisatie ondersteunt" is in het Nederlands dubbelzinnig: de organisatie kan onderwerp of lijdend voorwerp zijn. De ONJUIST-zin maakt de organisatie onderwerp. De JUIST-zin laat beide lezingen toe → **gevolg:** in de synthese niet als bronfeit over het voorbeeld opnemen. Wel is dit een extra argument voor een sprekender paar (redactiewens ASTRA; A's B-5).

**RA-B-23** → dossierdekking B (veertien onderdelen) → **aangevuld (niet materieel)** → B heeft geen expliciete dekkingstabel. Inhoudelijk zijn alle onderdelen aanwezig: 1–3 in §Q1, 4–7 in de V02-matrix, 8 en 10 in §Q4, 9 in V08, 11 in P1–P4, 12 in §Q3, 13 in §Q5 en V10, 14 in V09 en het register → **gevolg:** de synthese voegt één dekkingstabel toe.

**RA-B-24** → B §Q6 V09 (effectevaluatie) → **bevestigd, aangevuld** → Sterker dan A: minimaal zes nieuwe hold-out-gevallen, twee runs per variant en scenario, gemeten op verbeterd/gelijk/verslechterd/onbeslist → **gevolg:** toevoegen als behoudcriterium: het aantal gescoorde afkeuren (INT-10/INT-01) op V-casussen met `indien` (nu: 6 van 6 in A-P1) en het aantal meldingen "herschrijf zodat patronen niet voorkomen" op criteria.

## E. Besluitpunten B (K1–K5) tegenover A (B-1…B-9)

**RA-B-25** → B §Q6 V10 tegenover `onderzoek-a-v1.md` §8 → **overwegend overeenstemming; drie verschillen** →

| B | A | Oordeel | Beslissende casus |
|---|---|---|---|
| K1 (N-A tegenover N-B1; voorkeur N-B1) | B-1 (functie, geen vorm) + B-3 (N-b erbij) | Gelijk. Het "of voorwaarden"-verbod vervalt bij beide. De N-A/N-B1-keuze = A's B-3 | C02 (RA-B-01), C52/C03 tegenover C50 |
| — (ingebed in N-B1) | B-2 (lidmaatschapscriteria in voorwaardelijke vorm) | Gelijk. Geen aparte keuze nodig als K1 volgens voorkeur wordt besloten | C04, C54 |
| — (ingebed in N-B1, C53/C69) | B-6 (rechtsgevolg) | Gelijk (RA-B-05) | C16, C53, C69 |
| K2 (O1 nu, O2 afzonderlijk, O3 alleen ondersteunend) | B-4 | Gelijk | C51/C12, C52/C15, C55 |
| K3 (record, voorbeeld, prompt en skills als één contract) | B-5 + §5.5 | Gelijk, behalve de `example_pair_reason` (RA-B-21) | C02 |
| K4 (geen zelfstandige INT-02-poort, expliciet laten besluiten) | Niet als besluit. A leidde "geen gate" af uit het besluit van 15-09 | **Verschil: B is beter.** Een ontbrekende gate is niet hetzelfde als een besluit. Overnemen | C67; gate-codelezing |
| K5 (H niet activeren; één poging onder DEF-638) | §5.4, niet als besluit | Gelijk in inhoud. B maakt er terecht een keuze van | C63–C65 |
| — | **B-7 (`indien` in INT-10/INT-01)** | **Verschil: ontbreekt bij B** (RA-B-07). Materieel | C04, C11, C26; P3 |
| NE bij leeg of geen context (V06, C06/C56) | B-8 | Gelijk. Volgens RA-B-06 is dit uitvoering van bestaand beleid, geen keuze | C06, C56 |
| UI toont de reden (V08) | B-9 | Gelijk. Herstel van zichtbaarheid, geen normkeuze | C03, C50 |

→ **gevolg:** de synthese voegt K4 van B en B-7 van A toe aan de besluitenlijst. A's B-2 en B-6 vervallen als aparte keuzes (ze zijn opgenomen in K1). B-8 wordt "bestaand beleid uitvoeren".

## Afsluitende lijst

**Materieel (moet de synthese veranderen):**
1. RA-B-07/RA-B-08: `indien` wordt via INT-10 (gescoord, `error`/`critical`, "herschrijf zodat patronen niet voorkomen") en INT-01 afgekeurd, en kan latent herstel aansturen. Dit ontbreekt bij B.
2. RA-B-01: C02 is onder N-A geen INT-02-VN. B's casusregister is hier inconsistent. Het ASTRA-eigen voorbeeld is het beslissende argument in de N-A/N-B1-keuze.
3. RA-B-06: de K-9-contextplicht geldt appbreed. Dit corrigeert A v1 §2.
4. RA-B-04: C04 en C05 zijn niet betekenisgelijk. Dit corrigeert A's casusregister en H.
5. RA-B-13: G van A én B moet binnen het uitvoercontract van één zin blijven (ESS-03-patroon). Een verduidelijkingsvraag loopt via T.
6. RA-B-02: de normformulering mag geen determinisme- of eensluidendheidseis bevatten (C55, ESS-04 N2). Dit raakt A en de coördinator.
7. RA-B-25: K4 (expliciet besluit over de poort) toevoegen.

**Niet materieel:** RA-B-03, 05, 09, 10, 11, 12, 14 (voorbehoud valt onder punt 1), 15, 16, 18, 19, 20, 21 (behalve de keuze), 22, 23, 24.

**Keuzes voor Chris:**
- N-A tegenover N-B1 (K1/B-3; casus C02, C52).
- O1 tegenover O2 (K2/B-4).
- Signaaluitbreiding (RA-B-17; C13, C83).
- `example_pair_reason` en een sprekender voorbeeldpaar (RA-B-21, RA-B-22; C02).
- Een zelfstandige INT-02-poort ja of nee (K4).
- Activering en grenzen van H (K5).
- Doorgeven van het INT-10/INT-01-`indien`-punt aan de eigenaars van die regels (B-7).
