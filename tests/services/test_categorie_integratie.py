"""
Test suite voor ontologische categorie integratie.

Test de volledige flow van categorie bepaling tot prompt generatie.
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.definition_generator_prompts import BasicPromptBuilder
from services.interfaces import Definition, GenerationRequest
from services.service_factory import ServiceAdapter


class TestCategorieIntegratie:
    """Test ontologische categorie integratie in services."""

    def test_generation_request_heeft_categorie_veld(self):
        """Test dat GenerationRequest categorie veld heeft."""
        request = GenerationRequest(
            begrip="verificatie", context="OM", ontologische_categorie="proces"
        )

        assert hasattr(request, "ontologische_categorie")
        assert request.ontologische_categorie == "proces"

    def test_service_adapter_extraheert_categorie_uit_kwargs(self):
        """Test dat ServiceAdapter categorie uit kwargs haalt."""
        from domain.ontological_categories import OntologischeCategorie
        from services.container import get_container

        container = get_container()
        adapter = ServiceAdapter(container)

        # Mock de orchestrator create_definition methode (async)
        with patch.object(adapter.orchestrator, "create_definition") as mock_create:
            mock_response = Mock()
            mock_response.success = True
            mock_response.definition = Mock()
            mock_response.definition.definitie = "Test definitie"
            mock_response.definition.metadata = {}
            mock_response.validation = None

            # Make it return a coroutine that resolves to mock_response
            async def mock_coroutine(*args, **kwargs):
                return mock_response

            mock_create.side_effect = mock_coroutine

            # Test met OntologischeCategorie enum
            categorie_enum = OntologischeCategorie.PROCES
            result = adapter.generate_definition(
                begrip="verificatie",
                context_dict={"organisatorisch": ["OM"]},
                categorie=categorie_enum,
            )

            # Verifieer dat create_definition werd aangeroepen
            assert mock_create.called
            args = mock_create.call_args[0]
            request = args[0]

            # Check dat categorie correct werd doorgegeven
            assert request.ontologische_categorie == "proces"

    def test_service_adapter_extraheert_categorie_uit_string(self):
        """Test dat ServiceAdapter ook string categorieën accepteert."""
        from services.container import get_container

        container = get_container()
        adapter = ServiceAdapter(container)

        with patch.object(adapter.orchestrator, "create_definition") as mock_create:
            mock_response = Mock()
            mock_response.success = True
            mock_response.definition = Mock()
            mock_response.definition.definitie = "Test definitie"
            mock_response.definition.metadata = {}
            mock_response.validation = None

            # Make it return a coroutine that resolves to mock_response
            async def mock_coroutine(*args, **kwargs):
                return mock_response

            mock_create.side_effect = mock_coroutine

            # Test met string categorie
            result = adapter.generate_definition(
                begrip="verificatie",
                context_dict={"organisatorisch": ["OM"]},
                categorie="resultaat",
            )

            args = mock_create.call_args[0]
            request = args[0]

            assert request.ontologische_categorie == "resultaat"

    def test_basic_prompt_builder_selecteert_ontologie_template(self):
        """Test dat BasicPromptBuilder ontologische templates selecteert."""
        builder = BasicPromptBuilder()
        config = UnifiedGeneratorConfig()

        # Test voor elke ontologische categorie
        test_cases = [
            ("proces", "ontologie_proces"),
            ("type", "ontologie_type"),
            ("resultaat", "ontologie_resultaat"),
            ("exemplaar", "ontologie_exemplaar"),
        ]

        for categorie, expected_template in test_cases:
            context = EnrichedContext(
                base_context={"organisatorisch": ["OM"]},
                sources=[],
                expanded_terms={},
                confidence_scores={},
                metadata={"ontologische_categorie": categorie},
            )

            # Test template selectie
            template = builder._select_template("verificatie", context)
            assert (
                template.name == expected_template
            ), f"Verwachtte {expected_template}, kreeg {template.name}"

    def test_ontologie_templates_bevatten_juiste_instructies(self):
        """Test dat ontologische templates de juiste instructies bevatten."""
        builder = BasicPromptBuilder()

        # Test proces template
        proces_template = builder.templates["ontologie_proces"]
        assert "PROCES" in proces_template.template
        assert "is een activiteit waarbij" in proces_template.template

        # Test type template
        type_template = builder.templates["ontologie_type"]
        assert "TYPE" in type_template.template
        assert "is een soort/type" in type_template.template

        # Test resultaat template
        resultaat_template = builder.templates["ontologie_resultaat"]
        assert "RESULTAAT" in resultaat_template.template
        assert "is het resultaat van" in resultaat_template.template

        # Test exemplaar template
        exemplaar_template = builder.templates["ontologie_exemplaar"]
        assert "EXEMPLAAR" in exemplaar_template.template
        assert "is een exemplaar van" in exemplaar_template.template

    def test_prompt_building_met_ontologische_categorie(self):
        """Test volledige prompt building met ontologische categorie."""
        builder = BasicPromptBuilder()
        config = UnifiedGeneratorConfig()

        context = EnrichedContext(
            base_context={
                "organisatorisch": ["OM"],
                "juridisch": ["Wetboek van Strafrecht"],
            },
            sources=[],
            expanded_terms={},
            confidence_scores={},
            metadata={"ontologische_categorie": "proces"},
        )

        prompt = builder.build_prompt("verificatie", context, config)

        # Verify prompt bevat ontologische instructies
        assert "PROCES" in prompt
        assert "verificatie" in prompt
        assert "is een activiteit waarbij" in prompt

    def test_fallback_naar_default_template_zonder_categorie(self):
        """Test dat zonder categorie wordt teruggevallen op default template."""
        builder = BasicPromptBuilder()
        config = UnifiedGeneratorConfig()

        context = EnrichedContext(
            base_context={"organisatorisch": ["OM"]},
            sources=[],
            expanded_terms={},
            confidence_scores={},
            metadata={},  # Geen ontologische_categorie
        )

        template = builder._select_template("verificatie", context)
        assert template.name == "default"

    def test_complete_integration_flow_mock(self):
        """Test complete flow met mocks om asyncio.run te vermijden."""
        from domain.ontological_categories import OntologischeCategorie
        from services.container import get_container

        container = get_container()
        adapter = ServiceAdapter(container)

        # Mock het complete orchestrator gedrag
        with patch.object(adapter.orchestrator, "create_definition") as mock_create:
            # Mock response
            mock_response = Mock()
            mock_response.success = True
            mock_response.definition = Mock()
            mock_response.definition.definitie = "Verificatie is een activiteit waarbij de juistheid wordt gecontroleerd."
            mock_response.definition.metadata = {}
            mock_response.validation = None

            # Make it return a coroutine that resolves to mock_response
            async def mock_coroutine(*args, **kwargs):
                return mock_response

            mock_create.side_effect = mock_coroutine

            # Test complete flow
            result = adapter.generate_definition(
                begrip="verificatie",
                context_dict={
                    "organisatorisch": ["OM"],
                    "juridisch": ["Wetboek van Strafrecht"],
                },
                categorie=OntologischeCategorie.PROCES,
            )

            # Verify result
            assert result.success
            assert "verificatie" in result.final_definitie.lower()

            # Verify orchestrator werd aangeroepen met juiste categorie
            assert mock_create.called
            args = mock_create.call_args[0]
            request = args[0]
            assert request.ontologische_categorie == "proces"


class TestCategorieTemplateFormatting:
    """Test template formatting voor verschillende categorieën."""

    def test_proces_template_formatting(self):
        """Test proces template formatting."""
        builder = BasicPromptBuilder()
        template = builder.templates["ontologie_proces"]

        formatted = template.format(
            begrip="verificatie",
            context_section="Organisatorisch: OM\nJuridisch: Wetboek van Strafrecht",
        )

        assert "verificatie" in formatted
        assert "PROCES" in formatted
        assert "is een activiteit waarbij" in formatted

    def test_type_template_formatting(self):
        """Test type template formatting."""
        builder = BasicPromptBuilder()
        template = builder.templates["ontologie_type"]

        formatted = template.format(
            begrip="document", context_section="Organisatorisch: DJI"
        )

        assert "document" in formatted
        assert "TYPE" in formatted
        assert "is een soort/type" in formatted

    def test_resultaat_template_formatting(self):
        """Test resultaat template formatting."""
        builder = BasicPromptBuilder()
        template = builder.templates["ontologie_resultaat"]

        formatted = template.format(
            begrip="besluit", context_section="Organisatorisch: OM"
        )

        assert "besluit" in formatted
        assert "RESULTAAT" in formatted
        assert "is het resultaat van" in formatted

    def test_exemplaar_template_formatting(self):
        """Test exemplaar template formatting."""
        builder = BasicPromptBuilder()
        template = builder.templates["ontologie_exemplaar"]

        formatted = template.format(
            begrip="specifiek geval", context_section="Context beschrijving"
        )

        assert "specifiek geval" in formatted
        assert "EXEMPLAAR" in formatted
        assert "is een exemplaar van" in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
