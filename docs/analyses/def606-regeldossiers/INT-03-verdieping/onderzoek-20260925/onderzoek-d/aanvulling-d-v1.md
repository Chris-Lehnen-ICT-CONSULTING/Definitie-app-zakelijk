# INT-03 — zelfstandige verdieping onderzoeker D

25 september 2026 · eerste onderzoeksbijdrage · DEF-772 · **besluitvoorstel, geen implementatie**.

INT-03 bewaakt de begrijpelijkheid van verwijzingen. De actuele app neemt daarover geen inhoudelijk besluit: twintig service-uitkomsten blijven `review_required`. Bovendien ontbreekt de INT-03-instructie in de volledige generatieprompt zonder context en bij uitsluitend organisatorische context, terwijl de losse JSON-module de instructie daar wel kan renderen. Mijn voorstel is: maak de toepasselijkheid contextonafhankelijk, behoud duidelijke voornaamwoorden, verbeter eerst de menselijke beoordelingshulp en besluit afzonderlijk over eventuele AI-beoordeling. De nieuwe instructies zijn nog niet geïmplementeerd en hun kwaliteitseffect is nog niet aangetoond. [P2; S4–S7]

## Opdracht, onafhankelijkheid en toegang

Ik ben onderzoeker D, niet de coördinator. Onderzoeker A coördineert volgens [de startopdracht](../gedeeld/startopdracht-d-v1.md). Deze bijdrage behandelt Q1–Q6, G/T/H, veldrollen, casussen, effectevaluatie en besluitpunten. Ik heb geen nieuwe conclusies uit onderzoek-a/, onderzoek-b/ of onderzoek-c/ van dit INT-03-onderzoek gelezen en geen andere sessies gestart. Het vooraf aangewezen **historische INT-01-proefscript** is uitsluitend als uitvoeringsvoorbeeld gelezen. Historische reviews zijn geen nieuwe onafhankelijke bijdrage. Geen kruisreview of gezamenlijke afronding wordt geclaimd.

- Actieve branch en HEAD bij aanvang en proef: `onderzoek/DEF-772-INT-03-20260925`, `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`.
- App-taak `01a0d79e-c525-7e82-a798-1f5660a79a7f`; `turn_context` in het eigen sessielog bevestigt `model=gpt-6-astra`, `effort=high`. Geen instelling afgeleid uit alleen een profiel.
- De feitenbasis is gelezen en de hash klopt: `c160479ace16663bc89ebf902e69c1ab7c4f19ad87a0114473eddd82d158662d`. De gevraagde lokale norm-, code-, historische dossier- en skillbestanden zijn leesbaar. De twee onderzochte skills zijn byte-identiek in `.agents/skills`, `.claude/skills` en de beheerde bron `_claude-global-setup/skills`; zie manifest.
- `research-dispatch` en `analysis-mode` zijn via Skill aangeroepen. `toetsregel-onderzoek` en alle drie referenties zijn gelezen en inhoudelijk gevolgd. De expliciete D-opdracht begrenst de algemene pipeline: geen nieuwe tracks, andere sessies, scorebord of bestanden buiten onderzoek-d/.
- ASTRA is gelezen uit de aangeleverde raw-snapshot. Rechtstreekse webopen van de ASTRA-detailpagina gaf “not accessible”; de Ross-verwijspagina gaf “Cache miss”. De BRS-landingspagina en oorspronkelijke PDF waren via de webtool evenmin toegankelijk. **Ross §4.3 zelf is niet gelezen**; ik schrijf daar geen eigen uitzonderingen aan toe. De oorspronkelijke Onze Taal-pagina en haar pagina’s over betrekkelijke, bezittelijke en wederkerende voornaamwoorden zijn wel rechtstreeks gelezen op 25 september. [S1, W1–W4]
- Linear DEF-772 en de rechtstreeks gekoppelde eigenaren DEF-624/625/626/630/638 en parent DEF-606 zijn read-only opgehaald. Hun beschreven oude proeven zijn geen nieuw uitvoeringsbewijs. DEF-772 is Backlog; DEF-624 en DEF-606 In Progress; DEF-625/626/630/638 Backlog op raadpleging. Geselecteerde brontekst en actualisatiedatum staan in het manifest.
- Opslag betreft repositorygebonden DEF-onderzoek op het expliciet aangewezen pad. Het centrale register bevat geen DEF-route; er is geen nieuwe projectroot afgeleid. De concrete gebruikersopdracht bepaalt hier de repositorybestemming. Bestaande handovers en bestaande onderzoeksbestanden zijn behouden; er zijn geen commits of issues gemaakt.

**Bewijslabels:** S = gelezen lokale bron; W = rechtstreeks geraadpleegde webbron; P = uitgevoerde proef; B = vastgelegd besluit; N/G/T/H-D = voorstel van D. Een codefeit bewijst geen norm. Een ontworpen verwachte uitkomst is geen modelresultaat.

## Q1 — Norm, lokale toevoegingen, toepasselijkheid en uitzonderingen

### Bron versus operationalisering

ASTRA verlangt: “Voor ieder voornaamwoord binnen een definitie dient duidelijk te zijn waarnaar verwezen wordt.” De toelichting noemt ook `het`, `hij`, `zij` en `dat`. In het bronpaar over *context* wordt een onduidelijk `het` vervangen door `die gebeurtenis`; de betrekkelijke `die`-constructies blijven staan. Het paar is daarmee expliciet tegenbewijs tegen een algemeen voornaamwoordenverbod. “JUIST(ER)” is een relatief oordeel over dit normpunt, geen volledige goedkeuring onder alle appregels. [S1]

| Onderdeel | ASTRA-snapshot | Lokale implementatie | Duiding D |
|---|---|---|---|
| Normdoel | Begrijpelijk waarnaar ieder voornaamwoord verwijst | JSON-uitleg sluit hierbij aan | Behouden |
| Plaats antecedent | Geen letterlijke eis “dezelfde zin of zinsdeel” | JSON-toelichting voegt die eis toe; prompt noemt dezelfde zin | Lokale operationalisering, geen letterlijk ASTRA-vereiste; een zin is geen bewijs van eenduidigheid |
| Soort referent | Personen, dieren, voorwerpen of concepten | Altijd een zelfstandig naamwoord benoemd | Te smal als universele grammaticale eis: ook een naamwoordgroep of gehele uitspraak kan antecedent zijn [W2] |
| Signaallijst | Geen regexlijst | Tien patronen plus één aanvullend patroon | Technische hulp, geen normbron of volledige voornaamwoordeninventaris |
| Geldigheid | `alle` | `gehele definitie` | Niet woordelijk gelijk; definitiezin is primair toetsobject, andere velden afzonderlijk (§Q2). Geen grond voor juridische-contextfilter |
| Type | `term` | `interne structuur` | Verschillende metadata; betekenis/equivalentie niet vastgesteld. Bron- en projecttype apart registreren |
| Herkomst | DBT §4.3 | Alleen `ASTRA` | ASTRA → DBT-keten behouden; ontbrekende lezing van DBT zichtbaar |
| Prioriteit/status | Hoog, verplicht, definitief | Dezelfde waarden | Geen afleiding dat regexhit automatisch blokkeert |

