# ESS-04 — zelfstandige Cowork-opdracht

18 september 2026. Gereed voor overdracht; nog niet verstuurd. Er is geen ESS-04-sessie aangewezen en geen toestemming uit CON-01 overgenomen.

Onderzoek ESS-04 — Toetsbaarheid in DefinitieAgent als afzonderlijke Claude Cowork-onderzoeker. Codex coördineert in deze ESS-04-taak. Lees de vier bestanden in `feitenbasis/toetsregel-onderzoek/`: SKILL.md en references/werkcontract.md, startopdracht.md en genereren-en-toetsen.md. Pas ze inhoudelijk toe. Dit is onderzoek en documentatie, geen implementatie.

## Toegang en overdracht

- Project/bronmap op de Mac: `/Users/chrislehnen/.codex/worktrees/6ff5/Definitie-app`.
- Onderzoeksmap op de Mac: `/Users/chrislehnen/.codex/worktrees/6ff5/Definitie-app/docs/analyses/def606-regeldossiers/ESS-04-verdieping/onderzoek-20260918/`.
- Historische oorspronkelijke projectmap: `/Users/chrislehnen/Projecten/Definitie-app`; lees uitsluitend de hieronder genoemde bronkopieën als die map niet gedeeld is.
- Cowork-projectpad en Cowork-werkpad: nog niet gemount of aangetoond. Dit zijn bewust geen verzonnen `/mnt/`-paden. Eerste handeling na geautoriseerde start: bepaal de werkelijk gedeelde map en rapporteer de Mac→Cowork-padmapping.
- Route: na toestemming via de afzonderlijke ESS-04-sessie in Claude/Cowork; Codex draagt dit bestand plus `feitenbasis/` en `bronnen/` over. Nieuwe Codex-onderzoeksconclusies worden niet meegestuurd in de eerste fase.
- Bewijs van ontvangst: lees ESS-04-v1.md, het regelrecord in de projectmap, de vier skillbestanden en het ESS-02-besluit; rapporteer hun feitelijke paden, hashes en een korte inhoudsidentificatie. Een getoond pad of ZIP-bestand geldt niet als toegangsbewijs. Meld exact wat ontbreekt.
- Fase: zelfstandige eerste onderzoeken; eerstvolgende bijdrage `cowork-onderzoek-v1.md`, met Q1–Q6, G/T/H, veldrollen, concrete teksten en acceptatiegevallen.

## Gemeenschappelijke feitenbasis (zonder nieuwe Codex-conclusies)

Codebasis is `50d0770ded6f4e8337738126d6bc2aa8f169e3de` (21 augustus 2026) in deze werkmap. Noem dit uitdrukkelijk geen actuele main. Historische dossiers gebruiken `d68a98a909630e15db6e1cb9c9c8171f957bff9d` (11 september). Actuele Linear-registraties kunnen latere levering beschrijven; houd versies gescheiden.

Lees in `feitenbasis/historisch/`:

- docs/analyses/def606-regeldossiers/ESS-04-v1.md en ESS-04-bewijs-v1/{gevallen.json,uitkomsten.json,claude-review.json}; historische Claude-review mag worden gelezen, maar vervangt jouw zelfstandige bijdrage niet.
- docs/analyses/def606-regeldossiers/overzicht-v1.md en samenhang-v1.md.
- docs/plans/2026-09-11-def606-analyseplan-v4.md.
- docs/analyses/2026-09-11-DEF-606-productbedoeling-toetsregels-skills-v1.md.
- docs/analyses/2026-09-15-DEF-606-besluit-geen-totaalscore-v1.md.
- docs/analyses/2026-09-17-DEF-606-centraal-regelregister-v1.md.

`feitenbasis/bestanden-v1.json` bindt originele paden aan kopieën en hashes. `feitenbasis/actieve-skills/` bevat de gelezen definitie-, toetsregel-, ontologie-, modelleer- en voorbeeldenskills plus referenties. Ze zijn onderzoeksmateriaal, geen normbron.

Lees de op 18 september opgehaalde volledige Linear-JSONs in `bronnen/`: DEF-767 en DEF-606 (inclusief comments), DEF-622 (CON-01), DEF-743 (CON-02), DEF-745 (ESS-01), DEF-749 en DEF-750–754 (ESS-02), het document besluiten-ESS02 en comments-DEF-749, DEF-624, DEF-630 en DEF-638. Centraal issue blijft https://linear.app/definitie-app/issue/DEF-767 . Geen nieuw issue aanmaken.

Vastgelegde grenzen: appbreed geen totaalscore als kwaliteitsoordeel, acceptatiegrond of hersteldriver (15 september). CON-01 en ESS-01 zijn als Done geregistreerd; heropen hun besluiten niet. ESS-02: niveau en aard apart; menselijke inhoudelijke beoordeling; geen cijfer; geen zelfstandige ESS-02-vaststelblokkade; bewuste categoriebevestiging bindt actor/tijd/versie en bevestigt niet automatisch de kern. CON-02 heeft eigen goedgekeurde AI-beoordeling en bronuitzonderingen; kopieer dit beleid niet automatisch naar ESS-04. Algemene expertbeoordeling en handmatige vaststelling blijven gelden; een verplichte tweede persoon is daarmee niet besloten. DEF-638 plant maximaal één herstelpoging, maar activeert geen herstel in dit onderzoek.

## Zelfstandig te beantwoorden Q1–Q6

