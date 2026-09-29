# DEF-835 WP2 — correcties na de onafhankelijke review (v1)

27 september 2026. Claude Code CLI-uitvoerder, sessie `99ef6e30-cc76-445a-932d-8c8bd578b835`. Ik heb geen agents, reviewers of andere CLI-sessies gestart, niets gecommit of gepusht en geen livecalls gedaan.

Werkboom `.claude/worktrees/DEF-835-int02-o2`, branch `feature/DEF-835-int02-o2`, HEAD `0e336c6c4b40fd53d4a1ef3c2283f6a99691510f`, ongewijzigd.

Bron: `wp2-codex-review-v1.md`, drie P2-bevindingen, dispositie "fix nu". De tegenproef `probe-v2.py`/`uitvoer-v2.log` heb ik alleen gelezen.

## Scope

Gewijzigd, ten opzichte van HEAD:

| Bestand | Wijziging | SHA-256 |
|---|---|---|
| `src/services/validation/int02_assessment_service.py` | 926 regels (was 878) | `e2ab9f9a…54174` → **`dda9d274e3b7a93973f9df0bc3de0b422fe4d96d1766beb536162914a68c049e`** |
| `tests/unit/validation/test_def835_int02_assessment_service.py` | 60 → 70 testfuncties, geen verwijderd | `7dd08d1d…c89f9` → **`ca82cce18816e1f5b714678a5234596a536abb26ee202d56437d94a5173a0c1b`** |
| `tests/unit/services/prompts/test_def835_int02_prompt.py` | ongewijzigd | `2efcd7ae…6a0b` |

Niet gewijzigd: WP1, adapters en backend (`openai_client.py`, `anthropic_client.py`, `ai_service_v2.py`, `async_api.py` en de ESS-03-helpers), configuratie, record, UI, evaluator en dependencies. `git diff --stat` noemt alleen de dienst en het servicetestbestand.

Nieuw in het dossier:
- `bewijs/wp2-correcties-rood-v1.log` (SHA-256 `04a22d53…e691`)
- `bewijs/wp2-correcties-groen-v1.log` (`b478354c…b4ec`)
- `bewijs/wp2-correcties-lint-v1.log` (`c0ac3c1a…fcd2f`)
- dit rapport

## TDD-verloop

**RED** (`wp2-correcties-rood-v1.log`): de ongewijzigde dienst (`e2ab9f9a`) met de definitieve tests (`ca82cce1`) geeft **19 failed, 167 passed**, exit 1. Het zijn 17 nieuwe regressietests en de 2 herijkte assertions. Per test heb ik gecontroleerd dat hij om de bedoelde reden faalt:
- F1: `'fail' == 'error'`, dus een afgekapt of onbevestigd antwoord werd een oordeel;
- F2: `gecachet True is False`, gelijke binding, of een aanroep waar een blokkade hoorde;
- F3: `1 == 'unknown'`.

Tussen RED en GREEN zijn de tests niet meer gewijzigd.

**GREEN** (`wp2-correcties-groen-v1.log`), dienst `dda9d274`, tests ongewijzigd:

| Run | Resultaat |
|---|---|
| 1: WP2-testset (beide bestanden) | **186 passed**, exit 0 |
| 2: regressie (WP1-contract, INT-02 O1, INT-02-promptnorm, INT-02-skillcontract, INT-03-dienst/evaluator, ESS-03-dienst/correcties/truncatie, AIServiceV2 batch/routing, DEF-766 opt-ins en eventloop-transport, ModelRouter) | **434 passed, 0 skipped**, exit 0 |

Bij run 2 wees `DEF771_SKILLS_ROOT` naar de skillbron uit plan-v1 (read-only; `int02-beslisregel.md` SHA-256 `bc16c128…`).

**Lint** (`wp2-correcties-lint-v1.log`), alleen op de drie eigen bestanden: Ruff 0.15.17, Ruff 0.16.5 (hookversie, `UV_OFFLINE=1 uvx`, uit de lokale cache) en Black 26.5.1, alle drie exit 0. Zoals opgedragen heb ik geen brede mutatiecampagne gedraaid.

## F1 — een afgekapt antwoord werd een oordeel

