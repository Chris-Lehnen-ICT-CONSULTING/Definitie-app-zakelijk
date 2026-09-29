# DEF-835 WP2 — RED-rapport van de Claude Code CLI-uitvoerder (v1)

27 september 2026. Rol: Claude Code CLI-uitvoerder, RED-fase. Ik heb geen agents, reviewers of andere CLI-sessies gestart en niets gecommit of gepusht.
Werkboom `.claude/worktrees/DEF-835-int02-o2`, branch `feature/DEF-835-int02-o2`, HEAD `b56e0e225e65eac00ad73239900d2e6c1bfc2422`, ongewijzigd.

## Resultaat RED

Commando, exact zoals opgedragen:
`/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest tests/unit/validation/test_def835_int02_assessment_service.py tests/unit/services/prompts/test_def835_int02_prompt.py -o addopts= -q -ra`

Uitkomst: **158 failed, 3 passed in 2.39s**, exitcode **1**. Er zijn **0 setup-errors en 0 collectiefouten**. Volledige uitvoer en exitcode: `bewijs/wp2-rood-v1.log` (SHA-256 `1b63b538912be31ef2857daf2550919a74ff83e18f4ec0e0ce6aaf5a578d212a`).

Ik heb de faalredenen geteld met een aparte run met `--tb=line`. Die run staat niet in het bewijslog.

| Aantal | Reden | Betekenis |
|---:|---|---|
| 139 | `NotImplementedError` | De stub heeft nog geen dienst, promptbouw of normlader. |
| 18 | `Failed: DID NOT RAISE` | De stub-dataclasses valideren nog niet: 6 × `Modelprofiel`, 11 × `Budget`, 1 × `Int02Norm` met een andere normversie. |
| 1 | `AssertionError` | `T_TEKST` is in de stub leeg en verschilt dus van de T-tekst uit synthese v5 §4. |

Drie tests slagen al. Het zijn invarianten die ook na GREEN moeten blijven gelden:
- `test_taak_is_de_bestaande_routertaak_validation`: `validation` is een bestaande routertaak (`ModelRouter._DEFAULT_CONFIG`, tier critical).
- `test_dienst_wordt_niet_door_de_container_aangemaakt`: `container.py` noemt de dienst niet.
- `test_promptversie_is_eigen_en_verschilt_van_contract_en_norm`: de stub bevat deze constante al.

Ruff 0.15.17 (lokaal) en Ruff 0.16.5 (de hookversie, via `uvx`, offline) geven op de drie bestanden "All checks passed". Black geeft geen wijzigingen meer. Black heeft beide testbestanden eenmalig geformatteerd vóór de RED-run.

## Gewijzigde en nieuwe bestanden

Nieuw, inhoudelijk:
- `src/services/validation/int02_assessment_service.py`: stub van 103 regels, alleen de publieke vorm. SHA-256 `0ee28d80…a3add`.
- `tests/unit/validation/test_def835_int02_assessment_service.py`: 1017 regels. SHA-256 `85827b2e…6a681`.
- `tests/unit/services/prompts/test_def835_int02_prompt.py`: 298 regels. SHA-256 `fb05b19c…e2cc`.

Nieuw, dossier: `bewijs/wp2-rood-v1.log` en dit rapport.

Er is geen bestaand bestand gewijzigd. Het WP1-contract, de INT-03/ESS-03-diensten, de providerlagen, de configuratie, het record, de container en de skills zijn alleen gelezen.

## Gekozen service-API (vastgelegd in de tests)

Modules `services.validation.int02_assessment_service`:

- `PROMPT_VERSION = "def835-int02-prompt/1"` en `TASK_TYPE = "validation"`. De dienst leest beide op het moment van aanroepen uit de module, zodat een wijziging de cache ongeldig maakt.
- `T_TEKST`: letterlijk de T-tekst uit synthese v5 §4, 1999 tekens, zonder inkorting. Een test haalt de tekst uit de synthese en pint de SHA-256 `e6505d50…dee0d1`.
- `Int02ServiceConfigError(ValueError)`: ongeldige dienstconfiguratie.
- `Int02Norm(normversie, uitleg, toelichting, toetsvraag)`, frozen:
  - `normversie` moet `def771-int02/2` zijn (de koppeling met het WP1-contract);
  - `normhash` is een SHA-256 over de normvelden.
