# INT-02 O2 — nieuwe sleutel lokaal zichtbaar (takenlijst v49)

30 september 2026. Vervangt v48 als procesingang. Goldset, mislukte v1-proef en pending v2-manifest blijven ongewijzigd.

- [x] Chris meldde de API-sleutel lokaal te hebben vervangen.
- [x] Veilig gecontroleerd zonder sleutelinhoud te tonen: de vingerafdruk van `ANTHROPIC_API_KEY` in de project-`.env` veranderde; er is in de huidige shell geen procesvariabele die haar overschrijft. Een nieuw proces met de normale `ConfigManager` leest dezelfde nieuwe vingerafdruk. Dit bewijst nog geen geldige API-authenticatie of verbinding.
- [ ] Een al draaiende lokale app herstarten zodat zij de nieuwe sleutel leest.
- [ ] Chris bevestigt het nieuwe exacte v2-manifest (SHA-256 `99c127bd8a7547d31b8814b0c1abdf587f11e9a8d3e8fdbf6646c528f9233d8e`) en de ongewijzigde 43 gevallen (SHA-256 `af1ab46ce22c51308a58738bb7e91534dd67a2b2454c76ee2340e4e2037c6953`) voor het door de Q1-runner vereiste aparte akkoordbestand.
- [ ] Daarna eerst alleen regressie C105/C107/C112 onder de bestaande stopregels; ontwikkeling en hold-out alleen bij slagen.
- [ ] Modelkwaliteit, appintegratie en activering afzonderlijk afhandelen.

Geen nieuwe API-aanroep, codewijziging, push of merge. O2 en Actions blijven uit.
