# INT-02 O2 — nieuwe proefidentiteit voorbereid (takenlijst v47)

30 september 2026. Vervangt v46 als procesingang. De oude mislukte run, het akkoord en de goldset blijven ongewijzigd bewaard.

- [x] Chris' algemene akkoord op verbindingsdiagnose en voorbereiding van een nieuw proefmandaat ontvangen.
- [x] Diagnose zonder sleutel of casusinhoud via `curl --head` ook met verhoogde tooltoegang door PreToolUse geweigerd. Beveiligingsinstellingen intact gelaten.
- [x] Anthropic-statuspagina geraadpleegd: API operationeel; lokale oorzaak blijft onbewezen.
- [x] Nieuw pending manifest, nieuwe payloads en nieuwe vrije proefmap offline voorbereid. Alleen de proefmapidentiteit en aanmaaktijd verschillen van v1; de 43 bevroren gevallen en alle inhoudelijke en financiële grenzen zijn gelijk. Voorstel: `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-herstartvoorstel-v1.md`.
- [ ] Chris bevestigt de **nieuwe exacte** manifest-SHA-256 `99c127bd8a7547d31b8814b0c1abdf587f11e9a8d3e8fdbf6646c528f9233d8e` samen met gevallen-SHA-256 `af1ab46ce22c51308a58738bb7e91534dd67a2b2454c76ee2340e4e2037c6953` voor een nieuw akkoordbestand.
- [ ] Na dat akkoord alleen regressie via de bestaande Q1-runner met verhoogde uitvoering proberen. Bij auto-reviewweigering of technische fout stoppen; geen omzeiling van de PreToolUse-regel en geen automatische retry.
- [ ] Alleen bij technisch en inhoudelijk geslaagde regressie ontwikkeling en daarna hold-out uitvoeren; modelkwaliteit en activering afzonderlijk beoordelen.

O2 en Actions blijven uit. Geen codewijziging, push of merge.
