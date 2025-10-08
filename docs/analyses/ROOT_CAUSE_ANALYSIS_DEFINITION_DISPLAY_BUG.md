# ROOT CAUSE ANALYSIS: Definitie Weergave Bevat Ongewenste Metadata

**Datum:** 2025-10-07
**Status:** CRITICAL BUG
**Impacted Component:** UI Display → GPT Generation → Text Cleaning Pipeline

---

## EXECUTIVE SUMMARY

The UI is displaying unwanted metadata in the definition output:
- **Problem 1:** "Ontologische categorie: soort" header still visible (should be removed)
- **Problem 2:** "Vervoersverbod:" term prefix NOW visible (REGRESSION - was not there before)

**Root Cause:** The prompt **explicitly instructs GPT-4 to include the term** in its output, then the cleaning pipeline fails to remove it properly.

---

## OBSERVED BEHAVIOR

### Current (BROKEN) Output:
```
Ontologische categorie: soord
Vervoersverbod: maatregel die een persoon verbiedt zich met een vervoermiddel binnen een bepaald gebied of tussen specifieke locaties te verplaatsen
```

### Expected Output:
```
Maatregel die een persoon verbiedt zich met een vervoermiddel binnen een bepaald gebied of tussen specifieke locaties te verplaatsen
```

---

## COMPLETE DATA FLOW ANALYSIS

### 1. PROMPT GENERATION (What GPT-4 Receives)

**File:** `src/services/prompts/modules/definition_task_module.py`

#### Line 253: Ontological Marker Instruction
```python
def _build_ontological_marker(self) -> str:
    """Bouw ontologische marker instructie."""
    return """---

📋 **Ontologische marker (lever als eerste regel):**
- Ontologische categorie: kies uit [soort, exemplaar, proces, resultaat]"""
```

**PROBLEM 1:** This instructs GPT to output "Ontologische categorie: [type]" as the **first line**.

#### Line 256: Final Instruction
```python
def _build_final_instruction(self, begrip: str) -> str:
    """Bouw finale definitie instructie."""
    return f"✏️ Geef nu de definitie van het begrip **{begrip}** in één enkele zin, zonder toelichting."
```

**PROBLEM 2:** This asks GPT to provide the definition of the **term** ("begrip"), which GPT interprets as:
- Including the term name as a prefix: "Vervoersverbod: [definition]"
- This is a reasonable interpretation given the instruction pattern

**Prompt Example for "Vervoersverbod":**
```
### 🎯 FINALE INSTRUCTIES:

#### ✏️ Definitieopdracht:
Formuleer nu de definitie van **vervoersverbod** volgens deze specificaties:

[... checklist, quality control ...]

---

📋 **Ontologische marker (lever als eerste regel):**
- Ontologische categorie: kies uit [soort, exemplaar, proces, resultaat]

✏️ Geef nu de definitie van het begrip **vervoersverbod** in één enkele zin, zonder toelichting.
```

**What GPT-4 Generates (Based on These Instructions):**
```
Ontologische categorie: resultaat
Vervoersverbod: maatregel die een persoon verbiedt zich met een vervoermiddel binnen een bepaald gebied of tussen specifieke locaties te verplaatsen
```

GPT follows instructions perfectly:
1. First line: "Ontologische categorie: resultaat"
2. Second line: Definition of the term "vervoersverbod" (including the term as context)

---

### 2. TEXT CLEANING PIPELINE (Processing GPT Output)

**File:** `src/services/orchestrators/definition_orchestrator_v2.py`

#### Lines 578-597: Cleaning Process
```python
# V2 cleaning service (always available through adapter)
raw_gpt_output = (
    generation_result.text
    if hasattr(generation_result, "text")
    else str(generation_result)
)
cleaning_result = await self.cleaning_service.clean_text(
    raw_gpt_output,
    sanitized_request.begrip,
)
cleaned_text = cleaning_result.cleaned_text

# Extract definition without metadata headers for "origineel" display
# This removes "Ontologische categorie:" prefix but keeps the unprocessed definition
from opschoning.opschoning_enhanced import (
    extract_definition_from_gpt_response,
)

definitie_zonder_header = extract_definition_from_gpt_response(
    raw_gpt_output
)
```

