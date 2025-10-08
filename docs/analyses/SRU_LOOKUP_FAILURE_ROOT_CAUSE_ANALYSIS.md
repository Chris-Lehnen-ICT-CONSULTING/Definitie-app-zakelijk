# SRU Lookup Failure - Root Cause Analysis

**Datum**: 2025-10-08
**Analyst**: Debug Specialist (Claude Code)
**Status**: CRITICAL - All SRU providers failing with 0 results

## Executive Summary

All SRU (Search/Retrieve via URL) endpoints are consistently returning 0 results due to **incorrect recordSchema configuration**. The circuit breaker is correctly triggering after 2 consecutive empty responses, but the underlying issue is that the queries themselves are malformed or incompatible with the target endpoints.

**Impact**: Complete failure of juridical source lookup (Wetgeving.nl, Overheid.nl, Rechtspraak.nl)

**Root Cause**: Schema mismatch and incompatible CQL query syntax

## Investigation Timeline

### 1. Symptom Analysis (from logs)

**Log Evidence**:
```
2025-10-07 15:31:06,678 - services.web_lookup.sru_service - INFO - Parsed 0 results from Wetgeving.nl
2025-10-07 15:31:06,680 - services.web_lookup.sru_service - INFO - Parsed 0 results from Overheid.nl Zoekservice
2025-10-07 15:31:06,694 - services.web_lookup.sru_service - INFO - Parsed 0 results from Overheid.nl
```

**Pattern**: 100% failure rate across ALL SRU providers (Wetgeving.nl, Overheid.nl, Overheid.nl Zoekservice)

### 2. Code Analysis

**File**: `/Users/chrislehnen/Projecten/Definitie-app/src/services/web_lookup/sru_service.py`

#### Current Configuration (Lines 85-129)

```python
"overheid": SRUConfig(
    name="Overheid.nl",
    base_url="https://repository.overheid.nl/sru",
    default_collection="rijksoverheid",
    record_schema="dc",  # ❌ NOT SUPPORTED
    confidence_weight=1.0,
    is_juridical=True,
),
"wetgeving_nl": SRUConfig(
    name="Wetgeving.nl",
    base_url="https://zoekservice.overheid.nl/sru/Search",
    default_collection="",
    record_schema="oai_dc",  # ❌ NOT SUPPORTED for BWB
    sru_version="2.0",
    confidence_weight=0.9,
    is_juridical=True,
    extra_params={"x-connection": "BWB"},
),
```

## Root Causes Identified

### ROOT CAUSE #1: Unsupported recordSchema (CRITICAL)

**Evidence from Live Testing**:

#### Overheid.nl (repository.overheid.nl)
- **Configured**: `recordSchema="dc"`
- **Server Response**:
  ```xml
  <diagnostic>
    <uri>info:srw/diagnostic/1/6</uri>
    <details>dc</details>
    <message>record schema not supported</message>
  </diagnostic>
  ```
- **Supported Schemas** (from Explain): `gzd`, `short`, `sitemap`, `manifest`
- **Fix Required**: Change from `"dc"` → `"gzd"`

#### Wetgeving.nl (BWB via zoekservice.overheid.nl)
- **Configured**: `recordSchema="oai_dc"` with `x-connection=BWB`
- **Server Response**:
  ```xml
  <diagnostic>
    <uri>info:srw/diagnostic/1/67</uri>
    <message>The record schema is known, but this particular record cannot be transformed into it</message>
  </diagnostic>
  ```
- **Status Code**: 406 (Not Acceptable)
- **Issue**: BWB connection does not support transformation to oai_dc/dc schemas
- **Tested Schemas**: All failed (gzd, oai_dc, dc) with x-connection=BWB
- **Possible Fix**: BWB connection may be incompatible; needs further investigation of alternative query methods

#### Overheid.nl Zoekservice
- **Issue**: Returns `info:srw/diagnostic/1/7` - "Mandatory parameter not supplied: x-connection"
- **Current Config**: No x-connection parameter
- **Fix Required**: Add mandatory x-connection parameter (value TBD)

