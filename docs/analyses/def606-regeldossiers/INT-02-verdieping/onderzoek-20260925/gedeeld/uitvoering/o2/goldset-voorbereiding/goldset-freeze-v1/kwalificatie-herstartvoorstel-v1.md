# INT-02 O2 — nieuwe, begrensde kwalificatieproef (voorstel v1)

30 september 2026. Chris antwoordde **“ok akkoord”** op het vaststellen van de verbindingsfout en voorbereiden van een nieuw, exact gebonden proefmandaat. Dit document legt het concrete nieuwe manifest voor; **nog geen akkoord op de nieuwe SHA-256 en geen tweede live proef**.

## Identiteit en bereik

- Bevroren 43 gevallen: `kwalificatie-gevallen-v1.json`, SHA-256 `af1ab46ce22c51308a58738bb7e91534dd67a2b2454c76ee2340e4e2037c6953`. De 40 nieuwe gevalobjecten, hoofdlabels en 24/16-splitsing zijn ongewijzigd.
- Nieuw pending manifest: `kwalificatie-manifest-v2.json`, SHA-256 `99c127bd8a7547d31b8814b0c1abdf587f11e9a8d3e8fdbf6646c528f9233d8e`; identiteits-SHA-256 `fd61c138ff0037cb393f51f6e0edb58688fbde5e8be5bc1449ec899648fa88f7`.
- Nieuwe voorbereide payloads: `kwalificatie-payloads-v2.json`, SHA-256 `d0c5ef43880f6325749b2f10dd09ee069a71fe83ce8374205a9b7b52ba9cd2d0`. 43 gevallen, zonder goldlabelveld.
- Nieuwe en nog niet bestaande proefmap: `kwalificatieproef-v2`. De oude `kwalificatieproef-v1` met mislukte tokenmeting blijft ongewijzigd.
- Vergeleken met v1 zijn in het manifest alleen `aangemaakt`, `identiteit_sha256` en de identiteit verschillend; **binnen de identiteit verschilt alleen het pad van de nieuwe proefmap**. Model, prompt, norm, router, prijzen, payloadhashes, 43-callgrens en US$12-plafond zijn gelijk.

## Verbindingsdiagnose en route

De eerste proef faalde tijdens de C105-tokenmeting met `connection` / `AIServiceError`: nul inferenties. Ook met verhoogde tooltoegang weigerde de lokale PreToolUse-hook een credentialvrije `curl --head` naar `api.anthropic.com` wegens mogelijk exfiltratierisico. Deze beveiligingsregel is niet gewijzigd. De officiële Anthropic-statuspagina meldde op 30 september 2026 `Claude API (api.anthropic.com) Operational` en geen incident die dag (https://status.claude.com/); dit is geen bewijs van de lokale verbinding.

Bij apart akkoord op de twee exacte hashes hierboven is de voorgestelde volgende stap: de **bestaande Q1-applicatierunner** voor uitsluitend regressie C105/C107/C112 via de ondersteunde verhoogde uitvoering starten, met de bestaande projectsleutel alleen als procesomgevingsvariabele. De runner houdt zijn eigen 43-call-/43-tokenmeting-/US$12-grenzen, nul retries en stopregels. De aparte auto-review kan de verhoogde uitvoering weigeren; dan stopt het traject zonder netwerkproef. Een tweede verbindingfout beëindigt dit nieuwe manifest eveneens; geen derde proef op eigen initiatief.

Een akkoord op dit voorstel is geen goedkeuring voor O2-activering, Actions, push of merge. Ontwikkeling en hold-out volgen alleen als de regressiefase inhoudelijk én technisch slaagt.
