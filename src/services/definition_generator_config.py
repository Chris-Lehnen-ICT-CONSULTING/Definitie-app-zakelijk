"""
Definition Generator Configuration Module.

Centralized configuration for all generator implementations,
extracted from all 3 original implementations.
"""

import os
from dataclasses import dataclass, field
from enum import Enum


class GenerationStrategy(Enum):
    """Strategy for definition generation."""

    BASIC = "basic"  # Basic GPT generation
    CONTEXT_AWARE = "context"  # With context intelligence
    HYBRID = "hybrid"  # With document/web integration
    ADAPTIVE = "adaptive"  # Adaptive based on content


class CacheStrategy(Enum):
    """Caching strategy options."""

    NONE = "none"
    MEMORY = "memory"  # In-memory cache
    REDIS = "redis"  # Redis distributed cache
    HYBRID = "hybrid"  # Memory + Redis fallback


@dataclass
class GPTConfig:
    """GPT-specific configuration (from all implementations)."""

    # Model configuration (optimized from definitie_generator)
    model: str = "gpt-4"
    temperature: float = 0.01  # Optimized for consistency
    max_tokens: int = 350  # Balanced for quality/cost

    # Reliability (from services)
    retry_count: int = 3
    timeout: float = 30.0
    backoff_factor: float = 2.0

    # API configuration
    api_key: str | None = None
    api_base: str | None = None
    organization: str | None = None

    def __post_init__(self):
        """Load API key from environment if not provided."""
        if self.api_key is None:
            self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_base is None:
            self.api_base = os.getenv("OPENAI_API_BASE")
        if self.organization is None:
            self.organization = os.getenv("OPENAI_ORGANIZATION")


@dataclass
class CacheConfig:
    """Cache configuration (from definitie_generator)."""

    strategy: CacheStrategy = CacheStrategy.MEMORY
    ttl: int = 3600  # 1 hour default
    max_entries: int = 1000  # Memory cache limit

    # Redis configuration (if used)
    redis_url: str | None = None
    redis_db: int = 0
    redis_prefix: str = "defgen:"

    # Cache key strategy
    include_context_in_key: bool = True
    include_model_in_key: bool = True

    def __post_init__(self):
        """Load Redis URL from environment if not provided."""
        if self.redis_url is None:
            self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")


@dataclass
class ContextConfig:
    """Context processing configuration (from generation)."""

    # Context expansion
    enable_web_lookup: bool = True
    enable_document_search: bool = False
    enable_rule_interpretation: bool = True

    # Context afkortingen (from generation)
    context_abbreviations: dict[str, str] = field(
        default_factory=lambda: {
            "OM": "Openbaar Ministerie",
            "ZM": "Zittende Magistratuur",
            "3RO": "Samenwerkingsverband Reclasseringsorganisaties",
            "DJI": "Dienst Justitiële Inrichtingen",
            "NP": "Nederlands Politie",
            "FIOD": "Fiscale Inlichtingen- en Opsporingsdienst",
            "Justid": "Dienst Justitiële Informatievoorziening",
            "KMAR": "Koninklijke Marechaussee",
            "CJIB": "Centraal Justitieel Incassobureau",
            "AVG": "Algemene verordening gegevensbescherming",
        }
    )

    # Web lookup configuration
    web_lookup_timeout: float = 10.0
    web_lookup_max_results: int = 5
    web_lookup_fallback: bool = True

    # Rule interpretation
    rule_interpretation_mode: str = "creative"  # creative, strict, balanced


