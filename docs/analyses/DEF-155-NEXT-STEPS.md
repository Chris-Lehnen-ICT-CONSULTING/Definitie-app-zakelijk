# DEF-155: Next Steps & Action Items

**Date:** 2025-11-14
**Status:** Phase 1 Complete ✅ | Blockers Identified ⚠️

---

## QUICK STATUS

✅ **GOOD NEWS:** All 3 DEF-155 fixes are working correctly!
- Dependency declaration added
- Shared state bypasses eliminated
- Documentation math corrected

⚠️ **BLOCKERS:** Two issues preventing Phase 2:
1. 🔴 CachedToetsregelManager initializing 4x per request (should be 1x)
2. 🟡 Token count mystery: 3816 vs ~2500 baseline (need verification)

---

## IMMEDIATE ACTIONS (Week 1)

### Action 1: Establish Baseline ✅ URGENT

**Why:** Cannot verify 120-token reduction without knowing starting point

**How:**
```bash
# 1. Find commit before DEF-155
git log --oneline | grep -B5 "7f86ca73"

# 2. Checkout previous commit
git checkout <commit-before-7f86ca73>

# 3. Generate test prompt and measure tokens
python3 << 'EOF'
import sys
sys.path.insert(0, 'src')
from services.prompts.prompt_service_v2 import PromptServiceV2
# ... generate prompt for "toxisch" ...
# ... count tokens with tiktoken ...
EOF

# 4. Compare: BEFORE vs AFTER (7f86ca73)
echo "Baseline: X tokens"
echo "Current:  3816 tokens"
echo "Delta:    Y tokens"
```

**Expected Outcome:**
- If baseline was ~3936 tokens → ✅ Reduction achieved (-120)
- If baseline was ~2500 tokens → ❌ Something wrong

**Time:** 30 minutes

---

### Action 2: Debug CachedToetsregelManager 4x Issue 🔴 CRITICAL

**Why:** 4x initialization indicates singleton pattern broken in production

**Diagnosis Steps:**

**Step 1: Add Stack Trace Logging**
```python
# src/toetsregels/cached_manager.py line 163
import traceback

def get_cached_toetsregel_manager() -> CachedToetsregelManager:
    global _manager
    if _manager is None:
        stack = ''.join(traceback.format_stack())
        logger.warning(f"NEW CachedToetsregelManager instance - Stack:\n{stack}")
        _manager = CachedToetsregelManager()
    return _manager
```

**Step 2: Run Test Generation**
```bash
# Start app, generate definition for "toxisch"
streamlit run src/main.py

# Check logs/test_output.log for stack traces
grep -A 20 "NEW CachedToetsregelManager" logs/test_output.log
```

**Step 3: Analyze Call Patterns**
Look for:
- 🔍 Multiple import paths (circular imports?)
- 🔍 Streamlit rerun resetting global state
- 🔍 Parallel module execution race condition
- 🔍 ServiceContainer creating duplicate instances

**Likely Culprits:**

1. **HYPOTHESIS A: Streamlit Session Reset**
   ```python
   # Each st.rerun() might reimport modules → _manager = None
   # FIX: Move to st.cache_resource
   ```

2. **HYPOTHESIS B: Parallel Execution Race**
   ```python
   # 7 rule modules call get_cached_toetsregel_manager() in parallel
   # Race condition: Thread 1 sees _manager=None, Thread 2 also sees None
   # FIX: Add threading.Lock (already present in orchestrator!)
   ```

3. **HYPOTHESIS C: Import Side Effects**
   ```python
   # Multiple import paths: toetsregels.cached_manager vs src.toetsregels.cached_manager
   # FIX: Consolidate to single canonical import
   ```

**Expected Outcome:** Identify exact caller causing re-initialization

**Time:** 1-2 hours

---

### Action 3: Analyze Prompt Section Weights ✅ INFORMATIVE

**Why:** Understand where 3816 tokens are distributed

**How:**
```python
# Generate prompt and save to file
with open('generated_prompt.txt', 'w') as f:
    f.write(prompt)

# Manual section analysis
import tiktoken
encoding = tiktoken.get_encoding('cl100k_base')

sections = {
    'Expertise': extract_section('### 🎓 ROL:', prompt),
    'Output Spec': extract_section('### 📐 OUTPUT SPECIFICATIE:', prompt),
    'Context': extract_section('### 🌍 CONTEXT AWARENESS:', prompt),
    'ARAI Rules': extract_section('### ✅ Algemene Regels AI:', prompt),
    # ... etc for all 16 modules
}

for name, text in sections.items():
    tokens = len(encoding.encode(text))
    print(f"{name}: {tokens} tokens ({tokens/3816*100:.1f}%)")
```

