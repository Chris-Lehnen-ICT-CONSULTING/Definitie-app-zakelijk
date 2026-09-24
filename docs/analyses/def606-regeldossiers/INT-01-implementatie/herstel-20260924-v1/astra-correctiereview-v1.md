**Geen appvrijgave: R1 en R2 blijven gedeeltelijk open, beide Important / fix-nu.** De oorspronkelijke voorbeelden zijn gecorrigeerd, maar directe tegenhangers reproduceren dezelfde foutcategorieën.

1. **R1 — infinitief wordt nog als bewezen persoonsvorm behandeld.**  
   [zinsgrenzen.py:543](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:543) sluit bepaalde beginwoorden uit, maar bewijst daarmee geen onderwerp. Regel 551 accepteert vervolgens `worden` zodra er niet direct `te` voor staat.

   Rechtstreeks gereproduceerd:
   - `regeling. toegepast worden` → **fail**.
   - `regeling. uitsluitend worden toegepast` → **fail**.

   Beide vervolgen missen een bewezen eigen onderwerp en persoonsvorm. De melding claimt toch een zelfstandige tweede zin. **Herstel:** behandel niet-herkende constructies en ambigu infinitiefgebruik als onzeker; afwezigheid in de uitzonderingslijst is geen positief bewijs. Leg beide tegenhangers vast en behoud de positieve T24-controle.

2. **R2 — ontbreken van zinsbewijs wordt ten onrechte bewijs voor doorlopende tekst.**  
   [zinsgrenzen.py:390](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:390) combineert een negatieve onderwerpcheck met een voorzetselbegin of vermeend open bijzin.

   Rechtstreeks gereproduceerd:
   - `code met de melding “Gereed.” voor gebruik is controle vereist` → **zinsstructuur pass**, geen grens. Het voorzetselbegin verhindert herkenning van de zelfstandige vervolgzin met inversie.
   - `code die eindigt met de melding “Gereed.” de controle volgt later` → eveneens **zinsstructuur pass**. [Regel 406](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:406) mist `eindigt`; de vervolgcheck mist `volgt`.

   Dit concretiseert de beperking uit herstelanalyse-v3. **Herstel:** onderscheid bewezen voortzetting van onbekende syntaxis. Beide gevallen moeten minstens onzeker blijven, met passage en positie. Behoud de geldige voortzettingen `… “Gereed.” toont` en `… “Gereed.” op het scherm`.

Wel bevestigd: de oorspronkelijke R1/R2-repro’s lopen nu correct via onzekerheid; hun bewijsposities wijzen naar de punt. T24 behoudt één zekere en één onzekere grens. De gecontroleerde interne citaten en geldige citaatvoortzettingen blijven beschermd; compactheid en begrijpelijkheid blijven afzonderlijk open.

**Skills en distributie: geen zelfstandige bevinding.** De twee referenties sluiten aan op het bedoelde contract: betekenisbehoud, citaatnuance, uitsluitend deelclaims, `/2` en geen automatische hertoetsing bij herladen. Beide canonieke zips volgen de bronbytes; beide aliaszips volgen de bestaande naamrewrites en `.skill`-uitsluiting. Geen installatie uitgevoerd; ALG-391-freeze blijft intact.

Bewijs hergebruikt: zeven RED-failures, gerichte groene tests, **7147 passed** in `r2-make-test-v1.log`, groene lint en **94 bundeltests**. Zelf twaalf schrijfvrije segmentatieproeven, bundelvergelijkingen en hashcontroles uitgevoerd; geen brede suite herhaald.

Beide manifests en alle bestandshashes kloppen vóór en na review; geen drift:

| Pakket | Basis | SHA256 diff |
|---|---|---|
| App volledig | `ee13ae1d7ce05482bd61f37dd51099b7ba8d23f0` | `123d64265fb59263df748c8e94d04c25477e90ea34f308ec346acbf6ec6952cc` |
| Appcorrectie tegenover v1 | vorig reviewmanifest | `3c7db9e378e44e7dc28120852b4a4381930a47dc64395d4ff3ebc08a07b30297` |
| Skills | `16b773de8a5a94ad2c8da9468b05f58086917baa` | `7b921398034e6da6c79079afd9aaccdc6b202c8ac56e591a74053698228529bb` |

Geen wijzigingen, extra reviewers of betaalde calls. De nieuwe onafhankelijke eindproef moet nog volgen; geen effectwinst vastgesteld.