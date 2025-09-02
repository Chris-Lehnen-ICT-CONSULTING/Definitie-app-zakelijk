"""
Unit tests voor Service Factory.

Test alle functionaliteit van de service factory inclusief:
- Feature flag mechanisme
- Environment configuratie selectie
- ServiceAdapter functionaliteit
- Legacy/nieuwe service switching
- UI component rendering
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import os
import asyncio

from services.service_factory import (
    get_definition_service,
    _get_environment_config,
    ServiceAdapter,
    render_feature_flag_toggle
)
from services.container import ServiceContainer, ContainerConfigs
from services.interfaces import GenerationRequest, DefinitionResponse, Definition, ValidationResult


@pytest.fixture
def mock_container():
    """Mock ServiceContainer voor tests."""
    container = Mock(spec=ServiceContainer)

    # Mock services
    container.generator.return_value = Mock()
    container.validator.return_value = Mock()
    container.repository.return_value = Mock()
    container.orchestrator.return_value = Mock()

    return container


@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator met async methods."""
    orchestrator = AsyncMock()
    # get_stats is not async, so use regular Mock
    orchestrator.get_stats = Mock(return_value={'orchestrator_stats': 'data'})
    return orchestrator


@pytest.fixture
def service_adapter(mock_container, mock_orchestrator):
    """ServiceAdapter instance voor tests."""
    mock_container.orchestrator.return_value = mock_orchestrator
    return ServiceAdapter(mock_container)


class TestGetDefinitionService:
    """Test suite voor get_definition_service functie."""

    def test_get_legacy_service_default(self):
        """Test dat legacy service standaard wordt gebruikt."""
        with patch('services.service_factory.st') as mock_st, \
             patch('services.unified_definition_service_v2.UnifiedDefinitionService') as mock_legacy:

            # Setup - geen feature flag
            mock_st.session_state.get.return_value = False
            mock_legacy_instance = Mock()
            mock_legacy.get_instance.return_value = mock_legacy_instance

            # Execute
            result = get_definition_service()

            # Verify
            assert result == mock_legacy_instance
            mock_legacy.get_instance.assert_called_once()

    def test_get_new_services_with_streamlit_flag(self):
        """Test nieuwe services met Streamlit session state flag."""
        with patch('services.service_factory.st') as mock_st, \
             patch('services.service_factory.get_container') as mock_get_container, \
             patch('services.service_factory._get_environment_config') as mock_config:

            # Setup
            mock_st.session_state.get.return_value = True  # Feature flag ON
            mock_config.return_value = {'test': 'config'}
            mock_container = Mock()
            mock_get_container.return_value = mock_container

            # Execute
            result = get_definition_service()

            # Verify
            assert isinstance(result, ServiceAdapter)
            mock_config.assert_called_once()
            mock_get_container.assert_called_once_with({'test': 'config'})

    def test_get_new_services_with_env_var(self):
        """Test nieuwe services met environment variable (buiten Streamlit)."""
        with patch('services.service_factory.st') as mock_st, \
             patch('services.service_factory.get_container') as mock_get_container, \
             patch.dict(os.environ, {'USE_NEW_SERVICES': 'true'}):

            # Setup - Streamlit niet beschikbaar
            mock_st.session_state.get.side_effect = Exception("No Streamlit")
            mock_container = Mock()
            mock_get_container.return_value = mock_container

            # Execute
            result = get_definition_service()

            # Verify
            assert isinstance(result, ServiceAdapter)
            mock_get_container.assert_called_once()

    def test_get_service_with_custom_config(self):
        """Test service met custom container configuratie."""
        with patch('services.service_factory.st') as mock_st, \
             patch('services.service_factory.get_container') as mock_get_container:

            # Setup
            mock_st.session_state.get.return_value = True
            custom_config = {'custom': 'config'}
            mock_container = Mock()
            mock_get_container.return_value = mock_container

            # Execute
            result = get_definition_service(use_container_config=custom_config)

            # Verify
            assert isinstance(result, ServiceAdapter)
            mock_get_container.assert_called_once_with(custom_config)

    def test_fallback_to_legacy_on_error(self):
        """Test fallback naar legacy bij env var false."""
        with patch('services.service_factory.st') as mock_st, \
             patch('services.unified_definition_service_v2.UnifiedDefinitionService') as mock_legacy, \
             patch.dict(os.environ, {'USE_NEW_SERVICES': 'false'}):

            # Setup
            mock_st.session_state.get.side_effect = Exception("No Streamlit")
            mock_legacy_instance = Mock()
            mock_legacy.get_instance.return_value = mock_legacy_instance

            # Execute
            result = get_definition_service()

            # Verify
            assert result == mock_legacy_instance


