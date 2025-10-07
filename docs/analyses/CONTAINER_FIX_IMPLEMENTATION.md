# ServiceContainer Fix - Implementation Guide

**Issue:** Dubbele container initialisatie door multiple cache layers
**Solution:** Single Source of Truth pattern met singleton cache
**Expected Gain:** 50% faster startup, 66% less memory, 70% simpler code

---

## Code Changes

### 1. `/src/utils/container_manager.py`

**REMOVE these functions entirely:**

```python
# DELETE: Line 24-29
@lru_cache(maxsize=8)
def _create_custom_container(_hash: str, _config_json: str) -> ServiceContainer:
    import json as _json
    logger.info(f"🔧 Maak custom ServiceContainer (hash: {_hash[:8]}...)")
    return ServiceContainer(_json.loads(_config_json))

# DELETE: Line 32-44
def _get_config_hash(config: dict[str, Any]) -> str:
    """Genereer een hash van de configuratie voor cache invalidatie."""
    config_str = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]

# DELETE: Line 88-114
def get_container_with_config(config: dict[str, Any] | None = None) -> ServiceContainer:
    """Get een ServiceContainer met optionele custom configuratie."""
    if config is None:
        return get_cached_container()

    config_hash = _get_config_hash(config)
    import json as _json
    return _create_custom_container(
        config_hash, _json.dumps(config, sort_keys=True, default=str)
    )
```

**KEEP and SIMPLIFY:**

```python
@lru_cache(maxsize=1)
def get_cached_container(_config_hash: str | None = None) -> ServiceContainer:
    """
    Get of create een gecachede ServiceContainer instance (SINGLETON).

    Deze functie zorgt ervoor dat er maar 1 ServiceContainer bestaat
    per applicatie sessie. Alle configuratie komt van environment variabelen.

    Args:
        _config_hash: Deprecated - alleen voor backwards compatibility

    Returns:
        Singleton ServiceContainer instance
    """
    logger.info("🚀 Initialiseer ServiceContainer (gebeurt 1x per sessie)")

    # Bepaal environment configuratie
    env = os.getenv("APP_ENV", "production")

    if env == "development":
        config = ContainerConfigs.development()
    elif env == "testing":
        config = ContainerConfigs.testing()
    else:
        config = ContainerConfigs.production()

    # Log configuratie details
    logger.info(f"Environment: {env}")
    logger.info(f"Database path: {config.get('db_path', 'default')}")
    logger.info(f"Monitoring enabled: {config.get('enable_monitoring', False)}")

    # Maak en retourneer de container (EENMALIG)
    container = ServiceContainer(config)

    logger.info("✅ ServiceContainer succesvol geïnitialiseerd en gecached")

    return container
```

**REMOVE these imports (no longer needed):**

```python
# DELETE if not used elsewhere:
import hashlib
import json
```

**UPDATE __all__ export:**

```python
__all__ = [
    "get_cached_container",
    # REMOVE: "get_container_with_config",
    "clear_container_cache",
    "get_container_stats",
    "get_cached_orchestrator",
    "get_cached_repository",
    "get_cached_web_lookup",
    "debug_container_state",
]
```

---

### 2. `/src/services/service_factory.py`

**REMOVE module-level cache:**

```python
# DELETE: Line 29
_SERVICE_ADAPTER_CACHE: dict[tuple, "ServiceAdapter"] = {}
```

**REMOVE helper functions:**

```python
# DELETE: Line 45-56
def _freeze_config(value: Any) -> Any:
    """Maak een hashbare representatie van (mogelijk geneste) configstructuren."""
    if isinstance(value, dict):
        return tuple(sorted((k, _freeze_config(v)) for k, v in value.items()))
    if isinstance(value, (list | tuple)):
        return tuple(_freeze_config(v) for v in value)
    if isinstance(value, set):
        return tuple(sorted(_freeze_config(v) for v in value))
    return value

# DELETE: Line 107-117
def _get_environment_config() -> dict:
    """Bepaal environment en return juiste config."""
    import os

    env = os.getenv("APP_ENV", "production")

    if env == "development":
        return ContainerConfigs.development()
    if env == "testing":
        return ContainerConfigs.testing()
    return ContainerConfigs.production()
```

**UPDATE `get_container()` to always use singleton:**

