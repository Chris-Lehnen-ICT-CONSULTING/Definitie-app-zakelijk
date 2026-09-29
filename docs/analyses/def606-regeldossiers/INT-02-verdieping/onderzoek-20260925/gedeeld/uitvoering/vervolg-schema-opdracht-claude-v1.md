# DEF-771 — geaccordeerde schema-/contractcorrectie B1/B2

Jij bent dezelfde Claude Code CLI-uitvoerder a4b588d6-e4a1-4fd6-8f80-0aac55013d90. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Je bent niet alleen in de codebase: behoud het werk van anderen. Alles Nederlands. De hoofdsessie coördineert en commit; dezelfde afzonderlijke Codex CLI-sessie reviewt, zonder bronbestanden te wijzigen. Lees rules/codex-programmeerwerk.md in /Users/chrislehnen/Projecten/_claude-global-setup.

## Akkoord en bron

Chris antwoordde zojuist expliciet "ja akkoord" op het voorstel om het schema en de versieassertie te corrigeren, daarna te testen en onafhankelijk te reviewen. Dit is het afzonderlijke schema-/resultaatcontractakkoord voor B1/B2 uit vervolg-integratie-rapport-v1.md en processtatus-uitvoering-v7.md. De 100-regelsgrens is eerder voor noodzakelijk INT-02-werk verruimd. Geen akkoord voor PR-merge of actieve uitrol.

App /Users/chrislehnen/Projecten/Definitie-app, feature/DEF-771-int02-contract-o1, HEAD b56e2878268f744f224e8d1326c9198378b025bc, MERGE_HEAD 076c916671e4e7e9f2843d22669df38eeb79e170. De opgeloste merge staat in de index, geen ongestagede bronwijzigingen. Skillwerkboom .worktrees/DEF-771-int02-skills: HEAD 750068253a7389e201daedc5b9aa0afd5c0be032, MERGE_HEAD 770de55ece429fec826c9d53fd873a109ed8e670; niets meer wijzigen daar.

## Doel en eigendom — maximaal vijf inhoudelijke bestanden

1. docs/architectuur/contracts/schemas/validation_result.schema.json: breng het schema in overeenstemming met de bestaande INT-03-runtimevelden assessment en signals binnen rule_results. Expliciete typen, optioneel/backward-compatible; onbekende velden blijven afgewezen. Beperk waar passend deze bestaande INT-03-uitbreiding tot die regel, zonder de algemene strenge schemacontrole te verzwakken. Geen globaal additionalProperties=true, geen schema leegmaken, geen runtimeveld verwijderen.
2. src/services/validation/interfaces.py: werk de bijbehorende typing/commentaarbinding alleen bij voor zover nodig voor deze twee bestaande velden. De nog niet gemergde releasekandidaat blijft CONTRACT_VERSION 2.2.0: deze correctie wordt toegevoegd aan dezelfde additieve release boven main 2.1.0. Geen hernummering van alle bestaande historische verwijzingen nodig.
3. docs/architectuur/contracts/validation_result_contract.md: documenteer deze aanvullende inhoud van de nog niet gemergde 2.2.0; behoud de bestaande INT-02-NE-beschrijving, verduidelijk dat deze contractcorrectie bestaande INT-03-runtimevelden beschrijft. De eerdere zin "geen nieuw veld" moet binnen het juiste historische deelbereik staan. Geen nieuwe norm of live-modelbeleid.
4. tests/unit/services/orchestrators/test_def772_int03_wrappers.py: verouderde assertie en actuele contractverwijzing 2.1.0 naar 2.2.0; behoud inhoudelijke bindingtests.
5. tests/unit/validation/test_def771_int02_o1.py: bestaande brede rule_results-schemacontrole behouden. Voeg hier gerichte regressiegevallen toe voor bestaande INT-03-uitkomsten met/zonder beoordeling, expliciete typen van assessment/signals, afwijzing van onbekende velden en behoud van INT-02-NE/RR. Gebruik bestaande fakes/fixtures en echte evaluator waar passend; geen model of netwerk.

Als voor correctheid een zesde inhoudelijk bestand nodig blijkt: meld eerst concrete reden. Geen andere software wijzigen. Geen aliasbundels, Actions, gates, herstel, DEF-626, install/publicatie of brondata aanraken. Geen tests verwijderen/overslaan, geen afzwakking tot alleen INT-02, geen nieuwe dependencies.

## TDD en bewijs

Bewaar eerst de bestaande vier relevante failures als RED (of hergebruik exacte identieke bron en log met verwijzing); voer nieuw toegevoegde regressietests vóór schemawijziging rood uit. Corrigeer vervolgens schema/typing/docs en versieassertie. Maximaal drie pogingen per concrete actie. Alle tests via bestaande offline-bootstrap; DEF771_SKILLS_ROOT wijst naar de beheerde skillwerkboom/skills.

Draai dezelfde gerichte selectie als vervolg-integratie-tests-v1.log opnieuw, met nieuwe lognaam vervolg-schema-tests-v1.log; de al verklaarde negatieve-prompttest niet repareren. Verwacht B1 en B2 opgelost, geen nieuwe failures. Ruff/Black voor geraakte Python en make lint. De ongewijzigde ketenproef is al groen op dezelfde runtimecode; niet opnieuw draaien zonder concrete gedragswijziging. Geen volledige pytest-suite starten, die doet de coördinator na jouw afronding.

Alle prompts/logs/RED/GREEN/rapport volledig in gedeeld/uitvoering onder vrije vervolg-schema-* namen, geen bestaand bewijs overschrijven. Prompt Forge blijft de eerder vastgelegde dossierfallback. Leg exact gewijzigde bestanden en testresultaten vast. Geen commit/push. Laat de nieuwe correctie eerst ongestaged naast de bestaande voorbereide merge staan: de coördinator moet de correctiediff apart kunnen controleren. Stop na rapportage; geen extra review of delegatie.
