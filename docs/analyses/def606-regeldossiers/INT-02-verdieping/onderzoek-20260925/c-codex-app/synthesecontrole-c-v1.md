# INT-02 — synthesecontrole C v1

25 september 2026 · DEF-771 · onderzoeker C. **Eindoordeel: nog één materieel formuleringpunt open (SC-C-02); geen nieuwe normkeuze nodig om dat te corrigeren.** De eigen norm, uitzonderingen, strategie en alle negentien nieuwe casussen zijn verder herkenbaar verwerkt. De bewijsparagrafen hebben enkele achtergebleven verkortingen. Dit oordeel betreft de ontvangen v3, niet een nog te schrijven correctieversie.

## Controlebasis en begrenzing

Eerst zijn [onderzoek-c-v1.md](onderzoek-c-v1.md) (**C**) en [casusregister-c-v1.md](casusregister-c-v1.md) (**CR**) volledig herlezen; daarna volledig:

- **S:** [gezamenlijke-synthese-v3.md](../gedeeld/gezamenlijke-synthese-v3.md), leidend.
- **D:** [besluitnotitie-chris-v3.md](../gedeeld/besluitnotitie-chris-v3.md).
- **R:** [gezamenlijk-casusregister-v3.md](../gedeeld/gezamenlijk-casusregister-v3.md).
- **RA:** [review-a-op-c-v1.md](../a-cowork/review-a-op-c-v1.md), RA-C-01…14.

Gericht geverifieerd: **A2** [onderzoek-a-v2.md](../a-claude-cli/onderzoek-a-v2.md) §1.2, §5.2 en §8; **B3** [onderzoek-b-v3.md](../b-codex-cli/onderzoek-b-v3.md) Q1, Q2/V02, V04–V06 en V10. **CO** [normlezing-coordinator-v1.md](../a-cowork/normlezing-coordinator-v1.md) en [synthesecontrole-b-v2.md](../b-codex-cli/synthesecontrole-b-v2.md) zijn gelezen voor de standpunten en de reikwijdte van B's afronding. B verklaarde A+B afgerond en sloot C uit dat oordeel uit; dat wordt hier gerespecteerd.

De aangeleverde ASTRA-snapshots en relevante feitenbasispassages zijn gecontroleerd; geen webactualisering, rechtsactualiteitsclaim of hernieuwd apponderzoek. C's proefopzet, proefuitkomsten en [uitvoering-en-grenzen-v1.md](bewijs/uitvoering-en-grenzen-v1.md) zijn opnieuw gelezen. Alle elf hashes uit manifest-c-v1 komen overeen. Bronnen en bestanden zijn gebonden in [manifest-c-v2.json](manifest-c-v2.json). De opdracht bevestigt deze repositorymap als bestemming voor dit DEF-onderzoeksdocument; het centrale register bevat geen afzonderlijke DEF-route.

## Bevindingen

**SC-C-01 → S §2, §4 en §6; C-N1 → juist — materieel gecontroleerd, geen open correctie.**

Bron: C Q1/N1 en Q2; RA-C-01/02/11; S §2/4/6; ASTRA-snapshots. Functie boven woordvorm, gebonden opdracht ≠ afleiding, kwalitatief beoordelen ≠ beslisregel, beschrijven van normatieve begrippen en de verplichte afleiding bij afleidbare begrippen zijn behouden. C112 maakt de toegestane definitie van een verplichting expliciet. N-breed blijft lokale operationalisering, N-eng een open alternatief. Metadata en review_policy behouden hun eigen provenance. **Correctie: geen aan de normtekst.** Voor de doorwerking naar G geldt SC-C-02.

**SC-C-02 → S §3 exacte G en §6 Nederlandse-definities/reference.md; D voorstel G → tegenspraak — materieel, open.**

Bron: C Q1/N1, Q3/ESS-04, Q5 Exact G; CR-C107; S §2 en §4; R-C107; B3 V05; A2 §5.2. S-G verbiedt naast het actorvoorschrift: **“en geen afweging die aan het oordeel van een persoon of instantie wordt overgelaten.”** Daarmee ontbreekt de functiebeperking uit N/T: het verbod betreft een discretionaire beslisregel die een afweging **voorschrijft**, niet iedere beschreven beoordeling. De expliciete G-uitzondering noemt bevoegdheid, beslissing en rechtsgevolg, maar niet het kwalitatieve/classificerende kenmerk van C107. Die casus vraagt bij onduidelijke functie O en behoud van het constitutieve oordeel; zij rechtvaardigt geen voorafgaand afwegingsverbod in G. B3 V05 formuleert wél specifiek “discretionaire beslisregel”. Dit is een inconsistentie in een zelfstandig over te nemen prompt, geen gemeten modelschade. B's eerdere aanvaarding van de constitutieve uitzondering in de verkorte skillzin sluit deze C107/G-vraag niet af.

