# Performance Optimization Masterplan
**Project:** DefinitieAgent Performance Improvements
**Based On:** Cache Test Log Analysis (2025-10-07)
**Generated:** 2025-10-07
**Status:** READY FOR EXECUTION

---

## 📋 Executive Summary

Dit masterplan beschrijft **7 optimalisaties** om de DefinitieAgent applicatie sneller, schaalbaarder en beter te monitoren. Gebaseerd op grondige multi-agent analyse van startup logs en codebase.

### Huidige Status ✅
- **Startup tijd:** ~400ms (doel: <500ms) ✅
- **Cache werkt:** RuleCache 100% hit rate na initial load ✅
- **Singleton pattern:** ServiceContainer init count = 1 ✅

### Resterende Problemen 🔴
- **Config warnings:** Custom config passed but ignored
- **Logging overhead:** 79-111 INFO logs tijdens startup
- **Geen monitoring:** Cache effectiviteit niet zichtbaar
- **Geen baseline tracking:** Performance regressies worden niet gedetecteerd
- **Slow startup:** Eager loading van non-critical services

### Verwachte Impact
- **Startup:** 400ms → **210ms** (-47%)
- **Logging:** 111 INFO logs → **12** (-89%)
- **Monitoring:** 0% visibility → **100%** cache/performance inzicht
- **Regression detection:** 0% → **100%** automatisch
- **Code quality:** Technical debt opgeruimd

---

## 🎯 Overzicht Alle 7 Stappen

| # | Optimalisatie | Impact | Complexity | Effort | Priority |
|---|--------------|--------|------------|--------|----------|
| 1 | Config Parameter Removal | 🟡 LOW | 🟢 SIMPLE | 6-8h | 🔴 HIGH |
| 2 | PromptOrchestrator Verificatie | ℹ️ INFO | 🟢 SIMPLE | 1-2h | 🟡 MEDIUM |
| 3 | Logging Level Optimalisatie | 🟢 HIGH | 🟢 SIMPLE | 12-16h | 🔴 HIGH |
| 4 | Cache Monitoring | 🟢 MEDIUM | 🟡 MEDIUM | 8-10d | 🟡 MEDIUM |
| 5 | Lazy Loading Services | 🟢 HIGH | 🟢 SIMPLE | 10h | 🔴 HIGH |
| 6 | Structured Logging | 🟢 MEDIUM | 🟡 MEDIUM | 40-58h | 🟡 MEDIUM |
| 7 | Performance Baseline Tracking | 🟢 HIGH | 🟡 MEDIUM | 4-5d | 🟡 MEDIUM |

**Totale Effort (zonder optionals):** ~15 dagen
**Totale Effort (alles):** ~30 dagen
**Aanbevolen Aanpak:** Gefaseerd - Quick Wins eerst (1-3), dan Foundation (4-7)

---

## 📊 Stap 1: Config Parameter Removal

### 🎯 Doel
Elimineer WARNING: "Custom config passed to get_container() is IGNORED" door architectuur te consolideren.

### 🔍 Root Cause
**Dubbele `get_container()` implementaties:**
1. `services/container.py:get_container(config)` → Creëert NIEUWE instance als config != None
2. `services/service_factory.py:get_container(config)` → Wrapper die config negeert + WARNING logt

**Primaire oorzaak:** `get_definition_service()` genereert altijd config via `_get_environment_config()` en passt dit door.

### 📁 Betrokken Files

**Productie (1 locatie):**
- `src/services/service_factory.py:763` → `get_definition_service()`

**Tests (2 locaties):**
- `tests/functionality/test_deep_functionality.py:225`
- `tests/functionality/test_final_functionality.py:165`

**Architectuur (3 locaties):**
- `src/services/service_factory.py:32-49` (wrapper function)
- `src/services/container.py:531-546` (global container)
- `src/utils/container_manager.py` (cached container)

### 🛠️ Implementatie

#### Optie 1: Remove Config Entirely (Aanbevolen)
```python
# service_factory.py
def get_definition_service():  # Remove use_container_config parameter
    container = get_cached_container()  # No config!
    # ... rest of logic

# container.py
def get_container() -> ServiceContainer:  # Remove config parameter
    global _default_container
    if _default_container is None:
        _default_container = ServiceContainer(_load_default_config())
    return _default_container
```

#### Testbare Acceptatiecriteria
- [ ] Geen WARNING in logs
- [ ] ServiceContainer init count blijft 1
- [ ] Tests slagen zonder `{}` parameter
- [ ] Backward compatibility: bestaande code werkt

