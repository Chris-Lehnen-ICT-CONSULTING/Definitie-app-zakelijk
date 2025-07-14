# Configuration Management System Documentation

## Overview

The DefinitieAgent Configuration Management System provides centralized, environment-specific configuration management with validation, hot-reloading, and backward compatibility.

## Features

- ✅ **Environment-specific configurations** (development, testing, production)
- ✅ **Hot-reloading** of configuration changes
- ✅ **Validation** of configuration values
- ✅ **Backward compatibility** with existing code
- ✅ **Type safety** with dataclasses and enums
- ✅ **Hierarchical configuration** (default → environment → env vars)
- ✅ **Change callbacks** for reactive configuration

## Configuration Structure

### Configuration Sections

```python
from config import ConfigSection

ConfigSection.API           # API settings (OpenAI, models, etc.)
ConfigSection.CACHE         # Cache settings (TTL, size, cleanup)
ConfigSection.PATHS         # File paths and directories
ConfigSection.UI            # User interface settings
ConfigSection.VALIDATION    # Validation rules and limits
ConfigSection.MONITORING    # Monitoring and alerting
ConfigSection.LOGGING       # Logging configuration
ConfigSection.RATE_LIMITING # Rate limiting settings
ConfigSection.RESILIENCE    # Resilience and retry settings
ConfigSection.SECURITY      # Security settings
```

### Environment Types

```python
from config import Environment

Environment.DEVELOPMENT  # Development environment
Environment.TESTING      # Testing environment
Environment.STAGING      # Staging environment
Environment.PRODUCTION   # Production environment
```

## Quick Start

### Basic Usage

```python
from config import get_config_manager, get_config, ConfigSection

# Get configuration manager
config_manager = get_config_manager()

# Get specific configuration section
api_config = get_config(ConfigSection.API)
print(f"Default model: {api_config.default_model}")
print(f"Temperature: {api_config.default_temperature}")

# Get cache configuration
cache_config = get_config(ConfigSection.CACHE)
print(f"Cache enabled: {cache_config.enabled}")
print(f"Cache TTL: {cache_config.default_ttl}")
```

### Using Configuration Adapters

```python
from config import get_api_config, get_cache_config, get_paths_config

# API configuration adapter
api_config = get_api_config()
api_key = api_config.ensure_api_key()
model_config = api_config.get_model_config("gpt-4")
gpt_params = api_config.get_gpt_call_params(temperature=0.5)

# Cache configuration adapter
cache_config = get_cache_config()
cache_settings = cache_config.get_cache_config()
ttl = cache_config.get_operation_ttl("definition")

# Paths configuration adapter
paths_config = get_paths_config()
cache_dir = paths_config.get_directory("cache")
exports_dir = paths_config.get_directory("exports")
```

### Backward Compatibility

```python
# These functions work exactly as before
from config import (
    get_openai_api_key,
    get_default_model,
    get_default_temperature,
    get_cache_directory,
    get_allowed_toetsregels,
    get_afkortingen
)

api_key = get_openai_api_key()
model = get_default_model()
temp = get_default_temperature()
cache_dir = get_cache_directory()
toetsregels = get_allowed_toetsregels()
afkortingen = get_afkortingen()
```

## Configuration Files

### File Hierarchy

1. **`config/config_default.yaml`** - Default settings for all environments
2. **`config/config_development.yaml`** - Development-specific overrides
3. **`config/config_testing.yaml`** - Testing-specific overrides
4. **`config/config_production.yaml`** - Production-specific overrides
5. **Environment variables** - Runtime overrides

### Configuration Loading Order

1. Load default configuration from `config_default.yaml`
2. Load environment-specific configuration (e.g., `config_development.yaml`)
3. Apply environment variable overrides
4. Validate configuration values

### Example Configuration File

```yaml
# config/config_development.yaml
api:
  default_model: "gpt-4"
  default_temperature: 0.1
  request_timeout: 60.0
  max_retries: 5

cache:
  enabled: true
  default_ttl: 600
  max_cache_size: 500

logging:
  level: "DEBUG"
  console_enabled: true
  file_enabled: true

rate_limiting:
  enabled: true
  requests_per_minute: 120
  tokens_per_second: 2.0
```

## Environment Variables

### Supported Environment Variables

```bash
# Environment detection
ENVIRONMENT=development  # development, testing, staging, production

# API configuration
OPENAI_API_KEY=sk-...
OPENAI_DEFAULT_MODEL=gpt-4
OPENAI_DEFAULT_TEMPERATURE=0.01
OPENAI_DEFAULT_MAX_TOKENS=300

# Cache configuration
CACHE_DIR=cache
CACHE_DEFAULT_TTL=3600

# Logging configuration
LOG_LEVEL=INFO

# Rate limiting
RATE_LIMIT_RPM=60
RATE_LIMIT_RPH=3000
```

