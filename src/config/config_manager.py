"""
Gecentraliseerd Configuratie Beheer Systeem voor DefinitieAgent.
Biedt geïntegreerd configuratie beheer met omgeving-specifieke instellingen,
validatie en hot-reloading mogelijkheden.

Deze module beheert alle configuratie instellingen voor de applicatie,
inclusief API keys, cache instellingen en omgeving-specifieke configuraties.
"""

import logging  # Logging systeem voor foutrapportage en debugging
import os  # Operating system interface voor omgevingsvariabelen
from dataclasses import dataclass, field  # Decorators voor gestructureerde data klassen
from datetime import (  # Datum/tijd functionaliteit voor timestamps
    UTC,
    datetime,
)
from enum import Enum  # Enumeratie types voor constante waarden
from pathlib import Path  # Object-georiënteerde bestandspad manipulatie
from typing import Any  # Type hints voor betere code documentatie

import yaml  # YAML bestand parser voor configuratie bestanden

logger = logging.getLogger(__name__)  # Logger instantie voor deze module


class Environment(Enum):
    """Omgeving types voor configuratie bepaling."""

    DEVELOPMENT = "development"  # Ontwikkel omgeving voor lokale ontwikkeling
    TESTING = "testing"  # Test omgeving voor geautomatiseerde tests
    STAGING = "staging"  # Pre-productie omgeving voor laatste verificatie
    PRODUCTION = "production"  # Live productie omgeving voor eindgebruikers


class ConfigSection(Enum):
    """Configuratie secties voor georganiseerde instellingen."""

    API = "api"  # API configuratie (keys, endpoints, timeouts)
    CACHE = "cache"  # Cache instellingen (TTL, grootte, strategie)
    PATHS = "paths"  # Bestandspaden (data, logs, exports)
    UI = "ui"  # Gebruikersinterface instellingen (layout, theming)
    VALIDATION = "validation"  # Validatie regels en criteria
    MONITORING = "monitoring"  # Monitoring en metriek verzameling
    LOGGING = "logging"  # Log niveaus en output configuratie
    RATE_LIMITING = "rate_limiting"  # API rate limiting instellingen
    RESILIENCE = "resilience"  # Fout tolerantie en retry strategieën
    SECURITY = "security"  # Beveiligingsinstellingen en toegangscontrole


@dataclass
class APIConfig:
    """API configuratie instellingen voor externe service communicatie."""

    openai_api_key: str = ""  # OpenAI API sleutel voor AI model toegang
    default_model: str = (
        "gpt-4.1"  # Standaard AI model voor definitie generatie (stabiel voor juridische definities)
    )
    default_temperature: float = (
        0.0  # Creativiteit niveau (0.0 = deterministisch voor juridische definities)
    )
    default_max_tokens: int = 300  # Maximum aantal tokens per API response
    request_timeout: float = 30.0  # Timeout in seconden voor API verzoeken
    max_retries: int = 3  # Maximum aantal herhaalpogingen bij mislukte verzoeken
    retry_backoff_factor: float = 1.5  # Exponentiële vertraging tussen pogingen

    # Model-specifieke instellingen per AI model type
    model_settings: dict[str, dict[str, Any]] = field(
        default_factory=lambda: {
            "gpt-4": {  # GPT-4 configuratie - hoogste kwaliteit
                "max_tokens": 300,  # Standaard token limiet voor GPT-4
                "temperature": 0.01,  # Zeer lage temperatuur voor consistentie
                "cost_per_token": 0.00003,  # Kosten per token in USD
            },
            "gpt-4.1": {  # GPT-4.1 configuratie - stabiel voor juridische definities
                "max_tokens": 300,  # Standaard token limiet
                "temperature": 0.0,  # Maximale consistentie (deterministisch)
                "cost_per_token": 0.00003,  # Kosten per token in USD
            },
        }
    )


