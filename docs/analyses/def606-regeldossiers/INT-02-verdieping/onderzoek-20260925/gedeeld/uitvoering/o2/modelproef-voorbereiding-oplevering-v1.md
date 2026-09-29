# DEF-835 — technische modelproef voorbereid en gereviewd

28 september 2026. Vervolg op Chris' vraag waarom het werk bij takenlijst v14 stopte. De onafhankelijke voorbereiding is hervat en afgerond. **Nog geen echte INT-02-modelproef uitgevoerd.** Het concrete profiel-/budgetakkoord en WP5a-bereik zijn in deze chat voorgelegd en hebben bij het schrijven nog geen antwoord.

## Geleverd

- Een geïsoleerde proefrunner plus tests; twee nieuwe softwarebestanden. Runner 1106 regels, tests 909 regels. De oorspronkelijke raming 300–500 was te laag; de verruiming voor INT-02 is toegepast. Geen productiecode, actieve recordconfiguratie, dependency of database gewijzigd.
- Offline voorbereiding en manifestbinding op echte bestaande INT-02-keten/prompt, inclusief transportinstellingen; uitsluitend synthetische invoer C105/C107/C112. Geen goldsetclaim.
- Maximaal drie inferencecalls en drie tokenmetingen, met deadlines, geen retries/fallback/cache, conservatieve budgetreservering, daadwerkelijke usage en expliciete kostenonzekerheid. Nog geen uitvoeringsakkoordbestand aangemaakt.
- Concreet vervolgvoorstel voor WP5a: zeven bestanden en optionele API-injectie. Gedeelde opslag volgt daarna binnen DEF-626; geen parallelle INT-02-historie voorgesteld.

## Commits en rollen

Werkboom `.claude/worktrees/DEF-835-int02-o2`, branch `feature/DEF-835-int02-o2`.

- Basis: `558b50c3f161f819cda6c445f7f81b70888918ac`.
- Eerste runner: `dff713fd45a2c87b6d3b646e500e108b5cd61b03`.
- Geaccepteerde correctie/eindstand: **`979ca0585100d94b613829d924c6d8bba4f24f1b`**.
- Implementatie en correctie: echte Claude Code CLI 2.1.283, sessie `57f4b3fa-7776-4a45-bdee-732da1344d2f`, model claude-opus-5-5; Read/Glob/Grep/Edit/Write/Bash, geen MCP/Agent/Task. Dit ontwikkelmodel staat los van het app-proefmodel.
- Onafhankelijke review/herreview: Codex CLI 0.157.1, sessie `01a0e76c-9ee2-7ce1-be3c-e6a9d39b3417`, aparte reviewwerkroot `/private/tmp/def835-wp2-review-20260927`. Eigen bronbestanden niet gewijzigd; geen herdelegatie.
- Coördinator: opdrachten/documenten, gericht brononderzoek, uitvoering van tests en controle van bewijsbinding. Geen runner- of testcode geschreven.

Volledige opdrachten: `modelproef-opdracht-claude-v1.md`, `modelproef-opdracht-claude-correctie-v1.md`, `modelproef-opdracht-codex-review-v1.md`, `modelproef-opdracht-codex-herreview-v1.md`. Verslagen/reviews en geselecteerde bewijslogs staan in dit dossier. Ruwe CLI-streams en de tijdelijke mutatiehulpscripts blijven lokaal beschikbaar onder bewijs; zij vervangen geen reviewrapport. Eerder vastgestelde Prompt Forge-fallback blijft gelden.

## Bevindingen en dispositie