**Exacte correctie:** vervang in S-G de twee zinnen vanaf “Neem geen voorschrift op…” tot en met “…de uitoefening ervan voorschrijft.” door:

> Gebruik geen handelingsvoorschrift of behandelprocedure als definitiekern en geen discretionaire beslisregel die een actor voorschrijft wat te doen of af te wegen. Een kwalitatief of constitutief kenmerk waarvoor menselijke beoordeling nodig is, mag worden beschreven; dat is op zichzelf geen beslisregel. Ook een verplichting, bevoegdheid, beslissing, procedure of rechtsgevolg mag als begripskenmerk worden beschreven, zonder de uitvoering ervan voor te schrijven. Beoordeel de functie; verwijder een constitutief oordeel niet om een afweging uit de tekst te laten verdwijnen.

Vervang de volledige voorgestelde skillzin in S §6, rij `nederlandse-definities/reference.md:186`, door:

> - Beslisregels en voorschriften (INT-02): geen handelingsvoorschrift of discretionaire beslisregel als definitiekern. Behoud begripscriteria, voorwaarden en deterministische afleidingen, ook in voorwaardelijke vorm. Menselijke beoordeling van een kwalitatief of constitutief kenmerk is op zichzelf geen beslisregel; een verplichting, bevoegdheid, beslissing, procedure of rechtsgevolg beschrijven mag. Zie references/int02-beslisregel.md.

Vervang in D onder G “geen voorschrift of afweging in de kern” door **“geen handelingsvoorschrift of discretionaire beslisregel als kern; beschrijvende kwalitatieve en constitutieve kenmerken blijven behouden”**. Bij N-eng blijft de reeds afgesproken gezamenlijke versmalling gelden. Acceptatie: C107 niet louter wegens het beschreven oordeel verwijderen/afkeuren; C101 blijft VN bij de discretionaire instructiepremisse; C102/C105 blijven variantafhankelijk. Geen nieuwe modelproef nodig voor deze tekstcorrectie.

**SC-C-03 → S §4, meldingen en statusmapping → juist — materieel gecontroleerd.**

Bron: C Q2 en Q5 meldingen/T; RA-C-02/12; S §4; R-C104/117/118. Passagehulp en nul-trefferwaarschuwing geven geen oordeel; V/VN vragen inhoudelijke grond; O en nog niet uitgevoerde review zijn onderscheiden; NE/NB zijn dezelfde niet-uitgevoerde toestand; E blijft technisch; afleiding krijgt geen NA. Het behouden van B's uitgebreidere melding is inhoudelijk gemotiveerd en verliest C's boodschap niet. **Correctie: geen vereist.** Redactioneel kan na “een zelfstandig aangetoond gebrek blijft zichtbaar” worden toegevoegd: **“De regeluitkomst blijft dan VN; andere open punten worden erbij vermeld.”** Dat expliciteert C's VN-plus-open-punten zonder nieuw uitkomstenbeleid.

**SC-C-04 → S §5, D herstel en R-H-verwijzingen → juist — materieel gecontroleerd.**

Bron: C Q5 Exact H; CR-C108…111/114/115/117/118; S §5; R-inleiding en deze rijen. Diagnose vóór herstel, afzonderlijk verzoek, één poging, betekenisbehoud, bronsteun, originele tekst, herbeoordeling en conceptstatus zijn behouden. H is nauwer geconcretiseerd tot een aantoonbaar niet-begripsbepalend procesvoorschrift; dat is een toelaatbare begrenzing van mijn voorstel, geen toestemming voor criteriumverlies. G/T/H-rollen blijven gescheiden. **Correctie: geen materiële.** Voeg voor zelfstandige leesbaarheid bij de stopredenen toe: **“onbesliste toepasselijke normkeuze”**; die grens volgt al uit K1/variantdoorwerking en C's Exact H.

**SC-C-05 → RA-C-03/04 verwerkt in S §1, maar S §10, D Bewijsgrenzen en R Niet gemeten → tegenspraak — redactioneel te corrigeren.**

Bron: C Q4/Q6; `bewijs/proefuitkomsten-v1.json` P5/P6; uitvoering-en-grenzen; S §1 tegenover §10. S §1 beschrijft P5 en P6 correct, inclusief geïnjecteerd resultaat en gestubde CON-01/02-hulp. S §10 noemt UI/gate echter “alleen codelezing”; D zegt “geen … gate-…proef”; R zegt “Niet gemeten: UI, … gate”. Dat wist uitgevoerd functiebewijs uit. Omdat het concrete bewijs elders correct staat en nergens een volledige routeproef wordt bewezen verklaard, is dit een redactionele bewijslabelcorrectie, geen nieuw onderzoek.

