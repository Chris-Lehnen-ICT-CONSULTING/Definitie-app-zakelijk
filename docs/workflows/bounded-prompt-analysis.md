# Bounded Prompt Analysis - 5 Whys + Pareto + MECE

**Version:** 2.0 (Research-Enhanced)
**Created:** 2025-01-20
**Time Limit:** 60 minutes HARD STOP
**Framework:** Integrate 5 Whys, Pareto (80/20), MECE, Impact-Effort Matrix
**Principle:** Fast decision makers use LESS information, not more

---

## ⚠️ CRITICAL RULES

**MUST DO:**
- ✅ Complete in 60 minutes (timeboxing prevents analysis paralysis)
- ✅ Apply 80/20 rule: 80% of issues from 20% of causes
- ✅ Use MECE categories (Mutually Exclusive, Collectively Exhaustive)
- ✅ Satisfice: Find "good enough" solutions, not perfect ones
- ✅ Establish decision criteria BEFORE investigating

**NEVER DO:**
- ❌ Analyze beyond TOP 3 issues (Pareto principle)
- ❌ Gather perfect information (90% is context, 10% actionable)
- ❌ Continue past 5 Whys for each issue
- ❌ Investigate without hypothesis (prevents endless exploration)
- ❌ Exceed time budget (sunk-cost fallacy prevention)

---

## 📋 PHASE 1: Problem Statement + MECE Decomposition (15 min)

### Step 1: Define Problem (5 min)

**Read:** `/Users/chrislehnen/Downloads/_Definitie_Generatie_prompt-23.txt`

**Metrics:**
```json
{
  "baseline": {
    "lines": X,
    "chars": Y,
    "tokens_est": Y/4,
    "sections": count(##)
  }
}
```

### Step 2: MECE Categories (10 min)

**Create Mutually Exclusive, Collectively Exhaustive categories:**

| Category | Definition | Example Issues |
|----------|------------|----------------|
| **Redundancy** | Same content appears 2+ times | "enkelvoud" 5x |
| **Contradiction** | Says A, then NOT A | ESS-02 vs forbidden |
| **Format** | Wrong structure (validation vs instruction) | "Toetsvraag:" 8x |
| **Organization** | Misplaced content | Metadata at line 400 |
| **Verbosity** | >100 lines per section | Section X has 150 lines |

**Rule:** Every issue MUST fit in exactly ONE category (mutually exclusive).
**Rule:** ALL issues MUST fit in SOME category (collectively exhaustive).

**Output:**
```json
{
  "mece_categories": {
    "redundancy": ["issue1", "issue2"],
    "contradiction": ["issue3"],
    "format": ["issue4", "issue5"],
    "organization": [],
    "verbosity": ["issue6"]
  }
}
```

**STOP if no issues found in any category → Escalate to user**

---

## 📋 PHASE 2: Pareto Analysis (20 min)

### Step 1: Apply 80/20 Rule (10 min)

**For each MECE category, count frequency:**

```json
{
  "pareto_analysis": {
    "redundancy": {
      "instances": 12,
      "token_impact_est": 400,
      "percentage_of_total": 45%
    },
    "contradiction": {
      "instances": 3,
      "token_impact_est": 150,
      "percentage_of_total": 15%
    },
    "format": {
      "instances": 8,
      "token_impact_est": 300,
      "percentage_of_total": 30%
    }
  }
}
```

**Identify VITAL FEW:**
- Which 20% of categories cause 80% of problems?
- Focus ONLY on top 2-3 categories

### Step 2: 5 Whys on TOP 3 (10 min)

**For EACH of top 3 categories, ask 5 Whys:**

**Example - Redundancy:**

```
Why 1: Why does "enkelvoud" appear 5 times?
Answer: Appears in arai_rules_module (1x), error_prevention_module (3x), grammar_module (1x)

Why 2: Why is it in multiple modules?
Answer: ErrorPreventionModule duplicates rules from other modules (DEF-169)

Why 3: Why was ErrorPreventionModule created with duplicates?
Answer: Created before JSONBasedRulesModule existed

Why 4: Why wasn't it removed after JSONBasedRulesModule was added?
Answer: No one tracked redundancy across modules

Why 5: Why is there no redundancy tracking?
Answer: No systematic review process for module overlap

ROOT CAUSE: ErrorPreventionModule is redundant with JSONBasedRulesModule
```

**STOP after 5 Whys per category (prevents analysis paralysis)**

