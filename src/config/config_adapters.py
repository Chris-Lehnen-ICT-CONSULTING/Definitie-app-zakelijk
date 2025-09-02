"""
Configuration adapters for integrating the centralized config system
with existing modules and maintaining backward compatibility.
"""

import logging
import os
from dataclasses import asdict
from typing import Any

from config.config_manager import ConfigSection, get_config, get_config_manager
from utils.enhanced_retry import RetryConfig
from utils.resilience import ResilienceConfig as FrameworkResilienceConfig
from utils.smart_rate_limiter import RateLimitConfig

logger = logging.getLogger(__name__)


class ConfigAdapter:
    """Base class for configuration adapters."""

    def __init__(self, config_section: ConfigSection):
        self.config_section = config_section
        self.config_manager = get_config_manager()
        self.config = get_config(config_section)

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value with fallback."""
        return getattr(self.config, key, default)

    def set_value(self, key: str, value: Any):
        """Set configuration value."""
        self.config_manager.set_config(self.config_section, key, value)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self.config)


class APIConfigAdapter(ConfigAdapter):
    """Adapter for API configuration."""

    def __init__(self):
        super().__init__(ConfigSection.API)

    def get_openai_client_config(self) -> dict[str, Any]:
        """Get OpenAI client configuration."""
        return {
            "api_key": self.config.openai_api_key,
            "timeout": self.config.request_timeout,
            "max_retries": self.config.max_retries,
        }

    def get_model_config(self, model: str | None = None) -> dict[str, Any]:
        """Get model-specific configuration."""
        model = model or self.config.default_model
        model_settings = self.config.model_settings.get(model, {})

        return {
            "model": model,
            "temperature": model_settings.get(
                "temperature", self.config.default_temperature
            ),
            "max_tokens": model_settings.get(
                "max_tokens", self.config.default_max_tokens
            ),
            "cost_per_token": model_settings.get("cost_per_token", 0.0),
        }

    def get_gpt_call_params(
        self, model: str | None = None, **overrides
    ) -> dict[str, Any]:
        """Get parameters for GPT API calls."""
        config = self.get_model_config(model)

        params = {
            "model": config["model"],
            "temperature": config["temperature"],
            "max_tokens": config["max_tokens"],
        }

        # Apply overrides, maar filter None waarden om defaults te behouden
        valid_overrides = {k: v for k, v in overrides.items() if v is not None}
        params.update(valid_overrides)

        return params

    def ensure_api_key(self) -> str:
        """Ensure API key is available, with fallback to environment."""
        api_key = self.config.openai_api_key

        if not api_key:
            # Fallback to environment variable
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_PROD")
            if api_key:
                self.set_value("openai_api_key", api_key)

        if not api_key:
            msg = "OpenAI API key not configured"
            raise ValueError(msg)

        return api_key


class CacheConfigAdapter(ConfigAdapter):
    """Adapter for cache configuration."""

    def __init__(self):
        super().__init__(ConfigSection.CACHE)

    def get_cache_config(self) -> dict[str, Any]:
        """Get cache configuration for cache utilities."""
        return {
            "enabled": self.config.enabled,
            "cache_dir": self.config.cache_dir,
            "default_ttl": self.config.default_ttl,
            "max_cache_size": self.config.max_cache_size,
            "cleanup_interval": self.config.cleanup_interval,
        }

    def get_operation_ttl(self, operation: str) -> int:
        """Get TTL for specific operation."""
        ttl_mapping = {
            "definition": self.config.definition_ttl,
            "examples": self.config.examples_ttl,
            "synonyms": self.config.synonyms_ttl,
            "validation": self.config.validation_ttl,
        }
        return ttl_mapping.get(operation, self.config.default_ttl)

    def get_cache_key_prefix(self, operation: str) -> str:
        """Get cache key prefix for operation."""
        return f"definitie_agent_{operation}"


class RateLimitingConfigAdapter(ConfigAdapter):
    """Adapter for rate limiting configuration."""

    def __init__(self):
        super().__init__(ConfigSection.RATE_LIMITING)

    def get_rate_limit_config(self) -> RateLimitConfig:
        """Get rate limit configuration for SmartRateLimiter."""
        return RateLimitConfig(
            tokens_per_second=self.config.tokens_per_second,
            bucket_capacity=self.config.bucket_capacity,
            target_response_time=self.config.target_response_time,
            adjustment_factor=self.config.adjustment_factor,
            min_rate=self.config.min_rate,
            max_rate=self.config.max_rate,
        )

    def get_async_api_limits(self) -> dict[str, int]:
        """Get rate limits for async API calls."""
        return {
            "requests_per_minute": self.config.requests_per_minute,
            "requests_per_hour": self.config.requests_per_hour,
            "max_concurrent": self.config.max_concurrent,
        }

    def get_priority_weight(self, priority: str) -> float:
        """Get priority weight for request."""
        return self.config.priority_weights.get(priority.lower(), 0.5)


class ResilienceConfigAdapter(ConfigAdapter):
    """Adapter for resilience configuration."""

    def __init__(self):
        super().__init__(ConfigSection.RESILIENCE)

    def get_retry_config(self) -> RetryConfig:
        """Get retry configuration for AdaptiveRetryManager."""
        return RetryConfig(
            max_retries=self.config.max_retries,
            base_delay=self.config.base_delay,
            max_delay=self.config.max_delay,
            strategy=self.config.retry_strategy,
            failure_threshold=self.config.failure_threshold,
            recovery_timeout=self.config.recovery_timeout,
        )

    def get_resilience_framework_config(self) -> FrameworkResilienceConfig:
        """Get configuration for ResilienceFramework."""
        return FrameworkResilienceConfig(
            health_check_interval=self.config.health_check_interval,
            degraded_threshold=self.config.degraded_threshold,
            unhealthy_threshold=self.config.unhealthy_threshold,
            enable_graceful_degradation=True,
            persist_failed_requests=self.config.persist_failed_requests,
            fallback_cache_duration=self.config.fallback_cache_duration,
        )

    def get_circuit_breaker_config(self) -> dict[str, Any]:
        """Get circuit breaker configuration."""
        return {
            "failure_threshold": self.config.failure_threshold,
            "recovery_timeout": self.config.recovery_timeout,
            "degraded_threshold": self.config.degraded_threshold,
            "unhealthy_threshold": self.config.unhealthy_threshold,
        }


class PathsConfigAdapter(ConfigAdapter):
    """Adapter for paths configuration."""

    def __init__(self):
        super().__init__(ConfigSection.PATHS)

    def get_directory(self, dir_type: str) -> str:
        """Get directory path for specific type."""
        dir_mapping = {
            "cache": self.config.cache_dir,
            "exports": self.config.exports_dir,
            "logs": self.config.logs_dir,
            "config": self.config.config_dir,
            "reports": self.config.reports_dir,
        }
        return dir_mapping.get(dir_type, self.config.base_dir)

    def get_file_path(self, file_type: str) -> str:
        """Get file path for specific type."""
        file_mapping = {
            "toetsregels": self.config.toetsregels_file,
            "verboden_woorden": self.config.verboden_woorden_file,
            "context_mapping": self.config.context_mapping_file,
            "rate_limit_history": self.config.rate_limit_history_file,
        }
        return file_mapping.get(file_type, "")

    def resolve_path(self, path: str) -> str:
        """Resolve relative path to absolute path."""
        if os.path.isabs(path):
            return path
        return os.path.join(self.config.base_dir, path)


class UIConfigAdapter(ConfigAdapter):
    """Adapter for UI configuration."""

    def __init__(self):
        super().__init__(ConfigSection.UI)

    def get_streamlit_config(self) -> dict[str, Any]:
        """Get Streamlit page configuration."""
        return {
            "page_title": self.config.page_title,
            "page_icon": self.config.page_icon,
            "layout": "wide",
            "initial_sidebar_state": "expanded",
        }

    def get_context_options(self) -> dict[str, list]:
        """Get context options for UI dropdowns."""
        return {
            "organizational": self.config.organizational_contexts,
            "legal": self.config.legal_contexts,
            "ketenpartners": self.config.ketenpartners,
        }

    def get_abbreviation(self, abbr: str) -> str:
        """Get full name for abbreviation."""
        return self.config.afkortingen.get(abbr, abbr)

    def get_all_abbreviations(self) -> dict[str, str]:
        """Get all abbreviations mapping."""
        return self.config.afkortingen.copy()


class ValidationConfigAdapter(ConfigAdapter):
    """Adapter for validation configuration."""

    def __init__(self):
        super().__init__(ConfigSection.VALIDATION)

    def get_allowed_toetsregels(self) -> set:
        """Get allowed toetsregels as set."""
        return set(self.config.allowed_toetsregels)

    def get_validation_limits(self) -> dict[str, int]:
        """Get validation limits."""
        return {
            "max_text_length": self.config.max_text_length,
            "min_definition_length": self.config.min_definition_length,
            "max_definition_length": self.config.max_definition_length,
            "max_validation_errors": self.config.max_validation_errors,
        }

    def is_strict_mode(self) -> bool:
        """Check if strict validation mode is enabled."""
        return self.config.strict_mode


class MonitoringConfigAdapter(ConfigAdapter):
    """Adapter for monitoring configuration."""

    def __init__(self):
        super().__init__(ConfigSection.MONITORING)

    def get_alert_thresholds(self) -> dict[str, float]:
        """Get alert thresholds."""
        return {
            "error_rate": self.config.error_rate_threshold,
            "response_time": self.config.response_time_threshold,
            "cost_daily": self.config.cost_threshold_daily,
            "cost_monthly": self.config.cost_threshold_monthly,
        }

    def get_monitoring_intervals(self) -> dict[str, int]:
        """Get monitoring intervals."""
        return {
            "metrics": self.config.metrics_interval,
            "health_check": self.config.health_check_interval,
            "cost_calculation": self.config.cost_calculation_interval,
        }

    def get_openai_pricing(self) -> dict[str, float]:
        """Get OpenAI pricing information."""
        return self.config.openai_pricing.copy()

    def get_cost_per_token(self, model: str) -> float:
        """Get cost per token for specific model."""
        return self.config.openai_pricing.get(model, 0.0)


class LoggingConfigAdapter(ConfigAdapter):
    """Adapter for logging configuration."""

    def __init__(self):
        super().__init__(ConfigSection.LOGGING)

    def get_logging_config(self) -> dict[str, Any]:
        """Get logging configuration for Python logging."""
        return {
            "level": self.config.level,
            "format": self.config.format,
            "datefmt": self.config.date_format,
            "handlers": self._get_handlers(),
        }

    def _get_handlers(self) -> list:
        """Get logging handlers configuration."""
        handlers = []

        if self.config.console_enabled:
            handlers.append(
                {
                    "class": "logging.StreamHandler",
                    "level": self.config.level,
                    "formatter": "default",
                }
            )

        if self.config.file_enabled:
            handlers.append(
                {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": self.config.level,
                    "formatter": "default",
                    "filename": self.config.log_file,
                    "maxBytes": self.config.max_log_size,
                    "backupCount": self.config.backup_count,
                }
            )

        return handlers

    def get_module_level(self, module: str) -> str:
        """Get log level for specific module."""
        return self.config.module_levels.get(module, self.config.level)

    def configure_logging(self):
        """Configure Python logging with current settings."""
        logging.basicConfig(
            level=getattr(logging, self.config.level),
            format=self.config.format,
            datefmt=self.config.date_format,
        )

        # Set module-specific levels
        for module, level in self.config.module_levels.items():
            logging.getLogger(module).setLevel(getattr(logging, level))


# Factory functions for easy access
def get_api_config() -> APIConfigAdapter:
    """Get API configuration adapter."""
    return APIConfigAdapter()


def get_cache_config() -> CacheConfigAdapter:
    """Get cache configuration adapter."""
    return CacheConfigAdapter()


def get_rate_limiting_config() -> RateLimitingConfigAdapter:
    """Get rate limiting configuration adapter."""
    return RateLimitingConfigAdapter()


def get_resilience_config() -> ResilienceConfigAdapter:
    """Get resilience configuration adapter."""
    return ResilienceConfigAdapter()


def get_paths_config() -> PathsConfigAdapter:
    """Get paths configuration adapter."""
    return PathsConfigAdapter()


def get_ui_config() -> UIConfigAdapter:
    """Get UI configuration adapter."""
    return UIConfigAdapter()


def get_validation_config() -> ValidationConfigAdapter:
    """Get validation configuration adapter."""
    return ValidationConfigAdapter()


def get_monitoring_config() -> MonitoringConfigAdapter:
    """Get monitoring configuration adapter."""
    return MonitoringConfigAdapter()


def get_logging_config() -> LoggingConfigAdapter:
    """Get logging configuration adapter."""
    return LoggingConfigAdapter()


# Convenience functions for backward compatibility
def get_openai_api_key() -> str:
    """Get OpenAI API key (backward compatibility)."""
    return get_api_config().ensure_api_key()


def get_default_model() -> str:
    """Get default model (backward compatibility)."""
    return get_api_config().config.default_model


def get_default_temperature() -> float:
    """Get default temperature (backward compatibility)."""
    return get_api_config().config.default_temperature


def get_cache_directory() -> str:
    """Get cache directory (backward compatibility)."""
    return get_paths_config().get_directory("cache")


def get_allowed_toetsregels() -> set:
    """Get allowed toetsregels (backward compatibility)."""
    return get_validation_config().get_allowed_toetsregels()


def get_afkortingen() -> dict[str, str]:
    """Get abbreviations mapping (backward compatibility)."""
    return get_ui_config().get_all_abbreviations()


if __name__ == "__main__":
    # Test configuration adapters
    print("🔧 Testing Configuration Adapters")
    print("=" * 40)

    # Test API config
    api_config = get_api_config()
    print(f"Default model: {api_config.config.default_model}")
    print(f"Default temperature: {api_config.config.default_temperature}")

    # Test cache config
    cache_config = get_cache_config()
    print(f"Cache enabled: {cache_config.config.enabled}")
    print(f"Cache TTL: {cache_config.get_operation_ttl('definition')}s")

    # Test paths config
    paths_config = get_paths_config()
    print(f"Cache directory: {paths_config.get_directory('cache')}")
    print(f"Exports directory: {paths_config.get_directory('exports')}")

    # Test UI config
    ui_config = get_ui_config()
    print(f"Page title: {ui_config.config.page_title}")
    print(f"Organizational contexts: {len(ui_config.config.organizational_contexts)}")

    # Test backward compatibility
    print("\nBackward compatibility:")
    print(f"Default model: {get_default_model()}")
    print(f"Cache directory: {get_cache_directory()}")
    print(f"Allowed toetsregels: {len(get_allowed_toetsregels())}")
    print(f"Abbreviations: {len(get_afkortingen())}")