**File:** `src/opschoning/opschoning_enhanced.py`

#### Lines 42-84: extract_definition_from_gpt_response()
```python
def extract_definition_from_gpt_response(text: str) -> str:
    """
    Extract de werkelijke definitie uit een GPT response.

    Deze functie verwijdert:
    - Ontologische categorie headers (bijv. "Ontologische categorie: proces")
    - Lege regels aan het begin
    - Andere metadata regels
    """
    lines = text.strip().split("\n")

    # Filter regels die metadata bevatten
    filtered_lines = []
    for line in lines:
        line_lower = line.lower().strip()
        # Skip ontologische categorie regels
        if line_lower.startswith("ontologische categorie:"):
            continue
        # Skip lege regels
        if not line.strip():
            continue
        # Voeg toe aan gefilterde regels
        filtered_lines.append(line)

    # Join de overgebleven regels
    return "\n".join(filtered_lines).strip()
```

**CRITICAL FLAW:** This function:
- ✅ **DOES** remove "Ontologische categorie: resultaat" line
- ❌ **DOES NOT** remove the term prefix "Vervoersverbod:" from the definition line

**After extract_definition_from_gpt_response():**
```
Vervoersverbod: maatregel die een persoon verbiedt zich met een vervoermiddel binnen een bepaald gebied of tussen specifieke locaties te verplaatsen
```

The "Ontologische categorie:" line is gone, but **"Vervoersverbod:"** remains!

---

#### Lines 87-127: opschonen_enhanced()
```python
def opschonen_enhanced(
    definitie: str, begrip: str, handle_gpt_format: bool = True
) -> str:
    # Stap 1: Handle GPT format indien nodig
    if handle_gpt_format:
        definitie = extract_definition_from_gpt_response(definitie)

    # Stap 2: Gebruik de originele opschonen functie
    result: str = opschonen(definitie, begrip)
    return result
```

**Flow:**
1. Calls `extract_definition_from_gpt_response()` → removes "Ontologische categorie:" line
2. Calls `opschonen()` → should remove "Vervoersverbod:" prefix

**File:** `src/opschoning/opschoning.py`

#### Lines 33-142: opschonen() Function
```python
def opschonen(definitie: str, begrip: str) -> str:
    """
    Verwijdert herhaaldelijk alle verboden beginconstructies uit definitie.

    OPSCHONINGSREGELS IN DETAIL:

    1. VERBODEN WOORDEN (uit verboden_woorden.json)
    2. DRIE OPSCHONINGSPATRONEN:
       A. Woord aan begin: "is een proces" → "proces"
       B. Circulaire definitie: "Vonnis is een uitspraak" → "uitspraak"
       C. Begrip met leesteken: "Vonnis: een uitspraak" → "uitspraak"
    """
    # [... setup code ...]

    # Patroon 3c: Extra patroon voor begrip gevolgd door dubbelepunt of streepje
    # Voorbeelden: 'Vonnis:', 'vonnis -', 'vonnis: '
    # Regex: ^vonnis\s*[:\-]?\s* (\s* = nul of meer spaties, [:\-]? = optioneel : of -)
    regex_lijst.append(rf"^{begrip_esc}\s*[:\-]?\s*")

    # ✅ 4. Verwijder alle opeenvolgende verboden prefixes
    while True:
        for patroon in regex_lijst:
            if re.match(patroon, d, flags=re.IGNORECASE):
                d = re.sub(patroon, "", d, flags=re.IGNORECASE, count=1)
                d = d.lstrip(" ,:-")
                break
        else:
            # ✅ Geen patroon meer gevonden
            break
```

**Expected Behavior:** Pattern 3c should match "Vervoersverbod:" and remove it.

**Regex Pattern:**
```python
begrip_esc = re.escape("vervoersverbod".strip().lower())
# Pattern: ^vervoersverbod\s*[:\-]?\s*
```

