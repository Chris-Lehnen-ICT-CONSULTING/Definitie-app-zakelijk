# Quick Fix Checklist - DEF-138 Bug Hunt

**Use this checklist to fix bugs in priority order**

---

## ✅ TODAY'S FIXES (3-4 hours)

### 🔴 BUG-001: False Positive - "woordvoerder"

**Status:** [ ] Not Started | [ ] In Progress | [ ] Testing | [ ] Done

**Steps:**

1. [ ] **Update YAML schema** (30 min)
   - File: `config/classification/term_patterns.yaml`
   - Add exclusions for -woord, -naam, -boek patterns
   ```yaml
   TYPE:
     woord:
       weight: 0.70
       exclusions:
         - "woordvoerder"
         - "woordbreuk"
     naam:
       weight: 0.65
       exclusions:
         - "naamsverminking"
         - "naamgeving"
   ```

2. [ ] **Update TermPatternConfig** (30 min)
   - File: `src/services/classification/term_config.py`
   - Add `get_suffix_data()` method
   - Support both float and dict format

3. [ ] **Update pattern matching** (30 min)
   - File: `src/ontologie/improved_classifier.py:230-245`
   - Add exclusion check before pattern match
   ```python
   weight, exclusions = self.config.get_suffix_data(category_upper, suffix)
   if begrip_lower in exclusions:
       continue
   ```

4. [ ] **Add tests** (30 min)
   - File: `tests/ontologie/test_classifier_exclusions.py`
   - Test werkwoord → TYPE (correct)
   - Test woordvoerder → PROCES (fixed)

5. [ ] **Run regression tests** (15 min)
   ```bash
   pytest tests/ontologie/ -v
   ```

6. [ ] **Manual QA** (15 min)
   - Test in UI: "werkwoord", "woordvoerder", "handboek", "voornaam"

**Time Budget:** 2.5 hours

---

### 🟠 BUG-004: Empty String Validation

**Status:** [ ] Not Started | [ ] In Progress | [ ] Testing | [ ] Done

**Steps:**

1. [ ] **Add validation** (10 min)
   - File: `src/ontologie/improved_classifier.py:149`
   ```python
   def classify(self, begrip: str, ...) -> ClassificationResult:
       if not begrip or not begrip.strip():
           raise ValueError("Cannot classify empty or whitespace-only begrip")
       begrip_lower = begrip.lower().strip()
       # ... rest
   ```

2. [ ] **Add test** (10 min)
   - File: `tests/ontologie/test_classifier_edge_cases.py`
   ```python
   def test_empty_string_raises_error():
       classifier = ImprovedOntologyClassifier()
       with pytest.raises(ValueError, match="Cannot classify empty"):
           classifier.classify("")
   ```

3. [ ] **Update UI error handling** (10 min)
   - File: `src/ui/tabbed_interface.py:268-277`
   - Ensure ValueError is caught and shown to user

**Time Budget:** 30 minutes

---

## ✅ THIS WEEK'S FIXES (2 hours)

### 🟠 BUG-003: Division by Zero Optimization

**Status:** [ ] Not Started | [ ] In Progress | [ ] Testing | [ ] Done

**Steps:**

1. [ ] **Optimize max() call** (15 min)
   - File: `src/ontologie/improved_classifier.py:327`
   ```python
   score_values = list(scores.values())
   max_score = max(score_values) if score_values and max(score_values) > 0 else 1.0
   ```

2. [ ] **Add edge case test** (15 min)
   ```python
   def test_all_zero_scores():
       # When all patterns score 0.0
       result = classifier.classify("xyz123")
       assert result.confidence == 0.0
   ```

**Time Budget:** 30 minutes

---

### 🟡 BUG-008: Document Weight Choices

**Status:** [ ] Not Started | [ ] In Progress | [ ] Testing | [ ] Done

**Steps:**

1. [ ] **Add comments to YAML** (15 min)
   - File: `config/classification/term_patterns.yaml:71-76`
   ```yaml
   # Compound word patterns - DEF-138 fix
   # Weights chosen based on semantic strength:
   # - 0.70: Strong TYPE signal (woord, boek) - grammatical/reference terms
   # - 0.65: Moderate TYPE signal (naam, lijst) - less consistent
   woord: 0.70
   naam: 0.65
   ```

**Time Budget:** 15 minutes

---

### 🟡 BUG-007: SQL Injection Prevention

**Status:** [ ] Not Started | [ ] In Progress | [ ] Testing | [ ] Done

**Steps:**

1. [ ] **Add table validation** (15 min)
   - File: `src/database/migrate_database.py:414`
   ```python
   ALLOWED_TABLES = {"definities", "synoniemen", "voorbeelden"}
   if table not in ALLOWED_TABLES:
       raise ValueError(f"Invalid table: {table}")
   c = conn.execute(f"PRAGMA table_info({table})")
   ```

**Time Budget:** 15 minutes

---

## ✅ NEXT SPRINT FIXES (13-24 hours)

### 🟡 BUG-006: Standardize YAML Loading

**Status:** [ ] Not Started | [ ] In Progress | [ ] Testing | [ ] Done

