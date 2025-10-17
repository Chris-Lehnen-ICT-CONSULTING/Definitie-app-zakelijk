---
aangemaakt: 2025-10-17
applies_to: definitie-app@current
bijgewerkt: 2025-10-17
canonical: true
last_verified: 2025-10-17
owner: development
prioriteit: high
status: active
type: workflow-guide
---

# Vibe Coding Workflow for DefinitieAgent with Claude Code

**Purpose:** Optimize development workflow using Vibe Coding methodology with Claude Code as primary tool.

**Target Audience:** Solo developer using Claude Code for DefinitieAgent development.

**Key Principle:** Right workflow for the right task. No over-engineering, no under-engineering.

## Table of Contents

1. [Quick Decision Tree](#quick-decision-tree)
2. [Workflow Sequences](#workflow-sequences)
3. [Session Management](#session-management)
4. [Tool Integration](#tool-integration)
5. [Practical Examples](#practical-examples)
6. [Handoff Protocols](#handoff-protocols)

---

## Quick Decision Tree

```
┌─ Is this ONLY documentation? ──YES──> DOCUMENT workflow
│
├─ Is this urgent production bug? ──YES──> HOTFIX workflow
│
├─ Do I know WHAT to build? ──NO──> ANALYSIS workflow
│
├─ Is there existing code to review? ──YES──> REVIEW workflow
│
├─ Am I improving code quality only? ──YES──> REFACTOR workflow
│
└─ Am I building a new feature? ──YES──> FULL_TDD workflow
```

**Rule of Thumb:**
- **< 50 lines, no tests needed** → HOTFIX
- **Documentation only** → DOCUMENT
- **Need to understand first** → ANALYSIS
- **Quality improvement** → REFACTOR or REVIEW
- **New feature** → FULL_TDD

---

## Workflow Sequences

### 1. ANALYSIS Workflow (Vibe Coding: 5-Step Discovery)

**When:** Starting from user request, unclear requirements, or new feature planning.

**Vibe Template:** 5-Step Structured Discovery

**Sequence:**
```
USER REQUEST
    ↓
[1] CLARIFY - Ask targeted questions
    ↓
[2] RESEARCH - Explore codebase context
    ↓
[3] DESIGN - Draft solution approach
    ↓
[4] VALIDATE - Confirm with user
    ↓
[5] DOCUMENT - Create User Story + Architecture
```

**Claude Code Tools:**
```yaml
Step 1 (Clarify):
  - AskUserQuestion tool
  - Read: CLAUDE.md, PRD, EPIC files

Step 2 (Research):
  - Grep: Find similar patterns
  - Glob: Locate relevant modules
  - Read: Service files, config files

Step 3 (Design):
  - Read: Architecture docs (EA/SA/TA)
  - Write: Draft design doc

Step 4 (Validate):
  - AskUserQuestion: Confirm approach

Step 5 (Document):
  - Write: User Story (EPIC-XXX/US-XXX/US-XXX.md)
  - Edit: Update EPIC file
  - Write: Architecture notes
```

**Output Artifacts:**
- `docs/backlog/EPIC-XXX/US-XXX/US-XXX.md` (User Story)
- `docs/architectuur/<component>-design.md` (if needed)
- Session handoff notes

**Exit Criteria:**
- [ ] User Story has globally unique ID
- [ ] SMART criteria defined
- [ ] Acceptance criteria in BDD format
- [ ] Design approach validated
- [ ] Ready for implementation

**Typical Duration:** 15-30 minutes

---

### 2. FULL_TDD Workflow (Vibe Coding: 8-Step Implementation)

**When:** Building new feature with known requirements.

**Vibe Template:** 8-Step RED-GREEN-REFACTOR

**Sequence:**
```
USER STORY READY
    ↓
[1] UNDERSTAND - Read story, identify test cases
    ↓
[2] TEST-RED - Write failing tests
    ↓
[3] COMMIT - test(US-XXX): add failing tests
    ↓
[4] IMPLEMENT - Minimal code to pass
    ↓
[5] TEST-GREEN - All tests pass
    ↓
[6] COMMIT - feat(US-XXX): implement feature
    ↓
[7] REFACTOR - Improve code quality
    ↓
[8] VERIFY - Run full test suite
```

**Claude Code Tools:**
```yaml
Step 1 (Understand):
  - Read: User story file
  - Grep: Find similar implementations
  - Read: Relevant service files

Step 2 (Test-RED):
  - Read: Existing test patterns
  - Write: New test file(s)
  - Bash: pytest <new_test> (should fail)

Step 3 (Commit):
  - Bash: git add tests/
  - Bash: git commit -m "test(US-XXX): ..."

Step 4-5 (Implement):
  - Edit: Service/module files
  - Bash: pytest (watch tests turn green)

Step 6 (Commit):
  - Bash: git add src/
  - Bash: git commit -m "feat(US-XXX): ..."

Step 7 (Refactor):
  - Edit: Improve code structure
  - Bash: pytest (ensure still green)

Step 8 (Verify):
  - Bash: pytest --cov=src
  - Bash: ruff check src
  - Bash: black src
```

**Critical Rules:**
- **NO implementation before tests fail**
- **Complete feature in ONE session**
- **Maintain test coverage ≥ 60%**
- **Follow CLAUDE.md refactor rules**

**Output Artifacts:**
- New/modified source files (`src/`)
- Test files (`tests/`)
- Git commits (semantic format)
- Coverage report

**Exit Criteria:**
- [ ] All tests green
- [ ] Coverage ≥ 60%
- [ ] No linting errors
- [ ] Semantic commits made
- [ ] Ready for review

**Typical Duration:** 30-90 minutes

---

### 3. HOTFIX Workflow (Vibe Coding: 3-Step Emergency)

**When:** Production bug, urgent fix needed.

**Vibe Template:** 3-Step Emergency Response

**Sequence:**
```
BUG REPORTED
    ↓
[1] REPRODUCE - Identify exact issue
    ↓
[2] PATCH - Minimal fix + test
    ↓
[3] DEPLOY - Fast track to production
```

**Claude Code Tools:**
```yaml
Step 1 (Reproduce):
  - Read: Error logs
  - Grep: Find bug location
  - Bash: Reproduce locally

Step 2 (Patch):
  - Edit: Minimal fix
  - Write: Regression test
  - Bash: pytest <test>

Step 3 (Deploy):
  - Bash: git commit -m "fix(HOTFIX-XXX): ..."
  - Bash: git push
  - Monitor: Check production
```

**Critical Rules:**
- **Minimal scope** - Fix ONE thing
- **No feature creep**
- **Add regression test**
- **Document in commit message**

**Output Artifacts:**
- Patch commit
- Regression test
- Brief incident note

**Exit Criteria:**
- [ ] Bug fixed and verified
- [ ] Regression test added
- [ ] Production deployed
- [ ] Post-mortem scheduled (if needed)

**Typical Duration:** 10-30 minutes

---

### 4. REFACTOR Workflow (Vibe Coding: 4-Step Quality)

**When:** Improving code quality without changing behavior.

**Vibe Template:** 4-Step Safe Refactor

**Sequence:**
```
CODE QUALITY ISSUE
    ↓
[1] BASELINE - Establish test coverage
    ↓
[2] REFACTOR - Small, atomic improvements
    ↓
[3] VERIFY - Tests still green
    ↓
[4] DOCUMENT - Update refactor log
```

**Claude Code Tools:**
```yaml
Step 1 (Baseline):
  - Bash: pytest --cov=src/<module>
  - Read: Current code

Step 2 (Refactor):
  - Edit: Extract functions
  - Edit: Rename variables
  - Edit: Simplify logic

Step 3 (Verify):
  - Bash: pytest (ensure green)
  - Bash: pytest --cov=src (maintain coverage)

Step 4 (Document):
  - Edit: docs/refactor-log.md
  - Bash: git commit -m "refactor(US-XXX): ..."
```

**Critical Rules:**
- **Preserve exact behavior**
- **Keep tests green**
- **Micro-refactors only** (per CLAUDE.md)
- **Update refactor log**

**Output Artifacts:**
- Refactored code
- Entry in `docs/refactor-log.md`
- Commit

**Exit Criteria:**
- [ ] All tests still green
- [ ] Coverage maintained
- [ ] Behavior unchanged
- [ ] Refactor log updated

**Typical Duration:** 15-30 minutes

---

### 5. REVIEW Workflow (Vibe Coding: 2-Step Audit)

**When:** Code exists, need structured review.

**Vibe Template:** 2-Step Code Audit

**Sequence:**
```
CODE TO REVIEW
    ↓
[1] AUDIT - Comprehensive review
    ↓
[2] REPORT - Document findings
```

**Claude Code Tools:**
```yaml
Step 1 (Audit):
  - Read: Code to review
  - Grep: Find related code
  - Check: Security, performance, style

Step 2 (Report):
  - Write: docs/reviews/<ID>-review.md
  - Categorize: Critical/Recommendations/Good
```

**Review Checklist:**
- [ ] Correctness & Logic
- [ ] Test Coverage
- [ ] Security & Privacy
- [ ] Performance
- [ ] Code Style
- [ ] Documentation
- [ ] Domain Compliance

**Output Artifacts:**
- Review report (`docs/reviews/<ID>-review.md`)
- Verdict: APPROVED / APPROVED WITH CONDITIONS / CHANGES REQUESTED

**Exit Criteria:**
- [ ] Complete review report
- [ ] No critical blockers
- [ ] Concrete suggestions

**Typical Duration:** 15-30 minutes

---

### 6. DOCUMENT Workflow (Vibe Coding: 3-Step Cleanup)

**When:** Documentation only work.

**Vibe Template:** 3-Step Doc Maintenance

**Sequence:**
```
DOCS NEED UPDATE
    ↓
[1] AUDIT - Find issues
    ↓
[2] FIX - Update docs
    ↓
[3] VERIFY - Validate links/structure
```

**Claude Code Tools:**
```yaml
Step 1 (Audit):
  - Grep: Find broken references
  - Read: Existing docs

Step 2 (Fix):
  - Edit: Update content
  - Write: New docs (if needed)
  - Edit: Add frontmatter

Step 3 (Verify):
  - Bash: Check markdown links
  - Read: Verify canonical locations
```

**Critical Rules:**
- **Follow CANONICAL_LOCATIONS.md**
- **Add proper frontmatter**
- **Update INDEX.md if needed**
- **No code changes**

**Output Artifacts:**
- Updated documentation
- Git commit

**Exit Criteria:**
- [ ] Canonical locations correct
- [ ] Frontmatter present
- [ ] No broken links
- [ ] INDEX.md updated

**Typical Duration:** 5-20 minutes

---

## Session Management

### Session Continuity Strategy

**Problem:** Claude Code sessions don't persist context between conversations.

**Solution:** Use handoff documents and session notes.

### 1. Session Start Checklist

```yaml
Every new Claude Code session:
  - Read: CLAUDE.md (project instructions)
  - Read: Current EPIC/US file (if working on story)
  - Bash: git status (understand current state)
  - Bash: git log --oneline -5 (recent changes)
  - Read: Any handoff notes from previous session
```

### 2. Session End Protocol

```yaml
Before ending session:
  - Create handoff note if work incomplete
  - Commit any changes
  - Update User Story status
  - Document next steps
```

**Handoff Note Template:**
```markdown
## Session Handoff - [YYYY-MM-DD HH:MM]

**Work Unit:** US-XXX / EPIC-XXX
**Current Phase:** TEST-RED / DEV-GREEN / etc.
**Progress:** 40% complete

### What I Did
- Implemented X
- Fixed Y
- Created Z

### What's Next
- Need to implement A
- Test B
- Review C

### Context Notes
- Important decision: chose pattern X because Y
- Watch out for: Z dependency
- Files modified: list here

### Blockers
- None / Waiting for X
```

**Location:** `docs/backlog/EPIC-XXX/US-XXX/HANDOFF-NOTES.md`

### 3. Context Preservation

**Use Git commits as checkpoints:**
```bash
# Small checkpoint commit
git commit -m "WIP(US-XXX): partial implementation of X"

# Session end commit
git commit -m "chore(US-XXX): session checkpoint - 40% complete"
```

**Use session state files:**
```yaml
Location: docs/backlog/EPIC-XXX/US-XXX/SESSION-STATE.json

{
  "last_session": "2025-10-17T14:30:00Z",
  "current_phase": "DEV-GREEN",
  "progress_percent": 40,
  "files_modified": ["src/services/x.py", "tests/test_x.py"],
  "next_actions": [
    "Complete implementation of feature Y",
    "Add integration test for Z"
  ],
  "blockers": []
}
```

---

## Tool Integration

### Git Integration

**Commit Message Format:**
```
<type>(<scope>): <description>

[optional body]
[optional footer]

Examples:
test(US-042): add failing tests for validation rule
feat(US-042): implement validation rule SAM-002
fix(US-042): resolve edge case in validator
refactor(US-042): extract validation helper
docs(US-042): update architecture notes
chore(US-042): session checkpoint
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `test`: Test changes
- `refactor`: Code restructure
- `docs`: Documentation
- `chore`: Maintenance
- `perf`: Performance
- `style`: Formatting

### Testing Integration

**Pytest Commands:**
```bash
# Run specific test file
pytest tests/services/test_definition_generator.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test category
pytest -m unit
pytest -m integration
pytest -m smoke

# Run fast tests only
pytest -m "not slow"

# Run specific test
pytest tests/services/test_x.py::test_function_name
```

**High-Coverage Modules (Verify After Changes):**
```bash
pytest tests/services/test_definition_generator.py    # 99%
pytest tests/services/test_definition_validator.py    # 98%
pytest tests/services/test_definition_repository.py   # 100%
```

### Code Quality Integration

**Pre-Commit Workflow:**
```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
pre-commit run black --all-files

# Install hooks (one-time)
pre-commit install
```

**Manual Quality Checks:**
```bash
# Linting
ruff check src config

# Formatting
black src config

# Type checking (if enabled)
mypy src
```

### Development Server

**Start Application:**
```bash
# Recommended method (auto env mapping)
bash scripts/run_app.sh

# Alternative
make dev

# Direct run
OPENAI_API_KEY="$OPENAI_API_KEY_PROD" streamlit run src/main.py
```

---

## Practical Examples

### Example 1: Adding New Validation Rule

**Scenario:** User wants new validation rule for synonym consistency.

**Workflow Selection:** FULL_TDD (new feature)

**Step-by-Step:**

```
┌─ SESSION START ────────────────────────────────────┐
│ Read: CLAUDE.md                                    │
│ Read: docs/backlog/EPIC-002/EPIC-002.md           │
│ Bash: git status                                   │
└────────────────────────────────────────────────────┘

┌─ STEP 1: UNDERSTAND ───────────────────────────────┐
│ Read: docs/backlog/EPIC-002/US-XXX/US-XXX.md      │
│ Grep: "class.*ValidationRule" (find pattern)      │
│ Read: config/toetsregels/regels/SAM-001.json      │
│ Read: src/toetsregels/regels/SAM_001.py           │
└────────────────────────────────────────────────────┘

┌─ STEP 2: TEST-RED ─────────────────────────────────┐
│ Write: tests/toetsregels/test_SAM_003.py          │
│       def test_synonym_consistency_fail():         │
│           # Arrange: definition with inconsistent  │
│           # Act: validate                          │
│           # Assert: should fail                    │
│                                                    │
│ Bash: pytest tests/toetsregels/test_SAM_003.py    │
│       → 1 failed ✓ (RED state confirmed)          │
└────────────────────────────────────────────────────┘

┌─ STEP 3: COMMIT TEST ──────────────────────────────┐
│ Bash: git add tests/toetsregels/test_SAM_003.py   │
│ Bash: git commit -m "test(US-XXX): add failing    │
│       tests for synonym consistency rule"          │
└────────────────────────────────────────────────────┘

┌─ STEP 4: IMPLEMENT ────────────────────────────────┐
│ Write: config/toetsregels/regels/SAM-003.json     │
│ Write: src/toetsregels/regels/SAM_003.py          │
│       class SynonymConsistencyRule(ValidationRule):│
│           def validate(self, definition): ...      │
└────────────────────────────────────────────────────┘

┌─ STEP 5: TEST-GREEN ───────────────────────────────┐
│ Bash: pytest tests/toetsregels/test_SAM_003.py    │
│       → All tests passed ✓ (GREEN state)          │
└────────────────────────────────────────────────────┘

┌─ STEP 6: COMMIT FEATURE ───────────────────────────┐
│ Bash: git add config/toetsregels/ src/toetsregels/│
│ Bash: git commit -m "feat(US-XXX): implement      │
│       synonym consistency validation rule SAM-003" │
└────────────────────────────────────────────────────┘

┌─ STEP 7: REFACTOR ─────────────────────────────────┐
│ Edit: Extract common validation pattern           │
│ Bash: pytest (ensure still green)                 │
│ Edit: docs/refactor-log.md                        │
└────────────────────────────────────────────────────┘

┌─ STEP 8: VERIFY ───────────────────────────────────┐
│ Bash: pytest --cov=src/toetsregels               │
│       → Coverage: 98% ✓                           │
│ Bash: ruff check src/toetsregels                 │
│       → No issues ✓                               │
│ Bash: make validation-status                     │
│       → All rules loaded ✓                        │
└────────────────────────────────────────────────────┘

┌─ SESSION END ──────────────────────────────────────┐
│ Update: US-XXX status → "Ready for Review"        │
│ No handoff needed (work complete)                 │
└────────────────────────────────────────────────────┘
```

**Duration:** ~45 minutes

---

### Example 2: Refactoring Service Module

**Scenario:** `src/services/validation_service.py` is 800 lines (should be < 500).

**Workflow Selection:** REFACTOR

**Step-by-Step:**

```
┌─ STEP 1: BASELINE ─────────────────────────────────┐
│ Bash: wc -l src/services/validation_service.py    │
│       → 823 lines                                  │
│ Bash: pytest tests/services/test_validation*.py   │
│       --cov=src/services/validation_service.py    │
│       → Coverage: 94% (baseline)                  │
└────────────────────────────────────────────────────┘

┌─ STEP 2: ANALYZE ──────────────────────────────────┐
│ Read: src/services/validation_service.py          │
│ Identify: 3 logical groups                        │
│   - Rule loading (200 lines)                      │
│   - Validation execution (400 lines)              │
│   - Result formatting (223 lines)                 │
└────────────────────────────────────────────────────┘

┌─ STEP 3: REFACTOR (Atomic) ────────────────────────┐
│ Edit: Extract rule loading                        │
│   Create: src/services/validation/rule_loader.py │
│   Move: Rule loading logic                        │
│   Update: validation_service.py imports          │
│                                                    │
│ Bash: pytest tests/services/test_validation*.py   │
│       → All tests green ✓                         │
│                                                    │
│ Bash: git commit -m "refactor: extract rule       │
│       loader from validation service (200 lines)" │
└────────────────────────────────────────────────────┘

┌─ STEP 4: REFACTOR (Atomic) ────────────────────────┐
│ Edit: Extract result formatting                   │
│   Create: src/services/validation/formatter.py   │
│   Move: Result formatting logic                   │
│                                                    │
│ Bash: pytest tests/services/test_validation*.py   │
│       → All tests green ✓                         │
│                                                    │
│ Bash: git commit -m "refactor: extract result     │
│       formatter from validation service (223)"    │
└────────────────────────────────────────────────────┘

┌─ STEP 5: VERIFY ───────────────────────────────────┐
│ Bash: wc -l src/services/validation_service.py    │
│       → 400 lines ✓                               │
│ Bash: pytest --cov=src/services/validation*.py    │
│       → Coverage: 94% (maintained) ✓              │
│ Bash: ruff check src/services/                    │
│       → No issues ✓                               │
└────────────────────────────────────────────────────┘

┌─ STEP 6: DOCUMENT ─────────────────────────────────┐
│ Edit: docs/refactor-log.md                        │
│   Add: Entry for validation service split         │
│   Rationale: Reduce file size, improve modularity │
│   Files affected: 3                               │
└────────────────────────────────────────────────────┘
```

**Duration:** ~30 minutes

---

### Example 3: Designing New UI Feature

**Scenario:** User wants new "Export to JSON" button in UI.

**Workflow Selection:** ANALYSIS → FULL_TDD

**Step-by-Step (ANALYSIS Phase):**

```
┌─ SESSION 1: ANALYSIS ──────────────────────────────┐
│                                                    │
│ STEP 1: CLARIFY                                   │
│ AskUserQuestion:                                   │
│   - Which tab should have this button?           │
│   - What data to export?                          │
│   - Any specific JSON structure?                  │
│                                                    │
│ User answers:                                      │
│   - Tab: "Definitie Generatie"                    │
│   - Data: Current definition + metadata           │
│   - Structure: Standard DefinitionResponseV2      │
│                                                    │
│ STEP 2: RESEARCH                                   │
│ Grep: "export.*json" (find similar patterns)     │
│ Read: src/ui/tabs/definitie_generatie.py         │
│ Read: src/models/definition_response_v2.py       │
│ Glob: src/utils/*export*.py (check existing)     │
│                                                    │
│ STEP 3: DESIGN                                     │
│ Design decision:                                   │
│   - Add button to existing button row            │
│   - Use st.download_button with JSON bytes       │
│   - Leverage existing DefinitionResponseV2.dict() │
│   - No new service needed                        │
│                                                    │
│ STEP 4: VALIDATE                                   │
│ AskUserQuestion:                                   │
│   "Proposed design: Add download button next to   │
│    existing buttons, export current definition    │
│    as JSON using existing response model.         │
│    Confirm?"                                       │
│                                                    │
│ User: ✓ Approved                                  │
│                                                    │
│ STEP 5: DOCUMENT                                   │
│ Write: docs/backlog/EPIC-004/US-440/US-440.md    │
│   Title: Export Definition to JSON                │
│   Story: As a user, I want to export...          │
│   AC: Given definition generated, When I click... │
│   Design: Use st.download_button...              │
│                                                    │
│ Edit: docs/backlog/EPIC-004/EPIC-004.md          │
│   Add: - US-440 to stories list                  │
└────────────────────────────────────────────────────┘

Duration: 20 minutes
Exit: User Story ready for implementation
```

**Step-by-Step (IMPLEMENTATION Phase):**

```
┌─ SESSION 2: FULL_TDD ──────────────────────────────┐
│                                                    │
│ STEP 1: UNDERSTAND                                 │
│ Read: docs/backlog/EPIC-004/US-440/US-440.md     │
│ Read: src/ui/tabs/definitie_generatie.py         │
│                                                    │
│ STEP 2: TEST-RED                                   │
│ Write: tests/ui/test_export_json.py              │
│   def test_export_button_appears():              │
│   def test_export_json_structure():              │
│                                                    │
│ Bash: pytest tests/ui/test_export_json.py        │
│       → 2 failed ✓                                │
│                                                    │
│ STEP 3: COMMIT TEST                               │
│ Bash: git commit -m "test(US-440): add failing   │
│       tests for JSON export"                      │
│                                                    │
│ STEP 4-5: IMPLEMENT                               │
│ Edit: src/ui/tabs/definitie_generatie.py         │
│   Add: st.download_button for JSON export        │
│   Add: Helper function to format JSON            │
│                                                    │
│ Bash: pytest tests/ui/test_export_json.py        │
│       → All tests passed ✓                        │
│                                                    │
│ STEP 6: COMMIT FEATURE                            │
│ Bash: git commit -m "feat(US-440): add JSON      │
│       export button to definitie generatie tab"   │
│                                                    │
│ STEP 7-8: VERIFY                                  │
│ Bash: streamlit run src/main.py (manual test)    │
│       → Button works, JSON downloads ✓            │
│ Bash: pytest --cov=src/ui                        │
│       → Coverage maintained ✓                     │
└────────────────────────────────────────────────────┘

Duration: 30 minutes
Total: 50 minutes (both sessions)
```

---

### Example 4: Fixing Complex Bug

**Scenario:** Validation rule SAM-002 incorrectly flags valid definitions.

**Workflow Selection:** HOTFIX (if urgent) or FULL_TDD (if not urgent)

**Using HOTFIX Workflow:**

```
┌─ STEP 1: REPRODUCE ────────────────────────────────┐
│ Read: Bug report / error logs                     │
│ Read: src/toetsregels/regels/SAM_002.py          │
│ Read: tests/toetsregels/test_SAM_002.py          │
│                                                    │
│ Create reproduction test:                         │
│ Edit: tests/toetsregels/test_SAM_002.py          │
│   def test_false_positive_bug():                  │
│       # Arrange: valid definition                │
│       # Act: validate                             │
│       # Assert: should pass but currently fails  │
│                                                    │
│ Bash: pytest tests/toetsregels/test_SAM_002.py:: │
│       test_false_positive_bug                     │
│       → Failed ✓ (bug reproduced)                │
└────────────────────────────────────────────────────┘

┌─ STEP 2: PATCH ────────────────────────────────────┐
│ Analyze:                                           │
│   Root cause: Regex pattern too strict           │
│                                                    │
│ Edit: src/toetsregels/regels/SAM_002.py          │
│   Fix: Update regex pattern                       │
│                                                    │
│ Bash: pytest tests/toetsregels/test_SAM_002.py   │
│       → All tests passed ✓                        │
│                                                    │
│ Bash: pytest tests/toetsregels/ (regression)     │
│       → All tests passed ✓                        │
└────────────────────────────────────────────────────┘

┌─ STEP 3: DEPLOY ───────────────────────────────────┐
│ Bash: git add .                                    │
│ Bash: git commit -m "fix(SAM-002): correct       │
│       regex pattern causing false positives       │
│                                                    │
│       - Updated pattern to allow X                │
│       - Added regression test                     │
│       - Fixes #123"                               │
│                                                    │
│ Bash: git push                                     │
│                                                    │
│ Optional: Create brief incident note              │
│ Write: docs/incidents/2025-10-17-SAM-002-fix.md  │
└────────────────────────────────────────────────────┘

Duration: 20 minutes
```

---

## Handoff Protocols

### Between Workflow Phases

**ANALYSIS → FULL_TDD:**
```yaml
Handoff Artifact: User Story (US-XXX.md)

Required Content:
  - User Story with ID
  - SMART criteria
  - Acceptance criteria (BDD format)
  - Design notes (if complex)

Verification:
  - Read: US-XXX.md in new session
  - Confirm: All acceptance criteria clear
  - Identify: Test cases from AC
```

**FULL_TDD → REVIEW:**
```yaml
Handoff Artifact: Git commits + changed files

Required Content:
  - Semantic commits (test, feat, refactor)
  - All tests passing
  - No linting errors

Verification:
  - Bash: git log --oneline -5
  - Bash: git diff main
  - Bash: pytest && ruff check src
```

**REVIEW → REFACTOR:**
```yaml
Handoff Artifact: Review report

Required Content:
  - docs/reviews/<ID>-review.md
  - Categorized findings
  - Verdict

Verification:
  - Read: Review report
  - Identify: Refactor opportunities
  - Prioritize: High-impact improvements
```

### Between Sessions (Same Developer)

**Session End Checklist:**
```yaml
If work NOT complete:
  - [ ] Create HANDOFF-NOTES.md
  - [ ] Commit WIP changes
  - [ ] Update US-XXX status
  - [ ] Document blockers (if any)

If work complete:
  - [ ] Update US-XXX status → "Ready for Review"
  - [ ] Ensure all commits pushed
  - [ ] Update CHANGELOG.md (if needed)
  - [ ] No handoff needed
```

**Session Start Checklist:**
```yaml
Always:
  - [ ] Read: CLAUDE.md
  - [ ] Bash: git status
  - [ ] Bash: git log --oneline -5

If continuing work:
  - [ ] Read: HANDOFF-NOTES.md (if exists)
  - [ ] Read: US-XXX.md
  - [ ] Review: Last commit messages

If new work:
  - [ ] Read: EPIC-XXX.md
  - [ ] Identify: Next US to work on
  - [ ] Read: US-XXX.md
```

### Between Agent Roles (BMad Method)

**When using BMad Method agents (Codex):**

```yaml
Claude Code (Analysis) → Codex (BMad PM):
  Handoff: Draft User Story
  Tool: Write US-XXX.md draft
  Next: Codex PM validates and finalizes

Codex (BMad Architect) → Claude Code (Implementation):
  Handoff: Architecture design docs
  Tool: Read architecture docs in Claude
  Next: Claude implements following design

Claude Code (Implementation) → Codex (BMad QA):
  Handoff: Code + commits
  Tool: Git repo state
  Next: Codex QA reviews using *review command
```

**Agent Mapping Reference:**
| Claude Code Mode | Codex BMad Agent | Purpose |
|------------------|------------------|---------|
| Analysis mode | bmad-analyst | Research, planning |
| Design mode | bmad-architect | Architecture design |
| Implementation | bmad-dev | Code implementation |
| Review mode | bmad-reviewer | Code review |
| Workflow mode | bmad-pm | Process coordination |

---

## Advanced Patterns

### Pattern 1: Multi-Session Feature Development

**Scenario:** Large feature requiring multiple sessions.

**Strategy:**
1. **Session 1 (ANALYSIS):** Create User Story
2. **Session 2 (FULL_TDD Part 1):** Implement core logic
3. **Session 3 (FULL_TDD Part 2):** Implement UI integration
4. **Session 4 (REVIEW + REFACTOR):** Polish and optimize

**Session Boundaries:**
```yaml
Use US-XXX subtasks:
  - [ ] Task 1: Core service logic
  - [ ] Task 2: UI integration
  - [ ] Task 3: Tests and validation

Complete one subtask per session
Commit between sessions
Use HANDOFF-NOTES.md
```

### Pattern 2: Parallel Work Streams

**Scenario:** Working on bug fix while designing new feature.

**Strategy:**
```yaml
Workflow A (HOTFIX): Bug fix in progress
  - Branch: hotfix/SAM-002-fix
  - Session: 20 minutes
  - Complete and merge

Workflow B (ANALYSIS): New feature design
  - Branch: feature/US-450-analysis
  - Session: 30 minutes
  - Continue later

Git branching:
  main
   ├── hotfix/SAM-002-fix (active)
   └── feature/US-450-analysis (paused)
```

**Session Management:**
- Use git branches to isolate work
- One workflow per session (no context switching)
- HANDOFF-NOTES.md per branch if needed

### Pattern 3: Emergency Context Switch

**Scenario:** Working on feature, production bug reported.

**Strategy:**
```yaml
1. Current State Snapshot:
   - Bash: git stash save "WIP: US-XXX partial implementation"
   - Write: Quick HANDOFF-NOTES.md

2. Switch to HOTFIX:
   - Bash: git checkout main
   - Bash: git checkout -b hotfix/emergency-fix
   - Execute HOTFIX workflow

3. Return to Feature:
   - Bash: git checkout feature/US-XXX
   - Bash: git stash pop
   - Read: HANDOFF-NOTES.md
   - Continue FULL_TDD workflow
```

---

## Cheat Sheet

### Quick Workflow Selection

| Situation | Workflow | Duration |
|-----------|----------|----------|
| "What should I build?" | ANALYSIS | 15-30 min |
| "Build new feature" | FULL_TDD | 30-90 min |
| "Production is broken" | HOTFIX | 10-30 min |
| "Code is messy" | REFACTOR | 15-30 min |
| "Need code review" | REVIEW | 15-30 min |
| "Fix the docs" | DOCUMENT | 5-20 min |

### Essential Commands

```bash
# Session Start
git status
git log --oneline -5

# Testing
pytest tests/path/to/test.py
pytest --cov=src --cov-report=html
pytest -m unit

# Quality
ruff check src
black src
pre-commit run --all-files

# Development
bash scripts/run_app.sh
make dev

# Session End
git add .
git commit -m "type(scope): description"
git push
```

### File Locations Quick Reference

```
User Stories:       docs/backlog/EPIC-XXX/US-XXX/US-XXX.md
Architecture:       docs/architectuur/
Reviews:            docs/reviews/<ID>-review.md
Refactor Log:       docs/refactor-log.md
Session Handoffs:   docs/backlog/EPIC-XXX/US-XXX/HANDOFF-NOTES.md
Tests:              tests/ (mirror src/ structure)
Source:             src/
```

---

## References

- **CLAUDE.md:** Project-specific instructions
- **UNIFIED_INSTRUCTIONS.md:** ~/.ai-agents/UNIFIED_INSTRUCTIONS.md
- **TDD_TO_DEPLOYMENT_WORKFLOW.md:** Full TDD workflow details
- **WORKFLOW_LIBRARY.md:** All available workflows
- **CANONICAL_LOCATIONS.md:** File organization rules

---

**Last Updated:** 2025-10-17
**Status:** Active
**Owner:** Development
**Next Review:** 2025-11-17
