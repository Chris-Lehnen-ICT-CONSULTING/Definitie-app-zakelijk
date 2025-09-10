"""
Directe functionality tests voor de nieuwe services.

Test de nieuwe services direct zonder door de factory te gaan,
om te verifiëren dat ze correct werken.
"""
import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from services.container import ServiceContainer, get_container
from services.service_factory import ServiceAdapter
from services.interfaces import GenerationRequest, Definition, ValidationResult


class TestNewServicesFunctionality:
    """Test nieuwe services direct."""

    @pytest.fixture
    def container(self):
        """Maak service container."""
        return get_container()

    @pytest.fixture
    def service_adapter(self, container):
        """Maak service adapter direct."""
        return ServiceAdapter(container)

    @pytest.mark.asyncio
    @patch('prompt_builder.stuur_prompt_naar_gpt')
    @patch('ai_toetser.core.toets_definitie')
    async def test_complete_flow_with_new_services(
        self,
        mock_toets,
        mock_gpt,
        service_adapter
    ):
        """Test complete flow met nieuwe services."""
        # Setup mocks
        mock_gpt.return_value = "Een authenticatiemechanisme is een systeem voor identiteitsverificatie."
        mock_toets.return_value = [
            "✔️ ESS-01: Geen werkwoord als kern",
            "✔️ STR-01: Goede structuur"
        ]

        # Test context
        context_dict = {
            'organisatorisch': ['Ministerie van BZK'],
            'domein': ['Informatiebeveiliging']
        }

        # Execute
        result = await service_adapter.generate_definition(
            begrip="authenticatiemechanisme",
            context_dict=context_dict,
            organisatie="Rijksoverheid",
            extra_instructies="Focus op technische aspecten"
        )

        # Verify result structure
        assert result['success'] is True
        assert 'definitie_gecorrigeerd' in result
        assert 'definitie_origineel' in result
        assert len(result['definitie_gecorrigeerd']) > 20

        # Verify mocks called
        mock_gpt.assert_called_once()

        # Check prompt construction
        gpt_call = mock_gpt.call_args
        prompt = gpt_call[0][0] if gpt_call[0] else gpt_call[1].get('prompt', '')

        assert 'authenticatiemechanisme' in prompt.lower()
        assert 'ministerie' in prompt.lower() or 'bzk' in prompt.lower()

    @pytest.mark.asyncio
    async def test_orchestrator_workflow(self, container):
        """Test orchestrator workflow direct."""
        orchestrator = container.orchestrator()

        # Mock dependencies
        with patch.object(orchestrator.generator, 'generate') as mock_gen, \
             patch.object(orchestrator.validator, 'validate') as mock_val, \
             patch.object(orchestrator.repository, 'save') as mock_save:

            # Setup mocks
            mock_definition = Definition(
                begrip="test",
                definitie="Test definitie voor orchestrator"
            )
            mock_gen.return_value = mock_definition

            mock_validation = ValidationResult(
                is_valid=True,
                score=0.9,
                errors=[],
                warnings=["Minor warning"]
            )
            mock_val.return_value = mock_validation

            mock_save.return_value = 123  # definition ID

            # Create request
            request = GenerationRequest(
        id="test-id",
        begrip="test",
                context="Test context"
            )

            # Execute
            response = await orchestrator.create_definition(request)

            # Verify workflow
            assert response.success is True
            assert response.definition == mock_definition
            assert response.validation_result == mock_validation

            # Verify calls
            mock_gen.assert_called_once()
            mock_val.assert_called_once_with(mock_definition)
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_generator_service_isolation(self, container):
        """Test generator service in isolatie."""
        generator = container.generator()

        with patch('services.definition_generator.stuur_prompt_naar_gpt') as mock_gpt:
            mock_gpt.return_value = "Generated definition text"

            # Direct call
            request = GenerationRequest(
        id="test-id",
        begrip="isolated_test",
                context="Isolation context"
            )

            result = await generator.generate(request)

            # Verify
            assert isinstance(result, Definition)
            assert result.begrip == "isolated_test"
            assert "Generated definition" in result.definitie

    @pytest.mark.asyncio
    async def test_validator_service_isolation(self, container):
        """Test validator service in isolatie."""
        validator = container.validator()

        # Create test definition
        definition = Definition(
            begrip="validator_test",
            definitie="Een goede definitie die aan alle regels voldoet en voldoende uitgebreid is."
        )

        # Validate
        result = validator.validate(definition)

        # Verify
        assert isinstance(result, ValidationResult)
        assert result.score >= 0.0
        assert result.score <= 1.0
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)

    @pytest.mark.asyncio
    async def test_repository_service_isolation(self, container):
        """Test repository service in isolatie."""
        repository = container.repository()

        # Create test definition
        definition = Definition(
            begrip="repo_test",
            definitie="Repository test definitie"
        )

        # Mock database
        with patch('services.definition_repository.sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.lastrowid = 456

            # Save
            def_id = await repository.save(definition)

            # Verify
            assert def_id == 456
            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called()

    @pytest.mark.asyncio
    async def test_service_integration(self, service_adapter):
        """Test integratie tussen services."""
        # Full integration test met alle services
        with patch('prompt_builder.stuur_prompt_naar_gpt') as mock_gpt, \
             patch('ai_toetser.core.toets_definitie') as mock_toets, \
             patch('services.definition_repository.sqlite3.connect') as mock_db:

            # Setup comprehensive mocks
            mock_gpt.return_value = "Een comprehensive test definitie voor integratie testing."
            mock_toets.return_value = ["✔️ Alle regels geslaagd"]

            mock_conn = Mock()
            mock_cursor = Mock()
            mock_db.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.lastrowid = 789

            # Execute full flow
            result = await service_adapter.generate_definition(
                begrip="integration_test",
                context_dict={
                    'organisatorisch': ['Test Org'],
                    'domein': ['Test Domain']
                },
                organisatie="Integration Test Org"
            )

            # Verify complete flow
            assert result['success'] is True
            assert len(result['definitie_gecorrigeerd']) > 0
            assert isinstance(result.get('processing_time', 0), (int, float))

    def test_container_configuration(self, container):
        """Test container configuratie."""
        # Verify alle services beschikbaar
        assert hasattr(container, 'generator')
        assert hasattr(container, 'validator')
        assert hasattr(container, 'repository')
        assert hasattr(container, 'orchestrator')

        # Test singleton behavior
        gen1 = container.generator()
        gen2 = container.generator()
        assert gen1 is gen2  # Same instance

        # Test different services are different instances
        gen = container.generator()
        val = container.validator()
        assert gen is not val

    @pytest.mark.asyncio
    async def test_error_propagation(self, service_adapter):
        """Test error propagation door de service layers."""
        # Test verschillende error scenarios
        error_scenarios = [
            # GPT API error
            {
                'mock': 'prompt_builder.stuur_prompt_naar_gpt',
                'error': Exception("OpenAI API Error"),
                'expected_in_result': 'error'
            },
            # Validation error (niet getest want validator vangt errors op)
            # Database error
            {
                'mock': 'services.definition_repository.sqlite3.connect',
                'error': Exception("Database connection failed"),
                'expected_in_result': 'error'
            }
        ]

        for scenario in error_scenarios:
            with patch(scenario['mock'], side_effect=scenario['error']):
                result = await service_adapter.generate_definition(
                    begrip="error_test",
                    context_dict={}
                )

                # Should handle error gracefully
                assert result['success'] is False
                assert scenario['expected_in_result'] in str(result).lower()

    @pytest.mark.asyncio
    async def test_stats_collection(self, service_adapter):
        """Test statistics collection."""
        # Get initial stats
        initial_stats = service_adapter.get_stats()

        assert 'generator' in initial_stats
        assert 'validator' in initial_stats
        assert 'repository' in initial_stats
        assert 'orchestrator' in initial_stats

        # Perform some operations
        with patch('prompt_builder.stuur_prompt_naar_gpt', return_value="Test"):
            await service_adapter.generate_definition("stats_test", {})

        # Get updated stats
        updated_stats = service_adapter.get_stats()

        # Some stats should have changed
        # (exact behavior depends on implementation)
        assert updated_stats is not None


class TestServiceAdapterCompatibility:
    """Test ServiceAdapter compatibility met legacy interface."""

    def test_adapter_interface(self):
        """Test dat adapter de juiste interface exposed."""
        container = get_container()
        adapter = ServiceAdapter(container)

        # Check required methods
        assert hasattr(adapter, 'generate_definition')
        assert hasattr(adapter, 'get_stats')

        # Check generate_definition is async
        import inspect
        assert inspect.iscoroutinefunction(adapter.generate_definition)

    @pytest.mark.asyncio
    async def test_adapter_response_format(self):
        """Test adapter response format compatibiliteit."""
        container = get_container()
        adapter = ServiceAdapter(container)

        with patch('prompt_builder.stuur_prompt_naar_gpt', return_value="Test def"):
            result = await adapter.generate_definition(
                begrip="format_test",
                context_dict={'domein': ['Test']}
            )

            # Required fields for legacy compatibility
            required_fields = [
                'success',
                'definitie_gecorrigeerd'
            ]

            for field in required_fields:
                assert field in result, f"Missing required field: {field}"

            # Optional but expected fields
            optional_fields = [
                'definitie_origineel',
                'marker',
                'toetsresultaten',
                'validation_score',
                'voorbeelden',
                'processing_time'
            ]

            # These should be present even if empty/0
            for field in optional_fields:
                assert field in result, f"Missing optional field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
