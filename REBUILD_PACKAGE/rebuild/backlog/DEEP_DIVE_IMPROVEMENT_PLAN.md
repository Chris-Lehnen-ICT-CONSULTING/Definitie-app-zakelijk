---
title: Codebase Deep Dive en Verbeterplan
canonical: false
status: active
owner: architecture
last_verified: 2025-09-12
applies_to: definitie-app@current
---

# Codebase Deep Dive en Verbeterplan

Dit document geeft een diepgaande analyse van de huidige codebase en een concreet verbeterplan om te voldoen aan de eisen en requirements (o.a. REQ‑006 OWASP, EPIC‑010/012/014). Per domein staan Must/Should-acties en meetbare acceptatiecriteria.

## Samenvatting

- V2‑architectuur met stateless orchestratie staat; DI en service‑isolatie zijn grotendeels geborgd.
- Belangrijkste hiaten: security/auth, encryptie, monitoring, prompt‑grootte, caching (regels/container), web‑lookup robustheid, DB‑indexering, testdiscipline en CI‑gates (secrets/deps).
- Gefaseerde aanpak: P0 (stabiel maken en guards), P1 (security/monitoring/db/web‑lookup), P2 (auth/encryptie/enhancement/performance/traceability).

## Scope en Doel

- Scope: app UI (Streamlit), services (DI, orchestrator, prompts, validation, web lookup), database, utils, security, tests en documentatie.
- Doel: compliance met architectuurprincipes (EPIC‑010), non‑functionals (REQ‑006 e.a.), prestaties en onderhoudbaarheid verbeteren.

## Architectuur & DI

- Must
  - Vervang directe `ServiceContainer()` aanroepen buiten container zelf door `get_container()` (o.a. in `src/orchestration/definitie_agent.py`, `src/integration/definitie_checker.py`, `src/ontologie/ontological_analyzer.py`).
  - UI caching: `st.cache_resource` toepassen rond container/adapters in UI entry om re‑init te vermijden.
  - Handhaaf service‑laag isolatie: CI‑guard en tests tegen `import streamlit` in `src/services/**` (bestaat, uitbreiden waar nodig).
- Should
  - Convergeren op `DefinitionUIService` als enige UI‑facade; UI‑componenten geen directe repo/workflow‑calls.
- Acceptatie
  - 0 directe `ServiceContainer()` new’s buiten container; 1 container per sessie (trace in logs).
  - Alle guards groen; geen `import streamlit` in services.

## Orchestrator & Flow

- Must
  - Security en monitoring aansluiten: implementeer `SecurityServiceInterface` adapter op `security/security_middleware.py` en injecteer in container; voeg `MonitoringServiceInterface` wrapper (durations, tokens, error rates).
  - “Enhancement” pad realiseren (nu `None`): minimaal retry + gerichte correcties o.b.v. violations.
- Should
  - Uniforme output: alle paden leveren `UIResponseDict`/V2 contract (ook bij fouten).
- Acceptatie
  - 11‑fasen flow doorloopt; monitoringevents per generatie aanwezig; sanitization zichtbaar in metadata.

## Prompting

- Must
  - Tokenreductie ≥80% (±7.250→≤1.250): deduplicatie in `UnifiedPromptBuilder`, verwijder herhalingen, parameteriseer secties; strengere flags.
  - Prompt‑tokenmeting per prompt (tiktoken) en budget‑asserts in tests.
- Should
  - Web‑lookup augmentatie compact (top‑N, samenvat i.p.v. plakken), conditioneel.
- Acceptatie
  - p95 prompt tokens ≤1.500; prompt‑contract tests groen; stijlregels afgedwongen (geen emoji in PROMPT‑style).

## Validatie & Toetsregels

- Must
  - Determinisme borgen; caches in `ToetsregelManager` expliciet; voorkom herladen per call.
  - Eén canonieke `validation_rules.yaml`; overlays via config manager.
- Should
  - Uniforme mapping (RuleResult → aggregatie → `UIResponseDict.violations`) met correcte severities.
- Acceptatie
  - Batch‑validatie p95 <10ms per definitie (zonder AI); determinisme tests groen; geen dubbele regel‑loads.

## AI‑Integratie

- Must
  - Rate limiting/timeout/backoff consistent; errors gemapt naar servicefouten (geen raw SDK errors).
  - Modelconfig via config manager als SSOT; geen hardcoded defaults elders.
- Should
  - Centrale token‑tellingen (prompt + response) gelogd naar monitoring.
- Acceptatie
  - ≥95% “Anders...” success (CFR target); tijdouts traceerbaar; geen ongefilterde exceptions richting UI.

## Web Lookup

- Must
  - SRU 404/bronfouten afvangen met fallback providers; normaliseer/dedup in provenance + ranking.
  - Timeouts + retry policy per bron; provenance verplicht bij augmentatie.
- Should
  - Config via `WEB_LOOKUP_CONFIG` per omgeving met schema‑validatie.
- Acceptatie
  - Alle `tests/web_lookup/*` groen; p95 bronselectie <300ms; ≥1 authoritative bron in top‑N indien beschikbaar.

## Database & Repository

- Must
  - Versleuteling: SQLCipher of field‑level encryptie; vervang stub `services/storage.encrypt` door echte implementatie.
  - Indexen voor `begrip`, `status`, `categorie`; optimaliseer zoekqueries; voorkom N+1.
  - Alle queries geparameteriseerd (doorloop schrijf/zoekpaden).
- Should
  - Migratiepad: idempotent; automigratie in dev; wal/shm housekeeping.
- Acceptatie
  - Search p95 <50ms op 10k records; encryptie aantoonbaar (tests); injection tests slagen.

## Security & Privacy (REQ‑006 OWASP)

- Must
  - Authenticatie/Autorisatie: basislaag (API‑token of sessie + CSRF) voor niet‑publieke acties.
  - Inputvalidatie/whitelists op alle UI→service ingangen; XSS‑mitigatie in exports.
  - Security headers (CSP/HSTS/X‑Frame‑Options) via Streamlit hooks of reverse proxy.
  - Logging‑redactie: PII‑pseudonimisering, API key masking, retention beleid.
  - Dependency/secret scanning in CI (pip‑audit/safety + detect‑secrets/ggshield).
- Should
  - DPIA artefact en redaction service gekoppeld in orchestrator.
- Acceptatie
  - REQ‑006 acceptatiecriteria behaald; ZAP baseline: 0 High; secret scan: 0 leaks; audit log aanwezig.

## Performance

- Must
  - Container/regel caching; minimaliseer import‑I/O bij cold start.
  - Asynchrone UI‑acties met progress; vermijd sync bridges.
- Should
  - Benchmarks (pytest‑benchmark): “zonder AI” p95 <200ms; budgets vastgelegd.
- Acceptatie
  - CFR budgets: aggregatie <50ms, validatie <10ms (zonder AI); cold start dev <2s.

## UI Laag

- Must
  - UI→service via `DefinitionUIService` en adapters; minimaliseer `SessionState`‑lekkage.
  - Splits grote componenten (`tabbed_interface.py`) en consolideer keys/async‑gebruik.
- Should
  - Achtergrondtaken (lookup/validatie) met duidelijke status en user feedback.
- Acceptatie
  - Geen directe DB/repo calls in UI; UI responsief bij lange taken; geen blokkende loops.

## Config & Feature Flags

- Must
  - SSOT via `config_manager`; documenteer env‑vars; YAML‑schema validatie.
- Should
  - Profielen per omgeving (dev/test/staging/prod) met veilige defaults.
- Acceptatie
  - Config‑validatie tests groen; runtime logs tonen profiel en kritieke toggles.

## Logging & Monitoring

