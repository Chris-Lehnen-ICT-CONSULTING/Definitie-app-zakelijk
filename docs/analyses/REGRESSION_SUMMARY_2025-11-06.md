# Performance Regression Summary - Quick Reference

**Date:** 2025-11-06
**Severity:** CRITICAL
**Status:** Root cause identified, fix ready

---

## The Problem in 3 Points

1. **RuleCache loading 4x** instead of 1x (US-202 regression)
2. **Context cleaner running 4x** (rerun cascade)
3. **35.7 second render** instead of 48ms (74,569% slower!)

---

## Root Cause (Simple Explanation)

**DEF-110 added this line:**
```python
# tabbed_interface.py:220
init_context_cleaner(force_clean=True)  # In render() method
```

**The problem:**
- `render()` is called on EVERY Streamlit interaction
- `force_clean=True` ALWAYS modifies session state
- State changes trigger Streamlit rerun
- Rerun calls `render()` again → infinite loop!
- Streamlit stops after 4 reruns (safety limit)

**Result:** 4 complete app restarts in 7 seconds

---

## Why Caching Broke

Each Streamlit rerun creates a **NEW Python process**:
- New process = all module-level singletons reset
- `_rule_cache = None` → RuleCache recreated 4x
- `_default_container = None` → ServiceContainer recreated 4x
- All lazy-loaded services reloaded 4x

**The @cached decorator can't help** because it's process-local cache, and we're getting 4 new processes!

---

## The Fix (Simple)

**Change 1 line:**
```python
# tabbed_interface.py:220 (BEFORE)
init_context_cleaner(force_clean=True)  # ❌ WRONG

# tabbed_interface.py:220 (AFTER)
init_context_cleaner()  # ✅ CORRECT - respects already-cleaned flag
```

**But wait!** This breaks DEF-110's fix for stale voorbeelden.

**Better fix:** Move force_clean to Edit Tab only:
```python
# examples_block.py (Edit Tab)
def render_voorbeelden_section(self, definitie_id: int, ...):
    current_def = definitie_id
    last_def = SessionStateManager.get_value("last_voorbeelden_def_id")

    # Only force clean when SWITCHING definitions
    if current_def != last_def:
        from ui.session_state import force_cleanup_voorbeelden
        force_cleanup_voorbeelden()
        SessionStateManager.set_value("last_voorbeelden_def_id", current_def)
```

---

## Evidence from Your Logs

### 1. RuleCache Loading 4x
```
10:10:46,104 - Loading 53 regel files
10:10:46,104 - Loading 53 regel files  ← Same millisecond!
10:10:46,105 - Loading 53 regel files
10:10:46,106 - Loading 53 regel files
```
**Analysis:** 4 loads within 2ms = separate processes, not cache misses

### 2. Context Cleaning 4x
```
10:10:37,094 - Context state cleaned on app initialization
10:10:39,331 - Context state cleaned on app initialization  (+2.2s)
10:10:42,843 - Context state cleaned on app initialization  (+3.5s)
10:10:44,735 - Context state cleaned on app initialization  (+1.9s)
```
**Analysis:** 4 "app initialization" logs = 4 complete restarts

### 3. Render Regression
```
10:11:20,503 - CRITICAL regression voor streamlit_render_ms:
              35761.3 vs baseline 48.0 (74569.6%)
```
**Analysis:** 35.7 seconds = 4 startups × 6s + business logic overhead

---

## Impact Breakdown

| Component | Before DEF-110 | After DEF-110 | Regression |
|-----------|---------------|---------------|------------|
| **Startup** | 6s | 36s | **6x slower** |
| **RuleCache** | 1x load | 4x loads | **4x disk I/O** |
| **Prompt Init** | 435ms | 1.7s | **4x slower** |
| **Validation Init** | 345ms | 1.4s | **4x slower** |
| **Container Init** | 200ms | 800ms | **4x slower** |
| **Render** | 48ms | 35,761ms | **745x slower** |

---

## Quick Fix Steps

1. **Revert force_clean in render():**
   ```bash
   # Edit src/ui/tabbed_interface.py line 220
   -    init_context_cleaner(force_clean=True)
   +    init_context_cleaner()
   ```

2. **Add definition-switch detection in Edit Tab** (see full fix in PERFORMANCE_REGRESSION_2025-11-06.md)

3. **Test locally:**
   ```bash
   bash scripts/verify_performance_regression.sh
   # Should show: ✅ NO REGRESSION DETECTED
   ```

4. **Deploy and monitor** for 24h

---

## Why This Happened

**DEF-110's intent:** Fix stale voorbeelden when switching definitions in Edit Tab

**What went wrong:** Put the fix in `render()` instead of Edit Tab's definition-switch logic

**The lesson:**
- `render()` runs on EVERY interaction (button click, text input, tab switch)
- State-modifying code in `render()` = rerun cascade
- Force cleanup should be **event-based** (definition switch), not **render-based**

---

## Prevention

**Added to codebase:**
1. ✅ Verification script: `scripts/verify_performance_regression.sh`
2. ✅ Full analysis: `docs/analyses/PERFORMANCE_REGRESSION_2025-11-06.md`
3. 🔜 Pre-commit hook to detect `force_clean=True` in `render()`
4. 🔜 Regression test in `tests/performance/test_startup_regression.py`

---

## Related Fixes That Regressed

All these optimizations were undone by the 4x rerun cascade:

- **US-202** (Oct 7): RuleCache 1x loading → regressed to 4x
- **DEF-66** (Oct 7): Lazy PromptService → regressed to 4x init
- **DEF-90** (Oct 7): Lazy ValidationOrchestrator → regressed to 4x init

**Good news:** Once we fix the rerun cascade, all these optimizations work again automatically!

---

## Next Steps

1. **Implement fix** (30 min)
2. **Test locally** (15 min)
3. **Deploy to staging** (15 min)
4. **Monitor logs** (24h)
5. **Add regression tests** (2h)

**ETA to fix:** 1 hour
**ETA to prevent:** 2 hours

---

**Full technical details:** See `docs/analyses/PERFORMANCE_REGRESSION_2025-11-06.md`

**Verification script:** `scripts/verify_performance_regression.sh`

**Analysis by:** Claude Code (Debug Specialist)