De lokale restrictie op zelfstandige naamwoorden is ook om een andere reden kwetsbaar: betrekkelijke voornaamwoorden kunnen een ingesloten antecedent hebben. De gelezen taalbron noemt daarnaast verwijzing naar een volledige zin. Dit is grammaticale onderbouwing; het beslist niet automatisch welke constructies de productnorm voor definities wil toelaten. [W2] Bezittelijke voornaamwoorden drukken een relatie uit, niet uitsluitend juridisch eigendom: de identiteit van de drager van die relatie moet duidelijk zijn. [W3]

### Voorgestelde gedeelde norm N-D1

> Binnen de definitie moet voor de beoogde lezer eenduidig zijn waarnaar iedere verwijzende voornaamwoordelijke uitdrukking verwijst. Beoordeel de uitdrukking in haar grammaticale functie en samenhang. Een duidelijk betrekkelijk of bezittelijk voornaamwoord mag blijven staan. Een verwijzing kan ook een naamwoordgroep of een duidelijk uitgedrukte situatie betreffen; een los zelfstandig naamwoord in hetzelfde zinsdeel is geen algemene eis. De definitie mag niet afhankelijk zijn van een ongenoemde referent uit omliggende tekst. Signaalwoorden zijn geen overtreding op zichzelf. Als de verwijzing niet eenduidig is, leg mogelijke referenten en de ontbrekende grond vast; kies of wijzig de bedoelde betekenis niet stilzwijgend.

Dit is een **voorstel**, met twee expliciete productinterpretaties: zelfstandig begrijpelijke referentie binnen de kern en uitbreiding naar voornaamwoordelijke uitdrukkingen zoals `waarmee`. ASTRA gebruikt het woord voornaamwoord; de huidige app bevat zelf al voornaamwoordelijke bijwoorden. Chris moet die operationele reikwijdte bevestigen. Aanvullende definitiegegevens mogen bedoeld gebruik verklaren, maar een onduidelijke kern niet onzichtbaar repareren.

### Gevallen die de norm moet onderscheiden

- **Betrekkelijk die/dat:** toegestaan bij een heldere relatie met het antecedent. E06/E07 voldoen onder INT-03. Het toevoegen van een tweede plausibele actor kan de lezing wijzigen; geen automatische “dichtstbijzijnde zelfstandig naamwoord”-keuze. [W2; casussen]
- **Vooruitverwijzing:** niet categorisch afkeuren omdat de referent later staat. E12 vraagt inhoudelijke lezing. D stelt duidelijkheid als criterium voor; een expliciete Ross-uitzondering is niet geverifieerd. Een voorkeur bij generatie voor de eenvoudigste woordvolgorde is geen extra afkeurgrond bij toetsing.
- **Bezittelijk:** `zijn/haar/hun` kunnen ook bij een duidelijke betrekkelijke bijzin alsnog meer dan één bezits-/relatiedrager oproepen. Beoordeel ieder voorkomen; E08 geeft daarvoor een vastgelegde bedoeling. Huidige signalen vinden `die`, niet de tweede `zijn`. [W3; P2]
- **Verwijzing naar het gedefinieerde begrip:** een duidelijk genus met `die/dat` kan grammaticaal naar het bedoelde begrip verwijzen (E06/E13). Een los `deze` wordt niet vanzelf duidelijk doordat boven het veld een lemma staat. Onder N-D1 moet de kern het referentiebereik dragen. Herhaling van het lemma is een ander normpunt dan antecedentduidelijkheid.
- **Lidwoord, voegwoord en onpersoonlijk gebruik:** het woord `het` hoeft geen verwijzende voornaamwoordfunctie te hebben; `dat` kan een bijzin inleiden zonder antecedentrelatie. E10 en E16 zijn ontworpen tegenproeven tegen blind lexicaal zoeken. Voor E16 is de uitsluiting van niet-referentieel gebruik een expliciete D-operationalisering, nog geen vastgesteld ASTRA-exceptiebeleid.
- **Geen verwijzing:** na inhoudelijke controle voldoet een niet-lege kern zonder verwijzende constructies onder INT-03; liever `pass` met een beperkte motivering dan een algemene kwaliteitspass. `not_applicable` is een mogelijke productvariant, maar vraagt een expliciete afspraak; de huidige app geeft ook hier review_required. [P2, E05]
- **Leeg:** geen inhoudelijke uitspraak over referentiële kwaliteit. In T-D1: `not_evaluated`, naast de eigen leegtebevinding onder VAL-EMP-001. Actueel levert INT-03 review_required, omdat het invoerkanaal volgens `_available_inputs` ook bij lege tekst bestaat. [S4; P2, E09]

## Q2 — Invoer, veldmatrix en ontbrekende grond

De huidige INT-03-evaluator declareert uitsluitend `definition_text`. N-D1 vereist voor een normaal geval geen bron, ontologielabel of extra document. Voor herstel van werkelijke ambiguïteit is wel betrouwbare bedoeling nodig. Onderscheid **tekst onvoldoende duidelijk** (inhoudelijke bevinding) van **bedoeling voor herstel ontbreekt** (geen toestemming om een kandidaat te kiezen). Deze twee kunnen samen voorkomen, zoals E03/E11. Twijfel van de beoordelaar is niet vanzelf een bewezen overtreding. [S3–S4; interpretatie D]

| Veld | Zelf toetsobject | Bewijs voor INT-03 | Invoer voor G | Mag AI opleveren/wijzigen? | Ontbrekend/conflict en herkomst |
|---|---|---|---|---|---|
| Definitiezin | Primair; alle verwijzingen in exact beoordeelde versie | De kern zelf | Verplicht voor T/H; bij nieuwe G de begripsbedoeling vereist | Kandidaat/afzonderlijk wijzigingsvoorstel; origineel behouden | Lege kern: niet beoordeeld; tekstversie/hash binden |
| Context | Geen automatische gezamenlijke string met kern | Ondersteunt doelgroep en interpretatie; lost een ontbrekende referent niet stil op | Ondersteunend; geen juridische context nodig voor de norm | Registratiecontext niet zelf wijzigen of verzinnen | Tegenstrijdige context expliciet; gebruiker bepaalt identiteit/scope |
| Definitiebronnen | Bronpassage apart, niet als te herschrijven kern | Kan bedoelde referent aantonen; uitgesneden antecedent kan verdwijnen | Ondersteunend; brongetrouwheid bij aangeleverde passages | Citeren/herformuleren als voorstel, bron niet vervalsen | Herkomst, passage en versie bewaren; afwezigheid niet op zichzelf INT-03-fout |
| Ontologie/relaties | Geen INT-03-toets op een label | Rolrelaties kunnen een lezing ondersteunen, nooit alleen kandidaat kiezen | Ondersteunend bij echte ambiguïteit | Hoogstens voorstel; vastgesteld model niet wijzigen | Conflict met tekst zichtbaar; domeineigenaar verduidelijkt |
| Voorbeelden | Per voorbeeld eigen tekst en verwijzingen; geen score over samengeplakte velden | Illustreren lezing, geen onafhankelijk bewijs als model ze verzon | Ondersteunend | Nieuwe voorbeelden als herkenbare voorstellen | Ontbreken geen INT-03-kernfout; bronsoort labelen |
| Praktijkvoorbeelden | Zelfde tekstcriterium, afzonderlijk | Gevalideerde casus kan bedoeling staven | Alleen als werkelijk aangeleverd | Anonimiseren/herformuleren alleen binnen opdracht; praktijkfeit niet verzinnen | Synthetisch is geen praktijkbewijs; geen productiegegevens gebruikt |
| Tegenvoorbeelden | Zelf duidelijk over bedoelde referent | Toont alternatieve lezing/gevolg | Ondersteunend | Als voorstel, niet als autoritatieve interpretatie | Onjuist tegenvoorbeeld kan referentverwarring versterken |
| Grensgevallen | Afzonderlijk; onzekerheid tonen | Onderscheidt één/twee plausibele referenten of onbeslist beleid | Ondersteunend | Voorstel met vastgelegde bedoeling | Geen harde gold-uitkomst bij onbeslist beleid |
| Synoniemen | Termlabel meestal geen verwijzende zin; geen blanket woordverbod | Alleen indien gevalideerde betekenisgelijkheid relevant is | Ondersteunend | Suggestie; vastgestelde term niet vervangen | Synoniem lost grammaticale dubbelzinnigheid niet vanzelf op |
| Homoniemen | Afzonderlijke betekenissen/labels | Waarschuwt tegen schijnbaar gelijke referenten | Ondersteunend bij meerduidige term | Betekenisonderscheid voorstellen, identiteit niet wijzigen | Ontbrekend onderscheid expliciet laten verduidelijken |
| Toelichting | Eigen tekst; antecedent mag in die doorlopende toelichting elders staan | Bedoeling documenteren; kern blijft apart te toetsen | Ondersteunend | Afzonderlijk voorstel, niet heimelijk in definitie opnemen | Toelichting mag een lezer helpen, maar geen verborgen vrijstelling creëren |
| Beoordeling/metadata | Geen definitietekst | Actor, tijd, normversie, exact tekstfragment en gekozen referent | Geen verzonnen “eerder akkoord” | AI-advies onderscheiden van menselijke registratie | Na wijziging niet meer als actueel bewijs hergebruiken |

