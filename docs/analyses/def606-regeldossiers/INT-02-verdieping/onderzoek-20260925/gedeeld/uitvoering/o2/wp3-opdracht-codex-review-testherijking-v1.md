# DEF-835 WP3 — gerichte review geaccordeerde testherijking

Jij bent dezelfde Codex CLI-reviewer, sessie 01a0e4f2-9a94-70b2-9dcd-87202e24b697. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Geen bron-/testwijzigingen, live appmodelcalls, productiedata, Actions, push/merge, verwijderingen of handover-/globaal onderhoud.

Chris heeft op 28 september expliciet "akkoord om het te fixen" gegeven voor wp3-scopeaanvulling-tests-v1.md. De eerdere bestandsblokkade voor deze vijf tests is vervallen.

Werkroot /private/tmp/def835-wp2-review-20260927, detached op 4f28badee67c5f351235ac2b5cbb273f4bbc5721. Base voor deze testdelta: 91949c883c6de9ffc21740173aee457eb77cbe5a. De eerder door jou geaccepteerde productiecode 9769730d6 is ongewijzigd. Controleer alleen de vijfbestanden-testdiff (+31/−11) en bijbehorend bewijs; herhaal geen volledige evaluatorreview.

Lees onder /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2:
- wp3-scopeaanvulling-tests-v1.md (nu geaccordeerd)
- wp3-opdracht-claude-testherijking-v1.md
- wp3-claude-testherijking-verslag-v1.md
- bewijs/wp3-testherijking-rood-v1.log: 8 failed, 113 passed, exit 1
- bewijs/wp3-testherijking-groen-v1.log: 121 passed, exit 0
- bewijs/wp3-testherijking-regressie-v1.log: 555 passed, exit 0
- bewijs/wp3-testherijking-lint-v1.log: Ruff/Black groen
- bewijs/wp3-coordinator-testherijking-v1.log: 555 passed in 3.04s, exit 0; hashes van alle elf testbestanden.

Acceptatie:
- Alle vijf harde versiecontroles blijven echte assertions, nu op geaccordeerd contract 2.3.0.
- De oude INT-02 signals=[] en assessment=None-cases zijn behouden; hun verwachting is nu terecht toegestaan. Onbekende velden, ongeldige typen en assessment/signals op andere regels blijven expliciet geweigerd. Exacte NE-melding behouden.
- Geen testfunctie/casus verwijderd (één functienaam volgt de nieuwe versie), geen skip/xfail/filter als oplossing. Aantal vijfbestanden-tests blijft 121.
- Geen productie-/schema-/configwijziging.
- De acht eerder vastgelegde failures zijn daadwerkelijk verholpen in de repositorytests; geen diagnosekopie als bewijs gebruiken.

Gebruik bestaande Python /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python en importlib/offlineconftest. Een gerichte eigen run op de vijf testbestanden is voldoende naast bron-/hashcontrole van de 555-run. Geen brede unitrun; eerdere afzonderlijke performance-tracker/importkwesties buiten scope blijven als bewijsgrens staan.

Rapporteer in het Nederlands base/head, werkelijke toetsing/exitcodes, eventuele concrete bevindingen en of het laatste open WP3-testopleverpunt gesloten kan worden. WP3-acceptatie is evaluator/registry/schema, geen WP4-modelkwaliteit of WP5-appintegratie/activering. Eindrapport wordt opgeslagen als wp3-codex-review-testherijking-v1.md.
