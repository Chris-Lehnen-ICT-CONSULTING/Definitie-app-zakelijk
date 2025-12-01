# Linear Issue Templates - Silent Failures Remediation

**Ready to create:** Copy/paste these templates into Linear

---

## ISSUE 1: DEF-187-CRITICAL-1 (P0 Blocker)

### Title
```
Fix critical silent failures in exception handling (5 locations) - P0 Blocker
```

### Priority
```
P0 - Blocking (blocks other development until resolved)
```

### Estimate
```
5 (4-6 hours)
```

### Component/Team
```
Core Services / Validation
```

### Description
```markdown
## Overview
Critical silent failures allowing undetected system degradation. 5 locations
where exceptions are silently suppressed without visibility.

## Critical Issues

### 1. PII Logging Filter Initialization (SECURITY)
- **Location:** src/main.py:43-44
- **Risk:** PII sanitization may fail silently → sensitive data in logs
- **Current:** `except Exception: pass`
- **Fix:** Add logging: `logger.error(f"Failed to initialize PII filter: {e}")`

### 2. Threshold Config Override (CONFIGURATION)
- **Location:** src/services/validation/modular_validation_service.py:123
- **Risk:** overall_accept threshold conversion failure → defaults used silently
- **Current:** `with contextlib.suppress(Exception):`
- **Fix:** Catch `(ValueError, TypeError)` → `logger.error()`

### 3. Category Threshold Config Override (CONFIGURATION)
- **Location:** src/services/validation/modular_validation_service.py:131
- **Risk:** category_accept threshold conversion failure
- **Current:** `with contextlib.suppress(Exception):`
- **Fix:** Catch `(ValueError, TypeError)` → `logger.error()`

### 4. Validation Rules Degradation (VALIDATION)
- **Location:** src/services/validation/modular_validation_service.py:179-181
- **Risk:** Rules drop from 45 → 7 (85% loss) only WARNING logged
- **Current:** `logger.warning(f"Could not load rules from ToetsregelManager: {e}")`
- **Fix:** Upgrade to `logger.error()`, add metric counter
- **Impact:** Users may not notice 85% validation rule loss

### 5. Orchestrator Stats Enrichment (OBSERVABILITY)
- **Location:** src/services/orchestrators/definition_orchestrator_v2.py:261-262
- **Risk:** Telemetry gaps invisible → difficult to diagnose validation service issues
- **Current:** `with contextlib.suppress(Exception):`
- **Fix:** Add logging: `logger.warning("Failed to get validation stats: {e}")`

## Acceptance Criteria
- [ ] All 5 locations have appropriate error logging (ERROR or WARNING level)
- [ ] Error messages are descriptive and indicate severity
- [ ] No `contextlib.suppress(Exception)` remains unlogged
- [ ] Errors are observable in application logs
- [ ] Manual testing verifies error messages appear when components fail
- [ ] Tests added for each error path (5 new test cases)

## Definition of Done
- [ ] Code changes complete
- [ ] All tests passing
- [ ] Error logs reviewed and confirm appropriate levels
- [ ] PR reviewed by @architecture team
- [ ] Deployed and verified in staging
```

### Links
```
Related: DEF-187-HIGH, DEF-187-MEDIUM
References:
  - docs/analysis/2025-11-27_multi-agent-cleanup-analysis.md
  - docs/analysis/2025-11-27_silent-failures-gap-analysis.md
  - docs/analysis/SILENT_FAILURES_INVENTORY.md
```

---

## ISSUE 2: DEF-187-HIGH (P1)

### Title
```
Replace broad exception suppression with specific handling (11 locations) - P1
```

### Priority
```
P1 - High (important, should be done)
```

### Estimate
```
8 (8-10 hours)
```

### Component/Team
```
Core Services, UI Components
```

