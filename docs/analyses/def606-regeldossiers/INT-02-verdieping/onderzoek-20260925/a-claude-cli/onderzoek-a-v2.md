# INT-02 — Geen beslisregel · onderzoek onderzoekslijn A (v2, herzien advies)

25 september 2026 · DEF-771 (parent DEF-606) · onderzoekslijn A (Claude Code CLI) · fase **verwerking door beiden**. Onderzoek, geen normbesluit en geen implementatieopdracht. De structuur van v1 is behouden. Gewijzigde passages zijn gemarkeerd met "(v2: RB-A-nn / RA-B-nn)". Per-punt-verwerking: [`verwerking-a-v1.md`](verwerking-a-v1.md). Oorspronkelijke eerste versie: [`onderzoek-a-v1.md`](onderzoek-a-v1.md) (ongewijzigd, SHA-256 `ea59e45b…`).

**Labels.** [F] bronfeit · [B] vastgelegd besluit · [W] waarneming/proef · [I] interpretatie van A · [V] voorstel van A. Casussen: [`casusregister-a-v2.md`](casusregister-a-v2.md) (vervangt v1 waar verwachtingen wijzigen). Proeven: [`bewijs/`](bewijs/) (P1, P2, P3).

## 0. Startpositie, toegang en leesbasis

| Punt | Waarde |
|---|---|
| Leesbasis | HEAD `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`, checkout-branch `onderzoek/DEF-772-INT-03-20260925`. De commit is gelijk aan de opgegeven main-HEAD; er zijn geen getrackte wijzigingen. |
| Hergebruik historisch bewijs | Record ongewijzigd sinds `d68a98a9`. Het evaluatorbestand is gewijzigd voor andere regels, het INT-02-pad niet. C01–C06 opnieuw gemeten met identieke uitkomst. B komt via een AST-vergelijking tot dezelfde smalle hergebruikgrens (RB-A-11). |
| Toegang | Zoals in v1: `src/services/definition/cleaning_service.py` bestaat niet, het werkelijke pad is `src/services/cleaning_service.py`. |
| Werkwijze en bronbinding | Geen agents, geen modelcalls, geen netwerk en geen repo-wijzigingen. (v2: RB-A-09) Exit 0 is **gerapporteerd of afgeleid uit de tooluitvoer**, niet machinaal vastgelegd, omdat shell-omleiding was geweigerd. Model van deze sessie: claude-opus-5-5 (omgevingsgegeven); de CLI-versie is niet vastgesteld. Bij latere proeven exit, tijden en versies machinaal vastleggen. |

## 1. Q1 — Norm, lokale aanvullingen, toepasselijkheid en uitzonderingen

### 1.1 Wat ASTRA waarborgt [F]

Ongewijzigd ten opzichte van v1 (Regel, Toelichting met afleidingsregel toegestaan en verplicht, Achtergrond actieregel/definitional rule, voorbeeldpaar met redactieopmerking, Beslisregel-pagina met het Ppw-voorbeeld, Afleidingsregel-pagina). B bevestigt dit (RB-A-01).

### 1.2 Interpretatie van het normdoel [I]

(v2: RB-A-02, RB-A-03, RA-B-02) ASTRA onderscheidt **functie**, niet **zinsvorm**. Daaruit volgen twee functies die niet in een definitiekern horen, en één toegestane functie:

1. **N-a: geen discretionaire beslisregel.** De definitie voert geen afweging uit die aan een actor is overgelaten en schrijft zo'n afweging ook niet als handelingsrichtlijn voor (Ppw: "tenzij hij van oordeel is …"). Rechtstreeks gedragen door de ASTRA-Regel en de Beslisregel-pagina.
2. **N-b: geen gedragsvoorschrift of procedure als definitiekern.** Dit is een **lokale operationalisering met ASTRA-steun**: de Achtergrond (actieregel, "obligation concerning conduct") en het ASTRA-voorbeeldpaar, waarvan het ONJUIST-lid een verplichting zonder afweging is. ASTRA zegt "lijkt op" en de redactie vraagt of de afbakening "voldoende omlijnd" is. De grens is dus niet uitputtend door de bron bepaald en ligt ter keuze bij Chris (K1).
3. **Toegestaan, en voor afleidbare begrippen de aangewezen vorm:** begripsbepalende kenmerken en een deterministische afleiding, ook in voorwaardelijke zinsvorm.

