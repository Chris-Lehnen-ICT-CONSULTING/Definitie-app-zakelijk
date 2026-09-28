# DEF-835 — actuele takenlijst v16

28 september 2026. Actuele ingang na v15. Branch `feature/DEF-835-int02-o2`; technische eindstand `979ca0585100d94b613829d924c6d8bba4f24f1b`. Zie `modelproef-voorbereiding-oplevering-v1.md` voor bewijs en beperkingen.

- [x] WP1–WP3 afgerond; oorspronkelijk 555 gerichte regressietests en onafhankelijke WP3-review.
- [x] Actuele DEF-626/815/835 en bestaande providerroute gecontroleerd.
- [x] Technische proefrunner gebouwd door Claude CLI; standaard offline, exact drie synthetische invoeren voorbereid.
- [x] Onafhankelijke Codex CLI-review: twee fouten gevonden en door dezelfde Claude-uitvoerder gecorrigeerd.
- [x] Correcties met gedragsmatige RED→GREEN bewezen: 34 failed/41 passed → 75 passed.
- [x] Coördinator en dezelfde reviewer bevestigen 75 passed; beide bevindingen gesloten, geen nieuwe bevestigde bevindingen.
- [x] Manifest v2 en transport-/bronbinding gecontroleerd; modelpayloads gelijk aan v1.
- [ ] Concreet proefprofiel/kostenplafond vaststellen — vraag is in deze chat voorgelegd, nog geen antwoord. Bestaand Opus5, maximaal 3 calls, begroot $0,69, voorgesteld plafond US$1. Algemene toestemming voor echte modelcalls bestaat al.
- [ ] Ontvangen akkoord aan manifest v2 koppelen, echte technische proef uitvoeren en rapporteren.
- [x] WP5a concreet voorgesteld: zeven bestanden en optionele API-uitbreiding, zonder activering/opslagwijziging.
- [ ] WP5a-bereik/API accorderen — tweede vraag staat open — en implementeren via Claude CLI.
- [ ] WP4: onafhankelijke goldset/hold-out, inhoudelijke modelkwalificatie en acceptatiegrenzen.
- [ ] WP5 vervolg: gedeelde opslag DEF-626, historisch herladen, UI/export en ketenlogging.
- [ ] WP6: finale verificatie/PR en afzonderlijke activering.

Er loopt geen CLI-proces meer. Er zijn geen open bevestigde runnerbevindingen. De eerstvolgende afhankelijke acties wachten op de twee concreet voorgelegde besluiten; de onafhankelijke voorbereiding is voltooid. Actions blijven uit; niets gepusht, gemergd of geactiveerd. Geen live proef of modelkwaliteitsclaim.
