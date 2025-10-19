"""Feature flags configuration for DefinitieAgent.

This module provides centralized feature flag management to control
the availability of features, especially during migration from V1 to V2.
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FeatureStatus(Enum):
    """Feature status enumeration."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    BETA = "beta"
    DEPRECATED = "deprecated"


@dataclass
class FeatureFlag:
    """Feature flag configuration."""

    name: str
    description: str
    status: FeatureStatus
    default_enabled: bool
    env_var: str | None = None
    deprecation_message: str | None = None

    def is_enabled(self) -> bool:
        """Check if feature is enabled.

        Checks environment variable first, then falls back to default.
        """
        if self.env_var:
            env_value = os.getenv(self.env_var, "").lower()
            if env_value in ("true", "1", "yes", "on"):
                return True
            if env_value in ("false", "0", "no", "off"):
                return False

        return self.default_enabled and self.status != FeatureStatus.DISABLED


class FeatureFlags:
    """Centralized feature flags management."""

    # Legacy feature flags
    ENABLE_LEGACY_AGENT = FeatureFlag(
        name="legacy_agent",
        description="Enable legacy DefinitieAgent orchestrator",
        status=FeatureStatus.DEPRECATED,
        default_enabled=False,
        env_var="ENABLE_LEGACY_AGENT",
        deprecation_message=(
            "Legacy DefinitieAgent is deprecated. Please use V2 orchestrator."
        ),
    )

    ENABLE_V1_ORCHESTRATOR = FeatureFlag(
        name="v1_orchestrator",
        description="Enable V1 validation orchestrator",
        status=FeatureStatus.DEPRECATED,
        default_enabled=False,
        env_var="ENABLE_V1_ORCHESTRATOR",
        deprecation_message="V1 orchestrator is deprecated. V2 is now the default.",
    )

    ENABLE_DOMAIN_SERVICES = FeatureFlag(
        name="domain_services",
        description="Enable legacy domain services",
        status=FeatureStatus.DEPRECATED,
        default_enabled=False,
        env_var="ENABLE_DOMAIN_SERVICES",
        deprecation_message="Domain services are deprecated. Use unified services instead.",
    )

    # New/Current features
    ENABLE_CACHE = FeatureFlag(
        name="cache",
        description="Enable caching for voorbeelden generation",
        status=FeatureStatus.ENABLED,
        default_enabled=True,
        env_var="ENABLE_CACHE",
    )

    ENABLE_DEBUG_MODE = FeatureFlag(
        name="debug_mode",
        description="Enable debug mode with additional logging",
        status=FeatureStatus.ENABLED,
        default_enabled=False,
        env_var="DEBUG_MODE",
    )

    ENABLE_ASYNC_GENERATION = FeatureFlag(
        name="async_generation",
        description="Enable async generation for better performance",
        status=FeatureStatus.ENABLED,
        default_enabled=True,
        env_var="ENABLE_ASYNC_GENERATION",
    )

    @classmethod
    def get_all_flags(cls) -> dict[str, FeatureFlag]:
        """Get all feature flags.

        Returns:
            Dictionary of all feature flags
        """
        return {
            name: value
            for name, value in cls.__dict__.items()
            if isinstance(value, FeatureFlag)
        }

    @classmethod
    def get_enabled_features(cls) -> dict[str, bool]:
        """Get status of all features.

        Returns:
            Dictionary with feature names and their enabled status
        """
        return {flag.name: flag.is_enabled() for flag in cls.get_all_flags().values()}

    @classmethod
    def log_feature_status(cls):
        """Log the status of all feature flags."""
        logger.info("=== Feature Flags Status ===")
        for _name, flag in cls.get_all_flags().items():
            status = "ENABLED" if flag.is_enabled() else "DISABLED"
            logger.info(f"  {flag.name}: {status} ({flag.status.value})")
            if flag.deprecation_message and flag.is_enabled():
                logger.warning(f"    ⚠️  {flag.deprecation_message}")

    @classmethod
    def check_deprecated_features(cls) -> list[str]:
        """Check for enabled deprecated features.

        Returns:
            List of warning messages for enabled deprecated features
        """
        warnings = []
        for flag in cls.get_all_flags().values():
            if flag.status == FeatureStatus.DEPRECATED and flag.is_enabled():
                warnings.append(
                    f"Deprecated feature '{flag.name}' is enabled. {flag.deprecation_message}"
                )
        return warnings

    @classmethod
    def require_feature(cls, feature_flag: FeatureFlag) -> bool:
        """Check if a feature is required and enabled.

        Args:
            feature_flag: The feature flag to check

        Returns:
            True if enabled, False otherwise

        Raises:
            RuntimeError: If a required feature is disabled
        """
        if not feature_flag.is_enabled():
            if feature_flag.status == FeatureStatus.DEPRECATED:
                logger.warning(
                    f"Attempting to use deprecated feature '{feature_flag.name}'. "
                    f"{feature_flag.deprecation_message}"
                )
                return False
            msg = (
                f"Required feature '{feature_flag.name}' is disabled. "
                f"Enable it by setting {feature_flag.env_var}=true"
            )
            raise RuntimeError(
                msg
            )
        return True


def guard_legacy_route(feature_flag: FeatureFlag):
    """Decorator to guard legacy routes with feature flags.

    Args:
        feature_flag: The feature flag to check
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            if not feature_flag.is_enabled():
                logger.info(
                    f"Legacy route '{func.__name__}' is disabled by feature flag '{feature_flag.name}'"
                )
                # Return a no-op or raise an exception based on your needs
                return None

            # Log deprecation warning
            if feature_flag.deprecation_message:
                logger.warning(
                    f"Legacy route '{func.__name__}' is deprecated: {feature_flag.deprecation_message}"
                )

            return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator
