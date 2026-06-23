# Tech-debt Audit Rapport — DefinitieAgent

> Methode: multi-agent audit (8 finder-dimensies → adversariële verificatie tegen de échte code → synthese). 17 agents, 56 bevestigde bevindingen, 3 afgewezen. Orchestrator-verificatie: 8 kernclaims handmatig geverifieerd (alle bevestigd).
> Datum: 2026-06-23 · Branch: `feature/DEF-456-remove-dead-save-as-draft` · Scope: ~96.905 regels src (376 bestanden)

## 1. Executive Summary

De codebase is functioneel volwassen maar draagt aanzienlijke architectuurschuld, geconcentreerd in een handvol god-objects en een CI-gate die regressies onvoldoende afvangt. Het grootste enkele risico is de god-method `create_definition()` (~995 regels, nesting-diepte ~10) die actief verslechtert (bestand gegroeid van 733r → 1468r) en praktisch niet unit-testbaar is. Daarnaast maskeert de CI verschillende gates met `|| true` (integration-job, **coverage-stap én ruff**) en draait géén enkele verplichte workflow de gedocumenteerde 45%-coverage-ratchet — kwaliteitsregressies kunnen groen mergen. De type-safety-schuld is grotendeels te herleiden tot één config-omissie (DEF-439: ontbrekende `mypy_path`/`explicit_package_bases`, ~45% van de mypy-baseline). Tracking-gaten: stub-code in productie-DI (`GPT4SynonymSuggester`), dode modules (`async_progress.py`, `src/exports/`), en `gpt-5.2`-hardcodes verspreid over 4 bestanden.

**Totaaltelling per severity (56 bevindingen):** kritiek 1 · hoog 10 · midden 22 · laag 23. (Plus 3 afgewezen/foutpositief.)

---

## 2. Bevindingen per thema

### 2.1 God-objects & god-methods

| Sev | Locatie | Omschrijving | Fix | Effort |
|-----|---------|--------------|-----|--------|
| **kritiek** | `src/services/orchestrators/definition_orchestrator_v2.py:298-1293` | `create_definition()` ~995r, 11-phase flow in één methode, max-indent ~40 spaties (~nesting 10). Bestand gegroeid 733→1468r. | Extraheer per fase naar `_phase_*` of `PipelinePhase`-handlers; dunne sequencer. Guard-clauses tegen nesting. Prompt-builders niet wijzigen zonder overleg. | XL |
| hoog | `src/services/validation/modular_validation_service.py:850-1251` | `_evaluate_json_rule()` ~401r switch-on-type; 36 methoden in 1767r; `_has_*`-tekstheuristieken vermengd. | Dispatch-dict/Strategy per rule_type; `_has_*` → `TextHeuristics`-helper. **KRITIEK: AI-validatie-engine niet wijzigen zonder overleg.** | L |
| hoog | `src/services/ufo_pattern_matcher.py:68-1336` | ~1268/1642r zijn twee data-als-code methoden (`_initialize_legal_vocabulary`, `_initialize_comprehensive_patterns`). | Verplaats vocabulaire/patronen naar `config/ufo/*.yaml`; `_initialize_*` worden dunne loaders. | XL |
| hoog | `src/ui/components/definition_edit_tab.py:23-1914` | God-class, 31 methoden, 148 st.-calls, view+controller+concurrency vermengd. | Trek save/validate/search/auto-save/restore naar `DefinitionEditService`/controller; tab <600r. | XL |
| midden | `src/ui/components/expert_review_tab.py:34-1422` | God-class, 21 methoden, 206 st.-calls; bevat onverwacht 'verboden woorden management'. | Review-acties → `ReviewService`; verboden-woorden → admin-component; tab <700r. | L |
| midden | `src/services/interfaces.py:1-1275` | 40 top-level classes: TypedDicts + dataclasses + 8+ ABCs + exception-hiërarchie vermengd. | Splits: domein→`src/domain/`, DTO's→`types.py`, ABCs→`interfaces/`, exceptions→`exceptions.py`. Tijdelijke re-exports. | M |
| laag | `src/voorbeelden/unified_voorbeelden.py:453-530` | Deels foutpositief: 7/8 `_generate_resilient_*` zijn al thin delegators; rest is bewuste circuit-breaker-boilerplate. Module nog ongetypeerd (override). | Optioneel: collapse 7 trivialen naar geparametriseerde methode (mits per-type isolatie behouden). Hoofdwerk: typeer module (zie 2.2). | M |
| laag | `src/services/definition_generator_config.py:36` | `GPTConfig.model = "gpt-5.2"` hardcoded ondanks ModelRouter-patroon. | Verwijder literal of resolve via ModelRouter/centrale constante. | S |