- `laad_int02_norm(pad=None)`:
  - leest via de bestaande `lees_regelbestand` uit `src/toetsregels/regels/INT-02.json`;
  - de normversie komt uit het recordveld `contractversie`;
  - een leeg normveld of een andere versie geeft `Int02ServiceConfigError`.
- `Modelprofiel(profiel_id, provider, model, kwalificatie)`, frozen:
  - `kwalificatie` is een expliciete verwijzing naar het profielbesluit;
  - `None` betekent ongekwalificeerd;
  - een lege tekst wordt geweigerd.
- `Budget(max_uitvoertokens, deadline_seconden, max_invoertekens_veld, max_invoertekens_totaal, max_antwoordtekens)`, frozen:
  - de gehele getallen zijn positief en geen `bool`;
  - de deadline is eindig en groter dan 0.
- `bouw_int02_prompt(invoer, norm) -> (systeemprompt, dataprompt)`:
  - de systeemprompt bevat rol, norm uit het record met normversie, de T-tekst letterlijk, gegevens- en offsetregels en het gesloten WP1-JSON-contract met alle velden en enumwaarden;
  - de systeemprompt is onafhankelijk van de invoer;
  - de dataprompt is uitsluitend `json.dumps({"invoer": invoer.als_dict()})`, zonder extra instructie.
- `Int02AssessmentService(ai_service, model_router, *, profiel, budget, norm=None, cache_size=64, klok=time.perf_counter)`:
  - `ai_service` en `model_router` zijn verplicht, anders `Int02ServiceConfigError`;
  - er is geen fallback naar de container of naar `default_model`.
- `await assess(invoer: Int02Invoer, *, correlation_id=None) -> Int02Beoordeling`:
  - een andere invoer dan `Int02Invoer` geeft `Int02ContractError`.
- `Int02Beoordeling`, frozen:
  - `document`: het WP1-`Beoordelingsdocument`;
  - servicemetadata: `reden`, `gecachet`, `promptversie`, `prompt_sha256`, `profiel_id`, `task_type`, `uitzonderingstype`, `stop_reason` en `antwoord_sha256`;
  - `status` en `melding` komen uit het document.

### Volgorde en mapping (WP1 blijft beslissen)

1. Kern of context ontbreekt: `not_evaluated` (NE), zonder AI-aanroep, met `reden="missing_input"`. Dit gaat vóór profiel en budget.
2. Geblokkeerd zonder aanroep. De uitvoering is `Uitvoering(actor="ai", status="not_executed", transportpogingen=0)`. WP1 maakt daarvan `review_required` met reden `not_assessed` en de melding "INT-02 — Nog te beoordelen — beoordeling niet uitgevoerd."; er is geen oordeel. De servicereden is een van:
   - `profile_missing`: de binding krijgt provider en model `unknown`. De routerdefault wordt niet als profiel of kwalificatie gebruikt;
   - `budget_missing`;
   - `profile_unqualified`;
   - `router_unavailable`;
   - `router_mismatch`: `get_model("validation")` wijkt af van het profiel;
   - `input_too_long`: per veld of in totaal;
   - `input_not_encodable`: bijvoorbeeld een los surrogaat.
3. Precies één aanroep, met:
   - `prompt`, `system_prompt`, `task_type="validation"` en `model=profiel.model` (uit het geïnjecteerde profiel, na controle tegen de router);
   - `temperature=0.0`, `max_tokens=budget.max_uitvoertokens` en `timeout_seconds=budget.deadline_seconden`;
   - `use_cache=False`, `max_attempts=1`, `max_retries=0`, `token_estimate="heuristic"` en `offload_postprocessing=True`;
   - `asyncio.timeout(deadline)` rondom de aanroep, plus een meting achteraf.
4. Technische transportfouten worden `Uitvoering(status="failed")` en daarmee in WP1 `error` met de E-melding. Er is geen herstelcall. `CancelledError` wordt niet ingeslikt.

   | Situatie | Contractcategorie | Servicereden |
   |---|---|---|
   | Timeout of te late terugkomst | `timeout` | `timeout` |
   | Rate limit | `transport` | `rate_limit` |
   | Overige `AIServiceError` | `transport` | `connection` |
   | Andere uitzondering | `provider` | `unknown` |
   | Responsmodel ≠ profielmodel | `provider` | `model_mismatch` |
   | Ruwe cache gebruikt (`cached=True`) | `transport` | `raw_cache_used` |

