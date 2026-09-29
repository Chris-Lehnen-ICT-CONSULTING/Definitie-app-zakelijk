# DEF-771 — takenlijst v11: correctie opgeleverd, mergebesluit open

26 september 2026. Actuele ingang; vervangt takenlijst-v10 als voortgangsoverzicht. Volledig bewijs: vervolg-integratie-eindverificatie-v1.md.

- [x] INT-02 geïntegreerd met actuele INT-03/maininhoud, zonder verlies van normteksten.
- [x] Schema-/contractcorrectie B1/B2 uitgevoerd na expliciet akkoord van Chris.
- [x] TDD, gerichte tests, lint en normale hooks gecontroleerd.
- [x] Volledige offline suite: 8594 passed, 67 failed, 114 skipped, 24 xfailed. Exact dezelfde 67 failure-ID’s als de vorige volledige run; alle 64 DEF-771- en 367 DEF-772-tests geslaagd zonder skips.
- [x] Onafhankelijke Codex CLI-review: geen bevestigde bevindingen, B1/B2 gesloten. Beide oorspronkelijke reviews blijven geldig.
- [x] Geteste appcode 6a5fc3051eca6605e3e02c2d69f3330fa3deb1ff, skillcode 5ede20bb4762bc91e20af5d7607417176df6f93d vastgelegd en gepusht. Dossierbewijs in 4e6fb6c1 en e5f8dc786.
- [x] Beide PR-beschrijvingen bijgewerkt en teruggelezen; aanvullend oplevercomment op DEF-771 geplaatst (03605b3f-0d70-48ea-a53f-8feb34bc8a38).
- [x] Mergevoorwaarde vastgesteld: beide PRs conflictvrij; app-Actions repositorybreed uit, terwijl main tien verplichte checks vereist. Skill-PR CLEAN, app-PR BLOCKED. Beide draft.
- [ ] Wacht op Chris: app-Actions inschakelen voor de verplichte checks, expliciete eenmalige beheerdersmerge, of PRs laten staan. Niets gewijzigd aan app-Actions of branchbeveiliging.
- [ ] Daadwerkelijke PR-merge uitvoeren uitsluitend binnen het gekozen akkoord.
- [ ] Actieve skillpublicatie en korte aliasbundels via gecontroleerd publicatievoorstel; huidige bron en lange bundels zijn geverifieerd.
- [ ] Vervolg: gedeelde gewone opslag/herlaadketen DEF-626; O2 DEF-835; effectmeting; overige oorspronkelijke open punten waaronder DEF-830 en CON-01-keuze in DEF-831.

Geen groene-suiteclaim, volledige ketenoplevering, zelfstandige INT-02-poort of herstelroute. Het samengestelde implementatiecriterium van DEF-771 blijft open. Bij bewijslogpublicatie zijn alleen synthetische testwaarden afgeschermd; originals blijven lokaal. De derde logcommitpoging slaagde met alle normale gates. Publicatielog SHA-256: 9133bba225c220316de6452b438196174e46767c681a94fb0dd8b3e307ecef78.
