# EXECUTIVE SUMMARY: Definitie Display Bug

**Date:** 2025-10-07
**Status:** CRITICAL - Root Cause Identified
**Impact:** UI displays unwanted metadata in generated definitions

---

## THE PROBLEM

Users see this:
```
Ontologische categorie: soord
Vervoersverbod: maatregel die een persoon verbiedt zich met een vervoermiddel...
```

Users expect this:
```
Maatregel die een persoon verbiedt zich met een vervoermiddel...
```

---

## ROOT CAUSE (In Plain English)

### Issue 1: "Ontologische categorie: soort" Header

**Why it appears:** The prompt tells GPT to output this as the first line.

**Why it's not removed:** The cleaning function `extract_definition_from_gpt_response()` correctly removes lines starting with "ontologische categorie:", but the user reported "soord" (typo?) which suggests either:
- User typo in report
- OR the line comes from a different data source

**Fix status:** Already implemented in code, may be a reporting error.

### Issue 2: "Vervoersverbod:" Prefix (REGRESSION)

**Why it appears:**
1. The prompt says: "Geef nu de definitie van het begrip **vervoersverbod**"
2. GPT interprets this as: "Output should include the term being defined"
3. GPT generates: "Vervoersverbod: maatregel die..."

**Why it's not removed:**
- The "definitie_origineel" field uses `extract_definition_from_gpt_response()`
- This function only removes "Ontologische categorie:" lines
- It does NOT remove the term prefix from the definition line itself

**Why this is a regression:**
- The full cleaning pipeline (`opschonen()`) DOES remove term prefixes
- But it's only applied to "definitie_gecorrigeerd", not "definitie_origineel"
- Before the recent fix, this wasn't an issue because the cleaning was different

---

## DATA FLOW BREAKDOWN

```
PROMPT GENERATION
↓
GPT-4 generates:
  Line 1: "Ontologische categorie: resultaat"
  Line 2: "Vervoersverbod: maatregel die..."
↓
CLEANING PIPELINE (TWO PATHS)
↓
Path A: cleaning_service.clean_text() → opschonen()
  Result: "Maatregel die..."
  Used for: definitie_gecorrigeerd ✅ WORKS
↓
Path B: extract_definition_from_gpt_response()
  Removes: "Ontologische categorie:" line ✅
  Keeps: "Vervoersverbod: maatregel die..." ❌ BUG
  Used for: definitie_origineel
↓
UI DISPLAY
  Shows: "Vervoersverbod: maatregel die..." ❌ VISIBLE TO USER
```

---

## THE FIX

### Recommended: Hybrid Approach

**Short-term (Quick Fix):**
Enhance `extract_definition_from_gpt_response()` to also remove term prefixes.

```python
# In opschoning_enhanced.py
def extract_definition_from_gpt_response(text: str, begrip: str = None) -> str:
    lines = text.strip().split("\n")
    filtered_lines = []

    for line in lines:
        line_lower = line.lower().strip()

        # Skip ontologische categorie regels
        if line_lower.startswith("ontologische categorie:"):
            continue

        # Skip lege regels
        if not line.strip():
            continue

        # NEW: Remove term prefix if present
        if begrip and line_lower.startswith(begrip.lower() + ":"):
            line = line.split(":", 1)[1].strip()

        filtered_lines.append(line)

    return "\n".join(filtered_lines).strip()
```

**Long-term (Prevent at Source):**
Update prompt to explicitly tell GPT NOT to include the term prefix.

```python
# In definition_task_module.py
def _build_final_instruction(self, begrip: str) -> str:
    return f"""✏️ Geef nu de definitie van het begrip **{begrip}** in één enkele zin, zonder toelichting.

⚠️ BELANGRIJK: Begin DIRECT met de definitie. Gebruik NIET het begrip zelf aan het begin.

FOUT: "Vervoersverbod: maatregel die..."
GOED: "Maatregel die een persoon verbiedt..."
"""
```

---

## FILES TO CHANGE

1. **src/opschoning/opschoning_enhanced.py**
   - Line 42: Update function signature to accept `begrip` parameter
   - Line 80: Add logic to remove "term:" prefix

2. **src/services/orchestrators/definition_orchestrator_v2.py**
   - Line 595: Pass `begrip` to `extract_definition_from_gpt_response()`

3. **src/services/prompts/modules/definition_task_module.py**
   - Line 256: Update prompt to prohibit term prefix in output

---

## TESTING CHECKLIST

- [ ] Test "vervoersverbod" - verify no "Vervoersverbod:" prefix
- [ ] Test "elektronisch toezicht" - multi-word term
- [ ] Test "sanctie" - verify no "Sanctie:" prefix
- [ ] Verify "Ontologische categorie:" header is removed
- [ ] Test both definitie_origineel AND definitie_gecorrigeerd
- [ ] Regression test: verify opschonen() still works for other cases

---

## RISK ASSESSMENT

**Risk Level:** LOW

**Why:**
- Changes are localized to cleaning functions
- Existing tests should catch regressions
- The `opschonen()` function already handles term prefixes correctly
- We're just applying the same logic earlier in the pipeline

**Rollback Plan:**
- If issues arise, simply revert the changes to `extract_definition_from_gpt_response()`
- The "definitie_gecorrigeerd" path will still work correctly

---

## ESTIMATED EFFORT

- **Code changes:** 30 minutes
- **Testing:** 1 hour
- **Total:** ~1.5 hours

---

## NEXT STEPS

1. Implement short-term fix (enhance `extract_definition_from_gpt_response()`)
2. Update caller in `definition_orchestrator_v2.py` to pass `begrip`
3. Run test suite
4. Manual testing with real examples
5. Implement long-term fix (update prompt) if needed
6. Document changes in refactor log

---

## REFERENCE

Full technical analysis: `/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/ROOT_CAUSE_ANALYSIS_DEFINITION_DISPLAY_BUG.md`
