# @cached Decorator Race Condition - Visual Timeline

## The Race Condition Visualized

### Production Scenario: 4 Threads Call get_all_rules() Simultaneously

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ @cached Decorator Execution Timeline                                        │
│ File: src/utils/cache.py lines 260-271                                     │
└─────────────────────────────────────────────────────────────────────────────┘

Time    Thread-1              Thread-2              Thread-3              Thread-4
════    ═════════════════     ═════════════════     ═════════════════     ═════════════════

0ms     wrapper() called      wrapper() called      wrapper() called      wrapper() called
        ↓                     ↓                     ↓                     ↓
        cache_key =           cache_key =           cache_key =           cache_key =
        "load_all_rules"      "load_all_rules"      "load_all_rules"      "load_all_rules"


1ms     🔒 Lock acquired      🔒 Lock acquired      🔒 Lock acquired      🔒 Lock acquired
        backend_get(key)      backend_get(key)      backend_get(key)      backend_get(key)
        ↓                     ↓                     ↓                     ↓
        Returns: None         Returns: None         Returns: None         Returns: None
        🔓 Lock released      🔓 Lock released      🔓 Lock released      🔓 Lock released


2ms     ⚠️  UNPROTECTED GAP   ⚠️  UNPROTECTED GAP   ⚠️  UNPROTECTED GAP   ⚠️  UNPROTECTED GAP
        ↓                     ↓                     ↓                     ↓
        if None: ✗            if None: ✗            if None: ✗            if None: ✗
        Skip return           Skip return           Skip return           Skip return


3ms     🔴 Execute func()     🔴 Execute func()     🔴 Execute func()     🔴 Execute func()
        ↓                     ↓                     ↓                     ↓
        Load 53 JSON files    Load 53 JSON files    Load 53 JSON files    Load 53 JSON files
        ↓                     ↓                     ↓                     ↓
        Read disk...          Read disk...          Read disk...          Read disk...
        Parse JSON...         Parse JSON...         Parse JSON...         Parse JSON...
        Build dict...         Build dict...         Build dict...         Build dict...


13ms    ✅ Done               ✅ Done               ✅ Done               ✅ Done
        result = {...}        result = {...}        result = {...}        result = {...}


14ms    🔒 Lock acquired      🔒 Lock acquired      🔒 Lock acquired      🔒 Lock acquired
        backend_set(key, {})  backend_set(key, {})  backend_set(key, {})  backend_set(key, {})
        🔓 Lock released      🔓 Lock released      🔓 Lock released      🔓 Lock released
        (Last write wins!)    (Discarded!)          (Discarded!)          (Discarded!)


15ms    return result         return result         return result         return result
```

## The Problem: Check-Then-Act Race Condition

### The Unprotected Gap (Lines 260-271)

```python
# Line 260: CHECK (protected by lock)
cached_result = backend_get(cache_key)  # 🔒 Lock acquired → None → 🔓 Lock released

# Lines 261-266: Conditional logic (NO LOCK)
if cached_result is not None:           # ⚠️  UNPROTECTED - All threads see None
    return cached_result

# Lines 267-270: Cache miss logic (NO LOCK)
logger.debug(f"Cache miss for {fn}")    # ⚠️  UNPROTECTED - All threads log this
_stats["misses"] += 1

# Line 271: ACT (NO LOCK)
result = func(*args, **kwargs)          # ⚠️  UNPROTECTED - All threads execute!
```

### Why the Gap is Dangerous

```
Thread-1 checks cache → None                    ┐
Thread-2 checks cache → None                    │
Thread-3 checks cache → None                    ├─ ALL happen before ANY set()
Thread-4 checks cache → None                    ┘

        ↓ All threads in unprotected gap ↓

Thread-1 executes func()  ─┐
Thread-2 executes func()  ─┤
Thread-3 executes func()  ─├─ PARALLEL EXECUTION (4x waste)
Thread-4 executes func()  ─┘

        ↓ All threads try to set cache ↓

Thread-1 sets cache       ─┐
Thread-2 sets cache       ─┤
Thread-3 sets cache       ─├─ LAST WRITE WINS (3 results discarded)
Thread-4 sets cache       ─┘
```

## Production Evidence Matches Timeline

### Production Logs

```
12:26:06,561 - Loading 53 regel files  ← Thread 1 at 3ms
12:26:06,561 - Loading 53 regel files  ← Thread 2 at 3ms (0ms difference!)
12:26:06,562 - Loading 53 regel files  ← Thread 3 at 3ms (1ms difference)
12:26:06,562 - Loading 53 regel files  ← Thread 4 at 3ms (1ms difference)

12:26:06,574 - ✅ 53 regels geladen    ← Thread 1 done (13ms later)
12:26:06,574 - ✅ 53 regels geladen    ← Thread 2 done (13ms later)
12:26:06,574 - ✅ 53 regels geladen    ← Thread 3 done (12ms later)
12:26:06,575 - ✅ 53 regels geladen    ← Thread 4 done (13ms later)
```

**Analysis:**
- All start within 1ms → All threads in unprotected gap simultaneously ✓
- All take ~13ms → All threads doing actual I/O work ✓
- No instant cache hits → No thread benefited from cache ✓

## What Thread-Safe Would Look Like

### With Proper Locking

```
Time    Thread-1              Thread-2              Thread-3              Thread-4
════    ═════════════════     ═════════════════     ═════════════════     ═════════════════