This pattern **SHOULD** match "Vervoersverbod:" at the start of the line!

**WHY IS IT NOT WORKING?**

Let me trace through with the actual input:

```
Input to opschonen(): "Vervoersverbod: maatregel die..."
begrip: "vervoersverbod"
Pattern: ^vervoersverbod\s*[:\-]?\s*
Match: YES (case-insensitive)
Action: Remove "Vervoersverbod: "
Result: "maatregel die..."
```

**WAIT!** The logic **should work**. Let me check if there's a different issue...

---

### 3. ACTUAL PROBLEM DISCOVERY

Looking at the UI display code:

**File:** `src/ui/components/definition_generator_tab.py`

#### Lines 381-385: UI Display
```python
# Toon ALTIJD beide versies
st.subheader("1️⃣ Originele AI Definitie")
st.info(agent_result["definitie_origineel"])

st.subheader("2️⃣ Finale Definitie")
st.info(agent_result["definitie_gecorrigeerd"])
```

**File:** `src/services/orchestrators/definition_orchestrator_v2.py`

#### Lines 762-767: Metadata Storage
```python
# Store original definition without metadata headers (for UI display)
# This is the GPT output with "Ontologische categorie:" header removed
"definitie_origineel": definitie_zonder_header,
```

**KEY INSIGHT:** The "definitie_origineel" field is set to `definitie_zonder_header`, which comes from `extract_definition_from_gpt_response()`.

**This function only removes the "Ontologische categorie:" line, NOT the term prefix!**

---

## ROOT CAUSE SUMMARY

### Problem 1: "Ontologische categorie: soort" Still Visible

**Status:** PARTIALLY FIXED (typo in user report: "soord" vs "soort")

**Cause:** The `extract_definition_from_gpt_response()` function correctly removes lines starting with "ontologische categorie:", but if there's a typo or variant, it might not match.

**Evidence:**
```python
if line_lower.startswith("ontologische categorie:"):
    continue
```

This should work for "Ontologische categorie: soort" but user reported "soord" (typo).

**Hypothesis:** Either:
1. User has a typo in their report ("soord" instead of "soort")
2. The line is displayed from a different source (not from `definitie_origineel`)

### Problem 2: "Vervoersverbod:" Prefix NOW Visible (REGRESSION)

**Status:** CRITICAL - NEW BUG INTRODUCED

**Root Cause:** The prompt explicitly asks GPT to "define the term **vervoersverbod**", which GPT interprets as including the term in the output.

**Why It's a Regression:**
- **Before:** The `opschonen()` function was called on the full GPT output
- **After:** The `extract_definition_from_gpt_response()` function is called FIRST, which preserves the term prefix line intact
- The term prefix "Vervoersverbod:" is **not** removed because:
  - `extract_definition_from_gpt_response()` only removes lines starting with "ontologische categorie:"
  - The term prefix is part of the definition line itself, not a separate metadata line

**Example:**
```
GPT Output:
Ontologische categorie: resultaat
Vervoersverbod: maatregel die een persoon verbiedt...

After extract_definition_from_gpt_response():
Vervoersverbod: maatregel die een persoon verbiedt...

Expected after opschonen():
Maatregel die een persoon verbiedt...
```

---

## WHY THE FIX FAILED

### Original Fix (definition_orchestrator_v2.py lines 589-597)

The fix added `extract_definition_from_gpt_response()` to remove the "Ontologische categorie:" header, but:

1. **It only removes that specific header line**
2. **It does NOT remove the term prefix from the definition line**
3. **The `definitie_origineel` field is set to the result of this function**, which still contains "Vervoersverbod:"

### Why opschonen() Isn't Being Called on definitie_origineel

**Line 767:**
```python
"definitie_origineel": definitie_zonder_header,
```

This bypasses the full cleaning pipeline! The `opschonen()` function (which removes term prefixes) is only called via `cleaning_service.clean_text()`, which produces `cleaned_text` (not used for "definitie_origineel").

