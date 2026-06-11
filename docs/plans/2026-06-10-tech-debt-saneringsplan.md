# Tech-Debt Saneringsplan — DefinitieAgent

> **For Claude:** Uit te voeren met agent-teams. Per fase: dispatch agents per issue, TDD (characterization-tests vóór elke refactor), orchestrator-verificatie verplicht. Gebruik **executing-plans** / **story-runner** per issue.

**Goal:** De 26 als `tech-debt` gelabelde DEF-issues gestructureerd wegwerken — eerst meetbaarheid + vangnet, dan groei bevriezen, dan veilig refactoren.

**Kernprincipe:** *Eerst meten en bevriezen, dan pas snijden.* God-object-refactoring (Fase 3) is alleen veilig met een betrouwbare coverage-baseline (Fase 0) en CI-ratchets die nieuwe debt blokkeren (Fase 1). Volgorde is dus géén prioriteit-op-severity maar afhankelijkheidsvolgorde.

**Bron:** backlog-audit 2026-06-10 (`.claude/audits/2026-06-10-backlog-audit/eindrapport.md`). Alle claims geverifieerd tegen de codebase.

---

## Scope: 26 tech-debt-issues

| Issue | Sev | Fase-marker | Korte omschrijving |
|-------|-----|-------------|--------------------|
| DEF-416 | Urgent | 0 | Verse coverage-baseline (`.coverage` is stale) |
| DEF-417 | High | 0 | Docs-drift: `src/ai_toetser` bestaat niet |
| DEF-404 | High | 0 | CLAUDE.md/patterns.md verouderde referenties |
| DEF-405 | High | 0 | Coverage-threshold consolideren (85 vs 80) |
| DEF-426 | Med | 0 | Deps/Python 3.13-mismatch/root-opruim/Renovate |
| DEF-420 | High | 1 | Test-config: skips, filterwarnings, smoke-test |
| DEF-418 | High | 1 | Ruff complexity-violations: baseline + ratchet |
| DEF-419 | Med | 1 | mypy strictness omkeren (per-module overrides) |
| DEF-425 | High | 0/2 | Security: CORS/pickle/rate-limiter/pip-audit |
| DEF-311 | Med | — | API-key beveiliging (stem af met 425) |
| DEF-407 | Med | — | Temperature provider/model-aware (gate Opus 4.7+) |
| DEF-421 | High | 2 | God-method `create_definition` (733r, CC 56) |
| DEF-422 | High | 2 | God-object `DefinitionEditTab` (1910r) |
| DEF-423 | High | 2 | UI→DB laagschending (17 files) |
| DEF-424 | Med | 2 | `ModularValidationService`/`interfaces.py` split |
| DEF-312 | High | — | `container.py` opsplitsen (1023r) |
| DEF-392 | Med | — | Business-logic uit UI naar services |
| DEF-192 | Urgent | — | God-class refactoring (parent/epic) |
| DEF-197 | High | — | Resilience-modules consolideren (4 → 1) |
| DEF-391 | Med | — | DB transactie-atomiciteit |
| DEF-393 | Med | — | ~515 brede exception-handlers (herscope eerst) |
| DEF-394 | Low | — | Category-mapping + rule-versioning naar config |
| DEF-157 | — | — | Prompt: ErrorPreventionModule beoordelen/verwijderen |
| DEF-162 | — | — | Per-module token-logging + warning |
| DEF-106 | High | — | PromptValidator (regressiepreventie) |
| DEF-330 | High | — | Cloud SQLite-persistentie (post-mvp) |

---

## Fase 0 — Meetbaarheid & hygiëne (fundament)

> **Doel:** betrouwbaar kunnen meten + accurate docs, zodat latere refactors veilig zijn. Lage risico's, veel quick wins. **Geen** productiecode-refactor.

