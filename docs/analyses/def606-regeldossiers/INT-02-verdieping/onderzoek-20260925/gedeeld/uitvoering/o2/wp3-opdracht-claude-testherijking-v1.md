# DEF-835 WP3 — geaccordeerde herijking vijf bestaande testbestanden

Jij bent dezelfde Claude Code CLI-uitvoerder, sessie c75abf0d-3c01-4c02-a672-536d75daa15a. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Alles in het Nederlands.

Chris heeft op 28 september 2026 expliciet geantwoord: "akkoord om het te fixen", op de tussenoplevering met de open vraag voor vijf testbestanden. Daarmee is wp3-scopeaanvulling-tests-v1.md nu geaccordeerd. Geen nieuwe akkoordvraag nodig.

Werk uitsluitend in /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2, branch feature/DEF-835-int02-o2, HEAD 91949c883c6de9ffc21740173aee457eb77cbe5a. De gereviewde productiecode is 9769730d6 en blijft ongewijzigd. Je bent niet alleen in de repo: behoud ander werk.

## Eigendom: uitsluitend deze vijf testbestanden

1. tests/unit/validation/test_def771_int02_o1.py
2. tests/unit/validation/test_validation_readiness.py
3. tests/unit/services/orchestrators/test_def743_source_assessment_wrappers.py
4. tests/unit/services/orchestrators/test_def772_int03_wrappers.py
5. tests/unit/services/orchestrators/test_def766_ess03_wrappers.py

Lees het concrete voorstel wp3-scopeaanvulling-tests-v1.md. Herijk de vijf harde actuele versieassertions naar het goedgekeurde 2.3.0 en de bijbehorende actuele commentaren/testnaam waar nodig. Historische versiegeschiedenis niet herschrijven. Behoud de daadwerkelijke versiecontrole, vervang haar niet door een tautologie of verwijderen.

De O1-test met INT-02-assessment/signals verandert inhoudelijk van "verboden" naar "toegestaan voor INT-02"; BEHOUD beide cases en controleer dat ongeldige typen/onbekende velden en deze velden op andere regels nog worden geweigerd. Verwijder geen cases of assertions zonder gelijkwaardige, passende contractcontrole; alleen het inmiddels onjuiste verwachte resultaat moet veranderen. De exacte NE-uitkomst blijft behouden.

Vooraf unieke herstelkopieën onder dossierbewijs. Draai de vijf ongewijzigde bestanden eerst en bewaar de acht verwachte failures als RED. Na de gerichte herijking dezelfde bestanden GREEN. Geen skip/xfail/wegfilteren en geen productiecode/schema/dependencies wijzigen.

Doe daarna één gerichte regressierun op:
- de vijf gewijzigde testbestanden;
- tests/unit/validation/test_def835_int02_evaluator.py;
- tests/integration/contracts/test_validation_result_schema.py;
- tests/unit/validation/test_def772_int03_evaluator.py;
- tests/unit/validation/test_evaluator_registry_contract.py;
- tests/unit/validation/test_rule_cache_runtime_contract.py;
- tests/unit/domain/test_def835_int02_contract.py.

Gebruik /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest met -o addopts= --import-mode=importlib -q -ra. Ruff (ook geldige pre-commitversie) en Black-check op de vijf testbestanden. Geen nieuwe brede unitrun: dat bewijs en de bekende afzonderlijke isolatie/importkwesties zijn reeds vastgelegd; deze wijziging betreft uitsluitend testverwachtingen.

Bewaar volledige logs/exitcodes als bewijs/wp3-testherijking-rood-v1.log, wp3-testherijking-groen-v1.log, wp3-testherijking-regressie-v1.log en wp3-testherijking-lint-v1.log. Schrijf wp3-claude-testherijking-verslag-v1.md met scope, exacte diffomvang, casesbehoud, uitkomsten en hashes. Prompts volledig in dit dossier; eerder geautoriseerde Prompt Forge-fallback geldt.

Geen commit/push/merge/Actions/modelcalls/productiedata/verwijderingen. Maximaal drie pogingen per actie. Stop na verslag; de coördinator verifieert en geeft de concrete testdiff aan dezelfde Codex-reviewer. De rol-/projectregels en skills uit eerdere opdracht blijven gelden.