**Exacte vervangtekst voor deze drie bewijsgrenspassages:**

> UI en gate zijn beperkt functioneel onderzocht: C-P5 voert een uit bron geëxtraheerde UI-statushelper uit met een geïnjecteerd resultaat; C-P6 voert de geïsoleerde gatefunctie uit met gecontroleerd vervangen CON-01/02-hulp en recordinterfaces. Bij geïnjecteerde score 0,9 is de gate-uitkomst gelijk met en zonder INT-02-reviewitem; bij score None blokkeert zij. Dit bewijst geen Streamlit-schermgedrag, volledige vaststelroute, bevoegdheidscontrole of databasewerking. Volledige UI-, opslag-, import-, vaststel- en exportdoorlopen zijn niet uitgevoerd; overige ketenclaims berusten op codelezing. Geen model-, menselijke beoordelings- of herstelkwaliteit gemeten.

**SC-C-06 → S §1 keten, D geparkeerd → juist — materieel gecontroleerd.**

Bron: C Q4, RA-C-05/06, S §1, D geparkeerd. De fallback na herladen reconstrueert geen rule_statuses/review_required; dit wordt niet veralgemeniseerd naar bewezen verlies in iedere opslagroute. JSON-export bevat toetsresultaten, INT-02-veldtransport blijft onbewezen en de exportgate staat standaard uit. Parkeren bij DEF-626 heft uitvoeringsacceptatie niet op. **Correctie: geen.**

**SC-C-07 → R-C100…C118 en terugverwijzing naar CR → juist — materieel gecontroleerd.**

Bron: alle negentien CR-rijen vergeleken met R. C100–105 behouden afleiding/discretie/gebonden opdracht/rechtsgevolg/contextgebrek/signaalloze opdracht; C106–108 behouden expliciete equivalentie, constitutief oordeel en bronconflict; C109–111 scheiden transportverlies, schadelijk herstel en hypothetische validatorfout; C112–116 behouden normatief begrip, negatie, brongezag, implicatierichting en constitutieve berekening; C117–118 behouden error en versiebinding. De volledige G/H-kolommen blijven via CR bereikbaar. C102/C105 krijgen alleen onder N-breed VN; C101/C114 bij de discretionaire instructiepremisse onder beide. Ontwerp is niet als uitvoering opgevoerd. **Correctie: geen materiële.** Ter voorkoming van een ongeclausuleerde N-eng-lezing kan R-C108 “een intrinsiek helder voorschrift blijft VN” preciseren tot **“een onder de gekozen norm zelfstandig aangetoonde overtreding blijft VN, met de overige open punten erbij”**.

**SC-C-08 → R-C02 en S §6 example_pair_reason tegenover C-v1 → juist — materieel gecontroleerd.**

Bron: CR-C02; C Q1/N0; B3 I01/V01; RA-C-01; R-C02. Mijn v1 noemt VN als ASTRA-bronlabel en erkent dat het woord geen discretie bewijst. V3 onderscheidt dat label explicieter van het variantafhankelijke oordeel: onder eng geen VN zonder discretionaire grond; onder breed VN bij bevestigde voorschriftfunctie; anders O. Dat is een gegronde precisering, geen onjuiste weergave van een nieuwe C-norm. **Correctie: geen; bronlabel en variantverwachting gescheiden houden.**

**SC-C-09 → S §9, voorkeurkoppen en K2b → weglating — redactioneel.**

Bron: C Q1/Q5/Q6; A2 §1.2/8; B3 I01/V04/V10; CO §1/4; S §9. De weergegeven verschillen tussen A, B en CO over determinisme, rolomkering, context, gate en signalen zijn traceerbaar; hun latere beslechting is geen oorspronkelijk gedeeld standpunt. C's brede norm en keuzeconcordantie staan correct in §9, maar C ontbreekt nog in diverse actuele voorkeurkoppen. C heeft géén vaste S1- of vervangingsvoorkeur uitgesproken (“behoud desgewenst”); schrijf die niet alsnog toe.

**Exacte toevoeging aan S §9:**

> C kwam onafhankelijk uit op N-breed als lokale operationalisering, zonder universele determinisme-eis, met O1 als eerste stap, O2 afzonderlijk, geen zelfstandige INT-02-poort als expliciete productkeuze en geen geactiveerd herstel. C bevestigt C04/C05 niet als betekenisgelijk en neemt geen rolomkering door 'moet' aan. C legt geen keuze tussen S0, S1 en vervangen vast; signalen blijven uitsluitend passagehulp.