- Must
  - `MonitoringService` implementeren en injecteren; events voor start/complete, durations, tokens, cache‑hits.
  - Redactie‑filter in logging handler voor PII/API keys.
- Should
  - Metrics export naar bestand (`logs/metrics.json`) of Prometheus adapter.
- Acceptatie
  - Metingen zichtbaar per generatie; correlation id in fouten; block/allow ratio in security report.

## Testing & CI/CD

- Must
  - Fix test‑importissues; re‑enable disabled tests; guard tests verplicht in CI.
  - Secret scan + dependency audit toevoegen aan workflows.
- Should
  - Acceptatietests (UAT) skeleton (`tests/acceptance/`) voor hoofdscenario’s en REQ‑sporen.
- Acceptatie
  - Pytest groen; coverage ≥60% kritieke modules; CI‑gates voor legacy patterns, secrets en dependencies actief.

## Documentatie & Compliance

- Must
  - Update `last_verified` in canonieke docs; broken links fixen; traceability naar REQ’s compleet.
- Should
  - AGENTS/workflow‑library up‑to‑date met actuele routerconfig.
- Acceptatie
  - Docs‑validator groen; 0 broken links; één canonical per onderwerp.

## Gefaseerde Aanpak

- P0 (1–2 dagen)
  - DI/guards: `get_container()` overal, UI caching.
  - Prompt quick wins: deduplicatie, tokenbudget meten/asserteren.
  - Toetsregel/manager caching; test imports fixen; CI guards (secrets/deps) aan.
  - Log‑redactie (PII/API keys).
- P1 (deze week)
  - SecurityService + MonitoringService adapters; SRU fallback/timeout.
  - DB indexen en query‑optimalisaties; acceptance tests skeleton; ZAP baseline.
- P2 (volgende weken)
  - AuthN/Z, encryptie (SQLCipher/field‑level), enhancement‑pad.
  - Benchmarks en performance‑budgetten; docs cleanup/traceability.

## KPI’s en Meetpunten

- Beveiliging: ZAP (0 High), secret scan (0), dependency audit (0 High).
- Prestaties: prompt p95 ≤1.5k tokens; validatie p95 <10ms (zonder AI); aggregatie <50ms.
- Betrouwbaarheid: ≥95% “Anders...” success; determinisme‑tests groen.
- Onderhoudbaarheid: 0 legacy‑guard overtredingen; ≥60% coverage kritieke modules.

## Traceability naar Epics / User Stories / Bugs

Deze sectie koppelt de verbeterpunten uit dit plan aan bestaande Epics, User Stories, Features en bekende bugs (CFR‑BUGs).

- Architectuur & DI
  - Epics: EPIC‑010 (Context Flow Refactoring), EPIC‑012 (Legacy Orchestrator Refactoring)
  - User Stories: EPIC‑010/US‑043 Remove Legacy Context Routes; EPIC‑010/US‑050 E2E Context FLAAG tests
  - Bugs: CFR‑BUG‑001 (Context fields not passed), CFR‑BUG‑003 (GenerationResult import error)
  - Features: “Core Functionaliteit” consolidatie; guard script `scripts/check-legacy-patterns.sh`

- Orchestrator & Flow
  - Epics: EPIC‑012 (cutover naar V2), afhankelijk van EPIC‑010 guards
  - User Stories: EPIC‑012/US‑072 DefinitionWorkflowService (workflow + repo samenbrengen)
  - Bugs: Regressiepreventie voor CFR‑BUG‑001/002 via uniforme flow en contracts
  - Features: “Basis Definitie Generatie” stabiliteit (features DEF‑00x uit overzicht)

- Prompting
  - Epics: EPIC‑010 (context/ontologische categorie fix), EPIC‑014 (Business Logic Refactoring)
  - User Stories: EPIC‑010/US‑041 Fix Context Field Mapping; EPIC‑014 (US‑107..121) scoring/feedback rules
  - Bugs: CFR‑BUG‑001 (context naar prompt), CFR‑BUG‑014 (synoniemen/antoniemen – al gemarkeerd als opgelost)
  - Features: Prestaties/Tokenreductie valt onder “Prestaties” features; prompt template keuzes

