# INT-02 — kruisreview B op onderzoekslijn A — v1

25 september 2026 · DEF-771 · onderzoeker B, dezelfde Codex CLI-sessie `01a0d783-365b-7d82-81d3-684fd0e016fc` · wederzijdse review. **Reviewbijdrage; gezamenlijk onderzoek nog niet afgerond.** Geen implementatie of nieuw normbesluit.

De kernbevinding van A is houdbaar: ASTRA verbiedt geen voorwaardelijke zinsvorm, terwijl het lokale record en de actieve generatie-instructie dat wel suggereren. De directe service geeft open review, geen inhoudelijk INT-02-oordeel. De nieuwe bevinding over gescoorde afkeur via INT-10 is bevestigd. De synthese moet wel normverruiming, betekenisverlies in herstelvoorbeelden, contextplicht, statuscontract en de onjuiste afleiding van poortbeleid uit het totaalscorebesluit corrigeren.

## Versies, toegang en bewijs

Volledig beoordeeld: `a-claude-cli/onderzoek-a-v1.md` (**A**, SHA-256 `ea59e45bef2772d4b97e57a1c11ba1e5cf95500712d2fef26b03b12d0d5f8c00`), `casusregister-a-v1.md` (**AC**, `3d2c5cbfa3e00b9ce6713cdf674382e41b84071d24a37ebf7c2a21a437b2df53`), manifest, verwachtingen, proeflog, beide scripts, alle P1-invoer/uitkomsten en P2-uitkomsten. Ook volledig beoordeeld: `a-cowork/normlezing-coordinator-v1.md` (**CO**, `d48f0e2ce350b9b74e583f039f824f7a4c7bd3a5e452a615e0955e95d5c3a586`), C1-uitkomsten, verwachtingen en script. JSON is volledig ingelezen en per rij of compact weergegeven/gecontroleerd. Alle negen bestanden uit het A-manifest hebben de opgegeven hash. Ontvangst/vrijgave: `gedeeld/ontvangstlog.txt`. Geen gevraagd reviewbestand was onleesbaar.

Vergelijkingsbasis B: de vóór uitwisseling opgeslagen `onderzoek-b-v2.md` en `casusregister-b-v2.md` (**B**, **BC**). V1 blijft behouden. V2 corrigeerde vóór lezing van A het onjuiste equivalentievoorstel C57 en tabelweergave; dit was geen verwerking van ontvangen review. Alle onderzoeksversies blijven ongewijzigd.

Bronpaden zijn relatief aan de repo, behalve A/AC/CO/B/BC en `gedeeld/`, die binnen de onderzoeksmap liggen. **S-INT**, **S-BES**, **S-AFL** zijn de drie letterlijke ASTRA-wikitextbestanden in `gedeeld/bronnen/`. `A:143` betekent regel 143 van de vastgelegde versie. Een bronfeit, bestaand besluit, onderzoeksinterpretatie en voorstel hebben afzonderlijke status; een reviewoordeel maakt een voorstel niet tot besluit.

Gerichte controle: ASTRA, INT-10, gate, import, UI en bestaande besluiten. Bronextracten met hashes: `bewijs/review-broncontrole-v1.md`; ontvangen bronbinding: `bewijs/review-bronbinding-v1.json`. De nieuwe uitvoerbare controle is uitsluitend een **artefactaudit**, geen appproef: vooraf `review-auditplan-v1.md`, script `review-audit-v1.py`, uitkomst `review-audituitkomsten-v1.json`, commando/exit 0 `review-audituitvoering-v1.json`, alle in `bewijs/`. HEAD bleef `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`; checkoutbranch `onderzoek/DEF-772-INT-03-20260925`. Geen netwerk, modelcalls, UI-, database- of gateacties.

## Reviewpunten

### RB-A-01 → ASTRA en lokale verruiming (A §1.1/§1.3; CO §1/§2) → bevestigd

**Bron/tegenbewijs:** S-INT:4–7 verbiedt beslisregels, staat afleidingsregels toe en verplicht die voor afleidbare begrippen. S-BES:3–8 koppelt oordeelsvorming aan discretionaire beslissingen. S-INT:24–26 noemt alle definities en gehele definitie. Het lokale record/P2 voegt “of voorwaarden”, de voorwaardenvraag en het vermijdadvies toe; ASTRA bevat geen zeven patronen.

**Gevolg/correctie:** behoud dit als centrale bevinding. Een afleidingsregel kan aan INT-02 voldoen; zij is geen niet-toepasselijkheidsklasse. Voorwaarden/uitzonderingen niet alleen wegens woordvorm afkeuren of schrappen. Type/herkomstherstel blijft voorstel. Nauwkeurige bronvermelding: **“ASTRA (verwijst naar DBT §4.2; DBT niet rechtstreeks onderzocht)”**. DBT en actuele juridische geldigheid zijn niet onderzocht.

### RB-A-02 → N-A1 en universeel determinisme tegenover ASTRA/N-B1 (A:28–32,120–125,143,160; CO:9,34,40–43) → aangevuld

