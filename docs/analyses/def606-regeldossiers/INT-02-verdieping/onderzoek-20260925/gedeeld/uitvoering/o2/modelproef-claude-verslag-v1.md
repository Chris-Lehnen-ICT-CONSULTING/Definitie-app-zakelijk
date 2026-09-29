# DEF-835 — technische proefrunner INT-02, verslag Claude-uitvoerder v1

28 september 2026. Uitvoerder: Claude Code CLI (deze sessie), op `modelproef-opdracht-claude-v1.md`. Acceptatiecriteria: `technische-modelproef-voorstel-v1.md`. Ik heb geen echte providercalls gedaan, geen sleutel gelezen en niets gedelegeerd.

| Item | Waarde |
|---|---|
| Werkboom / branch | `.claude/worktrees/DEF-835-int02-o2` / `feature/DEF-835-int02-o2` |
| Basis | `558b50c3f161f819cda6c445f7f81b70888918ac` |
| Commit (alleen de 2 softwarebestanden) | `dff713fd45a2c87b6d3b646e500e108b5cd61b03` |
| Runner | `scripts/analysis/def835_int02_modelproef.py` — 925 regels, sha256 `d131ed34c68f28230fb981655540789789458d0dda334d77417ef9578e563c89` |
| Tests | `tests/unit/validation/test_def835_int02_modelproef.py` — 614 regels, sha256 `46b98cd1966d98fed795604756a3a87dd5027f9a01d27c1e02887d06aad25bc3` |
| Manifest (pending) | `bewijs/modelproef-manifest-v1.json`, sha256 `07b2dce9…1fbb3d`, identiteit_sha256 `ed394821…65b163c` |

Er zijn geen bestaande bestanden gewijzigd of verwijderd. Ook config, Actions, database, dependencies en de app bleven ongemoeid. Er is niet gepusht of gemerged. `bewijs/modelproef-claude-stream-v1.jsonl` bestond al en heb ik niet aangeraakt.

## Ontwerp

- **Keten ongewijzigd.** De keten loopt via `Int02AssessmentService` → `AIServiceV2` (`use_cache=False`, `RateLimitConfig` met 1 poging) → `AsyncGPTClient` → `AnthropicClient` (`max_retries=0`, geïnjecteerde router, `rebind_on_new_loop=False`) → Anthropic-SDK 0.107.1 → httpx 0.28.1. Prompt, parser, WP1-beoordeling en capabilitybeleid zijn die van de bestaande code. De runner dupliceert geen beleid. Voor `thinking`/`temperature` in de payload staat de router aan het roer.
- **Waarnemer aan de httpx-grens.** Dit is de SDK-interceptie. Een `httpx.AsyncBaseTransport` dient als transport van de httpx-client van de SDK. Per verzoek naar `/v1/messages` doet de waarnemer het volgende:
  - Hij controleert bestemming en payload:
    - bestemming: alleen `https://api.anthropic.com/v1/messages`, zonder query;
    - toegestane velden: `model`, `max_tokens`, `messages`, `system`, `thinking`, `temperature`;
    - `model`, `max_tokens` en `thinking` moeten precies `claude-opus-5`, `6000` en afwezig-of-`disabled` zijn;
    - precies één user-bericht;
    - nergens `cache_control`, geen `anthropic-beta` en `x-stainless-retry-count` = 0.
  - Hij bewaakt de harde inferentielimiet. Die wordt geteld vóór verzending, dus mislukte calls tellen mee.
  - Hij vergelijkt de payloadhash met het manifest.
  - Hij doet een provider-tokenmeting op dezelfde inhoud: `model`, `system`, `messages` en `thinking`, met dezelfde `x-api-key` en `anthropic-version`. Ook hier geldt een eigen harde limiet.
  - Hij stopt bij een schatting boven 16.000.
  - Hij reserveert conservatief 16.000×in + 6.000×uit ($0,23 per call) tegen het budget van $1.
  - Hij boekt de gemelde `input_tokens`/`output_tokens`.