### 2.2 Type-safety

| Sev | Locatie | Omschrijving | Fix | Effort |
|-----|---------|--------------|-----|--------|
| hoog | `pyproject.toml:173-207`; symptoom `src/database/definitie_repository.py:73-292` | **DEF-439 (open)**: ontbrekende `mypy_path`/`explicit_package_bases` laat `database.*`/`services.*` naar Any resolven → 22 spurieuze no-any-return (~45% van baseline-49). Fix bewezen: met beide settings 'Success'. | Voeg `mypy_path="src"` + `explicit_package_bases=true` toe (eigen PR). Daarna facade uit overrides, baselines omlaag. | M |
| midden | `src/voorbeelden/robust_cache.py` (349r), `unified_voorbeelden.py` (1224r); `pyproject.toml:204-206` | Twee echt-ongetypeerde override-modules. `unified_voorbeelden` heeft 3 echte fouten: `:159` no-any-return, `:400` assignment str\|None→str, `:1192` list[str]\|str→list[str]. | Annoteer beide (DEF-437 batch 4c); fix de 3 fouten; uit overrides, ratchets `--update`. Override→1 (→0 wacht op DEF-439). | L |
| laag | 10 bestanden (o.a. `integrated_resilience.py:21,24`; `modern_web_lookup_service.py:359,1046`; `CON-01.py:16`; `CON_01.py:15`) | 10 bare `# type: ignore` zonder error-code; PGH003 in ruff-ignore (`pyproject.toml:85`). | Maak alle 10 code-specifiek (`[import-untyped]`/`[no-untyped-def]`); overweeg PGH003 te activeren. | S |
| laag | `src/` breed (161 `cast()`); o.a. `async_api.py:156,233`, `smart_rate_limiter.py:353,634`, `models.py:118-210` | 161 casts verbergen Any; async_api/smart_rate_limiter zijn DEF-439-workarounds (overbodig na fix). json.loads-casts runtime-onveilig. | Na DEF-439: herzie async-casts. json-casts → validatie-helper/TypedDict. Geen brede sweep. | M |
| laag | `src/ui/status_flags.py:178,193,302,363,373`; `src/toetsregels/rule_cache.py:139,143` | ~7 echte fixbare fouten onder baseline (5 no-any-return + 2 has-type). `rule_cache._initialized` = init-ordering-smell. | Annoteer return-paths in status_flags; declareer `_initialized` als class-attribuut; ratchet omlaag. | S |

### 2.3 Test-infra & CI-gates

