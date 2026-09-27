# WP3 — noodzakelijke herijking bestaande contracttests

28 september 2026. Voorstel; nog niet toegepast. De negen eerder geaccordeerde bestanden worden binnen dat mandaat uitgevoerd.

## Gecontroleerde omissie

De centrale versie moet volgens het geaccordeerde WP3 naar 2.3.0. Een repositorybrede zoekopdracht naar 2.2.0 in tests toont vijf bestaande testbestanden met een harde pin op de oude centrale versie. Die verwachtingen kunnen niet tegelijk groen blijven met de geaccordeerde versie. Dit verandert geen INT-02-besluit.

Voorgestelde extra bestanden (negen → veertien inhoudelijke bestanden totaal):

1. tests/unit/validation/test_def771_int02_o1.py:291 — de harde versiepin 2.2.0 herijken naar 2.3.0. Regels 366–380: behoud de bestaande cases, maar toets dat assessment/signals voor INT-02 nu toegestaan zijn; onbekende velden blijven geweigerd, en bij andere regels dan INT-02/INT-03 blijven deze twee velden geweigerd. Exacte NE-melding blijft behouden.
2. tests/unit/validation/test_validation_readiness.py:188 — versiepin naar 2.3.0; omliggende commentaarregel gericht bijwerken.
3. tests/unit/services/orchestrators/test_def743_source_assessment_wrappers.py:138 — versiepin naar 2.3.0; versiecommentaar gericht bijwerken.
4. tests/unit/services/orchestrators/test_def772_int03_wrappers.py:103 — versiepin naar 2.3.0; actuele versiecommentaren gericht bijwerken, historische bronverwijzingen blijven herkenbaar.
5. tests/unit/services/orchestrators/test_def766_ess03_wrappers.py:95 — versiepin naar 2.3.0; versiecommentaar gericht bijwerken.

Geschat circa 20–40 gewijzigde test-/commentaarregels. Geen productiecode, dependencies of nieuwe contractbesluiten boven de goedgekeurde 2.3.0-uitbreiding. Geen testgeval verwijderen. Laat dezelfde Claude Code CLI-uitvoerder eerst de verouderde verwachtingen rood vastleggen na de productieaanpassing; pas daarna inhoudelijk herijken. Coördinator controleert de vijf testbestanden en laat dezelfde onafhankelijke WP3-reviewer de volledige concrete diff beoordelen.

## Reeds gecontroleerd bewijs

RED van de twee WP3-testbestanden: 92 failed, 19 passed in 5.53s, exit 1; geen collectie-/setupfouten. Bestands-SHA's komen overeen met het bewijslog. De eerste logpoging had een shellquotingfout (exit 127, pytest niet gestart); de directe opdracht daarna leverde de geldige RED-run. Geen bestaande testgevallen verwijderd. Zie wp3-claude-rood-verslag-v1.md §6 en bewijs/wp3-claude-rood-v1.log.

Deze beperkte testcorrecties vragen volgens de oorspronkelijke bestandsgrens expliciet akkoord. De implementatie binnen de negen reeds goedgekeurde bestanden hoeft er niet op te wachten; de regressie- en opleverclaim wel.