Noem C ook in de kop van §9 en bij de actuele gezamenlijke voorkeuren in S/D/R. Historische “A+B afgerond”-oordelen behouden hun beperkte reikwijdte.

**SC-C-10 → D K1–K5/K2b, bestaand beleid, nieuw besluit en parkeren → juist — materieel gecontroleerd.**

Bron: C Q6-keuzes, RA-C-09, D-keuzetabel, feitenbasis §5. C-K1=K1; C-K2 valt inhoudelijk onder K1; C-K3=K2; C-K4=K4; C-K5=K5. Gezamenlijk K3 bundelt mijn record/prompt/skillvoorstellen; het is geen verdwenen C-keuze. K2b maakt een signaalkeuze expliciet die mijn v1 openliet. Contextplicht, geen totaalscore en tekstbehoud bij T blijven bestaand beleid; N-breed, evaluator/signalen, contractpublicatie, poort en H zijn voorstellen. “Broncorrectie zonder nieuw normbesluit” is geen autorisatie om de brede norm alvast te publiceren. INT-10, INT-01, DBT en ketenuitvoering zijn zichtbaar geparkeerd. **Correctie: geen.**

**SC-C-11 → S §7, R-C116 en D geparkeerd → juist — materieel gecontroleerd.**

Bron: C Q3/ESS-04, CR-C116, RA-C-14, S §2/3/7. De spanning over “rekenmethode naar toelichting” staat expliciet bij ESS-04; N/G behouden de constitutieve afleiding in de kern. De buurregelspanning verandert C116 dus niet in een INT-02-uitzondering of toegestane verwijdering. **Correctie: geen materiële.** Vervang alleen de te absolute §7-kop door **“Relaties en resterende buurregelspanning”**.

**SC-C-12 → S §1/8/13, D metingsomvang en R-samenvatting → onjuiste weergave — redactioneel.**

Bron: R's 76 rijen, C Q6, proefuitkomsten P1–P6. S noemt nog 57 als “volledige ontwerpregister”; dat is de A+B+CO-omvang vóór C. R noemt terecht 76. De 45 servicewaarnemingen/39 ID's en twee A-P3-waarnemingen zijn de bestaande basis; C voegt twee servicewaarnemingen toe, naast zes evaluatorwaarnemingen. Historische P0-uitkomsten zijn hergebruik, niet twaalf nieuwe metingen. De C-opsomming in R vergeet P2.

**Exacte correctie in S/D bij de omvang:**

> A+B+CO: 45 servicewaarnemingen over 39 unieke casus-ID's, plus twee A-P3-waarnemingen. C: zes evaluatorwaarnemingen (P1), INT-02-formatteruitvoer met voorbeelden aan/uit (P2), twee servicewaarnemingen (P3), twee cleaninggevallen (P4), één UI-helperproef (P5) en één geïsoleerde gateproef met drie gecontroleerde condities (P6). C hergebruikt bovendien twaalf historische route-uitkomsten (P0); die tellen niet als nieuwe metingen. Het gezamenlijke ontwerpregister bevat 76 ID's: 57 bestaande en 19 nieuwe C-ID's; niet alle zijn uitgevoerd.

Voeg P2 ook toe aan R's C-opsomming. Schrijf in S §13 en D-inleiding **“19 nieuwe casussen, naast zes historische casussen in C's eigen register”**. De bewijsgrens is belangrijker dan een opgeteld proefcijfer.

**SC-C-13 → S §10 verwachting-/exitbewijs en ASTRA-revisie → onjuiste weergave — redactioneel.**

Bron: C-manifest, proefopzet, proefuitkomsten en exitstatus; RA-C-08/13. S veralgemeniseert “Verwachtingen vooraf zonder tijdstempel/hash” naar alle lijnen. C's uitvoer bevat start/eindtijd en de SHA-256 van de vooraf opgeslagen proefopzet; exit 0 is vastgelegd en alle zes proeven staan op uitgevoerd=true. Dit is lokaal bewijs, geen onafhankelijk tijdstempel. C-P3 mat de gehele-runstatus niet correct; nergens is die null alsnog als runtimefeit gebruikt. De ASTRA-oldid-beperking is juist overgenomen.

**Exacte correctie:**