| Sev | Locatie | Omschrijving | Fix | Effort |
|-----|---------|--------------|-----|--------|
| hoog | `.github/workflows/test.yml:50,89,139,146` | **Vier `\|\| true`-maskeringen**: `ruff check src/services` (:50), coverage-stap (:89), integration-job (:139), e2e-job (:146, dood — geen `tests/e2e/`). Alle failures onzichtbaar. | Verwijder `\|\| true` van ruff + coverage nu; van integration zodra hangs gevalideerd; e2e-regel schrappen. | M |
| hoog | `.github/workflows/test.yml:60-66` + `scripts/testing/run_tests.sh:27-44` | PR-gate draait alleen allowlist (~5 bestanden), niet `-m unit`. 45%-ratchet zit alleen in `make test-cov-ci`, door **geen** workflow aangeroepen. PR kan unit-breuk groen mergen. | Voeg verplichte CI-stap `make test-cov-ci` (`--cov-fail-under=45`) toe; behoud pr-profiel als snelle voorcheck. | M |
| hoog | `test.yml:19,127` + `ci.yml:20` vs `pyproject.toml` | **DEF-426**: CI op Python 3.11, target 3.13. 3.13-breuken niet gevangen. Migratie strandde op httpx/httpcore. | Aparte sessie: resolve deps, 3.13 in matrix, 3.11 verwijderen zodra groen. | L |
| midden | `ufo_pattern_matcher.py` (1642r), `synonym_admin.py` (844r), `expert_review_tab.py`, `definition_edit_tab.py` | Grootste modules zonder dekking: ufo_pattern_matcher=0, synonym_admin=0 test-refs. Geen vangnet bij god-object-refactor. | Characterization-tests vóór refactor; UI-logica naar testbare services. | XL |
| midden | `definitie_validator.py` (1043r), `input_validator.py` (871r), `config_manager.py` (906r), `definitie_checker.py` (881r), `sru_service.py` (1281r) | >4900r kritieke validatie/config zonder dedicated test-bestand. | Gerichte unit-tests; begin bij input_validator + definitie_validator. | L |
| midden | `test_validation_config_overlay.py`, `test_modular_validation_aggregation.py`, context-payload tests | ~45 permanente skips: 29 'not yet implemented' + 11 'function not found' + 5 'Run AFTER'. Valse veiligheid. | Triage: verwijder dode 'function not found'-tests (met toestemming); koppel US-041/042/043 aan issue of verwijder. | M |
| midden | `tests/integration/compliance/test_astra_nora_context_compliance.py:95,170,301,373,380` | 5 xfail-tests patchen niet-bestaande modules; `strict=False` (overschrijft globale strict). Dode tests. | Verwijder of herschrijf tegen huidige structuur; documenteer in Linear. | S |
| laag | `pytest.ini:31-32` | **DEF-420**: `filterwarnings = default` i.p.v. `error`; 3.13-deprecaties gaan als ruis voorbij. | Triage warnings, gerichte ignores, zet `error`. Combineer met 3.13-migratie. | M |
| laag | `.github/workflows/ci.yml:39-50` | Smoke-gate dekt slechts 2 bestanden, coverage zonder `--cov-fail-under`. | Voeg blokkerende `--cov-fail-under=45` toe (overlapt met PR-gate-bevinding). | S |

### 2.4 Anti-patronen

| Sev | Locatie | Omschrijving | Fix | Effort |
|-----|---------|--------------|-----|--------|
| midden | `definition_generator_config.py:36`, `config_manager.py:56-57`, `api_monitor.py:104,139,618`, `model_router.py:30,49` | `gpt-5.2` hardcoded op ≥5 plekken (7 hits/4 bestanden); schendt ModelRouter-patroon. Defaults kunnen afwijken bij ontbrekende config. | Centraliseer op `ModelRouter._DEFAULT_CONFIG`; dataclass-defaults → None + resolutie; api_monitor via ModelRouter. | M |
| midden | `definition_edit_tab.py:541-544, 632-635, 672-675` | Key-only-pattern geschonden: `value=` + `key=` op 3 text_inputs → race condition bij rerun. | Init session-state eenmalig, render key-only (zie `expert_review_tab.py:798-801`). | S |
| laag | `synonym_admin.py:410-422`, `definition_edit_tab.py:266-269`, `expert_review_tab.py:165-168` | `value=`+`key=` op slider/checkbox; lagere race-gevoeligheid. | State vooraf init via SessionStateManager; `value=` weglaten. | M |
| laag | `expert_review_tab.py:477, 800` | Directe `not in st.session_state` membershipcheck; SessionStateManager mist `has_key`/`__contains__`. | Voeg `has_key`-helper toe; vervang de 2 checks. | S |
| laag | `config_manager.py:135,153`, `components.py:47,75` | Engelse niet-canonieke `organizational_contexts`/`legal_contexts` (config-optielijsten, geen datavelden). | Rename naar `*_context_opties` (solo-dev, geen backwards-compat). | S |
| laag | `gpt4_synonym_suggester.py`, `container.py:474-526`, `synonym_admin.py:163,187-224` | Stub bedraad in productie-wiring; UI-knop 'Genereer (GPT-4)' levert stil 0 resultaten. | Implementeer via ModelRouter/AIServiceV2 óf verberg/disable UI met melding. Borg in Linear. | M |

