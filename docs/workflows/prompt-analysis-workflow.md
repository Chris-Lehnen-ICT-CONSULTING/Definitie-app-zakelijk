# ANALYSEER Prompt Issues - BOUNDED ANALYSIS

**Version:** 1.0
**Created:** 2025-01-20
**Purpose:** Bounded analyse van prompt issues → Direct actionable output voor implementatie
**Next Step:** Output feeds into `prompt-improvement-workflow.md`

---

## ⚠️ CRITICAL RULES - READ FIRST

**YOU MUST:**
- ✅ Deliver analysis in MAXIMUM 60 minutes
- ✅ Prioritize TOP 3 issues only
- ✅ Output structured JSON for implementation
- ✅ STOP after identifying actionable issues
- ✅ Use TodoWrite to track analysis progress

**YOU MUST NOT:**
- ❌ Analyze all possible issues (only top 3)
- ❌ Create comprehensive reports
- ❌ Deep-dive into root causes
- ❌ Explore edge cases
- ❌ Continue analysis beyond 60 minutes

**STOPPING CRITERIA:**
- Stop after identifying 3 critical issues
- Stop after 60 minutes (hard limit)
- Stop when enough data for implementation decision
- Stop if more than 3 Linear issues analyzed

---

## 🎯 TASK: Identify TOP 3 Prompt Issues

**Input Files:**
- Current prompt: `/Users/chrislehnen/Downloads/_Definitie_Generatie_prompt-23.txt`
- Previous prompt (optional): `/Users/chrislehnen/Downloads/_Definitie_Generatie_prompt-22.txt`

**Success = Actionable JSON output with TOP 3 issues + implementation priorities**

---

## 📋 PHASE 1: Quick Assessment (20 min MAX)

### Step 1: Read Current Prompt (10 min)

**Action:**
```bash
# Read prompt file
Read: /Users/chrislehnen/Downloads/_Definitie_Generatie_prompt-23.txt

# Quick metrics
Count:
- Total lines
- Total characters
- Estimated tokens (chars / 4)
- Number of sections (count ##, ###)
```

**Look for (5 min visual scan):**
- ❌ Obvious duplications (same text 2+ times)
- ❌ Contradictions (says A in section 1, says NOT A in section 2)
- ❌ "Toetsvraag:" patterns (should be instructions)
- ❌ Very long sections (>100 lines)
- ❌ Metadata positioning (should be early)

**Output:**
```json
{
  "quick_metrics": {
    "lines": 534,
    "characters": 45000,
    "tokens_estimated": 11250,
    "sections_count": 45
  },
  "visual_scan_issues": [
    "Duplication: 'enkelvoud' appears 5 times",
    "Contradiction: ESS-02 vs forbidden starts",
    "'Toetsvraag:' found 8 times (should be 0)"
  ]
}
```

### Step 2: Scan Linear for Known Issues (10 min)

**Action:**
```
Query Linear: "DEF-101 OR DEF-169 OR DEF-156 OR DEF-126 OR DEF-38"
Read: ONLY title + description (NOT full issue)
Extract: Problem statement + Desired state
```

**For each issue, note:**
- Issue ID
- Problem (1 sentence)
- Desired state (1 sentence)
- Status (In Progress / Backlog / Done)

**STOP after reading 5 issues maximum.**

**Output:**
```json
{
  "linear_issues": [
    {
      "id": "DEF-169",
      "problem": "ErrorPreventionModule duplicates JSONBasedRulesModule",
      "desired": "Remove redundant module, save 1000 tokens",
      "status": "Backlog",
      "priority": "HIGH"
    }
  ]
}
```

---

## 📋 PHASE 2: Issue Prioritization (20 min MAX)

### Step 1: Match Prompt Issues to Linear Issues (10 min)

**Create mapping:**

| Prompt Issue | Line Numbers | Linear Issue | Token Impact | Confidence |
|--------------|--------------|--------------|--------------|------------|
| Duplication: "enkelvoud" 5x | 45, 198, 312, 401, 478 | DEF-156 | -200 | 90% |
| "Toetsvraag:" pattern 8x | [...] | DEF-126 | -150 | 85% |
| ESS-02 contradiction | 77-90 | DEF-101 | -50 | 95% |

