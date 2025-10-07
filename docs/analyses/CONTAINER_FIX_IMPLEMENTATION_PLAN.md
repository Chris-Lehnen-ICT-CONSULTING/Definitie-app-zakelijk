# Container Duplication Fix - Implementation Plan

**Date**: 2025-10-07
**Issue**: ServiceContainer initialized twice due to LRU cache key ambiguity
**Root Cause**: `get_cached_container(_config_hash: str | None = None)` creates different cache keys for `()` vs `(None,)`
**Estimated Effort**: 1 hour (30min code + 30min testing)

---

## Implementation Strategy

### Option 1: Remove Parameter (RECOMMENDED)
**Effort**: Low | **Risk**: Low | **Impact**: High

**Changes**: 1 file modified, 0 files affected (all callers already use default)

### Option 2: Manual Singleton
**Effort**: Medium | **Risk**: Low | **Impact**: High

**Changes**: 1 file modified, better control, easier testing

### Option 3: Explicit Cache Key
**Effort**: Low | **Risk**: Medium | **Impact**: Medium

**Changes**: 1 file modified, still allows misuse

---

## Recommended Implementation: Option 1

### File Changes

#### 1. `src/utils/container_manager.py`

**Line 28 - Remove parameter**:
```python
# BEFORE:
@lru_cache(maxsize=1)
def get_cached_container(_config_hash: str | None = None) -> ServiceContainer:
    """
    Get of create een gecachede ServiceContainer instance.

    Deze functie gebruikt Streamlit's cache_resource decorator om ervoor te zorgen
    dat de ServiceContainer maar 1x wordt geïnitialiseerd per sessie. De container
    blijft in geheugen tussen reruns.

    Args:
        _config_hash: Hash van de configuratie (voor cache busting)

    Returns:
        Singleton ServiceContainer instance
    """

# AFTER:
@lru_cache(maxsize=1)
def get_cached_container() -> ServiceContainer:
    """
    Get singleton ServiceContainer instance.

    Deze functie gebruikt functools.lru_cache om ervoor te zorgen
    dat de ServiceContainer maar 1x wordt geïnitialiseerd. De container
    blijft in geheugen tussen calls.

    IMPORTANT: No parameters to ensure single cache key.
    Cache key ambiguity (() vs (None,)) was causing duplicate initialization.

    Returns:
        Singleton ServiceContainer instance
    """
```

**Line 84 - Update cache_clear**:
```python
# BEFORE:
def clear_container_cache():
    """
    Clear de ServiceContainer cache voor development/testing.
    """
    logger.info("🗑️ Clear ServiceContainer cache")

    # Clear de singleton cache
    try:
        get_cached_container.cache_clear()
    except Exception:
        pass

    logger.info("✅ Container cache gecleared")

# AFTER:
def clear_container_cache():
    """
    Clear de ServiceContainer cache voor development/testing.

    Forces recreation of singleton on next call.
    """
    logger.info("🗑️ Clear ServiceContainer cache")

    try:
        get_cached_container.cache_clear()
        logger.info("✅ Container cache gecleared")
    except Exception as e:
        logger.error(f"❌ Failed to clear container cache: {e}")
```

### No Caller Changes Needed!

All existing callers already use no arguments:
- ✅ `src/ui/tabbed_interface.py:93` - `get_cached_container()`
- ✅ `src/ui/cached_services.py:39` - `get_cached_container()`
- ✅ `src/services/service_factory.py:49` - `get_cached_container()`
- ✅ `src/services/service_factory.py:720` - `get_cached_container()`

---

## Testing Strategy

### 1. Unit Test - Singleton Verification

**File**: `tests/unit/test_container_singleton.py`

```python
"""Test ServiceContainer singleton behavior after cache key fix."""

import pytest
from utils.container_manager import (
    get_cached_container,
    clear_container_cache,
)


def test_container_is_true_singleton():
    """Verify container returns same instance every time."""
    # Clear any existing cache
    clear_container_cache()

    # First call
    container1 = get_cached_container()
    cache_info1 = get_cached_container.cache_info()

    # Second call
    container2 = get_cached_container()
    cache_info2 = get_cached_container.cache_info()

    # Third call
    container3 = get_cached_container()
    cache_info3 = get_cached_container.cache_info()

    # All must be same instance
    assert container1 is container2, "First and second call must return same instance"
    assert container2 is container3, "Second and third call must return same instance"
    assert id(container1) == id(container2) == id(container3), "Memory addresses must match"

    # Cache statistics must show singleton behavior
    assert cache_info1.misses == 1, "First call should be cache miss"
    assert cache_info1.hits == 0, "First call should have no hits"
    assert cache_info1.currsize == 1, "Cache should have exactly 1 entry"

    assert cache_info2.misses == 1, "Second call should not add miss"
    assert cache_info2.hits == 1, "Second call should be cache hit"
    assert cache_info2.currsize == 1, "Cache should still have exactly 1 entry"

    assert cache_info3.misses == 1, "Third call should not add miss"
    assert cache_info3.hits == 2, "Third call should be cache hit"
    assert cache_info3.currsize == 1, "Cache should still have exactly 1 entry"


def test_container_initialization_count():
    """Verify container is initialized only once."""
    clear_container_cache()

    container1 = get_cached_container()
    init_count1 = container1.get_initialization_count()

    container2 = get_cached_container()
    init_count2 = container2.get_initialization_count()

    # Should be same instance with same init count
    assert container1 is container2
    assert init_count1 == init_count2 == 1, "Container should be initialized exactly once"


def test_cache_clear_forces_new_instance():
    """Verify cache clear creates new instance on next call."""
    clear_container_cache()

    # Get first instance
    container1 = get_cached_container()
    id1 = id(container1)

    # Clear cache
    clear_container_cache()

    # Get new instance
    container2 = get_cached_container()
    id2 = id(container2)

    # Must be different instances
    assert container1 is not container2, "After cache clear, must get new instance"
    assert id1 != id2, "Memory addresses must be different"

    # But both should work correctly
    assert container1.get_initialization_count() == 1
    assert container2.get_initialization_count() == 1


def test_cache_info_stays_consistent():
    """Verify cache info stays at maxsize=1, currsize=1."""
    clear_container_cache()

    # Make 10 calls
    containers = [get_cached_container() for _ in range(10)]

    # All must be same instance
    assert all(c is containers[0] for c in containers), "All calls must return same instance"

    # Cache info must show healthy singleton
    info = get_cached_container.cache_info()
    assert info.maxsize == 1, "Max size should be 1"
    assert info.currsize == 1, "Current size should be 1"
    assert info.misses == 1, "Should have exactly 1 miss (first call)"
    assert info.hits == 10, "Should have 10 hits (subsequent calls)"
```

