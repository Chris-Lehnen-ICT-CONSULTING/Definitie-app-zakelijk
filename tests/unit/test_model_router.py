"""Unit tests for ModelRouter (DEF-314)."""

from unittest.mock import MagicMock, patch

import pytest

from services.ai.model_router import ModelRouter


@pytest.fixture
def routing_config():
    """Standard routing config for tests."""
    return {
        "active_provider": "openai",
        "task_tiers": {
            "critical": [
                "definition_core",
                "explanation",
                "examples",
                "counter_examples",
                "ontological_model",
            ],
            "standard": ["synonyms", "antonyms"],
        },
        "providers": {
            "openai": {
                "critical": "gpt-5.2",
                "standard": "gpt-5-mini",
            },
            "anthropic": {
                "critical": "claude-opus-4-5-20251101",
                "standard": "claude-haiku-4-5-20251001",
            },
        },
    }


@pytest.fixture
def router(routing_config):
    return ModelRouter(routing_config)


class TestTierMapping:
    """Test task_type → tier mapping."""

    def test_critical_tier_definition_core(self, router):
        _, model = router.get_model("definition_core")
        assert model == "gpt-5.2"

    def test_critical_tier_explanation(self, router):
        _, model = router.get_model("explanation")
        assert model == "gpt-5.2"

    def test_critical_tier_examples(self, router):
        _, model = router.get_model("examples")
        assert model == "gpt-5.2"

    def test_critical_tier_counter_examples(self, router):
        _, model = router.get_model("counter_examples")
        assert model == "gpt-5.2"

    def test_critical_tier_ontological_model(self, router):
        _, model = router.get_model("ontological_model")
        assert model == "gpt-5.2"

    def test_standard_tier_synonyms(self, router):
        _, model = router.get_model("synonyms")
        assert model == "gpt-5-mini"

    def test_standard_tier_antonyms(self, router):
        _, model = router.get_model("antonyms")
        assert model == "gpt-5-mini"


class TestProviderLookup:
    """Test provider selection."""

    def test_openai_provider(self, router):
        provider, _ = router.get_model("definition_core")
        assert provider == "openai"

    def test_anthropic_provider(self, routing_config):
        mock_cfg = MagicMock()
        mock_cfg.api.ai_provider = "anthropic"
        with patch("config.config_manager.get_config_manager", return_value=mock_cfg):
            router = ModelRouter(routing_config)
            provider, model = router.get_model("definition_core")
        assert provider == "anthropic"
        assert model == "claude-opus-4-5-20251101"

    def test_anthropic_standard_tier(self, routing_config):
        mock_cfg = MagicMock()
        mock_cfg.api.ai_provider = "anthropic"
        with patch("config.config_manager.get_config_manager", return_value=mock_cfg):
            router = ModelRouter(routing_config)
            _, model = router.get_model("synonyms")
        assert model == "claude-haiku-4-5-20251001"

    def test_active_provider_property(self, router):
        assert router.active_provider == "openai"


class TestUnknownTaskType:
    """Test fallback behavior for unknown task types."""

    def test_unknown_task_defaults_to_critical(self, router):
        _, model = router.get_model("unknown_task")
        assert model == "gpt-5.2"  # critical tier = safest

    def test_empty_string_defaults_to_critical(self, router):
        _, model = router.get_model("")
        assert model == "gpt-5.2"


class TestGetAvailableModels:
    """Test UI helper method."""

    def test_returns_tiers_for_openai(self, router):
        models = router.get_available_models()
        assert models == {"critical": "gpt-5.2", "standard": "gpt-5-mini"}

    def test_returns_tiers_for_anthropic(self, routing_config):
        mock_cfg = MagicMock()
        mock_cfg.api.ai_provider = "anthropic"
        with patch("config.config_manager.get_config_manager", return_value=mock_cfg):
            router = ModelRouter(routing_config)
            models = router.get_available_models()
        assert models == {
            "critical": "claude-opus-4-5-20251101",
            "standard": "claude-haiku-4-5-20251001",
        }