**Bron/tegenbewijs:** S-INT:7 specificeert een deterministisch algoritme voor afleidbare begrippen; :16 noemt noodzakelijke criteria per instantie, geen overeenstemming van alle lezers. CO:9 maakt daarvan “twee bevoegde lezers tot hetzelfde antwoord”; :40 noemt voorwaardelijke vorm “de aangewezen vorm”. Dat volgt niet uit de bron. ESS-04-N2 laat kwalitatieve criteria toe (feitenbasis:124); B-C55 onderscheidt waarneming/beoordeling van een eigenschap van actor-discretie. B:62–72/N-B1 verlangt geen algemeen algoritme voor ieder begrip.

**Gevolg/correctie:** N-A1 past bij B indien “vaststaan” betekent dat het kenmerk voor de bedoelde instanties geldt; niet als extra eis van algoritmische toepassing, absolute zekerheid of interbeoordelaarsovereenstemming. Schrap CO’s universele determinisme-eis en syntaxisvoorkeur als bronplicht. Exacte gezamenlijke aanvulling N/G/T: **“Behoud de onderbouwde begripsbepalende kenmerken. Een afleidbaar begrip wordt gedefinieerd met de deterministische afleiding uit de relevante feiten. Menselijke beoordeling van een kwalitatief kenmerk is op zichzelf geen discretionaire beslisregel.”** C55 en C10/C11 onderscheiden de lezingen. Dit is materieel normbereik.

### RB-A-03 → actorvoorschriften als volledig gesloten ASTRA-verbod (A:28,31,34/B-3; CO:15) → beleidskeuze

**Bron/tegenbewijs:** S-INT:11–16 biedt echte steun voor actor-/gedragslezing; “lijkt” en redactievragen :30–32 laten de categorieverhouding echter open. B N-B1/K1 kiest eveneens uitsluiting van zelfstandige actorvoorschriften/procedures, als **lokale operationalisering**. De enge B-variant N-A omvat alleen discretionaire beslisregels.

**Gevolg/correctie:** behoud de gedeelde brede voorkeur met bronsteun, maar presenteer N-b niet als reeds besloten of uitputtend bewezen. Chris beslist over de functionele grens. C03/C15/B-C52 onderscheiden de varianten. Voorwaardelijke criteria onderdrukken is onder geen van beide brongetrouw.

### RB-A-04 → beschrijving van discretie/rechtsgevolg versus beslisregel (A:123,143–145,155,167; AC-C12/C13/C16/C30; CO-C83) → aangevuld

**Bron/tegenbewijs:** A:155 erkent terecht dat een definitie van “discretionaire bevoegdheid” niet automatisch mag falen. G “geen afweging” en T “dat hoort in de regelgeving, niet in de definitie” borgen dat onvoldoende. B N-B1/C53/C69 behouden constitutieve rechtsgevolgen/bestaande besluiten. S-AFL:5–7 beschrijft het ontstaan van feiten: het beschrijven van zo’n feit voert geen nieuwe beslissing uit. C12 is een synthetische bewerking van S-BES:7, geen letterlijk Ppw-voorschrift. C13/CO-C83 kunnen zonder betekenisgrond ook kenmerken van een soort besluit/maatregel beschrijven.

**Gevolg/correctie:** behoud VN bij expliciet als actorinstructie bedoelde varianten, met die synthetische premisse vastgelegd. Geen zekere VN uit woorden als “oordeel”, “redelijk”, “opgelegd” of “wanneer” alleen. Voeg aan N/G/T/skill toe: **“Het beschrijven van een bevoegdheid, beslissing, procedure of constitutief rechtsgevolg als kenmerk van het begrip is niet op zichzelf een overtreding. Beoordeel of de definitiekern zelf het handelen voorschrijft of de actorafweging als beslisregel uitvoert. Is die functie met de beschikbare betekenisgrond onbeslist, geef onvoldoende informatie met één gerichte vraag.”** Geen generieke juridische vrijstelling; een bronvoorschrift mag niet klakkeloos als definiens worden gekopieerd.

### RB-A-05 → ASTRA-paar, modaliteit en rolomkering (A:34,80,132; AC-C01/C02; CO:15,44) → tegengesproken

**Bron/tegenbewijs:** S-INT:18/20 verschilt uitsluitend in “moet”. Een verplichting versus feit is betekenisverschil; “moet” bewijst geen actor-discretie. “Eis die een organisatie moet ondersteunen” dwingt niet CO’s rolomkering af: ook de lezing dat de **eis** de organisatie moet ondersteunen is mogelijk. ASTRA noemt het voorbeeld weinig sprekend. P1 bevestigt ARAI-04/SUB1-fail bij C02, INT-02 RR zonder signaal; geen automatisch inhoudelijk INT-02-oordeel.

**Gevolg/correctie:** schrap de stellige rolomkering. Behoud letterlijk bronpaar met `example_pair_policy=review_policy` zolang geen nieuw besluit anders bepaalt. Voorstel reden: **“Het ASTRA-paar verschilt in ‘moet’. Dat raakt modaliteit en kan een verplichting uitdrukken; of de definitie daardoor zelf als actorvoorschrift functioneert vergt betekenisbeoordeling. ASTRA noemt het voorbeeld weinig sprekend. Verwijderen van ‘moet’ bewijst geen betekenisbehoud.”** De bredere duiding valt onder B-3. C02→C01 is geen veilige automatische reparatie. “Kan” als vermogen blijft een afzonderlijke ARAI-04-nuance, geen algemene INT-02-fail.

