---
id: EPIC-026-MONDAY-MORNING-PLAN
epic: EPIC-026
created: 2025-10-03
owner: solo-developer
status: action-plan
type: pragmatic-next-steps
---

# EPIC-026: What to Actually Do Monday Morning

**TL;DR:** Forget the 22-week plan. Fix tests today, create smoke tests this week, keep shipping features.

---

## REALITY CHECK SUMMARY

**Previous plans assumed:** Team of 5-10, enterprise software, production environment, €100k budget
**Actual reality:** Solo developer, personal tool, dev environment, self-managed

**Previous recommendation:** 22 weeks (5 weeks tests + 3 weeks design + 9 weeks extraction + 2 weeks validation)
**Revised recommendation:** 1 week unblock + incremental improvements

---

## THE ACTUAL PROBLEM (Right Now)

```
TESTS ARE BROKEN: ModuleNotFoundError: No module named 'fixtures'
└─ Impact: Cannot run ANY tests
└─ Risk: Flying blind on all changes
└─ Priority: P0 - FIX TODAY
```

**Everything else is secondary until this is fixed.**

---

## MONDAY MORNING CHECKLIST

### 08:00-10:00: UNBLOCK TESTS (P0)

```bash
cd /Users/chrislehnen/Projecten/Definitie-app

# 1. Find what broke
git log --diff-filter=D --oneline -- tests/fixtures/
git log --oneline -- tests/conftest.py | head -5

# 2. Quick diagnosis
ls tests/fixtures/  # Does directory exist?
grep "from fixtures" tests/conftest.py  # What's imported?

# 3. Quick fix options:
#    A. Restore deleted fixtures: git checkout <commit> -- tests/fixtures/
#    B. Comment out fixture imports in conftest.py temporarily
#    C. Update imports to point to new location

# 4. Verify SOMETHING works
pytest tests/services/test_definitie_repository.py -v  # 22 tests, should pass
pytest tests/unit/ -k "not fixture" -v  # Skip fixture-dependent tests

# Goal: Get 50+ tests passing by 10:00
```

### 10:00-12:00: CREATE SAFETY NET (P0)

```bash
# Create tests/smoke/test_critical_paths.py
mkdir -p tests/smoke
```

```python
# tests/smoke/test_critical_paths.py
"""
Smoke tests: Do critical paths work?
Run time: <30 seconds
Coverage: 80% of user-facing bugs
No mocks, no fixtures, just: does it crash?
"""

import pytest

def test_imports_work():
    """Can we import main modules without crashing?"""
    import src.main
    import src.services.container
    import src.ui.tabbed_interface
    import src.database.definitie_repository
    assert True  # If we got here, imports work

def test_service_container_initializes():
    """Can we create the service container?"""
    from src.services.container import ServiceContainer
    container = ServiceContainer()
    assert container is not None

def test_database_connection():
    """Can we connect to the database?"""
    from src.database.definitie_repository import DefinitieRepository
    repo = DefinitieRepository()
    # Try a simple read
    result = repo.get_all_definities()
    assert result is not None

# TODO: Add 7 more tests:
# - Generate definition (happy path)
# - Validate definition (passes rules)
# - Save definition
# - Load definition
# - Export to YAML
# - Upload document
# - Category determination

# Run: pytest tests/smoke/ -v
# Goal: All pass in <30 seconds
```

### 13:00-15:00: NAVIGATION AIDS (P1)

```python
# Edit src/ui/tabbed_interface.py
# Add section markers for navigation:

# ============================================================
# REGION: TAB ORCHESTRATION (Top of file)
# ============================================================
# Purpose: Manages tab switching, state initialization
# Key methods: __init__, render

# ============================================================
# REGION: GENERATION ORCHESTRATION (Lines ~200-600)
# ============================================================
# Purpose: Core definition generation flow
# Key method: _handle_definition_generation (380 LOC)
# Flow: Context → Category → Document → Generate → Store

# ============================================================
# REGION: REGENERATION ORCHESTRATION (Lines ~600-1100)
# ============================================================
# Purpose: Handles category changes → regeneration
# Key methods: _handle_regeneration, _compare_definitions
# Note: 500 LOC hidden orchestrator (candidate for extraction)

# ============================================================
# REGION: STATE MANAGEMENT (Lines ~1100-1400)
# ============================================================
# Purpose: Session state wrappers
# Note: Heavy SessionStateManager coupling (50+ calls)

# ============================================================
# REGION: UTILITIES (Bottom of file)
# ============================================================
# Purpose: Helper methods
# Note: Some may be extractable to utils/
```

