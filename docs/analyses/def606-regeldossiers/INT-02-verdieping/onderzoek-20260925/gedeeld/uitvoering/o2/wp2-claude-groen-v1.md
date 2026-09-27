# DEF-835 WP2 — GREEN-rapport van de Claude Code CLI-uitvoerder (v1)

27 september 2026. Uitvoerder: Claude Code CLI, sessie `99ef6e30-cc76-445a-932d-8c8bd578b835`, dezelfde sessie als RED. Ik heb geen agents, reviewers of andere CLI-sessies gestart en niets gecommit of gepusht.

Werkboom `.claude/worktrees/DEF-835-int02-o2`, branch `feature/DEF-835-int02-o2`. HEAD is ongewijzigd `b56e0e225e65eac00ad73239900d2e6c1bfc2422`. Opdracht: `wp2-opdracht-claude-groen-v1.md`. API en mapping volgen `wp2-claude-rood-v1.md`.

## Wijzigingsscope

Er zijn alleen drie nieuwe, ongetrackte inhoudelijke bestanden. `git diff --stat` is leeg: geen enkel getrackt bestand is gewijzigd. WP1, INT-03/ESS-03, providerlagen, configuratie, record, container en skills zijn alleen gelezen.

| Bestand | Regels | SHA-256 (definitief) |
|---|---:|---|
| `src/services/validation/int02_assessment_service.py` | 878 | `e2ab9f9aef0fbc536179481b10063373cab4b6adc3d7c22bb2cc630ff5154174` |
| `tests/unit/validation/test_def835_int02_assessment_service.py` | 1085 | `7dd08d1d6400121ffb9ba5a1fa50dab119421b72d26d144bc1b68c5ea7cc89f9` |
| `tests/unit/services/prompts/test_def835_int02_prompt.py` | 315 | `2efcd7ae505a58f2b93731b36fd763c718f073776745e7a28944dc4967426a0b` |

De dienst telt 878 regels. Daarvan zijn ongeveer 120 moduledocumentatie en imports, 34 de letterlijke T-tekst en ongeveer 110 de systeemprompt. De repo-hook `file-size-check` (>500 LOC) waarschuwt alleen (`|| true`). Ik heb de dienst niet opgesplitst: de opdracht staat geen extra bestanden toe.

**De RED-tests zijn inhoudelijk ongewijzigd.** Het deel vóór de GREEN-aanvulling is bytegelijk aan RED: SHA-256 `85827b2e…6a681` en `fb05b19c…e2cc`. Bewijs: `bewijs/wp2-redtests-behoud-v1.log`.

## Aanvullende tests

**Eerst rood.** Zeven tests, bewijs `bewijs/wp2-aanvulling-rood-v1.log`: tegen de ongewijzigde stub `0ee28d80` gaven ze 7 × `NotImplementedError`, exit 1. Ze dekken:
- `Infinity` en `-Infinity` (2 tests);
- een getal boven de cijferlimiet, dat een `ValueError` geeft;
- te diepe nesting, die een `RecursionError` geeft;
- de antwoordgrens, die vóór het parsen geldt;
- het verschil tussen de invoersnapshot en een loglek;
- de norm als snapshot bij constructie.

Alle zeven zijn in GREEN geslaagd, zonder uitzondering naar buiten.

**Na een fix toegevoegd.** Eén prompttest: `test_elke_functiecode_staat_expliciet_bij_zijn_betekenis_uit_t`. Tijdens GREEN vond ik zelf een fout. De functiecodes stonden alfabetisch in de prompt, terwijl de tekst "respectievelijk" in een andere volgorde uitlegde. Daardoor kreeg `actor_prescription` de betekenis "begripscriterium". De koppeling staat nu per code expliciet in `_FUNCTIEBETEKENIS`. Omdat de test pas na de fix is geschreven, heb ik het onderscheidend vermogen aangetoond met een mutatie: criterion en derivation verwisseld. Ongemuteerd slaagt de test (exit 0), met de mutatie faalt hij (exit 1). Bewijs: `bewijs/wp2-functiebetekenis-mutatie-v1.log`.

