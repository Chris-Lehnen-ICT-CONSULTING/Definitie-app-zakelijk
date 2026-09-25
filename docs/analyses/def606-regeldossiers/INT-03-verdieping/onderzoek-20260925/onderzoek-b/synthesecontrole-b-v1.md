# Synthesecontrole B — INT-03 — v1

25 september 2026. Onderzoeker B, Codex CLI, GPT-6 Astra, reasoning high. Gecontroleerd: `gedeeld/synthese-v1.md`, SHA-256 **0065ec61dc0fff50902061a722698f8ca6c8cc2d4b2d54738df95f89e822ad4e**; hash komt overeen met de opdracht. Regelnummers hieronder verwijzen naar deze exacte versie.

**Oordeel: synthese-v2 is nodig.** De kernrichting en veel reviewcorrecties zijn behouden. De concrete generatie-/toetsteksten zijn echter nog niet onderling consistent, enkele voorkeuren zijn samengevoegd en bewijsgrenzen zijn op onderdelen versmald of te stellig weergegeven. Hieronder staan de gevraagde correcties; geen daarvan is door B in de synthese aangebracht.

## Leesbasis en methode

Volledig gelezen: synthese-v1, A’s aanvulling-a-v2 en verwerking-a-v1, D’s aanvulling-d-v1. Vergeleken met de eerder in deze sessie geschreven/gelezen B-v2, B-reviews op A/C en verwerking-b-v1. Aanvullend gericht gecontroleerd: C-v2 §T en G, C’s tweede omvangmeting, D’s eerste/tweede proefuitkomsten en D-casus E04-v2. De service-errorgrens is gericht herlezen. Branch en commit blijven `onderzoek/DEF-772-INT-03-20260925` / `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`.

Methodiek: toetsregel-onderzoek, analysis-mode en verification-before-completion. De voorgeschreven Skill-aanroepen voor research-dispatch, requesting-code-review en analysis-mode gaven “MCP tool call requires approval, but approval policy is never”; lokale instructies zijn gebruikt. Research-dispatch ontbrak op `~/.agents/skills/research-dispatch/SKILL.md` en was leesbaar via `~/.claude/skills/research-dispatch/SKILL.md`. De code-reviewskill sluit documentonderzoek uit van de programmeerworkflow. De expliciete opdracht bepaalt hier de rol en uitvoerlocatie: geen nieuwe pipeline, sessies, issues of wijzigingen buiten onderzoek-b. Alle verplicht te lezen onderzoeksstukken waren leesbaar.

Geen nieuwe appproef of modelcall: de concrete geschilpunten zijn beslisbaar door tekstvergelijking, bestaande versiegebonden artefacten en gerichte broncontrole. D’s uitvoering is niet door B herhaald. De proefscript-/code-/verwachtingshashes en gebruikte stukken worden in manifest-b-v3 gebonden.

## Concrete punten

### SB-01 → §3/K3, r. 37–41 en 57 → bevestigd, met begrenzing → redactioneel

**Grond:** mijn voorkeur staat correct: alleen INT-03 contextvrij als eerste stap; C kiest de hele INT-module. C’s nieuwe `proefuitkomsten-c-v2.json` meet nu daadwerkelijk 4.205 INT-tekens, 2.461 zonder voorbeelden en 607 voor INT-03. Dat vervangt het eerdere ongeïsoleerde circa-10K-argument waarop BC-13 wees.

**Gevraagde correctie:** behoud K3 en label de cijfers als omvang van de **huidige gemeten variant**. Zij zijn geen meting van de nieuwe langere instructie en voorbeelden. “G en T gelijk voor de hele categorie” beperken tot instructiedekking: het bewijst geen gelijke normuitvoering of modelnaleving. Geen wijziging van B’s smalle voorkeur.

### SB-02 → §1/K6 en §7, r. 13, 60 en 75 → standpunt deels correct, verschil te grof → materieel

