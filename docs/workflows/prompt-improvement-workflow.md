# IMPLEMENTEER Prompt Verbeteringen - GEEN ANALYSE

**Version:** 1.0
**Created:** 2025-01-20
**Purpose:** Actionable workflow voor Claude Code om prompt builder te verbeteren zonder analysis paralysis

---

## ⚠️ CRITICAL RULES - READ FIRST

**YOU MUST:**
- ✅ IMPLEMENT fixes directly in code
- ✅ STOP after each fix and validate
- ✅ Use TodoWrite to track progress
- ✅ Generate test definitions after each change
- ✅ Measure token reduction after each change

**YOU MUST NOT:**
- ❌ Create analysis documents
- ❌ Write implementation plans
- ❌ Generate recommendations
- ❌ Propose solutions without implementing
- ❌ Continue to next task before validating current task

**STOPPING CRITERIA:**
- Stop after 3 module fixes (not after analyzing all modules)
- Stop after achieving 500 token reduction (cumulative)
- Stop after 2 hours of work
- Stop when test generation starts failing

---

## 🎯 TASK: Fix Prompt Generation Issues

**Input:** `/Users/chrislehnen/Downloads/_Definitie_Generatie_prompt-23.txt`

**Success = 3 Implemented Fixes + Working Test Definitions**

---

## 📋 PHASE 1: Baseline (15 min MAX)

**Action sequence (do NOT analyze beyond this):**

1. **Read prompt-23.txt** (5 min)
   - Count total lines, characters
   - Estimate tokens (chars / 4)
   - Note 3 most obvious problems (NOT a comprehensive list)

2. **Search Linear for requirements** (5 min)
   ```
   Query: "DEF-101 OR DEF-169 OR DEF-156 OR DEF-126"
   Extract: TOP 3 CRITICAL requirements only
   ```

3. **Create Todo List** (5 min)
   ```
   [ ] Fix 1: [Most critical issue from Linear]
   [ ] Fix 2: [Second most critical]
   [ ] Fix 3: [Third most critical]
   [ ] Generate 3 test definitions
   [ ] Measure token reduction
   ```

**OUTPUT:** Todo list with 5 items. **STOP HERE. Wait for user approval.**

---

## 📋 PHASE 2: Implement Fixes (ReAct Loop)

**For EACH todo (max 3 fixes):**

### Iteration Pattern: REASON → ACT → OBSERVE → DECIDE

**REASON** (5 min):
- Which module causes this problem?
- What exact code change fixes it?
- Expected token impact?

**ACT** (15 min):
- Edit the module file
- Run existing tests
- Generate 1 test definition with new prompt

**OBSERVE** (10 min):
- Did tests pass? ✅/❌
- Did test definition improve? Compare to baseline
- Measure token count change

**DECIDE** (2 min):
- ✅ Success → Mark todo complete, move to next
- ❌ Failed → Revert change, escalate to user

**AUTONOMY RULES:**
- Confidence >80% → Implement directly
- Confidence 50-80% → Show code diff, ask approval
- Confidence <50% → Escalate to user immediately

**STOPPING CRITERIA PER ITERATION:**
- Stop after 30 min per fix (time budget)
- Stop if tests fail 2x (revert and escalate)
- Stop if token count increases (regression)

---

## 📋 PHASE 3: Validate & Report (15 min)

**Actions:**

1. **Generate 3 test definitions** with final prompt
2. **Compare to baseline:**
   ```
   Baseline (v22): [tokens] tokens, [quality issues]
   After fixes (v23): [tokens] tokens, [quality issues]
   Reduction: [X] tokens ([%]%)
   ```
3. **Update Linear issues** with completed work
4. **Report:**
   ```
   ✅ COMPLETED:
   - Fix 1: [module] - [change] - [token impact]
   - Fix 2: [module] - [change] - [token impact]
   - Fix 3: [module] - [change] - [token impact]

   📊 RESULTS:
   - Total token reduction: [X] ([%]%)
   - Test definitions: [quality assessment]
   - Tests passing: [X/Y]

   🚀 NEXT ACTIONS (for user):
   - [Optional: 1-2 follow-up items if critical]
   ```

**OUTPUT:** Completion report. **STOP. DO NOT continue to "next steps".**

---

## 🎯 STRUCTURED OUTPUT FORMAT (Enforce Boundaries)

**Use this JSON structure to force finite outputs:**

