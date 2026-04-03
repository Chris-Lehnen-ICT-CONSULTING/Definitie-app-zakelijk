"""Integration tests for unified_voorbeelden task_type routing (DEF-314).

Verifies that each ExampleType maps to the correct ModelRouter task_type,
ensuring critical-tier tasks use the powerful model and standard-tier tasks
use the cheaper model. Also tests that provider switches propagate correctly.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voorbeelden.unified_voorbeelden import (
    _EXAMPLE_TYPE_TO_TASK_TYPE,
    ExampleRequest,
    ExampleType,
    GenerationMode,
    UnifiedExamplesGenerator,
    reset_examples_generator,
)

pytestmark = [pytest.mark.unit]


class TestExampleTypeToTaskTypeMapping:
    """Verify the static mapping is correct."""

    def test_voorbeeldzinnen_maps_to_examples(self):
        assert _EXAMPLE_TYPE_TO_TASK_TYPE["VOORBEELDZINNEN"] == "examples"

    def test_praktijkvoorbeelden_maps_to_examples(self):
        assert _EXAMPLE_TYPE_TO_TASK_TYPE["PRAKTIJKVOORBEELDEN"] == "examples"

    def test_tegenvoorbeelden_maps_to_counter_examples(self):
        assert _EXAMPLE_TYPE_TO_TASK_TYPE["TEGENVOORBEELDEN"] == "counter_examples"

    def test_synoniemen_maps_to_synonyms(self):
        assert _EXAMPLE_TYPE_TO_TASK_TYPE["SYNONIEMEN"] == "synonyms"

    def test_antoniemen_maps_to_antonyms(self):
        assert _EXAMPLE_TYPE_TO_TASK_TYPE["ANTONIEMEN"] == "antonyms"

    def test_toelichting_maps_to_explanation(self):
        assert _EXAMPLE_TYPE_TO_TASK_TYPE["TOELICHTING"] == "explanation"

    def test_all_example_types_have_mapping(self):
        for example_type in ExampleType:
            assert example_type.name in _EXAMPLE_TYPE_TO_TASK_TYPE


class TestTaskTypeRoutingInGeneration:
    """Verify that generate_definition is called with task_type, not model."""

    @pytest.fixture
    def generator(self):
        """Generator with mocked AI service."""
        with patch(
            "utils.container_manager.get_cached_container",
            side_effect=RuntimeError("no container"),
        ):
            gen = UnifiedExamplesGenerator()
        gen.ai_service = MagicMock()
        gen.ai_service.generate_definition = AsyncMock(
            return_value=MagicMock(text="item1\nitem2\nitem3")
        )
        return gen

    @pytest.fixture
    def base_request(self):
        return {
            "begrip": "test",
            "definitie": "test definitie",
            "context_dict": {"organisatorisch": [], "juridisch": [], "wettelijk": []},
            "generation_mode": GenerationMode.SYNC,
            "max_examples": 3,
        }

    def test_synoniemen_uses_standard_tier(self, generator, base_request):
        """Synoniemen should route to 'synonyms' task_type (standard tier)."""
        request = ExampleRequest(**base_request, example_type=ExampleType.SYNONIEMEN)
        generator.generate_examples(request)

        call_kwargs = generator.ai_service.generate_definition.call_args[1]
        assert call_kwargs["task_type"] == "synonyms"
        assert "model" not in call_kwargs

    def test_antoniemen_uses_standard_tier(self, generator, base_request):
        """Antoniemen should route to 'antonyms' task_type (standard tier)."""
        request = ExampleRequest(**base_request, example_type=ExampleType.ANTONIEMEN)
        generator.generate_examples(request)

        call_kwargs = generator.ai_service.generate_definition.call_args[1]
        assert call_kwargs["task_type"] == "antonyms"
        assert "model" not in call_kwargs

    def test_voorbeeldzinnen_uses_critical_tier(self, generator, base_request):
        """Voorbeeldzinnen should route to 'examples' task_type (critical tier)."""
        request = ExampleRequest(
            **base_request, example_type=ExampleType.VOORBEELDZINNEN
        )
        generator.generate_examples(request)

        call_kwargs = generator.ai_service.generate_definition.call_args[1]
        assert call_kwargs["task_type"] == "examples"

    def test_tegenvoorbeelden_uses_critical_tier(self, generator, base_request):
        """Tegenvoorbeelden should route to 'counter_examples' task_type."""
        request = ExampleRequest(
            **base_request, example_type=ExampleType.TEGENVOORBEELDEN
        )
        generator.generate_examples(request)

        call_kwargs = generator.ai_service.generate_definition.call_args[1]
        assert call_kwargs["task_type"] == "counter_examples"

    def test_toelichting_uses_critical_tier(self, generator, base_request):
        """Toelichting should route to 'explanation' task_type."""
        generator.ai_service.generate_definition = AsyncMock(
            return_value=MagicMock(text="Dit is een toelichting.")
        )
        request = ExampleRequest(**base_request, example_type=ExampleType.TOELICHTING)
        generator.generate_examples(request)

        call_kwargs = generator.ai_service.generate_definition.call_args[1]
        assert call_kwargs["task_type"] == "explanation"

    def test_no_model_parameter_passed(self, generator, base_request):
        """No model= should be passed — task_type handles routing."""
        for example_type in ExampleType:
            generator.ai_service.generate_definition = AsyncMock(
                return_value=MagicMock(text="item1\nitem2\nitem3")
            )
            request = ExampleRequest(**base_request, example_type=example_type)
            generator.generate_examples(request)

            call_kwargs = generator.ai_service.generate_definition.call_args[1]
            assert (
                "model" not in call_kwargs
            ), f"{example_type.name} should not pass model= parameter"


class TestAiServicePropertyAndProviderSwitch:
    """Verify ai_service is a live property, not a stale captured reference."""

    def test_ai_service_is_property(self):
        """ai_service should be a property on the class."""
        assert isinstance(
            UnifiedExamplesGenerator.ai_service, property
        ), "ai_service must be a property, not a plain attribute"

    def test_setter_allows_override(self):
        """Setting ai_service stores an override (used in tests)."""
        with patch(
            "utils.container_manager.get_cached_container",
            side_effect=RuntimeError("no container"),
        ):
            gen = UnifiedExamplesGenerator()
        mock_service = MagicMock()
        gen.ai_service = mock_service
        assert gen.ai_service is mock_service

    def test_property_fetches_from_container(self):
        """Without override, ai_service fetches from container each time."""
        mock_container = MagicMock()
        service_a = MagicMock(name="service_a")
        service_b = MagicMock(name="service_b")
        mock_container.orchestrator.return_value.ai_service = service_a

        with patch(
            "utils.container_manager.get_cached_container",
            return_value=mock_container,
        ):
            gen = UnifiedExamplesGenerator()
            # First access
            assert gen.ai_service is service_a

            # Simulate provider switch: container returns different service
            mock_container.orchestrator.return_value.ai_service = service_b
            assert gen.ai_service is service_b

    def test_reset_examples_generator_clears_global(self):
        """reset_examples_generator() sets the module global to None."""
        import voorbeelden.unified_voorbeelden as mod

        mod._generator = MagicMock()
        reset_examples_generator()
        assert mod._generator is None