### 📦 Deliverables
1. ✅ `service_factory.py` - Remove config param from `get_definition_service()`
2. ✅ `container.py` - Fix `get_container()` to not create new instances
3. ✅ `service_factory.py` - Remove wrapper `get_container()`
4. ✅ Tests updated - Remove `{}` parameters
5. ✅ Documentation - Update architecture docs

### ⏱️ Effort Estimate
- **Development:** 4 hours
- **Testing:** 2 hours
- **Documentation:** 1-2 hours
- **Total:** **6-8 hours**

### 🎯 Success Metrics
- Zero warnings in startup logs
- ServiceContainer init count = 1 (verified)
- All tests pass
- No breaking changes

### 🔗 Dependencies
- None (kan onafhankelijk uitgevoerd worden)

### 🚨 Risks
- **LOW:** Mainly refactoring, not behavioral changes
- **Mitigation:** Comprehensive test coverage

---

## 📊 Stap 2: PromptOrchestrator Duplicatie Verificatie

### 🎯 Doel
Verifiëren dat PromptOrchestrator duplication issue is opgelost en documentatie bijwerken.

### 🔍 Bevindingen
**Status:** ✅ **OPGELOST** (indirect, via container fixes)

**Bewijs:**
- Log toont 1x initialisatie (regel 21-76)
- 16 modules geregistreerd 1x (niet 2x)
- Timing: 319ms voor alle modules
- Oorzaak dubbele init was: dubbele ServiceContainer (nu gefixt)

**Timeline:**
- Oct 6, 2025: Issue gedocumenteerd (2x init)
- Oct 7, 2025: Container fixes (`c2c8633c`, `49848881`)
- Oct 7, 2025 (current): 1x init geverifieerd

### 📁 Betrokken Files

**Documentatie (update needed):**
- `docs/reports/prompt-orchestrator-duplication-analysis.md`
- `CLAUDE.md` (regel ~207)

**Code (verification only):**
- `src/services/prompts/modular_prompt_adapter.py:69`
- `src/services/prompts/modules/prompt_orchestrator.py`

### 🛠️ Implementatie

#### Taak 1: Update Documentatie
```markdown
# docs/reports/prompt-orchestrator-duplication-analysis.md
## UPDATE (Oct 7, 2025): ✅ RESOLVED

**Status:** Issue resolved by ServiceContainer singleton fixes
**Root Cause:** PATH 2 was duplicate container initialization (now fixed by US-202)
**Current State:** 1x initialization during app startup
**Action:** None required (keep document for historical reference)
```

#### Taak 2: Update CLAUDE.md
```markdown
# CLAUDE.md (Performance Section)
2. **PromptOrchestrator**: ✅ OPGELOST (US-202, Oct 7 2025)
   - Was: 2x initialisatie door duplicate container
   - Nu: 1x initialization tijdens startup
   - Zie: docs/reports/prompt-orchestrator-duplication-analysis.md
```

#### Taak 3: Archiveren Oude Analyse
```bash
# Move to archive with resolution note
mv docs/reports/prompt-orchestrator-duplication-analysis.md \
   docs/archief/resolved-issues/prompt-orchestrator-duplication-analysis.md
```

### 📦 Deliverables
1. ✅ Updated analysis document with resolution
2. ✅ Updated CLAUDE.md performance section
3. ✅ Archive oude analyse met resolution note
4. ✅ Verification tests (optional: add to test suite)

### ⏱️ Effort Estimate
- **Documentation:** 1 hour
- **Verification tests (optional):** 1 hour
- **Total:** **1-2 hours**

### 🎯 Success Metrics
- Documentation accurately reflects current state
- No confusion about "known issue" that's already resolved
- Historical context preserved

### 🔗 Dependencies
- None (pure documentation update)

### 🚨 Risks
- **ZERO:** Documentation-only change

---

## 📊 Stap 3: Logging Level Optimalisatie

### 🎯 Doel
Reduceer logging overhead door 83-89% door juiste log levels te gebruiken.

### 🔍 Probleem
**Huidige situatie:**
- 79-111 INFO logs tijdens startup
- 48-64 logs alleen voor module initialization
- 16-32 logs voor service creation
- Per-batch execution logs bij elke definitie generatie

**Impact:**
- ~4ms per log statement
- Signal-to-noise ratio laag
- Production logs zijn rommelig

### 📁 Betrokken Files

**Priority 1 - Module Initialization (16 files):**
```
src/services/prompts/modules/template_module.py
src/services/prompts/modules/expertise_module.py
src/services/prompts/modules/arai_rules_module.py
src/services/prompts/modules/con_rules_module.py
src/services/prompts/modules/ess_rules_module.py
src/services/prompts/modules/sam_rules_module.py
src/services/prompts/modules/ver_rules_module.py
src/services/prompts/modules/structure_rules_module.py
src/services/prompts/modules/integrity_rules_module.py
src/services/prompts/modules/grammar_module.py
src/services/prompts/modules/metrics_module.py
src/services/prompts/modules/output_specification_module.py
src/services/prompts/modules/error_prevention_module.py
src/services/prompts/modules/definition_task_module.py
src/services/prompts/modules/context_awareness_module.py
src/services/prompts/modules/semantic_categorisation_module.py
```