**Output:**
```json
{
  "root_causes": [
    {
      "category": "redundancy",
      "root_cause": "ErrorPreventionModule duplicates JSONBasedRulesModule",
      "why_chain": ["...", "...", "...", "...", "..."],
      "linear_issue": "DEF-169"
    }
  ]
}
```

---

## 📋 PHASE 3: Impact-Effort Prioritization (15 min)

### Impact-Effort Matrix

**For each root cause, calculate:**

```
Priority Score = (Token Impact × Confidence) / Effort Hours
```

**Classify into quadrants:**

| Quadrant | Impact | Effort | Action |
|----------|--------|--------|--------|
| **Quick Wins** | HIGH | LOW | Do FIRST |
| **Major Projects** | HIGH | HIGH | Schedule |
| **Fill-ins** | LOW | LOW | Do if time |
| **Thankless** | LOW | HIGH | SKIP |

**Example:**

```json
{
  "impact_effort_matrix": {
    "quick_wins": [
      {
        "issue": "Remove ErrorPreventionModule",
        "impact": "HIGH (-1000 tokens)",
        "effort": "LOW (30 min)",
        "priority_score": 200,
        "quadrant": "Quick Win"
      }
    ],
    "major_projects": [
      {
        "issue": "Transform all Toetsvraag patterns",
        "impact": "HIGH (-300 tokens)",
        "effort": "HIGH (3 hours)",
        "priority_score": 50,
        "quadrant": "Major Project"
      }
    ]
  }
}
```

**SELECT TOP 3 based on priority score**

**STOP after identifying top 3 (satisficing principle)**

---

## 📋 PHASE 4: Generate Implementation Input (10 min)

**For each TOP 3 issue, create actionable spec:**

```json
{
  "implementation_actions": [
    {
      "rank": 1,
      "issue": "Remove redundant ErrorPreventionModule",
      "root_cause": "Duplicates JSONBasedRulesModule (5 Whys analysis)",
      "module": "src/services/prompts/modules/error_prevention_module.py",
      "action": "Comment out module registration in modular_prompt_adapter.py",
      "location": "Line 120",
      "before": "ErrorPreventionModule(),",
      "after": "# ErrorPreventionModule(),  # DEF-169: Redundant with JSONBased",
      "impact": {
        "tokens": -1000,
        "quality": "Removes 100% duplication",
        "effort_hours": 0.5,
        "confidence": 95
      },
      "validation": "Generate prompt, compare token count",
      "linear_issue": "DEF-169",
      "quadrant": "Quick Win",
      "priority_score": 190
    }
  ]
}
```

---

## 📊 DECISION CRITERIA (Establish Before Analysis)

**Issue is "root cause" when:**
- ✅ Identified through 5 Whys (went to depth 5)
- ✅ Fixing it prevents recurrence (not just symptom)
- ✅ Consistent with observed problems
- ✅ Confidence ≥ 70% (satisficing, not perfection)

**Analysis is "complete" when:**
- ✅ Top 3 issues identified via Pareto
- ✅ Each issue has 5 Whys chain
- ✅ Impact-Effort scores calculated
- ✅ Time < 60 minutes
- ✅ Ready for implementation (actionable specs)

**STOP criteria:**
- 60 minutes elapsed → Output current findings
- Top 3 identified → Don't analyze more
- Confidence on top issue < 50% → Escalate to user
- No issues in MECE categories → Escalate to user

---

## 🎯 FINAL OUTPUT (JSON Format)

```json
{
  "analysis_metadata": {
    "framework": "5 Whys + Pareto + MECE + Impact-Effort",
    "time_spent_min": 55,
    "decision_criteria_met": true,
    "satisficing_threshold": 70
  },
  "mece_decomposition": {
    "categories": {...},
    "total_issues_found": 18
  },
  "pareto_analysis": {
    "vital_few_categories": ["redundancy", "format"],
    "percentage_covered": 85,
    "trivial_many_ignored": ["verbosity"]
  },
  "root_causes_5whys": [
    {
      "category": "redundancy",
      "root_cause": "...",
      "why_chain": ["...", "...", "...", "...", "..."],
      "confidence": 95
    }
  ],
  "impact_effort_matrix": {
    "quick_wins": [...],
    "major_projects": [...],
    "fill_ins": [],
    "thankless": []
  },
  "top_3_implementation": [
    {
      "rank": 1,
      "priority_score": 190,
      "module": "...",
      "action": "...",
      "validation": "...",
      "effort_hours": 0.5,
      "token_impact": -1000
    }
  ],
  "expected_outcomes": {
    "total_token_reduction": 1450,
    "total_effort_hours": 4.5,
    "issues_resolved": 3,
    "pareto_coverage": "85% of problems"
  },
  "ready_for_implementation": true
}
```