### RB-A-06 → contextplicht/informatiegrenzen (A:60–74; AC-C29/C33; B Q2) → tegengesproken

**Bron/tegenbewijs:** ESS-05-besluiten-v1:16/K-9: zonder context op appniveau **niet genereren en niet toetsen**. A’s matrix noemt context ondersteunend en zegt dat zonder context het INT-02-oordeel wel mag. P1-C03/C29 bewijst alleen dat de huidige evaluator context niet gebruikt; B-P1-C56 bevestigt de uitvoeringskloof.

**Gevolg/correctie:** onderscheid intrinsieke menselijke beoordeelbaarheid van de appvoorwaarde. Context vóór G/T verplicht; ontbrekend → niet uitgevoerd met reden, geen inhoudelijke VN of stille pass. Geen nieuwe Chris-keuze. Een bronpassage is nodig wanneer de functie daarvan afhangt, niet voor ieder intrinsiek helder criterium. Gevulde lijsten zijn geen betekenisbewijs. Bij strijdige grond geen stil compromis: één gerichte vraag. Voeg B-C60 toe; C29’s domeinlabels bewijzen nog geen wettelijke betekenissteun.

### RB-A-07 → veldrollenmatrix (A §2; genereren-en-toetsen §A) → aangevuld

**Bron/tegenbewijs:** A:64–74 onderscheidt object/bewijs/G/wijziging al goed. Ontologische **relaties** ontbreken naast categorie; praktijkvoorbeelden ontbreken; positief/tegen/grens zijn samengevoegd. “Synoniemen/homoniemen niet relevant” (:73) is te sterk: betekenisambiguïteit kan het verschil maken tussen een handeling, resultaat en criterium. B Q2 maakt dit onderscheid.

**Gevolg/correctie:** voeg onderstaande rollen toe, zonder nieuwe norm:

| Veld | T/bewijsrol | G/H en grens |
|---|---|---|
| Ontologische relaties | Ondersteunen bovenbegrip, constitutieve relatie en afleiding; geen automatisch categorieoordeel | Alleen aangeleverd/bevestigd; ontbrekend blokkeren indien functie daarvan afhangt |
| Praktijkvoorbeeld | Afzonderlijk herkomstgebonden toepassingsbewijs | Niet vervangen door verzonnen praktijkbewijs |
| Positief/tegen/grensgeval | Apart: instantiatie/uitsluiting/onzekerheidsgrens; geen zelfstandig normbewijs | Gemarkeerde voorstellen; gegenereerde gevallen bevestigen hun eigen definitie niet |
| Synoniem/homoniem | Verduidelijkt referent of toont ambiguïteit | Geen stille term-/betekeniskeuze om toets te halen |
| Bedoeling/toelichting | Betekenisgrond onderscheiden van apart tekstveld | Geen noodzakelijk kenmerk alleen naar toelichting verplaatsen |
| Reviewmetadata | Binding tekst én relevante context/bron/normversie | Oud oordeel historisch na wijziging; AI verzint geen goedkeuring |

### RB-A-08 → relaties/eigenaarschap (A §3; CO §3) → aangevuld

**Bron/tegenbewijs:** Onderscheid ARAI-04-vorm/INT-02-functie, ESS-04-toepasbaarheid, ESS-05-lidmaatschap is bruikbaar. Het zijn geen exclusieve schotten: ESS-05 K-8 verlangt per regel de eigen motivering. INT-01’s woordlijstwijziging is nog open. STR-06-doel en INT-08-negatie hebben eigen normdoelen; “geen relatie behalve vorm” is voor herstel te beperkt (B-C58). Een uitzondering kan begripsbepalend zijn.

**Gevolg/correctie:** overlap behouden zonder andere oordelen te onderdrukken. INT-02 niet op doel/modaliteit/negatie alleen afkeuren. Herstel beschermt negatie, uitzondering, EN/OF en constitutieve doelrelaties; geraakte regels opnieuw beoordelen. INT-10-ontdekking opnemen (13), maar geen besluiten nemen namens INT-01/INT-10/STR-09/ARAI-04.

### RB-A-09 → bronbinding/verwachtingen/exitstatus/C1 (A §0/§7; manifest/proeflog) → aangevuld

**Bron/tegenbewijs:** B-artefactaudit: alle hashes stabiel; alle 25 P1-inputrijen exact gelijk aan begrip/tekst/context in output; 25 RR, nul INT-02-pass/violation, 11 signaalgevallen, 20 INT-01-fails, acht INT-10-fails precies bij `indien`. Scripts verkrijgen commit via git (P1:87/P2:24). C1 registreert commit/tijden/Python en 13 overeenkomende verwachtingen. Vooraf opgesteld verwachtingsdocument met grond aanwezig. A-log:5 noemt exit 0 uitdrukkelijk **afgeleid** uit tooluitvoer, niet zelfstandig machinevastgelegd. Manifest door coördinator opgeslagen; A-model-/CLI-versie ontbreken.

