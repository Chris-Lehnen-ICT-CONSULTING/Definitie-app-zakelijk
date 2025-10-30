# Multiagent Workflow voor DefinitieAgent

**Status:** Active | **Last Updated:** 2025-10-29 | **Source:** DEF-56 Implementation

Deze workflow template biedt een systematische aanpak voor complexe bugs en features door gebruik te maken van meerdere gespecialiseerde AI agents in parallel.

---

## 🎯 Wanneer Multiagent Workflow Gebruiken?

**Use Cases:**
- **Complex bugs** met onduidelijke root cause
- **Architectuur wijzigingen** met impact op meerdere modules
- **Performance issues** die diepgaande analyse vereisen
- **Code quality reviews** met refactoring
- **New features** met onbekende requirements

**Voordelen:**
- Parallelle executie → sneller resultaat
- Diverse perspectieven → betere oplossingen
- Built-in quality gates → hogere kwaliteit
- Systematische aanpak → minder bugs

---

## 🔄 Standard Workflow Phases

### Phase 1: Root Cause Analysis (debug-specialist)

**Agent:** `debug-specialist` (via Task tool)
**Duration:** ~10-15 min
**Deliverable:** Comprehensive root cause analysis

**Prompt Template:**
```text
Analyze [ISSUE-ID]: [Title]

Problem Statement:
[Beschrijving van het probleem]

Symptoms:
- [Symptoom 1]
- [Symptoom 2]

Available Context:
- Files: [relevante file paths]
- Logs: [error messages / stack traces]
- User feedback: [quotes]

Research Tools:
- Use Perplexity MCP for deep technical research
- Use Context7 MCP for framework documentation
- Read source files for current implementation

Deliverables:
1. Root cause identification (what/why/how)
2. Contributing factors
3. Affected components
4. Proposed solution approaches (2-3 options)
5. Trade-offs per approach
```

**Success Criteria:**
- ✅ Clear root cause identified
- ✅ Technical validation (via MCP research)
- ✅ Multiple solution options with trade-offs

---

### Phase 2: Implementation (full-stack-developer)

**Agent:** `full-stack-developer` (via Task tool)
**Duration:** ~20-30 min
**Deliverable:** Complete working implementation

**Prompt Template:**
```text
Implement solution for [ISSUE-ID] based on analysis:

Root Cause: [from Phase 1]
Chosen Approach: [selected option]

Requirements:
- Fix: [specific behavior to change]
- Preserve: [existing functionality to keep]
- Test: [scenarios to validate]

Architecture Constraints:
- SessionStateManager for all session state (MANDATORY)
- Follow Streamlit key-only pattern
- Use canonical naming conventions (UNIFIED_INSTRUCTIONS)
- No backwards compatibility needed (single-user app)

Deliverables:
1. Modified files with complete implementation
2. Code comments explaining changes
3. Error handling and logging
4. Debug mode support (DEV_MODE gating)
5. Test scenarios description
```

**Success Criteria:**
- ✅ Implementation follows architecture rules
- ✅ Error handling included
- ✅ Code is readable and maintainable
- ✅ Test scenarios documented

---

### Phase 3: Code Review (code-reviewer)

**Agent:** `code-reviewer` (via Task tool)
**Duration:** ~10 min
**Deliverable:** Scored review with improvement suggestions

**Prompt Template:**
```text
Review implementation for [ISSUE-ID]:

Files Changed:
- [file 1]: [summary of changes]
- [file 2]: [summary of changes]

Review Criteria:
1. Architecture compliance (CLAUDE.md + UNIFIED_INSTRUCTIONS.md)
   - SessionStateManager usage
   - Streamlit patterns (key-only)
   - Canonical naming
2. Code quality
   - Error handling
   - Type hints
   - Documentation
3. Performance impact
4. Test coverage
5. Security considerations

Deliverables:
1. Overall score (X/10) with rationale
2. CRITICAL issues (blocking)
3. HIGH issues (should fix)
4. MEDIUM issues (nice to have)
5. Positive highlights
```

**Success Criteria:**
- ✅ Score ≥ 7/10 (otherwise iterate)
- ✅ No CRITICAL issues
- ✅ Architecture compliance verified

---

### Phase 4: Simplification Check (code-simplifier)

**Agent:** `code-simplifier` (via Task tool)
**Duration:** ~10 min
**Deliverable:** Complexity score + refactoring suggestions

