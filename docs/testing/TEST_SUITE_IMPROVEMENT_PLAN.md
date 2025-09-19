canonical: true
status: active
owner: QA Lead
last_verified: 2025-09-19
applies_to: definitie-app@current
---

# Test Suite Improvement Plan (Gealigneerd met huidige implementatie)

Doel: de testsuite versnellen, stabiliseren en moderniseren richting de v2‑architectuur met duidelijke CI‑profielen, consistente dekkingsdoelen en gefaseerde afbouw van legacy paden — in lijn met de huidige stand van de code en tests.

## Samenvatting
- PR‑suite toont nog brede failures in integratie en legacy‑tests; unit/services + toegevoegde prompt/web‑lookup/mappers tests draaien groen.
- Coverage (unit+services+smoke): ~35% op `src`. Prompts/orchestrator v2 hebben hoge dekking; legacy paden vallen op door zeer lage of nul dekking.
- Directe verbeteringen toegepast:
  - Centrale Streamlit‑mock uitgebreid; builtins‑compat helpers voor config adapters.
  - Caching utilities robuuster (decorator werkt met mocks; persist‑fouten degraderen niet).
  - Netwerk in tests standaard geblokkeerd (override met `ALLOW_NETWORK=1`).
  - Runner script met profielen: `fast`, `pr`, `full`, `perf`.

## Huidige Stand (bevindingen)
- Integratie-/unit‑tests verwachten deels legacy importpaden (bijv. `ai_toetser.validators`), of symbolen die (nog) niet bestaan in de V2 structuur.
- Config‑tests veronderstellen environment‑afhankelijke defaults die afwijken van de huidige implementatie.
- Sanitizer/validators hanteren strengere/afwijkende semantiek dan sommige tests aannemen (o.a. `<script>`‑stripping, normalisatie).
- Markers en coverage‑doelen zijn niet uniform geconfigureerd tussen gids/plan/CI.

## Aanbevelingen (geconcretiseerd)
- Snelle feedback & profielen (convergeren met bestaande runner):
  - Gebruik `./scripts/run_tests.sh` profielen eenduidig:
    - `fast` (push): smoke + unit + services, `-m "not performance and not slow"`.
    - `pr` (pull_request): unit + services + integration + contracts (geen performance).
    - `full` (nightly): volledige suite (excl. performance tenzij expliciet).
    - `perf` (nightly/handmatig): performance/benchmark suites.
  - Optioneel: pytest‑xdist (`-n auto`) voor `fast`/`pr` zodra stabiliteit bevestigd is.
- Stabiliteit & determinisme
  - Netwerk dicht (actief in conftest); expliciet openen met `ALLOW_NETWORK=1`.
  - Voeg `pytest-randomly` toe om volgorde‑afhankelijkheid te detecteren; herstel gevonden issues iteratief.
  - Markeer trage/timing‑gevoelige tests met `@pytest.mark.slow` en sluit ze uit in `fast/pr`.
- Coverage (geharmoniseerd met praktijk en CI)
  - PR‑suite: overall `--cov=src --cov-fail-under=60`, plus subpakket‑gate voor services `--cov=src/services --cov-fail-under=80` (zoals CI al afdwingt).
  - Nightly: verhoog overall naar 65–70; subpakketten: prompts ≥80%, services/validation ≥80%, web_lookup ≥80%.
  - Verhoog dekking gericht: prompt‑modules (con/ess/arai/ver), services/validation (edge‑cases `ensure_schema_compliance`), web_lookup (suggestions/SRU‑parse met mocks).
- CI‑profielen (te implementeren)
  - push: `fast`
  - pull_request: `pr` (zonder perf; met contract/JSON‑schema checks)
  - nightly: `full` + `perf`; coverage‑rapportage.
  - Let op: workflow laat `scripts/run_tests.sh` aanroepen i.p.v. inline pytest‑commando’s.
- Documenteer beleid in `docs/testing/TESTING_GUIDE.md` (geüpdatet) en houd netwerkpolicy expliciet.

## Preflight & Approval Gates (AGENTS‑conform)

