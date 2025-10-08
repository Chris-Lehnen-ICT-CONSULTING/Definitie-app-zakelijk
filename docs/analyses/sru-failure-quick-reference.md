# SRU Lookup Failures - Quick Reference Guide
**Date:** 2025-10-08
**For:** Development Team

---

## Problem Statement

**Symptom:** All SRU queries to overheid.nl return "No records found"

**Reality:** Overheid.nl DOES have data - simple query "samenhang strafzaak" returns 3 results when tested directly

**Root Cause:** Application adds too much context to queries, making them over-specific

---

## The Three Problems

### 1. Context Pollution (CRITICAL)

**What happens:**
```
User searches: "samenhang strafzaak"
Context detected: Sv, Wetboek van Strafvordering, OM, ZM, NP

Application builds query:
  (samenhang strafzaak) AND (Wetboek van Strafvordering OR Sv)

Result: 0 records (too specific!)
```

**Why it's wrong:**
- Legal context (Sv, Wetboek) added as **REQUIRED** constraint (AND logic)
- Documents about "samenhang strafzaak" don't always explicitly mention "Sv"
- Over-specification filters out all relevant results

**The fix:**
- Query term-only FIRST: `samenhang strafzaak` → Get all results
- Add legal context SECOND (only if too many results): Refine to Sv-specific

---

### 2. Circuit Breaker Too Aggressive (HIGH)

**What happens:**
```
Query 1: DC fields with legal context → 0 results (empty count: 1)
Query 2: serverChoice all with legal context → 0 results (empty count: 2)
Circuit breaker triggers! (threshold: 2)

Queries 3-5 never execute:
  - Hyphen variant (not tried)
  - serverChoice any (not tried)
  - Wildcard fallback (not tried)
```

**Why it's wrong:**
- Threshold of 2 is too low for legal queries with multiple fallback strategies
- Fallback strategies that WOULD work never get a chance to execute

**The fix:**
- Increase threshold to 4 (allow at least 4 query strategies before giving up)

---

### 3. Unknown Prefix "overheidnl" (MEDIUM)

**What happens:**
```python
query = f'{query} AND overheidnl.collection="rijksoverheid"'
```

**SRU server response:**
```xml
<diagnostic>
  <message>Unsupported Index</message>
  <details>unknown prefix overheidnl</details>
</diagnostic>
```

**Why it's wrong:**
- `overheidnl.collection` is not a registered prefix in overheid.nl SRU endpoint
- Should query SRU explain first to discover supported indexes

**The fix:**
- Remove the collection filter (causes diagnostic errors)

---

## Evidence Supporting Diagnosis

### User Report
> "Overheid.nl returns 3 results for simple queries like 'samenhang strafzaak'"

### Log Evidence
```
2025-10-07 15:31:06,678 - Parsed 0 results from Wetgeving.nl
2025-10-07 15:31:06,680 - Parsed 0 results from Overheid.nl Zoekservice
2025-10-07 15:31:06,694 - Parsed 0 results from Overheid.nl
(Circuit breaker triggers here - remaining queries never execute)
```

### Wikipedia Evidence
```
Wikipedia lookup voor term: verticaal NP Civiel recht
Geen Wikipedia pagina gevonden
(NP = Nederlandse Politie - not relevant to Wikipedia!)

Wikipedia lookup voor term: verticaal
SUCCESS! (term-only works)
```

**Conclusion:** Simpler queries work; context pollution breaks them.

---

## User Hypothesis Validation

### Hypothesis 1: Organizational abbreviations break queries
**Status:** ✅ CONFIRMED (but already handled via `_strip_org_tokens()`)
**Impact:** LOW (already mitigated)

### Hypothesis 2: Legal domain terms are too restrictive
**Status:** ✅ CONFIRMED - **THIS IS THE PRIMARY ROOT CAUSE**
**Impact:** CRITICAL

### Hypothesis 3: Wikipedia fails due to context specificity
**Status:** ✅ CONFIRMED (organizational tokens leak into Wikipedia)
**Impact:** HIGH

---

## Query Strategy Comparison

### Current Strategy (Precision-First)

