DEF-835 — verslag van beoordelaar B, 29 september 2026

Voor alle 40 gevallen zijn zelfstandige labelvoorstellen vastgelegd in [labelvoorstellen-v1.json](labelvoorstellen-v1.json), status `voorstel_niet_geaccepteerd`, normversie `def771-int02/2`. Dit is de bewaarde eerste versie. Chris accepteert later de labels en beslist over verschillen, geschiktheid en selectie. Er is geen expertgoldset geaccepteerd, geen freeze uitgevoerd en geen splitsing gemaakt.

De vier inhoudsbronnen zijn volledig gelezen in de opgegeven volgorde: [besluiten-chris.md](../invoer/besluiten-chris.md), [normcontract.md](../invoer/normcontract.md), [casuspool.json](../invoer/casuspool.json) en [ontwerpregister.md](../invoer/ontwerpregister.md). De vier SHA-256-hashes zijn gecontroleerd tegen [manifest.json](../invoer/manifest.json) en ongewijzigd opgenomen onder `bronhashes`. Alleen deze aangeleverde kopieën zijn als inhoudsbron gebruikt; verwijzingen naar oorspronkelijke locaties zijn niet gevolgd. Het ontwerpregister met 76 C-ID’s dient uitsluitend voor de inhoudelijke afstand; historische uitkomsten en uitvoeringsinformatie daarin zijn geen bewijs voor deze labels.

Leidend zijn Chris’ brede norm B1 en de veldrollen en inhoudelijke T-instructie van het normcontract. Alleen de kern is toetsobject. Bedoeling en casusbron B1 ondersteunen de functieanalyse, maar leveren geen automatisch label. De bron-ID B1 in de JSON-gronden verwijst steeds naar de bron binnen dat G-geval, niet naar Chris’ gelijknamige besluit. De voorstellen zijn per geval inhoudelijk opgesteld; Python verzorgde uitsluitend documentopbouw, posities, tellingen en controle. Geen woordpatroon heeft labels bepaald en er is geen verdeling afgedwongen.

| Voorstel | Aantal |
|---|---:|
| pass | 20 |
| fail | 10 |
| review_required | 10 |
| not_evaluated | 0 |
| not_applicable | 0 |
| onbeslist | 0 |

Alle gevallen hebben een kern en context. Er is geen reikwijdtegrond voor not_applicable. De tien inhoudelijk open functies zijn G003, G006, G010, G014, G018, G022, G026, G030, G034 en G038: telkens botsen een begrips-/resultaatlezing en een handelingslezing zonder leidende keuze. Ze krijgen review_required met elk precies één gerichte vraag; er is geen pass of fail ingevuld om volledigheid te suggereren. Zekerheid hoog betreft de geschiktheid van het voorgestelde oordeel gegeven dit synthetische dossier, ook waar dat oordeel juist inhoudelijke onzekerheid vaststelt. Het betekent geen zekerheid over de nog te kiezen betekenis of over appkwaliteit.

De families tellen 10 begripscriterium_afleiding, 9 normatief_begrip, 10 actorvoorschrift_procedure_discretie, 10 ontbrekende_strijdige_grond en 1 anders. G039 is onder anders opgenomen als beschrijvend procesbegrip. Een proces als begrip is toegestaan; G036 schrijft daarentegen uitvoerderstaken en een deadline voor. In G028 bewijst het annuleringsdeel zelfstandig fail, ook als het eerste deel beschrijvend wordt gelezen. Dit volgt uit de inhoudelijke T-grens voor een zelfstandig aangetoond gebrek.

Geschiktheid: 13 bruikbaar, 21 aanpassen en 6 uitsluiten. Afstand tot het ontwerp: 25 zelfstandig, 9 twijfel en 6 triviale_variant. Dit zijn selectievoorstellen naast het INT-02-oordeel; uitsluiten wist een geval of label niet en aanpassen is geen uitgevoerde wijziging.

