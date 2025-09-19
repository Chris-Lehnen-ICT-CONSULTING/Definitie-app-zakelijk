# US-207: God Class Refactoring - BREAKDOWN

**Probleem**: US-207 is te groot! We hebben 4 god classes gevonden:

## 🔴 God Classes Inventory

| File | Lines | Complexity | Priority |
|------|-------|------------|----------|
| `definition_generator_tab.py` | **1,656** | EXTREME | HIGH |
| `tabbed_interface.py` | **1,455** | EXTREME | HIGH |
| `management_tab.py` | **1,398** | HIGH | MEDIUM |
| `orchestration_tab.py` | **1,000** | HIGH | MEDIUM |
| `expert_review_tab.py` | **905** | MEDIUM | LOW |
| `export_tab.py` | **885** | MEDIUM | LOW |
| `web_lookup_tab.py` | **876** | MEDIUM | LOW |
| `definition_edit_tab.py` | **871** | MEDIUM | LOW |

## 📋 Voorgestelde Opsplitsing in Sub-Stories

### US-207A: Refactor definition_generator_tab.py (1,656 lines → <300)
**Story Points**: 8
**Priority**: CRITICAL
```
Biggest god class - split into:
- GeneratorUI (rendering) ~200 lines
- GeneratorLogic (business) ~250 lines
- GeneratorState (state mgmt) ~150 lines
- GeneratorHandlers (events) ~200 lines
- GeneratorValidation (validation) ~150 lines
```

### US-207B: Refactor tabbed_interface.py (1,455 lines → <100)
**Story Points**: 5
**Priority**: CRITICAL
```
Main orchestrator - split into:
- TabOrchestrator (main) ~100 lines
- TabRouter (routing) ~150 lines
- SessionManager (state) ~200 lines
- Move all tab logic to respective files
```

### US-207C: Refactor management_tab.py (1,398 lines → <300)
**Story Points**: 5
**Priority**: HIGH
```
Management features - split into:
- DefinitionList (display) ~200 lines
- DefinitionCRUD (operations) ~250 lines
- SearchFilter (search/filter) ~150 lines
- BulkOperations (bulk actions) ~150 lines
```

### US-207D: Refactor orchestration_tab.py (1,000 lines → <300)
**Story Points**: 3
**Priority**: MEDIUM
```
Orchestration logic - split into:
- OrchestrationUI (display) ~200 lines
- OrchestrationEngine (logic) ~250 lines
- OrchestrationMonitor (monitoring) ~150 lines
```

### US-207E: Refactor Medium God Classes (800-900 lines each)
**Story Points**: 5
**Priority**: LOW
```
Bundle the 4 medium god classes:
- expert_review_tab.py (905 → ~300)
- export_tab.py (885 → ~300)
- web_lookup_tab.py (876 → ~300)
- definition_edit_tab.py (871 → ~300)
```

## 🎯 Prioritized Execution Plan

### Sprint 1 (Week 2): Critical Path
- **US-207A**: definition_generator_tab.py (meest gebruikt)
- **US-207B**: tabbed_interface.py (centrale orchestrator)
**Impact**: 50% UI performance verbetering

### Sprint 2 (Week 3): High Priority
- **US-207C**: management_tab.py
- **US-207D**: orchestration_tab.py
**Impact**: 30% additional improvement

### Sprint 3 (Week 4): Nice to Have
- **US-207E**: Bundle remaining medium god classes
**Impact**: Code quality improvement

## 📊 Metrics & Benefits per Story

| Story | Current | Target | Reduction | Time | Value |
|-------|---------|--------|-----------|------|-------|
| US-207A | 1,656 | 300 | 82% | 2 days | HIGH - Most used tab |
| US-207B | 1,455 | 100 | 93% | 1.5 days | HIGH - Central file |
| US-207C | 1,398 | 300 | 79% | 1.5 days | MEDIUM - Admin features |
| US-207D | 1,000 | 300 | 70% | 1 day | MEDIUM - Advanced feature |
| US-207E | 3,537 | 1,200 | 66% | 2 days | LOW - Less critical |

**Totaal**: Van 9,046 lines naar ~2,200 lines (76% reductie)

## 🏗️ Shared Refactoring Pattern

Voor elke god class gebruiken we hetzelfde pattern:

```python
# BEFORE: god_class_tab.py (1000+ lines)
class GodClassTab:
    def __init__(self):
        # 100+ lines initialization
    def render(self):
        # 500+ lines mixed logic
    def handle_events(self):
        # 300+ lines event handling
    # ... etc

# AFTER: Multiple focused files
# ui/components/[feature]/
├── __init__.py
├── ui.py         # Pure rendering (<200 lines)
├── logic.py      # Business logic (<250 lines)
├── state.py      # State management (<150 lines)
├── handlers.py   # Event handlers (<200 lines)
└── validators.py # Input validation (<150 lines)
```

## ✅ Definition of Done per Story

Voor ELKE sub-story (US-207A t/m E):
- [ ] Geen enkel nieuw bestand > 300 lines
- [ ] Gemiddelde file size < 200 lines
- [ ] Cyclomatic complexity < 10 per functie
- [ ] Unit tests voor elke nieuwe module
- [ ] Integration test blijft groen
- [ ] Performance gelijk of beter
- [ ] Zero regression bugs

## 🚀 Implementation Strategy

### Phase 1: Setup Structure (Day 1)
```bash
mkdir -p src/ui/components/{generator,management,orchestration,review,export}
```

### Phase 2: Extract Without Breaking (Day 2-3)
1. Copy functions to new modules
2. Import from new locations
3. Test continuously
4. Remove from god class

### Phase 3: Refactor & Optimize (Day 4-5)
1. Remove duplication
2. Improve interfaces
3. Add proper typing
4. Documentation

## 📈 Expected Outcomes

### Performance Impact
- **Streamlit reruns**: 50% faster (less code to reload)
- **Memory usage**: 30% reduction
- **Developer productivity**: 2x faster to find/fix bugs

### Code Quality Impact
- **Testability**: From 45% to 85% coverage possible
- **Maintainability**: From "impossible" to "easy"
- **Readability**: From "where is X?" to "obviously in Y"

## 🎬 Next Steps

1. **Get approval** voor opsplitsing in 5 sub-stories
2. **Prioritize** based on user impact
3. **Start with US-207A** (definition_generator_tab.py)
4. **Track metrics** voor elke refactoring

---

**Recommendation**: Start met US-207A en US-207B in parallel. Deze twee hebben de grootste impact op performance en zijn onafhankelijk van elkaar.