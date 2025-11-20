# Instruction Files Optimization Strategy

**Project:** DefinitieAgent
**Date:** 2025-01-18
**Strategy Version:** 1.0
**Target:** 83% token reduction (61,678 tokens saved)

---

## 1. Strategy Overview

### 1.1 Optimization Philosophy

**Research-Driven Approach:**
- ✅ Token efficiency as core design principle (Factory.ai, Anthropic research)
- ✅ Information architecture for machine consumption (not human narrative)
- ✅ Progressive disclosure patterns (TL;DR → Quick Ref → Deep Dive)
- ✅ Action-oriented language (imperatives outperform suggestive)
- ✅ Strategic concrete/abstract balance (examples for classification, principles for reasoning)

**Constraints:**
- ✅ **Zero information loss** - All critical rules preserved
- ✅ **Backwards compatibility** - Existing prompts continue working
- ✅ **Phased rollout** - Test each optimization before full deployment
- ✅ **Rollback capability** - Can revert if issues detected

### 1.2 Optimization Targets

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| **Total Tokens** | 74,536 | 12,858 | **-83%** |
| **AGENTS.md** | 57,378 | 500 | **-99%** (lazy-load) |
| **UNIFIED** | 6,318 | 4,800 | **-24%** |
| **CLAUDE.md** | 8,500 | 6,800 | **-20%** |
| **Supporting Files** | 2,340 | 1,758 | **-25%** |
| **Activation Time** | ~2-3 min | <1 min | **-66%** |

---

## 2. Content Reorganization Strategy

### 2.1 AGENTS.md Externalization (PRIMARY OPTIMIZATION)

**Current Problem:**
- 57,378 tokens (77% of total)
- Loaded in EVERY conversation
- Only used in ~5% of conversations (BMad commands)

**Strategy: Lazy-Load Protocol**

**Implementation:**

1. **Create Lazy-Load Trigger in CLAUDE.md/UNIFIED:**
   ```markdown
   ## BMad Method Integration (On-Demand Only)

   BMad workflows are loaded ONLY when explicitly invoked via slash commands.

   **DO NOT load AGENTS.md proactively** - it contains 57K tokens for specialized workflows.

   **To use BMad agents:** Type `/BMad:agents:bmad-master` (loads on first invocation)
   ```

2. **Add AGENTS.md Activation Notice:**
   ```markdown
   <!-- At top of AGENTS.md -->
   # AGENTS.md - BMad Method Workflows

   **LOAD PROTOCOL:** This file is loaded ONLY when user types `/BMad:agents:*` commands.

   **Token Cost:** 57,378 tokens - DO NOT load proactively!
   ```

3. **Update Slash Command Integration:**
   - Current: AGENTS.md always loaded
   - New: AGENTS.md loaded when SlashCommand tool invokes `/BMad:*`
   - Mechanism: Claude Code checks if AGENTS.md already in context, loads only if needed

**Benefits:**
- ✅ 56,878 tokens saved in 95% of conversations
- ✅ Zero functionality loss (still available when needed)
- ✅ No breaking changes (commands work identically)
- ✅ User experience unchanged

**Risks & Mitigation:**
- ⚠️  Risk: BMad commands slower on first invocation (loading delay)
- ✅ Mitigation: Add loading indicator "Loading BMad workflows..." (0.5-1 sec delay acceptable)

### 2.2 Single Source of Truth (SSoT) Matrix

**Eliminate duplication by designating authoritative sources:**

| Content | SSoT Location | Other Locations → Action |
|---------|---------------|--------------------------|
| **Approval Thresholds** | UNIFIED §APPROVAL LADDER | CLAUDE.md → Reference only |
| **Forbidden Imports** | quality-gates.yaml | UNIFIED/CLAUDE → Quick summary + reference |
| **Naming Conventions** | UNIFIED §NAMING CONVENTIONS | quality-gates.yaml → Validation rules only |
| **Project Root Policy** | CLAUDE.md §PROJECT ROOT | quality-gates.yaml → Validation only |
| **Workflow Selection** | UNIFIED §WORKFLOW MATRIX | quality-gates → Automation rules |
| **SessionStateManager** | CLAUDE.md §CRITICAL RULES | No duplication needed |

