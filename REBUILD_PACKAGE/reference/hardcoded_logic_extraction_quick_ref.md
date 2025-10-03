---
id: EPIC-026-LOGIC-EXTRACTION-QUICK-REF
epic: EPIC-026
phase: 1
created: 2025-10-02
owner: senior-developer
status: draft
---

# Hardcoded Logic Extraction - Quick Reference Card

**For:** Developers implementing logic extraction
**Full Plan:** `hardcoded_logic_extraction_plan.md` (61KB)
**Summary:** `hardcoded_logic_extraction_summary.md` (9KB)

---

## What Are We Doing?

**Extracting 250+ LOC of hardcoded business logic to YAML configs**

**Why?**
- Hardcoded logic blocks god object refactoring
- 93 instances of duplicated patterns
- NOT configurable, NOT maintainable

---

## The Numbers

| Category | Count | Duplication | LOC |
|----------|-------|-------------|-----|
| Rule Reasoning | 13 rules | 0% (single location) | 70 LOC |
| Ontological Patterns | 42 patterns | **100%** (3 methods!) | 180 LOC |
| **TOTAL** | 55 items | 42 duplicates | **250 LOC** |

---

## Timeline

```
Week 1: Rule Reasoning        Week 2: Pattern Matching
├── Day 1-2: Config schema     ├── Day 6-7: Pattern schema
├── Day 3-4: Service impl      ├── Day 8-9: Service impl
└── Day 5: Integration         └── Day 10: Cleanup
```

**Total:** 2 weeks (10 working days)

---

## Deliverables Checklist

**Week 1 (Rule Reasoning):**
- [ ] `config/validation/rule_reasoning_config.yaml` (13 rules)
- [ ] `src/config/config_loader.py` (Pydantic validation)
- [ ] `src/services/validation/rule_reasoning_service.py`
- [ ] `tests/config/test_config_loader.py` (100% coverage)
- [ ] `tests/services/validation/test_rule_reasoning_service.py` (100% coverage)
- [ ] `tests/integration/test_logic_extraction_backward_compat.py` (11+ cases)
- [ ] Updated `definition_generator_tab._build_pass_reason()` (thin wrapper)

**Week 2 (Pattern Matching):**
- [ ] `config/ontology/category_patterns.yaml` (42 patterns, ZERO duplication!)
- [ ] `src/services/ontology/ontological_pattern_service.py`
- [ ] `tests/services/ontology/test_ontological_pattern_service.py` (100% coverage)
- [ ] Updated `tabbed_interface._generate_category_reasoning()` (thin wrapper)
- [ ] Updated `tabbed_interface._get_category_scores()` (thin wrapper)
- [ ] Updated `tabbed_interface._legacy_pattern_matching()` (thin wrapper)
- [ ] **REMOVE:** 150 LOC hardcoded patterns from 3 methods

---

## File Structure

```
config/
├── validation/
│   └── rule_reasoning_config.yaml       # NEW (13 rules)
└── ontology/
    └── category_patterns.yaml           # NEW (42 patterns)

src/
├── config/
│   └── config_loader.py                 # NEW (loader + validation)
└── services/
    ├── validation/
    │   └── rule_reasoning_service.py    # NEW
    └── ontology/
        └── ontological_pattern_service.py  # NEW

tests/
├── config/
│   └── test_config_loader.py            # NEW
├── services/
│   ├── validation/
│   │   └── test_rule_reasoning_service.py  # NEW
│   └── ontology/
│       └── test_ontological_pattern_service.py  # NEW
└── integration/
    └── test_logic_extraction_backward_compat.py  # NEW
```

---

## Config Example (Rule Reasoning)

```yaml
# config/validation/rule_reasoning_config.yaml

schema_version: "1.0.0"

defaults:
  unknown_rule: "Geen issues gemeld door validator."

rules:
  VAL-EMP-001:
    display_name: "Lege definitie is ongeldig"
    pass_reason_template: "Niet leeg (tekens={chars} > 0)."
    logic:
      type: "threshold_check"
      metric: "chars"
      operator: ">"
      threshold: 0
    metrics_required:
      - chars
    fallback: "Tekst is aanwezig."

  VAL-LEN-001:
    display_name: "Minimale lengte check"
    pass_reason_template: "Lengte OK: {words} woorden ≥ 5 en {chars} tekens ≥ 15."
    logic:
      type: "multi_threshold_check"
      conditions:
        - metric: "words"
          operator: ">="
          threshold: 5
        - metric: "chars"
          operator: ">="
          threshold: 15
      combinator: "and"
    metrics_required:
      - words
      - chars
```

---

## Config Example (Patterns)

