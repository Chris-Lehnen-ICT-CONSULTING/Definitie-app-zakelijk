# DEF-771 — takenlijst v10: contractcorrectie en eindcontrole

Actuele voortzetting van takenlijst-v9 en processtatus-uitvoering-v7. Chris heeft de schema-/contractcorrectie expliciet goedgekeurd op 26 september 2026; de blokkade wegens ontbrekend akkoord is vervallen.

- [x] INT-02 en actuele INT-03 samen geïntegreerd; conflicten opgelost.
- [x] B1/B2 gecorrigeerd in vijf afgesproken bestanden, zonder nieuwe runtimefunctie.
- [x] RED: 13 failures vóór correctie; daarna vier bestaande fouten en negen nieuwe regressiegevallen groen.
- [x] Brede gerichte selectie: 1179 passed, 1 bekende failure, 5 skipped; aanvullende schemaconsumenten: 109 passed.
- [x] Ruff, Black, make lint en normale commithooks geslaagd.
- [x] Appmergecommit op featurebranch: 6a5fc3051eca6605e3e02c2d69f3330fa3deb1ff.
- [x] Skillmergecommit op featurebranch: 5ede20bb4762bc91e20af5d7607417176df6f93d.
- [ ] Lopend: volledige offline pytest op appmergecommit, seed 20260926; log vervolg-integratie-pytest-v1.log.
- [ ] Lopend: dezelfde onafhankelijke Codex CLI-reviewer controleert integratie en correctie; opdracht vervolg-integratie-reviewopdracht-codex-v1.md.
- [ ] Eventuele concrete nieuwe test-/reviewbevindingen verwerken en gericht verifiëren.
- [ ] Eindbewijs publiceren en bestaande PR-beschrijvingen plus DEF-771 actualiseren.
- [ ] Concreet mergevoorstel aan Chris; daadwerkelijke PR-merges pas na expliciet akkoord.
- [ ] Actieve skillpublicatie en korte aliasbundels via afzonderlijk gecontroleerd publicatievoorstel.

De ketenproef v3 is ongewijzigd groen op de geïntegreerde runtime; de schemacorrectie wijzigt geen uitvoeringsgedrag. Volledige gewone opslag/herladen blijft een gedeeld DEF-626-vraagstuk. O2 staat als DEF-835 geregistreerd; geen modelproef of implementatie gestart. Geen zelfstandige INT-02-poort, herstelroute, legacyverwijdering of effectmeting. Skill-CI blijft op verzoek uit; dat is geen groen CI-bewijs.