**Priority 2 - ServiceContainer:**
```
src/services/container.py
```

**Priority 3 - PromptOrchestrator:**
```
src/services/prompts/modules/prompt_orchestrator.py
```

**Priority 4 - Rules Cache:**
```
src/toetsregels/rule_cache.py
src/toetsregels/cached_manager.py
```

### 🛠️ Implementatie

#### Priority 1: Module Initialization (48-64 logs → 2-3 logs)

**Veranderingen in elk module bestand:**
```python
# BEFORE
logger.info(f"TemplateModule geïnitialiseerd (examples={self.include_examples})")

# AFTER
logger.debug(f"TemplateModule geïnitialiseerd (examples={self.include_examples})")
```

**Orchestrator summary (keep INFO):**
```python
# prompt_orchestrator.py:55
logger.info(f"PromptOrchestrator: {len(self.modules)} modules, {max_workers} workers")

# Remove per-module success log at line 90 (or change to DEBUG)
```

#### Priority 2: Service Creation (16 logs → 1 log)

**container.py veranderingen:**
```python
# Change ALL service creation logs to DEBUG:
logger.debug("DefinitionOrchestratorV2 instance aangemaakt")
logger.debug("WorkflowService instance aangemaakt")

# Keep only main init at INFO:
logger.info(f"ServiceContainer initialized (count: {self._initialization_count})")
```

#### Priority 3: Per-Batch Execution (5 logs → 1 log)

**prompt_orchestrator.py veranderingen:**
```python
# Change execution details to DEBUG:
logger.debug(f"Execution order: {len(batches)} batches")
logger.debug(f"Executing batch {batch_idx + 1}: {batch}")

# Keep final summary at INFO:
logger.info(f"Prompt built for '{begrip}': {len(prompt)} chars in {time}ms")
```

### 📦 Deliverables
1. ✅ 16 module files updated (DEBUG level)
2. ✅ `container.py` updated (1 INFO, rest DEBUG)
3. ✅ `prompt_orchestrator.py` updated (summary only INFO)
4. ✅ `rule_cache.py` + `cached_manager.py` optimized
5. ✅ Tests still pass (verify no log assertions)
6. ✅ Before/after log comparison

### ⏱️ Effort Estimate
- **Priority 1:** 6-8 hours (16 files)
- **Priority 2:** 2 hours
- **Priority 3:** 2 hours
- **Priority 4:** 2 hours
- **Testing:** 2-4 hours
- **Total:** **12-16 hours**

### 🎯 Success Metrics
- Startup logs: 79-111 → **12-19 INFO logs** (83% reduction)
- Per-generation: 5 → **1 INFO log** (80% reduction)
- All tests pass
- No behavioral changes

### 🔗 Dependencies
- None (independent change)

### 🚨 Risks
- **LOW:** Tests might assert on log output (easy to fix)
- **Mitigation:** Search for log assertions before starting

---

## 📊 Stap 4: Cache Monitoring Implementatie

### 🎯 Doel
Zichtbaarheid in cache effectiviteit, hit/miss rates, memory usage, en performance.

### 🔍 Rationale
**Huidige situatie:**
- RuleCache werkt goed (100% hit rate) maar geen metrics
- ServiceContainer is singleton maar geen tracking
- Geen inzicht in cache effectiveness over tijd
- Logging zegt "uit cache" maar geen hit/miss stats

**Voordelen:**
- Verify cache optimization actually works
- Detect performance regressions early
- Optimize cache TTL and sizing
- Data-driven decisions

### 📁 Betrokken Files

**Nieuwe files (~1400 lines):**
```
src/monitoring/cache_monitoring.py (300 lines)
src/monitoring/cache_logger.py (100 lines)
src/monitoring/cache_json_backend.py (150 lines)
src/monitoring/metrics_aggregator.py (100 lines)
config/monitoring.yaml (50 lines)
tests/monitoring/test_cache_monitoring.py (300 lines)
tests/monitoring/test_integration.py (200 lines)
```

**Modified files (~65 lines):**
```
src/toetsregels/rule_cache.py (+20 lines)
src/utils/container_manager.py (+30 lines)
src/utils/cache.py (+10 lines)
src/services/container.py (+5 lines)
```