**Gevolg/correctie:** claims voldoende ondersteund binnen die grenzen. Exit “gerapporteerd/afgeleid 0”, niet door B geobserveerd. Voorafvolgorde steunt op A’s verslag, niet zelfstandig op de eindhash. Bij latere uitvoering echte exit, proeftijden/versies opnemen; geen herhaalde app-run nodig voor dezelfde claims. C1-matches bewijzen softwareverwachtingen, geen norm/modelkwaliteit. Geen DBT-, juridische actualiteits- of ASTRA-revisieclaim toevoegen. De gerichte primaire controles in deze review vullen samenvattingsgebruik aan.

### RB-A-10 → voorspellingsfouten C21/C15 (A-log:15,47–50; AC:26) → bevestigd

**Bron/tegenbewijs:** P1-script:43 zet “tenzij-clausule” alleen in `begrip`, niet `tekst`; evaluator scant tekst. C15 (:37) bevat geen “moet”. Beide geen INT-02-signaal, C15 geen ARAI-04/SUB1-fail. Foutieve voorspellingen/invoerlezing, geen codefout.

**Gevolg/correctie:** hoofdclaims blijven intact. C21 raakt V3, C15 V6; “alle andere 23” vermengt twee voorspellingen. C21 bewijst niet dat een woord in de getoetste kern wordt genegeerd. Oorspronkelijke verwachtingen behouden, afwijkingen markeren.

### RB-A-11 → historisch hergebruik (A:12; B P4) → bevestigd

**Bron/tegenbewijs:** A herhaalt C01–C06 met identieke INT-02-status/signalen. B’s bestaande `historische-diff-v1.txt`/P4 toont recordgelijkheid, AST-gelijke `_signalen`, gewijzigd evaluatorbestand door andere regeltakken. B hergebruikt alleen ongewijzigd INT-02-pad.

**Gevolg/correctie:** beide dragen dezelfde smalle claim. Bestandswijziging maakt niet al het oude bewijs ongeldig; padgelijkheid bewijst niet huidige UI/import/opslag/gate/buurregels. INT-10 rust op actuele P1/code.

### RB-A-12 → actieve prompt, ESS-03/STR-09-spanning en dode module (A:83–84,97,139; P2) → bevestigd

**Bron/tegenbewijs:** P2: actieve `JSONBasedRulesModule` voor integriteit, letterlijk INT-02-blok, ESS-03 “behoud inhoudelijk noodzakelijke namen en voorwaarden”, positief STR-09-voorbeeld met `indien`. Code `json_based_rules_module.py:340–377` bevestigt dit. Adapter registreert geen `IntegrityRulesModule`. P2 executeert vier relevante modules, geen volledige build met echte EnrichedContext.

**Gevolg/correctie:** bewezen spanning in actieve instructies/voorbeelden, geen bewezen generatorfout. In sommige zinnen kan nominale vorm een voorwaarde behouden; het absolute vermijdadvies waarborgt dit niet. “In dezelfde prompt” preciseren als “in standaard geregistreerde promptmodules”; verzending/modelrespons niet gemeten. Dood voorbeeld afwezig in de vier gemeten outputs, niet elke denkbare configuratie. Geen verwijderopdracht afleiden.

### RB-A-13 → INT-10 scoort `\bindien\b` (A:82/B-7) → bevestigd

**Bron/tegenbewijs:** `INT-10.json:15,37–45`: patroon, generic/automated/scored. `generic.py:102–115` maakt finding; MVS:1532–1557 score/violation. P1/audit: acht indien-teksten fail, zeventien overige niet. Eigen INT-10-uitleg/vraag (:4–6) gaat over achtergrondkennis, geen voorwaardelijke vorm.

**Gevolg/correctie:** opnemen als bevestigde nieuwe bevinding. INT-02-V/OI bewijst op zichzelf geen INT-10-fout; diens eigen norm is nodig. C04’s eenvoudige deelbaarheidscriterium behoeft geen niet-openbare bron: `indien` draagt de afkeur niet. Niet alle synthetische juridische gevallen daarom integraal INT-10-goed verklaren. MVS:1918–1919 adviseert bij forbidden_patterns ook “Herschrijf de zin zodat de gedetecteerde patronen niet voorkomen”: risico op criteriumverlies, statisch vastgesteld, geen uitgevoerd herstel. Via synthese aan bestaande eigenaar; hier niets wijzigen.

### RB-A-14 → INT-02-reden onzichtbaar in UI (A:100,205,218) → bevestigd

**Bron/tegenbewijs:** `validation_view.py:237–263` toont statuscodes; :794–808 redenen alleen ESS-01/02/04; :862–864 slaat uitleg bij statuslijsten over. B-P1 heeft geen afzonderlijk INT-02-rule_result. Dit ondersteunt de claim voor het normale huidige RR-resultaatpad.

**Gevolg/correctie:** reden tonen is terecht O1-voorstel. “0 van 25 UI-redenen” vervangen door **statische codebevinding; geen browserproef**. Tuplewijziging toont pas passagehulp als de reden die werkelijk bevat; alleen oude vraag tonen voltooit O1 niet. Andere schermen/payloads niet bewezen.

### RB-A-15 → gate en besluitstatus (A:103,154,172,200) → tegengesproken