**The "definitie_origineel" should show the RAW GPT output (minus metadata headers), so this might be by design.**

But the UI is showing this field to users, who expect a clean definition!

---

## COMPLETE TRANSFORMATION CHAIN

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: PROMPT GENERATION                                      │
├─────────────────────────────────────────────────────────────────┤
│ definition_task_module.py:                                      │
│ - Line 253: "📋 **Ontologische marker (lever als eerste regel):**" │
│ - Line 256: "✏️ Geef nu de definitie van het begrip **{begrip}**" │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: GPT-4 GENERATION                                       │
├─────────────────────────────────────────────────────────────────┤
│ Output from GPT-4:                                              │
│                                                                 │
│   Ontologische categorie: resultaat                             │
│   Vervoersverbod: maatregel die een persoon verbiedt...         │
│                                                                 │
│ GPT follows instructions perfectly!                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: TEXT CLEANING (definition_orchestrator_v2.py)         │
├─────────────────────────────────────────────────────────────────┤
│ Line 583: cleaning_result = await cleaning_service.clean_text() │
│   ↓ (calls opschoning_enhanced → opschonen)                    │
│   Result: "Maatregel die een persoon verbiedt..."              │
│   (stored in cleaned_text, used for "definitie_gecorrigeerd")  │
│                                                                 │
│ Line 595: definitie_zonder_header = extract_definition_...()   │
│   ↓ (only removes "Ontologische categorie:" line)              │
│   Result: "Vervoersverbod: maatregel die een persoon verbiedt..."│
│   (stored in definitie_zonder_header)                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: METADATA STORAGE (line 767)                           │
├─────────────────────────────────────────────────────────────────┤
│ "definitie_origineel": definitie_zonder_header                  │
│   → "Vervoersverbod: maatregel die..."                         │
│                                                                 │
│ "definitie_gecorrigeerd": cleaned_text                          │
│   → "Maatregel die..."                                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 5: UI DISPLAY (definition_generator_tab.py:381-385)      │
├─────────────────────────────────────────────────────────────────┤
│ st.subheader("1️⃣ Originele AI Definitie")                      │
│ st.info(agent_result["definitie_origineel"])                    │
│   → Shows: "Vervoersverbod: maatregel die..."                  │
│                                                                 │
│ st.subheader("2️⃣ Finale Definitie")                            │
│ st.info(agent_result["definitie_gecorrigeerd"])                 │
│   → Shows: "Maatregel die..."                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## SOLUTIONS

### Option 1: Fix extract_definition_from_gpt_response() (RECOMMENDED)

**Change:** Make `extract_definition_from_gpt_response()` also remove term prefixes.

**Implementation:**
```python
def extract_definition_from_gpt_response(text: str, begrip: str = None) -> str:
    """
    Extract de werkelijke definitie uit een GPT response.

    Verwijdert:
    - Ontologische categorie headers
    - Term prefix (bijv. "Vervoersverbod:")
    - Lege regels
    """
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

        # Remove term prefix if present
        if begrip and line_lower.startswith(begrip.lower() + ":"):
            line = line.split(":", 1)[1].strip()

        filtered_lines.append(line)

    return "\n".join(filtered_lines).strip()
```

**Pros:**
- Minimal change
- Handles the specific case of "term: definition" format
- Backward compatible

**Cons:**
- Requires passing `begrip` parameter to the function
- Only handles simple "term:" prefix (not "term -" or other variants)

### Option 2: Use cleaned_text for definitie_origineel

**Change:** Store `cleaned_text` instead of `definitie_zonder_header` for "definitie_origineel".

**Implementation:**
```python
# Line 767 in definition_orchestrator_v2.py
"definitie_origineel": cleaned_text,  # Instead of definitie_zonder_header
```

**Pros:**
- Simplest fix
- Reuses existing cleaning logic
- No new code needed

