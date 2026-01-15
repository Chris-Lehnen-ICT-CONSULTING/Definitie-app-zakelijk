"""
Test suite for single-path classification implementation.

Validates that:
1. Classification only happens in _render_category_preview()
2. Generation validates classification exists
3. No fallback paths exist
4. Clear error messages when classification missing
5. Manual override works correctly
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from domain.ontological_categories import OntologischeCategorie


class TestSinglePathClassification:
    """Test single-path classification behavior."""

    @pytest.fixture
    def mock_session_state(self):
        """Mock session state manager."""
        with patch("ui.tabbed_interface.SessionStateManager") as mock:
            mock.get_value = Mock(return_value=None)
            mock.set_value = Mock()
            mock.clear_value = Mock()
            yield mock

    @pytest.fixture
    def mock_interface(self, mock_session_state):
        """Create TabbedInterface with mocked dependencies."""
        with (
            # US-202: get_cached_service_container moved to lazy import within __init__
            patch("ui.cached_services.get_cached_service_container"),
            patch("database.definitie_repository.get_definitie_repository"),
            patch("services.get_definition_service"),
            patch("ui.tabbed_interface.DefinitieChecker"),
            patch("ui.tabbed_interface.ContextSelector"),
            patch("ui.tabbed_interface.DefinitionGeneratorTab"),
            patch("ui.tabbed_interface.DefinitionEditTab"),
            patch("ui.tabbed_interface.ExpertReviewTab"),
            patch("ui.tabbed_interface.ImportExportBeheerTab"),
        ):

            from ui.tabbed_interface import TabbedInterface

            return TabbedInterface()

    def test_classification_preview_performs_classification(
        self, mock_interface, mock_session_state
    ):
        """Test that _render_category_preview performs classification when needed."""
        # Setup: begrip exists, no classification yet, context available
        mock_session_state.get_value.side_effect = lambda key, default=None: {
            "begrip": "authenticatie",
            "determined_category": None,
            "global_context": {
                "organisatorische_context": ["Justitie"],
                "juridische_context": ["Strafrecht"],
            },
        }.get(key, default)

        with patch.object(
            mock_interface, "_determine_ontological_category"
        ) as mock_classify:
            mock_classify.return_value = (
                OntologischeCategorie.PROCES,
                "Gedetecteerd als proces",
                {"proces": 2, "type": 0, "resultaat": 0, "exemplaar": 0},
            )

            # This would fail in real Streamlit but we test the logic
            with (
                patch("ui.tabbed_interface.st"),
                patch("ui.tabbed_interface.asyncio.run", side_effect=lambda coro: coro),
            ):
                try:
                    mock_interface._render_category_preview()
                except Exception:
                    pass  # Streamlit calls will fail, that's OK

        # Verify classification was called
        assert mock_classify.called or mock_session_state.set_value.called

    def test_generation_blocks_without_classification(
        self, mock_interface, mock_session_state
    ):
        """Test that generation blocks when no classification exists."""
        # Setup: no determined category, no manual override
        mock_session_state.get_value.side_effect = lambda key, default=None: {
            "begrip": "test",
            "global_context": {
                "organisatorische_context": [],
                "juridische_context": [],
                "wettelijke_basis": [],
            },
            "generation_options": {},
            "selected_documents": [],
            "determined_category": None,  # NO CLASSIFICATION
            "manual_ontological_category": None,
        }.get(key, default)

        with patch("ui.tabbed_interface.st") as mock_st:
            mock_st.spinner = MagicMock()
            mock_st.spinner.return_value.__enter__ = Mock()
            mock_st.spinner.return_value.__exit__ = Mock()
            mock_st.error = Mock()

            # Call generation
            mock_interface._handle_definition_generation("test", {})

            # Verify error was shown
            mock_st.error.assert_called_once()
            error_msg = mock_st.error.call_args[0][0]
            assert "Ontologische categorie is niet bepaald" in error_msg
            assert "Scroll naar boven" in error_msg

    def test_generation_succeeds_with_manual_override(
        self, mock_interface, mock_session_state
    ):
        """Test that manual override bypasses pre-classification requirement."""
        # Setup: manual override set
        mock_session_state.get_value.side_effect = lambda key, default=None: {
            "begrip": "test",
            "global_context": {
                "organisatorische_context": [],
                "juridische_context": [],
                "wettelijke_basis": [],
            },
            "generation_options": {},
            "selected_documents": [],
            "determined_category": None,  # No pre-classification
            "manual_ontological_category": "PROCES",  # But manual override exists
        }.get(key, default)

        with (
            patch("ui.tabbed_interface.st") as mock_st,
            patch.object(mock_interface, "_get_document_context", return_value=None),
            patch("ui.helpers.async_bridge.run_async") as mock_async,
        ):

            mock_st.spinner = MagicMock()
            mock_st.spinner.return_value.__enter__ = Mock()
            mock_st.spinner.return_value.__exit__ = Mock()
            mock_st.error = Mock()
            mock_st.success = Mock()

            # Mock service result
            mock_async.return_value = {
                "success": True,
                "definitie_gecorrigeerd": "Test definitie",
                "validation_details": {},
            }

            # Call generation - should NOT error
            mock_interface._handle_definition_generation("test", {})

            # Verify NO error was shown
            assert not mock_st.error.called

    def test_generation_succeeds_with_preclassification(
        self, mock_interface, mock_session_state
    ):
        """Test that generation succeeds when pre-classification exists."""
        # Setup: pre-classification exists
        mock_session_state.get_value.side_effect = lambda key, default=None: {
            "begrip": "authenticatie",
            "global_context": {
                "organisatorische_context": [],
                "juridische_context": [],
                "wettelijke_basis": [],
            },
            "generation_options": {},
            "selected_documents": [],
            "determined_category": "PROCES",  # Pre-classification exists
            "category_reasoning": "Test reasoning",
            "category_scores": {"proces": 2},
            "manual_ontological_category": None,
        }.get(key, default)

        with (
            patch("ui.tabbed_interface.st") as mock_st,
            patch.object(mock_interface, "_get_document_context", return_value=None),
            patch("ui.helpers.async_bridge.run_async") as mock_async,
        ):

            mock_st.spinner = MagicMock()
            mock_st.spinner.return_value.__enter__ = Mock()
            mock_st.spinner.return_value.__exit__ = Mock()
            mock_st.error = Mock()
            mock_st.success = Mock()

            # Mock service result
            mock_async.return_value = {
                "success": True,
                "definitie_gecorrigeerd": "Test definitie",
                "validation_details": {},
            }

            # Call generation - should succeed
            mock_interface._handle_definition_generation("authenticatie", {})

            # Verify NO error
            assert not mock_st.error.called

    def test_clear_all_fields_clears_classification(
        self, mock_interface, mock_session_state
    ):
        """Test that clear all fields removes classification state."""
        mock_interface._clear_all_fields()

        # Verify all classification-related fields are cleared
        cleared_fields = [
            call[0][0] for call in mock_session_state.clear_value.call_args_list
        ]

        assert "determined_category" in cleared_fields
        assert "category_reasoning" in cleared_fields
        assert "category_scores" in cleared_fields
        assert "manual_ontological_category" in cleared_fields

    def test_no_fallback_classification_in_generation(self, mock_interface):
        """Verify _handle_definition_generation does NOT call _determine_ontological_category."""
        with (
            patch.object(
                mock_interface, "_determine_ontological_category"
            ) as mock_classify,
            patch("ui.tabbed_interface.SessionStateManager") as mock_session,
            patch("ui.tabbed_interface.st"),
        ):

            # Setup: no classification
            mock_session.get_value.return_value = None

            try:
                mock_interface._handle_definition_generation("test", {})
            except Exception:
                pass  # Will fail due to missing classification, that's expected

            # Verify _determine_ontological_category was NEVER called (no fallback)
            assert (
                not mock_classify.called
            ), "Fallback classification found - SINGLE PATH violated!"


class TestDeadCodeRemoval:
    """Verify dead code has been removed."""

    def test_classify_term_on_change_removed(self):
        """Verify _classify_term_on_change method has been removed."""
        from ui.tabbed_interface import TabbedInterface

        assert not hasattr(
            TabbedInterface, "_classify_term_on_change"
        ), "_classify_term_on_change still exists - should be removed"

    def test_legacy_pattern_matching_removed(self):
        """Verify _legacy_pattern_matching method has been removed."""
        from ui.tabbed_interface import TabbedInterface

        assert not hasattr(
            TabbedInterface, "_legacy_pattern_matching"
        ), "_legacy_pattern_matching still exists - should be removed"

    def test_generate_category_reasoning_removed(self):
        """Verify _generate_category_reasoning method has been removed."""
        from ui.tabbed_interface import TabbedInterface

        assert not hasattr(
            TabbedInterface, "_generate_category_reasoning"
        ), "_generate_category_reasoning still exists - should be removed"

    def test_get_category_scores_removed(self):
        """Verify _get_category_scores method has been removed."""
        from ui.tabbed_interface import TabbedInterface

        assert not hasattr(
            TabbedInterface, "_get_category_scores"
        ), "_get_category_scores still exists - should be removed"


class TestClassificationFlow:
    """Test the complete classification flow."""

    @pytest.fixture
    def interface_with_mocks(self):
        """Setup interface with all necessary mocks."""
        with (
            # US-202: Patches updated for lazy imports
            patch("ui.cached_services.get_cached_service_container"),
            patch("database.definitie_repository.get_definitie_repository"),
            patch("services.get_definition_service"),
            patch("ui.tabbed_interface.SessionStateManager") as mock_session,
            patch("ui.tabbed_interface.DefinitieChecker"),
            patch("ui.tabbed_interface.ContextSelector"),
            patch("ui.tabbed_interface.DefinitionGeneratorTab"),
            patch("ui.tabbed_interface.DefinitionEditTab"),
            patch("ui.tabbed_interface.ExpertReviewTab"),
            patch("ui.tabbed_interface.ImportExportBeheerTab"),
        ):

            from ui.tabbed_interface import TabbedInterface

            interface = TabbedInterface()
            yield interface, mock_session

    def test_complete_flow_with_classification(self, interface_with_mocks):
        """Test complete flow: classify → generate."""
        interface, mock_session = interface_with_mocks

        # Step 1: User enters term and context
        classification_state = {
            "begrip": "authenticatie",
            "global_context": {
                "organisatorische_context": ["Justitie"],
                "juridische_context": ["Strafrecht"],
            },
            "determined_category": None,
        }

        # Step 2: Classification happens in preview
        with (
            patch.object(interface, "_determine_ontological_category") as mock_classify,
            patch("ui.tabbed_interface.st"),
            patch("ui.tabbed_interface.asyncio.run", side_effect=lambda coro: coro),
        ):

            mock_classify.return_value = (
                OntologischeCategorie.PROCES,
                "Proces patroon",
                {"proces": 2, "type": 0, "resultaat": 0, "exemplaar": 0},
            )

            mock_session.get_value.side_effect = (
                lambda k, d=None: classification_state.get(k, d)
            )

            try:
                interface._render_category_preview()
            except Exception:
                pass  # Streamlit calls will fail

            # Simulate classification result stored
            classification_state["determined_category"] = "PROCES"
            classification_state["category_reasoning"] = "Proces patroon"
            classification_state["category_scores"] = {"proces": 2}

        # Step 3: Generation uses pre-classification
        with (
            patch("ui.tabbed_interface.st") as mock_st,
            patch.object(interface, "_get_document_context", return_value=None),
            patch("ui.helpers.async_bridge.run_async") as mock_async,
        ):

            mock_st.spinner = MagicMock()
            mock_st.spinner.return_value.__enter__ = Mock()
            mock_st.spinner.return_value.__exit__ = Mock()
            mock_st.success = Mock()

            mock_async.return_value = {
                "success": True,
                "definitie_gecorrigeerd": "Test",
                "validation_details": {},
            }

            mock_session.get_value.side_effect = (
                lambda k, d=None: classification_state.get(k, d)
            )

            # Should succeed without errors
            interface._handle_definition_generation(
                "authenticatie", classification_state["global_context"]
            )

            # Verify success
            assert mock_st.success.called

    def test_flow_without_classification_blocks(self, interface_with_mocks):
        """Test that generation without classification is blocked."""
        interface, mock_session = interface_with_mocks

        # Setup: no classification
        state = {
            "begrip": "test",
            "global_context": {
                "organisatorische_context": [],
                "juridische_context": [],
                "wettelijke_basis": [],
            },
            "generation_options": {},
            "selected_documents": [],
            "determined_category": None,  # NO CLASSIFICATION
            "manual_ontological_category": None,
        }

        mock_session.get_value.side_effect = lambda k, d=None: state.get(k, d)

        with patch("ui.tabbed_interface.st") as mock_st:
            mock_st.spinner = MagicMock()
            mock_st.spinner.return_value.__enter__ = Mock()
            mock_st.spinner.return_value.__exit__ = Mock()
            mock_st.error = Mock()

            # Try to generate - should be blocked
            interface._handle_definition_generation("test", state["global_context"])

            # Verify error shown
            assert mock_st.error.called
            error_msg = mock_st.error.call_args[0][0]
            assert "niet bepaald" in error_msg.lower()
