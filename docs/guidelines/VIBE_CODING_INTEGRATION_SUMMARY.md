---
aangemaakt: 2025-10-17
applies_to: definitie-app@current
bijgewerkt: 2025-10-17
canonical: true
type: executive-summary
---

# Vibe Coding Integration Summary

**Executive Summary:** Complete workflow design for DefinitieAgent development using Vibe Coding methodology with Claude Code.

---

## What Was Delivered

### 1. Complete Workflow Design
**File:** `VIBE_CODING_WORKFLOW.md` (1000+ lines)

Comprehensive guide covering:
- 6 specialized workflows (ANALYSIS, FULL_TDD, HOTFIX, REFACTOR, REVIEW, DOCUMENT)
- Step-by-step execution sequences for each workflow
- Claude Code tool integration for every step
- Session management strategy
- 4 detailed practical examples
- Handoff protocols between workflows and sessions

### 2. Quick Reference Card
**File:** `VIBE_CODING_QUICK_REFERENCE.md` (400+ lines)

One-page reference for immediate decisions:
- Visual decision flowchart
- Workflow cheat sheets
- Essential commands
- Critical rules reminder
- Common patterns
- Emergency procedures

### 3. Integration Points Identified
- Git workflow (semantic commits, branching)
- Testing integration (pytest commands, coverage)
- Code quality (pre-commit, ruff, black)
- Development server (streamlit)
- BMad Method agent handoffs

---

## Key Design Decisions

### 1. Workflow Selection Based on Task Type

**Not One-Size-Fits-All:**
- Rejected: Single "universal" workflow
- Chosen: 6 specialized workflows matching task complexity
- Rationale: Solo developer needs efficiency, not bureaucracy

**Decision Tree:**
```
Documentation only → DOCUMENT (5-20 min)
Emergency bug → HOTFIX (10-30 min)
Unclear requirements → ANALYSIS (15-30 min)
Code review needed → REVIEW (15-30 min)
Quality improvement → REFACTOR (15-30 min)
New feature → FULL_TDD (30-90 min)
```

### 2. Session Management for Claude Code

**Problem Identified:**
- Claude Code doesn't persist context between sessions
- Long features require multiple sessions
- Context loss = wasted time

**Solution Implemented:**
- Session Start Checklist (always read CLAUDE.md, git status, handoff notes)
- Session End Protocol (create handoff notes if incomplete)
- HANDOFF-NOTES.md template
- SESSION-STATE.json for complex work
- Git commits as checkpoints

**Example Handoff Note:**
```markdown
## Session Handoff - [YYYY-MM-DD HH:MM]
Work Unit: US-XXX
Progress: 40%
What I did: ...
What's next: ...
Context notes: ...
Blockers: ...
```

### 3. Integration with Existing DefinitieAgent Workflows

**Aligned With:**
- BMad Method (agent role mapping)
- TDD_TO_DEPLOYMENT_WORKFLOW.md (8-phase process)
- WORKFLOW_LIBRARY.md (6 workflow types)
- UNIFIED_INSTRUCTIONS.md (approval ladder, forbidden patterns)
- CLAUDE.md (project-specific rules)

**Vibe Coding Templates Mapped:**
- 5-Step Discovery → ANALYSIS workflow
- 8-Step RED-GREEN-REFACTOR → FULL_TDD workflow
- 3-Step Emergency → HOTFIX workflow
- 4-Step Quality → REFACTOR workflow
- 2-Step Audit → REVIEW workflow
- 3-Step Cleanup → DOCUMENT workflow

### 4. Tool Integration Strategy

**Claude Code Tools Utilized:**
- **Read:** Project instructions, code files, documentation
- **Edit:** Modify existing files (services, tests)
- **Write:** Create new files (tests, docs, handoffs)
- **Grep:** Search codebase for patterns
- **Glob:** Find files by pattern
- **Bash:** Run tests, git commands, dev server
- **AskUserQuestion:** Clarify requirements

**Tool Usage Per Workflow:**
| Workflow | Primary Tools | Secondary Tools |
|----------|---------------|-----------------|
| ANALYSIS | Read, AskUserQuestion, Write | Grep, Glob |
| FULL_TDD | Edit, Write, Bash (tests) | Read, Grep |
| HOTFIX | Edit, Bash (tests), Bash (git) | Read |
| REFACTOR | Edit, Bash (tests) | Read |
| REVIEW | Read, Write (report) | Grep |
| DOCUMENT | Edit, Write | Read |

