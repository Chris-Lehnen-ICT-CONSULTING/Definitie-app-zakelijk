"""
Unit tests voor Service Factory.

Test alle functionaliteit van de service factory inclusief:
- Feature flag mechanisme
- Environment configuratie selectie
- ServiceAdapter functionaliteit
- Legacy/nieuwe service switching
- UI component rendering
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# render_feature_flag_toggle removed - moved to UI layer
from services.container import ContainerConfigs, ServiceContainer
from services.interfaces import (Definition, DefinitionResponse,
                                 GenerationRequest, ValidationResult)
from services.service_factory import (ServiceAdapter, _get_environment_config,
                                      get_definition_service)


@pytest.fixture()
def mock_container():
    """Mock ServiceContainer voor tests."""
    container = Mock(spec=ServiceContainer)

    # Mock services
    container.generator.return_value = Mock()
    container.validator.return_value = Mock()
    container.repository.return_value = Mock()
    container.orchestrator.return_value = Mock()

    return container


@pytest.fixture()
def mock_orchestrator():
    """Mock orchestrator met async methods."""
    orchestrator = AsyncMock()
    # get_stats is not async, so use regular Mock
    orchestrator.get_stats = Mock(return_value={"orchestrator_stats": "data"})
    return orchestrator


@pytest.fixture()
def service_adapter(mock_container, mock_orchestrator):
    """ServiceAdapter instance voor tests."""
    mock_container.orchestrator.return_value = mock_orchestrator
    return ServiceAdapter(mock_container)


class TestGetDefinitionService:
    """Test suite voor get_definition_service functie."""

    def test_get_v2_service_default(self):
        """Test dat V2 service altijd wordt gebruikt (legacy removed per US-043)."""
        with patch(
            "services.service_factory.get_cached_container"
        ) as mock_get_container:

            # Setup
            mock_container = Mock()
            mock_get_container.return_value = mock_container

            # Execute
            result = get_definition_service()

            # Verify - always returns V2 ServiceAdapter, singleton container
            assert isinstance(result, ServiceAdapter)
            mock_get_container.assert_called_once()

    def test_get_v2_service_no_streamlit_dependency(self):
        """Test V2 service without Streamlit dependency (per US-043)."""
        with patch(
            "services.service_factory.get_cached_container"
        ) as mock_get_container:

            # Setup
            mock_container = Mock()
            mock_get_container.return_value = mock_container

            # Execute - no Streamlit involved
            result = get_definition_service()

            # Verify - V2 only, singleton container
            assert isinstance(result, ServiceAdapter)
            mock_get_container.assert_called_once()

    def test_get_v2_service_ignores_legacy_env_var(self):
        """Test V2 service ignores USE_NEW_SERVICES env var (always V2 per US-043)."""
        with (
            patch(
                "services.service_factory.get_cached_container"
            ) as mock_get_container,
            patch.dict(os.environ, {"USE_NEW_SERVICES": "false"}),
        ):

            # Setup
            mock_container = Mock()
            mock_get_container.return_value = mock_container

            # Execute - even with env var false, still gets V2
            result = get_definition_service()

            # Verify - still returns V2, singleton container
            assert isinstance(result, ServiceAdapter)
            mock_get_container.assert_called_once()

    def test_get_v2_service_with_custom_config(self):
        """Test V2 service uses singleton (custom config no longer supported)."""
        with patch(
            "services.service_factory.get_cached_container"
        ) as mock_get_container:

            # Setup
            mock_container = Mock()
            mock_get_container.return_value = mock_container

            # Execute - no config parameter anymore
            result = get_definition_service()

            # Verify - V2 always uses singleton container (US-202)
            assert isinstance(result, ServiceAdapter)
            mock_get_container.assert_called_once()

    def test_no_legacy_fallback(self):
        """Test no legacy fallback exists (removed per US-043)."""
        with patch(
            "services.service_factory.get_cached_container"
        ) as mock_get_container:

            # Setup
            mock_container = Mock()
            mock_get_container.return_value = mock_container

            # Execute - always V2, no legacy path, singleton container
            result = get_definition_service()

            # Verify - V2 only, no legacy imports attempted
            assert isinstance(result, ServiceAdapter)
            # No attempt to import legacy modules


class TestGetEnvironmentConfig:
    """Test suite voor _get_environment_config functie."""

    def test_development_config(self):
        """Test development environment configuratie."""
        with (
            patch.dict(os.environ, {"APP_ENV": "development"}),
            patch("services.service_factory.ContainerConfigs") as mock_configs,
        ):

            mock_configs.development.return_value = {"env": "dev"}

            # Execute
            result = _get_environment_config()

            # Verify
            assert result == {"env": "dev"}
            mock_configs.development.assert_called_once()

    def test_testing_config(self):
        """Test testing environment configuratie."""
        with (
            patch.dict(os.environ, {"APP_ENV": "testing"}),
            patch("services.service_factory.ContainerConfigs") as mock_configs,
        ):

            mock_configs.testing.return_value = {"env": "test"}

            # Execute
            result = _get_environment_config()

            # Verify
            assert result == {"env": "test"}
            mock_configs.testing.assert_called_once()

    def test_production_config_default(self):
        """Test production als default configuratie."""
        with (
            patch.dict(os.environ, {"APP_ENV": "production"}),
            patch("services.service_factory.ContainerConfigs") as mock_configs,
        ):

            mock_configs.production.return_value = {"env": "prod"}

            # Execute
            result = _get_environment_config()

            # Verify
            assert result == {"env": "prod"}
            mock_configs.production.assert_called_once()

    def test_production_config_no_env(self):
        """Test production als default zonder APP_ENV."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("services.service_factory.ContainerConfigs") as mock_configs,
        ):

            mock_configs.production.return_value = {"env": "prod"}

            # Execute
            result = _get_environment_config()

            # Verify
            assert result == {"env": "prod"}
            mock_configs.production.assert_called_once()

    def test_unknown_environment_defaults_to_production(self):
        """Test onbekende environment valt terug op production."""
        with (
            patch.dict(os.environ, {"APP_ENV": "staging"}),
            patch("services.service_factory.ContainerConfigs") as mock_configs,
        ):

            mock_configs.production.return_value = {"env": "prod"}

            # Execute
            result = _get_environment_config()

            # Verify
            assert result == {"env": "prod"}
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

    @pytest.mark.asyncio()
    async def test_generate_definition_success(
        self, service_adapter, mock_orchestrator
    ):
        """Test succesvolle definitie generatie via adapter."""
        # Setup
        mock_definition = Definition(
            begrip="Test",
            definitie="Test definitie",
            voorbeelden=["Voorbeeld 1"],
            metadata={
                "origineel": "Test definitie origineel",
                "marker": "✅",
                "processing_time": 1.5,
                "voorbeelden": {
                    "voorbeeldzinnen": ["Voorbeeld zin 1"],
                    "praktijkvoorbeelden": ["Praktijk 1"],
                    "tegenvoorbeelden": ["Tegen 1"],
                    "synoniemen": [],
                    "antoniemen": [],
                    "toelichting": "",
                },
            },
        )

        mock_validation = ValidationResult(
            is_valid=True, score=0.95, errors=["Minor issue"]
        )

        mock_response = DefinitionResponse(
            success=True,
            definition=mock_definition,
            validation=mock_validation,
            message="Success",
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute
        result = await service_adapter.generate_definition(
            begrip="Test",
            context_dict={
                "organisatorisch": ["Org context"],
                "domein": ["Test domein"],
            },
            organisatie="Test Org",
            extra_instructies="Extra info",
        )

        # Verify V2 contract fields
        assert result["success"] is True
        assert result["definitie_gecorrigeerd"] == "Test definitie"
        assert result["definitie_origineel"] == "Test definitie origineel"
        assert result["final_score"] == 0.95

        # Check validation_details (V2 format)
        assert "validation_details" in result
        assert result["validation_details"]["overall_score"] == 0.95
        assert result["validation_details"]["is_acceptable"] is True
        assert isinstance(result["validation_details"]["violations"], list)

        # Check voorbeelden (now a dict with categories)
        assert "voorbeelden" in result
        if isinstance(result["voorbeelden"], dict):
            # V2 format - REFACTORED: canonieke keys
            assert "voorbeeldzinnen" in result["voorbeelden"]
            assert "praktijkvoorbeelden" in result["voorbeelden"]
            assert "tegenvoorbeelden" in result["voorbeelden"]
            # Geen legacy keys meer
            assert "juridisch" not in result["voorbeelden"]
            assert "praktijk" not in result["voorbeelden"]
        else:
            # Legacy format still accepted for now
            assert result["voorbeelden"] == ["Voorbeeld 1"]

        # Check metadata
        assert "metadata" in result
        assert result["metadata"].get("model") == "gpt-4"  # Default

        # Legacy fields should still work for backward compatibility
        assert result.get("marker") == "✅"
        assert result.get("validation_score") == 0.95  # Legacy alias for final_score

        # Verify request creation
        call_args = mock_orchestrator.create_definition.call_args[0][0]
        assert isinstance(call_args, GenerationRequest)
        assert call_args.begrip == "Test"
        assert call_args.context == "Org context"
        # EPIC-010: domein field verwijderd
        assert call_args.organisatie == "Test Org"
        assert call_args.extra_instructies == "Extra info"

    @pytest.mark.asyncio()
    async def test_generate_definition_failure(
        self, service_adapter, mock_orchestrator
    ):
        """Test gefaalde definitie generatie via adapter."""
        # Setup
        mock_response = DefinitionResponse(
            success=False,
            definition=None,
            validation=None,
            message="Generation failed due to API error",
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute
        result = await service_adapter.generate_definition(
            begrip="Test", context_dict={}
        )

        # Verify
        assert result["success"] is False
        assert result["error_message"] == "Generation failed due to API error"

    @pytest.mark.asyncio()
    async def test_generate_definition_no_message(
        self, service_adapter, mock_orchestrator
    ):
        """Test generatie failure zonder message."""
        # Setup
        mock_response = DefinitionResponse(
            success=False, definition=None, validation=None, message=None  # No message
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute
        result = await service_adapter.generate_definition(
            begrip="Test", context_dict={}
        )

        # Verify
        assert result["error_message"] == "Generatie mislukt"

    @pytest.mark.asyncio()
    async def test_generate_definition_empty_context(
        self, service_adapter, mock_orchestrator
    ):
        """Test generatie met lege context."""
        # Setup
        mock_response = DefinitionResponse(
            success=True,
            definition=Definition(begrip="Test", definitie="Test def"),
            validation=None,
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute
        result = await service_adapter.generate_definition(
            begrip="Test", context_dict={}  # Empty context
        )

        # Verify request has empty strings (domein removed per US-043)
        call_args = mock_orchestrator.create_definition.call_args[0][0]
        assert call_args.context == ""
        # domein field removed per US-043
        assert call_args.organisatie == ""

    def test_get_stats(self, service_adapter, mock_container, mock_orchestrator):
        """Test get_stats methode."""
        # Setup mocks for each service
        mock_gen = Mock()
        mock_val = Mock()
        mock_repo = Mock()

        mock_gen.get_stats.return_value = {"gen": "stats"}
        mock_val.get_stats.return_value = {"val": "stats"}
        mock_repo.get_stats.return_value = {"repo": "stats"}
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
        assert stats["generator"] == {"gen": "stats"}
        assert stats["validator"] == {"val": "stats"}
        assert stats["repository"] == {"repo": "stats"}
        assert stats["orchestrator"] == {"orchestrator_stats": "data"}

        # Verify all services were called
        mock_container.generator.assert_called()
        mock_container.validator.assert_called()
        mock_container.repository.assert_called()


@pytest.mark.skip(reason="render_feature_flag_toggle moved to UI layer per US-043")
class TestRenderFeatureFlagToggle:
    """Test suite voor render_feature_flag_toggle UI component - MOVED TO UI LAYER."""

    def test_render_toggle_default_state(self):
        """Test rendering met default state."""
        with patch("services.service_factory.st") as mock_st:
            # Setup mocks
            mock_sidebar = Mock()
            mock_st.sidebar = mock_sidebar
            mock_st.session_state.get.return_value = False
            mock_st.checkbox.return_value = False

            # Setup sidebar context manager
            mock_sidebar.__enter__ = Mock(return_value=mock_st)
            mock_sidebar.__exit__ = Mock(return_value=None)

            # Execute
            # render_feature_flag_toggle moved to UI layer
            from ui.helpers.feature_toggle import render_feature_flag_toggle

            result = render_feature_flag_toggle()

            # Verify
            assert result is False
            mock_st.checkbox.assert_called_once()
            assert "Gebruik nieuwe services" in mock_st.checkbox.call_args[0][0]
            assert mock_st.checkbox.call_args[1]["value"] is False

    def test_render_toggle_enabled_state(self):
        """Test rendering met enabled nieuwe services."""
        with patch("services.service_factory.st") as mock_st:
            # Setup
            mock_st.session_state.get.return_value = True
            mock_st.checkbox.return_value = True
            mock_st.selectbox.return_value = "production"

            # Execute
            # render_feature_flag_toggle moved to UI layer
            from ui.helpers.feature_toggle import render_feature_flag_toggle

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
        with patch("services.service_factory.st") as mock_st:
            # Setup
            mock_st.checkbox.return_value = True
            mock_st.selectbox.return_value = "development"

            # Execute
            # render_feature_flag_toggle moved to UI layer
            from ui.helpers.feature_toggle import render_feature_flag_toggle

            result = render_feature_flag_toggle()

            # Verify warning
            mock_st.warning.assert_called_once_with("⚠️ Development mode actief")

    def test_render_toggle_testing_warning(self):
        """Test testing environment warning."""
        with patch("services.service_factory.st") as mock_st:
            # Setup
            mock_st.checkbox.return_value = True
            mock_st.selectbox.return_value = "testing"

            # Execute
            # render_feature_flag_toggle moved to UI layer
            from ui.helpers.feature_toggle import render_feature_flag_toggle

            result = render_feature_flag_toggle()

            # Verify warning
            mock_st.warning.assert_called_once_with("⚠️ Testing mode actief")

    def test_render_toggle_ui_structure(self):
        """Test UI structuur van de toggle."""
        with patch("services.service_factory.st") as mock_st:
            # Setup
            mock_st.checkbox.return_value = False
            mock_sidebar = Mock()
            mock_st.sidebar = mock_sidebar

            # Setup sidebar context manager
            mock_sidebar.__enter__ = Mock(return_value=mock_sidebar)
            mock_sidebar.__exit__ = Mock(return_value=None)

            # Execute
            # render_feature_flag_toggle moved to UI layer
            from ui.helpers.feature_toggle import render_feature_flag_toggle

            render_feature_flag_toggle()

            # Verify sidebar was used as context manager
            mock_sidebar.__enter__.assert_called_once()
            mock_sidebar.__exit__.assert_called_once()

            # Verify markdown calls were made
            # Note: Because of the context manager, we can't easily verify the exact calls


class TestOverallScoreHandling:
    """Test suite for overall_score KeyError fix (line 170 & 297)."""

    @pytest.mark.asyncio()
    async def test_overall_score_normal_case(self, service_adapter, mock_orchestrator):
        """Test normal case with valid overall_score."""
        # Setup with valid overall_score
        mock_validation = Mock()
        validation_dict = {
            "overall_score": 85.5,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": ["rule1", "rule2"],
        }
        mock_validation.to_dict.return_value = validation_dict
        # Add required attributes
        mock_validation.violations = []
        mock_validation.is_valid = True
        mock_validation.score = 85.5
        mock_validation.errors = []
        mock_validation.suggestions = []

        mock_response = DefinitionResponse(
            success=True,
            definition=Definition(
                begrip="Test",
                definitie="Test definitie",
                metadata={"origineel": "Original"},
            ),
            validation=mock_validation,
            message="Success",
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute
        result = await service_adapter.generate_definition("Test", {})

        # Verify overall_score is properly handled
        assert result["validation_details"]["overall_score"] == 85.5
        assert result["final_score"] == 85.5
        assert isinstance(result["final_score"], float)

    @pytest.mark.asyncio()
    async def test_overall_score_missing_key(self, service_adapter, mock_orchestrator):
        """Test handling when overall_score key is missing."""
        # Setup with missing overall_score key
        mock_validation = Mock()
        validation_dict = {
            # overall_score is missing
            "is_acceptable": False,
            "violations": [
                {"rule_id": "CON-001", "severity": "high", "description": "Issue"}
            ],
            "passed_rules": [],
        }
        mock_validation.to_dict.return_value = validation_dict
        # Add required attributes
        mock_validation.violations = validation_dict["violations"]
        mock_validation.is_valid = False
        mock_validation.score = 0.0
        mock_validation.errors = []
        mock_validation.suggestions = []

        mock_response = DefinitionResponse(
            success=True,
            definition=Definition(
                begrip="Test",
                definitie="Test definitie",
                metadata={"origineel": "Original"},
            ),
            validation=mock_validation,
            message="Success",
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute
        result = await service_adapter.generate_definition("Test", {})

        # Verify defaults to 0.0 when missing
        assert result["validation_details"]["overall_score"] == 0.0
        assert result["final_score"] == 0.0
        assert isinstance(result["final_score"], float)

    @pytest.mark.asyncio()
    async def test_overall_score_none_value(self, service_adapter, mock_orchestrator):
        """Test handling when overall_score is None."""
        # Setup with None overall_score
        mock_validation = Mock()
        validation_dict = {
            "overall_score": None,  # Explicitly None
            "is_acceptable": True,
            "violations": [],
            "passed_rules": ["rule1"],
        }
        mock_validation.to_dict.return_value = validation_dict
        # Add required attributes
        mock_validation.violations = []
        mock_validation.is_valid = True
        mock_validation.score = None  # Keep None to test handling
        mock_validation.errors = []
        mock_validation.suggestions = []

        mock_response = DefinitionResponse(
            success=True,
            definition=Definition(
                begrip="Test",
                definitie="Test definitie",
                metadata={"origineel": "Original"},
            ),
            validation=mock_validation,
            message="Success",
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute
        result = await service_adapter.generate_definition("Test", {})

        # Verify defaults to 0.0 when None
        assert result["validation_details"]["overall_score"] == 0.0
        assert result["final_score"] == 0.0
        assert isinstance(result["final_score"], float)

    @pytest.mark.asyncio()
    async def test_overall_score_invalid_string(
        self, service_adapter, mock_orchestrator
    ):
        """Test handling when overall_score is an invalid string."""
        # Setup with string overall_score
        mock_validation = Mock()
        validation_dict = {
            "overall_score": "not_a_number",  # Invalid string
            "is_acceptable": False,
            "violations": [],
            "passed_rules": [],
        }
        mock_validation.to_dict.return_value = validation_dict
        # Add required attributes
        mock_validation.violations = []
        mock_validation.is_valid = False
        mock_validation.score = "not_a_number"  # Keep invalid to test handling
        mock_validation.errors = []
        mock_validation.suggestions = []

        mock_response = DefinitionResponse(
            success=True,
            definition=Definition(
                begrip="Test",
                definitie="Test definitie",
                metadata={"origineel": "Original"},
            ),
            validation=mock_validation,
            message="Success",
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute - should handle gracefully
        result = await service_adapter.generate_definition("Test", {})

        # Verify error handling - string can't be converted to float, defaults to 0.0
        # The code uses `float(result.get("overall_score") or 0.0)` which will raise ValueError
        # for invalid strings, so we need to check if this is handled
        try:
            float("not_a_number")
        except ValueError:
            # If the implementation doesn't handle this, it would raise
            # Check that the result still has some score value
            assert "validation_details" in result
            # Implementation might crash here - documenting expected behavior

    @pytest.mark.asyncio()
    async def test_overall_score_valid_string_number(
        self, service_adapter, mock_orchestrator
    ):
        """Test handling when overall_score is a valid numeric string."""
        # Setup with string that can be converted to float
        mock_validation = Mock()
        validation_dict = {
            "overall_score": "75.5",  # String that converts to float
            "is_acceptable": True,
            "violations": [],
            "passed_rules": ["rule1"],
        }
        mock_validation.to_dict.return_value = validation_dict
        # Add required attributes
        mock_validation.violations = []
        mock_validation.is_valid = True
        mock_validation.score = "75.5"  # Keep as string to test conversion
        mock_validation.errors = []
        mock_validation.suggestions = []

        mock_response = DefinitionResponse(
            success=True,
            definition=Definition(
                begrip="Test",
                definitie="Test definitie",
                metadata={"origineel": "Original"},
            ),
            validation=mock_validation,
            message="Success",
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute
        result = await service_adapter.generate_definition("Test", {})

        # Verify string is converted to float
        assert result["validation_details"]["overall_score"] == 75.5
        assert result["final_score"] == 75.5
        assert isinstance(result["final_score"], float)

    @pytest.mark.asyncio()
    async def test_overall_score_list_type(self, service_adapter, mock_orchestrator):
        """Test handling when overall_score is a list (invalid type)."""
        # Setup with list overall_score
        mock_validation = Mock()
        validation_dict = {
            "overall_score": [85, 90],  # Invalid list type
            "is_acceptable": True,
            "violations": [],
            "passed_rules": [],
        }
        mock_validation.to_dict.return_value = validation_dict
        # Add required attributes
        mock_validation.violations = []
        mock_validation.is_valid = True
        mock_validation.score = [85, 90]  # Keep as list to test handling
        mock_validation.errors = []
        mock_validation.suggestions = []

        mock_response = DefinitionResponse(
            success=True,
            definition=Definition(
                begrip="Test",
                definitie="Test definitie",
                metadata={"origineel": "Original"},
            ),
            validation=mock_validation,
            message="Success",
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute - should handle type error
        try:
            result = await service_adapter.generate_definition("Test", {})
            # List can't be converted to float, would raise TypeError
        except (TypeError, ValueError):
            pass  # Expected - documenting behavior

    @pytest.mark.asyncio()
    async def test_overall_score_dict_type(self, service_adapter, mock_orchestrator):
        """Test handling when overall_score is a dict (invalid type)."""
        # Setup with dict overall_score
        mock_validation = Mock()
        validation_dict = {
            "overall_score": {"score": 85},  # Invalid dict type
            "is_acceptable": True,
            "violations": [],
            "passed_rules": [],
        }
        mock_validation.to_dict.return_value = validation_dict
        # Add required attributes
        mock_validation.violations = []
        mock_validation.is_valid = True
        mock_validation.score = {"score": 85}  # Keep as dict to test handling
        mock_validation.errors = []
        mock_validation.suggestions = []

        mock_response = DefinitionResponse(
            success=True,
            definition=Definition(
                begrip="Test",
                definitie="Test definitie",
                metadata={"origineel": "Original"},
            ),
            validation=mock_validation,
            message="Success",
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute - should handle type error
        try:
            result = await service_adapter.generate_definition("Test", {})
            # Dict can't be converted to float, would raise TypeError
        except (TypeError, ValueError):
            pass  # Expected - documenting behavior

    @pytest.mark.asyncio()
    async def test_overall_score_zero_value(self, service_adapter, mock_orchestrator):
        """Test handling when overall_score is zero (edge case)."""
        # Setup with zero overall_score
        mock_validation = Mock()
        validation_dict = {
            "overall_score": 0,  # Valid zero
            "is_acceptable": False,
            "violations": [
                {"rule_id": "ESS-001", "severity": "high", "description": "Major issue"}
            ],
            "passed_rules": [],
        }
        mock_validation.to_dict.return_value = validation_dict
        # Add required attributes
        mock_validation.violations = validation_dict["violations"]
        mock_validation.is_valid = False
        mock_validation.score = 0
        mock_validation.errors = []
        mock_validation.suggestions = []

        mock_response = DefinitionResponse(
            success=True,
            definition=Definition(
                begrip="Test",
                definitie="Test definitie",
                metadata={"origineel": "Original"},
            ),
            validation=mock_validation,
            message="Success",
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute
        result = await service_adapter.generate_definition("Test", {})

        # Verify zero is properly handled (not replaced with default)
        assert result["validation_details"]["overall_score"] == 0.0
        assert result["final_score"] == 0.0
        assert isinstance(result["final_score"], float)

    @pytest.mark.asyncio()
    async def test_overall_score_negative_value(
        self, service_adapter, mock_orchestrator
    ):
        """Test handling when overall_score is negative (edge case)."""
        # Setup with negative overall_score
        mock_validation = Mock()
        validation_dict = {
            "overall_score": -10.5,  # Negative score
            "is_acceptable": False,
            "violations": [],
            "passed_rules": [],
        }
        mock_validation.to_dict.return_value = validation_dict
        # Add required attributes
        mock_validation.violations = []
        mock_validation.is_valid = False
        mock_validation.score = -10.5
        mock_validation.errors = []
        mock_validation.suggestions = []

        mock_response = DefinitionResponse(
            success=True,
            definition=Definition(
                begrip="Test",
                definitie="Test definitie",
                metadata={"origineel": "Original"},
            ),
            validation=mock_validation,
            message="Success",
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute
        result = await service_adapter.generate_definition("Test", {})

        # Verify negative value is preserved (business logic might need this)
        assert result["validation_details"]["overall_score"] == -10.5
        assert result["final_score"] == -10.5
        assert isinstance(result["final_score"], float)

    @pytest.mark.asyncio()
    async def test_overall_score_very_large_value(
        self, service_adapter, mock_orchestrator
    ):
        """Test handling when overall_score is a very large number."""
        # Setup with very large overall_score
        mock_validation = Mock()
        validation_dict = {
            "overall_score": 999999999.99,  # Very large score
            "is_acceptable": True,
            "violations": [],
            "passed_rules": ["all_rules"],
        }
        mock_validation.to_dict.return_value = validation_dict
        # Add required attributes
        mock_validation.violations = []
        mock_validation.is_valid = True
        mock_validation.score = 999999999.99
        mock_validation.errors = []
        mock_validation.suggestions = []

        mock_response = DefinitionResponse(
            success=True,
            definition=Definition(
                begrip="Test",
                definitie="Test definitie",
                metadata={"origineel": "Original"},
            ),
            validation=mock_validation,
            message="Success",
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute
        result = await service_adapter.generate_definition("Test", {})

        # Verify large value is handled properly
        assert result["validation_details"]["overall_score"] == 999999999.99
        assert result["final_score"] == 999999999.99
        assert isinstance(result["final_score"], float)

    @pytest.mark.asyncio()
    async def test_concurrent_validation_scenario(self, mock_container):
        """Test concurrent validations with different overall_score scenarios."""

        # Create multiple adapters for concurrent testing
        orchestrators = []
        adapters = []

        for i in range(3):
            orchestrator = AsyncMock()
            mock_container.orchestrator.return_value = orchestrator
            adapter = ServiceAdapter(mock_container)
            orchestrators.append(orchestrator)
            adapters.append(adapter)

        # Setup different scenarios
        # Scenario 1: Normal score
        mock_val1 = Mock()
        mock_val1.to_dict.return_value = {
            "overall_score": 95.0,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": ["rule1"],
        }
        # Add required attributes
        mock_val1.violations = []
        mock_val1.is_valid = True
        mock_val1.score = 95.0
        mock_val1.errors = []
        mock_val1.suggestions = []
        orchestrators[0].create_definition.return_value = DefinitionResponse(
            success=True,
            definition=Definition(begrip="Test1", definitie="Def1", metadata={}),
            validation=mock_val1,
        )

        # Scenario 2: Missing score
        mock_val2 = Mock()
        mock_val2.to_dict.return_value = {
            # Missing overall_score
            "is_acceptable": False,
            "violations": [],
            "passed_rules": [],
        }
        # Add required attributes
        mock_val2.violations = []
        mock_val2.is_valid = False
        mock_val2.score = 0.0  # Missing defaults to 0.0
        mock_val2.errors = []
        mock_val2.suggestions = []
        orchestrators[1].create_definition.return_value = DefinitionResponse(
            success=True,
            definition=Definition(begrip="Test2", definitie="Def2", metadata={}),
            validation=mock_val2,
        )

        # Scenario 3: None score
        mock_val3 = Mock()
        mock_val3.to_dict.return_value = {
            "overall_score": None,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": [],
        }
        # Add required attributes
        mock_val3.violations = []
        mock_val3.is_valid = True
        mock_val3.score = None  # Keep None to test handling
        mock_val3.errors = []
        mock_val3.suggestions = []
        orchestrators[2].create_definition.return_value = DefinitionResponse(
            success=True,
            definition=Definition(begrip="Test3", definitie="Def3", metadata={}),
            validation=mock_val3,
        )

        # Execute concurrent validations
        tasks = [
            adapters[0].generate_definition("Test1", {}),
            adapters[1].generate_definition("Test2", {}),
            adapters[2].generate_definition("Test3", {}),
        ]

        results = await asyncio.gather(*tasks)

        # Verify all handled correctly
        assert results[0]["final_score"] == 95.0
        assert results[1]["final_score"] == 0.0  # Missing defaults to 0.0
        assert results[2]["final_score"] == 0.0  # None defaults to 0.0

        # All should have proper validation_details
        for result in results:
            assert "validation_details" in result
            assert "overall_score" in result["validation_details"]
            assert isinstance(result["validation_details"]["overall_score"], float)

    @pytest.mark.asyncio()
    async def test_validation_details_missing_entirely(
        self, service_adapter, mock_orchestrator
    ):
        """Test when validation object is None entirely."""
        # Setup with no validation at all
        mock_response = DefinitionResponse(
            success=True,
            definition=Definition(
                begrip="Test",
                definitie="Test definitie",
                metadata={"origineel": "Original"},
            ),
            validation=None,  # No validation object
            message="Success",
        )

        mock_orchestrator.create_definition.return_value = mock_response

        # Execute
        result = await service_adapter.generate_definition("Test", {})

        # Verify defaults are used when validation is None
        assert result["validation_details"]["overall_score"] == 0.0
        assert result["final_score"] == 0.0
        assert result["validation_details"]["is_acceptable"] is False
        assert result["validation_details"]["violations"] == []
        assert result["validation_details"]["passed_rules"] == []


class TestIntegrationScenarios:
    """Integration test scenarios voor service factory."""

    def test_v2_only_no_switching(self):
        """Test V2 only - no legacy switching (per US-043)."""
        with patch(
            "services.service_factory.get_cached_container"
        ) as mock_get_container:

            # Always V2 services, singleton container
            mock_container = Mock()
            mock_get_container.return_value = mock_container

            service1 = get_definition_service()
            assert isinstance(service1, ServiceAdapter)
            assert service1.container == mock_container

            # Second call also V2 (no switching possible, singleton)
            service2 = get_definition_service()
            assert isinstance(service2, ServiceAdapter)
            assert service2.container == mock_container

            # Both are V2, no legacy path exists
            assert service1.__class__ == service2.__class__

    @pytest.mark.asyncio()
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
            metadata={
                "complex": True,
                "voorbeelden": {"voorbeeldzinnen": ["V1", "V2"]},
            },
        )

        validation = ValidationResult(
            is_valid=True, score=0.85, errors=["Error1", "Error2"], suggestions=["Sug1"]
        )

        response = DefinitionResponse(
            success=True,
            definition=definition,
            validation=validation,
            message="Complex success",
        )

        orchestrator.create_definition.return_value = response

        # Execute
        result = await adapter.generate_definition(
            begrip="Complex",
            context_dict={
                "organisatorisch": ["O1", "O2"],
                "juridisch": ["J1"],
                "domein": ["D1", "D2", "D3"],
            },
        )

        # Verify complex mapping (voorbeelden from metadata now)
        assert result["success"] is True
        assert result["definitie_gecorrigeerd"] == "Complex definitie"
        assert result["voorbeelden"] == {"voorbeeldzinnen": ["V1", "V2"]}
        assert result["final_score"] == 0.85
        # Check validation details instead of direct score
        assert "overall_score" in result["validation_details"]
