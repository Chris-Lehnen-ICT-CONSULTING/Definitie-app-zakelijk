# DEF-766 — correctieronde 4: twee CI-fouten op PR #467

**Uitvoerder:** Claude Code CLI (Opus 5), sessie in werkboom `/Users/chrislehnen/.codex/worktrees/2075/Definitie-app`, branch `feature/DEF-766-ess03-ai-beoordeling`, basis HEAD `c0d3423ab` (schoon bij start). Geen commit, push of PR; niets verwijderd; geen echte modelcalls (alle AI-verkeer via de bevroren testgrens).
**Diff-identiteit (werkboom t.o.v. HEAD):** `git diff | shasum -a 256` = `e6728cd50212c7fc23f5cdaaf5493a94a0d5bd7998008251d389ccfc09b22e50`; 5 bestanden, +153/−8; **`src/` onaangeroerd** (`git diff --stat -- src/` leeg).
**Logs:** `/tmp/def766-ai-20260921/c4-*.log` (laatste regel `EXIT=<code>`, geschreven via `logs/def766-c3/runlog.py`).

**Eindstand:** beide CI-fouten lokaal gereproduceerd (rood) en opgelost (groen): offline kernjourney 3 passed; timing-ratchet exit 0 (121 locaties, 0 te beoordelen). Alle gates groen: `make test-integration` 572 passed / exit 0, `make test-acceptance` 21 passed / exit 0, `make test` 6902 passed / exit 0, lint 0, mypy 0 (baseline 0), complexity 199 < 201, markers 491/491, preflight 4/4 stappen exit 0, root-allowlist 0. Systeemprompt- en normhash byte-identiek (`e51d06cb…` / `372bb329…`, `ess03-assess/2`).

---

## 1. Wijzigingen (bestand:regel)

| Bestand | Regels | Wat |
| --- | --- | --- |
| `tests/integration/functionality/conftest.py` | 32 | import `LOCATIE_TERM`, `VERDICT_INSUFFICIENT` uit `domain.ess03.contract` (+ `json`) |
| | 82–133 | `ESS03_SOORT = "ess03"`, `_ESS03_BEGRIPREGEL` (herkenning op de vaste materiaalregel `Begrip (vindplaats term): …` uit `bouw_beoordelingsprompt`, opgebouwd uit de contractconstante), `is_ess03_beoordelingsprompt()`, `ess03_bevroren_antwoord()` |
| | 163–164 | `_ontleed_prompt`: ESS-03-prompt → soort `ess03` (vóór de voorbeeldmarkeringen) |
| | 215–217 | klassedocstring `BevrorenAIClient`: gedrag per modus voor ESS-03 |
| | 242–244 | `chat_completion(..., max_retries: int \| None = None)` — optioneel keyword conform het Protocol, ongebruikt |
| | 261–262 | ESS-03 krijgt `ess03_bevroren_antwoord(prompt)` (in `leeg` blijft de respons leeg → technische fout, consistent met de modus-betekenis) |
| `tests/integration/test_offline_core_journey.py` | 124–131 | DEF-766-toelichting boven `VERWACHTE_DEKKING`: AI-beoordeling via de bevroren grens; bevroren antwoord = onvoldoende informatie → `review_required` |
| | 139 | `"not_applicable": 0` toegevoegd (zie § 2.3 — de tellingen 33/29/4/16/4/0 zijn ongewijzigd) |
| `tests/integration/test_synonym_orchestrator_e2e.py` | 51–54 | import `ess03_bevroren_antwoord`, `is_ess03_beoordelingsprompt` (precedent: de journey importeert al uit deze conftest) |
| | 96–103 | klassedocstring: ESS-03-antwoord |
| | 138–149 | `hoofddefinitieoproepen()` sluit de ESS-03-prompt uit (die draagt de *gereinigde* definitie en telde anders stil als hoofddefinitieprompt mee) |
| | 158–160 | `max_retries: int \| None = None` |
| | 174–175 | ESS-03-tak → `ess03_bevroren_antwoord(prompt)` |
| `docs/testing/def563-timing-baseline.json` | 676–683, 971–1002 | 5 nieuwe entries met `source_sha256`/`comparisons` uit `--inventory`, expliciete status en reden |
| `docs/testing/def563-timing-inventaris.md` | 41–61 | paragraaf "DEF-766 — 22 september 2026" met tabel en tellingen (151 vergelijkingen / 121 locaties; 114 onbeoordeeld, 7 beoordeeld) |

