"""Unit tests for ModelRouter (DEF-314)."""

from unittest.mock import MagicMock, patch

import pytest

from services.ai.model_router import ModelRouter

pytestmark = [pytest.mark.unit]


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
            # Arbitraire testwaarden om routing te bewijzen — NIET de app-default
            # (die is claude-opus-4-8, zie _DEFAULT_CONFIG in model_router.py).
            "anthropic": {
                "critical": "claude-opus-4-5-20251101",
                "standard": "claude-haiku-4-5-20251001",
            },
        },
    }


@pytest.fixture
def router(routing_config):
    # Pin provider=openai zodat deze routing-asserties deterministisch zijn,
    # onafhankelijk van de globale default-provider in config.yaml (nu anthropic).
    mock_cfg = MagicMock()
    mock_cfg.api.ai_provider = "openai"
    with patch("config.config_manager.get_config_manager", return_value=mock_cfg):
        yield ModelRouter(routing_config)


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


# === DEF-731: capability-policy (temperature) uit config ===
#
# De lijst met modelfamilies is een GECONFIGUREERDE verzendpolicy
# (legacycontract DEF-441), geen uitspraak over modelbeschikbaarheid of
# volledigheid. Router-kant: lezen en fail-safe interpreteren.


def _caps(families) -> dict:
    """Config-fragment met een temperature-policy voor provider anthropic."""
    return {
        "capabilities": {
            "anthropic": {
                "temperature": {
                    "source": "https://platform.claude.com/docs/en/about-claude/model-deprecations",
                    "checked_at": "2026-09-08",
                    "model_families": families,
                }
            }
        }
    }


class TestAcceptsTemperatureReadsConfig:
    def test_configured_family_is_accepted(self):
        router = ModelRouter(_caps(["opus-4-6"]))
        assert (
            router.accepts_temperature("claude-opus-4-6", provider="anthropic") is True
        )

    def test_model_outside_policy_is_omitted(self):
        router = ModelRouter(_caps(["opus-4-6"]))
        assert (
            router.accepts_temperature("claude-opus-4-8", provider="anthropic") is False
        )

    def test_match_is_case_insensitive(self):
        router = ModelRouter(_caps(["opus-4-6"]))
        assert (
            router.accepts_temperature("Claude-Opus-4-6", provider="anthropic") is True
        )

    def test_numeric_boundary_opus_4_1_does_not_match_4_10(self):
        """Bestaande grens uit DEF-441 blijft: 4-1 mag niet in 4-10 lekken."""
        router = ModelRouter(_caps(["opus-4-1"]))
        assert (
            router.accepts_temperature("claude-opus-4-1", provider="anthropic") is True
        )
        assert (
            router.accepts_temperature("claude-opus-4-10", provider="anthropic")
            is False
        )

    def test_policy_of_other_provider_does_not_leak(self):
        router = ModelRouter(
            {
                "capabilities": {
                    "openai": {"temperature": {"model_families": ["opus-4-6"]}}
                }
            }
        )
        # Positieve controle: bij openai telt de policy wel. Zonder deze
        # assertie zou de test ook slagen als het beleid nergens werkt.
        assert router.accepts_temperature("claude-opus-4-6", provider="openai") is True
        assert (
            router.accepts_temperature("claude-opus-4-6", provider="anthropic") is False
        )


class TestAcceptsTemperatureFailsSafe:
    """Ontbrekend, onbekend of malformed beleid schakelt temperature NOOIT in."""

    @pytest.mark.parametrize(
        "config",
        [
            {},
            {"capabilities": {}},
            {"capabilities": {"anthropic": {}}},
            {"capabilities": {"anthropic": {"temperature": {}}}},
            {"capabilities": {"anthropic": {"temperature": {"model_families": []}}}},
            # malformed: string in plaats van lijst (mag niet per karakter matchen)
            {
                "capabilities": {
                    "anthropic": {"temperature": {"model_families": "opus-4-6"}}
                }
            },
            {"capabilities": {"anthropic": {"temperature": {"model_families": False}}}},
            {"capabilities": {"anthropic": {"temperature": {"model_families": None}}}},
            {"capabilities": {"anthropic": {"temperature": "opus-4-6"}}},
            {"capabilities": {"anthropic": "opus-4-6"}},
            {"capabilities": "anthropic"},
            # malformed elementen binnen een verder geldige lijst
            {
                "capabilities": {
                    "anthropic": {"temperature": {"model_families": [None, 4, ""]}}
                }
            },
        ],
    )
    def test_malformed_or_missing_policy_omits(self, config):
        router = ModelRouter(config)
        assert (
            router.accepts_temperature("claude-opus-4-6", provider="anthropic") is False
        )

    def test_unknown_provider_omits(self):
        router = ModelRouter(_caps(["opus-4-6"]))
        assert (
            router.accepts_temperature("claude-opus-4-6", provider="mistral") is False
        )

    def test_valid_entries_still_work_next_to_malformed_ones(self):
        router = ModelRouter(_caps([None, "opus-4-6", 7]))
        assert (
            router.accepts_temperature("claude-opus-4-6", provider="anthropic") is True
        )