**Implementation Pattern:**

```markdown
<!-- In file without SSoT -->
## Quick Reference: Approval Thresholds

>100 lines OR >5 files → Ask approval

**For complete decision tree:** See UNIFIED §APPROVAL LADDER

<!-- DELETED: Full table duplication -->
```

**Estimated Savings:** 2,500 tokens from SSoT enforcement

### 2.3 Progressive Disclosure Architecture

**Current Problems:**
- TL;DR sections exist but still too long (5-10 min read)
- No clear navigation path from quick → medium → deep
- Deep sections buried, hard to find when needed

**New Architecture:**

```
📄 CLAUDE.md v4.0 Structure:
├── ⚡ ULTRA-TL;DR (30 sec, 5 bullet points)
├── 🔍 Quick Lookup Tables (2 min, scannable tables)
├── 🎯 Critical Rules (action-oriented imperatives)
├── 📚 Deep Dive (detailed explanations with escape hatches)
└── 🔗 References (external doc pointers)
```

**ULTRA-TL;DR Template (NEW):**

```markdown
## ⚡ ULTRA-TL;DR (30 Second Activation)

**5 Non-Negotiable Rules:**
1. **Files in root:** NO (except README, requirements, config)
2. **SessionStateManager:** ONLY access via SessionStateManager
3. **Approval gate:** >100 lines OR >5 files → Ask first
4. **No backwards compat:** Refactor in place (solo dev!)
5. **BMad Method:** Type `/BMad:agents:*` (loads on-demand, 57K tokens)

**Next:** See §🔍 Quick Lookup for instant answers
```

**Estimated Savings:** 800 tokens (TL;DR compression)

### 2.4 Table-Based Quick Reference Expansion

**Research Finding:** "Decision matrices outperform narrative conditionals" (Perplexity research)

**Expand Quick Lookup Tables:**

**Current:** 5 tables in CLAUDE.md
**Target:** 10 comprehensive tables covering all decision points

**New Tables to Add:**

| Table Name | Purpose | Token Efficiency |
|------------|---------|------------------|
| **Decision Tree Matrix** | "When X, do Y" for all common scenarios | Replaces 20 lines narrative with 5-line table |
| **Error Resolution Matrix** | Common errors → Solutions | Replaces troubleshooting section |
| **File Location Matrix** | File type → Required location → Forbidden locations | Already exists, expand |
| **Test Strategy Matrix** | Test type → When to run → Coverage target | New, replaces narrative |
| **Git Operations Matrix** | Command → Approval required? → Condition | Already exists |

**Table Format Standard:**

```markdown
| Situation | Required Action | Forbidden Action | Escalation | Reference |
|-----------|----------------|------------------|------------|-----------|
| Concise | Imperative verb | X Never do | When to ask | §Link |
```

**Estimated Savings:** 1,200 tokens (narrative → tables)

---

## 3. Token Optimization Techniques

### 3.1 Filler Language Elimination

**Pattern Detection & Removal:**

| Filler Pattern | Instances | Replacement | Savings |
|----------------|-----------|-------------|---------|
| "It's important to remember that..." | 17 | DELETE | ~180 tokens |
| "Please note that..." | 12 | DELETE | ~96 tokens |
| "You should be aware that..." | 9 | DELETE | ~81 tokens |
| "This is critical because..." | 23 | Merge into rule or DELETE | ~230 tokens |
| "Remember that..." | 14 | DELETE | ~84 tokens |

**Before/After Examples:**