```json
{
  "phase": "1|2|3",
  "todos": [
    {
      "id": 1,
      "description": "Fix [specific issue]",
      "module": "src/services/prompts/modules/[name].py",
      "status": "pending|in_progress|completed|failed",
      "token_impact": -150,
      "confidence": 85,
      "time_spent_min": 25
    }
  ],
  "baseline_metrics": {
    "prompt_lines": 534,
    "prompt_tokens": 7250,
    "issues_identified": 3
  },
  "final_metrics": {
    "prompt_tokens": 6750,
    "token_reduction": 500,
    "reduction_percentage": 6.9,
    "test_definitions_generated": 3,
    "tests_passing": "13/13"
  },
  "status": "completed|blocked|needs_escalation",
  "escalation_reason": null
}
```

---

## ⚡ QUICK DECISION MATRIX (Use This to Prevent Analysis)

| Situation | Confidence | Action |
|-----------|------------|--------|
| Clear contradiction in prompt | >90% | Fix immediately |
| Duplicated section (exact match) | >90% | Remove immediately |
| Token reduction >100 | >80% | Implement, then validate |
| Module structure unclear | <70% | Read module code, decide, OR escalate |
| Tests failing after change | N/A | **REVERT immediately** |
| Token count increased | N/A | **REVERT immediately** |
| Spent >30 min on one fix | N/A | **STOP, escalate** |
| Completed 3 fixes | N/A | **STOP, report** |

---

## 🚫 ANTI-PATTERNS TO AVOID

**If you catch yourself doing ANY of these, STOP immediately:**

- ❌ Writing "let me analyze..."
- ❌ Creating markdown analysis docs
- ❌ Listing "all possible approaches"
- ❌ Saying "we could..." or "we should consider..."
- ❌ Generating "comprehensive reports"
- ❌ Exploring "edge cases" before fixing main cases
- ❌ Reading more than 3 Linear issues
- ❌ Analyzing more than 3 modules before fixing

**Instead, ask yourself:**
- ✅ "What is the SINGLE next action?"
- ✅ "Can I implement this in 30 minutes?"
- ✅ "Will this reduce tokens by >100?"

---

## 📏 SUCCESS METRICS (Implementation, Not Analysis)

**Primary (MUST achieve):**
- ✅ 3 code changes committed
- ✅ Token reduction ≥300 (cumulative)
- ✅ Tests passing (13/13)
- ✅ 3 test definitions generated

**Secondary (nice to have):**
- ✅ Linear issues updated
- ✅ Documentation updated
- ✅ Token reduction >500

**Failure indicators:**
- ❌ Analysis docs created
- ❌ No code changes after 1 hour
- ❌ Token count increased
- ❌ Tests failing

---

## 🚀 START NOW

1. **Create todo list** (Phase 1)
2. **Show it to user**
3. **STOP and wait for approval**

Do NOT:
- Analyze all modules
- Read all Linear issues
- Create implementation plans
- Propose approaches

**Type:** "Created 5-item todo list. Ready to proceed with Phase 1?" **Then STOP.**

---

## 📚 References

**Research Sources:**
- Perplexity research: Action-oriented prompting & preventing analysis paralysis
- DAIR-AI Prompt Engineering Guide: Best practices for implementation-focused prompts
- ReAct Framework: Reasoning and Acting pattern
- MECE Decomposition: Mutually Exclusive, Collectively Exhaustive task breakdown
- Graduated Autonomy: Confidence-based decision making

**Related Linear Issues:**
- DEF-101: EPIC: Prompt Improvement Plan
- DEF-169: Remove redundant ErrorPreventionModule
- DEF-156: Context Injection Consolidation
- DEF-126: Transform validation rules to instructions
- DEF-38: Critical issues in ontological prompts

**Key Principles Applied:**
1. Explicit stopping criteria after each phase
2. ReAct loop (Reason → Act → Observe → Decide)
3. Time budgets (15min, 30min limits)
4. Graduated autonomy (confidence-based decisions)
5. Structured JSON output (forces finite outputs)
6. Quick decision matrix (prevents overthinking)
7. Resource constraints (3 fixes max, 2 hours max)
8. Anti-pattern detection (catches analysis drift)
9. Implementation metrics (not analysis quality)
10. Forced user checkpoints (approval gates)

---

**Last Updated:** 2025-01-20
**Status:** Active
**Maintenance:** Update when workflow improves or new anti-patterns discovered
