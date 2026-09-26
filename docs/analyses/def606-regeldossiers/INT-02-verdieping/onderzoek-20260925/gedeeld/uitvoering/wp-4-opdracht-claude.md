# Claude Code CLI — DEF-771, uitsluitend WP4

Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Jij bent dezelfde uitvoerder (a4b588d6-e4a1-4fd6-8f80-0aac55013d90). Coördinator verifieert; afzonderlijke verse Codex CLI-sessie reviewt de volledige diff in WP5. Alles Nederlands. Deze opdracht wordt pas verzonden na het WP3-controlepunt.

Werkboom /Users/chrislehnen/Projecten/Definitie-app; branch feature/DEF-771-int02-contract-o1; basis 0d26f0f4f5b2ebebe1c7d71fbff5e4ddb66b8c0d plus WP1–3. WP4 is onder plan-v1 goedgekeurd: twee bestaande bestanden, circa 10–30 gewijzigde regels. Alleen jij schrijft deze bestanden; behoud andere wijzigingen. Geen commit/push/PR/Linear, dependency, verwijdering, live modelcall of productiedata. Geen WP5 starten. Beveiliging intact; maximaal drie pogingen per actie.

## Doel en eigendom

1. tests/unit/validation/test_v2_golden_int_more.py: hernoem test_int02_no_decision_rules_fail zodat de naam review_required zegt; behoud de tekst, bestaande controles en andere testgevallen. Voeg expliciete synthetische context toe zodat de open menselijke beoordeling werkelijk wordt uitgevoerd. Bevestig status review_required, signaal en afwezigheid van pass/violation voor INT-02.
2. tests/fixtures/toetsregels/runtime_cases.yaml: uitsluitend INT-02-entry, korting: verlaging indien tijdig betaald. Herijk de toelichting naar de brede norm en functieafhankelijke menselijke beoordeling, C24/C25; voeg expliciete context toe volgens bestaande fixturestructuur. Geen regelclassificatie dupliceren en geen testgeval verwijderen.

Bron: synthese v5 §6 en register C24/C25. De contextloze NE-route is behouden in de WP3-tests. Dit pakket wijzigt geen norm, patroon of productiecode.

## RED → GREEN

Maak unieke herstelkopieën vóór wijzigen. Leg eerst de bestaande falende INT-02-golden-test en INT-02-runtime-matrixprobe na WP3 vast met commandoregel en exitstatus. Gebruik bestaande inhoudelijke failure, maak niets kunstmatig rood. Daarna wijzigingen uitvoeren en de volledige test_v2_golden_int_more.py plus test_rule_runtime_matrix.py draaien. Behoud alle tests; onverwachte failure verklaren en bij scope-uitbreiding melden. Ruff/Black op de gewijzigde Python-test. Gebruik .venv en de bestaande offline-bootstrap.

Bewaar opdracht en volledige uitvoer onder docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/. Gebruik vrije lognamen; bestaande logs/resultaten nooit overschrijven. Prompt Forge-dossierfallback is geautoriseerd.

Lever kort: exacte diffstat, twee paden en hashes, RED→GREEN-aantallen met logpaden/exitcodes, casusdekking C24/C25 en open punten. Stop na WP4 voor coördinatorcontrole.
