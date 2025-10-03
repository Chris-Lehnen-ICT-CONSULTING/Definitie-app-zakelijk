---
id: EPIC-026-APPROACH-COMPARISON
epic: EPIC-026
created: 2025-10-03
owner: bmad-orchestrator
status: comparison
type: decision-support
---

# EPIC-026: Approach Comparison Matrix

**TL;DR:** Enterprise plans assumed team/production. Solo dev reality needs pragmatic incremental approach.

---

## COMPARISON TABLE

| Aspect | Original (v1.0) | Revised (v2.0) | Technical Analysis | Single Dev Reality ✅ |
|--------|-----------------|----------------|--------------------|-----------------------|
| **Timeline** | 11-16 days | 22 weeks | 4-5 weeks | **1 week + incremental** |
| **Cost** | €12.8k | €92k-€121k | €43-67k | **Minimal (no features blocked)** |
| **Test Phase** | None | 5 weeks (Phase 0) | 7 days (Week 1) | **1 day (smoke tests)** |
| **Test Count** | 73 baseline | 435 tests (85% coverage) | 15-20 integration | **10 smoke tests** |
| **Design Phase** | 3-5 days | 3 weeks | 7 days | **2 hours (navigation aids)** |
| **Extraction** | 7-10 days | 9 weeks | 4 weeks | **Incremental (ongoing)** |
| **New Services** | Unknown | 7 services | 2 services | **0 (just move to files)** |
| **Architecture Layers** | Unknown | 4 layers | 3 layers | **Keep current (3 layers)** |
| **Features Blocked** | 11-16 days | 22 weeks | 4-5 weeks | **None** |
| **God Objects Split** | 3 files | 2 files (repository deferred) | 2 files | **Extract pain points only** |
| **DI Pattern** | Assumed | Full implementation | Enhanced existing | **Not needed (YAGNI)** |
| **Orchestrators** | Unknown | 2 new orchestrators | Use existing | **None (just handlers)** |
| **Hardcoded Patterns** | Unknown | Still hardcoded | Move to config | **Fix when changed 2x** |
| **Context** | Team assumed | Team assumed | Team assumed | **SOLO DEVELOPER** ✅ |

---

## DETAILED COMPARISON

### 1. TIMELINE & EFFORT

#### Original (v1.0) - NAIVE
```
Timeline: 11-16 days
Context: Assumed simple file splitting
Problem: Underestimated complexity
Outcome: REJECTED (too naive)
```

#### Revised (v2.0) - ENTERPRISE
```
Timeline: 22 weeks
  Phase 0: 5 weeks (test recovery - 435 tests)
  Phase 1: 3 weeks (design)
  Phase 2: 9 weeks (extraction)
  Phase 3: 2 weeks (validation)
  Phase 4: 3 weeks (documentation)

Context: Multi-developer team, production environment
Problem: Enterprise theater for solo dev
Outcome: OVERKILL (5.5 months no features)
```

#### Technical Analysis - PRAGMATIC
```
Timeline: 4-5 weeks
  Week 1: Foundation (7 days, not 5)
  Week 2: Business logic (5 days)
  Week 3: UI splitting (5 days)
  Week 4: Orchestration (5 days)
  Week 5: Cleanup (3 days)

Context: Still assumed team
Problem: Still too long for solo
Outcome: BETTER but still overkill
```

#### Single Dev Reality ✅ - HONEST
```
Timeline: 1 week + incremental
  Week 1: Unblock (5 days)
    - Fix tests: 4 hours
    - Smoke tests: 1 day
    - Navigation aids: 2 hours
    - Documentation: 1 hour
  Ongoing: Extract pain points (2-3 hours each, when encountered)

Context: SOLO developer, personal tool, dev environment
Problem: None (right-sized for reality)
Outcome: APPROVED (balanced)
```

---

### 2. TEST STRATEGY