### 2.5 Dode code, stubs & duplicatie

| Sev | Locatie | Omschrijving | Fix | Effort |
|-----|---------|--------------|-----|--------|
| midden | `gpt4_synonym_suggester.py:46-100` | Permanente placeholder: `suggest_synonyms()` → `[]`. Bedraad én aangeroepen (`synonym_orchestrator.py:275`). UI suggereert AI-verrijking, levert altijd nul. | Met Chris: implementeer (AIServiceV2+ModelRouter) óf verwijder hele keten. AI-engine = overleg. | L |
| laag | `src/services/definition_repository.py:397-490` | `get_or_create_draft` (~94r) heeft géén productie-caller, alleen tests. Restant DEF-456 save-as-draft-opschoning. | Verifieer geen externe entrypoint; verwijder methode + testklasse (toestemming Chris). | S |
| laag | `src/exports/__init__.py` | Lege git-tracked package naast actieve `src/export/`; verwarrende naam, geen importers. | Verwijder `src/exports/` (toestemming). | S |
| laag | `src/log/` (leeg), `src/logs/synonym_enrichment.log` | Untracked runtime-artefacten onder src/; code schrijft cwd-relatief (`synonym_orchestrator.py:51`). | Verwijder lokale mappen; maak log-paden config/absoluut. | S |
| laag | `definition_generator_config.py:36`, `api_monitor.py:104,139,618` | `gpt-5.2` dataclass-default + harde pricing-tabel-hardcode (verkeerde kostenberekening bij modelwissel). | Default → None/ModelRouter; pricing-tabel config-gestuurd. | M |
| laag | `src/toetsregels/regels/CON-01.py` + `src/toetsregels/validators/CON_01.py` | Twee CON-01-implementaties in aparte mappen (regels/ vs validators/) — verwarrend dubbel. | Bevestig welke actief is; consolideer/verwijder de dode. | M |

### 2.6 Dependencies & security

| Sev | Locatie | Omschrijving | Fix | Effort |
|-----|---------|--------------|-----|--------|
| midden | `config/config.yaml:6` | `default_temperature: 0.9` contradiceert code-default 0.0 ('deterministisch voor juridische definities'). config.yaml wint bij opstart. Nuance: per-prompt-pad (`get_prompt_temperature`, 'definition'→0.01) kan kerngeneratie ontzien. | Zet terug op 0.0; voeg test config-vs-code-default toe. | S |
| midden | `model_router.py:48-50`, `api_monitor.py:103-120`, `config_manager.py:72-86`, `config.yaml:7+` | Geen single source of truth modelnamen+pricing. config_manager+config.yaml bevatten legacy (gpt-4/gpt-4.1/gpt-4o-mini) met eigen cost_per_token. | Consolideer in één canonieke `model_routing`-sectie; verwijder legacy. | M |
| laag | `security.yml:27` vs `.pre-commit-config.yaml:29` | gitleaks-drift: CI v8.25.0 vs pre-commit v8.29.1; `check_tool_pins.py` dekt gitleaks niet. | Pin gelijk (bump CI→8.29.1); voeg gitleaks-cross-check toe. | S |
| laag | `gpt4_synonym_suggester.py:11,74,106` vs `scripts/ci/check_no_todo_markers.sh:8-9` | Hook matcht alleen `#`-TODO's; 3 docstring-TODO's ontsnappen → vals 'TODO-vrij'. | Breid regex uit naar docstring-TODO's óf converteer naar Linear-ref. | S |
| laag | `.pre-commit-config.yaml:62,69,83` | 3 hooks met `\|\| true` (pytest-smoke, forbidden-patterns, file-size). forbidden-patterns bewaakt 'geen streamlit in services' maar handhaaft niets. | Verwijder `\|\| true` van forbidden-patterns (architectuurregel = hard falen). | S |

