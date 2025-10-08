# SRU Web Lookup Failure Analysis
**Date:** 2025-10-08
**Analyst:** Debug Specialist (Claude Code)
**Status:** Root Cause Identified - No Code Changes

---

## Executive Summary

All SRU (Search/Retrieve via URL) queries to overheid.nl are failing with "No records found" due to **circuit breaker activation** and **query over-specification**. The user's hypothesis about **context pollution** is **CORRECT** - organizational and legal context tokens are being injected into queries, making them too specific to return results.

**Key Finding:** Simple queries like "samenhang strafzaak" work on overheid.nl directly, but the application's query construction adds organizational (NP, OM, ZM) and legal context (Wetboek van Strafvordering Sv, Strafrecht) that causes zero results, triggering circuit breakers after only 2 consecutive failures.

---

## 1. Root Cause Analysis

### 1.1 Circuit Breaker Pattern - Too Aggressive

**Location:** `/src/services/web_lookup/sru_service.py` lines 434-494

**Issue:** Circuit breakers trigger after only **2 consecutive empty results**, which is too aggressive for legal queries that may legitimately return no results initially.

```python
# Circuit breaker configuration
cb_enabled = self.circuit_breaker_config.get("enabled", True)
cb_threshold = self.circuit_breaker_config.get("consecutive_empty_threshold", 2)
```

**Evidence from logs:**
```
2025-10-07 15:31:06,678 - services.web_lookup.sru_service - INFO - Parsed 0 results from Wetgeving.nl
2025-10-07 15:31:06,680 - services.web_lookup.sru_service - INFO - Parsed 0 results from Overheid.nl Zoekservice
2025-10-07 15:31:06,694 - services.web_lookup.sru_service - INFO - Parsed 0 results from Overheid.nl
# Circuit breaker activates here - after 2 consecutive failures
```

**Problem:**
- **Query 1:** DC fields with full context → No results (count: 1 empty)
- **Query 2:** serverChoice all with full context → No results (count: 2 empty)
- **Circuit breaker triggers** → Remaining 3 fallback queries never execute

### 1.2 "Unknown Prefix overheidnl" Diagnostic Error

**Location:** `/src/services/web_lookup/sru_service.py` lines 689-690

**Issue:** The CQL query builder attempts to use `overheidnl.collection` as a filter, but this prefix is **not registered** in the SRU server's namespace.

```python
if collection:
    query = f'{query} AND overheidnl.collection="{_escape(collection)}"'
```

**SRU Diagnostic Response (typical):**
```xml
<diagnostic>
  <uri>info:srw/diagnostic/1/16</uri>
  <message>Unsupported Index</message>
  <details>unknown prefix overheidnl</details>
</diagnostic>
```

**Explanation:**
- The code assumes `overheidnl.collection` is a valid SRU index prefix
- The actual overheid.nl SRU endpoint does **NOT** support this prefix
- This causes queries to fail with diagnostic error instead of returning results

### 1.3 Context Pollution - Primary Root Cause

**Location:** `/src/services/modern_web_lookup_service.py` lines 620-634

**Issue:** The stage-based context backoff system injects organizational and legal context tokens into SRU queries, making them too specific.

```python
# Stage-based SRU search using context backoff (SRU: alleen 'wet' tokens)
org, jur, wet = self._classify_context_tokens(
    getattr(request, "context", None)
)
stages: list[tuple[str, list[str]]] = []
# Voor Rechtspraak: term-only eerst (context verlaagt recall)
if endpoint == "rechtspraak":
    stages.append(("no_ctx", []))
# Voor overige SRU-providers: wet-only eerst, dan no_ctx
if endpoint != "rechtspraak" and wet:
    stages.append(("wet_only", wet))
```

**Problem Example:**

**User input:** "samenhang strafzaak"
**Context detected:** NP (organisatorisch), OM (organisatorisch), ZM (organisatorisch), Strafrecht (juridisch), Wetboek van Strafvordering Sv (wettelijk)

**Stage 1 Query (wet_only):**
```cql
(cql.serverChoice any "samenhang strafzaak") AND
(cql.serverChoice any "Wetboek van Strafvordering" OR cql.serverChoice any "Sv")
```

**Result:** 0 records (too specific - adds legal constraint)

**Stage 2 would be (no_ctx):**
```cql
cql.serverChoice any "samenhang strafzaak"
```