## Testbewijs

Commando's draaiden vanuit de werkboom met `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest … -o addopts= -q -ra`. De offline conftest was actief; er waren geen liveproviders.

| Log | Inhoud | Uitkomst |
|---|---|---|
| `bewijs/wp2-groen-v2.log` | De twee WP2-testbestanden | **169 passed**, exit 0 |
| `bewijs/wp2-regressie-v2.log` | WP1-contract, INT-02 O1, INT-02-promptnorm, INT-02-skillcontract, INT-03-dienst en -evaluator, ESS-03-dienst/correcties/truncatie, AIServiceV2 batch/routing, DEF-766 opt-ins en eventloop-transport, ModelRouter. `DEF771_SKILLS_ROOT` wijst naar de skillbron uit plan-v1 (read-only). | **434 passed, 0 skipped**, exit 0 |
| `bewijs/wp2-lint-v2.log` | Ruff 0.15.17, Ruff 0.16.5 (hookversie, `UV_OFFLINE=1 uvx`, uit de lokale cache) en Black 26.5.1, uitsluitend op de drie eigen bestanden | alle drie exit 0 |
| `bewijs/wp2-mutatiecontrole-v3.log` | 15 naïeve mutaties op de definitieve bron; daarna bytegelijk hersteld | alle 15 gevangen (exit 1) |

Bij de regressierun had de skillbron `int02-beslisregel.md` SHA-256 `bc16c128…b043c`, gelijk aan plan-v1.

De mutatiecontrole ving onder meer:
- ontbrekende duplicaat- en NaN-detectie;
- het cachen van fouten;
- een ontbrekende antwoordgrens, modelcontrole, routervergelijking, `use_cache=False`, `max_attempts=1` of deadline;
- een uitzonderingstekst in het resultaat;
- NE na een profielblokkade;
- budget buiten de binding;
- het accepteren van een afgekapt antwoord, een ruwe cache of een te late terugkomst.

**Vervangen logs.** Deze logs horen bij een eerdere bronversie en blijven als historie bewaard:
- `wp2-groen-v1.log`, `wp2-regressie-v1.log` (11 skips zonder skillbron), `wp2-lint-v1.log` en `wp2-regressie-skillbron-v1.log`: bron `a0f47770`, vóór de refactor `_controleer_antwoord`;
- `wp2-mutatiecontrole-v1.log` en `-aanvulling-v1.log`: bron `e87a10d6`. In v1 waren M2 en M6 geen naïeve varianten: M6 veranderde niets, en bij M2 hielden andere guards fouten nog uit de cache. Dat is in de aanvulling en in v3 hersteld. De v2-log hoort bij `a0f47770`.

Alle v2/v3-logs vermelden in de kop de definitieve SHA-256 van de drie bestanden.

## Statussen (WP1 beslist)

- Kern of context ontbreekt: `not_evaluated`, zonder aanroep (servicereden `missing_input`). Dit gaat vóór profiel en budget.
- Blokkade vóór transport: `profile_missing`, `budget_missing`, `profile_unqualified`, `router_unavailable`, `router_mismatch`, `input_too_long` of `input_not_encodable`. De uitvoering is `not_executed`, dus `review_required`/`not_assessed` met "Nog te beoordelen — beoordeling niet uitgevoerd". Er is geen modelverdict en `transportpogingen` is 0.
- Transportfout: `failed` en daarmee `error` met de E-melding.

  | Situatie | Contractcategorie | Servicereden |
  |---|---|---|
  | Timeout, ook bij te late terugkomst | `timeout` | `timeout` |
  | Rate limit | `transport` | `rate_limit` |
  | Verbindingsfout | `transport` | `connection` |
  | Ander responsmodel | `provider` | `model_mismatch` |
  | Onbekende uitzondering | `provider` | `unknown` |
  | Ruwe cache gebruikt | `transport` | `raw_cache_used` |