| Voorgestelde uitsluiting | Dichtstbijzijnde ontwerp | Concrete herhaling |
|---|---|---|
| G013 | C112 | Plicht van een partij om een overeengekomen prestatie te verrichten. |
| G020 | C102 | Enkelvoudige gebonden actoropdracht bij een feitelijke trigger. |
| G025 | C53 | Constitutief verval van een eerder gevolg door een besluit/rechtshandeling. |
| G028 | C64 | Beschrijvende opening plus aangehecht conditioneel afhandelingsvoorschrift. |
| G032 | C03/C52/C102 | Gebonden actoropdracht verpakt als objectomschrijving. |
| G040 | C83 | Actor handelt naar eigen inzicht wanneer hij een waardering voldoende vindt. |

Twijfel over voldoende ontwerpafstand blijft bij G005, G006, G010, G014, G018, G022, G023, G026 en G038. De JSON noemt per geval de C-ID’s en de resterende verschillen. Andere inhoud binnen dezelfde normfamilie is niet automatisch als triviaal aangemerkt: G027 bevat bijvoorbeeld weging en normalisering, waar C116 alleen een som beschrijft.

Concrete onderlinge overlap is vastgelegd bij G001/G016, G003/G014/G034/G038, G006/G010/G026, G009/G019, G012/G024, G018/G022 en G020/G032. Deze relaties zijn wederzijds geregistreerd. Het zijn selectiesignalen, geen bewering dat de volledige teksten equivalent zijn. Zo voegt G019 een exact paar toe en wisselt G024 ten opzichte van G012 naar een nominale documentomschrijving; die verschillen kunnen contrastwaarde behouden.

Een belangrijke beperking is de sterke functiesturing door bedoeling en bronnen. Vooral de tien open gevallen geven al analytische samenvattingen van tegenstrijdige functies, in plaats van afzonderlijke oorspronkelijke passages. Ook G002, G021, G033, G035 en G039 zeggen expliciet welke handelingslezing niet bedoeld is. Dat helpt het oordeel over deze invoer, maar beperkt de zelfstandige uitdaging van het materiaal. De concrete opmerkingen per geval zijn bedoeld voor latere menselijke selectie of aanpassing; invoer is niet veranderd en er zijn geen hersteldefinities gemaakt.

Documentcontrole: de opgeslagen JSON is integraal teruggelezen. Alle 40 invoer-ID’s staan precies eenmaal in de uitvoer, zonder extra ID’s. Alle 41 kerncitaten en 80 grondcitaten voldoen aan `source[start:end] == citaat`, met nulgebaseerde Unicode-tekenposities en exclusief einde. Alle 10 review_required-gevallen hebben één vraag; de overige 30 hebben null. Elke ontwerpverwijzing bestaat in het register; elke redundantieverwijzing bestaat in de casuspool. De langste labelmotivering telt 49 woorden. De bronhashes komen 4/4 overeen. Het verslag en de definitieve bestanden worden bij oplevering opnieuw gelezen/gecontroleerd; dit is documentverificatie, geen modeltest.

Alle casussen en hun betekenisbronnen zijn synthetisch; niets is als geldend recht gepresenteerd. Er zijn geen andere beoordelaarsbestanden of logs, appcode, ontwikkelfixtures, externe dossiers of afzonderlijke implementatie-/reviewhistorie geraadpleegd. Geen agents, extra CLI-beoordelingssessies, netwerktools, webresearch, API-/appmodelcalls of Gitacties gebruikt. De scheiding is procedureel; technische isolatie is niet aangetoond. De werkwijze gebruikte analysis-mode en verification-before-completion uitsluitend als procedurele skills. Deze sessie heeft alle 40 gevallen gezien en is daarmee uitgesloten van latere ontwikkeling van de O2-prompt of implementatie op basis van deze inhoud. De eventuele 24/16-splitsing blijft buiten deze ronde en volgt pas na menselijke acceptatie.