- **Injectiepunt.** Productiecode biedt geen publieke route voor een eigen httpx-client. Daarom zet de runner `http_client` in `AnthropicClient._sdk_opties` en bouwt `_client` opnieuw op. Daarna controleert hij `adapter._client._client is http` en `max_retries == 0`. Klopt dat niet, dan volgt de weigering `sdk_interceptie_onbetrouwbaar`. Dit is toegang tot privé-attributen: betrouwbaar voor de vastgelegde SDK- en adapterversie (beide in de identiteit gehasht), maar fragiel bij een wijziging. Die wijziging leidt tot weigering, niet tot stille omzeiling.
- **Router.** De bestaande `ModelRouter` wordt gebouwd op `config/config.yaml` → `model_routing`. Eén afwijking: `active_provider` komt uit die config en niet uit ENV/`ConfigManager`, via een subklasse in de runner. Zo laadt de voorbereiding geen `.env` en geen sleutel. Een ENV-providerwissel (`AI_PROVIDER`) werkt dus niet door in de proef; het profiel pint toch al `anthropic`. Tiers, capabilitybeleid en prijzen blijven van de bestaande router. De dry-run gaf: routeruitkomst `anthropic/claude-opus-5`, `accepts_temperature=False`, `thinking_default_on=True`. De payload bevat dus `thinking: disabled` en geen `temperature`.
- **Voorbereiding (standaard).** De echte keten draait met de waarnemer in dry-runmodus. Die vangt elk verzoek op en verstuurt niets; er is geen binnentransport, dus netwerk is structureel uitgesloten. Het manifest legt vast:
  - profiel (experimenteel, `def815_kwalificatie: false`), limieten, dienstbudget en prijzen uit de router;
  - routeruitkomst en -beleid, normhash en T-teksthash;
  - sha256 van 13 bron- en configbestanden, waaronder de runner zelf;
  - versies van Python, anthropic en httpx;
  - per geval: invoer-, systeemprompt-, dataprompt- en payloadhash.

  Het manifest heeft altijd `toestemming: pending`. De volledige synthetische payloads gaan alleen naar een expliciet opgegeven `--payloads`-bestand.
- **Live.** Een live run vraagt `--live --akkoord --resultaat` en doorloopt deze volgorde:
  1. akkoord valideren;
  2. offline de identiteit herberekenen en exact vergelijken;
  3. pas daarna de sleutel lezen uit de bestaande lokale configuratie (`get_config_manager().api.anthropic_api_key`);
  4. C105, C107 en C112 sequentieel uitvoeren binnen maximaal 600 s totaal. Voor elke call geldt een deadline van 120 s in dienst en SDK.

  De run stopt na het eerste geval met een waarnemer-stopreden of een servicereden: fout, afkapping, citaat, usage, kostenvariant of budget. Een semantisch ander maar WP1-geldig oordeel is een bevinding en leidt niet tot stop of herhaling. Het resultaat bevat per geval:
  - het WP1-document ongewijzigd;
  - aangevraagd en gerapporteerd model;
  - payload- en tel-payloadhash;
  - geschatte en gemelde tokens, berekende kosten, `service_tier`, duur, HTTP-status en `request-id`;
  - fouttype zonder foutbericht.
- **Afscherming.** Monitoring en cache schrijven in een `TemporaryDirectory` als cwd; de chain-modules worden pas daarna geïmporteerd. Tijdens de proef staan deze loggers uit en daarna weer terug: `services.ai.anthropic_client`, `services.ai.base_client`, `services.ai_service_v2`, `utils.async_api` en alle `anthropic`-, `httpx`- en `httpcore`-loggers. Alle uitvoer gaat uitsluitend naar nieuwe bestanden (`open(..., "x")`).

### CLI

```
.venv/bin/python scripts/analysis/def835_int02_modelproef.py --manifest <nieuw.json> [--payloads <nieuw.json>]
.venv/bin/python scripts/analysis/def835_int02_modelproef.py --live --manifest <manifest> --akkoord <akkoord.json> --resultaat <nieuw.json> [--payloads <nieuw.json>]
```

Exitcodes: 0 = voltooid zonder stop, 3 = live gestopt (zie `stopreden`), 2 = geweigerd, bestand bestaat al of argumenten ontbreken.

## Benodigde akkoordvelden (door een mens op te stellen; de runner maakt dit nooit)

Het akkoord is een JSON-object met precies deze velden. Ontbreekt er een of is er een extra veld, dan volgt `akkoord_ongeldig`.

| Veld | Eis |
|---|---|
| `soort` | `"def835-int02-modelproef-akkoord/1"` |
| `manifest_sha256` | sha256 van de exacte bytes van het goedgekeurde manifestbestand (nu `07b2dce9fa2dbd18fd6790d200dac3c4bf138c29db56541b932d668dca1fbb3d`) |
| `profiel_id` | `"def835-technische-proef-opus5-v1"` |
| `experimenteel` | `true` (JSON-boolean) |
| `geen_def815_kwalificatie` | `true` |
| `live_verzending_toegestaan` | `true` |
| `akkoord_door` | niet-lege naam |
| `akkoord_op` | ISO-datum (`JJJJ-MM-DD`) |
| `akkoord_bron` | niet-lege herleidbare verwijzing naar het akkoord |