> De eerdere A/B/CO-beperkingen bij verwachting- en exitregistratie blijven lijnspecifiek gelden. C legt exit 0, uitgevoerd=true voor P1–P6, start/eindtijd en de hash van de vooraf opgeslagen proefopzet vast in zijn uitvoer; dit is geen extern geattesteerd tijdsbewijs. C-P3 bewijst de INT-02-regelvelden, niet de gehele-runstatus. ASTRA-oldid 8695 uit het rapport van 7 september is niet aantoonbaar gelijk aan de raw-snapshot van 25 september.

**SC-C-14 → S §8 effectontwerp tegenover C Q6 → weglating — redactioneel te verantwoorden.**

Bron: C Q6 Effectontwerp; S §8; RA-C-10. De materiële methode blijft: vooraf vastgelegde referenties, onafhankelijke hold-out, menselijke vergelijking, betekenisverlies, eerste poging/H apart en geen ongemeten kwaliteitswinst. Mijn concrete voorstel van twaalf G-scenario's en drie runs per variant is niet overgenomen; S kiest twee runs en minimaal zes hold-outs, zonder dispositie. Dat is een ontwerpkeuze, geen bewezen verlies van evaluatiekwaliteit.

**Exacte toevoeging aan S §8:**

> C stelde twaalf gerichte G-scenario's met drie runs per variant en vier extra ongebruikte gevallen voor. Deze synthese kiest voorlopig twee runs per scenario/variant en minimaal zes vooraf gelabelde hold-outs; die aantallen zijn ontwerpkeuzes zonder bewezen equivalentie. De uitvoeringsopzet moet expliciet C's onderscheidende grenzen afdekken: C105, C107, C112, C115 en C116; C117/C118 horen bij fout- en bindingsacceptatie. Eigenaar en definitieve selectie worden vóór uitvoering vastgelegd.

## Dekking van RA-C-01…14

| Reviewpunt | Controle / dispositie |
|---|---|
| RA-C-01 | Norm behouden (SC-C-01); doorwerking G vraagt SC-C-02. |
| RA-C-02 | Strategie/status/poort behouden (SC-C-03/10). |
| RA-C-03/04 | Functiebewijs in §1 juist; bewijsgrenzen corrigeren (SC-C-05). |
| RA-C-05/06 | Herladen/export begrensd opgenomen (SC-C-06). |
| RA-C-07 | P4 bewaard in R; omvang verduidelijken (SC-C-12). |
| RA-C-08 | Geen onterechte runstatusclaim (SC-C-13). |
| RA-C-09 | Concordantie juist (SC-C-10). |
| RA-C-10 | Alle C100–C118 behouden; G-grens en evaluatiedispositie apart (SC-C-02/07/14). |
| RA-C-11 | Metadata/provenance behouden (SC-C-01). |
| RA-C-12 | Meldingen zonder betekenisverlies (SC-C-03). |
| RA-C-13 | Revisiegrens behouden (SC-C-13). |
| RA-C-14 | ESS-04-spanning expliciet, afleiding beschermd (SC-C-11). |

## Eindoordeel en overdracht

**A+B+C kan op de ontvangen v3 nog niet onvoorwaardelijk inhoudelijk afgerond worden verklaard:** SC-C-02 laat in de exacte G-tekst een ruimer afwegingsverbod staan dan N/T en C107 dragen. De correctie is hierboven concreet begrensd en vraagt geen nieuw onderzoek, normbesluit of volledige reviewronde. De coördinator verwerkt haar in een nieuwe versie; C controleert uitsluitend de geraakte G-/skill-/besluitpassages. De redactionele punten kunnen daarbij worden verwerkt. Deze controle wijzigt de v3-bestanden niet en verklaart een toekomstige correctie niet alvast uitgevoerd.

Na aantoonbare verwerking kan het gezamenlijke onderzoek inhoudelijk worden afgesloten **met open K1–K5/K2b en expliciete bewijsleemten**: geen bewezen volledige keten, model-/gebruikers-/herstelwinst, actuele juridische validatie of rechtstreeks gelezen DBT §4.2. De geparkeerde ESS-04-relatie en ketenuitvoering blijven zichtbaar; ze vereisen geen extra INT-02-onderzoeksronde zolang de beschermde normgrenzen behouden blijven.

Alle bevindingen zijn bestemd voor gerichte verwerking door de coördinator; niets geïmplementeerd, geen bestaande versie gewijzigd, geen agents gestart. Dit document is volledig teruggelezen; bronbinding en bestandshashes staan in manifest-c-v2. De automatische goedkeuringscontrole weigerde research-dispatch en requesting-code-review wegens mogelijk starten van agents/reviewers tegen de opdracht; analysis-mode is geladen. Geen weigering omzeild en geen inhoudelijk werk daardoor onuitvoerbaar gebleven.