#### Original (v1.0)
- Baseline: 73 tests (maintain)
- New tests: Unknown
- Coverage: Not specified
- **Problem:** No test strategy

#### Revised (v2.0) - COMPREHENSIVE
- Phase 0: 5 weeks dedicated to tests
- New tests: 435 tests (85% coverage target)
- Test types: Unit (40%), Integration (60%)
- Infrastructure: Streamlit test harness, pytest-playwright
- **Problem:** Overkill for solo dev (5 weeks before ANY refactoring)

#### Technical Analysis - TARGETED
- Week 1: 15-20 integration tests
- Coverage: 70-75% on god objects
- Test types: Integration-focused
- **Problem:** Still requires 7 days upfront

#### Single Dev Reality ✅ - PRAGMATIC
- Day 1: Fix broken tests (pytest runs)
- Day 2: 10 smoke tests (<30 sec, 80% confidence)
- Ongoing: Add tests for extracted code (1-2 per extraction)
- Coverage: 80% of critical paths (not 85% of all code)
- **Benefit:** Unblocked in 1 day, not 5 weeks

---

### 3. ARCHITECTURE APPROACH

#### Original (v1.0)
- Approach: Naive file splitting
- Services: Unknown
- Layers: Unknown
- **Problem:** Would create more problems than it solves

#### Revised (v2.0) - ORCHESTRATOR-FIRST
- Approach: Extract hidden orchestrators, create service layers
- Services: 7 new services (89 → 96 total)
- Layers: 4 (UI → Orchestration → Service → Data)
- Orchestrators: `DefinitionGenerationOrchestrator`, `RegenerationOrchestrator`
- Pattern: Full DI, interface-based abstractions
- **Problem:** Over-engineering, orchestrator proliferation

#### Technical Analysis - PRAGMATIC
- Approach: Enhance existing services, not create new
- Services: 2 new (89 → 91 total)
- Layers: 3 (UI → Service → Data)
- Orchestrators: Use existing `DefinitionOrchestratorV2`
- Pattern: Minimal new abstractions
- **Problem:** Still creates services when files would suffice

#### Single Dev Reality ✅ - MINIMAL
- Approach: Move code to separate files (not services)
- Services: 0 new (keep 89, good enough)
- Layers: 3 (keep current)
- Orchestrators: 0 new (just extract to handlers)
- Pattern: No DI needed (YAGNI for solo)
- **Benefit:** Same outcome, 80% less abstraction

---

### 4. SCOPE DIFFERENCES

#### God Objects to Refactor