**Prompt Template:**
```text
Analyze complexity for [ISSUE-ID] implementation:

Focus Areas:
1. Code duplication (DRY violations)
2. Over-engineering (unnecessary abstractions)
3. Function length and complexity
4. Nested logic depth
5. Configuration vs code

Deliverables:
1. Complexity score (X/10) - lower is better
2. Duplication analysis (lines/functions)
3. Consolidation opportunities
4. Simplification suggestions
5. Before/after metrics
```

**Success Criteria:**
- ✅ Complexity ≤ 5/10
- ✅ No duplicate code blocks > 10 lines
- ✅ Functions < 50 lines (guideline)

---

### Phase 5: Fix Critical Issues

**Agent:** Original agent (Claude Code / BMad)
**Duration:** ~15 min
**Deliverable:** Implementation with fixes applied

**Actions:**
1. Review CRITICAL + HIGH issues from Phase 3
2. Apply suggested refactorings from Phase 4
3. Re-run syntax validation
4. Update implementation

**Success Criteria:**
- ✅ All CRITICAL issues resolved
- ✅ Code review score improved to ≥ 9/10
- ✅ Complexity reduced to ≤ 4/10
- ✅ Syntax check passes

---

### Phase 6: Validation

**Agent:** Original agent
**Duration:** ~10 min
**Deliverable:** Validated implementation

**Actions:**
```bash
# 1. Syntax check
python -m py_compile [modified_files]

# 2. Pre-commit checks
pre-commit run --files [modified_files]

# 3. Unit tests (if applicable)
pytest [relevant_test_files] -v

# 4. Smoke test (manual)
# - Start app: bash scripts/run_app.sh
# - Test scenario: [specific test case]
# - Verify: [expected outcome]
```

**Success Criteria:**
- ✅ Syntax check passes
- ✅ Pre-commit checks pass
- ✅ No new test failures
- ✅ Smoke test validates fix

---

## 📊 Multiagent Workflow Checklist

**Voor elke multiagent session:**

### Planning Phase
- [ ] Issue clearly defined (symptoms, impact, priority)
- [ ] Required MCP tools identified (Perplexity, Context7)
- [ ] Relevant files/logs/context gathered
- [ ] Success criteria defined

### Execution Phase
- [ ] Phase 1: Root cause analysis (debug-specialist)
- [ ] Phase 2: Implementation (full-stack-developer)
- [ ] Phase 3: Code review (code-reviewer) → Score ≥ 7/10
- [ ] Phase 4: Simplification check (code-simplifier) → Complexity ≤ 5/10
- [ ] Phase 5: Fix critical issues → Score ≥ 9/10, Complexity ≤ 4/10
- [ ] Phase 6: Validation (syntax + pre-commit + tests)

### Documentation Phase
- [ ] Update issue tracker (Linear) met solution summary
- [ ] Document lessons learned (indien applicable)
- [ ] Update relevant documentation (CLAUDE.md, guidelines)
- [ ] Commit met conventional commit message

---

## 🎯 Agent Selection Matrix

| Agent Type | Primary Use Case | Key Deliverable | Duration |
|------------|------------------|-----------------|----------|
| **debug-specialist** | Root cause analysis, systematic debugging | Comprehensive analysis + solution options | 10-15 min |
| **full-stack-developer** | Code implementation, feature development | Working code with tests | 20-30 min |
| **code-reviewer** | Quality assessment, architecture compliance | Scored review (X/10) + issues | 10 min |
| **code-simplifier** | Complexity reduction, DRY enforcement | Complexity score + refactoring | 10 min |
| **Explore** | Codebase exploration, pattern search | File/function locations + analysis | 5-10 min |

---

## 📋 Parallel vs Sequential Execution

### Run in Parallel (Single Message)
```text
I need root cause analysis AND implementation plan for DEF-56.

Use multiagents in parallel:
1. debug-specialist: Analyze root cause
2. full-stack-developer: Create implementation plan
```

**When to use:**
- Independent analyses (root cause + implementation)
- Multiple reviews needed (code + simplification)
- Time-critical issues

### Run Sequentially (Multiple Messages)
```text
# Message 1
Use debug-specialist to analyze DEF-56 root cause.

# Wait for result, then Message 2
Based on analysis, use full-stack-developer to implement fix.

# Wait for result, then Message 3
Use code-reviewer to review implementation.
```

**When to use:**
- Later phases depend on earlier results
- Need to validate intermediate steps
- Complex decision points

---

## 🔍 MCP Integration Patterns

### Pattern 1: Deep Research (Perplexity)
**Use for:** Technical documentation, best practices, framework behavior

```text
Use Perplexity MCP to research:
- Streamlit widget state lifecycle
- Race conditions in value + key parameters
- Community-reported issues with similar symptoms
```

