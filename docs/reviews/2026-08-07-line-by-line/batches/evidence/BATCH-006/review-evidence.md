# BATCH-006 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 9/9 blobs, 2.923/2.923 fysieke regels en 123/123 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit de immutable Git-objecten gelezen;
callers en foutpaden zijn gevolgd. Er zijn geen applicatiebestanden gewijzigd.

## Verificatie

- Primaire gecombineerde selectie voor B006/B010: 183 tests geslaagd.
- Onafhankelijke selectie: 160/160 tests geslaagd.
- Ruff: geslaagd. Veilige in-memory ASGI-, mock- en tempfilerepro’s gebruikt.
- Eén extra testbestand kon read-only niet worden verzameld omdat import naar
  `logs/synonym_enrichment.log` schrijft; twee pogingen gaven PermissionError.

## Bewezen bevindingen

### B006-001 — P2 — security-events verdwijnen uit auditrapportage

`src/security/security_middleware.py:97,160-343,509-591` maakt events alleen in
de lokale responslijst en schrijft nooit naar `self.security_events`, terwijl
rapport en export uitsluitend die store lezen. Een geblokkeerde XSS-request gaf
één response-event, maar stored/report/export alle nul. Aanbevolen: ieder event
vóór response centraal registreren in een begrensde thread-safe auditstore en
rapport/export dezelfde bron laten gebruiken.

### B006-002 — P3 — vermoed: ERROR-resultaten mogen tot vijf keer passeren

`security_middleware.py:255-270,318-325` blokkeert pas bij meer dan vijf ERROR-
resultaten. Met de echte validator gaf een request twee required/context-errors
maar `allowed=True`; mocks bevestigden 1 en 5 toegestaan, 6 geblokkeerd. Het
gedrag is bewezen, maar een bestaande test verwacht een contextloze request toe
te staan en het beoogde beleid is niet vastgelegd. Aanbevolen: beleid expliciet
maken; blokkeer iedere ERROR/CRITICAL of herclassificeer severity en tests.

### B006-003 — P3 — muterende feature-API zou gesanitized_data negeren

`src/api/feature_status_api.py:74-115` leest en sanitizet muterende bodies, maar
stuurt de originele Request door. Een in-memory POST-echo ontving de originele
BSN-achtige waarde. De actuele app heeft uitsluitend GET-routes; echte POST gaf
405, dus huidige exposure bestaat niet. Aanbevolen: ASGI-body en Content-Length
correct vervangen, of endpoints uitsluitend gevalideerde `request.state` laten
gebruiken.

### B006-004 — P2 — sanitizerlevels worden lexicografisch vergeleken

`src/validation/sanitizer.py:361-364` vergelijkt enum-stringwaarden. Daardoor is
`"moderate" <= "permissive"` waar en werd BSN al op PERMISSIVE geredigeerd.
Aanbevolen: expliciete numerieke rangorde met parametrische leveltests.

### B006-005 — P2 — geldige e-mail wordt verwijderd, ongeldige invoer behouden

`sanitizer.py:291-300` gebruikt een geldige-emailregex als vervangpatroon met
lege replacement. `user@example.com` werd `""`, terwijl `not-an-email`
ongewijzigd bleef. Aanbevolen: geldigheid met `fullmatch` controleren en geldige
waarden behouden; valideer/rapporteer ongeldige input volgens expliciet contract.

### B006-006 — P2 — nested dictionaries in lijsten verliezen hun datatype

`sanitizer.py:471-477` recurseert niet als dictionary in een lijst voorkomt. Een
geneste dict werd een stringrepresentatie met gedeeltelijke redactie. Aanbevolen:
type-preserverende recursieve traversal voor dictionaries en lijsten, met tests
voor willekeurige nesting.

### B006-007 — P2 — endpoint-rate-limiters besmetten elkaars configuratie

`src/utils/smart_rate_limiter.py:220-251,526-557` en
`integrated_resilience.py:137-147,197-215` gebruiken voor iedere limiter hetzelfde
`cache/rate_limit_history.json`. Limiter A schreef rate 7.0; limiter B met
config 2.0 startte op 7.0. Aanbevolen: history per endpoint/config namespacen,
waarden valideren/begrenzen en atomair opslaan.

### B006-008 — P3 — gepubliceerde queue-time blijft altijd nul

`smart_rate_limiter.py:334-413,487-502` bewaart timestamps, maar
`_update_queue_stats()` heeft geen caller. Na één echt queued en processed
request was `total_processed=1` en `avg_queue_time=0.0`. Aanbevolen: wachttijd
bij `popleft()` berekenen en de statistiek vóór future-completion bijwerken.

## Afgewezen of niet ingediende observaties

- De decorator/securityschemamap heeft geen productiecaller en is niet als
  actuele exploitclaim gerapporteerd.
- Ongebruikte exportpad- en SecurityService-configobservaties zijn niet als
  bewezen productfinding ingediend.

### B006-009 — P3 — Alle data-afhankelijke feature-status-GET-routes retourneren 500 doordat hun enige JSON-bron ontbreekt

**Bewijs:** get_feature_status construeert uitsluitend docs/architectuur/feature-status.json en opent dit bestand; de immutable tree bevat het niet. Verse TestClient-repro gaf 500 voor /api/feature-status, /summary, /epic/E-1 en /by-status/complete. Met gemockte geldige JSON waren de respectieve happy paths 200, een ontbrekende epic 404 en ongeldige status 400. De updater/workflow schrijft alleen ARCHITECTURE_VISUALIZATION_DETAILED.html en genereert het JSON-bestand niet. De FastAPI-module heeft een eigen __main__-entrypoint, maar geen verdere productiecaller werd gevonden.

**Reproductie:** Start de immutable FastAPI-app via TestClient met lege modulecache en GET de vier data-afhankelijke routes; observeer vier 500-responses met FileNotFoundError in de serverlog. Patch uitsluitend de file-read met een geldige epics-fixture en herhaal voor 200/404/400.

**Aanbevolen oplossing:** Maak één werkelijk gegenereerde/gepackageerde canonieke statusbron en laat workflow en API hetzelfde artefactcontract gebruiken. Valideer het schema bij startup, geef 503 bij ontbrekende dependency en voeg ongepatchte packaged-artifact/TestClient-happy-pathtests toe.

## Niet getest

- Echte muterende FastAPI-route, externe credentials/netwerk en productiebelasting.
- Visueel contrast, keyboard, screenreader, touch en responsive viewports; de
  batch bevat geen primaire Streamlit-view.
