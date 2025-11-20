# IMPLEMENTEER Prompt Fixes - Copy-Paste Prompt

**Version:** 1.0
**Purpose:** Direct copy-paste prompt voor Claude Code om fixes te implementeren
**Input:** JSON output van `bounded-prompt-analysis.md`

---

## 📋 Copy-Paste Prompt voor Claude Code

```markdown
# Implementeer Prompt Fixes - ReAct Pattern

**Time Budget:** 3 fixes in 2 hours MAX
**Pattern:** REASON → ACT → OBSERVE → DECIDE
**Input:** `/Users/chrislehnen/Downloads/prompt-analysis-output.json`

---

## ⚠️ RULES

**MUST DO:**
- ✅ Use TodoWrite to track progress
- ✅ Implement fixes ONE AT A TIME
- ✅ Validate after EACH fix (run tests)
- ✅ Revert immediately if tests fail
- ✅ Stop after 3 fixes or 2 hours

**NEVER DO:**
- ❌ Implement multiple fixes at once
- ❌ Continue if tests fail 2x
- ❌ Skip validation
- ❌ Analyze more issues (that was previous phase)
- ❌ Create new analysis documents

---

## 📋 PHASE 1: Load Analysis (5 min)

**Read analysis output:**
```bash
Read: /Users/chrislehnen/Downloads/prompt-analysis-output.json
```

**Extract TOP 3:**
```json
{
  "top_3_implementation": [
    {"rank": 1, "module": "...", "action": "..."},
    {"rank": 2, "module": "...", "action": "..."},
    {"rank": 3, "module": "...", "action": "..."}
  ]
}
```

**Create TodoWrite list:**
```
[ ] Fix 1: [description from JSON]
[ ] Fix 2: [description from JSON]
[ ] Fix 3: [description from JSON]
[ ] Generate 3 test definitions
[ ] Measure token reduction
```

**STOP - Show todo list, wait for approval**

---

## 📋 PHASE 2: Implement Each Fix (ReAct Loop)

**For EACH todo item (max 3):**

### REASON (5 min)

**Read the fix spec from JSON:**
- Module: `top_3_implementation[0].module`
- Action: `top_3_implementation[0].action`
- Location: `top_3_implementation[0].location`
- Before/After: `top_3_implementation[0].before/after`

**Verify understanding:**
- What file needs to change?
- What lines need to change?
- What is the exact change?

### ACT (15 min)

**Make the change:**

```python
# Read module file
Read: {module file path}

# Edit the file
Edit:
  file_path: {module}
  old_string: {before}
  new_string: {after}