```markdown
<!-- BEFORE (verbose) -->
It's important to remember that you should never place files in the project
root. This is critical because it violates our organization policy and makes
the codebase harder to maintain. Please note that there are some exceptions
to this rule, which you should be aware of.

<!-- AFTER (action-oriented) -->
**NO files in project root** (except: README, requirements, config)
```

**Estimated Total Savings:** 1,300 tokens

### 3.2 Action-Oriented Language Conversion

**Research Finding:** "Imperative language outperforms suggestive" (OpenAI, Anthropic 2024)

**Conversion Patterns:**

| Verbose Form | Token Cost | Action-Oriented | Token Cost | Savings |
|--------------|------------|-----------------|------------|---------|
| "You might consider asking clarifying questions" | 7 | "Ask clarifying questions" | 3 | 57% |
| "The agent should avoid making promises" | 6 | "Do not make promises" | 4 | 33% |
| "It would be beneficial to use SessionStateManager" | 7 | "Use SessionStateManager" | 2 | 71% |

**Systematic Conversion:**

1. Identify all suggestive constructions:
   - "You might consider..."
   - "It would be good to..."
   - "The agent should..."
   - "Try to..."

2. Convert to imperatives:
   - "Do X"
   - "Use Y"
   - "Never Z"

**Estimated Savings:** 800 tokens

### 3.3 Over-Explained Section Compression

**Target Sections:**

1. **CLAUDE.md §Lazy Import Pattern:**
   - Current: 45 lines with extensive examples
   - Target: 12-line table format
   - Savings: ~220 tokens

2. **UNIFIED §Vibe Coding Principles:**
   - Current: 190 lines with narrative
   - Target: 80 lines table-based catalog
   - Savings: ~800 tokens

3. **CLAUDE.md §Performance Context:**
   - Current: 60 lines historical detail
   - Target: 20-line status table
   - Savings: ~300 tokens

**Compression Template:**

```markdown
<!-- BEFORE: 45 lines narrative -->
The Lazy Import Pattern is used when circular imports are unavoidable...
[extensive explanation]

<!-- AFTER: 12 lines table -->
## Lazy Import Pattern (Circular Dependency Fix)

| When to Use | Example | Why |
|-------------|---------|-----|
| Circular import unavoidable | `from module import Class` inside function | Defer import |

**ONE codebase example:** session_state.py:205 (DEF-73)
```

**Total Estimated Savings:** 1,320 tokens

### 3.4 Historical Context Archival

**Move to Dedicated Files:**

| Content | Current Location | Move To | Savings |
|---------|-----------------|---------|---------|
| Enterprise architecture history | CLAUDE.md | Already archived | 200 tokens |
| Validation system evolution | CLAUDE.md | docs/architectuur/ | 150 tokens |
| Multiagent workflow lessons | UNIFIED | docs/methodologies/ | 150 tokens |

**Replacement Pattern:**

```markdown
<!-- BEFORE: 30-line historical explanation -->
The enterprise architecture documents were archived because...
[detailed rationale]

<!-- AFTER: 3-line pointer -->
**Enterprise docs:** Archived to `docs/archief/2025-11-enterprise-architecture-docs/`
(Reason: Misalignment with solo dev reality)
```

**Total Estimated Savings:** 500 tokens

---

## 4. Clarity Improvement Strategies

### 4.1 Conflict Resolution Framework

**Add to ALL instruction files (YAML frontmatter):**

```yaml
---
instruction_metadata:
  file: UNIFIED_INSTRUCTIONS.md
  version: 2.0
  precedence: 1  # 1=highest, 5=lowest
  last_updated: 2025-01-18
  overrides: []
  overridden_by: []
  conflicts_detected: []
---
```

**Precedence Table (add to UNIFIED TL;DR):**

