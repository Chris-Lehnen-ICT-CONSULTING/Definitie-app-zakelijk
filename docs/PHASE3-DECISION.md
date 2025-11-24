# PHASE 3 DECISION MATRIX

**Status: READY FOR EXECUTION**
**Recommendation: Option A (Maximum Value)**
**Effort: 32-34 min | Value: 70 errors (41% reduction) | Risk: SAFE**

---

## EXECUTIVE SUMMARY

| Metric | Value |
|--------|-------|
| **Errors Remaining** | 170 |
| **Phase 3 Target** | 70 errors |
| **Errors After Phase 3** | ~100 |
| **Total Reduction (Phases 1-3)** | 59% |
| **Time Budget** | 40 min |
| **Estimated Duration** | 32 min |
| **Risk Level** | SAFE |
| **Validation Method** | Existing tests |

---

## PARETO FOCUS (80/20)

**Top 7 categories = 83.6% of all errors**
```
UP035  ████████████████████░ 38  (22.4%)
RUF002 ██████████████░░░░░░░ 28  (16.5%)
RUF003 ██████████████░░░░░░░ 28  (16.5%)
I001   ████████████░░░░░░░░░ 24  (14.1%)
B007   ████░░░░░░░░░░░░░░░░░  8  (4.7%)
PT017  ████░░░░░░░░░░░░░░░░░  8  (4.7%)
SIM117 ████░░░░░░░░░░░░░░░░░  8  (4.7%)
```

---

## PHASE 3 OPTION A (RECOMMENDED) ✅

### 1. I001: Unsorted Imports (24 errors, 5 min)
```bash
ruff --fix I001 src config
```
- **Risk:** SAFE (100% deterministic)
- **Effort:** 5 min (pure automation)
- **Validation:** Run tests

### 2. UP035: Deprecated typing imports (38 errors, 15 min)
```bash
ruff --fix UP035 src config
# Manual review (5 min): Check for edge cases
```
- **Risk:** LOW (Python 3.11+ standard, backward compatible)
- **Effort:** 15 min (10 auto + 5 review)
- **Changes:** `typing.Dict` → `dict`, `List` → `list`, etc.
- **Validation:** Run tests, spot-check files

### 3. B007: Unused loop variables (8 errors, 12 min)
```bash
ruff check --select B007 src config
# For each match, rename unused var to `_`
```
- **Risk:** LOW (code clarity, follows PEP 8)
- **Effort:** 12 min (8 targeted edits, ~1.5 min each)
- **Pattern:** `for i in range(10):` → `for _ in range(10):`
- **Validation:** Run linter, spot-check logic

---

## SUMMARY TABLE: All Options

| Option | Errors Fixed | Time | Risk | Status |
|--------|-------------|------|------|--------|
| **A (Recommended)** | 70 | 32 min | SAFE | ✅ GO |
| B (Conservative) | 62 | 20 min | SAFE | ⚠️ Fewer errors |
| C (Extended) | 81 | 42 min | LOW | ⚠️ Slightly over budget |
| D (Skip) | 0 | 0 min | — | ❌ Low ROI |

---

## SKIP IN PHASE 3

| Category | Reason |
|----------|--------|
| **RUF002/003** (56 errors) | Cosmetic docstring cleanup, no automation, low value |
| **PT017** (8 errors) | Test refactoring, MEDIUM risk, needs review |
| **F821** (5 errors) | Complex cases deferred from Phase 2, HIGH risk |

---

## EXECUTION STEPS

```bash
# 1. Run I001 fix (5 min)
cd /Users/chrislehnen/Projecten/Definitie-app
ruff --fix I001 src config

# 2. Run UP035 fix (15 min)
ruff --fix UP035 src config
# Review: Check src/ for any issues (manual, 5 min)

# 3. Fix B007 (12 min)
ruff check --select B007 src config
# For each match: Rename unused variable to _ (8 edits)

# 4. Validate (2 min)
pytest -q
ruff check src config
```

**Total: 34 minutes**

---

## SUCCESS CRITERIA

- [ ] I001: 0 errors
- [ ] UP035: 0 errors
- [ ] B007: 0 errors
- [ ] All tests pass
- [ ] Ruff check shows 100 errors remaining

---

## NEXT STEPS

**After Phase 3:** Remaining ~100 errors in lower-priority categories (RUF002/003, PT017, F821, others)
- **Phase 4:** Can batch-fix RUF002/003 docstring cleanup (56 errors, 30 min)
- **Phase 5:** Address F821 with focused review (5 errors, 25 min)

---

**→ Ready to execute Phase 3?**
See full analysis: `docs/phase3-ultrathink-analysis.md`