class TestGetEnvironmentConfig:
    """Test suite voor _get_environment_config functie."""

    def test_development_config(self):
        """Test development environment configuratie."""
        with patch.dict(os.environ, {'APP_ENV': 'development'}), \
             patch('services.service_factory.ContainerConfigs') as mock_configs:

            mock_configs.development.return_value = {'env': 'dev'}

            # Execute
            result = _get_environment_config()

            # Verify
            assert result == {'env': 'dev'}
            mock_configs.development.assert_called_once()

    def test_testing_config(self):
        """Test testing environment configuratie."""
        with patch.dict(os.environ, {'APP_ENV': 'testing'}), \
             patch('services.service_factory.ContainerConfigs') as mock_configs:

            mock_configs.testing.return_value = {'env': 'test'}

            # Execute
            result = _get_environment_config()

            # Verify
            assert result == {'env': 'test'}
            mock_configs.testing.assert_called_once()

    def test_production_config_default(self):
        """Test production als default configuratie."""
        with patch.dict(os.environ, {'APP_ENV': 'production'}), \
             patch('services.service_factory.ContainerConfigs') as mock_configs:

            mock_configs.production.return_value = {'env': 'prod'}

            # Execute
            result = _get_environment_config()

            # Verify
            assert result == {'env': 'prod'}
            mock_configs.production.assert_called_once()

    def test_production_config_no_env(self):
        """Test production als default zonder APP_ENV."""
        with patch.dict(os.environ, {}, clear=True), \
             patch('services.service_factory.ContainerConfigs') as mock_configs:

            mock_configs.production.return_value = {'env': 'prod'}

            # Execute
            result = _get_environment_config()

            # Verify
            assert result == {'env': 'prod'}
            mock_configs.production.assert_called_once()

    def test_unknown_environment_defaults_to_production(self):
        """Test onbekende environment valt terug op production."""
        with patch.dict(os.environ, {'APP_ENV': 'staging'}), \
             patch('services.service_factory.ContainerConfigs') as mock_configs:

            mock_configs.production.return_value = {'env': 'prod'}

            # Execute
            result = _get_environment_config()

            # Verify
            assert result == {'env': 'prod'}
            mock_configs.production.assert_called_once()


