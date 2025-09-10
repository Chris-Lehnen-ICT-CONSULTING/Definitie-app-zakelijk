**EPIC-012 Code Audit — DefinitieAgent**

- Datum: 2025-09-10
- Scope: Volledige repo onder `src/` + top-level scripts/configs
- Doel: Identificeer dubbelingen, conflicten, refactor-kansen en technische schuld ter onderbouwing van EPIC-012

**Executive Summary**

- De codebase bevat zowel V1- als V2-architectuur in parallel (orchestrators, AI-services, validatie, UI-adapters). Dit levert dubbele paden, inconsistenties en hogere onderhoudslast op.
- Belangrijkste conflicten: twee orchestrators (legacy vs V2), twee AI-services (sync vs async), dubbele export-root (`export/` en `exports/`), mixed UI-afhankelijkheid in services, en .env-load in AI-service i.c.m. “geen .env” in main.
- Grootste refactor-waarden: standaardiseer op V2-architectuur (orchestrator, AI, prompts, validation), sane package imports (weg met `sys.path` hacks), één export-pad, één resilience-implementatie, en JSON-gedreven validators met gedeelde basisklasse.
- Quick wins: opruimen ongebruikte directories/files, verwijderen dubbele/legacy shims waar V2 beschikbaar is, rectificeren importpaden, uniformeren configuratiebron (env/YAML), en het isoleren van Streamlit-uit UI-laag.

**Architectuur & Structuur (observaties)**

- Orchestration
  - V1: `src/services/definition_orchestrator.py` en monolithische `src/orchestration/definitie_agent.py` (legacy adapter/flow).
  - V2: `src/services/orchestrators/definition_orchestrator_v2.py` (stateless 11-fasen flow), plus validation orchestrator en prompt-service modules.
  - Beide paden bestaan en worden (in)direct gebruikt via `services/service_factory.py` met feature flags/adapters.
- AI Services
  - V1: `src/services/ai_service.py` (sync OpenAI client, `load_dotenv()`, legacy compat `stuur_prompt_naar_gpt`).
  - V2: `src/services/ai_service_v2.py` (native async, caching, rate limiting integratie).
- Validatie
  - “Toetsregels” ecosysteem: JSON + bijbehorende Python validators per regel (bijv. `STR-01.json` + `validators/STR_01.py`).
  - Extra validatie-laag: `src/validation/definitie_validator.py` interpreteert regels voor scoring/violations.
  - V2 validation modules in `src/services/validation/*` (interfaces, modular service, mappers).
- UI
  - Streamlit UI met `src/ui/tabbed_interface.py`, componenten `src/ui/components/*`, en state manager `src/ui/session_state.py`.
  - Services lekkken Streamlit-afhankelijkheid (bijv. `services/service_factory.py` gebruikt `streamlit as st`).
- Export
  - `src/export/export_txt.py` met service-coördinatie in `src/services/export_service.py`.
  - Losse lege/legacy map `src/exports/` (lijkt ongebruikt).
- Config
  - Gecentraliseerd: `src/config/config_manager.py` (YAML + env overrides).
  - Conflicterend: `src/services/ai_service.py` doet `load_dotenv()` terwijl `src/main.py` expliciet aangeeft geen `.env` te laden.
- Overig
  - Resilience: meerdere varianten (`utils/resilience.py`, `optimized_resilience.py`, `integrated_resilience.py`, `resilience_summary.py`).
  - “External sources” UI gebruikt `sys.path` injectie om `external_source_adapter` te importeren i.p.v. package import.
  - Test-bestand in bronboom: `src/hybrid_context/test_hybrid_context.py` (testcode gemengd met productiecode).

**Conflicten en Inconsistenties**

- Dubbele orchestrators (V1 vs V2)
  - V1 `definition_orchestrator.py` en `orchestration/definitie_agent.py` vs V2 `orchestrators/definition_orchestrator_v2.py`.
  - `service_factory.py` houdt beide paden in leven; verhoogt complexiteit en risico.
- Dubbele AI-services
  - `ai_service.py` (sync, dotenv) tegenover `ai_service_v2.py` (async, rate-limit aware). Beiden worden nog aangeroepen.
- Config bron en .env-belasting
  - `main.py` zegt “geen .env-bestand laden”; `ai_service.py` doet `load_dotenv()`. Inconsistent deploymentgedrag.
