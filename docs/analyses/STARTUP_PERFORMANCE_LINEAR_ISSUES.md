# Startup Performance - Linear Issues Overzicht

**Aangemaakt:** 2025-10-30
**Basis:** Multi-agent analyse van startup log (537ms → target <200ms)
**Analyse documenten:**
- `docs/analyses/STARTUP_PERFORMANCE_ANALYSIS.md`
- `docs/analyses/STARTUP_PERFORMANCE_DIAGRAM.md`

---

## 📊 Overzicht Aangemaakte Issues

**Totaal:** 7 Linear issues
**Verdeling:**
- 🥇 **Phase 1 (Quick Wins):** 4 issues - HIGH priority, 2.5 uur, -380ms
- 🥈 **Phase 2 (DRY Cleanup):** 3 issues - MEDIUM priority, 7 uur, -300ms

**Geschatte totale impact:** 537ms → ~160ms (70% verbetering)

---

## 🥇 Phase 1: Quick Wins (DO FIRST)

### ⭐⭐⭐⭐⭐ HIGHEST ROI - Start hier!

#### [DEF-60: Implement true lazy loading for 5 optional services](https://linear.app/definitie-app/issue/DEF-60)
- **Priority:** HIGH (2)
- **Effort:** 1 uur
- **Impact:** -180ms init time, -15MB memory
- **Status:** Todo

**Services om lazy te maken:**
1. ModernWebLookupService (alleen bij web lookup enabled)
2. GPT4SynonymSuggester (alleen bij synonym flow)
3. ExportService (alleen bij export click)
4. DataAggregationService (zelden gebruikt)
5. PerformanceTracker (dev mode only)

**Implementatie:** `@property` pattern met lazy initialization

---

#### [DEF-61: Merge PromptOrchestrator + Adapter + Builder layers](https://linear.app/definitie-app/issue/DEF-61)
- **Priority:** HIGH (2)
- **Effort:** 1 uur
- **Impact:** -150ms init, -800 lines code
- **Status:** Todo

**Probleem:** 4-layer abstraction voor prompt building
- PromptOrchestrator (435ms = 85% van bottleneck!)
- ModularPromptAdapter
- UnifiedPromptBuilder
- DocumentProcessor

**Oplossing:** Merge naar single `PromptBuilder` class

---

#### [DEF-62: Replace 3 Context managers with simple dataclass](https://linear.app/definitie-app/issue/DEF-62)
- **Priority:** MEDIUM (3)
- **Effort:** 30 minuten
- **Impact:** -50ms init, -200 lines code
- **Status:** Todo

**Te mergen:**
- HybridContextManager
- ContextManager
- ContextStateCleaner

**Oplossing:** Simple `@dataclass DefinitionContext`

---

#### [DEF-66: Fix TabbedInterface cache miss (509ms vs 20ms expected)](https://linear.app/definitie-app/issue/DEF-66)
- **Priority:** HIGH (2)
- **Effort:** 1 uur (na DEF-60, DEF-61, DEF-62)
- **Impact:** Cache miss acceptabel maken (<180ms)
- **Status:** Todo
- **Blocked by:** DEF-60, DEF-61, DEF-62

**Probleem:** Log warning over 509ms vs 20ms expected
**Root cause:** Cache werkt, maar init is te zwaar (27 services eager)
**Oplossing:** Fix cache key stability + reduce init weight via dependencies

---

### 📊 Phase 1 Totaal
- **Effort:** 2.5 uur (1 middag)
- **Impact:** 537ms → ~160ms ✅ **MEETS <200ms TARGET**
- **Complexity:** 27 → 22 services
- **Risk:** Low (mechanische refactors)

**Volgorde:**
1. DEF-60 (lazy loading) - 1h
2. DEF-61 (merge prompt) - 1h
3. DEF-62 (merge context) - 30min
4. DEF-66 (fix cache) - 1h (na 1-3)

---

## 🥈 Phase 2: DRY Cleanup (AFTER Phase 1)

### ⭐⭐⭐⭐ CODE QUALITY - Doe alleen als Phase 1 succesvol

#### [DEF-63: Consolidate 3 Definition services (DRY violation)](https://linear.app/definitie-app/issue/DEF-63)
- **Priority:** MEDIUM (3)
- **Effort:** 3 uur
- **Impact:** -80ms init, -600 lines (DRY fix)
- **Status:** Todo

**DRY Violation:** CRUD logic in 3 services:
- DefinitionOrchestratorV2
- DefinitionRepository
- DefinitionEditService

**Oplossing:** Merge naar single `DefinitionService`

---

#### [DEF-64: Flatten Manager pattern (5 managers → config + dataclasses)](https://linear.app/definitie-app/issue/DEF-64)
- **Priority:** MEDIUM (3)
- **Effort:** 2 uur
- **Impact:** -120ms init, -400 lines
- **Status:** Todo

**Te vereenvoudigen:**
- ConfigManager → AppConfig singleton
- CachedToetsregelManager → RuleCache class method
- HybridContextManager → dataclass (zie DEF-62)
- ContextManager → dataclass (zie DEF-62)
- SynonymRegistry → Dict[str, List[str]]

---

#### [DEF-65: ServiceContainer slimming (27 → 10 core + 5 lazy)](https://linear.app/definitie-app/issue/DEF-65)
- **Priority:** LOW (4)
- **Effort:** 2 uur
- **Impact:** -100ms init, clearer architecture
- **Status:** Todo
- **Depends on:** DEF-60, DEF-61, DEF-62 (optional: DEF-63, DEF-64)

**Doel:** 10 core services (altijd geladen) + 5 lazy properties

---

