"""
Eenvoudige integration test om te verifiëren dat de nieuwe services werken.
"""
import pytest
import os
from unittest.mock import patch, Mock

# Ensure new services are used
os.environ['USE_NEW_SERVICES'] = 'true'

from services import get_definition_service
from services.container import get_container


class TestSimpleIntegration:
    """Simpele tests om basic functionality te verifiëren."""

    def test_new_services_enabled(self):
        """Verify nieuwe services zijn enabled."""
        service = get_definition_service()
        assert type(service).__name__ == 'ServiceAdapter'

    def test_container_exists(self):
        """Test dat container correct initialiseert."""
        container = get_container()
        assert container is not None
        assert hasattr(container, 'generator')
        assert hasattr(container, 'validator')
        assert hasattr(container, 'repository')
        assert hasattr(container, 'orchestrator')

    @pytest.mark.asyncio
    @patch('prompt_builder.stuur_prompt_naar_gpt')
    async def test_basic_generation(self, mock_gpt):
        """Test basic definitie generatie met nieuwe services."""
        # Setup
        mock_gpt.return_value = "Een test definitie voor integratie testing."

        service = get_definition_service()

        # Execute
        result = await service.generate_definition(
            begrip="test_begrip",
            context_dict={
                'organisatorisch': ['Test Org'],
                'domein': ['Test Domain']
            }
        )

        # Verify
        assert result['success'] is True
        assert 'definitie_gecorrigeerd' in result
        assert len(result['definitie_gecorrigeerd']) > 0

    @pytest.mark.asyncio
    async def test_service_stats(self):
        """Test dat stats werken."""
        service = get_definition_service()
        stats = service.get_stats()

        assert isinstance(stats, dict)
        assert 'generator' in stats
        assert 'validator' in stats
        assert 'repository' in stats
        assert 'orchestrator' in stats

    @pytest.mark.asyncio
    @patch('prompt_builder.stuur_prompt_naar_gpt')
    async def test_error_handling(self, mock_gpt):
        """Test error handling in nieuwe services."""
        # Setup - simulate error
        mock_gpt.side_effect = Exception("Test API Error")

        service = get_definition_service()

        # Execute
        result = await service.generate_definition(
            begrip="error_test",
            context_dict={}
        )

        # Verify - should handle error gracefully
        assert result['success'] is False
        assert 'error' in str(result).lower() or 'error_message' in result

    def test_legacy_disabled(self):
        """Verify legacy service is NOT used when flag is set."""
        os.environ['USE_NEW_SERVICES'] = 'true'
        service = get_definition_service()

        # Should NOT be legacy service
        assert 'UnifiedDefinitionService' not in type(service).__name__
        assert type(service).__name__ == 'ServiceAdapter'


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
