"""
Feature Flags Configuration voor V2 Services.
"""

import logging
import os
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class FeatureFlag(Enum):
    """Available feature flags."""

    # Validation Orchestrator V2
    VALIDATION_ORCHESTRATOR_V2 = "validation_orchestrator_v2"
    VALIDATION_ORCHESTRATOR_V2_SHADOW = "validation_orchestrator_v2_shadow"
    VALIDATION_ORCHESTRATOR_V2_CANARY = "validation_orchestrator_v2_canary"

    # AI Features
    AI_SUGGESTIONS = "ai_suggestions"
    AI_VALIDATION = "ai_validation"

    # Performance
    BATCH_PROCESSING = "batch_processing"
    ASYNC_VALIDATION = "async_validation"

    # Monitoring
    ENHANCED_METRICS = "enhanced_metrics"
    CORRELATION_TRACKING = "correlation_tracking"


class FeatureFlagManager:
    """
    Manages feature flags for gradual rollout of V2 services.

    Supports:
    - Environment variable overrides
    - Default configurations
    - Shadow mode (run both V1 and V2)
    - Canary deployments (percentage-based)
    - Kill switches for quick rollback
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize with optional config."""
        self._flags: dict[str, bool] = {}
        self._canary_percentages: dict[str, float] = {}
        self._load_defaults()

        if config:
            self._flags.update(config.get("feature_flags", {}))
            self._canary_percentages.update(config.get("canary_percentages", {}))

        self._load_from_environment()

    def _load_defaults(self) -> None:
        """Load default feature flag values."""
        # V2 Orchestrator - start disabled
        self._flags[FeatureFlag.VALIDATION_ORCHESTRATOR_V2.value] = False
        self._flags[FeatureFlag.VALIDATION_ORCHESTRATOR_V2_SHADOW.value] = False
        self._flags[FeatureFlag.VALIDATION_ORCHESTRATOR_V2_CANARY.value] = False

        # AI Features - enabled by default
        self._flags[FeatureFlag.AI_SUGGESTIONS.value] = True
        self._flags[FeatureFlag.AI_VALIDATION.value] = True

        # Performance - enabled
        self._flags[FeatureFlag.BATCH_PROCESSING.value] = True
        self._flags[FeatureFlag.ASYNC_VALIDATION.value] = True

        # Monitoring - enabled
        self._flags[FeatureFlag.ENHANCED_METRICS.value] = True
        self._flags[FeatureFlag.CORRELATION_TRACKING.value] = True

        # Canary percentages
        self._canary_percentages[
            FeatureFlag.VALIDATION_ORCHESTRATOR_V2_CANARY.value
        ] = 0.0

    def _load_from_environment(self) -> None:
        """Load feature flags from environment variables."""
        prefix = "FEATURE_FLAG_"

        for key, value in os.environ.items():
            if key.startswith(prefix):
                flag_name = key[len(prefix) :].lower()

                # Handle boolean flags
                if value.lower() in ("true", "1", "yes", "on"):
                    self._flags[flag_name] = True
                    logger.info(f"Feature flag '{flag_name}' enabled via environment")
                elif value.lower() in ("false", "0", "no", "off"):
                    self._flags[flag_name] = False
                    logger.info(f"Feature flag '{flag_name}' disabled via environment")

                # Handle canary percentages
                if flag_name.endswith("_canary"):
                    try:
                        percentage = float(value)
                        if 0 <= percentage <= 100:
                            self._canary_percentages[flag_name] = percentage / 100
                            logger.info(
                                f"Canary percentage for '{flag_name}' set to {percentage}%"
                            )
                    except ValueError:
                        logger.warning(
                            f"Invalid canary percentage for '{flag_name}': {value}"
                        )

    def is_enabled(self, flag: FeatureFlag, user_id: str | None = None) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            flag: The feature flag to check
            user_id: Optional user ID for canary deployments

        Returns:
            True if the feature is enabled for this request
        """
        flag_name = flag.value

        # Check if flag exists
        if flag_name not in self._flags:
            logger.warning(f"Unknown feature flag: {flag_name}")
            return False

        # Check basic enabled/disabled
        if not self._flags[flag_name]:
            return False

        # Check canary deployment
        if flag_name.endswith("_canary") and user_id:
            percentage = self._canary_percentages.get(flag_name, 0.0)
            if percentage > 0:
                # Simple hash-based canary (deterministic per user)
                user_hash = hash(user_id) % 100
                return user_hash < (percentage * 100)

        return self._flags[flag_name]

    def is_shadow_mode(self, flag: FeatureFlag) -> bool:
        """
        Check if a feature should run in shadow mode.

        Shadow mode runs both old and new implementations,
        comparing results without affecting the user.
        """
        shadow_flag = f"{flag.value}_shadow"
        return self._flags.get(shadow_flag, False)

    def set_flag(self, flag: FeatureFlag, enabled: bool) -> None:
        """
        Set a feature flag value (for testing).

        Args:
            flag: The feature flag to set
            enabled: Whether to enable or disable
        """
        self._flags[flag.value] = enabled
        logger.info(f"Feature flag '{flag.value}' set to {enabled}")

    def set_canary_percentage(self, flag: FeatureFlag, percentage: float) -> None:
        """
        Set canary deployment percentage.

        Args:
            flag: The feature flag
            percentage: Percentage of users (0-100)
        """
        if not 0 <= percentage <= 100:
            raise ValueError("Percentage must be between 0 and 100")

        canary_flag = f"{flag.value}_canary"
        self._canary_percentages[canary_flag] = percentage / 100
        logger.info(f"Canary percentage for '{flag.value}' set to {percentage}%")

    def get_status(self) -> dict[str, Any]:
        """Get current status of all feature flags."""
        return {
            "flags": dict(self._flags),
            "canary_percentages": {
                k: v * 100 for k, v in self._canary_percentages.items()
            },
        }

    def kill_switch(self, flag: FeatureFlag) -> None:
        """
        Emergency disable a feature flag.

        Args:
            flag: The feature flag to disable
        """
        self._flags[flag.value] = False

        # Also disable shadow and canary modes
        self._flags[f"{flag.value}_shadow"] = False
        self._flags[f"{flag.value}_canary"] = False
        self._canary_percentages[f"{flag.value}_canary"] = 0.0

        logger.warning(f"KILL SWITCH activated for feature '{flag.value}'")


# Global instance
_feature_flags = FeatureFlagManager()


def get_feature_flags() -> FeatureFlagManager:
    """Get the global feature flag manager."""
    return _feature_flags


def is_feature_enabled(flag: FeatureFlag, user_id: str | None = None) -> bool:
    """
    Convenience function to check if a feature is enabled.

    Args:
        flag: The feature flag to check
        user_id: Optional user ID for canary deployments

    Returns:
        True if the feature is enabled
    """
    return _feature_flags.is_enabled(flag, user_id)