5. Antwoordfouten worden `Uitvoering(status="completed")` met uitvoer `None`, of met de geparste uitvoer. WP1 maakt daar `error` van met `invalid_output` of `invalid_citation`. De servicereden is een van:
   - `truncated_response`: `stop_reason == "max_tokens"`, ook als de JSON toevallig geldig is;
   - `response_too_long`;
   - `malformed_response`: onder meer tekst rond de JSON, twee objecten, een lijst, afgekapte JSON of `NaN`. Precies één omhullend markdown-codeblok wordt aanvaard;
   - `duplicate_keys`: op elk niveau;
   - de WP1-foutcategorie, zoals `invalid_citation` bij C117 of `invalid_output` bij een scoreveld.
6. Een geldige uitvoer gaat ongewijzigd naar `domain.int02.contract.beoordeel`. Structuur, citaten, samenhang, status en melding worden in de dienst niet gedupliceerd.

### Binding en cache

- De `Configuratie` wordt als volgt gevuld:
  - `normhash` en `normversie` uit `Int02Norm`;
  - `promptversie = PROMPT_VERSION`;
  - `provider` en `model` = het gevraagde profiel;
  - `routeringshash` = SHA-256 over `task_type`, de routeruitkomst, het volledige `Modelprofiel` en het volledige `Budget`.

  Zo maakt een wijziging van budget, profiel of kwalificatie een bewaard document historisch, zonder uitbreiding van het WP1-contract.
- De cachesleutel is de volledige WP1-`Binding` plus `prompt_sha256`. Een wijziging van de T-tekst zonder versieverhoging glipt daardoor ook niet door. De cache is een begrensde LRU; bij `cache_size=0` wordt niets gecachet.
- Alleen een resultaat met `uitvoering.status == "completed"`, een geaccepteerd oordeel en een status anders dan `error` wordt gecachet. Fouten, timeouts en blokkades worden nooit gecachet.
- Een cachetreffer geeft hetzelfde, onveranderlijke document terug met `gecachet=True`. De routercheck gaat vóór de cache, zodat een gewijzigde router `router_mismatch` geeft en geen treffer.
- Uitvoeringsmetadata: `tijdstip` (UTC ISO), `duur_ms` (gemeten) en `transportpogingen` (1 + waargenomen herhalingen via de bestaande `_Pogingenteller`). `modelversie`, `invoertokens`, `uitvoertokens` en `kosten` zijn **`unknown`**; zie de beperkingen hieronder.

### Logging

De dienstlogger (`services.validation.int02_assessment_service`) logt bij elke technische fout of blokkade alleen de servicereden, het uitzonderingstype en de correlatie-id. De test eist dat er zo'n waarschuwing is, zodat de controle niet vacuüm is. De test eist ook dat invoer, prompt, antwoord en uitzonderingstekst ontbreken, zowel in de lograpporten als in `repr(resultaat)`, `resultaat.document.als_dict()` en de servicemetadata.

## Onderzochte providerinterface (gelezen, niet gewijzigd)

- **`AIServiceInterface.generate_definition`** (`src/services/interfaces.py:944`). De abstracte signatuur kent alleen `prompt`, `temperature`, `max_tokens`, `model`, `system_prompt` en `timeout_seconds`. `task_type` en de DEF-766-opt-ins bestaan alleen in `AIServiceV2.generate_definition` (`src/services/ai_service_v2.py:154-169`). INT-03 geeft ze ook door (`int03_assessment_service.py:496-512`). Een zuivere ABC-implementatie zonder `**kwargs` zou daarom een `TypeError` geven; de dienst vangt die af als technische fout (`provider`/`unknown`).
- **Doorwerking van de opt-ins, gecontroleerd in de code en in tests op de echte stack:**
  - `use_cache=False` omzeilt de ruwe cache van AIServiceV2 (`ai_service_v2.py:204`, 225-231). AsyncGPTClient krijgt `use_cache=False` (`:247`).
  - `max_attempts=1` begrenst de retrylus van AsyncGPTClient (`src/utils/async_api.py:240-244`).
  - `max_retries=0` reist als enige extra kwarg naar de providerclient (`async_api.py:245-262`). De test controleert `kw == {"max_retries": 0}` aan de netwerkgrens.
  - `stop_reason` reist via `response_hook` mee in `metadata` (`ai_service_v2.py:248-250`, 437-445).