**Cons:**
- "Originele AI Definitie" is now misleading (it's already cleaned)
- Loses the ability to show truly raw GPT output for debugging

### Option 3: Update Prompt to Not Include Term Prefix

**Change:** Modify the prompt to explicitly tell GPT NOT to include the term in its output.

**Implementation:**
```python
def _build_final_instruction(self, begrip: str) -> str:
    """Bouw finale definitie instructie."""
    return f"""✏️ Geef nu de definitie van het begrip **{begrip}** in één enkele zin, zonder toelichting.

⚠️ BELANGRIJK: Begin DIRECT met de definitie. Gebruik NIET het begrip zelf of een dubbele punt aan het begin.

FOUT: "Vervoersverbod: maatregel die..."
GOED: "Maatregel die een persoon verbiedt..."
"""
```

**Pros:**
- Prevents the problem at the source
- Aligns GPT output with expected format
- More robust long-term solution

**Cons:**
- Increases prompt size
- May not be 100% reliable (GPT might still add prefix)
- Requires testing to ensure it works

### Option 4: Full opschonen() on definitie_origineel

**Change:** Apply full `opschonen()` cleaning to `definitie_zonder_header` before storing.

**Implementation:**
```python
# Lines 595-597 in definition_orchestrator_v2.py
definitie_zonder_header = extract_definition_from_gpt_response(
    raw_gpt_output
)

# Apply full cleaning to remove term prefix
from opschoning.opschoning import opschonen
definitie_zonder_header = opschonen(definitie_zonder_header, sanitized_request.begrip)
```

**Pros:**
- Reuses existing `opschonen()` logic
- Handles all term prefix variants (":". "-", etc.)
- Consistent with existing cleaning approach

**Cons:**
- May over-clean the "origineel" version
- Double cleaning (once for origineel, once for gecorrigeerd)

---

## RECOMMENDED SOLUTION

**Hybrid Approach: Option 1 + Option 3**

1. **Short-term fix:** Update `extract_definition_from_gpt_response()` to remove simple term prefixes (Option 1)
2. **Long-term fix:** Update prompt to explicitly instruct GPT not to include term prefix (Option 3)

**Rationale:**
- Option 1 fixes the immediate bug with minimal code change
- Option 3 prevents future occurrences by fixing the root cause (prompt design)
- Both changes are complementary and provide defense-in-depth

---

## FILES REQUIRING CHANGES

### 1. src/opschoning/opschoning_enhanced.py
- Update `extract_definition_from_gpt_response()` to accept `begrip` parameter
- Add logic to remove "term:" prefix from definition lines

### 2. src/services/orchestrators/definition_orchestrator_v2.py
- Line 595: Pass `begrip` to `extract_definition_from_gpt_response()`

### 3. src/services/prompts/modules/definition_task_module.py
- Line 256: Update `_build_final_instruction()` to explicitly prohibit term prefix in output

---

## TESTING REQUIREMENTS

### Test Cases:

1. **Test normal case:**
   - Input: "vervoersverbod"
   - Expected output: No "Vervoersverbod:" prefix in definitie_origineel

2. **Test ontological header removal:**
   - Verify "Ontologische categorie: resultaat" line is removed
   - Verify typos like "Ontologische categorie: soord" are also removed

3. **Test term prefix variants:**
   - "Vervoersverbod: definition"
   - "Vervoersverbod - definition"
   - "Vervoersverbod definition" (no separator)

4. **Test edge cases:**
   - Multi-word terms: "elektronisch toezicht"
   - Terms with special characters
   - Terms that are substrings of other words

---

## CONCLUSION

The bug is caused by a **prompt design issue** where GPT is explicitly instructed to "define the term X", which it interprets as including the term in the output. The cleaning pipeline has two paths:

1. **definitie_gecorrigeerd:** Full cleaning via `opschonen()` → WORKS correctly
2. **definitie_origineel:** Partial cleaning via `extract_definition_from_gpt_response()` → FAILS to remove term prefix

The fix is straightforward: enhance `extract_definition_from_gpt_response()` to also remove term prefixes, and optionally update the prompt to prevent GPT from adding them in the first place.