### ROOT CAUSE #2: Incompatible CQL Query Syntax (SECONDARY)

**Code Location**: `_build_cql_query()` method (lines 575-663)

**Current Query Pattern** (without wet-context detection):
```cql
(dc.title="wetboek" OR dc.subject="wetboek" OR dc.description="wetboek")
```

**Problem**:
1. Uses Dublin Core field names (`dc.title`, `dc.subject`, `dc.description`)
2. These field names may not be supported by all SRU endpoints
3. The GZD schema has different field structure

**Evidence**: Even when servers return 200 OK, they parse 0 records because the query syntax doesn't match the schema's searchable fields.

### ROOT CAUSE #3: Missing Diagnostic Parsing (OPERATIONAL)

**Code Location**: `_parse_sru_response()` method (lines 741-777)

**Current Behavior**:
```python
logger.info(f"Parsed {len(results)} results from {config.name}")
```

**Problem**:
- Function returns empty list `[]` when diagnostics are present
- No logging of WHY the query failed
- Diagnostic messages are silently ignored in most code paths
- Only line 389-392 logs diagnostics, but incompletely

**Evidence from Code** (lines 269-302):
```python
def _extract_diag(xml_text: str) -> dict:
    # Diagnostic extraction exists but results aren't logged
```

The `_extract_diag()` helper is defined but diagnostic information is only stored in attempt records, never surfaced to application logs or users.

### ROOT CAUSE #4: Circuit Breaker Masking Underlying Issue (OPERATIONAL)

**Code Location**: Lines 408-514 (query cascade with circuit breaker)

**Current Logic**:
```python
# Query 1: DC fields
empty_result_count += 1
if cb_enabled and empty_result_count >= cb_threshold:
    logger.info("Circuit breaker triggered...")
    return []  # ❌ Stops after 2 empty results
```

**Problem**:
- Circuit breaker correctly stops wasteful queries
- BUT: Prevents discovery that ALL query strategies are failing
- No differentiation between "no data exists" vs "query is malformed"

**Evidence**:
- Circuit breaker triggers at threshold=2
- Logs show only 2 query strategies attempted (dc, serverChoice)
- Never reaches strategies 3-5 (hyphen, serverChoice_any, prefix_wildcard)

## Detailed Test Results

### Test 1: Overheid.nl Repository - Schema Testing

| recordSchema | Status | numberOfRecords | Diagnostic |
|--------------|--------|-----------------|------------|
| `dc` | 200 | 0 | "record schema not supported" |
| `oai_dc` | 200 | 0 | "record schema not supported" |
| `gzd` | 200 | **145,858** | ✅ SUCCESS |
| `dcx` | 200 | 0 | "record schema not supported" |
| `didl` | 200 | 0 | "record schema not supported" |

**Conclusion**: Only `gzd` schema works for repository.overheid.nl

### Test 2: Wetgeving.nl (BWB) - Schema Testing

| recordSchema | x-connection | Status | Result |
|--------------|--------------|--------|--------|
| `gzd` | BWB | 406 | "record cannot be transformed" |
| `oai_dc` | BWB | 406 | "record cannot be transformed" |
| `dc` | BWB | 406 | "record cannot be transformed" |
| `gzd` | (none) | 200 | "Mandatory parameter not supplied" |

**Conclusion**: BWB connection appears fundamentally incompatible with schema transformation

### Test 3: Query Syntax Testing (Overheid.nl with GZD)

| Query Type | Works? | Notes |
|------------|--------|-------|
| `(dc.title="..." OR dc.subject="...")` | ❌ No | Field names don't exist in GZD |
| `cql.serverChoice any "wetboek"` | ✅ Likely | Standard CQL syntax |
| Simple: `wetboek` | ✅ Likely | Simplest approach |

**Note**: Not yet tested with corrected schema configuration

## Code Flow Analysis

### Current Request Flow