Niet gewijzigd: productiecode, prompts, norm, de vijf unit-testbestanden uit de timing-inventaris.

## 2. Fout 1 — offline kernjourney (`max_retries` + ESS-03-antwoord)

### 2.1 Reproductie (rood)
`pytest tests/integration/test_offline_core_journey.py -x` op HEAD: `1 failed, 2 passed` — `ERROR utils.async_api:async_api.py:212 API call failed: BevrorenAIClient.chat_completion() got an unexpected keyword argument 'max_retries'` → `ESS-03: telbaarheidsbeoordeling mislukt (connection)` → `AssertionError: validatie: dekking wijkt af: {'evaluated': 33, 'passed': 29, 'failed': 4, 'review_required': 15, 'not_evaluated': 4, 'error': 1, 'not_applicable': 0, 'total': 53, 'coverage_ratio': 0.6226}` (identiek aan CI).

### 2.2 Keuze en motivering
**Fix in de fakes, niet in de productiecode.** Onderzoek:
- Fixture-keten: `test_offline_core_journey.py` → `bevroren_omgeving` (`tests/integration/functionality/conftest.py:379`) → `BevrorenAIClient` als enige bevroren grens (`services.ai.create_ai_client`). De validatie in de journey loopt via `ServiceAdapter` → `DefinitionOrchestratorV2` → `ValidationOrchestratorV2._ess03_beoordeling` (`validation_orchestrator_v2.py:488`) → `Ess03AssessmentService.assess` → `AIServiceV2.generate_definition(max_attempts=1, max_retries=0, …)` → `AsyncGPTClient._make_request_with_retries` → `self._ai_client.chat_completion(..., **clientopties)` met `clientopties = {"max_retries": 0}` (`async_api.py:245–262`).
- Het `AsyncAIClient`-Protocol (`src/services/ai/base_client.py:145–164`) **schrijft `max_retries: int | None = None` voor** als optioneel keyword ("DEF-766, opt-in: SDK-interne retries voor déze aanroep; None laat de clientdefault staan"). De echte `AnthropicClient`/`OpenAIClient` volgen dat; de twee bevroren clients waren achtergebleven op de oude signatuur. De abstractie schrijft het keyword dus wél voor → de productiecode versoepelen (kwargs stil wegfilteren) zou het Protocol ondergraven en de opt-in onzichtbaar maken. De fakes zijn hersteld naar de interface; het keyword wordt door hen niet gebruikt.
- Alle andere test-fakes met `chat_completion` (`test_def766_ai_route_optins.py`, `test_def766_ess03_correcties_service.py`, `test_def766_ess03_truncation.py`) accepteren al `**kw`; `tests/unit/scripts/test_ess02_praktijkproef.py` raakt ESS-03 niet (unitgate groen).

### 2.3 Het bevroren ESS-03-antwoord
`ess03_bevroren_antwoord(prompt)` levert één kaal JSON-object met exact de acht contractvelden: `verdict: insufficient_information`, `applicability: undetermined`, `unit: null`, `reason` (begint met "Bevroren proefantwoord: …" zodat het nooit voor modelkwaliteit doorgaat), `evidence: [{"location": "term", "quote": <begrip uit de prompt>}]`, `missing_information`, precies één `question` (één zin, één vraagteken), `uncertainty: null`. Het citaat is het begrip zoals het letterlijk op de materiaalregel `Begrip (vindplaats term): …` staat; `beoordelingsmateriaal()` zet exact dat begrip onder vindplaats `term`, dus `vind_citaat` slaagt. Is het begrip niet leesbaar, dan blijft `evidence` leeg (toegestaan bij dit verdict; `_bewijsfout`).

