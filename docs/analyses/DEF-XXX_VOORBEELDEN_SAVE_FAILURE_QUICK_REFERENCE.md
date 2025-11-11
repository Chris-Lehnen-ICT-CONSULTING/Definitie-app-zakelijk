# DEF-XXX: Voorbeelden Save Failure - Quick Reference

## The Bug
**Voorbeelden generated but NOT saved to database** (silent data loss)

## Evidence
```
ID 143 (2025-11-11): 0 voorbeelden ❌
ID 92  (2025-10-31): 40 voorbeelden ✅
```

## Save Flow (8 Steps)

```
[PHASE 5] Orchestrator generates voorbeelden
          ↓
[PHASE 8] Stores in Definition.metadata["voorbeelden"]
          ↓
[PHASE 9] Saves Definition to database (metadata only)
          ↓
[UI]      Extracts voorbeelden from agent_result
          ↓
[UI]      Displays voorbeelden (✅ WORKS)
          ↓
[UI]      Calls _maybe_persist_examples() ← AUTO-SAVE TRIGGER
          ↓
[SAVE]    4 early exit checks (⚠️ FAILURE POINTS)
          ↓
[SAVE]    repo.save_voorbeelden() ← DATABASE WRITE
```

## 4 Early Exit Points (Where Save Can Fail Silently)

```python
# EXIT 1: Already saved flag (LINE 808) ⚠️ MOST LIKELY CULPRIT
if SessionStateManager.get_value(flag_key):
    return  # Silent exit, no log

# EXIT 2: No voorbeelden data (LINE 816-817)
if not raw:
    return  # Silent exit

# EXIT 3: Empty lists (LINE 846-848)
if total_new == 0:
    return  # Silent exit

# EXIT 4: Identical to DB (LINE 874-876)
if _norm(current_canon) == _norm(to_save):
    return  # Silent exit
```

## Top 3 Root Causes (Ranked)

### 🔴 #1: Session State Flag Reuse (90% probability)
- **Symptom:** Flag says "already saved" but it wasn't
- **Cause:** Same generation_id used twice OR flag not cleared
- **Evidence:** No error logs, voorbeelden display in UI but not in DB
- **Check:** Look for duplicate `generation_id` in session state

### 🟡 #2: Empty Voorbeelden Dict (60% probability)
- **Symptom:** Orchestrator returns structure with empty lists
- **Cause:** Timeout during generation OR partial failure
- **Evidence:** Log says "6 types generated" but counts are all 0
- **Check:** Enable DEBUG_EXAMPLES, look for [EXAMPLES-A] log with zero counts

### 🟡 #3: Pydantic Validation Failure (40% probability)
- **Symptom:** Schema rejects valid data
- **Cause:** DEF-74 validation too strict OR data format mismatch
- **Evidence:** Log shows "Voorbeelden validation failed" (not shown to user!)
- **Check:** `grep "validation failed" logs/*.log`

## Quick Debug Commands

```bash
# 1. Check for validation errors
grep "Voorbeelden validation failed" logs/*.log

# 2. Enable debug logging
export DEBUG_EXAMPLES=1
streamlit run src/main.py

# 3. Check session state flags
# In Streamlit console:
[k for k in st.session_state.keys() if 'examples_saved' in k]

# 4. Verify voorbeelden in metadata
sqlite3 data/definities.db "
SELECT id, begrip,
       json_extract(metadata, '$.voorbeelden') as meta_voorbeelden
FROM definities WHERE id = 143;"
```

## Smoking Gun Evidence

**If you see this → It's Hypothesis #1 (flag reuse):**
```
✅ Session state key exists: examples_saved_for_gen_{uuid}
✅ NO log line "Voorbeelden automatisch opgeslagen voor definitie 143"
✅ UI shows voorbeelden but database has 0 rows
```

**If you see this → It's Hypothesis #2 (empty dict):**
```
✅ Log: "[EXAMPLES-A] V2 generated | counts={voorbeeldzinnen: 0, ...}"
✅ Log: "Voorbeelden generated (6 types)" ← counts keys not values!
✅ NO save attempt (early exit at line 848)
```

**If you see this → It's Hypothesis #3 (validation):**
```
✅ Log: "Voorbeelden validation failed: ..."
✅ Pydantic error with field details
✅ NO flag set in session state (failed before line 900)
```

## Fix Recommendations

### IMMEDIATE (Stop Silent Failures)
```python
# Add logging to ALL early exits
logger.warning(f"⚠️ Voorbeelden save skipped: {reason}")

# Validate generation_id format
try:
    uuid.UUID(gen_id)
except ValueError:
    logger.error(f"Invalid gen_id: {gen_id}")
```

### SHORT-TERM (Better Visibility)
- Show validation errors to user (not just logs)
- Add save confirmation in UI
- Count ITEMS not TYPES in "generated" message

### LONG-TERM (Prevent Recurrence)
- Replace flag-based deduplication with DB timestamp check
- Add retry logic for failed saves
- Create admin page to show "definitions without voorbeelden"

## Testing After Fix

```python
# Reproduce bug:
1. Generate definition A → save voorbeelden → note gen_id
2. Generate definition B with SAME gen_id (simulate collision)
3. Check: Are B's voorbeelden saved?

# Verify fix:
1. Clear session state completely
2. Generate definition C
3. Check: voorbeelden in DB?
4. Regenerate C in same session
5. Check: no duplicate voorbeelden? Flag behavior correct?
```

## Related Issues
- **DEF-108:** Timeout fixes (might cause partial generation)
- **DEF-110:** Stale voorbeelden fix (session state changes)
- **DEF-74:** Pydantic validation (might reject valid data)

## Key Files
- `src/ui/components/definition_generator_tab.py:787-905` (save logic)
- `src/services/orchestrators/definition_orchestrator_v2.py:631-722` (generation)
- `src/database/definitie_repository.py:1474-1726` (DB save)
