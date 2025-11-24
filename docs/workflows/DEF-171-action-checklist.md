# DEF-171 Action Checklist: Fix Prompt Bloat After DEF-126

**Root Cause:** Architectural debt from uncoordinated layer evolution
**Impact:** 3,810 tokens (36.3%) of duplication
**Target:** Reduce to 5,798 tokens (45% reduction)

---

## Phase 1: Stop the Bleeding (2 hours) ⏰ DO FIRST

### 1.1 Add Pre-Commit Hook for Token Budget
- [ ] Create `scripts/check_prompt_tokens.py`
  ```python
  """Check that prompt stays under token budget."""
  import tiktoken

  def check_token_budget(max_tokens=8000):
      # Build full prompt
      prompt = build_full_prompt()
      # Count tokens
      enc = tiktoken.get_encoding("cl100k_base")
      tokens = len(enc.encode(prompt))
      # Enforce limit
      assert tokens <= max_tokens, f"Prompt is {tokens} tokens (limit: {max_tokens})"
  ```
- [ ] Add to `.pre-commit-config.yaml`:
  ```yaml
  - id: prompt-token-budget
    name: Check prompt token budget
    entry: python scripts/check_prompt_tokens.py
    language: system
    pass_filenames: false
  ```
- [ ] Test: `pre-commit run prompt-token-budget --all-files`
- [ ] Verify fails if token budget exceeded

**Time estimate:** 45 minutes
**Risk:** LOW
**Blocker:** None

---

### 1.2 Add Integration Test for Duplication
- [ ] Create `tests/integration/test_prompt_architecture.py`
  ```python
  """Test prompt architecture integrity."""

  def test_no_cross_layer_duplication():
      """Verify static modules don't duplicate JSON module content."""
      # Build outputs from each layer
      static_output = get_static_module_outputs()  # Layer 1
      json_output = get_json_module_output()       # Layer 3

      # Detect semantic overlap
      overlap = detect_semantic_overlap(static_output, json_output)

      # Enforce <5% duplication threshold
      assert overlap < 5, f"Found {overlap}% duplication between layers"

  def test_prompt_token_budget():
      """Verify total prompt stays under 8,000 tokens."""
      prompt = build_full_prompt()
      tokens = count_tokens(prompt)
      assert tokens <= 8000, f"Prompt is {tokens} tokens (limit: 8000)"

  def test_layer_ownership():
      """Verify each rule has exactly ONE owner module."""
      rule_owners = get_rule_ownership_mapping()

      for rule_id, owners in rule_owners.items():
          assert len(owners) == 1, \
              f"Rule {rule_id} has multiple owners: {owners}"
  ```
- [ ] Implement helper functions:
  - `get_static_module_outputs()`
  - `get_json_module_output()`
  - `detect_semantic_overlap()`
  - `get_rule_ownership_mapping()`
- [ ] Run: `pytest tests/integration/test_prompt_architecture.py -v`
- [ ] Verify tests FAIL (detecting current duplication)

**Time estimate:** 60 minutes
**Risk:** LOW
**Blocker:** None

---

### 1.3 Create Architecture Documentation
- [ ] Create `docs/architectuur/PROMPT_SYSTEM_ARCHITECTURE.md`
- [ ] Document layer ownership matrix:
  ```markdown
  | Module | Owns | Does NOT Own |
  |--------|------|--------------|
  | GrammarModule | General grammar guidance | Specific VER rules |
  | OutputSpecificationModule | Output format specs | STR validation rules |
  | JSONBasedRulesModule | ALL 46 validation rules | Grammar/format guidance |
  ```
- [ ] Define deprecation policy
- [ ] Specify change coordination process
- [ ] Add to `docs/INDEX.md`

**Time estimate:** 15 minutes
**Risk:** NONE (documentation only)
**Blocker:** None

---

## Phase 2: Heal the Wounds (4 hours) ⏰ DO NEXT

### 2.1 Remove Static Duplication (1,200 tokens)

#### 2.1.1 Clean GrammarModule
- [ ] Open `src/services/prompts/modules/grammar_module.py`
- [ ] Identify VER-01/02/03 equivalents (lines ~27-31, ~36-44, ~46-61)
- [ ] Remove overlapping content:
  ```diff
  - 🔸 **Enkelvoud als standaard**
  - - Gebruik enkelvoud tenzij het begrip specifiek een meervoud aanduidt
  - - Bij twijfel: gebruik enkelvoud
  -   ✅ proces (niet: processen)
  ```
- [ ] Keep ONLY general grammar guidance (not specific rules)
- [ ] Update docstring: "General grammar guidance - does NOT include VER rules"
- [ ] Run tests: `pytest tests/unit/test_grammar_module.py -v`

**Time estimate:** 30 minutes
**Risk:** LOW (VER rules still in JSON module)
**Blocker:** None

---

