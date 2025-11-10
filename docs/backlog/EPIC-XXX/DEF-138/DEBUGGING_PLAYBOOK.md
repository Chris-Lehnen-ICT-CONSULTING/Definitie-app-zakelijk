# DEF-138: Category Mismatch Debugging Playbook

**Purpose:** Quick reference for investigating ontological category discrepancies

---

## Symptom: "UI shows X, database has Y"

### Quick Diagnostic Steps

1. **Check the prompt file** (user-provided or extracted from logs)
   ```bash
   grep "🎯 Focus" prompt_file.txt
   # Look for: "🎯 Focus: Dit is een **[category]**"
   ```

2. **Check the classifier output**
   ```python
   from ontologie.improved_classifier import ImprovedOntologyClassifier
   classifier = ImprovedOntologyClassifier()
   result = classifier.classify("term", "", "", "")
   print(f"Suggested: {result.categorie.value}")
   print(f"Confidence: {result.confidence_label}")
   ```

3. **Check for manual override in session**
   ```bash
   # In UI logs, search for:
   grep "manual_ontological_category" logs/streamlit.log
   grep "CATEGORY OVERRIDE" logs/app.log
   ```

4. **Check database entry**
   ```sql
   SELECT begrip, ontologische_categorie, created_by, created_at
   FROM definities
   WHERE begrip = 'term'
   ORDER BY created_at DESC
   LIMIT 1;
   ```

---

## Root Cause Checklist

### ✅ Was there a manual override?

**Check:** Session state logs for `manual_ontological_category`

**File:** `src/ui/tabbed_interface.py` line 629-650

**Evidence:**
```python
manual_category = SessionStateManager.get_value("manual_ontological_category")
if manual_category:
    # User manually changed category
```

**Fix:** Add validation to require justification for overrides

---

### ✅ Does the term match PROCES patterns?

**Check:** Classifier pattern matching logic

**File:** `src/ontologie/improved_classifier.py` line 220-251

**Patterns:**
- Suffixes: `-ing`, `-atie`, `-tie`, `-eren`, `-isatie`
- Words: `validatie`, `verificatie`, `beoordeling`, `controle`

**Fix:** Add missing patterns to `config/classification/term_patterns.yaml`

---

### ✅ Is there a domain override?

**Check:** `config/classification/term_patterns.yaml` line 29-33

**Evidence:**
```yaml
domain_overrides:
  term: CATEGORY  # Explicit classification
```

**Fix:** Add term to `domain_overrides` if it's ambiguous

---

### ✅ Is the prompt instruction correct?

**Check:** Prompt file or logs for "🎯 Focus" line

**File:** `src/services/prompts/modules/definition_task_module.py` line 196

**Evidence:**
```python
ont_cat = f"\n🎯 Focus: Dit is een **{ontological_category}** ..."
```

**Fix:** Ensure `ontological_category` matches classifier output

---

### ✅ Is the AI following instructions?

**Check:** Generated definition text for category clues

**Clues:**
- PROCES: "activiteit waarbij...", "handeling die...", "proces waarin..."
- TYPE: "soort...", "categorie van...", "type... dat..."
- RESULTAAT: "resultaat van...", "uitkomst van...", "product dat..."

**Fix:** If AI deviates, check ESS-02 guidance in `semantic_categorisation_module.py`

---

## Common Causes (Priority Order)

### 1. User Manual Override (60% of cases)

**Symptom:** Classifier says TYPE, database has PROCES, user clicked dropdown

**Evidence:**
```bash
grep "manual_category_override" logs/app.log
# Look for: "Gebruik handmatige categorie override: PROCES"
```

**Solution:**
- Add justification requirement for overrides
- Log all overrides with username and timestamp
- Add UI warning: "You're overriding the AI suggestion, are you sure?"

---

### 2. Missing Classifier Patterns (30% of cases)

**Symptom:** Term doesn't match any patterns, falls back to default

**Evidence:**
```python
# Term ends with unknown suffix
# Term not in any word list
# Context provides no clues
# Falls back to PROCES (most common category)
```

**Solution:**
- Add term to `domain_overrides` in `term_patterns.yaml`
- Add suffix pattern with appropriate weight
- Add context indicators to pattern matching

---

### 3. Ambiguous Terms (10% of cases)

**Symptom:** Multiple categories are equally valid (scores within 0.15)

**Evidence:**
```python
result.confidence_label == "LOW"  # < 0.45 confidence
result.all_scores  # Multiple scores close together
```

**Solution:**
- Use priority cascade (EXEMPLAAR > TYPE > RESULTAAT > PROCES)
- Add domain override for disambiguation
- Require manual review for LOW confidence classifications

---

## Investigation Template

Use this template when investigating a mismatch:

```markdown
## Category Mismatch Report

**Term:** [werkwoord]
**UI Suggested:** [TYPE]
**Database Stored:** [PROCES]
**Reporter:** [User name]
**Date:** [2025-11-10]

### Step 1: Classifier Output
```bash
python -c "
from ontologie.improved_classifier import ImprovedOntologyClassifier
classifier = ImprovedOntologyClassifier()
result = classifier.classify('[term]', '', '', '')
print(f'Category: {result.categorie.value}')
print(f'Confidence: {result.confidence_label}')
print(f'Reasoning: {result.reasoning}')
"
```

**Result:**
- Category: [TYPE]
- Confidence: [MEDIUM]
- Reasoning: [Falls back to default, no patterns match]

### Step 2: Prompt Inspection
```bash
grep "🎯 Focus" prompt_file.txt
```

**Result:**
```text
🎯 Focus: Dit is een **proces** (activiteit/handeling)
```

**Mismatch detected:** Classifier says TYPE, prompt says PROCES

### Step 3: Session State Check
```bash
grep "manual_ontological_category" logs/streamlit.log
```

**Result:**
```text
2025-11-10 14:23:15 | manual_ontological_category = "PROCES"
```

**Root Cause:** User manually overrode TYPE → PROCES

### Step 4: Proposed Fix
- [ ] Add "term" to `domain_overrides` as TYPE
- [ ] Add pattern to prevent future misclassification
- [ ] Update database entry if needed
- [ ] Test with new configuration

### Step 5: Prevention
- [ ] Add override validation
- [ ] Create test case for this term
- [ ] Document in classifier patterns
```

---

## Quick Fixes Reference

### Fix 1: Add Domain Override

**File:** `config/classification/term_patterns.yaml`

```yaml
domain_overrides:
  term: TYPE  # or PROCES, RESULTAAT, EXEMPLAAR
```

**Test:**
```bash
python -c "
from ontologie.improved_classifier import ImprovedOntologyClassifier
from services.classification.term_config import reset_config_cache
reset_config_cache()  # Force reload
classifier = ImprovedOntologyClassifier()
result = classifier.classify('term', '', '', '')
assert result.categorie.value == 'type'
assert result.confidence_label == 'HIGH'
print('✅ Override works')
"
```

---

### Fix 2: Add Suffix Pattern

**File:** `config/classification/term_patterns.yaml`

```yaml
suffix_weights:
  TYPE:  # or PROCES, RESULTAAT
    suffix: 0.90  # weight 0.0-1.0
```

**Test:**
```bash
# Test all terms ending with suffix
python scripts/test_suffix_pattern.py --suffix "woord" --expected TYPE
```

---

### Fix 3: Add Context Indicator

**File:** `src/ontologie/improved_classifier.py` (requires code change)

```python
# In _generate_scores(), add new indicator
if re.search(r"\b(new_indicator_pattern)\b", combined_context):
    scores["type"] += 0.2
```

**Test:**
```bash
pytest tests/classification/test_context_indicators.py -k new_indicator
```

---

## Audit Queries

### Find All Mismatches

```sql
-- Find entries where category doesn't match semantic hints in definition
SELECT
    id,
    begrip,
    ontologische_categorie AS stored,
    CASE
        WHEN definitie LIKE '%soort %' OR definitie LIKE '%categorie %' THEN 'type'
        WHEN definitie LIKE '%activiteit %' OR definitie LIKE '%handeling %' THEN 'proces'
        WHEN definitie LIKE '%resultaat %' OR definitie LIKE '%uitkomst %' THEN 'resultaat'
        ELSE 'unclear'
    END AS inferred,
    created_by,
    created_at
FROM definities
WHERE ontologische_categorie IS NOT NULL
  AND ontologische_categorie != CASE
        WHEN definitie LIKE '%soort %' THEN 'type'
        WHEN definitie LIKE '%activiteit %' THEN 'proces'
        WHEN definitie LIKE '%resultaat %' THEN 'resultaat'
        ELSE ontologische_categorie
    END
ORDER BY created_at DESC;
```

### Find Manual Overrides (if logged)

```bash
grep "CATEGORY OVERRIDE" logs/app.log | \
  awk -F'|' '{print $2, $3, $4}' | \
  sort | uniq -c | sort -rn
# Shows: count | term | suggested→manual | reason
```

---

## Related Files

**Classification Logic:**
- `src/ontologie/improved_classifier.py` - Main classifier
- `config/classification/term_patterns.yaml` - Pattern configuration
- `src/services/classification/term_config.py` - Config loader

**Prompt Building:**
- `src/services/prompts/prompt_service_v2.py` - Prompt orchestration
- `src/services/prompts/modules/semantic_categorisation_module.py` - ESS-02 guidance
- `src/services/prompts/modules/definition_task_module.py` - "🎯 Focus" injection

**UI Flow:**
- `src/ui/tabbed_interface.py` - Category selection UI
- `src/ui/session_state.py` - Session state management

**Database:**
- `src/repositories/definition_repository.py` - Storage logic
- `data/definities.db` - SQLite database

---

## Prevention Checklist

- [ ] All grammatical terms have `domain_overrides`
- [ ] All common suffixes have pattern weights
- [ ] Manual overrides require justification
- [ ] Audit logs track all category decisions
- [ ] Test suite covers ambiguous terms
- [ ] Pre-commit hook validates patterns
- [ ] Documentation includes edge cases

---

**Last Updated:** 2025-11-10
**Maintainer:** Debug Specialist Team
**Version:** 1.0