**Bewijs dat de dienst het antwoord accepteert** (`c4-probe-ess03-journey.log`, probe in git-ignored `logs/def766-c4/probe_ess03_journey.py` op dezelfde fixture en generatie als de journey; geen repo-artefact):
- precies 1 ESS-03-aanroep op de grens (`model=claude-opus-5`, `max_tokens=1200`);
- `ess03_assessment.status == "assessed"`, `error: null`, `rejected: []`, `attempts_observed: 1`, `retries_observed: 0`, `raw_response_sha256` gezet, `elapsed_seconds 0.001`;
- `judgment.verdict == "insufficient_information"`, `judgment.status == "review_required"`, `evidence == [{"location": "term", "quote": "vervoersverbod"}]`;
- `rule_results["ESS-03"].status == "review_required"`, `review.assessment.applied == True`, binding = verwachte binding (`ess03-assess/2`, norm `372bb329…`, `anthropic/claude-opus-5`);
- dekking `error == 0`, `review_required == 16`.
- **Discriminator:** met een gemonkeypatcht citaat dat niet in het materiaal staat meldt de dienst `error/unverifiable_evidence` ("citaat niet in materiaal (term: niet-verzonden citaat)") en wordt ESS-03 `error` (dekking `error == 1`). De groene uitkomst is dus niet toevallig.

**`VERWACHTE_DEKKING`:** de tellingen 33/29/4/16/4/0 zijn ongewijzigd. Wél moest de sleutel `"not_applicable": 0` erbij: deze branch voegde in commit `6c71bf128` het veld `not_applicable` aan het dekkingsblok toe (`modular_validation_service.py:1793`, "DEF-766: afgeronde niet-toepasselijkheid telt apart"), en de journey vergelijkt het hele dict. Zonder die sleutel blijft de test rood ook met een correct ESS-03-antwoord (zie de reproductiemelding in § 2.1, die `'not_applicable': 0` al toont). Precedent op de branch: `tests/unit/ui/test_def743_editor_ui.py:274`, `tests/unit/services/test_def766_ess03_herbinding_service.py:96`. Dit wijkt tekstueel af van de opdracht ("alleen toelichting bijwerken"); het is een additieve, door de branch zelf veroorzaakte contractuitbreiding, geen tellingwijziging.

### 2.4 Tweede fake (synonym e2e)
`test_definition_generation_with_synonym_enrichment_e2e` draait de volledige validatie (53 regels) via `orchestrator.create_definition`, dus ESS-03 raakt deze grens wél. Vóór de fix: `connection`-fout (zelfde `max_retries`-TypeError); na alleen de signatuurfix zou de fake `SYNTHETISCHE_DEFINITIE` als ESS-03-antwoord geven → `malformed_response` → `error`. Daarom ook hier de ESS-03-tak met hetzelfde antwoord, plus uitsluiting van de ESS-03-prompt uit `hoofddefinitieoproepen()` — die prompt draagt de *gereinigde* definitie (niet `SYNTHETISCHE_DEFINITIE`) en telde anders stil mee als bewijs dat "de definitiegeneratie langs de providergrens liep". Resultaat: `tests/integration/test_synonym_orchestrator_e2e.py` 5 passed (`c4-synonym-e2e.log`, exit 0) en in de integration-gate.

## 3. Fout 2 — DEF-563 timing-inventaris

### 3.1 Reproductie (rood)
`python -I -B scripts/ci/timing_assert_ratchet.py .` → 5× `nieuw`, "121 locaties; 5 te beoordelen wijzigingen", **exit 1** (`c4-timing-ratchet-voor.log`). Sleutels, `source_sha256` en `comparisons` overgenomen uit `--inventory` (AST-hash van het hele bestand; de vijf unit-testbestanden zijn niet gewijzigd, dus de hashes zijn stabiel).

### 3.2 Dispositie per kandidaat (metingen: `c4-timing-kandidaten-durations.log`, `c4-probe-timing-marges.log` — 5 herhalingen op de ontwikkelmachine, geen runnergarantie)