| File | v1.0 | v2.0 | Technical | Solo Dev ✅ |
|------|------|------|-----------|-------------|
| `definition_generator_tab.py` (2525 LOC) | Split | Extract UI/Logic/Renderer | Split into 3 components | **Extract pain points only** |
| `tabbed_interface.py` (1793 LOC) | Split | Extract orchestrators | Extract god method (380 LOC) | **Add navigation aids first** |
| `definitie_repository.py` (1815 LOC) | Split | Defer (false positive) | Defer (well-structured) | **Leave alone (it's fine)** ✅ |

**Key Difference:** Solo dev doesn't need perfect architecture, just navigable code.

---

### 5. COST-BENEFIT ANALYSIS

#### Revised (v2.0) - Enterprise Approach

**Investment:**
- 5 weeks test recovery
- 3 weeks design
- 9 weeks extraction
- 2 weeks validation
- **Total: 19 weeks = 4.75 months**

**Cost (solo dev context):**
- 4.75 months no features
- Opportunity cost: High
- Complexity: Orchestrators, DI, service layers

**Benefit (solo dev context):**
- Perfect architecture
- 85% test coverage
- Zero god objects

**ROI:** **NEGATIVE** (solo dev doesn't need team-oriented architecture)

#### Single Dev Reality ✅ - Pragmatic Approach

**Investment:**
- 4 hours fix tests
- 1 day smoke tests
- 2 hours navigation aids
- Ongoing: 2-3 hours per extraction (when needed)
- **Total: 2 days upfront + incremental**

**Cost:**
- 2 days initial investment
- No feature blocking
- Minimal complexity added

**Benefit:**
- Tests run (unblocked)
- 80% confidence (smoke tests)
- Code navigable (aids)
- Incremental improvement

**ROI:** **MASSIVE POSITIVE** (unblocked immediately, features continue)

---

## QUANTITATIVE COMPARISON

### Timeline Comparison

```
┌────────────────────────────────────────────────────────────┐
│                      TIMELINE COMPARISON                    │
│                                                             │
│  v1.0 (Naive):        ████ 11-16 days                      │
│                                                             │
│  v2.0 (Enterprise):   ████████████████████████             │
│                       22 weeks (110 days)                  │
│                                                             │
│  Technical:           ██████████ 4-5 weeks (25 days)      │
│                                                             │
│  Solo Dev ✅:         █ 1 week + incremental (5 days +)   │
│                                                             │
└────────────────────────────────────────────────────────────┘

Savings: 105 days (21 weeks) → feature development instead
```

### Test Investment Comparison

```
┌────────────────────────────────────────────────────────────┐
│                   TEST INVESTMENT COMPARISON                │
│                                                             │
│  v2.0 (Enterprise):   ████████████ 435 tests, 25 days     │
│                                                             │
│  Technical:           ████ 15-20 tests, 7 days             │
│                                                             │
│  Solo Dev ✅:         █ 10 smoke tests, 1 day              │
│                                                             │
└────────────────────────────────────────────────────────────┘

Efficiency: 80% confidence in 4% of time (1 day vs 25 days)
```

### Architecture Complexity Comparison

```
┌────────────────────────────────────────────────────────────┐
│              ARCHITECTURE COMPLEXITY COMPARISON             │
│                                                             │
│  v2.0 (Enterprise):                                         │
│    Layers: 4 (UI → Orchestration → Service → Data)        │
│    Services: 96 (+7 new)                                   │
│    Patterns: Orchestrators, DI, Interfaces                 │
│    Abstraction: HIGH                                       │
│                                                             │
│  Technical:                                                 │
│    Layers: 3 (UI → Service → Data)                        │
│    Services: 91 (+2 new)                                   │
│    Patterns: Enhanced existing                             │
│    Abstraction: MEDIUM                                     │
│                                                             │
│  Solo Dev ✅:                                               │
│    Layers: 3 (keep current)                                │
│    Services: 89 (no new services)                          │
│    Patterns: Simple file extraction                        │
│    Abstraction: LOW                                        │
│                                                             │
└────────────────────────────────────────────────────────────┘

Solo Dev wins: Same navigability, 80% less abstraction
```

---

## RISK COMPARISON

### v2.0 (Enterprise) Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| 5 weeks tests too long | HIGH | Features stalled | **Accept or reduce scope** |
| Timeline overrun (22→26 weeks) | MEDIUM | Delays compound | 2-week buffer added |
| Over-engineering | HIGH | Maintenance burden | Architecture review gates |
| Breaking changes | MEDIUM | Application broken | Comprehensive tests first |
| Orchestrator proliferation | HIGH | Abstraction debt | **Unavoidable with approach** |

**Overall Risk:** MEDIUM-HIGH (long timeline, over-engineering likely)

### Solo Dev ✅ Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Smoke tests miss bugs | MEDIUM | Some regressions | Add tests incrementally |
| Incremental extraction incomplete | LOW | Some god objects remain | **Acceptable (solo dev)** |
| Navigation aids insufficient | LOW | Still hard to find code | Extract when painful |
| Tests stay broken | LOW | Blocking development | Fix immediately (P0) |

**Overall Risk:** LOW (minimal changes, incremental, features continue)

---

## CONTEXT MATTERS

### Why v2.0 Makes Sense for Teams

✅ **Production environment:** 85% coverage prevents customer incidents
✅ **Multi-developer:** DI/interfaces enable parallel development
✅ **Stakeholder gates:** Architecture reviews ensure quality
✅ **Bus factor:** Service layers enable knowledge transfer
✅ **Scale:** God objects block team velocity

### Why Solo Dev Approach Makes Sense

✅ **Dev environment:** Can fix bugs immediately, no customers affected
✅ **Single developer:** No parallel development, no merge conflicts
✅ **Self-managed:** No approval gates needed
✅ **Personal tool:** Velocity matters more than perfect architecture
✅ **Pragmatic:** Good enough > perfect architecture never shipped

---

## DECISION MATRIX

| Criterion | v1.0 (Naive) | v2.0 (Enterprise) | Technical | Solo Dev ✅ |
|-----------|--------------|-------------------|-----------|-------------|
| **Timeline** | 11-16 days | 22 weeks | 4-5 weeks | **1 week + incremental** ✅ |
| **Features Blocked** | 11-16 days | 22 weeks | 4-5 weeks | **None** ✅ |
| **Test Investment** | None | 5 weeks | 1 week | **1 day** ✅ |
| **Architecture Quality** | Poor | Excellent | Good | **Good enough** ✅ |
| **Complexity Added** | Unknown | High | Medium | **Low** ✅ |
| **Solo Dev ROI** | Negative | **Very Negative** | Negative | **POSITIVE** ✅ |
| **Team ROI** | Negative | Positive | Positive | N/A |
| **Pragmatism** | Low | Low | Medium | **HIGH** ✅ |
| **Realistic?** | No | No (wrong context) | Maybe | **YES** ✅ |

**Winner for Solo Dev:** Single Dev Reality approach (8/9 criteria)

---

## RECOMMENDATIONS BY CONTEXT

### If You Are a Team (5-10 developers)

**Choose:** v2.0 (Enterprise) or Technical Analysis
**Why:** Need service layers, DI, comprehensive tests for parallel development
**Accept:** 4-22 weeks investment for sustainable team velocity

### If You Are Solo Dev (You) ✅

**Choose:** Single Dev Reality approach
**Why:** Velocity matters, incremental improvement, no features blocked
**Accept:** Some god objects remain (not a problem solo)

---

## THE VERDICT

### ❌ REJECT: v1.0 (Naive)
- Too naive (underestimated complexity)
- Would create more problems than it solves

### ❌ REJECT: v2.0 (Enterprise)
- Wrong context (team vs solo)
- Too long (22 weeks = 5.5 months no features)
- Over-engineering (orchestrators, DI overkill for solo)
- **ROI:** Negative for solo dev

### ⚠️ REJECT: Technical Analysis
- Better than v2.0 but still assumes team
- Still too long (4-5 weeks)
- Still creates unnecessary services
- **ROI:** Slightly negative for solo dev

### ✅ APPROVE: Single Dev Reality
- Right context (solo dev, personal tool)
- Right timeline (1 week + incremental)
- Right scope (unblock + pragmatic improvements)
- **ROI:** Massively positive

---

## IMMEDIATE NEXT STEPS

Based on Single Dev Reality approach:

1. **TODAY:** Fix tests (4 hours) → pytest runs
2. **THIS WEEK:** Create smoke tests (1 day) → 80% confidence
3. **NEXT WEEK:** Add navigation aids (2 hours) → find code faster
4. **ONGOING:** Extract pain points (when encountered) → incremental improvement

**Status:** Ready to execute
**Urgency:** HIGH (tests blocking)
**ROI:** MASSIVE (unblock + features continue)

---

**Prepared by:** BMad Orchestrator
**Date:** 2025-10-03
**Conclusion:** Solo dev needs pragmatic approach, not enterprise architecture programs
**Bottom Line:** Fix tests today, smoke tests this week, extract incrementally, keep shipping features
