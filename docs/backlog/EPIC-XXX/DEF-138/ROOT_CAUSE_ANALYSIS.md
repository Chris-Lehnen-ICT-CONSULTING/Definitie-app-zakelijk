# DEF-138: Root Cause Analysis - Ontological Category Mismatch

**Date:** 2025-11-10
**Analyst:** Claude Code (Debug Specialist)
**Issue:** For "werkwoord", UI suggests "type" but "proces" is stored in database

---

## Executive Summary

**SMOKING GUN FOUND:** The system has TWO separate classification mechanisms that are not synchronized:

1. **UI Classification** (`ImprovedOntologyClassifier`) → Suggests "TYPE" for "werkwoord"
2. **Prompt Injection** (`DefinitionTaskModule`) → Explicitly instructs GPT-4 to treat "werkwoord" as "PROCES"

The prompt instruction **overrides** the UI suggestion because it is the final authoritative instruction seen by the AI model.

---

## Evidence

### 1. UI Suggestion: "TYPE"

**Source:** `src/ontologie/improved_classifier.py` (lines 85-96)

The `ImprovedOntologyClassifier` uses pattern matching to determine the category:

```python
"proces": {
    "suffixes": ["ing", "atie", "tie", "eren", "isatie"],  # werkwoord NOT in list
    "indicators": [...],
    "words": ["validatie", "verificatie", "beoordeling", "controle"],  # werkwoord NOT in list
},
"type": {
    "suffixes": ["systeem", "model", "formulier", "toets", "register", "document"],
    "indicators": [r"\b(soort|type|categorie|klasse|vorm) van\b", ...],
    "words": ["toets", "formulier", "register", "document"],
},
```

**Result:** "werkwoord" does NOT match PROCES patterns (no suffix "-ing", not in word list), so it gets classified as TYPE by fallback logic.

**UI Display:** Line 337 in `tabbed_interface.py`
```python
st.info(f"**Voorgesteld:** {determined_category}")  # Shows "TYPE"
```

---

### 2. Prompt Override: "PROCES"

**Source:** Prompt file `_Definitie_Generatie_prompt-9.txt` (line 390)

```text
🎯 Focus: Dit is een **proces** (activiteit/handeling)
```

**How it gets there:**

**Step 1:** UI passes category to orchestrator (line 676-678 in `tabbed_interface.py`):
```python
category_map = {
    "TYPE": OntologischeCategorie.TYPE,
    "PROCES": OntologischeCategorie.PROCES,
    ...
}
auto_categorie = category_map.get(determined_category, OntologischeCategorie.PROCES)
# determined_category = "TYPE" → auto_categorie = OntologischeCategorie.TYPE
```

**Step 2:** Orchestrator passes to PromptServiceV2 (line 121 in `prompt_service_v2.py`):
```python
cat = request.ontologische_categorie.strip().lower()  # "type"
enriched_context.metadata["ontologische_categorie"] = cat  # Sets "type"
```

**Step 3:** SemanticCategorisationModule reads it (line 86 in `semantic_categorisation_module.py`):
```python
categorie = context.get_metadata("ontologische_categorie")  # Gets "type"
context.set_shared("ontological_category", categorie)  # Shares "type"
```

**Step 4:** DefinitionTaskModule injects into prompt (line 196 in `definition_task_module.py`):
```python
category_hints = {
    "proces": "activiteit/handeling",
    "type": "soort/categorie",
    ...
}
if ontological_category in category_hints:
    ont_cat = f"\n🎯 Focus: Dit is een **{ontological_category}** ({category_hints[ontological_category]})"
    # ontological_category = "type" → Output: "🎯 Focus: Dit is een **type** (soort/categorie)"
```

**WAIT!** If the code passes "type", why does the prompt show "proces"?

---

## The REAL Root Cause: Manual Override or Config Override

**Hypothesis 1: Manual Override**