### 📊 Phase 2 Totaal
- **Effort:** 7 uur (spread over 2-3 weken)
- **Impact:** -300ms extra, -1200 lines code
- **Complexity:** 8.5/10 → 4/10 (solo dev maintainable)
- **Risk:** Medium (requires workflow testing)

**Volgorde:**
1. DEF-63 (merge definitions) - 3h, week 1
2. DEF-64 (flatten managers) - 2h, week 2
3. DEF-65 (container slim) - 2h, week 3 (coördinatie task)

---

## 🎯 Aanbevolen Implementatie Strategie

### Week 1: Phase 1 (Performance Fix) ✅ CRITICAL
**Doel:** Haal <200ms target

**Maandag middag (2.5 uur):**
- [ ] DEF-60: Lazy loading (1h)
- [ ] DEF-61: Merge prompt layers (1h)
- [ ] DEF-62: Merge context (30min)

**Maandag eind:** Test, meet performance (moet ~160ms zijn)

**Dinsdag ochtend (1 uur):**
- [ ] DEF-66: Fix cache stability (1h)

**Dinsdag middag:** Final testing, merge

**Success criteria:**
- ✅ Startup < 200ms
- ✅ Alle UI tabs werken
- ✅ Tests groen

---

### Week 2-4: Phase 2 (Code Quality) ⚡ OPTIONAL
**Doel:** DRY compliance, maintainability

**Alleen doen als:**
- ✅ Phase 1 succesvol (< 200ms behaald)
- ✅ Geen blocker bugs
- ✅ Tijd over voor refactoring

**Week 2:**
- [ ] DEF-63: Merge definitions (3h, over 2 dagen)

**Week 3:**
- [ ] DEF-64: Flatten managers (2h, 1 middag)

**Week 4:**
- [ ] DEF-65: Container cleanup (2h, coördinatie)

---

## 📈 Verwachte Resultaten

### Na Phase 1 (Week 1)
```
BEFORE:
- Startup: 537ms
- Services: 27 eager loaded
- TabbedInterface: 509ms (25x too slow)
- Complexity: 8.5/10

AFTER PHASE 1:
- Startup: ~160ms ✅ (70% sneller)
- Services: 10 core + 5 lazy
- TabbedInterface: <180ms ✅ (9x verbetering)
- Complexity: 7/10
```

### Na Phase 2 (Week 2-4) - OPTIONAL
```
AFTER PHASE 1+2:
- Startup: ~100ms ✅✅ (81% sneller)
- Services: 10 core + 5 lazy (geconsolideerd)
- Lines removed: -2000
- Complexity: 4/10 ✅ (solo dev friendly)
- DRY violations: FIXED
```

---

## 🚨 Dependencies & Blockers

### Critical Path (Phase 1)
```
DEF-60 (lazy) ──┐
                 ├─→ DEF-66 (cache fix)
DEF-61 (prompt)─┤
                 │
DEF-62 (context)┘
```

**DEF-66 is blocked** totdat DEF-60, DEF-61, DEF-62 compleet zijn!

### Phase 2 Dependencies
```
DEF-60 ──┐
DEF-61 ──┤
DEF-62 ──┼─→ DEF-65 (container cleanup)
DEF-63 ──┤
DEF-64 ──┘
```

**DEF-65 coördineert** alle andere improvements.

---

## 📚 Referentie Documenten

### Analyse Documenten
- **`docs/analyses/STARTUP_PERFORMANCE_ANALYSIS.md`**
  Technische analyse met timing breakdown en root cause

- **`docs/analyses/STARTUP_PERFORMANCE_DIAGRAM.md`**
  Visual flowcharts en performance comparison

### Multi-Agent Rapporten
- **Debug Specialist:** Performance profiling (435ms PromptOrchestrator)
- **Code Reviewer:** Architecture quality score (6.5/10)
- **Code Simplifier:** Complexity assessment (8.5/10 → 4/10 target)

### Context
- **UNIFIED_INSTRUCTIONS.md:** Approval ladder, workflow selection
- **CLAUDE.md:** Performance goals (<200ms UI), US-202 fixes
- **US-202:** ServiceContainer singleton fix (Oct 7, 2025)

---

## ✅ Success Metrics

### Phase 1 (Performance) - MUST ACHIEVE
- [ ] Startup time < 200ms (current: 537ms)
- [ ] TabbedInterface < 180ms on cache miss (current: 509ms)
- [ ] Cache hit rate > 90%
- [ ] All 4 UI tabs functional
- [ ] Tests passing (no regressions)
- [ ] Memory usage < 60MB at startup (current: ~70MB)

### Phase 2 (Quality) - NICE TO HAVE
- [ ] Code complexity ≤ 4/10
- [ ] No DRY violations in definition/context services
- [ ] < 10 core services in container
- [ ] Lines of code reduced by ~2000
- [ ] Solo dev: can reason about architecture in < 5 min

---

## 🎯 Next Actions

**Voor implementatie:**
1. Review deze issue lijst
2. Confirm prioritering (Phase 1 first? Skip Phase 2?)
3. Start met DEF-60 (hoogste ROI, 1 uur)
4. Measure baseline performance (current 537ms)
5. Implement DEF-60, DEF-61, DEF-62 (2.5h blok)
6. Measure improvement (target: ~160ms)
7. DEF-66 als final polish

**Hulp nodig?**
- Code reviews per issue beschikbaar
- Detailed implementation patches op verzoek
- Testing strategy per issue
- Performance regression tests

---

**Status:** 7 issues klaar voor implementatie
**Estimated total effort:** 9.5 uur (2.5h Phase 1 + 7h Phase 2)
**Expected improvement:** 70-81% sneller startup
**Risk level:** Low (Phase 1), Medium (Phase 2)