**Optionele files:**
```
src/api/cache_metrics_api.py (100 lines)
src/ui/components/cache_metrics_dashboard.py (50 lines)
```

### 🛠️ Implementatie

#### Phase 1: Foundation (2-3 days)
```python
# src/monitoring/cache_monitoring.py
class CacheMonitor:
    """Base class for cache monitoring."""

    def track_operation(self, op: str, key: str) -> ContextManager:
        """Track cache operation with timing."""
        # Returns context manager

class RuleCacheMonitor(CacheMonitor):
    """Monitor RuleCache operations."""

class ContainerCacheMonitor(CacheMonitor):
    """Monitor ServiceContainer caching."""
```

**Integration pattern:**
```python
# toetsregels/rule_cache.py
with monitor.track_operation("get_all", "rules") as result:
    rules = self._load_all_rules()
    result["source"] = "cache" if cached else "disk"
```

#### Phase 2: Integration (2 days)
- Integrate with RuleCache
- Integrate with ServiceContainer
- Add logging backend
- Test hit/miss tracking

#### Phase 3: Exposure (2-3 days)
- JSON persistence to `data/metrics/`
- Streamlit dashboard (optional)
- Performance benchmarking

#### Phase 4: Polish (1 day)
- Remaining caches (general cache, file cache)
- Documentation
- Optimization

### 📦 Deliverables
1. ✅ Core monitoring classes (`cache_monitoring.py`)
2. ✅ RuleCache integration (+20 lines)
3. ✅ ServiceContainer integration (+30 lines)
4. ✅ Logging backend (`cache_logger.py`)
5. ✅ JSON backend (`cache_json_backend.py`)
6. ✅ Configuration (`monitoring.yaml`)
7. ✅ Tests (500 lines)
8. ✅ Documentation
9. 🔵 OPTIONAL: API endpoints
10. 🔵 OPTIONAL: Streamlit dashboard

### ⏱️ Effort Estimate
- **Phase 1 (Foundation):** 2-3 days
- **Phase 2 (Integration):** 2 days
- **Phase 3 (Exposure):** 2-3 days
- **Phase 4 (Polish):** 1 day
- **Total (core):** **8-10 days**
- **Total (with UI):** **10-12 days**

### 🎯 Success Metrics
- Track 100% of cache operations
- <5ms overhead per operation
- <10MB memory footprint
- Can be disabled with zero overhead
- Hit/miss rates visible in logs and JSON

### 🔗 Dependencies
- **Soft dependency:** Stap 6 (Structured Logging) makes metrics more useful
- **Independent:** Can implement standalone

### 🚨 Risks
- **MEDIUM:** Performance overhead if not careful
- **Mitigation:** Context manager pattern + early return if disabled
- **Testing:** Benchmark before/after

---

## 📊 Stap 5: Lazy Loading Services

### 🎯 Doel
Reduceer startup tijd met 47% (400ms → 210ms) door non-critical services lazy te loaden.

### 🔍 Rationale
**Huidige situatie:**
- Alle services worden geïnitialiseerd tijdens container creation
- DuplicateDetectionService, EditService, ExportService, etc. zijn NIET nodig bij startup
- Eager loading voegt ~150-190ms toe aan startup

**Impact:**
- Generator-only sessie: 400ms → 210ms (47% sneller)
- Edit tab gebruiker: 400ms → 235ms (41% sneller)
- Memory: -5MB per sessie

### 📁 Betrokken Files

**Modified files (~200 lines):**
```
src/services/container.py (+150 lines)
src/ui/components/ (minimal changes)
tests/services/test_container.py (+50 lines)
```

### 🛠️ Implementatie

#### Services Classificatie

**EAGER (keep as-is - ~200ms):**
- DefinitionRepository
- DefinitionOrchestrator
- ValidationOrchestrator
- ModernWebLookupService

**LAZY (load on-demand - ~150ms):**
- DuplicateDetectionService (alleen bij save)
- DefinitionEditService (alleen in edit tab)
- ExportService (alleen bij export)
- ImportService (alleen bij import)
- GatePolicyService (alleen bij validate+save)
- DefinitionWorkflowService (alleen in workflow)
- DataAggregationService (alleen in reports)

#### Implementation Pattern

**Huidige (eager):**
```python
class ServiceContainer:
    def __init__(self):
        self._duplicate_detector = DuplicateDetectionService(...)

    def duplicate_detector(self):
        return self._duplicate_detector
```

**Na (lazy):**
```python
class ServiceContainer:
    def __init__(self):
        self._instances = {}  # Lazy loading cache

    def duplicate_detector(self):
        if "duplicate_detector" not in self._instances:
            logger.info("⚡ DuplicateDetectionService lazy-loaded")
            self._instances["duplicate_detector"] = DuplicateDetectionService(...)
        return self._instances["duplicate_detector"]
```

