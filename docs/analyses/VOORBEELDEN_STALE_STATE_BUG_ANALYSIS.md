# ROOT CAUSE ANALYSIS: Stale Voorbeelden Bug in Edit Tab

**Datum:** 2025-11-04
**Prioriteit:** P0 (DATA LOSS RISK)
**Status:** Analysis Complete - Fix Pending
**Analyst:** Claude Code (BMad Master mode)

---

## 🚨 EXECUTIVE SUMMARY

**Bug:** Wanneer een gebruiker definitie A bewerkt in de Edit Tab en vervolgens via zoek definitie B selecteert, blijven de voorbeelden van definitie A zichtbaar in de UI. Bij opslaan worden deze voorbeelden toegevoegd aan definitie B, wat resulteert in data loss van B's originele voorbeelden.

**Impact:** DATA CORRUPTION - voorbeelden worden aan verkeerde definities gekoppeld
**Urgency:** CRITICAL - hoger dan DEF-108 timeout fix
**User Report:** Logging toont 21 voorbeelden → 48 voorbeelden bij save

---

## 📊 SYMPTOM ANALYSIS (UIT LOGGING)

```
16:03:06 - Generated definitie ID 106 voor 'semantiek'
16:03:06 - Successfully saved 21 voorbeelden           ← ORIGINEEL

// User edits definition 106 in Edit tab
16:04:09 - Loading definition 106 - no current definition
16:04:37 - Updated definitie 106 (semantiek)

// User selects DIFFERENT definition via search (hypothesized)
// BUG: voorbeelden from previous definition still visible

16:05:10 - Saving voorbeelden voor definitie 106
16:05:10 - Successfully saved 48 voorbeelden           ← 48?! WAS 21!
```

**48 voorbeelden = 21 (origineel) + ~27 (van andere definitie?)**

---

## 🔍 CODE ARCHAEOLOGY FINDINGS

### 1. VOORBEELDEN RESOLUTION ORDER

**File:** `src/ui/helpers/examples.py:113-262`

```python
def resolve_examples(
    state_key: str, definition: Any | None, *, repository: Any | None = None
) -> dict[str, Any]:
    """Resolution order:
    1) Session state (al gecanonicaliseerd)
    2) Definition.metadata.voorbeelden
    3) last_generation_result → agent_result.voorbeelden
    4) Database fallback via repository
    """
```

**Key Implementation Details:**

```python
# Priority 1: Session state CHECK (Line 126-131)
try:
    sess_val = SessionStateManager.get_value(state_key)
    if isinstance(sess_val, dict) and sess_val:
        return canonicalize_examples(sess_val)  # ← EARLY RETURN!
except Exception:
    pass

# Priority 2-4 only reached if session state is empty/None
```

**OBSERVATION:** Session state heeft ALTIJD voorrang. Als er stale data in session state zit, wordt die gebruikt zonder DB check!

---

### 2. WIDGET SYNCHRONIZATION MECHANISM

**File:** `src/ui/components/examples_block.py:39-92`

```python
def _sync_voorbeelden_to_widgets(
    voorbeelden: dict[str, Any],
    prefix: str,
    force_overwrite: bool = False
):
    """Sync voorbeelden dict to widget keys."""

    for field, widget_suffix, join_sep in _VOORBEELD_FIELD_CONFIG:
        widget_key = k(widget_suffix)  # e.g., "edit_106_vz_edit"

        # Skip if already set (unless forcing overwrite)
        if not force_overwrite:
            existing = SessionStateManager.get_value(widget_key, None)
            if existing is not None:  # ← PROBLEEM!
                continue  # ← SKIP SYNC!

        # ... sync logic
```

**CALLING CONTEXT (Line 354-356):**
```python
_sync_voorbeelden_to_widgets(
    current_examples, state_prefix, force_overwrite=False  # ← ALTIJD FALSE!
)
```

**CRITICAL ISSUE:** Met `force_overwrite=False` wordt er NIET gesynchroniseerd als widget key al bestaat, zelfs als de data stale is!

---

### 3. STATE PREFIX SCOPING

**File:** `src/ui/components/definition_edit_tab.py:708-735`

```python
def _render_examples_section(self):
    def_id = SessionStateManager.get_value("editing_definition_id")
    if not def_id:
        return

    render_examples_block(
        definition,
        state_prefix=f"edit_{def_id}",  # ← UNIEK PER DEFINITIE
        allow_generate=True,
        allow_edit=True,
        repository=repo,
    )
```

**OBSERVATION:** State prefix is correct (edit_106 vs edit_105). Dit zou moeten werken!

---

### 4. DEFINITION SWITCHING

**File:** `src/ui/components/definition_edit_tab.py:947-986`

