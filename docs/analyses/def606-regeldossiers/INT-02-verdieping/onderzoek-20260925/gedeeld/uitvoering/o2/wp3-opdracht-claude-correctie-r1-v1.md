# WP3-R1 — gerichte correctie, dezelfde Claude CLI-uitvoerder

Jij bent de Claude Code CLI-uitvoerder in sessie c75abf0d-3c01-4c02-a672-536d75daa15a. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies.

Werk in /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2, feature/DEF-835-int02-o2, huidige code d3fc53eaed14e6a303605146b7e5f8b9ea3cef5e. Niet alleen in de repository: behoud ander werk. Alle vorige scope-/offline-/geen-verwijdering-/geen-pushregels blijven gelden.

Lees wp3-codex-review-v1.md. Eén concrete Important/P2-bevinding WP3-R1 is door de coördinator bevestigd aan de hand van code en het gepubliceerde metadata-contract: een aanwezige record_text met verkeerd type valt nu terug op raw_text en kan pass/fail opleveren. Dat contract staat terugval alleen toe bij ontbreken van de sleutel.

Eigendom en wijzigingsscope, uitsluitend:
- src/services/validation/evaluators/decision_rule_assessment.py
- tests/unit/validation/test_def835_int02_evaluator.py

Schrijf eerst regressietests voor de acht onafhankelijk gereproduceerde combinaties: document met pass/fail, record_text expliciet None/42/[]/{}. Verwacht error, exacte WP1-foutmelding, geen assessment/violation, geen actueel oordeel. Behoud ook de bestaande test dat ontbrekende record_text op raw_text terugvalt. Bewaar RED-uitvoer vóór de correctie; voer daarna minimale fix uit en toon GREEN op dezelfde tests. Maak geen functionele wijziging voor legitieme lege string (NE) of afwezige sleutel.

Rond af met de twee WP3-testbestanden en relevante lint/Black. Geen nieuwe brede unitrun; dat bewijs is al bekend. Geen wijziging van de vijf voorgestelde extra testbestanden: akkoord daarvoor ontbreekt nog. Geen nieuwe contractbesluiten of appintegratie.

Bewaar volledige logs/exitcodes als bewijs/wp3-claude-r1-rood-v1.log, wp3-claude-r1-groen-v1.log en wp3-claude-r1-lint-v1.log. Schrijf wp3-claude-r1-verslag-v1.md met hashes en uitkomsten. Geen commit; coördinator doet de concrete reviewcommit. Maximaal drie pogingen per actie. Stop daarna.