Voor elke significante wijziging (verplaatsen/verwijderen van legacy paden; >50 regels of >3 files) voeren we preflight‑checks en approval‑gates uit:

- Preflight checks (uit te voeren vóór patch):
  - Unieke match: `rg "exact_string_to_change" --files-with-matches | wc -l` (verwacht 1)
  - Scope/impact: lijst paden + componenten met impact
  - Forbidden patterns:
    - Services: geen `from ui.*`, geen `asyncio.run(`
    - UI: geen directe repository‑imports (gebruik service‑facade)
  - Automatisch: `~/.ai-agents/preflight-checks.sh .`

- Approval Ladder (wanneer vragen):
  - Code patches >100 regels of >5 files: approval nodig
  - Verwijderen/archiveren van paden in kritieke directories: approval nodig + rollbackplan
  - Dependencies/schema‑wijzigingen: approval nodig
  - Netwerk/deps install: approval nodig

## Strict Mode & Beslissingslog

Gebruik strict‑mode toggles om aannames te voorkomen tijdens migratie:

- `/strict on patch,test` — blokkeer patches/tests tot expliciet `/approve`
- `/strict off` — deactiveer strict‑mode
- `/approve` — volgende geblokkeerde stap
- `/deny` — afwijzen; herplan/alternatief voorstellen

Houd per fase een korte decisions‑log bij (beslissing, motivatie, akkoordmoment).

## Naming & Import Canon (AGENTS)

Volg de verplichte namen en verboden import‑patronen (uit `docs/guidelines/AGENTS.md`):

- Verplicht (voorbeeld): `ValidationOrchestratorV2`, velden `organisatorische_context`, `juridische_context`.
- Verboden in `src/services/`: `from ui.*`, `asyncio.run(...)`.
- UI gebruikt service‑facades i.p.v. repository‑imports.

Bij migraties: pas tests en paden aan om aan deze canon te voldoen.

## Canonical Locations & Archivebeleid

- Houd één bron van waarheid voor actieve code (zie `docs/CANONICAL_LOCATIONS.md`).
- Legacy/dead code krijgt een quarantaineplek (bijv. `archive/legacy/`), met README (reden, end‑of‑life, vervangende paden).
- Werk documentatie/links bij en blokkeer nieuwe imports naar legacy via lint/gates.

## Legacy Tests Scope

- Verplaats pure legacy tests naar `tests/legacy/` (niet langer stilzwijgend overslaan via collection‑filters).
- Sluit `tests/legacy/` uit in `fast/pr`; draai in `full/nightly`.
- Markeer resterende legacy‑afhankelijke tests als `xfail` met motivatie totdat de V2‑variant klaar is (transparantie in rapportage).

## Degraded Modes (Cache & Netwerk)

- Cache: bij metadata/persist‑fouten degradeert `FileCache.set()` niet (return True) en wordt het probleem gelogd. Dit is een bewust “degraded mode” besluit om tests niet te blokkeren; herzien zodra cache‑persist kritisch wordt.
- Netwerk: standaard geblokkeerd in tests (override met `ALLOW_NETWORK=1`).

## Legacy/Dead Paths – Inventaris

Criteria:
- 0–10% coverage, geen inkomende imports in suite, vervangen door v2‑varianten, of niet headless testbaar.

Helder v2 (houden/tests uitbreiden):
- Orchestrator v2: `src/services/orchestrators/validation_orchestrator_v2.py`
- Prompts modules + orchestrator: `src/services/prompts/modules/*`
- Modern web lookup: `src/services/modern_web_lookup_service.py` + `services/web_lookup/{ranking,sanitization}.py`
- Validation contract/mappers: `src/services/validation/{interfaces,mappers}.py`
- Config adapters: `src/config/{__init__,config_adapters}.py`

Kandidaten legacy/dead (quarantaine/deprecate):
- Validation (legacy):
  - `src/validation/{definitie_validator,dutch_text_validator,input_validator}.py`
  - `src/security/security_middleware.py`
  - Actie: deprecate t.b.v. `src/services/validation/*`; markeer tests als legacy of update naar v2.