```

**Run tests:**
```bash
pytest tests/services/prompts/ -v
```

**Generate 1 test definition:**
```bash
# Generate prompt with fix applied
# Save to /Users/chrislehnen/Downloads/test-definition-{fix-number}.txt
```

### OBSERVE (10 min)

**Check results:**
- ✅ Did tests pass? (Y/N)
- ✅ Does test definition look better? (Compare quality)
- ✅ Estimate token change (compare prompt length)

**Measure:**
```json
{
  "fix_results": {
    "tests_passing": true/false,
    "test_definition_quality": "better/same/worse",
    "token_change_est": -200
  }
}
```

### DECIDE (2 min)

**Decision tree:**

```
Tests passing?
├─ NO → REVERT change immediately
│       Mark todo as FAILED
│       Escalate to user
│       STOP (don't continue to next fix)
│
└─ YES → Token reduction > 0?
         ├─ NO → REVERT (regression)
         │       Escalate to user
         │       STOP
         │
         └─ YES → Mark todo as COMPLETED
                  Move to next fix
```

**Autonomy rules:**
- Confidence >80% → Continue to next fix
- Confidence 50-80% → Show results, ask approval
- Confidence <50% → Escalate immediately

---

## 📋 PHASE 3: Final Validation (15 min)

**After completing all 3 fixes:**

1. **Generate 3 test definitions**
   - Save each to `/Users/chrislehnen/Downloads/test-definition-final-{1,2,3}.txt`

2. **Measure total impact:**
   ```bash
   # Count tokens in latest prompt vs baseline
   wc -c /Users/chrislehnen/Downloads/_Definitie_Generatie_prompt-23.txt
   wc -c /Users/chrislehnen/Downloads/test-definition-final-1.txt
   ```

3. **Calculate results:**
   ```json
   {
     "final_results": {
       "fixes_completed": 3,
       "fixes_failed": 0,
       "tests_passing": "13/13",
       "baseline_tokens": 7250,
       "final_tokens": 5800,
       "token_reduction": 1450,
       "reduction_percentage": 20
     }
   }
   ```

4. **Update Linear issues:**
   ```bash
   # For each completed fix:
   # - Add comment with results
   # - Update status if applicable
   ```

---

## 📊 COMPLETION REPORT

**Output this JSON:**

```json
{
  "implementation_summary": {
    "timestamp": "2025-01-20T15:30:00Z",
    "duration_min": 95,
    "fixes_attempted": 3,
    "fixes_completed": 3,
    "fixes_failed": 0
  },
  "fix_details": [
    {
      "rank": 1,
      "module": "...",
      "action": "...",
      "status": "completed",
      "token_impact": -1000,
      "time_spent_min": 25,
      "tests_passing": true
    }
  ],
  "validation_results": {
    "baseline_tokens": 7250,
    "final_tokens": 5800,
    "token_reduction": 1450,
    "reduction_percentage": 20,
    "test_definitions_generated": 3,
    "test_quality": "improved",
    "all_tests_passing": true
  },
  "linear_updates": [
    {"issue": "DEF-169", "status": "updated", "comment": "..."}
  ],
  "status": "completed",
  "ready_for_review": true
}
```

---

## ⚡ DECISION MATRIX

| Situation | Action |
|-----------|--------|
| Tests pass + token reduction | ✅ Continue to next fix |
| Tests pass + no token change | ⚠️ Show results, ask user |
| Tests fail once | ⚠️ Retry fix |
| Tests fail twice | 🛑 REVERT + STOP |
| Token count increased | 🛑 REVERT + STOP |
| Fix 1 completed | ✅ Move to fix 2 |
| Fix 2 completed | ✅ Move to fix 3 |
| Fix 3 completed | ✅ Generate report + STOP |
| 2 hours elapsed | 🛑 STOP, report progress |

---

## 🚫 IMPLEMENTATION ANTI-PATTERNS

**STOP if you catch yourself:**
- ❌ "Let me analyze why this failed..." → REVERT instead
- ❌ "I'll try a different approach..." → Escalate to user
- ❌ Implementing fixes 2 and 3 together → One at a time!
- ❌ Skipping test run → ALWAYS validate
- ❌ Creating analysis docs → Wrong phase!

**Instead:**
- ✅ Tests fail? REVERT immediately
- ✅ Uncertain? Show diff, ask approval
- ✅ One fix at a time, validate each
- ✅ Update todos in real-time

---

## 🚀 START COMMAND

**Copy-paste this to start:**

```
Starting Implementation Phase:

Input: /Users/chrislehnen/Downloads/prompt-analysis-output.json
Pattern: ReAct (Reason → Act → Observe → Decide)
Budget: 3 fixes, 2 hours max

Phase 1: Load analysis + create todos (5 min)
Phase 2: Implement each fix with ReAct pattern (30 min each)
Phase 3: Final validation + report (15 min)

Begin Phase 1: Load analysis now.
```

---

## 📚 References

**Pattern:** ReAct (Reasoning and Acting)
- Interleave reasoning with action
- Each action provides observation
- Observation informs next reasoning

**Principles:**
- One change at a time
- Validate immediately
- Revert on failure
- Graduated autonomy

**Related Files:**
- Input: `prompt-analysis-output.json` (from bounded-prompt-analysis.md)
- Workflow: `prompt-improvement-workflow.md` (detailed documentation)

---

**Last Updated:** 2025-01-20
**Status:** Active
**Type:** Copy-Paste Prompt (ready for Claude Code)