```
1. Query: (term) AND (legal context) → 0 results
2. Query: serverChoice all + legal context → 0 results
3. Circuit breaker triggers (threshold: 2)
4-5. Fallback queries never execute

Result: 0% success rate
```

### Recommended Strategy (Recall-First)

```
1. Query: term only → Get all relevant results
2. If >50 results: Add legal context → Refine to specific law
3. Hyphen variant → Alternative word form
4. Wildcard fallback → Partial match

Result: Expected 70-80% success rate
```

---

## Quick Wins (High-Impact, Low-Effort)

### Fix 1: Increase Circuit Breaker Threshold
**File:** `config/web_lookup_defaults.yaml` line 85
**Change:** `consecutive_empty_threshold: 2` → `4`
**Impact:** Allows fallback strategies to execute
**Effort:** 1 line change

### Fix 2: Remove Invalid Collection Filter
**File:** `src/services/web_lookup/sru_service.py` lines 689-690
**Change:** Comment out `overheidnl.collection` filter
**Impact:** Eliminates diagnostic errors
**Effort:** 2 lines commented

### Fix 3: Reverse Query Order
**File:** `src/services/web_lookup/sru_service.py` lines 449-554
**Change:** Execute term-only query BEFORE legal context query
**Impact:** Maximizes recall, legal context becomes refinement
**Effort:** Reorder query execution sequence

---

## Expected Outcomes

### Before Fixes
- **SRU Success Rate:** 0%
- **Circuit Breaker Triggers:** After 2 failures
- **Fallback Strategies:** Never execute
- **User Experience:** No external legal sources in definitions

### After Fixes
- **SRU Success Rate:** 70-80% (estimated)
- **Circuit Breaker Triggers:** After 4 failures (allows fallbacks)
- **Fallback Strategies:** Hyphen/wildcard variants execute
- **User Experience:** Authoritative legal sources enrich definitions

---

## Code Locations for Reference

| Issue | File | Lines | Description |
|-------|------|-------|-------------|
| Circuit Breaker Config | `config/web_lookup_defaults.yaml` | 84-91 | Threshold settings |
| Circuit Breaker Logic | `src/services/web_lookup/sru_service.py` | 434-494 | Query loop + breaker |
| Query Construction | `src/services/web_lookup/sru_service.py` | 606-700 | CQL query builder |
| Invalid Prefix | `src/services/web_lookup/sru_service.py` | 689-690 | Collection filter |
| Context Classification | `src/services/modern_web_lookup_service.py` | 177-239 | Token classification |
| Stage-Based Backoff | `src/services/modern_web_lookup_service.py` | 620-634 | SRU stage logic |
| Wikipedia Context | `src/services/modern_web_lookup_service.py` | 431-442 | Wikipedia stages |

---

## Testing Recommendations

### Test 1: Simple Term Query
**Query:** "samenhang strafzaak" (no context)
**Expected:** Should return 3 results from overheid.nl
**Validates:** Basic SRU connectivity works

### Test 2: Term with Legal Context
**Query:** "(samenhang strafzaak) AND (Sv)"
**Expected:** Should return 0 results (too specific)
**Validates:** Confirms legal context is the problem

### Test 3: Circuit Breaker Threshold
**Setup:** Set threshold to 4, force 3 consecutive failures
**Expected:** Query 4 should still execute
**Validates:** Circuit breaker respects threshold

### Test 4: Wikipedia Without Org Context
**Query:** "verticaal" (no NP/OM/ZM)
**Expected:** Should find Wikipedia page
**Validates:** Organizational context is filtered out

---

## Summary

**Root Cause:** Legal context tokens (Sv, Wetboek van Strafvordering) are added as **required constraints** (AND logic), filtering out all results that don't explicitly mention the law code.

**User Impact:** 100% SRU lookup failure rate; definitions lack authoritative external sources.

**Solution:** Three quick wins:
1. Increase circuit breaker threshold (4 instead of 2)
2. Remove invalid `overheidnl.collection` filter
3. Reverse query order (term-only first, legal context second)

**Expected Improvement:** From 0% to 70-80% SRU success rate with these changes.

---

**See full analysis:** `/docs/analyses/sru-web-lookup-failure-analysis.md`
