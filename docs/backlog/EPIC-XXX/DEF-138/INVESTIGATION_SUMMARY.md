# DEF-138: Investigation Summary - Category Mismatch Bug

**Date:** 2025-11-10
**Status:** ✅ Root Cause Identified
**Severity:** HIGH (Data Quality Impact)

---

## Quick Summary

**Problem:**
- UI suggests "TYPE" for "werkwoord"
- Database stores "PROCES" for "werkwoord"
- User expects "TYPE" (grammatical category), gets "PROCES" (activity)

**Root Cause:**
- User manually overrode classifier suggestion from TYPE → PROCES
- System accepted override without validation
- Prompt instructed GPT-4 with "🎯 Focus: Dit is een **proces**"
- AI followed prompt instruction, stored "PROCES"

**Solution:**
- Add "werkwoord" to domain_overrides as TYPE
- Add "-woord" suffix pattern for TYPE category
- Add validation/warning for manual overrides

---

## Evidence Trail

### 1. The Classifier Says "TYPE" ✅

**File:** `src/ontologie/improved_classifier.py`
**Lines:** 85-96

```python
"proces": {
    "suffixes": ["ing", "atie", "tie", "eren", "isatie"],
    # "werkwoord" does NOT match these patterns
}
```

**Result:** Falls back to TYPE (correct by accident)

---

### 2. The User Overrides to "PROCES" ⚠️

**File:** `src/ui/tabbed_interface.py`
**Lines:** 345-357

```python
manual_override = st.selectbox(
    "Aanpassen?",
    options=["", "TYPE", "EXEMPLAAR", "PROCES", "RESULTAAT"],
)
if manual_override:
    SessionStateManager.set_value("manual_ontological_category", manual_override)
    # NO VALIDATION - accepts any value
```

**Result:** User picks "PROCES", system stores it

---

### 3. The Prompt Enforces "PROCES" 🎯

**File:** `src/services/prompts/modules/definition_task_module.py`
**Line:** 196

```python
ont_cat = f"\n🎯 Focus: Dit is een **{ontological_category}** ({category_hints[ontological_category]})"
# ontological_category = "proces" (from user override)
# Output: "🎯 Focus: Dit is een **proces** (activiteit/handeling)"
```

**File:** `_Definitie_Generatie_prompt-9.txt`
**Line:** 390

```text
🎯 Focus: Dit is een **proces** (activiteit/handeling)
```

**Result:** GPT-4 treats "werkwoord" as PROCES, generates definition accordingly

---

### 4. The Database Stores "PROCES" 💾

**File:** `src/services/orchestrators/definition_orchestrator_v2.py`
**Line:** 789

```python
temp_definition = Definition(
    begrip=sanitized_request.begrip,
    ontologische_categorie=sanitized_request.ontologische_categorie,  # "proces"
)
```

**Result:** Database entry has `ontologische_categorie = "proces"`

---

## The Data Flow (Simplified)

```
┌──────────────────────────────────────────────┐
│ 1. CLASSIFIER                                │
│    ImprovedOntologyClassifier                │
│    → "TYPE" (no PROCES patterns match)       │
└──────────────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────────────┐
│ 2. UI DISPLAY                                │
│    st.info("Voorgesteld: TYPE")              │
│    st.selectbox("Aanpassen?", ...)           │
│    → User selects "PROCES" ⚠️                 │
└──────────────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────────────┐
│ 3. SESSION STATE                             │
│    manual_ontological_category = "PROCES"    │
│    (NO VALIDATION)                           │
└──────────────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────────────┐
│ 4. GENERATION REQUEST                        │
│    request.ontologische_categorie = "proces" │
└──────────────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────────────┐
│ 5. PROMPT INJECTION                          │
│    "🎯 Focus: Dit is een **proces**"         │
└──────────────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────────────┐
│ 6. GPT-4 GENERATION                          │
│    Follows prompt → generates PROCES def     │
└──────────────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────────────┐
│ 7. DATABASE STORAGE                          │
│    categorie = "proces" ✓ (as instructed)    │
└──────────────────────────────────────────────┘
```

---

## Why "werkwoord" Should Be TYPE

**Linguistic Analysis:**

