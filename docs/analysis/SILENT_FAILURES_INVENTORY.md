# Silent Failures Detailed Inventory

**Generated:** 2025-11-27 | **Updated:** 2025-12-01 (DEF-215 multiagent analysis)
**Total Patterns:** 38 original + 76 NEW = 114 | **Fixed:** 20 | **Remaining:** 94

---

## 📊 UPDATE 2025-12-01: DEF-215 Multiagent Analysis

### Belangrijkste Bevindingen

| Categorie | Origineel | Fixed | Nieuw Gevonden | Resterend |
|-----------|-----------|-------|----------------|-----------|
| CRITICAL | 5 | 5 | 6 | 6 |
| HIGH | 11 | 9 | 37+ | 39+ |
| MEDIUM | 15+ | 2 | 15+ | 28+ |
| **TOTAAL** | **31** | **16** | **76+** | **91+** |

### P0-Critical Fixes Geïmplementeerd (DEF-215, 2025-12-01)

1. ✅ **Validation degraded mode indicator** - `modular_validation_service.py:89-93, 190-212, 312-330, 630-637`
2. ✅ **Database save error handling** - `definitie_repository.py:1663-1675` (upgraded debug→warning)
3. ✅ **Stats enrichment fallback** - `definition_orchestrator_v2.py:258-284` (added fallback dict)
4. ✅ **UI degraded mode warning** - `definition_generator_tab.py:281-285, 1615-1652`

### Nieuw Ontdekte Risico's (niet in originele inventory)

| # | Locatie | Risico Score | Beschrijving |
|---|---------|--------------|--------------|
| 1 | `modular_validation_service.py:188-212` | 60/125 | Validation fallback 45→7 regels - NU MET INDICATOR |
| 2 | `service_factory.py` | 48/125 | 6 silent `except Exception: pass` patterns |
| 3 | `sru_service.py` | 45/125 | 17 silent exception patterns |
| 4 | `definition_generator_tab.py` | 40/125 | 15+ silent UI failures |

---

## CRITICAL (P0) - 5 Issues - ✅ ALL FIXED

### 1. PII Logging Filter Initialization Failure
```
File: src/main.py
Line: 47-59
Severity: 🔴 CRITICAL - Security
Status: ✅ FIXED (DEF-187)
```

**Previous Code:** `except Exception: pass`
**Fixed Code:** Now uses `logger.error()` with security context.

---

### 2. Config Threshold Override - First Threshold
```
File: src/services/validation/modular_validation_service.py
Line: 122-134
Severity: 🔴 CRITICAL - Configuration
Status: ✅ FIXED (DEF-187)
```

**Previous Code:** `contextlib.suppress(Exception)`
**Fixed Code:** Now uses `except (ValueError, TypeError) as e:` with `logger.error()`

---

### 3. Config Threshold Override - Second Threshold
```
File: src/services/validation/modular_validation_service.py
Line: 131-137
Severity: 🔴 CRITICAL - Configuration
Status: ❌ NOT COVERED
```

**Code:**
```python
with contextlib.suppress(Exception):
    self._category_threshold = float(
        safe_dict_get(thresholds, "category_accept", self._category_threshold)
    )
```

**Risk:** Category threshold config ignored → Validation inconsistent
**Fix:** Same as #2 above

---

### 4. Rules Fallback (45→7 Degradation)
```
File: src/services/validation/modular_validation_service.py
Line: 179-181
Severity: 🔴 CRITICAL - Validation Degradation
Status: ⚠️ PARTIALLY COVERED (logs WARNING, should be ERROR)
```

**Code:**
```python
except Exception as e:
    logger.warning(f"Could not load rules from ToetsregelManager: {e}")
    self._set_default_rules()  # Falls back from 45 to 7 rules
```

**Risk:** 85% validation rule loss with only WARNING visibility
**Fix:** Upgrade to `logger.error()`, add metric counter for rule loss

---

### 5. Stats Enrichment Silent Suppression
```
File: src/services/orchestrators/definition_orchestrator_v2.py
Line: 261-262
Severity: 🔴 CRITICAL - Observability
Status: ❌ NOT COVERED
```

