# Review B op onderzoek A — INT-03 — v1

25 september 2026. Reviewer: onderzoeker B, Codex CLI, GPT-6 Astra, reasoning high. Dit is de inhoudelijke fase-2-review; geen implementatie, normbesluit of gezamenlijke afronding.

## Beoordeelde versie en bewijs

Beoordeeld: `aanvulling-a-v1.md`, `proefverwachtingen-a-v1.json`, `proef-a-v1.py`, `proefuitkomsten-a-v1.json`, `bewijsmanifest-a-v1.json` en de daarin genoemde stdout/stderr. Alle zes bestandshashes uit A's manifest zijn opnieuw gecontroleerd en kloppen. Onderzoeksrapport: SHA-256 `3b3bc4e5689258021e067bcef996b0c9d95b1d55a5efe965919d492f71e6f277`.

Leesbasis: commit `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`. Bronpaden zijn relatief aan de repository; onderzoeksbestanden staan in de naastgelegen onderzoek-a/b/c-mappen. Gerichte broncontroles betreffen de hieronder genoemde evaluator, service, formatter, selectie en UI. B's bestaande nulmeting wordt hergebruikt; geen nieuwe appproef of modelcall uitgevoerd. Voor het normoordeel zijn ASTRA-raw en gelezen taalbronnen gebruikt, geen regex als norm.

A heeft in `review-a-op-b-v1.md` T-b en de concrete het-regex inmiddels ingetrokken. Hieronder blijft de beoordeelde A-v1 herkenbaar; die latere erkenning maakt de v1-tekst niet stilzwijgend correct.

## Bevindingen

### BA-01 → Q1: gedeelde norm versus lokale toevoegingen → bevestigd

**Bron/tegenbewijs:** `gedeeld/astra-INT-03-raw-20260925.txt` verlangt duidelijkheid van verwijzing en demonstreert een toegestane voornaamwoordconstructie. Het lokale JSON voegt zin/zinsdeel, zelfstandig naamwoord en herkenningspatronen toe. DBT §4.3 is niet gelezen en wordt terecht niet als zelfstandig gecontroleerd bewijs gepresenteerd.

**Gevolg/correctie:** behoud de bronlagen. Het schrappen van lokale aanscherpingen is een normvoorstel aan Chris. Dat A dezelfde zin bij een eenzinsdefinitie veelal redundant noemt, bewijst geen gelijkheid voor elk veld of elke aangeboden tekst.

### BA-02 → Q1: “die als betrekkelijk voornaamwoord komt driemaal voor” → tegengesproken

**Bron/tegenbewijs:** het goede ASTRA-voorbeeld bevat twee betrekkelijke die-vormen bij omstandigheden, plus het aanwijzende die in die gebeurtenis. A's eigen verwachtingenbestand onderscheidt dit al beter.

**Gevolg/correctie:** corrigeer de uitleg naar twee betrekkelijke en één aanwijzende vorm. Herhaling van gebeurtenis is de gedemonstreerde reparatie van dit paar, geen verplichte oplossing voor iedere referentiefout.

### BA-03 → Q1/Q5.1/Q5.3: ASTRA-getrouwe versoepeling maar verplichte verwijzing naar één zelfstandig naamwoord → tegengesproken

**Bron/tegenbewijs:** A's voorgestelde toetsvraag, toelichting, instruction_map en skillrij behouden de lokale woordsoortbeperking. [Onze Taal: betrekkelijk voornaamwoord](https://onzetaal.nl/taalloket/betrekkelijk-voornaamwoord) beschrijft ook een hele zin als antecedent en wie/wat met ingesloten antecedent; [voornaamwoord](https://onzetaal.nl/taalloket/voornaamwoord) behandelt onbepaalde vormen. Deze bronnen zijn door B in fase 1 rechtstreeks gelezen.

**Gevolg/correctie:** schrijf “bedoelde referent/betekenis” en bepaal eerst of een woord verwijzend gebruikt is. Werk dit door in zowel G als T en de skills. A's huidige voorstel is daardoor nog niet normgelijk aan zijn eigen Q1.