De zelfstandige toepassing op aanvullende tekstvelden is een voorstel voor consistent schrijfadvies; de huidige proef bewijst uitsluitend toetsing van de definitietekst. Geen bronmetadata of gebruikerstoestemming wordt erbij verzonnen. De inhoudelijke veldverdeling berust op N-D1 en de onderzoeksreferentie *genereren-en-toetsen*, niet op een aangetroffen complete appimplementatie. [M]

## Q3 — Relaties en grenzen van herstel

| Relatie | Bewezen/voorgestelde betekenis | Gevolg en eigenaar |
|---|---|---|
| INT-01 | JSON bevat `die`; E06 “Persoon die een aanvraag indient.” krijgt werkelijk INT-01 fail terwijl D voor INT-03 voldoet verwacht. Ook ASTRA-goed E01 krijgt INT-01 fail. [S11; P2] | Implementatieconflict; niet de duidelijke bijzin kapotmaken. Coördinator koppelt dit aan INT-01/DEF-770; geen buurregelwijziging in dit onderzoek |
| ARAI-05 | Zelfstandige begrijpelijkheid overlapt; lokale patronen en norm zijn niet identiek. E03 blijft ARAI-05 pass: geen bewijs dat de ontbrekende afspraak opgelost is. [S11; P2] | Geen dubbele automatische sanctie; vermeld welk gebrek feitelijk is vastgesteld. Geen extra context verzinnen om de ene regel groen te maken |
| CON-CIRC-001 / SAM-05 | Verduidelijking door een naamwoord te herhalen kan het lemma opnieuw introduceren. CON-CIRC-001 verbiedt letterlijk voorkomen; dat is niet gelijk aan een aangetoonde semantische cirkel. [S11] | E13 scheidt heldere verwijzing van circulariteit. Herhaal een onderbouwde referent of herformuleer; nooit blind het lemma invullen. Inhoudelijke normkeuze bij betreffende dossierhouders |
| INT-04 / INT-10 | Lidwoordidentificatie en toegankelijke kennis kunnen hetzelfde leesprobleem raken; grammaticale functie bepaalt INT-03-toepassing. [S2; N-D1] | “Het systeem” is niet automatisch een persoonlijk voornaamwoord; geen algemene taalcontrole als INT-03 vermommen |
| CON-02 / ESS-03 | Hun AI-beoordeling is een bestaand model voor uitvoering/uitkomsten, geen bewijs dat INT-03 al beoordeeld wordt of dat hetzelfde model goed antecedenten kan onderscheiden. [S4, S9] | Eventuele INT-03-AI apart besluiten en evalueren |
| DEF-624/626/630/638 | Resultaatcontract, versiebewijs, poorten en begrensd herstel hebben eigen eigenaarschap. [B; Linear] | Geen nieuw INT-03-cijfer, automatische vaststelling of reparatielus ontwerpen buiten die contracten |

**Alternatieve verklaringen getoetst:** (1) review_required zou door werkelijk gevonden ambiguïteit kunnen ontstaan; E05/E07/E09 zonder signalen weerleggen die uitleg van het huidige gedrag. (2) INT-03 zou ontbreken doordat het JSON-record niet geladen wordt; dezelfde module rendert het record wél, de adapter filtert de module per context. De actuele modulekeuze verklaart het verschil. Dit zegt niets over de kwaliteit van een model dat eventueel zonder dit blok genereert. [P2; S7]

## Q4 — Bewezen appgedrag en ontbrekende ketenbewijzen

### Toetsingsmechanisme

De gelezen service gebruikt `_evaluate_rule` → `_evaluate_via_registry` → `JudgmentReviewEvaluator`. De naam `_evaluate_json_rule` uit de feitenbasis is voor deze actuele dispatch niet de juiste concrete functienaam. De manager laadt JSON-records; het register resolveert een expliciete evaluator. INT-03 heeft geen regelspecifieke tak in `evaluate`: de reden wordt de toetsvraag; `_signalen` verzamelt treffende **patroonstrings**, geen tekstpassages of kandidaat-antecedenten. ESS-01/02/04 hebben wel aparte passagehulp. [S3–S4]

De aanvullende regex met negatieve lookahead verandert dit niet: hij verbiedt na een treffer drie volgende woorden, maar de afzonderlijke JSON-patronen blijven actief. De lijst mist onder meer `het`, `dat`, `hij`, `zij` en bezittelijke vormen; zij bevat de niet-voornaamwoordelijke frase `in het kader` en de zonder normgrond aangetroffen string `inzienelijk maken`. Meer tokens toevoegen zou signalering verbreden, maar bewijst geen antecedentresolutie. [S3, S5]

P2 actualiseert de historische meting op commit 26f2374d, zonder modelcalls. Beide laadpaden zijn gelijk:

| D-casus | Werkelijke INT-03-status | Signalen (beknopt; exacte strings in P2) | Betekenis van de waarneming |
|---|---|---|---|
| E01/E02 ASTRA goed/fout | Beide review_required | Beide `die` + aanvullend die-patroon | Geen inhoudelijk onderscheid tussen het paar |
| E03 regeling/afspraak | review_required | `deze`, `waarbij`, aanvullend patroon | Geen aanwijzing welke afspraak bedoeld is |
| E04 alleen `het` als voornaamwoord | review_required | Geen | Onheldere referent kan ongesignaleerd blijven; geen onterechte pass |
| E05 zonder voornaamwoord | review_required | Geen | Ook een ontworpen goed geval blijft open |
| E06 duidelijk `die` | review_required | `die` + aanvullend patroon | Treffer is geen foutbewijs |
| E07 duidelijk `dat` | review_required | Geen | Signaallijst is onvolledig |
| E08 bezittelijke ambiguïteit | review_required | `die` + aanvullend patroon | Tweede `zijn` wordt niet aangewezen |
| E09 leeg | review_required | Geen | VAL-EMP-001 faalt afzonderlijk; geen INT-03-inhoudsoordeel |
| E10 `in het kader` | review_required | `in het kader` | Niet-referentiële signaalfrase maakt geen overtreding |