@dataclass
class QualityConfig:
    """Quality control configuration (from services)."""

    # Text cleaning (from opschoning)
    enable_cleaning: bool = True
    cleaning_aggressive: bool = False

    # Ontology classification
    enable_ontology: bool = True
    ontology_confidence_threshold: float = 0.7

    # Enhancement features
    enable_enhancement: bool = True
    enhancement_temperature: float = 0.5
    enhancement_max_tokens: int = 300

    # New enhancement settings (Step 2)
    enable_completeness_enhancement: bool = True
    enable_linguistic_enhancement: bool = True
    enhancement_confidence_threshold: float = (
        0.6  # Minimum confidence to apply enhancement
    )

    # Validation
    enable_post_validation: bool = False
    validation_rules: list[str] = field(default_factory=list)


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration (from services)."""

    enable_monitoring: bool = True
    enable_metrics: bool = True
    enable_tracing: bool = False
    enable_alerts: bool = True  # Step 2 addition

    # Metrics collection
    track_generation_time: bool = True
    track_token_usage: bool = True
    track_cache_performance: bool = True
    track_quality_metrics: bool = True

    # Logging
    log_level: str = "INFO"
    log_prompts: bool = False  # Security: don't log prompts by default
    log_responses: bool = False  # Security: don't log responses by default
    log_errors: bool = True

    # Performance tracking
    performance_threshold_ms: int = 5000  # Warn if generation takes longer


@dataclass
class CompatibilityConfig:
    """Backward compatibility configuration."""

    enable_legacy_api: bool = True
    legacy_method_warnings: bool = True

    # Legacy service fallback
    fallback_to_legacy: bool = True
    legacy_timeout: float = 60.0

    # Migration settings
    gradual_rollout_percentage: int = 100  # % of traffic to new implementation


@dataclass
class UnifiedGeneratorConfig:
    """
    Master configuration class that combines all configuration aspects.

    This replaces the individual configs from all 3 implementations
    and provides a single source of truth for configuration.
    """

    # Core configurations
    gpt: GPTConfig = field(default_factory=GPTConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    context: ContextConfig = field(default_factory=ContextConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    compatibility: CompatibilityConfig = field(default_factory=CompatibilityConfig)

    # Generation strategy
    strategy: GenerationStrategy = GenerationStrategy.HYBRID

    # Feature flags (consolidated from all implementations)
    enable_async: bool = True
    enable_batch_processing: bool = False
    enable_feedback_learning: bool = True

    # Environment-based overrides
    environment: str = field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development")
    )

    def __post_init__(self):
        """Apply environment-specific configurations."""
        if self.environment == "production":
            # Production optimizations
            self.monitoring.enable_monitoring = True
            self.monitoring.log_prompts = False
            self.monitoring.log_responses = False
            self.cache.strategy = CacheStrategy.REDIS
            self.gpt.retry_count = 5

        elif self.environment == "development":
            # Development optimizations
            self.monitoring.log_level = "DEBUG"
            self.monitoring.log_errors = True
            self.cache.strategy = CacheStrategy.MEMORY
            self.compatibility.legacy_method_warnings = True

        elif self.environment == "testing":
            # Testing optimizations
            self.cache.strategy = CacheStrategy.NONE
            self.context.enable_web_lookup = False
            self.monitoring.enable_monitoring = False

    @classmethod
    def from_environment(cls) -> "UnifiedGeneratorConfig":
        """Create configuration from environment variables."""
        config = cls()

        # Override from environment variables
        if os.getenv("GENERATION_STRATEGY"):
            config.strategy = GenerationStrategy(os.getenv("GENERATION_STRATEGY"))

        if os.getenv("CACHE_STRATEGY"):
            config.cache.strategy = CacheStrategy(os.getenv("CACHE_STRATEGY"))

        gpt_model = os.getenv("GPT_MODEL")
        if gpt_model:
            config.gpt.model = gpt_model

        gpt_temperature = os.getenv("GPT_TEMPERATURE")
        if gpt_temperature:
            config.gpt.temperature = float(gpt_temperature)

        cache_ttl = os.getenv("CACHE_TTL")
        if cache_ttl:
            config.cache.ttl = int(cache_ttl)

        return config

    def validate(self) -> list[str]:
        """Validate configuration and return list of issues."""
        issues = []

        # Validate GPT config
        if not self.gpt.api_key:
            issues.append("OpenAI API key not configured")

        if self.gpt.temperature < 0 or self.gpt.temperature > 2:
            issues.append("GPT temperature must be between 0 and 2")

        if self.gpt.max_tokens < 1 or self.gpt.max_tokens > 4096:
            issues.append("GPT max_tokens must be between 1 and 4096")

        # Validate cache config
        if self.cache.strategy == CacheStrategy.REDIS and not self.cache.redis_url:
            issues.append("Redis URL required when using Redis cache strategy")

        # Validate context config
        if self.context.web_lookup_timeout <= 0:
            issues.append("Web lookup timeout must be positive")

        return issues

    def to_dict(self) -> dict:
        """Convert configuration to dictionary for serialization."""
        return {
            "gpt": {
                "model": self.gpt.model,
                "temperature": self.gpt.temperature,
                "max_tokens": self.gpt.max_tokens,
                "retry_count": self.gpt.retry_count,
                "timeout": self.gpt.timeout,
            },
            "cache": {
                "strategy": self.cache.strategy.value,
                "ttl": self.cache.ttl,
                "max_entries": self.cache.max_entries,
            },
            "context": {
                "enable_web_lookup": self.context.enable_web_lookup,
                "enable_rule_interpretation": self.context.enable_rule_interpretation,
            },
            "quality": {
                "enable_cleaning": self.quality.enable_cleaning,
                "enable_ontology": self.quality.enable_ontology,
                "enable_enhancement": self.quality.enable_enhancement,
            },
            "monitoring": {
                "enable_monitoring": self.monitoring.enable_monitoring,
                "enable_metrics": self.monitoring.enable_metrics,
                "log_level": self.monitoring.log_level,
            },
            "strategy": self.strategy.value,
            "environment": self.environment,
        }


# Convenience functions for common configurations


def get_production_config() -> UnifiedGeneratorConfig:
    """Get production-optimized configuration."""
    config = UnifiedGeneratorConfig()
    config.environment = "production"
    config.__post_init__()  # Apply environment-specific settings
    return config


def get_development_config() -> UnifiedGeneratorConfig:
    """Get development-optimized configuration."""
    config = UnifiedGeneratorConfig()
    config.environment = "development"
    config.__post_init__()  # Apply environment-specific settings
    return config


def get_testing_config() -> UnifiedGeneratorConfig:
    """Get testing-optimized configuration."""
    config = UnifiedGeneratorConfig()
    config.environment = "testing"
    config.__post_init__()  # Apply environment-specific settings
    return config