### 📦 Deliverables
1. ✅ Identify lazy-loadable services (7 services)
2. ✅ Refactor `container.py` with lazy pattern
3. ✅ Add lazy load logging
4. ✅ Tests for lazy loading behavior
5. ✅ Performance benchmarks (startup time)
6. ✅ Documentation update

### ⏱️ Effort Estimate
- **Analysis:** 2 hours (already done)
- **Implementation:** 4 hours
- **Testing:** 3 hours
- **Performance verification:** 1 hour
- **Total:** **10 hours**

### 🎯 Success Metrics
- Startup (generator-only): 400ms → **<250ms** (38%+)
- Startup (with edit): 400ms → **<300ms** (25%+)
- Zero breaking changes
- All tests pass
- First-access delay acceptable (<35ms)

### 🔗 Dependencies
- None (independent change)
- **Synergy:** Stap 7 (Performance Baseline) will track improvements

### 🚨 Risks
- **LOW:** Pattern is simple, well-tested in industry
- **Mitigation:** Comprehensive test coverage, backward compatibility guaranteed

---

## 📊 Stap 6: Structured Logging

### 🎯 Doel
Machine-parseable JSON logs voor analytics, monitoring, en debugging.

### 🔍 Rationale
**Huidige situatie:**
- String-based logs: `logger.info(f"Container init (count: {count})")`
- Niet machine-parseable
- Analytics vereist regex parsing
- Moeilijk te aggregeren over tijd

**Voordelen:**
- jq queries: `jq 'select(.init_count > 1)'`
- Cost tracking: `jq -s 'map(.cost) | add'`
- Performance analysis: `jq 'select(.duration_ms > 5000)'`
- Integration met monitoring tools (Elasticsearch, Grafana)

### 📁 Betrokken Files

**Nieuwe files (~800 lines):**
```
src/utils/structured_logging.py (200 lines)
config/logging_structured.yaml (50 lines)
tests/utils/test_structured_logging.py (150 lines)
docs/architectuur/structured-logging-*.md (3 docs)
```

**Modified files (~2500 lines - gradual migration):**
```
src/services/container.py (~100 lines)
src/services/prompts/prompt_service_v2.py (~50 lines)
src/services/validation/modular_validation_service.py (~50 lines)
... (16+ services)
```

### 🛠️ Implementatie

#### Phase 1: Infrastructure (Week 1 - 4-6h)
```bash
pip install python-json-logger==2.0.7
```

```python
# src/utils/structured_logging.py
from pythonjsonlogger import jsonlogger

def setup_structured_logging():
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(timestamp)s %(level)s %(logger)s %(message)s"
    )
    handler.setFormatter(formatter)
    # ... setup
```

#### Phase 2: Core Services (Weeks 2-3 - 12-16h)
```python
# BEFORE
logger.info(f"Container geïnitialiseerd (count: {count})")

# AFTER
logger.info("Container geïnitialiseerd", extra={
    "component": "service_container",
    "init_count": count,
    "environment": env
})
```

#### Phase 3: Supporting Services (Weeks 4-5 - 16-24h)
- Web lookup, UI, utilities
- Add component-specific fields
- Test analytics queries

#### Phase 4: Optimization (Week 6 - 8-12h)
- Remove f-strings (lazy evaluation)
- Add correlation IDs
- Final documentation

### 📦 Deliverables
1. ✅ `python-json-logger` added to requirements
2. ✅ `structured_logging.py` utility module
3. ✅ Core services migrated (Container, AI, Validation)
4. ✅ Log schema documentation
5. ✅ Analytics query examples
6. ✅ Performance benchmarks (<5% overhead)
7. 🔵 OPTIONAL: Full migration (all services)

### ⏱️ Effort Estimate
- **Phase 1 (Infrastructure):** 4-6 hours
- **Phase 2 (Core):** 12-16 hours
- **Phase 3 (Supporting):** 16-24 hours
- **Phase 4 (Optimization):** 8-12 hours
- **Total (core only):** **16-22 hours**
- **Total (full migration):** **40-58 hours**

### 🎯 Success Metrics
- Core services log in JSON format
- <5% performance overhead
- 5+ working analytics queries
- Backward compatible (old logs still work)

### 🔗 Dependencies
- **Synergy:** Stap 4 (Cache Monitoring) benefits from structured logging
- **Synergy:** Stap 7 (Performance Baseline) benefits from structured logging

### 🚨 Risks
- **MEDIUM:** Performance overhead if not optimized
- **Mitigation:** Lazy evaluation (`%s` formatting), sampling for DEBUG

