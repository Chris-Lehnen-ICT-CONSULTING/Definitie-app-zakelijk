# INT-02 O2 — tweede kwalificatieproef gestopt op C107 (v1)

30 september 2026. Chris antwoordde **“probeer het”** op het reeds voorgelegde exacte v2-voorstel. Het afzonderlijke `kwalificatie-akkoord-v2.json` bindt manifest-SHA-256 `99c127bd8a7547d31b8814b0c1abdf587f11e9a8d3e8fdbf6646c528f9233d8e` en de ongewijzigde 43 gevallen met SHA-256 `af1ab46ce22c51308a58738bb7e91534dd67a2b2454c76ee2340e4e2037c6953`. Akkoordbestand SHA-256: `87a210e787606bb69a1c1b11e1ae365d4576fe364ee28f9519faf9542a448149`.

De bestaande Q1-runner werd alleen voor regressie gestart met verhoogde tooltoegang. De nieuw ingestelde projectsleutel was uitsluitend een procesomgevingsvariabele; haar waarde is niet in dit dossier opgeslagen of afgedrukt. Anthropic antwoordde op twee tokenmetingen en twee inferenties met HTTP 200, `claude-opus-5`, `service_tier=standard`, `inference_geo=global`. Dit bewijst dat de v2-route werkte; omdat zowel de sleutel als de uitvoeromgeving ten opzichte van v1 wijzigde, is de afzonderlijke oorzaak van de eerdere verbindingsfout hiermee niet vastgesteld.

## Resultaten en stopregel

| Geval | Bevroren label | Contractstatus | Observatie |
| --- | --- | --- | --- |
| C105 | `fail` | `fail` | Juiste hoofdstatus, geldig citaat; inferentie uitgevoerd. |
| C107 | `review_required` | `error` / `invalid_citation` | Ruwe modeluitvoer zei `fail` en had een onjuist citaatinterval. Het modelantwoord is niet als inhoudelijk oordeel geaccepteerd. |
| C112 | `pass` | niet uitgevoerd | Runner stopte direct na C107. |

Bij C107 gaf de ruwe uitvoer voor het citaat `naar het gemotiveerde oordeel van de beoordelaar voldoende onderbouwd is` `start=14`, `end=85`. Het exacte citaat begint op positie **13** en is 72 codepunten lang; `kern[14:85]` mist de eerste `n`. Hetzelfde ongeldige interval stond in de grondverwijzing. Daarnaast koos de ruwe uitvoer `fail`, zonder vraag en met `uncertainty=none`; dat botst met het vooraf bevroren `review_required` voor onbekende bedoeling zonder beslissende betekenisgrond. Een gerepareerd interval zou die statusfout niet oplossen. Het contract heeft niets gerepareerd en terecht `error` teruggegeven.

De runner noteerde `stopreden=invalid_citation`, `mechanisch_geslaagd=false`, **2 inferenties, 2 tokenmetingen, US$0,05109 conservatief geboekt** en 13,852 seconden totale looptijd. Er waren geen automatische retries. Het grootboek sloot de fase af met `bewijs_opgeslagen=true`; ontwikkeling en hold-out zijn niet gestart. De v2-proefmap wordt niet hergebruikt of overschreven.

Bewijs-SHA-256:

- `kwalificatieproef-v2/grootboek.jsonl`: `6b7dd5a4e744a0c0795740d358dd485a022729ed1fd13282b8ad47e97cfc16e5`;
- `kwalificatieproef-v2/regressie-resultaat.json`: `db8e1e0bbbe47bdd2c1f12bd74c6776cb6c95a1a5b9715953d81003e01faf3a9`;
- `kwalificatieproef-v2/regressie-bundel.json`: `8dfe90e10c2398951a789f168ffcf88de79c02d74fa75a00b30ec79ca1cab0dc`.

De ruwe modelresponsen en volledige synthetische verzoeken staan in de bewaarde bundel. Geen modelkwaliteit, hold-outresultaat of productieactivering is hiermee bewezen. Actions bleven uit; geen push of merge.