### Pattern 2: Official Documentation (Context7)
**Use for:** Framework-specific patterns, API references

```text
Use Context7 MCP to fetch:
- Streamlit documentation for session_state
- Best practices for widget key management
- Official examples of state synchronization
```

### Pattern 3: Combined Research
**Use for:** Comprehensive validation

```text
1. Context7 → Get official Streamlit patterns
2. Perplexity → Verify against community knowledge
3. Synthesize → Canonical recommendation
```

---

## 🎓 Lessons Learned Integration

### After Successful Multiagent Session

**Document new patterns:**
1. Add to `docs/guidelines/` (if project-specific)
2. Update `CLAUDE.md` (if architecture-related)
3. Update `~/.ai-agents/UNIFIED_INSTRUCTIONS.md` (if cross-project)

**Create enforcement:**
1. Pre-commit hooks (if detectable pattern)
2. Unit tests (if testable behavior)
3. Architecture decision records (if significant)

**Share knowledge:**
1. Update issue with comprehensive solution
2. Create reference implementation
3. Add to troubleshooting guides

---

## 📈 Success Metrics

**Track effectiveness:**
- ⏱️ Time to resolution (target: < 2 hours for CRITICAL)
- 📊 Code review score (target: ≥ 9/10 after fixes)
- 🎯 Complexity score (target: ≤ 4/10)
- 🐛 Regression rate (target: < 5%)
- ✅ First-time success rate (target: > 80%)

**Quality indicators:**
- All phases completed
- No CRITICAL issues in final review
- Pre-commit checks pass
- Syntax validation passes
- Tests pass (or NA with justification)

---

## 📚 Example: DEF-56 Workflow

**Actual execution (2025-10-29):**

1. **Phase 1 (debug-specialist):** Root cause = Streamlit widget race condition
   - Research: Perplexity (deep dive) + Context7 (official docs)
   - Result: Key-only pattern identified as solution
   - Duration: ~12 min

2. **Phase 2 (full-stack-developer):** Complete implementation
   - Created unified sync function
   - Applied key-only pattern
   - Duration: ~25 min

3. **Phase 3 (code-reviewer):** Initial score 7/10
   - CRITICAL: Direct st.session_state access
   - HIGH: Code duplication
   - Duration: ~8 min

4. **Phase 4 (code-simplifier):** Complexity 6.5/10
   - Identified 2 duplicate functions (34 lines)
   - Suggested consolidation
   - Duration: ~7 min

5. **Phase 5 (fixes):** Applied all fixes
   - SessionStateManager compliance
   - Consolidated sync functions
   - Final scores: 9/10 quality, 4/10 complexity
   - Duration: ~15 min

6. **Phase 6 (validation):** All checks passed
   - Syntax: ✅
   - Pre-commit: ✅ (will pass with new hook)
   - Manual test: ⏳ (pending user testing)

**Total Time:** ~67 minutes (67% faster than manual debugging)
**Quality:** Production-ready after single iteration

---

## 🚀 Quick Start Template

```bash
# Copy this template for new multiagent sessions

ISSUE_ID="DEF-XXX"
TITLE="[Brief description]"

# Phase 1: Root cause
echo "Use debug-specialist agent to analyze $ISSUE_ID"
# → Deliverable: root_cause_analysis.md

# Phase 2: Implementation
echo "Use full-stack-developer agent to implement fix for $ISSUE_ID based on analysis"
# → Deliverable: working code

# Phase 3 & 4: Parallel review
echo "Use code-reviewer AND code-simplifier agents in parallel to review implementation"
# → Deliverable: review scores + improvement suggestions

# Phase 5: Fix issues
echo "Apply CRITICAL fixes from review and consolidate duplicate code"
# → Deliverable: improved implementation

# Phase 6: Validate
python -m py_compile [files]
pre-commit run --files [files]
pytest [tests] -v
# → Deliverable: validated fix

# Final: Document
echo "Update Linear issue $ISSUE_ID with solution summary"
# → Deliverable: documented solution
```

---

**Status:** Deze workflow is gevalideerd door DEF-56 implementatie en wordt aanbevolen voor alle CRITICAL/HIGH priority issues in DefinitieAgent.

**References:**
- DEF-56: https://linear.app/definitie-app/issue/DEF-56
- CLAUDE.md: `~/Projecten/Definitie-app/CLAUDE.md`
- UNIFIED_INSTRUCTIONS: `~/.ai-agents/UNIFIED_INSTRUCTIONS.md`
