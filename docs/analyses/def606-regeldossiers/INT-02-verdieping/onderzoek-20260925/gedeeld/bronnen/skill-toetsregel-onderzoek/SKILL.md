---
name: toetsregel-onderzoek
description: "Onderzoek en verbeter één definitiekwaliteitsregel: normbetekenis, appketen, skills/prompts en acceptatie, met onafhankelijke onderzoeken in twee afzonderlijke sessies, wederzijdse review en een gecontroleerde synthese. Gebruik voor een regeldossier of verdieping daarvan; niet voor het toetsen van één definitie, algemene webresearch of implementatie."
lastReviewed: null
evalScore: null
status: active
---

# Onderzoek van één toetsregel

Lever een besluitrijp voorstel gericht op aantoonbaar betere definities en beoordelingen, inclusief gevolgen voor applicatie, instructies en acceptatie. Leg per verbeteraanbeveling de beoogde kwaliteitswinst en de vergelijking met de bestaande situatie vast. Onderzoek en review zijn geen normbesluit of implementatieopdracht. Deze skill bevat een methode, geen vooraf goedgekeurde CON-01-uitkomsten.

## Modelkeuze in Codex

Voor inhoudelijk definitieregelonderzoek, norminterpretatie, verbetervoorstellen, grensgevallen, inhoudelijke kruisreview en synthesecontrole geldt standaard **GPT-6 Astra met reasoning effort `high`**. De algemene Codex-standaard staat eveneens op Astra high; besparing komt uit gerichter werken en hergebruik van geldig bewijs. Een expliciete gebruikerskeuze voor een andere onderzoekspartner of een ander model blijft leidend; wijzig die partner niet stilzwijgend.

- Controleer vóór inhoudelijke conclusies het werkelijk actieve model en denkniveau via beschikbare sessiemetadata. Een configuratiebestand of zelfbeschrijving van het model bewijst de actieve keuze niet. Is de instelling afwijkend of niet verifieerbaar, laat de modelkeuze eerst vaststellen; doe ondertussen alleen onafhankelijk ondersteunend werk. Presenteer een Sol-onderzoek niet als een Astra-onderzoek.
- CLI: de algemene standaard is Astra high; een apart profiel is niet nodig. Het bestaande profiel `definitieonderzoek` is optioneel. Controleer beschikbare opstartmetadata, omdat projectinstellingen en expliciete overrides de standaard kunnen overstemmen. Start geen extra modelproef wanneer geldige sessiemetadata al beschikbaar is. Waar een override nodig is: `codex -m gpt-6-astra -c model_reasoning_effort=high`.
- App: kies Astra en High in de modelinstelling van de onderzoekstaak. De algemene standaard, een CLI-profiel en deze skill schakelen een bestaande app-taak niet automatisch om. Als geen ondersteunde modelwissel beschikbaar is, meld de benodigde keuze eenmalig en wacht met het inhoudelijke onderzoek tot die is bevestigd.
- Vermeld Astra/high expliciet in een reeds geautoriseerde Codex-onderzoeks- of reviewopdracht voor de andere sessie; controleer diens werkelijke instelling. Dit verleent geen toestemming voor extra sessies of berichten.
- Afgebakende administratie, broninventarisatie en statuscontroles mogen op Sol medium. Laat inhoudelijke conclusies en de noodzakelijke oorspronkelijke bronpassages aan de Astra-onderzoeker; een Sol-samenvatting vervangt geen normbron. De bestaande onafhankelijke onderzoeken, kruisreview en acceptatie-eisen blijven behouden.

## Afbakening en hervatten

Leid actieve regel, project, gewenste diepte en opdrachtgrenzen af uit de vraag en beschikbare dossiers. Vraag alleen naar ontbrekende informatie die het werk daadwerkelijk bepaalt. Bij een vervolg: lees de aangewezen versies, bepaal de laatst afgeronde fase en werk alleen open punten bij. Een verzoek om één bevinding toe te lichten start geen nieuwe volledige review.