0ms     🔒 Acquire per-key    ⏳ Wait for lock...   ⏳ Wait for lock...   ⏳ Wait for lock...
        lock on "load_all"
        ↓
        Check cache → None
        ↓
1ms     Execute func()        ⏳ Still waiting...   ⏳ Still waiting...   ⏳ Still waiting...
        Load 53 files...
        ↓


13ms    Set cache             ⏳ Still waiting...   ⏳ Still waiting...   ⏳ Still waiting...
        🔓 Release lock
        ↓
        return result


14ms                          🔒 Acquire lock       ⏳ Wait for lock...   ⏳ Wait for lock...
                              Check cache → HIT!
                              🔓 Release lock
                              ↓
                              return cached


15ms                                                🔒 Acquire lock       ⏳ Wait for lock...
                                                    Check cache → HIT!
                                                    🔓 Release lock
                                                    ↓
                                                    return cached


16ms                                                                      🔒 Acquire lock
                                                                          Check cache → HIT!
                                                                          🔓 Release lock
                                                                          ↓
                                                                          return cached
```

**Expected production logs for thread-safe:**
```
12:26:06,561 - Loading 53 regel files  ← Thread 1 only
12:26:06,574 - ✅ 53 regels geladen    ← Thread 1 done (13ms)

(Threads 2-4 get instant cache hits - no logs!)
```

## The Fix Required

### Current Code (BROKEN)

```python
@wraps(func)
def wrapper(*args, **kwargs):
    cache_key = _generate_key_from_args(...)

    cached_result = backend_get(cache_key)  # ← CHECK
    if cached_result is not None:
        return cached_result

    # ⚠️  UNPROTECTED GAP - Multiple threads can be here!

    result = func(*args, **kwargs)          # ← ACT (4x execution!)

    backend_set(cache_key, result, ttl)
    return result
```

### Thread-Safe Pattern (SOLUTION)

```python
@wraps(func)
def wrapper(*args, **kwargs):
    cache_key = _generate_key_from_args(...)

    # Fast path: check cache without lock
    cached_result = backend_get(cache_key)
    if cached_result is not None:
        return cached_result

    # Get per-key computation lock
    with _get_computation_lock(cache_key):  # ← PROTECT THE GAP!
        # Double-check pattern
        cached_result = backend_get(cache_key)
        if cached_result is not None:
            return cached_result  # Another thread computed it

        # ONLY FIRST THREAD GETS HERE
        result = func(*args, **kwargs)  # ← 1x execution!

        backend_set(cache_key, result, ttl)
        return result
```

**Key difference:** Per-key lock protects the check-then-act gap

## Performance Impact Visualization

### Current (Race Condition)

```
Total Work = 4 threads × 13ms = 52ms CPU time
Total I/O = 4 threads × 53 files = 212 file reads

┌─────────┬─────────┬─────────┬─────────┐
│ Thread1 │ Thread2 │ Thread3 │ Thread4 │
│ 13ms ██ │ 13ms ██ │ 13ms ██ │ 13ms ██ │ ← All threads work
│ 53 read │ 53 read │ 53 read │ 53 read │
└─────────┴─────────┴─────────┴─────────┘

Cache hit rate: 0% (0/4 threads)
Wasted work: 75% (3/4 executions discarded)
```

### Thread-Safe (Expected)

```
Total Work = 1 thread × 13ms = 13ms CPU time
Total I/O = 1 thread × 53 files = 53 file reads

┌─────────┬─────────┬─────────┬─────────┐
│ Thread1 │ Thread2 │ Thread3 │ Thread4 │
│ 13ms ██ │ 0ms     │ 0ms     │ 0ms     │ ← Only first thread works
│ 53 read │ cached  │ cached  │ cached  │
└─────────┴─────────┴─────────┴─────────┘

Cache hit rate: 75% (3/4 threads)
Wasted work: 0% (all results used)
```

### Improvement

| Metric | Current | Thread-Safe | Improvement |
|--------|---------|-------------|-------------|
| CPU time | 52ms | 13ms | **75% faster** |
| File reads | 212 | 53 | **75% less I/O** |
| Cache hits | 0/4 (0%) | 3/4 (75%) | **∞ better** |
| Memory waste | 3× results | 0× results | **100% efficient** |

## Conclusion

The timeline visualization clearly shows:

1. **Root cause:** 11-line unprotected gap between cache check and function execution
2. **Symptom:** All 4 threads enter the gap simultaneously and all execute func()
3. **Evidence:** Production logs match the parallel execution pattern exactly
4. **Impact:** 4x CPU, 4x I/O, 4x memory, 0% cache hit rate
5. **Solution:** Per-key lock to protect check-then-act sequence

**The race condition is real and confirmed.**