---

## 📊 Stap 7: Performance Baseline Tracking

### 🎯 Doel
Automatisch detecteren van performance regressies en trends over tijd.

### 🔍 Rationale
**Huidige situatie:**
- Geen tracking van startup tijd over tijd
- Performance regressies worden niet gedetecteerd
- Geen data voor optimalisatie prioritering
- Manual testing is inconsistent

**Voordelen:**
- Auto-detect regressies (>10% = warning)
- Trend analysis (gradual degradation)
- Data-driven optimization
- CI/CD integration (fail PR on regression)

### 📁 Betrokken Files

**Nieuwe files (~4000 lines):**
```
src/monitoring/performance_tracker.py (500 lines)
src/monitoring/baseline_calculator.py (300 lines)
src/monitoring/regression_detector.py (400 lines)
src/ui/components/performance_dashboard.py (200 lines)
src/cli/performance_cli.py (150 lines)
tests/monitoring/test_performance_*.py (800 lines)
docs/architectuur/performance-baseline-*.md (4 docs)
```

**Modified files (~200 lines):**
```
src/main.py (+50 lines - track startup)
src/services/container.py (+30 lines - track init)
src/services/definition_generator.py (+30 lines - track generation)
data/definities.db (new tables - migration)
```

### 🛠️ Implementatie

#### Phase 1: Basic Tracking (4 hours)
```python
# src/monitoring/performance_tracker.py
class PerformanceTracker:
    def track_startup(self, duration_ms: float):
        # Store in SQLite

    def track_operation(self, name: str, duration_ms: float):
        # Store metrics
```

**Database schema:**
```sql
CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY,
    metric_name TEXT NOT NULL,
    value REAL NOT NULL,
    timestamp REAL NOT NULL,
    metadata JSON
);

CREATE TABLE performance_baselines (
    metric_name TEXT PRIMARY KEY,
    baseline_value REAL NOT NULL,
    confidence REAL NOT NULL,
    last_updated REAL NOT NULL
);
```

#### Phase 2: All Metrics (2 days)
- Startup time
- Container initialization
- Rule loading
- Validation time
- Definition generation
- API calls (tokens, cost)
- Memory usage
- Cache hit rates

#### Phase 3: Regression Detection (2 days)
```python
# src/monitoring/regression_detector.py
class RegressionDetector:
    def check(self, metric: str, current: float) -> Alert | None:
        baseline = self.get_baseline(metric)
        if current > baseline * 1.10:  # 10% threshold
            return Alert(severity="warning", ...)
        if current > baseline * 1.20:  # 20% threshold
            return Alert(severity="error", ...)
```

#### Phase 4: UI Dashboard (3 days)
- Streamlit dashboard met charts
- Metric cards (current/target/trend)
- Time-series plots
- Alerts overview

#### Phase 5: CI/CD Integration (1 day)
- GitHub Actions integration
- PR comments with perf comparison
- Fail CI on critical regression

### 📦 Deliverables
1. ✅ Performance tracking infrastructure
2. ✅ Database schema + migration
3. ✅ 13 core metrics tracked
4. ✅ Baseline calculation (rolling median)
5. ✅ Regression detection (3-tier)
6. ✅ CLI commands (status, report, alerts)
7. 🔵 OPTIONAL: Streamlit dashboard
8. 🔵 OPTIONAL: CI/CD integration

### ⏱️ Effort Estimate
- **Phase 1 (Basic):** 4 hours
- **Phase 2 (All Metrics):** 2 days
- **Phase 3 (Regression):** 2 days
- **Phase 4 (UI):** 3 days
- **Phase 5 (CI/CD):** 1 day
- **Total (core):** **4-5 days**
- **Total (with UI+CI):** **7-8 days**

### 🎯 Success Metrics
- Track 13+ performance metrics
- Auto-calculate baselines (20 samples)
- Detect regressions within 1 run
- <50ms overhead per app start
- Historical trending available

### 🔗 Dependencies
- **Builds on:** Stap 4 (Cache Monitoring) - reuse metrics
- **Synergy:** Stap 6 (Structured Logging) - better data
- **Synergy:** Stap 5 (Lazy Loading) - track improvement

### 🚨 Risks
- **MEDIUM:** Database growth (mitigate: archival policy)
- **MEDIUM:** Baseline accuracy (mitigate: outlier removal, confidence score)
- **LOW:** Performance overhead (mitigate: async writing)

---

## 🗓️ Implementatie Timeline

### Week 1: Quick Wins 🚀
**Goal:** Snelle verbeteringen, laag risico, direct impact