```markdown
## 🎯 Instruction Precedence (Conflict Resolution)

| Rank | File | When to Use | Overrides |
|------|------|-------------|-----------|
| 1 | UNIFIED | Always (cross-project rules) | All others |
| 2 | CLAUDE.md | DefinitieAgent-specific | quality-gates, mappings, AGENTS |
| 3 | quality-gates.yaml | Validation automation | mappings, AGENTS |
| 4 | agent-mappings.yaml | Tool translation | AGENTS |
| 5 | AGENTS.md | BMad workflows ONLY | None (specialized) |

**IF conflict detected:** Follow higher rank, report in notes.
```

**Token Cost:** +150 tokens (but eliminates ambiguity)

### 4.2 Decision Tree Simplification

**Problem:** Multiple decision points scattered across files

**Solution:** Unified Decision Tree at UNIFIED §TL;DR

```markdown
## 🎯 Master Decision Tree

START: User request
  ↓
Q1: Is request clear (WHAT/WHY/WHERE)?
├─ NO → Ask clarifying questions → Return to START
└─ YES → Continue to Q2

Q2: Is this >100 lines OR >5 files OR network call OR schema change?
├─ YES → Show structure + ask approval → WAIT for confirmation → Q3
└─ NO → Continue to Q3

Q3: Which workflow?
├─ Research/investigation → ANALYSIS workflow
├─ <50 LOC, known fix → HOTFIX workflow
├─ New feature → FULL_TDD workflow
└─ Code improvement → REFACTOR workflow

Q4: Forbidden pattern detected? (Check quality-gates.yaml)
├─ YES → STOP → Inform user → Suggest alternative
└─ NO → Proceed with implementation
```

**Token Cost:** +200 tokens (but replaces 500 tokens scattered guidance)
**Net Savings:** 300 tokens

### 4.3 Example Quality Improvement

**Research Finding:** "Concrete examples outperform abstract principles for classification tasks"

**Strategy: ONE excellent example > THREE mediocre examples**

**Current Pattern:**
```markdown
<!-- 3 examples, all variations of same concept -->
Example 1: [scenario A]
Example 2: [scenario A with slight variation]
Example 3: [scenario A with different variable names]
```

**New Pattern:**
```markdown
<!-- 1 comprehensive example with clear anti-pattern -->
✅ CORRECT: [best practice with code]
❌ WRONG: [anti-pattern with explanation]
📍 REAL: [actual codebase reference, e.g., session_state.py:205]
```

**Estimated Savings:** 400 tokens (reduce example count, increase quality)

---

## 5. Cross-Referencing Strategy

### 5.1 Reference Syntax Standard

**Unified Cross-Reference Format:**

```markdown
<!-- Within same file -->
See §Section Name below

<!-- To other instruction file -->
→ UNIFIED §APPROVAL LADDER for complete thresholds

<!-- To project documentation -->
→ docs/architectuur/ARCHITECTURE.md for system design

<!-- To codebase -->
→ src/ui/session_state.py:205 (implementation example)
```

**Benefits:**
- ✅ Consistent syntax (easier to parse)
- ✅ Grep-able (find all references to a section)
- ✅ Reduces duplication (point instead of copy)

### 5.2 Reference Density Optimization

**Problem:** Some sections over-reference, others under-reference

**Optimization Rules:**
1. **Core sections (TL;DR):** Minimal references (self-contained)
2. **Quick Lookup Tables:** Medium references (escape hatches)
3. **Deep Dive sections:** High references (connect to other resources)

**Example:**

```markdown
## ⚡ TL;DR
[Self-contained essentials, NO references]

## 🔍 Quick Lookup
| Scenario | Action | More Info |
|----------|--------|-----------|
| >100 lines | Ask approval | →UNIFIED §APPROVAL LADDER |

## 📚 Deep Dive: Approval Protocol
[Detailed explanation with references to examples, other docs, codebase]
```

---

## 6. Implementation Techniques

### 6.1 Compression Without Information Loss

**Technique: Table-Based Dense Encoding**

**Before (narrative):**
```markdown
When you encounter a situation where the user has made a request that involves
changing more than 100 lines of code, or when the change affects more than 5
different files, you should first show the user a structure of what you're
planning to change and ask for their approval before proceeding. This is
important because large changes have higher risk of introducing bugs.
```
**Tokens:** ~68

