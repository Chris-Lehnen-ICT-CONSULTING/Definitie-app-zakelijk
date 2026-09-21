# DEF-606: productbedoeling, toetsregels en skills

11 september 2026 · onderzoek en verbeteradvies · geen implementatie of normwijziging.

**DefinitieAgent hoort gebruikers te helpen een begrip correct af te bakenen, de onderbouwing te controleren en een expert een verantwoord vaststelbesluit te laten nemen. De toetsregels ondersteunen dat proces. Een hoge tekstscore is daarvoor onvoldoende.** DEF-606 levert het fundament voor één uitvoerbaar regelcontract, maar contexttransport, betekeniscontrole, resultaatdoorgifte en normherkomst zijn nog niet volledig geleverd. De zes definitie-skills bevatten bruikbare methoden én aantoonbare fouten; ze kunnen dus niet ongewijzigd als referentie voor de app dienen. [S1–S4]

Dit rapport verbreedt de eerdere DEF-606-analyse met productbedoeling, primaire standaarden, skillcontrole en nieuwe gerichte gedragsproeven. De bestaande roadmap en het gerichte ARAI-06-besluit blijven leidend. De overige voorstellen voor 17 eigen regels zijn nog geen vastgesteld beleid. [S1, S5]

## 1. Onderzoeksbasis en afbakening

- Live opgehaald: DEF-606, DEF-622/623/624/625, besluitcomments bij DEF-622/623/625, masterplan, productscope en het voorstel voor 17 eigen regels inclusief ARAI-06-verduidelijking.
- GitHub-main opnieuw read-only gecontroleerd: `d68a98a909630e15db6e1cb9c9c8171f957bff9d`. De schone bestaande onderzoeksclone `/private/tmp/def606-analyse-20260911` staat op exact die commit. De gebruikerswerkboom blijft op `feature/DEF-700-ui-smoke-prototypes`.
- Alle 53 JSON-records en twaalf skillbestanden geïnventariseerd. De twaalf bestanden onder `~/.agents/skills` zijn bytegelijk aan de corresponderende bestanden onder `~/.claude/skills`; dit bewijst niets over verpakte of andere installatiekopieën.
- Opnieuw 803 bestaande gerichte tests uitgevoerd: **803 passed, 7,81 s, exit 0**. Daarnaast nieuwe offline diagnostiek met echte tijdelijke SQLite-opslag via manager én productiecache; die reproduceert de hieronder genoemde fouten. Geslaagde diagnostische assertions bevestigen de defecten, geen gerepareerde applicatie.
- Twee oude WIP-handovers overeenkomstig de sessie-instructie gearchiveerd. Geen HANDOVER-marker aangetroffen in `.claude/CLAUDE.md`. Geen applicatie-, prompt-, skill- of normbestanden aangepast; geen externe publicatie of issuestatus gewijzigd.

Het [bronnen- en verificatiebestand](2026-09-11-def606-productonderzoek-bewijs/bronnen-en-verificatie-v1.json) bewaart de opgehaalde Linear-inhoud, 53 records, twaalf skillbestanden, 88 bronhashes en testuitvoer. De [proeven](2026-09-11-def606-productonderzoek-bewijs/proeven-v1.json) bewaren invoer, werkelijke uitkomsten en het uitgevoerde diagnostische script. [S2, S3]

## 2. Wat de app volgens de vastgelegde bedoeling moet doen

De productscope en het masterplan beschrijven een hulpmiddel voor projectgroepen en organisaties, aanvankelijk in de strafrechtketen. Het ondersteunt opstellen, toetsen, reviewen en menselijk vaststellen volgens bronnen, toepasselijke regels en begrippenkaders. Vaststelbaarheid vereist onder meer brongetrouwheid, correcte genus en onderscheidende kenmerken, geen kritieke overtredingen, provenance en goedkeuring door een bevoegde expert. [S1]

Daaruit volgt deze productketen; dit is een synthese van de bestaande besluiten, geen nieuwe roadmap:

