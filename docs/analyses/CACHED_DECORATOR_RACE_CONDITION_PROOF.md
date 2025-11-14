# @cached Decorator Race Condition - DEFINITIVE PROOF

**Date:** 2025-11-14
**Status:** CLAIM CONFIRMED
**Severity:** HIGH - Causes 4x file I/O in production

## Executive Summary

**CLAIM CONFIRMED:** The `@cached` decorator in `src/utils/cache.py` is **NOT thread-safe** and causes the check-then-act race condition that results in 4x parallel execution of `_load_all_rules_cached()`.

## Smoking Gun Evidence

### 1. Production Logs Show 4x Parallel Execution

```log
12:26:06,561 - Loading 53 regel files  ← Thread 1 start
12:26:06,561 - Loading 53 regel files  ← Thread 2 start (0ms later!)
12:26:06,562 - Loading 53 regel files  ← Thread 3 start (1ms later)
12:26:06,562 - Loading 53 regel files  ← Thread 4 start (1ms later)

12:26:06,574 - ✅ 53 regels geladen    ← Thread 1 done (13ms)
12:26:06,574 - ✅ 53 regels geladen    ← Thread 2 done (13ms)
12:26:06,574 - ✅ 53 regels geladen    ← Thread 3 done (12ms)
12:26:06,575 - ✅ 53 regels geladen    ← Thread 4 done (13ms)
```

**Analysis:**
- All 4 threads start within 1ms → PARALLEL execution
- All 4 threads take ~13ms → All doing actual I/O
- If thread-safe, would see: Thread 1 = 13ms, Threads 2-4 = 0ms (instant cache hit)

### 2. Reproduction Test Confirms Race Condition

**File:** `/tests/debug/test_cached_decorator_race_condition.py`

```log
12:41:45.002 [TestThread-4] 🔴 EXECUTING expensive_operation (execution #1)
12:41:45.002 [TestThread-1] 🔴 EXECUTING expensive_operation (execution #2)
12:41:45.002 [TestThread-2] 🔴 EXECUTING expensive_operation (execution #3)
12:41:45.002 [TestThread-3] 🔴 EXECUTING expensive_operation (execution #4)

Total function executions: 4
Threads that executed function: ['TestThread-4', 'TestThread-1', 'TestThread-2', 'TestThread-3']
```

**Conclusion:** All 4 threads executed the expensive function in parallel, proving race condition.

### 3. Production Test Shows Actual File Loading 4x

**File:** `/tests/debug/test_rule_cache_race_condition.py`

```log
12:42:23.355 [ProdThread-4] Loading 53 regel files
12:42:23.355 [ProdThread-3] Loading 53 regel files
12:42:23.356 [ProdThread-2] Loading 53 regel files
12:42:23.357 [ProdThread-1] Loading 53 regel files

12:42:23.368 [ProdThread-1] ✅ 53 regels succesvol geladen
12:42:23.368 [ProdThread-3] ✅ 53 regels succesvol geladen
12:42:23.368 [ProdThread-4] ✅ 53 regels succesvol geladen
12:42:23.368 [ProdThread-2] ✅ 53 regels succesvol geladen
```

**Matches production logs exactly!**

## Root Cause Analysis

### The Race Condition in @cached Decorator

**File:** `src/utils/cache.py` lines 229-277

```python
@wraps(func)
def wrapper(*args, **kwargs):
    # Generate cache key
    cache_key = _generate_key_from_args(func_name, *args, **kwargs)

    # Try to get from cache
    backend_get = cache_manager.get if cache_manager else _cache.get
    backend_set = cache_manager.set if cache_manager else _cache.set
    cached_result = backend_get(cache_key)  # Line 260 ← CHECK
    if cached_result is not None:
        return cached_result

    # Cache miss - execute function
    result = func(*args, **kwargs)          # Line 271 ← ACT

    # Store in cache
    backend_set(cache_key, result, ttl)

    return result
```

