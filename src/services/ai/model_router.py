"""
ModelRouter - Centralized model routing for DefinitieAgent.

Routes task types to the appropriate AI model via a tier system (critical/standard),
making the codebase provider-agnostic and eliminating hardcoded model names.

DEF-314: Replaces 12+ hardcoded model references across the codebase.
"""

import logging
from typing import Any, cast

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
        pricing:  # per-token input/output cost, keyed by model name
            "gpt-5.2": {input: 0.00003, output: 0.00006}
            ...
    """

    # Last-resort pricing when a model is absent from the pricing map.
    _DEFAULT_PRICING: dict[str, float] = {"input": 0.00003, "output": 0.00006}

    _DEFAULT_CONFIG: dict[str, Any] = {
        "active_provider": "openai",
        "task_tiers": {
            "critical": [
                "definition_core",
                "explanation",
                "examples",
                "validation",
            ],
            "standard": ["synonyms", "antonyms"],
        },
        "providers": {
            "openai": {"critical": "gpt-5.2", "standard": "gpt-5-mini"},
            "anthropic": {
                "critical": "claude-opus-4-5-20251101",
                "standard": "claude-haiku-4-5-20251001",
            },
        },
        # DEF-458: canonical pricing — single source for CostCalculator.
        "pricing": {
            "gpt-5.2": {"input": 0.00003, "output": 0.00006},
            "gpt-5-mini": {"input": 0.0000015, "output": 0.000006},
            "claude-opus-4-5-20251101": {"input": 0.000015, "output": 0.000075},
            "claude-haiku-4-5-20251001": {"input": 0.0000008, "output": 0.000004},
        },
    }

    @classmethod
    def from_config(cls) -> "ModelRouter":
        """Build a router from the active config, bypassing the service container.

        Reads the optional ``model_routing`` section via ConfigManager and falls
        back to ``_DEFAULT_CONFIG``. Container-free on purpose: it is safe to call
        during container construction (e.g. from ``get_default_model``) without
        triggering singleton re-entrancy.
        """
        try:
            from config.config_manager import get_config_manager

            routing = getattr(get_config_manager(), "_model_routing_config", None)
        except Exception:
            logger.debug("Config unavailable for ModelRouter; using _DEFAULT_CONFIG")
            routing = None
        return cls(routing or {})

    def __init__(self, config: dict[str, Any]):
        self._config = (
            {**self._DEFAULT_CONFIG, **config} if config else dict(self._DEFAULT_CONFIG)
        )
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
                return cast("str", tier)
        logger.warning(
            "Unknown task_type '%s', defaulting to 'critical' tier", task_type
        )
        return "critical"

    @property
    def active_provider(self) -> str:
        """Return current provider, synced with ENV (set by sidebar on switch)."""
        try:
            from config.config_manager import get_config_manager

            return cast("str", get_config_manager().api.ai_provider)
        except Exception:
            return cast("str", self._config.get("active_provider", "openai"))

    def get_available_models(self) -> dict[str, str]:
        """For UI: returns {tier: model} of the active provider."""
        provider = self.active_provider
        return dict(self._config["providers"][provider])

    def get_critical_model(self) -> str:
        """Return the active provider's critical-tier model.

        Used as the canonical default model for cost estimates and as the
        resolution target when no explicit model is configured.
        """
        provider = self.active_provider
        return cast("str", self._config["providers"][provider]["critical"])

    def default_definition_model(self) -> str:
        """Resolve the model used for core definition generation.

        Single helper so callers don't repeat ``get_model("definition_core")[1]``
        and the ``definition_core`` routing key stays encapsulated in ModelRouter.
        """
        return self.get_model("definition_core")[1]

    def get_pricing(self, model: str) -> dict[str, float]:
        """Return {input, output} per-token pricing for a model.

        Falls back to a safe default for unknown models instead of raising,
        so cost accounting never crashes on a model swap.
        """
        pricing = self._config.get("pricing", {})
        return dict(pricing.get(model, self._DEFAULT_PRICING))

    def get_active_pricing(self) -> dict[str, dict[str, float]]:
        """Return the full pricing map (canonical source for CostCalculator)."""
        return {
            model: dict(prices)
            for model, prices in self._config.get("pricing", {}).items()
        }