Bij een volledig onderzoek werken **onderzoeker A (coördinator) en onderzoeker B in een afzonderlijke sessie** samen: twee onafhankelijke eerste onderzoeken, wederzijdse review, verwerking door beiden en een door onderzoeker B gecontroleerde synthese. De rollen zijn niet aan een model of aanbieder gebonden. Onafhankelijkheid vereist gescheiden contexten vóór de eerste conclusies; een ander model is op zichzelf geen bewijs daarvan. Volg een expliciete gebruikerskeuze voor model, platform of samenwerkingspartner. Dit is onderdeel van de volledige oplevering. Alleen een expliciet enkelvoudige of beknopte gebruikersopdracht wijzigt deze omvang. Een ontbrekende sessie verandert de opdracht niet in een enkelvoudig onderzoek. Vervang een aangewezen onderzoekssessie niet stil door een andere uitvoerder, een kort modeladvies of een oude dossierreview.

Lees [het werkcontract](references/werkcontract.md), met name de startprocedure en faseovergangen. Onderzoeker A coördineert de uitwisseling en houdt de eerstvolgende actie bij; onderzoeker B levert een eigen onderzoek, kruisreview, reviewverwerking en synthesecontrole. Werk binnen de bestaande autorisatie en vraag niet opnieuw om reeds gegeven toestemming. Deze skill op zichzelf verleent geen toestemming voor nieuwe externe sessies of berichten.

Gebruik bij een nieuwe opdracht de [herbruikbare startopdrachten voor beide onderzoekers](references/startopdracht.md). Stel bij aanvang vast welke afzonderlijke onderzoekssessie en toegang beschikbaar zijn. Bereid bij een ontbrekende samenwerking de concrete opdracht voor onderzoeker B en gedeelde feitenbasis voor; leg daarna vroeg de ene nog benodigde actie of toestemming aan de gebruiker voor. Werk ondertussen zelfstandig uitvoerbare onderdelen uit. Alleen vermelden dat de tweede onderzoekssessie ontbreekt is geen uitgevoerde overdracht. Bewaar een tussenstand zolang een verplichte bijdrage ontbreekt.

Lees bij elk regeldossier ook [één norm, twee toepassingen](references/genereren-en-toetsen.md). Werk de gedeelde norm uit als generatie-instructie (G), toetsinstructie (T) en begrensde terugkoppeling (H), met veldrollen en gekoppelde acceptatiegevallen. Gebruik dit binnen Q1–Q6; bij bestaande dossiers alleen de ontbrekende uitsplitsing verdiepen. Beide onderzoekers en hun reviews behandelen deze toepassingen expliciet.

## 1. Maak een gedeelde feitenbasis vóór de onafhankelijke conclusies

- Leg regel-ID, relevante codecommit/configversie, bronversies, actuele besluiten en beschikbare historische proeven vast. Laat de gebruikerswerkboom intact; onderzoek een passende leesbasis.
- Controleer naast regellokale besluiten de **rechtstreeks relevante bovenliggende besluiten** over context/identiteit, validatiestatus, score, opslag, vaststelling en export. Volg concrete parent-/relatieverwijzingen, geen inventarisatie van alle issues. Leg datum, status en toepassingsbereik vast: ouder lokaal beleid kan door later overkoepelend beleid zijn aangevuld.
- Maak per onderzoeksvraag onderscheid tussen al bewezen, te actualiseren, ontbrekend feit en open beleidskeuze. De bronbasis is gedeeld; nieuwe interpretaties en antwoorden worden nog niet uitgewisseld.
- Hergebruik een proef wanneer bron/config en de precieze claim nog overeenkomen. Nieuwe uitvoering alleen voor gewijzigde code, ondeugdelijk bewijs of een concreet open grenspunt. Noteer bij een bekend defect de bestaande eigenaar en wat de nieuwe proef toevoegt.
- Onbereikbare bron: benoem de afhankelijke claim en consequentie; werk onafhankelijke onderdelen verder uit. Een toegankelijk abstract of secundaire samenvatting vervangt geen gelezen normpassage.

