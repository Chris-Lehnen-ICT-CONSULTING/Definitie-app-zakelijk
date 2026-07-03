"""Unit tests for model+pricing single-source-of-truth (DEF-458).

Borgt dat modelnaam én pricing uit één canonieke bron komen (ModelRouter),
zodat dataclass-defaults niet meer kunnen afwijken en de pricing-tabel
meebeweegt met een modelwissel.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.ai.model_router import ModelRouter

pytestmark = [pytest.mark.unit]


# Verwachte canonieke pricing (per token) voor het actieve model.
GPT52_PRICING = {"input": 0.00003, "output": 0.00006}


@pytest.fixture
def force_openai():
    """Pin de actieve provider op openai voor deze test.

    De default-provider is anthropic (config.yaml); deze tests borgen de
    openai-routing/-pricing als concreet voorbeeld en moeten dus onafhankelijk
    zijn van de globale default.
    """
    mock_cfg = MagicMock()
    mock_cfg.api.ai_provider = "openai"
    with patch("config.config_manager.get_config_manager", return_value=mock_cfg):
        yield


class TestModelRouterPricing:
    """ModelRouter is de canonieke bron voor pricing."""

    def test_default_router_exposes_pricing(self):
        """Een router zonder config-override heeft pricing uit _DEFAULT_CONFIG."""
        router = ModelRouter({})
        assert router.get_pricing("gpt-5.2") == GPT52_PRICING

    def test_get_active_pricing_contains_all_active_models(self):
        router = ModelRouter({})
        pricing = router.get_active_pricing()
        for model in (
            "gpt-5.2",
            "gpt-5-mini",
            "claude-opus-4-8",
            "claude-opus-4-5-20251101",
            "claude-haiku-4-5-20251001",
        ):
            assert model in pricing, f"{model} ontbreekt in pricing-map"

    def test_get_pricing_unknown_model_falls_back(self):
        """Onbekend model → veilige fallback i.p.v. KeyError."""
        router = ModelRouter({})
        pricing = router.get_pricing("does-not-exist")
        assert set(pricing) == {"input", "output"}

    def test_get_critical_model_openai(self, force_openai):
        router = ModelRouter({})
        assert router.get_critical_model() == "gpt-5.2"

    def test_get_critical_model_anthropic(self):
        mock_cfg = MagicMock()
        mock_cfg.api.ai_provider = "anthropic"
        with patch("config.config_manager.get_config_manager", return_value=mock_cfg):
            router = ModelRouter({})
            # Default Anthropic-model = hoogste Opus voor alle tiers.
            assert router.get_critical_model() == "claude-opus-4-8"

    def test_config_override_replaces_pricing(self):
        """config.yaml model_routing kan pricing overschrijven (single source)."""
        router = ModelRouter(
            {
                "providers": {
                    "openai": {"critical": "gpt-x", "standard": "gpt-x-mini"}
                },
                "pricing": {"gpt-x": {"input": 0.001, "output": 0.002}},
            }
        )
        assert router.get_pricing("gpt-x") == {"input": 0.001, "output": 0.002}

    def test_get_pricing_unknown_model_fallback_values(self):
        """Onbekend model → exacte fallback-waarden (niet alleen de vorm)."""
        router = ModelRouter({})
        assert router.get_pricing("does-not-exist") == GPT52_PRICING

    def test_get_active_pricing_exact_values(self):
        """get_active_pricing levert de exacte tarieven, niet enkel de keys."""
        pricing = ModelRouter({}).get_active_pricing()
        assert pricing["gpt-5.2"] == GPT52_PRICING
        assert pricing["claude-haiku-4-5-20251001"] == {
            "input": 0.0000008,
            "output": 0.000004,
        }

    def test_default_definition_model_helper(self, force_openai):
        """De helper resolveert het definition_core-model (geen magic-index)."""
        assert ModelRouter({}).default_definition_model() == "gpt-5.2"


class TestCostCalculatorSingleSource:
    """CostCalculator rekent met pricing uit ModelRouter, niet uit een eigen tabel."""

    def test_calculate_cost_uses_router_pricing(self):
        from monitoring.api_monitor import CostCalculator

        # Mock container.model_router() → router met afwijkende pricing.
        fake_router = ModelRouter(
            {
                "providers": {"openai": {"critical": "gpt-5.2", "standard": "m"}},
                "pricing": {"gpt-5.2": {"input": 0.01, "output": 0.02}},
            }
        )
        fake_container = MagicMock()
        fake_container.model_router.return_value = fake_router
        with patch("services.container.get_container", return_value=fake_container):
            cost = CostCalculator.calculate_cost("gpt-5.2", 100, 50)
        # 100*0.01 + 50*0.02 = 2.0 — bewijst dat de router-pricing wordt gebruikt.
        assert cost == pytest.approx(2.0)

    def test_calculate_cost_regression_gpt52(self):
        """Regressie: standaard-pricing voor het actieve model blijft gelijk."""
        from monitoring.api_monitor import CostCalculator

        cost = CostCalculator.calculate_cost("gpt-5.2", 1000, 1000)
        expected = 1000 * GPT52_PRICING["input"] + 1000 * GPT52_PRICING["output"]
        assert cost == pytest.approx(expected)

    def test_router_falls_back_to_from_config_when_container_fails(self, force_openai):
        """Except-tak: container kapot → _router() valt terug op from_config()."""
        from monitoring.api_monitor import CostCalculator

        with patch(
            "services.container.get_container", side_effect=RuntimeError("boom")
        ):
            router = CostCalculator._router()
        assert router.get_critical_model() == "gpt-5.2"

    def test_estimate_monthly_cost_uses_router_critical_model(self, force_openai):
        """Maandraming gebruikt router-resolved critical model + pricing."""
        from monitoring.api_monitor import CostCalculator

        # 1000 req/dag, 1000 tokens → 700 in / 300 out per request
        # per request: 700*0.00003 + 300*0.00006 = 0.039 ; *1000*30 = 1170
        cost = CostCalculator.estimate_monthly_cost(1000, 1000)
        assert cost == pytest.approx(1170.0)

    async def test_record_api_call_resolves_model_when_none(self, force_openai):
        """record_api_call(model=None) → kost berekend met critical model."""
        from monitoring import api_monitor

        collector = MagicMock()
        collector.record_api_call = AsyncMock()
        with patch.object(api_monitor, "get_metrics_collector", return_value=collector):
            await api_monitor.record_api_call(
                endpoint="e",
                function_name="f",
                duration=0.1,
                success=True,
                tokens_used=1000,
                model=None,
            )
        recorded = collector.record_api_call.call_args[0][0]
        # 700*0.00003 + 300*0.00006 = 0.039 (gpt-5.2 critical pricing)
        assert recorded.cost == pytest.approx(0.039)


class TestDataclassDefaultsResolveViaRouter:
    """Dataclass-defaults zijn niet langer hardcoded modelnamen."""

    def test_gptconfig_model_default_is_none(self):
        from services.definition_generator_config import GPTConfig

        assert GPTConfig().model is None

    def test_gptconfig_resolved_model_is_active_model(self, force_openai):
        from services.definition_generator_config import GPTConfig

        assert GPTConfig().resolved_model == "gpt-5.2"

    def test_gptconfig_explicit_model_overrides(self):
        from services.definition_generator_config import GPTConfig

        cfg = GPTConfig(model="gpt-x")
        assert cfg.resolved_model == "gpt-x"

    def test_apiconfig_default_model_empty(self):
        from config.config_manager import APIConfig

        assert APIConfig().default_model == ""

    def test_get_default_model_resolves_via_router(self, force_openai):
        """get_default_model() valt terug op ModelRouter als config leeg is."""
        from config import config_manager

        empty_api = config_manager.APIConfig()  # default_model == ""
        with patch.object(config_manager, "get_config", return_value=empty_api):
            assert config_manager.get_default_model() == "gpt-5.2"