- Validatie & Toetsregels
  - Epics: EPIC‑002 (Kwaliteitstoetsing), EPIC‑012 (consolidatie)
  - User Stories: determinisme/caching requirements in validatie suites; EPIC‑012 implementatieplannen
  - Bugs: Voorkomen duplicaten en drift (indirect uit EPIC‑010 reviewpunten)
  - Features: KWA‑00x (validatie zichtbaar, suggesties, iteraties) – reeds grotendeels compleet; plan borgt performance/determinisme

- AI‑Integratie
  - Epics: EPIC‑001 (Basis generatie), EPIC‑012 (resilience in V2 flow)
  - User Stories: rate limiting/timeout als NFRs; geen direct US, maar REQs gedekt (zie REQ‑006)
  - Bugs: Timeouts/rate limit gerelateerde regressies (preventief)
  - Features: “Prestaties” en “Infrastructure” (Async API layer al aanwezig)

- Web Lookup
  - Epics: EPIC‑003 (Content Verrijking / Web Lookup)
  - User Stories: EPIC‑003/US‑014 Modern Web Lookup; EPIC‑003/US‑015 Wikipedia; EPIC‑003/US‑016 SRU; EPIC‑003/US‑018 Source Attribution; EPIC‑003/US‑083 Wikidata
  - Bugs: CFR‑BUG‑015 (compat layer `title` attribuut) – plan eist robuuste titelbron + fallback; algemene 404/timeout afhandeling
  - Features: WEB‑001..004 (zoeken, validatie, automatische verrijking, attributie) – plan dekt robustheid, performance en provenance

- Database & Repository
  - Epics: EPIC‑007 (Onderhoud/Prestaties), EPIC‑006 (Data security aspecten)
  - User Stories: indexing/optimalisatie (NFR taken), migraties; geen specifieke US maar REQs (db security)
  - Bugs: N+1 queries en performance issues (EPIC‑007 backlog)
  - Features: “Export/Import” en “Prestaties” – plan dekt indexen en encryptie

- Security & Privacy (REQ‑006)
  - Epics: EPIC‑006 beveiliging & Auth
  - User Stories: EPIC‑006/US‑024 API key validation; overige US voor auth/z, headers, logging (diverse)
  - Bugs: Anders‑pad validaties en XSS‑edgecases (gekoppeld aan US‑042 en exports)
  - Features: Beveiliging features (authz/authn/encryptie) – plan levert OWASP dekking en CI scans

- Performance
  - Epics: EPIC‑007 (Performance en onderhoud)
  - User Stories: Benchmarks/latency doelen (NFR); CFR performance‑budgets
  - Bugs: Memory leaks/N+1 (EPIC‑007 checklist)
  - Features: “Prestaties” categorie – plan dekt caching en budgetten

- UI Laag
  - Epics: EPIC‑004/EPIC‑013 (UI/Docs workflows), EPIC‑001 UI‑tabbladen
  - User Stories: EPIC‑010/US‑042 ("Anders...") – plan borgt 95% success; UI‑facade centralisatie
  - Bugs: CFR‑BUG‑002 ("Anders..." crashes) – mitigatie via validatie en uniforme contextflow
  - Features: UI‑stabiliteit; a11y (EPIC‑013 US‑085) valt buiten scope van P0, als gap benoemd

- Config & Feature Flags
  - Epics: EPIC‑010 (guards), EPIC‑012 (cutover), EPIC‑013 (workflow/portal tooling)
  - User Stories: feature flag tests (US‑050 verwijst naar E2E context tests met flags)

- Logging & Monitoring
  - Epics: EPIC‑007 (Monitoring/onderhoud)
  - User Stories: monitoring events/metrics (NFR); security audit trail (EPIC‑006)

