# DEF-771 — eindverificatie na integratie en contractcorrectie

26 september 2026. Geteste en onafhankelijk beoordeelde appcode: **6a5fc3051eca6605e3e02c2d69f3330fa3deb1ff**. Skills: **5ede20bb4762bc91e20af5d7607417176df6f93d**. Beide zijn gewone mergecommits op de featurebranch; er is geen PR-merge naar main of actieve uitrol uitgevoerd. De getrackte werkbomen waren na de volledige run ongewijzigd.

## Volledige suite — letterlijk resultaat

Commando: `DEF771_SKILLS_ROOT=/Users/chrislehnen/Projecten/_claude-global-setup/.worktrees/DEF-771-int02-skills/skills .venv/bin/pytest --randomly-seed=20260926 --tb=short --junitxml=docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/vervolg-integratie-pytest-v1.xml`. De bestaande offline-bootstrap is actief; geen productiedata of live modelaanroep. Volledige uitvoer: vervolg-integratie-pytest-v1.log.

```text
67 failed, 8594 passed, 114 skipped, 24 xfailed, 3351 warnings, 21 subtests passed in 651.30s (0:10:51)
EXITSTATUS=1
```

De XML bevat alle **64 DEF-771-gevallen en 367 DEF-772-gevallen geslaagd**, zonder failures of skips. De aanvullende negen DEF-771-gevallen bewijzen de contractcorrectie samen met INT-03.

De coördinator vergeleek alle failure-ID's met de eerdere volledige run op 9ff3eac1: exact dezelfde 67, geen nieuwe of verdwenen ID. Actuele melding per failure: vervolg-integratie-failurevergelijking-v1.json. De oorzaken en eerder uitgevoerde basisproeven staan per failure in wp5-testbevindingen-v1.md. De afwijkende meldingen betreffen tijdelijke paden/objectadressen, gemeten looptijden en totalen van onderzochte bronbestanden/functies; de aantallen ontbrekende init-bestanden en documentatiebevindingen bleven gelijk. Dit is geen identieke volledige run op de nieuwe mainbasis en geen algemene regressievrijheidsclaim. **De volledige suite blijft rood.**

De originele XML blijft lokaal behouden. Voor publicatie zijn uitsluitend de expliciet verzonnen API-testwaarden uit de bestaande DEF-583-fixture afgeschermd in vervolg-integratie-pytest-publicatie-v1.xml. Metadata en hashes: vervolg-integratie-publicatieredactie-v1.json. Suite-attributen en testgevalaantallen zijn gelijk.

## Integratie, TDD en onafhankelijke review

- Nieuwe INT-02-G en INT-03-G letterlijk behouden; overige maininhoud blijft aanwezig. Beide skillcontracten blijven bytegelijk, versie def771-int02/2, SHA-256 **bc16c128c43e247b25db996d25059af48fe56dccea5cdc4012ceb401746b043c**.
- B1/B2 op expliciet akkoord gecorrigeerd in vijf bestanden: de nog niet gemergde contractkandidaat 2.2.0 beschrijft ook de bestaande INT-03-velden assessment/signals met expliciete typen; alleen voor INT-03 toegestaan. Brede schematests en afwijzing van onbekende velden behouden.
- RED vóór correctie: 13 failed, 31 passed. Daarna brede selectie: 1179 passed, 1 bekende promptfailure, 5 skipped. Alle vier contractfailures en negen nieuwe regressiegevallen groen. Aanvullend 109 schemaconsumenttests geslaagd. Zie vervolg-schema-rapport-v1.md en de bijbehorende logs.
- Ruff, Black, make lint en normale commithooks geslaagd. Geen hook of test afgezwakt.
- De geïntegreerde runtime levert in de ongewijzigde ketenproef v3 exact dezelfde JSON: drie casussen, twee routes, exit 0. De schema-/typingcorrectie verandert dit uitvoeringsgedrag niet.
- Claude Code CLI implementeerde/corrigeerde: a4b588d6-e4a1-4fd6-8f80-0aac55013d90. Onafhankelijke Codex CLI-review: 01a0dc44-26c6-7de3-b2f9-b0f79e5a27ff. Volledige opdrachten opgeslagen in vervolg-integratie-opdracht-claude-v1.md, vervolg-schema-opdracht-claude-v1.md en vervolg-integratie-reviewopdracht-codex-v1.md. Prompt Forge: eerder vastgelegde dossierfallback.
- Review vervolg-integratie-codex-review-v1.md: **geen bevestigde bevindingen, B1/B2 gesloten**. Onder meer 26 onafhankelijke schema-proeven voor volledig schema én deelschema geslaagd (vervolg-integratie-reviewproeven-v1.log). Review beoordeelde dezelfde code; de volledige suite liep toen nog. De coördinator heeft het uiteindelijke resultaat hierboven afzonderlijk gecontroleerd. Geen extra inhoudelijke reviewronde nodig zonder nieuwe bronwijziging of bevinding.

## Opleverbereik en vervolg

De O1-basis met contract, G, O1-passagehulp, S1, NE-doorgifte en bestaande UI-weergave is op de actuele maininhoud geïntegreerd en binnen het afgesproken bereik geverifieerd. De oorspronkelijke B1–B6 blijven ongewijzigd. Beide lange Cowork-bundels bevatten alle 13 getrackte skillbestanden bytegelijk. De korte aliasbundels vertegenwoordigen deze nieuwe INT-02-levering nog niet; actieve skillpublicatie volgt een afzonderlijk gecontroleerd voorstel dat de actuele INT-03-inhoud behoudt.

Geen volledige actieve ketenoplevering: gewone opslag/herladen (DEF-626), browser-/vaststelketen en overige exportvarianten zijn niet bewezen. De echte voorstelregistratie en expliciet meegegeven JSON-toetsresultaten zijn wel beperkt onderzocht; zie het gesloten ketenrapport v3. Het samengestelde implementatiecriterium van DEF-771 blijft daarom open.

O2 is geautoriseerd geregistreerd als DEF-835; geen modelproef gestart. Effectmeting, DEF-626, DEF-830, de CON-01-keuze in DEF-831 en overige oorspronkelijke grenzen blijven open. Geen zelfstandige INT-02-poort (DEF-831), geen herstelroute (DEF-832), geen legacyverwijdering. Skill-CI is op verzoek disabled_manually; dat is geen geslaagde CI-run. PR-merge en actieve publicatie vragen nog afzonderlijk akkoord van Chris.
