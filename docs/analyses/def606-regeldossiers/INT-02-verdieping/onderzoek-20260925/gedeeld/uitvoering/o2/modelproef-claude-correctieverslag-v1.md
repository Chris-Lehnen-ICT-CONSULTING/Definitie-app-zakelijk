# DEF-835 — correcties proefrunner na Codex-review, verslag Claude-uitvoerder v1

28 september 2026. Uitvoerder: Claude Code CLI, sessie 57f4b3fa-7776-4a45-bdee-732da1344d2f. Opdracht: `modelproef-opdracht-claude-correctie-v1.md`, op basis van `modelproef-codex-review-v1.md` (P1, P2) en `modelproef-providercontrole-v1.md`.

Er zijn geen echte provider- of modelcalls gedaan en er is geen sleutel gelezen. Productiecode, config, Actions, activering, push en merge zijn niet aangeraakt. Ik heb niets verwijderd of gedelegeerd, en geen akkoordbestand gemaakt.

| Item | Waarde |
|---|---|
| Basis | `dff713fd45a2c87b6d3b646e500e108b5cd61b03` |
| Correctiecommit | **`979ca0585100d94b613829d924c6d8bba4f24f1b`** (alleen de 2 softwarebestanden, normale hooks) |
| Runner | 1106 regels, sha256 `61ce9c5c187faab7e278540060cb2a25fe9017a921ded81fad1ee93e7badfe7a` |
| Tests | 909 regels, sha256 `8d0a6cd76acb79b9ba427f1bff1321a81c9fcc932735fbf15238354a43ab21ea` |
| Nieuw manifest | `bewijs/modelproef-manifest-v2.json`, sha256 `54c75b43b2b55a132e58a896f2d5d909bebf97b521a26ff0d77bb783a0df35c8`, identiteit `74aa689581ad22f79679d4e820a2a27b101e918dad312e974b6f88517d7bd576`, **toestemming pending** |
| Nieuwe payloads | `bewijs/modelproef-payloads-v2.json`, sha256 `3f072eeaa58b3f62a3fc4b1f6b65f32fa5735c92199044bbb798b16763586041`. De payloadhashes per geval zijn gelijk aan v1. |

Manifest v1, payloads v1 en alle eerdere logs blijven staan. Manifest v2 verschilt inhoudelijk op drie punten:
- de nieuwe runnerhash; dit is de enige gewijzigde bronhash, gelijk aan de gecommitte blob;
- de nieuwe identiteitsectie `transport`;
- het nieuwe topveld `controlemomenten`.

Een akkoord op manifest v1 past dus niet op v2. Voor v2 moet `manifest_sha256` gelijk zijn aan `54c75b43…df35c8`. De akkoordvelden zijn verder ongewijzigd.

## Eerlijke TDD-historie

- **Eerste ronde (dff713fd4):** de RED was uitsluitend een collectionfout, omdat de runner nog niet bestond (`modelproef-rood-v1.log`). Er is toen geen gedragsmatige RED bewezen. Dat blijft zo staan.
- **Deze ronde:** gedragsmatige RED op de ongewijzigde runner. `git diff --stat HEAD -- runner` was leeg, dat staat in beide logs.
  - `modelproef-correctie-rood-v1.log`: 34 failed, 41 passed, exit 1. De R1-tests faalden hier op `kostenvariant`, omdat de nieuwe SDK-usagevorm eerder stopte dan de modelcontrole. Daarmee was R1 niet geïsoleerd aangetoond.
  - `modelproef-correctie-rood-v2.log`: R1-test met minimale usage (optionele SDK-velden weggelaten). Weer 34 failed, 41 passed, exit 1. R1 faalt nu op **`assert 3 == 1`**: drie inferenties na een modelafwijking, precies de reviewreproductie.
