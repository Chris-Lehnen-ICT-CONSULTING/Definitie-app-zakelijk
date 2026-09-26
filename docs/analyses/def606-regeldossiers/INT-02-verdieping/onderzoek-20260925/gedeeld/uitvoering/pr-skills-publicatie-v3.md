## Actuele stand — 26 september 2026, na integratie

Skillcode `5ede20bb4762bc91e20af5d7607417176df6f93d` integreert main `770de55ece429fec826c9d53fd873a109ed8e670`. Beide INT-02/INT-03-teksten blijven behouden. Dezelfde onafhankelijke Codex CLI-reviewer heeft deze integratie goedgekeurd zonder bevindingen; alle 13 leden per lange ZIP zijn bytegelijk aan de getrackte bron. Contract-SHA-256 onveranderd: `bc16c128c43e247b25db996d25059af48fe56dccea5cdc4012ceb401746b043c`.

Gekoppelde geteste appcode: `6a5fc3051eca6605e3e02c2d69f3330fa3deb1ff`. Volledige offline suite: **8594 passed, 67 failed**, exact dezelfde failure-ID’s als de eerdere volledige run. Alle 64 DEF-771- en 367 DEF-772-tests slagen. Geen groene-suiteclaim. Dossier: `vervolg-integratie-eindverificatie-v1.md` en `vervolg-integratie-codex-review-v1.md` in de app-PR.

De CI-workflow is op expliciet verzoek van Chris disabled_manually wegens de GitHub-billingblokkade; geen wijziging aan app-Actions of lokale gates. Dat is geen geslaagde CI-run. De korte aliasbundels bevatten deze INT-02-levering nog niet en actieve skillpublicatie is nog niet uitgevoerd; die volgt een afzonderlijk gecontroleerd voorstel met behoud van INT-03. Geen PR-merge zonder Chris.

---

## Eerdere oplevering — historisch bewijs

# DEF-771 — gedeeld INT-02-contract in beide definitievaardigheden

Gekoppelde levering voor DEF-771. Onafhankelijke review afgerond; de appcorrectie R1 is door dezelfde reviewer gesloten. Geen merge of actieve uitrol.

## Wijziging

- Eén canoniek `references/int02-beslisregel.md` in definitie-toetsregels, met bytegelijke kopie in definitie-nederlandse-definities.
- Contract `def771-int02/2`: brede lokale norm, bronannotatie, veldrollen, exacte G/T, reviewerhulp, statusmapping, H als toelichtingsvoorstel en herleidbare voorbeelden/grensgevallen.
- Beide reference.md-vervangingen en SKILL.md-duidingen volgen synthese §6; geen kwaliteitscijfer of zelfstandige model-/herstel-/poortroute.
- Twee Cowork-ZIP's zijn door de normale commit-hook opnieuw gegenereerd; relevante inhoud is bytegelijk aan de beheerde bron gecontroleerd.

## Besluiten

B1 breed; B2 O1 nu/O2 afzonderlijk; B3 S1-leeshulp; B4 één versiegebonden contract; B5 geen zelfstandige poort (DEF-831); B6 geen betekenisreparatie (DEF-832). De app-PR implementeert de runtimehelft en resultaatcontract 2.2.0.

## Bewijs en rollen

Skillbasis `1e27a2da7668437423af3962cce48af5f1bc591b`, skill-HEAD `750068253a7389e201daedc5b9aa0afd5c0be032`. Contract-SHA-256 van beide kopieën: `bc16c128c43e247b25db996d25059af48fe56dccea5cdc4012ceb401746b043c`.

Appdossier `gedeeld/uitvoering/`: WP1-contracttests RED→GREEN, `wp3-transport-green-v2.log` (146 tests), `wp5-skillpublicatiecontrole.json` (bron/ZIP/actieve kopieën). De volledige app-pytest heeft 8215 geslaagde en 67 gefaalde tests; alle failures ook op basis aangetoond, suite blijft rood. Geen kwaliteitswinstclaim.

Claude Code CLI implementeerde (`a4b588d6-e4a1-4fd6-8f80-0aac55013d90`); afzonderlijke Codex CLI-review afgerond (`01a0dc44-26c6-7de3-b2f9-b0f79e5a27ff`). Geen open inhoudelijke reviewbevinding. Volledige review: wp5-codex-review-v2.md; gerichte R1-herbeoordeling: wp5-codex-review-r1.md. O2 is na afzonderlijk akkoord geregistreerd als [DEF-835](https://linear.app/definitie-app/issue/DEF-835/story-int-02-ai-beoordeling-o2-met-goldset).

Actieve ~/.agents-kopieën zijn gecontroleerd maar nog niet gepubliceerd. Deze PR levert de beheerde bron en bundels; geen actieve uitrolclaim. Geen merge zonder Chris. Geen legacyverwijdering, O2-modelaanroepen, effectmeting, poort of herstelroute.


Gekoppelde app-PR met dossier, review en testbewijs: [Definitie-app-zakelijk #483](https://github.com/Chris-Lehnen-ICT-CONSULTING/Definitie-app-zakelijk/pull/483).
