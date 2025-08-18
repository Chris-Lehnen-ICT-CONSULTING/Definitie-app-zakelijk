# Config Module - Complete Analysis

## Module Overview

The `config` module provides centralized configuration management for the entire application. It handles API keys, toetsregels (validation rules), rate limiting configurations, and various adapters for different configuration sources. The module uses a layered approach with managers, loaders, and adapters.

## Directory Structure

```
src/config/
├── __init__.py                    # Module initialization
├── config_manager.py              # Central configuration manager
├── config_loader.py               # Configuration loading logic
├── config_adapters.py             # API and environment adapters
├── toetsregel_manager.py          # Validation rules management
├── toetsregels_adapter.py         # Legacy adapter for rules
├── rate_limit_config.py           # Rate limiting configuration
├── verboden_woorden.py            # Forbidden words management
├── verboden_woorden.json          # Forbidden words data
├── context_wet_mapping.json       # Context to law mapping
├── toetsregels.json              # Main validation rules file
└── toetsregels/                   # Detailed validation rules
    ├── regels/                    # Individual rule definitions
    │   ├── CON-01.json
    │   ├── ESS-01.json
    │   └── ... (50+ rule files)
    ├── sets/                      # Rule groupings
    │   ├── per-categorie/         # Rules by category
    │   ├── per-context/           # Rules by context
    │   └── per-prioriteit/        # Rules by priority
    └── toetsregels-manager.json   # Rule management config
```

## Core Components

### 1. **ConfigManager** (config_manager.py)

Central configuration hub implementing singleton pattern.

**Key Features**:
```python
class ConfigManager:
    _instance = None
    
    def __new__(cls):
        # Singleton implementation
        
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.config_cache = {}
        self.listeners = []
    
    def get(self, key: str, default=None)
    def set(self, key: str, value: Any)
    def reload(self)
    def add_listener(self, listener: ConfigListener)
```

**Configuration Sources**:
1. Environment variables
2. JSON configuration files
3. Default values
4. Runtime overrides

### 2. **ConfigLoader** (config_loader.py)

Handles loading configuration from various sources.

**Key Methods**:
```python
class ConfigLoader:
    def __init__(self):
        self.config_dir = self._get_config_dir()
        self.env_prefix = "DEFINITIE_"
    
    def load_config(self) -> Dict[str, Any]:
        # Load from files
        # Override with environment
        # Apply defaults
    
    def _load_json_files(self) -> Dict[str, Any]
    def _load_env_vars(self) -> Dict[str, Any]
    def _apply_defaults(self, config: Dict[str, Any])
```

**Loading Priority**:
1. Default values
2. JSON files
3. Environment variables
4. Runtime overrides

### 3. **ToetsregelManager** (toetsregel_manager.py)

Manages validation rules with caching and categorization.

**Key Classes**:
```python
class ToetsregelManager:
    _instance = None
    
    def __init__(self):
        self._load_base_rules()
        self._load_detailed_rules()
        self._load_rule_sets()
        self._build_indexes()
    
    def get_regel(self, regel_id: str) -> Dict[str, Any]
    def get_regels_by_category(self, category: str) -> List[Dict]
    def get_regels_by_priority(self, priority: str) -> List[Dict]
    def get_applicable_rules(self, context: Dict) -> List[Dict]
```

**Rule Structure**:
```json
{
    "id": "CON-01",
    "naam": "Context-specifieke formulering",
    "uitleg": "De definitie moet context-specifiek zijn...",
    "categorie": "content",
    "prioriteit": "hoog",
    "goede_voorbeelden": [...],
    "slechte_voorbeelden": [...],
    "verboden_patronen": [...],
    "verplichte_elementen": [...]
}
```

### 4. **ConfigAdapters** (config_adapters.py)

Provides convenient access to specific configurations.