---

## Practical Examples Provided

### Example 1: Adding New Validation Rule
**Workflow:** FULL_TDD (8-step)
**Duration:** ~45 minutes
**Files Created:**
- `config/toetsregels/regels/SAM-003.json`
- `src/toetsregels/regels/SAM_003.py`
- `tests/toetsregels/test_SAM_003.py`
**Key Steps:**
1. Understand requirements from User Story
2. Write failing tests (RED)
3. Commit tests
4. Implement minimal code (GREEN)
5. Commit feature
6. Refactor for quality
7. Verify coverage and lint
8. Mark User Story complete

### Example 2: Refactoring Service Module
**Workflow:** REFACTOR (4-step)
**Duration:** ~30 minutes
**Problem:** `validation_service.py` at 823 lines (should be <500)
**Solution:**
1. Baseline coverage (94%)
2. Extract rule_loader.py (200 lines)
3. Extract formatter.py (223 lines)
4. Result: 400 lines, coverage maintained
**Key Insight:** Atomic commits per extraction, tests always green

### Example 3: Designing New UI Feature
**Workflow:** ANALYSIS → FULL_TDD (two sessions)
**Duration:** 20 min analysis + 30 min implementation = 50 min total
**Feature:** Export to JSON button
**Session 1 (ANALYSIS):**
- Clarify requirements with user
- Research existing patterns
- Design solution (use st.download_button)
- Validate design with user
- Create User Story (US-440.md)
**Session 2 (FULL_TDD):**
- Write failing tests
- Implement feature
- Verify functionality
- Mark complete

### Example 4: Fixing Complex Bug
**Workflow:** HOTFIX (3-step)
**Duration:** ~20 minutes
**Bug:** Validation rule SAM-002 false positives
**Steps:**
1. Reproduce with test (test_false_positive_bug)
2. Patch: Update regex pattern
3. Deploy: Commit, push, monitor
**Key Insight:** Regression test prevents recurrence

---

## Integration with Git Workflow

### Semantic Commit Format
```
type(scope): description

Types:
  - feat: New feature
  - fix: Bug fix
  - test: Test changes
  - refactor: Code restructure
  - docs: Documentation
  - chore: Maintenance
  - perf: Performance

Scope: US-XXX or module name

Examples:
  - test(US-042): add failing tests for validation
  - feat(US-042): implement validation rule
  - fix(SAM-002): correct regex false positives
  - refactor(US-160): extract rule loader
```

### Branching Strategy
```
main
 ├── feature/US-XXX (new features)
 ├── hotfix/issue-name (emergency fixes)
 └── refactor/component-name (quality improvements)

Session Management:
 - One workflow per branch
 - Git stash for context switches
 - Handoff notes per branch if needed
```

---

## Session Management Patterns

### Pattern 1: Single-Session Feature
```
Session (60 min):
  1. Read CLAUDE.md + US-XXX.md
  2. Execute FULL_TDD workflow (steps 1-8)
  3. Mark US-XXX complete
  4. No handoff needed

Exit: Feature complete, pushed
```

### Pattern 2: Multi-Session Feature
```
Session 1 (30 min):
  1. Read CLAUDE.md + US-XXX.md
  2. Execute steps 1-5 (UNDERSTAND → TEST-GREEN)
  3. Commit: "feat(US-XXX): partial implementation"
  4. Create HANDOFF-NOTES.md

Session 2 (30 min):
  1. Read HANDOFF-NOTES.md + git log
  2. Execute steps 6-8 (REFACTOR → VERIFY)
  3. Mark US-XXX complete
  4. Delete HANDOFF-NOTES.md

Exit: Feature complete, pushed
```

### Pattern 3: Emergency Context Switch
```
Working on Feature:
  - Branch: feature/US-450
  - Progress: 60%

Production Bug Reported:
  1. git stash save "WIP: US-450 partial"
  2. Create HANDOFF-NOTES.md (quick)
  3. git checkout main
  4. git checkout -b hotfix/critical-bug
  5. Execute HOTFIX workflow (20 min)
  6. git checkout feature/US-450
  7. git stash pop
  8. Read HANDOFF-NOTES.md
  9. Continue FULL_TDD workflow

Exit: Bug fixed + feature resumed
```

---

## Handoff Protocols