## 2. Beantwoord dezelfde vragen zelfstandig

| ID | Te beantwoorden vraag |
|---|---|
| Q1 | Wat waarborgt de oorspronkelijke norm, wat is lokale aanvulling, wanneer geldt de regel en welke uitzonderingen zijn onderbouwd of open? |
| Q2 | Welke invoer en onderbouwing zijn noodzakelijk of ondersteunend, en wat betekent ontbrekende of tegenstrijdige informatie? |
| Q3 | Welke concrete relaties bestaan met andere regels, wat is een conflict of slechts overlap, en wie beslist over welk normdoel? |
| Q4 | Welk gedrag is daadwerkelijk bewezen per relevante appingang en waar ontbreken transport-, beoordelings-, opslag-, UI- of poortbewijzen? |
| Q5 | Welke exacte regeltekst, appmeldingen/contracten en skill-/promptvervangingen worden aanbevolen, met alternatieven en gevolgen? |
| Q6 | Welke kwaliteitswinst wordt beoogd, welke vergelijking vóór/na kan die aantonen of weerleggen, welke risico's/bewijsgaten blijven en welke besluiten worden aan de gebruiker voorgelegd? |

Scheid bronfeit, vastgelegd besluit, waarneming, interpretatie en voorstel. Een voorstel van twee onderzoekers blijft een voorstel. Gebruik geen huidige regex als uitgangspunt voor de norm en geen vereiste menselijke betekenisbeoordeling als impliciet deterministische controle.

Lees primaire bronnen voor open normvragen, citeer exacte passages/secties en begrens toegang. Lees relevante skill-/promptpassages als te onderzoeken implementatie, niet als zelfstandig normbewijs. Onderzoek buurregels alleen voor een concrete relatie; neem hun besluiten niet over.

## 3. Kies onderscheidend bewijs