| Aspect | TYPE (Correct) | PROCES (Wrong) |
|--------|----------------|----------------|
| **Definition** | Category of words (like "mammal" is a type of animal) | Activity of using words (nonsensical) |
| **Example phrase** | "Werkwoord is een soort woord dat..." | "Werkwoord is een activiteit waarbij..." ❌ |
| **Parallel** | "Car is a type of vehicle" ✅ | "Car is an activity of..." ❌ |
| **Ontology** | Classification/taxonomy | Process/action |

**Correct Classifications:**

| Term | Category | Rationale |
|------|----------|-----------|
| werkwoord | TYPE | Word category (classification) |
| vervoegen | PROCES | Activity of conjugating verbs |
| vervoeging | RESULTAAT | Result of conjugation |

---

## The Fix (Simple)

### Step 1: Add Domain Override

**File:** `config/classification/term_patterns.yaml`
**Add after line 33:**

```yaml
domain_overrides:
  machtiging: TYPE
  vergunning: RESULTAAT
  # ... existing entries

  # NEW: Grammatical meta-terms
  werkwoord: TYPE
  zelfstandig naamwoord: TYPE
  bijvoeglijk naamwoord: TYPE
  bijwoord: TYPE
  voorzetsel: TYPE
  lidwoord: TYPE
  voegwoord: TYPE
```

### Step 2: Add Suffix Pattern

**File:** `config/classification/term_patterns.yaml`
**Add to TYPE suffix_weights (after line 69):**

```yaml
suffix_weights:
  TYPE:
    systeem: 0.80
    model: 0.80
    # ... existing entries
    woord: 0.90        # NEW: werkwoord, bijwoord, etc.
```

### Step 3: Test

```bash
# Run classifier on "werkwoord"
python -c "
from ontologie.improved_classifier import ImprovedOntologyClassifier
classifier = ImprovedOntologyClassifier()
result = classifier.classify('werkwoord', '', '', '')
print(f'Category: {result.categorie.value}')
print(f'Confidence: {result.confidence_label}')
print(f'Reasoning: {result.reasoning}')
"

# Expected output:
# Category: type
# Confidence: HIGH
# Reasoning: Classificatie: TYPE (score: 1.00) | Confidence: 0.95 🟢 (HIGH) | domain override
```

---

## Implementation Checklist

- [ ] Add "werkwoord" and other grammatical terms to `domain_overrides`
- [ ] Add "woord" suffix to TYPE patterns with weight 0.90
- [ ] Test classifier on "werkwoord" (expect TYPE, HIGH confidence)
- [ ] Create test suite for meta-linguistic terms
- [ ] Add audit logging for manual category overrides
- [ ] Add UI warning when user overrides classifier suggestion
- [ ] Re-classify existing "werkwoord" entries in database (if any)
- [ ] Document pattern in `docs/analyses/` for future reference

---

## Files Modified

1. `config/classification/term_patterns.yaml` (domain_overrides + suffix_weights)
2. `tests/classification/test_meta_linguistic_terms.py` (new test file)
3. `src/ui/tabbed_interface.py` (optional: add override validation)
4. `scripts/audit_category_mismatches.py` (optional: audit script)

---

## Key Learnings

1. **Manual overrides need validation** - Don't accept user input blindly
2. **Classifier patterns have gaps** - Meta-linguistic terms weren't considered
3. **Prompt instructions are authoritative** - Whatever is in "🎯 Focus" wins
4. **Audit trails are critical** - Need to track WHO changed WHAT and WHY
5. **Data quality requires consistency checks** - Reconcile classifier vs. final instruction

---

## Related Documents

- **Full Analysis:** `ROOT_CAUSE_ANALYSIS.md` (comprehensive 200+ line investigation)
- **Test Plan:** `DEF-138-test-plan.md` (testing strategy)
- **Config Changes:** `term_patterns.yaml` (implementation)
- **Unique Index Removal:** `DEF-138-UNIQUE-INDEX-REMOVAL-ANALYSIS.md` (related but separate issue)

---

**Status:** ✅ Ready for implementation
**Effort:** 2 hours (config changes + tests + validation)
**Impact:** HIGH (prevents future misclassifications)
**Risk:** LOW (config-only change, no code modifications)

---

**Next Step:** Get approval to update `term_patterns.yaml` and implement fix.