- **GREEN:** `modelproef-correctie-groen-v1.log`, **75 passed**, exit 0. Het zijn dezelfde tests, de testhash is gelijk aan de gecommitte blob en `-rA` toont elk testresultaat.
- **Lint:** `modelproef-correctie-lint-v1.log`. Black --check, ruff 0.15.17 en `uvx ruff@0.16.5` (hookversie) geven allemaal exit 0.
- **Commit:** `modelproef-correctie-commit-v1.log`. Alle hooks Passed, of Skipped omdat er geen bestanden waren; geen bypass.
- **CLI-dry-run:** `modelproef-correctie-dryrun-v1.log`, zonder sleutel en zonder `.env`.
  - Manifest v2 aangemaakt, exit 0.
  - Reviewreproductie via de CLI: `ANTHROPIC_BASE_URL=https://api.anthropic.com:8443` plus `ANTHROPIC_CUSTOM_HEADERS` met `anthropic-version: 2099-01-01` en `Authorization: Bearer SYNTHETIC-REVIEW` geeft `geweigerd: transportconfig_niet_toegestaan`, exit 2, en er is geen bestand gemaakt.

Commando's (vanuit de werkboom):
- Tests: `env -u ANTHROPIC_API_KEY -u OPENAI_API_KEY DEFINITIE_DISABLE_DOTENV=1 /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest tests/unit/validation/test_def835_int02_modelproef.py -p no:cacheprovider --tb=short -rA`
- Lint: zie de lintlog.

De overige 478 regressietests heb ik niet opnieuw gedraaid. De wijziging zit uitsluitend in de losse runner en het eigen testbestand; er is geen productiecode, config of gedeelde fixture gewijzigd. Ik heb dus geen doorwerking vastgesteld. Er is geen mutatiematrix gedraaid, conform de opdracht.

## R1/P1 — responsemodel niet gebonden