```yaml
# config/ontology/category_patterns.yaml

schema_version: "1.0.0"

detection:
  case_sensitive: false
  match_mode: "substring"
  scoring:
    method: "pattern_count"

categories:
  proces:
    display_name: "Proces"
    all_patterns:
      - "atie"
      - "eren"
      - "ing"
      - "verificatie"
      - "authenticatie"
      - "validatie"
      # ... 15 patterns total

  type:
    display_name: "Type"
    all_patterns:
      - "bewijs"
      - "document"
      - "middel"
      # ... 10 patterns total
```

---

## Code Migration Pattern

### BEFORE (Hardcoded)

```python
def _build_pass_reason(self, rule_id: str, text: str, begrip: str) -> str:
    rid = ensure_string(rule_id).upper()
    m = self._compute_text_metrics(text)
    w, c = m.get("words", 0), m.get("chars", 0)

    if rid == "VAL-EMP-001":
        return f"Niet leeg (tekens={c} > 0)." if c > 0 else ""
    if rid == "VAL-LEN-001":
        return f"Lengte OK: {w} woorden ≥ 5 en {c} tekens ≥ 15." if (w >= 5 and c >= 15) else ""
    # ... 11 more hardcoded rules (70 lines total)
    return "Geen issues gemeld door validator."
```

### AFTER (Data-Driven)

```python
def _build_pass_reason(self, rule_id: str, text: str, begrip: str) -> str:
    """Thin wrapper - delegates to RuleReasoningService."""
    service = get_rule_reasoning_service()
    return service.build_pass_reason(rule_id, text, begrip)
```

**Result:**
- 70 LOC → 5 LOC (**-65 LOC**)
- Logic now in config (easily editable!)
- Service is reusable and testable

---

## Testing Checklist

**Config Validation:**
- [ ] YAML syntax valid
- [ ] Schema validation passes (Pydantic)
- [ ] All 13 rules present
- [ ] All 42 patterns present (zero duplication!)

**Service Tests (100% coverage):**
- [ ] Config loading works
- [ ] Config caching works
- [ ] Each rule logic works correctly
- [ ] Pattern matching works correctly
- [ ] Edge cases handled

**Backward Compatibility (CRITICAL!):**
- [ ] All 13 rules: old vs new identical output
- [ ] All 42 patterns: old vs new identical output
- [ ] Parametrized tests cover all cases
- [ ] Integration tests pass (zero regressions)

**Performance:**
- [ ] Config loading: <100ms (first load)
- [ ] Config caching: <1ms (subsequent)
- [ ] Rule reasoning: <0.1ms per call
- [ ] Pattern matching: <1ms per begrip
- [ ] Overall overhead: <10%

---

## Rollback Plan

**If tests fail or behavior changes:**

1. **Quick Fix (30 min max)**
   - Fix config syntax errors
   - Fix template errors
   - Fix logic evaluator bugs

2. **Rollback (if quick fix fails)**
   ```bash
   # Revert commits
   git revert <commit-hash>

   # Verify rollback
   pytest -q

   # Confirm old behavior restored
   ```

3. **Post-Rollback**
   - Root cause analysis
   - Update plan
   - Schedule retry

**Rollback is EASY because:**
- ✅ Thin wrapper approach
- ✅ Old methods preserved
- ✅ Git branches
- ✅ Fast tests

---

## Common Pitfalls & Solutions

### Pitfall 1: YAML Syntax Errors

**Problem:** Invalid YAML breaks config loading

**Solution:**
```bash
# Validate YAML before committing
python -c "import yaml; yaml.safe_load(open('config/validation/rule_reasoning_config.yaml'))"
```

**Prevention:**
- Use YAML linter in IDE
- Schema validation catches errors early

### Pitfall 2: Template Formatting Errors

**Problem:** Template has wrong placeholders

**Solution:**
```python
# Template uses {chars}, but metric is "characters"
# FIX: Ensure metrics_required matches template placeholders

# BAD:
pass_reason_template: "Tekens={chars}"
metrics_required: ["characters"]  # MISMATCH!

# GOOD:
pass_reason_template: "Tekens={chars}"
metrics_required: ["chars"]  # MATCH!
```

### Pitfall 3: Pattern Duplication Creeps Back

**Problem:** Developer adds pattern to 1 method, forgets others

**Solution:**
```python
# PREVENT: Remove ALL hardcoded patterns from code
# ONLY source: config/ontology/category_patterns.yaml

# If you need to add a pattern:
# 1. Add to YAML config (single location)
# 2. Reload config (or restart app)
# 3. NEVER edit code!
```

### Pitfall 4: Backward Compat Tests Fail

**Problem:** New service produces different output

**Solution:**
```python
# DEBUG: Compare old vs new output
old_result = tab._build_pass_reason("VAL-EMP-001", text, begrip)
new_result = service.build_pass_reason("VAL-EMP-001", text, begrip)

print(f"Old: {repr(old_result)}")
print(f"New: {repr(new_result)}")
print(f"Match: {old_result == new_result}")

# Find diff:
import difflib
diff = list(difflib.unified_diff([old_result], [new_result]))
print("\n".join(diff))
```

### Pitfall 5: Performance Regression