Iedere reden is exact de JSON-toetsvraag. P2 registreert voor INT-03 geen `rule_result` en geen `rule_score` via de bevraagde dictionaries (`None`); de positieve bewijsgrond voor uitsluiting is de `excluded_from_score`-policy plus serviceweging, niet de betekenis van zo’n ontbrekend veld. `review_required` is geen pass of fail. [S3–S4; P2]

### Generatie: module-uitvoer versus volledige prompt

| Synthetische context | Losse JSONBasedRulesModule | Volledige ModularPromptAdapter |
|---|---|---|
| Geen | INT-03 aanwezig | INT-03 afwezig |
| Alleen organisatorisch | INT-03 aanwezig | INT-03 afwezig |
| Juridisch | INT-03 aanwezig | INT-03 aanwezig |
| Wettelijk | INT-03 aanwezig | INT-03 aanwezig |

De exacte INT-03-blokken, volledige moduleteksten, volledige adapterprompts en hashes staan in P2. Het getoonde blok bevat titel, JSON-uitleg, `instruction_map`-instructie en het ASTRA-paar; geen toetsvraag of JSON-toelichting. Dus alléén de JSON-toelichting aanpassen bereikt deze generatie-instructie niet. De vier varianten actualiseren de 7-septemberclaim; zij bewijzen niet alle mogelijke aangepaste/compacte configuraties. [S6–S7; P2]

`IntegrityRulesModule` bestaat nog en heeft eigen hardcoded voorbeelden. In de onderzochte `src`-referenties staat alleen de definitie/export, geen gevonden instantiërende productiecaller. De adapter registreert de JSON-module onder `integrity_rules`. Beide legacy INT03Validator-bestanden zijn aanwezig en inhoudelijk gelijk; hun hit→fail/goed-voorbeeld-uitzondering is niet het geproefde servicegedrag. De gelezen dispatch laadt die validator niet; P2 heeft geen legacy INT03-module in `sys.modules`. Dit is bewijs voor de onderzochte route en een gerichte referentiezoekactie, geen mathematisch bewijs over iedere denkbare externe import. [S7–S8; P2]

### Keten en lifecycle

| Ingang/stap | Bewijs en grens | Open acceptatie |
|---|---|---|
| Genereren | Echte module/adapterrendering, geen modeluitvoer | Prompt daadwerkelijk aan model geleverd; ruwe uitvoer/extractie/nabewerking vergelijken |
| Uitsluitend toetsen | Echte ModularValidationService, manager/cache, synthetische tekst | UI→adaptertransport van precies dezelfde tekst nog niet uitgevoerd |
| Import/bewerken | N-D1 hoort dezelfde kern te toetsen; geen routeproef | Import/edit, verlies van bronomgeving, stale-detectie en hervalidatie bewijzen |
| Reviewweergave | Statische lezing `validation_view`: INT-03 in lijst “Nog te beoordelen”; expliciet zichtbare reviewredenen buiten details zijn alleen ESS-01/02/04. Geen bewezen INT-03-passage-/kandidaatweergave | UI-interactie, letterlijke fragmenten en menselijke bevestiging testen |
| Opslag/herladen | ReviewRequirement bevat code/category/reason/signals; geen referentvelden. Geen save/reload-proef | Versioned oordeel, actor/reden/fragment, definitie-/context-/bronbinding onder DEF-626 |
| Expertbeoordeling/vaststelling | Bestaand beleid vereist menselijke vaststelling; de gelezen expert-tab bewijst geen INT-03-signaalgebonden opslag | Geen automatische goedkeuring uit service-uitkomst; DEF-624/630 bepaalt precieze poort |
| Export/herbeoordeling | `export_txt` kent statuslabel nog te beoordelen; geen INT-03-exportproef | Gebonden actuele review, conceptlabel en gelijke vaststel-/exportbeslissing bewijzen |

De historische 15-september-gateproblemen in DEF-630 worden niet opnieuw als huidige productwaarneming opgevoerd. Evenmin bewijst een Backlog-status dat er nergens deelimplementatie bestaat. Bestaand appbesluit: geen totaalscore als kwaliteitscijfer, acceptatiegrond of hersteldriver. De oudere formulering “voorlopig” in DEF-624/skills is voor dat beleidsaspect ingehaald door B; dit INT-03-onderzoek maakt geen zelfstandige score- of gate-uitzondering. [B; S9–S10; Linear]

## Q5 — Exacte vervangingen, T-uitkomsten en H

Alle onderstaande teksten zijn voorstellen voor bespreking. Geen enkel doelbestand is gewijzigd.

### G-D1: appprompt en regelrecord

**Vindplaats:** `src/services/prompts/modules/json_based_rules_module.py:378`, sleutel `instruction_map["INT-03"]`. Huidig: duidelijke antecedentverwijzing “in dezelfde zin”. Probleem: smalle voorbeeldenlijst, geen expliciete behoudgrenzen en mogelijk verwarring tussen plaats en duidelijkheid. **Exacte vervanging:**

> Maak in de definitie eenduidig waarnaar iedere verwijzende voornaamwoordelijke uitdrukking verwijst. Behoud duidelijke betrekkelijke bijzinnen met 'die' of 'dat' en duidelijke bezittelijke verwijzingen. Beoordeel de grammaticale functie; een woordtreffer is geen reden om het woord te vermijden. Herhaal bij onduidelijkheid alleen een onderbouwde referent of herformuleer met behoud van betekenis, actorrollen, tijdsrelaties, voorwaarden en bronbeperkingen. Verzin geen referent en vervang een verwijzing niet automatisch door het lemma. Maak ontbrekende of strijdige bedoeling zichtbaar via het bestaande verduidelijkings- of toelichtingskanaal, buiten de definitiekern. Een toelichting of externe context repareert een onduidelijke verwijzing in de kern niet stilzwijgend.

**Transportvoorstel:** INT-03-instructie bij iedere generatie van een definitie opnemen, ook zonder juridische/wettelijke context. Niet zonder afzonderlijk onderzoek de gehele INT/SAM-categorie activeren: kies een gerichte contextvrije opname van INT-03 of besluit expliciet over een bredere groep. Behoud de huidige promptlimiet; de extra instructie mag niet stil worden afgekapt. Acceptatie: de vier P2-varianten met INT-03 aanwezig in de daadwerkelijk verzonden prompt. [S7; E01–E18]

**Vindplaats JSON `src/toetsregels/regels/INT-03.json`:**