**STOP after identifying 5 issues maximum.**

### Step 2: Apply Priority Matrix (10 min)

**Formula:** `Priority Score = (Token Impact × Confidence) / Effort`

**Effort estimates:**
- Remove duplication: 1 hour
- Transform to instructions: 2 hours
- Fix contradiction: 30 min

**Calculate & Sort:**

```json
{
  "prioritized_issues": [
    {
      "rank": 1,
      "issue": "ESS-02 contradiction",
      "module": "semantic_categorisation_module.py",
      "token_impact": -50,
      "effort_hours": 0.5,
      "confidence": 95,
      "priority_score": 95,
      "linear_ref": "DEF-101"
    },
    {
      "rank": 2,
      "issue": "Duplicate 'enkelvoud' rules",
      "module": "arai_rules_module.py + error_prevention_module.py",
      "token_impact": -200,
      "effort_hours": 1.0,
      "confidence": 90,
      "priority_score": 180,
      "linear_ref": "DEF-156"
    },
    {
      "rank": 3,
      "issue": "'Toetsvraag:' pattern in 8 rules",
      "module": "Multiple rule modules",
      "token_impact": -150,
      "effort_hours": 2.0,
      "confidence": 85,
      "priority_score": 64,
      "linear_ref": "DEF-126"
    }
  ]
}
```

**SELECT TOP 3 ONLY. STOP HERE.**

---

## 📋 PHASE 3: Generate Implementation Input (20 min MAX)

### Step 1: Create Module-Specific Actions (15 min)

**For each TOP 3 issue:**

```json
{
  "implementation_actions": [
    {
      "priority": 1,
      "issue_id": "ESS-02 contradiction",
      "module": "src/services/prompts/modules/semantic_categorisation_module.py",
      "action": "Remove 'is een activiteit' template, keep only active verb patterns",
      "location": "Lines 77-90",
      "before": "is een activiteit waarbij...",
      "after": "activiteit waarbij...",
      "expected_impact": {
        "tokens": -50,
        "quality": "Removes contradiction"
      },
      "validation": {
        "test_command": "pytest tests/services/prompts/",
        "success_criteria": "All tests pass + generate 1 test definition"
      },
      "confidence": 95,
      "estimated_effort": "30 min"
    },
    {
      "priority": 2,
      "issue_id": "Duplicate enkelvoud rules",
      "module": "src/services/prompts/modules/arai_rules_module.py",
      "action": "Keep in arai_rules_module, remove from error_prevention_module",
      "location": "error_prevention_module.py lines 45, 198, 312",
      "before": "3 instances of 'enkelvoud' rule",
      "after": "1 instance in arai_rules_module only",
      "expected_impact": {
        "tokens": -200,
        "quality": "Eliminates redundancy"
      },
      "validation": {
        "test_command": "pytest tests/services/prompts/",
        "success_criteria": "Tests pass + token count reduced"
      },
      "confidence": 90,
      "estimated_effort": "1 hour"
    },
    {
      "priority": 3,
      "issue_id": "Toetsvraag pattern transformation",
      "module": "Multiple: str_rules_module.py, int_rules_module.py, ver_rules_module.py",
      "action": "Transform 'Toetsvraag: Is X?' to 'Zorg dat X' format",
      "location": "8 instances across 3 modules",
      "before": "Toetsvraag: Is de definitie in enkelvoud?",
      "after": "Formuleer de definitie in enkelvoud",
      "expected_impact": {
        "tokens": -150,
        "quality": "Better LLM guidance"
      },
      "validation": {
        "test_command": "pytest tests/services/prompts/",
        "success_criteria": "Tests pass + improved definition quality"
      },
      "confidence": 85,
      "estimated_effort": "2 hours"
    }
  ]
}
```

### Step 2: Create Implementation Checklist (5 min)

**Generate TodoWrite-ready format:**

