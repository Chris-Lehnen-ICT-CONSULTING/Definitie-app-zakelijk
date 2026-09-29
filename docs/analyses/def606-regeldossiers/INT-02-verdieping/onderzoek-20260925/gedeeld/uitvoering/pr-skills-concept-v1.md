# DEF-771 — gedeeld INT-02-contract in beide definitievaardigheden

Conceptbeschrijving; onafhankelijke review loopt. Gekoppeld aan de app-PR voor DEF-771; definitieve links en reviewuitkomst volgen bij publicatie.

## Wijziging

- Eén canoniek `references/int02-beslisregel.md` in definitie-toetsregels, met bytegelijke kopie in definitie-nederlandse-definities.
- Contract `def771-int02/2`: brede lokale norm, bronannotatie, veldrollen, exacte G/T, reviewerhulp, statusmapping, H als toelichtingsvoorstel en herleidbare voorbeelden/grensgevallen.
- Beide reference.md-vervangingen en SKILL.md-duidingen volgen synthese §6; geen kwaliteitscijfer of zelfstandige model-/herstel-/poortroute.
- Twee Cowork-ZIP's zijn door de normale commit-hook opnieuw gegenereerd; relevante inhoud is bytegelijk aan de beheerde bron gecontroleerd.

## Besluiten

B1 breed; B2 O1 nu/O2 afzonderlijk; B3 S1-leeshulp; B4 één versiegebonden contract; B5 geen zelfstandige poort (DEF-831); B6 geen betekenisreparatie (DEF-832). De app-PR implementeert de runtimehelft en resultaatcontract 2.2.0.

## Bewijs en rollen

Skillbasis `1e27a2da7668437423af3962cce48af5f1bc591b`, skill-HEAD `750068253a7389e201daedc5b9aa0afd5c0be032`. Contract-SHA-256 van beide kopieën: `bc16c128c43e247b25db996d25059af48fe56dccea5cdc4012ceb401746b043c`.

Appdossier `gedeeld/uitvoering/`: WP1-contracttests RED→GREEN, `wp3-transport-green-v2.log` (146 tests), `wp5-skillpublicatiecontrole.json` (bron/ZIP/actieve kopieën). De volledige app-pytest heeft 8212 geslaagde en 67 gefaalde tests; alle failures ook op basis aangetoond, suite blijft rood. Geen kwaliteitswinstclaim.

Claude Code CLI implementeerde (`a4b588d6-e4a1-4fd6-8f80-0aac55013d90`); afzonderlijke Codex CLI-review loopt (`01a0dc44-26c6-7de3-b2f9-b0f79e5a27ff`). Definitieve reviewuitkomst nog toevoegen.

Actieve ~/.agents-kopieën zijn gecontroleerd maar nog niet gepubliceerd. Deze PR levert de beheerde bron en bundels; geen actieve uitrolclaim. Geen merge zonder Chris. Geen legacyverwijdering, O2-modelaanroepen, effectmeting, poort of herstelroute.