### 2.7 Error-handling & resilience

| Sev | Locatie | Omschrijving | Fix | Effort |
|-----|---------|--------------|-----|--------|
| hoog | `unified_voorbeelden.py:161-185` | **DEF-428**: `_run_async_safe` maakt wegwerp-event-loops per call (loop-gebonden rate-limiter/circuit-state persisteert niet); `future.result()` zonder timeout (`:181`) → UI-thread oneindige hang mogelijk. | Async-entrypoint doorvoeren; bridge → `future.result(timeout=...)`; overweeg gedeelde achtergrond-loop. Generatieflow = overleg. | L |
| midden | `integrated_resilience.py:311-312` | `duration = time.time() - time.time()` (altijd ~0) naar `record_success` → retry-latency-metrics structureel 0 (comment geeft bug toe). | Leg `start_time` vóór de call vast; bereken echte duration. | S |
| midden | `resilience.py:508` | Generieke `raise Exception(msg)` in productie-`execute_with_resilience` → callers kunnen niet selectief vangen. | Introduceer `ResilienceError`/hergebruik `AIClientError`. | S |
| midden | `gpt4_synonym_suggester.py:68-100`, `container.py:474-499`, `synonym_orchestrator.py:100`, `synonym_admin.py:97-104` | Stub in productie-DI geeft stil `[]` (graceful degradation zonder zichtbare melding). | `is_available()`/feature-flag → UI verbergt of toont melding. | M |
| midden | `definition_workflow_service.py:658`, `CON-01.py:111`, `CON_01.py:101`, `definition_edit_tab.py:450,536,1422,1782` | Ingeslikte excepties (kale `pass`); CON-01/CON_01 breed `except Exception` als 'soft-fail' in toetsregel → stille validatie-misser. | `logger.debug(..., exc_info=True)` in elk blok; vernauw CON-01/CON_01. | M |
| midden | `definitie_manager.py:79,116,119,212`; `logging_filters.py:27-54` | `approved_by`/`approval_notes` in klare tekst gelogd; PII-filter dekt geen vrije persoonsnamen → schendt 'geen persoonsdata in logs'. | Log `approver_id`/gehasht of weglaten op INFO; bevestig PII-filter draait op src/tools. | M |
| laag | `definition_import_service.py:72,167` | Deprecated `asyncio.get_event_loop()` in async-methoden (3.13-target). | Vervang door `asyncio.get_running_loop()`. | S |
| laag | `integrated_resilience.py:155,225-228,372` | `with_full_resilience` `timeout=None` default → nieuwe caller krijgt opnieuw onbegrensde hang. | Veilige default-timeout (config) óf parameter verplicht maken. | S |
| laag | `resilience.py:35-41,350-351` | `FailoverStrategy`-enum dood; `retry_manager`/`rate_limiter` blijven None; twee parallelle resilience-stacks. | Verwijder dode enum/None-attributen óf documenteer laag-scheiding; consolideer. | M |

### 2.8 Tracking-gaten (Linear, team DEF)

| Sev | Item | Omschrijving |
|-----|------|--------------|
| midden | Inventaris | 49 tech-debt-issues (29 backlog + 4 in progress + 16 done). In progress: DEF-418, DEF-419, DEF-428, DEF-456. |
| hoog | DEF-428 (In Progress) | Productie-timeout-gat in `_run_async_safe` (`:181`) nog niet gefixt; DEF-429 (rate-limiter) is Done maar dit staat open. |
| midden | DEF-426 (Backlog) | 3.13/3.11 CI-mismatch + recidive: 4 untracked `test_import_*.csv` in root (schendt 'geen bestanden in root'). |
| hoog | DEF-421/422/424/192/312 (Backlog) | God-objects getrackt maar gegroeid: orchestrator 733→1468r, container 839→1041r. Titel-regelaantallen achterhaald. |
| laag | DEF-444 (Backlog) | `async_progress.py:12` kapotte import (`services.async_definition_service` bestaat niet) — hard geverifieerd dood. |
| laag | DEF-393 (Backlog) | Scope-drift: titel '~30 handlers' vs body/meting 514 `except Exception`/bare. |