**Oorzaak.** De dienst weigerde alleen `stop_reason == "max_tokens"`. De bestaande OpenAI-adapter (`src/services/ai/openai_client.py:129-141`) zet `finish_reason` niet in `ChatResponse.stop_reason`. Contractueel geldig JSON uit een afgekapt OpenAI-antwoord werd daardoor een inhoudelijk oordeel en gecachet.

**Wijziging.** Er is een witte lijst in `_controleer_antwoord`:
- `_AFGEROND = {"end_turn", "stop"}` (Anthropic en OpenAI) laat het antwoord door naar parse en WP1;
- `_AFGEKAPT = {"max_tokens", "length"}` geeft `truncated_response`;
- elke andere of ontbrekende reden geeft de nieuwe servicereden `unconfirmed_completion`.

Beide uitkomsten zijn `completed` zonder uitvoer, dus WP1 maakt er `error`/`invalid_output` van. Een error wordt nooit gecachet. Er is geen proxy via tokenraming of modelnaam.

**Regressietests:**
- ontbrekende stopreden: error, en niet gecachet (twee aanroepen);
- `refusal`, `pause_turn`, `tool_use` en een onbekende reden: `unconfirmed_completion`;
- `length`: `truncated_response`;
- **de echte `OpenAIClient` + echte `AIServiceV2`**, met alleen de SDK aan de netwerkgrens als fake:
  - SDK-respons met `finish_reason="length"` en geldig JSON: `error`, reden `unconfirmed_completion`, twee SDK-calls zonder cachetreffer;
  - `finish_reason="stop"`: óók `unconfirmed_completion`. Dit pint de beperking vast.

**Herijkte fixtures.** `FakeAI` en `_Provider` melden nu standaard `stop_reason="end_turn"`, zoals de Anthropic-adapter doorgeeft (`anthropic_client.py:212`). `FakeAI(stop_reason=None)` laat de reden weg, zoals de OpenAI-adapter. Geen testgeval is afgezwakt: alle bestaande foutpaden testen onveranderd hun eigen fout.

**Resterende beperking.** De huidige OpenAI-route kan **geen enkel inhoudelijk O2-oordeel** opleveren zolang de adapter `finish_reason` niet doorgeeft. Dat vraagt een backendwijziging in `openai_client.py` en een afzonderlijk scopebesluit. Verder is de witte lijst gebaseerd op de huidige stopredenen van beide providers. Een nieuwe providerreden die wél een afgerond antwoord betekent, wordt tot een bewuste aanvulling geweigerd: fail-closed.

## F2 — het capability-beleid ontbrak in de binding

**Oorzaak.** De routeringshash bevatte de routeruitkomst, het profiel en het budget, maar niet het capability-beleid. Dat beleid bepaalt in de bestaande Anthropic-adapter (`anthropic_client.py:215-250`, `_verzendbeleid`) of `temperature` en `thinking` worden meegestuurd. Bij hetzelfde provider/model konden de gewijzigde verzendparameters daardoor langs de cache en de WP1-replay glippen.

**Wijziging.**
- `_route()` vraagt bij de **geïnjecteerde** router de bestaande publieke functies `accepts_temperature(model, provider=…)` en `thinking_default_on(model, provider=…)` op (`model_router.py:217-229`).
- Het resultaat (`_Route.beleid`) gaat als `"beleid"` mee in de routeringshash. Zo verandert de WP1-`Binding`, en daarmee de cachesleutel én de replay. Het publieke resultaatcontract is niet gewijzigd.
- Een ontbrekende functie, een uitzondering of een niet-booleaanse uitkomst geeft een blokkade vóór de aanroep met de nieuwe servicereden `router_policy_unavailable` (`not_executed`, 0 pogingen). Er is geen verzonnen default en alleen het uitzonderingstype wordt vastgelegd.

**Herijkte fixture.** `FakeRouter` heeft nu dezelfde publieke vorm als `ModelRouter` (`accepts_temperature`, `thinking_default_on`), met instelbaar beleid en een instelbare beleidsfout.