| Moment | Verondersteld productgedrag | Rol van toetsregels |
|---|---|---|
| Begrip afbakenen | Term, bedoelde betekenis, drie contextlijsten, categorie en bestaande begrippen bijeenbrengen. Minstens één contextwaarde is vereist. | Toepasselijkheid en benodigde invoer bepalen; ontbrekende context zichtbaar maken. |
| Formuleren | Een brongetrouwe omschrijving met genus en onderscheidende kenmerken opstellen. Bronnen, toelichting en voorbeelden blijven herkenbare aanvullende informatie. | Gerichte generatie-instructies geven, met behoud van normuitzonderingen. |
| Uitsluitend toetsen | De aangeleverde tekst beoordelen; eventuele verbetertekst afzonderlijk aanbieden. | Origineel blijft beoordelingsobject. Geen stil opschonen vóór het oordeel. |
| Samenhang controleren | Vergelijken met hoofdbegrippen, verwante begrippen, voorkeurstermen en repository. | Echte relaties en gegevens beoordelen; ontbrekende invoer nooit als slagen uitleggen. |
| Reviewen en vaststellen | Een expert ziet bevindingen, onzekerheden en onderbouwing en neemt het inhoudelijke besluit. | Regelstatus, score, dekking en blokkade onderscheiden; bewijs bewaren onder DEF-626 en vaststelpolicy onder DEF-630. |

De lokale CON-01-keuze blijft: context is recordmetadata en wordt inhoudelijk verwerkt zonder contextlabels letterlijk in de definitie op te nemen. Duplicaatidentiteit berust op term plus genormaliseerde context; de vastgelegde force-route vereist een auditreden. Dat is geen opdracht om een brondefinitie stilistisch origineel te maken. [S4]

**Twee soorten herkomst moeten herkenbaar blijven:** de bron en versie van een toetsregel, en de bronpassage waarop een definitie berust. Een ASTRA-link bij een regel bewijst niet dat een gegeven definitie juridisch klopt; een wetsverwijzing bij een definitie bewijst niet dat de gebruikte toetsregel correct is uitgevoerd. Dit onderscheid volgt uit de verschillende contracten van DEF-625 en de productscope. [S1, S4]

## 3. Wat er nu werkt en waar het bewijs breekt

De root-YAML wijst de 53 JSON-records aan. Records declareren hun evaluator, invoervereisten, automatiseringsklasse en scorepolicy. Manager en productiecache laden dit contract; de historische losse Pythonvalidatorlagen worden niet alsnog aangesloten. De contract-/cache-/statusgates hebben gericht groen testbewijs. [S2, S3, S6]

De verse inventaris telt **37 automated, 12 review_required, 4 not_evaluated; 21 scored en 32 excluded_from_score**. Dit zijn recorddeclaraties. De werkelijke status kan per aanroep veranderen wanneer invoer ontbreekt. Het is dus geen meting dat 37 regels inhoudelijk betrouwbaar worden beoordeeld. Alle 53 regelidentiteiten staan ook in de toetsregels-skill. [S2, S3]

| Bevinding op actuele main | Vers bewijs | Verbetering binnen bestaande scope |
|---|---|---|
| Context verdwijnt tussen Definition en validator. | Zelfde dummyrecord: directe service `DUP_01=fail`, via V2-orchestrator `not_evaluated`, bij beide laadpaden. Ontvangen kwargs missen de contextlijsten. | DEF-622: context, categorie en recordidentiteit aantoonbaar doorgeven; bij bewerken eigen record herkennen. |
| CON-01 beoordeelt de contextinvariant niet volledig. | Zonder context `CON-01=pass`; geselecteerd `Team Zilver` letterlijk in tekst eveneens `pass`. Workflow geeft bij ontbrekende context `override_required`. | DEF-622: geselecteerde waarden controleren en contextminimum buiten de algemene override houden. |
| Woorduitgangen worden als grammaticaal bewijs gebruikt. | `besluit` krijgt VER-03-fail; `gegeven` VER-01-fail; `kosten` met enkelvoudige definitie eveneens VER-01-fail. | DEF-623: bestaande taalbronnen, toepasselijkheid per lemma en onzekerheid naar review volgens besluit. |
| Een normuitzondering verdwijnt in de evaluator. | `Voertuig dat niet over rails rijdt.` krijgt INT-08-fail, hoewel de eigen JSON precisering door ontkenning in een relatieve bijzin toestaat. Beide laadpaden geven dit resultaat. | DEF-624: uitzondering als directe casus opnemen; alleen betrouwbaar beslisbare gevallen automatisch beoordelen. Externe ASTRA-detailactualiteit hier niet bevestigd. |
| Lidwoordadvies blijft via een andere regel inhoudelijk meetellen. | `Een veelhoek met drie zijden.` geeft ARAI-06-fail én scorerende STR-01-fail; zonder `Een` zijn beide pass. STR-01 krijgt het lidwoordpatroon uit `additional_patterns.py`. | ARAI-06-besluit onder DEF-624 moet over alle betrokken regels heen gelden; alleen ARAI-06 aanpassen is onvoldoende. |
| Resultaatmetadata gaat verloren. | ServiceAdapter behoudt de discriminator maar verliest onder meer `evaluation_coverage`, `rule_statuses` en `review_required`. Een resultaat zonder status en met `is_acceptable=true` passeert de mapper; degraded-resultaat mist de discriminator. | DEF-624: volledig consumercontract en veilige afhandeling van ontbrekende status; opslagverantwoordelijkheid blijft DEF-626. |
| Normherkomst is geen volledig runtimecontract. | 0 van de 53 JSON-records heeft een `provenance`-blok. Beschrijvende bronvelden zijn wel aanwezig. | DEF-625: bronrevisie, snapshot, bron-/projectkeuze en gemotiveerde afwijking valideren. |