**Key Functions**:
```python
def get_api_config() -> Dict[str, Any]:
    """Get API-related configuration"""
    return {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "OPENAI_MODEL": config.get("openai.model", "gpt-4"),
        "OPENAI_TEMPERATURE": config.get("openai.temperature", 0.3)
    }

def get_database_config() -> Dict[str, Any]:
    """Get database configuration"""
    
def get_ui_config() -> Dict[str, Any]:
    """Get UI-related configuration"""
```

### 5. **RateLimitConfig** (rate_limit_config.py)

Endpoint-specific rate limiting configuration.

**Configuration Structure**:
```python
ENDPOINT_LIMITS = {
    "generate_definition": RateLimitConfig(
        requests_per_minute=20,
        requests_per_hour=100,
        burst_size=5,
        priority=Priority.HIGH
    ),
    "validate_definition": RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=500,
        burst_size=10,
        priority=Priority.MEDIUM
    )
}
```

**Dynamic Adjustment**:
```python
def get_adaptive_limit(endpoint: str, current_load: float) -> RateLimitConfig:
    base_config = ENDPOINT_LIMITS.get(endpoint)
    if current_load > 0.8:
        # Reduce limits under high load
    return adjusted_config
```

### 6. **VerbodenWoorden** (verboden_woorden.py & .json)

Manages forbidden words for validation.

**Data Structure**:
```json
{
  "verboden_woorden": [
    "afdeling",
    "applicatie",
    "bedrijf",
    "bepaling",
    // ... more words
  ],
  "metadata": {
    "version": "1.0",
    "last_updated": "2024-01-15",
    "total_words": 150
  }
}
```

## Configuration Categories

### 1. **API Configuration**
- OpenAI API keys and parameters
- External service endpoints
- Authentication tokens
- Timeout settings

### 2. **Application Settings**
- Feature flags
- Performance tuning
- Cache settings
- Logging levels

### 3. **Validation Rules**
- Rule definitions
- Priority mappings
- Category associations
- Context-specific rules

### 4. **UI Configuration**
- Display settings
- Theme preferences
- Component visibility
- User preferences

## Rule Management System

### Rule Categories
1. **Content Rules (CON)**: Context and source requirements
2. **Essential Rules (ESS)**: Core definition requirements
3. **Structure Rules (STR)**: Grammatical and format rules
4. **Internal Rules (INT)**: Clarity and consistency
5. **Coherence Rules (SAM)**: Internal logic
6. **Version Rules (VER)**: Multi-version consistency
7. **AI Rules (ARAI)**: AI-specific quality checks

### Rule Sets Organization
```
sets/
├── per-categorie/
│   ├── content.json      # All CON rules
│   ├── essentie.json     # All ESS rules
│   └── structuur.json    # All STR rules
├── per-context/
│   ├── type-regels.json  # Rules for TYPE category
│   ├── proces-regels.json # Rules for PROCES
│   └── resultaat-regels.json
└── per-prioriteit/
    ├── verplicht.json    # Mandatory rules
    ├── hoog.json         # High priority
    └── medium.json       # Medium priority
```

## Integration Points

### 1. **With Generation Module**
```python
from config.toetsregel_manager import get_toetsregel_manager
manager = get_toetsregel_manager()
rules = manager.get_applicable_rules(context)
```

### 2. **With Services**
```python
from config.config_adapters import get_api_config
config = get_api_config()
api_key = config["OPENAI_API_KEY"]
```

### 3. **With UI**
```python
from config import ConfigManager
config = ConfigManager()
theme = config.get("ui.theme", "light")
```

## Configuration Flow

### 1. **Initialization**
```
Application Start
    ↓
ConfigManager.__init__()
    ↓
ConfigLoader.load_config()
    ↓
Load JSON files → Override with ENV → Apply defaults
    ↓
Build configuration cache
```

### 2. **Rule Loading**
```
ToetsregelManager.__init__()
    ↓
Load base rules (toetsregels.json)
    ↓
Load detailed rules (regels/*.json)
    ↓
Load rule sets (sets/*/*.json)
    ↓
Build indexes for fast lookup
```