**Grond:** B-v2 Q1/D1 verlangt een zelfstandig leesbare kern. “B: onvoldoende” betekent niet automatisch review in plaats van fail: een bewezen ontbrekende verwijzing faalt onder T-B1. C-v2 sluit het losse lemma inmiddels eveneens uit; A sluit zich daarbij aan. Dan is “B onvoldoende versus C/A geen antecedent” op zichzelf geen overblijvend normverschil. Bovendien bevatten A-E09 (“term waarvoor deze definitie geldt”) en C-E11 (“voorschrift dat bepaalt hoe deze regel wordt toegepast”) meer dan alleen een kaal voornaamwoord met verborgen lemma; hun volledige constructie moet worden beoordeeld (BC-04).

**Gevraagde correctie:** scheid (a) gedeelde voorgestelde kernscope, (b) de nog door Chris te kiezen alternatieve scope lemma+kern, en (c) betwiste casusinterpretaties. Gebruik bij een echte ontbrekende referent onder kernscope “voldoet niet”; behoud de vraag naar bedoeling apart. Presenteer de genoemde casussen niet als sluitend bewijs dat het lemma steeds het enige antecedent is.

### SB-03 → §2-resultaatcontract en §7, r. 27 en 75 → B’s fail-standpunt correct, consensusclaim onjuist → materieel

**Grond:** B T-B1 en verwerking RB-03/09 onderscheiden bewezen ambiguïteit van ontbrekende herstelbedoeling. D T-D1 doet dit ook; A-v2 zegt B te volgen. C-v2 §T koppelt fail nog letterlijk aan een vaststaande bedoeling. De synthese benoemt dat verschil terecht, maar zet erboven “A/B/C/D eens”.

**Gevraagde correctie:** vervang het consensusetiket door “gedeelde uitkomstcategorieën; besliscriterium nog betwist”. Leg als afzonderlijke contractkeuze vast: B/A/D adviseren fail **plus** herstelvraag bij bewezen onduidelijkheid; C’s huidige tabel wijkt af. Een nog onzekere taalkundige beoordeling blijft review. Deze keuze moet vóór het vastzetten van referentieoordelen worden opgelost, niet als twee uitwisselbare succesuitkomsten blijven bestaan.

### SB-04 → §1/K6/K7 en §2, r. 13, 27, 60–61 → statusvoorkeur B/D onvoldoende weergegeven → materieel

**Grond:** B-v2 D4 en D-v1 D-B02 kiezen **voldoet na inhoudelijke controle** bij een niet-lege kern zonder verwijzende functie; niet van toepassing is voor beiden een afzonderlijke productvariant. A kiest n.v.t.; C-v2 noemt beide. “n.v.t./voldoet — A/B/C/D” verbergt de voorkeur. “Loos het n.v.t.” kan bovendien onbedoeld het oordeel over de hele definitie bepalen, terwijl andere woorden daarin wél verwijzen.

**Gevraagde correctie:** maak K7 werkelijk tweekeuzig met voorkeuren en gevolgen voor dekking/label. Zet bij loos het: “dit voorkomen vraagt geen referentiebeoordeling; beoordeel de overige verwijzingen”. Geen automatische n.v.t. voor een complete zin vanwege één niet-verwijzend woord.

### SB-05 → §3 exacte G-tekst, r. 40 → geen gelijkwaardig alternatief voor B-G-B1 → materieel

**Grond:** de gekozen tekst vraagt “lever dan één voorlopige kandidaat” wanneer de bedoeling onbekend is. B-v2 G-B1/G-B2 en RB-07 vullen die bedoeling niet in en eisen een aantoonbare afzonderlijke uitvoerroute; BC-14 vroeg expliciet hoe zo’n kandidaat veilig kan blijven. “Verzin geen antecedent” plus “voorlopige kandidaat” bepaalt nog niet welke inhoud mag worden ingevuld of welke status zichtbaar blijft. De opmerking over een niet aangetoonde vraagroute lost dat niet op.

**Gevraagde correctie:** kies één exacte G-variant. Mijn voorkeur blijft de korte B-G-B1 met G-B2 als uitvoervoorwaarde. Wordt de voorlopige-kandidaatroute gekozen, leg dan vast: geen gegokte referent, geen claim van geslaagd herstel, herkenbaar onopgeloste betekenis, vraag buiten het definitieveld en bewezen transport. Label dit als afwijkend ontwerp, niet als gelijkwaardig aan B. Neem ook de uitzondering voor niet-verwijzend gebruik en toestemming voor duidelijke vooruitverwijzing in het daadwerkelijke generatiepakket op.

