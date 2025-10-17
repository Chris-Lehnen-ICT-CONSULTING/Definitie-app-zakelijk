---
aangemaakt: 2025-10-17
applies_to: definitie-app@current
bijgewerkt: 2025-10-17
canonical: true
type: quick-reference
parent: VIBE_CODING_WORKFLOW.md
---

# Vibe Coding Quick Reference Card

**One-page reference for immediate workflow decisions.**

---

## Decision Flowchart

```
START: What am I doing?
│
├─ "I don't know what to build yet"
│   └─> ANALYSIS Workflow (5-step)
│       Duration: 15-30 min
│       Output: User Story + Design
│
├─ "Production is broken RIGHT NOW"
│   └─> HOTFIX Workflow (3-step)
│       Duration: 10-30 min
│       Output: Quick fix + test
│
├─ "I have a clear feature to build"
│   └─> FULL_TDD Workflow (8-step)
│       Duration: 30-90 min
│       Output: Complete feature + tests
│
├─ "Code quality is bad but it works"
│   └─> REFACTOR Workflow (4-step)
│       Duration: 15-30 min
│       Output: Cleaner code, same behavior
│
├─ "I need to review existing code"
│   └─> REVIEW Workflow (2-step)
│       Duration: 15-30 min
│       Output: Review report
│
└─ "Just fixing documentation"
    └─> DOCUMENT Workflow (3-step)
        Duration: 5-20 min
        Output: Updated docs
```

---

## Workflow Cheat Sheet

### ANALYSIS (5-Step Discovery)
```
[1] CLARIFY    → Ask questions (AskUserQuestion)
[2] RESEARCH   → Explore codebase (Grep, Read)
[3] DESIGN     → Draft solution
[4] VALIDATE   → Confirm with user
[5] DOCUMENT   → Create US-XXX.md
```
**Exit:** User Story ready for implementation

### FULL_TDD (8-Step RED-GREEN-REFACTOR)
```
[1] UNDERSTAND → Read US-XXX.md
[2] TEST-RED   → Write failing tests
[3] COMMIT     → test(US-XXX): ...
[4] IMPLEMENT  → Write minimal code
[5] TEST-GREEN → All tests pass
[6] COMMIT     → feat(US-XXX): ...
[7] REFACTOR   → Improve quality
[8] VERIFY     → Coverage + lint
```
**Exit:** Feature complete, tests green

### HOTFIX (3-Step Emergency)
```
[1] REPRODUCE  → Identify bug
[2] PATCH      → Minimal fix + test
[3] DEPLOY     → Push to production
```
**Exit:** Bug fixed, deployed

### REFACTOR (4-Step Quality)
```
[1] BASELINE   → Check current coverage
[2] REFACTOR   → Small improvements
[3] VERIFY     → Tests still green
[4] DOCUMENT   → Update refactor log
```
**Exit:** Code cleaner, behavior unchanged

### REVIEW (2-Step Audit)
```
[1] AUDIT      → 7-point checklist
[2] REPORT     → Document findings
```
**Exit:** Review report created

### DOCUMENT (3-Step Cleanup)
```
[1] AUDIT      → Find issues
[2] FIX        → Update docs
[3] VERIFY     → Check links/structure
```
**Exit:** Docs updated

---

## Session Management

### Every Session Start
```bash
# ALWAYS run these three
git status
git log --oneline -5
cat CLAUDE.md  # Read project instructions

# If continuing work
cat docs/backlog/EPIC-XXX/US-XXX/HANDOFF-NOTES.md
```

### Every Session End (Work Incomplete)
```bash
# Create handoff note
cat > docs/backlog/EPIC-XXX/US-XXX/HANDOFF-NOTES.md << EOF
## Handoff [$(date +%Y-%m-%d)]
Work Unit: US-XXX
Progress: X%
What I did: ...
What's next: ...
Blockers: ...
EOF

# Commit WIP
git add .
git commit -m "WIP(US-XXX): <description>"
```

### Every Session End (Work Complete)
```bash
# Update status
# Edit US-XXX.md: status: "Ready for Review"

# Final commit
git commit -m "feat(US-XXX): <description>"
git push
```

---

## Essential Commands

### Testing
```bash
# Run specific test
pytest tests/path/to/test_file.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run category
pytest -m unit
pytest -m integration
pytest -m smoke

# Fast tests only
pytest -m "not slow"
```

### Code Quality
```bash
# All quality checks
pre-commit run --all-files

# Individual checks
ruff check src
black src
```

### Development
```bash
# Start app (recommended)
bash scripts/run_app.sh

# Alternative
make dev

# Direct run
OPENAI_API_KEY="$OPENAI_API_KEY_PROD" streamlit run src/main.py
```

### Git
```bash
# Semantic commit
git commit -m "type(scope): description"

# Types: feat, fix, test, refactor, docs, chore, perf

# Examples
git commit -m "test(US-042): add failing tests"
git commit -m "feat(US-042): implement feature"
git commit -m "fix(US-042): resolve edge case"
git commit -m "refactor(US-042): extract helper"
```

---

## Critical Rules

### From CLAUDE.md