Het manifest moet `soort` `def835-int02-modelproef-manifest/1` en `toestemming: pending` hebben. Live wordt geweigerd als de herberekende identiteit afwijkt. Dat gebeurt bij elke wijziging van runner, keten, config, norm, fixture of SDK/httpx/Python-versie. Na zo'n wijziging zijn een nieuw manifest en een nieuw akkoord nodig. In de Modelprofiel-kwalificatie van de live run staat `experimenteel:proefakkoord:<sha256 akkoord>:geen-DEF-815`. Die waarde is geen productiekwalificatie. De dry-run gebruikt `experimenteel:dry-run:geen-kwalificatie` en die waarde reist niet mee in de payload.

## Verloop en bewijs (alle bestanden in `bewijs/`)

| Stap | Bestand | Commando (kern) | Exit | Uitkomst |
|---|---|---|---|---|
| RED | `modelproef-rood-v1.log` | `pytest tests/unit/validation/test_def835_int02_modelproef.py` | 2 | Collection-fout: runner bestond niet (TDD-rood op de ontbrekende feature, geen falen per test) |
| 1e groen-poging | (niet bewaard) | idem | 1 | 1 fout in mijn test (C112-antwoord voor C105 → terecht `invalid_citation`). Hersteld met per geval een WP1-geldig afwijkend oordeel. |
| Mutatie v1 | `modelproef-mutatie-v1.py/.log` | 8 tekstmutaties op kopieën buiten de werkboom | 1 | 6/8 gedood. M6 (tellimiet) en M7 (cache_control) overleefden: dat waren echte testgaten. |
| Lint 1 | (terminal) | ruff 0.15.17 | 1 | N818 (exception-suffix), I001/RUF100. Hersteld: `…Error`-namen en `importlib`. |
| Groen | `modelproef-groen-v1.log`, `-v2.log` | idem | 0 | 40 passed. v2 na aanscherping van de tel-verzoekassertie (inhoud + `x-api-key`/`anthropic-version`). |
| Mutatie v2 | `modelproef-mutatie-v2.py/.log` | +M9 SDK-retries aan, +M10 geen scratch-cwd | 0 | 10/10 gedood |
| Lint | `modelproef-lint-v1.log`, `-v2.log` | `black --check`; `ruff` 0.15.17; `uvx ruff@0.16.5` (hookversie) | 0 | schoon |
| Regressie | `modelproef-regressie-v1.log`, `-v2.log` | nieuwe tests + WP1 (`test_def835_int02_contract`), WP2 (`test_def835_int02_assessment_service`), WP3 (`test_def835_int02_evaluator`), Anthropic-client (4 bestanden), `test_def766_ai_route_optins`, `test_ai_service_v2_routing`, `test_ai_clients` | 0 | 518 passed (v2 met samenvattingsregel; v1 is dezelfde set in `-q -q`) |
| Dry-run CLI | `modelproef-dryrun-v1.log` | `env -u ANTHROPIC_API_KEY -u OPENAI_API_KEY DEFINITIE_DISABLE_DOTENV=1 … --manifest …manifest-v1.json --payloads …payloads-v1.json` | 0 | manifest pending. Herhaling op hetzelfde pad: exit 2, hash ongewijzigd. `--live` zonder akkoord: exit 2. Repo-`cache/api_metrics.json` niet aangemaakt; `git status` toont alleen de 2 nieuwe bewijsbestanden. |
| Commit | `modelproef-commit-v1.log` | `git commit -F …` met normale hooks | 0 | alle hooks Passed/Skipped (no files), geen bypass |

Hashes: manifest `07b2dce9fa2dbd18fd6790d200dac3c4bf138c29db56541b932d668dca1fbb3d`, payloads `3befdae8035dbab7dfbb5daf7622c43986cbb0c8073b961b14aae031dc03bc73`, normhash `df1ff9a9…ccf207e`, T-tekst `e6505d50…dee0d1` (gelijk aan de docstring van de dienst). De payloadhashes zijn:

- C105 `e2a8d9a6…fbd4537` (7973 B)
- C107 `c6266a44…c03941d` (8027 B)
- C112 `3d0a2e25…fb80527` (8043 B)

De runnerhash in het manifest is gelijk aan de gecommitte blob.

**Wat de tests bewijzen (offline; sockets geblokkeerd; `httpx.MockTransport` als nep-provider achter de echte SDK):**