### SB-06 → §1 norm/uitzonderingen en §3 G, r. 11–13 en 40 → te absolute grammaticale formuleringen → materieel

**Grond:** B-v2 Q1/S9 zegt dat wie/wat een **ingesloten antecedent** kan hebben en geen verzonnen eerder naamwoord nodig heeft. “Ingesloten vormen vragen geen antecedent” is iets anders. Verder heeft de norm geen positie-eis, maar de G-tekst voegt “geen tussenliggend naamwoord dat als antecedent kan worden gelezen” toe. Dat mag geen zelfstandige mechanische nabijheidseis worden; meerdere naamwoorden bewijzen geen twee plausibele lezingen. De gelezen taalbronnen zijn onderbouwing, geen bewijs voor iedere afzonderlijke het/er/dat-constructie.

**Gevraagde correctie:** formuleer “geen afzonderlijk expliciet voorafgaand naamwoord vereist bij een ingesloten antecedent; beoordeel het bedoelde bereik”. Behoud in G uitsluitend de inhoudelijke eis van eenduidigheid, met eventuele plaatsingsvoorkeur als stijl. Schrijf bij functies consequent “voor zover hier niet-verwijzend gebruikt”. Dit herstelt de aansluiting tussen norm, G en T.

### SB-07 → §2 T-a zonder hit, r. 30 → instructie verzwakt de reviewplicht → materieel

**Grond:** “beoordeel bij twijfel” maakt beoordeling optioneel op basis van twijfel die de onvolledige signaalhulp niet kan vaststellen. B T-B1 en D T-D1 verlangen inhoudelijke beoordeling ook zonder treffer. De waarschuwing dat het/zijn/haar/dat niet worden gesignaleerd kan bovendien verouderen zodra K4 uitbreiding invoert.

**Gevraagde correctie:** gebruik: **“Geen patroonsignaal gevonden; de inhoudelijke beoordeling is nog niet uitgevoerd en blijft nodig.”** Eventuele dekkingswaarschuwing aan de feitelijke patroonversie binden. Noem een getroffen token eerst “passage”; de grammaticale verwijzingsfunctie is nog niet door regex bewezen. Behoud de open status totdat een mens of afzonderlijk geautoriseerde evaluator oordeelt.

### SB-08 → §2 meldingen via drie documenten, r. 33 → geen consistente definitieve meldingenset → materieel

**Grond:** C-v2 §T bevat nog “die → gebeurtenis” voor het ASTRA-goede voorbeeld; de twee betrekkelijke die-vormen verwijzen naar omstandigheden (BC-09). A-v2 §5.2 noemt bij het-fout omgeving/gebeurtenis zonder volledige casusgrond en laat “deze kan naar medewerker of collega” als reviewmelding staan, terwijl A-E07 en B’s criterium die bewezen ambiguïteit afkeuren. De verwijzing naar drie tabellen neemt deze tegenstrijdigheden mee de synthese in.

**Gevraagde correctie:** selecteer één exacte meldingenset met stabiele casusverwijzingen. B T-B1 kan als basis dienen na besluit K7. Corrigeer C’s foutieve pass-uitleg, motiveer plausibele kandidaten en scheid review-onzekerheid van bewezen ambiguïteit plus ontbrekende herstelgrond. Een verwijzing naar conflicterende bijlagen is geen geïntegreerd contract.

### SB-09 → §2 T-c en K8, r. 27, 32 en 62 → poortkeuze opnieuw ingevuld → materieel

**Grond:** r. 27/K8 houdt het gedeelde DEF-630-beleid terecht open. T-c wordt vervolgens zonder kwalificatie “niet-blokkerend” genoemd. BA-15/BC-16 en B-v2 Q3 verwerpen juist het overnemen van de regelspecifieke ESS-03-vrijstelling. Ook “A/B/C/D: pas ná evaluatie van de ESS-03-ervaring” is strenger dan B/D’s vastgelegde eis: afzonderlijk besluit en INT-03-effectbewijs; zo’n specifieke volgorde is door ons niet als absolute voorwaarde gekozen.