### Description
```markdown
## Overview
11 locations using `contextlib.suppress(Exception)` which blocks all exception
visibility. Need to migrate to specific exception handling with appropriate
logging.

## Locations to Fix

### UI Components
1. **src/ui/components/examples_block.py:350** - Voorbeelden repository query
   - Catch: `ValueError, KeyError`
   - Log: WARNING

2. **src/ui/components/examples_block.py:472** - Voorbeelden search
   - Catch: `ValueError, KeyError`
   - Log: WARNING

3. **src/ui/components/examples_block.py:518** - Voorbeelden formatting
   - Catch: `ValueError, KeyError`
   - Log: WARNING

4. **src/ui/components/expert_review_tab.py:879** - Expert comments query
   - Catch: `ValueError, KeyError`
   - Log: WARNING

### Services
5. **src/services/definition_edit_service.py:570** - Version save
   - Catch: `SQLAlchemy errors, IOError`
   - Log: ERROR (data operation)

6. **src/services/definition_edit_repository.py:81** - JSON parse edit data
   - Catch: `json.JSONDecodeError`
   - Log: WARNING (include what failed to parse)

7. **src/services/definition_edit_repository.py:486** - JSON parse related
   - Catch: `ValueError, TypeError`
   - Log: WARNING

### Utilities
8. **src/toetsregels/rule_cache.py:298** - Cache clear
   - Catch: `OSError, RuntimeError`
   - Log: WARNING (cache management critical)

9. **src/utils/cache.py:617** - Cache eviction
   - Catch: `MemoryError, OSError`
   - Log: WARNING

10. **src/utils/container_manager.py:96** - Container shutdown
    - Catch: `RuntimeError, Exception` (resources)
    - Log: ERROR (resource leak risk)

### Databases
11. **src/services/definition_edit_repository.py:81** (already listed as #6)

## Migration Pattern

### BEFORE
```python
with contextlib.suppress(Exception):
    result = risky_operation()
    process(result)
```

### AFTER
```python
try:
    result = risky_operation()
    process(result)
except SpecificException as e:
    logger.warning(f"Operation failed (recoverable): {e}")
except OtherException as e:
    logger.error(f"Operation failed (serious): {e}", exc_info=True)
except Exception as e:  # Only as last resort
    logger.error(f"Unexpected failure: {e}", exc_info=True)
```

## Acceptance Criteria
- [ ] All 11 locations use specific exception types (not broad Exception)
- [ ] Logging levels chosen appropriately (ERROR for critical ops, WARNING for recoverable)
- [ ] Error messages include context about what operation failed
- [ ] Unit tests added for error paths (verify logging occurs)
- [ ] No `contextlib.suppress(Exception)` remain unlogged
- [ ] Integration tests verify error handling doesn't break normal flows

## Definition of Done
- [ ] Code changes complete
- [ ] 11+ new test cases added (error paths)
- [ ] All tests passing
- [ ] Manual testing in UI verifies error feedback to users
- [ ] Error logs reviewed for message quality
- [ ] Performance: no degradation from logging addition
- [ ] PR reviewed
- [ ] Deployed and verified
```

### Links
```
Depends on: DEF-187-CRITICAL-1
Related: DEF-187-MEDIUM
References:
  - docs/analysis/SILENT_FAILURES_INVENTORY.md
  - docs/analysis/2025-11-27_silent-failures-gap-analysis.md
```

---

## ISSUE 3: DEF-187-MEDIUM (P2)

### Title
```
Add logging to async cleanup handlers (6 locations) - P2 Polish
```

### Priority
```
P2 - Medium (nice to have, low urgency)
```

### Estimate
```
5 (4-6 hours)
```

### Component/Team
```
Utils, Async Infrastructure
```