**Volgorde & samenhang:**
1. **DEF-416** (Urgent) — draai `make test-cov-ci` (unit+integration), stel de echte baseline-coverage vast, commit een vers `.coverage`-artefact + documenteer in CLAUDE.md. *Blokkeert Fase 1-ratchet en Fase 3-vangnet.*
2. **DEF-405** — consolideer coverage-config op één plek (`pyproject [tool.coverage]`); fix CLAUDE.md:50 (`test-cov`→`test-cov-ci`) en `coverage-badge.yml:52` (80→85 of motiveer). *Hangt aan 416.*
3. **DEF-417 + DEF-404** (samen — zelfde drift) — corrigeer CLAUDE.md structuurboom (`ai_toetser` weg), `config/toetsregels.json`→`config/toetsregels/` in CLAUDE.md **én** patterns.md, "45 regels"→53.
4. **DEF-426** — Python-versie alignen (3.13 vs 3.11), root opruimen (10 losse bestanden → `docs/`/`tests/fixtures/`), Renovate + pip-audit in CI, mypy draaien vóór anthropic-bump.
5. **DEF-420** (config-deel) — `filterwarnings` in pytest.ini, smoke-test hernoemen (`smoke_test`→`test_smoke`), skip-inventaris (permanent vs tijdelijk), coverage-key fix.

**Agent-team:** 1 agent per issue, 5 parallel (alle onafhankelijk behalve 405→416). Effort: S-M elk. **Quick wins:** 417+404 (docs), 426 root-opruim.

**Exit-criterium Fase 0:** `make test-cov-ci` groen met gedocumenteerde baseline; CLAUDE.md/patterns.md verwijzen alleen naar bestaande paden; root schoon; CI heeft pip-audit.

---

## Fase 1 — Bevries de groei (CI-ratchets)

> **Doel:** stop *nieuwe* debt vóór je oude wegwerkt. Vereist de Fase 0-baseline.

1. **DEF-418** — `C901`+PLR-codes in `select`, `ruff check --add-noqa` als baseline, CI-gate "geen nieuwe `# noqa`", verwijder 6 dode per-file-ignores.
2. **DEF-419** — `check_untyped_defs=true`, globaal `disallow_untyped_defs=true` + per-module `false`-overrides als krimpende debt-teller; CI-gate op aangeraakte modules.
3. **Coverage-ratchet** (uit DEF-416) — huidige % = vloer; PR's mogen niet zakken.

**Agent-team:** 1 agent per issue, sequentieel binnen config (race op `pyproject.toml`). Effort: M elk. **Let op:** 419 raakt anthropic/openai-modules → koppel aan DEF-426 SDK-bump-discipline.

**Exit-criterium Fase 1:** CI faalt bij nieuwe complexity/type/coverage-regressie. Oppervlak kan alleen krimpen.

---

## Fase 2 — Security (parallel inplanbaar, hoge prio)

> **Doel:** security-debt dichten. Deels al in Fase 0 (pip-audit). Kan parallel aan Fase 1 lopen.

1. **DEF-425** — CORS-allowlist i.p.v. wildcard (`feature_status_api.py:90`); HMAC/signatuur of JSON/msgpack i.p.v. kale pickle (`robust_cache.py:185`, `definition_generator_cache.py:200`); rate-limiter naar gedeelde store; pip-audit als CI-gate.
2. **DEF-311** — middleware-integratie in `main.py` verifiëren; sessie-isolatie API-keys; **stem af met DEF-425** (overlap) om dubbel werk te voorkomen → overweeg samen te voegen.

**Agent-team:** security-reviewer + 1 implementatie-agent. Quick wins: CORS-allowlist, pip-audit-gate.

---

## Fase 3 — God-object refactoring (grootste effort, mét vangnet)

> **Doel:** de 5 grootste structurele schulden. **Alleen na Fase 0+1** (coverage-baseline + ratchets). Elke refactor begint met **characterization-tests** (Feathers) rond bestaand publiek gedrag.