- Antwoordfout: `completed` zonder geldige uitvoer, dus `error` met `invalid_output`. Servicereden: `truncated_response`, `response_too_long`, `malformed_response` of `duplicate_keys`. Een door WP1 afgewezen uitvoer geeft `invalid_output` of `invalid_citation` (C117). `CancelledError` wordt niet ingeslikt.
- Een geldige uitvoer levert de WP1-status `pass`, `fail`, `review_required` (`insufficient_information`) of `not_applicable`. De servicereden is dan `None`.
- De domeincategorieën van WP1 zijn niet gewijzigd; de servicereden is uitsluitend metadata van `Int02Beoordeling`.

## Binding van model, norm, prompt, budget en cache

**Model.** Het gevraagde provider/model komt uitsluitend uit het geïnjecteerde `Modelprofiel`. De router wordt voor `task_type="validation"` vergeleken met dat profiel en moet gelijk zijn. Daarna gaat `model=profiel.model` als gecontroleerde override naar de AI-dienst. Zonder profiel zijn provider en model in de binding `unknown`: de routerdefault wordt nooit als profiel of kwalificatie gebruikt.

**Kwalificatie.** Dat is uitsluitend de meegegeven verwijzing. De dienst kent geen kwalificatie toe. Het testprofiel `fixture-offline-1` ("testfixture; geen kwaliteitsclaim") is alleen een testfixture.

**Norm.** De norm komt letterlijk uit het record INT-02.json via `lees_regelbestand`; de normversie moet `def771-int02/2` zijn. De normhash is een SHA-256 over de vier normvelden. **Levenscyclus:** de norm wordt bij constructie eenmaal gelezen of expliciet geïnjecteerd en is een snapshot voor de levensduur van de instantie. Een wijziging op schijf werkt een bestaande instantie **niet** bij; de test bewijst dat pas een nieuwe instantie de nieuwe norm leest. Automatisch herladen claim ik niet.

**Prompt.** `PROMPT_VERSION` en `T_TEKST` worden bij elke aanroep uit de module gelezen. De cachesleutel bevat ook de SHA-256 van de gerenderde prompt, zodat een tekstwijziging zonder versieverhoging niet langs de cache glipt.

**Routeringshash.** SHA-256 over de taak, de routeruitkomst, het volledige profiel (inclusief kwalificatie) en het volledige budget. Zo maakt een ander budget, profiel of andere kwalificatie een bewaard document `historical` (getest via `toets_actualiteit`). Het WP1-contract is daarvoor niet uitgebreid.

**Cache.**
- De sleutel is de volledige WP1-`Binding` plus de prompthash.
- Het is een begrensde LRU per instantie; bij `cache_size=0` wordt niets gecachet.
- Alleen een `completed` resultaat met een geaccepteerd oordeel en een status anders dan `error` wordt gecachet.
- Een cachetreffer geeft hetzelfde onveranderlijke resultaat terug met `gecachet=True`. De router wordt vóór de cache vergeleken.

**Budget.** `Budget` begrenst uitvoertokens, deadline, invoertekens per veld en in totaal, en antwoordtekens (vóór het parsen). Het is **geen monetair budget**: kosten worden niet gemeten (`kosten = unknown`) en de dienst geeft geen kostengarantie.

## Grenzen van de providerattributie