**Problem:** Config loading slows down UI

**Solution:**
```python
# ENSURE: Config is cached (loaded once)
class ConfigLoader:
    def __init__(self):
        self._cache = {}  # Cache here!

    def load_rule_reasoning_config(self):
        if "rule_reasoning" in self._cache:
            return self._cache["rule_reasoning"]  # Fast!
        # ... load and cache
```

---

## Daily Standup Template

```markdown
### Day X Progress

**Completed:**
- [ ] Config schema designed
- [ ] Service implemented
- [ ] Tests written (X% coverage)

**In Progress:**
- [ ] Integration with UI layer
- [ ] Backward compat validation

**Blockers:**
- None / [describe blocker]

**Next:**
- [ ] [next task]

**Risk Updates:**
- No new risks / [describe risk]
```

---

## Acceptance Criteria

**Week 1 (Rule Reasoning) DONE when:**
- ✅ All 13 rules in YAML config
- ✅ Config loader with Pydantic validation
- ✅ RuleReasoningService implemented
- ✅ 100% test coverage (unit + integration)
- ✅ Backward compat tests pass (11+ cases)
- ✅ Performance overhead <10%
- ✅ Integration tests pass (zero regressions)
- ✅ Code review approved
- ✅ Merged to main

**Week 2 (Pattern Matching) DONE when:**
- ✅ All 42 patterns in YAML config (ZERO duplication!)
- ✅ OntologicalPatternService implemented
- ✅ 100% test coverage
- ✅ 3 UI methods updated (thin wrappers)
- ✅ 150 LOC hardcoded patterns REMOVED
- ✅ Backward compat tests pass
- ✅ Performance overhead <10%
- ✅ Integration tests pass (zero regressions)
- ✅ Code review approved
- ✅ Merged to main

**Both Weeks DONE when:**
- ✅ Zero hardcoded business logic in UI layer
- ✅ All logic in config files
- ✅ Services are data-driven
- ✅ EPIC-026 Phase 2 can proceed

---

## Commands Cheat Sheet

```bash
# Validate YAML configs
python -c "import yaml; yaml.safe_load(open('config/validation/rule_reasoning_config.yaml'))"
python -c "import yaml; yaml.safe_load(open('config/ontology/category_patterns.yaml'))"

# Run config loader tests
pytest tests/config/test_config_loader.py -v

# Run service tests
pytest tests/services/validation/test_rule_reasoning_service.py -v
pytest tests/services/ontology/test_ontological_pattern_service.py -v

# Run backward compat tests (CRITICAL!)
pytest tests/integration/test_logic_extraction_backward_compat.py -v

# Run all tests
pytest -q

# Check coverage
pytest --cov=src/config --cov=src/services/validation --cov=src/services/ontology --cov-report=term-missing

# Performance benchmark
pytest tests/performance/test_logic_extraction_performance.py -v

# Lint & format
ruff check src/config src/services/validation src/services/ontology
black src/config src/services/validation src/services/ontology
```

---

## File Sizes (for reference)

| File | LOC | Purpose |
|------|-----|---------|
| `rule_reasoning_config.yaml` | ~200 | 13 rules × ~15 lines |
| `category_patterns.yaml` | ~100 | 42 patterns × ~2 lines |
| `config_loader.py` | ~150 | Loader + validation |
| `rule_reasoning_service.py` | ~150 | Service + evaluators |
| `ontological_pattern_service.py` | ~100 | Service + scoring |
| **TOTAL NEW CODE** | ~700 LOC | Clean, testable, reusable |
| **REMOVED CODE** | ~250 LOC | Hardcoded, duplicated |
| **NET** | +450 LOC | Better architecture! |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Hardcoded Logic** | 0 LOC | Manual code review |
| **Pattern Duplication** | 0 instances | YAML has 42 patterns (single source) |
| **Test Coverage** | 100% | pytest --cov |
| **Backward Compat** | 100% | All parametrized tests pass |
| **Performance Overhead** | <10% | Benchmark tests |
| **Config Validation** | 100% | Pydantic validation |
| **Integration Regressions** | 0 | Integration test suite |

---

## Links to Full Documentation

- **Full Plan:** `hardcoded_logic_extraction_plan.md` (61KB, 8 parts)
- **Summary:** `hardcoded_logic_extraction_summary.md` (9KB, TL;DR)
- **Decision Tree:** `hardcoded_logic_extraction_decision_tree.md` (visual framework)
- **This Quick Ref:** `hardcoded_logic_extraction_quick_ref.md` (developer reference)

---

## Contact & Questions

**Owner:** Senior Developer
**Reviewer:** Code Architect (EPIC-026 owner)
**Questions:** Slack #epic-026-refactoring channel
**Issues:** Tag with `epic-026` and `logic-extraction`

---

**Print this card and keep it handy during implementation!**

**Version:** 1.0.0
**Last Updated:** 2025-10-02