| Dag | Stap | Activiteit | Output |
|-----|------|-----------|--------|
| Ma | Stap 1 | Config parameter removal | No more warnings ✅ |
| Di | Stap 2 | Documentatie update | Accurate docs ✅ |
| Wo | Stap 3.1 | Logging - Module init (Priority 1) | -48 logs ✅ |
| Do | Stap 3.2 | Logging - Container + Orchestrator (P2+P3) | -32 logs ✅ |
| Vr | Stap 5 | Lazy loading services | -190ms startup ✅ |

**Week 1 Impact:**
- Startup: 400ms → **210ms** (-47%)
- Logging: 111 → **31 INFO logs** (-72%)
- Code quality: Warnings eliminated, docs accurate

---

### Week 2-3: Foundation 🏗️
**Goal:** Monitoring en analytics infrastructure

| Week | Stap | Activiteit | Effort |
|------|------|-----------|--------|
| 2 | Stap 6.1 | Structured logging - Infrastructure | 4-6h |
| 2 | Stap 6.2 | Structured logging - Core services | 12-16h |
| 3 | Stap 4.1 | Cache monitoring - Foundation | 2-3d |
| 3 | Stap 4.2 | Cache monitoring - Integration | 2d |

**Week 2-3 Impact:**
- JSON logs voor analytics
- Cache hit/miss tracking
- Performance visibility

---

### Week 4-5: Enhancement 📊
**Goal:** Advanced monitoring en optimalisatie

| Week | Stap | Activiteit | Effort |
|------|------|-----------|--------|
| 4 | Stap 7.1-7.2 | Performance tracking (basic + all metrics) | 4h + 2d |
| 4-5 | Stap 6.3 | Structured logging - Supporting services | 16-24h |
| 5 | Stap 4.3 | Cache monitoring - Exposure (JSON/UI) | 2-3d |

**Week 4-5 Impact:**
- Performance baseline tracking
- Regression detection
- Complete monitoring stack

---

### Week 6: Polish & Optimization ✨
**Goal:** Afronding, documentatie, optimization

| Dag | Activiteit | Output |
|-----|-----------|--------|
| Ma-Di | Stap 7.3 | Regression detection + alerts | Auto-detection ✅ |
| Wo | Stap 4.4 | Cache monitoring - Polish | Final optimizations ✅ |
| Do | Stap 6.4 | Structured logging - Optimization | Remove f-strings ✅ |
| Vr | - | Documentation + handoff | Complete docs ✅ |

---

### Optional Extensions (Week 7+)
**Goal:** Advanced features (not required for core benefits)

| Feature | Effort | Value |
|---------|--------|-------|
| Stap 7.4: Streamlit dashboard | 3d | 🟢 HIGH (visualization) |
| Stap 7.5: CI/CD integration | 1d | 🟢 HIGH (automated checks) |
| Stap 4: API endpoints | 1d | 🟡 MEDIUM (external access) |
| Stap 6: Full migration (all services) | 2-3w | 🟡 MEDIUM (consistency) |

---

## 📈 Cumulative Impact

### Performance Improvements

| Milestone | Startup Time | Reduction | Logging Overhead |
|-----------|--------------|-----------|------------------|
| **Baseline** | 400ms | - | 111 INFO logs |
| After Week 1 | **210ms** | -47% | 31 INFO logs |
| After Week 2-3 | 210ms | -47% | 19 INFO logs |
| After Week 4-5 | 210ms | -47% | 12 INFO logs |
| **Final** | **210ms** | **-47%** | **12 INFO logs (-89%)** |

### Monitoring Coverage

| Week | Cache Monitoring | Performance Tracking | Structured Logging |
|------|------------------|---------------------|-------------------|
| Baseline | 0% | 0% | 0% |
| Week 1 | 0% | 0% | 0% |
| Week 2-3 | 60% | 0% | 40% |
| Week 4-5 | 100% | 80% | 60% |
| **Week 6** | **100%** | **100%** | **80%+** |

---

## 🎯 Success Criteria

### Functional Requirements ✅
- [ ] Zero config warnings in logs
- [ ] Startup time <250ms (generator-only sessions)
- [ ] <20 INFO logs during startup
- [ ] Cache hit/miss rates visible
- [ ] Performance baselines established
- [ ] Regression detection working
- [ ] JSON logs for core services

### Non-Functional Requirements ✅
- [ ] <5% performance overhead (monitoring)
- [ ] <10MB memory overhead (monitoring)
- [ ] Zero breaking changes
- [ ] All tests pass
- [ ] Documentation complete

### Quality Requirements ✅
- [ ] Code review passed
- [ ] Test coverage >80%
- [ ] No new warnings/errors
- [ ] Backward compatible

---

## 🚨 Risks & Mitigation

