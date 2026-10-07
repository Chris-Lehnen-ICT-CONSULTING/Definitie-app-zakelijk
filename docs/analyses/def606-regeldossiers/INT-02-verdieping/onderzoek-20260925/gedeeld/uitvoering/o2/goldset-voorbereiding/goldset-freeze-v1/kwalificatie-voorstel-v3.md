# INT-02 O2 — voorstel derde, exact gebonden kwalificatieproef

30 september 2026. **Offline voorbereiding voltooid; geen live verzending onder v3.** Chris gaf akkoord op de promptcorrectie en vroeg door te gaan met O2. Het bestaande `kwalificatieprotocol-v1.md` eist daarnaast een apart akkoord op de exacte nieuwe manifest- en gevallenhash vóór iedere live proef.

## Bevroren identiteit

- Nieuw pending manifest `kwalificatie-manifest-v3.json`: SHA-256 **`62d1e3dbfcf19c6a6d4a32971ac27361df7f75b9eb983db7eed2878e4df8fcd1`**; identiteits-SHA-256 `072afdbca056d85f905a8756e6fcdc9a246945f78fa2fce054c341fa4c25357d`.
- Ongewijzigde 43 synthetische gevallen `kwalificatie-gevallen-v1.json`: SHA-256 **`af1ab46ce22c51308a58738bb7e91534dd67a2b2454c76ee2340e4e2037c6953`**. Verdeling: drie bekende regressies, 24 ontwikkeling, 16 afgeschermde hold-out.
- Voorbereide, labelvrije verzoeken `kwalificatie-payloads-v3.json`: SHA-256 `6dc579dc99e7c388959ff8a4b8b18a25306fe07d10a84f75af850d8a57e1a269`.
- Nieuwe proefmap `kwalificatieproef-v3`; v1 en v2 worden niet hergebruikt of gewijzigd. Profiel-ID van de bestaande runner blijft `def835-kwalificatieproef-opus5-v1`; de identiteit bindt nu expliciet **promptversie `def835-int02-prompt/2`** en de gewijzigde bron-SHA-256 `1b7144c5d0e99984dcc4130b40c9c0708ffde16539a2ccf48ccfe5804436b39f`.
- Provider/model: Anthropic `claude-opus-5`, routertaak `validation`; maximaal **43 inferenties, 43 tokenmetingen, 16.000 input- en 6.000 outputtokens per call, 120 seconden per call, 6.000 seconden totaal en US$12 cumulatief** volgens het bestaande protocol. Nul automatische retries, nul fallback, geen productiedata of tools in modelverzoeken. Gebruik uitsluitend de lokaal ingestelde projectsleutel als procesomgevingsvariabele.

De promptwijziging is door de oorspronkelijke Claude CLI-uitvoerder gemaakt, door een afzonderlijke verse Codex CLI-sessie zonder blocker gereviewd en na de definitieve diff offline getest: 5 rood vóór code, daarna 452 groen. Zie `promptcorrectie-testbinding-v1.md` en `promptcorrectie-codex-review-v1.md`. Dit bewijst de nieuwe promptrendering, niet de modelkwaliteit.

## Voorgestelde uitvoering na apart akkoord

Maak een nieuw machineleesbaar akkoordbestand dat precies de twee vetgedrukte hashes hierboven bindt. Start daarna **alleen regressie C105/C107/C112** via de bestaande Q1-runner. Bij een technische/citaatfout of kritieke uitkomst direct stoppen en het grootboek vastleggen. Alleen bij drie juiste hoofdstatussen met geldige citaten volgen 24 ontwikkeling en daarna 16 hold-out onder de reeds vastgelegde gates; geen promptwijziging tussen ontwikkeling en hold-out. De inhoudelijke gronden vraagt het protocol daarna nog aan Chris te beoordelen. Geen activering, Actions-wijziging, push of merge uit dit proefakkoord.
