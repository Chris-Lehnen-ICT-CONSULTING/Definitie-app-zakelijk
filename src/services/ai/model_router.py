"""
ModelRouter - Centralized model routing for DefinitieAgent.

Routes task types to the appropriate AI model via a tier system (critical/standard),
making the codebase provider-agnostic and eliminating hardcoded model names.

DEF-314: Replaces 12+ hardcoded model references across the codebase.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ModelRouter:
    """Routes task types to the correct AI model based on tier configuration.

    Uses a two-level routing strategy:
    1. Task type → tier (critical/standard)
    2. Tier + active provider → concrete model name

    Config structure (from config.yaml 'model_routing' section):
        active_provider: "openai"
        task_tiers:
            critical: [definition_core, explanation, examples, ...]
            standard: [synonyms, antonyms]
        providers:
            openai:
                critical: "gpt-5.2"
                standard: "gpt-5-mini"
            anthropic:
                critical: "claude-opus-4-5-20251101"
                standard: "claude-haiku-4-5-20251001"
    """

    def __init__(self, config: dict[str, Any]):
        self._config = config
        logger.info(
            "ModelRouter initialized: provider=%s, tiers=%s",
            self.active_provider,
            list(self._config.get("task_tiers", {}).keys()),
        )

    def get_model(self, task_type: str) -> tuple[str, str]:
        """Get (provider, model_name) for a task type.

        Args:
            task_type: The type of AI task (e.g. 'definition_core', 'synonyms')

        Returns:
            Tuple of (provider, model_name)
        """
        tier = self._get_tier(task_type)
        provider = self.active_provider
        model = self._config["providers"][provider][tier]
        return provider, model

    def _get_tier(self, task_type: str) -> str:
        """Map task type to tier. Unknown tasks default to 'critical' (safest)."""
        for tier, tasks in self._config.get("task_tiers", {}).items():
            if task_type in tasks:
                return tier
        logger.warning(
            "Unknown task_type '%s', defaulting to 'critical' tier", task_type
        )
        return "critical"

    @property
    def active_provider(self) -> str:
        """Return current provider, synced with ENV (set by sidebar on switch)."""
        try:
            from config.config_manager import get_config_manager

            return get_config_manager().api.ai_provider
        except Exception:
            return self._config.get("active_provider", "openai")

    def get_available_models(self) -> dict[str, str]:
        """For UI: returns {tier: model} of the active provider."""
        provider = self.active_provider
        return dict(self._config["providers"][provider])