- `uitleg`, exacte vervanging: “Binnen de definitie is voor de beoogde lezer eenduidig waarnaar iedere verwijzende voornaamwoordelijke uitdrukking verwijst.”
- `toelichting`, exacte vervanging: “Beoordeel voornaamwoorden in hun grammaticale functie en samenhang, waaronder persoonlijke, aanwijzende, betrekkelijke en bezittelijke verwijzingen en verwijzende constructies zoals 'waarmee'. Een duidelijke verwijzing mag blijven staan. De referent kan een naamwoordgroep of een duidelijk uitgedrukte situatie zijn; een zelfstandig naamwoord in hetzelfde zinsdeel is niet altijd vereist en bewijst op zichzelf geen duidelijkheid. Ontbreekt een identificeerbare referent of zijn meer lezingen mogelijk, benoem dit zonder de bedoeling te raden. Niet-referentiële woordfuncties vallen buiten deze beoordeling. Context en toelichting mogen de bedoelde lezing onderbouwen, maar geen onduidelijke kern verbergen.”
- `toetsvraag`, exacte vervanging: “Is bij iedere verwijzende voornaamwoordelijke uitdrukking duidelijk welke referent bedoeld is? Benoem per onduidelijke passage de mogelijke referenten of de ontbrekende referent; beoordeel ook verwijzingen die geen patroonsignaal opleveren.”
- `goede_voorbeelden`: behoud het bestaande ASTRA-goede voorbeeld met herkomst; voeg exact toe: “Persoon die een aanvraag indient.” en “Teken dat een richting aangeeft.”
- `foute_voorbeelden`: behoud het ASTRA-foute voorbeeld met herkomst; voeg exact toe: “Verslag over een besluit nadat het is vastgesteld.” Leg als voorbeeldbedoeling apart vast: het besluit, niet het verslag, is vastgesteld. Voeg geen normclaim toe dat ieder gebruik van `het` fout is.
- **Grensvoorbeeld voor toelichting/reviewerhulp:** “Bericht dat, zodra deze gereed is, de aanvraag vergezelt.” Uitkomst nog te beoordelen; niet als universeel fout voorbeeld in de binaire lijst zetten.

De binaire JSON-voorbeeldvelden kunnen bedoeling en onzekerheidsstatus onvoldoende uitdrukken. Houd het casusregister daarom naast de bronvoorbeelden; het vervangen van dit schema valt buiten de huidige opdracht. Bronmetadata voor ASTRA/DBT, bron-type/geldigheid en lokale aanvullingen onder DEF-625 apart vastleggen. Patternselectie verbeteren is implementatiebeleid voor signaalhulp; de patronen worden nooit de definitie van een overtreding.

### Exacte skillvervangingen

**`definitie-toetsregels/reference.md:64` — vervang de INT-03-tabelrij door:**

> | INT-03 | Duidelijke voornaamwoord-verwijzing | **hoog** | Maak duidelijk waarnaar iedere verwijzende voornaamwoordelijke uitdrukking verwijst; behoud duidelijke die/dat-bijzinnen en bezittelijke verwijzingen. Beoordeel de functie en mogelijke referenten, niet de woordaanwezigheid. Kies bij onduidelijkheid geen betekenis zonder grond. Toetsing wijzigt de kern niet en blijft zonder inhoudelijke beoordeling nog te beoordelen. |

**`definitie-nederlandse-definities/reference.md:185` — vervang het item onder Vermijden door:**

> - Onduidelijke voornaamwoordelijke verwijzingen: maak eenduidig waarnaar onder meer 'deze', 'dit', 'die', 'dat', 'het', 'zijn', 'haar' of 'hun' verwijst. Duidelijke betrekkelijke en bezittelijke verwijzingen zijn toegestaan. Beoordeel eerst de grammaticale functie; niet ieder voorkomen verwijst naar een antecedent. Verduidelijk alleen met een onderbouwde referent of betekenisbehoudende herformulering; verzin geen ontbrekende bedoeling en gebruik het lemma niet als automatische vervanging.

De bestaande aanbeveling voor correcte die/dat-bijzinnen rond regel 167 blijft inhoudelijk verenigbaar. Aanvullend voorstel bij INT-03 in toetsregels/SKILL.md: “INT-03 kent geen automatische woord-afkeur of kwaliteitsscore. Een skilladvies is geen opgeslagen menselijke beoordeling. Gebruik voor toetsing T-D1 en voor voorstellen H-D1; verander de getoetste definitie niet.” De definitieve tekst hoort na besluit in een gedeeld versiegebonden contract; niet opnieuw drie onafhankelijke normvarianten beheren. Actieve en canonieke skillkopieën moeten na latere uitvoering functioneel worden gecontroleerd; gelijke hashes nu bewijzen alleen huidige kopiegelijkheid. [S9]

### T-D1: inhoudelijke toetsinstructie

**Vindplaats voor later:** regelspecifieke INT-03-beoordelingshulp bij `JudgmentReviewEvaluator.evaluate`; bij een expliciet gekozen AI-optie een afzonderlijke evaluator. De bestaande JSON-toetsvraag hierboven blijft de korte ingang. Volledige exacte instructie:

> Toets uitsluitend de aangeleverde definitieversie. Zoek alle verwijzende voornaamwoordelijke uitdrukkingen, ook zonder patroontreffer, en onderscheid verwijzend gebruik van lidwoord-, voegwoord- of niet-referentieel gebruik. Citeer bij ieder relevant geval de letterlijke passage en benoem de mogelijke referenten in die tekst. Beoordeel of voor de beoogde lezer één lezing voldoende duidelijk is; kies niet alleen op afstand, ontologielabel of modelwaarschijnlijkheid. Noteer gebruikte grond en resterende twijfel. Duidelijke betrekkelijke en bezittelijke verwijzingen mogen blijven. Een vooruitverwijzing is niet op zichzelf een fout. Leg een aantoonbaar onduidelijke verwijzing vast als voldoet niet; ontbrekende beoordelingsgrond of semantische twijfel als nog te beoordelen, met een gerichte vraag. Een ontbrekende of lege definitie is niet beoordeeld. Een technische fout geeft geen inhoudelijk oordeel. Verander geen invoer. Houd een eventueel herformuleringsvoorstel apart en presenteer advies niet als geregistreerde menselijke beoordeling of vaststelling.

| Uitkomst | Voorgesteld contractgebruik | Exacte voorbeeldmelding |
|---|---|---|
| Voldoet | `pass`, uitsluitend na inhoudelijke beoordeling; onder huidige menselijke optie eerst review_required | “INT-03 — Voldoet. In 'Persoon die een aanvraag indient' verwijst 'die' duidelijk naar 'Persoon'.” |
| Overtreding | `fail`, met passage en grond; herstelbedoeling mag nog ontbreken | “INT-03 — Voldoet niet. In 'Verslag over een besluit nadat het is vastgesteld' kan 'het' naar 'Verslag' of 'besluit' verwijzen. Maak duidelijk welke van beide is vastgesteld.” |
| Nog te beoordelen | `review_required`; twijfel is geen fail | “INT-03 — Nog te beoordelen. Bij 'deze' zijn 'de aanvraag' en een verwijzing buiten de zin te onderzoeken. Welke referent is bedoeld, en blijkt die voldoende duidelijk uit de definitie?” |
| Ontbrekende betekenisgrond | `review_required` met oorzaak/vraag; onderscheid van bewezen tekstgebrek | “INT-03 — Onvoldoende informatie voor beoordeling. Geef aan welke afspraak met 'deze afspraak' wordt bedoeld. De app kiest die niet zelf.” |
| Ontbrekende/lege kern | `not_evaluated`; niet dezelfde oorzaak als semantische twijfel | “INT-03 — Niet beoordeeld: er is geen definitietekst om verwijzingen te beoordelen.” |
| Technische fout | `error`, behoud technische diagnose apart | “INT-03 — Beoordeling technisch mislukt. Er is geen inhoudelijk oordeel over de verwijzingen.” |
| Geen verwijzende functie | Voorkeur `pass` na controle; alternatief not_applicable expliciet besluiten | “INT-03 — Voldoet voor verwijzingen: in deze definitie zijn geen verwijzende voornaamwoordelijke uitdrukkingen aangetroffen bij inhoudelijke controle.” |