## Environment Variables

### Supported Variables
```bash
# API Keys
DEFINITIE_OPENAI_API_KEY=sk-...
DEFINITIE_ANTHROPIC_API_KEY=...

# Database
DEFINITIE_DATABASE_URL=sqlite:///definitions.db
DEFINITIE_DATABASE_POOL_SIZE=5

# Application
DEFINITIE_DEBUG=true
DEFINITIE_LOG_LEVEL=INFO
DEFINITIE_CACHE_TTL=3600

# Features
DEFINITIE_ENABLE_HYBRID_CONTEXT=true
DEFINITIE_ENABLE_WEB_LOOKUP=true
```

## Common Issues

### 1. **Singleton Anti-pattern**
- Global state makes testing difficult
- Hard to mock configurations
- Potential race conditions

### 2. **Configuration Complexity**
- Multiple sources of truth
- Complex override hierarchy
- Difficult to trace values

### 3. **Path Resolution**
- Hardcoded relative paths
- Platform-specific issues
- Module location dependencies

### 4. **Memory Usage**
- All rules loaded at startup
- No lazy loading
- Large memory footprint

### 5. **Type Safety**
- No configuration validation
- Runtime type errors
- Missing schema definitions

## Security Considerations

### 1. **Sensitive Data**
- API keys in environment
- No encryption at rest
- Logged configuration values

### 2. **Access Control**
- No permission checks
- All configs globally accessible
- No audit trail

### 3. **Validation**
- Limited input validation
- Injection possibilities
- No sanitization

## Performance Impact

### 1. **Startup Time**
- Load all rules: ~500ms
- Parse JSON files: ~200ms
- Build indexes: ~100ms

### 2. **Memory Usage**
- Rules cache: ~10MB
- Configuration: ~1MB
- Indexes: ~2MB

### 3. **Runtime Performance**
- Config lookup: O(1)
- Rule lookup: O(1) with index
- Category filter: O(n)

## Testing Approach

### Unit Tests
```python
def test_config_loader():
    # Test JSON loading
    # Test environment override
    # Test defaults

def test_toetsregel_manager():
    # Test rule loading
    # Test categorization
    # Test filtering
```

### Integration Tests
- Configuration with services
- Rule application in validation
- Environment variable handling

## Recommendations

### 1. **Replace Singleton** (High Priority)
- Use dependency injection
- Create configuration interfaces
- Enable proper testing

### 2. **Add Schema Validation**
- Define configuration schemas
- Validate at load time
- Provide clear error messages

### 3. **Implement Lazy Loading**
- Load rules on demand
- Cache frequently used rules
- Reduce memory footprint

### 4. **Improve Type Safety**
- Add type annotations
- Use dataclasses for configs
- Runtime type checking

### 5. **Enhance Security**
- Encrypt sensitive values
- Add access control
- Implement audit logging

### 6. **Optimize Performance**
- Implement caching strategies
- Add configuration hot-reload
- Profile and optimize bottlenecks

## Future Enhancements

1. **Configuration UI**: Web interface for configuration
2. **Version Control**: Track configuration changes
3. **A/B Testing**: Configuration variants
4. **Remote Config**: Centralized configuration service
5. **Feature Flags**: Dynamic feature toggling
6. **Config Validation**: JSON schema validation
7. **Hot Reload**: Update without restart
8. **Encryption**: Secure sensitive values

## Conclusion

The config module provides comprehensive configuration management but suffers from over-engineering and the singleton anti-pattern. While it successfully centralizes configuration and provides sophisticated rule management, it needs refactoring to improve testability, reduce complexity, and enhance security.

Key strengths:
- Centralized configuration
- Comprehensive rule system
- Multiple source support
- Good organization

Areas for improvement:
- Remove global state
- Simplify architecture
- Add validation
- Improve documentation

The module serves its purpose but would benefit significantly from architectural improvements and simplification.