- Legacy orchestrators/services:
  - `src/services/{definition_orchestrator,definition_workflow_service,ai_service,ab_testing_framework,feature_flags}.py`
  - Actie: deprecated; importpaden migreren naar v2; daarna verwijderen/archiveren.
- ai_toetser validators API:
  - Diverse tests verwachten `ai_toetser.validators` (bestaat niet). Wel aanwezig: `ai_toetser/{modular_toetser,toetser}.py` en JSON‑validatoren onder `toetsregels/validators`.
  - Actie (kortetermijn): introduceer een lichte shim `ai_toetser/validators` die types/exports aanbiedt of update tests naar JSON‑loader/V2‑services.
  - Actie (langetermijn): consolideer op V2‑importpaden en verwijder shim zodra tests gemigreerd zijn.
- Web lookup contracts/provenance (lage dekking):
  - `src/services/web_lookup/{contracts,provenance}.py`
  - Actie: aligneren met feitelijke API of verplaatsen naar docs/tools.
- Domein prototypes/external adapters:
  - `src/external/external_source_adapter.py`, `src/domain/{juridisch,linguistisch}/*`
  - Actie: archive/legacy/, tenzij hard referenties.
- Voorbeelden/* (oude flows):
  - `src/voorbeelden/*`
  - Actie: check UI‑gebruik; anders deprecate/archiveren.
- Tools/CLI (geen tests):
  - `src/tools/{definitie_manager,setup_database}.py`, `src/main.py`
  - Actie: verplaatsen naar tools/cli, uit runtime pad.
- UI (groot, 0% unit coverage):
  - `src/ui/components/*.py`, `src/ui/tabbed_interface.py`
  - Actie: niet verwijderen; teststrategie aanpassen (smoke/gated, services scheiden voor unit‑tests).

## Migratieplan
1) Quick wins
   - Markers uniformeren in `pytest.ini` (unit, integration, contract, smoke, regression, performance, benchmark, acceptance, red_phase, antipattern).
   - Mocks consolideren (Streamlit, config builtins) — is grotendeels gereed.
   - Shim of testmigratie voor legacy imports (`ai_toetser.validators`) om PR‑suite niet te blokkeren.
2) Triage/markering
   - Verplaats pure legacy tests naar `tests/legacy/` en markeer `xfail` met rationale.
   - Sluit `tests/legacy/` uit in `fast/pr`; run in `full/nightly`.
3) Implementatie/alignering
   - Leveren van minimale V2‑interfaces waar tests om vragen (validation schema/dutch validator) of tests aligneren naar V2.
   - Config‑env gedrag expliciteren; tests bijwerken naar V2‑defaults.
   - Pas `tests/ci/test_forbidden_symbols.py` aan: vervang file‑verboden door inhoudelijke pattern‑checks en een expliciete allowlist.
4) Cleanup
   - Deprecated bestanden verplaatsen naar `archive/legacy/` (of verwijderen) zodra referenties zijn gemigreerd.
   - Dekkingsbudgets en CI‑gates gefaseerd opschroeven; adopteer `scripts/run_tests.sh` in workflows.

## Taken (suggestie)
- [ ] Legacy Map definitief maken met bron→doel + owners
- [ ] Pytest markers/xfail voor legacy tests en aanmaak `tests/legacy/`
- [ ] Shim `ai_toetser/validators` (kortetermijn) of testmigratie naar V2‑importpaden
- [ ] Sanitizer consistentie (moderate/strict strip `<script>`)
- [ ] CI‑workflows laten aanroepen: `scripts/run_tests.sh {fast|pr|full|perf}`
- [ ] Coverage‑budgets harmoniseren (PR: overall 60 + services 80; nightly hoger)
- [ ] Voeg `pytest-randomly` toe; evalueer optioneel `pytest-xdist`

## Bijlagen
- Runner: `./scripts/run_tests.sh {fast|pr|full|perf}`
- Netwerkpolicy: standaard geblokkeerd; override met `ALLOW_NETWORK=1`.
- Markers (uniformeren in pytest.ini): `unit`, `integration`, `contract`, `smoke`, `regression`, `performance`, `benchmark`, `acceptance`, `red_phase`, `antipattern`.