De twee driehoekproeven bewijzen het afzonderlijke lidwoordeffect op ARAI-06/STR-01. De totaalscores bevatten ook andere regels en lengteheuristieken; ik behandel het scoreverschil niet als een geïsoleerde effectmeting. De proeven bewijzen evenmin dat iedere UI-route dezelfde optionele cleaning-service gebruikt. [S2]

Een extra aandachtspunt is de scorepolicy zelf. De rootconfig noemt prioriteitsgewichten 1,0/0,8/0,5, terwijl `_calculate_rule_weight` standaard 1,0/0,7/0,4 gebruikt. De service vermenigvuldigt de geaggregeerde score bovendien met een woordenaantalfactor, bijvoorbeeld 0,75 onder twaalf woorden. Dit zijn gelezen uitvoeringsregels, geen door dit onderzoek goedgekeurde kwaliteitsmaatstaven. De skill beschrijft die volledige berekening niet. Maak de bestaande policy eerst reproduceerbaar en herleidbaar; kies geen nieuwe gewichten of drempels zonder inhoudelijk besluit. [S6]

## 4. Controle van de zes skills

De skills zijn bekeken als onderzoeksobject. Hun technische beschrijvingen en voorbeelden zijn geen onafhankelijk bewijs dat het product werkt of dat een norm is vastgesteld.

| Skill | Bruikbaar | Concrete correctie of aanscherping |
|---|---|---|
| `toetsregels` | Volledige 53-ID-dekking en verband tussen regel en generatie-instructie. | Beschrijft nog een Pythonvalidator per regel en parallelle uitvoering. Mist de vijf uitkomsten en volledige score-uitsluitingen. Samenvatting telt 52 prioriteiten; records tellen 25 hoog/26 midden/2 laag. Aanbevelingen zijn 39 verplicht/6 aanbevolen/8 optioneel. DUP-instructie over originaliteit corrigeren. |
| `nederlandse-definities` | Genus/differentia, noodzakelijke en voldoende kenmerken, te brede/te smalle definitie herkennen. | Absoluut lidwoordverbod onderscheiden van lokale generatiestijl en uitsluitend toetsen. Uitzonderingen op ontkenning en contextgevoelige formuleringen behouden. Eigen voorkeuren niet zonder specifieke bron als ISO-eis presenteren. |
| `juridisch-nederland` | Domein, rechtsgebied en wettelijke grondslag expliciet onderzoeken. | De tabel noemt bij gevangenhouding ten onrechte de rechter-commissaris na inverzekeringstelling. Rechtspraak onderscheidt bewaring door de rechter-commissaris en gevangenhouding door de raadkamer. Deze voorbeeldfout mag niet als betrouwbare generatiebron blijven gelden. Andere juridische voorbeelden zijn niet integraal geverifieerd. |
| `ufo-ontologie` | Benoemt zelf dat de vier appcategorieën een reductie zijn en RESULTAAT geen direct UFO-equivalent heeft. | Houd modeltheorie, lokale mapping en classificatieadvies gescheiden. `beschikking` staat bij TYPE in deze referentie en bij RESULTAAT in de juridische skill; een vaste termmapping zonder betekenis/context is onvoldoende. Dit onderzoek stelt geen vervangend UFO-model vast. |
| `ontologisch-modelleren` | Eerst domein afbakenen, bronnen verzamelen, relaties en genus onderzoeken. | De passage dat iedere term precies één begrip heeft, is als algemene NL-SBB-claim te sterk: homonieme termen kunnen meerdere begrippen aanduiden. Een model opstellen garandeert ook niet automatisch volledigheid of juiste semantiek. SAM-automatisering als gewenste, nog te bewijzen capaciteit beschrijven. |
| `voorbeelden-generatie` | Kenmerken ontleden en doelgericht positieve, negatieve en grensgevallen maken. | `extensie ⊆ intensie` vergelijkt instanties met kenmerken en is onzuivere notatie. Gebruik: iedere positieve casus voldoet aan alle kenmerken. Laat verwachte labels onafhankelijk onderbouwen; uit dezelfde definitie gegenereerde voorbeelden kunnen dezelfde fout bevestigen. Voorbeelden leveren geen vervangend bewijs voor een repositorybrede cycluscontrole. |