### The Unprotected Gap

**Lines 260-271:** 11 lines of code with **NO LOCK** between:
1. **CHECK** (line 260): `cached_result = backend_get(cache_key)`
2. **ACT** (line 271): `result = func(*args, **kwargs)`

### Thread Execution Timeline

```
Time   Thread-1              Thread-2              Thread-3              Thread-4
----   -------------------   -------------------   -------------------   -------------------
0ms    get(key) → None      get(key) → None       get(key) → None       get(key) → None
1ms    Execute func()       Execute func()        Execute func()        Execute func()
       (load 53 files)      (load 53 files)       (load 53 files)       (load 53 files)
13ms   set(key, result)     set(key, result)      set(key, result)      set(key, result)
       Return result        Return result         Return result         Return result
```

**All 4 threads see cache miss because they check BEFORE any thread has set the cache!**

## Why CacheManager Locks Don't Help

### CacheManager IS Thread-Safe Internally

**File:** `src/utils/cache.py` lines 451-564

```python
class CacheManager:
    def __init__(self, ...):
        self._lock = threading.Lock()  # Line 467

    def get(self, key: str, default=None):
        if self._lock:
            with self._lock:              # Line 523 ← GET is locked
                return self._get_locked(key, default)

    def set(self, key: str, value: Any, ttl=None):
        if self._lock:
            with self._lock:              # Line 492 ← SET is locked
                self._set_locked(key, value, expires_at)
```

**CacheManager.get() and .set() ARE locked!**

### But the Gap Between Calls is Unprotected

```
Thread-1: CacheManager.get("key")     ← Lock acquired → returns None → Lock released
Thread-2: CacheManager.get("key")     ← Lock acquired → returns None → Lock released
Thread-3: CacheManager.get("key")     ← Lock acquired → returns None → Lock released
Thread-4: CacheManager.get("key")     ← Lock acquired → returns None → Lock released

↓ All threads now in unprotected gap ↓

Thread-1: func(*args, **kwargs)       ← Executing expensive operation
Thread-2: func(*args, **kwargs)       ← Executing expensive operation
Thread-3: func(*args, **kwargs)       ← Executing expensive operation
Thread-4: func(*args, **kwargs)       ← Executing expensive operation
```

**The lock protects individual get/set operations, but NOT the gap between them!**

## Performance Impact

### Current Behavior (Race Condition)

**Startup scenario:**
1. ServiceContainer initialized
2. ValidationOrchestratorV2 calls `RuleCache.get_all_rules()`
3. 4 worker threads handle parallel validation
4. All 4 threads call `_load_all_rules_cached()` simultaneously
5. **Result:** 4x file I/O (212 file reads: 53 files × 4 threads)

**Measurements:**
- Time per thread: ~13-15ms (all threads work)
- Total CPU: 4× JSON parsing
- Total I/O: 4× disk reads
- Memory: 4× data structures created (3 discarded)
- Cache behavior: Only last `set()` wins, 3 results thrown away

### Expected Behavior (Thread-Safe)

**If decorator was thread-safe:**
1. Thread 1: Loads files (13ms)
2. Threads 2-4: Wait for cache, instant hit (0ms)
3. **Result:** 1x file I/O (53 file reads)

**Expected measurements:**
- Thread 1: ~13ms (does work)
- Threads 2-4: ~0ms (cache hit)
- Total CPU: 1× JSON parsing
- Total I/O: 1× disk reads
- Memory: 1× data structure (reused)

### Performance Regression

| Metric | Thread-Safe | Current (Race) | Waste |
|--------|-------------|----------------|-------|
| File reads | 53 | 212 | **4x** |
| CPU (parsing) | 13ms | 52ms | **4x** |
| Memory allocated | 1× | 4× | **4x** |
| Effective cache hits | 75% (3/4) | 0% (0/4) | **100% miss rate** |

## Comparison with UNIFIED_INSTRUCTIONS.md Claim

**Original claim was CORRECT:**