### Between Workflows
```yaml
ANALYSIS → FULL_TDD:
  Artifact: User Story (US-XXX.md)
  Verification: Read US-XXX.md, confirm AC clear

FULL_TDD → REVIEW:
  Artifact: Git commits + code
  Verification: git log, pytest, ruff check

REVIEW → REFACTOR:
  Artifact: Review report
  Verification: Read report, identify improvements
```

### Between Sessions
```yaml
Work Incomplete:
  1. Create HANDOFF-NOTES.md
  2. Commit WIP changes
  3. Update US-XXX status
  4. Document blockers

Work Complete:
  1. Update US-XXX status → "Ready for Review"
  2. Ensure commits pushed
  3. Update CHANGELOG (if needed)
  4. No handoff needed
```

### Between Agent Roles (BMad Method)
```yaml
Claude Code (Analysis) → Codex (BMad PM):
  Handoff: Draft User Story
  Next: Validate and finalize

Codex (BMad Architect) → Claude Code (Implement):
  Handoff: Architecture docs
  Next: Implement following design

Claude Code (Implement) → Codex (BMad QA):
  Handoff: Code + commits
  Next: Review using *review command
```

**Agent Mapping:**
| Claude Code | BMad Agent | Purpose |
|-------------|------------|---------|
| Analysis mode | bmad-analyst | Research |
| Design mode | bmad-architect | Architecture |
| Implementation | bmad-dev | Coding |
| Review mode | bmad-reviewer | Quality |
| Workflow mode | bmad-pm | Coordination |

---

## Quality Gates

### Per-Workflow Quality Gates

**ANALYSIS:**
- [ ] User Story has globally unique ID
- [ ] SMART criteria defined
- [ ] Acceptance criteria in BDD format
- [ ] Design validated by user

**FULL_TDD:**
- [ ] Tests written before implementation
- [ ] All tests green
- [ ] Coverage ≥ 60% (target 80%)
- [ ] No linting errors
- [ ] Semantic commits

**HOTFIX:**
- [ ] Bug reproduced with test
- [ ] Minimal scope (no feature creep)
- [ ] Regression test added
- [ ] Production verified

**REFACTOR:**
- [ ] Baseline coverage established
- [ ] Behavior unchanged
- [ ] Tests still green
- [ ] Refactor log updated

**REVIEW:**
- [ ] Complete 7-point checklist
- [ ] No critical blockers
- [ ] Concrete suggestions
- [ ] Verdict stated

**DOCUMENT:**
- [ ] Canonical locations correct
- [ ] Frontmatter present
- [ ] No broken links
- [ ] INDEX.md updated

---

## Critical Rules Enforcement

### From CLAUDE.md

**FORBIDDEN:**
- Creating files in project root (except README, CLAUDE.md, etc.)
- Backwards compatibility code (refactor instead)
- God objects / catch-all helpers
- Direct `st.session_state` access (use SessionStateManager)
- `import streamlit` in `services/` layer

**REQUIRED:**
- RED before GREEN (tests fail before implementation)
- Files < 500 LOC (split if larger)
- Semantic commits
- Coverage ≥ 60%
- Refactor log updates

### From UNIFIED_INSTRUCTIONS.md

**APPROVAL REQUIRED:**
- > 100 lines changed
- > 5 files modified
- Network calls
- Database schema changes
- Git push/merge/rebase

**AUTO-APPROVED:**
- Read/search operations
- Test execution (< 10 files)
- Lint/format existing files
- Documentation (< 100 lines, no structure changes)

---

## Metrics & Success Criteria

### Workflow Efficiency Metrics

| Workflow | Target Duration | Success Rate Target |
|----------|----------------|---------------------|
| ANALYSIS | 15-30 min | >90% (clear User Story) |
| FULL_TDD | 30-90 min | >80% (feature complete) |
| HOTFIX | 10-30 min | >95% (bug fixed) |
| REFACTOR | 15-30 min | >90% (quality improved) |
| REVIEW | 15-30 min | >90% (thorough review) |
| DOCUMENT | 5-20 min | >95% (docs updated) |

### Code Quality Metrics

| Metric | Target | Command |
|--------|--------|---------|
| Test Coverage | ≥ 60% (target 80%) | `pytest --cov=src` |
| File Size | < 500 LOC | `wc -l <file>` |
| Lint Errors | 0 | `ruff check src` |
| Tests Passing | 100% | `pytest` |

### Session Management Metrics