Bovenstaande meldingen zijn **voorbeeldoutput na inhoudelijke analyse**, niet wat de huidige regex kan produceren. De huidige signaalhulp mag alleen automatisch een werkelijk getroffen passage tonen. Een lijst met zelfstandig-naamwoordkandidaten blijft een voorstel, tenzij een mens de syntactische en semantische grond heeft gecontroleerd. Zonder treffer: “Geen patroonsignaal gevonden; de inhoudelijke beoordeling is nog niet uitgevoerd.” Nooit “geen onduidelijke verwijzing” afleiden uit een lege lijst. Bewaar ook de uitdrukking/offset, teksthash, kandidaten, gekozen referent of expliciet onbekend, reden, beoordelaar, tijd en normversie; dit is een contractvoorstel onder DEF-624/626, geen bestaande opslagclaim.

### Drie uitvoeringsopties

| Optie | Inhoudelijke opbrengst en beperking | Voorwaarde/gevolg |
|---|---|---|
| A. Huidig menselijk oordeel laten bestaan | Geen automatische schijnzekerheid; generieke toetsvraag helpt weinig | Kleine technische impact, blijvende open reviewlast; gericht G-transportprobleem blijft wel op te lossen |
| B. AI-beoordeling zoals aparte ESS-03/CON-02-route | Kan passages/kandidaten en gemotiveerde uitkomsten voorstellen; kan ook referenten verzinnen of onterecht zeker worden | Apart Chris-besluit; model/promptversie, goldset, uitkomstcontract, foutgedrag, invoerbinding, kosten en menselijke afwijkingsroute vóór ingebruikname vastleggen. Geen algemeen modelgesprek als evaluatorbewijs |
| C. Verbeterde signaalhulp + menselijk oordeel (**voorkeur D voor eerste stap**) | Toon echte passages, volledige beoordelingsvraag en kandidaatvelden; behoud review_required totdat inhoudelijk beoordeeld | Meet gebruikerseffect; kandidaatvelden handmatig of duidelijk als onbevestigde suggestie. Betere regex alleen lost semantiek niet op |

Optie C kan later B ondersteunen. Geen van de opties wordt door de offline nulmeting als beste gebruikersuitkomst bewezen. N-D1 geldt in alle opties gelijk. Chris beslist tevens hoe de bestaande integrale expertbeoordeling de INT-03-bevinding vastlegt; geen nieuwe afzonderlijke akkoordpoort op grond van alleen de regelprioriteit.

### H-D1: begrensde terugkoppeling en herstel

**Exact voorstel voor herstelcontract/instructie:**

> Herstel uitsluitend een inhoudelijk bevestigde onduidelijke verwijzing wanneer de bedoelde referent uit de aangeleverde gegevens of een expliciete gebruikersverduidelijking vaststaat. Bewaar de oorspronkelijke kandidaat en bied hoogstens één gerichte nieuwe kandidaat met diff aan. Herhaal de juiste referent of herformuleer; behoud begripsomvang, actor- en bezitrelaties, tijdsvolgorde, voorwaarden, bronbeperkingen en noodzakelijke namen. Vul nooit context, bron of reviewbewijs in. Stop zonder tekstwijziging bij ontbrekende bedoeling, bronconflict, technische fout, foutpositieve beoordelaar of dreigend betekenisverlies. Toets de gewijzigde kandidaat opnieuw onder INT-03 en geraakte buurregels; bij onduidelijke afhankelijkheden alle toepasselijke regels. Een blijvend probleem of nieuwe strijdigheid blijft zichtbaar en start geen volgende automatische poging. Een voorstel of geslaagde technische toets is geen menselijke vaststelling.

De limiet van één poging sluit aan bij het geplande DEF-638-contract; deze opdracht activeert geen repairservice. Diagnoses vóór herstel: generatieovertreding, botsende instructies, verlies tijdens transport/nabewerking, foutpositieve evaluator, ontbrekend bewijs of technische storing. E01/E06 zijn belangrijke tegenproeven: verwijder `die` niet wegens een patroon of INT-01-fail. E02 laat gerichte naamwoordherhaling zien; E04 toont dat een kortere zin de uitgedrukte tijdsrelatie kan verliezen. Daarom is de aanvankelijke G/H-verwachting van E04 vóór enige G/H-uitvoering aangescherpt in casusregister/verwachtingen **v2**. De service-invoer en vooraf verwachte actuele status/reden/signalen zijn niet veranderd en blijven aan v1 gebonden. Geen achteraf passend maken van meetverwachtingen.

## Q6 — Effectevaluatie, besluitpunten en overdracht

### Wat is nu gemeten?

P1 strandde vóór applicatie-imports/proeven: de eigen schrijfbeperking liet de standaard tijdelijke map niet toe tijdens de tempfile-schrijfbaarheidstest. Exit 1 en traceback zijn behouden. Voor P2 is uitsluitend `TMPDIR` naar de eigen runtime in onderzoek-d/ gezet. Het script, de casusinvoer en service-/promptverwachtingen bleven ongewijzigd. P2: exit 0, **20/20 serviceverwachtingen en 4/4 promptverwachtingen uitgekomen**; offline gate actief vóór applicatiemodules, geen stubs. De stderr bevat macOS/xcodebuild-omgevingsmeldingen, geen mislukte proefassertie. [P1–P2]

Dit bewijst een nulmeting van huidige routewerking en promptdekking. Het bewijst geen betere definities, geen automatische ambiguïteitsdetectie, geen afgeronde UI-/opslagketen en geen gebruikersverbetering. Voorgestelde varianten zijn nog niet beschikbaar. De 18 D-gevallen zijn vooraf ontworpen, met E04-G/H-correctie expliciet versiegebonden; zij zijn geen gevalideerde juridische praktijkset.

### Vooraf te hanteren effectcriteria per aanbeveling

| Aanbeveling | Beoogde winst | Behoud/weerlegging | Vergelijking en eigenaar |
|---|---|---|---|
| N-D1 + G-D1 en gerichte promptactivering | Minder onduidelijke referenten; ook niet-juridische generatie ontvangt instructie | Geen verlies van duidelijke die/dat-bijzinnen, tijdsrelaties of begripsomvang; geen verzonnen referent | Oude/nieuwe werkelijke generatie op dezelfde invoer; coördinator A draagt aan toekomstige DEF-772-uitvoerder over |
| JSON-/skillharmonisatie | G en T passen dezelfde duidelijkheidsnorm toe | Geen nieuwe blanketwoordafkeur; behoud ASTRA-paar en grammaticale uitzonderingen | Vergelijk echte skillantwoorden vóór/na, met prompt/skillhash, model en vaste bronset; beheerder van actieve skills nog door Chris aan te wijzen |
| T-D1/optie C | Reviewer herkent relevante passage en beslist met betere onderbouwing | Regexhit niet als overtreding; geen hit niet als pass; onbeslist beleid blijft zichtbaar | Geblindeerde gebruikersevaluatie met oude vraag versus nieuwe hulp; onafhankelijk materie-/taaldeskundige, naam nog toe te wijzen |
| Eventuele optie B | Meer juiste, onderbouwde semantische oordelen | Gemiste ambiguïteit, foutieve afkeur en gefingeerde kandidaten afzonderlijk tellen; technische/inhoudelijke onzekerheid onderscheiden | Paarsgewijze AI-evaluatie met onafhankelijke referentieoordelen; alleen na apart besluit/modeltoegang |
| H-D1 | Gerichte verwijzingsreparatie zonder betekenisverlies | Eén poging; stop bij ontbrekende grond; geen actor-, bezit-, tijd-, scope- of bronwijziging | Beoordeling originele en gerepareerde kandidaat, niet alleen groene evaluator; bestaande DEF-638-eigenaar |
| Versiebinding/routeweergave | Oordeel blijft bij exact beoordeelde tekst | Geen actuele goedkeuring na tekst-/bronwijziging; open en error zichtbaar na reload/export | Tijdelijke repository/UI-ketenproef na implementatie; DEF-624/626/630, buiten deze eerste bijdrage |