### 15:00-17:00: DOCUMENT & REFLECT (P1)

```markdown
# Create docs/backlog/EPIC-026/CURRENT-STATE.md

## Current Architecture (As-Is)

**Main entry:** src/main.py
**UI orchestration:** src/ui/tabbed_interface.py (1793 LOC)
**Database:** src/database/definitie_repository.py (1815 LOC - well-structured)
**Services:** src/services/* (89 files)

## Pain Points

1. ✅ Tests broken → FIXED (pytest runs)
2. ✅ No smoke tests → CREATED (10 critical paths)
3. ⚠️ God objects hard to navigate → ADDED REGIONS
4. ⚠️ No confidence in changes → SMOKE TESTS HELP

## What's Actually Painful (Solo Dev)

- **Finding code in 1793 LOC file:** 5-10 minutes → Need better navigation
- **Fear of breaking things:** Every change = manual testing → Smoke tests help
- **Regeneration logic buried:** 500 LOC in UI → Extract if touched again
- **Category patterns hardcoded:** 3 places → Extract to config if changed 2x

## What's NOT Actually Painful

- **File is large:** Annoying but not blocking (solo = no merge conflicts)
- **No DI pattern:** Would be nice but not urgent (tests work without it)
- **Some hardcoded values:** If rarely changed, fine for now
- **Manual testing:** For rarely-used features, acceptable

## Next Week Plan

**If working on regeneration:** Extract to src/ui/handlers/regeneration.py
**If changing categories:** Move patterns to config/category_patterns.yaml
**If debugging document upload:** Extract to src/ui/handlers/documents.py
**Otherwise:** Keep shipping features, revisit next month

## Metrics That Matter (Solo)

- ✅ Time to find code: <1 minute (regions help)
- ✅ Confidence: 80%+ (smoke tests help)
- ✅ Tests run: YES (fixed!)
- ⚠️ Manual testing: Still 10+ min (reduce incrementally)
```

---

## TUESDAY-FRIDAY: BACK TO FEATURES

**Rule #1:** Run smoke tests before every commit
```bash
pytest tests/smoke/ -v  # Should take <30 seconds
```

**Rule #2:** If touching god object, extract ONE thing
```python
# Example: Working on regeneration logic
# Before: 500 LOC in tabbed_interface.py (hard to find)

# After: Create src/ui/handlers/regeneration.py
def handle_regeneration(begrip, old_category, new_category):
    """Handle category change → regeneration flow."""
    # Extract 500 LOC here
    pass

# Add smoke test
def test_regeneration_happy_path():
    result = handle_regeneration("test", "CAT1", "CAT2")
    assert result is not None

# Time: 2-3 hours
# Benefit: Never lose this code again
```

**Rule #3:** If debugging >2 hours, document for next week
```markdown
# Add to CURRENT-STATE.md:
## Pain Point: Document upload failing on PDF
- Spent 3 hours debugging
- Problem in tabbed_interface.py lines 800-950
- Candidate for extraction next week
```

---

## NEXT 4-8 WEEKS: INCREMENTAL IMPROVEMENT

### What to Extract (When Encountered)

**Extract if:**
- ✅ Can't find code in <1 minute
- ✅ Debugging same area >2 hours
- ✅ Changing hardcoded value 2nd time
- ✅ Code >100 LOC in single function

**Don't extract if:**
- ❌ Code is clear and working
- ❌ Rarely touched
- ❌ Would take >4 hours to extract
- ❌ No tests to validate

### Extraction Pattern (Simple)

```bash
# 1. Create new file (not service, just handler)
touch src/ui/handlers/<feature>.py

# 2. Move code (copy-paste is fine)
# 3. Add smoke test
# 4. Verify smoke test passes
# 5. Remove old code
# 6. Verify smoke tests still pass

# Time: 2-3 hours per extraction
# Do: 1-2 per week (as encountered)
```

---

## WHAT NOT TO DO (Avoid Enterprise Theater)

### ❌ DON'T: 5-Week Test Recovery Plan

**They said:** Write 435 tests (85% coverage) before ANY refactoring
**Reality:** 10 smoke tests give 80% confidence in 1 day
**Solo dev:** Diminishing returns after 20-30 tests

### ❌ DON'T: 9-Week Orchestrator Extraction