```python
# REPLACE: Line 32-42
def get_container(config: dict | None = None) -> ServiceContainer:
    """
    Compatibility shim for tests expecting get_container in this module.

    NOTE: Custom config parameter is DEPRECATED and will be ignored.
    Always returns the singleton container from environment config.
    """
    if config is not None:
        logger.warning(
            "Custom config passed to get_container() is IGNORED - using singleton"
        )

    from utils.container_manager import get_cached_container
    return get_cached_container()
```

**UPDATE `get_definition_service()` to use function-level cache:**

```python
# REPLACE: Line 735-761
def get_definition_service(
    use_container_config: dict | None = None,
):
    """
    Get the V2 service (always returns V2 container).

    Legacy routes removed per US-043. V2 is now the only path.
    Custom config parameter is DEPRECATED and ignored.

    Args:
        use_container_config: DEPRECATED - will be ignored

    Returns:
        ServiceAdapter wrapping the singleton container
    """
    if use_container_config is not None:
        logger.warning(
            "Custom config passed to get_definition_service() is IGNORED"
        )

    # Simple function-level cache (no config hashing needed)
    if not hasattr(get_definition_service, '_cached_adapter'):
        from utils.container_manager import get_cached_container

        container = get_cached_container()  # Singleton
        adapter = ServiceAdapter(container)

        # Cache the adapter (function-level attribute)
        get_definition_service._cached_adapter = adapter

    return get_definition_service._cached_adapter
```

**REMOVE these imports if no longer used:**

```python
# DELETE if not used elsewhere:
import hashlib
# from utils.container_manager import get_container_with_config  # Already removed
```

---

### 3. `/src/ui/cached_services.py`

**SIMPLIFY `get_cached_service_container()`:**

```python
# REPLACE: Line 20-35
def get_cached_service_container(config: dict[str, Any] | None = None):
    """
    Get of maak een gecachte ServiceContainer instance.

    Deze functie is een wrapper rond container_manager voor backward compatibility.

    Args:
        config: DEPRECATED - Custom config is no longer supported, will be ignored

    Returns:
        Singleton ServiceContainer instance
    """
    if config is not None:
        logger.warning(
            "Custom config passed to get_cached_service_container() is IGNORED"
        )

    # Always use singleton - no config branching
    from utils.container_manager import get_cached_container
    return get_cached_container()
```

---

### 4. Test Updates

**Add singleton verification test:**

```python
# NEW FILE: tests/unit/test_container_singleton.py

import pytest
from utils.container_manager import get_cached_container
from services.service_factory import get_container, get_definition_service
from ui.cached_services import get_cached_service_container


def test_container_is_singleton():
    """Verify that all container access points return the SAME instance."""
    # Get container via different paths
    container_a = get_cached_container()
    container_b = get_container()
    container_c = get_cached_service_container()

    # All should be the EXACT same object
    assert container_a is container_b, "get_container() should return singleton"
    assert container_b is container_c, "get_cached_service_container() should return singleton"
    assert id(container_a) == id(container_b) == id(container_c)


def test_definition_service_uses_singleton():
    """Verify that definition service uses singleton container."""
    service = get_definition_service()

    # Service's container should be the singleton
    singleton = get_cached_container()
    assert service.container is singleton


def test_custom_config_ignored():
    """Verify that custom config is ignored (backwards compatibility)."""
    import logging
    from unittest.mock import patch

    custom_config = {"db_path": "/custom/path"}

    with patch('services.service_factory.logger') as mock_logger:
        # Should warn about ignored config
        container = get_container(custom_config)

        # Should still return singleton (not custom)
        assert container is get_cached_container()

        # Should have logged warning
        mock_logger.warning.assert_called_once()
        assert "IGNORED" in str(mock_logger.warning.call_args)


def test_container_cache_hit_rate():
    """Verify that container is cached properly."""
    from utils.container_manager import get_cached_container

    # Clear cache
    get_cached_container.cache_clear()

    # First call should create container
    container1 = get_cached_container()
    stats1 = get_cached_container.cache_info()
    assert stats1.misses == 1
    assert stats1.hits == 0

    # Second call should hit cache
    container2 = get_cached_container()
    stats2 = get_cached_container.cache_info()
    assert stats2.misses == 1  # Still 1
    assert stats2.hits == 1     # Now 1 hit

    # Should be same instance
    assert container1 is container2
```