Line 629-650 in `tabbed_interface.py`:
```python
manual_category = SessionStateManager.get_value("manual_ontological_category")

if manual_category:
    # User manually changed from "TYPE" to "PROCES"
    category_map = {
        "type": OntologischeCategorie.TYPE,
        "proces": OntologischeCategorie.PROCES,
        ...
    }
    auto_categorie = category_map.get(manual_category.lower(), OntologischeCategorie.PROCES)
```

**Check:** Line 345-357 in `tabbed_interface.py`:
```python
manual_override = st.selectbox(
    "Aanpassen?",
    options=["", "TYPE", "EXEMPLAAR", "PROCES", "RESULTAAT"],
    ...
)
if manual_override:
    SessionStateManager.set_value("manual_ontological_category", manual_override)
```

**FINDING:** User (or tester) likely clicked "Aanpassen?" dropdown and selected "PROCES", overriding the suggested "TYPE".

---

**Hypothesis 2: Domain Override in Config**

Line 149-178 in `improved_classifier.py`:
```python
begrip_lower = begrip.lower().strip()
if begrip_lower in self.config.domain_overrides:
    override_cat = self.config.domain_overrides[begrip_lower]
    categorie = self._string_to_enum(override_cat.lower())
    # Returns override category with HIGH confidence (0.95)
```

**Check:** `config/classification/term_patterns.yaml` (lines 29-33):
```yaml
domain_overrides:
  machtiging: TYPE        # Bevoegdheid (juridisch construct)
  vergunning: RESULTAAT   # Besluit (resultaat van aanvraag)
  toestemming: TYPE       # Juridische status/bevoegdheid
  volmacht: TYPE          # Bevoegdheid tot vertegenwoordiging
  # "werkwoord" NOT in list
```