**Gevraagde correctie:** maak “geen nieuwe eigen poort; gedeeld poortbeleid afzonderlijk bepalen” ook voor T-c leidend. Label evaluatie van ESS-03 als aanbeveling/afhankelijkheid van de betreffende onderzoekers of als nieuw coördinatorvoorstel, niet als ongemarkeerde unanieme voorwaarde.

### SB-10 → §2 bewijscontract/citaatcontrole, r. 27 en 32 → relevante B-voorwaarden ontbreken → materieel

**Grond:** B-v2 T-B1/BC-15 verlangt positiegebonden passages, taalfunctie, gemotiveerde kandidaten, bron-/contextbinding, norm-/model-/promptversie, beoordelaar/tijd en menselijke correctie. Synthese noemt slechts een deel. Letterlijke citaatcontrole kan geen impliciet antecedent als expliciet naamwoord afdwingen en bewijst geen semantische juistheid. De ESS-04-helper dedupliceert fragmentteksten, waardoor meerdere die-voorkomens zonder aanvullende positie-informatie samenvallen (BC-10; B-v2 zichtbare reviewroute).

**Gevraagde correctie:** verwijs expliciet naar het volledige B-bewijscontract als leveringsvoorwaarde, met onderscheid tussen letterlijk citaat en interpretatie/ingesloten antecedent. Leg vast of passagehulp unieke fragmenten of afzonderlijke voorkomens toont; per-voorkomenanalyse vergt extra werk. Bind ook de voor het oordeel gebruikte betekenisgrond, zodat een bron-/contextwijziging herkenbaar tot herbeoordeling kan leiden.

### SB-11 → §2 runtimeclaim “altijd”, r. 25 → bereik van bewijs te ruim → materieel

**Grond:** alle normale gemeten INT-03-uitkomsten zijn review_required. De omliggende service geeft bij evaluator-/contractfouten echter error; dit staat in `modular_validation_service.py:1430–1483`, opnieuw gelezen op dezelfde commit. B-v2 Q4 en BC-07 corrigeerden dit al. De huidige error-grens is geen pas in de toekomst te bouwen uitkomst.

**Gevraagde correctie:** schrijf “in de succesvol afgeronde normale evaluator en alle gemeten invoeren review_required; technische fouten worden al afzonderlijk error”. Bewaar apart het aangetoonde lege-teksthiaat en de gewenste not_evaluated-uitkomst. Geen foutinjectie of nieuwe serviceproef nodig voor deze broncorrectie.

### SB-12 → §2 UI/opslag/legacy, r. 25 → B’s bewijsvoorbehoud ten onrechte weggehaald → materieel

**Grond:** B-v2 Q4 en RB-14/16 bevestigen de codeweergave zonder INT-03-reden **in de onderzochte renderer**. B neemt de universele claim “geen reviewbesluit per INT-03 opgeslagen” juist niet over zonder save/reload-proef. D-v1 Q4 houdt dezelfde grens aan. “Door A en B gecontroleerd” mag die sterkere opslagclaim niet dekken. Statische afwezigheid van src-callers sluit externe/dynamische consumenten evenmin universeel uit (BA-10/BC-11).

**Gevraagde correctie:** scheid bevestigde UI-route, niet aangetroffen specifieke registratieactie en nog ontbrekend ketenbewijs. Formuleer opslag niet als universeel onmogelijk. Kwalificeer legacy als niet gebruikt door de onderzochte productieroute, met aangetroffen testgebruik waar bewezen. Behoud de bron-/versieverwijzingen.

### SB-13 → §1 voorbeelden en §7 “vervuild”, r. 19 en 73 → betekenis van de buurregelproef onvoldoende behouden → materieel

**Grond:** B-v2 “Afbakening buurregelbewijs” en RB-05 zeggen dat E03/E04 vooraf al een lemma-fail hebben. Hun INT-03-status/reden/signalen blijven geldig; E03 was letterlijk voorgeschreven. Zij bewijzen geen door herstel veroorzaakte CON-CIRC-regressie. Een generiek JSON-voorbeeld heeft bovendien niet vanzelf het lemma instrument: “bevat het lemma” is een eigenschap van het **term/tekst-paar** in de B-proef, geen universele taalfout van die tekst.