@dataclass
class CacheConfig:
    """Cache configuration settings."""

    enabled: bool = True
    cache_dir: str = "cache"
    default_ttl: int = 3600
    max_cache_size: int = 1000
    cleanup_interval: int = 300

    # Operation-specific TTLs
    definition_ttl: int = 3600
    examples_ttl: int = 1800
    synonyms_ttl: int = 7200
    validation_ttl: int = 900


@dataclass
class PathsConfig:
    """File paths and directory configuration."""

    base_dir: str = "."
    cache_dir: str = "cache"
    exports_dir: str = "exports"
    logs_dir: str = "log"
    config_dir: str = "config"
    reports_dir: str = "reports"

    # Specific file paths
    toetsregels_file: str = "config/toetsregels.json"
    verboden_woorden_file: str = "config/verboden_woorden.json"
    context_mapping_file: str = "config/context_wet_mapping.json"
    rate_limit_history_file: str = "cache/rate_limit_history.json"


@dataclass
class UIConfig:
    """User interface configuration."""

    page_title: str = "DefinitieAgent"
    page_icon: str = "🧠"
    sidebar_width: int = 300

    # Context options
    organizational_contexts: list[str] = field(
        default_factory=lambda: [
            "OM",
            "ZM",
            "Reclassering",
            "DJI",
            "NP",
            "Justid",
            "KMAR",
            "FIOD",
            "CJIB",
            "Strafrechtketen",
            "Migratieketen",
            "Justitie en Veiligheid",
            "Anders...",
        ]
    )

    legal_contexts: list[str] = field(
        default_factory=lambda: [
            "Strafrecht",
            "Civiel recht",
            "Bestuursrecht",
            "Internationaal recht",
            "Anders...",
        ]
    )

    ketenpartners: list[str] = field(
        default_factory=lambda: [
            "ZM",
            "DJI",
            "KMAR",
            "CJIB",
            "JUSTID",
            "OM",
            "Politie",
            "Reclassering",
            "Halt",
            "Raad voor de Kinderbescherming",
        ]
    )

    # Afkortingen mapping voor gebruiksvriendelijke weergave
    # Helpt gebruikers om organisatie afkortingen te begrijpen
    afkortingen: dict[str, str] = field(
        default_factory=lambda: {
            "OM": "Openbaar Ministerie",  # Vervolging en opsporing
            "ZM": "Zittende Magistratuur",  # Rechterlijke macht
            "3RO": "Samenwerkingsverband Reclasseringsorganisaties",  # Reclassering
            "DJI": "Dienst Justitiële Inrichtingen",  # Gevangeniswezen
            "NP": "Nederlands Politie",  # Landelijke politie organisatie
            "FIOD": "Fiscale Inlichtingen- en Opsporingsdienst",  # Financieel onderzoek
            "Justid": "Dienst Justitiële Informatievoorziening",  # IT services Justitie
            "KMAR": "Koninklijke Marechaussee",  # Militaire politie
            "CJIB": "Centraal Justitieel Incassobureau",  # Boetes en incasso
            "AVG": "Algemene verordening gegevensbescherming",  # Privacy wetgeving
        }
    )


@dataclass
class ValidationConfig:
    """Validation configuration settings."""

    enabled: bool = True
    strict_mode: bool = False

    # Toegestane toetsregels
    allowed_toetsregels: list[str] = field(
        default_factory=lambda: [
            "CON-01",
            "CON-02",
            "ESS-01",
            "ESS-02",
            "ESS-04",
            "ESS-05",
            "INT-01",
            "INT-02",
            "INT-03",
            "INT-04",
            "INT-06",
            "INT-07",
            "INT-08",
            "SAM-01",
            "SAM-05",
            "SAM-07",
            "STR-01",
            "STR-02",
            "STR-03",
            "STR-04",
            "STR-05",
            "STR-06",
            "STR-07",
            "STR-08",
            "STR-09",
            "ARAI01",
            "ARAI02",
            "ARAI02SUB1",
            "ARAI02SUB2",
            "ARAI03",
            "ARAI04",
            "ARAI04SUB1",
            "ARAI05",
            "ARAI06",
        ]
    )

    # Validation thresholds
    max_text_length: int = 10000
    min_definition_length: int = 10
    max_definition_length: int = 500
    max_validation_errors: int = 10


