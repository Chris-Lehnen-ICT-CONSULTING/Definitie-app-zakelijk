"""
Tests voor Ontological Category Fix.

Valideert dat de ontologische categorie correct wordt gebruikt voor template selectie.
"""

import asyncio
from unittest.mock import Mock, patch

import pytest

from services.interfaces import GenerationRequest
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.prompts.prompt_service_v2 import PromptServiceConfig, PromptServiceV2


class TestOntologicalCategoryFix:
    """Test ontological category template selection fix."""

    def setup_method(self):
        """Setup test dependencies."""
        self.prompt_service = PromptServiceV2()

    @pytest.mark.asyncio
    async def test_prompt_service_v2_uses_ontological_category(self):
        """Test dat PromptServiceV2 ontological category gebruikt voor template selectie."""

        # Test verschillende categories
        test_cases = [
            ("proces", "authenticatie", "Proces waarbij gebruikers zich identificeren"),
            ("type", "document", "Soort schriftelijk stuk"),
            ("resultaat", "besluit", "Uitkomst van een beoordelingsproces"),
            ("exemplaar", "contract", "Specifiek exemplaar van een overeenkomst"),
        ]

        for category, begrip, _expected_context in test_cases:
            request = GenerationRequest(
                id="test-001",
                begrip=begrip,
                ontologische_categorie=category,
                context="Test context",
                actor="test_user",
                legal_basis="legitimate_interest",
            )

            result = await self.prompt_service.build_generation_prompt(request)

            # Verificeer dat result correct is
            assert result.text is not None
            assert len(result.text) > 100  # Prompt should be substantial
            assert result.metadata["ontologische_categorie"] == category
            assert f"ontologische_{category}" in result.components_used

            # Verificeer dat prompt category-specifieke elementen bevat
            assert category in result.text.lower() or begrip in result.text.lower()

    @pytest.mark.asyncio
    async def test_orchestrator_v2_with_prompt_service_v2(self):
        """Test dat DefinitionOrchestratorV2 correct werkt met PromptServiceV2."""

        # Mock dependencies met async methods
        from unittest.mock import AsyncMock

        mock_ai_service = Mock()
        mock_ai_service.generate_definition = AsyncMock(
            return_value=Mock(text="Test definitie", model="gpt-4", tokens_used=50)
        )

        mock_cleaning_service = Mock()
        mock_cleaning_service.clean_definition = AsyncMock(
            return_value="Clean test definitie"
        )

        mock_validation_service = Mock()
        mock_validation_service.validate_definition = AsyncMock(
            return_value=Mock(is_valid=True, violations=[], suggestions=[])
        )

        mock_repository = Mock()
        mock_repository.save_definition = AsyncMock(return_value="def-123")

        # Mock monitoring met async methods
        from unittest.mock import AsyncMock

        mock_monitoring = Mock()
        mock_monitoring.start_generation = AsyncMock(return_value=None)
        mock_monitoring.complete_generation = AsyncMock(return_value=None)
        mock_monitoring.track_error = AsyncMock(return_value=None)

        # Create orchestrator with V2 prompt service
        orchestrator = DefinitionOrchestratorV2(
            prompt_service=self.prompt_service,
            ai_service=mock_ai_service,
            validation_service=mock_validation_service,
            enhancement_service=None,
            security_service=None,
            cleaning_service=mock_cleaning_service,
            repository=mock_repository,
            monitoring=mock_monitoring,
            feedback_engine=None,
        )

        # Test request with ontological category
        request = GenerationRequest(
            id="test-002",
            begrip="authenticatie",
            ontologische_categorie="proces",
            context="Beveiligingscontext",
            actor="test_user",
            legal_basis="legitimate_interest",
        )

        # Execute orchestration
        response = await orchestrator.create_definition(request)

        # Verify response
        assert response.success is True
        assert response.definition is not None
        assert response.definition.ontologische_categorie == "proces"

        # Verify that response contains ontological category info
        assert response.metadata.get("ontological_category") == "proces"

    def test_enriched_context_conversion(self):
        """Test conversie van GenerationRequest naar EnrichedContext."""

        request = GenerationRequest(
            id="test-003",
            begrip="toezicht",
            ontologische_categorie="proces",
            context="Juridische context, Compliance",
            actor="legal_user",
            legal_basis="legal_obligation",
        )

        enriched_context = self.prompt_service._convert_request_to_context(request)

        # Verify conversion
        assert enriched_context.metadata["ontologische_categorie"] == "proces"
        assert enriched_context.metadata["request_id"] == "test-003"
        assert enriched_context.metadata["actor"] == "legal_user"
        assert enriched_context.metadata["legal_basis"] == "legal_obligation"

        # Verify context structure
        assert "organisatorisch" in enriched_context.base_context
        assert "domein" in enriched_context.base_context
        assert enriched_context.base_context["organisatorisch"] == [
            "Juridische context, Compliance"
        ]
        assert enriched_context.base_context["domein"] == ["Rechtspraak"]

    @pytest.mark.asyncio
    async def test_category_specific_template_selection(self):
        """Test dat verschillende categories leiden tot verschillende prompts."""

        base_request_data = {
            "id": "test-004",
            "begrip": "test_begrip",
            "context": "Test context",
            # "domein": "Test domein"  # removed per US-043,
            "actor": "test_user",
            "legal_basis": "legitimate_interest",
        }

        # Test verschillende categories
        categories = ["proces", "type", "resultaat", "exemplaar"]
        prompts = {}

        for category in categories:
            request = GenerationRequest(
                ontologische_categorie=category, **base_request_data
            )

            result = await self.prompt_service.build_generation_prompt(request)
            prompts[category] = result.text

        # Verify dat verschillende categories verschillende prompts genereren
        unique_prompts = set(prompts.values())
        assert (
            len(unique_prompts) >= 2
        ), "Different categories should generate different prompts"

        # Verify dat elke prompt de category weergeeft
        for _category, prompt_text in prompts.items():
            # Elk prompt moet iets hebben dat specifiek is voor die category
            assert len(prompt_text) > 0
            # Deze test kan worden uitgebreid met meer specifieke checks

    @pytest.mark.asyncio
    async def test_fallback_when_no_category_provided(self):
        """Test dat service correct werkt zonder ontological category."""

        request = GenerationRequest(
            id="test-005",
            begrip="algemeen_begrip",
            ontologische_categorie=None,  # Geen category
            context="Test context",
            actor="test_user",
            legal_basis="legitimate_interest",
        )

        result = await self.prompt_service.build_generation_prompt(request)

        # Verify dat service nog steeds werkt
        assert result.text is not None
        assert len(result.text) > 100
        assert result.metadata["ontologische_categorie"] is None

        # Maar geen category-specifieke components
        category_components = [
            c for c in result.components_used if c.startswith("ontologische_")
        ]
        assert len(category_components) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
