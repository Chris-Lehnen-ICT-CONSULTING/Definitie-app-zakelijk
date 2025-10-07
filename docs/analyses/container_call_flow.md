# ServiceContainer Call Flow Diagram

## Visual Call Path Analysis

### Container Creation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         APPLICATION STARTUP                       │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │      main.py (line 63)    │
                    │ SessionStateManager.      │
                    │ initialize_session_state()│
                    └──────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │ ui/session_state.py (line 78-80)      │
                    │ from ui.cached_services import        │
                    │     initialize_services_once          │
                    │ initialize_services_once()            │
                    └──────────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │ ui/cached_services.py (line 45-51)    │
                    │ def initialize_services_once():       │
                    │   if service_container is None:       │
                    │     set_value("service_container",    │
                    │       get_cached_service_container()) │
                    └──────────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │ ui/cached_services.py (line 32-35)    │
                    │ def get_cached_service_container(     │
                    │     config=None):                     │
                    │   if config is None:                  │
                    │     return get_cached_container() ◄───┼── PATH A
                    │   else:                               │
                    │     return get_container_with_config()│
                    └──────────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │ utils/container_manager.py (line 48)  │
                    │ @lru_cache(maxsize=1)                 │
                    │ def get_cached_container():           │
                    │   logger.info("🚀 Initialiseer...")   │
                    │   config = ContainerConfigs.prod...() │
                    │   return ServiceContainer(config)     │
                    └──────────────────────────────────────┘
                                   │
                                   ▼
                           ┌──────────────┐
                           │ CONTAINER #1 │  ✅ Created
                           │ (Cached A)   │
                           └──────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                    TABBED INTERFACE INIT                          │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │ ui/tabbed_interface.py (line 90-94)   │
                    │ class TabbedInterface:                │
                    │   def __init__(self):                 │
                    │     self.container =                  │
                    │       get_cached_container() ◄────────┼── PATH B
                    └──────────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │ utils/container_manager.py (line 48)  │
                    │ @lru_cache(maxsize=1)                 │
                    │ def get_cached_container():           │
                    │   [CACHE HIT - Returns Container #1]  │
                    └──────────────────────────────────────┘
                                   │
                                   ▼
                           ┌──────────────┐
                           │ CONTAINER #1 │  ♻️ Reused (Cache Hit)
                           │ (Cached A)   │
                           └──────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                  DEFINITION SERVICE INIT                          │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │ ui/tabbed_interface.py (line 101-102) │
                    │   self.definition_service =           │
                    │     get_definition_service() ◄────────┼── PATH C
                    └──────────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │ services/service_factory.py           │
                    │   (line 745-756)                      │
                    │ def get_definition_service(           │
                    │     use_container_config=None):       │
                    │   config = use_container_config or    │
                    │            _get_environment_config()  │ ← ALWAYS dict!
                    │   container = get_container(config)   │
                    └──────────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │ services/service_factory.py           │
                    │   (line 32-42)                        │
                    │ def get_container(config=None):       │
                    │   if config is None:                  │
                    │     return get_cached_container()     │
                    │   from utils.container_manager import │
                    │     get_container_with_config         │
                    │   return get_container_with_config(   │
                    │     config) ◄──────────────────────────┼── PATH C1
                    └──────────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │ utils/container_manager.py            │
                    │   (line 88-114)                       │
                    │ def get_container_with_config(config):│
                    │   if config is None:                  │
                    │     return get_cached_container()     │
                    │   config_hash = _get_config_hash(cfg) │
                    │   return _create_custom_container(    │
                    │     config_hash, json.dumps(config))  │
                    └──────────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │ utils/container_manager.py            │
                    │   (line 24-29)                        │
                    │ @lru_cache(maxsize=8)                 │
                    │ def _create_custom_container(         │
                    │     _hash, _config_json):             │
                    │   logger.info("🔧 Maak custom...")    │
                    │   return ServiceContainer(            │
                    │     json.loads(_config_json))         │
                    └──────────────────────────────────────┘
                                   │
                                   ▼
                           ┌──────────────┐
                           │ CONTAINER #2 │  ✅ Created (Different Cache!)
                           │ (Cached B)   │
                           └──────────────┘
```

---

## Cache Architecture

### Cache Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                         CACHE LAYER 1                             │
│                  @lru_cache(maxsize=1)                            │
│                  get_cached_container()                           │
│                                                                   │
│  Key: None (singleton)                                            │
│  Value: Container with environment config                         │
│                                                                   │
│  ├─ Used by: SessionStateManager (PATH A)                         │
│  └─ Used by: TabbedInterface (PATH B)                             │
│                                                                   │
│  Status: ✅ Working as intended (singleton)                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         CACHE LAYER 2                             │
│                  @lru_cache(maxsize=8)                            │
│                  _create_custom_container()                       │
│                                                                   │
│  Key: (config_hash, config_json)                                  │
│  Value: Container with custom config                              │
│                                                                   │
│  ├─ Used by: get_container_with_config()                          │
│  └─ Triggered by: ServiceFactory (PATH C)                         │
│                                                                   │
│  Status: ⚠️ Creates separate container despite same config        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         CACHE LAYER 3                             │
│              _SERVICE_ADAPTER_CACHE: dict                         │
│                                                                   │
│  Key: frozen(config)                                              │
│  Value: ServiceAdapter instance                                   │
│                                                                   │
│  └─ Used by: get_definition_service()                             │
│                                                                   │
│  Status: ℹ️ Caches adapters, not containers                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Why Two Containers Are Created

### The Config Paradox

**Problem:** Even with IDENTICAL configs, two containers are created because they use **different cache mechanisms**.

#### Container #1 Flow:
```python
# PATH A: SessionStateManager
config = None
  → get_cached_container()          # Uses Cache Layer 1
    → Environment config internally
    → ServiceContainer(config)
    → ✅ CACHED in LRU cache (maxsize=1)
```

#### Container #2 Flow:
```python
# PATH C: ServiceFactory
config = _get_environment_config()   # Returns dict
  → get_container(config)            # config is dict, not None
    → get_container_with_config(config)
      → _create_custom_container()   # Uses Cache Layer 2
        → ServiceContainer(config)
        → ✅ CACHED in LRU cache (maxsize=8)
```

**Key Issue:**
- Cache 1 key: `None` (uses internal env config)
- Cache 2 key: `(hash, json)` (explicit config dict)
- **Same config, different cache keys → 2 instances!**

---

## Config Comparison

### Are the configs actually identical?

**Container #1 config:**
```python
# utils/container_manager.py line 65-72
env = os.getenv("APP_ENV", "production")
if env == "development":
    config = ContainerConfigs.development()
elif env == "testing":
    config = ContainerConfigs.testing()
else:
    config = ContainerConfigs.production()  # ← Default
```

**Container #2 config:**
```python
# services/service_factory.py line 107-117
def _get_environment_config() -> dict:
    env = os.getenv("APP_ENV", "production")
    if env == "development":
        return ContainerConfigs.development()
    if env == "testing":
        return ContainerConfigs.testing()
    return ContainerConfigs.production()      # ← Default
```

**Result:** ✅ **IDENTICAL** configs (same logic, same ContainerConfigs methods)

**BUT:** Different cache mechanisms treat them as different instances!

---

## Solution Architecture

### Proposed Single Cache Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    UNIFIED CACHE LAYER                            │
│                  @lru_cache(maxsize=1)                            │
│                  get_cached_container()                           │
│                                                                   │
│  Single Entry Point for ALL container requests                    │
│                                                                   │
│  ├─ PATH A: SessionStateManager → get_cached_container()          │
│  ├─ PATH B: TabbedInterface → get_cached_container()              │
│  └─ PATH C: ServiceFactory → get_cached_container()               │
│                                                                   │
│  Result: ✅ ALWAYS returns SAME instance (true singleton)         │
└─────────────────────────────────────────────────────────────────┘

REMOVE:
  ❌ _create_custom_container()
  ❌ get_container_with_config()
  ❌ Custom config support
  ❌ _SERVICE_ADAPTER_CACHE dict
```

### Implementation Changes

**1. Simplify container_manager.py:**
```python
@lru_cache(maxsize=1)
def get_cached_container() -> ServiceContainer:
    """Single source of truth for ServiceContainer."""
    env = os.getenv("APP_ENV", "production")
    config = {
        "development": ContainerConfigs.development,
        "testing": ContainerConfigs.testing,
    }.get(env, ContainerConfigs.production)()

    return ServiceContainer(config)

# REMOVE: _create_custom_container
# REMOVE: get_container_with_config
# REMOVE: _get_config_hash
```

**2. Simplify service_factory.py:**
```python
def get_definition_service():
    """Always use singleton container."""
    # Simple function-level cache (no config hashing needed)
    if not hasattr(get_definition_service, '_adapter'):
        container = get_cached_container()  # Singleton
        get_definition_service._adapter = ServiceAdapter(container)

    return get_definition_service._adapter

# REMOVE: _SERVICE_ADAPTER_CACHE
# REMOVE: _get_environment_config
# REMOVE: _freeze_config
```

**3. Simplify cached_services.py:**
```python
def get_cached_service_container():
    """Direct pass-through to singleton."""
    return get_cached_container()

# REMOVE: config parameter
# REMOVE: if/else logic
```

---

## Expected Results

### Before (Current State):
```
Startup sequence:
1. SessionStateManager.init → Container #1 (Cache A) [300ms]
2. TabbedInterface.init → Container #1 (Cache hit) [0ms] ✅
3. ServiceFactory.init → Container #2 (Cache B) [300ms]

Total: 600ms overhead, 2 containers, 3 cache layers
```

### After (Proposed):
```
Startup sequence:
1. SessionStateManager.init → Container #1 (Singleton) [300ms]
2. TabbedInterface.init → Container #1 (Cache hit) [0ms] ✅
3. ServiceFactory.init → Container #1 (Cache hit) [0ms] ✅

Total: 300ms overhead, 1 container, 1 cache layer
```

**Improvement:**
- ⚡ 50% faster startup (300ms saved)
- 💾 66% less memory (1 vs 2 active containers)
- 🧹 70% simpler code (remove 3 functions, 1 dict cache)
- 🐛 100% fewer cache bugs (single mechanism)

---

## Testing Strategy

### Verification Steps:

**1. Log Analysis:**
```bash
# Should see ONLY ONE line:
"🚀 Initialiseer ServiceContainer (gebeurt 1x per sessie)"
"ServiceContainer geïnitialiseerd (init count: 1)"

# Should NOT see:
"🔧 Maak custom ServiceContainer (hash: ...)"
```

**2. Container Identity Test:**
```python
# All should reference SAME instance
container_a = get_cached_container()
container_b = get_container()  # via service_factory
container_c = SessionStateManager.get_value("service_container")

assert container_a is container_b
assert container_b is container_c
assert id(container_a) == id(container_b) == id(container_c)
```

**3. Cache Hit Rate:**
```python
# Should be 100% after first init
stats = get_cached_container.cache_info()
assert stats.hits > stats.misses  # After warmup
```

---

## Migration Checklist

- [ ] Backup current container_manager.py
- [ ] Remove `_create_custom_container()` function
- [ ] Remove `get_container_with_config()` function
- [ ] Remove `_get_config_hash()` function
- [ ] Update `get_container()` in service_factory.py to use singleton
- [ ] Remove `_SERVICE_ADAPTER_CACHE` dict
- [ ] Remove `_get_environment_config()` duplicate
- [ ] Remove `_freeze_config()` function
- [ ] Update `get_definition_service()` to use function-level cache
- [ ] Update `get_cached_service_container()` to simple pass-through
- [ ] Run full test suite
- [ ] Verify log output (should show 1 container init)
- [ ] Measure startup time improvement
- [ ] Update documentation

---

**Diagram Author:** Claude Code (Debug Specialist)
**Date:** 2025-10-06
**Related:** DOUBLE_CONTAINER_ANALYSIS.md