**Volgorde (laag risico → hoog):**
1. **DEF-424** (quick win + L) — verwijder dode `DefinitionValidatorInterface` (0 refs) direct; daarna `ModularValidationService` (1766r) splitsen in RuleLoader/JsonRuleEvaluator/ScoreAggregator + `interfaces.py` per domein. *KRITIEK-module: extra voorzichtig.*
2. **DEF-421** (L) — `create_definition` (733r, CC 56) extracten per fase: prompt-build → AI-call → parse → validate → persist. *KRITIEKE generatieflow — niet zonder overleg.*
3. **DEF-312** (L) — `container.py` (1023r) reduceren door registraties naar bestaande `ServiceFactory` te verplaatsen.
4. **DEF-423 + DEF-392 + DEF-422** (samenhangend UI-blok, XL) — plan als één ontvlechting: route UI→DB via service-laag (423), business-logic naar services (392), `DefinitionEditTab` (1910r) splitsen in EditSession/SearchController/ValidationPresenter/VersionController + Streamlit `st.fragment`/`@st.cache_data` (422).
5. **DEF-192** — na bovenstaande: sluiten als parent/duplicaat, of als epic eroverheen leggen.

**Agent-team:** 1 agent per issue, **niet** parallel binnen hetzelfde bestand. Worktree-isolatie aanbevolen. Per issue: characterization-tests → extract → groen → commit. Doel CC ≤10.

**Exit-criterium Fase 3:** geen file >1000r in de hotspots; CC ≤10 op aangeraakte methoden; coverage niet gezakt.

---

## Fase 4 — Resterende debt (kleiner, parallel)

1. **DEF-197** — resilience: kies `SmartRateLimiter` als standaard, refactor rest naar thin wrappers; corrigeer paden (`src/utils/`).
2. **DEF-391** — DB transactie-atomiciteit: expliciete `BEGIN/COMMIT/ROLLBACK` in `definitie_crud.py`/`voorbeelden_repository.py` (autocommit-issue `db_connection.py:37`).
3. **DEF-393** — **eerst herscope** (werkelijk ~515, niet ~91); selecteer de echte risico-handlers (geen logging/re-raise), specificeer die.
4. **DEF-394** — category-mapping naar `config/`, `version`-veld op 53 regel-JSONs.
5. **DEF-407** — temperature provider/model-aware in `anthropic_client.py` (gate vóór Opus 4.7+).
6. **DEF-157 / DEF-162 / DEF-106** (prompt-system) — 157: ErrorPreventionModule beoordelen/verwijderen; 162: per-module token-logging + 8000-warning; 106: PromptValidator bouwen (regressiepreventie, hangt aan stabiel prompt-systeem).

**Agent-team:** tot 5 parallel (onafhankelijke modules). Effort: S-M elk.

---

## Fase 5 — Deploy-voorbereiding (post-mvp)

- **DEF-330** — cloud SQLite-persistentie. Pas oppakken zodra deployment concreet wordt; nu `post-mvp`. Herformuleren als "persistentiestrategie + restore-procedure".

---

## Uitvoering met agent-teams

| Aspect | Aanpak |
|--------|--------|
| Per fase | Orchestrator dispatcht agents per issue (max 5 parallel, globale regel) |
| Per refactor-issue | TDD: characterization/failing test → minimale change → groen → commit |
| Branch | `feature/DEF-XX-...` per issue; **nooit** op main |
| Verificatie | Orchestrator-verificatie verplicht (lees diff, draai `make test`/`make lint`) |
| Worktree | Fase 3 (parallelle file-mutaties): worktree-isolatie |
| Oplevering | Per issue PR + `/review-pr`; merge alleen op expliciete instructie |

## Aanbevolen eerste sprint (laagste risico, hoogste fundament-waarde)

DEF-416 → DEF-405 → DEF-417+404 → DEF-426 → DEF-420 (heel Fase 0). Levert betrouwbare meetbaarheid + schone docs in één sprint, zonder productiecode-risico. Daarna pas Fase 1-ratchets aanzetten.

## Verificatie bij oplevering (per fase)

- [ ] `make test` groen · `make lint` schoon
- [ ] Coverage niet gezakt t.o.v. Fase 0-baseline
- [ ] Geen nieuwe `# noqa`/type-ignores zonder tech-debt-registratie
- [ ] Betrokken issue(s) bijgewerkt + gesloten via PR-merge