- Export pad verdubbeling
  - `src/export/` is actief; `src/exports/` bestaat maar lijkt ongebruikt → verwarrend voor tooling/imports.
- Streamlit in services
  - `service_factory.py` gebruikt `st.session_state` (UI-lek in services-laag).
- Import pad hacks
  - `ui/components/external_sources_tab.py` voegt `external/` aan `sys.path` toe en importeert modulair zonder package namespace.
- Mixed sync/async paden
  - V1 code draait sync-oproepen in event loops of threads; V2 is async-first. Er zijn meerdere plekken met `asyncio.run_coroutine_threadsafe` en `run_until_complete` wrappers.
- Duplicerende validatielogica
  - Toetsregel-validators (per regel Python + JSON) naast de generieke `validation/definitie_validator.py` én de V2 validation orchestrator. Overlap vergroot onderhoud.
- Script verwijzingen zonder tests
  - `run_smoke_tests.sh` verwijst naar `tests/smoke/test_validation_v2_smoke.py` die niet in repo staat.

**Dubbelingen (selectie)**

- Orchestrators: V1 monolith + V1 service + V2 orchestrator.
- AI: `ai_service.py` en `ai_service_v2.py` leveren vergelijkbare functionaliteit.
- Resilience utils: `resilience.py`, `optimized_resilience.py`, `integrated_resilience.py`, `resilience_summary.py` – overlappende verantwoordelijkheden.
- Validators: voor veel regels bestaan én JSON-spec én Python-validator met vrijwel identieke fabriekspatronen en returnvormen.
- Export mappen: `export/` vs `exports/`.

**Technische Schuld (belangrijkste punten)**

- Legacy shims en dubbele paden blijven actief, wat de codebase complex maakt (feature flags, adapters, legacy compat-klassen).
- UI-lekken in service-laag (hard dependency op Streamlit in `service_factory.py` en diverse modules die direct `st.session_state` benaderen via adapters).
- Inconsistente configuratiebron (env vs YAML vs dotenv), risico op afwijkend gedrag tussen omgevingen.
- Import-hacks (handmatig `sys.path` manipuleren) i.p.v. correcte module-namespaces.
- Tests vermengd met broncode (`src/hybrid_context/test_hybrid_context.py`).
- Ongebruikte/lege directories en bestanden (bijv. `src/exports/`, `CLAUDE.md` voor build irrelevant).

**Refactorvoorstellen (EPIC-012)**

- Standaardiseer op V2-architectuur
  - Maak `DefinitionOrchestratorV2` de enige orchestrator; plan gefaseerde uitfasering van `definition_orchestrator.py` en `orchestration/definitie_agent.py`.
  - Convergeer AI-calls naar `AIServiceV2` (async); verwijder of shim `ai_service.py` enkel als dun compatibiliteitslaag zonder `dotenv`.
  - Prompts en validatie via V2-services (`services/prompts/*`, `services/validation/*`).
- Strict layering en decoupling
  - Verwijder Streamlit-afhankelijkheid uit services: verplaats UI toggles/feature flags naar UI-laag. Services consumen enkel contracten uit `services/interfaces.py`.
  - Vervang `sys.path`-injecties door correcte package imports (bijv. `from external.external_source_adapter import ...`) en zorg dat `src/external` een echt package is.
- Config-unificatie
  - Eén bron van waarheid: `config_manager` (YAML + env overrides). Verwijder `load_dotenv()` en documenteer env-keys.
  - Valideer config bij start-up en faal vroeg bij ontbrekende secrets in non-dev.
- Validators consolideren
  - Introduceer een gedeelde basisklasse/utility voor validators en laat per-regel-Python classes generiek JSON-driven zijn (minder boilerplate, 1 codepad voor create_validator()).
  - Overweeg om waar mogelijk alleen JSON + generieke validator te houden; per-regel Python enkel voor afwijkende logica.
- Exports consolideren
  - Behoud `src/export/`, verwijder `src/exports/`. Centraliseer export-API in `services/export_service.py`.
- Resilience-utilities consolideren
  - Kies één robuuste implementatie (bijv. `integrated_resilience.py`) en absorbeer functionaliteit uit de overige bestanden; voeg documentatie/tests toe.