**After (table):**
```markdown
| Change Size | Action | Rationale |
|-------------|--------|-----------|
| >100 lines OR >5 files | Show structure + ask approval | High risk |
```
**Tokens:** ~22
**Savings:** 68% reduction

### 6.2 Semantic Chunking

**Technique: Natural Topic Boundaries**

**Current:** Sections split by arbitrary line counts
**New:** Sections split by semantic topics with clear boundaries

**Example Organization:**

```markdown
## 🎯 CORE PRINCIPLES (Semantic Chunk 1: Philosophy)
[Complete topic: what guides all decisions]

## 🚫 FORBIDDEN PATTERNS (Semantic Chunk 2: Constraints)
[Complete topic: what never to do]

## ✅ APPROVED PATTERNS (Semantic Chunk 3: Best Practices)
[Complete topic: recommended approaches]
```

### 6.3 Modular Component Design

**Technique: Reusable Prompt Components**

**Create Shared Modules:**

```markdown
<!-- File: .claude/modules/approval-gate.md -->
# Approval Gate Module v1.0

>100 lines OR >5 files → Ask approval

[Reusable detailed rules]

<!-- In CLAUDE.md -->
Approval rules: @@@module:approval-gate@@@

<!-- In UNIFIED -->
Approval rules: @@@module:approval-gate@@@
```

**Benefits:**
- Single source of truth
- Version controlled modules
- Easy to update globally

**Note:** Check if Claude Code supports module referencing (from Context7 research: prompt composability exists in Langfuse SDK)

---

## 7. Integration Strategy

### 7.1 Backward Compatibility Plan

**Ensure Existing Prompts Continue Working:**

1. **Maintain Key Section Headers:**
   - Existing prompts may reference "§APPROVAL LADDER"
   - Keep headers stable, optimize content

2. **Add Redirect Comments:**
   ```markdown
   <!-- DEPRECATED: §Old Section Name -->
   <!-- NOW: §New Section Name -->
   ```

3. **Gradual Migration:**
   - Phase 1: Add optimized sections alongside old
   - Phase 2: Mark old sections deprecated
   - Phase 3: Remove old sections after 2-week validation

### 7.2 Version Control Strategy

**Semantic Versioning:**

- CLAUDE.md: v3.0 → v4.0 (major reorganization)
- UNIFIED: v3.0 → v2.0 (yes, downgrade number to match optimization goals)
  - Actually: v3.0 → v3.1 (minor optimization, no breaking changes)
- quality-gates.yaml: v1.0 → v1.1 (minor additions)
- agent-mappings.yaml: v1.0 → v1.1 (minor additions)

**Git Workflow:**

```bash
# Create optimization branch
git checkout -b feature/instruction-files-optimization

# Commit each file separately for granular rollback
git commit -m "opt(AGENTS): implement lazy-load protocol (-56K tokens)"
git commit -m "opt(UNIFIED): deduplicate approval thresholds (-1.5K tokens)"
git commit -m "opt(CLAUDE): compress v3.0 → v4.0 (-1.7K tokens)"

# Validation before merge
pytest tests/integration/test_instruction_compliance.py
```

### 7.3 Rollback Procedures

**IF Optimization Causes Issues:**

```bash
# Immediate rollback (per file)
git checkout main -- CLAUDE.md  # Rollback CLAUDE.md only

# Full rollback
git revert <commit-hash>

# Incremental rollback
# Keep AGENTS.md externalization (56K savings)
# Revert other optimizations if problematic
```

**Rollback Triggers:**
- Agent fails to follow critical rules
- Test suite regression
- User reports degraded performance
- Token budget exceeded (paradoxical - optimization broke something)

---

## 8. Success Metrics

### 8.1 Primary Metrics