**Bron/tegenbewijs:** `_evaluate_gate`, `definition_workflow_service.py:715–835`, leest geen INT-02-reviewlijst: bevestigd. Het besluit `2026-09-15-DEF-606-besluit-geen-totaalscore-v1.md`, §Doorwerking en grenzen, wijzigt individuele scorepolicy/reviewplicht/poorten juist **niet automatisch**. ESS-05 K-4 is geen INT-02-besluit. B K4 noemt geen zelfstandige blokkade een voorkeur.

**Gevolg/correctie:** vervang A:172: **“De totaalscore vervalt volgens het appbrede besluit. INT-02 is momenteel uitgesloten van scoring. Geen zelfstandige INT-02-gate is gevonden; toekomstig poortbeleid is een afzonderlijke productkeuze. Voorkeur: geen eigen INT-02-blokkade, met zichtbare open/negatieve uitkomst en afzonderlijke expertvaststelling.”** Ook O2/skillcontract niet als besloten presenteren. Score-None kan nog blokkeren: afwezigheid eigen gate bewijst geen geslaagde vaststelling. INT-10-gate-effect blijft onbewezen: MVS geeft severity=error en severity_level=critical, gate vergelijkt severity met critical/high. Zonder transportconversie geen directe doorwerking claimen. Algemene migratie DEF-630 behouden.

### RB-A-16 → import/review/opslag/export/cleaning (A §4) → aangevuld

**Bron/tegenbewijs:** `definition_import_service.py:67–73,98–112` valideert preview/import; management-CSV `csv_importer.py:245–276` heeft no-op auto_validate. A:99 “import valideert niet” is te algemeen. `expert_review_tab.py:1071–1091` betreft CON-02-brononderdelen/part_correction; statuscitaat bewijst geen INT-02-review. B Q4 bevat route-/opslag-/exportvindplaatsen. B-P3 mat cleaning C50/C52: label/header/punt, behoud indien/moet in die gevallen; grep zonder woorden bewijst geen algemeen betekenisbehoud.

**Gevolg/correctie:** splits importroutes; A:101 corrigeren naar CON-02-citaat en INT-02-route niet bewezen. Opslag/snapshot/export blijven open bewijs. Neem B’s statische aanvulling over: resultaatcontract kan RR transporteren; opslaghelper uit violations dekt RR niet vanzelf; optionele async exportgate gebruikt uitgevoerd resultaat/is_acceptable. Geen vrije export of volledige redenpersistentie claimen. Generatie-cleaning als aparte stap met ruwe/geëxtraheerde/getoetste tekstbinding; uitsluitend toetsen bewaart aangeboden tekst. Geen volledige UI→opslag→export-proef geleverd.

### RB-A-17 → leeg/alleen term (A B-8; AC-C06/C23) → bevestigd

**Bron/tegenbewijs:** P1/C1 bevestigen RR bij lege tekst. “Toegang:” is niet leeg; P1 voert geen cleaning uit. NB/not_evaluated is een ontwerp voor ontbrekende kern, geen bestaande ingangsfoutafhandeling.

**Gevolg/correctie:** ontbrekende kern → niet uitgevoerd met reden; geen pass/NA/inhoudelijke fail. Kernherkenning bij alleen-term begrenzen; origineel zichtbaar bewaren, niet stil herschrijven tijdens toetsen. Andere invoerbevindingen apart. Huidige RR-waarneming behouden.

### RB-A-18 → uitkomsten/evaluatoropties (A:149–170) → aangevuld

**Bron/tegenbewijs:** O1/O2 passen bij B K2; geen marker→semantische fail is terecht. A:154 “vier uitkomsten (V/VN/niet van toepassing → hier NB/OI + één vraag)” vermengt inhoud en uitvoering. ESS-03 is precedent, geen INT-02-mandaat.

**Gevolg/correctie:** precies **voldoet / voldoet niet / niet van toepassing / onvoldoende informatie**, bij laatste één vraag. Daarnaast niet uitgevoerd (ontbrekende kern/appvoorwaarde) en technisch mislukt, zonder inhoudelijk oordeel. O1-review_required is geen afgeronde V/VN. NA alleen met concrete reikwijdtegrond; geen routinevrijstelling voor afleiding/leegte. Gedeelde voorkeur O1 nu, O2 afzonderlijk; geen verplicht nieuwe LLM-toets/modelkeuze DEF-815. Deterministisch deel kan invoer/signaal/citaatbinding controleren, geen semantisch verdict afdwingen.

### RB-A-19 → N–G–T-aansluiting en exacte vervangingen (A §5; CO §4) → aangevuld

**Bron/tegenbewijs:** A geeft concrete teksten met dezelfde functiegrens. Uitzondering :155 en H-grenzen zijn onvoldoende doorgetrokken naar G:143/T:167/skill:199–201. CO wil signalen **vervangen**, A behouden/uitbreiden: geen gezamenlijke keuze. G laat een voorlopige kandidaat toe waar C33 onthouding heet.

**Gevolg/correctie:** RB-A-02/04-aanvullingen synchroon opnemen in norm, prompt, beide skillreferenties en reviewerhulp. Voeg G toe: **“Een voorlopige kandidaat is alleen toegestaan voor zover de beschikbare betekenisgrond die kandidaat draagt. Ontbreekt die grond of is de functie strijdig onderbouwd, maak geen stille keuze en geef de ontbrekende keuze afzonderlijk aan; verzin geen definitiekern.”** Vervang T-VN(N-a): **“Deze passage functioneert als discretionaire beslisregel voor het handelen: ‘{citaat}’. Dat is onder de gekozen INT-02-norm geen beschrijvende afbakening van dit begrip. Het enkele beschrijven van een bevoegdheid of besluit is geen overtreding.”** Alleen gebruiken bij onderbouwde VN.