| Kandidaat | Vergelijking | Status | Reden |
| --- | --- | --- | --- |
| `test_def766_ai_route_optins.py::test_heuristische_tokenraming_slaat_tiktoken_over` | `time.perf_counter() - start < 0.4` | **retain-risk** | Wall-clock-bovengrens naast een deterministische teller: het discriminerende bewijs dat de heuristische raming tiktoken overslaat is `geraakt["encoder"] == 0` (de stub zou 0,5 s slapen). Gemeten 0,01 s (in-process fake), maar runnergevoelig en naast de teller redundant. Behouden; bij valse failure de klokgrens laten vervallen ten gunste van de teller, niet oprekken. |
| `test_def766_ess03_assessment_service.py::test_gegronde_beoordeling_via_taakrouting_zonder_hardcoded_model` | `call['timeout_seconds'] <= 60` | **non-timing** | Vergelijkt de configuratiewaarde `timeout_seconds` (kwarg aan de AI-laag) met 60; geen klok, geen meting. Alleen door de naamregex (`_seconds`) gezien. |
| `test_def766_ess03_correcties_service.py::test_trage_aanroep_wordt_door_de_deadline_afgebroken` | `time.perf_counter() - start < 1.5` | **contract** | Deadline 0,1 s (`asyncio.timeout`) bij een AI-laag die 5 s wacht; `<1,5 s` mét foutsoort `timeout` bewijst tijdige afbreking — de foutsoort alleen zou via het vangnet ook na 5 s ontstaan. Marge 15× de deadline; gemeten 0,101–0,102 s. Analoog aan de bestaande contract-entry `test_with_full_resilience_bounds_execution_time`. |
| `test_def766_ess03_correcties_service.py::test_vangnet_een_te_laat_teruggekeerd_antwoord_is_timeout_zonder_oordeel` | `d['elapsed_seconds'] >= 0.3` | **deterministic** | Ondergrens, geen bovengrens: de gemeten duur omvat een synchrone `time.sleep(0.3)` (niet onderbreekbaar door asyncio), dus `>= 0.3` geldt per constructie; belasting kan de meting alleen verhogen. Gemeten 0,302–0,306 s. |
| `test_def766_ess03_correcties_service.py::test_vertraagde_nabewerking_op_de_echte_route_komt_binnen_de_deadline_terug` | `duur < 0.45` | **retain-risk** | Contractgrens met krappe marge: nabewerking blokkeert 0,6 s in een werkthread, deadline 0,2 s, terugkeer vereist vóór 0,45 s (zonder `offload_postprocessing` pas na 0,6 s). Speling 0,25 s boven de deadline, 0,15 s onder de ongefixte duur; gemeten 0,201–0,202 s. Op een zwaar belaste runner kan de wake-up de 0,45 s overschrijden. Behouden; bij valse failure hooguit tot `<0,55` (moet onder 0,6 blijven om te discrimineren) of vervangen door een deterministisch signaal uit de werkthread. |

Baseline-eindstand: 121 locaties, 151 vergelijkingen; status: 114 unreviewed, 2 retain-risk, 2 deterministic, 2 contract, 1 non-timing. Ratchet na de update: **exit 0** (`c4-timing-ratchet-na.log`; nogmaals als allerlaatste stap na alle testwijzigingen: `c4-timing-ratchet-eind.log`, exit 0). De drie gewijzigde integratietestbestanden staan niet in de inventaris (geen timingvergelijkingen), dus geen `gewijzigd`-meldingen.

## 4. Gate-uitkomsten (alle met `PY=/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python`; test-gates met dezelfde env als CI: `ANTHROPIC_API_KEY=dummy OPENAI_API_KEY=dummy OPENAI_API_KEY_PROD=dummy AI_CLIENT_TIMEOUT=2 AI_SDK_MAX_RETRIES=0 AI_RATE_LIMIT_MAX_RETRIES=1 AI_RATE_LIMIT_BACKOFF_FACTOR=1.0` — de worktree heeft geen `.env`)