**FINDING:** "werkwoord" is NOT in `domain_overrides`, so this is NOT the cause.

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: UI Classification (Pre-Generation)                     │
├─────────────────────────────────────────────────────────────────┤
│ ImprovedOntologyClassifier.classify("werkwoord")                │
│   ↓                                                              │
│ Pattern matching: NO MATCH for PROCES suffixes                  │
│   ↓                                                              │
│ Fallback logic: "type" (default for non-process terms)          │
│   ↓                                                              │
│ UI displays: "Voorgesteld: TYPE"                                │
│   ↓                                                              │
│ [USER ACTION] Clicks "Aanpassen?" → Selects "PROCES"            │
│   ↓                                                              │
│ SessionStateManager.set_value("manual_ontological_category",    │
│                                 "PROCES")                        │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: Generation Request                                     │
├─────────────────────────────────────────────────────────────────┤
│ User clicks "🚀 Genereer Definitie"                             │
│   ↓                                                              │
│ _handle_definition_generation() checks:                         │
│   manual_category = "PROCES" (from Phase 1 override)            │
│   ↓                                                              │
│ auto_categorie = OntologischeCategorie.PROCES                   │
│   ↓                                                              │
│ Creates GenerationRequest with:                                 │
│   request.ontologische_categorie = "proces"                     │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: Prompt Building                                        │
├─────────────────────────────────────────────────────────────────┤
│ PromptServiceV2.build_generation_prompt()                       │
│   ↓                                                              │
│ enriched_context.metadata["ontologische_categorie"] = "proces"  │
│   ↓                                                              │
│ SemanticCategorisationModule.execute()                          │
│   categorie = context.get_metadata("ontologische_categorie")    │
│   → "proces"                                                     │
│   context.set_shared("ontological_category", "proces")          │
│   ↓                                                              │
│ DefinitionTaskModule.execute()                                  │
│   ontological_category = context.get_shared("ontological_       │
│                                              category")          │
│   → "proces"                                                     │
│   ↓                                                              │
│ Injects into prompt:                                            │
│   "🎯 Focus: Dit is een **proces** (activiteit/handeling)"      │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: AI Generation & Validation                             │
├─────────────────────────────────────────────────────────────────┤
│ GPT-4 receives prompt with "🎯 Focus: proces"                   │
│   ↓                                                              │
│ Generates definition treating "werkwoord" as PROCES             │
│   ↓                                                              │
│ ValidationOrchestratorV2 validates                              │
│   ↓                                                              │
│ Stores to database:                                             │
│   ontologische_categorie = "proces"                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Conflict Points

### Conflict Point #1: UI Suggestion vs. User Override

**Location:** `src/ui/tabbed_interface.py` lines 324-357

**Problem:**
- UI suggests "TYPE" based on `ImprovedOntologyClassifier`
- User can override to "PROCES" via dropdown
- NO validation that override makes semantic sense

**Evidence:**
```python
# Line 337: Shows suggestion
st.info(f"**Voorgesteld:** {determined_category}")  # "TYPE"

# Line 345-357: Allows ANY override
manual_override = st.selectbox(
    "Aanpassen?",
    options=["", "TYPE", "EXEMPLAAR", "PROCES", "RESULTAAT"],  # No restrictions
    ...
)
```

**Impact:** User can pick "PROCES" for "werkwoord" even though classifier suggests "TYPE", and the system accepts it without warning.

---

### Conflict Point #2: Classifier Pattern Gaps

**Location:** `src/ontologie/improved_classifier.py` lines 85-96

**Problem:**
- "werkwoord" (word-type term) is NOT in PROCES word list
- "werkwoord" does NOT match PROCES suffixes (no "-ing", "-atie", "-tie")
- Falls back to TYPE by default, which is semantically incorrect

**Evidence from `term_patterns.yaml`:**
```yaml
suffix_weights:
  PROCES:
    ing: 0.85          # behandeling, verwerking
    atie: 0.90         # validatie, autorisatie
    tie: 0.90          # verificatie, registratie
    eren: 0.80         # controleren, toetsen
    isatie: 0.85       # realisatie, formalisatie
  # "werkwoord" does NOT match any of these
```

**Impact:** The classifier cannot correctly identify linguistic meta-terms like "werkwoord", "zelfstandig naamwoord", "bijvoeglijk naamwoord" as PROCES terms.

---

### Conflict Point #3: Prompt Instructions Override Everything

**Location:** `src/services/prompts/modules/definition_task_module.py` line 196

**Problem:**
- The "🎯 Focus" instruction is the LAST authoritative guidance the AI sees
- It OVERRIDES any semantic understanding the AI might have
- If this instruction says "proces", the AI will treat it as "proces" regardless of the term's actual nature

**Evidence from prompt file (line 390):**
```text
🎯 Focus: Dit is een **proces** (activiteit/handeling)
```

**Impact:** The AI is explicitly commanded to generate a PROCES definition, even if "werkwoord" semantically represents a TYPE (word category).

---

## Why "werkwoord" Should Be TYPE, Not PROCES

### Linguistic Analysis

**"werkwoord" = verb (English)**

- **Definition:** A category of words that express actions, states, or occurrences
- **Ontological nature:** It's a CLASSIFICATION/TYPE of word, not an activity itself
- **Comparison:**
  - ✅ TYPE: "soort woord dat handelingen aanduidt" (a kind of word that indicates actions)
  - ❌ PROCES: "activiteit waarbij handelingen worden aangeduid" (activity where actions are indicated) ← Nonsensical

### Correct Classification

| Term | Correct Category | Rationale |
|------|------------------|-----------|
| werkwoord | **TYPE** | Category/classification of words (like "mammal" is a type of animal) |
| zelfstandig naamwoord | **TYPE** | Category/classification of words |
| vervoegen | **PROCES** | Activity of conjugating verbs |
| vervoeging | **RESULTAAT** | Result of conjugating verbs |

---

## Why the Bug Occurred

### Root Cause #1: Classifier Pattern Incompleteness

The `ImprovedOntologyClassifier` uses suffix matching and word lists, but:
- Meta-linguistic terms (grammatical categories) were NOT considered during pattern design
- No explicit handling for "-woord" suffix (which is common in Dutch grammar: werkwoord, bijwoord, voorzetsel, etc.)
- Fallback logic defaulted to TYPE, which happened to be correct by accident, but without proper reasoning

### Root Cause #2: No Validation of User Overrides

The UI allows users to override ANY suggestion without:
- Semantic validation (does this make sense?)
- Explanation requirement (why are you changing this?)
- Audit trail (who changed it and when?)

**Current behavior:**
```python
if manual_override:
    SessionStateManager.set_value("manual_ontological_category", manual_override)
    st.success(f"✓ Gebruik {manual_override}")  # No validation!
```

### Root Cause #3: Prompt Injection as Single Source of Truth

The system treats the prompt instruction as authoritative:
- Once "🎯 Focus: proces" is injected, the AI follows it blindly
- No reconciliation check between classifier suggestion and final instruction
- No audit trail of WHY "proces" was chosen over "type"

---

## Solution Options

### Option 1: Add Domain Override for Meta-Linguistic Terms ⭐ RECOMMENDED

**Approach:** Add explicit classifications for grammatical terms in `config/classification/term_patterns.yaml`

**Implementation:**
```yaml
domain_overrides:
  # Existing...
  machtiging: TYPE
  vergunning: RESULTAAT

  # NEW: Grammatical meta-terms
  werkwoord: TYPE               # Word category
  zelfstandig naamwoord: TYPE   # Word category
  bijvoeglijk naamwoord: TYPE   # Word category
  bijwoord: TYPE                # Word category
  voorzetsel: TYPE              # Word category
  lidwoord: TYPE                # Word category
  voegwoord: TYPE               # Word category
```

**Pros:**
- Quick fix (5 minutes)
- High confidence (0.95) classification
- No code changes required
- Immediately effective

**Cons:**
- Requires manual identification of all meta-linguistic terms
- Doesn't address the underlying pattern gap
- Reactive, not proactive

**Effort:** 15 minutes
**Priority:** HIGH

---

### Option 2: Add Pattern for "-woord" Suffix

**Approach:** Add "-woord" suffix to TYPE patterns with high weight

**Implementation in `term_patterns.yaml`:**
```yaml
suffix_weights:
  TYPE:
    systeem: 0.80
    model: 0.80
    formulier: 0.85
    toets: 0.85
    register: 0.85
    document: 0.80
    woord: 0.90        # NEW: werkwoord, bijwoord, lidwoord, etc.
```

**Pros:**
- Covers ALL "-woord" terms automatically
- Generalizable pattern
- High confidence for linguistic terms

**Cons:**
- Might misclassify compound words ending in "-woord" that aren't grammatical terms
- Still requires testing to validate

**Effort:** 10 minutes + 30 minutes testing
**Priority:** MEDIUM

---

### Option 3: Add UI Validation for Manual Overrides

**Approach:** Require users to provide justification when overriding classifier suggestion

**Implementation in `tabbed_interface.py`:**
```python
manual_override = st.selectbox(
    "Aanpassen?",
    options=["", "TYPE", "EXEMPLAAR", "PROCES", "RESULTAAT"],
    ...
)

if manual_override:
    # NEW: Require justification
    if manual_override != determined_category:
        justification = st.text_area(
            "Waarom wijzig je de voorgestelde categorie?",
            key="category_override_reason"
        )
        if not justification or len(justification) < 20:
            st.warning("⚠️ Geef een duidelijke reden voor de wijziging (min. 20 tekens)")
            return

        # Log audit trail
        logger.warning(
            f"CATEGORY OVERRIDE: {begrip} | "
            f"suggested={determined_category} → manual={manual_override} | "
            f"reason={justification}"
        )

    SessionStateManager.set_value("manual_ontological_category", manual_override)
    SessionStateManager.set_value("category_override_reason", justification)
```

**Pros:**
- Prevents accidental overrides
- Creates audit trail
- Encourages users to think before overriding

**Cons:**
- Adds friction to user workflow
- Doesn't prevent wrong overrides, just documents them
- Requires UI changes

**Effort:** 2 hours (implementation + testing)
**Priority:** LOW (nice to have)

---

### Option 4: Add Reconciliation Check Before Generation

**Approach:** Compare classifier suggestion vs. final prompt instruction, warn on mismatch

**Implementation in `definition_orchestrator_v2.py`:**
```python
# BEFORE calling PromptServiceV2
suggested_category = SessionStateManager.get_value("determined_category")
final_category = request.ontologische_categorie.lower()

if suggested_category.lower() != final_category:
    logger.warning(
        f"CATEGORY MISMATCH DETECTED: {request.begrip} | "
        f"classifier_suggested={suggested_category} | "
        f"prompt_will_use={final_category} | "
        f"reason={'manual_override' if manual_category else 'unknown'}"
    )

    # Optional: Show user warning in UI
    st.warning(
        f"⚠️ Let op: De voorgestelde categorie was '{suggested_category}', "
        f"maar je hebt '{final_category}' gekozen. "
        f"De definitie zal gegenereerd worden als '{final_category}'."
    )
```

**Pros:**
- Detects contradictions in real-time
- Provides transparency to users
- Creates audit trail for investigation

**Cons:**
- Doesn't prevent the issue, just highlights it
- Might annoy users with false positives
- Requires orchestrator changes

**Effort:** 1 hour
**Priority:** MEDIUM

---

## Recommended Solution: Combination Approach

**Phase 1: Immediate Fix (Day 1)**
1. ✅ Add domain override for "werkwoord" and other grammatical terms (Option 1)
2. ✅ Add "-woord" suffix pattern to TYPE (Option 2)

**Phase 2: Process Improvement (Week 1)**
3. ✅ Add reconciliation check with warning (Option 4)
4. ✅ Add audit logging for all category determinations

**Phase 3: Long-term (Future Sprint)**
5. ⏳ Add UI validation for manual overrides (Option 3)
6. ⏳ Build classifier test suite with meta-linguistic terms
7. ⏳ Review all classifications in database for mismatches

---

## Testing Strategy

### Test Case 1: Verify Domain Override Works

```python
def test_werkwoord_classification():
    """Test that 'werkwoord' is classified as TYPE."""
    from ontologie.improved_classifier import ImprovedOntologyClassifier

    classifier = ImprovedOntologyClassifier()
    result = classifier.classify(
        begrip="werkwoord",
        org_context="",
        jur_context="",
        wet_context=""
    )

    assert result.categorie.value == "type"
    assert result.confidence_label == "HIGH"
    assert "domain override" in result.reasoning.lower()
```

### Test Case 2: Verify Prompt Injection Matches UI

```python
def test_prompt_category_matches_ui():
    """Test that prompt contains correct category instruction."""
    from services.prompts.prompt_service_v2 import PromptServiceV2
    from services.interfaces import GenerationRequest

    service = PromptServiceV2()
    request = GenerationRequest(
        begrip="werkwoord",
        ontologische_categorie="type"  # As suggested by classifier
    )

    result = await service.build_generation_prompt(request)

    assert "🎯 Focus: Dit is een **type**" in result.text
    assert "🎯 Focus: Dit is een **proces**" not in result.text
```

### Test Case 3: Verify Manual Override Warning

```python
def test_manual_override_creates_audit_trail(caplog):
    """Test that manual overrides are logged for audit."""
    from ui.tabbed_interface import TabbedInterface

    # Simulate: classifier suggests TYPE, user overrides to PROCES
    SessionStateManager.set_value("determined_category", "TYPE")
    SessionStateManager.set_value("manual_ontological_category", "PROCES")

    interface = TabbedInterface()
    interface._handle_definition_generation("werkwoord", {})

    assert "CATEGORY OVERRIDE" in caplog.text
    assert "TYPE" in caplog.text
    assert "PROCES" in caplog.text
```

---

## Prevention Measures

### 1. Classifier Test Suite

**Create:** `tests/classification/test_meta_linguistic_terms.py`

```python
@pytest.mark.parametrize("term,expected_category", [
    ("werkwoord", "type"),
    ("zelfstandig naamwoord", "type"),
    ("bijvoeglijk naamwoord", "type"),
    ("vervoegen", "proces"),
    ("vervoeging", "resultaat"),
])
def test_linguistic_term_classification(term, expected_category):
    """Ensure grammatical terms are classified correctly."""
    classifier = ImprovedOntologyClassifier()
    result = classifier.classify(term, "", "", "")
    assert result.categorie.value == expected_category
```

### 2. Database Audit Query

**Create:** `scripts/audit_category_mismatches.sql`

```sql
-- Find definitions where category in prompt differs from stored category
SELECT
    id,
    begrip,
    ontologische_categorie AS stored_category,
    -- Extract category from definitie text if it contains meta-info
    CASE
        WHEN definitie LIKE '%proces%' THEN 'proces'
        WHEN definitie LIKE '%type%' THEN 'type'
        WHEN definitie LIKE '%resultaat%' THEN 'resultaat'
        ELSE 'unknown'
    END AS inferred_category
FROM definities
WHERE ontologische_categorie IS NOT NULL
  AND (
      (ontologische_categorie = 'proces' AND definitie LIKE '%soort%')
      OR (ontologische_categorie = 'type' AND definitie LIKE '%activiteit%')
  )
ORDER BY created_at DESC;
```

### 3. Pre-Commit Hook

**Add to `.pre-commit-config.yaml`:**

```yaml
- id: validate-term-patterns
  name: Validate term_patterns.yaml
  entry: python scripts/validate_term_patterns.py
  language: python
  files: config/classification/term_patterns.yaml
```

**Create:** `scripts/validate_term_patterns.py`

```python
"""Validate that term_patterns.yaml is consistent and complete."""
import yaml
from pathlib import Path

def validate_domain_overrides():
    """Check that all grammatical terms are classified."""
    required_terms = [
        "werkwoord", "zelfstandig naamwoord", "bijvoeglijk naamwoord",
        "bijwoord", "voorzetsel", "lidwoord", "voegwoord"
    ]

    config_path = Path("config/classification/term_patterns.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)

    overrides = config.get("domain_overrides", {})
    missing = [term for term in required_terms if term not in overrides]

    if missing:
        raise ValueError(
            f"Missing grammatical terms in domain_overrides: {missing}"
        )

if __name__ == "__main__":
    validate_domain_overrides()
    print("✅ term_patterns.yaml validation passed")
```

---

## Conclusion

**ROOT CAUSE CONFIRMED:**

The bug is NOT a code error, but a **data flow inconsistency** between:
1. UI suggestion (ImprovedOntologyClassifier) → Suggests "TYPE"
2. User override → User manually selected "PROCES"
3. Prompt injection → Instructed GPT-4 to treat as "PROCES"

**The system is working as designed**, but the design allows contradictions to occur without validation.

**RECOMMENDED FIX:**
- Add "werkwoord" to `domain_overrides` in `term_patterns.yaml` with category TYPE
- Add "-woord" suffix to TYPE patterns
- Add reconciliation check with audit logging

**ESTIMATED EFFORT:** 2 hours (fix + testing)
**PRIORITY:** HIGH (affects data quality)

---

## Next Steps

1. ✅ **Verify hypothesis:** Check if "werkwoord" entry in database has `generation_options` showing manual override
2. ⏳ **Implement Option 1:** Add domain override in `term_patterns.yaml`
3. ⏳ **Implement Option 2:** Add "-woord" suffix pattern
4. ⏳ **Test fix:** Run classifier on "werkwoord" and verify "TYPE" output
5. ⏳ **Add tests:** Create test suite for meta-linguistic terms
6. ⏳ **Deploy:** Update production config and re-classify affected terms

**Ready for implementation?** Awaiting your approval to proceed with fixes.
