# Linear Issues Dependency Graph - DefinitieAgent
**Date:** 2025-10-30
**Visual representation of issue dependencies and critical paths**

---

## 🎯 CRITICAL PATH VISUALIZATION

```
BLOCKING ISSUES (MUST FIX FIRST)
═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│  P0: DATA LOSS PREVENTION (DAYS 1-2)                       │
│  🔴 BLOCKS ALL OTHER WORK                                   │
└─────────────────────────────────────────────────────────────┘
         │
         ├──► DEF-74: Pydantic validation enforcement (2h)
         │         │
         │         └──► Blocks DEF-69 ──┐
         │                               │
         ├──► DEF-69: Voorbeelden save errors (3-4h)
         │         │                     │
         │         └──► Blocks CSV import
         │                               │
         └──► DEF-68: Context validation errors (2-3h)
                   │                     │
                   └──► Blocks all imports
                                         │
                                         ▼
                        ┌──────────────────────────────────┐
                        │  SAFE IMPORT OPERATIONS          │
                        │  ✅ Data integrity guaranteed    │
                        └──────────────────────────────────┘
```

---

## 🔗 DEPENDENCY CHAINS

### Chain 1: Data Integrity (CRITICAL)
```
START
  │
  ├─► [DEF-74] Pydantic validation
  │        │
  │        ├─► prevents: TypeError crashes
  │        ├─► enables:  Safe voorbeelden input
  │        │
  │        └──► BLOCKS ──► [DEF-69] Voorbeelden save errors
  │                              │
  │                              ├─► prevents: Silent data loss
  │                              ├─► enables:  Reliable CSV import
  │                              │
  │                              └──► BLOCKS ──► [DEF-68] Context validation
  │                                                    │
  │                                                    ├─► prevents: Silent corruption
  │                                                    ├─► enables:  Safe validation flow
  │                                                    │
  │                                                    └──► ENABLES ──► ✅ SAFE OPERATIONS
  │
END: Data integrity guaranteed
     - No silent exceptions
     - All errors logged
     - User feedback on failures
```

**CRITICAL:** Sequential execution required - each step blocks the next!

---

### Chain 2: SessionState Compliance
```
START
  │
  ├─► [DEF-73] Fix 10 st.session_state violations (3-4h)
  │        │
  │        ├─► Replaces: Direct st.session_state[...] access
  │        ├─► With: SessionStateManager.get_value()
  │        │
  │        └──► ENABLES ──► Streamlit anti-pattern prevention
  │                              │
  │                              ├─► Pre-commit hook enforcement
  │                              ├─► UI stability improvements
  │                              │
  │                              └──► ✅ COMPLIANT UI
  │
END: SessionStateManager is single source of truth
     - No direct st.session_state access
     - Pre-commit hook prevents violations
     - Easier debugging
```

**Impact:** 10 files need updates, but LOW risk (find-replace pattern)

---

### Chain 3: Performance Optimization
```
START
  │
  ├─► [DEF-60] Lazy tab loading (4h)
  │        │
  │        ├─► Reduces: 509ms → 180ms (65% faster)
  │        ├─► Method: Defer tab component initialization
  │        │
  │        └──► ENABLES ──► [DEF-61] Async prompt loading (8h)
  │                              │
  │                              ├─► Reduces: 180ms → 90ms (50% faster)
  │                              ├─► Method: Parallel module loading
  │                              │
  │                              └──► ENABLES ──► [DEF-66] Cache tuning (2h)
  │                                                    │
  │                                                    ├─► Final: < 100ms startup
  │                                                    │
  │                                                    └──► ✅ PERFORMANCE TARGET MET
  │
END: Total improvement 82% (509ms → 90ms)
     - Lazy tab initialization
     - Async prompt loading
     - Optimized caching
```

**Recommended:** Phase approach (Week 1: DEF-60, Week 2: DEF-61, Week 3: DEF-66)

---

### Chain 4: God Object Simplification (LONG-TERM)
```
START
  │
  ├─► [DEF-70] ServiceContainer simplification (4-6h)
  │        │
  │        ├─► Reduces: 818 LOC → 100-150 LOC (82-88%)
  │        ├─► Method: Replace with module singletons
  │        │
  │        └──► ENABLES ──► [DEF-60] Lazy loading (easier implementation)
  │                              │
  │                              └──► Performance boost
  │
  ├─► [DEF-71] DefinitieRepository simplification (8-12h)
  │        │
  │        ├─► Reduces: 2,101 LOC → 300-400 LOC (81-86%)
  │        ├─► Method: Remove dual repository, direct SQL
  │        │
  │        └──► ENABLES ──► Simpler tests, faster development
  │
  └──► ENABLES ──► [DEF-72] Directory consolidation (8-10h)
                        │
                        ├─► Reduces: 34 dirs → 8 dirs
                        │
                        └──► ✅ MAINTAINABLE CODEBASE
  │
END: 70-80% LOC reduction across 5 major components
     - Simpler architecture
     - Easier onboarding
     - Faster testing
```

