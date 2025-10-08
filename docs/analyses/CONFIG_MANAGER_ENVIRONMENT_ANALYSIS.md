# ConfigManager Environment Handling Analysis

**Date:** 2025-10-07
**Analyst:** Claude Code
**Context:** US-202 Performance Optimization - Understanding forced DEVELOPMENT environment

---

## Executive Summary

ConfigManager has been intentionally **hardcoded to DEVELOPMENT mode** (lines 389-421) and ignores the `ENVIRONMENT` variable. However, this creates a **critical inconsistency** because:

1. **ServiceContainer uses APP_ENV** (via `container_manager.py` and `service_factory.py`)
2. **ConfigManager ignores APP_ENV/ENVIRONMENT** (forced to DEVELOPMENT)
3. These two systems load **different config files** based on different environment variables
4. The Environment enum still has PRODUCTION/TESTING values that are **unreachable**

This analysis examines the impact, inconsistencies, and provides recommendations.

---

## 1. Current Environment Handling Behavior

### 1.1 ConfigManager (src/config/config_manager.py)

**Lines 389-421: Forced DEVELOPMENT mode**

```python
class ConfigManager:
    def __init__(
        self,
        environment: Environment = Environment.DEVELOPMENT,
        config_dir: str = "config",
    ):
        # Forceer vaste omgeving (development) ongeacht ENVIRONMENT variabele
        self.environment = Environment.DEVELOPMENT  # <-- HARDCODED
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / f"config_{self.environment.value}.yaml"
        # ...
```

**Line 474: ENVIRONMENT variable explicitly ignored**

```python
def _load_from_environment(self):
    # ...
    # ENVIRONMENT wordt genegeerd; we hanteren één vaste omgeving
```

**Lines 664-672: Global singleton forced to DEVELOPMENT**

```python
def get_config_manager(environment: Environment | None = None) -> ConfigManager:
    """Get or create global configuration manager."""
    global _config_manager

    if _config_manager is None:
        # Eén vaste omgeving; negeer meegegeven/omgevingswaarde
        _config_manager = ConfigManager(Environment.DEVELOPMENT)

    return _config_manager
```

**Result:** ConfigManager **always** loads `config/config_development.yaml`, regardless of:
- `ENVIRONMENT` environment variable
- `environment` parameter passed to constructor
- Any runtime detection

### 1.2 ServiceContainer (src/utils/container_manager.py)

**Lines 48-57: Uses APP_ENV variable**

```python
@lru_cache(maxsize=1)
def get_cached_container() -> ServiceContainer:
    logger.info("🚀 Initialiseer ServiceContainer (gebeurt 1x per sessie)")

    # Bepaal environment configuratie
    env = os.getenv("APP_ENV", "production")  # <-- DIFFERENT VARIABLE

    if env == "development":
        config = ContainerConfigs.development()
    elif env == "testing":
        config = ContainerConfigs.testing()
    else:
        config = ContainerConfigs.production()
```

**Result:** ServiceContainer uses `APP_ENV` and loads **different configurations** based on it.

### 1.3 ServiceFactory (src/services/service_factory.py)

**Lines 94-104: Also uses APP_ENV**

```python
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

---

## 2. Configuration Files Analysis

### 2.1 Available Config Files

```
config/
├── config_default.yaml        # Base config (373 lines)
├── config_development.yaml    # Dev overrides (207 lines) - ALWAYS LOADED BY ConfigManager
├── config_production.yaml     # Prod overrides (128 lines) - NEVER LOADED
├── config_testing.yaml        # Test overrides (110 lines) - NEVER LOADED
```

### 2.2 Key Differences Between Environments

#### Development vs Production (Critical Differences)

| Setting | Development | Production | Impact |
|---------|------------|------------|--------|
| **default_model** | `gpt-4o-mini` | `gpt-4.1` (from default) | Cost & Quality |
| **default_temperature** | `0.9` | `0.01` | Determinism |
| **max_retries** | `5` | `3` | Resilience |
| **cache.default_ttl** | `600s` (10min) | `3600s` (1hr) | Performance |
| **cache.max_cache_size** | `500` | `2000` | Memory |
| **logging.level** | `DEBUG` | `INFO` | Verbosity |
| **logging.console_enabled** | `true` | `false` | Output |
| **monitoring.enabled** | `true` | `true` | Same |
| **rate_limiting.requests_per_minute** | `120` | `30` | Throttling |
| **validation.strict_mode** | `false` | `true` | Quality |

#### Testing vs Default (Critical Differences)

| Setting | Testing | Default | Impact |
|---------|---------|---------|--------|
| **default_model** | `gpt-3.5-turbo` | `gpt-4.1` | Speed |
| **cache.enabled** | `false` | `true` | Determinism |
| **monitoring.enabled** | `false` | `true` | Speed |
| **logging.level** | `ERROR` | `INFO` | Quiet |
| **rate_limiting.enabled** | `false` | `true` | Speed |
| **security.enabled** | `false` | `true` | Speed |

### 2.3 Component-Specific AI Configuration (config_default.yaml only)

The `ai_components` section (lines 23-121) defines **per-component model and temperature settings**:

```yaml
ai_components:
  definition_generator:
    model: "gpt-4.1"
    temperature: 0.0

  voorbeelden:
    synoniemen:
      model: "gpt-4.1"
      temperature: 0.2
    praktijkvoorbeelden:
      model: "gpt-4.1"
      temperature: 0.6
    # ... 15+ more component configs