- Repo-hygiëne
  - Verplaats testbestanden naar `tests/`, maak `src` vrij van test-code. Corrigeer `run_smoke_tests.sh` of verwijder wanneer niet in gebruik.
  - Opruimen legacy/unused modules en losse docs die niet in build/deploy horen.

**Kandidaat Deletions/Consolidations (veilig gefaseerd)**

- Orchestrators
  - Deprecate: `src/services/definition_orchestrator.py`, `src/orchestration/definitie_agent.py` (na UI/flows migratie naar V2).
- AI
  - Deprecate: `src/services/ai_service.py` → vervang gebruik door `AIServiceV2` en optionele dunne compat wrapper zonder `dotenv`.
- Export
  - Remove: `src/exports/` map (lijkt ongebruikt). Valideer geen referenties in code (huidig none).
- Resilience
  - Merge: `resilience.py`, `optimized_resilience.py`, `integrated_resilience.py` → 1 module + samenvattingsrapport in `resilience_summary.py`.
- Tests in `src`
  - Move: `src/hybrid_context/test_hybrid_context.py` → `tests/hybrid_context/test_hybrid_context.py`.
- External import
  - Fix: gebruik package imports `external.external_source_adapter` en voeg `__init__.py` toe indien nodig; verwijder `sys.path`-manipulatie.

**Risico’s & Gaps om te adresseren**

- Mixed async/sync: UI en services moeten een duidelijke async-grens hebben; voorkom nested event loops en threadfutures waar niet strikt nodig.
- Validatie-overlap: definieer één bron van “violations” en score (V2 contract), en map legacy alleen aan UI-randen.
- Config en secrets: zonder `.env`-load in prod zijn env-secrets verplicht; documenteer CI/CD variabelen en fail-fast.
- Monitoring en smoke tests: script verwijst naar niet-bestaande tests; herstel teststructuur of verwijder scripts om verwarring te voorkomen.

**Quick Wins (laag risico, hoge waarde)**

- Verwijder `load_dotenv()` uit `services/ai_service.py` of markeer module deprecated en migreer aanroepen naar V2.
- Verwijder `src/exports/` en update README/links.
- Vervang `sys.path`-injectie in `ExternalSourcesTab` door package import; maak `src/external` een volwaardig package.
- Centraliseer Streamlit toggles in UI; verwijder `st.session_state` gebruik uit `services/service_factory.py` (laat UI de adapter/config construeren).
- Voeg lint/CI check die voorkomt dat tests in `src/` blijven liggen.

**Specifieke Bevindingen (selectie per bestand/groep)**

- `src/main.py`
  - Zet Streamlit-config en start Tabbed UI. Opmerking in code zegt geen `.env` laden; conflicteert met `ai_service.py`.
- `src/services/definition_orchestrator.py` (V1)
  - Async orchestratie met inline promptbouw + AI-call; bevat cleaning/validation/save; overlapt met V2, verhoogt onderhoudslast.
- `src/services/orchestrators/definition_orchestrator_v2.py` (V2)
  - Heldere 11-fase flow, afhankelijk van interfaces (Prompt, AI, Validation, Cleaning). Aanrader als standaard.
- `src/services/ai_service.py` vs `src/services/ai_service_v2.py`
  - V1: sync, dotenv-load, cache decorator; V2: async, tiktoken/heuristics, rate-limit aware. Convergeren naar V2.
- `src/toetsregels/*`
  - JSON + Python per regel; overweeg generieke validator-basisklasse en JSON-first; reduceer Python per regel tot uitzonderingen.
- `src/validation/definitie_validator.py`
  - Interpreteert toetsregels en berekent violations/scores; check overlap met V2 pipeline en maak één authoritative pad.
- `src/ui/components/external_sources_tab.py`
  - Importeert `external_source_adapter` via `sys.path` hack → vervang door `from external.external_source_adapter import ...` en package-ify `external/`.
- `src/export` vs `src/exports`
  - `export/` is in gebruik via `services/export_service.py`; `exports/` lijkt dood gewicht.
- `src/utils/resilience*`
  - Meerdere varianten; kies één en deprecate de rest.
- `run_smoke_tests.sh`
  - Verwijst naar tests die ontbreken; aanpassen of verwijderen.

**Voorstel Migratieplan (EPIC-012)**