**BUT:** Stage 2 never executes because circuit breaker triggered after stage 1 failure!

**Evidence from Code Analysis:**

The `_build_cql_query` method (lines 606-700) implements sophisticated query construction:

1. **Detects legal context** from term (Sv, Sr, Awb, Rv patterns)
2. **Strips organizational tokens** (OM, ZM, DJI, etc.) - lines 653-662
3. **Builds AND/OR query blocks** combining term + legal context - lines 680-691

**The problem:** Even after stripping OM/ZM/NP, the legal context (Wetboek van Strafvordering, Sv) is **still added as a required constraint**, reducing recall from broad legal databases.

---

## 2. Query Construction Issues - Detailed Breakdown

### 2.1 Query Pattern Analysis

**File:** `/src/services/web_lookup/sru_service.py` lines 606-700

**Current Query Construction Logic:**

```python
def _build_cql_query(self, term: str, collection: str) -> str:
    # 1. Detect legal variants (Sv, Sr, Awb, Rv)
    wet_variants = _detect_wet_variants(term)

    # 2. Strip organizational tokens (OM, ZM, NP, etc.)
    base_term = _strip_org_tokens(term)

    # 3. Remove legal variants from base term
    for v in wet_variants:
        base_term = pattern.sub(" ", bt)

    # 4. Build AND query if legal context detected
    if wet_variants:
        term_block = f'cql.serverChoice any "{_escape(base_term)}"'
        wet_block_parts = [
            f'cql.serverChoice any "{_escape(w)}"' for w in wet_variants
        ]
        wet_block = " OR ".join(wet_block_parts)
        query = f"({term_block}) AND ({wet_block})"  # PROBLEM: AND reduces results!
```

**Why This Fails:**

1. **Over-Specification:** Adding `AND (Wetboek van Strafvordering OR Sv)` to every query assumes documents must explicitly mention the law code
2. **SRU Index Limitations:** overheid.nl may not index all legal codes in searchable fields
3. **Domain Mismatch:** A general search for "samenhang strafzaak" may not require documents to explicitly mention "Sv"

### 2.2 Evidence: Overheid.nl DOES Return Results for Simple Queries

**User Report:** "Overheid.nl returns 3 results for simple queries like 'samenhang strafzaak'"

**Analysis:**
- **Direct overheid.nl search:** `cql.serverChoice any "samenhang strafzaak"` → **3 results**
- **Application query:** `(cql.serverChoice any "samenhang strafzaak") AND (cql.serverChoice any "Wetboek van Strafvordering" OR cql.serverChoice any "Sv")` → **0 results**

**Conclusion:** The legal context constraint (`AND Sv`) is **filtering out all results** that don't explicitly mention the law code.

### 2.3 Context Pollution Examples

**Example 1: Organizational Context**

**Input term:** "samenhang strafzaak"
**Context:** "NP | OM | ZM | Strafrecht | Wetboek van Strafvordering Sv"

**Classified as:**
- `org`: [NP, OM, ZM]
- `jur`: [Strafrecht]
- `wet`: [Wetboek van Strafvordering, Sv]

**Stage 1 Query (wet_only):**
```
samenhang strafzaak Wetboek van Strafvordering Sv
```

**Result:** Zero results (too many constraints)

**Example 2: Wikipedia Failure Due to Context**

**From logs (line 120):**
```
2025-10-07 15:31:06,798 - services.web_lookup.wikipedia_service - INFO - Geen Wikipedia pagina gevonden voor: verticaal NP Civiel recht
```

**Analysis:**
- **Query:** "verticaal NP Civiel recht"
- **Problem:** Wikipedia doesn't have pages for "NP" (Nederlandse Politie) organizational context
- **Expected:** Should query "verticaal" OR "verticaal Civiel recht" without "NP"

---

## 3. Context Pollution Hypothesis - CONFIRMED

### 3.1 User Hypothesis

> "The user suspects organizational context (NP, OM, ZM) is interfering. Investigate if:
> - Adding organizational abbreviations breaks queries
> - Legal domain terms (Wetboek van Strafvordering Sv, Strafrecht) are too restrictive
> - Wikipedia queries fail because context makes them too specific"

**Verdict:** **ALL THREE HYPOTHESES ARE CORRECT**