**Uitvoerbaar evaluatieontwerp:** bevries na Chris’ normkeuze de 18 ontwikkelgevallen en laat een onafhankelijke beoordelaar 12 nieuwe, niet voor ontwerp gebruikte gevallen vastleggen (4 helder, 4 onhelder, 2 grammaticale grensgevallen, 2 ontbrekende/strijdige invoer). E17 is een technische routecontrole, geen inhoudelijke modelkwaliteitsvraag. Laat dezelfde betekenis en beschikbare bronnen in oude en nieuwe variant doorlopen; G beoordeelt werkelijk gegenereerde kernen, T oordelen én redenen, H werkelijke wijzigingen. Bij modelgebruik: hetzelfde model, instellingen en bronset, drie herhalingen per gekozen semantische proef om toeval zichtbaar te houden. De omvang is een voorstel voor een kleine evaluatie, geen autorisatie voor calls.

Laat uitkomsten waar mogelijk zonder variantlabel beoordelen. Registreer verbeterd/gelijk/verslechterd/onbeslist, correcte onthouding, gemiste onduidelijkheid, onterechte afkeur en betekenisverlies apart. **Acceptatievoorstel:** het ASTRA-paar en heldere E06/E07 correct onderscheiden; geen onjuiste zekerheid bij E03/E11/E18; geen inhoudelijke uitspraak bij E17; geen betekenisverlies bij enig herstel. Voor de nieuwe steekproef: minder inhoudelijke fouten dan de oude variant, zonder verslechtering van de vooraf beschermde gevallen. Bij gelijke uitkomsten is geen inhoudelijke winst aangetoond; bij regressie herstellen of aanbeveling herzien. Geen universele kwaliteitsscore of claim buiten de onderzochte casussen. Een volledige adjudicatie bij verschil is nodig; modelovereenstemming is geen onafhankelijke maatstaf.

Voor optie C is aanvullend een echte gebruikersproef vereist: laat reviewers in gespreide volgorde vergelijkbare, vooraf beoordeelde gevallen met oude/nieuwe hulp beoordelen, zonder dezelfde referentoplossing vooraf te tonen. Meet juistheid en navolgbare motivering; tijd alleen indien daadwerkelijk gemeten. Tot deze proef blijft “betere hulp” een hypothese.

### Besluiten die Chris nu kan nemen

| ID | Keuze | Voorkeur D en alternatief | Gevolg / onderscheidende casus |
|---|---|---|---|
| D-B01 | Normdoel en lokale plaats-/woordsoorteis | N-D1: referentiële duidelijkheid; alternatief strikt dezelfde zin/zelfstandig naamwoord | Strikte variant sluit meer grammaticaal heldere constructies uit en vraagt expliciete lokale normgrond; E06/E12/E16 |
| D-B02 | Voornaamwoordelijke bijwoorden en geen-verwijzing-status | `waarmee` e.d. meenemen als expliciete operationalisering; inhoudelijk geen verwijzing → pass voor INT-03. Alternatief beperk tot woordsoort + not_applicable | Scope en UI-label vastleggen; niet uit regex afleiden; E05/E10/E15 |
| D-B03 | Beoordelingsvorm | C: verbeterde signalering + mens; alternatief A niets aan hulp of B afzonderlijke AI-beoordeling | C vraagt gebruikerseffectbewijs; B aparte goldset en model-/foutcontract; alle normgevallen |
| D-B04 | Generatiebereik | INT-03 gericht in alle contextvarianten; alternatief huidige juridische beperking | Huidige beperking laat instructiegat bestaan; vier promptvarianten zijn reeds gemeten |
| D-B05 | Herstel en betekenisbehoud | Alleen voorstel op bevestigde bedoeling, maximaal één gerichte poging; alternatief geheel handmatig | Geen automatische vervanging door lemma of meest nabije naamwoord; E02/E04/E11/E18 |
| D-B06 | Opslag/poorten en effectacceptatie | Aansluiten op bestaande eigenaren en integrale review; criteria hierboven meenemen in uitvoeringsopdracht | Geen nieuwe INT-03-poort of cijfer uit dit onderzoek; geen technische opleverclaim als kwaliteitswinst |

D-B01/02/03/05 zijn nog open productkeuzes. D-B04 herstelt de aansluiting op een algemene norm, maar de precieze implementatie is eveneens nog op te dragen. Het appbrede geen-totaalscorebesluit wordt behouden en niet opnieuw ter goedkeuring voorgelegd.

### Ontbrekend bewijs met volgende actie

| Open werk | Eigenaar | Concrete volgende actie | Afhankelijkheid/moment |
|---|---|---|---|
| Ross §4.3 rechtstreeks lezen | Bronbeheer DEF-625/coördinator A | Verkrijg leesbare primaire passage; toets vooral dezelfde-zin-eis en uitzonderingen | Zodra legitieme bron beschikbaar is; N-D1 tot dan eigen voorstel, geen Ross-citaat |
| Kruisreview en synthese | A organiseert; aangewezen onderzoekers voeren uit | Leg deze versie met manifest naast opgeslagen zelfstandige A/B/C-bijdragen; vraag gerichte review van norm, G/T/H en bewijslimieten | Na ontvangst van de eerste bijdragen; D heeft niets uit hun nieuwe werk gelezen |
| Nieuwe tekst/module-/skillvariant | Nog afzonderlijk op te dragen uitvoerder, DEF-772 en skillbeheer | Implementeer uitsluitend Chris’ keuzes; koppel nieuwe variant aan norm-/prompt-/skillhash | Na besluit en programmeeropdracht; CLI-rolverdeling dan toepassen |
| G/T/H-effectbewijs | A draagt over; onafhankelijke beoordelaar nog aan te wijzen | Bevries ongeziene set en verwachtingen, voer beschreven vergelijking op echte varianten uit | Na implementatie en expliciete toestemming voor model-/gebruikersproeven |
| UI/reviewopslag/versiewijziging/export | DEF-624/626/630 | Tijdelijke recordketen met huidige, ontbrekende en verouderde INT-03-review bewijzen | Zodra contract/implementatie beschikbaar is; geen productiegegevens |
| Gerichte herstelroute | DEF-638 | Eén herstel met betekenisvergelijking en actuele hertoetsing uitvoeren | Na regelcontract, bewijs-/gatevoorwaarden en afzonderlijke autorisatie |

**Status:** eerste bijdrage van D opgeleverd; gezamenlijk onderzoek niet afgerond; geen technische verbeterslag opgeleverd; kwaliteitswinst niet vastgesteld. De volgende overdracht is dit pakket aan coördinator A voor vergelijking en gerichte kruisreview. Dit document verstuurt geen bericht en start geen vervolgsessie.

