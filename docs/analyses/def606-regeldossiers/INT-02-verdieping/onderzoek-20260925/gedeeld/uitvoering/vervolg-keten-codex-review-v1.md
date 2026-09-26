**Het rapport moet inhoudelijk worden aangescherpt voordat het als onderbouwing voor merge/uitrol dient.** Drie bewijsbevindingen; geen nieuwe productiebug vastgesteld.

1. **Important — opslagverlies en algemene exportafwezigheid zijn niet zo bewezen.**  
   [Rapport:22](/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/vervolg-keten-rapport-v1.md:22) en conclusies K1/K2 beschrijven opslag van validatiebewijs. De [proef:97](/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/vervolg-keten-replay-v1.py:97) berekent echter alleen de issues-projectie. Geen schrijfaanroep bewaart vervolgens het validatieresultaat. Herladen en exporteren betreffen dus het oorspronkelijke record zonder validatiebewijs.

   De algemene uitspraken zijn bovendien te ruim: [definitie_crud.py:2245](/Users/chrislehnen/Projecten/Definitie-app/src/database/definitie_crud.py:2245) neemt bij voorsteltoepassing het volledige validatieresultaat op in de registratie; [data_aggregation_service.py:628](/Users/chrislehnen/Projecten/Definitie-app/src/services/data_aggregation_service.py:628) accepteert aangeleverde `toetsresultaten` voor export. Dit is codebewijs van andere routes, geen bewijs dat de volledige INT-02-keten daarmee werkt.

   **Minimale correctie — fix nu:** benoem `bewaarde_issues_int02` als berekende projectie, markeer werkelijk opslaan→teruglezen van validatiebewijs als **niet uitgevoerd**, en beperk exportafwezigheid tot deze JSON-export zonder aangeleverd resultaat. Behoud DEF-626 als bekende open leemte, zonder algemene afwezigheid uit deze proef af te leiden.

2. **Important — de NE-hervalidatievergelijking meet `None == None`.**  
   [Proef:109](/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/vervolg-keten-replay-v1.py:109) vergelijkt uitsluitend `reden` uit `review_required`. Bij C56 is die `None`; de daadwerkelijke NE-melding staat in `deel`. Daardoor kan `opnieuw_gevalideerd_gelijk=true` blijven terwijl de tweede NE-status of melding verandert.

   **Minimale correctie — fix nu:** bewaar de tweede uitkomst en vergelijk minstens `status`, `reden` én `deel`, met de exacte verwachte NE-melding. Zonder herhaling moet het rapport deze vergelijking voor C56 als onbewezen markeren. De eerste validatie en exportgate bevatten wél aantoonbaar de juiste NE-melding; dat bewijs blijft geldig.

3. **Important — de conclusie maakt van functieproeven volledige UI-/poortclaims.**  
   [Rapport:32](/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/vervolg-keten-rapport-v1.md:32) noemt werkende bewerktab- en experttabknoppen en stelt dat INT-02 nergens blokkeert. De proef roept rechtstreeks de orchestrator en renderer aan; `st.button` retourneert altijd `False`. De genoemde knoproutes zijn slechts met broncode vergeleken.

   Voor vaststellen wordt alleen `preview_gate` aangeroepen. Alle drie resultaten bevatten bovendien **“Geen validatieresultaat beschikbaar”**, naast CON-02 en bij C56 CON-01. Er is geen geslaagde INT-02-vaststelling uitgevoerd. Afwezigheid van de tekenreeks `INT-02` bewijst geen algemene causale onafhankelijkheid.

   **Minimale correctie — fix nu:** onderscheid uitgevoerde functies van statische routevergelijking. Formuleer: “De drie previews blokkeren op genoemde bestaande voorwaarden; INT-02 wordt niet als afzonderlijke blokkade genoemd.” B5 blijft het geldige productbesluit; deze proef bewijst geen volledige vaststelroute.

**Wat het bewijs wel draagt**

- De 19 bestaande tests zijn geslaagd, exit 0. Hun CON-01-/exportcontractbewijs vervangt geen INT-02-opslagproef.
- De casusteksten passen bij C83, C105 en C56. De verse resultaten tonen respectievelijk passagehulp, de signaalloze waarschuwing en de exacte NE-contextmelding.
- Opgeslagen synthetische invoer bereikt de echte validatieservice; de opgevangen renderer toont RR via `st.text` en NE via `st.warning`.
- De isolatie is passend: offline-bootstrap vóór appimports, tijdelijke SQLite en geen geïnjecteerde modelservices. Geen aanwijzing voor productiedata- of netwerkgebruik.
- Export zonder gate is uitsluitend een diagnostische route. Het geeft geen toestemming om productgates uit te schakelen.

Het voorstel in [rapport:46](/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/vervolg-keten-rapport-v1.md:46) voor `int02/opslag.py` is **geen vastgesteld vervolgontwerp**. Een regelgebonden opslagoplossing past niet zonder nadere contractafstemming bij DEF-626’s gedeelde, append-only snapshots die atomair met definitieversies worden opgeslagen. Alleen omvangakkoord volstaat daarvoor niet. B5 vraagt geen zelfstandige INT-02-poort. De bekende omvangoverschrijding blijft ongeautoriseerd; deze review keurt haar niet achteraf goed. De twee RUF100-meldingen zijn geen aanvullende inhoudelijke bevinding.

App-HEAD `e9a865b856ca6dba85ee73bedc0e303f05fa86fb`, ongewijzigde productiecode/tests sinds R1 en skill-HEAD `750068253a7389e201daedc5b9aa0afd5c0be032` bevestigd. Alle drie opgegeven bestandshashes kloppen; JSON en gelogde uitvoer zijn gelijk. Reviewsessie: `01a0dc44-26c6-7de3-b2f9-b0f79e5a27ff`.

**Betrouwbare conclusie voor het voorstel:** verse INT-02-validatie en rendereruitvoer werken op herladen synthetische invoer. Opslag en teruglezen van het validatiebewijs, browserbediening en succesvolle vaststelling zijn hiermee niet bewezen. De eerdere implementatiegoedkeuring blijft geldig; het aanvullende rapport is pas bruikbaar na bovenstaande begrenzing en correctie.