### Description
```markdown
## Overview
6 locations with specific exception suppression (mostly async cleanup) need
DEBUG-level logging added. These are mostly expected failures but should be
observable for troubleshooting async issues.

## Locations

### Async Task Cleanup
1. **src/utils/smart_rate_limiter.py:261** - Cancellation cleanup
   ```python
   with contextlib.suppress(asyncio.CancelledError):
       await pending_task
   ```
   - Add: `logger.debug(f"Rate limiter task cancelled")`

2. **src/utils/smart_rate_limiter.py:317** - ValueError in cleanup
   ```python
   with contextlib.suppress(ValueError):
       cleanup_operation()
   ```
   - Add: `logger.debug(f"Cleanup value error (expected): {e}")`

3. **src/utils/resilience.py:192** - Task cancellation
   ```python
   with contextlib.suppress(asyncio.CancelledError):
       await task
   ```
   - Add: `logger.debug("Resilience task cancelled")`

4. **src/utils/resilience.py:410** - Another cancellation cleanup
   ```python
   with contextlib.suppress(asyncio.CancelledError):
       cleanup()
   ```
   - Add: `logger.debug("Resilience cleanup cancelled")`

5. **src/utils/optimized_resilience.py:160** - Optimized cleanup
   ```python
   with contextlib.suppress(asyncio.CancelledError):
       finalize()
   ```
   - Add: `logger.debug("Optimized resilience cleanup cancelled")`

### Session State
6. **src/ui/session_state.py:350** - Key lookup (review only)
   ```python
   with contextlib.suppress(KeyError):
       value = st.session_state[key]
   ```
   - Status: ✅ ACCEPTABLE (expected case)
   - Recommendation: Add comment explaining why KeyError suppression is OK
   - Optional DEBUG logging if tracing session state issues

## Approach
- Add DEBUG-level logging to all 5 async cleanup paths
- Include task/operation name in log message
- Comment explaining why this failure is expected
- Consider adding metrics counter for cancellation events

## Example Implementation
```python
def _cleanup_async_task(task):
    """Clean up async task, expecting possible cancellation."""
    try:
        task.cancel()
        # Suppress CancelledError - expected when task is cancelled
        with contextlib.suppress(asyncio.CancelledError):
            # Run any async cleanup code
            pass
    except Exception as e:
        logger.error(f"Unexpected error in async cleanup: {e}", exc_info=True)
    finally:
        logger.debug("Async task cleanup completed")
```

## Acceptance Criteria
- [ ] All 5 async cleanup paths have DEBUG logging
- [ ] Log messages explain context (task name, operation type)
- [ ] Comments document why these exceptions are expected
- [ ] Session state location reviewed (decision documented)
- [ ] No log spam: DEBUG level so off by default
- [ ] Tests verify logging occurs in debug mode (optional)

## Definition of Done
- [ ] Code changes complete
- [ ] Code review approved
- [ ] Manual testing: enable DEBUG logging, verify messages appear
- [ ] No performance impact
- [ ] Deployed and verified in staging
```

### Links
```
Depends on: DEF-187-CRITICAL-1, DEF-187-HIGH (recommended order)
Related: DEF-187-CRITICAL-1, DEF-187-HIGH
References:
  - docs/analysis/SILENT_FAILURES_INVENTORY.md (Medium section)
```

---

## Quick Reference: What Changed

| Issue | Priority | Locations | Effort | Risk |
|-------|----------|-----------|--------|------|
| DEF-187-CRITICAL-1 | P0 | 5 | 4-6h | HIGH (core systems) |
| DEF-187-HIGH | P1 | 11 | 8-10h | MEDIUM (UI + services) |
| DEF-187-MEDIUM | P2 | 6 | 4-6h | LOW (async cleanup) |
| **TOTAL** | - | **22** | **16-22h** | **MEDIUM** |

---

## Creation Instructions

1. Copy each issue template above
2. Create in Linear with:
   - Title (exact)
   - Priority (as marked)
   - Estimate (as marked)
   - Description (paste markdown)
   - Links (link between issues)
3. Tag: `technical-debt`, `error-handling`, `logging`
4. Assign to: DevOps/Architecture team for initial review
5. Link to: Multi-agent analysis report (parent reference)

---

## Acceptance Timeline

- **P0 (CRITICAL-1):** Must complete before other development
- **P1 (HIGH):** Schedule after P0 done (in same sprint if possible)
- **P2 (MEDIUM):** Nice to have in same sprint, otherwise next sprint

---