1. Q1: oorspronkelijke norm, lokale aanvulling, toepasselijkheid en onderbouwde/open uitzonderingen. Lees primaire bronnen voor open vragen; https://www.astraonline.nl/index.php/Toetsbaarheid is de aangewezen regelbron. Beperk claims als die niet leesbaar is; ISO-abstracts vervangen geen normpassage.
2. Q2: noodzakelijke versus ondersteunende invoer/bewijzen; ontbreken en tegenspraak. Leg veldrollen afzonderlijk vast voor kernzin, context, definitiebronnen, ontologierelaties, voorbeelden, praktijkvoorbeelden, tegenvoorbeelden, grensgevallen, synoniemen, homoniemen, toelichting en metadata. Onderscheid toetsobject, noodzakelijk bewijs, generatie-invoer en presentatie; benoem wat AI wel/niet mag wijzigen.
3. Q3: concrete relaties met ARAI-03, ESS-01/02/03/05 en CON-01/02. Een reproduceerbaar gemeten eigenschap hoeft niet begripsbepalend te zijn. Beslis niet over buurregels.
4. Q4: daadwerkelijk bewezen appgedrag per ingang: generatie, alleen toetsen, import, bewerken, review, conceptopslag, vaststelling en export/herbeoordeling. Volg invoer→transport→oordeel→opslag→weergave→handeling. Signaal is geen menselijk oordeel. Codelezing, serviceproef en UI-bewijs apart. Vergelijk ruwe modeluitvoer, extractie/opschoning en opgeslagen kandidaat waar nodig.
5. Q5: exacte norm-/regeltekst, toepasselijkheid, appmeldingen/contractvoorstellen en concrete vervangteksten met huidige vindplaats voor generatie (G), toetsing (T) en begrensde terugkoppeling (H). Dezelfde norm voor gegenereerde en aangeleverde inhoud. Geen extra afkeurgrond uit een stijlvoorkeur.
6. Q6: onderscheidende casussen, risico's, ontbrekend bewijs, concrete keuze met alternatief en gevolgen voor Chris. Voorverwachtingen onderbouwen vóór een nieuwe proef. Geen expertgold of juridische praktijkvaliditeit claimen voor synthetische voorbeelden.

Regelspecifieke vragen binnen Q1–Q6: wat maakt gevalslidmaatschap beoordeelbaar, anders dan numerieke meetbaarheid, juistheid of essentieel onderscheid? Wanneer volstaan kwalitatieve criteria? Hoe voorkomen we schijnprecisie, verzonnen drempels, noemerloze percentages en trefwoord-pass? Wanneer zijn meetcontext, populatie/noemer, inclusieve/exclusieve grens, referentietijd, werk-/kalenderdagen, bronversie en conflictafhandeling werkelijk nodig? Onderzoek twee onafhankelijke beoordelaars als kwaliteitsproef; onderscheid verschil in betekenis van verschil in toepassing/bewijs en stel geen universele tweepersoonspoort stilzwijgend vast.

H onderscheidt generatieovertreding, instructieconflict, invoer-/transportverlies, foutpositieve evaluator, ontbrekend bewijs, technische fout en schadelijke nabewerking. Geen bron, context, drempel of menselijke review verzinnen. Bescherm betekenis, bronbeperkingen, noodzakelijke namen en gebruikersinvoer. Geen automatische tekstwijziging in alleen-toetsen. Geef herstelgrond, stopreden, oorspronkelijke kandidaat en hertoetsing aan.

Dek de 14 onderdelen: doel, norm/besluiten, toepasselijkheid, context, definitiebronnen, ontologie, aanvullingen, appgedrag, skills/prompts, status/score/poorten, proeven, samenhang, verbeteringen/review, acceptatie/overdracht. Eén dekkingsmatrix volstaat.

## Onafhankelijkheid en volgende fasen

Bewaar je volledige eerste onderzoek met bijlagen vóór je nieuwe Codex-conclusies leest. Lees in deze fase geen `codex-onderzoek-*`, `besluitnotitie-*`, `casusregister-*`, nieuwe proefuitkomsten of synthese. De historische bronnen en actuele vastgestelde besluiten zijn gemeenschappelijk. Lever een bestandspad, hash, bewijsgrenzen en volgende actie.

Pas na bevestiging dat beide eerste versies bewaard zijn: review het volledige Codex-onderzoek en relevante bijlagen per punt (claim/versie, oordeel, bron/tegenbewijs, gevolg/correctie). Verwerk daarna ieder Codex-reviewpunt zichtbaar als overgenomen, deels overgenomen, afgewezen met grond of open; bewaar je v1. Controleer vervolgens de volledige synthese op weglatingen, juiste weergave van verschillen en betekenisverlies. Eén wederzijdse review en één synthesecontrole, daarna alleen gerichte controle van materiële punten.

Gebruik stabiele casus-ID's; behoud de zeven historische labels. Nieuwe proeven uitsluitend voor concrete open vragen of gewijzigde/ondeugdelijke bewijsbasis, offline, synthetisch en met verse opslag. Geen productiegegevens, live modelcalls, brede suite, appwijziging, databasewijziging, actieve skillwijziging, issuepublicatie, PR, automatisering of andere sessie. Schrijf uitsluitend nieuwe onderzoeksversies in de werkelijk gemapte onderzoeksmap. Claim geen gezamenlijke afronding zolang bijdragen of verwerkingen ontbreken.