(v2: RB-A-02) Een **universele eis van determinisme of eensluidendheid volgt niet uit de bron**. Het deterministische algoritme hoort bij afleidbare begrippen. Een kwalitatief kenmerk dat menselijke waarneming vraagt (B-C55; ESS-04-N2) is geen discretionaire beslisregel. De v1-formulering "kenmerken die voor elke instantie vaststaan" betekent alleen: het kenmerk geldt voor de bedoelde instanties. Het is geen eis van een algoritme, van absolute zekerheid of van overeenstemming tussen beoordelaars.

(v2: RB-A-05) Het ASTRA-paar verschilt in "moet". Dat raakt modaliteit en kan een verplichting uitdrukken. Of de definitie daardoor zelf als actorvoorschrift functioneert, vergt een betekenisbeoordeling. Een rolomkering ("de eis steunt de organisatie") is niet bewezen, omdat de JUIST-zin dubbelzinnig is. Onder de enge variant (N-a alleen) is het ONJUIST-voorbeeld van ASTRA géén INT-02-overtreding. Dat is het belangrijkste argument voor N-b, maar ASTRA noemt het voorbeeld zelf "niet erg sprekend".

(v2: RB-A-04) **Beschrijven is niet voorschrijven.** Een bevoegdheid, beslissing, procedure of constitutief rechtsgevolg beschrijven als kenmerk van het begrip is op zichzelf geen overtreding. Voorbeelden: B-C53 vernietiging, B-C69 afgewezen aanvraag, B-C59 het begrip beslisregel, A-C30. Het gaat erom of de definitiekern zelf het handelen voorschrijft of de actorafweging als beslisregel uitvoert.

### 1.3 Lokale aanvullingen [F] en hun beoordeling [I]

Als v1, met twee wijzigingen:
- Rij `brondocument` (v2: RB-A-01): voorgestelde vermelding "ASTRA (verwijst naar DBT §4.2; DBT niet rechtstreeks onderzocht)".
- Rij patronen: de tellingen blijven bestaan, maar zijn **verwachtingen onder N-A1, geen semantische nulmeting** (RB-A-24).

### 1.4 Toepasselijkheid en uitzonderingen

- **Toepasselijk:** alle definities. Een afleidingsregel **voldoet**; het is geen niet-toepasselijkheidsklasse (v2: RB-A-01).
- **Noodzakelijke lidmaatschapscriteria**, ook in voorwaardelijke vorm, vallen niet onder het verbod. (v2: RB-A-20) Dezelfde toegestane functie betekent niet dezelfde logische afbakening. "X indien Y" geeft een voldoende voorwaarde, "alleen als" een noodzakelijke. Herformuleringen (C04→C05, C11→C10, C17→C18) zijn **niet** als betekenisgelijk bewezen.
- **Begripscriterium tegenover voorschrift of procedure:** de vraag is of de kern vastlegt wat tot het begrip behoort, of voorschrijft wat een actor moet doen of mag afwegen. (v2: RB-A-04) Is die functie met de beschikbare betekenisgrond onbeslist, dan is de uitkomst *onvoldoende informatie* met één gerichte vraag. Woorden als "oordeel", "redelijk", "opgelegd" of "wanneer" beslissen dat niet.
- **Grensgevallen:** rechtsgevolg of grondslag (C16) valt onder de beschrijvingsregel hierboven. "wanneer→wegens" lost de ambiguïteit niet op (RB-A-23). Een onbepaalde voorwaarde (C24) wordt *onvoldoende informatie*; onder de brede norm kan ook een deterministisch voorschrift VN zijn (RB-A-23). "kan" als vermogen is ARAI-04-terrein.
- **Niet onderbouwd als uitzondering:** een categorielabel of een juridische bron als zodanig. Een bronvoorschrift mag niet klakkeloos als definiens worden gekopieerd (RB-A-04).

## 2. Q2 — Invoer, onderbouwing, ontbrekende of strijdige informatie

(v2: RB-A-06, RA-B-06) [B] **Context is op appniveau verplicht:** zonder context wordt niet gegenereerd en niet getoetst (`ESS-05-verdieping/onderzoek-20260921/gedeeld/besluiten-v1.md:16`, K-9). Dit is geen keuze voor Chris.
- De INT-02-evaluator gebruikt vandaag geen context. P1-C29 is identiek aan C03, en de service voert ook zonder context uit (A-P1, B-P1-C56): een uitvoeringskloof.
- Onderscheid: of een kern intrinsiek menselijk beoordeelbaar is, verschilt van de appvoorwaarde. Ontbreekt context, dan is de uitkomst *niet uitgevoerd* met reden, niet VN en niet een stille pass.
- Een bronpassage is nodig wanneer de functie ervan afhangt, niet bij elk intrinsiek helder criterium (B-C68). Gevulde contextlijsten zijn geen betekenisbewijs.
- Strijdige grond: geen stil compromis, één gerichte vraag (B-C60).