1. **Entry**: `search()` method called with term="wetboek", endpoint="wetgeving_nl"
2. **Config**: Reads `SRUConfig` with `record_schema="oai_dc"`, `x-connection="BWB"`
3. **Query Build**: `_build_cql_query()` returns DC-field query
4. **Request Attempt**: `_try_query()` loops through schemas:
   - Primary: `oai_dc` (from config)
   - Fallback: `oai_dc`, `srw_dc`, `dc` (for SRU 2.0)
5. **Response**: Server returns 406 with diagnostic
6. **Parsing**: `_parse_sru_response()` finds 0 records
7. **Circuit Breaker**: After 2 empty results, returns `[]`
8. **Logging**: "Parsed 0 results" (no diagnostic info)

### Why Diagnostics Are Lost

**Attempt Recording** (lines 324-350):
```python
attempt_rec: dict = {
    "endpoint": config.name,
    "url": u,
    "query": query_str,
    "strategy": strategy,
    "status": response.status,
    "recordSchema": schema,
}
# ... diagnostic extraction happens here
attempt_rec.update(_extract_diag(txt))  # ✅ Stored in attempt
self._attempts.append(attempt_rec)       # ✅ Available via get_attempts()
```

**But**: These attempts are never logged or surfaced to users. The only logging is:
```python
logger.info(f"Parsed {len(results)} results from {config.name}")  # No diagnostic info
```

## Additional Findings

### 1. Rechtspraak.nl DNS Issues

**Log Evidence**:
```
2025-09-03 10:03:49,408 - services.web_lookup.sru_service - ERROR - SRU API error 404 voor Rechtspraak.nl
```

**Live Test Result**:
```
ClientConnectorDNSError: Cannot connect to host zoeken.rechtspraak.nl:443 ssl:default
[nodename nor servname provided, or not known]
```

**Issue**: DNS resolution failure for `zoeken.rechtspraak.nl`
**Cause**: Likely network-specific or temporary DNS issue (not schema-related)

### 2. SRU Explain Support

**Tested**:
- ✅ `repository.overheid.nl/sru`: Explain works, returns schema list
- ❌ `zoekservice.overheid.nl/sru/Search`: Explain requires x-connection parameter

**Implication**: Cannot dynamically discover BWB schemas via Explain

## Prioritized Root Causes

| Priority | Root Cause | Impact | Effort to Fix |
|----------|------------|--------|---------------|
| **P0** | Overheid.nl using unsupported `dc` schema | 100% failure | LOW - 1 line change |
| **P0** | Missing diagnostic logging | Hidden failures | LOW - Add logging |
| **P1** | BWB/Wetgeving.nl schema incompatibility | 100% failure | MEDIUM - Needs research |
| **P1** | DC-field CQL queries incompatible with GZD | Low result quality | MEDIUM - Query refactor |
| **P2** | Overheid Zoekservice missing x-connection | 100% failure | LOW - Add parameter |
| **P3** | Circuit breaker hiding full failure scope | Delayed diagnosis | N/A - Working as designed |

## Recommended Immediate Fixes

### Fix #1: Overheid.nl Schema Correction (IMMEDIATE)

**File**: `src/services/web_lookup/sru_service.py`
**Line**: 92

```python
# BEFORE
"overheid": SRUConfig(
    name="Overheid.nl",
    base_url="https://repository.overheid.nl/sru",
    default_collection="rijksoverheid",
    record_schema="dc",  # ❌
    ...
),

# AFTER
"overheid": SRUConfig(
    name="Overheid.nl",
    base_url="https://repository.overheid.nl/sru",
    default_collection="rijksoverheid",
    record_schema="gzd",  # ✅
    ...
),
```

**Expected Outcome**: Overheid.nl will start returning results immediately

### Fix #2: Add Diagnostic Logging (IMMEDIATE)

**File**: `src/services/web_lookup/sru_service.py`
**Location**: After line 769

