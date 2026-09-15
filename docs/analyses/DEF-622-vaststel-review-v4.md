# DEF-622 — derde gerichte versiedelta

Dezelfde onafhankelijke reviewer beoordeelde `e9739635e..dc1b12fc3`. V2c is gesloten voor geldige integerbindingen: generieke metadata-/tekst-/statusupdates verlengen de review niet; legitieme vaststelling, afzonderlijke actors, expected_version en auditrollback werken. Bool/float-payloads worden geweigerd; malformed markers worden niet langer geldig herstempeld.

V2b blijft open met twee Important-restpunten:

1. Ontbrekende/null payloadversie wordt bij `set_context_review` alsnog gestempeld; expected_version wordt wel onder lock gecontroleerd. Dit voldoet niet aan de opgedragen strikte payloadversie-eis.
2. Opgeslagen marker `version_number="2"` bij recordversie 2 passeert de gate, maar de strikte carry weigert de tekstversie. Handmatige vaststelling kan slagen, waarna readback op recordversie3 de review blokkeert. Gate en carry hanteren verschillende typeconventies.

Na drie gerichte herstelpogingen stopt dit herstelpad volgens AGENTS.md (maximaal drie pogingen per actie). Geen vierde automatische fix of review. Dit is geen waiver en geen gesloten acceptatiepunt; opnemen als blokkerend restpunt in de reviewbare draft. Onafhankelijk export-/AppTest-/kwaliteitswerk gaat door.

Bewijs: coördinator107 tests, nul failures/errors/skips, exit0 op `/private/tmp/DEF622-strict-version-hsgwovda`. Bronbinding `reports/def622/coordinator-strict-version-source.json`, JUnit `.xml`, log `coordinator-strict-version-v2.log`. Eerste onjuiste testpadpoging exit4 afzonderlijk bewaard in `coordinator-strict-version.log`. Reviewer heeft490 bytegelijke bron/configbestanden en eigen geheugenproeven gebruikt; reviewexec19782 exit0. Volledig resultaat lokaal `/private/tmp/DEF-622-codex-strict-version-deltareview-v1-result.md`.
