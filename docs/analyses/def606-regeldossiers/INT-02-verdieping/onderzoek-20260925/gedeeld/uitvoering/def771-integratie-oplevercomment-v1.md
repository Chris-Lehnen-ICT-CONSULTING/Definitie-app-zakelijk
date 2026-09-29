## Actuele stand — 26 september 2026, na integratie

Geteste appcode: `6a5fc3051eca6605e3e02c2d69f3330fa3deb1ff`, geïntegreerd met main `076c916671e4e7e9f2843d22669df38eeb79e170`. Skillcode: `5ede20bb4762bc91e20af5d7607417176df6f93d`. Beide gewone mergecommits staan op de featurebranches; geen PR-merge of actieve publicatie.

- INT-02- en INT-03-inhoud samen behouden. B1/B2 op expliciet akkoord opgelost: bestaande INT-03-velden assessment/signals met expliciete typen in contractkandidaat 2.2.0; onbekende velden blijven geweigerd, de brede schematests blijven behouden.
- TDD: 13 failures vóór correctie; daarna 1179 passed, 1 bekende promptfailure, 5 skipped; daarnaast 109 schemaconsumenttests geslaagd. Lint en normale hooks groen.
- Volledige offline pytest: **67 failed, 8594 passed, 114 skipped, 24 xfailed, 3351 warnings, 21 subtests passed in 651.30s; exit 1**. Alle 64 DEF-771- en 367 DEF-772-tests slagen zonder skips. De 67 failure-ID’s zijn exact gelijk aan de eerdere volledige run; oorzaken per failure vastgelegd. Dit is geen groene suite of identieke volledige baselinevergelijking op nieuwe main.
- Dezelfde onafhankelijke Codex CLI-reviewer: geen bevestigde bevindingen; integratie akkoord en B1/B2 gesloten. Eerdere reviews blijven geldig. Aanvullend 26 schema-proeven voor volledig schema én deelschema bevestigd.
- Ketenproef v3 opnieuw groen op geïntegreerde runtime, resultaat bytegelijk: echte CON-02-voorstelregistratie met teruglezen bewezen; gewone opslag/herladen, browser-/vaststelketen en overige exportvarianten niet bewezen.

Actueel dossierbewijs: `vervolg-integratie-eindverificatie-v1.md`, `vervolg-integratie-codex-review-v1.md`, `vervolg-schema-rapport-v1.md`, `vervolg-integratie-failurevergelijking-v1.json`, `vervolg-integratie-pytest-v1.log` en `vervolg-integratie-pytest-publicatie-v1.xml`. De XML-publicatie schermt alleen expliciet verzonnen API-testwaarden af; raw XML blijft lokaal. Volledige prompts staan in de dossiermap; Prompt Forge gebruikt de eerder vastgelegde fallback.

Beide contractkopieën: `def771-int02/2`, SHA-256 `bc16c128c43e247b25db996d25059af48fe56dccea5cdc4012ceb401746b043c`. De twee lange Cowork-bundels zijn bytegelijk aan de beheerde bron. Korte aliasbundels en actieve skillpublicatie volgen afzonderlijk; INT-03-inhoud moet behouden blijven. Skill-CI is op verzoek uitgeschakeld (disabled_manually); geen groene CI-claim.

B1–B6 ongewijzigd. Geen zelfstandige poort (DEF-831), herstelroute (DEF-832), O2-modelproef, effectmeting, DEF-626-implementatie of DEF-830-opruiming. O2-vervolg staat als DEF-835 geregistreerd. Het samengestelde implementatiecriterium van DEF-771 blijft open vanwege actieve publicatie en ketengrenzen. Geen merge zonder Chris.

App-PR: https://github.com/Chris-Lehnen-ICT-CONSULTING/Definitie-app-zakelijk/pull/483
Skill-PR: https://github.com/ChrisLehnen/claude-global-setup/pull/358
