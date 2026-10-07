# DEF-835 — actuele takenlijst v20

28 september 2026. Vervangt v19 als actuele ingang. Branch `feature/DEF-835-int02-o2`, HEAD `d769276041e619103ace7bc66e65419d480dae99`.

- [x] Technische proefrunner en eerder WP1–WP3-bewijs vastgelegd.
- [x] Geaccordeerde live proef uitgevoerd: drie calls, US$0,07814 berekend. C105 verwacht fail; C107 onverwacht fail; C112 error/invalid_citation. Geen geslaagde modelkwalificatie.
- [x] WP5a door Claude CLI geïmplementeerd: zeven bestanden, O1 actief, aanvankelijk 49 nieuwe tests groen.
- [x] Onafhankelijke Codex CLI-review: F1 context/invoercontract, F2 configuratiebinding, F3 oude teksttest bevestigd.
- [x] F1 door dezelfde Claude CLI gecorrigeerd en dezelfde Codex CLI-reviewer gesloten. Coördinator: 102 tests plus Ruff/Black groen; reviewer: 53 gerichte tests groen.
- [ ] **Nog akkoord nodig:** gecombineerd voorstel `wp5a-reviewcorrectie-uitbreiding-v1.md` voor F2/F3: twee extra bestanden, totaal negen, plus publieke configuratiesnapshot-API. Omvat de eerdere achtste-bestandsvraag. Nog geen antwoord ontvangen.
- [ ] Na akkoord: dezelfde uitvoerder corrigeert F2/F3, dezelfde reviewer beoordeelt de delta; geen nieuwe modelcalls nodig.
- [x] Exacte scanneruitzondering geaccordeerd door Chris en geïmplementeerd door Claude CLI.
- [x] Scannerpakket onafhankelijk gereviewd; twee kleine bevindingen A/B door dezelfde uitvoerder gecorrigeerd en dezelfde reviewer gesloten. Uiteindelijke scope vijf bestanden; uitzonderingsbereik niet verruimd.
- [x] Bewijs scanner: eerste volledige vaste suite 105 geslaagd; na gerichte correctie 35 betrokken tests en lint groen bij uitvoerder en coördinator; twee zelfscantests groen bij herreview.
- [x] Gewone commitcontrole geslaagd, inclusief Gitleaks. Commit `d76927604` bevat vijf scannerbestanden en alle 38 oorspronkelijk staged dossierbestanden. Geen hookbypass of scanverkleining. Index nu leeg.
- [x] Na commit geverifieerd: vijf gecommitteerde hashes exact gelijk aan de review; alle zeven WP5a-bestanden onveranderd, nog ongestaged. INT-02 blijft `judgment_review` (O1).
- [x] GitHub Actions opnieuw alleen-lezen gecontroleerd: `enabled=false`, exit 0. Geen push, merge of activering.
- [ ] WP4: onafhankelijke goldset/hold-out en inhoudelijke modelkwalificatie, inclusief C107/C112.
- [ ] WP5 vervolg: DEF-626-opslag, historie/herladen/C118, UI/export en ketenlogging.
- [ ] Finale type-/testpoort: dertien mypy-fouten in eigen WP1/WP2-code blijven open. Twee performance_tracker-fouten bestaan ook op de basis en ontstaan door OfflineGateError op het productiedbpad. Geen groene volledige-appsuiteclaim.
- [ ] WP6: PR/oplevering en afzonderlijke activering na bewezen criteria.

Geen CLI-processen meer actief. De recente WP5a-code en nieuwe uitvoeringsdocumenten/bewijsbestanden staan lokaal in deze werkboom; zij zijn nog niet allemaal gecommit. Het opgeloste commitblok betrof de oorspronkelijke 38 staged dossierbestanden. De beperkte lokale commit is geen verklaring dat O2 klaar of modelgekwalificeerd is.

Detail: `processtatus-uitvoering-v10.md`. De tweede, gecombineerde akkoordvraag is de relevante vervolgbeslissing; één akkoord daarop dekt zowel F2 als F3. Actions blijven uit.
