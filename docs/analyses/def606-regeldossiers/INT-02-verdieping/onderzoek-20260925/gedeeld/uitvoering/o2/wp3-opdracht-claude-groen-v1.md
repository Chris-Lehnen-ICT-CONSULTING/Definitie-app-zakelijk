# DEF-835 WP3 — GREEN, dezelfde Claude Code CLI-uitvoerder

Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Hervat je eigen RED-sessie en voer nu de implementatie uit. Deze prompt wordt pas door de coördinator verzonden nadat de RED-uitvoer gecontroleerd is. Je vorige opdracht en het geaccordeerde negen-bestandenvoorstel blijven leidend.

Werk uitsluitend in /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2, feature/DEF-835-int02-o2. Je bent niet alleen; behoud ander werk. Geen nieuwe dependencies, verwijderingen, appmodelcalls, productiegegevens, push, merge, Actions of activering. Geen wijziging aan WP1/WP2 of ModularValidationService. Maximaal drie pogingen per actie; meld echte blokkades.

Implementeer het ontbrekende gedrag binnen de zeven productie-/contractbestanden uit de negenbestandenlijst. De twee testbestanden mogen alleen gericht worden aangevuld of aantoonbaar onjuiste assertions worden gecorrigeerd, met reden en afzonderlijk RED-bewijs vóór de fix. Verwijder geen testgeval. Maak vóór de wijziging van een bestaand contractdocument een unieke herstelkopie in dossierbewijs; gebruik gerichte edits.

Hergebruik WP1-toets_actualiteit en de bestaande contracttypen. Bind aan de actuele exacte kern, betekenis, context, bronnen en expliciete configuratie; ontleen actuele invoer/configuratie niet aan het historische document. Ontbrekende of ongeldige metadata mag geen positieve uitkomst leveren en geen ruwe inhoud loggen. Signalen blijven losse leeshulp en komen uit het huidige record. Onbekende metadata wordt niet als bewezen oordeel vertrouwd.

Publieke versie 2.3.0 en uitsluitend INT-02-uitbreiding naast bestaande INT-03, gesloten onbekende velden. Documenteer de getypeerde metadata-aansluiting en de grens: evaluator/registry/schema gereed betekent nog geen container-/orchestrator-/appintegratie. Actief INT-02-record blijft O1. Geef adviserend fail, score null, zes statuspaden en de letterlijke normmeldingen.

Verificatie:
1. De twee WP3-testbestanden met /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest, -o addopts= -q -ra.
2. Gerichte regressie: tests/unit/validation/test_def771_int02_o1.py, tests/unit/validation/test_def772_int03_evaluator.py, tests/unit/validation/test_evaluator_registry_contract.py, tests/unit/validation/test_rule_cache_runtime_contract.py en tests/unit/domain/test_def835_int02_contract.py.
3. Ruff en Black-controle op gewijzigde Pythonbestanden. Gebruik bestaande installatie; geen dependencywijzigingen.

Bewaar volledige uitvoer en exitcodes in vrije wp3-claude-groen-v1.log, wp3-claude-regressie-v1.log en wp3-claude-lint-v1.log onder gedeeld/uitvoering/o2/bewijs. Geen bestaande log overschrijven.

Schrijf wp3-claude-groen-verslag-v1.md onder dezelfde dossiermap met gewijzigde bestanden/omvang, testresultaten, metadata-interface, bewijsgrenzen, eventuele testcorrecties en afwijkingen. Geen commit: de coördinator inspecteert en maakt de concrete reviewcommit. Geen verdere taken of afgeleide sessies starten. Stop na rapportage.
