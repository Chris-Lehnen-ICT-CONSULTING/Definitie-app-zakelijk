# Bounded Codebase Analysis - 5 Whys + Pareto + MECE

**Version:** 1.0 (Adapted for Codebase Investigation)
**Created:** 2025-11-21
**Time Limit:** 60 minutes HARD STOP
**Framework:** Integrate 5 Whys, Pareto (80/20), MECE, Impact-Effort Matrix
**Principle:** Fast decision makers use LESS information, not more

---

## ⚠️ CRITICAL RULES

**MUST DO:**
- ✅ Complete in 60 minutes (timeboxing prevents analysis paralysis)
- ✅ Apply 80/20 rule: 80% of risks/issues come from 20% of the codebase
- ✅ Use MECE categories (Mutually Exclusive, Collectively Exhaustive)
- ✅ Satisfice: Find "good enough" insights, not a perfect audit
- ✅ Establish decision criteria BEFORE investigating

**NEVER DO:**
- ❌ Analyze every single file (impossible in 60m)
- ❌ Gather perfect information (90% is context, 10% actionable)
- ❌ Continue past 5 Whys for each issue
- ❌ Investigate without hypothesis (prevents endless exploration)
- ❌ Exceed time budget (sunk-cost fallacy prevention)

---

## 📋 PHASE 1: Problem Statement + MECE Decomposition (15 min)

### Step 1: Define Problem (5 min)

**Goal:** Investigate the health, quality, and architectural integrity of the entire codebase.

**Metrics:**
- **Size:** Lines of Code (LOC), Number of Files
- **Complexity:** Cyclomatic complexity, Dependency depth
- **Coverage:** Test coverage percentage
- **Debt:** TODOs, FIXMEs, Deprecated usage

### Step 2: MECE Categories (10 min)

**Create Mutually Exclusive, Collectively Exhaustive categories for investigation:**

| Category | Definition | Example Issues |
|----------|------------|----------------|
| **Architecture** | Structural design & patterns | Circular dependencies, violation of layers |
| **Code Quality** | Readability & Maintainability | Long functions, duplicate code, lack of types |
| **Security** | Vulnerabilities & Safety | Hardcoded secrets, injection risks, no auth |
| **Performance** | Efficiency & Speed | N+1 queries, unoptimized loops, memory leaks |
| **Documentation** | Clarity & Completeness | Missing docstrings, outdated README, no API docs |

**Rule:** Every issue MUST fit in exactly ONE category.
**Rule:** ALL issues MUST fit in SOME category.

**Output:**
```json
{
  "mece_categories": {
    "architecture": ["issue1"],
    "code_quality": ["issue2", "issue3"],
    "security": [],
    "performance": ["issue4"],
    "documentation": ["issue5"]
  }
}
```

**STOP if no issues found in any category → Report clean health**

---

## 📋 PHASE 2: Pareto Analysis (20 min)

### Step 1: Apply 80/20 Rule (10 min)

**For each MECE category, estimate impact/frequency:**

```json
{
  "pareto_analysis": {
    "code_quality": {
      "instances": 50,
      "risk_impact_est": "HIGH",
      "percentage_of_total": 60%
    },
    "architecture": {
      "instances": 5,
      "risk_impact_est": "CRITICAL",
      "percentage_of_total": 20%
    },
    ...
  }
}
```

**Identify VITAL FEW:**
- Which 20% of categories cause 80% of the risk?
- Focus ONLY on top 2-3 categories.

### Step 2: 5 Whys on TOP 3 (10 min)

**For EACH of top 3 categories, ask 5 Whys:**

**Example - Code Quality (High Complexity):**

```
Why 1: Why is module X so complex?
Answer: It handles validation, generation, and storage in one file.

Why 2: Why does it handle all three?
Answer: It was the initial prototype and never refactored.

Why 3: Why wasn't it refactored?
Answer: No clear architectural guidelines for splitting services.

Why 4: Why are there no guidelines?
Answer: The project started as a script and grew organically.

Why 5: Why is it still treated as a script?
Answer: Lack of dedicated refactoring sprints.

ROOT CAUSE: Lack of architectural enforcement and refactoring time.
```

**STOP after 5 Whys per category.**

---

## 📋 PHASE 3: Impact-Effort Prioritization (15 min)

### Impact-Effort Matrix

**For each root cause, calculate:**

```
Priority Score = (Risk Impact × Confidence) / Effort Hours
```

**Classify into quadrants:**

| Quadrant | Impact | Effort | Action |
|----------|--------|--------|--------|
| **Quick Wins** | HIGH | LOW | Do FIRST |
| **Major Projects** | HIGH | HIGH | Schedule |
| **Fill-ins** | LOW | LOW | Do if time |
| **Thankless** | LOW | HIGH | SKIP |

**SELECT TOP 3 based on priority score.**

---

## 📋 PHASE 4: Generate Recommendations (10 min)

**For each TOP 3 issue, create actionable spec:**

```json
{
  "recommendations": [
    {
      "rank": 1,
      "issue": "Monolithic Service X",
      "root_cause": "Lack of architectural enforcement",
      "action": "Split Service X into Validator, Generator, Repository",
      "impact": {
        "risk_reduction": "HIGH",
        "effort_hours": 8
      },
      "quadrant": "Major Project"
    }
  ]
}
```

---

## 🎯 FINAL OUTPUT (JSON Format)

```json
{
  "analysis_metadata": {
    "framework": "Bounded Codebase Analysis",
    "time_spent_min": 55
  },
  "mece_decomposition": {...},
  "pareto_analysis": {...},
  "root_causes_5whys": [...],
  "impact_effort_matrix": {...},
  "top_3_recommendations": [...]
}
```

**Save to:** `reports/codebase-analysis-output.json`