> "@cached decorator is NOT thread-safe and causes 4x file loading"

**Evidence confirming claim:**
1. ✅ Production logs show 4x "Loading..." messages with 0-1ms spacing
2. ✅ Reproduction test confirms 4x function execution
3. ✅ Code analysis identifies unprotected 11-line gap
4. ✅ CacheManager locks don't protect check-then-act pattern
5. ✅ Performance impact: 4x I/O, 4x CPU, 4x memory

## Thread-Safe Solution Pattern

### What Would Fix It

```python
# Thread-safe version (EXAMPLE - NOT IMPLEMENTED)
def cached(ttl=None, cache_key_func=None, cache_manager=None):
    # Need per-key lock for thread safety
    _computation_locks = {}
    _locks_lock = threading.Lock()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = _generate_key_from_args(...)

            # Check cache
            cached_result = backend_get(cache_key)
            if cached_result is not None:
                return cached_result

            # Get or create per-key lock
            with _locks_lock:
                if cache_key not in _computation_locks:
                    _computation_locks[cache_key] = threading.Lock()
                compute_lock = _computation_locks[cache_key]

            # Protect check-then-act with per-key lock
            with compute_lock:
                # Double-check pattern
                cached_result = backend_get(cache_key)
                if cached_result is not None:
                    return cached_result

                # Actually compute (only first thread gets here)
                result = func(*args, **kwargs)
                backend_set(cache_key, result, ttl)
                return result

        return wrapper
    return decorator
```

**Key differences:**
1. **Per-key lock:** Each cache key gets its own lock
2. **Double-check locking:** Recheck cache after acquiring lock
3. **Only first thread computes:** Others wait and get cached result

### Why Current Implementation Fails

**Missing:** Per-key lock to protect check-then-act sequence
**Result:** Multiple threads can all be in the gap simultaneously

## Conclusion

**A) CLAIM CONFIRMED**

The `@cached` decorator in `src/utils/cache.py` **IS NOT thread-safe**.

**Evidence:**
1. **Smoking gun code:** 11-line unprotected gap between cache check (line 260) and function execution (line 271)
2. **Timing analysis:** Production logs show all 4 threads start within 1ms and all take ~13ms (parallel execution pattern)
3. **Reproduction test:** Confirms 4x function execution with synchronized thread start
4. **Production test:** Shows actual 4x "Loading 53 regel files" messages
5. **CacheManager analysis:** Internal locks don't protect decorator's check-then-act pattern

**Performance impact:** 4x file I/O, 4x CPU, 4x memory allocation, 0% effective cache hit rate

**Files are loaded 4x in production.**

## Recommendations

### Immediate Actions

1. **DO NOT add backwards compatibility code** (per CLAUDE.md refactor policy)
2. **Fix the @cached decorator** with per-key locking pattern
3. **Add thread-safety test** to prevent regression
4. **Document the fix** for future reference

### Long-Term

1. Consider using proven caching library (e.g., `cachetools.cached` with lock)
2. Add thread-safety documentation to all decorators
3. Add concurrency tests to CI/CD pipeline

## Test Files

**Proof tests created:**
- `/tests/debug/test_cached_decorator_race_condition.py` - Generic race condition proof
- `/tests/debug/test_rule_cache_race_condition.py` - Production scenario test

**Run tests:**
```bash
python tests/debug/test_cached_decorator_race_condition.py
python tests/debug/test_rule_cache_race_condition.py
```

Both tests confirm the race condition.

## References

- **Production logs:** Shows 4x "Loading..." at timestamps 561, 561, 562, 562ms
- **Source code:** `src/utils/cache.py` lines 229-277 (@cached decorator)
- **Source code:** `src/utils/cache.py` lines 451-564 (CacheManager)
- **Source code:** `src/toetsregels/rule_cache.py` lines 31-87 (_load_all_rules_cached)
- **CLAUDE.md:** Refactor policy (no backwards compatibility)