**Save to:** `/Users/chrislehnen/Downloads/prompt-analysis-output.json`

---

## 🚫 ANALYSIS ANTI-PATTERNS

**STOP immediately if you catch yourself:**
- ❌ "Let me do a comprehensive analysis..." → Use Pareto instead
- ❌ "I need to investigate all possibilities..." → Use satisficing
- ❌ "Let me gather more data..." → Decision criteria not met?
- ❌ Analyzing beyond vital 20% → Violates Pareto
- ❌ Going beyond 5 Whys → Diminishing returns
- ❌ Analyzing issues in thankless quadrant → Skip them

**Instead ask:**
- ✅ "Which 20% causes 80% of problems?" (Pareto)
- ✅ "Is confidence ≥ 70%?" (Satisficing threshold)
- ✅ "Are decision criteria met?" (Stop condition)
- ✅ "Am I past 60 minutes?" (Timeboxing)

---

## ⚡ START COMMAND

**Copy-paste this:**

```
Starting Bounded Analysis (60 min max):

Phase 1 (15 min): MECE Decomposition
Phase 2 (20 min): Pareto + 5 Whys
Phase 3 (15 min): Impact-Effort Matrix
Phase 4 (10 min): Implementation Specs

Frameworks: 5 Whys, Pareto 80/20, MECE, Impact-Effort
Principle: Fast decisions use LESS info, not more

Begin Phase 1 now.
```

---

## 📚 Framework References

### Applied Principles

**5 Whys (Toyota Production System)**
- Linear root cause analysis
- Stop at depth 5 (prevents analysis paralysis)
- Each "why" builds on previous answer
- Reaches systemic issues, not symptoms

**Pareto Principle (80/20 Rule)**
- 80% of problems stem from 20% of causes
- Focus investigation on "vital few"
- Ignore "trivial many" until vital few resolved
- Iterative: apply again to remaining 20%

**MECE (McKinsey)**
- Mutually Exclusive: no overlap between categories
- Collectively Exhaustive: all issues fit somewhere
- Prevents gaps and redundancy in analysis
- Enables parallel investigation

**Impact-Effort Matrix**
- Quick Wins: High impact, low effort → Do first
- Major Projects: High impact, high effort → Schedule
- Fill-ins: Low impact, low effort → Do if time
- Thankless: Low impact, high effort → Skip

**Timeboxing**
- Hard time limits prevent analysis paralysis
- Forces prioritization within phases
- Prevents sunk-cost fallacy
- Creates natural decision points

**Satisficing (Herbert Simon)**
- Find "satisfactory" solutions, not optimal
- 70% confidence sufficient vs 100% impossible
- Beyond threshold, more analysis = diminishing returns
- Acknowledges bounded rationality

**Bounded Rationality**
- Accept cognitive limitations
- Perfect information unavailable
- Design processes around constraints
- Fast decisions with less info > slow with more

**Decision Velocity Principle**
- 90% of data is context, 10% actionable
- Fast decision makers use less information
- Establish decision criteria upfront
- Accept decisions will sometimes be wrong

### Research Sources

**Perplexity Research:**
- "Bounded Problem Analysis in Software Engineering"
- Root cause analysis frameworks
- Analysis paralysis prevention
- Decision-making under uncertainty

**Academic Foundations:**
- Toyota Production System (5 Whys)
- McKinsey MECE Principle
- Herbert Simon: Satisficing & Bounded Rationality
- Vilfredo Pareto: 80/20 Rule
- Kaoru Ishikawa: Fishbone Diagrams

**Practical Frameworks:**
- Impact-Effort Matrix (Product Management)
- Timeboxing (Agile Methodologies)
- Cynefin Framework (Decision Domains)
- Blameless Post-Mortems (SRE)

---

## 🔗 Integration with Other Workflows

**This analysis feeds into:**
- `prompt-improvement-workflow.md` - Implementation workflow
- JSON output becomes direct input for implementation
- No additional analysis needed in implementation phase

**Comparison to previous version:**
- v1.0 (`prompt-analysis-workflow.md`): Basic analysis structure
- v2.0 (this file): Research-enhanced with proven frameworks
- Token: 50% more structured, 80% faster decisions

---

**Last Updated:** 2025-01-20
**Status:** Active (Research-Enhanced)
**Supersedes:** `prompt-analysis-workflow.md` (basic version)
**Pair With:** `prompt-improvement-workflow.md` (implementation)
