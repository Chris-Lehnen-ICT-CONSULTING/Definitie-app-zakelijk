# Review B op onderzoek C — INT-03 — v1

25 september 2026. Reviewer B: Codex CLI, GPT-6 Astra, reasoning high. Beoordeeld onderzoek C: Claude Code CLI, `claude-fable-5-1`, `xhigh`, volgens overgedragen onderzoeksidentiteit. Geen sessielogs of andere sessies geopend.

## Beoordeelde versie en controle

Beoordeeld: `aanvulling-c-v1.md`, `casusregister-c-v1.md`, `proefverwachtingen-c-v1.json`, `proef-c-v1.py`, `proefuitkomsten-c-v1.json`, `bewijsmanifest-c-v1.json` en het daarin genoemde `proef-c-v1-run1.log`. Alle zes manifestbestanden komen overeen met hun hash. Rapport: SHA-256 `31f3a53247584abac9722f27ef952af2a38b409de300175b9d18696c2241fbd3`. Eventuele latere C-v2-bestanden vallen buiten deze review en zijn niet gelezen.

De zeven codehashes in de proefuitkomsten en de hash van de verwachtingen komen overeen met de beschikbare bestanden op commit `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`. Dertig servicevergelijkingen en zeven promptvergelijkingen staan op waar; manifest rapporteert exitstatus 0. Bootstrap is vóór de appimports geïnstalleerd; uitvoer schrijft exclusief naar een nieuwe naam. Geen nieuwe appproef uitgevoerd: gerichte broncontrole volstaat voor de feitelijke geschilpunten.

## Bevindingen

### BC-01 → Q1: norm en lokale aanscherpingen → bevestigd

**Bron/tegenbewijs:** ASTRA-raw bevat geen naamwoordeis of vaste plaatsingsafstand; JSON bevat die wel. C onderscheidt twee betrekkelijke die-vormen correct, waar A-v1 er ten onrechte drie noemt. B deelt de brede referentinterpretatie.

**Gevolg/correctie:** behoud dit onderscheid, maar formuleer “precies één ding” als één eenduidige betekenis/referent, zodat meervoudige referenten, een groep of een propositie niet per ongeluk verboden raken. Afzwakken van lokale tekst blijft een Chris-besluit.

### BC-02 → Q1/Q2: norm geldt vanzelf ook voor alle aanvullende prozavelden → beleidskeuze

**Bron/tegenbewijs:** ASTRA “binnen een definitie” en metadata “alle” bepalen niet welke recordvelden de app als definitie ziet. C's veldmatrix is uitgebreider dan A's en scheidt kern en onderbouwing goed; B behandelt toepassing op aanvullende teksten als afzonderlijke projectkeuze.

**Gevolg/correctie:** label de veldscope en zinsgrensregel voor toelichting/voorbeelden als voorgestelde toepassing, geen letterlijk ASTRA-voorschrift. Tegenvoorbeelden mogen opzettelijk een fout tonen; die fout mag niet automatisch het kernoordeel afkeuren.

### BC-03 → Q1: uitzonderingen → aangevuld

