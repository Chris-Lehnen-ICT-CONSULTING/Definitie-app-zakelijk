# Synonym Pages Review - Executive Summary

**Date:** 2025-10-10
**Files Reviewed:** `src/pages/synonym_admin.py` (460 lines), `src/pages/synonym_metrics.py` (78 lines)
**Status:** ⚠️ **DO NOT DEPLOY - Critical Bugs Found**

## Critical Bugs (Must Fix)

### 🔴 Bug #1: Non-Existent API Call
**Location:** `synonym_admin.py:299`

```python
all_groups = registry.get_all_groups()  # ❌ METHOD DOES NOT EXIST
```

**Impact:** Page will crash with `AttributeError` on first load.

**Fix:** Add to `SynonymRegistry`:
```python
def get_all_groups(self, limit: int | None = None) -> list[SynonymGroup]:
    """Get all synonym groups."""
    with self._get_connection() as conn:
        query = "SELECT * FROM synonym_groups ORDER BY updated_at DESC"
        if limit:
            query += f" LIMIT {limit}"
        cursor = conn.execute(query)
        return [self._row_to_group(row) for row in cursor.fetchall()]
```

---

### 🔴 Bug #2: N+1 Query Problem
**Location:** `synonym_admin.py:299-312`

```python
for group in all_groups:  # 100 groups = 100 queries!
    members = registry.get_group_members(group_id=group.id, ...)
```

**Impact:** Severe performance degradation (100+ DB queries per page load).

**Fix:** Add to `SynonymRegistry`:
```python
def get_all_members_filtered(
    self,
    statuses: list[str] | None = None,
    min_weight: float = 0.0,
    term_search: str | None = None,
    limit: int | None = None,
    offset: int = 0
) -> list[SynonymGroupMember]:
    """Get all members across groups with filters (single query)."""
    with self._get_connection() as conn:
        query = "SELECT * FROM synonym_group_members WHERE weight >= ?"
        params = [min_weight]

        if statuses:
            placeholders = ", ".join("?" for _ in statuses)
            query += f" AND status IN ({placeholders})"
            params.extend(statuses)

        if term_search:
            query += " AND term LIKE ?"
            params.append(f"%{term_search}%")

        query += " ORDER BY weight DESC, is_preferred DESC"

        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        cursor = conn.execute(query, params)
        return [self._row_to_member(row) for row in cursor.fetchall()]
```

---

### 🔴 Bug #3: Wrong Statistics Keys
**Location:** `synonym_metrics_tab.py:195, 209, 213, 254`

```python
# ❌ Wrong keys (will return 0 for all counts)
pending_count = stats.get('by_status', {}).get('ai_pending', 0)
source_stats = stats.get('by_source', {})

# ✅ Correct keys
pending_count = stats.get('members_by_status', {}).get('ai_pending', 0)
source_stats = stats.get('members_by_source', {})
```

**Impact:** Metrics dashboard shows incorrect data (all zeros).

---

### 🔴 Bug #4: Wrong Parameter Type
**Location:** `synonym_admin.py:309`

```python
order_by=['weight DESC']  # ❌ Expects str | None, receives list[str]
```

**Fix:**
```python
order_by='weight DESC'  # ✅ Single string
```

---

## High Priority Issues

### 🟡 Missing Async Error Handling
**Location:** `synonym_admin.py:193-199`

```python
# ❌ No error handling for timeouts
synonyms, ai_pending_count = asyncio.run(
    orchestrator.ensure_synonyms(...)
)
```

**Fix:**
```python
try:
    synonyms, ai_pending_count = asyncio.run(...)
except asyncio.TimeoutError:
    st.error("❌ GPT-4 timeout na 30 seconden")
except Exception as e:
    st.error(f"❌ Fout: {e}")
    logger.error(f"Generation error: {e}", exc_info=True)
```

---

### 🟡 No Database Schema Validation
**Impact:** Pages crash if `synonym_groups` tables don't exist.

**Fix:** Add to both pages before rendering:
```python
try:
    stats = registry.get_statistics()
except sqlite3.OperationalError:
    st.error(
        "❌ Synonym tables not found. "
        "Run migration: `python scripts/migrate_synonym_tables.py`"
    )
    st.stop()
```

---

## What Works Well ✅

1. **Architecture conformance** - Correct use of v3.1 orchestrator/registry pattern
2. **Streamlit patterns** - Good use of `@st.cache_resource`, session state
3. **UX design** - Progressive disclosure, confirmations for destructive actions
4. **SQL safety** - No injection vulnerabilities, parameterized queries
5. **Component structure** - Metrics page delegates well to reusable tab component

---

## Fix Effort Estimate

| Priority | Tasks | Time |
|----------|-------|------|
| Critical | Add registry methods, fix queries, fix stats keys | 2-3 hours |
| High | Error handling, schema validation | 1-2 hours |
| Testing | Unit + integration tests | 1-2 hours |
| **Total** | | **4-7 hours** |

---

## Recommendation

**DO NOT DEPLOY** current version to production.

**Action Plan:**
1. Fix critical bugs (#1-4) - **Required for basic functionality**
2. Add error handling and validation - **Required for stability**
3. Test thoroughly with realistic data - **Required for confidence**
4. Deploy to staging for user acceptance testing

**Post-fix assessment:** With bugs resolved, these pages provide excellent synonym management capabilities and integrate cleanly with existing architecture.

---

## Quick Reference: Files to Edit

```bash
# 1. Add missing methods
src/repositories/synonym_registry.py
  - Add: get_all_groups()
  - Add: get_all_members_filtered()
  - Add: count_members_filtered()

# 2. Fix admin page
src/pages/synonym_admin.py
  - Lines 299-312: Replace with get_all_members_filtered()
  - Lines 193-227: Add try/except for async calls
  - Add: Schema validation at top

# 3. Fix metrics tab
src/ui/tabs/synonym_metrics_tab.py
  - Lines 195, 209, 213, 254: Fix statistics keys

# 4. Add tests
tests/repositories/test_synonym_registry_queries.py (new)
tests/integration/test_synonym_admin_workflow.py (new)
```

---

**Detailed analysis:** See `docs/reviews/synonym-pages-technical-review.md`
