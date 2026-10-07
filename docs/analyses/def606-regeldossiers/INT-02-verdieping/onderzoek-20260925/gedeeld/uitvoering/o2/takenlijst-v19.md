# DEF-835 — actuele takenlijst v19

28 september 2026. Vervangt v18 als actuele ingang. Branch feature/DEF-835-int02-o2, HEAD 979ca0585100d94b613829d924c6d8bba4f24f1b; huidige wijzigingen zijn nog niet gecommit.

- [x] WP1–WP3 en technische proefrunner geleverd met het eerder vastgelegde bewijs.
- [x] Akkoord voor technische live proef en WP5a ontvangen en gekoppeld aan de concrete voorstellen.
- [x] Live proef uitgevoerd: drie calls, US$0,07814 berekend; C105 verwacht fail, C107 onverwacht fail, C112 error/invalid_citation. Geen modelkwalificatie.
- [x] WP5a door Claude CLI geïmplementeerd: zeven bestanden, O1 blijft actief, 49 initiële nieuwe tests groen.
- [x] Onafhankelijke Codex CLI-review uitgevoerd: F1 context/invoercontract, F2 configuratiebinding en F3 oude teksttest bevestigd.
- [x] F1 via dezelfde Claude CLI gecorrigeerd: negen nieuwe gedragsmatige failures rood, daarna 59 WP5a-tests groen; coördinator 102 tests plus Ruff/Black groen.
- [x] F1 door dezelfde Codex CLI-reviewer gesloten; 53 gerichte tests inclusief O1 groen. Geen nieuwe bevindingen.
- [ ] F2 en F3: gecombineerde uitbreiding naar negen bestanden en publieke configuratielees-API ter akkoord bij Chris. Zie wp5a-reviewcorrectie-uitbreiding-v1.md; omvat de eerdere achtste-bestandsvraag. Nog niet uitvoeren zonder antwoord.
- [ ] Na akkoord F2/F3 door dezelfde uitvoerder corrigeren, bewijs controleren, dezelfde reviewer de delta laten beoordelen.
- [x] Chris heeft uitsluitend de twee exacte metadata-combinaties als scanneruitzondering geaccordeerd, met regressietests.
- [ ] **Nu actief:** Claude CLI voert die scanneruitzondering uit. Opdracht gitleaks-opdracht-claude-v3.md; sessie 5bc9ae88-46e4-489b-9a78-489c125a07bd. Nieuwe canary komt in de vaste Makefile-selectie en het runbook wordt daarmee consistent gemaakt.
- [ ] Scanneruitzondering onafhankelijk reviewen en normaal op de volledige staged index verifiëren; geen bypass of scopeverkleining.
- [ ] Dossiercommit afronden zodra de normale gate slaagt; bestaande 38 staged bestanden blijven intact.
- [ ] WP4: onafhankelijke goldset/hold-out en modelkwalificatie, inclusief concrete C107/C112-problemen.
- [ ] WP5 vervolg: DEF-626-opslag, historie/herladen/C118, UI/export en ketenlogging.
- [ ] Finale verificatie: dertien bestaande mypy-fouten in eigen WP1/WP2-code oplossen of expliciet afhandelen; twee performance_tracker-failures op de basis blijven verklaard door OfflineGateError, geen groene volledige-suiteclaim.
- [ ] WP6: PR/oplevering en afzonderlijke activering na werkelijk bewezen criteria.

Eén actief uitvoeringspakket: de scanneruitzondering. WP5a wacht alleen voor F2/F3 op het concrete uitbreidingsakkoord; F1 is gesloten. Actions blijven uit. Geen push, merge of activering. Het maximum van drie live proefcalls is gebruikt; alle latere tests zijn offline. Laatste gedetailleerde processtatus v9 is aangevuld door wp5a-codex-review-v1.md en wp5a-codex-F1-herreview-v1.md.