- `AIServiceV2` geeft in `AIGenerationResult.model` het *aangevraagde* model terug. De controle `model_mismatch` vergelijkt dus alleen de door de AI-dienst gemelde ID met het profiel. **Het is geen attestatie van de echte provider of het echte model.** `ChatResponse.model` van de provider gaat in AIServiceV2 verloren.
- `Uitvoering.modelversie` blijft `unknown`. De test op de echte stack pint dit ook als de fake provider een andere versie meldt.
- De provider van het antwoord is niet verifieerbaar. Ik controleer alleen router ≟ profiel vóór de aanroep.
- `invoertokens`, `uitvoertokens` en `kosten` blijven `unknown`. AIServiceV2 levert alleen een geraamd totaal.
- Gemeten wordt alleen: `tijdstip` (UTC), `duur_ms` (via de geïnjecteerde klok) en `transportpogingen` (1 + herhalingen die de bestaande `_Pogingenteller` waarneemt; bij een blokkade 0).

## Logging

**Wat de dienst en de tests bewijzen.** De dienstlogger `services.validation.int02_assessment_service` logt uitsluitend:
- de servicereden;
- het uitzonderingstype;
- de correlatie-id (in `extra`).

Hij logt nooit invoer, prompt, antwoord of uitzonderingstekst. De logtests eisen dat er per foutpad wél een waarschuwing met de reden is, zodat de controle niet vacuüm is. Ze bewijzen voor vier paden dat de geheime markering niet in bericht of argumenten staat: misvormd antwoord, uitzondering, timeout en fictief citaat.

Een aparte test onderscheidt de **bewust bewaarde invoersnapshot** van een loglek. De exacte kern staat in `document.invoer` en in `als_dict()`, maar niet in de eigen log. Uitzonderingstekst komt nergens in het resultaat terecht, ook niet in `repr` of in het document (getest).

**Resterende loggingrisico's voor de keten** (buiten de drie bestanden, niet gewijzigd):
1. `AsyncGPTClient.chat_completion` logt op ERROR `f"API call failed: {e!s}"` (`src/utils/async_api.py:212`). Bij herhalingen logt het de fout ook op WARNING (`:280-282`), wat met `max_attempts=1` niet voorkomt.
2. AIServiceV2 zet de tekst van de providerfout in de eigen uitzondering, bijvoorbeeld `f"AI API connection error: {e!s}"` (`src/services/ai_service_v2.py:321`), en `_record_api_call` logt op DEBUG een fout met `{e}` (`:152`). De dienst vangt die uitzondering af en logt alleen het type. De bestaande lagen kunnen wel providerfoutteksten in hun eigen logs zetten.
3. `AIServiceV2._cachetreffer` logt `prompt[:50]` op DEBUG (`ai_service_v2.py:359`). Met `use_cache=False` wordt dat pad niet bereikt; getest op de echte stack via twee providercalls bij `cache_size=0`.

Mijn tests controleren alleen de eigen dienstlogger. Voor review en activering moet worden beslist of de transportlaag moet worden gesaneerd; dat valt buiten WP2.

## Resterende beperkingen

- **Geen semantische kwaliteitsclaim.** Het model moet zelf codepoint-offsets en citaten leveren. Een verkeerde positie wordt zonder reparatie `invalid_citation`. Meting hoort bij de technische smoke en WP4.
- **Geen echte smoke uitgevoerd.** Het kostenplafond is gevraagd maar niet beantwoord. De toestemming van Chris voor echte aanroepen staat genoteerd in `akkoord-wp2-v1.md`.
- **ABC-compatibiliteit.** `AIServiceInterface` (ABC) kent `task_type` en de opt-ins niet. Een implementatie zonder `**kwargs` levert een technische fout (`provider`/`unknown`), geen stille pass of fail. De compatibiliteit met `AIServiceV2` + `AsyncGPTClient` is getest met een fake provider aan de netwerkgrens:
  - precies één providercall met `max_retries=0`;
  - geen ruwe cache;
  - `stop_reason` reist mee;
  - bij een verbindingsfout één poging, ondanks een retryconfiguratie van 3.
- **Dienstgrootte.** 878 regels in één bestand, zie de scope hierboven.
- **Niet geactiveerd.** Geen container, evaluator, publiek schema, UI of opslag; dat is WP3+.

Stop na GREEN voor verificatie door de coördinator en de onafhankelijke Codex-review.