---

## 3. Geprioriteerde Remediatie-roadmap

### Quick-wins (hoge waarde / lage effort) — eerst

| # | Actie | Effort | Issue |
|---|-------|--------|-------|
| 1 | **DEF-439 config-fix**: `mypy_path="src"` + `explicit_package_bases=true` → ruimt ~45% mypy-baseline + facade-override + async-casts op | M | nieuw (DEF-439-vervolg) |
| 2 | **Coverage-ratchet afdwingen** in CI (`make test-cov-ci`) + `\|\| true` weg bij ruff/coverage — grootste gate-gat | M | nieuw |
| 3 | `resilience.py:508` → domein-exception | S | DEF-393-deel |
| 4 | `integrated_resilience.py:311` duurmeting-bug fixen | S | nieuw |
| 5 | `config.yaml:6` temperature 0.9→0.0 + verificatietest | S | nieuw |
| 6 | gitleaks-pin gelijktrekken + `check_tool_pins.py` uitbreiden | S | nieuw |
| 7 | `\|\| true` weg bij forbidden-patterns pre-commit hook | S | nieuw |
| 8 | Dode code opruimen: `async_progress.py` (DEF-444), `src/exports/`, `get_or_create_draft` (DEF-456), `src/log(s)/` | S | DEF-444/DEF-456 |
| 9 | 10 bare `# type: ignore` code-specifiek maken | S | nieuw |
| 10 | status_flags/rule_cache ~7 mypy-fouten annoteren | S | DEF-431/437-deel |

### Middelgrote brokken

| # | Actie | Effort | Issue |
|---|-------|--------|-------|
| 11 | **DEF-428**: timeout in `_run_async_safe` (productie-hang) — overleg vereist | L | DEF-428 (In Progress) |
| 12 | Annoteer `robust_cache` + `unified_voorbeelden` + fix 3 echte fouten; override→1 | L | DEF-437 batch 4c |
| 13 | `gpt-5.2`-hardcodes centraliseren op ModelRouter (4 bestanden) | M | nieuw |
| 14 | Key-only-pattern fixen (text_inputs eerst, dan slider/checkbox) + `has_key`-helper | M | nieuw |
| 15 | Stub `GPT4SynonymSuggester`: implementeer óf verberg UI — beslis met Chris | L | nieuw |
| 16 | Ingeslikte excepties loggen; CON-01/CON_01 vernauwen + consolideren | M | DEF-393-deel |
| 17 | PII: approver-naam-logging dichten | M | nieuw |
| 18 | Stale/xfail-tests triage (~45 skips + 5 xfail) | M | nieuw |
| 19 | Model+pricing single source of truth | M | nieuw |
| 20 | `filterwarnings=error` (DEF-420) | M | DEF-420-vervolg |

### Grote brokken (overleg + tests vereist)

| # | Actie | Effort | Issue |
|---|-------|--------|-------|
| 21 | **`create_definition()` refactor** (995r → fase-handlers) — eerst characterization-tests | XL | DEF-421 (upwaarderen→hoog) |
| 22 | `definition_edit_tab` god-class → service-extractie | XL | DEF-422 |
| 23 | `ufo_pattern_matcher` data→YAML + characterization-tests | XL | DEF-424-deel/nieuw |
| 24 | `_evaluate_json_rule` dispatch-refactor (AI-engine, overleg) | L | nieuw |
| 25 | `interfaces.py` (40 classes) opsplitsen | M | DEF-312 |
| 26 | Python 3.13 CI-migratie | L | DEF-426-vervolg |
| 27 | Characterization-tests grootste ongeteste modules vóór refactor | XL | nieuw |

---

## 4. Tracking-gaten — voorstel nieuwe DEF-issues

Niet getrackt in de 49 bestaande tech-debt-issues (laat Linear de ID toewijzen):

