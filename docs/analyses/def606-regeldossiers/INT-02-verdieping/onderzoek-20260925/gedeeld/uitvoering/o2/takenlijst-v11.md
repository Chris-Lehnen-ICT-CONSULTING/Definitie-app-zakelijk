# DEF-835 — actuele takenlijst v11

28 september 2026. Actuele ingang; v10 en eerdere versies blijven bewijs.

- [x] WP1 en offline WP2 afgerond, code 48a6b3fa5.
- [x] WP3-contract en negen bestanden expliciet akkoord van Chris.
- [x] Nulmeting 55 geslaagd; Claude/Codex beschikbaar en aangemeld.
- [x] RED: 92 failed, 19 passed; geen collectie-/setupfouten.
- [x] GREEN: 111 passed, met bytegelijke WP3-testbestanden.
- [x] Negen bestanden lokaal vastgelegd in d3fc53eaed14e6a303605146b7e5f8b9ea3cef5e; normale commitgates geslaagd.
- [x] Coördinatorverificatie: 539 passed, 8 failed in 2.63s, exit 1. Alle failures door bestaande oude contractassertions, volledig bewaard.
- [ ] Chris: voorstel wp3-scopeaanvulling-tests-v1.md voor vijf extra testbestanden goedkeuren. Vraag staat open; bestanden niet gewijzigd.
- [ ] Onafhankelijke review loopt: Codex CLI gpt-6-astra/high, sessie 01a0e4f2-9a94-70b2-9dcd-87202e24b697, aparte werkroot /private/tmp/def835-wp2-review-20260927.
- [ ] Eventuele reviewcorrecties door dezelfde Claude CLI-sessie c75abf0d-3c01-4c02-a672-536d75daa15a, gevolgd door gerichte herreview.
- [ ] WP3 definitief opleveren: pas na review en afhandeling van de bestaande contracttests.
- [ ] Technische echte modelproef: toestemming aanwezig, profiel/kostenplafond open.
- [ ] WP4 goldset/hold-out en inhoudelijke modelevaluatie.
- [ ] WP5 appintegratie en gedeelde opslag, inclusief ModularValidationService-boekhouding en ketenlogging.
- [ ] WP6 eindverificatie/PR en afzonderlijke activering.

Werkboom .claude/worktrees/DEF-835-int02-o2; branch feature/DEF-835-int02-o2; WP3-basis 2be81c577653f8efbab6fa2c3794598556d32d13. Geen push/merge/activering. Actions blijven uit; actief INT-02 blijft O1. Geen appmodelcalls gedaan.

Brede unitrun door Claude: 8395 passed, 10 failed, 86 skipped, 1 xfailed, 1 collectie-error. Acht failures zijn de bekende oude assertions. Twee andere failures betreffen database-isolatie; Claude rapporteert gelijk gedrag op basis-HEAD. De collectie-error kwam bij een commando zonder importlibmodus. Dit is geen volledige groene-suiteclaim. Mijn gerichte 547-testcontrole gebruikt wel importlib en geeft alleen de acht bekende failures.

Bewijs: wp3-claude-rood-verslag-v1.md, wp3-claude-groen-verslag-v1.md, bewijs/wp3-coordinator-verificatie-v1.log. De vijf aanvullende testcorrecties zijn nog niet uitgevoerd. De implementatie binnen negen bestanden is gereed voor review, WP3 als geheel nog niet afgerond.