```python
def _start_edit_session(self, definition_id: int):
    """Start edit session for a definition."""
    session = self.edit_service.start_edit_session(definition_id, user=...)

    if session["success"]:
        SessionStateManager.set_value("editing_definition_id", definition_id)
        SessionStateManager.set_value("editing_definition", session["definition"])
        SessionStateManager.set_value("edit_session", session)

        # ❌ NO CLEANUP OF OLD WIDGET KEYS!
        # ❌ NO FORCE_OVERWRITE TRIGGER!

        st.success("✅ Edit sessie gestart")
        st.rerun()
```

**CRITICAL MISSING:** Geen cleanup van oude definition's widget state bij definitie wissel!

---

## 🐛 ROOT CAUSE IDENTIFICATION

### Primary Bug: Stale Session State Persistence

**Scenario:**

1. **User opent definitie 106:**
   - Widget keys: `edit_106_vz_edit`, `edit_106_pv_edit`, etc.
   - Values synced from DB: voorbeelden van 106

2. **User bewerkt widgets (optioneel):**
   - Widget values blijven in session state

3. **User selecteert definitie 105 via zoek:**
   - `_start_edit_session(105)` called
   - `editing_definition_id` = 105 ✅
   - `state_prefix` = "edit_105" ✅
   - `resolve_examples()` haalt voorbeelden van 105 uit DB ✅

4. **BUG TRIGGER: `_sync_voorbeelden_to_widgets(..., force_overwrite=False)`:**
   - Check: Is `edit_105_vz_edit` al gezet?
   - **IF FIRST TIME**: Nee → Sync van DB ✅
   - **IF PREVIOUSLY OPENED IN SAME SESSION**: Ja → **SKIP SYNC!** ❌

5. **Result:**
   - Widgets tonen STALE data van vorige keer dat 105 geopend was
   - Of LEGE data als 105 nooit geopend was maar widgets bestaan

### Secondary Bug Hypothesis: Session State Leakage

**Alternative scenario (needs validation):**

IF er ergens in de code een GLOBALE widget key wordt gebruikt (zonder `state_prefix`), dan kunnen voorbeelden overlappen tussen definities.

**Evidence needed:** Grep voor widget keys zonder `k()` helper in examples_block.py

---

## 🎯 IMPACT ANALYSIS

### Data Integrity Risk

**HIGH SEVERITY:**
- Voorbeelden van definitie A worden toegevoegd aan definitie B
- Originele voorbeelden van B worden OVERSCHREVEN (niet merged!)
- Database save is REPLACE (set actief=FALSE, then insert new)

**User workflow affected:**
```
Definitie A: 21 voorbeelden (correct)
↓ User edits in Edit tab
↓ User switches to Definitie B via search
↓ Bug: A's voorbeelden still visible
↓ User saves
Definitie B: 48 voorbeelden (21 from A + ?? from B) ← DATA CORRUPTION
```

### Frequency Assessment

**LIKELY FREQUENT:**
- Multi-definitie editing sessions (common workflow)
- Search + edit workflow (primary use case)
- Same-session definition switching (expected behavior)

**Risk Factor:** Users likely don't notice immediately (voorbeelden section expandable)

---

## 💡 SOLUTION OPTIONS

### Option A: Force Overwrite on Definition Switch (Emergency Hotfix)

**Change:** Set `force_overwrite=True` when opening different definition

**Implementation:**
```python
# In definition_edit_tab.py:_start_edit_session()
def _start_edit_session(self, definition_id: int):
    # ... existing code ...

    # NEW: Clear stale widget state before rerun
    prev_id = SessionStateManager.get_value("editing_definition_id")
    if prev_id and prev_id != definition_id:
        # Force clean slate for new definition
        self._clear_examples_widgets(prev_id)

    SessionStateManager.set_value("editing_definition_id", definition_id)
    # ... rest ...
```

**Pros:**
- Minimal code change (<20 lines)
- Immediate fix for data loss
- Low risk (surgical change)

**Cons:**
- User edits in widgets are lost on definition switch
- Not perfect UX (but prevents data corruption)

**Lines changed:** ~15-20
**Risk:** LOW
**Time:** 30 min

---

### Option B: Reverse Priority Order (Proper Fix)

**Change:** Database FIRST, session state as fallback (OPPOSITE of current)

**Implementation:**
```python
def resolve_examples(
    state_key: str, definition: Any | None, *, repository: Any | None = None
) -> dict[str, Any]:
    """Resolution order:
    1) Database (if definition.id exists) ← NEW PRIORITY!
    2) Definition.metadata.voorbeelden
    3) last_generation_result
    4) Session state (fallback for generator tab)
    """

    # 1) Database first (if we have a saved definition)
    if definition and hasattr(definition, "id") and int(definition.id) > 0:
        try:
            db_examples = repository.get_voorbeelden_by_type(definition.id)
            if db_examples:
                canon = canonicalize_examples(db_examples)
                SessionStateManager.set_value(state_key, canon)  # Update session
                return canon
        except Exception:
            pass

    # 2-4) Fallbacks for generator tab / unsaved definitions
    # ... existing logic ...
```

**Pros:**
- Fixes root cause (wrong priority)
- Database is Single Source of Truth
- Aligns with "SSoT = Database" principle