Neutrale passagehulp kan conditionele én actorwoorden gebruiken; effect toetsen zonder woord→fail. “Redelijk/passend/acht” bewijzen niets. CO’s “ten onrechte aangewezen” preciseren als niet-onderscheidende signalering. A’s minimale recordalternatief (:135) volstaat niet los: hardcoded G blijft dan bestaan. Record/uitleg/instructie/voorbeelden/T/skill/H samenhangend wijzigen in een latere opdracht; bij enge normkeuze alle relevante teksten aanpassen.

### RB-A-20 → logische gelijkwaardigheid (AC-C04/C05,C10/C11,C17/C18,C28; CO-C80/C81) → tegengesproken

**Bron/tegenbewijs:** AC:12–13 noemt C04 noodzakelijk criterium en C05 dezelfde betekenis. “Even indien deelbaar” geeft op zichzelf een voldoende voorwaarde; C05 voegt domein “geheel getal” toe. C17→C18 voegt “lopende verenigingsjaar” toe en kan voldoende in volledige/noodzakelijke afbakening veranderen. C10/C11/CO-C80/C81 delen kenmerken, maar indien bewijst geen tweezijdige equivalentie. B-C54 onderscheidt alleen-als/als; B-v2-C57 toont dat zelfs “als en slechts als” verkeerd geplaatst de afbakening verandert.

**Gevolg/correctie:** teksten/IDs behouden, maar “zelfde betekenis” en veilige stijlconversie niet als bewezen presenteren. Zelfde toegestane INT-02-functie is niet dezelfde logische afbakening. G/H beschermen noodzakelijkheid, voldoende voorwaarden, domein, tijd en uitzonderingen; bij ontbrekende grond stoppen. INT-02-V sluit afzonderlijk ESS-/brongebrek niet uit. B paste deze correctie vóór uitwisseling ook op eigen C57 toe.

### RB-A-21 → H-C02/C12/C13/C14 en betekenisverlies (AC:10,17–19; A:183–190) → tegengesproken

**Bron/tegenbewijs:** Moet schrappen verandert plicht in feit. C12-uitzondering schrappen verruimt de klasse als zij constitutief is. C14 verwijdert getuige-beperking en erkent reikwijdteverandering, terwijl A:188 dan stoppen verlangt. Menselijke bevestiging maakt betekenissen niet gelijk.

**Gevolg/correctie:** vervang H hier: **“Geen betekenisbehoudend herstel bewezen. Stop; bepaal eerst of de passage zelfstandige procesinformatie is of een noodzakelijk kenmerk. Een gewenste betekeniswijziging vergt een afzonderlijke bewuste inhoudelijke keuze en nieuwe beoordeling; zij telt niet als geslaagd INT-02-herstel.”** Naar toelichting verplaatsen alleen als volledige kernafbakening behouden blijft. Positief onderscheidend geval B-C64: zelfstandig definitiesegment plus aparte proceszin. Behoud A-C31/C32 als negatieve gevallen. C33 geeft geen vrijbrief voor ononderbouwde voorlopige kern.

### RB-A-22 → H-diagnose/limiet/transport (A §5.4) → aangevuld

**Bron/tegenbewijs:** A scheidt meerdere fouten terecht, maar H-diagnose mist transport/cleaning. Skill §D verlangt zo nodig prompt→ruw→kern→getoetst→opslag. Vaste hertoetslijst :190 mist mogelijk INT-08/INT-10, CON-02, STR-08/09.

**Gevolg/correctie:** transportverlies afzonderlijk diagnosticeren; geen correcte ruwe kandidaat “repareren” wegens fout onderweg. H op verzoek, ontwerp DEF-638, maximaal één poging als voorgesteld INT-02-contract; geen activatie claimen. Bescherm logische richting/negatie/namen/referent/bron/context/recordidentiteit. Stop bij herhaling, bronconflict, ontbrekend bewijs, foute validator, betekenisverlies. Alle geraakte regels hertoetsen; bij onbekende afhankelijkheden alle toepasselijke controles. Origineel, apart voorstel, verschil, actuele uitkomsten/stopreden tonen. Conceptstatus, expertbesluit en vaststelling apart.

### RB-A-23 → volledige casusverwachtingen/G–T-koppeling (AC geheel) → aangevuld

**Bron/tegenbewijs:** Alle 30 scenario’s hebben G/T/H-kolommen; 25 uitgevoerd, vijf ontwerpgevallen. Synthetische bedoeling draagt ontwerpverwachting, geen juridische waarheid. C28-generatie-ingang niet uitgevoerd; P1 levert geen inhoudelijke V/VN.

**Gevolg/correctie:** onderstaande beoordeling omvat ook de overige gevallen:

| Gevallen | Oordeel/correctie |
|---|---|
| C01/C02 | Bronpaar houden; RB-A-05/21; doelbijzin eigen regelvraag |
| C03/C15/C29 | VN onder bedoelde actorinstructie/brede norm; labels geen bronbewijs, nieuwe kern niet invullen zonder grond |
| C04/C05/C10/C11/C17/C18 | Criteriumfunctie toegestaan; equivalentie/noodzakelijkheid corrigeren (20) |
| C06/C23 | Ontbrekende kern niet uitgevoerd; huidige RR behouden |
| C12/C13/C16/C30 | Functie/constitutieve betekenis expliciteren; wanneer→wegens lost ambiguïteit niet zelfstandig op |
| C14 | VN onder gedragslezing; betekenisverlies geen herstel |
| C19/C20/C22 | INT-02-V onder synthetische criteriumbedoeling; geen juridische geldigheidsclaim; datum/voorwaarden behouden |
| C21 | Woord in apart termveld; geen bewijs over term-in-kernvariant |
| C24 | OI bij onbesliste functie; onbepaaldheid alleen geen VN. Ook deterministisch voorschrift kan onder brede norm VN zijn, niet alleen discretie |
| C25 | V bij criterium, OI bij onbekende functie, VN bij bewezen behandel-/toekenningsinstructie onder brede norm; niet altijd OI bij toekenningsregel |
| C26 | INT-02-V als terugvalcriterium; STR-09-voorbeeld onderbouwt niet de zelf toegevoegde term identificatieplichtige of juridische klasse |
| C27 | Afleiding toegestaan; volledige jaren/peildatum synthetische concretisering, niet letterlijk ASTRA vandaag–geboortedatum |
| C28 | Dezelfde norm in beide routes als contract; routegelijkheid niet gemeten |
| C31/C32 | Goede negatieve H-gevallen; verlies/verzinsel stoppen; geen uitgevoerde model/softwareproef |
| C33 | Geen definitieve kern zonder grond; voorlopige kandidaat slechts voor zover zelfstandig onderbouwd |

Koppel B-C55 (kwalitatief), C58 (negatie/uitzondering), C60 (bronconflict), C61 (transport), C64/C65 (mogelijk herstel/uitgeputte poging), C67 (versiebinding) aan syntheseacceptatie. Geen nieuwe IDs nodig en ontwerp niet als gemeten presenteren.

### RB-A-24 → effectevaluatie/nulmeting (A §6; skill §E) → aangevuld

**Bron/tegenbewijs:** A onderscheidt implementatie/kwaliteitswinst, noemt vóór/na, blinde beoordeling, onafhankelijke referentie O2 en herhaalde G-runs. P1 is geen semantische validatornulmeting: slechts RR. Zeven VN’s en zes goede signaalgevallen zijn N-A1-verwachtingen, na verduidelijking mogelijk anders. UI 0/25 is statisch. Zelfstandige H-effectvergelijking ontbreekt.

**Gevolg/correctie:** ruwe tellingen/normversie behouden. Vóór uitvoering betwiste referenties besluiten; oude/nieuwe variant blind vergelijken met dezelfde input/bron/context, ongebruikte gevallen, onterechte afkeur, gemiste overtreding, terecht open oordeel en betekenisverlies. H toevoegen: C02/C12/C14/C31/C32/C33 en B-C64/C65; echte voorstellen toetsen op betekenisbehoud/bronsteun/stop, niet groene regels. Eerste poging en na herstel apart. Omvang/instellingen/eigenaar (zo nodig toe te wijzen)/autorisatie/moment opnemen in latere opdracht. Geen model-, herstel- of gebruikersonderzoek uitgevoerd; promptwijziging/overeenstemming bewijst geen verbetering.

### RB-A-25 → veertien dossieronderdelen (A §9) → aangevuld

**Bron/tegenbewijs:** Alle onderdelen hebben een vindplaats, maar een kop bewijst geen volledige dekking. Deze review omvat het gehele onderzoek.

**Gevolg/correctie:** onderstaande lacunes en bewijsgrenzen meenemen:

| Onderdeel | Status/aanvulling |
|---|---|
| 1 Doel | Functiegrens gedekt; punten 01–04 |
| 2 Norm/besluiten | Determinisme, actorstatus, context/gate corrigeren; 02–06/15 |
| 3 Toepasselijkheid | Alle definities; afleiding voldoet, leegte niet uitgevoerd; 01/04/17–18 |
| 4 Context | K-9 verplicht, semantische sufficiëntie apart; 06 |
| 5 Definitiebronnen | Noodzaak waar functie afhangt, conflict/bron versus norm; 04/06–07 |
| 6 Ontologie | Relaties aanvullen, categorie beslist niet; 07 |
| 7 Aanvullingen | Praktijk/tegen/grens/homoniemen onderscheiden; 07 |
| 8 Appgedrag | Service/modules gemeten; import/review corrigeren, opslag/export open; 12/14/16–17 |
| 9 Skills/prompts | Uitzonderingen/semantiek synchroon; 19–22 |
| 10 Status/score/poort | Geen-gate niet uit scorebesluit; statuscontract scheiden; 15/18 |
| 11 Proeven | Binding/tellingen bevestigd, beperkingen/hergebruik behouden; 09–11 |
| 12 Samenhang | INT-10 en G-spanning toevoegen; geen buurbeleid besluiten; 08/12–13 |
| 13 Verbeteringen/review | Per punt verwerken met vindplaats; 26 |
| 14 Acceptatie/overdracht | Logica/H-effect en open routebewijs; 20–24 |