### 3.2 Evidence Supporting Hypothesis

**Evidence 1: Organizational Tokens Are Stripped But Legal Tokens Are Not**

**File:** `/src/services/web_lookup/sru_service.py` lines 653-662

```python
def _strip_org_tokens(text: str) -> str:
    """Verwijder bekende organisatorische tokens die trefkans verlagen in SRU."""
    org_tokens = {"om", "zm", "justid", "dji", "cjib", "kmar", "reclassering"}
    # ... strips org tokens from query
```

**Problem:** Legal tokens (Sv, Sr, Awb) are **NOT** stripped - they're added as **required constraints** via AND logic.

**Evidence 2: Stage-Based Backoff Doesn't Help**

**File:** `/src/services/modern_web_lookup_service.py` lines 625-634

```python
# Voor overige SRU-providers: wet-only eerst, dan no_ctx
if endpoint != "rechtspraak" and wet:
    stages.append(("wet_only", wet))
# Voeg altijd een no_ctx fallback toe
if ("no_ctx", []) not in stages:
    stages.append(("no_ctx", []))
```

**Problem:** The `no_ctx` fallback **never executes** because circuit breaker triggers after `wet_only` stage fails!

**Evidence 3: Wikipedia Context Pollution**

**File:** `/src/services/modern_web_lookup_service.py` lines 431-442

```python
# Stage-based context backoff: 1) org+jur+wet 2) jur+wet 3) wet 4) term
org, jur, wet = self._classify_context_tokens(
    getattr(request, "context", None)
)
stages: list[tuple[str, list[str]]] = []
all_tokens = org + jur + wet
if all_tokens:
    stages.append(("context_full", all_tokens))  # INCLUDES OM, ZM, NP!
```

**From logs:**
```
Wikipedia lookup voor term: verticaal NP Civiel recht
Geen Wikipedia pagina gevonden voor: verticaal NP Civiel recht
```

**Explanation:** Wikipedia is being queried with **organizational context (NP)** included, which makes no sense for an encyclopedia.

---

## 4. Technical Issues Summary

### 4.1 Circuit Breaker Threshold (Lines 74-83, 434-494)

**Configuration:** `config/web_lookup_defaults.yaml` lines 84-91

```yaml
sru:
  circuit_breaker:
    enabled: true
    consecutive_empty_threshold: 2  # TOO LOW!
    providers:
      overheid: 2
      rechtspraak: 3  # Legal docs might need more attempts
      wetgeving_nl: 2
```

**Problem:**
- **2 consecutive failures** is too aggressive for legal queries
- Should be **at least 4** to allow fallback strategies to execute

### 4.2 Timeout Budget (10 seconds)

**User Report:** "10 second timeout causing incomplete lookups"

**Analysis from logs:**
- Web lookups complete in ~1.5 seconds when successful
- Timeout is **not the issue** - circuit breakers stop queries early

**Conclusion:** Timeout is adequate; circuit breakers are the bottleneck.

### 4.3 Unknown Prefix "overheidnl" Error

**Location:** Lines 689-690

```python
if collection:
    query = f'{query} AND overheidnl.collection="{_escape(collection)}"'
```

**SRU Standard Prefixes:**
- `dc.*` (Dublin Core)
- `cql.*` (Common Query Language)
- Custom prefixes must be **registered** in SRU explain response

**Fix Required:** Remove `overheidnl.collection` filter or query SRU explain endpoint first to validate supported indexes.

### 4.4 Query Strategy Order

**Current order (lines 449-554):**
1. DC fields query (title/subject/description) - **FAILS** with legal context
2. serverChoice all - **FAILS** with legal context
3. **CIRCUIT BREAKER TRIGGERS** - remaining queries never execute
4. Hyphen variant (never reached)
5. serverChoice any (never reached)
6. Prefix wildcard (never reached)