**Code:**
```python
if hasattr(self.validation_service, "get_stats"):
    with contextlib.suppress(Exception):
        stats["validation"] = self.validation_service.get_stats()
```

**Risk:** Telemetry gaps invisible → Can't diagnose validation service issues
**Fix:** Log as WARNING when stats retrieval fails

---

## HIGH (P1) - 11 Issues - SHOULD FIX

### 6-8. Examples Block Broad Exceptions (3 locations)
```
File: src/ui/components/examples_block.py
Lines: 350, 472, 518
Severity: 🟠 HIGH - UI Reliability
Status: ❌ NOT COVERED
Count: 3 instances
```

**Pattern:**
```python
with contextlib.suppress(Exception):
    vorbeelden_data = repository.get_voorbeelden(...)
```

**Risk:** Example rendering failures hidden → Users see blank results without knowing why
**Fix:** Catch `ValueError, KeyError` specifically, log+display error message

---

### 9. Expert Review Tab Silent Failure
```
File: src/ui/components/expert_review_tab.py
Line: 879
Severity: 🟠 HIGH - UI Reliability
Status: ❌ NOT COVERED
```

**Code:**
```python
with contextlib.suppress(Exception):
    expert_comments = repository.get_expert_comments(...)
```

**Risk:** Expert feedback lost without user notification
**Fix:** Log as WARNING, show user message

---

### 10. Definition Edit Service Silent Suppression
```
File: src/services/definition_edit_service.py
Line: 570
Severity: 🟠 HIGH - Data Integrity
Status: ❌ NOT COVERED
```

**Code:**
```python
with contextlib.suppress(Exception):
    self.repository.save_definition_version(...)
```

**Risk:** Definition save may fail silently → Data loss potential
**Fix:** Catch `SQLError, IOError` specifically, propagate error to user

---

### 11. Rule Cache Clear Operation
```
File: src/toetsregels/rule_cache.py
Line: 298-300
Severity: 🟠 HIGH - Cache Management
Status: ❌ NOT COVERED
```

**Code:**
```python
else:
    with contextlib.suppress(Exception):
        _global_cache_clear()
    logger.info("Rule cache gecleared (global cache cleared)")
```

**Risk:** Cache clear may fail silently → Stale rules used → Inconsistent validation
**Fix:** Catch `OSError, RuntimeError` specifically, log as WARNING if fails

---

### 12. Generic Cache Eviction
```
File: src/utils/cache.py
Line: 617
Severity: 🟠 HIGH - Cache Reliability
Status: ❌ NOT COVERED
```

**Code:**
```python
with contextlib.suppress(Exception):
    _cache.clear()
```

**Risk:** Cache pollution from eviction failure → Memory bloat
**Fix:** Log as WARNING, return eviction status

---

### 13. Container Manager Shutdown
```
File: src/utils/container_manager.py
Line: 96
Severity: 🟠 HIGH - Resource Management
Status: ❌ NOT COVERED
```

**Code:**
```python
with contextlib.suppress(Exception):
    self.container.shutdown()
```

**Risk:** Resources leak if shutdown fails silently
**Fix:** Log as ERROR, attempt cleanup fallback

---

### 14-15. Definition Edit Repository JSON Handling (2 locations)
```
File: src/services/definition_edit_repository.py
Lines: 81, 486
Severity: 🟠 HIGH - Data Integrity
Status: ❌ NOT COVERED
Count: 2 instances
```

**Code:**
```python
# Line 81:
with contextlib.suppress(json.JSONDecodeError):
    edit_data = json.loads(...)

# Line 486:
with contextlib.suppress(ValueError, TypeError):
    related_data = json.loads(...)
```

**Risk:** JSON parsing failures may lose edit history or related data
**Fix:** Log as WARNING what failed to parse (include line/column info if possible)

---

## MEDIUM (P2) - 15+ Issues - NICE TO FIX