#### 2.1.2 Clean OutputSpecificationModule
- [ ] Open `src/services/prompts/modules/output_specification_module.py`
- [ ] Identify STR rule equivalents
- [ ] Remove overlapping structure guidance
- [ ] Keep ONLY output format specs (not validation rules)
- [ ] Update docstring
- [ ] Run tests: `pytest tests/unit/test_output_specification_module.py -v`

**Time estimate:** 30 minutes
**Risk:** LOW
**Blocker:** None

---

#### 2.1.3 Clean SemanticCategorisationModule
- [ ] Open `src/services/prompts/modules/semantic_categorisation_module.py`
- [ ] Identify ESS-02 equivalents (ontological category determination)
- [ ] Remove overlapping content
- [ ] Keep ONLY category mapping logic (not validation)
- [ ] Update docstring
- [ ] Run tests: `pytest tests/unit/test_semantic_categorisation_module.py -v`

**Time estimate:** 30 minutes
**Risk:** MEDIUM (ontological category is critical)
**Blocker:** Verify UI provides category BEFORE cleanup

---

### 2.2 Remove Validation Content (1,170 tokens)

#### 2.2.1 Audit Current Prompt
- [ ] Generate current prompt: `python scripts/generate_prompt.py > current_prompt.txt`
- [ ] Find all "Toetsvraag:" sections: `grep -n "Toetsvraag:" current_prompt.txt`
- [ ] Count: Should find 39 instances
- [ ] Document line numbers for removal

**Time estimate:** 15 minutes
**Risk:** NONE (audit only)
**Blocker:** None

---

#### 2.2.2 Remove from JSON Module Logic
- [ ] Open `src/services/prompts/modules/json_based_rules_module.py`
- [ ] Find `_format_rule()` method (lines 183-240)
- [ ] Current logic:
  ```python
  instruction = self._get_instruction_for_rule(regel_key)
  if instruction:
      lines.append(f"- **Instructie:** {instruction}")
  else:
      # Fallback: gebruik originele toetsvraag
      toetsvraag = regel_data.get("toetsvraag", "")
      if toetsvraag:
          lines.append(f"- Toetsvraag: {toetsvraag}")
  ```
- [ ] Change to:
  ```python
  instruction = self._get_instruction_for_rule(regel_key)
  if instruction:
      lines.append(f"- **Instructie:** {instruction}")
  # REMOVED: toetsvraag fallback (validation is post-generation)
  ```
- [ ] Run tests: `pytest tests/unit/test_json_based_rules_module.py -v`
- [ ] Verify prompt no longer has "Toetsvraag:" sections

**Time estimate:** 20 minutes
**Risk:** LOW (toetsvraag still in JSON for validation module)
**Blocker:** None

---

### 2.3 Update JSON Files for Consistency

#### 2.3.1 Add "instructie" Field to JSON Schema
- [ ] Open `config/toetsregels/regels/ARAI.json`
- [ ] Current structure:
  ```json
  {
    "ARAI-01": {
      "naam": "geen werkwoord als kern",
      "uitleg": "De kern van de definitie...",
      "toetsvraag": "Is de kern...",
      "goede_voorbeelden": [...],
      "foute_voorbeelden": [...]
    }
  }
  ```
- [ ] Add "instructie" field:
  ```json
  {
    "ARAI-01": {
      "naam": "geen werkwoord als kern",
      "uitleg": "De kern van de definitie...",
      "instructie": "Begin de definitie met een zelfstandig naamwoord...",
      "toetsvraag": "Is de kern...",  # DEPRECATED - kept for validation
      "goede_voorbeelden": [...],
      "foute_voorbeelden": [...]
    }
  }
  ```
- [ ] Repeat for all 8 rule files (ARAI, CON, ESS, INT, SAM, STR, VER, DUP)
- [ ] Add schema validation: `scripts/validate_rule_json_schema.py`

**Time estimate:** 90 minutes
**Risk:** LOW
**Blocker:** instruction_map already exists in code (can copy)

---

#### 2.3.2 Update JSON Module to Use "instructie" Field
- [ ] Open `src/services/prompts/modules/json_based_rules_module.py`
- [ ] Update `_format_rule()`:
  ```python
  # Try instruction field from JSON first (NEW)
  instruction = regel_data.get("instructie")

  # Fallback to instruction_map if JSON doesn't have it yet
  if not instruction:
      instruction = self._get_instruction_for_rule(regel_key)

  # Emit instruction if available
  if instruction:
      lines.append(f"- **Instructie:** {instruction}")
  ```
- [ ] Plan to deprecate `instruction_map` after JSON migration complete

**Time estimate:** 15 minutes
**Risk:** LOW
**Blocker:** 2.3.1 must complete first

---

### 2.4 Verify with Tests

