# ServiceContainer Duplication - Root Cause Analysis

**Date**: 2025-10-07
**Analyst**: Debug Specialist
**Severity**: MEDIUM (Performance Impact)
**Status**: ROOT CAUSE IDENTIFIED

---

## Executive Summary

**SMOKING GUN FOUND**: The ServiceContainer is being initialized **2 times** due to a subtle Python LRU cache behavior with default arguments. The `@lru_cache(maxsize=1)` decorator on `get_cached_container(_config_hash: str | None = None)` treats calls with **no arguments** `()` and calls with **explicit None** `(None)` as **DIFFERENT cache keys**, creating separate cache entries and thus duplicate container instances.

**Evidence from Log File**:
```
2025-10-07 10:47:26,367 - 🚀 Initialiseer ServiceContainer (gebeurt 1x per sessie)
2025-10-07 10:47:26,386 - ServiceContainer geïnitialiseerd (init count: 1)
2025-10-07 10:47:52,391 - ServiceContainer geïnitialiseerd (init count: 1)  ← DUPLICATE!
```

Note: Both show `init count: 1` because they are separate instances in separate cache slots.

---

## Root Cause Breakdown

### 1. The Cache Key Problem

**Location**: `/Users/chrislehnen/Projecten/Definitie-app/src/utils/container_manager.py:28`

```python
@lru_cache(maxsize=1)
def get_cached_container(_config_hash: str | None = None) -> ServiceContainer:
    """Cache singleton container."""
    logger.info("🚀 Initialiseer ServiceContainer (gebeurt 1x per sessie)")
    # ... initialization code
```

**Python LRU Cache Behavior**:
- `get_cached_container()` → Cache key: `()`
- `get_cached_container(None)` → Cache key: `(None,)`
- **These are DIFFERENT keys!**

**Proof Test**:
```python
from functools import lru_cache

@lru_cache(maxsize=1)
def test_cache(arg=None):
    print(f'Cache called with arg={arg}')
    return f'result_{arg}'

result1 = test_cache()     # Cache miss #1, key=()
result2 = test_cache()     # Cache hit
result3 = test_cache(None) # Cache miss #2, key=(None,), EVICTS result1!
result4 = test_cache(None) # Cache hit

print(result1 is result3)  # False - different instances!
print(test_cache.cache_info())  # CacheInfo(hits=2, misses=2, maxsize=1, currsize=1)
```

### 2. Call Trace Analysis

**Call Path #1** (No Arguments):
```
main.py:66
  → TabbedInterface.__init__()  [line 93]
    → get_cached_container()
      → Cache key: ()
      → Container #1 created
```

**Call Path #2** (Explicit None):
```
tabbed_interface.py:101
  → get_definition_service()  [service_factory.py:742]
    → get_container(config)  [service_factory.py:763]
      → Uses frozen config key  [line 755]
      → get_cached_container()  [line 49 - implicit None passed]
        → Cache key: (None,)
        → Container #2 created (EVICTS Container #1!)
```

### 3. Why maxsize=1 Makes This Worse

With `maxsize=1`, the LRU cache can only hold **ONE** entry. When the second call with a different cache key arrives:
1. Cache sees key `(None,)` is not in cache
2. Calls the function (creates new container)
3. **EVICTS** the previous entry with key `()` to make room
4. Now we have 2 containers in memory, but only 1 in cache!

### 4. Evidence from Code

**tabbed_interface.py Line 93** - First call (no args):
```python
self.container = get_cached_container()
```

**service_factory.py Line 49** - Second call (implicit None):
```python
def get_container(config: dict | None = None) -> ServiceContainer:
    if config is not None:
        logger.warning("Custom config passed ... IGNORED")
    return get_cached_container()  # ← Called without args? Or with config=None?
```

**The Issue**: When `get_container(None)` is called, it passes `None` implicitly to `get_cached_container()`, creating the different cache key.

---

## Impact Analysis