```

**Critical Finding:** This section **only exists in config_default.yaml**. Development/production/testing configs don't define it, so they inherit from default.

---

## 3. What ConfigManager Actually Configures

### 3.1 Values Read Through ConfigManager

Based on grep analysis, ConfigManager is used for:

1. **API Configuration** (AIServiceV2, container.py)
   - OpenAI API key
   - Default model/temperature/max_tokens
   - Rate limiting settings (RateLimitConfig)

2. **UI Configuration** (components.py, definition_edit_tab.py, expert_review_tab.py)
   - Page title, icon, sidebar width
   - Context options (organizational, legal, laws)
   - Abbreviations mapping

3. **Component-Specific AI Config** (unified_voorbeelden.py)
   - Per-component model/temperature via `get_component_config()`

4. **Cache/Paths/Logging** (minimal usage)
   - Directory paths
   - Log levels

### 3.2 Values NOT Used from ConfigManager

ServiceContainer loads its own config from `ContainerConfigs` classes which are **not** derived from ConfigManager:

- Generator/validator feature toggles
- Database path
- Monitoring/quality/cleaning configs
- Duplicate detection settings
- Export/import settings

---

## 4. The Problem: Two Independent Configuration Systems

### 4.1 Inconsistency Table

| Component | Config Source | Environment Variable | Config File |
|-----------|--------------|---------------------|-------------|
| **ConfigManager** | config_manager.py | **NONE** (ignores ENVIRONMENT) | config_development.yaml |
| **ServiceContainer** | container_manager.py | **APP_ENV** (default: production) | ContainerConfigs.{env}() |
| **ServiceFactory** | service_factory.py | **APP_ENV** (default: production) | ContainerConfigs.{env}() |

### 4.2 Concrete Example of Inconsistency

**Scenario:** User sets `APP_ENV=production` to run in production mode

**What happens:**

1. **ServiceContainer** uses `APP_ENV=production` → loads `ContainerConfigs.production()`
   - Uses production thresholds, monitoring, etc.

2. **ConfigManager** ignores everything → always loads `config_development.yaml`
   - Uses `gpt-4o-mini` (dev model)
   - Uses `temperature=0.9` (high creativity)
   - Uses `DEBUG` logging
   - Uses `requests_per_minute=120` (high rate limit)

**Result:** Mixed configuration with unpredictable behavior!

---

## 5. What Breaks if We Respect APP_ENV

### 5.1 Theoretical Breakage

If ConfigManager were to respect `APP_ENV`:

1. **Production mode would use different models**
   - Current: Always `gpt-4o-mini` (from development config)
   - With fix: Would use `gpt-4.1` (from default, as production doesn't override)
   - Impact: **Better quality, higher cost**

2. **Temperature would become deterministic**
   - Current: Always `0.9` (creative)
   - With fix: Would use `0.01` (deterministic)
   - Impact: **More consistent results**

3. **Rate limiting would become stricter**
   - Current: Always `120 rpm` (development)
   - With fix: Would use `30 rpm` (production)
   - Impact: **Slower throughput**

4. **Logging would be quieter**
   - Current: Always `DEBUG` level
   - With fix: Would use `INFO` (production) or `ERROR` (testing)
   - Impact: **Less verbose output**

### 5.2 Actual Runtime Impact

**Finding:** The codebase appears to have been **developed and tested entirely in forced DEVELOPMENT mode**.

Evidence:
- No production deployments found
- All tests use forced development config
- CLAUDE.md states: "single-user applicatie, NIET in productie"

**Therefore:** Respecting APP_ENV would cause **zero production breakage** because there is no production environment.

### 5.3 Test Impact

Tests use multiple approaches:
- Some set `APP_ENV=testing`
- Some mock ConfigManager
- Some use `:memory:` database

If ConfigManager respected APP_ENV:
- Tests setting `APP_ENV=testing` would get testing config (cache disabled, faster model)
- Tests not setting APP_ENV would get **production** config (default in container_manager.py line 50)
- Result: **Some tests might become slower** but more realistic

---

## 6. Environment-Dependent Configuration Values

### 6.1 Critical Environment-Specific Values

**Values that SHOULD differ between environments:**

| Configuration | Development | Production | Testing | Purpose |
|--------------|------------|------------|---------|---------|
| **Model** | Fast/cheap | High-quality | Fast | Cost vs Quality |
| **Temperature** | Flexible | Deterministic | Deterministic | Consistency |
| **Cache** | Short TTL | Long TTL | Disabled | Performance vs freshness |
| **Logging** | Verbose | Moderate | Quiet | Debugging |
| **Rate Limiting** | Relaxed | Strict | Disabled | Protection |
| **Security** | Relaxed | Strict | Disabled | Speed vs safety |
| **Validation** | Relaxed | Strict | Relaxed | Quality gates |

### 6.2 Values That Should Be Consistent

**Values that should NOT differ:**

- UI configuration (contexts, laws, abbreviations)
- Component AI configs (voorbeelden temperatures)
- File paths structure
- Validation rules (toetsregels)

---

## 7. Dead Code Analysis

### 7.1 Unreachable Environment Enum Values

**Lines 23-31: Environment enum**

```python
class Environment(Enum):
    """Omgevingstype (vast: development)."""
    DEVELOPMENT = "development"
    # PRODUCTION and TESTING removed from enum