**Expected Outcome:**
```
Expertise: 150 tokens (3.9%)
Output Spec: 200 tokens (5.2%)
Context: 400 tokens (10.5%)  ← Likely duplication target
ARAI Rules: 800 tokens (21.0%)  ← Check if verbose
...
```

**Time:** 1 hour

---

## DECISION POINT (End of Week 1)

After completing Actions 1-3, assess:

### ✅ PROCEED TO PHASE 2 IF:
- Baseline confirms 120-token reduction achieved
- CachedToetsregelManager 4x issue resolved (or understood)
- Section analysis shows >300 tokens of context duplication

### ⚠️ PAUSE AND DEBUG IF:
- No token reduction from baseline (Phase 1 didn't work?)
- 4x issue causes race conditions or errors
- Section analysis shows no significant duplication

### ❌ ABORT PHASE 2 IF:
- Token count actually increased from baseline
- Architectural issues discovered in Phase 1 code
- Performance regressions detected

---

## PHASE 2 READINESS CHECKLIST

Before starting context consolidation:

- [ ] ✅ Baseline established (know starting point)
- [ ] 🔴 CachedToetsregelManager 4x resolved
- [ ] ✅ Section weights analyzed (know targets)
- [ ] ✅ Duplication >300 tokens confirmed
- [ ] ✅ No performance regressions from Phase 1
- [ ] ✅ All tests passing

**Current Score: 2/6** ⚠️ NOT READY YET

---

## QUICK COMMANDS

### Measure Current Token Count
```bash
python3 << 'EOF'
import sys, tiktoken
sys.path.insert(0, 'src')

# Generate prompt (pseudo-code)
# prompt = generate_prompt_for("toxisch")

encoding = tiktoken.get_encoding('cl100k_base')
tokens = encoding.encode(prompt)
print(f"Tokens: {len(tokens)}")
EOF
```

### Check Singleton Behavior
```bash
python3 -c "
from src.toetsregels.cached_manager import get_cached_toetsregel_manager
m1 = get_cached_toetsregel_manager()
m2 = get_cached_toetsregel_manager()
print('Singleton:', m1 is m2)
"
```

### Verify Fixes Still In Place
```bash
# Check dependency
grep "context_awareness" src/services/prompts/modules/definition_task_module.py

# Check no bypasses
grep "base_context.get" src/services/prompts/modules/*.py
# Should return: no results
```

---

## RISK ASSESSMENT

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| 4x issue is Streamlit bug | MEDIUM | HIGH | Use st.cache_resource instead of global |
| Baseline was never 2500 | HIGH | LOW | Update documentation, adjust expectations |
| Phase 2 breaks existing code | LOW | MEDIUM | Thorough testing, feature flag |
| Token reduction not measurable | LOW | LOW | Section-by-section analysis |

---

## SUCCESS METRICS

Track these after each action:

1. **CachedToetsregelManager Initializations**
   - Current: 2x-4x per request
   - Target: 1x per request
   - Measure: Count log messages

2. **Token Count**
   - Current: 3816 tokens
   - Target: ~3696 tokens (-120 from baseline)
   - Measure: tiktoken encoding

3. **Build Time**
   - Current: 1.8-2.83ms (excellent!)
   - Target: <5ms
   - Measure: prompt_orchestrator logs

4. **Code Quality**
   - Architectural violations: 0 ✅
   - Test coverage: TBD
   - Dependency correctness: 100% ✅

---

## CONTACT / ESCALATION

If blockers cannot be resolved in Week 1:

1. **CachedToetsregelManager 4x:**
   - Escalate to: ServiceContainer maintainer
   - Fallback: Revert to non-cached manager (accept perf hit)

2. **Token count mystery:**
   - Escalate to: Prompt architect
   - Fallback: Accept current count, document accurately

3. **Phase 2 timing:**
   - Can be deferred if blockers persist
   - Phase 1 already delivered architectural value

---

**Last Updated:** 2025-11-14
**Next Review:** 2025-11-21 (after Week 1 actions complete)