**Risk:** MEDIUM (database layer changes require careful testing)
**Recommended:** Phase 1 (ServiceContainer) first, then Phase 2 (Repository)

---

## 🚧 BLOCKING RELATIONSHIPS

### What Blocks What?

```
DEF-74 (Pydantic validation)
   ↓ BLOCKS
DEF-69 (Voorbeelden save errors)
   ↓ BLOCKS
All CSV import operations
All voorbeelden reliability
   ↓ BLOCKS
DEF-45 (Voorbeelden consistency)


DEF-68 + DEF-69 + DEF-74 (Data integrity)
   ↓ BLOCKS
DEF-35 (Classifier MVP)
   ↓ BLOCKS
DEF-38 (Ontological prompt fixes)
   ↓ BLOCKS
DEF-40 (Category-specific prompts)


DEF-70 (ServiceContainer simplification)
   ↓ ENABLES (easier implementation)
DEF-60 (Lazy tab loading)
   ↓ ENABLES
DEF-61 (Async prompt loading)


DEF-70 + DEF-71 (God object splits)
   ↓ ENABLES
DEF-72 (Directory consolidation)
   ↓ ENABLES
DEF-63, DEF-64, DEF-65 (Module consolidation)
```

---

## 📊 RISK vs EFFORT MATRIX

```
    HIGH RISK
        │
    🔴  │  DEF-68 ●────────────────┐
        │  DEF-69 ●────────────┐   │
        │  DEF-74 ●──────┐     │   │ (P0 CRITICAL)
        │                │     │   │
        │                │     │   │
    🟡  │           DEF-71 ●   │   │ (God objects)
        │                │ DEF-70 ●│
        │                │     │   │
        │                │     │   │
    🟠  │          DEF-35 ●─────┐  │ (Classifier MVP)
        │                │      │  │
        │  DEF-60 ●      │      │  │ (Performance)
        │  DEF-61 ●──────┘      │  │
        │                       │  │
    🟢  │  DEF-73 ●             │  │ (SessionState)
        │  DEF-66 ●             │  │
        │                       │  │
        │  DEF-38, DEF-40 ●─────┘  │ (Features)
        │  DEF-42, DEF-45 ●────────┘
        │
    LOW │  DEF-72, DEF-63-65 ●       (Cleanup)
    RISK│  DEF-75-77, DEF-78-79 ●
        │
        └────────────────────────────────
         1h   5h   10h  15h  20h  EFFORT
        LOW           HIGH
```

**Legend:**
- 🔴 Critical (P0) - Data loss risk
- 🟡 High (P1) - Blocking features
- 🟠 Medium (P2) - Performance/architecture
- 🟢 Low (P3/P4) - Quality/cleanup

**Prioritization:** Risk first, then effort

---

## ⏱️ SEQUENTIAL vs PARALLEL WORK

### Can Run in PARALLEL (Same week)
```
Week 1:
┌──────────────────┐   ┌──────────────────┐
│  DEF-73          │   │  After P0 done:  │
│  SessionState    │ ∥ │  Documentation   │
│  violations      │   │  updates         │
│  (3-4h)          │   │  (2h)            │
└──────────────────┘   └──────────────────┘

Week 2:
┌──────────────────┐   ┌──────────────────┐
│  DEF-60          │   │  DEF-38, DEF-40  │
│  Lazy loading    │ ∥ │  Prompt work     │
│  (4h)            │   │  (if DEF-35 done)│
└──────────────────┘   └──────────────────┘
```

### MUST Run SEQUENTIALLY (Days)
```
Day 1-2: P0 Data Loss Prevention
┌───────────────┐
│  DEF-74       │  (2h)
└───────┬───────┘
        │ BLOCKS
        ▼
┌───────────────┐
│  DEF-69       │  (3-4h)
└───────┬───────┘
        │ BLOCKS
        ▼
┌───────────────┐
│  DEF-68       │  (2-3h)
└───────────────┘

Day 3: SessionState
┌───────────────┐
│  DEF-73       │  (3-4h)
└───────────────┘

Day 4: Performance
┌───────────────┐
│  DEF-60       │  (4h)
└───────────────┘

Week 2: Classifier MVP
┌───────────────┐
│  DEF-35       │  (16-20h)
└───────────────┘
```