- Testing & CI/CD
  - Epics: EPIC‑012 (testinfra herstel), EPIC‑010 (legacy guards)
  - User Stories: US‑050 E2E context tests; diverse test fixes/import issues in backlog
  - Bugs: CFR‑BUG‑003 (import error) – plan dekt shims + testfixes; secret/dependency scans in CI

### Gaps / Niet gedekt door dit plan (bewust uit scope of vervolg)

- EPIC‑009 Advanced Features (bulk operations, collaboration, API): niet gedekt door P0–P2.
- A11y en multi‑language (EPIC‑013 US‑085 e.a.): niet in P0; plan kan P3 uitbreiden.
- API exposure (FastAPI) en microservices uit target‑architectuur: niet in huidige scope.
- Volledige UAT‑set (tests/acceptance) bestaat nog niet; skeleton staat in P1.

### Bekende Bugs en Plan‑maatregelen

- CFR‑BUG‑001 (Context fields not passed to prompts): Prompting + ContextManager mapping (US‑041), E2E tests (US‑050).
- CFR‑BUG‑002 ("Anders..." crashes): UI validatie, 95% success target, edge‑case tests (US‑042).
- CFR‑BUG‑003 (GenerationResult import error): shim in `services/interfaces.py`, test‑import fixes, CI guard.
- CFR‑BUG‑014 (Synoniemen/Antoniemen): gemarkeerd als opgelost; non‑regressietesten via validatie/prompt‑checks.
- CFR‑BUG‑015 (web lookup `title`): compat wrapper fix + fallback; timeouts/retries en provenance.

## Dependencies & Risico’s

- Auth/encryptie keuzes (SQLCipher vs. field‑encryptie) en integratie in Streamlit.
- SRU/extern bronnen instabiliteit → fallback en tijdouts cruciaal.
- Promptreductie kan effect op kwaliteit hebben → A/B in tests.

## Volgende Stappen

1) P0‑taken oppakken (PR‑set 1). 2) CI uitbreiden met scans. 3) Security/Monitoring injecteren. 4) DB indexen/migraties. 5) Acceptance tests toevoegen en roadmap bijwerken.

## Compliance met Architectuur, CLAUDE.md en README.md

- Backlog‑structuur en documentatie
  - Dit is een niet‑canoniek plan (canonical: false) onder `docs/backlog/`, conform CANONICAL_LOCATIONS.md. Geen duplicaten of nieuwe archiefmappen aangemaakt.
  - Frontmatter aanwezig (owner/status/last_verified/applies_to) conform README “Single Source of Truth Policy”.

- CLAUDE.md richtlijnen (kritiek)
  - Geen nieuwe backwards‑compatibility lagen toevoegen; focus op refactor naar V2 (EPIC‑010/012). Bestaande shims niet uitbreiden; waar mogelijk opruimen.
  - Geen feature flags/migratiepaden toevoegen in services; UI‑toggles blijven in UI‑laag zoals README aangeeft.
  - Wijzigen beperken tot noodzakelijke scope; bestaande master/canonieke documenten updaten i.p.v. dupliceren.

- Architectuurprincipes
  - DI via `ServiceContainer` en service‑isolatie (geen `streamlit` in `src/services/**`), geborgd met bestaande CI‑guards.
  - Stateless orchestrator V2 blijft het enige pad; alle stappen in dit plan volgen de 11‑fasen flow en CFR‑performancebudgetten (aggregatie <50ms, validatie <10ms zonder AI).

- README‑afspraken en CI‑gates
  - “Geen TODO/FIXME” geldt; dit plan introduceert geen TODO markers in code.
  - Legacy pattern gates blijven actief; plan versterkt ze (DI‑hygiëne, context‑mapping, geen `.best_iteration`, etc.).
  - Config SSOT: alle wijzigingen via `config_manager` en YAML‑overlays; geen hardcoded waarden.