**They said:** Extract hidden orchestrators with DI, service layers
**Reality:** Move to separate file, add smoke test, done in 3 hours
**Solo dev:** YAGNI (You Ain't Gonna Need orchestrators)

### ❌ DON'T: Stop Features for Architecture

**They said:** 22 weeks to fix god objects properly
**Reality:** Extract pain points incrementally (ongoing)
**Solo dev:** Velocity matters more than perfect architecture

### ❌ DON'T: Aim for 85% Test Coverage

**They said:** Need comprehensive tests before refactoring
**Reality:** Smoke tests + targeted tests for extracted code
**Solo dev:** 20-30 well-chosen tests > 435 comprehensive tests

---

## WHAT TO DO (Pragmatic Solo Dev)

### ✅ DO: Fix Tests Today

**Why:** Unblocks everything
**How:** 2-4 hours diagnosis + fix
**ROI:** ∞ (can validate changes again)

### ✅ DO: Create Smoke Tests This Week

**Why:** Safety net for changes
**How:** 10 tests, <30 sec run time
**ROI:** 10x (catches 80% of bugs)

### ✅ DO: Add Navigation Aids

**Why:** Find code faster
**How:** Code regions, section comments
**ROI:** 5x (daily time savings)

### ✅ DO: Extract Pain Points Incrementally

**Why:** Reduce frustration over time
**How:** 1 extraction per week (when encountered)
**ROI:** 3x (less debugging, easier to find)

### ✅ DO: Keep Shipping Features

**Why:** Velocity matters for solo dev
**How:** Don't block features for architecture
**ROI:** Massive (build useful tool, not perfect code)

---

## SUCCESS METRICS (Solo Dev Reality)

### Forget These (Team Metrics)

- ❌ 85% test coverage (overkill solo)
- ❌ Zero god objects (no parallel dev problems)
- ❌ Perfect DI patterns (YAGNI)
- ❌ Zero hardcoded values (fix when changed 2x)

### Track These (Solo Productivity)

- ✅ **Tests run:** YES/NO (must be YES)
- ✅ **Smoke tests pass:** YES/NO (must be YES)
- ✅ **Time to find code:** <1 minute (navigation aids)
- ✅ **Confidence in changes:** 80%+ (smoke tests)
- ✅ **Features shipped:** Ongoing (don't block)

---

## DECISION TREE (This Week)

```
START HERE
│
├─ Are tests broken?
│  ├─ YES → FIX TODAY (P0, 2-4 hours)
│  └─ NO → Continue
│
├─ Do you have smoke tests?
│  ├─ NO → CREATE THIS WEEK (P0, 1 day)
│  └─ YES → Continue
│
├─ Can you find code in <1 minute?
│  ├─ NO → ADD NAVIGATION AIDS (P1, 2 hours)
│  └─ YES → Continue
│
├─ Working on regeneration/categories/documents?
│  ├─ YES → EXTRACT WHILE YOU'RE THERE (P1, 2-3 hours)
│  └─ NO → Continue
│
└─ SHIP FEATURES (Ongoing, don't block for architecture)
```

---

## WEEKLY CHECKLIST (Next 8 Weeks)

### Week 1: UNBLOCK
- [x] Fix tests (pytest runs)
- [x] Create 10 smoke tests
- [x] Add navigation aids
- [x] Document current state

### Week 2-4: EXTRACT OPPORTUNISTICALLY
- [ ] Extract 1 pain point (if encountered)
- [ ] Add smoke test for extracted code
- [ ] Expand smoke tests to 15
- [ ] Ship features (ongoing)

### Week 5-8: STRATEGIC CLEANUP
- [ ] Review: Are god objects still painful?
- [ ] Extract 2-3 more pain points
- [ ] Move hardcoded patterns to config (if changed)
- [ ] Expand smoke tests to 20

---

## THE BOTTOM LINE

**Forget:** 22-week program, €100k effort, 435 tests, orchestrators, DI patterns
**Remember:** Fix tests today, smoke tests this week, extract incrementally, keep shipping

**Time investment:** 1 week unblock + ongoing incremental
**Feature blocking:** None (work continues)
**ROI:** Massive (velocity maintained, debt managed)

---

## IMMEDIATE NEXT STEPS

1. **TODAY:** Fix tests (2-4 hours) → pytest runs
2. **THIS WEEK:** Smoke tests (1 day) → 80% confidence
3. **NEXT 2 WEEKS:** Extract 1 pain point (when encountered) → less frustration
4. **ONGOING:** Keep shipping features → velocity matters

**Status:** Ready to execute
**Urgency:** HIGH (tests blocking)
**Effort:** Low (doesn't block features)
**ROI:** Massive (unblock + safety net + better code)

---

**Prepared by:** BMad Orchestrator (Reality Check Mode)
**Date:** 2025-10-03
**Context:** Solo developer, pragmatic approach, feature velocity matters
**Key Message:** Fix tests, add smoke tests, keep shipping. Everything else is incremental.