1. **CI-gate dwingt coverage-ratchet niet af** (test.yml PR-gate = allowlist; `\|\| true` op coverage/integration/ruff). Hoog.
2. **`gpt-5.2`-hardcodes verspreid** over 4 productiebestanden incl. pricing-tabel. Midden.
3. **`GPT4SynonymSuggester` stub in productie-DI** — 3 docstring-TODO's ontsnappen aan no-todo-hook. Midden.
4. **`config.yaml` temperature 0.9 vs code-default 0.0** — config-drift, ontbrekende validatietest. Midden.
5. **PII: approver-namen in klare-tekst logs** (`definitie_manager.py`). Midden.
6. **Retry-latency-metrics structureel 0** (`integrated_resilience.py:311`). Laag/midden.
7. **Generieke `raise Exception` in resilience-flow** (`resilience.py:508`). Laag/midden.
8. **gitleaks-versie-drift CI vs pre-commit**. Laag.
9. **Bare `# type: ignore` + PGH003 niet gehandhaafd**. Laag.
10. **Dode artefacten**: `src/exports/`, `src/log(s)/`, CON-01/CON_01-duplicaat, key-only-violaties. Laag.

Daarnaast: **actualiseer regelaantallen** in DEF-421/422/424/312 (titels achterhaald door groei) en **hernoem/herscope DEF-393** (titel ~30 vs werkelijkheid 514).

---

## 5. Reeds opgelost / foutpositief (niet opnieuw oppakken)

- **DEF-439 issue zelf is Done** (2026-06-19, PR #264) — máár de onderliggende config-fix (`mypy_path`/`explicit_package_bases`) is in de code **niet** aanwezig; de open debt is geverifieerd reëel. Maak een vervolg-issue, heropen niet blind.
- **DEF-429 (rate-limiter cross-loop deadlock)**: Done — SmartRateLimiter self-healing. Niet verwarren met het nog-open DEF-428-productie-timeout-gat.
- **web_lookup duplicatie** (`sru_service` vs `modern_web_lookup_service`): GEEN duplicaat — SRUService is sub-component met 1 importer; geen V1-restanten. Afgewezen.
- **`unified_voorbeelden` copy-paste bodies**: stale claim — 7/8 al gerefactord naar common-delegators; rest is bewuste circuit-breaker-isolatie.
- **`st.session_state` direct (6 modules)**: overschat — 4/6 zijn comments/docstrings/`id()`/log-labels; alleen `expert_review_tab.py:477,800` zijn echte hits.
- **`definitie_crud.py` no-any-return**: DEF-439-symptoom (verdwijnt met config-fix), niet apart annoteren.
- **xfail `strict=True`-claim**: onjuist — lokale `strict=False` overschrijft globale `xfail_strict=true`.
- **`integrated_resilience.py:482` raise Exception**: testcode, geen productie-foutcontract.

---

## Orchestrator-verificatie (handmatig, 2026-06-23)

8 kernclaims tegen de huidige code gecontroleerd — allemaal bevestigd:

1. `create_definition` begint op `definition_orchestrator_v2.py:298` ✓
2. `\|\| true` in `test.yml` op regels 50 (ruff), 89 (coverage), 139 (integration), 146 (e2e) ✓ — sterker dan de finder claimde
3. `config/config.yaml:6` → `default_temperature: 0.9` ✓
4. `integrated_resilience.py:311` → letterlijk `time.time() - time.time()` ✓
5. `async_progress.py:12` importeert niet-bestaande `services.async_definition_service` ✓
6. `CON-01.py` (regels/) én `CON_01.py` (validators/) bestaan beide ✓
7. `gpt-5.2` in 4 bestanden (config_manager, api_monitor, definition_generator_config, model_router) ✓
8. `src/exports/` is leeg naast actieve `src/export/` ✓

**Bronnen:** 56 adversarieel-geverifieerde bevindingen (8 dimensies, 17 agents) + Linear team DEF tech-debt-inventaris (49 issues) + 8 handmatig geverifieerde kernclaims. Alle code-locaties verwijzen naar branch `feature/DEF-456-remove-dead-save-as-draft`.