- **`AIGenerationResult.model` is het gevraagde model, niet het gemelde model.** AIServiceV2 zet `model=model_to_use` (`ai_service_v2.py:280-282`). `ChatResponse.model` (`anthropic_client.py:210`: `response.model`) gaat verloren, omdat alleen `stop_reason` uit de respons wordt overgenomen.
- **Een provider ontbreekt in het resultaat.** `AIGenerationResult` heeft geen providerveld (`interfaces.py:901-915`).
- **`ModelRouter.get_model`** (`model_router.py:107-119`). Een onbekende taak valt stil terug op `critical` (`:121-129`). Daarom gebruik ik alleen de bestaande taak `validation`. `active_provider` volgt de configmanager en niet de routerconfig (`:131-139`).
- **Hergebruikte bestaande hulpen**, alleen via import en ongewijzigd: `lees_regelbestand`, `_foutsoort`, `_Pogingenteller` en `_stop_reason` uit `ess03_assessment_service.py`. `parse_modeluitvoer` is **niet** bruikbaar: het gebruikt `json.loads` zonder `object_pairs_hook`, kiest bij dubbele sleutels dus stil de laatste waarde en accepteert `NaN` (`ess03_assessment_service.py:303-321`). WP2 heeft daarom een eigen strikte parser nodig. Dat is geen nieuwe generieke infrastructuur, maar een lokale hulp in de dienst.

## Concrete beperkingen (geen verbreding gedaan)

1. **Gemelde modelversie is niet beschikbaar.** Via AIServiceInterface/AIServiceV2 is de door de provider gemelde modelversie niet zichtbaar. `modelversie` blijft daarom `unknown`; een test pint dit op de echte stack. De modelmismatchcontrole vergelijkt het teruggegeven `AIGenerationResult.model` met het profiel. Bij AIServiceV2 is dat het aangevraagde model, dus die controle vangt vooral afwijkende implementaties. Een echte providerversiecontrole vraagt een wijziging van AIServiceV2 en valt buiten WP2.
2. **Provider van de respons is niet verifieerbaar.** De providercheck beperkt zich tot router ≟ profiel vóór de aanroep. Welke providerclient AIServiceV2 werkelijk gebruikt, is zonder toegang tot het private `_ai_client` niet te zien.
3. **Tokens en kosten zijn onbekend.** AIServiceV2 meldt alleen een geraamd totaal (`tokens_estimated`) en geen verdeling in/uit of kosten. Die velden blijven `unknown`; er worden geen metingen verzonnen.
4. **De bestaande transportlaag logt uitzonderingstekst.** `AsyncGPTClient.chat_completion` logt `f"API call failed: {e!s}"` (`async_api.py:212`) en logt bij herhalingen de fout mee (`:280-282`). Mijn dienst logt geen inhoud en de test controleert alleen de dienstlogger. De bestaande logregel valt buiten mijn bevoegdheid (read-only). Dit is een bestaande beperking en geen WP2-regressie.
5. **Foutcategorieën van het contract zijn beperkt.** WP1 kent voor `failed` alleen `timeout`, `transport` en `provider`. Modelmismatch en ruwe cache vallen daarom onder `provider`/`transport`, met de precieze servicereden als metadata. Het domeincontract is niet uitgebreid.
6. **Blokkades gebruiken de not_executed-melding.** Blokkades vóór de aanroep gebruiken de WP1-route `not_executed`, dus "nog te beoordelen — beoordeling niet uitgevoerd", en niet `error`. WP1 heeft geen categorie voor configuratiefouten. De servicereden maakt het onderscheid.
7. **Offsets berekent het model zelf.** Dat is een bekend kwaliteitsrisico voor echte modellen (C117-achtige `invalid_citation`). De dienst herstelt niets. Meting hoort bij WP4 en de technische smoke.
8. **Geen kwaliteitslabel.** Er is geen kwalificatie of kwaliteitslabel voor een echt model toegekend. Het testprofiel heet `fixture-offline-1` met kwalificatie "testfixture; geen kwaliteitsclaim". Budgetwaarden in de tests zijn fixtures en geen vastgesteld modelbudget.

## Grenzen

- Dit is RED: er is geen GREEN-implementatie.
- Er zijn geen live calls gedaan en er is niets uit `.env` of credentials gelezen.
- De container, het record, het schema, de UI en de opslag zijn niet gewijzigd.
- De testfixtures zijn synthetisch.
- De tests bewijzen contract- en transportgedrag, geen semantische modelkwaliteit.

Stop na RED voor controle door de coördinator.