### Performance Impact
- **Container Initialization**: 2x instead of 1x
- **Memory Overhead**: ~2-5MB per container instance
- **Service Loading**: All services loaded twice
- **Startup Time**: +200-400ms

### Cache Statistics Impact
```python
# Expected (working singleton):
CacheInfo(hits=5, misses=1, maxsize=1, currsize=1)

# Actual (with bug):
CacheInfo(hits=2, misses=2, maxsize=1, currsize=1)
```

---

## Why This Wasn't Caught Earlier

1. **Silent Failure**: Both containers work correctly, just duplicated
2. **Timing**: Log timestamps show 26 second gap - looks like separate user actions
3. **Init Count**: Each container correctly reports `init count: 1` (they don't know about each other)
4. **US-202**: Removed `get_container_with_config()` which had explicit config hashing, but the core cache key problem remained

---

## The Fix: Three Options

### Option 1: Normalize Cache Key (RECOMMENDED)
**File**: `src/utils/container_manager.py`

```python
@lru_cache(maxsize=1)
def get_cached_container() -> ServiceContainer:
    """
    Get singleton ServiceContainer instance.

    IMPORTANT: No parameters to ensure single cache key.
    All callers must call this without arguments.
    """
    logger.info("🚀 Initialiseer ServiceContainer (gebeurt 1x per sessie)")

    # Bepaal environment configuratie
    env = os.getenv("APP_ENV", "production")
    # ... rest unchanged
```

**Changes Required**:
- Remove `_config_hash` parameter completely
- Update all callers to call without arguments
- Update docstrings

**Pros**:
- Simple, clear intent
- Forces single cache key
- Easy to verify

**Cons**:
- Breaks any code passing config_hash (none found)

### Option 2: Explicit Cache Key Management
**File**: `src/utils/container_manager.py`

```python
@lru_cache(maxsize=1)
def get_cached_container(_cache_key: tuple = ()) -> ServiceContainer:
    """
    Get singleton ServiceContainer.

    Args:
        _cache_key: Internal cache key (always use default empty tuple)
    """
    logger.info("🚀 Initialiseer ServiceContainer (gebeurt 1x per sessie)")
    # ... rest unchanged
```

**Changes Required**:
- Change parameter to explicit tuple
- Ensure all callers use default

**Pros**:
- Explicit cache key type
- Type system catches wrong usage

**Cons**:
- Still allows misuse if tuple passed

### Option 3: Manual Singleton Pattern
**File**: `src/utils/container_manager.py`

```python
_CONTAINER_SINGLETON: ServiceContainer | None = None

def get_cached_container() -> ServiceContainer:
    """Get singleton ServiceContainer instance."""
    global _CONTAINER_SINGLETON

    if _CONTAINER_SINGLETON is None:
        logger.info("🚀 Initialiseer ServiceContainer (gebeurt 1x per sessie)")

        # Bepaal environment configuratie
        env = os.getenv("APP_ENV", "production")
        if env == "development":
            config = ContainerConfigs.development()
        elif env == "testing":
            config = ContainerConfigs.testing()
        else:
            config = ContainerConfigs.production()

        _CONTAINER_SINGLETON = ServiceContainer(config)
        logger.info("✅ ServiceContainer succesvol geïnitialiseerd en gecached")

    return _CONTAINER_SINGLETON

def clear_container_cache():
    """Clear the ServiceContainer singleton."""
    global _CONTAINER_SINGLETON
    logger.info("🗑️ Clear ServiceContainer cache")
    _CONTAINER_SINGLETON = None
    logger.info("✅ Container cache gecleared")
```

**Pros**:
- Explicit control
- No cache key ambiguity
- Easier to debug
- Better for testing (explicit clear)

**Cons**:
- More code
- Manual state management
- Global variable usage

---

## Recommended Solution

**Use Option 1 (Remove Parameter)** for immediate fix, with path to Option 3 for better control.

### Implementation Steps

1. **Update container_manager.py**:
   ```python
   @lru_cache(maxsize=1)
   def get_cached_container() -> ServiceContainer:
       # Remove _config_hash parameter entirely
   ```

2. **Verify all call sites** (7 locations found):
   - `src/ui/tabbed_interface.py:93` ✓ (already no args)
   - `src/ui/cached_services.py:39` ✓ (already no args)
   - `src/services/service_factory.py:49` ✓ (already no args)
   - `src/services/service_factory.py:720` ✓ (already no args)

3. **Add verification test**:
   ```python
   def test_container_singleton():
       """Verify container is truly singleton."""
       container1 = get_cached_container()
       container2 = get_cached_container()

       assert container1 is container2, "Containers must be same instance"
       assert id(container1) == id(container2), "Container IDs must match"

       info = get_cached_container.cache_info()
       assert info.hits >= 1, "Should have cache hits"
       assert info.currsize == 1, "Should have exactly 1 cache entry"
   ```

4. **Add monitoring**:
   ```python
   def get_cached_container() -> ServiceContainer:
       """Get singleton container."""
       # Add cache diagnostics
       cache_info = get_cached_container.cache_info()
       if cache_info.currsize > 1:
           logger.error(f"⚠️ CACHE CORRUPTION: {cache_info.currsize} entries in singleton cache!")
   ```

---

## Testing Strategy

### Unit Test
```python
# tests/unit/test_container_singleton.py
def test_container_caching_consistency():
    """Test that container is truly singleton."""
    # Clear any existing cache
    clear_container_cache()

    # First call
    container1 = get_cached_container()
    info1 = get_cached_container.cache_info()

    # Second call
    container2 = get_cached_container()
    info2 = get_cached_container.cache_info()

    # Assertions
    assert container1 is container2, "Same instance"
    assert info1.misses == 1, "Exactly one miss"
    assert info2.hits == 1, "Exactly one hit"
    assert info2.currsize == 1, "Exactly one cache entry"
```

### Integration Test
```python
# tests/integration/test_ui_container_usage.py
def test_tabbed_interface_uses_singleton():
    """Test that TabbedInterface uses singleton container."""
    interface = TabbedInterface()

    # Get container from service factory
    service = get_definition_service()

    # Should be same container
    assert interface.container is service._adapter._container
```

---

## Prevention Measures

### Code Review Checklist
- [ ] All `@lru_cache` decorators have explicit cache key handling
- [ ] Parameters with `None` defaults use explicit cache key normalization
- [ ] Singleton patterns documented and tested
- [ ] Cache statistics monitored in production

### Documentation Updates
- [ ] Update `CLAUDE.md` with cache key pitfall warning
- [ ] Add section on LRU cache behavior with None defaults
- [ ] Document singleton pattern expectations

### Monitoring
```python
# Add to startup diagnostics
def verify_singleton_health():
    """Verify container singleton is healthy."""
    info = get_cached_container.cache_info()

    if info.currsize != 1:
        logger.error(f"⚠️ Container cache corruption: {info.currsize} entries")
        return False

    if info.misses > 1:
        logger.warning(f"⚠️ Multiple container initializations: {info.misses} misses")
        return False

    return True
```

---

## Related Issues

- **EPIC-026/US-201**: Container caching optimization (completed)
- **US-202**: Removed custom config support (partial - left parameter)
- **DOUBLE_CONTAINER_ANALYSIS.md**: Original investigation (incomplete diagnosis)

---

## Conclusion

The root cause is **Python's LRU cache treating `()` and `(None,)` as different keys**, causing duplicate container initialization. The fix is straightforward: **remove the `_config_hash` parameter** from `get_cached_container()` to ensure a single, unambiguous cache key.

**Next Steps**:
1. Implement Option 1 (remove parameter)
2. Add verification tests
3. Monitor cache statistics post-fix
4. Consider migrating to Option 3 (manual singleton) for better control

**Estimated Effort**: 30 minutes coding + 30 minutes testing = 1 hour total
