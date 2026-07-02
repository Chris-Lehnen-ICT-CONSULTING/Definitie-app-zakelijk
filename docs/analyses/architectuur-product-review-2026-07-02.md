---
canonical: false
status: active
owner: architecture
last_verified: 2026-07-02
applies_to: definitie-app@v2
---

# Kritische architectuur- & productreview — DefinitieAgent

> Multi-agent review (8 assen + statuscheck vorige review + pip-audit), branch `main` @ `5be6b0cf`, datum 2026-07-02.
> Elke claim met pad:regel. Zware claims door de orchestrator zelf geverifieerd (zie §Verificatie).

## Samenvatting (hoe gezond is de app écht?)

De **kern is fundamenteel gezond**: de laagscheiding UI↔services klopt (0 streamlit-imports in services), de dependency-hygiëne is voorbeeldig (alle kern-pins actueel, 0 CVE's), de kritieke validatie-engine is 78% gedekt, en 24 van de 52 bevindingen uit de vorige review zijn echt gefixt. Maar er is **één acuut incident** — een volledige, werkende OpenAI-key staat sinds november 2025 in vier git-getrackte docs op GitHub — en drie systemische zwakke plekken: het loop-per-call async-model + één gedeelde SQLite-connectie (bron van alle historische deadlocks en de harde multi-user-grens), een god-method `create_definition` die tegen de tech-debt-inspanning in **groeit** (733→~990 regels) en géén hermetische unit-dekking heeft, en een DB die door prompt-duplicatie is opgezwollen tot 168 MB voor 179 definities. De outward-facing documentatie is bovendien zo verouderd dat de aanbevolen start-opdracht (`make dev`) simpelweg faalt.

**Wat dit is:** een AI-app die Nederlandse juridische/overheids-definities genereert en valideert tegen 53 toetsregels, voor **één gebruiker/één developer** (Chris; PRD `docs/prd.md:16`). De kernwaarde — sneller consistente, toetsbare definities dan handmatig — wordt end-to-end geleverd. Het is een echt probleem, geen oplossing-zonder-probleem.

---

## As 1 — Product & functionaliteit

- **[HOOG]** Dode "📝 Bewerk Definitie"-knop na generatie → `st.info("Edit functionality coming soon...")` (`src/ui/components/definition_generator_tab.py:641`), terwijl een volledige Edit-tab als hoofdtab bestaat. Tweede dode knop: "Settings modal coming soon" (`:708`). *Meest natuurlijke vervolgstap in de journey loopt dood.* → Koppel aan bestaande Edit-tab of verwijder.
- **[MIDDEL]** Twee navigatieparadigma's naast elkaar: radio-tabs (`src/ui/tabbed_interface.py:161-183`) én 3 multipage-sidebar-pagina's met eigen `st.set_page_config` (`src/pages/rag_management.py:37`, `synonym_admin.py:47`, `synonym_metrics.py:27`). → Consolideer tot één navigatiemodel.
- **[MIDDEL]** Gepubliceerde stack "Streamlit + FastAPI" overdrijft: de enige FastAPI-app (`src/api/feature_status_api.py:24`) start alleen standalone (`:190-193`), wordt nergens door het product gestart. Het is een dev-status-endpoint, geen product-API. → Herbenoem stack; markeer `api/`+`security/` als dev-tooling.
- **[LAAG]** Scope-sprawl-signalen: lege packages (zie As 4), 745 docs-bestanden.

**Goed:** de kern-journey (invoer → genereren → valideren → score/bronnen/voorbeelden → opslaan → review → export) is echt bedraad, geen mockup; risicoplekken vangen exceptions leesbaar af (`definition_generator_tab.py:398,439,563-570`); duplicaat-check vóór generatie (`tabbed_interface.py:476-484`).

## As 2 — Architectuur

- **[HOOG]** Async-bridge maakt **per aanroep** een verse event loop in een nieuwe thread (`src/ui/helpers/async_bridge.py:35-44`). Dit is de wortel van de historische cross-loop-deadlocks (DEF-429/477 zijn symptoombestrijding); elke nieuwe async-stateful component erft dezelfde valkuil. → Eén langlevende background-loop + `run_coroutine_threadsafe`.
- **[HOOG]** Eén proces-globale SQLite-connectie (`src/database/db_connection.py:29-48`, `check_same_thread=False`, singleton-container `src/utils/container_manager.py:33`) wordt vanuit wisselende worker-threads aangeraakt. WAL + `busy_timeout` dekken multi-*connectie*, niet multi-*thread op één connectie*. *Latente race; niet runtime-gereproduceerd.* → connectie-per-thread of pool.
- **[HOOG]** `create_definition` = 11-fasen god-method van ~990 regels (`src/services/orchestrators/definition_orchestrator_v2.py:315`). Orchestrator bevat fase-logica inline i.p.v. te coördineren. → Fasen naar aparte handlers; loop van ~50 regels.
- **[MIDDEL]** Onbekende hotspot: `ufo_pattern_matcher.py` (1642r) met 100+ regex-patronen hardcoded in een functie van 797r (`:539`) — schendt de eigen regel "validatieregels in config, niet in code" en staat níét in god-object-tracking DEF-421/422/424. → Patronen naar YAML.
- **[MIDDEL]** `interfaces.py` (1293r) mengt kern-datamodel `Definition` (`:217`, geïmporteerd door 40 files) met 6 ABC's → maximale blast-radius. → Split models/interfaces.
- **[MIDDEL]** Naamgeving `DefinitieRepository` (DB) vs `DefinitionRepository` (service) verschilt één letter (verantwoorde anti-corruption-layer, maar verwarrend). → Hernoem DB-laag ondubbelzinnig.

**Goed:** zuivere laagrichting (services/domain kennen UI niet, 0 hits); interface-gedreven DI met centrale container; expliciete `DatabaseConnection.transaction()` met `BEGIN IMMEDIATE` (DEF-391).

## As 3 — Code-kwaliteit (gemeten)

| Metriek | Waarde |
|---|---|
| Ruff-violations buiten C901 | **0** |
| C901-overtreders (>10) | **91** |
| Zwaarste | `create_definition` C901 **56** / ~990r; `_evaluate_json_rule` **53**; `validate_definition` **45** |
| Files >800 regels | **19** (grootste: `definition_edit_tab.py` 1924r) |
| Functies >100 regels | **90** |
| `except Exception` | **512**; bare `except:` **0** |
| Fout-maskerende catch-alls (→`[]`/`False`/`None`) | **84** |

- **[HOOG]** `create_definition` gegroeid 733→~990r sinds de audit — tech-debt neemt hier tóé (`definition_orchestrator_v2.py:315`, DEF-421).
- **[HOOG]** 84 catch-alls maskeren I/O-fouten; write-ops geven `False` waarbij "niets gedaan" niet te onderscheiden is van "mislukt" (`src/services/definition_repository.py` delete/update/hard_delete). → write-ops laten propageren.
- **[MIDDEL]** Twee `DefinitionStatus`-enums in `src/services/interfaces.py` (`:43` én `:157`) — verkeerde import compileert stil. → dedup.
- **[MIDDEL]** Context-keys als string-literal in 42 files; 3 overlappende adapters (`context_adapter.py`/`context_helpers.py`/`components_adapter.py`). → centraliseer via `get_context_dict()`.
- **[MIDDEL]** 10 ongecoördineerde cache-implementaties; UFO-vocabulaire (795r+469r) als code i.p.v. config.

**Goed:** ruff-schoon buiten complexiteit; 0 bare excepts; alle 84 catch-alls loggen wél; sterke transactie-abstractie; 297 pytestmark-markers.

## As 4 — Tech debt & dependencies

Dependency-tabel (geverifieerd tegen PyPI, 2026-07-02): streamlit 1.58.0 **actueel**, openai 2.44.0 **actueel**, pydantic 2.13.4 **actueel**, pandas 3.0.3 **actueel**, anthropic 0.115.0 (1 patch achter), fastapi 0.138.2 (1 minor achter). **Geen CVE's** (pip-audit op requirements.txt én requirements-dev.txt).

- **[HOOG]** Duplicaat-validatorlaag: `src/toetsregels/regels/*.py` (**47**, koppelteken-namen, niet-importeerbaar) naast `src/toetsregels/validators/*.py` (**46**). Loader leest Python alleen uit `validators/` (`json_validator_loader.py:66-72`); uit `regels/` alleen `.json` (de 53 echte regels). De 47 `regels/*.py` zijn dood/duplicaat. *Wijzigingen kunnen in het dode bestand landen.* → verifieer + verwijder `regels/*.py`.
- **[MIDDEL]** Dode legacy-shim `src/orchestration/definitie_agent.py` (186r, "compatibility shim", 0 importeurs).
- **[MIDDEL]** 6 orphaned config-YAML's nergens bij naam geladen (`config/monitoring.yaml`, `cache_config.yaml`, `ufo_rules.yaml`+`_v5.yaml`, `logging_structured.yaml`; `logging_config.yaml` vóór verwijdering verifiëren — mogelijk PII-gerelateerd).
- **[LAAG]** `|| true` op de integration-CI-job (`test.yml:152,157`, bewust tot DEF-429); ruff/coverage-`|| true` zijn wél weg (DEF-466).

**Goed:** `.in`→`make lock`-workflow met hashes is voorbeeldig; `type: ignore` spaarzaam (28, geen bestand >3); `opschoning/ontologie/integration/monitoring` zijn — anders dan op naam vermoed — **wél in gebruik** (4-6 imports elk). Alleen `analysis/`, `reports/`, `cache/` zijn echt leeg (onschuldig).

## As 5 — Tests & betrouwbaarheid (gemeten: 297 files, 2533 unit-tests, 0 collect-errors)

- **[KRITIEK]** Het kritieke generatiepad heeft **géén hermetische unit-dekking**: `definition_orchestrator_v2.py` = **26%** (regels 810-1254 volledig ongedekt); alle 6 orchestrator-tests staan onder `tests/integration/` en doen echte API-calls → hangen zonder key → draaien de facto nooit in de unit-gate. *De duurste code mergt ongebewaakt groen.* → mock `AsyncAIClient`, unit-test de orchestratielogica.
- **[HOOG]** 7 assert-loze "print-tests" in `tests/unit/` tellen groen mee zonder iets te bewijzen (`test_env.py` print zelfs een stuk API-key `:13`, `test_ui_scores.py`, `test_csv_import_websocket.py` e.a.). → asserts of naar `tests/manual/`.
- **[HOOG]** asyncio-run-in-Streamlit-risicopaden hebben 0 directe tests (`synonym_admin.py`, `async_progress.py`, `regeneration_handler.py` = 0%).
- **[HOOG]** UI-laag: 80 modules op 0% (`definition_edit_tab.py` 6%, `expert_review_tab.py` 5%).
- **[MIDDEL]** DB-schrijf/transactielaag dun: `db_connection.py` 25% (juist de `transaction()`-logica missend), `migrate_database.py` 14%.

**Goed:** volwassen infra (`--strict-markers`, `xfail_strict`, `pytest-timeout=120`); hermetische env (`conftest.py:316`); validatie-engine 78%; repository-swallow-contract is getest; 0 flaky-markers.

## As 6 — Security & privacy

- **[KRITIEK — ECHT, fix nu]** Volledige werkende OpenAI-key in git-getrackte docs sinds nov 2025: `docs/analyses/CONFIG_ENVIRONMENT_MASTERPLAN.md:143` (177 tekens, niet-getrunct) + getruncte varianten in `SECURITY_AUDIT_REPORT.md`, `CONFIG_ENVIRONMENT_VERIFICATION_REPORT.md`, `MASTER_IMPROVEMENT_PLAN.md`. Repo staat op GitHub → iedereen met read-access heeft een werkende key. → **(1) key nu revoken; (2) 4 docs redigeren; (3) history scrubben met `git filter-repo` + force-push** (patroon = ADHD-PII-incident).
- **[MIDDEL lokaal / HOOG bij uitrol]** FastAPI: CORS `*`, bind `0.0.0.0`, geen auth (`feature_status_api.py:94,193`). Verzacht: API draait nergens automatisch, serveert alleen projectstatus. Streamlit zelf luistert ook zonder auth op alle interfaces → uitrol-blocker.
- **[LAAG→MIDDEL]** XML-parsing van externe SRU/rechtspraak-feeds via stdlib-ElementTree (`sru_service.py:279,787,931`) — geen entity-expansion-bescherming. → `defusedxml`.
- **[LAAG]** PII-filter (`logging_filters.py`) dekt gelabelde patronen maar geen vrije-tekst-PII in definitie-teksten; file-handler logt op DEBUG. Lokaal, `logs/` gitignored.
- **[LAAG]** Externe AI-verzending (definities/documenten → OpenAI/Anthropic VS) niet AVG-gedocumenteerd.

**Goed:** SQL volledig geparametriseerd + allowlist voor dynamische UPDATE (`definitie_crud.py:210-241`); geen pickle (JSON+HMAC); snippet-sanitization vóór prompt (`prompt_service_v2.py:324,443`); CSV gehard; geen echte hardcoded keys in `src/`; gitleaks-hook actief.

## As 7 — Performance & schaalbaarheid

- **[HOOG]** DB-bloat: **168 MB voor 179 definities**; tabel `definitie_voorbeelden` = 142 MB doordat `generation_parameters` de **volledige prompt-template per rij** opslaat (AVG 41 KB/rij, gemeten via dbstat). → sla alleen model+params op; migratie + VACUUM.
- **[KRITIEK bij 10x / MIDDEL nu]** Eén gedeelde SQLite-connectie serialiseert álle toegang + interleaving-risico bij threads (zie As 2). Eerste hard breekpunt bij multi-user.
- **[MIDDEL]** `run_async` bouwt per call nieuwe loop+thread → async AI-client-pool niet hergebruikt → TLS-handshake per generatie.
- **[MIDDEL]** `@cached`-regels worden per call van **disk** gelezen (FileCache), niet uit memory — docstring-claim "uit memory" klopt niet (`rule_cache.py:30` + `cache.py:101-119`).

**Goed:** de oude README-claims (6x init/20s startup/45x herladen) zijn op HEAD **weerlegd** — caching via `@st.cache_resource` + singleton is opgelost; goede SQLite-pragmas (WAL/NORMAL/busy_timeout); dekkende indexes; prompt hard begrensd op 10k tokens; caches begrensd (LRU/TTL, geen lek).

## As 8 — Onderhoudbaarheid & DX

- **[KRITIEK]** `make dev` is **stuk**: `Makefile:7` roept `bash scripts/run_app.sh` — dat bestaat niet (echte pad: `scripts/deployment/run_app.sh`). De aanbevolen start-opdracht faalt direct. → fix pad.
- **[KRITIEK]** README beschrijft een verkeerd product: "GPT-4" (is gpt-5.2/claude), "45 regels" (is 53), "919 tests" (is 3112), "Python 3.11" (is 3.13), "we laden geen .env" (wordt wél geladen, `main.py:19`). → herschrijf tot dunne geverifieerde kern.
- **[HOOG]** Dode script/doc-verwijzingen in README (`scripts/test_web_lookup.py`, `ai_code_reviewer.py` e.a. bestaan niet); zelf-tegensprekende `.env`-instructie (`README.md:117` vs `:145`).
- **[MIDDEL]** Toetsregels-bron verkeerd gedocumenteerd: CLAUDE.md/memory noemen `toetsregels_config.yaml` "single source of truth", maar dat is de **loader-config** die naar `src/toetsregels/regels/*.json` (de 53 echte regels) wijst. *Wie een regel wil wijzigen zoekt op de verkeerde plek.*
- **[MIDDEL]** Near-duplicate docs-mappen (`analyse`/`analyses`/`analysis`, `implementation`/`implementations`/`implementation-plans`).

**Goed:** CLAUDE.md + memory zijn accuraat en actueel (dáár leeft de echte kennis); requirements gelockt/hashed; 15 CI-workflows + 13 pre-commit hooks; Makefile-targets overigens correct.

---

## Status vorige review (24 juni, 52 bevindingen)

**24 GEFIXT · 2 DEELS · 26 OPEN** (open: 1 kritiek, 12 hoog, 10 middel, 3 laag). De DEF-469-opruiming van stille failures was grondig. Nog open, zwaarst:
1. **#46 KRITIEK** proces-globale `_SERVICE_ADAPTER_CACHE` (`service_factory.py:33`) — multi-user session-leak.
2. **#4/#5 HOOG** race in edit-tab auto-load (geen early-return, widget-key-mismatch → data-verlies-risico).
3. **#34 HOOG** ongesanitized RAG `chunk_text` (`prompt_service_v2.py:235`) — prompt-injection-pad (web/document wél gesanitized, RAG niet).
4. **#35/36/39/40 HOOG** LLM-JSON-parsing zonder guards in `ontological_classifier.py` — 4 open bevindingen in één bestand.
5. **#18 HOOG** delete meldt success bij falen; **#21** version-history `[]` bij DB-fout.

---

## Verificatie (orchestrator, niet blind vertrouwd op agents)

Zelf bevestigd: `make dev`-pad stuk (`scripts/run_app.sh` ontbreekt, `scripts/deployment/run_app.sh` bestaat); DB 168 MB; "coming soon"-knoppen (`definition_generator_tab.py:641,708`); validatorlaag 47 `.py` + 46 `.py` + 53 `.json`; gelekte key-prefix in 4 git-getrackte docs (regel 143 = 182 tekens); pip-audit 0 CVE's op beide requirements. **Opgeloste tegenstrijdigheid:** As 1 nam aan dat `make dev` werkt; As 8 + eigen check tonen dat het stuk is — As 8 heeft gelijk. As 4 weerlegt As 1's vermoeden dat `opschoning/ontologie/monitoring/integration` dood zijn (wél in gebruik).

## Top 5 prioriteiten

1. **OpenAI-key revoken + uit git-history scrubben** — *quick win* (revoke = minuten) + *groter project* (history-scrub). Acuut, financieel risico, staat remote op GitHub.
2. **`make dev` fixen + README herschrijven tot geverifieerde kern** — *quick win*. Eén-regel-fix in Makefile + README-sanering; herstelt onboarding onmiddellijk.
3. **Hermetische unit-tests voor `create_definition`** (mock AI-client) — *groter project*. De duurste, meest kritieke code is nu ongebewaakt in de gate.
4. **DB-bloat migreren** (prompt-template uit `generation_parameters`) + VACUUM — *quick win* qua concept, *middel* qua migratie. 168→~5 MB.
5. **Async+DB-fundament**: langlevende event-loop + connectie-per-thread — *groter project*. Lost de systemische bron van deadlocks op en is de voorwaarde voor élke multi-user-ambitie; sluit #46 (kritiek open) mee af.