**FORBIDDEN:**
- `import streamlit` in `services/` (UI in business logic)
- Creating files in project root (use proper directories)
- Backwards compatibility code (refactor, don't bridge)
- God object / catch-all helpers (e.g., dry_helpers.py)
- Direct `st.session_state` access (use SessionStateManager)

**REQUIRED:**
- Tests BEFORE implementation (RED → GREEN)
- Semantic commits (type(scope): description)
- Files < 500 LOC (split if larger)
- Coverage ≥ 60% (target 80%+)
- Update refactor log when refactoring

### From UNIFIED_INSTRUCTIONS.md

**APPROVAL REQUIRED:**
- > 100 lines changed
- > 5 files modified
- Network calls (external APIs)
- Database schema changes
- Git push/merge/rebase

**AUTO-APPROVED:**
- Read/search operations
- Test execution (< 10 files)
- Lint/format existing files
- Documentation (< 100 lines)

---

## File Locations

```
User Stories:       docs/backlog/EPIC-XXX/US-XXX/US-XXX.md
EPICs:              docs/backlog/EPIC-XXX/EPIC-XXX.md
Architecture:       docs/architectuur/
Reviews:            docs/reviews/<ID>-review.md
Refactor Log:       docs/refactor-log.md
Handoff Notes:      docs/backlog/EPIC-XXX/US-XXX/HANDOFF-NOTES.md

Tests:              tests/ (mirrors src/ structure)
Source Code:        src/
Config:             config/
Scripts:            scripts/
Data:               data/ (only database here)
```

---

## Troubleshooting

### "I'm stuck, what workflow?"
→ Start with **ANALYSIS** workflow to clarify

### "Tests won't pass"
→ Check you're in correct phase (RED before GREEN)

### "File too large (>500 LOC)"
→ Use **REFACTOR** workflow to split

### "Production bug"
→ Use **HOTFIX** workflow (fast track)

### "Lost context between sessions"
→ Read HANDOFF-NOTES.md or git log

### "Not sure what to commit"
→ Use semantic commit format cheat sheet above

---

## Common Patterns

### Pattern: Add New Validation Rule
```
Workflow: FULL_TDD
Files:
  - config/toetsregels/regels/<RULE>.json
  - src/toetsregels/regels/<RULE>.py
  - tests/toetsregels/test_<RULE>.py
Steps: 1→8 (all TDD steps)
```

### Pattern: Fix Service Bug
```
Workflow: HOTFIX (if urgent) or FULL_TDD (if not)
Steps:
  1. Reproduce with test
  2. Fix minimal code
  3. Verify no regression
```

### Pattern: Split Large File
```
Workflow: REFACTOR
Steps:
  1. Baseline coverage
  2. Extract logical groups
  3. Keep tests green
  4. Update refactor log
```

### Pattern: New UI Feature
```
Workflow: ANALYSIS → FULL_TDD
Session 1 (ANALYSIS):
  - Clarify requirements
  - Design approach
  - Create US-XXX.md
Session 2 (FULL_TDD):
  - Write tests
  - Implement
  - Verify
```

---

## When to Switch Workflows

### Switch from ANALYSIS to FULL_TDD
**Trigger:** User Story complete, design validated
**Handoff:** US-XXX.md file

### Switch from FULL_TDD to REVIEW
**Trigger:** Feature complete, all tests green
**Handoff:** Git commits

### Switch from REVIEW to REFACTOR
**Trigger:** Review complete, recommendations identified
**Handoff:** Review report

### Switch from any to HOTFIX
**Trigger:** Production incident
**Action:** Git stash current work, switch branches

---

## Quality Checklist

### Before Committing
- [ ] All tests green (`pytest`)
- [ ] No linting errors (`ruff check src`)
- [ ] Files formatted (`black src`)
- [ ] Coverage maintained (≥ 60%)
- [ ] Semantic commit message
- [ ] No files in root directory

### Before Pushing
- [ ] All commits made
- [ ] CHANGELOG updated (if needed)
- [ ] US-XXX status updated
- [ ] Handoff notes created (if incomplete)

### Before Session End
- [ ] Work committed or stashed
- [ ] Git status clean
- [ ] Next steps documented

---

## Emergency Procedures

### Production Incident
```
1. STOP current work
2. git stash save "WIP: <description>"
3. git checkout main
4. git checkout -b hotfix/<issue>
5. Execute HOTFIX workflow
6. Deploy fix
7. Return to feature work: git stash pop
```

### Lost Context
```
1. git log --oneline -10 (review recent work)
2. git diff main (see what changed)
3. Read HANDOFF-NOTES.md (if exists)
4. Read US-XXX.md (understand goal)
5. Continue from current state
```

### Breaking Change
```
1. git status (identify changes)
2. git diff (review changes)
3. pytest (identify failures)
4. git revert <commit> (if needed)
5. git reset --hard HEAD (nuclear option)
```

---

## Key Metrics

| Metric | Target | Command |
|--------|--------|---------|
| Test Coverage | ≥ 60% (target 80%) | `pytest --cov=src` |
| File Size | < 500 LOC | `wc -l <file>` |
| Lint Errors | 0 | `ruff check src` |
| Session Duration | < 90 min | Timer |
| Tests Passing | 100% | `pytest` |

---

## Reference Links

- **Full Workflow Guide:** VIBE_CODING_WORKFLOW.md
- **Project Instructions:** CLAUDE.md
- **Unified Rules:** ~/.ai-agents/UNIFIED_INSTRUCTIONS.md
- **TDD Workflow:** TDD_TO_DEPLOYMENT_WORKFLOW.md
- **Canonical Locations:** CANONICAL_LOCATIONS.md

---

**Print this page and keep it visible during development sessions.**

**Last Updated:** 2025-10-17