### Environment Variable Example

```bash
# .env file
ENVIRONMENT=development
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_DEFAULT_MODEL=gpt-4
OPENAI_DEFAULT_TEMPERATURE=0.1
CACHE_DIR=dev_cache
LOG_LEVEL=DEBUG
RATE_LIMIT_RPM=120
```

## Advanced Usage

### Configuration Change Callbacks

```python
from config import get_config_manager

def on_api_config_change(section, key, old_value, new_value):
    print(f"API config changed: {key} = {new_value}")
    # Reinitialize API client, etc.

def on_cache_config_change(section, key, old_value, new_value):
    print(f"Cache config changed: {key} = {new_value}")
    # Clear cache, update TTL, etc.

# Register callbacks
config_manager = get_config_manager()
config_manager.register_change_callback("api", on_api_config_change)
config_manager.register_change_callback("cache", on_cache_config_change)
```

### Dynamic Configuration Updates

```python
from config import get_config_manager, set_config, ConfigSection

# Update configuration at runtime
set_config(ConfigSection.API, "default_temperature", 0.5)
set_config(ConfigSection.CACHE, "default_ttl", 1800)
set_config(ConfigSection.RATE_LIMITING, "requests_per_minute", 100)

# Save configuration changes
config_manager = get_config_manager()
config_manager.save_configuration()
```

### Configuration Validation

```python
from config import get_config_manager

config_manager = get_config_manager()

# Validate API key
if not config_manager.validate_api_key():
    print("Invalid or missing API key")

# Get environment information
env_info = config_manager.get_environment_info()
print(f"Environment: {env_info['environment']}")
print(f"Config loaded: {env_info['config_loaded']}")
print(f"API key configured: {env_info['api_key_configured']}")
```

## Environment-Specific Settings

### Development Environment

- Higher temperature for variation
- Longer timeouts for debugging
- More verbose logging
- Relaxed rate limiting
- Enabled monitoring and metrics export

### Testing Environment

- Deterministic settings (temperature = 0.0)
- Disabled caching
- Minimal logging
- Disabled resilience features
- Relaxed validation

### Production Environment

- Maximum consistency (temperature = 0.01)
- Strict validation
- Conservative rate limiting
- Comprehensive monitoring
- Security features enabled

## Integration Examples

### API Client Integration

```python
from config import get_api_config
from openai import OpenAI

api_config = get_api_config()

# Create OpenAI client with configuration
client = OpenAI(
    api_key=api_config.ensure_api_key(),
    timeout=api_config.config.request_timeout
)

# Get model-specific parameters
params = api_config.get_gpt_call_params(
    model="gpt-4",
    temperature=0.3  # Override if needed
)

# Make API call
response = client.chat.completions.create(
    model=params['model'],
    messages=[{"role": "user", "content": "Hello"}],
    temperature=params['temperature'],
    max_tokens=params['max_tokens']
)
```

### Cache System Integration

```python
from config import get_cache_config
from utils.cache import cached

cache_config = get_cache_config()

# Use configured TTL for caching
@cached(ttl=cache_config.get_operation_ttl("definition"))
def generate_definition(term):
    # Definition generation logic
    return f"Definition for {term}"

# Get cache directory
cache_dir = cache_config.config.cache_dir
```

### UI Integration

```python
from config import get_ui_config
import streamlit as st

ui_config = get_ui_config()

# Configure Streamlit page
st.set_page_config(**ui_config.get_streamlit_config())

# Get context options for dropdowns
context_options = ui_config.get_context_options()

organizational_context = st.selectbox(
    "Organizational Context",
    context_options['organizational']
)

# Get abbreviation expansion
if organizational_context in ui_config.config.afkortingen:
    full_name = ui_config.get_abbreviation(organizational_context)
    st.info(f"Full name: {full_name}")
```

### Validation Integration

```python
from config import get_validation_config

validation_config = get_validation_config()

# Check if toetsregel is allowed
if "CON-01" in validation_config.get_allowed_toetsregels():
    print("CON-01 is allowed")

# Get validation limits
limits = validation_config.get_validation_limits()
max_length = limits['max_text_length']

# Check strict mode
if validation_config.is_strict_mode():
    print("Strict validation enabled")
```

## Migration Guide

### From Hardcoded Values

**Before:**
```python
# Hardcoded values
DEFAULT_MODEL = "gpt-4"
DEFAULT_TEMPERATURE = 0.01
CACHE_DIR = "cache"
REQUESTS_PER_MINUTE = 60
```

