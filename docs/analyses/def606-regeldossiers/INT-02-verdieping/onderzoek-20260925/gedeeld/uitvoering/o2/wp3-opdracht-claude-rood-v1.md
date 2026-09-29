# DEF-835 WP3 — Claude Code CLI, eerst RED

Jij bent de Claude Code CLI-uitvoerder. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. De coördinator verifieert en organiseert later onafhankelijke Codex CLI-review. Alles in het Nederlands.

## Mandaat en werkplek

Werk uitsluitend in /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2, branch feature/DEF-835-int02-o2, basis 2be81c577653f8efbab6fa2c3794598556d32d13. Controleer branch/status. Je bent niet alleen in de repository: behoud ander werk en draai niets terug. Chris heeft nu expliciet de uitbreiding naar **negen bestanden** uit wp3-scopeaanvulling-v1.md geaccordeerd. Meer dan 100 regels voor INT-02 is toegestaan. Geen verdere akkoordvraag voor dit pakket nodig.

Lees CLAUDE.md, .claude/rules/project-rules.md en patterns.md, globale programmeerregels en toepasselijke TDD-skill. Toegewezen uitvoerder, dus geen herdelegatie. Geen bestanden/testgevallen verwijderen, geen nieuwe dependencies, geen live appmodelcalls, geen productiegegevens, geen Actions/push/merge/activering. Behoud normale veiligheidscontroles. Bij echte blokkade rapporteren; maximaal drie pogingen per actie.

## Leidende bronnen

Dossier docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/.
Lees gedeeld/besluiten-chris-v1.md en gezamenlijke-synthese-v5.md §2/§4 voor exacte betekenis/meldingen; gedeeld/uitvoering/o2/plan-v1.md WP3; wp3-scopeaanvulling-v1.md en takenlijst-v9.md. WP1/WP2 zijn al geïmplementeerd en gereviewd: src/domain/int02/contract.py, docs/architectuur/contracts/int02_assessment_contract_v1.md en src/services/validation/int02_assessment_service.py. Gebruik bestaande domeinvalidatie/toets_actualiteit; schrijf geen parallelle semantische beoordelingslogica. Gebruik INT-03 evaluator als architectuurvoorbeeld, niet als bron van INT-02-norm.

## Geaccordeerde totale scope

1. nieuw src/services/validation/evaluators/decision_rule_assessment.py
2. src/toetsregels/runtime_contract.py
3. src/services/validation/evaluators/__init__.py
4. docs/architectuur/contracts/validation_result_contract.md
5. docs/architectuur/contracts/schemas/validation_result.schema.json
6. nieuw tests/unit/validation/test_def835_int02_evaluator.py
7. tests/integration/contracts/test_validation_result_schema.py
8. config/toetsregels/toetsregels_config.yaml — alleen bekende evaluatorwaarde.
9. src/services/validation/interfaces.py — versie 2.3.0 en gerichte INT-02-documentatie.

In deze RED-opdracht uitsluitend bestanden 6 en 7 schrijven/bewerken. Nog GEEN productiecode, schema of documentcontract wijzigen. Voor het bestaande testbestand vooraf unieke herstelkopie in dossierbewijs bewaren. Geen tests verwijderen; geen versie-hardcodes aan andere bestaande tests aanpassen om rood te verbergen.

## Gewenst gedrag dat je nu met tests specificeert

- Nieuw evaluatortype decision_rule_assessment geregistreerd en toegestaan door root-SSOT. Actief INT-02.json blijft judgment_review en excluded_from_score.
- Pure synchrone evaluator leest exact de huidige invoer en expliciete actuele configuratie uit EvaluationContext/metadata, naast getypeerd WP1-beoordelingsdocument. Geen modelcalls. Gebruik de bestaande mechanische WP1-controles: onbekend/ongeldig/gesaboteerd oordeel kan nooit pass of fail dragen. Ontbrekende benodigde input geeft exacte NE; ontbrekend oordeel RR; veranderd bindingsveld historisch RR; fout/ongeldig document error. Rapportage maakt onderscheid actueel/historisch/niet beoordeeld.
- Alle zes statussen met controleerbaar assessment naar metadata.rule_result, score null. Fail adviserend, uitgesloten van score, geen acceptatiepoort/herstel. Signalen zijn losse leeshulp en wijzigen geen status of bewijs. Signalen komen uit huidig record/invoer, niet blind uit meegegeven oordeel.
- Publiek contractversie 2.3.0, assessment/signals optioneel uitsluitend voor INT-02 en reeds bestaande INT-03. Andere regels en onbekende velden blijven gesloten. Bestaande geldige O1/INT-03-resultaten blijven geldig. Maak relevante tests die de echte evaluatoruitkomst tegen het echte schema controleren, niet alleen zelfbedachte losse dicts.
- Tijdelijk testrecord via bestaande registry; test juist dat rootpolicy/enums overeenkomen. Geen wijziging aan actief record.
- Centrale interfaces.CONTRACT_VERSION wordt 2.3.0 en is de publieke versiebron.
- Geen verborgen documentmutatie; herhaalde evaluatie moet oorspronkelijke input/oordeel behouden. Ongeldige metadata netjes afgehandeld.

## Expliciete grens

WP3 is evaluator + registry + schema; de volledige ModularValidationService-boekhouding en container/orchestrator/UI/opslag horen bij WP5. De coördinator heeft vastgesteld dat _EVALUATORS_MET_DEELUITKOMST later uitgebreid moet worden. Dat bestand nu NIET wijzigen en geen claim dat de volledige appketen O2 al uitvoert. WP1/WP2 evenmin wijzigen. Kies een kleine expliciete metadata-interface die bij hun getypeerde contract past; documenteer die in je verslag.

## RED-bewijs en stop

Python /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python.
Schrijf assertieve gedragstests: ontbrekende nieuwe module bij voorkeur als testfailure via importlib/assert afhandelen, niet alleen één collectiefout. Bestaande schemafile moet blijven collecteren. Draai de twee testfiles met -o addopts= -q -ra en bewaar volledige uitvoer plus exitcode in gedeeld/uitvoering/o2/bewijs/wp3-claude-rood-v1.log. Zorg dat rood door ontbrekend gedrag ontstaat; bestaande controles mogen groen blijven.

Daarna STOP vóór implementatie. Schrijf gedeeld/uitvoering/o2/wp3-claude-rood-verslag-v1.md met scope, testselectie/resultaat, ontbrekend gedrag, voorgestelde metadata-interface en eventuele concrete blocker. Geen commit/push in deze RED-fase. Volledige prompt staat in het dossier; Prompt Forge-check was eerder door hook geblokkeerd en dossierfallback is toegestaan. Geen nieuwe poging/omzeiling.
