# ESS-04 — geïntegreerd besluitvoorstel v2

18 september 2026. Onderzoeksvoorstel voor Chris; nog geen normbesluit of uitvoeringsopdracht. Beide onderzoeken, beide kruisreviews en beide verwerkingen zijn bewaard en gelezen. Deze versie is aangeboden voor de afsluitende Cowork-synthesecontrole; gezamenlijk afgerond wordt pas daarna geclaimd.

## Aanbevolen norm

**Ieder criterium in de definitie is binnen de bedoelde betekenis en context voldoende bepaald om navolgbaar te beoordelen of een geval eraan voldoet.**

De [ASTRA-regel](https://www.astraonline.nl/index.php/Toetsbaarheid) stelt toetsbaarheid van een criterium centraal. Een kwalitatief criterium kan volstaan; een getal bewijst geen toetsbaarheid. Of het kenmerk inhoudelijk juist, brongetrouw, essentieel of voldoende onderscheidend is, blijft een afzonderlijke vraag. Deze uitwerking verplicht niet dat alle gevallen feitelijk bekend of zonder beoordelingsruimte beslisbaar zijn. Coworks criteriumgerichte onderwerp verbetert Codex N1; Codex onderscheid tussen criteriumkwaliteit en gevalsbewijs begrenst de strengere eerste Cowork-formulering.

Voorbeelden: *Veelhoek waarvan alle zijden even lang zijn* is in abstracte geometrie kwalitatief toepasbaar. *Object dat minimaal 80% voldoet* mist een criterium en noemer. *Document waarop de afzender een handtekening heeft geplaatst* kan een helder criterium bevatten terwijl voor één document het bewijs van afzenderschap ontbreekt. Een zichtbare markering bewijst dat niet. Dit zijn synthetische illustraties, geen juridische geldigheidsuitspraken.

ASTRA toont slechts korte numerieke voorbeeldfragmenten; het startpunt ‘nadat het verzoek is ingediend’ in onze historische fixture is lokaal toegevoegd. De bron legt geen algemene getallenplicht op. Een bedoelde open norm wordt niet door een zelfbedachte termijn vervangen; eerst het toepasselijke beoordelingskader bepalen. Een essentieel beperkend kenmerk hoort in de kern, methode/bewijsplaatsen mogen apart.

## Drie hoofdkeuzes

| Keuze | Aanbeveling en alternatief | Gevolg / onderscheidend bewijs |
|---|---|---|
| **1. Indicatorpatronen** | **Neutrale aandachtssignalen voor zowel mogelijke onbepaaldheid als kwantitatieve grenzen.** Cowork stelde deze gemengde richting voor; Codex neemt haar als te kalibreren kandidaat over. Alternatief: huidige richting houden en zes patroongebreken repareren; of tijdelijk alleen vaste reviewvragen tonen. | Nooit pass/fail op een hit. Algemene woorden als bevat/omvat zijn weinig onderscheidend. C05/C08/C11 tonen gemiste signalen; C14 foutieve aanhechting; C12/C13 vormvarianten. Een nieuwe set is nog niet empirisch gevalideerd. |
| **2. Review en vaststelling** | **Voer de bestaande algemene DEF-630-reviewplicht uit via de gedeelde expertbeoordeling, met expliciete regellokale voorwaarden.** Geen extra ESS-04-akkoordknop of eis van positief ESS-04-oordeel aanbevelen. Alternatief: zo’n nieuwe zelfstandige harde ESS-04-poort expliciet besluiten. | Bestaande plicht mag niet vervallen. Coworks aanvankelijke ‘verplichte reviewregels’ is een bruikbaar vertrekpunt, geen blinde mapping naar13 identieke harde poorten. ESS-01/02-besluiten zonder eigen poort blijven staan. Open/negatief wordt door vaststelling geen pass. Algemene reviewregistratie, regeloordeel en formele vaststelling blijven apart. |
| **3. Ontbrekend noodzakelijk gegeven** | **Splits ontbrekende criterium-/betekenisgrond van ontbrekend bewijs over één geval.** Bij eerste: tekortkoming als die vaststaat, anders open met benoemde vraag. Bij tweede: gevalsoordeel onbekend; definitie kan na echte menselijke beoordeling voldoen. Alternatief: alle ontbrekende gegevens als definitie-fail behandelen, wat wij afraden. | C05/N09/N13 verschillen van C06/N17. Niet-uitgevoerde review, lege tekst en technische fout zijn nog andere toestanden. Geen automatisch voldoet bij ontbreken van gegevens. |

**Precisering keuze2:** aanwezigheid alleen is onvoldoende: de integrale beoordeling moet werkelijk uitgevoerd, bevoegd en versiegebonden zijn en de vereiste onderwerpen behandelen. Een lege review, aangeleverd actorlabel of notitie vervangt ontbrekend verplicht bewijs niet. Een na beoordeling gemotiveerd open criteriumoordeel is iets anders dan een niet-uitgevoerde review. De precieze mapping van verplichte kwaliteitscomponenten en bestaande uitzonderingen hoort bij DEF-630. Geen onbekende verplichte component stil passeren.

**Verschil in onderbouwing:** Cowork stelt na verwerking B-I voor: één integrale geldige beoordeling, geen ESS-04-inhoudsblokkade; B-II (slechts tonen) zou expliciete afwijking van DEF-630 zijn. Codex deelt de aanbeveling B-I, maar beschouwt de toepassing van de ESS-01/02-keuze op ESS-04 nog als regellokaal voorstel; die buurregelbesluiten gelden niet automatisch voor alle ESS-regels. Een aparte ESS-04-poort is daarom bij Codex een niet-aanbevolen nieuw besluit, bij Cowork strijdig met zijn bredere lezing van bestaand beleid. Uitkomstadvies is gelijk; besluitstatus niet stil gelijkgetrokken.

Deze keuzes staan samen met de exacte N/G/T/H-uitwerking ter beoordeling. De algemene reviewplicht en afschaffing van totaalscore zijn **bestaand beleid**; indicatorselectie, concrete menselijke uitkomsten en ESS-04-specifieke vervolgvoorwaarden zijn voorstellen. ‘Al het overige is herstel’ is te ruim: opslagvorm en verduidelijkingsflow vragen nog ontwerp. Geen aparte keuze om reeds vastgesteld beleid buiten werking te stellen.

## Wat het bewijs werkelijk laat zien

Op commit `4cdb8ea43` retourneert de onderzochte echte ESS-04-evaluator review_required zonder score. Zowel aangeleverde pass/reviewer-metadata als de14 Cowork-cases veranderen dat niet. `additional_patterns.py` voegt geen ESS-04-patronen toe: het belangrijkste aanvankelijke bewijsgat is gesloten. Vier procentpatronen missen normale spaties/punten na `%`; twee tijdpatronen missen enkelvoud. Dat zijn zes beperkte patroondefecten, geen zes inhoudelijke regeloordelen.

De oude normalisatie verloor reviewvelden; de actuele tegenproef bewaart ze. Wel laat de bestaande legacyproef vier categoriecijfers0.9 staan naast validation_unknown en acceptablefalse. Dit is een generiek contractrisico onder DEF-624/630; we hebben niet aangetoond dat de UI die cijfers toont. De generatie-instructie noemt nog deadlines/aantallen/percentages. Daarmee is sturende tekst bewezen, geen daadwerkelijk verzonnen modelantwoord. Eén getalszin doorstaat extractie en cleaning; opslag en overige teksten zijn daarmee niet getest.

In de onderzochte UI/repository/evaluator ontbreekt een aangesloten versiegebonden ESS-04-reviewroute. Het gelezen schema bewijst niet dat opslag technisch nergens mogelijk is. De gelezen vaststelgate controleert geen algemene review_required-status. De snapshot-YAML staat harde overrides toe, de actieve environment-overlay is onbekend, en CON-01/02 hebben afzonderlijke voorwaarden. Exportvalidatie is conditioneel. We claimen geen nieuw uitgevoerde bypass, volledige import-/review-/exportketen of menselijke acceptatietest.

## Gevolgen voor applicatie en instructies

De exacte vervangteksten en vindplaatsen staan in [instructievoorstellen v3](instructievoorstellen-v3.md). G vraagt onderbouwde criteria zonder verzonnen drempel; T beoordeelt de aangeleverde kern ongewijzigd met aanvullingen herkenbaar apart; H lokaliseert de oorzaak vóór een afzonderlijk betekenisbehoudend voorstel. Geen kwalificatie schrappen alleen om het oordeel gunstiger te maken. De huidige één-zin-uitvoer ondersteunt niet vanzelf verduidelijking: ontbrekende grond moet vooraf of via een afzonderlijk ondersteund resultaat worden afgehandeld, nooit als foutmelding in de opgeslagen definitie.

Een menselijk oordeel legt passage, grond, conclusie en onzekerheid vast, gebonden aan tekst/term/context, relevante bron- en normversie, echte actor/rol en tijd. Gerichte herbeoordeling na materiële wijziging. **Scoreloos contract** expliciet ontwerpen; alleen excluded_from_score behouden is onvoldoende zodra menselijke PASS/FAIL wordt teruggevoerd. no_score is een kandidaat, geen bewezen aangesloten oplossing. Geen AI-jury, tweede verplichte persoon of automatische herstelronde toegevoegd. Gerichte onafhankelijke dubbelbeoordeling is nuttig voor kalibratie; overeenstemming bewijst geen waarheid.

Regelmetadata krijgen brongetrouw thema en ESS-03-relatie; verwar ASTRA-publicatie niet met zelfstandig gelezen Politie-bron. De vijf skillfamilies krijgen gekoppelde teksten: toetsregels, Nederlandse definities, voorbeelden, ontologisch modelleren en UFO. Bestaande CON-01/02- en ESS-01/02-besluiten blijven leidend. Onderliggende paden zijn gecontroleerd. Geen actieve bestanden gewijzigd. De samengevoegde [veldrollen, ingangen en herstelgrenzen](veldrollen-en-keten-v2.md) leggen per veld vast wat toetsobject, bewijs, voorstel of presentatie is.

## Bijlagen, dekking en resterende beperkingen

Het [geïntegreerde register](casusregister-v2.md) bevat37 unieke scenario’s, met zeven historische/Cowork-aliasparen; scenario’s zijn niet aangepast aan de resultaten. [Bron- en bewijsregister v2](bron-bewijsregister-v2.md) koppelt claims aan primaire bron, besluit, statische code of uitgevoerde proef. [Codex-reviewverwerking](codex-reviewverwerking-v1.md) en [Codex-review op Cowork](cowork-uitwisseling/codex-review-op-cowork-v1.md) bewaren de meningsverschillen en correcties. [Coworks verwerking](cowork-uitwisseling/cowork-reviewverwerking-v1.md) trekt onder meer totale beslisbaarheid, de absolute opslagclaim en de blinde regelpoort in. Zijn oorspronkelijke voorkeur verwijdert voldoende wegens overlap met ARAI-03; Codex acht overlap op zichzelf geen uitsluitgrond. Dat beperkte patroonontwerpverschil blijft zichtbaar en wordt via kalibratie beslist. Cowork laat de plaatsing in de Nederlandse-definities-skill redactioneel open; de voorgestelde tekst voert geen nieuwe taalafkeurgrond in.

| Dekking | Waar uitgewerkt |
|---|---|
| Q1 norm/toepasselijkheid; dossier1–3 | Norm hierboven, exacte N2, oorspronkelijke onderzoeken met addenda |
| Q2 context/bron/ontologie/aanvullingen; dossier4–7 | Geïntegreerde veldmatrix in veldrollen-en-keten-v2.md; cases en tekstenv3 |
| Q3 samenhang; dossier12 | Relaties in Q3 van beide onderzoeken; ESS-03-bron en regellokale poortafbakening hierboven |
| Q4 gedrag/score/poort/proeven; dossier8/10/11 | Bewijsregisterv2 en voorafverwachting/scripts/logs |
| Q5 instructies; dossier9 | Exact N2/G2/T2/H2, meldingen, vijf skillfamilies in tekstvoorstelv3 |
| Q6 advies/acceptatie; dossier13/14 | Drie keuzes, geïntegreerde cases; wederzijdse verwerking en synthesecontrole |

Vóór implementatieacceptatie ontbreken volledige eindprompt-, UI-, opslag/readback-, stale-, actor-, vaststel- en exportproeven en deskundige gevalslabels. De actuele ASTRA-pagina is gelezen; oorspronkelijke Politie-norm en volledige ISO-standaarden niet. Onderzoek is geen implementatieacceptatie. Uitvoering vraagt een afzonderlijke opdracht onder bestaande owners; er zijn geen issues, PRs, productwijzigingen of automations aangemaakt.