| Gate | Log | Exit | Resultaat |
| --- | --- | --- | --- |
| Gerichte reproductie journey (HEAD) | console | 1 | 1 failed, 2 passed (zie § 2.1) |
| `pytest tests/integration/test_offline_core_journey.py` (na fix) | `c4-journey-na-fix.log` | **0** | 3 passed (33,3 s) |
| Bewijsprobe ESS-03 + discriminator | `c4-probe-ess03-journey.log` | 0 | 2 passed |
| `pytest tests/integration/test_synonym_orchestrator_e2e.py` | `c4-synonym-e2e.log` | 0 | 5 passed |
| Duur 5 timingkandidaten | `c4-timing-kandidaten-durations.log` | 0 | 5 passed |
| Margeprobe timing | `c4-probe-timing-marges.log` | 0 | 1 passed (cijfers in § 3.2) |
| `timing_assert_ratchet.py .` vóór | `c4-timing-ratchet-voor.log` | 1 | 5 nieuw |
| `timing_assert_ratchet.py .` na / eind | `c4-timing-ratchet-na.log`, `c4-timing-ratchet-eind.log` | **0** | 121 locaties; 0 te beoordelen |
| `test_preflight_checks.py` | `c4-preflight-test-gate.log` | 0 | OK |
| `preflight_checks.py .` | `c4-preflight-checks.log` | 0 | blocking=0 |
| `test_timing_assert_ratchet.py` | `c4-timing-ratchet-selftest.log` | 0 | OK |
| `make test-integration` | `c4-make-test-integration.log` | **0** | 572 passed, 28 skipped, 15 xfailed, 2 xpassed (82,3 s); `run_profile status=ok` — geen hang op real-API-tests |
| `make test-acceptance` | `c4-make-test-acceptance.log` | **0** | 21 passed, 5 skipped (37,7 s); journey erin |
| `make test` (unitgate) | `c4-make-test.log` | **0** | 6902 passed, 75 skipped, 722 deselected, 1 xfailed, 21 subtests (278 s) |
| `make lint` | `c4-make-lint.log` | 0 | ruff + black schoon (src/config); gewijzigde testbestanden apart met ruff/black gecontroleerd: schoon |
| `make mypy-check` | `c4-make-mypy-check.log` | 0 | baseline 0 |
| `make complexity-check` | `c4-make-complexity-check.log` | 0 | 199 < baseline 201 |
| `make test-markers-check` | `c4-make-test-markers-check.log` | 0 | 491/491 |
| `scripts/ci/check_root_allowlist.sh` | `c4-root-allowlist.log` | 0 | OK |

## 5. Prompt- en normhash
`logs/def766-c3/hashes.py` (dezelfde methode als `scripts/ess03/run_ess03_gevallen.py`) vóór en na: `prompt_version ess03-assess/2`, `system_prompt_sha256 e51d06cb3c878d78f2a66135c248e5e8d2a4e95cc589a4fed816c411b125c758`, `norm_sha256 372bb329fa6630191cc13aaed20c715613043a4790ccb6a5dd9e01949e41e028` (`c4-hashes-na.log`; de voor-meting stond in de sessieconsole met identieke waarden). Per constructie ongewijzigd: `src/` heeft geen diff. De journey-probe bevestigt dezelfde normhash in de binding van de verkregen beoordeling.

## 6. Resterende beperkingen en observaties
1. **Pre-existing cache-isolatiegat in `test_synonym_orchestrator_e2e.py`** (niet veroorzaakt door en buiten deze opdracht): de test isoleert de CWD-relatieve `cache/` van `AIServiceV2` niet (anders dan `bevroren_omgeving`). Bij een *tweede directe* pytest-run vanuit de werkboom binnen de cache-TTL (1 u) zijn de definitie- én voorbeeldprompts cache-hits, waardoor `hoofddefinitieoproepen()`/`voorbeeldoproepen()` leeg zijn (`c4-synonym-e2e-logcli.log`: "Cache hit for prompt: …", failure op regel 441; vóór mijn wijziging zou dezelfde herhaalde run op regel 444 `voorbeeldoproepen()` zijn omgevallen). In de gates (runner met verse werkmap) en in CI (verse checkout) speelt dit niet; alle gates zijn groen. Aanbeveling voor een apart issue: cache-map in de `container`-fixture naar `tmp_path` monkeypatchen zoals `bevroren_omgeving` doet.
2. **`not_applicable` in `VERWACHTE_DEKKING`** (§ 2.3): additieve sleutel, vereist door de branch zelf; tellingen ongewijzigd.
3. **Herkenning van de ESS-03-prompt** in de fakes hangt aan de materiaalregel `Begrip (vindplaats term): …` (uit de contractconstante `LOCATIE_TERM`). Wijzigt `bouw_beoordelingsprompt` die regel, dan valt de journey luid om (ESS-03 → `error`, dekking wijkt af) — geen stille pass.
4. De ResourceWarnings "unclosed database in `_GateVerbinding`" in de journey- en gate-logs zijn pre-existing (ook in de rode run op HEAD) en vallen buiten deze opdracht.
5. Complexity daalde naar 199 (< baseline 201); de baseline is bewust niet met `--update` vastgezet (geen productiecodewijziging in deze ronde).
6. De probes (`logs/def766-c4/probe_ess03_journey.py`, `probe_timing_marges.py`) staan in de git-ignored `logs/`-map en zijn geen onderdeel van de diff.