**Regressietests:**
- **echte `ModelRouter`** met capabilities voor het gerouteerde model, plus de **echte `AnthropicClient._verzendbeleid`** als bewijs dat het verzendbeleid werkelijk verandert. Bij hetzelfde provider/model is er na de beleidswijziging geen cachetreffer (twee aanroepen). Een **nieuwe dienstinstantie** levert een andere binding, en `toets_actualiteit` verklaart het oude document `historical`;
- `temperature` en `thinking` veranderen elk afzonderlijk de binding;
- beleidsfout, niet-bool (`"ja"`, `None`) en een router zonder beleidsfuncties: geblokkeerd, zonder aanroep, en de fouttekst staat niet in log of resultaat.

**Resterende beperkingen.**
1. De binding legt het beleid van de **geïnjecteerde** router vast. De `AnthropicClient` gebruikt zijn eigen router: een expliciet geïnjecteerde, of per aanroep `ModelRouter.from_config()` (`anthropic_client.py:105-118`). Dat de adapter hetzelfde beleid toepast, is alleen gegarandeerd als beide uit dezelfde configuratie komen. Er is geen attestatie van het werkelijk verzonden beleid.
2. De `OpenAIClient` gebruikt de capability-policy niet en stuurt altijd `temperature` mee. Een beleidswijziging maakt daar een oordeel onnodig historisch. Dat is conservatief, niet onveilig.

## F3 — een transportpoging werd gerapporteerd zonder providercall

**Oorzaak.** `transportpogingen` kwam uit `_Pogingenteller.attributie()["attempts_observed"]` (`ess03_assessment_service.py:800-804`). Die waarde begint altijd bij 1, ook als er geen providercall is geweest, bijvoorbeeld bij een timeout tijdens het wachten op de semaphore.

**Wijziging.** De dienst gebruikt de teller niet meer; de helper zelf is in de backendlaag ongewijzigd gebleven. Na een (poging tot) aanroep is `transportpogingen = "unknown"`, omdat de AI-interface het aantal niet meldt. Alleen bij een blokkade vóór transport, waarbij vaststaat dat er geen aanroep is geweest, blijft het `0`.

**Regressietests:**
- **echte `AIServiceV2`/`AsyncGPTClient`** met een bezette semaphore (`Semaphore(0)`) en een deadline van 0,03 s: `timeout`, nul providercalls, `transportpogingen == "unknown"`;
- een uitzondering van de AI-laag: `unknown`.

**Herijkte assertions**, met bronreden in de test:
- `test_geldig_fail_oordeel_met_volledige_binding_en_eerlijke_metadata`: `transportpogingen == 1` → `ONBEKEND`. De 1 was de beginwaarde van de logteller, geen meting.
- `test_echte_ai_laag_verbindingsfout_geeft_een_poging_ondanks_retryconfig`: `transportpogingen == 1` → `ONBEKEND`. De test meet het ene providercall zelf aan de netwerkgrens (`len(provider.calls) == 1`, onveranderd). De dienst kan dat via de interface niet vaststellen.

**Resterende beperking.** Het werkelijke aantal providercalls wordt door de dienst niet gemeten. Het "één poging"-gedrag berust op de opt-ins (`max_attempts=1`, `max_retries=0`), en die zijn alleen voor de echte `AIServiceV2`-stack getest.

## Volledige lijst van gewijzigde bestaande testregels

`git diff -U0` van het servicetestbestand bevat precies deze zes verwijderde regels. Alle andere wijzigingen zijn toevoegingen.

- De signaturen van `FakeRouter.__init__`, `FakeAI.__init__` en `_Provider.__init__`: uitgebreid of herijkt als hierboven.
- De docstring van `FakeAI`: uitgebreid.
- Twee `transportpogingen == 1`-assertions: herijkt als hierboven.

Er is geen testgeval verwijderd of afgezwakt.

## Logging: gemotiveerde scopewaiver

De review bevestigt dat `utils.async_api` (`async_api.py:212`) tekst uit een providerexceptie logt. De dienstlogger doet dat aantoonbaar niet. Voor deze uitsluitend offline, niet-geactiveerde WP2 is dit een **gemotiveerde scopewaiver**: de transportlaag is read-only en buiten scope. Ik claim **geen ketenbrede privacy** en **geen productiegereedheid**. Inhoudsvrije logging van de hele keten blijft een voorwaarde voor integratie en activering.

## Stop

Stop voor verificatie door de coördinator en herreview door dezelfde Codex CLI.