```json
{
  "implementation_checklist": {
    "total_items": 5,
    "estimated_total_effort": "3.5 hours",
    "expected_token_reduction": 400,
    "todos": [
      {
        "id": 1,
        "description": "Fix ESS-02 contradiction in semantic_categorisation_module",
        "activeForm": "Fixing ESS-02 contradiction",
        "module": "semantic_categorisation_module.py",
        "lines": "77-90",
        "effort": "30 min",
        "token_impact": -50,
        "status": "pending"
      },
      {
        "id": 2,
        "description": "Remove duplicate enkelvoud rules from error_prevention_module",
        "activeForm": "Removing duplicate enkelvoud rules",
        "module": "error_prevention_module.py",
        "lines": "45, 198, 312",
        "effort": "1 hour",
        "token_impact": -200,
        "status": "pending"
      },
      {
        "id": 3,
        "description": "Transform Toetsvraag patterns to instructions in 3 modules",
        "activeForm": "Transforming Toetsvraag patterns",
        "module": "str_rules_module.py, int_rules_module.py, ver_rules_module.py",
        "lines": "Multiple",
        "effort": "2 hours",
        "token_impact": -150,
        "status": "pending"
      },
      {
        "id": 4,
        "description": "Generate 3 test definitions with fixed prompt",
        "activeForm": "Generating test definitions",
        "module": "N/A",
        "effort": "30 min",
        "token_impact": 0,
        "status": "pending"
      },
      {
        "id": 5,
        "description": "Measure token reduction and update Linear issues",
        "activeForm": "Measuring results",
        "module": "N/A",
        "effort": "30 min",
        "token_impact": 0,
        "status": "pending"
      }
    ]
  }
}
```

---

## 📊 FINAL OUTPUT: Implementation Package

**Combine all data into single JSON:**

```json
{
  "analysis_metadata": {
    "timestamp": "2025-01-20T14:30:00Z",
    "current_prompt": "_Definitie_Generatie_prompt-23.txt",
    "analysis_duration_min": 55,
    "issues_analyzed": 3,
    "total_issues_found": 8,
    "issues_prioritized": 3
  },
  "baseline_metrics": {
    "prompt_lines": 534,
    "prompt_tokens_estimated": 11250,
    "major_sections": 45,
    "duplications_found": 5,
    "contradictions_found": 2,
    "toetsvraag_instances": 8
  },
  "top_3_issues": [
    {
      "rank": 1,
      "id": "ESS-02 contradiction",
      "severity": "CRITICAL",
      "module": "semantic_categorisation_module.py",
      "description": "Templates contain 'is een' patterns that contradict forbidden starts rule",
      "token_impact": -50,
      "effort_hours": 0.5,
      "confidence": 95,
      "linear_issue": "DEF-101"
    },
    {
      "rank": 2,
      "id": "Duplicate enkelvoud rules",
      "severity": "HIGH",
      "module": "arai_rules_module.py + error_prevention_module.py",
      "description": "Enkelvoud rule appears 3 times across 2 modules",
      "token_impact": -200,
      "effort_hours": 1.0,
      "confidence": 90,
      "linear_issue": "DEF-156"
    },
    {
      "rank": 3,
      "id": "Toetsvraag pattern",
      "severity": "MEDIUM",
      "module": "Multiple rule modules",
      "description": "8 rules use validation format instead of instruction format",
      "token_impact": -150,
      "effort_hours": 2.0,
      "confidence": 85,
      "linear_issue": "DEF-126"
    }
  ],
  "implementation_actions": [
    /* Full action details from Phase 3 Step 1 */
  ],
  "implementation_checklist": {
    /* Full checklist from Phase 3 Step 2 */
  },
  "expected_outcomes": {
    "total_token_reduction": 400,
    "total_effort_hours": 3.5,
    "tests_affected": "13 test files",
    "modules_changed": 4,
    "linear_issues_resolved": 3
  },
  "ready_for_implementation": true,
  "next_step": "Use prompt-improvement-workflow.md with this output"
}
```