```python
# CURRENT
logger.info(f"Parsed {len(results)} results from {config.name}")
return results

# ADD
if len(results) == 0:
    # Log diagnostic information from attempts
    for attempt in self._attempts:
        if 'diag_message' in attempt:
            logger.warning(
                f"SRU diagnostic for {config.name}: {attempt['diag_message']} "
                f"(URI: {attempt.get('diag_uri', 'N/A')}, Status: {attempt.get('status')})"
            )
        elif attempt.get('status') not in [200, None]:
            logger.warning(
                f"SRU HTTP error for {config.name}: Status {attempt['status']}"
            )
```

**Expected Outcome**: Failed queries will surface diagnostic messages in logs

### Fix #3: Wetgeving.nl Investigation (RESEARCH REQUIRED)

**Problem**: BWB connection incompatible with all tested schemas

**Investigation Steps**:
1. Research BWB (Basiswettenbestand) documentation
2. Test alternative endpoints (e.g., `wetten.overheid.nl` directly)
3. Test without x-connection parameter
4. Consider if BWB should be separate endpoint config

**Possible Solutions**:
- Option A: Use different base URL (not zoekservice)
- Option B: Remove x-connection and use different collection parameter
- Option C: Disable wetgeving_nl endpoint until proper config is found

## Testing Recommendations

### Validation Test Suite

Create test: `tests/services/web_lookup/test_sru_schema_validation.py`

```python
@pytest.mark.asyncio
async def test_overheid_nl_returns_results():
    """Verify Overheid.nl returns results after schema fix."""
    service = SRUService()
    async with service:
        results = await service.search('wetboek', 'overheid', max_records=3)
        assert len(results) > 0, "Overheid.nl should return results with gzd schema"

@pytest.mark.asyncio
async def test_diagnostics_logged_on_failure():
    """Verify diagnostic messages are logged when queries fail."""
    service = SRUService()
    # Force wrong schema for test
    service.endpoints['overheid'].record_schema = 'dc'

    with LogCapture() as logs:
        async with service:
            await service.search('test', 'overheid')

        # Verify diagnostic was logged
        assert any('diagnostic' in log.lower() for log in logs)
```

## Long-term Recommendations

1. **Dynamic Schema Discovery**: Use SRU Explain to auto-detect supported schemas
2. **Query Strategy Per Schema**: Build CQL queries appropriate for each schema type
3. **Comprehensive Error Handling**: Surface all SRU diagnostics to users/logs
4. **Integration Monitoring**: Add metrics for SRU success/failure rates
5. **Configuration Validation**: Validate endpoint configs on startup using Explain

## Conclusion

The SRU lookup failures are caused by **incorrect recordSchema configuration** (P0 root cause). The current code uses `dc` and `oai_dc` schemas that are not supported by the target endpoints.

**Immediate Impact**: Changing Overheid.nl to `gzd` schema will restore functionality for that provider.

**Remaining Work**: Wetgeving.nl (BWB) requires deeper investigation as it appears fundamentally incompatible with the current approach.

**Visibility Issue**: Lack of diagnostic logging prevented this issue from being discovered earlier. Adding diagnostic logging will prevent similar issues in the future.

---

## File Paths Referenced

- **SRU Service Implementation**: `/Users/chrislehnen/Projecten/Definitie-app/src/services/web_lookup/sru_service.py`
- **Modern Web Lookup Service**: `/Users/chrislehnen/Projecten/Definitie-app/src/services/modern_web_lookup_service.py`
- **Integration Tests**: `/Users/chrislehnen/Projecten/Definitie-app/tests/services/web_lookup/test_sru_integration.py`
- **Circuit Breaker Tests**: `/Users/chrislehnen/Projecten/Definitie-app/tests/services/web_lookup/test_sru_circuit_breaker.py`

## Log Files Analyzed

- `/Users/chrislehnen/Projecten/Definitie-app/logs/log om caching te testen.txt` (lines 98-145)
- `/Users/chrislehnen/Projecten/Definitie-app/logs/log.txt` (line 2319)