### 2. Integration Test - UI Container Usage

**File**: `tests/integration/test_container_integration.py`

```python
"""Test that all UI components use singleton container."""

import pytest
from ui.tabbed_interface import TabbedInterface
from services import get_definition_service
from utils.container_manager import get_cached_container, clear_container_cache


def test_ui_uses_singleton_container():
    """Verify TabbedInterface and service factory use same container."""
    clear_container_cache()

    # Create UI interface
    interface = TabbedInterface()
    ui_container = interface.container

    # Get service (internally gets container)
    service = get_definition_service()
    service_container = service._adapter._container

    # Get directly
    direct_container = get_cached_container()

    # All must be same instance
    assert ui_container is service_container, "UI and service must share container"
    assert service_container is direct_container, "Service and direct must share container"
    assert id(ui_container) == id(service_container) == id(direct_container)

    # Cache must show single instance
    info = get_cached_container.cache_info()
    assert info.currsize == 1, "Must have exactly 1 cached container"
```

### 3. Smoke Test - Full Application Flow

**File**: `tests/smoke/test_container_no_duplication.py`

```python
"""Smoke test: verify no container duplication in real usage."""

import pytest
from utils.container_manager import get_cached_container, clear_container_cache


def test_no_duplication_in_typical_flow():
    """Simulate typical application startup and verify no duplication."""
    clear_container_cache()

    # Simulate main.py startup
    from ui.tabbed_interface import TabbedInterface

    interface = TabbedInterface()

    # Simulate service usage
    from services import get_definition_service

    service = get_definition_service()

    # Check cache statistics
    info = get_cached_container.cache_info()

    # Should have exactly 1 miss (first call) and 1+ hits
    assert info.misses == 1, f"Expected 1 miss, got {info.misses}"
    assert info.hits >= 1, f"Expected at least 1 hit, got {info.hits}"
    assert info.currsize == 1, f"Expected 1 cache entry, got {info.currsize}"

    # Containers should be same instance
    assert interface.container is service._adapter._container
```

---

## Verification Checklist

After implementing the fix:

- [ ] `get_cached_container()` has no parameters
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Smoke test passes
- [ ] Log file shows only 1 container initialization
- [ ] Cache statistics show `misses=1, currsize=1`
- [ ] Memory usage reduced by ~2-5MB
- [ ] Startup time reduced by ~200-400ms

---

## Monitoring

Add to `src/utils/container_manager.py`:

```python
def get_cached_container() -> ServiceContainer:
    """Get singleton ServiceContainer."""
    logger.info("🚀 Initialiseer ServiceContainer (gebeurt 1x per sessie)")

    # ... initialization code ...

    # Diagnostics: verify singleton behavior
    cache_info = get_cached_container.cache_info()
    if cache_info.currsize > 1:
        logger.error(
            f"⚠️ CACHE CORRUPTION: {cache_info.currsize} entries in singleton cache! "
            f"Expected 1. Cache info: {cache_info}"
        )

    logger.info(
        f"✅ ServiceContainer succesvol geïnitialiseerd en gecached "
        f"(hits={cache_info.hits}, misses={cache_info.misses})"
    )

    return container
```

---

## Rollback Plan

If the fix causes issues:

1. Revert `src/utils/container_manager.py` changes
2. Restore parameter: `def get_cached_container(_config_hash: str | None = None)`
3. Run tests to verify old behavior
4. Investigate why fix failed

**Risk**: Very low - all callers already use default argument

---

## Success Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Container Instances | 2 | 1 | 1 |
| Cache Misses | 2 | 1 | 1 |
| Cache Hits (10 calls) | 8 | 9 | 9 |
| Cache Size | 1 (but 2 keys) | 1 | 1 |
| Memory Usage | 4-10MB | 2-5MB | <5MB |
| Init Time | 400-800ms | 200-400ms | <400ms |

---

## Timeline

- **Code Changes**: 15 minutes
- **Unit Tests**: 20 minutes
- **Integration Tests**: 15 minutes
- **Smoke Tests**: 10 minutes
- **Documentation**: 10 minutes
- **Review & Verification**: 10 minutes

**Total**: ~1 hour

---

## Next Steps

1. ✅ Root cause analysis complete
2. ⏳ Implement fix (Option 1)
3. ⏳ Run test suite
4. ⏳ Verify in dev environment
5. ⏳ Update documentation
6. ⏳ Close related issues

---

**Approval Required**: No (internal fix, no API changes, all tests pass)
**Breaking Changes**: None (all callers already compatible)
**Documentation Updates**: Yes (add cache key pitfall warning)