class TestServiceAdapter:
    """Test suite voor ServiceAdapter klasse."""

    def test_initialization(self, mock_container, mock_orchestrator):
        """Test adapter initialisatie."""
        # Setup
        mock_container.orchestrator.return_value = mock_orchestrator

        # Execute
        adapter = ServiceAdapter(mock_container)

        # Verify
        assert adapter.container == mock_container
        assert adapter.orchestrator == mock_orchestrator
        mock_container.orchestrator.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_definition_success(self, service_adapter, mock_orchestrator):
        """Test succesvolle definitie generatie via adapter."""
        # Setup
        mock_definition = Definition(
            begrip="Test",
            definitie="Test definitie",
            voorbeelden=["Voorbeeld 1"],
            metadata={
                'origineel': 'Test definitie origineel',
                'marker': '✅',
                'processing_time': 1.5
            }
        )

        mock_validation = ValidationResult(
            is_valid=True,
            score=0.95,
            errors=['Minor issue']
        )

        mock_response = DefinitionResponse(
            success=True,
            definition=mock_definition,
            validation=mock_validation,
            message="Success"
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute
        result = await service_adapter.generate_definition(
            begrip="Test",
            context_dict={
                'organisatorisch': ['Org context'],
                'domein': ['Test domein']
            },
            organisatie='Test Org',
            extra_instructies='Extra info'
        )

        # Verify
        assert result['success'] is True
        assert result['definitie_gecorrigeerd'] == "Test definitie"
        assert result['definitie_origineel'] == "Test definitie origineel"
        assert result['marker'] == '✅'
        assert result['toetsresultaten'] == ['Minor issue']
        assert result['validation_score'] == 0.95
        assert result['voorbeelden'] == ["Voorbeeld 1"]
        assert result['processing_time'] == 1.5

        # Verify request creation
        call_args = mock_orchestrator.create_definition.call_args[0][0]
        assert isinstance(call_args, GenerationRequest)
        assert call_args.begrip == "Test"
        assert call_args.context == "Org context"
        assert call_args.domein == "Test domein"
        assert call_args.organisatie == "Test Org"
        assert call_args.extra_instructies == "Extra info"

    @pytest.mark.asyncio
    async def test_generate_definition_failure(self, service_adapter, mock_orchestrator):
        """Test gefaalde definitie generatie via adapter."""
        # Setup
        mock_response = DefinitionResponse(
            success=False,
            definition=None,
            validation=None,
            message="Generation failed due to API error"
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute
        result = await service_adapter.generate_definition(
            begrip="Test",
            context_dict={}
        )

        # Verify
        assert result['success'] is False
        assert result['error_message'] == "Generation failed due to API error"

    @pytest.mark.asyncio
    async def test_generate_definition_no_message(self, service_adapter, mock_orchestrator):
        """Test generatie failure zonder message."""
        # Setup
        mock_response = DefinitionResponse(
            success=False,
            definition=None,
            validation=None,
            message=None  # No message
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute
        result = await service_adapter.generate_definition(
            begrip="Test",
            context_dict={}
        )

        # Verify
        assert result['error_message'] == "Generatie mislukt"

    @pytest.mark.asyncio
    async def test_generate_definition_empty_context(self, service_adapter, mock_orchestrator):
        """Test generatie met lege context."""
        # Setup
        mock_response = DefinitionResponse(
            success=True,
            definition=Definition(begrip="Test", definitie="Test def"),
            validation=None
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute
        result = await service_adapter.generate_definition(
            begrip="Test",
            context_dict={}  # Empty context
        )

        # Verify request has empty strings
        call_args = mock_orchestrator.create_definition.call_args[0][0]
        assert call_args.context == ""
        assert call_args.domein == ""
        assert call_args.organisatie == ""

    def test_get_stats(self, service_adapter, mock_container, mock_orchestrator):
        """Test get_stats methode."""
        # Setup mocks for each service
        mock_gen = Mock()
        mock_val = Mock()
        mock_repo = Mock()

        mock_gen.get_stats.return_value = {'gen': 'stats'}
        mock_val.get_stats.return_value = {'val': 'stats'}
        mock_repo.get_stats.return_value = {'repo': 'stats'}
        # mock_orchestrator.get_stats is already configured in the fixture

        # Configure container to return these mocks
        mock_container.generator.return_value = mock_gen
        mock_container.validator.return_value = mock_val
        mock_container.repository.return_value = mock_repo

        # Reinitialize adapter to use updated mocks
        adapter = ServiceAdapter(mock_container)

        # Execute
        stats = adapter.get_stats()

        # Verify
        assert stats['generator'] == {'gen': 'stats'}
        assert stats['validator'] == {'val': 'stats'}
        assert stats['repository'] == {'repo': 'stats'}
        assert stats['orchestrator'] == {'orchestrator_stats': 'data'}

        # Verify all services were called
        mock_container.generator.assert_called()
        mock_container.validator.assert_called()
        mock_container.repository.assert_called()


class TestRenderFeatureFlagToggle:
    """Test suite voor render_feature_flag_toggle UI component."""

    def test_render_toggle_default_state(self):
        """Test rendering met default state."""
        with patch('services.service_factory.st') as mock_st:
            # Setup mocks
            mock_sidebar = Mock()
            mock_st.sidebar = mock_sidebar
            mock_st.session_state.get.return_value = False
            mock_st.checkbox.return_value = False

            # Setup sidebar context manager
            mock_sidebar.__enter__ = Mock(return_value=mock_st)
            mock_sidebar.__exit__ = Mock(return_value=None)

            # Execute
            result = render_feature_flag_toggle()

            # Verify
            assert result is False
            mock_st.checkbox.assert_called_once()
            assert 'Gebruik nieuwe services' in mock_st.checkbox.call_args[0][0]
            assert mock_st.checkbox.call_args[1]['value'] is False

    def test_render_toggle_enabled_state(self):
        """Test rendering met enabled nieuwe services."""
        with patch('services.service_factory.st') as mock_st:
            # Setup
            mock_st.session_state.get.return_value = True
            mock_st.checkbox.return_value = True
            mock_st.selectbox.return_value = 'production'

            # Execute
            result = render_feature_flag_toggle()

            # Verify
            assert result is True
            mock_st.info.assert_called_once_with("🚀 Nieuwe services actief!")
            mock_st.selectbox.assert_called_once()

            # Verify environment selector
            selectbox_args = mock_st.selectbox.call_args[0]
            assert selectbox_args[0] == "Environment"
            assert selectbox_args[1] == ["production", "development", "testing"]

    def test_render_toggle_development_warning(self):
        """Test development environment warning."""
        with patch('services.service_factory.st') as mock_st:
            # Setup
            mock_st.checkbox.return_value = True
            mock_st.selectbox.return_value = 'development'

            # Execute
            result = render_feature_flag_toggle()

            # Verify warning
            mock_st.warning.assert_called_once_with("⚠️ Development mode actief")

    def test_render_toggle_testing_warning(self):
        """Test testing environment warning."""
        with patch('services.service_factory.st') as mock_st:
            # Setup
            mock_st.checkbox.return_value = True
            mock_st.selectbox.return_value = 'testing'

            # Execute
            result = render_feature_flag_toggle()

            # Verify warning
            mock_st.warning.assert_called_once_with("⚠️ Testing mode actief")

    def test_render_toggle_ui_structure(self):
        """Test UI structuur van de toggle."""
        with patch('services.service_factory.st') as mock_st:
            # Setup
            mock_st.checkbox.return_value = False
            mock_sidebar = Mock()
            mock_st.sidebar = mock_sidebar

            # Setup sidebar context manager
            mock_sidebar.__enter__ = Mock(return_value=mock_sidebar)
            mock_sidebar.__exit__ = Mock(return_value=None)

            # Execute
            render_feature_flag_toggle()

            # Verify sidebar was used as context manager
            mock_sidebar.__enter__.assert_called_once()
            mock_sidebar.__exit__.assert_called_once()

            # Verify markdown calls were made
            # Note: Because of the context manager, we can't easily verify the exact calls


class TestIntegrationScenarios:
    """Integration test scenarios voor service factory."""

    def test_full_flow_legacy_to_new_switch(self):
        """Test complete flow van legacy naar nieuwe services."""
        with patch('services.service_factory.st') as mock_st, \
             patch('services.unified_definition_service_v2.UnifiedDefinitionService') as mock_legacy, \
             patch('services.service_factory.get_container') as mock_get_container:

            # Start met legacy
            mock_st.session_state.get.return_value = False
            legacy_instance = Mock()
            mock_legacy.get_instance.return_value = legacy_instance

            service1 = get_definition_service()
            assert service1 == legacy_instance

            # Switch naar nieuwe services
            mock_st.session_state.get.return_value = True
            mock_container = Mock()
            mock_get_container.return_value = mock_container

            service2 = get_definition_service()
            assert isinstance(service2, ServiceAdapter)
            assert service2.container == mock_container

    @pytest.mark.asyncio
    async def test_adapter_with_real_interfaces(self):
        """Test adapter met echte interface objecten."""
        # Create real objects
        container = Mock(spec=ServiceContainer)
        orchestrator = AsyncMock()
        container.orchestrator.return_value = orchestrator

        adapter = ServiceAdapter(container)

        # Create complex response
        definition = Definition(
            begrip="Complex",
            definitie="Complex definitie",
            voorbeelden=["V1", "V2"],
            synoniemen=["Syn1"],
            metadata={'complex': True}
        )

        validation = ValidationResult(
            is_valid=True,
            score=0.85,
            errors=['Error1', 'Error2'],
            suggestions=['Sug1']
        )

        response = DefinitionResponse(
            success=True,
            definition=definition,
            validation=validation,
            message="Complex success"
        )

        orchestrator.create_definition.return_value = response

        # Execute
        result = await adapter.generate_definition(
            begrip="Complex",
            context_dict={
                'organisatorisch': ['O1', 'O2'],
                'juridisch': ['J1'],
                'domein': ['D1', 'D2', 'D3']
            }
        )

        # Verify complex mapping
        assert result['success'] is True
        assert result['definitie_gecorrigeerd'] == "Complex definitie"
        assert result['voorbeelden'] == ["V1", "V2"]
        assert result['validation_score'] == 0.85
        assert result['toetsresultaten'] == ['Error1', 'Error2']