### Technical Risks

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Performance overhead from monitoring | 🟡 MEDIUM | 🟢 LOW | Context manager pattern, can disable |
| Breaking changes in refactoring | 🔴 HIGH | 🟢 LOW | Comprehensive tests, gradual migration |
| Database growth (baseline tracking) | 🟡 MEDIUM | 🟡 MEDIUM | Archival policy, data rotation |
| Baseline inaccuracy | 🟡 MEDIUM | 🟡 MEDIUM | Outlier removal, confidence scoring |

### Project Risks

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Scope creep (too many features) | 🟡 MEDIUM | 🟡 MEDIUM | Phased approach, optional extensions |
| Timeline overrun | 🟡 MEDIUM | 🟡 MEDIUM | Focus on quick wins first |
| Incomplete testing | 🔴 HIGH | 🟢 LOW | Test-driven approach, coverage requirements |

---

## 📚 Dependencies & Sequencing

### Must-Do-First (Week 1)
```
Stap 1 (Config Removal) → Stap 2 (Docs) → Stap 3 (Logging) → Stap 5 (Lazy Loading)
```
**Rationale:** Quick wins, no dependencies, immediate impact

### Foundation (Week 2-3)
```
Stap 6.1-6.2 (Structured Logging Infrastructure)
Stap 4.1-4.2 (Cache Monitoring Foundation)
```
**Rationale:** Infrastructure for later phases

### Enhancement (Week 4-5)
```
Stap 7 (Performance Baseline) ← depends on → Stap 4 (Cache Monitoring)
Stap 6.3 (Structured Logging Expansion) ← benefits from → Stap 4 & 7
```
**Rationale:** Advanced features build on foundation

---

## 🔧 Development Setup

### Prerequisites
```bash
# Ensure Python 3.11+
python --version

# Install new dependencies
pip install python-json-logger==2.0.7

# Verify test environment
pytest --version
```

### Branching Strategy
```bash
# Week 1: Quick Wins
git checkout -b perf/quick-wins-week1
# Stap 1-3, 5

# Week 2-3: Foundation
git checkout -b perf/monitoring-foundation
# Stap 4.1-4.2, 6.1-6.2

# Week 4-5: Enhancement
git checkout -b perf/advanced-monitoring
# Stap 7, 6.3, 4.3

# Week 6: Polish
git checkout -b perf/polish-and-docs
# Final optimizations, documentation
```

### Testing Strategy
```bash
# Before each commit
pytest -q  # All tests
pytest --cov=src --cov-report=html  # Coverage

# Before each PR
make lint  # Ruff + Black
make test  # Full test suite
python scripts/ai_code_reviewer.py  # AI review

# Performance benchmarks
python -m timeit "import src.main"  # Startup time
/usr/bin/time -l streamlit run src/main.py  # Memory usage
```

---

## 📖 Documentation Updates

### Files to Update
```
docs/architectuur/TECHNICAL_ARCHITECTURE.md (add monitoring section)
docs/INDEX.md (link new architecture docs)
CLAUDE.md (update performance section, known issues)
README.md (add monitoring features)
```

### New Documentation
```
docs/architectuur/cache-monitoring-design.md ✅ (created)
docs/architectuur/lazy-loading-design.md ✅ (created)
docs/architectuur/structured-logging-architecture.md ✅ (created)
docs/architectuur/performance-baseline-tracking-design.md ✅ (created)
docs/planning/PERFORMANCE_OPTIMIZATION_MASTERPLAN.md ✅ (this document)
```

---

## 🎓 Lessons Learned (To Be Updated)

### What Worked Well
- Multi-agent analysis approach
- Phased implementation strategy
- Focus on quick wins first

### What Could Be Improved
- TBD (update during implementation)

### Key Insights
- TBD (update during implementation)

---

## 📞 Support & Questions

### Technical Questions
- Architecture: Review `docs/architectuur/` documents
- Implementation: Check individual design docs
- Testing: See test files in `tests/`

### Project Management
- Timeline: See "Implementatie Timeline" section
- Dependencies: See "Dependencies & Sequencing" section
- Risks: See "Risks & Mitigation" section

---

## ✅ Sign-Off

### Pre-Implementation Checklist
- [ ] Masterplan reviewed by team
- [ ] Priority confirmed (start with Week 1?)
- [ ] Timeline approved
- [ ] Resources allocated (developer time)
- [ ] Success criteria agreed upon

### Ready to Start?
**Recommended:** Start with Week 1 (Quick Wins) immediately
- Low risk
- High impact
- Builds confidence
- Provides quick ROI

---

**Generated:** 2025-10-07
**Version:** 1.0
**Status:** READY FOR EXECUTION
**Next Action:** Review + Approve + Begin Week 1
