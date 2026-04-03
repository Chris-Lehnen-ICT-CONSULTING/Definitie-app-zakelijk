"""Unit tests for AIServiceV2 task_type routing (DEF-314)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.ai.model_router import ModelRouter
from services.ai_service_v2 import AIServiceV2

pytestmark = [pytest.mark.unit]


@pytest.fixture
def mock_model_router():
    """ModelRouter mock that returns predictable models."""
    router = MagicMock(spec=ModelRouter)
    router.get_model.side_effect = lambda task_type: {
        "definition_core": ("openai", "gpt-5.2"),
        "synonyms": ("openai", "gpt-5-mini"),
    }.get(task_type, ("openai", "gpt-5.2"))
    return router


@pytest.fixture
def ai_service(mock_model_router):
    """AIServiceV2 with mocked ModelRouter."""
    return AIServiceV2(
        model_router=mock_model_router,
        ai_client=MagicMock(),
    )


class TestConstructor:
    """Test AIServiceV2 constructor model resolution."""

    def test_default_model_from_router(self, mock_model_router):
        service = AIServiceV2(model_router=mock_model_router, ai_client=MagicMock())
        assert service.default_model == "gpt-5.2"

    def test_explicit_default_model_overrides_router(self, mock_model_router):
        service = AIServiceV2(
            default_model="custom-model",
            model_router=mock_model_router,
            ai_client=MagicMock(),
        )
        assert service.default_model == "custom-model"

    def test_no_router_falls_back_to_config(self):
        with patch("services.ai_service_v2.get_config_manager") as mock_cfg:
            mock_cfg.return_value.api.default_model = "config-model"
            mock_cfg.return_value.api.rate_limit_requests_per_minute = 60
            mock_cfg.return_value.api.rate_limit_requests_per_hour = 3000
            mock_cfg.return_value.api.rate_limit_max_concurrent = 10
            mock_cfg.return_value.api.rate_limit_backoff_factor = 1.5
            mock_cfg.return_value.api.rate_limit_max_retries = 3
            service = AIServiceV2(ai_client=MagicMock())
            assert service.default_model == "config-model"


class TestTaskTypeRouting:
    """Test generate_definition task_type parameter."""

    @pytest.mark.asyncio
    async def test_task_type_routes_via_model_router(
        self, ai_service, mock_model_router
    ):
        """task_type should resolve model via ModelRouter."""
        with patch.object(ai_service, "_get_client") as mock_client:
            mock_client.return_value.chat_completion = AsyncMock(
                return_value="test definition"
            )

            result = await ai_service.generate_definition(
                prompt="test prompt",
                task_type="synonyms",
            )

            # Should have used the standard tier model
            mock_model_router.get_model.assert_called_with("synonyms")
            assert result.model == "gpt-5-mini"

    @pytest.mark.asyncio
    async def test_explicit_model_overrides_task_type(
        self, ai_service, mock_model_router
    ):
        """Explicit model= should override task_type."""
        # Reset call count (constructor calls get_model once for default_model)
        mock_model_router.get_model.reset_mock()

        with patch.object(ai_service, "_get_client") as mock_client:
            mock_client.return_value.chat_completion = AsyncMock(
                return_value="test definition"
            )

            result = await ai_service.generate_definition(
                prompt="test prompt",
                model="explicit-model",
                task_type="synonyms",
            )

            # model= takes precedence, ModelRouter should NOT be called during generate
            mock_model_router.get_model.assert_not_called()
            assert result.model == "explicit-model"

    @pytest.mark.asyncio
    async def test_no_task_type_uses_default_model(self, ai_service):
        """Without task_type, should use default_model."""
        with patch.object(ai_service, "_get_client") as mock_client:
            mock_client.return_value.chat_completion = AsyncMock(
                return_value="test definition"
            )

            result = await ai_service.generate_definition(
                prompt="test prompt",
            )

            assert result.model == "gpt-5.2"  # default from router's critical tier
