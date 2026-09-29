# DEF-835 — actuele takenlijst v12

28 september 2026. Actuele ingang; v11 en eerdere versies zijn historisch bewijs.

- [x] WP1 en offline WP2 afgerond.
- [x] WP3: negen bestanden geaccordeerd en geïmplementeerd, code d3fc53eae.
- [x] RED 92/19 → GREEN 111 met bytegelijke tests.
- [x] Coördinatorcontrole: 539 geslaagd, 8 bekende oude assertions falend.
- [x] Onafhankelijke review; WP3-R1 gecorrigeerd door dezelfde Claude-uitvoerder.
- [x] Correctiecode 9769730d6: 119 tests groen, zowel coördinator als dezelfde onafhankelijke reviewer. R1 gesloten.
- [ ] Chris: vijf extra bestaande testbestanden uit wp3-scopeaanvulling-tests-v1.md goedkeuren. Async vraag staat nog open.
- [ ] Die testverwachtingen herijken zonder cases te verwijderen; gerichte verificatie en review.
- [ ] WP3 volledig aftekenen; nu uitsluitend tussenoplevering van de negen bestanden.
- [ ] Technische echte modelproef: toestemming aanwezig, profiel/kostenplafond open.
- [ ] WP4 goldset/hold-out en inhoudelijke modelevaluatie.
- [ ] WP5 appintegratie/gedeelde opslag/ketenlogging, inclusief ModularValidationService-boekhouding.
- [ ] WP6 eindverificatie/PR en afzonderlijke activering.

Actuele code 9769730d6e4a68dda9834c21c384f140e16c75e4 op feature/DEF-835-int02-o2 in .claude/worktrees/DEF-835-int02-o2. Alle CLI-processen afgerond. Geen push/merge/activering/modelproef. Actions blijven uit; actief INT-02 blijft O1.

Lees wp3-tussenoplevering-v1.md voor bewijs, rollen, hashes en concrete grenzen. De acht oude assertions zijn niet opgelost of weggefilterd; geen volledige groene-suiteclaim.