**Critical:** P0 chain MUST be sequential - no parallelization possible!

---

## 🎯 RECOMMENDED EXECUTION ORDER

### PHASE 0: Data Loss Prevention (DAYS 1-2) 🔴 CRITICAL
```
Priority: HIGHEST
Risk: Data loss in production
Impact: Blocks all other work

1. DEF-74: Enforce Pydantic validation     [2h]   ●━━━━━┐
2. DEF-69: Add voorbeelden error handling  [3-4h] ●━━━━━┤ Sequential
3. DEF-68: Add context error handling      [2-3h] ●━━━━━┘

Total: 7-9 hours
Success: No silent exceptions, all errors logged
```

### PHASE 1: Quick Wins (DAYS 3-4) 🟡 HIGH
```
Priority: High value, low risk
Risk: UI stability issues
Impact: Enables safe development

1. DEF-73: Fix SessionState violations     [3-4h] ●━━━━━┐
2. DEF-60: Lazy tab loading               [4h]   ●━━━━━┤ Parallel
   Documentation updates                   [2h]   ●━━━━━┘

Total: 9-10 hours
Success: SessionState compliant, 65% faster startup
```

### PHASE 2: Critical Feature (WEEK 2) 🟠 MEDIUM
```
Priority: Blocking other features
Risk: Integration complexity
Impact: Enables ontological work

1. DEF-35: Classifier MVP                  [16-20h] ●━━━━━━━━

Total: 16-20 hours
Success: 80%+ accuracy, AI fallback working
```

### PHASE 3: God Objects (WEEKS 3-4) 🟢 LOW (OPTIONAL)
```
Priority: Long-term maintainability
Risk: Database changes
Impact: 70-80% code reduction

Week 3:
1. DEF-70: ServiceContainer → Singletons   [4-6h]  ●━━━━━┐
2. Update all service access patterns      [2h]    ●━━━━━┘

Week 4:
1. DEF-71: Repository simplification       [8-12h] ●━━━━━━━━
2. Database migration testing              [2h]    ●━━━━━

Total: 16-20 hours
Success: 70-80% LOC reduction, faster tests
```

---

## 📈 PROGRESS TRACKING

### Week 1 Milestones
- [ ] Day 1: DEF-74 complete (Pydantic enforced)
- [ ] Day 2: DEF-69 complete (Voorbeelden errors handled)
- [ ] Day 2: DEF-68 complete (Context errors handled)
- [ ] Day 3: DEF-73 complete (SessionState compliant)
- [ ] Day 4: DEF-60 complete (Lazy loading working)

### Week 2 Milestones
- [ ] Day 5-7: DEF-35 complete (Classifier MVP done)
- [ ] Ontological prompts validated
- [ ] Integration tests passing

### Week 3-4 Milestones (OPTIONAL)
- [ ] Week 3: DEF-70 complete (Singleton pattern)
- [ ] Week 4: DEF-71 complete (Repository simplified)
- [ ] All tests passing
- [ ] 70%+ code reduction achieved

---

## 🚨 EMERGENCY PROTOCOLS

### If Data Loss Detected
```
IMMEDIATE ACTIONS:
1. STOP all development work
2. Rollback last changes (git)
3. Restore database from backup
4. Root cause analysis (which issue?)
5. Fix + test + deploy
6. Resume normal work
```

### If Silent Failure Found
```
IMMEDIATE ACTIONS:
1. Add logging IMMEDIATELY (don't wait for fix)
2. Create emergency Linear issue (P0)
3. Add to critical path (blocks other work)
4. Fix within 24 hours
```

### If Performance Regression > 20%
```
IMMEDIATE ACTIONS:
1. Measure baseline (before/after)
2. Rollback optimization if critical
3. Profile bottleneck
4. Fix or revert permanently
```

---

## 📚 REFERENCES

### Analysis Documents
- **Main Analysis:** `LINEAR_ISSUES_DEPENDENCY_RISK_ANALYSIS.md`
- **Performance:** `STARTUP_PERFORMANCE_ANALYSIS.md`
- **Over-Engineering:** `OVER_ENGINEERING_ANALYSIS.md`
- **Streamlit Patterns:** `STREAMLIT_PATTERNS.md`

### Code Locations
- **SessionStateManager:** `src/ui/session_state.py` (311 LOC)
- **ServiceContainer:** `src/services/container.py` (817 LOC)
- **DefinitieRepository:** `src/database/definitie_repository.py` (2,100 LOC)
- **VoorbeeldenValidation:** `src/models/voorbeelden_validation.py` (184 LOC)

---

**END OF DEPENDENCY GRAPH**