| Metric | Target | Measure |
|--------|--------|---------|
| Context Loss | < 5 min recovery | Time to resume work |
| Handoff Quality | Complete info | Handoff note completeness |
| Session Duration | < 90 min | Timer |

---

## Usage Guidelines

### For Solo Developer (Primary Use Case)

**Daily Workflow:**
1. Start session: Read CLAUDE.md, check git status
2. Select workflow based on task (use decision tree)
3. Execute workflow steps sequentially
4. End session: Commit or create handoff
5. Repeat

**Weekly Review:**
- Check metrics (coverage, file sizes)
- Review refactor log
- Update User Stories status
- Plan next week's priorities

### For Team Collaboration (Future)

**Cross-Developer Handoffs:**
- Use HANDOFF-NOTES.md for work transfer
- Include context notes
- Document decisions made
- Highlight blockers

**Code Reviews:**
- Use REVIEW workflow
- Create review report
- Share with team
- Track resolution

---

## Next Steps & Recommendations

### Immediate Actions (Week 1)

1. **Print Quick Reference Card**
   - Keep visible during development
   - Reference decision tree frequently

2. **Practice Workflows**
   - Start with DOCUMENT workflow (simplest)
   - Progress to FULL_TDD
   - Master session management

3. **Create First Handoff Note**
   - Template provided in workflow guide
   - Practice session continuity

### Short-Term Improvements (Month 1)

1. **Track Workflow Metrics**
   - Record durations
   - Measure success rates
   - Identify bottlenecks

2. **Refine Templates**
   - Adjust based on experience
   - Simplify if too complex
   - Add project-specific patterns

3. **Automate Common Patterns**
   - Create shell scripts for common sequences
   - Add make targets for workflows
   - Generate session reports

### Long-Term Evolution (Quarter 1)

1. **Workflow Optimization**
   - Analyze metrics
   - Identify pain points
   - Streamline processes

2. **Tool Integration**
   - Enhance git hooks
   - Improve pre-commit checks
   - Add workflow validators

3. **Documentation Updates**
   - Keep workflows current
   - Add new patterns discovered
   - Archive obsolete practices

---

## Troubleshooting

### Common Issues

**Issue: "I'm not sure which workflow to use"**
Solution: Use decision tree in Quick Reference, default to ANALYSIS if unclear

**Issue: "Lost context between sessions"**
Solution: Always create HANDOFF-NOTES.md, read git log --oneline -5

**Issue: "Tests won't pass in FULL_TDD"**
Solution: Verify you're in correct phase (RED before GREEN), check test setup

**Issue: "File too large (>500 LOC)"**
Solution: Use REFACTOR workflow to split into smaller modules

**Issue: "Production bug during feature work"**
Solution: Use emergency context switch pattern (git stash, HOTFIX workflow, return)

---

## References

### Primary Documents
- **VIBE_CODING_WORKFLOW.md:** Complete workflow guide (1000+ lines)
- **VIBE_CODING_QUICK_REFERENCE.md:** One-page cheat sheet (400+ lines)

### Supporting Documents
- **CLAUDE.md:** Project-specific instructions
- **UNIFIED_INSTRUCTIONS.md:** Cross-project rules (~/.ai-agents/)
- **TDD_TO_DEPLOYMENT_WORKFLOW.md:** Full TDD workflow details
- **WORKFLOW_LIBRARY.md:** All available workflows
- **CANONICAL_LOCATIONS.md:** File organization rules

### External Resources
- Vibe Coding methodology documentation
- Claude Code tool documentation
- BMad Method agent guides

---

## Version History

**v1.0 (2025-10-17):**
- Initial release
- 6 workflows defined
- Session management strategy
- 4 practical examples
- Integration with existing DefinitieAgent workflows

**Next Review:** 2025-11-17

---

## Conclusion

This Vibe Coding integration provides:

✅ **Right-sized workflows** for different task types
✅ **Session management** for Claude Code's stateless nature
✅ **Practical examples** for common scenarios
✅ **Tool integration** for every workflow step
✅ **Quality gates** to maintain standards
✅ **Handoff protocols** for continuity

**Result:** Efficient, consistent development workflow optimized for solo developer using Claude Code with DefinitieAgent project.

**Status:** Ready for immediate use. Start with Quick Reference Card and DOCUMENT workflow for simplest entry.

---

**Prepared by:** Claude Code (Workflow Architect mode)
**Date:** 2025-10-17
**Document Status:** Canonical, Active