### BA-04 → Q1/Q5: uitzonderingen en regeloverlap → aangevuld

**Bron/tegenbewijs:** een duidelijke die/dat-bijzin is toegestaan; onmiddellijke nabijheid alleen bewijst geen eenduidigheid. Loos het behoeft geen antecedent ([Taaladvies: onderwerp](https://taaladvies.net/termen-onderwerp/)); een token mag desgewenst als neutrale zoekhulp verschijnen, maar niet als bewezen verwijzing. Bezit is terecht meegenomen. Vooruitverwijzing is geen automatische vrijstelling. “Dit houdt in”/“dit betekent” kan zowel toelichtend als onduidelijk verwijzend zijn: INT-06 sluit INT-03 niet uit.

**Gevolg/correctie:** vervang automatische uitzonderingen door functie- en zinsbeoordeling. Houd lemma plus kern versus kern alleen als expliciete scopekeuze. Bij “deze definitie” is grammaticale duidelijkheid contextafhankelijk, geen algemene vrijstelling voor dat patroon.

### BA-05 → Q2: veldmatrix en noodzakelijke invoer → aangevuld

**Bron/tegenbewijs:** A scheidt kern, metadata en aanvullingen, maar de matrix onderscheidt niet overal generatie-invoer, AI-wijzigbaarheid en herkomst/conflict. B-v1 Q2 en C-v1 Q2 doen dat explicieter. ASTRA “alle” bepaalt niet vanzelf dat alle recordvelden één toetsobject zijn.

**Gevolg/correctie:** completeer de matrix per veld, inclusief praktijkvoorbeelden, tegenvoorbeelden, grensgevallen, synoniemen en homoniemen. Kerntekst volstaat voor veel leestoetsen; herstel kan bevestigde betekenisgrond nodig hebben. Een opzettelijk fout tegenvoorbeeld is geen fout in de definitiekern.

### BA-06 → Q3: INT-01-wrijving nog niet geverifieerd → aangevuld

**Bron/tegenbewijs:** B's `proefuitkomsten-b-v1.json`, E01/E02/E03 op manager/cache, bewaart daadwerkelijke INT-01-fails. De INT-01-patronen en C's verwijzingen ondersteunen de oorzaak. A's terughoudendheid was voor zijn eigen v1 correct.

**Gevolg/correctie:** in de synthese mag deze wrijving als actueel servicebewijs staan, met B's proefidentiteit. Het bewijst een implementatiereactie, geen normatieve onverenigbaarheid. Goede bijzinnen niet herschrijven om een onjuiste buurregel te ontwijken.

### BA-07 → Q4/proef: alle twintig service-uitkomsten review met toetsvraag → bevestigd

**Bron/tegenbewijs:** tien invoeren × twee routes in A's uitkomsten, bootstrap vóór applicatie-imports, geïsoleerde runtime en geen modelcalls. Alle gemeten INT-03-statussen zijn review_required; redenen bevatten de toetsvraag. De scriptvergelijking controleert status/signalen, terwijl de opgeslagen redenen aanvullend leesbaar zijn. B's zestien en C's dertig service-uitkomsten bevestigen het mechanisme op dezelfde commit.

**Gevolg/correctie:** bruikbare contractnulmeting. Niet presenteren als twintig inhoudelijk correcte normoordelen. Technische fouten en ontbrekende invoer vragen eigen bewijs; de normale proefrijen dekken die routes niet.

### BA-08 → Q4/proef: “signalen zijn patroonstrings” en reproduceerbaarheid → aangevuld

**Bron/tegenbewijs:** de app levert ruwe strings, maar A's `norm_sig` vervangt de extra regex met negatieve lookahead door een verkorte representatie. Het uitkomstenbestand is op dat punt geen letterlijke appuitvoer. A's manifest noemt exitstatus 0; het commandoveld bevat placeholders/afgekorte commit, het script neemt de commit uit argv over.

**Gevolg/correctie:** label de signalen als genormaliseerd en verwijs voor de exacte string naar JSON/code of B/C. Neem in een volgende bewijsversie het volledige werkelijk gebruikte commando op. Deze administratie beperkt de zelfstandige reproduceerbaarheid, maar ontkracht de overeenstemmende statuswaarnemingen niet. Geen herhaling nodig om alleen een commando uit te schrijven.

### BA-09 → Q4/proef: promptblok en contextselectie → bevestigd

**Bron/tegenbewijs:** A rendert formatter/moduletekst en controleert de selectiemethode; A vermeldt terecht dat dit geen volledige adapterdoorloop is. `json_based_rules_module.py` rendert uitleg, instruction_map en voorbeelden, niet toelichting/toetsvraag. B's adapterproef bevestigt geen/organisatorisch/juridisch; C bevestigt bovendien wettelijk en voorbeelden uit.

**Gevolg/correctie:** bind claims aan de juiste route. De gezamenlijke bronbasis ondersteunt afwezigheid van het gelabelde INT-03-blok zonder juridische/wettelijke context in deze varianten. “In de meeste generaties afwezig” is zonder gebruiksverdeling niet gemeten. Promptaanwezigheid bewijst geen modelnaleving of effect.

### BA-10 → Q4: legacy en vervolgketen → aangevuld

**Bron/tegenbewijs:** adapter registreert JSONBasedRulesModule; de hardcoded IntegrityRulesModule en beide identieke legacyvalidators zijn geen bewijs voor de actuele beoordeelde route. Een gerichte statische callerzoekactie sluit onbekende externe/dynamische consumenten niet universeel uit. UI/opslag/import/export zijn in A's proef niet uitgevoerd.

**Gevolg/correctie:** behoud die grenzen. Opruimen blijft afzonderlijke implementatiekeuze. Voeg de statisch gecontroleerde INT-03-weergavebeperking toe (BA-14) zonder een volledige opslag-/exportclaim te maken.

### BA-11 → Q5.2 T-b: geen uitgebreide patroonhit kan n.v.t./pass opleveren → tegengesproken

**Bron/tegenbewijs:** de voorgestelde lijst bevat bijvoorbeeld hem niet. De synthetische zin “instructie van een begeleider aan een deelnemer om hem te registreren” illustreert het semantische risico zonder beroep op een ontbrekende het-hit: begeleider en deelnemer zijn te onderzoeken referenten, hem staat in geen voorgestelde patroonvariant. Dit is een gerichte vergelijking van tekst en patroonbron, geen uitgevoerde serviceproef. Volledige afwezigheid van een verwijzende functie volgt niet uit afwezigheid van zo'n woordhit.

**Gevolg/correctie:** trek T-b in deze vorm in; een disclaimer “geen betekeniscontrole” rechtvaardigt geen pass. Alleen na daadwerkelijke inhoudelijke controle kan een oordeel over afwezigheid van verwijzingen volgen. A heeft deze correctie inmiddels toegezegd in RB-09; verwerk haar in A's eigen volgende versie.

### BA-12 → Q5.1: extra patroon verwijderen óf negatieve lookahead in record invoegen → tegengesproken

**Bron/tegenbewijs:** huidige losse deze/dit/die/daarvan-patronen blijven signaleren waar het extra patroon uitsluit. Een recorduitsluiting voor “deze regel/definitie/begrip” invoeren verandert de dekking; dubbeling verwijderen met behoud van losse patronen doet dat niet. De twee opties zijn functioneel niet gelijk. A's het-lookahead is niet beproefd en mist verwijzende constructies buiten de opsomming.

**Gevolg/correctie:** scheid consolidatie van nieuwe uitzonderingen en patroonuitbreiding. Voor elk: vooraf dekking én ruis toetsen; nooit semantische afkeur/goedkeuring. A's intrekking van de concrete het-regex in RB-10 is passend.

### BA-13 → Q5.2: kandidaatmeldingen, onzekerheid en foutuitkomsten → aangevuld

**Bron/tegenbewijs:** T-a kan met de bestaande passagehelper trefwoorden tonen, maar geen betrouwbaar bepaalde kandidaten. A's gecombineerde melding voor T-a/T-c suggereert dat wel. `ReviewRequirement` bevat alleen rule_id/category/reason/signals. B's T-B1 onderscheidt aangetoonde ambiguïteit, onbekende bedoeling voor herstel, onvoldoende beoordeling, ontbrekend toetsobject en technische fout.

**Gevolg/correctie:** markeer kandidaten als menselijke vaststelling of als te beoordelen modelvoorstel. Aantoonbare dubbelzinnigheid mag fail zijn terwijl herstelbedoeling nog ontbreekt; een informatievraag is geen reden om die vastgestelde fout weg te laten. Niet elke open beoordeling is ontbrekend bewijs. De service heeft al een error-grens, zodat dit geen volledig nieuw mechanisme is.

### BA-14 → Q5 T-a: betere reden levert zichtbare reviewhulp → onvoldoende bewezen

**Bron/tegenbewijs:** gerichte controle `src/ui/components/validation_view.py:803–808` toont redenen alleen voor ESS-01/02/04. De detailroute voor review_required toont de regelcode en gaat verder zonder uitleg-expander (r. 859 e.v.).

**Gevolg/correctie:** expliciete UI-presentatie hoort bij T-a, naast resultaatvorming. Laat reden, letterlijke passage en open oordeel zien; voeg vastlegging/binding via DEF-624/626/627 toe. Alleen de evaluator aanpassen levert in deze route nog geen zichtbare hulp. Geen UI-run of opslagdoorloop gedaan.

### BA-15 → Q5.2: scoreloos en geen aparte vaststelblokkade → beleidskeuze

**Bron/tegenbewijs:** geen totaalscore volgt het appbesluit van 15 september; scoreloze judgment_review is actueel. Een ESS-03- of andere regelspecifieke poortvrijstelling is geen INT-03-besluit. DEF-630 betreft gedeeld vaststel-/exportbeleid; B-v1 Q3 onderscheidt dit.

**Gevolg/correctie:** geen nieuwe losse INT-03-poort voorstellen is verdedigbaar. Formuleer niet dat een negatief of open INT-03-oordeel onder alle toekomstige gedeelde poorten zeker niet blokkeert. Laat Chris dit binnen het gezamenlijke contract kiezen.

### BA-16 → Q5.3 G/skills en overeenstemming G↔T → aangevuld

**Bron/tegenbewijs:** de huidige skillbullet luidt al “... zonder duidelijk antecedent”; zij verbiedt die/dat dus niet letterlijk. Een mogelijke modelinterpretatie als vermijdadvies is een hypothese. Nieuwe A-teksten zijn positiever, maar bevatten nog de te smalle naamwoordeis (BA-03) en automatische nabijheidsvrijstelling (BA-04). Het schrappen van JSON-toelichting bereikt de live prompt niet.

**Gevolg/correctie:** lever één gedeelde norm in instruction_map, uitleg/voorbeelden en beide skillreferences, met volledige T/H-instructie op een werkelijk meegeleverde skillvindplaats. Toets het echte samengestelde promptblok. Er is geen gemeten bewijs dat de huidige skilltekst het model werkelijk verwarde.

### BA-17 → Q5.4 H: betekenis behouden en oorzaak benoemen → aangevuld

**Bron/tegenbewijs:** één bevestigde referent, geen actor gokken, niet repareren wegens een neutraal signaal en hertoetsen zijn juist. E04 zonder signalen is een detectorhiaat, geen ontbrekende betekenisgrond op zichzelf. Een treffer op een goede bijzin is pas een foutpositief oordeel als de hulp het als fout presenteert; huidige hits zijn neutraal.

**Gevolg/correctie:** voeg herformulering naast naamwoordherhaling expliciet toe. Stop bij betekenis- of regelconflict en toon dat conflict; maak “nooit lemma invoegen” niet tot een manier om een betwiste buurnorm stil te laten winnen. Scheid bewijstekort, detectietekort en verkeerde beoordeling.

### BA-18 → casustabel en vooraf opgeslagen verwachtingen → aangevuld

**Bron/tegenbewijs:** de tien uitgevoerde gevallen zijn vooraf als runtime-/normverwachtingen opgeslagen; E11–E13 zijn terecht ontwerp/niet uitgevoerd. De G/T/H-kolommen in het eindrapport zijn geen zelfstandig bewijs dat iedere formulering vóór uitvoering was bevroren. De nieuwe registergevallen hebben stabiele A-IDs; historische IDs blijven apart herkenbaar te houden.

**Gevolg/correctie:** onderscheid vooraf bevroren runtimeverwachting, inhoudelijke interpretatie en toekomstige variantverwachting. Geen claim van uitgevoerde G/H. Beoordeel bij ASTRA-fout niet alle aanwezige naamwoorden alsof ze grammaticaal en semantisch gelijkwaardige kandidaten zijn.

### BA-19 → Q6: kwaliteitswinst T-a → tegengesproken

**Bron/tegenbewijs:** Q6 noemt “geen open oordeel bij definities zonder voornaamwoord” als winst; aanbevolen T-a blijft volgens Q5.2 altijd review_required. Ook kandidaat-antecedenten ontstaan niet automatisch door passagehulp.

**Gevolg/correctie:** meet bij T-a de kwaliteit/tijd/onderbouwing van het menselijke oordeel, niet een automatische statuswijziging die deze variant niet levert. Een pass volgt hoogstens na een afzonderlijk vastgelegd inhoudelijk oordeel. Maak effectcriteria variantgebonden.

### BA-20 → Q6: kan de effectevaluatie winst én verslechtering vaststellen? → aangevuld

**Bron/tegenbewijs:** gepaarde oude/nieuwe instructies, herhaalde modelruns, blinde beoordeling en behoudcriteria zijn goed. De voorgestelde gebruikersproef gebruikt uitsluitend E02/E04/E07/E08: foutgerichte gevallen. Daarmee wordt onterechte afkeur of hinder bij goede/noisige constructies onvoldoende zichtbaar. Buurregelsignalen mogen niet de enige semantische behoudmaat zijn.

**Gevolg/correctie:** voeg goede relatieve zinnen, loos het, geen voornaamwoorden en neutrale ruis toe; rapporteer juist/onjuist/open/fout, betekenisverlies, tijd en onnodig herstel afzonderlijk. Reserveer echt nieuwe, voor ontwerp afgeschermde gevallen; reeds besproken B/C-gevallen zijn na deze review geen ongeziene controlegroep. Leg generatiebrief, model/instellingen, bronbedoeling en uitvoereigenaar vooraf vast. De nulmeting bewijst nog geen winst.

### BA-21 → Q6: “K1/K4/K6 herstellen bestaand beleid” en dossierdekking → beleidskeuze

**Bron/tegenbewijs:** Q1–Q6, historie, appketen, skills, G/T/H, proeven en besluitpunten zijn inhoudelijk behandeld. Maar een lokale normversmalling vervangen, nieuwe uitzonderingen invoeren of een voorgestelde skilltekst als norm publiceren vergt een herkenbaar besluit; ASTRA-getrouwheid als doel is geen goedkeuring van elke concrete tekst.

**Gevolg/correctie:** overdraagbaar als eerste onderzoek, met materiële correcties BA-02/03/11/12/19 en de genoemde bewijsgrenzen. Chris kiest normscope, nul-voornaamwoordstatus, contextvrij bereik, AI versus mens en herstel-/poortbeleid. A verwerkt zijn eigen correcties; B wijzigt A's bestanden niet.

## Overdracht

Deze review kan naar A voor eigen verwerking en vervolgens synthese. Belangrijkste open verschillen zijn de referentscope, status bij onbekende herstelbedoeling, promptbereik en gedeeld poortbeleid. De bestaande offline bewijzen blijven bruikbaar binnen hun bereik. Geen nieuwe proef nodig voor de gevonden tegenstrijdigheden: gerichte code-/tekstcontrole levert het benodigde tegenbewijs. Fase-2-bronnen en eigen bestanden worden gebonden in `bewijsmanifest-b-v2.json`.