@dataclass
class MonitoringConfig:
    """Monitoring and metrics configuration."""

    enabled: bool = True
    collect_metrics: bool = True
    export_metrics: bool = False

    # Alert thresholds
    error_rate_threshold: float = 0.1
    response_time_threshold: float = 5.0
    cost_threshold_daily: float = 10.0
    cost_threshold_monthly: float = 300.0

    # Metric collection intervals
    metrics_interval: int = 60
    health_check_interval: int = 30
    cost_calculation_interval: int = 300

    # OpenAI pricing (per 1K tokens)
    openai_pricing: dict[str, float] = field(
        default_factory=lambda: {"gpt-4": 0.03, "gpt-4.1": 0.03}
    )


@dataclass
class LoggingConfig:
    """Logging configuration settings."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"

    # Log destinations
    console_enabled: bool = True
    file_enabled: bool = True
    log_file: str = "log/definitie_agent.log"
    max_log_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

    # Module-specific log levels
    module_levels: dict[str, str] = field(
        default_factory=lambda: {
            "openai": "WARNING",
            "urllib3": "WARNING",
            "requests": "WARNING",
        }
    )


@dataclass
class RateLimitingConfig:
    """Rate limiting configuration."""

    enabled: bool = True

    # Default rate limits
    requests_per_minute: int = 60
    requests_per_hour: int = 3000
    max_concurrent: int = 10

    # Smart rate limiting
    tokens_per_second: float = 1.0
    bucket_capacity: int = 10
    target_response_time: float = 2.0
    adjustment_factor: float = 0.1
    min_rate: float = 0.1
    max_rate: float = 10.0

    # Priority settings
    priority_weights: dict[str, float] = field(
        default_factory=lambda: {
            "critical": 1.0,
            "high": 0.8,
            "normal": 0.6,
            "low": 0.4,
            "background": 0.2,
        }
    )


@dataclass
class ResilienceConfig:
    """Resilience and retry configuration."""

    enabled: bool = True

    # Retry settings
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    retry_strategy: str = "adaptive"

    # Circuit breaker
    failure_threshold: int = 3
    recovery_timeout: float = 30.0

    # Health monitoring
    health_check_interval: float = 30.0
    degraded_threshold: float = 0.8
    unhealthy_threshold: float = 0.5

    # Fallback settings
    enable_fallback: bool = True
    fallback_cache_duration: float = 300.0
    persist_failed_requests: bool = True


@dataclass
class SecurityConfig:
    """Security configuration settings."""

    enabled: bool = True

    # Input validation
    validate_inputs: bool = True
    sanitize_inputs: bool = True
    max_input_length: int = 10000

    # API security
    require_api_key: bool = True
    api_key_validation: bool = True

    # Rate limiting for security
    security_rate_limit: int = 100  # requests per minute
    block_duration: int = 300  # seconds

    # Threat detection
    detect_xss: bool = True
    detect_sql_injection: bool = True
    detect_path_traversal: bool = True


class ConfigManager:
    """Central configuration manager."""

    def __init__(
        self,
        environment: Environment = Environment.DEVELOPMENT,
        config_dir: str = "config",
    ):
        self.environment = environment
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / f"config_{environment.value}.yaml"
        self.default_config_file = self.config_dir / "config_default.yaml"

        # Configuration sections
        self.api: APIConfig = APIConfig()
        self.cache: CacheConfig = CacheConfig()
        self.paths: PathsConfig = PathsConfig()
        self.ui: UIConfig = UIConfig()
        self.validation: ValidationConfig = ValidationConfig()
        self.monitoring: MonitoringConfig = MonitoringConfig()
        self.logging: LoggingConfig = LoggingConfig()
        self.rate_limiting: RateLimitingConfig = RateLimitingConfig()
        self.resilience: ResilienceConfig = ResilienceConfig()
        self.security: SecurityConfig = SecurityConfig()

        # Component-specific AI configurations
        self.ai_components: dict = {}

        # Load configuration
        self._load_configuration()

        # Configuration change callbacks
        self._change_callbacks: dict[str, list[callable]] = {}

        logger.info(f"Configuration loaded for environment: {environment.value}")

    def _load_configuration(self):
        """Load configuration from files and environment variables."""
        # Geen .env laden; vertrouw op al ingestelde omgeving

        # Load from YAML files
        self._load_from_yaml()

        # Override with environment variables
        self._load_from_environment()

        # Validate configuration
        self._validate_configuration()

    def _load_from_yaml(self):
        """Load configuration from YAML files."""
        try:
            # Load default configuration
            if self.default_config_file.exists():
                with open(self.default_config_file) as f:
                    default_config = yaml.safe_load(f)
                    self._apply_config_dict(default_config)

            # Load environment-specific configuration
            if self.config_file.exists():
                with open(self.config_file) as f:
                    env_config = yaml.safe_load(f)
                    self._apply_config_dict(env_config)

        except Exception as e:
            logger.warning(f"Failed to load YAML configuration: {e}")

    def _load_from_environment(self):
        """Laad configuratie uit omgevingsvariabelen.

        Overschrijft standaard waarden met omgevingsvariabelen
        voor flexibele deployment configuratie.
        """
        # API configuratie uit omgevingsvariabelen
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_PROD")
        if api_key:
            self.api.openai_api_key = api_key

        if model := os.getenv("OPENAI_DEFAULT_MODEL"):
            self.api.default_model = model

        if temp := os.getenv("OPENAI_DEFAULT_TEMPERATURE"):
            self.api.default_temperature = float(temp)

        if tokens := os.getenv("OPENAI_DEFAULT_MAX_TOKENS"):
            self.api.default_max_tokens = int(tokens)

        # Omgeving-specifieke instellingen
        if env := os.getenv("ENVIRONMENT"):
            try:
                self.environment = Environment(env.lower())
            except ValueError:
                logger.warning(f"Ongeldige omgeving: {env}")

        # Cache configuratie
        if cache_dir := os.getenv("CACHE_DIR"):
            self.cache.cache_dir = cache_dir

        if cache_ttl := os.getenv("CACHE_DEFAULT_TTL"):
            self.cache.default_ttl = int(cache_ttl)

        # Logging configuratie
        if log_level := os.getenv("LOG_LEVEL"):
            self.logging.level = log_level.upper()

        # Rate limiting instellingen
        if rpm := os.getenv("RATE_LIMIT_RPM"):
            self.rate_limiting.requests_per_minute = int(rpm)

        if rph := os.getenv("RATE_LIMIT_RPH"):
            self.rate_limiting.requests_per_hour = int(rph)

    def _apply_config_dict(self, config_dict: dict[str, Any]):
        """Pas configuratie dictionary toe op config objecten.

        Args:
            config_dict: Dictionary met configuratie instellingen
        """
        for section_name, section_config in config_dict.items():
            if section_name == "ai_components":
                # Speciale behandeling voor ai_components
                self.ai_components = section_config
            elif hasattr(self, section_name):
                section_obj = getattr(self, section_name)
                for key, value in section_config.items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)

    def _validate_configuration(self):
        """Valideer configuratie instellingen.

        Controleert of alle configuratie waarden geldig zijn en
        maakt benodigde directories aan.
        """
        # Valideer API configuratie
        if not self.api.openai_api_key:
            logger.warning("OpenAI API key niet geconfigureerd")

        if self.api.default_temperature < 0 or self.api.default_temperature > 2:
            logger.warning(f"Ongeldige temperatuur: {self.api.default_temperature}")

        if self.api.default_max_tokens < 1 or self.api.default_max_tokens > 4096:
            logger.warning(f"Ongeldige max_tokens: {self.api.default_max_tokens}")

        # Valideer paden en maak directories aan
        for path_attr in [
            "cache_dir",
            "exports_dir",
            "logs_dir",
            "config_dir",
            "reports_dir",
        ]:
            path_value = getattr(self.paths, path_attr)
            path_obj = Path(path_value)
            if not path_obj.exists():
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Directory aangemaakt: {path_obj}")
                except Exception as e:
                    logger.error(f"Kan directory niet aanmaken {path_obj}: {e}")

        # Valideer rate limiting
        if self.rate_limiting.requests_per_minute <= 0:
            logger.warning("Ongeldige requests_per_minute")

        if self.rate_limiting.tokens_per_second <= 0:
            logger.warning("Ongeldige tokens_per_second")

    def get_config(self, section: ConfigSection) -> Any:
        """Get configuration for a specific section."""
        return getattr(self, section.value)

    def set_config(self, section: ConfigSection, key: str, value: Any):
        """Set configuration value and trigger callbacks."""
        config_obj = getattr(self, section.value)
        if hasattr(config_obj, key):
            old_value = getattr(config_obj, key)
            setattr(config_obj, key, value)

            # Trigger change callbacks
            self._trigger_callbacks(section.value, key, old_value, value)

            logger.info(f"Configuration updated: {section.value}.{key} = {value}")
        else:
            msg = f"Invalid config key: {section.value}.{key}"
            raise ValueError(msg)

    def register_change_callback(self, section: str, callback: callable):
        """Register callback for configuration changes."""
        if section not in self._change_callbacks:
            self._change_callbacks[section] = []
        self._change_callbacks[section].append(callback)

    def _trigger_callbacks(
        self, section: str, key: str, old_value: Any, new_value: Any
    ):
        """Trigger registered callbacks for configuration changes."""
        if section in self._change_callbacks:
            for callback in self._change_callbacks[section]:
                try:
                    callback(section, key, old_value, new_value)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

    def save_configuration(self):
        """Save current configuration to YAML file."""
        config_dict = {
            "api": self._dataclass_to_dict(self.api),
            "cache": self._dataclass_to_dict(self.cache),
            "paths": self._dataclass_to_dict(self.paths),
            "ui": self._dataclass_to_dict(self.ui),
            "validation": self._dataclass_to_dict(self.validation),
            "monitoring": self._dataclass_to_dict(self.monitoring),
            "logging": self._dataclass_to_dict(self.logging),
            "rate_limiting": self._dataclass_to_dict(self.rate_limiting),
            "resilience": self._dataclass_to_dict(self.resilience),
            "security": self._dataclass_to_dict(self.security),
        }

        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def _dataclass_to_dict(self, obj) -> dict[str, Any]:
        """Convert dataclass to dictionary."""
        result = {}
        for field_name, field_value in obj.__dict__.items():
            if isinstance(field_value, dict | list):
                result[field_name] = field_value
            else:
                result[field_name] = field_value
        return result

    def reload_configuration(self):
        """Reload configuration from files."""
        logger.info("Reloading configuration...")
        self._load_configuration()

        # Trigger callbacks for all sections
        for section in ConfigSection:
            if section.value in self._change_callbacks:
                for callback in self._change_callbacks[section.value]:
                    try:
                        callback(section.value, "reload", None, None)
                    except Exception as e:
                        logger.error(f"Reload callback error: {e}")

    def get_environment_info(self) -> dict[str, Any]:
        """Get current environment information."""
        return {
            "environment": self.environment.value,
            "config_file": str(self.config_file),
            "config_loaded": self.config_file.exists(),
            "api_key_configured": bool(self.api.openai_api_key),
            "directories_created": all(
                Path(getattr(self.paths, attr)).exists()
                for attr in ["cache_dir", "exports_dir", "logs_dir", "reports_dir"]
            ),
            "loaded_at": datetime.now(UTC).isoformat(),
        }

    def validate_api_key(self) -> bool:
        """Validate OpenAI API key."""
        if not self.api.openai_api_key:
            return False

        # Basic validation (starts with 'sk-')
        if not self.api.openai_api_key.startswith("sk-"):
            return False

        # Length validation
        return not len(self.api.openai_api_key) < 20


# Global configuration manager instance
_config_manager: ConfigManager | None = None


def get_config_manager(environment: Environment | None = None) -> ConfigManager:
    """Get or create global configuration manager."""
    global _config_manager

    if _config_manager is None:
        # Determine environment
        if environment is None:
            env_str = os.getenv("ENVIRONMENT", "development").lower()
            try:
                environment = Environment(env_str)
            except ValueError:
                environment = Environment.DEVELOPMENT

        _config_manager = ConfigManager(environment)

    return _config_manager


def get_config(section: ConfigSection) -> Any:
    """Convenience function to get configuration section."""
    return get_config_manager().get_config(section)


def set_config(section: ConfigSection, key: str, value: Any):
    """Convenience function to set configuration value."""
    get_config_manager().set_config(section, key, value)


def get_default_model() -> str:
    """Get the default AI model from configuration."""
    api_config: APIConfig = get_config(ConfigSection.API)
    return api_config.default_model


def get_default_temperature() -> float:
    """Get the default temperature from configuration."""
    api_config: APIConfig = get_config(ConfigSection.API)
    return api_config.default_temperature


def fill_ai_defaults(**kwargs) -> dict:
    """Fill AI request parameters with defaults from config where None."""
    if "model" in kwargs and kwargs["model"] is None:
        kwargs["model"] = get_default_model()
    if "temperature" in kwargs and kwargs["temperature"] is None:
        kwargs["temperature"] = get_default_temperature()
    return kwargs


def get_component_config(component: str, sub_component: str | None = None) -> dict:
    """Get AI configuration for a specific component.

    Args:
        component: Main component (e.g. 'voorbeelden', 'expert_review')
        sub_component: Optional sub-component (e.g. 'synoniemen', 'uitleg')

    Returns:
        Dict with model, temperature, and max_tokens settings
    """
    config = get_config_manager()

    # Check if we have ai_components in config
    if hasattr(config, "ai_components") and config.ai_components:
        comp_config = config.ai_components.get(component, {})

        # If sub_component specified, get nested config
        if sub_component and isinstance(comp_config, dict):
            comp_config = comp_config.get(sub_component, comp_config)

        # Return config if found
        if comp_config:
            return comp_config

    # Fallback to defaults
    return {
        "model": get_default_model(),
        "temperature": get_default_temperature(),
        "max_tokens": config.api.default_max_tokens,
    }


def reload_config():
    """Convenience function to reload configuration."""
    get_config_manager().reload_configuration()


def save_config():
    """Convenience function to save configuration."""
    get_config_manager().save_configuration()


# Environment detection helpers
def is_development() -> bool:
    """Check if running in development environment."""
    return get_config_manager().environment == Environment.DEVELOPMENT


def is_production() -> bool:
    """Check if running in production environment."""
    return get_config_manager().environment == Environment.PRODUCTION


def is_testing() -> bool:
    """Check if running in testing environment."""
    return get_config_manager().environment == Environment.TESTING


if __name__ == "__main__":
    # Test configuration manager
    print("🔧 Testing Configuration Manager")
    print("=" * 35)

    config = get_config_manager()

    print(f"Environment: {config.environment.value}")
    print(f"API Key configured: {config.validate_api_key()}")
    print(f"Default model: {config.api.default_model}")
    print(f"Cache directory: {config.cache.cache_dir}")
    print(f"Rate limit: {config.rate_limiting.requests_per_minute} RPM")

    # Test configuration access
    api_config = get_config(ConfigSection.API)
    print(f"API timeout: {api_config.request_timeout}s")

    # Test environment info
    env_info = config.get_environment_info()
    print(f"Environment info: {env_info}")

    # Save configuration
    config.save_configuration()
    print("Configuration saved successfully")