---

## ⚡ QUICK DECISION TREE

**After analysis, check:**

```
Issues found < 3?
  ✅ YES → Output analysis, mark as low-priority
  ❌ NO  → Continue

Token impact > 300?
  ✅ YES → High priority, implement immediately
  ❌ NO  → Medium priority, schedule

All modules identifiable?
  ✅ YES → Ready for implementation
  ❌ NO  → Escalate unclear modules to user

Effort > 4 hours?
  ✅ YES → Break into 2 implementation phases
  ❌ NO  → Single implementation phase
```

---

## 🚫 ANALYSIS ANTI-PATTERNS

**If you catch yourself doing ANY of these, STOP:**

- ❌ Analyzing more than 3 issues in detail
- ❌ Reading more than 5 Linear issues
- ❌ Creating root cause analysis
- ❌ Exploring "all possible solutions"
- ❌ Deep-diving into module architecture
- ❌ Analyzing token economics in detail
- ❌ Creating comparison matrices
- ❌ Reading module code (save for implementation)

**Instead:**
- ✅ Focus on TOP 3 highest impact
- ✅ Surface-level scan only
- ✅ Direct mapping to action
- ✅ Concrete line numbers
- ✅ Estimations, not precision

---

## 📏 SUCCESS CRITERIA

**Analysis is complete when:**
- ✅ TOP 3 issues identified with line numbers
- ✅ Implementation actions specified per issue
- ✅ TodoWrite-ready checklist created
- ✅ JSON output generated
- ✅ Total time < 60 minutes
- ✅ Ready for `prompt-improvement-workflow.md`

**Analysis FAILS if:**
- ❌ More than 60 minutes spent
- ❌ Output not actionable (vague recommendations)
- ❌ No concrete line numbers provided
- ❌ No module names specified
- ❌ Token impact not estimated
- ❌ Cannot feed directly into implementation

---

## 🔗 HANDOFF TO IMPLEMENTATION

**Once analysis complete:**

1. **Save JSON output** to `/Users/chrislehnen/Downloads/prompt-analysis-output.json`

2. **User reviews** TOP 3 issues and approves

3. **Start implementation** using `prompt-improvement-workflow.md`:
   ```markdown
   Input: prompt-analysis-output.json
   Action: Execute implementation_checklist
   Validate: Run tests after each todo
   Report: Final metrics vs expected_outcomes
   ```

4. **Implementation prompt** has all needed data:
   - Exact modules to change
   - Exact line numbers
   - Before/after examples
   - Token impact expectations
   - Success criteria
   - Test commands

**No additional analysis needed in implementation phase!**

---

## 🚀 START COMMAND

**Copy-paste this to start:**

```markdown
# Start Bounded Prompt Analysis

**Task:** Analyze `/Users/chrislehnen/Downloads/_Definitie_Generatie_prompt-23.txt`

**Deliverable:** JSON with TOP 3 issues ready for implementation

**Time Limit:** 60 minutes MAX

**Next Step:** Output feeds into `prompt-improvement-workflow.md`

Begin Phase 1: Quick Assessment (20 min)
```

---

## 📚 References

**Analysis Frameworks:**
- MECE Principle: Mutually Exclusive, Collectively Exhaustive prioritization
- 80/20 Rule: Focus on 20% of issues causing 80% of problems
- Priority Queue Pattern: Process highest-impact items first
- Vertical Slicing: End-to-end actionable outputs, not components

**Related Workflows:**
- `prompt-improvement-workflow.md` - Uses this analysis as input
- Linear Issues: DEF-101, DEF-169, DEF-156, DEF-126, DEF-38

**Key Principles:**
1. Bounded analysis (60 min hard limit)
2. TOP 3 only (not comprehensive)
3. Actionable output (ready for implementation)
4. Structured JSON (machine-readable)
5. Priority-driven (impact × confidence / effort)
6. No deep-dives (save for implementation)

---

**Last Updated:** 2025-01-20
**Status:** Active
**Pair With:** `prompt-improvement-workflow.md`