Bronnen: de twaalf vastgelegde skillbestanden [S3], [Rechtspraak](https://www.rechtspraak.nl/onderwerpen/voorlopige-hechtenis) en [NL-SBB §2.4.1.1](https://docs.geostandaarden.nl/nl-sbb/nl-sbb/#termen). De uitspraak over voorbeelden en onafhankelijke labels is een methodologisch verbeteradvies; de juridische juistheid van alle voorbeeldcasussen is niet onderzocht.

Ook delen skills en appinstructies dezelfde betekenisverschuivingen: bij SAM-08 wordt dezelfde *definitiestructuur* gevraagd waar de JSON dezelfde definitie verlangt; bij INT-08 verdwijnt de uitzondering; bij DUP_01 wordt originaliteit gevraagd. Alleen skills met de promptteksten synchroniseren zou deze fouten dus bestendigen. [S3, S6]

## 5. Wat externe bronnen toevoegen

De ASTRA-standaard beschrijft definitiekwaliteit als ondersteuning van gedeelde, eenduidige taal in de strafrechtketen. Dat ondersteunt de nadruk op betekenis en samenwerking. De opgehaalde pagina toont een oudere besluitstand; dit onderzoek leidt daar geen actuele formele status van alle detailregels uit af. [ASTRA](https://www.astraonline.nl/index.php/Standaard_Definitiekwaliteit)

NL-SBB onderscheidt definitie, toelichting, voorbeelden, termen, relaties en bronnen. Het beschrijft zowel volledige zinnen als lemmadefinities en kiest zelf de zinsvorm. Daaruit volgt niet dat de lokale artikelvrije generatiestijl moet verdwijnen; wel dat die niet als universele inhoudelijke geldigheidseis mag worden voorgesteld. [NL-SBB §2.2](https://docs.geostandaarden.nl/nl-sbb/nl-sbb/#conventies)

SKOS legt maximaal één voorkeursterm per taal per resource vast. Het verbiedt hiërarchische cycli niet algemeen; toepassingen moeten daar zelf beleid voor voeren. Voor DEF betekent dit: voorkeurstermen en relaties zijn bruikbare bouwstenen, maar SKOS-validiteit vervangt SAM-05 of inhoudelijke beoordeling niet. De bestaande DEF-eis tegen definitiecycli blijft gelden. [W3C SKOS §5.4 en §8.6.8](https://www.w3.org/TR/skos-reference/)

De officiële ISO-pagina bevestigt dat ISO 704:2022 relaties tussen objecten, begrippen, definities en aanduidingen behandelt. De volledige normtekst is hier niet gecontroleerd. Een generiek beroep op ISO rechtvaardigt daarom geen afzonderlijk woordverbod of automatische goedkeuring. [ISO 704:2022](https://www.iso.org/standard/79077.html)

## 6. Verbeteradvies: één normbetekenis, expliciete beoordeling, controleerbare hulp

**1. Maak per regel een kort normdossier onder het bestaande contract.** Beschrijf normdoel, bron en versie, toepasselijkheid, vereiste invoer, uitzonderingen, evaluatiemethode, betekenis van iedere uitkomst en goedgekeurde lokale afwijking. Leid de gedeelde uitleg en technische inventaris daaruit af. Generatie-instructie, evaluatie en revieweruitleg mogen verschillende teksten zijn, mits ze dezelfde norm en uitzonderingen respecteren. Dit sluit aan op DEF-624/625; het introduceert geen tweede regelsysteem.

**2. Herstel de context- en resultaatketen als eerste functionele stap.** De evaluator heeft de bedoelde betekenis/context en record-ID nodig; de reviewer heeft het volledige resultaat nodig. Een ontbrekende status of ontbrekende bron krijgt een zichtbare consequentie. De bijbehorende acceptatiecriteria bestaan al onder DEF-622/624; bouw is in deze opdracht niet gestart.

**3. Behandel taalpatronen als indicator zodra zij de norm niet volledig beslissen.** Een treffer op `niet`, `kan`, `-en` of `-t` is op zichzelf geen inhoudelijk oordeel. Voor vastgelegde VER-scope geldt al: onzekerheid naar review. Voor andere regels vraagt een veranderde automatiseringsklasse een gemotiveerde beoordeling onder DEF-624. De onbevestigde 17-regelvoorstellen blijven voorstellen.

**4. Toon gebruikers vier afzonderlijke antwoorden.** Welke regels zijn beoordeeld? Welke bevindingen zijn er? Welke oordelen ontbreken of vragen review? Wat betekent dat voor de volgende handeling? Een percentage kan als aanvullende samenvatting blijven bestaan, maar mag deze antwoorden niet vervangen. Een mogelijke presentatie is bijvoorbeeld: “Toetsing uitgevoerd; drie controles vragen beoordeling; broncontrole ontbreekt.” Dit is een weergavevoorstel, geen actuele screenshot of gemeten status.

**5. Gebruik de skills voor methode en uitleg, met toetsbare herkomst.** Laat `toetsregels` actuele contractvelden lezen in plaats van tellingen en scorepolicy over te schrijven. Laat `nederlandse-definities` formuleren, `juridisch-nederland` bronnen/context onderzoeken, `ufo-ontologie` categorieadvies onderbouwen, `ontologisch-modelleren` relaties controleren en `voorbeelden-generatie` casussen ontwerpen. Voeg per skill duidelijk toe wat advies, lokale policy, bewezen functionaliteit en nog gewenste functionaliteit is. Het concrete correctiepakket staat in §4; niets is geïnstalleerd of aangepast.

**6. Bewijs kwaliteitsverbetering met onafhankelijk beoordeelde gevallen.** Maak de 44 bestaande voorbeeldparen direct uitvoerbaar en voeg grensgevallen toe. Leg per geval context, normversie, verwacht oordeel en rationale vast vóór de appuitkomst wordt bekeken. Meet per regelterrein foutieve afkeur, gemiste fouten en onthouding/review afzonderlijk. Verander de drempels niet om bestaande proeven groen te krijgen. Dit ondersteunt DEF-624 en de latere goldsets uit het masterplan; het vervroegt geen pilot of modelbenchmark.

## 7. Concrete acceptatiegevallen voor een latere uitvoering

Deze tabel is een onderzoeksuitkomst en casusvoorstel, geen nieuw geïmplementeerde testsuite.

| Casus | Te bewijzen gedrag | Bestaand eigenaarschap |
|---|---|---|
| Zelfde term en context, andere formulering | Blijft duplicaat; herschrijven om de check te omzeilen helpt niet. | DEF-622 |
| Zelfde term, andere context | Verschillende betekenis/context kan apart bestaan. | DEF-622 |
| Bestaand record bewerken | Eigen record herkenbaar; andere echte duplicaten blijven controleerbaar. | DEF-622 |
| Alle contextlijsten leeg | Zichtbare, niet algemeen overridebare contextfout. | DEF-622 |
| `besluit`, `gegeven`, `kosten` | Woordsoort, getal en toepasselijkheid correct; twijfel niet als zekere afkeur. | DEF-623 |
| Betekenisvolle beperkende ontkenning | Niet uitsluitend door `niet` afkeuren; normuitzondering aantoonbaar toepassen. | DEF-624 |
| Definitie met beginnend lidwoord uitsluitend toetsen | Origineel blijft intact; hoogstens stijladvies; ook STR-01 of andere regels veroorzaken geen indirecte inhoudelijke afkeur vanwege dat lidwoord. | DEF-624, ARAI-06-besluit |
| A→B→A en A→B→C→A versus directe lemmaherhaling | Begripsrelaties echt gebruiken en directe/indirecte controle onderscheiden; geen repository betekent geen bewezen acycliciteit. | DEF-623 |
| Synoniemen versus homoniemen | Dezelfde betekenis koppelen aan voorkeursterm; dezelfde tekenreeks niet automatisch hetzelfde begrip noemen. | DEF-623/624 |
| Adapter → UI → opslag/export | Ontbrekende of verloren status wordt geen geldig kwaliteitsbewijs; dekking/review blijven zichtbaar volgens consumercontract. | DEF-624; persistentie DEF-626, vaststellen DEF-630 |
| Regelbron gewijzigd | Drift ter beoordeling aanbieden; runtime verandert niet automatisch mee. | DEF-625 |

Laat toepasselijke gevallen via manager én cache lopen en bewijs daarnaast de echte V2-/repositoryroute. Leg tekst vóór en na eventuele generatieopschoning apart vast. Bij uitsluitend toetsen blijft de originele invoer leidend. Deze verificatie sluit het gat dat de huidige 803 groene contracttests naast aantoonbare betekenisfouten laten bestaan. [S2, S3, S5]

## 8. Conclusie en beperkingen

**DEF-606 verdient afronding als bewijs van de volledige regelbetekenis in de gebruikersketen.** Contexttransport is de eerste functionele breuk. De inhoudelijke verbetering is breder: uitzonderingen bewaren, semantische twijfel zichtbaar maken, bewijs meenemen en de skills corrigeren tegen hetzelfde normdossier. De huidige skills bevatten zowel documentatiedrift als inhoudelijke bronfouten.

Beperkingen: geen volledige UI-doorloop, geen complete testsuite/lint nodig of uitgevoerd voor dit onderzoek zonder productwijzigingen, geen live AI-kwaliteitstest, geen onafhankelijke menselijke normreview en geen formele ISO/UFO/NL-SBB-conformiteitsclaim. ASTRA-overzicht en INT-08-detailpagina waren via de browser niet bereikbaar; de volledige 36-regelactualiteit en historische prioriteitsverschillen zijn niet opnieuw extern geverifieerd. De interne INT-08-tegenstrijdigheid is wél vers functioneel bewezen. De aangehaalde juridische correctie is gericht geverifieerd; de overige juridische skillinhoud niet integraal.

## Bronnen

- **S1:** [Masterplan DefinitieAgent Kwaliteitsketen](https://linear.app/definitie-app/document/implementatieplan-definitieagent-kwaliteitsketen-645f1330ac28), [Productscope en definitiekwaliteitsbesluiten](https://linear.app/definitie-app/document/productscope-en-definitiekwaliteitsbesluiten-2026-08-10-53c1afe6bc69), [DEF-606](https://linear.app/definitie-app/issue/DEF-606). Live opgehaald; complete ontvangen inhoud in S3.
- **S2:** [Nieuwe offline proeven, invoer/uitvoer en script](2026-09-11-def606-productonderzoek-bewijs/proeven-v1.json).
- **S3:** [Bronnen, 53 records, twaalf skills, 88 hashes en testbewijs](2026-09-11-def606-productonderzoek-bewijs/bronnen-en-verificatie-v1.json).
- **S4:** [DEF-622](https://linear.app/definitie-app/issue/DEF-622), [DEF-623](https://linear.app/definitie-app/issue/DEF-623), [DEF-624](https://linear.app/definitie-app/issue/DEF-624), [DEF-625](https://linear.app/definitie-app/issue/DEF-625), inclusief genoemde besluitcomments.
- **S5:** [Voorstel 17 eigen regels, inclusief afzonderlijk ARAI-06-besluit](https://linear.app/definitie-app/document/def-625-stap-2-besluitvoorstel-voor-17-eigen-toetsregelaanvullingen-c3204b3f1f23).
- **S6:** Code op gecontroleerde main: [rootcontract](/private/tmp/def606-analyse-20260911/config/toetsregels/toetsregels_config.yaml:1), [morfologie](/private/tmp/def606-analyse-20260911/src/services/validation/evaluators/lemma_morphology.py:39), [context](/private/tmp/def606-analyse-20260911/src/services/validation/evaluators/context_metadata.py:61), [promptinstructies](/private/tmp/def606-analyse-20260911/src/services/prompts/modules/json_based_rules_module.py:254), [extra STR-01-patroon](/private/tmp/def606-analyse-20260911/src/validation/additional_patterns.py:42), [scoregewichten](/private/tmp/def606-analyse-20260911/src/services/validation/modular_validation_service.py:703), [lengtefactor](/private/tmp/def606-analyse-20260911/src/services/validation/modular_validation_service.py:1051).
- Primaire externe bronnen staan direct bij de bijbehorende claims in §4–5. ISO beperkt tot officiële abstract/metadata; ASTRA beperkt tot bereikbare standaardpagina.