```

**Finding:** The enum originally had PRODUCTION and TESTING values (evidenced by helper functions):

```python
def is_production() -> bool:
    return get_config_manager().environment == Environment.PRODUCTION  # Always False!

def is_testing() -> bool:
    return get_config_manager().environment == Environment.TESTING  # Always False!
```

**Problem:** These functions are **dead code** that always return False because:
1. ConfigManager.environment is always `Environment.DEVELOPMENT`
2. But the enum definition doesn't include PRODUCTION/TESTING anymore
3. The helper functions reference non-existent enum values

This would cause an **AttributeError** at runtime if called!

### 7.2 Unused Config Files

- `config/config_production.yaml` - **Never loaded by ConfigManager**
- `config/config_testing.yaml` - **Never loaded by ConfigManager**

These files exist but are never used by the ConfigManager system.

---

## 8. Recommendations

### 8.1 Option A: Remove Environment Abstraction Entirely (RECOMMENDED)

**Rationale:**
- Single-user application
- No production deployment
- Simplifies codebase
- Aligns with current reality

**Changes:**
1. Remove Environment enum entirely
2. Remove `is_production()`, `is_testing()` helper functions
3. Rename `config_development.yaml` to `config.yaml`
4. Delete `config_production.yaml` and `config_testing.yaml`
5. Remove environment parameter from ConfigManager
6. Update container_manager.py to not use `APP_ENV`

**Benefits:**
- Eliminates confusion
- Removes dead code
- Simpler mental model
- Faster startup (no environment detection)

**Risks:**
- Future production deployment would require re-adding environment support
- Tests might need adjustment

### 8.2 Option B: Fix Environment Handling Consistency

**Rationale:**
- Future-proofs for production deployment
- Proper separation of concerns
- More maintainable

**Changes:**
1. ConfigManager respects `APP_ENV` variable
2. Add PRODUCTION and TESTING back to Environment enum
3. Unify environment variable (use APP_ENV everywhere)
4. ServiceContainer and ConfigManager use same environment logic
5. Test with all three environments

**Benefits:**
- Correct environment separation
- Supports future production deployment
- Tests can use realistic production config

**Risks:**
- More complex
- Tests might break
- Requires thorough testing

### 8.3 Option C: Keep Current Behavior, Document It

**Rationale:**
- Don't fix what isn't broken
- Current behavior is intentional (per comments)

**Changes:**
1. Document that app always runs in development mode
2. Remove unused production/testing config files
3. Remove dead helper functions (is_production, is_testing)
4. Update tests to not set APP_ENV (it's ignored)

**Benefits:**
- No behavior changes
- Low risk

**Risks:**
- Perpetuates confusion
- Future maintainers will be confused

---

## 9. Impact Analysis: Removing Development Config

### 9.1 What Uses config_development.yaml

Currently loaded by ConfigManager for all values. Key consumers:

1. **AIServiceV2** - Gets default model/temperature
2. **UI Components** - Gets context lists, abbreviations
3. **Rate Limiting** - Gets rate limit thresholds

### 9.2 Migration Path

If we remove development config:

1. **Merge development-specific values into config_default.yaml**
   - Keep the more permissive settings (higher rate limits, verbose logging)
   - OR make them configurable via environment variables

2. **Update ConfigManager to always load config_default.yaml**
   - Remove environment parameter
   - Remove config file selection logic

3. **Environment variables for key settings**
   ```bash
   OPENAI_MODEL=gpt-4o-mini  # Override default model
   LOG_LEVEL=DEBUG           # Override log level
   RATE_LIMIT_RPM=120        # Override rate limit
   ```

### 9.3 Affected Files

Files that would need updates:

- `src/config/config_manager.py` - Remove environment logic
- `src/utils/container_manager.py` - Remove APP_ENV usage
- `src/services/service_factory.py` - Remove environment config selection
- `tests/` - Update tests that set APP_ENV
- `config/` - Consolidate YAML files

---

## 10. Conclusion

**Current State:**
- ConfigManager is hardcoded to DEVELOPMENT mode
- This is intentional (per code comments)
- However, it creates inconsistency with ServiceContainer which uses APP_ENV
- Production/testing configs exist but are never loaded
- Helper functions reference non-existent enum values

**Root Cause:**
- Two independent configuration systems (ConfigManager vs ContainerConfigs)
- Different environment variables (ignored ENVIRONMENT vs APP_ENV)
- Partial refactoring left dead code

**Impact:**
- No production deployment → No actual breakage
- Confusing codebase for future maintainers
- Dead code (is_production, is_testing) that would error if called
- Inconsistent configuration loading

**Recommended Action:**
**Option A** - Remove environment abstraction entirely. This application is single-user, not deployed to production, and the complexity of environment handling is not justified.

**Critical Fix Required:**
Remove `is_production()` and `is_testing()` functions immediately - they reference non-existent enum values and will cause AttributeError if ever called.

---

## Appendix: File Locations

### Configuration Files
- `/Users/chrislehnen/Projecten/Definitie-app/config/config_default.yaml` (373 lines)
- `/Users/chrislehnen/Projecten/Definitie-app/config/config_development.yaml` (207 lines) - ALWAYS LOADED
- `/Users/chrislehnen/Projecten/Definitie-app/config/config_production.yaml` (128 lines) - NEVER LOADED
- `/Users/chrislehnen/Projecten/Definitie-app/config/config_testing.yaml` (110 lines) - NEVER LOADED

### Source Files
- `/Users/chrislehnen/Projecten/Definitie-app/src/config/config_manager.py` (788 lines)
- `/Users/chrislehnen/Projecten/Definitie-app/src/services/container.py` (639 lines)
- `/Users/chrislehnen/Projecten/Definitie-app/src/services/service_factory.py` (746 lines)
- `/Users/chrislehnen/Projecten/Definitie-app/src/utils/container_manager.py` (198 lines)
- `/Users/chrislehnen/Projecten/Definitie-app/src/services/ai_service_v2.py` (323 lines)

### Key Line References
- **config_manager.py:389-421** - Forced DEVELOPMENT initialization
- **config_manager.py:474** - ENVIRONMENT ignored comment
- **config_manager.py:664-672** - Global singleton forced to DEVELOPMENT
- **config_manager.py:749-762** - Dead helper functions (is_production, is_testing)
- **container_manager.py:48-57** - APP_ENV usage
- **service_factory.py:94-104** - Environment config selection