**Steps:**

1. [ ] **Create helper function** (1 hour)
   - File: `src/utils/yaml_loader.py` (new file)
   ```python
   def load_yaml_config(path: Path, description: str = "config") -> dict:
       if not path.exists():
           raise FileNotFoundError(f"{description} not found: {path}")
       # ... load with error handling
   ```

2. [ ] **Refactor 11 call sites** (1-2 hours)
   - Replace raw yaml.safe_load with helper

**Time Budget:** 2-3 hours

---

### 🟢 BUG-010: Unicode Test Coverage

**Status:** [ ] Not Started | [ ] In Progress | [ ] Testing | [ ] Done

**Steps:**

1. [ ] **Add test cases** (30 min)
   ```python
   def test_dutch_diacritics():
       assert classifier.classify("bëloning").categorie
       assert classifier.classify("coördinatie").categorie
   ```

**Time Budget:** 30 minutes

---

### 🟡 BUG-005: Exception Handling Audit (ONGOING)

**Status:** [ ] Not Started | [ ] In Progress | [ ] Testing | [ ] Done

**Steps:**

1. [ ] **Audit phase 1** - Critical paths (4 hours)
   - Review exception handling in:
     - `src/ontologie/` (classifier)
     - `src/services/validation/` (validation)
     - `src/database/` (database access)

2. [ ] **Audit phase 2** - UI components (3 hours)
   - Review exception handling in:
     - `src/ui/components/` (100+ instances)

3. [ ] **Audit phase 3** - Services (3 hours)
   - Review exception handling in:
     - `src/services/` (50+ instances)

**Time Budget:** 10-20 hours (ongoing)

---

## Testing Checklist

After each fix, run:

### Unit Tests
```bash
# Test classifier
pytest tests/ontologie/ -v

# Test all services
pytest tests/services/ -v

# Full test suite
pytest -q
```

### Manual QA
```bash
# Start app
bash scripts/run_app.sh

# Test cases:
1. Enter "werkwoord" → Should classify as TYPE
2. Enter "woordvoerder" → Should classify as PROCES (fixed!)
3. Enter "" (empty) → Should show error (fixed!)
4. Enter "bëloning" → Should handle unicode correctly
```

### Regression Check
```bash
# Run smoke tests
pytest -m smoke

# Run full validation suite
make validation-status
```

---

## Commit Messages

Use conventional commits:

```bash
# BUG-001
git commit -m "fix(classifier): add exclusion patterns to prevent false positives

- Add exclusion list support to term_patterns.yaml
- Extend TermPatternConfig with get_suffix_data()
- Update pattern matching to check exclusions
- Add test cases for woordvoerder, werkwoord

Fixes: BUG-138-001
Related: DEF-138"

# BUG-004
git commit -m "fix(classifier): validate empty string input

- Raise ValueError for empty/whitespace begrip
- Add test case for empty string validation
- Update UI error handling for ValueError

Fixes: BUG-138-004"

# BUG-003
git commit -m "perf(classifier): optimize max() call in score normalization

- Cache score_values to avoid duplicate max() call
- Add edge case test for all-zero scores

Fixes: BUG-138-003"
```

---

## Success Criteria

Before marking DONE:

### BUG-001
- [ ] ✅ `woordvoerder` → PROCES (not TYPE)
- [ ] ✅ `werkwoord` → TYPE (not broken)
- [ ] ✅ All existing tests pass
- [ ] ✅ New exclusion tests pass

### BUG-004
- [ ] ✅ Empty string raises ValueError
- [ ] ✅ Whitespace-only raises ValueError
- [ ] ✅ UI shows user-friendly error message

### BUG-003
- [ ] ✅ max() called only once
- [ ] ✅ Edge case tests pass
- [ ] ✅ No performance regression

---

## Monitoring (48 Hours After Deploy)

### Logs to Watch

```bash
# Classification errors
grep "Ontologische classificatie gefaald" logs/*.log

# Validation failures
grep "ERROR" logs/*.log | grep -i "classificat"

# Performance issues
grep "SLOW" logs/*.log
```

### Metrics to Track

- [ ] Classification success rate: >95%
- [ ] Average confidence score: >0.60
- [ ] False positive rate: <5%
- [ ] Response time: <500ms

---

## Rollback Plan

If critical issues emerge:

1. **Revert BUG-001 fix:**
   ```bash
   git revert <commit-hash>
   # Removes exclusions, falls back to old behavior
   ```

2. **Disable validation (BUG-004):**
   ```python
   # Comment out ValueError raise
   # if not begrip or not begrip.strip():
   #     raise ValueError(...)
   ```

3. **Restart app:**
   ```bash
   pkill -f streamlit
   bash scripts/run_app.sh
   ```

---

## Questions / Issues

**Who to contact:**
- Classification issues: @architect
- Testing issues: @tester
- Deployment issues: @devops

**Slack channels:**
- #def-138-bug-fixes
- #definitie-agent-dev

---

**Created:** 2025-11-10
**Last Updated:** 2025-11-10
**Owner:** Debug Specialist
**Status:** Ready for implementation