- **Oorzaak.** De waarnemer registreerde `data["model"]` maar vergeleek die niet. `AIServiceV2` geeft het *aangevraagde* model door, dus ook de dienstcontrole zag de afwijking niet. Het gevolg: vervolgcalls, een geaccepteerd WP1-oordeel en Opus-prijzen voor een onbekend model.
- **Fix.**
  - Na een 200-antwoord moet `model` exact gelijk zijn aan `MODEL` (`"claude-opus-5"`). Er is geen prefixmatching en geen aliaslijst.
  - Een afwijkende, ontbrekende, lege of niet-tekstuele ID werkt zo:
    - de in- en uitvoertokens worden zonder prijs geregistreerd;
    - de waarnemer stopt met `model_afwijkend` en werpt een uitzondering. Het antwoord bereikt de keten dus niet: de dienst geeft een WP1-`error` zonder oordeel;
    - het limietslot sluit alle vervolgcalls af.
  - Alleen tekst wordt als `gerapporteerd_model` bewaard; een niet-tekstuele ID wordt `null`.
  - **Kostenonzekerheid is expliciet.** Elke verstuurde inferentie begint met `kosten_usd: null` en krijgt alleen na een betrouwbare boeking een bedrag. Het resultaat bevat `kosten_onzeker` (lijst van geval-ID's), `kosten_usd_bekend_deel`, en `kosten_usd_berekend`. Dat laatste is `null` zodra er één onzekere call is. Dat geldt ook bij een kostenvariant, providerfout, transportfout, afbreking of ontbrekende usage.
- **RED→GREEN.** `test_r1_afwijkend_responsemodel_stopt_zonder_oordeel_of_opus_kosten` met zes varianten: `ander-model`, revisie `claude-opus-5-20260101`, alias `claude-opus-5-latest`, leeg, `123`, ontbrekend.
  - RED v2: `assert 3 == 1`.
  - GREEN: precies 1 telling en 1 inferentie, `stopreden=model_afwijkend`, status `error`, `oordeel` null, `kosten_usd` null, `kosten_usd_berekend` null, `kosten_onzeker == ["C105"]`.
  - De hoofd-ketentest controleert nu ook `kosten_onzeker == []`.
- **Beperking.** Een latere, door Anthropic gemelde revisie- of alias-ID van Opus 5 stopt de proef ook. Zo'n ID moet later expliciet worden beoordeeld en in het profiel vastgelegd.

## R2/P2 — transportconfiguratie buiten de manifestbinding

- **Oorzaak.** `AsyncAnthropic` leest `ANTHROPIC_BASE_URL` en `ANTHROPIC_CUSTOM_HEADERS` uit de omgeving (SDK `_client.py`, constructor). De bestemmingscontrole negeerde poort en gebruikerinfo en keek niet naar headers. De telling kopieerde maar drie headers, waardoor een extra `Authorization` wel bij de inference zat en niet bij de telling.
- **Fix (drie lagen, geen algemeen framework).**
  1. **SDK-configuratie, offline en vóór de sleutel.** Direct na het bouwen van de SDK-client moet gelden:
     - `base_url` is exact `https://api.anthropic.com`, zonder poort, gebruikerinfo, pad, query of fragment;
     - `_custom_headers` en `_custom_query` zijn leeg;
     - `auth_token`, `credentials` en `custom_auth` zijn `None`;
     - `api_key` is exact de doorgegeven sleutel.

     Anders volgt de weigering `transportconfig_niet_toegestaan`. Live doorloopt eerst de dry-run in dezelfde omgeving, dus de weigering valt vóór het lezen van de sleutel en vóór enige verzending. De environment wordt niet gewijzigd en waarden worden niet gelogd.
  2. **Per verzoek.** Op het transport gelden deze eisen:
     - bestemming: POST, HTTPS, host `api.anthropic.com`, standaardpoort, geen gebruikerinfo, pad `/v1/messages`, geen query. Anders `onverwachte_bestemming`.
     - headernamen: alleen de 19 namen die SDK 0.107.1 zonder envopties verstuurt (`SDK_HEADERS`). Aanwezig moeten zijn: `host`, `anthropic-version` en `x-api-key`.
     - vaste waarden: `host`, `anthropic-version: 2023-06-01`, `accept`, `content-type` en `x-stainless-retry-count: 0`. Anders `transport_niet_toegestaan`.

     Na deze controle is `x-api-key` de enige authenticatie. De telling krijgt `x-api-key` en `anthropic-version` identiek mee, en valt onder dezelfde bestemmingsregel.
  3. **Manifestbinding.** Het manifest bevat nu:

     ```
     identiteit.transport = {basis_url, anthropic_version, authenticatie: "x-api-key", headernamen}
     ```

     De headernamen komen uit de werkelijk opgevangen dry-runverzoeken.
- **RED→GREEN.**
  - `test_r2_sdk_transportdrift_weigert_voor_sleutel_en_verzending`, met negen varianten:
    - de reviewreproductie (poort 8443, versie 2099, `Authorization`);
    - alleen poort 8443;
    - gebruikerinfo;
    - `http`;
    - een ander pad;
    - een andere host;
    - een env-versieheader;
    - een env-authheader;
    - een extra env-header.

    In RED liep de run door ("DID NOT RAISE") of werd geweigerd met een andere reden. Andere host, `http` en ander pad gaven al `onverwachte_bestemming`: de oude bestemmingscontrole hield die in de offline dry-run al tegen, vóór het lezen van de sleutel. Poort, gebruikerinfo en de headervarianten liepen wel door. In GREEN volgt overal de weigering `transportconfig_niet_toegestaan`, met 0 verzoeken, sleutel niet gelezen, geen resultaatbestand en geen `SYNTHETIC`/`geheim` in de logs.
  - `test_r2_voorbereiding_weigert_transportdrift`: de voorbereiding weigert en schrijft geen manifest.
  - `test_waarnemer_weigert_niet_toegestaan_verzoek`, nieuwe varianten: poort 8443, gebruikerinfo, `authorization`, API-versie 2099, extra header en afwijkende `host` (plus beta/retry, die nu onder `transport_niet_toegestaan` vallen). RED: "DID NOT RAISE" of een verkeerde reden. GREEN: geweigerd met 0 verzoeken.
  - `test_r2_equivalente_standaardconfiguratie_blijft_toegestaan`: een expliciete `ANTHROPIC_BASE_URL=https://api.anthropic.com`, en `ANTHROPIC_AUTH_TOKEN`, dat de SDK negeert bij een expliciete `api_key`. Beide lopen volledig door, zonder `authorization`. In RED faalden deze alleen door de usagevorm.
  - Hoofd-ketentest: de inference-headers zijn exact de 19 standaardnamen, de telling-headers vormen daar een deelverzameling van, en er is nergens `authorization`.
- **Beperkingen.**
  - De controle leest privé-attributen van de SDK (`_custom_headers`, `_custom_query`). Dat is betrouwbaar voor de gehashte SDK-versie; een andere versie wijzigt de identiteit.
  - De headerallowlist is gebonden aan anthropic 0.107.1. Een SDK-update die een header toevoegt, leidt tot weigering, niet tot stille doorgang.
  - `ANTHROPIC_PROFILE` en federatie-envs worden door de SDK niet gebruikt zolang er een expliciete `api_key` is. De controle op `credentials`/`custom_auth` borgt dat.

## Providercompatibiliteit — usagevorm

- **Oorzaak.** `anthropic/types/usage.py` (SDK 0.107.1) declareert `inference_geo: Optional[str]` en `output_tokens_details: Optional[OutputTokensDetails]` (`thinking_tokens: int`). Volgens de SDK is `output_tokens` het inclusieve, gezaghebbende facturatietotaal. De runner kende beide velden niet en zou daarom na de eerste echte call stoppen.
- **Fix.**
  - Beide velden staan nu in `USAGE_VELDEN`.
  - Een prijs volgt alleen bij alle volgende voorwaarden:
    - `service_tier == "standard"`;
    - `inference_geo == "global"`: standaardprijs volgens de data-residency- en prijsbronnen uit de providercontrole. Een US-only-geo heeft een 1,1×-tarief;
    - `output_tokens_details` is `null`, of precies `{thinking_tokens: int ≥ 0, ≤ output_tokens}`;
    - `cache_creation` en `server_tool_use` zijn `null`, of bevatten alleen hun SDK-subvelden met gehele waarden, allemaal 0;
    - de cache-tokens zijn 0;
    - er is geen onbekend veld.

    Anders volgt `kostenvariant` zonder prijs (`kosten_usd` null).
  - Kosten = `input_tokens × in + output_tokens × uit`. `thinking_tokens` wordt alleen geregistreerd, niet opgeteld.
  - De fake-provider gebruikt nu standaard de actuele SDK-vorm: `cache_creation` met twee nullen, `inference_geo: "global"`, `output_tokens_details: {thinking_tokens: 0}`, `server_tool_use: null`, `service_tier: "standard"`.
- **RED→GREEN.**
  - De hoofd-ketentest en `test_actuele_sdk_usage_details_worden_niet_opgeteld` (met `thinking_tokens: 37`). RED: stop op `kostenvariant` (of `1 == 3`). GREEN: 3 calls, kosten `3 × (1500×$0,000005 + 400×$0,000025)` zonder de details, `thinking_tokens == 37` geregistreerd.
  - Nieuwe stopvarianten in `test_afwijking_stopt_verdere_calls`:
    - geo `us`, `onbekend`, ontbrekend of `null`;
    - details met extra veld, boven het totaal, of geen object;
    - servertool gebruikt;
    - onbekend subveld in `cache_creation`.

    Die stopten in RED ook al, als onbekend veld; ze borgen nu de specifieke vorm. De bestaande varianten `boven-limiet`, `afgekapt` en `ongeldig-citaat` faalden in RED op `kostenvariant` door de nieuwe vorm en zijn in GREEN weer specifiek.
- **Controlemomenten (eerlijk).** Het manifest bevat `controlemomenten`.
  - *Vóór verzending:* SDK-configuratie, bestemming, headers, API-versie, payloadvelden, payloadhash, harde limieten, tokenschatting en budgetreservering.
  - *Pas ná het antwoord:* gerapporteerd model, `service_tier`, `inference_geo`, usagevorm, cache/servertools, tokenlimieten en budget.

  De standaardtier wordt **niet** vooraf in het verzoek gepind: de keten stuurt geen `service_tier` mee en de providerdefault kan volgens de bronnen Priority kiezen. Hetzelfde geldt voor geografie: een workspace-default kan van global afwijken. Afwijkingen stoppen de proef ná de betreffende call; die call kan dan al kosten hebben gemaakt. Die kosten staan als onzeker gemarkeerd, binnen de harde maxima: 3 calls, ≤$0,23 gereserveerd per call.
- **Beperking.** Een ontbrekende `inference_geo` telt als niet aantoonbaar global en stopt de proef. Als Opus 5 het veld live niet meldt, stopt de proef dus na de eerste call. Welke velden de provider werkelijk meldt, blijkt pas live.

## Deadline/cancellation (aanvullend)

- **Oorzaak.** De review kon het deadlinepad niet dynamisch vaststellen. `_verstuur` ving alleen `Exception` af; een afbreking door de deadline (`CancelledError`) werd niet vastgelegd.
- **Fix.** `except BaseException`: het fouttype wordt altijd vastgelegd en daarna opnieuw geworpen. Alleen een gewone `Exception` zet de stopreden `transportfout`. Bij afbreking komt de reden van de dienst (`timeout`).
- **Test.** `test_deadline_breekt_hangende_inferentie_af_zonder_vervolgcall` gebruikt een geïnjecteerde limiet `deadline_seconden=0.05` (eigen manifest/akkoord met die limiet). Een fake-transport hangt (`asyncio.sleep(30)`) en wordt na 0,05 s afgebroken; er zijn geen echte wachttijden of calls.
  - RED: `KeyError: 'fouttype'`.
  - GREEN: klaar in < 5 s, `stopreden=timeout`, 1 telling en 1 inferentie, status `error`, `fouttype=CancelledError`, geen ruwe tekst of sleutel in resultaat of log.

## Open punten voor de herbeoordeling

1. De omvang is verder gegroeid: runner 1106 en tests 909 regels.
2. `kosten_usd_berekend` is nu `null` bij elke onzekere call, ook bij een providerfout die mogelijk niet wordt gefactureerd. Dat is conservatief: `kosten_usd_bekend_deel` blijft beschikbaar.
3. Tier en geo worden alleen na het antwoord gecontroleerd (zie hierboven). Vooraf pinnen vraagt een request-veld dat de bestaande keten niet verstuurt; dat valt buiten deze runner.

## Bronnen

- `modelproef-codex-review-v1.md` (P1 r.5–24, P2 r.26–44, bewijsgrenzen r.64–70); `modelproef-providercontrole-v1.md` (r.5–15)
- Anthropic-SDK 0.107.1: `anthropic/types/usage.py`, `output_tokens_details.py`, `server_tool_usage.py`, `cache_creation.py`; `anthropic/_client.py` (AsyncAnthropic-constructor: `ANTHROPIC_BASE_URL`, `ANTHROPIC_CUSTOM_HEADERS`, credentials, `auth_headers`)
- Offline headeropname van SDK 0.107.1 via `httpx.MockTransport` (19 headernamen, `anthropic-version: 2023-06-01`)
- `src/services/validation/ess03_assessment_service.py` r.807–814 (`_foutsoort`: timeout)
- Bewijs: `bewijs/modelproef-correctie-{rood-v1,rood-v2,groen-v1,lint-v1,commit-v1,dryrun-v1}.log`, `bewijs/modelproef-manifest-v2.json`, `bewijs/modelproef-payloads-v2.json`