- [ ] Run full test suite: `pytest -v`
- [ ] Run integration tests: `pytest tests/integration/ -v`
- [ ] Verify `test_no_cross_layer_duplication()` PASSES
- [ ] Verify `test_prompt_token_budget()` PASSES
- [ ] Generate new prompt: `python scripts/generate_prompt.py > new_prompt.txt`
- [ ] Count tokens: `python scripts/count_tokens.py new_prompt.txt`
- [ ] Verify: tokens <= 8,000
- [ ] Compare quality:
  - [ ] Generate 5 definitions with OLD prompt
  - [ ] Generate 5 definitions with NEW prompt
  - [ ] Verify quality maintained or improved

**Time estimate:** 45 minutes
**Risk:** MEDIUM (regression in quality)
**Blocker:** All cleanup tasks must complete first

---

## Phase 3: Prevent Recurrence (future sprint) 🔮

### 3.1 Implement Layer Responsibility Contract
- [ ] Create `src/services/prompts/contracts/layer_contract.py`
  ```python
  from typing import Protocol, Set

  class PromptLayer(Protocol):
      """Contract for all prompt generation layers."""

      def get_content_type(self) -> ContentType:
          """Return STATIC, DYNAMIC, or TEMPLATE."""

      def get_content_domain(self) -> Set[str]:
          """Return set of content domains (e.g., {"VER", "ARAI"})."""

      def check_overlap_with(self, other: PromptLayer) -> OverlapReport:
          """Detect content overlap with another layer."""
  ```
- [ ] Implement for all modules
- [ ] Add enforcement in PromptOrchestrator

**Time estimate:** 3 hours
**Risk:** LOW
**Blocker:** None

---

### 3.2 Set Up Nightly Health Checks
- [ ] Create `.github/workflows/prompt-health.yml`
  ```yaml
  name: Prompt System Health Check
  on:
    schedule:
      - cron: '0 2 * * *'  # 2 AM daily
  jobs:
    check-prompt-health:
      runs-on: ubuntu-latest
      steps:
        - name: Checkout code
        - name: Set up Python
        - name: Check token budget
          run: python scripts/check_prompt_tokens.py
        - name: Detect duplication
          run: pytest tests/integration/test_prompt_architecture.py
        - name: Validate coverage
          run: python scripts/check_rule_coverage.py
        - name: Report results
          run: python scripts/report_prompt_health.py
  ```
- [ ] Create reporting script
- [ ] Configure Slack/email notifications

**Time estimate:** 2 hours
**Risk:** LOW
**Blocker:** CI/CD pipeline access

---

### 3.3 Auto-Generate Architecture Diagrams
- [ ] Create `scripts/generate_prompt_architecture_diagram.py`
  ```python
  """Generate visual diagram of prompt system layers."""
  import graphviz

  def generate_layer_diagram():
      # Parse modules to extract relationships
      # Generate GraphViz diagram
      # Output PNG to docs/architectuur/
  ```
- [ ] Add to pre-commit hook
- [ ] Integrate with documentation

**Time estimate:** 2 hours
**Risk:** LOW
**Blocker:** None

---

## Success Criteria

### Phase 1 (Stop the Bleeding)
- [ ] Pre-commit hook enforces 8,000 token limit
- [ ] Integration tests detect duplication
- [ ] Architecture documentation exists

### Phase 2 (Heal the Wounds)
- [ ] Prompt tokens: 10,508 → 5,798 (45% reduction)
- [ ] Duplication: 36.3% → <5%
- [ ] All tests passing
- [ ] Quality maintained (verified with smoke tests)

### Phase 3 (Prevent Recurrence)
- [ ] Layer contracts implemented
- [ ] Nightly health checks running
- [ ] Auto-generated diagrams in docs

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Quality regression | MEDIUM | HIGH | Run smoke tests before/after |
| Breaking changes | LOW | HIGH | Comprehensive test coverage |
| Token budget violation | LOW | MEDIUM | Pre-commit hook prevents |
| Incomplete cleanup | MEDIUM | MEDIUM | Integration tests verify |

---

## Rollback Plan

If quality regresses after cleanup:
1. Git revert to commit before cleanup
2. Re-run smoke tests to verify restoration
3. Analyze which specific change caused regression
4. Apply more granular cleanup approach

---

## Timeline

```
Week 1:
  Day 1-2: Phase 1 (Stop the Bleeding) - 2 hours
  Day 3-5: Phase 2 (Heal the Wounds) - 4 hours

Week 2:
  Day 1-2: Verification and smoke tests
  Day 3-5: Documentation updates

Future Sprint:
  Week X: Phase 3 (Prevent Recurrence) - 7 hours
```

---

## Notes

- All file paths are absolute from project root
- Token counts measured with tiktoken (cl100k_base encoding)
- Test coverage must remain ≥60% throughout changes
- Document all architectural decisions in ADR format

---

*Checklist created by Debug Specialist*
*Companion to: DEF-171-root-cause-analysis.md*
*Status: READY FOR EXECUTION*
