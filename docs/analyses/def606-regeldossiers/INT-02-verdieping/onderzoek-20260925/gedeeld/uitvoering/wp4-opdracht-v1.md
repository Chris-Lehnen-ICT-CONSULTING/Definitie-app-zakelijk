# Claude Code CLI — DEF-771, uitsluitend WP4 (ontvangen 26 september 2026)

Uitvoerder: Claude Code CLI-sessie a4b588d6-e4a1-4fd6-8f80-0aac55013d90. Letterlijke kern van de opdracht:

1. tests/unit/validation/test_v2_golden_int_more.py: hernoem test_int02_no_decision_rules_fail zodat de naam review_required zegt; behoud de tekst, bestaande controles en andere testgevallen. Voeg expliciete synthetische context toe zodat de open menselijke beoordeling werkelijk wordt uitgevoerd. Bevestig status review_required, signaal en afwezigheid van pass/violation voor INT-02.
2. tests/fixtures/toetsregels/runtime_cases.yaml: uitsluitend INT-02-entry, korting: verlaging indien tijdig betaald. Herijk de toelichting naar de brede norm en functieafhankelijke menselijke beoordeling, C24/C25; voeg expliciete context toe volgens bestaande fixturestructuur. Geen regelclassificatie dupliceren en geen testgeval verwijderen.

Bron: synthese v5 §6 en register C24/C25. De contextloze NE-route is behouden in de WP3-tests. Dit pakket wijzigt geen norm, patroon of productiecode.

RED → GREEN: unieke herstelkopieën vóór wijzigen; eerst de bestaande falende INT-02-golden-test en de INT-02-runtime-matrixprobe na WP3 vastleggen met commandoregel en exitstatus; niets kunstmatig rood maken. Daarna de volledige test_v2_golden_int_more.py plus test_rule_runtime_matrix.py draaien; Ruff/Black op de gewijzigde Python-test. Raming: twee bestaande bestanden, circa 10–30 gewijzigde regels. Geen commit/push/PR/Linear, dependency, verwijdering, live modelcall of productiedata; geen WP5. Stop na WP4 voor coördinatorcontrole.