- Fase 1: Align op V2 paden
  - UI laat `ServiceFactory` V2 afdwingen; alle definities via `DefinitionOrchestratorV2` en `AIServiceV2`.
  - Verwijder `dotenv` uit pad of migreer calls weggehaald van V1-service.
- Fase 2: Validatie consolidatie
  - Eén pad voor violations/score (V2 contract). Legacy mappers bij UI-only boundaries.
  - Introduceer generieke validator-basisklasse en JSON-first regels.
- Fase 3: Code hygiene
  - Exports consolideren; resilience consolideren; imports normaliseren; tests verplaatsen.
- Fase 4: Opschoning
  - Verwijder legacy orchestrators/AI-service; verwijder ongebruikte directories; update docs.

**Checklijst (DoD) voor EPIC-012**

- Alle definities lopen via `DefinitionOrchestratorV2` en `AIServiceV2`.
- Geen `streamlit`-import in service-laag (UI-only).
- Eén export pad (`src/export/`) en werkende export-service.
- Eén resilience module + documentatie.
- Validators JSON-first, Python per-regel alleen bij noodzaak; gedeelde basisklasse aanwezig.
- Config via `config_manager` (geen `load_dotenv()` in productiecode); CI-secrets gedocumenteerd.
- `tests/` map aanwezig en scripts refereren naar bestaande tests; geen testbestanden in `src/`.

—

Vragen of wil je dat ik dit uitsplit in concrete PR’s met taakverdeling per fase? Ik kan ook een migratie-branchstructuur en checklist genereren.

**Volledige Sweep — Verificatie en Detailbevindingen**

- Scopeverificatie
  - Bestanden geïnventariseerd: alle `.py`, `.json`, `.yaml/.yml`, `.sql`, `.sh` onder repo (exclusief `.git`).
  - Tests: volledige `tests/`-boom meegenomen; enkele testachtige bestanden binnen `src/` (zie hieronder) gemarkeerd.
  - Archief-/niet-relevante docs (bijv. `CLAUDE.md`, `.ai/debug-log.md`) uitgesloten van inhoudelijke beoordeling.

- Regels-JSON ↔ Validators mapping (consistentiecheck)
  - Regels: 43 JSON-bestanden onder `src/toetsregels/regels/` (ARAI/CON/ESS/INT/SAM/STR/VER).
  - Validators: 43 Python-bestanden onder `src/toetsregels/validators/` (excl. `__init__.py`).
  - Mapping validatie: 1-op-1 dekking (bevestigd). ARAI-varianten correct genormaliseerd (`ARAI-04SUB1` ↔ `ARAI04SUB1`), overige via `-`→`_` (bijv. `STR-01` ↔ `STR_01`).

- Services met Streamlit-afhankelijkheid (UI-lek)
  - `src/services/service_factory.py` (feature flag/toggles via `st.session_state`).
  - `src/services/context/context_adapter.py` (leest/zet context in `st.session_state`).
  - `src/config/feature_flags.py`, `src/config/verboden_woorden.py` (UI-koppeling in configlaag).
  - `src/utils/voorbeelden_debug.py` (debugger leest `st.session_state`).
  - Actie (EPIC-012): UI-afhankelijkheden uit services/config/utils trekken; adapter aan UI-zijde plaatsen.

- `sys.path`-manipulaties (import-hacks)
  - `src/ui/components/external_sources_tab.py` (voegt `external/` toe; gebruikt `from external_source_adapter import ...`).
  - `src/ui/components/orchestration_tab.py`, `quality_control_tab.py`, `monitoring_tab.py`, `management_tab.py` voegen paden toe voor analysis/orchestration/monitoring.
  - `src/tools/*.py`, `src/__init__.py`, `src/main.py` voegen/insert src-paden toe (acceptabel voor entrypoints, maar liever package-setup).
  - Actie: correcte package imports (bijv. `from external.external_source_adapter import ...`), en project packaging (editable install) of sys.path-clean adapters in UI.

- `.env`/dotenv vs gecentraliseerde config
  - `src/services/ai_service.py` laadt `.env` via `load_dotenv()`; `src/main.py` vermeldt expliciet geen `.env` gebruiken.
  - Actie: uniformeren op `config_manager` (YAML + env overrides), dotenv verwijderen uit productiepad of conditioneel slechts in dev.