- De voorbereiding werkt zonder netwerk of sleutel, is deterministisch en overschrijft niets.
- De payload bevat alleen de invoer van de fixture: geen modelrespons of verwachting, geen tools, cache of stream.
- Een ongeldig akkoord (8 varianten), een gewijzigde identiteit of een ontbrekende sleutel leidt tot weigering vóór enig verzoek of sleutelgebruik.
- De volle keten doet exact tel/inferentie ×3, met exacte usage- en kostenboeking en WP1-statussen fail / review_required / pass. De sleutel staat niet in resultaat of log.
- Een semantisch afwijkend oordeel leidt niet tot stop of herhaling.
- Na 1 call volgt een stop bij: ontbrekende of onvolledige usage, cache-tokens, `priority`, ontbrekende `service_tier`, een onbekend usage-veld, usage boven de limiet, afkapping en een ongeldig citaat.
- Een providerfout (529) of transportfout leidt tot 1 poging, zonder SDK- of appretry, met alleen het fouttype en zonder ruwe tekst in resultaat of log. De loggers staan daarna weer aan.
- Een schatting boven 16.000 geeft 0 inferenties.
- De waarnemer weigert 9 payloadvarianten, een hashmismatch en een budgetreservering boven het budget.
- Inferentie- en tellimiet tellen ook mislukte verzoeken mee.

**Niet bewezen:** het echte providergedrag en de kwaliteit van het model.

## Beperkingen en open bevindingen (ter beoordeling door coördinator/Codex)

1. **Omvang.** Runner 925 plus tests 614 regels, tegen de verwachting van 300–500 in het voorstel. Binnen de verruiming voor INT-02 en binnen twee bestanden, maar duidelijk groter. Ingekort kan worden op de CLI, het payloadbestand en de docstrings.
2. **Fragiel injectiepunt.** Privé-attributen van `AnthropicClient` en `AsyncAnthropic` (zie Ontwerp). Een wijziging daarvan leidt tot weigering, niet tot stille omzeiling.
3. **Strenge usagecontrole (fail-closed).** Een onbekend usage-veld of een ontbrekende of andere `service_tier` dan `standard` stopt de proef ná de eerste call; de kosten van die call zijn dan al gemaakt. Ik heb niet geverifieerd welke usage-velden Opus 5 live meldt; een veld zoals `inference_geo` zou deze stop veroorzaken. De veldnamen worden bewaard in `onbekende_usagevelden`.
4. **Grens van de stop.** Een stop op antwoordniveau (usage, afkapping, citaat) gebeurt inherent ná die call. De harde maxima (3 tellingen, 3 inferenties, ≤$0,69 gereserveerd) blijven gelden.
5. **Niet live geverifieerde aannames.**
   - count_tokens accepteert `thinking: {"type":"disabled"}` en is kosteloos. Dat laatste is door de coördinator geraadpleegd, niet door mij.
   - Het tel-verzoek stuurt alleen `x-api-key`, `anthropic-version` en `user-agent` mee.
   - Tokenmeting blijft een schatting en de berekende kosten zijn geen factuurgarantie.
6. **Monitoringruis in de dry-run.** De opgevangen dry-runverzoeken tellen in de tijdelijke monitoring als mislukte calls. De bestaande monitor print daardoor `ALERT: High Error Rate` naar stdout (zichtbaar in `modelproef-dryrun-v1.log`). Er wordt niets in de repo of productie geschreven. Tijdens de dry-run staat de dienstlogger stil.
7. **Retentie.** De runner verwijdert niets. Over retentie bij de provider doe ik geen uitspraak.

## Bronnen

- `technische-modelproef-voorstel-v1.md`, `modelproef-opdracht-claude-v1.md` (deze dossiermap)
- `src/services/validation/int02_assessment_service.py` (o.a. r.705–771 aanroep met opt-ins, r.888–916 antwoordcontrole)
- `src/services/ai/anthropic_client.py` r.56–80 (`_sdk_opties`), r.120–213 (`chat_completion`)
- `src/services/ai_service_v2.py` r.61–120, r.154–288; `src/utils/async_api.py` r.117–287
- `src/services/ai/model_router.py` r.97–177, r.217–229; `config/config.yaml` `model_routing.capabilities`
- `src/config/config_manager.py` r.422–562 (dotenv/ENV/mappen); `src/utils/cache.py` r.254–255 en `src/monitoring/api_monitor.py` r.203–239 (relatieve paden)
- Anthropic-SDK 0.107.1 `_base_client.py` r.1690–1800 (retrylus, uitzonderingen), `_client.py` r.855 (`copy` hergebruikt `http_client`)
- `tests/fixtures/def835_int02_ontwerpgevallen.json` (C105/C107/C112)
- Bewijsbestanden `bewijs/modelproef-*` (hashes hierboven)