**Gevraagde correctie:** behoud de oorspronkelijke gevallen en IDs als geldige nulmeting; label ze “niet geïsoleerd voor causaliteit van buurregelherstel”. Een lemmavrije ontwerpvariant mag erbij met eigen ID en vooraf bevroren bedoeling. Motiveer het niet overnemen van B’s instrument-voorbeeld als voorbeeldselectie voor buurregelisolatie, niet als diskwalificatie van de INT-03-analyse. Onderscheid vooraf aanwezige en nieuw ontstane buurreacties in de effectmeting.

### SB-14 → §3 exacte skilltekst, r. 42–45 → afgesproken volledige G/T/H-publicatie ontbreekt gedeeltelijk → materieel

**Grond:** B-v2 bevat na RB-12 een volledig publiceerbaar blok voor beide SKILL.md-bestanden. De synthese vervangt dat door een kortere sectie voor alleen de toetsregelskill. Daar ontbreken onder meer niet beoordeeld/error, positie-/grondbinding, één begrensde poging met origineel/diff/hertoets en het onderscheid tussen oordeel- en herstelonzekerheid. A’s verwerking BA-16 zegt het volledige T/H-blok over te nemen.

**Gevraagde correctie:** lever het volledige overeengekomen contract op een werkelijk te publiceren skillvindplaats en laat beide skills dat daadwerkelijk laden; of benoem de inkorting als bewuste niet-overname met consequenties. Alleen een onderzoeksverwijzing is onvoldoende. Laat de twee reference-regels en het echte apppromptpakket dezelfde gekozen norm bevatten; verifieer later ook daadwerkelijke skillantwoorden, niet alleen hashes.

### SB-15 → §4 herstel, r. 49 → goede behoudgrenzen, maar enkele voorwaarden vallen weg → materieel

**Grond:** actor/rol/bezit/reikwijdte, diff, één kandidaat en stoppen bij conflict zijn goed behouden. De opgesomde “integrale hertoets” noemt INT-03 zelf en de gevraagde ARAI-05 echter niet expliciet; technische fout/ontbrekende grond zijn wel diagnose, niet volledig stopcontract. D’s E04-v2 onderstreept behoud van de tijdsrelatie “nadat”: minder ambiguïteit door die relatie weg te laten is betekenisverlies. “Foutpositief signaal (correcte bijzin)” blijft onzuiver: een neutrale hit is nog geen foutpositief oordeel.

**Gevraagde correctie:** maak hertoets van INT-03 plus alle geraakte regels expliciet, waaronder ARAI-05 waar relevant. Voeg tijdsrelaties/voorwaarden en de technische/bronconflictstops toe, of neem B-H-B1/D-H-D1 integraal als contract. Gebruik “ruis/neutrale treffer” voor een correcte bijzin. De generatie- en herstelroute mogen een bevestigd gebrek niet stil wijzigen zonder bevestigde bedoeling.

### SB-16 → §7 veldmatrix en “gedekt”, r. 73 → samenvatting is stelliger dan de matrices → materieel

**Grond:** B Q2 en D Q2 zeggen dat losse synoniem-/homoniemlabels doorgaans geen verwijzende zin zijn; dit is geen categorische vrijstelling voor prozatekst in zo’n veld. Context/bronnen zijn voor de normale leestoets vaak ondersteunend, maar kunnen voor herstel noodzakelijke betekenisgrond leveren. Zelfstandige toepassing op aanvullingen is een voorgestelde veldscope; het is geen reeds bewezen ASTRA- of appcontract. Een opzettelijk fout tegenvoorbeeld kan correct zijn als gelabeld tegenvoorbeeld.

**Gevraagde correctie:** behoud de conditionele veldrollen, onderscheid leestoets/generatie/herstel en markeer de scope als K8-voorstel. Noem kernversie én gekozen normscope/versie als beoordelingsbasis. “Dossieronderdelen behandeld, met open bewijs” is correcter dan een dekkingsclaim die actuele veldfunctionaliteit suggereert. Volledige matrices mogen via verwijzing worden overgenomen, mits niet vervolgens categorisch anders samengevat.

### SB-17 → §6 effectevaluatie, r. 69 → geschikt principe, nog onvoldoende vastgezet voor uitvoering → materieel

