# DEF-622 — tweede versiedelta

Dezelfde reviewer beoordeelde `6b233060f..95396232b`. V2a is gesloten:
verouderde payload wordt geweigerd zonder database-/auditmutatie; oude
expected_version geeft False en ongeldige expected_version wordt afgewezen.

V2b en V2c blijven Important, dispositie **fix nu**:

| Punt | Bewezen resterend gedrag | Gerichte correctie |
|---|---|---|
| V2b | Payloadversies True/1.0 vergelijken gelijk aan 1 en worden opgeslagen; marker 2.0 wordt door een metadata-update van blocked naar geldige integer 3/pass gestempeld. | Dezelfde strikte integercontrole zonder bool/float bij invoer én gecontroleerd overnemen, vóór mutatie. |
| V2c | Generieke updates van score, toelichting, categorie, ufo_categorie en status draft laten de review automatisch meegroeien. | Gecontroleerd behoud begrenzen tot de toegestane atomaire statusactie; geen generieke verlengingsregel. |

Wel bewezen: legitieme opslag→readback→vaststelling→readback blijft consistent,
reviewer A en vaststeller B blijven onderscheiden, stale vaststelling muteert
niets, auditfout rolt status én reviewbinding terug en tekstwijziging invalideert.
Deze garanties behouden; geen brede herwerking van gesloten punten.

Coördinator:85 tests, nul failures/errors/skips, exit 0 op exact snapshot
(`reports/def622/coordinator-version-fix-source.json`, JUnit/log coordinator-version-fix).
Reviewer:490 bytegelijke bestanden en eigen synthetische SQLite-geheugenproeven.
Volledig lokaal resultaat `/private/tmp/DEF-622-codex-version-deltareview-v1-result.md`.

Twee gerichte correcties naar dezelfde Claude; daarna beperkte deltaverificatie.
De zes onafhankelijke koppelingsbevindingen blijven apart gevolgd.
