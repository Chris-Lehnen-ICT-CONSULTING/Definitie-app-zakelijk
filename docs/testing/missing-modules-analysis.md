# Missing Modules Analysis - Sprint 0 Day 1

## Status: Import Errors Geanalyseerd

### 1. Modules die NIET bestaan (echt missing)

| Module | Used In | Action Required |
|--------|---------|-----------------|
| `prompt_builder.prompt_logger` | test_deep_functionality.py | Remove test or create mock |
| `AsyncAPIManager` from utils.async_api | test_performance.py | Check if renamed or removed |
| `validate_definitie_rich` from ai_toetser | test_enhanced_toetser.py | Use different validation function |
| `get_resilience_system` from utils.integrated_resilience | test_rate_limiter.py | Check actual function name |
| `CacheManager` from utils.cache | test_cache_system.py | Check if exists in cache.py |

### 2. Modules met WRONG IMPORT PATH (fixed)

| Module | Problem | Solution |
|--------|---------|----------|
| `get_config_manager` | Was importing from `config` | ✅ Fixed: `from config.config_manager` |
| `ConfigManager` | Was importing from `config` | ✅ Fixed: `from config.config_manager` |
| `get_api_config` | Old function name | Need to use `get_config(ConfigSection.API)` |

### 3. Other Issues

| File | Issue | Solution |
|------|-------|----------|
| test_ui_rate_limiter.py | Mock Streamlit setup | Need proper mock setup |
| test_toets_ver_03.py | Data structure error | Check toetsregels format |

## Investigation Needed

### 1. Check utils.async_api for actual exports
```python
# Need to check what's actually available in:
/src/utils/async_api.py
```

### 2. Check ai_toetser for validation functions
```python
# What validation functions are available in:
/src/ai_toetser/__init__.py
```

### 3. Check utils.integrated_resilience
```python
# What functions are exported from:
/src/utils/integrated_resilience.py
```

### 4. Check utils.cache for CacheManager
```python
# Is there a CacheManager class in:
/src/utils/cache.py
```

## Quick Fixes Still Needed

1. **Replace old function calls**:
   - `get_api_config()` → `get_config(ConfigSection.API)`
   - `get_cache_config()` → `get_config(ConfigSection.CACHE)`
   - `get_default_model()` → `get_config(ConfigSection.API).default_model`

2. **Remove/Update tests for missing modules**:
   - test_deep_functionality.py - remove prompt_logger dependency
   - test_enhanced_toetser.py - use available validation function

3. **Fix Mock Setup**:
   - test_ui_rate_limiter.py needs proper Streamlit mock