| Punt | Actie en uitkomst |
| --- | --- |
| R1/P1: antwoordmodel kon afwijken zonder stop | Dezelfde uitvoerder corrigeerde exacte modelbinding en kostenonzekerheid. Zes varianten geven één call, error zonder oordeel en onbekende kosten. Dezelfde reviewer sloot R1. |
| R2/P2: SDK-environment kon transport/authenticatie veranderen buiten akkoord | SDK- en requestcontroles, standaard endpoint/poort/APIversie en manifesttransportbinding toegevoegd. Reproducties geven nul verzendingen. Dezelfde reviewer sloot R2. |
| Bestaande provider-usagevelden ontbraken | Officiële SDK/primaire documentatie gericht gecontroleerd; global/standard-vormen ondersteund, overige kostenvarianten blijven stoppen. Detailtokens worden niet dubbel geteld. Herreview akkoord. |
| Deadlinebewijs ontbrak | Fake-inference met 0,05s deadline toont cancellation, één call en geen ruwe fouttekst. Herreview gesloten voor dit concrete scenario. |

Geen open bevestigde runnerbevindingen. Geen extra algemene review of mutatiematrix na de correctie.

## Bewijs

| Controle | Uitkomst |
| --- | --- |
| Eerste runner | 40 tests groen; 518 in de gecombineerde regressieset, inclusief die 40 |
| Eerste RED | Alleen collectionfout doordat runner ontbrak; geen bewijs van gedragsmatige TDD |
| Correctie RED-v2 op oude runner | **34 failed, 41 passed**, exit 1; R1 reproduceert drie calls waar één verwacht is |
| Uitvoerder GREEN na correctie | **75 passed**, exit 0 |
| Coördinator op uiteindelijke commit | **75 passed in 3.27s**, exit 0 |
| Onafhankelijke herreview op uiteindelijke commit | **75 passed in 3.26s**, exit 0; R1/R2 gesloten, geen nieuwe bevindingen |
| Lint en normale commithooks | Geslaagd volgens gecontroleerde logs |
| Manifest v2 | Alle 13 bronhashes en drie payloadhashes gecontroleerd; geen afwijking; payloads gelijk aan v1 |

Tussen correctie-RED en GREEN is het testbestand geformatteerd: de bytes zijn niet identiek. De reviewer bevestigde de relevante gedragsmatige RED en de uiteindelijke checks. De oorspronkelijke mutatiematrix bewees tien specifieke mutaties, geen volledige guarddekking. De 478 overige regressietests zijn na de runnercorrectie niet herhaald: geen productiecode of gedeelde fixtures gewijzigd en geen concrete doorwerking vastgesteld. Geen volledige groene-suiteclaim.

Definitief manifest: `bewijs/modelproef-manifest-v2.json`, toestemming **pending**, SHA-256:

`54c75b43b2b55a132e58a896f2d5d909bebf97b521a26ff0d77bb783a0df35c8`

## Eerstvolgende stappen

1. Antwoord verwerken op het voorgelegde technische profiel: bestaand claude-opus-5, maximaal drie synthetische calls, begroting maximaal $0,69 en voorgesteld US$1-plafond. Algemene toestemming voor echte modelaanroepen bestaat al. Het ontvangen profiel-/budgetbesluit herleidbaar aan manifest v2 koppelen; geen nieuwe algemene toestemmingsvraag.
2. Daarna echte proef eenmaal uitvoeren, stoppen volgens runner, gemeten usage/kosten/uitkomsten rapporteren. Alleen synthetische payloads/antwoorden in het bewijsdossier; geen productiedata.
3. Na akkoord op `wp5a-integratievoorstel-v1.md`: volgende afgebakende CLI-opdracht voor aansluiting op validatieketen, met actieve O1-route behouden.
4. Voor volledige O2 blijven onafhankelijke goldset/inhoudelijke kwalificatie, gedeelde opslag DEF-626, presentatie/herladen/export, finale verificatie en afzonderlijke activering nodig.

Model-ID, tier en geografie worden pas na het antwoord gecontroleerd. Een afwijkende call kan al kosten hebben gemaakt; die worden als onzeker geregistreerd. De reservering is geen providerfactuurgarantie. Technische offline geschiktheid bewijst geen echte provideracceptatie, modelkwaliteit of productiegeschiktheid.

Actions niet aangezet. Geen push, merge of activering. Beide CLI-processen zijn afgerond.