### RB-A-26 → A B-1…B-9 tegenover B K1…K5 → beleidskeuze

**Bron/tegenbewijs:** A:249–263; B-beslissentabel:256–263. Een casus verheldert gevolgen, maar vervangt Chris’ beleidskeuze niet.

**Gevolg/correctie:** overeenstemming én verschillen expliciet overdragen:

| A | B | Overeenstemming/verschil/beslissende casus |
|---|---|---|
| B-1 functie/vorm | K1/K3 | Eens functie; algemeen voorwaardeverbod geen brongetrouw alternatief. Universeel determinisme corrigeren: B-C55 versus C10/C11 |
| B-2 criteria | K1/K3 | Eens toegestaan; logica behouden. C04/C05,C17/C18 geen bewezen equivalenten; B-C54/C57 |
| B-3 actorvoorschrift | K1 | Gedeelde brede voorkeur; A noemt direct volgend, B lokale operationalisering. C03/C15/B-C52 versus C16/B-C69 |
| B-4 strategie | K2 | Eens O1 nu/O2 apart; geen modelkeuze. C13 zonder huidige marker versus beschrijving discretionaire bevoegdheid |
| B-5 paar | K3 | Eens behouden plus functiegevallen; B behoudt review_policy en geen moet→zelfstandig functiebewijs. C02/C12 |
| B-6 rechtsgevolg | K1 | Eens beschrijving kan; betekenisvraag niet grammaticaal oplossen. C16/C30/B-C53/C69 |
| B-7 INT-10/INT-01 | Q3/K3 | Nieuwe INT-10-bevinding bevestigd; doorgeven eigenaar, geen uitvoering hier. C04/C11/C26 |
| B-8 leeg | K2/V03 | Eens niet uitgevoerd; C06 versus C23 vraagt begrensde kernherkenning |
| B-9 UI | K2/V03 | Eens tonen; menselijke beoordeling/opslag meer dan tuple. C03/C13 |
| Ontbrekend: poort | K4 | Expliciet toevoegen; voorkeur geen zelfstandige INT-02-blokkade, niet reeds besloten. B-C67/actueel open oordeel |
| Ontbrekend apart: H-uitvoering | K5 | Ontwerp niet actief; semantiek/limiet/effectacceptatie bij opdracht. C14 versus B-C64/C65 |

B-8/B-9 passen bij transparantie/statusbeleid; uitvoering niet geleverd. B-1/B-2 als onderbouwd bronherstel benoemen; lokaal afwijken vergt expliciete keuze. Contextplicht en geen totaalscore niet opnieuw ter keuze stellen. DBT, juridische geldigheid en routebewijs blijven bewijsleemten, geen door beleid te vervangen feiten.

## Materiële punten voor de synthese

- **Norm/besluiten:** 02–06/15: geen universeel determinisme, beschrijven versus voorschrijven bewaken, rolomkering niet bewezen, actorgrens als keuze, contextplicht toepassen, geen-gate niet uit 15 september.
- **N/G/T/H en betekenisbehoud:** 19–23: geen onbewezen equivalenties of veilig herstel bij C02/C12/C14; gelijke uitzonderingen; stoppen bij betekenisverlies.
- **Resultaat/app:** 13/16–18: INT-10 bevestigd; importroutes/reviewverwijzing corrigeren; statuscontract scheiden; opslag/export/gate-transport niet bewezen.
- **Veldrollen/effect:** 07/24–25: relaties/aanvullingen/H-effectontwerp toevoegen; statische UI-claim geen meting noemen.

## Niet-materiële preciseringen

- 09–11: exit afgeleid, A-model/CLI-versie ontbreekt; C21 bij V3/C15 bij V6; smal oud bewijs blijft geldig. Hoofdwaarnemingen niet ontkracht.
- 12/14: moduleproef/codelezing juist labelen; geen gemeten generatorfout/volledige UI- of promptketen claimen.
- CO’s herkomsthypothese “voorwaarden” blijft hypothese; DBT lezen bewijst zonder wijzigingshistorie niet de lokale ontstaansroute.

## Keuzes voor Chris en overdracht

Keuzes: brede/enge actorgrens met constitutieve uitzonderingen, evaluatorstrategie, voorbeeldpaar-/signaalbeleid, zelfstandige INT-02-poort en eventuele latere G/T/H-uitvoering met effectacceptatie. B blijft bij voorkeur N-B1, O1, geen zelfstandige blokkade **na expliciet besluit**, H niet activeren in dit onderzoek. Concrete betekenisleemten vereisen informatie/brononderzoek.

A/coördinator: verwerk RB-A-01…26 per punt als overgenomen, gedeeltelijk overgenomen, afgewezen met grond of open, met vindplaats in een nieuwe versie. B verwerkt de ontvangen review op zijn eigen onderzoek zodra die expliciet is overgedragen. Daarna op verzoek één volledige synthesecontrole op weglatingen, standpuntweergave, tegenspraken en betekenisverlies. Geen extra volledige reviewronde zonder materiële wijziging. Deze bijdrage claimt geen wederzijds of gezamenlijk afgerond onderzoek.