**Bron/tegenbewijs:** C meldt eerlijk dat de taalbron niet is gelezen. B las [Taaladvies: onderwerp](https://taaladvies.net/termen-onderwerp/) en [Onze Taal: betrekkelijk voornaamwoord](https://onzetaal.nl/taalloket/betrekkelijk-voornaamwoord): loos het, grotere antecedenten en wie/wat met ingesloten antecedent vragen geen verzonnen naamwoord. Dat ondersteunt de uitzondering, maar niet elke afzonderlijke het/er-constructie automatisch. Direct achter een naamwoord staan is geen algemene garantie voor duidelijkheid.

**Gevolg/correctie:** neem de gelezen onderbouwing met herkomst B over; verwijder geen leesstatus alsof C zelf die bronnen las. Vul onbepaalde/ingesloten vormen aan in G/T. Vooruitverwijzing blijft functieafhankelijk, geen categorische fout of vrijstelling. C's stijlvoorkeur antecedent eerst is verenigbaar met B, mits geen afkeurgrond.

### BC-04 → Q1 uitzondering 5 en E11: lemma als antecedent → beleidskeuze

**Bron/tegenbewijs:** C wil een verwijzing naar het lemma als duidelijk kunnen aanmerken; B verlangt eenduidigheid in de kern en benoemt lemma+kern als ander leesobject. A laat dit open. E11 (“voorschrift dat bepaalt hoe deze regel wordt toegepast”) is geen zuivere demonstratie van alleen een verborgen lemma: regel staat ook letterlijk in de kern en voorschrift is een aanwezige te onderzoeken referent.

**Gevolg/correctie:** leg beide scopes aan Chris voor, inclusief transport/export. Gebruik E11 niet als beslissend empirisch bewijs voor de scopekeuze. Vergelijk desgewenst later een werkelijk ontbrekende referent met een expliciete genusverwijzing; nu geen nieuw runtime-experiment nodig.

### BC-05 → Q4/proef route A: actuele uitkomsten → bevestigd

**Bron/tegenbewijs:** vijftien gevallen × manager/cache leveren review_required, letterlijke toetsvraag en ruwe patroonstrings. A meet twintig, B zestien uitkomsten; de verschillende aantallen zijn verschillende selecties, geen tegenspraak. C herhaalt de historische gevallen en toont bovendien in het kader en de niet-effectieve uitzondering in het extra patroon.

**Gevolg/correctie:** sterker historisch dekkingsbewijs dan B's kleinere selectie. De nieuwe ID voor leeg bewaart de alias empty; blijf die koppeling expliciet gebruiken. Dit is contractgedrag, geen vijftien juiste semantische beoordelingen.

### BC-06 → Q4/Q6: “nul onderscheidend vermogen” en “foutpositieve signalen” → onvoldoende bewezen

**Bron/tegenbewijs:** hetzelfde statustype op alle gevallen en gelijke signalen voor het ASTRA-paar bewijzen dat geen semantische uitslag wordt berekend. Ze bewijzen niet dat signalen een menselijke reviewer nooit helpen. “2 van 5 werkelijke overtredingen” heeft geen transparant vastgezette noemer naast de overige historische/geactualiseerde fouten. Goede zinnen met een neutrale tokenhit zijn niet automatisch foutpositief beoordeeld.

**Gevolg/correctie:** rapporteer de exacte lijsten en het ontbreken van semantisch onderscheid door de evaluator. Benoem niet-verwijzende/irrelevante treffers als ruis en gemiste relevante vormen als detectiehiaten. Werkelijke hulp of schade vraagt de geplande gebruikersproef. Dit sluit aan op B; A-v1 gebruikt “foutpositief signaal” eveneens te ruim.

### BC-07 → Q5 T: technische fout wordt ook altijd review → tegengesproken

**Bron/tegenbewijs:** gericht herlezen `src/services/validation/modular_validation_service.py:1430–1483`: ontbrekende vereiste invoer leidt tot not_evaluated; RuleContractError en andere exceptions worden error. `judgment_review.py` laat compileerfouten naar die grens doorlopen. De normale INT-03-evaluator geeft review, de omringende service heeft wel een technisch foutonderscheid.

**Gevolg/correctie:** beperk “alles review” tot de normale succesvol uitgevoerde evaluator en gemeten gevallen. Lege tekst is een apart bevestigd invoerhiaat: het kanaal geldt beschikbaar, ook als de tekst leeg is. B/A onderscheiden deze zaken al beter. Geen foutinjectie uitgevoerd of nodig om de bestaande except-route vast te stellen.

### BC-08 → Q5 T-contract: fail alleen als bedoelde referent vaststaat → tegengesproken

**Bron/tegenbewijs:** een lezer kan vaststellen dat twee referenten plausibel zijn zonder te weten welke de schrijver bedoelt. C's eigen E08 noemt de zin normatief fout maar accepteert bij T2 ook onvoldoende informatie. B-v1 Q2/T-B1 houdt aantoonbare ambiguïteit en ontbrekende herstelbedoeling naast elkaar; A's T-c is op dit onderscheid nog niet scherp genoeg.

**Gevolg/correctie:** geef fail plus gerichte herstelvraag bij bewezen onduidelijkheid. Laat review over als juist het taalkundige oordeel nog onvoldoende zeker is. Stel vooraf één verdedigbare normverwachting vast of label het werkelijk betwiste geval; maak “fail of review” niet tot een ruime succespoort voor iedere fout.

### BC-09 → Q5 T-melding: 'die' → gebeurtenis en kandidaatlijst bij 'het' → tegengesproken

**Bron/tegenbewijs:** in het ASTRA-paar verwijzen de twee betrekkelijke die-vormen naar omstandigheden; aanwijzend die in die gebeurtenis hoort bij gebeurtenis. De lijst omstandigheden/omgeving/gebeurtenis/basis bevat niet alle, en zeker niet automatisch gelijkwaardige, referentmogelijkheden voor het. Grammaticale functie, getal/geslacht en eventuele propositieverwijzing moeten meewegen; geheel is bovendien een aanwezig onzijdig naamwoord.

**Gevolg/correctie:** meld per afzonderlijke passage de juiste analyse. Toon alleen gemotiveerde plausibele kandidaten, geen willekeurige lijst van naamwoorden. C's pass-melding mag niet als exacte voorbeeldtekst worden gepubliceerd. A moet dezelfde kandidaatvoorzichtigheid toepassen.

### BC-10 → casusregister T1a: twee/drie afzonderlijke die-passages volgens bestaande helper → tegengesproken

**Bron/tegenbewijs:** gerichte broncontrole `judgment_review.py:157–192`: `_reden_met_passages` dedupliceert de fragmenttekst met `dict.fromkeys`. Identieke die-fragmenten worden bij ongewijzigd gebruik één keer vermeld, ook bij meerdere posities/patronen.

**Gevolg/correctie:** schrijf één uniek die-fragment als verwachting bij hergebruik van de bestaande helper, of label per-voorkomenweergave met offsets als extra ontwerpwijziging. B's bewijscontract vraagt juist zo'n herkenbare positiebinding; die volgt niet vanzelf uit het ESS-04-sjabloon.

### BC-11 → Q4 UI/opslag: sterkere statische keteninspectie → aangevuld

**Bron/tegenbewijs:** de gecontroleerde reviewweergave toont INT-03 als code; alleen ESS-01/02/04 krijgen een reden, en de detailtak gaat zonder expander verder. Dit vult A en B aan. C noemt zelf ontbrekende opslag-/herlaad-, import- en exportproeven. Een ontbrekend `signals`-token in src/ui en de gelezen expertschermen bewijzen geen universele afwezigheid van iedere mogelijke debugweergave of opslag in generieke JSON.

**Gevolg/correctie:** formuleer “in de onderzochte route geen zichtbare INT-03-reden en geen specifieke besluitactie aangetroffen”. T1a moet zichtbaar worden gemaakt én een versiegebonden beoordelingsroute krijgen via DEF-624/626/627. Geen totale opslagafwezigheid of werkende export claimen zonder doorloop. B-v2 neemt het concrete UI-punt over.

### BC-12 → Q4/proef route B: module, voorbeelden en contextvarianten → bevestigd

**Bron/tegenbewijs:** C rendert drie modulevarianten en vier volledige adaptervarianten. Wetcontext activeert INT-03; voorbeelden uit verwijdert het paar in de moduleproef. Dit gaat verder dan A's selectieproef en B's drie adaptervarianten. Exacte blokken en skips zijn bewaard.

**Gevolg/correctie:** herbruikbaar bewijs voor deze configuraties. P03 stelt include_examples=False rechtstreeks in: “compact verwijdert het paar” is niet óók dynamisch bewezen met een compact-adaptervariant. De geautoriseerde proef bevat geen model; afwezigheid van het blok bewijst nog niet slechtere definities.

### BC-13 → Q5 G5/B3: hele INT-module nodig, smalle optie breekt structuur, +10K tekens → onvoldoende bewezen

**Bron/tegenbewijs:** verschil 35.907 − 25.925 betreft de volledige juridische versus contextloze prompt; context_awareness en sam_rules veranderen mede. Dat is geen geïsoleerde kostprijs van alleen integrity_rules. `JSONBasedRulesModule.execute` filtert generiek op `startswith(self.rule_prefix)`; de bron bewijst geen onvermijdelijke architectuurbreuk bij regelspecifieke selectie.

**Gevolg/correctie:** presenteer brede en smalle toevoeging als ontwerp-/scopekeuzes; meet later een gecontroleerd verschil met dezelfde invoer. A en B kiezen de smalle INT-03-stap; C kiest de hele categorie. Dat materiële verschil blijft naar Chris, zonder onbewezen kosten- of architectuurargument als doorslag.

### BC-14 → Q5 G1–G4: normconsistentie en onbekende bedoeling → aangevuld

**Bron/tegenbewijs:** C laat herformuleren en behoudt betekenis explicieter dan A. G1 verbiedt verzinnen, maar vraagt toch een voorlopige kandidaat als de referent onbekend is. Dat is alleen veilig als de onbekendheid niet wordt ingevuld en de kandidaat niet als hersteld/goedgekeurd verschijnt. B stopt bij ontbrekende herstelgrond. Direct-na-antecedent-voldoet in G2/G3 mist opnieuw de beoordeling van mogelijke concurrerende lezingen.

**Gevolg/correctie:** leg vast wat de voorlopige kandidaat inhoudelijk mag bevatten, hoe de vraag apart verschijnt en welke actuele route dat ondersteunt. Ontbrekende appondersteuning mag geen vraag in de definitiezin laten belanden. Neem niet-verwijzende vormen mee; C's Q1-uitzondering is in de voorgestelde G-teksten onvoldoende zichtbaar.

### BC-15 → Q5 T2: versiegebonden AI-contract → bevestigd

**Bron/tegenbewijs:** C noemt aparte evaluator/dienst, norm-/prompt-/modelbinding, citaten, onzekerheid en foutbeleid. Dit is concreter technisch dan A en verenigbaar met B's bewijscontract. C erkent een afzonderlijk ADR/productbesluit.

**Gevolg/correctie:** hergebruik de werkvorm, niet het regelspecifieke oordeel of de kwaliteit van ESS-03/CON-02. Letterlijk citaatbestaan controleert geen semantische juistheid; impliciete of propositionele referenten kunnen niet altijd als één zelfstandig naamwoord geciteerd worden. Blijf hele tekst en gekozen normscope beoordelen, ook zonder signalen.

### BC-16 → Q5 T/B2: geen vaststel-/exportblokkade volgens ESS-03 → beleidskeuze

**Bron/tegenbewijs:** het expliciete geen-totaalscorebesluit is appbreed; de ESS-03-poortafspraak is regelspecifiek. B maakt onderscheid tussen geen losse INT-03-poort invoeren en gedeeld DEF-630-beleid. A-v1 loopt hier hetzelfde risico als C.

**Gevolg/correctie:** trek geen bestaande INT-03-poortvrijstelling uit ESS-03. Chris beslist de aansluiting op gedeelde verplichte review, vaststelling en export. Scoreloos blijft; niet-blokkerend is een afzonderlijke beleidsdimensie.

### BC-17 → Q5 H: diagnose, herstel en buurnormen → aangevuld

**Bron/tegenbewijs:** alleen bevestigde bedoeling, één kandidaat, origineel bewaren en hertoetsen zijn bruikbaar. “INT-blok ontbrak, dan is de generator niet fout” bewijst geen causale schuldverdeling: de tekst kan de norm schenden ongeacht promptaanwezigheid. Een ontbrekende hit is een detectorhiaat, niet automatisch ontbrekend bewijs. “Nooit automatisch” en “één automatische kandidaat” vragen een expliciete betekenis: na afzonderlijk gebruikersverzoek?

**Gevolg/correctie:** onderscheid kandidaatkwaliteit, mogelijke instructieoorzaak, betekenisgrond en technisch falen. Geen causale generatieclaim zonder gepaarde modelproef. Verduidelijk de activeringsvoorwaarde voor de ene poging. Stop bij een buurregelconflict en toon het; pas geen goede tekst stil aan om een onjuiste INT-01-regex te ontlopen. A/B/C delen betekenisbehoud, verschillen in de activering en uitwerking.

### BC-18 → Q6: effectevaluatie detecteert winst en verslechtering → aangevuld

**Bron/tegenbewijs:** C's vaste invoer, ≥3 runs, blind beoordelen, onafhankelijke maatstaf en verbeterd/gelijk/verslechterd/onbeslist zijn geschikt. De set bevat goede en slechte gevallen, anders dan A's smalle gebruikersproef. Behoud van acteurs/bezit/bronbedoeling is expliciet. Ruime alternatieven fail óf review en onbekende aantallen “werkelijke overtredingen” verzwakken echter het referentieoordeel.

**Gevolg/correctie:** verscherp eerst het oordeelcontract (BC-08), bevries generatiebrief en referentbedoeling, en meet T1a via mensen. Voor echte holdout tien nieuwe, voor ontwerp afgeschermde gevallen; reeds in A/B/C besproken gevallen zijn ontwerpgevallen. +10 van C versus ≥6 van B is een omvangkeuze, geen inhoudelijk conflict. Geen effect bewezen vóór uitvoering.

### BC-19 → Q6/B1–B7: dossierdekking en “bestaand beleid herstellen” → beleidskeuze

**Bron/tegenbewijs:** alle Q's en dossieronderdelen zijn behandeld; bronhiaten zijn expliciet. DBT blijft ongecontroleerd. C's uitgebreidere keteninspectie en historische actualisatie vullen A/B aan. De hele INT-module activeren raakt andere regels, ook als DEF-126/171 alle regels wilden tonen; nieuwe uitzonderingen of normtekst zijn geen uitvoeringsakkoord.

**Gevolg/correctie:** behoud C als zelfstandig advies met materiële correcties BC-07/08/09/10/13. Chris beslist scope (kern/lemma/aanvullingen), smal/breed promptbereik, statussemantiek, mens/AI en herstel/poorten. Geen legacybestanden verwijderen vanuit deze review.

## Overdracht

C's service- en promptbewijs is bruikbaar en op onderdelen uitgebreider dan dat van A/B. De aanbevolen eerste stap menselijke passagehulp wordt gedeeld, maar vereist zichtbare en versiegebonden afhandeling. Materiële verschillen blijven expliciet: C kiest de hele INT-module, laat lemma als referent toe, maakt fail afhankelijk van bekende bedoeling en draagt ESS-03-poortbeleid over; B verkiest smalle scope en scheidt tekstfout, herstelgrond en gedeeld productbeleid. A staat bij promptscope dichter bij B, maar moet zijn eigen norm- en T-b-teksten corrigeren. Verwerking hoort bij C en de coördinator; B wijzigt hun bestanden niet. Geen gezamenlijke afronding.

