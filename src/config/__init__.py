"""
Configuration package for DefinitieAgent.
Provides centralized configuration management with environment-specific settings.
"""

# Legacy imports for backward compatibility
from .config_loader import (
    laad_toetsregels,
    laad_verboden_woorden,
    _TOETSREGELS_PATH,
    _VERBODEN_WOORDEN_PATH,
)
from .verboden_woorden import (
    sla_verboden_woorden_op,
    log_test_verboden_woord,
    genereer_verboden_startregex,
)

# Core configuration system
from .config_manager import (
    ConfigManager,
    Environment,
    ConfigSection,
    get_config_manager,
    get_config,
    set_config,
    reload_config,
    save_config,
    is_development,
    is_production,
    is_testing
)

# Configuration adapters
from .config_adapters import (
    APIConfigAdapter,
    CacheConfigAdapter,
    RateLimitingConfigAdapter,
    ResilienceConfigAdapter,
    PathsConfigAdapter,
    UIConfigAdapter,
    ValidationConfigAdapter,
    MonitoringConfigAdapter,
    LoggingConfigAdapter,
    get_api_config,
    get_cache_config,
    get_rate_limiting_config,
    get_resilience_config,
    get_paths_config,
    get_ui_config,
    get_validation_config,
    get_monitoring_config,
    get_logging_config,
    # Backward compatibility functions
    get_openai_api_key,
    get_default_model,
    get_default_temperature,
    get_cache_directory,
    get_allowed_toetsregels,
    get_afkortingen
)

__all__ = [
    # Legacy exports
    "laad_toetsregels",
    "laad_verboden_woorden",
    "sla_verboden_woorden_op",
    "log_test_verboden_woord",
    "genereer_verboden_startregex",
    "_TOETSREGELS_PATH",
    "_VERBODEN_WOORDEN_PATH",
    
    # Core configuration
    "ConfigManager",
    "Environment",
    "ConfigSection",
    "get_config_manager",
    "get_config",
    "set_config",
    "reload_config",
    "save_config",
    "is_development",
    "is_production",
    "is_testing",
    
    # Configuration adapters
    "APIConfigAdapter",
    "CacheConfigAdapter",
    "RateLimitingConfigAdapter",
    "ResilienceConfigAdapter",
    "PathsConfigAdapter",
    "UIConfigAdapter",
    "ValidationConfigAdapter",
    "MonitoringConfigAdapter",
    "LoggingConfigAdapter",
    "get_api_config",
    "get_cache_config",
    "get_rate_limiting_config",
    "get_resilience_config",
    "get_paths_config",
    "get_ui_config",
    "get_validation_config",
    "get_monitoring_config",
    "get_logging_config",
    
    # Backward compatibility
    "get_openai_api_key",
    "get_default_model",
    "get_default_temperature",
    "get_cache_directory",
    "get_allowed_toetsregels",
    "get_afkortingen"
]

# Version info
__version__ = "1.0.0"
__author__ = "DefinitieAgent Development Team"
__description__ = "Centralized configuration management system with environment-specific settings"