**Veldrollenmatrix** (v2: RB-A-07; aangevuld naar B's V02):

| Veld | Zelf toetsobject en criterium | Bewijs voor ander oordeel | Invoer bij generatie | Mag AI dit opleveren/wijzigen? | Herkomst, ontbrekend/conflicterend |
|---|---|---|---|---|---|
| Definitiezin (kern) | Ja: functie (criterium/afleiding tegenover voorschrift/afweging) | — | Resultaat | Bij G ja; bij T nooit; H alleen apart op verzoek | Leeg → niet uitgevoerd. Versie binden (ruw/geëxtraheerd/getoetst/opgeslagen) |
| Term + bedoelde betekenis | Nee; een woord in de term is geen signaal (C21) | Onderscheidt referent, bijv. procedurebegrip tegenover uitvoering | Term verplicht; betekenis waar meerduidig | Geen stille vervanging of vernauwing | Conflict → gerichte vraag |
| Context (org./jur./wettelijke basis) | Nee | Domein en lezing; geen volledig betekenisbewijs | **Verplicht (K-9)** | Niet verzinnen of wijzigen | Ontbrekend → geen G/T; strijdig → OI met vraag |
| Definitiebronnen/passages | Nee (CON-02) | Herkomst van criterium, plicht, uitzondering of discretie | Ondersteunend; noodzakelijk waar de functie ervan afhangt | Citeren met herkomst; niets verzinnen | Alleen procedure in de bron → geen kern verzinnen (C33) |
| Ontologische categorie | Nee | Zwak: helpt lezen, beslist niet | Ondersteunend | Nee (ESS-02: claim) | — |
| **Ontologische relaties** | Nee | Bovenbegrip, constitutieve relatie, afleiding; geen categorieoordeel | Ondersteunend | Alleen aangeleverd of bevestigd | Ontbrekend blokkeert als de functie ervan afhangt |
| Voorbeelden | Nee | Illustreren lidmaatschap; gegenereerd ≠ bevestiging | Optioneel | Gemarkeerde voorstellen | — |
| **Praktijkvoorbeelden** | Nee | Herkomstgebonden toepassingsbewijs | Niet nodig | Geen verzonnen praktijkbewijs | Gevalsbewijs ≠ definitiegebrek |
| **Tegenvoorbeelden / grensgevallen** | Nee | Uitsluiting of onzekerheidsgrens; geen normbewijs | Ondersteunend | Gemarkeerde voorstellen | Reviewer bevestigt bedoeling |
| **Synoniemen/homoniemen** | Nee | Verduidelijken referent of tonen ambiguïteit (handeling/resultaat/criterium) | Relevant bij meerduidigheid | Geen stille term- of betekeniskeuze | Onbeslist → OI |
| Bedoeling/toelichting | Nee (apart kanaal) | Betekenisgrond | Ondersteunend | Geen noodzakelijk kenmerk naar de toelichting verplaatsen | Tegenstelling met kern zichtbaar |
| Regelbron/normversie | Nee | Bepaalt N/G/T-versie | Verplichte instructiegrond | Nee | DEF-625 |
| **Reviewmetadata** | Nee | Binding aan tekst én context/bron/normversie | — | AI verzint geen goedkeuring | Oud oordeel wordt historisch na wijziging (DEF-626) |

## 3. Q3 — Relaties met andere regels

Als v1, met de volgende wijzigingen (v2: RB-A-08, RB-A-12, RB-A-13). Het zijn **geen exclusieve schotten**: elke regel motiveert zelf (ESS-05-K-8). INT-02 keurt niet af op doel, modaliteit of negatie alleen.

| Regel | Wijziging ten opzichte van v1 |
|---|---|
| ARAI-04/SUB1 | Aangevuld: `ARAI-04SUB1.json:31-32` verwijst naar "Geen beslisregel" (RA-B-19). "moet" bewijst geen INT-02-overtreding |
| INT-10 | **Ketenfeit, geparkeerd** (instructie Chris 25-09). `INT-10.json:15` `\bindien\b` is generic, automated en scored. Alle 8 `indien`-teksten falen, geen enkele andere. P3: `severity "error"`, `severity_level "critical"`, suggestie "Herschrijf de zin zodat de gedetecteerde patronen niet voorkomen" (`modular_validation_service.py:1920-1921`). Waarneming voor het latere INT-10-dossier, geen besluit in dit onderzoek. INT-02-V bewijst zelf geen INT-10-fout; daarvoor is de eigen norm van INT-10 nodig |
| ESS-03/STR-09 | Precisering: de spanning staat "in standaard geregistreerde promptmodules (module-niveau)". Verzending en modelrespons zijn niet gemeten |
| INT-08 | "Geen relatie behalve vorm" vervalt: een uitzondering of negatie kan begripsbepalend zijn (B-C58). H beschermt negatie |
| STR-06/ESS-01 | Een constitutieve doelrelatie kan begripsbepalend zijn; H schrapt doel niet om INT-02 te halen |
| INT-01 | Eigen woordlijstbesluit is open; hier geen besluit |

## 4. Q4 — Feitelijk appgedrag per ingang

(v2: RB-A-14, RB-A-15, RB-A-16, RB-A-17) Gewijzigde rijen ten opzichte van v1:

| Ingang | Waarneming (v2) | Bewijsniveau |
|---|---|---|
| Uitsluitend toetsen | Ongewijzigd: altijd `review_required`, ook bij lege tekst en zonder context (uitvoeringskloof K-9) | [W] P1 |
| Genereren | Ongewijzigd, met precisering: spanning in de standaard geregistreerde modules; opschoning apart (B-P3: label, kop en punt; `indien`/`moet` behouden in twee gevallen) | [W] P2 module-niveau; B-P3 |
| **Import** | Twee routes: `DefinitionImportService.validate_single`/`import_single` valideert (`definition_import_service.py:67-112`, bron B). De management-CSV-route schrijft een concept met `validation_score=0.0` en een no-op `auto_validate` (`csv_importer.py:245-276`, door A gecontroleerd) | Statisch; geen import-proef |
| **Expertreview** | `expert_review_tab.py:1071-1091` betreft CON-02-brononderdelen. **Een INT-02-reviewroute is niet bewezen** | Statisch (bron B) |
| UI-weergave | INT-02 verschijnt alleen als code in de statuslijst. **Statische codebevinding, geen browserproef** | Codelezing |
| **Opslag/snapshot** | Het resultaatcontract kan RR transporteren (`result_contract.py:49-68`, bron B). `issues_uit_validatieresultaat` neemt alleen `violations` over (`models.py:147`). Persistentie van reden en passage is open bewijs (DEF-626) | Statisch |
| **Vaststellen** | `_evaluate_gate` leest geen INT-02-reviewlijst. Het besluit van 15-09 **bepaalt het poortbeleid per regel niet** (besluit r. 27). Tekst van B: "De totaalscore vervalt volgens het appbrede besluit. INT-02 is momenteel uitgesloten van scoring. Geen zelfstandige INT-02-gate is gevonden; toekomstig poortbeleid is een afzonderlijke productkeuze." (→ K4). Score-None kan nog blokkeren. INT-10-gate-effect onbewezen: de gate vergelijkt `severity`, niet `severity_level` | Statisch |
| **Export** | Optionele async exportgate op uitgevoerd resultaat en `is_acceptable` (`export_service.py:400-472`, bron B). Geen vrije export en geen redenpersistentie geclaimd | Statisch; open |

Foutsoorten: als v1. Toegevoegd zijn transport- of cleaningverlies als aparte diagnose (RB-A-22) en het buurregeleffect van INT-10 als geparkeerd ketenfeit.

## 5. Q5 — Voorstellen

### 5.1 Norm (N) en record [V]

(v2: RB-A-02, RB-A-04, RB-A-05, RB-A-01) Voorstel N-A2, gelijk aan N-B1 van B in strekking:

> **uitleg:** "Een definitie bakent het begrip af met de kenmerken die bepalen wat ertoe behoort; zij is geen beslisregel die een afweging aan een actor overlaat, en geen voorschrift over wat iemand moet doen of hoe iets wordt afgehandeld."
>
> **toelichting:** "Bij een beslisregel komt oordeelsvorming kijken: wet of beleid laat een discretionaire bevoegdheid open (bijvoorbeeld 'tenzij zij van oordeel is dat …'). Ook een handelingsvoorschrift of procedure hoort niet als definitiekern (lokale operationalisering van ASTRA's achtergrond). Behoud de onderbouwde begripsbepalende kenmerken, ook in voorwaardelijke vorm met 'indien', 'mits', 'tenzij' of 'voor zover'. Een afleidbaar begrip wordt gedefinieerd met de deterministische afleiding uit de relevante feiten. Menselijke beoordeling van een kwalitatief kenmerk is op zichzelf geen discretionaire beslisregel. Het beschrijven van een bevoegdheid, beslissing, procedure of constitutief rechtsgevolg als kenmerk van het begrip is niet op zichzelf een overtreding. Beoordeel of de definitiekern zelf het handelen voorschrijft of de actorafweging als beslisregel uitvoert."
>
> **toetsvraag:** "Bakent de definitiekern het begrip af met kenmerken of een deterministische afleiding, of functioneert zij als handelingsvoorschrift, procedure of discretionaire beslisregel?"

Overige recordvelden:
- `type`: "gehele definitie".
- `brondocument`: "ASTRA (verwijst naar DBT §4.2; DBT niet rechtstreeks onderzocht)".
- `goede_voorbeelden`: ASTRA-JUIST plus C10 (gelabeld als synthetische parafrase van de ASTRA-afleidingsregel).
- `foute_voorbeelden`: ASTRA-ONJUIST plus C12 (gelabeld als synthetische bewerking van het Beslisregel-voorbeeld, bedoeld als actorinstructie).
- `example_pair_policy`: `review_policy` (ongewijzigd).
- `example_pair_reason` (v2: tekst van B, RB-A-05): "Het ASTRA-paar verschilt in 'moet'. Dat raakt modaliteit en kan een verplichting uitdrukken; of de definitie daardoor zelf als actorvoorschrift functioneert vergt betekenisbeoordeling. ASTRA noemt het voorbeeld weinig sprekend. Verwijderen van 'moet' bewijst geen betekenisbehoud."
- `herkenbaar_patronen`: alleen leeshulp. Het signaalbeleid (behouden, uitbreiden met discretiemarkers of vervangen) is een keuze binnen K2 (RB-A-19). "redelijk", "passend" en "acht" bewijzen niets.

(v2: RB-A-19) Het minimale recordalternatief uit v1 volstaat **niet** los: de hardgecodeerde G-instructie blijft dan bestaan. Record, uitleg, instructie, voorbeelden, T, skill en H worden samenhangend gewijzigd. Bij de enge keuze (K1 = N-A) worden alle teksten daarop aangepast.

### 5.2 Generatie-instructie (G) [V]

Huidig en probleem: als v1, plus het ongedekte uitvoerkanaal (RA-B-13).
**Vervanging (v2: RB-A-02, RB-A-04, RB-A-19, RB-A-20, RA-B-13):**

> "Beschrijf wat het begrip is met de onderbouwde begripsbepalende kenmerken binnen de gegeven betekenis en context. Behoud die kenmerken, ook als de bron ze als voorwaarde of uitzondering formuleert ('indien', 'mits', 'tenzij', 'alleen als'); vermijd die woorden niet ten koste van betekenis, en verander geen noodzakelijke voorwaarde in een voldoende voorwaarde of omgekeerd. Een afleidbaar begrip definieer je met de deterministische afleiding uit de relevante feiten. Gebruik geen handelingsvoorschrift, behandelprocedure of discretionaire afweging van een actor als definitiekern. Een bevoegdheid, beslissing of rechtsgevolg mag je beschrijven wanneer die het begrip bepaalt, zonder de uitoefening ervan voor te schrijven. Verzin geen criterium, bron, context of afweging om een afweging te vervangen. Een voorlopige kandidaat is alleen toegestaan voor zover de beschikbare betekenisgrond die kandidaat draagt; ontbreekt die grond of is de functie strijdig onderbouwd, maak dan geen stille keuze en verzin geen definitiekern. Lever uitsluitend de definitiekern in één zin, zonder melding of toelichting in de zin; een ontbrekende keuze komt als gerichte vraag uit de INT-02-beoordeling."

App vooraf: context aanwezig (K-9); term, betekenis en bronpassages doorgeven; ruwe uitvoer, geëxtraheerde kern en getoetste tekst bewaren. Toetsgevallen: C10/C11, C12/C13, C03/C15, C33, B-C54, B-C58.

### 5.3 Toetsinstructie (T) en evaluatorstrategie [V]

Opties O1/O2/O3 als v1. (v2: RB-A-18) Precisering van O2: precies **voldoet / voldoet niet / niet van toepassing / onvoldoende informatie** (bij de laatste één vraag). Daarnaast **niet uitgevoerd** (ontbrekende kern of context) en **technisch mislukt**, beide zonder inhoudelijk oordeel. NA alleen met een concrete reikwijdtegrond, nooit voor een afleiding of een lege tekst. O1-`review_required` is geen afgeronde V of VN. O3 controleert alleen invoer, signalen en citaatbinding. **Voorkeur A en B: O1 nu, O2 als apart besluit (K2).** (v2: RB-A-15) O2 en het skillcontract zijn niet als besloten gepresenteerd.

O1-reviewerhulp (v2: RB-A-04, RA-B-16):
- Kop: "INT-02 — Nog te beoordelen: bakent de kern het begrip af (kenmerk of afleiding, ook in voorwaardelijke vorm), of functioneert zij als handelingsvoorschrift, procedure of discretionaire beslisregel?"
- Per passage (volledige bijzin of zin met positie, niet alleen het signaalwoord): "Te beoordelen passage: '{passage}'. Beschrijft dit een kenmerk, of schrijft het voor wat een actor moet doen of afwegen? Het beschrijven van een bevoegdheid of besluit is geen overtreding. Dit signaal geeft geen oordeel."
- Zonder signaal: "Geen signaalwoord gevonden; een voorschrift of afweging kan ook zonder signaalwoord voorkomen."
- Lege kern of geen context: `not_evaluated`, reden "INT-02 — Niet uitgevoerd: {definitiekern/context} ontbreekt. Er is geen inhoudelijk oordeel." (v2: RB-A-17: kernherkenning bij alleen-term begrensd; het origineel blijft zichtbaar.)

Meldingen (v2: RB-A-19, tekst van B voor VN):
- V: "INT-02 — Voldoet. '{passage}' beschrijft {criterium/afleiding/constitutief kenmerk}; grond: {grond}. Andere toetsregels zijn hiermee niet beoordeeld."
- VN: "INT-02 — Voldoet niet. Deze passage functioneert als {discretionaire beslisregel/handelingsvoorschrift} voor het handelen: '{citaat}'. Dat is onder de gekozen INT-02-norm geen beschrijvende afbakening van dit begrip. Het enkele beschrijven van een bevoegdheid of besluit is geen overtreding. De tekst is ongewijzigd."
- OI: "INT-02 — Onvoldoende informatie. {ontbrekende of strijdige betekenisgrond}. Vraag: {één gerichte vraag}"
- Technisch: "INT-02 — De beoordeling kon niet worden uitgevoerd door een technische fout. Er is geen inhoudelijk oordeel; de tekst is ongewijzigd."
- Historisch: "INT-02 — Eerdere beoordeling hoort bij een andere tekst-, context-, bron- of normversie. Opnieuw beoordelen is nodig."

Geen score, geen totaalscore [B]. Poortbeleid: K4 (v2: RB-A-15).

### 5.4 Begrensde terugkoppeling (H) — ontwerp onder DEF-638 [V]

(v2: RB-A-20, RB-A-21, RB-A-22)
- **Diagnose vóór advies.** Onderscheid:
  - een werkelijke generatieovertreding;
  - een instructie- of normconflict;
  - **invoer-, transport- of cleaningverlies** (vergelijk prompt → ruw → kern → getoetst → opgeslagen); een correcte ruwe kandidaat wordt niet "gerepareerd" wegens een fout onderweg;
  - een foutpositieve evaluator of buurregel (een INT-10/INT-01-fail op `indien` is geen INT-02-herstelgrond);
  - ontbrekende betekenisgrond;
  - een technische storing.
- **Geen betekenisbehoudend herstel bewezen bij C02, C12, C13 en C14.** Tekst van B, overgenomen: "Stop; bepaal eerst of de passage zelfstandige procesinformatie is of een noodzakelijk kenmerk. Een gewenste betekeniswijziging vergt een afzonderlijke bewuste inhoudelijke keuze en nieuwe beoordeling; zij telt niet als geslaagd INT-02-herstel." Menselijke bevestiging maakt betekenissen niet gelijk. "moet" schrappen verandert een plicht in een feit.
- **Het C04→C05-stijlvoorstel is ingetrokken.** C05 voegt het domein "geheel getal" toe. Omzetting van voorwaardelijke vorm naar kenmerkvorm is geen stilistische omzetting maar een mogelijk betekenisveranderend voorstel.
- **Positief herstelgeval:** B-C64. Een zelfstandig definitiesegment plus een aparte proceszin; de proceszin mag naar een toelichtingsvoorstel, alleen als de volledige kernafbakening behouden blijft.
- **Beschermd:** noodzakelijke en voldoende voorwaarden, domein, tijd, aantallen, negatie, uitzondering, EN/OF, constitutieve doelrelatie, namen, referent, bron, context en recordidentiteit.
- **Stop bij:** herhaling, bronconflict, ontbrekend bewijs, foute validator, betekenisverlies, of na één poging zonder verantwoorde verbetering.
- **Hertoetsen:** INT-02 plus alle geraakte regels; bij een onbekende afhankelijkheid alle toepasselijke controles. Oude oordelen worden historisch.
- **Gebruiker ziet:** het origineel, een apart voorstel, het verschil, de actuele uitkomsten of de stopreden. Conceptstatus, expertbesluit en vaststelling blijven apart.
- **Activeringsvoorwaarde** (RA-B-08): patroonviolations zonder normgrond sturen geen herstel aan.

### 5.5 Skills en prompts: huidig → probleem → vervanging → toetsgeval [V]

Als v1, met deze wijzigingen (v2: RB-A-19, RB-A-20, RB-A-14):
- `json_based_rules_module.py:377`: vervanging = G uit §5.2.
- `INT-02.json` uitleg, toelichting en toetsvraag: §5.1.
- `definitie-toetsregels/reference.md:63`: "`\| INT-02 \| Geen beslisregel \| midden \| Geen handelingsvoorschrift of discretionaire beslisregel als definiens; begripsbepalende kenmerken en afleidingen mogen, ook in voorwaardelijke vorm — zie references/int02-beslisregel.md \|`".
- `definitie-nederlandse-definities/reference.md:186` (v2: voorbeeld zonder equivalentieclaim): "- Beslisregels en voorschriften (INT-02): geen afweging die aan iemands oordeel wordt overgelaten ('tenzij … van oordeel is') en geen handelingsvoorschrift als definitiekern. Een begripsbepalende voorwaarde mag en blijft behouden; laat haar niet weg of verzwak haar niet om het woord 'indien' te vermijden."
- Nieuw `references/int02-beslisregel.md` (N/G/T/H) plus een blok in beide SKILL.md's (canoniek in toetsregels, byte-identieke kopie; overgenomen van B V08). Voorbeelden: ✅ C10, B-C53, B-C54, B-C58; ❌ C02 (bronpaar, met betekenisvoorbehoud), C12 (synthetisch, actorinstructie); grens: C16, C24, B-C55.
- `validation_view.py:807`: "INT-02" toevoegen aan de tuple, **alleen samen met de nieuwe passagehulp**; alleen de oude vraag tonen voltooit O1 niet.
- Overige rijen (SKILL.md:39, dode `IntegrityRulesModule`, testnaam): als v1.

## 6. Q6 — Beoogde kwaliteitswinst, effectevaluatie, risico's

Als v1, met deze wijzigingen (v2: RB-A-24, RB-A-14):
- **Nulmeting:** P1 is geen semantische validatornulmeting; de app geeft alleen RR. De tellingen (11 signalen, 4 gemiste VN, 6 signalen op criteria) zijn verwachtingen onder de normversie N-A1 en kunnen na K1 verschuiven. De UI-bevinding is statisch.
- **Vóór uitvoering:** eerst de betwiste referentieverwachtingen besluiten (K1). Daarna oud en nieuw blind vergelijken, met dezelfde invoer, bron en context, plus ongebruikte hold-out-gevallen (≥6, volgens B). Gemeten worden: onterechte afkeur, gemiste overtreding, terecht open oordeel en betekenisverlies.
- **H-effectvergelijking (nieuw):** C02, C12, C14, C31, C32, C33 en B-C64/C65. Echte voorstellen worden beoordeeld op betekenisbehoud, bronsteun en juist stoppen, niet op groene regels. De eerste poging en het resultaat na herstel worden apart gerapporteerd.
- Omvang, instellingen, eigenaar (zo nodig nog toe te wijzen), autorisatie en moment gaan mee in een latere opdracht. Er is geen model-, herstel- of gebruikersonderzoek uitgevoerd.

## 7. Proeven: uitgevoerd en niet uitgevoerd

Als v1, plus:
- **P3** (review-fase): INT-10/INT-01-melding en ernst bij C04/C05, met context, exit 0 gerapporteerd ([`bewijs/proeflog-a-v2-p3.md`](bewijs/proeflog-a-v2-p3.md)).
- (v2: RB-A-10) De voorspellingsfouten C21 (raakt V3) en C15 (raakt V6) zijn gemarkeerd. De oorspronkelijke verwachtingen blijven, het zijn geen codefouten. C21 bewijst niet dat een woord in de getoetste kern wordt genegeerd.
- Exitstatus: zie §0 (RB-A-09).

## 8. Besluiten voorgelegd aan Chris (v2: RB-A-26, RA-B-25; samengevoegde nummering)

| K (B) | Koppeling A (v1) | Keuze | Voorkeur A en B | Beslissende casus |
|---|---|---|---|---|
| **K1** | B-1, B-2, B-3, B-6 | Functiegrens: brede variant (N-B1/N-A2: + handelingsvoorschrift/procedure) of enge variant (N-A: alleen discretie). In beide: voorwaardelijke criteria en afleiding voldoen, beschrijving van een rechtsgevolg of bevoegdheid voldoet, geen universeel determinisme | Brede variant, als lokale operationalisering | C02 (onder de enge variant geen VN), C03/C15/B-C52 tegenover C16/B-C53/C69, B-C55 |
| **K2** | B-4, B-9 | Evaluator: O1 nu (passagehulp + zichtbare reden) en O2 later apart. Signaalbeleid: behouden, uitbreiden of vervangen | O1 nu; signaalbeleid open | C13, CO-C83, B-C52, B-C55 |
| **K3** | B-5 | Eén versiegebonden contract voor record, prompt, skills en voorbeelden; bronpaar met `review_policy` en een gecorrigeerde reden (tekst van B) | Gelijk | C02, C10, C12 |
| **K4** | — (nieuw) | Wel of geen zelfstandige INT-02-poort voor vaststellen of export | Geen eigen blokkade; open of negatieve uitkomst zichtbaar; expertvaststelling apart | B-C67 |
| **K5** | (v1 §5.4) | H niet activeren; later hoogstens één poging onder DEF-638, met effectacceptatie | Gelijk | C14, C31/C32, B-C64/C65 |

**Geen keuze (bestaand beleid uitvoeren):**
- K-9-contextplicht;
- geen totaalscore;
- toetsen wijzigt de tekst niet;
- lege of ontbrekende kern → niet uitgevoerd (was B-8).

**Geparkeerd** (instructie Chris 25-09): B-7, dus `\bindien\b` in INT-10. Het is een ketenfeit en een waarneming voor het latere INT-10-dossier, geen besluit hier. Het INT-01-deel loopt via het open INT-01-besluit.

## 9. Dekkingstabel (veertien dossieronderdelen) (v2: RB-A-25)

| Onderdeel | Waar | Status en grens |
|---|---|---|
| 1 Doel | §1.2 | Functiegrens |
| 2 Norm/besluiten | §1, §8 | Geen determinisme-eis; N-b = keuze; K-9 en poort gecorrigeerd |
| 3 Toepasselijkheid | §1.4 | Afleiding voldoet; leeg = niet uitgevoerd |
| 4 Context | §2 | K-9 verplicht; semantische toereikendheid apart |
| 5 Definitiebronnen | §2 | Noodzakelijk waar de functie ervan afhangt; conflict → vraag |
| 6 Ontologie | §2 | Relaties toegevoegd; categorie beslist niet |
| 7 Aanvullingen | §2 | Praktijk-, tegen- en grensgevallen en homoniemen onderscheiden |
| 8 Appgedrag | §4 | Service en modules gemeten; import en review gecorrigeerd; opslag en export open |
| 9 Skills/prompts | §5.2, §5.5 | Uitzonderingen synchroon |
| 10 Status/score/poort | §5.3, §8 K4 | Statuscontract gescheiden; poort = keuze |
| 11 Proeven | §7, bewijs/ | Binding en grenzen (exit afgeleid) |
| 12 Samenhang | §3 | INT-10 geparkeerd; G-spanning; geen buurbeleid |
| 13 Verbeteringen/review | verwerking-a-v1.md | Alle 26 punten verwerkt |
| 14 Acceptatie/overdracht | §6, casusregister v2 | Logica, H-effect, open routebewijs |

## Bronnen

Als v1, plus:
- `b-codex-cli/review-b-op-a-v1.md` en `-erratum.md`; `b-codex-cli/onderzoek-b-v2.md`, `casusregister-b-v2.md`;
- `docs/analyses/2026-09-15-DEF-606-besluit-geen-totaalscore-v1.md:27`;
- `ESS-05-verdieping/onderzoek-20260921/gedeeld/besluiten-v1.md:16`;
- `src/database/models.py:136-162`; `src/ui/components/tabs/import_export_beheer/csv_importer.py:245-276`;
- `src/services/validation/modular_validation_service.py:1920-1921`; `src/toetsregels/regels/ARAI-04SUB1.json:31-32`;
- `bewijs/proeflog-a-v2-p3.md`, `bewijs/p3-uitkomsten.json`.