**Grond:** oud/nieuw, herhaling, blind beoordelen, goede én slechte gevallen, echte nieuwe controlegevallen en per-gevalverslechtering zijn goed overgenomen (BA-19/20, RB-15). Daardoor **kan** het ontwerp winst én schade zichtbaar maken. Dat lukt niet betrouwbaar zolang C’s fail-of-review-verwachtingen en concurrerende G-varianten beide als equivalent blijven gelden. B Q6 verlangt vooraf bevroren generatiebrief, bedoeling, bronnen, instellingen en normuitkomsten, een onafhankelijke beoordelaar en controle van werkelijke H-wijzigingen; D voegt skillantwoorden en tijds-/voorwaardebehoud toe.

**Gevraagde correctie:** voeg de ontbrekende bevriezings- en acceptatievoorwaarden toe, inclusief model/instellingen/bronset en afbakening instructietekst versus contextactivering. Beoordeel norminhoud onafhankelijk van de aangepaste evaluator; behandel technische fouten apart. Behoud beschermde goede gevallen, tel gemiste fouten, onterechte afkeur, onnodig herstel en betekenisverlies, en scheid vooraf bestaande buurregel-fails. Vermeld wie generatiebrieven, referentieoordelen, skillproef, gebruikersproef en ketenproef voorbereidt. Een minimum van ≥6 nieuwe gevallen is B’s voorstel; C’s tien en D’s twaalf zijn omvangalternatieven, geen bewezen gelijkwaardige steekproef.

### SB-18 → inleiding, §2 en §6: D-uitvoeringsbewijs → tegengesproken door artefacten → materieel

**Grond:** `proefuitkomsten-d-v1.json` heeft exitstatus **1** en alleen stdout in resultaat; de start strandde vóór de appproeven. `proefuitkomsten-d-v2.json` heeft exitstatus **0**, twintig service-uitkomsten en vier promptvarianten, alle verwachtingen uitgekomen. D-v1 noemt v2 expliciet het leidende bewijs. De inleiding verwijst voor D naar v1 en §2 laat het aantal weg (“D rijen”).

**Gevraagde correctie:** citeer D-v2 voor de nulmeting, vul **D 20** in en behoud D-v1 als mislukte start. Benoem de G/H-aanscherping in D-casus/verwachtingen-v2 als versiecorrectie vóór G/H-uitvoering; niet als wijziging van de gemeten serviceverwachtingen. Dit is een bewijscorrectie, geen reden de proef opnieuw uit te voeren.

### SB-19 → §5 beleid en §2 parser, r. 31 en 65 → onbesliste keuzes te gemakkelijk als vastgesteld behandeld → materieel

**Grond:** BA-21/RB-01 behouden Chris’ keuze over de concrete normprecisering. De toevoeging “richting; geen goedkeuring” helpt, maar “bestaand beleid herstellen: K1(a)” naast “nieuw normbesluit” zonder K1/K7 kan alsnog suggereren dat de voorkeursvariant al besloten is. Evenmin is lage precisie van een niet gekozen Nederlandse parser in dit dossier gemeten.

**Gevraagde correctie:** onderscheid bronherkomst/geen-schijnpass als bestaande richting van de nog te besluiten concrete norm, scope, nul-verwijzingstatus en publicatietekst. Label parserkwaliteit als risico/onbewezen en parser als niet aanbevolen ontwerpoptie; geen algemene empirische claim zonder proef. Geen extra parseronderzoek gevraagd: het risico kan gewoon als onzekerheid blijven staan.

### SB-20 → §7 status en bronverwijzingen → verduidelijking zonder nieuwe inhoud → redactioneel

**Grond:** B heeft zijn zelfstandige bijdrage en fase-2-review/verwerking geleverd; synthesecontrole en verwerking blijven expliciet open. De woorden “onderzoek A/B/C afgerond” kunnen ruimer worden gelezen. Ook ontbreekt in de synthese de reeds bekende kanttekening dat A’s opgeslagen signalen genormaliseerd zijn; de exacte strings staan bij B/C/D.

**Gevraagde correctie:** schrijf “eerste bijdragen, wederzijdse reviews en verwerkingen geleverd; synthesecontrole/verwerking nog open”. Label de genormaliseerde A-signalen bij de bewijsverwijzing. Behoud historische IDs; gebruik waar nodig volledige prefixes INT03-A/B/C/D om verwisseling van ASTRA-goed/fout te voorkomen.