- Async/sync-bridging patronen (complexiteit/risico)
  - Diverse modules gebruiken `asyncio.run(...)`, `run_coroutine_threadsafe(...)`, `new_event_loop()`, `run_until_complete(...)` (o.a. in `services/service_factory.py`, `prompt_service_v2.py`, `export_service.py`, meerdere UI componenten, `orchestration/definitie_agent.py`).
  - Actie: duidelijke async-grenzen; UI roept async-services via event loop helpers in één centrale laag i.p.v. verspreide bridging.

- Schrijfbewerkingen naar disk (paden & hygiene)
  - Schrijven in: `services/export_service.py`, `export/export_txt.py`, `monitoring/api_monitor.py`, `utils/*` (cache, resilience, rate_limiter), `database/definitie_repository.py` (export), `config/verboden_woorden.py`, `config/config_manager.py` (YAML write in dev?), validators testhelpers.
  - Actie: paden via `config_manager.paths`, consistent encoding/atomic writes, write-permissies in CI bewaken.

- Tests — aanwezigheid en observaties
  - Uitgebreide testboom aanwezig: `tests/` met unit/integration/performance/smoke/ci/security/uitgebreide V2-coverage.
  - Enkele testachtige scripts in `src/`: `src/hybrid_context/test_hybrid_context.py` (moet naar `tests/`), meerdere `if __name__ == '__main__'` in libmodules (alleen voor manuele runs).
  - Shell `run_smoke_tests.sh` verwijst correct naar `tests/smoke/test_validation_v2_smoke.py` (aanwezig).

- Config-bestanden (YAML/JSON)
  - YAML: `config/config_{development,testing,production,default}.yaml`, `config/validation_rules.yaml`, `config/web_lookup_defaults.yaml`.
  - JSON: `config/context_wet_mapping.json`, `config/verboden_woorden.json` + toetsregel sets per categorie/context/prioriteit.
  - Actie: één bron van waarheid via `config_manager`; documenteer env-override matrix; valideren schema’s (bijv. pydantic/voluptuous).

- Overige specifieke flags per bestand (uitgelicht)
  - `src/services/definition_orchestrator.py` vs `src/services/orchestrators/definition_orchestrator_v2.py`: dubbele orchestrators; V2 preferred.
  - `src/services/ai_service.py` (sync/dotenv) vs `src/services/ai_service_v2.py` (async/rate-limit aware): consolideren op V2.
  - `src/ui/components/external_sources_tab.py`: sys.path-hack + import zonder package namespace.
  - `src/export` vs `src/exports`: `exports` lijkt ongebruikt; opruimen.
  - `src/services/service_factory.py`: Streamlit in services; feature flagging naar UI.
  - `src/security/security_middleware.py`: bevat zelftest met `asyncio.run(...)`; verplaatsen naar tests.

- Concrete refactor-tickets (addendum)
  - UI-decoupling: verwijder `streamlit`-import uit `services/service_factory.py`, `services/context/context_adapter.py`, `config/feature_flags.py`, `config/verboden_woorden.py`, `utils/voorbeelden_debug.py`. Voeg UI-bridge/adapters in `src/ui/services/`.
  - Imports normaliseren: vervang sys.path-manipulaties; maak alle submodules echte packages (met `__init__.py`) en gebruik absolute imports.
  - Async-brug consolideren: centrale async helper in UI-laag; verwijder verspreide `asyncio.run/...` calls in services.
  - Config-harmonisatie: verwijder `load_dotenv()` of conditioneer op dev; verplaats alle defaults naar YAML + env overrides.
  - Resilience-consolidatie: kies 1 implementatie, archiveer rest met verwijzing, update callsites.
  - Tests hygiene: verplaats `src/hybrid_context/test_hybrid_context.py` naar `tests/`; verwijder `__main__` selftestblokken uit libraries of markeer als dev-only scripts in `scripts/`.
  - Exports: verwijder `src/exports/` (na bevestigde onbruik) en borg centralisatie via `services/export_service.py`.

Deze sectie vormt de “line-by-line sweep” output op bestandsniveau: waar direct broncode-observaties relevant zijn heb ik de concrete paden hierboven opgenomen, zodat ze 1-op-1 te traceren zijn naar code. Voor de toetsregel-JSONs is de setconsistentie gevalideerd; inhoudelijke semantiek blijft onder de validator-pijplijn (V2) vallen en is verder consistent met de Python-validators.