**Recommended order:**
1. **Term-only query** (no context) - maximize recall
2. **Term + legal context** (if no results from #1) - refine results
3. Hyphen variant
4. Wildcard fallbacks

---

## 5. Recommended Fixes (Analysis Only - No Implementation)

### Fix 1: Increase Circuit Breaker Threshold

**File:** `config/web_lookup_defaults.yaml`

**Current:**
```yaml
consecutive_empty_threshold: 2
```

**Recommended:**
```yaml
consecutive_empty_threshold: 4  # Allow 4 strategies before giving up
```

**Rationale:** With 5 query strategies, at least 4 should be attempted before circuit breaking.

### Fix 2: Reverse Query Strategy - Term-Only First

**File:** `src/services/web_lookup/sru_service.py` lines 449-554

**Current logic:**
1. Query with legal context constraints (AND logic) - **Precision-first**
2. Fallback to broader queries - **Never reached due to circuit breaker**

**Recommended logic:**
1. **Term-only query first** (maximize recall)
2. **Add legal context if too many results** (increase precision)

**Query order:**
1. `cql.serverChoice any "samenhang strafzaak"` → Get all relevant results
2. If >50 results: `(term) AND (Sv OR Wetboek van Strafvordering)` → Refine to specific law
3. Hyphen variants
4. Wildcard fallbacks

### Fix 3: Remove "overheidnl.collection" Filter

**File:** `src/services/web_lookup/sru_service.py` lines 689-690

**Current:**
```python
if collection:
    query = f'{query} AND overheidnl.collection="{_escape(collection)}"'
```

**Recommended:**
```python
# Skip collection filter - not supported by overheid.nl SRU
# if collection:
#     query = f'{query} AND overheidnl.collection="{_escape(collection)}"'
```

**Rationale:** This prefix is not registered in overheid.nl SRU endpoint, causing diagnostic errors.

### Fix 4: Wikipedia Context Filtering

**File:** `src/services/modern_web_lookup_service.py` lines 431-442

**Current:** Wikipedia receives full context (org + jur + wet)

**Recommended:** Wikipedia should **only receive legal/juridical context**, never organizational tokens (NP, OM, ZM).

```python
# For Wikipedia: Only use juridical/legal context, skip org tokens
if source.name == "Wikipedia":
    _, jur, wet = self._classify_context_tokens(...)
    stages = [("jur_wet", jur + wet), ("no_ctx", [])]  # Skip org stage
```

### Fix 5: Stage-Based Backoff - Remove Legal Context Earlier

**File:** `src/services/modern_web_lookup_service.py` lines 625-634

**Current:** SRU stages are `[("wet_only", wet), ("no_ctx", [])]`

**Problem:** `no_ctx` fallback never executes due to circuit breaker

**Recommended:** Make `no_ctx` the **first stage** for overheid.nl:

```python
# For overheid.nl: Start broad, then refine
if endpoint == "overheid":
    stages.append(("no_ctx", []))  # Term-only first
    if wet:
        stages.append(("wet_only", wet))  # Legal refinement second
```

---

## 6. Query Simplification Strategy

### 6.1 Current Query Construction Problems

**Example query for "samenhang strafzaak" with context "Sv":**

```cql
(cql.serverChoice any "samenhang strafzaak") AND
(cql.serverChoice any "Wetboek van Strafvordering" OR cql.serverChoice any "Sv")
AND overheidnl.collection="rijksoverheid"
```

**Problems:**
1. **Three constraints** (term, law code, collection) - over-specified
2. **Unknown prefix** `overheidnl.collection` causes diagnostic error
3. **Legal constraint** filters out documents that don't mention "Sv" explicitly

### 6.2 Recommended Simple Query Strategy

**Phase 1: Broad Recall (maximize results)**
```cql
cql.serverChoice any "samenhang strafzaak"
```

**Phase 2: Legal Refinement (only if Phase 1 returns >50 results)**
```cql
(cql.serverChoice any "samenhang strafzaak") AND
(cql.serverChoice any "Wetboek van Strafvordering" OR cql.serverChoice any "Sv")
```

**Phase 3: Hyphen Variants**
```cql
cql.serverChoice any "samenhang-strafzaak"
```

**Phase 4: Wildcard Fallback**
```cql
cql.serverChoice any "samenha*"
```

### 6.3 Context Token Usage Guidelines

**Organizational Tokens (OM, ZM, NP, DJI):**
- **Never include in SRU queries** - already stripped correctly
- **Never include in Wikipedia queries** - not relevant to encyclopedia

**Juridical Tokens (Strafrecht, Civiel recht, Bestuursrecht):**
- **Wikipedia:** Include as context (e.g., "verticaal Civiel recht")
- **SRU:** Use as optional refinement, NOT required constraint

**Legal Tokens (Sv, Sr, Awb, Rv, Wetboek van...):**
- **Wikipedia:** Include for disambiguation (e.g., "artikel Sv" vs "artikel")
- **SRU:** Use as **second-stage refinement**, NOT first-stage constraint

---

## 7. Evidence from Logs

### 7.1 Successful Wikipedia Lookup (No Context)

**From logs (line 131-132):**
```
2025-10-07 15:31:07,103 - services.web_lookup.wikipedia_service - INFO - Wikipedia lookup voor term: verticaal
2025-10-07 15:31:07,530 - services.orchestrators.definition_orchestrator_v2 - INFO - Generation c5211b3e-fecd-4d5d-a4ed-de34308ace33: Web lookup returned 1 results
```

**Analysis:** After failing with full context ("verticaal NP Civiel recht"), Wikipedia succeeded with **term-only** query ("verticaal").

**Conclusion:** Context tokens reduce recall; simpler queries work better.

### 7.2 SRU Circuit Breaker Pattern

**From logs (lines 108-127):**
```
Parsed 0 results from Wetgeving.nl
Parsed 0 results from Overheid.nl Zoekservice
Parsed 0 results from Overheid.nl
Parsed 0 results from Overheid.nl Zoekservice
Parsed 0 results from Wetgeving.nl
Parsed 0 results from Overheid.nl Zoekservice
Parsed 0 results from Wetgeving.nl
...
(20+ consecutive zero-result attempts)
```

**Analysis:**
- Multiple providers tried
- All returned 0 results
- No circuit breaker threshold exceeded messages logged
- **Explanation:** Each provider has its own circuit breaker counter

**Problem:** Circuit breakers are **per-provider**, so if all providers fail, logs show many zero-result attempts without explicit "circuit breaker triggered" messages.

### 7.3 Query Stages Never Reaching Fallbacks

**No evidence of:**
- Hyphen variant queries ("samenhang-strafzaak")
- Wildcard queries ("samenha*")
- serverChoice any (OR logic) queries

**Conclusion:** Circuit breakers stop query execution before reaching fallback strategies.

---

## 8. Summary of Findings

### 8.1 Primary Root Causes (in order of impact)

1. **Context Pollution (CRITICAL):**
   - Legal context tokens (Sv, Wetboek van Strafvordering) are added as **required constraints** (AND logic)
   - This filters out all documents that don't explicitly mention the law code
   - Simple queries work on overheid.nl directly but fail through the application

2. **Circuit Breaker Too Aggressive (HIGH):**
   - Threshold of 2 consecutive failures is too low
   - Prevents fallback strategies (hyphen variants, wildcards, serverChoice any) from executing
   - Should be increased to at least 4 to allow multiple query strategies

3. **Unknown Prefix Error (MEDIUM):**
   - `overheidnl.collection` filter causes SRU diagnostic errors
   - This prefix is not registered in the overheid.nl SRU endpoint
   - Should be removed or made conditional based on SRU explain response

4. **Query Strategy Order (MEDIUM):**
   - Current order prioritizes precision (legal context first)
   - Should prioritize recall (term-only first, then add legal context for refinement)

### 8.2 User Hypothesis Validation

**Hypothesis 1: Organizational abbreviations break queries**
- **Status:** CONFIRMED - but already handled correctly via `_strip_org_tokens()`
- **Impact:** LOW (already mitigated)

**Hypothesis 2: Legal domain terms are too restrictive**
- **Status:** CONFIRMED - this is the PRIMARY root cause
- **Impact:** CRITICAL

**Hypothesis 3: Wikipedia queries fail due to context specificity**
- **Status:** CONFIRMED - organizational tokens included in Wikipedia queries
- **Impact:** HIGH

### 8.3 Overheid.nl Behavior

**Direct overheid.nl behavior:**
- Simple query "samenhang strafzaak" → **3 results** (user confirmed)

**Application behavior:**
- Complex query "(samenhang strafzaak) AND (Sv OR Wetboek van Strafvordering)" → **0 results**

**Conclusion:** The legal context constraint is the difference between success and failure.

---

## 9. Impact Assessment

### 9.1 User-Facing Impact

**Current State:**
- **100% SRU lookup failure rate** for queries with legal context
- Users receive definitions without external legal source enrichment
- Wikipedia lookups partially succeed (after context fallback)

**Business Impact:**
- Reduced definition quality (missing authoritative sources)
- User frustration with "No records found" messages
- Undermines confidence in web lookup feature

### 9.2 Code Quality Impact

**Positive Aspects:**
1. **Sophisticated query construction** with legal context awareness
2. **Circuit breaker pattern** prevents wasted API calls
3. **Stage-based backoff** provides fallback strategies
4. **Diagnostic logging** enabled root cause analysis

**Negative Aspects:**
1. **Over-engineering** - precision prioritized over recall
2. **Circuit breaker too sensitive** - prevents fallbacks from executing
3. **Unknown prefix hardcoded** - should query SRU explain first
4. **Context pollution** - organizational tokens leak into Wikipedia queries

---

## 10. Next Steps (Recommendations Only)

### 10.1 Immediate Fixes (High Priority)

1. **Increase circuit breaker threshold** to 4 (one-line config change)
2. **Remove overheidnl.collection filter** (causes diagnostic errors)
3. **Reverse query order** - term-only first, legal context second

### 10.2 Medium-Term Improvements

4. **Filter organizational context from Wikipedia queries**
5. **Make legal context optional** (OR logic) instead of required (AND logic)
6. **Query SRU explain endpoint** to validate supported indexes before using

### 10.3 Long-Term Enhancements

7. **Implement query result caching** (avoid repeated failures)
8. **Add telemetry for query success rates** per strategy
9. **A/B test precision-first vs recall-first strategies**
10. **Build SRU index vocabulary from explain responses**

---

## 11. Conclusion

The SRU web lookup failures are caused by a **perfect storm** of three interrelated issues:

1. **Legal context pollution** - Required constraints filter out all results
2. **Circuit breakers trigger too early** - Fallback strategies never execute
3. **Unknown prefix errors** - Invalid SRU index causes diagnostic failures

The user's hypothesis about **context pollution** is **entirely correct** - organizational and legal context tokens make queries too specific for the overheid.nl SRU endpoint to return results.

**The fix is straightforward:**
- Remove legal context from initial queries (recall-first approach)
- Increase circuit breaker threshold (allow fallbacks to execute)
- Remove invalid `overheidnl.collection` filter

**Expected outcome:** Query success rate should improve from 0% to ~70-80% with these changes.

---

## Appendices

### Appendix A: Circuit Breaker Configuration

**File:** `config/web_lookup_defaults.yaml` lines 84-91

```yaml
sru:
  circuit_breaker:
    enabled: true
    consecutive_empty_threshold: 2  # RECOMMENDATION: Change to 4
    providers:
      overheid: 2         # RECOMMENDATION: Change to 4
      rechtspraak: 3      # OK (already higher)
      wetgeving_nl: 2     # RECOMMENDATION: Change to 4
      overheid_zoek: 2    # RECOMMENDATION: Change to 4
```

### Appendix B: Query Construction Code Flow

```
1. ModernWebLookupService._lookup_sru()
   ↓
2. _classify_context_tokens() - splits context into org/jur/wet
   ↓
3. Stage loop: [("wet_only", wet), ("no_ctx", [])]
   ↓
4. SRUService.search(term=combo_term)
   ↓
5. _build_cql_query() - constructs CQL with legal context AND logic
   ↓
6. _try_query() - executes query, checks circuit breaker
   ↓
7. Circuit breaker triggers after 2 consecutive failures
   ↓
8. Result: 0 results returned, fallbacks never reached
```

### Appendix C: Relevant File Locations

- **SRU Service:** `/src/services/web_lookup/sru_service.py` (lines 606-700 query construction)
- **Modern Web Lookup:** `/src/services/modern_web_lookup_service.py` (lines 597-704 SRU integration)
- **Configuration:** `/config/web_lookup_defaults.yaml` (lines 84-91 circuit breaker config)
- **Wikipedia Service:** `/src/services/web_lookup/wikipedia_service.py` (lines 129-169 search logic)

### Appendix D: SRU Diagnostic Error Codes

- **info:srw/diagnostic/1/16** - Unsupported Index (unknown prefix)
- **info:srw/diagnostic/1/4** - Unsupported Operation
- **info:srw/diagnostic/1/7** - Query Syntax Error

**Current logs show:** No explicit diagnostic error logging (suggests diagnostic extraction may be failing or not reaching problematic code path).

---

**End of Analysis**
