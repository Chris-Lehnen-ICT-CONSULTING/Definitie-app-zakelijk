"""
Configuration package voor DefinitieAgent.

Biedt gecentraliseerd configuratie management met omgeving-specifieke instellingen.
Beheert alle configuratie voor API's, caching, rate limiting, en applicatie instellingen.
"""

# Legacy imports voor achterwaartse compatibiliteit met oude code
from .config_loader import (
    laad_toetsregels,         # Laadt toetsregels uit configuratie bestand
    laad_verboden_woorden,    # Laadt verboden woorden lijst
    _TOETSREGELS_PATH,        # Pad naar toetsregels configuratie
    _VERBODEN_WOORDEN_PATH,   # Pad naar verboden woorden bestand
)
from .verboden_woorden import (
    sla_verboden_woorden_op,    # Slaat verboden woorden op naar bestand
    log_test_verboden_woord,    # Logt test van verboden woord
    genereer_verboden_startregex, # Genereert regex voor verboden woord start
)

# Kern configuratie systeem voor gecentraliseerd settings management
from .config_manager import (
    ConfigManager,        # Hoofdklasse voor configuratie management
    Environment,          # Omgeving enumeratie (dev, test, prod)
    ConfigSection,        # Configuratie sectie container
    get_config_manager,   # Factory functie voor config manager
    get_config,           # Haalt configuratie waarde op
    set_config,           # Zet configuratie waarde
    reload_config,        # Herlaadt configuratie uit bestanden
    save_config,          # Slaat configuratie op naar bestanden
    is_development,       # Check of development omgeving actief is
    is_production,        # Check of production omgeving actief is
    is_testing           # Check of testing omgeving actief is
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
