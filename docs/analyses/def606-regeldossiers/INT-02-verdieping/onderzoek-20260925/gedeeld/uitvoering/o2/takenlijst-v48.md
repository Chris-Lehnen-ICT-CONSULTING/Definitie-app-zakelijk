# INT-02 O2 — verlopen API-sleutel gemeld (takenlijst v48)

30 september 2026. Vervangt v47 als procesingang. Goldset, v1-foutbewijs en het pending v2-manifest blijven ongewijzigd.

- [x] Chris' mededeling vastgelegd dat de bestaande Anthropic API-sleutel verlopen is; zie `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-sleutelstatus-v1.md`.
- [x] Onderscheid vastgelegd tussen die mededeling en de runnerlog (`connection` zonder HTTP-status). Geen onbewezen 401-claim.
- [ ] Chris vervangt de sleutel veilig in de bestaande lokale projectconfiguratie en meldt alleen dat dit gelukt is; geen sleutel in chat of dossier.
- [ ] Chris bevestigt het nieuwe exacte v2-manifest (SHA-256 `99c127bd8a7547d31b8814b0c1abdf587f11e9a8d3e8fdbf6646c528f9233d8e`) en de ongewijzigde 43 gevallen (SHA-256 `af1ab46ce22c51308a58738bb7e91534dd67a2b2454c76ee2340e4e2037c6953`). De Q1-runner eist dit aparte akkoordbestand.
- [ ] Daarna regressie C105/C107/C112 met de bestaande runner uitvoeren; bij fout stoppen. Ontwikkeling en hold-out alleen na geslaagde eerdere fase.
- [ ] Modelkwaliteit, appintegratie en eventuele activering afzonderlijk afhandelen.

Geen nieuwe API-poging, codewijziging, push of merge. O2 en Actions blijven uit.