### 16-19. Async Cleanup Patterns (4 locations)
```
Files:
- src/utils/smart_rate_limiter.py:261,317
- src/utils/resilience.py:192,410
- src/utils/optimized_resilience.py:160

Severity: 🟡 MEDIUM - Expected Failures (mostly async cleanup)
Status: ❌ NOT COVERED
Count: ~5 instances
```

**Pattern:**
```python
with contextlib.suppress(asyncio.CancelledError):
    await pending_task
```

**Risk:** Async task cleanup failures go unobserved (expected, but still nice to track)
**Fix:** Add DEBUG-level logging, count cancellation metrics

---

### 20. Session State Key Error
```
File: src/ui/session_state.py
Line: 350
Severity: 🟢 LOW - Expected Case
Status: ✅ ACCEPTABLE (specific exception)
```

**Code:**
```python
with contextlib.suppress(KeyError):
    session_value = st.session_state[key]
```

**Note:** This is acceptable - KeyError is expected when key doesn't exist. Only add DEBUG logging if tracing session issues.

---

## Summary by File

| File | Critical | High | Medium | Total | Priority |
|------|----------|------|--------|-------|----------|
| src/main.py | 1 | - | - | 1 | P0 |
| src/services/validation/modular_validation_service.py | 3 | - | - | 3 | P0 |
| src/services/orchestrators/definition_orchestrator_v2.py | 1 | - | - | 1 | P0 |
| src/repositories/synonym_repository.py | 1 | - | - | 1 | P0 |
| src/ui/components/examples_block.py | - | 3 | - | 3 | P1 |
| src/ui/components/expert_review_tab.py | - | 1 | - | 1 | P1 |
| src/services/definition_edit_service.py | - | 1 | - | 1 | P1 |
| src/toetsregels/rule_cache.py | - | 1 | - | 1 | P1 |
| src/utils/cache.py | - | 1 | - | 1 | P1 |
| src/utils/container_manager.py | - | 1 | - | 1 | P1 |
| src/services/definition_edit_repository.py | - | 2 | - | 2 | P1 |
| src/utils/smart_rate_limiter.py | - | - | 2 | 2 | P2 |
| src/utils/resilience.py | - | - | 2 | 2 | P2 |
| src/utils/optimized_resilience.py | - | - | 1 | 1 | P2 |
| src/ui/session_state.py | - | - | 1 | 1 | P2 |
| **TOTAL** | **5** | **11** | **9** | **25** | - |

---

## Remediation Checklist

### Phase 1: Critical (4-6 hours)
- [ ] Fix main.py PII filter
- [ ] Fix modular_validation_service thresholds (×2)
- [ ] Upgrade modular_validation_service rules fallback to ERROR
- [ ] Add logging to orchestrator stats

### Phase 2: High Impact (8-10 hours)
- [ ] Fix examples_block (×3)
- [ ] Fix expert_review_tab
- [ ] Fix definition_edit_service
- [ ] Fix rule_cache clear
- [ ] Fix cache eviction
- [ ] Fix container shutdown
- [ ] Fix definition_edit_repository (×2)

### Phase 3: Polish (4-6 hours)
- [ ] Add DEBUG logging to async cleanup (×5)
- [ ] Verify session_state acceptable

---

## Testing Strategy

For each fix, add unit test that:
1. Mocks the operation to raise the exception
2. Verifies logging occurs at correct level
3. Verifies graceful degradation or fallback

Example:
```python
def test_pii_filter_failure_logged(caplog):
    """Verify PII filter failure is logged, not silently suppressed."""
    with patch("utils.logging_filters.PIIRedactingFilter") as mock_filter:
        mock_filter.side_effect = ImportError("test failure")
        # Run initialization
        assert "PII filter" in caplog.text
        assert "ERROR" in caplog.text  # or "WARNING"
```

---

## References

- Multi-Agent Analysis Report: `/docs/analysis/2025-11-27_multi-agent-cleanup-analysis.md`
- Gap Analysis: `/docs/analysis/2025-11-27_silent-failures-gap-analysis.md`
- CLAUDE.md Error Handling Guidelines: `/CLAUDE.md` (section on logging)