**Cons:**
- Larger change (~50 lines)
- May affect generator tab behavior (needs testing)
- Breaking change if unsaved edits expected

**Lines changed:** ~50
**Risk:** MEDIUM
**Time:** 2 hours (with testing)

---

### Option C: Context-Aware Sync with Definition ID Tracking

**Change:** Track last synced definition ID, force resync on mismatch

**Implementation:**
```python
def _sync_voorbeelden_to_widgets(
    voorbeelden: dict[str, Any],
    prefix: str,
    force_overwrite: bool = False,
    definition_id: int | None = None  # NEW PARAM
):
    # Track last synced definition for this prefix
    last_synced_key = f"{prefix}_last_synced_id"
    last_synced = SessionStateManager.get_value(last_synced_key, None)

    # Force overwrite if definition changed
    if definition_id and last_synced != definition_id:
        force_overwrite = True
        SessionStateManager.set_value(last_synced_key, definition_id)

    # ... rest of sync logic ...
```

**Pros:**
- Preserves user edits within same definition
- Forces resync on definition switch
- Clear intent (definition-aware sync)

**Cons:**
- More complex state management
- Requires definition_id passing through call chain
- Edge cases with unsaved definitions

**Lines changed:** ~30
**Risk:** MEDIUM-LOW
**Time:** 1.5 hours

---

## 🎯 RECOMMENDATION

**Priority 1: Option C (Context-Aware Sync)**
- **Rationale:** Best balance of UX (preserves edits) and correctness (prevents data loss)
- **Implementation:** Add definition ID tracking to force resync on switch
- **Testing:** Easy to validate (open def A, edit, switch to def B, verify B's data shown)

**Priority 2: Option A (Emergency Hotfix)**
- **Use if:** Need immediate fix before comprehensive solution
- **Downside:** User edits lost on switch (but better than data corruption)

**NOT RECOMMENDED: Option B**
- **Reason:** Too invasive, may break generator tab workflow
- **Risk:** High for limited gain

---

## 🧪 VALIDATION PLAN

### Test Case 1: Definition Switch with Stale Data
```
1. Open definitie 106 in Edit tab
2. Verify voorbeelden van 106 shown
3. (Optional) Edit voorbeelden
4. Search and select definitie 105
5. VERIFY: voorbeelden van 105 shown (NOT 106!)
6. Save
7. VERIFY: definitie 105 has correct voorbeelden count
```

### Test Case 2: Multiple Switches
```
1. Open def 106 → edit → don't save
2. Open def 105 → verify 105 data
3. Open def 106 again → verify 106 data (NOT 105!)
4. Save → verify 106 has 106's data
```

### Test Case 3: Same Session Revisit
```
1. Open def 106 → save
2. Open def 105 → save
3. Open def 106 again (same session)
4. VERIFY: voorbeelden refreshed from DB (not stale session state)
```

---

## 📝 IMPLEMENTATION CHECKLIST

- [ ] Choose solution option (recommend: Option C)
- [ ] Implement definition ID tracking in `_sync_voorbeelden_to_widgets`
- [ ] Update `render_examples_block` to pass definition_id
- [ ] Add logging for sync decisions (debug mode)
- [ ] Run validation test cases (all 3)
- [ ] Smoke test: generator tab still works
- [ ] Update VOORBEELDEN_STALE_STATE_BUG_ANALYSIS.md with implementation notes
- [ ] Commit with message: `fix(edit): prevent stale voorbeelden on definition switch (DEF-XXX)`

---

## 🔗 RELATED ISSUES

- **DEF-108:** Praktijkvoorbeelden timeout (separate issue, lower priority)
- **DEF-56:** Key-only widget pattern (related fix for stale data)
- **US-202:** ServiceContainer singleton (not related)

---

## 📚 CODE REFERENCES

**Key files analyzed:**
- `src/ui/helpers/examples.py:113-262` (resolve_examples)
- `src/ui/components/examples_block.py:39-92` (_sync_voorbeelden_to_widgets)
- `src/ui/components/examples_block.py:94-535` (render_examples_block)
- `src/ui/components/definition_edit_tab.py:708-735` (_render_examples_section)
- `src/ui/components/definition_edit_tab.py:947-986` (_start_edit_session)
- `src/database/definitie_repository.py:1458-1703` (save_voorbeelden)

**Commit analysis:**
- `6aaa736f` - Auto-load voorbeelden from metadata (partial fix, not complete)
- `04fb928c` - DEF-74 Pydantic validation (orthogonal fix)
- `1490c1ca` - DEF-108 timeout fix (separate issue)

---

## ✅ NEXT ACTIONS

1. **User confirmation:** Verify this matches observed behavior
2. **Solution selection:** Option A (hotfix) or Option C (proper fix)?
3. **Implementation:** If approved, implement + test
4. **Merge strategy:** Standalone PR or merge with DEF-108?

**Estimated total time:** 2-3 hours (Option C) or 30 min (Option A)