**After:**
```python
# Using configuration system
from config import get_api_config, get_cache_config, get_rate_limiting_config

api_config = get_api_config()
model = api_config.config.default_model
temperature = api_config.config.default_temperature

cache_config = get_cache_config()
cache_dir = cache_config.config.cache_dir

rate_config = get_rate_limiting_config()
rpm = rate_config.config.requests_per_minute
```

### From Environment Variables

**Before:**
```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL", "gpt-4")
```

**After:**
```python
# Configuration system handles environment loading
from config import get_api_config

api_config = get_api_config()
api_key = api_config.ensure_api_key()  # Handles fallback to env var
model = api_config.config.default_model
```

### From Multiple Config Files

**Before:**
```python
# Multiple config imports
from config.toetsregels import laad_toetsregels
from config.verboden_woorden import laad_verboden_woorden
from some_module import CACHE_SETTINGS
from another_module import API_SETTINGS
```

**After:**
```python
# Single configuration system
from config import (
    get_validation_config,
    get_api_config,
    get_cache_config,
    laad_toetsregels,  # Backward compatibility
    laad_verboden_woorden  # Backward compatibility
)

validation_config = get_validation_config()
api_config = get_api_config()
cache_config = get_cache_config()
```

## Best Practices

### 1. Use Configuration Adapters

```python
# Good - Use adapters for type safety and convenience
from config import get_api_config
api_config = get_api_config()
params = api_config.get_gpt_call_params()

# Avoid - Direct config access
from config import get_config, ConfigSection
api_section = get_config(ConfigSection.API)
params = {'model': api_section.default_model}  # Less convenient
```

### 2. Environment-Specific Configuration

```python
# Good - Check environment and adjust behavior
from config import is_development, is_production

if is_development():
    # Enable debug features
    enable_debug_logging()

if is_production():
    # Enable monitoring
    enable_monitoring()
```

### 3. Configuration Validation

```python
# Good - Validate configuration at startup
from config import get_config_manager

def validate_configuration():
    config_manager = get_config_manager()
    
    if not config_manager.validate_api_key():
        raise ValueError("Invalid API key")
    
    env_info = config_manager.get_environment_info()
    if not env_info['directories_created']:
        raise ValueError("Required directories not created")

validate_configuration()
```

### 4. Use Change Callbacks

```python
# Good - React to configuration changes
from config import get_config_manager

def on_config_change(section, key, old_value, new_value):
    if section == 'api' and key == 'default_model':
        # Reinitialize API client
        reinitialize_api_client()
    elif section == 'cache' and key == 'default_ttl':
        # Update cache settings
        update_cache_settings()

config_manager = get_config_manager()
config_manager.register_change_callback('api', on_config_change)
config_manager.register_change_callback('cache', on_config_change)
```

## Troubleshooting

### Common Issues

1. **Missing API Key**
   ```python
   from config import get_api_config
   
   api_config = get_api_config()
   if not api_config.ensure_api_key():
       print("Set OPENAI_API_KEY environment variable")
   ```

2. **Configuration Not Loading**
   ```python
   from config import get_config_manager
   
   config_manager = get_config_manager()
   env_info = config_manager.get_environment_info()
   print(f"Config loaded: {env_info['config_loaded']}")
   print(f"Config file: {env_info['config_file']}")
   ```

3. **Directory Creation Issues**
   ```python
   from config import get_paths_config
   
   paths_config = get_paths_config()
   cache_dir = paths_config.get_directory('cache')
   if not os.path.exists(cache_dir):
       os.makedirs(cache_dir, exist_ok=True)
   ```

### Debug Configuration

```python
from config import get_config_manager

config_manager = get_config_manager()

# Print environment info
env_info = config_manager.get_environment_info()
print(json.dumps(env_info, indent=2))

# Print all configuration
for section in ConfigSection:
    config = get_config(section)
    print(f"{section.value}: {config.__dict__}")
```

## Testing

### Test Configuration

```python
# Set environment for testing
os.environ['ENVIRONMENT'] = 'testing'

from config import get_config_manager, is_testing

assert is_testing()

# Test configuration has appropriate settings
config_manager = get_config_manager()
assert config_manager.environment == Environment.TESTING
```

### Mocking Configuration

```python
import pytest
from config import get_config_manager, set_config, ConfigSection

@pytest.fixture
def mock_config():
    # Set test values
    set_config(ConfigSection.API, 'default_model', 'gpt-3.5-turbo')
    set_config(ConfigSection.API, 'default_temperature', 0.0)
    yield
    # Reset after test
    reload_config()
```

## Performance Considerations

- Configuration is loaded once at startup
- Adapters provide cached access to configuration
- Change callbacks allow efficient updates
- YAML parsing is done once per environment
- Environment variable lookups are cached

---

**Generated**: July 9, 2025  
**Version**: 1.0.0  
**Phase**: 2.6 - Configuration Management System