Bouw één casusregister met stabiele IDs. Een ID behoudt zijn scenario; wijziging van scenario krijgt een nieuw ID, gewijzigde verwachting een expliciete versie/reden. Leg verwachte uitkomsten en regelspecifieke verbetercriteria vóór uitvoering vast; bij onbeslist beleid staan de opties naast elkaar. Werk de vergelijking vóór/na en de beoordeling van echte uitkomsten uit volgens [effectevaluatie](references/genereren-en-toetsen.md#effectevaluatie-van-de-verbeterslag). Synthetische proeven zijn geen gevalideerde juridische praktijkgevallen.

Kies gewone toepassingen én tegenvoorbeelden die een voorgestelde automatisering kunnen weerleggen: bedoelde functie versus dezelfde woorden, noodzakelijke naam versus losse context, wel/niet geselecteerde waarde, ontbrekende versus onjuiste invoer en wijzigen na beoordeling. Pas deze categorieën toe voor zover relevant voor de actieve regel; kopieer niet automatisch de CON-01-casuslijst.

Volg per relevante ingang invoer → transport → oordeel → opslag → weergave → vervolghandeling. Houd regelstatus, score, dekking, review en blokkade afzonderlijk. Test minimaal één concrete open grens wanneer de feitelijke claim dat nodig heeft; markeer niet uitgevoerde delen. Een serviceproef is geen UI-test; losse proeven zijn geen volledige keten. Een ingestelde score of rolstring is geen actuele validatiesnapshot of bewezen bevoegdheid.

Proeven zijn klein, offline waar mogelijk, met synthetische data en verse opslag. Bewaar uitvoercommando, runtime/stubs, commit/config, invoer, verwachting/grond, werkelijke uitkomst en exitstatus. Geen productiegegevens, live modelcalls of brede testsuite zonder concrete onderzoeksnoodzaak en passende autorisatie. Benoem relevante uitvoeringsvolgorde, bijvoorbeeld wanneer een hardere poort bestaande foutpositieven ernstiger maakt.

## 4. Bewaar eerst, review daarna

Iedere onderzoeker bewaart een complete eigen eerste beantwoording van Q1–Q6 vóór het lezen van nieuwe conclusies van de ander. Compleet betekent ook verantwoord ontbrekend bewijs, niet dat elke approute is getest. Bewaar de exacte uitgewisselde versie; inhoudshash waar nodig voor overdrachtszekerheid.

Review het volledige onderzoek en de claimrelevante bijlagen. Beoordeel norm/besluitstatus, informatie, relaties, proefclaims, verwachtingen, concrete regel/app/skillvoorstellen en of de effectevaluatie kwaliteitswinst én verslechtering kan vaststellen. Gebruik reviewpunt → beoordeelde claim/versie → oordeel → bron/tegenbewijs → gevolg/correctie. Scores voor modelkwaliteit of overeenstemming vervangen dit niet.

Iedere onderzoeker verwerkt elk ontvangen punt als overgenomen, gedeeltelijk overgenomen, afgewezen met grond of open. Behoud oorspronkelijke eerste versies en corrigeer in een herzien advies; genereer niet telkens het hele bronpakket opnieuw. Een materiële feitelijke tegenspraak vraagt gerichte broncontrole of proef. Een normkeuze blijft een expliciete keuze, geen eindeloze zoektocht naar consensus.

## 5. Maak een korte synthese en rond aantoonbaar af

Schrijf één **geïntegreerde besluitnotitie**, bij voorkeur enkele pagina's: aanbevolen normtekst en voorbeelden; gevolgen voor app en instructies; belangrijkste bewijs; concrete keuzes met beide standpunten, gevolgen en onderscheidende casussen. Verwijs naar de volledige casus- en bewijsregisters. Plak geen twee casusmatrices achter elkaar en vul geen hoofdstukken met herhaalde conclusies.

Koppel belangrijke aanbevelingen aan bron/proef/review en controleer Q1–Q6 en toepasselijke dossieronderdelen via een compacte dekkingstabel. Benoem per open punt of nieuw bewijs nodig is of de gebruiker een keuze moet maken. Lever vervangende skill-/prompttekst met huidige vindplaats; ook positieve, negatieve en grensvoorbeelden van de regel zijn concrete voorstellen, geen ontbrekende placeholders.

Controleer bij een gewijzigde conclusie ook de bijbehorende casusrijen, gevolgkolommen, voorbeelden en samenvatting. Een voorbehoud boven een tabel repareert geen te stellige rij. Bij versmalling van een beslisregel: controleer welke invoer buiten de nieuwe voorwaarden valt en leg het vervolg daarvoor vast.

Laat bij het volledige onderzoek onderzoeker B de synthese controleren op weglatingen, standpuntweergave en betekenisverlies. Verwerk die controle zichtbaar. Daarna alleen gerichte herbeoordeling bij een materiële wijziging of onopgeloste feitelijke tegenspraak; redactie of een open beleidskeuze vraagt geen nieuwe algemene ronde.

Noem het onderzoek gezamenlijk afgerond pas wanneer beide bijdragen, beide reviews, beide verwerkingen, de afgesproken synthesecontrole en een uitvoerbare effectevaluatie of gerichte overdracht daarvoor aanwezig zijn. Controleer relevante bronbinding, bijlagelinks en bewijslogs; een geslaagde structuurcontrole bewijst geen inhoudelijke juistheid. Onderscheid onderzoeksafronding, technische oplevering en aangetoonde kwaliteitswinst. Zonder passend effectbewijs blijft een geïmplementeerde verbeterslag: **geïmplementeerd; kwaliteitswinst nog niet vastgesteld**, met eigenaar, concrete vervolgactie en uitvoeringsmoment of afhankelijkheid. Lever een hervatbare tussenstand als een verplichte onderzoeksbijdrage ontbreekt.

Eindig met de besluiten die de gebruiker nu kan nemen en de resterende beperkingen. Maak duidelijk welke vervolgstappen bestaand beleid herstellen en welke een nieuw normbesluit vereisen. Maak geen issues, wijzig geen app/regels/skills en ga niet naar de volgende regel tenzij die uitvoering afzonderlijk is opgedragen.