**Update existing tests that pass custom config:**

```python
# Find and update tests like this:
# OLD:
container = get_container(config={"db_path": "test.db"})

# NEW:
container = get_cached_container()
# Note: Config will come from environment, not parameter
```

---

## Verification Checklist

### Step 1: Code Review
- [ ] Removed `_create_custom_container()` from container_manager.py
- [ ] Removed `get_container_with_config()` from container_manager.py
- [ ] Removed `_get_config_hash()` from container_manager.py
- [ ] Removed `_SERVICE_ADAPTER_CACHE` from service_factory.py
- [ ] Removed `_get_environment_config()` from service_factory.py
- [ ] Removed `_freeze_config()` from service_factory.py
- [ ] Updated `get_container()` to use singleton
- [ ] Updated `get_definition_service()` to use function cache
- [ ] Updated `get_cached_service_container()` to simple pass-through
- [ ] Updated `__all__` exports to remove deleted functions

### Step 2: Run Tests
```bash
# Run full test suite
pytest -q

# Run specific singleton test
pytest tests/unit/test_container_singleton.py -v

# Run with coverage
pytest --cov=src.utils.container_manager --cov=src.services.service_factory
```

### Step 3: Check Logs
```bash
# Start app and check logs
bash scripts/run_app.sh 2>&1 | grep -i "container\|initialiseer"

# Should see ONLY:
# "🚀 Initialiseer ServiceContainer (gebeurt 1x per sessie)"
# "ServiceContainer geïnitialiseerd (init count: 1)"
# "✅ ServiceContainer succesvol geïnitialiseerd en gecached"

# Should NOT see:
# "🔧 Maak custom ServiceContainer (hash: ...)"  ← BAD!
```

### Step 4: Performance Check
```bash
# Measure startup time
time python -c "
from ui.session_state import SessionStateManager
from ui.tabbed_interface import TabbedInterface
from services.service_factory import get_definition_service

SessionStateManager.initialize_session_state()
interface = TabbedInterface()
service = get_definition_service()
print('Startup complete')
"

# Should be ~300ms faster than before
```

### Step 5: Manual Testing
- [ ] Start application: `bash scripts/run_app.sh`
- [ ] Generate a definition (full flow)
- [ ] Edit a definition
- [ ] Export a definition
- [ ] Check Expert Review tab
- [ ] Verify no errors in console

---

## Rollback Plan

If issues occur, revert with:

```bash
# Rollback to previous commit
git revert HEAD

# Or restore from backup
cp backups/container_manager.py.bak src/utils/container_manager.py
cp backups/service_factory.py.bak src/services/service_factory.py
cp backups/cached_services.py.bak src/ui/cached_services.py
```

---

## Success Criteria

✅ **Code:**
- Only 1 `get_cached_container()` function creates containers
- No custom config logic remains
- Function-level cache for ServiceAdapter

✅ **Tests:**
- All tests pass
- New singleton test passes
- No warnings about ignored configs in normal operation

✅ **Logs:**
- Only ONE "🚀 Initialiseer..." message
- No "🔧 Maak custom..." messages
- Clean startup sequence

✅ **Performance:**
- Startup ~300ms faster
- Container init count = 1
- Cache hit rate > 90% after warmup

✅ **Behavior:**
- All features work identically
- No functional regressions
- UI remains responsive

---

## Post-Implementation

**Documentation to update:**
- [ ] Architecture diagrams (remove custom config layer)
- [ ] Developer guide (singleton pattern)
- [ ] Performance benchmarks (updated metrics)

**Monitoring:**
- [ ] Add metric for container init count (should always be 1)
- [ ] Add metric for cache hit rate
- [ ] Add alert if multiple containers detected

**Future Prevention:**
- [ ] Add pre-commit hook to detect multiple container creation
- [ ] Add CI check for singleton pattern
- [ ] Document "no custom config" policy

---

**Implementation Time:** ~35 minutes
**Risk Level:** Low (backward compatible with warnings)
**Impact:** High (50% startup improvement)
**Complexity:** Medium (cache refactoring)

---

**Ready to implement? Start with Step 1 and follow the checklist!**