## Bewijs, versies en bronnen

### Eigen bestanden en reproduceerbaarheid

- [Casusregister v1](casusregister-d-v1.md) en [verwachtingen v1](proefverwachtingen-d-v1.json): vooraf bevroren nulmeting.
- [Casusregister v2](casusregister-d-v2.md) en [verwachtingen v2](proefverwachtingen-d-v2.json): actuele G/H-aanscherping E04 vóór G/H-uitvoering; geen wijziging van meetinvoer of gemeten verwachtingen.
- [P1: proefuitkomsten v1](proefuitkomsten-d-v1.json): mislukte start, exit 1, geen uitgevoerde service-/promptproeven.
- [P2: proefuitkomsten v2](proefuitkomsten-d-v2.json): **leidend uitvoeringsbewijs**, exit 0; volledige prompts, status/reden/signalen, runtime, commando, stderr en hashes.
- [Proefscript v1](proef-d-v1.py): ongewijzigd bij beide pogingen. Mac `.venv/bin/python -B`; `tests/offline_bootstrap.py` vóór appimports; extra schrijfbewaking en alle runtime/caches onder `.offline-runtime-d-v1/` binnen onderzoek-d. Die werkmap is behouden, inclusief eigen testcache; geen productiegegevens gebruikt.
- [Bewijsmanifest v1](bewijsmanifest-d-v1.json): eigen bestands- en bronhashes, selectieve Linear-bronvastlegging, bronbinding en controles. Het manifest bevat geen zelfhash; een hash daarvan kan extern worden gecontroleerd.

Heruitvoering vereist een **verse geautoriseerde werkmap** met script/verwachtingen onder dezelfde namen en een eigen lege runtime; de bestaande proefuitkomsten/runtime worden niet overschreven. Zet `TMPDIR` naar die eigen schrijfbare runtime vóór de interpreter de bootstrap uitvoert. Het exacte werkelijk uitgevoerde commando en de gebruikte override staan in P2. Een heruitvoering is niet nodig zolang code/config en de onderzochte claim gelijk blijven.

### Bronregister

Repositorypaden hieronder zijn relatief aan `/Users/chrislehnen/Projecten/Definitie-app`; het manifest bewaart absolute bronpaden en SHA-256. Sectieverwijzingen in de tekst verwijzen naar deze brongroepen.

| Label | Gelezen bron en relevante vindplaats | Rol |
|---|---|---|
| S1 | `docs/analyses/def606-regeldossiers/INT-03-verdieping/onderzoek-20260925/gedeeld/astra-INT-03-raw-20260925.txt`; feitenbasis-v1.md | Aangeleverde normsnapshot / gedeelde bronbasis |
| S2 | `docs/analyses/def606-regeldossiers/INT-03-v1.md`; `INT-03-bewijs-v1/gevallen.json`, uitkomsten.json, claude-review.json; `docs/analyses/2026-09-07-definitiekwaliteit-dossiers-int-sam.md:128` | Historisch onderzoek, geen huidige runtimeclaim |
| S3 | `src/toetsregels/regels/INT-03.json`; `src/toetsregels/manager.py:306`; cached_manager.py; `config/toetsregels/toetsregels_config.yaml` | Regelcontract/laden |
| S4 | `src/services/validation/modular_validation_service.py:1412`; `evaluators/judgment_review.py:66`; `evaluators/registry.py`; `interfaces.py:268` | Servicegedrag en resultaatcontract |
| S5 | `src/validation/additional_patterns.py:36` | Aanvullende signalering |
| S6 | `src/services/prompts/modules/json_based_rules_module.py:130`, `:262`, `:378` | Werkelijke formatter/instructie |
| S7 | `src/services/prompts/modular_prompt_adapter.py:102`; `modules/prompt_orchestrator.py:403`; `modules/integrity_rules_module.py:182`; `modular_prompt_builder.py` | Registratie, activering, alternatieve module |
| S8 | `src/toetsregels/regels/INT-03.py`; `src/toetsregels/validators/INT_03.py` | Legacy implementatie, geen normbron |
| S9 | `/Users/chrislehnen/.agents/skills/definitie-toetsregels/SKILL.md`, reference.md:64; `/Users/chrislehnen/.agents/skills/definitie-nederlandse-definities/SKILL.md`, reference.md:167/185; identieke beheerde/Claude-kopieën | Onderzochte instructies |
| S10 | `src/ui/components/validation_view.py:238,803,839`; `expert_review_tab.py`; `src/export/export_txt.py:14` | Statische consumercontrole, geen UI-proef |
| S11 | `src/toetsregels/regels/INT-01.json`, ARAI-05.json, CON-CIRC-001.json | Concrete buurregelrelaties |
| B | `docs/analyses/2026-09-15-DEF-606-besluit-geen-totaalscore-v1.md` | Vastgelegd appbreed besluit, geen softwareoplevering |
| M | `/Users/chrislehnen/.agents/skills/toetsregel-onderzoek/SKILL.md`, references/werkcontract.md, startopdracht.md, genereren-en-toetsen.md | Onderzoeksmethode, G/T/H en effectevaluatie |
| S12 | `docs/analyses/2026-09-07-DEF-625-ross-brononderzoek-v1.md:37,66`; centraal regelregister 17 september:30 | Historische bronleemte en administratieve koppeling |

Rechtstreeks geraadpleegde webbronnen (25 september 2026): [W1 — Onze Taal, voornaamwoord](https://onzetaal.nl/taalloket/voornaamwoord), met name soorten en verwijzing binnen/buiten de tekst; [W2 — betrekkelijk voornaamwoord](https://onzetaal.nl/taalloket/betrekkelijk-voornaamwoord), inleiding over antecedent en secties die/dat/wat; [W3 — bezittelijk voornaamwoord](https://onzetaal.nl/taalloket/bezittelijk-voornaamwoord), inleiding over relationele functie; [W4 — wederkerend/wederkerig](https://onzetaal.nl/taalloket/wederkerend-voornaamwoord-wederkerig-voornaamwoord), als aanvullende scopecontrole. Deze taalbeschrijvingen zijn geen productbesluiten.

Actuele read-only issuebronnen: [DEF-772](https://linear.app/definitie-app/issue/DEF-772), [DEF-624](https://linear.app/definitie-app/issue/DEF-624), [DEF-625](https://linear.app/definitie-app/issue/DEF-625), [DEF-626](https://linear.app/definitie-app/issue/DEF-626), [DEF-630](https://linear.app/definitie-app/issue/DEF-630), [DEF-638](https://linear.app/definitie-app/issue/DEF-638), [DEF-606](https://linear.app/definitie-app/issue/DEF-606). Geen nieuwe comments, issues of statuswijzigingen.

### Dekking en resterende grenzen

De veertien methodeonderdelen zijn gedekt als volgt: 1–3 in Q1; 4–7 in Q2; 8 en 10–11 in Q4; 9 en 13 in Q5; 12 in Q3; 14 in Q6 en casusregister. Q6 bevat zowel kwaliteitswinst als mogelijke regressie en concrete overdracht.

De kernconclusies zijn beperkt tot gelezen bronversies en de genoemde proeven. Ross-uitzonderingen, echte modelkwaliteit, gebruikerseffect, volledige UI-/opslag-/exportwerking en gezamenlijk gedragen normkeuzes ontbreken nog. Die leemten hebben hierboven een eigenaar/volgende actie; zij worden niet verborgen achter geslaagde offline proeven.