## Dekking van mijn eerdere materiële punten

| Eerder B-punt / advies | Staat in synthese of herkenbaar gekozen? | Deze controle |
|---|---|---|
| Q1, BA-01–04/21, BC-01–04/19, RB-01–03/13: norm versus lokale tekst, bronstatus, uitzonderingen/lemma | Kern en Ross-leemte behouden; enkele uitzonderingen en standpunten te absoluut | SB-02/04/06/19 |
| Q2, BA-05, BC-02, B-D6: veldrollen en betekenisgrond | Volledige matrices aangewezen, maar samenvatting verliest voorwaarden | SB-16 |
| Q3/Q4, BA-06–10, BC-05–07/11–13, RB-04–06/14/16: service, prompt, buren, UI en bewijsgrenzen | Veel behouden; error-/opslag-/fixturegrenzen en D-proefidentiteit corrigeren; nieuwe C-omvangmeting bruikbaar | SB-01/11–13/18/20 |
| T, BA-11–15/19, BC-08–10/15–16, RB-09–11: geen hit ≠ pass, status, kandidaten, versie, poort | T-b-zonder-hit ingetrokken; concrete meldingen, geen-hittekst, consensus en poorttekst nog inconsistent | SB-03/04/07–12 |
| G/skills, BA-16, BC-14, RB-07/08/12: exacte normconsistentie, smalle prompt, vraagroute, volledig skillcontract | Smalle voorkeur goed vermeld; G niet gelijkwaardig; volledig contract niet herkenbaar overgenomen | SB-01/05/06/14 |
| H, BA-17, BC-17, B-H-B1: geen betekenisverlies, bevestigde bedoeling, één poging, hertoets | Hoofdgrenzen behouden; concretisering en routeconsistentie nodig | SB-05/13/15 |
| Casussen/effect, BA-18/20, BC-18, RB-15: voorafverwachtingen, echte controlegroep, positief/negatief, winst én regressie | Goed ontwerpprincipe; uitvoerbare bevriezing, acceptatie en versiegrenzen ontbreken deels | SB-08/13/17/18 |
| B-D1–D6/overdracht: open besluiten en geen gezamenlijke afronding | Besluitlijst aanwezig; voorkeuren/consensusetiketten en faseformulering corrigeren | SB-01–04/09/19/20 |

Geen van de open punten vereist nieuwe productiegegevens, live modelcalls of een brede testsuite om de synthese nu te corrigeren. Keuzes mogen bewust afwijken van B, mits de afwijking en gevolgen herkenbaar worden vastgelegd. Het ongewijzigd citeren van drie verschillende voorstellen vervangt zo’n keuze niet.

## Bronnen, bewijsgrenzen en overdracht

Hoofdbronnen: de vier volledig gelezen stukken uit de opdracht; eigen `aanvulling-b-v2.md`, `review-b-op-a-v1.md`, `review-b-op-c-v1.md`, `verwerking-b-v1.md`; gerichte C-v2-passages en C-proefuitkomsten-v2; D-proefuitkomsten-v1/v2 en casusregister-v2 E04. Eerder gelezen primaire taalbronnen en broncode blijven gebonden via de bestaande B-manifesten; geen nieuwe primaire Ross- of webclaim. Het nieuwe `bewijsmanifest-b-v3.json` bindt de gecontroleerde synthese, nieuwe bronnen en alle eigen bestandsversies.

Deze controle is geen volledige onafhankelijke review van D’s gehele proefscript of nieuwe brononderzoekscyclus. Ze controleert D’s relevante aanspraken en uitvoeringsidentiteit voor de synthese. UI/opslag/export, generatiekwaliteit en kwaliteitswinst zijn nog niet uitgevoerd of aangetoond.

**Volgende overdracht:** A verwerkt de materiële punten in synthese-v2 en geeft per SB-punt een vindplaats of gemotiveerde niet-overname. Chris’ open keuzes blijven zichtbaar. Daarna kan dezelfde reviewer de concrete correcties en resterende verschillen gericht controleren. B levert uitsluitend dit controlebestand en manifest-b-v3; bestaande bestanden blijven intact. Geen implementatie, commits, issues, andere sessies of gezamenlijke afronding.

