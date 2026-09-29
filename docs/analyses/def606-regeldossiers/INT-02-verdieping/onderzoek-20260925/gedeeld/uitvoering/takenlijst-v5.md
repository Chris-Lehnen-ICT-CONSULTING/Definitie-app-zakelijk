# DEF-771 — actuele takenlijst v5

26 september 2026. Deze versie vervangt v4 als actuele ingang. Plan en eerdere bewijsversies blijven bewaard. De opdracht is nog niet afgerond.

## Voorbereiding en besluiten

- [x] V01–V05 — actuele origin/main opgehaald, featurebranch, dossier/Linear/bronnen gecontroleerd en plan gemaakt.
- [x] A01 — plan goedgekeurd.
- [x] A02a — afzonderlijke beheerde skillbranch en gekoppelde PR goedgekeurd; werkboom aanwezig.
- [ ] A02b — actieve skillpublicatie afhandelen; controle heeft verschillen en ontbrekende actieve contracten aangetoond.
- [x] A03–A05 — context_lists, NE-guard, nieuwe C1-replay en CLI-rolverdeling bevestigd.
- [x] A06 — publiek NE-transport en additief resultaatcontract 2.2.0 afzonderlijk goedgekeurd en uitgevoerd (15 bestanden, 865 regels).

## Uitvoering

- [x] W1.1–W1.5 — contract en skillkopie, RED→GREEN, bytegelijkheid en lint. Onafhankelijke review volgt bij WP5.
- [x] W2.1–W2.3 — exacte G, rendering met/zonder voorbeelden, RED→GREEN en lint; 133 regels geaccepteerd.
- [x] W3.1–W3.6 — zes S1-markers geaccordeerd, O1/passagehulp/NE/UI uitgevoerd; 146 tests groen, lint en C1 36/36 op definitieve productiecode.
- [x] W4.1–W4.3 — bestaande tests herijkt zonder gevallen te verwijderen; 437 tests en lint groen.

## WP5 — verificatie en onafhankelijke review

- [x] W5.1a — appbasis/head en skillbasis/head, opdrachten en bewijs vastgelegd; app-HEAD 5fb535ee45671007e5cb4557509560c793eec290, skill-HEAD 750068253a7389e201daedc5b9aa0afd5c0be032.
- [ ] W5.1b — reviewopdracht bij geslaagde herstart actualiseren naar deze HEAD en het eindtestbewijs; oorspronkelijke reviewstart ging uit van d5bf3a0e.
- [ ] W5.2 — onafhankelijke Codex CLI-review: geblokkeerd op 401 Unauthorized, geen inhoudelijk reviewresultaat. Chris gevraagd de CLI-aanmelding te herstellen.
- [ ] W5.3 — eventuele reviewbevindingen via dezelfde Claude-uitvoerder en Codex-reviewer verwerken.
- [x] W5.4a — make test uitgevoerd, drie verouderde versieasserties gecorrigeerd door dezelfde Claude-sessie; 57 relevante tests en lint groen.
- [x] W5.4b — volledige offline pytest uitgevoerd op huidige HEAD: 67 failed, 8212 passed, 114 skipped, 24 xfailed, exit 1.
- [x] W5.4c — iedere failure vastgelegd en op basis gecontroleerd: 66 in de falende selectie, de laatste via twee securitytestbestanden. Zie wp5-testbevindingen-v1.md. De volledige suite blijft rood; dit is geen waiver of algemene regressievrijheidsclaim.
- [x] W5.5a — contractkopieën en Cowork-ZIP-inhoud gecontroleerd; contract-SHA bc16c128c43e247b25db996d25059af48fe56dccea5cdc4012ceb401746b043c.
- [x] W5.5b — actieve skillversies gecontroleerd en verschillen geregistreerd (wp5-skillpublicatiecontrole.json); publicatie is nog open onder A02b.

## WP6 — oplevering

- [ ] W6.1 — app-PR en gekoppelde skill-PR na review; geen merge zonder Chris.
- [ ] W6.2 — Linear-oplevering met uitsluitend bewezen criteria en contract-SHA.
- [x] W6.3a — concreet O2-issuevoorstel voorbereid: o2-vervolgissue-concept-v1.md.
- [ ] W6.3b — afzonderlijk akkoord voor O2-issue ontvangen; nog niet aangemaakt.
- [ ] W6.4 — definitief eindbericht met PR's, CLI-reviewbewijs, tests en vervolgwerk.

Geen actieve modelrun, geen actieve testsessie, geen PR, geen Linear-oplevering, geen skilluitrol en geen merge. Geen bestanden of testgevallen verwijderd. Prompt Forge volgt de geautoriseerde dossierfallback. Volgende noodzakelijke actie: CLI-aanmeldherstel en onafhankelijke review hervatten.