| Metric | Baseline | Target | Measurement Method |
|--------|----------|--------|-------------------|
| **Total Tokens** | 74,536 | 12,858 | Sum of optimized files |
| **Activation Time** | 2-3 min | <1 min | User feedback |
| **Comprehension Score** | TBD | >9/10 | Clarity evaluation (5 metrics) |
| **Error Rate** | Baseline | <50% of baseline | Track instruction violations |
| **User Satisfaction** | Baseline | >Baseline | Survey after 2 weeks |

### 8.2 Secondary Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Reference Lookup Time** | <10 sec | Time to find info in Quick Lookup |
| **Conflict Resolution Time** | <30 sec | Time to determine precedence |
| **Duplication %** | <5% | Automated duplication detection |
| **Filler Language %** | <2% | Automated pattern detection |

### 8.3 Validation Test Scenarios

**Create Test Suite:**

1. **Approval Gate Test:**
   - Scenario: 150-line refactor request
   - Expected: Agent asks approval BEFORE coding
   - Pass: Agent shows structure, waits for confirmation

2. **Forbidden Import Test:**
   - Scenario: Import streamlit in services/
   - Expected: Agent refuses, suggests alternative
   - Pass: Agent blocks import, references async_bridge

3. **SessionStateManager Test:**
   - Scenario: Need to access session state
   - Expected: Agent uses SessionStateManager only
   - Pass: No direct st.session_state access

4. **Project Root Test:**
   - Scenario: Create test_foo.py in root
   - Expected: Agent refuses, moves to tests/
   - Pass: File created in tests/ subdirectory

5. **BMad Command Test:**
   - Scenario: User types `/BMad:agents:bmad-master`
   - Expected: AGENTS.md loads (first invocation only)
   - Pass: BMad agent activates, functionality preserved

---

## 9. Risk Assessment

### 9.1 High Risk Items

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **AGENTS.md lazy-load breaks BMad** | LOW | HIGH | Test BMad commands extensively |
| **Deduplication removes critical info** | MEDIUM | HIGH | Manual review + diff validation |
| **Token count estimations wrong** | MEDIUM | MEDIUM | Actual measurement after optimization |
| **Agent confusion from reorganization** | LOW | MEDIUM | Gradual migration, keep headers stable |

### 9.2 Mitigation Strategies

**For AGENTS.md Lazy-Load:**
- ✅ Test ALL BMad slash commands before deployment
- ✅ Add explicit loading indicators
- ✅ Keep rollback script ready
- ✅ Monitor first 50 BMad invocations post-deployment

**For Deduplication:**
- ✅ Create "removed content log" (track what was deleted, why)
- ✅ User validation: "Was this info critical?"
- ✅ A/B test: 50% conversations with old version, 50% with new

**For Token Estimation:**
- ✅ Actual token count BEFORE and AFTER using tiktoken library
- ✅ Account for markdown formatting overhead
- ✅ Measure in Claude Code actual context

---

## 10. Next Steps: Implementation Roadmap

**Proceed to:**

1. ✅ **Implementation Roadmap** (detailed phased approach)
   - Phase 1: AGENTS.md externalization (quick win)
   - Phase 2: UNIFIED deduplication
   - Phase 3: CLAUDE.md v4.0 compression
   - Phase 4: Supporting files optimization

2. ✅ **Generate Optimized File Versions**
   - CLAUDE.md v4.0 (with ULTRA-TL;DR, expanded tables)
   - UNIFIED v3.1 (deduplicated, action-oriented)
   - Updated quality-gates.yaml
   - Updated agent-mappings.yaml

3. ✅ **Validation Test Suite**
   - 5 core scenarios (approval, forbidden, session, root, BMad)
   - Automated test execution
   - Success criteria definition

4. ✅ **Executive Summary & Deliverables Package**
   - 1-page executive summary
   - Change log with rationale
   - Migration guide
   - Rollback procedures

---

**Strategy Design Complete. Ready for Implementation Roadmap.**
