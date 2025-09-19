---
canonical: true
status: draft
owner: QA Lead
last_verified: 2025-09-19
applies_to: definitie-app@current
---

# Test Suite Improvement Plan

Doel: de testsuite versnellen, stabiliseren en moderniseren richting de v2‑architectuur met duidelijke CI‑profielen, dekkingsdoelen en gefaseerde afbouw van legacy paden.

## Samenvatting
- PR‑suite toont nog brede failures in integratie en legacy‑tests; unit/services + toegevoegde prompt/web‑lookup/mappers tests draaien groen.
- Coverage (unit+services+smoke): ~35% op `src`. Prompts/orchestrator v2 hebben hoge dekking; legacy paden vallen op door zeer lage of nul dekking.
- Directe verbeteringen toegepast:
  - Centrale Streamlit‑mock uitgebreid; builtins‑compat helpers voor config adapters.
  - Caching utilities robuuster (decorator werkt met mocks; persist‑fouten degraderen niet).
  - Netwerk in tests standaard geblokkeerd (override met `ALLOW_NETWORK=1`).
  - Runner script met profielen: `fast`, `pr`, `full`, `perf`.

## Huidige Stand (bevindingen)
- Veel integratietests verwachten legacy symbolen/paden (bijv. `ai_toetser.validators`), of methoden die in v2 (nog) niet bestaan.
- Config‑tests verwachten environment‑afhankelijke defaults (temperatuur) die afwijken van de huidige implementatie.
- Sanitizer/validators hebben strengere of afwijkende semantiek dan tests aannemen (bijv. `<script>` stripping, path‑sanitization).

## Aanbevelingen
- Snelle feedback
  - Gebruik profielen:
    - `./scripts/run_tests.sh fast` (on push: smoke + unit + services)
    - `./scripts/run_tests.sh pr` (on PR: + integration + contracts, zonder performance)
    - `./scripts/run_tests.sh full` (nightly)
    - `./scripts/run_tests.sh perf` (performance/benchmark)
  - Optioneel: pytest‑xdist (`-n auto`) op snelle suites.
- Stabiliteit & determinisme
  - Netwerk dicht (al geblokkeerd); expliciet openen met `ALLOW_NETWORK=1` voor specifieke integraties.
  - pytest‑randomly toevoegen om volgorde‑afhankelijkheid te vangen.
  - Markeer echt trage of timing‑gevoelige tests met `@pytest.mark.slow` (standaard uitgesloten).
- Coverage
  - Start budget: `--cov-fail-under=40` → 50% → 60% (gefaseerd). Subpakket‑doelen: prompts ≥80%, services/validation ≥70%, web_lookup ≥80%.
  - Verhoog dekking gericht: prompt‑modules (con/ess/arai/ver), services/validation (edge cases ensure_schema_compliance), web_lookup (suggestions/SRU‑parse met mocks).
- CI‑profielen
  - On push: fast
  - On PR: pr (zonder perf)
  - Nightly: full + perf; coverage rapportage
- Documenteer beleid in `docs/testing/TESTING_GUIDE.md` (bijgewerkt) en houd netwerk policy expliciet.

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
- ai_toetser legacy entry points:
  - Tests verwachten `ai_toetser.validators` (bestaat niet). Wel aanwezig: `ai_toetser/{modular_toetser,toetser}.py`.
  - Actie: shim module of tests migreren naar v2.
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
   - Mocks consolideren (Streamlit, config builtins). Sanitizer aanscherpen (<script> strippen).
   - Shim of skips voor legacy imports (ai_toetser.validators) om PR‑suite niet te blokkeren.
2) Triage/markering
   - Verplaats pure legacy tests naar `tests/legacy/` of markeer `xfail` met rationale.
   - Sluit `tests/legacy/` uit in PR‑suite; run in nightly.
3) Implementatie/alignering
   - Leveren van minimale v2‑interfaces waar tests om vragen (validation schema/dutch validator) of tests aligneren naar v2.
   - Config‑env gedrag expliciteren en tests bijwerken naar v2‑defaults.
4) Cleanup
   - Deprecated bestanden verplaatsen naar `archive/legacy/` (of verwijderen) zodra referenties zijn gemigreerd.
   - Dekkingsbudgets en CI‑gates gefaseerd opschroeven.

## Taken (suggestie)
- [ ] Legacy Map definitief maken met bron→doel + owners
- [ ] Pytest markers/xfail voor legacy tests
- [ ] Shim `ai_toetser/validators` (optioneel) of testmigratie
- [ ] Sanitizer consistentie (moderate/strict strip `<script>`)
- [ ] CI‑workflows met profielen
- [ ] Coverage budgets initialiseren en bijsturen

## Bijlagen
- Runner: `./scripts/run_tests.sh {fast|pr|full|perf}`
- Netwerkpolicy: standaard geblokkeerd; override met `ALLOW_NETWORK=1`.
- Markers: `unit`, `integration`, `contract`, `regression`, `performance`, `benchmark`, `acceptance`, `red_phase`, `antipattern`.

